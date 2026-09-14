"""Generate hardware-facing model_config.json.

This is intentionally small: it reads a local HuggingFace config, resolves the
common HuggingFace cache layout, and records only the model facts needed by the
current accelerator framework.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def required_int(config: dict[str, Any], key: str) -> int:
    value = config.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"missing or invalid integer field: {key}")
    if value <= 0:
        raise ConfigError(f"{key} must be positive, got {value}")
    return value


def resolve_model_dir(model_dir: Path) -> Path:
    """Return a directory that contains config.json.

    Supports both ordinary model directories and HF cache roots such as:
    ~/.cache/huggingface/hub/models--facebook--opt-125m
    """
    if (model_dir / "config.json").exists():
        return model_dir

    refs_main = model_dir / "refs" / "main"
    if refs_main.exists():
        commit = refs_main.read_text(encoding="utf-8").strip()
        snapshot_dir = model_dir / "snapshots" / commit
        if (snapshot_dir / "config.json").exists():
            return snapshot_dir

    candidates = sorted((model_dir / "snapshots").glob("*/config.json"))
    if candidates:
        return candidates[-1].parent

    raise ConfigError(f"cannot find config.json under model directory: {model_dir}")


def head_dim(hidden_size: int, num_heads: int) -> int:
    if hidden_size % num_heads != 0:
        raise ConfigError(f"hidden_size {hidden_size} not divisible by heads {num_heads}")
    return hidden_size // num_heads


def model_head_dim(config: dict[str, Any], hidden_size: int, num_heads: int) -> int:
    value = config.get("head_dim")
    if value is None:
        return head_dim(hidden_size, num_heads)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError("invalid head_dim")
    return value


def attention_kind(num_q_heads: int, num_kv_heads: int) -> str:
    if num_q_heads % num_kv_heads != 0:
        raise ConfigError(
            f"num_attention_heads {num_q_heads} not divisible by num_key_value_heads {num_kv_heads}"
        )
    if num_q_heads == num_kv_heads:
        return "mha"
    if num_kv_heads == 1:
        return "mqa"
    return "gqa"


def opt_operator_sequence(pre_norm: bool) -> list[str]:
    if pre_norm:
        return [
            "layer_norm_1",
            "self_attention",
            "residual_add_1",
            "layer_norm_2",
            "mlp_fc1",
            "activation",
            "mlp_fc2",
            "residual_add_2",
        ]
    return [
        "self_attention",
        "residual_add_1",
        "layer_norm_1",
        "mlp_fc1",
        "activation",
        "mlp_fc2",
        "residual_add_2",
        "layer_norm_2",
    ]


def gpt2_operator_sequence() -> list[str]:
    return [
        "layer_norm_1",
        "self_attention",
        "residual_add_1",
        "layer_norm_2",
        "mlp_fc",
        "activation",
        "mlp_proj",
        "residual_add_2",
    ]


def qwen2_operator_sequence() -> list[str]:
    return [
        "rms_norm_1",
        "self_attention",
        "residual_add_1",
        "rms_norm_2",
        "mlp_gate_proj",
        "mlp_up_proj",
        "activation_mul",
        "mlp_down_proj",
        "residual_add_2",
    ]


def gemma3_operator_sequence() -> list[str]:
    return [
        "rms_norm_input",
        "self_attention",
        "rms_norm_post_attention",
        "residual_add_1",
        "rms_norm_pre_ffn",
        "mlp_gate_proj",
        "mlp_up_proj",
        "activation_mul",
        "mlp_down_proj",
        "rms_norm_post_ffn",
        "residual_add_2",
    ]


def llama_operator_sequence() -> list[str]:
    return [
        "rms_norm_1",
        "self_attention",
        "residual_add_1",
        "rms_norm_2",
        "mlp_gate_proj",
        "mlp_up_proj",
        "activation_mul",
        "mlp_down_proj",
        "residual_add_2",
    ]


def normalize_opt(config: dict[str, Any], target_seq: int) -> dict[str, Any]:
    hidden_size = required_int(config, "hidden_size")
    num_heads = required_int(config, "num_attention_heads")
    pre_norm = bool(config.get("do_layer_norm_before", True))
    enable_bias = bool(config.get("enable_bias", True))
    norm_affine = bool(config.get("layer_norm_elementwise_affine", True))

    return {
        "model_type": "opt",
        "num_layers": required_int(config, "num_hidden_layers"),
        "hidden_size": hidden_size,
        "target_max_seq_len": target_seq,
        "block": {
            "type": "decoder",
            "operator_sequence": opt_operator_sequence(pre_norm),
        },
        "attention": {
            "kind": "mha",
            "num_q_heads": num_heads,
            "num_kv_heads": num_heads,
            "head_dim": head_dim(hidden_size, num_heads),
            "causal": True,
            "position_encoding": {"type": "learned_absolute"},
            "qkv_bias": enable_bias,
            "out_bias": enable_bias,
        },
        "norm": {
            "type": "layer_norm",
            "position": "pre" if pre_norm else "post",
            "eps": float(config.get("layer_norm_eps", 1e-5)),
            "has_bias": norm_affine,
        },
        "mlp": {
            "type": "dense",
            "intermediate_size": required_int(config, "ffn_dim"),
            "activation": str(config.get("activation_function", "relu")),
            "up_bias": enable_bias,
            "down_bias": enable_bias,
        },
        "weight_layout": {
            "qkv": "separate_q_k_v",
            "out_proj": "dense",
            "mlp": "fc1_fc2",
            "norm": "weight_bias" if norm_affine else "none",
        },
    }


def normalize_gpt2(config: dict[str, Any], target_seq: int) -> dict[str, Any]:
    if bool(config.get("add_cross_attention", False)):
        raise ConfigError("minimal extractor only supports GPT2 self-attention blocks")

    hidden_size = required_int(config, "n_embd")
    num_heads = required_int(config, "n_head")
    intermediate_size = config.get("n_inner") or (4 * hidden_size)
    if not isinstance(intermediate_size, int) or intermediate_size <= 0:
        raise ConfigError("invalid GPT2 n_inner/intermediate size")

    return {
        "model_type": "gpt2",
        "num_layers": required_int(config, "n_layer"),
        "hidden_size": hidden_size,
        "target_max_seq_len": target_seq,
        "block": {
            "type": "decoder",
            "operator_sequence": gpt2_operator_sequence(),
        },
        "attention": {
            "kind": "mha",
            "num_q_heads": num_heads,
            "num_kv_heads": num_heads,
            "head_dim": head_dim(hidden_size, num_heads),
            "causal": True,
            "position_encoding": {"type": "learned_absolute"},
            "qkv_bias": True,
            "out_bias": True,
        },
        "norm": {
            "type": "layer_norm",
            "position": "pre",
            "eps": float(config.get("layer_norm_epsilon", 1e-5)),
            "has_bias": True,
        },
        "mlp": {
            "type": "dense",
            "intermediate_size": intermediate_size,
            "activation": str(config.get("activation_function", "gelu_new")),
            "up_bias": True,
            "down_bias": True,
        },
        "weight_layout": {
            "qkv": "fused_qkv",
            "out_proj": "dense",
            "mlp": "c_fc_c_proj",
            "norm": "weight_bias",
        },
    }


def normalize_qwen2(config: dict[str, Any], target_seq: int) -> dict[str, Any]:
    hidden_size = required_int(config, "hidden_size")
    num_heads = required_int(config, "num_attention_heads")
    num_kv_heads = required_int(config, "num_key_value_heads")
    attn_head_dim = model_head_dim(config, hidden_size, num_heads)

    return {
        "model_type": "qwen2",
        "num_layers": required_int(config, "num_hidden_layers"),
        "hidden_size": hidden_size,
        "target_max_seq_len": target_seq,
        "block": {
            "type": "decoder",
            "operator_sequence": qwen2_operator_sequence(),
        },
        "attention": {
            "kind": attention_kind(num_heads, num_kv_heads),
            "num_q_heads": num_heads,
            "num_kv_heads": num_kv_heads,
            "head_dim": attn_head_dim,
            "causal": True,
            "position_encoding": {
                "type": "rope",
                "rope_theta": config.get("rope_theta", 10000.0),
            },
            "qkv_bias": True,
            "out_bias": False,
        },
        "norm": {
            "type": "rms_norm",
            "position": "pre",
            "eps": float(config.get("rms_norm_eps", 1e-6)),
            "has_bias": False,
        },
        "mlp": {
            "type": "gated",
            "intermediate_size": required_int(config, "intermediate_size"),
            "activation": str(config.get("hidden_act", "silu")),
            "up_bias": False,
            "down_bias": False,
        },
        "weight_layout": {
            "qkv": "separate_q_k_v",
            "out_proj": "dense",
            "mlp": "gate_up_down",
            "norm": "weight_only",
        },
    }


def normalize_gemma3_text(config: dict[str, Any], target_seq: int) -> dict[str, Any]:
    hidden_size = required_int(config, "hidden_size")
    num_heads = required_int(config, "num_attention_heads")
    num_kv_heads = required_int(config, "num_key_value_heads")
    attn_head_dim = model_head_dim(config, hidden_size, num_heads)
    attention_bias = bool(config.get("attention_bias", False))

    position_encoding = {
        "type": "rope",
        "rope_theta": config.get("rope_theta", 10000),
    }
    if "rope_local_base_freq" in config:
        position_encoding["rope_local_base_freq"] = config["rope_local_base_freq"]

    attention = {
        "kind": attention_kind(num_heads, num_kv_heads),
        "num_q_heads": num_heads,
        "num_kv_heads": num_kv_heads,
        "head_dim": attn_head_dim,
        "causal": True,
        "position_encoding": position_encoding,
        "qkv_bias": attention_bias,
        "out_bias": attention_bias,
        "qk_norm": True,
    }
    if "sliding_window" in config:
        attention["sliding_window"] = config["sliding_window"]
    if "sliding_window_pattern" in config:
        attention["sliding_window_pattern"] = config["sliding_window_pattern"]

    return {
        "model_type": "gemma3_text",
        "num_layers": required_int(config, "num_hidden_layers"),
        "hidden_size": hidden_size,
        "target_max_seq_len": target_seq,
        "block": {
            "type": "decoder",
            "operator_sequence": gemma3_operator_sequence(),
        },
        "attention": attention,
        "norm": {
            "type": "rms_norm",
            "position": "pre",
            "eps": float(config.get("rms_norm_eps", 1e-6)),
            "has_bias": False,
        },
        "mlp": {
            "type": "gated",
            "intermediate_size": required_int(config, "intermediate_size"),
            "activation": str(config.get("hidden_activation", "gelu_pytorch_tanh")),
            "up_bias": False,
            "down_bias": False,
        },
        "weight_layout": {
            "qkv": "separate_q_k_v",
            "out_proj": "dense",
            "mlp": "gate_up_down",
            "norm": "weight_only",
        },
    }


def normalize_llama(config: dict[str, Any], target_seq: int) -> dict[str, Any]:
    hidden_size = required_int(config, "hidden_size")
    num_heads = required_int(config, "num_attention_heads")
    num_kv_heads = int(config.get("num_key_value_heads", num_heads))
    attn_head_dim = model_head_dim(config, hidden_size, num_heads)

    position_encoding = {
        "type": "rope",
        "rope_theta": config.get("rope_theta", 10000.0),
    }
    if config.get("rope_scaling") is not None:
        position_encoding["rope_scaling"] = config["rope_scaling"]

    attention_bias = bool(config.get("attention_bias", False))
    mlp_bias = bool(config.get("mlp_bias", False))

    return {
        "model_type": "llama",
        "num_layers": required_int(config, "num_hidden_layers"),
        "hidden_size": hidden_size,
        "target_max_seq_len": target_seq,
        "block": {
            "type": "decoder",
            "operator_sequence": llama_operator_sequence(),
        },
        "attention": {
            "kind": attention_kind(num_heads, num_kv_heads),
            "num_q_heads": num_heads,
            "num_kv_heads": num_kv_heads,
            "head_dim": attn_head_dim,
            "causal": True,
            "position_encoding": position_encoding,
            "qkv_bias": attention_bias,
            "out_bias": attention_bias,
        },
        "norm": {
            "type": "rms_norm",
            "position": "pre",
            "eps": float(config.get("rms_norm_eps", 1e-5)),
            "has_bias": False,
        },
        "mlp": {
            "type": "gated",
            "intermediate_size": required_int(config, "intermediate_size"),
            "activation": str(config.get("hidden_act", "silu")),
            "up_bias": mlp_bias,
            "down_bias": mlp_bias,
        },
        "weight_layout": {
            "qkv": "separate_q_k_v",
            "out_proj": "dense",
            "mlp": "gate_up_down",
            "norm": "weight_only",
        },
    }


def normalize(config: dict[str, Any], target_seq: int, family: str) -> dict[str, Any]:
    if target_seq <= 0:
        raise ConfigError("--target-seq must be positive")

    model_type = infer_family_from_config(config) if family == "auto" else family.lower()

    if model_type == "opt":
        return normalize_opt(config, target_seq)
    if model_type == "gpt2":
        return normalize_gpt2(config, target_seq)
    if model_type == "qwen2":
        return normalize_qwen2(config, target_seq)
    if model_type == "gemma3_text":
        return normalize_gemma3_text(config, target_seq)
    if model_type == "llama":
        return normalize_llama(config, target_seq)
    raise ConfigError(f"unsupported minimal model_type: {model_type}")


def infer_family_from_config(config: dict[str, Any]) -> str:
    model_type = str(config.get("model_type", "")).lower()
    if model_type:
        return model_type
    architectures = config.get("architectures", [])
    if isinstance(architectures, list) and architectures:
        arch = str(architectures[0]).lower()
        if "opt" in arch:
            return "opt"
        if "gpt2" in arch:
            return "gpt2"
        if "qwen2" in arch:
            return "qwen2"
        if "gemma3" in arch:
            return "gemma3_text"
        if "llama" in arch or "tinyllama" in arch:
            return "llama"
    raise ConfigError("cannot infer family from config")


def extraction_report(
    config_path: Path,
    model_config: dict[str, Any],
    family: str,
) -> dict[str, Any]:
    source_class = {
        "opt": "transformers.models.opt.modeling_opt.OPTDecoderLayer",
        "gpt2": "transformers.models.gpt2.modeling_gpt2.GPT2Block",
        "qwen2": "transformers.models.qwen2.modeling_qwen2.Qwen2DecoderLayer",
        "llama": "transformers.models.llama.modeling_llama.LlamaDecoderLayer",
        "gemma3_text": "transformers.models.gemma3.modeling_gemma3.Gemma3DecoderLayer",
    }.get(model_config["model_type"], "")
    return {
        "schema_version": "spatialaccagent.model_config_extraction_report.v0",
        "config_path": str(config_path),
        "requested_family": family,
        "resolved_model_type": model_config["model_type"],
        "operator_sequence_source": source_class,
        "note": "Only audit/provenance lives here. Hardware binding should read model_config.json.",
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate model_config.json")
    parser.add_argument("--model-dir", type=Path, help="HF model directory or HF cache root")
    parser.add_argument("--config", type=Path, help="Explicit config.json path")
    parser.add_argument("--family", default="auto", help="auto, opt, gpt2, llama, qwen2, or gemma3_text")
    parser.add_argument("--target-seq", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.config is None and args.model_dir is None:
        print("error: either --config or --model-dir is required", file=sys.stderr)
        return 2

    try:
        if args.config is not None:
            config_path = args.config
        else:
            config_path = resolve_model_dir(args.model_dir) / "config.json"
        raw_config = read_json(config_path)
        model_config = normalize(raw_config, args.target_seq, args.family)
        report_path = args.report or args.out.with_name("model_config_extraction_report.json")
        write_json(args.out, model_config)
        write_json(report_path, extraction_report(config_path, model_config, args.family))
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
