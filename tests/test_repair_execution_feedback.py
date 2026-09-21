"""Current Stage-6 feedback semantics.

The former suite modeled retired Stage-8 hash/checkpoint veto chains. These
tests protect the active rule: current evidence either yields a repair or a
new observation plan, never a terminal framework block.
"""

from __future__ import annotations

import unittest

from accagent.framework.stage_repair_execute import (
    board_integration_prompt_rules,
    repair_loop_disposition,
)


class RepairExecutionFeedbackTest(unittest.TestCase):
    def test_no_progress_requests_an_observation_replan(self) -> None:
        result = repair_loop_disposition({"step_results": []})

        self.assertEqual(result["status"], "continue")
        self.assertTrue(result["observation_replan_required"])

    def test_stage6_prompt_keeps_current_epoch_and_excludes_old_signal_values(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("repair"))

        self.assertIn("Each new Layer-3 run is a fresh signal epoch", rules)
        self.assertIn("never use old signal values as current evidence", rules)
        self.assertIn("at least 300 real scalar signals", rules)


if __name__ == "__main__":
    unittest.main()
