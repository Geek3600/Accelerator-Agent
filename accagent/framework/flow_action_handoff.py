"""Content-addressed handoff from flow-controller decisions into Stage 6.

The flow controller may produce a bounded next-step plan after a Stage-6
failure.  Those actions are planning evidence, not direct framework commands:
Stage 6 supplies one verified decision to its repair planner, which remains
responsible for choosing and validating the executable repair workflow.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from accagent.framework.sacg_utils import safe_id, write_json
from accagent.framework.workflow_contract import STAGE_TARGET_ALIASES


HANDOFF_SCHEMA_VERSION = "spatialaccagent.stage6_flow_controller_handoff.v1"
CONSUMPTION_SCHEMA_VERSION = "spatialaccagent.stage6_flow_controller_consumption.v1"
_VOLATILE_LLM_RECORD_FIELDS = {
    "duration_sec",
    "live_transaction_id",
    "live_transaction_path",
    "request_path",
    "result_path",
}


def read_json_if_exists(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "utf-8"
        )
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def is_within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def resolve_run_path(run_dir: Path, value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = run_dir / path
    if not is_within(run_dir, path):
        return None
    return path.resolve()


def normalized_llm_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key not in _VOLATILE_LLM_RECORD_FIELDS
    }


def normalized_action(action: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(action, sort_keys=True, ensure_ascii=True))


def target_stage(action: dict[str, Any]) -> str:
    value = str(action.get("target_stage") or action.get("stage") or "").strip()
    if value in STAGE_TARGET_ALIASES:
        return STAGE_TARGET_ALIASES[value]
    return value


def action_record_path(event_path: Path, event_index: int, action: dict[str, Any]) -> Path:
    action_type = safe_id(str(action.get("action_type") or "action"))
    action_id = safe_id(str(action.get("id") or action_type))
    if any(token in action_type for token in ("barrier", "contamination", "quarantine")):
        directory = "trust_barriers"
    elif any(token in action_type for token in ("repair", "recovery")):
        directory = "bounded_repairs"
    elif any(token in action_type for token in ("retry", "replay")):
        directory = "retry_requests"
    else:
        directory = "flow_actions"
    return event_path.parent.parent / directory / f"{event_index:03d}_{action_id}.json"


def source_sacg_identity(event: dict[str, Any], run_dir: Path) -> tuple[Path | None, str]:
    state_path = resolve_run_path(run_dir, event.get("sacg_state"))
    if state_path is None or not state_path.is_file():
        return None, ""
    return state_path, sha256_file(state_path)


def flow_controller_record(event: dict[str, Any], run_dir: Path) -> tuple[Path | None, dict[str, Any]]:
    review = event.get("llm_flow_controller", {})
    if not isinstance(review, dict):
        return None, {}
    result_path = resolve_run_path(run_dir, review.get("agent_record"))
    if result_path is None or not result_path.is_file():
        return None, {}
    record = read_json_if_exists(result_path)
    output = record.get("output", {}) if isinstance(record.get("output"), dict) else {}
    if (
        record.get("schema_version") != "spatialaccagent.stage_worker_record.v0"
        or record.get("agent") != "flow_controller_agent"
        or record.get("stage") != "flow_orchestration"
        or record.get("used_fallback") is True
        or record.get("error") not in {None, ""}
        or output.get("agent") != "flow_controller_agent"
        or not str(output.get("status") or "").strip()
    ):
        return None, {}
    return result_path, record


def event_candidate(
    *,
    event_path: Path,
    event: dict[str, Any],
    run_dir: Path,
    current_sacg_sha256: str,
) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if event.get("schema_version") != "spatialaccagent.flow_event_action_record.v0":
        return None, ["flow event has an unsupported schema"]
    try:
        event_index = int(event.get("flow_event_index"))
    except (TypeError, ValueError):
        return None, ["flow event has no numeric index"]
    source_state_path, source_state_sha256 = source_sacg_identity(event, run_dir)
    if source_state_sha256 != current_sacg_sha256:
        return None, []
    identities = event.get("source_identities", {})
    if isinstance(identities, dict):
        expected_state_sha256 = str(identities.get("source_sacg_state_sha256") or "")
        if expected_state_sha256 and expected_state_sha256 != source_state_sha256:
            return None, ["flow event source SACG identity is stale"]
    result_path, result_record = flow_controller_record(event, run_dir)
    if result_path is None:
        return None, ["flow event is missing a successful flow-controller record"]
    if isinstance(identities, dict):
        expected_result_sha256 = str(identities.get("flow_controller_result_sha256") or "")
        if expected_result_sha256 and expected_result_sha256 != sha256_file(result_path):
            return None, ["flow event flow-controller result identity is stale"]
    output = result_record.get("output", {})
    event_actions = event.get("executable_actions", [])
    result_actions = output.get("executable_actions", [])
    if not isinstance(event_actions, list) or not isinstance(result_actions, list):
        return None, ["flow-controller actions are not a list"]
    result_action_hashes = {
        canonical_sha256(normalized_action(action))
        for action in result_actions
        if isinstance(action, dict)
    }
    eligible: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    materialized_paths: list[dict[str, str]] = []
    for action in event_actions:
        if not isinstance(action, dict) or target_stage(action) != "debug_loop":
            continue
        action_hash = canonical_sha256(normalized_action(action))
        if action_hash not in result_action_hashes:
            errors.append("flow action does not match its flow-controller result")
            continue
        materialized = action_record_path(event_path, event_index, action)
        record = read_json_if_exists(materialized)
        if (
            not materialized.is_file()
            or record.get("schema_version") != "spatialaccagent.flow_action_record.v0"
            or canonical_sha256(normalized_action(record.get("action", {}))) != action_hash
            or resolve_run_path(run_dir, record.get("source_flow_event"))
            != event_path.resolve()
        ):
            errors.append(f"flow action is not faithfully materialized: {action.get('id')}")
            continue
        action_ref = {
            "id": str(action.get("id") or action.get("action_type") or "action"),
            "action_sha256": action_hash,
            "path": str(materialized),
            "sha256": sha256_file(materialized),
            "action": normalized_action(action),
        }
        if action.get("requires_approval") is True:
            deferred.append(action_ref)
            continue
        if action.get("requires_approval") is not False:
            errors.append(f"flow action lacks explicit approval boundary: {action_ref['id']}")
            continue
        if not isinstance(action.get("acceptance_checkers"), list) or not action.get("acceptance_checkers"):
            errors.append(f"flow action lacks acceptance checkers: {action_ref['id']}")
            continue
        eligible.append(action_ref)
        materialized_paths.append(
            {key: action_ref[key] for key in ("id", "path", "sha256", "action_sha256")}
        )
    if errors:
        return None, errors
    if not eligible:
        return None, ["current flow decision has no auto-executable Stage-6 action"]
    output_identity = canonical_sha256(normalized_llm_record(result_record))
    identity_payload = {
        "target_stage": "debug_loop",
        "source_sacg_state_sha256": source_state_sha256,
        "flow_controller_result_sha256": output_identity,
        "actions": [item["action"] for item in eligible],
        "deferred_actions": [item["action"] for item in deferred],
    }
    return {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "status": "ready",
        "target_stage": "debug_loop",
        "handoff_identity": canonical_sha256(identity_payload),
        "identity_payload": identity_payload,
        "source_sacg_state": {
            "path": str(source_state_path),
            "sha256": source_state_sha256,
        },
        "flow_controller_result": {
            "path": str(result_path),
            "sha256": output_identity,
            "agent_status": output.get("status"),
            "summary": output.get("summary"),
        },
        "source_flow_event": {
            "path": str(event_path),
            "sha256": sha256_file(event_path),
            "index": event_index,
            "decision": event.get("decision"),
            "stage": event.get("stage"),
        },
        "actions": eligible,
        "deferred_actions": deferred,
        "materialized_actions": materialized_paths,
        "audit": {
            "status": "pass",
            "same_stage_target_required": True,
            "source_sacg_identity_required": True,
            "flow_controller_result_identity_required": True,
            "approval_required_actions_deferred": True,
        },
    }, []


def consumption_path(run_dir: Path) -> Path:
    return run_dir / "debug_loop" / "flow_handoffs" / "consumed.json"


def consumed_handoffs(run_dir: Path) -> dict[str, Any]:
    payload = read_json_if_exists(consumption_path(run_dir))
    values = payload.get("consumed", {}) if isinstance(payload.get("consumed"), dict) else {}
    return values


def pending_stage6_flow_handoff(run_dir: Path, source_sacg_state: Path) -> dict[str, Any]:
    """Return the newest valid, unconsumed flow decision for the current Stage-6 entry."""

    source_sacg_state = source_sacg_state.resolve()
    if not source_sacg_state.is_file():
        return {"status": "blocked", "summary": "Stage-6 source SACG state is unavailable"}
    current_sacg_sha256 = sha256_file(source_sacg_state)
    candidates: list[tuple[int, Path, dict[str, Any]]] = []
    invalid_latest: tuple[int, list[str]] | None = None
    for event_path in run_dir.rglob("flow_events/*.json"):
        event = read_json_if_exists(event_path)
        candidate, errors = event_candidate(
            event_path=event_path,
            event=event,
            run_dir=run_dir,
            current_sacg_sha256=current_sacg_sha256,
        )
        if candidate is not None:
            candidates.append((int(candidate["source_flow_event"]["index"]), event_path, candidate))
            continue
        if errors:
            event_stage_path, event_state_sha = source_sacg_identity(event, run_dir)
            actions = event.get("executable_actions", [])
            has_stage6_action = isinstance(actions, list) and any(
                isinstance(action, dict) and target_stage(action) == "debug_loop"
                for action in actions
            )
            if event_state_sha == current_sacg_sha256 and has_stage6_action:
                try:
                    event_index = int(event.get("flow_event_index"))
                except (TypeError, ValueError):
                    event_index = -1
                if invalid_latest is None or event_index >= invalid_latest[0]:
                    invalid_latest = (event_index, errors)
    if not candidates:
        if invalid_latest is not None:
            return {
                "status": "blocked",
                "summary": "latest Stage-6 flow decision failed handoff validation: "
                + "; ".join(invalid_latest[1]),
            }
        return {"status": "not_required", "summary": "no current Stage-6 flow-controller handoff"}
    _, _, newest = max(candidates, key=lambda item: (item[0], str(item[1])))
    if invalid_latest is not None and invalid_latest[0] > newest["source_flow_event"]["index"]:
        return {
            "status": "blocked",
            "summary": "latest Stage-6 flow decision failed handoff validation: "
            + "; ".join(invalid_latest[1]),
        }
    if newest["handoff_identity"] in consumed_handoffs(run_dir):
        return {
            "status": "already_consumed",
            "handoff_identity": newest["handoff_identity"],
            "summary": "current content-addressed Stage-6 flow decision was already consumed",
        }
    return newest


def validate_stage6_flow_handoff(handoff: Any, run_dir: Path) -> list[str]:
    if not isinstance(handoff, dict):
        return ["flow-controller handoff is not an object"]
    if handoff.get("schema_version") != HANDOFF_SCHEMA_VERSION:
        return ["flow-controller handoff has an unsupported schema"]
    if handoff.get("status") != "ready" or handoff.get("target_stage") != "debug_loop":
        return ["flow-controller handoff is not ready for Stage 6"]
    identity_payload = handoff.get("identity_payload")
    if not isinstance(identity_payload, dict) or canonical_sha256(identity_payload) != handoff.get("handoff_identity"):
        return ["flow-controller handoff identity does not match its content"]
    source = handoff.get("source_sacg_state", {})
    result = handoff.get("flow_controller_result", {})
    event = handoff.get("source_flow_event", {})
    for name, value in (("source SACG state", source), ("flow-controller result", result), ("flow event", event)):
        if not isinstance(value, dict):
            return [f"flow-controller handoff {name} binding is invalid"]
        path = resolve_run_path(run_dir, value.get("path"))
        if path is None or not path.is_file() or not is_sha256(value.get("sha256")):
            return [f"flow-controller handoff {name} binding is unavailable"]
    source_path = resolve_run_path(run_dir, source.get("path"))
    event_path = resolve_run_path(run_dir, event.get("path"))
    if source_path is None or event_path is None:
        return ["flow-controller handoff binding escaped the run directory"]
    if sha256_file(source_path) != source.get("sha256") or sha256_file(event_path) != event.get("sha256"):
        return ["flow-controller handoff source evidence changed after selection"]
    record = read_json_if_exists(resolve_run_path(run_dir, result.get("path")) or Path())
    if canonical_sha256(normalized_llm_record(record)) != result.get("sha256"):
        return ["flow-controller result identity changed after selection"]
    actions = handoff.get("actions", [])
    if not isinstance(actions, list) or not actions:
        return ["flow-controller handoff has no auto-executable actions"]
    for item in actions:
        action = item.get("action", {}) if isinstance(item, dict) else {}
        path = resolve_run_path(run_dir, item.get("path") if isinstance(item, dict) else None)
        if (
            not isinstance(item, dict)
            or target_stage(action) != "debug_loop"
            or action.get("requires_approval") is not False
            or not isinstance(action.get("acceptance_checkers"), list)
            or not action.get("acceptance_checkers")
            or path is None
            or not path.is_file()
            or sha256_file(path) != item.get("sha256")
            or canonical_sha256(normalized_action(action)) != item.get("action_sha256")
        ):
            return ["flow-controller handoff action binding is invalid"]
    return []


def mark_stage6_flow_handoff_consumed(run_dir: Path, handoff: dict[str, Any], repair_plan_path: Path) -> Path:
    errors = validate_stage6_flow_handoff(handoff, run_dir)
    if errors:
        raise ValueError("; ".join(errors))
    path = consumption_path(run_dir)
    payload = read_json_if_exists(path)
    consumed = payload.get("consumed", {}) if isinstance(payload.get("consumed"), dict) else {}
    consumed[str(handoff["handoff_identity"])] = {
        "source_sacg_state_sha256": handoff["source_sacg_state"]["sha256"],
        "flow_controller_result_sha256": handoff["flow_controller_result"]["sha256"],
        "source_flow_event_sha256": handoff["source_flow_event"]["sha256"],
        "repair_plan_path": str(repair_plan_path),
        "repair_plan_sha256": sha256_file(repair_plan_path) if repair_plan_path.is_file() else "",
    }
    write_json(
        path,
        {
            "schema_version": CONSUMPTION_SCHEMA_VERSION,
            "consumed": consumed,
        },
    )
    return path
