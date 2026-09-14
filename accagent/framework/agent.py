"""MAGE-style top-level orchestration for SpatialAccAgent."""

from __future__ import annotations

import shutil
import sys
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from accagent.framework.agent_common import CommandResult, ToolRunner, compact_json, read_json, write_json
from accagent.framework.sacg_utils import sacg_memory_summary, safe_id
from accagent.framework.stage_agent import (
    ConstraintExtractionAgent,
    GenericStageAgent,
    InputPreparationAgent,
    SACGValidationAgent,
    StageResult,
    TemplateSelectionAgent,
    temporary_env,
)
from accagent.framework.config import CFG, RunCfg
from accagent.framework.llm_client import PreStageSafetyGate
from accagent.framework.stage_input_common import DEFAULT_TEMPLATE_DIR
from accagent.framework.stage_llm import run_stage_agent


STAGE_TARGET_ALIASES = {
    "stage3.pipeline_planning": "pipeline_planning",
    "stage4.parameter_binding": "parameter_binding",
    "stage5.code_generation": "code_generation",
    "stage6.verification_artifacts": "verification_artifacts",
    "stage7.verification": "debug_loop",
    "stage7.debug_loop": "debug_loop",
    "stage8.repair": "debug_loop",
    "stage9.backend_board": "backend_board",
}

MAX_STAGE_ATTEMPTS = 2
MAX_FLOW_BACKTRACKS = 6


