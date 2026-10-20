#!/usr/bin/env python3
"""Assemble strict real-weight semantic evidence for one verification layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.verification_evidence_contract import (
    COMPILE_ONLY_POLICY,
    canonical_sha256,
    evidence_contract_for_level,
)


SCHEMA_VERSION = "spatialaccagent.semantic_evidence_report.v1"
LEVELS = {
    "operator_leaf_functional",
    "single_layer_functional",
    "multilayer_pipeline_functional",
    "axi_ddr_functional",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonempty_hash(value: Any) -> str:
    text = str(value or "").strip()
    return text if len(text) == 64 else ""


def binding_errors(binding: dict[str, Any], reference: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_checkpoint = str(reference.get("weights", {}).get("source_checkpoint_sha256") or "")
    if binding.get("status") != "pass":
        errors.append("DUT weight-binding manifest status is not pass")
    if binding.get("accelerator_scope") != "transformer_blocks_only":
        errors.append("DUT weight binding is not limited to the transformer-block accelerator scope")
    if binding.get("source_checkpoint_sha256") != expected_checkpoint:
        errors.append("DUT weight binding does not match the reference checkpoint hash")
    if binding.get("scope_coverage_complete") is not True:
        errors.append("DUT weight binding does not cover the complete verification scope")
    if binding.get("dut_consumes_bound_weights") is not True:
        errors.append("DUT real-weight consumption is not proven")
    if binding.get("default_or_identity_weight_fallback_disabled") is not True:
        errors.append("default/identity weight fallback is not explicitly disabled")
    hashes = binding.get("consumed_tensor_hashes", [])
    if not isinstance(hashes, list) or not hashes or any(not nonempty_hash(item) for item in hashes):
        errors.append("DUT consumed tensor hashes are missing or malformed")
    return errors


def comparison_errors(
    comparison: dict[str, Any],
    expected_sha256: str,
    required_weight_hashes: set[str],
) -> list[str]:
    errors: list[str] = []
    if comparison.get("status") != "pass" or comparison.get("passed") is not True:
        errors.append("semantic comparison status is not pass")
    if comparison.get("expected_output_sha256") != expected_sha256:
        errors.append("comparison expected-output hash does not match the generated target-model vector")
    if not nonempty_hash(comparison.get("rtl_output_sha256")):
        errors.append("RTL output hash is missing")
    if not nonempty_hash(comparison.get("testbench_sha256")):
        errors.append("executed semantic testbench hash is missing")
    consumed = {
        str(item)
        for item in comparison.get("consumed_tensor_hashes", [])
        if nonempty_hash(item)
    }
    if not required_weight_hashes.issubset(consumed):
        errors.append("comparison does not prove consumption of every required real-weight tensor")
    metrics = comparison.get("numeric_metrics", {})
    if not isinstance(metrics, dict) or metrics.get("passed") is not True:
        errors.append("numeric comparison metrics are missing or failed")
    if comparison.get("expected_output_source") != "target_model_inference":
        errors.append("comparison expected output is not bound to target-model inference")
    return errors


def operator_comparisons(
    run_dir: Path,
    testbench: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    contracts = testbench.get("stage_contracts", [])
    if not isinstance(contracts, list) or not contracts:
        return rows, ["semantic testbench has no operator-stage contracts"]
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        stage_id = str(contract.get("stage_id") or "")
        report_path = run_dir / "verification" / "operator_leaf_golden" / f"{stage_id.lower()}.json"
        report = read_json(report_path)
        comparison = report.get("semantic_comparison", {}) if isinstance(report.get("semantic_comparison"), dict) else {}
        expected = contract.get("expected_output", {}) if isinstance(contract.get("expected_output"), dict) else {}
        required_hashes = {
            str(item.get("sha256"))
            for item in contract.get("real_weight_bindings", [])
            if isinstance(item, dict) and nonempty_hash(item.get("sha256"))
        }
        row_errors = comparison_errors(comparison, str(expected.get("sha256") or ""), required_hashes)
        if contract.get("status") != "ready":
            row_errors.append("operator semantic testbench contract is not ready")
        if row_errors:
            errors.extend(f"{stage_id}: {message}" for message in row_errors)
        rows.append(
            {
                "stage_id": stage_id,
                "op": contract.get("op"),
                "status": "pass" if not row_errors else "fail",
                "report": str(report_path),
                "comparison": comparison,
                "required_weight_hashes": sorted(required_hashes),
                "errors": row_errors,
            }
        )
    return rows, errors


def single_layer_comparison(
    run_dir: Path,
    testbench: dict[str, Any],
    reference: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    section = testbench.get("single_layer", {}) if isinstance(testbench.get("single_layer"), dict) else {}
    expected = section.get("expected_output", {}) if isinstance(section.get("expected_output"), dict) else {}
    report_path = run_dir / "verification" / "single_layer" / "single_layer_golden_compare.json"
    report = read_json(report_path)
    comparison = report.get("semantic_comparison", {}) if isinstance(report.get("semantic_comparison"), dict) else {}
    required_hashes = {
        str(item.get("sha256"))
        for item in reference.get("weights", {}).get("layer_0_tensor_bindings", [])
        if isinstance(item, dict) and nonempty_hash(item.get("sha256"))
    }
    errors = comparison_errors(comparison, str(expected.get("sha256") or ""), required_hashes)
    if section.get("real_weight_binding_verified") is not True:
        errors.append("single-layer testbench does not have a verified real-weight binding")
    return [
        {
            "scope": "single_layer",
            "status": "pass" if not errors else "fail",
            "report": str(report_path),
            "comparison": comparison,
            "required_weight_hashes": sorted(required_hashes),
            "errors": errors,
        }
    ], errors


def board_comparison(
    run_dir: Path,
    testbench: dict[str, Any],
    binding: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    board_section = testbench.get("board", {}) if isinstance(testbench.get("board"), dict) else {}
    expected = board_section.get("expected_output", {}) if isinstance(board_section.get("expected_output"), dict) else {}
    diagnosis_path = run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
    diagnosis = read_json(diagnosis_path)
    comparison = diagnosis.get("semantic_comparison", {}) if isinstance(diagnosis.get("semantic_comparison"), dict) else {}
    required_hashes = {
        str(item)
        for item in binding.get("consumed_tensor_hashes", [])
        if nonempty_hash(item)
    }
    errors = comparison_errors(comparison, str(expected.get("sha256") or ""), required_hashes)
    identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    identity = read_json(identity_path)
    if identity.get("status") != "pass" or identity.get("exact_user_sample_wrapper") is not True:
        errors.append("exact user sample-project board wrapper identity is not proven")
    if identity.get("simulation_hashes_match_source") is not True:
        errors.append("simulated board-wrapper hashes do not match sample-project source hashes")
    return [
        {
            "scope": "board_axi_ddr",
            "status": "pass" if not errors else "fail",
            "report": str(diagnosis_path),
            "comparison": comparison,
            "required_weight_hashes": sorted(required_hashes),
            "errors": errors,
        }
    ], errors, identity


def assemble(run_dir: Path, level: str) -> dict[str, Any]:
    return assemble_compile_only(run_dir, level)


def assemble_compile_only(run_dir: Path, level: str) -> dict[str, Any]:
    logs: list[dict[str, Any]] = []
    errors: list[str] = []
    source_reports: list[str] = []

    def add_compile_evidence(report_path: Path) -> None:
        report = read_json(report_path)
        evidence = report.get("compile_evidence", {}) if isinstance(report.get("compile_evidence"), dict) else {}
        compile_result = evidence.get("compile", {}) if isinstance(evidence.get("compile"), dict) else {}
        log_path = Path(str(evidence.get("log_path") or ""))
        source_reports.append(str(report_path))
        if report.get("status") != "pass" or report.get("validation_policy") != COMPILE_ONLY_POLICY:
            errors.append(f"compile report is not a passing {COMPILE_ONLY_POLICY} result: {report_path}")
        if evidence.get("status") != "pass" or compile_result.get("status") != "pass" or compile_result.get("returncode") != 0:
            errors.append(f"VCS compile/elaboration did not pass: {report_path}")
        if not log_path.is_file():
            errors.append(f"VCS compile log is missing: {log_path}")
            return
        digest = sha256_file(log_path)
        if evidence.get("log_sha256") != digest:
            errors.append(f"VCS compile log hash mismatch: {log_path}")
        logs.append(
            {
                "path": str(log_path),
                "sha256": digest,
                "top_module": evidence.get("top_module"),
                "input_fingerprint_sha256": evidence.get("input_fingerprint_sha256"),
                "compile": compile_result,
            }
        )

    if level == "operator_leaf_functional":
        manifest = read_json(run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json")
        contracts = manifest.get("stage_contracts", [])
        if not isinstance(contracts, list) or not contracts:
            errors.append("operator semantic testbench has no compile targets")
        for contract in contracts:
            if not isinstance(contract, dict) or not contract.get("stage_id"):
                continue
            report_path = (
                run_dir
                / "verification"
                / "operator_leaf_functional"
                / f"{str(contract['stage_id']).lower()}.json"
            )
            if not report_path.is_file():
                errors.append(f"operator VCS compile report is missing: {report_path}")
                continue
            add_compile_evidence(report_path)
    elif level == "single_layer_functional":
        add_compile_evidence(
            run_dir
            / "verification"
            / "single_layer"
            / "single_layer_functional_report.json"
        )
    else:
        runner_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
        runner = read_json(runner_path)
        source_reports.append(str(runner_path))
        evidence = runner.get("compile_evidence", {}) if isinstance(runner.get("compile_evidence"), dict) else {}
        compile_result = runner.get("compile", {}) if isinstance(runner.get("compile"), dict) else {}
        log_path = Path(str(evidence.get("log_path") or runner.get("compile_log") or ""))
        if runner.get("status") != "pass" or runner.get("validation_policy") != COMPILE_ONLY_POLICY:
            errors.append("exact-board VCS report is not a passing compile-only result")
        if evidence.get("status") != "pass" or compile_result.get("status") != "pass" or compile_result.get("returncode") != 0:
            errors.append("exact-board VCS compile/elaboration did not pass")
        if not log_path.is_file():
            errors.append(f"exact-board VCS compile log is missing: {log_path}")
        else:
            digest = sha256_file(log_path)
            if evidence.get("log_sha256") != digest:
                errors.append("exact-board VCS compile log hash mismatch")
            logs.append(
                {
                    "path": str(log_path),
                    "sha256": digest,
                    "top_module": runner.get("top_module"),
                    "input_fingerprint_sha256": runner.get("input_fingerprint_sha256"),
                    "compile": compile_result,
                }
            )
        identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
        identity = read_json(identity_path)
        if identity.get("status") != "pass" or identity.get("exact_user_sample_wrapper") is not True:
            errors.append("exact sample-project board wrapper identity is not proven")
        if identity.get("simulation_hashes_match_source") is not True:
            errors.append("board compile sources do not match the sample-project source identity")

    covered_levels = (
        ["multilayer_pipeline_functional", "axi_ddr_functional"]
        if level in {"multilayer_pipeline_functional", "axi_ddr_functional"}
        else [level]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not errors and logs else "fail",
        "level_id": level,
        "covered_levels": covered_levels,
        "validation_policy": COMPILE_ONLY_POLICY,
        "evidence_contract": evidence_contract_for_level(level),
        "evidence_contracts": {
            covered_level: evidence_contract_for_level(covered_level)
            for covered_level in covered_levels
        },
        "compile_evidence": {
            "status": "pass" if not errors and logs else "fail",
            "compile": {
                "status": "pass" if not errors and logs else "fail",
                "returncode": 0 if not errors and logs else None,
            },
            "logs": logs,
            "source_reports": source_reports,
        },
        "functional_semantics_claimed": False,
        "errors": errors,
        "policy": {
            "simulation_executed": False,
            "output_and_weight_load_required": False,
            "vcs_compile_and_elaboration_required": True,
            "compile_failures_block_promotion": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble strict real-weight semantic verification evidence")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--level", choices=sorted(LEVELS), required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = assemble(args.run_dir.resolve(), args.level)
    write_json(args.out.resolve(), report)
    print(args.out.resolve())
    if report.get("status") != "pass":
        print("semantic_evidence_assembler.py: " + "; ".join(report.get("errors", [])[:10]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
