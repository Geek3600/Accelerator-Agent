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
    reference_path = run_dir / "verification" / "model_reference" / "reference_manifest.json"
    testbench_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    numeric_path = run_dir / "input" / "numeric_policy.json"
    reference = read_json(reference_path)
    testbench = read_json(testbench_path)
    binding = read_json(binding_path)
    errors: list[str] = []
    if reference.get("status") != "ready":
        errors.append("target-model reference manifest is not ready")
    if testbench.get("status") != "ready":
        errors.append("semantic testbench manifest is not ready")
    errors.extend(binding_errors(binding, reference))

    board_identity: dict[str, Any] = {}
    if level == "operator_leaf_functional":
        comparisons, compare_errors = operator_comparisons(run_dir, testbench)
    elif level == "single_layer_functional":
        comparisons, compare_errors = single_layer_comparison(run_dir, testbench, reference)
    else:
        comparisons, compare_errors, board_identity = board_comparison(run_dir, testbench, binding)
    errors.extend(compare_errors)

    comparison_hashes = [
        str(row.get("comparison", {}).get("rtl_output_sha256") or "")
        for row in comparisons
        if isinstance(row.get("comparison"), dict)
    ]
    expected_hashes = [
        str(row.get("comparison", {}).get("expected_output_sha256") or "")
        for row in comparisons
        if isinstance(row.get("comparison"), dict)
    ]
    consumed_hashes = sorted(
        {
            str(item)
            for row in comparisons
            for item in row.get("comparison", {}).get("consumed_tensor_hashes", [])
            if isinstance(row.get("comparison"), dict) and nonempty_hash(item)
        }
    )
    input_info = reference.get("input", {}) if isinstance(reference.get("input"), dict) else {}
    target = reference.get("target_model", {}) if isinstance(reference.get("target_model"), dict) else {}
    reference_info = reference.get("reference", {}) if isinstance(reference.get("reference"), dict) else {}
    testbench_hashes = [
        str(row.get("comparison", {}).get("testbench_sha256") or "")
        for row in comparisons
        if isinstance(row.get("comparison"), dict)
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not errors else "fail",
        "level_id": level,
        "evidence_contract": evidence_contract_for_level(level),
        "semantic_provenance": {
            "target_model": {
                "model_id": target.get("model_id"),
                "revision": target.get("revision"),
                "architecture": target.get("architecture"),
                "accelerator_scope": target.get("accelerator_scope"),
                "excluded_model_regions": target.get("excluded_model_regions", []),
            },
            "weights": {
                "real_target_weights": reference.get("weights", {}).get("real_target_weights") is True,
                "scope_coverage_complete": binding.get("scope_coverage_complete") is True,
                "consumed_by_dut": binding.get("dut_consumes_bound_weights") is True,
                "manifest": str(binding_path),
                "manifest_sha256": sha256_file(binding_path) if binding_path.exists() else None,
                "source_checkpoint_sha256": reference.get("weights", {}).get("source_checkpoint_sha256"),
                "consumed_tensor_hashes": consumed_hashes,
            },
            "input": {
                "source": input_info.get("source"),
                "seed": input_info.get("seed"),
                "dtype": input_info.get("dtype"),
                "shape": input_info.get("shape"),
                "sha256": input_info.get("tensor_sha256"),
            },
            "reference": {
                "engine": reference_info.get("engine"),
                "independent_of_rtl": reference_info.get("independent_of_rtl") is True,
                "uses_same_input_and_weights": reference_info.get("uses_same_input_and_weights") is True,
                "expected_output_source": reference_info.get("expected_output_source"),
                "oracle_kind": reference_info.get("oracle_kind"),
                "execution_dtype": reference_info.get("execution_dtype"),
                "expected_output_sha256": canonical_sha256(expected_hashes),
            },
            "numeric_policy": {
                "path": str(numeric_path),
                "policy_sha256": sha256_file(numeric_path) if numeric_path.exists() else None,
                "reference_bound": reference_info.get("numeric_policy_sha256") == (sha256_file(numeric_path) if numeric_path.exists() else None),
                "encoding_bound": testbench.get("numeric_policy_sha256") == (sha256_file(numeric_path) if numeric_path.exists() else None),
                "comparison_policy": testbench.get("numeric_comparison_policy", {}),
            },
            "testbench": {
                "manifest": str(testbench_path),
                "manifest_sha256": sha256_file(testbench_path) if testbench_path.exists() else None,
                "testbench_sha256": canonical_sha256(testbench_hashes),
                "loads_real_weights": testbench.get("dut_weight_binding_verified") is True,
            },
            "comparison": {
                "passed": not compare_errors,
                "rtl_output_sha256": canonical_sha256(comparison_hashes),
                "expected_output_sha256": canonical_sha256(expected_hashes),
                "records": comparisons,
            },
            "operator_coverage_complete": level != "operator_leaf_functional" or (
                bool(comparisons) and all(row.get("status") == "pass" for row in comparisons)
            ),
            "connected_single_layer": level != "single_layer_functional" or (
                bool(comparisons) and all(row.get("status") == "pass" for row in comparisons)
            ),
            "validation_scope": {
                "model_layer_count": binding.get("model_layer_count"),
                "validation_layer_indices": binding.get("validation_layer_indices"),
                "bound_layer_count": binding.get("bound_layer_count"),
                "all_target_layers": binding.get("all_target_layers"),
            },
            "all_validation_layers": level not in {"multilayer_pipeline_functional", "axi_ddr_functional"} or (
                binding.get("status") == "pass"
                and binding.get("scope_coverage_complete") is True
                and isinstance(binding.get("validation_layer_indices"), list)
                and binding.get("validation_layer_indices")
                == list(range(len(binding.get("validation_layer_indices"))))
                and int(binding.get("bound_layer_count") or 0)
                == len(binding.get("validation_layer_indices"))
                and bool(comparisons)
                and all(row.get("status") == "pass" for row in comparisons)
            ),
            "all_target_layers": level not in {"multilayer_pipeline_functional", "axi_ddr_functional"} or (
                binding.get("all_target_layers") is True
                and bool(comparisons)
                and all(row.get("status") == "pass" for row in comparisons)
            ),
            "board_wrapper": {
                "exact_user_sample_wrapper": board_identity.get("exact_user_sample_wrapper") is True,
                "simulation_hashes_match_source": board_identity.get("simulation_hashes_match_source") is True,
                "sample_project": board_identity.get("sample_project"),
                "top_module": board_identity.get("top_module"),
                "source_hashes": board_identity.get("source_hashes", []),
            },
        },
        "errors": errors,
        "policy": {
            "old_status_only_reports_are_rejected": True,
            "rtl_output_cannot_define_expected_output": True,
            "random_expected_output_is_forbidden": True,
            "default_or_sampled_weight_pass_is_forbidden": True,
        },
    }
    return report


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
