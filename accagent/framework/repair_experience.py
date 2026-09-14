"""Evidence-bound repair experience shared across accelerator design runs."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EPISODE_SCHEMA_VERSION = "spatialaccagent.repair_experience_episode.v2"
LEGACY_EPISODE_SCHEMA_VERSION = "spatialaccagent.repair_experience_episode.v1"
CONTEXT_SCHEMA_VERSION = "spatialaccagent.repair_experience_context.v2"
PROJECT_KNOWLEDGE_CONTEXT_SCHEMA_VERSION = (
    "spatialaccagent.project_knowledge_context.v1"
)
HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
RETRIEVABLE_OUTCOMES = {"validated_success", "falsified"}
RETRIEVABLE_EVIDENCE_GRADES = {
    "same_layer_real_tool_pass",
    "same_layer_real_tool_fail",
    "compile_or_elaboration_fail",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def repair_experience_db_path(run_dir: Path) -> Path:
    override = str(os.environ.get("SPATIALACC_REPAIR_EXPERIENCE_DB") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (run_dir.resolve().parent / "_shared_experience" / "repair_experience.jsonl").resolve()


def _scalar(value: Any) -> str | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (str, int, float)):
        text = str(value).strip()
        return text or None
    return None


def _first_nested_value(value: Any, field: str) -> str | None:
    if isinstance(value, dict):
        direct = _scalar(value.get(field))
        if direct is not None:
            return direct
        for child in value.values():
            found = _first_nested_value(child, field)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _first_nested_value(child, field)
            if found is not None:
                return found
    return None


def _stage_role(stage_id: str | None) -> str | None:
    if not stage_id:
        return None
    match = re.fullmatch(r"stage_\d+_(.+)", stage_id.strip().lower())
    return match.group(1) if match else stage_id.strip().lower()


def _bounded_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _snapshot_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in record.get("evidence_snapshots", []):
        if not isinstance(row, dict):
            continue
        snapshot = Path(str(row.get("snapshot_path") or ""))
        expected = str(row.get("source_sha256") or "")
        if (
            not snapshot.is_file()
            or not HEX_SHA256.fullmatch(expected)
            or _sha256_file(snapshot) != expected
        ):
            continue
        rows.append(row)
    return rows


def _snapshot_for_source(
    rows: list[dict[str, Any]],
    role: str,
    source_path: Any,
) -> Path | None:
    source_text = str(source_path or "")
    candidates = [row for row in rows if row.get("role") == role]
    if source_text:
        exact = [row for row in candidates if str(row.get("source_path") or "") == source_text]
        if exact:
            candidates = exact
    if len(candidates) != 1:
        return None
    return Path(str(candidates[0]["snapshot_path"])).resolve()


def _snapshot_bindings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role": str(row.get("role") or "artifact"),
            "path": str(Path(str(row["snapshot_path"])).resolve()),
            "source_path": str(row.get("source_path") or ""),
            "sha256": str(row["source_sha256"]),
        }
        for row in rows[:24]
    ]


def _resolved_edit_path(path: Any, repo_root: Path) -> Path:
    value = Path(str(path or ""))
    return (value if value.is_absolute() else repo_root / value).resolve()


def _complete_replacement_projection(
    output: dict[str, Any],
    repo_root: Path,
) -> list[dict[str, Any]] | None:
    projection: list[dict[str, Any]] = []
    edits = output.get("file_edits", [])
    if not isinstance(edits, list) or not edits:
        return None
    for edit in edits:
        if (
            not isinstance(edit, dict)
            or edit.get("operation") not in {"create", "replace"}
            or not isinstance(edit.get("content"), str)
            or not edit.get("content")
        ):
            return None
        content = edit["content"].encode("utf-8")
        projection.append(
            {
                "path": str(_resolved_edit_path(edit.get("path"), repo_root)),
                "operation": edit.get("operation"),
                "before_sha256": str(edit.get("expected_sha256") or ""),
                "after_sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
            }
        )
    return sorted(projection, key=lambda row: row["path"])


def _applied_patch_projection(patch: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "path": str(Path(str(row.get("path") or "")).resolve()),
                "operation": row.get("operation"),
                "before_sha256": str(row.get("before_sha256") or ""),
                "after_sha256": str(row.get("after_sha256") or ""),
                "bytes": row.get("bytes"),
            }
            for row in patch.get("files", [])
            if isinstance(row, dict)
            and row.get("after_sha256")
            and row.get("after_sha256") != row.get("before_sha256")
        ],
        key=lambda row: row["path"],
    )


def _recover_unarchived_llm_rows(
    record_path: Path,
    result: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if _snapshot_for_source(rows, "llm_record", result.get("llm_record")) is not None:
        return []
    patch_snapshot = _snapshot_for_source(
        rows,
        "agent_patch_application",
        result.get("agent_patch_application"),
    )
    if patch_snapshot is None:
        return []
    patch = _read_json(patch_snapshot)
    expected_projection = _applied_patch_projection(patch)
    if patch.get("status") != "pass" or not expected_projection:
        return []
    run_dir = record_path.resolve().parents[3]
    repo_root = run_dir.parents[2]
    llm_dir = record_path.resolve().parents[2] / "llm"
    matches: list[tuple[float, Path, dict[str, Any]]] = []
    for candidate in llm_dir.glob("*_result.json"):
        try:
            value = _read_json(candidate)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        output = value.get("output", {}) if isinstance(value.get("output"), dict) else {}
        projection = _complete_replacement_projection(output, repo_root)
        if projection != expected_projection:
            continue
        matches.append((candidate.stat().st_mtime, candidate.resolve(), value))
    if len(matches) != 1:
        return []
    _, source, value = matches[0]
    snapshot = record_path.parent / f"recovered_{source.name}"
    source_sha256 = _sha256_file(source)
    if snapshot.exists() and _sha256_file(snapshot) != source_sha256:
        return []
    if not snapshot.exists():
        shutil.copy2(source, snapshot)
    recovered = [
        {
            "role": "llm_record",
            "source_path": str(source),
            "source_sha256": source_sha256,
            "snapshot_path": str(snapshot.resolve()),
            "recovery": "exact_complete_file_edit_projection_match",
        }
    ]
    request_path = Path(str(value.get("request_path") or ""))
    prompt_hash = str(value.get("prompt_hash") or "")
    if (
        request_path.is_file()
        and HEX_SHA256.fullmatch(prompt_hash)
        and _sha256_file(request_path) == prompt_hash
    ):
        prompt_snapshot = record_path.parent / f"recovered_{request_path.name}"
        if prompt_snapshot.exists() and _sha256_file(prompt_snapshot) != prompt_hash:
            return recovered
        if not prompt_snapshot.exists():
            shutil.copy2(request_path, prompt_snapshot)
        recovered.append(
            {
                "role": "request_path",
                "source_path": str(request_path.resolve()),
                "source_sha256": prompt_hash,
                "snapshot_path": str(prompt_snapshot.resolve()),
                "recovery": "llm_record_bound_prompt_hash",
            }
        )
    return recovered


def _context_failure_sources(context: dict[str, Any]) -> list[Any]:
    values = []
    for key in (
        "current_single_layer_real_tool_failure",
        "current_single_layer_pipeline_trace_record",
        "current_board_vcs_feedback",
        "current_board_preflight_feedback",
        "capability_probe",
        "failed_current_layer_gates",
    ):
        if key in context:
            values.append(context[key])
    values.append(context)
    return values


def _first_from_sources(sources: list[Any], field: str) -> str | None:
    for source in sources:
        value = _first_nested_value(source, field)
        if value is not None:
            return value
    return None


def _bounded_string_list(value: Any, *, limit: int, item_limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _bounded_text(item, item_limit)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _evidence_ref_is_bound(ref: str, rows: list[dict[str, Any]]) -> bool:
    base = ref.split("#", 1)[0].strip()
    if not base:
        return False
    for row in rows:
        source = str(row.get("source_path") or "")
        snapshot = str(row.get("snapshot_path") or "")
        if base in {source, snapshot}:
            return True
        try:
            if Path(base).name and Path(base).name in {
                Path(source).name,
                Path(snapshot).name,
            }:
                return True
        except (OSError, ValueError):
            continue
    return False


def _project_knowledge_updates(
    output: dict[str, Any],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for value in output.get("project_knowledge_updates", []):
        if not isinstance(value, dict):
            continue
        kind = str(value.get("knowledge_kind") or "").strip()
        claim = _bounded_text(value.get("claim"), 5000)
        evidence_refs = _bounded_string_list(
            value.get("evidence_refs"), limit=12, item_limit=1000
        )
        if (
            kind not in _PROJECT_KNOWLEDGE_KINDS
            or not claim
            or not evidence_refs
            or not any(_evidence_ref_is_bound(ref, rows) for ref in evidence_refs)
        ):
            continue
        confidence = str(value.get("confidence") or "").strip().lower()
        if confidence not in _PROJECT_KNOWLEDGE_CONFIDENCE:
            confidence = "medium"
        validity_scope = str(value.get("validity_scope") or "").strip()
        if validity_scope not in {
            "current_source_fingerprint",
            "current_contract",
            "architecture_invariant",
        }:
            validity_scope = "current_source_fingerprint"
        updates.append(
            {
                "knowledge_kind": kind,
                "subject_ids": _bounded_string_list(
                    value.get("subject_ids"), limit=16, item_limit=300
                ),
                "claim": claim,
                "timing_observations": _bounded_string_list(
                    value.get("timing_observations"), limit=16, item_limit=1000
                ),
                "validity_scope": validity_scope,
                "validity_conditions": _bounded_string_list(
                    value.get("validity_conditions"), limit=12, item_limit=1000
                ),
                "evidence_refs": evidence_refs,
                "confidence": confidence,
                "reuse_guidance": _bounded_text(value.get("reuse_guidance"), 2000),
                "supersedes_knowledge_ids": _bounded_string_list(
                    value.get("supersedes_knowledge_ids"), limit=12, item_limit=160
                ),
                "contradicts_knowledge_ids": _bounded_string_list(
                    value.get("contradicts_knowledge_ids"), limit=12, item_limit=160
                ),
            }
        )
        if len(updates) >= 12:
            break
    return updates


def build_repair_experience_query(package: dict[str, Any]) -> dict[str, Any]:
    sources = _context_failure_sources(package)
    stage_id = _scalar(package.get("stage_id")) or _first_from_sources(sources, "stage_id")
    target_modules = sorted(
        {
            str(value)
            for value in package.get("target_modules", [])
            if isinstance(value, (str, int)) and str(value)
        }
    )
    query = {
        "verification_scope": _scalar(package.get("verification_scope")),
        "debug_layer": _scalar(package.get("debug_layer")),
        "repair_scope": _scalar(package.get("repair_scope")),
        "repair_kind": _scalar(package.get("repair_kind")),
        "repair_gate": _scalar(package.get("repair_gate")),
        "violated_contract": _scalar(package.get("violated_contract"))
        or _first_from_sources(sources, "violated_contract"),
        "stage_id": stage_id,
        "stage_role": _stage_role(stage_id),
        "module_role": target_modules[0] if len(target_modules) == 1 else None,
        "failure_class": _first_from_sources(sources, "failure_class"),
        "proof_mode": _first_from_sources(sources, "proof_mode"),
        "frontier_id": _first_from_sources(sources, "frontier_id"),
        "frontier_type": _first_from_sources(sources, "frontier_type"),
    }
    return {key: value for key, value in query.items() if value is not None}


def _file_change_projection(row: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(row.get("path") or ""))
    return {
        "path_basename": path.name,
        "suffix": path.suffix.lower(),
        "operation": row.get("operation"),
        "before_sha256": row.get("before_sha256"),
        "after_sha256": row.get("after_sha256"),
        "bytes": row.get("bytes"),
    }


def _capability_report_values(
    result: dict[str, Any],
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    values: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    for report in result.get("capability_reports", []):
        if not isinstance(report, dict) or not report.get("path"):
            continue
        snapshot = _snapshot_for_source(rows, "capability_report", report.get("path"))
        if snapshot is None:
            continue
        values.append(_read_json(snapshot))
        bindings.append(
            {
                "path": str(snapshot),
                "sha256": _sha256_file(snapshot),
                "schema_version": report.get("schema_version"),
                "status": report.get("status"),
            }
        )
    return values, bindings


def _episode_identity_projection(episode: dict[str, Any]) -> dict[str, Any]:
    intervention = episode.get("intervention", {})
    outcome = episode.get("outcome", {})
    schema_version = str(episode.get("schema_version") or EPISODE_SCHEMA_VERSION)
    projection = {
        "schema_version": schema_version,
        "key": episode.get("key", {}),
        "intervention": {
            "agent": intervention.get("agent"),
            "prompt_hash": intervention.get("prompt_hash"),
            "file_changes": intervention.get("file_changes", []),
        },
        "outcome": {
            "status": outcome.get("status"),
            "evidence_grade": outcome.get("evidence_grade"),
            "post_input_fingerprint_sha256": outcome.get(
                "post_input_fingerprint_sha256"
            ),
            "post_failure_class": outcome.get("post_failure_class"),
        },
    }
    if schema_version == EPISODE_SCHEMA_VERSION:
        projection["intervention"].update(
            {
                "summary": intervention.get("summary"),
                "root_cause": intervention.get("root_cause"),
                "project_knowledge_updates": intervention.get(
                    "project_knowledge_updates", []
                ),
            }
        )
    return projection


def _build_episode(
    *,
    record_path: Path,
    record: dict[str, Any],
    step: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    result = step.get("result", {}) if isinstance(step.get("result"), dict) else {}
    llm_snapshot = _snapshot_for_source(rows, "llm_record", result.get("llm_record"))
    patch_snapshot = _snapshot_for_source(
        rows,
        "agent_patch_application",
        result.get("agent_patch_application"),
    )
    if llm_snapshot is None or patch_snapshot is None:
        return None
    llm_record = _read_json(llm_snapshot)
    patch = _read_json(patch_snapshot)
    changed_files = [
        row
        for row in patch.get("files", [])
        if isinstance(row, dict)
        and row.get("after_sha256")
        and row.get("after_sha256") != row.get("before_sha256")
    ]
    if patch.get("status") != "pass" or not changed_files:
        return None

    context_snapshot = _snapshot_for_source(rows, "context_package", result.get("context_package"))
    context = _read_json(context_snapshot) if context_snapshot is not None else {}
    checkpoint = patch.get("repair_checkpoint", {})
    if not isinstance(checkpoint, dict):
        checkpoint = {}
    context_sources = _context_failure_sources(context)
    stage_id = _scalar(checkpoint.get("stage_id")) or _scalar(context.get("stage_id"))
    target_modules = [str(value) for value in result.get("target_modules", []) if str(value)]
    module_role = (
        _scalar(checkpoint.get("module"))
        or (target_modules[0] if len(target_modules) == 1 else None)
    )
    key = {
        "verification_scope": _scalar(context.get("verification_scope")),
        "debug_layer": _scalar(context.get("debug_layer")),
        "repair_scope": _scalar(step.get("scope")),
        "repair_kind": _scalar(checkpoint.get("repair_kind"))
        or _scalar(context.get("repair_kind")),
        "repair_gate": _scalar(context.get("repair_gate")),
        "violated_contract": _scalar(checkpoint.get("violated_contract"))
        or _first_from_sources(context_sources, "violated_contract"),
        "stage_id": stage_id,
        "stage_role": _stage_role(stage_id),
        "module_role": module_role,
        "failure_class": _first_from_sources(context_sources, "failure_class"),
        "proof_mode": _first_from_sources(context_sources, "proof_mode"),
        "frontier_id": _first_from_sources(context_sources, "frontier_id"),
        "frontier_type": _first_from_sources(context_sources, "frontier_type"),
    }
    key = {name: value for name, value in key.items() if value is not None}

    validation_snapshot = _snapshot_for_source(
        rows,
        "agent_requested_validation",
        result.get("agent_requested_validation"),
    )
    validation = _read_json(validation_snapshot) if validation_snapshot is not None else {}
    capability_values, capability_bindings = _capability_report_values(result, rows)
    result_status = str(result.get("status") or "")
    stage_passed = result.get("stage_passed") is True
    any_capability_pass = any(
        str(value.get("status") or "") in {"pass", "ready"}
        for value in capability_values
    )
    any_capability_fail = any(
        str(value.get("status") or "") in {"fail", "failed", "incomplete"}
        for value in capability_values
    )
    if stage_passed and result_status == "pass" and any_capability_pass:
        outcome_status = "validated_success"
        evidence_grade = "same_layer_real_tool_pass"
    elif result_status in {"fail", "blocked"} and capability_values and (
        any_capability_fail or not stage_passed
    ):
        outcome_status = "falsified"
        evidence_grade = "same_layer_real_tool_fail"
    elif str(validation.get("status") or "") == "fail":
        outcome_status = "falsified"
        evidence_grade = "compile_or_elaboration_fail"
    else:
        outcome_status = "inconclusive"
        evidence_grade = "insufficient_post_intervention_evidence"

    output = llm_record.get("output", {})
    if not isinstance(output, dict):
        output = {}
    project_knowledge_updates = _project_knowledge_updates(output, rows)
    post_sources: list[Any] = [*capability_values, result]
    episode = {
        "schema_version": EPISODE_SCHEMA_VERSION,
        "recorded_at": _utc_now(),
        "key": key,
        "observation": {
            "summary": _bounded_text(
                _first_from_sources(context_sources, "summary") or result.get("summary"),
                3000,
            ),
            "input_fingerprint_sha256": _first_from_sources(
                context_sources, "input_fingerprint_sha256"
            ),
            "contract_sha256": _first_from_sources(context_sources, "contract_sha256"),
            "trace_sha256": _first_from_sources(context_sources, "pipeline_trace_sha256"),
        },
        "intervention": {
            "agent": llm_record.get("agent"),
            "model": llm_record.get("model"),
            "prompt_hash": llm_record.get("prompt_hash"),
            "summary": _bounded_text(output.get("summary"), 3000),
            "root_cause": _bounded_text(output.get("root_cause"), 5000),
            "project_knowledge_updates": project_knowledge_updates,
            "file_changes": [_file_change_projection(row) for row in changed_files[:12]],
            "repair_checkpoint": copy.deepcopy(checkpoint),
        },
        "outcome": {
            "status": outcome_status,
            "evidence_grade": evidence_grade,
            "stage_passed": stage_passed,
            "step_status": result_status,
            "summary": _bounded_text(result.get("summary"), 3000),
            "post_input_fingerprint_sha256": _first_from_sources(
                post_sources, "input_fingerprint_sha256"
            ),
            "post_failure_class": _first_from_sources(post_sources, "failure_class"),
            "capability_reports": capability_bindings,
            "agent_requested_validation": (
                {
                    "path": str(validation_snapshot),
                    "sha256": _sha256_file(validation_snapshot),
                    "status": validation.get("status"),
                }
                if validation_snapshot is not None
                else None
            ),
        },
        "provenance": {
            "design_id": _scalar(
                record.get("repair_execution_report", {}).get("design_id")
            ),
            "project_id": record_path.resolve().parents[3].name,
            "run_dir": str(record_path.resolve().parents[3]),
            "iteration": record.get("iteration"),
            "iteration_record": str(record_path.resolve()),
        },
        "evidence_bindings": _snapshot_bindings(rows),
        "transfer_policy": {
            "use_as_hypothesis_prior_only": True,
            "rebind_current_sources_and_contracts": True,
            "same_layer_real_tool_revalidation_required": True,
            "never_authorizes_file_edits_or_promotion": True,
        },
    }
    identity = _canonical_sha256(_episode_identity_projection(episode))
    episode["experience_id"] = f"repair_experience.{identity}"
    return episode


def _intervention_signature(episode: dict[str, Any]) -> str:
    intervention = (
        episode.get("intervention", {})
        if isinstance(episode.get("intervention"), dict)
        else {}
    )
    key = episode.get("key", {}) if isinstance(episode.get("key"), dict) else {}
    return _canonical_sha256(
        {
            "verification_scope": key.get("verification_scope"),
            "debug_layer": key.get("debug_layer"),
            "repair_gate": key.get("repair_gate"),
            "agent": intervention.get("agent"),
            "prompt_hash": intervention.get("prompt_hash"),
            "file_changes": intervention.get("file_changes", []),
            "repair_checkpoint": intervention.get("repair_checkpoint", {}),
        }
    )


def _effective_repair_experiences(path: Path) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for episode in load_repair_experiences(path):
        signature = _intervention_signature(episode)
        prior = latest.get(signature)
        if prior is None or str(episode.get("recorded_at") or "") >= str(
            prior.get("recorded_at") or ""
        ):
            latest[signature] = episode
    return list(latest.values())


def _deferred_validation_episode(
    *,
    record_path: Path,
    record: dict[str, Any],
    step: dict[str, Any],
    rows: list[dict[str, Any]],
    prior_episodes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    result = step.get("result", {}) if isinstance(step.get("result"), dict) else {}
    patch_snapshot = _snapshot_for_source(
        rows,
        "agent_patch_application",
        result.get("agent_patch_application"),
    )
    if patch_snapshot is None:
        return None
    patch = _read_json(patch_snapshot)
    changed_files = [
        row
        for row in patch.get("files", [])
        if isinstance(row, dict)
        and row.get("after_sha256")
        and row.get("after_sha256") != row.get("before_sha256")
    ]
    projected_changes = [_file_change_projection(row) for row in changed_files[:12]]
    checkpoint = patch.get("repair_checkpoint", {})
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    if patch.get("status") != "pass" or not projected_changes:
        return None

    candidates: list[dict[str, Any]] = []
    current_project = record_path.resolve().parents[3].name
    checkpoint_fields = (
        "repair_kind",
        "stage_id",
        "module",
        "violated_contract",
        "source_bound_failure_identity_sha256",
    )
    for episode in prior_episodes:
        intervention = (
            episode.get("intervention", {})
            if isinstance(episode.get("intervention"), dict)
            else {}
        )
        provenance = (
            episode.get("provenance", {})
            if isinstance(episode.get("provenance"), dict)
            else {}
        )
        episode_project = str(
            provenance.get("project_id")
            or Path(str(provenance.get("run_dir") or ".")).name
        )
        prior_checkpoint = intervention.get("repair_checkpoint", {})
        prior_checkpoint = prior_checkpoint if isinstance(prior_checkpoint, dict) else {}
        if (
            episode_project != current_project
            or intervention.get("file_changes") != projected_changes
            or any(
                checkpoint.get(field) != prior_checkpoint.get(field)
                for field in checkpoint_fields
                if checkpoint.get(field) is not None
                or prior_checkpoint.get(field) is not None
            )
        ):
            continue
        candidates.append(episode)
    if not candidates:
        return None
    source_episode = max(
        candidates,
        key=lambda value: str(value.get("recorded_at") or ""),
    )

    capability_values, capability_bindings = _capability_report_values(result, rows)
    result_status = str(result.get("status") or "")
    stage_passed = result.get("stage_passed") is True
    any_capability_pass = any(
        str(value.get("status") or "") in {"pass", "ready"}
        for value in capability_values
    )
    any_capability_fail = any(
        str(value.get("status") or "") in {"fail", "failed", "incomplete"}
        for value in capability_values
    )
    if stage_passed and result_status == "pass" and any_capability_pass:
        outcome_status = "validated_success"
        evidence_grade = "same_layer_real_tool_pass"
    elif result_status in {"fail", "blocked"} and capability_values and (
        any_capability_fail or not stage_passed
    ):
        outcome_status = "falsified"
        evidence_grade = "same_layer_real_tool_fail"
    else:
        return None

    validation_snapshot = _snapshot_for_source(
        rows,
        "agent_requested_validation",
        result.get("agent_requested_validation"),
    )
    validation = _read_json(validation_snapshot) if validation_snapshot is not None else {}
    episode = copy.deepcopy(source_episode)
    episode["schema_version"] = EPISODE_SCHEMA_VERSION
    episode["recorded_at"] = _utc_now()
    episode["outcome"] = {
        "status": outcome_status,
        "evidence_grade": evidence_grade,
        "stage_passed": stage_passed,
        "step_status": result_status,
        "summary": _bounded_text(result.get("summary"), 3000),
        "post_input_fingerprint_sha256": _first_from_sources(
            [*capability_values, result], "input_fingerprint_sha256"
        ),
        "post_failure_class": _first_from_sources(
            [*capability_values, result], "failure_class"
        ),
        "capability_reports": capability_bindings,
        "agent_requested_validation": (
            {
                "path": str(validation_snapshot),
                "sha256": _sha256_file(validation_snapshot),
                "status": validation.get("status"),
            }
            if validation_snapshot is not None
            else None
        ),
        "deferred_real_tool_attribution": {
            "source_intervention_experience_id": source_episode.get(
                "experience_id"
            ),
            "source_intervention_iteration": source_episode.get(
                "provenance", {}
            ).get("iteration"),
            "validation_iteration": record.get("iteration"),
            "exact_patch_and_checkpoint_match": True,
        },
    }
    episode["provenance"] = {
        **copy.deepcopy(source_episode.get("provenance", {})),
        "project_id": current_project,
        "run_dir": str(record_path.resolve().parents[3]),
        "iteration": record.get("iteration"),
        "iteration_record": str(record_path.resolve()),
        "source_intervention_experience_id": source_episode.get("experience_id"),
    }
    combined_bindings: list[dict[str, Any]] = []
    seen_bindings: set[tuple[str, str]] = set()
    for binding in [
        *source_episode.get("evidence_bindings", []),
        *_snapshot_bindings(rows),
    ]:
        if not isinstance(binding, dict):
            continue
        identity = (str(binding.get("path") or ""), str(binding.get("sha256") or ""))
        if not all(identity) or identity in seen_bindings:
            continue
        seen_bindings.add(identity)
        combined_bindings.append(copy.deepcopy(binding))
        if len(combined_bindings) >= 24:
            break
    episode["evidence_bindings"] = combined_bindings
    episode.setdefault("transfer_policy", {})[
        "deferred_real_tool_outcome_is_attributed_only_by_exact_patch_and_checkpoint"
    ] = True
    identity = _canonical_sha256(_episode_identity_projection(episode))
    episode["experience_id"] = f"repair_experience.{identity}"
    return episode


def _valid_episode(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("schema_version") not in {
        EPISODE_SCHEMA_VERSION,
        LEGACY_EPISODE_SCHEMA_VERSION,
    }:
        return False
    experience_id = str(value.get("experience_id") or "")
    if not re.fullmatch(r"repair_experience\.[0-9a-f]{64}", experience_id):
        return False
    return experience_id.split(".", 1)[1] == _canonical_sha256(
        _episode_identity_projection(value)
    )


def load_repair_experiences(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _valid_episode(value):
                records.append(value)
    return records


def _append_episode(path: Path, episode: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        existing = set()
        for line in handle:
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if _valid_episode(value):
                existing.add(value.get("experience_id"))
        if episode["experience_id"] in existing:
            return False
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(episode, sort_keys=True, ensure_ascii=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        return True


def record_repair_iteration_experience(
    record_path: Path,
    *,
    run_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    record_path = record_path.resolve()
    record = _read_json(record_path)
    resolved_run_dir = run_dir.resolve() if run_dir is not None else record_path.parents[3]
    resolved_db = db_path.resolve() if db_path is not None else repair_experience_db_path(resolved_run_dir)
    rows = _snapshot_rows(record)
    prior_episodes = load_repair_experiences(resolved_db)
    recorded = 0
    duplicates = 0
    episode_ids: list[str] = []
    for step in record.get("repair_execution_report", {}).get("step_results", []):
        if not isinstance(step, dict):
            continue
        result = step.get("result", {}) if isinstance(step.get("result"), dict) else {}
        recovered_rows = _recover_unarchived_llm_rows(
            record_path,
            result,
            rows,
        )
        step_rows = [*rows, *recovered_rows]
        episode = _build_episode(
            record_path=record_path,
            record=record,
            step=step,
            rows=step_rows,
        )
        if episode is None:
            episode = _deferred_validation_episode(
                record_path=record_path,
                record=record,
                step=step,
                rows=step_rows,
                prior_episodes=prior_episodes,
            )
        if episode is None:
            continue
        if recovered_rows:
            episode.setdefault("provenance", {})[
                "llm_record_recovery"
            ] = {
                "status": "pass",
                "method": "exact_complete_file_edit_projection_match",
                "snapshot_paths": [
                    str(row.get("snapshot_path")) for row in recovered_rows
                ],
            }
            identity = _canonical_sha256(_episode_identity_projection(episode))
            episode["experience_id"] = f"repair_experience.{identity}"
        episode_ids.append(str(episode["experience_id"]))
        if _append_episode(resolved_db, episode):
            recorded += 1
            prior_episodes.append(episode)
        else:
            duplicates += 1
    return {
        "schema_version": "spatialaccagent.repair_experience_ingest.v1",
        "status": "pass",
        "database_path": str(resolved_db),
        "recorded": recorded,
        "duplicates": duplicates,
        "experience_ids": episode_ids,
    }


def sync_recent_repair_experience(
    run_dir: Path,
    *,
    limit: int = 32,
) -> dict[str, Any]:
    paths = sorted(
        (run_dir / "repair_execution" / "loop").glob("iteration_*/iteration_record.json")
    )[-max(1, limit) :]
    recorded = 0
    duplicates = 0
    errors: list[str] = []
    for path in paths:
        try:
            result = record_repair_iteration_experience(path, run_dir=run_dir)
            recorded += int(result.get("recorded") or 0)
            duplicates += int(result.get("duplicates") or 0)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
    return {
        "schema_version": "spatialaccagent.repair_experience_sync.v1",
        "status": "pass" if not errors else "partial",
        "database_path": str(repair_experience_db_path(run_dir)),
        "scanned_iteration_count": len(paths),
        "recorded": recorded,
        "duplicates": duplicates,
        "errors": errors[:8],
    }


_MATCH_WEIGHTS = {
    "failure_class": 12,
    "violated_contract": 12,
    "stage_role": 8,
    "proof_mode": 6,
    "frontier_type": 6,
    "frontier_id": 5,
    "repair_gate": 5,
    "verification_scope": 4,
    "repair_kind": 3,
    "debug_layer": 2,
    "module_role": 1,
}
_SEMANTIC_MATCH_FIELDS = {
    "failure_class",
    "violated_contract",
    "stage_role",
    "proof_mode",
    "frontier_type",
}

_PROJECT_KNOWLEDGE_KINDS = {
    "operator_semantics",
    "ready_valid_protocol",
    "state_machine",
    "timing_relationship",
    "buffering_backpressure",
    "memory_mapping",
    "board_lifecycle",
    "negative_hypothesis",
    "causal_mechanism",
}

_PROJECT_KNOWLEDGE_CONFIDENCE = {"high", "medium", "low"}


def retrieve_repair_experience(
    run_dir: Path,
    query: dict[str, Any],
    *,
    limit: int = 6,
) -> dict[str, Any]:
    path = repair_experience_db_path(run_dir)
    candidates = []
    for episode in _effective_repair_experiences(path):
        outcome = episode.get("outcome", {})
        if (
            outcome.get("status") not in RETRIEVABLE_OUTCOMES
            or outcome.get("evidence_grade") not in RETRIEVABLE_EVIDENCE_GRADES
        ):
            continue
        key = episode.get("key", {}) if isinstance(episode.get("key"), dict) else {}
        matches = []
        score = 0
        for field, weight in _MATCH_WEIGHTS.items():
            if query.get(field) is not None and key.get(field) == query.get(field):
                matches.append(field)
                score += weight
        if not _SEMANTIC_MATCH_FIELDS.intersection(matches):
            continue
        candidates.append((score, str(episode.get("recorded_at") or ""), episode, matches))
    candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
    selected = []
    for score, _, episode, matches in candidates[: max(1, limit)]:
        selected.append(
            {
                "experience_id": episode["experience_id"],
                "outcome": copy.deepcopy(episode.get("outcome", {})),
                "similarity": {"score": score, "exact_match_fields": matches},
                "key": copy.deepcopy(episode.get("key", {})),
                "observation": copy.deepcopy(episode.get("observation", {})),
                "intervention": copy.deepcopy(episode.get("intervention", {})),
                "evidence_bindings": copy.deepcopy(episode.get("evidence_bindings", []))[:12],
                "transfer_policy": copy.deepcopy(episode.get("transfer_policy", {})),
            }
        )
    return {
        "schema_version": CONTEXT_SCHEMA_VERSION,
        "status": "ready" if selected else "empty",
        "query": copy.deepcopy(query),
        "database_path": str(path),
        "database_sha256": _sha256_file(path) if path.is_file() else None,
        "selected_count": len(selected),
        "episodes": selected,
        "policy": {
            "validated_success_is_a_hypothesis_prior_not_a_pass": True,
            "falsified_interventions_must_not_be_repeated_without_new_distinguishing_evidence": True,
            "current_source_contract_and_real_tool_evidence_take_precedence": True,
            "current_same_layer_real_tool_revalidation_is_mandatory": True,
            "experience_never_expands_edit_authority": True,
        },
    }


def _nested_values(value: Any, field: str) -> list[Any]:
    values: list[Any] = []
    if isinstance(value, dict):
        if field in value:
            values.append(value[field])
        for child in value.values():
            values.extend(_nested_values(child, field))
    elif isinstance(value, list):
        for child in value:
            values.extend(_nested_values(child, field))
    return values


def _nested_sha256_values(value: Any, field_suffix: str) -> list[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).endswith(field_suffix) and HEX_SHA256.fullmatch(str(child or "")):
                values.add(str(child))
            values.update(_nested_sha256_values(child, field_suffix))
    elif isinstance(value, list):
        for child in value:
            values.update(_nested_sha256_values(child, field_suffix))
    return sorted(values)


def build_project_knowledge_query(package: dict[str, Any]) -> dict[str, Any]:
    query = build_repair_experience_query(package)
    run_dir = str(package.get("run_dir") or "").strip()
    project_id = Path(run_dir).name if run_dir else None
    subject_ids: set[str] = set()
    for field in ("stage_id", "boundary_id", "frontier_id"):
        for value in _nested_values(package, field):
            scalar = _scalar(value)
            if scalar:
                subject_ids.add(scalar)
    for field in ("candidate_stage_ids", "target_modules"):
        for values in _nested_values(package, field):
            if isinstance(values, list):
                subject_ids.update(str(value) for value in values if str(value))
    query.update(
        {
            "project_id": project_id,
            "subject_ids": sorted(subject_ids)[:64],
            "current_input_fingerprint_sha256s": _nested_sha256_values(
                package, "input_fingerprint_sha256"
            )[:32],
            "current_contract_sha256s": _nested_sha256_values(
                package, "contract_sha256"
            )[:32],
        }
    )
    return {key: value for key, value in query.items() if value not in (None, [], {})}


def _fallback_project_knowledge_update(episode: dict[str, Any]) -> dict[str, Any] | None:
    intervention = (
        episode.get("intervention", {})
        if isinstance(episode.get("intervention"), dict)
        else {}
    )
    claim = _bounded_text(intervention.get("root_cause"), 5000)
    if not claim:
        return None
    key = episode.get("key", {}) if isinstance(episode.get("key"), dict) else {}
    subject_ids = [
        str(key[field])
        for field in ("stage_id", "module_role", "frontier_id")
        if key.get(field)
    ]
    refs = [
        str(row.get("path"))
        for row in episode.get("evidence_bindings", [])
        if isinstance(row, dict) and row.get("path")
    ][:12]
    return {
        "knowledge_kind": "causal_mechanism",
        "subject_ids": subject_ids,
        "claim": claim,
        "timing_observations": [],
        "validity_scope": "current_source_fingerprint",
        "validity_conditions": [
            "The recorded source, contract, workload, and real-tool evidence identity remain applicable."
        ],
        "evidence_refs": refs,
        "confidence": "high" if episode.get("outcome", {}).get("status") == "validated_success" else "medium",
        "reuse_guidance": _bounded_text(intervention.get("summary"), 2000),
        "supersedes_knowledge_ids": [],
        "contradicts_knowledge_ids": [],
    }


def _project_knowledge_updates_from_episode(
    episode: dict[str, Any],
) -> list[dict[str, Any]]:
    intervention = (
        episode.get("intervention", {})
        if isinstance(episode.get("intervention"), dict)
        else {}
    )
    updates = [
        copy.deepcopy(value)
        for value in intervention.get("project_knowledge_updates", [])
        if isinstance(value, dict)
    ]
    if updates:
        return updates[:12]
    fallback = _fallback_project_knowledge_update(episode)
    return [fallback] if fallback is not None else []


def _project_knowledge_epistemic_status(episode: dict[str, Any]) -> str:
    outcome = episode.get("outcome", {}) if isinstance(episode.get("outcome"), dict) else {}
    grade = str(outcome.get("evidence_grade") or "")
    if outcome.get("status") == "validated_success" and grade == "same_layer_real_tool_pass":
        return "validated_for_recorded_source"
    if grade == "same_layer_real_tool_fail":
        return "falsified_or_causally_insufficient"
    if grade == "compile_or_elaboration_fail":
        return "implementation_invalid_causal_claim_unresolved"
    return "unresolved_hypothesis"


def retrieve_project_knowledge(
    run_dir: Path,
    query: dict[str, Any],
    *,
    limit: int = 8,
    exclude_experience_ids: set[str] | None = None,
) -> dict[str, Any]:
    path = repair_experience_db_path(run_dir)
    excluded = exclude_experience_ids or set()
    query_project = str(query.get("project_id") or run_dir.resolve().name)
    query_subjects = {str(value) for value in query.get("subject_ids", []) if str(value)}
    query_fingerprints = {
        str(value)
        for value in query.get("current_input_fingerprint_sha256s", [])
        if HEX_SHA256.fullmatch(str(value))
    }
    query_contracts = {
        str(value)
        for value in query.get("current_contract_sha256s", [])
        if HEX_SHA256.fullmatch(str(value))
    }
    candidates: list[tuple[int, str, dict[str, Any]]] = []
    for episode in _effective_repair_experiences(path):
        if str(episode.get("experience_id") or "") in excluded:
            continue
        outcome = episode.get("outcome", {}) if isinstance(episode.get("outcome"), dict) else {}
        if (
            outcome.get("status") not in RETRIEVABLE_OUTCOMES
            or outcome.get("evidence_grade") not in RETRIEVABLE_EVIDENCE_GRADES
        ):
            continue
        key = episode.get("key", {}) if isinstance(episode.get("key"), dict) else {}
        provenance = (
            episode.get("provenance", {})
            if isinstance(episode.get("provenance"), dict)
            else {}
        )
        episode_project = str(
            provenance.get("project_id")
            or Path(str(provenance.get("run_dir") or ".")).name
        )
        exact_matches = []
        score = 0
        for field, weight in _MATCH_WEIGHTS.items():
            if query.get(field) is not None and key.get(field) == query.get(field):
                exact_matches.append(field)
                score += weight
        same_project = episode_project == query_project
        if same_project:
            score += 24
            exact_matches.append("project_id")
        elif not _SEMANTIC_MATCH_FIELDS.intersection(exact_matches):
            continue
        observation = (
            episode.get("observation", {})
            if isinstance(episode.get("observation"), dict)
            else {}
        )
        recorded_fingerprints = {
            str(observation.get("input_fingerprint_sha256") or ""),
            str(outcome.get("post_input_fingerprint_sha256") or ""),
        } - {""}
        exact_source = bool(recorded_fingerprints & query_fingerprints)
        exact_contract = bool(
            str(observation.get("contract_sha256") or "") in query_contracts
        )
        if exact_source:
            score += 32
            exact_matches.append("input_fingerprint_sha256")
        if exact_contract:
            score += 16
            exact_matches.append("contract_sha256")
        for index, update in enumerate(_project_knowledge_updates_from_episode(episode)):
            subjects = {
                str(value) for value in update.get("subject_ids", []) if str(value)
            }
            overlap = sorted(subjects & query_subjects)
            update_score = score + min(20, 5 * len(overlap))
            knowledge_projection = {
                "source_experience_id": episode.get("experience_id"),
                "update_index": index,
                "update": update,
            }
            knowledge_id = "project_knowledge." + _canonical_sha256(knowledge_projection)
            applicability = (
                "exact_current_source"
                if exact_source
                else "exact_current_contract"
                if exact_contract
                else "same_project_source_rebind_required"
                if same_project
                else "cross_project_hypothesis_only"
            )
            candidates.append(
                (
                    update_score,
                    str(episode.get("recorded_at") or ""),
                    {
                        "knowledge_id": knowledge_id,
                        "source_experience_id": episode.get("experience_id"),
                        "recorded_at": episode.get("recorded_at"),
                        "project_id": episode_project,
                        "epistemic_status": _project_knowledge_epistemic_status(episode),
                        "applicability": applicability,
                        "lifecycle_status": "active",
                        "similarity": {
                            "score": update_score,
                            "exact_match_fields": sorted(set(exact_matches)),
                            "subject_overlap": overlap,
                        },
                        "key": copy.deepcopy(key),
                        "knowledge": copy.deepcopy(update),
                        "recorded_identity": {
                            "input_fingerprint_sha256": observation.get(
                                "input_fingerprint_sha256"
                            ),
                            "post_input_fingerprint_sha256": outcome.get(
                                "post_input_fingerprint_sha256"
                            ),
                            "contract_sha256": observation.get("contract_sha256"),
                            "trace_sha256": observation.get("trace_sha256"),
                        },
                        "outcome": {
                            key: copy.deepcopy(outcome.get(key))
                            for key in (
                                "status",
                                "evidence_grade",
                                "post_failure_class",
                            )
                        },
                        "evidence_bindings": copy.deepcopy(
                            episode.get("evidence_bindings", [])
                        )[:12],
                    },
                )
            )
    candidates.sort(key=lambda row: (row[0], row[1]), reverse=True)
    selected = [row for _, _, row in candidates[: max(1, limit)]]
    superseded = {
        str(value)
        for row in selected
        for value in row.get("knowledge", {}).get("supersedes_knowledge_ids", [])
    }
    contradicted = {
        str(value)
        for row in selected
        for value in row.get("knowledge", {}).get("contradicts_knowledge_ids", [])
    }
    for row in selected:
        if row["knowledge_id"] in superseded:
            row["lifecycle_status"] = "superseded"
        elif row["knowledge_id"] in contradicted:
            row["lifecycle_status"] = "challenged_by_later_evidence"
    return {
        "schema_version": PROJECT_KNOWLEDGE_CONTEXT_SCHEMA_VERSION,
        "status": "ready" if selected else "empty",
        "query": copy.deepcopy(query),
        "database_path": str(path),
        "database_sha256": _sha256_file(path) if path.is_file() else None,
        "selected_count": len(selected),
        "knowledge": selected,
        "policy": {
            "knowledge_is_llm_interpretation_bound_to_real_tool_evidence": True,
            "current_source_contract_and_real_tool_evidence_take_precedence": True,
            "source_or_contract_change_requires_explicit_rebinding": True,
            "validated_knowledge_never_substitutes_for_higher_layer_validation": True,
            "falsified_or_challenged_claims_are_negative_evidence": True,
            "knowledge_never_expands_edit_authority_or_promotion": True,
        },
    }
