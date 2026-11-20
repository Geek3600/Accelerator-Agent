import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class Plan6ExternalKvStreamTests(unittest.TestCase):
    def test_external_history_and_current_rope_kv_share_one_stream(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_external_kv_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    "/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                    "--build-jobs", "2", "--top-module", "tb_rtwsr_external_kv_stream",
                    "--Mdir", str(build_dir),
                    str(ROOT / "hardware/rtwsr_rope_kv_cache.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_external_kv_stream.sv"),
                ],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-120:]))
            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_external_kv_stream")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
                check=False,
            )
            self.assertEqual(simulation.returncode, 0, simulation.stdout)
            self.assertIn("PASS external KV stream", simulation.stdout)
            print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
