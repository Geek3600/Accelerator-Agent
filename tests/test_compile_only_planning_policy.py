from pathlib import Path
from unittest import TestCase

from accagent.framework.stage_llm import ACTION_GROUNDING_REGISTRY
from accagent.framework.stage_verification_plan import compact_plan_for_planner


class CompileOnlyPlanningPolicyTests(TestCase):
    def test_planner_keeps_existing_execution_modes(self):
        policy = ACTION_GROUNDING_REGISTRY["verification_execution_policy"]
        compact = compact_plan_for_planner({"verification_execution_policy": policy})
        self.assertEqual(compact["verification_execution_policy"], policy)
        self.assertEqual(policy["validation_policy"], "vcs_compile_only")
        self.assertEqual(set(policy["existing_tool_modes"]), {
            "case_leaf_functional", "case_single_layer_functional", "case_vcs_functional_sim",
        })

    def test_documented_tools_have_compile_only_implementation(self):
        root = Path(__file__).resolve().parents[1]
        policy = ACTION_GROUNDING_REGISTRY["verification_execution_policy"]
        for role, description in policy["existing_tool_modes"].items():
            with self.subTest(role=role):
                source = (root / description.split(":", 1)[0]).read_text()
                self.assertIn("COMPILE_ONLY_POLICY", source)
