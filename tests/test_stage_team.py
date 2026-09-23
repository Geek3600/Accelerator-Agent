from __future__ import annotations

from unittest import TestCase

from accagent.framework.stage_team import acceptance_checkers_for


class StageTeamAcceptanceCheckersTests(TestCase):
    def test_board_work_uses_the_registered_real_tool_evidence_gate(self) -> None:
        checkers = acceptance_checkers_for([], ["exact board AXI/DDR functional verification"])

        self.assertIn("required_real_tool_evidence_check", checkers)
        self.assertNotIn("real_tool_evidence_check", checkers)
