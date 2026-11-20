import subprocess
import tempfile
import unittest
from pathlib import Path

from hardware.plan6_models import PLAN6_MODELS


ROOT = Path(__file__).resolve().parents[2]
VERILATOR = Path("/usr/bin/verilator")


class Plan6ModelScheduleTests(unittest.TestCase):
    def test_full_recurrent_schedules_for_all_models(self):
        if not VERILATOR.is_file():
            self.fail(f"Verilator is required at {VERILATOR}")

        parameter_names = {
            "hidden_size": "HIDDEN_SIZE",
            "intermediate_size": "INTERMEDIATE_SIZE",
            "query_size": "QUERY_SIZE",
            "kv_size": "KV_SIZE",
            "head_dim": "HEAD_DIM",
            "attention_gate_rows": "ATTENTION_GATE_ROWS",
            "has_pre_attention_norm": "HAS_PRE_ATTENTION_NORM",
            "has_pre_ffn_norm": "HAS_PRE_FFN_NORM",
            "core_blocks": "CORE_BLOCKS",
            "recurrences": "RECURRENCES",
            "pre_stage": "PRE_RECURRENCE_STAGE",
            "pre_rows": "PRE_STAGE_ROWS",
            "pre_columns": "PRE_STAGE_COLUMNS",
            "pre_vector_length": "PRE_STAGE_VECTOR_LENGTH",
            "post_stage": "POST_RECURRENCE_STAGE",
            "full_attention_mask": "FULL_ATTENTION_MASK",
            "sliding_window": "SLIDING_WINDOW",
        }

        for model_name, model in PLAN6_MODELS.items():
            with self.subTest(model=model_name), tempfile.TemporaryDirectory(
                prefix=f"loopquant_plan6_{model_name}_"
            ) as temp_name:
                build_dir = Path(temp_name) / "obj_dir"
                command = [
                    str(VERILATOR), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
                    "--top-module", "tb_rtwsr_recurrent_sequencer",
                    "--Mdir", str(build_dir),
                    str(ROOT / "hardware/rtwsr_recurrent_sequencer.sv"),
                    str(ROOT / "hardware/tests/tb_rtwsr_recurrent_sequencer.sv"),
                ]
                for key, parameter_name in parameter_names.items():
                    value = model[key]
                    if isinstance(value, bool):
                        value = int(value)
                    command.append(f"-G{parameter_name}={value}")
                build = subprocess.run(
                    command, cwd=temp_name, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, check=False,
                )
                if build.returncode:
                    self.fail(
                        f"{model_name} Verilator build failed:\n" +
                        "\n".join(build.stdout.splitlines()[-80:])
                    )

                simulation = subprocess.run(
                    [str(build_dir / "Vtb_rtwsr_recurrent_sequencer")],
                    cwd=temp_name, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, check=False,
                )
                if simulation.returncode:
                    self.fail(
                        f"{model_name} schedule simulation failed:\n" +
                        "\n".join(simulation.stdout.splitlines()[-80:])
                    )
                self.assertIn("PASS: recurrent schedule", simulation.stdout)


if __name__ == "__main__":
    unittest.main()
