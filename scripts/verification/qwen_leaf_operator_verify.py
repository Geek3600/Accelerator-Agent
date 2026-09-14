#!/usr/bin/env python3
"""Run operator-local Qwen leaf verification and emit hierarchy evidence.

This is a case-adapter tool, not framework-core logic.  Stage7 calls it
through the generic leaf_functional_sim / leaf_golden_compare tool roles, and
the conservative hierarchy checker consumes the JSON reports emitted here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.semantic_simulator import (
    reusable_semantic_execution,
    run_configured_semantic_harness,
)


SCHEMA = "spatialaccagent.qwen_leaf_operator_verify.v0"
INTERNAL_TRACE_PREFIX = "SPATIALACC_INTERNAL_TRACE "


def safe_id(value: Any, default: str = "unknown") -> str:
    text = str(value or default).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or default


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def tail(text: str, limit: int = 8000) -> str:
    return text[-limit:] if text else ""


def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def env_timeout_sec(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def semantic_sim_timeout_sec() -> int:
    tool_budget = env_timeout_sec("SPATIALACC_TOOL_TIMEOUT_SEC", 0)
    return env_timeout_sec("SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC", tool_budget)


def semantic_stage_max_workers(stage_count: int) -> int:
    if stage_count <= 0:
        return 1
    return min(stage_count, env_int("SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS", 1))


def internal_trace_records(
    sim_log: Path,
    expected_stage_id: str,
    limit: int = 256,
    supplemental_paths: list[Path] | None = None,
    supplemental_texts: list[tuple[str, str]] | None = None,
) -> list[dict[str, Any]]:
    sources: list[tuple[str, str]] = []
    for path in [sim_log, *(supplemental_paths or [])]:
        if path.is_file():
            sources.append((str(path), path.read_text(encoding="utf-8", errors="replace")))
    sources.extend(
        (str(label), str(content))
        for label, content in (supplemental_texts or [])
        if str(content)
    )
    records: list[dict[str, Any]] = []
    seen_lines: set[str] = set()
    for source, text in sources:
        for line in text.splitlines():
            marker = line.find(INTERNAL_TRACE_PREFIX)
            if marker < 0:
                continue
            trace_line = line[marker:]
            if trace_line in seen_lines:
                continue
            seen_lines.add(trace_line)
            fields = dict(
                re.findall(
                    r"([A-Za-z_][A-Za-z0-9_]*)=\s*([^\s]+)",
                    trace_line[len(INTERNAL_TRACE_PREFIX) :],
                )
            )
            stage_id = str(fields.get("stage") or expected_stage_id)
            if stage_id != expected_stage_id:
                continue
            boundary = str(fields.get("boundary") or "unknown")
            module = str(fields.get("module") or boundary)
            data = str(fields.get("data") or "")

            def integer(name: str) -> int | None:
                try:
                    return int(str(fields.get(name)), 0) if fields.get(name) is not None else None
                except ValueError:
                    return None

            valid = integer("valid")
            ready = integer("ready")
            beat = integer("beat")
            contains_unknown = bool(re.search(r"[xz]", data, re.IGNORECASE))
            status = "fail" if valid == 1 and contains_unknown else "diagnostic_seed"
            records.append(
                {
                    "status": status,
                    "source": source,
                    "evidence_type": "semantic_internal_boundary_trace",
                    "failure_class": "unknown_logic_value" if status == "fail" else None,
                    "stage_id": stage_id,
                    "boundary_id": (
                        boundary
                        if boundary.startswith("boundary.")
                        else f"boundary.internal_{safe_id(stage_id)}_{safe_id(boundary)}"
                    ),
                    "module": module,
                    "contract": "internal_submodule_ready_valid_data",
                    "violated_contract": "internal_submodule_known_value_when_valid" if status == "fail" else None,
                    "cycle": integer("cycle"),
                    "beat_index": beat,
                    "logical_index": beat,
                    "tx_id": fields.get("tx"),
                    "tile_id": fields.get("tile"),
                    "observed_value": {
                        "valid": valid,
                        "ready": ready,
                        "packed_literal": data or None,
                    },
                    "expected_value": "known packed value whenever valid=1",
                    "summary": (
                        f"{module} emitted unknown data at internal boundary {boundary}"
                        if status == "fail"
                        else f"captured internal boundary {boundary}"
                    ),
                }
            )
            if len(records) >= limit:
                return records
    return records


def hex_const(width: int, value: int) -> str:
    digits = max(1, (width + 3) // 4)
    return f"{width}'h{value & ((1 << width) - 1):0{digits}x}"


def pack_lanes(width: int, values: list[int]) -> int:
    mask = (1 << width) - 1
    result = 0
    for index, value in enumerate(values):
        result |= (value & mask) << (width * index)
    return result


def signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def scalar_param(stage: dict[str, Any], names: list[str], default: int) -> int:
    bound = stage.get("bound_params", {}) if isinstance(stage.get("bound_params"), dict) else {}
    for name in names:
        row = bound.get(name)
        if isinstance(row, dict) and row.get("value") is not None:
            try:
                return int(row["value"])
            except (TypeError, ValueError):
                pass
        if stage.get(name) is not None:
            try:
                return int(stage[name])
            except (TypeError, ValueError):
                pass
    return default


def plan_stages(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "pipeline_planning" / "pipeline_plan.json"
    plan = read_json(path)
    return [stage for stage in plan.get("stages", []) if isinstance(stage, dict)]


def generated_dir(run_dir: Path) -> Path:
    return run_dir / "generated" / "chisel"


def require_sv(chisel_dir: Path, names: list[str]) -> list[Path]:
    paths = []
    for name in names:
        path = chisel_dir / name
        if not path.exists():
            raise FileNotFoundError(path)
        paths.append(path)
    return paths


def source_files(chisel_dir: Path, module: str) -> list[Path]:
    deps = {
        "RMSNorm": ["RMSNorm.sv", "VectorNorm.sv"],
        "QKVProjection": ["QKVProjection.sv", "Linear.sv"],
        "Queue1792_StreamBeat": ["Queue1792_StreamBeat.sv", "ram_1792x256.sv"],
        "Queue4_StreamBeat": ["Queue4_StreamBeat.sv", "ram_4x129.sv"],
    }
    return require_sv(chisel_dir, deps.get(module, [f"{module}.sv"]))


def source_text(run_dir: Path, module: str) -> str:
    path = generated_dir(run_dir) / f"{module}.sv"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def port_width(sv_text: str, port: str, default: int = 1) -> int:
    match = re.search(
        rf"\b(?:input|output)\s+(?:logic\s+|wire\s+|reg\s+)?(?:\[(\d+):(\d+)\]\s+)?{re.escape(port)}\b",
        sv_text,
    )
    if not match:
        return default
    if not match.group(1):
        return 1
    return abs(int(match.group(1)) - int(match.group(2))) + 1


def count_named_regs(sv_text: str, prefix: str) -> int:
    return len(set(re.findall(rf"\b{re.escape(prefix)}_(\d+)\b", sv_text)))


def output_beats_from_sv(sv_text: str, default: int = 1) -> int:
    match = re.search(r"io_out_bits_last_0\s*=\s*outCnt\s*==\s*(\d+)'h([0-9A-Fa-f]+)", sv_text)
    if match:
        return int(match.group(2), 16) + 1
    match = re.search(r"io_out_bits_last_0\s*=\s*outCnt\s*==\s*(\d+)'d(\d+)", sv_text)
    if match:
        return int(match.group(2)) + 1
    return default


def numeric_contract(stage: dict[str, Any]) -> dict[str, Any]:
    return stage.get("numeric_contract", {}) if isinstance(stage.get("numeric_contract"), dict) else {}


def shape_width(stage: dict[str, Any], key: str, default: int = 1) -> int:
    shape = stage.get(key, {}) if isinstance(stage.get(key), dict) else {}
    return scalar_param(shape, ["width"], default)


def elem_bits_for_stage(stage: dict[str, Any], default: int = 16) -> int:
    numeric = numeric_contract(stage)
    return scalar_param(
        {
            "bound_params": stage.get("bound_params", {}),
            "elem_bits": numeric.get("internal_elem_bits"),
            "input_bits": numeric.get("input_bits"),
        },
        ["elem_bits", "elemBits", "input_bits"],
        default,
    )


def linear_config_from_sv(run_dir: Path, module: str, stage: dict[str, Any]) -> dict[str, int]:
    sv_text = source_text(run_dir, module)
    elem_bits = elem_bits_for_stage(stage, 16)
    in_width = port_width(sv_text, "io_in_bits_data", max(1, shape_width(stage, "input_shape", 1) * elem_bits))
    out_width = port_width(sv_text, "io_out_bits_data", max(1, shape_width(stage, "output_shape", 1) * elem_bits))
    in_beats = count_named_regs(sv_text, "inputMem") or max(1, shape_width(stage, "input_shape", 1) // max(1, scalar_param(stage, ["lanes"], 1)))
    out_beats = output_beats_from_sv(sv_text, max(1, shape_width(stage, "output_shape", 1) // max(1, scalar_param(stage, ["lanes"], 1))))
    out_lanes = count_named_regs(sv_text, "acc") or max(1, scalar_param(stage, ["lanes"], 1))
    in_lanes = max(1, in_width // max(1, elem_bits))
    output_bits = max(1, out_width // max(1, out_lanes))
    addr_width = port_width(sv_text, "io_out_bits_addr", 1)
    max_cycles = max(2000, in_beats * out_beats + out_beats * 8 + 256)
    planned_latency = stage.get("latency", {}) if isinstance(stage.get("latency"), dict) else {}
    planned_cycles = scalar_param(planned_latency, ["cycles"], 0)
    if planned_cycles:
        max_cycles = max(max_cycles, min(planned_cycles * 2, max_cycles * 4))
    return {
        "in_width": in_width,
        "out_width": out_width,
        "elem_bits": elem_bits,
        "input_lanes": in_lanes,
        "output_lanes": out_lanes,
        "output_bits": output_bits,
        "addr_width": addr_width,
        "in_beats": in_beats,
        "out_beats": out_beats,
        "max_cycles": max_cycles,
    }


def run_command(argv: list[str], cwd: Path, timeout_sec: int) -> dict[str, Any]:
    started = time.monotonic()
    result: dict[str, Any] = {
        "argv": argv,
        "cwd": str(cwd),
        "timeout_sec": timeout_sec,
        "returncode": None,
        "status": "not_run",
        "stdout_tail": "",
        "stderr_tail": "",
        "duration_sec": 0.0,
    }
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=None if timeout_sec <= 0 else timeout_sec,
            check=False,
        )
        result["returncode"] = proc.returncode
        result["status"] = "pass" if proc.returncode == 0 else "fail"
        result["stdout_tail"] = tail(proc.stdout)
        result["stderr_tail"] = tail(proc.stderr)
    except subprocess.TimeoutExpired as exc:
        result["returncode"] = 124
        result["status"] = "fail"
        result["stdout_tail"] = tail(exc.stdout if isinstance(exc.stdout, str) else "")
        result["stderr_tail"] = tail(exc.stderr if isinstance(exc.stderr, str) else "")
    result["duration_sec"] = time.monotonic() - started
    return result


def parse_fail_diag(stdout: str) -> dict[str, Any]:
    match = re.search(r"FAIL_DIAG\s+([^\n\r]+)", stdout or "")
    if not match:
        return {}
    result: dict[str, Any] = {}
    for token in match.group(1).split():
        if "=" not in token:
            continue
        key, raw = token.split("=", 1)
        try:
            result[key] = int(raw, 0)
        except ValueError:
            result[key] = raw
    return result


def run_verilator(
    *,
    run_dir: Path,
    module: str,
    top_name: str,
    tb_text: str,
    timeout_sec: int,
) -> dict[str, Any]:
    chisel_dir = generated_dir(run_dir)
    work_dir = run_dir / "verification" / "operator_leaf_verilator" / top_name
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tb_path = work_dir / f"{top_name}.sv"
    tb_path.write_text(tb_text, encoding="utf-8")
    verilator = shutil.which("verilator")
    result: dict[str, Any] = {
        "module": module,
        "top_module": top_name,
        "work_dir": str(work_dir),
        "testbench": str(tb_path),
        "source_files": [],
        "compile": None,
        "run": None,
        "status": "fail",
        "summary": "",
    }
    if not verilator:
        result["summary"] = "verilator executable not found"
        return result
    try:
        sv_files = source_files(chisel_dir, module)
    except FileNotFoundError as exc:
        result["summary"] = f"required RTL source missing: {exc}"
        return result
    result["source_files"] = [str(path) for path in sv_files]
    obj_dir = work_dir / "obj_dir"
    compile_argv = [
        verilator,
        "--binary",
        "--sv",
        "--timing",
        "-Wno-fatal",
        "-Wno-WIDTH",
        "-Wno-UNOPTFLAT",
        "-Wno-CASEINCOMPLETE",
        "--Mdir",
        str(obj_dir),
        "--top-module",
        top_name,
        *[str(path) for path in sv_files],
        str(tb_path),
    ]
    compile_result = run_command(compile_argv, work_dir, timeout_sec)
    result["compile"] = compile_result
    if compile_result["status"] != "pass":
        result["summary"] = "verilator compile failed"
        return result
    binary = obj_dir / f"V{top_name}"
    if not binary.exists():
        result["summary"] = f"verilator binary missing: {binary}"
        return result
    run_result = run_command([str(binary)], work_dir, timeout_sec)
    result["run"] = run_result
    result["status"] = run_result["status"]
    result["summary"] = "verilator run passed" if run_result["status"] == "pass" else "verilator run failed"
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_contract(run_dir: Path, stage_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    contract = next(
        (
            row
            for row in manifest.get("stage_contracts", [])
            if isinstance(row, dict) and str(row.get("stage_id")) == stage_id
        ),
        {},
    )
    return manifest, contract


def run_semantic_harness(
    run_dir: Path,
    stage_id: str,
    contract: dict[str, Any],
    timeout_sec: int,
) -> dict[str, Any]:
    output_capture = Path(str(contract.get("rtl_output_capture") or ""))
    if output_capture.exists():
        output_capture.unlink()
    return run_configured_semantic_harness(run_dir, stage_id, contract, timeout_sec)


def decoded_memh(path: Path, bits: int, lanes: int) -> tuple[Any | None, dict[str, Any]]:
    import torch

    words: list[int] = []
    mask = (1 << bits) - 1
    unknown_count = 0
    first_unknown_index = None
    first_unknown_literal = None
    lines = path.read_text(encoding="ascii").splitlines()
    for index, raw in enumerate(lines):
        literal = raw.strip()
        if not literal or re.fullmatch(r"[0-9a-fA-F]+", literal) is None:
            unknown_count += 1
            if first_unknown_index is None:
                first_unknown_index = index
                first_unknown_literal = literal
            continue
        packed = int(literal, 16)
        words.extend((packed >> (lane * bits)) & mask for lane in range(lanes))
    if unknown_count:
        return None, {
            "status": "fail",
            "path": str(path),
            "word_count": len(lines),
            "unknown_word_count": unknown_count,
            "unknown_element_count": unknown_count * lanes,
            "first_unknown_word_index": first_unknown_index,
            "first_unknown_literal": first_unknown_literal,
            "summary": "memory capture contains Verilog unknown/high-impedance values",
        }
    if bits == 16:
        signed = [word - 0x10000 if word & 0x8000 else word for word in words]
        return torch.tensor(signed, dtype=torch.int16).view(torch.float16).float(), {}
    if bits == 32:
        signed = [word - 0x100000000 if word & 0x80000000 else word for word in words]
        return torch.tensor(signed, dtype=torch.int32).view(torch.float32), {}
    raise ValueError(f"unsupported semantic output width {bits}")


def ieee_value(word: int, bits: int) -> float:
    if bits == 16:
        return float(struct.unpack("<e", int(word & 0xFFFF).to_bytes(2, "little"))[0])
    if bits == 32:
        return float(struct.unpack("<f", int(word & 0xFFFFFFFF).to_bytes(4, "little"))[0])
    raise ValueError(f"unsupported semantic output width {bits}")


def memh_word_observation(path: Path, word_index: int, bits: int, lanes: int) -> dict[str, Any]:
    lines = path.read_text(encoding="ascii").splitlines()
    if word_index < 0 or word_index >= len(lines):
        return {
            "status": "fail",
            "path": str(path),
            "word_index": word_index,
            "error": "word index is outside the memory capture",
        }
    literal = lines[word_index].strip()
    if not literal or re.fullmatch(r"[0-9a-fA-F]+", literal) is None:
        return {
            "status": "unknown",
            "path": str(path),
            "word_index": word_index,
            "packed_literal": literal,
        }
    packed = int(literal, 16)
    mask = (1 << bits) - 1
    return {
        "status": "pass",
        "path": str(path),
        "word_index": word_index,
        "packed_literal": literal,
        "lanes": [
            {
                "lane_index": lane,
                "raw_bits": f"{(packed >> (lane * bits)) & mask:0{max(1, (bits + 3) // 4)}x}",
                "ieee_value": ieee_value((packed >> (lane * bits)) & mask, bits),
            }
            for lane in range(lanes)
        ],
    }


def numeric_compare(
    actual_path: Path,
    expected: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    import torch

    expected_path = Path(str(expected.get("path") or ""))
    bits = int(expected.get("bits") or 0)
    lanes = int(expected.get("lanes") or 0)
    if not expected_path.is_file() or sha256_file(expected_path) != expected.get("sha256"):
        return {"passed": False, "error": "expected target-model vector file/hash mismatch"}
    actual, actual_decode = decoded_memh(actual_path, bits, lanes)
    if actual is None:
        first_word = int(actual_decode.get("first_unknown_word_index") or 0)
        expected_word = memh_word_observation(expected_path, first_word, bits, lanes)
        unknown_elements = int(actual_decode.get("unknown_element_count") or 0)
        expected_elements = len(expected_path.read_text(encoding="ascii").splitlines()) * lanes
        return {
            "passed": False,
            "error": "RTL output contains Verilog unknown/high-impedance values",
            "failure_class": "unknown_logic_value",
            "num_elements": expected_elements,
            "num_mismatch": unknown_elements,
            "mismatch_fraction": unknown_elements / max(1, expected_elements),
            "max_mismatch_fraction": float(policy.get("max_mismatch_fraction")),
            "first_mismatch_index": first_word * lanes,
            "first_failed_word_index": first_word,
            "first_failed_beat_index": first_word,
            "first_failed_lane_index": 0,
            "first_actual_value": None,
            "first_expected_value": (
                expected_word.get("lanes", [{}])[0].get("ieee_value")
                if expected_word.get("status") == "pass"
                else None
            ),
            "first_absolute_error": None,
            "first_relative_error": None,
            "actual_output_sha256": sha256_file(actual_path),
            "expected_output_sha256": expected.get("sha256"),
            "actual_decode": actual_decode,
            "expected_word": expected_word,
        }
    golden, golden_decode = decoded_memh(expected_path, bits, lanes)
    if golden is None:
        return {
            "passed": False,
            "error": "target-model golden contains undecodable values",
            "expected_decode": golden_decode,
        }
    if actual.numel() != golden.numel():
        return {
            "passed": False,
            "num_actual": actual.numel(),
            "num_expected": golden.numel(),
            "error": "RTL output element count differs from target-model golden",
        }
    atol = float(policy.get("atol"))
    rtol = float(policy.get("rtol"))
    max_fraction = float(policy.get("max_mismatch_fraction"))
    finite = torch.isfinite(actual) & torch.isfinite(golden)
    close = torch.isclose(actual, golden, atol=atol, rtol=rtol, equal_nan=False) & finite
    mismatch = ~close
    mismatch_count = int(mismatch.sum().item())
    count = int(actual.numel())
    difference = torch.abs(actual - golden)
    finite_difference = difference[torch.isfinite(difference)]
    max_abs = float(finite_difference.max().item()) if finite_difference.numel() else float("inf")
    mean_abs = float(finite_difference.mean().item()) if finite_difference.numel() else float("inf")
    mismatch_fraction = mismatch_count / max(1, count)
    first_mismatch_index = int(torch.nonzero(mismatch, as_tuple=False)[0].item()) if mismatch_count else None
    first_actual = float(actual[first_mismatch_index].item()) if first_mismatch_index is not None else None
    first_expected = float(golden[first_mismatch_index].item()) if first_mismatch_index is not None else None
    first_absolute = abs(first_actual - first_expected) if first_actual is not None and first_expected is not None else None
    first_relative = None
    if first_absolute is not None and first_expected is not None:
        first_relative = first_absolute / abs(first_expected) if first_expected != 0 else (0.0 if first_absolute == 0 else float("inf"))
    return {
        "passed": mismatch_fraction <= max_fraction,
        "failure_class": None if mismatch_count == 0 else "numeric_mismatch",
        "num_elements": count,
        "num_mismatch": mismatch_count,
        "mismatch_fraction": mismatch_fraction,
        "max_mismatch_fraction": max_fraction,
        "max_abs_error": max_abs,
        "mean_abs_error": mean_abs,
        "atol": atol,
        "rtol": rtol,
        "first_mismatch_index": first_mismatch_index,
        "first_failed_word_index": first_mismatch_index // lanes if first_mismatch_index is not None else None,
        "first_failed_beat_index": first_mismatch_index // lanes if first_mismatch_index is not None else None,
        "first_failed_lane_index": first_mismatch_index % lanes if first_mismatch_index is not None else None,
        "first_actual_value": first_actual,
        "first_expected_value": first_expected,
        "first_absolute_error": first_absolute,
        "first_relative_error": first_relative,
        "actual_output_sha256": sha256_file(actual_path),
        "expected_output_sha256": expected.get("sha256"),
    }


def semantic_stage_report(
    run_dir: Path,
    stage: dict[str, Any],
    mode: str,
    timeout_sec: int,
    invocation_id: str,
) -> dict[str, Any]:
    stage_id = str(stage.get("stage_id") or "unknown")
    manifest, contract = semantic_contract(run_dir, stage_id)
    blockers: list[str] = []
    if manifest.get("status") != "ready":
        blockers.append("semantic testbench preparation is not ready")
    if contract.get("status") != "ready":
        blockers.append("stage semantic testbench contract is not ready")
    if blockers:
        return {
            "schema_version": SCHEMA,
            "gate": "leaf_functional" if mode == "functional" else "leaf_golden_compare",
            "mode": mode,
            "stage_id": stage_id,
            "stage": {"op": stage.get("op"), "kind": stage.get("kind")},
            "status": "fail",
            "summary": f"{stage_id} semantic verification preparation failed",
            "module_results": [],
            "blockers": blockers,
            "semantic_contract": contract,
            "debug_closure": {
                "mechanism": "contract_guided_leaf_boundary_verification",
                "root_candidate_module": contract.get("dut_harness", {}).get("top_module"),
            },
        }
    reuse_errors: list[str] = []
    execution = None
    reuse_prior_functional = mode == "functional" and env_flag(
        "SPATIALACC_REUSE_SEMANTIC_STAGE_RESULTS"
    )
    if mode == "golden" or reuse_prior_functional:
        functional_report = (
            run_dir / "verification" / "operator_leaf_functional" / f"{safe_id(stage_id)}.json"
        )
        golden_report = (
            run_dir / "verification" / "operator_leaf_golden" / f"{safe_id(stage_id)}.json"
        )
        candidate_reports = (
            [golden_report, functional_report]
            if mode == "golden"
            else [functional_report, golden_report]
        )
        candidate_errors: list[str] = []
        for candidate_report in candidate_reports:
            execution, errors = reusable_semantic_execution(
                run_dir,
                stage_id,
                contract,
                candidate_report,
            )
            if execution is not None:
                reuse_errors = []
                break
            candidate_errors.extend(f"{candidate_report.name}: {error}" for error in errors)
        else:
            reuse_errors = candidate_errors
    if execution is None:
        execution = run_semantic_harness(run_dir, stage_id, contract, timeout_sec)
    if execution.get("status") != "pass":
        blockers.append(str(execution.get("summary") or "semantic harness failed"))
    sim_log_path = Path(str(execution.get("sim_log") or ""))
    sim_stderr_path = Path(str(execution.get("sim_stderr_log") or ""))
    run_evidence = execution.get("run", {}) if isinstance(execution.get("run"), dict) else {}
    internal_trace = internal_trace_records(
        sim_log_path,
        stage_id,
        supplemental_paths=[sim_stderr_path],
        supplemental_texts=[
            ("semantic_simulator.run.stderr_tail", str(run_evidence.get("stderr_tail") or "")),
            ("semantic_simulator.run.stdout_tail", str(run_evidence.get("stdout_tail") or "")),
        ],
    )
    internal_failures = [record for record in internal_trace if record.get("status") == "fail"]
    comparison: dict[str, Any] = {}
    if mode == "golden" and not blockers:
        metrics = numeric_compare(
            Path(str(contract.get("rtl_output_capture"))),
            contract.get("expected_output", {}),
            manifest.get("numeric_comparison_policy", {}),
        )
        required_hashes = [
            str(row.get("sha256"))
            for row in contract.get("real_weight_bindings", [])
            if isinstance(row, dict) and row.get("sha256")
        ]
        comparison = {
            "status": "pass" if metrics.get("passed") is True else "fail",
            "passed": metrics.get("passed") is True,
            "expected_output_source": "target_model_inference",
            "expected_output_sha256": contract.get("expected_output", {}).get("sha256"),
            "rtl_output_sha256": execution.get("rtl_output_sha256"),
            "testbench_sha256": contract.get("testbench_sha256"),
            "consumed_tensor_hashes": contract.get("dut_harness", {}).get("consumed_tensor_hashes", []),
            "required_tensor_hashes": required_hashes,
            "numeric_metrics": metrics,
            "canonical_run_id": (
                execution.get("canonical_reuse", {}).get("canonical_run_id")
                if isinstance(execution.get("canonical_reuse"), dict)
                else invocation_id
            ),
        }
        if comparison["status"] != "pass":
            blockers.append("RTL output does not satisfy the target-model semantic numeric contract")
    status = "pass" if not blockers else "fail"
    harness = contract.get("dut_harness", {}) if isinstance(contract.get("dut_harness"), dict) else {}
    root_module = (
        internal_failures[0].get("module")
        if internal_failures
        else harness.get("top_module")
    )
    metrics = comparison.get("numeric_metrics", {}) if isinstance(comparison.get("numeric_metrics"), dict) else {}
    numeric_failure = mode == "golden" and comparison.get("status") == "fail"
    failure_record = None
    if numeric_failure:
        failure_record = {
            "status": "fail",
            "source": str(run_dir / "verification" / "operator_leaf_golden" / f"{safe_id(stage_id)}.json"),
            "evidence_type": "semantic_numeric_compare",
            "stage_id": stage_id,
            "module": root_module,
            "contract": "leaf_golden_compare",
            "violated_contract": "target_model_operator_semantics",
            "failure_class": metrics.get("failure_class") or "numeric_mismatch",
            "summary": metrics.get("error") or "RTL output failed the target-model numeric contract",
            "word_index": metrics.get("first_failed_word_index"),
            "beat_index": metrics.get("first_failed_beat_index"),
            "lane_index": metrics.get("first_failed_lane_index"),
            "logical_index": metrics.get("first_mismatch_index"),
            "tx_id": None,
            "tile_id": None,
            "observed_value": {
                "ieee_value": metrics.get("first_actual_value"),
                "packed_literal": metrics.get("actual_decode", {}).get("first_unknown_literal")
                if isinstance(metrics.get("actual_decode"), dict)
                else None,
            },
            "expected_value": {
                "ieee_value": metrics.get("first_expected_value"),
                "word": metrics.get("expected_word"),
            },
            "absolute_error": metrics.get("first_absolute_error"),
            "relative_error": metrics.get("first_relative_error"),
            "num_mismatch": metrics.get("num_mismatch"),
            "mismatch_fraction": metrics.get("mismatch_fraction"),
            "rtl_output_sha256": execution.get("rtl_output_sha256"),
            "input_fingerprint_sha256": execution.get("input_fingerprint_sha256"),
            "expected_output_sha256": comparison.get("expected_output_sha256"),
            "testbench_sha256": comparison.get("testbench_sha256"),
            "numeric_metrics": metrics,
        }
    failure_slice = [*internal_failures[:1], *([failure_record] if failure_record is not None else [])]
    if not failure_slice and status != "pass" and execution.get("status") != "pass":
        failure_slice = [execution]
    return {
        "schema_version": SCHEMA,
        "gate": "leaf_functional" if mode == "functional" else "leaf_golden_compare",
        "mode": mode,
        "stage_id": stage_id,
        "stage": {"op": stage.get("op"), "kind": stage.get("kind")},
        "status": status,
        "canonical_run_id": (
            execution.get("canonical_reuse", {}).get("canonical_run_id")
            if isinstance(execution.get("canonical_reuse"), dict)
            else invocation_id
        ),
        "execution_source": (
            "canonical_previous_semantic_real_tool_run"
            if isinstance(execution.get("canonical_reuse"), dict)
            else "fresh_real_tool_run"
        ),
        "canonical_reuse_errors": reuse_errors,
        "summary": f"{stage_id} real-weight semantic {mode} {'passed' if status == 'pass' else 'failed'}",
        "module_results": [execution],
        "blockers": blockers,
        "semantic_contract_path": contract.get("path"),
        "real_weight_execution": {
            "source_checkpoint_sha256": manifest.get("real_weight_source", {}).get("source_checkpoint_sha256"),
            "consumed_tensor_hashes": contract.get("dut_harness", {}).get("consumed_tensor_hashes", []),
            "random_input": manifest.get("random_input"),
        },
        "semantic_comparison": comparison,
        "internal_boundary_trace": internal_trace,
        "target_failure_diagnostics": metrics if numeric_failure else {},
        "first_failed_module": root_module if numeric_failure else None,
        "first_failed_summary": (
            internal_failures[0].get("summary")
            if internal_failures
            else failure_record.get("summary") if failure_record else None
        ),
        "debug_closure": {
            "mechanism": "contract_guided_leaf_boundary_verification",
            "causal_path": [stage_id],
            "root_candidate_module": root_module if status != "pass" else None,
            "failure_slice": failure_slice,
            "boundary_trace": [*internal_trace, *([failure_record] if failure_record is not None else [])],
        },
    }


def comb_norm_tb(module: str, top_name: str) -> str:
    words = [0x10000001, 0x20000002, 0x30008003, 0x40000004, 0x50000005, 0x6000FF06, 0x70000007, 0x80000008]
    expected = [word & 0xFFFF for word in words]
    return f"""
