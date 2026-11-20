import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / "hardware"
VERILATOR = Path("/usr/bin/verilator")
PAYLOAD = ROOT / "results/plan6/huginn_recurrent_core/rmsnorm.q4_12"
CONVERTER = RTL / "prepare_plan6_rmsnorm_q412.py"
SOURCES = [
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
]


class Plan6NormGammaDmaTest(unittest.TestCase):
    def test_full_q412_payload_load_and_address_regression(self):
        if not VERILATOR.is_file():
            self.skipTest(f"Verilator is not installed at {VERILATOR}")

        subprocess.run([sys.executable, str(CONVERTER)], check=True, cwd=ROOT)
        values = np.fromfile(PAYLOAD, dtype="<i2")
        self.assertEqual(values.size, 4 * 4 * 5280)
        self.assertEqual(PAYLOAD.stat().st_size, 168960)

        with tempfile.TemporaryDirectory(prefix="plan6_norm_gamma_dma_") as temp_name:
            temp_dir = Path(temp_name)
            memory_file = temp_dir / "rmsnorm_q412.mem"
            with memory_file.open("w") as stream:
                for value in values.view("<u2"):
                    stream.write(f"{int(value):04x}\n")

            executable = temp_dir / "tb_norm_gamma_dma"
            build_dir = temp_dir / "obj"
            sources = [str(RTL / source) for source in SOURCES]
            sources.append(str(RTL / "tests/tb_rtwsr_norm_gamma_dma.sv"))
            compile_result = subprocess.run(
                [
                    str(VERILATOR),
                    "--binary",
                    "--timing",
                    "-Wno-fatal",
                    "--top-module",
                    "tb_rtwsr_norm_gamma_dma",
                    "--Mdir",
                    str(build_dir),
                    "-o",
                    str(executable),
                    *sources,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=600,
            )
            self.assertEqual(
                compile_result.returncode,
                0,
                compile_result.stdout + compile_result.stderr,
            )
            simulation_result = subprocess.run(
                [str(executable)],
                check=False,
                capture_output=True,
                text=True,
                cwd=temp_dir,
                timeout=180,
            )
            self.assertEqual(
                simulation_result.returncode,
                0,
                simulation_result.stdout + simulation_result.stderr,
            )
            self.assertRegex(
                simulation_result.stdout,
                r"NORM_GAMMA_DMA_PASS cycles=[1-9][0-9]* bytes=168960 words=2640 tiles=880 bursts=42 address_checks=6160",
            )
            print(simulation_result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
