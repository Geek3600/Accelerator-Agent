from __future__ import annotations

import unittest

from accagent.framework.dse_estimator import (
    RESOURCE_KEYS,
    cost_features,
    estimate,
    linear_schedule_id,
    rank_candidates,
    validation_report,
)


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
            "resources": {key: round(features["proxies"][key] * 3) for key in RESOURCE_KEYS},
            "clock_frequency_mhz": 200.0,
            "performance_estimation": {"latency_cycles": cycles},
            "performance_tokens_per_second": features["workload"]["processed_tokens"] * 200_000_000 / cycles,
        }

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