module {top_name};
  logic io_in_ready;
  logic io_in_valid;
  logic [255:0] io_in_bits_data;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [127:0] io_out_bits_data;
  logic io_out_bits_last;
  {module} dut (
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_last(io_out_bits_last)
  );
  initial begin
    io_out_ready = 1'b1;
    io_in_valid = 1'b1;
    io_in_bits_last = 1'b1;
    io_in_bits_data = {hex_const(256, pack_lanes(32, words))};
    #1;
    if (!io_in_ready || !io_out_valid || !io_out_bits_last) $fatal(1, "norm handshake failed");
    if (io_out_bits_data !== {hex_const(128, pack_lanes(16, expected))}) $fatal(1, "norm output mismatch");
    $display("PASS {module} exact boundary contract");
    $finish;
  end
endmodule
"""


def residual_tb(top_name: str) -> str:
    residual = [0x10, 0x20, 0x7FFFFFF0, 0x80000000, 0x5, 0x1000, 0xFFFFFFFF, 0xABCDEF01]
    computed = [0x1, 0x2, 0x30, 0x80000000, 0x6, 0x2000, 0x2, 0x01020304]
    expected = [(a + b) & 0xFFFFFFFF for a, b in zip(residual, computed)]
    return f"""
module {top_name};
  logic io_residual_ready;
  logic io_residual_valid;
  logic [255:0] io_residual_bits_data;
  logic io_computed_ready;
  logic io_computed_valid;
  logic [255:0] io_computed_bits_data;
  logic io_computed_bits_st;
  logic [10:0] io_computed_bits_addr;
  logic io_computed_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [255:0] io_out_bits_data;
  logic io_out_bits_st;
  logic [10:0] io_out_bits_addr;
  logic io_out_bits_last;
  ResidualAdd dut (
    .io_residual_ready(io_residual_ready),
    .io_residual_valid(io_residual_valid),
    .io_residual_bits_data(io_residual_bits_data),
    .io_computed_ready(io_computed_ready),
    .io_computed_valid(io_computed_valid),
    .io_computed_bits_data(io_computed_bits_data),
    .io_computed_bits_st(io_computed_bits_st),
    .io_computed_bits_addr(io_computed_bits_addr),
    .io_computed_bits_last(io_computed_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_st(io_out_bits_st),
    .io_out_bits_addr(io_out_bits_addr),
    .io_out_bits_last(io_out_bits_last)
  );
  initial begin
    io_out_ready = 1'b1;
    io_residual_valid = 1'b1;
    io_computed_valid = 1'b1;
    io_residual_bits_data = {hex_const(256, pack_lanes(32, residual))};
    io_computed_bits_data = {hex_const(256, pack_lanes(32, computed))};
    io_computed_bits_st = 1'b1;
    io_computed_bits_addr = 11'h155;
    io_computed_bits_last = 1'b1;
    #1;
    if (!io_residual_ready || !io_computed_ready || !io_out_valid) $fatal(1, "residual handshake failed");
    if (io_out_bits_data !== {hex_const(256, pack_lanes(32, expected))}) $fatal(1, "residual data mismatch");
    if (!io_out_bits_st || io_out_bits_addr !== 11'h155 || !io_out_bits_last) $fatal(1, "residual metadata mismatch");
    $display("PASS ResidualAdd exact boundary contract");
    $finish;
  end
endmodule
"""


def activation_tb(top_name: str) -> str:
    values = [0x0001, 0xFFFF, 0x7FFF, 0x8000, 0x0000, 0x00F0, 0xF000, 0x1234]
    expected = [0 if signed16(value) < 0 else value for value in values]
    return f"""
module {top_name};
  logic io_in_ready;
  logic io_in_valid;
  logic [127:0] io_in_bits_data;
  logic io_in_bits_st;
  logic [13:0] io_in_bits_addr;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [127:0] io_out_bits_data;
  logic io_out_bits_st;
  logic [13:0] io_out_bits_addr;
  logic io_out_bits_last;
  Activation dut (
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_st(io_in_bits_st),
    .io_in_bits_addr(io_in_bits_addr),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_st(io_out_bits_st),
    .io_out_bits_addr(io_out_bits_addr),
    .io_out_bits_last(io_out_bits_last)
  );
  initial begin
    io_out_ready = 1'b1;
    io_in_valid = 1'b1;
    io_in_bits_data = {hex_const(128, pack_lanes(16, values))};
    io_in_bits_st = 1'b1;
    io_in_bits_addr = 14'h25a;
    io_in_bits_last = 1'b1;
    #1;
    if (!io_in_ready || !io_out_valid) $fatal(1, "activation handshake failed");
    if (io_out_bits_data !== {hex_const(128, pack_lanes(16, expected))}) $fatal(1, "activation output mismatch");
    if (!io_out_bits_st || io_out_bits_addr !== 14'h25a || !io_out_bits_last) $fatal(1, "activation metadata mismatch");
    $display("PASS Activation exact boundary contract");
    $finish;
  end
endmodule
"""


def elementwise_mul_tb(top_name: str) -> str:
    lhs = [0x0003, 0x0004, 0x00F0, 0x0100, 0x7FFF, 0x8000, 0xFFFF, 0x1234]
    rhs = [0x0005, 0x0006, 0x0002, 0x0003, 0x0002, 0x0002, 0x0002, 0x0004]
    expected = [(a * b) & 0xFFFF for a, b in zip(lhs, rhs)]
    return f"""
module {top_name};
  logic io_lhs_ready;
  logic io_lhs_valid;
  logic [127:0] io_lhs_bits_data;
  logic io_lhs_bits_last;
  logic io_rhs_ready;
  logic io_rhs_valid;
  logic [127:0] io_rhs_bits_data;
  logic io_out_ready;
  logic io_out_valid;
  logic [127:0] io_out_bits_data;
  logic io_out_bits_last;
  ElementwiseMul dut (
    .io_lhs_ready(io_lhs_ready),
    .io_lhs_valid(io_lhs_valid),
    .io_lhs_bits_data(io_lhs_bits_data),
    .io_lhs_bits_last(io_lhs_bits_last),
    .io_rhs_ready(io_rhs_ready),
    .io_rhs_valid(io_rhs_valid),
    .io_rhs_bits_data(io_rhs_bits_data),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_last(io_out_bits_last)
  );
  initial begin
    io_out_ready = 1'b1;
    io_lhs_valid = 1'b1;
    io_rhs_valid = 1'b1;
    io_lhs_bits_last = 1'b1;
    io_lhs_bits_data = {hex_const(128, pack_lanes(16, lhs))};
    io_rhs_bits_data = {hex_const(128, pack_lanes(16, rhs))};
    #1;
    if (!io_lhs_ready || !io_rhs_ready || !io_out_valid || !io_out_bits_last) $fatal(1, "mul handshake failed");
    if (io_out_bits_data !== {hex_const(128, pack_lanes(16, expected))}) $fatal(1, "mul output mismatch");
    $display("PASS ElementwiseMul exact boundary contract");
    $finish;
  end
endmodule
"""


def rope_tb(top_name: str) -> str:
    values = [0x0001, 0x0002, 0x0003, 0x0004, 0x0005, 0x0006]
    even_expected = values
    odd_expected = [(-values[1]) & 0xFFFF, values[0], (-values[3]) & 0xFFFF, values[2], values[4], values[5]]
    return f"""
module {top_name};
  logic [3:0] io_position;
  logic io_in_ready;
  logic io_in_valid;
  logic [95:0] io_in_bits_data;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [95:0] io_out_bits_data;
  logic io_out_bits_last;
  RoPE dut (
    .io_position(io_position),
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_last(io_out_bits_last)
  );
  initial begin
    io_out_ready = 1'b1;
    io_in_valid = 1'b1;
    io_in_bits_last = 1'b1;
    io_in_bits_data = {hex_const(96, pack_lanes(16, values))};
    io_position = 4'h0;
    #1;
    if (!io_in_ready || !io_out_valid || io_out_bits_data !== {hex_const(96, pack_lanes(16, even_expected))}) $fatal(1, "rope even mismatch");
    io_position = 4'h1;
    #1;
    if (!io_out_valid || io_out_bits_data !== {hex_const(96, pack_lanes(16, odd_expected))}) $fatal(1, "rope odd mismatch");
    $display("PASS RoPE exact boundary contract");
    $finish;
  end
endmodule
"""


def linear_liveness_tb(module: str, top_name: str, in_width: int, out_width: int, in_beats: int, max_cycles: int) -> str:
    has_start = "io_start" if module != "AttentionGQA" else ""
    start_decl = "logic io_start;" if has_start else ""
    start_conn = ".io_start(io_start)," if has_start else ""
    start_init = "io_start = 1'b0;" if has_start else ""
    start_pulse = "io_start = 1'b1; @(posedge clock); io_start = 1'b0;" if has_start else ""
    qkv_probe_decls = ""
    qkv_probe_init = ""
    qkv_probe_update = ""
    qkv_fail_diag = ""
    if module == "QKVProjection":
        qkv_probe_decls = """
  integer linear_out_beats;
  integer linear_last_beats;
  integer collect_state_cycles;
  integer emit_state_cycles;
"""
        qkv_probe_init = """
    linear_out_beats = 0;
    linear_last_beats = 0;
    collect_state_cycles = 0;
    emit_state_cycles = 0;
"""
        qkv_probe_update = """
      if (!dut.state) collect_state_cycles = collect_state_cycles + 1;
      if (dut.state) emit_state_cycles = emit_state_cycles + 1;
      if (dut._linear_io_out_valid && !dut.state) begin
        linear_out_beats = linear_out_beats + 1;
        if (dut._linear_io_out_bits_last) linear_last_beats = linear_last_beats + 1;
      end
"""
        qkv_fail_diag = f"""
      $display("FAIL_DIAG module=QKVProjection accepted=%0d produced=%0d cycles=%0d max_cycles=%0d dut_state=%0d collectCnt=%0d headCnt=%0d beatCnt=%0d linear_out_beats=%0d linear_last_beats=%0d collect_state_cycles=%0d emit_state_cycles=%0d linear_state=%0d linear_inCnt=%0d linear_rowCnt=%0d linear_outCnt=%0d linear_io_out_valid=%0d linear_io_out_last=%0d io_in_ready=%0d io_out_valid=%0d",
               accepted, produced, cycles, {max_cycles}, dut.state, dut.collectCnt, dut.headCnt, dut.beatCnt,
               linear_out_beats, linear_last_beats, collect_state_cycles, emit_state_cycles,
               dut.linear.state, dut.linear.inCnt, dut.linear.rowCnt, dut.linear.outCnt,
               dut._linear_io_out_valid, dut._linear_io_out_bits_last, io_in_ready, io_out_valid);
"""
    data_ports = ""
    data_checks = ""
    if module in {"Linear_1", "Linear_2", "Linear_4"}:
        data_ports = """
  logic io_out_bits_st;
  logic [13:0] io_out_bits_addr_wide;
"""
        addr_conn = ".io_out_bits_addr(io_out_bits_addr_wide[10:0])," if module in {"Linear_1", "Linear_4"} else ".io_out_bits_addr(io_out_bits_addr_wide[13:0]),"
        data_checks = """
        if (^io_out_bits_data === 1'bx) $fatal(1, "linear output contains X");
"""
    else:
        addr_conn = ""
    return f"""
module {top_name};
  logic clock = 1'b0;
  logic reset;
  {start_decl}
  logic io_in_ready;
  logic io_in_valid;
  logic [{in_width - 1}:0] io_in_bits_data;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [{out_width - 1}:0] io_out_bits_data;
  logic io_out_bits_last;
  {data_ports}
  always #1 clock = ~clock;
  {module} dut (
    .clock(clock),
    .reset(reset),
    {start_conn}
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    {".io_out_bits_st(io_out_bits_st)," if module in {"Linear_1", "Linear_2", "Linear_4"} else ""}
    {addr_conn}
    .io_out_bits_last(io_out_bits_last)
  );
  integer accepted;
  integer produced;
  integer cycles;
  {qkv_probe_decls}
  initial begin
    reset = 1'b1;
    {start_init}
    io_in_valid = 1'b0;
    io_in_bits_data = '0;
    io_in_bits_last = 1'b0;
    io_out_ready = 1'b1;
    accepted = 0;
    produced = 0;
    cycles = 0;
    {qkv_probe_init}
    repeat (4) @(posedge clock);
    reset = 1'b0;
    {start_pulse}
    while (produced < 1 && cycles < {max_cycles}) begin
      @(negedge clock);
      if (accepted < {in_beats}) begin
        io_in_valid = 1'b1;
        io_in_bits_data = '0;
        io_in_bits_data[15:0] = accepted[15:0] + 16'h1;
        io_in_bits_last = accepted == ({in_beats} - 1);
      end else begin
        io_in_valid = 1'b0;
        io_in_bits_last = 1'b0;
      end
      @(posedge clock);
      if (io_in_valid && io_in_ready) accepted = accepted + 1;
      if (io_out_valid && io_out_ready) begin
        produced = produced + 1;
        {data_checks}
      end
      {qkv_probe_update}
      cycles = cycles + 1;
    end
    if (accepted != {in_beats}) $fatal(1, "{module} accepted %0d beats, expected {in_beats}", accepted);
    if (produced < 1) begin
      {qkv_fail_diag}
      $fatal(1, "{module} did not produce an output beat within {max_cycles} cycles");
    end
    $display("PASS {module} ready-valid liveness accepted=%0d produced=%0d cycles=%0d", accepted, produced, cycles);
    $finish;
  end
endmodule
"""


def lane_value(beat: int, lane: int) -> int:
    return ((beat % 23) + lane + 1) & 0xFFFF


def linear_expected_lanes(config: dict[str, int]) -> list[int]:
    out_lanes = config["output_lanes"]
    in_lanes = config["input_lanes"]
    in_beats = config["in_beats"]
    elem_mask = (1 << config["elem_bits"]) - 1
    values = []
    for lane in range(out_lanes):
        total = 0
        for beat in range(in_beats):
            total += signed16(lane_value(beat, lane % in_lanes) & elem_mask)
        values.append(total)
    return values


def linear_golden_tb(module: str, top_name: str, config: dict[str, int]) -> str:
    expected = linear_expected_lanes(config)
    expected_word = pack_lanes(config["output_bits"], expected)
    input_words = [
        hex_const(config["in_width"], pack_lanes(config["elem_bits"], [lane_value(beat, lane) for lane in range(config["input_lanes"])]))
        for beat in range(config["in_beats"])
    ]
    input_array = ",\n    ".join(input_words)
    has_metadata = module.startswith("Linear_")
    metadata_decls = """
  logic io_out_bits_st;
  logic [{addr_width}:0] io_out_bits_addr;
""" if has_metadata else ""
    metadata_conns = """
    .io_out_bits_st(io_out_bits_st),
    .io_out_bits_addr(io_out_bits_addr),
""" if has_metadata else ""
    metadata_checks = """
        if (produced == 0 && !io_out_bits_st) $fatal(1, "linear first output st mismatch");
        if (io_out_bits_addr !== produced[{addr_width}:0]) $fatal(1, "linear output addr mismatch produced=%0d addr=%0d", produced, io_out_bits_addr);
""" if has_metadata else ""
    metadata_decls = metadata_decls.format(addr_width=max(0, config["addr_width"] - 1)) if has_metadata else ""
    metadata_checks = metadata_checks.format(addr_width=max(0, config["addr_width"] - 1)) if has_metadata else ""
    return f"""
module {top_name};
  logic clock = 1'b0;
  logic reset;
  logic io_start;
  logic io_in_ready;
  logic io_in_valid;
  logic [{config['in_width'] - 1}:0] io_in_bits_data;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [{config['out_width'] - 1}:0] io_out_bits_data;
  logic io_out_bits_last;
  {metadata_decls}
  logic [{config['in_width'] - 1}:0] input_words [0:{config['in_beats'] - 1}];
  always #1 clock = ~clock;
  {module} dut (
    .clock(clock),
    .reset(reset),
    .io_start(io_start),
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    {metadata_conns}
    .io_out_bits_last(io_out_bits_last)
  );
  integer accepted;
  integer produced;
  integer cycles;
  initial begin
    input_words = '{{
    {input_array}
    }};
    reset = 1'b1;
    io_start = 1'b0;
    io_in_valid = 1'b0;
    io_in_bits_data = '0;
    io_in_bits_last = 1'b0;
    io_out_ready = 1'b1;
    accepted = 0;
    produced = 0;
    cycles = 0;
    repeat (4) @(posedge clock);
    reset = 1'b0;
    io_start = 1'b1;
    @(posedge clock);
    io_start = 1'b0;
    while (produced < {config['out_beats']} && cycles < {config['max_cycles']}) begin
      @(negedge clock);
      if (accepted < {config['in_beats']}) begin
        io_in_valid = 1'b1;
        io_in_bits_data = input_words[accepted];
        io_in_bits_last = accepted == ({config['in_beats']} - 1);
      end else begin
        io_in_valid = 1'b0;
        io_in_bits_data = '0;
        io_in_bits_last = 1'b0;
      end
      @(posedge clock);
      if (io_in_valid && io_in_ready) accepted = accepted + 1;
      if (io_out_valid && io_out_ready) begin
        if (io_out_bits_data !== {hex_const(config['out_width'], expected_word)}) $fatal(1, "linear golden data mismatch produced=%0d got=%h expected=%h", produced, io_out_bits_data, {hex_const(config['out_width'], expected_word)});
        {metadata_checks}
        if (io_out_bits_last !== (produced == ({config['out_beats']} - 1))) $fatal(1, "linear last mismatch produced=%0d last=%0d", produced, io_out_bits_last);
        produced = produced + 1;
      end
      cycles = cycles + 1;
    end
    if (accepted != {config['in_beats']}) $fatal(1, "{module} accepted %0d beats, expected {config['in_beats']}", accepted);
    if (produced != {config['out_beats']}) $fatal(1, "{module} produced %0d beats, expected {config['out_beats']}", produced);
    $display("PASS {module} independent linear golden accepted=%0d produced=%0d cycles=%0d", accepted, produced, cycles);
    $finish;
  end
endmodule
"""


def qkv_golden_config(run_dir: Path, stage: dict[str, Any]) -> dict[str, int]:
    config = qkv_liveness_config(stage)
    linear_config = linear_config_from_sv(run_dir, "Linear", stage)
    return {
        **config,
        "elem_bits": elem_bits_for_stage(stage, 16),
        "input_lanes": max(1, config["in_width"] // max(1, elem_bits_for_stage(stage, 16))),
        "linear_output_lanes": linear_config["output_lanes"],
        "head_dim": scalar_param(stage, ["head_dim", "headDim"], max(1, shape_width(stage, "output_shape", 1))),
        "qkv_elems_per_beat": scalar_param(stage, ["qkv_elems_per_beat", "qkvElemsPerBeat"], max(1, config["out_width"] // (3 * max(1, elem_bits_for_stage(stage, 16))))),
        "q_heads": scalar_param(stage, ["num_q_heads", "q_heads", "qHeads"], 1),
        "kv_heads": scalar_param(stage, ["num_kv_heads", "kv_heads", "kvHeads"], 1),
    }


def qkv_expected_word(config: dict[str, int], beat: int) -> int:
    accum = linear_expected_lanes(
        {
            "output_lanes": config["linear_output_lanes"],
            "input_lanes": config["input_lanes"],
            "in_beats": config["in_beats"],
            "elem_bits": config["elem_bits"],
            "output_bits": config["elem_bits"],
        }
    )
    qkv_elems = config["qkv_elems_per_beat"]
    base = (beat % max(1, config["emit_beats"] // max(1, config["q_heads"]))) * qkv_elems
    lanes = [accum[(base + idx) % len(accum)] for idx in range(qkv_elems)]
    return pack_lanes(config["elem_bits"], lanes + lanes + lanes)


def qkv_golden_tb(top_name: str, config: dict[str, int]) -> str:
    input_words = [
        hex_const(config["in_width"], pack_lanes(config["elem_bits"], [lane_value(beat, lane) for lane in range(config["input_lanes"])]))
        for beat in range(config["in_beats"])
    ]
    input_array = ",\n    ".join(input_words)
    expected_words = [
        hex_const(config["out_width"], qkv_expected_word(config, beat))
        for beat in range(config["emit_beats"])
    ]
    expected_array = ",\n    ".join(expected_words)
    return f"""
module {top_name};
  logic clock = 1'b0;
  logic reset;
  logic io_start;
  logic io_in_ready;
  logic io_in_valid;
  logic [{config['in_width'] - 1}:0] io_in_bits_data;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [{config['out_width'] - 1}:0] io_out_bits_data;
  logic io_out_bits_last;
  logic [{config['in_width'] - 1}:0] input_words [0:{config['in_beats'] - 1}];
  logic [{config['out_width'] - 1}:0] expected_words [0:{config['emit_beats'] - 1}];
  always #1 clock = ~clock;
  QKVProjection dut (
    .clock(clock),
    .reset(reset),
    .io_start(io_start),
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_last(io_out_bits_last)
  );
  integer accepted;
  integer produced;
  integer cycles;
  initial begin
    input_words = '{{
    {input_array}
    }};
    expected_words = '{{
    {expected_array}
    }};
    reset = 1'b1;
    io_start = 1'b0;
    io_in_valid = 1'b0;
    io_in_bits_data = '0;
    io_in_bits_last = 1'b0;
    io_out_ready = 1'b1;
    accepted = 0;
    produced = 0;
    cycles = 0;
    repeat (4) @(posedge clock);
    reset = 1'b0;
    io_start = 1'b1;
    @(posedge clock);
    io_start = 1'b0;
    while (produced < {config['emit_beats']} && cycles < {config['max_cycles']}) begin
      @(negedge clock);
      if (accepted < {config['in_beats']}) begin
        io_in_valid = 1'b1;
        io_in_bits_data = input_words[accepted];
        io_in_bits_last = accepted == ({config['in_beats']} - 1);
      end else begin
        io_in_valid = 1'b0;
        io_in_bits_data = '0;
        io_in_bits_last = 1'b0;
      end
      @(posedge clock);
      if (io_in_valid && io_in_ready) accepted = accepted + 1;
      if (io_out_valid && io_out_ready) begin
        if (io_out_bits_data !== expected_words[produced]) $fatal(1, "QKVProjection golden data mismatch produced=%0d got=%h expected=%h", produced, io_out_bits_data, expected_words[produced]);
        if (io_out_bits_last !== (produced == ({config['emit_beats']} - 1))) $fatal(1, "QKVProjection last mismatch produced=%0d last=%0d", produced, io_out_bits_last);
        produced = produced + 1;
      end
      cycles = cycles + 1;
    end
    if (accepted != {config['in_beats']}) $fatal(1, "QKVProjection accepted %0d beats, expected {config['in_beats']}", accepted);
    if (produced != {config['emit_beats']}) $fatal(1, "QKVProjection produced %0d beats, expected {config['emit_beats']}", produced);
    $display("PASS QKVProjection independent qkv packing golden accepted=%0d produced=%0d cycles=%0d", accepted, produced, cycles);
    $finish;
  end
