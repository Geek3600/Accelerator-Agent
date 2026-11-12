"""MAGE-style top-level orchestration for SpatialAccAgent."""

from __future__ import annotations

import gzip
import shutil
import sys
import hashlib
import importlib.util
import json
import os
import tempfile
from dataclasses import replace
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
from accagent.framework.experiment_profile import (
    PROFILE_ENV as ACCORD_PROFILE_ENV,
    active_profile as active_accord_experiment_profile,
    without_design_graph_context,
    without_guided_repair_context,
)
from accagent.framework.stage_input_common import DEFAULT_TEMPLATE_DIR
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.workflow_contract import (
    STAGE_TARGET_ALIASES,
    public_stage,
    public_workflow_manifest,
)


def json_dumps_stable(data: object) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def is_formal_dse_backtrack(request: dict[str, Any], target_stage: str | None = None) -> bool:
    """Formal exact DSE measurements are not generic retry churn."""

    if not isinstance(request, dict):
        return False
    requested_target = str(request.get("target_stage") or "")
    if target_stage is not None and requested_target not in {target_stage, f"stage4.{target_stage}"}:
        return False
    return str(request.get("verification_scope") or "") == "formal_dse_campaign"


def is_framework_flow_failure(request: dict[str, Any]) -> bool:
    """Identify orchestration and evidence-identity failures that must not rewind design work."""

    if not isinstance(request, dict):
        return False
    framework_classes = {
        "agent_framework",
        "framework",
        "framework_bug",
        "orchestration",
        "orchestration_bug",
        "artifact_binding",
        "evidence_binding",
        "hash_drift",
        "manifest_hash_drift",
        "provenance_binding",
        "stage_routing",
    }
    for key in ("failure_category", "failure_class", "root_cause_class", "issue_type", "error_category"):
        value = str(request.get(key) or "").strip().lower().replace("-", "_").replace(" ", "_")
        if value in framework_classes or any(
            marker in value
            for marker in (
                "framework", "orchestration", "hash", "manifest", "provenance",
                "evidence_binding", "artifact_binding", "stage_routing",
            )
        ):
            return True

    diagnostic_parts: list[str] = []
    for key in (
        "reason",
        "summary",
        "error",
        "failure_reason",
        "root_cause",
        "missing_or_invalid_contracts",
        "failed_gates",
        "blocked_artifacts",
    ):
        value = request.get(key)
        if isinstance(value, list):
            diagnostic_parts.extend(str(item) for item in value)
        elif value is not None:
            diagnostic_parts.append(str(value))
    diagnostic = " ".join(diagnostic_parts).lower().replace("-", " ").replace("_", " ")
    markers = (
        "framework",
        "orchestration",
        "agent code",
        "agent implementation",
        "agent internal",
        "agent.py",
        "flow controller",
        "stage routing",
        "stage mapping",
        "provenance mismatch",
        "provenance binding",
        "evidence binding",
        "certificate binding",
        "artifact binding",
        "artifact identity mismatch",
        "source fingerprint mismatch",
        "projection mismatch",
        "stale evidence",
        "promotion certificate",
        "hash mismatch",
        "hash drift",
        "hash changed",
        "hash binding failed",
        "hash binding failure",
        "hash check failed",
        "hash verification failed",
        "sha256 mismatch",
        "checksum mismatch",
        "manifest drift",
        "manifest mismatch",
        "manifest sha mismatch",
        "manifest sha changed",
    )
    return any(marker in diagnostic for marker in markers)


