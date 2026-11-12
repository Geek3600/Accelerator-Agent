from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from scripts.synthesis import case_stage7_metrics as metrics


class Stage7MetricsTest(unittest.TestCase):
    def test_multiclock_timing_uses_selected_clock_and_its_own_slack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            timing = Path(tmp) / "timing.rpt"
            timing.write_text(
                "WNS(ns)\n-------\n-1.500\n\n"
                "Clock Waveform(ns) Period(ns) Frequency(MHz)\n"
                "ddr_clk {0.000 5.000} 10.000 100.000\n"
                "  compute_clk {0.000 2.000} 4.000 250.000\n\n"
                "| Intra Clock Table\nClock WNS(ns) TNS(ns)\n"
                "ddr_clk -1.500 -20.000\ncompute_clk -0.477 -10.000\n"
                "| Inter Clock Table\n",
                encoding="utf-8",
            )
            self.assertIsNone(metrics.parse_achieved_frequency_mhz(timing, None))
            self.assertIsNone(metrics.parse_achieved_frequency_mhz(timing, 4.0))
            self.assertIsNone(metrics.parse_achieved_frequency_mhz(timing, None, "missing_clk"))
            self.assertAlmostEqual(metrics.parse_achieved_frequency_mhz(timing, None, "compute_clk"), 1000 / 4.477)

    def test_clock_constraint_without_timing_evidence_is_not_achieved_frequency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            timing = Path(tmp) / "timing.rpt"
            timing.write_text("clk {0.000 2.000} 4.000 250.000\n", encoding="utf-8")
            self.assertIsNone(metrics.parse_achieved_frequency_mhz(timing, None))

    def test_kernel_qor_keeps_its_boundary_and_clock_instead_of_sample_cnn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            synthesis = root / "synthesis.json"
            synthesis.write_text(json.dumps({
                "status": "pass", "mode": "synth", "measurement_scope": metrics.SYNTHESIS_KERNEL_SCOPE,
                "synthesis_top": "DifferentModelKernel", "timing_clock": "kernel_clk",
            }), encoding="utf-8")
            utilization = root / "utilization.rpt"
            utilization.write_text(
                "| Instance | Module | Total LUTs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n"
                "| DifferentModelKernel | (top) | 123 | 456 | 7 | 8 | 9 | 10 |\n",
                encoding="utf-8",
            )
            timing = root / "timing.rpt"
            timing.write_text(
                "kernel_clk {0.000 2.000} 4.000 250.000\n"
                "| Intra Clock Table\nClock WNS(ns) TNS(ns)\nkernel_clk -0.500 -10.000\n",
                encoding="utf-8",
            )
            args = Namespace(
                run_dir=root, out=None, app_shell_report=synthesis,
                utilization_report=utilization, timing_report=timing, power_report=None, performance_report=None,
                clock_frequency_hz=None, clock_period_ns=None, processed_tokens=None,
            )
            report = metrics.build_report(args)
            provenance = metrics.measurement_provenance(args)

        self.assertEqual(report["measurement_scope"], metrics.SYNTHESIS_KERNEL_SCOPE)
        self.assertEqual(provenance["measurement_scope"], metrics.SYNTHESIS_KERNEL_SCOPE)
        self.assertEqual(report["resource_top"], "DifferentModelKernel")
        self.assertIn("excluding_board_shell", report["resource_boundary"])
        self.assertEqual(report["resources"]["lut"], 123)
        self.assertAlmostEqual(report["clock_frequency_mhz"], 1000 / 4.5)

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
                        "measurement_complete": True,
                        "count_is_latency": True,
                        "latency_cycles": 1000,
                        "processed_tokens": 25,
                        "source_fingerprint": "current-synthesis",
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "accagent.framework.source_cycle_analysis.source_fingerprint",
                return_value="current-synthesis",
            ):
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

        self.assertEqual(
            set(report),
            {
                "status",
                "missing_metrics",
                "measurement_scope",
                "metric_quality",
                "resources",
                "power_w",
                "clock_frequency_mhz",
                "performance_tokens_per_second",
                "performance_model",
                "performance_estimation",
            },
        )
        self.assertEqual(report["resources"]["lut"], 58_843)
        self.assertEqual(report["resources"]["ff"], 126_397)
        self.assertEqual(report["resources"]["dsp"], 8)
        self.assertEqual(report["power_w"], 2.986)
        self.assertAlmostEqual(report["clock_frequency_mhz"], 40.500587, places=6)
        self.assertAlmostEqual(report["performance_tokens_per_second"], 1_012_514.681, places=3)
        self.assertTrue(report["performance_estimation"]["rtl_cycles_measured"])

    def test_synthesis_scope_calculates_throughput_from_rtl_cycles_without_board_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            out_dir = run_dir / "app_shell_runtime_bitstream"
            out_dir.mkdir()
            diagnostics = run_dir / "backend_board" / "case_diagnostics"
            diagnostics.mkdir(parents=True)
            app_shell_report = diagnostics / "app_shell_runtime_vivado.json"
            app_shell_report.write_text(json.dumps({"mode": "synth", "status": "pass"}), encoding="utf-8")
            utilization = out_dir / "app_shell_synth_utilization.rpt"
            utilization.write_text(
                "| Instance | Module | Total LUTs | Logic LUTs | LUTRAMs | SRLs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n"
                "| app_shell | (top) | 101 | 80 | 21 | 0 | 202 | 3 | 4 | 5 | 6 |\n",
                encoding="utf-8",
            )
            timing = out_dir / "app_shell_synth_timing.rpt"
            timing.write_text(
                "WNS(ns)\n----\n 0.000\n\nClock Waveform(ns) Period(ns) Frequency(MHz)\nclk {0.000 5.000} 10.000 100.000\n",
                encoding="utf-8",
            )
            (out_dir / "app_shell_synth_power.rpt").write_text("", encoding="utf-8")
            performance = run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
            performance.parent.mkdir(parents=True)
            performance.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "counter_source": "synthesizable_dut_counter",
                        "measurement_complete": True,
                        "count_is_latency": True,
                        "latency_cycles": 200_000_000,
                        "processed_tokens": 912,
                        "source_fingerprint": "current-synthesis",
                    }
                ),
                encoding="utf-8",
            )
            output = run_dir / "backend_board" / "qor" / "qor_metrics.json"
            args = Namespace(
                run_dir=run_dir,
                out=output,
                utilization_report=None,
                timing_report=None,
                power_report=None,
                performance_report=None,
                app_shell_report=app_shell_report,
                clock_frequency_hz=None,
                clock_period_ns=None,
                processed_tokens=None,
            )

            with patch(
                "accagent.framework.source_cycle_analysis.source_fingerprint",
                return_value="current-synthesis",
            ):
                report = metrics.build_report(args)
                provenance = metrics.measurement_provenance(args)

        self.assertEqual(report["measurement_scope"], metrics.SYNTHESIS_APP_SHELL_SCOPE)
        self.assertEqual(report["metric_quality"], "post_synthesis_clock_and_rtl_cycle_calculation")
        self.assertEqual(report["performance_tokens_per_second"], 456.0)
        self.assertEqual(report["performance_model"], "synthesizable_dut_counter")
        self.assertIn(str(performance.resolve()), provenance["evidence_paths"])

    def test_rejects_legacy_serial_source_cycle_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "backend_board/qor/source_cycle_analysis.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({
                "status": "pass", "counter_source": "source_schedule_analysis",
                "performance_model": "single_block_reuse_throughput",
                "latency_cycles": 100, "processed_tokens": 10, "model_layers": 12,
            }), encoding="utf-8")
            self.assertIsNone(metrics.parse_performance_tokens_per_second(report, 250.0, None))

    def test_rejects_counter_not_bound_to_latest_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "performance_counter_report.json"
            report.write_text(json.dumps({
                "status": "pass", "counter_source": "synthesizable_dut_counter",
                "source_fingerprint": "old-source", "latency_cycles": 100,
                "processed_tokens": 10,
            }), encoding="utf-8")
            with patch(
                "accagent.framework.source_cycle_analysis.source_fingerprint",
                return_value="current-source",
            ):
                self.assertIsNone(metrics.parse_performance_tokens_per_second(report, 250.0, None, Path(tmp)))

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
                        "measurement_complete": True,
                        "count_is_latency": True,
                        "latency_cycles": 100,
                        "processed_tokens": 10,
                        "source_fingerprint": "current-synthesis",
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

            report = metrics.build_report(
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
        self.assertEqual(report["status"], "incomplete")
        self.assertIsNone(report["resources"])
        self.assertIn("resources", report["missing_metrics"])

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
                        "measurement_complete": True,
                        "count_is_latency": True,
                        "latency_cycles": 100,
                        "processed_tokens": 10,
                        "source_fingerprint": "current-synthesis",
                    }
                ),
                encoding="utf-8",
            )
            output = run_dir / "backend_board" / "qor" / "qor_metrics.json"

            with patch(
                "accagent.framework.source_cycle_analysis.source_fingerprint",
                return_value="current-synthesis",
            ):
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
