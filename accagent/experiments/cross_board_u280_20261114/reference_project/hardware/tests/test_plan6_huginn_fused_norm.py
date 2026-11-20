import subprocess
import tempfile
import unittest
from pathlib import Path

from test_plan6_transformer_top_lint import ROOT, RTL


class HuginnFusedNormTests(unittest.TestCase):
    def test_full_huginn_residual_writeback_and_norm(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_huginn_fused_norm_") as directory:
            build_dir = Path(directory) / "obj_dir"
            build = subprocess.run(
                ["/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                 "--build-jobs", "2", "--top-module", "tb_rtwsr_huginn_fused_norm",
                 "--Mdir", str(build_dir), *(str(ROOT / source) for source in RTL),
                 str(ROOT / "hardware/tests/tb_rtwsr_huginn_fused_norm.sv")],
                cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_huginn_fused_norm")],
                cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=600,
            )
            self.assertEqual(simulation.returncode, 0, simulation.stdout)
            self.assertIn("PASS full Huginn fused Norm command=10", simulation.stdout)
            self.assertIn("PASS full Huginn fused Norm command=16", simulation.stdout)
            print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
