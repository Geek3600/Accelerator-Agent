from __future__ import annotations

import unittest

from accagent.framework.dse_estimator import (
    RESOURCE_KEYS,
    _integer_attention_row_services,
    _integer_attention_softmax_cycles,
    _integer_linear_service_profile,
    _integer_norm_service,
    _pipeline_cycles,
    cost_features,
    estimate,
    linear_schedule_id,
    rank_candidates,
    validation_report,
)
from accagent.framework.stage_params import apply_candidate_schedule_gate


class DseEstimatorTest(unittest.TestCase):
    def features(self, **overrides) -> dict:
        parameters = {
            "lanes": 16, "compute_array_rows": 4, "compute_array_cols": 2,
            "elem_bits": 16, "fifo_depth": 16, "activation_banks": 2,
            "weight_banks": 1, "weight_memory": "xpm_uram",
            "activation_memory": "xpm_bram", "large_cache_memory": "xpm_uram",
            "cache_refill_data_width_bits": 512,
            "cross_token_reuse_tokens": 16,
        }
        parameters.update(overrides)
        workload = {"hidden_size": 1024, "intermediate_size": 4096, "sequence_length": 16, "processed_tokens": 16, "model_layers": 12, "axi_data_width_bits": 512}
        terms = [
            {"stage": "project", "physical_role": "weight_project", "elements": 1024 * 1024, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "up", "physical_role": "weight_up", "elements": 1024 * 4096, "element_bits": 16, "factors": ["hidden_size", "intermediate_size"]},
            {"stage": "down", "physical_role": "weight_down", "elements": 1024 * 4096, "element_bits": 16, "factors": ["intermediate_size", "hidden_size"]},
        ]
        return cost_features(parameters, workload, terms, "example_decoder", "target_fpga")

    def sample(self, features: dict, fingerprint: str = "first") -> dict:
        cycles = round(features["proxies"]["cycles"] * 2)
        return {
            "source_fingerprint": fingerprint, "cost_features": features,
            "performance_model": "synthesizable_dut_counter",
            "cycle_evidence": {"kind": "rtl_counter", "status": "pass", "is_rtl_counter_measurement": True},
            "resources": {key: round(features["proxies"][key] * 3) for key in RESOURCE_KEYS},
            "clock_frequency_mhz": 200.0,
            "performance_estimation": {
                "latency_cycles": cycles, "rtl_cycles_measured": True,
                "measurement_complete": True, "count_is_latency": True,
            },
            "performance_tokens_per_second": features["workload"]["processed_tokens"] * 200_000_000 / cycles,
        }

    def analytical_sample(self, features: dict, fingerprint: str) -> dict:
        sample = self.sample(features, fingerprint)
        sample["performance_model"] = "single_block_reuse_operator_token_pipeline_v2_no_handoff"
        sample["cycle_evidence"] = {
            "kind": "analytical_source_schedule", "status": "pass",
            "is_rtl_counter_measurement": False,
        }
        sample["performance_estimation"]["rtl_cycles_measured"] = False
        sample["performance_estimation"].pop("measurement_complete")
        sample["performance_estimation"].pop("count_is_latency")
        return sample

    def anchors(self, features: dict) -> list[dict]:
        return [self.sample(features, "first"), self.sample(features, "second")]

    def test_no_samples_does_not_invent_qor(self) -> None:
        prediction = estimate(self.features(), [])
        self.assertEqual(prediction["status"], "insufficient_evidence")
        self.assertNotIn("resources", prediction)

    def test_calibrates_cycles_resources_and_clock_against_an_anchor(self) -> None:
        features = self.features()
        sample = self.sample(features)
        sample["resources"]["bram18"] = 0
        second = self.sample(features, "second")
        second["resources"]["bram18"] = 0
        prediction = estimate(features, [sample, second])
        self.assertEqual(prediction["latency_cycles"], sample["performance_estimation"]["latency_cycles"])
        self.assertEqual(prediction["resources"], sample["resources"])
        self.assertAlmostEqual(prediction["performance_tokens_per_second"], sample["performance_tokens_per_second"])
        self.assertFalse(prediction["cross_model_extrapolation"])

    def test_larger_array_is_not_assumed_to_give_ideal_linear_speedup(self) -> None:
        small = self.features()
        larger = self.features(compute_array_rows=8, compute_array_cols=4)
        sample = self.sample(small)
        prediction = estimate(larger, [sample, self.sample(small, "second")])
        self.assertGreater(prediction["performance_tokens_per_second"], sample["performance_tokens_per_second"])
        self.assertLess(prediction["performance_tokens_per_second"] / sample["performance_tokens_per_second"], 4)
        self.assertGreater(prediction["resources"]["dsp"], sample["resources"]["dsp"])

    def test_more_banks_do_not_multiply_compute_throughput(self) -> None:
        features = self.features()
        sample = self.sample(features)
        prediction = estimate(self.features(weight_banks=8), [sample, self.sample(features, "second")])
        self.assertAlmostEqual(prediction["performance_tokens_per_second"], sample["performance_tokens_per_second"])

    def test_refill_beats_follow_repeated_physical_cache_traffic(self) -> None:
        features = self.features(cross_token_reuse_tokens=8)
        proxy = features["proxies"]

        self.assertGreater(
            proxy["ddr_refill_bytes_per_layer"],
            proxy["semantic_weight_image_bytes_per_layer"],
        )
        self.assertEqual(
            proxy["ddr_refill_beats_per_layer"],
            (proxy["ddr_refill_bytes_per_layer"] + 63) // 64,
        )
        self.assertEqual(
            proxy["semantic_weight_image_beats_per_layer"],
            (proxy["semantic_weight_image_bytes_per_layer"] + 63) // 64,
        )

    def test_cycle_breakdown_is_integer_and_declares_analytical_limits(self) -> None:
        proxy = self.features()["proxies"]

        self.assertEqual(type(proxy["cycles"]), int)
        self.assertEqual(type(proxy["compute_cycles_per_layer"]), int)
        self.assertEqual(
            proxy["pipeline_steady_state_ii_cycles"],
            max(proxy["operator_stage_service_cycles_per_token"].values()),
        )
        self.assertEqual(proxy["pipeline_cycle_terms"]["total"], proxy["cycles"])
        self.assertEqual(
            sum(proxy["pipeline_cycle_terms"][key] for key in (
                "initial_weight_refill",
                "compute_all_layers",
                "exposed_inter_layer_refill_stall",
            )),
            proxy["cycles"],
        )
        self.assertFalse(proxy["cycle_model_is_rtl_exact"])
        self.assertTrue(proxy["cycle_model_unmodeled_effects"])

    def test_integer_operator_services_use_per_token_cycles(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "weight_bits": 4,
            "activation_bits": 8, "acc_bits": 32, "scale_bits": 32,
            "scale_shift": 31, "rounding": "nearest_even", "saturation": True,
        }
        workload = {**base["workload"], "num_q_heads": 16, "head_dim": 64}
        terms = [
            {**term, "element_bits": 4}
            for term in [
                {"stage": "project", "physical_role": "weight_project", "elements": 1024 * 1024, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]},
                {"stage": "up", "physical_role": "weight_up", "elements": 1024 * 4096, "element_bits": 16, "factors": ["hidden_size", "intermediate_size"]},
                {"stage": "down", "physical_role": "weight_down", "elements": 1024 * 4096, "element_bits": 16, "factors": ["intermediate_size", "hidden_size"]},
            ]
        ]

        features = cost_features(
            parameters, workload, terms, "example_decoder", "target_fpga"
        )
        stages = features["proxies"]["operator_stage_service_cycles_per_token"]
        profile = features["proxies"]["operator_stage_service_profile_cycles_per_token"]

        self.assertEqual(
            stages["attention"],
            max(_integer_attention_row_services(
                workload["sequence_length"], workload["num_q_heads"],
                output_projection_cycles=max((
                    components["attention_projection_completion_after_final_input_cycles"]
                    for role, components in features["proxies"]["integer_linear_fsm_cycle_components"].items()
                    if "attn" in role.lower() and ("out" in role.lower() or "proj" in role.lower())
                ), default=0),
            )),
        )
        self.assertEqual(stages["norm1"], _integer_norm_service(workload["hidden_size"], parameters["lanes"])[0])
        self.assertEqual(stages["norm2"], stages["norm1"])
        self.assertEqual(features["proxies"]["operator_stage_sequence_barriers"], [])
        self.assertEqual(
            features["proxies"]["compute_cycles_per_layer"],
            _pipeline_cycles(
                [(name, values, False) for name, values in profile.items()],
                workload["processed_tokens"],
            ),
        )

    def test_integer_linear_counts_fsm_control_memory_and_pipeline_cycles(self) -> None:
        profile, components = _integer_linear_service_profile(
            input_dim=16, output_dim=8, input_lanes=8, output_lanes=8,
            rows=4, cols=4, token_tile_size=1, tokens=1,
        )

        self.assertEqual(components["mac_terms_per_output_tile"], 4)
        self.assertEqual(components["output_tiles"], 2)
        self.assertEqual(components["pipeline_tail_cycles_per_output_tile"], 5)
        self.assertEqual(components["maximum_internal_chunk_compute_cycles"], 25)
        self.assertEqual(
            components["maximum_chunk_fsm_cycles"],
            {
                "sIdle": 1,
                "sInit_per_output_tile": 1,
                "mac_issue_per_output_tile": 4,
                "mac_pipeline_drain_per_output_tile": 5,
                "sCapture_per_output_tile": 1,
                "sWrite_per_output_tile": 1,
            },
        )
        self.assertEqual(components["attention_projection_completion_after_final_input_cycles"], 27)
        self.assertEqual(profile, [25])

    def test_attention_rows_run_as_causal_tokens_arrive(self) -> None:
        stages = [("producer", [5, 5, 5, 5], False), ("attention", [1, 1, 1, 1], False)]

        self.assertEqual(_pipeline_cycles(stages, 4), 21)
        self.assertEqual(_pipeline_cycles([stages[0], ("attention", stages[1][1], True)], 4), 24)

    def test_integer_linear_counts_run_local_output_pipeline_tail(self) -> None:
        source = """
          val writePipeValid0 = RegInit(false.B)
          val writePipeValid5 = RegInit(false.B)
          val outputWritePendingForDrain = WireDefault(false.B)
          val issueOutputRead = outputFull(drainBank) && !outputWritePendingForDrain
        """
        profile, components = _integer_linear_service_profile(
            input_dim=16, output_dim=8, input_lanes=8, output_lanes=8,
            rows=4, cols=4, token_tile_size=1, tokens=1, source=source,
        )

        self.assertEqual(components["output_requant_pipeline_tail_cycles"], 6)
        self.assertEqual(components["attention_projection_completion_after_final_input_cycles"], 33)
        self.assertEqual(profile, [25])

    def test_integer_norm_counts_bound_multicycle_source_states(self) -> None:
        source = """
          val statsAccumulatePending = RegInit(false.B)
          when(state === sFinalize && finalizeStage === 3.U) { state := sSqrtIssue }
          when(state === sReciprocal) {
            when(divIterationReg === 24.U) { state := sEmitRead }
          }
          when(state === sEmitCapture && emitStage === 8.U) { state := sEmit }
        """
        cycles, components = _integer_norm_service(16, 4, source)

        self.assertEqual(components["statistics_read_capture"], 12)
        self.assertEqual(components["statistics_finalize"], 4)
        self.assertEqual(components["reciprocal"], 25)
        self.assertEqual(components["output_read_capture_and_handshake"], 44)
        self.assertEqual(cycles, 123)

    def test_attention_softmax_cycles_follow_the_bound_source_fsm(self) -> None:
        iterative_source = """
          private val sSoftmaxMax :: sSoftmaxExp :: sSoftmaxDivide :: sSoftmaxProb :: Nil = Enum(4)
          when(state === sSoftmaxDivide) {
            when(divIterationReg === 31.U) { state := sSoftmaxProb }
              .otherwise { divIterationReg := divIterationReg + 1.U }
          }
        """
        cycles, components = _integer_attention_softmax_cycles(iterative_source)

        self.assertEqual(cycles, 35)
        self.assertEqual(components["restoring_divider_iterations"], 32)
        self.assertEqual(_integer_attention_softmax_cycles("when(state === sSoftmax) { state := sVRead }")[0], 1)

    def test_cost_features_count_run_local_iterative_softmax(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "weight_bits": 4,
            "activation_bits": 8, "acc_bits": 32, "scale_bits": 32,
            "scale_shift": 31, "rounding": "nearest_even", "saturation": True,
        }
        terms = [
            {**term, "element_bits": 4}
            for term in [
                {"stage": "attention", "physical_role": "weight_qkv", "elements": 1024 * 1024, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]},
                {"stage": "attention", "physical_role": "weight_attn_out", "elements": 1024 * 1024, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]},
            ]
        ]
        workload = {**base["workload"], "num_q_heads": 16, "head_dim": 64}
        iterative_source = """
          private val sSoftmaxMax :: sSoftmaxExp :: sSoftmaxDivide :: sSoftmaxProb :: Nil = Enum(4)
          when(state === sSoftmaxDivide) {
            when(divIterationReg === 31.U) { state := sSoftmaxProb }
              .otherwise { divIterationReg := divIterationReg + 1.U }
          }
        """
        baseline = cost_features(parameters, workload, terms, "gpt2", "target_fpga")
        iterative = cost_features(
            parameters, workload, terms, "gpt2", "target_fpga",
            attention_source=iterative_source, allow_cycle_break_fallback=True,
        )

        self.assertEqual(baseline["proxies"]["integer_attention_softmax_cycles_per_head"], 1)
        self.assertEqual(iterative["proxies"]["integer_attention_softmax_cycles_per_head"], 35)
        self.assertIn(iterative["proxies"]["cycle_model_status"], {"estimated", "counterfactual_cycle_break"})

    def test_attention_output_projection_uses_query_head_width(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "weight_bits": 4,
            "activation_bits": 8, "acc_bits": 32, "scale_bits": 32,
            "scale_shift": 31, "rounding": "nearest_even", "saturation": True,
            "lanes": 8, "compute_array_rows": 8, "compute_array_cols": 4,
            "cross_token_reuse_tokens": 4,
        }
        workload = {
            **base["workload"], "hidden_size": 1152, "intermediate_size": 6912,
            "num_q_heads": 4, "num_kv_heads": 1, "head_dim": 256,
            "sequence_length": 32, "processed_tokens": 32, "model_layers": 26,
        }
        terms = [
            {"stage": "attention", "physical_role": "weight_qkv",
             "elements": 1152 * (4 + 2) * 256, "element_bits": 4,
             "factors": ["hidden_size", "num_q_heads", "head_dim"]},
            {"stage": "attention", "physical_role": "weight_attn_out",
             "elements": 1152 * 4 * 256, "element_bits": 4,
             "factors": ["num_q_heads", "head_dim", "hidden_size"]},
            {"stage": "mlp", "physical_role": "weight_mlp_gate",
             "elements": 1152 * 6912, "element_bits": 4,
             "factors": ["hidden_size", "intermediate_size"]},
            {"stage": "mlp", "physical_role": "weight_mlp_up",
             "elements": 1152 * 6912, "element_bits": 4,
             "factors": ["hidden_size", "intermediate_size"]},
            {"stage": "mlp", "physical_role": "weight_mlp_down",
             "elements": 6912 * 1152, "element_bits": 4,
             "factors": ["intermediate_size", "hidden_size"]},
        ]

        features = cost_features(parameters, workload, terms, "gemma3_text", "xcvu9p")
        projection = features["proxies"]["integer_linear_fsm_cycle_components"]["weight_attn_out"]

        self.assertEqual(projection["mac_terms_per_output_tile"], 256)
        self.assertEqual(projection["input_beats_per_token"], 4)
        self.assertEqual(projection["output_beats_per_token"], 144)
        self.assertEqual(features["architecture_regime"]["attention_output_cross_token_reuse_tokens"], 1)
        self.assertEqual(features["proxies"]["cycle_model_status"], "estimated")
        self.assertGreater(features["proxies"]["cycles"], 0)

    def test_batch_size_one_keeps_sequence_length_token_context(self) -> None:
        base = self.features()
        workload = {**base["workload"], "batch_size": 1}
        features = cost_features(
            base["parameters"], workload,
            [
                {"stage": "project", "physical_role": "weight_project", "elements": 1024 * 1024, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]},
                {"stage": "up", "physical_role": "weight_up", "elements": 1024 * 4096, "element_bits": 16, "factors": ["hidden_size", "intermediate_size"]},
                {"stage": "down", "physical_role": "weight_down", "elements": 1024 * 4096, "element_bits": 16, "factors": ["intermediate_size", "hidden_size"]},
            ],
            "example_decoder", "target_fpga",
        )

        self.assertEqual(features["proxies"]["effective_cross_token_reuse_tokens"], 8)

    def test_attention_projection_chunk_wait_blocks_by_default_and_fallback_is_explicit(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "weight_bits": 4,
            "activation_bits": 8, "acc_bits": 32, "scale_bits": 32,
            "scale_shift": 31, "rounding": "nearest_even", "saturation": True,
            "attention_output_cross_token_reuse_tokens": 8,
        }
        terms = [
            {"stage": "attention", "physical_role": "weight_qkv", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "attention", "physical_role": "weight_attn_out", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "mlp", "physical_role": "weight_mlp_down", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
        ]
        features = cost_features(
            parameters,
            {**base["workload"], "num_q_heads": 16, "head_dim": 64},
            terms, "gpt2", "target_fpga",
        )

        self.assertEqual(features["proxies"]["cycle_model_status"], "blocked")
        self.assertIsNone(features["proxies"]["cycles"])
        self.assertEqual(features["proxies"]["cycle_model_blockers"][0]["token_tile_size"], 8)
        self.assertEqual(estimate(features, [])["status"], "blocked_schedule")
        hypothetical = cost_features(
            parameters,
            {**base["workload"], "num_q_heads": 16, "head_dim": 64},
            terms, "gpt2", "target_fpga", allow_cycle_break_fallback=True,
        )
        self.assertEqual(hypothetical["proxies"]["cycle_model_status"], "counterfactual_cycle_break")
        self.assertGreater(hypothetical["proxies"]["cycles"], 0)
        self.assertEqual(estimate(hypothetical, [])["status"], "counterfactual_schedule")
        hypothetical_proxy = hypothetical["proxies"]
        self.assertEqual(
            hypothetical_proxy["effective_cross_token_reuse_tokens_by_role"],
            {"weight_qkv": 8, "weight_attn_out": 1, "weight_mlp_down": 8},
        )
        self.assertEqual(
            hypothetical_proxy["ddr_refill_traversals_by_role"],
            {"weight_qkv": 2, "weight_attn_out": 16, "weight_mlp_down": 2},
        )
        self.assertEqual(
            hypothetical_proxy["tile_requests_by_role"]["weight_attn_out"],
            8 * features["proxies"]["tile_requests_by_role"]["weight_attn_out"],
        )
        self.assertGreater(
            hypothetical_proxy["ddr_refill_bytes_per_layer"],
            features["proxies"]["ddr_refill_bytes_per_layer"],
        )

        role_scoped = cost_features(
            {
                **parameters,
                "attention_output_cross_token_reuse_tokens": 1,
            },
            {**base["workload"], "num_q_heads": 16, "head_dim": 64},
            terms, "gpt2", "target_fpga",
        )
        self.assertEqual(role_scoped["proxies"]["cycle_model_status"], "estimated")
        self.assertEqual(
            role_scoped["proxies"]["effective_cross_token_reuse_tokens_by_role"],
            {"weight_qkv": 8, "weight_attn_out": 1, "weight_mlp_down": 8},
        )
        self.assertEqual(
            role_scoped["architecture_regime"]["attention_output_cross_token_reuse_tokens"],
            1,
        )

    def test_candidate_schedule_gate_survives_qor_estimation_failure(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "compute_array_cols": 3,
            "cross_token_reuse_tokens": 4, "weight_bits": 4, "activation_bits": 8,
            "acc_bits": 32, "scale_bits": 32, "scale_shift": 31,
            "rounding": "nearest_even", "saturation": True,
            "attention_output_cross_token_reuse_tokens": 4,
        }
        workload = {
            **base["workload"], "sequence_length": 32, "processed_tokens": 32,
            "intermediate_size": 1000, "num_q_heads": 16, "head_dim": 64,
        }
        terms = [
            {"stage": "attention", "physical_role": "weight_qkv", "elements": 1024 * 1024,
             "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "attention", "physical_role": "weight_attn_out", "elements": 1024 * 1024,
             "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "mlp", "physical_role": "weight_mlp_down", "elements": 1000 * 1024,
             "element_bits": 4, "factors": ["intermediate_size", "hidden_size"]},
        ]
        record = {"feasible": True, "hard_constraint_errors": []}

        blockers = apply_candidate_schedule_gate(record, parameters, workload, terms)
        self.assertEqual(blockers[0]["kind"], "cyclic_stream_wait")
        with self.assertRaises(ValueError):
            cost_features(parameters, workload, terms, "gpt2", "target_fpga")

        self.assertFalse(record["feasible"])
        self.assertEqual(len(record["hard_constraint_errors"]), 1)
        self.assertIn("DSE source schedule is blocked", record["hard_constraint_errors"][0])

    def test_single_token_attention_projection_chunk_has_finite_cycles(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "weight_bits": 4,
            "activation_bits": 8, "acc_bits": 32, "scale_bits": 32,
            "scale_shift": 31, "rounding": "nearest_even", "saturation": True,
            "cross_token_reuse_tokens": 1,
        }
        terms = [
            {"stage": "attention", "physical_role": "weight_qkv", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "attention", "physical_role": "weight_attn_out", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "mlp", "physical_role": "weight_mlp_down", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
        ]
        features = cost_features(
            parameters,
            {**base["workload"], "num_q_heads": 16, "head_dim": 64},
            terms, "gpt2", "target_fpga",
        )

        self.assertEqual(features["proxies"]["cycle_model_status"], "estimated")
        self.assertGreater(features["proxies"]["cycles"], 0)

    def test_counterfactual_reuse_does_not_repeat_cache_resident_weight_refills(self) -> None:
        base = self.features()
        parameters = {
            **base["parameters"], "compute_backend": "integer_dsp", "weight_bits": 4,
            "activation_bits": 8, "acc_bits": 32, "scale_bits": 32,
            "scale_shift": 31, "rounding": "nearest_even", "saturation": True,
            "attention_output_cross_token_reuse_tokens": 8,
        }
        terms = [
            {"stage": "attention", "physical_role": "weight_qkv", "elements": 1024 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "attention", "physical_role": "weight_attn_out", "elements": 16 * 1024, "element_bits": 4, "factors": ["hidden_size", "hidden_size"]},
        ]
        workload = {**base["workload"], "num_q_heads": 16, "head_dim": 64}
        features = cost_features(
            parameters, workload, terms, "gpt2", "target_fpga",
            allow_cycle_break_fallback=True,
        )

        self.assertEqual(features["proxies"]["effective_cross_token_reuse_tokens_by_role"]["weight_attn_out"], 1)
        self.assertEqual(features["proxies"]["cycle_model_fallback"]["token_chunks_by_role"]["weight_attn_out"], 16)
        self.assertEqual(features["proxies"]["ddr_refill_traversals_by_role"]["weight_attn_out"], 1)

    def test_analytical_cycles_do_not_calibrate_cycle_counts(self) -> None:
        features = self.features()
        samples = [
            self.analytical_sample(features, "analysis-a"),
            self.analytical_sample(features, "analysis-b"),
        ]

        prediction = estimate(features, samples)

        self.assertEqual(prediction["cycle_calibration_sample_count"], 0)
        self.assertEqual(prediction["cycle_estimate_source"], "uncalibrated_integer_structural_proxy")
        self.assertEqual(prediction["latency_cycles"], features["proxies"]["cycles"])

    def test_missing_counter_estimation_does_not_crash_counter_filter(self) -> None:
        sample = self.sample(self.features())
        sample["performance_estimation"] = None
        self.assertFalse(__import__(
            "accagent.framework.dse_estimator", fromlist=["_has_measured_cycle_counter"]
        )._has_measured_cycle_counter(sample))

    def test_uram_weight_storage_does_not_consume_bram_proxy(self) -> None:
        features = self.features()
        bram_weights = self.features(weight_memory="xpm_bram")
        self.assertGreater(bram_weights["proxies"]["bram36"], features["proxies"]["bram36"])
        self.assertGreater(features["proxies"]["uram"], bram_weights["proxies"]["uram"])

    def test_factored_attention_bias_does_not_add_a_compute_array(self) -> None:
        features = self.features()
        matrix = {
            "stage": "attention", "physical_role": "weight_qkv",
            "elements": 1024 * 1024, "element_bits": 16,
            "factors": ["hidden_size", "num_q_heads", "head_dim"],
        }
        bias = {
            "stage": "attention", "physical_role": "weight_qkv_bias",
            "elements": 1024, "element_bits": 16,
            "factors": ["num_q_heads", "head_dim"],
        }
        def build(terms):
            return cost_features(features["parameters"], features["workload"], terms,
                                 "example_decoder", "target_fpga")
        without_bias = build([matrix])
        with_bias = build([matrix, bias])
        self.assertEqual(with_bias["proxies"]["dsp"], without_bias["proxies"]["dsp"])
        self.assertEqual(with_bias["proxies"]["compute_cycles_per_layer"], without_bias["proxies"]["compute_cycles_per_layer"])
        self.assertGreater(with_bias["proxies"]["ddr_refill_beats_per_layer"], without_bias["proxies"]["ddr_refill_beats_per_layer"])
        # 16 lanes of FP16 bias need four 72-bit-wide URAM slices.
        self.assertEqual(with_bias["proxies"]["uram"] - without_bias["proxies"]["uram"], 4)

    def test_changed_structural_model_requires_matching_anchor_features(self) -> None:
        features = self.features()
        old_features = {**features, "estimator_model": "previous_structural_model"}
        self.assertEqual(estimate(features, self.anchors(old_features))["status"], "insufficient_evidence")

    def test_resident_weight_capacity_bound_does_not_shrink_with_banking(self) -> None:
        features = self.features()
        banked = self.features(weight_banks=8)
        self.assertEqual(features["resource_lower_bounds"], banked["resource_lower_bounds"])
        anchors = self.anchors(features)
        for sample in anchors:
            sample["resources"]["uram"] = 0
        prediction = estimate(features, anchors)
        self.assertEqual(prediction["resources"]["uram"], features["resource_lower_bounds"]["uram"])

    def test_blocking_kernel_samples_cannot_calibrate_the_streaming_kernel(self) -> None:
        features = self.features()
        self.assertEqual(features["linear_schedule"], linear_schedule_id())
        old_sample = self.sample({**features, "linear_schedule": "legacy_blocking_fp"})
        self.assertEqual(estimate(features, [old_sample])["status"], "insufficient_evidence")
        del old_sample["cost_features"]["linear_schedule"]
        self.assertEqual(estimate(features, [old_sample])["status"], "insufficient_evidence")
        self.assertEqual(validation_report([old_sample])["status"], "insufficient_independent_samples")

    def test_token_tile_buffers_increase_structural_bram_proxy(self) -> None:
        full_tile = self.features()
        small_workload = {**full_tile["workload"], "sequence_length": 8, "processed_tokens": 8}
        terms = [
            {"stage": "project", "physical_role": "weight_project", "elements": 1024 * 1024, "element_bits": 16, "factors": ["hidden_size", "hidden_size"]},
            {"stage": "up", "physical_role": "weight_up", "elements": 1024 * 4096, "element_bits": 16, "factors": ["hidden_size", "intermediate_size"]},
            {"stage": "down", "physical_role": "weight_down", "elements": 1024 * 4096, "element_bits": 16, "factors": ["intermediate_size", "hidden_size"]},
        ]
        full_tile = cost_features(full_tile["parameters"], full_tile["workload"], terms, "example_decoder", "target_fpga")
        small_tile = cost_features(
            full_tile["parameters"], small_workload, terms,
            "example_decoder", "target_fpga",
        )
        self.assertGreater(full_tile["proxies"]["bram36"], small_tile["proxies"]["bram36"])

    def test_model_layers_change_cycles_not_physical_resource_counts(self) -> None:
        features = self.features()
        sample = self.sample(features)
        doubled = {**features, "workload": {**features["workload"], "model_layers": 24}, "proxies": {**features["proxies"], "cycles": features["proxies"]["cycles"] * 2}}
        prediction = estimate(doubled, [sample, self.sample(features, "second")])
        self.assertEqual(prediction["resources"], sample["resources"])
        self.assertAlmostEqual(prediction["performance_tokens_per_second"], sample["performance_tokens_per_second"] / 2)

    def test_incompatible_device_precision_and_memory_are_not_calibrators(self) -> None:
        features = self.features()
        sample = self.sample(features)
        for key, value in [("part", "other"), ("precision_bits", 32), ("memory_implementation", ["other"])]:
            with self.subTest(key=key):
                prediction = estimate({**features, key: value}, [sample])
                self.assertEqual(prediction["status"], "insufficient_evidence")
        prediction = estimate({**features, "family": "different_decoder"}, [sample, self.sample(features, "second")])
        self.assertTrue(prediction["cross_model_extrapolation"])

    def test_compatible_cross_model_samples_are_combined(self) -> None:
        features = self.features()
        same_family = self.sample(features, "same")
        cross_family = self.sample({**features, "family": "other_decoder"}, "cross")
        prediction = estimate(features, [same_family, cross_family])

        self.assertEqual(prediction["status"], "estimated")
        self.assertEqual(prediction["calibration_sample_count"], 2)
        self.assertTrue(prediction["cross_model_calibration"])
        self.assertFalse(prediction["cross_model_extrapolation"])
        self.assertEqual(prediction["anchor_source_fingerprints"], ["same", "cross"])

    def test_single_compatible_sample_is_not_reported_as_an_estimate(self) -> None:
        prediction = estimate(self.features(), [self.sample(self.features())])
        self.assertEqual(prediction["status"], "insufficient_evidence")
        self.assertNotIn("performance_tokens_per_second", prediction)

    def test_held_out_validation_excludes_the_test_fingerprint(self) -> None:
        features = self.features()
        first = self.sample(features)
        second = self.sample(features, "second")
        third = self.sample(features, "third")
        second["resources"]["dsp"] *= 2
        report = validation_report([first, second, third])
        self.assertEqual(report["held_out_prediction_count"], 3)
        self.assertGreater(report["mean_relative_absolute_error"]["dsp"], 0)
        self.assertEqual(validation_report([first])["status"], "insufficient_independent_samples")

    def test_candidates_with_predicted_resource_overflow_rank_after_fitting_ones(self) -> None:
        anchor = self.anchors(self.features())
        records = [
            {"candidate_id": "huge", "feasible": True, "qor_estimate": estimate(self.features(compute_array_rows=16, compute_array_cols=16), anchor)},
            {"candidate_id": "fits", "feasible": True, "qor_estimate": estimate(self.features(), anchor)},
        ]
        ranked = rank_candidates(records, {"performance_tokens_per_second": 170}, {"dsp": anchor[0]["resources"]["dsp"] + 1})
        self.assertEqual(ranked, ["fits", "huge"])

    def test_target_meeting_throughput_beats_small_resources_and_anchor_proximity(self) -> None:
        def record(name, tps, clock, dsp, distance):
            return {"candidate_id": name, "feasible": True, "qor_estimate": {
                "status": "estimated", "resources": {"dsp": dsp},
                "performance_tokens_per_second": tps, "clock_frequency_mhz": clock,
                "extrapolation_distance": distance,
            }}
        records = [record("small", 10, 300, 20, 0),
                   record("meets", 180, 250, 500, 0),
                   record("fast", 250, 260, 800, 2)]
        targets = {"performance_tokens_per_second": 170, "clock_frequency_mhz": 250}
        self.assertEqual(rank_candidates(records, targets, {"dsp": 1000}),
                         ["fast", "meets", "small"])
        self.assertEqual(rank_candidates(records, targets, {"dsp": 600}),
                         ["meets", "small", "fast"])

    def test_uncalibrated_candidates_rank_by_structural_cycles_not_candidate_id(self) -> None:
        narrow = self.features(compute_array_rows=4, compute_array_cols=1)
        wide = self.features(compute_array_rows=4, compute_array_cols=16)
        records = [
            {
                "candidate_id": "a_narrow",
                "feasible": True,
                "qor_estimate": {"status": "insufficient_evidence"},
                "structural_cost_proxy": narrow["proxies"],
            },
            {
                "candidate_id": "z_wide",
                "feasible": True,
                "qor_estimate": {"status": "insufficient_evidence"},
                "structural_cost_proxy": wide["proxies"],
            },
        ]

        self.assertLess(wide["proxies"]["cycles"], narrow["proxies"]["cycles"])
        budget = {key: 10_000_000 for key in RESOURCE_KEYS}
        self.assertEqual(rank_candidates(records, {}, budget), ["z_wide", "a_narrow"])

    def test_uncalibrated_proxy_resource_overflow_is_only_a_ranking_penalty(self) -> None:
        balanced = self.features(compute_array_rows=4, compute_array_cols=8)
        over_budget = self.features(compute_array_rows=16, compute_array_cols=16)
        records = [
            {
                "candidate_id": "fast_over_budget",
                "feasible": True,
                "qor_estimate": {"status": "insufficient_evidence"},
                "structural_cost_proxy": over_budget["proxies"],
            },
            {
                "candidate_id": "balanced",
                "feasible": True,
                "qor_estimate": {"status": "insufficient_evidence"},
                "structural_cost_proxy": balanced["proxies"],
            },
        ]
        budget = {"dsp": balanced["proxies"]["dsp"] + 1}

        self.assertEqual(rank_candidates(records, {}, budget), ["balanced", "fast_over_budget"])
        self.assertTrue(all(record["feasible"] for record in records))


if __name__ == "__main__":
    unittest.main()
