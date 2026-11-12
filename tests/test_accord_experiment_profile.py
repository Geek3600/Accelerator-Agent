from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from accagent.framework.experiment_profile import (
    active_profile,
    without_design_graph_context,
    without_guided_repair_context,
    without_guided_repair_prompt_rules,
)
from accagent.framework.stage_llm import build_stage_agent_prompt_inputs


class AccordExperimentProfileTests(unittest.TestCase):
    def test_default_profile_keeps_full_accord(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(active_profile(), "ACCORD")

    def test_b2_removes_guided_repair_projection_only(self) -> None:
        with patch.dict(os.environ, {"SPATIALACC_ACCORD_PROFILE": "B2"}, clear=True):
            self.assertEqual(active_profile(), "B2")
        original = {
            "run_dir": "/experiments/cctg_b2_replay/run",
            "tool_report": {"status": "fail", "summary": "timing failure"},
            "sacg_state": {"constraints": ["clock"]},
            "sacg_cctg_causal_slice": {"earliest_unproven_frontier": "stage_x"},
            "repair_workflow": {
                "cctg_policy": {"localized_action": "causal_slice_repair"},
                "repair_loop": "tool_run__cctg_localize__bounded_repair__rerun",
                "failure_loop": ["collect CCTG boundary trace", "rerun current layer"],
                "experiment_profile": {"disabled_mechanisms": ["CCTG-guided repair"]},
                "prior_repair_execution_feedback": {
                    "summary": "Move state declarations before first references."
                },
                "policy": {"same_debug_layer_must_rerun": True},
            },
            "sacg_memory": {
                "failure_lessons": [
                    {
                        "recommended_action": "Use contract-guided debug closure first.",
                        "failure_class": "compile error",
                    },
                    {
                        "recommended_action": "Read the current compiler diagnostic.",
                        "failure_class": "compile error",
                    },
                ]
            },
            "repair": {"minimal_repair_context": {"root_candidate_module": "Norm"}},
            "action_grounding_registry": {
                "tool_roles": ["case_vcs_functional", "failure_slice_localization"],
                "acceptance_checkers": [
                    "case_vcs_functional",
                    "connected_kernel_cctg_contradiction_reconciliation_check",
                    "failure_localization_check",
                ],
            },
        }
        projected = without_guided_repair_context(original)
        self.assertEqual(projected["run_dir"], original["run_dir"])
        self.assertEqual(projected["tool_report"], original["tool_report"])
        self.assertEqual(projected["sacg_state"], original["sacg_state"])
        self.assertNotIn("sacg_cctg_causal_slice", projected)
        self.assertEqual(
            projected["repair_workflow"],
            {"policy": {"same_debug_layer_must_rerun": True}},
        )
        self.assertEqual(
            projected["sacg_memory"]["failure_lessons"],
            [
                {
                    "recommended_action": "Read the current compiler diagnostic.",
                    "failure_class": "compile error",
                }
            ],
        )
        self.assertEqual(projected["repair"], {})
        self.assertEqual(
            projected["action_grounding_registry"],
            {
                "tool_roles": ["case_vcs_functional"],
                "acceptance_checkers": ["case_vcs_functional"],
            },
        )
        self.assertIn("sacg_cctg_causal_slice", original)

    def test_b0_removes_graph_context_but_keeps_task_and_tool_evidence(self) -> None:
        original = {
            "task_card": {"goal": "update downstream design"},
            "model_config": {"hidden_size": 768},
            "source_sacg_state": "/run/sacg_state.json",
            "sacg_memory": {"constraints": ["width"]},
            "hierarchical_learning_context": {"validated": True},
            "tool_report": {"status": "fail", "summary": "compile failed"},
        }
        projected = without_design_graph_context(original)
        self.assertEqual(projected["task_card"], original["task_card"])
        self.assertEqual(projected["model_config"], original["model_config"])
        self.assertEqual(projected["tool_report"], original["tool_report"])
        self.assertNotIn("source_sacg_state", projected)
        self.assertNotIn("sacg_memory", projected)
        self.assertNotIn("hierarchical_learning_context", projected)

    def test_b1_is_rejected_until_static_graph_profile_is_implemented(self) -> None:
        with patch.dict(os.environ, {"SPATIALACC_ACCORD_PROFILE": "B1"}, clear=True):
            with self.assertRaises(ValueError):
                active_profile()

    def test_prompt_projection_matches_default_and_b2_profiles(self) -> None:
        inputs = {
            "candidate_repair_plan": {
                "diagnostics": {
                    "contract_guided_debug_closure": {"root_candidate_module": "Norm"},
                    "tool_report": {"status": "fail"},
                },
                "repair_workflow": {
                    "cctg_policy": {"localized_action": "causal_slice_repair"},
                    "repair_loop": "tool_run__cctg_localize__bounded_repair__rerun",
                    "failure_loop": ["collect CCTG boundary trace", "rerun current layer"],
                    "experiment_profile": {"disabled_mechanisms": ["CCTG-guided repair"]},
                    "prior_repair_execution_feedback": {
                        "summary": "Move state declarations before first references."
                    },
                    "policy": {"same_debug_layer_must_rerun": True},
                },
                "sacg_memory": {
                    "failure_lessons": [
                        {"recommended_action": "Use contract-guided debug closure first."},
                        {"recommended_action": "Read the current compiler diagnostic."},
                    ]
                },
            }
        }
        with patch.dict(os.environ, {}, clear=True):
            default_prompt, _, _ = build_stage_agent_prompt_inputs(inputs)
        with patch.dict(os.environ, {"SPATIALACC_ACCORD_PROFILE": "B2"}, clear=True):
            b2_prompt, _, _ = build_stage_agent_prompt_inputs(inputs)
        with patch.dict(os.environ, {"SPATIALACC_ACCORD_PROFILE": "B0"}, clear=True):
            b0_prompt, _, _ = build_stage_agent_prompt_inputs(
                {
                    **inputs,
                    "source_sacg_state": "/run/sacg_state.json",
                    "sacg_memory": {"constraints": ["width"]},
                    "tool_report": {"status": "fail"},
                }
            )

        self.assertIn("contract_guided_debug_closure", default_prompt["candidate_repair_plan"]["diagnostics"])
        self.assertNotIn("contract_guided_debug_closure", b2_prompt["candidate_repair_plan"]["diagnostics"])
        self.assertEqual(
            b2_prompt["candidate_repair_plan"]["repair_workflow"],
            {"policy": {"same_debug_layer_must_rerun": True}},
        )
        self.assertNotIn("contract-guided", str(b2_prompt).lower())
        self.assertEqual(
            without_guided_repair_prompt_rules(
                [
                    "Keep the current layer as the acceptance scope.",
                    "Use the earliest causal boundary before repairing.",
                    "Repair the complete causally affected interface family.",
                ]
            ),
            ["Keep the current layer as the acceptance scope."],
        )
        self.assertEqual(
            b2_prompt["candidate_repair_plan"]["diagnostics"]["tool_report"],
            {"status": "fail"},
        )
        self.assertNotIn(
            "failure_slice_localization",
            b2_prompt["action_grounding_registry"]["tool_roles"],
        )
        self.assertNotIn("sacg_memory", b0_prompt)
        self.assertNotIn("source_sacg_state", b0_prompt)
        self.assertEqual(b0_prompt["tool_report"], {"status": "fail"})


if __name__ == "__main__":
    unittest.main()
