from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.agent import is_formal_dse_backtrack
from accagent.framework.dse_ledger import EXACT_TARGET_BOARD_APP_SHELL_SCOPE, load_latest
from accagent.framework.stage_backend import (
    builtin_backend_tool,
    check_upstream_hierarchical_verification_closure,
    classify_qor_optimization,
    record_exact_dse_measurement,
    roles_for_scope,
)


class DseBackendTest(unittest.TestCase):
    @staticmethod
    def state_for(parameters_path: Path) -> dict[str, object]:
        return {
            "artifacts": [
                {
                    "id": "artifact.stage4.parameter_binding",
                    "path": str(parameters_path),
                }
            ]
        }

    @staticmethod
    def binding(path: Path) -> None:
        path.write_text(
            json.dumps(
                {
                    "selected_architecture": {
                        "parameters": {
                            "lanes": 16,
                            "fifo_depth": 32,
                            "activation_banks": 2,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def exact_qor(run_dir: Path) -> None:
        report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps({"mode": "bitstream", "status": "pass"}), encoding="utf-8")
        bitstream = run_dir / "app_shell_runtime_bitstream"
        bitstream.mkdir()
        utilization = bitstream / "app_shell_impl_utilization.rpt"
        timing = bitstream / "app_shell_impl_timing.rpt"
        power = bitstream / "app_shell_impl_power.rpt"
        utilization.write_text("present\n", encoding="utf-8")
        timing.write_text("present\n", encoding="utf-8")
        power.write_text("present\n", encoding="utf-8")
        counter = run_dir / "verification" / "board_simulation" / "reports" / "performance_counter_report.json"
        counter.parent.mkdir(parents=True)
        counter.write_text("present\n", encoding="utf-8")
        metrics_path = run_dir / "backend_board" / "qor" / "qor_metrics.json"
        metrics_path.parent.mkdir(parents=True)
        evidence_paths = [
            str(path.resolve())
            for path in [report, utilization, timing, power, counter, metrics_path]
        ]
        metrics_path.write_text(
            json.dumps(
                {
                    "measurement_scope": EXACT_TARGET_BOARD_APP_SHELL_SCOPE,
                    "evidence_paths": evidence_paths,
                    "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 0, "uram": 2, "dsp": 3},
                    "power_w": 2.0,
                    "clock_frequency_mhz": 200.0,
                    "performance_tokens_per_second": 1_000.0,
                }
            ),
            encoding="utf-8",
        )

    def test_default_backend_scope_uses_only_exact_app_shell_measurement_chain(self) -> None:
        roles = roles_for_scope("all")
        self.assertIn("app_shell_runtime_bitstream", roles)
        self.assertIn("stage7_metrics", roles)
        self.assertNotIn("vivado_synthesis", roles)
        self.assertNotIn("vivado_implementation", roles)
        self.assertNotIn("vivado_power", roles)
        self.assertNotIn("board_runtime", roles)

    def test_backend_never_falls_back_to_a_legacy_power_script_or_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            self.assertIsNone(builtin_backend_tool("vivado_power", run_dir, []))

        gate = check_upstream_hierarchical_verification_closure({"artifacts": []})
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["closure_mode"], "unresolved_current_run")

    def test_unmeasured_legal_candidates_force_the_exact_dse_backtrack(self) -> None:
        metrics = {
            "resources": {"lut": 10, "ff": 20, "bram36": 1, "bram18": 0, "uram": 1, "dsp": 1},
            "power_w": 1.0,
            "clock_frequency_mhz": 100.0,
            "performance_tokens_per_second": 1_000.0,
        }
        result = classify_qor_optimization(
            {},
            metrics,
            campaign={"unmeasured_candidate_ids": ["arch_next"]},
            measurement={"measurement_status": "measured"},
        )

        self.assertEqual(result["decision"], "dse_backtrack")
        self.assertEqual(result["next_stage"], "stage4.parameter_binding")

    def test_exact_dse_backtrack_is_identified_across_public_stage_aliases(self) -> None:
        request = {
            "target_stage": "stage4.parameter_binding",
            "verification_scope": "formal_dse_campaign",
        }
        self.assertTrue(is_formal_dse_backtrack(request, "parameter_binding"))

    def test_only_complete_exact_app_shell_qor_enters_the_measurement_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            binding = run_dir / "parameter_binding" / "parameter_binding.json"
            binding.parent.mkdir()
            self.binding(binding)
            self.exact_qor(run_dir)

            result = record_exact_dse_measurement(self.state_for(binding), run_dir)
            latest = load_latest(run_dir / "parameter_binding" / "dse_measurements.jsonl")

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(result["measurement_status"], "measured")
        self.assertEqual(len(latest), 1)
        self.assertEqual(next(iter(latest.values()))["measurement_scope"], EXACT_TARGET_BOARD_APP_SHELL_SCOPE)

    def test_explicit_app_shell_implementation_failure_records_only_infeasible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            binding = run_dir / "parameter_binding" / "parameter_binding.json"
            binding.parent.mkdir()
            self.binding(binding)
            report = run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {
                        "mode": "bitstream",
                        "status": "fail",
                        "summary": "place failed",
                        "inspection": {"top_impl_status": "place_design failed"},
                    }
                ),
                encoding="utf-8",
            )

            result = record_exact_dse_measurement(self.state_for(binding), run_dir)
            latest = load_latest(run_dir / "parameter_binding" / "dse_measurements.jsonl")

        self.assertEqual(result["measurement_status"], "infeasible")
        row = next(iter(latest.values()))
        self.assertEqual(row["measurement_status"], "infeasible")
        self.assertIsNone(row["metrics"])


if __name__ == "__main__":
    unittest.main()
