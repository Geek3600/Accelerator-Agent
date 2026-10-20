"""Trust contract for hierarchical real-weight verification evidence."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


EVIDENCE_CONTRACT_VERSION = "spatialaccagent.real_weight_semantic_evidence.v2"
TOOL_ENVIRONMENT_CONTRACT_VERSION = "spatialaccagent.tool_environment_identity.v1"
PROMOTION_CERTIFICATE_SCHEMA_VERSION = "spatialaccagent.stage7_promotion_certificate.v2"
PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION = "spatialaccagent.stage7_promotion_evidence_binding.v3"
COMPILE_ONLY_POLICY = "vcs_compile_only"






ROLE_CAPABILITY_REQUIREMENTS: dict[str, set[str]] = {
    "weight_manifest_generate": {
        "real_model_weights",
        "complete_scope_weight_manifest",
        "artifact_hash_manifest",
    },
    "target_model_reference_generate": {
        "real_model_weights_loaded",
        "deterministic_random_input",
        "target_model_inference",
        "operator_reference_capture",
        "independent_expected_output",
        "numeric_policy_binding",
        "explicit_reference_execution_contract",
    },
    "semantic_testbench_generate": {
        "semantic_testbench_generate",
        "reference_vector_encoding",
        "dut_weight_binding_validation",
        "default_weight_rejection",
        "artifact_hash_manifest",
    },
    "leaf_functional_sim": {
        "target_model_operator_semantics",
        "real_model_weights_consumed",
        "random_input_stimulus",
    },
    "leaf_golden_compare": {
        "target_model_operator_semantics",
        "real_model_weights_consumed",
        "independent_expected_output",
    },
    "single_layer_functional_sim": {
        "target_model_single_layer_semantics",
        "real_model_weights_consumed",
        "random_input_stimulus",
    },
    "single_layer_golden_compare": {
        "target_model_single_layer_semantics",
        "real_model_weights_consumed",
        "independent_expected_output",
    },
    "board_interface_discovery": {
        "exact_sample_board_wrapper_identity",
        "sample_project_source_hashes",
    },
    "vcs_functional_sim": {
        "all_target_layers",
        "real_model_weights_consumed",
        "complete_scope_weight_image",
        "random_input_stimulus",
        "exact_sample_board_wrapper_simulation",
    },
    "vcs_evidence_analyzer": {
        "semantic_comparison_evidence",
        "real_weight_provenance",
        "exact_sample_board_wrapper_identity",
        "boundary_trace",
    },
    "operator_leaf_semantic_evidence": {
        "semantic_comparison_evidence",
        "real_weight_provenance",
        "operator_coverage_evidence",
    },
    "single_layer_semantic_evidence": {
        "semantic_comparison_evidence",
        "real_weight_provenance",
        "connected_single_layer_evidence",
    },
    "board_semantic_evidence": {
        "semantic_comparison_evidence",
        "real_weight_provenance",
        "all_target_layers",
        "exact_sample_board_wrapper_identity",
    },
}


ROLE_PATH_REQUIREMENTS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "weight_manifest_generate": (("checkpoint", "safetensor"), ("weight", "hash", "catalog")),
    "target_model_reference_generate": (
        ("weight", "model", "numeric"),
        ("reference", "random", "golden", "operator"),
    ),
    "semantic_testbench_generate": (
        ("reference", "pipeline", "numeric", "binding"),
        ("testbench", "vector", "manifest", "requirement"),
    ),
    "leaf_functional_sim": (("weight", "input"), ("semantic", "report")),
    "leaf_golden_compare": (("weight", "input"), ("semantic", "golden", "report")),
    "single_layer_functional_sim": (("weight", "input"), ("semantic", "functional", "report")),
    "single_layer_golden_compare": (("weight", "input", "golden"), ("semantic", "golden", "report")),
    "board_interface_discovery": (("target_board", "sample_project"), ("identity", "hash", "board")),
    "vcs_functional_sim": (("weight", "input", "wrapper", "sample"), ("log", "trace", "output")),
    "vcs_evidence_analyzer": (("weight", "input", "log", "identity"), ("semantic", "trace", "report")),
    "operator_leaf_semantic_evidence": (
        ("reference", "binding", "leaf", "output"),
        ("semantic", "operator", "report"),
    ),
    "single_layer_semantic_evidence": (
        ("reference", "binding", "single", "output"),
        ("semantic", "single", "report"),
    ),
    "board_semantic_evidence": (
        ("reference", "binding", "board", "output", "identity"),
        ("semantic", "board", "report"),
    ),
}


ORACLE_PYTHON_ENVIRONMENT_ROLES = {
    "target_model_reference_generate",
    "semantic_testbench_generate",
    "leaf_functional_sim",
    "leaf_golden_compare",
    "single_layer_functional_sim",
    "single_layer_golden_compare",
    "vcs_evidence_analyzer",
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compile_log_errors(path: Path) -> list[str]:
    if not path.is_file():
        return [f"VCS compile log is missing: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    error_pattern = re.compile(
        r"(?im)^\s*(?:Error(?:-\[[^\]]+\])?\s*:|\*E,|Fatal\s*:)|\bsyntax error\b"
    )
    matches = [line.strip() for line in text.splitlines() if error_pattern.search(line)]
    return matches[:10]


def evidence_contract_for_level(level_id: str) -> dict[str, Any]:
    return {
        "version": EVIDENCE_CONTRACT_VERSION,
        "level_id": level_id,
        "validation_policy": COMPILE_ONLY_POLICY,
        "vcs_compile_and_elaboration_required": True,
        "simulation_execution_required": False,
        "functional_semantics_claimed": False,
    }


def certificate_contract_fingerprint(level_id: str, required_gates: list[str]) -> str:
    return canonical_sha256(
        {
            "evidence_contract": evidence_contract_for_level(level_id),
            "required_gates": sorted(str(gate) for gate in required_gates if str(gate)),
        }
    )


def selector_contract_matches_certificate(
    selector_contract: Any,
    certificate: dict[str, Any],
    level_id: str,
) -> bool:
    expected = evidence_contract_for_level(level_id)
    return selector_contract == expected or (
        certificate.get("validation_policy") == COMPILE_ONLY_POLICY
        and certificate.get("functional_semantics_claimed") is False
        and certificate.get("evidence_contract") == expected
    )


def tool_environment_contract(groups: dict[str, str]) -> dict[str, Any]:
    normalized = {str(name): str(fingerprint) for name, fingerprint in sorted(groups.items()) if name and fingerprint}
    identity = {"version": TOOL_ENVIRONMENT_CONTRACT_VERSION, "groups": normalized}
    return {
        **identity,
        "status": "pass",
        "fingerprint_sha256": canonical_sha256(identity),
    }


def promotion_evidence_binding_fingerprint(binding: dict[str, Any]) -> str:
    """Hash the exact live files and gate associations used by a certificate."""

    projection = {
        "schema_version": binding.get("schema_version"),
        "required_gates": sorted(str(value) for value in binding.get("required_gates", []) if str(value)),
        "file_bindings": [
            {
                "gate": str(row.get("gate") or ""),
                "path": str(row.get("path") or ""),
                "sha256": str(row.get("sha256") or "").lower(),
                "role": str(row.get("role") or ""),
                "source_path": str(row.get("source_path") or ""),
            }
            for row in binding.get("file_bindings", [])
            if isinstance(row, dict)
        ],
        "fingerprints": [
            {
                "name": str(row.get("name") or ""),
                "value": str(row.get("value") or "").lower(),
                "source": str(row.get("source") or ""),
                "kind": str(row.get("kind") or ""),
                "artifact_path": str(row.get("artifact_path") or ""),
            }
            for row in binding.get("fingerprints", [])
            if isinstance(row, dict)
        ],
        "excluded_same_scope_promotion_certificates": [
            {
                "artifact_id": str(row.get("artifact_id") or ""),
                "path": str(row.get("path") or ""),
                "declared_sha256": str(row.get("declared_sha256") or "").lower(),
                "current_sha256": str(row.get("current_sha256") or "").lower(),
                "role": str(row.get("role") or ""),
                "source": str(row.get("source") or ""),
                "reason": str(row.get("reason") or ""),
            }
            for row in binding.get("excluded_same_scope_promotion_certificates", [])
            if isinstance(row, dict)
        ],
    }
    return canonical_sha256(projection)


def promotion_evidence_binding_errors(
    payload: dict[str, Any],
    required_gates: list[str],
    *,
    verify_live_files: bool = True,
) -> list[str]:
    """Validate a certificate's evidence snapshot and reusable live identity.

    Gate logs and produced reports are immutable certificate snapshots.  RTL
    sources and semantic inputs remain live identity checks.  Derived input
    manifests are historical execution records: higher verification layers may
    regenerate them without invalidating a lower-layer hardware result.
    """

    errors: list[str] = []
    binding = payload.get("evidence_binding")
    if not isinstance(binding, dict):
        return ["promotion certificate is missing the live evidence binding"]
    if binding.get("schema_version") != PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION:
        errors.append("promotion certificate evidence binding schema is not current")
    expected_gates = sorted(str(gate) for gate in required_gates if str(gate))
    declared_gates = sorted(str(gate) for gate in binding.get("required_gates", []) if str(gate))
    if declared_gates != expected_gates:
        errors.append("promotion certificate evidence binding required gates do not match the selector")
    rows = [row for row in binding.get("file_bindings", []) if isinstance(row, dict)]
    if not rows:
        errors.append("promotion certificate evidence binding has no files")
    seen_paths: set[str] = set()
    bound_gates = {str(row.get("gate") or "") for row in rows if row.get("gate")}
    bound_paths = {
        str(value)
        for row in rows
        for value in (row.get("path"), row.get("source_path"))
        if str(value or "")
    }
    semantic_input_paths = {
        str(row.get("artifact_path") or "")
        for row in binding.get("fingerprints", [])
        if isinstance(row, dict)
        and row.get("kind") == "declared_nonbyte_content_identity"
        and str(row.get("artifact_path") or "")
    }
    missing_gates = [gate for gate in expected_gates if gate not in bound_gates]
    if missing_gates:
        errors.append(f"promotion certificate has no live evidence file for gates: {missing_gates}")
    for row in rows:
        path_text = str(row.get("path") or "")
        expected_hash = str(row.get("sha256") or "").lower()
        role = str(row.get("role") or "")
        if not path_text or not re_full_sha256(expected_hash):
            errors.append("promotion certificate contains an invalid live evidence binding")
            continue
        if path_text in seen_paths:
            continue
        seen_paths.add(path_text)
        if not verify_live_files or (
            role == "input_artifact" and path_text not in semantic_input_paths
        ):
            continue
        path = Path(path_text)
        if not path.is_file():
            errors.append(f"promotion certificate live evidence file is missing: {path_text}")
            continue
        try:
            actual = sha256_file(path)
        except OSError as exc:
            errors.append(f"promotion certificate live evidence file is unreadable: {path_text}: {exc}")
            continue
        if actual != expected_hash:
            errors.append(f"promotion certificate live evidence hash drift: {path_text}")
    for fingerprint in binding.get("fingerprints", []):
        if not isinstance(fingerprint, dict):
            errors.append("promotion certificate contains an invalid evidence fingerprint")
            continue
        name = str(fingerprint.get("name") or "")
        value = str(fingerprint.get("value") or "").lower()
        source = str(fingerprint.get("source") or "")
        kind = str(fingerprint.get("kind") or "")
        artifact_path = str(fingerprint.get("artifact_path") or "")
        if not name or not source or not re_full_sha256(value):
            errors.append("promotion certificate contains an invalid evidence fingerprint")
            continue
        if kind == "declared_nonbyte_content_identity":
            if not artifact_path or artifact_path not in bound_paths:
                errors.append(
                    "promotion certificate semantic/content identity is not bound to a live evidence file"
                )
    for exclusion in binding.get("excluded_same_scope_promotion_certificates", []):
        if not isinstance(exclusion, dict):
            errors.append("promotion certificate contains an invalid same-scope certificate exclusion")
            continue
        if not all(
            str(exclusion.get(key) or "").strip()
            for key in ("artifact_id", "path", "source", "reason")
        ):
            errors.append("promotion certificate contains an invalid same-scope certificate exclusion")
            continue
        for key in ("declared_sha256", "current_sha256"):
            value = str(exclusion.get(key) or "").lower()
            if value and not re_full_sha256(value):
                errors.append("promotion certificate contains an invalid same-scope certificate exclusion")
    declared_binding_hash = str(binding.get("binding_sha256") or "").lower()
    if not re_full_sha256(declared_binding_hash):
        errors.append("promotion certificate evidence binding fingerprint is missing")
    elif declared_binding_hash != promotion_evidence_binding_fingerprint(binding):
        errors.append("promotion certificate evidence binding fingerprint does not match its rows")
    return errors


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def certificate_contract_errors(
    payload: dict[str, Any],
    level_id: str,
    required_gates: list[str],
    *,
    verify_live_files: bool = True,
) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != PROMOTION_CERTIFICATE_SCHEMA_VERSION:
        errors.append("promotion certificate schema is not current")
    expected_contract = evidence_contract_for_level(level_id)
    if payload.get("evidence_contract") != expected_contract:
        errors.append(f"evidence contract is not current version {EVIDENCE_CONTRACT_VERSION}")
    expected_fingerprint = certificate_contract_fingerprint(level_id, required_gates)
    if payload.get("evidence_contract_fingerprint") != expected_fingerprint:
        errors.append("evidence contract fingerprint does not match current required gates")
    environment = payload.get("tool_environment_contract")
    if not isinstance(environment, dict):
        errors.append("certificate does not bind the current tool environment identity contract")
    else:
        groups = environment.get("groups", {}) if isinstance(environment.get("groups"), dict) else {}
        expected_environment = tool_environment_contract(groups)
        if environment != expected_environment:
            errors.append("certificate tool environment identity contract is invalid")
    rows = {
        str(row.get("name")): str(row.get("status") or "")
        for row in payload.get("required_gates", [])
        if isinstance(row, dict) and row.get("name")
    }
    missing = [gate for gate in required_gates if rows.get(str(gate)) != "pass"]
    if missing:
        errors.append(f"certificate does not contain current passing required gates: {missing}")
    errors.extend(
        promotion_evidence_binding_errors(
            payload,
            required_gates,
            verify_live_files=verify_live_files,
        )
    )
    return errors


def _capabilities(spec: dict[str, Any]) -> set[str]:
    value = spec.get("capabilities", [])
    if isinstance(value, dict):
        return {str(key) for key, enabled in value.items() if enabled}
    if isinstance(value, list):
        return {str(item) for item in value}
    return set()


def _paths(spec: dict[str, Any], key: str) -> list[str]:
    values = spec.get(key, [])
    return [str(value).lower() for value in values] if isinstance(values, list) else []


def tool_evidence_contract_errors(role: str, spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if role in {
        "leaf_functional_sim",
        "leaf_golden_compare",
        "single_layer_functional_sim",
        "single_layer_golden_compare",
        "vcs_functional_sim",
        "vcs_evidence_analyzer",
        "operator_leaf_semantic_evidence",
        "single_layer_semantic_evidence",
        "board_semantic_evidence",
    }:
        return []
    else:
        required_caps = ROLE_CAPABILITY_REQUIREMENTS.get(role, set())
    missing_caps = sorted(required_caps - _capabilities(spec))
    if missing_caps:
        errors.append(f"missing real-weight semantic capabilities {missing_caps}")
    path_requirements = ROLE_PATH_REQUIREMENTS.get(role)
    if path_requirements:
        consume_terms, produce_terms = path_requirements
        consumes = " ".join(_paths(spec, "consumes"))
        produces = " ".join(_paths(spec, "produces"))
        missing_consumes = [term for term in consume_terms if term not in consumes]
        missing_produces = [term for term in produce_terms if term not in produces]
        if missing_consumes:
            errors.append(f"declared inputs do not bind required evidence terms {missing_consumes}")
        if missing_produces:
            errors.append(f"declared outputs do not bind required evidence terms {missing_produces}")
    if role in ORACLE_PYTHON_ENVIRONMENT_ROLES:
        modules = spec.get("python_modules", [])
        if not isinstance(modules, list) or not modules:
            errors.append("tool does not declare its Python module environment contract")
        if not str(spec.get("python_environment_group") or ""):
            errors.append("tool does not bind a shared Python oracle environment group")
    return errors


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def semantic_evidence_report_errors(path: Path, level_id: str) -> list[str]:
    if not path.is_file():
        return [f"VCS evidence report is missing: {path}"]
    report = read_json_object(path)
    errors: list[str] = []
    expected = evidence_contract_for_level(level_id)
    contracts = report.get("evidence_contracts", {})
    if not isinstance(contracts, dict):
        contracts = {}
    if report.get("evidence_contract") != expected and contracts.get(level_id) != expected:
        errors.append("VCS evidence report does not bind the current evidence contract")
    if report.get("validation_policy") != COMPILE_ONLY_POLICY:
        errors.append("VCS evidence report does not use the current verification standard")
    evidence = report.get("compile_evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    compile_result = evidence.get("compile", {})
    if not isinstance(compile_result, dict):
        compile_result = {}
    if report.get("status") != "pass" or evidence.get("status") != "pass":
        errors.append("VCS evidence status is not pass")
    if compile_result.get("status") != "pass" or compile_result.get("returncode") != 0:
        errors.append("VCS compile/elaboration did not complete successfully")
    logs = evidence.get("logs")
    if not isinstance(logs, list) or not logs:
        logs = [{"path": evidence.get("log_path"), "sha256": evidence.get("log_sha256")}]
    for row in logs:
        if not isinstance(row, dict):
            errors.append("VCS compile log evidence row is malformed")
            continue
        log_path = Path(str(row.get("path") or ""))
        if not log_path.is_file() or not row.get("sha256"):
            errors.append(f"VCS compile log evidence is missing: {log_path}")
        elif sha256_file(log_path) != row["sha256"]:
            errors.append(f"VCS compile log hash does not match: {log_path}")
        elif compile_log_errors(log_path):
            errors.append(f"VCS compile log contains errors: {log_path}")
    return errors
