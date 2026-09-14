#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


LABEL_RE = re.compile(r"(?m)(?:^|[\n,])([A-Za-z_][A-Za-z0-9_\-]*):")
DTYPE_RE = re.compile(r"torch\.(float16|float32|int8|int32|uint8)")
SHAPE_RE = re.compile(r"torch\.Size\((.*?)\)")
SCALAR_RE = re.compile(r"[-+]?(?:\d+\.\d+|\d+|\.\d+)(?:e[-+]?\d+)?")

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_CASE_DIR = REPO_ROOT / "verification" / "cases" / "opt125m_stage_full"
DEFAULT_WINDOW_ROOT = REPO_ROOT / "verification" / "cases" / "opt125m_stage_windows"
DEFAULT_9P_FULLSEQ_ROOT = REPO_ROOT / "verification" / "cases" / "opt125m_9p_fullseq"
GENERATED_TOP = REPO_ROOT / "generated" / "Top.sv"
GENERATED_TOP_VIVADO = REPO_ROOT / "generated" / "Top_vivado.sv"
VERILATOR_INCLUDE_DIRS = [
    REPO_ROOT / "verification",
    REPO_ROOT / "verification" / "assert",
    REPO_ROOT / "verification" / "assume",
    REPO_ROOT / "verification" / "cover",
]
VCS_INCLUDE_DIRS = VERILATOR_INCLUDE_DIRS
CURRENT_CORE_MAX_SEQLEN = 26
CURRENT_CORE_MAX_PREFILL = 8
DEFAULT_BUILD_JOBS = min(4, max(1, os.cpu_count() or 1))

BOARD_AXI_C0_BASE_ADDR = 0x0080_0000_00
BOARD_AXI_C1_BASE_ADDR = 0x0100_0000_00
BOARD_AXI_DATA_BYTES = 32
BOARD_AXI_LINE_BYTES = 64
BOARD_SAMPLE_IP_ROOT = REPO_ROOT / "verification" / "board_sample_ip"
BOARD_DDR_IP_ROOT = REPO_ROOT / "verification" / "board_ddr_ip"

LANES = 12
FP32_WORDS = LANES
INT8_WORDS = LANES // 4
LINEAR_WORDS = 36 // 4


@dataclass
class LabelOccurrence:
    label: str
    occurrence: int
    start: int
    end: int


@dataclass
class ParsedEntry:
    label: str
    occurrence: int
    shape: list[int] | None
    dtype: str | None
    kind: str
    value_start: int
    value_end: int


@dataclass
class TensorArtifact:
    stage: str
    alias: str
    shape: list[int] | None
    dtype: str
    array: np.ndarray


def parse_shape(shape_text: str) -> list[int]:
    return [int(item.strip()) for item in shape_text.strip("[]").split(",") if item.strip()]


def next_label_start(occurrences: list[LabelOccurrence], idx: int, text_len: int) -> int:
    if idx + 1 < len(occurrences):
        return occurrences[idx + 1].start
    return text_len


def scan_labels(text: str) -> list[LabelOccurrence]:
    counts: dict[str, int] = {}
    results: list[LabelOccurrence] = []
    for match in LABEL_RE.finditer(text):
        label = match.group(1)
        occ = counts.get(label, 0)
        counts[label] = occ + 1
        results.append(
            LabelOccurrence(
                label=label,
                occurrence=occ,
                start=match.start(1),
                end=match.end(1) + 1,
            )
        )
    return results


def match_bracket_region(text: str, start_idx: int) -> tuple[int, int]:
    depth = 0
    begin = -1
    for idx in range(start_idx, len(text)):
        ch = text[idx]
        if ch == "[":
            if begin < 0:
                begin = idx
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and begin >= 0:
                return begin, idx + 1
    raise ValueError(f"unmatched bracket starting at offset {start_idx}")


def parse_entries(path: Path) -> list[ParsedEntry]:
    text = path.read_text()
    labels = scan_labels(text)
    entries: list[ParsedEntry] = []

    for idx, occurrence in enumerate(labels):
        chunk_end = next_label_start(labels, idx, len(text))
        chunk = text[occurrence.end:chunk_end]

        shape_match = SHAPE_RE.search(chunk)
        dtype_match = DTYPE_RE.search(chunk)
        tensor_idx_rel = chunk.find("tensor(")

        if tensor_idx_rel >= 0:
            begin, end = match_bracket_region(text, occurrence.end + tensor_idx_rel)
            shape = parse_shape(shape_match.group(1)) if shape_match else None
            dtype = dtype_match.group(1) if dtype_match else None
            entries.append(
                ParsedEntry(
                    label=occurrence.label,
                    occurrence=occurrence.occurrence,
                    shape=shape,
                    dtype=dtype,
                    kind="tensor",
                    value_start=begin,
                    value_end=end,
                )
            )
            continue

        scalar_match = SCALAR_RE.search(chunk)
        if scalar_match:
            start = occurrence.end + scalar_match.start()
            end = start + len(scalar_match.group(0))
            shape = parse_shape(shape_match.group(1)) if shape_match else None
            dtype = dtype_match.group(1) if dtype_match else None
            entries.append(
                ParsedEntry(
                    label=occurrence.label,
                    occurrence=occurrence.occurrence,
                    shape=shape,
                    dtype=dtype,
                    kind="scalar",
                    value_start=start,
                    value_end=end,
                )
            )

    return entries


def resolve_entry(
    path: Path,
    *,
    label: str | None = None,
    occurrence: int = 0,
    tensor_label: str | None = None,
    tensor_occurrence: int | None = None,
    shape_label: str | None = None,
    shape_occurrence: int | None = None,
) -> ParsedEntry:
    entries = parse_entries(path)

    def find_one(target_label: str, target_occurrence: int) -> ParsedEntry:
        for entry in entries:
            if entry.label == target_label and entry.occurrence == target_occurrence:
                return entry
        raise KeyError(f"{path}: missing label={target_label!r} occurrence={target_occurrence}")

    if label is not None:
        return find_one(label, occurrence)

    if tensor_label is None and shape_label is None:
        raise KeyError(f"{path}: no label selector provided")

    tensor_entry = find_one(tensor_label, tensor_occurrence or 0) if tensor_label else None
    shape_entry = find_one(shape_label, shape_occurrence or 0) if shape_label else None

    if tensor_entry and shape_entry and tensor_entry is not shape_entry:
        return ParsedEntry(
            label=tensor_entry.label,
            occurrence=tensor_entry.occurrence,
            shape=shape_entry.shape,
            dtype=tensor_entry.dtype or shape_entry.dtype,
            kind=tensor_entry.kind,
            value_start=tensor_entry.value_start,
            value_end=tensor_entry.value_end,
        )
    return tensor_entry or shape_entry  # type: ignore[return-value]


def tensor_to_array(path: Path, entry: ParsedEntry) -> np.ndarray:
    text = path.read_text()
    raw = text[entry.value_start : entry.value_end]
    cleaned = raw.replace("[", " ").replace("]", " ").replace("\n", " ")
    values = np.fromstring(cleaned, sep=",", dtype=np.float64)

    if entry.shape:
        expected = int(np.prod(entry.shape))
        if values.size != expected:
            raise ValueError(
                f"{path}: parsed {values.size} values for {entry.label}, expected {expected}"
            )
        values = values.reshape(entry.shape)

    if entry.dtype == "int8":
        return values.astype(np.int8)
    if entry.dtype == "uint8":
        return values.astype(np.uint8)
    if entry.dtype == "int32":
        return values.astype(np.int32)
    return values.astype(np.float32)


def scalar_to_value(path: Path, entry: ParsedEntry) -> float:
    text = path.read_text()
    return float(text[entry.value_start : entry.value_end])


