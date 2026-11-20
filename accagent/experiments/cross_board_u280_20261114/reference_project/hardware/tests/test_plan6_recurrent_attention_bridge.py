import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class Plan6RecurrentAttentionBridgeTests(unittest.TestCase):
    def test_multichunk_qkv_heads_run_through_rope_and_attention(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_attention_bridge_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    "/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                    "--build-jobs", "2", "--top-module", "tb_rtwsr_recurrent_attention_bridge",
                    "--Mdir", str(build_dir),
                    str(ROOT / "hardware/rtwsr_recurrent_attention_bridge.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_recurrent_attention_bridge.sv"),
                ],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-120:]))
            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_recurrent_attention_bridge")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=60,
                check=False,
            )
            self.assertEqual(simulation.returncode, 0, simulation.stdout)
            self.assertIn("PASS QKV-to-attention bridge", simulation.stdout)
            print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
