import subprocess
import tempfile
import unittest
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6HuginnFfnPipelineTests(unittest.TestCase):
    def test_full_huginn_ffn_projection_to_down_activation_path(self):
        outputs = {}
        for stream_fused, gemv_stream_fused in ((0, 0), (1, 0), (1, 1)):
            with self.subTest(stream_fused=stream_fused, gemv_stream_fused=gemv_stream_fused), tempfile.TemporaryDirectory(
                prefix=f"loopquant_plan6_huginn_ffn_{stream_fused}_{gemv_stream_fused}_"
            ) as directory:
                build_dir = Path(directory) / "obj_dir"
                build = subprocess.run(
                    [
                        str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "2",
                        "--top-module", "tb_rtwsr_huginn_ffn_pipeline", "--Mdir", str(build_dir),
                        f"-GSTREAM_FUSED={stream_fused}",
                        f"-GGEMV_STREAM_FUSED={gemv_stream_fused}",
                        str(ROOT / "hardware/rtwsr_huginn_ffn_pipeline.sv"),
                        str(ROOT / "hardware/rtwsr_swiglu_residual_unit.sv"),
                        str(ROOT / "hardware/tests/tb_rtwsr_huginn_ffn_pipeline.sv"),
                    ],
                    cwd=directory,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_huginn_ffn_pipeline")],
                    cwd=directory,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=3600,
                )
                self.assertEqual(simulation.returncode, 0, simulation.stdout)
                self.assertIn("PASS Huginn FFN rows=17920 chunks=1120 nonzero=17920", simulation.stdout)
                scale = re.search(r"scale=([0-9a-fA-F]+)", simulation.stdout)
                digest = re.search(r"FFN activation digest=([0-9a-fA-F]+)", simulation.stdout)
                window_digests = re.findall(r"FFN window=(\d+) digest=([0-9a-fA-F]+)", simulation.stdout)
                self.assertIsNotNone(scale, simulation.stdout)
                self.assertIsNotNone(digest, simulation.stdout)
                self.assertEqual(len(window_digests), 70, simulation.stdout)
                outputs[(stream_fused, gemv_stream_fused)] = (
                    scale.group(1), digest.group(1), tuple(window_digests)
                )
                print(
                    f"STREAM_FUSED={stream_fused} GEMV_STREAM_FUSED={gemv_stream_fused} "
                    f"{simulation.stdout}", end=""
                )
        reference = outputs[(0, 0)]
        for config, output in outputs.items():
            self.assertEqual(output, reference, f"activation output mismatch for {config}")


if __name__ == "__main__":
    unittest.main()
