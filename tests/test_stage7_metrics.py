from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from scripts.synthesis import case_stage7_metrics as metrics


class Stage7MetricsTest(unittest.TestCase):
    def test_collects_resource_power_and_completed_performance_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            utilization = run_dir / "utilization.rpt"
            timing = run_dir / "timing.rpt"
            power = run_dir / "power.rpt"
            performance = run_dir / "performance.json"
            utilization.write_text(
                """
| Instance | Module | Total LUTs | Logic LUTs | LUTRAMs | SRLs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |
| top      | (top)  | 58,843     | 42,115     | 16,728 | 0    | 126,397 | 0 | 0 | 0 | 8 |
""",
                encoding="utf-8",
            )
            timing.write_text(
                """
    WNS(ns)      TNS(ns)
    -------      -------
     -4.691     -676.362

Clock          Waveform(ns)       Period(ns)      Frequency(MHz)
-----          ------------       ----------      --------------
qwen_core_clk  {0.000 10.000}     20.000          50.000
""",
                encoding="utf-8",
            )
            power.write_text(
                """
| Total On-Chip Power (W)  | 2.986 |
| Dynamic (W)              | 0.509 |
| Device Static (W)        | 2.477 |
| Confidence Level         | Low   |
| Clock         | Domain | Constraint (ns) |
+---------------+--------+-----------------+
| qwen_core_clk | clock  |            20.0 |
""",
                encoding="utf-8",
            )
            performance.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "counter_source": "synthesizable_dut_counter",
                        "latency_cycles": 1000,
                        "processed_tokens": 25,
                    }
                ),
                encoding="utf-8",
            )

            report = metrics.build_report(
                Namespace(
                    run_dir=run_dir,
                    out=None,
                    utilization_report=utilization,
                    timing_report=timing,
                    power_report=power,
                    performance_report=performance,
                    clock_frequency_hz=None,
                    clock_period_ns=None,
                    processed_tokens=None,
                )
            )

        self.assertEqual(set(report), {"resources", "power_w", "clock_frequency_mhz", "performance_tokens_per_second"})
        self.assertEqual(report["resources"]["lut"], 58_843)
        self.assertEqual(report["resources"]["ff"], 126_397)
        self.assertEqual(report["resources"]["dsp"], 8)
        self.assertEqual(report["power_w"], 2.986)
        self.assertAlmostEqual(report["clock_frequency_mhz"], 40.500587, places=6)
        self.assertAlmostEqual(report["performance_tokens_per_second"], 1_012_514.681, places=3)

    def test_missing_performance_measurement_remains_pending(self) -> None:
        result = metrics.parse_performance_tokens_per_second(
            Path("missing-performance-report.json"),
            50.0,
            None,
        )

        self.assertIsNone(result)

    def test_prefers_real_app_shell_reports_over_legacy_standalone_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            app_shell = run_dir / "app_shell_runtime_bitstream"
            app_shell.mkdir()
            (app_shell / "app_shell_impl_utilization.rpt").write_text(
                "| Instance | Module | Total LUTs | Logic LUTs | LUTRAMs | SRLs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n"
                "| app_shell | (top) | 101 | 80 | 21 | 0 | 202 | 3 | 4 | 5 | 6 |\n",
                encoding="utf-8",
            )
            (app_shell / "app_shell_impl_timing.rpt").write_text(
                "WNS(ns)\n----\n 0.000\n\nClock Waveform(ns) Period(ns) Frequency(MHz)\nclk {0.000 5.000} 10.000 100.000\n",
                encoding="utf-8",
            )
            (app_shell / "app_shell_impl_power.rpt").write_text(
                "| Total On-Chip Power (W) | 3.250 |\n", encoding="utf-8"
            )
            performance = run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
            performance.parent.mkdir(parents=True)
            performance.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "counter_source": "synthesizable_dut_counter",
                        "latency_cycles": 100,
                        "processed_tokens": 10,
                    }
                ),
                encoding="utf-8",
            )

            report = metrics.build_report(
                Namespace(
                    run_dir=run_dir,
                    out=None,
                    utilization_report=None,
                    timing_report=None,
                    power_report=None,
                    performance_report=None,
                    clock_frequency_hz=100_000_000.0,
                    clock_period_ns=None,
                    processed_tokens=None,
                )
            )

        self.assertEqual(report["resources"]["lut"], 101)
        self.assertEqual(report["resources"]["dsp"], 6)
        self.assertEqual(report["power_w"], 3.25)

    def test_rejects_legacy_standalone_reports_when_app_shell_reports_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            legacy = run_dir / "vivado_qwen_generated_bitstream"
            legacy.mkdir()
            (legacy / "qwen_generated_impl_utilization.rpt").write_text("legacy", encoding="utf-8")
            (legacy / "qwen_generated_impl_timing.rpt").write_text("legacy", encoding="utf-8")
            power = run_dir / "vivado_qwen_generated_power"
            power.mkdir()
            (power / "qwen_generated_impl_power.rpt").write_text("legacy", encoding="utf-8")

            with self.assertRaises(ValueError):
                metrics.build_report(
                    Namespace(
                        run_dir=run_dir,
                        out=None,
                        utilization_report=None,
                        timing_report=None,
                        power_report=None,
                        performance_report=None,
                        clock_frequency_hz=None,
                        clock_period_ns=None,
                        processed_tokens=None,
                    )
                )

    def test_main_records_exact_app_shell_provenance_without_changing_qor_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            app_shell = run_dir / "app_shell_runtime_bitstream"
            app_shell.mkdir()
            (run_dir / "backend_board" / "case_diagnostics").mkdir(parents=True)
            (run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json").write_text(
                json.dumps({"mode": "bitstream", "status": "pass"}), encoding="utf-8"
            )
            (app_shell / "app_shell_impl_utilization.rpt").write_text(
                "| Instance | Module | Total LUTs | Logic LUTs | LUTRAMs | SRLs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n"
                "| app_shell | (top) | 100 | 80 | 20 | 0 | 200 | 3 | 4 | 5 | 6 |\n",
                encoding="utf-8",
            )
            (app_shell / "app_shell_impl_timing.rpt").write_text(
                "WNS(ns)\n----\n 0.000\n\nClock Waveform(ns) Period(ns) Frequency(MHz)\nclk {0.000 5.000} 10.000 100.000\n",
                encoding="utf-8",
            )
            (app_shell / "app_shell_impl_power.rpt").write_text(
                "| Total On-Chip Power (W) | 3.0 |\n", encoding="utf-8"
            )
            counter = run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
            counter.parent.mkdir(parents=True)
            counter.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "counter_source": "synthesizable_dut_counter",
                        "latency_cycles": 100,
                        "processed_tokens": 10,
                    }
                ),
                encoding="utf-8",
            )
            output = run_dir / "backend_board" / "qor" / "qor_metrics.json"

            self.assertEqual(
                metrics.main([
                    "--run-dir", str(run_dir), "--out", str(output), "--clock-frequency-hz", "100000000"
                ]),
                0,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(report["measurement_scope"], "exact_target_board_app_shell")
        self.assertEqual(len(report["evidence_paths"]), 6)
        self.assertEqual(report["performance_tokens_per_second"], 10_000_000.0)


if __name__ == "__main__":
    unittest.main()
