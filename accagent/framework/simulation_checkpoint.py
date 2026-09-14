"""Content-addressed checkpoint planning for long-running RTL simulations.

The framework treats a simulator checkpoint as evidence, not as an implicit
permission to skip verification.  Native snapshots are reusable only by the
exact compiled model.  Cross-revision replay additionally requires a portable
state capsule, a compatible state schema, a CCTG cut that precedes the changed
causal cone, and a same-source cold/replay equivalence certificate.
"""

from __future__ import annotations

import copy
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import time
from itertools import zip_longest
from pathlib import Path
from typing import Any, Iterator

from accagent.framework.board_acceptance_contract import canonical_contract_sha256
CHECKPOINT_CONTRACT_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_contract.v1"
)
CHECKPOINT_REQUEST_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_request.v1"
)
CHECKPOINT_MANIFEST_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_manifest.v1"
)
CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_replay_decision.v1"
)
CHECKPOINT_EQUIVALENCE_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_equivalence.v1"
)
CHECKPOINT_SUFFIX_EVIDENCE_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_suffix_evidence.v1"
)
CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_suffix_record_diff.v1"
)
CHECKPOINT_LIVE_STATE_WITNESS_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_live_state_witness.v1"
)
CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_capture_report.v1"
)
CHECKPOINT_RESTORE_REPORT_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_restore_report.v1"
)
CHECKPOINT_CUT_REACHABILITY_SCHEMA_VERSION = (
    "spatialaccagent.checkpoint_cut_reachability.v1"
)
CHECKPOINT_DEBUG_EPISODE_SCHEMA_VERSION = (
    "spatialaccagent.simulation_checkpoint_debug_episode.v1"
)
HEAVY_JOB_RESOURCE_SCHEMA_VERSION = "spatialaccagent.heavy_job_resource.v1"

DEFAULT_MAX_CHECKPOINT_COUNT = 3
DEFAULT_MAX_CHECKPOINT_BYTES = 8 * 1024**3
DEFAULT_MIN_AVAILABLE_MEMORY_BYTES = 4 * 1024**3
DEFAULT_DEBUG_EPISODE_MIN_REPRODUCTION_SEC = 600.0
DEFAULT_DEBUG_EPISODE_MIN_UNRESOLVED_ITERATIONS = 2

SEMANTIC_CUT_PHASE_SUFFIXES = (
    "_complete",
    "_commit",
    "_switch",
    "_start",
)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_root(run_dir: Path) -> Path:
    return run_dir / "verification" / "simulation_checkpoints"


def checkpoint_debug_episode_path(run_dir: Path) -> Path:
    return checkpoint_root(run_dir) / "episodes" / "current.json"


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def checkpoint_debug_episode_projection(
    episode: dict[str, Any] | None,
) -> dict[str, Any]:
    value = episode if isinstance(episode, dict) else {}
    return {
        key: value.get(key)
        for key in (
            "schema_version",
            "status",
            "episode_id",
            "workload_sha256",
            "state_schema_contract_sha256",
            "initial_failure_class",
            "initial_frontier_id",
            "current_frontier_id",
            "opened_at_unix_sec",
            "admission_thresholds",
            "policy",
        )
    }


def _update_debug_episode_frontier(
    episode: dict[str, Any],
    observation: dict[str, Any],
    *,
    observed_at_unix_sec: float,
) -> None:
    """Keep the latest proven frontier without erasing it on incomplete evidence."""

    frontier_id = str(observation.get("frontier_id") or "").strip()
    if not frontier_id:
        return
    episode["current_frontier_id"] = frontier_id
    history = episode.get("frontier_history")
    if not isinstance(history, list):
        history = []
    if not history or history[-1].get("frontier_id") != frontier_id:
        causal_evidence = observation.get("causal_evidence", {})
        causal_evidence = (
            causal_evidence if isinstance(causal_evidence, dict) else {}
        )
        history.append(
            {
                "frontier_id": frontier_id,
                "observed_at_unix_sec": observed_at_unix_sec,
                "failure_class": observation.get("failure_class"),
                "causal_evidence": {
                    "path": causal_evidence.get("path"),
                    "sha256": causal_evidence.get("sha256"),
                },
            }
        )
    episode["frontier_history"] = history


def _bound_iteration_snapshot(
    record_path: Path,
    record: dict[str, Any],
    *,
    marker: str,
) -> dict[str, Any]:
    rows = record.get("evidence_snapshots", [])
    if not isinstance(rows, list):
        return {}
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and marker in Path(str(row.get("snapshot_path") or "")).name
    ]
    if len(matches) != 1:
        return {}
    row = matches[0]
    path = Path(str(row.get("snapshot_path") or "")).resolve()
    expected_sha256 = str(row.get("source_sha256") or "")
    if (
        not path.is_file()
        or not path.is_relative_to(record_path.parent.resolve())
        or not expected_sha256
        or sha256_file(path) != expected_sha256
    ):
        return {}
    return read_json(path)


def _consecutive_unresolved_frontier_iterations(
    run_dir: Path,
    frontier_id: str,
    *,
    required_count: int,
) -> tuple[int, list[dict[str, Any]]]:
    count = 0
    evidence: list[dict[str, Any]] = []
    loop_dir = run_dir / "repair_execution" / "loop"
    for record_path in sorted(
        loop_dir.glob("iteration_*/iteration_record.json"),
        reverse=True,
    ):
        record = read_json(record_path)
        if (
            record.get("schema_version")
            != "spatialaccagent.stage8_repair_loop_iteration.v1"
            or record.get("repair_execution_report", {}).get("status")
            not in {"incomplete", "fail"}
        ):
            break
        causal = _bound_iteration_snapshot(
            record_path,
            record,
            marker="sacg_cctg_causal_slice",
        )
        diagnosis = _bound_iteration_snapshot(
            record_path,
            record,
            marker="vcs_functional_diagnosis",
        )
        frontier = (
            causal.get("earliest_unproven_frontier", {})
            if isinstance(causal.get("earliest_unproven_frontier"), dict)
            else {}
        )
        if (
            diagnosis.get("status") != "needs_repair"
            or frontier.get("status") != "earliest_unproven"
            or str(frontier.get("frontier_id") or "") != frontier_id
        ):
            break
        count += 1
        evidence.append(
            {
                "iteration": record.get("iteration"),
                "record_path": str(record_path),
                "record_sha256": sha256_file(record_path),
                "failure_class": diagnosis.get("failure_class"),
                "frontier_id": frontier_id,
            }
        )
        if count >= max(1, required_count):
            break
    return count, evidence


def checkpoint_debug_episode_observation(run_dir: Path) -> dict[str, Any]:
    board_manifest_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "board_simulation_manifest.json"
    )
    executed_manifest_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "board_simulation_executed_manifest.json"
    )
    runner_path = (
        run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
    )
    diagnosis_path = (
        run_dir
        / "verification"
        / "case_diagnostics"
        / "vcs_functional_diagnosis.json"
    )
    causal_path = (
        run_dir
        / "verification"
        / "case_diagnostics"
        / "sacg_cctg_causal_slice.json"
    )
    board_manifest = read_json(board_manifest_path)
    executed_manifest = read_json(executed_manifest_path)
    runner = read_json(runner_path)
    diagnosis = read_json(diagnosis_path)
    causal = read_json(causal_path)
    identity = simulation_execution_identity(board_manifest)
    observed_identity = simulation_execution_identity(executed_manifest)
    frontier = (
        causal.get("earliest_unproven_frontier", {})
        if isinstance(causal.get("earliest_unproven_frontier"), dict)
        else {}
    )
    frontier_id = str(frontier.get("frontier_id") or "")
    minimum_duration = float(
        os.environ.get(
            "SPATIALACC_CHECKPOINT_EPISODE_MIN_REPRODUCTION_SEC",
            str(DEFAULT_DEBUG_EPISODE_MIN_REPRODUCTION_SEC),
        )
    )
    minimum_iterations = max(
        1,
        int(
            os.environ.get(
                "SPATIALACC_CHECKPOINT_EPISODE_MIN_UNRESOLVED_ITERATIONS",
                str(DEFAULT_DEBUG_EPISODE_MIN_UNRESOLVED_ITERATIONS),
            )
        ),
    )
    duration = runner.get("run", {}).get("duration_sec")
    duration = float(duration) if isinstance(duration, (int, float)) else None
    unresolved_count, iteration_evidence = (
        _consecutive_unresolved_frontier_iterations(
            run_dir,
            frontier_id,
            required_count=minimum_iterations,
        )
        if frontier_id
        else (0, [])
    )
    current_failure_class = (
        frontier.get("failure_class") or diagnosis.get("failure_class")
    )
    episode_failure_class = current_failure_class
    if (
        current_failure_class
        == "simulation_checkpoint_capability_missing_or_invalid"
        and iteration_evidence
        and iteration_evidence[0].get("failure_class")
    ):
        episode_failure_class = iteration_evidence[0]["failure_class"]
    blockers: list[str] = []
    if runner.get("phase") != "remote_vcs":
        blockers.append("latest evidence is not a real remote VCS execution")
    if runner.get("status") in {"pass", "candidate_pass"}:
        blockers.append("latest exact-board execution does not reproduce a failure")
    if runner.get("checkpoint_execution", {}).get("candidate_screening") is True:
        blockers.append("checkpoint replay screening cannot admit a new checkpoint episode")
    if diagnosis.get("status") != "needs_repair":
        blockers.append("latest independent diagnosis does not require repair")
    if frontier.get("status") != "earliest_unproven" or not frontier_id:
        blockers.append("latest SACG/CCTG evidence has no earliest unproven frontier")
    if duration is None or duration < minimum_duration:
        blockers.append(
            "real failure reproduction duration is below the checkpoint episode threshold"
        )
    if unresolved_count < minimum_iterations:
        blockers.append(
            "the same SACG/CCTG frontier has not remained unresolved for enough iterations"
        )
    if not identity.get("workload_sha256"):
        blockers.append("current exact-board workload identity is unavailable")
    if (
        observed_identity.get("workload_sha256")
        != identity.get("workload_sha256")
    ):
        blockers.append("latest executed workload differs from the current board workload")
    return {
        "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode_observation.v1",
        "status": "admit" if not blockers else "not_admitted",
        "workload_sha256": identity.get("workload_sha256"),
        "state_schema_contract_sha256": identity.get(
            "state_schema_contract_sha256"
        ),
        "failure_class": episode_failure_class,
        "current_failure_class": current_failure_class,
        "frontier_id": frontier_id or None,
        "reproduction_duration_sec": duration,
        "full_cold_stage_pass": bool(
            runner.get("status") == "pass"
            and runner.get("stage_pass_eligible") is True
            and runner.get("checkpoint_execution", {}).get(
                "candidate_screening"
            )
            is not True
        ),
        "consecutive_unresolved_iteration_count": unresolved_count,
        "iteration_evidence": iteration_evidence,
        "runner_evidence": {
            "path": str(runner_path),
            "sha256": sha256_file(runner_path) if runner_path.is_file() else None,
            "input_fingerprint_sha256": runner.get("input_fingerprint_sha256"),
        },
        "diagnosis_evidence": {
            "path": str(diagnosis_path),
            "sha256": (
                sha256_file(diagnosis_path) if diagnosis_path.is_file() else None
            ),
        },
        "causal_evidence": {
            "path": str(causal_path),
            "sha256": sha256_file(causal_path) if causal_path.is_file() else None,
        },
        "admission_thresholds": {
            "minimum_reproduction_duration_sec": minimum_duration,
            "minimum_consecutive_unresolved_iterations": minimum_iterations,
            "both_thresholds_are_required": True,
        },
        "blockers": blockers,
    }


def _set_episode_manifests_inactive(
    run_dir: Path,
    episode_id: str,
) -> list[str]:
    changed: list[str] = []
    for path, manifest in checkpoint_manifests(run_dir):
        manifest_episode = (
            manifest.get("debug_episode", {})
            if isinstance(manifest.get("debug_episode"), dict)
            else {}
        )
        if (
            manifest.get("debug_episode_id") != episode_id
            and not (
                manifest.get("active") is True
                and manifest_episode.get("episode_id") == episode_id
            )
        ):
            continue
        if manifest.get("active") is not False:
            manifest["active"] = False
            write_json(path, manifest)
            changed.append(str(path))
    return changed


def prepare_checkpoint_debug_episode(run_dir: Path) -> dict[str, Any]:
    """Open one checkpoint episode only for a long, repeatedly reproduced bug."""

    path = checkpoint_debug_episode_path(run_dir)
    current = read_json(path)
    observation = checkpoint_debug_episode_observation(run_dir)
    if (
        current.get("schema_version") == CHECKPOINT_DEBUG_EPISODE_SCHEMA_VERSION
        and current.get("status") == "active"
    ):
        if observation.get("full_cold_stage_pass") is True:
            close_checkpoint_debug_episode(
                run_dir,
                reason=(
                    "recovered full cold exact-board VCS pass after an "
                    "interrupted episode-close transition"
                ),
            )
            return read_json(path)
        compatible = (
            current.get("workload_sha256") == observation.get("workload_sha256")
            and current.get("state_schema_contract_sha256")
            == observation.get("state_schema_contract_sha256")
        )
        if compatible:
            observed_at = time.time()
            current["last_observed_at_unix_sec"] = observed_at
            current["latest_observation"] = observation
            _update_debug_episode_frontier(
                current,
                observation,
                observed_at_unix_sec=observed_at,
            )
            _atomic_write_json(path, current)
            return current
        episode_id = str(current.get("episode_id") or "")
        current["status"] = "invalidated"
        current["closed_at_unix_sec"] = time.time()
        current["close_reason"] = (
            "workload or runtime state-schema contract changed"
        )
        current["deactivated_checkpoint_manifests"] = (
            _set_episode_manifests_inactive(run_dir, episode_id)
            if episode_id
            else []
        )
        history_path = (
            path.parent / "history" / f"{episode_id or 'unknown'}.json"
        )
        _atomic_write_json(history_path, current)
        _atomic_write_json(path, current)

    if observation.get("status") != "admit":
        return {
            "schema_version": CHECKPOINT_DEBUG_EPISODE_SCHEMA_VERSION,
            "status": "not_admitted",
            "checkpoint_required": False,
            "observation": observation,
            "policy": {
                "ordinary_exact_board_validation_runs_without_checkpoint": True,
                "long_duration_and_repeated_unresolved_failure_both_required": True,
                "checkpoint_is_not_refreshed_each_repair_iteration": True,
            },
        }

    opened = time.time()
    projection = {
        "workload_sha256": observation.get("workload_sha256"),
        "state_schema_contract_sha256": observation.get(
            "state_schema_contract_sha256"
        ),
        "initial_failure_class": observation.get("failure_class"),
        "initial_frontier_id": observation.get("frontier_id"),
        "opening_runner_sha256": observation.get("runner_evidence", {}).get(
            "sha256"
        ),
        "opened_at_unix_sec": opened,
    }
    episode = {
        "schema_version": CHECKPOINT_DEBUG_EPISODE_SCHEMA_VERSION,
        "status": "active",
        "checkpoint_required": True,
        "episode_id": canonical_contract_sha256(projection),
        **projection,
        "admission_thresholds": observation.get("admission_thresholds", {}),
        "opening_observation": observation,
        "latest_observation": observation,
        "checkpoint": {
            "status": "pending_same_source_certification",
            "checkpoint_id": None,
            "manifest": None,
        },
        "policy": {
            "one_checkpoint_episode_per_long_unresolved_bug": True,
            "reuse_certified_checkpoint_until_bug_is_fixed": True,
            "do_not_refresh_checkpoint_each_repair_iteration": True,
            "replace_only_after_workload_schema_or_causal_eligibility_invalidation": True,
            "adaptive_probe_frontier_may_move_within_the_same_episode": True,
            "final_stage_acceptance_requires_full_cold_exact_board_vcs": True,
            "close_and_prune_after_full_cold_bug_resolution": True,
        },
    }
    _update_debug_episode_frontier(
        episode,
        observation,
        observed_at_unix_sec=opened,
    )
    _atomic_write_json(path, episode)
    return episode


