import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RoundDividerTests(unittest.TestCase):
    def test_full_signed_activation_range_matches_rounded_division(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_round_divider_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "4",
                    "--top-module", "tb_rtwsr_round_divider_7bit", "--Mdir", str(build_dir),
                    str(ROOT / "hardware/rtwsr_round_divider_7bit.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_round_divider_7bit.sv"),
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
                [str(build_dir / "Vtb_rtwsr_round_divider_7bit")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=60,
            )
            if simulation.returncode:
                self.fail("rounded divider regression failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-100:]))
            self.assertIn("ROUND_DIVIDER_7BIT_VECTOR_PASS fast=0 vector_length=5280 vectors=128", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
