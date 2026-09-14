#!/usr/bin/env python3
"""Build an independent single-layer golden stream from template semantics.

This is a case-adapter tool, not a framework-core shortcut. It derives the
reference from the generated template parameters and the adapter-provided input
activation image. It must not read the RTL output memh.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def adapter_paths(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "input" / "case_adapter.json"
    if not path.exists():
        return {}
    data = read_json(path)
    return data.get("paths", {}) if isinstance(data.get("paths"), dict) else {}


def resolve_input_manifest(run_dir: Path, paths: dict[str, Any]) -> Path:
    candidates = [
        Path(str(paths["input_manifest"])) if paths.get("input_manifest") else None,
        Path(str(paths["packed_input_manifest"])) if paths.get("packed_input_manifest") else None,
        run_dir / "verification" / "case_real_weights" / "input_manifest.json",
        run_dir / "verification" / "qwen_real_weights" / "input_manifest.json",
    ]
    path = first_existing([item for item in candidates if item is not None])
    if path is None:
        raise FileNotFoundError("input manifest is missing")
    return path


def resolve_input_memh(run_dir: Path, paths: dict[str, Any], manifest: dict[str, Any]) -> Path:
    image = manifest.get("activation_image", {}) if isinstance(manifest.get("activation_image"), dict) else {}
    candidates = [
        Path(str(paths["input_memh"])) if paths.get("input_memh") else None,
        Path(str(image["path"])) if image.get("path") else None,
        run_dir / "verification" / "case_real_weights" / "input_activation.u32.memh",
        run_dir / "verification" / "qwen_real_weights" / "input_activation.u32.memh",
    ]
    path = first_existing([item for item in candidates if item is not None])
    if path is None:
        raise FileNotFoundError("input activation memh is missing")
    return path


def read_memh_words(path: Path) -> list[int]:
    words: list[int] = []
    for token in path.read_text(encoding="utf-8").split():
        if token.startswith("@"):
            continue
        words.append(int(token, 16))
    return words


def sign_mask(bits: int) -> int:
    return (1 << bits) - 1


def to_signed(value: int, bits: int) -> int:
    value &= sign_mask(bits)
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


def resize_signed_to_uint(value: int, bits: int) -> int:
    return value & sign_mask(bits)


def linear_default_identity(
    beats: list[list[int]],
    *,
    out_beats: int,
    out_lanes: int,
    in_bits: int,
    out_bits: int,
    acc_bits: int = 32,
    activation: str = "none",
) -> list[list[int]]:
    outputs: list[list[int]] = []
    for _ in range(out_beats):
        row: list[int] = []
        for lane in range(out_lanes):
            acc = 0
            for beat in beats:
                acc = to_signed(acc + to_signed(beat[lane], in_bits), acc_bits)
            if activation == "relu" and acc < 0:
                acc = 0
            row.append(resize_signed_to_uint(acc, out_bits))
        outputs.append(row)
    return outputs


def rms_resize(beats: list[list[int]], input_bits: int, output_bits: int) -> list[list[int]]:
    return [[resize_signed_to_uint(to_signed(value, input_bits), output_bits) for value in beat] for beat in beats]


def residual_add(lhs: list[list[int]], rhs: list[list[int]], bits: int) -> list[list[int]]:
    return [
        [resize_signed_to_uint(to_signed(a, bits) + to_signed(b, bits), bits) for a, b in zip(lhs_beat, rhs_beat)]
        for lhs_beat, rhs_beat in zip(lhs, rhs)
    ]


def activation_template(beats: list[list[int]], bits: int, kind: str) -> list[list[int]]:
    out: list[list[int]] = []
    for beat in beats:
        row: list[int] = []
        for value in beat:
            x = to_signed(value, bits)
            if kind in {"relu", "silu", "swish"}:
                y = 0 if x < 0 else x
            elif kind in {"gelu", "gelu_new", "gelu_pytorch_tanh"}:
                y = x >> 1 if x < 0 else x
            else:
                y = x
            row.append(resize_signed_to_uint(y, bits))
        out.append(row)
    return out


def elementwise_mul(lhs: list[list[int]], rhs: list[list[int]], bits: int) -> list[list[int]]:
    return [
        [resize_signed_to_uint(to_signed(a, bits) * to_signed(b, bits), bits) for a, b in zip(lhs_beat, rhs_beat)]
        for lhs_beat, rhs_beat in zip(lhs, rhs)
    ]


def llama_style_block_token(token: list[list[int]], params: dict[str, Any]) -> list[list[int]]:
    hidden = int(params["hidden_size"])
    lanes = int(params["lanes"])
    q_heads = int(params["num_q_heads"])
    kv_heads = int(params["num_kv_heads"])
    head_dim = int(params["head_dim"])
    intermediate = int(params["intermediate_size"])
    input_bits = int(params.get("input_bits", 32))
    elem_bits = int(params.get("elem_bits", 16))
    output_bits = int(params.get("output_bits", input_bits))

    hidden_beats = hidden // lanes
    rms1 = rms_resize(token, input_bits, elem_bits)
    qkv_out_beats = (q_heads + 2 * kv_heads) * head_dim // lanes
    qkv_linear = linear_default_identity(rms1, out_beats=qkv_out_beats, out_lanes=lanes, in_bits=elem_bits, out_bits=elem_bits)
    flat = [value for beat in qkv_linear for value in beat]

    q_dim = q_heads * head_dim
    k_dim = kv_heads * head_dim
    kv_group = q_heads // kv_heads
    attention_beats: list[list[int]] = []
    for head in range(q_heads):
        kv_head = head // kv_group
        base = q_dim + k_dim + kv_head * head_dim
        attention_beats.append([flat[base + idx] for idx in range(head_dim)])

    out_proj = linear_default_identity(
        attention_beats,
        out_beats=hidden_beats,
        out_lanes=lanes,
        in_bits=elem_bits,
        out_bits=output_bits,
    )
    add1 = residual_add(token, out_proj, output_bits)
    rms2 = rms_resize(add1, output_bits, elem_bits)

    mlp_beats = intermediate // lanes
    gate = linear_default_identity(rms2, out_beats=mlp_beats, out_lanes=lanes, in_bits=elem_bits, out_bits=elem_bits)
    up = linear_default_identity(rms2, out_beats=mlp_beats, out_lanes=lanes, in_bits=elem_bits, out_bits=elem_bits)
    act = activation_template(gate, elem_bits, "silu")
    mul = elementwise_mul(act, up, elem_bits)
    down = linear_default_identity(mul, out_beats=hidden_beats, out_lanes=lanes, in_bits=elem_bits, out_bits=output_bits)
    return residual_add(add1, down, output_bits)


def build_golden(run_dir: Path, out_path: Path, manifest_path: Path) -> dict[str, Any]:
    paths = adapter_paths(run_dir)
    codegen_path = run_dir / "code_generation" / "code_generation_manifest.json"
    codegen = read_json(codegen_path)
    generated_top = codegen.get("generated_top", {}) if isinstance(codegen.get("generated_top"), dict) else {}
    params = generated_top.get("params", {}) if isinstance(generated_top.get("params"), dict) else {}
    param_class = str(generated_top.get("param_class") or "")
    if param_class != "LlamaStyleBlockParams":
        raise ValueError(f"unsupported template param_class for golden builder: {param_class}")

    input_manifest_path = resolve_input_manifest(run_dir, paths)
    input_manifest = read_json(input_manifest_path)
    input_memh = resolve_input_memh(run_dir, paths, input_manifest)
    image = input_manifest.get("activation_image", {}) if isinstance(input_manifest.get("activation_image"), dict) else {}
    lanes = int(params.get("lanes") or image.get("lanes") or 1)
    hidden = int(params.get("hidden_size") or image.get("hidden_size") or 0)
    hidden_beats = hidden // lanes
    expected_beats = int(image.get("stream_beats") or 0)
    if expected_beats <= 0:
        expected_beats = len(read_memh_words(input_memh)) // lanes
    if hidden_beats <= 0 or expected_beats % hidden_beats != 0:
        raise ValueError("input stream shape is incompatible with generated hidden_size/lanes")

    words = read_memh_words(input_memh)
    beats = [words[idx : idx + lanes] for idx in range(0, expected_beats * lanes, lanes)]
    outputs: list[list[int]] = []
    for offset in range(0, expected_beats, hidden_beats):
        outputs.extend(llama_style_block_token(beats[offset : offset + hidden_beats], params))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join("".join(f"{value:08x}" for value in reversed(beat)) + "\n" for beat in outputs), encoding="utf-8")
    manifest = {
        "schema_version": "spatialaccagent.single_layer_template_golden.v0",
        "status": "pass",
        "run_dir": str(run_dir),
        "golden_memh": str(out_path),
        "golden_sha256": sha256_file(out_path),
        "input_manifest": str(input_manifest_path),
        "input_memh": str(input_memh),
        "input_sha256": sha256_file(input_memh),
        "code_generation_manifest": str(codegen_path),
        "param_class": param_class,
        "params": params,
        "stream_beats": expected_beats,
        "token_count": expected_beats // hidden_beats,
        "policy": {
            "independent_of_rtl_output": True,
            "template_semantics_reference": True,
            "do_not_modify_to_match_rtl": True,
        },
    }
    write_json(manifest_path, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build independent single-layer template golden memh")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--manifest", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    out_path = args.out or (run_dir / "verification" / "single_layer" / "single_layer_golden.memh")
    manifest_path = args.manifest or (run_dir / "verification" / "single_layer" / "single_layer_golden_manifest.json")
    try:
        manifest = build_golden(run_dir, out_path, manifest_path)
    except Exception as exc:
        report = {
            "schema_version": "spatialaccagent.single_layer_template_golden.v0",
            "status": "fail",
            "run_dir": str(run_dir),
            "golden_memh": str(out_path),
            "summary": str(exc),
            "blockers": [str(exc)],
        }
        write_json(manifest_path, report)
        print(manifest_path)
        return 1
    print(manifest["golden_memh"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
