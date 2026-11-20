import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6LinearCommandDispatchTests(unittest.TestCase):
    def test_matrix_commands_share_one_engine_handshake(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_linear_dispatch_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                    "--top-module", "tb_rtwsr_linear_command_dispatch", "--Mdir", str(build_dir),
                    str(ROOT / "hardware/rtwsr_linear_command_dispatch.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_linear_command_dispatch.sv"),
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
                [str(build_dir / "Vtb_rtwsr_linear_command_dispatch")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if simulation.returncode:
                self.fail("shared engine dispatch failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-80:]))
            self.assertIn("PASS: shared linear engine routes", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
