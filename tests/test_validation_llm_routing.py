"""Current LLM routing contracts for the Stage-6 repair loop."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.stage_repair import (
    build_repair_actions,
    deterministic_localized_repair_record,
    exact_localized_repair_route,
    repair_specialist_trigger,
)
from accagent.framework.stage_verification import exact_failed_stage6_route


class ValidationLlmRoutingTest(unittest.TestCase):
    def test_vcs_tool_crash_uses_deterministic_same_fingerprint_retry(self) -> None:
        repair = {
            "diagnostics": {
                "case_vcs_functional": {"status": "historical_only"}
            },
            "repair_actions": [
                {
                    "repair_kind": "exact_board_environment_retry",
                    "scope": "regression_rerun",
                    "tool": "case_vcs_functional_sim",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "approval_required": False,
                    "failure_signature": {
                        "failure_class": "vcs_tool_process_failure",
                        "repair_scope": "execution_environment_retry",
                    },
                }
            ],
        }

        with patch.dict(os.environ, {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "full"}):
            self.assertTrue(exact_localized_repair_route(repair))
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.stage_repair.authoritative_repair_routing_priority",
            return_value={"status": "none"},
        ):
            record = deterministic_localized_repair_record(repair, Path(temp_dir))

        self.assertTrue(record["llm_skipped"])
        self.assertEqual(record["mode"], "deterministic_environment_retry")
        self.assertEqual(record["output"]["executable_actions"], [])

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

    def test_missing_board_identity_routes_to_discovery_before_integration(self) -> None:
        actions = build_repair_actions(
            [
                {
                    "checker": "real_tool.case_vcs_functional_sim",
                    "status": "fail",
                    "summary": (
                        "returncode=1 report_status=fail blockers=exact board preflight: "
                        "board source identity is missing"
                    ),
                }
            ],
            None,
            {},
            {"status": "verification_capability_gap"},
            {
                "failure_kind": "verification_capability_gap",
                "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                "failed_current_layer_gates": [
                    {"name": "functional_sim", "status": "fail"}
                ],
            },
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "exact_board_interface_discovery")

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

    def test_compile_only_board_diagnostic_skips_unavailable_boundary_trace(self) -> None:
        with patch.dict(os.environ, {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}):
            actions = build_repair_actions(
                [
                    {
                        "checker": "real_tool.case_vcs_functional_sim",
                        "status": "fail",
                        "summary": (
                            "exact-board VCS compile/elaboration failed: "
                            "Error-[URMI] Unresolved modules"
                        ),
                    }
                ],
                None,
                {},
                {"status": "needs_boundary_trace"},
                {
                    "failure_kind": "board_wrapper_or_pipeline_integration",
                    "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                    "failed_current_layer_gates": [
                        {"name": "functional_sim", "status": "fail"}
                    ],
                },
            )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], "exact_board_integration_harness")
        self.assertTrue(actions[0]["minimal_repair_context"]["compile_only_direct_repair"])

    def test_codegen_source_closure_precedes_semantic_binding_route(self) -> None:
        actions = build_repair_actions(
            [
                {
                    "checker": "codegen_package_static_check",
                    "status": "fail",
                    "summary": "no planned code outputs",
                },
                {
                    "checker": "case_stage_leaf_static",
                    "status": "fail",
                    "summary": (
                        "required RTL file missing: "
                        "/run/generated/chisel/GeneratedAxiDdrTop.sv"
                    ),
                },
            ],
            None,
            {},
            {"status": "verification_capability_gap"},
            {
                "failure_kind": "verification_capability_gap",
                "current_layer": {"id": "operator_leaf_modules"},
                "failed_current_layer_gates": [
                    {"name": "case_stage_leaf_static", "status": "fail"}
                ],
            },
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "code_generation_package_recovery")

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

    def test_localized_route_tolerates_missing_optional_vcs_diagnosis(self) -> None:
        repair = {
            "diagnostics": {"case_vcs_functional": None},
            "repair_actions": [
                {
                    "repair_kind": "exact_board_integration_harness",
                    "scope": "verification_capability_repair",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "approval_required": False,
                }
            ],
        }
        with patch.dict(os.environ, {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertFalse(exact_localized_repair_route(repair))

        repair["diagnostics"]["case_vcs_functional"] = {"failure_evidence": None}
        with patch.dict(os.environ, {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertFalse(exact_localized_repair_route(repair))


if __name__ == "__main__":
    unittest.main()
