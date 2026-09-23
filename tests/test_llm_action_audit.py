from __future__ import annotations

import unittest

from accagent.framework.llm_action_audit import build_audit_from_outputs


class LlmActionAuditTests(unittest.TestCase):
    def test_unqualified_real_tool_checker_is_normalized(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "discover_board_target",
                                "tool_roles": ["app_shell_target_discovery_contract"],
                                "acceptance_checkers": ["app_shell_target_discovery_contract"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        action = audit["actions"][0]
        self.assertEqual(
            action["canonical_acceptance_checkers"],
            ["real_tool.app_shell_target_discovery_contract"],
        )

