import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RopeKvCacheTests(unittest.TestCase):
    def test_full_context_rope_and_kv_stream_for_all_head_dimensions(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        for head_dim in (96, 128, 256):
            with self.subTest(head_dim=head_dim), tempfile.TemporaryDirectory(
                prefix=f"loopquant_plan6_rope_kv_{head_dim}_"
            ) as temp_name:
                build_dir = Path(temp_name) / "obj_dir"
                build = subprocess.run(
                    [
                        str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "4",
                        "--top-module", "tb_rtwsr_rope_kv_cache", "--Mdir", str(build_dir),
                        f"-GHEAD_DIM={head_dim}", "-GMAX_CONTEXT=2048",
                        str(ROOT / "hardware/rtwsr_rope_kv_cache.sv"),
                        str(ROOT / "hardware/tests/tb_rtwsr_rope_kv_cache.sv"),
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
                    [str(build_dir / "Vtb_rtwsr_rope_kv_cache")],
                    cwd=temp_name,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=600,
                )
                if simulation.returncode:
                    self.fail("full-context RoPE/KV regression failed:\n" +
                              "\n".join(simulation.stdout.splitlines()[-120:]))
                self.assertIn(
                    f"HEAD_DIM={head_dim} context=2048",
                    simulation.stdout,
                )


if __name__ == "__main__":
    unittest.main()
