import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RuntimeWeightPoolTests(unittest.TestCase):
    def test_full_huginn_ffn_runtime_weight_load_and_readback(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_runtime_pool_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "2",
                    "--top-module", "tb_rtwsr_runtime_weight_pool", "--Mdir", str(build_dir),
                    str(ROOT / "hardware/uram_active_pool_bank.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_pool.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_runtime_weight_pool.sv"),
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
                [str(build_dir / "Vtb_rtwsr_runtime_weight_pool")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=3600,
            )
            if simulation.returncode:
                self.fail("full runtime weight-pool regression failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-100:]))
            self.assertIn("loaded and read back 376320 records", simulation.stdout)
            self.assertIn("words_per_port=15708", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