def write_array(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if array.dtype == np.float32:
        path.write_bytes(array.astype("<f4").tobytes())
    elif array.dtype == np.int8:
        path.write_bytes(array.astype(np.int8).tobytes())
    elif array.dtype == np.uint8:
        path.write_bytes(array.astype(np.uint8).tobytes())
    elif array.dtype == np.int32:
        path.write_bytes(array.astype("<i4").tobytes())
    elif array.dtype == np.uint32:
        path.write_bytes(array.astype("<u4").tobytes())
    else:
        raise TypeError(f"unsupported dtype {array.dtype}")


def inspect_file(path: Path) -> None:
    print(f"file: {path}")
    for entry in parse_entries(path):
        shape = entry.shape or []
        shape_text = "x".join(str(dim) for dim in shape) if shape else "[]"
        print(
            f"  - label={entry.label!r} occurrence={entry.occurrence} kind={entry.kind} "
            f"shape=[{shape_text}] dtype={entry.dtype} offset={entry.value_start}:{entry.value_end}"
        )


def prepare_case(manifest_path: Path, out_dir: Path) -> None:
    manifest = json.loads(manifest_path.read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir = out_dir / "artifacts"
    artifact_dir.mkdir(exist_ok=True)

    summary: dict[str, Any] = {
        "case_name": manifest.get("case_name", manifest_path.stem),
        "source_manifest": str(manifest_path),
        "artifacts": [],
        "missing_required_artifacts": manifest.get("required_future_artifacts", []),
    }

    for artifact in manifest.get("artifacts", []):
        file_path = Path(artifact["path"])
        artifact_summary = {
            "name": artifact["name"],
            "path": str(file_path),
            "entries": [],
        }

        for entry_cfg in artifact.get("entries", []):
            entry = resolve_entry(
                file_path,
                label=entry_cfg.get("label"),
                occurrence=int(entry_cfg.get("occurrence", 0)),
                tensor_label=entry_cfg.get("tensor_label"),
                tensor_occurrence=entry_cfg.get("tensor_occurrence"),
                shape_label=entry_cfg.get("shape_label"),
                shape_occurrence=entry_cfg.get("shape_occurrence"),
            )

            stem = f"{artifact['name']}.{entry_cfg['alias']}"
            meta_path = artifact_dir / f"{stem}.meta.json"

            if entry.kind == "tensor":
                array = tensor_to_array(file_path, entry)
                bin_path = artifact_dir / f"{stem}.{entry.dtype or 'fp32'}.bin"
                write_array(bin_path, array)
                meta = {
                    "alias": entry_cfg["alias"],
                    "label": entry.label,
                    "occurrence": entry.occurrence,
                    "kind": entry.kind,
                    "shape": entry.shape,
                    "dtype": str(array.dtype),
                    "num_values": int(array.size),
                    "source_file": str(file_path),
                    "binary_file": str(bin_path.relative_to(out_dir)),
                }
            else:
                value = scalar_to_value(file_path, entry)
                txt_path = artifact_dir / f"{stem}.scalar.txt"
                txt_path.write_text(f"{value}\n")
                meta = {
                    "alias": entry_cfg["alias"],
                    "label": entry.label,
                    "occurrence": entry.occurrence,
                    "kind": entry.kind,
                    "shape": entry.shape,
                    "dtype": entry.dtype,
                    "value": value,
                    "source_file": str(file_path),
                    "scalar_file": str(txt_path.relative_to(out_dir)),
                }

            meta_path.write_text(json.dumps(meta, indent=2))
            artifact_summary["entries"].append(meta)

        summary["artifacts"].append(artifact_summary)

    (out_dir / "resolved_manifest.json").write_text(json.dumps(summary, indent=2))
    print(f"prepared case: {out_dir}")
    print(f"artifacts written: {artifact_dir}")
    if summary["missing_required_artifacts"]:
        print("missing required future artifacts:")
        for item in summary["missing_required_artifacts"]:
            print(f"  - {item}")


def dtype_from_name(name: str) -> np.dtype:
    if name == "float32":
        return np.dtype("<f4")
    if name == "int8":
        return np.dtype("i1")
    if name == "uint8":
        return np.dtype("u1")
    if name == "int32":
        return np.dtype("<i4")
    if name == "uint32":
        return np.dtype("<u4")
    raise ValueError(f"unsupported dtype name {name}")


def load_artifact(case_dir: Path, stage: str, alias: str) -> TensorArtifact:
    meta_path = case_dir / "artifacts" / f"{stage}.{alias}.meta.json"
    meta = json.loads(meta_path.read_text())
    if meta["kind"] != "tensor":
        raise TypeError(f"{meta_path} is not a tensor artifact")
    binary_path = case_dir / meta["binary_file"]
    dtype = meta["dtype"]
    array = np.fromfile(binary_path, dtype=dtype_from_name(dtype))
    shape = meta.get("shape")
    if shape is not None:
        array = array.reshape(shape)
    return TensorArtifact(stage=stage, alias=alias, shape=shape, dtype=dtype, array=array)


def load_scalar(case_dir: Path, stage: str, alias: str) -> float:
    meta_path = case_dir / "artifacts" / f"{stage}.{alias}.meta.json"
    meta = json.loads(meta_path.read_text())
    if meta["kind"] != "scalar":
        raise TypeError(f"{meta_path} is not a scalar artifact")
    return float(meta["value"])


def iter_case_tensor_metas(case_dir: Path) -> list[dict[str, Any]]:
    metas: list[dict[str, Any]] = []
    for meta_path in sorted((case_dir / "artifacts").glob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        if meta.get("kind") != "tensor":
            continue
        stem = meta_path.name.removesuffix(".meta.json")
        stage, alias = stem.split(".", 1)
        metas.append(
            {
                "meta_path": meta_path,
                "stage": stage,
                "alias": alias,
                "meta": meta,
            }
        )
    return metas


def iter_case_scalar_metas(case_dir: Path) -> list[dict[str, Any]]:
    metas: list[dict[str, Any]] = []
    for meta_path in sorted((case_dir / "artifacts").glob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        if meta.get("kind") != "scalar":
            continue
        stem = meta_path.name.removesuffix(".meta.json")
        stage, alias = stem.split(".", 1)
        metas.append(
            {
                "meta_path": meta_path,
                "stage": stage,
                "alias": alias,
                "meta": meta,
            }
        )
    return metas


def read_tensor_as_u32_words(case_dir: Path, meta: dict[str, Any]) -> np.ndarray:
    binary_path = case_dir / meta["binary_file"]
    dtype = meta["dtype"]
    if dtype in {"float32", "int32", "uint32"}:
        return np.fromfile(binary_path, dtype=np.uint32)
    if dtype in {"int8", "uint8"}:
        byte_data = np.fromfile(binary_path, dtype=np.uint8)
        pad = (-byte_data.size) % 4
        if pad:
            byte_data = np.pad(byte_data, (0, pad), constant_values=0)
        reshaped = byte_data.reshape(-1, 4).astype(np.uint32)
        packed = reshaped[:, 0]
        packed |= reshaped[:, 1] << 8
        packed |= reshaped[:, 2] << 16
        packed |= reshaped[:, 3] << 24
        return packed
    raise ValueError(f"unsupported tensor dtype for DDR packing: {dtype}")


def slice_tokens_1bn(array: np.ndarray, token_start: int, token_count: int) -> np.ndarray:
    if array.ndim != 3 or array.shape[0] != 1:
        raise ValueError(f"expected [1, N, C], got {array.shape}")
    return np.array(array[0, token_start : token_start + token_count], copy=True)


def slice_token_rows(
    array: np.ndarray,
    token_start: int,
    token_count: int,
    *,
    width: int = 768,
) -> np.ndarray:
    if array.ndim == 3 and array.shape[0] == 1:
        return np.array(array[0, token_start : token_start + token_count], copy=True)
    if array.ndim == 2:
        return np.array(array[token_start : token_start + token_count], copy=True)
    if array.ndim == 1 and array.size % width == 0:
        reshaped = array.reshape(-1, width)
        return np.array(reshaped[token_start : token_start + token_count], copy=True)
    raise ValueError(f"expected [1, N, C], [N, C], or flat multiple of {width}, got {array.shape}")


def reshape_output_like(reference: np.ndarray, output: np.ndarray) -> np.ndarray:
    if output.ndim == reference.ndim:
        return output
    if output.ndim == reference.ndim - 1 and reference.shape[0] == 1:
        return output.reshape(reference.shape[1:])
    return output


def pack_int8_rows(rows: np.ndarray, lanes: int) -> np.ndarray:
    flat = np.asarray(rows, dtype=np.int8).reshape(-1, lanes).astype(np.uint8)
    words_per_beat = lanes // 4
    words = np.zeros((flat.shape[0], words_per_beat), dtype=np.uint32)
    for word_idx in range(words_per_beat):
        chunk = flat[:, word_idx * 4 : (word_idx + 1) * 4].astype(np.uint32)
        words[:, word_idx] = chunk[:, 0]
        words[:, word_idx] |= chunk[:, 1] << 8
        words[:, word_idx] |= chunk[:, 2] << 16
        words[:, word_idx] |= chunk[:, 3] << 24
    return words


def pack_qkv_output_beats(q_rows: np.ndarray, k_rows: np.ndarray, v_rows: np.ndarray) -> np.ndarray:
    q = np.asarray(q_rows, dtype=np.int8)
    k = np.asarray(k_rows, dtype=np.int8)
    v = np.asarray(v_rows, dtype=np.int8)
    if q.shape != k.shape or q.shape != v.shape:
        raise ValueError(f"q/k/v shape mismatch: {q.shape}, {k.shape}, {v.shape}")
    if q.ndim != 2 or q.shape[1] != 768:
        raise ValueError(f"expected [tokens, 768] qkv rows, got {q.shape}")

    token_count = q.shape[0]
    head_dim = 64
    head_num = 12
    beats_per_head = head_dim // 2
    words = np.zeros((token_count * head_num * beats_per_head, 2), dtype=np.uint32)
    beat_idx = 0
    for head in range(head_num):
        base = head * head_dim
        for token in range(token_count):
            for beat in range(beats_per_head):
                idx = base + beat * 2
                q0 = np.uint32(np.uint8(q[token, idx]))
                q1 = np.uint32(np.uint8(q[token, idx + 1]))
                k0 = np.uint32(np.uint8(k[token, idx]))
                k1 = np.uint32(np.uint8(k[token, idx + 1]))
                v0 = np.uint32(np.uint8(v[token, idx]))
                v1 = np.uint32(np.uint8(v[token, idx + 1]))
                words[beat_idx, 0] = q0 | (q1 << 8) | (k0 << 16) | (k1 << 24)
                words[beat_idx, 1] = v0 | (v1 << 8)
                beat_idx += 1
    return words


def pack_dm1_input_beats(q_rows: np.ndarray, k_rows: np.ndarray) -> np.ndarray:
    q = np.asarray(q_rows, dtype=np.int8)
    k = np.asarray(k_rows, dtype=np.int8)
    if q.shape != k.shape:
        raise ValueError(f"q/k shape mismatch: {q.shape}, {k.shape}")
    if q.ndim != 2 or q.shape[1] != 64:
        raise ValueError(f"expected [tokens, 64] q/k rows, got {q.shape}")

    packed = np.zeros((q.shape[0] * (64 // 2), 1), dtype=np.uint32)
    beat_idx = 0
    for token in range(q.shape[0]):
        for pair in range(32):
            idx = pair * 2
            q0 = np.uint32(np.uint8(q[token, idx]))
            q1 = np.uint32(np.uint8(q[token, idx + 1]))
            k0 = np.uint32(np.uint8(k[token, idx]))
            k1 = np.uint32(np.uint8(k[token, idx + 1]))
            packed[beat_idx, 0] = q0 | (q1 << 8) | (k0 << 16) | (k1 << 24)
            beat_idx += 1
    return packed


def pack_softmax_mask_rows(num_rows: int, width: int) -> np.ndarray:
    words = np.zeros((num_rows, 1), dtype=np.uint32)
    for row in range(num_rows):
        mask = 0
        valid = min(row + 1, width)
        for col in range(valid):
            mask |= 1 << col
        words[row, 0] = np.uint32(mask)
    return words


def pack_fp32_rows(rows: np.ndarray, lanes: int) -> np.ndarray:
    return np.asarray(rows, dtype=np.float32).reshape(-1, lanes).view(np.uint32).copy()


def pack_tiled_row(row: np.ndarray, lanes: int, *, dtype: np.dtype | None = None) -> np.ndarray:
    src = np.asarray(row, dtype=dtype)
    beats = max(1, (src.size + lanes - 1) // lanes)
    out = np.zeros((beats, lanes), dtype=src.dtype)
    out.reshape(-1)[: src.size] = src.reshape(-1)
    return out


def pack_single_query_softmax_masks(seq_len: int, beat_count: int) -> np.ndarray:
    if seq_len + 1 > 29:
        raise ValueError(
            f"single-query softmax mask currently only supports seq_len<=28, got seq_len={seq_len}"
        )
    mask = (1 << (seq_len + 1)) - 1
    words = np.zeros((beat_count, 1), dtype=np.uint32)
    words[:, 0] = np.uint32(mask)
    return words


def pack_weight_matrix(weight_out_in: np.ndarray, *, input_dim: int, output_dim: int) -> np.ndarray:
    weight_t = np.asarray(weight_out_in, dtype=np.int8).reshape(output_dim, input_dim).transpose()
    rowblock = input_dim // LANES
    colblock = (output_dim + 36 - 1) // 36
    words: list[np.ndarray] = []
    for rowblock_idx in range(rowblock):
        for row_idx in range(LANES):
            global_row = rowblock_idx * LANES + row_idx
            for colblock_idx in range(colblock):
                start = colblock_idx * 36
                end = min(start + 36, output_dim)
                vals = np.zeros(36, dtype=np.int8)
                vals[: end - start] = weight_t[global_row, start:end]
                words.append(pack_int8_rows(vals.reshape(1, 36), 36)[0])
    return np.asarray(words, dtype=np.uint32)


def float_to_u32(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", np.float32(value)))[0]


def quantize_fp32_to_int8(values: np.ndarray, inv_scale: np.float32, zero_point: int = 0) -> np.ndarray:
    scaled = np.rint(values.astype(np.float32) * np.float32(inv_scale) + np.float32(zero_point))
    clipped = np.clip(scaled, -128, 127)
    return clipped.astype(np.int8)


def refine_fp32_to_int8_scale(
    values: np.ndarray,
    target: np.ndarray,
    *,
    base_scale: np.float32,
    zero_point: int,
    radius: int = 512,
) -> np.float32:
    flat_x = values.astype(np.float32).reshape(-1)
    flat_q = target.astype(np.int8).reshape(-1)
    best_scale = np.float32(base_scale)
    best_mismatch = int(np.count_nonzero(quantize_fp32_to_int8(flat_x, best_scale, zero_point) != flat_q))
    if best_mismatch == 0:
        return best_scale

    down = np.float32(base_scale)
    up = np.float32(base_scale)
    for _ in range(radius):
        down = np.nextafter(down, np.float32(-np.inf), dtype=np.float32)
        up = np.nextafter(up, np.float32(np.inf), dtype=np.float32)
        for candidate in (down, up):
            pred = quantize_fp32_to_int8(flat_x, candidate, zero_point)
            mismatch = int(np.count_nonzero(pred != flat_q))
            if mismatch < best_mismatch:
                best_mismatch = mismatch
                best_scale = np.float32(candidate)
                if best_mismatch == 0:
                    return best_scale
    return best_scale


def infer_fp32_to_int8_scale(
    values: np.ndarray,
    target: np.ndarray,
    *,
    zero_point_candidates: list[int] | None = None,
    refine_radius: int = 512,
) -> tuple[np.float32, int]:
    flat_x = values.astype(np.float32).reshape(-1)
    flat_q = target.astype(np.int16).reshape(-1)
    mask = np.abs(flat_x) > np.float32(1.0e-12)
    zero_point_candidates = zero_point_candidates or [0]

    best: tuple[int, int, np.float32] | None = None
    for zp in zero_point_candidates:
        if np.any(mask):
            num = np.dot(flat_x[mask].astype(np.float64), (flat_q[mask] - zp).astype(np.float64))
            den = np.dot(flat_x[mask].astype(np.float64), flat_x[mask].astype(np.float64))
            scale = np.float32(num / den) if den != 0 else np.float32(1.0)
        else:
            scale = np.float32(1.0)
        scale = refine_fp32_to_int8_scale(
            values,
            target,
            base_scale=scale,
            zero_point=zp,
            radius=refine_radius,
        )
        pred = quantize_fp32_to_int8(flat_x, scale, zp)
        mismatch = int(np.count_nonzero(pred != flat_q.astype(np.int8)))
        score = int(np.max(np.abs(pred.astype(np.int16) - flat_q))) if flat_q.size else 0
        if best is None or (mismatch, score) < best[:2]:
            best = (mismatch, score, scale)
            best_zp = zp

    assert best is not None
    return best[2], best_zp


def infer_layernorm_quant_params(
    inp: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    out_q: np.ndarray,
) -> tuple[np.float32, int]:
    x = np.asarray(inp, dtype=np.float32)
    mean = x.mean(axis=-1, keepdims=True, dtype=np.float32)
    centered = x - mean
    var = np.mean(centered * centered, axis=-1, keepdims=True, dtype=np.float32)
    inv_std = np.float32(1.0) / np.sqrt(var + np.float32(1.0e-5)).astype(np.float32)
    ln = centered * inv_std
    ln = ln * gamma.astype(np.float32)
    ln = ln + beta.astype(np.float32)
    return infer_fp32_to_int8_scale(ln, out_q, zero_point_candidates=[0], refine_radius=16384)


def predict_ffnup(acc: np.ndarray, bias: np.ndarray, inv_scale: np.float32) -> np.ndarray:
    requant = np.rint(acc.astype(np.float32) * inv_scale).astype(np.int32)
    requant = np.clip(requant, -128, 127)
    summed = requant + bias.astype(np.int32)
    summed = np.clip(summed, -128, 127)
    relu = np.maximum(summed, 0)
    return relu.astype(np.int8)


def predict_qkvproj(acc: np.ndarray, bias: np.ndarray, inv_scale: np.float32) -> np.ndarray:
    requant = np.rint(acc.astype(np.float32) * inv_scale).astype(np.int32)
    summed = requant + bias.astype(np.int32)
    summed = np.clip(summed, -128, 127)
    return summed.astype(np.int8)


def infer_ffnup_inv_scale(
    inp: np.ndarray,
    weight: np.ndarray,
    bias: np.ndarray,
    out_q: np.ndarray,
) -> np.float32:
    acc = inp.astype(np.int32) @ weight.astype(np.int32).transpose()
    target = out_q.astype(np.int32)
    bias_i32 = bias.astype(np.int32)
    pseudo = target - bias_i32
    mask = (acc != 0) & (target > 0)
    if np.any(mask):
        num = np.dot(acc[mask].astype(np.float64), pseudo[mask].astype(np.float64))
        den = np.dot(acc[mask].astype(np.float64), acc[mask].astype(np.float64))
        scale = np.float32(num / den) if den != 0 else np.float32(1.0)
    else:
        scale = np.float32(1.0)
    return scale


def infer_ffnup_runtime_params(
    inp: np.ndarray,
    weight: np.ndarray,
    raw_bias: np.ndarray,
    out_q: np.ndarray,
    *,
    weight_scale: float,
    bias_scale: float,
) -> tuple[np.float32, np.ndarray]:
    acc = inp.astype(np.int32) @ weight.astype(np.int32).transpose()
    target = out_q.astype(np.int32)
    bias_i32 = raw_bias.astype(np.int32)

    if bias_scale == 0.0:
        raise ValueError("fc1 bias_scale must be non-zero")

    scale_ratio = np.float32(weight_scale / bias_scale)
    positive_bias = np.max(np.maximum(bias_i32, 0))
    positive_target = int(np.max(np.maximum(target, 0)))
    beta_hi = 1.0
    if positive_bias > 0:
        beta_hi = min(1.0, max(0.125, (positive_target + 16) / float(positive_bias)))

    best_score: tuple[int, int, int] | None = None
    best_beta = np.float32(0.0)

    def score_beta(beta: np.float32) -> tuple[int, int, int]:
        bias_hw = np.clip(
            np.rint(bias_i32.astype(np.float32) * beta).astype(np.int32),
            -128,
            127,
        ).astype(np.int8)
        pred = predict_ffnup(acc, bias_hw, np.float32(scale_ratio * beta)).astype(np.int32)
        diff = np.abs(pred - target)
        return (
            int(np.count_nonzero(diff > 2)),
            int(diff.max()),
            int(diff.sum()),
        )

    lo = np.float32(0.0)
    hi = np.float32(beta_hi)
    for points in (2049, 2049):
        grid = np.linspace(lo, hi, points, dtype=np.float32)
        for beta in grid:
            cur = score_beta(beta)
            if best_score is None or cur < best_score:
                best_score = cur
                best_beta = np.float32(beta)
        step = (hi - lo) / np.float32(points - 1)
        lo = np.float32(max(0.0, float(best_beta - step)))
        hi = np.float32(min(float(beta_hi), float(best_beta + step)))

    bias_hw = np.clip(
        np.rint(bias_i32.astype(np.float32) * best_beta).astype(np.int32),
        -128,
        127,
    ).astype(np.int8)
    out_inv_scale = np.float32(scale_ratio * best_beta)
    return out_inv_scale, bias_hw


def infer_qkv_runtime_params(
    inp: np.ndarray,
    weight: np.ndarray,
    raw_bias: np.ndarray,
    out_q: np.ndarray,
    *,
    weight_scale: float,
    bias_scale: float,
) -> tuple[np.float32, np.ndarray]:
    acc = inp.astype(np.int32) @ weight.astype(np.int32).transpose()
    target = out_q.astype(np.int32)
    bias_i32 = raw_bias.astype(np.int32)

    if bias_scale == 0.0:
        raise ValueError("qkv bias_scale must be non-zero")

    scale_ratio = np.float32(weight_scale / bias_scale)
    best_score: tuple[int, int, int] | None = None
    best_beta = np.float32(0.0)

    def score_beta(beta: np.float32) -> tuple[int, int, int]:
        bias_hw = np.clip(
            np.rint(bias_i32.astype(np.float32) * beta).astype(np.int32),
            -128,
            127,
        ).astype(np.int8)
        pred = predict_qkvproj(acc, bias_hw, np.float32(scale_ratio * beta)).astype(np.int32)
        diff = np.abs(pred - target)
        return (
            int(np.count_nonzero(diff > 2)),
            int(diff.max()),
            int(diff.sum()),
        )

    lo = np.float32(0.0)
    hi = np.float32(0.25)
    for points in (4097, 4097):
        grid = np.linspace(lo, hi, points, dtype=np.float32)
        for beta in grid:
            cur = score_beta(beta)
            if best_score is None or cur < best_score:
                best_score = cur
                best_beta = np.float32(beta)
        step = (hi - lo) / np.float32(points - 1)
        lo = np.float32(max(0.0, float(best_beta - step)))
        hi = np.float32(min(0.25, float(best_beta + step)))

    bias_hw = np.clip(
        np.rint(bias_i32.astype(np.float32) * best_beta).astype(np.int32),
        -128,
        127,
    ).astype(np.int8)
    out_inv_scale = np.float32(scale_ratio * best_beta)
    return out_inv_scale, bias_hw


def infer_ffndown_out_scale(
    inp: np.ndarray,
    weight: np.ndarray,
    bias: np.ndarray,
    out_fp: np.ndarray,
) -> np.float32:
    acc = inp.astype(np.int32) @ weight.astype(np.int32).transpose()
    target = out_fp.astype(np.float32) - bias.astype(np.float32)
    mask = acc != 0
    if np.any(mask):
        num = np.dot(acc[mask].astype(np.float64), target[mask].astype(np.float64))
        den = np.dot(acc[mask].astype(np.float64), acc[mask].astype(np.float64))
        return np.float32(num / den) if den != 0 else np.float32(1.0)
    return np.float32(1.0)


def write_words(path: Path, words: np.ndarray) -> None:
    write_array(path, np.asarray(words, dtype=np.uint32))


def write_cfg(path: Path, items: dict[str, Any]) -> None:
    lines = [f"{key}={value}" for key, value in items.items()]
    path.write_text("\n".join(lines) + "\n")


def pack_into_ddr_words(words: np.ndarray, ddr_words_per_beat: int = 16) -> np.ndarray:
    src = np.asarray(words, dtype=np.uint32)
    if src.ndim == 1:
        pad = (-src.size) % ddr_words_per_beat
        if pad:
            src = np.pad(src, (0, pad), constant_values=0)
        src = src.reshape(-1, ddr_words_per_beat)
    if src.shape[1] > ddr_words_per_beat:
        raise ValueError(f"region width {src.shape[1]} exceeds DDR beat width {ddr_words_per_beat}")
    out = np.zeros((src.shape[0], ddr_words_per_beat), dtype=np.uint32)
    out[:, : src.shape[1]] = src
    return out


def build_ddr_image(regions: list[tuple[str, np.ndarray]]) -> tuple[np.ndarray, dict[str, int]]:
    cursor = 0
    bases: dict[str, int] = {}
    packed_regions: list[np.ndarray] = []
    for name, words in regions:
        region = pack_into_ddr_words(words)
        bases[f"ddr_{name}_base_addr"] = cursor
        packed_regions.append(region)
        cursor += region.shape[0]
    image = np.concatenate(packed_regions, axis=0) if packed_regions else np.zeros((0, 16), dtype=np.uint32)
    return image, bases


def load_raw_tensor(path: Path, label: str) -> np.ndarray:
    return tensor_to_array(path, resolve_entry(path, label=label))


def load_raw_scalar(path: Path, label: str) -> float:
    return float(scalar_to_value(path, resolve_entry(path, label=label)))


def is_all_layers_raw_case(case_dir: Path) -> bool:
    return (case_dir / "layers" / "layer_0").is_dir()


def prepare_all_layers_9p_fullseq_case(case_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = out_dir / "artifacts"
    artifacts.mkdir(exist_ok=True)

    layer_dirs = sorted((case_dir / "layers").glob("layer_*"), key=lambda p: int(p.name.split("_")[-1]))
    if len(layer_dirs) != 12:
        raise ValueError(f"expected 12 layer dirs under {case_dir / 'layers'}, got {len(layer_dirs)}")

    ln1_in = load_raw_tensor(layer_dirs[0] / "layernormQ.json", "x")
    token_count_full = int(ln1_in.shape[1])
    input_words = pack_fp32_rows(ln1_in, LANES)
    top_out = load_raw_tensor(layer_dirs[-1] / "res2.json", "residual2")

    ddr_regions: list[tuple[str, np.ndarray]] = [("input", input_words)]
    layer_scalar_rows: list[np.ndarray] = []
    layer_stride_beats = 0

    for layer_idx, layer_dir in enumerate(layer_dirs):
        ln1_path = layer_dir / "layernormQ.json"
        ln2_path = layer_dir / "final_layernorm.json"
        q_path = layer_dir / "q.json"
        k_path = layer_dir / "k.json"
        v_path = layer_dir / "v.json"
        qk_path = layer_dir / "qk_bmm.json"
        pv_path = layer_dir / "pv_bmm.json"
        out_path = layer_dir / "outproj.json"
        fc1_path = layer_dir / "fc1.json"
        fc2_path = layer_dir / "fc2.json"

        ln1_gamma = load_raw_tensor(ln1_path, "weight").reshape(768)
        ln1_beta = load_raw_tensor(ln1_path, "bias").reshape(768)
        ln1_out = load_raw_tensor(ln1_path, "ln_output_int8")
        ln1_inv_scale, ln1_zero_point = infer_layernorm_quant_params(ln1_in, ln1_gamma, ln1_beta, ln1_out)

        ln2_in = load_raw_tensor(ln2_path, "x")
        ln2_gamma = load_raw_tensor(ln2_path, "weight").reshape(768)
        ln2_beta = load_raw_tensor(ln2_path, "bias").reshape(768)
        ln2_out = load_raw_tensor(ln2_path, "ln_output_int8")
        ln2_inv_scale, ln2_zero_point = infer_layernorm_quant_params(ln2_in, ln2_gamma, ln2_beta, ln2_out)

        q_weight = load_raw_tensor(q_path, "weight").reshape(768, 768)
        k_weight = load_raw_tensor(k_path, "weight").reshape(768, 768)
        v_weight = load_raw_tensor(v_path, "weight").reshape(768, 768)
        q_bias = load_raw_tensor(q_path, "bias").reshape(768)
        k_bias = load_raw_tensor(k_path, "bias").reshape(768)
        v_bias = load_raw_tensor(v_path, "bias").reshape(768)
        qkv_weight = np.concatenate([q_weight, k_weight, v_weight], axis=0)
        qkv_bias_hw = np.concatenate([q_bias, k_bias, v_bias], axis=0)

        q_weight_scale = np.float32(load_raw_scalar(q_path, "scale1"))
        k_weight_scale = np.float32(load_raw_scalar(k_path, "scale1"))
        v_weight_scale = np.float32(load_raw_scalar(v_path, "scale1"))
        q_bias_scale = np.float32(load_raw_scalar(q_path, "scale2"))
        k_bias_scale = np.float32(load_raw_scalar(k_path, "scale2"))
        v_bias_scale = np.float32(load_raw_scalar(v_path, "scale2"))

        out_in = load_raw_tensor(out_path, "x").reshape(token_count_full, 768)
        out_weight = load_raw_tensor(out_path, "weight").reshape(768, 768)
        out_bias = load_raw_tensor(out_path, "bias").reshape(768)
        out_fp = slice_tokens_1bn(load_raw_tensor(out_path, "output"), 0, token_count_full)
        out_out_scale = infer_ffndown_out_scale(out_in, out_weight, out_bias, out_fp)

        fc1_in = load_raw_tensor(fc1_path, "x").reshape(token_count_full, 768)
        fc1_weight = load_raw_tensor(fc1_path, "weight").reshape(3072, 768)
        fc1_bias = load_raw_tensor(fc1_path, "bias").reshape(3072)
        fc1_weight_scale = np.float32(load_raw_scalar(fc1_path, "scale1"))
        fc1_bias_scale = np.float32(load_raw_scalar(fc1_path, "scale2"))

        fc2_in = load_raw_tensor(fc2_path, "x").reshape(token_count_full, 3072)
        fc2_weight = load_raw_tensor(fc2_path, "weight").reshape(768, 3072)
        fc2_bias = load_raw_tensor(fc2_path, "bias").reshape(768)
        fc2_out = slice_tokens_1bn(load_raw_tensor(fc2_path, "output"), 0, token_count_full)
        ffndown_out_scale = infer_ffndown_out_scale(fc2_in, fc2_weight, fc2_bias, fc2_out)

        scalar_words = np.array(
            [
                float_to_u32(float(ln1_inv_scale)),
                np.uint32(int(ln1_zero_point) & 0xFF),
                float_to_u32(float(q_weight_scale)),
                float_to_u32(float(k_weight_scale)),
                float_to_u32(float(v_weight_scale)),
                float_to_u32(float(q_bias_scale)),
                float_to_u32(float(k_bias_scale)),
                float_to_u32(float(v_bias_scale)),
                float_to_u32(float(load_raw_scalar(qk_path, "scale"))),
                float_to_u32(127.0),
                np.uint32(0),
                float_to_u32(float(load_raw_scalar(pv_path, "scale"))),
                float_to_u32(float(out_out_scale)),
                float_to_u32(float(ln2_inv_scale)),
                np.uint32(int(ln2_zero_point) & 0xFF),
                float_to_u32(float(fc1_weight_scale)),
                float_to_u32(float(fc1_bias_scale)),
                float_to_u32(float(ffndown_out_scale)),
            ],
            dtype=np.uint32,
        )
        scalar_beats = pack_into_ddr_words(scalar_words)
        layer_scalar_rows.append(scalar_beats.reshape(-1))

        layer_regions = [
            (f"layer{layer_idx}_scalars", scalar_beats),
            (f"layer{layer_idx}_ln1_w", pack_fp32_rows(np.concatenate([ln1_beta.reshape(1, 768), ln1_gamma.reshape(1, 768)]).reshape(2 * 64, 12), 12)),
            (f"layer{layer_idx}_qkv_w", pack_weight_matrix(qkv_weight, input_dim=768, output_dim=2304)),
            (f"layer{layer_idx}_qkv_b", pack_int8_rows(qkv_bias_hw.reshape(1, 2304), LANES)),
            (f"layer{layer_idx}_sm", pack_softmax_mask_rows(26, token_count_full)),
            (f"layer{layer_idx}_out_w", pack_weight_matrix(out_weight, input_dim=768, output_dim=768)),
            (f"layer{layer_idx}_out_b", pack_fp32_rows(out_bias.reshape(1, 768), LANES)),
            (f"layer{layer_idx}_ln2_w", pack_fp32_rows(np.concatenate([ln2_beta.reshape(1, 768), ln2_gamma.reshape(1, 768)]).reshape(2 * 64, 12), 12)),
            (f"layer{layer_idx}_ffnup_w", pack_weight_matrix(fc1_weight, input_dim=768, output_dim=3072)),
            (f"layer{layer_idx}_ffnup_b", pack_int8_rows(fc1_bias.reshape(1, 3072), LANES)),
            (f"layer{layer_idx}_ffndown_w", pack_weight_matrix(fc2_weight, input_dim=3072, output_dim=768)),
            (f"layer{layer_idx}_ffndown_b", pack_fp32_rows(fc2_bias.reshape(1, 768), LANES)),
        ]
        if layer_idx == 0:
            layer_stride_beats = sum(pack_into_ddr_words(words).shape[0] for _, words in layer_regions)
        ddr_regions.extend(layer_regions)

    output_scratch_beats = token_count_full * 64
    output_guard_beats = 1024
    ddr_regions.append(("output_scratch", np.zeros((output_scratch_beats + output_guard_beats, 16), dtype=np.uint32)))

    ddr_image, ddr_bases = build_ddr_image(ddr_regions)
    write_words(artifacts / "ddr_image.u32.bin", ddr_image)
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(top_out, LANES))
    write_words(artifacts / "layer_scalars.u32.bin", np.asarray(layer_scalar_rows, dtype=np.uint32))

    window_cfg = {
        "cfg_seqlen": token_count_full - 1,
        "input_beats": token_count_full * 64,
        "output_beats": token_count_full * 64,
        "all_layers_mode": 1,
        "layer_count": len(layer_dirs),
        "ddr_layers_base_addr": ddr_bases["ddr_layer0_scalars_base_addr"],
        "ddr_layer_stride_beats": layer_stride_beats,
        "ddr_output_scratch_base_addr": ddr_bases["ddr_output_scratch_base_addr"],
        "ddr_output_scratch_beats": output_scratch_beats,
        "ddr_output_guard_beats": output_guard_beats,
        "ln1_out_inv_scale_u32": int(layer_scalar_rows[0][0]),
        "ln1_out_zero_point_s8": int(layer_scalar_rows[0][1] & 0xFF),
        "q_out_inv_scale_u32": int(layer_scalar_rows[0][2]),
        "k_out_inv_scale_u32": int(layer_scalar_rows[0][3]),
        "v_out_inv_scale_u32": int(layer_scalar_rows[0][4]),
        "q_bias_scale_u32": int(layer_scalar_rows[0][5]),
        "k_bias_scale_u32": int(layer_scalar_rows[0][6]),
        "v_bias_scale_u32": int(layer_scalar_rows[0][7]),
        "dm1_out_scale_u32": int(layer_scalar_rows[0][8]),
        "dm2_ctx_inv_scale_u32": int(layer_scalar_rows[0][9]),
        "dm2_ctx_zero_point_u8": int(layer_scalar_rows[0][10] & 0xFF),
        "dm2_out_inv_scale_u32": int(layer_scalar_rows[0][11]),
        "out_out_scale_u32": int(layer_scalar_rows[0][12]),
        "ln2_out_inv_scale_u32": int(layer_scalar_rows[0][13]),
        "ln2_out_zero_point_s8": int(layer_scalar_rows[0][14] & 0xFF),
        "ffnup_out_inv_scale_u32": int(layer_scalar_rows[0][15]),
        "ffnup_bias_scale_u32": int(layer_scalar_rows[0][16]),
        "ffndown_out_scale_u32": int(layer_scalar_rows[0][17]),
    }
    window_cfg.update(ddr_bases)
    board_axi_bases = {
        "axi_c0_window_base_addr": BOARD_AXI_C0_BASE_ADDR,
        "axi_c1_window_base_addr": BOARD_AXI_C1_BASE_ADDR,
        "axi_data_bytes": BOARD_AXI_DATA_BYTES,
        "axi_line_bytes": BOARD_AXI_LINE_BYTES,
        "axi_input_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_input_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_output_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_output_scratch_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_output_stride_bytes": BOARD_AXI_LINE_BYTES,
    }
    window_cfg.update(board_axi_bases)
    write_cfg(out_dir / "window.cfg", window_cfg)

    summary = {
        "board_model": "9p-ddr-only",
        "source_case_dir": str(case_dir),
        "source_mode": "all_layers_raw",
        "layer_count": len(layer_dirs),
        "layer_stride_beats": layer_stride_beats,
    }
    (out_dir / "case.json").write_text(json.dumps(summary, indent=2))


def prepare_9p_fullseq_case(case_dir: Path, out_dir: Path) -> None:
    if is_all_layers_raw_case(case_dir):
        prepare_all_layers_9p_fullseq_case(case_dir, out_dir)
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = out_dir / "artifacts"
    artifacts.mkdir(exist_ok=True)

    ln1_in = load_artifact(case_dir, "layernorm1", "input").array
    if ln1_in.ndim == 3:
        token_count_full = int(ln1_in.shape[1])
    elif ln1_in.ndim == 2:
        token_count_full = int(ln1_in.shape[0])
    else:
        raise ValueError(f"unexpected layernorm1 input shape: {ln1_in.shape}")
    ln1_gamma = load_artifact(case_dir, "layernorm1", "gamma").array.reshape(768)
    ln1_beta = load_artifact(case_dir, "layernorm1", "beta").array.reshape(768)
    ln1_out = load_artifact(case_dir, "layernorm1", "output").array
    ln1_inv_scale, ln1_zero_point = infer_layernorm_quant_params(ln1_in, ln1_gamma, ln1_beta, ln1_out)

    ln2_in = load_artifact(case_dir, "layernorm2", "input").array
    ln2_gamma = load_artifact(case_dir, "layernorm2", "gamma").array.reshape(768)
    ln2_beta = load_artifact(case_dir, "layernorm2", "beta").array.reshape(768)
    ln2_out = load_artifact(case_dir, "layernorm2", "output").array
    ln2_inv_scale, ln2_zero_point = infer_layernorm_quant_params(ln2_in, ln2_gamma, ln2_beta, ln2_out)

    q_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "q_weight_scale"))
    k_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "k_weight_scale"))
    v_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "v_weight_scale"))
    q_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "q_bias_scale"))
    k_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "k_bias_scale"))
    v_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "v_bias_scale"))

    out_in = load_artifact(case_dir, "out_proj", "input").array
    out_weight = load_artifact(case_dir, "out_proj", "weight").array.reshape(768, 768)
    out_bias = load_artifact(case_dir, "out_proj", "bias").array.reshape(768)
    out_fp = load_artifact(case_dir, "out_proj", "output").array
    out_out_scale = infer_ffndown_out_scale(out_in, out_weight, out_bias, out_fp)

    fc1_weight_scale = np.float32(load_scalar(case_dir, "fc1", "weight_scale"))
    fc1_bias_scale = np.float32(load_scalar(case_dir, "fc1", "bias_scale"))

    fc2_in = load_artifact(case_dir, "fc2", "input").array
    fc2_weight = load_artifact(case_dir, "fc2", "weight").array.reshape(768, 3072)
    fc2_bias = load_artifact(case_dir, "fc2", "bias").array.reshape(768)
    fc2_out = load_artifact(case_dir, "fc2", "output").array
    ffndown_out_scale = infer_ffndown_out_scale(fc2_in, fc2_weight, fc2_bias, fc2_out)

    resadd1_out = load_artifact(case_dir, "res_add1", "output").array
    top_out = (resadd1_out.astype(np.float32) + fc2_out.astype(np.float32)).astype(np.float32)

    q_weight = load_artifact(case_dir, "qkv_proj", "q_weight").array.reshape(768, 768)
    k_weight = load_artifact(case_dir, "qkv_proj", "k_weight").array.reshape(768, 768)
    v_weight = load_artifact(case_dir, "qkv_proj", "v_weight").array.reshape(768, 768)
    q_bias = load_artifact(case_dir, "qkv_proj", "q_bias").array.reshape(768)
    k_bias = load_artifact(case_dir, "qkv_proj", "k_bias").array.reshape(768)
    v_bias = load_artifact(case_dir, "qkv_proj", "v_bias").array.reshape(768)
    qkv_weight = np.concatenate([q_weight, k_weight, v_weight], axis=0)
    qkv_bias_hw = np.concatenate([q_bias, k_bias, v_bias], axis=0)

    fc1_weight = load_artifact(case_dir, "fc1", "weight").array.reshape(3072, 768)
    fc1_bias = load_artifact(case_dir, "fc1", "bias").array.reshape(3072)

    ddr_regions = [
        ("input", pack_fp32_rows(ln1_in, LANES)),
        (
            "ln1_w",
            pack_fp32_rows(
                np.concatenate([ln1_beta.reshape(1, 768), ln1_gamma.reshape(1, 768)]).reshape(2 * 64, 12),
                12,
            ),
        ),
        ("qkv_w", pack_weight_matrix(qkv_weight, input_dim=768, output_dim=2304)),
        ("qkv_b", pack_int8_rows(qkv_bias_hw.reshape(1, 2304), LANES)),
        (
            "sm",
            pack_softmax_mask_rows(
                26 if token_count_full > 26 else token_count_full,
                26 if token_count_full > 26 else token_count_full,
            ),
        ),
        ("out_w", pack_weight_matrix(out_weight, input_dim=768, output_dim=768)),
        ("out_b", pack_fp32_rows(out_bias.reshape(1, 768), LANES)),
        (
            "ln2_w",
            pack_fp32_rows(
                np.concatenate([ln2_beta.reshape(1, 768), ln2_gamma.reshape(1, 768)]).reshape(2 * 64, 12),
                12,
            ),
        ),
        ("ffnup_w", pack_weight_matrix(fc1_weight, input_dim=768, output_dim=3072)),
        ("ffnup_b", pack_int8_rows(fc1_bias.reshape(1, 3072), LANES)),
        ("ffndown_w", pack_weight_matrix(fc2_weight, input_dim=3072, output_dim=768)),
        ("ffndown_b", pack_fp32_rows(fc2_bias.reshape(1, 768), LANES)),
    ]
    ddr_image, ddr_bases = build_ddr_image(ddr_regions)
    write_words(artifacts / "ddr_image.u32.bin", ddr_image)
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(top_out, LANES))

    window_cfg = {
        "cfg_seqlen": token_count_full - 1,
        "input_beats": token_count_full * 64,
        "output_beats": token_count_full * 64,
        "ln1_out_inv_scale_u32": float_to_u32(float(ln1_inv_scale)),
        "ln1_out_zero_point_s8": int(ln1_zero_point),
        "q_out_inv_scale_u32": float_to_u32(float(q_weight_scale)),
        "k_out_inv_scale_u32": float_to_u32(float(k_weight_scale)),
        "v_out_inv_scale_u32": float_to_u32(float(v_weight_scale)),
        "q_bias_scale_u32": float_to_u32(float(q_bias_scale)),
        "k_bias_scale_u32": float_to_u32(float(k_bias_scale)),
        "v_bias_scale_u32": float_to_u32(float(v_bias_scale)),
        "dm1_out_scale_u32": float_to_u32(load_scalar(case_dir, "qk", "scale")),
        "dm2_ctx_inv_scale_u32": float_to_u32(127.0),
        "dm2_ctx_zero_point_u8": 0,
        "dm2_out_inv_scale_u32": float_to_u32(load_scalar(case_dir, "pv", "scale")),
        "out_out_scale_u32": float_to_u32(float(out_out_scale)),
        "ln2_out_inv_scale_u32": float_to_u32(float(ln2_inv_scale)),
        "ln2_out_zero_point_s8": int(ln2_zero_point),
        "ffnup_out_inv_scale_u32": float_to_u32(float(fc1_weight_scale)),
        "ffnup_bias_scale_u32": float_to_u32(float(fc1_bias_scale)),
        "ffndown_out_scale_u32": float_to_u32(float(ffndown_out_scale)),
    }
    window_cfg.update(ddr_bases)

    # Board-facing AXI shell uses byte addresses in the global system map.
    # Reuse the existing 64-byte packed DDR image layout and map it into the
    # first board DDR window so board-realistic shells can fetch the same data.
    board_axi_bases = {
        "axi_c0_window_base_addr": BOARD_AXI_C0_BASE_ADDR,
        "axi_c1_window_base_addr": BOARD_AXI_C1_BASE_ADDR,
        "axi_data_bytes": BOARD_AXI_DATA_BYTES,
        "axi_line_bytes": BOARD_AXI_LINE_BYTES,
        "axi_input_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_input_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_ln1_w_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_ln1_w_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_qkv_w_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_qkv_w_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_qkv_b_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_qkv_b_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_sm_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_sm_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_out_w_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_out_w_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_out_b_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_out_b_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_ln2_w_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_ln2_w_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_ffnup_w_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_ffnup_w_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_ffnup_b_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_ffnup_b_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_ffndown_w_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_ffndown_w_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_ffndown_b_base_addr": BOARD_AXI_C0_BASE_ADDR + ddr_bases["ddr_ffndown_b_base_addr"] * BOARD_AXI_LINE_BYTES,
        "axi_output_base_addr": BOARD_AXI_C0_BASE_ADDR + int(ddr_image.shape[0]) * BOARD_AXI_LINE_BYTES,
        "axi_output_stride_bytes": BOARD_AXI_LINE_BYTES,
    }
    window_cfg.update(board_axi_bases)
    write_cfg(out_dir / "window.cfg", window_cfg)

    summary = {
        "board_model": "9p-ddr-only",
        "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
        "source_case_dir": str(case_dir),
        "token_count_full": token_count_full,
        "ddr_word_width_bits": 512,
        "ddr_u32_words_per_beat": 16,
        "ddr_total_beats": int(ddr_image.shape[0]),
        "board_axi_c0_window_base_addr": BOARD_AXI_C0_BASE_ADDR,
        "board_axi_c1_window_base_addr": BOARD_AXI_C1_BASE_ADDR,
        "board_axi_data_bytes": BOARD_AXI_DATA_BYTES,
        "regions": [
            {
                "region": region_name,
                "ddr_base_addr": int(ddr_bases[f"ddr_{region_name}_base_addr"]),
            }
            for region_name, _ in ddr_regions
        ],
    }
    (out_dir / "case.json").write_text(json.dumps(summary, indent=2))
    print(f"prepared 9P full-sequence case: {out_dir}")
    print(f"ddr image beats: {ddr_image.shape[0]}")


