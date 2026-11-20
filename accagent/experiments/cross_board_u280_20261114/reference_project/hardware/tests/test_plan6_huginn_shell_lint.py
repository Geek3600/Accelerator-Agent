import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / "hardware"
VERILATOR = Path("/usr/bin/verilator")


class Plan6HuginnShellLintTest(unittest.TestCase):
    def test_vu9p_shell_wrapper_elaborates(self):
        if not VERILATOR.is_file():
            self.skipTest(f"Verilator is not installed at {VERILATOR}")

        sources = [
            "rtwsr_plan6_huginn_9p_axi_bd.v",
            "rtwsr_plan6_huginn_shell.sv",
            "rtwsr_transformer_top.sv",
            "rtwsr_linear_command_dispatch.sv",
            "rtwsr_linear_tile_controller.sv",
            "rtwsr_recurrent_command_scheduler.sv",
            "rtwsr_recurrent_sequencer.sv",
            "rtwsr_recurrent_attention_bridge.sv",
            "rtwsr_recurrent_attention_bridge4.sv",
            "rtwsr_qkv_head_buffer.sv",
            "rtwsr_qkv_head_buffer_banked.sv",
            "rtwsr_runtime_tile_gemv.sv",
            "rtwsr_adapter_static_cache.sv",
            "rtwsr_runtime_gamma_pool.sv",
            "rtwsr_dual_track_gemv_array.sv",
            "rtwsr_runtime_weight_subsystem.sv",
            "rtwsr_runtime_weight_pool.sv",
            "rtwsr_runtime_weight_ring.sv",
            "uram_active_pool_bank.sv",
            "radix3_5trit_decoder.sv",
            "scale_hoisted_ternary_lane.sv",
            "usw512_word_decoder.sv",
            "usw512_dual_track_channel.sv",
            "usw512_channel_array.sv",
            "rtwsr_rope_kv_cache.sv",
            "rtwsr_attention_gemv_unit.sv",
            "rtwsr_rmsnorm_quant_unit.sv",
            "rtwsr_swiglu_residual_unit.sv",
            "rtwsr_huginn_ffn_pipeline.sv",
            "rtwsr_huginn_payload_descriptor.sv",
            "rtwsr_weight_dma.sv",
            "rtwsr_round_divider_7bit.sv",
            "candidates/u280_hbm/rtwsr_huginn_u280_hbm_descriptor.sv",
            "candidates/u280_hbm/rtwsr_hbm_read_dma_27pc.sv",
            "candidates/u280_hbm/rtwsr_hbm_gearbox_27lane.sv",
            "candidates/u280_hbm/rtwsr_hbm_weight_pool_adapter_27to24.sv",
            "candidates/u280_hbm/rtwsr_plan6_huginn_u280_hbm_weight_path.sv",
            "rtwsr_plan6_huginn_u280_hbm_shell.sv",
        ]
        result = subprocess.run(
            [
                str(VERILATOR),
                "--lint-only",
                "-Wno-fatal",
                "--top-module",
                "rtwsr_plan6_huginn_9p_axi_bd",
                *[str(RTL / source) for source in sources],
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_u280_hbm_shell_elaborates(self):
        if not VERILATOR.is_file():
            self.skipTest(f"Verilator is not installed at {VERILATOR}")

        sources = [
            "rtwsr_plan6_huginn_shell.sv",
            "rtwsr_transformer_top.sv",
            "rtwsr_linear_command_dispatch.sv",
            "rtwsr_linear_tile_controller.sv",
            "rtwsr_recurrent_command_scheduler.sv",
            "rtwsr_recurrent_sequencer.sv",
            "rtwsr_recurrent_attention_bridge.sv",
            "rtwsr_recurrent_attention_bridge4.sv",
            "rtwsr_qkv_head_buffer.sv",
            "rtwsr_qkv_head_buffer_banked.sv",
            "rtwsr_runtime_tile_gemv.sv",
            "rtwsr_adapter_static_cache.sv",
            "rtwsr_runtime_gamma_pool.sv",
            "rtwsr_dual_track_gemv_array.sv",
            "rtwsr_runtime_weight_subsystem.sv",
            "rtwsr_runtime_weight_pool.sv",
            "rtwsr_runtime_weight_ring.sv",
            "uram_active_pool_bank.sv",
            "radix3_5trit_decoder.sv",
            "scale_hoisted_ternary_lane.sv",
            "usw512_word_decoder.sv",
            "usw512_dual_track_channel.sv",
            "usw512_channel_array.sv",
            "rtwsr_rope_kv_cache.sv",
            "rtwsr_attention_gemv_unit.sv",
            "rtwsr_rmsnorm_quant_unit.sv",
            "rtwsr_swiglu_residual_unit.sv",
            "rtwsr_huginn_ffn_pipeline.sv",
            "rtwsr_huginn_payload_descriptor.sv",
            "rtwsr_weight_dma.sv",
            "rtwsr_round_divider_7bit.sv",
            "candidates/u280_hbm/rtwsr_huginn_u280_hbm_descriptor.sv",
            "candidates/u280_hbm/rtwsr_hbm_read_dma_27pc.sv",
            "candidates/u280_hbm/rtwsr_hbm_gearbox_27lane.sv",
            "candidates/u280_hbm/rtwsr_hbm_weight_pool_adapter_27to24.sv",
            "candidates/u280_hbm/rtwsr_plan6_huginn_u280_hbm_weight_path.sv",
            "rtwsr_plan6_huginn_u280_hbm_shell.sv",
        ]
        for attention_candidate in (0, 1):
            with self.subTest(attention_candidate=attention_candidate):
                result = subprocess.run(
                    [
                        str(VERILATOR),
                        "--lint-only",
                        "-Wno-fatal",
                        "--top-module",
                        "rtwsr_plan6_huginn_u280_hbm_shell",
                        f"-GATTENTION_PARALLEL_CANDIDATE={attention_candidate}",
                        *[str(RTL / source) for source in sources],
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=240,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_u280_hbm_cycle_e2e_elaborates(self):
        if not VERILATOR.is_file():
            self.skipTest(f"Verilator is not installed at {VERILATOR}")

        sources = [
            "rtwsr_plan6_huginn_shell.sv",
            "rtwsr_transformer_top.sv",
            "rtwsr_linear_command_dispatch.sv",
            "rtwsr_linear_tile_controller.sv",
            "rtwsr_recurrent_command_scheduler.sv",
            "rtwsr_recurrent_sequencer.sv",
            "rtwsr_recurrent_attention_bridge.sv",
            "rtwsr_recurrent_attention_bridge4.sv",
            "rtwsr_qkv_head_buffer.sv",
            "rtwsr_qkv_head_buffer_banked.sv",
            "rtwsr_runtime_tile_gemv.sv",
            "rtwsr_adapter_static_cache.sv",
            "rtwsr_runtime_gamma_pool.sv",
            "rtwsr_dual_track_gemv_array.sv",
            "rtwsr_runtime_weight_subsystem.sv",
            "rtwsr_runtime_weight_pool.sv",
            "rtwsr_runtime_weight_ring.sv",
            "uram_active_pool_bank.sv",
            "radix3_5trit_decoder.sv",
            "scale_hoisted_ternary_lane.sv",
            "usw512_word_decoder.sv",
            "usw512_dual_track_channel.sv",
            "usw512_channel_array.sv",
            "rtwsr_rope_kv_cache.sv",
            "rtwsr_attention_gemv_unit.sv",
            "rtwsr_rmsnorm_quant_unit.sv",
            "rtwsr_swiglu_residual_unit.sv",
            "rtwsr_huginn_ffn_pipeline.sv",
            "rtwsr_huginn_payload_descriptor.sv",
            "rtwsr_weight_dma.sv",
            "rtwsr_round_divider_7bit.sv",
            "candidates/u280_hbm/rtwsr_huginn_u280_hbm_descriptor.sv",
            "candidates/u280_hbm/rtwsr_hbm_read_dma_27pc.sv",
            "candidates/u280_hbm/rtwsr_hbm_gearbox_27lane.sv",
            "candidates/u280_hbm/rtwsr_hbm_weight_pool_adapter_27to24.sv",
            "candidates/u280_hbm/rtwsr_plan6_huginn_u280_hbm_weight_path.sv",
            "candidates/u280_hbm/rtwsr_u280_hbm_axi_cycle_model.sv",
            "rtwsr_plan6_huginn_u280_hbm_shell.sv",
            "tests/rtwsr_u280_hbm_e2e_bfms.sv",
            "candidates/u280_hbm/rtwsr_u280_hbm_cycle_e2e_tb.sv",
        ]
        for context_tokens in (512, 2048):
            for attention_candidate in (0, 1):
                with self.subTest(context_tokens=context_tokens,
                                  attention_candidate=attention_candidate):
                    result = subprocess.run(
                        [
                            str(VERILATOR),
                            "--lint-only",
                            "--timing",
                            "-Wno-fatal",
                            "--top-module",
                            "rtwsr_u280_hbm_cycle_e2e_tb",
                            f"-GCONTEXT_TOKENS={context_tokens}",
                            "-GGAMMA_PARALLEL_LOAD=1",
                            f"-GATTENTION_PARALLEL_CANDIDATE={attention_candidate}",
                            *[str(RTL / source) for source in sources],
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=240,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_gamma_regions_do_not_overlap(self):
        adapter_size = (ROOT / "results/plan6/huginn_recurrent_core/adapter_gamma.fp16").stat().st_size
        shell = (RTL / "rtwsr_plan6_huginn_shell.sv").read_text()
        self.assertEqual(adapter_size, 337920)
        self.assertLessEqual(adapter_size, 0x00100000)
        self.assertIn("DDR_GAMMA_BASE + 37'h00100000", shell)


if __name__ == "__main__":
    unittest.main()
