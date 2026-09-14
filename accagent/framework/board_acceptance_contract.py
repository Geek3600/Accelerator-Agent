"""Fail-closed contract for exact sample-project board simulation.

The contract deliberately validates evidence rather than inferring board facts
from filenames or model-specific module names.  A case adapter must describe
the user's sample-project simulation closure, compute-slot ABI, timing and AXI
contracts.  The board simulation manifest must bind those contracts to the
actual compile set, elaborated hierarchy, and structured protocol monitors.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Any, Iterable

from accagent.framework.board_progress import (
    BOARD_DEBUG_OBSERVABILITY_SCHEMA_VERSION,
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    PIPELINE_BOUNDARY_OBSERVATION_FIELDS,
    PIPELINE_BOUNDARY_OBSERVATION_SCHEMA_VERSION,
    REQUIRED_DEBUG_EVENT_KINDS,
    REQUIRED_DEBUG_SEMANTIC_ROLES,
    REQUIRED_PROGRESS_EVENT_FIELDS,
    pipeline_boundary_observation_authority,
)


SCHEMA_VERSION = "spatialaccagent.exact_board_acceptance.v1"
PREFLIGHT_SCHEMA_VERSION = "spatialaccagent.exact_board_preflight.v1"
IDENTITY_SCHEMA_VERSION = "spatialaccagent.exact_board_identity_validation.v1"
VCS_COMPILE_PLAN_SCHEMA_VERSION = "spatialaccagent.vcs_compile_plan.v1"
EXACT_BOARD_IDENTITY_V2 = "spatialaccagent.exact_sample_board_source_identity.v2"
PROGRESSIVE_SELECTOR_COVERAGE_SCHEMA_VERSION = (
    "spatialaccagent.board_interface_selection_coverage.v1"
)
SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION = (
    "spatialaccagent.board_interface_selection_map_checkpoint.v1"
)
COMPUTE_SLOT_AXI_VALIDATION_MODE = "compute_slot_axi"
EXACT_SAMPLE_PHYSICAL_DDR_VALIDATION_MODE = "exact_sample_physical_ddr"
FROZEN_COMPUTE_SLOT_IDENTITY_ATTESTATION_SCHEMA_VERSION = (
    "spatialaccagent.frozen_compute_slot_identity_attestation.v1"
)
FROZEN_COMPUTE_SLOT_IDENTITY_REQUIRED_CHECKS = {
    "exact_sample_identity",
    "llm_discovery_and_source_evidence",
    "recursive_simulation_source_closure",
    "progressive_selector_full_coverage",
    "compute_slot_abi",
    "clock_reset_calibration_timing",
    "complete_axi_interfaces",
    "simulation_identity_binding",
    "external_simulation_fixture_binding",
    "simulation_compile_source_set",
    "canonical_vcs_compile_plan",
}

VCS_COMMAND_FIELDS = {
    "order",
    "phase",
    "tool_role",
    "executable",
    "argv",
    "source_ids",
    "cwd",
    "env",
    "shell",
    "authority_refs",
}
VCS_PLAN_FIELDS = {
    "schema_version",
    "status",
    "compile_authority",
    "tool_binding",
    "top_module",
    "output",
    "ordered_commands",
    "tool_profile_sha256",
}
VCS_COMPILE_AUTHORITY_FIELDS = {
    "vivado_facts_path",
    "vivado_facts_sha256",
    "simulator_export_context_sha256s",
    "external_fixture_contract_sha256",
    "external_fixture_export_context_sha256s",
}
LEGACY_IGNORED_VCS_COMPILE_AUTHORITY_FIELDS = {
    "functional_elaboration_projection",
}
VCS_TOOL_DRIVERS = {"vcs", "vlogan", "vhdlan"}

AXI_CHANNEL_SIGNALS = {
    "aw": {"id", "addr", "len", "size", "burst", "lock", "cache", "prot", "qos", "region", "user", "valid", "ready"},
    "w": {"data", "strb", "last", "user", "valid", "ready"},
    "b": {"id", "resp", "user", "valid", "ready"},
    "ar": {"id", "addr", "len", "size", "burst", "lock", "cache", "prot", "qos", "region", "user", "valid", "ready"},
    "r": {"id", "data", "resp", "last", "user", "valid", "ready"},
}

AXI_WIDTH_FIELDS = {
    "address_width_bits",
    "data_width_bits",
    "id_width_bits",
    "strb_width_bits",
    "len_width_bits",
    "size_width_bits",
    "burst_width_bits",
    "lock_width_bits",
    "cache_width_bits",
    "prot_width_bits",
    "qos_width_bits",
    "region_width_bits",
    "awuser_width_bits",
    "wuser_width_bits",
    "buser_width_bits",
    "aruser_width_bits",
    "ruser_width_bits",
}

REQUIRED_PROTOCOL_MONITOR_CHECKS = {
    "no_unknown_control",
    "valid_stable_until_ready",
    "burst_length_size_address",
    "no_4kb_crossing",
    "write_strobe_legality",
    "last_beat_consistency",
    "response_legality",
    "transaction_id_ordering",
    "outstanding_transaction_accounting",
    "reset_calibration_traffic_gating",
}

REQUIRED_TESTBENCH_AST_CHECKS = {
    "forced_calibration_assignments",
    "behavioral_memory_models",
    "synthetic_latency_constructs",
}

REQUIRED_PROTOCOL_REPORT_FIELDS = {
    "status",
    "violations",
    "transaction_counts",
}

PROTOCOL_MONITOR_REPORT_OUTPUT_KEY = "protocol_monitor_reports"

SYNTHESIS_ONLY_ROLES = {
    "bd_synth",
    "synth",
    "synthesis",
    "synthesis_only",
    "synthesis_netlist",
    "synth_netlist",
}

BOARD_EVIDENCE_SOURCE_KINDS = {
    "vivado_project",
    "vivado_block_design",
    "vivado_ip_metadata",
    "vivado_tool_report",
    "rtl_source",
    "simulation_netlist",
    "xdc_constraint",
}


def canonical_contract_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _is_compute_slot_axi_validation(simulation: dict[str, Any]) -> bool:
    return simulation.get("validation_mode") == COMPUTE_SLOT_AXI_VALIDATION_MODE


def _closure_parts(identity: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = identity.get("selected_simulation_source_closure")
    if isinstance(raw, list):
        return _as_rows(raw), identity
    if isinstance(raw, dict):
        files = raw.get(
            "source_files",
            raw.get("sources", raw.get("files", raw.get("materialized_sources"))),
        )
        return _as_rows(files), raw
    return [], {}


def _source_id(row: dict[str, Any]) -> str:
    return str(row.get("source_id") or "").strip()


def _source_role(row: dict[str, Any]) -> str:
    return str(row.get("role") or row.get("source_role") or "").strip().lower()


def _source_path(row: dict[str, Any]) -> str:
    return str(row.get("local_path") or row.get("path") or "").strip()


def _dependencies(row: dict[str, Any]) -> list[str]:
    values = row.get("dependencies")
    if not isinstance(values, list):
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _declared_modules(row: dict[str, Any]) -> list[str]:
    values = row.get("declared_modules")
    if not isinstance(values, list):
        return []
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _normalized_source_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [
        {
            "source_id": _source_id(row),
            "role": _source_role(row),
            "sha256": str(row.get("sha256") or row.get("local_sha256") or "").strip().lower(),
            "dependencies": _dependencies(row),
            "declared_modules": _declared_modules(row),
        }
        for row in rows
    ]
    return sorted(normalized, key=lambda row: row["source_id"])


def source_closure_fingerprint(rows: Iterable[dict[str, Any]]) -> str:
    """Hash the semantic simulation closure independently of staging paths."""

    return canonical_contract_sha256(_normalized_source_rows(rows))


def compile_source_set_fingerprint(rows: Iterable[dict[str, Any]]) -> str:
    """Hash the exact source identities selected for simulator compilation."""

    return source_closure_fingerprint(rows)


def compute_slot_port_map_fingerprint(compute_slot_abi: dict[str, Any]) -> str:
    bindings = _as_rows(compute_slot_abi.get("port_bindings"))
    normalized = sorted(
        [
            {
                "port_id": str(row.get("port_id") or ""),
                "accelerator_port": str(row.get("accelerator_port") or ""),
                "direction": str(row.get("direction") or "").lower(),
                "width_bits": row.get("width_bits"),
            }
            for row in bindings
        ],
        key=lambda row: row["port_id"],
    )
    return canonical_contract_sha256(normalized)


def _resolve_path(value: str, document_path: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else document_path.parent / path


def _checkpoint_record_artifact_path(
    checkpoint_path: Path, chunk: dict[str, Any]
) -> Path | None:
    """Resolve a checkpoint record's bounded materialization path.

    `record_file` is the canonical contract name.  A checkpoint may additionally
    point at a hash-bound archived materialization under `llm/history/` after a
    live transaction is archived; that provenance must not be confused with a
    different worker record.
    """
    record_file = str(chunk.get("record_file") or "").strip()
    artifact_path = str(chunk.get("record_artifact_path") or "").strip()
    relative = Path(artifact_path) if artifact_path else Path(record_file)
    if (
        not record_file
        or relative.is_absolute()
        or ".." in relative.parts
        or (not artifact_path and relative.name != record_file)
    ):
        return None
    return (checkpoint_path.parent / relative).resolve()


def _verified_source_file(row: dict[str, Any], document_path: Path, label: str, errors: list[str]) -> None:
    source_id = _source_id(row)
    path_text = _source_path(row)
    expected = str(row.get("sha256") or row.get("local_sha256") or "").strip().lower()
    if not source_id:
        errors.append(f"{label}.source_id is missing")
    if not path_text:
        errors.append(f"{label}.path/local_path is missing")
        return
    path = _resolve_path(path_text, document_path)
    if not path.is_file():
        errors.append(f"{label} source file is missing: {path}")
        return
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        errors.append(f"{label}.sha256 is missing or invalid")
    elif sha256_file(path) != expected:
        errors.append(f"{label} source hash does not match file: {path}")


def _verified_artifact(
    row: dict[str, Any], document_path: Path, label: str, path_field: str, errors: list[str]
) -> None:
    path_text = str(row.get(path_field) or "").strip()
    expected = str(row.get("sha256") or "").strip().lower()
    if not path_text:
        errors.append(f"{label}.{path_field} is missing")
        return
    path = _resolve_path(path_text, document_path)
    if not path.is_file():
        errors.append(f"{label} artifact is missing: {path}")
        return
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        errors.append(f"{label}.sha256 is missing or invalid")
    elif sha256_file(path) != expected:
        errors.append(f"{label} artifact hash does not match: {path}")


def validate_frozen_compute_slot_identity_attestation(
    identity: dict[str, Any],
    identity_path: Path,
    simulation: dict[str, Any],
    simulation_path: Path,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate a content-addressed certificate for a previously accepted VCS plan.

    The certificate recovers only immutable Vivado command authority after a
    mutable discovery sidecar was replaced.  Current source files, compile-set
    hashes, tool binding, top, testbench, and runtime evidence are validated by
    the normal preflight on every invocation.
    """

    raw = simulation.get("frozen_compute_slot_identity_attestation")
    if raw is None:
        return False, [], {"required": False}
    errors: list[str] = []
    details: dict[str, Any] = {"required": True}
    if not isinstance(raw, dict):
        return False, ["frozen compute-slot identity attestation is not an object"], details
    if simulation.get("validation_mode") != COMPUTE_SLOT_AXI_VALIDATION_MODE:
        errors.append("frozen identity attestation is permitted only for compute_slot_axi validation")
    if raw.get("schema_version") != FROZEN_COMPUTE_SLOT_IDENTITY_ATTESTATION_SCHEMA_VERSION:
        errors.append("frozen compute-slot identity attestation schema_version is unsupported")
    if raw.get("status") != "pass":
        errors.append("frozen compute-slot identity attestation status is not pass")
    supported_fields = {
        "schema_version",
        "status",
        "source_identity_sha256",
        "attested_vivado_facts_sha256",
        "observed_replaced_live_fact_bundle_sha256",
        "vcs_compile_plan_sha256",
        "attested_simulator_export_context_sha256s",
        "prior_executed_manifest",
        "prior_vcs_runner_report",
        "prior_vcs_job_contract",
        "required_passed_checks",
    }
    unknown_fields = sorted(set(raw) - supported_fields)
    if unknown_fields:
        errors.append(
            "frozen compute-slot identity attestation contains unsupported fields: "
            f"{unknown_fields}"
        )

    identity_sha256 = sha256_file(identity_path) if identity_path.is_file() else ""
    if not identity_sha256 or raw.get("source_identity_sha256") != identity_sha256:
        errors.append("frozen identity attestation does not bind the current identity document")

    certificate_root = (identity_path.parent / "certificates").resolve()

    def load_certificate(
        field: str, label: str
    ) -> tuple[Path, dict[str, Any]]:
        reference = raw.get(field)
        if not isinstance(reference, dict):
            errors.append(f"frozen identity attestation {field} is missing")
            return Path(), {}
        _verified_artifact(reference, simulation_path, label, "path", errors)
        path_text = str(reference.get("path") or "")
        path = _resolve_path(path_text, simulation_path) if path_text else Path()
        if (
            not path_text
            or not path.is_absolute()
            or not path.resolve().is_relative_to(certificate_root)
        ):
            errors.append(f"{label} is outside the identity certificate directory")
            return path, {}
        value, load_errors = (
            _load_json_object(path, label) if path.is_file() else ({}, [])
        )
        errors.extend(load_errors)
        return path, value

    prior_path, prior = load_certificate(
        "prior_executed_manifest",
        "frozen prior executed board manifest",
    )
    runner_path, runner = load_certificate(
        "prior_vcs_runner_report",
        "frozen prior VCS runner report",
    )
    job_path, job = load_certificate(
        "prior_vcs_job_contract",
        "frozen prior VCS job contract",
    )

    declared_plan_sha256 = str(raw.get("vcs_compile_plan_sha256") or "").lower()
    if re.fullmatch(r"[0-9a-f]{64}", declared_plan_sha256) is None:
        errors.append("frozen identity attestation vcs_compile_plan_sha256 is invalid")
    declared_contexts = raw.get("attested_simulator_export_context_sha256s")
    if (
        not isinstance(declared_contexts, list)
        or not declared_contexts
        or not all(
            isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
            for value in declared_contexts
        )
        or len(declared_contexts) != len(set(declared_contexts))
    ):
        errors.append(
            "frozen identity attestation attested_simulator_export_context_sha256s is invalid"
        )
        declared_context_set: set[str] = set()
    else:
        declared_context_set = set(declared_contexts)

    attested_facts_sha256 = str(raw.get("attested_vivado_facts_sha256") or "").lower()
    if (
        re.fullmatch(r"[0-9a-f]{64}", attested_facts_sha256) is None
        or attested_facts_sha256
        != str(identity.get("vivado_facts_sha256") or "").lower()
    ):
        errors.append(
            "frozen identity attestation does not bind identity.vivado_facts_sha256"
        )
    observed_facts_sha256 = str(
        raw.get("observed_replaced_live_fact_bundle_sha256") or ""
    ).lower()
    facts_path_text = str(identity.get("vivado_facts_path") or "")
    facts_path = (
        _resolve_path(facts_path_text, identity_path) if facts_path_text else Path()
    )
    if (
        re.fullmatch(r"[0-9a-f]{64}", observed_facts_sha256) is None
        or not facts_path_text
        or not facts_path.is_file()
        or sha256_file(facts_path) != observed_facts_sha256
        or observed_facts_sha256 == attested_facts_sha256
    ):
        errors.append(
            "frozen identity attestation does not bind the replaced live Vivado fact bundle"
        )

    required_checks = raw.get("required_passed_checks")
    if (
        not isinstance(required_checks, list)
        or set(required_checks) != FROZEN_COMPUTE_SLOT_IDENTITY_REQUIRED_CHECKS
        or len(required_checks) != len(set(required_checks))
    ):
        errors.append(
            "frozen identity attestation required_passed_checks is incomplete or ambiguous"
        )

    prior_plan: dict[str, Any] = {}
    prior_compile_source_ids: list[str] = []

    if prior:
        if prior.get("validation_mode") != COMPUTE_SLOT_AXI_VALIDATION_MODE:
            errors.append("frozen prior executed manifest is not compute_slot_axi")
        if prior.get("exact_sample_wrapper_unmodified") is not True:
            errors.append("frozen prior executed manifest modified the sample wrapper")
        if prior.get("compiled_sample_source_ids") != []:
            errors.append("frozen prior executed manifest compiled sample-project sources")
        if prior.get("external_simulation_fixture") not in (None, {}):
            errors.append("frozen prior executed manifest binds an external fixture")
        prior_execution = (
            prior.get("execution_evidence")
            if isinstance(prior.get("execution_evidence"), dict)
            else {}
        )
        if (
            prior.get("source_identity_sha256") != identity_sha256
            or prior_execution.get("source_identity_sha256") != identity_sha256
        ):
            errors.append("frozen prior executed manifest does not bind the current identity")
        execution = prior_execution
        compile_evidence = (
            execution.get("compile")
            if isinstance(execution.get("compile"), dict)
            else {}
        )
        compile_exit = compile_evidence.get("exit_code")
        if (
            execution.get("tool") != "vcs"
            or not isinstance(compile_exit, int)
            or isinstance(compile_exit, bool)
        ):
            errors.append(
                "frozen prior executed manifest does not prove entry into real VCS compilation"
            )
        if (
            re.fullmatch(
                r"[0-9a-f]{64}", str(prior_execution.get("command_sha256") or "")
            )
            is None
            or not str(prior_execution.get("tool_version") or "").strip()
        ):
            errors.append(
                "frozen prior executed manifest lacks real VCS command/version evidence"
            )
        prior_acceptance = (
            runner.get("exact_board_preflight")
            if isinstance(runner.get("exact_board_preflight"), dict)
            else {}
        )
        check_rows = [
            row
            for row in prior_acceptance.get("checks", [])
            if isinstance(row, dict) and str(row.get("name") or "")
        ]
        check_names = [str(row.get("name")) for row in check_rows]
        if len(check_names) != len(set(check_names)):
            errors.append("frozen prior VCS preflight contains duplicate check names")
        checks = {str(row.get("name")): row for row in check_rows}
        for name in sorted(FROZEN_COMPUTE_SLOT_IDENTITY_REQUIRED_CHECKS):
            check = checks.get(name, {})
            if check.get("status") != "pass" or check.get("blockers") not in (None, []):
                errors.append(f"frozen prior VCS preflight did not pass required check: {name}")
        for prior_field, identity_field in (
            (
                "source_closure_sha256",
                "selected_simulation_source_closure_sha256",
            ),
            ("compute_slot_abi_sha256", "compute_slot_abi_sha256"),
            ("timing_contract_sha256", "timing_contract_sha256"),
            ("axi_interfaces_sha256", "axi_interfaces_sha256"),
        ):
            if (
                not identity.get(identity_field)
                or prior.get(prior_field) != identity.get(identity_field)
            ):
                errors.append(
                    f"frozen prior executed manifest does not bind identity.{identity_field}"
                )
            if (
                prior_execution.get(prior_field)
                != identity.get(identity_field)
            ):
                errors.append(
                    "frozen prior VCS execution does not bind "
                    f"identity.{identity_field}"
                )
        prior_plan = (
            prior.get("vcs_compile_plan")
            if isinstance(prior.get("vcs_compile_plan"), dict)
            else {}
        )
        prior_plan_sha256 = canonical_contract_sha256(prior_plan) if prior_plan else ""
        prior_authority = (
            prior_plan.get("compile_authority")
            if isinstance(prior_plan.get("compile_authority"), dict)
            else {}
        )
        if (
            str(prior_authority.get("vivado_facts_sha256") or "").lower()
            != attested_facts_sha256
            or set(prior_authority.get("simulator_export_context_sha256s", []))
            != declared_context_set
            or prior_plan_sha256 != declared_plan_sha256
        ):
            errors.append(
                "frozen prior executed manifest does not bind the attested Vivado export authority"
            )
        if (
            str(prior.get("vcs_compile_plan_sha256") or "").lower()
            != declared_plan_sha256
            or str(prior_execution.get("vcs_compile_plan_sha256") or "").lower()
            != declared_plan_sha256
        ):
            errors.append("frozen prior execution does not bind its canonical VCS plan")
        prior_compile_source_ids = [
            str(value)
            for value in prior.get("compile_source_ids", [])
            if isinstance(value, str) and value
        ]
        planned_source_ids: list[str] = []
        for command in prior_plan.get("ordered_commands", []):
            if isinstance(command, dict) and command.get("phase") == "compile":
                source_ids = command.get("source_ids")
                if isinstance(source_ids, list):
                    planned_source_ids.extend(
                        str(value)
                        for value in source_ids
                        if isinstance(value, str) and value
                    )
        if (
            not prior_compile_source_ids
            or planned_source_ids != prior_compile_source_ids
            or len(prior_compile_source_ids) != len(set(prior_compile_source_ids))
        ):
            errors.append(
                "frozen prior VCS plan does not bind the prior transformed source-ID order"
            )

    if runner:
        prior_preflight = (
            runner.get("exact_board_preflight")
            if isinstance(runner.get("exact_board_preflight"), dict)
            else {}
        )
        if (
            runner.get("exact_board_preflight_passed") is not True
            or prior_preflight.get("status") != "pass"
            or prior_preflight.get("blockers") not in (None, [])
            or str(runner.get("vcs_compile_plan_sha256") or "").lower()
            != declared_plan_sha256
            or str(prior_preflight.get("vcs_compile_plan_sha256") or "").lower()
            != declared_plan_sha256
        ):
            errors.append(
                "frozen prior VCS runner report does not attest a passing exact-board preflight"
            )
        if runner.get("validation_mode") != COMPUTE_SLOT_AXI_VALIDATION_MODE:
            errors.append("frozen prior VCS runner is not exact compute-slot validation")
        runner_implementation_path = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "verification"
            / "case_board_vcs_functional.py"
        )
        if (
            not runner_implementation_path.is_file()
            or runner.get("runner_implementation_sha256")
            != sha256_file(runner_implementation_path)
        ):
            errors.append(
                "frozen prior VCS runner report does not bind the current runner implementation"
            )

    runner_fingerprint = str(runner.get("input_fingerprint_sha256") or "")
    recovery = (
        runner.get("remote_job_recovery_contract")
        if isinstance(runner.get("remote_job_recovery_contract"), dict)
        else {}
    )
    job_ref = raw.get("prior_vcs_job_contract")
    job_ref_sha256 = (
        str(job_ref.get("sha256") or "").lower()
        if isinstance(job_ref, dict)
        else ""
    )
    if (
        recovery.get("status") != "pass"
        or recovery.get("job_contract_sha256") != job_ref_sha256
        or re.fullmatch(r"[0-9a-f]{64}", runner_fingerprint) is None
    ):
        errors.append("frozen prior VCS runner does not bind its recoverable remote job")
    if job:
        runner_remote_workdir = str(runner.get("remote_workdir") or "")
        job_fingerprint_payload = {
            key: value
            for key, value in job.items()
            if key not in {"input_fingerprint_sha256", "remote_workdir"}
        }
        recomputed_fingerprint = canonical_contract_sha256(job_fingerprint_payload)
        remote_stage_root = str(job.get("remote_stage_root") or "").rstrip("/")
        expected_remote_workdir = (
            f"{remote_stage_root}/{runner_fingerprint[:12]}_"
            f"{int(runner_fingerprint[12:], 16)}"
            if remote_stage_root
            and re.fullmatch(r"[0-9a-f]{64}", runner_fingerprint)
            else ""
        )
        job_source_ids = job.get("verified_compile_source_ids")
        if (
            job.get("input_fingerprint_sha256") != runner_fingerprint
            or recomputed_fingerprint != runner_fingerprint
            or job.get("source_identity_sha256") != identity_sha256
            or job.get("source_closure_sha256")
            != identity.get("selected_simulation_source_closure_sha256")
            or job.get("vcs_compile_plan_sha256") != declared_plan_sha256
            or canonical_contract_sha256(job.get("vcs_compile_plan", {}))
            != declared_plan_sha256
            or not isinstance(job_source_ids, list)
            or len(job_source_ids) != len(set(job_source_ids))
            or set(job_source_ids) != set(prior_compile_source_ids)
            or job.get("top_module") != prior.get("top_module")
            or job.get("remote_workdir") != runner_remote_workdir
            or runner_remote_workdir != expected_remote_workdir
            or prior.get("execution_evidence", {}).get("job_id")
            != runner_remote_workdir
            or job.get("preflight_manifest_projection_sha256")
            != runner.get("preflight_manifest_projection_sha256")
        ):
            errors.append(
                "frozen prior VCS job contract does not bind the runner, identity, plan, and source IDs"
            )
        runner_compile = (
            runner.get("compile") if isinstance(runner.get("compile"), dict) else {}
        )
        launch = (
            runner_compile.get("launch")
            if isinstance(runner_compile.get("launch"), dict)
            else {}
        )
        prior_compile_exit = prior.get("execution_evidence", {}).get("compile", {}).get(
            "exit_code"
        )
        if (
            runner.get("phase") != "remote_vcs"
            or runner_compile.get("remote_state") != "done"
            or runner_compile.get("transport")
            != "detached_remote_job_with_short_ssh_polling"
            or runner_compile.get("returncode") != prior_compile_exit
            or launch.get("status") != "pass"
            or launch.get("returncode") != 0
            or "SPATIALACC_REMOTE_JOB_STARTED pid="
            not in str(launch.get("stdout_tail") or "")
            or runner_compile.get("remote_command") != job.get("compile_command")
        ):
            errors.append(
                "frozen prior VCS runner does not prove detached real-tool compilation"
            )

    current_plan = (
        simulation.get("vcs_compile_plan")
        if isinstance(simulation.get("vcs_compile_plan"), dict)
        else {}
    )
    if (
        not current_plan
        or canonical_contract_sha256(current_plan) != declared_plan_sha256
        or str(simulation.get("vcs_compile_plan_sha256") or "").lower()
        != declared_plan_sha256
    ):
        errors.append(
            "current VCS compile plan differs from the frozen preflight-validated plan"
        )

    details.update(
        {
            "source_identity_sha256": identity_sha256 or None,
            "prior_executed_manifest": str(prior_path) if prior_path.is_file() else None,
            "prior_vcs_runner_report": str(runner_path) if runner_path.is_file() else None,
            "prior_vcs_job_contract": str(job_path) if job_path.is_file() else None,
            "attested_vivado_facts_sha256": attested_facts_sha256 or None,
            "observed_replaced_live_fact_bundle_sha256": observed_facts_sha256 or None,
            "vcs_compile_plan_sha256": declared_plan_sha256 or None,
            "simulator_export_context_count": len(declared_context_set),
        }
    )
    return not errors, errors, details