def validate_9p_fullseq(
    *,
    case_dir: Path,
    out_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
    skip_prepare: bool,
) -> None:
    if not skip_prepare:
        prepare_9p_fullseq_case(case_dir, out_dir)
    wrapper = REPO_ROOT / "verification" / "rtl" / "NinePSystemTop.sv"
    harness = REPO_ROOT / "testbench" / "verilator" / "ninepsystemtop_main.cpp"
    build_dir = build_root / "fullseq"
    build_dir.mkdir(parents=True, exist_ok=True)

    verilator_bin = os.getenv("VERILATOR_BIN", "verilator")
    verilator_cmd = [
        verilator_bin,
        *[f"-I{path}" for path in VERILATOR_INCLUDE_DIRS],
        "--cc",
        str(GENERATED_TOP),
        str(wrapper),
        "--top-module",
        "NinePSystemTop",
        "-Mdir",
        str(build_dir),
        "--exe",
        str(harness),
        "-CFLAGS",
        f"-std=c++17 -O3 -I{REPO_ROOT / 'testbench' / 'verilator'}",
    ]
    prefix = "VNinePSystemTop"
    binary_path = build_verilated_binary(
        verilator_cmd=verilator_cmd,
        build_dir=build_dir,
        prefix=prefix,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd([str(binary_path), str(out_dir)])


def prepare_layernorm_window(
    case_dir: Path,
    stage: str,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    inp = slice_tokens_1bn(load_artifact(case_dir, stage, "input").array, token_start, token_count)
    gamma = load_artifact(case_dir, stage, "gamma").array.reshape(768)
    beta = load_artifact(case_dir, stage, "beta").array.reshape(768)
    out_q = slice_tokens_1bn(load_artifact(case_dir, stage, "output").array, token_start, token_count)
    inv_scale, zero_point = infer_layernorm_quant_params(inp, gamma, beta, out_q)

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_fp32_rows(inp, LANES))
    write_words(
        artifacts / "weights.u32.bin",
        pack_fp32_rows(np.concatenate([beta.reshape(1, 768), gamma.reshape(1, 768)]).reshape(2 * 64, 12), 12),
    )
    write_words(artifacts / "golden.u32.bin", pack_int8_rows(out_q, LANES))

    manifest = {
        "stage": stage,
        "validator": "layernormq",
        "top_module": "LayerNormQ",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "data_beats": token_count * 64,
        "weight_beats": 128,
        "output_beats": token_count * 64,
        "out_inv_scale_u32": float_to_u32(float(inv_scale)),
        "out_zero_point_s8": int(zero_point),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_qk_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    head_idx: int,
    out_dir: Path,
) -> None:
    q_all = load_artifact(case_dir, "qk", "query_states").array
    k_all = load_artifact(case_dir, "qk", "key_states").array
    out_all = load_artifact(case_dir, "qk", "output").array
    if not (0 <= head_idx < q_all.shape[0]):
        raise ValueError(f"head_idx out of range: {head_idx}")

    q = np.array(q_all[head_idx, token_start : token_start + token_count], copy=True)
    k = np.array(k_all[head_idx, token_start : token_start + token_count], copy=True)
    golden = np.zeros((token_count, 26), dtype=np.float32)
    sub = np.array(
        out_all[head_idx, token_start : token_start + token_count, token_start : token_start + token_count],
        dtype=np.float32,
        copy=True,
    )
    golden[:, :token_count] = sub

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_dm1_input_beats(q, k))
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(golden, 26))

    manifest = {
        "stage": "qk",
        "validator": "dm1fp32",
        "top_module": "DM1FP32",
        "token_start": token_start,
        "token_count": token_count,
        "head_idx": head_idx,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 32,
        "output_beats": token_count,
        "out_scale_u32": float_to_u32(load_scalar(case_dir, "qk", "scale")),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_qkv_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    inp = slice_tokens_1bn(load_artifact(case_dir, "qkv_proj", "input").array, token_start, token_count)
    q_weight = load_artifact(case_dir, "qkv_proj", "q_weight").array.reshape(768, 768)
    k_weight = load_artifact(case_dir, "qkv_proj", "k_weight").array.reshape(768, 768)
    v_weight = load_artifact(case_dir, "qkv_proj", "v_weight").array.reshape(768, 768)
    q_bias = load_artifact(case_dir, "qkv_proj", "q_bias").array.reshape(768)
    k_bias = load_artifact(case_dir, "qkv_proj", "k_bias").array.reshape(768)
    v_bias = load_artifact(case_dir, "qkv_proj", "v_bias").array.reshape(768)
    q_out = slice_tokens_1bn(load_artifact(case_dir, "qkv_proj", "q_output").array.reshape(1, 912, 768), token_start, token_count)
    k_out = slice_tokens_1bn(load_artifact(case_dir, "qkv_proj", "k_output").array.reshape(1, 912, 768), token_start, token_count)
    v_out = slice_tokens_1bn(load_artifact(case_dir, "qkv_proj", "v_output").array.reshape(1, 912, 768), token_start, token_count)

    combined_weight = np.concatenate([q_weight, k_weight, v_weight], axis=0)
    combined_bias_hw = np.concatenate([q_bias, k_bias, v_bias], axis=0)
    q_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "q_weight_scale"))
    k_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "k_weight_scale"))
    v_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "v_weight_scale"))
    q_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "q_bias_scale"))
    k_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "k_bias_scale"))
    v_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "v_bias_scale"))

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_int8_rows(inp, LANES))
    write_words(artifacts / "weight_init.u32.bin", pack_weight_matrix(combined_weight, input_dim=768, output_dim=2304))
    write_words(artifacts / "bias_init.u32.bin", pack_int8_rows(combined_bias_hw.reshape(1, 2304), LANES))
    write_words(artifacts / "golden.u32.bin", pack_qkv_output_beats(q_out, k_out, v_out))
    q_rows = q_out.reshape(-1, 768)
    k_rows = k_out.reshape(-1, 768)
    v_rows = v_out.reshape(-1, 768)
    write_words(artifacts / "q_output_rows.u32.bin", pack_int8_rows(q_rows, LANES))
    write_words(artifacts / "k_output_rows.u32.bin", pack_int8_rows(k_rows, LANES))
    write_words(artifacts / "v_output_rows.u32.bin", pack_int8_rows(v_rows, LANES))
    write_words(artifacts / "qkv_q_chunk0.u32.bin", pack_int8_rows(q_rows[:, :12], LANES))
    write_words(artifacts / "qkv_k_chunk0.u32.bin", pack_int8_rows(k_rows[:, :12], LANES))
    write_words(artifacts / "qkv_v_chunk0.u32.bin", pack_int8_rows(v_rows[:, :12], LANES))

    manifest = {
        "stage": "qkv_proj",
        "validator": "qkvlinear",
        "top_module": "QKVLinear",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 64,
        "weight_init_words": 49152,
        "bias_init_words": 192,
        "output_beats": token_count * 384,
        "q_out_inv_scale_u32": float_to_u32(float(q_weight_scale)),
        "k_out_inv_scale_u32": float_to_u32(float(k_weight_scale)),
        "v_out_inv_scale_u32": float_to_u32(float(v_weight_scale)),
        "q_bias_scale_u32": float_to_u32(float(q_bias_scale)),
        "k_bias_scale_u32": float_to_u32(float(k_bias_scale)),
        "v_bias_scale_u32": float_to_u32(float(v_bias_scale)),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_softmax_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    head_idx: int,
    out_dir: Path,
) -> None:
    softmax_in = load_artifact(case_dir, "softmax", "input").array
    softmax_out = load_artifact(case_dir, "softmax", "output").array
    if not (0 <= head_idx < softmax_in.shape[0]):
        raise ValueError(f"head_idx out of range: {head_idx}")
    if token_start == 0:
        if token_count > 26:
            raise ValueError(
                "prefix softmax validation currently only supports token_count<=26; "
                "use token_start>0, token_count=1 for single-query multi-tile rows"
            )
        rows_to_feed = 26
        inp = np.array(softmax_in[head_idx, :rows_to_feed, :26], dtype=np.float32, copy=True)
        golden = np.array(softmax_out[head_idx, :token_count, :26], dtype=np.float32, copy=True)
        masks = pack_softmax_mask_rows(rows_to_feed, 26)
        cfg_seqlen = token_count - 1
        cfg_single_query = 0
    else:
        if token_count != 1:
            raise ValueError("single-query softmax validation currently requires token_count=1")
        seq_len = token_start + 1
        row_in = np.array(softmax_in[head_idx, token_start, :seq_len], dtype=np.float32, copy=True)
        row_out = np.array(softmax_out[head_idx, token_start, :seq_len], dtype=np.float32, copy=True)
        inp = pack_tiled_row(row_in, 26, dtype=np.float32)
        golden = pack_tiled_row(row_out, 26, dtype=np.float32)
        masks = pack_single_query_softmax_masks(token_start, inp.shape[0])
        rows_to_feed = inp.shape[0]
        cfg_seqlen = token_start
        cfg_single_query = 1

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_fp32_rows(inp, 26))
    write_words(artifacts / "masks.u32.bin", masks)
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(golden, 26))

    manifest = {
        "stage": "softmax",
        "validator": "softmaxfp32",
        "top_module": "SoftmaxPipFP32",
        "token_start": token_start,
        "token_count": token_count,
        "head_idx": head_idx,
        "cfg_seqlen": cfg_seqlen,
        "cfg_prefill": 0,
        "cfg_single_query": cfg_single_query,
        "input_beats": rows_to_feed,
        "mask_beats": rows_to_feed,
        "output_beats": golden.shape[0],
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_pv_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    head_idx: int,
    out_dir: Path,
) -> None:
    attn_prob = load_artifact(case_dir, "pv", "attn_prob").array
    softmax_out = load_artifact(case_dir, "softmax", "output").array
    value_states = load_artifact(case_dir, "pv", "value_states").array
    output = load_artifact(case_dir, "pv", "output").array
    if not (0 <= head_idx < attn_prob.shape[0]):
        raise ValueError(f"head_idx out of range: {head_idx}")
    if token_start == 0:
        if token_count > 26:
            raise ValueError(
                "prefix DM2 validation currently only supports token_count<=26; "
                "use token_start>0, token_count=1 for single-query multi-tile rows"
            )
        ctx = np.zeros((token_count, 26), dtype=np.float32)
        ctx[:, :token_count] = np.asarray(attn_prob[head_idx, :token_count, :token_count], dtype=np.float32)
        v = np.array(value_states[head_idx, :, :token_count].transpose(1, 0), dtype=np.int8, copy=True)
        golden = np.array(output[head_idx, :token_count, :], dtype=np.int8, copy=True)
        cfg_seqlen = token_count - 1
        cfg_single_query = 0
    else:
        if token_count != 1:
            raise ValueError("single-query DM2 validation currently requires token_count=1")
        seq_len = token_start + 1
        ctx_row = np.array(softmax_out[head_idx, token_start, :seq_len], dtype=np.float32, copy=True)
        ctx = pack_tiled_row(ctx_row, 26, dtype=np.float32)
        v = np.array(value_states[head_idx, :, :seq_len].transpose(1, 0), dtype=np.int8, copy=True)
        golden = np.array(output[head_idx, token_start : token_start + 1, :], dtype=np.int8, copy=True)
        cfg_seqlen = token_start
        cfg_single_query = 1

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "ctx_in.u32.bin", pack_fp32_rows(ctx, 26))
    write_words(artifacts / "v_in.u32.bin", pack_int8_rows(v, 64))
    write_words(artifacts / "golden.u32.bin", pack_int8_rows(golden, 64))

    manifest = {
        "stage": "pv",
        "validator": "dm2quant",
        "top_module": "DM2Quant",
        "token_start": token_start,
        "token_count": token_count,
        "head_idx": head_idx,
        "cfg_seqlen": cfg_seqlen,
        "cfg_prefill": 0,
        "cfg_single_query": cfg_single_query,
        "ctx_beats": ctx.shape[0],
        "v_beats": v.shape[0],
        "output_beats": golden.shape[0],
        "ctx_inv_scale_u32": float_to_u32(1.0),
        "ctx_zero_point_u8": 0,
        "out_inv_scale_u32": float_to_u32(load_scalar(case_dir, "pv", "scale")),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_out_proj_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    inp = slice_tokens_1bn(load_artifact(case_dir, "out_proj", "input").array, token_start, token_count)
    weight = load_artifact(case_dir, "out_proj", "weight").array.reshape(768, 768)
    bias = load_artifact(case_dir, "out_proj", "bias").array.reshape(768)
    out_fp = slice_tokens_1bn(load_artifact(case_dir, "out_proj", "output").array, token_start, token_count)
    out_scale = infer_ffndown_out_scale(inp, weight, bias, out_fp)

    head_beats = np.asarray(inp.reshape(token_count, 12, 64).transpose(1, 0, 2), dtype=np.int8)

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_int8_rows(head_beats.reshape(-1, 64), 64))
    write_words(artifacts / "weight_init.u32.bin", pack_weight_matrix(weight, input_dim=768, output_dim=768))
    write_words(artifacts / "bias_init.u32.bin", pack_fp32_rows(bias.reshape(1, 768), LANES))
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(out_fp, LANES))

    manifest = {
        "stage": "out_proj",
        "validator": "outlinearfp32",
        "top_module": "OutLinearFP32",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 12,
        "weight_init_words": 16896,
        "bias_init_words": 64,
        "output_beats": token_count * 64,
        "out_scale_u32": float_to_u32(float(out_scale)),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_resadd_window(
    case_dir: Path,
    stage: str,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    lhs_alias, rhs_alias = (
        ("res_input", "out_proj_output") if stage == "res_add1" else ("res_add1_output", "fc2_output")
    )
    lhs = slice_tokens_1bn(load_artifact(case_dir, stage, lhs_alias).array, token_start, token_count)
    rhs_artifact = load_artifact(case_dir, stage, rhs_alias)
    if rhs_artifact.shape is None and stage == "res_add2":
        rhs_full = rhs_artifact.array.reshape(1, 912, 768)
    else:
        rhs_full = rhs_artifact.array
    rhs = slice_tokens_1bn(rhs_full, token_start, token_count)
    out_fp = (lhs.astype(np.float32) + rhs.astype(np.float32)).astype(np.float32)

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "lhs.u32.bin", pack_fp32_rows(lhs, LANES))
    write_words(artifacts / "rhs.u32.bin", pack_fp32_rows(rhs, LANES))
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(out_fp, LANES))

    manifest = {
        "stage": stage,
        "validator": "resadd" if stage == "res_add1" else "resadd2",
        "top_module": "ResAddFP32" if stage == "res_add1" else "ResAdd2FP32",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 64,
        "output_beats": token_count * 64,
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_fc1_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    inp = slice_tokens_1bn(load_artifact(case_dir, "fc1", "input").array, token_start, token_count)
    weight = load_artifact(case_dir, "fc1", "weight").array.reshape(3072, 768)
    raw_bias = load_artifact(case_dir, "fc1", "bias").array.reshape(3072)
    weight_scale = load_scalar(case_dir, "fc1", "weight_scale")
    bias_scale = load_scalar(case_dir, "fc1", "bias_scale")
    out_q = slice_tokens_1bn(load_artifact(case_dir, "fc1", "output").array, token_start, token_count)

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_int8_rows(inp, LANES))
    write_words(artifacts / "weight_init.u32.bin", pack_weight_matrix(weight, input_dim=768, output_dim=3072))
    write_words(artifacts / "bias_init.u32.bin", pack_int8_rows(raw_bias.reshape(1, 3072), LANES))
    write_words(artifacts / "golden.u32.bin", pack_int8_rows(out_q, LANES))

    manifest = {
        "stage": "fc1",
        "validator": "ffnup",
        "top_module": "FFNUp",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 64,
        "weight_init_words": 66048,
        "bias_init_words": 256,
        "output_beats": token_count * 256,
        "out_inv_scale_u32": float_to_u32(float(weight_scale)),
        "bias_scale_u32": float_to_u32(float(bias_scale)),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_fc2_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    inp = slice_tokens_1bn(load_artifact(case_dir, "fc2", "input").array, token_start, token_count)
    weight = load_artifact(case_dir, "fc2", "weight").array.reshape(768, 3072)
    bias = load_artifact(case_dir, "fc2", "bias").array.reshape(768)
    out_fp = slice_tokens_1bn(load_artifact(case_dir, "fc2", "output").array, token_start, token_count)
    out_scale = infer_ffndown_out_scale(inp, weight, bias, out_fp)

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", pack_int8_rows(inp, LANES))
    write_words(artifacts / "weight_init.u32.bin", pack_weight_matrix(weight, input_dim=3072, output_dim=768))
    write_words(artifacts / "bias_init.u32.bin", pack_fp32_rows(bias.reshape(1, 768), LANES))
    write_words(artifacts / "golden.u32.bin", pack_fp32_rows(out_fp, LANES))

    manifest = {
        "stage": "fc2",
        "validator": "ffndown",
        "top_module": "FFNDownFP32",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 256,
        "weight_init_words": 67584,
        "bias_init_words": 64,
        "output_beats": token_count * 64,
        "out_scale_u32": float_to_u32(float(out_scale)),
    }
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_top_window(
    case_dir: Path,
    token_start: int,
    token_count: int,
    out_dir: Path,
) -> None:
    if token_start != 0:
        raise ValueError("Top validation currently only supports token_start=0 prefix windows")
    ensure_supported_top_runtime(token_count)

    ln1_in = slice_tokens_1bn(load_artifact(case_dir, "layernorm1", "input").array, token_start, token_count)
    ln1_gamma = load_artifact(case_dir, "layernorm1", "gamma").array.reshape(768)
    ln1_beta = load_artifact(case_dir, "layernorm1", "beta").array.reshape(768)
    ln1_out = slice_tokens_1bn(load_artifact(case_dir, "layernorm1", "output").array, token_start, token_count)
    ln1_inv_scale, ln1_zero_point = infer_layernorm_quant_params(ln1_in, ln1_gamma, ln1_beta, ln1_out)

    qkv_in = slice_tokens_1bn(load_artifact(case_dir, "qkv_proj", "input").array, token_start, token_count)
    q_weight = load_artifact(case_dir, "qkv_proj", "q_weight").array.reshape(768, 768)
    k_weight = load_artifact(case_dir, "qkv_proj", "k_weight").array.reshape(768, 768)
    v_weight = load_artifact(case_dir, "qkv_proj", "v_weight").array.reshape(768, 768)
    q_bias = load_artifact(case_dir, "qkv_proj", "q_bias").array.reshape(768)
    k_bias = load_artifact(case_dir, "qkv_proj", "k_bias").array.reshape(768)
    v_bias = load_artifact(case_dir, "qkv_proj", "v_bias").array.reshape(768)
    q_out = slice_token_rows(load_artifact(case_dir, "qkv_proj", "q_output").array, token_start, token_count)
    k_out = slice_token_rows(load_artifact(case_dir, "qkv_proj", "k_output").array, token_start, token_count)
    v_out = slice_token_rows(load_artifact(case_dir, "qkv_proj", "v_output").array, token_start, token_count)
    q_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "q_weight_scale"))
    k_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "k_weight_scale"))
    v_weight_scale = np.float32(load_scalar(case_dir, "qkv_proj", "v_weight_scale"))
    q_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "q_bias_scale"))
    k_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "k_bias_scale"))
    v_bias_scale = np.float32(load_scalar(case_dir, "qkv_proj", "v_bias_scale"))
    qkv_weight = np.concatenate([q_weight, k_weight, v_weight], axis=0)
    qkv_bias_hw = np.concatenate([q_bias, k_bias, v_bias], axis=0)
    qk_head0 = np.array(
        load_artifact(case_dir, "qk", "output").array[0, token_start : token_start + token_count, token_start : token_start + token_count],
        dtype=np.float32,
        copy=True,
    )
    qk_head0_padded = np.zeros((token_count, 26), dtype=np.float32)
    qk_head0_padded[:, :token_count] = qk_head0
    softmax_input_head0 = np.array(load_artifact(case_dir, "softmax", "input").array[0, :token_count, :26], dtype=np.float32, copy=True)
    softmax_head0 = np.array(load_artifact(case_dir, "softmax", "output").array[0, :token_count, :26], dtype=np.float32, copy=True)

    out_in = slice_tokens_1bn(load_artifact(case_dir, "out_proj", "input").array, token_start, token_count)
    out_weight = load_artifact(case_dir, "out_proj", "weight").array.reshape(768, 768)
    out_bias = load_artifact(case_dir, "out_proj", "bias").array.reshape(768)
    out_fp = slice_tokens_1bn(load_artifact(case_dir, "out_proj", "output").array, token_start, token_count)
    out_out_scale = infer_ffndown_out_scale(out_in, out_weight, out_bias, out_fp)
    head_beats = np.asarray(out_in.reshape(token_count, 12, 64).transpose(1, 0, 2), dtype=np.int8)

    ln2_in = slice_tokens_1bn(load_artifact(case_dir, "layernorm2", "input").array, token_start, token_count)
    ln2_gamma = load_artifact(case_dir, "layernorm2", "gamma").array.reshape(768)
    ln2_beta = load_artifact(case_dir, "layernorm2", "beta").array.reshape(768)
    ln2_out = slice_tokens_1bn(load_artifact(case_dir, "layernorm2", "output").array, token_start, token_count)
    ln2_inv_scale, ln2_zero_point = infer_layernorm_quant_params(ln2_in, ln2_gamma, ln2_beta, ln2_out)

    fc1_in = slice_tokens_1bn(load_artifact(case_dir, "fc1", "input").array, token_start, token_count)
    fc1_weight = load_artifact(case_dir, "fc1", "weight").array.reshape(3072, 768)
    fc1_bias = load_artifact(case_dir, "fc1", "bias").array.reshape(3072)
    fc1_out = slice_tokens_1bn(load_artifact(case_dir, "fc1", "output").array, token_start, token_count)
    fc1_weight_scale = load_scalar(case_dir, "fc1", "weight_scale")
    fc1_bias_scale = load_scalar(case_dir, "fc1", "bias_scale")

    fc2_in = slice_tokens_1bn(load_artifact(case_dir, "fc2", "input").array, token_start, token_count)
    fc2_weight = load_artifact(case_dir, "fc2", "weight").array.reshape(768, 3072)
    fc2_bias = load_artifact(case_dir, "fc2", "bias").array.reshape(768)
    fc2_out = slice_tokens_1bn(load_artifact(case_dir, "fc2", "output").array, token_start, token_count)
    ffndown_out_scale = infer_ffndown_out_scale(fc2_in, fc2_weight, fc2_bias, fc2_out)

    resadd1_out = slice_tokens_1bn(load_artifact(case_dir, "res_add1", "output").array, token_start, token_count)
    top_out = (resadd1_out.astype(np.float32) + fc2_out.astype(np.float32)).astype(np.float32)

    data_in_words = pack_fp32_rows(ln1_in, LANES)
    ln1_weight_words = pack_fp32_rows(
        np.concatenate([ln1_beta.reshape(1, 768), ln1_gamma.reshape(1, 768)]).reshape(2 * 64, 12),
        12,
    )
    ln2_weight_words = pack_fp32_rows(
        np.concatenate([ln2_beta.reshape(1, 768), ln2_gamma.reshape(1, 768)]).reshape(2 * 64, 12),
        12,
    )
    qkv_weight_words = pack_weight_matrix(qkv_weight, input_dim=768, output_dim=2304)
    qkv_bias_words = pack_int8_rows(qkv_bias_hw.reshape(1, 2304), LANES)
    sm_words = pack_softmax_mask_rows(26, 26)
    out_weight_words = pack_weight_matrix(out_weight, input_dim=768, output_dim=768)
    out_bias_words = pack_fp32_rows(out_bias.reshape(1, 768), LANES)
    ffnup_weight_words = pack_weight_matrix(fc1_weight, input_dim=768, output_dim=3072)
    ffnup_bias_words = pack_int8_rows(fc1_bias.reshape(1, 3072), LANES)
    ffndown_weight_words = pack_weight_matrix(fc2_weight, input_dim=3072, output_dim=768)
    ffndown_bias_words = pack_fp32_rows(fc2_bias.reshape(1, 768), LANES)
    golden_words = pack_fp32_rows(top_out, LANES)

    artifacts = out_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    write_words(artifacts / "data_in.u32.bin", data_in_words)
    write_words(artifacts / "ln1_weights.u32.bin", ln1_weight_words)
    write_words(artifacts / "ln2_weights.u32.bin", ln2_weight_words)
    write_words(artifacts / "qkv_weight_init.u32.bin", qkv_weight_words)
    write_words(artifacts / "qkv_bias_init.u32.bin", qkv_bias_words)
    write_words(artifacts / "qkv_q_chunk0.u32.bin", pack_int8_rows(q_out[:, :12], LANES))
    write_words(artifacts / "qkv_k_chunk0.u32.bin", pack_int8_rows(k_out[:, :12], LANES))
    write_words(artifacts / "qkv_v_chunk0.u32.bin", pack_int8_rows(v_out[:, :12], LANES))
    write_words(artifacts / "sm_masks.u32.bin", sm_words)
    write_words(artifacts / "qk_head0_golden.u32.bin", pack_fp32_rows(qk_head0_padded, 26))
    write_words(artifacts / "softmax_input_head0.u32.bin", pack_fp32_rows(softmax_input_head0, 26))
    write_words(artifacts / "softmax_head0_golden.u32.bin", pack_fp32_rows(softmax_head0, 26))
    write_words(artifacts / "out_weight_init.u32.bin", out_weight_words)
    write_words(artifacts / "out_bias_init.u32.bin", out_bias_words)
    write_words(artifacts / "out_proj_input.u32.bin", pack_int8_rows(head_beats.reshape(-1, 64), 64))
    write_words(artifacts / "out_proj_golden.u32.bin", pack_fp32_rows(out_fp, LANES))
    write_words(artifacts / "ffnup_weight_init.u32.bin", ffnup_weight_words)
    write_words(artifacts / "ffnup_bias_init.u32.bin", ffnup_bias_words)
    write_words(artifacts / "ffnup_golden.u32.bin", pack_int8_rows(fc1_out, LANES))
    write_words(artifacts / "ffndown_weight_init.u32.bin", ffndown_weight_words)
    write_words(artifacts / "ffndown_bias_init.u32.bin", ffndown_bias_words)
    write_words(artifacts / "ffndown_golden.u32.bin", pack_fp32_rows(fc2_out, LANES))
    write_words(artifacts / "resadd1_golden.u32.bin", pack_fp32_rows(resadd1_out, LANES))
    write_words(artifacts / "golden.u32.bin", golden_words)

    ddr_image, ddr_bases = build_ddr_image(
        [
            ("input", data_in_words),
            ("ln1_w", ln1_weight_words),
            ("qkv_w", qkv_weight_words),
            ("qkv_b", qkv_bias_words),
            ("sm", sm_words),
            ("out_w", out_weight_words),
            ("out_b", out_bias_words),
            ("ln2_w", ln2_weight_words),
            ("ffnup_w", ffnup_weight_words),
            ("ffnup_b", ffnup_bias_words),
            ("ffndown_w", ffndown_weight_words),
            ("ffndown_b", ffndown_bias_words),
        ]
    )
    write_words(artifacts / "ddr_image.u32.bin", ddr_image)

    manifest = {
        "stage": "top",
        "validator": "top",
        "top_module": "Top",
        "token_start": token_start,
        "token_count": token_count,
        "cfg_seqlen": token_count - 1,
        "input_beats": token_count * 64,
        "output_beats": token_count * 64,
        "ln1_out_inv_scale_u32": float_to_u32(float(ln1_inv_scale)),
        "ln1_out_zero_point_s8": int(ln1_zero_point),
        "q_out_inv_scale_u32": float_to_u32(float(q_weight_scale)),
        "k_out_inv_scale_u32": float_to_u32(float(k_weight_scale)),
        "v_out_inv_scale_u32": float_to_u32(float(v_weight_scale)),
        "q_bias_scale_u32": float_to_u32(float(q_bias_scale)),
        "k_bias_scale_u32": float_to_u32(float(k_bias_scale)),
        "v_bias_scale_u32": float_to_u32(float(v_bias_scale)),
        "dm1_out_scale_u32": float_to_u32(load_scalar(case_dir, "qk", "scale")),
        "dm2_ctx_inv_scale_u32": float_to_u32(127.0),
        "dm2_ctx_zero_point_u8": 0,
        "dm2_out_inv_scale_u32": float_to_u32(load_scalar(case_dir, "pv", "scale")),
        "out_out_scale_u32": float_to_u32(float(out_out_scale)),
        "ln2_out_inv_scale_u32": float_to_u32(float(ln2_inv_scale)),
        "ln2_out_zero_point_s8": int(ln2_zero_point),
        "ffnup_out_inv_scale_u32": float_to_u32(float(fc1_weight_scale)),
        "ffnup_bias_scale_u32": float_to_u32(float(fc1_bias_scale)),
        "ffndown_out_scale_u32": float_to_u32(float(ffndown_out_scale)),
    }
    manifest.update(ddr_bases)
    (out_dir / "window.json").write_text(json.dumps(manifest, indent=2))
    write_cfg(out_dir / "window.cfg", manifest)


