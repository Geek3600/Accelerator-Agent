import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
class Plan6QKVHeadBufferTests(unittest.TestCase):
    def test_full_model_qkv_dimensions_and_head_reads(self):
        for variant in ("rtwsr_qkv_head_buffer.sv", "rtwsr_qkv_head_buffer_timing_candidate.sv"):
            self.check_variant(variant)

    def test_huginn_four_port_parallel_read_per_value(self):
        for parallel_ports in (4, 8):
            with tempfile.TemporaryDirectory(prefix=f"loopquant_plan6_qkv_parallel{parallel_ports}_") as directory:
                build_dir = Path(directory) / "obj_dir"
                build = subprocess.run(
                    ["/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                     "--build-jobs", "4", "--top-module", "tb_rtwsr_qkv_head_buffer_parallel",
                     f"-GPARALLEL_READ_PORTS={parallel_ports}", "--Mdir", str(build_dir),
                     str(ROOT / "hardware/rtwsr_qkv_head_buffer.sv"),
                     str(ROOT / "hardware/rtwsr_qkv_head_buffer_banked.sv"),
                     str(ROOT / "hardware/tests/tb_rtwsr_qkv_head_buffer_parallel.sv")],
                    cwd=directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, check=False,
                )
                self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_qkv_head_buffer_parallel")],
                    cwd=directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=3600, check=False,
                )
                self.assertEqual(simulation.returncode, 0, simulation.stdout)
                self.assertIn("PASS Huginn QKV per-value regression", simulation.stdout)
                print(simulation.stdout, end="")

    def test_huginn_parallel_attention_full_head_regression(self):
        for parallel_heads in (2, 4, 8):
            with tempfile.TemporaryDirectory(prefix=f"loopquant_plan6_attn_parallel{parallel_heads}_") as directory:
                build_dir = Path(directory) / "obj_dir"
                rtl = [
                    "rtwsr_qkv_head_buffer.sv",
                    "rtwsr_qkv_head_buffer_banked.sv",
                    "candidates/resource_opt/rtl_integrated/rtwsr_recurrent_attention_bridge.sv",
                    "candidates/resource_opt/rtl_integrated/rtwsr_recurrent_attention_bridge4.sv",
                    "rtwsr_rope_kv_cache.sv",
                    "rtwsr_attention_gemv_unit.sv",
                ]
                build = subprocess.run(
                    ["/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                     "--build-jobs", "2", "--top-module", "tb_rtwsr_attention_parallel4_e2e",
                     f"-GPARALLEL_HEADS={parallel_heads}", "--Mdir", str(build_dir),
                     *(str((ROOT / "hardware" / source).resolve()) for source in rtl),
                     str(ROOT / "hardware/tests/tb_rtwsr_attention_parallel4_e2e.sv")],
                    cwd=directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, check=False,
                )
                self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_attention_parallel4_e2e")],
                    cwd=directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=3600, check=False,
                )
                self.assertEqual(simulation.returncode, 0, simulation.stdout)
                self.assertIn("PASS Huginn attention full-head regression", simulation.stdout)
                print(simulation.stdout, end="")

    def check_variant(self, variant):
        for model_id in (0, 1, 2):
            with self.subTest(variant=variant, model_id=model_id), tempfile.TemporaryDirectory(
                prefix=f"loopquant_plan6_qkv_{model_id}_"
            ) as directory:
                build_dir = Path(directory) / "obj_dir"
                build = subprocess.run(
                    ["/usr/bin/verilator", "--binary", "--timing", "-Wno-fatal",
                     "--build-jobs", "2", "--top-module", "tb_rtwsr_qkv_head_buffer",
                     f"-GMODEL_ID={model_id}", "--Mdir", str(build_dir),
                     str(ROOT / "hardware" / variant),
                     str(ROOT / "hardware/tests/tb_rtwsr_qkv_head_buffer.sv")],
                    cwd=directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, check=False,
                )
                self.assertEqual(build.returncode, 0, "\n".join(build.stdout.splitlines()[-100:]))
                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_qkv_head_buffer")],
                    cwd=directory, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, timeout=3600, check=False,
                )
                self.assertEqual(simulation.returncode, 0, simulation.stdout)
                self.assertIn(f"PASS QKV buffer model={model_id}", simulation.stdout)
                print(simulation.stdout, end="")


if __name__ == "__main__":
    unittest.main()
