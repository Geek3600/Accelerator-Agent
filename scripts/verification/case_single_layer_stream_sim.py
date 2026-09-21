#!/usr/bin/env python3
"""Case-adapter driven single-layer stream simulation and compare tool.

This tool is intentionally generic: the framework supplies a run directory and
the case adapter supplies artifact paths. It does not encode Qwen/OPT model
semantics in the framework core. Functional mode runs the generated single
transformer-layer stream top with Verilator and emits boundary-trace evidence.
Golden mode compares the captured output against an explicit adapter-provided
reference; missing reference data is a verifier capability failure, not a pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.connected_kernel_targeted_replay import (
    immutable_semantic_replay_inputs,
    materialize_connected_kernel_replay_testbench,
    materialize_connected_kernel_targeted_replay_evidence,
    replay_semantic_contract,
)
from accagent.framework.semantic_simulator import run_configured_semantic_harness


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def optional_file_sha256(value: object) -> str | None:
    path = Path(str(value or ""))
    return sha256_file(path) if path.is_file() else None


def semantic_manifest(run_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
    return path, read_json(path) if path.exists() else {}


def run_generated_semantic_tb(
    run_dir: Path,
    manifest: dict[str, Any],
    section_override: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Path]:
    section = section_override if isinstance(section_override, dict) else (
        manifest.get("single_layer", {}) if isinstance(manifest.get("single_layer"), dict) else {}
    )
    output_path = Path(str(section.get("rtl_output_capture") or ""))
    if section.get("status") != "ready" or section.get("real_weight_binding_verified") is not True:
        return {"status": "fail", "phase": "semantic_preparation", "summary": "semantic testbench or DUT real-weight binding is not ready"}, output_path
    timeout_sec = int(
        os.environ.get(
            "SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC",
            os.environ.get("SPATIALACC_TOOL_TIMEOUT_SEC", "0"),
        )
    )
    progress_observer = SingleLayerPipelineProgressObserver(run_dir, section)
    result = run_configured_semantic_harness(
        run_dir,
        "single_transformer_layer_kernel",
        section,
        timeout_sec,
        progress_observer,
    )
    return result, output_path


PIPELINE_TRACE_RE = re.compile(
    r"SPATIALACC_PIPELINE_TRACE\s+"
    r"boundary=(?P<boundary>\S+)\s+cycle=\s*(?P<cycle>\d+)\s+"
    r"token=\s*(?P<token>\d+)\s+beat=\s*(?P<beat>\d+)\s+"
    r"st=\s*(?P<st>[01])\s+last=\s*(?P<last>[01])\s+"
    r"valid=\s*(?P<valid>[01])\s+ready=\s*(?P<ready>[01])"
)

SEMANTIC_PASS_RE = re.compile(
    r"^PASS semantic harness real-weight execution\s+"
    r"beats=\s*(?P<beats>\d+)\s+cycles=\s*(?P<cycles>\d+)\s*$",
    re.MULTILINE,
)

PIPELINE_CONTRACT_V2 = "spatialaccagent.single_layer_pipeline_overlap_contract.v2"
PIPELINE_CONTRACT_V3 = "spatialaccagent.single_layer_pipeline_overlap_contract.v3"
SUPPORTED_PIPELINE_CONTRACTS = {PIPELINE_CONTRACT_V2, PIPELINE_CONTRACT_V3}
CCTG_BOUNDARY_REPLAY_SCHEMA = "spatialaccagent.cctg_boundary_replay.v1"


def targeted_cctg_replay_requested() -> bool:
    return (
        os.environ.get("SPATIALACC_CCTG_CONNECTED_KERNEL_REPLAY", "0") == "1"
        or os.environ.get("SPATIALACC_CONNECTED_KERNEL_TARGETED_REPLAY", "0") == "1"
    )


def connected_kernel_targeted_replay_requested(args: argparse.Namespace) -> bool:
    return bool(args.connected_kernel_targeted_replay) or (
        os.environ.get("SPATIALACC_CONNECTED_KERNEL_TARGETED_REPLAY", "0") == "1"
    )


def pipeline_trace_records(
    execution: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Parse unique ready/valid observations from a real semantic run."""

    records: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    unparsed_trace_line_count = 0
    for key in ("sim_log", "sim_stderr_log"):
        path = Path(str(execution.get(key) or ""))
        if not path.is_file():
            continue
        for line in read_text(path).splitlines():
            if "SPATIALACC_PIPELINE_TRACE" not in line:
                continue
            match = PIPELINE_TRACE_RE.search(line)
            if match is None:
                unparsed_trace_line_count += 1
                continue
            row = {
                "boundary": match.group("boundary"),
                "cycle": int(match.group("cycle")),
                "token": int(match.group("token")),
                "beat": int(match.group("beat")),
                "st": int(match.group("st")),
                "last": int(match.group("last")),
                "valid": int(match.group("valid")),
                "ready": int(match.group("ready")),
            }
            identity = tuple(row.values())
            if identity not in seen:
                seen.add(identity)
                records.append(row)
    records.sort(key=lambda row: (row["cycle"], row["boundary"], row["token"], row["beat"]))
    return records, unparsed_trace_line_count


def cctg_boundary_replay_evidence(
    execution: dict[str, Any],
    section: dict[str, Any],
) -> dict[str, Any]:
    """Materialize a fresh, contract-derived CCTG boundary replay artifact.

    This is deliberately an observation producer, not a semantic pass shortcut:
    it records each declared boundary's accepted transactions for the next LLM
    repair decision and rejects cached executions.
    """

    contract = (
        section.get("pipeline_overlap_contract", {})
        if isinstance(section.get("pipeline_overlap_contract"), dict)
        else {}
    )
    records, unparsed_trace_line_count = pipeline_trace_records(execution)
    required_boundaries = [str(value) for value in contract.get("required_boundaries", []) if str(value)]
    boundary_contracts = {
        str(row.get("boundary_id")): row
        for row in contract.get("boundary_contracts", [])
        if isinstance(row, dict) and str(row.get("boundary_id") or "")
    }
    token_count = int(contract.get("token_count") or 0)
    observation_blockers: list[str] = []
    remote_reuse = (
        execution.get("remote_job_reuse", {})
        if isinstance(execution.get("remote_job_reuse"), dict)
        else {}
    )
    fresh_remote_vcs = (
        execution.get("status") == "pass"
        and execution.get("simulator") == "vcs"
        and execution.get("tool_scope") == "remote"
        and execution.get("fresh_remote_vcs_execution_required") is True
        and remote_reuse.get("real_tool_was_not_relaunched") is False
        and isinstance(execution.get("run"), dict)
        and execution["run"].get("status") == "pass"
    )
    if not fresh_remote_vcs:
        observation_blockers.append("targeted CCTG replay requires a fresh completed remote VCS execution")
    if (
        not contract.get("contract_sha256")
        or token_count <= 0
        or not required_boundaries
        or set(required_boundaries) != set(boundary_contracts)
    ):
        observation_blockers.append("pipeline overlap contract does not declare every CCTG boundary")
    if unparsed_trace_line_count:
        observation_blockers.append("targeted CCTG replay contains unparsed pipeline trace observations")
    if not records:
        observation_blockers.append("targeted CCTG replay contains no parseable internal boundary observations")

    boundary_records: list[dict[str, Any]] = []
    for boundary_id in required_boundaries:
        boundary = boundary_contracts.get(boundary_id, {})
        beats_per_token = int(boundary.get("beats_per_token") or 0)
        # The generated CCTG trace ABI records accepted token endpoints, not
        # every payload beat.  A multi-beat token emits its first and last
        # accepted handshake; for a one-beat token those are one observation.
        # Keep the complete data-beat count as execution-scale context, but
        # never use it as the trace-coverage expectation.
        expected_data_beat_count = token_count * beats_per_token
        expected_endpoint_trace_observation_count = token_count * (
            1 if beats_per_token == 1 else 2
        )
        rows = [row for row in records if row["boundary"] == boundary_id]
        accepted = [row for row in rows if row["valid"] == 1 and row["ready"] == 1]
        first_by_token = {
            token: next(
                (
                    row
                    for row in accepted
                    if row["token"] == token
                    and row["beat"] == 0
                    and row["st"] == 1
                ),
                None,
            )
            for token in range(token_count)
        }
        terminal_by_token = {
            token: next(
                (
                    row
                    for row in reversed(accepted)
                    if row["token"] == token
                    and row["beat"] == beats_per_token - 1
                    and row["last"] == 1
                ),
                None,
            )
            for token in range(token_count)
        }
        missing_first_token_ids = [
            token for token, row in first_by_token.items() if row is None
        ]
        missing_terminal_token_ids = [
            token for token, row in terminal_by_token.items() if row is None
        ]
        endpoint_observations = {
            (
                row["boundary"],
                row["cycle"],
                row["token"],
                row["beat"],
                row["st"],
                row["last"],
                row["valid"],
                row["ready"],
            )
            for row in [*first_by_token.values(), *terminal_by_token.values()]
            if row is not None
        }
        boundary_blockers: list[str] = []
        if beats_per_token <= 0:
            boundary_blockers.append("boundary has no positive beats_per_token contract")
        if missing_first_token_ids:
            boundary_blockers.append(
                "missing first accepted transaction for token(s): "
                + ", ".join(str(token) for token in missing_first_token_ids)
            )
        if missing_terminal_token_ids:
            boundary_blockers.append(
                "missing terminal-last accepted transaction for token(s): "
                + ", ".join(str(token) for token in missing_terminal_token_ids)
            )
        boundary_records.append(
            {
                "boundary_id": boundary_id,
                "src_stage": boundary.get("src_stage"),
                "dst_stage": boundary.get("dst_stage"),
                "beats_per_token": beats_per_token,
                "token_count": token_count,
                "trace_observation_mode": "first_last_accepted_handshake_endpoints",
                "accepted_count": len(accepted),
                "expected_accepted_count": expected_endpoint_trace_observation_count,
                "accepted_trace_observation_count": len(accepted),
                "expected_endpoint_trace_observation_count": expected_endpoint_trace_observation_count,
                "observed_endpoint_trace_observation_count": len(endpoint_observations),
                "expected_data_beat_count": expected_data_beat_count,
                "missing_first_token_ids": missing_first_token_ids,
                "missing_terminal_token_ids": missing_terminal_token_ids,
                "first_accepted_transaction": first_by_token.get(0),
                "terminal_last_accepted_transaction": terminal_by_token.get(token_count - 1),
                "status": "pass" if not boundary_blockers else "fail",
                "blockers": boundary_blockers,
            }
        )
    incomplete_boundaries = [
        row for row in boundary_records if row["status"] != "pass"
    ]

    trace_digest = hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": CCTG_BOUNDARY_REPLAY_SCHEMA,
        # Completion of this read-only producer means that the Agent now has a
        # fresh source-bound causal trace.  A nonpassing boundary is the
        # diagnosis input, not a reason to discard the replay and silently
        # fall back to stale aggregate evidence.
        "status": "pass" if not observation_blockers else "fail",
        "summary": (
            "fresh remote VCS CCTG boundary replay captured the declared boundary frontier"
            if not observation_blockers
            else "targeted CCTG boundary replay did not produce usable internal observations"
        ),
        "targeted_replay": targeted_cctg_replay_requested(),
        "contract_sha256": contract.get("contract_sha256"),
        "source_execution": {
            "input_fingerprint_sha256": execution.get("input_fingerprint_sha256"),
            "remote_workdir": execution.get("remote_workdir"),
            "simulator": execution.get("simulator"),
            "tool_scope": execution.get("tool_scope"),
            "fresh_remote_vcs_execution_required": execution.get("fresh_remote_vcs_execution_required"),
            "remote_job_reuse": remote_reuse,
            "vcs_log": {"path": execution.get("vcs_log"), "sha256": optional_file_sha256(execution.get("vcs_log"))},
            "sim_log": {"path": execution.get("sim_log"), "sha256": optional_file_sha256(execution.get("sim_log"))},
            "sim_stderr_log": {"path": execution.get("sim_stderr_log"), "sha256": optional_file_sha256(execution.get("sim_stderr_log"))},
        },
        "fresh_remote_vcs_execution_observed": fresh_remote_vcs,
        "trace_record_count": len(records),
        "accepted_trace_record_count": sum(1 for row in records if row["valid"] == 1 and row["ready"] == 1),
        "trace_sha256": trace_digest,
        "unparsed_trace_line_count": unparsed_trace_line_count,
        "boundary_records": boundary_records,
        "boundary_liveness_status": "pass" if not incomplete_boundaries else "fail",
        "first_incomplete_boundary": (
            incomplete_boundaries[0]["boundary_id"] if incomplete_boundaries else None
        ),
        "observation_blockers": observation_blockers,
        "blockers": observation_blockers,
    }


