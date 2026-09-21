import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.stage_params import (
    build_dse_search,
    build_parameter_bindings,
    select_dse_candidate,
)
from accagent.framework.stage_pipeline import build_pipeline_plan
from tests.test_stage_pipeline import state_for


def prepare_state(family: str, root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    state = state_for(family, root)
    plan = build_pipeline_plan(state)
    plan_path = root / "pipeline_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    state["artifacts"].append({"id": "artifact.stage3.pipeline_plan", "path": str(plan_path)})
    return state


class SemanticParameterBindingTest(TestCase):
    def test_dse_requires_an_explicit_llm_candidate_selection(self) -> None:
        dse = {
            "records": [
                {"candidate_id": "candidate_a", "parameters": {}},
                {"candidate_id": "candidate_b", "parameters": {}},
            ],
            "measurement_summary": {"complete": False},
            "unmeasured_candidate_ids": ["candidate_a", "candidate_b"],
            "pareto_candidate_ids": [],
        }

        with self.assertRaisesRegex(ValueError, "requires the LLM"):
            select_dse_candidate(dse, {"ranked_candidate_ids": ["candidate_a"]})

    def test_dse_preserves_explicit_llm_measurement_order(self) -> None:
        dse = {
            "records": [
                {"candidate_id": "candidate_a", "parameters": {}},
                {"candidate_id": "candidate_b", "parameters": {}},
            ],
            "measurement_summary": {"complete": False},
            "unmeasured_candidate_ids": ["candidate_a", "candidate_b"],
            "pareto_candidate_ids": [],
        }

        selected, rationale = select_dse_candidate(
            dse,
            {
                "selected_candidate_id": "candidate_b",
                "ranked_candidate_ids": ["candidate_b", "candidate_a"],
                "selection_rationale": "measure the wider-buffer point first",
            },
        )

        self.assertEqual(selected["candidate_id"], "candidate_b")
        self.assertEqual(rationale["selection_source"], "llm_measurement_order")
        self.assertNotIn("deterministic_reason", rationale)

    def test_gpt2_uses_dense_mlp_dimensions_and_its_own_weight_terms(self) -> None:
        with TemporaryDirectory() as temp:
            state = prepare_state("gpt2", Path(temp))
            bindings = build_parameter_bindings(state)

        self.assertEqual(bindings["status"], "ready")
        layouts = bindings["physical_weight_layout"]["roles"]
        roles = {row["role"] for row in layouts}
        self.assertIn("weight_mlp_up", roles)
        self.assertIn("weight_mlp_down", roles)
        self.assertNotIn("weight_mlp_gate", roles)
        by_op = {row["op"]: row for row in bindings["bindings"]}
        self.assertEqual(by_op["mlp_fc"]["structural_dimensions"]["input_elements"], 16 * 64)
        self.assertEqual(by_op["mlp_fc"]["structural_dimensions"]["output_elements"], 16 * 256)
        self.assertEqual(by_op["mlp_fc"]["structural_dimensions"]["weight_term_ids"], ["mlp_c_fc_weight", "mlp_c_fc_bias"])

    def test_qwen2_and_llama_keep_their_distinct_semantic_weight_layouts(self) -> None:
        with TemporaryDirectory() as temp:
            qwen = build_parameter_bindings(prepare_state("qwen2", Path(temp) / "qwen"))
            llama = build_parameter_bindings(prepare_state("llama", Path(temp) / "llama"))

        qwen_roles = {row["role"] for row in qwen["physical_weight_layout"]["roles"]}
        llama_roles = {row["role"] for row in llama["physical_weight_layout"]["roles"]}
        self.assertIn("weight_qkv_bias", qwen_roles)
        self.assertNotIn("weight_qkv_bias", llama_roles)
        self.assertIn("weight_mlp_gate", qwen_roles)
        self.assertIn("weight_mlp_gate", llama_roles)
        self.assertEqual(qwen["status"], "ready")
        self.assertEqual(llama["status"], "ready")

    def test_dse_derives_a_complete_model_specific_layout_when_stage0_omits_one(self) -> None:
        with TemporaryDirectory() as temp:
            state = prepare_state("gpt2", Path(temp))
            dse = build_dse_search(state, Path(temp))

        self.assertEqual(dse["candidate_count"], 1)
        parameters = dse["records"][0]["parameters"]
        self.assertIn("weight_mlp_up", parameters["weight_banks_by_role"])
        self.assertIn("weight_qkv", parameters["weight_banks_by_role"])

    def test_wrong_model_weight_role_layout_is_rejected_instead_of_silently_reused(self) -> None:
        with TemporaryDirectory() as temp:
            state = prepare_state("gpt2", Path(temp))
            design_space = next(item for item in state["constraints"] if item["id"] == "constraint.arch.design_space")
            design_space["facts"]["search_params"]["physical_weight_layout_candidates"] = [
                {
                    "weight_banks_by_role": {"weight_qkv": 1},
                }
            ]
            with self.assertRaises(ValueError):
                build_dse_search(state, Path(temp))
