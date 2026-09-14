"""Read-only binding for an exact-board VCS job that still needs collection."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .semantic_simulator import REMOTE_SEMANTIC_JOB_CONTRACT


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


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
            report.get("phase") == "active_exact_job_collection"
            and report.get("failure_class")
            == "active_exact_job_terminal_acceptance_required"
        ):
            return None
    return {
        "job": job,
        "job_path": job_path,
        "manifest_path": manifest_path,
    }
