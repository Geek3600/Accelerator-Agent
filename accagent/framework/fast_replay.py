"""Optional fast replay decisions for the Layer-3 debug loop.

This module is deliberately separate from Agent reasoning.  For an eligible
observation-only iteration, the fast path is the normal execution path: a
missing or invalid cache is prepared or repaired, rather than being treated
as permission to silently launch a cold run.  A cold run is selected only
when the compiled model itself changed, or for the final Layer-3 acceptance.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
import json
from typing import Any, Iterable

from .live_state import (
    activate_live_state_slot,
    read_live_state,
    update_live_state_slot,
)


FAST_REPLAY_SCHEMA_VERSION = "spatialaccagent.fast_replay_decision.v1"
STABLE_CHECKPOINT_CUT = "after_weight_load_before_first_token"
STABLE_CHECKPOINT_VALIDATION_FIELDS = (
    "compiled_model_sha256",
    "workload_sha256",
    "cut",
    "verified",
)

_OBSERVATION_ONLY_MARKERS = (
    "/runtime_observation/",
    "/observer_runtime/",
    "/monitor_runtime/",
    "/verification/adaptive_observation/",
)
_OBSERVATION_ONLY_SUFFIXES = {
    ".jsonl",
    ".csv",
    ".log",
}
_COMPILED_SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sv",
    ".svh",
    ".v",
    ".vh",
    ".vhd",
    ".vhdl",
    ".vp",
    ".svp",
    ".tab",
    ".f",
}
_DUT_OR_WRAPPER_MARKERS = (
    "/sources/",
    "app_shell_",
    "axi_protocol_monitor",
    "board_wrapper",
    "ddr",
)


def _normal_path(value: Any) -> str:
    return str(value or "").replace("\\", "/")


def classify_changed_sources(paths: Iterable[Any]) -> dict[str, Any]:
    """Classify changed files without making the classification a hard gate."""

    changed = sorted({_normal_path(path) for path in paths if _normal_path(path)})
    observation_only: list[str] = []
    functional: list[str] = []
    unknown: list[str] = []
    for path in changed:
        lower = path.lower()
        suffix = Path(path).suffix.lower()
        if (
            any(marker in lower for marker in _OBSERVATION_ONLY_MARKERS)
            and suffix in _OBSERVATION_ONLY_SUFFIXES
        ):
            observation_only.append(path)
        elif (
            suffix in _COMPILED_SOURCE_SUFFIXES
            or any(marker in lower for marker in _DUT_OR_WRAPPER_MARKERS)
        ):
            functional.append(path)
        else:
            unknown.append(path)
    kind = "observation_only" if observation_only and not functional and not unknown else (
        "functional" if functional else "unknown"
    )
    return {
        "schema_version": FAST_REPLAY_SCHEMA_VERSION,
        "kind": kind,
        "changed_paths": changed,
        "observation_only_paths": observation_only,
        "functional_paths": functional,
        "unknown_paths": unknown,
    }


def fast_replay_decision(
    *,
    enabled: bool,
    source_classification: dict[str, Any],
    compiled_model_sha256: str,
    workload_sha256: str,
    cached_simv: Path | None,
    token_checkpoint_manifest: Path | None,
    current_checkpoint_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an execution decision that keeps fast replay as the default.

    Missing fast-path artifacts are preparation work.  They are not a reason
    to switch to cold execution for an observation-only iteration.
    """

    reasons: list[str] = []
    kind = source_classification.get("kind")
    if kind != "observation_only":
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "cold_required_for_model_change",
            "enabled": bool(enabled),
            "mode": "cold_vcs",
            "reuse_compiled_simv": False,
            "reuse_token_input_checkpoint": False,
            "reasons": ["changed source is not observation-only"],
            "final_acceptance_requires_cold_run": True,
        }
    if not enabled:
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "fast_replay_required_but_disabled",
            "enabled": False,
            "mode": "prepare_fast_replay",
            "reuse_compiled_simv": False,
            "reuse_token_input_checkpoint": False,
            "reasons": ["fast replay must be explicitly enabled for this path"],
            "final_acceptance_requires_cold_run": True,
        }
    preparation_reasons: list[str] = []
    if not compiled_model_sha256:
        preparation_reasons.append("compiled model identity is missing")
    if not workload_sha256:
        preparation_reasons.append("workload identity is missing")
    if cached_simv is None or not cached_simv.is_file():
        preparation_reasons.append("matching compiled simulator is unavailable")
    if token_checkpoint_manifest is None or not token_checkpoint_manifest.is_file():
        preparation_reasons.append("token-input checkpoint is unavailable")
    identity = current_checkpoint_identity or {}
    if identity.get("compiled_model_sha256") != compiled_model_sha256:
        preparation_reasons.append("checkpoint compiled-model identity does not match")
    if identity.get("workload_sha256") != workload_sha256:
        preparation_reasons.append("checkpoint workload identity does not match")
    ready = not preparation_reasons
    return {
        "schema_version": FAST_REPLAY_SCHEMA_VERSION,
        "status": "ready" if ready else "prepare_fast_replay",
        "enabled": bool(enabled),
        "mode": "observation_only_token_checkpoint" if ready else "prepare_fast_replay",
        "reuse_compiled_simv": ready,
        "reuse_token_input_checkpoint": ready,
        "reasons": preparation_reasons,
        "final_acceptance_requires_cold_run": True,
    }


