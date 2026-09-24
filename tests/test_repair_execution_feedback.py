"""Current Stage-6 feedback semantics."""

from __future__ import annotations

import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from accagent.framework.stage_repair_execute import (
    board_integration_prompt_rules,
    repair_loop_disposition,
    run_repair_loop,
)


class RepairExecutionFeedbackTest(unittest.TestCase):
    def test_incomplete_empty_report_blocks_without_spinning(self) -> None:
        result = repair_loop_disposition({"status": "incomplete", "step_results": []})

        self.assertEqual(result["status"], "blocked")

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

    def test_stage6_prompt_keeps_current_epoch_and_excludes_old_signal_values(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("repair"))

        self.assertIn("Each new Layer-3 run is a fresh signal epoch", rules)
        self.assertIn("never use old signal values as current evidence", rules)
        self.assertIn("at least 300 real scalar signals", rules)


if __name__ == "__main__":
    unittest.main()
