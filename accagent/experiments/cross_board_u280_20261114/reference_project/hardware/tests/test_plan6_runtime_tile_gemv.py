import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6RuntimeTileGemvTests(unittest.TestCase):
    def run_full_shape_regression(self, trits_per_cycle, read_parallel_slots, channels=96,
                                  adapter_cache_test=False):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        with tempfile.TemporaryDirectory(prefix="loopquant_plan6_runtime_gemv_") as temp_name:
            build_dir = Path(temp_name) / "obj_dir"
            build = subprocess.run(
                [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                    "--top-module", "tb_rtwsr_runtime_tile_gemv", "--Mdir", str(build_dir),
                    f"-GCHANNELS={channels}",
                    f"-GTRITS_PER_CYCLE={trits_per_cycle}",
                    f"-GREAD_PARALLEL_SLOTS={int(read_parallel_slots)}",
                    f"-GADAPTER_STATIC_REUSE={int(adapter_cache_test)}",
                    f"-GADAPTER_CACHE_TEST={int(adapter_cache_test)}",
                    str(ROOT / "hardware/uram_active_pool_bank.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_ring.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_pool.sv"),
                    str(ROOT / "hardware/rtwsr_runtime_weight_subsystem.sv"),
                    *(str(ROOT / "hardware" / name) for name in (
                        "radix3_5trit_decoder.sv", "scale_hoisted_ternary_lane.sv",
                        "usw512_word_decoder.sv", "usw512_dual_track_channel.sv",
                        "usw512_channel_array.sv", "rtwsr_dual_track_gemv_array.sv",
                        "rtwsr_adapter_static_cache.sv",
                        "rtwsr_runtime_tile_gemv.sv")),
                    str(ROOT / "hardware/tests/tb_rtwsr_runtime_tile_gemv.sv"),
                ],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if build.returncode:
                self.fail("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-100:]))

            simulation = subprocess.run(
                [str(build_dir / "Vtb_rtwsr_runtime_tile_gemv")],
                cwd=temp_name,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=3600,
            )
            if simulation.returncode:
                self.fail("runtime shadow and primary-pool regression failed:\n" +
                          "\n".join(simulation.stdout.splitlines()[-100:]))
            shapes = (
                (17920, 5280), (5280, 17920), (5280, 10560), (15840, 5280), (5280, 5280),
                (2048, 2048), (5632, 2048), (2048, 5632), (4096, 2560), (1024, 2560),
                (2560, 4096), (7168, 2560), (2560, 7168),
            )
            if adapter_cache_test:
                self.assertEqual(simulation.stdout.count("PASS full matrix 5280x10560"), 3)
                self.assertIn("adapter_cache_run=0", simulation.stdout)
                self.assertIn("adapter_cache_run=1", simulation.stdout)
                self.assertIn("adapter_cache_run=2", simulation.stdout)
            else:
                for rows, columns in shapes:
                    self.assertIn(
                        f"PASS full matrix {rows}x{columns}: tiles={(rows + channels - 1) // channels}",
                        simulation.stdout,
                    )
                self.assertIn("PASS sustained array throughput", simulation.stdout)
                self.assertIn("channels=%d valid rows=76736 tiles=%d" % (
                    channels, sum((rows + channels - 1) // channels for rows, _ in shapes)),
                    simulation.stdout)
            print(simulation.stdout, end="")

    def test_all_three_models_full_matrix_shapes_storage_to_arithmetic(self):
        self.run_full_shape_regression(64, False)

    def test_parallel_slot_reads_with_128_trit_array_full_matrix_shapes(self):
        self.run_full_shape_regression(128, True)

    def test_192_channel_128_trit_storage_to_array_full_matrix_shapes(self):
        self.run_full_shape_regression(128, True, channels=192)

    def test_192_channel_adapter_static_cache_full_matrix_reuse(self):
        self.run_full_shape_regression(128, True, channels=192, adapter_cache_test=True)


if __name__ == "__main__":
    unittest.main()