def prepare_stage_window(
    stage: str,
    *,
    token_start: int,
    token_count: int,
    head_idx: int,
    case_dir: Path,
    out_dir: Path,
) -> None:
    if token_count <= 0:
        raise ValueError("token_count must be positive")
    out_dir.mkdir(parents=True, exist_ok=True)

    if stage in {"layernorm1", "layernorm2"}:
        prepare_layernorm_window(case_dir, stage, token_start, token_count, out_dir)
    elif stage == "qk":
        prepare_qk_window(case_dir, token_start, token_count, head_idx, out_dir)
    elif stage == "softmax":
        prepare_softmax_window(case_dir, token_start, token_count, head_idx, out_dir)
    elif stage == "pv":
        prepare_pv_window(case_dir, token_start, token_count, head_idx, out_dir)
    elif stage == "out_proj":
        prepare_out_proj_window(case_dir, token_start, token_count, out_dir)
    elif stage == "qkv_proj":
        prepare_qkv_window(case_dir, token_start, token_count, out_dir)
    elif stage in {"res_add1", "res_add2"}:
        prepare_resadd_window(case_dir, stage, token_start, token_count, out_dir)
    elif stage == "fc1":
        prepare_fc1_window(case_dir, token_start, token_count, out_dir)
    elif stage == "fc2":
        prepare_fc2_window(case_dir, token_start, token_count, out_dir)
    else:
        raise ValueError(f"unsupported stage for current real-data flow: {stage}")

    print(f"prepared stage window: {out_dir}")


