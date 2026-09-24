#!/usr/bin/env python3
"""Check Qwen hierarchical verification evidence gates.

This checker is intentionally conservative. It records the evidence that is
already present in a run directory and fails when a required real-design
artifact is absent. It does not generate replacement artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.board_acceptance_contract import validate_exact_board_preflight
from accagent.framework.active_board_job import pending_exact_board_job
from accagent.framework.board_validation_scope import (
    BoardValidationScopeError,
    resolve_board_validation_scope,
    validation_scope_record_errors,
)
from accagent.framework.stage_verification_plan import leaf_module_checks


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def json_text(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True).lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_id(value: Any, default: str = "unknown") -> str:
    text = str(value or default).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or default


def pipeline_plan_path(run_dir: Path) -> Path:
    return run_dir / "pipeline_planning" / "pipeline_plan.json"


def model_config_path(run_dir: Path) -> Path:
    return run_dir / "input" / "model_config.json"


def task_card_path(run_dir: Path) -> Path:
    return run_dir / "input" / "task_card.json"


def generated_chisel_dir(run_dir: Path) -> Path:
    return run_dir / "generated" / "chisel"


def sv_paths(run_dir: Path) -> list[Path]:
    return sorted(generated_chisel_dir(run_dir).glob("*.sv"))


def module_available(module: str, paths: list[Path], text_index: str) -> bool:
    if ":" in module and "." in module:
        parent_role, module_base = module.split(":", 1)
        parent, role = parent_role.split(".", 1)
        parent_text = ""
        for path in paths:
            if path.stem == parent:
                parent_text = read_text(path)
                break
        if not parent_text:
            match = re.search(rf"\bmodule\s+{re.escape(parent)}\b(?P<body>.*?)\bendmodule\b", text_index, re.S)
            parent_text = match.group("body") if match else ""
        role_pattern = r"\w+" if role == "*" else re.escape(role)
        return re.search(rf"\b{re.escape(module_base)}(?:_\d+)?\s+{role_pattern}\s*\(", parent_text) is not None
    if any(path.stem == module for path in paths):
        return True
    return re.search(rf"\bmodule\s+{re.escape(module)}\b", text_index) is not None


def result(gate: str, checks: list[dict[str, Any]], blockers: list[str], run_dir: Path) -> dict[str, Any]:
    failed_checks = [
        str(check.get("name") or "unnamed_check")
        for check in checks
        if isinstance(check, dict) and check.get("status") == "fail"
    ]
    effective_blockers = list(blockers)
    if failed_checks:
        effective_blockers.append(
            "failed checks: " + ", ".join(dict.fromkeys(failed_checks))
        )
    return {
        "schema_version": "spatialaccagent.qwen_hierarchical_check.v0",
        "gate": gate,
        "status": "pass" if not effective_blockers else "fail",
        "run_dir": str(run_dir),
        "checks": checks,
        "blockers": effective_blockers,
    }


def check_stage_leaf_static(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    plan_path = pipeline_plan_path(run_dir)
    paths = sv_paths(run_dir)
    top_path = generated_chisel_dir(run_dir) / "GeneratedAcceleratorTop.sv"
    fpga_top_path = generated_chisel_dir(run_dir) / "GeneratedAxiDdrTop.sv"
    block_path = generated_chisel_dir(run_dir) / "LlamaStyleBlock.sv"
    if not plan_path.exists():
        blockers.append(f"pipeline plan missing: {plan_path}")
        return result("stage_leaf_static", checks, blockers, run_dir)
    plan = read_json(plan_path)
    model_path = model_config_path(run_dir)
    model_config = read_json(model_path) if model_path.exists() else {}
    stages = plan.get("stages", [])
    edges = plan.get("stream_edges", [])
    data_edges = plan.get("data_edges", [])
    checks.append({"name": "pipeline_plan_exists", "status": "pass", "path": str(plan_path), "stages": len(stages)})
    if not stages:
        blockers.append("pipeline plan has no stages")
    stream_ids = [edge.get("edge_id") for edge in edges]
    data_ids = [edge.get("edge_id") for edge in data_edges]
    if data_ids != stream_ids:
        blockers.append("stream_edges must mirror data_edges including boundary, skip, branch, and join edges")
    endpoints = {(edge.get("src_stage"), edge.get("dst_stage")) for edge in edges}
    stage_ids = {stage.get("stage_id") for stage in stages}
    missing_inputs = sorted(str(stage_id) for stage_id in stage_ids if stage_id and not any(dst == stage_id for _, dst in endpoints))
    missing_outputs = sorted(str(stage_id) for stage_id in stage_ids if stage_id and not any(src == stage_id for src, _ in endpoints))
    edge_contract_errors = [
        edge.get("edge_id")
        for edge in edges
        if edge.get("flow_control") != "ready_valid" or not isinstance(edge.get("stream_contract"), dict)
    ]
    if not any(src == "block_input" for src, _ in endpoints):
        blockers.append("stream graph has no block_input boundary edge")
    if not any(dst == "block_output" for _, dst in endpoints):
        blockers.append("stream graph has no block_output boundary edge")
    if missing_inputs:
        blockers.append(f"pipeline stages missing stream input edges: {missing_inputs}")
    if missing_outputs:
        blockers.append(f"pipeline stages missing stream output edges: {missing_outputs}")
    if edge_contract_errors:
        blockers.append(f"stream edges missing ready_valid stream contracts: {edge_contract_errors}")
    checks.append(
        {
            "name": "pipeline_stream_graph_contract",
            "status": "pass" if not (missing_inputs or missing_outputs or edge_contract_errors) else "fail",
            "stream_edges": len(edges),
            "data_edges": len(data_edges),
            "has_block_input": any(src == "block_input" for src, _ in endpoints),
            "has_block_output": any(dst == "block_output" for _, dst in endpoints),
            "missing_inputs": missing_inputs,
            "missing_outputs": missing_outputs,
            "edge_contract_errors": edge_contract_errors,
        }
    )

    for path in [top_path, fpga_top_path, block_path]:
        if path.exists():
            checks.append({"name": "rtl_file_exists", "status": "pass", "path": str(path)})
        else:
            checks.append({"name": "rtl_file_exists", "status": "fail", "path": str(path)})
            blockers.append(f"required RTL file missing: {path}")

    top_text = read_text(top_path)
    for signal in ["io_in_valid", "io_in_ready", "io_out_valid", "io_out_ready"]:
        status = "pass" if signal in top_text else "fail"
        checks.append({"name": "top_stream_signal", "signal": signal, "status": status})
        if status != "pass":
            blockers.append(f"GeneratedAcceleratorTop missing stream signal {signal}")

    text_index = "\n".join(path.name + "\n" + read_text(path) for path in paths)
    focus_stage_id = os.environ.get("SPATIALACC_PIPELINE_STAGE_ID", "").strip()
    stages_to_check = [
        stage
        for stage in stages
        if not focus_stage_id or str(stage.get("stage_id")) == focus_stage_id
    ]
    if focus_stage_id and not stages_to_check:
        blockers.append(f"requested leaf stage not found in pipeline plan: {focus_stage_id}")
    for stage in stages_to_check:
        required_modules = leaf_module_checks(stage, model_config)
        missing = [
            name
            for name in required_modules
            if not module_available(name, paths, text_index)
        ]
        status = "pass" if not missing else "fail"
        checks.append(
            {
                "name": "stage_leaf_modules",
                "stage_id": stage.get("stage_id"),
                "op": stage.get("op"),
                "kind": stage.get("kind"),
                "required_modules": required_modules,
                "missing_modules": missing,
                "status": status,
            }
        )
        if missing:
            blockers.append(f"{stage.get('stage_id')} missing leaf modules {missing}")
    return result("stage_leaf_static", checks, blockers, run_dir)


def manifest_candidates(run_dir: Path) -> list[Path]:
    candidates = []
    env_manifest = os.environ.get("QWEN_REAL_WEIGHT_MANIFEST")
    if env_manifest:
        candidates.append(Path(env_manifest))
    candidates.extend(
        [
            run_dir / "verification" / "model_weights" / "weight_manifest.json",
            run_dir / "verification" / "qwen_real_weights" / "weight_manifest.json",
            run_dir / "generated" / "memory" / "qwen_real_weight_manifest.json",
            run_dir / "generated" / "memory" / "resolved_manifest.json",
            REPO_ROOT / "verification" / "cases" / "qwen2_stage_full" / "resolved_manifest.json",
            REPO_ROOT / "verification" / "cases" / "qwen2_real_weights" / "resolved_manifest.json",
        ]
    )
    return candidates


def check_real_weights(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    evidence_dir = run_dir / "verification" / "model_weights"
    manifest_path = evidence_dir / "weight_manifest.json"
    catalog_path = evidence_dir / "full_tensor_catalog.json"
    accelerator_catalog_path = evidence_dir / "transformer_block_weight_catalog.json"
    hashes_path = evidence_dir / "artifact_hashes.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    catalog = read_json(catalog_path) if catalog_path.exists() else {}
    accelerator_catalog = read_json(accelerator_catalog_path) if accelerator_catalog_path.exists() else {}
    hashes = read_json(hashes_path) if hashes_path.exists() else {}
    manifest_ok = (
        manifest.get("status") == "pass"
        and manifest.get("validation", {}).get("complete_checkpoint_tensor_catalog") is True
        and manifest.get("weights", {}).get("offsets_valid") is True
    )
    checks.append(
        {
            "name": "complete_real_weight_manifest",
            "path": str(manifest_path),
            "status": "pass" if manifest_ok else "fail",
            "tensor_count": manifest.get("weights", {}).get("tensor_count"),
            "layer_ids": manifest.get("weights", {}).get("layer_ids", []),
        }
    )
    if not manifest_ok:
        blockers.append("complete target-checkpoint weight manifest is missing or invalid")
    catalog_ok = (
        catalog.get("status") == "pass"
        and catalog.get("scope_coverage_complete") is True
        and catalog.get("tensor_count") == len(catalog.get("tensors", []))
        and bool(catalog.get("source_checkpoint_sha256"))
    )
    checks.append(
        {
            "name": "complete_checkpoint_tensor_catalog",
            "path": str(catalog_path),
            "status": "pass" if catalog_ok else "fail",
            "tensor_count": catalog.get("tensor_count"),
            "source_checkpoint_sha256": catalog.get("source_checkpoint_sha256"),
        }
    )
    if not catalog_ok:
        blockers.append("full checkpoint tensor catalog/hash evidence is missing or incomplete")
    accelerator_tensors = [row for row in accelerator_catalog.get("tensors", []) if isinstance(row, dict)]
    accelerator_catalog_ok = (
        accelerator_catalog.get("status") == "pass"
        and accelerator_catalog.get("accelerator_scope") == "transformer_blocks_only"
        and accelerator_catalog.get("scope_coverage_complete") is True
        and accelerator_catalog.get("tensor_count") == len(accelerator_tensors)
        and bool(accelerator_tensors)
        and all(row.get("source_slice_sha256") for row in accelerator_tensors)
        and accelerator_catalog.get("source_checkpoint_sha256") == catalog.get("source_checkpoint_sha256")
    )
    checks.append(
        {
            "name": "complete_transformer_block_weight_catalog",
            "path": str(accelerator_catalog_path),
            "status": "pass" if accelerator_catalog_ok else "fail",
            "accelerator_scope": accelerator_catalog.get("accelerator_scope"),
            "tensor_count": accelerator_catalog.get("tensor_count"),
            "target_layer_count": accelerator_catalog.get("target_layer_count"),
            "excluded_non_accelerator_tensors": accelerator_catalog.get("excluded_non_accelerator_tensors", []),
        }
    )
    if not accelerator_catalog_ok:
        blockers.append("complete transformer-block-only weight catalog/hash evidence is missing or incomplete")
    hash_roles = {
        str(item.get("role"))
        for item in hashes.get("artifacts", [])
        if isinstance(item, dict) and item.get("sha256")
    }
    hashes_ok = {
        "weight_manifest",
        "complete_checkpoint_tensor_catalog",
        "transformer_block_weight_catalog",
    }.issubset(hash_roles) and bool({"target_model_checkpoint", "hf_safetensors_weights"} & hash_roles)
    checks.append(
        {
            "name": "real_weight_artifact_hashes",
            "path": str(hashes_path),
            "status": "pass" if hashes_ok else "fail",
            "roles": sorted(hash_roles),
        }
    )
    if not hashes_ok:
        blockers.append("checkpoint/manifest/catalog artifact hashes are incomplete")
    diagnostic_path = evidence_dir / "packed_weight_manifest.json"
    if diagnostic_path.exists():
        diagnostic = read_json(diagnostic_path)
        checks.append(
            {
                "name": "sampled_weight_path_diagnostic",
                "path": str(diagnostic_path),
                "status": "not_acceptance_evidence",
                "manifest_status": diagnostic.get("status"),
                "scope_coverage_complete": diagnostic.get("scope_coverage_complete"),
            }
        )
    return result("real_weights", checks, blockers, run_dir)


def check_multilayer_pipeline(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    model_path = model_config_path(run_dir)
    model = read_json(model_path) if model_path.exists() else {}
    task_path = task_card_path(run_dir)
    task_card = read_json(task_path) if task_path.exists() else {}
    num_layers = int(model.get("num_layers") or model.get("num_hidden_layers") or 0)
    binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    binding = read_json(binding_path) if binding_path.exists() else {}
    accelerator_catalog_path = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
    accelerator_catalog = read_json(accelerator_catalog_path) if accelerator_catalog_path.exists() else {}
    try:
        scope = resolve_board_validation_scope(task_card, model)
        scope_errors: list[str] = []
    except BoardValidationScopeError as exc:
        scope = None
        scope_errors = [str(exc)]
    required_hashes = {
        str(row.get("source_slice_sha256"))
        for row in accelerator_catalog.get("tensors", [])
        if (
            isinstance(row, dict)
            and row.get("source_slice_sha256")
            and scope is not None
            and row.get("layer_index") in scope.layer_indices
        )
    }
    bound_hashes = {
        str(value)
        for value in binding.get("board_consumed_tensor_hashes", binding.get("consumed_tensor_hashes", []))
        if str(value)
    }
    harness = binding.get("multilayer_harness", {}) if isinstance(binding.get("multilayer_harness"), dict) else {}
    binding_errors = (
        validation_scope_record_errors(
            scope,
            binding,
            allowed_statuses={"pass"},
            require_accelerator_scope=True,
        )
        if scope is not None
        else ["board validation scope is unavailable"]
    )
    checks.append({"name": "model_config_num_layers", "path": str(model_path), "num_layers": num_layers, "status": "pass" if num_layers > 0 else "fail"})
    checks.append(
        {
            "name": "board_validation_scope",
            "path": str(task_path),
            "status": "pass" if scope is not None else "fail",
            "model_layer_count": scope.model_layer_count if scope is not None else None,
            "validation_layer_indices": list(scope.layer_indices) if scope is not None else [],
            "validation_layer_count": scope.validation_layer_count if scope is not None else 0,
            "scope_errors": scope_errors,
        }
    )
    checks.append(
        {
            "name": "multilayer_real_weight_binding",
            "path": str(binding_path),
            "status": "pass" if not binding_errors and required_hashes == bound_hashes else "fail",
            "all_target_layers": binding.get("all_target_layers"),
            "validation_layer_indices": binding.get("validation_layer_indices"),
            "bound_layer_count": binding.get("bound_layer_count"),
            "accelerator_scope": binding.get("accelerator_scope"),
            "required_tensor_count": len(required_hashes),
            "bound_tensor_count": len(bound_hashes),
            "scope_errors": binding_errors,
        }
    )
    source_errors = []
    for row in harness.get("source_files", []):
        if not isinstance(row, dict):
            source_errors.append("invalid source row")
            continue
        path = Path(str(row.get("path") or ""))
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            source_errors.append(str(path))
    checks.append({"name": "multilayer_harness_sources", "status": "pass" if harness and not source_errors else "fail", "errors": source_errors})
    if num_layers <= 0:
        blockers.append("target model layer count is missing")
    if scope_errors:
        blockers.append("board validation scope is invalid: " + "; ".join(scope_errors))
    if (
        binding_errors
        or accelerator_catalog.get("scope_coverage_complete") is not True
        or not required_hashes
        or required_hashes != bound_hashes
    ):
        blockers.append("DUT binding does not cover every Transformer-block weight in the current board validation range")
    if not harness or source_errors:
        blockers.append("hash-verified multi-layer pipeline harness is missing")
    return result("multilayer_pipeline", checks, blockers, run_dir)


def check_axi_ddr_interface(run_dir: Path) -> dict[str, Any]:
    pending_job = pending_exact_board_job(run_dir)
    if pending_job is not None:
        job = pending_job["job"]
        report = result(
            "axi_ddr_interface",
            [
                {
                    "name": "pending_exact_board_job_contract",
                    "status": "pass",
                    "input_fingerprint_sha256": job["input_fingerprint_sha256"],
                    "source_identity_sha256": job["source_identity_sha256"],
                    "source_closure_sha256": job["source_closure_sha256"],
                    "compile_source_set_sha256": job["compile_source_set_sha256"],
                }
            ],
            [],
            run_dir,
        )
        report["status_detail"] = (
            "preflight is sealed by the pending exact VCS job; final board acceptance "
            "remains dependent on its collected real-tool result"
        )
        report["source_closure_sha256"] = job["source_closure_sha256"]
        report["compile_source_set_sha256"] = job["compile_source_set_sha256"]
        return report
    identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
    simulation_path = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
    acceptance = validate_exact_board_preflight(identity_path, simulation_path)
    report = result(
        "axi_ddr_interface",
        list(acceptance.get("checks", [])),
        list(acceptance.get("blockers", [])),
        run_dir,
    )
    report["acceptance_contract_schema_version"] = acceptance.get("schema_version")
    report["source_closure_sha256"] = acceptance.get("source_closure_sha256")
    report["compile_source_set_sha256"] = acceptance.get("compile_source_set_sha256")
    return report


def check_tb_scaffold(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    manifest_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    contracts = [row for row in manifest.get("stage_contracts", []) if isinstance(row, dict)]
    stage_ready = bool(contracts) and all(
        row.get("status") == "ready"
        and Path(str(row.get("testbench") or "")).is_file()
        and sha256_file(Path(str(row.get("testbench")))) == row.get("testbench_sha256")
        for row in contracts
    )
    single = manifest.get("single_layer", {}) if isinstance(manifest.get("single_layer"), dict) else {}
    single_tb = Path(str(single.get("testbench") or ""))
    single_ready = (
        single.get("real_weight_binding_verified") is True
        and single_tb.is_file()
        and sha256_file(single_tb) == single.get("testbench_sha256")
    )
    checks.append({"name": "operator_semantic_testbenches", "path": str(manifest_path), "count": len(contracts), "status": "pass" if stage_ready else "fail"})
    checks.append({"name": "single_layer_semantic_testbench", "path": str(single_tb), "status": "pass" if single_ready else "fail"})
    if manifest.get("status") != "ready" or not stage_ready:
        blockers.append("not every operator has a hash-verified real-weight semantic testbench")
    if not single_ready:
        blockers.append("connected single-layer real-weight semantic testbench is not ready")
    return result("tb_scaffold", checks, blockers, run_dir)


def check_single_layer_kernel(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    prerequisite_reports = [
        hierarchy_dir / "stage_leaf_static.json",
        hierarchy_dir / "tb_scaffold.json",
        hierarchy_dir / "real_weights.json",
    ]
    for path in prerequisite_reports:
        exists = path.exists()
        status = "missing"
        if exists:
            try:
                status = read_json(path).get("status", "unknown")
            except Exception as exc:
                status = f"unreadable:{exc}"
        checks.append({"name": "single_layer_prerequisite_report", "path": str(path), "exists": exists, "report_status": status, "status": "pass" if status == "pass" else "fail"})
        if status != "pass":
            blockers.append(f"single-layer prerequisite report is not pass: {path} status={status}")

    binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    binding = read_json(binding_path) if binding_path.exists() else {}
    harness = binding.get("single_layer_harness", {}) if isinstance(binding.get("single_layer_harness"), dict) else {}
    interface = harness.get("interface", {}) if isinstance(harness.get("interface"), dict) else {}
    sources_ok = True
    source_rows = []
    for row in harness.get("source_files", []):
        if not isinstance(row, dict):
            sources_ok = False
            continue
        path = Path(str(row.get("path") or ""))
        ok = path.is_file() and sha256_file(path) == row.get("sha256")
        sources_ok = sources_ok and ok
        source_rows.append({"path": str(path), "status": "pass" if ok else "fail"})
    interface_ok = (
        bool(interface.get("clock_port"))
        and bool(interface.get("reset_port"))
        and isinstance(interface.get("inputs"), list)
        and len(interface.get("inputs", [])) == 1
        and isinstance(interface.get("output"), dict)
        and isinstance(interface.get("weight_loader"), dict)
    )
    checks.append({"name": "single_layer_harness_sources", "top_module": harness.get("top_module"), "sources": source_rows, "status": "pass" if harness and sources_ok else "fail"})
    checks.append({"name": "single_layer_harness_interface", "status": "pass" if interface_ok else "fail"})
    if not harness or not sources_ok:
        blockers.append("connected single-layer kernel has no hash-verified generated source harness")
    if not interface_ok:
        blockers.append("single-layer harness does not expose the standard stream and real-weight loader interface")
    return result("single_layer_kernel", checks, blockers, run_dir)


def report_status(path: Path) -> tuple[str, dict[str, Any]]:
    if not path.exists():
        return "missing", {}
    try:
        report = read_json(path)
    except Exception as exc:
        return f"unreadable:{exc}", {}
    return str(report.get("status") or "unknown"), report


def pass_candidate_check(name: str, candidates: list[Path]) -> tuple[dict[str, Any], bool]:
    rows = []
    passed = False
    for path in candidates:
        status, report = report_status(path)
        ok = status == "pass"
        passed = passed or ok
        rows.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "report_status": status,
                "summary": report.get("summary") if report else None,
                "status": "pass" if ok else "fail",
            }
        )
    return {"name": name, "status": "pass" if passed else "fail", "candidates": rows}, passed


def pipeline_stages(run_dir: Path) -> list[dict[str, Any]]:
    path = pipeline_plan_path(run_dir)
    if not path.exists():
        return []
    try:
        plan = read_json(path)
    except Exception:
        return []
    return [stage for stage in plan.get("stages", []) if isinstance(stage, dict)]


def stage_ids_for_leaf_gate(run_dir: Path) -> list[str]:
    focus_stage_id = os.environ.get("SPATIALACC_PIPELINE_STAGE_ID", "").strip()
    stages = pipeline_stages(run_dir)
    if focus_stage_id:
        return [focus_stage_id] if any(str(stage.get("stage_id")) == focus_stage_id for stage in stages) else []
    return [str(stage.get("stage_id")) for stage in stages if stage.get("stage_id")]


def leaf_evidence_candidates(run_dir: Path, gate: str, stage_id: str) -> list[Path]:
    safe_stage = safe_id(stage_id)
    if gate == "leaf_functional":
        return [
            run_dir / "verification" / "operator_leaf_functional" / f"{safe_stage}.json",
            run_dir / "verification" / "operator_leaf_functional" / f"{safe_stage}_report.json",
            run_dir / "verification" / "leaf_functional" / f"{safe_stage}.json",
            run_dir / "verification" / "leaf_stage" / f"{safe_stage}_functional.json",
            run_dir / "verification" / "leaf_stage" / f"{safe_stage}__leaf_functional.json",
        ]
    return [
        run_dir / "verification" / "operator_leaf_golden" / f"{safe_stage}.json",
        run_dir / "verification" / "operator_leaf_golden" / f"{safe_stage}_report.json",
        run_dir / "verification" / "leaf_golden" / f"{safe_stage}.json",
        run_dir / "verification" / "leaf_stage" / f"{safe_stage}_golden_compare.json",
        run_dir / "verification" / "leaf_stage" / f"{safe_stage}__leaf_golden_compare.json",
    ]


def check_boundary_contract(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    debug_dir = run_dir / "verification" / "debug_closure"
    contracts_path = debug_dir / "boundary_contracts.json"
    manifest_path = debug_dir / "trace_manifest.json"
    status, contracts = report_status(contracts_path)
    boundary_count = len(contracts.get("boundaries", [])) if isinstance(contracts.get("boundaries"), list) else 0
    checks.append(
        {
            "name": "boundary_contracts",
            "path": str(contracts_path),
            "report_status": status,
            "boundary_count": boundary_count,
            "status": "pass" if boundary_count > 0 else "fail",
        }
    )
    manifest_status, manifest = report_status(manifest_path)
    required_fields = manifest.get("required_record_fields", []) if isinstance(manifest.get("required_record_fields"), list) else []
    missing_fields = [
        field
        for field in ["cycle", "boundary_id", "tx_id", "logical_index", "observed_value", "expected_value", "contract", "status"]
        if field not in required_fields
    ]
    checks.append(
        {
            "name": "trace_manifest",
            "path": str(manifest_path),
            "report_status": manifest_status,
            "missing_required_fields": missing_fields,
            "status": "pass" if manifest_status != "missing" and not missing_fields else "fail",
        }
    )
    if boundary_count <= 0:
        blockers.append("debug closure boundary contracts are missing or empty")
    if manifest_status == "missing" or missing_fields:
        blockers.append(f"boundary trace manifest missing required fields: {missing_fields}")
    return result("boundary_contract", checks, blockers, run_dir)


def check_leaf_evidence_gate(run_dir: Path, gate: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    stage_ids = stage_ids_for_leaf_gate(run_dir)
    focus_stage_id = os.environ.get("SPATIALACC_PIPELINE_STAGE_ID", "").strip()
    if focus_stage_id and not stage_ids:
        blockers.append(f"requested leaf stage not found in pipeline plan: {focus_stage_id}")
    if not stage_ids:
        blockers.append("pipeline plan has no leaf stage ids for functional verification")
    boundary_report = check_boundary_contract(run_dir)
    checks.append(
        {
            "name": "boundary_contract_prerequisite",
            "status": boundary_report.get("status"),
            "blockers": boundary_report.get("blockers", []),
        }
    )
    if boundary_report.get("status") != "pass":
        blockers.append("leaf functional/golden gate requires boundary contracts and trace manifest")
    for stage_id in stage_ids:
        static_candidates = [
            run_dir / "verification" / "leaf_stage" / f"{safe_id(stage_id)}.json",
            run_dir / "verification" / "qwen_hierarchy" / f"stage_leaf_static__{safe_id(stage_id)}.json",
            run_dir / "verification" / "qwen_hierarchy" / "stage_leaf_static.json",
        ]
        static_check, static_ok = pass_candidate_check(f"{stage_id}.static_prerequisite", static_candidates)
        checks.append(static_check)
        evidence_check, evidence_ok = pass_candidate_check(f"{stage_id}.{gate}", leaf_evidence_candidates(run_dir, gate, stage_id))
        checks.append(evidence_check)
        if not static_ok:
            blockers.append(f"{stage_id} has no passing stage_leaf_static prerequisite")
        if not evidence_ok:
            blockers.append(
                f"{stage_id} has no passing {gate} report; provide an operator-local functional sim/golden compare report instead of treating static RTL presence as correctness"
            )
    return result(gate, checks, blockers, run_dir)


def check_leaf_functional(run_dir: Path) -> dict[str, Any]:
    return check_leaf_evidence_gate(run_dir, "leaf_functional")


def check_leaf_golden_compare(run_dir: Path) -> dict[str, Any]:
    return check_leaf_evidence_gate(run_dir, "leaf_golden_compare")


def check_single_layer_functional(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    for name, candidates in [
        (
            "leaf_functional_prerequisite",
            [
                hierarchy_dir / "leaf_functional.json",
                run_dir / "verification" / "operator_leaf_functional" / "summary.json",
            ],
        ),
        (
            "single_layer_kernel_prerequisite",
            [
                hierarchy_dir / "single_layer_kernel.json",
                run_dir / "verification" / "single_layer" / "single_transformer_layer_report.json",
            ],
        ),
        (
            "single_layer_functional_report",
            [
                hierarchy_dir / "single_layer_functional.json",
                run_dir / "verification" / "single_layer" / "single_layer_functional_report.json",
            ],
        ),
    ]:
        check, ok = pass_candidate_check(name, candidates)
        checks.append(check)
        if not ok:
            blockers.append(f"{name} has no passing report")
    return result("single_layer_functional", checks, blockers, run_dir)


def check_single_layer_golden_compare(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    for name, candidates in [
        ("single_layer_functional_prerequisite", [hierarchy_dir / "single_layer_functional.json"]),
        (
            "single_layer_golden_compare_report",
            [
                hierarchy_dir / "single_layer_golden_compare.json",
                run_dir / "verification" / "single_layer" / "single_layer_golden_compare.json",
            ],
        ),
    ]:
        check, ok = pass_candidate_check(name, candidates)
        checks.append(check)
        if not ok:
            blockers.append(f"{name} has no passing report")
    return result("single_layer_golden_compare", checks, blockers, run_dir)


def check_multilayer_functional(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    for name, candidates in [
        ("single_layer_functional_prerequisite", [hierarchy_dir / "single_layer_functional.json"]),
        ("multilayer_pipeline_prerequisite", [hierarchy_dir / "multilayer_pipeline.json"]),
        (
            "real_board_wrapped_vcs_functional",
            [
                run_dir / "verification" / "real_tools" / "case_vcs_functional_sim.json",
            ],
        ),
        (
            "vcs_functional_diagnosis",
            [
                run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json",
            ],
        ),
        (
            "multilayer_progress_and_ddr_evidence",
            [
                run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json",
            ],
        ),
    ]:
        check, ok = pass_candidate_check(name, candidates)
        checks.append(check)
        if not ok:
            blockers.append(f"{name} has no passing report")
    return result("multilayer_functional", checks, blockers, run_dir)


def check_pipeline_deadlock(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    for name, candidates in [
        ("multilayer_functional_prerequisite", [hierarchy_dir / "multilayer_functional.json"]),
        (
            "pipeline_deadlock_report",
            [
                run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json",
            ],
        ),
    ]:
        check, ok = pass_candidate_check(name, candidates)
        checks.append(check)
        if not ok:
            blockers.append(f"{name} has no passing report")
    return result("pipeline_deadlock", checks, blockers, run_dir)


def check_axi_protocol(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    for name, candidates in [
        ("axi_ddr_interface_prerequisite", [hierarchy_dir / "axi_ddr_interface.json"]),
        (
            "axi_protocol_runtime_evidence",
            [
                run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json",
            ],
        ),
    ]:
        check, ok = pass_candidate_check(name, candidates)
        checks.append(check)
        if not ok:
            blockers.append(f"{name} has no passing report")
    return result("axi_protocol", checks, blockers, run_dir)


def check_ddr_image_roundtrip(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    hierarchy_dir = run_dir / "verification" / "qwen_hierarchy"
    board_manifest_path = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
    board_manifest = read_json(board_manifest_path) if board_manifest_path.exists() else {}
    for name in ("input", "weight_image", "expected_output"):
        row = board_manifest.get("artifacts", {}).get(name, {}) if isinstance(board_manifest.get("artifacts"), dict) else {}
        path = Path(str(row.get("path") or ""))
        ok = path.is_file() and bool(row.get("sha256")) and sha256_file(path) == row.get("sha256")
        if name == "weight_image":
            ok = ok and row.get("scope_coverage_complete") is True
        checks.append({"name": f"board_ddr_{name}", "path": str(path), "status": "pass" if ok else "fail"})
        if not ok:
            blockers.append(f"board DDR {name} artifact/hash/coverage is invalid: {path}")
    for name, candidates in [
        ("axi_protocol_prerequisite", [hierarchy_dir / "axi_protocol.json"]),
        (
            "ddr_image_runtime_evidence",
            [
                run_dir / "verification" / "case_diagnostics" / "deadlock_axi_check.json",
            ],
        ),
    ]:
        check, ok = pass_candidate_check(name, candidates)
        checks.append(check)
        if not ok:
            blockers.append(f"{name} has no passing report")
    return result("ddr_image_roundtrip", checks, blockers, run_dir)


def check_runtime_bitstream(run_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    script_candidates = [
        REPO_ROOT / "scripts" / "synthesis" / "run_qwen_runtime_bitstream_23.sh",
        REPO_ROOT / "scripts" / "synthesis" / "qwen_runtime_bitstream_23.tcl",
    ]
    found_script = False
    for path in script_candidates:
        exists = path.exists()
        found_script = found_script or exists
        checks.append({"name": "runtime_bitstream_script_candidate", "path": str(path), "exists": exists, "status": "pass" if exists else "not_found"})
    bit_candidates = [
        run_dir / "qwen_runtime_app_shell.bit",
        run_dir / "runtime_bitstream" / "qwen_runtime_app_shell.bit",
        run_dir / "vivado_qwen_runtime_bitstream" / "qwen_runtime_app_shell.bit",
    ]
    found_runtime_bit = False
    for path in bit_candidates:
        exists = path.exists()
        found_runtime_bit = found_runtime_bit or exists
        checks.append({"name": "runtime_bitstream_candidate", "path": str(path), "exists": exists, "status": "pass" if exists else "not_found"})
    standalone_bits = [path for path in [run_dir / "qwen_generated_core_50mhz_agent.bit"] if path.exists()]
    checks.append({"name": "standalone_core_bitstreams", "paths": [str(path) for path in standalone_bits], "status": "informational"})
    if not found_script:
        blockers.append("no Qwen runtime/app_shell bitstream synthesis script exists")
    if not found_runtime_bit:
        blockers.append("no Qwen runtime/app_shell bitstream artifact exists; standalone generated-core bitstream is insufficient")
    return result("runtime_bitstream", checks, blockers, run_dir)


GATE_CHECKS = {
    "stage_leaf_static": check_stage_leaf_static,
    "boundary_contract": check_boundary_contract,
    "leaf_functional": check_leaf_functional,
    "leaf_golden_compare": check_leaf_golden_compare,
    "real_weights": check_real_weights,
    "tb_scaffold": check_tb_scaffold,
    "single_layer_kernel": check_single_layer_kernel,
    "single_layer_functional": check_single_layer_functional,
    "single_layer_golden_compare": check_single_layer_golden_compare,
    "multilayer_pipeline": check_multilayer_pipeline,
    "multilayer_functional": check_multilayer_functional,
    "pipeline_deadlock": check_pipeline_deadlock,
    "axi_ddr_interface": check_axi_ddr_interface,
    "axi_protocol": check_axi_protocol,
    "ddr_image_roundtrip": check_ddr_image_roundtrip,
    "runtime_bitstream": check_runtime_bitstream,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Qwen hierarchical verification evidence gates")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--gate", choices=[*GATE_CHECKS.keys(), "all"], required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir.resolve()
    out_dir = run_dir / "verification" / "qwen_hierarchy"
    leaf_out_dir = run_dir / "verification" / "leaf_stage"
    gates = list(GATE_CHECKS) if args.gate == "all" else [args.gate]
    reports = []
    for gate in gates:
        report = GATE_CHECKS[gate](run_dir)
        focus_stage_id = os.environ.get("SPATIALACC_PIPELINE_STAGE_ID", "").strip()
        if gate in {"stage_leaf_static", "leaf_functional", "leaf_golden_compare"} and focus_stage_id:
            path = out_dir / f"{gate}__{safe_id(focus_stage_id)}.json"
            leaf_name = f"{safe_id(focus_stage_id)}.json" if gate == "stage_leaf_static" else f"{safe_id(focus_stage_id)}__{gate}.json"
            write_json(leaf_out_dir / leaf_name, report)
        else:
            path = out_dir / f"{gate}.json"
        write_json(path, report)
        print(path)
        reports.append(report)
    if args.gate == "all":
        summary = {
            "schema_version": "spatialaccagent.qwen_hierarchical_check_summary.v0",
            "status": "pass" if all(item["status"] == "pass" for item in reports) else "fail",
            "reports": [str(out_dir / f"{item['gate']}.json") for item in reports],
        }
        write_json(out_dir / "summary.json", summary)
        print(out_dir / "summary.json")
        return 0 if summary["status"] == "pass" else 1
    return 0 if reports[0]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
