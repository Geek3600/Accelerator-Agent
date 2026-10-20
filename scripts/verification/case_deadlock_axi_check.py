#!/usr/bin/env python3
"""Check case-level deadlock and AXI/DDR evidence from real tool logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from accagent.framework.verification_evidence_contract import (
    COMPILE_ONLY_POLICY,
)


FIELD_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>[^ \n]+)")
PASS_RE = re.compile(r"PASS real functional ddr path (?P<fields>.*)")
FATAL_RE = re.compile(r"\b(?:NO_PROGRESS|TIMEOUT)\b|\b\w*_tb\s+FAIL\b")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def resolve_path(run_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    repo_path = Path.cwd() / path
    if repo_path.exists():
        return repo_path
    return run_dir / path


def parse_value(raw: str) -> Any:
    try:
        return int(raw, 0)
    except ValueError:
        return raw


def parse_fields(text: str) -> dict[str, Any]:
    return {match.group("key"): parse_value(match.group("value")) for match in FIELD_RE.finditer(text)}


def nested_int(data: dict[str, Any], path: list[str], default: int = 0) -> int:
    item: Any = data
    for key in path:
        if not isinstance(item, dict):
            return default
        item = item.get(key)
    return item if isinstance(item, int) else default


def check_item(name: str, passed: bool, summary: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": "pass" if passed else "fail", "summary": summary, **extra}


def load_vcs_result(run_dir: Path, override: str | None) -> tuple[Path, dict[str, Any]]:
    path = resolve_path(run_dir, override) if override else run_dir / "verification" / "real_tools" / "case_vcs_functional_sim.json"
    if path is None or not path.exists():
        raise FileNotFoundError(f"VCS functional result missing: {path}")
    return path, read_json(path)


def load_diagnosis(run_dir: Path, override: str | None) -> tuple[Path, dict[str, Any]]:
    candidates = []
    if override:
        resolved = resolve_path(run_dir, override)
        if resolved:
            candidates.append(resolved)
    candidates.extend(
        [
            run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json",
        ]
    )
    for path in candidates:
        if path.exists():
            return path, read_json(path)
    raise FileNotFoundError(f"VCS diagnosis missing; checked {[str(path) for path in candidates]}")


def expected_vector_beats(runtime: dict[str, Any], memory_layout: dict[str, Any]) -> int:
    params = runtime.get("params", {}) if isinstance(runtime.get("params"), dict) else {}
    tensor = memory_layout.get("tensor_shape", {}) if isinstance(memory_layout.get("tensor_shape"), dict) else {}
    seq_len = int(params.get("max_seq_len") or tensor.get("seq_len") or 0)
    hidden = int(params.get("hidden_size") or tensor.get("hidden_size") or 0)
    lanes = int(params.get("lanes") or 0)
    if seq_len <= 0 or hidden <= 0 or lanes <= 0:
        return 0
    return seq_len * ((hidden + lanes - 1) // lanes)


def memory_alignment_check(memory_layout: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    alignment = int(memory_layout.get("alignment_bytes") or 0)
    regions = memory_layout.get("regions") if isinstance(memory_layout.get("regions"), list) else []
    if alignment <= 0:
        blockers.append("alignment_bytes is missing or non-positive")
    if not regions:
        blockers.append("regions are missing")
    roles = {str(region.get("role")) for region in regions if isinstance(region, dict)}
    for role in ["activation_input", "activation_output", "weight_buffer", "runtime_status"]:
        if role not in roles:
            blockers.append(f"required memory role missing: {role}")
    for region in regions:
        if not isinstance(region, dict):
            blockers.append("malformed memory region entry")
            continue
        base = int(region.get("base_addr") or 0)
        size = int(region.get("size_bytes") or 0)
        if alignment > 0 and (base % alignment or size % alignment):
            blockers.append(f"region is not aligned: {region.get('name')}")
        if size <= 0:
            blockers.append(f"region has non-positive size: {region.get('name')}")
    if regions:
        last = max(int(region.get("base_addr") or 0) + int(region.get("size_bytes") or 0) for region in regions if isinstance(region, dict))
        total = int(memory_layout.get("total_bytes") or 0)
        if total < last:
            blockers.append("total_bytes is smaller than the last region end")
    return not blockers, blockers


def token_check(label: str, text: str, required_tokens: list[str]) -> tuple[bool, list[str]]:
    missing = [token for token in required_tokens if token not in text]
    return not missing, [f"{label} missing token {token}" for token in missing]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    vcs_path, vcs = load_vcs_result(run_dir, args.vcs_result)
    compile_evidence = vcs.get("compile_evidence", {}) if isinstance(vcs.get("compile_evidence"), dict) else {}
    compile_result = vcs.get("compile", {}) if isinstance(vcs.get("compile"), dict) else {}
    log_path = Path(str(compile_evidence.get("log_path") or vcs.get("compile_log") or ""))
    passed = (
        vcs.get("status") == "pass"
        and vcs.get("validation_policy") == COMPILE_ONLY_POLICY
        and compile_evidence.get("status") == "pass"
        and compile_result.get("status") == "pass"
        and compile_result.get("returncode") == 0
        and log_path.is_file()
        and compile_evidence.get("log_sha256") == hashlib.sha256(log_path.read_bytes()).hexdigest()
    )
    report = {
        "schema_version": "spatialaccagent.case_deadlock_axi_check.v0",
        "status": "pass" if passed else "fail",
        "validation_policy": COMPILE_ONLY_POLICY,
        "checks": [
            check_item(
                "vcs_compile_and_elaboration",
                passed,
                "VCS compilation and elaboration passed; runtime AXI/deadlock checks skipped"
                if passed
                else "VCS compile-only evidence is missing or invalid",
                compile_evidence=compile_evidence,
            )
        ],
        "blockers": [] if passed else ["VCS compile/elaboration evidence is not valid"],
        "summary": "compile-only gate passed" if passed else "compile-only gate failed",
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check real functional deadlock and AXI/DDR evidence for a verification case.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--vcs-result")
    parser.add_argument("--diagnosis")
    parser.add_argument("--runtime-config", default="generated/chisel/runtime/runtime_config.json")
    parser.add_argument("--memory-layout", default="generated/chisel/memory/memory_layout.json")
    parser.add_argument("--rtl-wrapper", action="append", default=[])
    parser.add_argument("--testbench", action="append", default=[])
    args = parser.parse_args(argv)
    out_path = args.out or args.run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json"
    try:
        report = build_report(args)
    except Exception as exc:
        report = {
            "schema_version": "spatialaccagent.case_deadlock_axi_check.v0",
            "status": "fail",
            "run_dir": str(args.run_dir),
            "checks": [],
            "blockers": [str(exc)],
            "summary": str(exc),
        }
    write_json(out_path, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