def write_cctg_boundary_replay(
    run_dir: Path,
    execution: dict[str, Any],
    section: dict[str, Any],
) -> Path | None:
    if not targeted_cctg_replay_requested():
        return None
    path = run_dir / "verification" / "debug_closure" / "cctg_boundary_replay.json"
    write_json(path, cctg_boundary_replay_evidence(execution, section))
    return path


def rematerialize_cctg_boundary_replay(run_dir: Path) -> tuple[Path, dict[str, Any]]:
    """Reinterpret one completed fresh VCS execution without rerunning it.

    This is only for an evidence-schema/decoder correction.  The source report,
    manifest, remote execution identity, and raw-log hashes stay bound in the
    resulting artifact; a missing or non-fresh execution remains a failure and
    must use the normal real-tool replay path instead.
    """

    semantic_path, semantic = semantic_manifest(run_dir)
    report_path = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
    report = read_json(report_path) if report_path.is_file() else {}
    source_report_sha256 = sha256_file(report_path) if report_path.is_file() else None
    section = (
        semantic.get("single_layer", {})
        if isinstance(semantic.get("single_layer"), dict)
        else {}
    )
    execution = report.get("stats", {}) if isinstance(report.get("stats"), dict) else {}
    direct_requested = os.environ.get("SPATIALACC_CONNECTED_KERNEL_TARGETED_REPLAY", "0") == "1"

    def source_report_is_reusable() -> bool:
        if report.get("status") == "pass" and execution.get("status") == "pass":
            return True
        if not direct_requested or report.get("status") != "fail":
            return False
        overlap = report.get("pipeline_overlap_evidence", {})
        cctg = report.get("cctg_boundary_replay", {})
        direct = report.get("connected_kernel_targeted_replay", {})
        trace = direct.get("trace", {}) if isinstance(direct, dict) else {}
        context = direct.get("causal_context", {}) if isinstance(direct, dict) else {}
        reconciliation = direct.get("reconciliation", {}) if isinstance(direct, dict) else {}
        return bool(
            execution.get("status") == "pass"
            and isinstance(overlap, dict)
            and overlap.get("status") == "pass"
            and isinstance(cctg, dict)
            and cctg.get("status") == "pass"
            and isinstance(trace, dict)
            and trace.get("status") == "fail"
            and isinstance(context, dict)
            and context.get("status") == "fail"
            and isinstance(reconciliation, dict)
            and reconciliation.get("status") == "fail"
        )

    source_blockers: list[str] = []
    if not report_path.is_file():
        source_blockers.append("completed source functional report is missing")
    if report.get("schema_version") != "spatialaccagent.single_layer_functional_sim.v1":
        source_blockers.append("completed source report is not a semantic single-layer functional report")
    if not source_report_is_reusable():
        source_blockers.append(
            "completed source report is not a passing semantic execution or an "
            "isolated direct-evidence classification failure"
        )
    if semantic.get("status") != "ready" or section.get("real_weight_binding_verified") is not True:
        source_blockers.append("semantic testbench or real-weight binding is no longer ready")

    evidence = cctg_boundary_replay_evidence(execution, section)
    if source_blockers:
        evidence["status"] = "fail"
        evidence["observation_blockers"] = list(
            dict.fromkeys([*evidence.get("observation_blockers", []), *source_blockers])
        )
        evidence["blockers"] = list(evidence["observation_blockers"])
    prior_path = run_dir / "verification" / "debug_closure" / "cctg_boundary_replay.json"
    prior = read_json(prior_path) if prior_path.is_file() else {}
    evidence["targeted_replay"] = bool(prior.get("targeted_replay") is True)
    source_snapshot_path = (
        run_dir
        / "verification"
        / "debug_closure"
        / "cctg_evidence_rematerialization_source_functional_report.json"
    )
    if report_path.is_file():
        shutil.copyfile(report_path, source_snapshot_path)
    evidence["evidence_rematerialization"] = {
        "schema_version": "spatialaccagent.cctg_evidence_rematerialization.v1",
        "status": "pass" if evidence.get("status") == "pass" else "fail",
        "mode": "completed_fresh_execution_evidence_rematerialization",
        "reexecution_performed": False,
        "reason": "recomputed CCTG endpoint coverage after an evidence interpretation revision",
        "source_functional_report": str(source_snapshot_path) if source_snapshot_path.is_file() else str(report_path),
        "source_functional_report_sha256": (
            sha256_file(source_snapshot_path) if source_snapshot_path.is_file() else source_report_sha256
        ),
        "source_functional_report_current_path": str(report_path),
        "semantic_testbench_manifest": str(semantic_path),
        "semantic_testbench_manifest_sha256": sha256_file(semantic_path),
        "prior_cctg_artifact": str(prior_path) if prior_path.is_file() else None,
        "prior_cctg_artifact_sha256": sha256_file(prior_path),
        "source_execution_identity": {
            "input_fingerprint_sha256": execution.get("input_fingerprint_sha256"),
            "remote_workdir": execution.get("remote_workdir"),
            "sim_log_sha256": optional_file_sha256(execution.get("sim_log")),
            "sim_stderr_log_sha256": optional_file_sha256(execution.get("sim_stderr_log")),
            "vcs_log_sha256": optional_file_sha256(execution.get("vcs_log")),
        },
    }
    cctg_path = run_dir / "verification" / "debug_closure" / "cctg_boundary_replay.json"
    write_json(cctg_path, evidence)

    direct_rematerialization: dict[str, Any] | None = None
    if direct_requested and not source_blockers:
        direct = materialize_connected_kernel_targeted_replay_evidence(
            run_dir,
            execution,
            evidence,
        )
        direct_trace = direct["trace"]
        direct_rematerialization = {
            "status": direct_trace.get("status"),
            "reexecution_performed": False,
            "mode": "completed_fresh_execution_direct_evidence_rematerialization",
            "trace": {
                "path": str(direct["trace_path"]),
                "sha256": sha256_file(direct["trace_path"]),
                "status": direct_trace.get("status"),
            },
            "causal_context": {
                "path": str(direct["context_path"]),
                "sha256": sha256_file(direct["context_path"]),
                "status": direct["context"].get("status"),
            },
            "reconciliation": {
                "path": str(direct["reconciliation_path"]),
                "sha256": sha256_file(direct["reconciliation_path"]),
                "status": direct["reconciliation"].get("status"),
            },
        }
        evidence["evidence_rematerialization"]["status"] = direct_trace.get("status")
        evidence["evidence_rematerialization"]["connected_kernel_targeted_replay"] = direct_rematerialization
        write_json(cctg_path, evidence)

    rematerialization = {
        **evidence["evidence_rematerialization"],
        "cctg_boundary_replay": str(cctg_path),
        "cctg_boundary_replay_sha256": sha256_file(cctg_path),
        "boundary_liveness_status": evidence.get("boundary_liveness_status"),
        "first_incomplete_boundary": evidence.get("first_incomplete_boundary"),
    }
    if direct_rematerialization is not None:
        rematerialization["connected_kernel_targeted_replay"] = direct_rematerialization
    rematerialization_path = (
        run_dir / "verification" / "debug_closure" / "cctg_evidence_rematerialization.json"
    )
    write_json(rematerialization_path, rematerialization)
    refreshed_context_packages: list[dict[str, Any]] = []
    for package_path in sorted(
        (run_dir / "repair_execution").glob(
            "*_current_layer_causal_repair_context_package.json"
        )
    ):
        package = read_json(package_path)
        if str(package.get("capability_id") or "") not in {
            "cctg_connected_kernel_boundary_replay",
            "connected_kernel_cctg_contradiction_targeted_replay",
        }:
            continue
        package["status"] = evidence.get("status")
        package["cctg_boundary_replay"] = {
            "path": str(cctg_path),
            "sha256": sha256_file(cctg_path),
            "status": evidence.get("status"),
            "boundary_liveness_status": evidence.get("boundary_liveness_status"),
            "first_incomplete_boundary": evidence.get("first_incomplete_boundary"),
            "blockers": list(evidence.get("blockers", [])),
        }
        package["cctg_boundary_replay_evidence"] = evidence
        package["cctg_evidence_rematerialization"] = {
            "path": str(rematerialization_path),
            "sha256": sha256_file(rematerialization_path),
            "status": rematerialization.get("status"),
        }
        if (
            direct_rematerialization is not None
            and str(package.get("capability_id") or "")
            == "connected_kernel_cctg_contradiction_targeted_replay"
        ):
            package["connected_kernel_cctg_targeted_replay_trace"] = {
                **direct_rematerialization["trace"],
                "schema_version": "spatialaccagent.connected_kernel_cctg_targeted_replay_trace.v1",
                "blockers": [],
            }
            package["connected_kernel_targeted_replay_causal_context"] = {
                **direct_rematerialization["causal_context"],
                "schema_version": "spatialaccagent.connected_kernel_targeted_replay_causal_context.v1",
                "blockers": [],
            }
            package["connected_kernel_cctg_contradiction_reconciliation"] = {
                **direct_rematerialization["reconciliation"],
                "schema_version": "spatialaccagent.connected_kernel_cctg_contradiction_reconciliation.v1",
                "blockers": [],
            }
        write_json(package_path, package)
        refreshed_context_packages.append(
            {"path": str(package_path), "sha256": sha256_file(package_path)}
        )
    rematerialization["refreshed_cctg_context_packages"] = refreshed_context_packages
    write_json(rematerialization_path, rematerialization)
    if report:
        report["cctg_boundary_replay"] = {
            "path": str(cctg_path),
            "sha256": sha256_file(cctg_path),
            "status": evidence.get("status"),
            "boundary_liveness_status": evidence.get("boundary_liveness_status"),
        }
        report["cctg_evidence_rematerialization"] = {
            "path": str(rematerialization_path),
            "sha256": sha256_file(rematerialization_path),
            "status": rematerialization.get("status"),
        }
        if direct_rematerialization is not None:
            report["connected_kernel_targeted_replay"] = {
                "trace": direct_rematerialization["trace"],
                "causal_context": direct_rematerialization["causal_context"],
                "reconciliation": direct_rematerialization["reconciliation"],
            }
            if direct_rematerialization.get("status") == "pass":
                report["status"] = "pass"
        write_json(report_path, report)
        hierarchy_path = run_dir / "verification" / "case_hierarchy" / "single_layer_functional.json"
        if hierarchy_path.parent.exists():
            write_json(hierarchy_path, {**report, "gate": "single_layer_functional"})
    return rematerialization_path, rematerialization


