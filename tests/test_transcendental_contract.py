import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.transcendental_contract import (
    exp2_fraction_lut,
    exp_approximation,
    materialize_transcendental_contract,
)


class TranscendentalContractTest(TestCase):
    def test_materialized_tables_have_exhaustive_passing_error_bounds(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = materialize_transcendental_contract(Path(temp_dir))
            persisted = json.loads(Path(report["path"]).read_text(encoding="utf-8"))

            self.assertEqual(report["status"], "pass")
            self.assertEqual(persisted["contract_sha256"], report["contract_sha256"])
            self.assertEqual(
                persisted["exp_for_shifted_softmax"]["validation"]["acceptance_bound"]["status"],
                "pass",
            )
            self.assertEqual(
                persisted["sigmoid_and_silu"]["validation"]["acceptance_bound"]["status"],
                "pass",
            )
            self.assertLess(
                persisted["exp_for_shifted_softmax"]["validation"]["max_absolute_error"]["error"],
                0.001,
            )
            self.assertLess(
                persisted["sigmoid_and_silu"]["validation"]["max_silu_absolute_error"]["error"],
                0.005,
            )

    def test_exp_contract_clamps_only_outside_shifted_softmax_domain(self) -> None:
        fraction_bits = 11
        output_fraction_bits = 24
        table = exp2_fraction_lut(fraction_bits, output_fraction_bits)
        kwargs = {
            "input_fraction_bits": fraction_bits,
            "output_fraction_bits": output_fraction_bits,
            "log2e_fixed": round(math.log2(math.e) * (1 << fraction_bits)),
            "table": table,
            "minimum_input_fixed": -16 << fraction_bits,
        }

        self.assertEqual(exp_approximation(1, **kwargs), 1.0)
        self.assertEqual(exp_approximation(-17 << fraction_bits, **kwargs), 0.0)
        self.assertAlmostEqual(
            exp_approximation(-1 << fraction_bits, **kwargs),
            math.exp(-1.0),
            delta=0.001,
        )

    def test_table_files_match_declared_entry_counts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = materialize_transcendental_contract(Path(temp_dir))
            for section in ("exp_for_shifted_softmax", "sigmoid_and_silu"):
                table = report[section]["table"]
                lines = Path(table["path"]).read_text(encoding="ascii").splitlines()
                self.assertEqual(len(lines), table["entry_count"])
                self.assertTrue(all(lines))
