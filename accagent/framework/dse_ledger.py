"""Persistent exact-measurement ledger for Stage 4 DSE.

Stage 4 may enumerate and validate candidates statically, but it never assigns
QoR values.  A candidate becomes measured only after the exact target-board
app-shell flow has emitted all four real metrics.  Implementation failure is
also a measurement outcome because it proves that the concrete candidate is
not deployable on the target board.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


QOR_KEYS = (
    "resources",
    "power_w",
    "clock_frequency_mhz",
    "performance_tokens_per_second",
)

EXACT_TARGET_BOARD_APP_SHELL_SCOPE = "exact_target_board_app_shell"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def candidate_fingerprint(parameters: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(parameters).encode("utf-8")).hexdigest()


def candidate_id(parameters: dict[str, Any]) -> str:
    return f"arch_{candidate_fingerprint(parameters)[:12]}"


def ledger_path(run_dir: Path) -> Path:
    return run_dir / "parameter_binding" / "dse_measurements.jsonl"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def complete_metrics(metrics: dict[str, Any]) -> bool:
    if not isinstance(metrics, dict):
        return False
    if not isinstance(metrics.get("resources"), dict) or not metrics["resources"]:
        return False
    for key in QOR_KEYS[1:]:
        try:
            if float(metrics.get(key)) < 0:
                return False
        except (TypeError, ValueError):
            return False
    return True


def load_latest(path: Path) -> dict[str, dict[str, Any]]:
    """Return one current record per candidate; malformed historic rows are ignored."""

    latest: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return latest
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        fingerprint = str(row.get("candidate_fingerprint") or "")
        status = str(row.get("measurement_status") or "")
        scope = str(row.get("measurement_scope") or "")
        if (
            fingerprint
            and status in {"measured", "infeasible"}
            and scope == EXACT_TARGET_BOARD_APP_SHELL_SCOPE
        ):
            latest[fingerprint] = row
    return latest


def append_measurement(
    path: Path,
    *,
    parameters: dict[str, Any],
    measurement_status: str,
    measurement_scope: str,
    metrics: dict[str, Any] | None = None,
    evidence_paths: list[str] | None = None,
    binding_path: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    if measurement_status not in {"measured", "infeasible"}:
        raise ValueError("measurement_status must be measured or infeasible")
    if measurement_scope != EXACT_TARGET_BOARD_APP_SHELL_SCOPE:
        raise ValueError("DSE measurements require exact_target_board_app_shell scope")
    if measurement_status == "measured" and not complete_metrics(metrics or {}):
        raise ValueError("a measured candidate requires all four real QoR metrics")
    row = {
        "schema_version": "spatialaccagent.dse_measurement.v1",
        "timestamp": utc_now(),
        "candidate_id": candidate_id(parameters),
        "candidate_fingerprint": candidate_fingerprint(parameters),
        "parameters": parameters,
        "measurement_status": measurement_status,
        "measurement_scope": measurement_scope,
        "metrics": metrics if measurement_status == "measured" else None,
        "evidence_paths": [str(value) for value in evidence_paths or [] if str(value)],
        "binding_path": str(binding_path or ""),
        "reason": str(reason or ""),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(row) + "\n")
    return row


def measurement_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    legal = [record for record in records if record.get("feasible")]
    measured = [
        record
        for record in legal
        if isinstance(record.get("measurement"), dict)
        and record["measurement"].get("measurement_status") == "measured"
    ]
    infeasible = [
        record
        for record in legal
        if isinstance(record.get("measurement"), dict)
        and record["measurement"].get("measurement_status") == "infeasible"
    ]
    pending = [record for record in legal if record.get("measurement") is None]
    return {
        "legal_candidate_count": len(legal),
        "measured_candidate_count": len(measured),
        "implementation_infeasible_count": len(infeasible),
        "unmeasured_candidate_count": len(pending),
        "complete": bool(legal) and not pending,
    }
