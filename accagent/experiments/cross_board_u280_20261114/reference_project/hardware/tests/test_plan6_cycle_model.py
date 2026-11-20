import csv
import json
import tempfile
import unittest
from pathlib import Path

from hardware.plan6_cycle_model import (
    KV_CACHE_BRAM_BYTES,
    PLAN6_MODELS,
    active_context,
    attention_kv_cycles,
    attention_quantizer_cycles,
    block_nonlinear_cycles,
    estimate_case,
    elementwise_cycles,
    linear_cycles,
    norm_cycles,
    prefetch_stall_cycles,
    recurrent_kv_cache_bytes,
    write_outputs,
)


class Plan6CycleModelTests(unittest.TestCase):
    def test_linear_equation(self):
        # ceil(5280/96) * (4 * ceil(17920/256)) + 5 + ceil(5280*16/256)
        self.assertEqual(linear_cycles(5280, 17920), 15735)

    def test_dory_attention_pattern_and_window(self):
        model = PLAN6_MODELS["dory4b"]
        self.assertEqual(active_context(model, 0, 2048), 1024)
        self.assertEqual(active_context(model, 3, 2048), 2048)
        self.assertEqual(active_context(model, 19, 2048), 2048)
        self.assertEqual(active_context(model, 3, 512), 512)

        terms = attention_kv_cycles(model, 3, 2048)
        self.assertEqual(terms["active_context_tokens"], 2048)
        self.assertGreater(terms["qk_pv_cycles"], terms["rope_cycles"])

    def test_attention_quantizer_cycles_match_full_vector_and_windows(self):
        for model in PLAN6_MODELS.values():
            expected = 1 + 11 * model["query_size"] + 2 * ((model["query_size"] + 255) // 256)
            self.assertEqual(attention_quantizer_cycles(model["query_size"]), expected)

    def test_full_core_kv_storage_and_bram_window_accounting(self):
        huginn = estimate_case("huginn", 512)
        self.assertTrue(huginn["kv_cache_offchip"])
        self.assertEqual(huginn["kv_cache_copies"], 4 * 32)
        self.assertEqual(huginn["kv_cache_onchip_window_capacity_bytes"], KV_CACHE_BRAM_BYTES)
        self.assertGreater(huginn["kv_cache_window_max_bytes_per_block"], KV_CACHE_BRAM_BYTES)
        self.assertEqual(
            huginn["kv_cache_bytes_per_recurrent_core"],
            512 * 5280 * 2 * 2 * 4 * 32,
        )
        self.assertEqual(
            huginn["kv_cache_bytes_per_recurrent_core"],
            recurrent_kv_cache_bytes(PLAN6_MODELS["huginn"], 512),
        )

        dory = estimate_case("dory4b", 2048)
        self.assertEqual(dory["kv_cache_copies"], 20 * 4)
        self.assertEqual(dory["kv_cache_window_bytes_per_block"].count(1024 * 1024 * 4), 15)
        self.assertEqual(dory["kv_cache_window_bytes_per_block"].count(2048 * 1024 * 4), 5)
        self.assertEqual(
            dory["kv_cache_bytes_per_recurrent_core"],
            (15 * 1024 + 5 * 2048) * 1024 * 2 * 2 * 4,
        )

    def test_dory_keeps_g_projection_and_separate_gate_up_ops(self):
        result = estimate_case("dory4b", 512)
        self.assertEqual(
            [row["name"] for row in result["attention_linear_ops"]],
            ["q_proj", "k_proj", "v_proj", "g_proj", "o_proj"],
        )
        self.assertEqual(
            [row["name"] for row in result["ffn_linear_ops"]],
            ["gate_proj", "up_proj", "down_proj"],
        )
        self.assertEqual(result["full_attention_blocks"], [3, 7, 11, 15, 19])

    def test_huginn_uses_exported_fused_qkv_and_capacity_safe_gate_up_matrices(self):
        result = estimate_case("huginn", 512)
        self.assertEqual(
            [(row["name"], row["rows"], row["columns"]) for row in result["attention_linear_ops"]],
            [("qkv_proj", 15840, 5280), ("o_proj", 5280, 5280)],
        )
        self.assertEqual(
            [(row["name"], row["rows"], row["columns"]) for row in result["ffn_linear_ops"]],
            [("gate_proj", 17920, 5280), ("up_proj", 17920, 5280), ("down_proj", 5280, 17920)],
        )

    def test_nonlinear_cycles_count_residuals_and_dory_slerp(self):
        huginn = PLAN6_MODELS["huginn"]
        expected_huginn = (
            4 * norm_cycles(huginn["hidden_size"])
            + elementwise_cycles(huginn["intermediate_size"])
            + 2 * elementwise_cycles(huginn["hidden_size"])
        )
        self.assertEqual(block_nonlinear_cycles(huginn), expected_huginn)

        dory = PLAN6_MODELS["dory4b"]
        expected_slerp = 3 * norm_cycles(dory["hidden_size"]) + elementwise_cycles(dory["hidden_size"])
        self.assertGreater(block_nonlinear_cycles(dory), expected_slerp)

    def test_rmsnorm_cycles_include_chunked_bram_reads_and_serial_quantizer(self):
        self.assertEqual(norm_cycles(5280), 34 * 330 + 126)
        self.assertEqual(norm_cycles(7168), 34 * 448 + 126)

    def test_prefetch_transitions_are_adjacent_in_token_and_not_cyclic(self):
        model = PLAN6_MODELS["huginn"]
        result = prefetch_stall_cycles(model, 512)
        operator_count_per_recurrence = 1 + model["core_blocks"] * 5
        expected_operator_count = model["recurrences"] * operator_count_per_recurrence
        self.assertEqual(result["prefetch_transitions"], expected_operator_count - 1)
        self.assertEqual(
            result["prefetched_bytes"],
            result["token_matrix_bytes"] - result["initial_matrix_bytes"],
        )

    def test_categories_sum_and_context_changes_attention_only(self):
        short = estimate_case("ouro14", 512)
        long = estimate_case("ouro14", 2048)
        self.assertEqual(
            sum(short["category_cycles"].values()), short["estimated_cycles_per_token"]
        )
        self.assertEqual(
            sum(long["category_cycles"].values()), long["estimated_cycles_per_token"]
        )
        self.assertEqual(
            short["category_cycles"]["attention_linear_cycles"],
            long["category_cycles"]["attention_linear_cycles"],
        )
        self.assertEqual(
            short["category_cycles"]["ffn_linear_cycles"],
            long["category_cycles"]["ffn_linear_cycles"],
        )
        self.assertGreater(
            long["category_cycles"]["attention_kv_cycles"],
            short["category_cycles"]["attention_kv_cycles"],
        )

    def test_category_latency_and_percent_cover_all_platform_scenarios(self):
        for model_name, model in PLAN6_MODELS.items():
            for context_tokens in model["context_lengths"]:
                case = estimate_case(model_name, context_tokens)
                self.assertAlmostEqual(
                    sum(case["category_latency_ms_per_token"].values()),
                    case["estimated_latency_ms_per_token"],
                    places=9,
                )
                self.assertAlmostEqual(
                    sum(case["category_percent_per_token"].values()), 100.0, places=9
                )

    def test_vu9p_ddr4_and_u280_hbm2_are_distinct_platform_cases(self):
        vu9p = estimate_case("huginn", 512, platform="vu9p_ddr4")
        u280 = estimate_case("huginn", 512, platform="u280_hbm2")
        self.assertEqual((vu9p["fpga_device"], vu9p["external_memory_system"]), ("VU9P", "DDR4"))
        self.assertEqual((u280["fpga_device"], u280["external_memory_system"]), ("U280", "HBM2"))
        self.assertEqual(
            vu9p["category_cycles"]["attention_linear_cycles"],
            u280["category_cycles"]["attention_linear_cycles"],
        )
        self.assertEqual(
            vu9p["category_cycles"]["ffn_linear_cycles"],
            u280["category_cycles"]["ffn_linear_cycles"],
        )
        self.assertEqual(vu9p["kv_cache_bytes_per_recurrent_core"], u280["kv_cache_bytes_per_recurrent_core"])
        self.assertLess(
            u280["category_cycles"]["attention_kv_cycles"],
            vu9p["category_cycles"]["attention_kv_cycles"],
        )
        self.assertLess(
            u280["category_cycles"]["prefetch_stall_cycles"],
            vu9p["category_cycles"]["prefetch_stall_cycles"],
        )
        self.assertLess(u280["estimated_cycles_per_token"], vu9p["estimated_cycles_per_token"])

    def test_outputs_are_compact_and_reproducible(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_cycles_") as directory:
            json_path, csv_path = write_outputs(
                Path(directory) / "cycles.json",
                Path(directory) / "cycles.csv",
            )
            payload = json.loads(json_path.read_text())
            self.assertEqual(payload["format"], "Plan6-Recurrent-Core-Cycle-Model-v4")
            self.assertEqual(payload["result_kind"], "equation_estimate_not_measurement")
            self.assertEqual(
                payload["evaluation_mode"],
                "analytical_equation_model_with_RTL_FSM_cycles",
            )
            self.assertTrue(payload["unmodelled_components"])
            self.assertEqual(len(payload["cases"]), 12)
            self.assertEqual(
                payload["cases"][0]["result_kind"], "equation_estimate_not_measurement"
            )
            self.assertIn("estimated_latency_ms_per_token", payload["cases"][0])
            with csv_path.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 12)
            self.assertEqual({row["model"] for row in rows}, set(PLAN6_MODELS))
            self.assertEqual({row["platform"] for row in rows}, {"vu9p_ddr4", "u280_hbm2"})
            self.assertIn("estimated_cycles_per_token", rows[0])
            self.assertIn("attention_linear_ms_per_token", rows[0])
            self.assertIn("prefetch_stall_percent", rows[0])
            self.assertIn("kv_cache_bytes_per_recurrent_core", rows[0])
            self.assertTrue(rows[0]["unmodelled_components"])


if __name__ == "__main__":
    unittest.main()
