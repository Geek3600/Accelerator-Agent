from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework import dse_calibration
from accagent.framework.source_cycle_analysis import PERFORMANCE_MODEL, ensure_source_cycle_analysis
from accagent.framework.stage_params import dse_llm_selection_evidence, select_dse_candidate
from tests import test_source_cycle_analysis


class DseCalibrationTest(unittest.TestCase):
    def make_report(self, root: Path) -> dict:
        result = test_source_cycle_analysis.SourceCycleAnalysisTest().make_sources(root)
        with patch("accagent.framework.stage_llm.run_stage_agent", return_value=result):
            performance = json.loads(ensure_source_cycle_analysis(root).read_text())
        expected_tps = (
            performance["processed_tokens"] * 100_000_000
            / performance["latency_cycles"]
        )
        return {
            "status": "pass",
            "measurement_scope": "generated_kernel_synthesis",
            "performance_model": PERFORMANCE_MODEL,
            "performance_estimation": performance,
            "clock_frequency_mhz": 100.0,
            "performance_tokens_per_second": expected_tps,
            "resources": {"lut": 100, "ff": 200, "dsp": 8, "bram36": 10, "bram18": 0, "uram": 0},
        }

    def test_publishes_only_current_source_bound_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.make_report(root / "run")
            with patch.object(dse_calibration, "SAMPLE_DIR", root / "samples"):
                path = dse_calibration.publish_sample(root / "run", report)
                self.assertIsNotNone(path)
                samples = dse_calibration.load_samples()
        self.assertEqual(len(samples), 1)
        self.assertEqual(
            samples[0]["performance_estimation"]["latency_cycles"],
            report["performance_estimation"]["latency_cycles"],
        )
        self.assertEqual(samples[0]["workload"]["processed_tokens"], 2)
        self.assertEqual(samples[0]["resources"], report["resources"])

    def test_rejects_stale_wrong_or_nonfinite_performance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = self.make_report(root / "run")
            variants = [
                {**report, "status": "incomplete"},
                {**report, "performance_model": "serial_legacy"},
                {**report, "performance_tokens_per_second": 123},
                {**report, "clock_frequency_mhz": float("nan")},
                {**report, "performance_tokens_per_second": float("inf")},
                {**report, "resources": {"lut": -1}},
            ]
            for key, value in [("source_fingerprint", "old"), ("latency_cycles", 999), ("processed_tokens", 3), ("synthesis_source_archive_sha256", "old")]:
                variants.append({**report, "performance_estimation": {**report["performance_estimation"], key: value}})
            with patch.object(dse_calibration, "SAMPLE_DIR", root / "samples"):
                for invalid in variants:
                    with self.subTest(invalid=invalid):
                        self.assertIsNone(dse_calibration.publish_sample(root / "run", invalid))
                self.assertEqual(dse_calibration.load_samples(), [])

    def test_loader_ignores_broken_or_wrong_model_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.joinpath("broken.json").write_text("[", encoding="utf-8")
            root.joinpath("list.json").write_text("[]", encoding="utf-8")
            root.joinpath("legacy.json").write_text(json.dumps({"performance_model": "old"}), encoding="utf-8")
            with patch.object(dse_calibration, "SAMPLE_DIR", root):
                self.assertEqual(dse_calibration.load_samples(), [])

    def test_dse_receives_samples_and_keeps_predictions_separate(self) -> None:
        anchor = {"source_fingerprint": "current", "resources": {"lut": 100}}
        candidate = {"candidate_id": "next", "parameters": {"lanes": 8}, "measurement": None}
        dse = {
            "records": [candidate], "unmeasured_candidate_ids": ["next"],
            "measurement_summary": {"complete": False}, "qor_calibration_samples": [anchor],
        }
        evidence = dse_llm_selection_evidence(dse, [candidate], [])
        estimate = {"status": "estimated", "anchor_source_fingerprints": ["current"], "resources": {"lut": 200}}
        candidate["qor_estimate"] = estimate
        selected, rationale = select_dse_candidate(dse, {"selected_candidate_id": "next", "qor_estimate": {"resources": {"lut": 1}}})
        self.assertEqual(evidence["qor_calibration_samples"], [anchor])
        self.assertIsNone(selected["measurement"])
        self.assertFalse(rationale["campaign_complete"])
        self.assertEqual(rationale["qor_estimate"], estimate)


if __name__ == "__main__":
    unittest.main()
