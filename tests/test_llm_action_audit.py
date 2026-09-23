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

    def test_unqualified_real_tool_checker_is_normalized_when_used_as_checker(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "discover_board_target",
                                "tool_roles": ["case_board_interface_discovery"],
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

    def test_registered_checker_suffix_is_normalized(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "check_kernel_replay",
                                "tool_roles": ["targeted_replay"],
                                "acceptance_checkers": ["connected_kernel_targeted_replay_checker"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["connected_kernel_targeted_replay_check"],
        )

    def test_registered_checker_base_name_is_normalized(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "audit_verification_actions",
                                "tool_roles": ["verification_action_audit"],
                                "acceptance_checkers": ["verification_action_audit"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["verification_action_audit_check"],
        )

    def test_functional_sim_contract_alias_requires_the_real_functional_gate(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "run_board_wrapped_functional_sim",
                                "tool_roles": ["case_vcs_functional_sim"],
                                "acceptance_checkers": ["functional_sim_contract_check"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["functional_sim"],
        )

    def test_registered_tool_base_name_is_normalized(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "replay_connected_kernel",
                                "tool_roles": ["connected_kernel_targeted_replay"],
                                "acceptance_checkers": ["targeted_replay_check"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_tool_roles"],
            ["connected_kernel_targeted_replay_check"],
        )

    def test_unknown_checker_still_fails_closed(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "unknown_gate",
                                "tool_roles": ["artifact_hash_check"],
                                "acceptance_checkers": ["totally_unregistered_gate"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "fail")
        self.assertEqual(
            audit["ungrounded_actions"][0]["unknown_acceptance_checkers"],
            ["totally_unregistered_gate"],
        )
