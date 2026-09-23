import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.agent_common import CommandResult, write_json
from accagent.framework.agent import TopAgent
from accagent.framework.config import RunCfg
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


if __name__ == "__main__":
    unittest.main()
