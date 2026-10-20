import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.synthesis.export_timing_history import export_timing_history


class TimingHistoryTest(unittest.TestCase):
    def test_keeps_regressions_and_clock_only_attempts_in_source_bound_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            for index, frequency in enumerate([17.0, 45.0, 27.0]):
                source = str(index).encode()
                digest = hashlib.sha256(source).hexdigest()
                folder = run / "backend_board/measurements" / digest
                folder.mkdir(parents=True)
                (folder / "closure.tar.gz").write_bytes(source)
                report = folder / "app_shell_runtime_vivado.json"
                report.write_text(json.dumps({"status": "pass", "synthesis_source_archive_sha256": digest,
                                               "closure_archive": "closure.tar.gz"}))
                os.utime(report, (100 + index, 100 + index))
                (folder / "qor_metrics.json").write_text(json.dumps({
                    "status": "pass" if index != 2 else "incomplete",
                    "clock_frequency_mhz": frequency, "performance_tokens_per_second": 999,
                    "performance_estimation": {"synthesis_source_archive_sha256": digest},
                }))
            out = export_timing_history(run)
            rows = json.loads((out / "history.json").read_text())["measurements"]
            self.assertEqual([r["clock_frequency_mhz"] for r in rows], [17.0, 45.0, 27.0])
            self.assertEqual([r["best_clock_so_far_mhz"] for r in rows], [17.0, 45.0, 45.0])
            self.assertIsNone(rows[-1]["estimated_tokens_per_second"])
            export_timing_history(run)
            self.assertEqual(json.loads((out / "history.json").read_text())["measurements"], rows)
            (folder / "closure.tar.gz").unlink()
            export_timing_history(run)
            missing = json.loads((out / "history.json").read_text())["measurements"][-1]
            self.assertEqual(missing["evidence_status"], "reports_only_source_archive_missing")
            self.assertIsNone(missing["source_archive"])
            (folder / "closure.tar.gz").write_bytes(b"wrong source")
            export_timing_history(run)
            self.assertEqual(len(json.loads((out / "history.json").read_text())["measurements"]), 2)
