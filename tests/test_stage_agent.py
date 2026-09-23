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
