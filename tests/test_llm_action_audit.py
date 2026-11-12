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

    def test_debug_boundary_contract_alias_uses_registered_boundary_checker(self) -> None:
        audit = build_audit_from_outputs(
            [
                (
                    "planner",
                    {
                        "executable_actions": [
                            {
                                "id": "materialize_debug_boundary_contract",
                                "acceptance_checkers": ["debug_boundary_contract"],
                            }
                        ]
                    },
                )
            ]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["boundary_contract_check"],
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

    def test_exact_current_team_handoff_targets_are_grounded(self) -> None:
        role = "verification_artifacts.operator_leaf_merge_auditor"
        plan = {
            "subtasks": [
                {
                    "handoff_rule": {"target": role},
                    "role_assignment": {
                        "collaboration_interfaces": {
                            "handoff_to": ["verification_artifacts.hierarchical_verification_auditor"]
                        }
                    },
                }
            ]
        }
        audit = build_audit_from_outputs(
            [("design_team", {"executable_actions": [{"id": "handoff_to_merge", "tool_roles": [role]}]})],
            team_plan=plan,
        )

        self.assertEqual(audit["status"], "pass")
        self.assertIn(role, audit["declared_handoff_roles"])
        self.assertEqual(audit["actions"][0]["grounded_handoff_role_references"], [role])

    def test_declared_handoff_role_in_checker_slot_is_scoped_to_handoff_actions(self) -> None:
        role = "verification_artifacts.operator_leaf_merge_auditor"
        plan = {"subtasks": [{"handoff_to": [role]}]}
        handoff = build_audit_from_outputs(
            [("design_team", {"executable_actions": [{
                "id": "handoff_to_merge_agent",
                "action_type": "handoff_to_merge_agent",
                "tool_roles": [role],
                "acceptance_checkers": [role, "unknown_checker"],
            }]})],
            team_plan=plan,
        )

        self.assertEqual(handoff["status"], "fail")
        action = handoff["actions"][0]
        self.assertEqual(action["grounded_handoff_role_references"], [role])
        self.assertEqual(action["unknown_acceptance_checkers"], ["unknown_checker"])

        embedded_handoff = build_audit_from_outputs(
            [("design_team", {"executable_actions": [{
                "id": "leaf_stage_handoff_to_merge_agent",
                "action_type": "leaf_stage_handoff_to_merge_agent",
                "acceptance_checkers": [role],
            }]})],
            team_plan=plan,
        )
        self.assertEqual(embedded_handoff["status"], "pass")
        self.assertEqual(
            embedded_handoff["actions"][0]["grounded_handoff_role_references"],
            [role],
        )

        id_marked_handoff = build_audit_from_outputs(
            [("design_team", {"executable_actions": [{
                "id": "action.stage_04_mlp_fc.handoff_to_merge_auditor",
                "action_type": "leaf_stage_promotion",
                "acceptance_checkers": [role],
            }]})],
            team_plan=plan,
        )
        self.assertEqual(id_marked_handoff["status"], "pass")
        self.assertEqual(
            id_marked_handoff["actions"][0]["grounded_handoff_role_references"],
            [role],
        )

        validation = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "validate_role",
                "action_type": "validation",
                "tool_roles": ["artifact_hash_check"],
                "acceptance_checkers": [role],
            }]})],
            team_plan=plan,
        )
        self.assertEqual(validation["status"], "fail")
        self.assertEqual(validation["ungrounded_actions"][0]["unknown_acceptance_checkers"], [role])

        tool_validation = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "validate_role_as_tool",
                "action_type": "validation",
                "tool_roles": [role],
                "acceptance_checkers": ["artifact_hash_check"],
            }]})],
            team_plan=plan,
        )
        self.assertEqual(tool_validation["status"], "fail")
        self.assertEqual(tool_validation["ungrounded_actions"][0]["unknown_tool_roles"], [role])

    def test_team_agent_ids_are_plan_bound_handoff_roles(self) -> None:
        role = "verification_artifacts.self_attention_merge_auditor"
        plan = {
            "stage": "verification_artifacts",
            "subtasks": [{
                "id": "verification_artifacts.self_attention_merge_agent",
                "agent": "self_attention_merge_auditor",
            }],
        }
        audit = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "action.stage_00.handoff_to_merge_auditor",
                "action_type": "verification_evidence_preparation",
                "tool_roles": [role],
                "acceptance_checkers": ["case_stage_leaf_static"],
            }]})],
            team_plan=plan,
        )

        self.assertEqual(audit["status"], "pass")
        self.assertIn(role, audit["declared_handoff_roles"])
        self.assertEqual(audit["actions"][0]["grounded_handoff_role_references"], [role])

    def test_native_stage_refinement_actions_are_not_external_tools(self) -> None:
        audit = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "stage5.refine_gate_dag",
                "stage": "verification_artifacts",
                "action_type": "verification_gate_dag_refinement",
                "tool_roles": [
                    "verification_gate_dag_refinement",
                    "stage6_gate_selector_contract_refinement",
                ],
                "acceptance_checkers": [
                    "verification_gate_dag_refinement",
                    "verification_artifact_contract_check",
                ],
            }]})]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["grounded_framework_action_references"],
            ["stage6_gate_selector_contract_refinement", "verification_gate_dag_refinement"],
        )
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["verification_artifact_contract_check"],
        )

        unknown = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "ordinary_action",
                "stage": "parameter_binding",
                "action_type": "ordinary_action",
                "tool_roles": ["verification_gate_dag_refinement"],
            }]})]
        )
        self.assertEqual(unknown["status"], "fail")

        certificate = build_audit_from_outputs(
            [("team", {"executable_actions": [{
                "id": "action.single_block.emit_certificate",
                "stage": "verification_artifacts",
                "action_type": "certificate_issuance",
                "tool_roles": ["verification_contract_promotion"],
                "acceptance_checkers": ["verification_contract_promotion"],
            }]})]
        )
        self.assertEqual(certificate["status"], "pass")
        self.assertEqual(
            certificate["actions"][0]["canonical_acceptance_checkers"],
            ["verification_artifact_contract_check"],
        )

    def test_compile_only_policy_is_context_not_tool_or_checker(self) -> None:
        audit = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "stage5.compile_only_policy",
                "stage": "stage5.verification_artifacts",
                "action_type": "verification_execution_policy",
                "tool_roles": ["verification_execution_policy", "required_real_tool_evidence_check"],
                "acceptance_checkers": ["verification_execution_policy", "human_boundary_check"],
            }]})]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["grounded_policy_references"],
            ["verification_execution_policy"],
        )
        self.assertEqual(
            audit["actions"][0]["canonical_acceptance_checkers"],
            ["human_boundary_check"],
        )

        invalid = build_audit_from_outputs(
            [("planner", {"executable_actions": [{
                "id": "ordinary_action",
                "stage": "parameter_binding",
                "action_type": "ordinary_action",
                "tool_roles": ["verification_execution_policy"],
            }]})]
        )
        self.assertEqual(invalid["status"], "fail")

    def test_undeclared_team_role_remains_ungrounded(self) -> None:
        audit = build_audit_from_outputs(
            [("design_team", {"executable_actions": [{
                "id": "merge", "tool_roles": ["verification_artifacts.unknown_merge_agent"],
            }]})],
            team_plan={"subtasks": [{"handoff_to": ["verification_artifacts.operator_leaf_merge_auditor"]}]},
        )

        self.assertEqual(audit["status"], "fail")
        self.assertEqual(
            audit["ungrounded_actions"][0]["unknown_tool_roles"],
            ["verification_artifacts.unknown_merge_agent"],
        )

    def test_legacy_checker_role_aliases_resolve_to_registered_capabilities(self) -> None:
        audit = build_audit_from_outputs(
            [("design_team", {"executable_actions": [{
                "id": "check_discovery", "tool_roles": ["backend_app_shell_target_discovery_contract", "llm_action_audit"],
            }]})]
        )

        self.assertEqual(audit["status"], "pass")
        self.assertEqual(
            audit["actions"][0]["canonical_tool_roles"],
            ["backend_app_shell_target_discovery_check", "verification_action_audit_check"],
        )
