"""Current Stage-6 feedback semantics."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from accagent.framework.stage_repair_execute import (
    current_compiler_module_interfaces,
    capability_agent_consumed_materialization_feedback,
    execute_stage6_gate_dag_repair,
    current_repair_action_execution_frontier,
    mark_repair_action_execution_frontier_consumed,
    post_validation_materialization_feedback,
    repair_step_checkpoint,
    board_integration_prompt_rules,
    repair_loop_disposition,
    record_exact_board_rerun_agent_handoff,
    resume_prior_resource_failed_validation,
    run_rerun_step,
    run_repair_loop,
    stage6_live_verification_context,
    targeted_replay_already_executed,
    targeted_replay_input_identity,
    targeted_replay_plan_for_step,
    record_targeted_replay_execution,
)


class RepairExecutionFeedbackTest(unittest.TestCase):
    def test_compiler_port_failure_receives_only_current_module_header(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "unfamiliar.sv"
            source.write_text("module CustomCore(\ninput cfgLength,\noutput ready\n);\nendmodule\n")
            manifest = root / "verification/board_simulation/board_simulation_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"source_files": [{
                "path": str(source), "declared_modules": ["CustomCore"],
                "source_id": "current-core", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()
            }]}))
            feedback = {"diagnosis": {"value": {"failure_evidence": {
                "first_real_error_context": "Port old_cfg is not defined in module 'CustomCore' defined in source"
            }}}}
            rows = current_compiler_module_interfaces(root, feedback)
            self.assertEqual(len(rows), 1)
            self.assertIn("input cfgLength", rows[0]["module_header"])
            self.assertNotIn("endmodule", rows[0]["module_header"])
            source.write_text(source.read_text().replace("cfgLength", "changed"))
            self.assertEqual(current_compiler_module_interfaces(root, feedback), [])

    def test_failed_exact_board_rerun_refreshes_diagnosis_before_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            analyzer_argv = ["python3", "scripts/verification/case_vcs_evidence_analyzer.py"]
            case_adapter = {
                "tools": {
                    "board_vcs": {
                        "capabilities": ["real_functional_sim", "board_wrapper_functional_sim"],
                        "argv": ["python3", "scripts/verification/case_board_vcs_functional.py"],
                    },
                    "vcs_analyzer": {
                        "capabilities": ["vcs_evidence_analyzer", "semantic_comparison_evidence", "failure_localization_input"],
                        "argv": analyzer_argv,
                        "env": {"ANALYZER_TEST_MODE": "1"},
                    },
                }
            }
            with patch(
                "accagent.framework.stage_repair_execute.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    analyzer_argv, 0, stdout="diagnosis refreshed", stderr=""
                ),
            ) as analyzer, patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value={"status": "ready"},
            ) as feedback, patch(
                "accagent.framework.stage_repair_execute.exact_board_probe_requires_agent_continuation",
                return_value=False,
            ):
                result = record_exact_board_rerun_agent_handoff(
                    {"status": "fail"},
                    case_adapter=case_adapter,
                    run_dir=run_dir,
                )

        self.assertEqual(result["current_vcs_diagnosis_refresh"]["status"], "pass")
        self.assertEqual(analyzer.call_args.args[0], analyzer_argv)
        self.assertEqual(analyzer.call_args.kwargs["cwd"], Path.cwd())
        self.assertEqual(analyzer.call_args.kwargs["env"]["ANALYZER_TEST_MODE"], "1")
        feedback.assert_called_once()

    def test_compile_only_gate_dag_repair_reuses_complete_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            artifacts_dir = run_dir / "verification_artifacts"
            artifacts_dir.mkdir(parents=True)
            for name, payload in {
                "verification_plan.json": {"status": "ready"},
                "verification_artifact_contract.json": {"status": "pass"},
                "verification_review_artifact.json": {"status": "ready"},
                "sacg_state.json": {"status": "ready"},
            }.items():
                (artifacts_dir / name).write_text(
                    json.dumps(payload), encoding="utf-8"
                )

            with patch.dict(
                "os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
            ), patch(
                "accagent.framework.stage_repair_execute.run_optional_post_execution_review"
            ) as review, patch(
                "accagent.framework.stage_verification_plan.plan_verification"
            ) as plan_verification:
                result = execute_stage6_gate_dag_repair(
                    {
                        "id": "repair_step.00",
                        "scope": "stage6_gate_dag_repair",
                        "action": {"debug_layer": "board_axi_ddr_wrapped_system"},
                    },
                    run_dir / "source_sacg_state.json",
                    run_dir,
                    run_dir / "repair_execution",
                    0,
                )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["gate_dag_reused"])
        review.assert_not_called()
        plan_verification.assert_not_called()

    def test_targeted_replay_plan_is_read_from_action_and_bound_to_identity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            first_step = {
                "action": {
                    "targeted_replay_plan": {
                        "stage_id": "stage_00",
                        "rerun_env": {
                            "SPATIALACC_TARGET_BOUNDARY": "boundary.input",
                        },
                        "probe_sequence": ["boundary.input"],
                        "rationale": "first explanation",
                    }
                }
            }
            second_step = {
                "action": {
                    "targeted_replay_plan": {
                        "stage_id": "stage_00",
                        "rerun_env": {
                            "SPATIALACC_TARGET_BOUNDARY": "boundary.input",
                        },
                        "probe_sequence": ["boundary.input", "unused.plan.field"],
                        "rationale": "reworded explanation",
                    }
                }
            }
            third_step = {
                "action": {
                    "targeted_replay_plan": {
                        "stage_id": "stage_00",
                        "rerun_env": {
                            "SPATIALACC_TARGET_BOUNDARY": "boundary.output",
                        },
                    }
                }
            }
            distinguished_step = {
                "action": {
                    "targeted_replay_plan": {
                        "stage_id": "stage_00",
                        "rerun_env": {
                            "SPATIALACC_TARGET_BOUNDARY": "boundary.input",
                            "SPATIALACC_TRACE_FIRST_X_PROVENANCE": "1",
                        },
                    }
                }
            }
            env = {
                "SPATIALACC_BOUNDARY_TRACE": "1",
                "SPATIALACC_TARGETED_REPLAY": "1",
                "SPATIALACC_CHECKPOINT_REPLAY": "1",
            }

            first = targeted_replay_input_identity(run_dir, first_step, env)
            second = targeted_replay_input_identity(run_dir, second_step, env)
            third = targeted_replay_input_identity(run_dir, third_step, env)
            distinguished = targeted_replay_input_identity(run_dir, distinguished_step, env)
            record_targeted_replay_execution(
                run_dir, first, {"status": "fail", "summary": "probe"}
            )

            self.assertEqual(
                targeted_replay_plan_for_step(first_step)["probe_sequence"],
                ["boundary.input"],
            )
            self.assertTrue(targeted_replay_already_executed(run_dir, first))
            self.assertTrue(targeted_replay_already_executed(run_dir, second))
            self.assertFalse(targeted_replay_already_executed(run_dir, third))
            self.assertFalse(targeted_replay_already_executed(run_dir, distinguished))
            self.assertEqual(first["identity_sha256"], second["identity_sha256"])
            self.assertNotEqual(first["identity_sha256"], third["identity_sha256"])
            self.assertNotEqual(first["identity_sha256"], distinguished["identity_sha256"])
            self.assertEqual(
                distinguished["execution_input"]["trace_env"]["SPATIALACC_TRACE_FIRST_X_PROVENANCE"],
                "1",
            )

    def test_targeted_trace_scope_changes_replay_identity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            step = {
                "action": {
                    "targeted_replay_plan": {
                        "stage_id": "stage_00",
                        "rerun_env": {
                            "SPATIALACC_BOUNDARY_TRACE": "1",
                            "SPATIALACC_TARGETED_REPLAY": "1",
                            "SPATIALACC_TARGET_BOUNDARY": "boundary.input",
                        },
                    }
                }
            }
            first = targeted_replay_input_identity(
                run_dir,
                step,
                {"SPATIALACC_TARGETED_TRACE_SCOPE": "upstream"},
            )
            second = targeted_replay_input_identity(
                run_dir,
                step,
                {"SPATIALACC_TARGETED_TRACE_SCOPE": "downstream"},
            )

        self.assertNotEqual(
            first["execution_input"]["trace_env"],
            second["execution_input"]["trace_env"],
        )
        self.assertNotEqual(first["identity_sha256"], second["identity_sha256"])

    def test_targeted_replay_identity_changes_when_semantic_rtl_changes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            stage_id = "stage_00_norm"
            stage_dir = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "stages"
                / stage_id
            )
            source_dir = run_dir / "generated" / "semantic_harness" / stage_id
            stage_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            testbench = stage_dir / "semantic_tb.sv"
            source = source_dir / "Norm.sv"
            input_vector = stage_dir / "input_0.memh"
            weight_stream = stage_dir / "weight.memh"
            testbench.write_text("module semantic_tb; endmodule\n", encoding="utf-8")
            source.write_text("module Norm; wire value = 1'b0; endmodule\n", encoding="utf-8")
            input_vector.write_text("00000000\n", encoding="ascii")
            weight_stream.write_text("00000000\n", encoding="ascii")

            def file_row(path: Path) -> dict[str, str]:
                return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

            contract_path = stage_dir / "testbench_contract.json"
            contract = {
                "stage_id": stage_id,
                "testbench": str(testbench),
                "testbench_sha256": hashlib.sha256(testbench.read_bytes()).hexdigest(),
                "dut_harness": {
                    "top_module": "Norm",
                    "source_files": [file_row(source)],
                },
                "input_vectors": [file_row(input_vector)],
                "real_weight_stream": file_row(weight_stream),
                "expected_output": {"beats": 1, "bits": 32, "lanes": 1},
            }
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            step = {
                "repair_context": {"trace_record": {"stage_id": stage_id}},
                "targeted_replay_plan": {
                    "stage_id": stage_id,
                    "rerun_env": {
                        "SPATIALACC_BOUNDARY_TRACE": "1",
                        "SPATIALACC_TARGET_BOUNDARY": "boundary.input",
                    },
                },
            }
            env = {"SPATIALACC_BOUNDARY_TRACE": "1"}
            first = targeted_replay_input_identity(run_dir, step, env)
            record_targeted_replay_execution(
                run_dir, first, {"status": "fail", "summary": "before RTL edit"}
            )

            source.write_text("module Norm; wire value = 1'b1; endmodule\n", encoding="utf-8")
            contract["dut_harness"]["source_files"] = [file_row(source)]
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            second = targeted_replay_input_identity(run_dir, step, env)

        self.assertNotEqual(
            first["execution_input"]["semantic_input_fingerprint_sha256"],
            second["execution_input"]["semantic_input_fingerprint_sha256"],
        )
        self.assertFalse(targeted_replay_already_executed(run_dir, second))

    def test_stage6_live_context_uses_latest_hierarchical_transition(self) -> None:
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "sacg_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "transitions": [
                            {
                                "debug_layer": "operator_leaf_modules",
                                "verification_scope": "operator_leaf_closure",
                            },
                            {
                                "debug_layer": "single_transformer_layer_kernel",
                                "verification_scope": "single_layer_closure",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            context = stage6_live_verification_context(state_path)

        self.assertEqual(context["verification_layer"], "layer2_connected_single_transformer")
        self.assertEqual(context["verification_scope"], "single_layer_closure")
        self.assertEqual(context["debug_layer"], "single_transformer_layer_kernel")

    def test_stage6_live_context_defaults_to_unpromoted_layer_one(self) -> None:
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "sacg_state.json"
            state_path.write_text("{}", encoding="utf-8")

            context = stage6_live_verification_context(state_path)

        self.assertEqual(context["verification_layer"], "layer1_operator_leaf")
        self.assertEqual(context["verification_scope"], "operator_leaf_closure")

    def _post_validation_fixture(
        self,
        root: Path,
        *,
        materialization_status: str,
    ) -> tuple[Path, Path, dict[str, object]]:
        run_dir = root / "run"
        out_dir = run_dir / "repair_execution"
        source_path = run_dir / "generated" / "semantic_harness.txt"
        manifest_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
        requirements_path = (
            run_dir
            / "verification"
            / "semantic_testbench"
            / "dut_weight_binding_requirements.json"
        )
        for path in (out_dir, source_path.parent, manifest_path.parent, requirements_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        source_path.write_text("current harness source\n", encoding="utf-8")
        manifest_path.write_text('{"status": "incomplete"}\n', encoding="utf-8")
        requirements_path.write_text(
            '{"stage_requirements": [{"stage_id": "stage_00"}]}\n',
            encoding="utf-8",
        )
        step: dict[str, object] = {
            "id": "repair_step.00",
            "scope": "verification_capability_repair",
            "action": {
                "repair_kind": "semantic_loader_harness_binding",
                "violated_contract": "verification_capability_must_execute",
            },
        }
        (out_dir / "agent_patch_application.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "files": [
                        {
                            "path": str(source_path),
                            "after_sha256": hashlib.sha256(
                                source_path.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                    "repair_checkpoint": repair_step_checkpoint(step),
                }
            ),
            encoding="utf-8",
        )
        (out_dir / "agent_requested_validation.json").write_text(
            '{"status": "pass", "results": []}\n', encoding="utf-8"
        )
        blockers = (
            []
            if materialization_status == "pass"
            else ["stage_00: harness top does not declare required input valid port"]
        )
        (out_dir / "dut_weight_binding_materialization.json").write_text(
            json.dumps(
                {
                    "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                    "status": materialization_status,
                    "blockers": blockers,
                    "manifest": str(manifest_path),
                    "stage_harness_count": 0,
                    "single_layer_harness_materialized": False,
                }
            ),
            encoding="utf-8",
        )
        return run_dir, out_dir, step

    def _write_repair_action_disposition(
        self,
        run_dir: Path,
        step: dict[str, object],
        actions: list[dict[str, object]],
    ) -> None:
        repair_path = run_dir / "repair" / "repair_plan.json"
        repair_path.parent.mkdir(parents=True, exist_ok=True)
        repair_path.write_text(
            json.dumps(
                {
                    "repair_workflow": {
                        "status": "ready",
                        "steps": [{"id": step["id"]}],
                        "llm_disposition": {
                            "status": "ready",
                            "summary": "checker-bound current-layer repair",
                            "executable_actions": actions,
                            "approval_action_ids": [],
                            "active_approval_action_ids": [],
                            "deferred_approval_action_ids": [],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )

    def _current_action_frontier(
        self,
        run_dir: Path,
        step: dict[str, object],
        *,
        summary: str = "reconcile current leaf evidence",
    ) -> dict[str, object]:
        self._write_repair_action_disposition(
            run_dir,
            step,
            [
                {
                    "id": "repair.current_leaf",
                    "summary": summary,
                    "requires_approval": False,
                    "acceptance_checkers": ["case_stage_leaf_static"],
                }
            ],
        )
        frontier = current_repair_action_execution_frontier(
            run_dir,
            step,
            "operator_leaf_closure",
        )
        self.assertIsNotNone(frontier)
        assert frontier is not None
        return frontier

    def test_new_post_validation_materialization_failure_requires_fresh_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="incomplete"
            )

            result = resume_prior_resource_failed_validation(
                run_dir, out_dir, 0, step=step
            )

        feedback = result["post_validation_materialization_feedback"]
        self.assertEqual(result["status"], "not_run")
        self.assertEqual(feedback["status"], "ready")
        self.assertEqual(len(feedback["feedback_frontier_sha256"]), 64)
        self.assertEqual(len(feedback["patch_application"]["sha256"]), 64)
        self.assertEqual(len(feedback["requested_validation"]["sha256"]), 64)
        self.assertEqual(len(feedback["materialization"]["sha256"]), 64)
        self.assertEqual(len(feedback["binding_manifest"]["sha256"]), 64)
        self.assertEqual(len(feedback["binding_requirements"]["sha256"]), 64)

    def test_consumed_post_validation_materialization_failure_blocks_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="incomplete"
            )
            feedback = post_validation_materialization_feedback(run_dir, out_dir, step)
            result_path = out_dir / "llm" / "verification_capability_repair_agent_result.json"
            result_path.parent.mkdir()
            result_path.write_text(
                json.dumps(
                    {
                        "agent": "verification_capability_repair_agent",
                        "capability_repair_context": {
                            "repair_step_id": step["id"],
                        },
                        "post_validation_materialization_feedback": feedback,
                    }
                ),
                encoding="utf-8",
            )
            result = resume_prior_resource_failed_validation(
                run_dir, out_dir, 0, step=step
            )

            self.assertTrue(
                capability_agent_consumed_materialization_feedback(
                    out_dir, step, feedback
                )
            )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["post_validation_materialization_feedback_consumed"])

    def test_passing_materialization_keeps_validation_resume(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )

            result = resume_prior_resource_failed_validation(
                run_dir, out_dir, 0, step=step
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["applied_patch_checkpoint_reused"])

    def test_fresh_checker_bound_action_frontier_invalidates_validation_cache(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            frontier = self._current_action_frontier(run_dir, step)

            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=frontier,
            )

        self.assertEqual(result["status"], "not_run")
        self.assertEqual(
            result["fresh_action_execution_frontier"]["identity_sha256"],
            frontier["identity_sha256"],
        )

    def test_consumed_action_frontier_reuses_validation_cache(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            frontier = self._current_action_frontier(run_dir, step)
            mark_repair_action_execution_frontier_consumed(
                out_dir,
                frontier,
                {"status": "fail", "summary": "current probe failed"},
            )

            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=frontier,
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["applied_patch_checkpoint_reused"])

    def test_changed_action_frontier_requires_one_new_probe(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            initial_frontier = self._current_action_frontier(run_dir, step)
            mark_repair_action_execution_frontier_consumed(
                out_dir,
                initial_frontier,
                {"status": "fail", "summary": "initial probe failed"},
            )
            changed_frontier = self._current_action_frontier(
                run_dir,
                step,
                summary="reconcile current leaf evidence after new CCTG slice",
            )

            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=changed_frontier,
            )

        self.assertNotEqual(
            initial_frontier["identity_sha256"],
            changed_frontier["identity_sha256"],
        )
        self.assertEqual(result["status"], "not_run")

    def test_approval_or_malformed_action_cannot_invalidate_validation_cache(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            for action in (
                {
                    "id": "repair.requires_approval",
                    "requires_approval": True,
                    "acceptance_checkers": ["case_stage_leaf_static"],
                },
                {
                    "id": "repair.malformed",
                    "requires_approval": False,
                    "acceptance_checkers": [],
                },
            ):
                self._write_repair_action_disposition(run_dir, step, [action])
                frontier = current_repair_action_execution_frontier(
                    run_dir,
                    step,
                    "operator_leaf_closure",
                )
                result = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    0,
                    step=step,
                    action_execution_frontier=frontier,
                )
                self.assertIsNone(frontier)
                self.assertEqual(result["status"], "pass")

    def test_deferred_approval_action_preserves_checker_bound_auto_frontier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            self._write_repair_action_disposition(
                run_dir,
                step,
                [
                    {
                        "id": "repair.auto_reconcile",
                        "requires_approval": False,
                        "acceptance_checkers": ["case_stage_leaf_static"],
                    },
                    {
                        "id": "repair.escalate_if_needed",
                        "requires_approval": True,
                        "acceptance_checkers": ["repair_boundary_check"],
                    },
                ],
            )
            frontier = current_repair_action_execution_frontier(
                run_dir,
                step,
                "operator_leaf_closure",
            )
            assert frontier is not None
            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=frontier,
            )

        self.assertEqual(frontier["action_ids"], ["repair.auto_reconcile"])
        self.assertEqual(
            frontier["deferred_action_ids"], ["repair.escalate_if_needed"]
        )
        self.assertEqual(result["status"], "not_run")

    def test_incomplete_empty_report_blocks_without_spinning(self) -> None:
        result = repair_loop_disposition({"status": "incomplete", "step_results": []})

        self.assertEqual(result["status"], "blocked")

    def test_passed_repair_execution_requires_full_current_layer_rerun(self) -> None:
        result = repair_loop_disposition(
            {
                "status": "ready",
                "errors": [],
                "step_results": [
                    {"result": {"status": "pass", "stage_passed": True}}
                ],
            }
        )

        self.assertEqual(result["status"], "verification_required")
        self.assertIn("complete current-layer verification gate DAG", result["summary"])

    def test_waiting_agent_supported_capability_replans_upstream(self) -> None:
        capability = {
            "capability_id": "planned_tool.operator_leaf_static_inventory_trace",
            "debug_layer": "operator_leaf_modules",
            "producer_scope": "operator_leaf_closure",
            "target_modules": ["stage_02_residual_add_1"],
            "required_evidence": ["hash-bound generated RTL inventory"],
            "rationale": "classify the checker-visible generated RTL inventory",
        }
        result = repair_loop_disposition(
            {
                "status": "incomplete",
                "step_results": [
                    {
                        "result": {
                            "status": "llm_waiting_for_current_evidence",
                            "summary": "need a current generated RTL inventory",
                            "framework_action_required": True,
                            "required_capabilities": [capability],
                        }
                    }
                ],
            }
        )

        self.assertEqual(result["status"], "continue")
        self.assertTrue(result["upstream_capability_replan_required"])
        self.assertEqual(result["required_capabilities"], [capability])

    def test_repeated_no_edit_llm_wait_blocks_without_new_tool_evidence(self) -> None:
        report = {
            "status": "incomplete",
            "step_results": [
                {
                    "step_id": "repair_step.00",
                    "scope": "verification_capability_repair",
                    "result": {
                        "status": "llm_waiting_for_current_evidence",
                        "repair_kind": "checkpoint_adapter_diagnosis",
                        "summary": "need a different explanation",
                        "framework_action_required": False,
                        "required_capabilities": [
                            {
                                "capability_id": "unconfigured.checkpoint_adapter_observation",
                                "producer_scope": "operator_leaf_closure",
                                "target_modules": ["model_weight_catalog"],
                                "rationale": "first wording",
                            }
                        ],
                    },
                }
            ],
        }

        first = repair_loop_disposition(report)
        report["step_results"][0]["result"]["summary"] = "same facts in new wording"
        report["step_results"][0]["result"]["required_capabilities"][0]["rationale"] = "second wording"
        repeated = repair_loop_disposition(
            report,
            prior_failure_frontiers=first["observed_failure_frontiers"],
        )

        self.assertEqual(first["status"], "continue")
        self.assertEqual(repeated["status"], "blocked")
        self.assertEqual(
            repeated["no_progress_waiting_decisions"],
            ["checkpoint_adapter_diagnosis"],
        )

    def test_unchanged_failure_without_new_observation_blocks(self) -> None:
        result = repair_loop_disposition(
            {
                "status": "incomplete",
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "result": {
                            "status": "fail",
                            "summary": "unchanged applied patch replay did not pass",
                            "llm_record": None,
                            "post_patch_capability_probe_log": None,
                            "capability_reports": [],
                            "instrumentation_evidence_collected": False,
                            "instrumentation_evidence": {"status": "not_run"},
                        },
                    }
                ],
            }
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["no_progress_failures"], ["unchanged applied patch replay did not pass"])

    def test_debug_trace_rerun_forces_fresh_vcs_and_returns_target_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            report_path = (
                run_dir
                / "verification"
                / "operator_leaf_functional"
                / "stage_00.json"
            )
            report_path.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            report_path.write_text(
                json.dumps({"status": "fail", "stage_id": "stage_00", "summary": "old replay"}),
                encoding="utf-8",
            )
            step = {
                "id": "repair_step.00",
                "scope": "debug_trace_rerun",
                "tool": "case_leaf_functional",
                "repair_context": {"trace_record": {"stage_id": "stage_00"}},
                "targeted_replay_plan": {
                    "rerun_env": {
                        "SPATIALACC_TARGET_BOUNDARY": "boundary.stage_00_input",
                    },
                },
                "execution": {"argv": ["case-leaf-tool"], "cwd": str(run_dir)},
            }
            case_adapter = {
                "tools": {
                    "leaf_functional_sim": {
                        "name": "case_leaf_functional",
                        "produces": [str(report_path.parent)],
                    }
                }
            }

            def write_fresh_report(*args, **kwargs):
                report_path.write_text(
                    json.dumps(
                        {
                            "status": "fail",
                            "stage_id": "stage_00",
                            "summary": "fresh VCS diagnostic replay",
                        }
                    ),
                    encoding="utf-8",
                )
                return subprocess.CompletedProcess(
                    args[0], 1, stdout="fresh diagnostic failure", stderr=""
                )

            with patch(
                "accagent.framework.stage_repair_execute.subprocess.run",
                side_effect=write_fresh_report,
            ) as runner:
                result = run_rerun_step(
                    step,
                    out_dir,
                    include_remote=True,
                    timeout_sec=60,
                    case_adapter=case_adapter,
                )
                repeated = run_rerun_step(
                    step,
                    out_dir,
                    include_remote=True,
                    timeout_sec=60,
                    case_adapter=case_adapter,
                )
                ledger_path = (
                    run_dir
                    / "verification"
                    / "debug_closure"
                    / "targeted_replay_ledger.json"
                )
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                for entry in ledger["completed"].values():
                    entry.pop("execution_input", None)
                ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
                handoff_step = json.loads(json.dumps(step))
                handoff_step["targeted_replay_plan"].update(
                    {
                        "source": "validated_flow_controller_handoff",
                        "stage_id": "stage_00",
                    }
                )
                provenance_repeated = run_rerun_step(
                    handoff_step,
                    out_dir,
                    include_remote=True,
                    timeout_sec=60,
                    case_adapter=case_adapter,
                )
            disposition = repair_loop_disposition(
                {"status": "incomplete", "step_results": [{"scope": step["scope"], "result": result}]}
            )

        self.assertEqual(
            runner.call_args.kwargs["env"]["SPATIALACC_FORCE_FRESH_REMOTE_VCS"],
            "1",
        )
        self.assertEqual(
            runner.call_args.kwargs["env"]["SPATIALACC_TARGET_BOUNDARY"],
            "boundary.stage_00_input",
        )
        self.assertEqual(result["leaf_stage_report"], str(report_path))
        self.assertFalse(result["stage_passed"])
        self.assertTrue(result["requires_agent_followup"])
        self.assertIn(str(report_path), result["capability_reports"])
        self.assertEqual(result["targeted_replay_reports"][0]["stage_id"], "stage_00")
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(repeated["status"], "blocked")
        self.assertEqual(provenance_repeated["status"], "blocked")
        self.assertEqual(disposition["status"], "continue")
        self.assertTrue(disposition["capability_producer_replan_required"])
        self.assertNotIn("observation_replan_required", disposition)
        self.assertIn("leaf_stage_report", disposition["observed_failure_frontiers"][0]["artifact_identities"])

    def test_board_trace_does_not_fall_back_to_leaf_verifier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            step = {
                "id": "repair_step.board",
                "scope": "debug_trace_rerun",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "tool": "case_leaf_functional",
                "execution": {
                    "argv": ["python3", "scripts/verification/case_leaf_operator_verify.py"],
                    "cwd": str(run_dir),
                },
            }
            with patch("accagent.framework.stage_repair_execute.subprocess.run") as runner:
                result = run_rerun_step(
                    step,
                    out_dir,
                    include_remote=True,
                    timeout_sec=60,
                )

        runner.assert_not_called()
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["rejected_wrong_layer_tool"])
        self.assertTrue(result["requires_agent_followup"])

    def test_fresh_leaf_trace_replans_before_regular_verification_can_replace_it(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source_state = run_dir / "verification" / "sacg_state.json"
            execution_state = run_dir / "repair_execution" / "sacg_state.json"
            planned_state = run_dir / "repair" / "sacg_state.json"
            report_path = execution_state.parent / "repair_execution_report.json"
            repair_report_path = planned_state.parent / "repair_report.json"
            repair_plan_path = planned_state.parent / "repair_plan.json"
            for path in (source_state, execution_state, planned_state, report_path, repair_report_path):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
            repair_plan_path.write_text(json.dumps({
                "repair_workflow": {
                    "status": "ready",
                    "steps": [{"id": "repair_step.00", "status": "ready_for_agent_patch"}],
                },
            }), encoding="utf-8")
            fresh_trace = {
                "status": "incomplete",
                "errors": ["leaf trace still fails"],
                "step_results": [{
                    "step_id": "repair_step.00",
                    "scope": "debug_trace_rerun",
                    "repair_execution_context": {"debug_layer": "operator_leaf_modules"},
                    "result": {
                        "status": "fail",
                        "requires_agent_followup": True,
                        "stage_passed": False,
                        "summary": "new internal control trace",
                    },
                }],
            }
            repaired = {"status": "ready", "errors": [], "step_results": [{"result": {"status": "pass"}}]}
            with (
                patch("accagent.framework.stage_repair_execute.execute_repair", side_effect=[
                    (report_path, fresh_trace), (report_path, repaired),
                ]) as executor,
                patch("accagent.framework.stage_repair.plan_repair", return_value=(repair_report_path, {
                    "outputs": {"repair_plan": str(repair_plan_path), "sacg_state": str(planned_state)},
                })) as planner,
                patch("accagent.framework.stage_repair_execute.archive_repair_loop_iteration", return_value=run_dir / "iteration_record.json"),
            ):
                _, result = run_repair_loop(Namespace(sacg_state=source_state, max_loop_iters=2))

        planner.assert_called_once()
        self.assertEqual(planner.call_args.args[0].sacg_state, execution_state)
        self.assertEqual(executor.call_args_list[1].args[0].sacg_state, planned_state)
        self.assertEqual(result["repair_loop_disposition"]["status"], "verification_required")

    def test_repeated_failed_probe_uses_content_not_runtime_duration(self) -> None:
        with TemporaryDirectory() as temp_dir:
            probe_path = Path(temp_dir) / "resource_resume.json"

            def write_probe(*, duration_sec: float, stderr_tail: str) -> None:
                probe_path.write_text(
                    json.dumps(
                        {
                            "argv": ["python3", "case_hierarchical_check.py"],
                            "case_adapter_tool": "case_stage_leaf_static",
                            "duration_sec": duration_sec,
                            "returncode": 1,
                            "status": "fail",
                            "summary": "returncode=1",
                            "stderr_tail": stderr_tail,
                        }
                    ),
                    encoding="utf-8",
                )

            report = {
                "status": "incomplete",
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "verification_capability_repair",
                        "result": {
                            "status": "fail",
                            "summary": "unchanged applied patch replay did not pass",
                            "post_patch_capability_probe_log": str(probe_path),
                            "llm_record": None,
                            "capability_reports": [],
                        },
                    }
                ],
            }
            write_probe(duration_sec=0.01, stderr_tail="same failure")
            first = repair_loop_disposition(report)

            write_probe(duration_sec=0.99, stderr_tail="same failure")
            repeated = repair_loop_disposition(
                report,
                prior_failure_frontiers=first["observed_failure_frontiers"],
            )

            write_probe(duration_sec=0.02, stderr_tail="new failure observation")
            changed = repair_loop_disposition(
                report,
                prior_failure_frontiers=first["observed_failure_frontiers"],
            )

        self.assertEqual(first["status"], "continue")
        self.assertEqual(repeated["status"], "blocked")
        self.assertEqual(changed["status"], "continue")

    def test_repeated_leaf_failure_ignores_random_canonical_run_id(self) -> None:
        with TemporaryDirectory() as temp_dir:
            leaf_report = Path(temp_dir) / "stage_00_layer_norm.json"

            def write_leaf_report(canonical_run_id: str) -> None:
                leaf_report.write_text(
                    json.dumps(
                        {
                            "status": "fail",
                            "stage_id": "stage_00_layer_norm",
                            "canonical_run_id": canonical_run_id,
                            "first_failed_module": "Stage00LayerNormHarness",
                            "blockers": [
                                "semantic VCS fingerprint validation failed closed"
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

            report = {
                "status": "incomplete",
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "operator_leaf_closure",
                        "result": {
                            "status": "fail",
                            "summary": "Stage00LayerNormHarness causal slice replay still fails",
                            "leaf_stage_report": str(leaf_report),
                        },
                    }
                ],
            }
            write_leaf_report("operator-leaf-functional-first")
            first = repair_loop_disposition(report)
            write_leaf_report("operator-leaf-functional-second")
            repeated = repair_loop_disposition(
                report,
                prior_failure_frontiers=first["observed_failure_frontiers"],
            )

        self.assertEqual(first["status"], "continue")
        self.assertEqual(repeated["status"], "blocked")
        self.assertEqual(
            repeated["no_progress_failures"],
            ["Stage00LayerNormHarness causal slice replay still fails"],
        )

    def test_repair_loop_reconstructs_legacy_archived_probe_frontier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            report_path = run_dir / "repair_execution" / "repair_execution_report.json"
            loop_record_path = (
                run_dir
                / "repair_execution"
                / "loop"
                / "iteration_0001"
                / "iteration_record.json"
            )
            snapshot_path = loop_record_path.parent / "00_post_patch_probe.json"
            state_path.parent.mkdir(parents=True)
            report_path.parent.mkdir(parents=True)
            loop_record_path.parent.mkdir(parents=True)
            state_path.write_text("{}", encoding="utf-8")
            snapshot_path.write_text(
                json.dumps(
                    {
                        "argv": ["python3", "case_hierarchical_check.py"],
                        "case_adapter_tool": "case_stage_leaf_static",
                        "duration_sec": 0.01,
                        "returncode": 1,
                        "status": "fail",
                        "summary": "returncode=1",
                        "stderr_tail": "same failure",
                    }
                ),
                encoding="utf-8",
            )
            current_probe = run_dir / "repair_execution" / "resource_resume.json"
            current_probe.write_text(
                json.dumps(
                    {
                        "argv": ["python3", "case_hierarchical_check.py"],
                        "case_adapter_tool": "case_stage_leaf_static",
                        "duration_sec": 0.99,
                        "returncode": 1,
                        "status": "fail",
                        "summary": "returncode=1",
                        "stderr_tail": "same failure",
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "status": "incomplete",
                "errors": ["repair_step.00: unchanged replay"],
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "verification_capability_repair",
                        "result": {
                            "status": "fail",
                            "summary": "unchanged replay",
                            "post_patch_capability_probe_log": str(current_probe),
                            "llm_record": None,
                            "capability_reports": [],
                        },
                    }
                ],
            }
            loop_record_path.write_text(
                json.dumps(
                    {
                        "repair_execution_report": report,
                        "evidence_snapshots": [
                            {
                                "role": "post_patch_capability_probe_log",
                                "snapshot_path": str(snapshot_path),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(report_path, report),
            ) as execute_mock, patch(
                "accagent.framework.stage_repair_execute.archive_repair_loop_iteration",
                return_value=run_dir / "iteration_record.json",
            ):
                _, result = run_repair_loop(
                    Namespace(sacg_state=state_path, max_loop_iters=0)
                )

        execute_mock.assert_called_once()
        self.assertEqual(result["repair_loop_disposition"]["status"], "blocked")

    def test_repair_loop_stops_after_unchanged_failure_without_new_observation(self) -> None:
        report = {
            "status": "incomplete",
            "errors": ["repair_step.00: unchanged replay"],
            "step_results": [
                {
                    "step_id": "repair_step.00",
                    "result": {
                        "status": "fail",
                        "summary": "unchanged replay",
                        "llm_record": None,
                        "post_patch_capability_probe_log": None,
                        "capability_reports": [],
                        "instrumentation_evidence_collected": False,
                        "instrumentation_evidence": {"status": "not_run"},
                    },
                }
            ],
        }
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            report_path = run_dir / "repair_execution" / "repair_execution_report.json"
            state_path.parent.mkdir()
            report_path.parent.mkdir()
            state_path.write_text("{}", encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(report_path, report),
            ) as execute_mock, patch(
                "accagent.framework.stage_repair_execute.archive_repair_loop_iteration",
                return_value=run_dir / "iteration_record.json",
            ):
                _, result = run_repair_loop(
                    Namespace(sacg_state=state_path, max_loop_iters=0)
                )

        execute_mock.assert_called_once()
        self.assertEqual(result["repair_loop_disposition"]["status"], "blocked")

    def test_repair_loop_returns_observation_replan_to_flow_controller(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            report_path = run_dir / "repair_execution" / "repair_execution_report.json"
            leaf_report = run_dir / "verification" / "operator_leaf_functional" / "stage_00.json"
            state_path.parent.mkdir(parents=True)
            report_path.parent.mkdir(parents=True)
            leaf_report.parent.mkdir(parents=True)
            state_path.write_text("{}", encoding="utf-8")
            leaf_report.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "stage_id": "stage_00",
                        "first_failed_module": "Stage00Harness",
                        "blockers": ["semantic VCS fingerprint validation failed closed"],
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "status": "incomplete",
                "errors": ["repair_step.00: Stage00 replay still fails"],
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "causal_slice_repair",
                        "result": {
                            "status": "fail",
                            "summary": "Stage00 replay still fails",
                            "leaf_stage_report": str(leaf_report),
                        },
                    }
                ],
            }
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(report_path, report),
            ) as execute_mock, patch(
                "accagent.framework.stage_repair_execute.archive_repair_loop_iteration",
                return_value=run_dir / "iteration_record.json",
            ):
                _, result = run_repair_loop(
                    Namespace(sacg_state=state_path, max_loop_iters=0)
                )

        execute_mock.assert_called_once()
        disposition = result["repair_loop_disposition"]
        self.assertEqual(disposition["status"], "blocked")
        self.assertTrue(disposition["observation_replan_required"])
        self.assertIn("return the bounded current-layer evidence", disposition["summary"])

    def test_stage6_prompt_keeps_current_epoch_and_excludes_old_signal_values(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("repair"))

        self.assertIn("Each new Layer-3 run is a fresh signal epoch", rules)
        self.assertIn("never use old signal values as current evidence", rules)
        self.assertIn("Runtime observation is optional", rules)
        self.assertIn("validation_mode exactly to compute_slot_axi", rules)


if __name__ == "__main__":
    unittest.main()