def json_dumps_stable(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class TopAgent:
    """Coordinate stage tools and record a reproducible design-run report."""

    def __init__(self, cfg: RunCfg):
        self.cfg = cfg
        self.root = cfg.root.resolve()
        self.out = cfg.out.resolve()
        self.log_dir = self.out / "agent" / "logs"
        self.report_path = self.out / "agent" / "agent_run_report.json"
        self.checkpoint_dir = self.out / "agent" / "checkpoints"
        self.flow_state_path = self.out / "agent" / "flow_state.json"
        self.runner = ToolRunner(self.root, self.log_dir)
        self.safety_gate = PreStageSafetyGate(self.out, cfg.llm)
        self.tool_env = {
            "SPATIALACC_RUN_REAL_TOOLS": "1" if cfg.run_real_tools else "0",
            "SPATIALACC_TOOL_TIMEOUT_SEC": str(cfg.real_tool_timeout_sec),
            "SPATIALACC_LLM_MODE": "llm",
            "SPATIALACC_LLM_MODEL": cfg.llm.model,
            "SPATIALACC_LLM_ENDPOINT": cfg.llm.endpoint,
            "SPATIALACC_LLM_API_KEY": cfg.llm.api_key,
            "SPATIALACC_LLM_TIMEOUT_SEC": str(cfg.llm.timeout_sec),
            "SPATIALACC_LLM_ENFORCE": "1",
            "SPATIALACC_LLM_REASONING_EFFORT": cfg.llm.reasoning_effort or "",
            "SPATIALACC_LLM_STORE": "1" if cfg.llm.store else "0",
            "SPATIALACC_LLM_TEXT_VERBOSITY": cfg.llm.text_verbosity or "",
            "SPATIALACC_LLM_STREAM": "1" if cfg.llm.stream else "0",
            "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": os.environ.get(
                "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED", "1"
            ),
            "SPATIALACC_LLM_RETRY_404_MODEL_ROUTE": os.environ.get("SPATIALACC_LLM_RETRY_404_MODEL_ROUTE", "1"),
            "SPATIALACC_TEAM_LLM_WORKERS": "1",
        }
        self.results: list[StageResult] = []
        self.flow_events: list[dict[str, Any]] = []
        self.flow_state: dict[str, Any] = self.default_flow_state()

    def default_flow_state(self) -> dict[str, Any]:
        return {
            "schema_version": "spatialaccagent.flow_state.v0",
            "stage_attempts": {},
            "legacy_stage_failures": {},
            "backtrack_count": 0,
            "flow_events": [],
        }

    def load_flow_state(self) -> dict[str, Any]:
        state = self.default_flow_state()
        if self.flow_state_path.exists():
            try:
                loaded = read_json(self.flow_state_path)
                if isinstance(loaded, dict):
                    state.update({k: v for k, v in loaded.items() if k in state or k == "schema_version"})
            except Exception:
                pass
        elif self.report_path.exists():
            try:
                report = read_json(self.report_path)
                events = report.get("flow_events", []) if isinstance(report, dict) else []
                if isinstance(events, list):
                    state["flow_events"] = [event for event in events if isinstance(event, dict)]
                    attempts: dict[str, int] = {}
                    for event in state["flow_events"]:
                        stage = str(event.get("stage") or "")
                        if stage and event.get("stage_passed") is False:
                            attempts[stage] = attempts.get(stage, 0) + 1
                    state["stage_attempts"] = attempts
            except Exception:
                pass
        if not isinstance(state.get("legacy_stage_failures"), dict):
            state["legacy_stage_failures"] = {}
        if not isinstance(state.get("stage_attempts"), dict):
            state["stage_attempts"] = {}
        active_attempts: dict[str, Any] = {}
        legacy_failures = dict(state.get("legacy_stage_failures", {}))
        for key, value in state.get("stage_attempts", {}).items():
            stage = str(key)
            if isinstance(value, dict) and value.get("epoch_hash"):
                try:
                    count = max(0, int(value.get("count", 0) or 0))
                except (TypeError, ValueError):
                    count = 0
                active_attempts[stage] = {**value, "count": count}
            else:
                try:
                    legacy_failures[stage] = max(int(legacy_failures.get(stage, 0) or 0), int(value or 0))
                except (TypeError, ValueError):
                    pass
        state["stage_attempts"] = active_attempts
        state["legacy_stage_failures"] = {
            str(key): max(0, int(value or 0))
            for key, value in legacy_failures.items()
        }
        try:
            state["backtrack_count"] = max(0, int(state.get("backtrack_count", 0) or 0))
        except (TypeError, ValueError):
            state["backtrack_count"] = 0
        if not isinstance(state.get("flow_events"), list):
            state["flow_events"] = []
        return state

    def save_flow_state(self) -> None:
        state = dict(self.flow_state)
        state["schema_version"] = "spatialaccagent.flow_state.v0"
        state["flow_events"] = self.flow_events
        write_json(self.flow_state_path, state)

    def stage_attempt_epoch(self, stage: str, module: str) -> dict[str, Any]:
        orchestration_hash = self.file_tree_hash(
            [
                Path(__file__),
                Path(__file__).with_name("stage_team.py"),
                Path(__file__).with_name("stage_llm.py"),
            ]
        )
        return {
            "stage": stage,
            "module": module,
            "stage_code_hash": self.stage_code_hash(module),
            "stage_input_hash": self.stage_input_hash(stage),
            "orchestration_hash": orchestration_hash,
        }

    def stage_attempt_epoch_hash(self, stage: str, module: str) -> str:
        payload = self.stage_attempt_epoch(stage, module)
        return hashlib.sha256(json_dumps_stable(payload).encode("utf-8")).hexdigest()

    def stage_attempt_count(self, stage: str, module: str) -> int:
        attempts = self.flow_state.get("stage_attempts", {})
        record = attempts.get(stage) if isinstance(attempts, dict) else None
        if not isinstance(record, dict):
            return 0
        if record.get("epoch_hash") != self.stage_attempt_epoch_hash(stage, module):
            return 0
        try:
            return max(0, int(record.get("count", 0) or 0))
        except (TypeError, ValueError):
            return 0

    def increment_stage_attempt(self, stage: str, module: str) -> int:
        attempts = dict(self.flow_state.get("stage_attempts", {}))
        epoch = self.stage_attempt_epoch(stage, module)
        epoch_hash = hashlib.sha256(json_dumps_stable(epoch).encode("utf-8")).hexdigest()
        prior = attempts.get(stage)
        count = int(prior.get("count", 0) or 0) if isinstance(prior, dict) and prior.get("epoch_hash") == epoch_hash else 0
        count += 1
        attempts[stage] = {
            "count": count,
            "epoch_hash": epoch_hash,
            "epoch": epoch,
        }
        self.flow_state["stage_attempts"] = attempts
        self.save_flow_state()
        return count

    def reset_stage_attempt(self, stage: str, module: str) -> None:
        attempts = dict(self.flow_state.get("stage_attempts", {}))
        record = attempts.get(stage)
        if isinstance(record, dict) and record.get("epoch_hash") == self.stage_attempt_epoch_hash(stage, module):
            attempts.pop(stage, None)
            self.flow_state["stage_attempts"] = attempts
            self.save_flow_state()

    def record_flow_event(self, event: dict[str, Any]) -> None:
        self.flow_events.append(event)
        self.materialize_flow_event_actions(event)
        self.flow_state["flow_events"] = self.flow_events
        self.save_flow_state()

    def materialize_flow_event_actions(self, event: dict[str, Any]) -> None:
        stage = safe_id(str(event.get("stage") or "flow"))
        decision = safe_id(str(event.get("decision") or "event"))
        llm_review = event.get("llm_flow_controller", {})
        actions = llm_review.get("agent_executable_actions", []) if isinstance(llm_review, dict) else []
        if not isinstance(actions, list):
            actions = []
        stage_dir = self.out / stage
        event_index = len(self.flow_events)
        for index, candidate in enumerate(self.flow_events, start=1):
            if candidate is event:
                event_index = index
                break
        event["flow_event_index"] = event_index
        payload = {
            "schema_version": "spatialaccagent.flow_event_action_record.v0",
            "flow_event_index": event_index,
            "stage": event.get("stage"),
            "decision": event.get("decision"),
            "reason": event.get("reason"),
            "attempt_count": event.get("attempt_count"),
            "sacg_state": event.get("sacg_state"),
            "llm_flow_controller": llm_review,
            "executable_actions": [action for action in actions if isinstance(action, dict)],
        }
        record_paths: list[str] = []
        event_path = stage_dir / "flow_events" / f"{event_index:03d}_{decision}.json"
        write_json(event_path, payload)
        record_paths.append(str(event_path))
        for action in payload["executable_actions"]:
            action_type = safe_id(str(action.get("action_type") or "action"))
            action_id = safe_id(str(action.get("id") or action_type))
            if any(token in action_type for token in ("barrier", "contamination", "quarantine")):
                action_dir = stage_dir / "trust_barriers"
            elif any(token in action_type for token in ("repair", "recovery")):
                action_dir = stage_dir / "bounded_repairs"
            elif any(token in action_type for token in ("retry", "replay")):
                action_dir = stage_dir / "retry_requests"
            else:
                action_dir = stage_dir / "flow_actions"
            action_path = action_dir / f"{event_index:03d}_{action_id}.json"
            write_json(
                action_path,
                {
                    "schema_version": "spatialaccagent.flow_action_record.v0",
                    "flow_event_index": event_index,
                    "stage": event.get("stage"),
                    "decision": event.get("decision"),
                    "attempt_count": event.get("attempt_count"),
                    "sacg_state": event.get("sacg_state"),
                    "action": action,
                    "source_flow_event": str(event_path),
                    "materialization_policy": {
                        "records_flow_controller_action": True,
                        "does_not_mark_stage_passed": True,
                        "does_not_promote_failed_stage_artifacts": True,
                    },
                },
            )
            record_paths.append(str(action_path))
        event["flow_action_records"] = record_paths

    def hydrate_stage_attempts_from_logs(self, stage_names: list[str]) -> None:
        legacy = dict(self.flow_state.get("legacy_stage_failures", {}))
        for stage in stage_names:
            count = 0
            for log_path in sorted(self.log_dir.glob(f"*_{safe_id(stage)}.json")):
                try:
                    log = read_json(log_path)
                except Exception:
                    continue
                if log.get("name") != stage:
                    continue
                try:
                    returncode = int(log.get("returncode", 0) or 0)
                except (TypeError, ValueError):
                    returncode = 1
                if returncode != 0:
                    count += 1
            if count > int(legacy.get(stage, 0) or 0):
                legacy[stage] = count
        self.flow_state["legacy_stage_failures"] = legacy
        self.save_flow_state()

    def resume_enabled(self) -> bool:
        if not self.cfg.resume_existing:
            return False
        raw = os.environ.get("SPATIALACC_AGENT_RESUME", "1").strip().lower()
        return raw not in {"0", "false", "no", "off"}

    def initialize_run_counters(self) -> None:
        if self.resume_enabled():
            self.runner.index = len(list(self.log_dir.glob("*.json")))
            self.safety_gate.i = len(list((self.out / "agent" / "llm").glob("*_decision.json")))
            self.flow_state = self.load_flow_state()
            self.flow_events = [
                event for event in self.flow_state.get("flow_events", []) if isinstance(event, dict)
            ]
            return
        shutil.rmtree(self.log_dir, ignore_errors=True)
        shutil.rmtree(self.out / "agent" / "llm", ignore_errors=True)
        shutil.rmtree(self.checkpoint_dir, ignore_errors=True)
        if self.flow_state_path.exists():
            self.flow_state_path.unlink()
        self.flow_state = self.default_flow_state()
        self.flow_events = []

    def stage_code_hash(self, module: str) -> str:
        spec = importlib.util.find_spec(module)
        if not spec or not spec.origin:
            return ""
        path = Path(spec.origin)
        if not path.exists():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def file_tree_hash(self, paths: list[Path]) -> str:
        digest = hashlib.sha256()
        for root in sorted(path.resolve() for path in paths):
            digest.update(str(root).encode("utf-8"))
            if not root.exists():
                digest.update(b"\0missing")
                continue
            if root.is_file():
                digest.update(b"\0file\0")
                digest.update(root.read_bytes())
                continue
            for child in sorted(item for item in root.rglob("*") if item.is_file()):
                digest.update(str(child.relative_to(root)).encode("utf-8"))
                digest.update(b"\0")
                digest.update(child.read_bytes())
                digest.update(b"\0")
        return digest.hexdigest()

    def prepared_input_artifact_paths(self) -> list[Path]:
        prepared = self.out / "input" / "prepared_inputs.json"
        paths = [prepared]
        if not prepared.exists():
            return paths
        try:
            manifest = read_json(prepared)
        except Exception:
            return paths
        run_dir = Path(str(manifest.get("run_dir") or self.out)).resolve()
        inputs = manifest.get("inputs", {})
        if not isinstance(inputs, dict):
            return paths
        for value in inputs.values():
            if not value:
                continue
            path = Path(str(value))
            if not path.is_absolute():
                path = run_dir / path
            paths.append(path)
        return paths

    def stage_input_hash(self, stage: str) -> str:
        if stage == "input_preparation":
            return self.file_tree_hash(
                [
                    self.cfg.task_spec,
                    self.cfg.model_source,
                    self.cfg.board_materials_dir,
                    self.cfg.quantization_materials_dir,
                    self.cfg.tool_materials_dir,
                    DEFAULT_TEMPLATE_DIR,
                ]
            )
        if stage == "constraint_extraction":
            return self.file_tree_hash(self.prepared_input_artifact_paths())
        if stage == "template_selection":
            return self.file_tree_hash([self.out / "constraint_extraction" / "initial_design_graph.json"])
        stage_inputs = {
            "pipeline_planning": self.out / "template_selection" / "sacg_state.json",
            "parameter_binding": self.out / "pipeline_planning" / "sacg_state.json",
            "code_generation": self.out / "parameter_binding" / "sacg_state.json",
            "verification_artifacts": self.out / "code_generation" / "sacg_state.json",
            "debug_loop": self.out / "verification_artifacts" / "sacg_state.json",
            "backend_board": self.out / "debug_loop" / "sacg_state.json",
        }
        return self.file_tree_hash([stage_inputs.get(stage, self.out)])

    def checkpoint_path(self, stage: str) -> Path:
        return self.checkpoint_dir / f"{safe_id(stage)}.json"

    def latest_checkpoint_path(self) -> Path:
        return self.checkpoint_dir / "latest.json"

    def write_stage_checkpoint(
        self,
        *,
        stage: str,
        module: str,
        result: StageResult,
        report_path: Path | None,
        sacg_state: Path | None,
    ) -> None:
        checkpoint = {
            "schema_version": "spatialaccagent.stage_checkpoint.v0",
            "stage": stage,
            "module": module,
            "stage_code_hash": self.stage_code_hash(module),
            "stage_input_hash": self.stage_input_hash(stage),
            "status": "pass" if result.passed else "fail",
            "report_path": str(report_path) if report_path else result.output_path,
            "sacg_state": str(sacg_state) if sacg_state else None,
            "command_log": result.command_result.log_path,
            "summary_status": (result.summary or {}).get("status"),
            "reuse_policy": {
                "only_reuse_passed_stage": True,
                "require_matching_stage_code_hash": True,
                "require_matching_stage_input_hash": True,
                "require_ready_report": True,
                "failed_or_stale_artifacts_are_never_promoted": True,
            },
        }
        write_json(self.checkpoint_path(stage), checkpoint)
        write_json(
            self.latest_checkpoint_path(),
            {
                "schema_version": "spatialaccagent.latest_checkpoint.v0",
                "stage": stage,
                "status": checkpoint["status"],
                "report_path": checkpoint["report_path"],
                "sacg_state": checkpoint["sacg_state"],
            },
        )

    def reusable_stage_result(
        self,
        *,
        stage: str,
        module: str,
        report_path: Path,
        sacg_state: Path | None = None,
    ) -> StageResult | None:
        if not self.resume_enabled():
            return None
        checkpoint_path = self.checkpoint_path(stage)
        if not checkpoint_path.exists() or not report_path.exists():
            return None
        try:
            checkpoint = read_json(checkpoint_path)
            report = read_json(report_path)
        except Exception:
            return None
        if checkpoint.get("status") != "pass":
            return None
        if checkpoint.get("stage_code_hash") != self.stage_code_hash(module):
            return None
        if checkpoint.get("stage_input_hash") != self.stage_input_hash(stage):
            return None
        if report.get("status") not in {"ready", "pass"}:
            return None
        if sacg_state is not None and not sacg_state.exists():
            return None
        cmd = CommandResult(
            name=f"{stage}_resume",
            command=["checkpoint", "reuse", stage],
            cwd=str(self.root),
            returncode=0,
            stdout=f"reused checkpoint {checkpoint_path}\n",
            stderr="",
            duration_sec=0.0,
            log_path=str(checkpoint_path),
        )
        return StageResult(
            name=stage,
            passed=True,
            command_result=cmd,
            output_path=str(report_path),
            summary=report,
            safety_gate={"enabled": False, "decision": {"decision": "reuse_checkpoint", "tool_command_allowed": False}},
        )

    def record(self, result: StageResult) -> None:
        self.results.append(result)
        self.write_report(status="running" if result.passed else "failed")
        status = "pass" if result.passed else "fail"
        print(f"[agent] stage {result.name}: {status}", file=sys.stderr, flush=True)
        if result.output_path:
            print(f"[agent] output {result.output_path}", file=sys.stderr, flush=True)
        if result.summary:
            print(f"[agent] summary {result.name}: {compact_json(result.summary, 1200)}", file=sys.stderr, flush=True)

    def write_report(self, status: str) -> None:
        write_json(
            self.report_path,
            {
                "schema_version": "spatialaccagent.agent_run_report.v0",
                "agent": "TopAgent",
                "design_id": self.cfg.design,
                "run_dir": str(self.out),
                "status": status,
                "llm": {
                    "mode": "llm",
                    "model": self.cfg.llm.model,
                    "endpoint": self.cfg.llm.endpoint,
                    "enforce": True,
                    "mandatory": True,
                },
                "stages": [result.to_dict() for result in self.results],
                "flow_events": self.flow_events,
                "flow_state": {
                    "path": str(self.flow_state_path),
                    "stage_attempts": self.flow_state.get("stage_attempts", {}),
                    "backtrack_count": self.flow_state.get("backtrack_count", 0),
                },
            },
        )

    def stage_key_for_target(self, target_stage: str, stage_names: list[str]) -> str | None:
        value = str(target_stage or "").strip()
        if not value:
            return None
        if value in stage_names:
            return value
        if value in STAGE_TARGET_ALIASES:
            return STAGE_TARGET_ALIASES[value]
        for name in stage_names:
            if value.endswith(f".{name}"):
                return name
        return None

    def stage_state_path(self, report_dir: str) -> Path:
        return self.out / report_dir / "sacg_state.json"

    def report_state_path(self, result: StageResult) -> Path | None:
        outputs = (result.summary or {}).get("outputs", {})
        if isinstance(outputs, dict) and outputs.get("sacg_state"):
            path = Path(str(outputs["sacg_state"]))
            if path.exists():
                return path
        final_state = (result.summary or {}).get("final_sacg_state")
        if final_state:
            path = Path(str(final_state))
            if path.exists():
                return path
        return None

    def flow_controller_review(
        self,
        *,
        current_stage: str,
        result: StageResult,
        sacg_state: Path | None,
        stage_names: list[str],
        attempt_count: int,
    ) -> dict[str, Any]:
        state = read_json(sacg_state) if sacg_state and sacg_state.exists() else {}
        out_dir = self.out / "agent" / "flow_controller" / f"{len(self.flow_events) + 1:03d}_{safe_id(current_stage)}"
        inputs = {
            "current_stage": current_stage,
            "stage_passed": result.passed,
            "attempt_count": attempt_count,
            "available_stages": stage_names,
            "recent_stage_summary": result.summary or {},
            "command": result.command_result.command,
            "command_returncode": result.command_result.returncode,
            "command_log": result.command_result.log_path,
            "sacg_memory": sacg_memory_summary(state, limit=10) if state else {},
            "source_sacg_state": str(sacg_state) if sacg_state else "",
            "flow_policy": {
                "llm_is_required": True,
                "do_not_use_failed_artifacts_as_validated_downstream_inputs": True,
                "prefer_retry_same_stage_for_retry_requests": True,
                "honor_backtrack_requests_before_downstream_progress": True,
                "bounded_attempts_per_stage": MAX_STAGE_ATTEMPTS,
                "bounded_total_backtracks": MAX_FLOW_BACKTRACKS,
            },
        }
        with temporary_env(self.tool_env):
            record = run_stage_agent(
                agent="flow_controller_agent",
                stage="flow_orchestration",
                task=(
                    "Review SACG memory and the latest stage result, then decide whether the autonomous "
                    "design team should proceed, retry the current stage, backtrack to an earlier stage, "
                    "run bounded repair, or stop to avoid artifact contamination."
                ),
                inputs=inputs,
                out_dir=out_dir,
                fallback_summary="Flow controller must preserve SACG failure memory and avoid invalid downstream promotion.",
            )
        return {
            "agent_record": record.get("result_path"),
            "agent_status": (record.get("output") or {}).get("status"),
            "agent_summary": (record.get("output") or {}).get("summary"),
            "agent_executable_actions": (record.get("output") or {}).get("executable_actions", []),
        }

    def choose_next_stage(
        self,
        *,
        current_index: int,
        result: StageResult,
        sacg_state: Path | None,
        stage_specs: list[tuple[str, str, str, str]],
        attempt_counts: dict[str, int],
        backtrack_count: int,
    ) -> tuple[int | None, Path | None, dict[str, Any]]:
        current_stage = stage_specs[current_index][0]
        stage_names = [spec[0] for spec in stage_specs]
        state = read_json(sacg_state) if sacg_state and sacg_state.exists() else {}
        memory = state.get("memory", {}) if isinstance(state.get("memory"), dict) else {}
        llm_review = self.flow_controller_review(
            current_stage=current_stage,
            result=result,
            sacg_state=sacg_state,
            stage_names=stage_names,
            attempt_count=attempt_counts.get(current_stage, 0),
        )

        def open_items(name: str) -> list[dict[str, Any]]:
            values = memory.get(name, []) if isinstance(memory.get(name), list) else []
            return [item for item in values if isinstance(item, dict) and item.get("status") == "open"]

        event: dict[str, Any] = {
            "stage": current_stage,
            "stage_passed": result.passed,
            "sacg_state": str(sacg_state) if sacg_state else None,
            "llm_flow_controller": llm_review,
            "decision": "unset",
            "reason": "",
        }

        def llm_actions_for(action_type: str) -> list[dict[str, Any]]:
            actions = llm_review.get("agent_executable_actions", [])
            if not isinstance(actions, list):
                return []
            matched: list[dict[str, Any]] = []
            for action in actions:
                if not isinstance(action, dict):
                    continue
                if str(action.get("action_type") or "").strip() != action_type:
                    continue
                target = self.stage_key_for_target(str(action.get("target_stage") or action.get("stage") or ""), stage_names)
                if target in {None, current_stage}:
                    matched.append(action)
            return matched

        def llm_status_contains(text: str) -> bool:
            return text in str(llm_review.get("agent_status") or "").strip().lower()

        if open_items("backtrack_requests"):
            latest = open_items("backtrack_requests")[-1]
            target = self.stage_key_for_target(str(latest.get("target_stage") or ""), stage_names)
            if target is None:
                event.update(
                    {
                        "decision": "stop",
                        "reason": f"open backtrack request has no known target stage: {latest.get('target_stage')}",
                    }
                )
                return None, sacg_state, event
            target_index = stage_names.index(target)
            if backtrack_count >= MAX_FLOW_BACKTRACKS:
                event.update(
                    {
                        "decision": "stop",
                        "reason": f"bounded backtrack limit reached before target {target}",
                    }
                )
                return None, sacg_state, event
            event.update(
                {
                    "decision": "backtrack",
                    "reason": latest.get("reason", "SACG requested backtrack"),
                    "target_stage": target,
                    "target_index": target_index,
                    "request_id": latest.get("id"),
                }
            )
            return target_index, sacg_state, event

        if result.passed:
            next_index = current_index + 1
            event.update({"decision": "proceed", "reason": "stage passed and no open backtrack request"})
            return (next_index if next_index < len(stage_specs) else None), sacg_state, event

        retries = open_items("retry_requests")
        retry_current = [
            item
            for item in retries
            if self.stage_key_for_target(str(item.get("target_stage") or ""), stage_names) == current_stage
        ]
        if retry_current and attempt_counts.get(current_stage, 0) < MAX_STAGE_ATTEMPTS:
            latest = retry_current[-1]
            event.update(
                {
                    "decision": "retry",
                    "reason": latest.get("reason", "SACG requested retry"),
                    "target_stage": current_stage,
                    "target_index": current_index,
                    "request_id": latest.get("id"),
                }
            )
            return current_index, sacg_state, event

        llm_retry_actions = llm_actions_for("retry_current_stage")
        if (
            not result.passed
            and (llm_retry_actions or llm_status_contains("retry_current_stage"))
            and attempt_counts.get(current_stage, 0) < MAX_STAGE_ATTEMPTS
        ):
            latest = llm_retry_actions[-1] if llm_retry_actions else {}
            event.update(
                {
                    "decision": "retry",
                    "reason": latest.get("rationale")
                    or llm_review.get("agent_summary")
                    or "LLM flow controller requested bounded same-stage retry",
                    "target_stage": current_stage,
                    "target_index": current_index,
                    "request_id": latest.get("id"),
                    "source": "llm_flow_controller",
                }
            )
            return current_index, sacg_state, event

        if (
            not result.passed
            and (llm_retry_actions or llm_status_contains("retry_current_stage"))
            and attempt_counts.get(current_stage, 0) >= MAX_STAGE_ATTEMPTS
        ):
            event.update(
                {
                    "decision": "stop",
                    "reason": f"bounded stage retry limit reached after LLM flow controller requested retry: {current_stage}",
                    "source": "llm_flow_controller",
                }
            )
            return None, sacg_state, event

        retry_targets = [
            self.stage_key_for_target(str(item.get("target_stage") or ""), stage_names)
            for item in retries
        ]
        retry_targets = [target for target in retry_targets if target]
        if retry_targets and backtrack_count < MAX_FLOW_BACKTRACKS:
            target = retry_targets[-1]
            target_index = stage_names.index(target)
            event.update(
                {
                    "decision": "reroute_retry_target",
                    "reason": "SACG retry request targets a different stage",
                    "target_stage": target,
                    "target_index": target_index,
                }
            )
            return target_index, sacg_state, event

        if current_stage == "debug_loop":
            event.update(
                {
                    "decision": "stop",
                    "reason": "hierarchical debug loop failed; backend must not run until closed",
                }
            )
            return None, sacg_state, event

        event.update(
            {
                "decision": "stop",
                "reason": "stage failed and no bounded retry/backtrack/repair route is available",
            }
        )
        return None, sacg_state, event

    def run(self) -> bool:
        self.initialize_run_counters()
        self.write_report(status="running")

        input_report = self.out / "input" / "prepared_inputs.json"
        input_module = "accagent.framework.stage_input"
        input_result = self.reusable_stage_result(
            stage="input_preparation",
            module=input_module,
            report_path=input_report,
        )
        if input_result is None:
            input_agent = InputPreparationAgent(self.runner, self.tool_env)
            input_result = input_agent.run(
                out=self.out,
                task=self.cfg.task_spec,
                model_source=self.cfg.model_source,
                board_materials_dir=self.cfg.board_materials_dir,
                quantization_materials_dir=self.cfg.quantization_materials_dir,
                tool_materials_dir=self.cfg.tool_materials_dir,
                safety_gate=self.safety_gate,
            )
        self.record(input_result)
        self.write_stage_checkpoint(
            stage="input_preparation",
            module=input_module,
            result=input_result,
            report_path=input_report,
            sacg_state=None,
        )
        if not input_result.passed:
            self.write_report(status="failed")
            return False

        prepared_inputs = self.out / "input" / "prepared_inputs.json"
        constraint_module = "accagent.framework.stage_constraints"
        constraint_report = self.out / "constraint_extraction" / "constraint_extraction_report.json"
        constraint_state = self.out / "constraint_extraction" / "initial_design_graph.json"
        constraint_result = self.reusable_stage_result(
            stage="constraint_extraction",
            module=constraint_module,
            report_path=constraint_report,
            sacg_state=constraint_state,
        )
        if constraint_result is None:
            constraint_agent = ConstraintExtractionAgent(self.runner, self.tool_env)
            constraint_result = constraint_agent.run(prepared_inputs, self.cfg.design, safety_gate=self.safety_gate)
        self.record(constraint_result)
        self.write_stage_checkpoint(
            stage="constraint_extraction",
            module=constraint_module,
            result=constraint_result,
            report_path=constraint_report,
            sacg_state=constraint_state,
        )
        if not constraint_result.passed:
            self.write_report(status="failed")
            return False

        sacg_state = constraint_state
        template_module = "accagent.framework.stage_templates"
        template_report = self.out / "template_selection" / "template_selection_report.json"
        template_state = self.out / "template_selection" / "sacg_state.json"
        template_result = self.reusable_stage_result(
            stage="template_selection",
            module=template_module,
            report_path=template_report,
            sacg_state=template_state,
        )
        if template_result is None:
            template_agent = TemplateSelectionAgent(self.runner, self.tool_env)
            template_result = template_agent.run(sacg_state, safety_gate=self.safety_gate)
        self.record(template_result)
        self.write_stage_checkpoint(
            stage="template_selection",
            module=template_module,
            result=template_result,
            report_path=template_report,
            sacg_state=template_state,
        )
        if not template_result.passed:
            self.write_report(status="failed")
            return False

        stage_specs = [
            (
                "pipeline_planning",
                "accagent.framework.stage_pipeline",
                "pipeline_planning",
                "pipeline_planning_report.json",
            ),
            (
                "parameter_binding",
                "accagent.framework.stage_params",
                "parameter_binding",
                "parameter_binding_report.json",
            ),
            (
                "code_generation",
                "accagent.framework.stage_code_generation",
                "code_generation",
                "code_generation_report.json",
            ),
            (
                "verification_artifacts",
                "accagent.framework.stage_verification_plan",
                "verification_artifacts",
                "verification_artifacts_report.json",
            ),
            (
                "debug_loop",
                "accagent.framework.stage_debug_loop",
                "debug_loop",
                "debug_loop_report.json",
            ),
            (
                "backend_board",
                "accagent.framework.stage_backend",
                "backend_board",
                "backend_board_report.json",
            ),
        ]

        sacg_state = self.out / "template_selection" / "sacg_state.json"
        stage_index = 0
        self.hydrate_stage_attempts_from_logs([spec[0] for spec in stage_specs])
        while stage_index < len(stage_specs):
            name, module, report_dir, report_file = stage_specs[stage_index]
            active_attempt_count = self.stage_attempt_count(name, module)
            if active_attempt_count >= MAX_STAGE_ATTEMPTS:
                self.record_flow_event(
                    {
                        "stage": name,
                        "stage_passed": False,
                        "sacg_state": str(sacg_state) if sacg_state else None,
                        "decision": "stop",
                        "reason": f"persistent bounded attempt limit reached for {name}: {MAX_STAGE_ATTEMPTS}",
                        "attempt_count": active_attempt_count,
                        "legacy_failure_count": int(
                            self.flow_state.get("legacy_stage_failures", {}).get(name, 0) or 0
                        ),
                        "flow_state_path": str(self.flow_state_path),
                    }
                )
                self.write_report(status="failed")
                return False
            attempt_count = self.increment_stage_attempt(name, module)
            report_path = self.out / report_dir / report_file
            expected_state = self.stage_state_path(report_dir)
            stage_result = self.reusable_stage_result(
                stage=name,
                module=module,
                report_path=report_path,
                sacg_state=expected_state,
            )
            if stage_result is None:
                stage_agent = GenericStageAgent(self.runner, name, module, report_dir, report_file, self.tool_env)
                stage_result = stage_agent.run(sacg_state, safety_gate=self.safety_gate)
            self.record(stage_result)
            next_sacg_state = self.report_state_path(stage_result)
            if next_sacg_state is None:
                expected_state = self.stage_state_path(report_dir)
                next_sacg_state = expected_state if stage_result.passed and expected_state.exists() else sacg_state
            self.write_stage_checkpoint(
                stage=name,
                module=module,
                result=stage_result,
                report_path=report_path,
                sacg_state=next_sacg_state,
            )
            if stage_result.passed:
                self.reset_stage_attempt(name, module)
            if stage_result.passed and stage_result.command_result.command[:2] == ["checkpoint", "reuse"]:
                next_index = stage_index + 1
                self.record_flow_event(
                    {
                        "stage": name,
                        "stage_passed": True,
                        "sacg_state": str(next_sacg_state) if next_sacg_state else None,
                        "decision": "reuse_checkpoint_proceed",
                        "reason": "stage checkpoint passed with matching code hash and ready report",
                    }
                )
                self.write_report(status="running")
                sacg_state = next_sacg_state
                stage_index = next_index
                continue
            try:
                next_index, routed_state, event = self.choose_next_stage(
                    current_index=stage_index,
                    result=stage_result,
                    sacg_state=next_sacg_state,
                    stage_specs=stage_specs,
                    attempt_counts={name: attempt_count},
                    backtrack_count=int(self.flow_state.get("backtrack_count", 0) or 0),
                )
            except Exception as exc:
                self.record_flow_event(
                    {
                        "stage": name,
                        "stage_passed": stage_result.passed,
                        "sacg_state": str(next_sacg_state) if next_sacg_state else None,
                        "decision": "stop",
                        "reason": f"LLM flow controller failed: {exc}",
                    }
                )
                self.write_report(status="failed")
                return False
            event["attempt_count"] = attempt_count
            event["flow_state_path"] = str(self.flow_state_path)
            self.record_flow_event(event)
            self.write_report(status="running" if next_index is not None else ("ready" if stage_result.passed else "failed"))
            if next_index is None:
                if stage_result.passed:
                    break
                self.write_report(status="failed")
                return False
            if event.get("decision") in {"backtrack", "reroute_retry_target"}:
                self.flow_state["backtrack_count"] = int(self.flow_state.get("backtrack_count", 0) or 0) + 1
                self.save_flow_state()
            sacg_state = routed_state or next_sacg_state
            stage_index = next_index

        validation_agent = SACGValidationAgent(self.runner, self.tool_env)
        validation_result = validation_agent.run(sacg_state, safety_gate=self.safety_gate)
        self.record(validation_result)
        final_status = "ready" if validation_result.passed else "failed"
        self.write_report(status=final_status)
        return validation_result.passed


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        print("error: edit accagent/framework/config.py instead of passing CLI arguments", file=sys.stderr)
        return 2

    agent = TopAgent(CFG)
    passed = agent.run()
    print(agent.report_path)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