def default_window_dir(stage: str, token_start: int, token_count: int, head_idx: int) -> Path:
    if stage in {"qk", "softmax", "pv"}:
        return DEFAULT_WINDOW_ROOT / stage / f"head_{head_idx}_tok_{token_start}_{token_count}"
    return DEFAULT_WINDOW_ROOT / stage / f"tok_{token_start}_{token_count}"


def default_top_window_dir(token_start: int, token_count: int) -> Path:
    return DEFAULT_WINDOW_ROOT / "top" / f"tok_{token_start}_{token_count}"


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join(str(item) for item in cmd))
    subprocess.run(cmd, cwd=cwd or REPO_ROOT, check=True)


def resolve_build_jobs(requested: int | None) -> int:
    if requested is None:
        env_value = os.getenv("VERILATOR_BUILD_JOBS") or os.getenv("MAKE_JOBS")
        if env_value is not None:
            requested = int(env_value)
        else:
            requested = DEFAULT_BUILD_JOBS
    if requested <= 0:
        raise ValueError(f"build jobs must be positive, got {requested}")
    return requested


def build_verilated_binary(
    *,
    verilator_cmd: list[str],
    build_dir: Path,
    prefix: str,
    build_jobs: int | None,
    skip_build: bool,
) -> Path:
    binary_path = build_dir / prefix
    if skip_build:
        if not binary_path.exists():
            raise FileNotFoundError(
                f"requested --skip-build, but missing existing binary: {binary_path}"
            )
        return binary_path

    run_cmd(verilator_cmd)
    jobs = resolve_build_jobs(build_jobs)
    run_cmd(["make", "-C", str(build_dir), "-f", f"{prefix}.mk", "-j", str(jobs), prefix])
    return binary_path


