import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6LinearTileControllerTests(unittest.TestCase):
    def run_all_model_matrix_dimensions(self, channels):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_linear_tiles_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                    "--top-module", "tb_rtwsr_linear_tile_controller", "--Mdir", str(build_dir),
                    f"-GCHANNELS={channels}",
                    str(ROOT / "hardware/rtwsr_linear_tile_controller.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_linear_tile_controller.sv"),
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
                [str(build_dir / "Vtb_rtwsr_linear_tile_controller")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if simulation.returncode:
                self.fail(f"shared {channels}-channel tiling failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-80:]))
            self.assertIn(f"PASS: shared {channels}-channel matrix tiling", simulation.stdout)

    def test_all_model_matrix_dimensions_tile_over_shared_96_channels(self):
        self.run_all_model_matrix_dimensions(96)

    def test_all_model_matrix_dimensions_tile_over_shared_192_channels(self):
        self.run_all_model_matrix_dimensions(192)


if __name__ == "__main__":
    unittest.main()
