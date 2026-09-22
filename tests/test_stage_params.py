import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.dse_candidates import physical_candidate_tuples
from accagent.framework.stage_params import (
    architecture_candidate_space,
    build_dse_search,
    build_parameter_bindings,
    dse_llm_constraint_report,
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
    def test_dse_llm_constraint_report_omits_repeated_infeasible_rows(self) -> None:
        report = {
            "schema_version": "full",
            "status": "pass",
            "candidate_count": 12,
            "feasible_candidate_count": 4,
            "infeasible_candidates": [
                {
                    "candidate_id": "bad_a",
                    "hard_constraint_errors": ["width mismatch", "width mismatch"],
                },
                {
                    "candidate_id": "bad_b",
                    "hard_constraint_errors": ["width mismatch"],
                },
            ],
            "policy": {"candidate_universe_is_complete_and_unsampled": True},
            "candidate_materialization": {
                "status": "pass",
                "candidate_count": 12,
                "candidate_signatures": {"bad_a": {"lanes": 32}},
                "generated_fields": {"lanes": "GeneratedDesignParams.lanes"},
            },
        }

        projected = dse_llm_constraint_report(report)

        self.assertEqual(projected["infeasible_candidate_count"], 2)
        self.assertEqual(projected["hard_constraint_error_counts"], {"width mismatch": 3})
        self.assertNotIn("infeasible_candidates", projected)
        self.assertNotIn("candidate_signatures", projected["candidate_materialization"])
        self.assertEqual(projected["candidate_materialization"]["status"], "pass")

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

    def test_explicit_physical_tuples_preserve_declared_correlations(self) -> None:
        search = {
            "hardware_parameter_tuples": [
                {
                    "lanes": 8,
                    "compute_array": {"rows": 2, "cols": 4},
                    "physical_fifo_depth_entries": 16,
                    "activation_bank_count": 2,
                },
                {
                    "lanes": 16,
                    "compute_array": {"rows": 4, "cols": 8},
                    "physical_fifo_depth_entries": 48,
                    "activation_bank_count": 4,
                },
            ]
        }

        self.assertEqual(
            physical_candidate_tuples(search),
            [
                {
                    "lanes": 8,
                    "compute_array_rows": 2,
                    "compute_array_cols": 4,
                    "fifo_depth": 16,
                    "activation_banks": 2,
                },
                {
                    "lanes": 16,
                    "compute_array_rows": 4,
                    "compute_array_cols": 8,
                    "fifo_depth": 48,
                    "activation_banks": 4,
                },
            ],
        )

    def test_explicit_candidate_universe_list_preserves_declared_correlations(self) -> None:
        search = {
            "candidate_universe": [
                {
                    "lanes": 16,
                    "compute_array": {"rows": 4, "cols": 4},
                    "physical_fifo_depth": 16,
                    "activation_bank_count": 2,
                },
                {
                    "lanes": 32,
                    "compute_array": {"rows": 4, "cols": 8},
                    "physical_fifo_depth": 32,
                    "activation_bank_count": 4,
                },
            ]
        }

        tuples = physical_candidate_tuples(search)
        self.assertEqual(len(tuples), 2)
        self.assertEqual(
            {(row["lanes"], row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(16, 4, 4), (32, 4, 8)},
        )

    def test_candidate_universe_expands_only_declared_legal_array_tuples(self) -> None:
        search = {
            "candidate_universe": {
                "compute_array": {
                    "legal_compute_array_tuples": [
                        {"lanes": 8, "rows": 2, "cols": 4},
                        {"lanes": 16, "rows": 4, "cols": 8},
                    ]
                },
                "physical_fifo_depth": {"candidate_values": [16, 32]},
                "activation_bank_count": {"candidate_values": [2, 4]},
            }
        }

        tuples = physical_candidate_tuples(search)
        self.assertEqual(len(tuples), 8)
        self.assertEqual(
            {(row["lanes"], row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(8, 2, 4), (16, 4, 8)},
        )
        space = architecture_candidate_space(search, {"weight_qkv"})
        self.assertEqual(space["physical_candidate_tuples"], tuples)

    def test_candidate_universe_supports_explicit_legal_pairs(self) -> None:
        search = {
            "candidate_universe": {
                "lanes": {"candidates": [32]},
                "compute_array": {"legal_pairs": [[8, 8], [16, 32]]},
                "physical_fifo_depth": {"entries_candidates": [16, 32]},
                "activation_bank_count": {"candidates": [1, 2]},
            }
        }

        tuples = physical_candidate_tuples(search)
        self.assertEqual(len(tuples), 8)
        self.assertEqual(
            {(row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(8, 8), (16, 32)},
        )

    def test_candidate_universe_supports_stage0_physical_shape_schema(self) -> None:
        search = {
            "candidate_universe": {
                "lanes": [32],
                "compute_array": {
                    "valid_physical_shapes": [
                        {"rows": 8, "cols": 8, "pe_count": 64},
                        {"rows": 8, "cols": 16, "pe_count": 128},
                        {"rows": 16, "cols": 8, "pe_count": 128},
                        {"rows": 16, "cols": 16, "pe_count": 256},
                    ]
                },
                "physical_fifo_depth_entries": [16, 32],
                "activation_bank_count": [1, 2, 4],
            }
        }

        tuples = physical_candidate_tuples(search)

        self.assertEqual(len(tuples), 24)
        self.assertEqual(
            {(row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(8, 8), (8, 16), (16, 8), (16, 16)},
        )
        self.assertEqual({row["fifo_depth"] for row in tuples}, {16, 32})
        self.assertEqual({row["activation_banks"] for row in tuples}, {1, 2, 4})

    def test_candidate_dimensions_expand_only_declared_physical_axes(self) -> None:
        search = {
            "candidate_dimensions": {
                "lanes": {"values": [32]},
                "compute_array": {
                    "values": [
                        {"rows": 4, "cols": 8},
                        {"rows": 8, "cols": 16},
                    ]
                },
                "physical_fifo_depth": {"values": [32, 64]},
                "activation_bank_count": {"values": [2, 4]},
            }
        }

        tuples = physical_candidate_tuples(search)

        self.assertEqual(len(tuples), 8)
        self.assertEqual(
            {(row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(4, 8), (8, 16)},
        )

    def test_summary_universe_uses_top_level_declared_physical_axes(self) -> None:
        search = {
            "candidate_universe": {
                "candidate_count": 81,
                "complete": True,
                "finite": True,
                "no_unlisted_candidates_permitted": True,
            },
            "lanes": {"candidate_values": [32]},
            "compute_array": {
                "rows": {"candidate_values": [8, 16, 32]},
                "cols": {"candidate_values": [8, 16, 32]},
                "valid_candidate_pairs": [
                    {"rows": rows, "cols": cols}
                    for rows in (8, 16, 32)
                    for cols in (8, 16, 32)
                ],
            },
            "physical_fifo_depth": {"candidate_values": [16, 32, 64]},
            "activation_bank_count": {"candidate_values": [1, 2, 4]},
        }

        tuples = physical_candidate_tuples(search)

        self.assertEqual(len(tuples), 81)
        self.assertEqual(
            {(row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(rows, cols) for rows in (8, 16, 32) for cols in (8, 16, 32)},
        )
        self.assertTrue(all(row["lanes"] == 32 for row in tuples))

    def test_legacy_axes_accept_physical_fifo_depth_name(self) -> None:
        tuples = physical_candidate_tuples(
            {
                "lanes": [4],
                "compute_array": {"rows": [2], "cols": [2]},
                "physical_fifo_depth": [16],
                "activation_bank_count": [2],
            }
        )
        self.assertEqual(tuples[0]["fifo_depth"], 16)

    def test_global_params_come_from_current_bound_physical_tuple(self) -> None:
        with TemporaryDirectory() as temp:
            state = prepare_state("gpt2", Path(temp))
            design_space = next(
                item for item in state["constraints"] if item["id"] == "constraint.arch.design_space"
            )
            design_space["facts"]["search_params"]["hardware_parameter_tuples"] = [
                {
                    "lanes": 8,
                    "compute_array": {"rows": 4, "cols": 4},
                    "physical_fifo_depth_entries": 48,
                    "activation_bank_count": 3,
                }
            ]
            bindings = build_parameter_bindings(state)

        self.assertEqual(bindings["global_params"]["fifo_depth"], 48)
        self.assertEqual(bindings["global_params"]["activation_banks"], 3)

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
