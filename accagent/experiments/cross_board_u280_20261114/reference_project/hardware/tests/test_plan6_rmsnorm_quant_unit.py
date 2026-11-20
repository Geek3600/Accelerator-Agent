import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RmsnormQuantUnitTests(unittest.TestCase):
    def test_full_hidden_sizes_for_three_models(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        for vector_len in (5280, 2048, 2560, 4096, 7168):
            for parallel_quantize in (0, 1):
                with self.subTest(vector_len=vector_len, parallel_quantize=parallel_quantize), \
                        tempfile.TemporaryDirectory(
                            prefix=f"loopquant_plan6_rmsnorm_{vector_len}_{parallel_quantize}_"
                        ) as temp_name:
                    build_dir = Path(temp_name) / "obj_dir"
                    build = subprocess.run(
                        [
                            str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "4",
                            "--top-module", "tb_rtwsr_rmsnorm_quant_unit", "--Mdir", str(build_dir),
                            f"-GVECTOR_LEN={vector_len}", f"-GPARALLEL_QUANTIZE={parallel_quantize}",
                            "-GMAX_VECTOR_LEN=7168",
                            str(ROOT / "hardware/rtwsr_rmsnorm_quant_unit.sv"),
                            str(ROOT / "hardware/tests/tb_rtwsr_rmsnorm_quant_unit.sv"),
                        ],
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
                    if build.returncode:
                        self.fail("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-120:]))

                    simulation = subprocess.run(
                        [str(build_dir / "Vtb_rtwsr_rmsnorm_quant_unit")],
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                        timeout=600,
                    )
                    if simulation.returncode:
                        self.fail("full hidden-size RMSNorm regression failed:\n" +
                                  "\n".join(simulation.stdout.splitlines()[-120:]))
                    self.assertIn(f"VECTOR_LEN={vector_len}", simulation.stdout)
                    print(f"PARALLEL_QUANTIZE={parallel_quantize} {simulation.stdout}", end="")


if __name__ == "__main__":
    unittest.main()
