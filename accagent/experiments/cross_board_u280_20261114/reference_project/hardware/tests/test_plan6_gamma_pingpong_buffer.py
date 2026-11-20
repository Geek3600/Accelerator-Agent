import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6GammaPingPongBufferTests(unittest.TestCase):
    def test_two_full_capacity_gamma_banks(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_gamma_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "4",
                    "--top-module", "tb_rtwsr_gamma_pingpong_buffer", "--Mdir", str(build_dir),
                    "-GBANK_DEPTH=65536",
                    str(ROOT / "hardware/rtwsr_gamma_pingpong_buffer.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_gamma_pingpong_buffer.sv"),
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
                [str(build_dir / "Vtb_rtwsr_gamma_pingpong_buffer")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=600,
            )
            if simulation.returncode:
                self.fail("full-capacity Gamma buffer simulation failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-80:]))
            self.assertIn("two 65536-entry Gamma banks", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
