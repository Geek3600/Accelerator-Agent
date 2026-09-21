from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.board_progress import (
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    REQUIRED_PROGRESS_EVENT_FIELDS,
)
from scripts.verification import qwen_vcs_evidence_analyzer as analyzer


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class QwenVcsEvidenceAnalyzerTest(unittest.TestCase):
    def make_run(self, root: Path) -> tuple[Path, Path]:
        run_dir = root / "run"
        source = run_dir / "generated" / "board" / "board_shell.sv"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("module board_shell; endmodule\n", encoding="utf-8")
        write_json(
            run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
            {
                "board_consumed_tensor_hashes": ["b" * 64],
                "source_files": [
                    {
                        "source_id": "generated.board_shell",
                        "path": str(source),
                        "staged_path": "generated/board_shell.sv",
                    }
                ],
                "vcs_compile_plan": {
                    "ordered_commands": [
                        {
                            "phase": "compile",
                            "source_ids": ["generated.board_shell"],
                        }
                    ]
                },
                "testbench": {"sha256": "c" * 64},
            },
        )
        write_json(
            run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json",
            {
                "all_target_layers": True,
                "board_consumed_tensor_hashes": ["a" * 64],
                "consumed_tensor_hashes": ["f" * 64],
            },
        )
        write_json(
            run_dir / "verification" / "board_interface" / "board_source_identity.json",
            {
                "exact_user_sample_wrapper": True,
                "simulation_hashes_match_source": True,
            },
        )
        return run_dir, source

    def analyze(self, run_dir: Path, runner: dict) -> dict:
        write_json(
            run_dir / "verification" / "vcs" / "case_board_vcs_functional.json",
            runner,
        )
        return analyzer.analyze_manifest_board(run_dir)

    def test_manifest_failure_is_not_mislabeled_as_semantic_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "manifest_validation",
                    "errors": ["vcs_compile_plan ordered_commands is empty"],
                },
            )

        self.assertEqual(report["runner_phase"], "manifest_validation")
        self.assertEqual(report["failure_class"], "manifest_validation_failure")
        self.assertEqual(report["semantic_comparison"]["status"], "not_run")
        self.assertEqual(
            report["semantic_comparison"]["consumed_tensor_hashes"],
            ["a" * 64],
        )
        self.assertEqual(
            report["semantic_comparison"]["consumed_tensor_hash_source"],
            "dut_weight_binding_manifest.board_consumed_tensor_hashes",
        )
        self.assertNotIn("semantic", report["root_cause_class"])
        self.assertTrue(
            report["board_wrapper_identity"]
            ["complete_identity_bound_by_path_and_sha256"]
        )
        self.assertNotIn("evidence_records", report["board_wrapper_identity"])

    def test_remote_transport_failure_does_not_request_code_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            causal_slice_path = (
                run_dir
                / "verification"
                / "case_diagnostics"
                / "sacg_cctg_causal_slice.json"
            )
            write_json(
                causal_slice_path,
                {
                    "status": "ready",
                    "input_fingerprint_sha256": "stale-prior-fingerprint",
                },
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_sync",
                    "stderr_tail": "Connection reset by peer",
                },
            )
            current_slice = json.loads(causal_slice_path.read_text(encoding="utf-8"))

        self.assertEqual(report["failure_class"], "remote_transport_failure")
        self.assertFalse(report["repair_handoff"]["agent_should_apply_code_changes"])
        self.assertIn("Connection reset", report["failure_evidence"]["log_tail"])
        self.assertEqual(
            current_slice["status"], "not_applicable_before_runtime_execution"
        )
        self.assertNotEqual(
            current_slice.get("input_fingerprint_sha256"), "stale-prior-fingerprint"
        )
        self.assertEqual(
            report["failure_evidence"]["sacg_cctg_causal_slice"]["value"],
            current_slice,
        )

    def test_adaptive_semantic_stall_precedes_missing_terminal_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            stall = {
                "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                "status": "proven_semantic_stall",
                "last_semantic_event_cycle": 100,
                "latest_cycle": 10_000,
                "adaptive_silent_cycle_bound": 1_000,
            }
            write_json(
                run_dir
                / "verification"
                / "vcs"
                / "live"
                / "adaptive_semantic_stall.json",
                {
                    "input_fingerprint_sha256": "f" * 64,
                    "remote_workdir": "/remote/exact-job",
                    "evidence": stall,
                },
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 86,
                        "failure_class": "adaptive_semantic_stall",
                    },
                    "input_fingerprint_sha256": "f" * 64,
                    "remote_workdir": "/remote/exact-job",
                    "elaborated_hierarchy_report_valid": False,
                    "pipeline_overlap_passed": False,
                },
            )

        self.assertEqual(report["failure_class"], "vcs_runtime_semantic_stall")
        self.assertTrue(report["repair_handoff"]["agent_should_apply_code_changes"])
        self.assertIn("semantic progress stopped at cycle 100", report["summary"])
        self.assertNotIn("hierarchy report is invalid", report["summary"])
        self.assertEqual(
            report["failure_evidence"]["adaptive_semantic_stall_evidence"],
            stall,
        )

    def test_recovered_orphaned_stall_keeps_cycles_in_agent_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            recovered = {
                "schema_version": "spatialaccagent.orphaned_board_job_semantic_stall_recovery.v1",
                "status": "proven_semantic_stall",
                "last_semantic_event": {"cycle": 100, "phase": "prefetch_complete"},
                "latest_complete_remote_event": {"cycle": 10_000, "phase": "watch"},
                "observed_silent_cycles": 9_900,
                "observed_stall_snapshot_count": 8,
                "adaptive_bound": {"cycles": 1_000},
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 86,
                        "failure_class": "adaptive_semantic_stall",
                        "adaptive_semantic_stall_evidence": recovered,
                    },
                },
            )

        stall = report["failure_evidence"]["adaptive_semantic_stall_evidence"]
        self.assertEqual(stall["last_semantic_event_cycle"], 100)
        self.assertEqual(stall["latest_cycle"], 10_000)
        self.assertIn("cycle 100", report["summary"])

    def test_zero_time_livelock_precedes_missing_terminal_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            evidence = {
                "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                "status": "proven_zero_time_livelock",
                "last_cycle": 20_607_400,
                "last_semantic_progress_cycle": 20_607_400,
                "fixed_wall_clock_timeout": False,
                "fixed_cycle_timeout": False,
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": analyzer.ZERO_TIME_LIVELOCK_EXIT_CODE,
                        "failure_class": "zero_time_simulation_livelock",
                        "zero_time_livelock_evidence": evidence,
                    },
                    "elaborated_hierarchy_report_valid": False,
                    "pipeline_overlap_passed": False,
                },
            )

        self.assertEqual(report["failure_class"], "vcs_runtime_zero_time_livelock")
        self.assertIn("simulation time stopped advancing", report["summary"])
        self.assertNotIn("hierarchy report is invalid", report["summary"])
        self.assertEqual(
            report["failure_evidence"]["zero_time_livelock_evidence"],
            evidence,
        )
        self.assertEqual(report["failure_evidence"]["structured_failures"], {})
        self.assertTrue(report["repair_handoff"]["agent_should_apply_code_changes"])

    def test_fast_replay_livelock_is_not_mislabeled_as_board_runner_failure(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            evidence = {
                "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                "status": "proven_zero_time_livelock",
                "last_cycle": 20_606_976,
                "last_semantic_progress_cycle": 20_606_789,
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "fast_replay_restore_check",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": analyzer.ZERO_TIME_LIVELOCK_EXIT_CODE,
                        "failure_class": "zero_time_simulation_livelock",
                        "zero_time_livelock_evidence": evidence,
                    },
                    "pipeline_overlap_passed": False,
                },
            )

        self.assertEqual(report["failure_class"], "vcs_runtime_zero_time_livelock")
        self.assertIn("simulation time stopped advancing", report["summary"])
        self.assertNotIn("pipeline overlap report", report["summary"])
        self.assertTrue(report["repair_handoff"]["agent_should_apply_code_changes"])

    def test_supplemental_observation_artifact_reaches_failure_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            sidecar = (
                run_dir
                / "verification"
                / "vcs"
                / "reports"
                / "payload_probe.jsonl"
            )
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_text(
                '{"probe_id":"generic.payload","same_time_index":1}\n',
                encoding="utf-8",
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": analyzer.ZERO_TIME_LIVELOCK_EXIT_CODE,
                        "failure_class": "zero_time_simulation_livelock",
                    },
                    "supplemental_observation_artifacts": [
                        {
                            "status": "ready",
                            "path": str(sidecar),
                            "relative_path": "reports/payload_probe.jsonl",
                            "copied": True,
                            "summary": {
                                "record_count": 1,
                                "last_scalar_record": {
                                    "same_time_index": 1
                                },
                            },
                        }
                    ],
                    "vcs_native_loop_report": {
                        "enabled": True,
                        "native_loop_detected": False,
                        "loop_detection_enabled_observed": True,
                    },
                },
            )

        supplemental = report["failure_evidence"][
            "supplemental_observation_artifacts"
        ][0]
        self.assertEqual(supplemental["relative_path"], "reports/payload_probe.jsonl")
        self.assertEqual(
            supplemental["summary"]["last_scalar_record"]["same_time_index"],
            1,
        )
        self.assertIn(str(sidecar), report["sources"])
        self.assertFalse(
            report["failure_evidence"]["vcs_native_loop_report"][
                "native_loop_detected"
            ]
        )

    def test_pipeline_violation_routes_back_to_single_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            violation = {
                "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
                "status": "proven_pipeline_violation",
                "completed_input_tokens": 16,
                "final_input_cycle": 1234,
                "observed_output_beats": 0,
                "output_ready": 1,
            }
            contradiction = {
                "schema_version": (
                    "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1"
                ),
                "status": "proven",
                "target_debug_layer": "single_transformer_layer_kernel",
                "source_binding": {
                    "input_fingerprint_sha256": "f" * 64,
                    "board_trace_sha256": "a" * 64,
                    "lower_layer_certificate_sha256": "b" * 64,
                },
                "direct_kernel_boundary_observations": {
                    "kernel_start_accepted": True,
                    "kernel_ingress_complete": True,
                    "kernel_egress_ready": True,
                },
                "causal_localization": {
                    "earliest_causal_owner": "single_transformer_layer_kernel",
                    "named_contract_boundary_id": "edge.kernel.output",
                },
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "input_fingerprint_sha256": "f" * 64,
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 143,
                        "failure_class": "remote_tool_failure",
                    },
                    "progress_event_summary": {
                        "intra_layer_pipeline_violation_evidence": violation,
                    },
                    "board_to_lower_layer_contradiction_evidence": contradiction,
                },
            )

        self.assertEqual(
            report["failure_class"], "intra_layer_spatial_pipeline_violation"
        )
        self.assertEqual(
            report["repair_handoff"]["debug_layer"],
            "single_transformer_layer_kernel",
        )
        self.assertEqual(
            report["repair_handoff"]["repair_scope"],
            "single_transformer_layer_kernel",
        )
        self.assertEqual(
            report["schema_version"],
            "spatialaccagent.case_vcs_functional_diagnosis.v4",
        )
        self.assertEqual(
            report["applicability_binding"]["origin_layer"],
            "board_axi_ddr_wrapped_system",
        )
        self.assertEqual(
            report["applicability_binding"]["target_layer"],
            "single_transformer_layer_kernel",
        )
        self.assertTrue(report["applicability_binding"]["source_artifacts"])
        self.assertNotIn(
            "single_layer_pipeline_overlap",
            report["repair_handoff"]["must_rerun"],
        )
        self.assertEqual(
            report["repair_handoff"]["acceptance_contracts_to_revalidate"],
            ["single_layer_pipeline_overlap"],
        )

    def test_pipeline_output_symptom_without_direct_core_proof_stays_board_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            violation = {
                "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
                "status": "proven_pipeline_violation",
                "completed_input_tokens": 16,
                "final_input_cycle": 1234,
                "observed_output_beats": 0,
                "output_ready": 1,
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {"status": "fail", "returncode": 143},
                    "progress_event_summary": {
                        "intra_layer_pipeline_violation_evidence": violation,
                    },
                },
            )

        self.assertEqual(
            report["failure_class"], "board_output_lifecycle_frontier_violation"
        )
        self.assertEqual(
            report["repair_handoff"]["debug_layer"],
            "board_axi_ddr_wrapped_system",
        )
        self.assertEqual(
            report["repair_handoff"]["repair_scope"], "board_rtl_or_testbench"
        )
        self.assertEqual(
            report["failure_evidence"][
                "board_to_lower_layer_contradiction_evidence"
            ]["status"],
            "insufficient_evidence",
        )

    def test_checkpoint_artifact_failure_never_masks_hardware_stall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            stall = {
                "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                "status": "proven_semantic_stall",
                "last_semantic_event_cycle": 100,
                "latest_cycle": 10_000,
                "adaptive_silent_cycle_bound": 1_000,
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 86,
                        "failure_class": "adaptive_semantic_stall",
                        "adaptive_semantic_stall_evidence": stall,
                    },
                    "checkpoint_execution": {
                        "status": "pass",
                        "enabled": True,
                        "mode": "cold_capture",
                        "request_sha256": "a" * 64,
                        "required_for_stage3_repair": True,
                    },
                    "checkpoint_artifacts": {
                        "status": "fail",
                        "mode": "cold_capture",
                        "errors": [
                            "checkpoint capture report checkpoint_trigger_observed is not true"
                        ],
                    },
                    "checkpoint_runtime_execution_failure": {
                        "status": "ready",
                        "mode": "cold_capture",
                        "trigger_observation": {
                            "status": "observed",
                            "sequence": 6196,
                            "cycle": 20978345,
                        },
                    },
                },
            )

        self.assertEqual(
            report["failure_class"],
            "vcs_runtime_semantic_stall",
        )
        self.assertEqual(
            report["repair_handoff"]["repair_scope"],
            "board_rtl_or_testbench",
        )
        self.assertIn("semantic progress stopped", report["summary"])
        self.assertEqual(
            report["failure_evidence"]["checkpoint_artifacts"]["status"],
            "fail",
        )
        self.assertTrue(report["repair_handoff"]["agent_should_apply_code_changes"])

    def test_checkpoint_artifact_failure_does_not_mask_unreached_cut(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            stall = {
                "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                "status": "proven_semantic_stall",
                "last_semantic_event_cycle": 100,
                "latest_cycle": 10_000,
                "adaptive_silent_cycle_bound": 1_000,
            }
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 86,
                        "failure_class": "adaptive_semantic_stall",
                        "adaptive_semantic_stall_evidence": stall,
                    },
                    "checkpoint_execution": {
                        "status": "pass",
                        "enabled": True,
                        "mode": "cold_capture",
                    },
                    "checkpoint_artifacts": {
                        "status": "fail",
                        "mode": "cold_capture",
                        "errors": ["checkpoint capture report is missing"],
                    },
                },
            )

        self.assertEqual(report["failure_class"], "vcs_runtime_semantic_stall")
        self.assertEqual(
            report["failure_evidence"]["checkpoint_runtime_execution_failure"],
            {},
        )

    def test_compile_failure_reports_first_error_and_related_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            compile_log = run_dir / "verification" / "board_simulation" / "logs" / "compile.log"
            compile_log.parent.mkdir(parents=True, exist_ok=True)
            compile_log.write_text(
                "VCS compilation started\n"
                "Using synopsys_sim.setup from the bound fixture\n"
                "Error-[SE] Syntax error\n"
                "  sources/generated/board_shell.sv, 17\n"
                "token is unexpected\n",
                encoding="utf-8",
            )
            stale_simulation_log = compile_log.parent / "vcs_simulation.log"
            stale_simulation_log.write_text(
                "STALE_PRIOR_SIMULATION_HEARTBEAT\n" * 100,
                encoding="utf-8",
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile_log": str(compile_log),
                    "sim_log": str(stale_simulation_log),
                    "compile": {
                        "status": "fail",
                        "returncode": 1,
                        "failure_class": "remote_tool_failure",
                    },
                    "run": {"status": "not_run"},
                },
            )

        self.assertEqual(report["failure_class"], "vcs_compile_failure")
        self.assertEqual(report["failure_evidence"]["first_real_error"], "Error-[SE] Syntax error")
        self.assertEqual(
            report["failure_evidence"]["related_source_ids"],
            ["generated.board_shell"],
        )
        self.assertIn("token is unexpected", report["failure_evidence"]["log_tail"])
        self.assertNotIn(
            "STALE_PRIOR_SIMULATION_HEARTBEAT",
            report["failure_evidence"]["log_tail"],
        )

    def test_remote_storage_exhaustion_requests_unchanged_job_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            compile_log = run_dir / "verification" / "board_simulation" / "reports" / "vcs_compile.log"
            compile_log.parent.mkdir(parents=True, exist_ok=True)
            compile_log.write_text(
                "Error-[VFS_SDB_ERROR] VCS database file access error\n"
                "simv.daidir/prof.sdb\n"
                "due to I/O error: No space left on device\n",
                encoding="utf-8",
            )
            fingerprint = "7" * 64
            remote_workdir = "/tmp/spatialaccagent_board_vcs_run/777777777777_123"
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile_log": str(compile_log),
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "compile": {
                        "status": "fail",
                        "returncode": 1,
                        "failure_class": "remote_tool_failure",
                        "remote_workdir": remote_workdir,
                    },
                    "run": {"status": "not_run"},
                },
            )
            retry = json.loads(
                (
                    run_dir
                    / "verification"
                    / "vcs"
                    / analyzer.REMOTE_JOB_RETRY_REQUEST
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(
            report["failure_class"], "vcs_execution_environment_failure"
        )
        self.assertEqual(
            report["repair_handoff"]["repair_scope"],
            "execution_environment_retry",
        )
        self.assertFalse(
            report["repair_handoff"]["agent_should_apply_code_changes"]
        )
        self.assertEqual(retry["input_fingerprint_sha256"], fingerprint)
        self.assertEqual(retry["remote_workdir"], remote_workdir)
        self.assertTrue(retry["policy"]["hardware_edits_forbidden"])

    def test_signal_termination_is_not_routed_to_hardware_repair(self) -> None:
        provenance = {
            "schema_version": (
                "spatialaccagent.simulation_termination_provenance.v1"
            ),
            "status": "complete",
            "termination_source": "non_framework_signal_exit",
            "remote_state": "done",
            "exit_code": 143,
            "signal_number": 15,
            "simulator_terminal_log": {
                "status": "not_observed",
                "tail_lines": ["last exact-board heartbeat"],
            },
            "raw_terminal_log_tail": "last exact-board heartbeat",
        }
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            simulation_log = (
                run_dir
                / "verification"
                / "board_simulation"
                / "reports"
                / "vcs_simulation.log"
            )
            simulation_log.parent.mkdir(parents=True, exist_ok=True)
            simulation_log.write_text(
                "last exact-board heartbeat\n", encoding="utf-8"
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "sim_log": str(simulation_log),
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 143,
                        "failure_class": "remote_tool_failure",
                        "remote_state": "done",
                        "termination_provenance": provenance,
                    },
                    "termination_provenance": provenance,
                },
            )

        self.assertEqual(
            report["failure_class"], "vcs_external_or_signal_termination"
        )
        self.assertEqual(
            report["repair_handoff"]["repair_scope"],
            "execution_environment_retry",
        )
        self.assertFalse(
            report["repair_handoff"]["agent_should_apply_code_changes"]
        )
        self.assertEqual(
            report["failure_evidence"]["termination_provenance"], provenance
        )

    def test_runner_owned_simulator_signal_requires_capability_not_hardware_patch(
        self,
    ) -> None:
        provenance = {
            "schema_version": (
                "spatialaccagent.simulation_termination_provenance.v1"
            ),
            "status": "complete",
            "termination_source": "runner_owned_simulator_signal_exit",
            "remote_state": "done",
            "exit_code": 139,
            "signal_number": 11,
            "runner_process_provenance": {
                "attribution": "runner_owned_simulator_process_signal_exit",
                "last_running_process_snapshot": {
                    "simulator_like_process_observed": True,
                    "processes": [{"pid": 75, "command": "simv"}],
                },
            },
            "causal_classification": {
                "classification": "runner_owned_simulator_signal_exit_unattributed",
                "deterministic_hdl_or_testbench_failure_proven": False,
            },
            "simulator_terminal_log": {
                "status": "not_observed",
                "tail_lines": ["last exact-board heartbeat"],
            },
            "raw_terminal_log_tail": "last exact-board heartbeat",
        }
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            simulation_log = (
                run_dir
                / "verification"
                / "board_simulation"
                / "reports"
                / "vcs_simulation.log"
            )
            simulation_log.parent.mkdir(parents=True, exist_ok=True)
            simulation_log.write_text(
                "last exact-board heartbeat\n", encoding="utf-8"
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "sim_log": str(simulation_log),
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 139,
                        "failure_class": "remote_tool_failure",
                        "remote_state": "done",
                        "termination_provenance": provenance,
                    },
                    "termination_provenance": provenance,
                },
            )

        self.assertEqual(
            report["failure_class"], "vcs_simulator_signal_exit_unattributed"
        )
        self.assertEqual(
            report["repair_handoff"]["repair_scope"], "verification_capability"
        )
        self.assertEqual(
            report["failure_evidence"]["termination_provenance"], provenance
        )

    def test_proven_simulator_crash_forbids_semantic_source_repair(self) -> None:
        crash_line = (
            "An unexpected termination has occurred in ./vcs_work/simv "
            "due to a signal: Segmentation fault"
        )
        causal_classification = {
            "classification": "simulator_process_crash",
            "deterministic_hdl_or_testbench_failure_proven": False,
            "simulator_infrastructure_failure_proven": True,
            "source_semantic_repair_eligible": False,
        }
        provenance = {
            "schema_version": (
                "spatialaccagent.simulation_termination_provenance.v1"
            ),
            "status": "complete",
            "termination_source": "nonzero_process_exit",
            "remote_state": "done",
            "exit_code": 1,
            "causal_classification": causal_classification,
            "simulator_terminal_log": {
                "status": "observed",
                "simulator_crash_lines": [crash_line],
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {
                        "status": "fail",
                        "returncode": 1,
                        "failure_class": "remote_tool_failure",
                        "remote_state": "done",
                        "termination_provenance": provenance,
                    },
                    "termination_provenance": provenance,
                    "errors": ["pipeline overlap report is invalid"],
                },
            )

        self.assertEqual(report["failure_class"], "vcs_simulator_process_crash")
        self.assertEqual(
            report["repair_handoff"]["repair_scope"], "simulation_environment"
        )
        self.assertFalse(
            report["repair_handoff"]["agent_should_apply_code_changes"]
        )
        self.assertEqual(
            report["failure_evidence"]["first_real_error"], crash_line
        )
        self.assertEqual(
            report["repair_handoff"]["termination_causal_classification"],
            causal_classification,
        )

    def test_library_resolution_and_elaboration_are_distinct(self) -> None:
        cases = (
            (
                "Error: logical library vendor_primitives is not defined in synopsys_sim.setup\n",
                "vcs_library_resolution_failure",
                False,
            ),
            (
                "Error-[TMENF] Top Module/Entity not found during elaboration\n",
                "vcs_elaboration_failure",
                True,
            ),
        )
        for log_text, expected_class, code_change in cases:
            with self.subTest(expected_class=expected_class), tempfile.TemporaryDirectory() as tmp:
                run_dir, _ = self.make_run(Path(tmp))
                compile_log = run_dir / "compile.log"
                compile_log.write_text(log_text, encoding="utf-8")
                report = self.analyze(
                    run_dir,
                    {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "compile_log": str(compile_log),
                        "compile": {
                            "status": "fail",
                            "returncode": 1,
                            "failure_class": "remote_tool_failure",
                        },
                        "run": {"status": "not_run"},
                    },
                )

            self.assertEqual(report["failure_class"], expected_class)
            self.assertEqual(
                report["repair_handoff"]["agent_should_apply_code_changes"],
                code_change,
            )

    def test_protocol_monitor_failure_is_returned_structurally(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            executed = run_dir / "verification" / "board_simulation" / "executed.json"
            write_json(
                executed,
                {
                    "protocol_monitor_results": {
                        "interfaces": [
                            {
                                "interface": "memory_axi",
                                "status": "fail",
                                "violations": [{"rule": "wlast_alignment"}],
                                "transaction_counts": {"aw": 1, "w": 2, "b": 0, "ar": 1, "r": 1},
                            }
                        ]
                    }
                },
            )
            with patch.object(analyzer, "semantic_compare", return_value={"passed": True}):
                report = self.analyze(
                    run_dir,
                    {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "executed_manifest": str(executed),
                        "compile": {"status": "pass", "returncode": 0},
                        "run": {"status": "pass", "returncode": 0},
                        "elaborated_hierarchy_report_valid": True,
                        "structured_monitors_passed": False,
                        "structured_monitor_results": {
                            "monitor.memory_axi": {
                                "status": "fail",
                                "interface": "memory_axi",
                                "violation_count": 1,
                            }
                        },
                        "pipeline_overlap_passed": True,
                        "required_outputs_copied": True,
                        "pass_regex_matched": True,
                    },
                )

        self.assertEqual(report["failure_class"], "protocol_monitor_failure")
        failures = report["failure_evidence"]["structured_failures"]["protocol_monitors"]
        self.assertTrue(any(row.get("interface") == "memory_axi" for row in failures))
        self.assertTrue(
            any(row.get("violations") == [{"rule": "wlast_alignment"}] for row in failures)
        )
        self.assertIn("wlast_alignment", report["failure_evidence"]["first_real_error"])

    def test_hierarchy_failure_preserves_structured_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            executed = run_dir / "verification" / "board_simulation" / "executed.json"
            write_json(
                executed,
                {
                    "elaborated_hierarchy": {
                        "status": "fail",
                        "errors": ["compute-slot binding instance is absent"],
                        "failed_checks": ["compute_slot_binding"],
                    }
                },
            )
            with patch.object(analyzer, "semantic_compare", return_value={"passed": True}):
                report = self.analyze(
                    run_dir,
                    {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "executed_manifest": str(executed),
                        "compile": {"status": "pass", "returncode": 0},
                        "run": {"status": "pass", "returncode": 0},
                        "elaborated_hierarchy_report_valid": False,
                        "structured_monitors_passed": True,
                        "pipeline_overlap_passed": True,
                        "required_outputs_copied": True,
                        "pass_regex_matched": True,
                    },
                )

        self.assertEqual(report["failure_class"], "elaborated_hierarchy_failure")
        hierarchy = report["failure_evidence"]["structured_failures"]["elaborated_hierarchy"]
        self.assertEqual(hierarchy["status"], "fail")
        self.assertEqual(hierarchy["failed_checks"], ["compute_slot_binding"])
        self.assertIn("compute-slot binding", report["failure_evidence"]["first_real_error"])

    def test_jsonl_boundary_trace_is_normalized_with_partial_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _ = self.make_run(Path(tmp))
            trace = run_dir / "verification" / "board_simulation" / "boundary_trace.jsonl"
            trace.parent.mkdir(parents=True, exist_ok=True)
            row = {field: None for field in REQUIRED_PROGRESS_EVENT_FIELDS}
            row.update(
                {
                    "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
                    "sequence": 0,
                    "cycle": 100,
                    "event_kind": "semantic_progress",
                    "phase": "compute",
                    "semantic_progress": True,
                    "progress_epoch": 1,
                    "last_semantic_progress_cycle": 100,
                    "scheduler_state": "compute",
                    "layer": 0,
                    "token": 0,
                    "beat": 0,
                    "stage_or_boundary": "block_output",
                    "active_weight_bank": 0,
                    "preload_weight_bank": 1,
                    "activation_read_bank": 0,
                    "activation_write_bank": 1,
                    "prefetch_progress": {},
                    "runtime_load_progress": {},
                    "final_writeback_progress": {},
                    "axi_read": {},
                    "axi_write": {},
                }
            )
            trace.write_text(
                json.dumps(row) + "\n" + '{"schema_version":',
                encoding="utf-8",
            )
            report = self.analyze(
                run_dir,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "compile": {"status": "pass", "returncode": 0},
                    "run": {"status": "fail", "returncode": 1},
                    "outputs": {
                        "boundary_trace_file": {"path": str(trace), "copied": True}
                    },
                },
            )

            normalized = json.loads(
                (
                    run_dir
                    / "verification"
                    / "debug_closure"
                    / "boundary_trace.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(report["debug_closure"]["boundary_trace_record_count"], 1)
        self.assertEqual(
            report["debug_closure"]["progress_event_summary"]["progress_epoch"],
            1,
        )
        self.assertEqual(normalized["source_format"], "jsonl")
        self.assertEqual(normalized["record_count"], 1)


if __name__ == "__main__":
    unittest.main()
