import json
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, mock

from accagent.framework.dse_candidates import physical_candidate_tuples
from accagent.framework.sacg_store import SACGStore, write_json
from accagent.framework.stage_params import (
    architecture_candidate_space,
    bind_parameters,
    build_dse_search,
    build_parameter_bindings,
    dse_llm_constraint_report,
    dse_llm_candidate_record,
    dse_llm_selection_evidence,
    normalize_legacy_dse_handoff,
    select_dse_candidate,
    stage4_llm_errors,
    stage4_measurement_request_ready,
    run_parameter_static_checks,
    update_sacg,
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
    state["nodes"] = [
        {"id": node_id}
        for node_id in (
            "node.design_space", "node.pipeline.block_input", "node.pipeline.block_output",
            *(f"node.pipeline.{stage['stage_id']}" for stage in plan["stages"]),
        )
    ]
    state["edges"] = [
        {"id": edge["edge_id"], "src": f"node.pipeline.{edge['src_stage']}", "dst": f"node.pipeline.{edge['dst_stage']}"}
        for edge in plan["stream_edges"]
    ]
    return state


class SemanticParameterBindingTest(TestCase):
    def test_explicit_array_trial_updates_old_geometry_without_widening_other_axes(self) -> None:
        search = {
            "candidate_universe": {
                "compute_array": {"legal_compute_array_tuples": [
                    {"lanes": 16, "rows": 8, "cols": 16}]},
                "physical_fifo_depth": {"candidate_values": [32]},
                "activation_bank_count": {"candidate_values": [2]},
            },
            "board_axi_data_width_bits": 512,
            "campaign_array_policy": {"preferred_rows": 16, "preferred_cols": 32,
                                      "parallel_multiply_positions": 512,
                                      "defer_array_positions_at_or_above": 1024},
        }
        space = architecture_candidate_space(search, {"projection_weight"})
        points = space["physical_candidate_tuples"]
        self.assertTrue(any((p["compute_array_rows"], p["compute_array_cols"]) == (16, 32) for p in points))
        self.assertEqual({(p["lanes"], p["fifo_depth"], p["activation_banks"]) for p in points}, {(16, 32, 2)})
        self.assertEqual(space["cache_refill_data_width_bits"], [512])
        self.assertEqual(space["attention_output_cross_token_reuse_tokens"], [1])
        self.assertTrue(all(p["compute_array_rows"] * p["compute_array_cols"] < 1024 for p in points))
        search["campaign_array_policy"].update(preferred_rows=32, parallel_multiply_positions=1024)
        with self.assertRaises(ValueError):
            architecture_candidate_space(search, {"projection_weight"})

    def test_explicit_run_array_policy_overrides_campaign_default(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            state = prepare_state("gpt2", root / "inputs")
            design_space = next(
                row["facts"]
                for row in state["constraints"]
                if row["id"] == "constraint.arch.design_space"
            )
            design_space["search_params"]["campaign_array_policy"] = {
                "parallel_multiply_positions": 64,
                "preferred_rows": 8,
                "preferred_cols": 8,
                "defer_array_positions_at_or_above": 1024,
            }

            dse = build_dse_search(state, root)

        self.assertEqual(dse["search_space"]["array_trial_binding"]["preferred_rows"], 8)
        self.assertEqual(dse["search_space"]["array_trial_binding"]["preferred_cols"], 8)
        self.assertEqual(dse["search_space"]["attention_output_cross_token_reuse_tokens"], [1])
        self.assertTrue(all(
            record["parameters"]["attention_output_cross_token_reuse_tokens"] == 1
            for record in dse["records"]
        ))
        self.assertEqual(
            {
                (item["compute_array_rows"], item["compute_array_cols"])
                for item in dse["search_space"]["physical_candidate_tuples"]
                if item["compute_array_rows"] == 8 and item["compute_array_cols"] == 8
            },
            {(8, 8)},
        )

    def test_backtrack_attaches_current_numeric_check_evidence(self) -> None:
        for numeric_valid in (True, False):
            with self.subTest(numeric_valid=numeric_valid), TemporaryDirectory() as temp:
                root = Path(temp)
                state = prepare_state("gpt2", root / "inputs")
                state["invariants"] = [{
                    "id": "invariant.numeric_policy_check",
                    "checker": "numeric_policy_check",
                    "constraints": ["constraint.numeric.policy", "constraint.parameter.binding"],
                    "status": "pass",
                }]
                source_path = root / "code_generation" / "sacg_state.json"
                target_path = root / "parameter_binding" / "sacg_state.json"
                write_json(source_path, state)
                bindings = build_parameter_bindings(state)
                if not numeric_valid:
                    bindings["bindings"][0]["params"]["input_bits"] = 8
                checks = run_parameter_static_checks(state, bindings)
                dse_paths = {
                    key: target_path.parent / f"{key}.json"
                    for key in (
                        "search_space", "candidate_records", "constraint_report",
                        "pareto_frontier", "measurements", "selected_architecture",
                        "selection_rationale",
                    )
                }

                transition_id = update_sacg(
                    source_path, target_path,
                    target_path.parent / "parameter_binding.json",
                    target_path.parent / "parameter_static_checks.json",
                    dse_paths, bindings, {}, {}, checks, checks["summary"]["errors"],
                )
                store = SACGStore(target_path)
                transition = next(
                    row for row in store.state["transitions"] if row["id"] == transition_id
                )
                numeric_evidence = next(
                    row for row in store.state["evidence"]
                    if row["id"] in transition["evidence"] and row["checker"] == "numeric_policy_check"
                )

                self.assertIn("numeric_policy_check", transition["required_checkers"])
                self.assertEqual(transition["status"], "promoted" if numeric_valid else "rejected")
                self.assertEqual(numeric_evidence["status"], "pass" if numeric_valid else "fail")
                self.assertEqual(numeric_evidence["log_path"], str(target_path.parent / "parameter_static_checks.json"))

    def test_measurement_handoff_does_not_wait_for_auxiliary_team_audit(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            state = prepare_state("gpt2", root / "inputs")
            state_path = root / "stage3" / "sacg_state.json"
            write_json(state_path, state)
            dse = build_dse_search(state, root)
            candidate_id = dse["unmeasured_candidate_ids"][0]
            result_path = root / "dse_agent_result.json"
            write_json(result_path, {})
            llm_result = {
                "output": {
                    "status": "next_exact_measurement_selected",
                    "selected_candidate_id": candidate_id,
                    "ranked_candidate_ids": [candidate_id],
                    "selection_rationale": "Select the legal candidate for exact measurement.",
                    "assumptions": [],
                },
                "result_path": str(result_path),
            }
            with mock.patch(
                "accagent.framework.stage_params.run_dir_from_state", return_value=root
            ), mock.patch(
                "accagent.framework.stage_params.run_stage_agent", return_value=llm_result
            ), mock.patch(
                "accagent.framework.stage_team.run_design_team",
                side_effect=AssertionError("auxiliary team audit must not block measurement"),
            ):
                _, report = bind_parameters(Namespace(sacg_state=state_path))

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["selected_architecture"]["candidate_id"], candidate_id)
        self.assertEqual(report["checker_summary"]["errors"], [])
        self.assertEqual(report["design_team"]["status"], "not_required_for_measurement_handoff")

    def test_legacy_measurement_handoff_normalizes_only_for_exact_incomplete_selection(self) -> None:
        legacy = {
            "status": "measurement_pending",
            "selected_candidate_id": "candidate_b",
        }
        selected = {"candidate_id": "candidate_b", "parameters": {"lanes": 16}}

        normalized = normalize_legacy_dse_handoff(legacy, selected, campaign_complete=False)

        self.assertEqual(legacy["status"], "measurement_pending")
        self.assertEqual(normalized["status"], "next_exact_measurement_selected")
        self.assertEqual(
            normalize_legacy_dse_handoff(legacy, {**selected, "candidate_id": "candidate_a"}, campaign_complete=False),
            legacy,
        )
        self.assertEqual(normalize_legacy_dse_handoff(legacy, selected, campaign_complete=True), legacy)

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

    def test_dse_selection_table_is_lossless_and_compact_for_full_candidate_universe(self) -> None:
        role_banks = {
            "weight": 1,
            "weight_attn_out": 1,
            "weight_attn_out_bias": 1,
            "weight_mlp_down": 1,
            "weight_mlp_down_bias": 1,
            "weight_mlp_up": 1,
            "weight_mlp_up_bias": 1,
            "weight_qkv": 1,
            "weight_qkv_bias": 1,
        }
        records = []
        for index in range(360):
            records.append({
                "candidate_id": f"arch_{index:04d}",
                "parameters": {
                    "lanes": (8, 16)[index % 2],
                    "compute_array_rows": (4, 8, 16)[index % 3],
                    "compute_array_cols": (4, 16, 32, 64)[index % 4],
                    "fifo_depth": (64, 128, 256)[index % 3],
                    "activation_banks": (2, 4)[index % 2],
                    "weight_banks": 1,
                    "weight_banks_by_role": role_banks,
                    "cache_tile_words": 256,
                    "cache_tile_count": 2,
                    "cache_refill_data_width_bits": 512,
                    "cross_token_reuse_tokens": (4, 8, 16)[index % 3],
                },
                "feasible": True,
                "hard_constraint_errors": [],
                "measurement": None,
                "resource_lower_bounds": {"uram": 16 + 8 * (index % 4)},
                "resource_headroom": {
                    "maximum_utilization_fraction": 0.85,
                    "measured_utilization": {},
                    "missing_resource_measurements": ["bram18", "bram36", "dsp", "ff", "lut", "uram"],
                    "status": "unknown",
                },
                "qor_estimate": {
                    "model": "structural_proxy_v1",
                    "reason": "no source-bound calibration sample",
                    "status": "insufficient_evidence",
                },
            })
        ranked_ids = [record["candidate_id"] for record in reversed(records)]
        evidence = dse_llm_selection_evidence(
            {
                "candidate_count": len(records),
                "estimated_ranked_candidate_ids": ranked_ids,
                "search_space": {
                    "lanes": [8, 16],
                    "compute_array_rows": [4, 8, 16],
                    "compute_array_cols": [4, 16, 32, 64],
                    "fifo_depth": [64, 128, 256],
                },
            },
            records,
            [],
        )
        table = evidence["eligible_candidate_table"]
        self.assertNotIn("eligible_candidates", evidence)
        self.assertEqual(table["candidate_ids"], ranked_ids)

        def expand(column: dict, row_index: int) -> object:
            if "shared" in column:
                return column["shared"]
            return column["value_dictionary"][column["row_indices"][row_index]]

        for row_index, candidate_id in enumerate(table["candidate_ids"]):
            actual = {"candidate_id": candidate_id, "parameters": {}}
            actual["parameters"] = {
                key: expand(column, row_index)
                for key, column in table["parameter_columns"].items()
            }
            actual.update({
                key: expand(column, row_index)
                for key, column in table["candidate_fact_columns"].items()
            })
            expected = dse_llm_candidate_record(records[int(candidate_id[5:])])
            self.assertEqual(actual, expected)

        self.assertLess(len(json.dumps(evidence, separators=(",", ":"))), 50000)

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

    def test_unmeasured_dse_selection_can_only_handoff_the_exact_llm_candidate(self) -> None:
        output = {
            "status": "next_exact_measurement_selected",
            "selected_candidate_id": "candidate_b",
        }
        selected = {"candidate_id": "candidate_b", "parameters": {"lanes": 16}}

        self.assertTrue(stage4_measurement_request_ready(output, selected, campaign_complete=False))
        self.assertFalse(
            stage4_measurement_request_ready(
                {**output, "selected_candidate_id": "candidate_a"},
                selected,
                campaign_complete=False,
            )
        )
        self.assertFalse(stage4_measurement_request_ready(output, selected, campaign_complete=True))
        self.assertFalse(
            stage4_measurement_request_ready(
                {**output, "status": "measurement_pending"},
                selected,
                campaign_complete=False,
            )
        )

    def test_unmeasured_dse_selection_does_not_become_a_stage_failure(self) -> None:
        output = {
            "status": "next_exact_measurement_selected",
            "selected_candidate_id": "candidate_b",
            "risks": ["real QoR measurement is still required"],
        }
        selected = {"candidate_id": "candidate_b", "parameters": {"lanes": 16}}

        self.assertEqual(stage4_llm_errors(output, selected, campaign_complete=False), [])
        self.assertIn(
            "dse_parameter_agent status is next_exact_measurement_selected",
            stage4_llm_errors(output, selected, campaign_complete=True),
        )
        self.assertIn(
            "dse_parameter_agent status is next_exact_measurement_selected",
            stage4_llm_errors(
                {**output, "selected_candidate_id": "candidate_a"},
                selected,
                campaign_complete=False,
            ),
        )

    def test_stage4_successor_reconciles_its_retry_and_contamination_barrier(self) -> None:
        with TemporaryDirectory() as temp:
            state_path = Path(temp) / "sacg_state.json"
            write_json(
                state_path,
                {
                    "design_id": "stage4-retry-reconciliation",
                    "nodes": [
                        {
                            "id": "node.parameter_binding",
                            "type": "stage",
                            "name": "parameter binding",
                            "constraints": ["constraint.parameter.binding"],
                            "artifacts": [],
                        }
                    ],
                    "constraints": [
                        {
                            "id": "constraint.parameter.binding",
                            "type": "parameter",
                            "nodes": ["node.parameter_binding"],
                            "edges": [],
                            "artifacts": ["artifact.stage4.parameter_binding"],
                            "facts": {},
                        }
                    ],
                    "invariants": [
                        {
                            "id": "invariant.parameter_binding_static",
                            "checker": "parameter_binding_static_check",
                            "constraints": ["constraint.parameter.binding"],
                            "status": "unknown",
                            "latest_evidence": None,
                        }
                    ],
                    "memory": {
                        "retry_requests": [
                            {
                                "id": "retry_request.0001",
                                "status": "open",
                                "target_stage": "stage4.parameter_binding",
                            }
                        ],
                        "contamination_barriers": [
                            {
                                "id": "contamination_barrier.0001",
                                "artifact_id": "artifact.stage4.parameter_binding",
                                "status": "active",
                            }
                        ],
                    },
                },
            )
            store = SACGStore(state_path)
            transition = store.declare_transition(
                action_type="parameter_binding",
                touched_nodes=["node.parameter_binding"],
                touched_edges=[],
                touched_constraints=["constraint.parameter.binding"],
            )
            store.bind_artifact(
                "artifact.stage4.parameter_binding",
                str(Path(temp) / "parameter_binding.json"),
                "stage.parameter_binding",
                ["node.parameter_binding"],
                [],
                ["constraint.parameter.binding"],
                transition["id"],
            )
            store.attach_evidence(
                checker="parameter_binding_static_check",
                status="pass",
                invariant="invariant.parameter_binding_static",
                constraints=["constraint.parameter.binding"],
                artifacts=["artifact.stage4.parameter_binding"],
                log_path=str(Path(temp) / "parameter_static_checks.json"),
                transition_id=transition["id"],
            )

            store.promote(transition["id"])
            store.record_stage_outcome(
                stage="stage4.parameter_binding",
                status="ready",
                transition_id=transition["id"],
                summary="measurement-only Stage-4 handoff is valid",
            )

            memory = store.state["memory"]
            self.assertEqual(memory["retry_requests"][0]["status"], "closed")
            self.assertEqual(memory["contamination_barriers"][0]["status"], "superseded")

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

    def test_explicit_flattened_physical_tuples_keep_compute_array_binding(self) -> None:
        tuples = physical_candidate_tuples({
            "hardware_parameter_tuples": [{
                "lanes": 16,
                "compute_array_rows": 16,
                "compute_array_cols": 32,
                "fifo_depth": 8,
                "activation_banks": 2,
            }]
        })

        self.assertEqual(tuples, [{
            "lanes": 16,
            "compute_array_rows": 16,
            "compute_array_cols": 32,
            "fifo_depth": 8,
            "activation_banks": 2,
        }])

    def test_internal_compute_columns_can_exceed_stream_lanes_by_whole_groups(self) -> None:
        tuples = physical_candidate_tuples({
            "hardware_parameter_tuples": [{
                "lanes": 4,
                "compute_array": {"rows": 4, "cols": 16},
                "physical_fifo_depth_entries": 16,
                "activation_bank_count": 2,
            }]
        })

        self.assertEqual(len(tuples), 1)
        self.assertEqual(tuples[0]["compute_array_cols"], 16)

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

    def test_candidate_universe_preserves_lane_conditioned_pe_pairs(self) -> None:
        search = {
            "candidate_universe": {
                "compute_array": {
                    "legal_row_col_pairs_by_lanes": {
                        "8": [{"rows": 4, "cols": 4}],
                        "16": [{"rows": 8, "cols": 16}],
                    }
                },
                "physical_fifo_depth": {"legal_values": [32, 64]},
                "activation_bank_count": {"legal_values": [2, 4]},
            }
        }

        tuples = physical_candidate_tuples(search)

        self.assertEqual(len(tuples), 8)
        self.assertEqual(
            {(row["lanes"], row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(8, 4, 4), (16, 8, 16)},
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

    def test_nested_candidate_dimensions_preserve_declared_pe_pairs(self) -> None:
        search = {
            "candidate_universe": {
                "candidate_dimensions": {
                    "lanes": {"legal_values": [8, 16]},
                    "compute_array": {
                        "legal_row_col_pairs": [
                            {"rows": 2, "cols": 4},
                            {"rows": 4, "cols": 8},
                        ]
                    },
                    "physical_fifo_depth": {"legal_values": [2, 4]},
                    "activation_bank_count": {"legal_values": [1, 2]},
                }
            }
        }

        tuples = physical_candidate_tuples(search)

        self.assertEqual(len(tuples), 16)
        self.assertEqual(
            {(row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(2, 4), (4, 8)},
        )
        self.assertNotIn(
            (2, 8),
            {(row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
        )

    def test_candidate_dimensions_preserve_lane_conditioned_array_tuples(self) -> None:
        dimensions = {
            "lanes": {"legal_values": [8, 16]},
            "compute_array": {"legal_lane_row_col_tuples": [
                {"lanes": 8, "rows": 4, "cols": 32},
                {"lanes": 16, "rows": 16, "cols": 32},
            ]},
            "physical_fifo_depth": {"legal_values": [32, 64]},
            "activation_bank_count": {"legal_values": [2]},
        }
        tuples = physical_candidate_tuples({"candidate_dimensions": dimensions})
        self.assertEqual(len(tuples), 4)
        self.assertEqual(
            {(row["lanes"], row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(8, 4, 32), (16, 16, 32)},
        )
        dimensions["compute_array"]["legal_lane_row_col_tuples"][0]["lanes"] = 32
        with self.assertRaisesRegex(ValueError, "undeclared lane"):
            physical_candidate_tuples({"candidate_dimensions": dimensions})

    def test_universe_correlated_tuples_with_separate_physical_axes(self) -> None:
        universe = {
            "legal_tuples": [
                {"lanes": 8, "compute_array_rows": 4, "compute_array_cols": 32},
                {"lanes": 16, "compute_array_rows": 16, "compute_array_cols": 32},
            ],
            "physical_axes": {
                "physical_fifo_depth": {"legal_values": [32, 64]},
                "activation_bank_count": {"legal_values": [2, 4]},
            },
        }
        tuples = physical_candidate_tuples({"candidate_universe": universe})
        self.assertEqual(len(tuples), 8)
        self.assertEqual(
            {(row["lanes"], row["compute_array_rows"], row["compute_array_cols"]) for row in tuples},
            {(8, 4, 32), (16, 16, 32)},
        )
        del universe["physical_axes"]["physical_fifo_depth"]
        with self.assertRaises(ValueError):
            physical_candidate_tuples({"candidate_universe": universe})

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
        self.assertEqual(bindings["global_params"]["attention_output_cross_token_reuse_tokens"], 1)

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