def activate_checkpoint_for_debug_episode(
    run_dir: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    episode_path = checkpoint_debug_episode_path(run_dir)
    episode = read_json(episode_path)
    manifest_path = manifest_path.resolve()
    root = checkpoint_root(run_dir).resolve()
    manifest = read_json(manifest_path)
    blockers: list[str] = []
    if (
        episode.get("schema_version") != CHECKPOINT_DEBUG_EPISODE_SCHEMA_VERSION
        or episode.get("status") != "active"
    ):
        blockers.append("no active long-bug checkpoint episode exists")
    if (
        not manifest_path.is_file()
        or not manifest_path.is_relative_to(root)
        or manifest_path.name != "manifest.json"
    ):
        blockers.append("checkpoint manifest is outside the current checkpoint store")
    manifest_episode = (
        manifest.get("debug_episode", {})
        if isinstance(manifest.get("debug_episode"), dict)
        else {}
    )
    manifest_episode_id = str(
        manifest.get("debug_episode_id")
        or manifest_episode.get("episode_id")
        or ""
    )
    episode_id = str(episode.get("episode_id") or "")
    if not manifest_episode_id or manifest_episode_id != episode_id:
        blockers.append("checkpoint manifest is not bound to the active debug episode")
    if (
        manifest_episode.get("initial_frontier_id")
        != episode.get("initial_frontier_id")
    ):
        blockers.append("checkpoint manifest initial frontier differs from the active episode")
    manifest_cut = (
        manifest.get("semantic_cut", {})
        if isinstance(manifest.get("semantic_cut"), dict)
        else {}
    )
    manifest_frontier_id = str(manifest_cut.get("frontier_id") or "").strip()
    allowed_frontiers = checkpoint_debug_episode_frontier_ids(episode)
    if not manifest_frontier_id:
        blockers.append("checkpoint manifest semantic cut has no causal frontier")
    elif manifest_frontier_id not in allowed_frontiers:
        blockers.append(
            "checkpoint manifest semantic cut frontier is outside the active episode history"
        )
    if manifest.get("remote_acknowledgment_status") != "pass":
        blockers.append("checkpoint remote persistence is not acknowledged")
    if manifest.get("portable_state_capsule", {}).get("status") != "pass":
        blockers.append("checkpoint portable state capsule is not certified")
    if manifest.get("causal_cut_certificate", {}).get("status") != "pass":
        blockers.append("checkpoint causal cut is not certified")
    if not _equivalence_valid(manifest):
        blockers.append("checkpoint same-source equivalence is not certified")
    if blockers:
        return {
            "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode_activation.v1",
            "status": "fail",
            "blockers": blockers,
        }
    episode_id = str(episode["episode_id"])
    deactivated = []
    for path, candidate in checkpoint_manifests(run_dir):
        if path.resolve() == manifest_path:
            continue
        if candidate.get("active") is True:
            candidate["active"] = False
            write_json(path, candidate)
            deactivated.append(str(path))
    if (
        manifest.get("active") is not True
        or manifest.get("debug_episode_id") != episode_id
    ):
        manifest["active"] = True
        manifest["debug_episode_id"] = episode_id
        manifest["debug_episode"] = checkpoint_debug_episode_projection(episode)
        write_json(manifest_path, manifest)
    episode["checkpoint"] = {
        "status": "certified_active",
        "checkpoint_id": manifest.get("checkpoint_id"),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
    }
    episode["last_observed_at_unix_sec"] = time.time()
    _atomic_write_json(episode_path, episode)
    return {
        "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode_activation.v1",
        "status": "pass",
        "episode_id": episode_id,
        "checkpoint_id": manifest.get("checkpoint_id"),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "deactivated_manifests": deactivated,
    }


def invalidate_debug_episode_checkpoint(
    run_dir: Path,
    blockers: list[str],
) -> dict[str, Any]:
    path = checkpoint_debug_episode_path(run_dir)
    episode = read_json(path)
    if episode.get("status") != "active":
        return {"status": "not_active", "blockers": []}
    checkpoint = (
        episode.get("checkpoint", {})
        if isinstance(episode.get("checkpoint"), dict)
        else {}
    )
    manifest_path = Path(str(checkpoint.get("manifest") or ""))
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        manifest["active"] = False
        write_json(manifest_path, manifest)
    episode["checkpoint"] = {
        **checkpoint,
        "status": "invalidated",
        "invalidated_at_unix_sec": time.time(),
        "invalidation_blockers": [str(value) for value in blockers if str(value)],
    }
    _atomic_write_json(path, episode)
    return {"status": "pass", "checkpoint": episode["checkpoint"]}


def close_checkpoint_debug_episode(
    run_dir: Path,
    *,
    reason: str,
) -> dict[str, Any]:
    path = checkpoint_debug_episode_path(run_dir)
    episode = read_json(path)
    if episode.get("status") != "active":
        return {
            "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode_close.v1",
            "status": "not_active",
            "reason": reason,
        }
    episode_id = str(episode.get("episode_id") or "")
    deactivated = _set_episode_manifests_inactive(run_dir, episode_id)
    episode["status"] = "closed"
    episode["closed_at_unix_sec"] = time.time()
    episode["close_reason"] = reason
    episode["deactivated_checkpoint_manifests"] = deactivated
    history_path = path.parent / "history" / f"{episode_id}.json"
    _atomic_write_json(history_path, episode)
    _atomic_write_json(path, episode)
    retention = checkpoint_retention_plan(
        checkpoint_manifests(run_dir),
        max_count=int(
            os.environ.get(
                "SPATIALACC_CHECKPOINT_KEEP_COUNT",
                str(DEFAULT_MAX_CHECKPOINT_COUNT),
            )
        ),
        max_bytes=int(
            os.environ.get(
                "SPATIALACC_CHECKPOINT_MAX_BYTES",
                str(DEFAULT_MAX_CHECKPOINT_BYTES),
            )
        ),
    )
    retention_execution = apply_checkpoint_retention_plan(run_dir, retention)
    return {
        "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode_close.v1",
        "status": (
            "pass" if retention_execution.get("status") == "pass" else "fail"
        ),
        "episode_id": episode_id,
        "reason": reason,
        "history_path": str(history_path),
        "retention_plan": retention,
        "retention_execution": retention_execution,
    }


def checkpoint_contract(board_manifest: dict[str, Any]) -> dict[str, Any]:
    testbench = (
        board_manifest.get("testbench", {})
        if isinstance(board_manifest.get("testbench"), dict)
        else {}
    )
    value = testbench.get("simulation_checkpoint_contract", {})
    return value if isinstance(value, dict) else {}


def checkpoint_contract_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != CHECKPOINT_CONTRACT_SCHEMA_VERSION:
        errors.append("simulation checkpoint contract schema_version is invalid")
    if contract.get("status") not in {"ready", "pass"}:
        errors.append("simulation checkpoint contract status is not ready/pass")
    required = {
        "simulation_only": True,
        "drives_dut_signals": False,
        "captures_complete_simulator_state": True,
        "captures_testbench_and_external_model_state": True,
        "flushes_evidence_before_capture": True,
        "native_reuse_requires_exact_compiled_model": True,
        "cross_revision_reuse_requires_state_schema_match": True,
        "cross_revision_reuse_requires_causal_cut_certificate": True,
        "cross_revision_reuse_requires_equivalence_certificate": True,
        "full_cold_run_required_before_stage_pass": True,
    }
    for field, expected in required.items():
        if contract.get(field) is not expected:
            errors.append(
                f"simulation checkpoint contract {field} must be "
                f"{str(expected).lower()}"
            )
    if contract.get("synthesis_impact") != "none":
        errors.append("simulation checkpoint contract synthesis_impact is not none")
    modes = {str(value) for value in contract.get("supported_modes", [])}
    if "native_exact_model" not in modes or "cold_capture" not in modes:
        errors.append(
            "simulation checkpoint contract must support native_exact_model and cold_capture"
        )
    portable = contract.get("portable_state_capsule", {})
    if "portable_cross_revision" in modes:
        if not isinstance(portable, dict) or portable.get("status") not in {
            "ready",
            "pass",
        }:
            errors.append(
                "portable_cross_revision mode lacks a ready portable_state_capsule contract"
            )
        elif portable.get("quiescent_cut_required") is not True:
            errors.append("portable state capsule must require a quiescent cut")
        if portable.get("restore_requires_runtime_schema_recheck") is not True:
            errors.append(
                "portable state capsule must recheck the elaborated state schema before restore"
            )
        state_schema = portable.get("state_schema", {})
        if not isinstance(state_schema, dict) or not state_schema:
            errors.append("portable state capsule has no state_schema contract")
        if portable.get("state_adapter") != "framework_vpi_state_capsule_v1":
            errors.append(
                "portable state capsule does not use the framework VPI state adapter"
            )
        if not str(portable.get("dut_state_root") or "").strip():
            errors.append("portable state capsule has no current DUT state root")
        external = portable.get("testbench_external_state", {})
        if not isinstance(external, dict) or external.get("status") != "ready":
            errors.append("portable state capsule external testbench state is not ready")
        else:
            for field in (
                "captures_axi_ddr_model_state",
                "captures_pending_transactions_and_responses",
                "captures_queues_and_associative_arrays",
                "captures_rng_state",
                "captures_and_reopens_file_offsets",
            ):
                if external.get(field) is not True:
                    errors.append(
                        f"portable external state contract {field} must be true"
                    )
        adapter_artifacts = portable.get("framework_adapter_artifacts", [])
        if not isinstance(adapter_artifacts, list) or len(adapter_artifacts) != 2:
            errors.append(
                "portable state capsule must bind the framework VPI source and table"
            )
    outputs = contract.get("outputs", {})
    for name in (
        "manifest",
        "capture_report",
        "restore_report",
        "equivalence_report",
    ):
        row = outputs.get(name, {}) if isinstance(outputs, dict) else {}
        path = str(row.get("path") or "") if isinstance(row, dict) else ""
        if not path or Path(path).is_absolute() or ".." in Path(path).parts:
            errors.append(f"simulation checkpoint output {name} path is unsafe or missing")
    return errors


def _artifact_projection(board_manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = board_manifest.get("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
    return {
        str(name): {
            key: row.get(key)
            for key in ("path", "sha256", "byte_count", "size")
            if row.get(key) is not None
        }
        for name, row in sorted(artifacts.items())
        if isinstance(row, dict)
    }


def simulation_execution_identity(
    board_manifest: dict[str, Any],
    *,
    runner_sha256: str | None = None,
) -> dict[str, Any]:
    source_rows = []
    declared_sources = board_manifest.get("source_files")
    if not isinstance(declared_sources, list):
        declared_sources = board_manifest.get("compile_source_files", [])
    for row in declared_sources:
        if not isinstance(row, dict):
            continue
        source_rows.append(
            {
                "source_id": row.get("source_id"),
                "sha256": row.get("sha256") or row.get("local_sha256"),
                "role": row.get("role"),
            }
        )
    source_rows.sort(key=lambda row: str(row.get("source_id") or ""))
    compiled_projection = {
        "top_module": board_manifest.get("top_module"),
        "validation_mode": board_manifest.get("validation_mode"),
        "source_closure_sha256": board_manifest.get("source_closure_sha256"),
        "compile_source_set_sha256": board_manifest.get(
            "compile_source_set_sha256"
        ),
        "vcs_compile_plan_sha256": board_manifest.get("vcs_compile_plan_sha256"),
        "source_rows": source_rows,
    }
    workload_projection = {
        "artifacts": _artifact_projection(board_manifest),
        "runtime_plusargs": (
            board_manifest.get("vcs", {}).get("runtime_plusargs", {})
            if isinstance(board_manifest.get("vcs"), dict)
            else {}
        ),
        "compute_slot_abi_sha256": board_manifest.get("compute_slot_abi_sha256"),
        "timing_contract_sha256": board_manifest.get("timing_contract_sha256"),
        "axi_interfaces_sha256": board_manifest.get("axi_interfaces_sha256"),
        "target_layer_count": board_manifest.get("target_layer_count"),
    }
    identity = {
        "schema_version": "spatialaccagent.simulation_execution_identity.v1",
        "compiled_model_sha256": canonical_contract_sha256(compiled_projection),
        "workload_sha256": canonical_contract_sha256(workload_projection),
        "compiled_model": compiled_projection,
        "workload": workload_projection,
        "runner_sha256": runner_sha256,
    }
    portable = checkpoint_contract(board_manifest).get("portable_state_capsule", {})
    if isinstance(portable, dict):
        if portable.get("state_schema_sha256"):
            identity["state_schema_sha256"] = portable["state_schema_sha256"]
        elif isinstance(portable.get("state_schema"), dict) and portable.get(
            "state_schema"
        ):
            identity["state_schema_contract_sha256"] = canonical_contract_sha256(
                portable["state_schema"]
            )
    identity["identity_sha256"] = canonical_contract_sha256(identity)
    return identity


def _frontier_observation(causal_slice: dict[str, Any]) -> dict[str, Any]:
    frontier = causal_slice.get("earliest_unproven_frontier", {})
    if not isinstance(frontier, dict):
        frontier = {}
    observed = frontier.get("observed", {})
    if not isinstance(observed, dict):
        observed = {}
    return {"frontier": frontier, "observed": observed}


def checkpoint_debug_episode_frontier_ids(
    episode: dict[str, Any] | None,
) -> set[str]:
    value = episode if isinstance(episode, dict) else {}
    frontier_ids = {
        str(value.get(field) or "").strip()
        for field in ("initial_frontier_id", "current_frontier_id")
    }
    history = value.get("frontier_history", [])
    if isinstance(history, list):
        frontier_ids.update(
            str(row.get("frontier_id") or "").strip()
            for row in history
            if isinstance(row, dict)
        )
    return {frontier_id for frontier_id in frontier_ids if frontier_id}


def checkpoint_debug_episode_frontier_binding(
    debug_episode: dict[str, Any] | None,
    causal_slice: dict[str, Any],
) -> dict[str, Any]:
    """Bind a new capture request to the active episode's latest proven frontier."""

    episode = debug_episode if isinstance(debug_episode, dict) else {}
    if episode.get("status") != "active":
        return {
            "schema_version": (
                "spatialaccagent.checkpoint_debug_episode_frontier_binding.v1"
            ),
            "status": "not_required",
            "blockers": [],
        }
    frontier = _frontier_observation(causal_slice)["frontier"]
    observed_frontier_id = str(frontier.get("frontier_id") or "").strip()
    expected_frontier_id = str(
        episode.get("current_frontier_id")
        or episode.get("initial_frontier_id")
        or ""
    ).strip()
    blockers: list[str] = []
    if not expected_frontier_id:
        blockers.append("active debug episode has no proven causal frontier")
    if frontier.get("status") != "earliest_unproven":
        blockers.append("current SACG/CCTG evidence has no earliest unproven frontier")
    if not observed_frontier_id:
        blockers.append("current SACG/CCTG frontier identity is absent")
    elif expected_frontier_id and observed_frontier_id != expected_frontier_id:
        blockers.append(
            "current SACG/CCTG frontier differs from the active debug episode frontier"
        )
    return {
        "schema_version": (
            "spatialaccagent.checkpoint_debug_episode_frontier_binding.v1"
        ),
        "status": "pass" if not blockers else "fail",
        "episode_id": episode.get("episode_id"),
        "expected_frontier_id": expected_frontier_id or None,
        "observed_frontier_id": observed_frontier_id or None,
        "observed_frontier_status": frontier.get("status"),
        "allowed_episode_frontier_ids": sorted(
            checkpoint_debug_episode_frontier_ids(episode)
        ),
        "blockers": blockers,
        "policy": {
            "missing_frontier_fails_closed": True,
            "frontier_must_be_refreshed_by_real_SACG_CCTG_evidence": True,
            "adaptive_frontier_moves_are_recorded_before_checkpoint_preparation": True,
            "never_synthesize_a_frontier_from_checkpoint_metadata": True,
        },
    }


def _frontier_upper_cycle(causal_slice: dict[str, Any]) -> int | None:
    projection = _frontier_observation(causal_slice)
    frontier = projection["frontier"]
    observed = projection["observed"]
    return next(
        (
            int(value)
            for value in (
                observed.get("last_frontier_cycle"),
                observed.get("first_output_frontier_cycle"),
                frontier.get("cycle"),
            )
            if isinstance(value, int) and not isinstance(value, bool)
        ),
        None,
    )


def _semantic_terms(value: Any) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if len(term) > 1
        and term
        not in {
            "boundary",
            "edge",
            "node",
            "pipeline",
            "stage",
            "trace",
            "complete",
            "commit",
            "start",
            "switch",
        }
    }


def _semantic_cut_relevance(
    record: dict[str, Any],
    causal_slice: dict[str, Any],
) -> tuple[int, list[str]]:
    frontier = _frontier_observation(causal_slice)["frontier"]
    graph = (
        causal_slice.get("causal_graph_slice", {})
        if isinstance(causal_slice.get("causal_graph_slice"), dict)
        else {}
    )
    focus_terms: set[str] = set()
    for value in (
        frontier.get("frontier_id"),
        frontier.get("frontier_type"),
        frontier.get("causal_domain"),
    ):
        focus_terms.update(_semantic_terms(value))
    for collection, fields in (
        (graph.get("sacg_nodes", []), ("id", "name", "type")),
        (graph.get("sacg_edges", []), ("id", "src", "dst", "type")),
        (
            graph.get("cctg_boundaries", []),
            ("boundary_id", "src_stage", "dst_stage"),
        ),
    ):
        for row in collection if isinstance(collection, list) else []:
            if not isinstance(row, dict):
                continue
            for field in fields:
                focus_terms.update(_semantic_terms(row.get(field)))
    record_terms = set()
    for field in ("phase", "stage_or_boundary", "event_kind"):
        record_terms.update(_semantic_terms(record.get(field)))
    matched = sorted(focus_terms.intersection(record_terms))
    return len(matched), matched


def read_checkpoint_cut_records(
    path: Path,
    causal_slice: dict[str, Any],
) -> dict[str, Any]:
    """Stream only the latest useful cut records from a potentially large JSONL."""

    if not path.is_file():
        return {
            "status": "missing",
            "path": str(path),
            "records": [],
            "committed_record_count": 0,
            "invalid_record_count": 0,
            "trailing_partial_byte_count": 0,
        }
    upper_cycle = _frontier_upper_cycle(causal_slice)
    latest_any: tuple[int, int, dict[str, Any]] | None = None
    latest_complete: tuple[int, int, dict[str, Any]] | None = None
    latest_quiescent: tuple[int, int, dict[str, Any]] | None = None
    latest_complete_quiescent: tuple[int, int, dict[str, Any]] | None = None
    committed_record_count = 0
    invalid_record_count = 0
    trailing_partial_byte_count = 0
    with path.open("rb") as stream:
        while True:
            line = stream.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                trailing_partial_byte_count = len(line)
                break
            if not line.strip():
                continue
            try:
                value = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                invalid_record_count += 1
                continue
            if not isinstance(value, dict):
                invalid_record_count += 1
                continue
            committed_record_count += 1
            cycle = value.get("cycle")
            phase = str(value.get("phase") or "")
            if (
                not isinstance(cycle, int)
                or isinstance(cycle, bool)
                or value.get("semantic_progress") is not True
                or value.get("event_kind")
                in {"terminal", "heartbeat", "stall_snapshot"}
                or (upper_cycle is not None and cycle > upper_cycle)
            ):
                continue
            relevance, _ = _semantic_cut_relevance(value, causal_slice)
            candidate = (relevance, cycle, value)
            if latest_any is None or candidate[:2] >= latest_any[:2]:
                latest_any = candidate
            if phase.endswith(SEMANTIC_CUT_PHASE_SUFFIXES) and (
                latest_complete is None or candidate[:2] >= latest_complete[:2]
            ):
                latest_complete = candidate
            quiescent, _ = _quiescent_external_state(value)
            if quiescent and (
                latest_quiescent is None
                or candidate[:2] >= latest_quiescent[:2]
            ):
                latest_quiescent = candidate
            if (
                quiescent
                and phase.endswith(SEMANTIC_CUT_PHASE_SUFFIXES)
                and (
                    latest_complete_quiescent is None
                    or candidate[:2] >= latest_complete_quiescent[:2]
                )
            ):
                latest_complete_quiescent = candidate
    selected = []
    for candidate in (
        latest_any,
        latest_complete,
        latest_quiescent,
        latest_complete_quiescent,
    ):
        value = candidate[2] if candidate is not None else None
        if value is not None and value not in selected:
            selected.append(value)
    return {
        "status": "ready",
        "path": str(path),
        "records": selected,
        "committed_record_count": committed_record_count,
        "selected_record_count": len(selected),
        "invalid_record_count": invalid_record_count,
        "trailing_partial_byte_count": trailing_partial_byte_count,
        "streaming_read": True,
        "constant_memory_candidate_classes": [
            "latest_any",
            "latest_complete",
            "latest_quiescent",
            "latest_complete_quiescent",
        ],
    }


def _quiescent_external_state(record: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    axi_read = record.get("axi_read", {})
    axi_write = record.get("axi_write", {})
    boundary = record.get("active_boundary_observation", {})
    if not isinstance(axi_read, dict):
        axi_read = {}
    if not isinstance(axi_write, dict):
        axi_write = {}
    if not isinstance(boundary, dict):
        boundary = {}

    explicit = {
        "read_outstanding": axi_read.get("outstanding"),
        "write_outstanding": axi_write.get("outstanding"),
        "pending_read_response": axi_read.get("pending_response"),
        "pending_write_response": axi_write.get("pending_response"),
        "event_queue_quiescent": boundary.get("event_queue_quiescent"),
    }
    for field in ("read_outstanding", "write_outstanding"):
        if explicit[field] != 0:
            reasons.append(f"{field} is not explicitly zero")
    for field in ("pending_read_response", "pending_write_response"):
        if explicit[field] not in {0, False}:
            reasons.append(f"{field} is not explicitly false")
    if explicit["event_queue_quiescent"] is not True:
        reasons.append("event_queue_quiescent is not explicitly true")
    return not reasons, reasons


def semantic_checkpoint_cut_sha256(cut: dict[str, Any]) -> str:
    return canonical_contract_sha256(
        {key: value for key, value in cut.items() if key != "cut_sha256"}
    )


def select_semantic_checkpoint_cut(
    records: list[dict[str, Any]],
    causal_slice: dict[str, Any],
) -> dict[str, Any]:
    frontier_projection = _frontier_observation(causal_slice)
    frontier = frontier_projection["frontier"]
    upper_cycle = _frontier_upper_cycle(causal_slice)
    candidates = []
    for record in records:
        if not isinstance(record, dict):
            continue
        cycle = record.get("cycle")
        phase = str(record.get("phase") or "")
        if (
            not isinstance(cycle, int)
            or isinstance(cycle, bool)
            or record.get("semantic_progress") is not True
            or record.get("event_kind") in {"terminal", "heartbeat", "stall_snapshot"}
            or (upper_cycle is not None and cycle > upper_cycle)
        ):
            continue
        complete = phase.endswith(SEMANTIC_CUT_PHASE_SUFFIXES)
        quiescent, reasons = _quiescent_external_state(record)
        relevance, matched_terms = _semantic_cut_relevance(record, causal_slice)
        candidates.append(
            (complete, relevance, quiescent, cycle, record, reasons, matched_terms)
        )

    if not candidates:
        return {
            "status": "unavailable",
            "summary": "no committed semantic event exists before the active CCTG frontier",
            "frontier_id": frontier.get("frontier_id"),
        }
    complete_candidates = [row for row in candidates if row[0]]
    complete_quiescent_candidates = [
        row for row in complete_candidates if row[2]
    ]
    quiescent_candidates = [row for row in candidates if row[2]]
    if complete_quiescent_candidates:
        pool = complete_quiescent_candidates
        selection_mode = "complete_quiescent_boundary"
    elif complete_candidates:
        pool = complete_candidates
        selection_mode = "complete_nonportable_boundary"
    elif quiescent_candidates:
        pool = quiescent_candidates
        selection_mode = "quiescent_noncompletion_boundary"
    else:
        pool = candidates
        selection_mode = "nonportable_fallback_boundary"
    _, relevance, quiescent, _, selected, reasons, matched_terms = max(
        pool,
        key=lambda row: (row[1], row[3]),
    )
    trigger = {
        key: selected.get(key)
        for key in (
            "sequence",
            "cycle",
            "phase",
            "event_kind",
            "layer",
            "token",
            "beat",
            "stage_or_boundary",
            "progress_epoch",
        )
    }
    projection = {
        "frontier_id": frontier.get("frontier_id"),
        "frontier_type": frontier.get("frontier_type"),
        "trigger": trigger,
        "settle_cycles": 2,
        "portable_state_quiescent": quiescent,
        "portable_state_blockers": reasons,
        "selection_mode": selection_mode,
        "causal_relevance_score": relevance,
        "causal_relevance_terms": matched_terms,
    }
    result = {
        "schema_version": "spatialaccagent.semantic_checkpoint_cut.v1",
        "status": "ready",
        **projection,
        "policy": {
            "trigger_is_semantic_not_wall_clock": True,
            "capture_occurs_after_committed_event_and_settle_cycles": True,
            "native_snapshot_may_capture_nonquiescent_simulator_state": True,
            "portable_cross_revision_requires_explicit_quiescence": True,
            "complete_quiescent_boundary_is_preferred_before_relevance_and_recency": True,
        },
    }
    result["cut_sha256"] = semantic_checkpoint_cut_sha256(result)
    return result


def _causal_aliases(value: Any) -> set[str]:
    text = str(value or "").strip()
    if not text:
        return set()
    aliases = {text}
    for separator in (".", "->"):
        if separator in text:
            aliases.add(text.rsplit(separator, 1)[-1])
    for prefix in (
        "node.pipeline.",
        "pipeline_boundary.",
        "boundary.",
    ):
        if text.startswith(prefix) and len(text) > len(prefix):
            aliases.add(text[len(prefix) :])
    return aliases


def checkpoint_cut_reachability(
    cut: dict[str, Any],
    causal_graph: dict[str, Any],
) -> dict[str, Any]:
    """Prove which graph identifiers are strictly downstream of a semantic cut.

    A frontier-scoped graph is not itself proof that every row is after the
    selected checkpoint. Unknown or ambiguous anchors intentionally yield no
    reusable nodes, which forces cross-revision replay back to a cold run.
    """

    nodes = [
        row
        for row in causal_graph.get("sacg_nodes", [])
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    ]
    edges = [
        row
        for row in causal_graph.get("sacg_edges", [])
        if isinstance(row, dict)
    ]
    boundaries = [
        row
        for row in causal_graph.get("cctg_boundaries", [])
        if isinstance(row, dict)
    ]
    paths = [
        row
        for row in causal_graph.get("cctg_causal_paths", [])
        if isinstance(row, dict)
    ]
    graph_projection = {
        "sacg_nodes": nodes,
        "sacg_edges": edges,
        "cctg_boundaries": boundaries,
        "cctg_causal_paths": paths,
    }
    graph_sha256 = canonical_contract_sha256(graph_projection)
    base = {
        "schema_version": CHECKPOINT_CUT_REACHABILITY_SCHEMA_VERSION,
        "graph_sha256": graph_sha256,
        "future_cctg_nodes": [],
        "policy": {
            "frontier_slice_membership_alone_is_not_downstream_proof": True,
            "directed_reachability_is_required": True,
            "unknown_or_ambiguous_anchor_forces_cold_capture": True,
        },
    }
    if cut.get("status") != "ready":
        return {
            **base,
            "status": "unavailable",
            "anchor": {},
            "errors": ["semantic checkpoint cut is not ready"],
        }
    if not nodes:
        return {
            **base,
            "status": "unavailable",
            "anchor": {},
            "errors": ["causal graph has no directed SACG nodes"],
        }

    node_by_id = {str(row["id"]): row for row in nodes}
    node_aliases: dict[str, set[str]] = {}
    for node_id, row in node_by_id.items():
        facts = row.get("facts", {}) if isinstance(row.get("facts"), dict) else {}
        for value in (node_id, row.get("name"), facts.get("stage_id")):
            for alias in _causal_aliases(value):
                node_aliases.setdefault(alias, set()).add(node_id)

    def resolve_node(value: Any) -> set[str]:
        resolved: set[str] = set()
        for alias in _causal_aliases(value):
            resolved.update(node_aliases.get(alias, set()))
        return resolved

    adjacency = {node_id: set() for node_id in node_by_id}
    directed_edges: list[tuple[dict[str, Any], str, str]] = []
    for row in edges:
        src = str(row.get("src") or "")
        dst = str(row.get("dst") or "")
        if src in node_by_id and dst in node_by_id:
            adjacency[src].add(dst)
            directed_edges.append((row, src, dst))

    boundary_rows: list[tuple[int, dict[str, Any], str, str]] = []
    boundary_aliases: dict[str, set[int]] = {}
    for index, row in enumerate(boundaries):
        src_candidates = resolve_node(row.get("src_stage"))
        dst_candidates = resolve_node(row.get("dst_stage"))
        if len(src_candidates) != 1 or len(dst_candidates) != 1:
            continue
        src = next(iter(src_candidates))
        dst = next(iter(dst_candidates))
        adjacency[src].add(dst)
        boundary_rows.append((index, row, src, dst))
        for value in (
            row.get("boundary_id"),
            row.get("boundary"),
            row.get("edge_id"),
        ):
            text = str(value or "").strip()
            if text:
                boundary_aliases.setdefault(text, set()).add(index)

    trigger = cut.get("trigger", {}) if isinstance(cut.get("trigger"), dict) else {}
    stage_or_boundary = str(trigger.get("stage_or_boundary") or "").strip()
    phase = str(trigger.get("phase") or "")
    boundary_matches: set[int] = set()
    boundary_matches.update(boundary_aliases.get(stage_or_boundary, set()))
    node_matches = resolve_node(stage_or_boundary)
    anchor_kind = ""
    anchor_node = ""
    include_anchor = False
    anchor_ids: list[str] = []
    errors: list[str] = []
    if len(boundary_matches) == 1:
        boundary_index = next(iter(boundary_matches))
        matching = next(
            (row for row in boundary_rows if row[0] == boundary_index),
            None,
        )
        if matching is None:
            errors.append("semantic cut boundary has no uniquely directed graph endpoints")
        else:
            _, row, _, anchor_node = matching
            anchor_kind = "cctg_boundary"
            include_anchor = True
            anchor_ids = sorted(
                {
                    str(value)
                    for value in (
                        row.get("boundary_id"),
                        row.get("edge_id"),
                    )
                    if value
                }
            )
    elif len(boundary_matches) > 1:
        errors.append("semantic cut boundary alias is ambiguous")
    elif len(node_matches) == 1:
        anchor_node = next(iter(node_matches))
        anchor_kind = "sacg_node"
        anchor_ids = [anchor_node]
        if phase.endswith("_start"):
            include_anchor = True
        elif phase.endswith(("_complete", "_commit", "_switch")):
            include_anchor = False
        else:
            errors.append("semantic cut phase has no directional start/completion meaning")
    elif len(node_matches) > 1:
        errors.append("semantic cut node alias is ambiguous")
    else:
        errors.append("semantic cut stage_or_boundary does not map to the causal graph")
    if errors or not anchor_node:
        return {
            **base,
            "status": "unavailable",
            "anchor": {
                "kind": anchor_kind or None,
                "stage_or_boundary": stage_or_boundary,
                "phase": phase,
                "identifiers": anchor_ids,
            },
            "errors": errors,
        }

    future_node_ids: set[str] = set()
    pending = [anchor_node] if include_anchor else sorted(adjacency[anchor_node])
    while pending:
        current = pending.pop()
        if current in future_node_ids:
            continue
        future_node_ids.add(current)
        pending.extend(sorted(adjacency.get(current, set()) - future_node_ids))

    future_identifiers: set[str] = set()
    for node_id in future_node_ids:
        row = node_by_id[node_id]
        facts = row.get("facts", {}) if isinstance(row.get("facts"), dict) else {}
        for value in (node_id, row.get("name"), facts.get("stage_id")):
            if value:
                future_identifiers.add(str(value))
    for row, src, dst in directed_edges:
        if src in future_node_ids and dst in future_node_ids:
            facts = (
                row.get("facts", {})
                if isinstance(row.get("facts"), dict)
                else {}
            )
            for value in (row.get("id"), facts.get("edge_id")):
                if value:
                    future_identifiers.add(str(value))
    for _, row, src, dst in boundary_rows:
        if src in future_node_ids and dst in future_node_ids:
            for value in (row.get("boundary_id"), row.get("edge_id")):
                if value:
                    future_identifiers.add(str(value))
    return {
        **base,
        "status": "pass",
        "anchor": {
            "kind": anchor_kind,
            "stage_or_boundary": stage_or_boundary,
            "phase": phase,
            "identifiers": anchor_ids,
            "graph_node_id": anchor_node,
            "anchor_is_in_future_set": include_anchor,
        },
        "future_cctg_nodes": sorted(future_identifiers),
        "future_graph_node_count": len(future_node_ids),
        "errors": [],
    }


def checkpoint_manifest_errors(
    manifest: dict[str, Any],
    *,
    artifact_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != CHECKPOINT_MANIFEST_SCHEMA_VERSION:
        errors.append("checkpoint manifest schema_version is invalid")
    if manifest.get("status") != "pass":
        errors.append("checkpoint manifest status is not pass")
    identity = manifest.get("execution_identity", {})
    if not isinstance(identity, dict) or not identity.get("compiled_model_sha256"):
        errors.append("checkpoint execution identity is missing")
    cut = manifest.get("semantic_cut", {})
    if not isinstance(cut, dict) or cut.get("status") != "ready":
        errors.append("checkpoint semantic cut is not ready")
    elif cut.get("cut_sha256") != semantic_checkpoint_cut_sha256(cut):
        errors.append("checkpoint semantic cut hash is invalid")
    if manifest.get("remote_acknowledgment_status") != "pass":
        errors.append("checkpoint remote acknowledgment is not pass")
    artifacts = manifest.get("state_artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("checkpoint has no state artifacts")
    else:
        for index, row in enumerate(artifacts):
            if not isinstance(row, dict):
                errors.append(f"checkpoint state_artifacts[{index}] is invalid")
                continue
            path = Path(str(row.get("path") or ""))
            if artifact_root is not None and not path.is_absolute():
                path = artifact_root / path
            expected = str(row.get("sha256") or "")
            if not path.is_file():
                errors.append(f"checkpoint state artifact is missing: {path}")
            elif not expected or sha256_file(path) != expected:
                errors.append(f"checkpoint state artifact hash mismatch: {path}")
    certificate = manifest.get("equivalence_certificate", {})
    if isinstance(certificate, dict) and certificate:
        errors.extend(
            checkpoint_equivalence_certificate_errors(
                manifest,
                artifact_root=artifact_root,
            )
        )
    return errors


def checkpoint_equivalence_certificate_errors(
    manifest: dict[str, Any],
    *,
    artifact_root: Path | None = None,
) -> list[str]:
    certificate = manifest.get("equivalence_certificate", {})
    errors: list[str] = []
    if not isinstance(certificate, dict):
        return ["checkpoint equivalence certificate is invalid"]
    if certificate.get("schema_version") != CHECKPOINT_EQUIVALENCE_SCHEMA_VERSION:
        errors.append("checkpoint equivalence certificate schema_version is invalid")
    if certificate.get("producer") != "framework":
        errors.append("checkpoint equivalence certificate is not framework-produced")
    if certificate.get("status") != "pass":
        errors.append("checkpoint equivalence certificate status is not pass")
    live_witnesses: dict[str, dict[str, Any]] = {}
    for side in ("cold", "restored"):
        row_name = f"{side}_live_state_witness"
        row = certificate.get(row_name, {})
        if not isinstance(row, dict):
            errors.append(f"checkpoint equivalence {row_name} is invalid")
            continue
        live_witnesses[side] = row
        if row.get("schema_version") != CHECKPOINT_LIVE_STATE_WITNESS_SCHEMA_VERSION:
            errors.append(f"checkpoint equivalence {row_name} schema is invalid")
        if row.get("status") != "pass":
            errors.append(f"checkpoint equivalence {row_name} is not pass")
        record = row.get("record", {})
        if not isinstance(record, dict) or not record:
            errors.append(f"checkpoint equivalence {row_name} has no live record")
        elif row.get("record_sha256") != canonical_contract_sha256(record):
            errors.append(f"checkpoint equivalence {row_name} record hash is invalid")
    if certificate.get("live_state_witness_match") is not True:
        errors.append("checkpoint equivalence live-state witnesses do not match")
    elif (
        live_witnesses.get("cold", {}).get("record")
        != live_witnesses.get("restored", {}).get("record")
    ):
        errors.append("checkpoint equivalence claims mismatched live-state witnesses match")
    for row_name in ("cold_progress_suffix", "restored_progress_suffix"):
        row = certificate.get(row_name, {})
        if not isinstance(row, dict):
            errors.append(f"checkpoint equivalence {row_name} is invalid")
            continue
        path = Path(str(row.get("path") or ""))
        if artifact_root is not None:
            if path.is_absolute() or ".." in path.parts:
                errors.append(
                    f"checkpoint equivalence {row_name} path is outside its artifact root"
                )
                continue
            path = artifact_root / path
        expected = str(row.get("sha256") or "")
        if not path.is_file():
            errors.append(f"checkpoint equivalence evidence is missing: {path}")
        elif not expected or sha256_file(path) != expected:
            errors.append(f"checkpoint equivalence evidence hash mismatch: {path}")
    comparisons = certificate.get("required_artifact_comparisons", [])
    if not isinstance(comparisons, list) or not comparisons:
        errors.append("checkpoint equivalence has no required artifact comparisons")
    else:
        for row in comparisons:
            if not isinstance(row, dict):
                errors.append("checkpoint equivalence artifact comparison is invalid")
                continue
            cold_present = row.get("cold_present")
            restored_present = row.get("restored_present")
            if cold_present is None:
                cold_present = bool(row.get("cold_sha256"))
            if restored_present is None:
                restored_present = bool(row.get("restored_sha256"))
            if cold_present is not restored_present or row.get("match") is not True:
                errors.append(
                    "checkpoint equivalence artifact presence or content does not match"
                )
            for side in ("cold", "restored"):
                path = Path(str(row.get(f"{side}_path") or ""))
                present = cold_present if side == "cold" else restored_present
                expected = str(row.get(f"{side}_sha256") or "")
                if present is False:
                    if expected:
                        errors.append(
                            f"checkpoint equivalence {side} artifact is absent but has a hash"
                        )
                    continue
                if artifact_root is not None:
                    if path.is_absolute() or ".." in path.parts:
                        errors.append(
                            "checkpoint equivalence artifact path is outside its artifact root"
                        )
                        continue
                    path = artifact_root / path
                if not path.is_file():
                    errors.append(
                        f"checkpoint equivalence {side} artifact is missing: {path}"
                    )
                elif not expected or sha256_file(path) != expected:
                    errors.append(
                        f"checkpoint equivalence {side} artifact hash mismatch: {path}"
                    )
    return errors


def _equivalence_bundle_digest(
    certificate: dict[str, Any],
    side: str,
) -> str:
    progress = certificate.get(f"{side}_progress_suffix", {})
    comparisons = certificate.get("required_artifact_comparisons", [])
    projection = {
        "progress_suffix_sha256": (
            progress.get("suffix_sha256") if isinstance(progress, dict) else None
        ),
        "live_state_witness_sha256": certificate.get(
            f"{side}_live_state_witness", {}
        ).get("record_sha256"),
        "artifacts": [
            {
                "kind": row.get("kind"),
                "sha256": row.get(f"{side}_sha256"),
                "present": (
                    row.get(f"{side}_present")
                    if row.get(f"{side}_present") is not None
                    else bool(row.get(f"{side}_sha256"))
                ),
            }
            for row in comparisons
            if isinstance(row, dict)
        ],
        "terminal": certificate.get(f"{side}_terminal", {}),
    }
    return canonical_contract_sha256(projection)


def _equivalence_valid(manifest: dict[str, Any]) -> bool:
    certificate = manifest.get("equivalence_certificate", {})
    comparisons = (
        certificate.get("required_artifact_comparisons", [])
        if isinstance(certificate, dict)
        else []
    )
    comparison_kinds = {
        str(row.get("kind") or "")
        for row in comparisons
        if isinstance(row, dict) and row.get("match") is True
    }
    return bool(
        isinstance(certificate, dict)
        and certificate.get("schema_version")
        == CHECKPOINT_EQUIVALENCE_SCHEMA_VERSION
        and certificate.get("status") == "pass"
        and certificate.get("producer") == "framework"
        and certificate.get("request_sha256") == manifest.get("request_sha256")
        and certificate.get("compiled_model_sha256")
        == manifest.get("execution_identity", {}).get("compiled_model_sha256")
        and certificate.get("workload_sha256")
        == manifest.get("execution_identity", {}).get("workload_sha256")
        and certificate.get("semantic_cut_sha256")
        == manifest.get("semantic_cut", {}).get("cut_sha256")
        and certificate.get("same_source_cold_suffix_sha256")
        and certificate.get("same_source_cold_suffix_sha256")
        == certificate.get("restored_suffix_sha256")
        and certificate.get("same_source_cold_suffix_sha256")
        == _equivalence_bundle_digest(certificate, "cold")
        and certificate.get("restored_suffix_sha256")
        == _equivalence_bundle_digest(certificate, "restored")
        and certificate.get("complete_required_state_coverage") is True
        and certificate.get("runtime_state_schema_match") is True
        and certificate.get("cold_and_restored_terminal_class_match") is True
        and certificate.get("live_state_witness_match") is True
        and certificate.get("cold_live_state_witness", {}).get("status") == "pass"
        and certificate.get("restored_live_state_witness", {}).get("status") == "pass"
        and certificate.get("cold_live_state_witness", {}).get("record_sha256")
        == canonical_contract_sha256(
            certificate.get("cold_live_state_witness", {}).get("record", {})
        )
        and certificate.get("restored_live_state_witness", {}).get("record_sha256")
        == canonical_contract_sha256(
            certificate.get("restored_live_state_witness", {}).get("record", {})
        )
        and certificate.get("cold_live_state_witness", {}).get("record")
        == certificate.get("restored_live_state_witness", {}).get("record")
        and certificate.get("cold_progress_suffix", {}).get("status") == "pass"
        and certificate.get("restored_progress_suffix", {}).get("status") == "pass"
        and {"rtl_output", "boundary_trace"}.issubset(comparison_kinds)
        and all(
            isinstance(row, dict) and row.get("match") is True
            for row in comparisons
        )
    )


def _is_checkpoint_suffix_semantic_record(
    row: dict[str, Any],
    *,
    anchor_sequence: int,
    anchor_cycle: int,
) -> bool:
    sequence = row.get("sequence")
    cycle = row.get("cycle")
    after_anchor = (
        isinstance(sequence, int)
        and not isinstance(sequence, bool)
        and sequence >= anchor_sequence
    ) or (
        not isinstance(sequence, int)
        and isinstance(cycle, int)
        and not isinstance(cycle, bool)
        and cycle >= anchor_cycle
    )
    if not after_anchor:
        return False
    phase = str(row.get("phase") or "")
    event_kind = str(row.get("event_kind") or "")
    return bool(
        event_kind != "checkpoint_control"
        and not phase.startswith("simulation_checkpoint_")
        and row.get("semantic_progress") is True
    )


def _checkpoint_suffix_semantic_records(
    path: Path,
    *,
    anchor_sequence: int,
    anchor_cycle: int,
) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("rb") as stream:
        while True:
            raw = stream.readline()
            if not raw or not raw.endswith(b"\n"):
                break
            try:
                row = json.loads(raw)
            except (ValueError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and _is_checkpoint_suffix_semantic_record(
                row,
                anchor_sequence=anchor_sequence,
                anchor_cycle=anchor_cycle,
            ):
                yield row


def _is_checkpoint_live_state_witness_record(
    row: dict[str, Any],
    *,
    anchor_sequence: int,
    anchor_cycle: int,
) -> bool:
    sequence = row.get("sequence")
    cycle = row.get("cycle")
    strictly_after_anchor = (
        isinstance(sequence, int)
        and not isinstance(sequence, bool)
        and sequence > anchor_sequence
    ) or (
        not isinstance(sequence, int)
        and isinstance(cycle, int)
        and not isinstance(cycle, bool)
        and cycle > anchor_cycle
    )
    if not strictly_after_anchor:
        return False
    phase = str(row.get("phase") or "")
    event_kind = str(row.get("event_kind") or "")
    if (
        event_kind == "checkpoint_control"
        or phase.startswith("simulation_checkpoint_")
        or phase.startswith("checkpoint_")
    ):
        return False
    return bool(
        row.get("semantic_progress") is True
        or event_kind in {"heartbeat", "stall_snapshot"}
    )


def checkpoint_live_state_witness(
    path: Path,
    *,
    anchor_sequence: int,
    anchor_cycle: int,
) -> dict[str, Any]:
    """Bind the first factual post-anchor event, not a replayed barrier record."""

    base = {
        "schema_version": CHECKPOINT_LIVE_STATE_WITNESS_SCHEMA_VERSION,
        "source_path": str(path),
        "anchor_sequence": anchor_sequence,
        "anchor_cycle": anchor_cycle,
    }
    if not path.is_file():
        return {
            **base,
            "status": "fail",
            "errors": ["live-state witness source progress log is missing"],
        }
    scanned_record_count = 0
    with path.open("rb") as stream:
        while True:
            raw = stream.readline()
            if not raw or not raw.endswith(b"\n"):
                break
            try:
                row = json.loads(raw)
            except (ValueError, json.JSONDecodeError):
                continue
            if not isinstance(row, dict):
                continue
            scanned_record_count += 1
            if not _is_checkpoint_live_state_witness_record(
                row,
                anchor_sequence=anchor_sequence,
                anchor_cycle=anchor_cycle,
            ):
                continue
            return {
                **base,
                "status": "pass",
                "source_sha256": sha256_file(path),
                "source_byte_count": path.stat().st_size,
                "scanned_record_count": scanned_record_count,
                "record_sha256": canonical_contract_sha256(row),
                "record": row,
                "errors": [],
            }
    return {
        **base,
        "status": "fail",
        "source_sha256": sha256_file(path),
        "source_byte_count": path.stat().st_size,
        "scanned_record_count": scanned_record_count,
        "errors": [
            "progress log has no factual non-checkpoint live-state record strictly after the capture anchor"
        ],
    }


def _checkpoint_live_state_witness_diff(
    cold: dict[str, Any],
    restored: dict[str, Any],
) -> dict[str, Any]:
    if cold.get("status") != "pass" or restored.get("status") != "pass":
        return {
            "schema_version": CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION,
            "status": "unavailable",
            "errors": ["cold or restored live-state witness is unavailable"],
        }
    cold_record = cold.get("record", {}) if isinstance(cold, dict) else {}
    restored_record = restored.get("record", {}) if isinstance(restored, dict) else {}
    if not isinstance(cold_record, dict) or not isinstance(restored_record, dict):
        return {
            "schema_version": CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION,
            "status": "unavailable",
            "errors": ["cold or restored live-state witness is unavailable"],
        }
    differences, truncated = _checkpoint_record_field_differences(
        cold_record,
        restored_record,
    )
    return {
        "schema_version": CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION,
        "status": "match" if not differences else "different",
        "field_differences": differences,
        "field_differences_truncated": truncated,
        "errors": [],
    }


_MISSING_SUFFIX_VALUE = object()


def _json_pointer_segment(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _bounded_suffix_diff_value(value: Any) -> Any:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    if len(encoded) <= 512:
        return value
    return {
        "value_type": type(value).__name__,
        "json_byte_count": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _checkpoint_record_field_differences(
    cold: Any,
    restored: Any,
    *,
    max_differences: int = 64,
) -> tuple[list[dict[str, Any]], bool]:
    differences: list[dict[str, Any]] = []
    truncated = False

    def append_difference(
        path: str,
        kind: str,
        cold_value: Any = _MISSING_SUFFIX_VALUE,
        restored_value: Any = _MISSING_SUFFIX_VALUE,
    ) -> None:
        nonlocal truncated
        if len(differences) >= max_differences:
            truncated = True
            return
        row: dict[str, Any] = {"path": path or "/", "kind": kind}
        if cold_value is not _MISSING_SUFFIX_VALUE:
            row["cold"] = _bounded_suffix_diff_value(cold_value)
        if restored_value is not _MISSING_SUFFIX_VALUE:
            row["restored"] = _bounded_suffix_diff_value(restored_value)
        differences.append(row)

    def visit(cold_value: Any, restored_value: Any, path: str) -> None:
        nonlocal truncated
        if len(differences) >= max_differences:
            truncated = True
            return
        if type(cold_value) is not type(restored_value):
            append_difference(path, "type_mismatch", cold_value, restored_value)
            return
        if cold_value == restored_value:
            return
        if isinstance(cold_value, dict):
            for key in sorted(set(cold_value) | set(restored_value)):
                child_path = f"{path}/{_json_pointer_segment(str(key))}"
                if key not in cold_value:
                    append_difference(
                        child_path,
                        "missing_from_cold",
                        restored_value=restored_value[key],
                    )
                elif key not in restored_value:
                    append_difference(
                        child_path,
                        "missing_from_restored",
                        cold_value=cold_value[key],
                    )
                else:
                    visit(cold_value[key], restored_value[key], child_path)
            return
        if isinstance(cold_value, list):
            for index, (cold_item, restored_item) in enumerate(
                zip_longest(
                    cold_value,
                    restored_value,
                    fillvalue=_MISSING_SUFFIX_VALUE,
                )
            ):
                child_path = f"{path}/{index}"
                if cold_item is _MISSING_SUFFIX_VALUE:
                    append_difference(
                        child_path,
                        "missing_from_cold",
                        restored_value=restored_item,
                    )
                elif restored_item is _MISSING_SUFFIX_VALUE:
                    append_difference(
                        child_path,
                        "missing_from_restored",
                        cold_value=cold_item,
                    )
                else:
                    visit(cold_item, restored_item, child_path)
            return
        append_difference(path, "value_mismatch", cold_value, restored_value)

    visit(cold, restored, "")
    return differences, truncated


def _checkpoint_suffix_semantic_record_diff(
    cold_path: Path,
    restored_path: Path,
    *,
    anchor_sequence: int,
    anchor_cycle: int,
    max_record_differences: int = 4,
) -> dict[str, Any]:
    if not cold_path.is_file() or not restored_path.is_file():
        return {
            "schema_version": CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION,
            "status": "unavailable",
            "errors": ["cold or restored semantic suffix evidence is missing"],
        }
    cold_records = _checkpoint_suffix_semantic_records(
        cold_path,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    restored_records = _checkpoint_suffix_semantic_records(
        restored_path,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    differing_record_count = 0
    reported: list[dict[str, Any]] = []
    cold_record_count = 0
    restored_record_count = 0
    identity_fields = (
        "sequence",
        "cycle",
        "event_kind",
        "phase",
        "layer",
        "token",
        "beat",
        "stage_or_boundary",
    )
    for ordinal, (cold, restored) in enumerate(
        zip_longest(
            cold_records,
            restored_records,
            fillvalue=_MISSING_SUFFIX_VALUE,
        )
    ):
        if cold is not _MISSING_SUFFIX_VALUE:
            cold_record_count += 1
        if restored is not _MISSING_SUFFIX_VALUE:
            restored_record_count += 1
        if cold is not _MISSING_SUFFIX_VALUE and restored is not _MISSING_SUFFIX_VALUE:
            if cold == restored:
                continue
            field_differences, field_diff_truncated = (
                _checkpoint_record_field_differences(cold, restored)
            )
        elif cold is _MISSING_SUFFIX_VALUE:
            field_differences = [
                {
                    "path": "/",
                    "kind": "record_missing_from_cold",
                    "restored": _bounded_suffix_diff_value(restored),
                }
            ]
            field_diff_truncated = False
        else:
            field_differences = [
                {
                    "path": "/",
                    "kind": "record_missing_from_restored",
                    "cold": _bounded_suffix_diff_value(cold),
                }
            ]
            field_diff_truncated = False
        differing_record_count += 1
        if len(reported) >= max_record_differences:
            continue
        reported.append(
            {
                "ordinal": ordinal,
                "cold_identity": (
                    {key: cold.get(key) for key in identity_fields}
                    if cold is not _MISSING_SUFFIX_VALUE
                    else None
                ),
                "restored_identity": (
                    {key: restored.get(key) for key in identity_fields}
                    if restored is not _MISSING_SUFFIX_VALUE
                    else None
                ),
                "field_differences": field_differences,
                "field_differences_truncated": field_diff_truncated,
            }
        )
    return {
        "schema_version": CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION,
        "status": "match" if differing_record_count == 0 else "different",
        "cold_record_count": cold_record_count,
        "restored_record_count": restored_record_count,
        "differing_record_count": differing_record_count,
        "reported_record_count": len(reported),
        "record_differences_truncated": differing_record_count > len(reported),
        "record_differences": reported,
        "errors": [],
    }


def checkpoint_suffix_evidence(
    path: Path,
    *,
    anchor_sequence: int,
    anchor_cycle: int,
) -> dict[str, Any]:
    """Hash committed post-capture progress records without loading the log.

    Checkpoint-control records are excluded from the semantic stream.  Every
    other field remains bound, including restored cycle/sequence counters and
    boundary payload digests, so a missing external-state field cannot be
    hidden by broad normalization.
    """

    digest = hashlib.sha256()
    record_count = 0
    semantic_progress_count = 0
    invalid_record_count = 0
    trailing_partial_byte_count = 0
    first_record: dict[str, Any] = {}
    last_record: dict[str, Any] = {}
    if not path.is_file():
        return {
            "schema_version": CHECKPOINT_SUFFIX_EVIDENCE_SCHEMA_VERSION,
            "status": "fail",
            "path": str(path),
            "errors": ["progress event log is missing"],
        }
    with path.open("rb") as stream:
        while True:
            raw = stream.readline()
            if not raw:
                break
            if not raw.endswith(b"\n"):
                trailing_partial_byte_count += len(raw)
                break
            try:
                row = json.loads(raw)
            except (ValueError, json.JSONDecodeError):
                invalid_record_count += 1
                continue
            if not isinstance(row, dict):
                invalid_record_count += 1
                continue
            if not _is_checkpoint_suffix_semantic_record(
                row,
                anchor_sequence=anchor_sequence,
                anchor_cycle=anchor_cycle,
            ):
                continue
            canonical = json.dumps(
                row,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
            digest.update(len(canonical).to_bytes(8, "big"))
            digest.update(canonical)
            record_count += 1
            semantic_progress_count += 1
            projection = {
                key: row.get(key)
                for key in (
                    "sequence",
                    "cycle",
                    "event_kind",
                    "phase",
                    "layer",
                    "token",
                    "beat",
                    "stage_or_boundary",
                )
            }
            if not first_record:
                first_record = projection
            last_record = projection
    errors = []
    if invalid_record_count:
        errors.append("progress suffix contains invalid complete JSONL records")
    if trailing_partial_byte_count:
        errors.append("progress suffix has a trailing partial JSONL record")
    if record_count == 0:
        errors.append(
            "progress suffix has no committed semantic records at or after the capture anchor"
        )
    return {
        "schema_version": CHECKPOINT_SUFFIX_EVIDENCE_SCHEMA_VERSION,
        "status": "pass" if not errors else "fail",
        "path": str(path),
        "sha256": sha256_file(path),
        "byte_count": path.stat().st_size,
        "suffix_sha256": digest.hexdigest() if record_count else None,
        "anchor_sequence": anchor_sequence,
        "anchor_cycle": anchor_cycle,
        "record_count": record_count,
        "semantic_progress_count": semantic_progress_count,
        "invalid_record_count": invalid_record_count,
        "trailing_partial_byte_count": trailing_partial_byte_count,
        "first_record": first_record,
        "last_record": last_record,
        "errors": errors,
    }


def framework_equivalence_certificate(
    *,
    request_sha256: str,
    execution_identity: dict[str, Any],
    semantic_cut: dict[str, Any],
    capture_report: dict[str, Any],
    restore_report: dict[str, Any],
    cold_progress_path: Path,
    restored_progress_path: Path,
    cold_live_progress_path: Path | None = None,
    restored_live_progress_path: Path | None = None,
    cold_required_artifacts: dict[str, Path],
    restored_required_artifacts: dict[str, Path],
    cold_terminal: dict[str, Any],
    restored_terminal: dict[str, Any],
) -> dict[str, Any]:
    """Create a framework-owned same-source cold/restore certificate."""

    errors: list[str] = []
    anchor_sequence = capture_report.get("captured_sequence")
    anchor_cycle = capture_report.get("captured_cycle")
    if not isinstance(anchor_sequence, int) or isinstance(anchor_sequence, bool):
        errors.append("capture report has no integer captured_sequence")
        anchor_sequence = -1
    if not isinstance(anchor_cycle, int) or isinstance(anchor_cycle, bool):
        errors.append("capture report has no integer captured_cycle")
        anchor_cycle = -1
    if restore_report.get("schema_version") != CHECKPOINT_RESTORE_REPORT_SCHEMA_VERSION:
        errors.append("restore report schema_version is invalid")
    if restore_report.get("status") != "pass":
        errors.append("restore report status is not pass")
    if restore_report.get("mode") != "portable_cross_revision":
        errors.append("restore report mode is not portable_cross_revision")
    if restore_report.get("same_source_equivalence_probe") is not True:
        errors.append("restore report is not bound to the same-source probe")
    if restore_report.get("request_sha256") != request_sha256:
        errors.append("restore report request hash mismatch")
    if restore_report.get("semantic_cut_sha256") != semantic_cut.get("cut_sha256"):
        errors.append("restore report semantic cut hash mismatch")
    if restore_report.get("runtime_state_schema_match") is not True:
        errors.append("restore report did not prove runtime state-schema equality")
    capture_schema = capture_report.get("state_schema", {})
    restored_schema_sha256 = str(restore_report.get("runtime_state_schema_sha256") or "")
    if (
        not restored_schema_sha256
        or restored_schema_sha256 != str(capture_schema.get("sha256") or "")
    ):
        errors.append("restored runtime state schema does not match the captured schema")
    if restore_report.get("restored_sequence") != anchor_sequence:
        errors.append("restored progress sequence does not match the capture anchor")
    if restore_report.get("restored_cycle") != anchor_cycle:
        errors.append("restored cycle does not match the capture anchor")
    for field in (
        "complete_testbench_external_state_restored",
        "pending_transactions_and_responses_restored",
        "immutable_files_reopened_at_captured_offsets",
        "event_queue_quiescent_after_restore",
    ):
        if restore_report.get(field) is not True:
            errors.append(f"restore report {field} is not true")

    cold_live_witness = checkpoint_live_state_witness(
        cold_live_progress_path or cold_progress_path,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    restored_live_witness = checkpoint_live_state_witness(
        restored_live_progress_path or restored_progress_path,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    for side, witness in (
        ("cold", cold_live_witness),
        ("restored", restored_live_witness),
    ):
        if witness.get("status") != "pass":
            errors.extend(
                f"{side} live-state witness: {value}"
                for value in witness.get("errors", [])
            )
    live_state_witness_diff = _checkpoint_live_state_witness_diff(
        cold_live_witness,
        restored_live_witness,
    )
    live_state_witness_match = bool(
        cold_live_witness.get("status") == "pass"
        and restored_live_witness.get("status") == "pass"
        and live_state_witness_diff.get("status") == "match"
    )
    if not live_state_witness_match:
        errors.append(
            "cold and restored factual post-anchor live-state witnesses differ"
        )

    cold_suffix = checkpoint_suffix_evidence(
        cold_progress_path,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    restored_suffix = checkpoint_suffix_evidence(
        restored_progress_path,
        anchor_sequence=anchor_sequence,
        anchor_cycle=anchor_cycle,
    )
    if cold_suffix.get("status") != "pass":
        errors.extend(
            f"cold suffix: {value}" for value in cold_suffix.get("errors", [])
        )
    if restored_suffix.get("status") != "pass":
        errors.extend(
            f"restored suffix: {value}"
            for value in restored_suffix.get("errors", [])
        )
    if cold_suffix.get("suffix_sha256") != restored_suffix.get("suffix_sha256"):
        errors.append("cold and restored progress suffix digests differ")
        semantic_record_diff = _checkpoint_suffix_semantic_record_diff(
            cold_progress_path,
            restored_progress_path,
            anchor_sequence=anchor_sequence,
            anchor_cycle=anchor_cycle,
        )
    else:
        semantic_record_diff = {
            "schema_version": CHECKPOINT_SUFFIX_RECORD_DIFF_SCHEMA_VERSION,
            "status": "match",
            "cold_record_count": cold_suffix.get("record_count"),
            "restored_record_count": restored_suffix.get("record_count"),
            "differing_record_count": 0,
            "reported_record_count": 0,
            "record_differences_truncated": False,
            "record_differences": [],
            "errors": [],
        }

    artifact_kinds = sorted(
        set(cold_required_artifacts) | set(restored_required_artifacts)
    )
    artifact_comparisons: list[dict[str, Any]] = []
    for kind in artifact_kinds:
        cold_path = cold_required_artifacts.get(kind)
        restored_path = restored_required_artifacts.get(kind)
        cold_present = bool(
            isinstance(cold_path, Path) and cold_path.is_file()
        )
        restored_present = bool(
            isinstance(restored_path, Path) and restored_path.is_file()
        )
        cold_sha256 = (
            sha256_file(cold_path)
            if cold_present
            else None
        )
        restored_sha256 = (
            sha256_file(restored_path)
            if restored_present
            else None
        )
        matches = bool(
            cold_present == restored_present
            and (
                not cold_present
                or bool(cold_sha256 and cold_sha256 == restored_sha256)
            )
        )
        if not matches:
            errors.append(f"cold and restored {kind} artifacts differ or are missing")
        artifact_comparisons.append(
            {
                "kind": kind,
                "cold_path": str(cold_path or ""),
                "cold_present": cold_present,
                "cold_sha256": cold_sha256,
                "cold_byte_count": (
                    cold_path.stat().st_size
                    if cold_present
                    else None
                ),
                "restored_path": str(restored_path or ""),
                "restored_present": restored_present,
                "restored_sha256": restored_sha256,
                "restored_byte_count": (
                    restored_path.stat().st_size
                    if restored_present
                    else None
                ),
                "match": matches,
            }
        )
    required_kinds = {"rtl_output", "boundary_trace"}
    if not required_kinds.issubset(artifact_kinds):
        errors.append(
            "equivalence evidence is missing required artifact kinds: "
            + ", ".join(sorted(required_kinds - set(artifact_kinds)))
        )

    terminal_match = bool(
        cold_terminal.get("returncode") is not None
        and cold_terminal.get("returncode") == restored_terminal.get("returncode")
        and cold_terminal.get("failure_class")
        == restored_terminal.get("failure_class")
    )
    if not terminal_match:
        errors.append("cold and restored terminal classes differ")

    cold_projection = {
        "progress_suffix_sha256": cold_suffix.get("suffix_sha256"),
        "live_state_witness_sha256": cold_live_witness.get("record_sha256"),
        "artifacts": [
            {
                "kind": row["kind"],
                "present": row["cold_present"],
                "sha256": row["cold_sha256"],
            }
            for row in artifact_comparisons
        ],
        "terminal": cold_terminal,
    }
    restored_projection = {
        "progress_suffix_sha256": restored_suffix.get("suffix_sha256"),
        "live_state_witness_sha256": restored_live_witness.get("record_sha256"),
        "artifacts": [
            {
                "kind": row["kind"],
                "present": row["restored_present"],
                "sha256": row["restored_sha256"],
            }
            for row in artifact_comparisons
        ],
        "terminal": restored_terminal,
    }
    cold_digest = canonical_contract_sha256(cold_projection)
    restored_digest = canonical_contract_sha256(restored_projection)
    if cold_digest != restored_digest:
        errors.append("cold and restored required-evidence bundle digests differ")
    return {
        "schema_version": CHECKPOINT_EQUIVALENCE_SCHEMA_VERSION,
        "status": "pass" if not errors else "fail",
        "producer": "framework",
        "request_sha256": request_sha256,
        "compiled_model_sha256": execution_identity.get("compiled_model_sha256"),
        "workload_sha256": execution_identity.get("workload_sha256"),
        "semantic_cut_sha256": semantic_cut.get("cut_sha256"),
        "same_source_cold_suffix_sha256": cold_digest,
        "restored_suffix_sha256": restored_digest,
        "complete_required_state_coverage": not errors,
        "runtime_state_schema_match": restore_report.get(
            "runtime_state_schema_match"
        )
        is True,
        "cold_and_restored_terminal_class_match": terminal_match,
        "live_state_witness_match": live_state_witness_match,
        "cold_live_state_witness": cold_live_witness,
        "restored_live_state_witness": restored_live_witness,
        "live_state_witness_diff": live_state_witness_diff,
        "cold_progress_suffix": cold_suffix,
        "restored_progress_suffix": restored_suffix,
        "semantic_record_diff": semantic_record_diff,
        "required_artifact_comparisons": artifact_comparisons,
        "cold_terminal": cold_terminal,
        "restored_terminal": restored_terminal,
        "errors": errors,
    }


def checkpoint_reuse_decision(
    manifest: dict[str, Any],
    current_identity: dict[str, Any],
    *,
    repair_impact: dict[str, Any] | None = None,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    blockers = checkpoint_manifest_errors(manifest, artifact_root=artifact_root)
    identity = manifest.get("execution_identity", {})
    if blockers:
        return {
            "schema_version": CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION,
            "status": "cold_capture_required",
            "mode": "cold_capture",
            "blockers": blockers,
        }
    if identity.get("workload_sha256") != current_identity.get("workload_sha256"):
        blockers.append("checkpoint workload identity differs from the current run")
    native = manifest.get("native_simulator_snapshot", {})
    exact_compiled_model = (
        identity.get("compiled_model_sha256")
        == current_identity.get("compiled_model_sha256")
    )
    if (
        not blockers
        and exact_compiled_model
        and isinstance(native, dict)
        and native.get("status") == "pass"
    ):
        if _equivalence_valid(manifest):
            return {
                "schema_version": CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION,
                "status": "ready",
                "mode": "native_exact_model",
                "checkpoint_id": manifest.get("checkpoint_id"),
                "blockers": [],
                "final_acceptance_requires_full_cold_run": True,
            }
        return {
            "schema_version": CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION,
            "status": "cold_capture_required",
            "mode": "cold_capture",
            "checkpoint_id": manifest.get("checkpoint_id"),
            "blockers": [
                "exact-model checkpoint lacks a same-source cold/replay equivalence certificate"
            ],
            "final_acceptance_requires_full_cold_run": True,
        }

    impact = repair_impact if isinstance(repair_impact, dict) else {}
    portable = manifest.get("portable_state_capsule", {})
    cut_certificate = manifest.get("causal_cut_certificate", {})
    semantic_cut = manifest.get("semantic_cut", {})
    state_schema = manifest.get("state_schema", {})
    if not blockers:
        if portable.get("status") != "pass":
            blockers.append("checkpoint has no passing portable state capsule")
        current_schema = current_identity.get("state_schema_sha256")
        if current_schema:
            if state_schema.get("sha256") != current_schema:
                blockers.append(
                    "portable checkpoint state schema differs from the current model"
                )
        elif state_schema.get("contract_sha256") != current_identity.get(
            "state_schema_contract_sha256"
        ):
            blockers.append(
                "portable checkpoint state-schema contract differs from the current model"
            )
        if not _equivalence_valid(manifest):
            blockers.append("checkpoint lacks a same-source cold/replay equivalence certificate")
        if cut_certificate.get("status") != "pass":
            blockers.append("checkpoint causal cut certificate is not pass")
        reachability = cut_certificate.get("reachability", {})
        if (
            not isinstance(reachability, dict)
            or reachability.get("schema_version")
            != CHECKPOINT_CUT_REACHABILITY_SCHEMA_VERSION
            or reachability.get("status") != "pass"
            or reachability.get("future_cctg_nodes")
            != cut_certificate.get("future_cctg_nodes")
            or reachability != semantic_cut.get("causal_reachability")
            or cut_certificate.get("future_cctg_nodes")
            != semantic_cut.get("future_cctg_nodes")
            or cut_certificate.get("semantic_cut_sha256")
            != semantic_cut.get("cut_sha256")
        ):
            blockers.append(
                "checkpoint lacks a matching directed cut-reachability certificate"
            )
        if not exact_compiled_model:
            if impact.get("status") != "ready":
                blockers.append("agent repair impact declaration is absent or not ready")
            if impact.get("state_schema_change") not in {"none", "compatible"}:
                blockers.append("repair may change the serialized state schema")
            affected = {
                str(value) for value in impact.get("affected_cctg_nodes", [])
            }
            future = {
                str(value)
                for value in cut_certificate.get("future_cctg_nodes", [])
            }
            if not affected or not affected.issubset(future):
                blockers.append(
                    "changed causal nodes are not wholly downstream of the checkpoint cut"
                )
        if cut_certificate.get("external_state_quiescent") is not True:
            blockers.append("checkpoint external AXI/testbench state is not certified quiescent")
    if blockers:
        return {
            "schema_version": CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION,
            "status": "cold_capture_required",
            "mode": "cold_capture",
            "checkpoint_id": manifest.get("checkpoint_id"),
            "blockers": blockers,
            "final_acceptance_requires_full_cold_run": True,
        }
    return {
        "schema_version": CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION,
        "status": "ready",
        "mode": "portable_cross_revision",
        "checkpoint_id": manifest.get("checkpoint_id"),
        "blockers": [],
        "final_acceptance_requires_full_cold_run": True,
    }


def checkpoint_manifests(run_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    rows = []
    for path in checkpoint_root(run_dir).glob("*/manifest.json"):
        value = read_json(path)
        if value:
            rows.append((path, value))
    return sorted(
        rows,
        key=lambda row: float(row[1].get("created_at_unix_sec") or 0.0),
        reverse=True,
    )


def prepare_checkpoint_request(
    run_dir: Path,
    *,
    targeted_replay_plan: dict[str, Any] | None = None,
    repair_impact: dict[str, Any] | None = None,
    debug_episode: dict[str, Any] | None = None,
) -> dict[str, Any]:
    board_manifest_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "board_simulation_manifest.json"
    )
    board_manifest = read_json(board_manifest_path)
    causal_path = (
        run_dir
        / "verification"
        / "case_diagnostics"
        / "sacg_cctg_causal_slice.json"
    )
    causal_slice = read_json(causal_path)
    progress_path = (
        run_dir
        / "verification"
        / "board_simulation"
        / "reports"
        / "progress_event_log.jsonl"
    )
    progress = read_checkpoint_cut_records(progress_path, causal_slice)
    records = progress.get("records", []) if isinstance(progress, dict) else []
    identity = simulation_execution_identity(board_manifest)
    cut = select_semantic_checkpoint_cut(records, causal_slice)
    causal_graph = (
        causal_slice.get("causal_graph_slice", {})
        if isinstance(causal_slice.get("causal_graph_slice"), dict)
        else {}
    )
    if cut.get("status") == "ready":
        reachability = checkpoint_cut_reachability(cut, causal_graph)
        cut["causal_reachability"] = reachability
        cut["future_cctg_nodes"] = reachability.get("future_cctg_nodes", [])
        cut["cut_sha256"] = semantic_checkpoint_cut_sha256(cut)
    contract = checkpoint_contract(board_manifest)
    contract_errors = checkpoint_contract_errors(contract)

    episode_projection = (
        checkpoint_debug_episode_projection(debug_episode)
        if isinstance(debug_episode, dict)
        and debug_episode.get("status") == "active"
        else {}
    )
    episode_frontier_binding = checkpoint_debug_episode_frontier_binding(
        debug_episode,
        causal_slice,
    )
    episode_frontier_ready = (
        not episode_projection or episode_frontier_binding.get("status") == "pass"
    )
    episode_id = str(episode_projection.get("episode_id") or "")
    decision: dict[str, Any] | None = None
    selected_manifest_path: Path | None = None
    for path, manifest in checkpoint_manifests(run_dir):
        if not episode_frontier_ready:
            break
        manifest_episode_id = str(
            manifest.get("debug_episode_id")
            or (
                manifest.get("debug_episode", {}).get("episode_id")
                if isinstance(manifest.get("debug_episode"), dict)
                else ""
            )
            or ""
        )
        if episode_id and manifest_episode_id and manifest_episode_id != episode_id:
            continue
        candidate = checkpoint_reuse_decision(
            manifest,
            identity,
            repair_impact=repair_impact,
            artifact_root=path.parent,
        )
        if candidate.get("status") == "ready":
            decision = candidate
            selected_manifest_path = path
            break
    if selected_manifest_path is not None and episode_id:
        activation = activate_checkpoint_for_debug_episode(
            run_dir,
            selected_manifest_path,
        )
        if activation.get("status") == "pass":
            selected_manifest_path = Path(str(activation["manifest"]))
        else:
            decision = None
            selected_manifest_path = None
    impact = repair_impact if isinstance(repair_impact, dict) else {}
    active_checkpoint = (
        debug_episode.get("checkpoint", {})
        if isinstance(debug_episode, dict)
        and isinstance(debug_episode.get("checkpoint"), dict)
        else {}
    )
    if (
        decision is None
        and episode_id
        and active_checkpoint.get("status") == "certified_active"
        and impact.get("status") == "ready"
    ):
        active_manifest_path = Path(str(active_checkpoint.get("manifest") or ""))
        active_manifest = read_json(active_manifest_path)
        invalidation = checkpoint_reuse_decision(
            active_manifest,
            identity,
            repair_impact=impact,
            artifact_root=active_manifest_path.parent,
        )
        if invalidation.get("status") != "ready":
            invalidate_debug_episode_checkpoint(
                run_dir,
                [str(value) for value in invalidation.get("blockers", [])],
            )
    if decision is None:
        decision_blockers = (
            contract_errors
            or ["no compatible content-addressed checkpoint is available"]
        )
        if not episode_frontier_ready:
            decision_blockers = list(
                dict.fromkeys(
                    [
                        *decision_blockers,
                        *[
                            str(value)
                            for value in episode_frontier_binding.get(
                                "blockers", []
                            )
                        ],
                    ]
                )
            )
        decision = {
            "schema_version": CHECKPOINT_REPLAY_DECISION_SCHEMA_VERSION,
            "status": "cold_capture_required",
            "mode": "cold_capture",
            "blockers": decision_blockers,
            "final_acceptance_requires_full_cold_run": True,
        }

    projection = {
        "execution_identity": identity,
        "semantic_cut": cut,
        "replay_decision": decision,
        "checkpoint_contract_status": (
            "ready" if not contract_errors else "missing_or_invalid"
        ),
        "checkpoint_contract_blockers": contract_errors,
        "selected_checkpoint_manifest": str(selected_manifest_path or ""),
        "selected_checkpoint_manifest_sha256": (
            sha256_file(selected_manifest_path)
            if selected_manifest_path is not None
            else None
        ),
        "targeted_replay_plan": targeted_replay_plan or {},
        "repair_impact": repair_impact or {},
    }
    if episode_projection:
        projection["debug_episode"] = episode_projection
        projection["debug_episode_frontier_binding"] = episode_frontier_binding
    request_ready = cut.get("status") == "ready" and episode_frontier_ready
    return {
        "schema_version": CHECKPOINT_REQUEST_SCHEMA_VERSION,
        "status": "ready" if request_ready else "blocked",
        **projection,
        "request_sha256": canonical_contract_sha256(projection),
        "storage_policy": {
            "root": str(checkpoint_root(run_dir)),
            "content_addressed": True,
            "immutable_workload_artifacts_are_referenced_not_duplicated": True,
            "max_checkpoint_count": int(
                os.environ.get(
                    "SPATIALACC_CHECKPOINT_KEEP_COUNT",
                    str(DEFAULT_MAX_CHECKPOINT_COUNT),
                )
            ),
            "max_checkpoint_bytes": int(
                os.environ.get(
                    "SPATIALACC_CHECKPOINT_MAX_BYTES",
                    str(DEFAULT_MAX_CHECKPOINT_BYTES),
                )
            ),
            "prune_only_acknowledged_inactive_checkpoints": True,
        },
        "resource_policy": {
            "max_heavy_jobs": 1,
            "llm_compile_and_simulation_must_not_overlap": True,
            "minimum_available_memory_bytes": int(
                os.environ.get(
                    "SPATIALACC_MIN_AVAILABLE_MEMORY_BYTES",
                    str(DEFAULT_MIN_AVAILABLE_MEMORY_BYTES),
                )
            ),
        },
        "acceptance_policy": {
            "checkpoint_replay_is_candidate_screening_not_stage_pass": True,
            "full_cold_exact_board_vcs_required_before_stage_pass": True,
            "unsafe_or_unproven_reuse_falls_back_to_cold_capture": True,
        },
    }


def checkpoint_request_projection(request: dict[str, Any]) -> dict[str, Any]:
    projection = {
        key: request.get(key)
        for key in (
            "execution_identity",
            "semantic_cut",
            "replay_decision",
            "checkpoint_contract_status",
            "checkpoint_contract_blockers",
            "selected_checkpoint_manifest",
            "selected_checkpoint_manifest_sha256",
            "targeted_replay_plan",
            "repair_impact",
        )
    }
    if "debug_episode" in request:
        projection["debug_episode"] = request.get("debug_episode")
        projection["debug_episode_frontier_binding"] = request.get(
            "debug_episode_frontier_binding"
        )
    return projection


def checkpoint_request_errors(request: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if request.get("schema_version") != CHECKPOINT_REQUEST_SCHEMA_VERSION:
        errors.append("checkpoint request schema_version is invalid")
    if request.get("status") != "ready":
        errors.append("checkpoint request status is not ready")
    if request.get("request_sha256") != canonical_contract_sha256(
        checkpoint_request_projection(request)
    ):
        errors.append("checkpoint request hash does not match its semantic projection")
    semantic_cut = request.get("semantic_cut", {})
    if not isinstance(semantic_cut, dict) or semantic_cut.get("status") != "ready":
        errors.append("checkpoint request semantic cut is not ready")
    elif semantic_cut.get("cut_sha256") != semantic_checkpoint_cut_sha256(
        semantic_cut
    ):
        errors.append("checkpoint request semantic cut hash is invalid")
    decision = request.get("replay_decision", {})
    if not isinstance(decision, dict) or decision.get("mode") not in {
        "cold_capture",
        "native_exact_model",
        "portable_cross_revision",
    }:
        errors.append("checkpoint request replay decision is invalid")
    if "debug_episode" in request:
        episode = request.get("debug_episode", {})
        identity = request.get("execution_identity", {})
        frontier_binding = request.get("debug_episode_frontier_binding", {})
        if (
            not isinstance(episode, dict)
            or episode.get("schema_version")
            != CHECKPOINT_DEBUG_EPISODE_SCHEMA_VERSION
            or episode.get("status") != "active"
            or not episode.get("episode_id")
        ):
            errors.append("checkpoint request debug episode is not active and valid")
        elif episode.get("workload_sha256") != identity.get("workload_sha256"):
            errors.append("checkpoint request debug episode workload identity mismatch")
        if (
            not isinstance(frontier_binding, dict)
            or frontier_binding.get("status") != "pass"
        ):
            errors.append("checkpoint request debug episode frontier binding is invalid")
        elif (
            not isinstance(semantic_cut, dict)
            or semantic_cut.get("frontier_id")
            != frontier_binding.get("observed_frontier_id")
            or frontier_binding.get("expected_frontier_id")
            != frontier_binding.get("observed_frontier_id")
        ):
            errors.append("checkpoint request semantic cut is not bound to the debug episode frontier")
    return errors


def persist_checkpoint_request(
    run_dir: Path,
    request: dict[str, Any],
    *,
    label: str = "latest",
) -> Path:
    safe_label = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in label
    ).strip("_") or "latest"
    path = checkpoint_root(run_dir) / "requests" / f"{safe_label}.json"
    write_json(path, request)
    return path


def checkpoint_framework_adapter_artifacts() -> list[dict[str, Any]]:
    """Return the current content-addressed framework checkpoint adapters."""

    adapter_dir = Path(__file__).parent / "simulator_adapters"
    rows = []
    for name, kind in (
        ("vcs_state_checkpoint_vpi.c", "vpi_source"),
        ("vcs_state_checkpoint_vpi.tab", "vpi_table"),
    ):
        path = adapter_dir / name
        rows.append(
            {
                "kind": kind,
                "path": str(path),
                "sha256": sha256_file(path) if path.is_file() else None,
                "framework_owned_read_only": True,
            }
        )
    return rows


def rebind_checkpoint_framework_adapter_artifacts(
    contract: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replace copied adapter identities with hashes from the immutable files."""

    rebound = copy.deepcopy(contract)
    portable = rebound.get("portable_state_capsule")
    if not isinstance(portable, dict):
        return rebound, {
            "schema_version": (
                "spatialaccagent.checkpoint_framework_adapter_binding.v1"
            ),
            "status": "fail",
            "changed": False,
            "errors": ["portable_state_capsule is unavailable for adapter binding"],
        }
    before = copy.deepcopy(portable.get("framework_adapter_artifacts"))
    after = checkpoint_framework_adapter_artifacts()
    errors = [
        f"framework checkpoint adapter is missing: {row['path']}"
        for row in after
        if not row.get("sha256")
    ]
    portable["framework_adapter_artifacts"] = after
    return rebound, {
        "schema_version": "spatialaccagent.checkpoint_framework_adapter_binding.v1",
        "status": "pass" if not errors else "fail",
        "changed": before != after,
        "source": "framework_owned_filesystem_content",
        "before": before,
        "after": copy.deepcopy(after),
        "errors": errors,
    }


def checkpoint_generation_authority(
    run_dir: Path,
    request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe the generic agent/framework split for a generated simulator hook."""

    current = request if isinstance(request, dict) else {}
    adapter_rows = checkpoint_framework_adapter_artifacts()
    return {
        "schema_version": "spatialaccagent.simulation_checkpoint_generation_authority.v1",
        "status": "ready",
        "current_request": current,
        "required_manifest_contract": {
            "schema_version": CHECKPOINT_CONTRACT_SCHEMA_VERSION,
            "status": "ready",
            "simulation_only": True,
            "synthesis_impact": "none",
            "drives_dut_signals": False,
            "captures_complete_simulator_state": True,
            "captures_testbench_and_external_model_state": True,
            "flushes_evidence_before_capture": True,
            "native_reuse_requires_exact_compiled_model": True,
            "cross_revision_reuse_requires_state_schema_match": True,
            "cross_revision_reuse_requires_causal_cut_certificate": True,
            "cross_revision_reuse_requires_equivalence_certificate": True,
            "full_cold_run_required_before_stage_pass": True,
            "supported_modes": [
                "cold_capture",
                "native_exact_model",
                "portable_cross_revision",
            ],
            "portable_state_capsule": {
                "status": "ready",
                "quiescent_cut_required": True,
                "restore_requires_runtime_schema_recheck": True,
                "state_adapter": "framework_vpi_state_capsule_v1",
                "state_schema": {
                    "selection": "all_mutable_dut_state_under_current_exact_dut_root",
                    "testbench_external_state_is_serialized_separately": True,
                    "hierarchical_name_width_kind_and_index_are_schema_keys": True,
                },
                "testbench_external_state": {
                    "status": "ready",
                    "captures_axi_ddr_model_state": True,
                    "captures_pending_transactions_and_responses": True,
                    "captures_queues_and_associative_arrays": True,
                    "captures_rng_state": True,
                    "captures_and_reopens_file_offsets": True,
                },
                "framework_adapter_artifacts": adapter_rows,
            },
            "adaptive_required_fields": {
                "portable_state_capsule.dut_state_root": (
                    "the exact current generated DUT instance path derived from the current "
                    "elaborated hierarchy; no prior-case path is valid"
                )
            },
            "outputs": {
                "manifest": {
                    "path": "checkpoint/manifest.json",
                    "producer": "framework_from_hash_verified_capture_artifacts",
                },
                "capture_report": {
                    "path": "checkpoint/capture_report.json",
                    "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
                },
                "restore_report": {
                    "path": "checkpoint/restore_report.json",
                    "schema_version": CHECKPOINT_RESTORE_REPORT_SCHEMA_VERSION,
                },
                "equivalence_report": {
                    "path": "checkpoint/equivalence_report.json",
                    "schema_version": CHECKPOINT_EQUIVALENCE_SCHEMA_VERSION,
                    "producer": "framework_from_two_executed_suffixes",
                },
            },
        },
        "agent_owned": {
            "derive_hook_from_current_exact_testbench_and_elaborated_hierarchy": True,
            "framework_vpi_system_function_abi": {
                "capture": (
                    "$spatialacc_state_capture(state_path, dut_state_root, schema_path)"
                ),
                "restore": (
                    "$spatialacc_state_restore(state_path, dut_state_root, schema_path)"
                ),
                "success_return_value": 0,
                "call_only_at_agent_proven_semantic_cut_or_restore_barrier": True,
            },
            "framework_runtime_plusarg_abi": {
                "common_required": [
                    "SPATIALACC_CHECKPOINT_MODE",
                    "SPATIALACC_CHECKPOINT_REQUEST",
                    "SPATIALACC_CHECKPOINT_REQUEST_SHA256",
                    "SPATIALACC_CHECKPOINT_SEMANTIC_CUT_SHA256",
                    "SPATIALACC_CHECKPOINT_DUT_ROOT",
                ],
                "capture_paths": [
                    "SPATIALACC_CHECKPOINT_DUT_STATE",
                    "SPATIALACC_CHECKPOINT_DUT_SCHEMA",
                    "SPATIALACC_CHECKPOINT_EXTERNAL_STATE",
                    "SPATIALACC_CHECKPOINT_CAPTURE_REPORT",
                ],
                "restore_paths": [
                    "SPATIALACC_CHECKPOINT_RESTORE_DUT_STATE",
                    "SPATIALACC_CHECKPOINT_RESTORE_DUT_SCHEMA",
                    "SPATIALACC_CHECKPOINT_RESTORE_EXTERNAL_STATE",
                    "SPATIALACC_CHECKPOINT_RESTORE_REPORT",
                ],
                "normal_restore_identity": "SPATIALACC_CHECKPOINT_ID",
                "same_source_probe_flag": (
                    "SPATIALACC_CHECKPOINT_EQUIVALENCE_PROBE"
                ),
                "adaptive_cut_fields": [
                    "SPATIALACC_CHECKPOINT_CUT_SEQUENCE",
                    "SPATIALACC_CHECKPOINT_CUT_CYCLE",
                    "SPATIALACC_CHECKPOINT_CUT_PHASE",
                    "SPATIALACC_CHECKPOINT_CUT_LAYER",
                    "SPATIALACC_CHECKPOINT_CUT_TOKEN",
                    "SPATIALACC_CHECKPOINT_CUT_BEAT",
                    "SPATIALACC_CHECKPOINT_FRONTIER",
                    "SPATIALACC_CHECKPOINT_SETTLE_CYCLES",
                ],
                "policy": {
                    "parse_values_at_runtime": True,
                    "never_embed_current_request_hash_or_cut_as_rtl_constants": True,
                    "missing_required_value_fails_before_capture_or_restore": True,
                },
            },
            "serialize_external_file_and_axi_ddr_model_state": True,
            "emit_stable_cut_safety_evidence": {
                "semantic_event_fields": {
                    "axi_read.outstanding": "nonnegative_integer",
                    "axi_read.pending_response": "boolean",
                    "axi_write.outstanding": "nonnegative_integer",
                    "axi_write.pending_response": "boolean",
                    "active_boundary_observation.event_queue_quiescent": True,
                },
                "prefer_boundary_before_downstream_cfg_preload_or_token_pulses": True,
                "restore_reexecutes_all_downstream_control_pulses_in_real_rtl": True,
                "never_jump_directly_to_observed_failure_state": True,
            },
            "reopen_immutable_workload_files_at_recorded_offsets_on_restore": True,
            "emit_capture_and_restore_reports": True,
            "never_self_certify_cold_restore_equivalence": True,
            "support_framework_same_source_restore_probe": True,
            "same_source_restore_probe_plusarg": (
                "+SPATIALACC_CHECKPOINT_EQUIVALENCE_PROBE=1"
            ),
            "never_copy_prior_case_signal_names_or_state_encodings": True,
            "capture_report_required_fields": [
                "schema_version",
                "status",
                "request_sha256",
                "mode",
                "semantic_cut_sha256",
                "checkpoint_trigger_observed",
                "complete_dut_state_captured",
                "complete_testbench_external_state_captured",
                "evidence_flushed_before_capture",
                "portable_state_capsule_complete",
                "captured_sequence",
                "captured_cycle",
                "external_state_quiescent_at_capture",
                "pending_event_queue_empty_at_capture",
                "state_schema",
                "state_artifacts",
            ],
            "restore_report_required_fields": [
                "schema_version",
                "status",
                "request_sha256",
                "mode",
                "semantic_cut_sha256",
                "runtime_state_schema_match",
                "runtime_state_schema_sha256",
                "restored_sequence",
                "restored_cycle",
                "complete_testbench_external_state_restored",
                "pending_transactions_and_responses_restored",
                "immutable_files_reopened_at_captured_offsets",
                "event_queue_quiescent_after_restore",
            ],
            "restore_report_conditional_fields": {
                "normal_checkpoint_replay": ["checkpoint_id"],
                "same_source_equivalence_probe": [
                    "same_source_equivalence_probe"
                ],
            },
            "required_state_artifact_kinds": [
                "dut_vpi_state",
                "dut_vpi_schema",
                "testbench_external_state",
            ],
        },
        "framework_owned": {
            "select_cut_from_sacg_cctg_progress": True,
            "verify_compiled_model_workload_state_schema_and_artifact_hashes": True,
            "run_same_compiled_model_cold_restore_probe_serially": True,
            "derive_suffix_equivalence_from_executed_evidence": True,
            "content_address_and_retain_capsules": True,
            "admit_at_most_one_heavy_job": True,
            "fall_back_to_cold_capture_on_any_unproven_reuse": True,
            "require_full_cold_exact_board_vcs_before_stage_pass": True,
        },
        "storage_root": str(checkpoint_root(run_dir)),
    }


def checkpoint_retention_plan(
    manifests: list[tuple[Path, dict[str, Any]]],
    *,
    max_count: int = DEFAULT_MAX_CHECKPOINT_COUNT,
    max_bytes: int = DEFAULT_MAX_CHECKPOINT_BYTES,
) -> dict[str, Any]:
    max_count = max(0, int(max_count))
    max_bytes = max(0, int(max_bytes))
    ordered = sorted(
        manifests,
        key=lambda row: float(row[1].get("created_at_unix_sec") or 0.0),
        reverse=True,
    )
    protected: list[tuple[Path, dict[str, Any]]] = []
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for path, manifest in ordered:
        is_protected = bool(
            manifest.get("active") is True
            or manifest.get("pinned") is True
            or manifest.get("remote_acknowledgment_status") != "pass"
        )
        if is_protected:
            protected.append((path, manifest))
        else:
            candidates.append((path, manifest))

    def declared_size(row: tuple[Path, dict[str, Any]]) -> int:
        return max(0, int(row[1].get("total_state_bytes") or 0))

    def frontier_id(row: tuple[Path, dict[str, Any]]) -> str:
        cut = row[1].get("semantic_cut", {})
        return str(cut.get("frontier_id") or "unknown") if isinstance(cut, dict) else "unknown"

    keep_rows = list(protected)
    selected_paths = {path for path, _ in keep_rows}
    kept_bytes = sum(declared_size(row) for row in keep_rows)
    kept_frontiers = {frontier_id(row) for row in keep_rows}
    overflow_reasons: list[str] = []
    if len(keep_rows) > max_count:
        overflow_reasons.append("protected checkpoint count exceeds the configured budget")
    if kept_bytes > max_bytes:
        overflow_reasons.append("protected checkpoint bytes exceed the configured budget")

    def select(row: tuple[Path, dict[str, Any]]) -> None:
        nonlocal kept_bytes
        keep_rows.append(row)
        selected_paths.add(row[0])
        kept_bytes += declared_size(row)
        kept_frontiers.add(frontier_id(row))

    def fits_budget(row: tuple[Path, dict[str, Any]]) -> bool:
        return (
            len(keep_rows) < max_count
            and kept_bytes + declared_size(row) <= max_bytes
        )

    # Preserve the most recent usable debugging state first.  A single state
    # larger than the byte target is retained only when no protected state is
    # already consuming the store; otherwise every prunable state remains
    # globally bounded by both configured budgets.
    if candidates and len(keep_rows) < max_count:
        latest = candidates[0]
        if fits_budget(latest):
            select(latest)
        elif not protected and max_bytes > 0 and declared_size(latest) > max_bytes:
            select(latest)
            overflow_reasons.append(
                "the latest usable checkpoint alone exceeds the configured byte budget"
            )

    # Spend remaining capacity on frontier diversity, then on recency.  The
    # preference never overrides the global budget as the previous
    # newest-per-frontier rule did.
    for row in candidates:
        if row[0] in selected_paths or frontier_id(row) in kept_frontiers:
            continue
        if fits_budget(row):
            select(row)
    for row in candidates:
        if row[0] in selected_paths:
            continue
        if fits_budget(row):
            select(row)

    prune_rows = [row for row in candidates if row[0] not in selected_paths]
    keep = [path for path, _ in keep_rows]
    prune = [path for path, _ in prune_rows]
    pruned_bytes = sum(declared_size(row) for row in prune_rows)
    retained_prunable = [row for row in keep_rows if row[0] not in {p for p, _ in protected}]
    return {
        "schema_version": "spatialaccagent.simulation_checkpoint_retention_plan.v1",
        "status": "ready",
        "keep": [str(path) for path in keep],
        "prune": [str(path) for path in prune],
        "kept_bytes": kept_bytes,
        "pruned_bytes": pruned_bytes,
        "protected_count": len(protected),
        "protected_bytes": sum(declared_size(row) for row in protected),
        "retained_acknowledged_inactive_count": len(retained_prunable),
        "max_count": max_count,
        "max_bytes": max_bytes,
        "budget_overflow": bool(overflow_reasons),
        "budget_overflow_reasons": overflow_reasons,
        "policy": {
            "plan_does_not_delete_files": True,
            "active_pinned_or_unacknowledged_never_pruned": True,
            "latest_usable_checkpoint_preferred": True,
            "frontier_diversity_preferred_within_global_budget": True,
            "acknowledged_inactive_checkpoints_are_globally_bounded": True,
            "single_oversize_latest_checkpoint_is_the_only_prunable_byte_exception": True,
        },
    }


def apply_checkpoint_retention_plan(
    run_dir: Path,
    plan: dict[str, Any],
) -> dict[str, Any]:
    root = checkpoint_root(run_dir).resolve()
    deleted: list[str] = []
    blockers: list[str] = []
    for value in plan.get("prune", []):
        manifest_path = Path(str(value)).resolve()
        directory = manifest_path.parent
        manifest = read_json(manifest_path)
        if (
            manifest_path.name != "manifest.json"
            or not directory.is_relative_to(root)
            or directory == root
        ):
            blockers.append(f"refused unsafe checkpoint prune target: {manifest_path}")
            continue
        if (
            manifest.get("remote_acknowledgment_status") != "pass"
            or manifest.get("active") is True
            or manifest.get("pinned") is True
        ):
            blockers.append(f"refused protected checkpoint prune target: {manifest_path}")
            continue
        try:
            shutil.rmtree(directory)
        except OSError as exc:
            blockers.append(f"checkpoint prune failed for {manifest_path}: {exc}")
            continue
        deleted.append(str(directory))
    report = {
        "schema_version": "spatialaccagent.simulation_checkpoint_retention_execution.v1",
        "status": "pass" if not blockers else "fail",
        "deleted": deleted,
        "blockers": blockers,
        "plan": plan,
        "policy": {
            "only_plan_selected_directories_are_deleted": True,
            "root_escape_is_forbidden": True,
            "active_pinned_or_unacknowledged_are_never_deleted": True,
        },
    }
    write_json(root / "retention_execution.json", report)
    return report


def available_memory_bytes(meminfo_path: Path = Path("/proc/meminfo")) -> int:
    try:
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return 0
    return 0


def resource_admission(
    *,
    purpose: str,
    estimated_peak_bytes: int = 0,
    minimum_available_bytes: int = DEFAULT_MIN_AVAILABLE_MEMORY_BYTES,
    observed_available_bytes: int | None = None,
) -> dict[str, Any]:
    available = (
        available_memory_bytes()
        if observed_available_bytes is None
        else observed_available_bytes
    )
    required = minimum_available_bytes + max(0, estimated_peak_bytes)
    admitted = available >= required
    return {
        "schema_version": HEAVY_JOB_RESOURCE_SCHEMA_VERSION,
        "status": "pass" if admitted else "wait",
        "purpose": purpose,
        "available_memory_bytes": available,
        "estimated_peak_bytes": estimated_peak_bytes,
        "minimum_reserve_bytes": minimum_available_bytes,
        "required_available_bytes": required,
        "max_heavy_jobs": 1,
        "summary": (
            "resource budget admits one heavy job"
            if admitted
            else "wait for memory before starting the heavy job"
        ),
    }


@contextlib.contextmanager
def heavy_job_lease(
    run_dir: Path,
    *,
    purpose: str,
    wait: bool = True,
    poll_seconds: float = 5.0,
) -> Iterator[dict[str, Any]]:
    lease_dir = run_dir / "agent" / "resource_leases"
    lease_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lease_dir / "heavy_job.lock"
    record_path = lease_dir / "heavy_job.json"
    with lock_path.open("a+", encoding="utf-8") as lock:
        while True:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if not wait:
                    raise RuntimeError("another SpatialAccAgent heavy job is active")
                time.sleep(max(0.1, poll_seconds))
        record = {
            "schema_version": HEAVY_JOB_RESOURCE_SCHEMA_VERSION,
            "status": "active",
            "purpose": purpose,
            "pid": os.getpid(),
            "started_at_unix_sec": time.time(),
            "max_heavy_jobs": 1,
        }
        write_json(record_path, record)
        try:
            yield record
        finally:
            completed = {
                **record,
                "status": "released",
                "released_at_unix_sec": time.time(),
            }
            write_json(record_path, completed)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