endmodule
"""


def attention_golden_config(run_dir: Path, stage: dict[str, Any]) -> dict[str, int]:
    sv_text = source_text(run_dir, "AttentionGQA")
    elem_bits = elem_bits_for_stage(stage, 16)
    in_width = port_width(sv_text, "io_in_bits_data", 3 * 2 * elem_bits)
    out_width = port_width(sv_text, "io_out_bits_data", max(1, scalar_param(stage, ["head_dim", "headDim"], 1) * elem_bits))
    qkv_elems = max(1, in_width // max(1, 3 * elem_bits))
    head_dim = max(1, out_width // max(1, elem_bits))
    head_beats = max(1, (head_dim + qkv_elems - 1) // qkv_elems)
    return {
        "elem_bits": elem_bits,
        "in_width": in_width,
        "out_width": out_width,
        "qkv_elems_per_beat": qkv_elems,
        "head_dim": head_dim,
        "head_beats": head_beats,
        "max_cycles": max(2000, head_beats * 8 + 128),
    }


def attention_golden_tb(top_name: str, config: dict[str, int]) -> str:
    qkv_elems = config["qkv_elems_per_beat"]
    input_values = []
    expected_values = []
    for beat in range(config["head_beats"]):
        q_vals = [0x100 + beat * qkv_elems + lane for lane in range(qkv_elems)]
        k_vals = [0x200 + beat * qkv_elems + lane for lane in range(qkv_elems)]
        v_vals = [0x300 + beat * qkv_elems + lane for lane in range(qkv_elems)]
        input_values.append(hex_const(config["in_width"], pack_lanes(config["elem_bits"], q_vals + k_vals + v_vals)))
        expected_values.extend(v_vals)
    expected_word = pack_lanes(config["elem_bits"], expected_values[: config["head_dim"]])
    input_array = ",\n    ".join(input_values)
    return f"""
