import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6CoreLinearIntegrationTests(unittest.TestCase):
    def test_full_recurrent_core_schedules_reach_shared_tiled_engine(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        expected = {
            0: "commands=1696",
            1: "commands=1444",
            2: "commands=1208",
        }
        for model_id, summary in expected.items():
            with self.subTest(model_id=model_id), tempfile.TemporaryDirectory(
                prefix=f"loopquant_plan6_core_linear_{model_id}_"
            ) as temp_name:
                build_dir = Path(temp_name) / "obj_dir"
                build = subprocess.run(
                    [
                        str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                        "--top-module", "tb_rtwsr_plan6_core_linear_integration",
                        "--Mdir", str(build_dir), f"-GMODEL_ID={model_id}",
                        str(ROOT / "hardware/rtwsr_recurrent_sequencer.sv"),
                        str(ROOT / "hardware/rtwsr_recurrent_command_scheduler.sv"),
                        str(ROOT / "hardware/rtwsr_linear_command_dispatch.sv"),
                        str(ROOT / "hardware/rtwsr_linear_tile_controller.sv"),
                        str(ROOT / "hardware/tests/tb_rtwsr_plan6_core_linear_integration.sv"),
                    ],
                    cwd=temp_name,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if build.returncode:
                    self.fail(
                        f"model {model_id} integration build failed:\n" +
                        "\n".join(build.stdout.splitlines()[-100:])
                    )

                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_plan6_core_linear_integration")],
                    cwd=temp_name,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if simulation.returncode:
                    self.fail(
                        f"model {model_id} full-core descriptor simulation failed:\n" +
                        "\n".join(simulation.stdout.splitlines()[-100:])
                    )
                self.assertIn(summary, simulation.stdout)
                self.assertIn("max_pool_words=", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
