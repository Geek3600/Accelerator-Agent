"""Minimal current Stage-6 LLM execution-contract regressions."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from accagent.framework.stage_repair_execute import (
    layer3_required_code_edit_errors,
    repair_loop_disposition,
)


class RepairPatchExecutionTest(unittest.TestCase):
    def test_evidence_gap_accepts_runtime_observation_without_speculative_rtl_edit(self) -> None:
        output = {
            "status": "ready_to_apply",
            "blocked_reasons": [],
            "file_edits": [],
            "adaptive_observation_decision": {"mode": "deepen_simulation_observation"},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = layer3_required_code_edit_errors(
                output,
                Path(temp_dir),
                current_signal_epoch=True,
            )

        self.assertEqual(errors, [])

    def test_missing_action_is_rejected_before_a_vcs_replay(self) -> None:
        output = {"status": "ready_to_apply", "blocked_reasons": [], "file_edits": []}
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = layer3_required_code_edit_errors(
                output,
                Path(temp_dir),
                current_signal_epoch=True,
            )

        self.assertTrue(any("observation" in error for error in errors))

    def test_blocked_step_is_turned_into_a_continue_disposition(self) -> None:
        result = repair_loop_disposition(
            {"step_results": [{"result": {"status": "blocked", "summary": "need a deeper signal plan"}}]}
        )

        self.assertEqual(result["status"], "continue")
        self.assertTrue(result["observation_replan_required"])


if __name__ == "__main__":
    unittest.main()
