import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class Plan6RuntimeWeightOverlapTests(unittest.TestCase):
    def test_full_model_matrices_preserve_live_tiles_during_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_overlap_") as directory:
            build_dir = Path(directory) / "obj_dir"
            sources = (
                "uram_active_pool_bank.sv",
                "rtwsr_runtime_weight_ring.sv",
                "rtwsr_runtime_weight_pool.sv",
                "rtwsr_runtime_weight_subsystem.sv",
                "tests/tb_rtwsr_runtime_weight_overlap.sv",
            )
            build = subprocess.run(
                ["/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                 "--build-jobs", "2", "--top-module", "tb_rtwsr_runtime_weight_overlap",
                 "--Mdir", str(build_dir),
                 *(str(ROOT / "hardware" / source) for source in sources)],
                cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_runtime_weight_overlap")],
                cwd=directory, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=3600,
            )
            self.assertEqual(simulation.returncode, 0, simulation.stdout)
            self.assertEqual(simulation.stdout.count("PASS overwrite"), 4, simulation.stdout)
            self.assertIn("PASS full-shape overlap checked_records=1725312", simulation.stdout)
            print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