module {top_name};
  logic clock = 1'b0;
  logic reset;
  logic io_in_ready;
  logic io_in_valid;
  logic [{config['in_width'] - 1}:0] io_in_bits_data;
  logic io_in_bits_last;
  logic io_out_ready;
  logic io_out_valid;
  logic [{config['out_width'] - 1}:0] io_out_bits_data;
  logic io_out_bits_last;
  logic [{config['in_width'] - 1}:0] input_words [0:{config['head_beats'] - 1}];
  always #1 clock = ~clock;
  AttentionGQA dut (
    .clock(clock),
    .reset(reset),
    .io_in_ready(io_in_ready),
    .io_in_valid(io_in_valid),
    .io_in_bits_data(io_in_bits_data),
    .io_in_bits_last(io_in_bits_last),
    .io_out_ready(io_out_ready),
    .io_out_valid(io_out_valid),
    .io_out_bits_data(io_out_bits_data),
    .io_out_bits_last(io_out_bits_last)
  );
  integer accepted;
  integer produced;
  integer cycles;
  initial begin
    input_words = '{{
    {input_array}
    }};
    reset = 1'b1;
    io_in_valid = 1'b0;
    io_in_bits_data = '0;
    io_in_bits_last = 1'b0;
    io_out_ready = 1'b1;
    accepted = 0;
    produced = 0;
    cycles = 0;
    repeat (4) @(posedge clock);
    reset = 1'b0;
    while (produced < 1 && cycles < {config['max_cycles']}) begin
      @(negedge clock);
      if (accepted < {config['head_beats']}) begin
        io_in_valid = 1'b1;
        io_in_bits_data = input_words[accepted];
        io_in_bits_last = accepted == ({config['head_beats']} - 1);
      end else begin
        io_in_valid = 1'b0;
        io_in_bits_data = '0;
        io_in_bits_last = 1'b0;
      end
      @(posedge clock);
      if (io_in_valid && io_in_ready) accepted = accepted + 1;
      if (io_out_valid && io_out_ready) begin
        if (io_out_bits_data !== {hex_const(config['out_width'], expected_word)}) $fatal(1, "AttentionGQA V-vector golden mismatch got=%h expected=%h", io_out_bits_data, {hex_const(config['out_width'], expected_word)});
        if (!io_out_bits_last) $fatal(1, "AttentionGQA last mismatch");
        produced = produced + 1;
      end
      cycles = cycles + 1;
    end
    if (accepted != {config['head_beats']}) $fatal(1, "AttentionGQA accepted %0d beats, expected {config['head_beats']}", accepted);
    if (produced != 1) $fatal(1, "AttentionGQA did not produce golden output");
    $display("PASS AttentionGQA independent V-vector golden accepted=%0d produced=%0d cycles=%0d", accepted, produced, cycles);
    $finish;
  end
