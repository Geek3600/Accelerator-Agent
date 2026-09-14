#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import random
import shutil
import argparse
import importlib.util
import inspect
from dataclasses import dataclass
from typing import List, Tuple
import time
import torch
import pandas as pd
from tqdm import tqdm
from transformers import AutoModelForCausalLM
from smoothquant.opt import Int8OPTForCausalLM

# =========================
# 路径配置
# =========================
#MODEL_DIR = "/root/smoothquant/pyjm_opt_last"
MODEL_DIR = "/root/smoothquant/cpfs01/projects-HDD/cfff-4da39d3c1e4e_HDD/cyl_23110240101/opt128_train_output/final"
PATTERNS_FILE = "/root/smoothquant/patterns.txt"
OUTPUT_FILE = "/root/smoothquant/10^4.txt"

TOTAL_GENERATE = 10000
MAX_LENGTH = 128
MAX_NEW_TOKENS = 32

TEMPERATURE = 0.9
TOP_K = 50
TOP_P = 1.0
SEED = 42

# 训练代码本身并不拼接 pattern，而是直接 tokenizer(text)
# 因此这里默认假设训练文件每一行格式为: pattern\tpassword
PROMPT_MODE = "tab"


# =========================
# 动态加载 CharTokenizer
# =========================
def load_char_tokenizer_class(tokenizer_py_path: str):
    if not os.path.isfile(tokenizer_py_path):
        raise FileNotFoundError(f"char_tokenizer.py 不存在: {tokenizer_py_path}")

    spec = importlib.util.spec_from_file_location("char_tokenizer", tokenizer_py_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {tokenizer_py_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "CharTokenizer"):
        raise AttributeError(f"{tokenizer_py_path} 中未找到 CharTokenizer")

    return module.CharTokenizer


def build_tokenizer_kwargs(CharTokenizer, vocab_file: str):
    """
    尽量与训练代码保持一致:
        tokenizer = CharTokenizer(
            vocab_file=VOCAB_FILE,
            bos_token="<BOS>",
            eos_token="<EOS>",
            pad_token="<PAD>",
        )
    但考虑到不同 CharTokenizer 构造函数参数可能略有不同，这里做兼容。
    """
    sig = inspect.signature(CharTokenizer.__init__)
    params = set(sig.parameters.keys())

    kwargs = {}
    if "vocab_file" in params:
        kwargs["vocab_file"] = vocab_file
    elif "vocab_path" in params:
        kwargs["vocab_path"] = vocab_file
    else:
        raise ValueError("CharTokenizer.__init__ 中未找到 vocab_file / vocab_path 参数")

    if "bos_token" in params:
        kwargs["bos_token"] = "<BOS>"
    if "eos_token" in params:
        kwargs["eos_token"] = "<EOS>"
    if "pad_token" in params:
        kwargs["pad_token"] = "<PAD>"
    if "sep_token" in params:
        kwargs["sep_token"] = "<SEP>"
    if "unk_token" in params:
        kwargs["unk_token"] = "<UNK>"

    return kwargs


def load_tokenizer(model_dir: str):
    vocab_file = os.path.join(model_dir, "vocab.json")
    tokenizer_py = os.path.join(model_dir, "char_tokenizer.py")

    if not os.path.isfile(vocab_file):
        raise FileNotFoundError(f"vocab.json 不存在: {vocab_file}")
    if not os.path.isfile(tokenizer_py):
        raise FileNotFoundError(f"char_tokenizer.py 不存在: {tokenizer_py}")

    CharTokenizer = load_char_tokenizer_class(tokenizer_py)
    kwargs = build_tokenizer_kwargs(CharTokenizer, vocab_file)
    tokenizer = CharTokenizer(**kwargs)

    if not hasattr(tokenizer, "vocab_size"):
        if hasattr(tokenizer, "vocab") and isinstance(tokenizer.vocab, dict):
            tokenizer.vocab_size = len(tokenizer.vocab)
        else:
            raise AttributeError("tokenizer 中未找到 vocab_size")

    return tokenizer


# =========================
# 工具函数
# =========================
def set_seed(seed: int):
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_model(model_dir: str, device: str):
    if not os.path.isdir(model_dir):
        raise FileNotFoundError(f"模型目录不存在: {model_dir}")

    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        local_files_only=True,
    )
    # model = Int8OPTForCausalLM.from_pretrained(
    #     model_dir,
    #     local_files_only=True,
    # )
    model.to(device)
    model.eval()
    model.config.use_cache = True
    return model


