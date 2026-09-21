"""One stable live-status file shared by the running Agent workflow."""

from __future__ import annotations

import copy
import fcntl
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


LIVE_STATE_SLOTS = (
    "controller",
    "agent",
    "board_run",
    "signals",
    "execution",
)


def live_state_path(run_dir: Path) -> Path:
    """Return the only cross-module live-status location for one run."""

    return Path(run_dir) / "repair_execution" / "live_state.json"


def _empty_state() -> dict[str, dict[str, Any]]:
    return {slot: {} for slot in LIVE_STATE_SLOTS}


def _normalized_state(value: Any) -> dict[str, dict[str, Any]]:
    state = value if isinstance(value, dict) else {}
    return {
        slot: copy.deepcopy(state.get(slot))
        if isinstance(state.get(slot), dict)
        else {}
        for slot in LIVE_STATE_SLOTS
    }


def _read_state(path: Path) -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    return _normalized_state(value)


def _json_copy(value: dict[str, Any]) -> dict[str, Any]:
    """Keep the live file ordinary JSON even when a caller has Path values."""

    normalized = json.loads(json.dumps(value, sort_keys=True, default=str))
    return normalized if isinstance(normalized, dict) else {}


def _atomic_write(path: Path, state: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


@contextmanager
def _locked_state(path: Path) -> Iterator[dict[str, dict[str, Any]]]:
    """Serialize slot replacements so independent writers preserve each other."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            state = _read_state(path)
            yield state
            _atomic_write(path, state)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_live_state(run_dir: Path) -> dict[str, dict[str, Any]]:
    """Read the fixed live state without making an absent file a failure."""

    return _read_state(live_state_path(run_dir))


def activate_live_state_slot(
    run_dir: Path,
    slot: str,
    data: dict[str, Any],
    *,
    binding: str,
) -> dict[str, Any]:
    """Start a new owner for one fixed state slot.

    Only a launch path may replace a slot binding. Later updates must supply
    the same binding, which prevents a late report from an old board job from
    replacing the active job's status.
    """

    if slot not in LIVE_STATE_SLOTS:
        raise ValueError(f"unsupported live state slot: {slot}")
    if not binding:
        raise ValueError(f"live state slot {slot} requires a binding")
    path = live_state_path(run_dir)
    entry = {
        "binding": str(binding),
        "updated_at_unix_ns": time.time_ns(),
        "data": _json_copy(data),
    }
    with _locked_state(path) as state:
        state[slot] = entry
    return {"applied": True, "slot": slot, **copy.deepcopy(entry)}


def update_live_state_slot(
    run_dir: Path,
    slot: str,
    data: dict[str, Any],
    *,
    binding: str,
) -> dict[str, Any]:
    """Replace a current slot value only when it belongs to the same owner."""

    if slot not in LIVE_STATE_SLOTS:
        raise ValueError(f"unsupported live state slot: {slot}")
    if not binding:
        raise ValueError(f"live state slot {slot} requires a binding")
    path = live_state_path(run_dir)
    with _locked_state(path) as state:
        existing = state.get(slot, {})
        if str(existing.get("binding") or "") != str(binding):
            return {
                "applied": False,
                "slot": slot,
                "binding": existing.get("binding"),
                "data": copy.deepcopy(existing.get("data") or {}),
            }
        entry = {
            "binding": str(binding),
            "updated_at_unix_ns": time.time_ns(),
            "data": _json_copy(data),
        }
        state[slot] = entry
    return {"applied": True, "slot": slot, **copy.deepcopy(entry)}


def run_dir_from_live_artifact(path: Path) -> Path | None:
    """Find a run directory from a repair or repair-execution artifact path."""

    for parent in Path(path).resolve().parents:
        if parent.name in {"repair", "repair_execution"}:
            return parent.parent
    return None


def board_run_binding(report: dict[str, Any]) -> str:
    """Return the stable ownership key for one real board execution."""

    fingerprint = str(report.get("input_fingerprint_sha256") or "").strip()
    remote_workdir = str(report.get("remote_workdir") or "").strip()
    if fingerprint and remote_workdir:
        return f"{fingerprint}@{remote_workdir}"
    return ""


def board_run_status(report: dict[str, Any]) -> dict[str, Any]:
    """Project a board result into a small status value, never full evidence."""

    compile_report = report.get("compile", {})
    run_report = report.get("run", {})
    return {
        key: report.get(key)
        for key in (
            "verification_layer",
            "status",
            "phase",
            "failure_class",
            "stage_pass_eligible",
            "input_fingerprint_sha256",
            "remote_workdir",
            "simulator_path",
        )
        if report.get(key) is not None
    } | {
        "compile_status": compile_report.get("status")
        if isinstance(compile_report, dict)
        else None,
        "run_status": run_report.get("status")
        if isinstance(run_report, dict)
        else None,
    }
