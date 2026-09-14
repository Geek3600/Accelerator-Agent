"""LLM pre-stage safety gate for SACG-aware stage decisions."""

from __future__ import annotations

import json
import hashlib
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from accagent.framework.agent_common import compact_json, read_json, write_json
from accagent.framework.llm_config import LlmCfg, resolved_llm_cfg
from accagent.framework.llm_io import (
    PROMPT_PROTOCOL,
    build_prompt,
    parse_json_object,
    read_response_text,
    repair_prompt,
    response_payload,
    validate_schema,
)
from accagent.framework.llm_prompts import STAGE_DECISION_SCHEMA, SYSTEM_PROMPT
from accagent.framework.sacg_utils import sacg_memory_truth


DECISIONS = {"run_tool", "stop", "needs_human_approval"}

PLANNING_STAGES = {
    "constraint_extraction",
    "template_selection",
    "pipeline_planning",
    "parameter_binding",
    "code_generation",
    "verification_artifacts",
    "repair",
    "backend_board",
}

FORBIDDEN_STOP_MARKERS = {
    "delete failing test",
    "delete tests",
    "modify golden",
    "golden outputs",
    "loosen tolerance",
    "change model semantics",
    "treat gqa as mha",
    "bypass checker",
    "claim hardware pass",
    "claim final design pass",
    "mark failed",
    "forbidden",
}


