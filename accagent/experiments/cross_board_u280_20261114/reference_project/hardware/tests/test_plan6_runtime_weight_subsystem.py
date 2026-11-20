import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RuntimeWeightSubsystemTests(unittest.TestCase):
    def test_shadow_fifo_and_runtime_pool_with_full_huginn_ffn(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_runtime_subsystem_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "2",
                    "--top-module", "tb_rtwsr_runtime_weight_subsystem", "--Mdir", str(build_dir),
                    str(ROOT / "hardware/uram_active_pool_bank.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_ring.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_pool.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_subsystem.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_runtime_weight_subsystem.sv"),
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
                [str(build_dir / "Vtb_rtwsr_runtime_weight_subsystem")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=3600,
            )
            if simulation.returncode:
                self.fail("runtime shadow and primary-pool regression failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-100:]))
            self.assertIn("drained 376320 records into 24 pool banks", simulation.stdout)
            self.assertIn("words_per_port=15708", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
