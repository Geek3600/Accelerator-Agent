"""Persistent exact-measurement ledger for Stage 4 DSE.

Stage 4 may estimate and rank candidates, but predictions are not measurements.
A synthesis candidate is measured from real Vivado resource/timing
reports and RTL-cycle-derived throughput; implementation scope can add power
and implementation evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
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
SYNTHESIS_APP_SHELL_SCOPE = "exact_target_board_app_shell_synthesis"
SYNTHESIS_KERNEL_SCOPE = "generated_kernel_synthesis"
DSE_ESTIMATED_CYCLE_MODEL = "dse_structural_cycle_estimate_v1"
SUPPORTED_PERFORMANCE_MODELS = {
    DSE_ESTIMATED_CYCLE_MODEL,
    "single_block_reuse_operator_token_pipeline_v1",
    "single_block_reuse_operator_token_pipeline_v2_no_handoff",
    "synthesizable_dut_counter",
}


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


def complete_metrics(metrics: dict[str, Any], measurement_scope: str = EXACT_TARGET_BOARD_APP_SHELL_SCOPE) -> bool:
    if not isinstance(metrics, dict):
        return False
    if not isinstance(metrics.get("resources"), dict) or not metrics["resources"]:
        return False
    if any(type(value) is not int or value < 0 for value in metrics["resources"].values()):
        return False
    if metrics.get("performance_model") not in SUPPORTED_PERFORMANCE_MODELS:
        return False
    required = (
        ("clock_frequency_mhz", "performance_tokens_per_second")
        if measurement_scope in {SYNTHESIS_APP_SHELL_SCOPE, SYNTHESIS_KERNEL_SCOPE}
        else QOR_KEYS[1:]
    )
    for key in required:
        try:
            value = float(metrics.get(key))
            if not math.isfinite(value) or value < 0 or (key != "power_w" and value == 0):
                return False
        except (TypeError, ValueError):
            return False
    return True


def load_latest(path: Path, *, linear_schedule: str | None = None) -> dict[str, dict[str, Any]]:
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
            and (linear_schedule is None or row.get("linear_schedule") == linear_schedule)
            and status in {"measured", "infeasible"}
            and scope in {EXACT_TARGET_BOARD_APP_SHELL_SCOPE, SYNTHESIS_APP_SHELL_SCOPE, SYNTHESIS_KERNEL_SCOPE}
            and (status != "measured" or complete_metrics(row.get("metrics") or {}, scope))
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
    linear_schedule: str | None = None,
) -> dict[str, Any]:
    from accagent.framework.dse_estimator import linear_schedule_id

    if measurement_status not in {"measured", "infeasible"}:
        raise ValueError("measurement_status must be measured or infeasible")
    if measurement_scope not in {EXACT_TARGET_BOARD_APP_SHELL_SCOPE, SYNTHESIS_APP_SHELL_SCOPE, SYNTHESIS_KERNEL_SCOPE}:
        raise ValueError("DSE measurement scope is unsupported")
    if measurement_status == "measured" and not complete_metrics(metrics or {}, measurement_scope):
        raise ValueError("the measured candidate is missing required QoR metrics for its scope")
    row = {
        "schema_version": "spatialaccagent.dse_measurement.v1",
        "linear_schedule": linear_schedule or linear_schedule_id(),
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
