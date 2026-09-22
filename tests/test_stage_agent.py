import tempfile
import unittest
from pathlib import Path

from accagent.framework.agent_common import CommandResult, write_json
from accagent.framework.stage_agent import GenericStageAgent


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


if __name__ == "__main__":
    unittest.main()
