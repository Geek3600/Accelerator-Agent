import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")
EXP_BASE_Q15 = (32768, 19875, 12055, 7312, 4435, 2690, 1631, 990,
                600, 364, 221, 134, 81, 49, 30, 18)
EXP_SLOPE_Q15 = (-12893, -7820, -4743, -2877, -1745, -1059, -641, -390,
                 -236, -143, -87, -53, -32, -19, -12, -7)


def exp_neg_q15(delta_q12):
    if delta_q12 <= 0:
        return 32768
    if delta_q12 >= 32768:
        return 0
    segment = delta_q12 >> 11
    fraction = delta_q12 & 0x7FF
    return EXP_BASE_Q15[segment] + ((EXP_SLOPE_Q15[segment] * fraction) >> 11)


def q_value(dimension):
    return (((dimension * 37 + 11) % 101) - 50) * 20


def k_value(token, dimension):
    return (((token * 29 + dimension * 13 + 7) % 67) - 33) * 12


def v_value(token, dimension):
    return (((token * 17 + dimension * 23 + 5) % 401) - 200) * 16


def reference_output(head_dim, context_length, attention_scale_q15):
    query = [q_value(dimension) for dimension in range(head_dim)]
    maximum = None
    denominator = 0
    accumulator = [0] * head_dim

    for token in range(context_length):
        dot = sum(query[d] * k_value(token, d) for d in range(head_dim))
        score_q12 = (dot * attention_scale_q15) >> 27
        if maximum is None:
            maximum = score_q12
            old_weight = 0
            current_weight = 32768
        else:
            next_maximum = max(maximum, score_q12)
            old_weight = exp_neg_q15(next_maximum - maximum)
            current_weight = exp_neg_q15(next_maximum - score_q12)
            maximum = next_maximum

        denominator = ((denominator * old_weight) >> 15) + current_weight
        for dimension in range(head_dim):
            accumulator[dimension] = (
                ((accumulator[dimension] * old_weight) >> 15)
                + v_value(token, dimension) * current_weight
            )

    reciprocal_q40 = (1 << 40) // denominator
    return [(value * reciprocal_q40) >> 40 for value in accumulator]


def write_expected(path, values):
    path.write_text("".join(f"{value & 0xFFFF:04x}\n" for value in values))


class Plan6AttentionGemvUnitTests(unittest.TestCase):
    def test_full_head_dimensions_and_contexts_match_integer_reference(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        model_heads = ((96, 3344), (128, 2896), (256, 2048))
        rtl_configs = (
            ("baseline", ROOT / "hardware/rtwsr_attention_gemv_unit.sv", 0, 0),
            ("fast_reciprocal", ROOT / "hardware/rtwsr_attention_gemv_unit.sv", 1, 0),
            ("timing_candidate", ROOT / "hardware/rtwsr_attention_gemv_unit_timing_candidate.sv", 0, 1),
            ("dsp_shared", ROOT / "hardware/candidates/resource_opt/rtwsr_attention_gemv_unit_dsp_shared.sv", 1, 0),
        )
        for head_dim, attention_scale in model_heads:
            for source_name, rtl_source, fast_reciprocal, use_timing_candidate in rtl_configs:
                with self.subTest(head_dim=head_dim, source=source_name), tempfile.TemporaryDirectory(
                    prefix=f"loopquant_plan6_attention_{head_dim}_{source_name}_"
                ) as temp_name:
                    temp_path = Path(temp_name)
                    build_dir = temp_path / "obj_dir"
                    write_expected(
                        temp_path / "expected_512.mem",
                        reference_output(head_dim, 512, attention_scale),
                    )
                    write_expected(
                        temp_path / "expected_2048.mem",
                        reference_output(head_dim, 2048, attention_scale),
                    )
                    build = subprocess.run(
                        [
                            str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "4",
                            "--top-module", "tb_rtwsr_attention_gemv_unit", "--Mdir", str(build_dir),
                            f"-GHEAD_DIM={head_dim}", f"-GATTN_SCALE_Q15={attention_scale}",
                            f"-GFAST_RECIPROCAL={fast_reciprocal}",
                            f"-GUSE_TIMING_CANDIDATE={use_timing_candidate}",
                            *(["-DRTWSR_USE_TIMING_CANDIDATE"] if use_timing_candidate else []),
                            str(rtl_source),
                            str(ROOT / "hardware/tests/tb_rtwsr_attention_gemv_unit.sv"),
                        ],
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
                    if build.returncode:
                        self.fail(f"Verilator build failed for {source_name}:\n" +
                                  "\n".join(build.stdout.splitlines()[-100:]))

                    simulation = subprocess.run(
                        [str(build_dir / "Vtb_rtwsr_attention_gemv_unit")],
                        cwd=temp_name,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        check=False,
                        timeout=600,
                    )
                    if simulation.returncode:
                        self.fail(f"full-context attention regression failed for {source_name}:\n" +
                                  "\n".join(simulation.stdout.splitlines()[-100:]))
                    self.assertIn(
                        f"HEAD_DIM={head_dim}, contexts=512/2048, 128 lanes",
                        simulation.stdout,
                    )
                    print(f"{source_name}: {simulation.stdout}", end="")


if __name__ == "__main__":
    unittest.main()
