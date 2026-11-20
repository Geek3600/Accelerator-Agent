import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6SwigluResidualUnitTests(unittest.TestCase):
    def test_full_intermediate_sizes_for_three_models(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        for vector_len in (17920, 5632, 7168):
            for stream_fused in (0, 1):
                with self.subTest(vector_len=vector_len, stream_fused=stream_fused), tempfile.TemporaryDirectory(
                    prefix=f"loopquant_plan6_swiglu_{vector_len}_{stream_fused}_"
                ) as temp_name:
                    build_dir = Path(temp_name) / "obj_dir"
                    build = subprocess.run(
                        [
                            str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "4",
                            "--top-module", "tb_rtwsr_swiglu_residual_unit", "--Mdir", str(build_dir),
                            f"-GVECTOR_LEN={vector_len}", f"-GSTREAM_FUSED={stream_fused}",
                            str(ROOT / "hardware/rtwsr_swiglu_residual_unit.sv"),
                            str(ROOT / "hardware/tests/tb_rtwsr_swiglu_residual_unit.sv"),
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
                        [str(build_dir / "Vtb_rtwsr_swiglu_residual_unit")],
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                        timeout=600,
                    )
                    if simulation.returncode:
                        self.fail("full intermediate-size SwiGLU regression failed:\n" +
                                  "\n".join(simulation.stdout.splitlines()[-120:]))
                    self.assertIn(f"VECTOR_LEN={vector_len}", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