def transient_post_error(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 404 and retry_404_model_route_errors():
            return True
        return exc.code in {408, 409, 425, 429, 500, 502, 503, 504}
    if isinstance(exc, (TimeoutError, socket.timeout, ssl.SSLError, urllib.error.URLError)):
        return True
    text = str(exc).lower()
    return "timed out" in text or "bad record mac" in text or "decryption failed" in text or "ssl" in text


def retry_bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def retry_float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(0.0, float(raw))
    except ValueError:
        return default


def safety_gate_retry_unbounded() -> bool:
    return retry_bool_env("SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED", True)


def retry_404_model_route_errors() -> bool:
    return retry_bool_env("SPATIALACC_LLM_RETRY_404_MODEL_ROUTE", True)


def safety_gate_retry_attempts(default: int = 5) -> int:
    raw = os.environ.get("SPATIALACC_LLM_TRANSIENT_ATTEMPTS", "").strip()
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def safety_gate_retry_sleep_seconds(attempt: int) -> float:
    base = retry_float_env("SPATIALACC_LLM_RETRY_BASE_SEC", 8.0)
    max_delay = retry_float_env("SPATIALACC_LLM_RETRY_MAX_SEC", 90.0)
    return min(max_delay, base * (2 ** max(0, attempt - 1)))


def small_list(items: list[dict[str, Any]], keys: list[str], n: int) -> list[dict[str, Any]]:
    return [{key: item.get(key) for key in keys if key in item} for item in items[:n]]


def brief_json(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    data = read_json(path)
    return {
        "path": str(path),
        "schema_version": data.get("schema_version"),
        "stage": data.get("stage"),
        "status": data.get("status"),
        "errors": data.get("errors", []),
        "warnings": data.get("warnings", []),
    }


def brief_sacg(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    state = read_json(path)
    return {
        "path": str(path),
        "design_id": state.get("design_id"),
        "counts": {
            "nodes": len(state.get("nodes", [])),
            "edges": len(state.get("edges", [])),
            "constraints": len(state.get("constraints", [])),
            "invariants": len(state.get("invariants", [])),
            "artifacts": len(state.get("artifacts", [])),
            "evidence": len(state.get("evidence", [])),
            "transitions": len(state.get("transitions", [])),
        },
        "nodes": small_list(state.get("nodes", []), ["id", "type", "name"], 16),
        "edges": small_list(state.get("edges", []), ["id", "type", "src", "dst"], 16),
        "constraints": small_list(state.get("constraints", []), ["id", "type"], 32),
        "invariants": small_list(state.get("invariants", []), ["id", "checker", "status"], 16),
        "artifacts": small_list(state.get("artifacts", []), ["id", "type", "path"], 20),
        "sacg_memory_truth": sacg_memory_truth(state),
    }


def goal(stage: str) -> str:
    goals = {
        "input_preparation": "Prepare model, numeric, template, design-space, and board inputs.",
        "constraint_extraction": "Create the initial design graph from prepared inputs.",
        "template_selection": "Select hardware templates for model operators.",
        "pipeline_planning": "Create a spatial pipeline plan from selected templates.",
        "parameter_binding": "Bind design-space parameters to pipeline stages.",
        "code_generation": "Generate accelerator hardware code from selected templates and parameters.",
        "verification_artifacts": "Plan checkers and verification artifacts.",
        "verification": "Run framework-level checks and collect evidence.",
        "repair": "Plan bounded repair actions from verification failures.",
        "backend_board": "Plan implementation and board closure steps.",
        "sacg_validate": "Validate final SACG state references.",
    }
    return goals.get(stage, "Run the next SpatialAccAgent stage.")


def ok(stage: str, reason: str) -> dict[str, Any]:
    return {
        "decision": "run_tool",
        "tool_command_allowed": True,
        "stage": stage,
        "reason": reason,
        "sacg_focus": {"nodes": [], "edges": [], "constraints": [], "artifacts": []},
        "expected_evidence": ["stage report", "SACG transition log"],
        "risks": ["pre-stage safety gate does not replace checker evidence"],
        "approval_required_for": [],
    }


def fail_open(stage: str, reason: str) -> dict[str, Any]:
    data = ok(stage, reason)
    data["risks"] = ["LLM call failed; deterministic tools are the only evidence"]
    return data


def check(stage: str, data: dict[str, Any]) -> dict[str, Any]:
    if data.get("decision") not in DECISIONS:
        raise ValueError(f"bad safety gate decision: {data.get('decision')}")
    if data.get("stage") != stage:
        raise ValueError(f"safety gate stage mismatch: {data.get('stage')} != {stage}")
    if not isinstance(data.get("tool_command_allowed"), bool):
        raise ValueError("safety gate decision missing tool_command_allowed")
    data.setdefault("reason", "")
    data.setdefault("sacg_focus", {"nodes": [], "edges": [], "constraints": [], "artifacts": []})
    data.setdefault("expected_evidence", [])
    data.setdefault("risks", [])
    data.setdefault("approval_required_for", [])
    return data


def has_forbidden_stop_reason(data: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(item).lower()
        for item in [
            data.get("reason", ""),
            *data.get("risks", []),
            *data.get("expected_evidence", []),
            *data.get("approval_required_for", []),
        ]
    )
    return any(marker in haystack for marker in FORBIDDEN_STOP_MARKERS)


def normalize_decision(stage: str, data: dict[str, Any]) -> dict[str, Any]:
    """Keep conservative safety-gate blocks from stopping candidate stages.

    Stages before verification/implementation closure create candidate artifacts and
    SACG records for later checkers. They should be blocked only for explicitly
    forbidden actions, not because checker evidence for the just-created
    artifact does not exist yet.
    """

    decision = str(data.get("decision") or "").strip()
    if decision not in {"stop", "needs_human_approval"}:
        return data
    if stage not in PLANNING_STAGES or has_forbidden_stop_reason(data):
        return data

    original_reason = data.get("reason", "")
    data["decision"] = "run_tool"
    data["tool_command_allowed"] = True
    data["reason"] = (
        "Safety gate block normalized to run_tool: this is a candidate planning "
        "stage that must emit artifacts before later checkers can verify them; "
        "approval-sensitive changes remain recorded in approval_required_for."
    )
    data.setdefault("risks", []).append(f"safety gate originally requested {decision}: {original_reason}")
    data.setdefault("expected_evidence", []).append("downstream checker evidence must verify this candidate artifact")
    return data


def print_decision(stage: str, data: dict[str, Any], req_path: Path, dec_path: Path) -> None:
    print(f"[safety_gate] request {req_path}", file=sys.stderr, flush=True)
    print(f"[safety_gate] decision {stage}: {data.get('decision')}", file=sys.stderr, flush=True)
    print(f"[safety_gate] allowed {stage}: {data.get('tool_command_allowed')}", file=sys.stderr, flush=True)
    if data.get("reason"):
        print(f"[safety_gate] reason {stage}: {data.get('reason')}", file=sys.stderr, flush=True)
    focus = data.get("sacg_focus") or {}
    print(f"[safety_gate] focus {stage}: {compact_json(focus, 700)}", file=sys.stderr, flush=True)
    if data.get("expected_evidence"):
        print(f"[safety_gate] evidence {stage}: {compact_json(data.get('expected_evidence'), 700)}", file=sys.stderr, flush=True)
    if data.get("risks"):
        print(f"[safety_gate] risks {stage}: {compact_json(data.get('risks'), 700)}", file=sys.stderr, flush=True)
    if data.get("approval_required_for"):
        print(
            f"[safety_gate] approval_required {stage}: {compact_json(data.get('approval_required_for'), 700)}",
            file=sys.stderr,
            flush=True,
        )
    print(f"[safety_gate] log {dec_path}", file=sys.stderr, flush=True)


class PreStageSafetyGate:
    """Write one LLM safety decision record before each stage tool."""

    def __init__(self, out: Path, cfg: LlmCfg):
        self.out = out.resolve()
        self.cfg = cfg
        self.log_dir = self.out / "agent" / "llm"
        self.i = 0

    @property
    def on(self) -> bool:
        return str(self.cfg.mode).strip().lower() not in {"", "off", "none", "disabled"}

    def prompt_hash(self, req: dict[str, Any]) -> str:
        text = str(req.get("system_prompt") or "") + "\n" + str(req.get("user_prompt") or "")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def cached_run_tool_decision(self, stage: str, prompt_hash: str) -> tuple[Path, Path, dict[str, Any]] | None:
        for dec_path in sorted(self.log_dir.glob(f"*_{stage}_decision.json"), reverse=True):
            try:
                rec = read_json(dec_path)
            except Exception:
                continue
            if rec.get("stage") != stage or rec.get("error"):
                continue
            rec_hash = rec.get("prompt_hash")
            req_path = Path(str(rec.get("request_path") or ""))
            if not rec_hash and req_path.exists():
                try:
                    rec_hash = self.prompt_hash(read_json(req_path))
                except Exception:
                    rec_hash = None
            if rec_hash != prompt_hash:
                continue
            decision = rec.get("decision", {})
            if (
                isinstance(decision, dict)
                and decision.get("decision") == "run_tool"
                and decision.get("tool_command_allowed") is True
            ):
                return req_path, dec_path, rec
        return None

    def ask(
        self,
        stage: str,
        cmd: list[str],
        sacg: Path | None = None,
        prepared: Path | None = None,
    ) -> dict[str, Any]:
        if not self.on:
            data = fail_open(stage, f"LLM mode is disabled: {self.cfg.mode}.")
            if self.cfg.enforce:
                data["decision"] = "stop"
                data["tool_command_allowed"] = False
            return {
                "enabled": False,
                "mode": self.cfg.mode,
                "decision": data,
                "enforced": self.cfg.enforce,
                "error": None if not self.cfg.enforce else f"LLM mode is disabled: {self.cfg.mode}",
            }

        req = self.build_req(stage, cmd, sacg, prepared)
        current_prompt_hash = self.prompt_hash(req)
        cached = self.cached_run_tool_decision(stage, current_prompt_hash)
        if cached is not None:
            req_path, dec_path, rec = cached
            print(f"[safety_gate] reuse {stage}: {dec_path}", file=sys.stderr, flush=True)
            return {
                "enabled": True,
                "mode": self.cfg.mode,
                "request_path": str(req_path),
                "decision_path": str(dec_path),
                "decision": rec.get("decision", {}),
                "enforced": self.cfg.enforce,
                "error": None,
                "reused": True,
            }

        self.i += 1
        req_path = self.log_dir / f"{self.i:02d}_{stage}_request.json"
        dec_path = self.log_dir / f"{self.i:02d}_{stage}_decision.json"
        write_json(req_path, req)

        start = time.monotonic()
        error = None
        raw_text = ""
        print(f"[safety_gate] start {stage}", file=sys.stderr, flush=True)
        print(f"[safety_gate] prompt {req_path}", file=sys.stderr, flush=True)
        try:
            raw_text = self.call(req["user_prompt"], "spatialaccagent_stage_decision")
            data = parse_json_object(raw_text)
            validate_schema(data, STAGE_DECISION_SCHEMA, stage)
            data = check(stage, data)
            data = normalize_decision(stage, data)
        except Exception as exc:
            try:
                if not raw_text:
                    raise
                fix_prompt = repair_prompt("pre_stage_safety_gate", req["user_prompt"], raw_text, str(exc), STAGE_DECISION_SCHEMA)
                raw_text = self.call(fix_prompt, "spatialaccagent_stage_decision_repair")
                data = parse_json_object(raw_text)
                validate_schema(data, STAGE_DECISION_SCHEMA, stage)
                data = check(stage, data)
                data = normalize_decision(stage, data)
            except Exception as repair_exc:
                error = str(repair_exc)
                data = fail_open(stage, f"LLM call failed: {error}")
                if self.cfg.enforce:
                    data["decision"] = "stop"
                    data["tool_command_allowed"] = False

        rec = {
            "schema_version": "spatialaccagent.pre_stage_safety_gate_decision.v0",
            "stage": stage,
            "mode": self.cfg.mode,
            "request_path": str(req_path),
            "prompt_hash": current_prompt_hash,
            "duration_sec": time.monotonic() - start,
            "decision": data,
            "enforced": self.cfg.enforce,
            "error": error,
        }
        write_json(dec_path, rec)
        print(
            f"[safety_gate] done {stage}: decision={data.get('decision')} "
            f"allowed={data.get('tool_command_allowed')} ({rec['duration_sec']:.1f}s)",
            file=sys.stderr,
            flush=True,
        )
        print_decision(stage, data, req_path, dec_path)
        return {
            "enabled": True,
            "mode": self.cfg.mode,
            "request_path": str(req_path),
            "decision_path": str(dec_path),
            "decision": data,
            "enforced": self.cfg.enforce,
            "error": error,
        }

    def build_req(self, stage: str, cmd: list[str], sacg: Path | None, prepared: Path | None) -> dict[str, Any]:
        stage_req = {
            "stage": stage,
            "objective": goal(stage),
            "tool_command": cmd,
            "sacg_summary": brief_sacg(sacg),
            "prepared_inputs_summary": brief_json(prepared),
        }
        prompt = build_prompt(
            agent="pre_stage_safety_gate",
            task="Decide whether the next deterministic SpatialAccAgent stage tool is safe to run.",
            inputs={"stage_request": stage_req},
            output_schema=STAGE_DECISION_SCHEMA,
            rules=[
                "No checker pass, no design pass.",
                "Do not approve deleting tests, changing golden outputs, loosening tolerance, or changing model semantics.",
                "Return stop only for forbidden or unsafe actions.",
                "Planning stages create candidate artifacts that later checker stages validate; do not stop them only because their own future checker evidence does not exist yet.",
                "Use stage_request.sacg_summary.sacg_memory_truth as the authoritative current blocker set; closed, superseded, rejected, or historical memory records are recovery evidence only.",
                "If a pipeline stage, tile size, parallelism, memory layout, data packing, numeric policy, AXI/DDR access, or major template change may need approval, record it in approval_required_for.",
                "For analysis, planning, evidence collection, or checker stages, do not block the tool just because future human approval may be required.",
                "If the stage is safe to run, set decision to run_tool and tool_command_allowed to true.",
                "Focus the answer on SACG nodes, edges, constraints, artifacts, evidence, and cross-layer consistency risk.",
            ],
        )
        return {
            "schema_version": "spatialaccagent.pre_stage_safety_gate_request.v0",
            "prompt_protocol": PROMPT_PROTOCOL,
            "stage": stage,
            "model": self.cfg.model,
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": prompt,
            "output_schema": STAGE_DECISION_SCHEMA,
            "stage_request": stage_req,
        }

    def call(self, prompt: str, schema_name: str) -> str:
        payload = response_payload(
            self.cfg.model,
            SYSTEM_PROMPT,
            prompt,
            schema_name,
            STAGE_DECISION_SCHEMA,
            temperature=self.cfg.temperature,
            strict=True,
            store=self.cfg.store,
            reasoning_effort=self.cfg.reasoning_effort,
            text_verbosity=self.cfg.text_verbosity,
            max_output_tokens=self.cfg.max_output_tokens,
            stream=self.cfg.stream,
        )
        return self.post(payload)

    def post(self, payload: dict[str, Any]) -> str:
        key = self.cfg.api_key
        if not key:
            raise RuntimeError("LLM api_key is required when LLM mode is enabled")

        req = urllib.request.Request(
            self.cfg.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream" if self.cfg.stream else "application/json",
                "Connection": "close",
            },
            method="POST",
        )
        last_error = ""
        max_attempts = None if safety_gate_retry_unbounded() else safety_gate_retry_attempts()
        attempt = 1
        while True:
            try:
                data = read_response_text(req, self.cfg.timeout_sec, self.cfg.stream)
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_error = f"LLM HTTP error {exc.code}: {detail}"
                if not transient_post_error(exc):
                    raise RuntimeError(last_error) from exc
                if max_attempts is not None and attempt >= max_attempts:
                    raise RuntimeError(last_error) from exc
                retry_mode = "unbounded" if max_attempts is None else f"{attempt}/{max_attempts}"
                delay = safety_gate_retry_sleep_seconds(attempt)
                print(
                    f"[safety_gate] retry request after transient error ({retry_mode}): "
                    f"{last_error}; sleep {delay:.1f}s",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(delay)
            except Exception as exc:
                last_error = str(exc)
                if not transient_post_error(exc):
                    raise RuntimeError(f"LLM request failed: {last_error}") from exc
                if max_attempts is not None and attempt >= max_attempts:
                    raise RuntimeError(f"LLM request failed: {last_error}") from exc
                retry_mode = "unbounded" if max_attempts is None else f"{attempt}/{max_attempts}"
                delay = safety_gate_retry_sleep_seconds(attempt)
                print(
                    f"[safety_gate] retry request after transient error ({retry_mode}): "
                    f"{last_error}; sleep {delay:.1f}s",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(delay)
            attempt += 1
        return data


def default_llm_cfg() -> LlmCfg:
    return resolved_llm_cfg()