def stable_checkpoint_lifecycle(
    *,
    enabled: bool,
    identity: dict[str, Any],
    checkpoint: dict[str, Any] | None,
    capture_result: dict[str, Any] | None = None,
    restore_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose one stable checkpoint action without creating a retry loop.

    The cut is fixed and intentionally independent of the current debug
    frontier.  A failed capture or restore is remembered for this exact model
    and workload identity, but it is routed to checkpoint repair or recapture.
    It must never silently turn into an ordinary cold validation run.
    """

    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    capture_result = capture_result if isinstance(capture_result, dict) else {}
    restore_result = restore_result if isinstance(restore_result, dict) else {}
    expected = {
        "compiled_model_sha256": str(identity.get("compiled_model_sha256") or ""),
        "workload_sha256": str(identity.get("workload_sha256") or ""),
        "cut": STABLE_CHECKPOINT_CUT,
    }
    reasons: list[str] = []
    if not enabled:
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "enable_required",
            "action": "enable_checkpoint",
            "cut": STABLE_CHECKPOINT_CUT,
            "reasons": ["fast replay is disabled"],
        }
    if checkpoint.get("identity") != expected:
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "capture_required",
            "action": "capture_once",
            "cut": STABLE_CHECKPOINT_CUT,
            "identity": expected,
            "capture_attempts": 0,
            "restore_attempts": 0,
            "reasons": ["no checkpoint matches the fixed token-input cut"],
        }
    if checkpoint.get("status") in {
        "disabled_for_identity",
        "repair_required",
        "invalidated",
        "failed",
    }:
        # Older executor versions could fail after a successful capture
        # without consuming the one restore check.  Retry that saved snapshot
        # once before paying the weight-load cost of a recapture.
        if (
            checkpoint.get("status") == "repair_required"
            and int(checkpoint.get("restore_attempts") or 0) == 0
            and str(
                checkpoint.get("checkpoint_manifest") or checkpoint.get("manifest") or ""
            ).strip()
        ):
            return {
                "schema_version": FAST_REPLAY_SCHEMA_VERSION,
                "status": "restore_check_required",
                "action": "restore_once_and_check",
                "cut": STABLE_CHECKPOINT_CUT,
                "identity": expected,
                "capture_attempts": checkpoint.get("capture_attempts", 1),
                "restore_attempts": 1,
                "reasons": [
                    "saved snapshot has one unconsumed restore check after executor repair"
                ],
            }
        remote_workdir = str(checkpoint.get("remote_workdir") or "").strip()
        simulator_path = str(checkpoint.get("simulator_path") or "").strip()
        simulator = Path(simulator_path)
        if (
            remote_workdir.startswith("/")
            and simulator_path
            and not simulator.is_absolute()
            and ".." not in simulator.parts
        ):
            return {
                "schema_version": FAST_REPLAY_SCHEMA_VERSION,
                "status": "recapture_required",
                "action": "recapture_existing_simv",
                "cut": STABLE_CHECKPOINT_CUT,
                "identity": expected,
                "capture_attempts": checkpoint.get("capture_attempts", 1),
                "restore_attempts": checkpoint.get("restore_attempts", 0),
                "reasons": [
                    "the previous native snapshot is invalid, but the matching "
                    "compiled simulator can be reused for recapture"
                ],
            }
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "repair_required",
            "action": "repair_or_recapture",
            "cut": STABLE_CHECKPOINT_CUT,
            "identity": expected,
            "reasons": [
                "previous capture or restore failed for this identity; "
                "repair or recapture is required"
            ],
        }
    if checkpoint.get("status") == "captured" and not checkpoint.get("verified"):
        if checkpoint.get("restore_attempts", 0) >= 1:
            return {
                "schema_version": FAST_REPLAY_SCHEMA_VERSION,
                "status": "repair_required",
                "action": "repair_or_recapture",
                "cut": STABLE_CHECKPOINT_CUT,
                "identity": expected,
                "reasons": [
                    "checkpoint restore was already attempted once; "
                    "repair or recapture is required"
                ],
            }
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "restore_check_required",
            "action": "restore_once_and_check",
            "cut": STABLE_CHECKPOINT_CUT,
            "identity": expected,
            "capture_attempts": checkpoint.get("capture_attempts", 1),
            "restore_attempts": 1,
            "reasons": ["checkpoint was captured and needs one restore check"],
        }
    if checkpoint.get("status") == "ready" and checkpoint.get("verified") is True:
        return {
            "schema_version": FAST_REPLAY_SCHEMA_VERSION,
            "status": "ready",
            "action": "restore_and_run",
            "cut": STABLE_CHECKPOINT_CUT,
            "identity": expected,
            "capture_attempts": checkpoint.get("capture_attempts", 1),
            "restore_attempts": checkpoint.get("restore_attempts", 1),
            "reasons": [],
        }
    if capture_result.get("status") == "fail" or restore_result.get("status") == "fail":
        reasons.append("one-time checkpoint capture or restore check failed")
    return {
        "schema_version": FAST_REPLAY_SCHEMA_VERSION,
        "status": "repair_required",
        "action": "repair_or_recapture",
        "cut": STABLE_CHECKPOINT_CUT,
        "identity": expected,
        "reasons": reasons or ["checkpoint state is not reusable; repair or recapture is required"],
    }


def validate_stable_checkpoint(
    checkpoint: dict[str, Any] | None,
    *,
    compiled_model_sha256: str,
    workload_sha256: str,
) -> dict[str, Any]:
    """Validate only the current minimal checkpoint contract.

    Historical manifests, extra fields, and legacy digest fields are ignored.
    This function only selects or rejects a checkpoint; it never blocks the
    validation loop.
    """

    value = checkpoint if isinstance(checkpoint, dict) else {}
    identity = value.get("identity") if isinstance(value.get("identity"), dict) else value
    checks = {
        "compiled_model_sha256": identity.get("compiled_model_sha256"),
        "workload_sha256": identity.get("workload_sha256"),
        "cut": identity.get("cut") or value.get("cut"),
        "verified": value.get("verified"),
    }
    reasons: list[str] = []
    if checks["compiled_model_sha256"] != compiled_model_sha256:
        reasons.append("current compiled model does not match")
    if checks["workload_sha256"] != workload_sha256:
        reasons.append("current workload does not match")
    if checks["cut"] != STABLE_CHECKPOINT_CUT:
        reasons.append("checkpoint is not at the fixed token-input cut")
    if checks["verified"] is not True:
        reasons.append("checkpoint has not passed its one-time restore check")
    return {
        "schema_version": FAST_REPLAY_SCHEMA_VERSION,
        "status": "ready" if not reasons else "not_reusable",
        "selected": not reasons,
        "required_fields": list(STABLE_CHECKPOINT_VALIDATION_FIELDS),
        "ignored_historical_fields": True,
        "reasons": reasons,
    }


def fast_replay_state_path(run_dir: Path) -> Path:
    """Return the durable state file for the current Layer-3 run."""

    return (
        Path(run_dir)
        / "verification"
        / "board_simulation"
        / "fast_replay_state.json"
    )


def fast_replay_request_path(run_dir: Path) -> Path:
    """Return the immutable request copy used by later replay runs."""

    return (
        Path(run_dir)
        / "verification"
        / "board_simulation"
        / "fast_replay_request.json"
    )


def read_fast_replay_state(run_dir: Path) -> dict[str, Any]:
    """Read the current replay state without turning stale data into a failure."""

    path = fast_replay_state_path(run_dir)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def validate_fast_replay_state(
    run_dir: Path,
    state: dict[str, Any] | None,
    *,
    current_identity: dict[str, Any],
    require_verified: bool = True,
) -> dict[str, Any]:
    """Validate the small set of facts required to reuse a remote ``simv``.

    This is intentionally only a small identity check. It does not compare
    historical hashes, validate past request contents, or decide whether the
    hardware run passed.
    """

    value = state if isinstance(state, dict) else {}
    reasons: list[str] = []
    expected_status = "ready" if require_verified else "captured"
    if value.get("status") != expected_status:
        reasons.append(f"fast replay state is not {expected_status}")
    if require_verified and value.get("verified") is not True:
        reasons.append("fast replay state has not passed its restore check")
    if not require_verified and value.get("verified") is not False:
        reasons.append("captured fast replay state is not awaiting restore confirmation")
    saved_identity = value.get("identity", {})
    saved_identity = saved_identity if isinstance(saved_identity, dict) else {}
    for field in ("compiled_model_sha256", "workload_sha256"):
        expected = str(current_identity.get(field) or "")
        actual = str(saved_identity.get(field) or "")
        if not expected or actual != expected:
            reasons.append(f"fast replay {field} does not match the current run")

    remote_workdir = str(value.get("remote_workdir") or "").strip()
    simulator_path = str(value.get("simulator_path") or "").strip()
    if not remote_workdir:
        reasons.append("fast replay remote workdir is missing")
    if not simulator_path or Path(simulator_path).is_absolute() or ".." in Path(simulator_path).parts:
        reasons.append("fast replay simulator path is missing or unsafe")

    manifest_value = str(value.get("checkpoint_manifest") or "").strip()
    manifest_path = Path(manifest_value).expanduser() if manifest_value else Path()
    checkpoint_root = (
        Path(run_dir) / "verification" / "simulation_checkpoints"
    ).resolve()
    if not manifest_path.is_absolute():
        manifest_path = (Path(run_dir) / manifest_path).resolve()
    else:
        manifest_path = manifest_path.resolve()
    if (
        not manifest_value
        or not manifest_path.is_file()
        or not manifest_path.is_relative_to(checkpoint_root)
    ):
        reasons.append("fast replay checkpoint manifest is missing or outside the store")
    else:
        manifest = _read_json_file(manifest_path)
        manifest_identity = manifest.get("execution_identity", {})
        manifest_identity = (
            manifest_identity if isinstance(manifest_identity, dict) else {}
        )
        for field in ("compiled_model_sha256", "workload_sha256"):
            if manifest_identity.get(field) != current_identity.get(field):
                reasons.append(f"checkpoint manifest {field} does not match the current run")
        if manifest.get("remote_acknowledgment_status") != "pass":
            reasons.append("checkpoint remote persistence is not acknowledged")
        native_rows = [
            row
            for row in manifest.get("state_artifacts", [])
            if isinstance(row, dict) and row.get("kind") == "native_vcs_snapshot"
        ]
        if len(native_rows) != 1:
            reasons.append("checkpoint has no single native VCS snapshot")
        else:
            native_path = Path(str(native_rows[0].get("remote_path") or ""))
            if (
                not native_path.name
                or native_path.is_absolute()
                or ".." in native_path.parts
            ):
                reasons.append("checkpoint native VCS snapshot path is unsafe")

    return {
        "schema_version": FAST_REPLAY_SCHEMA_VERSION,
        "status": "ready" if not reasons else "repair_required",
        "selected": not reasons,
        "remote_workdir": remote_workdir or None,
        "simulator_path": simulator_path or None,
        "checkpoint_manifest": str(manifest_path) if manifest_path else None,
        "reasons": reasons,
    }


def restore_inputs(run_dir: Path) -> dict[str, Any]:
    """Return saved replay inputs without reading current board source files.

    A restore check runs the simulator that was saved with the checkpoint.  It
    must therefore use the snapshot's own remote directory, simulator and
    state files.  Current generated sources may legitimately have changed for
    the next debug round, so their hashes are intentionally not part of this
    lookup.
    """

    state = read_fast_replay_state(run_dir)
    reasons: list[str] = []
    retry_after_executor_repair = (
        state.get("status") == "repair_required"
        and int(state.get("restore_attempts") or 0) == 0
        and str(
            state.get("checkpoint_manifest") or state.get("manifest") or ""
        ).strip()
    )
    if state.get("status") not in {"captured", "ready"} and not retry_after_executor_repair:
        reasons.append("saved replay state is not ready for restore")

    remote_workdir = str(state.get("remote_workdir") or "").strip()
    if not remote_workdir or not remote_workdir.startswith("/"):
        reasons.append("saved replay remote directory is missing")

    simulator_path = str(state.get("simulator_path") or "").strip()
    simulator = Path(simulator_path)
    if (
        not simulator_path
        or simulator.is_absolute()
        or ".." in simulator.parts
    ):
        reasons.append("saved replay simulator path is missing or unsafe")

    manifest_value = str(state.get("checkpoint_manifest") or "").strip()
    manifest_path = Path(manifest_value).expanduser() if manifest_value else Path()
    checkpoint_store = (
        Path(run_dir) / "verification" / "simulation_checkpoints"
    ).resolve()
    if manifest_path and not manifest_path.is_absolute():
        manifest_path = (Path(run_dir) / manifest_path).resolve()
    elif manifest_path:
        manifest_path = manifest_path.resolve()
    if (
        not manifest_value
        or not manifest_path.is_file()
        or not manifest_path.is_relative_to(checkpoint_store)
    ):
        reasons.append("saved replay checkpoint record is missing")
        manifest: dict[str, Any] = {}
    else:
        manifest = _read_json_file(manifest_path)
        if manifest.get("status") != "pass":
            reasons.append("saved replay checkpoint record is not complete")
        if manifest.get("remote_acknowledgment_status") != "pass":
            reasons.append("saved replay is not present on the remote host")
        saved_remote = str(manifest.get("remote_workdir") or "").strip()
        if saved_remote and remote_workdir and saved_remote != remote_workdir:
            reasons.append("saved replay remote directory does not match the checkpoint")

    state_rows = manifest.get("state_artifacts", []) if manifest else []
    state_rows = state_rows if isinstance(state_rows, list) else []
    native_rows = [
        row
        for row in state_rows
        if isinstance(row, dict) and row.get("kind") == "native_vcs_snapshot"
    ]
    native_snapshot_path = ""
    native_snapshot_files_path = ""
    if len(native_rows) != 1:
        reasons.append("saved replay has no single native VCS snapshot")
    else:
        native_snapshot_path = str(native_rows[0].get("remote_path") or "").strip()
        native_snapshot_files_path = str(
            native_rows[0].get("remote_files_path")
            or f"{native_snapshot_path}.FILES"
        ).strip()
        for label, value in (
            ("snapshot", native_snapshot_path),
            ("snapshot files", native_snapshot_files_path),
        ):
            relative = Path(value)
            if not value or relative.is_absolute() or ".." in relative.parts:
                reasons.append(f"saved replay native {label} path is unsafe or missing")

    return {
        "status": "ready" if not reasons else "fail",
        "state": state,
        "checkpoint_manifest": manifest,
        "checkpoint_manifest_path": str(manifest_path) if manifest_path else None,
        "remote_workdir": remote_workdir or None,
        "simulator_path": simulator_path or None,
        "native_snapshot_path": native_snapshot_path or None,
        "native_snapshot_files_path": native_snapshot_files_path or None,
        "reasons": reasons,
    }


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _restore_execution_id(report: dict[str, Any]) -> str:
    """Return one stable ID for one native restore execution report."""

    epoch = report.get("observation_epoch", {})
    epoch = epoch if isinstance(epoch, dict) else {}
    live_progress = report.get("live_progress", {})
    live_progress = live_progress if isinstance(live_progress, dict) else {}
    latest = live_progress.get("latest", {})
    latest = latest if isinstance(latest, dict) else {}
    if not epoch and isinstance(latest.get("observation_epoch"), dict):
        epoch = latest["observation_epoch"]
    projection = {
        "input_fingerprint_sha256": report.get("input_fingerprint_sha256"),
        "remote_workdir": report.get("remote_workdir"),
        "observation_epoch": epoch,
        "simulation_log": report.get("simulation_log"),
        "run": report.get("run"),
        "status": report.get("status"),
    }
    return hashlib.sha256(
        json.dumps(
            projection,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def update_fast_replay_state(
    run_dir: Path,
    runner_report: dict[str, Any] | None,
) -> dict[str, Any]:
    """Record one capture/restore result for one model and workload identity.

    This state is execution metadata only.  It never decides whether the
    hardware run passed and it never becomes LLM evidence.  A failed attempt
    remains actionable: the next Layer-3 run must repair or recapture it.
    """

    path = fast_replay_state_path(run_dir)
    previous = read_fast_replay_state(run_dir)
    report = runner_report if isinstance(runner_report, dict) else {}
    execution = report.get("checkpoint_execution", {})
    execution = execution if isinstance(execution, dict) else {}
    artifacts = report.get("checkpoint_artifacts", {})
    artifacts = artifacts if isinstance(artifacts, dict) else {}
    identity = report.get("simulation_execution_identity", {})
    identity = identity if isinstance(identity, dict) else {}
    compiled = str(identity.get("compiled_model_sha256") or "")
    workload = str(identity.get("workload_sha256") or "")
    if not compiled or not workload:
        return previous
    mode = str(execution.get("mode") or artifacts.get("mode") or "")
    if mode not in {"cold_capture", "native_exact_model"}:
        return previous
    current_identity = {
        "compiled_model_sha256": compiled,
        "workload_sha256": workload,
        "cut": STABLE_CHECKPOINT_CUT,
    }
    previous_identity = previous.get("identity", {})
    previous_identity = (
        previous_identity if isinstance(previous_identity, dict) else {}
    )
    same_identity = previous_identity == current_identity
    state: dict[str, Any] = {
        "schema_version": FAST_REPLAY_SCHEMA_VERSION,
        "identity": current_identity,
        # A snapshot belongs to exactly one compiled-model/workload pair.
        # Counters from an older pair are history only and must not make the
        # first capture or restore of a new pair look like a recapture.
        "capture_attempts": int(previous.get("capture_attempts") or 0)
        if same_identity
        else 0,
        "restore_attempts": int(previous.get("restore_attempts") or 0)
        if same_identity
        else 0,
        "reuse_count": int(previous.get("reuse_count") or 0)
        if same_identity
        else 0,
        "counted_restore_execution_ids": list(
            previous.get("counted_restore_execution_ids", [])
            if isinstance(previous.get("counted_restore_execution_ids"), list)
            and same_identity
            else []
        ),
        "manifest": artifacts.get("manifest") or (
            previous.get("manifest") if same_identity else None
        ),
        "checkpoint_id": artifacts.get("checkpoint_id") or (
            previous.get("checkpoint_id") if same_identity else None
        ),
        "checkpoint_manifest": artifacts.get("manifest") or (
            previous.get("checkpoint_manifest") if same_identity else None
        ),
        "remote_workdir": report.get("remote_workdir") or (
            previous.get("remote_workdir") if same_identity else None
        ),
        "simulator_path": report.get("simulator_path") or (
            previous.get("simulator_path") if same_identity else None
        ),
    }
    artifact_status = artifacts.get("status")
    remote_ack = artifacts.get("remote_acknowledgment_status")
    manifest_path = Path(str(state.get("checkpoint_manifest") or ""))
    if manifest_path and not manifest_path.is_absolute():
        manifest_path = (Path(run_dir) / manifest_path).resolve()
    manifest = _read_json_file(manifest_path) if manifest_path.is_file() else {}
    if manifest_path.is_file():
        state["checkpoint_manifest"] = str(manifest_path)
        state["manifest"] = str(manifest_path)
        state["checkpoint_id"] = manifest.get("checkpoint_id") or state.get("checkpoint_id")
        state["remote_workdir"] = manifest.get("remote_workdir") or state.get("remote_workdir")

    request_value = str(execution.get("request_path") or "").strip()
    request_path = Path(request_value).expanduser() if request_value else Path()
    request = _read_json_file(request_path) if request_path.is_file() else {}
    request_identity = request.get("execution_identity", {})
    request_identity = request_identity if isinstance(request_identity, dict) else {}
    request_ready = bool(
        request
        and request_identity.get("compiled_model_sha256") == compiled
        and request_identity.get("workload_sha256") == workload
    )
    capture_ready = bool(
        artifact_status == "pass"
        and remote_ack == "pass"
        and manifest.get("remote_acknowledgment_status") == "pass"
        and request_ready
    )
    restore_confirmed = bool(
        artifacts.get("native_restore_marker_seen") is True
    )
    restore_ready = bool(
        mode == "native_exact_model"
        and (artifact_status == "pass" or restore_confirmed)
        and (
            restore_confirmed
            or
            previous.get("status") in {"captured", "ready"}
            or (
                previous.get("status") == "repair_required"
                and int(previous.get("restore_attempts") or 0) == 0
            )
        )
    )
    if mode == "cold_capture" and capture_ready:
        _atomic_write_json(fast_replay_request_path(run_dir), request)
        state["capture_attempts"] = max(1, state["capture_attempts"])
        # A successful capture is a new snapshot.  Restore attempts recorded
        # for an older snapshot must not make this one look already consumed.
        state["restore_attempts"] = 0
        state["verified"] = False
        state["status"] = "captured"
        state["next_action"] = "restore_once_and_check"
        state["reason"] = (
            "checkpoint capture and remote persistence passed; one restore "
            "confirmation is required before reuse"
        )
        state["last_replay"] = {
            "mode": mode,
            "status": artifact_status,
            "hardware_run_status": report.get("status"),
        }
    elif restore_ready:
        state["capture_attempts"] = max(1, state["capture_attempts"])
        state["verified"] = True
        # The runner and its outer controller can both observe the same report.
        # Keep this transition idempotent instead of counting that report twice.
        state["restore_attempts"] = max(1, state["restore_attempts"])
        state["status"] = "ready"
        state["next_action"] = "restore_and_run"
        restore_execution_id = _restore_execution_id(report)
        counted_restore_execution_ids = [
            str(value)
            for value in state.get("counted_restore_execution_ids", [])
            if str(value)
        ]
        if restore_execution_id not in counted_restore_execution_ids:
            counted_restore_execution_ids.append(restore_execution_id)
            state["reuse_count"] = int(state.get("reuse_count") or 0) + 1
        state["counted_restore_execution_ids"] = counted_restore_execution_ids
        state["last_restore_execution_id"] = restore_execution_id
        state["reason"] = (
            "checkpoint restore confirmation passed"
            if previous.get("status") == "captured"
            else "reused previously confirmed checkpoint"
        )
        state["reuse_policy"] = (
            "permanent_for_compiled_model_and_workload"
        )
        state["last_replay"] = {
            "mode": mode,
            "status": artifact_status,
            "hardware_run_status": report.get("status"),
            "restore_confirmed": restore_confirmed,
        }
    elif mode == "native_exact_model" and artifact_status != "pass":
        state["capture_attempts"] = max(1, state["capture_attempts"])
        state["restore_attempts"] = max(
            1, int(previous.get("restore_attempts") or 0)
        )
        state["verified"] = False
        state["status"] = "repair_required"
        state["reason"] = (
            "current checkpoint attempt failed; checkpoint repair or recapture "
            "is required before the next Layer-3 run"
        )
        state["next_action"] = "repair_or_recapture"
        state["failure_class"] = artifacts.get("failure_class")
        state["errors"] = [
            str(value) for value in artifacts.get("errors", []) if str(value)
        ]
    elif mode == "cold_capture":
        state["capture_attempts"] = max(1, state["capture_attempts"])
        state["verified"] = False
        state["status"] = "repair_required"
        state["reason"] = (
            "cold capture completed without a confirmed restore and remote-persisted checkpoint"
        )
        state["next_action"] = "repair_or_recapture"
        state["failure_class"] = artifacts.get("failure_class")
        state["errors"] = [
            str(value) for value in artifacts.get("errors", []) if str(value)
        ]
        if not request_ready:
            state["errors"].append(
                "current capture request is missing or does not match the current model and workload"
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(path, state)
    binding = "@".join(
        str(current_identity.get(field) or "")
        for field in ("compiled_model_sha256", "workload_sha256")
    )
    if binding != "@":
        payload = {
            key: state.get(key)
            for key in (
                "status",
                "verified",
                "capture_attempts",
                "restore_attempts",
                "reuse_count",
                "next_action",
                "reason",
                "checkpoint_id",
                "remote_workdir",
                "simulator_path",
                "failure_class",
                "errors",
            )
            if state.get(key) is not None
        }
        try:
            existing = read_live_state(run_dir).get("execution", {})
            if existing.get("binding") == binding:
                update_live_state_slot(
                    run_dir,
                    "execution",
                    payload,
                    binding=binding,
                )
            else:
                activate_live_state_slot(
                    run_dir,
                    "execution",
                    payload,
                    binding=binding,
                )
        except OSError:
            # Replay correctness is determined by its own durable state file.
            # Live status is observability only and must not stop Layer 3.
            pass
    return state