endmodule
"""


def golden_tb(run_dir: Path, module: str, top_name: str, stage: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    if module in {"Linear_1", "Linear_2", "Linear_4"}:
        config = linear_config_from_sv(run_dir, module, stage)
        return linear_golden_tb(module, top_name, config), {"derivation": "rtl_port_and_stage_bound_linear_default_weight_golden", **config}
    if module == "QKVProjection":
        config = qkv_golden_config(run_dir, stage)
        return qkv_golden_tb(top_name, config), {"derivation": "stage_bound_qkv_projection_default_weight_packing_golden", **config}
    if module == "AttentionGQA":
        config = attention_golden_config(run_dir, stage)
        return attention_golden_tb(top_name, config), {"derivation": "stage_bound_attention_v_vector_boundary_golden", **config}
    if module in {"Queue1792_StreamBeat", "Queue4_StreamBeat"}:
        sv_text = source_text(run_dir, module)
        width = port_width(sv_text, "io_enq_bits_data", 256 if module == "Queue1792_StreamBeat" else 128)
        return queue_tb(module, top_name, width), {"derivation": "queue_single_transaction_data_preservation_golden", "width": width}
    return None


def queue_tb(module: str, top_name: str, width: int) -> str:
    addr_decl = "logic [10:0] io_enq_bits_addr;" if module == "Queue1792_StreamBeat" else "logic [13:0] io_enq_bits_addr;"
    last_out = "" if module == "Queue1792_StreamBeat" else "logic io_deq_bits_last;"
    last_conn = "" if module == "Queue1792_StreamBeat" else ",\n    .io_deq_bits_last(io_deq_bits_last)"
    last_check = "" if module == "Queue1792_StreamBeat" else "if (!io_deq_bits_last) $fatal(1, \"queue last mismatch\");"
    return f"""
