import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.agent_common import CommandResult, write_json
from accagent.framework.agent import TopAgent
from accagent.framework.config import RunCfg
from accagent.framework.llm_config import LlmCfg
from accagent.framework.stage_agent import GenericStageAgent, StageResult


class _FailingRunner:
    def run(self, name: str, command: list[str], env: dict[str, str] | None = None) -> CommandResult:
        return CommandResult(
            name=name,
            command=command,
            cwd="/work",
            returncode=1,
            stdout="current stage report was written before the gate failed",
            stderr="",
            duration_sec=0.1,
            log_path="/work/log.json",
        )


class GenericStageAgentTests(unittest.TestCase):
    def test_stage_worker_inherits_selected_llm_wire_api(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(
                out=root / "run",
                model_source=root / "model.json",
                model_dir=root / "model",
                llm=LlmCfg(
                    model="claude-opus-5",
                    endpoint="https://api.example/v1/chat/completions",
                    api_key="probe-key",
                    wire_api="chat/completions",
                ),
            )

            agent = TopAgent(cfg)

        self.assertEqual(agent.tool_env["SPATIALACC_LLM_WIRE_API"], "chat/completions")

    def test_completed_timing_scope_stops_without_deployment_or_extra_flow_llm(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(out=root / "run", model_source=root / "model.json", model_dir=root / "model")
            state = cfg.out / "backend_board/sacg_state.json"
            write_json(state, {})
            write_json(cfg.out / "backend_board/optimization_request.json", {"scope": "existing_design_timing"})
            command = CommandResult(name="stage", command=["stage"], cwd=str(root), returncode=0,
                stdout="", stderr="", duration_sec=0, log_path=str(root / "stage.log"))
            result = StageResult(name="backend_board", passed=True, command_result=command,
                output_path="backend.json", summary={"status": "ready", "final_design_pass": True,
                    "outputs": {"sacg_state": str(state)}})
            agent = TopAgent(cfg)
            with patch("accagent.framework.agent.GenericStageAgent") as stage, patch.object(
                agent, "choose_next_stage", side_effect=AssertionError("timing scope already complete")
            ), patch.object(agent, "reusable_stage_result", return_value=None):
                stage.return_value.run.return_value = result
                self.assertTrue(agent.run(start_stage="backend_board", source_state=state))
            self.assertEqual(agent.flow_events[-1]["decision"], "complete_existing_design_timing")

    def test_source_repair_and_passing_stage6_do_not_need_extra_flow_llm_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(out=root / "run", model_source=root / "model.json", model_dir=root / "model")
            source_state = cfg.out / "verification" / "sacg_state.json"
            write_json(source_state, {})
            command = CommandResult(
                name="stage", command=["stage"], cwd=str(root), returncode=0,
                stdout="", stderr="", duration_sec=0.0, log_path=str(root / "stage.log"),
            )
            repair = StageResult(
                name="backend_board", passed=False, command_result=command,
                output_path="repair.json", summary={"status": "incomplete",
                    "outputs": {"sacg_state": str(source_state)},
                    "real_tool_results": [{"source_change_requires_stage6_refresh": True}]},
            )
            verified = StageResult(
                name="debug_loop", passed=True, command_result=command,
                output_path="verified.json", summary={"status": "pass", "outputs": {"sacg_state": str(source_state)}},
            )
            backend = StageResult(
                name="backend_board", passed=True, command_result=command,
                output_path="backend.json", summary={"status": "ready", "outputs": {"sacg_state": str(source_state)}},
            )
            agent = TopAgent(cfg)
            with patch(
                "accagent.framework.agent.GenericStageAgent"
            ) as stage, patch(
                "accagent.framework.agent.SACGValidationAgent"
            ) as validation, patch.object(
                agent, "choose_next_stage", return_value=(None, source_state, {"decision": "complete"})
            ) as controller, patch.object(agent, "reusable_stage_result", return_value=None):
                stage.return_value.run.side_effect = [repair, verified, backend]
                validation.return_value.run.return_value = backend
                passed = agent.run(start_stage="backend_board", source_state=source_state)

        self.assertTrue(passed)
        self.assertEqual([call.args[1] for call in stage.call_args_list], ["backend_board", "debug_loop", "backend_board"])
        controller.assert_called_once()

    def test_pending_timing_repair_runs_stage6_before_backend_routing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(out=root / "run", model_source=root / "model.json", model_dir=root / "model")
            source_state = cfg.out / "verification" / "sacg_state.json"
            write_json(source_state, {})
            command = CommandResult(
                name="stage", command=["stage"], cwd=str(root), returncode=0,
                stdout="", stderr="", duration_sec=0.0, log_path=str(root / "stage.log"),
            )
            repaired = StageResult(
                name="backend_board", passed=True, command_result=command,
                output_path="backend.json", summary={
                    "status": "ready",
                    "outputs": {"sacg_state": str(source_state)},
                    "timing_source_repair": {"status": "compiled_pending_vcs"},
                },
            )
            verified = StageResult(
                name="debug_loop", passed=True, command_result=command,
                output_path="verified.json", summary={
                    "status": "pass", "outputs": {"sacg_state": str(source_state)},
                },
            )
            measured = StageResult(
                name="backend_board", passed=True, command_result=command,
                output_path="backend.json", summary={
                    "status": "ready", "outputs": {"sacg_state": str(source_state)},
                },
            )
            agent = TopAgent(cfg)
            with patch("accagent.framework.agent.GenericStageAgent") as stage, patch(
                "accagent.framework.agent.SACGValidationAgent"
            ) as validation, patch.object(
                agent, "choose_next_stage", return_value=(None, source_state, {"decision": "complete"})
            ) as controller, patch.object(agent, "reusable_stage_result", return_value=None):
                stage.return_value.run.side_effect = [repaired, verified, measured]
                validation.return_value.run.return_value = measured
                passed = agent.run(start_stage="backend_board", source_state=source_state)

        self.assertTrue(passed)
        self.assertEqual(
            [call.args[1] for call in stage.call_args_list],
            ["backend_board", "debug_loop", "backend_board"],
        )
        self.assertEqual(agent.flow_events[0]["decision"], "refresh_stage6_compile_evidence")
        self.assertEqual(agent.flow_events[0]["target_stage"], "debug_loop")
        controller.assert_called_once()

    def test_top_agent_can_resume_backend_and_keep_the_flow_controller(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(
                out=root / "run", model_source=root / "model.json", model_dir=root / "model",
            )
            source_state = cfg.out / "verification" / "sacg_state.json"
            write_json(source_state, {"status": "ready"})
            command = CommandResult(
                name="backend_board", command=["backend"], cwd=str(root), returncode=0,
                stdout="", stderr="", duration_sec=0.0, log_path=str(root / "backend.log"),
            )
            result = StageResult(
                name="backend_board", passed=True, command_result=command,
                output_path=str(cfg.out / "backend_board" / "backend_board_report.json"),
                summary={"status": "ready", "outputs": {"sacg_state": str(source_state)}},
            )
            agent = TopAgent(cfg)
            with patch(
                "accagent.framework.agent.GenericStageAgent"
            ) as stage, patch(
                "accagent.framework.agent.SACGValidationAgent"
            ) as validation, patch.object(
                agent, "choose_next_stage", return_value=(None, source_state, {"decision": "complete"})
            ), patch.object(agent, "reusable_stage_result", return_value=None):
                stage.return_value.run.return_value = result
                validation.return_value.run.return_value = result
                passed = agent.run(start_stage="backend_board", source_state=source_state)

        self.assertTrue(passed)
        self.assertEqual(stage.call_count, 1)
        self.assertEqual(stage.call_args.args[1], "backend_board")
        stage.return_value.run.assert_called_once_with(source_state.resolve())

    def test_top_agent_resume_rejects_a_state_from_another_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(out=root / "run", model_source=root / "model.json", model_dir=root / "model")
            source = root / "other_run" / "verification" / "sacg_state.json"
            write_json(source, {})
            agent = TopAgent(cfg)
            with self.assertRaisesRegex(ValueError, "current-run SACG"):
                agent.run(start_stage="backend_board", source_state=source)
            self.assertFalse(agent.report_path.exists())

    def test_failed_stage_surfaces_its_current_structured_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_dir = Path(temp) / "run"
            sacg = run_dir / "template_selection" / "sacg_state.json"
            write_json(sacg, {"status": "ready"})
            report = run_dir / "pipeline_planning" / "pipeline_planning_report.json"
            current = {
                "status": "needs_refinement",
                "errors": ["current pipeline evidence requires a narrower repair"],
                "sacg_state": str(run_dir / "pipeline_planning" / "sacg_state.json"),
            }
            write_json(report, current)

            result = GenericStageAgent(
                _FailingRunner(),
                "pipeline_planning",
                "accagent.framework.stage_pipeline",
                "pipeline_planning",
                "pipeline_planning_report.json",
            ).run(sacg)

        self.assertFalse(result.passed)
        self.assertEqual(result.output_path, str(report))
        self.assertEqual(result.summary, current)


class StageCheckpointReuseTests(unittest.TestCase):
    def _agent(self, root: Path) -> TopAgent:
        return TopAgent(
            RunCfg(
                root=root,
                out=root / "run",
                design="test",
                task_spec=root / "task.md",
                model_source=root / "model.json",
                model_dir=root / "model",
                board_materials_dir=root / "board",
                quantization_materials_dir=root / "quantization",
                tool_materials_dir=root / "tools",
                resume_existing=True,
            )
        )

    def test_dse_measurement_arrival_invalidates_parameter_checkpoint_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            first = agent.stage_input_hash("parameter_binding")
            ledger = agent.out / "parameter_binding/dse_measurements.jsonl"
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.write_text('{"measurement_status": "measured"}\n')
            self.assertNotEqual(first, agent.stage_input_hash("parameter_binding"))

    def test_old_dse_decision_is_not_reused_even_with_current_checkpoint_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            report = agent.out / "parameter_binding/parameter_binding_report.json"
            write_json(report, {"status": "ready", "dse_selection_rationale": {
                "qor_estimator": {"model": "old_estimator"},
            }})
            module = "accagent.framework.stage_params"
            write_json(agent.checkpoint_path("parameter_binding"), {
                "status": "pass", "stage_code_hash": agent.stage_code_hash(module),
                "stage_input_hash": agent.stage_input_hash("parameter_binding"),
            })
            self.assertIsNone(agent.reusable_stage_result(
                stage="parameter_binding", module=module, report_path=report,
            ))

    def test_open_design_backtrack_prevents_target_stage_checkpoint_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            module = "accagent.framework.stage_pipeline"
            report = agent.out / "pipeline_planning/pipeline_planning_report.json"
            write_json(report, {"status": "ready"})
            checkpoint = {
                "status": "pass",
                "stage_code_hash": agent.stage_code_hash(module),
                "stage_input_hash": agent.stage_input_hash("pipeline_planning"),
            }
            write_json(agent.checkpoint_path("pipeline_planning"), checkpoint)
            source_state = agent.out / "parameter_binding/sacg_state.json"
            write_json(source_state, {"memory": {"backtrack_requests": [{
                "id": "empty_dse_request",
                "status": "open",
                "stage": "stage4.parameter_binding",
                "target_stage": "stage3.pipeline_planning",
                "verification_scope": "formal_dse_campaign",
                "failed_gates": ["stage4_dse_candidate_eligibility"],
                "evidence": ["dse_constraint_report.json"],
            }]}})

            self.assertIsNotNone(agent.reusable_stage_result(
                stage="pipeline_planning", module=module, report_path=report,
            ))
            self.assertIsNone(agent.reusable_stage_result(
                stage="pipeline_planning",
                module=module,
                report_path=report,
                source_state=source_state,
            ))

    def test_backend_checkpoint_changes_with_actual_synthesis_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            rtl = agent.out / "generated/chisel/vivado/Kernel.sv"
            rtl.parent.mkdir(parents=True)
            rtl.write_text("module Kernel; endmodule")
            first = agent.stage_input_hash("backend_board")
            self.assertEqual(first, agent.stage_input_hash("backend_board"))
            rtl.write_text("module Kernel; wire changed; endmodule")
            self.assertNotEqual(first, agent.stage_input_hash("backend_board"))

    def test_debug_loop_checkpoint_changes_with_board_validation_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            compile_only = {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
            runtime = {"SPATIALACC_VERIFICATION_POLICY": "full_semantic_simulation"}
            with patch.dict("os.environ", compile_only):
                compile_hash = agent.stage_input_hash("debug_loop")
            with patch.dict("os.environ", runtime):
                runtime_hash = agent.stage_input_hash("debug_loop")
            self.assertNotEqual(compile_hash, runtime_hash)

    def test_backend_tool_pass_with_pending_qor_repair_is_not_final_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            report = agent.out / "backend_board/backend_board_report.json"
            module = "accagent.framework.stage_backend"
            write_json(agent.checkpoint_path("backend_board"), {
                "status": "pass", "stage_code_hash": agent.stage_code_hash(module),
                "stage_input_hash": agent.stage_input_hash("backend_board"),
            })
            write_json(report, {"status": "ready", "final_design_pass": False,
                                "qor_optimization": {"decision": "local_optimization"},
                                "timing_source_repair": {"status": "compile_failed"}})
            self.assertIsNone(agent.reusable_stage_result(
                stage="backend_board", module=module, report_path=report,
            ))

    def test_raised_clock_target_does_not_reuse_previously_complete_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            report = agent.out / "backend_board/backend_board_report.json"
            module = "accagent.framework.stage_backend"
            write_json(report, {"status": "ready", "final_design_pass": True,
                                "qor": {"clock_frequency_mhz": 121.08}})
            request = agent.out / "backend_board/optimization_request.json"
            write_json(request, {"scope": "existing_design_timing", "clock_frequency_mhz": 150})
            write_json(agent.checkpoint_path("backend_board"), {
                "status": "pass", "stage_code_hash": agent.stage_code_hash(module),
                "stage_input_hash": agent.stage_input_hash("backend_board"),
            })
            self.assertIsNone(agent.reusable_stage_result(stage="backend_board", module=module, report_path=report))
            write_json(request, {"scope": "existing_design_timing", "clock_frequency_mhz": 100})
            self.assertIsNotNone(agent.reusable_stage_result(stage="backend_board", module=module, report_path=report))

    def test_stage0_reuses_passed_input_after_current_semantic_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            report = agent.out / "input" / "prepared_inputs.json"
            write_json(report, {"status": "ready", "errors": []})
            checkpoint = agent.checkpoint_path("input_preparation")
            write_json(
                checkpoint,
                {
                    "stage": "input_preparation",
                    "status": "pass",
                    "stage_code_hash": "old-stage-input-code",
                    "stage_input_hash": agent.stage_input_hash("input_preparation"),
                },
            )

            with patch.object(agent, "semantic_revalidation_errors", return_value=[]) as revalidate:
                result = agent.reusable_stage_result(
                    stage="input_preparation",
                    module="accagent.framework.stage_input",
                    report_path=report,
                )

        self.assertIsNotNone(result)
        self.assertEqual(result.command_result.command, ["checkpoint", "reuse", "input_preparation", "semantic_revalidation"])
        revalidate.assert_called_once_with("input_preparation", report)

    def test_constraint_extraction_uses_its_initial_graph_as_checkpoint_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)

            state = agent.expected_stage_sacg_state(
                "constraint_extraction", "constraint_extraction"
            )

        self.assertEqual(state, root / "run" / "constraint_extraction" / "initial_design_graph.json")

    def test_stage0_does_not_reuse_incomplete_report_after_code_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            report = agent.out / "input" / "prepared_inputs.json"
            write_json(report, {"status": "incomplete", "errors": ["missing physical domain"]})
            write_json(
                agent.checkpoint_path("input_preparation"),
                {
                    "stage": "input_preparation",
                    "status": "pass",
                    "stage_code_hash": "old-stage-input-code",
                    "stage_input_hash": agent.stage_input_hash("input_preparation"),
                },
            )

            with patch.object(agent, "semantic_revalidation_errors") as revalidate:
                result = agent.reusable_stage_result(
                    stage="input_preparation",
                    module="accagent.framework.stage_input",
                    report_path=report,
                )

        self.assertIsNone(result)
        revalidate.assert_not_called()

    def test_stage1_reuses_only_after_current_semantic_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            report = agent.out / "constraint_extraction" / "constraint_extraction_report.json"
            state = agent.out / "constraint_extraction" / "sacg_state.json"
            write_json(report, {"status": "ready", "errors": []})
            write_json(state, {"sacg_version": "1.0", "nodes": [], "edges": [], "constraints": []})
            write_json(
                agent.checkpoint_path("constraint_extraction"),
                {
                    "stage": "constraint_extraction",
                    "status": "pass",
                    "stage_code_hash": "old-stage-constraint-code",
                    "stage_input_hash": "old-stage1-input",
                },
            )

            with patch.object(agent, "semantic_revalidation_errors", return_value=[]) as revalidate:
                result = agent.reusable_stage_result(
                    stage="constraint_extraction",
                    module="accagent.framework.stage_constraints",
                    report_path=report,
                    sacg_state=state,
                )

        self.assertIsNotNone(result)
        self.assertEqual(result.command_result.command[-1], "semantic_revalidation")
        revalidate.assert_called_once_with("constraint_extraction", report)

    def test_later_stage_does_not_reuse_when_its_input_hash_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            report = agent.out / "pipeline_planning" / "pipeline_planning_report.json"
            state = agent.out / "pipeline_planning" / "sacg_state.json"
            write_json(report, {"status": "ready", "errors": []})
            write_json(state, {"sacg_version": "1.0", "nodes": [], "edges": [], "constraints": []})
            write_json(
                agent.checkpoint_path("pipeline_planning"),
                {
                    "stage": "pipeline_planning",
                    "status": "pass",
                    "stage_code_hash": agent.stage_code_hash("accagent.framework.stage_pipeline"),
                    "stage_input_hash": "old-stage3-input",
                },
            )

            with patch.object(agent, "semantic_revalidation_errors") as revalidate:
                result = agent.reusable_stage_result(
                    stage="pipeline_planning",
                    module="accagent.framework.stage_pipeline",
                    report_path=report,
                    sacg_state=state,
                )

        self.assertIsNone(result)
        revalidate.assert_called_once_with("pipeline_planning", report)

    def test_code_generation_input_hash_tracks_physical_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            write_json(
                agent.out / "parameter_binding" / "sacg_state.json",
                {"sacg_version": "1.0"},
            )
            template_dir = root / "templates"
            template_dir.mkdir()
            template = template_dir / "PhysicalResources.scala"
            template.write_text("initial\n", encoding="utf-8")

            with patch("accagent.framework.agent.DEFAULT_TEMPLATE_DIR", template_dir):
                before = agent.stage_input_hash("code_generation")
                template.write_text("updated\n", encoding="utf-8")
                after = agent.stage_input_hash("code_generation")

        self.assertNotEqual(before, after)

    def test_verification_artifacts_input_hash_tracks_codegen_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            write_json(agent.out / "code_generation" / "sacg_state.json", {"status": "ready"})
            write_json(agent.out / "code_generation" / "code_generation_manifest.json", {"version": 1})
            write_json(agent.out / "code_generation" / "code_generation_report.json", {"status": "ready"})

            before = agent.stage_input_hash("verification_artifacts")
            write_json(agent.out / "code_generation" / "code_generation_manifest.json", {"version": 2})
            after = agent.stage_input_hash("verification_artifacts")

        self.assertNotEqual(before, after)

    def test_stage3_and_stage4_dispatch_to_semantic_revalidators(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            pipeline_report = agent.out / "pipeline_planning" / "pipeline_planning_report.json"
            parameter_report = agent.out / "parameter_binding" / "parameter_binding_report.json"

            with patch(
                "accagent.framework.stage_pipeline.revalidate_pipeline_planning", return_value=[]
            ) as pipeline_revalidate, patch(
                "accagent.framework.stage_params.revalidate_parameter_binding", return_value=[]
            ) as parameter_revalidate:
                pipeline_errors = agent.semantic_revalidation_errors("pipeline_planning", pipeline_report)
                parameter_errors = agent.semantic_revalidation_errors("parameter_binding", parameter_report)

        self.assertEqual(pipeline_errors, [])
        self.assertEqual(parameter_errors, [])
        pipeline_revalidate.assert_called_once_with(pipeline_report)
        parameter_revalidate.assert_called_once_with(parameter_report)


class TopAgentBootstrapRecoveryTests(unittest.TestCase):
    @staticmethod
    def result(name: str, passed: bool, root: Path) -> StageResult:
        return StageResult(
            name=name,
            passed=passed,
            command_result=CommandResult(
                name=name,
                command=["fake", name],
                cwd=str(root),
                returncode=0 if passed else 1,
                stdout="",
                stderr="",
                duration_sec=0.0,
                log_path=str(root / f"{name}.log"),
            ),
            output_path=str(root / f"{name}.json"),
            summary={"status": "ready" if passed else "incomplete"},
        )

    def test_template_failure_is_routed_through_flow_controller_and_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = RunCfg(
                root=root,
                out=root / "run",
                design="test",
                task_spec=root / "task.md",
                model_source=root / "model.json",
                model_dir=root / "model",
                board_materials_dir=root / "board",
                quantization_materials_dir=root / "quantization",
                tool_materials_dir=root / "tools",
                resume_existing=False,
            )
            agent = TopAgent(cfg)
            template_attempts = 0
            routed_failures: list[tuple[int, str]] = []

            def input_run(*_args, **_kwargs):
                return self.result("input_preparation", True, root)

            def constraint_run(*_args, **_kwargs):
                return self.result("constraint_extraction", True, root)

            def template_run(*_args, **_kwargs):
                nonlocal template_attempts
                template_attempts += 1
                return self.result("template_selection", template_attempts > 1, root)

            def generic_run(instance, _sacg):
                return self.result(instance.name, True, root)

            def validation_run(*_args, **_kwargs):
                return self.result("sacg_validation", True, root)

            def choose_next(*, current_index, result, sacg_state, **_kwargs):
                if not result.passed:
                    routed_failures.append((current_index, result.name))
                    return current_index, sacg_state, {
                        "decision": "retry",
                        "reason": "test flow-controller same-stage retry",
                        "target_stage": result.name,
                        "target_index": current_index,
                    }
                return current_index + 1, sacg_state, {
                    "decision": "proceed",
                    "reason": "test flow-controller proceed",
                }

            with (
                patch("accagent.framework.agent.InputPreparationAgent.run", side_effect=input_run),
                patch("accagent.framework.agent.ConstraintExtractionAgent.run", side_effect=constraint_run),
                patch("accagent.framework.agent.TemplateSelectionAgent.run", side_effect=template_run),
                patch("accagent.framework.agent.GenericStageAgent.run", new=generic_run),
                patch("accagent.framework.agent.SACGValidationAgent.run", side_effect=validation_run),
                patch.object(agent, "choose_next_stage", side_effect=choose_next),
            ):
                self.assertTrue(agent.run())

        self.assertEqual(template_attempts, 2)
        self.assertEqual(routed_failures, [(2, "template_selection")])


class TopAgentFlowControllerBacktrackTests(unittest.TestCase):
    @staticmethod
    def _agent(root: Path) -> TopAgent:
        return TopAgent(
            RunCfg(
                root=root,
                out=root / "run",
                design="test",
                task_spec=root / "task.md",
                model_source=root / "model.json",
                model_dir=root / "model",
                board_materials_dir=root / "board",
                quantization_materials_dir=root / "quantization",
                tool_materials_dir=root / "tools",
                resume_existing=False,
            )
        )

    @staticmethod
    def _stage_specs() -> list[tuple[str, str, str, str]]:
        names = [
            "input_preparation",
            "constraint_extraction",
            "template_selection",
            "pipeline_planning",
            "parameter_binding",
            "code_generation",
            "verification_artifacts",
            "debug_loop",
            "backend_board",
        ]
        return [(name, "", "", "") for name in names]

    @staticmethod
    def _failed_debug_result(root: Path) -> StageResult:
        return StageResult(
            name="debug_loop",
            passed=False,
            command_result=CommandResult(
                name="debug_loop",
                command=["fake", "debug_loop"],
                cwd=str(root),
                returncode=1,
                stdout="",
                stderr="verification gate failed",
                duration_sec=0.0,
                log_path=str(root / "debug_loop.log"),
            ),
            output_path=str(root / "debug_loop.json"),
            summary={"status": "needs_repair"},
        )

    def _choose(self, action: dict) -> tuple[int | None, dict]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            review = {
                "agent_status": "backtrack",
                "agent_summary": "restore trusted verification artifacts before retrying Stage-6",
                "agent_executable_actions": [action],
            }
            with patch.object(agent, "flow_controller_review", return_value=review):
                next_index, _, event = agent.choose_next_stage(
                    current_index=7,
                    result=self._failed_debug_result(root),
                    sacg_state=None,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"debug_loop": 1},
                    backtrack_count=0,
                )
        return next_index, event

    def test_backend_flow_controller_receives_run_local_timing_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            result = StageResult(
                name="backend_board",
                passed=False,
                command_result=self._failed_debug_result(root).command_result,
                output_path=str(root / "backend_board.json"),
                summary={"timing_source_repair": {"status": "compiled_pending_vcs"}},
            )
            with patch(
                "accagent.framework.agent.run_stage_agent",
                return_value={"result_path": "flow.json", "output": {"status": "retry_current_stage"}},
            ) as run_agent:
                agent.flow_controller_review(
                    current_stage="backend_board",
                    result=result,
                    sacg_state=None,
                    stage_names=[name for name, *_ in self._stage_specs()],
                    attempt_count=1,
                )

        inputs = run_agent.call_args.kwargs["inputs"]
        self.assertIn("repair_timing_sources", inputs["stage_local_capabilities"]["backend_board"]["run_local_timing_repair"])
        self.assertEqual(inputs["recent_stage_summary"]["timing_source_repair"]["status"], "compiled_pending_vcs")
        self.assertTrue(inputs["flow_policy"]["compiled_pending_vcs_must_not_restart_code_generation"])

    def test_failed_debug_loop_defers_a_later_stage_backtrack_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(state_path, {"memory": {"backtrack_requests": [{
                "id": "old_backend_request", "status": "open", "target_stage": "backend_board",
                "failure_category": "design_target_miss",
                "failed_gates": ["case_stage7_metrics"],
                "evidence": ["artifact.stage7.backend_real_tool_results"],
            }]}})
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=7,
                    result=self._failed_debug_result(root),
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"debug_loop": 1},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 7)
        self.assertEqual(event["decision"], "retry_replan")
        self.assertEqual(event["deferred_request_id"], "old_backend_request")
        self.assertEqual(event["target_stage"], "debug_loop")

    def test_passed_stage_advances_in_order_before_later_backtrack_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(state_path, {"memory": {"backtrack_requests": [{
                "id": "old_backend_request",
                "status": "open",
                "target_stage": "backend_board",
                "failure_category": "design_target_miss",
                "failed_gates": ["case_stage7_metrics"],
                "evidence": ["artifact.stage7.backend_real_tool_results"],
            }]}})
            result = StageResult(
                name="parameter_binding",
                passed=True,
                command_result=CommandResult(
                    name="parameter_binding",
                    command=["fake", "parameter_binding"],
                    cwd=str(root),
                    returncode=0,
                    stdout="",
                    stderr="",
                    duration_sec=0.0,
                    log_path=str(root / "parameter_binding.log"),
                ),
                output_path=str(root / "parameter_binding.json"),
                summary={"status": "ready"},
            )
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=4,
                    result=result,
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"parameter_binding": 1},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 5)
        self.assertEqual(event["decision"], "proceed")
        self.assertEqual(
            event["deferred_backtrack_requests"],
            [{"id": "old_backend_request", "target_stage": "backend_board"}],
        )

    def test_passed_backtrack_target_proceeds_to_downstream_recheck(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(state_path, {"memory": {"backtrack_requests": [{
                "id": "empty_dse_request",
                "status": "open",
                "stage": "stage4.parameter_binding",
                "target_stage": "stage3.pipeline_planning",
                "verification_scope": "formal_dse_campaign",
                "failed_gates": ["stage4_dse_candidate_eligibility"],
                "evidence": ["dse_constraint_report.json"],
            }]}})
            passed = StageResult(
                name="pipeline_planning",
                passed=True,
                command_result=CommandResult(
                    name="pipeline_planning",
                    command=["fake", "pipeline_planning"],
                    cwd=str(root),
                    returncode=0,
                    stdout="",
                    stderr="",
                    duration_sec=0.0,
                    log_path=str(root / "pipeline_planning.log"),
                ),
                output_path=str(root / "pipeline_planning.json"),
                summary={"status": "ready"},
            )
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=3,
                    result=passed,
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"pipeline_planning": 2},
                    backtrack_count=0,
                )
            self.assertEqual(next_index, 4)
            self.assertEqual(event["decision"], "proceed")
            self.assertEqual(
                event["deferred_backtrack_requests"],
                [{"id": "empty_dse_request", "target_stage": "pipeline_planning"}],
            )

            failed_dse = StageResult(
                name="parameter_binding",
                passed=False,
                command_result=CommandResult(
                    name="parameter_binding",
                    command=["fake", "parameter_binding"],
                    cwd=str(root),
                    returncode=1,
                    stdout="",
                    stderr="no eligible candidate",
                    duration_sec=0.0,
                    log_path=str(root / "parameter_binding.log"),
                ),
                output_path=str(root / "parameter_binding.json"),
                summary={"status": "incomplete"},
            )
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=4,
                    result=failed_dse,
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"parameter_binding": 2},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 3)
        self.assertEqual(event["decision"], "backtrack")
        self.assertEqual(event["request_id"], "empty_dse_request")

    def test_invalid_backtrack_target_does_not_mask_current_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(
                state_path,
                {
                    "memory": {
                        "backtrack_requests": [{
                            "id": "malformed_request",
                            "status": "open",
                            "target_stage": "repair the current backend package before retry",
                            "failure_category": "design_target_miss",
                            "failed_gates": ["case_stage7_metrics"],
                            "evidence": ["artifact.stage7.backend_real_tool_results"],
                        }],
                        "retry_requests": [{
                            "id": "retry_current_stage",
                            "status": "open",
                            "target_stage": "backend_board",
                        }],
                    }
                },
            )
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=8,
                    result=StageResult(
                        name="backend_board",
                        passed=False,
                        command_result=CommandResult(
                            name="backend_board",
                            command=["fake", "backend_board"],
                            cwd=str(root),
                            returncode=1,
                            stdout="",
                            stderr="failed",
                            duration_sec=0.0,
                            log_path=str(root / "backend_board.log"),
                        ),
                        output_path=str(root / "backend_board.json"),
                        summary={"status": "incomplete"},
                    ),
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"backend_board": 1},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 8)
        self.assertEqual(event["decision"], "retry")
        self.assertEqual(event["request_id"], "retry_current_stage")
        self.assertEqual(event["ignored_invalid_backtrack_requests"][0]["id"], "malformed_request")

    def test_llm_backtrack_routes_to_unique_unapproved_earlier_stage(self) -> None:
        next_index, event = self._choose(
            {
                "id": "bounded_verification_artifact_repair",
                "stage": "verification_artifacts",
                "failure_category": "functional_design_failure",
                "failed_gates": ["case_single_layer_stream_sim"],
                "evidence": ["artifact.stage6.verification_result"],
                "requires_approval": False,
                "rationale": "RTL integration evidence shows the streaming design fails its functional gate",
            }
        )

        self.assertEqual(next_index, 6)
        self.assertEqual(event["decision"], "backtrack")
        self.assertEqual(event["target_stage"], "verification_artifacts")
        self.assertEqual(event["target_index"], 6)
        self.assertEqual(event["source"], "llm_flow_controller")

    def test_sacg_hash_or_manifest_failure_retries_current_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(state_path, {"memory": {"backtrack_requests": [{
                "id": "manifest_hash_drift",
                "status": "open",
                "target_stage": "code_generation",
                "reason": "Stage-6 promotion rejected because manifest hash drifted",
            }]}})
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=7,
                    result=self._failed_debug_result(root),
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"debug_loop": 1},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 7)
        self.assertEqual(event["decision"], "retry_framework_failure_current_stage")
        self.assertEqual(event["target_stage"], "debug_loop")
        self.assertEqual(event["ignored_framework_backtrack_request_id"], "manifest_hash_drift")

    def test_local_qor_miss_with_report_evidence_can_enter_verification_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(state_path, {"memory": {"backtrack_requests": [{
                "id": "local_timing_optimization",
                "status": "open",
                "target_stage": "stage6.verification",
                "verification_scope": "local_qor_optimization",
                "reason": "The measured design clock is below the requested target",
                "missing_or_invalid_contracts": ["clock_frequency_mhz"],
                "evidence": ["artifact.stage7.backend_real_tool_results"],
            }]}})
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=8,
                    result=self._failed_debug_result(root),
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"backend_board": 1},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 7)
        self.assertEqual(event["decision"], "backtrack")
        self.assertEqual(event["target_stage"], "debug_loop")

    def test_llm_framework_failure_action_cannot_rewind_design_stages(self) -> None:
        next_index, event = self._choose(
            {
                "id": "repair_agent_routing",
                "stage": "code_generation",
                "failure_category": "framework_bug",
                "requires_approval": False,
                "rationale": "The flow controller routed an evidence binding failure to code generation",
            }
        )

        self.assertEqual(next_index, 7)
        self.assertEqual(event["decision"], "retry_framework_failure_current_stage")
        self.assertEqual(event["target_stage"], "debug_loop")
        self.assertEqual(event["ignored_framework_backtrack_actions"][0]["id"], "repair_agent_routing")

    def test_passed_stage_ignores_stale_framework_backtrack_and_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = self._agent(root)
            state_path = root / "sacg_state.json"
            write_json(state_path, {"memory": {"backtrack_requests": [{
                "id": "stale_hash_drift",
                "status": "open",
                "target_stage": "code_generation",
                "reason": "Old manifest SHA256 binding failed before framework repair",
            }]}})
            passed = StageResult(
                name="debug_loop",
                passed=True,
                command_result=self._failed_debug_result(root).command_result,
                output_path=str(root / "debug_loop.json"),
                summary={"status": "pass"},
            )
            with patch.object(agent, "flow_controller_review", return_value={}):
                next_index, _, event = agent.choose_next_stage(
                    current_index=7,
                    result=passed,
                    sacg_state=state_path,
                    stage_specs=self._stage_specs(),
                    attempt_counts={"debug_loop": 2},
                    backtrack_count=0,
                )

        self.assertEqual(next_index, 8)
        self.assertEqual(event["decision"], "proceed")
        self.assertEqual(event["ignored_framework_backtrack_requests"][0]["id"], "stale_hash_drift")

    def test_ambiguous_stage5_verification_repair_routes_to_verification_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            action = {
                "id": "repair_verification_contract_provenance",
                "stage": "stage5",
                "requires_approval": False,
                "consumes": [
                    "artifact.stage5.verification_artifact_contract",
                    "artifact.stage5.llm_action_audit",
                ],
                "produces": ["artifact.stage5.verification_plan"],
            }
            target = agent.stage_key_for_action(action, [name for name, *_ in self._stage_specs()])

        self.assertEqual(target, "verification_artifacts")
        next_index, event = self._choose(action)
        self.assertEqual(next_index, 7)
        self.assertEqual(event["decision"], "retry_replan")
        self.assertEqual(event["ignored_unsupported_design_backtrack_actions"][0]["id"], action["id"])

    def test_ambiguous_stage5_codegen_target_keeps_codegen_route(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agent = self._agent(Path(temp))
            target = agent.stage_key_for_action(
                {
                    "id": "repair_generated_hardware_package",
                    "stage": "stage5",
                    "requires_approval": False,
                    "produces": ["artifact.stage5.generated_code_package"],
                },
                [name for name, *_ in self._stage_specs()],
            )

        self.assertEqual(target, "code_generation")

    def test_llm_backtrack_rejects_approval_or_non_earlier_actions(self) -> None:
        for action in (
            {
                "id": "approval_required_repair",
                "stage": "verification_artifacts",
                "requires_approval": True,
            },
            {
                "id": "same_stage_repair",
                "stage": "debug_loop",
                "requires_approval": False,
            },
        ):
            with self.subTest(action=action["id"]):
                next_index, event = self._choose(action)
                self.assertEqual(next_index, 7)
                self.assertEqual(event["decision"], "retry_replan")
                self.assertEqual(event["target_stage"], "debug_loop")


if __name__ == "__main__":
    unittest.main()
