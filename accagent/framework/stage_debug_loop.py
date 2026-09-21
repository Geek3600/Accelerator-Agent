"""Run the hierarchical hardware verification/repair loop.

This orchestrates the Stage 6 verification/repair closure. It does not make
hardware-debug decisions itself; the LLM repair agents own analysis and
bounded actions.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from accagent.framework.sacg_utils import artifact_path, run_dir_from_state, write_json
from accagent.framework.stage_repair import plan_repair
from accagent.framework.stage_repair_execute import (
    prepare_stage3_checkpoint_probe_environment,
    run_repair_loop,
)
from accagent.framework.stage_verification import run_verification
from accagent.framework.verification_evidence_contract import (
    certificate_contract_errors,
    evidence_contract_for_level,
)


def ns(**kwargs: Any) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def scope_sequence(target_scope: str) -> list[str]:
    target = (target_scope or "board_axi_ddr_closure").strip().lower()
    order = ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"]
    aliases = {
        "operator_leaf": "operator_leaf_closure",
        "leaf": "operator_leaf_closure",
        "single_layer": "single_layer_closure",
        "stage6_single_layer": "single_layer_closure",
        "multilayer": "board_axi_ddr_closure",
        "multilayer_closure": "board_axi_ddr_closure",
        "axi_ddr": "board_axi_ddr_closure",
        "axi_ddr_closure": "board_axi_ddr_closure",
        "board_axi_ddr": "board_axi_ddr_closure",
        "functional": "board_axi_ddr_closure",
        "functional_sim": "board_axi_ddr_closure",
        "stage6_functional": "board_axi_ddr_closure",
    }
    target = aliases.get(target, target)
    if target in order:
        return order[: order.index(target) + 1]
    if target in {"all", "*"}:
        return order
    return order


SCOPE_PROMOTION_CERTIFICATES = {
    "operator_leaf_closure": "artifact.stage6.operator_leaf_promotion_certificate",
    "single_layer_closure": "artifact.stage6.single_layer_promotion_certificate",
    "board_axi_ddr_closure": "artifact.stage6.board_axi_ddr_promotion_certificate",
}

SCOPE_SELECTOR_KEYS = {
    "operator_leaf_closure": "operator_leaf_promotion_certificate",
    "single_layer_closure": "single_layer_promotion_certificate",
    "board_axi_ddr_closure": "board_axi_ddr_promotion_certificate",
}

SCOPE_LEVEL_IDS = {
    "operator_leaf_closure": "operator_leaf_functional",
    "single_layer_closure": "single_layer_functional",
    "board_axi_ddr_closure": "axi_ddr_functional",
}


def artifact_by_id(state: dict[str, Any], artifact_id: str) -> dict[str, Any] | None:
    for artifact in state.get("artifacts", []):
        if isinstance(artifact, dict) and artifact.get("id") == artifact_id:
            return artifact
    return None


def transition_status(state: dict[str, Any], transition_id: str | None) -> str:
    if not transition_id:
        return ""
    for transition in state.get("transitions", []):
        if isinstance(transition, dict) and transition.get("id") == transition_id:
            return str(transition.get("status") or "")
    return ""


def validated_scope_certificate(state: dict[str, Any], scope: str) -> dict[str, Any] | None:
    artifact_id = SCOPE_PROMOTION_CERTIFICATES.get(scope)
    if not artifact_id:
        return None
    artifact = artifact_by_id(state, artifact_id)
    if not artifact:
        return None
    if artifact.get("trust_status") == "rejected_producer":
        return None
    if transition_status(state, artifact.get("producer_transition")) != "promoted":
        return None
    path = Path(str(artifact.get("path") or ""))
    if not path.exists():
        return None
    try:
        payload = read_json(path)
    except Exception:
        return None
    if payload.get("status") != "pass":
        return None
    selector_artifact = artifact_by_id(state, "artifact.stage5.stage6_gate_selector_contract")
    selector_path = Path(str(selector_artifact.get("path") or "")) if selector_artifact else Path()
    selector = read_json(selector_path) if selector_artifact and selector_path.exists() else {}
    selector_key = SCOPE_SELECTOR_KEYS.get(scope, "")
    selector_spec = selector.get(selector_key, {}) if isinstance(selector.get(selector_key), dict) else {}
    level_id = SCOPE_LEVEL_IDS.get(scope, str(payload.get("level_id") or ""))
    required_gates = [str(gate) for gate in selector_spec.get("required_gates", []) if str(gate)]
    if selector_spec.get("evidence_contract") != evidence_contract_for_level(level_id):
        return None
    if certificate_contract_errors(payload, level_id, required_gates):
        return None
    return {
        "scope": scope,
        "artifact_id": artifact_id,
        "artifact_path": str(path),
        "producer_transition": artifact.get("producer_transition"),
        "evidence_contract": payload.get("evidence_contract"),
        "evidence_contract_fingerprint": payload.get("evidence_contract_fingerprint"),
    }


def reusable_scope_prefix(state: dict[str, Any], scopes: list[str]) -> list[str]:
    reusable: list[str] = []
    for scope in scopes:
        if not validated_scope_certificate(state, scope):
            break
        reusable.append(scope)
    return reusable


def targeted_lower_layer_backtrack_completed(run_dir: Path) -> bool:
    """Do not pin lower certificates after an explicit agent backtrack."""

    path = run_dir / "repair_execution" / "repair_execution_report.json"
    if not path.is_file():
        return False
    try:
        report = read_json(path)
    except Exception:
        return False
    for row in report.get("step_results", []):
        if not isinstance(row, dict) or row.get("scope") != "targeted_lower_layer_backtrack":
            continue
        result = row.get("result", {}) if isinstance(row.get("result"), dict) else {}
        if result.get("status") in {"pass", "ready", "complete"}:
            return True
    return False


def reusable_scope_checkpoint_prefix(
    state: dict[str, Any],
    run_dir: Path,
    target_scope: str,
    scopes: list[str],
) -> list[str]:
    """Recover the last scope-entry certificate decision without replaying tools."""

    if targeted_lower_layer_backtrack_completed(run_dir):
        return []
    candidates = [
        run_dir / "debug_loop" / "active_scope.json",
        run_dir / "debug_loop" / "debug_loop_report.json",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            checkpoint = read_json(path)
        except Exception:
            continue
        if checkpoint.get("target_scope") != target_scope:
            continue
        declared_scopes = checkpoint.get("reused_scopes", [])
        if not isinstance(declared_scopes, list) or not declared_scopes:
            legacy_rows = checkpoint.get("skipped_reusable_scopes", [])
            declared_scopes = [
                str(row.get("scope"))
                for row in legacy_rows
                if isinstance(row, dict) and row.get("scope")
            ]
        if not isinstance(declared_scopes, list):
            continue
        recovered: list[str] = []
        for expected_scope, declared_scope in zip(scopes, declared_scopes):
            if declared_scope != expected_scope:
                break
            artifact_id = SCOPE_PROMOTION_CERTIFICATES.get(expected_scope)
            artifact = artifact_by_id(state, str(artifact_id or ""))
            certificate_path = Path(str((artifact or {}).get("path") or ""))
            if (
                not artifact
                or artifact.get("trust_status") != "validated"
                or not certificate_path.is_file()
            ):
                break
            try:
                certificate = read_json(certificate_path)
            except Exception:
                break
            if certificate.get("status") != "pass":
                break
            recovered.append(expected_scope)
        if recovered:
            return recovered
    return []


class stage6_scope_env:
    def __init__(
        self,
        scope: str,
        timeout_sec: int | None = None,
        reused_scopes: list[str] | None = None,
    ) -> None:
        self.scope = scope
        self.timeout_sec = timeout_sec
        self.reused_scopes = list(reused_scopes or [])
        self.previous_gate_scope: str | None = None
        self.previous_execution_scope: str | None = None
        self.previous_tool_timeout: str | None = None
        self.previous_semantic_timeout: str | None = None
        self.previous_reused_scopes: str | None = None

    def __enter__(self) -> None:
        self.previous_gate_scope = os.environ.get("SPATIALACC_STAGE6_GATE_SCOPE")
        self.previous_execution_scope = os.environ.get("SPATIALACC_VERIFICATION_EXECUTION_SCOPE")
        self.previous_tool_timeout = os.environ.get("SPATIALACC_TOOL_TIMEOUT_SEC")
        self.previous_semantic_timeout = os.environ.get("SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC")
        self.previous_reused_scopes = os.environ.get("SPATIALACC_DEBUG_LOOP_REUSED_SCOPES")
        os.environ["SPATIALACC_STAGE6_GATE_SCOPE"] = self.scope
        os.environ["SPATIALACC_VERIFICATION_EXECUTION_SCOPE"] = self.scope
        os.environ["SPATIALACC_DEBUG_LOOP_REUSED_SCOPES"] = ",".join(self.reused_scopes)
        if self.timeout_sec is not None:
            os.environ["SPATIALACC_TOOL_TIMEOUT_SEC"] = str(self.timeout_sec)
            os.environ["SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC"] = str(self.timeout_sec)

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.previous_gate_scope is None:
            os.environ.pop("SPATIALACC_STAGE6_GATE_SCOPE", None)
        else:
            os.environ["SPATIALACC_STAGE6_GATE_SCOPE"] = self.previous_gate_scope
        if self.previous_execution_scope is None:
            os.environ.pop("SPATIALACC_VERIFICATION_EXECUTION_SCOPE", None)
        else:
            os.environ["SPATIALACC_VERIFICATION_EXECUTION_SCOPE"] = self.previous_execution_scope
        if self.previous_tool_timeout is None:
            os.environ.pop("SPATIALACC_TOOL_TIMEOUT_SEC", None)
        else:
            os.environ["SPATIALACC_TOOL_TIMEOUT_SEC"] = self.previous_tool_timeout
        if self.previous_semantic_timeout is None:
            os.environ.pop("SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC", None)
        else:
            os.environ["SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC"] = self.previous_semantic_timeout
        if self.previous_reused_scopes is None:
            os.environ.pop("SPATIALACC_DEBUG_LOOP_REUSED_SCOPES", None)
        else:
            os.environ["SPATIALACC_DEBUG_LOOP_REUSED_SCOPES"] = self.previous_reused_scopes


class temporary_process_env:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = {
            str(key): str(value)
            for key, value in values.items()
            if value is not None
        }
        self.previous: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self.values.items():
            self.previous[key] = os.environ.get(key)
            os.environ[key] = value

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_stage6_verification(
    *,
    current_state: Path,
    run_dir: Path,
    active_scope: str,
    timeout_sec: int,
    reused_scopes: list[str],
    iteration_index: int,
) -> tuple[Path | None, dict[str, Any] | None, dict[str, Any]]:
    """Run one Stage-6 scope with mandatory Layer-3 checkpoint execution."""

    checkpoint_preparation: dict[str, Any] = {
        "status": "not_required",
        "summary": "checkpoint execution is only required for Layer 3",
        "env": {},
        "remote_tool_must_not_start": False,
    }
    if active_scope == "board_axi_ddr_closure":
        checkpoint_preparation = prepare_stage3_checkpoint_probe_environment(
            run_dir,
            label=f"stage6_iteration_{iteration_index:04d}",
        )
        if checkpoint_preparation.get("status") != "pass":
            return None, None, checkpoint_preparation

    with stage6_scope_env(
        active_scope,
        timeout_sec,
        reused_scopes=reused_scopes,
    ), temporary_process_env(dict(checkpoint_preparation.get("env") or {})):
        verification_path, verification_report = run_verification(
            ns(sacg_state=current_state)
        )
    return verification_path, verification_report, checkpoint_preparation


def pending_repair_execution_resume(
    state: dict[str, Any], run_dir: Path | None = None
) -> dict[str, Any] | None:
    """Return one executor retry when planning already completed unchanged."""

    try:
        plan_path = artifact_path(state, "artifact.stage6.repair_plan")
        execution_path = artifact_path(state, "artifact.stage6.repair_execution_report")
    except Exception:
        return None
    if not plan_path.is_file() or not execution_path.is_file():
        return None
    plan = read_json(plan_path)
    execution = read_json(execution_path)
    workflow = plan.get("repair_workflow", {})
    steps = workflow.get("steps", []) if isinstance(workflow, dict) else []
    if (
        plan.get("status") != "needs_repair"
        or not isinstance(workflow, dict)
        or workflow.get("status") != "ready"
        or not steps
        or execution.get("stage") != "repair_execution"
        or execution.get("status") != "incomplete"
        or not execution.get("errors")
    ):
        return None
    if run_dir is not None and any(
        isinstance(step, dict)
        and isinstance(step.get("action"), dict)
        and step["action"].get("repair_kind") == "exact_board_interface_discovery"
        for step in steps
    ):
        identity_path = (
            run_dir
            / "verification"
            / "board_interface"
            / "board_source_identity.json"
        )
        if identity_path.is_file():
            from accagent.framework.board_acceptance_contract import (
                validate_exact_board_identity,
            )

            if validate_exact_board_identity(identity_path).get("status") == "pass":
                # The persisted repair plan was generated from an older failed
                # discovery result. Re-enter Stage 6 so its current plan can
                # consume the validated identity instead of replaying the
                # obsolete producer action.
                return None
    for row in execution.get("step_results", []):
        result = row.get("result", {}) if isinstance(row, dict) else {}
        capabilities = (
            result.get("required_capabilities", [])
            if isinstance(result, dict)
            else []
        )
        if (
            isinstance(result, dict)
            and result.get("framework_action_required") is True
            and isinstance(capabilities, list)
            and capabilities
            and all(
                isinstance(capability, dict)
                and capability.get("producer_scope")
                == "framework_execution_environment"
                for capability in capabilities
            )
        ):
            # An environment-only refusal has no hardware edit or tool evidence
            # to replay. Re-enter Stage7 so its current tool report is refreshed.
            return None
    return {
        "repair_plan": plan_path,
        "repair_execution_report": execution_path,
        "execution": execution,
    }


def repair_execution_has_new_real_tool_evidence(report: dict[str, Any]) -> bool:
    return any(
        isinstance(row, dict)
        and isinstance(row.get("result"), dict)
        and row["result"].get("new_current_real_tool_failure_requires_agent") is True
        for row in report.get("step_results", [])
    )


def repair_execution_requires_fresh_agent_planning(report: dict[str, Any]) -> bool:
    """Route unresolved Agent-owned capabilities through fresh Stage 6 evidence."""

    for row in report.get("step_results", []):
        result = row.get("result", {}) if isinstance(row, dict) else {}
        capabilities = (
            result.get("required_capabilities", [])
            if isinstance(result, dict)
            else []
        )
        if (
            not isinstance(result, dict)
            or result.get("status") != "blocked"
            or result.get("framework_action_required") is not True
            or not isinstance(capabilities, list)
        ):
            continue
        if any(
            isinstance(capability, dict)
            and str(capability.get("producer_scope") or "")
            not in {"", "framework_execution_environment"}
            for capability in capabilities
        ):
            return True
    return False


def deterministic_repair_followup_key(report: dict[str, Any]) -> str | None:
    """Identify a new deterministic board-preflight frontier for the same plan."""

    for row in report.get("step_results", []):
        result = row.get("result", {}) if isinstance(row, dict) else {}
        if not isinstance(result, dict):
            continue
        patch_path = Path(str(result.get("agent_patch_application") or ""))
        materialization_path = Path(
            str(result.get("dut_weight_binding_materialization") or "")
        )
        if not patch_path.is_file() or not materialization_path.is_file():
            continue
        patch = read_json(patch_path)
        materialization = read_json(materialization_path)
        blockers = materialization.get("blockers", [])
        if (
            patch.get("status") != "pass"
            or materialization.get("status") != "incomplete"
            or not isinstance(blockers, list)
            or not blockers
        ):
            continue
        return json.dumps(
            {
                "manifest_sha256": materialization.get("manifest_sha256"),
                "blockers": blockers,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    return None


def agent_transaction_retry_key(report: dict[str, Any]) -> str | None:
    """Identify one deterministic no-tool Agent transaction rejection."""

    for row in report.get("step_results", []):
        result = row.get("result", {}) if isinstance(row, dict) else {}
        if not isinstance(result, dict):
            continue
        patch_path = Path(str(result.get("agent_patch_application") or ""))
        if not patch_path.is_file():
            continue
        patch = read_json(patch_path)
        rejection = patch.get("agent_transaction_rejection", {})
        if not (
            patch.get("status") == "blocked"
            and patch.get("retry_agent_without_real_tool") is True
            and isinstance(rejection, dict)
            and rejection.get("status") == "ready_for_agent_retry"
            and rejection.get("real_tool_replay_required_before_retry") is False
            and patch.get("files") == []
        ):
            continue
        return json.dumps(
            {
                "failure_class": rejection.get("failure_class"),
                "unchanged_pre_edit_files": rejection.get(
                    "unchanged_pre_edit_files", []
                ),
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    return None


def debug_loop(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    current_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(current_state)
    out_dir = run_dir / "debug_loop"
    out_dir.mkdir(parents=True, exist_ok=True)
    iterations: list[dict[str, Any]] = []
    status = "running"
    summary = ""
    scopes = scope_sequence(args.target_scope)
    initial_state_data = read_json(current_state)
    live_reusable_scopes = reusable_scope_prefix(initial_state_data, scopes)
    checkpoint_reusable_scopes = reusable_scope_checkpoint_prefix(
        initial_state_data,
        run_dir,
        args.target_scope,
        scopes,
    )
    reused_scopes = max(
        (live_reusable_scopes, checkpoint_reusable_scopes),
        key=len,
    )
    scope_index = len(reused_scopes)
    active_scope_path = out_dir / "active_scope.json"
    write_json(
        active_scope_path,
        {
            "target_scope": args.target_scope,
            "reused_scopes": reused_scopes,
        },
    )
    executor_resume = pending_repair_execution_resume(initial_state_data, run_dir)
    deterministic_followup_keys: set[str] = set()
    if scope_index >= len(scopes):
        status = "pass"
        summary = f"hierarchical debug loop reused validated certificates through target_scope={args.target_scope}"
    index = 0
    while args.max_iters <= 0 or index < args.max_iters:
        if scope_index >= len(scopes):
            break
        active_scope = scopes[min(scope_index, len(scopes) - 1)]
        iteration: dict[str, Any] = {
            "index": index,
            "input_sacg_state": str(current_state),
            "stage6_scope": active_scope,
            "target_scope": args.target_scope,
        }
        try:
            if executor_resume is not None:
                resumed_execution = executor_resume
                execute_path, execute_report = run_repair_loop(
                    ns(
                        sacg_state=current_state,
                        execute_reruns=True,
                        include_remote=args.include_remote,
                        timeout_sec=args.timeout_sec,
                        max_loop_iters=0,
                    )
                )
                execute_state = run_dir / "repair_execution" / "sacg_state.json"
                iteration["repair_execution_resumed"] = True
                iteration["resumed_repair_plan"] = str(resumed_execution["repair_plan"])
                iteration["prior_repair_execution_report"] = str(
                    resumed_execution["repair_execution_report"]
                )
                iteration["repair_execution_report"] = str(execute_path)
                iteration["repair_execution_status"] = execute_report.get("status")
                iteration["repair_execution_errors"] = execute_report.get("errors", [])
                iterations.append(iteration)
                executor_resume = None
                current_state = execute_state if execute_state.exists() else current_state
                if execute_report.get("errors"):
                    if repair_execution_has_new_real_tool_evidence(execute_report):
                        iteration["same_plan_real_tool_followup"] = True
                        executor_resume = {
                            "repair_plan": resumed_execution["repair_plan"],
                            "repair_execution_report": execute_path,
                            "execution": execute_report,
                        }
                        continue
                    transaction_key = agent_transaction_retry_key(execute_report)
                    if transaction_key is not None:
                        iteration["agent_transaction_rejected"] = True
                        iteration["fresh_stage6_agent_replan"] = True
                        iteration["fresh_stage6_agent_replan_reason"] = (
                            "the prior transaction was rejected before a source write; "
                            "replan from the current observation evidence"
                        )
                        continue
                    followup_key = deterministic_repair_followup_key(execute_report)
                    if (
                        followup_key is not None
                        and followup_key not in deterministic_followup_keys
                    ):
                        deterministic_followup_keys.add(followup_key)
                        iteration["deterministic_repair_followup"] = True
                        executor_resume = {
                            "repair_plan": resumed_execution["repair_plan"],
                            "repair_execution_report": execute_path,
                            "execution": execute_report,
                        }
                        continue
                    if repair_execution_requires_fresh_agent_planning(execute_report):
                        iteration["fresh_stage6_agent_replan"] = True
                        iteration["fresh_stage6_agent_replan_reason"] = (
                            "an unresolved Agent-owned capability must be replanned "
                            "against current Stage 6 evidence"
                        )
                        continue
                    iteration["fresh_stage6_agent_replan"] = True
                    iteration["fresh_stage6_agent_replan_reason"] = (
                        "repair execution did not complete; obtain a fresh LLM plan "
                        "from the current real-tool evidence"
                    )
                    index += 1
                    continue
                continue
            verification_path, verification_report, checkpoint_preparation = (
                run_stage6_verification(
                    current_state=current_state,
                    run_dir=run_dir,
                    active_scope=active_scope,
                    timeout_sec=args.timeout_sec,
                    reused_scopes=reused_scopes,
                    iteration_index=index,
                )
            )
            iteration["checkpoint_preparation"] = {
                key: checkpoint_preparation.get(key)
                for key in (
                    "status",
                    "summary",
                    "request_path",
                    "request_sha256",
                    "checkpoint_enabled",
                    "cold_fallback",
                    "remote_tool_must_not_start",
                )
            }
            if verification_path is None or verification_report is None:
                iterations.append(iteration)
                iteration["fresh_stage6_agent_replan"] = True
                iteration["fresh_stage6_agent_replan_reason"] = (
                    "verification preparation produced no report; retry the same "
                    "scope without creating a terminal framework state"
                )
                index += 1
                continue
            verification_state = Path(str(verification_report["outputs"]["sacg_state"]))
            iteration["verification_report"] = str(verification_path)
            iteration["verification_status"] = verification_report.get("status")
            iteration["hierarchical_repair_loop"] = verification_report.get("hierarchical_repair_loop")
            if verification_report.get("status") == "ready":
                current_state = verification_state
                iterations.append(iteration)
                if scope_index >= len(scopes) - 1:
                    status = "pass"
                    summary = f"hierarchical debug loop passed through target_scope={args.target_scope}"
                    break
                scope_index += 1
                promoted_scope = scopes[scope_index - 1]
                promoted_certificate = validated_scope_certificate(
                    read_json(current_state),
                    promoted_scope,
                )
                if promoted_certificate and len(reused_scopes) < scope_index:
                    reused_scopes.append(promoted_scope)
                write_json(
                    active_scope_path,
                    {
                        "target_scope": args.target_scope,
                        "reused_scopes": reused_scopes,
                    },
                )
                continue

            repair_path, repair_report = plan_repair(ns(sacg_state=verification_state))
            repair_state = Path(str(repair_report["outputs"]["sacg_state"]))
            iteration["repair_report"] = str(repair_path)
            iteration["repair_status"] = repair_report.get("status")
            repair_plan_path = Path(str(repair_report.get("outputs", {}).get("repair_plan") or ""))
            repair_plan = read_json(repair_plan_path) if repair_plan_path.exists() else {}
            workflow = repair_plan.get("repair_workflow", {}) if isinstance(repair_plan.get("repair_workflow"), dict) else {}
            workflow_status = str(workflow.get("status") or "missing")
            plan_status = str(repair_plan.get("status") or repair_report.get("repair_status") or "missing")
            iteration["repair_plan"] = str(repair_plan_path) if repair_plan_path else None
            iteration["repair_plan_status"] = plan_status
            iteration["repair_workflow_status"] = workflow_status
            workflow_ready = plan_status == "needs_repair" and workflow_status == "ready"
            if plan_status == "ready":
                current_state = repair_state
                iterations.append(iteration)
                iteration["fresh_stage6_agent_replan"] = True
                iteration["fresh_stage6_agent_replan_reason"] = (
                    "verification failed but the previous plan had no repair action; "
                    "request a fresh LLM plan from current evidence"
                )
                index += 1
                continue
            if not workflow_ready:
                current_state = repair_state
                iterations.append(iteration)
                iteration["fresh_stage6_agent_replan"] = True
                iteration["fresh_stage6_agent_replan_reason"] = (
                    f"repair workflow was not executable (plan={plan_status}, "
                    f"workflow={workflow_status}); request a new current-evidence plan"
                )
                index += 1
                continue

            execute_path, execute_report = run_repair_loop(
                ns(
                    sacg_state=repair_state,
                    execute_reruns=True,
                    include_remote=args.include_remote,
                    timeout_sec=args.timeout_sec,
                    max_loop_iters=0,
                )
            )
            execute_state = run_dir / "repair_execution" / "sacg_state.json"
            iteration["repair_execution_report"] = str(execute_path)
            iteration["repair_execution_status"] = execute_report.get("status")
            iteration["repair_execution_errors"] = execute_report.get("errors", [])
            iterations.append(iteration)
            regenerated_stage6_states = [
                Path(str(item.get("result", {}).get("stage6_sacg_state")))
                for item in execute_report.get("step_results", [])
                if isinstance(item, dict) and item.get("result", {}).get("stage6_sacg_state")
            ]
            if regenerated_stage6_states and regenerated_stage6_states[-1].exists():
                current_state = regenerated_stage6_states[-1]
            else:
                current_state = execute_state if execute_state.exists() else repair_state
            if execute_report.get("errors"):
                if repair_execution_has_new_real_tool_evidence(execute_report):
                    iteration["same_plan_real_tool_followup"] = True
                    executor_resume = {
                        "repair_plan": repair_plan_path,
                        "repair_execution_report": execute_path,
                        "execution": execute_report,
                    }
                    continue
                transaction_key = agent_transaction_retry_key(execute_report)
                if transaction_key is not None:
                    iteration["agent_transaction_rejected"] = True
                    iteration["fresh_stage6_agent_replan"] = True
                    iteration["fresh_stage6_agent_replan_reason"] = (
                        "the prior transaction was rejected before a source write; "
                        "replan from the current observation evidence"
                    )
                    continue
                if repair_execution_requires_fresh_agent_planning(execute_report):
                    iteration["fresh_stage6_agent_replan"] = True
                    iteration["fresh_stage6_agent_replan_reason"] = (
                        "an unresolved Agent-owned capability must be replanned "
                        "against current Stage 6 evidence"
                    )
                    continue
                iteration["fresh_stage6_agent_replan"] = True
                iteration["fresh_stage6_agent_replan_reason"] = (
                    "repair execution did not complete; obtain a new observation and "
                    "fresh LLM plan rather than suppressing replanning"
                )
                index += 1
                continue
        except Exception as exc:
            iteration["exception"] = str(exc)
            iterations.append(iteration)
            iteration["fresh_stage6_agent_replan"] = True
            iteration["fresh_stage6_agent_replan_reason"] = (
                f"debug-loop execution raised {exc}; retain current evidence and retry"
            )
            index += 1
            continue
        index += 1
    if status != "pass" and args.max_iters > 0 and index >= args.max_iters:
        status = "needs_repair"
        summary = f"debug loop reached max_iters={args.max_iters}"

    report = {
        "schema_version": "spatialaccagent.hierarchical_debug_loop_run.v0",
        "stage": "debug_loop",
        "status": status,
        "summary": summary,
        "source_sacg_state": str(args.sacg_state.resolve()),
        "final_sacg_state": str(current_state),
        "max_iters": args.max_iters,
        "target_scope": args.target_scope,
        "scope_sequence": scopes,
        "reused_scopes": reused_scopes,
        "iterations": iterations,
        "policy": {
            "three_layer_order_required": True,
            "same_scope_repair_loop_until_pass": True,
            "advance_scope_only_after_stage6_ready": True,
            "reuse_validated_lower_layer_certificates": True,
            "debug_layers": [
                "operator_leaf_modules",
                "single_transformer_layer_kernel",
                "board_axi_ddr_wrapped_system",
            ],
            "uses_stage6_stage6_repair_execute_agents": True,
            "llm_required_for_agentic_decisions": True,
            "real_tools_required_for_acceptance": True,
        },
    }
    report_path = out_dir / "debug_loop_report.json"
    write_json(report_path, report)
    return report_path, report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hierarchical verification/repair loop")
    parser.add_argument("--sacg-state", type=Path, required=True)
    parser.add_argument(
        "--max-iters",
        type=int,
        default=0,
        help="positive value limits iterations; 0 keeps the current repair scope active until pass",
    )
    parser.add_argument("--target-scope", default="board_axi_ddr_closure")
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=0,
        help="outer real-tool wall-clock timeout in seconds; <=0 waits without a wall-clock limit",
    )
    parser.add_argument("--include-remote", action="store_true")
    parser.add_argument("--stop-after-failed-repair", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_path, report = debug_loop(args)
    print(report_path)
    print(json.dumps({"status": report["status"], "summary": report["summary"]}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
