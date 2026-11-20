import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6HbmPoolPathTests(unittest.TestCase):
    def run_pool_path(self, channels, read_parallel_slots, pool_lanes=24):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_hbm_pool_path_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                    "--top-module", "tb_rtwsr_hbm_pool_path", "--Mdir", str(build_dir),
                    f"-GCHANNELS={channels}",
                    f"-GREAD_PARALLEL_SLOTS={int(read_parallel_slots)}",
                    f"-GPOOL_LANES={pool_lanes}",
                    str(ROOT / "hardware/uram_active_pool_bank.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_pool.sv"),
                    str(ROOT / "hardware/candidates/u280_hbm/rtwsr_hbm_weight_pool_adapter_27to24.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_hbm_pool_path.sv"),
                ],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if build.returncode:
                self.fail("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-100:]))

            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_hbm_pool_path")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=3600,
            )
            if simulation.returncode:
                self.fail("HBM pool path regression failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-100:]))
            expected_groups = 187 * 21 * (96 // pool_lanes)
            self.assertIn(
                f"PASS: full Huginn down-proj 32-PC stream loaded and read back {expected_groups} groups for {channels} channels at {pool_lanes} pool lanes",
                simulation.stdout,
            )
            print(simulation.stdout, end="")

    def test_96_channel_parallel_hbm_pool_path(self):
        self.run_pool_path(96, False)

    def test_192_channel_parallel_hbm_pool_path(self):
        self.run_pool_path(192, True)

    def test_96_channel_32_lane_parallel_hbm_pool_path(self):
        self.run_pool_path(96, True, 32)

    def test_192_channel_32_lane_parallel_hbm_pool_path(self):
        self.run_pool_path(192, True, 32)


if __name__ == "__main__":
    unittest.main()