def is_evidence_supported_design_backtrack(request: dict[str, Any]) -> bool:
    """Require an explicit design failure and linked evidence before rewinding stages."""

    if not isinstance(request, dict) or is_framework_flow_failure(request):
        return False
    category = str(
        request.get("failure_category")
        or request.get("failure_class")
        or request.get("root_cause_class")
        or ""
    ).strip().lower().replace("-", "_").replace(" ", "_")
    design_categories = {
        "design_defect",
        "hardware_design_failure",
        "design_target_miss",
        "timing_target_miss",
        "resource_limit_exceeded",
        "functional_design_failure",
        "rtl_design_failure",
        "performance_target_miss",
    }
    verification_scope = str(request.get("verification_scope") or "")
    design_optimization = verification_scope in {
        "formal_dse_campaign",
        "local_qor_optimization",
        "board_axi_ddr_closure",
        "single_layer_closure",
        "operator_leaf_closure",
    }
    if not design_optimization and category not in design_categories:
        return False
    evidence_keys = (
        "evidence", "evidence_paths", "failed_gates", "critical_path", "measured_metrics",
        "observed_metrics", "tool_results", "real_tool_results",
    )
    return any(request.get(key) for key in evidence_keys)


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
        self.tool_env = {
            "SPATIALACC_RUN_REAL_TOOLS": "1" if cfg.run_real_tools else "0",
            "SPATIALACC_TOOL_TIMEOUT_SEC": str(cfg.real_tool_timeout_sec),
            "SPATIALACC_LLM_MODE": "llm",
            "SPATIALACC_LLM_MODEL": cfg.llm.model,
            "SPATIALACC_LLM_ENDPOINT": cfg.llm.endpoint,
            "SPATIALACC_LLM_BASE_URL": cfg.llm.base_url,
            "SPATIALACC_LLM_WIRE_API": cfg.llm.wire_api,
            "SPATIALACC_LLM_API_KEY": cfg.llm.api_key,
            "SPATIALACC_LLM_FALLBACK_ENDPOINT": cfg.llm.fallback_endpoint,
            "SPATIALACC_LLM_FALLBACK_BASE_URL": cfg.llm.fallback_base_url,
            "SPATIALACC_LLM_FALLBACK_API_KEY": cfg.llm.fallback_api_key,
            "SPATIALACC_LLM_TIMEOUT_SEC": str(cfg.llm.timeout_sec),
            "SPATIALACC_LLM_REASONING_EFFORT": cfg.llm.reasoning_effort or "",
            "SPATIALACC_LLM_STORE": "1" if cfg.llm.store else "0",
            "SPATIALACC_LLM_TEXT_VERBOSITY": cfg.llm.text_verbosity or "",
            "SPATIALACC_LLM_STREAM": "1" if cfg.llm.stream else "0",
            "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED": os.environ.get(
                "SPATIALACC_LLM_TRANSIENT_RETRY_UNBOUNDED", "1"
            ),
            "SPATIALACC_LLM_RETRY_404_MODEL_ROUTE": os.environ.get("SPATIALACC_LLM_RETRY_404_MODEL_ROUTE", "1"),
            "SPATIALACC_LLM_LIMITER_DIR": str(self.out / "agent" / "llm_limiter"),
            "SPATIALACC_TEAM_LLM_WORKERS": "1",
        }
        if ACCORD_PROFILE_ENV in os.environ:
            self.tool_env[ACCORD_PROFILE_ENV] = active_accord_experiment_profile()
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
        source_sacg_path = Path(str(event.get("sacg_state") or ""))
        original_source_sacg_state = str(source_sacg_path)
        source_sacg_sha256 = ""
        if source_sacg_path.is_file():
            source_digest = hashlib.sha256()
            with source_sacg_path.open("rb") as source_file:
                for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                    source_digest.update(chunk)
            source_sacg_sha256 = source_digest.hexdigest()
            snapshot_path = (
                stage_dir
                / "flow_handoff_sources"
                / f"{source_sacg_sha256}.json.gz"
            )
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            if not snapshot_path.exists():
                fd, temporary_name = tempfile.mkstemp(
                    dir=snapshot_path.parent,
                    prefix=f".{source_sacg_sha256}.",
                    suffix=".tmp",
                )
                os.close(fd)
                try:
                    with source_sacg_path.open("rb") as source_file, gzip.open(
                        temporary_name, "wb", compresslevel=1
                    ) as snapshot_file:
                        shutil.copyfileobj(source_file, snapshot_file, length=1024 * 1024)
                    os.replace(temporary_name, snapshot_path)
                finally:
                    try:
                        os.unlink(temporary_name)
                    except FileNotFoundError:
                        pass
            event["source_sacg_state"] = original_source_sacg_state
            event["sacg_state"] = str(snapshot_path.resolve())
        flow_controller_result = Path(
            str(llm_review.get("agent_record") or "")
        )
        flow_controller_result_sha256 = ""
        if flow_controller_result.is_file():
            flow_controller_result_sha256 = hashlib.sha256(
                flow_controller_result.read_bytes()
            ).hexdigest()
        payload = {
            "schema_version": "spatialaccagent.flow_event_action_record.v0",
            "flow_event_index": event_index,
            "stage": event.get("stage"),
            "decision": event.get("decision"),
            "reason": event.get("reason"),
            "attempt_count": event.get("attempt_count"),
            "sacg_state": event.get("sacg_state"),
            "source_sacg_state": event.get("source_sacg_state"),
            "llm_flow_controller": llm_review,
            "executable_actions": [action for action in actions if isinstance(action, dict)],
            "source_identities": {
                "source_sacg_state_sha256": source_sacg_sha256,
                "flow_controller_result_sha256": flow_controller_result_sha256,
            },
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
                    "source_sacg_state": event.get("source_sacg_state"),
                    "action": action,
                    "source_flow_event": str(event_path),
                    "source_identities": payload["source_identities"],
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
                    self.cfg.model_dir,
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
        if stage == "parameter_binding":
            from accagent.framework.dse_calibration import SAMPLE_DIR
            from accagent.framework.dse_ledger import ledger_path

            return self.file_tree_hash([
                self.cfg.task_spec,
                self.out / "pipeline_planning" / "sacg_state.json",
                DEFAULT_TEMPLATE_DIR,
                Path(__file__).with_name("dse_estimator.py"),
                Path(__file__).with_name("dse_calibration.py"),
                ledger_path(self.out),
                SAMPLE_DIR,
            ])
        stage_inputs = {
            "pipeline_planning": self.out / "template_selection" / "sacg_state.json",
            "code_generation": [
                self.out / "parameter_binding" / "sacg_state.json",
                DEFAULT_TEMPLATE_DIR,
            ],
            "verification_artifacts": [
                self.out / "code_generation" / "sacg_state.json",
                self.out / "code_generation" / "code_generation_manifest.json",
                self.out / "code_generation" / "code_generation_report.json",
            ],
            "debug_loop": self.out / "verification_artifacts" / "sacg_state.json",
            "backend_board": [
                self.out / "debug_loop" / "sacg_state.json",
                self.out / "verification" / "sacg_state.json",
                self.out / "generated" / "chisel" / "vivado",
                self.out / "generated" / "chisel" / "scripts" / "gen_xilinx_fp_ips_23.tcl",
            ],
        }
        stage_input = stage_inputs.get(stage, self.out)
        if stage == "debug_loop":
            evidence_hash = self.file_tree_hash([stage_input])
            validation_policy = os.environ.get(
                "SPATIALACC_VERIFICATION_POLICY", "vcs_compile_only"
            )
            if validation_policy != "full_semantic_simulation":
                return evidence_hash
            return hashlib.sha256(
                f"{evidence_hash}\0{validation_policy}".encode("utf-8")
            ).hexdigest()
        if isinstance(stage_input, list):
            return self.file_tree_hash(stage_input)
        return self.file_tree_hash([stage_input])

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
                "require_matching_stage_code_and_input_hash_or_early_stage_semantic_revalidation": True,
                "require_ready_report": True,
                "allow_early_stage_semantic_revalidation_on_code_change": True,
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

    def semantic_revalidation_errors(self, stage: str, report_path: Path) -> list[str]:
        """Return current deterministic gate failures for code-change reuse.

        Early stages are closed artifacts with current deterministic rebuild
        checks.  Their LLM reviews are not replayed when those checks prove
        the same input graph and trusted-template bindings remain valid.
        """

        try:
            if stage == "input_preparation":
                from accagent.framework.stage_input import revalidate_prepared_inputs

                return revalidate_prepared_inputs(report_path)
            if stage == "constraint_extraction":
                from accagent.framework.stage_constraints import revalidate_constraint_extraction

                return revalidate_constraint_extraction(report_path)
            if stage == "template_selection":
                from accagent.framework.stage_templates import revalidate_template_selection

                return revalidate_template_selection(report_path)
            if stage == "pipeline_planning":
                from accagent.framework.stage_pipeline import revalidate_pipeline_planning

                return revalidate_pipeline_planning(report_path)
            if stage == "parameter_binding":
                from accagent.framework.stage_params import revalidate_parameter_binding

                return revalidate_parameter_binding(report_path)
        except Exception as exc:
            return [f"{stage} semantic checkpoint revalidation failed: {exc}"]
        return [f"{stage} has no semantic checkpoint revalidator"]

    def reusable_stage_result(
        self,
        *,
        stage: str,
        module: str,
        report_path: Path,
        sacg_state: Path | None = None,
        source_state: Path | None = None,
    ) -> StageResult | None:
        if not self.resume_enabled():
            return None
        if source_state is not None and source_state.is_file():
            try:
                source = read_json(source_state)
            except Exception:
                return None
            memory = source.get("memory", {}) if isinstance(source.get("memory"), dict) else {}
            for request in memory.get("backtrack_requests", []):
                if not isinstance(request, dict) or request.get("status") != "open":
                    continue
                if not is_evidence_supported_design_backtrack(request):
                    continue
                target = self.stage_key_for_target(
                    str(request.get("target_stage") or ""), [stage]
                )
                if target == stage:
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
        if report.get("status") not in {"ready", "pass"}:
            return None
        if stage == "backend_board" and (
            report.get("final_design_pass") is False
            or report.get("qor_optimization", {}).get("decision") in {"local_optimization", "dse_backtrack"}
        ):
            # A completed tool scope can still require a current-design repair.
            return None
        if stage == "backend_board":
            request_path = self.out / "backend_board/optimization_request.json"
            request = read_json(request_path) if request_path.is_file() else {}
            target = request.get("clock_frequency_mhz")
            clock = report.get("qor", {}).get("clock_frequency_mhz")
            if (request.get("scope") == "existing_design_timing"
                    and isinstance(target, (int, float)) and target > 0
                    and (not isinstance(clock, (int, float)) or clock < target)):
                return None
        if stage == "parameter_binding":
            from accagent.framework.dse_estimator import MODEL

            # A legal old binding is not a current optimization decision.
            rationale = report.get("dse_selection_rationale") or {}
            if (rationale.get("qor_estimator") or {}).get("model") != MODEL:
                return None
        if sacg_state is not None and not sacg_state.exists():
            return None
        reuse_kind = "exact_code_hash"
        code_hash_matches = checkpoint.get("stage_code_hash") == self.stage_code_hash(module)
        input_hash_matches = checkpoint.get("stage_input_hash") == self.stage_input_hash(stage)
        if not (code_hash_matches and input_hash_matches):
            errors = self.semantic_revalidation_errors(stage, report_path)
            if errors:
                return None
            reuse_kind = "semantic_revalidation"
        cmd = CommandResult(
            name=f"{stage}_resume_{reuse_kind}",
            command=["checkpoint", "reuse", stage, reuse_kind],
            cwd=str(self.root),
            returncode=0,
            stdout=f"reused checkpoint {checkpoint_path} ({reuse_kind})\n",
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
        )

    def record(self, result: StageResult) -> None:
        self.results.append(result)
        self.write_report(status="running" if result.passed else "failed")
        status = "pass" if result.passed else "fail"
        stage = public_stage(result.name)
        label = f"Stage {stage['id']} {stage['name']}" if stage["id"] is not None else "internal"
        print(f"[agent] {label} ({result.name}): {status}", file=sys.stderr, flush=True)
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
                "public_workflow": public_workflow_manifest(),
                "stages": [
                    {**result.to_dict(), "public_stage": public_stage(result.name)}
                    for result in self.results
                ],
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

    def stage_key_for_action(self, action: dict[str, Any], stage_names: list[str]) -> str | None:
        value = str(action.get("target_stage") or action.get("stage") or "").strip()
        target = self.stage_key_for_target(value, stage_names)
        if target != "code_generation" or value not in {
            "stage5",
            "stage5.hardware_implementation_and_verification_preparation",
        }:
            return target

        artifact_refs = {
            str(item)
            for key in ("consumes", "produces")
            for item in (action.get(key) if isinstance(action.get(key), list) else [])
        }
        verification_artifacts = {
            "artifact.stage5.verification_artifact_contract",
            "artifact.stage5.verification_plan",
            "artifact.stage5.llm_action_audit",
        }
        if artifact_refs.intersection(verification_artifacts):
            return "verification_artifacts"
        return target

    def stage_state_path(self, report_dir: str) -> Path:
        return self.out / report_dir / "sacg_state.json"

    def expected_stage_sacg_state(self, stage: str, report_dir: str) -> Path | None:
        """Return the promoted SACG artifact owned by one completed stage."""

        if stage == "input_preparation":
            return None
        if stage == "constraint_extraction":
            return self.out / report_dir / "initial_design_graph.json"
        return self.stage_state_path(report_dir)

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
            "stage_local_capabilities": {
                "backend_board": {
                    "run_local_timing_repair": "stage_backend invokes repair_timing_sources on current-run RTL after local_optimization is selected",
                    "compiled_pending_vcs": "the source-local patch and Chisel elaboration are complete; verify current sources compile-only, then return to Stage 7 synthesis",
                    "timing_repair_scope": "preserve Stage-4 parameters and shared templates; never restart code_generation for timing-only repair",
                }
            },
            "flow_policy": {
                "llm_is_required": True,
                "do_not_use_failed_artifacts_as_validated_downstream_inputs": True,
                "prefer_retry_same_stage_for_retry_requests": True,
                "honor_backtrack_requests_before_downstream_progress": True,
                "framework_hash_evidence_or_orchestration_failures_never_backtrack": True,
                "framework_failure_on_failed_stage_action": "retry_current_stage_without_rewinding_design",
                "design_backtrack_requires_explicit_failure_category_and_linked_evidence": True,
                "local_qor_optimization_is_an_evidence_supported_design_backtrack": True,
                "backend_timing_repair_does_not_need_a_planned_tool": True,
                "compiled_pending_vcs_must_not_restart_code_generation": True,
                "allowed_design_backtrack_categories": [
                    "design_defect",
                    "hardware_design_failure",
                    "design_target_miss",
                    "timing_target_miss",
                    "resource_limit_exceeded",
                    "functional_design_failure",
                    "rtl_design_failure",
                    "performance_target_miss",
                ],
                "stage_attempt_counters_are_observability_only": True,
                "backtrack_counters_are_observability_only": True,
                "framework_never_terminates_a_valid_llm_repair_or_replan_loop": True,
            },
        }
        experiment_profile = active_accord_experiment_profile()
        if experiment_profile == "B0":
            inputs = without_design_graph_context(inputs)
        elif experiment_profile == "B2":
            inputs = without_guided_repair_context(inputs)
        with temporary_env(self.tool_env):
            record = run_stage_agent(
                agent="flow_controller_agent",
                stage="flow_orchestration",
                task=(
                    "Review SACG memory and the latest stage result, then decide whether the autonomous "
                    "design team should proceed, retry the current stage, backtrack to an earlier stage, "
                    "run bounded repair, or stop to avoid artifact contamination. Framework, hash, "
                    "manifest, provenance, evidence-binding, or stage-routing failures must never "
                    "rewind hardware design stages; retry the failed current stage. Backtracking is "
                    "allowed only when the action names a hardware-design failure category and cites "
                    "failed gates, measurements, a critical path, or tool evidence. For backend timing, "
                    "use the run-local timing repair executed by Stage 7; when its status is "
                    "compiled_pending_vcs, request current-source compile-only verification and return "
                    "to Stage 7, never code_generation or parameter_binding."
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

        invalid_backtracks: list[dict[str, Any]] = []
        deferred_backtracks: list[dict[str, Any]] = []
        ignored_framework_backtracks: list[dict[str, Any]] = []
        ignored_unsupported_backtracks: list[dict[str, Any]] = []
        for latest in reversed(open_items("backtrack_requests")):
            if is_framework_flow_failure(latest):
                ignored_framework_backtracks.append(
                    {
                        "id": latest.get("id"),
                        "target_stage": latest.get("target_stage"),
                        "reason": latest.get("reason"),
                    }
                )
                if not result.passed:
                    event.update(
                        {
                            "decision": "retry_framework_failure_current_stage",
                            "reason": "framework/hash/evidence failure cannot rewind hardware design stages",
                            "target_stage": current_stage,
                            "target_index": current_index,
                            "ignored_framework_backtrack_request_id": latest.get("id"),
                        }
                    )
                    event["ignored_framework_backtrack_requests"] = ignored_framework_backtracks[:8]
                    return current_index, sacg_state, event
                continue
            if not is_evidence_supported_design_backtrack(latest):
                ignored_unsupported_backtracks.append(
                    {"id": latest.get("id"), "target_stage": latest.get("target_stage")}
                )
                continue
            target = self.stage_key_for_target(str(latest.get("target_stage") or ""), stage_names)
            if target is None:
                invalid_backtracks.append(
                    {
                        "id": latest.get("id"),
                        "target_stage": latest.get("target_stage"),
                    }
                )
                continue
            target_index = stage_names.index(target)
            if not result.passed and target_index > current_index:
                event.update({
                    "decision": "retry_replan",
                    "reason": "the current failed stage must pass before a later-stage request can run",
                    "deferred_request_id": latest.get("id"),
                    "target_stage": current_stage,
                    "target_index": current_index,
                })
                return current_index, sacg_state, event
            if result.passed and target_index == current_index:
                deferred_backtracks.append(
                    {"id": latest.get("id"), "target_stage": target}
                )
                continue
            if target_index > current_index:
                deferred_backtracks.append(
                    {"id": latest.get("id"), "target_stage": target}
                )
                continue
            formal_dse_campaign = is_formal_dse_backtrack(latest, target)
            event.update(
                {
                    "decision": "backtrack",
                    "reason": latest.get("reason", "SACG requested backtrack"),
                    "target_stage": target,
                    "target_index": target_index,
                    "request_id": latest.get("id"),
                    "formal_dse_campaign": formal_dse_campaign,
                }
            )
            return target_index, sacg_state, event
        if invalid_backtracks:
            event["ignored_invalid_backtrack_requests"] = invalid_backtracks[:8]
        if deferred_backtracks:
            event["deferred_backtrack_requests"] = deferred_backtracks[:8]
        if ignored_framework_backtracks:
            event["ignored_framework_backtrack_requests"] = ignored_framework_backtracks[:8]
        if ignored_unsupported_backtracks:
            event["ignored_unsupported_design_backtrack_requests"] = ignored_unsupported_backtracks[:8]

        if llm_status_contains("backtrack"):
            llm_backtrack_actions: list[tuple[dict[str, Any], str, int]] = []
            ignored_framework_actions: list[dict[str, Any]] = []
            ignored_unsupported_actions: list[dict[str, Any]] = []
            actions = llm_review.get("agent_executable_actions", [])
            if isinstance(actions, list):
                for action in actions:
                    if not isinstance(action, dict) or action.get("requires_approval") is True:
                        continue
                    if is_framework_flow_failure(action):
                        ignored_framework_actions.append(
                            {"id": action.get("id"), "target_stage": action.get("target_stage") or action.get("stage")}
                        )
                        continue
                    if not is_evidence_supported_design_backtrack(action):
                        ignored_unsupported_actions.append(
                            {"id": action.get("id"), "target_stage": action.get("target_stage") or action.get("stage")}
                        )
                        continue
                    target = self.stage_key_for_action(action, stage_names)
                    if target is None:
                        continue
                    target_index = stage_names.index(target)
                    if target_index >= current_index:
                        continue
                    llm_backtrack_actions.append((action, target, target_index))
            target_names = {target for _, target, _ in llm_backtrack_actions}
            if len(target_names) == 1:
                action, target, target_index = llm_backtrack_actions[-1]
                event.update(
                    {
                        "decision": "backtrack",
                        "reason": action.get("rationale")
                        or llm_review.get("agent_summary")
                        or "LLM flow controller requested a bounded earlier-stage repair",
                        "target_stage": target,
                        "target_index": target_index,
                        "request_id": action.get("id"),
                        "formal_dse_campaign": is_formal_dse_backtrack(action, target),
                        "source": "llm_flow_controller",
                    }
                )
                return target_index, sacg_state, event
            if ignored_framework_actions:
                event["ignored_framework_backtrack_actions"] = ignored_framework_actions[:8]
                if not result.passed:
                    event.update(
                        {
                            "decision": "retry_framework_failure_current_stage",
                            "reason": "LLM framework/hash/evidence repair action cannot rewind hardware design stages",
                            "target_stage": current_stage,
                            "target_index": current_index,
                        }
                    )
                    return current_index, sacg_state, event
            if ignored_unsupported_actions:
                event["ignored_unsupported_design_backtrack_actions"] = ignored_unsupported_actions[:8]

        if result.passed:
            next_index = current_index + 1
            event.update({"decision": "proceed", "reason": "stage passed with no unresolved earlier-stage backtrack"})
            return (next_index if next_index < len(stage_specs) else None), sacg_state, event

        retries = open_items("retry_requests")
        retry_current = [
            item
            for item in retries
            if self.stage_key_for_target(str(item.get("target_stage") or ""), stage_names) == current_stage
        ]
        if retry_current:
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

        retry_targets = [
            self.stage_key_for_target(str(item.get("target_stage") or ""), stage_names)
            for item in retries
        ]
        retry_targets = [target for target in retry_targets if target]
        if retry_targets:
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
                    "decision": "retry_replan",
                    "reason": (
                        "hierarchical debug loop is incomplete; rerun its current repair "
                        "scope so the LLM can replan from current real-tool evidence"
                    ),
                    "target_stage": current_stage,
                    "target_index": current_index,
                }
            )
            return current_index, sacg_state, event

        event.update(
            {
                "decision": "retry_replan",
                "reason": (
                    "stage failed without a valid route; keep the current stage active "
                    "and request a fresh LLM replan rather than terminating the flow"
                ),
                "target_stage": current_stage,
                "target_index": current_index,
            }
        )
        return current_index, sacg_state, event

    def run(self, *, start_stage: str | None = None, source_state: Path | None = None) -> bool:
        if self.cfg.model_source is None or self.cfg.model_dir is None:
            raise ValueError("a complete design run requires explicit model_source and model_dir inputs")
        stage_specs = [
            (
                "input_preparation",
                "accagent.framework.stage_input",
                "input",
                "prepared_inputs.json",
            ),
            (
                "constraint_extraction",
                "accagent.framework.stage_constraints",
                "constraint_extraction",
                "constraint_extraction_report.json",
            ),
            (
                "template_selection",
                "accagent.framework.stage_templates",
                "template_selection",
                "template_selection_report.json",
            ),
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

        stage_names = [spec[0] for spec in stage_specs]
        if start_stage is not None and start_stage not in stage_names:
            raise ValueError(f"unknown resume stage: {start_stage}")
        stage_index = stage_names.index(start_stage) if start_stage is not None else 0
        sacg_state = source_state.resolve() if source_state is not None else None
        if stage_index > 0 and (
            sacg_state is None or not sacg_state.is_file() or not sacg_state.is_relative_to(self.out)
        ):
            raise ValueError("resuming a later stage requires a current-run SACG state file")
        self.initialize_run_counters()
        self.write_report(status="running")
        self.hydrate_stage_attempts_from_logs(stage_names)
        while stage_index < len(stage_specs):
            name, module, report_dir, report_file = stage_specs[stage_index]
            attempt_count = self.increment_stage_attempt(name, module)
            report_path = self.out / report_dir / report_file
            expected_state = self.expected_stage_sacg_state(name, report_dir)
            stage_result = self.reusable_stage_result(
                stage=name,
                module=module,
                report_path=report_path,
                sacg_state=expected_state,
                source_state=sacg_state,
            )
            if stage_result is None:
                if name == "input_preparation":
                    stage_result = InputPreparationAgent(self.runner, self.tool_env).run(
                        out=self.out,
                        task=self.cfg.task_spec,
                        model_source=self.cfg.model_source,
                        model_dir=self.cfg.model_dir,
                        board_materials_dir=self.cfg.board_materials_dir,
                        quantization_materials_dir=self.cfg.quantization_materials_dir,
                        tool_materials_dir=self.cfg.tool_materials_dir,
                    )
                elif name == "constraint_extraction":
                    stage_result = ConstraintExtractionAgent(self.runner, self.tool_env).run(
                        self.out / "input" / "prepared_inputs.json",
                        self.cfg.design,
                    )
                elif name == "template_selection":
                    upstream_state = sacg_state or self.out / "constraint_extraction" / "initial_design_graph.json"
                    stage_result = TemplateSelectionAgent(self.runner, self.tool_env).run(upstream_state)
                else:
                    stage_agent = GenericStageAgent(self.runner, name, module, report_dir, report_file, self.tool_env)
                    stage_result = stage_agent.run(sacg_state)
            self.record(stage_result)
            next_sacg_state = self.report_state_path(stage_result)
            if name == "constraint_extraction" and stage_result.passed:
                next_sacg_state = self.out / "constraint_extraction" / "initial_design_graph.json"
            elif name == "template_selection" and stage_result.passed:
                next_sacg_state = self.out / "template_selection" / "sacg_state.json"
            elif next_sacg_state is None:
                next_sacg_state = sacg_state
            self.write_stage_checkpoint(
                stage=name,
                module=module,
                result=stage_result,
                report_path=report_path,
                sacg_state=next_sacg_state,
            )
            if stage_result.passed:
                self.reset_stage_attempt(name, module)

            stage_summary = stage_result.summary or {}
            if name == "backend_board" and stage_result.passed and stage_summary.get("final_design_pass") is True:
                request_path = self.out / "backend_board/optimization_request.json"
                request = read_json(request_path) if request_path.is_file() else {}
                if request.get("scope") == "existing_design_timing":
                    self.record_flow_event({
                        "stage": name, "stage_passed": True,
                        "sacg_state": str(next_sacg_state) if next_sacg_state else None,
                        "decision": "complete_existing_design_timing",
                        "reason": "Current source-bound QoR meets the requested timing scope and resource limits",
                    })
                    self.write_report(status="ready")
                    return True
            timing_source_repair = stage_summary.get("timing_source_repair")
            timing_patch_needs_vcs = (
                isinstance(timing_source_repair, dict)
                and timing_source_repair.get("status") == "compiled_pending_vcs"
            )
            stage6_refresh_required = name == "backend_board" and (
                stage_summary.get("stage6_refresh_required") is True
                or timing_patch_needs_vcs
                or any(
                    isinstance(item, dict) and item.get("source_change_requires_stage6_refresh") is True
                    for item in stage_summary.get("real_tool_results", [])
                )
            )
            if (name == "debug_loop" and stage_result.passed) or stage6_refresh_required:
                next_index = stage_names.index("debug_loop") if stage6_refresh_required else stage_index + 1
                self.record_flow_event({
                    "stage": name, "stage_passed": stage_result.passed,
                    "sacg_state": str(next_sacg_state) if next_sacg_state else None,
                    "decision": "refresh_stage6_compile_evidence" if stage6_refresh_required else "proceed_verified_stage6",
                    "target_stage": stage_names[next_index], "target_index": next_index,
                    "reason": "required current Stage-6 compile evidence" if stage6_refresh_required else "all Stage-6 verification scopes passed",
                })
                self.write_report(status="running")
                sacg_state = next_sacg_state
                stage_index = next_index
                continue

            # The first three stages have no architecture/workflow choice to
            # make after a clean pass.  Avoid spending an extra LLM call on a
            # no-op flow decision, but route every failure through the same
            # flow-controller logic as later stages.
            if stage_result.passed and stage_index < 3:
                self.record_flow_event(
                    {
                        "stage": name,
                        "stage_passed": True,
                        "sacg_state": str(next_sacg_state) if next_sacg_state else None,
                        "decision": "proceed_bootstrap_stage",
                        "reason": "bootstrap stage passed its deterministic gate",
                        "attempt_count": attempt_count,
                        "flow_state_path": str(self.flow_state_path),
                    }
                )
                self.write_report(status="running")
                sacg_state = next_sacg_state
                stage_index += 1
                continue

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
                        "decision": "retry_replan",
                        "reason": f"LLM flow controller failed transiently: {exc}",
                        "target_stage": name,
                        "target_index": stage_index,
                    }
                )
                self.write_report(status="running")
                sacg_state = next_sacg_state or sacg_state
                continue
            event["attempt_count"] = attempt_count
            event["flow_state_path"] = str(self.flow_state_path)
            self.record_flow_event(event)
            self.write_report(status="running" if next_index is not None else ("ready" if stage_result.passed else "running"))
            if next_index is None:
                if stage_result.passed:
                    break
                # A failed stage must never become a terminal framework state.
                # Keep its current SACG evidence and obtain a fresh LLM route.
                sacg_state = next_sacg_state or sacg_state
                continue
            if event.get("decision") in {"backtrack", "reroute_retry_target"}:
                self.flow_state["backtrack_count"] = int(self.flow_state.get("backtrack_count", 0) or 0) + 1
                self.save_flow_state()
            sacg_state = routed_state or next_sacg_state
            stage_index = next_index

        validation_agent = SACGValidationAgent(self.runner, self.tool_env)
        validation_result = validation_agent.run(sacg_state)
        self.record(validation_result)
        final_status = "ready" if validation_result.passed else "failed"
        self.write_report(status=final_status)
        return validation_result.passed


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    import argparse

    parser = argparse.ArgumentParser(description="Run one complete SpatialAccAgent design flow")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--design", required=True)
    parser.add_argument("--task-spec", type=Path, required=True)
    parser.add_argument("--model-source", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--board-materials-dir", type=Path, default=CFG.board_materials_dir)
    parser.add_argument("--quantization-materials-dir", type=Path, default=CFG.quantization_materials_dir)
    parser.add_argument("--tool-materials-dir", type=Path, default=CFG.tool_materials_dir)
    parser.add_argument("--tool-timeout-sec", type=int, default=CFG.real_tool_timeout_sec)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--start-stage", help="resume the flow controller at a current stage without replaying earlier stages")
    parser.add_argument("--sacg-state", type=Path, help="current-run state required with a later --start-stage")
    parsed = parser.parse_args(args)
    cfg = replace(
        CFG,
        out=parsed.run_dir,
        design=parsed.design,
        task_spec=parsed.task_spec,
        model_source=parsed.model_source,
        model_dir=parsed.model_dir,
        board_materials_dir=parsed.board_materials_dir,
        quantization_materials_dir=parsed.quantization_materials_dir,
        tool_materials_dir=parsed.tool_materials_dir,
        real_tool_timeout_sec=parsed.tool_timeout_sec,
        resume_existing=not parsed.no_resume,
    )
    agent = TopAgent(cfg)
    passed = agent.run(start_stage=parsed.start_stage, source_state=parsed.sacg_state)
    print(agent.report_path)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