module {top_name};
  logic clock = 1'b0;
  logic reset;
  logic io_enq_ready;
  logic io_enq_valid;
  logic [{width - 1}:0] io_enq_bits_data;
  logic io_enq_bits_st;
  {addr_decl}
  logic io_enq_bits_last;
  logic io_deq_ready;
  logic io_deq_valid;
  logic [{width - 1}:0] io_deq_bits_data;
  {last_out}
  always #1 clock = ~clock;
  {module} dut (
    .clock(clock),
    .reset(reset),
    .io_enq_ready(io_enq_ready),
    .io_enq_valid(io_enq_valid),
    .io_enq_bits_data(io_enq_bits_data),
    .io_enq_bits_st(io_enq_bits_st),
    .io_enq_bits_addr(io_enq_bits_addr),
    .io_enq_bits_last(io_enq_bits_last),
    .io_deq_ready(io_deq_ready),
    .io_deq_valid(io_deq_valid),
    .io_deq_bits_data(io_deq_bits_data){last_conn}
  );
  initial begin
    reset = 1'b1;
    io_enq_valid = 1'b0;
    io_deq_ready = 1'b0;
    io_enq_bits_data = {hex_const(width, 0x123456789abcdef)};
    io_enq_bits_st = 1'b1;
    io_enq_bits_addr = '0;
    io_enq_bits_last = 1'b1;
    repeat (3) @(posedge clock);
    reset = 1'b0;
    @(negedge clock);
    io_enq_valid = 1'b1;
    @(posedge clock);
    if (!io_enq_ready) $fatal(1, "queue not ready for first enqueue");
    @(negedge clock);
    io_enq_valid = 1'b0;
    io_deq_ready = 1'b0;
    #1;
    if (!io_deq_valid) $fatal(1, "queue did not produce dequeue valid");
    if (io_deq_bits_data !== {hex_const(width, 0x123456789abcdef)}) $fatal(1, "queue data mismatch");
    {last_check}
    io_deq_ready = 1'b1;
    @(posedge clock);
    $display("PASS {module} single-transaction ready-valid contract");
    $finish;
  end
