import json
import os
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.stage_debug_loop import (
    agent_transaction_retry_key,
    backend_requested_board_recompile,
    deterministic_repair_followup_key,
    debug_loop,
    parse_args,
    pending_repair_execution_resume,
    repair_plan_matches_scope,
    repair_execution_requires_fresh_agent_planning,
    repair_execution_has_new_real_tool_evidence,
    reusable_scope_checkpoint_prefix,
    run_stage6_verification,
    terminal_repair_loop_disposition,
    validated_scope_certificate,
)
from accagent.framework.flow_action_handoff import action_record_path


class DebugLoopResumeTest(TestCase):
    def test_board_entry_materializes_current_compile_authority_after_single_layer_refresh(self):
        with TemporaryDirectory() as tmp:
            run = Path(tmp)
            binding = run / "generated/memory/dut_weight_binding_manifest.json"
            binding.parent.mkdir(parents=True)
            binding.write_text("{}")
            with patch("accagent.framework.stage_debug_loop.stage2_compile_only_authority", return_value={"status": "ready"}), \
                    patch("accagent.framework.stage_debug_loop.finalize_dut_weight_binding_manifest", return_value={"status": "pass"}) as materialize, \
                    patch("accagent.framework.stage_debug_loop.run_verification", return_value=(run / "report.json", {"status": "ready"})) as verify:
                _, _, preparation = run_stage6_verification(current_state=run / "state.json", run_dir=run,
                    active_scope="board_axi_ddr_closure", timeout_sec=0,
                    reused_scopes=["operator_leaf_closure", "single_layer_closure"], iteration_index=1)
            materialize.assert_called_once_with(run, run / "repair_execution", require_board=True)
            self.assertEqual(preparation["binding_materialization"]["status"], "pass")
            verify.assert_called_once()

    def test_changed_original_kernel_reopens_single_layer_even_if_staged_certificate_passes(self):
        with TemporaryDirectory() as tmp:
            run = Path(tmp)
            path = run / "verification/certificates/single_layer_promotion_certificate.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"status": "pass", "validation_policy": "vcs_compile_only"}))
            state = {"artifacts": [{"id": "artifact.stage6.single_layer_promotion_certificate",
                     "path": str(path), "producer_transition": "t"}],
                     "transitions": [{"id": "t", "status": "promoted"}]}
            with patch("accagent.framework.stage_debug_loop.stage2_compile_only_authority",
                       return_value={"status": "blocked", "blockers": ["original source changed"]}):
                self.assertIsNone(validated_scope_certificate(state, "single_layer_closure"))
            with patch("accagent.framework.stage_debug_loop.stage2_compile_only_authority",
                       return_value={"status": "ready"}), \
                    patch("accagent.framework.stage_debug_loop.case_adapter_for_state", return_value={}), \
                    patch("accagent.framework.stage_debug_loop.compile_only_required_gates_by_level", return_value={}), \
                    patch("accagent.framework.stage_debug_loop.certificate_contract_errors", return_value=[]), \
                    patch("accagent.framework.stage_debug_loop.selector_contract_matches_certificate", return_value=True):
                self.assertIsNotNone(validated_scope_certificate(state, "single_layer_closure"))

    def test_changed_tool_profile_refreshes_board_compile_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            profile = run_dir / "input/tool_profile.json"
            profile.parent.mkdir()
            profile.write_text('{"tools": []}\n', encoding="utf-8")
            manifest = run_dir / "verification/board_simulation/board_simulation_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"vcs_compile_plan": {"tool_profile_sha256": "a" * 64}}), encoding="utf-8")
            self.assertTrue(backend_requested_board_recompile({}, run_dir))

    def test_current_board_source_change_requires_recompile_without_a_new_request(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source = run_dir / "adapter.sv"
            source.write_text("current source", encoding="utf-8")
            manifest = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"source_files": [{
                "path": str(source), "sha256": "a" * 64,
            }]}), encoding="utf-8")
            self.assertTrue(backend_requested_board_recompile({}, run_dir))

    def test_backend_source_change_refreshes_only_board_scope_even_with_valid_certificates(self) -> None:
        scopes = ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"]
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "backend_board" / "sacg_state.json"
            state_path.parent.mkdir()
            state_path.write_text(json.dumps({"memory": {"backtrack_requests": [{
                "status": "open", "stage": "stage7.backend_board",
                "target_stage": "stage6.verification", "verification_scope": "board_axi_ddr_closure",
            }]}}), encoding="utf-8")
            verified_state = run_dir / "verification" / "sacg_state.json"
            verified_state.parent.mkdir()
            verified_state.write_text(json.dumps({}), encoding="utf-8")
            binding_manifest = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            binding_manifest.parent.mkdir(parents=True)
            binding_manifest.write_text("{}\n", encoding="utf-8")
            with patch(
                "accagent.framework.stage_debug_loop.finalize_dut_weight_binding_manifest",
                return_value={"status": "pass"},
            ) as materialization, patch(
                "accagent.framework.stage_debug_loop.reusable_scope_prefix", return_value=scopes
            ), patch(
                "accagent.framework.stage_debug_loop.reusable_scope_checkpoint_prefix", return_value=scopes
            ), patch(
                "accagent.framework.stage_debug_loop.pending_repair_execution_resume",
                side_effect=AssertionError("must compile current source, not resume an old repair plan"),
            ), patch(
                "accagent.framework.stage_debug_loop.run_stage6_verification",
                return_value=(run_dir / "verification" / "report.json", {
                    "status": "ready", "outputs": {"sacg_state": str(verified_state)},
                }, {"status": "not_required"}),
            ) as verification:
                _, report = debug_loop(Namespace(
                    sacg_state=state_path, max_iters=0, target_scope="board_axi_ddr_closure",
                    timeout_sec=0, include_remote=True, stop_after_failed_repair=False,
                ))

        self.assertEqual(report["status"], "pass")
        materialization.assert_called_once_with(
            run_dir, run_dir / "repair_execution", require_board=True,
        )
        verification.assert_called_once()
        self.assertEqual(verification.call_args.kwargs["active_scope"], "board_axi_ddr_closure")
        self.assertEqual(verification.call_args.kwargs["current_state"], state_path)
        self.assertEqual(verification.call_args.kwargs["reused_scopes"][:2], scopes[:2])

    def test_stale_lower_layer_plan_is_not_resumed_for_board_scope(self) -> None:
        plan = {
            "status": "needs_repair",
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "repair_execution_context": {
                            "verification_scope": "operator_leaf_closure",
                            "debug_layer": "operator_leaf_modules",
                        }
                    }
                ],
            },
        }
        execution = {
            "stage": "repair_execution",
            "status": "incomplete",
            "errors": ["stale lower-layer plan"],
        }

        self.assertFalse(
            repair_plan_matches_scope(
                plan,
                execution,
                "board_axi_ddr_closure",
            )
        )

    def test_resume_defers_unconsumed_flow_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps({"artifacts": [], "transitions": []}),
                encoding="utf-8",
            )
            handoff = {
                "status": "ready",
                "handoff_identity": "a" * 64,
                "target_stage": "debug_loop",
            }
            resume = {
                "repair_plan": run_dir / "repair" / "repair_plan.json",
                "repair_execution_report": run_dir / "repair_execution" / "repair_execution_report.json",
                "execution": {"status": "incomplete", "errors": ["retry"]},
            }
            with (
                patch(
                    "accagent.framework.stage_debug_loop.pending_stage6_flow_handoff",
                    return_value=handoff,
                ),
                patch(
                    "accagent.framework.stage_debug_loop.pending_repair_execution_resume",
                    return_value=resume,
                ),
                patch(
                    "accagent.framework.stage_debug_loop.run_repair_loop",
                    return_value=(
                        run_dir / "repair_execution" / "repair_execution_report.json",
                        {
                            "status": "incomplete",
                            "errors": ["retry"],
                            "repair_loop_disposition": {
                                "status": "blocked",
                                "summary": "retry requires fresh planning",
                            },
                        },
                    ),
                ),
            ):
                _, report = debug_loop(
                    Namespace(
                        sacg_state=state_path,
                        max_iters=0,
                        target_scope="operator_leaf_closure",
                        timeout_sec=0,
                        include_remote=True,
                        stop_after_failed_repair=False,
                    )
                )

        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["flow_controller_handoff"]["status"], "deferred")
        self.assertEqual(
            report["flow_controller_handoff"]["handoff_identity"],
            handoff["handoff_identity"],
        )

    def test_debug_loop_consumes_one_current_flow_controller_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            verification_state = run_dir / "verification" / "sacg_state.json"
            repair_state = run_dir / "repair" / "sacg_state.json"
            repair_plan_path = run_dir / "repair" / "repair_plan.json"
            flow_result_path = (
                run_dir
                / "agent"
                / "flow_controller"
                / "001_debug_loop"
                / "llm"
                / "flow_controller_agent_result.json"
            )
            event_path = run_dir / "debug_loop" / "flow_events" / "001_retry.json"
            action = {
                "id": "debug_loop.run_current_leaf_gate",
                "stage": "debug_loop",
                "action_type": "real_tool_execution",
                "acceptance_checkers": ["case_stage_leaf_static"],
                "tool_roles": ["case_stage_leaf_static"],
                "consumes": ["artifact.stage5.verification_artifact_contract"],
                "produces": ["verification/operator_leaf/leaf_static_report.json"],
                "rationale": "Run the current leaf static gate.",
                "on_failure": "Keep the current layer blocked.",
                "requires_approval": False,
            }
            for path in (state_path, verification_state, repair_state, repair_plan_path):
                path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({"artifacts": [], "transitions": []}), encoding="utf-8")
            verification_state.write_text("{}", encoding="utf-8")
            repair_state.write_text("{}", encoding="utf-8")
            flow_result_path.parent.mkdir(parents=True, exist_ok=True)
            flow_result_path.write_text(
                json.dumps(
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
                            "summary": "retry the current leaf gate",
                            "executable_actions": [action],
                        },
                    }
                ),
                encoding="utf-8",
            )
            import hashlib

            event = {
                "schema_version": "spatialaccagent.flow_event_action_record.v0",
                "flow_event_index": 1,
                "stage": "debug_loop",
                "decision": "retry",
                "sacg_state": str(state_path),
                "llm_flow_controller": {"agent_record": str(flow_result_path)},
                "executable_actions": [action],
                "source_identities": {
                    "source_sacg_state_sha256": hashlib.sha256(state_path.read_bytes()).hexdigest(),
                    "flow_controller_result_sha256": hashlib.sha256(flow_result_path.read_bytes()).hexdigest(),
                },
            }
            event_path.parent.mkdir(parents=True, exist_ok=True)
            event_path.write_text(json.dumps(event), encoding="utf-8")
            action_path = action_record_path(event_path, 1, action)
            action_path.parent.mkdir(parents=True, exist_ok=True)
            action_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.flow_action_record.v0",
                        "source_flow_event": str(event_path),
                        "action": action,
                    }
                ),
                encoding="utf-8",
            )
            repair_plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {"status": "ready", "steps": [{"id": "repair_step.00"}]},
                    }
                ),
                encoding="utf-8",
            )
            observed: dict[str, object] = {}

            def fake_plan_repair(args):
                observed["handoff"] = args.flow_controller_handoff
                consumption_path = run_dir / "debug_loop" / "flow_handoffs" / "consumed.json"
                consumption_path.parent.mkdir(parents=True, exist_ok=True)
                consumption_path.write_text(
                    json.dumps(
                        {
                            "consumed": {
                                args.flow_controller_handoff["handoff_identity"]: {}
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                return (
                    run_dir / "repair" / "repair_report.json",
                    {
                        "status": "needs_repair",
                        "outputs": {
                            "sacg_state": str(repair_state),
                            "repair_plan": str(repair_plan_path),
                            "flow_controller_handoff_consumption": str(consumption_path),
                        },
                    },
                )

            with patch(
                "accagent.framework.stage_debug_loop.run_stage6_verification",
                return_value=(
                    run_dir / "verification" / "verification_result.json",
                    {"status": "fail", "outputs": {"sacg_state": str(verification_state)}},
                    {"status": "not_required"},
                ),
            ), patch(
                "accagent.framework.stage_debug_loop.plan_repair",
                side_effect=fake_plan_repair,
            ), patch(
                "accagent.framework.stage_debug_loop.run_repair_loop",
                return_value=(
                    run_dir / "repair_execution" / "repair_execution_report.json",
                    {
                        "status": "incomplete",
                        "errors": ["unchanged repair frontier"],
                        "repair_loop_disposition": {"status": "blocked", "summary": "unchanged repair frontier"},
                    },
                ),
            ):
                _, report = debug_loop(
                    Namespace(
                        sacg_state=state_path,
                        max_iters=0,
                        target_scope="operator_leaf_closure",
                        timeout_sec=0,
                        include_remote=True,
                        stop_after_failed_repair=False,
                    )
                )
            consumed_handoff = (
                run_dir / "debug_loop" / "flow_handoffs" / "consumed.json"
            ).is_file()

        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(observed["handoff"]["target_stage"], "debug_loop")
        self.assertEqual(report["iterations"][0]["flow_controller_handoff"]["status"], "consumed")
        self.assertTrue(consumed_handoff)

    def test_local_framework_exception_stops_current_debug_loop_without_spinning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            state_path.parent.mkdir()
            state_path.write_text(json.dumps({"artifacts": [], "transitions": []}), encoding="utf-8")
            with patch(
                "accagent.framework.stage_debug_loop.run_stage6_verification",
                side_effect=KeyError("missing Stage5 verification contract"),
            ) as verification_mock:
                _, report = debug_loop(
                    Namespace(
                        sacg_state=state_path,
                        max_iters=0,
                        target_scope="operator_leaf_closure",
                        timeout_sec=0,
                        include_remote=True,
                        stop_after_failed_repair=False,
                    )
                )

        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(len(report["iterations"]), 1)
        self.assertIn("missing Stage5 verification contract", report["summary"])
        self.assertIn("KeyError", report["iterations"][0]["exception_traceback"])
        verification_mock.assert_called_once()

    def test_terminal_repair_loop_disposition_returns_to_flow_controller(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            verification_state = run_dir / "verification" / "sacg_state.json"
            repair_state = run_dir / "repair" / "sacg_state.json"
            repair_plan_path = run_dir / "repair" / "repair_plan.json"
            state_path.parent.mkdir()
            verification_state.parent.mkdir()
            repair_state.parent.mkdir()
            state_path.write_text(json.dumps({"artifacts": [], "transitions": []}), encoding="utf-8")
            verification_state.write_text("{}", encoding="utf-8")
            repair_state.write_text("{}", encoding="utf-8")
            repair_plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_debug_loop.run_stage6_verification",
                return_value=(
                    run_dir / "verification" / "verification_result.json",
                    {
                        "status": "fail",
                        "outputs": {"sacg_state": str(verification_state)},
                    },
                    {"status": "not_required"},
                ),
            ) as verification_mock, patch(
                "accagent.framework.stage_debug_loop.plan_repair",
                return_value=(
                    run_dir / "repair" / "repair_report.json",
                    {
                        "outputs": {
                            "sacg_state": str(repair_state),
                            "repair_plan": str(repair_plan_path),
                        }
                    },
                ),
            ), patch(
                "accagent.framework.stage_debug_loop.run_repair_loop",
                return_value=(
                    run_dir / "repair_execution" / "repair_execution_report.json",
                    {
                        "status": "incomplete",
                        "errors": ["unchanged repair frontier"],
                        "repair_loop_disposition": {
                            "status": "blocked",
                            "summary": "unchanged repair frontier",
                        },
                    },
                ),
            ) as repair_loop_mock:
                _, report = debug_loop(
                    Namespace(
                        sacg_state=state_path,
                        max_iters=0,
                        target_scope="operator_leaf_closure",
                        timeout_sec=0,
                        include_remote=True,
                        stop_after_failed_repair=False,
                    )
                )

        self.assertEqual(report["status"], "needs_repair")
        self.assertEqual(report["summary"], "unchanged repair frontier")
        self.assertEqual(len(report["iterations"]), 1)
        self.assertEqual(
            report["iterations"][0]["repair_execution_disposition"]["status"],
            "blocked",
        )
        verification_mock.assert_called_once()
        repair_loop_mock.assert_called_once()

    def test_agent_capability_replan_precedes_terminal_blocked_disposition(self) -> None:
        report = {
            "repair_loop_disposition": {
                "status": "blocked",
                "summary": "targeted observation needs a fresh specialist plan",
            },
            "step_results": [
                {
                    "result": {
                        "status": "blocked",
                        "framework_action_required": True,
                        "required_capabilities": [
                            {
                                "capability_id": "targeted_leaf_observation_replan",
                                "producer_scope": "verification_targeted_specialist",
                            }
                        ],
                    }
                }
            ],
        }

        self.assertTrue(repair_execution_requires_fresh_agent_planning(report))
        self.assertIsNone(terminal_repair_loop_disposition(report))

    def test_no_progress_wait_is_terminal_without_new_producer_evidence(self) -> None:
        report = {
            "repair_loop_disposition": {
                "status": "blocked",
                "no_progress_waiting_decisions": ["semantic_loader_harness_binding"],
                "summary": "the same no-edit decision recurred without new evidence",
            },
            "step_results": [],
        }

        self.assertFalse(repair_execution_requires_fresh_agent_planning(report))
        self.assertEqual(
            terminal_repair_loop_disposition(report),
            report["repair_loop_disposition"],
        )

    def test_debug_loop_enables_remote_reruns_by_default(self) -> None:
        args = parse_args(["--sacg-state", "state.json"])

        self.assertTrue(args.include_remote)

    def test_debug_loop_allows_explicit_local_only_diagnostics(self) -> None:
        args = parse_args([
            "--sacg-state",
            "state.json",
            "--no-include-remote",
        ])

        self.assertFalse(args.include_remote)

    def test_initial_layer3_verification_receives_required_checkpoint_environment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "sacg_state.json"
            request = root / "checkpoint_request.json"
            observed: dict[str, str | None] = {}

            def fake_run_verification(_args):
                observed["required"] = os.environ.get(
                    "SPATIALACC_CHECKPOINT_REQUIRED"
                )
                observed["request"] = os.environ.get(
                    "SPATIALACC_CHECKPOINT_REQUEST"
                )
                return root / "verification_report.json", {"status": "ready"}

            with patch(
                "accagent.framework.stage_debug_loop.prepare_stage3_checkpoint_probe_environment",
                return_value={
                    "status": "pass",
                    "summary": "prepared cold capture",
                    "request_path": str(request),
                    "checkpoint_enabled": True,
                    "cold_fallback": False,
                    "remote_tool_must_not_start": False,
                    "env": {
                        "SPATIALACC_CHECKPOINT_REQUIRED": "1",
                        "SPATIALACC_CHECKPOINT_REQUEST": str(request),
                    },
                },
            ), patch(
                "accagent.framework.stage_debug_loop.run_verification",
                side_effect=fake_run_verification,
            ):
                verification_path, verification_report, preparation = (
                    run_stage6_verification(
                        current_state=state,
                        run_dir=root,
                        active_scope="board_axi_ddr_closure",
                        timeout_sec=0,
                        reused_scopes=[
                            "operator_leaf_closure",
                            "single_layer_closure",
                        ],
                        iteration_index=0,
                    )
                )

        self.assertEqual(verification_path, root / "verification_report.json")
        self.assertEqual(verification_report, {"status": "ready"})
        self.assertEqual(preparation["status"], "pass")
        self.assertEqual(observed["required"], "0")
        self.assertEqual(observed["request"], "")

    def test_layer3_has_no_checkpoint_preparation_prerequisite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expected = (root / "verification.json", {"status": "ready"})
            with patch(
                "accagent.framework.stage_debug_loop.prepare_stage3_checkpoint_probe_environment",
                side_effect=AssertionError("retired checkpoint preparation must not run"),
            ) as prepare, patch(
                "accagent.framework.stage_debug_loop.run_verification", return_value=expected,
            ) as verify:
                path, report, preparation = run_stage6_verification(
                    current_state=root / "sacg_state.json", run_dir=root,
                    active_scope="board_axi_ddr_closure", timeout_sec=0,
                    reused_scopes=[], iteration_index=0,
                )
        self.assertEqual((path, report), expected)
        self.assertFalse(preparation["remote_tool_must_not_start"])
        prepare.assert_not_called()
        verify.assert_called_once()

    def test_lower_layer_verification_does_not_prepare_checkpoint(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for index, scope in enumerate(
                ("operator_leaf_closure", "single_layer_closure")
            ):
                with self.subTest(scope=scope), patch(
                    "accagent.framework.stage_debug_loop.prepare_stage3_checkpoint_probe_environment"
                ) as prepare_mock, patch(
                    "accagent.framework.stage_debug_loop.run_verification",
                    return_value=(
                        root / f"verification_report_{index}.json",
                        {"status": "ready"},
                    ),
                ) as run_verification_mock:
                    verification_path, verification_report, preparation = (
                        run_stage6_verification(
                            current_state=root / "sacg_state.json",
                            run_dir=root,
                            active_scope=scope,
                            timeout_sec=0,
                            reused_scopes=[],
                            iteration_index=index,
                        )
                    )

                prepare_mock.assert_not_called()
                run_verification_mock.assert_called_once()
                self.assertIsNotNone(verification_path)
                self.assertEqual(verification_report, {"status": "ready"})
                self.assertEqual(preparation["status"], "not_required")

    def test_recovers_scope_entry_certificates_without_replaying_lower_tools(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            debug_dir = run_dir / "debug_loop"
            debug_dir.mkdir()
            leaf_path = run_dir / "leaf_certificate.json"
            single_path = run_dir / "single_certificate.json"
            leaf_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            single_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            (debug_dir / "debug_loop_report.json").write_text(
                json.dumps(
                    {
                        "target_scope": "board_axi_ddr_closure",
                        "reused_scopes": [
                            "operator_leaf_closure",
                            "single_layer_closure",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage6.operator_leaf_promotion_certificate",
                        "path": str(leaf_path),
                        "trust_status": "validated",
                    },
                    {
                        "id": "artifact.stage6.single_layer_promotion_certificate",
                        "path": str(single_path),
                        "trust_status": "validated",
                    },
                ]
            }

            with patch(
                "accagent.framework.stage_debug_loop.validated_scope_certificate",
                side_effect=lambda state, scope: {"scope": scope},
            ):
                recovered = reusable_scope_checkpoint_prefix(
                    state, run_dir, "board_axi_ddr_closure",
                    ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"],
                )
            with patch(
                "accagent.framework.stage_debug_loop.validated_scope_certificate",
                side_effect=lambda state, scope: {"scope": scope} if scope == "operator_leaf_closure" else None,
            ):
                self.assertEqual(reusable_scope_checkpoint_prefix(
                    state, run_dir, "board_axi_ddr_closure",
                    ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"],
                ), ["operator_leaf_closure"])
            # A bare old pass without a valid live binding cannot be reused.
            self.assertEqual(reusable_scope_checkpoint_prefix(
                state, run_dir, "board_axi_ddr_closure",
                ["operator_leaf_closure", "single_layer_closure", "board_axi_ddr_closure"],
            ), [])

        self.assertEqual(recovered, [
            "operator_leaf_closure",
            "single_layer_closure",
        ])

    def test_resumes_executable_plan_without_replanning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "repair_plan.json"
            execution_path = root / "repair_execution.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["executor must retry after framework update"],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state)

        self.assertIsNotNone(resume)
        assert resume is not None
        self.assertEqual(resume["repair_plan"], plan_path)

    def test_blocked_no_progress_frontier_does_not_resume_old_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "repair_plan.json"
            execution_path = root / "repair_execution.json"
            record_path = (
                root
                / "repair_execution"
                / "loop"
                / "iteration_0001"
                / "iteration_record.json"
            )
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["unchanged repair frontier"],
                    }
                ),
                encoding="utf-8",
            )
            record_path.parent.mkdir(parents=True)
            record_path.write_text(
                json.dumps(
                    {
                        "repair_execution_report_path": str(execution_path),
                        "disposition": {
                            "status": "blocked",
                            "no_progress_failures": ["unchanged repair frontier"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            loop_status_path = root / "repair_execution" / "loop" / "status.json"
            loop_status_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "latest_iteration_record": str(record_path),
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state, root)

        self.assertIsNone(resume)

    def test_ready_flow_handoff_supersedes_rebased_blocked_frontier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "repair_plan.json"
            execution_path = root / "repair_execution.json"
            archived_execution_path = root / "archived_repair_execution.json"
            record_path = (
                root
                / "repair_execution"
                / "loop"
                / "iteration_0001"
                / "iteration_record.json"
            )
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["unchanged repair frontier"],
                    }
                ),
                encoding="utf-8",
            )
            record_path.parent.mkdir(parents=True)
            record_path.write_text(
                json.dumps(
                    {
                        "repair_execution_report_path": str(archived_execution_path),
                        "disposition": {
                            "status": "blocked",
                            "observation_replan_required": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            loop_status_path = root / "repair_execution" / "loop" / "status.json"
            loop_status_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "latest_iteration_record": str(record_path),
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state, root)
            handoff_resume = pending_repair_execution_resume(
                state,
                root,
                prefer_ready_flow_handoff=True,
            )

        self.assertIsNotNone(resume)
        self.assertIsNone(handoff_resume)

    def test_environment_only_block_reenters_stage6(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "repair_plan.json"
            execution_path = root / "repair_execution.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["implementation agent requires an upstream capability"],
                        "step_results": [
                            {
                                "result": {
                                    "framework_action_required": True,
                                    "required_capabilities": [
                                        {
                                            "producer_scope": "framework_execution_environment"
                                        }
                                    ],
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state)

        self.assertIsNone(resume)

    def test_validated_identity_supersedes_stale_discovery_repair_resume(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            plan_path = run_dir / "repair_plan.json"
            execution_path = run_dir / "repair_execution.json"
            identity_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json"
            )
            identity_path.parent.mkdir(parents=True)
            identity_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [
                                {
                                    "id": "repair_step.00",
                                    "action": {
                                        "repair_kind": "exact_board_interface_discovery"
                                    },
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["historical discovery failure"],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }
            with patch(
                "accagent.framework.board_acceptance_contract.validate_exact_board_identity",
                return_value={"status": "pass"},
            ):
                resume = pending_repair_execution_resume(state, run_dir)

        self.assertIsNone(resume)

    def test_does_not_resume_completed_or_new_tool_execution(self) -> None:
        report = {
            "step_results": [
                {
                    "result": {
                        "new_current_real_tool_failure_requires_agent": True,
                    }
                }
            ]
        }

        self.assertTrue(repair_execution_has_new_real_tool_evidence(report))
        self.assertFalse(repair_execution_has_new_real_tool_evidence({}))

    def test_agent_owned_capability_reenters_stage6(self) -> None:
        report = {
            "step_results": [
                {
                    "result": {
                        "status": "blocked",
                        "framework_action_required": True,
                        "required_capabilities": [
                            {
                                "producer_scope": (
                                    "generated board-integration simulation "
                                    "observability"
                                )
                            }
                        ],
                    }
                }
            ]
        }

        self.assertTrue(repair_execution_requires_fresh_agent_planning(report))
        self.assertFalse(
            repair_execution_requires_fresh_agent_planning(
                {
                    "step_results": [
                        {
                            "result": {
                                "status": "blocked",
                                "framework_action_required": True,
                                "required_capabilities": [
                                    {
                                        "producer_scope": (
                                            "framework_execution_environment"
                                        )
                                    }
                                ],
                            }
                        }
                    ]
                }
            )
        )

    def test_recognizes_only_new_applied_deterministic_preflight_feedback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            patch_path = root / "agent_patch_application.json"
            materialization_path = root / "dut_weight_binding_materialization.json"
            patch_path.write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            materialization_path.write_text(
                json.dumps(
                    {
                        "status": "incomplete",
                        "manifest_sha256": "a" * 64,
                        "blockers": ["current preflight contract is incomplete"],
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "step_results": [
                    {
                        "result": {
                            "agent_patch_application": str(patch_path),
                            "dut_weight_binding_materialization": str(
                                materialization_path
                            ),
                        }
                    }
                ]
            }

            key = deterministic_repair_followup_key(report)

            self.assertIsNotNone(key)
            self.assertIn("manifest_sha256", key)
            patch_path.write_text(
                json.dumps({"status": "blocked"}), encoding="utf-8"
            )
            self.assertIsNone(deterministic_repair_followup_key(report))

    def test_identifies_only_no_tool_agent_transaction_rejections(self) -> None:
        with TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "retry_agent_without_real_tool": True,
                        "files": [],
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "real_tool_replay_required_before_retry": False,
                            "failure_class": "agent_transaction_contract",
                            "blockers": ["missing required edit metadata"],
                            "unchanged_pre_edit_files": ["board_tb.sv"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "step_results": [
                    {"result": {"agent_patch_application": str(patch_path)}}
                ]
            }

            key = agent_transaction_retry_key(report)
            self.assertIsNotNone(key)

            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "retry_agent_without_real_tool": True,
                        "files": [],
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "real_tool_replay_required_before_retry": False,
                            "failure_class": "agent_transaction_contract",
                            "blockers": ["a different invalid field"],
                            "unchanged_pre_edit_files": ["board_tb.sv"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(key, agent_transaction_retry_key(report))

            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "retry_agent_without_real_tool": True,
                        "files": ["board_tb.sv"],
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "real_tool_replay_required_before_retry": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertIsNone(agent_transaction_retry_key(report))


if __name__ == "__main__":
    import unittest

    unittest.main()
