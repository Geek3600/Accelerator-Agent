#!/usr/bin/env python3
"""Build the complete real-checkpoint catalog for the built-in Qwen2 adapter.

The script deliberately uses only the Python standard library for safetensors
metadata parsing. The complete tensor catalog and source hashes are acceptance
evidence. Legacy packed input/prefetch files remain diagnostic-only and cannot
prove complete DUT weight consumption.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import struct
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_ID = "Qwen/Qwen2-0.5B"
DEFAULT_MODEL_CACHE = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen2-0.5B"
REQUIRED_TENSORS = [
    "model.embed_tokens.weight",
    "model.norm.weight",
    "model.layers.0.input_layernorm.weight",
    "model.layers.0.post_attention_layernorm.weight",
    "model.layers.0.self_attn.q_proj.weight",
    "model.layers.0.self_attn.k_proj.weight",
    "model.layers.0.self_attn.v_proj.weight",
    "model.layers.0.self_attn.o_proj.weight",
    "model.layers.0.mlp.gate_proj.weight",
    "model.layers.0.mlp.up_proj.weight",
    "model.layers.0.mlp.down_proj.weight",
]


class ManifestError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ManifestError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def resolve_snapshot(path: Path) -> tuple[Path, str | None]:
    path = path.expanduser().resolve()
    if (path / "config.json").exists():
        return path, path.name

    refs_main = path / "refs" / "main"
    if refs_main.exists():
        revision = refs_main.read_text(encoding="utf-8").strip()
        snapshot = path / "snapshots" / revision
        if (snapshot / "config.json").exists():
            return snapshot.resolve(), revision

    candidates = sorted((path / "snapshots").glob("*/config.json"))
    if candidates:
        snapshot = candidates[-1].parent.resolve()
        return snapshot, snapshot.name

    raise ManifestError(f"cannot resolve HF snapshot with config.json under {path}")


def parse_safetensors(path: Path) -> dict[str, Any]:
    file_size = path.stat().st_size
    with path.open("rb") as f:
        raw_len = f.read(8)
        if len(raw_len) != 8:
            raise ManifestError(f"{path} is too small for safetensors header")
        (header_len,) = struct.unpack("<Q", raw_len)
        if header_len <= 0 or header_len > file_size - 8:
            raise ManifestError(f"invalid safetensors header length {header_len} for {path}")
        header_raw = f.read(header_len)
    try:
        header = json.loads(header_raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"safetensors header JSON parse failed for {path}: {exc}") from exc
    if not isinstance(header, dict):
        raise ManifestError(f"safetensors header is not an object: {path}")

    metadata = header.get("__metadata__", {})
    tensors = {name: value for name, value in header.items() if name != "__metadata__"}
    dtype_counts: dict[str, int] = {}
    layer_ids: set[int] = set()
    max_data_end = 0
    param_count = 0
    bad_offsets: list[str] = []
    examples: list[dict[str, Any]] = []
    tensor_catalog: list[dict[str, Any]] = []
    required_tensor_slices: list[dict[str, Any]] = []

    for name, item in sorted(tensors.items()):
        if not isinstance(item, dict):
            raise ManifestError(f"tensor entry is not an object: {name}")
        dtype = str(item.get("dtype"))
        shape = item.get("shape", [])
        offsets = item.get("data_offsets", [])
        if not isinstance(shape, list) or not all(isinstance(dim, int) and dim >= 0 for dim in shape):
            raise ManifestError(f"invalid tensor shape for {name}: {shape}")
        if not isinstance(offsets, list) or len(offsets) != 2 or not all(isinstance(v, int) for v in offsets):
            raise ManifestError(f"invalid tensor data_offsets for {name}: {offsets}")
        start, end = offsets
        if start < 0 or end < start:
            bad_offsets.append(name)
        max_data_end = max(max_data_end, end)
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
        param_count += math.prod(shape) if shape else 1
        match = re.match(r"model\.layers\.(\d+)\.", name)
        if match:
            layer_ids.add(int(match.group(1)))
        if len(examples) < 24:
            examples.append({"name": name, "dtype": dtype, "shape": shape, "data_offsets": offsets})
        tensor_catalog.append({"name": name, "dtype": dtype, "shape": shape, "data_offsets": offsets})
        if name in REQUIRED_TENSORS:
            required_tensor_slices.append({"name": name, "dtype": dtype, "shape": shape, "data_offsets": offsets})

    expected_size = 8 + header_len + max_data_end
    if expected_size != file_size:
        bad_offsets.append(f"max_data_end_expected_file_size={expected_size}, actual={file_size}")

    missing_required = [name for name in REQUIRED_TENSORS if name not in tensors]
    return {
        "format": "safetensors",
        "metadata": metadata,
        "header_len": header_len,
        "tensor_count": len(tensors),
        "param_count": param_count,
        "dtype_counts": dtype_counts,
        "layer_ids": sorted(layer_ids),
        "max_data_end": max_data_end,
        "expected_file_size": expected_size,
        "actual_file_size": file_size,
        "offsets_valid": not bad_offsets,
        "bad_offsets": bad_offsets,
        "missing_required_tensors": missing_required,
        "required_tensors_present": not missing_required,
        "required_tensor_slices": required_tensor_slices,
        "tensor_catalog": tensor_catalog,
        "tensor_examples": examples,
    }


def transformer_block_scope(tensors: list[dict[str, Any]], num_layers: int) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    excluded: list[str] = []
    suffixes_by_layer: dict[int, set[str]] = {}
    for row in tensors:
        name = str(row.get("name") or "")
        match = re.fullmatch(r"model\.layers\.(\d+)\.(.+)", name)
        if not match:
            excluded.append(name)
            continue
        layer_index = int(match.group(1))
        if layer_index >= num_layers:
            excluded.append(name)
            continue
        selected.append(dict(row))
        suffixes_by_layer.setdefault(layer_index, set()).add(match.group(2))
    expected_layers = list(range(num_layers))
    layer_ids = sorted(suffixes_by_layer)
    baseline = suffixes_by_layer.get(0, set())
    inconsistent_layers = [
        layer_index
        for layer_index in expected_layers
        if suffixes_by_layer.get(layer_index, set()) != baseline
    ]
    return {
        "accelerator_scope": "transformer_blocks_only",
        "target_layer_count": num_layers,
        "layer_ids": layer_ids,
        "tensor_count": len(selected),
        "per_layer_tensor_count": len(baseline),
        "tensor_suffixes": sorted(baseline),
        "scope_coverage_complete": bool(baseline) and layer_ids == expected_layers and not inconsistent_layers,
        "inconsistent_layers": inconsistent_layers,
        "tensors": selected,
        "excluded_non_accelerator_tensors": sorted(excluded),
    }


def hash_tensor_slices(path: Path, header_len: int, tensors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data_base = 8 + header_len
    rows: list[dict[str, Any]] = []
    with path.open("rb") as stream:
        for row in tensors:
            start, end = [int(value) for value in row["data_offsets"]]
            stream.seek(data_base + start)
            remaining = end - start
            digest = hashlib.sha256()
            while remaining > 0:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise ManifestError(f"short read while hashing tensor {row.get('name')}")
                digest.update(chunk)
                remaining -= len(chunk)
            rows.append(
                {
                    **row,
                    "source_byte_count": end - start,
                    "source_slice_sha256": digest.hexdigest(),
                }
            )
    return rows


def file_info(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "realpath": str(path.resolve()),
        "size_bytes": path.stat().st_size,
    }


def tokenizer_info(snapshot: Path) -> dict[str, Any]:
    info: dict[str, Any] = {}
    for name in ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"]:
        path = snapshot / name
        if path.exists():
            info[name] = file_info(path)
    cfg_path = snapshot / "tokenizer_config.json"
    if cfg_path.exists():
        cfg = read_json(cfg_path)
        info["tokenizer_class"] = cfg.get("tokenizer_class")
    return info


def build_memory_layout(run_dir: Path, manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    config = manifest["config"]
    return {
        "schema_version": "spatialaccagent.qwen_real_memory_layout.v0",
        "policy": "qwen2_hf_safetensors_static_tensor_catalog",
        "model_id": manifest["model_id"],
        "revision": manifest["snapshot"]["revision"],
        "manifest": str(manifest_path),
        "packing_status": "tensor_catalog_ready_packed_ddr_image_pending",
        "tensor_catalog": {
            "format": "safetensors",
            "dtype_counts": manifest["weights"]["dtype_counts"],
            "tensor_count": manifest["weights"]["tensor_count"],
            "param_count": manifest["weights"]["param_count"],
        },
        "model_shape": {
            "hidden_size": config.get("hidden_size"),
            "intermediate_size": config.get("intermediate_size"),
            "num_hidden_layers": config.get("num_hidden_layers"),
            "num_attention_heads": config.get("num_attention_heads"),
            "num_key_value_heads": config.get("num_key_value_heads"),
            "vocab_size": config.get("vocab_size"),
        },
        "regions": [
            {"name": "input_activation", "base": "0x00000000", "owner": "runtime"},
            {"name": "qwen2_weights", "base": "0x10000000", "owner": "hf_safetensors_weight_loader"},
            {"name": "kv_cache", "base": "0x18000000", "owner": "runtime"},
            {"name": "output_activation", "base": "0x20000000", "owner": "runtime"},
        ],
        "constraints": ["constraint.memory.board", "constraint.runtime.board", "constraint.codegen.package"],
    }


def generated_run_params(run_dir: Path, config: dict[str, Any]) -> dict[str, int]:
    params_scala = run_dir / "generated" / "chisel" / "src" / "main" / "scala" / "spatialaccagent" / "generated" / "GeneratedDesignParams.scala"
    params_text = params_scala.read_text(encoding="utf-8", errors="ignore") if params_scala.exists() else ""
    model_path = run_dir / "input" / "model_config.json"
    model = read_json(model_path) if model_path.exists() else {}

    def from_scala(name: str, default: int) -> int:
        match = re.search(rf"{re.escape(name)}\s*=\s*(\d+)", params_text)
        return int(match.group(1)) if match else default

    hidden_size = int(model.get("hidden_size") or config.get("hidden_size") or from_scala("hiddenSize", 896))
    seq_len = int(model.get("target_max_seq_len") or from_scala("targetMaxSeqLen", 16))
    lanes = from_scala("lanes", 8)
    return {
        "hidden_size": hidden_size,
        "target_max_seq_len": seq_len,
        "lanes": lanes,
        "stream_beats": seq_len * max(1, hidden_size // max(1, lanes)),
        "axi_data_width_bits": 256,
    }


def write_memh(path: Path, words: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for word in words:
            f.write(f"{word & 0xFFFFFFFF:08x}\n")


def direct_vocab_tokens(snapshot: Path) -> list[dict[str, Any]]:
    vocab_path = snapshot / "vocab.json"
    vocab = read_json(vocab_path)
    token_strings = ["Hello", "Ġworld", "!", "ĠQwen", "ĠFPGA", "Ġaccelerator", "."]
    tokens = []
    for token in token_strings:
        token_id = vocab.get(token)
        if isinstance(token_id, int):
            tokens.append({"token": token, "id": token_id})
    if len(tokens) < 3:
        raise ManifestError(f"Qwen vocab does not contain enough direct prompt tokens in {vocab_path}")
    return tokens


def build_input_activation_words(tokens: list[dict[str, Any]], params: dict[str, int]) -> list[int]:
    seq_len = params["target_max_seq_len"]
    hidden_size = params["hidden_size"]
    lanes = params["lanes"]
    beats_per_token = max(1, hidden_size // max(1, lanes))
    words: list[int] = []
    for token_index in range(seq_len):
        token_id = int(tokens[token_index % len(tokens)]["id"])
        for beat in range(beats_per_token):
            for lane in range(lanes):
                word = (token_id & 0xFFFFF) | ((lane & 0xF) << 20) | ((beat & 0xFF) << 24)
                words.append(word)
    return words


def u32_words_from_bytes(raw: bytes) -> list[int]:
    words = []
    for idx in range(0, len(raw), 4):
        chunk = raw[idx : idx + 4]
        if len(chunk) < 4:
            chunk = chunk + b"\x00" * (4 - len(chunk))
        words.append(int.from_bytes(chunk, byteorder="little", signed=False))
    return words


def build_weight_prefetch_words(manifest: dict[str, Any], max_words: int = 8192) -> tuple[list[int], list[dict[str, Any]]]:
    weights_path = Path(manifest["weights"]["path"])
    data_base = 8 + int(manifest["weights"]["header_len"])
    words: list[int] = []
    slices: list[dict[str, Any]] = []
    per_tensor_bytes = 4096
    with weights_path.open("rb") as f:
        for item in manifest.get("required_tensor_slices", []):
            if len(words) >= max_words:
                break
            start, end = item["data_offsets"]
            byte_count = min(per_tensor_bytes, max(0, int(end) - int(start)), (max_words - len(words)) * 4)
            if byte_count <= 0:
                continue
            f.seek(data_base + int(start))
            raw = f.read(byte_count)
            offset_words = len(words)
            new_words = u32_words_from_bytes(raw)
            words.extend(new_words)
            slices.append(
                {
                    "tensor": item["name"],
                    "dtype": item["dtype"],
                    "shape": item["shape"],
                    "source_data_offsets": item["data_offsets"],
                    "packed_word_offset": offset_words,
                    "packed_words": len(new_words),
                }
            )
    if not words:
        raise ManifestError("no real Qwen weight bytes were packed into the DDR prefetch image")
    return words[:max_words], slices


def write_stage7_ddr_artifacts(run_dir: Path, manifest: dict[str, Any], snapshot: Path) -> dict[str, Any]:
    evidence_dir = run_dir / "verification" / "qwen_real_weights"
    params = generated_run_params(run_dir, manifest["config"])
    tokens = direct_vocab_tokens(snapshot)
    input_words = build_input_activation_words(tokens, params)
    weight_words, packed_slices = build_weight_prefetch_words(manifest)
    input_memh = evidence_dir / "input_activation.u32.memh"
    weight_memh = evidence_dir / "weight_prefetch.u32.memh"
    write_memh(input_memh, input_words)
    write_memh(weight_memh, weight_words)
    return {
        "params": params,
        "tokens": tokens,
        "input_memh": input_memh,
        "input_words": len(input_words),
        "weight_memh": weight_memh,
        "weight_words": len(weight_words),
        "packed_weight_slices": packed_slices,
    }


def build_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    snapshot, revision = resolve_snapshot(args.model_dir)
    config_path = snapshot / "config.json"
    weights_path = snapshot / args.weights_name
    if not config_path.exists():
        raise ManifestError(f"missing config.json: {config_path}")
    if not weights_path.exists():
        raise ManifestError(f"missing Qwen weights: {weights_path}")

    config = read_json(config_path)
    tensor_meta = parse_safetensors(weights_path)
    if not tensor_meta["offsets_valid"]:
        raise ManifestError(f"safetensors offsets are invalid: {tensor_meta['bad_offsets']}")
    if not tensor_meta["required_tensors_present"]:
        raise ManifestError(f"required Qwen tensors missing: {tensor_meta['missing_required_tensors']}")

    num_layers = int(config.get("num_hidden_layers") or 0)
    accelerator_scope = transformer_block_scope(tensor_meta["tensor_catalog"], num_layers)
    if not accelerator_scope["scope_coverage_complete"]:
        raise ManifestError(
            "transformer-block weight scope is incomplete: "
            f"layers={accelerator_scope['layer_ids']} inconsistent={accelerator_scope['inconsistent_layers']}"
        )

    manifest = {
        "schema_version": "spatialaccagent.qwen_real_weight_manifest.v0",
        "status": "pass",
        "gate": "qwen_real_weight_artifacts",
        "model_id": args.model_id,
        "snapshot": {
            "revision": revision,
            "snapshot_dir": str(snapshot),
        },
        "weights": {
            **file_info(weights_path),
            "format": tensor_meta["format"],
            "metadata": tensor_meta["metadata"],
            "tensor_count": tensor_meta["tensor_count"],
            "param_count": tensor_meta["param_count"],
            "dtype_counts": tensor_meta["dtype_counts"],
            "layer_ids": tensor_meta["layer_ids"],
            "offsets_valid": tensor_meta["offsets_valid"],
            "header_len": tensor_meta["header_len"],
            "max_data_end": tensor_meta["max_data_end"],
            "safetensors_package_available": package_available("safetensors"),
            "torch_available": package_available("torch"),
            "direct_torch_loadable": False,
        },
        "config": {
            "path": str(config_path),
            "model_type": config.get("model_type"),
            "architectures": config.get("architectures"),
            "hidden_size": config.get("hidden_size"),
            "intermediate_size": config.get("intermediate_size"),
            "num_hidden_layers": config.get("num_hidden_layers"),
            "num_attention_heads": config.get("num_attention_heads"),
            "num_key_value_heads": config.get("num_key_value_heads"),
            "torch_dtype": config.get("torch_dtype"),
            "tie_word_embeddings": config.get("tie_word_embeddings"),
            "vocab_size": config.get("vocab_size"),
        },
        "tokenizer": tokenizer_info(snapshot),
        "required_tensor_examples": REQUIRED_TENSORS,
        "required_tensor_slices": tensor_meta["required_tensor_slices"],
        "tensor_catalog": tensor_meta["tensor_catalog"],
        "accelerator_scope": {
            key: value
            for key, value in accelerator_scope.items()
            if key not in {"tensors", "excluded_non_accelerator_tensors"}
        },
        "accelerator_tensor_catalog": accelerator_scope["tensors"],
        "excluded_non_accelerator_tensors": accelerator_scope["excluded_non_accelerator_tensors"],
        "tensor_examples": tensor_meta["tensor_examples"],
        "validation": {
            "config_is_qwen2": config.get("model_type") == "qwen2",
            "safetensors_header_json_valid": True,
            "safetensors_offsets_match_file_size": tensor_meta["expected_file_size"] == tensor_meta["actual_file_size"],
            "required_tensors_present": tensor_meta["required_tensors_present"],
            "layer_count_from_tensor_names": len(tensor_meta["layer_ids"]),
            "complete_checkpoint_tensor_catalog": len(tensor_meta["tensor_catalog"]) == tensor_meta["tensor_count"],
            "complete_accelerator_scope_tensor_catalog": accelerator_scope["scope_coverage_complete"],
            "accelerator_scope_is_transformer_blocks_only": accelerator_scope["accelerator_scope"] == "transformer_blocks_only",
        },
    }
    return manifest, snapshot


def default_out(args: argparse.Namespace) -> Path:
    if args.out:
        return args.out
    if args.run_dir:
        return args.run_dir / "generated" / "memory" / "qwen_real_weight_manifest.json"
    return REPO_ROOT / "verification" / "cases" / "qwen2_real_weights" / "resolved_manifest.json"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a real Qwen2 safetensors manifest")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--model-dir", type=Path, default=Path(os.environ.get("QWEN2_HF_CACHE", DEFAULT_MODEL_CACHE)))
    parser.add_argument("--weights-name", default="model.safetensors")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--write-repo-copy", action="store_true")
    parser.add_argument("--no-memory-layout", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.run_dir:
        args.run_dir = args.run_dir.resolve()
    out = default_out(args).resolve()
    manifest, snapshot = build_manifest(args)
    write_json(out, manifest)
    print(out)

    if args.run_dir and not args.no_memory_layout:
        ddr = write_stage7_ddr_artifacts(args.run_dir, manifest, snapshot)
        layout_path = args.run_dir / "generated" / "memory" / "memory_layout.json"
        write_json(layout_path, build_memory_layout(args.run_dir, out, manifest))
        print(layout_path)
        evidence_dir = args.run_dir / "verification" / "qwen_real_weights"
        canonical_manifest = evidence_dir / "weight_manifest.json"
        write_json(canonical_manifest, manifest)
        print(canonical_manifest)
        weights_path = Path(manifest["weights"]["path"])
        checkpoint_sha256 = sha256_file(weights_path)
        accelerator_tensor_rows = hash_tensor_slices(
            weights_path,
            int(manifest["weights"]["header_len"]),
            manifest.get("accelerator_tensor_catalog", []),
        )
        full_tensor_catalog_path = evidence_dir / "full_tensor_catalog.json"
        full_tensor_catalog = {
            "schema_version": "spatialaccagent.complete_checkpoint_tensor_catalog.v1",
            "status": "pass",
            "model_id": manifest["model_id"],
            "revision": manifest.get("snapshot", {}).get("revision"),
            "source_checkpoint": str(weights_path),
            "source_checkpoint_sha256": checkpoint_sha256,
            "tensor_count": manifest.get("weights", {}).get("tensor_count"),
            "layer_ids": manifest.get("weights", {}).get("layer_ids", []),
            "scope_coverage_complete": True,
            "catalog_scope": "complete_checkpoint_for_source_provenance",
            "tensors": manifest.get("tensor_catalog", []),
        }
        write_json(full_tensor_catalog_path, full_tensor_catalog)
        print(full_tensor_catalog_path)
        accelerator_tensor_catalog_path = evidence_dir / "transformer_block_weight_catalog.json"
        accelerator_tensor_catalog = {
            "schema_version": "spatialaccagent.transformer_block_weight_catalog.v1",
            "status": "pass",
            "model_id": manifest["model_id"],
            "revision": manifest.get("snapshot", {}).get("revision"),
            "source_checkpoint": str(weights_path),
            "source_checkpoint_sha256": checkpoint_sha256,
            **manifest.get("accelerator_scope", {}),
            "scope_coverage_complete": manifest.get("accelerator_scope", {}).get("scope_coverage_complete") is True,
            "tensors": accelerator_tensor_rows,
            "excluded_non_accelerator_tensors": manifest.get("excluded_non_accelerator_tensors", []),
            "policy": {
                "dut_must_consume_every_catalog_tensor": True,
                "embedding_final_norm_lm_head_are_out_of_scope": True,
                "complete_checkpoint_catalog_is_provenance_not_dut_consumption_scope": True,
            },
        }
        write_json(accelerator_tensor_catalog_path, accelerator_tensor_catalog)
        print(accelerator_tensor_catalog_path)
        input_manifest = {
            "schema_version": "spatialaccagent.qwen_real_input_manifest.v0",
            "status": "diagnostic_only",
            "model_id": manifest["model_id"],
            "tokenizer": manifest.get("tokenizer", {}),
            "tokenization": {
                "mode": "direct_qwen_vocab_token_sequence",
                "prompt": "Hello world! Qwen FPGA accelerator.",
                "tokens": ddr["tokens"],
                "note": "The generated core consumes activation streams, so Stage 7 packs a concrete activation DDR image derived from real Qwen vocab token ids rather than claiming numerical embedding equivalence.",
            },
            "activation_image": {
                "path": str(ddr["input_memh"]),
                "format": "readmemh_u32",
                "word_count": ddr["input_words"],
                "stream_beats": ddr["params"]["stream_beats"],
                "hidden_size": ddr["params"]["hidden_size"],
                "lanes": ddr["params"]["lanes"],
                "target_max_seq_len": ddr["params"]["target_max_seq_len"],
                "axi_data_width_bits": ddr["params"]["axi_data_width_bits"],
            },
            "acceptance_eligible": False,
            "note": "Legacy token-pattern activation image retained for path diagnostics only. Semantic acceptance uses model_reference/random_hidden_input.pt and target-model inference golden outputs.",
        }
        write_json(evidence_dir / "input_manifest.json", input_manifest)
        print(evidence_dir / "input_manifest.json")
        packed_weight_manifest = {
            "schema_version": "spatialaccagent.qwen_weight_prefetch_image.v0",
            "status": "incomplete",
            "model_id": manifest["model_id"],
            "source_weight_manifest": str(canonical_manifest),
            "image": {
                "path": str(ddr["weight_memh"]),
                "format": "readmemh_u32",
                "word_count": ddr["weight_words"],
                "axi_data_width_bits": ddr["params"]["axi_data_width_bits"],
            },
            "packed_slices": ddr["packed_weight_slices"],
            "scope_coverage_complete": False,
            "dut_consumption_proven": False,
            "acceptance_eligible": False,
            "note": "This image contains sampled safetensors bytes for path diagnostics. It cannot satisfy semantic or board-level real-weight acceptance.",
        }
        write_json(evidence_dir / "packed_weight_manifest.json", packed_weight_manifest)
        print(evidence_dir / "packed_weight_manifest.json")
        input_manifest_path = evidence_dir / "input_manifest.json"
        packed_weight_manifest_path = evidence_dir / "packed_weight_manifest.json"
        hashes = {
            "schema_version": "spatialaccagent.qwen_artifact_hashes.v0",
            "status": "pass",
            "artifacts": [
                {
                    "role": "hf_safetensors_weights",
                    "path": str(weights_path),
                    "size_bytes": weights_path.stat().st_size,
                    "sha256": checkpoint_sha256,
                },
                {
                    "role": "weight_manifest",
                    "path": str(canonical_manifest),
                    "size_bytes": canonical_manifest.stat().st_size,
                    "sha256": sha256_file(canonical_manifest),
                },
                {
                    "role": "complete_checkpoint_tensor_catalog",
                    "path": str(full_tensor_catalog_path),
                    "size_bytes": full_tensor_catalog_path.stat().st_size,
                    "sha256": sha256_file(full_tensor_catalog_path),
                },
                {
                    "role": "transformer_block_weight_catalog",
                    "path": str(accelerator_tensor_catalog_path),
                    "size_bytes": accelerator_tensor_catalog_path.stat().st_size,
                    "sha256": sha256_file(accelerator_tensor_catalog_path),
                },
                {
                    "role": "input_manifest",
                    "path": str(input_manifest_path),
                    "size_bytes": input_manifest_path.stat().st_size,
                    "sha256": sha256_file(input_manifest_path),
                },
                {
                    "role": "input_activation_memh",
                    "path": str(ddr["input_memh"]),
                    "size_bytes": ddr["input_memh"].stat().st_size,
                    "sha256": sha256_file(ddr["input_memh"]),
                },
                {
                    "role": "packed_weight_manifest",
                    "path": str(packed_weight_manifest_path),
                    "size_bytes": packed_weight_manifest_path.stat().st_size,
                    "sha256": sha256_file(packed_weight_manifest_path),
                },
                {
                    "role": "weight_prefetch_memh",
                    "path": str(ddr["weight_memh"]),
                    "size_bytes": ddr["weight_memh"].stat().st_size,
                    "sha256": sha256_file(ddr["weight_memh"]),
                },
            ],
        }
        write_json(evidence_dir / "artifact_hashes.json", hashes)
        print(evidence_dir / "artifact_hashes.json")

    if args.write_repo_copy and out != REPO_ROOT / "verification" / "cases" / "qwen2_real_weights" / "resolved_manifest.json":
        repo_copy = REPO_ROOT / "verification" / "cases" / "qwen2_real_weights" / "resolved_manifest.json"
        write_json(repo_copy, manifest)
        print(repo_copy)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ManifestError as exc:
        print(f"qwen_weight_manifest.py: {exc}", file=sys.stderr)
        raise SystemExit(1)
