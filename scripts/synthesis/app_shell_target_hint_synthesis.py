#!/usr/bin/env python3
"""Use an LLM design-team role to approve or defer app-shell target hints.

The tool does not discover targets itself and does not contain project/model
keywords. It consumes user-material evidence plus real Vivado target-discovery
evidence, asks the LLM for a bounded decision, and updates the app-shell
contract only when the decision is evidence-cited and machine-checkable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.llm_config import resolved_llm_cfg
from accagent.framework.llm_io import build_prompt, parse_json_object, repair_prompt, validate_schema
from accagent.framework.stage_llm import call_llm_with_retry, llm_timeout_sec


SYSTEM = """You are the SpatialAccAgent app-shell target-selection engineer.

You are part of an AI chip design team for automatic FPGA spatial accelerator
design. Your job is to interpret user-supplied board/app-shell materials and
real Vivado evidence, then either approve a bounded app-shell integration
target update or explicitly defer. You must not use fixed project, board, or
model keywords as semantic understanding. Candidate names are evidence from
Vivado, not proof of user intent by themselves.
"""


DECISION_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "status": {"type": "string"},
        "decision": {"type": "string"},
        "confidence": {"type": "string"},
        "summary": {"type": "string"},
        "rationale": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "candidate_evidence": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "proposed_contract_update": {"type": "object", "additionalProperties": True},
        "requires_approval": {"type": "boolean"},
        "approval_boundary": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "next_actions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "status",
        "decision",
        "confidence",
        "summary",
        "rationale",
        "citations",
        "candidate_evidence",
        "proposed_contract_update",
        "requires_approval",
        "approval_boundary",
        "risks",
        "next_actions",
    ],
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def compact_list(items: Any, limit: int) -> list[Any]:
    return list(items[:limit]) if isinstance(items, list) else []


def compact_evidence(field_evidence: dict[str, Any], limit: int = 80) -> dict[str, Any]:
    rows = []
    for item in compact_list(field_evidence.get("evidence"), limit):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "field": item.get("field"),
                "value": item.get("value"),
                "source": item.get("source"),
                "chunk_id": item.get("chunk_id"),
                "excerpt": str(item.get("excerpt") or "")[:360],
            }
        )
    return {
        "schema_version": field_evidence.get("schema_version"),
        "policy": field_evidence.get("policy", {}),
        "evidence": rows,
    }


def compact_target_candidates(contract: dict[str, Any], discovery_report: dict[str, Any]) -> list[dict[str, Any]]:
    target_discovery = contract.get("target_discovery", {}) if isinstance(contract.get("target_discovery"), dict) else {}
    candidates = discovery_report.get("target_candidates")
    if not isinstance(candidates, list):
        candidates = target_discovery.get("candidates", [])
    result = []
    for item in compact_list(candidates, 80):
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "name": item.get("name"),
                "sources": item.get("sources", []),
                "score": item.get("score"),
                "matched_hints": item.get("matched_hints", []),
                "raw_evidence": compact_list(item.get("raw_evidence"), 10),
                "selection_policy": item.get("selection_policy"),
            }
        )
    return result


def input_context(run_dir: Path, contract: dict[str, Any], discovery_report: dict[str, Any], app_shell_report: dict[str, Any]) -> dict[str, Any]:
    input_dir = run_dir / "input"
    material_index = read_json_if_exists(input_dir / "material_index.json")
    board_index = read_json_if_exists(input_dir / "material_index_board.json")
    field_evidence = read_json_if_exists(input_dir / "field_evidence.json")
    board_profile = read_json_if_exists(input_dir / "target_board_profile.json")
    prepared_inputs = read_json_if_exists(input_dir / "prepared_inputs.json")
    return {
        "app_shell_contract": {
            "status": contract.get("status"),
            "integration_target": contract.get("integration_target"),
            "target_discovery_policy": contract.get("target_discovery_policy"),
            "target_discovery": contract.get("target_discovery"),
            "shell_project": contract.get("shell_project"),
            "board_interface": contract.get("board_interface"),
            "required_actions": contract.get("required_actions", []),
        },
        "vivado_target_candidates": compact_target_candidates(contract, discovery_report),
        "target_discovery_report": {
            "status": discovery_report.get("status"),
            "summary": discovery_report.get("summary"),
            "recovery_status": discovery_report.get("recovery_status"),
            "selection_reason": discovery_report.get("selection_reason"),
            "target_discovery_policy": discovery_report.get("target_discovery_policy"),
            "blockers": discovery_report.get("blockers", []),
            "discovery": discovery_report.get("discovery", {}),
        },
        "app_shell_runtime_report": {
            "status": app_shell_report.get("status"),
            "summary": app_shell_report.get("summary"),
            "blockers": compact_list(app_shell_report.get("blockers"), 12),
            "target_discovery": app_shell_report.get("target_discovery", {}),
            "candidate_discovery": app_shell_report.get("candidate_discovery", {}),
        },
        "field_evidence": compact_evidence(field_evidence),
        "target_board_profile": {
            "board": board_profile.get("board", {}),
            "shell": board_profile.get("shell", {}),
            "memory_system": board_profile.get("memory_system", {}),
            "runtime_interface": board_profile.get("runtime_interface", {}),
            "notes": compact_list(board_profile.get("notes"), 20),
        },
        "material_index": {
            "schema_version": material_index.get("schema_version"),
            "board_files": compact_list(board_index.get("files"), 20),
            "board_chunks": compact_list(board_index.get("chunks"), 30),
        },
        "prepared_inputs_summary": {
            "status": prepared_inputs.get("status"),
            "errors": prepared_inputs.get("errors", []),
            "warnings": prepared_inputs.get("warnings", []),
            "design_team": prepared_inputs.get("design_team", {}),
        },
    }


def prompt_for_decision(context: dict[str, Any]) -> str:
    return build_prompt(
        agent="app_shell_target_hint_synthesis_agent",
        task=(
            "Synthesize a bounded app-shell integration target decision. Return either an approved contract update "
            "with source citations, or a deferral record explaining what evidence is missing."
        ),
        inputs=context,
        output_schema=DECISION_SCHEMA,
        rules=[
            "Valid decision values are approved_target, approved_policy_hints, or defer.",
            "Default to defer unless user-supplied materials explicitly identify a target candidate or unambiguous target-name hint.",
            "Vivado candidate names alone are not user intent. Do not approve a candidate only because its name looks like a compute block.",
            "For approved_target, proposed_contract_update.integration_target.ip_name or bd_cell must exactly match one vivado_target_candidates.name.",
            "For approved_policy_hints, proposed_contract_update.target_discovery_policy.candidate_name_hints must be non-empty and must be cited by user materials or LLM-confirmed field evidence.",
            "Every approved_target or approved_policy_hints decision must cite at least one user-material/field-evidence source and at least one Vivado candidate evidence row.",
            "If app-shell BD open or AXI prefix evidence is incomplete, mention that as a risk and only approve target fields when target identity is still independently clear.",
            "Do not mention Qwen, OPT, VU9P, app_shell, cnn, llm, core, acc, or any other model/project token as a built-in rule. These strings may appear only when quoted from supplied evidence.",
            "Set requires_approval=true for any semantic change that remains ambiguous. Set decision=defer when approval is still needed before contract update.",
            "Return one JSON object only.",
        ],
    )


def candidate_names(discovery_report: dict[str, Any], contract: dict[str, Any]) -> set[str]:
    return {str(item.get("name")) for item in compact_target_candidates(contract, discovery_report) if item.get("name")}


def validate_decision(decision: dict[str, Any], candidates: set[str]) -> list[str]:
    errors: list[str] = []
    kind = str(decision.get("decision") or "").strip()
    citations = decision.get("citations", []) if isinstance(decision.get("citations"), list) else []
    update = decision.get("proposed_contract_update", {}) if isinstance(decision.get("proposed_contract_update"), dict) else {}
    if kind not in {"approved_target", "approved_policy_hints", "defer"}:
        errors.append(f"invalid decision={kind}")
    if kind in {"approved_target", "approved_policy_hints"} and not citations:
        errors.append(f"{kind} requires citations")
    if kind == "approved_target":
        target = update.get("integration_target", {}) if isinstance(update.get("integration_target"), dict) else {}
        selected = target.get("ip_name") or target.get("bd_cell")
        if not selected:
            errors.append("approved_target missing integration_target.ip_name or bd_cell")
        elif str(selected) not in candidates:
            errors.append(f"approved_target {selected} does not exactly match a Vivado candidate")
    if kind == "approved_policy_hints":
        policy = update.get("target_discovery_policy", {}) if isinstance(update.get("target_discovery_policy"), dict) else {}
        hints = policy.get("candidate_name_hints") or policy.get("hint_keywords")
        if not isinstance(hints, list) or not [item for item in hints if str(item).strip()]:
            errors.append("approved_policy_hints missing non-empty target_discovery_policy.candidate_name_hints")
    return errors


def apply_decision(contract: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(contract))
    kind = str(decision.get("decision") or "")
    update = decision.get("proposed_contract_update", {}) if isinstance(decision.get("proposed_contract_update"), dict) else {}
    updated["target_selection_decision"] = decision
    if kind == "approved_target":
        target = updated.get("integration_target", {}) if isinstance(updated.get("integration_target"), dict) else {}
        proposed = update.get("integration_target", {}) if isinstance(update.get("integration_target"), dict) else {}
        for key in ["ip_name", "bd_cell", "bd_path", "adapter_contract"]:
            if proposed.get(key) not in {None, "", []}:
                target[key] = proposed.get(key)
        target["selection_source"] = "llm_target_hint_synthesis"
        target["selection_citations"] = decision.get("citations", [])[:12]
        updated["integration_target"] = target
        updated["status"] = "ready_for_app_shell_generation"
    elif kind == "approved_policy_hints":
        policy = updated.get("target_discovery_policy", {}) if isinstance(updated.get("target_discovery_policy"), dict) else {}
        proposed = update.get("target_discovery_policy", {}) if isinstance(update.get("target_discovery_policy"), dict) else {}
        hints = proposed.get("candidate_name_hints") or proposed.get("hint_keywords") or []
        if isinstance(hints, list):
            existing = policy.get("candidate_name_hints", []) if isinstance(policy.get("candidate_name_hints"), list) else []
            merged = []
            for item in [*existing, *hints]:
                text = str(item).strip()
                if text and text not in merged:
                    merged.append(text)
            policy["candidate_name_hints"] = merged
            policy["auto_select"] = bool(policy.get("auto_select", False)) if proposed.get("auto_select") is None else bool(proposed.get("auto_select"))
            policy["hint_sources"] = decision.get("citations", [])[:12]
            policy["selection_source"] = "llm_target_hint_synthesis"
        updated["target_discovery_policy"] = policy
        updated["status"] = "target_discovery_required"
    else:
        updated["status"] = "target_discovery_deferred"
    return updated


def call_decision_llm(prompt: str, out_dir: Path) -> dict[str, Any]:
    llm = resolved_llm_cfg()
    if str(llm.mode).strip().lower() in {"", "off", "none", "disabled"}:
        raise RuntimeError(f"LLM mode is disabled: {llm.mode}")
    if not llm.endpoint or not llm.api_key or not llm.model:
        raise RuntimeError("missing LLM endpoint, API key, or model")
    prompt_path = out_dir / "app_shell_target_hint_synthesis_prompt.md"
    result_path = out_dir / "app_shell_target_hint_synthesis_result.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    started = time.monotonic()
    raw_text = ""
    retry_errors: list[str] = []
    try:
        raw_text, retry_errors = call_llm_with_retry(
            llm.endpoint,
            llm.api_key,
            llm.model,
            prompt,
            "app_shell_target_hint_synthesis_json",
            DECISION_SCHEMA,
            llm_timeout_sec(),
            reasoning_effort=llm.reasoning_effort,
        )
        try:
            output = parse_json_object(raw_text)
            validate_schema(output, DECISION_SCHEMA, "app_shell_target_hint_synthesis")
        except Exception as exc:
            repair = repair_prompt("app_shell_target_hint_synthesis_agent", prompt, raw_text, str(exc), DECISION_SCHEMA)
            repair_text, repair_retry_errors = call_llm_with_retry(
                llm.endpoint,
                llm.api_key,
                llm.model,
                repair,
                "app_shell_target_hint_synthesis_repair_json",
                DECISION_SCHEMA,
                llm_timeout_sec(),
                reasoning_effort=llm.reasoning_effort,
            )
            retry_errors.extend(repair_retry_errors)
            output = parse_json_object(repair_text)
            validate_schema(output, DECISION_SCHEMA, "app_shell_target_hint_synthesis_repair")
        record = {
            "schema_version": "spatialaccagent.target_hint_synthesis_llm_record.v0",
            "request_path": str(prompt_path),
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "result_path": str(result_path),
            "used_fallback": False,
            "error": None,
            "retry_errors": retry_errors,
            "duration_sec": time.monotonic() - started,
            "output": output,
        }
        write_json(result_path, record)
        return output
    except Exception as exc:
        record = {
            "schema_version": "spatialaccagent.target_hint_synthesis_llm_record.v0",
            "request_path": str(prompt_path),
            "prompt_hash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "result_path": str(result_path),
            "used_fallback": False,
            "error": str(exc),
            "retry_errors": retry_errors,
            "duration_sec": time.monotonic() - started,
            "raw_text_tail": raw_text[-2000:],
            "output": None,
        }
        write_json(result_path, record)
        raise


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM app-shell target hint synthesis and approval/deferral.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--target-discovery-report", type=Path, required=True)
    parser.add_argument("--app-shell-report", type=Path, required=True)
    parser.add_argument("--out-contract", type=Path, required=True)
    parser.add_argument("--out-decision", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = args.run_dir.resolve()
    contract = read_json(args.contract)
    discovery_report = read_json_if_exists(args.target_discovery_report)
    app_shell_report = read_json_if_exists(args.app_shell_report)
    llm_dir = run_dir / "backend_board" / "llm"
    llm_dir.mkdir(parents=True, exist_ok=True)

    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    context = input_context(run_dir, contract, discovery_report, app_shell_report)
    prompt = prompt_for_decision(context)
    decision: dict[str, Any] = {}
    updated_contract = contract
    try:
        decision = call_decision_llm(prompt, llm_dir)
        errors = validate_decision(decision, candidate_names(discovery_report, contract))
        if errors:
            blockers.extend(errors)
        else:
            updated_contract = apply_decision(contract, decision)
            write_json(args.out_contract, updated_contract)
            write_json(args.out_decision, decision)
    except Exception as exc:
        blockers.append(f"LLM target hint synthesis failed: {exc}")

    if blockers:
        write_json(args.out_contract, contract)
        if decision:
            write_json(args.out_decision, decision)

    checks.extend(
        [
            {"name": "llm_target_hint_synthesis_output", "status": "pass" if decision else "fail", "summary": str(decision.get("decision") if decision else "")},
            {"name": "target_candidate_exact_match", "status": "pass" if not blockers else "fail", "summary": "; ".join(blockers[:4])},
            {"name": "contract_written", "status": "pass" if args.out_contract.is_file() else "fail", "path": str(args.out_contract)},
            {"name": "decision_written", "status": "pass" if args.out_decision.is_file() else "fail", "path": str(args.out_decision)},
        ]
    )
    report = {
        "schema_version": "spatialaccagent.app_shell_target_hint_synthesis.v0",
        "status": "pass" if not blockers else "fail",
        "summary": decision.get("summary") if decision and not blockers else f"{len(blockers)} blocker(s)",
        "run_dir": str(run_dir),
        "contract": str(args.contract),
        "updated_contract": str(args.out_contract),
        "target_discovery_report": str(args.target_discovery_report),
        "app_shell_report": str(args.app_shell_report),
        "decision_path": str(args.out_decision),
        "decision": decision,
        "target_selection_decision": {
            "decision": decision.get("decision"),
            "status": decision.get("status"),
            "confidence": decision.get("confidence"),
            "requires_approval": decision.get("requires_approval"),
            "citations": compact_list(decision.get("citations"), 12),
            "proposed_contract_update": decision.get("proposed_contract_update", {}),
        }
        if decision
        else {},
        "checks": checks,
        "blockers": blockers,
        "acceptance_policy": "Pass means an LLM-produced, source-cited approval or deferral artifact was generated; it does not imply app-shell bitstream pass.",
    }
    write_json(args.out, report)
    if blockers:
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