def build_prompt(pattern: str, prompt_mode: str) -> str:
    pattern = str(pattern).strip()

    # 默认与当前训练数据对齐：pattern\tpassword
    if prompt_mode == "tab":
        return f"{pattern}\t"

    # 仅保留为兼容选项；只有当训练集本身就是这种格式时才应使用
    if prompt_mode == "pat_sep":
        return f"<PAT>{pattern}</PAT><SEP>"

    raise ValueError(f"不支持的 prompt_mode: {prompt_mode}")


def safe_decode_ids(tokenizer, token_ids, skip_special_tokens: bool = False) -> str:
    if hasattr(tokenizer, "decode"):
        try:
            return tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)
        except Exception:
            pass

    id_to_token = None
    if hasattr(tokenizer, "inv_vocab") and isinstance(tokenizer.inv_vocab, dict):
        id_to_token = tokenizer.inv_vocab
    elif hasattr(tokenizer, "decoder") and isinstance(tokenizer.decoder, dict):
        id_to_token = tokenizer.decoder
    elif hasattr(tokenizer, "vocab") and isinstance(tokenizer.vocab, dict):
        id_to_token = {int(v): k for k, v in tokenizer.vocab.items()}

    if id_to_token is None:
        raise RuntimeError("无法从 tokenizer 中找到可用的 id->token 映射")

    special_ids = set()
    for attr in ["bos_token_id", "eos_token_id", "pad_token_id", "unk_token_id", "sep_token_id"]:
        if hasattr(tokenizer, attr):
            val = getattr(tokenizer, attr)
            if val is not None:
                special_ids.add(int(val))

    pieces = []
    for tid in token_ids:
        tid = int(tid)
        if skip_special_tokens and tid in special_ids:
            continue
        pieces.append(id_to_token.get(tid, ""))

    return "".join(pieces)


def filter_generated_text(text: str) -> str:
    for tok in ["<BOS>", "<EOS>", "<PAD>", "<UNK>", "<SEP>", "<PAT>", "</PAT>"]:
        text = text.replace(tok, "")
    text = text.replace("\r", "")
    text = text.replace("\n", "")
    return text.strip()


def encode_prompt(tokenizer, prompt: str):
    """
    与训练代码保持一致：直接 tokenizer(text)
    """
    enc = tokenizer(prompt)

    if "input_ids" not in enc or "attention_mask" not in enc:
        raise ValueError("tokenizer(prompt) 返回结果中缺少 input_ids 或 attention_mask")

    input_ids = enc["input_ids"]
    attention_mask = enc["attention_mask"]

    if not isinstance(input_ids, list):
        input_ids = list(input_ids)
    if not isinstance(attention_mask, list):
        attention_mask = list(attention_mask)

    return input_ids, attention_mask


def top_k_top_p_filtering(logits: torch.Tensor, top_k: int = 0, top_p: float = 1.0) -> torch.Tensor:
    logits = logits.clone()

    if top_k > 0:
        top_k = min(top_k, logits.size(-1))
        threshold = torch.topk(logits, top_k)[0][..., -1, None]
        logits[logits < threshold] = -float("inf")

    if top_p < 1.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True, dim=-1)
        probs = torch.softmax(sorted_logits, dim=-1)
        cumulative_probs = torch.cumsum(probs, dim=-1)

        sorted_indices_to_remove = cumulative_probs > top_p
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = False

        for b in range(logits.size(0)):
            remove_ids = sorted_indices[b][sorted_indices_to_remove[b]]
            logits[b, remove_ids] = -float("inf")

    return logits


