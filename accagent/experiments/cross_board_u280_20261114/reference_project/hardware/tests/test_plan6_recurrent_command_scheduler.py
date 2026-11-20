import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RecurrentCommandSchedulerTests(unittest.TestCase):
    def test_full_command_schedules_for_all_models(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        expected = {
            0: "stages=1312 commands=1696",
            1: "stages=964 commands=1444",
            2: "stages=648 commands=1208",
        }
        for model_id, counts in expected.items():
            with self.subTest(model_id=model_id), tempfile.TemporaryDirectory(
                prefix=f"loopquant_plan6_commands_{model_id}_"
            ) as temp_name:
                build_dir = Path(temp_name) / "obj_dir"
                build = subprocess.run(
                    [
                        str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                        "--top-module", "tb_rtwsr_recurrent_command_scheduler",
                        "--Mdir", str(build_dir), "-GMODEL_ID=" + str(model_id),
                        str(ROOT / "hardware/rtwsr_recurrent_sequencer.sv"),
                        str(ROOT / "hardware/rtwsr_recurrent_command_scheduler.sv"),
                        str(ROOT / "hardware/rtwsr_linear_command_dispatch.sv"),
                        str(ROOT / "hardware/tests/tb_rtwsr_recurrent_command_scheduler.sv"),
                    ],
                    cwd=temp_name,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if build.returncode:
                    self.fail(
                        f"model {model_id} Verilator build failed:\n" +
                        "\n".join(build.stdout.splitlines()[-80:])
                    )

                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_recurrent_command_scheduler")],
                    cwd=temp_name,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if simulation.returncode:
                    self.fail(
                        f"model {model_id} full command simulation failed:\n" +
                        "\n".join(simulation.stdout.splitlines()[-80:])
                    )
                self.assertIn(counts, simulation.stdout)


if __name__ == "__main__":
    unittest.main()