def sanitize_generated_top_for_vcs(top_path: Path) -> None:
    text = top_path.read_text()
    filtered = []
    changed = False
    for line in text.splitlines(True):
        if '`include "layers-' in line and 'Verification' in line:
            changed = True
            continue
        filtered.append(line)
    if changed:
        top_path.write_text("".join(filtered))


def build_vcs_binary(
    *,
    vcs_cmd: list[str],
    build_dir: Path,
    build_jobs: int | None,
    skip_build: bool,
) -> Path:
    binary_path = build_dir / "simv"
    if skip_build:
        if not binary_path.exists():
            raise FileNotFoundError(
                f"requested --skip-build, but missing existing binary: {binary_path}"
            )
        return binary_path

    jobs = resolve_build_jobs(build_jobs)
    extra_args = shlex.split(os.getenv("VCS_EXTRA_ARGS", ""))
    run_cmd([*vcs_cmd, *extra_args, "-j", str(jobs)])
    return binary_path


def ensure_supported_top_runtime(token_count: int) -> None:
    if token_count > CURRENT_CORE_MAX_PREFILL:
        raise ValueError(
            "current Top/SystemTop verification runs the core in Prefill mode, "
            f"but the RTL currently hard-codes MAX_PREFILL={CURRENT_CORE_MAX_PREFILL}; "
            f"the core also still assumes MAX_SEQLEN={CURRENT_CORE_MAX_SEQLEN}. "
            f"A true {token_count}-token full-sequence board-level run is not supported by "
            "the current core/SystemTop implementation yet."
        )