def _require_evidence_refs(value: Any, label: str, evidence_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{label}.evidence_refs must be a non-empty list")
        return
    refs = {str(item).strip() for item in value if str(item).strip()}
    missing = sorted(refs - evidence_ids)
    if not refs or missing:
        errors.append(f"{label}.evidence_refs contain unknown evidence ids: {missing}")


def _validate_discovery_provenance(
    identity: dict[str, Any], identity_path: Path
) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    provenance = identity.get("discovery_provenance")
    if not isinstance(provenance, dict):
        return set(), ["identity.discovery_provenance is missing"]
    if str(provenance.get("mode") or "").lower() != "llm":
        errors.append("identity.discovery_provenance.mode must be llm")
    if provenance.get("used_fallback") is not False:
        errors.append("identity.discovery_provenance.used_fallback must be false")
    for field in ("agent_id", "model"):
        if not str(provenance.get(field) or "").strip():
            errors.append(f"identity.discovery_provenance.{field} is missing")
    fact_bundle = provenance.get("input_fact_bundle")
    if not isinstance(fact_bundle, dict):
        errors.append("identity.discovery_provenance.input_fact_bundle is missing")
    else:
        _verified_artifact(
            fact_bundle,
            identity_path,
            "identity.discovery_provenance.input_fact_bundle",
            "path",
            errors,
        )

    records = _as_rows(identity.get("evidence_records"))
    if not records:
        errors.append("identity.evidence_records is empty")
        return set(), errors
    evidence_ids: set[str] = set()
    for index, row in enumerate(records):
        label = f"identity.evidence_records[{index}]"
        evidence_id = str(row.get("evidence_id") or "").strip()
        if not evidence_id:
            errors.append(f"{label}.evidence_id is missing")
        elif evidence_id in evidence_ids:
            errors.append(f"identity.evidence_records has duplicate evidence_id: {evidence_id}")
        evidence_ids.add(evidence_id)
        if str(row.get("source_kind") or "") not in BOARD_EVIDENCE_SOURCE_KINDS:
            errors.append(f"{label}.source_kind is not a supported board-source evidence kind")
        _verified_artifact(row, identity_path, label, "source_path", errors)
        locator = row.get("locator")
        if not isinstance(locator, dict) or not str(locator.get("kind") or "").strip() or "value" not in locator:
            errors.append(f"{label}.locator must be a structured source locator")
        if not str(row.get("fact_kind") or "").strip() or "observed_value" not in row:
            errors.append(f"{label} lacks fact_kind/observed_value")
    return evidence_ids, errors


def _nested_fact_object_ids(value: Any) -> list[str]:
    result: list[str] = []
    if isinstance(value, dict):
        object_id = value.get("object_id")
        if isinstance(object_id, str) and object_id:
            result.append(object_id)
        for child in value.values():
            result.extend(_nested_fact_object_ids(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(_nested_fact_object_ids(child))
    return list(dict.fromkeys(result))


def _coverage_id_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        errors.append(f"{label} must be a string-ID list")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label} contains duplicate IDs")
    return list(value)


def _validate_progressive_selector_coverage(
    identity: dict[str, Any], identity_path: Path, closure_rows: list[dict[str, Any]]
) -> tuple[list[str], dict[str, Any]]:
    """Validate the v2 progressive LLM selector's persisted full-coverage proof."""

    if identity.get("schema_version") != EXACT_BOARD_IDENTITY_V2:
        return [], {"required_for_identity_schema": False}

    errors: list[str] = []
    details: dict[str, Any] = {"required_for_identity_schema": True}
    provenance = (
        identity.get("discovery_provenance")
        if isinstance(identity.get("discovery_provenance"), dict)
        else {}
    )
    coverage_ref = provenance.get("progressive_selector_coverage")
    if not isinstance(coverage_ref, dict):
        return [
            "identity.discovery_provenance.progressive_selector_coverage is required for exact identity v2"
        ], details
    _verified_artifact(
        coverage_ref,
        identity_path,
        "identity.discovery_provenance.progressive_selector_coverage",
        "path",
        errors,
    )
    ledger_path_text = str(coverage_ref.get("path") or "")
    ledger_path = _resolve_path(ledger_path_text, identity_path) if ledger_path_text else Path()
    details["ledger_path"] = str(ledger_path) if ledger_path_text else None
    details["ledger_sha256"] = str(coverage_ref.get("sha256") or "") or None
    if not ledger_path.is_file():
        return errors, details
    ledger, load_errors = _load_json_object(
        ledger_path, "progressive selector coverage ledger"
    )
    errors.extend(load_errors)
    if not ledger:
        return errors, details
    if ledger.get("schema_version") != PROGRESSIVE_SELECTOR_COVERAGE_SCHEMA_VERSION:
        errors.append("progressive selector coverage ledger schema_version is unsupported")
    if ledger.get("status") != "pass":
        errors.append("progressive selector coverage ledger status is not pass")

    checkpoint_ref = ledger.get("map_semantic_checkpoint")
    checkpoint_path = Path()
    checkpoint_chunks: dict[int, dict[str, Any]] = {}
    if not isinstance(checkpoint_ref, dict):
        errors.append("progressive selector coverage ledger map_semantic_checkpoint is missing")
    else:
        _verified_artifact(
            checkpoint_ref,
            ledger_path,
            "progressive selector coverage ledger map_semantic_checkpoint",
            "path",
            errors,
        )
        checkpoint_path_text = str(checkpoint_ref.get("path") or "")
        checkpoint_path = (
            _resolve_path(checkpoint_path_text, ledger_path)
            if checkpoint_path_text
            else Path()
        )
        details["map_semantic_checkpoint_path"] = (
            str(checkpoint_path) if checkpoint_path_text else None
        )
        details["map_semantic_checkpoint_sha256"] = (
            str(checkpoint_ref.get("sha256") or "") or None
        )
        if checkpoint_path.is_file():
            checkpoint, checkpoint_load_errors = _load_json_object(
                checkpoint_path, "progressive selector map semantic checkpoint"
            )
            errors.extend(checkpoint_load_errors)
            if checkpoint.get("schema_version") != SELECTOR_MAP_CHECKPOINT_SCHEMA_VERSION:
                errors.append("progressive selector map semantic checkpoint schema_version is unsupported")
            if checkpoint.get("status") != "pass":
                errors.append("progressive selector map semantic checkpoint status is not pass")
            raw_chunk_count = checkpoint.get("chunk_count")
            raw_chunks = checkpoint.get("chunks")
            checkpoint_chunk_count = (
                raw_chunk_count
                if isinstance(raw_chunk_count, int)
                and not isinstance(raw_chunk_count, bool)
                and raw_chunk_count > 0
                else 0
            )
            if (
                checkpoint_chunk_count == 0
                or not isinstance(raw_chunks, list)
                or len(raw_chunks) != checkpoint_chunk_count
            ):
                errors.append(
                    "progressive selector map semantic checkpoint chunk_count/chunks are invalid"
                )
                raw_chunks = raw_chunks if isinstance(raw_chunks, list) else []
            seen_checkpoint_agents: set[str] = set()
            for index, chunk in enumerate(raw_chunks):
                label = f"progressive selector map semantic checkpoint chunks[{index}]"
                if not isinstance(chunk, dict):
                    errors.append(f"{label} is not an object")
                    continue
                chunk_index = chunk.get("chunk_index")
                if (
                    not isinstance(chunk_index, int)
                    or isinstance(chunk_index, bool)
                    or chunk_index in checkpoint_chunks
                ):
                    errors.append(f"{label}.chunk_index is invalid or duplicated")
                    continue
                checkpoint_chunks[chunk_index] = chunk
                if chunk.get("chunk_count") != checkpoint_chunk_count or isinstance(
                    chunk.get("chunk_count"), bool
                ):
                    errors.append(f"{label}.chunk_count differs from the checkpoint")
                agent = str(chunk.get("agent") or "")
                if not agent or agent in seen_checkpoint_agents:
                    errors.append(f"{label}.agent is missing or duplicated")
                seen_checkpoint_agents.add(agent)
                fingerprint = str(chunk.get("semantic_fingerprint") or "").lower()
                if re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
                    errors.append(f"{label}.semantic_fingerprint is invalid")
                record_file = str(chunk.get("record_file") or "")
                if (
                    not record_file
                    or Path(record_file).is_absolute()
                    or Path(record_file).name != record_file
                ):
                    errors.append(f"{label}.record_file is not a safe checkpoint-local filename")
                record_artifact_path = str(
                    chunk.get("record_artifact_path") or ""
                ).strip()
                if record_artifact_path:
                    artifact_relative = Path(record_artifact_path)
                    if artifact_relative.is_absolute() or ".." in artifact_relative.parts:
                        errors.append(
                            f"{label}.record_artifact_path is outside the checkpoint directory"
                        )
                if re.fullmatch(r"[0-9a-f]{64}", str(chunk.get("record_sha256") or "")) is None:
                    errors.append(f"{label}.record_sha256 is invalid")
                if chunk.get("last_materialization_source") not in {
                    "exact_prompt",
                    "semantic_checkpoint",
                }:
                    errors.append(f"{label}.last_materialization_source is invalid")
                if chunk.get("origin_exact_prompt_validated") is not True:
                    errors.append(f"{label}.origin_exact_prompt_validated is not true")
            if set(checkpoint_chunks) != set(range(checkpoint_chunk_count)):
                errors.append(
                    "progressive selector map semantic checkpoint chunk indexes are not contiguous"
                )
            details["map_semantic_checkpoint_chunk_count"] = len(checkpoint_chunks)

    fact_bundle = (
        provenance.get("input_fact_bundle")
        if isinstance(provenance.get("input_fact_bundle"), dict)
        else {}
    )
    fact_path_text = str(fact_bundle.get("path") or "")
    fact_path = _resolve_path(fact_path_text, identity_path) if fact_path_text else Path()
    identity_fact_path_text = str(identity.get("vivado_facts_path") or "")
    identity_fact_path = (
        _resolve_path(identity_fact_path_text, identity_path)
        if identity_fact_path_text
        else Path()
    )
    if (
        not fact_path_text
        or not identity_fact_path_text
        or fact_path.resolve() != identity_fact_path.resolve()
        or str(fact_bundle.get("sha256") or "").lower()
        != str(identity.get("vivado_facts_sha256") or "").lower()
    ):
        errors.append(
            "exact identity v2 input_fact_bundle does not bind identity.vivado_facts_path/sha256"
        )
    facts: dict[str, Any] = {}
    if not fact_path.is_file():
        errors.append("exact identity v2 Vivado fact bundle is missing")
    else:
        facts, fact_load_errors = _load_json_object(fact_path, "exact identity v2 Vivado fact bundle")
        errors.extend(fact_load_errors)
        expected_fact_canonical_sha256 = canonical_contract_sha256(facts) if facts else ""
        if (
            str(ledger.get("input_vivado_fact_canonical_sha256") or "").lower()
            != expected_fact_canonical_sha256
        ):
            errors.append(
                "progressive selector coverage ledger does not bind the current Vivado fact canonical hash"
            )

    expected_object_ids = _nested_fact_object_ids(facts.get("objects", [])) if facts else []
    if len(expected_object_ids) != len(set(expected_object_ids)):
        errors.append("current Vivado facts contain duplicate progressive-selector object IDs")
    expected_source_ids = [_source_id(row) for row in closure_rows if _source_id(row)]
    fact_simulation = facts.get("simulation") if isinstance(facts.get("simulation"), dict) else {}
    fact_source_rows = _as_rows(fact_simulation.get("source_files"))
    fact_source_ids = [_source_id(row) for row in fact_source_rows if _source_id(row)]
    if (
        not fact_source_ids
        or len(fact_source_ids) != len(set(fact_source_ids))
        or set(fact_source_ids) != set(expected_source_ids)
    ):
        errors.append(
            "exact identity v2 Vivado source catalog does not exactly match the selected simulation source closure"
        )

    coverage = ledger.get("complete_coverage")
    reviewed_object_ids: list[str] = []
    reviewed_source_ids: list[str] = []
    if not isinstance(coverage, dict):
        errors.append("progressive selector coverage ledger complete_coverage is missing")
    else:
        reviewed_object_ids = _coverage_id_list(
            coverage.get("reviewed_object_ids"),
            "progressive selector complete_coverage.reviewed_object_ids",
            errors,
        )
        reviewed_source_ids = _coverage_id_list(
            coverage.get("reviewed_source_ids"),
            "progressive selector complete_coverage.reviewed_source_ids",
            errors,
        )
        for kind, reviewed, expected in (
            ("object", reviewed_object_ids, expected_object_ids),
            ("source", reviewed_source_ids, expected_source_ids),
        ):
            if set(reviewed) != set(expected):
                errors.append(
                    f"progressive selector complete {kind} coverage differs from current identity facts"
                )
            if coverage.get(f"reviewed_{kind}_count") != len(reviewed) or isinstance(
                coverage.get(f"reviewed_{kind}_count"), bool
            ):
                errors.append(
                    f"progressive selector complete_coverage.reviewed_{kind}_count is stale"
                )
            expected_hash = canonical_contract_sha256(sorted(reviewed))
            if str(coverage.get(f"reviewed_{kind}_ids_sha256") or "").lower() != expected_hash:
                errors.append(
                    f"progressive selector complete_coverage.reviewed_{kind}_ids_sha256 is stale"
                )
        if coverage.get("all_fact_and_source_units_reviewed") is not True:
            errors.append(
                "progressive selector complete_coverage.all_fact_and_source_units_reviewed is not true"
            )
    details["reviewed_object_count"] = len(reviewed_object_ids)
    details["reviewed_source_count"] = len(reviewed_source_ids)

    worker_rows = ledger.get("worker_records")
    if not isinstance(worker_rows, list) or not worker_rows:
        errors.append("progressive selector coverage ledger worker_records is empty")
        worker_rows = []
    seen_worker_paths: set[Path] = set()
    seen_map_chunk_indexes: set[int] = set()
    map_object_ids: list[str] = []
    map_source_ids: list[str] = []
    for index, row in enumerate(worker_rows):
        label = f"progressive selector coverage ledger worker_records[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} is not an object")
            continue
        phase = str(row.get("phase") or "")
        if phase not in {"map", "reduce"}:
            errors.append(f"{label}.phase is invalid")
        path_text = str(row.get("path") or "")
        worker_path = _resolve_path(path_text, ledger_path) if path_text else Path()
        expected_worker_sha256 = str(row.get("sha256") or "").lower()
        if not path_text or worker_path in seen_worker_paths:
            errors.append(f"{label}.path is missing or duplicated")
        seen_worker_paths.add(worker_path)
        if not worker_path.is_file():
            errors.append(f"{label} artifact is missing: {worker_path}")
            continue
        if (
            re.fullmatch(r"[0-9a-f]{64}", expected_worker_sha256) is None
            or sha256_file(worker_path) != expected_worker_sha256
        ):
            errors.append(f"{label} artifact hash does not match")
        if phase == "map":
            chunk_index = row.get("chunk_index")
            if (
                not isinstance(chunk_index, int)
                or isinstance(chunk_index, bool)
                or chunk_index in seen_map_chunk_indexes
            ):
                errors.append(f"{label}.chunk_index is invalid or duplicated")
                checkpoint_chunk = None
            else:
                seen_map_chunk_indexes.add(chunk_index)
                checkpoint_chunk = checkpoint_chunks.get(chunk_index)
                if checkpoint_chunk is None:
                    errors.append(f"{label}.chunk_index has no map checkpoint chunk")
            semantic_fingerprint = str(row.get("semantic_fingerprint") or "").lower()
            if re.fullmatch(r"[0-9a-f]{64}", semantic_fingerprint) is None:
                errors.append(f"{label}.semantic_fingerprint is invalid")
            reuse_authority = row.get("reuse_authority")
            if not isinstance(reuse_authority, dict):
                errors.append(f"{label}.reuse_authority is missing")
                reuse_authority = {}
            if checkpoint_chunk is not None:
                checkpoint_fingerprint = str(
                    checkpoint_chunk.get("semantic_fingerprint") or ""
                ).lower()
                checkpoint_record_path = _checkpoint_record_artifact_path(
                    checkpoint_path, checkpoint_chunk
                )
                if row.get("agent") != checkpoint_chunk.get("agent"):
                    errors.append(f"{label}.agent differs from its map checkpoint chunk")
                if checkpoint_record_path is None:
                    errors.append(
                        f"{label}.map checkpoint record artifact path is invalid"
                    )
                elif worker_path.resolve() != checkpoint_record_path:
                    errors.append(
                        f"{label}.path differs from its hash-bound map checkpoint record artifact"
                    )
                if expected_worker_sha256 != str(
                    checkpoint_chunk.get("record_sha256") or ""
                ).lower():
                    errors.append(f"{label}.sha256 differs from its map checkpoint record_sha256")
                if semantic_fingerprint != checkpoint_fingerprint:
                    errors.append(
                        f"{label}.semantic_fingerprint differs from its map checkpoint chunk"
                    )
                if (
                    reuse_authority.get("checkpoint_chunk_index") != chunk_index
                    or isinstance(reuse_authority.get("checkpoint_chunk_index"), bool)
                    or str(
                        reuse_authority.get("checkpoint_semantic_fingerprint") or ""
                    ).lower()
                    != checkpoint_fingerprint
                    or reuse_authority.get("materialization_source")
                    != checkpoint_chunk.get("last_materialization_source")
                    or reuse_authority.get("materialization_source")
                    not in {"exact_prompt", "semantic_checkpoint"}
                ):
                    errors.append(
                        f"{label}.reuse_authority does not bind its current map checkpoint chunk"
                    )
        worker, worker_load_errors = _load_json_object(worker_path, label)
        errors.extend(worker_load_errors)
        if worker and row.get("agent") != worker.get("agent"):
            errors.append(f"{label}.agent differs from the hash-bound worker record")
        output = worker.get("output") if isinstance(worker.get("output"), dict) else {}
        worker_object_ids = _coverage_id_list(
            output.get("reviewed_object_ids"), f"{label}.output.reviewed_object_ids", errors
        )
        worker_source_ids = _coverage_id_list(
            output.get("reviewed_source_ids"), f"{label}.output.reviewed_source_ids", errors
        )
        for kind, reviewed, expected in (
            ("object", worker_object_ids, expected_object_ids),
            ("source", worker_source_ids, expected_source_ids),
        ):
            if not set(reviewed).issubset(set(expected)):
                errors.append(f"{label} reviews unknown {kind} IDs")
            if row.get(f"reviewed_{kind}_count") != len(reviewed) or isinstance(
                row.get(f"reviewed_{kind}_count"), bool
            ):
                errors.append(f"{label}.reviewed_{kind}_count is stale")
            if (
                str(row.get(f"reviewed_{kind}_ids_sha256") or "").lower()
                != canonical_contract_sha256(sorted(reviewed))
            ):
                errors.append(f"{label}.reviewed_{kind}_ids_sha256 is stale")
        if phase == "map":
            map_object_ids.extend(worker_object_ids)
            map_source_ids.extend(worker_source_ids)
    if seen_map_chunk_indexes != set(checkpoint_chunks):
        errors.append(
            "progressive selector map worker rows do not cover every semantic checkpoint chunk exactly once"
        )
    for kind, reviewed, expected in (
        ("object", map_object_ids, expected_object_ids),
        ("source", map_source_ids, expected_source_ids),
    ):
        if len(reviewed) != len(set(reviewed)) or set(reviewed) != set(expected):
            errors.append(
                f"progressive selector map worker records do not exactly partition all {kind} IDs"
            )
    details["worker_record_count"] = len(worker_rows)
    return errors, details


def _is_synthesis_only(row: dict[str, Any]) -> bool:
    role = _source_role(row)
    source_set = str(row.get("source_set") or row.get("purpose") or "").strip().lower()
    return role in SYNTHESIS_ONLY_ROLES or source_set in {"synth", "synthesis", "synthesis_only"}


def _is_simulator_compile_input(row: dict[str, Any]) -> bool:
    path = Path(str(row.get("path") or row.get("local_path") or row.get("remote_path") or ""))
    language = " ".join(
        str(row.get(field) or "").lower() for field in ("file_type", "language")
    )
    suffix = path.suffix.lower()
    if suffix in {".vh", ".svh"} or "header" in language:
        return False
    if any(
        value in language
        for value in ("elf", "firmware", "runtime auxiliary", "non-hdl", "non hdl")
    ):
        return False
    return suffix in {
        ".v",
        ".vp",
        ".sv",
        ".svp",
        ".vhd",
        ".vhdl",
    } or any(value in language for value in ("verilog", "vhdl"))


def _root_ids(identity: dict[str, Any], metadata: dict[str, Any], rows: list[dict[str, Any]]) -> list[str]:
    for value in (
        metadata.get("root_source_ids"),
        identity.get("selected_simulation_source_roots"),
    ):
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
    return [_source_id(row) for row in rows if row.get("is_root") is True]


def _meta_value(identity: dict[str, Any], metadata: dict[str, Any], key: str) -> Any:
    return metadata[key] if key in metadata else identity.get(key)


def _validate_source_closure(
    identity: dict[str, Any], identity_path: Path, evidence_ids: set[str]
) -> tuple[list[dict[str, Any]], str, list[str], dict[str, Any]]:
    errors: list[str] = []
    rows, metadata = _closure_parts(identity)
    if not rows:
        errors.append("identity.selected_simulation_source_closure has no source files")
        return [], "", errors, {}

    ids = [_source_id(row) for row in rows]
    if any(not value for value in ids):
        errors.append("identity.selected_simulation_source_closure contains a source without source_id")
    duplicates = sorted({value for value in ids if value and ids.count(value) > 1})
    if duplicates:
        errors.append(f"identity.selected_simulation_source_closure has duplicate source_id values: {duplicates}")
    for index, row in enumerate(rows):
        label = f"identity.selected_simulation_source_closure[{index}]"
        _verified_source_file(row, identity_path, label, errors)
        if not _source_role(row):
            errors.append(f"{label}.role is missing")
        if "dependencies" not in row or not isinstance(row.get("dependencies"), list):
            errors.append(f"{label}.dependencies must be an explicit list")
        _require_evidence_refs(row.get("evidence_refs"), label, evidence_ids, errors)
        if _is_synthesis_only(row):
            errors.append(f"{label} is synthesis-only and must not enter the simulation compile closure")

    roots = _root_ids(identity, metadata, rows)
    if not roots:
        errors.append("identity.selected_simulation_source_closure root_source_ids are missing")
    id_set = {value for value in ids if value}
    unknown_roots = sorted(set(roots) - id_set)
    if unknown_roots:
        errors.append(f"identity simulation closure roots are not source_ids in the closure: {unknown_roots}")
    dep_errors: list[str] = []
    by_id = {_source_id(row): row for row in rows if _source_id(row)}
    for row in rows:
        missing = sorted(set(_dependencies(row)) - id_set)
        if missing:
            dep_errors.append(f"{_source_id(row)} -> {missing}")
    if dep_errors:
        errors.append(f"identity simulation closure has unresolved internal dependencies: {dep_errors}")

    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        source_id = stack.pop()
        if source_id in reachable or source_id not in by_id:
            continue
        reachable.add(source_id)
        stack.extend(_dependencies(by_id[source_id]))
    unreachable = sorted(id_set - reachable)
    if unreachable:
        errors.append(f"identity simulation source closure contains files not reachable recursively from its roots: {unreachable}")

    if _meta_value(identity, metadata, "recursive_dependency_scan_complete") is not True:
        errors.append("identity simulation closure recursive_dependency_scan_complete is not true")
    unresolved = _meta_value(identity, metadata, "unresolved_dependencies")
    if not isinstance(unresolved, list) or unresolved:
        errors.append("identity simulation closure unresolved_dependencies must be an explicit empty list")
    duplicate_modules = _meta_value(identity, metadata, "duplicate_module_definitions")
    if not isinstance(duplicate_modules, list) or duplicate_modules:
        errors.append("identity simulation closure duplicate_module_definitions must be an explicit empty list")
    external = _meta_value(identity, metadata, "external_library_dependencies")
    if not isinstance(external, list):
        errors.append("identity simulation closure external_library_dependencies must be an explicit list")
    else:
        for index, row in enumerate(external):
            if not isinstance(row, dict) or not row.get("library") or row.get("resolved") is not True:
                errors.append(
                    f"identity simulation closure external_library_dependencies[{index}] is not a resolved structured library binding"
                )

    top_module = str(identity.get("top_module") or "").strip()
    if not top_module:
        errors.append("identity.top_module is missing")
    root_rows = [by_id[value] for value in roots if value in by_id]
    if top_module and not any(top_module in _declared_modules(row) for row in root_rows):
        errors.append("identity.top_module is not declared by a simulation closure root source")
    if not any(
        _source_role(row) in {"wrapper", "board_wrapper", "sample_wrapper"}
        or str(row.get("closure_role") or "").strip().lower() == "exact_sample_top"
        for row in root_rows
    ):
        errors.append("identity simulation closure root does not identify the exact sample-project wrapper")

    fingerprint = source_closure_fingerprint(rows)
    declared_fingerprint = str(
        identity.get("selected_simulation_source_closure_sha256")
        or metadata.get("closure_sha256")
        or ""
    ).strip().lower()
    if declared_fingerprint != fingerprint:
        errors.append("identity.selected_simulation_source_closure_sha256 does not match the recursive closure")
    return rows, fingerprint, errors, {"source_count": len(rows), "root_source_ids": roots}


def _validate_compute_slot_abi(
    identity: dict[str, Any], evidence_ids: set[str]
) -> tuple[dict[str, Any], str, list[str]]:
    errors: list[str] = []
    abi = identity.get("compute_slot_abi")
    if not isinstance(abi, dict):
        return {}, "", ["identity.compute_slot_abi is missing"]
    for field in (
        "slot_module",
        "slot_instance_path",
        "replacement_module_identity",
        "replacement_instance_boundary",
    ):
        if not str(abi.get(field) or "").strip():
            errors.append(f"identity.compute_slot_abi.{field} is missing")
    if abi.get("replacement_module_identity") != abi.get("slot_module"):
        errors.append("identity.compute_slot_abi.replacement_module_identity must equal slot_module")
    if abi.get("replacement_instance_boundary") != abi.get("slot_instance_path"):
        errors.append("identity.compute_slot_abi.replacement_instance_boundary must equal slot_instance_path")
    if abi.get("status") != "pass":
        errors.append("identity.compute_slot_abi.status is not pass")
    if abi.get("all_required_ports_bound") is not True:
        errors.append("identity.compute_slot_abi.all_required_ports_bound is not true")
    if abi.get("no_behavioral_substitution") is not True:
        errors.append("identity.compute_slot_abi.no_behavioral_substitution is not true")
    replaced_source_ids = abi.get("replaced_source_ids")
    if (
        not isinstance(replaced_source_ids, list)
        or not replaced_source_ids
        or any(not str(value).strip() for value in replaced_source_ids)
        or len(set(map(str, replaced_source_ids))) != len(replaced_source_ids)
    ):
        errors.append("identity.compute_slot_abi.replaced_source_ids must be a non-empty unique list")
    _require_evidence_refs(abi.get("evidence_refs"), "identity.compute_slot_abi", evidence_ids, errors)

    ports = _as_rows(abi.get("required_ports"))
    bindings = _as_rows(abi.get("port_bindings"))
    if not ports:
        errors.append("identity.compute_slot_abi.required_ports is empty")
    port_ids: set[str] = set()
    port_contract: dict[str, tuple[str, int]] = {}
    for index, row in enumerate(ports):
        port_id = str(row.get("port_id") or "").strip()
        direction = str(row.get("direction") or "").strip().lower()
        width = row.get("width_bits")
        if not port_id or not str(row.get("name") or "").strip() or not str(row.get("semantic_role") or "").strip():
            errors.append(f"identity.compute_slot_abi.required_ports[{index}] lacks port_id/name/semantic_role")
        if direction not in {"input", "output", "inout"}:
            errors.append(f"identity.compute_slot_abi.required_ports[{index}].direction is invalid")
        if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
            errors.append(f"identity.compute_slot_abi.required_ports[{index}].width_bits must be positive")
        if port_id in port_ids:
            errors.append(f"identity.compute_slot_abi has duplicate required port_id: {port_id}")
        _require_evidence_refs(
            row.get("evidence_refs"),
            f"identity.compute_slot_abi.required_ports[{index}]",
            evidence_ids,
            errors,
        )
        if port_id:
            port_ids.add(port_id)
            if direction in {"input", "output", "inout"} and isinstance(width, int):
                port_contract[port_id] = (direction, width)

    bound_ids: set[str] = set()
    for index, row in enumerate(bindings):
        port_id = str(row.get("port_id") or "").strip()
        accelerator_port = str(row.get("accelerator_port") or "").strip()
        if not accelerator_port:
            errors.append(f"identity.compute_slot_abi.port_bindings[{index}].accelerator_port is missing")
        if port_id not in port_ids:
            errors.append(f"identity.compute_slot_abi.port_bindings[{index}] references unknown port_id: {port_id}")
            continue
        if port_id in bound_ids:
            errors.append(f"identity.compute_slot_abi has duplicate binding for port_id: {port_id}")
        bound_ids.add(port_id)
        expected = port_contract.get(port_id)
        actual = (str(row.get("direction") or "").lower(), row.get("width_bits"))
        if expected and actual != expected:
            errors.append(f"identity.compute_slot_abi binding direction/width mismatch for port_id: {port_id}")
        _require_evidence_refs(
            row.get("evidence_refs"),
            f"identity.compute_slot_abi.port_bindings[{index}]",
            evidence_ids,
            errors,
        )
    if bound_ids != port_ids:
        errors.append(f"identity.compute_slot_abi port binding coverage mismatch: missing={sorted(port_ids - bound_ids)}")

    control = abi.get("control_abi")
    if not isinstance(control, dict):
        errors.append("identity.compute_slot_abi.control_abi is missing")
    else:
        _require_evidence_refs(
            control.get("evidence_refs"),
            "identity.compute_slot_abi.control_abi",
            evidence_ids,
            errors,
        )
        if not str(control.get("clock_domain") or "").strip():
            errors.append("identity.compute_slot_abi.control_abi.clock_domain is missing")
        fields = _as_rows(control.get("configuration_fields"))
        if not fields:
            errors.append("identity.compute_slot_abi.control_abi.configuration_fields is empty")
        occupied: dict[str, set[int]] = {}
        field_ids: set[str] = set()
        for index, row in enumerate(fields):
            label = f"identity.compute_slot_abi.control_abi.configuration_fields[{index}]"
            field_id = str(row.get("field_id") or "").strip()
            register = str(row.get("register") or "").strip()
            width = row.get("width_bits")
            offset = row.get("bit_offset")
            if not field_id or field_id in field_ids:
                errors.append(f"{label}.field_id is missing or duplicated")
            field_ids.add(field_id)
            if not register:
                errors.append(f"{label}.register is missing")
            if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
                errors.append(f"{label}.width_bits must be positive")
            if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
                errors.append(f"{label}.bit_offset must be non-negative")
            if str(row.get("access") or "").lower() not in {"ro", "rw", "wo"}:
                errors.append(f"{label}.access must be ro/rw/wo")
            if "reset_value" not in row:
                errors.append(f"{label}.reset_value is missing")
            if register and isinstance(width, int) and width > 0 and isinstance(offset, int) and offset >= 0:
                bits = set(range(offset, offset + width))
                if bits & occupied.setdefault(register, set()):
                    errors.append(f"{label} overlaps another bitfield in register {register}")
                occupied[register].update(bits)
            _require_evidence_refs(row.get("evidence_refs"), label, evidence_ids, errors)

        signals = control.get("signals")
        required_control_signals = {"valid", "done", "start", "clear", "count", "status"}
        if not isinstance(signals, dict):
            errors.append("identity.compute_slot_abi.control_abi.signals is missing")
            signals = {}
        semantic_options = {
            "valid": {"pulse", "level"},
            "done": {"pulse", "level", "counter_nonzero", "status_predicate"},
            "start": {"pulse", "level"},
            "clear": {"pulse", "level"},
            "count": {"counter"},
            "status": {"status"},
        }
        for name in sorted(required_control_signals):
            row = signals.get(name)
            label = f"identity.compute_slot_abi.control_abi.signals.{name}"
            if not isinstance(row, dict):
                errors.append(f"{label} is missing")
                continue
            if not str(row.get("name") or "").strip():
                errors.append(f"{label}.name is missing")
            if str(row.get("direction") or "").lower() not in {"input", "output", "inout"}:
                errors.append(f"{label}.direction is invalid")
            if not isinstance(row.get("width_bits"), int) or row.get("width_bits", 0) <= 0:
                errors.append(f"{label}.width_bits must be positive")
            if str(row.get("semantic") or "").lower() not in semantic_options[name]:
                errors.append(f"{label}.semantic is invalid for {name}")
            binding_kind = str(row.get("binding_kind") or "physical_port")
            if binding_kind not in {"physical_port", "derived_from_physical_port"}:
                errors.append(f"{label}.binding_kind is invalid")
            if binding_kind == "derived_from_physical_port":
                source_role = str(row.get("derived_from_role") or "")
                source = signals.get(source_role)
                if name != "done" or source_role not in {"count", "status"} or not isinstance(source, dict):
                    errors.append(f"{label}.derived_from_role is invalid")
                elif (
                    str(source.get("binding_kind") or "physical_port") != "physical_port"
                    or source.get("fact_port_id") != row.get("fact_port_id")
                ):
                    errors.append(f"{label} is not bound to its declared physical source role")
                if not str(row.get("predicate") or "").strip():
                    errors.append(f"{label}.predicate is missing")
            if str(row.get("clock_domain") or "") != str(control.get("clock_domain") or ""):
                errors.append(f"{label}.clock_domain differs from control_abi.clock_domain")
            matching_ports = [
                port
                for port in ports
                if str(port.get("name") or "") == str(row.get("name") or "")
                and str(port.get("direction") or "").lower() == str(row.get("direction") or "").lower()
                and port.get("width_bits") == row.get("width_bits")
            ]
            if len(matching_ports) != 1:
                errors.append(f"{label} is not exactly represented in compute_slot_abi.required_ports")
            _require_evidence_refs(row.get("evidence_refs"), label, evidence_ids, errors)

        timing = control.get("timing")
        if not isinstance(timing, dict):
            errors.append("identity.compute_slot_abi.control_abi.timing is missing")
        else:
            for field in ("start_assertion_cycles", "clear_assertion_cycles"):
                if not isinstance(timing.get(field), int) or timing.get(field, 0) <= 0:
                    errors.append(f"identity.compute_slot_abi.control_abi.timing.{field} must be positive")
            for field in ("start_sampling_edge", "clear_sampling_edge"):
                if str(timing.get(field) or "").lower() not in {"rising", "falling"}:
                    errors.append(f"identity.compute_slot_abi.control_abi.timing.{field} is invalid")
            for field in (
                "start_accept_condition",
                "done_relation_to_valid",
                "done_clear_condition",
                "count_update_event",
                "status_update_event",
            ):
                if not str(timing.get(field) or "").strip():
                    errors.append(f"identity.compute_slot_abi.control_abi.timing.{field} is missing")
            _require_evidence_refs(
                timing.get("evidence_refs"),
                "identity.compute_slot_abi.control_abi.timing",
                evidence_ids,
                errors,
            )

    fingerprint = canonical_contract_sha256(abi)
    if str(identity.get("compute_slot_abi_sha256") or "").lower() != fingerprint:
        errors.append("identity.compute_slot_abi_sha256 does not match compute_slot_abi")
    return abi, fingerprint, errors


def _validate_timing_contract(
    identity: dict[str, Any], closure_source_ids: set[str], evidence_ids: set[str], abi: dict[str, Any]
) -> tuple[dict[str, Any], str, list[str]]:
    errors: list[str] = []
    timing = identity.get("timing_contract")
    if not isinstance(timing, dict):
        return {}, "", ["identity.timing_contract is missing"]
    if timing.get("exact_sample_timing") is not True:
        errors.append("identity.timing_contract.exact_sample_timing is not true")
    if not str(timing.get("timescale") or "").strip() or not str(timing.get("timeprecision") or "").strip():
        errors.append("identity.timing_contract timescale/timeprecision are missing")

    clocks = _as_rows(timing.get("clock_domains"))
    clock_names: set[str] = set()
    if not clocks:
        errors.append("identity.timing_contract.clock_domains is empty")
    for index, row in enumerate(clocks):
        name = str(row.get("name") or "").strip()
        if not name:
            errors.append(f"identity.timing_contract.clock_domains[{index}].name is missing")
        if not isinstance(row.get("period_ps"), int) or row.get("period_ps", 0) <= 0:
            errors.append(f"identity.timing_contract.clock_domains[{index}].period_ps must be positive")
        duty = row.get("duty_cycle_percent")
        if not isinstance(duty, (int, float)) or isinstance(duty, bool) or not 0 < duty < 100:
            errors.append(f"identity.timing_contract.clock_domains[{index}].duty_cycle_percent is invalid")
        if not isinstance(row.get("phase_ps"), int) or row.get("phase_ps", -1) < 0:
            errors.append(f"identity.timing_contract.clock_domains[{index}].phase_ps is invalid")
        if str(row.get("source") or "").lower() not in {"exact_sample_project", "exact_sample_ip"}:
            errors.append(f"identity.timing_contract.clock_domains[{index}] is not sourced from the exact sample project")
        if name:
            clock_names.add(name)
        _require_evidence_refs(row.get("evidence_refs"), f"identity.timing_contract.clock_domains[{index}]", evidence_ids, errors)
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    if str(control.get("clock_domain") or "") not in clock_names:
        errors.append("identity.compute_slot_abi.control_abi.clock_domain is not a timing_contract clock domain")

    resets = _as_rows(timing.get("resets"))
    reset_names: set[str] = set()
    if not resets:
        errors.append("identity.timing_contract.resets is empty")
    for index, row in enumerate(resets):
        name = str(row.get("name") or "").strip()
        if row.get("active_level") not in {0, 1}:
            errors.append(f"identity.timing_contract.resets[{index}].active_level must be 0 or 1")
        if str(row.get("clock_domain") or "") not in clock_names:
            errors.append(f"identity.timing_contract.resets[{index}] references an unknown clock_domain")
        if not isinstance(row.get("minimum_assert_cycles"), int) or row.get("minimum_assert_cycles", 0) <= 0:
            errors.append(f"identity.timing_contract.resets[{index}].minimum_assert_cycles must be positive")
        if str(row.get("deassertion_edge") or "").lower() not in {"rising", "falling"}:
            errors.append(f"identity.timing_contract.resets[{index}].deassertion_edge is invalid")
        if str(row.get("source") or "").lower() not in {"exact_sample_project", "exact_sample_ip"}:
            errors.append(f"identity.timing_contract.resets[{index}] is not sourced from the exact sample project")
        if not name:
            errors.append(f"identity.timing_contract.resets[{index}].name is missing")
        else:
            reset_names.add(name)
        _require_evidence_refs(row.get("evidence_refs"), f"identity.timing_contract.resets[{index}]", evidence_ids, errors)

    calibration = _as_rows(timing.get("calibration"))
    calibration_names: set[str] = set()
    if not calibration:
        errors.append("identity.timing_contract.calibration is empty")
    for index, row in enumerate(calibration):
        name = str(row.get("name") or "").strip()
        if row.get("active_level") not in {0, 1}:
            errors.append(f"identity.timing_contract.calibration[{index}].active_level must be 0 or 1")
        if str(row.get("clock_domain") or "") not in clock_names:
            errors.append(f"identity.timing_contract.calibration[{index}] references an unknown clock_domain")
        if row.get("gates_axi_traffic") is not True:
            errors.append(f"identity.timing_contract.calibration[{index}].gates_axi_traffic is not true")
        if str(row.get("source") or "").lower() not in {"exact_sample_memory_model", "exact_sample_ip"}:
            errors.append(f"identity.timing_contract.calibration[{index}] is not driven by the exact sample memory model")
        if not name:
            errors.append(f"identity.timing_contract.calibration[{index}].name is missing")
        else:
            calibration_names.add(name)
        _require_evidence_refs(row.get("evidence_refs"), f"identity.timing_contract.calibration[{index}]", evidence_ids, errors)

    sequence = _as_rows(timing.get("startup_sequence"))
    events = [str(row.get("event") or "").strip() for row in sequence]
    required_events = {"assert_reset", "release_reset", "wait_calibration", "enable_axi_traffic"}
    if not required_events.issubset(set(events)):
        errors.append(f"identity.timing_contract.startup_sequence lacks events: {sorted(required_events - set(events))}")
    orders = [row.get("order") for row in sequence]
    if not orders or any(not isinstance(value, int) for value in orders) or orders != sorted(set(orders)):
        errors.append("identity.timing_contract.startup_sequence order is missing, duplicated, or non-monotonic")
    for index, row in enumerate(sequence):
        _require_evidence_refs(row.get("evidence_refs"), f"identity.timing_contract.startup_sequence[{index}]", evidence_ids, errors)

    memory = timing.get("memory_timing_model")
    if not isinstance(memory, dict):
        errors.append("identity.timing_contract.memory_timing_model is missing")
    else:
        source_ids = {str(value) for value in memory.get("source_ids", []) if str(value)}
        if not source_ids or not source_ids.issubset(closure_source_ids):
            errors.append("identity.timing_contract.memory_timing_model source_ids are not bound to the simulation closure")
        if memory.get("parameters_bound_from_sample_project") is not True:
            errors.append("identity.timing_contract.memory_timing_model is not parameter-bound from the sample project")
        if memory.get("synthetic_fixed_latency") is not False:
            errors.append("identity.timing_contract.memory_timing_model permits a synthetic fixed-latency replacement")
        _require_evidence_refs(
            memory.get("evidence_refs"),
            "identity.timing_contract.memory_timing_model",
            evidence_ids,
            errors,
        )

    fingerprint = canonical_contract_sha256(timing)
    if str(identity.get("timing_contract_sha256") or "").lower() != fingerprint:
        errors.append("identity.timing_contract_sha256 does not match timing_contract")
    timing["_validated_clock_names"] = sorted(clock_names)
    timing["_validated_reset_names"] = sorted(reset_names)
    timing["_validated_calibration_names"] = sorted(calibration_names)
    return timing, fingerprint, errors


def _valid_signal(value: Any, width: int) -> bool:
    if width == 0:
        return value is None or value == ""
    return isinstance(value, str) and bool(value.strip())


def _safe_relative_output_path(value: Any) -> bool:
    path = Path(str(value or ""))
    return bool(path.name) and not path.is_absolute() and ".." not in path.parts


def _unsafe_command_text(value: str) -> bool:
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return True
    if any(char in value for char in ";|&<>`"):
        return True
    return "$(" in value or "${" in value


def _contains_absolute_path_fragment(value: str) -> bool:
    if re.fullmatch(
        r"-timescale=[0-9]+(?:s|ms|us|ns|ps|fs)/[0-9]+(?:s|ms|us|ns|ps|fs)",
        value,
    ):
        return False
    if Path(value).is_absolute():
        return True
    if value.startswith("-") and "/" in value:
        return True
    return re.search(r"(?:^|[+=,:@])/(?!/)", value) is not None


def _safe_compile_cwd(value: Any) -> bool:
    if not isinstance(value, str) or not value or _unsafe_command_text(value):
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _normalized_authority_shell_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    logical_text = text.replace("\\\r\n", " ").replace("\\\n", " ")
    for line in logical_text.splitlines():
        try:
            tokens.update(shlex.split(line, comments=True, posix=True))
        except ValueError:
            continue
    return tokens


def _authority_contains_token(
    contexts: dict[str, str],
    refs: set[str],
    token: str,
    normalized_tokens: dict[str, set[str]] | None = None,
) -> bool:
    pattern = re.compile(
        rf"(?:^|[\s'\"=]){re.escape(token)}(?:$|[\s'\"\\])",
        flags=re.MULTILINE,
    )
    return any(
        pattern.search(contexts.get(ref, "")) is not None
        or (
            isinstance(normalized_tokens, dict)
            and token in normalized_tokens.get(ref, set())
        )
        for ref in refs
    )


def _normalized_physical_direction(value: Any) -> str:
    direction = str(value or "").strip().lower().replace("/", "")
    if direction in {"i", "in", "input"}:
        return "input"
    if direction in {"o", "out", "output"}:
        return "output"
    if direction in {"io", "inout"}:
        return "inout"
    return ""


def _provider_pin_binding(
    row: dict[str, Any], label: str, errors: list[str]
) -> dict[str, Any]:
    properties = row.get("properties") if isinstance(row.get("properties"), dict) else {}
    object_id = str(row.get("object_id") or "").strip()
    path = str(row.get("path") or "").strip()
    direction = _normalized_physical_direction(row.get("direction") or properties.get("DIR"))
    width = row.get("width_bits")
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        left, right = properties.get("LEFT"), properties.get("RIGHT")
        if left in (None, "") and right in (None, ""):
            width = 1
        else:
            try:
                width = abs(int(left) - int(right)) + 1
            except (TypeError, ValueError):
                width = 0
    if not object_id or not path or not direction or not isinstance(width, int) or width <= 0:
        errors.append(f"{label} lacks structured object_id/path/width/direction")
    return {
        "object_id": object_id,
        "path": path,
        "width_bits": width,
        "direction": direction,
    }


def _declared_physical_bindings(
    value: Any,
    label: str,
    timing_clock_names: set[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a non-empty list")
        return []
    normalized: list[dict[str, Any]] = []
    common_fields = {
        "object_id",
        "path",
        "width_bits",
        "direction",
        "sample_top_port",
        "binding_role",
    }
    for index, row in enumerate(value):
        row_label = f"{label}[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{row_label} is not an object")
            continue
        binding = _provider_pin_binding(row, row_label, errors)
        sample_top_port = str(row.get("sample_top_port") or "").strip()
        binding_role = str(row.get("binding_role") or "").strip()
        if not sample_top_port:
            errors.append(f"{row_label}.sample_top_port is missing")
        binding.update(
            {
                "sample_top_port": sample_top_port,
                "binding_role": binding_role,
            }
        )
        if binding_role == "external_memory_component":
            if set(row) != common_fields | {"target_port"}:
                errors.append(
                    f"{row_label} memory binding must contain target_port and no timing_clock_name"
                )
            target_port = str(row.get("target_port") or "").strip()
            if not target_port:
                errors.append(f"{row_label}.target_port is missing")
            binding["target_port"] = target_port
        elif binding_role == "exact_timing_clock_driver":
            if set(row) != common_fields | {"timing_clock_name"}:
                errors.append(
                    f"{row_label} timing-clock binding must contain timing_clock_name and no target_port"
                )
            timing_clock_name = str(row.get("timing_clock_name") or "").strip()
            if not timing_clock_name or timing_clock_name not in timing_clock_names:
                errors.append(
                    f"{row_label}.timing_clock_name is not an identity timing clock domain"
                )
            binding["timing_clock_name"] = timing_clock_name
        else:
            errors.append(f"{row_label}.binding_role is unsupported")
        normalized.append(binding)
    keys = [(row["object_id"], row["path"]) for row in normalized]
    if len(keys) != len(set(keys)):
        errors.append(f"{label} contains duplicate physical pin bindings")
    return sorted(normalized, key=lambda row: (row["object_id"], row["path"]))


def _validate_external_simulation_fixture(
    simulation: dict[str, Any], simulation_path: Path, identity: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Validate the selected vendor fixture without interpreting provider names."""

    errors: list[str] = []
    reference = simulation.get("external_simulation_fixture")
    if not isinstance(reference, dict):
        return {}, ["simulation.external_simulation_fixture is missing"]
    before = len(errors)
    _verified_artifact(
        reference,
        simulation_path,
        "simulation.external_simulation_fixture",
        "path",
        errors,
    )
    path_text = str(reference.get("path") or "")
    fixture_path = _resolve_path(path_text, simulation_path) if path_text else simulation_path
    fixture: dict[str, Any] = {}
    if len(errors) == before:
        fixture, load_errors = _load_json_object(fixture_path, "external simulation fixture")
        errors.extend(load_errors)
    if fixture.get("status") != "pass":
        errors.append("external simulation fixture status is not pass")
    if fixture.get("blockers") not in ([], None):
        errors.append("external simulation fixture contains blockers")
    expected_contract_sha256 = canonical_contract_sha256(
        {
            key: value
            for key, value in fixture.items()
            if key not in {"contract_sha256", "cache_reused"}
        }
    ) if fixture else ""
    fixture_contract_sha256 = str(fixture.get("contract_sha256") or "").lower()
    if (
        not expected_contract_sha256
        or fixture_contract_sha256 != expected_contract_sha256
        or str(reference.get("contract_sha256") or "").lower() != expected_contract_sha256
    ):
        errors.append("external simulation fixture contract_sha256 is stale or unbound")

    authority = fixture.get("authority") if isinstance(fixture.get("authority"), dict) else {}
    authority_sha256 = str(authority.get("authority_sha256") or "").lower()
    if (
        not authority
        or authority_sha256 != _self_contract_sha256(authority, "authority_sha256")
        or str(fixture.get("authority_sha256") or "").lower() != authority_sha256
    ):
        errors.append("external simulation fixture authority hash is stale or unbound")

    compile_authority = (
        fixture.get("compile_authority")
        if isinstance(fixture.get("compile_authority"), dict)
        else {}
    )
    if compile_authority.get("status") != "pass":
        errors.append("external simulation fixture compile_authority status is not pass")
    if str(compile_authority.get("compile_authority_sha256") or "").lower() != (
        _self_contract_sha256(compile_authority, "compile_authority_sha256")
        if compile_authority else ""
    ):
        errors.append("external simulation fixture compile_authority hash is stale")
    provider_groups = _as_rows(authority.get("provider_groups"))
    if str(compile_authority.get("provider_groups_sha256") or "").lower() != canonical_contract_sha256(
        provider_groups
    ):
        errors.append("external simulation fixture compile authority does not bind provider groups")

    compile_sources = _as_rows(compile_authority.get("compile_sources"))
    source_ids = [_source_id(row) for row in compile_sources]
    if not source_ids or any(not value for value in source_ids) or len(source_ids) != len(set(source_ids)):
        errors.append("external simulation fixture compile_sources have missing or duplicate source IDs")
    source_by_id = {_source_id(row): row for row in compile_sources if _source_id(row)}
    selected = reference.get("selected_source_ids")
    selected_ids = [str(value) for value in selected] if isinstance(selected, list) else []
    if (
        not selected_ids
        or any(not value for value in selected_ids)
        or len(selected_ids) != len(set(selected_ids))
        or not set(selected_ids).issubset(source_by_id)
    ):
        errors.append("external simulation fixture selected_source_ids are not exact compile-authority IDs")
    elif selected_ids != [value for value in source_ids if value in set(selected_ids)]:
        errors.append("external simulation fixture selected_source_ids do not preserve compile-authority order")
    for source_id in selected_ids:
        row = source_by_id.get(source_id)
        if row is not None:
            _verified_source_file(
                row,
                fixture_path,
                f"external simulation fixture compile source {source_id}",
                errors,
            )

    contexts_by_hash: dict[str, str] = {}
    contexts = _as_rows(compile_authority.get("export_contexts"))
    if not contexts:
        errors.append("external simulation fixture compile authority has no export contexts")
    for index, row in enumerate(contexts):
        label = f"external simulation fixture export_contexts[{index}]"
        text = row.get("text")
        digest = str(row.get("sha256") or "").lower()
        if not isinstance(text, str) or not text or hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
            errors.append(f"{label} text/hash binding is invalid")
            continue
        if digest in contexts_by_hash:
            errors.append(f"external simulation fixture export contexts repeat hash: {digest}")
            continue
        contexts_by_hash[digest] = text

    portable_fixture = str(compile_authority.get("schema_version") or "").endswith(
        ".v2"
    )
    portable_fields = (
        "runtime_auxiliary_files",
        "include_directories",
        "synopsys_sim_setup",
    )
    for field in portable_fields:
        expected = compile_authority.get(field)
        declared = reference.get(field)
        if declared != expected:
            errors.append(
                f"simulation.external_simulation_fixture.{field} differs from compile authority"
            )

    materialized_rows = _as_rows(fixture.get("materialized_files"))
    materialized_by_source_id = {
        _source_id(row): row for row in materialized_rows if _source_id(row)
    }
    runtime_auxiliary = _as_rows(
        compile_authority.get("runtime_auxiliary_files")
    )
    for index, row in enumerate(runtime_auxiliary):
        _verified_source_file(
            row,
            fixture_path,
            f"external simulation fixture runtime_auxiliary_files[{index}]",
            errors,
        )

    include_directories = _as_rows(compile_authority.get("include_directories"))
    include_directory_ids: list[str] = []
    for index, row in enumerate(include_directories):
        label = f"external simulation fixture include_directories[{index}]"
        include_id = str(row.get("include_dir_id") or "")
        staged_path = str(row.get("staged_path") or "")
        member_ids = row.get("member_source_ids")
        member_ids = [str(value) for value in member_ids] if isinstance(member_ids, list) else []
        if not include_id or include_id in include_directory_ids:
            errors.append(f"{label}.include_dir_id is missing or duplicate")
        if not _safe_relative_output_path(staged_path):
            errors.append(f"{label}.staged_path is unsafe")
        if (
            not member_ids
            or len(member_ids) != len(set(member_ids))
            or not set(member_ids).issubset(materialized_by_source_id)
        ):
            errors.append(f"{label}.member_source_ids are missing, duplicate, or unknown")
        else:
            for member_id in member_ids:
                _verified_source_file(
                    materialized_by_source_id[member_id],
                    fixture_path,
                    f"{label} member {member_id}",
                    errors,
                )
        include_directory_ids.append(include_id)
    if portable_fixture and not include_directories:
        errors.append("external simulation fixture v2 has no portable include directories")

    setup = (
        compile_authority.get("synopsys_sim_setup")
        if isinstance(compile_authority.get("synopsys_sim_setup"), dict)
        else {}
    )
    if portable_fixture:
        if setup.get("status") != "pass":
            errors.append("external simulation fixture v2 synopsys setup is not pass")
        _verified_source_file(
            {**setup, "source_id": setup.get("source_id") or "synopsys_sim_setup"},
            fixture_path,
            "external simulation fixture synopsys_sim_setup",
            errors,
        )
        expected_setup_sha = _self_contract_sha256(
            setup, "setup_authority_sha256"
        )
        if str(setup.get("setup_authority_sha256") or "").lower() != expected_setup_sha:
            errors.append("external simulation fixture synopsys setup authority hash is stale")
        for index, row in enumerate(_as_rows(setup.get("files"))):
            _verified_source_file(
                {**row, "source_id": row.get("source_id") or f"setup_file_{index}"},
                fixture_path,
                f"external simulation fixture synopsys setup file[{index}]",
                errors,
            )

    model_instance = reference.get("model_instance")
    if not isinstance(model_instance, dict):
        model_instance = {}
        errors.append("simulation.external_simulation_fixture.model_instance is missing")
    elif set(model_instance) != {"module", "source_id", "physical_port_bindings"}:
        errors.append("external simulation fixture model_instance has unsupported or missing fields")
    module = str(model_instance.get("module") or "").strip()
    model_source_id = str(model_instance.get("source_id") or "").strip()
    if not module or model_source_id not in selected_ids:
        errors.append("external simulation fixture model_instance does not bind a selected source/module")

    expected_bindings: list[dict[str, Any]] = []
    model_source = source_by_id.get(model_source_id, {})
    provider_configuration = str(model_source.get("provider_configuration_sha256") or "")
    matching_groups = [
        row
        for row in provider_groups
        if str(row.get("configuration_sha256") or "") == provider_configuration
    ]
    if len(matching_groups) != 1:
        errors.append("external simulation fixture model source does not select one provider group")
    else:
        representative = matching_groups[0].get("representative")
        representative = representative if isinstance(representative, dict) else {}
        pins = [
            pin
            for interface in _as_rows(representative.get("external_interfaces"))
            for pin in _as_rows(interface.get("provider_member_pins"))
        ]
        if not pins:
            errors.append("external simulation fixture provider has no physical member pins")
        expected_bindings = sorted(
            [
                _provider_pin_binding(
                    pin,
                    f"external simulation fixture provider_member_pins[{index}]",
                    errors,
                )
                for index, pin in enumerate(pins)
            ],
            key=lambda row: (row["object_id"], row["path"]),
        )
        keys = [(row["object_id"], row["path"]) for row in expected_bindings]
        if len(keys) != len(set(keys)):
            errors.append("external simulation fixture provider repeats a physical member pin")
    timing = identity.get("timing_contract")
    timing = timing if isinstance(timing, dict) else {}
    timing_clock_names = {
        str(row.get("name") or "")
        for row in _as_rows(timing.get("clock_domains"))
        if str(row.get("name") or "")
    }
    declared_bindings = _declared_physical_bindings(
        model_instance.get("physical_port_bindings"),
        "simulation.external_simulation_fixture.model_instance.physical_port_bindings",
        timing_clock_names,
        errors,
    )
    declared_provider_pins = [
        {
            key: row.get(key)
            for key in ("object_id", "path", "width_bits", "direction")
        }
        for row in declared_bindings
    ]
    if expected_bindings != declared_provider_pins:
        errors.append("external simulation fixture physical_port_bindings do not exactly cover provider pins")

    testbench = simulation.get("testbench") if isinstance(simulation.get("testbench"), dict) else {}
    if str(testbench.get("external_simulation_fixture_contract_sha256") or "").lower() != expected_contract_sha256:
        errors.append("simulation.testbench does not bind the external fixture contract hash")
    if testbench.get("external_memory_component") != model_instance:
        errors.append("simulation.testbench does not bind the exact external memory component")

    return {
        "path": str(fixture_path),
        "contract_sha256": expected_contract_sha256,
        "selected_source_ids": selected_ids,
        "source_by_id": source_by_id,
        "model_instance": model_instance,
        "physical_port_bindings": declared_bindings,
        "export_contexts_by_hash": contexts_by_hash,
        "include_directory_ids": include_directory_ids,
        "include_directories": include_directories,
        "runtime_auxiliary_files": runtime_auxiliary,
        "synopsys_sim_setup": setup,
        "vivado_tool": dict(authority.get("vivado_tool", {}))
        if isinstance(authority.get("vivado_tool"), dict)
        else {},
    }, errors


def _candidate_tool_profiles(
    identity_path: Path, simulation_path: Path, facts_path: Path | None
) -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()
    anchors = [simulation_path.parent, identity_path.parent]
    if facts_path is not None:
        anchors.append(facts_path.parent)
    for anchor in anchors:
        for parent in (anchor, *anchor.parents):
            candidate = (parent / "input" / "tool_profile.json").resolve()
            if candidate not in seen and candidate.is_file():
                seen.add(candidate)
                candidates.append(candidate)
    return candidates


def _validate_vcs_compile_plan(
    simulation: dict[str, Any],
    simulation_path: Path,
    identity: dict[str, Any],
    identity_path: Path,
    compile_details: dict[str, Any],
    external_fixture: dict[str, Any],
    frozen_identity_attestation_valid: bool = False,
) -> tuple[str, list[str], dict[str, Any]]:
    """Validate the immutable, no-shell Vivado-authorized VCS execution plan."""

    errors: list[str] = []
    compute_slot_axi = _is_compute_slot_axi_validation(simulation)
    raw_plan = simulation.get("vcs_compile_plan")
    if not isinstance(raw_plan, dict):
        return "", ["simulation.vcs_compile_plan is missing"], {}
    plan = raw_plan
    plan_sha256 = canonical_contract_sha256(plan)
    if str(simulation.get("vcs_compile_plan_sha256") or "").lower() != plan_sha256:
        errors.append("simulation.vcs_compile_plan_sha256 does not match the complete canonical plan")
    unknown_plan_fields = sorted(set(plan) - VCS_PLAN_FIELDS)
    if unknown_plan_fields:
        errors.append(f"simulation.vcs_compile_plan contains unsupported fields: {unknown_plan_fields}")
    if plan.get("schema_version") != VCS_COMPILE_PLAN_SCHEMA_VERSION:
        errors.append("simulation.vcs_compile_plan.schema_version is missing or unsupported")
    if plan.get("status") != "ready":
        errors.append("simulation.vcs_compile_plan.status is not ready")

    facts_path_text = str(identity.get("vivado_facts_path") or "")
    facts_path = _resolve_path(facts_path_text, identity_path) if facts_path_text else None
    identity_facts_sha256 = str(identity.get("vivado_facts_sha256") or "").lower()
    frozen_attestation = (
        simulation.get("frozen_compute_slot_identity_attestation")
        if frozen_identity_attestation_valid
        and isinstance(
            simulation.get("frozen_compute_slot_identity_attestation"), dict
        )
        else {}
    )
    frozen_context_hashes = {
        str(value).lower()
        for value in frozen_attestation.get(
            "attested_simulator_export_context_sha256s", []
        )
        if isinstance(value, str)
    }
    facts: dict[str, Any] = {}
    context_by_hash: dict[str, str] = {}
    if frozen_identity_attestation_valid:
        # The certificate validator above hash-binds the replaced live sidecar
        # and the prior export-authority snapshots.  Do not reinterpret the
        # replacement as the authority for the already certified plan.
        pass
    elif facts_path is None or not facts_path.is_file():
        errors.append("identity.vivado_facts_path does not resolve to the current Vivado fact bundle")
    else:
        facts, load_errors = _load_json_object(facts_path, "identity Vivado fact bundle")
        errors.extend(load_errors)
        actual_facts_sha256 = sha256_file(facts_path)
        if not identity_facts_sha256 or identity_facts_sha256 != actual_facts_sha256:
            errors.append("identity.vivado_facts_sha256 does not bind the current Vivado fact bundle bytes")
        simulation_facts = facts.get("simulation") if isinstance(facts.get("simulation"), dict) else {}
        export_contexts = simulation_facts.get("simulator_export_contexts")
        if not isinstance(export_contexts, list) or not export_contexts:
            errors.append("identity Vivado fact bundle has no simulator_export_contexts")
            export_contexts = []
        for index, row in enumerate(export_contexts):
            label = f"identity Vivado simulator_export_contexts[{index}]"
            if not isinstance(row, dict):
                errors.append(f"{label} is not an object")
                continue
            context_text = row.get("text")
            context_sha256 = str(row.get("sha256") or "").lower()
            if not isinstance(context_text, str) or not context_text:
                errors.append(f"{label}.text is empty")
                continue
            actual_context_sha256 = hashlib.sha256(context_text.encode("utf-8")).hexdigest()
            if context_sha256 != actual_context_sha256:
                errors.append(f"{label}.sha256 does not bind its command text")
                continue
            if context_sha256 in context_by_hash:
                errors.append(f"identity Vivado simulator_export_contexts has duplicate hash: {context_sha256}")
                continue
            context_by_hash[context_sha256] = context_text

    fixture_context_by_hash = external_fixture.get("export_contexts_by_hash", {})
    fixture_context_by_hash = (
        fixture_context_by_hash if isinstance(fixture_context_by_hash, dict) else {}
    )
    combined_context_by_hash = dict(context_by_hash)
    for digest, text in fixture_context_by_hash.items():
        if digest in combined_context_by_hash and combined_context_by_hash[digest] != text:
            errors.append(f"external fixture export context hash collides with different text: {digest}")
        combined_context_by_hash[digest] = text
    normalized_context_tokens_by_hash = {
        digest: _normalized_authority_shell_tokens(text)
        for digest, text in combined_context_by_hash.items()
    }

    authority = plan.get("compile_authority")
    declared_context_hashes: list[str] = []
    declared_fixture_context_hashes: list[str] = []
    if not isinstance(authority, dict):
        errors.append("simulation.vcs_compile_plan.compile_authority is missing")
    else:
        unknown_authority_fields = sorted(
            set(authority)
            - VCS_COMPILE_AUTHORITY_FIELDS
            - LEGACY_IGNORED_VCS_COMPILE_AUTHORITY_FIELDS
        )
        if unknown_authority_fields:
            errors.append(
                "simulation.vcs_compile_plan.compile_authority contains unsupported fields: "
                f"{unknown_authority_fields}"
            )
        raw_context_hashes = authority.get("simulator_export_context_sha256s")
        if (
            not isinstance(raw_context_hashes, list)
            or not raw_context_hashes
            or not all(
                isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
                for value in raw_context_hashes
            )
        ):
            errors.append(
                "simulation.vcs_compile_plan.compile_authority.simulator_export_context_sha256s is invalid"
            )
        else:
            declared_context_hashes = [value.lower() for value in raw_context_hashes]
            if len(declared_context_hashes) != len(set(declared_context_hashes)):
                errors.append("simulation.vcs_compile_plan compile authority repeats an export context hash")
        expected_context_hashes = (
            frozen_context_hashes
            if frozen_identity_attestation_valid
            else set(context_by_hash)
        )
        if (
            authority.get("vivado_facts_path") != facts_path_text
            or str(authority.get("vivado_facts_sha256") or "").lower() != identity_facts_sha256
            or set(declared_context_hashes) != expected_context_hashes
        ):
            errors.append(
                "simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts"
            )
        raw_fixture_context_hashes = authority.get(
            "external_fixture_export_context_sha256s"
        )
        if compute_slot_axi:
            if raw_fixture_context_hashes not in (None, []):
                errors.append(
                    "compute-slot AXI compile authority must not bind external fixture export contexts"
                )
            if authority.get("external_fixture_contract_sha256") not in (None, ""):
                errors.append(
                    "compute-slot AXI compile authority must not bind an external fixture contract"
                )
        else:
            if (
                not isinstance(raw_fixture_context_hashes, list)
                or not raw_fixture_context_hashes
                or not all(
                    isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
                    for value in raw_fixture_context_hashes
                )
            ):
                errors.append(
                    "simulation.vcs_compile_plan.compile_authority.external_fixture_export_context_sha256s is invalid"
                )
            else:
                declared_fixture_context_hashes = [
                    value.lower() for value in raw_fixture_context_hashes
                ]
                if len(declared_fixture_context_hashes) != len(
                    set(declared_fixture_context_hashes)
                ):
                    errors.append(
                        "simulation.vcs_compile_plan compile authority repeats an external fixture context hash"
                    )
            if (
                str(authority.get("external_fixture_contract_sha256") or "").lower()
                != str(external_fixture.get("contract_sha256") or "").lower()
                or set(declared_fixture_context_hashes) != set(fixture_context_by_hash)
            ):
                errors.append(
                    "simulation.vcs_compile_plan.compile_authority does not bind the exact external fixture export"
                )

    declared_tool_profile_sha256 = str(plan.get("tool_profile_sha256") or "").lower()
    if re.fullmatch(r"[0-9a-f]{64}", declared_tool_profile_sha256) is None:
        errors.append("simulation.vcs_compile_plan.tool_profile_sha256 is missing or invalid")
    profile_candidates = _candidate_tool_profiles(identity_path, simulation_path, facts_path)
    matching_profiles = [
        path
        for path in profile_candidates
        if declared_tool_profile_sha256 and sha256_file(path) == declared_tool_profile_sha256
    ]
    tool_profile_path = matching_profiles[0] if len(matching_profiles) == 1 else None
    if len(matching_profiles) != 1:
        errors.append(
            "simulation.vcs_compile_plan.tool_profile_sha256 does not uniquely bind the current run tool_profile"
        )
    tool_profile: dict[str, Any] = {}
    configured_tool: dict[str, Any] = {}
    if tool_profile_path is not None:
        tool_profile, load_errors = _load_json_object(tool_profile_path, "current tool profile")
        errors.extend(load_errors)
        configured_tools = [
            row
            for row in tool_profile.get("tools", [])
            if isinstance(row, dict) and row.get("role") == "functional_verification"
        ]
        if len(configured_tools) != 1:
            errors.append("current tool_profile must contain exactly one functional_verification tool")
        else:
            configured_tool = configured_tools[0]
            if str(configured_tool.get("name") or "").lower() != "vcs":
                errors.append("current functional_verification tool is not VCS")
            configured_driver = Path(str(configured_tool.get("executable") or "")).name.lower()
            if configured_driver != "vcs":
                errors.append("current functional_verification executable is not the VCS driver")

    planned_tool = plan.get("tool_binding")
    if not isinstance(planned_tool, dict):
        errors.append("simulation.vcs_compile_plan.tool_binding is missing")
        planned_tool = {}
    for field in ("role", "name", "host", "port", "executable"):
        if not configured_tool or planned_tool.get(field) != configured_tool.get(field):
            errors.append(
                f"simulation.vcs_compile_plan.tool_binding.{field} does not match current tool_profile"
            )
    fixture_tool = external_fixture.get("vivado_tool")
    fixture_tool = fixture_tool if isinstance(fixture_tool, dict) else {}
    if external_fixture.get("synopsys_sim_setup"):
        if (
            str(fixture_tool.get("host") or "")
            != str(configured_tool.get("host") or "")
            or int(fixture_tool.get("port") or 22)
            != int(configured_tool.get("port") or 22)
        ):
            errors.append(
                "external fixture simulator library map was not validated on the configured VCS host"
            )

    top_module = str(plan.get("top_module") or "")
    expected_top = str(simulation.get("top_module") or "")
    testbench = simulation.get("testbench") if isinstance(simulation.get("testbench"), dict) else {}
    if (
        not top_module
        or _unsafe_command_text(top_module)
        or top_module != expected_top
        or top_module != str(testbench.get("top_module") or "")
    ):
        errors.append("simulation.vcs_compile_plan.top_module does not bind the board testbench top")
    output = str(plan.get("output") or "")
    if output != "simv" or not _safe_relative_output_path(output):
        errors.append("simulation.vcs_compile_plan.output must be the safe simulator artifact simv")

    commands = plan.get("ordered_commands")
    if not isinstance(commands, list) or not commands:
        errors.append("simulation.vcs_compile_plan.ordered_commands is missing or empty")
        commands = []
    covered_source_ids: list[str] = []
    compile_indexes: list[int] = []
    elaboration_indexes: list[int] = []
    elaboration_literals: list[str] = []
    elaboration_driver = ""
    fixture_include_ids = {
        str(value)
        for value in external_fixture.get("include_directory_ids", [])
        if str(value)
    }
    for index, command in enumerate(commands):
        label = f"simulation.vcs_compile_plan.ordered_commands[{index}]"
        if not isinstance(command, dict):
            errors.append(f"{label} is not an object")
            continue
        unknown_command_fields = sorted(set(command) - VCS_COMMAND_FIELDS)
        if unknown_command_fields:
            errors.append(f"{label} contains unsupported fields: {unknown_command_fields}")
        order = command.get("order")
        if isinstance(order, bool) or order != index:
            errors.append(f"{label}.order is not the contiguous execution order")
        phase = str(command.get("phase") or "")
        if phase == "compile":
            compile_indexes.append(index)
        elif phase == "elaborate":
            elaboration_indexes.append(index)
        else:
            errors.append(f"{label}.phase is neither compile nor elaborate")
        if command.get("shell") is not False:
            errors.append(f"{label}.shell must be false")
        if command.get("tool_role") != str(configured_tool.get("role") or ""):
            errors.append(f"{label}.tool_role does not bind the current functional simulator")

        refs = command.get("authority_refs")
        ref_set: set[str] = set()
        if (
            not isinstance(refs, list)
            or not refs
            or not all(
                isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value)
                for value in refs
            )
        ):
            errors.append(f"{label}.authority_refs is empty or invalid")
        else:
            normalized_refs = [value.lower() for value in refs]
            ref_set = set(normalized_refs)
            authorized_context_hashes = (
                frozen_context_hashes | set(fixture_context_by_hash)
                if frozen_identity_attestation_valid
                else set(combined_context_by_hash)
            )
            if len(ref_set) != len(normalized_refs) or not ref_set.issubset(
                authorized_context_hashes
            ):
                errors.append(f"{label}.authority_refs do not bind exact Vivado export contexts")

        executable = command.get("executable")
        driver = ""
        if (
            not isinstance(executable, str)
            or not executable
            or _unsafe_command_text(executable)
            or any(char.isspace() for char in executable)
        ):
            errors.append(f"{label}.executable is missing or unsafe")
        else:
            driver = Path(executable).name.lower()
            if driver not in VCS_TOOL_DRIVERS:
                errors.append(f"{label}.executable is not a vcs/vlogan/vhdlan driver")
            if phase == "elaborate" and driver != "vcs":
                errors.append(f"{label} elaboration must use the vcs driver")
            configured_executable = str(configured_tool.get("executable") or "")
            if (
                executable != configured_executable
                and not frozen_identity_attestation_valid
                and not _authority_contains_token(
                    combined_context_by_hash,
                    ref_set,
                    executable,
                    normalized_context_tokens_by_hash,
                )
            ):
                errors.append(
                    f"{label}.executable is not authorized by current tool_profile or referenced Vivado export"
                )

        if not _safe_compile_cwd(command.get("cwd")):
            errors.append(f"{label}.cwd is not a safe relative staging directory")
        env = command.get("env")
        if not isinstance(env, dict):
            errors.append(f"{label}.env is not an object")
            env = {}
        else:
            for key, value in env.items():
                if (
                    not isinstance(key, str)
                    or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) is None
                    or not isinstance(value, str)
                    or _unsafe_command_text(value)
                ):
                    errors.append(f"{label}.env contains an unsafe name or value")
                    break
                if (
                    _contains_absolute_path_fragment(value)
                    and not frozen_identity_attestation_valid
                    and not any(
                        value in combined_context_by_hash.get(ref, "")
                        for ref in ref_set
                    )
                ):
                    errors.append(f"{label}.env contains an arbitrary absolute path")
                    break

        argv = command.get("argv")
        if not isinstance(argv, list) or not argv:
            errors.append(f"{label}.argv is missing or empty")
            argv = []
        token_source_ids: list[str] = []
        token_include_ids: list[str] = []
        literal_argv: list[str] = []
        for token_index, token in enumerate(argv):
            if isinstance(token, str):
                literal_argv.append(token)
                if not token or _unsafe_command_text(token):
                    errors.append(f"{label}.argv[{token_index}] is an unsafe literal token")
                elif (
                    _contains_absolute_path_fragment(token)
                    and not frozen_identity_attestation_valid
                    and not _authority_contains_token(
                        combined_context_by_hash,
                        ref_set,
                        token,
                        normalized_context_tokens_by_hash,
                    )
                ):
                    errors.append(f"{label}.argv[{token_index}] contains an arbitrary absolute path")
            elif isinstance(token, dict) and set(token) == {"source_id"}:
                source_id = token.get("source_id")
                if not isinstance(source_id, str) or not source_id:
                    errors.append(f"{label}.argv[{token_index}].source_id is missing")
                else:
                    token_source_ids.append(source_id)
            elif isinstance(token, dict) and set(token) == {"include_dir_id"}:
                include_dir_id = token.get("include_dir_id")
                if (
                    not isinstance(include_dir_id, str)
                    or not include_dir_id
                    or include_dir_id not in fixture_include_ids
                ):
                    errors.append(
                        f"{label}.argv[{token_index}].include_dir_id is not fixture-authorized"
                    )
                else:
                    token_include_ids.append(include_dir_id)
            else:
                errors.append(
                    f"{label}.argv[{token_index}] is not a literal, source_id, or include_dir_id token"
                )
        source_ids = command.get("source_ids")
        if not isinstance(source_ids, list) or source_ids != token_source_ids:
            errors.append(f"{label}.source_ids do not exactly match argv source tokens in order")
        if phase == "compile":
            if not token_source_ids:
                errors.append(f"{label} compile command has no source_id token")
            if set(token_source_ids).intersection(
                set(external_fixture.get("selected_source_ids", []))
            ) and not ref_set.intersection(fixture_context_by_hash):
                errors.append(
                    f"{label} external fixture sources are not bound to their export context"
                )
            covered_source_ids.extend(token_source_ids)
        elif phase == "elaborate":
            if token_source_ids:
                errors.append(f"{label} elaboration command must not contain source_id tokens")
            if token_include_ids:
                errors.append(
                    f"{label} elaboration command must not contain include_dir_id tokens"
                )
            elaboration_literals = literal_argv
            elaboration_driver = driver

    expected_compile_order = simulation.get("compile_source_ids")
    if not isinstance(expected_compile_order, list) or not all(
        isinstance(value, str) and value for value in expected_compile_order
    ):
        expected_compile_order = []
    verified_source_ids = set(compile_details.get("verified_compile_source_ids", []))
    replaced_source_ids = set(compile_details.get("replaced_sample_source_ids", []))
    if (
        len(covered_source_ids) != len(set(covered_source_ids))
        or set(covered_source_ids) != verified_source_ids
    ):
        errors.append(
            "simulation.vcs_compile_plan compile commands do not cover every transformed source ID exactly once"
        )
    if covered_source_ids != expected_compile_order:
        errors.append(
            "simulation.vcs_compile_plan compile source order does not exactly match simulation.compile_source_ids"
        )
    if set(covered_source_ids).intersection(replaced_source_ids):
        errors.append("simulation.vcs_compile_plan references a replaced sample-project source ID")
    if compile_indexes != list(range(max(len(commands) - 1, 0))):
        errors.append("simulation.vcs_compile_plan compile commands are not all before elaboration")
    if elaboration_indexes != [len(commands) - 1]:
        errors.append("simulation.vcs_compile_plan must end with exactly one elaboration command")
    else:
        if elaboration_driver != "vcs":
            errors.append("simulation.vcs_compile_plan final elaboration driver is not vcs")
        if top_module not in elaboration_literals:
            errors.append("simulation.vcs_compile_plan elaboration argv does not contain top_module")
        output_indexes = [
            index for index, value in enumerate(elaboration_literals) if value == "-o"
        ]
        if (
            len(output_indexes) != 1
            or output_indexes[0] + 1 >= len(elaboration_literals)
            or elaboration_literals[output_indexes[0] + 1] != output
        ):
            errors.append("simulation.vcs_compile_plan elaboration argv does not bind -o simv")
    if len(compile_indexes) == 1 and len(verified_source_ids) > 1:
        command = commands[compile_indexes[0]] if commands else {}
        literal_argv = [
            token for token in command.get("argv", []) if isinstance(token, str)
        ] if isinstance(command, dict) else []
        if command.get("executable") == configured_tool.get("executable") and "-sverilog" in literal_argv:
            errors.append(
                "simulation.vcs_compile_plan cannot replace Vivado export ordering with a collapsed -sverilog fallback"
            )

    return plan_sha256, errors, {
        "sha256": plan_sha256,
        "command_count": len(commands),
        "compile_source_count": len(covered_source_ids),
        "vivado_export_context_count": (
            len(frozen_context_hashes)
            if frozen_identity_attestation_valid
            else len(context_by_hash)
        ),
        "frozen_vivado_export_authority_reused": frozen_identity_attestation_valid,
        "external_fixture_export_context_count": len(fixture_context_by_hash),
        "tool_profile_path": str(tool_profile_path) if tool_profile_path is not None else None,
    }


def _validate_axi_contract(
    identity: dict[str, Any], timing: dict[str, Any], evidence_ids: set[str]
) -> tuple[list[dict[str, Any]], str, list[str]]:
    errors: list[str] = []
    interfaces = _as_rows(identity.get("axi_interfaces"))
    if not interfaces:
        return [], "", ["identity.axi_interfaces is empty"]
    names: set[str] = set()
    clocks = set(timing.get("_validated_clock_names", []))
    resets = set(timing.get("_validated_reset_names", []))
    calibration = set(timing.get("_validated_calibration_names", []))
    for index, row in enumerate(interfaces):
        label = f"identity.axi_interfaces[{index}]"
        name = str(row.get("name") or "").strip()
        if not name:
            errors.append(f"{label}.name is missing")
        elif name in names:
            errors.append(f"identity.axi_interfaces has duplicate name: {name}")
        names.add(name)
        if str(row.get("protocol") or "").upper() not in {"AXI4", "AXI4-FULL"}:
            errors.append(f"{label}.protocol must be full AXI4")
        if str(row.get("role") or "").lower() not in {"master", "slave"}:
            errors.append(f"{label}.role must be master or slave")
        if str(row.get("clock") or "") not in clocks:
            errors.append(f"{label}.clock is not a timing_contract clock domain")
        if str(row.get("reset") or "") not in resets:
            errors.append(f"{label}.reset is not a timing_contract reset")
        if str(row.get("calibration") or "") not in calibration:
            errors.append(f"{label}.calibration is not a timing_contract calibration gate")
        _require_evidence_refs(row.get("evidence_refs"), label, evidence_ids, errors)

        for field in sorted(AXI_WIDTH_FIELDS):
            value = row.get(field)
            allow_zero = field.endswith("user_width_bits") or field in {
                "id_width_bits",
                "lock_width_bits",
                "cache_width_bits",
                "prot_width_bits",
                "qos_width_bits",
                "region_width_bits",
            }
            if not isinstance(value, int) or isinstance(value, bool) or value < (0 if allow_zero else 1):
                errors.append(f"{label}.{field} is missing or invalid")
        parameter_evidence = row.get("parameter_evidence_refs")
        required_parameter_evidence = AXI_WIDTH_FIELDS | {
            "max_burst_length",
            "supports_narrow_bursts",
            "supports_unaligned_access",
            "read_outstanding_limit",
            "write_outstanding_limit",
            "byte_order",
        }
        if not isinstance(parameter_evidence, dict):
            errors.append(f"{label}.parameter_evidence_refs is missing")
        else:
            for field in sorted(required_parameter_evidence):
                _require_evidence_refs(
                    parameter_evidence.get(field),
                    f"{label}.parameter_evidence_refs.{field}",
                    evidence_ids,
                    errors,
                )
        data_width = row.get("data_width_bits")
        if isinstance(data_width, int) and data_width > 0 and data_width % 8:
            errors.append(f"{label}.data_width_bits must be byte-addressable")
        if isinstance(data_width, int) and row.get("strb_width_bits") != data_width // 8:
            errors.append(f"{label}.strb_width_bits must equal data_width_bits / 8")
        if not isinstance(row.get("max_burst_length"), int) or not 1 <= row.get("max_burst_length", 0) <= 256:
            errors.append(f"{label}.max_burst_length is missing or invalid")
        for field in ("supports_narrow_bursts", "supports_unaligned_access"):
            if not isinstance(row.get(field), bool):
                errors.append(f"{label}.{field} must be an explicit boolean")
        for field in ("read_outstanding_limit", "write_outstanding_limit"):
            if not isinstance(row.get(field), int) or row.get(field, 0) <= 0:
                errors.append(f"{label}.{field} must be positive")
        if str(row.get("byte_order") or "").lower() not in {
            "little",
            "big",
            "physical_byte_lane_order_preserved",
        }:
            errors.append(f"{label}.byte_order is invalid")

        signal_map = row.get("signal_map")
        signal_evidence = row.get("signal_evidence_refs")
        if not isinstance(signal_map, dict):
            errors.append(f"{label}.signal_map is missing")
            continue
        if not isinstance(signal_evidence, dict):
            errors.append(f"{label}.signal_evidence_refs is missing")
            signal_evidence = {}
        for channel, required_signals in AXI_CHANNEL_SIGNALS.items():
            channel_map = signal_map.get(channel)
            if not isinstance(channel_map, dict):
                errors.append(f"{label}.signal_map.{channel} is missing")
                continue
            channel_evidence = signal_evidence.get(channel)
            if not isinstance(channel_evidence, dict):
                errors.append(f"{label}.signal_evidence_refs.{channel} is missing")
                channel_evidence = {}
            missing = sorted(required_signals - set(channel_map))
            if missing:
                errors.append(f"{label}.signal_map.{channel} lacks signals: {missing}")
            for signal in required_signals & set(channel_map):
                width_field = {
                    "addr": "address_width_bits",
                    "data": "data_width_bits",
                    "id": "id_width_bits",
                    "strb": "strb_width_bits",
                    "len": "len_width_bits",
                    "size": "size_width_bits",
                    "burst": "burst_width_bits",
                    "lock": "lock_width_bits",
                    "cache": "cache_width_bits",
                    "prot": "prot_width_bits",
                    "qos": "qos_width_bits",
                    "region": "region_width_bits",
                    "user": f"{channel}user_width_bits",
                }.get(signal)
                width = row.get(width_field, -1) if width_field else 1
                if not _valid_signal(channel_map.get(signal), width):
                    errors.append(f"{label}.signal_map.{channel}.{signal} is invalid for declared width {width}")
                _require_evidence_refs(
                    channel_evidence.get(signal),
                    f"{label}.signal_evidence_refs.{channel}.{signal}",
                    evidence_ids,
                    errors,
                )

    fingerprint = canonical_contract_sha256(interfaces)
    if str(identity.get("axi_interfaces_sha256") or "").lower() != fingerprint:
        errors.append("identity.axi_interfaces_sha256 does not match axi_interfaces")
    return interfaces, fingerprint, errors


def _generated_source_contract_rows(simulation: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    harness = simulation.get("multilayer_harness")
    harness_rows = _as_rows(harness.get("source_files")) if isinstance(harness, dict) else []
    allowed_harness_roles = {"generated_accelerator", "generated_kernel", "compute_slot_adapter"}
    for index, row in enumerate(harness_rows):
        if _source_role(row) not in allowed_harness_roles:
            errors.append(
                f"simulation.multilayer_harness.source_files[{index}].role is not a generated accelerator/kernel/slot-adapter role"
            )
        rows.append(row)

    testbench = simulation.get("testbench")
    if isinstance(testbench, dict) and testbench.get("source_id"):
        testbench_rows = [testbench]
    elif isinstance(testbench, dict):
        testbench_rows = _as_rows(testbench.get("source_files"))
    else:
        testbench_rows = []
    if not testbench_rows:
        errors.append("simulation.testbench does not declare its generated source row")
    testbench_top = str(simulation.get("top_module") or "").strip()
    declared_testbench_top = str(testbench.get("top_module") or "").strip() if isinstance(testbench, dict) else ""
    if not testbench_top or declared_testbench_top != testbench_top:
        errors.append("simulation top_module is missing or differs from testbench.top_module")
    if testbench_top and not any(testbench_top in _declared_modules(row) for row in testbench_rows):
        errors.append("simulation top_module is not declared by the generated testbench source")
    for index, row in enumerate(testbench_rows):
        if _source_role(row) != "testbench":
            errors.append(f"simulation.testbench source[{index}].role is not testbench")
        rows.append(row)

    monitor_contract = simulation.get("protocol_monitor_contract")
    monitors = _as_rows(monitor_contract.get("monitors")) if isinstance(monitor_contract, dict) else []
    monitor_rows: list[dict[str, Any]] = []
    for monitor_index, monitor in enumerate(monitors):
        sources = _as_rows(monitor.get("source_files"))
        if not sources:
            errors.append(f"simulation.protocol_monitor_contract.monitors[{monitor_index}].source_files is empty")
        for source_index, row in enumerate(sources):
            if _source_role(row) != "protocol_monitor":
                errors.append(
                    f"simulation.protocol_monitor_contract.monitors[{monitor_index}].source_files[{source_index}].role is not protocol_monitor"
                )
            monitor_rows.append(row)
    rows.extend(monitor_rows)
    ids = [_source_id(row) for row in rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        errors.append("generated harness/kernel/testbench/monitor sources must have unique non-empty source_id values")
    return rows, errors


def _validate_generated_evidence(
    simulation: dict[str, Any], simulation_rows: list[dict[str, Any]], generated_source_ids: set[str]
) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    records = _as_rows(simulation.get("generated_evidence_records"))
    if not records:
        return set(), ["simulation.generated_evidence_records is empty"]
    source_by_id = {_source_id(row): row for row in simulation_rows}
    evidence_ids: set[str] = set()
    for index, row in enumerate(records):
        label = f"simulation.generated_evidence_records[{index}]"
        evidence_id = str(row.get("evidence_id") or "").strip()
        source_id = str(row.get("source_id") or "").strip()
        if not evidence_id or evidence_id in evidence_ids:
            errors.append(f"{label}.evidence_id is missing or duplicated")
        evidence_ids.add(evidence_id)
        if source_id not in generated_source_ids:
            errors.append(f"{label}.source_id is not a generated compile source: {source_id}")
        source = source_by_id.get(source_id, {})
        expected_hash = str(source.get("sha256") or source.get("local_sha256") or "").lower()
        if not expected_hash or str(row.get("source_sha256") or "").lower() != expected_hash:
            errors.append(f"{label}.source_sha256 does not bind the generated source")
        locator = row.get("locator")
        if not isinstance(locator, dict) or not str(locator.get("kind") or "").strip() or "value" not in locator:
            errors.append(f"{label}.locator must be a structured generated-source locator")
        if not str(row.get("fact_kind") or "").strip() or "observed_value" not in row:
            errors.append(f"{label} lacks fact_kind/observed_value")
    return evidence_ids, errors


def _validate_debug_observability_contract(
    simulation: dict[str, Any],
    testbench: dict[str, Any],
    simulation_rows: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    contract = testbench.get("debug_observability_contract")
    if not isinstance(contract, dict):
        return ["simulation.testbench.debug_observability_contract is missing"]
    if contract.get("schema_version") != BOARD_DEBUG_OBSERVABILITY_SCHEMA_VERSION:
        errors.append("debug observability contract schema_version is invalid")
    if contract.get("status") not in {"ready", "pass"}:
        errors.append("debug observability contract status is not ready/pass")
    if str(contract.get("format") or "").lower() != "jsonl":
        errors.append("debug observability contract format is not jsonl")
    required_values = {
        "observational_only": True,
        "drives_dut_signals": False,
        "new_synthesizable_ports_or_state": False,
        "flush_after_each_event": True,
        "heartbeat_is_semantic_progress": False,
        "fixed_wall_clock_timeout": False,
        "fixed_cycle_timeout": False,
        "bounded_deep_trace": True,
    }
    for field, expected in required_values.items():
        if contract.get(field) is not expected:
            errors.append(
                f"debug observability contract {field} must be {str(expected).lower()}"
            )
    if contract.get("synthesis_impact") != "none":
        errors.append("debug observability contract synthesis_impact is not none")
    if contract.get("implementation") not in {"testbench_only", "simulation_only"}:
        errors.append("debug observability implementation is not simulation/testbench only")
    event_kinds = {str(value) for value in contract.get("required_event_kinds", [])}
    missing_event_kinds = sorted(REQUIRED_DEBUG_EVENT_KINDS - event_kinds)
    if missing_event_kinds:
        errors.append(
            f"debug observability contract lacks required event kinds: {missing_event_kinds}"
        )
    event_fields = {str(value) for value in contract.get("required_event_fields", [])}
    missing_event_fields = sorted(REQUIRED_PROGRESS_EVENT_FIELDS - event_fields)
    if missing_event_fields:
        errors.append(
            f"debug observability contract lacks required event fields: {missing_event_fields}"
        )

    output = contract.get("progress_event_log")
    planned_outputs = simulation.get("execution_outputs")
    planned = (
        planned_outputs.get("progress_event_log")
        if isinstance(planned_outputs, dict)
        and isinstance(planned_outputs.get("progress_event_log"), dict)
        else {}
    )
    if (
        not isinstance(output, dict)
        or not _safe_relative_output_path(output.get("path"))
        or output.get("schema_version") != BOARD_PROGRESS_EVENT_SCHEMA_VERSION
        or output.get("path") != planned.get("path")
        or output.get("schema_version") != planned.get("schema_version")
    ):
        errors.append(
            "debug observability progress_event_log does not bind the planned JSONL output"
        )

    source_by_id = {
        _source_id(row): row for row in simulation_rows if _source_id(row)
    }
    probes = _as_rows(contract.get("probes"))
    seen_probe_ids: set[str] = set()
    observed_roles: set[str] = set()
    for index, probe in enumerate(probes):
        label = f"debug observability probe[{index}]"
        probe_id = str(probe.get("probe_id") or "")
        role = str(probe.get("semantic_role") or "")
        source_id = str(probe.get("source_id") or "")
        source = source_by_id.get(source_id)
        if not probe_id or probe_id in seen_probe_ids:
            errors.append(f"{label} has a missing or duplicate probe_id")
        if role not in REQUIRED_DEBUG_SEMANTIC_ROLES:
            errors.append(f"{label} has an unsupported semantic_role")
        else:
            observed_roles.add(role)
        if source is None:
            errors.append(f"{label} does not bind a compiled current-run source_id")
        elif str(probe.get("source_sha256") or "").lower() != str(
            source.get("sha256") or source.get("local_sha256") or ""
        ).lower():
            errors.append(f"{label} source_sha256 does not bind its current source")
        if not str(probe.get("instance_path") or "").strip():
            errors.append(f"{label} instance_path is missing")
        fields = probe.get("observed_fields")
        if not isinstance(fields, list) or not fields or not all(
            isinstance(value, str) and value for value in fields
        ):
            errors.append(f"{label} observed_fields is empty or invalid")
        if probe.get("read_only") is not True:
            errors.append(f"{label} is not explicitly read-only")
        seen_probe_ids.add(probe_id)
    missing_roles = sorted(REQUIRED_DEBUG_SEMANTIC_ROLES - observed_roles)
    if missing_roles:
        errors.append(
            f"debug observability probes lack required semantic roles: {missing_roles}"
        )

    testbench_path = Path(str(testbench.get("path") or ""))
    if testbench_path.is_file() and isinstance(output, dict):
        source_text = testbench_path.read_text(encoding="utf-8", errors="ignore")
        required_literals = {
            BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
            str(output.get("path") or ""),
            *REQUIRED_DEBUG_EVENT_KINDS,
            *REQUIRED_PROGRESS_EVENT_FIELDS,
        }
        missing_literals = sorted(
            value for value in required_literals if value and value not in source_text
        )
        if missing_literals:
            errors.append(
                "generated testbench does not emit the complete declared progress-event ABI: "
                f"{missing_literals}"
            )
        if "$fflush" not in source_text:
            errors.append("generated testbench does not flush live progress events")
        if "$display" not in source_text and "$write" not in source_text:
            errors.append("generated testbench has no concise live progress console output")
    return errors


def _semantic_manifest_path(simulation: dict[str, Any]) -> Path | None:
    reference = simulation.get("semantic_testbench_manifest")
    reference = reference if isinstance(reference, dict) else {}
    path = Path(str(reference.get("path") or ""))
    if not path.is_file():
        return None
    expected_sha256 = str(reference.get("sha256") or "").lower()
    if expected_sha256 and sha256_file(path).lower() != expected_sha256:
        return None
    return path


def _validate_pipeline_boundary_observation_contract(
    simulation: dict[str, Any],
    testbench: dict[str, Any],
) -> list[str]:
    """Validate current-DAG observation declarations after a real run.

    This remains absent from preflight so the first exact VCS execution can
    establish source-bound evidence.  Once the current semantic manifest is
    available, all later board acceptance requires the declaration to bind it.
    """

    semantic_path = _semantic_manifest_path(simulation)
    if semantic_path is None:
        return []
    try:
        semantic_manifest = json.loads(semantic_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ["semantic testbench manifest cannot be read for pipeline boundary observation"]
    if not isinstance(semantic_manifest, dict):
        return ["semantic testbench manifest is not an object for pipeline boundary observation"]
    authority = pipeline_boundary_observation_authority(
        semantic_manifest,
        semantic_manifest_path=semantic_path,
        testbench_source={
            "source_id": testbench.get("source_id"),
            "sha256": testbench.get("sha256"),
        },
    )
    if authority.get("status") != "ready":
        return ["current semantic pipeline boundary observation authority is unavailable"]
    debug = testbench.get("debug_observability_contract")
    debug = debug if isinstance(debug, dict) else {}
    contract = debug.get("pipeline_boundary_observation_contract")
    if not isinstance(contract, dict):
        return ["debug observability contract lacks current-DAG pipeline boundary observation declaration"]
    errors: list[str] = []
    if contract.get("schema_version") != PIPELINE_BOUNDARY_OBSERVATION_SCHEMA_VERSION:
        errors.append("pipeline boundary observation schema_version is invalid")
    for field, expected in (
        ("authority_sha256", authority.get("authority_sha256")),
        (
            "semantic_manifest_sha256",
            authority.get("source", {}).get("semantic_manifest_sha256"),
        ),
        (
            "pipeline_overlap_contract_sha256",
            authority.get("source", {}).get("pipeline_overlap_contract_sha256"),
        ),
        (
            "trace_contract_sha256",
            authority.get("source", {}).get("trace_contract_sha256"),
        ),
    ):
        if contract.get(field) != expected:
            errors.append(f"pipeline boundary observation {field} does not bind current semantic authority")
    if contract.get("read_only") is not True:
        errors.append("pipeline boundary observation contract is not explicitly read-only")
    if contract.get("bounded_first_last_records_only") is not True:
        errors.append("pipeline boundary observation contract is not bounded to first/last records")
    if set(map(str, contract.get("required_fields", []))) != set(
        PIPELINE_BOUNDARY_OBSERVATION_FIELDS
    ):
        errors.append("pipeline boundary observation contract required_fields are incomplete")
    required = {
        str(row.get("boundary_id")): row
        for row in authority.get("required_boundaries", [])
        if isinstance(row, dict) and row.get("boundary_id")
    }
    declared_rows = _as_rows(contract.get("boundaries"))
    declared: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(declared_rows):
        boundary_id = str(row.get("boundary_id") or "")
        if not boundary_id or boundary_id in declared:
            errors.append(f"pipeline boundary observation boundaries[{index}] has missing or duplicate boundary_id")
            continue
        declared[boundary_id] = row
    missing = sorted(set(required) - set(declared))
    unexpected = sorted(set(declared) - set(required))
    if missing:
        errors.append(f"pipeline boundary observation declaration misses current boundaries: {missing}")
    if unexpected:
        errors.append(f"pipeline boundary observation declaration has unknown boundaries: {unexpected}")
    for boundary_id, required_row in required.items():
        row = declared.get(boundary_id, {})
        if not row:
            continue
        if row.get("read_only") is not True:
            errors.append(f"pipeline boundary observation {boundary_id} is not read-only")
        if row.get("src_stage") != required_row.get("src_stage") or row.get("dst_stage") != required_row.get("dst_stage"):
            errors.append(f"pipeline boundary observation {boundary_id} does not bind current stages")
        unavailable_reason = str(row.get("unavailable_reason") or "").strip()
        observed_fields = {str(value) for value in row.get("observed_fields", [])}
        if unavailable_reason:
            continue
        missing_fields = sorted(set(PIPELINE_BOUNDARY_OBSERVATION_FIELDS) - observed_fields)
        if missing_fields:
            errors.append(f"pipeline boundary observation {boundary_id} lacks fields: {missing_fields}")
    return errors


def _validate_testbench_contract(
    simulation: dict[str, Any],
    identity: dict[str, Any],
    closure_rows: list[dict[str, Any]],
    simulation_rows: list[dict[str, Any]],
    abi: dict[str, Any],
    abi_hash: str,
    timing_hash: str,
    axi_hash: str,
    preserved_sample_source_ids: set[str],
    generated_evidence_ids: set[str],
    *,
    require_debug_observability: bool,
) -> list[str]:
    errors: list[str] = []
    testbench = simulation.get("testbench")
    if not isinstance(testbench, dict):
        return ["simulation.testbench contract is missing"]
    compute_slot_axi = _is_compute_slot_axi_validation(simulation)
    if (
        not compute_slot_axi
        and testbench.get("exact_sample_top_module") != identity.get("top_module")
    ):
        errors.append("simulation.testbench.exact_sample_top_module does not match identity.top_module")
    timing = identity.get("timing_contract") if isinstance(identity.get("timing_contract"), dict) else {}
    memory = timing.get("memory_timing_model") if isinstance(timing.get("memory_timing_model"), dict) else {}
    expected_memory_ids = {str(value) for value in memory.get("source_ids", []) if str(value)}
    used_memory_ids = testbench.get("uses_memory_model_source_ids")
    if compute_slot_axi:
        if used_memory_ids not in (None, []):
            errors.append(
                "compute-slot AXI testbench must not compile sample memory-model source IDs"
            )
        transaction_model = testbench.get("axi_transaction_memory_model")
        if not isinstance(transaction_model, dict):
            errors.append(
                "simulation.testbench.axi_transaction_memory_model is required for compute_slot_axi validation"
            )
        else:
            if transaction_model.get("status") not in {"ready", "pass"}:
                errors.append("compute-slot AXI transaction memory model is not ready/pass")
            if transaction_model.get("contract_driven") is not True:
                errors.append("compute-slot AXI transaction memory model is not contract-driven")
            if transaction_model.get("boundary") != COMPUTE_SLOT_AXI_VALIDATION_MODE:
                errors.append("AXI transaction memory model is not bound at the compute-slot AXI boundary")
            if (
                str(transaction_model.get("axi_interfaces_sha256") or "").lower()
                != axi_hash
            ):
                errors.append("AXI transaction memory model does not bind the identity AXI contract")
            if (
                str(transaction_model.get("timing_contract_sha256") or "").lower()
                != timing_hash
            ):
                errors.append("AXI transaction memory model does not bind the identity timing contract")
            if transaction_model.get("replaces_compute_slot_rtl") is not False:
                errors.append("AXI transaction memory model may not replace compute-slot RTL")
    else:
        if not isinstance(used_memory_ids, list) or set(map(str, used_memory_ids)) != expected_memory_ids:
            errors.append("simulation.testbench.uses_memory_model_source_ids does not exactly bind the identity memory timing model")
        if not expected_memory_ids.issubset(preserved_sample_source_ids):
            errors.append("exact sample memory-model sources were removed by the compute-slot transformation")
    if str(testbench.get("timing_contract_sha256") or "").lower() != timing_hash:
        errors.append("simulation.testbench.timing_contract_sha256 does not bind identity timing")
    if str(testbench.get("compute_slot_abi_sha256") or "").lower() != abi_hash:
        errors.append("simulation.testbench.compute_slot_abi_sha256 does not bind the compute-slot ABI")
    control = abi.get("control_abi") if isinstance(abi.get("control_abi"), dict) else {}
    if str(testbench.get("control_abi_sha256") or "").lower() != canonical_contract_sha256(control):
        errors.append("simulation.testbench.control_abi_sha256 does not bind the compute-slot control ABI")
    for field in ("force_calibration", "synthetic_memory_latency", "behavioral_ddr_substitute"):
        if testbench.get(field) is not False:
            errors.append(f"simulation.testbench.{field} must be false")
    _require_evidence_refs(
        testbench.get("evidence_refs"),
        "simulation.testbench",
        generated_evidence_ids,
        errors,
    )
    # The first exact-board VCS run must prove the real AXI/DDR path before a
    # failure can justify a complete adaptive probe plan. Post-run acceptance
    # still requires the full read-only observability contract.
    if require_debug_observability:
        errors.extend(
            _validate_debug_observability_contract(
                simulation,
                testbench,
                simulation_rows,
            )
        )
        errors.extend(
            _validate_pipeline_boundary_observation_contract(
                simulation,
                testbench,
            )
        )
    scan = testbench.get("forbidden_construct_scan")
    if not isinstance(scan, dict):
        errors.append("simulation.testbench.forbidden_construct_scan is missing")
    else:
        if scan.get("status") != "planned" or not isinstance(scan.get("required"), bool):
            errors.append("simulation.testbench.forbidden_construct_scan must be an explicit planned optional/required contract")
        if str(scan.get("source_sha256") or "").lower() != str(testbench.get("sha256") or "").lower():
            errors.append("simulation.testbench.forbidden_construct_scan does not bind the testbench source hash")
        if scan.get("required") is False:
            if str(scan.get("producer") or "") != "existing_simulator_compile":
                errors.append("optional forbidden-construct scan must be produced only by the existing simulator compile")
            return errors
        if str(scan.get("method") or "").lower() != "hdl_ast":
            errors.append("required forbidden-construct scan method is not hdl_ast")
        tool = scan.get("tool")
        version_regex = str(tool.get("version_regex") or "") if isinstance(tool, dict) else ""
        if (
            not isinstance(tool, dict)
            or not str(tool.get("name") or "").strip()
            or not version_regex
            or not isinstance(tool.get("version_argv"), list)
            or not tool.get("version_argv")
            or not all(isinstance(value, str) and value for value in tool.get("version_argv", []))
        ):
            errors.append("simulation.testbench.forbidden_construct_scan.tool name/version_regex/version_argv is missing")
        elif version_regex:
            try:
                re.compile(version_regex)
            except re.error:
                errors.append("simulation.testbench.forbidden_construct_scan.tool.version_regex is invalid")
        invocation = scan.get("invocation")
        invocation_argv = invocation.get("argv") if isinstance(invocation, dict) else None
        if (
            not isinstance(invocation, dict)
            or not isinstance(invocation_argv, list)
            or not invocation_argv
            or not all(isinstance(value, str) and value for value in invocation_argv)
            or sum(value.count("{source}") for value in invocation_argv) != 1
            or sum(value.count("{report}") for value in invocation_argv) != 1
            or invocation.get("shell") is not False
            or not _safe_relative_output_path(invocation.get("cwd"))
        ):
            errors.append("simulation.testbench.forbidden_construct_scan.invocation is not a safe source/report-bound argv contract")
        required_checks = set(map(str, scan.get("required_checks", [])))
        if required_checks != REQUIRED_TESTBENCH_AST_CHECKS:
            errors.append("simulation.testbench.forbidden_construct_scan.required_checks is incomplete")
        report = scan.get("report_output")
        if (
            not isinstance(report, dict)
            or not _safe_relative_output_path(report.get("path"))
            or not str(report.get("schema_version") or "").strip()
        ):
            errors.append("simulation.testbench.forbidden_construct_scan.report_output is invalid")
    if not compute_slot_axi:
        closure_ids = {_source_id(row) for row in closure_rows}
        if not expected_memory_ids.issubset(closure_ids):
            errors.append("simulation testbench memory model ids are not part of the original exact sample closure")
    return errors


def _validate_compute_slot_axi_simulation_sources(
    simulation: dict[str, Any],
    rows: list[dict[str, Any]],
    closure_rows: list[dict[str, Any]],
    closure_hash: str,
    abi: dict[str, Any],
    errors: list[str],
) -> tuple[list[dict[str, Any]], str, list[str], dict[str, Any]]:
    """Validate the generated-only compile set used at the real compute-slot AXI boundary."""

    ids = [_source_id(row) for row in rows]
    compile_ids = simulation.get("compile_source_ids")
    if not isinstance(compile_ids, list) or list(map(str, compile_ids)) != ids:
        errors.append(
            "compute-slot AXI compile_source_ids must exactly enumerate source_files in order"
        )

    closure_by_id = {_source_id(row): row for row in closure_rows if _source_id(row)}
    closure_ids = set(closure_by_id)
    replaced_ids = {
        str(value) for value in abi.get("replaced_source_ids", []) if str(value)
    }
    unknown_replaced = sorted(replaced_ids - closure_ids)
    if unknown_replaced:
        errors.append(
            f"compute-slot replaced_source_ids are not in the exact sample closure: {unknown_replaced}"
        )

    generated_rows, generated_errors = _generated_source_contract_rows(simulation)
    errors.extend(generated_errors)
    generated_by_id = {
        _source_id(row): row for row in generated_rows if _source_id(row)
    }
    generated_ids = set(generated_by_id)
    if generated_ids & closure_ids:
        errors.append(
            "generated source_ids collide with sample-project source_ids: "
            f"{sorted(generated_ids & closure_ids)}"
        )
    if set(ids) != generated_ids:
        errors.append(
            "compute-slot AXI source_files must contain only the generated/certified "
            f"boundary source set; extra={sorted(set(ids) - generated_ids)} "
            f"missing={sorted(generated_ids - set(ids))}"
        )

    compiled_sample_ids = simulation.get("compiled_sample_source_ids")
    if compiled_sample_ids not in (None, []):
        errors.append("compute-slot AXI validation must not compile sample-project sources")
    declared_replaced = simulation.get("replaced_sample_source_ids")
    if (
        not isinstance(declared_replaced, list)
        or set(map(str, declared_replaced)) != replaced_ids
    ):
        errors.append(
            "simulation.replaced_sample_source_ids does not bind compute_slot_abi.replaced_source_ids"
        )
    declared_generated = simulation.get("generated_source_ids")
    if (
        not isinstance(declared_generated, list)
        or set(map(str, declared_generated)) != generated_ids
    ):
        errors.append(
            "simulation.generated_source_ids does not exactly enumerate harness/kernel/testbench/monitor sources"
        )
    if simulation.get("sample_runtime_auxiliary_files") not in (None, []):
        errors.append(
            "compute-slot AXI validation must not stage sample runtime auxiliary files"
        )

    by_id = {_source_id(row): row for row in rows}
    for source_id, expected in generated_by_id.items():
        actual = by_id.get(source_id)
        if actual is None:
            errors.append(f"simulation source list omits generated contract source: {source_id}")
        elif _normalized_source_rows([actual]) != _normalized_source_rows([expected]):
            errors.append(
                f"simulation generated source identity differs from its hash-bound producer contract: {source_id}"
            )

    slot_module = str(abi.get("slot_module") or "")
    replacements = _as_rows(simulation.get("source_replacements"))
    replacement_by_source: dict[str, dict[str, Any]] = {}
    for index, replacement in enumerate(replacements):
        source_id = str(replacement.get("replaced_source_id") or "")
        if source_id in replacement_by_source:
            errors.append(
                f"simulation.source_replacements has duplicate replaced_source_id: {source_id}"
            )
        replacement_by_source[source_id] = replacement
        generated_id = str(replacement.get("generated_source_id") or "")
        generated = generated_by_id.get(generated_id)
        if (
            source_id not in replaced_ids
            or generated is None
            or _source_role(generated) != "compute_slot_adapter"
        ):
            errors.append(
                f"simulation.source_replacements[{index}] is not a valid compute-slot adapter replacement"
            )
        if (
            replacement.get("replaced_module") != slot_module
            or replacement.get("generated_module") != slot_module
            or (generated is not None and slot_module not in _declared_modules(generated))
        ):
            errors.append(
                f"simulation.source_replacements[{index}] does not preserve the compute-slot module ABI"
            )
        if str(replacement.get("compute_slot_abi_sha256") or "").lower() != str(
            simulation.get("compute_slot_abi_sha256") or ""
        ).lower():
            errors.append(
                f"simulation.source_replacements[{index}] does not bind the compute-slot ABI hash"
            )
    if set(replacement_by_source) != replaced_ids:
        errors.append(
            "simulation.source_replacements does not cover exactly all replaced compute-slot sources"
        )

    for source_id, row in by_id.items():
        for dependency in _dependencies(row):
            if dependency not in generated_ids:
                errors.append(
                    "compute-slot AXI compile source depends outside the generated boundary "
                    f"closure: {source_id} -> {dependency}"
                )
    module_owners: dict[str, list[str]] = {}
    for source_id, row in by_id.items():
        for module in _declared_modules(row):
            module_owners.setdefault(module, []).append(source_id)
    duplicate_modules = {
        module: owners for module, owners in module_owners.items() if len(owners) > 1
    }
    if duplicate_modules:
        errors.append(
            f"simulation compile source transformation has duplicate module definitions: {duplicate_modules}"
        )
    if simulation.get("synthesis_sources_excluded") is not True:
        errors.append("simulation.synthesis_sources_excluded is not true")
    if str(simulation.get("source_closure_sha256") or "").lower() != closure_hash:
        errors.append(
            "simulation.source_closure_sha256 does not bind the exact recursive sample-project closure"
        )
    compile_hash = compile_source_set_fingerprint(rows)
    if str(simulation.get("compile_source_set_sha256") or "").lower() != compile_hash:
        errors.append(
            "simulation.compile_source_set_sha256 does not match the actual compile source set"
        )
    details = {
        "verified_compile_source_ids": sorted(generated_ids),
        "preserved_sample_source_ids": [],
        "replaced_sample_source_ids": sorted(replaced_ids),
        "generated_source_ids": sorted(generated_ids),
        "external_fixture_source_ids": [],
        "sample_runtime_auxiliary_source_ids": [],
    }
    return rows, compile_hash, errors, details


def _validate_simulation_sources(
    simulation: dict[str, Any],
    simulation_path: Path,
    closure_rows: list[dict[str, Any]],
    closure_hash: str,
    abi: dict[str, Any],
    external_fixture: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, list[str], dict[str, Any]]:
    errors: list[str] = []
    rows = _as_rows(simulation.get("source_files"))
    if not rows:
        return [], "", ["simulation.source_files is empty"], {}
    ids = [_source_id(row) for row in rows]
    if any(not value for value in ids):
        errors.append("simulation.source_files contains a source without source_id")
    if len(set(ids)) != len(ids):
        errors.append("simulation.source_files contains duplicate source_id values")
    for index, row in enumerate(rows):
        _verified_source_file(row, simulation_path, f"simulation.source_files[{index}]", errors)
        if not _source_role(row):
            errors.append(f"simulation.source_files[{index}].role is missing")
        if _is_synthesis_only(row):
            errors.append(f"simulation.source_files[{index}] is synthesis-only and must not be compiled")

    if _is_compute_slot_axi_validation(simulation):
        return _validate_compute_slot_axi_simulation_sources(
            simulation,
            rows,
            closure_rows,
            closure_hash,
            abi,
            errors,
        )

    compile_ids = simulation.get("compile_source_ids")
    if not isinstance(compile_ids, list) or set(map(str, compile_ids)) != set(ids):
        errors.append("simulation.compile_source_ids does not exactly enumerate source_files")
    full_closure_by_id = {_source_id(row): row for row in closure_rows}
    closure_by_id = {
        source_id: row
        for source_id, row in full_closure_by_id.items()
        if _is_simulator_compile_input(row)
    }
    closure_ids = set(closure_by_id)
    runtime_auxiliary_by_id = {
        source_id: row
        for source_id, row in full_closure_by_id.items()
        if not _is_simulator_compile_input(row)
    }
    declared_runtime_auxiliary = _as_rows(
        simulation.get("sample_runtime_auxiliary_files")
    )
    declared_runtime_by_id = {
        _source_id(row): row for row in declared_runtime_auxiliary if _source_id(row)
    }
    if set(declared_runtime_by_id) != set(runtime_auxiliary_by_id):
        errors.append(
            "simulation.sample_runtime_auxiliary_files do not exactly enumerate non-HDL sample closure entries"
        )
    for source_id, expected in runtime_auxiliary_by_id.items():
        actual = declared_runtime_by_id.get(source_id)
        if actual is None:
            continue
        _verified_source_file(
            actual,
            simulation_path,
            f"simulation.sample_runtime_auxiliary_files[{source_id}]",
            errors,
        )
        expected_path = _resolve_path(_source_path(expected), simulation_path).resolve()
        actual_path = _resolve_path(_source_path(actual), simulation_path).resolve()
        runtime_staged_path = Path(str(actual.get("runtime_staged_path") or ""))
        if (
            actual_path != expected_path
            or str(actual.get("sha256") or actual.get("local_sha256") or "").lower()
            != str(expected.get("sha256") or expected.get("local_sha256") or "").lower()
            or not runtime_staged_path.name
            or runtime_staged_path.is_absolute()
            or ".." in runtime_staged_path.parts
        ):
            errors.append(
                f"simulation sample runtime auxiliary differs from exact closure: {source_id}"
            )
    replaced_ids = {str(value) for value in abi.get("replaced_source_ids", []) if str(value)}
    unknown_replaced = sorted(replaced_ids - closure_ids)
    if unknown_replaced:
        errors.append(f"compute-slot replaced_source_ids are not in the exact sample closure: {unknown_replaced}")
    slot_module = str(abi.get("slot_module") or "")
    protected_roles = {"wrapper", "board_wrapper", "sample_wrapper", "bd_sim", "ip_sim", "memory_model", "vendor_sim"}
    for source_id in sorted(replaced_ids & closure_ids):
        row = closure_by_id[source_id]
        if (
            str(row.get("closure_role") or "").lower() != "compute_slot_implementation"
            or _source_role(row) in protected_roles
        ):
            errors.append(f"compute-slot replacement tries to remove a protected wrapper/BD/memory/IP source: {source_id}")
        if slot_module not in _declared_modules(row):
            errors.append(f"compute-slot replaced source does not declare compute_slot_abi.slot_module: {source_id}")
    preserved_ids = closure_ids - replaced_ids
    generated_contract_rows, generated_errors = _generated_source_contract_rows(simulation)
    errors.extend(generated_errors)
    generated_by_id = {_source_id(row): row for row in generated_contract_rows if _source_id(row)}
    generated_ids = set(generated_by_id)
    if generated_ids & closure_ids:
        errors.append(f"generated source_ids collide with sample-project source_ids: {sorted(generated_ids & closure_ids)}")
    fixture_by_id = external_fixture.get("source_by_id", {})
    fixture_by_id = fixture_by_id if isinstance(fixture_by_id, dict) else {}
    fixture_ids = {
        str(value)
        for value in external_fixture.get("selected_source_ids", [])
        if str(value)
    }
    fixture_collisions = fixture_ids.intersection(closure_ids | generated_ids)
    if fixture_collisions:
        errors.append(
            f"external fixture source_ids collide with sample/generated source_ids: {sorted(fixture_collisions)}"
        )
    expected_compile_ids = preserved_ids | generated_ids | fixture_ids
    if set(ids) != expected_compile_ids:
        errors.append(
            "simulation.source_files is not the verified sample-closure transformation; "
            f"extra={sorted(set(ids) - expected_compile_ids)} missing={sorted(expected_compile_ids - set(ids))}"
        )
    compiled_sample_ids = simulation.get("compiled_sample_source_ids")
    if not isinstance(compiled_sample_ids, list) or set(map(str, compiled_sample_ids)) != preserved_ids:
        errors.append("simulation.compiled_sample_source_ids does not exactly enumerate preserved sample-project sources")
    declared_replaced = simulation.get("replaced_sample_source_ids")
    if not isinstance(declared_replaced, list) or set(map(str, declared_replaced)) != replaced_ids:
        errors.append("simulation.replaced_sample_source_ids does not bind compute_slot_abi.replaced_source_ids")
    declared_generated = simulation.get("generated_source_ids")
    if not isinstance(declared_generated, list) or set(map(str, declared_generated)) != generated_ids:
        errors.append("simulation.generated_source_ids does not exactly enumerate harness/kernel/testbench/monitor sources")

    by_id = {_source_id(row): row for row in rows}
    for source_id in sorted(preserved_ids):
        expected = closure_by_id[source_id]
        actual = by_id.get(_source_id(expected))
        if actual is None:
            errors.append(f"simulation source list omits exact sample-project source: {_source_id(expected)}")
        elif (
            str(actual.get("sha256") or actual.get("local_sha256") or "").lower()
            != str(expected.get("sha256") or expected.get("local_sha256") or "").lower()
            or _source_role(actual) != _source_role(expected)
        ):
            errors.append(f"simulation source identity differs from exact sample closure: {_source_id(expected)}")
    for source_id, expected in generated_by_id.items():
        actual = by_id.get(source_id)
        if actual is None:
            errors.append(f"simulation source list omits generated contract source: {source_id}")
        elif _normalized_source_rows([actual]) != _normalized_source_rows([expected]):
            errors.append(f"simulation generated source identity differs from its hash-bound producer contract: {source_id}")
    for source_id in sorted(fixture_ids):
        expected = fixture_by_id.get(source_id)
        actual = by_id.get(source_id)
        if not isinstance(expected, dict) or actual is None:
            errors.append(f"simulation source list omits selected external fixture source: {source_id}")
            continue
        expected_path = _resolve_path(
            _source_path(expected), Path(str(external_fixture.get("path") or simulation_path))
        ).resolve()
        actual_path = _resolve_path(_source_path(actual), simulation_path).resolve()
        if (
            _source_role(actual) != "external_fixture_compile_source"
            or actual_path != expected_path
            or str(actual.get("sha256") or actual.get("local_sha256") or "").lower()
            != str(expected.get("sha256") or expected.get("local_sha256") or "").lower()
            or str(actual.get("provider_configuration_sha256") or "")
            != str(expected.get("provider_configuration_sha256") or "")
        ):
            errors.append(f"simulation external fixture source differs from compile authority: {source_id}")
    ordered_fixture_ids = [
        str(value)
        for value in external_fixture.get("selected_source_ids", [])
        if str(value)
    ]
    if [source_id for source_id in compile_ids if source_id in fixture_ids] != ordered_fixture_ids:
        errors.append("simulation.compile_source_ids do not preserve selected external fixture order")

    replacements = _as_rows(simulation.get("source_replacements"))
    replacement_by_source: dict[str, dict[str, Any]] = {}
    for index, replacement in enumerate(replacements):
        source_id = str(replacement.get("replaced_source_id") or "")
        if source_id in replacement_by_source:
            errors.append(f"simulation.source_replacements has duplicate replaced_source_id: {source_id}")
        replacement_by_source[source_id] = replacement
        generated_id = str(replacement.get("generated_source_id") or "")
        generated = generated_by_id.get(generated_id)
        if source_id not in replaced_ids or generated is None or _source_role(generated) != "compute_slot_adapter":
            errors.append(f"simulation.source_replacements[{index}] is not a valid compute-slot adapter replacement")
        if (
            replacement.get("replaced_module") != slot_module
            or replacement.get("generated_module") != slot_module
            or (generated is not None and slot_module not in _declared_modules(generated))
        ):
            errors.append(f"simulation.source_replacements[{index}] does not preserve the compute-slot module ABI")
        if str(replacement.get("compute_slot_abi_sha256") or "").lower() != str(
            simulation.get("compute_slot_abi_sha256") or ""
        ).lower():
            errors.append(f"simulation.source_replacements[{index}] does not bind the compute-slot ABI hash")
    if set(replacement_by_source) != replaced_ids:
        errors.append("simulation.source_replacements does not cover exactly all replaced compute-slot sources")

    for source_id, row in by_id.items():
        for dependency in _dependencies(row):
            if dependency in replaced_ids:
                if dependency not in replacement_by_source:
                    errors.append(f"compiled source dependency has no compute-slot replacement: {source_id} -> {dependency}")
            elif dependency not in expected_compile_ids:
                errors.append(f"compiled source has unresolved transformed dependency: {source_id} -> {dependency}")
    module_owners: dict[str, list[str]] = {}
    for source_id, row in by_id.items():
        for module in _declared_modules(row):
            module_owners.setdefault(module, []).append(source_id)
    duplicate_modules = {module: owners for module, owners in module_owners.items() if len(owners) > 1}
    if duplicate_modules:
        errors.append(f"simulation compile source transformation has duplicate module definitions: {duplicate_modules}")
    if simulation.get("synthesis_sources_excluded") is not True:
        errors.append("simulation.synthesis_sources_excluded is not true")
    if str(simulation.get("source_closure_sha256") or "").lower() != closure_hash:
        errors.append("simulation.source_closure_sha256 does not bind the exact recursive sample-project closure")
    compile_hash = compile_source_set_fingerprint(rows)
    if str(simulation.get("compile_source_set_sha256") or "").lower() != compile_hash:
        errors.append("simulation.compile_source_set_sha256 does not match the actual compile source set")
    details = {
        "verified_compile_source_ids": sorted(expected_compile_ids),
        "preserved_sample_source_ids": sorted(preserved_ids),
        "replaced_sample_source_ids": sorted(replaced_ids),
        "generated_source_ids": sorted(generated_ids),
        "external_fixture_source_ids": ordered_fixture_ids,
        "sample_runtime_auxiliary_source_ids": sorted(runtime_auxiliary_by_id),
    }
    return rows, compile_hash, errors, details


def _path_matches(full_path: str, declared_path: str) -> bool:
    return bool(full_path and declared_path) and (full_path == declared_path or full_path.endswith(f".{declared_path}"))


def _instance_has_role(row: dict[str, Any], role: str) -> bool:
    roles = row.get("binding_roles")
    return row.get("binding_role") == role or (isinstance(roles, list) and role in roles)


def _validate_multilayer_board_integration(
    simulation: dict[str, Any],
    simulation_path: Path,
    simulation_rows: list[dict[str, Any]],
    closure_hash: str,
    abi_hash: str,
    timing_hash: str,
    axi_interfaces: list[dict[str, Any]],
    generated_evidence_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    harness = simulation.get("multilayer_harness")
    if not isinstance(harness, dict):
        return {}, ["simulation.multilayer_harness is missing"]
    source_rows = _as_rows(harness.get("source_files"))
    if not source_rows:
        errors.append("simulation.multilayer_harness.source_files is empty")
    simulation_by_id = {_source_id(row): row for row in simulation_rows}
    for index, row in enumerate(source_rows):
        _verified_source_file(row, simulation_path, f"simulation.multilayer_harness.source_files[{index}]", errors)
        actual = simulation_by_id.get(_source_id(row))
        if actual is None:
            errors.append(f"multilayer harness source is not in the simulator compile set: {_source_id(row)}")
        elif str(actual.get("sha256") or "").lower() != str(row.get("sha256") or "").lower():
            errors.append(f"multilayer harness source hash differs from the compile set: {_source_id(row)}")
    top_module = str(harness.get("top_module") or "").strip()
    instance_path = str(harness.get("instance_path") or "").strip()
    single_layer_top = str(harness.get("verified_single_layer_top_module") or "").strip()
    source_by_id = {_source_id(row): row for row in source_rows if _source_id(row)}
    certified_kernel_ids = harness.get("certified_kernel_source_ids")
    certified_kernel_set = (
        {str(value) for value in certified_kernel_ids if str(value)}
        if isinstance(certified_kernel_ids, list)
        else set()
    )
    if not top_module:
        errors.append("simulation.multilayer_harness.top_module is missing")
    if not instance_path:
        errors.append("simulation.multilayer_harness.instance_path is missing")
    if not single_layer_top:
        errors.append("simulation.multilayer_harness.verified_single_layer_top_module is missing")
    if not certified_kernel_set or not certified_kernel_set.issubset(set(source_by_id)):
        errors.append("simulation.multilayer_harness.certified_kernel_source_ids is missing or outside harness sources")
    elif any(_source_role(source_by_id[source_id]) != "generated_kernel" for source_id in certified_kernel_set):
        errors.append("multilayer harness certified_kernel_source_ids contain a non-kernel source")
    elif not any(single_layer_top in _declared_modules(source_by_id[source_id]) for source_id in certified_kernel_set):
        errors.append("verified_single_layer_top_module is not declared by a certified kernel source")
    if top_module and not any(top_module in _declared_modules(row) for row in source_rows):
        errors.append("simulation.multilayer_harness.top_module is not declared by a harness source")
    harness_source_hash = compile_source_set_fingerprint(source_rows) if source_rows else ""
    if str(harness.get("source_set_sha256") or "").lower() != harness_source_hash:
        errors.append("simulation.multilayer_harness.source_set_sha256 does not match its hash-verified sources")
    if harness.get("instantiated_kernel_count") != 1:
        errors.append("simulation.multilayer_harness.instantiated_kernel_count must be exactly one reusable connected-layer kernel")
    certificate = harness.get("single_layer_promotion_certificate")
    if not isinstance(certificate, dict):
        errors.append("simulation.multilayer_harness.single_layer_promotion_certificate is missing")
    else:
        _verified_artifact(
            certificate,
            simulation_path,
            "simulation.multilayer_harness.single_layer_promotion_certificate",
            "path",
            errors,
        )
        certificate_path_text = str(certificate.get("path") or "")
        if certificate_path_text:
            certificate_path = _resolve_path(certificate_path_text, simulation_path)
            if certificate_path.is_file():
                try:
                    certificate_data = json.loads(certificate_path.read_text(encoding="utf-8"))
                except Exception:
                    certificate_data = {}
                if not isinstance(certificate_data, dict) or certificate_data.get("status") != "pass":
                    errors.append("multilayer harness single-layer promotion certificate status is not pass")

    model_layer_count = simulation.get("model_layer_count")
    bound_layer_count = simulation.get("bound_layer_count")
    target_layer_count = simulation.get("target_layer_count", harness.get("target_layer_count"))
    if (
        not isinstance(target_layer_count, int)
        or isinstance(target_layer_count, bool)
        or target_layer_count <= 0
    ):
        target_layer_count = 0
    if model_layer_count is None:
        model_layer_count = target_layer_count
    validation_layer_indices = simulation.get("validation_layer_indices")
    if validation_layer_indices is None:
        validation_layer_indices = list(range(target_layer_count))
    covers_full_model = target_layer_count == model_layer_count
    consumed_hashes = simulation.get("board_consumed_tensor_hashes")
    if (
        not isinstance(model_layer_count, int)
        or isinstance(model_layer_count, bool)
        or model_layer_count < target_layer_count
    ):
        errors.append("simulation.model_layer_count is invalid for the board workload")
    if validation_layer_indices != list(range(target_layer_count)):
        errors.append("simulation.validation_layer_indices must be a contiguous prefix")
    if simulation.get("all_target_layers") is not covers_full_model:
        errors.append("simulation.all_target_layers does not match the board workload scope")
    if not isinstance(bound_layer_count, int) or isinstance(bound_layer_count, bool) or bound_layer_count <= 0:
        errors.append("simulation.bound_layer_count must be positive")
    if target_layer_count <= 0:
        errors.append("simulation.target_layer_count must be positive")
    elif bound_layer_count != target_layer_count:
        errors.append("simulation.bound_layer_count does not equal target_layer_count")
    if (
        not isinstance(consumed_hashes, list)
        or not consumed_hashes
        or len(set(map(str, consumed_hashes))) != len(consumed_hashes)
        or any(not re.fullmatch(r"[0-9a-fA-F]{64}", str(value)) for value in consumed_hashes)
    ):
        errors.append("simulation.board_consumed_tensor_hashes must be a non-empty unique list of SHA-256 values")

    integration = simulation.get("board_integration_contract")
    if not isinstance(integration, dict):
        errors.append("simulation.board_integration_contract is missing")
        return harness, errors
    if integration.get("status") != "pass":
        errors.append("simulation.board_integration_contract.status is not pass")
    integration_hash = canonical_contract_sha256(integration)
    if str(simulation.get("board_integration_contract_sha256") or "").lower() != integration_hash:
        errors.append("simulation.board_integration_contract_sha256 does not match board_integration_contract")
    for field, expected in (
        ("source_closure_sha256", closure_hash),
        ("compute_slot_abi_sha256", abi_hash),
        ("timing_contract_sha256", timing_hash),
    ):
        if not expected or str(integration.get(field) or "").lower() != expected:
            errors.append(f"simulation.board_integration_contract.{field} does not bind the board identity")

    scheduler = integration.get("scheduler")
    if not isinstance(scheduler, dict):
        errors.append("simulation.board_integration_contract.scheduler is missing")
    else:
        _require_evidence_refs(scheduler.get("evidence_refs"), "simulation.board_integration_contract.scheduler", generated_evidence_ids, errors)
        if (
            scheduler.get("enabled") is not True
            or scheduler.get("all_validation_layers", scheduler.get("all_target_layers"))
            is not True
            or scheduler.get("all_target_layers", covers_full_model) is not covers_full_model
        ):
            errors.append("board integration scheduler does not execute the complete validation workload")
        if isinstance(target_layer_count, int) and scheduler.get("layer_count") != target_layer_count:
            errors.append("board integration scheduler layer_count does not match target_layer_count")

    weight_buffer = integration.get("double_weight_buffer")
    if not isinstance(weight_buffer, dict):
        errors.append("simulation.board_integration_contract.double_weight_buffer is missing")
    elif (
        weight_buffer.get("enabled") is not True
        or not isinstance(weight_buffer.get("bank_count"), int)
        or weight_buffer.get("bank_count", 0) < 2
        or weight_buffer.get("atomic_layer_switch") is not (target_layer_count > 1)
    ):
        errors.append("board integration does not prove the scoped double-buffered weight path")
    if isinstance(weight_buffer, dict):
        _require_evidence_refs(
            weight_buffer.get("evidence_refs"),
            "simulation.board_integration_contract.double_weight_buffer",
            generated_evidence_ids,
            errors,
        )

    activation = integration.get("activation_ping_pong")
    if not isinstance(activation, dict):
        errors.append("simulation.board_integration_contract.activation_ping_pong is missing")
    elif (
        activation.get("enabled") is not True
        or not isinstance(activation.get("bank_count"), int)
        or activation.get("bank_count", 0) < 2
        or activation.get("inter_layer_chaining") is not (target_layer_count > 1)
    ):
        errors.append("board integration does not prove the scoped ping-pong activation path")
    if isinstance(activation, dict):
        _require_evidence_refs(
            activation.get("evidence_refs"),
            "simulation.board_integration_contract.activation_ping_pong",
            generated_evidence_ids,
            errors,
        )

    prefetch = integration.get("background_prefetch")
    if not isinstance(prefetch, dict):
        errors.append("simulation.board_integration_contract.background_prefetch is missing")
    elif target_layer_count > 1:
        if (
            prefetch.get("enabled") is not True
            or prefetch.get("overlaps_current_layer_compute") is not True
            or str(prefetch.get("prefetch_scope") or "").lower()
            != "next_layer_weights"
        ):
            errors.append("board integration does not prove background next-layer weight prefetch overlap")
    elif (
        prefetch.get("enabled") is not False
        or prefetch.get("overlaps_current_layer_compute") is not False
        or str(prefetch.get("prefetch_scope") or "").lower() != "none"
    ):
        errors.append("single-layer terminal board schedule fabricates next-layer prefetch")
    if isinstance(prefetch, dict):
        _require_evidence_refs(
            prefetch.get("evidence_refs"),
            "simulation.board_integration_contract.background_prefetch",
            generated_evidence_ids,
            errors,
        )

    writeback = integration.get("final_writeback")
    axi_names = {str(row.get("name") or "") for row in axi_interfaces}
    if not isinstance(writeback, dict):
        errors.append("simulation.board_integration_contract.final_writeback is missing")
    elif (
        writeback.get("enabled") is not True
        or writeback.get("only_after_last_layer") is not True
        or str(writeback.get("axi_interface") or "") not in axi_names
    ):
        errors.append("board integration final writeback is not bound to a declared AXI interface after the last layer")
    if isinstance(writeback, dict):
        _require_evidence_refs(
            writeback.get("evidence_refs"),
            "simulation.board_integration_contract.final_writeback",
            generated_evidence_ids,
            errors,
        )

    spatial_pipeline = integration.get("intra_layer_spatial_pipeline")
    if not isinstance(spatial_pipeline, dict):
        errors.append("simulation.board_integration_contract.intra_layer_spatial_pipeline is missing")
    else:
        if (
            spatial_pipeline.get("preserved") is not True
            or spatial_pipeline.get("pipeline_semantics")
            != "elastic_rate_insensitive_token_pipeline"
            or spatial_pipeline.get(
                "different_tokens_overlap_across_required_dataflow"
            )
            is not True
            or spatial_pipeline.get("heterogeneous_stage_latency_supported")
            is not True
            or spatial_pipeline.get("stage_turnover_gaps_are_diagnostic")
            is not True
            or spatial_pipeline.get(
                "all_stages_same_cycle_concurrency_required"
            )
            is not False
            or spatial_pipeline.get("serial_leaf_execution") is not False
        ):
            errors.append(
                "board integration does not preserve elastic rate-insensitive intra-layer token pipeline semantics"
            )
        _require_evidence_refs(
            spatial_pipeline.get("evidence_refs"),
            "simulation.board_integration_contract.intra_layer_spatial_pipeline",
            generated_evidence_ids,
            errors,
        )
    return harness, errors


def _json_artifact_value(
    row: Any,
    simulation_path: Path,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    if not isinstance(row, dict):
        errors.append(f"{label} is missing")
        return {}
    before = len(errors)
    _verified_artifact(row, simulation_path, label, "path", errors)
    path_text = str(row.get("path") or "")
    if len(errors) != before or not path_text:
        return {}
    path = _resolve_path(path_text, simulation_path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object")
        return {}
    return value


def _self_contract_sha256(value: dict[str, Any], field: str) -> str:
    return canonical_contract_sha256(
        {key: item for key, item in value.items() if key != field}
    )


def _validate_runtime_constant_binding(
    simulation: dict[str, Any],
    simulation_path: Path,
    target_layer_count: Any,
    generated_evidence_ids: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Validate framework-owned runtime artifacts and generated loader binding."""

    errors: list[str] = []
    integration = simulation.get("board_integration_contract")
    integration = integration if isinstance(integration, dict) else {}
    expected_plan_file_sha = str(
        integration.get("board_memory_runtime_contract_sha256") or ""
    ).lower()
    if not expected_plan_file_sha:
        return {"declared": False, "enabled": False}, []

    binding = simulation.get("runtime_constant_binding")
    if not isinstance(binding, dict):
        return {}, [
            "simulation.runtime_constant_binding is required by the declared board memory/runtime contract"
        ]
    plan_row = binding.get("board_memory_runtime_contract")
    plan = _json_artifact_value(
        plan_row,
        simulation_path,
        "simulation.runtime_constant_binding.board_memory_runtime_contract",
        errors,
    )
    plan_file_sha = str(plan_row.get("sha256") or "").lower() if isinstance(plan_row, dict) else ""
    if plan_file_sha != expected_plan_file_sha:
        errors.append(
            "runtime constant binding does not bind the board integration runtime-plan file hash"
        )
    plan_validation = (
        plan.get("validation") if isinstance(plan.get("validation"), dict) else {}
    )
    if plan.get("status") != "ready" or plan_validation.get("status") != "pass":
        errors.append("bound board memory/runtime plan is not validation-pass")
    plan_contract_sha = str(plan.get("contract_sha256") or "").lower()
    if not plan_contract_sha or plan_contract_sha != canonical_contract_sha256(
        {
            key: value
            for key, value in plan.items()
            if key not in {"contract_sha256", "validation"}
        }
    ):
        errors.append("bound board memory/runtime plan contract hash is invalid")

    runtime = plan.get("runtime_constants")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("enabled"), bool):
        errors.append("bound board memory/runtime plan lacks explicit runtime_constants")
        return {"declared": True, "enabled": False}, errors
    enabled = runtime.get("enabled") is True
    if binding.get("enabled") is not enabled:
        errors.append("simulation.runtime_constant_binding.enabled differs from the runtime plan")
    implementation = integration.get("runtime_constants")
    if not isinstance(implementation, dict):
        errors.append("simulation.board_integration_contract.runtime_constants is missing")
        implementation = {}
    if implementation.get("enabled") is not enabled:
        errors.append("board integration runtime_constants.enabled differs from the runtime plan")
    if not enabled:
        for field in ("runtime_image_manifest", "runtime_image"):
            if binding.get(field) not in (None, {}):
                errors.append(f"disabled runtime constants must not bind {field}")
        return {
            "declared": True,
            "enabled": False,
            "plan_file_sha256": plan_file_sha,
            "plan_contract_sha256": plan_contract_sha,
        }, errors

    manifest_row = binding.get("runtime_image_manifest")
    manifest = _json_artifact_value(
        manifest_row,
        simulation_path,
        "simulation.runtime_constant_binding.runtime_image_manifest",
        errors,
    )
    manifest_file_sha = (
        str(manifest_row.get("sha256") or "").lower()
        if isinstance(manifest_row, dict)
        else ""
    )
    manifest_contract_sha = str(manifest.get("manifest_contract_sha256") or "").lower()
    if (
        not manifest_contract_sha
        or manifest_contract_sha
        != _self_contract_sha256(manifest, "manifest_contract_sha256")
    ):
        errors.append("bound runtime image manifest contract hash is invalid")
    if runtime.get("full_runtime_image_manifest") != manifest:
        errors.append("runtime plan embedded manifest differs from the bound runtime image manifest")
    expected_layers = (
        int(target_layer_count)
        if isinstance(target_layer_count, int) and not isinstance(target_layer_count, bool)
        else 0
    )
    if (
        manifest.get("status") != "pass"
        or manifest.get("accelerator_scope") != "transformer_blocks_only"
        or manifest.get("scope_coverage_complete") is not True
        or manifest.get("target_layer_count") != expected_layers
    ):
        errors.append("runtime image manifest is not complete for every target Transformer layer")

    image_row = binding.get("runtime_image")
    image_path_text = str(image_row.get("path") or "") if isinstance(image_row, dict) else ""
    if not isinstance(image_row, dict):
        errors.append("simulation.runtime_constant_binding.runtime_image is missing")
        image_path = Path()
    else:
        _verified_artifact(
            image_row,
            simulation_path,
            "simulation.runtime_constant_binding.runtime_image",
            "path",
            errors,
        )
        image_path = _resolve_path(image_path_text, simulation_path) if image_path_text else Path()
    image_sha = str(image_row.get("sha256") or "").lower() if isinstance(image_row, dict) else ""
    declared_manifest_image = str(manifest.get("path") or "")
    manifest_image_path = (
        _resolve_path(declared_manifest_image, simulation_path)
        if declared_manifest_image
        else Path()
    )
    image_size = image_path.stat().st_size if image_path_text and image_path.is_file() else -1
    if (
        not image_path_text
        or not declared_manifest_image
        or image_path.resolve() != manifest_image_path.resolve()
        or image_sha != str(manifest.get("image_sha256", manifest.get("sha256")) or "").lower()
        or image_size != manifest.get("total_bytes", manifest.get("byte_count"))
        or image_row.get("byte_count", image_row.get("total_bytes")) != image_size
    ):
        errors.append("runtime image file does not match its hash-bound manifest path/hash/size")
    artifacts = simulation.get("artifacts")
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    staged_image = artifacts.get("runtime_image")
    if not isinstance(staged_image, dict):
        errors.append("simulation.artifacts.runtime_image is missing")
    else:
        staged_path_text = str(staged_image.get("path") or "")
        staged_path = (
            _resolve_path(staged_path_text, simulation_path)
            if staged_path_text
            else Path()
        )
        if (
            not staged_path_text
            or staged_path.resolve() != image_path.resolve()
            or str(staged_image.get("sha256") or "").lower() != image_sha
            or staged_image.get("byte_count", staged_image.get("total_bytes"))
            != image_size
        ):
            errors.append(
                "simulation.artifacts.runtime_image differs from the runtime constant binding"
            )
    vcs = simulation.get("vcs")
    vcs = vcs if isinstance(vcs, dict) else {}
    plusargs = vcs.get("runtime_plusargs")
    if (
        not isinstance(plusargs, dict)
        or "runtime_image" not in {str(value) for value in plusargs.values()}
    ):
        errors.append("simulation VCS plusargs do not pass the bound runtime image")

    layer_bindings = _as_rows(manifest.get("layer_bindings"))
    schedule = _as_rows(runtime.get("load_schedule"))
    expected_indices = list(range(expected_layers))
    if [row.get("layer_index") for row in layer_bindings] != expected_indices:
        errors.append("runtime image manifest does not bind every target layer exactly once in order")
    if [row.get("layer_index") for row in schedule] != expected_indices:
        errors.append("runtime load schedule does not cover every target layer exactly once in order")
    manifest_fields = (
        "layer_index",
        "segment_id",
        "byte_offset",
        "byte_count",
        "word_offset",
        "word_count",
        "sha256",
    )
    for index, row in enumerate(schedule):
        expected = layer_bindings[index] if index < len(layer_bindings) else {}
        if any(row.get(field) != expected.get(field) for field in manifest_fields):
            errors.append(f"runtime load schedule[{index}] differs from the runtime image manifest")
        if row.get("complete_before_kernel_start") is not True:
            errors.append(f"runtime load schedule[{index}] does not require completion before kernel start")

    loader_abi_sha = canonical_contract_sha256(runtime.get("loader_abi", {}))
    load_schedule_sha = canonical_contract_sha256(schedule)
    expected_implementation = {
        "runtime_plan_contract_sha256": plan_contract_sha,
        "runtime_image_manifest_sha256": manifest_file_sha,
        "runtime_image_manifest_contract_sha256": manifest_contract_sha,
        "runtime_image_sha256": image_sha,
        "connected_runtime_stream_contract_sha256": runtime.get(
            "connected_runtime_stream_contract_sha256"
        ),
        "loader_abi_sha256": loader_abi_sha,
        "load_schedule_sha256": load_schedule_sha,
    }
    for field, expected in expected_implementation.items():
        if not expected or str(implementation.get(field) or "").lower() != str(expected).lower():
            errors.append(f"board integration runtime_constants.{field} does not bind the runtime authority")
    model_layer_count = simulation.get("model_layer_count", expected_layers)
    covers_full_model = model_layer_count == expected_layers
    if (
        implementation.get(
            "all_validation_layers", implementation.get("all_target_layers")
        )
        is not True
        or implementation.get("all_target_layers", covers_full_model)
        is not covers_full_model
        or implementation.get("complete_before_kernel_start") is not True
    ):
        errors.append(
            "board integration runtime loader does not require every validation layer before kernel start"
        )
    _require_evidence_refs(
        implementation.get("evidence_refs"),
        "simulation.board_integration_contract.runtime_constants",
        generated_evidence_ids,
        errors,
    )
    for field, expected in (
        ("full_runtime_image_manifest_sha256", manifest_file_sha),
        ("full_runtime_image_sha256", image_sha),
    ):
        if field in integration and str(integration.get(field) or "").lower() != expected:
            errors.append(f"simulation.board_integration_contract.{field} is stale")
    return {
        "declared": True,
        "enabled": True,
        "plan_file_sha256": plan_file_sha,
        "plan_contract_sha256": plan_contract_sha,
        "manifest_file_sha256": manifest_file_sha,
        "manifest_contract_sha256": manifest_contract_sha,
        "image_sha256": image_sha,
        "image_byte_count": image_size,
        "target_layer_count": expected_layers,
        "loader_abi_sha256": loader_abi_sha,
        "load_schedule_sha256": load_schedule_sha,
        "load_schedule": schedule,
    }, errors


def _validate_elaborated_hierarchy(
    simulation: dict[str, Any],
    simulation_path: Path,
    identity: dict[str, Any],
    closure_rows: list[dict[str, Any]],
    simulation_rows: list[dict[str, Any]],
    closure_hash: str,
    compile_hash: str,
    abi: dict[str, Any],
    abi_hash: str,
    multilayer_harness: dict[str, Any],
    external_fixture: dict[str, Any],
    dynamic_evidence: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    compute_slot_axi = _is_compute_slot_axi_validation(simulation)
    hierarchy = simulation.get("elaborated_hierarchy")
    if not isinstance(hierarchy, dict):
        return ["simulation.elaborated_hierarchy is missing"]
    _require_dynamic_refs(
        hierarchy.get("evidence_refs"),
        "simulation.elaborated_hierarchy",
        dynamic_evidence,
        "elaborated_hierarchy",
        errors,
    )
    if hierarchy.get("status") != "pass" or hierarchy.get("elaboration_exit_code") != 0:
        errors.append("simulation.elaborated_hierarchy is not a successful real-tool elaboration")
    if not str(hierarchy.get("elaboration_tool") or "").strip():
        errors.append("simulation.elaborated_hierarchy.elaboration_tool is missing")
    if str(hierarchy.get("source_closure_sha256") or "").lower() != closure_hash:
        errors.append("elaborated hierarchy does not bind the exact sample source closure hash")
    if str(hierarchy.get("compile_source_set_sha256") or "").lower() != compile_hash:
        errors.append("elaborated hierarchy does not bind the simulator compile source set hash")
    if str(hierarchy.get("compute_slot_abi_sha256") or "").lower() != abi_hash:
        errors.append("elaborated hierarchy does not bind the compute-slot ABI hash")

    log = hierarchy.get("elaboration_log")
    if not isinstance(log, dict):
        errors.append("simulation.elaborated_hierarchy.elaboration_log is missing")
    else:
        _verified_source_file(
            {**log, "source_id": log.get("source_id") or "elaboration_log"},
            simulation_path,
            "simulation.elaborated_hierarchy.elaboration_log",
            errors,
        )

    instances = _as_rows(hierarchy.get("instances"))
    if not instances:
        errors.append("simulation.elaborated_hierarchy.instances is empty")
        return errors
    exact_top = str(identity.get("top_module") or "")
    accelerator_module = str(multilayer_harness.get("top_module") or "")
    slot_module = str(abi.get("slot_module") or "")
    sample_rows = [
        row for row in instances
        if row.get("module") == exact_top and _instance_has_role(row, "exact_sample_top")
    ]
    accelerator_rows = [
        row for row in instances
        if row.get("module") == accelerator_module and _instance_has_role(row, "generated_accelerator")
    ]
    slot_rows = [
        row for row in instances
        if row.get("module") == slot_module and _instance_has_role(row, "compute_slot")
    ]
    if not compute_slot_axi and len(sample_rows) != 1:
        errors.append("elaborated hierarchy does not contain exactly one exact sample top instance")
    if len(accelerator_rows) != 1:
        errors.append("elaborated hierarchy does not contain exactly one generated accelerator instance")
    if len(slot_rows) != 1:
        errors.append("elaborated hierarchy does not contain exactly one compute-slot instance")

    harness_top = str(multilayer_harness.get("top_module") or "")
    single_layer_top = str(multilayer_harness.get("verified_single_layer_top_module") or "")
    harness_rows = [
        row for row in instances
        if row.get("module") == harness_top and _instance_has_role(row, "multilayer_harness")
    ]
    kernel_rows = [
        row for row in instances
        if row.get("module") == single_layer_top and _instance_has_role(row, "verified_single_layer_kernel")
    ]
    if len(harness_rows) != 1:
        errors.append("elaborated hierarchy does not contain exactly one multilayer harness instance")
    if len(kernel_rows) != 1:
        errors.append("elaborated hierarchy does not contain exactly one verified connected-layer kernel instance")

    external_rows = [
        row for row in instances if _instance_has_role(row, "external_memory_component")
    ]
    if not compute_slot_axi and len(external_rows) != 1:
        errors.append(
            "elaborated hierarchy does not contain exactly one external memory component instance"
        )
    elif not compute_slot_axi:
        external_row = external_rows[0]
        model_instance = external_fixture.get("model_instance", {})
        source_id = str(model_instance.get("source_id") or "")
        fixture_source = external_fixture.get("source_by_id", {}).get(source_id, {})
        expected_source_sha256 = str(
            fixture_source.get("sha256") or fixture_source.get("local_sha256") or ""
        ).lower()
        if (
            external_row.get("module") != model_instance.get("module")
            or str(external_row.get("source_id") or "") != source_id
            or str(external_row.get("source_sha256") or "").lower()
            != expected_source_sha256
        ):
            errors.append(
                "external memory hierarchy instance does not bind the selected fixture source/module/hash"
            )
        hierarchy_bindings = _declared_physical_bindings(
            external_row.get("physical_port_bindings"),
            "simulation.elaborated_hierarchy external memory physical_port_bindings",
            {
                str(row.get("name") or "")
                for row in _as_rows(
                    (
                        identity.get("timing_contract")
                        if isinstance(identity.get("timing_contract"), dict)
                        else {}
                    ).get("clock_domains")
                )
                if str(row.get("name") or "")
            },
            errors,
        )
        if hierarchy_bindings != external_fixture.get("physical_port_bindings", []):
            errors.append(
                "external memory hierarchy instance does not bind every physical provider pin"
            )
        if external_row.get("calibration_forced") is not False:
            errors.append("external memory hierarchy instance forces calibration")

    closure_hashes = {
        str(row.get("sha256") or row.get("local_sha256") or "").lower()
        for row in closure_rows
        if exact_top in _declared_modules(row)
    }
    generated_hashes = {
        str(row.get("sha256") or row.get("local_sha256") or "").lower()
        for row in simulation_rows
        if accelerator_module in _declared_modules(row) and _source_role(row) == "generated_accelerator"
    }
    slot_adapter_hashes = {
        str(row.get("sha256") or row.get("local_sha256") or "").lower()
        for row in simulation_rows
        if slot_module in _declared_modules(row) and _source_role(row) == "compute_slot_adapter"
    }
    certified_kernel_ids = {
        str(value) for value in multilayer_harness.get("certified_kernel_source_ids", []) if str(value)
    }
    certified_kernel_hashes = {
        str(row.get("sha256") or row.get("local_sha256") or "").lower()
        for row in simulation_rows
        if _source_id(row) in certified_kernel_ids
    }
    if (
        not compute_slot_axi
        and sample_rows
        and str(sample_rows[0].get("source_sha256") or "").lower()
        not in closure_hashes
    ):
        errors.append("exact sample top hierarchy instance is not bound to its closure source hash")
    if accelerator_rows and str(accelerator_rows[0].get("source_sha256") or "").lower() not in generated_hashes:
        errors.append("generated accelerator hierarchy instance is not bound to its compiled source hash")
    if slot_rows and str(slot_rows[0].get("source_sha256") or "").lower() not in slot_adapter_hashes:
        errors.append("compute-slot hierarchy instance is not bound to the generated slot-adapter source hash")
    if kernel_rows and str(kernel_rows[0].get("source_sha256") or "").lower() not in certified_kernel_hashes:
        errors.append("verified connected-layer kernel instance is not bound to its certified source hash")

    binding = hierarchy.get("compute_slot_binding")
    if not isinstance(binding, dict):
        errors.append("simulation.elaborated_hierarchy.compute_slot_binding is missing")
    else:
        sample_path = str(binding.get("exact_sample_top_instance_path") or "")
        slot_path = str(binding.get("compute_slot_instance_path") or "")
        accelerator_path = str(binding.get("generated_accelerator_instance_path") or "")
        if (
            not compute_slot_axi
            and sample_rows
            and sample_path != str(sample_rows[0].get("instance_path") or "")
        ):
            errors.append("compute-slot binding sample-top path does not match elaborated hierarchy")
        if slot_rows and slot_path != str(slot_rows[0].get("instance_path") or ""):
            errors.append("compute-slot binding slot path does not match elaborated hierarchy")
        if accelerator_rows and accelerator_path != str(accelerator_rows[0].get("instance_path") or ""):
            errors.append("compute-slot binding accelerator path does not match elaborated hierarchy")
        if compute_slot_axi:
            testbench_path = str(binding.get("testbench_instance_path") or "")
            if testbench_path and not (
                slot_path == testbench_path or slot_path.startswith(f"{testbench_path}.")
            ):
                errors.append("compute-slot instance is not below the board testbench")
            if not testbench_path and "." not in slot_path:
                errors.append("compute-slot instance path does not identify a testbench parent")
        elif sample_path and not (
            slot_path == sample_path or slot_path.startswith(f"{sample_path}.")
        ):
            errors.append("compute-slot instance is not below the exact sample top")
        if slot_path and not (accelerator_path == slot_path or accelerator_path.startswith(f"{slot_path}.")):
            errors.append("generated accelerator instance is not bound below the compute slot")
        if not _path_matches(slot_path, str(abi.get("slot_instance_path") or "")):
            errors.append("elaborated compute-slot path does not match compute_slot_abi.slot_instance_path")
        if not _path_matches(accelerator_path, str(multilayer_harness.get("instance_path") or "")):
            errors.append("elaborated accelerator path does not match multilayer_harness.instance_path")
        if binding.get("all_required_ports_bound") is not True:
            errors.append("elaborated compute-slot binding does not prove all required ports are bound")
        if binding.get("no_stub_or_behavioral_substitution") is not True:
            errors.append("elaborated compute-slot binding permits a stub or behavioral substitution")
        if str(binding.get("port_map_sha256") or "").lower() != compute_slot_port_map_fingerprint(abi):
            errors.append("elaborated compute-slot binding port-map hash does not match the ABI")

    unresolved = hierarchy.get("unresolved_modules")
    blackboxes = hierarchy.get("blackboxes")
    if not isinstance(unresolved, list) or unresolved:
        errors.append("simulation.elaborated_hierarchy.unresolved_modules must be an explicit empty list")
    if not isinstance(blackboxes, list) or blackboxes:
        errors.append("simulation.elaborated_hierarchy.blackboxes must be an explicit empty list")
    return errors


def _validate_protocol_monitors(
    simulation: dict[str, Any], axi_interfaces: list[dict[str, Any]], axi_hash: str
) -> list[str]:
    errors: list[str] = []
    contract = simulation.get("protocol_monitor_contract")
    if not isinstance(contract, dict):
        return ["simulation.protocol_monitor_contract is missing"]
    if contract.get("status") not in {"ready", "pass"}:
        errors.append("simulation.protocol_monitor_contract.status is neither ready nor pass")
    if str(contract.get("axi_interfaces_sha256") or "").lower() != axi_hash:
        errors.append("protocol monitor contract does not bind the complete AXI interface contract hash")
    if contract.get("all_axi_interfaces_covered") is not True:
        errors.append("protocol monitor contract does not cover all AXI interfaces")
    contract_hash = canonical_contract_sha256(contract)
    if str(simulation.get("protocol_monitor_contract_sha256") or "").lower() != contract_hash:
        errors.append("simulation.protocol_monitor_contract_sha256 does not match the structured monitor plan")
    monitors = _as_rows(contract.get("monitors"))
    by_interface: dict[str, list[dict[str, Any]]] = {}
    for row in monitors:
        by_interface.setdefault(str(row.get("interface") or ""), []).append(row)
    for interface in axi_interfaces:
        name = str(interface.get("name") or "")
        rows = by_interface.get(name, [])
        if len(rows) != 1:
            errors.append(f"protocol monitor contract must have exactly one aggregate monitor for AXI interface: {name}")
            continue
        row = rows[0]
        if not str(row.get("monitor_id") or "").strip() or not str(row.get("bound_instance_path") or "").strip():
            errors.append(f"protocol monitor for {name} lacks monitor_id/bound_instance_path")
        harness = simulation.get("multilayer_harness")
        harness_path = str(harness.get("instance_path") or "") if isinstance(harness, dict) else ""
        if not _path_matches(str(row.get("bound_instance_path") or ""), harness_path):
            errors.append(f"protocol monitor for {name} is not bound to the generated multilayer harness instance")
        if set(str(value).upper() for value in row.get("channels", [])) != {"AW", "W", "B", "AR", "R"}:
            errors.append(f"protocol monitor for {name} does not cover all five AXI channels")
        if row.get("fatal_on_violation") is not True:
            errors.append(f"protocol monitor for {name} is not fatal on protocol violations")
        checks = _as_rows(row.get("checks"))
        enabled_fatal = {
            str(check.get("kind") or "")
            for check in checks
            if check.get("enabled") is True and str(check.get("severity") or "").lower() == "fatal"
        }
        missing = sorted(REQUIRED_PROTOCOL_MONITOR_CHECKS - enabled_fatal)
        if missing:
            errors.append(f"protocol monitor for {name} lacks fatal checks: {missing}")
        report = row.get("structured_report")
        if not isinstance(report, dict):
            errors.append(f"protocol monitor for {name} lacks a structured_report contract")
        else:
            if not str(report.get("path") or "").strip() or not str(report.get("schema_version") or "").strip():
                errors.append(f"protocol monitor for {name} structured_report path/schema_version is missing")
            required_fields = set(map(str, report.get("required_fields", [])))
            if not REQUIRED_PROTOCOL_REPORT_FIELDS.issubset(required_fields):
                errors.append(f"protocol monitor for {name} structured_report lacks required fields")
    extra = sorted(set(by_interface) - {str(row.get("name") or "") for row in axi_interfaces})
    if extra:
        errors.append(f"protocol monitor contract references unknown AXI interfaces: {extra}")
    return errors


def _validate_execution_output_plan(
    simulation: dict[str, Any], axi_interfaces: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    outputs = simulation.get("execution_outputs")
    if not isinstance(outputs, dict):
        return {}, ["simulation.execution_outputs is missing"]
    for field in ("compile_log", "simulation_log"):
        row = outputs.get(field)
        if not isinstance(row, dict) or not _safe_relative_output_path(row.get("path")):
            errors.append(f"simulation.execution_outputs.{field}.path must be a safe relative path")
    progress = outputs.get("progress_event_log")
    if (
        not isinstance(progress, dict)
        or not _safe_relative_output_path(progress.get("path"))
        or progress.get("schema_version") != BOARD_PROGRESS_EVENT_SCHEMA_VERSION
    ):
        errors.append(
            "simulation.execution_outputs.progress_event_log path/schema_version is invalid"
        )
    hierarchy = outputs.get("elaborated_hierarchy_report")
    if (
        not isinstance(hierarchy, dict)
        or not _safe_relative_output_path(hierarchy.get("path"))
        or not str(hierarchy.get("schema_version") or "").strip()
    ):
        errors.append("simulation.execution_outputs.elaborated_hierarchy_report path/schema_version is invalid")
    ast_scan = outputs.get("testbench_ast_scan_report")
    testbench = simulation.get("testbench")
    scan = testbench.get("forbidden_construct_scan") if isinstance(testbench, dict) else None
    scan_report = scan.get("report_output") if isinstance(scan, dict) else None
    if isinstance(scan, dict) and scan.get("required") is True:
        if (
            not isinstance(ast_scan, dict)
            or not _safe_relative_output_path(ast_scan.get("path"))
            or not str(ast_scan.get("schema_version") or "").strip()
            or not isinstance(scan_report, dict)
            or str(ast_scan.get("path") or "") != str(scan_report.get("path") or "")
            or str(ast_scan.get("schema_version") or "") != str(scan_report.get("schema_version") or "")
        ):
            errors.append("simulation.execution_outputs.testbench_ast_scan_report does not bind the planned AST scan report")
    pipeline = outputs.get("pipeline_overlap_report")
    if (
        not isinstance(pipeline, dict)
        or not _safe_relative_output_path(pipeline.get("path"))
        or not str(pipeline.get("schema_version") or "").strip()
    ):
        errors.append("simulation.execution_outputs.pipeline_overlap_report path/schema_version is invalid")
    runtime_binding = simulation.get("runtime_constant_binding")
    runtime_enabled = (
        isinstance(runtime_binding, dict) and runtime_binding.get("enabled") is True
    )
    runtime_loader = outputs.get("runtime_loader_report")
    if runtime_enabled and (
        not isinstance(runtime_loader, dict)
        or not _safe_relative_output_path(runtime_loader.get("path"))
        or not str(runtime_loader.get("schema_version") or "").strip()
    ):
        errors.append(
            "simulation.execution_outputs.runtime_loader_report path/schema_version is invalid"
        )
    protocol = _as_rows(outputs.get(PROTOCOL_MONITOR_REPORT_OUTPUT_KEY))
    monitor_contract = simulation.get("protocol_monitor_contract")
    monitor_rows = _as_rows(monitor_contract.get("monitors")) if isinstance(monitor_contract, dict) else []
    by_interface: dict[str, list[dict[str, Any]]] = {}
    for row in protocol:
        by_interface.setdefault(str(row.get("interface") or ""), []).append(row)
    for interface in axi_interfaces:
        name = str(interface.get("name") or "")
        rows = by_interface.get(name, [])
        if len(rows) != 1:
            errors.append(f"execution output plan must declare exactly one protocol report for AXI interface: {name}")
            continue
        row = rows[0]
        if not _safe_relative_output_path(row.get("path")) or not str(row.get("schema_version") or "").strip():
            errors.append(f"execution output protocol report path/schema_version is invalid for AXI interface: {name}")
        monitor = next((item for item in monitor_rows if str(item.get("interface") or "") == name), {})
        monitor_report = monitor.get("structured_report") if isinstance(monitor, dict) else None
        if (
            not isinstance(monitor_report, dict)
            or str(monitor_report.get("path") or "") != str(row.get("path") or "")
            or str(monitor_report.get("schema_version") or "") != str(row.get("schema_version") or "")
        ):
            errors.append(f"execution output protocol report does not match the monitor contract for AXI interface: {name}")
    extra = sorted(set(by_interface) - {str(row.get("name") or "") for row in axi_interfaces})
    if extra:
        errors.append(f"execution output plan references unknown AXI interfaces: {extra}")
    return outputs, errors


def _planned_output_path(outputs: dict[str, Any], field: str, interface: str | None = None) -> str:
    if interface is None:
        row = outputs.get(field)
        return str(row.get("path") or "") if isinstance(row, dict) else ""
    rows = _as_rows(outputs.get(field))
    row = next((item for item in rows if str(item.get("interface") or "") == interface), {})
    return str(row.get("path") or "")


def _validate_dynamic_evidence(
    simulation: dict[str, Any], simulation_path: Path
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    records = _as_rows(simulation.get("dynamic_evidence_records"))
    if not records:
        return {}, ["simulation.dynamic_evidence_records is empty"]
    by_id: dict[str, dict[str, Any]] = {}
    allowed_kinds = {
        "compile_log",
        "simulation_log",
        "elaborated_hierarchy",
        "protocol_monitor_report",
        "pipeline_overlap_report",
        "progress_event_log",
        "testbench_ast_scan_report",
        "runtime_loader_report",
        "pipeline_boundary_observation_summary",
        "supplemental_debug_observation",
    }
    for index, row in enumerate(records):
        label = f"simulation.dynamic_evidence_records[{index}]"
        evidence_id = str(row.get("evidence_id") or "").strip()
        if not evidence_id or evidence_id in by_id:
            errors.append(f"{label}.evidence_id is missing or duplicated")
        if str(row.get("evidence_kind") or "") not in allowed_kinds:
            errors.append(f"{label}.evidence_kind is invalid")
        if not str(row.get("schema_version") or "").strip():
            errors.append(f"{label}.schema_version is missing")
        _verified_artifact(row, simulation_path, label, "path", errors)
        if evidence_id:
            by_id[evidence_id] = row
    return by_id, errors


def _require_dynamic_refs(
    value: Any,
    label: str,
    records: dict[str, dict[str, Any]],
    expected_kind: str,
    errors: list[str],
) -> None:
    ids = set(records)
    before = len(errors)
    _require_evidence_refs(value, label, ids, errors)
    if len(errors) != before:
        return
    for evidence_id in map(str, value):
        if str(records[evidence_id].get("evidence_kind") or "") != expected_kind:
            errors.append(f"{label}.evidence_refs includes {evidence_id} with the wrong dynamic evidence kind")


def _validate_execution_evidence(
    simulation: dict[str, Any],
    simulation_path: Path,
    identity_path: Path,
    closure_hash: str,
    compile_hash: str,
    abi_hash: str,
    timing_hash: str,
    axi_hash: str,
    outputs: dict[str, Any],
    dynamic_evidence: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    execution = simulation.get("execution_evidence")
    if not isinstance(execution, dict):
        return ["simulation.execution_evidence is missing"]
    if execution.get("status") != "pass":
        errors.append("simulation.execution_evidence.status is not pass")
    for field in ("tool", "tool_version", "job_id"):
        if not str(execution.get(field) or "").strip():
            errors.append(f"simulation.execution_evidence.{field} is missing")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(execution.get("command_sha256") or "")):
        errors.append("simulation.execution_evidence.command_sha256 is missing or invalid")
    expected_hashes = {
        "source_identity_sha256": sha256_file(identity_path) if identity_path.is_file() else "",
        "source_closure_sha256": closure_hash,
        "compile_source_set_sha256": compile_hash,
        "compute_slot_abi_sha256": abi_hash,
        "timing_contract_sha256": timing_hash,
        "axi_interfaces_sha256": axi_hash,
    }
    for field, expected in expected_hashes.items():
        if not expected or str(execution.get(field) or "").lower() != expected.lower():
            errors.append(f"simulation.execution_evidence.{field} does not bind the executed board contract")

    for field, plan_field in (("compile", "compile_log"), ("simulation", "simulation_log")):
        row = execution.get(field)
        if not isinstance(row, dict):
            errors.append(f"simulation.execution_evidence.{field} is missing")
            continue
        if row.get("exit_code") != 0:
            errors.append(f"simulation.execution_evidence.{field}.exit_code is not zero")
        if field == "simulation" and (row.get("completed") is not True or row.get("pass_marker_seen") is not True):
            errors.append("simulation execution did not complete with its manifest-bound pass marker")
        log = row.get("log")
        if not isinstance(log, dict):
            errors.append(f"simulation.execution_evidence.{field}.log is missing")
        else:
            _verified_artifact(log, simulation_path, f"simulation.execution_evidence.{field}.log", "path", errors)
            if str(log.get("relative_path") or "") != _planned_output_path(outputs, plan_field):
                errors.append(f"simulation.execution_evidence.{field}.log does not match the preflight output path")
            _require_dynamic_refs(
                log.get("evidence_refs"),
                f"simulation.execution_evidence.{field}.log",
                dynamic_evidence,
                "compile_log" if field == "compile" else "simulation_log",
                errors,
            )

    hierarchy_artifact = execution.get("elaborated_hierarchy_report")
    if not isinstance(hierarchy_artifact, dict):
        errors.append("simulation.execution_evidence.elaborated_hierarchy_report is missing")
    else:
        _verified_artifact(
            hierarchy_artifact,
            simulation_path,
            "simulation.execution_evidence.elaborated_hierarchy_report",
            "path",
            errors,
        )
        if str(hierarchy_artifact.get("relative_path") or "") != _planned_output_path(
            outputs, "elaborated_hierarchy_report"
        ):
            errors.append("executed elaborated hierarchy report does not match the preflight output path")
        _require_dynamic_refs(
            hierarchy_artifact.get("evidence_refs"),
            "simulation.execution_evidence.elaborated_hierarchy_report",
            dynamic_evidence,
            "elaborated_hierarchy",
            errors,
        )
        hierarchy_path_text = str(hierarchy_artifact.get("path") or "")
        if hierarchy_path_text:
            hierarchy_path = _resolve_path(hierarchy_path_text, simulation_path)
            if hierarchy_path.is_file():
                try:
                    actual_hierarchy = json.loads(hierarchy_path.read_text(encoding="utf-8"))
                except Exception:
                    actual_hierarchy = None
                if actual_hierarchy != simulation.get("elaborated_hierarchy"):
                    errors.append("inline elaborated_hierarchy does not exactly match the real-tool hierarchy report")
                expected_schema = str(
                    (outputs.get("elaborated_hierarchy_report") or {}).get("schema_version") or ""
                )
                if not isinstance(actual_hierarchy, dict) or actual_hierarchy.get("schema_version") != expected_schema:
                    errors.append("real-tool elaborated hierarchy report schema does not match the preflight plan")
    return errors


def _validate_pipeline_overlap_results(
    simulation: dict[str, Any],
    simulation_path: Path,
    outputs: dict[str, Any],
    dynamic_evidence: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    integration = simulation.get("board_integration_contract")
    results = simulation.get("pipeline_overlap_results")
    if not isinstance(integration, dict) or not isinstance(results, dict):
        return ["simulation.pipeline_overlap_results is missing"]
    _require_dynamic_refs(
        results.get("evidence_refs"),
        "simulation.pipeline_overlap_results",
        dynamic_evidence,
        "pipeline_overlap_report",
        errors,
    )
    if results.get("status") != "pass":
        errors.append("simulation.pipeline_overlap_results.status is not pass")
    if str(results.get("board_integration_contract_sha256") or "").lower() != canonical_contract_sha256(integration):
        errors.append("pipeline overlap results do not bind the board integration contract hash")
    if (
        results.get("pipeline_semantics")
        != "elastic_rate_insensitive_token_pipeline"
    ):
        errors.append("pipeline overlap results do not bind elastic rate-insensitive semantics")
    if results.get("required_dependency_overlap_complete") is not True:
        errors.append(
            "pipeline overlap results do not cover every required dataflow dependency"
        )
    if (
        results.get("all_planned_stages_participate_in_required_overlap")
        is not True
    ):
        errors.append(
            "pipeline overlap results do not involve every planned stage in required different-token overlap"
        )
    if results.get("token_order_preserved") is not True:
        errors.append("pipeline overlap results do not preserve token order")
    if results.get("serial_leaf_execution_observed") is not False:
        errors.append("pipeline overlap results permit serialized leaf execution")
    if results.get("stage_turnover_gaps_are_diagnostic") is not True:
        errors.append("pipeline overlap results incorrectly make stage turnover gaps functional gates")
    if results.get("all_stages_same_cycle_concurrency_required") is not False:
        errors.append("pipeline overlap results incorrectly require all stages in the same cycle")
    if results.get("whole_sequence_barrier_observed") is not False:
        errors.append("pipeline overlap results permit a whole-sequence operator barrier")
    expected_stage_count = results.get("expected_stage_count")
    observed_stage_count = results.get("observed_stage_count")
    if (
        not isinstance(expected_stage_count, int)
        or isinstance(expected_stage_count, bool)
        or expected_stage_count <= 0
        or observed_stage_count != expected_stage_count
    ):
        errors.append("pipeline overlap results do not observe the complete planned stage count")
    if (
        not isinstance(results.get("observed_different_token_overlap_count"), int)
        or isinstance(results.get("observed_different_token_overlap_count"), bool)
        or results.get("observed_different_token_overlap_count", 0) <= 0
    ):
        errors.append("pipeline overlap results have no different-token overlap witness")
    report = results.get("structured_trace_report")
    if not isinstance(report, dict):
        errors.append("pipeline overlap results lack a structured trace report")
    else:
        _verified_artifact(
            report,
            simulation_path,
            "simulation.pipeline_overlap_results.structured_trace_report",
            "path",
            errors,
        )
        if str(report.get("relative_path") or "") != _planned_output_path(outputs, "pipeline_overlap_report"):
            errors.append("pipeline overlap trace report does not match the preflight output path")
        report_path_text = str(report.get("path") or "")
        if report_path_text:
            report_path = _resolve_path(report_path_text, simulation_path)
            if report_path.is_file():
                try:
                    actual = json.loads(report_path.read_text(encoding="utf-8"))
                except Exception:
                    actual = None
                expected_projection = {
                    "status": results.get("status"),
                    "pipeline_semantics": results.get("pipeline_semantics"),
                    "required_dependency_overlap_complete": results.get(
                        "required_dependency_overlap_complete"
                    ),
                    "all_planned_stages_participate_in_required_overlap": results.get(
                        "all_planned_stages_participate_in_required_overlap"
                    ),
                    "token_order_preserved": results.get("token_order_preserved"),
                    "serial_leaf_execution_observed": results.get("serial_leaf_execution_observed"),
                    "observed_different_token_overlap_count": results.get(
                        "observed_different_token_overlap_count"
                    ),
                    "stage_turnover_gaps_are_diagnostic": results.get(
                        "stage_turnover_gaps_are_diagnostic"
                    ),
                    "all_stages_same_cycle_concurrency_required": results.get(
                        "all_stages_same_cycle_concurrency_required"
                    ),
                    "diagnostic_maximum_concurrent_stage_count": results.get(
                        "diagnostic_maximum_concurrent_stage_count"
                    ),
                    "all_spatial_stages_concurrent_observed": results.get(
                        "all_spatial_stages_concurrent_observed"
                    ),
                    "whole_sequence_barrier_observed": results.get("whole_sequence_barrier_observed"),
                    "expected_stage_count": results.get("expected_stage_count"),
                    "observed_stage_count": results.get("observed_stage_count"),
                }
                actual_projection = {
                    key: actual.get(key) for key in expected_projection
                } if isinstance(actual, dict) else None
                if actual_projection != expected_projection:
                    errors.append("inline pipeline overlap results differ from the real trace report")
    return errors


def _validate_runtime_loader_results(
    simulation: dict[str, Any],
    simulation_path: Path,
    outputs: dict[str, Any],
    dynamic_evidence: dict[str, dict[str, Any]],
    authority: dict[str, Any],
) -> list[str]:
    if authority.get("enabled") is not True:
        return []
    errors: list[str] = []
    results = simulation.get("runtime_loader_results")
    if not isinstance(results, dict):
        return ["simulation.runtime_loader_results is missing"]
    _require_dynamic_refs(
        results.get("evidence_refs"),
        "simulation.runtime_loader_results",
        dynamic_evidence,
        "runtime_loader_report",
        errors,
    )
    if results.get("status") != "pass":
        errors.append("simulation.runtime_loader_results.status is not pass")
    for field in (
        "runtime_plan_contract_sha256",
        "runtime_image_manifest_contract_sha256",
        "runtime_image_sha256",
        "loader_abi_sha256",
        "load_schedule_sha256",
    ):
        authority_field = {
            "runtime_plan_contract_sha256": "plan_contract_sha256",
            "runtime_image_manifest_contract_sha256": "manifest_contract_sha256",
            "runtime_image_sha256": "image_sha256",
            "loader_abi_sha256": "loader_abi_sha256",
            "load_schedule_sha256": "load_schedule_sha256",
        }[field]
        if str(results.get(field) or "").lower() != str(
            authority.get(authority_field) or ""
        ).lower():
            errors.append(f"runtime loader results do not bind {field}")
    target_layers = int(authority.get("target_layer_count") or 0)
    if results.get("target_layer_count") != target_layers:
        errors.append("runtime loader results target_layer_count differs from the runtime authority")
    if results.get("all_layers_loaded_exactly_once") is not True:
        errors.append("runtime loader results do not prove every layer was loaded exactly once")
    if results.get("kernel_start_before_load_complete_observed") is not False:
        errors.append("runtime loader results observed or did not exclude an early kernel start")

    expected_schedule = _as_rows(authority.get("load_schedule"))
    layers = _as_rows(results.get("layers"))
    if [row.get("layer_index") for row in layers] != list(range(target_layers)):
        errors.append("runtime loader results do not contain every target layer exactly once in order")
    for index, expected in enumerate(expected_schedule):
        label = f"simulation.runtime_loader_results.layers[{index}]"
        if index >= len(layers):
            errors.append(f"{label} is missing")
            continue
        row = layers[index]
        expected_words = expected.get("word_count")
        expected_start = expected.get("loader_address_start")
        expected_last = expected.get("last_word_address")
        for field, value in (
            ("layer_index", expected.get("layer_index")),
            ("segment_id", expected.get("segment_id")),
            ("segment_sha256", expected.get("sha256")),
            ("expected_word_count", expected_words),
            ("accepted_word_count", expected_words),
            ("accepted_address_count", expected.get("loader_address_count")),
            ("first_accepted_address", expected_start),
            ("last_accepted_address", expected_last),
        ):
            actual = str(row.get(field)).lower() if field == "segment_sha256" else row.get(field)
            reference = str(value).lower() if field == "segment_sha256" else value
            if actual != reference:
                errors.append(f"{label}.{field} differs from the runtime load schedule")
        for field in (
            "address_sequence_contiguous",
            "address_sequence_unique",
            "data_matches_image_segment",
            "last_asserted_on_final_accept",
        ):
            if row.get(field) is not True:
                errors.append(f"{label}.{field} is not true")
        load_complete = row.get("load_complete_cycle")
        kernel_start = row.get("kernel_start_cycle")
        if (
            not isinstance(load_complete, int)
            or isinstance(load_complete, bool)
            or not isinstance(kernel_start, int)
            or isinstance(kernel_start, bool)
            or load_complete < 0
            or kernel_start <= load_complete
        ):
            errors.append(f"{label} does not prove load_complete_cycle < kernel_start_cycle")

    report = results.get("structured_report")
    if not isinstance(report, dict):
        errors.append("runtime loader results lack a structured report artifact")
        return errors
    _verified_artifact(
        report,
        simulation_path,
        "simulation.runtime_loader_results.structured_report",
        "path",
        errors,
    )
    if str(report.get("relative_path") or "") != _planned_output_path(
        outputs, "runtime_loader_report"
    ):
        errors.append("runtime loader report does not match the preflight output path")
    report_path_text = str(report.get("path") or "")
    if report_path_text:
        report_path = _resolve_path(report_path_text, simulation_path)
        if report_path.is_file():
            try:
                actual = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                actual = None
            fields = (
                "status",
                "runtime_plan_contract_sha256",
                "runtime_image_manifest_contract_sha256",
                "runtime_image_sha256",
                "loader_abi_sha256",
                "load_schedule_sha256",
                "target_layer_count",
                "all_layers_loaded_exactly_once",
                "kernel_start_before_load_complete_observed",
                "layers",
            )
            expected_projection = {field: results.get(field) for field in fields}
            actual_projection = (
                {field: actual.get(field) for field in fields}
                if isinstance(actual, dict)
                else None
            )
            if actual_projection != expected_projection:
                errors.append("inline runtime loader results differ from the real trace report")
    return errors


def _validate_testbench_scan_result(
    simulation: dict[str, Any],
    simulation_path: Path,
    outputs: dict[str, Any],
    dynamic_evidence: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    compute_slot_axi = _is_compute_slot_axi_validation(simulation)
    testbench = simulation.get("testbench")
    plan = testbench.get("forbidden_construct_scan") if isinstance(testbench, dict) else None
    result = simulation.get("testbench_forbidden_construct_scan_result")
    if not isinstance(plan, dict) or not isinstance(result, dict):
        return ["simulation.testbench_forbidden_construct_scan_result is missing"]
    if result.get("status") != "pass" or result.get("exit_code") != 0:
        errors.append("executed testbench HDL-AST scan is not pass with exit_code=0")
    plan_tool = plan.get("tool") if isinstance(plan.get("tool"), dict) else {}
    if result.get("tool") != plan_tool.get("name") or not str(result.get("tool_version") or "").strip():
        errors.append("executed testbench HDL-AST scan tool identity/version does not match the plan")
    if str(result.get("source_sha256") or "").lower() != str(testbench.get("sha256") or "").lower():
        errors.append("executed testbench HDL-AST scan does not bind the testbench source hash")
    if str(result.get("invocation_sha256") or "").lower() != canonical_contract_sha256(plan.get("invocation", {})):
        errors.append("executed testbench HDL-AST scan does not bind the planned argv invocation")
    for field in ("forced_calibration_assignments", "synthetic_latency_constructs"):
        if not isinstance(result.get(field), list) or result.get(field):
            errors.append(f"executed testbench HDL-AST scan {field} must be an explicit empty list")
    behavioral_models = result.get("behavioral_memory_models")
    if not isinstance(behavioral_models, list) or (
        not compute_slot_axi and behavioral_models
    ):
        errors.append(
            "executed testbench HDL-AST scan behavioral_memory_models must be "
            + ("an explicit list" if compute_slot_axi else "an explicit empty list")
        )
    _require_dynamic_refs(
        result.get("evidence_refs"),
        "simulation.testbench_forbidden_construct_scan_result",
        dynamic_evidence,
        "testbench_ast_scan_report",
        errors,
    )
    report = result.get("structured_report")
    if not isinstance(report, dict):
        errors.append("executed testbench HDL-AST scan structured_report is missing")
        return errors
    _verified_artifact(
        report,
        simulation_path,
        "simulation.testbench_forbidden_construct_scan_result.structured_report",
        "path",
        errors,
    )
    if str(report.get("relative_path") or "") != _planned_output_path(outputs, "testbench_ast_scan_report"):
        errors.append("testbench HDL-AST scan report does not match the preflight output path")
    report_path_text = str(report.get("path") or "")
    if report_path_text:
        report_path = _resolve_path(report_path_text, simulation_path)
        if report_path.is_file():
            try:
                actual = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                actual = None
            fields = (
                "status",
                "tool",
                "tool_version",
                "exit_code",
                "source_sha256",
                "invocation_sha256",
                "forced_calibration_assignments",
                "behavioral_memory_models",
                "synthetic_latency_constructs",
            )
            expected_projection = {field: result.get(field) for field in fields}
            actual_projection = {field: actual.get(field) for field in fields} if isinstance(actual, dict) else None
            if actual_projection != expected_projection:
                errors.append("inline testbench HDL-AST scan result differs from the real parser report")
    return errors


def _validate_protocol_monitor_results(
    simulation: dict[str, Any],
    simulation_path: Path,
    axi_interfaces: list[dict[str, Any]],
    outputs: dict[str, Any],
    dynamic_evidence: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    contract = simulation.get("protocol_monitor_contract")
    results = simulation.get("protocol_monitor_results")
    if not isinstance(contract, dict) or not isinstance(results, dict):
        return ["simulation.protocol_monitor_results is missing"]
    if results.get("status") != "pass" or results.get("all_axi_interfaces_covered") is not True:
        errors.append("simulation.protocol_monitor_results is not pass for all AXI interfaces")
    if str(results.get("protocol_monitor_contract_sha256") or "").lower() != canonical_contract_sha256(contract):
        errors.append("protocol monitor results do not bind the monitor contract hash")
    rows = _as_rows(results.get("interfaces"))
    by_interface: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_interface.setdefault(str(row.get("interface") or ""), []).append(row)
    for interface in axi_interfaces:
        name = str(interface.get("name") or "")
        matches = by_interface.get(name, [])
        if len(matches) != 1:
            errors.append(f"protocol monitor results must contain exactly one result for AXI interface: {name}")
            continue
        row = matches[0]
        _require_dynamic_refs(
            row.get("evidence_refs"),
            f"simulation.protocol_monitor_results[{name}]",
            dynamic_evidence,
            "protocol_monitor_report",
            errors,
        )
        if row.get("status") != "pass":
            errors.append(f"protocol monitor result is not pass for AXI interface: {name}")
        if not isinstance(row.get("violations"), list) or row.get("violations"):
            errors.append(f"protocol monitor result has violations or lacks an explicit empty list: {name}")
        counts = row.get("transaction_counts")
        if not isinstance(counts, dict) or any(
            not isinstance(counts.get(channel), int) or counts.get(channel, 0) <= 0
            for channel in ("aw", "w", "b", "ar", "r")
        ):
            errors.append(f"protocol monitor result lacks positive five-channel transaction counts: {name}")
        report = row.get("structured_report")
        if not isinstance(report, dict):
            errors.append(f"protocol monitor result lacks a structured report artifact: {name}")
        else:
            _verified_artifact(
                report,
                simulation_path,
                f"simulation.protocol_monitor_results[{name}].structured_report",
                "path",
                errors,
            )
            if str(report.get("relative_path") or "") != _planned_output_path(
                outputs, "protocol_monitor_reports", name
            ):
                errors.append(f"protocol monitor report does not match the preflight output path: {name}")
            report_path_text = str(report.get("path") or "")
            if report_path_text:
                report_path = _resolve_path(report_path_text, simulation_path)
                if report_path.is_file():
                    try:
                        actual = json.loads(report_path.read_text(encoding="utf-8"))
                    except Exception:
                        actual = None
                    expected_projection = {
                        "status": row.get("status"),
                        "violations": row.get("violations"),
                        "transaction_counts": row.get("transaction_counts"),
                    }
                    actual_projection = {
                        "status": actual.get("status"),
                        "violations": actual.get("violations"),
                        "transaction_counts": actual.get("transaction_counts"),
                    } if isinstance(actual, dict) else None
                    if actual_projection != expected_projection:
                        errors.append(f"inline protocol result differs from the real monitor report: {name}")
    extra = sorted(set(by_interface) - {str(row.get("name") or "") for row in axi_interfaces})
    if extra:
        errors.append(f"protocol monitor results reference unknown AXI interfaces: {extra}")
    return errors


def _load_json_object(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.is_file():
        return {}, [f"{label} is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, [f"{label} is not valid JSON: {exc}"]
    if not isinstance(value, dict):
        return {}, [f"{label} must be a JSON object"]
    return value, []


def _validate_exact_board_contract(
    identity_path: Path, simulation_path: Path, *, require_execution: bool
) -> dict[str, Any]:
    """Validate shared preflight evidence and optional post-run evidence."""

    identity_path = identity_path.resolve()
    simulation_path = simulation_path.resolve()
    identity, identity_load_errors = _load_json_object(identity_path, "board source identity")
    simulation, simulation_load_errors = _load_json_object(simulation_path, "board simulation manifest")
    compute_slot_axi = (
        not simulation_load_errors and _is_compute_slot_axi_validation(simulation)
    )
    sections: list[tuple[str, list[str], dict[str, Any]]] = []

    if not identity_load_errors and not simulation_load_errors:
        (
            frozen_identity_attestation_valid,
            frozen_identity_attestation_errors,
            frozen_identity_attestation_details,
        ) = validate_frozen_compute_slot_identity_attestation(
            identity,
            identity_path,
            simulation,
            simulation_path,
        )
    else:
        frozen_identity_attestation_valid = False
        frozen_identity_attestation_errors = []
        frozen_identity_attestation_details = {"required": False}
    sections.append(
        (
            "frozen_compute_slot_identity_attestation",
            frozen_identity_attestation_errors,
            frozen_identity_attestation_details,
        )
    )

    identity_errors = list(identity_load_errors)
    if not identity_errors:
        if identity.get("status") != "pass":
            identity_errors.append("identity.status is not pass")
        if identity.get("exact_user_sample_wrapper") is not True:
            identity_errors.append("identity.exact_user_sample_wrapper is not true")
    sections.append(("exact_sample_identity", identity_errors, {"path": str(identity_path)}))

    if not identity_load_errors:
        evidence_ids, errors = _validate_discovery_provenance(identity, identity_path)
        if frozen_identity_attestation_valid:
            identity_fact_path_text = str(identity.get("vivado_facts_path") or "")
            identity_fact_path = (
                _resolve_path(identity_fact_path_text, identity_path)
                if identity_fact_path_text
                else Path()
            )
            errors = [
                error
                for error in errors
                if not (
                    "artifact hash does not match:" in error
                    and identity_fact_path_text
                    and str(identity_fact_path.resolve()) in error
                )
            ]
    else:
        evidence_ids, errors = set(), ["LLM discovery provenance cannot be checked without a valid identity document"]
    sections.append(("llm_discovery_and_source_evidence", errors, {"evidence_count": len(evidence_ids)}))

    closure_rows: list[dict[str, Any]] = []
    closure_hash = ""
    if not identity_load_errors:
        closure_rows, closure_hash, errors, details = _validate_source_closure(identity, identity_path, evidence_ids)
    else:
        errors, details = ["source closure cannot be checked without a valid identity document"], {}
    sections.append(("recursive_simulation_source_closure", errors, details))

    if not identity_load_errors:
        errors, details = _validate_progressive_selector_coverage(
            identity, identity_path, closure_rows
        )
        if frozen_identity_attestation_valid:
            errors = []
            details = {
                **details,
                "reused_from_frozen_identity_attestation": True,
            }
    else:
        errors, details = [
            "progressive selector coverage cannot be checked without a valid identity document"
        ], {}
    sections.append(("progressive_selector_full_coverage", errors, details))

    if not identity_load_errors:
        abi, abi_hash, errors = _validate_compute_slot_abi(identity, evidence_ids)
    else:
        abi, abi_hash, errors = {}, "", ["compute-slot ABI cannot be checked without a valid identity document"]
    sections.append(("compute_slot_abi", errors, {"sha256": abi_hash}))

    closure_ids = {_source_id(row) for row in closure_rows}
    if not identity_load_errors:
        timing, timing_hash, errors = _validate_timing_contract(identity, closure_ids, evidence_ids, abi)
    else:
        timing, timing_hash, errors = {}, "", ["timing contract cannot be checked without a valid identity document"]
    sections.append(("clock_reset_calibration_timing", errors, {"sha256": timing_hash}))

    if not identity_load_errors:
        axi_interfaces, axi_hash, errors = _validate_axi_contract(identity, timing, evidence_ids)
    else:
        axi_interfaces, axi_hash, errors = [], "", ["AXI contract cannot be checked without a valid identity document"]
    sections.append(("complete_axi_interfaces", errors, {"sha256": axi_hash, "interface_count": len(axi_interfaces)}))

    simulation_identity_errors = list(simulation_load_errors)
    if not simulation_load_errors:
        validation_mode = simulation.get("validation_mode")
        if validation_mode not in (
            None,
            EXACT_SAMPLE_PHYSICAL_DDR_VALIDATION_MODE,
            COMPUTE_SLOT_AXI_VALIDATION_MODE,
        ):
            simulation_identity_errors.append(
                f"simulation.validation_mode is unsupported: {validation_mode}"
            )
        allowed_status = {"pass"} if require_execution else {"ready", "pass"}
        if simulation.get("status") not in allowed_status:
            simulation_identity_errors.append(
                "simulation.status is not " + ("pass" if require_execution else "ready/pass")
            )
        if simulation.get("exact_sample_wrapper_unmodified") is not True:
            simulation_identity_errors.append("simulation.exact_sample_wrapper_unmodified is not true")
        expected_identity_hash = sha256_file(identity_path) if identity_path.is_file() else ""
        if str(simulation.get("source_identity_sha256") or "").lower() != expected_identity_hash:
            simulation_identity_errors.append("simulation.source_identity_sha256 does not bind the current identity document")
        for field, expected in (
            ("compute_slot_abi_sha256", abi_hash),
            ("timing_contract_sha256", timing_hash),
            ("axi_interfaces_sha256", axi_hash),
        ):
            if str(simulation.get(field) or "").lower() != expected or not expected:
                simulation_identity_errors.append(f"simulation.{field} does not bind the identity contract")
    sections.append(("simulation_identity_binding", simulation_identity_errors, {"path": str(simulation_path)}))

    if not simulation_load_errors and not compute_slot_axi:
        external_fixture, errors = _validate_external_simulation_fixture(
            simulation, simulation_path, identity
        )
    elif compute_slot_axi:
        external_fixture, errors = {}, []
    else:
        external_fixture, errors = {}, [
            "external simulation fixture cannot be checked without a valid simulation manifest"
        ]
    sections.append(
        (
            "external_simulation_fixture_binding",
            errors,
            {
                "required": not compute_slot_axi,
                "contract_sha256": external_fixture.get("contract_sha256"),
                "selected_source_ids": external_fixture.get("selected_source_ids", []),
            },
        )
    )

    if not simulation_load_errors:
        simulation_rows, compile_hash, errors, compile_details = _validate_simulation_sources(
            simulation,
            simulation_path,
            closure_rows,
            closure_hash,
            abi,
            external_fixture,
        )
    else:
        simulation_rows, compile_hash, errors, compile_details = [], "", ["compile source set cannot be checked without a valid simulation manifest"], {}
    sections.append(
        (
            "simulation_compile_source_set",
            errors,
            {"sha256": compile_hash, "source_count": len(simulation_rows), **compile_details},
        )
    )

    if not simulation_load_errors and not identity_load_errors:
        vcs_compile_plan_hash, errors, details = _validate_vcs_compile_plan(
            simulation,
            simulation_path,
            identity,
            identity_path,
            compile_details,
            external_fixture,
            frozen_identity_attestation_valid,
        )
    else:
        vcs_compile_plan_hash, errors, details = "", [
            "VCS compile plan cannot be checked without valid identity and simulation manifests"
        ], {}
    sections.append(("canonical_vcs_compile_plan", errors, details))

    if not simulation_load_errors:
        generated_evidence_ids, errors = _validate_generated_evidence(
            simulation,
            simulation_rows,
            set(compile_details.get("generated_source_ids", [])),
        )
    else:
        generated_evidence_ids, errors = set(), ["generated RTL evidence cannot be checked without a valid simulation manifest"]
    sections.append(("generated_rtl_evidence", errors, {"evidence_count": len(generated_evidence_ids)}))

    if not simulation_load_errors:
        errors = _validate_testbench_contract(
            simulation,
            identity,
            closure_rows,
            simulation_rows,
            abi,
            abi_hash,
            timing_hash,
            axi_hash,
            set(compile_details.get("preserved_sample_source_ids", [])),
            generated_evidence_ids,
            require_debug_observability=require_execution,
        )
    else:
        errors = ["testbench contract cannot be checked without a valid simulation manifest"]
    sections.append(("exact_sample_testbench_contract", errors, {}))

    if not simulation_load_errors:
        multilayer_harness, errors = _validate_multilayer_board_integration(
            simulation,
            simulation_path,
            simulation_rows,
            closure_hash,
            abi_hash,
            timing_hash,
            axi_interfaces,
            generated_evidence_ids,
        )
    else:
        multilayer_harness, errors = {}, ["multilayer board integration cannot be checked without a valid simulation manifest"]
    sections.append(("multilayer_board_integration", errors, {}))

    if not simulation_load_errors:
        runtime_authority, errors = _validate_runtime_constant_binding(
            simulation,
            simulation_path,
            simulation.get("target_layer_count"),
            generated_evidence_ids,
        )
    else:
        runtime_authority, errors = {}, [
            "runtime constant binding cannot be checked without a valid simulation manifest"
        ]
    sections.append(
        (
            "runtime_constant_image_and_loader_binding",
            errors,
            {
                "enabled": runtime_authority.get("enabled") is True,
                "runtime_image_sha256": runtime_authority.get("image_sha256"),
            },
        )
    )

    if not simulation_load_errors:
        errors = _validate_protocol_monitors(simulation, axi_interfaces, axi_hash)
    else:
        errors = ["protocol monitor contract cannot be checked without a valid simulation manifest"]
    sections.append(("structured_axi_protocol_monitors", errors, {}))

    if not simulation_load_errors:
        execution_outputs, errors = _validate_execution_output_plan(simulation, axi_interfaces)
    else:
        execution_outputs, errors = {}, ["execution output plan cannot be checked without a valid simulation manifest"]
    sections.append(("real_tool_execution_output_plan", errors, {}))

    if require_execution:
        if not simulation_load_errors:
            dynamic_evidence, errors = _validate_dynamic_evidence(simulation, simulation_path)
        else:
            dynamic_evidence, errors = {}, ["dynamic evidence cannot be checked without a valid simulation manifest"]
        sections.append(("dynamic_real_tool_evidence", errors, {"evidence_count": len(dynamic_evidence)}))

        testbench_scan = (
            simulation.get("testbench", {}).get("forbidden_construct_scan", {})
            if isinstance(simulation.get("testbench"), dict)
            else {}
        )
        if not simulation_load_errors and testbench_scan.get("required") is True:
            errors = _validate_testbench_scan_result(
                simulation, simulation_path, execution_outputs, dynamic_evidence
            )
            sections.append(("executed_testbench_hdl_ast_scan", errors, {}))
        elif simulation_load_errors:
            errors = ["testbench HDL-AST scan result cannot be checked without a valid simulation manifest"]
            sections.append(("executed_testbench_hdl_ast_scan", errors, {}))

        if not simulation_load_errors:
            errors = _validate_execution_evidence(
                simulation,
                simulation_path,
                identity_path,
                closure_hash,
                compile_hash,
                abi_hash,
                timing_hash,
                axi_hash,
                execution_outputs,
                dynamic_evidence,
            )
        else:
            errors = ["execution evidence cannot be checked without a valid simulation manifest"]
        sections.append(("real_tool_execution_identity_and_logs", errors, {}))

        if not simulation_load_errors and not identity_load_errors:
            errors = _validate_elaborated_hierarchy(
                simulation,
                simulation_path,
                identity,
                closure_rows,
                simulation_rows,
                closure_hash,
                compile_hash,
                abi,
                abi_hash,
                multilayer_harness,
                external_fixture,
                dynamic_evidence,
            )
        else:
            errors = ["elaborated hierarchy cannot be checked without valid identity and simulation manifests"]
        sections.append(("elaborated_exact_top_and_accelerator_binding", errors, {}))

        if not simulation_load_errors:
            errors = _validate_protocol_monitor_results(
                simulation,
                simulation_path,
                axi_interfaces,
                execution_outputs,
                dynamic_evidence,
            )
        else:
            errors = ["protocol monitor results cannot be checked without a valid simulation manifest"]
        sections.append(("dynamic_axi_protocol_monitor_results", errors, {}))

        if not simulation_load_errors:
            errors = _validate_pipeline_overlap_results(
                simulation, simulation_path, execution_outputs, dynamic_evidence
            )
        else:
            errors = ["pipeline overlap results cannot be checked without a valid simulation manifest"]
        sections.append(("dynamic_intra_layer_spatial_pipeline_overlap", errors, {}))

        if not simulation_load_errors:
            errors = _validate_runtime_loader_results(
                simulation,
                simulation_path,
                execution_outputs,
                dynamic_evidence,
                runtime_authority,
            )
        else:
            errors = [
                "runtime loader results cannot be checked without a valid simulation manifest"
            ]
        sections.append(("dynamic_runtime_loader_consumption", errors, {}))

    checks = [
        {
            "name": name,
            "status": "fail" if errors else "pass",
            **details,
            "blockers": errors,
        }
        for name, errors, details in sections
    ]
    blockers = [error for _, errors, _ in sections for error in errors]
    return {
        "schema_version": SCHEMA_VERSION if require_execution else PREFLIGHT_SCHEMA_VERSION,
        "phase": "post_run_acceptance" if require_execution else "preflight",
        "status": "fail" if blockers else "pass",
        "identity_path": str(identity_path),
        "simulation_manifest_path": str(simulation_path),
        "source_closure_sha256": closure_hash or None,
        "compile_source_set_sha256": compile_hash or None,
        "vcs_compile_plan_sha256": vcs_compile_plan_hash or None,
        **compile_details,
        "checks": checks,
        "blockers": blockers,
    }


def validate_exact_board_preflight(
    identity_path: Path, simulation_path: Path
) -> dict[str, Any]:
    """Validate everything required before launching the real board simulator."""

    return _validate_exact_board_contract(identity_path, simulation_path, require_execution=False)


def validate_exact_board_identity(identity_path: Path) -> dict[str, Any]:
    """Validate LLM-discovered sample-project facts before board RTL generation."""

    identity_path = identity_path.resolve()
    identity, load_errors = _load_json_object(identity_path, "board source identity")
    sections: list[tuple[str, list[str], dict[str, Any]]] = []

    errors = list(load_errors)
    if not errors:
        if identity.get("status") != "pass":
            errors.append("identity.status is not pass")
        if identity.get("exact_user_sample_wrapper") is not True:
            errors.append("identity.exact_user_sample_wrapper is not true")
    sections.append(("exact_sample_identity", errors, {"path": str(identity_path)}))

    if not load_errors:
        evidence_ids, errors = _validate_discovery_provenance(identity, identity_path)
    else:
        evidence_ids, errors = set(), [
            "LLM discovery provenance cannot be checked without a valid identity document"
        ]
    sections.append(
        ("llm_discovery_and_source_evidence", errors, {"evidence_count": len(evidence_ids)})
    )

    if not load_errors:
        closure_rows, closure_hash, errors, details = _validate_source_closure(
            identity, identity_path, evidence_ids
        )
    else:
        closure_rows, closure_hash = [], ""
        errors, details = ["source closure cannot be checked without a valid identity document"], {}
    sections.append(("recursive_simulation_source_closure", errors, details))

    if not load_errors:
        errors, details = _validate_progressive_selector_coverage(
            identity, identity_path, closure_rows
        )
    else:
        errors, details = [
            "progressive selector coverage cannot be checked without a valid identity document"
        ], {}
    sections.append(("progressive_selector_full_coverage", errors, details))

    if not load_errors:
        abi, abi_hash, errors = _validate_compute_slot_abi(identity, evidence_ids)
    else:
        abi, abi_hash, errors = {}, "", [
            "compute-slot ABI cannot be checked without a valid identity document"
        ]
    sections.append(("compute_slot_abi", errors, {"sha256": abi_hash}))

    closure_ids = {_source_id(row) for row in closure_rows}
    if not load_errors:
        timing, timing_hash, errors = _validate_timing_contract(
            identity, closure_ids, evidence_ids, abi
        )
    else:
        timing, timing_hash, errors = {}, "", [
            "timing contract cannot be checked without a valid identity document"
        ]
    sections.append(("clock_reset_calibration_timing", errors, {"sha256": timing_hash}))

    if not load_errors:
        axi_interfaces, axi_hash, errors = _validate_axi_contract(identity, timing, evidence_ids)
    else:
        axi_interfaces, axi_hash, errors = [], "", [
            "AXI contract cannot be checked without a valid identity document"
        ]
    sections.append(
        (
            "complete_axi_interfaces",
            errors,
            {"sha256": axi_hash, "interface_count": len(axi_interfaces)},
        )
    )

    checks = [
        {
            "name": name,
            "status": "fail" if row_errors else "pass",
            **details,
            "blockers": row_errors,
        }
        for name, row_errors, details in sections
    ]
    blockers = [error for _, row_errors, _ in sections for error in row_errors]
    return {
        "schema_version": IDENTITY_SCHEMA_VERSION,
        "phase": "identity",
        "status": "fail" if blockers else "pass",
        "identity_path": str(identity_path),
        "source_closure_sha256": closure_hash or None,
        "compute_slot_abi_sha256": abi_hash or None,
        "timing_contract_sha256": timing_hash or None,
        "axi_interfaces_sha256": axi_hash or None,
        "checks": checks,
        "blockers": blockers,
    }


def validate_exact_board_acceptance(
    identity_path: Path, simulation_path: Path
) -> dict[str, Any]:
    """Validate post-run elaboration and dynamic protocol evidence."""

    return _validate_exact_board_contract(identity_path, simulation_path, require_execution=True)
