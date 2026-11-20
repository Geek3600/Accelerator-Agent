import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6DualTrackGemvArrayTests(unittest.TestCase):
    def run_full_huginn_ffn_case(self, trits_per_cycle, channels_per_slr=32):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_gemv_width_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                    "--top-module", "tb_rtwsr_dual_track_gemv_array", "--Mdir", str(build_dir),
                    "-GK=17920",
                    f"-GCHANNELS_PER_SLR={channels_per_slr}",
                    f"-GTRITS_PER_CYCLE={trits_per_cycle}",
                    str(ROOT / "hardware/radix3_5trit_decoder.sv"),
                    str(ROOT / "hardware/scale_hoisted_ternary_lane.sv"),
                    str(ROOT / "hardware/usw512_word_decoder.sv"),
                    str(ROOT / "hardware/usw512_dual_track_channel.sv"),
                    str(ROOT / "hardware/usw512_channel_array.sv"),
                    str(ROOT / "hardware/rtwsr_dual_track_gemv_array.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_dual_track_gemv_array.sv"),
                ],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if build.returncode:
                self.fail("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-80:]))

            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_dual_track_gemv_array")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=600,
            )
            if simulation.returncode:
                self.fail(f"{3 * channels_per_slr}-channel full-width RTL regression failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-80:]))
            self.assertIn(
                f"full K=17920, 3 SLR x {channels_per_slr} channels, {trits_per_cycle} trits/cycle",
                simulation.stdout,
            )

    def test_full_huginn_ffn_input_width_on_all_96_channels(self):
        self.run_full_huginn_ffn_case(64)

    def test_full_huginn_ffn_input_width_with_128_trits_per_cycle(self):
        self.run_full_huginn_ffn_case(128)

    def test_192_output_channels_full_huginn_ffn_input_width(self):
        self.run_full_huginn_ffn_case(128, 64)


if __name__ == "__main__":
    unittest.main()