def validate_stage(
    stage: str,
    *,
    token_start: int,
    token_count: int,
    head_idx: int,
    case_dir: Path,
    window_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
) -> None:
    prepare_stage_window(
        stage,
        token_start=token_start,
        token_count=token_count,
        head_idx=head_idx,
        case_dir=case_dir,
        out_dir=window_dir,
    )
    manifest = json.loads((window_dir / "window.json").read_text())
    validator = manifest["validator"]
    top_module = manifest["top_module"]
    harness_map = {
        "layernormq": "layernormq_main.cpp",
        "dm1fp32": "dm1fp32_main.cpp",
        "softmaxfp32": "softmaxfp32_main.cpp",
        "dm2quant": "dm2quant_main.cpp",
        "outlinearfp32": "outlinearfp32_main.cpp",
        "qkvlinear": "qkvlinear_main.cpp",
        "resadd": "resadd_fp32_main.cpp",
        "resadd2": "resadd2_fp32_main.cpp",
        "ffnup": "ffnup_main.cpp",
        "ffndown": "ffndown_fp32_main.cpp",
    }
    harness = REPO_ROOT / "testbench" / "verilator" / harness_map[validator]
    build_dir = build_root / f"{stage}_tok_{token_start}_{token_count}"
    build_dir.mkdir(parents=True, exist_ok=True)

    verilator_bin = os.getenv("VERILATOR_BIN", "verilator")
    verilator_cmd = [
        verilator_bin,
        *[f"-I{path}" for path in VERILATOR_INCLUDE_DIRS],
        "--cc",
        str(GENERATED_TOP),
        "--top-module",
        top_module,
        "-Mdir",
        str(build_dir),
        "--exe",
        str(harness),
        "-CFLAGS",
        f"-std=c++17 -O3 -I{REPO_ROOT / 'testbench' / 'verilator'}",
    ]
    prefix = f"V{top_module}"
    binary_path = build_verilated_binary(
        verilator_cmd=verilator_cmd,
        build_dir=build_dir,
        prefix=prefix,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd([str(binary_path), str(window_dir)])


def validate_top(
    *,
    token_start: int,
    token_count: int,
    case_dir: Path,
    window_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
) -> None:
    prepare_top_window(
        case_dir,
        token_start=token_start,
        token_count=token_count,
        out_dir=window_dir,
    )
    harness = REPO_ROOT / "testbench" / "verilator" / "top_main.cpp"
    build_dir = build_root / f"top_tok_{token_start}_{token_count}"
    build_dir.mkdir(parents=True, exist_ok=True)

    verilator_bin = os.getenv("VERILATOR_BIN", "verilator")
    verilator_cmd = [
        verilator_bin,
        *[f"-I{path}" for path in VERILATOR_INCLUDE_DIRS],
        "--cc",
        str(GENERATED_TOP),
        "--top-module",
        "Top",
        "-Mdir",
        str(build_dir),
        "--exe",
        str(harness),
        "-CFLAGS",
        f"-std=c++17 -O3 -I{REPO_ROOT / 'testbench' / 'verilator'}",
    ]
    prefix = "VTop"
    binary_path = build_verilated_binary(
        verilator_cmd=verilator_cmd,
        build_dir=build_dir,
        prefix=prefix,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd([str(binary_path), str(window_dir)])


def validate_system_top(
    *,
    token_start: int,
    token_count: int,
    case_dir: Path,
    window_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
) -> None:
    prepare_top_window(
        case_dir,
        token_start=token_start,
        token_count=token_count,
        out_dir=window_dir,
    )
    wrapper = REPO_ROOT / "verification" / "rtl" / "NinePSystemTop.sv"
    harness = REPO_ROOT / "testbench" / "verilator" / "ninepsystemtop_main.cpp"
    build_dir = build_root / f"system_top_tok_{token_start}_{token_count}"
    build_dir.mkdir(parents=True, exist_ok=True)

    verilator_bin = os.getenv("VERILATOR_BIN", "verilator")
    verilator_cmd = [
        verilator_bin,
        *[f"-I{path}" for path in VERILATOR_INCLUDE_DIRS],
        "--cc",
        str(GENERATED_TOP),
        str(wrapper),
        "--top-module",
        "NinePSystemTop",
        "-Mdir",
        str(build_dir),
        "--exe",
        str(harness),
        "-CFLAGS",
        f"-std=c++17 -O3 -I{REPO_ROOT / 'testbench' / 'verilator'}",
    ]
    prefix = "VNinePSystemTop"
    binary_path = build_verilated_binary(
        verilator_cmd=verilator_cmd,
        build_dir=build_dir,
        prefix=prefix,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd([str(binary_path), str(window_dir)])


def validate_9p_fullseq_vcs(
    *,
    case_dir: Path,
    out_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
    skip_prepare: bool,
) -> None:
    sanitize_generated_top_for_vcs(GENERATED_TOP)
    if not skip_prepare:
        prepare_9p_fullseq_case(case_dir=case_dir, out_dir=out_dir)
    wrapper = REPO_ROOT / "verification" / "rtl" / "NinePSystemTop.sv"
    harness = REPO_ROOT / "testbench" / "vcs" / "ninepsystemtop_tb.sv"
    build_dir = build_root / "fullseq"
    build_dir.mkdir(parents=True, exist_ok=True)

    vcs_bin = os.getenv("VCS_BIN", "vcs")
    vcs_cmd = [
        vcs_bin,
        "-full64",
        "-sverilog",
        "-timescale=1ns/1ps",
        *[f"+incdir+{path}" for path in VCS_INCLUDE_DIRS],
        str(GENERATED_TOP),
        str(wrapper),
        str(harness),
        "-top",
        "NinePSystemTop_tb",
        "-Mdir=" + str(build_dir / "csrc"),
        "-o",
        str(build_dir / "simv"),
        "-l",
        str(build_dir / "compile.log"),
    ]
    binary_path = build_vcs_binary(
        vcs_cmd=vcs_cmd,
        build_dir=build_dir,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd(
        ["./simv", f"+window_dir={out_dir.resolve()}", "-l", "run.log"],
        cwd=build_dir,
    )


def validate_axi_board_fullseq_vcs(
    *,
    case_dir: Path,
    out_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
    skip_prepare: bool,
) -> None:
    sanitize_generated_top_for_vcs(GENERATED_TOP)
    if not skip_prepare:
        prepare_9p_fullseq_case(case_dir=case_dir, out_dir=out_dir)
    wrapper = REPO_ROOT / "verification" / "rtl" / "AxiBoardSystemTop.sv"
    harness = REPO_ROOT / "testbench" / "vcs" / "axiboardsystemtop_tb.sv"
    build_dir = build_root / "fullseq"
    build_dir.mkdir(parents=True, exist_ok=True)

    vivado_home = Path(os.getenv("XILINX_VIVADO_HOME", "/home/EDA/Xilinx/Vivado/2021.1"))
    glbl_v = vivado_home / "data" / "verilog" / "src" / "glbl.v"
    unisims_dir = vivado_home / "data" / "verilog" / "src" / "unisims"
    missing_xilinx = [str(path) for path in [glbl_v, unisims_dir] if not path.exists()]
    if missing_xilinx:
        raise FileNotFoundError(
            "missing Xilinx simulation sources for board-sample netlists:\n"
            + "\n".join(missing_xilinx)
        )

    sample_netlists = [
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_auto_us_0_sim_netlist.v",
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_auto_us_1_sim_netlist.v",
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_s02_data_fifo_0_sim_netlist.v",
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_s03_data_fifo_0_sim_netlist.v",
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_auto_cc_0_sim_netlist.v",
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_auto_cc_1_sim_netlist.v",
        BOARD_SAMPLE_IP_ROOT / "app_shell_9p_xbar_0_sim_netlist.v",
    ]
    missing_netlists = [str(path) for path in sample_netlists if not path.exists()]
    if missing_netlists:
        raise FileNotFoundError(
            "missing board sample simulation netlists:\n" + "\n".join(missing_netlists)
        )

    vcs_bin = os.getenv("VCS_BIN", "vcs")
    vcs_cmd = [
        vcs_bin,
        "-full64",
        "-sverilog",
        "-timescale=1ns/1ps",
        f"+libext+.v+.sv",
        "-y",
        str(unisims_dir),
        *[f"+incdir+{path}" for path in VCS_INCLUDE_DIRS],
        str(GENERATED_TOP),
        str(wrapper),
        str(glbl_v),
        *(str(path) for path in sample_netlists),
        str(harness),
        "-top",
        "AxiBoardSystemTop_tb",
        "-top",
        "glbl",
        "-Mdir=" + str(build_dir / "csrc"),
        "-o",
        str(build_dir / "simv"),
        "-l",
        str(build_dir / "compile.log"),
    ]
    binary_path = build_vcs_binary(
        vcs_cmd=vcs_cmd,
        build_dir=build_dir,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd(
        ["./simv", f"+window_dir={out_dir.resolve()}", "-l", "run.log"],
        cwd=build_dir,
    )


def validate_cnn_core_fullseq_vcs(
    *,
    case_dir: Path,
    out_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
    skip_prepare: bool,
) -> None:
    sanitize_generated_top_for_vcs(GENERATED_TOP)
    if not skip_prepare:
        prepare_9p_fullseq_case(case_dir=case_dir, out_dir=out_dir)
    wrapper = REPO_ROOT / "verification" / "rtl" / "cnn_core.sv"
    harness = REPO_ROOT / "testbench" / "vcs" / "cnn_core_tb.sv"
    build_dir = build_root / "fullseq"
    build_dir.mkdir(parents=True, exist_ok=True)

    vcs_bin = os.getenv("VCS_BIN", "vcs")
    vcs_cmd = [
        vcs_bin,
        "-full64",
        "-sverilog",
        "-timescale=1ns/1ps",
        "+libext+.v+.sv",
        *[f"+incdir+{path}" for path in VCS_INCLUDE_DIRS],
        str(GENERATED_TOP),
        str(wrapper),
        str(harness),
        "-top",
        "cnn_core_tb",
        "-Mdir=" + str(build_dir / "csrc"),
        "-o",
        str(build_dir / "simv"),
        "-l",
        str(build_dir / "compile.log"),
    ]
    build_vcs_binary(
        vcs_cmd=vcs_cmd,
        build_dir=build_dir,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd(
        ["./simv", f"+window_dir={out_dir.resolve()}", "-l", "run.log"],
        cwd=build_dir,
    )


def validate_opt_acc_core_fullseq_vcs(
    *,
    case_dir: Path,
    out_dir: Path,
    build_root: Path,
    build_jobs: int | None,
    skip_build: bool,
    skip_prepare: bool,
) -> None:
    # VCS validation must use the simulation backend. Top_vivado.sv is reserved for
    # synthesis and may elaborate Vivado floating-point blackboxes that do not have
    # software simulation models in this flow.
    top_rtl = GENERATED_TOP
    sanitize_generated_top_for_vcs(top_rtl)
    if not skip_prepare:
        prepare_9p_fullseq_case(case_dir=case_dir, out_dir=out_dir)
    wrapper = REPO_ROOT / "deliverables" / "vivado_opt_acc_core_ip" / "hdl" / "opt_acc_core.sv"
    harness = REPO_ROOT / "testbench" / "vcs" / "cnn_core_tb.sv"
    build_dir = build_root / "fullseq"
    build_dir.mkdir(parents=True, exist_ok=True)

    vcs_bin = os.getenv("VCS_BIN", "vcs")
    vcs_cmd = [
        vcs_bin,
        "-full64",
        "-sverilog",
        "-timescale=1ns/1ps",
        "+libext+.v+.sv",
        "+define+USE_OPT_ACC_CORE",
        *[f"+incdir+{path}" for path in VCS_INCLUDE_DIRS],
        str(top_rtl),
        str(wrapper),
        str(harness),
        "-top",
        "cnn_core_tb",
        "-Mdir=" + str(build_dir / "csrc"),
        "-o",
        str(build_dir / "simv"),
        "-l",
        str(build_dir / "compile.log"),
    ]
    build_vcs_binary(
        vcs_cmd=vcs_cmd,
        build_dir=build_dir,
        build_jobs=build_jobs,
        skip_build=skip_build,
    )
    run_cmd(
        ["./simv", f"+window_dir={out_dir.resolve()}", "-l", "run.log"],
        cwd=build_dir,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OPT-125M accelerator real-data verification tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    inspect_p = sub.add_parser("inspect", help="inspect tensor labels/shapes in a torch text dump")
    inspect_p.add_argument("path", type=Path)

    prepare_p = sub.add_parser("prepare-case", help="normalize artifacts from a manifest")
    prepare_p.add_argument("manifest", type=Path)
    prepare_p.add_argument("--out-dir", type=Path, required=True)

    stage_p = sub.add_parser("prepare-stage-window", help="prepare one real-data stage window")
    stage_p.add_argument("stage", choices=["layernorm1", "layernorm2", "qk", "softmax", "pv", "qkv_proj", "out_proj", "res_add1", "res_add2", "fc1", "fc2"])
    stage_p.add_argument("--token-start", type=int, default=0)
    stage_p.add_argument("--token-count", type=int, default=1)
    stage_p.add_argument("--head", type=int, default=0)
    stage_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    stage_p.add_argument("--out-dir", type=Path)

    top_prepare_p = sub.add_parser("prepare-top-window", help="prepare one real-data Top window")
    top_prepare_p.add_argument("--token-start", type=int, default=0)
    top_prepare_p.add_argument("--token-count", type=int, default=1)
    top_prepare_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    top_prepare_p.add_argument("--out-dir", type=Path)

    fullseq_prepare_p = sub.add_parser(
        "prepare-9p-fullseq-case",
        help="pack the full 912-token real-data case into one DDR image for 9P-side system validation",
    )
    fullseq_prepare_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    fullseq_prepare_p.add_argument("--out-dir", type=Path, default=DEFAULT_9P_FULLSEQ_ROOT)

    validate_p = sub.add_parser("validate-stage", help="prepare a stage window and validate it with Verilator")
    validate_p.add_argument("stage", choices=["layernorm1", "layernorm2", "qk", "softmax", "pv", "qkv_proj", "out_proj", "res_add1", "res_add2", "fc1", "fc2"])
    validate_p.add_argument("--token-start", type=int, default=0)
    validate_p.add_argument("--token-count", type=int, default=1)
    validate_p.add_argument("--head", type=int, default=0)
    validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    validate_p.add_argument("--window-dir", type=Path)
    validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "stage_validation")
    validate_p.add_argument("--build-jobs", type=int)
    validate_p.add_argument("--skip-build", action="store_true")

    top_validate_p = sub.add_parser("validate-top", help="prepare a Top real-data window and validate it with Verilator")
    top_validate_p.add_argument("--token-start", type=int, default=0)
    top_validate_p.add_argument("--token-count", type=int, default=1)
    top_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    top_validate_p.add_argument("--window-dir", type=Path)
    top_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "top_validation")
    top_validate_p.add_argument("--build-jobs", type=int)
    top_validate_p.add_argument("--skip-build", action="store_true")

    system_top_validate_p = sub.add_parser(
        "validate-system-top",
        help="prepare a Top real-data window and validate it through a 9P-side DDR-only SystemTop wrapper",
    )
    system_top_validate_p.add_argument("--token-start", type=int, default=0)
    system_top_validate_p.add_argument("--token-count", type=int, default=1)
    system_top_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    system_top_validate_p.add_argument("--window-dir", type=Path)
    system_top_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "system_validation")
    system_top_validate_p.add_argument("--build-jobs", type=int)
    system_top_validate_p.add_argument("--skip-build", action="store_true")

    fullseq_validate_p = sub.add_parser(
        "validate-9p-fullseq",
        help="prepare the full 912-token 9P DDR case and validate it through the 9P-side DDR-only SystemTop wrapper",
    )
    fullseq_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    fullseq_validate_p.add_argument("--out-dir", type=Path, default=DEFAULT_9P_FULLSEQ_ROOT)
    fullseq_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "fullseq_system_validation")
    fullseq_validate_p.add_argument("--build-jobs", type=int)
    fullseq_validate_p.add_argument("--skip-build", action="store_true")
    fullseq_validate_p.add_argument("--skip-prepare", action="store_true")

    fullseq_vcs_validate_p = sub.add_parser(
        "validate-9p-fullseq-vcs",
        help="prepare the full 912-token 9P DDR case and validate it with a pure-SV VCS testbench",
    )
    fullseq_vcs_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    fullseq_vcs_validate_p.add_argument("--out-dir", type=Path, default=DEFAULT_9P_FULLSEQ_ROOT)
    fullseq_vcs_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "fullseq_vcs_validation")
    fullseq_vcs_validate_p.add_argument("--build-jobs", type=int)
    fullseq_vcs_validate_p.add_argument("--skip-build", action="store_true")
    fullseq_vcs_validate_p.add_argument("--skip-prepare", action="store_true")

    cnn_core_fullseq_vcs_validate_p = sub.add_parser(
        "validate-cnn-core-fullseq-vcs",
        help="prepare the full 912-token case and validate it with the direct cnn_core-compatible 512-bit AXI VCS testbench",
    )
    cnn_core_fullseq_vcs_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    cnn_core_fullseq_vcs_validate_p.add_argument("--out-dir", type=Path, default=DEFAULT_9P_FULLSEQ_ROOT)
    cnn_core_fullseq_vcs_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "cnn_core_vcs_validation")
    cnn_core_fullseq_vcs_validate_p.add_argument("--build-jobs", type=int)
    cnn_core_fullseq_vcs_validate_p.add_argument("--skip-build", action="store_true")
    cnn_core_fullseq_vcs_validate_p.add_argument("--skip-prepare", action="store_true")

    opt_acc_core_fullseq_vcs_validate_p = sub.add_parser(
        "validate-opt-acc-core-fullseq-vcs",
        help="prepare the full 912-token case and validate it with the direct opt_acc_core-compatible 512-bit AXI VCS testbench",
    )
    opt_acc_core_fullseq_vcs_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    opt_acc_core_fullseq_vcs_validate_p.add_argument("--out-dir", type=Path, default=DEFAULT_9P_FULLSEQ_ROOT)
    opt_acc_core_fullseq_vcs_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "opt_acc_core_vcs_validation")
    opt_acc_core_fullseq_vcs_validate_p.add_argument("--build-jobs", type=int)
    opt_acc_core_fullseq_vcs_validate_p.add_argument("--skip-build", action="store_true")
    opt_acc_core_fullseq_vcs_validate_p.add_argument("--skip-prepare", action="store_true")

    axi_board_fullseq_vcs_validate_p = sub.add_parser(
        "validate-axi-board-fullseq-vcs",
        help="prepare the full 912-token case and validate it with a board-style AXI DDR VCS testbench",
    )
    axi_board_fullseq_vcs_validate_p.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    axi_board_fullseq_vcs_validate_p.add_argument("--out-dir", type=Path, default=DEFAULT_9P_FULLSEQ_ROOT)
    axi_board_fullseq_vcs_validate_p.add_argument("--build-root", type=Path, default=REPO_ROOT / "obj_dir" / "axi_board_vcs_validation")
    axi_board_fullseq_vcs_validate_p.add_argument("--build-jobs", type=int)
    axi_board_fullseq_vcs_validate_p.add_argument("--skip-build", action="store_true")
    axi_board_fullseq_vcs_validate_p.add_argument("--skip-prepare", action="store_true")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.cmd == "inspect":
        inspect_file(args.path)
    elif args.cmd == "prepare-case":
        prepare_case(args.manifest, args.out_dir)
    elif args.cmd == "prepare-stage-window":
        out_dir = args.out_dir or default_window_dir(args.stage, args.token_start, args.token_count, args.head)
        prepare_stage_window(
            args.stage,
            token_start=args.token_start,
            token_count=args.token_count,
            head_idx=args.head,
            case_dir=args.case_dir,
            out_dir=out_dir,
        )
    elif args.cmd == "prepare-top-window":
        out_dir = args.out_dir or default_top_window_dir(args.token_start, args.token_count)
        prepare_top_window(
            args.case_dir,
            token_start=args.token_start,
            token_count=args.token_count,
            out_dir=out_dir,
        )
    elif args.cmd == "prepare-9p-fullseq-case":
        prepare_9p_fullseq_case(args.case_dir, args.out_dir)
    elif args.cmd == "validate-stage":
        window_dir = args.window_dir or default_window_dir(args.stage, args.token_start, args.token_count, args.head)
        validate_stage(
            args.stage,
            token_start=args.token_start,
            token_count=args.token_count,
            head_idx=args.head,
            case_dir=args.case_dir,
            window_dir=window_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
        )
    elif args.cmd == "validate-top":
        window_dir = args.window_dir or default_top_window_dir(args.token_start, args.token_count)
        validate_top(
            token_start=args.token_start,
            token_count=args.token_count,
            case_dir=args.case_dir,
            window_dir=window_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
        )
    elif args.cmd == "validate-system-top":
        window_dir = args.window_dir or default_top_window_dir(args.token_start, args.token_count)
        validate_system_top(
            token_start=args.token_start,
            token_count=args.token_count,
            case_dir=args.case_dir,
            window_dir=window_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
        )
    elif args.cmd == "validate-9p-fullseq":
        validate_9p_fullseq(
            case_dir=args.case_dir,
            out_dir=args.out_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
            skip_prepare=args.skip_prepare,
        )
    elif args.cmd == "validate-9p-fullseq-vcs":
        validate_9p_fullseq_vcs(
            case_dir=args.case_dir,
            out_dir=args.out_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
            skip_prepare=args.skip_prepare,
        )
    elif args.cmd == "validate-axi-board-fullseq-vcs":
        validate_axi_board_fullseq_vcs(
            case_dir=args.case_dir,
            out_dir=args.out_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
            skip_prepare=args.skip_prepare,
        )
    elif args.cmd == "validate-cnn-core-fullseq-vcs":
        validate_cnn_core_fullseq_vcs(
            case_dir=args.case_dir,
            out_dir=args.out_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
            skip_prepare=args.skip_prepare,
        )
    elif args.cmd == "validate-opt-acc-core-fullseq-vcs":
        validate_opt_acc_core_fullseq_vcs(
            case_dir=args.case_dir,
            out_dir=args.out_dir,
            build_root=args.build_root,
            build_jobs=args.build_jobs,
            skip_build=args.skip_build,
            skip_prepare=args.skip_prepare,
        )
    else:
        raise RuntimeError(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
