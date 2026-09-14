#!/usr/bin/env python3
"""Normalize and apply a bounded backend recovery approval.

This tool is intentionally narrow. It lets the multi-agent system resume after
an LLM-generated human-boundary request, but only when an approval artifact
selects exactly one currently cited option. It does not choose targets itself.
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
from accagent.framework.sacg_utils import safe_id
from accagent.framework.stage_llm import call_llm_with_retry, llm_timeout_sec


APPROVAL_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        "schema_version": {"type": "string"},
        "decision": {"type": "string"},
        "selected_option": {"type": "string"},
        "rationale": {"type": "string"},
        "approver": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        "allowed_contract_updates": {"type": "array", "items": {"type": "string"}},
        "forbidden_contract_updates": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "schema_version",
        "decision",
        "selected_option",
        "rationale",
        "approver",
        "citations",
        "allowed_contract_updates",
        "forbidden_contract_updates",
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


def read_approval_material(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return {"format": "json", "content": parsed, "raw_text": text[:4000]}
    except json.JSONDecodeError:
        pass
    return {"format": "text", "content": {}, "raw_text": text[:8000]}


def candidate_names_from_report(report: dict[str, Any]) -> list[str]:
    rows = report.get("target_candidates")
    if not isinstance(rows, list):
        discovery = report.get("target_discovery", {}) if isinstance(report.get("target_discovery"), dict) else {}
        rows = discovery.get("candidates", [])
    names: list[str] = []
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and row.get("name"):
            text = str(row["name"]).strip()
            if text and text not in names:
                names.append(text)
    return names


def allowed_options(request: dict[str, Any]) -> list[str]:
    action = request.get("action", {}) if isinstance(request.get("action"), dict) else {}
    run_dir = Path(str(request.get("run_dir") or "."))
    options: list[str] = []
    for value in action.get("consumes", []) if isinstance(action.get("consumes"), list) else []:
        path = Path(str(value))
        if not path.is_absolute():
            path = run_dir / path
        report = read_json_if_exists(path)
        for name in candidate_names_from_report(report):
            if name not in options:
                options.append(name)
    return options


def prompt_for_approval(request: dict[str, Any], approval_material: dict[str, Any], options: list[str]) -> str:
    return build_prompt(
        agent="backend_recovery_approval_ingest_agent",
        task=(
            "Normalize a human/design-team approval artifact for a bounded backend recovery action. "
            "Do not choose an option yourself; only interpret whether the supplied approval explicitly selects "
            "one current option, rejects all options, or requests more evidence."
        ),
        inputs={
            "pending_request": {
                "status": request.get("status"),
                "decision": request.get("decision"),
                "next_stage": request.get("next_stage"),
                "action": request.get("action"),
                "evidence_citations": request.get("evidence_citations", [])[:12]
                if isinstance(request.get("evidence_citations"), list)
                else [],
                "approval_record_schema": request.get("approval_record_schema", {}),
            },
            "current_allowed_options": options,
            "approval_material": approval_material,
        },
        output_schema=APPROVAL_SCHEMA,
        rules=[
            "Valid decision values are approved, rejected, or request_more_evidence.",
            "Use decision=approved only when approval_material explicitly selects exactly one current_allowed_options value.",
            "selected_option must be empty unless decision=approved.",
            "For decision=approved, selected_option must exactly match one current_allowed_options string.",
            "Do not infer a target from score, order, name token, model token, board token, or project token.",
            "Do not authorize BD path, adapter_contract, runtime ABI, memory layout, architecture, numeric policy, or bitstream pass changes.",
            "Return one JSON object only.",
        ],
    )


def call_approval_llm(prompt: str, out_dir: Path) -> dict[str, Any]:
    llm = resolved_llm_cfg()
    if str(llm.mode).strip().lower() in {"", "off", "none", "disabled"}:
        raise RuntimeError(f"LLM mode is disabled: {llm.mode}")
    if not llm.endpoint or not llm.api_key or not llm.model:
        raise RuntimeError("missing LLM endpoint, API key, or model")
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = out_dir / "backend_recovery_approval_ingest_prompt.md"
    result_path = out_dir / "backend_recovery_approval_ingest_result.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    expected_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if result_path.is_file():
        cached = read_json_if_exists(result_path)
        if (
            cached.get("prompt_hash") == expected_hash
            and not cached.get("error")
            and isinstance(cached.get("output"), dict)
        ):
            print(f"[approval-ingest] reuse cached {result_path}", flush=True)
            return cached
    started = time.monotonic()
    raw_text = ""
    retry_errors: list[str] = []
    try:
        raw_text, retry_errors = call_llm_with_retry(
            llm.endpoint,
            llm.api_key,
            llm.model,
            prompt,
            "backend_recovery_approval_ingest_json",
            APPROVAL_SCHEMA,
            llm_timeout_sec(),
            reasoning_effort=llm.reasoning_effort,
        )
        try:
            output = parse_json_object(raw_text)
            validate_schema(output, APPROVAL_SCHEMA, "backend_recovery_approval_ingest")
        except Exception as exc:
            repair = repair_prompt("backend_recovery_approval_ingest_agent", prompt, raw_text, str(exc), APPROVAL_SCHEMA)
            repair_text, repair_retry_errors = call_llm_with_retry(
                llm.endpoint,
                llm.api_key,
                llm.model,
                repair,
                "backend_recovery_approval_ingest_repair_json",
                APPROVAL_SCHEMA,
                llm_timeout_sec(),
                reasoning_effort=llm.reasoning_effort,
            )
            retry_errors.extend(repair_retry_errors)
            output = parse_json_object(repair_text)
            validate_schema(output, APPROVAL_SCHEMA, "backend_recovery_approval_ingest_repair")
        record = {
            "schema_version": "spatialaccagent.backend_recovery_approval_ingest_llm_record.v0",
            "request_path": str(prompt_path),
            "prompt_hash": expected_hash,
            "result_path": str(result_path),
            "error": None,
            "retry_errors": retry_errors,
            "duration_sec": time.monotonic() - started,
            "output": output,
        }
        write_json(result_path, record)
        return record
    except Exception as exc:
        record = {
            "schema_version": "spatialaccagent.backend_recovery_approval_ingest_llm_record.v0",
            "request_path": str(prompt_path),
            "prompt_hash": expected_hash,
            "result_path": str(result_path),
            "error": str(exc),
            "retry_errors": retry_errors,
            "duration_sec": time.monotonic() - started,
            "raw_text_tail": raw_text[-2000:],
            "output": None,
        }
        write_json(result_path, record)
        raise


def validate_approval(approval: dict[str, Any], options: list[str]) -> list[str]:
    errors: list[str] = []
    decision = str(approval.get("decision") or "").strip()
    selected = str(approval.get("selected_option") or "").strip()
    if decision not in {"approved", "rejected", "request_more_evidence"}:
        errors.append(f"invalid decision={decision}")
    if decision == "approved":
        if not selected:
            errors.append("approved decision missing selected_option")
        elif selected not in options:
            errors.append(f"selected_option does not exactly match a current option: {selected}")
    elif selected:
        errors.append("selected_option must be empty unless decision=approved")
    forbidden = approval.get("forbidden_contract_updates", [])
    if not isinstance(forbidden, list) or not forbidden:
        errors.append("forbidden_contract_updates must explicitly preserve blocked fields")
    return errors


def apply_approval_to_contract(contract: dict[str, Any], approval: dict[str, Any], request: dict[str, Any], report_path: Path) -> dict[str, Any]:
    updated = json.loads(json.dumps(contract))
    target = updated.get("integration_target", {}) if isinstance(updated.get("integration_target"), dict) else {}
    decision = str(approval.get("decision") or "")
    if decision == "approved":
        selected = str(approval.get("selected_option") or "")
        target["ip_name"] = selected
        target["selection_source"] = "human_boundary_approval_ingest"
        target["selection_approval"] = {
            "decision": decision,
            "rationale": approval.get("rationale"),
            "approver": approval.get("approver"),
            "citations": approval.get("citations", [])[:12] if isinstance(approval.get("citations"), list) else [],
            "report_path": str(report_path),
        }
        updated["integration_target"] = target
        updated["status"] = "ready_for_app_shell_generation"
        updated["target_discovery"] = {
            **(updated.get("target_discovery", {}) if isinstance(updated.get("target_discovery"), dict) else {}),
            "status": "selected_by_approval",
            "selected_target": {"name": selected, "selection_source": "human_boundary_approval_ingest"},
            "selection_reason": "approved_human_boundary_target_selection",
        }
    else:
        updated["status"] = "target_discovery_deferred"
        updated["target_discovery"] = {
            **(updated.get("target_discovery", {}) if isinstance(updated.get("target_discovery"), dict) else {}),
            "status": decision,
            "selected_target": None,
            "selection_reason": "approval_ingest_did_not_select_target",
        }
    updated["target_selection_approval"] = {
        "schema_version": "spatialaccagent.backend_target_selection_approval.v0",
        "decision": decision,
        "selected_option": approval.get("selected_option"),
        "approval_artifact_status": request.get("status"),
        "allowed_contract_update": "integration_target.ip_name only when decision=approved",
        "report_path": str(report_path),
    }
    return updated


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest bounded backend recovery approval and update contract safely.")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out-contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    request = read_json(args.request)
    contract = read_json(args.contract)
    approval_material = read_approval_material(args.approval)
    options = allowed_options(request)
    llm_dir = args.out.parent.parent / "llm" if args.out.parent.name == "case_diagnostics" else args.out.parent / "llm"
    blockers: list[str] = []
    normalized: dict[str, Any] = {}
    llm_record: dict[str, Any] = {}
    try:
        prompt = prompt_for_approval(request, approval_material, options)
        llm_record = call_approval_llm(prompt, llm_dir)
        normalized = llm_record.get("output", {}) if isinstance(llm_record.get("output"), dict) else {}
        blockers.extend(validate_approval(normalized, options))
    except Exception as exc:
        blockers.append(f"approval ingest LLM failed: {exc}")

    if normalized and not blockers:
        updated = apply_approval_to_contract(contract, normalized, request, args.out)
        write_json(args.out_contract, updated)
    else:
        write_json(args.out_contract, contract)

    checks = [
        {
            "name": "approval_options_available",
            "status": "pass" if options else "fail",
            "summary": f"{len(options)} option(s)",
        },
        {
            "name": "approval_llm_normalized",
            "status": "pass" if normalized else "fail",
            "summary": str(normalized.get("decision") or ""),
        },
        {
            "name": "approval_exact_option_check",
            "status": "pass" if normalized and not blockers else "fail",
            "summary": "; ".join(blockers[:4]) if blockers else "approval is bounded to current options",
        },
    ]
    report = {
        "schema_version": "spatialaccagent.backend_recovery_approval_ingest.v0",
        "status": "pass" if normalized and not blockers else "fail",
        "summary": normalized.get("decision") if normalized and not blockers else f"{len(blockers)} blocker(s)",
        "request": str(args.request),
        "approval": str(args.approval),
        "contract": str(args.contract),
        "updated_contract": str(args.out_contract),
        "allowed_options": options,
        "normalized_approval": normalized,
        "llm_record_path": llm_record.get("result_path"),
        "checks": checks,
        "blockers": blockers,
        "policy": "LLM normalizes the approval material; deterministic checks enforce exact-option and contract-update boundaries.",
    }
    write_json(args.out, report)
    if blockers:
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
