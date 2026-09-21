"""Read-only binding for an exact-board VCS job that still needs collection."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .live_state import (
    activate_live_state_slot,
    board_run_binding,
    board_run_status,
)
from .semantic_simulator import REMOTE_SEMANTIC_JOB_CONTRACT


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_pending_exact_board_job_report(
    run_dir: Path,
    pending_job: dict[str, Any],
) -> dict[str, Any]:
    """Make the fixed runner report describe the current job immediately.

    The report path is a live pointer, not a history store.  Replacing it as
    soon as a contract exists prevents a previous job's terminal state from
    being mistaken for the current remote job.
    """

    job = pending_job.get("job", {})
    fingerprint = str(job.get("input_fingerprint_sha256") or "")
    remote_workdir = str(job.get("remote_workdir") or "")
    report = {
        "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
        "verification_layer": "layer3_real_board_axi_ddr",
        "status": "pending",
        "phase": "active_exact_job_pending",
        "failure_class": "active_exact_job_pending",
        "stage_pass_eligible": False,
        "input_fingerprint_sha256": fingerprint,
        "remote_workdir": remote_workdir,
        "manifest": str(pending_job.get("manifest_path") or ""),
        "source_identity_sha256": job.get("source_identity_sha256"),
        "source_closure_sha256": job.get("source_closure_sha256"),
        "compile_source_set_sha256": job.get("compile_source_set_sha256"),
        "exact_job_contract_bound": True,
        "exact_board_preflight_at_launch": True,
        "exact_board_preflight_passed": True,
        "checkpoint_execution": job.get("checkpoint_execution", {}),
        "remote_job_recovery_contract": {
            "status": "pending",
            "job_contract": str(pending_job.get("job_path") or ""),
            "policy": "the current fingerprint is the only live job state",
        },
    }
    report_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = report_path.with_name(report_path.name + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, report_path)
    binding = board_run_binding(report)
    if binding:
        try:
            activate_live_state_slot(
                run_dir,
                "board_run",
                board_run_status(report),
                binding=binding,
            )
        except OSError:
            # The fixed runner report remains the board execution authority.
            pass
    return report


def pending_exact_board_job(run_dir: Path) -> dict[str, Any] | None:
    """Return a manifest-bound job until its terminal VCS report is recorded.

    The contract is intentionally read-only.  It prevents preparatory tools from
    changing the source inputs of a real remote simulation that is already live.
    """

    stage_dir = run_dir / "verification" / "board_simulation" / "vcs_stage"
    job_path = stage_dir / REMOTE_SEMANTIC_JOB_CONTRACT
    manifest_path = (
        run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
    )
    report_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    job = _read_json(job_path)
    manifest = _read_json(manifest_path)
    if not job or not manifest:
        return None
    fingerprint = str(job.get("input_fingerprint_sha256") or "")
    if (
        re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
        or not str(job.get("remote_workdir") or "")
    ):
        return None
    for field in (
        "source_identity_sha256",
        "source_closure_sha256",
        "compile_source_set_sha256",
    ):
        if not job.get(field) or job.get(field) != manifest.get(field):
            return None
    report = _read_json(report_path)
    if report.get("input_fingerprint_sha256") == fingerprint:
        # A completed attachment can be written before the normal execution
        # path materializes the full executed manifest.  Keep that exact job
        # eligible for one hash-bound collection pass; never relaunch it.
        if not (
            (
                report.get("phase") == "active_exact_job_collection"
                and report.get("failure_class")
                == "active_exact_job_terminal_acceptance_required"
            )
            or report.get("phase") == "active_exact_job_pending"
        ):
            return None
    return {
        "job": job,
        "job_path": job_path,
        "manifest_path": manifest_path,
    }