def irreversible_stage_turnover_evidence(
    contract: dict[str, Any],
    accepted: list[dict[str, Any]],
) -> dict[str, Any]:
    schema_version = str(contract.get("schema_version") or "")
    token_count = int(contract.get("token_count") or 0)
    boundary_rows = [
        row
        for row in contract.get("boundary_contracts", [])
        if isinstance(row, dict) and row.get("boundary_id")
    ]
    beats_by_boundary = {
        str(row["boundary_id"]): int(row.get("beats_per_token") or 0)
        for row in boundary_rows
    }
    stages = [
        row
        for row in contract.get("stage_activity_contracts", [])
        if isinstance(row, dict) and row.get("stage_id")
    ]
    if (
        schema_version not in SUPPORTED_PIPELINE_CONTRACTS
        or token_count < 2
        or not stages
        or any(value <= 0 for value in beats_by_boundary.values())
    ):
        return {
            "status": "not_available",
            "failed_stage_turnover_evidence": [],
            "candidate_stage_ids": [],
        }
    strict_turnover = schema_version == PIPELINE_CONTRACT_V2
    maximum_gap = (
        int(
            contract.get("acceptance", {}).get(
                "maximum_next_token_stage_entry_gap_cycles", 1
            )
        )
        if strict_turnover
        else None
    )

    def exact_boundary_cycle(
        boundaries: list[str],
        token: int,
        *,
        first: bool,
    ) -> int | None:
        cycles: list[int] = []
        for boundary in boundaries:
            beat = 0 if first else beats_by_boundary.get(boundary, 0) - 1
            rows = [
                row
                for row in accepted
                if row["boundary"] == boundary
                and row["token"] == token
                and row["beat"] == beat
                and row["st" if first else "last"] == 1
            ]
            if len(rows) != 1:
                return None
            cycles.append(int(rows[0]["cycle"]))
        return max(cycles) if cycles else None

    failed_turnovers: list[dict[str, Any]] = []
    diagnostic_turnovers: list[dict[str, Any]] = []
    for stage in stages:
        stage_id = str(stage["stage_id"])
        inputs = [str(value) for value in stage.get("input_boundaries", [])]
        outputs = [str(value) for value in stage.get("output_boundaries", [])]
        if not inputs or not outputs:
            continue
        for token in range(token_count - 1):
            prior_end = exact_boundary_cycle(outputs, token, first=False)
            following_start = exact_boundary_cycle(inputs, token + 1, first=True)
            if prior_end is None or following_start is None:
                continue
            gap = following_start - prior_end
            if not strict_turnover:
                diagnostic_turnovers.append(
                    {
                        "stage_id": stage_id,
                        "prior_token": token,
                        "next_token": token + 1,
                        "prior_token_active_end_cycle": prior_end,
                        "next_token_active_start_cycle": following_start,
                        "gap_cycles": gap,
                        "idle_cycles": max(0, gap - 1),
                        "tokens_overlap": gap <= 0,
                        "immediate_turnover": gap <= 1,
                        "acceptance_role": "diagnostic",
                    }
                )
                continue
            assert maximum_gap is not None
            if gap <= maximum_gap:
                continue
            failed_turnovers.append(
                {
                    "stage_id": stage_id,
                    "prior_token": token,
                    "next_token": token + 1,
                    "prior_token_active_end_cycle": prior_end,
                    "next_token_active_start_cycle": following_start,
                    "gap_cycles": gap,
                    "keeps_pipeline_filled": False,
                    "overlapped": False,
                }
            )
    failed_stage_ids = {str(row["stage_id"]) for row in failed_turnovers}
    candidate_stage_ids = set(failed_stage_ids)
    planned_stage_ids = {str(stage["stage_id"]) for stage in stages}
    for edge in contract.get("dependency_edges", []):
        if not isinstance(edge, dict):
            continue
        src_stage = str(edge.get("src_stage") or "")
        dst_stage = str(edge.get("dst_stage") or "")
        if src_stage in failed_stage_ids or dst_stage in failed_stage_ids:
            if src_stage in planned_stage_ids:
                candidate_stage_ids.add(src_stage)
            if dst_stage in planned_stage_ids:
                candidate_stage_ids.add(dst_stage)
    return {
        "status": (
            "fail"
            if failed_turnovers
            else "diagnostic"
            if not strict_turnover and diagnostic_turnovers
            else "observing"
        ),
        "maximum_next_token_stage_entry_gap_cycles": maximum_gap,
        "stage_turnover_gaps_are_diagnostic": not strict_turnover,
        "diagnostic_stage_turnover_evidence": diagnostic_turnovers,
        "failed_stage_turnover_evidence": failed_turnovers,
        "candidate_stage_ids": [
            str(stage["stage_id"])
            for stage in stages
            if str(stage["stage_id"]) in candidate_stage_ids
        ],
    }


class SingleLayerPipelineProgressObserver:
    """Close a real Stage2 run only after an irreversible contract violation."""

    remote_progress_log_name = "sim.stderr.log"

    def __init__(self, run_dir: Path, section: dict[str, Any]) -> None:
        self.contract = (
            section.get("pipeline_overlap_contract", {})
            if isinstance(section.get("pipeline_overlap_contract"), dict)
            else {}
        )
        self.snapshot_path = (
            run_dir
            / "verification"
            / "operator_leaf_vcs"
            / "single_transformer_layer_kernel"
            / "live_progress.json"
        )
        self.fingerprint = ""
        self.records: dict[tuple[Any, ...], dict[str, Any]] = {}

    def __call__(self, observation: dict[str, Any]) -> None:
        for match in PIPELINE_TRACE_RE.finditer(
            str(observation.get("progress_log_tail") or "")
        ):
            row = {
                "boundary": match.group("boundary"),
                "cycle": int(match.group("cycle")),
                "token": int(match.group("token")),
                "beat": int(match.group("beat")),
                "st": int(match.group("st")),
                "last": int(match.group("last")),
                "valid": int(match.group("valid")),
                "ready": int(match.group("ready")),
            }
            self.records[tuple(row.values())] = row

        evidence = self._barrier_evidence()
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            self.snapshot_path,
            {
                "schema_version": "spatialaccagent.single_layer_live_progress.v1",
                "status": (
                    "fail"
                    if evidence.get("status") == "proven_semantic_stall"
                    else "observing"
                ),
                "input_fingerprint_sha256": self.fingerprint,
                "remote_workdir": observation.get("remote_workdir"),
                "remote_pid": observation.get("pid"),
                "process_state": observation.get("state"),
                "poll_attempt": observation.get("poll_attempt"),
                "trace_record_count": len(self.records),
                "latest_trace_cycle": max(
                    (int(row["cycle"]) for row in self.records.values()),
                    default=None,
                ),
                "adaptive_semantic_stall_evidence": evidence,
            },
        )

    def _barrier_evidence(self) -> dict[str, Any]:
        contract = self.contract
        token_count = int(contract.get("token_count") or 0)
        boundary_rows = [
            row
            for row in contract.get("boundary_contracts", [])
            if isinstance(row, dict) and row.get("boundary_id")
        ]
        beats_by_boundary = {
            str(row["boundary_id"]): int(row.get("beats_per_token") or 0)
            for row in boundary_rows
        }
        stages = [
            row
            for row in contract.get("stage_activity_contracts", [])
            if isinstance(row, dict) and row.get("stage_id")
        ]
        base = {
            "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
            "status": "observing",
            "proof_mode": "single_layer_pipeline_contract",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "contract_sha256": contract.get("contract_sha256"),
            "fixed_wall_clock_timeout": False,
            "fixed_cycle_timeout": False,
        }
        if (
            contract.get("schema_version") not in SUPPORTED_PIPELINE_CONTRACTS
            or token_count < 2
            or not stages
            or any(value <= 0 for value in beats_by_boundary.values())
        ):
            return {**base, "reason": "complete supported pipeline contract is not available"}

        accepted = [
            row
            for row in self.records.values()
            if row["valid"] == 1 and row["ready"] == 1
        ]
        turnover = irreversible_stage_turnover_evidence(contract, accepted)
        failed_turnovers = turnover.get("failed_stage_turnover_evidence", [])
        if (
            contract.get("schema_version") == PIPELINE_CONTRACT_V2
            and turnover.get("status") == "fail"
            and failed_turnovers
        ):
            return {
                **base,
                "status": "proven_semantic_stall",
                "reason": (
                    "v2 contract proves an accepted adjacent-token stage turnover "
                    "exceeded the maximum entry gap"
                ),
                "irreversible_violation_kind": "stage_turnover",
                "first_stalled_boundary": str(
                    next(
                        stage.get("output_boundaries", [""])[0]
                        for stage in stages
                        if str(stage["stage_id"])
                        == str(failed_turnovers[0]["stage_id"])
                    )
                ),
                "last_semantic_event_cycle": max(
                    int(row["cycle"]) for row in accepted
                ),
                "latest_cycle": max(int(row["cycle"]) for row in accepted),
                "failed_stage_turnover_evidence": failed_turnovers,
                "candidate_stage_ids": turnover.get(
                    "candidate_stage_ids", []
                ),
                "trace_record_count": len(self.records),
                "policy": {
                    "only_irreversible_contract_violations_may_terminate_early": True,
                    "clock_activity_or_wall_time_alone_cannot_terminate": True,
                    "partial_trace_cannot_claim_hardware_pass": True,
                    "candidate_stages_are_a_one_hop_causal_authorization_ceiling": True,
                },
            }
        violations = []
        for stage in stages:
            inputs = [str(value) for value in stage.get("input_boundaries", [])]
            outputs = [str(value) for value in stage.get("output_boundaries", [])]
            if not inputs or not outputs:
                continue
            final_input_rows = [
                row
                for boundary in inputs
                for row in accepted
                if row["boundary"] == boundary
                and row["token"] == token_count - 1
                and row["beat"] == beats_by_boundary.get(boundary, 0) - 1
                and row["last"] == 1
            ]
            first_output_rows = [
                row
                for boundary in outputs
                for row in accepted
                if row["boundary"] == boundary
                and row["token"] == 0
                and row["beat"] == 0
                and row["st"] == 1
            ]
            if (
                len({row["boundary"] for row in final_input_rows}) != len(inputs)
                or len({row["boundary"] for row in first_output_rows}) != len(outputs)
            ):
                continue
            final_input_cycle = max(int(row["cycle"]) for row in final_input_rows)
            first_output_cycle = min(int(row["cycle"]) for row in first_output_rows)
            if first_output_cycle >= final_input_cycle:
                violations.append(
                    {
                        "stage_id": str(stage["stage_id"]),
                        "input_boundaries": inputs,
                        "output_boundaries": outputs,
                        "final_token_last_input_cycle": final_input_cycle,
                        "token_0_first_output_cycle": first_output_cycle,
                        "whole_sequence_barrier_observed": True,
                    }
                )
        if not violations:
            return {
                **base,
                "reason": "no irreversible whole-sequence barrier witness is complete",
            }
        return {
            **base,
            "status": "proven_semantic_stall",
            "reason": (
                "the contract proves a stage accepted the complete token sequence "
                "before emitting token 0"
            ),
            "first_stalled_boundary": violations[0]["output_boundaries"][0],
            "irreversible_violation_kind": "whole_sequence_barrier",
            "last_semantic_event_cycle": max(
                int(row["cycle"]) for row in accepted
            ),
            "latest_cycle": max(int(row["cycle"]) for row in accepted),
            "whole_sequence_barrier_evidence": violations,
            "trace_record_count": len(self.records),
            "policy": {
                "only_irreversible_contract_violations_may_terminate_early": True,
                "clock_activity_or_wall_time_alone_cannot_terminate": True,
                "partial_trace_cannot_claim_hardware_pass": True,
            },
        }