endmodule
"""


def exact_tb(module: str, top_name: str) -> str | None:
    if module in {"RMSNorm", "VectorNorm"}:
        return comb_norm_tb(module, top_name)
    if module == "ResidualAdd":
        return residual_tb(top_name)
    if module == "Activation":
        return activation_tb(top_name)
    if module == "ElementwiseMul":
        return elementwise_mul_tb(top_name)
    if module == "RoPE":
        return rope_tb(top_name)
    return None


def qkv_liveness_config(stage: dict[str, Any]) -> dict[str, int]:
    hidden = scalar_param(stage, ["hidden_size", "hiddenSize"], shape_width(stage, "input_shape", 1))
    lanes = scalar_param(stage, ["lanes"], numeric_contract(stage).get("lanes") or 1)
    elem_bits = elem_bits_for_stage(stage, 16)
    q_heads = scalar_param(stage, ["num_q_heads", "q_heads", "qHeads"], 1)
    kv_heads = scalar_param(stage, ["num_kv_heads", "kv_heads", "kvHeads"], 1)
    head_dim = scalar_param(stage, ["head_dim", "headDim"], 1)
    qkv_elems_per_beat = scalar_param(stage, ["qkv_elems_per_beat", "qkvElemsPerBeat"], 2)
    in_beats = max(1, hidden // max(1, lanes))
    out_dim = max(1, (q_heads + 2 * kv_heads) * head_dim)
    linear_out_beats = max(1, (out_dim + lanes - 1) // max(1, lanes))
    emit_beats = max(1, q_heads * ((head_dim + qkv_elems_per_beat - 1) // max(1, qkv_elems_per_beat)))
    estimated_cycles = in_beats + linear_out_beats * (in_beats + 4) + emit_beats + 1024
    planned_latency = stage.get("latency", {}) if isinstance(stage.get("latency"), dict) else {}
    planned_cycles = scalar_param(planned_latency, ["cycles"], 0)
    max_cycles = max(2000, estimated_cycles, planned_cycles * 2 if planned_cycles else 0)
    return {
        "in_width": lanes * elem_bits,
        "out_width": 3 * qkv_elems_per_beat * elem_bits,
        "in_beats": in_beats,
        "max_cycles": max_cycles,
        "linear_out_beats": linear_out_beats,
        "emit_beats": emit_beats,
        "estimated_cycles": estimated_cycles,
    }


def liveness_tb(run_dir: Path, module: str, top_name: str, stage: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]] | None:
    if module == "QKVProjection":
        config = qkv_liveness_config(stage or {})
        return (
            linear_liveness_tb(module, top_name, config["in_width"], config["out_width"], config["in_beats"], config["max_cycles"]),
            {
                "derivation": "stage_bound_qkv_projection_liveness",
                **config,
            },
        )
    if module == "AttentionGQA":
        config = attention_golden_config(run_dir, stage or {})
        return (
            linear_liveness_tb(module, top_name, config["in_width"], config["out_width"], config["head_beats"], config["max_cycles"]),
            {
                "derivation": "rtl_port_and_stage_bound_attention_liveness",
                "in_width": config["in_width"],
                "out_width": config["out_width"],
                "in_beats": config["head_beats"],
                "max_cycles": config["max_cycles"],
            },
        )
    if module in {"Linear_1", "Linear_2", "Linear_4"}:
        config = linear_config_from_sv(run_dir, module, stage or {})
        return (
            linear_liveness_tb(module, top_name, config["in_width"], config["out_width"], config["in_beats"], config["max_cycles"]),
            {
                "derivation": "rtl_port_and_stage_bound_linear_liveness",
                **config,
            },
        )
    if module in {"Queue1792_StreamBeat", "Queue4_StreamBeat"}:
        sv_text = source_text(run_dir, module)
        width = port_width(sv_text, "io_enq_bits_data", 1)
        return queue_tb(module, top_name, width), {"derivation": "queue_single_transaction_contract", "width": width}
    return None


def stage_modules(stage: dict[str, Any]) -> list[dict[str, str]]:
    kind = str(stage.get("kind", ""))
    op = str(stage.get("op", ""))
    if kind == "norm":
        return [{"module": "RMSNorm", "coverage": "exact"}, {"module": "VectorNorm", "coverage": "exact"}]
    if kind == "attention":
        return [
            {"module": "QKVProjection", "coverage": "liveness"},
            {"module": "RoPE", "coverage": "exact"},
            {"module": "AttentionGQA", "coverage": "liveness"},
            {"module": "Linear_1", "coverage": "liveness"},
        ]
    if kind == "residual":
        return [{"module": "ResidualAdd", "coverage": "exact"}, {"module": "Queue1792_StreamBeat", "coverage": "liveness"}]
    if op in {"mlp_gate_proj", "mlp_up_proj"}:
        return [{"module": "Linear_2", "coverage": "liveness"}]
    if op == "mlp_down_proj":
        return [{"module": "Linear_4", "coverage": "liveness"}]
    if op == "activation_mul" or kind in {"activation", "activation_mul"}:
        return [{"module": "Activation", "coverage": "exact"}, {"module": "ElementwiseMul", "coverage": "exact"}]
    return []


def run_module_check(run_dir: Path, stage: dict[str, Any], module_row: dict[str, str], mode: str, timeout_sec: int) -> dict[str, Any]:
    stage_id = str(stage.get("stage_id") or "unknown")
    module = module_row["module"]
    coverage = module_row["coverage"]
    top_name = f"tb_{safe_id(stage_id)}_{safe_id(module)}_{mode}"
    result: dict[str, Any] = {
        "module": module,
        "coverage": coverage,
        "mode": mode,
        "status": "fail",
        "blockers": [],
    }
    tb_text = exact_tb(module, top_name)
    verifier_contract: dict[str, Any] = {}
    if mode == "golden" and tb_text is None:
        golden = golden_tb(run_dir, module, top_name, stage)
        if golden is not None:
            tb_text, verifier_contract = golden
    if mode == "golden" and tb_text is None:
        result["blockers"].append(
            "independent golden boundary reference is not implemented for this stateful leaf; "
            "do not promote to single-layer verification until this module has a real golden compare"
        )
        result["summary"] = "missing independent golden reference"
        return result
    if tb_text is None and mode == "functional":
        liveness = liveness_tb(run_dir, module, top_name, stage)
        if liveness is not None:
            tb_text, verifier_contract = liveness
    if tb_text is None:
        result["blockers"].append(f"no verifier template is registered for module {module}")
        result["summary"] = "verifier template missing"
        return result
    if verifier_contract:
        key = "golden_contract" if mode == "golden" else "liveness_contract"
        result[key] = verifier_contract
    verilator_result = run_verilator(
        run_dir=run_dir,
        module=module,
        top_name=top_name,
        tb_text=tb_text,
        timeout_sec=timeout_sec,
    )
    result["verilator"] = verilator_result
    result["status"] = verilator_result["status"]
    result["summary"] = verilator_result.get("summary", "")
    run_stdout = ""
    if isinstance(verilator_result.get("run"), dict):
        run_stdout = str(verilator_result["run"].get("stdout_tail") or "")
    diagnostics = parse_fail_diag(run_stdout)
    if diagnostics:
        result["failure_diagnostics"] = diagnostics
    if result["status"] != "pass":
        result["blockers"].append(f"{module} {mode} verifier failed: {result['summary']}")
    return result


def stage_report(
    run_dir: Path,
    stage: dict[str, Any],
    mode: str,
    timeout_sec: int,
    invocation_id: str,
) -> dict[str, Any]:
    stage_id = str(stage.get("stage_id") or "unknown")
    semantic_manifest = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    if semantic_manifest.exists():
        return semantic_stage_report(run_dir, stage, mode, timeout_sec, invocation_id)
    modules = stage_modules(stage)
    blockers: list[str] = []
    module_results = []
    if not modules:
        blockers.append(f"no leaf module verification mapping for stage {stage_id}")
    for module_row in modules:
        module_result = run_module_check(run_dir, stage, module_row, mode, timeout_sec)
        module_results.append(module_result)
        blockers.extend(str(item) for item in module_result.get("blockers", []))
    status = "pass" if not blockers else "fail"
    root_candidate = None
    failure_slice = []
    for module_result in module_results:
        if module_result.get("status") != "pass":
            root_candidate = module_result.get("module")
            failure_slice = [module_result]
            break
    gate = "leaf_functional" if mode == "functional" else "leaf_golden_compare"
    return {
        "schema_version": SCHEMA,
        "gate": gate,
        "mode": mode,
        "stage_id": stage_id,
        "stage": {
            "op": stage.get("op"),
            "kind": stage.get("kind"),
        },
        "status": status,
        "canonical_run_id": invocation_id,
        "execution_source": "fresh_real_tool_run",
        "summary": f"{stage_id} {mode} {'passed' if status == 'pass' else 'failed'} with {len(module_results)} module check(s)",
        "module_results": module_results,
        "blockers": blockers,
        "debug_closure": {
            "mechanism": "contract_guided_leaf_boundary_verification",
            "causal_path": [stage_id],
            "root_candidate_module": root_candidate,
            "repair_context_policy": "repair only the earliest failing leaf module and preserve the ready-valid boundary contract",
            "failure_slice": failure_slice,
        },
    }


def aggregate_report(run_dir: Path, stage_reports: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    blockers = []
    checks = []
    for report in stage_reports:
        checks.append(
            {
                "name": f"{report.get('stage_id')}.{mode}",
                "status": report.get("status"),
                "summary": report.get("summary"),
                "path": report.get("path"),
            }
        )
        for blocker in report.get("blockers", []):
            blockers.append(f"{report.get('stage_id')}: {blocker}")
    gate = "leaf_functional" if mode == "functional" else "leaf_golden_compare"
    return {
        "schema_version": SCHEMA,
        "gate": gate,
        "mode": mode,
        "status": "pass" if not blockers else "fail",
        "run_dir": str(run_dir),
        "checks": checks,
        "blockers": blockers,
        "summary": f"{gate} {'passed' if not blockers else 'failed'} for {len(stage_reports)} pipeline stage(s)",
        "canonical_run_ids": sorted(
            {str(report.get("canonical_run_id")) for report in stage_reports if report.get("canonical_run_id")}
        ),
        "all_golden_comparisons_derived_from_functional_runs": (
            mode == "golden"
            and bool(stage_reports)
            and all(report.get("execution_source") == "canonical_functional_real_tool_run" for report in stage_reports)
        ),
        "debug_closure": {
            "mechanism": "contract_guided_debug_closure",
            "first_failing_stage": next((report.get("stage_id") for report in stage_reports if report.get("status") != "pass"), None),
            "root_candidate_module": next(
                (
                    report.get("debug_closure", {}).get("root_candidate_module")
                    for report in stage_reports
                    if report.get("debug_closure", {}).get("root_candidate_module")
                ),
                None,
            ),
            "repair_context_policy": "feed failed stage report, module verifier log, and boundary contract into the repair agent",
        },
    }


def execute_stage_reports(
    run_dir: Path,
    stages: list[dict[str, Any]],
    mode: str,
    timeout_sec: int,
    invocation_id: str,
    out_dir: Path,
) -> list[dict[str, Any]]:
    def execute(index: int, stage: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        stage_id = str(stage.get("stage_id") or "unknown")
        try:
            report = stage_report(run_dir, stage, mode, timeout_sec, invocation_id)
        except Exception as exc:
            report = {
                "schema_version": SCHEMA,
                "gate": "leaf_functional" if mode == "functional" else "leaf_golden_compare",
                "mode": mode,
                "stage_id": stage_id,
                "stage": {"op": stage.get("op"), "kind": stage.get("kind")},
                "status": "fail",
                "summary": f"{stage_id} {mode} verifier raised {type(exc).__name__}",
                "module_results": [],
                "blockers": [f"stage verifier exception: {type(exc).__name__}: {exc}"],
                "exception_traceback": traceback.format_exc()[-12000:],
                "debug_closure": {
                    "mechanism": "contract_guided_leaf_boundary_verification",
                    "causal_path": [stage_id],
                    "root_candidate_module": None,
                },
            }
        path = out_dir / f"{safe_id(report['stage_id'])}.json"
        report["path"] = str(path)
        write_json(path, report)
        return index, report

    workers = semantic_stage_max_workers(len(stages))
    if workers == 1:
        return [execute(index, stage)[1] for index, stage in enumerate(stages)]

    ordered: list[dict[str, Any] | None] = [None] * len(stages)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="semantic-stage") as executor:
        futures = [executor.submit(execute, index, stage) for index, stage in enumerate(stages)]
        for future in as_completed(futures):
            index, report = future.result()
            ordered[index] = report
    return [report for report in ordered if report is not None]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--mode", choices=["functional", "golden"], required=True)
    parser.add_argument("--stage-id", default="")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir).resolve()
    timeout_sec = semantic_sim_timeout_sec()
    focus_stage = args.stage_id.strip() or os.environ.get("SPATIALACC_PIPELINE_STAGE_ID", "").strip()
    stages = plan_stages(run_dir)
    if focus_stage:
        stages = [stage for stage in stages if str(stage.get("stage_id")) == focus_stage]
    if not stages:
        report = {
            "schema_version": SCHEMA,
            "gate": "leaf_functional" if args.mode == "functional" else "leaf_golden_compare",
            "mode": args.mode,
            "status": "fail",
            "run_dir": str(run_dir),
            "checks": [],
            "blockers": [f"no pipeline stages selected for focus={focus_stage or '<all>'}"],
        }
        out_dir = run_dir / "verification" / ("operator_leaf_functional" if args.mode == "functional" else "operator_leaf_golden")
        write_json(out_dir / "summary.json", report)
        return 1

    out_dir = run_dir / "verification" / ("operator_leaf_functional" if args.mode == "functional" else "operator_leaf_golden")
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    invocation_id = f"operator-leaf-{args.mode}-{uuid.uuid4().hex}"
    reports = execute_stage_reports(
        run_dir,
        stages,
        args.mode,
        timeout_sec,
        invocation_id,
        out_dir,
    )
    aggregate = aggregate_report(run_dir, reports, args.mode)
    hierarchy_name = "leaf_functional.json" if args.mode == "functional" else "leaf_golden_compare.json"
    if focus_stage:
        focus_name = safe_id(focus_stage)
        write_json(out_dir / f"summary_{focus_name}.json", aggregate)
        diagnostics_dir = run_dir / "verification" / "case_diagnostics" / "leaf_replay"
        write_json(diagnostics_dir / f"{focus_name}_{args.mode}.json", aggregate)
        write_json(hierarchy_dir / f"{hierarchy_name.removesuffix('.json')}_{focus_name}.json", aggregate)
    else:
        write_json(out_dir / "summary.json", aggregate)
        write_json(hierarchy_dir / hierarchy_name, aggregate)
    print(json.dumps({"status": aggregate["status"], "summary": aggregate["summary"], "blockers": aggregate["blockers"][:8]}, indent=2))
    return 0 if aggregate["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