# =========================
# 可选的简单模式校验
# 仅支持 L/N/S/U/l 这类简单格式
# 对复杂 W/K/Lf/Nf 等模式不适用
# =========================
def parse_simple_pattern(pattern: str) -> List[Tuple[str, int]]:
    parts = re.findall(r"([A-Za-z])(\d+)", pattern)
    return [(p[0], int(p[1])) for p in parts]


def char_type_match(ch: str, kind: str) -> bool:
    if kind == "L":
        return ch.isalpha()
    if kind == "N":
        return ch.isdigit()
    if kind == "S":
        return (not ch.isalnum()) and (not ch.isspace())
    if kind == "U":
        return ch.isupper()
    if kind == "l":
        return ch.islower()
    return False


def match_simple_pattern(password: str, pattern: str) -> bool:
    pattern = str(pattern).strip()
    password = str(password)

    parts = parse_simple_pattern(pattern)
    if not parts:
        return True

    expected_len = sum(n for _, n in parts)
    if len(password) != expected_len:
        return False

    pos = 0
    for kind, cnt in parts:
        seg = password[pos:pos + cnt]
        if len(seg) != cnt:
            return False
        if not all(char_type_match(ch, kind) for ch in seg):
            return False
        pos += cnt

    return True


@torch.no_grad()
def generate_one(
    pattern: str,
    model,
    tokenizer,
    device: str = "cuda",
    prompt_mode: str = "tab",
    max_new_tokens: int = 32,
    max_length: int = 128,
    temperature: float = 0.9,
    top_k: int = 50,
    top_p: float = 1.0,
) -> str:
    prompt = build_prompt(pattern, prompt_mode)

    input_ids, _ = encode_prompt(tokenizer, prompt)

    eos_token_id = getattr(tokenizer, "eos_token_id", None)
    if eos_token_id is not None and len(input_ids) > 0 and input_ids[-1] == eos_token_id:
        input_ids = input_ids[:-1]

    if len(input_ids) == 0:
        raise ValueError("prompt 编码后为空")

    remain_len = max_length - len(input_ids)
    if remain_len <= 0:
        return ""

    max_gen_len = min(max_new_tokens, remain_len)

    generated = torch.tensor([input_ids], dtype=torch.long, device=device)
    start_time = time.time()
    generated_tokens_count = 0
    for _ in range(max_gen_len):
        outputs = model(input_ids=generated)
        logits = outputs.logits[:, -1, :]

        logits = logits / max(temperature, 1e-8)
        logits = top_k_top_p_filtering(logits, top_k=top_k, top_p=top_p)
        probs = torch.softmax(logits, dim=-1)

        if (not torch.isfinite(probs).all()) or torch.sum(probs).item() <= 0:
            next_token = torch.argmax(outputs.logits[:, -1, :], dim=-1, keepdim=True)
        else:
            next_token = torch.multinomial(probs, num_samples=1)

        next_id = int(next_token.item())
        generated = torch.cat([generated, next_token], dim=1)
        generated_tokens_count += 1
        if eos_token_id is not None and next_id == int(eos_token_id):
            break
    end_time = time.time()
    time_taken = end_time - start_time
    tokens_per_second = generated_tokens_count / time_taken if time_taken > 0 else 0.0
    print(f"speed: {tokens_per_second:.2f} tokens/s (generated {generated_tokens_count} tokens in {time_taken:.2f} seconds)")
    gen_ids = generated[0].tolist()[len(input_ids):]
    text = safe_decode_ids(tokenizer, gen_ids, skip_special_tokens=False)
    text = filter_generated_text(text)

    # tab 训练格式下，只保留 password 部分
    if prompt_mode == "tab":
        if "\t" in text:
            text = text.split("\t", 1)[0].strip()

    return text


