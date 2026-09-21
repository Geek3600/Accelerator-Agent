from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from accagent.framework.dse_ledger import (
    EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
    append_measurement,
    candidate_fingerprint,
    complete_metrics,
    load_latest,
)


class DseLedgerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = {
            "lanes": 16,
            "compute_array_rows": 8,
            "compute_array_cols": 8,
            "fifo_depth": 32,
            "activation_banks": 2,
            "weight_banks_by_role": {"weight_qkv": 4},
        }
        self.metrics = {
            "resources": {"lut": 10, "ff": 20, "bram36": 3, "bram18": 0, "uram": 4, "dsp": 5},
            "power_w": 2.5,
            "clock_frequency_mhz": 200.0,
            "performance_tokens_per_second": 10_000.0,
        }

    def test_measured_row_requires_all_four_real_metrics(self) -> None:
        self.assertTrue(complete_metrics(self.metrics))
        incomplete = dict(self.metrics)
        incomplete["performance_tokens_per_second"] = None
        self.assertFalse(complete_metrics(incomplete))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                append_measurement(
                    Path(tmp) / "measurements.jsonl",
                    parameters=self.parameters,
                    measurement_status="measured",
                    measurement_scope=EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
                    metrics=incomplete,
                )

    def test_latest_record_replaces_prior_outcome_for_the_same_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurements.jsonl"
            append_measurement(
                path,
                parameters=self.parameters,
                measurement_status="infeasible",
                measurement_scope=EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
                reason="real app-shell implementation failed",
            )
            append_measurement(
                path,
                parameters=self.parameters,
                measurement_status="measured",
                measurement_scope=EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
                metrics=self.metrics,
                evidence_paths=["app_shell_impl_utilization.rpt"],
            )
            latest = load_latest(path)

        row = latest[candidate_fingerprint(self.parameters)]
        self.assertEqual(row["measurement_status"], "measured")
        self.assertEqual(row["metrics"], self.metrics)

    def test_rejects_any_non_app_shell_measurement_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                append_measurement(
                    Path(tmp) / "measurements.jsonl",
                    parameters=self.parameters,
                    measurement_status="measured",
                    measurement_scope="standalone_generated_top",
                    metrics=self.metrics,
                )

    def test_legacy_rows_without_measurement_scope_are_not_current_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurements.jsonl"
            path.write_text(
                '{"candidate_fingerprint":"legacy","measurement_status":"measured"}\n',
                encoding="utf-8",
            )
            self.assertEqual(load_latest(path), {})


if __name__ == "__main__":
    unittest.main()
