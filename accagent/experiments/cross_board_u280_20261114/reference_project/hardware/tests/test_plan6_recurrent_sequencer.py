import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RecurrentSequencerTests(unittest.TestCase):
    def test_full_huginn_schedule_for_both_context_lengths(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_seq_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            command = [
                str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                "--top-module", "tb_rtwsr_huginn_recurrent_sequencer",
                "--Mdir", str(build_dir),
                str(ROOT / "hardware/rtwsr_huginn_recurrent_sequencer.sv"),
                str(ROOT / "hardware/tests/tb_rtwsr_huginn_recurrent_sequencer.sv"),
            ]
            build = subprocess.run(
                command, cwd=temp_name, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
            )
            if build.returncode:
                self.fail("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-60:]))

            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_huginn_recurrent_sequencer")],
                cwd=temp_name, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, check=False,
            )
            if simulation.returncode:
                self.fail("full schedule simulation failed:\n" + "\n".join(simulation.stdout.splitlines()[-60:]))
            self.assertIn(
                "PASS: Huginn recurrent schedule, 1312 stages at context 512 and 2048",
                simulation.stdout,
            )


if __name__ == "__main__":
    unittest.main()
