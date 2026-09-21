"""Current LLM routing contracts for the Stage-6 repair loop."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from accagent.framework.stage_repair import build_repair_actions, repair_specialist_trigger
from accagent.framework.stage_verification import exact_failed_stage6_route


class ValidationLlmRoutingTest(unittest.TestCase):
    def test_board_capability_gap_routes_to_board_integration_repair(self) -> None:
        actions = build_repair_actions(
            [{"checker": "real_tool.case_multilayer_pipeline", "status": "fail"}],
            None,
            {},
            {"status": "verification_capability_gap"},
            {
                "failure_kind": "verification_capability_gap",
                "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                "failed_current_layer_gates": [{"name": "case_multilayer_pipeline", "status": "fail"}],
            },
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["debug_layer"], "board_axi_ddr_wrapped_system")

    def test_repairable_vcs_failure_routes_to_the_same_board_agent(self) -> None:
        actions = build_repair_actions(
            [{"checker": "real_tool.case_vcs_functional_sim", "status": "fail"}],
            {
                "status": "needs_repair",
                "failure_class": "vcs_runtime_failure",
                "repair_handoff": {"agent_should_apply_code_changes": True, "repair_scope": "board_rtl_or_testbench"},
            },
            {},
            {"status": "localized"},
            {
                "failure_kind": "board_wrapper_or_pipeline_integration",
                "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                "failed_current_layer_gates": [{"name": "case_vcs_functional_sim", "status": "fail"}],
            },
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "exact_board_integration_harness")

    def test_failed_current_scope_uses_stage6_route_only_in_conditional_review_mode(self) -> None:
        result = {
            "status": "fail",
            "hierarchical_repair_loop": {
                "status": "needs_repair",
                "failure_kind": "hardware_value_mismatch",
                "current_layer": {"status": "needs_repair"},
                "root_candidate_module": "attention_core",
                "violated_contract": "ready_valid_dataflow",
                "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
            },
        }
        with patch.dict(os.environ, {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertTrue(exact_failed_stage6_route(result))
        with patch.dict(os.environ, {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "full"}):
            self.assertFalse(exact_failed_stage6_route(result))

    def test_capability_gap_does_not_start_a_redundant_repair_specialist(self) -> None:
        repair = {
            "diagnostics": {"hierarchical_repair_loop": {"failure_kind": "verification_capability_gap"}},
            "repair_actions": [{"scope": "verification_capability_repair", "approval_required": False}],
        }
        self.assertIsNone(repair_specialist_trigger(repair))


if __name__ == "__main__":
    unittest.main()