def terminal_trace_flush_evidence(
    execution: dict[str, Any],
    required_boundaries: list[str],
    token_count: int,
    beats_by_boundary: dict[str, int],
    output_boundary: str,
    records: list[dict[str, Any]],
    unparsed_trace_line_count: int,
) -> dict[str, Any]:
    output_beats_per_token = int(beats_by_boundary.get(output_boundary) or 0)
    expected_output_lines = token_count * output_beats_per_token
    run = execution.get("run", {}) if isinstance(execution.get("run"), dict) else {}
    output_path = Path(str(execution.get("output_capture") or ""))
    actual_output_lines = None
    if output_path.is_file():
        actual_output_lines = sum(
            1
            for line in read_text(output_path).splitlines()
            if line.strip()
        )

    sim_path = Path(str(execution.get("sim_log") or ""))
    pass_rows = [
        {"beats": int(match.group("beats")), "cycles": int(match.group("cycles"))}
        for match in SEMANTIC_PASS_RE.finditer(read_text(sim_path))
    ] if sim_path.is_file() else []

    required_set = set(required_boundaries)
    required_records = [row for row in records if row["boundary"] in required_set]
    accepted_records = [
        row for row in required_records
        if row["valid"] == 1 and row["ready"] == 1
    ]
    positions: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
    malformed_records = []
    for row in accepted_records:
        key = (row["boundary"], row["token"], row["beat"])
        positions.setdefault(key, []).append(row)
        boundary_beats = int(beats_by_boundary.get(row["boundary"]) or 0)
        if (
            not (0 <= row["token"] < token_count)
            or not (0 <= row["beat"] < boundary_beats)
            or row["st"] != int(row["beat"] == 0)
            or row["last"] != int(row["beat"] == boundary_beats - 1)
        ):
            malformed_records.append(key)

    expected_positions = {
        (boundary, token, beat)
        for boundary in required_boundaries
        for token in range(token_count)
        for beat in {0, beats_by_boundary.get(boundary, 0) - 1}
        if beat >= 0
    }
    observed_positions = set(positions)
    missing_positions = sorted(expected_positions - observed_positions)
    duplicate_positions = sorted(key for key, rows in positions.items() if len(rows) != 1)
    terminal_position = (
        output_boundary,
        token_count - 1,
        output_beats_per_token - 1,
    )
    checks = {
        "execution_status_pass": execution.get("status") == "pass",
        "remote_exit_status_pass": run.get("status") == "pass" and run.get("returncode") == 0,
        "output_line_count_matches": actual_output_lines == expected_output_lines,
        "single_matching_sim_pass_declaration": (
            len(pass_rows) == 1 and pass_rows[0]["beats"] == expected_output_lines
        ),
        "required_boundaries_are_valid": (
            len(required_boundaries) == len(required_set)
            and output_boundary in required_set
            and all(beats_by_boundary.get(boundary, 0) > 0 for boundary in required_set)
            and token_count >= 2
            and output_beats_per_token > 0
        ),
        "all_required_trace_records_are_accepted": len(required_records) == len(accepted_records),
        "trace_positions_are_unique_and_well_formed": (
            unparsed_trace_line_count == 0
            and not duplicate_positions
            and not malformed_records
        ),
        "only_terminal_block_output_trace_is_missing": missing_positions == [terminal_position],
    }
    inferred = all(checks.values())
    return {
        "inferred": inferred,
        "checks": checks,
        "expected_output_line_count": expected_output_lines,
        "actual_output_line_count": actual_output_lines,
        "sim_pass_declarations": pass_rows,
        "required_trace_position_count": len(expected_positions),
        "observed_required_trace_position_count": len(observed_positions),
        "missing_required_trace_position_count": len(missing_positions),
        "duplicate_required_trace_position_count": len(duplicate_positions),
        "unexpected_required_trace_position_count": 0,
        "malformed_required_trace_position_count": len(malformed_records),
        "unparsed_pipeline_trace_line_count": unparsed_trace_line_count,
        "missing_required_trace_positions": [
            {"boundary": boundary, "token": token, "beat": beat}
            for boundary, token, beat in missing_positions[:8]
        ],
        "duplicate_required_trace_positions": [
            {"boundary": boundary, "token": token, "beat": beat}
            for boundary, token, beat in duplicate_positions[:8]
        ],
        "unexpected_required_trace_positions": [],
        "malformed_required_trace_positions": [
            {"boundary": boundary, "token": token, "beat": beat}
            for boundary, token, beat in malformed_records[:8]
        ],
        "inferred_record": (
            {
                "boundary": terminal_position[0],
                "token": terminal_position[1],
                "beat": terminal_position[2],
                "basis": "passing simulation and exact output count prove the sole terminal transfer; only its final trace printf was not flushed",
            }
            if inferred
            else None
        ),
    }