# =========================
# patterns 分配逻辑
# =========================
def read_patterns_and_allocate(patterns_file: str, total_generate: int) -> pd.DataFrame:
    if not os.path.exists(patterns_file):
        raise FileNotFoundError(f"Patterns file not found: {patterns_file}")

    df = pd.read_table(
        patterns_file,
        sep="\t",
        header=None,
        names=["pattern", "ratio"],
        dtype={0: str, 1: float},
    )

    df["pattern"] = df["pattern"].map(lambda x: str(x).strip())
    df["ratio"] = df["ratio"].astype(float)
    df = df[df["ratio"] > 0].copy()

    df["PwNum"] = (df["ratio"] * total_generate).astype(int)

    diff = total_generate - int(df["PwNum"].sum())
    if diff > 0:
        idxs = df["ratio"].sort_values(ascending=False).index[:diff]
        df.loc[idxs, "PwNum"] += 1
    elif diff < 0:
        idxs = df["PwNum"].sort_values(ascending=False).index[:abs(diff)]
        df.loc[idxs, "PwNum"] -= 1

    assert int(df["PwNum"].sum()) == total_generate
    return df


# =========================
# 主函数
# =========================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", type=str, default=MODEL_DIR)
    parser.add_argument("--patterns_file", type=str, default=PATTERNS_FILE)
    parser.add_argument("--output_file", type=str, default=OUTPUT_FILE)
    parser.add_argument("--total_generate", type=int, default=TOTAL_GENERATE)
    parser.add_argument("--prompt_mode", type=str, default=PROMPT_MODE, choices=["tab", "pat_sep"])
    parser.add_argument("--max_length", type=int, default=MAX_LENGTH)
    parser.add_argument("--max_new_tokens", type=int, default=MAX_NEW_TOKENS)
    parser.add_argument("--temperature", type=float, default=TEMPERATURE)
    parser.add_argument("--top_k", type=int, default=TOP_K)
    parser.add_argument("--top_p", type=float, default=TOP_P)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--device", type=str, default="cuda:0")
    parser.add_argument(
        "--validate_simple_pattern",
        action="store_true",
        help="仅对简单 L/N/S/U/l 模式启用弱校验；复杂 W/K/Lf/Nf 等模式不建议开启",
    )
    parser.add_argument("--max_retry_factor", type=int, default=10, help="每个 pattern 最大尝试倍数")
    args = parser.parse_args()

    set_seed(args.seed)

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        print("[Warning] CUDA 不可用，切换到 CPU")
        device = "cpu"

    print("Loading tokenizer...")
    tokenizer = load_tokenizer(args.model_dir)
    print("Tokenizer vocab size:", tokenizer.vocab_size)

    print("Loading model...")
    model = load_model(args.model_dir, device=device)
    print("Model loaded from:", args.model_dir)

    print("Reading patterns...")
    df = read_patterns_and_allocate(args.patterns_file, args.total_generate)

    out_dir = os.path.dirname(args.output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    total_written = 0
    empty_count = 0
    mismatch_count = 0
    incomplete_patterns = 0

    with open(args.output_file, "w", encoding="utf-8") as f:
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating"):
            pattern = row["pattern"]
            target_num = int(row["PwNum"])

            if target_num <= 0:
                continue

            written_for_pattern = 0
            attempts = 0
            max_attempts = max(target_num * args.max_retry_factor, 20)

            while written_for_pattern < target_num and attempts < max_attempts:
                attempts += 1

                pwd = generate_one(
                    pattern=pattern,
                    model=model,
                    tokenizer=tokenizer,
                    device=device,
                    prompt_mode=args.prompt_mode,
                    max_new_tokens=args.max_new_tokens,
                    max_length=args.max_length,
                    temperature=args.temperature,
                    top_k=args.top_k,
                    top_p=args.top_p,
                )

                if pwd == "":
                    empty_count += 1
                    continue

                if args.validate_simple_pattern:
                    if not match_simple_pattern(pwd, pattern):
                        mismatch_count += 1
                        continue

                f.write(f"{pattern}\t{pwd}\n")
                total_written += 1
                written_for_pattern += 1

            if written_for_pattern < target_num:
                incomplete_patterns += 1
                print(
                    f"[Warn] pattern={pattern} target={target_num} written={written_for_pattern} "
                    f"attempts={attempts}"
                )

    print(f"[Done] output_file = {args.output_file}")
    print(f"[Done] total_written = {total_written}")
    print(f"[Stats] empty_count = {empty_count}")
    print(f"[Stats] mismatch_count = {mismatch_count}")
    print(f"[Stats] incomplete_patterns = {incomplete_patterns}")


if __name__ == "__main__":
    main()