import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")
RTL = [
    "hardware/rtwsr_transformer_top.sv",
    "hardware/rtwsr_linear_command_dispatch.sv",
    "hardware/rtwsr_linear_tile_controller.sv",
    "hardware/rtwsr_recurrent_command_scheduler.sv",
    "hardware/rtwsr_recurrent_sequencer.sv",
    "hardware/rtwsr_recurrent_attention_bridge.sv",
    "hardware/rtwsr_recurrent_attention_bridge4.sv",
    "hardware/rtwsr_qkv_head_buffer.sv",
    "hardware/rtwsr_qkv_head_buffer_banked.sv",
    "hardware/rtwsr_runtime_tile_gemv.sv",
    "hardware/rtwsr_adapter_static_cache.sv",
    "hardware/rtwsr_runtime_gamma_pool.sv",
    "hardware/rtwsr_dual_track_gemv_array.sv",
    "hardware/rtwsr_runtime_weight_subsystem.sv",
    "hardware/rtwsr_runtime_weight_pool.sv",
    "hardware/rtwsr_runtime_weight_ring.sv",
    "hardware/uram_active_pool_bank.sv",
    "hardware/radix3_5trit_decoder.sv",
    "hardware/scale_hoisted_ternary_lane.sv",
    "hardware/usw512_word_decoder.sv",
    "hardware/usw512_dual_track_channel.sv",
    "hardware/usw512_channel_array.sv",
    "hardware/rtwsr_rope_kv_cache.sv",
    "hardware/rtwsr_attention_gemv_unit.sv",
    "hardware/rtwsr_round_divider_7bit.sv",
    "hardware/rtwsr_rmsnorm_quant_unit.sv",
    "hardware/rtwsr_swiglu_residual_unit.sv",
    "hardware/rtwsr_huginn_ffn_pipeline.sv",
    "hardware/rtwsr_huginn_payload_descriptor.sv",
]


class Plan6TransformerTopLintTests(unittest.TestCase):
    def test_top_lints_for_huginn_ouro_and_dory(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")
        for model_id in (0, 1, 2):
            for timing_candidate in (0, 1):
                for attention_candidate in (0, 1):
                    for attention_heads in (4, 8):
                        with self.subTest(model_id=model_id, timing_candidate=timing_candidate,
                                          attention_candidate=attention_candidate,
                                          attention_heads=attention_heads):
                            lint = subprocess.run(
                                [
                                    str(VERILATOR), "--lint-only", "--timing", "-Wno-fatal",
                                    "--top-module", "rtwsr_transformer_top", f"-GMODEL_ID={model_id}",
                                    f"-GCORE_TIMING_CANDIDATE={timing_candidate}",
                                    f"-GATTENTION_PARALLEL_CANDIDATE={attention_candidate}",
                                    f"-GATTENTION_PARALLEL_HEADS={attention_heads}",
                                    *(str(ROOT / path) for path in RTL),
                                ],
                                cwd=ROOT,
                                text=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                check=False,
                            )
                            if lint.returncode:
                                self.fail(f"model {model_id}, timing {timing_candidate}, attention "
                                          f"{attention_candidate}, heads {attention_heads} top lint failed:\n" +
                                          "\n".join(lint.stdout.splitlines()[-120:]))

    def test_huginn_192_channel_top_elaborates(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")
        lint = subprocess.run(
            [
                str(VERILATOR), "--lint-only", "--timing", "-Wno-fatal",
                "--top-module", "rtwsr_transformer_top", "-GMODEL_ID=0",
                "-GLINEAR_CHANNELS=192", "-GHBM_PARALLEL_LOAD=1'b1",
                "-GCORE_TIMING_CANDIDATE=1'b1", "-GCORE_128TRIT_CANDIDATE=1'b1",
                "-GPOOL_READ_PARALLEL_SLOTS=1'b1", "-GGAMMA_PARALLEL_LOAD=1'b1",
                "-GADAPTER_STATIC_REUSE=1'b1",
                "-GRESIDUAL_NORM_FUSION=1'b1", "-GRESIDUAL_NORM_TILE_PRELOAD=1'b1",
                "-GATTENTION_PARALLEL_CANDIDATE=1'b1", "-GATTENTION_PARALLEL_HEADS=8",
                *(str(ROOT / path) for path in RTL),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if lint.returncode:
            self.fail("192-channel Huginn top lint failed:\n" +
                      "\n".join(lint.stdout.splitlines()[-160:]))


if __name__ == "__main__":
    unittest.main()