def pipeline_overlap_evidence(
    execution: dict[str, Any],
    section: dict[str, Any],
) -> dict[str, Any]:
    contract = (
        section.get("pipeline_overlap_contract", {})
        if isinstance(section.get("pipeline_overlap_contract"), dict)
        else {}
    )
    records, unparsed_trace_line_count = pipeline_trace_records(execution)
    accepted = [row for row in records if row["valid"] == 1 and row["ready"] == 1]
    blockers: list[str] = []
    token_count = int(contract.get("token_count") or 0)
    required_boundaries = [str(value) for value in contract.get("required_boundaries", [])]
    boundary_rows = [
        row
        for row in contract.get("boundary_contracts", [])
        if isinstance(row, dict) and row.get("boundary_id")
    ]
    beats_by_boundary = {
        str(row["boundary_id"]): int(row.get("beats_per_token") or 0)
        for row in boundary_rows
    }
    output_boundary = str(contract.get("block_output_boundary") or "")
    stage_contracts = [
        row
        for row in contract.get("stage_activity_contracts", [])
        if isinstance(row, dict) and row.get("stage_id")
    ]
    dependency_edges = [
        row
        for row in contract.get("dependency_edges", [])
        if isinstance(row, dict)
    ]
    stage_order = [str(value) for value in contract.get("stage_order", []) if str(value)]
    contract_schema = str(contract.get("schema_version") or "")
    rate_insensitive = contract_schema == PIPELINE_CONTRACT_V3
    if (
        contract_schema not in SUPPORTED_PIPELINE_CONTRACTS
        or not contract.get("contract_sha256")
        or token_count < 2
        or not required_boundaries
        or set(required_boundaries) != set(beats_by_boundary)
        or any(value <= 0 for value in beats_by_boundary.values())
        or not output_boundary
        or not stage_contracts
        or not stage_order
    ):
        blockers.append(
            "single-layer pipeline-overlap contract must be a supported version with every planned stream boundary and stage"
        )
    if rate_insensitive:
        required_dependency_rows = [
            row
            for row in dependency_edges
            if row.get("overlap_requirement") == "required"
        ]
        if any(
            row.get("overlap_requirement") not in {"required", "diagnostic"}
            for row in dependency_edges
        ):
            blockers.append(
                "v3 pipeline contract has a dependency without a required/diagnostic overlap role"
            )
        if int(contract.get("required_dependency_count") or 0) != len(
            required_dependency_rows
        ):
            blockers.append("v3 pipeline contract required-dependency count is inconsistent")
        if len(stage_order) > 1 and not required_dependency_rows:
            blockers.append("v3 multi-stage pipeline contract has no required dataflow dependency")
    irreversible_turnover = irreversible_stage_turnover_evidence(
        contract, accepted
    )

    terminal_flush = terminal_trace_flush_evidence(
        execution,
        required_boundaries,
        token_count,
        beats_by_boundary,
        output_boundary,
        records,
        unparsed_trace_line_count,
    )
    terminal_flush_inferred = terminal_flush["inferred"] is True

    first_cycle: dict[tuple[str, int], int] = {}
    last_cycle: dict[tuple[str, int], int] = {}
    for boundary in required_boundaries:
        boundary_beats = int(beats_by_boundary.get(boundary) or 0)
        for token in range(token_count):
            token_rows = [
                row for row in accepted
                if row["boundary"] == boundary and row["token"] == token
            ]
            first_rows = [row for row in token_rows if row["st"] == 1 and row["beat"] == 0]
            last_rows = [
                row for row in token_rows
                if row["last"] == 1 and row["beat"] == boundary_beats - 1
            ]
            terminal_record = boundary == output_boundary and token == token_count - 1
            if terminal_flush_inferred and terminal_record:
                if len(first_rows) == 1:
                    first_cycle[(boundary, token)] = first_rows[0]["cycle"]
                continue
            if len(first_rows) != 1 or len(last_rows) != 1:
                blockers.append(
                    f"pipeline trace boundary={boundary} token={token} does not contain exactly one first/last accepted beat"
                )
                continue
            first_cycle[(boundary, token)] = first_rows[0]["cycle"]
            last_cycle[(boundary, token)] = last_rows[0]["cycle"]
            if first_rows[0]["cycle"] > last_rows[0]["cycle"]:
                blockers.append(f"pipeline trace boundary={boundary} token={token} is out of order")
    if terminal_flush_inferred:
        inferred_rows = terminal_flush.get("sim_pass_declarations", [])
        inferred_cycle = (
            int(inferred_rows[0]["cycles"])
            if len(inferred_rows) == 1
            and isinstance(inferred_rows[0].get("cycles"), int)
            else None
        )
        terminal_key = (output_boundary, token_count - 1)
        if inferred_cycle is not None and terminal_key in first_cycle:
            last_cycle[terminal_key] = max(first_cycle[terminal_key], inferred_cycle)

    boundary_order_evidence = []
    boundary_contract_by_id = {
        str(row["boundary_id"]): row for row in boundary_rows
    }
    for boundary in required_boundaries:
        ordered_first = [first_cycle.get((boundary, token)) for token in range(token_count)]
        ordered_last = [last_cycle.get((boundary, token)) for token in range(token_count)]
        complete = all(value is not None for value in ordered_first + ordered_last)
        first_ordered = complete and all(
            int(ordered_first[token]) <= int(ordered_first[token + 1])
            for token in range(token_count - 1)
        )
        last_ordered = complete and all(
            int(ordered_last[token]) <= int(ordered_last[token + 1])
            for token in range(token_count - 1)
        )
        boundary_order_evidence.append(
            {
                "boundary_id": boundary,
                "src_stage": boundary_contract_by_id.get(boundary, {}).get(
                    "src_stage"
                ),
                "dst_stage": boundary_contract_by_id.get(boundary, {}).get(
                    "dst_stage"
                ),
                "complete": complete,
                "token_first_transfer_order_preserved": first_ordered,
                "token_last_transfer_order_preserved": last_ordered,
            }
        )
        if rate_insensitive and complete and not (first_ordered and last_ordered):
            blockers.append(f"pipeline trace boundary={boundary} reorders logical tokens")

    stage_intervals: dict[tuple[str, int], tuple[int, int]] = {}
    stage_activity_evidence = []
    for stage in stage_contracts:
        stage_id = str(stage["stage_id"])
        inputs = [str(value) for value in stage.get("input_boundaries", [])]
        outputs = [str(value) for value in stage.get("output_boundaries", [])]
        for token in range(token_count):
            input_starts = [first_cycle.get((boundary, token)) for boundary in inputs]
            output_ends = [last_cycle.get((boundary, token)) for boundary in outputs]
            if any(value is None for value in input_starts + output_ends):
                continue
            start_cycle = max(int(value) for value in input_starts if value is not None)
            end_cycle = max(int(value) for value in output_ends if value is not None)
            if end_cycle < start_cycle:
                blockers.append(
                    f"stage {stage_id} token {token} output precedes its accepted input"
                )
                continue
            stage_intervals[(stage_id, token)] = (start_cycle, end_cycle)
            stage_activity_evidence.append(
                {
                    "stage_id": stage_id,
                    "token": token,
                    "active_start_cycle": start_cycle,
                    "active_end_cycle": end_cycle,
                }
            )

    maximum_gap = (
        int(
            contract.get("acceptance", {}).get(
                "maximum_next_token_stage_entry_gap_cycles", 1
            )
        )
        if not rate_insensitive
        else None
    )
    stage_turnover_evidence = []
    for stage_id in stage_order:
        covered = 0
        for token in range(token_count - 1):
            prior = stage_intervals.get((stage_id, token))
            following = stage_intervals.get((stage_id, token + 1))
            if prior is None or following is None:
                continue
            gap = following[0] - prior[1]
            immediate_turnover = gap <= 1
            keeps_filled = (
                gap <= maximum_gap if maximum_gap is not None else None
            )
            covered += 1
            stage_turnover_evidence.append(
                {
                    "stage_id": stage_id,
                    "prior_token": token,
                    "next_token": token + 1,
                    "prior_token_active_end_cycle": prior[1],
                    "next_token_active_start_cycle": following[0],
                    "gap_cycles": gap,
                    "idle_cycles": max(0, gap - 1),
                    "keeps_pipeline_filled": keeps_filled,
                    "overlapped": (
                        keeps_filled if not rate_insensitive else gap <= 0
                    ),
                    "immediate_turnover": immediate_turnover,
                    "acceptance_role": (
                        "diagnostic" if rate_insensitive else "required"
                    ),
                }
            )
            if not rate_insensitive and not keeps_filled:
                blockers.append(
                    f"stage {stage_id} left a {gap}-cycle bubble before token {token + 1}"
                )
        if covered < token_count - 1:
            blockers.append(
                f"pipeline trace does not cover every adjacent-token turnover for stage {stage_id}"
            )

    whole_sequence_barrier_evidence = []
    for stage in stage_contracts:
        stage_id = str(stage["stage_id"])
        inputs = [str(value) for value in stage.get("input_boundaries", [])]
        outputs = [str(value) for value in stage.get("output_boundaries", [])]
        first_output = [first_cycle.get((boundary, 0)) for boundary in outputs]
        final_input = [last_cycle.get((boundary, token_count - 1)) for boundary in inputs]
        if any(value is None for value in first_output + final_input):
            continue
        first_output_cycle = min(int(value) for value in first_output if value is not None)
        final_input_cycle = max(int(value) for value in final_input if value is not None)
        barrier_free = first_output_cycle < final_input_cycle
        whole_sequence_barrier_evidence.append(
            {
                "stage_id": stage_id,
                "token_0_first_output_cycle": first_output_cycle,
                "final_token_last_input_cycle": final_input_cycle,
                "whole_sequence_barrier_observed": not barrier_free,
            }
        )
        if not barrier_free:
            blockers.append(
                f"stage {stage_id} waits for the complete token sequence before its first output"
            )
    if len(whole_sequence_barrier_evidence) != len(stage_order):
        blockers.append("pipeline trace cannot exclude a whole-sequence barrier at every stage")

    dependency_overlap_evidence = []
    for edge in dependency_edges:
        src_stage = str(edge.get("src_stage") or "")
        dst_stage = str(edge.get("dst_stage") or "")
        required_for_acceptance = (
            edge.get("overlap_requirement") == "required"
            if rate_insensitive
            else True
        )
        overlaps = []
        if rate_insensitive:
            for downstream_token in range(token_count - 1):
                downstream = stage_intervals.get((dst_stage, downstream_token))
                if downstream is None:
                    continue
                for upstream_token in range(downstream_token + 1, token_count):
                    upstream = stage_intervals.get((src_stage, upstream_token))
                    if upstream is None:
                        continue
                    start = max(upstream[0], downstream[0])
                    end = min(upstream[1], downstream[1])
                    if start <= end:
                        overlaps.append(
                            {
                                "upstream_token": upstream_token,
                                "downstream_token": downstream_token,
                                "token_distance": upstream_token - downstream_token,
                                "overlap_start_cycle": start,
                                "overlap_end_cycle": end,
                            }
                        )
                        break
                if len(overlaps) >= 8:
                    break
        else:
            for token in range(token_count - 1):
                upstream = stage_intervals.get((src_stage, token + 1))
                downstream = stage_intervals.get((dst_stage, token))
                if upstream is None or downstream is None:
                    continue
                start = max(upstream[0], downstream[0])
                end = min(upstream[1], downstream[1])
                if start <= end:
                    overlaps.append(
                        {
                            "upstream_token": token + 1,
                            "downstream_token": token,
                            "overlap_start_cycle": start,
                            "overlap_end_cycle": end,
                        }
                    )
        observed = bool(overlaps)
        dependency_overlap_evidence.append(
            {
                "boundary_id": edge.get("boundary_id"),
                "src_stage": src_stage,
                "dst_stage": dst_stage,
                "relationship": edge.get("relationship"),
                "overlap_requirement": edge.get("overlap_requirement"),
                "required_for_acceptance": required_for_acceptance,
                "different_token_overlap_observed": observed,
                "overlaps": overlaps[:8],
            }
        )
        if required_for_acceptance and not observed:
            blockers.append(
                f"required dataflow stages {src_stage} -> {dst_stage} never have different tokens in flight concurrently"
            )

    required_dependency_rows = [
        row
        for row in dependency_overlap_evidence
        if row["required_for_acceptance"] is True
    ]
    participating_stage_ids = {
        str(row[key])
        for row in required_dependency_rows
        if row["different_token_overlap_observed"] is True
        for key in ("src_stage", "dst_stage")
    }
    missing_overlap_stage_ids = [
        stage_id for stage_id in stage_order if stage_id not in participating_stage_ids
    ]
    require_stage_participation = bool(
        rate_insensitive
        and contract.get("acceptance", {}).get(
            "every_planned_stage_participates_in_required_overlap"
        )
        is True
    )
    if require_stage_participation and missing_overlap_stage_ids:
        blockers.append(
            "planned stages lack required cross-stage different-token overlap: "
            + ", ".join(missing_overlap_stage_ids)
        )

    candidate_cycles = sorted(
        {
            cycle
            for interval in stage_intervals.values()
            for cycle in interval
        }
    )
    maximum_concurrent_stage_count = 0
    maximum_concurrency_snapshot: dict[str, Any] = {}
    for cycle in candidate_cycles:
        active = {
            stage_id: token
            for (stage_id, token), interval in stage_intervals.items()
            if interval[0] <= cycle <= interval[1]
        }
        if len(active) > maximum_concurrent_stage_count:
            maximum_concurrent_stage_count = len(active)
            maximum_concurrency_snapshot = {
                "cycle": cycle,
                "active_stage_tokens": active,
            }
    required_concurrent_stage_count = int(
        contract.get("acceptance", {}).get(
            "minimum_concurrent_stage_count", len(stage_order)
        )
    )
    if maximum_concurrent_stage_count < required_concurrent_stage_count:
        if rate_insensitive:
            blockers.append(
                "no cross-stage token concurrency was observed: "
                f"observed={maximum_concurrent_stage_count} required={required_concurrent_stage_count}"
            )
        else:
            blockers.append(
                "all planned spatial stages were never concurrently active after pipeline fill: "
                f"observed={maximum_concurrent_stage_count} required={required_concurrent_stage_count}"
            )

    first_stage = stage_order[0] if stage_order else ""
    transition_evidence = [
        row for row in stage_turnover_evidence if row["stage_id"] == first_stage
    ]
    required_dependency_overlap_complete = bool(
        (
            required_dependency_rows
            or (rate_insensitive and len(stage_order) == 1)
        )
        and all(
            row["different_token_overlap_observed"] is True
            for row in required_dependency_rows
        )
    )
    stage_participation_complete = (
        not missing_overlap_stage_ids
        if require_stage_participation
        else rate_insensitive
    )
    return {
        "schema_version": (
            "spatialaccagent.single_layer_pipeline_overlap_evidence.v3"
            if rate_insensitive
            else "spatialaccagent.single_layer_pipeline_overlap_evidence.v2"
        ),
        "pipeline_semantics": (
            "elastic_rate_insensitive_token_pipeline"
            if rate_insensitive
            else "strict_adjacent_token_full_occupancy"
        ),
        "status": "pass" if not blockers else "fail",
        "contract_sha256": contract.get("contract_sha256"),
        "trace_record_count": len(records),
        "accepted_trace_record_count": len(accepted),
        "transition_evidence": transition_evidence,
        "boundary_order_evidence": boundary_order_evidence,
        "stage_activity_evidence": stage_activity_evidence,
        "stage_turnover_evidence": stage_turnover_evidence,
        "stage_turnover_gaps_are_diagnostic": rate_insensitive,
        "irreversible_stage_turnover_evidence": irreversible_turnover,
        "whole_sequence_barrier_evidence": whole_sequence_barrier_evidence,
        "dependency_overlap_evidence": dependency_overlap_evidence,
        "required_dependency_overlap_complete": required_dependency_overlap_complete,
        "all_planned_stages_participate_in_required_overlap": stage_participation_complete,
        "missing_required_overlap_stage_ids": (
            missing_overlap_stage_ids if require_stage_participation else []
        ),
        "planned_stage_count": len(stage_order),
        "maximum_concurrent_stage_count": maximum_concurrent_stage_count,
        "all_planned_stages_concurrent_observed": (
            maximum_concurrent_stage_count == len(stage_order)
        ),
        "all_planned_stages_same_cycle_concurrency_required": not rate_insensitive,
        "maximum_concurrency_snapshot": maximum_concurrency_snapshot,
        "terminal_trace_flush_inferred": terminal_flush_inferred,
        "terminal_trace_flush_evidence": terminal_flush,
        "blockers": blockers,
        "trace_sha256": hashlib.sha256(
            json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def decode_semantic_memh(path: Path, bits: int, lanes: int) -> Any:
    import torch

    values = []
    mask = (1 << bits) - 1
    for raw in path.read_text(encoding="ascii").splitlines():
        packed = int(raw.strip(), 16)
        values.extend((packed >> (lane * bits)) & mask for lane in range(lanes))
    if bits == 16:
        signed = [value - 0x10000 if value & 0x8000 else value for value in values]
        return torch.tensor(signed, dtype=torch.int16).view(torch.float16).float()
    if bits == 32:
        signed = [value - 0x100000000 if value & 0x80000000 else value for value in values]
        return torch.tensor(signed, dtype=torch.int32).view(torch.float32)
    raise ValueError(f"unsupported semantic vector width {bits}")


def compare_semantic_output(actual_path: Path, expected: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    import torch

    expected_path = Path(str(expected.get("path") or ""))
    if not actual_path.is_file() or not expected_path.is_file() or sha256_file(expected_path) != expected.get("sha256"):
        return {"passed": False, "error": "RTL or expected semantic output file/hash is missing"}
    actual = decode_semantic_memh(actual_path, int(expected.get("bits") or 0), int(expected.get("lanes") or 0))
    golden = decode_semantic_memh(expected_path, int(expected.get("bits") or 0), int(expected.get("lanes") or 0))
    if actual.numel() != golden.numel():
        return {"passed": False, "num_actual": actual.numel(), "num_expected": golden.numel(), "error": "output shape mismatch"}
    atol = float(policy.get("atol"))
    rtol = float(policy.get("rtol"))
    max_fraction = float(policy.get("max_mismatch_fraction"))
    close = torch.isclose(actual, golden, atol=atol, rtol=rtol, equal_nan=False) & torch.isfinite(actual) & torch.isfinite(golden)
    mismatch = ~close
    mismatch_count = int(mismatch.sum().item())
    difference = torch.abs(actual - golden)
    finite_difference = difference[torch.isfinite(difference)]
    fraction = mismatch_count / max(1, actual.numel())
    return {
        "passed": fraction <= max_fraction,
        "num_elements": int(actual.numel()),
        "num_mismatch": mismatch_count,
        "mismatch_fraction": fraction,
        "max_mismatch_fraction": max_fraction,
        "max_abs_error": float(finite_difference.max().item()) if finite_difference.numel() else float("inf"),
        "mean_abs_error": float(finite_difference.mean().item()) if finite_difference.numel() else float("inf"),
        "atol": atol,
        "rtol": rtol,
        "first_mismatch_index": int(torch.nonzero(mismatch, as_tuple=False)[0].item()) if mismatch_count else None,
    }


def adapter_paths(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "input" / "case_adapter.json"
    if not path.exists():
        return {}
    return read_json(path).get("paths", {}) if isinstance(read_json(path).get("paths"), dict) else {}


def first_existing(candidates: list[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def resolve_input_manifest(run_dir: Path, paths: dict[str, Any]) -> Path:
    candidates = [
        Path(str(paths.get("input_manifest"))) if paths.get("input_manifest") else None,
        Path(str(paths.get("packed_input_manifest"))) if paths.get("packed_input_manifest") else None,
        run_dir / "verification" / "model_weights" / "input_manifest.json",
    ]
    path = first_existing([p for p in candidates if p is not None])
    if path is None:
        raise FileNotFoundError("input manifest is missing")
    return path


def resolve_input_memh(run_dir: Path, paths: dict[str, Any], manifest: dict[str, Any]) -> Path:
    image = manifest.get("activation_image", {}) if isinstance(manifest.get("activation_image"), dict) else {}
    candidates = [
        Path(str(paths.get("input_memh"))) if paths.get("input_memh") else None,
        Path(str(image.get("path"))) if image.get("path") else None,
        run_dir / "verification" / "model_weights" / "input_activation.u32.memh",
    ]
    path = first_existing([p for p in candidates if p is not None])
    if path is None:
        raise FileNotFoundError("input activation memh is missing")
    return path


def top_stream_width(top_path: Path) -> int:
    text = read_text(top_path)
    match = re.search(r"input\s+\[(\d+):0\]\s+io_in_bits_data", text)
    if not match:
        raise ValueError(f"cannot infer io_in_bits_data width from {top_path}")
    return int(match.group(1)) + 1


def top_module_name(top_path: Path) -> str:
    text = read_text(top_path)
    match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
    if not match:
        raise ValueError(f"cannot infer top module name from {top_path}")
    return match.group(1)


def sv_files(chisel_dir: Path) -> list[Path]:
    filelist = chisel_dir / "filelist.f"
    if filelist.exists():
        result = []
        for raw in filelist.read_text(encoding="utf-8").splitlines():
            text = raw.strip()
            if not text or text.startswith("#"):
                continue
            path = Path(text)
            result.append(path if path.is_absolute() else chisel_dir / path)
        return result
    return sorted(chisel_dir.glob("*.sv"))


def harness_cpp(top_module: str, lanes: int) -> str:
    return f"""#include "V{top_module}.h"
#include "verilated.h"

#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static std::string arg_value(int argc, char** argv, const std::string& key, const std::string& def = "") {{
  for (int i = 1; i + 1 < argc; ++i) {{
    if (argv[i] == key) return argv[i + 1];
  }}
  return def;
}}

static uint64_t arg_u64(int argc, char** argv, const std::string& key, uint64_t def) {{
  std::string value = arg_value(argc, argv, key, "");
  if (value.empty()) return def;
  return std::stoull(value);
}}

static std::vector<uint32_t> read_memh(const std::string& path) {{
  std::ifstream in(path);
  std::vector<uint32_t> words;
  std::string token;
  while (in >> token) {{
    if (!token.empty() && token[0] == '@') continue;
    words.push_back(static_cast<uint32_t>(std::stoul(token, nullptr, 16)));
  }}
  return words;
}}

static void tick(V{top_module}& top, uint64_t& ticks) {{
  top.clock = 0;
  top.eval();
  ++ticks;
  top.clock = 1;
  top.eval();
  ++ticks;
}}

static void set_input_data(V{top_module}& top, const std::vector<uint32_t>& words, uint64_t beat) {{
  const uint64_t base = beat * {lanes};
  for (int i = 0; i < {lanes}; ++i) {{
    top.io_in_bits_data[i] = (base + static_cast<uint64_t>(i) < words.size()) ? words[base + i] : 0;
  }}
}}

static std::string beat_hex(const WData* data) {{
  std::ostringstream os;
  os << std::hex << std::setfill('0');
  for (int i = {lanes} - 1; i >= 0; --i) os << std::setw(8) << data[i];
  return os.str();
}}

int main(int argc, char** argv) {{
  Verilated::commandArgs(argc, argv);
  const std::string input_path = arg_value(argc, argv, "--input");
  const std::string output_path = arg_value(argc, argv, "--output");
  const std::string stats_path = arg_value(argc, argv, "--stats");
  const uint64_t expected_beats = arg_u64(argc, argv, "--expected-beats", 1);
  const uint64_t token_beats = arg_u64(argc, argv, "--token-beats", expected_beats);
  const uint64_t max_cycles = arg_u64(argc, argv, "--max-cycles", 2000000);
  const uint64_t no_progress_limit = arg_u64(argc, argv, "--no-progress-limit", 300000);

  std::vector<uint32_t> input_words = read_memh(input_path);
  V{top_module} top;
  uint64_t ticks = 0;
  uint64_t input_beats = 0;
  uint64_t output_beats = 0;
  uint64_t last_progress = 0;
  uint64_t cycle = 0;
  bool timed_out = false;
  bool no_progress = false;

  top.clock = 0;
  top.reset = 1;
  top.io_start = 0;
  top.io_position = 0;
  top.io_in_valid = 0;
  top.io_in_bits_st = 0;
  top.io_in_bits_addr = 0;
  top.io_in_bits_last = 0;
  top.io_out_ready = 1;
  for (int i = 0; i < 12; ++i) tick(top, ticks);
  top.reset = 0;
  for (int i = 0; i < 4; ++i) tick(top, ticks);
  top.io_start = 1;
  tick(top, ticks);
  top.io_start = 0;

  std::ofstream out(output_path);
  for (cycle = 0; cycle < max_cycles && output_beats < expected_beats; ++cycle) {{
    const bool have_input = input_beats < expected_beats;
    top.io_in_valid = have_input ? 1 : 0;
    top.io_out_ready = 1;
    if (have_input) {{
      set_input_data(top, input_words, input_beats);
      const uint64_t token_index = token_beats ? (input_beats % token_beats) : input_beats;
      top.io_in_bits_st = (token_index == 0) ? 1 : 0;
      top.io_in_bits_addr = static_cast<uint16_t>(token_index & 0x7ffu);
      top.io_in_bits_last = (token_beats && token_index == token_beats - 1) ? 1 : 0;
    }} else {{
      top.io_in_bits_st = 0;
      top.io_in_bits_addr = 0;
      top.io_in_bits_last = 0;
    }}
    tick(top, ticks);
    if (have_input && top.io_in_ready) {{
      ++input_beats;
      last_progress = cycle;
    }}
    if (top.io_out_valid && top.io_out_ready) {{
      out << beat_hex(top.io_out_bits_data) << "\\n";
      ++output_beats;
      last_progress = cycle;
    }}
    if (cycle > last_progress && cycle - last_progress > no_progress_limit) {{
      no_progress = true;
      break;
    }}
  }}
  if (output_beats < expected_beats && cycle >= max_cycles) timed_out = true;
  const bool pass = (input_beats == expected_beats) && (output_beats >= expected_beats) && !timed_out && !no_progress;
  std::ofstream stats(stats_path);
  stats << "{{\\n";
  stats << "  \\"status\\": \\"" << (pass ? "pass" : "fail") << "\\",\\n";
  stats << "  \\"input_beats\\": " << input_beats << ",\\n";
  stats << "  \\"output_beats\\": " << output_beats << ",\\n";
  stats << "  \\"expected_beats\\": " << expected_beats << ",\\n";
  stats << "  \\"cycles\\": " << cycle << ",\\n";
  stats << "  \\"last_progress_cycle\\": " << last_progress << ",\\n";
  stats << "  \\"timed_out\\": " << (timed_out ? "true" : "false") << ",\\n";
  stats << "  \\"no_progress\\": " << (no_progress ? "true" : "false") << "\\n";
  stats << "}}\\n";
  top.final();
  return pass ? 0 : 1;
}}
"""


def compile_and_run(
    run_dir: Path,
    chisel_dir: Path,
    top_path: Path,
    input_memh: Path,
    expected_beats: int,
    token_beats: int,
    max_cycles: int,
    no_progress_limit: int,
) -> tuple[dict[str, Any], Path, Path]:
    top = top_module_name(top_path)
    width = top_stream_width(top_path)
    if width % 32 != 0:
        raise ValueError(f"top stream width must be a multiple of 32 bits, got {width}")
    lanes = width // 32
    out_dir = run_dir / "verification" / "single_layer"
    build_dir = out_dir / "verilator_build"
    harness_path = out_dir / "single_layer_harness.cpp"
    output_path = out_dir / "single_layer_output.memh"
    stats_path = out_dir / "single_layer_sim_stats.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    harness_path.write_text(harness_cpp(top, lanes), encoding="utf-8")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    cmd = [
        "verilator",
        "--cc",
        "--exe",
        "--build",
        "--top-module",
        top,
        "--Mdir",
        str(build_dir),
        "--Wno-fatal",
        *[str(path) for path in sv_files(chisel_dir)],
        str(harness_path),
    ]
    compile_proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if compile_proc.returncode != 0:
        stats = {
            "status": "fail",
            "phase": "verilator_compile",
            "summary": f"verilator compile failed returncode={compile_proc.returncode}",
            "stdout_tail": compile_proc.stdout[-8000:],
            "stderr_tail": compile_proc.stderr[-8000:],
            "command": cmd,
        }
        return stats, output_path, stats_path
    binary = build_dir / f"V{top}"
    run_cmd = [
        str(binary),
        "--input",
        str(input_memh),
        "--output",
        str(output_path),
        "--stats",
        str(stats_path),
        "--expected-beats",
        str(expected_beats),
        "--token-beats",
        str(token_beats),
        "--max-cycles",
        str(max_cycles),
        "--no-progress-limit",
        str(no_progress_limit),
    ]
    run_proc = subprocess.run(run_cmd, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    stats = read_json(stats_path) if stats_path.exists() else {}
    stats.update(
        {
            "phase": "verilator_run",
            "returncode": run_proc.returncode,
            "stdout_tail": run_proc.stdout[-8000:],
            "stderr_tail": run_proc.stderr[-8000:],
            "command": run_cmd,
            "verilator_compile_command": cmd,
        }
    )
    if run_proc.returncode != 0 and stats.get("status") != "fail":
        stats["status"] = "fail"
    return stats, output_path, stats_path


def functional_mode(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.resolve()
    semantic_path, semantic = semantic_manifest(run_dir)
    if semantic_path.exists():
        section = semantic.get("single_layer", {}) if isinstance(semantic.get("single_layer"), dict) else {}
        targeted_replay = connected_kernel_targeted_replay_requested(args)
        replay_manifest: dict[str, Any] = {}
        if targeted_replay:
            _, immutable = immutable_semantic_replay_inputs(run_dir)
            replay_path, replay_manifest = materialize_connected_kernel_replay_testbench(run_dir, section)
            if immutable.get("status") == "pass" and replay_manifest.get("status") == "pass" and replay_path is not None:
                stats, output_path = run_generated_semantic_tb(
                    run_dir,
                    semantic,
                    replay_semantic_contract(section, replay_path),
                )
            else:
                stats = {
                    "status": "fail",
                    "phase": "connected_kernel_targeted_replay_preparation",
                    "summary": "connected-kernel direct replay inputs or testbench are not ready",
                    "blockers": [
                        *immutable.get("blockers", []),
                        *replay_manifest.get("blockers", []),
                    ],
                }
                output_path = Path(str(section.get("rtl_output_capture") or ""))
        else:
            stats, output_path = run_generated_semantic_tb(run_dir, semantic)
        overlap = pipeline_overlap_evidence(stats, section)
        status = "pass" if stats.get("status") == "pass" and overlap.get("status") == "pass" else "fail"
        report = {
            "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
            "verification_layer": "layer2_connected_single_transformer",
            "status": status,
            "run_dir": str(run_dir),
            "semantic_testbench_manifest": str(semantic_path),
            "semantic_testbench_sha256": sha256_file(semantic_path),
            "testbench": section.get("testbench"),
            "testbench_sha256": section.get("testbench_sha256"),
            "input_vector": section.get("input_vector"),
            "output_memh": str(output_path),
            "stats": stats,
            "pipeline_overlap_evidence": overlap,
            "output_sha256": sha256_file(output_path),
            "real_weight_execution": {
                "verified": section.get("real_weight_binding_verified") is True,
                "binding_manifest": semantic.get("dut_weight_binding_manifest"),
                "consumed_tensor_hashes": section.get("dut_harness", {}).get("consumed_tensor_hashes", []),
            },
            "policy": {
                "real_weight_semantic_harness_required": True,
                "remote_vcs_execution_required": True,
                "elastic_rate_insensitive_operator_token_pipeline_required": True,
                "legacy_pattern_input_is_not_acceptance": True,
            },
        }
        cctg_replay_path = write_cctg_boundary_replay(run_dir, stats, section)
        if cctg_replay_path is not None:
            cctg_replay = read_json(cctg_replay_path)
            report["cctg_boundary_replay"] = {
                "path": str(cctg_replay_path),
                "sha256": sha256_file(cctg_replay_path),
                "status": cctg_replay.get("status"),
            }
        if targeted_replay:
            direct = materialize_connected_kernel_targeted_replay_evidence(
                run_dir,
                stats,
                cctg_replay if cctg_replay_path is not None else {},
            )
            report["connected_kernel_targeted_replay"] = {
                "manifest": replay_manifest,
                "trace": {
                    "path": str(direct["trace_path"]),
                    "sha256": sha256_file(direct["trace_path"]),
                    "status": direct["trace"].get("status"),
                },
                "causal_context": {
                    "path": str(direct["context_path"]),
                    "sha256": sha256_file(direct["context_path"]),
                    "status": direct["context"].get("status"),
                },
                "reconciliation": {
                    "path": str(direct["reconciliation_path"]),
                    "sha256": sha256_file(direct["reconciliation_path"]),
                    "status": direct["reconciliation"].get("status"),
                },
            }
            if direct["trace"].get("status") != "pass":
                status = "fail"
                report["status"] = "fail"
        report_path = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
        write_json(report_path, report)
        hierarchy_path = run_dir / "verification" / "case_hierarchy" / "single_layer_functional.json"
        write_json(hierarchy_path, {**report, "gate": "single_layer_functional"})
        expected_beats = int(section.get("expected_output", {}).get("beats") or 0)
        write_boundary_trace(run_dir, report, expected_beats)
        print(report_path)
        return 0 if status == "pass" else 1
    paths = adapter_paths(run_dir)
    chisel_dir = run_dir / "generated" / "chisel"
    top_path = chisel_dir / "GeneratedAcceleratorTop.sv"
    input_manifest_path = resolve_input_manifest(run_dir, paths)
    input_manifest = read_json(input_manifest_path)
    input_memh = resolve_input_memh(run_dir, paths, input_manifest)
    image = input_manifest.get("activation_image", {}) if isinstance(input_manifest.get("activation_image"), dict) else {}
    expected_beats = int(args.expected_beats or image.get("stream_beats") or 0)
    if expected_beats <= 0:
        width = top_stream_width(top_path)
        word_count = sum(1 for line in input_memh.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("@"))
        expected_beats = max(1, word_count // max(1, width // 32))
    hidden = int(image.get("hidden_size") or 0)
    lanes = int(image.get("lanes") or max(1, top_stream_width(top_path) // 32))
    token_beats = int(args.token_beats or (hidden // lanes if hidden and lanes else expected_beats))
    max_cycles = int(args.max_cycles or os.environ.get("SPATIALACC_SINGLE_LAYER_MAX_CYCLES", 0) or max(2_000_000, expected_beats * 4000))
    no_progress_limit = int(args.no_progress_limit or os.environ.get("SPATIALACC_SINGLE_LAYER_NO_PROGRESS_LIMIT", 300000))
    stats, output_path, stats_path = compile_and_run(
        run_dir,
        chisel_dir,
        top_path,
        input_memh,
        expected_beats,
        token_beats,
        max_cycles,
        no_progress_limit,
    )
    status = "pass" if stats.get("status") == "pass" else "fail"
    report = {
        "schema_version": "spatialaccagent.single_layer_functional_sim.v0",
        "verification_layer": "layer2_connected_single_transformer",
        "status": status,
        "run_dir": str(run_dir),
        "top": str(top_path),
        "input_manifest": str(input_manifest_path),
        "input_memh": str(input_memh),
        "output_memh": str(output_path),
        "stats": stats,
        "output_sha256": sha256_file(output_path),
        "policy": {
            "real_verilator_execution_required": True,
            "functional_acceptance": "input and output stream transaction counts must match the real activation stream beats",
            "not_bit_exact_model_claim": True,
        },
    }
    report_path = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
    write_json(report_path, report)
    hierarchy_path = run_dir / "verification" / "case_hierarchy" / "single_layer_functional.json"
    if hierarchy_path.parent.exists():
        write_json(hierarchy_path, {**report, "gate": "single_layer_functional"})
    write_boundary_trace(run_dir, report, expected_beats)
    print(report_path)
    return 0 if status == "pass" else 1


def write_boundary_trace(run_dir: Path, report: dict[str, Any], expected_beats: int) -> None:
    stats = report.get("stats", {}) if isinstance(report.get("stats"), dict) else {}
    transport_passed = stats.get("status") == "pass"
    transport_record = {
        "cycle": stats.get("cycles"),
        "boundary_id": "boundary.single_layer.block_input_to_block_output",
        "tx_id": expected_beats if transport_passed else 0,
        "tile_id": 0,
        "logical_index": [0, expected_beats if transport_passed else 0],
        "observed_value": expected_beats if transport_passed else 0,
        "expected_value": expected_beats,
        "contract": "single_layer_stream_transaction_count",
        "status": "pass" if transport_passed else "fail",
        "module": "single_transformer_layer_kernel",
        "summary": "single layer stream transaction count matched" if transport_passed else "single layer stream transaction count did not match",
    }
    overlap = (
        report.get("pipeline_overlap_evidence", {})
        if isinstance(report.get("pipeline_overlap_evidence"), dict)
        else {}
    )
    overlap_passed = overlap.get("status") == "pass"
    overlap_witness_count = sum(
        len(row.get("overlaps", []))
        for row in overlap.get("dependency_overlap_evidence", [])
        if isinstance(row, dict) and row.get("required_for_acceptance") is True
    )
    overlap_record = {
        "cycle": None,
        "boundary_id": "boundary.single_layer.elastic_token_pipeline_overlap",
        "tx_id": overlap_witness_count,
        "tile_id": 0,
        "logical_index": [0, overlap_witness_count],
        "observed_value": overlap_passed,
        "expected_value": True,
        "contract": "single_layer_elastic_rate_insensitive_token_pipeline",
        "status": "pass" if overlap_passed else "fail",
        "module": "single_transformer_layer_kernel",
        "summary": (
            "different tokens overlapped across every required connected dataflow edge"
            if overlap_passed
            else "; ".join(str(value) for value in overlap.get("blockers", [])[:2])
        ),
    }
    trace = {
        "schema_version": "spatialaccagent.boundary_trace.v0",
        "status": "ready",
        "boundary_trace": [transport_record, overlap_record],
    }
    write_json(run_dir / "verification" / "debug_closure" / "boundary_trace.json", trace)


def golden_mode(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.resolve()
    semantic_path, semantic = semantic_manifest(run_dir)
    if semantic_path.exists():
        section = semantic.get("single_layer", {}) if isinstance(semantic.get("single_layer"), dict) else {}
        functional_report = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
        output_path = Path(str(section.get("rtl_output_capture") or ""))
        blockers = []
        if semantic.get("status") != "ready" or section.get("real_weight_binding_verified") is not True:
            blockers.append("semantic testbench or DUT real-weight binding is not ready")
        if not functional_report.is_file() or read_json(functional_report).get("status") != "pass":
            blockers.append("real-weight single-layer functional simulation has not passed")
        metrics: dict[str, Any] = {}
        if not blockers:
            metrics = compare_semantic_output(
                output_path,
                section.get("expected_output", {}),
                semantic.get("numeric_comparison_policy", {}),
            )
            if metrics.get("passed") is not True:
                blockers.append("single-layer RTL output does not satisfy target-model semantic tolerance")
        consumed_hashes = section.get("dut_harness", {}).get("consumed_tensor_hashes", [])
        comparison = {
            "status": "pass" if not blockers else "fail",
            "passed": not blockers,
            "expected_output_source": "target_model_inference",
            "expected_output_sha256": section.get("expected_output", {}).get("sha256"),
            "rtl_output_sha256": sha256_file(output_path),
            "testbench_sha256": section.get("testbench_sha256"),
            "consumed_tensor_hashes": consumed_hashes,
            "numeric_metrics": metrics,
        }
        report = {
            "schema_version": "spatialaccagent.single_layer_golden_compare.v1",
            "status": "pass" if not blockers else "fail",
            "run_dir": str(run_dir),
            "functional_report": str(functional_report),
            "output_memh": str(output_path),
            "golden_memh": section.get("expected_output", {}).get("path"),
            "output_sha256": sha256_file(output_path),
            "golden_sha256": section.get("expected_output", {}).get("sha256"),
            "matched": not blockers,
            "semantic_comparison": comparison,
            "blockers": blockers,
            "policy": {
                "target_model_inference_reference_required": True,
                "same_random_input_and_checkpoint_required": True,
                "do_not_loosen_tolerance_or_edit_golden_to_pass": True,
            },
        }
        report_path = run_dir / "verification" / "single_layer" / "single_layer_golden_compare.json"
        write_json(report_path, report)
        hierarchy_path = run_dir / "verification" / "case_hierarchy" / "single_layer_golden_compare.json"
        write_json(hierarchy_path, {**report, "gate": "single_layer_golden_compare"})
        print(report_path)
        return 0 if not blockers else 1
    paths = adapter_paths(run_dir)
    output_path = run_dir / "verification" / "single_layer" / "single_layer_output.memh"
    functional_report = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
    golden_candidates = []
    if args.golden:
        golden_candidates.append(args.golden)
    if paths.get("single_layer_golden_memh"):
        golden_candidates.append(Path(str(paths["single_layer_golden_memh"])))
    golden_candidates.extend(
        [
            run_dir / "verification" / "single_layer" / "single_layer_golden.memh",
            run_dir / "verification" / "case_real_weights" / "single_layer_golden.memh",
        ]
    )
    golden_path = first_existing(golden_candidates)
    blockers: list[str] = []
    if not functional_report.exists():
        blockers.append(f"functional report missing: {functional_report}")
    if not output_path.exists():
        blockers.append(f"functional output missing: {output_path}")
    if golden_path is None:
        blockers.append("single-layer golden reference memh is missing; provide adapter path single_layer_golden_memh or --golden")
    matched = False
    if not blockers and golden_path is not None:
        matched = output_path.read_text(encoding="utf-8").splitlines() == golden_path.read_text(encoding="utf-8").splitlines()
        if not matched:
            blockers.append("single-layer output does not match independent golden reference")
    status = "pass" if not blockers else "fail"
    report = {
        "schema_version": "spatialaccagent.single_layer_golden_compare.v0",
        "status": status,
        "run_dir": str(run_dir),
        "functional_report": str(functional_report),
        "output_memh": str(output_path),
        "golden_memh": str(golden_path) if golden_path else None,
        "output_sha256": sha256_file(output_path),
        "golden_sha256": sha256_file(golden_path) if golden_path else None,
        "matched": matched,
        "blockers": blockers,
        "policy": {
            "independent_reference_required": True,
            "missing_golden_is_not_hardware_pass": True,
            "do_not_loosen_tolerance_or_edit_golden_to_pass": True,
        },
    }
    report_path = run_dir / "verification" / "single_layer" / "single_layer_golden_compare.json"
    write_json(report_path, report)
    hierarchy_path = run_dir / "verification" / "case_hierarchy" / "single_layer_golden_compare.json"
    if hierarchy_path.parent.exists():
        write_json(hierarchy_path, {**report, "gate": "single_layer_golden_compare"})
    print(report_path)
    return 0 if status == "pass" else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run generated single-layer stream simulation or golden compare")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["functional", "golden"], default="functional")
    parser.add_argument(
        "--rematerialize-cctg-evidence",
        action="store_true",
        help="rebuild CCTG evidence from one already-completed fresh VCS execution without rerunning VCS",
    )
    parser.add_argument(
        "--connected-kernel-targeted-replay",
        action="store_true",
        help="run a fresh immutable-input replay with verification-only connected-kernel lifecycle probes",
    )
    parser.add_argument("--golden", type=Path)
    parser.add_argument("--expected-beats", type=int)
    parser.add_argument("--token-beats", type=int)
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--no-progress-limit", type=int)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.rematerialize_cctg_evidence:
            report_path, report = rematerialize_cctg_boundary_replay(args.run_dir.resolve())
            print(report_path)
            return 0 if report.get("status") == "pass" else 1
        if args.mode == "golden":
            return golden_mode(args)
        return functional_mode(args)
    except Exception as exc:
        out = args.run_dir / "verification" / "single_layer"
        report_path = out / ("single_layer_golden_compare.json" if args.mode == "golden" else "single_layer_functional_report.json")
        write_json(
            report_path,
            {
                "schema_version": "spatialaccagent.single_layer_stream_sim.error.v0",
                "status": "fail",
                "mode": args.mode,
                "error": str(exc),
            },
        )
        print(f"error: {exc}", file=sys.stderr)
        print(report_path)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
