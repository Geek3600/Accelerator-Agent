from __future__ import annotations

import unittest

from accagent.framework.llm_action_audit import build_audit_from_outputs
from accagent.framework.stage_llm import ACTION_GROUNDING_REGISTRY


class LlmActionAuditTests(unittest.TestCase):
    def test_registered_checks_are_validation_operations_but_unknown_tools_fail(self) -> None:
        checker = "real_weight_semantic_evidence_check"
        self.assertIn(checker, ACTION_GROUNDING_REGISTRY["acceptance_checkers"])
        result = build_audit_from_outputs([("planner", {"executable_actions": [{
            "id": "validate_evidence", "tool_roles": [checker], "acceptance_checkers": [checker],
        }]})])
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["actions"][0]["canonical_tool_roles"], [checker])
        invalid = build_audit_from_outputs([("planner", {"executable_actions": [{
            "id": "unknown", "tool_roles": ["unregistered_validation_operation"],
        }]})])
        self.assertEqual(invalid["status"], "fail")

    def test_existing_backend_static_check_can_be_requested_as_validation_tool(self) -> None:
        checker = "backend_app_shell_integration_contract_static_check"
        self.assertIn(checker, ACTION_GROUNDING_REGISTRY["acceptance_checkers"])
        result = build_audit_from_outputs([("planner", {"executable_actions": [{
            "id": "layer3.backend_eligibility", "tool_roles": [checker],
            "acceptance_checkers": [checker],
        }]})])
        self.assertEqual(result["status"], "pass")

    def test_stage7_metrics_runner_is_registered_as_an_existing_tool(self) -> None:
        self.assertIn("case_stage7_metrics", ACTION_GROUNDING_REGISTRY["tool_roles"])

    def test_stage7_adapter_generator_is_registered_as_an_existing_tool(self) -> None:
        self.assertIn("case_compute_slot_adapter_generate", ACTION_GROUNDING_REGISTRY["tool_roles"])

    def test_stage7_adapter_generator_action_is_not_reported_as_missing_capability(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "flow_controller",
                    {
                        "executable_actions": [
                            {
                                "id": "repair_loader_mapping",
                                "tool_roles": ["case_compute_slot_adapter_generate"],
                                "acceptance_checkers": ["required_real_tool_evidence_check"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_tool_roles"],
            ["case_compute_slot_adapter_generate"],
        )

    def test_stage7_trust_audit_can_use_registered_component_checks(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "flow_controller",
                    {
                        "executable_actions": [
                            {
                                "id": "audit_stage7_artifact_trust",
                                "tool_roles": ["sacg_validate", "artifact_hash_check"],
                                "acceptance_checkers": [
                                    "stage_artifact_trust_barrier_check",
                                    "verification_action_audit_check",
                                    "sacg_memory_check",
                                    "stage_backtrack_request_check",
                                    "stage_retry_request_check",
                                ],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")

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

    def test_real_tool_evidence_role_as_a_checker_normalizes_to_the_required_gate(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "audit_exact_board_evidence",
                                "tool_roles": ["case_vcs_functional_sim"],
                                "acceptance_checkers": ["real_tool_evidence_check"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["required_real_tool_evidence_check"],
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
