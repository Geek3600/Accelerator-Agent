import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RuntimeGammaPoolTests(unittest.TestCase):
    def test_full_model_gamma_tiles_and_overlapped_prefetch(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_gamma_pool_") as temp_name:
            for channels in (96, 192):
                huginn_tiles = (17920 + channels - 1) // channels
                dory_tiles = (7168 + channels - 1) // channels
                ouro_tiles = (5632 + channels - 1) // channels
                for parallel_load in (0, 1):
                    build_dir = Path(temp_name) / f"obj_dir_{channels}_{parallel_load}"
                    build_command = [
                        str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                        "--top-module", "tb_rtwsr_runtime_gamma_pool", "--Mdir", str(build_dir),
                        f"-GCHANNELS={channels}",
                        f"-GPARALLEL_LOAD={parallel_load}",
                        str(ROOT / "hardware/rtwsr_runtime_gamma_pool.sv"),
                        str(ROOT / "hardware/tests/tb_rtwsr_runtime_gamma_pool.sv"),
                    ]
                    build = subprocess.run(
                        build_command,
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
                    if build.returncode:
                        self.fail("Verilator build failed:\n" +
                                  "\n".join(build.stdout.splitlines()[-100:]))

                    simulation = subprocess.run(
                        [str(build_dir / "Vtb_rtwsr_runtime_gamma_pool")],
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                        timeout=600,
                    )
                    if simulation.returncode:
                        self.fail("full-model Gamma simulation failed:\n" +
                                  "\n".join(simulation.stdout.splitlines()[-100:]))
                    self.assertIn(
                        f"Huginn {huginn_tiles} tiles, Dory {dory_tiles} tiles, Ouro {ouro_tiles} tiles",
                        simulation.stdout,
                    )
                    self.assertIn(f"parallel_load={parallel_load}", simulation.stdout)
                    print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
