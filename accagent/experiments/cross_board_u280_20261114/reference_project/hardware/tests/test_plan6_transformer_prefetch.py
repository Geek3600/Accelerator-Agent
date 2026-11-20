import subprocess
import tempfile
import unittest
from pathlib import Path

from test_plan6_transformer_top_lint import ROOT, RTL


class Plan6TransformerPrefetchTests(unittest.TestCase):
    def test_full_huginn_adapter_to_qkv_with_background_prefetch(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_top_prefetch_") as directory:
            build_dir = Path(directory) / "obj_dir"
            build = subprocess.run(
                ["/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                 "--build-jobs", "2", "--top-module", "tb_rtwsr_transformer_prefetch",
                 "--Mdir", str(build_dir), *(str(ROOT / source) for source in RTL),
                 str(ROOT / "hardware/tests/tb_rtwsr_transformer_prefetch.sv")],
                cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_transformer_prefetch")],
                cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=3600,
            )
            self.assertEqual(simulation.returncode, 0, simulation.stdout)
            self.assertIn("PASS internal adapter-norm-qkv rows=21120 tiles=220 norm_chunks=330", simulation.stdout)
            self.assertIn("PASS top propagates RoPE/KV protocol error", simulation.stdout)
            print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
