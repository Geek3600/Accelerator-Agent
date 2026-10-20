import hashlib
import json
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.agent import TopAgent
from accagent.framework.flow_action_handoff import (
    HANDOFF_SCHEMA_VERSION,
    action_record_path,
    mark_stage6_flow_handoff_consumed,
    pending_stage6_flow_handoff,
    validate_stage6_flow_handoff,
)
from accagent.framework.stage_repair import (
    build_repair_plan,
    build_repair_workflow,
    flow_handoff_repair_actions,
    plan_repair,
)


class FlowActionHandoffTest(TestCase):
    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def materialize_event(
        self,
        run_dir: Path,
        state_path: Path,
        *,
        index: int,
        action: dict,
        requires_approval: bool = False,
    ) -> Path:
        action = {**action, "requires_approval": requires_approval}
        result_path = (
            run_dir
            / "agent"
            / "flow_controller"
            / f"{index:03d}_debug_loop"
            / "llm"
            / "flow_controller_agent_result.json"
        )
        result = {
            "schema_version": "spatialaccagent.stage_worker_record.v0",
            "agent": "flow_controller_agent",
            "stage": "flow_orchestration",
            "used_fallback": False,
            "error": None,
            "output": {
                "agent": "flow_controller_agent",
                "stage": "debug_loop",
                "status": "retry_current_stage",
                "summary": "run the current operator-leaf repair closure",
                "executable_actions": [action],
            },
        }
        self.write_json(result_path, result)
        event_path = run_dir / "debug_loop" / "flow_events" / f"{index:03d}_retry.json"
        event = {
            "schema_version": "spatialaccagent.flow_event_action_record.v0",
            "flow_event_index": index,
            "stage": "debug_loop",
            "decision": "retry",
            "sacg_state": str(state_path),
            "llm_flow_controller": {"agent_record": str(result_path)},
            "executable_actions": [action],
            "source_identities": {
                "source_sacg_state_sha256": self.sha256(state_path),
                "flow_controller_result_sha256": self.sha256(result_path),
            },
        }
        self.write_json(event_path, event)
        action_path = action_record_path(event_path, index, action)
        self.write_json(
            action_path,
            {
                "schema_version": "spatialaccagent.flow_action_record.v0",
                "source_flow_event": str(event_path),
                "action": action,
            },
        )
        return event_path

    def valid_action(self, identifier: str) -> dict:
        return {
            "id": identifier,
            "stage": "debug_loop",
            "action_type": "real_tool_execution",
            "acceptance_checkers": ["case_stage_leaf_static"],
            "tool_roles": ["case_stage_leaf_static"],
            "consumes": ["artifact.stage5.verification_artifact_contract"],
            "produces": ["verification/operator_leaf/leaf_static_report.json"],
            "rationale": "Run the current required operator-leaf static gate.",
            "on_failure": "Keep the current layer blocked and localize the failure.",
        }

    def test_current_handoff_is_consumed_once_and_new_source_is_eligible(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                state_path,
                index=1,
                action=self.valid_action("debug_loop.run_leaf_static"),
            )

            handoff = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(handoff["schema_version"], HANDOFF_SCHEMA_VERSION)
            self.assertEqual(handoff["status"], "ready")
            self.assertEqual(validate_stage6_flow_handoff(handoff, run_dir), [])

            repair_plan = run_dir / "repair" / "repair_plan.json"
            self.write_json(repair_plan, {"status": "needs_repair"})
            mark_stage6_flow_handoff_consumed(run_dir, handoff, repair_plan)
            self.assertEqual(
                pending_stage6_flow_handoff(run_dir, state_path)["status"],
                "already_consumed",
            )

            self.write_json(
                state_path,
                {"artifacts": [{"id": "artifact.stage6.real_tool_results"}], "transitions": [], "memory": {}},
            )
            self.materialize_event(
                run_dir,
                state_path,
                index=2,
                action=self.valid_action("debug_loop.run_leaf_static_after_new_observation"),
            )
            refreshed = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(refreshed["status"], "ready")
            self.assertNotEqual(refreshed["handoff_identity"], handoff["handoff_identity"])

    def test_latest_invalid_or_approval_only_handoff_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                state_path,
                index=1,
                action=self.valid_action("debug_loop.valid_old_action"),
            )
            self.materialize_event(
                run_dir,
                state_path,
                index=2,
                action=self.valid_action("debug_loop.approval_only_action"),
                requires_approval=True,
            )

            result = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("no auto-executable", result["summary"])

    def test_source_identity_drift_is_not_reused(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                state_path,
                index=1,
                action=self.valid_action("debug_loop.source_bound_action"),
            )
            self.write_json(state_path, {"artifacts": [{"id": "changed"}], "transitions": [], "memory": {}})

            result = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(result["status"], "not_required")

    def test_top_agent_snapshot_survives_later_source_state_update(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            state_path = run_dir / "repair" / "sacg_state.json"
            result_path = run_dir / "agent" / "flow_controller" / "result.json"
            self.write_json(state_path, {"artifacts": [], "transitions": [], "memory": {}})
            action = {**self.valid_action("debug_loop.snapshot_bound_action"), "requires_approval": False}
            self.write_json(
                result_path,
                {
                    "schema_version": "spatialaccagent.stage_worker_record.v0",
                    "agent": "flow_controller_agent",
                    "stage": "flow_orchestration",
                    "used_fallback": False,
                    "error": None,
                    "output": {
                        "agent": "flow_controller_agent",
                        "stage": "debug_loop",
                        "status": "retry_current_stage",
                        "summary": "retry with the current SACG evidence",
                        "executable_actions": [action],
                    },
                },
            )
            event = {
                "stage": "debug_loop",
                "decision": "retry",
                "sacg_state": str(state_path),
                "llm_flow_controller": {
                    "agent_record": str(result_path),
                    "agent_executable_actions": [action],
                },
            }
            agent = TopAgent.__new__(TopAgent)
            agent.out = run_dir
            agent.flow_events = [event]

            agent.materialize_flow_event_actions(event)

            event_path = run_dir / "debug_loop" / "flow_events" / "001_retry.json"
            materialized = json.loads(event_path.read_text(encoding="utf-8"))
            snapshot_path = Path(materialized["sacg_state"])
            handoff = pending_stage6_flow_handoff(run_dir, state_path)
            self.assertEqual(materialized["source_sacg_state"], str(state_path))
            self.assertEqual(snapshot_path.read_bytes(), state_path.read_bytes())
            self.assertEqual(handoff["status"], "ready")

            self.write_json(state_path, {"artifacts": [{"id": "changed"}], "transitions": []})

            self.assertEqual(pending_stage6_flow_handoff(run_dir, state_path)["status"], "not_required")
            self.assertEqual(validate_stage6_flow_handoff(handoff, run_dir), [])

    def test_repair_plan_consumes_handoff_before_updating_source_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            self.write_json(source_state, {"artifacts": [], "transitions": [], "memory": {}})
            self.materialize_event(
                run_dir,
                source_state,
                index=1,
                action=self.valid_action("debug_loop.repair_from_current_evidence"),
            )
            handoff = pending_stage6_flow_handoff(run_dir, source_state)
            repair_plan = {
                "status": "needs_repair",
                "repair_actions": [{"scope": "signal_connection"}],
                "diagnostics": {},
                "failures": [],
            }
            llm = {
                "output": {"executable_actions": []},
                "result_path": str(run_dir / "repair" / "llm" / "result.json"),
            }

            def mutate_source_state(source: Path, target: Path, _plan_path: Path, _plan: dict) -> str:
                self.write_json(source, {"artifacts": ["repair-planned"]})
                return "transition.1"

            with (
                patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}),
                patch("accagent.framework.stage_repair.build_repair_plan", return_value=repair_plan),
                patch(
                    "accagent.framework.stage_repair.run_repair_review_team",
                    side_effect=AssertionError("compile-only repair must not run a review team"),
                ),
                patch("accagent.framework.stage_repair.exact_localized_repair_route", return_value=True),
                patch("accagent.framework.stage_repair.deterministic_localized_repair_record", return_value=llm),
                patch("accagent.framework.stage_repair.exact_board_identity_contract_passed", return_value=False),
                patch("accagent.framework.stage_repair.reconcile_repair_workflow_with_llm", return_value=repair_plan),
                patch("accagent.framework.stage_repair.update_sacg", side_effect=mutate_source_state),
            ):
                _, report = plan_repair(
                    Namespace(sacg_state=source_state, flow_controller_handoff=handoff)
                )

            consumed_path = Path(report["outputs"]["flow_controller_handoff_consumption"])
            consumed = json.loads(consumed_path.read_text(encoding="utf-8"))["consumed"]
            self.assertIn(handoff["handoff_identity"], consumed)
            self.assertEqual(
                consumed[handoff["handoff_identity"]]["source_sacg_state_sha256"],
                handoff["source_sacg_state"]["sha256"],
            )
            self.assertTrue(source_state.read_text(encoding="utf-8").find("repair-planned") >= 0)

    def test_compile_only_repair_sends_failure_directly_to_primary_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "source_state.json"
            self.write_json(source_state, {"artifacts": [], "transitions": [], "memory": {}})
            run_dir = root / "run"
            run_dir.mkdir()
            repair_plan = {
                "status": "needs_repair",
                "repair_actions": [{"scope": "compile_failure"}],
                "diagnostics": {},
                "failures": [{"checker": "real_tool.vcs_compile", "summary": "syntax error"}],
            }
            llm = {
                "result_path": str(run_dir / "repair" / "llm" / "repair_agent_result.json"),
                "used_fallback": False,
                "output": {"status": "ready", "executable_actions": []},
            }

            with (
                patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}),
                patch("accagent.framework.stage_repair.run_dir_from_state", return_value=run_dir),
                patch("accagent.framework.stage_repair.case_adapter_for_state", return_value={}),
                patch("accagent.framework.stage_repair.build_repair_plan", return_value=repair_plan),
                patch("accagent.framework.stage_repair.run_repair_review_team", side_effect=AssertionError),
                patch("accagent.framework.stage_repair.exact_localized_repair_route", return_value=False),
                patch("accagent.framework.stage_repair.run_stage_agent", return_value=llm) as run_agent,
                patch("accagent.framework.stage_repair.exact_board_identity_contract_passed", return_value=False),
                patch("accagent.framework.stage_repair.reconcile_repair_workflow_with_llm", return_value=repair_plan),
                patch("accagent.framework.stage_repair.update_sacg", return_value="transition"),
            ):
                _, report = plan_repair(Namespace(sacg_state=source_state))

            inputs = run_agent.call_args.kwargs["inputs"]
            self.assertNotIn("design_team", inputs)
            self.assertIn("VCS compile failures", run_agent.call_args.kwargs["task"])
            self.assertEqual(report["status"], "needs_repair")

    def test_trace_handoff_routes_to_targeted_layer1_replay(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                },
                "board_vcs": {
                    "name": "case_vcs_functional_sim",
                    "argv": ["python3", str(script)],
                    "capabilities": [
                        "boundary_trace_rerun",
                        "all_target_layers",
                        "board_wrapper_functional_sim",
                    ],
                },
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "debug_loop.fresh_trace",
                        "action_type": "debug_trace_rerun",
                        "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                        "rationale": "collect a fresh Stage-00 trace",
                    }
                }
            ]
        }
        localization = {
            "targeted_replay_plan": {
                "rerun_env": {
                    "SPATIALACC_TARGET_BOUNDARY": "boundary.edge_input_to_stage_00",
                }
            },
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }
        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(actions[0]["tool"], "case_leaf_functional")
        self.assertEqual(actions[0]["trace_target_stage_id"], "stage_00_rms_norm_1")
        self.assertEqual(
            actions[0]["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"],
            "boundary.edge_input_to_stage_00",
        )
        self.assertNotEqual(actions[0]["scope"], "causal_slice_repair")

        workflow = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)
        step = workflow["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["debug_layer"], "operator_leaf_modules")
        self.assertEqual(step["tool"], "case_leaf_functional")
        self.assertEqual(step["trace_target"]["stage_id"], "stage_00_rms_norm_1")
        self.assertEqual(
            step["execution"]["argv"][-2:],
            ["--stage-id", "stage_00_rms_norm_1"],
        )
        self.assertEqual(step["execution"]["env"]["SPATIALACC_BOUNDARY_TRACE"], "1")
        self.assertEqual(step["execution"]["env"]["SPATIALACC_TARGETED_REPLAY"], "1")

    def test_trace_role_routes_semantic_action_and_defers_repair_sequence(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "debug_loop.refine_operator_leaf_debug_contract",
                        "action_type": "contract_guided_replan",
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.layer1_hash_bound_causal_replay",
                        "action_type": "causal_localization_and_evidence_integrity_replay",
                        "tool_roles": ["boundary_trace_rerun", "failure_slice_localization"],
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.layer1_trace_selected_causal_repair",
                        "action_type": "bounded_causal_slice_repair",
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.layer1_post_repair_full_gate_rerun",
                        "action_type": "same_layer_real_tool_verification",
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.record_candidate_trust_reconciliation",
                        "action_type": "sacg_retry_and_trust_barrier_reconciliation",
                    }
                },
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_type"],
            "causal_localization_and_evidence_integrity_replay",
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["preflight_flow_actions"]],
            ["debug_loop.refine_operator_leaf_debug_contract"],
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["deferred_flow_actions"]],
            [
                "debug_loop.layer1_trace_selected_causal_repair",
                "debug_loop.layer1_post_repair_full_gate_rerun",
                "debug_loop.record_candidate_trust_reconciliation",
            ],
        )
        step = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["tool"], "case_leaf_functional")
        self.assertEqual(step["execution"]["argv"][-2:], ["--stage-id", "stage_00_rms_norm_1"])

    def test_targeted_boundary_trace_producer_routes_after_sacg_preflight(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "record_current_bounded_retry_contract",
                        "action_type": "sacg_retry_and_trust_barrier_update",
                        "tool_roles": [
                            "sacg_validate",
                            "sacg_memory_update",
                            "stage_retry_request",
                            "stage_artifact_trust_barrier",
                            "artifact_hash_check",
                        ],
                    }
                },
                {
                    "action": {
                        "id": "debug_leaf_fresh_hash_bound_replay",
                        "action_type": "fresh_current_layer_real_tool_replay",
                        "tool_roles": ["targeted_replay", "case_vcs_functional_sim"],
                        "produces": ["candidate verification/debug_closure/stage00_hash_bound_boundary_trace.json"],
                    }
                },
                {
                    "action": {
                        "id": "localize_stage00_harness_fingerprint_boundary",
                        "action_type": "cctg_causal_slice_localization",
                        "tool_roles": ["boundary_trace_rerun", "failure_slice_localization"],
                    }
                },
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_id"],
            "debug_leaf_fresh_hash_bound_replay",
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["preflight_flow_actions"]],
            ["record_current_bounded_retry_contract"],
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["deferred_flow_actions"]],
            ["localize_stage00_harness_fingerprint_boundary"],
        )
        step = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["tool"], "case_leaf_functional")
        self.assertEqual(step["execution"]["argv"][-2:], ["--stage-id", "stage_00_rms_norm_1"])

    def test_ordered_handoff_routes_first_causal_replay_only(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "preserve_trust_boundary",
                        "action_type": "artifact_trust_control",
                    }
                },
                {
                    "action": {
                        "id": "freeze_retry_contract",
                        "action_type": "retry_contract_validation",
                    }
                },
                {
                    "action": {
                        "id": "fresh_stage00_replay",
                        "action_type": "current_layer_causal_replay",
                        "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                    }
                },
                {
                    "action": {
                        "id": "repair_from_trace",
                        "action_type": "bounded_repair",
                    }
                },
                {
                    "action": {
                        "id": "rerun_leaf_gate_dag",
                        "action_type": "real_tool_verification_rerun",
                    }
                },
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_type"],
            "current_layer_causal_replay",
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["preflight_flow_actions"]],
            ["preserve_trust_boundary", "freeze_retry_contract"],
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["deferred_flow_actions"]],
            ["repair_from_trace", "rerun_leaf_gate_dag"],
        )
        workflow = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)
        step = workflow["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["tool"], "case_leaf_functional")
        self.assertEqual(step["execution"]["argv"][-2:], ["--stage-id", "stage_00_rms_norm_1"])

    def test_contract_guided_sequence_routes_first_targeted_replay_only(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "build_fresh_causal_context",
                        "action_type": "contract_guided_failure_localization",
                    }
                },
                {
                    "action": {
                        "id": "repair_after_trace",
                        "action_type": "bounded_repair",
                    }
                },
                {
                    "action": {
                        "id": "replay_stage00",
                        "action_type": "real_tool_targeted_replay",
                        "tool_roles": ["targeted_replay", "case_vcs_evidence_analyzer"],
                    }
                },
                {
                    "action": {
                        "id": "verify_full_leaf_scope",
                        "action_type": "real_tool_operator_leaf_verification",
                    }
                },
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_type"],
            "real_tool_targeted_replay",
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["preflight_flow_actions"]],
            ["build_fresh_causal_context"],
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["deferred_flow_actions"]],
            ["repair_after_trace", "verify_full_leaf_scope"],
        )
        step = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["tool"], "case_leaf_functional")
        self.assertEqual(step["execution"]["argv"][-2:], ["--stage-id", "stage_00_rms_norm_1"])

    def test_cctg_trace_sequence_routes_only_current_leaf_trace(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "debug_loop.current_leaf_trace_reconciliation",
                        "action_type": "cctg_current_layer_trace",
                        "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.repair_leaf_binding_and_source_identity",
                        "action_type": "bounded_leaf_harness_repair",
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.rerun_operator_leaf_functional",
                        "action_type": "real_tool_operator_leaf_rerun",
                    }
                },
                {
                    "action": {
                        "id": "debug_loop.complete_operator_leaf_certificate",
                        "action_type": "operator_leaf_golden_and_semantic_closure",
                    }
                },
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "SemanticRmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_id"],
            "debug_loop.current_leaf_trace_reconciliation",
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["deferred_flow_actions"]],
            [
                "debug_loop.repair_leaf_binding_and_source_identity",
                "debug_loop.rerun_operator_leaf_functional",
                "debug_loop.complete_operator_leaf_certificate",
            ],
        )
        step = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["tool"], "case_leaf_functional")
        self.assertEqual(step["execution"]["argv"][-2:], ["--stage-id", "stage_00_rms_norm_1"])

    def test_provenance_then_failure_localization_routes_to_targeted_replay(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "reconcile_handoff",
                        "action_type": "artifact_provenance_reconciliation",
                    }
                },
                {
                    "action": {
                        "id": "capture_retry_trace",
                        "action_type": "real_tool_failure_localization",
                        "tool_roles": ["boundary_trace_rerun", "failure_slice_localization"],
                    }
                },
                {
                    "action": {
                        "id": "repair_localized_slice",
                        "action_type": "bounded_causal_repair",
                    }
                },
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_type"],
            "real_tool_failure_localization",
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["preflight_flow_actions"]],
            ["reconcile_handoff"],
        )
        self.assertEqual(
            [action["id"] for action in actions[0]["minimal_repair_context"]["deferred_flow_actions"]],
            ["repair_localized_slice"],
        )
        step = build_repair_workflow(actions, {}, Path.cwd(), case_adapter)["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["tool"], "case_leaf_functional")

    def test_observation_plans_route_as_preflight_before_boundary_trace(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "tools": {
                "leaf_functional": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        plan_types = [
            "hash_bound_failure_localization_plan",
            "debug_observation_plan",
            "causal_observation_planning",
        ]
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": f"debug_loop.plan_{index}",
                        "action_type": action_type,
                    }
                }
                for index, action_type in enumerate(plan_types)
            ]
            + [
                {
                    "action": {
                        "id": "debug_loop.execute_boundary_trace",
                        "action_type": "debug_trace_rerun",
                        "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                    }
                }
            ]
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }

        actions = flow_handoff_repair_actions(
            handoff,
            case_adapter,
            localization,
            {"current_layer": {"id": "operator_leaf_modules"}},
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "debug_trace_rerun")
        self.assertEqual(
            [action["action_type"] for action in actions[0]["minimal_repair_context"]["preflight_flow_actions"]],
            plan_types,
        )
        self.assertNotIn(
            "flow_controller_action_unroutable",
            [action.get("scope") for action in actions],
        )
        self.assertEqual(
            actions[0]["minimal_repair_context"]["flow_action_id"],
            "debug_loop.execute_boundary_trace",
        )

    def test_trace_handoff_takes_priority_over_stale_inferred_repair(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "verification"
            / "case_leaf_operator_verify.py"
        )
        case_adapter = {
            "case_id": "test_case",
            "model_family": "test",
            "status": "ready",
            "source": "test",
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            },
        }
        localization = {
            "minimal_repair_context": {
                "trace_record": {
                    "status": "fail",
                    "stage_id": "stage_00_rms_norm_1",
                    "module": "Stage00RmsNorm1Harness",
                }
            }
        }
        handoff = {
            "actions": [
                {
                    "action": {
                        "id": "debug_loop.fresh_trace",
                        "action_type": "debug_trace_rerun",
                        "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                        "rationale": "collect a fresh Stage-00 trace",
                    }
                }
            ]
        }

        with (
            patch("accagent.framework.stage_repair.case_adapter_for_state", return_value=case_adapter),
            patch("accagent.framework.stage_repair.artifact_path", return_value=Path("verification.json")),
            patch(
                "accagent.framework.stage_repair.read_json",
                return_value={"status": "fail", "results": [{"status": "fail", "checker": "real_tool.case_leaf_functional"}]},
            ),
            patch("accagent.framework.stage_repair.load_vcs_diagnosis", return_value=None),
            patch("accagent.framework.stage_repair.load_debug_closure_localization", return_value=localization),
            patch(
                "accagent.framework.stage_repair.build_repair_loop_report",
                return_value={"current_layer": {"id": "operator_leaf_modules"}},
            ),
            patch("accagent.framework.stage_repair.prior_repair_execution_feedback", return_value={"status": "blocked"}),
            patch("accagent.framework.stage_repair.rematerialized_lower_layer_capability_evidence", return_value=[]),
            patch("accagent.framework.stage_repair.diagnosis_applicability_report", return_value={}),
            patch("accagent.framework.stage_repair.validate_stage6_flow_handoff", return_value=[]),
            patch(
                "accagent.framework.stage_repair.required_capability_repair_actions",
                return_value=[{"scope": "causal_slice_repair", "source": "stale_inferred_action"}],
            ),
            patch("accagent.framework.stage_repair.exact_board_identity_contract_passed", return_value=False),
            patch("accagent.framework.stage_repair.authoritative_repair_routing_priority", return_value={}),
        ):
            plan = build_repair_plan({}, Path.cwd(), flow_controller_handoff=handoff)

        self.assertEqual(plan["repair_actions"][0]["scope"], "debug_trace_rerun")
        self.assertNotIn("causal_slice_repair", [action["scope"] for action in plan["repair_actions"]])
        step = plan["repair_workflow"]["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["trace_target"]["stage_id"], "stage_00_rms_norm_1")
