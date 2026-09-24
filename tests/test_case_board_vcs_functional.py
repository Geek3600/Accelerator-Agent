from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.board_progress import (
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    REQUIRED_PROGRESS_EVENT_FIELDS,
    adaptive_semantic_stall_evidence,
)
from accagent.framework.fpga_ip_contract import simulation_source_contract
from accagent.framework.simulation_checkpoint import (
    CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
    CHECKPOINT_CONTRACT_SCHEMA_VERSION,
    CHECKPOINT_EQUIVALENCE_SCHEMA_VERSION,
    CHECKPOINT_REQUEST_SCHEMA_VERSION,
    CHECKPOINT_RESTORE_REPORT_SCHEMA_VERSION,
    checkpoint_request_projection,
    semantic_checkpoint_cut_sha256,
)
from scripts.verification import case_board_vcs_functional as board_vcs


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_file(path: Path, value: str) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return {"path": str(path), "sha256": board_vcs.sha256_file(path)}


def progress_event(sequence: int, event_kind: str, semantic_progress: bool) -> dict:
    row = {field: None for field in REQUIRED_PROGRESS_EVENT_FIELDS}
    row.update(
        {
            "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
            "sequence": sequence,
            "cycle": sequence + 1,
            "event_kind": event_kind,
            "phase": "run",
            "semantic_progress": semantic_progress,
            "progress_epoch": 1,
            "last_semantic_progress_cycle": 1,
            "scheduler_state": "run",
            "layer": 0,
            "token": 0,
            "beat": 0,
            "stage_or_boundary": "block_output",
            "active_weight_bank": 0,
            "preload_weight_bank": 1,
            "activation_read_bank": 0,
            "activation_write_bank": 1,
            "prefetch_progress": {"accepted": 1},
            "runtime_load_progress": {"accepted": 1},
            "final_writeback_progress": {"accepted": 1},
            "axi_read": {"accepted": 1, "outstanding": 0},
            "axi_write": {"accepted": 1, "outstanding": 0},
        }
    )
    return row


def checkpoint_ready_manifest() -> dict:
    return {
        "top_module": "board_tb",
        "validation_mode": "compute_slot_axi",
        "source_closure_sha256": "a" * 64,
        "compile_source_set_sha256": "b" * 64,
        "vcs_compile_plan_sha256": "c" * 64,
        "source_files": [
            {
                "source_id": "generated.testbench",
                "sha256": "d" * 64,
                "role": "testbench",
            }
        ],
        "artifacts": {
            "input": {"path": "input.memh", "sha256": "e" * 64},
            "weight_image": {"path": "weights.bin", "sha256": "f" * 64},
        },
        "vcs": {"runtime_plusargs": {"INPUT": "input"}},
        "testbench": {
            "simulation_checkpoint_contract": board_vcs.framework_checkpoint_contract({})
        },
    }


def cold_checkpoint_request(manifest: dict) -> dict:
    request = {
        "schema_version": CHECKPOINT_REQUEST_SCHEMA_VERSION,
        "status": "ready",
        "execution_identity": board_vcs.simulation_execution_identity(manifest),
        "semantic_cut": {
            "status": "ready",
            "frontier_id": "frontier.output",
            "settle_cycles": 2,
            "portable_state_quiescent": True,
            "future_cctg_nodes": ["node.output"],
            "causal_reachability": {
                "schema_version": (
                    "spatialaccagent.checkpoint_cut_reachability.v1"
                ),
                "status": "pass",
                "future_cctg_nodes": ["node.output"],
            },
            "trigger": {
                "sequence": 10,
                "cycle": 100,
                "phase": "kernel_output_token_complete",
                "token": 0,
            },
        },
        "replay_decision": {
            "status": "cold_capture_required",
            "mode": "cold_capture",
            "blockers": ["no compatible checkpoint"],
        },
        "checkpoint_contract_status": "ready",
        "checkpoint_contract_blockers": [],
        "selected_checkpoint_manifest": "",
        "selected_checkpoint_manifest_sha256": None,
        "targeted_replay_plan": {},
        "repair_impact": {},
    }
    request["semantic_cut"]["cut_sha256"] = semantic_checkpoint_cut_sha256(
        request["semantic_cut"]
    )
    request["request_sha256"] = board_vcs.canonical_contract_sha256(
        checkpoint_request_projection(request)
    )
    return request


def fixed_checkpoint_request(manifest: dict) -> dict:
    request = cold_checkpoint_request(manifest)
    request["semantic_cut"] = {
        "schema_version": "spatialaccagent.semantic_checkpoint_cut.v1",
        "status": "ready",
        "cut_kind": "fixed_runtime_boundary",
        "fixed_cut": "after_weight_load_before_first_token",
        "frontier_id": "checkpoint.after_weight_load_before_first_token",
        "trigger": {
            "phase": "after_weight_load_before_first_token",
            "event_kind": "fixed_runtime_cut",
            "layer": -1,
            "token": -1,
            "beat": -1,
            "stage_or_boundary": "checkpoint.after_weight_load_before_first_token",
        },
        "settle_cycles": 1,
        "portable_state_quiescent": True,
        "portable_state_blockers": [],
        "selection_mode": "fixed_first_capture_boundary",
    }
    request["semantic_cut"]["cut_sha256"] = semantic_checkpoint_cut_sha256(
        request["semantic_cut"]
    )
    request["request_sha256"] = board_vcs.canonical_contract_sha256(
        checkpoint_request_projection(request)
    )
    return request


class BoardVcsFunctionalTest(unittest.TestCase):
    def test_cold_capture_stops_after_the_checkpoint_is_durable(self) -> None:
        plan = {
            "enabled": True,
            "mode": "cold_capture",
            "contract": {
                "outputs": {
                    "capture_report": {
                        "path": "checkpoint/capture_report.json",
                    }
                },
                "portable_state_capsule": {"dut_state_root": "board_tb.dut"},
            },
        }

        args = board_vcs.checkpoint_runtime_plusargs(plan)

        self.assertEqual(args, ["+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE"])

    def test_checkpoint_uses_native_vcs_without_a_vpi_adapter(self) -> None:
        self.assertEqual(
            board_vcs.checkpoint_adapter_elaboration_args({}, Path("."), Path(".")),
            [],
        )
        self.assertEqual(board_vcs.checkpoint_adapter_compile_define_args({}, "vlogan"), [])

    def test_fresh_replay_generation_selects_a_new_recoverable_workdir(self) -> None:
        root = "/remote/board/run"
        fingerprint = "a" * 64
        generation_a = "b" * 64
        generation_b = "c" * 64

        ordinary = board_vcs.exact_board_remote_workdir(root, fingerprint)
        fresh_a = board_vcs.exact_board_remote_workdir(
            root, fingerprint, generation_a
        )
        repeated_a = board_vcs.exact_board_remote_workdir(
            root, fingerprint, generation_a
        )
        fresh_b = board_vcs.exact_board_remote_workdir(
            root, fingerprint, generation_b
        )

        self.assertNotEqual(fresh_a, ordinary)
        self.assertEqual(fresh_a, repeated_a)
        self.assertNotEqual(fresh_a, fresh_b)
        self.assertRegex(Path(fresh_a).name, r"^a{12}_[0-9]+$")
        with self.assertRaises(ValueError):
            board_vcs.exact_board_remote_workdir(
                root, fingerprint, "not-a-generation"
            )

    def test_main_uses_single_lease_without_local_memory_admission_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report = {
                "schema_version": board_vcs.SCHEMA_VERSION,
                "status": "fail",
                "phase": "preflight",
                "errors": ["expected test failure"],
            }
            lease = {"purpose": "exact_board_vcs_controller", "status": "active"}
            with patch.object(
                board_vcs,
                "heavy_job_lease",
                return_value=contextlib.nullcontext(lease),
            ), patch.object(board_vcs, "execute", return_value=report) as execute:
                exit_code = board_vcs.main(["--run-dir", str(run_dir)])

            persisted = json.loads(
                (
                    run_dir
                    / "verification"
                    / "vcs"
                    / "case_board_vcs_functional.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 1)
        execute.assert_called_once_with(run_dir.resolve(), 0)
        self.assertEqual(persisted["heavy_job_lease"]["status"], "released")
        self.assertNotIn("resource_admission", persisted)

    def test_supplemental_jsonl_outputs_are_discovered_without_case_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            testbench = Path(temp_dir) / "board_tb.sv"
            testbench.write_text(
                """
module board_tb;
  initial begin
    progress_fd = $fopen("reports/progress_event_log.jsonl", "w");
    probe_fd = $fopen("reports/custom_payload_probe.jsonl", "w");
    // ignored_fd = $fopen("reports/comment_only.jsonl", "w");
    unsafe_fd = $fopen("../outside.jsonl", "w");
  end
endmodule
""",
                encoding="utf-8",
            )

            paths = board_vcs.supplemental_jsonl_output_paths(
                testbench,
                {Path("reports/progress_event_log.jsonl")},
            )

        self.assertEqual(paths, [Path("reports/custom_payload_probe.jsonl")])

    def test_supplemental_jsonl_summary_preserves_bounded_scalar_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "probe.jsonl"
            rows = [
                {
                    "schema_version": "example.probe.v1",
                    "probe_id": "probe.payload",
                    "probe_revision": 7,
                    "sequence": index,
                    "simulation_time": 100,
                    "same_time_index": index,
                    "stage0": {"valid": 1, "ready": 0},
                }
                for index in range(5)
            ]
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )

            summary = board_vcs.summarize_supplemental_jsonl(path)

        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["record_count"], 5)
        self.assertEqual(summary["probe_revisions"], [7])
        self.assertEqual(summary["last_scalar_record"]["same_time_index"], 4)
        self.assertEqual(summary["last_scalar_record"]["stage0.valid"], 1)
        self.assertEqual(summary["last_scalar_record"]["stage0.ready"], 0)

    def test_boundary_trace_summary_accepts_jsonl_and_keeps_current_dag_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            semantic = root / "semantic.json"
            semantic.write_text(
                json.dumps(
                    {
                        "single_layer": {
                            "pipeline_overlap_contract": {
                                "contract_sha256": "a" * 64,
                                "trace_contract_sha256": "b" * 64,
                                "required_boundaries": ["edge.input"],
                                "boundary_contracts": [
                                    {
                                        "boundary_id": "edge.input",
                                        "src_stage": "block_input",
                                        "dst_stage": "stage_a",
                                    }
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            trace = root / "trace.jsonl"
            trace.write_text(
                json.dumps(
                    {
                        "boundary_id": "boundary.edge_input",
                        "cycle": 10,
                        "observed_value": {
                            "valid": 1,
                            "ready": 1,
                            "fire": 1,
                            "accepted_count": 1,
                            "current_payload_digest": "abcd",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            summary = board_vcs.summarize_boundary_trace_observations(
                trace,
                {"path": str(semantic)},
                {"source_id": "tb", "sha256": "c" * 64},
            )

        self.assertEqual(summary["status"], "complete")
        self.assertEqual(summary["required_boundary_count"], 1)
        self.assertEqual(
            summary["boundary_summaries"][0]["last_accepted_payload_digest"],
            "abcd",
        )

    def test_boundary_trace_summary_includes_internal_vcs_log_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            semantic = root / "semantic.json"
            semantic.write_text(
                json.dumps(
                    {
                        "single_layer": {
                            "pipeline_overlap_contract": {
                                "contract_sha256": "a" * 64,
                                "trace_contract_sha256": "b" * 64,
                                "required_boundaries": ["edge.norm.to.attention"],
                                "boundary_contracts": [
                                    {
                                        "boundary_id": "edge.norm.to.attention",
                                        "src_stage": "norm",
                                        "dst_stage": "attention",
                                    }
                                ],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            trace = root / "trace.jsonl"
            trace.write_text("", encoding="utf-8")
            simulation_log = root / "simulation.log"
            simulation_log.write_text(
                "SPATIALACC_PIPELINE_TRACE "
                "boundary=edge.norm.to.attention cycle= 42 token= 3 beat= 7 "
                "st=0 last=1 valid=1 ready=1\n",
                encoding="utf-8",
            )
            summary = board_vcs.summarize_boundary_trace_observations(
                trace,
                {"path": str(semantic)},
                {"source_id": "tb", "sha256": "c" * 64},
                simulation_log,
            )

        self.assertEqual(summary["simulation_log_trace_record_count"], 1)
        self.assertEqual(summary["observed_boundary_count"], 1)
        record = summary["boundary_summaries"][0]["last_accepted_record"]
        self.assertEqual(record["token"], 3)
        self.assertTrue(record["fire"])

    def test_bounded_supplemental_vcd_is_discovered_and_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            testbench = Path(temp_dir) / "board_tb.sv"
            testbench.write_text(
                """
module board_tb;
  initial begin
    $dumpfile("reports/core_probe.vcd");
    $dumplimit(33554432);
    $dumpvars(1, dut.core);
  end
endmodule
""",
                encoding="utf-8",
            )
            paths = board_vcs.supplemental_vcd_output_paths(testbench)
            vcd = Path(temp_dir) / "core_probe.vcd"
            vcd.write_text(
                "$timescale 1 ps $end\n$scope module core $end\n"
                "$var wire 1 ! clock $end\n$enddefinitions $end\n"
                "#100\n0!\n#104\n1!\n",
                encoding="utf-8",
            )
            summary = board_vcs.summarize_supplemental_vcd(vcd)

        self.assertEqual(paths, [Path("reports/core_probe.vcd")])
        self.assertEqual(summary["timescale"], "1 ps")
        self.assertEqual(summary["last_timestamp"], 104)
        self.assertTrue(summary["simulation_time_advanced"])

    def test_unbounded_supplemental_vcd_is_not_discovered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            testbench = Path(temp_dir) / "board_tb.sv"
            testbench.write_text(
                'module board_tb; initial $dumpfile("reports/unbounded.vcd"); endmodule\n',
                encoding="utf-8",
            )

            paths = board_vcs.supplemental_vcd_output_paths(testbench)

        self.assertEqual(paths, [])

    def test_zero_time_recovery_binds_only_to_exact_vcs_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            live_dir = run_dir / "verification" / "vcs" / "live"
            fingerprint = "f" * 64
            remote_workdir = "/remote/exact-job"
            evidence = {
                "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                "status": "proven_zero_time_livelock",
                "remote_workdir": remote_workdir,
                "remote_pid": 123,
                "last_cycle": 456,
                "fixed_wall_clock_timeout": False,
                "fixed_cycle_timeout": False,
            }
            termination = {
                "schema_version": "spatialaccagent.zero_time_livelock_termination.v1",
                "status": "pass",
                "remote_exit_code": board_vcs.ZERO_TIME_LIVELOCK_EXIT_CODE,
                "remote_pid": 123,
                "remote_workdir": remote_workdir,
                "fixed_wall_clock_timeout": False,
                "fixed_cycle_timeout": False,
                "evidence": evidence,
            }
            write_json(
                live_dir / "live_progress.json",
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "zero_time_livelock_evidence": evidence,
                },
            )
            fresh_failure = {
                "status": "fail",
                "returncode": board_vcs.ZERO_TIME_LIVELOCK_EXIT_CODE,
                "failure_class": "zero_time_simulation_livelock",
                "remote_workdir": remote_workdir,
                "zero_time_livelock_evidence": evidence,
                "zero_time_livelock_termination": termination,
            }
            persisted = board_vcs.persist_zero_time_livelock_recovery(
                run_dir,
                fresh_failure,
                remote_workdir=remote_workdir,
                input_fingerprint_sha256=fingerprint,
            )
            remote_failure = {
                "status": "fail",
                "returncode": board_vcs.ZERO_TIME_LIVELOCK_EXIT_CODE,
                "failure_class": "remote_tool_failure",
                "remote_workdir": remote_workdir,
            }

            bound = board_vcs.bind_zero_time_livelock_recovery(
                run_dir,
                remote_failure,
                remote_workdir=remote_workdir,
                input_fingerprint_sha256=fingerprint,
            )
            mismatched = board_vcs.bind_zero_time_livelock_recovery(
                run_dir,
                remote_failure,
                remote_workdir=remote_workdir,
                input_fingerprint_sha256="0" * 64,
            )

        self.assertTrue(persisted)
        self.assertEqual(bound["failure_class"], "zero_time_simulation_livelock")
        self.assertEqual(bound["zero_time_livelock_evidence"], evidence)
        self.assertNotIn("transport", bound["zero_time_livelock_termination"])
        self.assertEqual(mismatched, remote_failure)

    def test_zero_time_recovery_rejects_mismatch_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            live_dir = run_dir / "verification" / "vcs" / "live"
            fingerprint = "f" * 64
            remote_workdir = "/remote/exact-job"
            evidence = {
                "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                "status": "proven_zero_time_livelock",
                "remote_workdir": remote_workdir,
            }
            termination = {
                "schema_version": "spatialaccagent.zero_time_livelock_termination.v1",
                "status": "pass",
                "remote_exit_code": board_vcs.ZERO_TIME_LIVELOCK_EXIT_CODE,
                "remote_workdir": remote_workdir,
                "evidence": evidence,
            }
            recovery_path = live_dir / "zero_time_livelock_recovery.json"
            write_json(
                live_dir / "live_progress.json",
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "zero_time_livelock_evidence": evidence,
                },
            )
            valid_result = {
                "status": "fail",
                "returncode": board_vcs.ZERO_TIME_LIVELOCK_EXIT_CODE,
                "remote_workdir": remote_workdir,
                "zero_time_livelock_evidence": evidence,
                "zero_time_livelock_termination": termination,
            }
            self.assertTrue(
                board_vcs.persist_zero_time_livelock_recovery(
                    run_dir,
                    valid_result,
                    remote_workdir=remote_workdir,
                    input_fingerprint_sha256=fingerprint,
                )
            )
            original = recovery_path.read_text(encoding="utf-8")

            mismatched = copy.deepcopy(valid_result)
            mismatched["remote_workdir"] = "/remote/other-job"
            persisted = board_vcs.persist_zero_time_livelock_recovery(
                run_dir,
                mismatched,
                remote_workdir="/remote/other-job",
                input_fingerprint_sha256="0" * 64,
            )

            self.assertFalse(persisted)
            self.assertEqual(recovery_path.read_text(encoding="utf-8"), original)

    def test_checkpoint_hook_source_requires_executable_native_capture_hook(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            testbench_path = Path(temp_dir) / "board_tb.sv"
            testbench_path.write_text(
                "// SPATIALACC_NATIVE_CHECKPOINT_CAPTURE\n"
                "/* SPATIALACC_NATIVE_CHECKPOINT_READY */\n",
                encoding="utf-8",
            )
            manifest = checkpoint_ready_manifest()
            manifest["testbench"]["sole_dut_instance"] = "dut"

            errors = board_vcs.checkpoint_hook_source_errors(
                manifest, testbench_path, checkpoint_required=True
            )

        self.assertTrue(any("lacks native capture plusarg" in row for row in errors))
        self.assertTrue(any("lacks native capture ready marker" in row for row in errors))
        self.assertTrue(any("no executable $stop" in row for row in errors))

    def test_checkpoint_hook_source_accepts_native_capture_hook(self) -> None:
        source = """module board_tb;
initial begin
  if ($test$plusargs("SPATIALACC_NATIVE_CHECKPOINT_CAPTURE")) begin
    $display("SPATIALACC_NATIVE_CHECKPOINT_READY");
    $stop;
  end
end
endmodule
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            testbench_path = Path(temp_dir) / "board_tb.sv"
            testbench_path.write_text(source, encoding="utf-8")
            manifest = checkpoint_ready_manifest()
            manifest["testbench"]["sole_dut_instance"] = "dut"

            errors = board_vcs.checkpoint_hook_source_errors(
                manifest, testbench_path, checkpoint_required=True
            )

        self.assertEqual(errors, [])

    def test_checkpoint_hook_source_rejects_incomplete_native_hook(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            testbench_path = Path(temp_dir) / "board_tb.sv"
            testbench_path.write_text(
                "module board_tb; initial begin\n"
                "  if ($test$plusargs(\"SPATIALACC_NATIVE_CHECKPOINT_CAPTURE\"))\n"
                "    $display(\"SPATIALACC_NATIVE_CHECKPOINT_READY\");\n"
                "end endmodule\n",
                encoding="utf-8",
            )
            manifest = checkpoint_ready_manifest()
            manifest["testbench"]["sole_dut_instance"] = "other_dut"

            errors = board_vcs.checkpoint_hook_source_errors(
                manifest, testbench_path, checkpoint_required=True
            )

        self.assertTrue(any("no executable $stop" in row for row in errors))

    def test_invalid_checkpoint_request_requires_repair_before_vcs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            manifest = checkpoint_ready_manifest()
            manifest["testbench"] = {}
            request = cold_checkpoint_request(checkpoint_ready_manifest())
            request_path = run_dir / "verification" / "simulation_checkpoints" / "requests" / "current.json"
            write_json(request_path, request)

            plan = board_vcs.checkpoint_execution_plan(
                run_dir,
                manifest,
                {
                    "SPATIALACC_CHECKPOINT_REPLAY": "1",
                    "SPATIALACC_CHECKPOINT_REQUEST": str(request_path),
                },
            )

        self.assertEqual(plan["status"], "pass")
        self.assertEqual(plan["mode"], "cold_capture")
        self.assertTrue(plan["enabled"])
        self.assertNotIn("checkpoint_failure_is_nonblocking", plan)

    def test_stage3_repair_rejects_disabled_checkpoint_before_remote_start(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()

            plan = board_vcs.checkpoint_execution_plan(
                run_dir,
                checkpoint_ready_manifest(),
                {"SPATIALACC_CHECKPOINT_REQUIRED": "1"},
            )

        self.assertEqual(plan["status"], "fail")
        self.assertFalse(plan["enabled"])
        self.assertTrue(plan["required_for_stage3_repair"])
        self.assertTrue(
            any("Layer-3 replay requires a checkpoint request" in row for row in plan["errors"])
        )

    def test_fast_replay_uses_capture_request_without_rewriting_its_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            manifest = checkpoint_ready_manifest()
            request = cold_checkpoint_request(manifest)
            request_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "requests"
                / "capture.json"
            )
            write_json(request_path, request)
            checkpoint_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "checkpoint-1"
                / "manifest.json"
            )
            write_json(
                checkpoint_path,
                {
                    "checkpoint_id": "checkpoint-1",
                    "request_sha256": request["request_sha256"],
                    "execution_identity": request["execution_identity"],
                },
            )
            validation = {
                "status": "ready",
                "remote_workdir": "/remote/replay",
                "simulator_path": "vcs_work/simv",
                "checkpoint_manifest": str(checkpoint_path),
            }
            with patch.object(
                board_vcs,
                "read_fast_replay_state",
                return_value={"checkpoint_id": "checkpoint-1"},
            ), patch.object(
                board_vcs,
                "validate_fast_replay_state",
                return_value=validation,
            ), patch.object(board_vcs, "checkpoint_manifest_errors", return_value=[]):
                plan = board_vcs.checkpoint_execution_plan(
                    run_dir,
                    manifest,
                    {
                        "SPATIALACC_CHECKPOINT_REPLAY": "1",
                        "SPATIALACC_CHECKPOINT_REQUEST": str(request_path),
                        "SPATIALACC_FAST_REPLAY": "1",
                    },
                )

        self.assertEqual(plan["status"], "pass")
        self.assertEqual(plan["mode"], "native_exact_model")
        self.assertTrue(plan["fast_replay"]["used"])
        self.assertEqual(
            plan["request"]["replay_decision"]["mode"], "cold_capture"
        )
        self.assertEqual(board_vcs.checkpoint_runtime_plusargs(plan), [])

    def test_fixed_checkpoint_cut_uses_only_the_fixed_cut_plusarg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            manifest = checkpoint_ready_manifest()
            request = fixed_checkpoint_request(manifest)
            request_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "requests"
                / "fixed.json"
            )
            write_json(request_path, request)
            plan = board_vcs.checkpoint_execution_plan(
                run_dir,
                manifest,
                {
                    "SPATIALACC_CHECKPOINT_REPLAY": "1",
                    "SPATIALACC_CHECKPOINT_REQUEST": str(request_path),
                },
            )
            plusargs = board_vcs.checkpoint_runtime_plusargs(plan)
            equivalence_plusargs = board_vcs.checkpoint_equivalence_runtime_plusargs(
                plan
            )

        self.assertEqual(plan["status"], "pass")
        self.assertEqual(plusargs, ["+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE"])
        self.assertEqual(equivalence_plusargs, [])

    def test_native_checkpoint_scripts_wait_for_the_real_testbench_cut(self) -> None:
        capture = board_vcs.native_checkpoint_capture_tcl().splitlines()
        restore = board_vcs.native_checkpoint_restore_tcl().splitlines()

        self.assertEqual(capture[0], "run")
        self.assertEqual(
            capture[:3],
            ["run", "run 0", "save checkpoint/native_state"],
        )
        self.assertNotIn("run 100s", capture)
        self.assertEqual(restore[-2], "run")
        self.assertIn("restore checkpoint/native_state", restore)
        self.assertNotIn("run 100s", restore)

    def test_saved_replay_rebinds_testbench_observation_logs(self) -> None:
        command, outputs, errors = board_vcs.saved_replay_command(
            {
                "simulate_command": (
                    "mkdir -p reports; ./vcs_work/simv "
                    "+INPUT=artifacts/input.memh "
                    "+WEIGHT_IMAGE=artifacts/weights.bin "
                    "+RUNTIME_IMAGE=artifacts/runtime.bin "
                    "+SPATIALACC_OBSERVATION_SELECTION=observation/old.json "
                    "+EXPECTED_OUTPUT=artifacts/expected.memh"
                )
            },
            {"simulator_path": "vcs_work/simv"},
        )

        self.assertEqual(errors, [])
        self.assertEqual(outputs["restore_log"], Path("reports/fast_replay_restore.log"))
        self.assertIn("+SPATIALACC_NATIVE_CHECKPOINT_RESTORE", command)
        self.assertIn("+INPUT=artifacts/input.memh", command)
        self.assertNotIn("observation/old.json", command)
        self.assertEqual(command.count("+SPATIALACC_OBSERVATION_SELECTION="), 1)
        self.assertIn(
            "+SPATIALACC_OBSERVATION_SELECTION=observation/current_selection.json",
            command,
        )
        self.assertNotIn("SPATIALACC_NATIVE_CHECKPOINT_CAPTURE", command)

    def test_fast_replay_uploads_the_latest_runtime_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            selection = (
                run_dir
                / "verification"
                / "adaptive_observation"
                / "current_selection.json"
            )
            write_json(
                selection,
                {
                    "schema_version": "spatialaccagent.runtime_observation_selection.v1",
                    "status": "ready",
                    "decision_sha256": "f" * 64,
                    "selected_signals": [{"expression": "dut.core.out_valid"}],
                },
            )
            calls: list[list[str]] = []

            def transfer(argv: list[str], timeout_sec: int):
                calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(board_vcs, "run_transfer_command", side_effect=transfer):
                result = board_vcs.upload_current_observation_selection(
                    run_dir,
                    host="vcs.example",
                    port=22,
                    remote_dir="/remote/exact-job",
                    timeout_sec=0,
                )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][0], "scp")
        self.assertEqual(Path(calls[1][-2]), selection)
        self.assertEqual(
            calls[1][-1],
            "vcs.example:/remote/exact-job/observation/current_selection.json",
        )

    def test_saved_recapture_reuses_workload_without_old_checkpoint_arguments(self) -> None:
        command, outputs, errors = board_vcs.saved_recapture_command(
            {
                "simulate_command": (
                    "mkdir -p reports; ./vcs_work/simv -ucli -do checkpoint/old.tcl "
                    "+INPUT=artifacts/input.memh +WEIGHT_IMAGE=artifacts/weights.bin "
                    "+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE "
                    "+SPATIALACC_CHECKPOINT_MODE=cold_capture > reports/simulation.log 2>&1"
                )
            },
            {"simulator_path": "vcs_work/simv"},
        )

        self.assertEqual(errors, [])
        self.assertEqual(outputs["capture_log"], Path("reports/fast_replay_recapture.log"))
        self.assertIn("./vcs_work/simv -ucli -do checkpoint/ucli_capture.tcl", command)
        self.assertIn("+INPUT=artifacts/input.memh", command)
        self.assertIn("+WEIGHT_IMAGE=artifacts/weights.bin", command)
        self.assertIn("+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE", command)
        self.assertNotIn("checkpoint/old.tcl", command)
        self.assertNotIn("+SPATIALACC_CHECKPOINT_MODE=cold_capture", command)

    def test_recapture_bypasses_pending_job_and_full_compile_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            expected = {"status": "checkpoint_capture_complete"}
            with patch.dict(
                "os.environ", {"SPATIALACC_FAST_REPLAY_RECAPTURE": "1"}, clear=False
            ), patch.object(
                board_vcs, "execute_saved_fast_recapture", return_value=expected
            ) as recapture, patch.object(
                board_vcs, "pending_exact_board_job"
            ) as pending, patch.object(board_vcs, "validate_manifest") as validate:
                result = board_vcs.execute(run_dir, 0)

        self.assertEqual(result["status"], expected["status"])
        recapture.assert_called_once_with(run_dir, 0)
        pending.assert_not_called()
        validate.assert_not_called()

    def test_completed_pending_job_reaches_full_collection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report_path = (
                run_dir
                / "verification"
                / "vcs"
                / "case_board_vcs_functional.json"
            )
            write_json(
                report_path,
                {
                    "input_fingerprint_sha256": "a" * 64,
                    "phase": "active_exact_job_collection",
                    "failure_class": (
                        "active_exact_job_terminal_acceptance_required"
                    ),
                },
            )
            pending_job = {
                "job": {"input_fingerprint_sha256": "a" * 64},
                "job_path": run_dir / "job.json",
                "manifest_path": run_dir / "manifest.json",
            }
            with patch.object(
                board_vcs, "pending_exact_board_job", return_value=pending_job
            ), patch.object(
                board_vcs, "write_pending_exact_board_job_report"
            ) as write_pending, patch.object(
                board_vcs, "execute_pending_exact_board_job"
            , return_value={"status": "pass", "phase": "active_exact_job_collection"}
            ) as attach, patch.object(
                board_vcs,
                "validate_manifest",
                return_value=(
                    {},
                    {
                        "exact_board_preflight": {},
                        "evidence": {},
                        "weight_binding_evidence": {},
                    },
                    ["stop after collection handoff"],
                ),
            ):
                result = board_vcs.execute(run_dir, 0)

        self.assertEqual(result["phase"], "active_exact_job_collection")
        write_pending.assert_not_called()
        attach.assert_called_once_with(run_dir, 0, pending_job)

    def test_fixed_cut_testbench_has_weight_accept_trigger(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "accagent"
            / "runs"
            / "spatialacc_qwen_agent_fast_run"
            / "generated"
            / "board_integration"
            / "spatialacc_exact_board_multilayer_tb.sv"
        ).read_text(encoding="utf-8")
        self.assertIn("SPATIALACC_NATIVE_CHECKPOINT_CAPTURE", source)
        self.assertIn("SPATIALACC_NATIVE_CHECKPOINT_READY", source)
        self.assertIn("dut.weight_last_q === 1'b1", source)
        self.assertIn("kernel_input_accept_total == 0", source)

    def test_fast_replay_does_not_attach_an_old_pending_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            resolved = {
                "exact_board_preflight": {},
                "evidence": {},
                "weight_binding_evidence": {},
            }
            with patch.dict(
                "os.environ", {"SPATIALACC_FAST_REPLAY": "1"}, clear=False
            ), patch.object(board_vcs, "pending_exact_board_job") as pending, patch.object(
                board_vcs,
                "validate_manifest",
                return_value=({}, resolved, ["stop after pending-job check"]),
            ):
                result = board_vcs.execute(run_dir, 0)

        pending.assert_not_called()
        self.assertEqual(result["phase"], "fast_replay_validation")

    def test_restore_check_bypasses_current_manifest_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            expected = {
                "status": "checkpoint_restore_complete",
                "phase": "fast_replay_restore_check",
            }
            with patch.dict(
                "os.environ",
                {
                    "SPATIALACC_FAST_REPLAY": "1",
                    "SPATIALACC_FAST_REPLAY_RESTORE_CHECK": "1",
                },
                clear=False,
            ), patch.object(
                board_vcs,
                "execute_saved_fast_replay",
                return_value=expected,
            ) as replay, patch.object(board_vcs, "validate_manifest") as validate:
                result = board_vcs.execute(run_dir, 0)

        self.assertEqual(result["status"], expected["status"])
        self.assertEqual(result["phase"], expected["phase"])
        replay.assert_called_once_with(run_dir, 0)
        validate.assert_not_called()

    def test_capture_completion_immediately_requests_restore_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            request_path = board_vcs.fast_replay_request_path(run_dir)
            request_path.parent.mkdir(parents=True)
            request_path.write_text("{}\n", encoding="utf-8")
            state = {
                "status": "captured",
                "verified": False,
            }
            with patch.object(
                board_vcs,
                "read_fast_replay_state",
                return_value=state,
            ):
                env = board_vcs.automatic_restore_check_environment(
                    run_dir,
                    {"status": "checkpoint_capture_complete"},
                )

        self.assertEqual(env["SPATIALACC_FAST_REPLAY"], "1")
        self.assertEqual(env["SPATIALACC_FAST_REPLAY_RESTORE_CHECK"], "1")
        self.assertEqual(env["SPATIALACC_CHECKPOINT_REQUEST"], str(request_path))

    def test_restore_result_does_not_start_another_automatic_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            "os.environ",
            {"SPATIALACC_FAST_REPLAY_RESTORE_CHECK": "1"},
            clear=False,
        ):
            env = board_vcs.automatic_restore_check_environment(
                Path(temp_dir),
                {"status": "checkpoint_capture_complete"},
            )

        self.assertEqual(env, {})

    def test_optional_checkpoint_contract_never_blocks_cold_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            manifest = checkpoint_ready_manifest()
            manifest["testbench"]["simulation_checkpoint_contract"][
                "status"
            ] = "broken"

            ordinary = board_vcs.checkpoint_execution_plan(
                run_dir,
                manifest,
                {},
            )
            final_cold = board_vcs.checkpoint_execution_plan(
                run_dir,
                manifest,
                {"SPATIALACC_CHECKPOINT_FINAL_COLD": "1"},
            )

        self.assertEqual(ordinary["status"], "pass")
        self.assertEqual(ordinary["mode"], "disabled")
        self.assertFalse(ordinary["enabled"])
        self.assertEqual(ordinary["errors"], [])
        self.assertNotIn("nonblocking_checkpoint_diagnostics", ordinary)
        self.assertEqual(final_cold["status"], "pass")
        self.assertEqual(final_cold["mode"], "full_cold_acceptance")
        self.assertEqual(final_cold["errors"], [])
        self.assertNotIn("nonblocking_checkpoint_diagnostics", final_cold)

    def test_checkpoint_plan_binds_request_to_current_model_and_plusargs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            manifest = checkpoint_ready_manifest()
            request = cold_checkpoint_request(manifest)
            request_path = run_dir / "verification" / "simulation_checkpoints" / "requests" / "current.json"
            write_json(request_path, request)

            plan = board_vcs.checkpoint_execution_plan(
                run_dir,
                manifest,
                {
                    "SPATIALACC_CHECKPOINT_REPLAY": "1",
                    "SPATIALACC_CHECKPOINT_REQUEST": str(request_path),
                },
            )
            stage_dir = run_dir / "verification" / "board_simulation" / "vcs_stage"
            staged = board_vcs.stage_checkpoint_inputs(plan, stage_dir)
            plusargs = board_vcs.checkpoint_runtime_plusargs(plan)
            equivalence_plusargs = (
                board_vcs.checkpoint_equivalence_runtime_plusargs(plan)
            )
            no_frontier_plan = json.loads(json.dumps(plan))
            no_frontier_plan["request"]["semantic_cut"].pop(
                "frontier_id",
                None,
            )
            no_frontier_plusargs = board_vcs.checkpoint_runtime_plusargs(
                no_frontier_plan
            )
            no_frontier_equivalence_plusargs = (
                board_vcs.checkpoint_equivalence_runtime_plusargs(
                    no_frontier_plan
                )
            )
            elaboration_args = board_vcs.checkpoint_adapter_elaboration_args(
                plan,
                stage_dir,
                Path("vcs_work"),
            )
            vlogan_defines = board_vcs.checkpoint_adapter_compile_define_args(
                plan,
                "vlogan",
            )
            vcs_defines = board_vcs.checkpoint_adapter_compile_define_args(
                plan,
                "/tools/vcs/bin/vcs",
            )

        self.assertEqual(plan["status"], "pass")
        self.assertEqual(plan["mode"], "cold_capture")
        self.assertFalse(plan["adapter_enabled"])
        self.assertFalse(plan["candidate_screening"])
        self.assertEqual(staged, [])
        self.assertEqual(plusargs, ["+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE"])
        self.assertEqual(equivalence_plusargs, [])
        self.assertEqual(no_frontier_plusargs, ["+SPATIALACC_NATIVE_CHECKPOINT_CAPTURE"])
        self.assertEqual(no_frontier_equivalence_plusargs, [])
        self.assertEqual(vlogan_defines, [])
        self.assertEqual(vcs_defines, [])
        self.assertEqual(elaboration_args, [])

    def test_full_cold_still_compiles_declared_checkpoint_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            plan = board_vcs.checkpoint_execution_plan(
                run_dir,
                checkpoint_ready_manifest(),
                {"SPATIALACC_CHECKPOINT_FINAL_COLD": "1"},
            )

        self.assertEqual(plan["status"], "pass")
        self.assertEqual(plan["mode"], "full_cold_acceptance")
        self.assertFalse(plan["enabled"])
        self.assertFalse(plan["adapter_enabled"])

    def test_framework_checkpoint_manifest_keeps_replay_screening_nonaccepting(self) -> None:
        manifest = checkpoint_ready_manifest()
        request = cold_checkpoint_request(manifest)
        plan = {
            "mode": "cold_capture",
            "request": request,
            "request_sha256": request["request_sha256"],
            "execution_identity": request["execution_identity"],
        }
        report = {
            "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
            "status": "pass",
            "mode": "cold_capture",
            "captured_sequence": 10,
            "captured_cycle": 100,
            "state_artifacts": [
                {
                    "path": "checkpoint/native_state",
                    "remote_path": "checkpoint/native_state",
                    "remote_files_path": "checkpoint/native_state.FILES",
                    "kind": "native_vcs_snapshot",
                },
            ],
        }

        errors = board_vcs.checkpoint_capture_report_errors(plan, report)
        checkpoint_manifest = board_vcs.framework_checkpoint_manifest(
            plan,
            report,
            [
                {
                    "path": "native_state",
                    "remote_path": "checkpoint/native_state",
                    "remote_files_path": "checkpoint/native_state.FILES",
                    "kind": "native_vcs_snapshot",
                    "byte_count": 0,
                },
            ],
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            checkpoint_manifest["state_artifacts"][0]["kind"],
            "native_vcs_snapshot",
        )
        self.assertEqual(checkpoint_manifest["remote_acknowledgment_status"], "pending")

    def test_native_capture_ignores_legacy_vpi_fields(
        self,
    ) -> None:
        manifest = checkpoint_ready_manifest()
        request = cold_checkpoint_request(manifest)
        plan = {
            "mode": "cold_capture",
            "request": request,
            "request_sha256": request["request_sha256"],
            "execution_identity": request["execution_identity"],
        }
        report = {
            "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
            "status": "pass",
            "mode": "cold_capture",
            "captured_sequence": 10,
            "captured_cycle": 100,
            "state_artifacts": [{"kind": "native_vcs_snapshot", "remote_path": "checkpoint/native_state"}],
        }
        rows = [
            {
                "path": "native_state",
                "remote_path": "checkpoint/native_state",
                "remote_files_path": "checkpoint/native_state.FILES",
                "kind": "native_vcs_snapshot",
            },
        ]

        checkpoint_manifest = board_vcs.framework_checkpoint_manifest(
            plan,
            report,
            rows,
        )

        self.assertEqual(checkpoint_manifest["status"], "pass")
        self.assertTrue(checkpoint_manifest["checkpoint_id"])
        self.assertEqual(
            [row["kind"] for row in checkpoint_manifest["state_artifacts"]],
            ["native_vcs_snapshot"],
        )

    def test_semantic_suffix_materialization_is_compact_and_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "progress.jsonl"
            destination = root / "suffix.jsonl"
            rows = [
                progress_event(1, "semantic_progress", True),
                progress_event(2, "heartbeat", False),
                progress_event(3, "semantic_progress", True),
            ]
            source.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            source_bytes = source.stat().st_size
            result = board_vcs.materialize_checkpoint_semantic_suffix(
                source,
                destination,
                anchor_sequence=2,
                anchor_cycle=0,
            )
            persisted = [
                json.loads(line)
                for line in destination.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(result["status"], "pass")
        self.assertEqual([row["sequence"] for row in persisted], [3])
        self.assertLess(result["byte_count"], source_bytes)

    def test_semantic_suffix_materialization_preserves_invalid_record_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "restored_progress.jsonl"
            destination = root / "suffix.jsonl"
            raw = (
                b'{"sequence":10,"cycle":100,"semantic_progress":true,'
                b'"event_kind":"semantic_progress","output_valid":x}\n'
            )
            source.write_bytes(raw)

            result = board_vcs.materialize_checkpoint_semantic_suffix(
                source,
                destination,
                anchor_sequence=10,
                anchor_cycle=100,
            )
            destination_exists = destination.exists()

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["invalid_record_count"], 1)
        self.assertIn('"output_valid":x', result["invalid_records"][0]["raw_preview"])
        self.assertFalse(destination_exists)

    def test_pending_calibration_requires_current_content_addressed_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_manifest = checkpoint_ready_manifest()
            request = cold_checkpoint_request(board_manifest)
            capture = {
                "schema_version": CHECKPOINT_CAPTURE_REPORT_SCHEMA_VERSION,
                "status": "pass",
                "mode": "cold_capture",
                "request_sha256": request["request_sha256"],
                "semantic_cut_sha256": request["semantic_cut"]["cut_sha256"],
                "checkpoint_trigger_observed": True,
                "portable_state_capsule_complete": True,
                "complete_dut_state_captured": True,
                "complete_testbench_external_state_captured": True,
                "evidence_flushed_before_capture": True,
                "external_state_quiescent_at_capture": True,
                "pending_event_queue_empty_at_capture": True,
                "axi_read": {"outstanding": 0, "pending_response": False},
                "axi_write": {"outstanding": 0, "pending_response": False},
                "active_boundary_observation": {"event_queue_quiescent": True},
                "captured_sequence": 10,
                "captured_cycle": 100,
            }
            payloads = {
                "dut_vpi_state": b"dut",
                "dut_vpi_schema": b"schema",
                "testbench_external_state": b"external",
            }
            rows = []
            for index, (kind, payload) in enumerate(payloads.items()):
                digest = hashlib.sha256(payload).hexdigest()
                rows.append(
                    {
                        "path": f"state/{index:04d}_{kind}.bin",
                        "kind": kind,
                        "sha256": digest,
                        "byte_count": len(payload),
                    }
                )
                if kind == "dut_vpi_schema":
                    capture["state_schema"] = {"sha256": digest}
            plan = {
                "mode": "cold_capture",
                "request": request,
                "request_sha256": request["request_sha256"],
                "execution_identity": request["execution_identity"],
            }
            checkpoint_manifest = board_vcs.framework_checkpoint_manifest(
                plan,
                capture,
                rows,
                remote_workdir="/remote/exact-job",
            )
            checkpoint_manifest["remote_acknowledgment_status"] = "pass"
            checkpoint_id = checkpoint_manifest["checkpoint_id"]
            checkpoint_dir = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / checkpoint_id
            )
            for row, payload in zip(rows, payloads.values()):
                path = checkpoint_dir / row["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
            write_json(checkpoint_dir / "manifest.json", checkpoint_manifest)
            write_json(
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json",
                board_manifest,
            )
            fingerprint = "9" * 64
            runner_path = (
                run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
            )
            write_json(
                runner_path,
                {
                    "status": "fail",
                    "phase": "remote_vcs",
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": "/remote/exact-job",
                    "checkpoint_artifacts": {
                        "status": "pass",
                        "mode": "cold_capture",
                        "checkpoint_id": checkpoint_id,
                        "manifest": str(checkpoint_dir / "manifest.json"),
                        "equivalence_status": None,
                    },
                },
            )
            write_json(
                run_dir
                / "verification"
                / "board_simulation"
                / "vcs_stage"
                / board_vcs.REMOTE_SEMANTIC_JOB_CONTRACT,
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": "/remote/exact-job",
                },
            )

            pending = board_vcs.pending_same_source_checkpoint_calibration(run_dir)
            board_manifest["source_closure_sha256"] = "0" * 64
            write_json(
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json",
                board_manifest,
            )
            stale = board_vcs.pending_same_source_checkpoint_calibration(run_dir)

        self.assertIsNone(pending)
        self.assertIsNone(stale)

    def test_equivalence_oracle_terminates_at_first_missing_cold_event(self) -> None:
        expected = progress_event(11, "semantic_progress", True)
        expected["cycle"] = 200
        heartbeat = progress_event(12, "heartbeat", False)
        heartbeat["cycle"] = 201
        contract = {
            "same_source_equivalence_oracle": {
                "status": "ready",
                "capture_sequence": 10,
                "capture_cycle": 100,
                "cold_terminal_cycle": 300,
                "expected_semantic_records": [expected],
                "oracle_sha256": "a" * 64,
                "cold_progress_sha256": "b" * 64,
            }
        }

        missing = adaptive_semantic_stall_evidence([heartbeat], contract)
        matched = adaptive_semantic_stall_evidence(
            [expected, {**heartbeat, "cycle": 300}],
            contract,
        )

        self.assertEqual(missing["status"], "proven_semantic_stall")
        self.assertTrue(missing["same_source_equivalence_divergence"])
        self.assertEqual(missing["proof_mode"], "same_source_equivalence_oracle")
        self.assertEqual(matched["status"], "proven_semantic_stall")
        self.assertFalse(matched["same_source_equivalence_divergence"])
        self.assertTrue(matched["cold_terminal_match_candidate"])

    def test_equivalence_oracle_is_built_from_executed_cold_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            progress_path = Path(temp_dir) / "cold.jsonl"
            before = progress_event(9, "semantic_progress", True)
            before["cycle"] = 90
            after = progress_event(11, "semantic_progress", True)
            after["cycle"] = 200
            progress_path.write_text(
                json.dumps(before) + "\n" + json.dumps(after) + "\n",
                encoding="utf-8",
            )
            contract = board_vcs.same_source_equivalence_progress_contract(
                {},
                progress_path,
                {"captured_sequence": 10, "captured_cycle": 100},
                {
                    "returncode": 86,
                    "failure_class": "adaptive_semantic_stall",
                    "adaptive_semantic_stall_evidence": {"latest_cycle": 300},
                },
            )

        oracle = contract["same_source_equivalence_oracle"]
        self.assertEqual(oracle["status"], "ready")
        self.assertEqual(oracle["expected_semantic_record_count"], 1)
        self.assertEqual(oracle["expected_semantic_records"][0]["cycle"], 200)
        self.assertEqual(oracle["cold_terminal_cycle"], 300)

    def test_calibration_failure_projection_is_acyclic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner_path = root / "runner.json"
            manifest_path = root / "manifest.json"
            runner_path.write_text("{}\n", encoding="utf-8")
            manifest_path.write_text("{}\n", encoding="utf-8")
            report = {
                "phase": "remote_vcs",
                "checkpoint_artifacts": {
                    "status": "fail",
                    "runtime_execution_failure": {"status": "stale"},
                    "failure_class": (
                        "simulation_checkpoint_restore_equivalence_failed"
                    ),
                    "errors": ["suffix differs"],
                },
                "checkpoint_same_source_calibration": {"status": "fail"},
            }
            manifest = {
                "checkpoint_id": "checkpoint",
                "request_sha256": "a" * 64,
                "semantic_cut": {
                    "cut_sha256": "b" * 64,
                    "trigger": {"cycle": 100},
                },
                "capture_report": {
                    "status": "pass",
                    "checkpoint_trigger_observed": True,
                    "captured_sequence": 10,
                    "captured_cycle": 100,
                },
            }
            projection = (
                board_vcs.same_source_checkpoint_calibration_failure_projection(
                    report,
                    manifest,
                    runner_report_path=runner_path,
                    checkpoint_manifest_path=manifest_path,
                )
            )
            report["checkpoint_artifacts"]["runtime_execution_failure"] = projection
            serialized = json.dumps(report)

        self.assertEqual(projection["status"], "ready")
        self.assertIn("factual_same_source_restore", serialized)
        self.assertNotIn(
            "runtime_execution_failure", projection["checkpoint_artifacts"]
        )

    def test_current_calibration_failure_materialization_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            runner_path = (
                run_dir
                / "verification"
                / "vcs"
                / "case_board_vcs_functional.json"
            )
            checkpoint_dir = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "checkpoint-id"
            )
            checkpoint_manifest_path = checkpoint_dir / "manifest.json"
            board_manifest = {}
            execution_identity = board_vcs.simulation_execution_identity(
                board_manifest
            )
            checkpoint_manifest = {
                "checkpoint_id": "checkpoint-id",
                "request_sha256": "a" * 64,
                "execution_identity": execution_identity,
                "semantic_cut": {
                    "cut_sha256": "b" * 64,
                    "trigger": {"cycle": 100},
                },
                "capture_report": {
                    "status": "pass",
                    "checkpoint_trigger_observed": True,
                    "captured_sequence": 10,
                    "captured_cycle": 100,
                },
            }
            runner = {
                "phase": "remote_vcs",
                "input_fingerprint_sha256": "c" * 64,
                "remote_workdir": "/remote/exact-job",
                "checkpoint_artifacts": {
                    "status": "fail",
                    "manifest": str(checkpoint_manifest_path),
                    "failure_class": (
                        "simulation_checkpoint_restore_equivalence_failed"
                    ),
                    "errors": ["live witnesses differ"],
                },
                "checkpoint_same_source_calibration": {
                    "status": "fail",
                    "equivalence_report": {
                        "status": "fail",
                        "errors": ["live witnesses differ"],
                        "live_state_witness_diff": {
                            "status": "different",
                            "field_differences": [
                                {
                                    "path": "/scheduler_state",
                                    "cold": 30,
                                    "restored": 0,
                                }
                            ],
                        },
                    },
                },
            }
            write_json(board_manifest_path, board_manifest)
            write_json(checkpoint_manifest_path, checkpoint_manifest)
            write_json(runner_path, runner)

            first = board_vcs.materialize_current_checkpoint_calibration_failure(
                run_dir
            )
            first_sha256 = board_vcs.sha256_file(runner_path)
            second = board_vcs.materialize_current_checkpoint_calibration_failure(
                run_dir
            )
            second_sha256 = board_vcs.sha256_file(runner_path)

        self.assertIsNotNone(first)
        self.assertEqual(first, second)
        self.assertEqual(first_sha256, second_sha256)
        self.assertRegex(first["failure_identity_sha256"], r"^[0-9a-f]{64}$")

    def test_runtime_failure_evidence_is_bounded_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "restore.log"
            lines = [f"noise-{index}" for index in range(60)]
            lines.extend(
                [
                    "SPATIALACC_CHECKPOINT_RESTORE_PASS root=tb.dut states=8",
                    "Fatal: restored checkpoint boundary record differs at field one",
                    "Error: restored checkpoint boundary record differs at field two",
                    "Fatal: restored checkpoint boundary record differs at field three",
                    "$finish at simulation time 100",
                ]
            )
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            expected_sha256 = board_vcs.sha256_file(path)

            evidence = board_vcs.simulation_runtime_failure_evidence(
                path,
                max_tail_lines=8,
                max_matched_lines=2,
            )

        self.assertEqual(evidence["status"], "observed")
        self.assertEqual(evidence["sha256"], expected_sha256)
        self.assertEqual(len(evidence["tail_lines"]), 8)
        self.assertEqual(len(evidence["matched_lines"]), 2)
        self.assertTrue(evidence["matched_lines_truncated"])
        self.assertTrue(evidence["tail_lines_truncated"])
        self.assertTrue(
            any("boundary record differs" in line for line in evidence["matched_lines"])
        )
        self.assertEqual(len(evidence["checkpoint_markers"]), 1)
        self.assertEqual(len(evidence["termination_markers"]), 1)

    def test_checkpoint_pass_marker_is_not_runtime_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "restore.log"
            path.write_text(
                "SPATIALACC_CHECKPOINT_RESTORE_PASS root=tb.dut states=8\n"
                "$finish at simulation time 100\n",
                encoding="utf-8",
            )

            evidence = board_vcs.simulation_runtime_failure_evidence(path)

        self.assertEqual(evidence["status"], "not_observed")
        self.assertEqual(evidence["matched_lines"], [])
        self.assertEqual(len(evidence["checkpoint_markers"]), 1)
        self.assertEqual(len(evidence["termination_markers"]), 1)

    def test_terminal_log_fatal_overrides_successful_simulator_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text(
                "Fatal: monitor.sv, 211: AXI protocol violation\n"
                "SPATIALACC_AXI_PROTOCOL_VIOLATION\n"
                "$finish at simulation time 100\n",
                encoding="utf-8",
            )

            result = board_vcs.apply_simulation_terminal_log_result(
                {
                    "status": "pass",
                    "returncode": 0,
                    "remote_state": "done",
                },
                path,
            )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(
            result["failure_class"], "simulator_reported_terminal_failure"
        )
        self.assertTrue(result["terminal_log_failure_overrode_successful_exit"])
        self.assertEqual(result["runtime_failure_evidence"]["status"], "observed")

    def test_simulator_segmentation_fault_is_runtime_crash_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            crash_line = (
                "An unexpected termination has occurred in ./vcs_work/simv "
                "due to a signal: Segmentation fault"
            )
            path.write_text(
                f"semantic progress\n{crash_line}\nDumping VCS Annotated Stack:\n",
                encoding="utf-8",
            )

            evidence = board_vcs.simulation_runtime_failure_evidence(path)

        self.assertEqual(evidence["status"], "observed")
        self.assertEqual(evidence["failure_lines"], [])
        self.assertEqual(evidence["simulator_crash_lines"], [crash_line])
        self.assertEqual(evidence["matched_lines"], [crash_line])

    def test_termination_provenance_classifies_simulator_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text(
                "An unexpected termination has occurred in ./vcs_work/simv "
                "due to a signal: Segmentation fault\n",
                encoding="utf-8",
            )
            provenance = board_vcs.simulation_termination_provenance(
                {
                    "status": "fail",
                    "returncode": 1,
                    "failure_class": "remote_tool_failure",
                    "remote_state": "done",
                    "runner_process_provenance": {
                        "status": "observed",
                        "attribution": "runner_owned_nonzero_process_exit",
                        "last_running_process_snapshot": {
                            "simulator_like_process_observed": True,
                            "simulator_process_commands": ["simv"],
                        },
                        "last_simulator_process_commands": ["simv"],
                    },
                },
                path,
                timeout_sec=0,
                progress_summary={
                    "terminal_event_seen": False,
                    "last_cycle": 20788597,
                    "policy": {},
                },
                input_fingerprint_sha256="c" * 64,
            )

        classification = provenance["causal_classification"]
        self.assertEqual(classification["classification"], "simulator_process_crash")
        self.assertTrue(classification["simulator_infrastructure_failure_proven"])
        self.assertFalse(
            classification["deterministic_hdl_or_testbench_failure_proven"]
        )
        self.assertFalse(classification["source_semantic_repair_eligible"])

    def test_termination_provenance_allows_repair_for_proven_pipeline_stall(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text("semantic progress stopped\n", encoding="utf-8")
            provenance = board_vcs.simulation_termination_provenance(
                {
                    "status": "fail",
                    "returncode": 86,
                    "failure_class": "adaptive_semantic_stall",
                    "remote_state": "done",
                    "adaptive_semantic_stall_evidence": {
                        "status": "proven_semantic_stall",
                        "intra_layer_pipeline_violation_evidence": {
                            "status": "proven_pipeline_violation",
                        },
                    },
                    "adaptive_semantic_stall_termination": {
                        "status": "pass",
                    },
                },
                path,
                timeout_sec=0,
                progress_summary={
                    "terminal_event_seen": False,
                    "last_cycle": 4096,
                    "last_committed_progress_event": {
                        "active_boundary_observation": {
                            "input_ready": 0,
                            "output_ready": 1,
                            "output_valid": 0,
                            "output_accept_count": 0,
                        }
                    },
                    "policy": {},
                },
                input_fingerprint_sha256="d" * 64,
            )

        classification = provenance["causal_classification"]
        self.assertEqual(
            provenance["termination_source"],
            "framework_adaptive_semantic_stall_termination",
        )
        self.assertEqual(
            classification["classification"], "proven_semantic_pipeline_stall"
        )
        self.assertTrue(classification["source_semantic_repair_eligible"])

    def test_termination_provenance_requires_internal_boundary_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text("semantic progress stopped\n", encoding="utf-8")
            provenance = board_vcs.simulation_termination_provenance(
                {
                    "status": "fail",
                    "returncode": 86,
                    "failure_class": "adaptive_semantic_stall",
                    "remote_state": "done",
                    "adaptive_semantic_stall_evidence": {
                        "status": "proven_semantic_stall",
                        "intra_layer_pipeline_violation_evidence": {
                            "status": "proven_pipeline_violation",
                        },
                    },
                    "adaptive_semantic_stall_termination": {
                        "status": "pass",
                    },
                },
                path,
                timeout_sec=0,
                progress_summary={
                    "terminal_event_seen": False,
                    "last_cycle": 4096,
                    "policy": {},
                },
                input_fingerprint_sha256="e" * 64,
            )

        classification = provenance["causal_classification"]
        self.assertEqual(
            classification["classification"],
            "external_or_unattributed_termination",
        )
        self.assertFalse(classification["source_semantic_repair_eligible"])

    def test_termination_provenance_binds_process_log_and_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text(
                "cycle 4096\nFatal: exact-board runtime stopped\n",
                encoding="utf-8",
            )
            provenance = board_vcs.simulation_termination_provenance(
                {
                    "status": "fail",
                    "returncode": 1,
                    "failure_class": "remote_tool_failure",
                    "remote_state": "done",
                    "duration_sec": 17.5,
                },
                path,
                timeout_sec=0,
                progress_summary={
                    "terminal_event_seen": False,
                    "last_cycle": 4096,
                    "policy": {
                        "fixed_cycle_timeout": False,
                        "cycle_limit": None,
                    },
                },
                input_fingerprint_sha256="a" * 64,
            )

        self.assertEqual(provenance["status"], "complete")
        self.assertEqual(
            provenance["termination_source"], "nonzero_process_exit"
        )
        self.assertEqual(
            provenance["simulator_terminal_log"]["status"], "observed"
        )
        self.assertIn("exact-board runtime stopped", provenance["raw_terminal_log_tail"])
        self.assertTrue(provenance["wall_clock_budget"]["unbounded"])
        self.assertEqual(provenance["cycle_budget"]["last_observed_cycle"], 4096)
        self.assertEqual(
            provenance["missing_completion_reports_causal_classification"],
            "process_ended_before_terminal_event",
        )
        self.assertEqual(
            provenance["exact_source_replay_fingerprint_sha256"], "a" * 64
        )

    def test_termination_provenance_preserves_runner_owned_signal_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text("last simulator heartbeat\n", encoding="utf-8")
            provenance = board_vcs.simulation_termination_provenance(
                {
                    "status": "fail",
                    "returncode": 139,
                    "failure_class": "remote_tool_failure",
                    "remote_state": "done",
                    "runner_process_provenance": {
                        "attribution": (
                            "runner_owned_simulator_process_signal_exit"
                        ),
                        "last_running_process_snapshot": {
                            "simulator_like_process_observed": True,
                            "processes": [{"pid": 75, "command": "simv"}],
                        },
                    },
                },
                path,
                timeout_sec=0,
                progress_summary={
                    "terminal_event_seen": False,
                    "last_committed_progress_event": {
                        "event": "stage0_complete",
                        "cycle": 4096,
                    },
                    "policy": {},
                },
                input_fingerprint_sha256="b" * 64,
            )

        self.assertEqual(
            provenance["termination_source"],
            "runner_owned_simulator_signal_exit",
        )
        self.assertEqual(provenance["signal_number"], 11)
        self.assertEqual(
            provenance["causal_classification"]["classification"],
            "runner_owned_simulator_signal_exit_unattributed",
        )
        self.assertFalse(
            provenance["causal_classification"][
                "deterministic_hdl_or_testbench_failure_proven"
            ]
        )
        self.assertEqual(
            provenance["final_committed_progress_event"]["event"],
            "stage0_complete",
        )

    def test_fresh_transfer_target_removes_stale_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "nested" / "restore_report.json"
            path.parent.mkdir(parents=True)
            path.write_text('{"request_sha256":"stale"}\n', encoding="utf-8")

            board_vcs._prepare_fresh_transfer_target(path)

            self.assertFalse(path.exists())
            self.assertTrue(path.parent.is_dir())

    def test_inline_cold_equivalence_failure_projects_for_agent_routing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner_path = root / "runner.json"
            manifest_path = root / "manifest.json"
            runner_path.write_text("{}\n", encoding="utf-8")
            manifest_path.write_text("{}\n", encoding="utf-8")
            report = {
                "phase": "remote_vcs",
                "checkpoint_artifacts": {
                    "status": "fail",
                    "failure_class": (
                        "simulation_checkpoint_restore_equivalence_failed"
                    ),
                    "errors": ["restored suffix differs"],
                    "equivalence_execution": {
                        "status": "pass",
                        "same_compiled_simulator_reused": True,
                        "second_vcs_compile_was_not_launched": True,
                        "serial_execution": True,
                    },
                },
            }
            manifest = {
                "checkpoint_id": "checkpoint",
                "request_sha256": "a" * 64,
                "semantic_cut": {
                    "cut_sha256": "b" * 64,
                    "trigger": {"cycle": 100},
                },
                "capture_report": {
                    "status": "pass",
                    "checkpoint_trigger_observed": True,
                    "captured_sequence": 10,
                    "captured_cycle": 100,
                },
                "equivalence_attempt": {
                    "schema_version": (
                        "spatialaccagent.simulation_checkpoint_equivalence.v1"
                    ),
                    "status": "fail",
                    "producer": "framework",
                    "request_sha256": "a" * 64,
                    "semantic_cut_sha256": "b" * 64,
                    "errors": ["restored suffix differs"],
                    "restore_runtime_failure_evidence": {
                        "schema_version": (
                            "spatialaccagent.simulation_runtime_failure_evidence.v1"
                        ),
                        "status": "observed",
                        "matched_lines": [
                            "Fatal: restored checkpoint boundary record differs"
                        ],
                    },
                },
            }
            projection = (
                board_vcs.same_source_checkpoint_calibration_failure_projection(
                    report,
                    manifest,
                    runner_report_path=runner_path,
                    checkpoint_manifest_path=manifest_path,
                )
            )

        self.assertEqual(projection["status"], "ready")
        calibration = projection["same_source_calibration"]
        self.assertEqual(calibration["status"], "fail")
        self.assertEqual(
            calibration["source"],
            "inline_cold_capture_serial_same_source_equivalence",
        )
        self.assertTrue(calibration["second_vcs_compile_was_not_launched"])
        self.assertEqual(
            projection["restore_runtime_failure_evidence"]["status"],
            "observed",
        )
        self.assertIn(
            "boundary record differs",
            projection["restore_runtime_failure_evidence"]["matched_lines"][0],
        )

    def test_projection_recovers_schema_bound_restored_runtime_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_dir = root / "checkpoints" / "checkpoint"
            schema_path = checkpoint_dir / "state" / "dut_state.schema"
            schema_path.parent.mkdir(parents=True)
            schema_path.write_text(
                "schema_version=spatialaccagent.vcs_vpi_state_schema.v1\n"
                "state_count=1\n"
                "fnv1a64=0123456789abcdef\n",
                encoding="utf-8",
            )
            restored_log = root / "restored" / "vcs_simulation.log"
            restored_log.parent.mkdir(parents=True)
            restored_log.write_text(
                "SPATIALACC_CHECKPOINT_RESTORE_PASS root=tb.dut states=1 "
                "schema=0123456789abcdef\n"
                "Fatal: restored checkpoint boundary record differs from live "
                "factual state\n",
                encoding="utf-8",
            )
            restored_progress = root / "restored" / "progress_event_log.jsonl"
            restored_progress.write_bytes(
                b'{"sequence":10,"cycle":100,"semantic_progress":true,'
                b'"event_kind":"semantic_progress","output_valid":x}\n'
            )
            runner_path = root / "runner.json"
            manifest_path = checkpoint_dir / "manifest.json"
            runner_path.write_text("{}\n", encoding="utf-8")
            manifest_path.write_text("{}\n", encoding="utf-8")
            remote_workdir = "/remote/current-job"
            report = {
                "phase": "remote_vcs",
                "remote_workdir": remote_workdir,
                "checkpoint_artifacts": {
                    "status": "fail",
                    "failure_class": (
                        "simulation_checkpoint_restore_equivalence_failed"
                    ),
                    "errors": ["restore report is missing"],
                    "equivalence_execution": {
                        "status": "pass",
                        "same_compiled_simulator_reused": True,
                        "second_vcs_compile_was_not_launched": True,
                        "serial_execution": True,
                        "simulation": {
                            "status": "fail",
                            "failure_class": "adaptive_semantic_stall",
                            "remote_job_preserved": False,
                            "adaptive_semantic_stall_evidence": {
                                "status": "proven_semantic_stall"
                            },
                            "adaptive_semantic_stall_termination": {
                                "status": "pass"
                            },
                            "remote_workdir": remote_workdir,
                        },
                    },
                },
            }
            manifest = {
                "checkpoint_id": "checkpoint",
                "remote_workdir": remote_workdir,
                "request_sha256": "a" * 64,
                "semantic_cut": {
                    "cut_sha256": "b" * 64,
                    "trigger": {"cycle": 100},
                },
                "capture_report": {
                    "status": "pass",
                    "checkpoint_trigger_observed": True,
                    "captured_sequence": 10,
                    "captured_cycle": 100,
                },
                "state_artifacts": [
                    {
                        "kind": "dut_vpi_schema",
                        "path": "state/dut_state.schema",
                        "sha256": board_vcs.sha256_file(schema_path),
                    }
                ],
                "equivalence_attempt": {
                    "schema_version": (
                        "spatialaccagent.simulation_checkpoint_equivalence.v1"
                    ),
                    "status": "fail",
                    "producer": "framework",
                    "request_sha256": "a" * 64,
                    "semantic_cut_sha256": "b" * 64,
                    "errors": ["restore report is missing"],
                },
            }
            projection = (
                board_vcs.same_source_checkpoint_calibration_failure_projection(
                    report,
                    manifest,
                    runner_report_path=runner_path,
                    checkpoint_manifest_path=manifest_path,
                    restored_simulation_log_path=restored_log,
                    restored_progress_event_log_path=restored_progress,
                )
            )
            evidence = projection["restore_runtime_failure_evidence"]
            self.assertEqual(evidence["status"], "observed")
            self.assertEqual(evidence["binding"]["checkpoint_id"], "checkpoint")
            self.assertEqual(evidence["binding"]["remote_workdir"], remote_workdir)
            self.assertIn("boundary record differs", evidence["matched_lines"][-1])
            self.assertTrue(Path(evidence["path"]).is_file())
            materialization = projection[
                "restored_semantic_suffix_materialization"
            ]
            self.assertEqual(materialization["status"], "fail")
            self.assertEqual(materialization["invalid_record_count"], 1)
            self.assertIn(
                '"output_valid":x',
                materialization["invalid_records"][0]["raw_preview"],
            )

    def test_projection_rejects_runtime_failure_with_schema_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_dir = root / "checkpoint"
            schema_path = checkpoint_dir / "state" / "dut_state.schema"
            schema_path.parent.mkdir(parents=True)
            schema_path.write_text(
                "fnv1a64=0123456789abcdef\n",
                encoding="utf-8",
            )
            restored_log = root / "vcs_simulation.log"
            restored_log.write_text(
                "SPATIALACC_CHECKPOINT_RESTORE_PASS schema=fedcba9876543210\n"
                "Fatal: stale failure\n",
                encoding="utf-8",
            )
            remote_workdir = "/remote/current-job"
            report = {
                "remote_workdir": remote_workdir,
                "checkpoint_artifacts": {
                    "status": "fail",
                    "failure_class": (
                        "simulation_checkpoint_restore_equivalence_failed"
                    ),
                    "equivalence_execution": {
                        "status": "pass",
                        "same_compiled_simulator_reused": True,
                        "second_vcs_compile_was_not_launched": True,
                        "serial_execution": True,
                        "simulation": {
                            "status": "pass",
                            "remote_workdir": remote_workdir,
                        },
                    },
                },
            }
            manifest = {
                "checkpoint_id": "checkpoint",
                "remote_workdir": remote_workdir,
                "request_sha256": "a" * 64,
                "semantic_cut": {
                    "cut_sha256": "b" * 64,
                    "trigger": {"cycle": 100},
                },
                "capture_report": {
                    "status": "pass",
                    "checkpoint_trigger_observed": True,
                },
                "state_artifacts": [
                    {
                        "kind": "dut_vpi_schema",
                        "path": "state/dut_state.schema",
                        "sha256": board_vcs.sha256_file(schema_path),
                    }
                ],
                "equivalence_attempt": {
                    "status": "fail",
                    "producer": "framework",
                    "request_sha256": "a" * 64,
                    "semantic_cut_sha256": "b" * 64,
                },
            }
            projection = (
                board_vcs.same_source_checkpoint_calibration_failure_projection(
                    report,
                    manifest,
                    runner_report_path=root / "runner.json",
                    checkpoint_manifest_path=checkpoint_dir / "manifest.json",
                    restored_simulation_log_path=restored_log,
                )
            )

        self.assertEqual(projection["restore_runtime_failure_evidence"], {})

    def test_equivalence_finalize_restores_cold_outputs_even_when_archive_is_incomplete(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "reports" / "progress.jsonl"
            report.parent.mkdir(parents=True)
            report.write_text("cold\n", encoding="utf-8")
            prepare = board_vcs.checkpoint_equivalence_archive_command(
                [Path("reports/progress.jsonl")],
                destination=Path("checkpoint/equivalence/cold_outputs"),
            )
            prepared = subprocess.run(
                ["bash", "-lc", prepare],
                cwd=root,
                check=False,
                capture_output=True,
            )
            report.write_text("restored\n", encoding="utf-8")
            finalize = board_vcs.checkpoint_equivalence_restore_cold_command(
                [
                    Path("reports/progress.jsonl"),
                    Path("reports/missing.json"),
                ]
            )
            finalized = subprocess.run(
                ["bash", "-lc", finalize],
                cwd=root,
                check=False,
                capture_output=True,
            )
            restored_content = report.read_text(encoding="utf-8")

        self.assertEqual(prepared.returncode, 0)
        self.assertEqual(finalized.returncode, 0)
        self.assertEqual(restored_content, "cold\n")

    def test_checkpoint_calibration_reattaches_existing_job_without_relaunch(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            board_vcs,
            "remote_background_job_state",
            return_value={
                "certainty": "determinate",
                "state": "running",
                "pid": 123,
            },
        ), patch.object(
            board_vcs,
            "wait_for_existing_remote_job",
            return_value={"status": "pass", "returncode": 0},
        ) as wait_existing, patch.object(
            board_vcs,
            "run_remote_background_command",
        ) as launch:
            result = board_vcs.run_or_recover_remote_command(
                host="builder",
                port=22,
                command="./simv",
                remote_dir="/remote/job",
                cwd=Path(temp_dir),
                timeout_sec=0,
                label="vcs_checkpoint_equivalence_simulate",
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["recovered_existing_job"])
        wait_existing.assert_called_once()
        launch.assert_not_called()

    def test_checkpoint_is_acknowledged_only_after_remote_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest_path = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "checkpoint-id"
                / "manifest.json"
            )
            write_json(
                manifest_path,
                {
                    "checkpoint_id": "checkpoint-id",
                    "created_at_unix_sec": 1,
                    "total_state_bytes": 1,
                    "remote_acknowledgment_status": "pending",
                    "remote_workdir": "/remote/job",
                    "semantic_cut": {"frontier_id": "output"},
                    "storage_policy": {
                        "max_checkpoint_count": 3,
                        "max_checkpoint_bytes": 1024,
                    },
                },
            )
            report = {
                "remote_workdir": "/remote/job",
                "checkpoint_artifacts": {
                    "status": "pass",
                    "mode": "cold_capture",
                    "manifest": str(manifest_path),
                },
            }

            pending = board_vcs.acknowledge_checkpoint_after_remote_persistence(
                run_dir,
                report,
                {"status": "fail"},
            )
            acknowledged = (
                board_vcs.acknowledge_checkpoint_after_remote_persistence(
                    run_dir,
                    report,
                    {"status": "pass", "receipt_sha256": "a" * 64},
                )
            )

        self.assertEqual(pending.get("remote_acknowledgment_status"), None)
        self.assertEqual(acknowledged["remote_acknowledgment_status"], "pass")

    def test_live_progress_observer_commits_only_complete_jsonl_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            remote_fixture.write_text(
                json.dumps(progress_event(0, "semantic_progress", True))
                + "\n"
                + json.dumps(progress_event(1, "heartbeat", False))
                + "\n"
                + '{"schema_version":',
                encoding="utf-8",
            )
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
            )

            def transfer(argv: list[str], timeout_sec: int):
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(board_vcs, "run_transfer_command", side_effect=transfer):
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 1,
                        "remote_workdir": "/remote/exact-job",
                        "process_snapshot": {
                            "simulator_like_process_observed": True,
                            "simulator_process_commands": ["simv"],
                        },
                    }
                )

            report = observer.report()

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["latest"]["record_count"], 2)
        self.assertEqual(report["latest"]["semantic_progress_event_count"], 1)
        self.assertGreater(report["latest"]["trailing_partial_byte_count"], 0)
        self.assertTrue(
            report["latest"]["policy"]["observer_never_terminates_the_remote_job"]
        )
        self.assertEqual(report["latest"]["live_transfer"]["mode"], "full_snapshot")
        self.assertEqual(
            report["latest"]["last_committed_progress_event"]["event_kind"],
            "heartbeat",
        )
        self.assertEqual(
            report["latest"]["testbench_observation_activity"][
                "testbench_observation_process"
            ],
            "simulator_process",
        )

    def test_live_progress_observer_reuses_matching_proven_stall_without_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_workdir = "/remote/exact-job"
            fingerprint = "f" * 64
            live_dir = run_dir / "verification" / "vcs" / "live"
            write_json(
                live_dir / "live_progress.json",
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "adaptive_semantic_stall_evidence": {
                        "status": "proven_semantic_stall"
                    },
                },
            )
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint=fingerprint,
            )

            with patch.object(board_vcs, "run_transfer_command") as transfer, patch.object(
                board_vcs, "run_stream_transfer_command"
            ) as stream_transfer:
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 1,
                        "remote_workdir": remote_workdir,
                    }
                )
                observer(
                    {
                        "state": "done",
                        "pid": None,
                        "poll_attempt": 2,
                        "remote_workdir": remote_workdir,
                    }
                )

            report = observer.report()

        transfer.assert_not_called()
        stream_transfer.assert_not_called()
        self.assertEqual(
            report["latest"]["adaptive_semantic_stall_evidence"]["status"],
            "proven_semantic_stall",
        )

    def test_live_progress_observer_appends_only_new_bytes_while_running(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            first_payload = json.dumps(progress_event(0, "semantic_progress", True)) + "\n"
            appended_payload = (
                json.dumps(progress_event(1, "heartbeat", False))
                + "\n"
                + '{"schema_version":'
            )
            remote_fixture.write_text(first_payload, encoding="utf-8")
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
            )
            full_transfers: list[list[str]] = []
            incremental_offsets: list[int] = []

            def transfer(argv: list[str], timeout_sec: int):
                full_transfers.append(argv)
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            def transfer_increment(
                argv: list[str], destination: Path, timeout_sec: int
            ) -> subprocess.CompletedProcess[str]:
                offset_match = board_vcs.re.search(r"tail -c \+(\d+)", argv[-1])
                self.assertIsNotNone(offset_match)
                offset = int(offset_match.group(1)) - 1
                incremental_offsets.append(offset)
                destination.write_bytes(remote_fixture.read_bytes()[offset:])
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(board_vcs, "run_transfer_command", side_effect=transfer), patch.object(
                board_vcs,
                "run_stream_transfer_command",
                side_effect=transfer_increment,
            ):
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 1,
                        "remote_workdir": "/remote/exact-job",
                    }
                )
                remote_fixture.write_text(first_payload + appended_payload, encoding="utf-8")
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 4,
                        "remote_workdir": "/remote/exact-job",
                    }
                )

            report = observer.report()

        self.assertEqual(len(full_transfers), 1)
        self.assertEqual(incremental_offsets, [len(first_payload.encode("utf-8"))])
        self.assertEqual(report["latest"]["record_count"], 2)
        self.assertGreater(report["latest"]["trailing_partial_byte_count"], 0)
        self.assertEqual(report["latest"]["live_transfer"]["mode"], "incremental_append")
        self.assertEqual(
            report["latest"]["live_transfer"]["received_byte_count"],
            len(appended_payload.encode("utf-8")),
        )

    def test_live_progress_observer_epoch_excludes_pre_restore_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            old_payload = json.dumps(progress_event(0, "semantic_progress", True)) + "\n"
            current_payload = json.dumps(progress_event(1, "heartbeat", False)) + "\n"
            remote_fixture.write_text(old_payload + current_payload, encoding="utf-8")
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
            )
            observer.begin_epoch(
                "/remote/exact-job",
                remote_start_byte=len(old_payload.encode("utf-8")),
                signal_start_bytes={
                    Path("reports/progress_events.jsonl"): len(
                        old_payload.encode("utf-8")
                    ),
                    Path("reports/boundary_trace.jsonl"): 99,
                },
                signal_start_metadata={
                    Path("reports/progress_events.jsonl"): {
                        "device": 1,
                        "inode": 7,
                        "byte_count": len(old_payload.encode("utf-8")),
                    }
                },
            )
            requested_offsets: list[int] = []

            def stream_transfer(
                argv: list[str], destination: Path, timeout_sec: int
            ) -> subprocess.CompletedProcess[str]:
                offset_match = board_vcs.re.search(r"tail -c \+(\d+)", argv[-1])
                self.assertIsNotNone(offset_match)
                offset = int(offset_match.group(1)) - 1
                requested_offsets.append(offset)
                destination.write_bytes(remote_fixture.read_bytes()[offset:])
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(
                board_vcs, "run_stream_transfer_command", side_effect=stream_transfer
            ):
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 1,
                        "remote_workdir": "/remote/exact-job",
                    }
                )

            report = observer.report()

        self.assertEqual(requested_offsets, [len(old_payload.encode("utf-8"))])
        self.assertEqual(report["latest"]["record_count"], 1)
        self.assertEqual(report["latest"]["last_cycle"], 2)
        self.assertEqual(report["latest"]["live_transfer"]["mode"], "epoch_suffix")
        self.assertEqual(
            report["latest"]["observation_epoch"]["signal_start_bytes"],
            {
                "reports/boundary_trace.jsonl": 99,
                "reports/progress_events.jsonl": len(old_payload.encode("utf-8")),
            },
        )

    def test_live_progress_observer_reads_new_file_after_restore_recreates_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            old_payload = json.dumps(progress_event(0, "semantic_progress", True)) + "\n"
            current_payload = json.dumps(progress_event(1, "heartbeat", False)) + "\n"
            remote_fixture.write_text(current_payload, encoding="utf-8")
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
            )
            observer.begin_epoch(
                "/remote/exact-job",
                remote_start_byte=len(old_payload.encode("utf-8")),
                signal_start_bytes={
                    Path("reports/progress_events.jsonl"): len(
                        old_payload.encode("utf-8")
                    )
                },
                signal_start_metadata={
                    Path("reports/progress_events.jsonl"): {
                        "device": 1,
                        "inode": 7,
                        "byte_count": len(old_payload.encode("utf-8")),
                    }
                },
            )

            def transfer(argv: list[str], timeout_sec: int):
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(
                board_vcs,
                "remote_file_metadata",
                return_value={"device": 1, "inode": 8, "byte_count": len(current_payload)},
            ), patch.object(board_vcs, "run_transfer_command", side_effect=transfer):
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 1,
                        "remote_workdir": "/remote/exact-job",
                    }
                )

            report = observer.report()

        self.assertEqual(report["latest"]["record_count"], 1)
        self.assertTrue(
            report["latest"]["observation_epoch"]["progress_file_recreated"]
        )
        self.assertEqual(report["latest"]["live_transfer"]["mode"], "full_snapshot")

    def test_live_progress_observer_does_not_infer_zero_time_from_progress_alone(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            remote_fixture.write_text(
                json.dumps(progress_event(0, "semantic_progress", True)) + "\n",
                encoding="utf-8",
            )
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
            )

            def full_transfer(argv: list[str], timeout_sec: int):
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            def empty_increment(
                argv: list[str], destination: Path, timeout_sec: int
            ) -> subprocess.CompletedProcess[str]:
                destination.write_bytes(b"")
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(board_vcs, "run_transfer_command", side_effect=full_transfer), patch.object(
                board_vcs,
                "run_stream_transfer_command",
                side_effect=empty_increment,
            ):
                for poll_attempt in (1, 4, 8, 12):
                    observer(
                        {
                            "state": "running",
                            "pid": 123,
                            "poll_attempt": poll_attempt,
                            "remote_workdir": "/remote/exact-job",
                        }
                    )

            evidence = observer.report()["zero_time_livelock_evidence"]

        self.assertEqual(evidence, {})

    def test_live_progress_observer_requires_native_loop_and_static_vcd_time(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            remote_fixture.write_text(
                json.dumps(progress_event(0, "semantic_progress", True)) + "\n",
                encoding="utf-8",
            )
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
                remote_time_probe_paths=[Path("reports/core_probe.vcd")],
                native_loop_report_path=Path("reports/simulation.log"),
            )

            def full_transfer(argv: list[str], timeout_sec: int):
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            def stream_transfer(
                argv: list[str], destination: Path, timeout_sec: int
            ) -> subprocess.CompletedProcess[str]:
                command = argv[-1]
                if "core_probe.vcd" in command:
                    destination.write_bytes(b"#100\n0!\n#104\n1!\n")
                elif "simulation.log" in command:
                    destination.write_text(
                        "delta-cycles exceeded the threshold-limit.\n"
                        "Possible zero delay loop(s).\n",
                        encoding="utf-8",
                    )
                else:
                    destination.write_bytes(b"")
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(
                board_vcs, "run_transfer_command", side_effect=full_transfer
            ), patch.object(
                board_vcs,
                "run_stream_transfer_command",
                side_effect=stream_transfer,
            ):
                for poll_attempt in (1, 4, 8, 12):
                    observer(
                        {
                            "state": "running",
                            "pid": 123,
                            "poll_attempt": poll_attempt,
                            "remote_workdir": "/remote/exact-job",
                        }
                    )

            evidence = observer.report()["zero_time_livelock_evidence"]

        self.assertEqual(evidence["status"], "proven_zero_time_livelock")
        self.assertEqual(evidence["simulation_time_watermark"], 104)
        self.assertEqual(evidence["consecutive_unchanged_running_snapshots"], 3)

    def test_live_progress_observer_does_not_stop_while_vcd_time_advances(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            remote_fixture.write_text(
                json.dumps(progress_event(0, "semantic_progress", True)) + "\n",
                encoding="utf-8",
            )
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
                remote_time_probe_paths=[Path("reports/core_probe.vcd")],
                native_loop_report_path=Path("reports/simulation.log"),
            )
            vcd_probe_count = 0

            def full_transfer(argv: list[str], timeout_sec: int):
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            def stream_transfer(
                argv: list[str], destination: Path, timeout_sec: int
            ) -> subprocess.CompletedProcess[str]:
                nonlocal vcd_probe_count
                command = argv[-1]
                if "core_probe.vcd" in command:
                    vcd_probe_count += 1
                    destination.write_text(
                        f"#100\n0!\n#{100 + vcd_probe_count}\n1!\n",
                        encoding="utf-8",
                    )
                elif "simulation.log" in command:
                    destination.write_text(
                        "Possible zero delay loop(s).\n", encoding="utf-8"
                    )
                else:
                    destination.write_bytes(b"")
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(
                board_vcs, "run_transfer_command", side_effect=full_transfer
            ), patch.object(
                board_vcs,
                "run_stream_transfer_command",
                side_effect=stream_transfer,
            ):
                for poll_attempt in (1, 4, 8, 12, 16):
                    observer(
                        {
                            "state": "running",
                            "pid": 123,
                            "poll_attempt": poll_attempt,
                            "remote_workdir": "/remote/exact-job",
                        }
                    )

            report = observer.report()

        self.assertEqual(report["zero_time_livelock_evidence"], {})
        self.assertEqual(report["latest"]["simulation_time_probe"]["last_timestamp"], 105)

    def test_live_progress_observer_replaces_incremental_copy_when_job_is_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            remote_fixture = Path(temp_dir) / "remote_progress.jsonl"
            remote_fixture.write_text(
                json.dumps(progress_event(0, "semantic_progress", True)) + "\n",
                encoding="utf-8",
            )
            observer = board_vcs.LiveProgressObserver(
                host="vcs.example",
                port=22,
                run_dir=run_dir,
                remote_path=Path("reports/progress_events.jsonl"),
                fingerprint="f" * 64,
            )
            full_transfer_count = 0

            def transfer(argv: list[str], timeout_sec: int):
                nonlocal full_transfer_count
                full_transfer_count += 1
                destination = Path(argv[-1])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(remote_fixture.read_bytes())
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(board_vcs, "run_transfer_command", side_effect=transfer):
                observer(
                    {
                        "state": "running",
                        "pid": 123,
                        "poll_attempt": 1,
                        "remote_workdir": "/remote/exact-job",
                    }
                )
                remote_fixture.write_text(
                    remote_fixture.read_text(encoding="utf-8")
                    + json.dumps(progress_event(1, "terminal", False))
                    + "\n",
                    encoding="utf-8",
                )
                observer(
                    {
                        "state": "done",
                        "pid": None,
                        "poll_attempt": 2,
                        "remote_workdir": "/remote/exact-job",
                    }
                )

            report = observer.report()

        self.assertEqual(full_transfer_count, 2)
        self.assertEqual(report["latest"]["record_count"], 2)
        self.assertTrue(report["latest"]["terminal_event_seen"])
        self.assertTrue(report["latest"]["live_transfer"]["final_full_snapshot"])

    def vcs_compile_plan(self) -> dict:
        common = {
            "cwd": "stage",
            "env": {},
            "shell": False,
            "authority_refs": ["b" * 64],
        }
        return {
            "schema_version": "spatialaccagent.vcs_compile_plan.v1",
            "status": "ready",
            "tool_binding": {
                "role": "functional_verification",
                "name": "vcs",
                "host": "vcs.example",
                "port": 22,
                "executable": "/opt/vcs/bin/vcs",
            },
            "top_module": "board_tb",
            "output": "simv",
            "compile_authority": {
                "vivado_facts_path": "board_interface_facts.json",
                "vivado_facts_sha256": "a" * 64,
                "simulator_export_context_sha256s": ["b" * 64],
            },
            "ordered_commands": [
                {
                    **common,
                    "order": 0,
                    "phase": "compile",
                    "tool_role": "functional_verification",
                    "executable": "/opt/vcs/bin/vlogan",
                    "argv": ["-full64", "-work", "xil_defaultlib", {"source_id": "sample.wrapper"}],
                    "source_ids": ["sample.wrapper"],
                },
                {
                    **common,
                    "order": 1,
                    "phase": "compile",
                    "tool_role": "functional_verification",
                    "executable": "/opt/vcs/bin/vhdlan",
                    "argv": ["-full64", "-work", "xil_defaultlib", {"source_id": "sample.bd_sim"}],
                    "source_ids": ["sample.bd_sim"],
                },
                {
                    **common,
                    "order": 2,
                    "phase": "compile",
                    "tool_role": "functional_verification",
                    "executable": "/opt/vcs/bin/vlogan",
                    "argv": ["-full64", "-sverilog", "-work", "xil_defaultlib", {"source_id": "generated.testbench"}],
                    "source_ids": ["generated.testbench"],
                },
                {
                    **common,
                    "order": 3,
                    "phase": "elaborate",
                    "tool_role": "functional_verification",
                    "executable": "/opt/vcs/bin/vcs",
                    "argv": ["-full64", "board_tb", "-o", "simv"],
                    "source_ids": [],
                },
            ],
        }

    def test_unbounded_transfer_retries_only_indeterminate_transport(self) -> None:
        disconnected = subprocess.CompletedProcess(
            ["scp"],
            255,
            "",
            "Connection reset by peer",
        )
        completed = subprocess.CompletedProcess(["scp"], 0, "", "")
        with patch.object(
            board_vcs,
            "run_command",
            side_effect=[disconnected, completed],
        ) as invoke, patch.object(board_vcs.time, "sleep") as delay:
            result = board_vcs.run_transfer_command(["scp"], 0)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(invoke.call_count, 2)
        delay.assert_called_once_with(15.0)

    def test_unbounded_transfer_does_not_retry_determinate_ssh_failure(self) -> None:
        rejected = subprocess.CompletedProcess(
            ["scp"],
            255,
            "",
            "Permission denied (publickey).",
        )
        with patch.object(board_vcs, "run_command", return_value=rejected) as invoke, patch.object(
            board_vcs.time,
            "sleep",
        ) as delay:
            result = board_vcs.run_transfer_command(["scp"], 0)

        self.assertEqual(result.returncode, 255)
        invoke.assert_called_once_with(["scp"])
        delay.assert_not_called()

    def test_stream_transfer_retries_indeterminate_transport(self) -> None:
        disconnected = subprocess.CompletedProcess(
            ["ssh"],
            255,
            None,
            b"Connection reset by peer",
        )
        completed = subprocess.CompletedProcess(["ssh"], 0, None, b"")
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "increment.jsonl"
            with patch.object(
                board_vcs.subprocess,
                "run",
                side_effect=[disconnected, completed],
            ) as invoke, patch.object(board_vcs.time, "sleep") as delay:
                result = board_vcs.run_stream_transfer_command(
                    ["ssh", "vcs.example", "tail"],
                    destination,
                    0,
                )

            self.assertTrue(destination.is_file())

        self.assertEqual(result.returncode, 0)
        self.assertEqual(invoke.call_count, 2)
        delay.assert_called_once_with(15.0)

    def test_stream_transfer_removes_partial_file_after_determinate_failure(self) -> None:
        def rejected(argv: list[str], **kwargs):
            kwargs["stdout"].write(b"partial remote payload")
            return subprocess.CompletedProcess(
                argv,
                255,
                None,
                b"Permission denied (publickey).",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "increment.jsonl"
            with patch.object(board_vcs.subprocess, "run", side_effect=rejected):
                result = board_vcs.run_stream_transfer_command(
                    ["ssh", "vcs.example", "tail"],
                    destination,
                    0,
                )

            self.assertFalse(destination.exists())

        self.assertEqual(result.returncode, 255)

    def test_preflight_projection_is_stable_after_runtime_evidence_is_added(self) -> None:
        plan = {"status": "ready", "source_files": [{"source_id": "a"}]}
        executed = {
            **plan,
            "status": "pass",
            "execution_evidence": {"status": "pass"},
            "dynamic_evidence_records": [{"evidence_id": "runtime"}],
            "elaborated_hierarchy": {"status": "pass"},
            "protocol_monitor_results": {"status": "pass"},
            "pipeline_overlap_results": {"status": "pass"},
            "runtime_loader_results": {"status": "pass"},
        }
        self.assertEqual(
            board_vcs.preflight_manifest_projection_sha256(plan),
            board_vcs.preflight_manifest_projection_sha256(executed),
        )

    def test_runtime_loader_output_is_required_only_when_runtime_is_enabled(self) -> None:
        base = {
            "execution_outputs": {
                "compile_log": {"path": "logs/compile.log"},
                "simulation_log": {"path": "logs/simulation.log"},
                "progress_event_log": {
                    "path": "evidence/progress_events.jsonl",
                    "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
                },
                "elaborated_hierarchy_report": {
                    "path": "evidence/hierarchy.json",
                    "schema_version": "test.hierarchy.v1",
                },
                "pipeline_overlap_report": {
                    "path": "evidence/pipeline.json",
                    "schema_version": "test.pipeline.v1",
                },
                "protocol_monitor_reports": [
                    {
                        "interface": "memory",
                        "path": "evidence/axi.json",
                        "schema_version": "test.axi.v1",
                    }
                ],
            }
        }
        disabled_errors: list[str] = []
        disabled = board_vcs.execution_output_plan(base, disabled_errors)
        self.assertFalse(disabled_errors)
        self.assertNotIn("runtime_loader_report", disabled)

        enabled_manifest = json.loads(json.dumps(base))
        enabled_manifest["runtime_constant_binding"] = {"enabled": True}
        enabled_errors: list[str] = []
        board_vcs.execution_output_plan(enabled_manifest, enabled_errors)
        self.assertTrue(
            any("runtime_loader_report" in error for error in enabled_errors),
            enabled_errors,
        )

        enabled_manifest["execution_outputs"]["runtime_loader_report"] = {
            "path": "evidence/runtime_loader.json",
            "schema_version": "test.runtime_loader.v1",
        }
        enabled_errors = []
        enabled = board_vcs.execution_output_plan(
            enabled_manifest, enabled_errors
        )
        self.assertFalse(enabled_errors)
        self.assertEqual(
            enabled["runtime_loader_report"]["path"],
            Path("evidence/runtime_loader.json"),
        )

    def test_performance_counter_output_is_optional_and_parsed_when_declared(self) -> None:
        manifest = {
            "execution_outputs": {
                "compile_log": {"path": "logs/compile.log"},
                "simulation_log": {"path": "logs/simulation.log"},
                "progress_event_log": {
                    "path": "evidence/progress_events.jsonl",
                    "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
                },
                "elaborated_hierarchy_report": {
                    "path": "evidence/hierarchy.json",
                    "schema_version": "test.hierarchy.v1",
                },
                "pipeline_overlap_report": {
                    "path": "evidence/pipeline.json",
                    "schema_version": "test.pipeline.v1",
                },
                "protocol_monitor_reports": [
                    {
                        "interface": "memory",
                        "path": "evidence/axi.json",
                        "schema_version": "test.axi.v1",
                    }
                ],
            }
        }
        errors: list[str] = []
        without_counter = board_vcs.execution_output_plan(manifest, errors)
        self.assertFalse(errors)
        self.assertNotIn("performance_counter_report", without_counter)

        manifest["execution_outputs"]["performance_counter_report"] = {
            "path": "reports/performance_counter_report.json",
            "schema_version": "spatialaccagent.performance_counter_report.v1",
        }
        errors = []
        with_counter = board_vcs.execution_output_plan(manifest, errors)
        self.assertFalse(errors)
        self.assertEqual(
            with_counter["performance_counter_report"]["path"],
            Path("reports/performance_counter_report.json"),
        )

    def make_run(self, root: Path) -> tuple[Path, dict, dict]:
        run_dir = root / "run"
        sources = run_dir / "board_sources"
        wrapper = write_file(
            sources / "wrapper.v",
            "module BoardWrapper; BoardBd bd(); fp_add_sp_12 arithmetic_ip(); endmodule\n",
        )
        wrapper.update(
            {
                "source_id": "sample.wrapper",
                "role": "wrapper",
                "dependencies": ["sample.bd_sim"],
                "declared_modules": ["BoardWrapper"],
            }
        )
        bd_sim = write_file(
            sources / "bd_sim.vhd",
            "entity BoardBd is end entity; architecture sim of BoardBd is begin end architecture;\n",
        )
        bd_sim.update(
            {
                "source_id": "sample.bd_sim",
                "role": "bd_sim",
                "dependencies": [],
                "declared_modules": ["BoardBd"],
            }
        )
        testbench = write_file(sources / "board_tb.sv", "module board_tb; BoardWrapper dut(); endmodule\n")
        testbench.update(
            {
                "source_id": "generated.testbench",
                "role": "testbench",
                "dependencies": ["sample.wrapper"],
                "declared_modules": ["board_tb"],
                "forbidden_construct_scan": {
                    "status": "planned",
                    "required": False,
                    "producer": "existing_simulator_compile",
                    "method": "simulator_elaboration",
                    "source_sha256": testbench["sha256"],
                },
            }
        )
        input_vector = write_file(run_dir / "vectors" / "input.memh", "00000001\n")
        expected = write_file(run_dir / "vectors" / "expected.memh", "00000002\n")
        weight = write_file(run_dir / "vectors" / "weights.memh", "00000003\n")

        identity = {
            "status": "pass",
            "exact_user_sample_wrapper": True,
            "top_module": "BoardWrapper",
            "selected_simulation_source_closure": {
                "status": "pass",
                "source_files": [wrapper, bd_sim],
                "root_source_ids": ["sample.wrapper"],
            },
            "materialized_sources": [wrapper, bd_sim],
            "source_hashes": [wrapper, bd_sim],
        }
        identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
        write_json(identity_path, identity)

        catalog = {
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "tensor_count": 1,
            "target_layer_count": 2,
            "tensors": [{"source_slice_sha256": "a" * 64}],
        }
        catalog_path = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
        write_json(catalog_path, catalog)
        binding = {
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "all_target_layers": True,
            "bound_layer_count": 2,
            "default_or_identity_weight_fallback_disabled": True,
            "dut_consumes_bound_weights": True,
            "scope_coverage_complete": True,
            "board_consumed_tensor_hashes": ["a" * 64],
        }
        write_json(run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json", binding)
        write_json(
            run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json",
            {
                "status": "ready",
                "board": {
                    "all_target_layer_reference_captured": True,
                    "input_vector": {"sha256": input_vector["sha256"]},
                    "expected_output": {"sha256": expected["sha256"]},
                },
            },
        )
        write_json(
            run_dir / "verification" / "model_reference" / "reference_manifest.json",
            {
                "status": "ready",
                "weights": {"source_checkpoint_sha256": "b" * 64},
                "input": {"source": "random", "seed": 7},
            },
        )
        weight.update(
            {
                "source_checkpoint_sha256": "b" * 64,
                "scope_coverage_complete": True,
                "accelerator_scope": "transformer_blocks_only",
                "accelerator_weight_catalog_sha256": board_vcs.sha256_file(catalog_path),
                "packed_tensor_hashes": ["a" * 64],
            }
        )
        compile_plan = self.vcs_compile_plan()
        manifest = {
            "status": "ready",
            "source_identity_sha256": board_vcs.sha256_file(identity_path),
            "source_closure_sha256": "c" * 64,
            "compile_source_set_sha256": "d" * 64,
            "all_target_layers": True,
            "bound_layer_count": 2,
            "target_layer_count": 2,
            "board_consumed_tensor_hashes": ["a" * 64],
            "source_files": [wrapper, bd_sim, testbench],
            "compile_source_ids": ["sample.wrapper", "sample.bd_sim", "generated.testbench"],
            "testbench": testbench,
            "artifacts": {
                "input": input_vector,
                "weight_image": weight,
                "expected_output": expected,
            },
            "exact_sample_wrapper_unmodified": True,
            "top_module": "board_tb",
            "pass_regex": r"BOARD PASS",
            "rtl_output_file": "rtl_output.memh",
            "boundary_trace_file": "boundary_trace.json",
            "execution_outputs": {
                "compile_log": {"path": "execution/vcs.log"},
                "simulation_log": {"path": "execution/sim.log"},
                "progress_event_log": {
                    "path": "execution/progress_events.jsonl",
                    "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
                },
                "elaborated_hierarchy_report": {
                    "path": "execution/elaborated_hierarchy.json",
                    "schema_version": "spatialaccagent.elaborated_hierarchy.v1",
                },
                "pipeline_overlap_report": {
                    "path": "execution/pipeline_overlap.json",
                    "schema_version": "spatialaccagent.pipeline_overlap.v1",
                },
                "protocol_monitor_reports": [
                    {
                        "interface": "ddr_axi",
                        "path": "execution/axi_monitor.json",
                        "schema_version": "spatialaccagent.axi_monitor.v1",
                    }
                ],
            },
            "vcs_compile_plan": compile_plan,
            "vcs_compile_plan_sha256": board_vcs.canonical_contract_sha256(compile_plan),
            "protocol_monitor_contract": {
                "status": "ready",
                "monitors": [
                    {
                        "monitor_id": "axi.ddr",
                        "interface": "ddr_axi",
                        "structured_report": {
                            "path": "axi_monitor.json",
                            "schema_version": "spatialaccagent.axi_monitor.v1",
                            "required_fields": ["schema_version", "status", "violations", "transaction_counts"],
                        },
                    }
                ],
            },
            "vcs": {
                "runtime_plusargs": {
                    "INPUT": "input",
                    "WEIGHTS": "weight_image",
                    "EXPECTED": "expected_output",
                },
            },
        }
        manifest_path = run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
        write_json(manifest_path, manifest)
        write_json(
            run_dir / "input" / "tool_profile.json",
            {
                "tools": [
                    {
                        "name": "vcs",
                        "role": "functional_verification",
                        "host": "vcs.example",
                        "port": 22,
                        "executable": "/opt/vcs/bin/vcs",
                    },
                    {
                        "name": "vivado",
                        "role": "implementation",
                        "host": "vcs.example",
                        "port": 22,
                        "executable": "/opt/Xilinx/Vivado/2021.1/bin/vivado",
                    },
                ]
            },
        )
        simulation_dir = run_dir / "generated" / "chisel" / "simulation"
        scripts_dir = simulation_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        ip_tcl = scripts_dir / "gen_xilinx_fp_ips.tcl"
        ip_tcl.write_text("puts ip-generation\n", encoding="utf-8")
        ip_modules = simulation_dir / "fpga_ip_modules.txt"
        ip_modules.write_text("fp_add_sp_12\n", encoding="utf-8")
        write_json(
            simulation_dir / "fpga_ip_simulation_closure.json",
            {
                "status": "ready",
                "policy": simulation_source_contract(),
                "ip_generation_tcl": str(ip_tcl),
                "ip_output_dir": str(simulation_dir / "vivado_ip"),
                "ip_project_dir": str(simulation_dir / "vivado_ip_project"),
                "ip_module_manifest": str(ip_modules),
                "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
                "required_ip_modules": ["fp_add_sp_12"],
                "vcs_compile_requirements": {
                    "generated_ip_simulation_sources": "generated IP sources",
                    "xpm_library": "xpm",
                    "unisims_library": "unisims_ver",
                    "global_module": "glbl.v",
                },
            },
        )
        return run_dir, identity, manifest

    def test_cold_vcs_payload_and_simulator_use_current_runtime_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            selection = (
                run_dir
                / "verification"
                / "adaptive_observation"
                / "current_selection.json"
            )
            write_json(
                selection,
                {
                    "schema_version": "spatialaccagent.runtime_observation_selection.v1",
                    "status": "ready",
                    "decision_sha256": "e" * 64,
                    "selected_signals": [{"expression": "dut.core.out_valid"}],
                },
            )
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(
                board_vcs,
                "run_command",
                self.successful_remote_mock(run_dir, calls),
            ), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)

            job = json.loads(
                (
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "vcs_stage"
                    / board_vcs.REMOTE_SEMANTIC_JOB_CONTRACT
                ).read_text(encoding="utf-8")
            )
            staged = (
                run_dir
                / "verification"
                / "board_simulation"
                / "vcs_stage"
                / "observation"
                / "current_selection.json"
            )

            self.assertEqual(result["status"], "pass")
            self.assertTrue(staged.is_file())
            self.assertEqual(
                json.loads(staged.read_text(encoding="utf-8")),
                json.loads(selection.read_text(encoding="utf-8")),
            )
            self.assertIn(
                "observation/current_selection.json",
                {row["path"] for row in job["payload"]},
            )
            simulation_commands = [
                command
                for label, _, command in detached_calls
                if label == "vcs_simulate"
            ]

        self.assertEqual(len(simulation_commands), 1)
        self.assertIn(
            "+SPATIALACC_OBSERVATION_SELECTION=observation/current_selection.json",
            simulation_commands[0],
        )

    def rewrite_identity_and_manifest(
        self,
        run_dir: Path,
        identity: dict,
        manifest: dict,
    ) -> None:
        identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
        write_json(identity_path, identity)
        digest = board_vcs.sha256_file(identity_path)
        manifest["source_identity_sha256"] = digest
        write_json(
            run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
            manifest,
        )

    def configure_scoped_weight_image(
        self, run_dir: Path, manifest: dict
    ) -> None:
        catalog_path = (
            run_dir
            / "verification"
            / "model_weights"
            / "transformer_block_weight_catalog.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["tensor_count"] = 2
        catalog["tensors"] = [
            {"layer_index": 0, "source_slice_sha256": "a" * 64},
            {"layer_index": 1, "source_slice_sha256": "b" * 64},
        ]
        write_json(catalog_path, catalog)

        write_json(
            run_dir
            / "generated"
            / "memory"
            / "dut_weight_binding_manifest.json",
            {
                "status": "pass",
                "accelerator_scope": "transformer_blocks_only",
                "all_target_layers": False,
                "model_layer_count": 2,
                "bound_layer_count": 1,
                "validation_layer_indices": [0],
                "default_or_identity_weight_fallback_disabled": True,
                "dut_consumes_bound_weights": True,
                "scope_coverage_complete": True,
                "board_consumed_tensor_hashes": ["a" * 64],
            },
        )
        semantic_path = (
            run_dir
            / "verification"
            / "semantic_testbench"
            / "semantic_testbench_manifest.json"
        )
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic["board"].update(
            {
                "model_layer_count": 2,
                "expected_target_layers": 1,
                "validation_layer_indices": [0],
                "scoped_layer_reference_captured": True,
            }
        )
        write_json(semantic_path, semantic)

        manifest.update(
            {
                "all_target_layers": False,
                "bound_layer_count": 1,
                "target_layer_count": 1,
                "validation_layer_indices": [0],
                "board_consumed_tensor_hashes": ["a" * 64],
            }
        )
        weight = manifest["artifacts"]["weight_image"]
        weight.update(
            {
                "target_layer_count": 1,
                "validation_layer_indices": [0],
                "packed_tensor_hashes": ["a" * 64],
                "accelerator_weight_catalog_sha256": board_vcs.sha256_file(
                    catalog_path
                ),
            }
        )
        write_json(
            run_dir
            / "verification"
            / "board_simulation"
            / "board_simulation_manifest.json",
            manifest,
        )

    def test_scoped_weight_image_uses_validation_layer_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            self.configure_scoped_weight_image(run_dir, manifest)
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ):
                _, resolved, errors = board_vcs.validate_manifest(run_dir)

            self.assertFalse(errors, errors)
            self.assertTrue(resolved["evidence"]["complete_scope_weight_image"])
            self.assertEqual(
                resolved["evidence"]["required_transformer_block_tensor_count"],
                1,
            )
            self.assertEqual(
                resolved["weight_binding_evidence"]["required_tensor_hashes"],
                ["a" * 64],
            )

    def test_scoped_weight_image_missing_validation_tensor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            self.configure_scoped_weight_image(run_dir, manifest)
            manifest["artifacts"]["weight_image"]["packed_tensor_hashes"] = [
                "b" * 64
            ]
            write_json(
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ):
                _, _, errors = board_vcs.validate_manifest(run_dir)

            self.assertTrue(
                any(
                    "board weight image does not contain every transformer-block tensor hash"
                    in error
                    for error in errors
                ),
                errors,
            )

    def successful_remote_mock(self, run_dir: Path, calls: list[tuple[list[str], int | None]]):
        def invoke(argv: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str]:
            calls.append((argv, timeout))
            if argv and argv[0] == "scp" and len(argv) >= 2:
                destination = Path(argv[-1])
                remote_source = argv[-2]
                if ":" in remote_source:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if remote_source.endswith("/vcs.log"):
                        destination.write_text("Version TEST-VCS\ncompile pass\n", encoding="utf-8")
                    elif remote_source.endswith("/sim.log"):
                        destination.write_text("BOARD PASS\n", encoding="utf-8")
                    elif remote_source.endswith("/progress_events.jsonl"):
                        destination.write_text(
                            "\n".join(
                                json.dumps(row, sort_keys=True)
                                for row in (
                                    progress_event(0, "semantic_progress", True),
                                    progress_event(1, "terminal", False),
                                )
                            )
                            + "\n",
                            encoding="utf-8",
                        )
                    elif remote_source.endswith("/rtl_output.memh"):
                        destination.write_text("00000002\n", encoding="utf-8")
                    elif remote_source.endswith("/boundary_trace.json"):
                        destination.write_text("{}\n", encoding="utf-8")
                    elif remote_source.endswith("/axi_monitor.json"):
                        destination.write_text(
                            json.dumps(
                                {
                                    "schema_version": "spatialaccagent.axi_monitor.v1",
                                    "status": "pass",
                                    "violations": [],
                                    "transaction_counts": {"aw": 1, "w": 1, "b": 1, "ar": 1, "r": 1},
                                }
                            )
                            + "\n",
                            encoding="utf-8",
                        )
                    elif remote_source.endswith("/elaborated_hierarchy.json"):
                        destination.write_text(
                            json.dumps(
                                {
                                    "schema_version": "spatialaccagent.elaborated_hierarchy.v1",
                                    "status": "pass",
                                    "evidence_refs": ["runtime.elaborated_hierarchy.report"],
                                }
                            )
                            + "\n",
                            encoding="utf-8",
                        )
                    elif remote_source.endswith("/pipeline_overlap.json"):
                        destination.write_text(
                            json.dumps(
                                {
                                    "schema_version": "spatialaccagent.pipeline_overlap.v1",
                                    "status": "pass",
                                    "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                                    "required_dependency_overlap_complete": True,
                                    "all_planned_stages_participate_in_required_overlap": True,
                                    "token_order_preserved": True,
                                    "serial_leaf_execution_observed": False,
                                    "observed_different_token_overlap_count": 3,
                                    "stage_turnover_gaps_are_diagnostic": True,
                                    "all_stages_same_cycle_concurrency_required": False,
                                    "diagnostic_maximum_concurrent_stage_count": 2,
                                    "all_spatial_stages_concurrent_observed": False,
                                    "whole_sequence_barrier_observed": False,
                                    "expected_stage_count": 3,
                                    "observed_stage_count": 3,
                                }
                            )
                            + "\n",
                            encoding="utf-8",
                        )
            return subprocess.CompletedProcess(argv, 0, "", "")

        return invoke

    def exact_board_preflight(self, passed: bool = True, plan_sha256: str | None = None) -> dict:
        blockers = [] if passed else ["real elaboration evidence is missing"]
        return {
            "status": "pass" if passed else "fail",
            "blockers": blockers,
            "verified_compile_source_ids": ["sample.wrapper", "sample.bd_sim", "generated.testbench"],
            "vcs_compile_plan_sha256": plan_sha256
            or board_vcs.canonical_contract_sha256(self.vcs_compile_plan()),
            "checks": [
                {
                    "name": "simulation_compile_source_set",
                    "status": "pass" if passed else "fail",
                    "blockers": blockers,
                }
            ],
        }

    def successful_detached_mock(self, calls: list[tuple[str, int, str]]):
        def invoke(
            host: str,
            port: int,
            command: str,
            remote_dir: str,
            cwd: Path,
            timeout_sec: int,
            label: str,
            progress_callback=None,
        ) -> dict:
            calls.append((label, timeout_sec, command))
            return {
                "status": "pass",
                "returncode": 0,
                "remote_workdir": remote_dir,
                "stderr_tail": "",
            }

        return invoke

    def exact_board_acceptance(self, passed: bool = True) -> dict:
        blockers = [] if passed else ["post-run exact board evidence is incomplete"]
        return {
            "status": "pass" if passed else "fail",
            "blockers": blockers,
            "checks": [
                {
                    "name": "elaborated_exact_top_and_accelerator_binding",
                    "status": "pass" if passed else "fail",
                    "blockers": blockers,
                }
            ],
        }

    def attach_external_fixture_staging(
        self, run_dir: Path, manifest: dict
    ) -> tuple[dict, str]:
        auxiliary = write_file(
            run_dir / "fixture_inputs" / "model.smi",
            "fixture-runtime-metadata\n",
        )
        auxiliary.update(
            {
                "source_id": "fixture.source.model_smi",
                "artifact_id": "fixture.artifact.model_smi",
                "remote_path": "/tmp/export/model.smi",
                "staged_path": "runtime-parent/model.smi",
                "runtime_staged_path": "model.smi",
            }
        )
        runtime = write_file(
            run_dir / "fixture_inputs" / "temp_mem.txt",
            "00000000\n",
        )
        runtime.update(
            {
                "source_id": "fixture.source.temp_mem",
                "artifact_id": "fixture.artifact.temp_mem",
                "remote_path": "/tmp/export/temp_mem.txt",
                "staged_path": "runtime-parent/temp_mem.txt",
                "runtime_staged_path": "temp_mem.txt",
            }
        )
        include_file = write_file(
            run_dir / "fixture_inputs" / "include" / "ddr_defs.vh",
            "`define DDR_DATA_WIDTH 72\n",
        )
        include_file.update(
            {
                "source_id": "fixture.source.ddr_defs",
                "artifact_id": "fixture.artifact.ddr_defs",
                "remote_path": "/tmp/export/include/ddr_defs.vh",
                "staged_path": "include-parent/ddr_defs.vh",
            }
        )
        vendor_map = write_file(
            run_dir / "fixture_inputs" / "vendor" / "synopsys_sim.setup",
            "unisims_ver:/opt/vendor/unisims_ver\n",
        )
        setup_remote_path = "/opt/vendor/synopsys_sim.setup"
        setup_file = {
            **vendor_map,
            "source_id": "fixture.source.synopsys_setup",
            "artifact_id": "fixture.artifact.synopsys_setup",
            "remote_path": setup_remote_path,
            "staged_path": "setup-parent/synopsys_sim.setup",
        }
        materialized_files = [
            {key: value for key, value in row.items() if key != "runtime_staged_path"}
            for row in (auxiliary, runtime, include_file, setup_file)
        ]
        fixture_report_path = (
            run_dir
            / "verification"
            / "board_interface"
            / "external_simulation_fixture.json"
        )
        write_json(
            fixture_report_path,
            {"status": "pass", "materialized_files": materialized_files},
        )
        manifest["external_simulation_fixture"] = {
            "path": str(fixture_report_path),
            "sha256": board_vcs.sha256_file(fixture_report_path),
            "runtime_auxiliary_files": [auxiliary, runtime, setup_file],
            "include_directories": [
                {
                    "include_dir_id": "fixture.ddr_headers",
                    "remote_path": "/tmp/export/include",
                    "staged_path": "include-parent",
                    "member_source_ids": [include_file["source_id"]],
                }
            ],
            "synopsys_sim_setup": {
                **setup_file,
                "files": [setup_file],
            },
        }
        plan = manifest["vcs_compile_plan"]
        plan["ordered_commands"][0]["argv"].insert(
            -1, {"include_dir_id": "fixture.ddr_headers"}
        )
        plan_sha256 = board_vcs.canonical_contract_sha256(plan)
        manifest["vcs_compile_plan_sha256"] = plan_sha256
        write_json(
            run_dir
            / "verification"
            / "board_simulation"
            / "board_simulation_manifest.json",
            manifest,
        )
        return manifest["external_simulation_fixture"], plan_sha256

    def test_success_uses_resolved_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(board_vcs, "run_command", self.successful_remote_mock(run_dir, calls)), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)

            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["exact_sample_wrapper_unmodified"])
            self.assertTrue(result["all_target_layers"])
            self.assertTrue(result["real_model_weights_consumed"])
            self.assertTrue(result["complete_scope_weight_image"])
            self.assertTrue(result["random_input_stimulus"])
            self.assertTrue(result["exact_board_preflight_passed"])
            self.assertTrue(result["exact_board_acceptance_passed"])
            self.assertTrue(result["structured_monitors_passed"])
            self.assertTrue(result["pipeline_overlap_passed"])
            self.assertTrue(result["elaborated_hierarchy_report_valid"])
            self.assertEqual(result["selected_simulation_source_count"], 2)
            self.assertEqual([row[0] for row in detached_calls], ["vcs_compile", "vcs_simulate"])
            compile_shell = detached_calls[0][2]
            self.assertNotIn("vcs_filelist.f", compile_shell)
            self.assertLess(compile_shell.index("vlogan"), compile_shell.index("vhdlan"))
            self.assertLess(compile_shell.index("vhdlan"), compile_shell.rindex("vcs"))
            self.assertIn("sources/wrapper.v", compile_shell)
            self.assertIn("sources/bd_sim.vhd", compile_shell)
            self.assertIn("sources/board_tb.sv", compile_shell)
            self.assertIn("./stage/simv", detached_calls[1][2])
            executed = json.loads(Path(result["executed_manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(executed["status"], "pass")
            self.assertEqual(executed["execution_evidence"]["compile"]["exit_code"], 0)
            self.assertEqual(executed["elaborated_hierarchy"]["status"], "pass")
            self.assertEqual(executed["protocol_monitor_results"]["status"], "pass")
            self.assertEqual(executed["pipeline_overlap_results"]["status"], "pass")
            contract = json.loads(
                Path(result["remote_job_recovery_contract"]["job_contract"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(contract["source_closure_sha256"], "c" * 64)
            self.assertEqual(contract["compile_source_set_sha256"], "d" * 64)
            self.assertEqual(contract["remote_workdir"], result["remote_workdir"])
            self.assertEqual(contract["input_fingerprint_sha256"], result["input_fingerprint_sha256"])
            self.assertIn("compile_command", contract)
            self.assertIn("simulate_command", contract)
            self.assertFalse(any(row["path"] == "vcs_filelist.f" for row in contract["payload"]))
            self.assertEqual(
                contract["vcs_compile_plan_sha256"],
                board_vcs.canonical_contract_sha256(self.vcs_compile_plan()),
            )

    def test_agent_requested_vcs_loop_report_changes_compile_and_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            with patch.dict(
                board_vcs.os.environ,
                {"SPATIALACC_VCS_LOOP_REPORT": "1"},
            ), patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(
                board_vcs,
                "run_command",
                self.successful_remote_mock(run_dir, calls),
            ), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)

        self.assertEqual(result["status"], "pass")
        self.assertIn("+vcs+loopreport", detached_calls[0][2])
        self.assertIn("+vcs+loopreport", detached_calls[1][2])
        self.assertTrue(
            result["remote_resource_policy"]["vcs_native_loop_report_enabled"]
        )
        self.assertTrue(result["vcs_native_loop_report"]["enabled"])

    def test_external_fixture_files_include_and_library_map_are_in_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            manifest["vcs_compile_plan"]["ordered_commands"][1]["cwd"] = "stage_vhdl"
            manifest["vcs_compile_plan"]["ordered_commands"][-1]["cwd"] = "elab"
            sample_elf = write_file(
                run_dir / "sample_runtime" / "controller.elf",
                "sample-runtime-payload\n",
            )
            sample_elf["runtime_staged_path"] = "controller.elf"
            manifest["sample_runtime_auxiliary_files"] = [
                sample_elf,
                dict(sample_elf),
            ]
            fixture, plan_sha256 = self.attach_external_fixture_staging(
                run_dir, manifest
            )
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(plan_sha256=plan_sha256),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(
                board_vcs,
                "run_command",
                self.successful_remote_mock(run_dir, calls),
            ), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)

            self.assertEqual(result["status"], "pass", result)
            compile_shell = detached_calls[0][2]
            self.assertIn("+incdir+../sources/include-parent", compile_shell)
            self.assertEqual(
                compile_shell.count("sources/wrapper.v"),
                1,
                "the include-dir token must not alter source coverage",
            )
            stage_dir = (
                run_dir / "verification" / "board_simulation" / "vcs_stage"
            )
            setup = stage_dir / "stage" / "synopsys_sim.setup"
            self.assertEqual(
                setup.read_text(encoding="utf-8"),
                "xil_defaultlib:../vcs_lib/xil_defaultlib\n"
                "OTHERS=../sources/setup-parent/synopsys_sim.setup\n",
            )
            self.assertTrue(
                (stage_dir / "vcs_lib" / "xil_defaultlib").is_dir()
            )
            contract = json.loads(
                Path(result["remote_job_recovery_contract"]["job_contract"]).read_text(
                    encoding="utf-8"
                )
            )
            payload = {row["path"]: row["sha256"] for row in contract["payload"]}
            expected_paths = {
                "stage/model.smi",
                "stage/temp_mem.txt",
                "stage/controller.elf",
                "stage_vhdl/model.smi",
                "stage_vhdl/temp_mem.txt",
                "stage_vhdl/controller.elf",
                "elab/model.smi",
                "elab/temp_mem.txt",
                "elab/controller.elf",
                "sources/include-parent/ddr_defs.vh",
                "sources/setup-parent/synopsys_sim.setup",
                "stage/synopsys_sim.setup",
                "stage_vhdl/synopsys_sim.setup",
                "elab/synopsys_sim.setup",
            }
            self.assertTrue(expected_paths.issubset(payload), payload)
            for index in range(2):
                row = fixture["runtime_auxiliary_files"][index]
                for cwd in ("stage", "stage_vhdl", "elab"):
                    self.assertEqual(
                        payload[f"{cwd}/{row['runtime_staged_path']}"],
                        row["sha256"],
                    )
            for cwd in ("stage", "stage_vhdl", "elab"):
                self.assertEqual(
                    payload[f"{cwd}/controller.elf"], sample_elf["sha256"]
                )
            include_source_id = fixture["include_directories"][0][
                "member_source_ids"
            ][0]
            fixture_report = json.loads(Path(fixture["path"]).read_text(encoding="utf-8"))
            include_row = next(
                row
                for row in fixture_report["materialized_files"]
                if row["source_id"] == include_source_id
            )
            self.assertEqual(
                payload["sources/include-parent/ddr_defs.vh"],
                include_row["sha256"],
            )
            self.assertEqual(
                payload["sources/setup-parent/synopsys_sim.setup"],
                fixture["synopsys_sim_setup"]["sha256"],
            )

    def test_external_fixture_hash_and_staged_paths_fail_before_remote(self) -> None:
        mutations = (
            (
                "hash mismatch",
                lambda fixture: Path(
                    fixture["runtime_auxiliary_files"][0]["path"]
                ).write_text("tampered\n", encoding="utf-8"),
            ),
            (
                "safe relative path",
                lambda fixture: fixture["runtime_auxiliary_files"][1].update(
                    {"runtime_staged_path": "../temp_mem.txt"}
                ),
            ),
        )
        for expected_error, mutate in mutations:
            with self.subTest(expected_error=expected_error), tempfile.TemporaryDirectory() as tmp:
                run_dir, _, manifest = self.make_run(Path(tmp))
                fixture, plan_sha256 = self.attach_external_fixture_staging(
                    run_dir, manifest
                )
                mutate(fixture)
                manifest["external_simulation_fixture"] = fixture
                write_json(
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "board_simulation_manifest.json",
                    manifest,
                )
                with patch.object(
                    board_vcs,
                    "validate_exact_board_preflight",
                    return_value=self.exact_board_preflight(
                        plan_sha256=plan_sha256
                    ),
                ), patch.object(board_vcs, "run_command") as remote:
                    result = board_vcs.execute(run_dir, 0)
                self.assertEqual(result["phase"], "manifest_validation")
                self.assertTrue(
                    any(expected_error in error for error in result["errors"]),
                    result["errors"],
                )
                remote.assert_not_called()

    def test_sample_runtime_auxiliary_validation_fails_before_remote(self) -> None:
        def tamper(rows: list[dict]) -> None:
            Path(rows[0]["path"]).write_text("tampered\n", encoding="utf-8")

        def escape(rows: list[dict]) -> None:
            rows[0]["runtime_staged_path"] = "../controller.elf"

        def conflict(rows: list[dict]) -> None:
            second_path = Path(rows[0]["path"]).with_name("other.elf")
            second = write_file(second_path, "different-runtime-payload\n")
            second["runtime_staged_path"] = rows[0]["runtime_staged_path"]
            rows.append(second)

        mutations = (
            ("hash mismatch", tamper),
            ("safe relative path", escape),
            ("conflicting content", conflict),
        )
        for expected_error, mutate in mutations:
            with self.subTest(expected_error=expected_error), tempfile.TemporaryDirectory() as tmp:
                run_dir, _, manifest = self.make_run(Path(tmp))
                sample = write_file(
                    run_dir / "sample_runtime" / "controller.elf",
                    "sample-runtime-payload\n",
                )
                sample["runtime_staged_path"] = "controller.elf"
                rows = [sample]
                mutate(rows)
                manifest["sample_runtime_auxiliary_files"] = rows
                write_json(
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "board_simulation_manifest.json",
                    manifest,
                )
                with patch.object(
                    board_vcs,
                    "validate_exact_board_preflight",
                    return_value=self.exact_board_preflight(),
                ), patch.object(board_vcs, "run_command") as remote:
                    result = board_vcs.execute(run_dir, 0)
                self.assertEqual(result["phase"], "manifest_validation")
                self.assertTrue(
                    any(expected_error in error for error in result["errors"]),
                    result["errors"],
                )
                remote.assert_not_called()

    def test_compile_command_without_explicit_work_library_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            plan = manifest["vcs_compile_plan"]
            argv = plan["ordered_commands"][0]["argv"]
            work_index = argv.index("-work")
            del argv[work_index : work_index + 2]
            plan_sha256 = board_vcs.canonical_contract_sha256(plan)
            manifest["vcs_compile_plan_sha256"] = plan_sha256
            write_json(
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(plan_sha256=plan_sha256),
            ), patch.object(board_vcs, "run_command") as remote:
                result = board_vcs.execute(run_dir, 0)
            self.assertEqual(result["phase"], "manifest_validation")
            self.assertTrue(
                any("explicit -work <library>" in error for error in result["errors"]),
                result["errors"],
            )
            remote.assert_not_called()

    def test_manifest_source_outside_selected_closure_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            extra = write_file(run_dir / "board_sources" / "extra.v", "module Extra; endmodule\n")
            manifest["source_files"].append(extra)
            write_json(
                run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ):
                _, _, errors = board_vcs.validate_manifest(run_dir)
            self.assertTrue(
                any(
                    "source_id is missing" in error or "transformed compile source IDs" in error
                    for error in errors
                )
            )

    def test_bd_synth_is_rejected_even_when_identity_selects_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, identity, manifest = self.make_run(Path(tmp))
            synth = write_file(run_dir / "board_sources" / "synth" / "bd_synth.v", "module SynthBd; endmodule\n")
            synth.update(
                {
                    "source_id": "sample.bd_synth",
                    "role": "bd_synth",
                    "dependencies": [],
                    "declared_modules": ["SynthBd"],
                }
            )
            identity["selected_simulation_source_closure"]["source_files"].append(synth)
            identity["materialized_sources"].append(synth)
            manifest["source_files"].append(synth)
            self.rewrite_identity_and_manifest(run_dir, identity, manifest)
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ):
                _, _, errors = board_vcs.validate_manifest(run_dir)
            self.assertTrue(any("contains synthesis source" in error for error in errors))

    def test_vendor_duplicate_module_definitions_are_deferred_to_vcs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, identity, manifest = self.make_run(Path(tmp))
            duplicate = Path(manifest["source_files"][1]["path"])
            duplicate.write_text("module BoardWrapper; endmodule\n", encoding="utf-8")
            digest = board_vcs.sha256_file(duplicate)
            identity["selected_simulation_source_closure"]["source_files"][1]["sha256"] = digest
            identity["materialized_sources"][1]["sha256"] = digest
            identity["source_hashes"][1]["sha256"] = digest
            manifest["source_files"][1]["sha256"] = digest
            self.rewrite_identity_and_manifest(run_dir, identity, manifest)
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ):
                _, _, errors = board_vcs.validate_manifest(run_dir)
            self.assertFalse(any("declares module BoardWrapper more than once" in error for error in errors))

    def test_agent_owned_duplicate_module_definitions_fail_before_remote_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = write_file(root / "sample.v", "module SharedModule; endmodule\n")
            generated = write_file(root / "generated.sv", "module SharedModule; endmodule\n")
            errors = board_vcs.duplicate_module_errors(
                [
                    {
                        "path": Path(sample["path"]),
                        "source_id": "sample-source:one",
                        "role": "simulation_source",
                    },
                    {
                        "path": Path(generated["path"]),
                        "source_id": "generated-board-source:adapter",
                        "role": "compute_slot_adapter",
                    },
                ]
            )
            self.assertTrue(
                any("SharedModule" in error for error in errors), errors
            )

    def test_failed_exact_board_preflight_blocks_remote_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(False),
            ), patch.object(board_vcs, "run_command") as remote:
                result = board_vcs.execute(run_dir, 0)
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["phase"], "manifest_validation")
            self.assertTrue(any("real elaboration evidence" in error for error in result["errors"]))
            remote.assert_not_called()

    def test_missing_compile_plan_fails_before_remote_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            manifest.pop("vcs_compile_plan")
            manifest.pop("vcs_compile_plan_sha256")
            write_json(
                run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(board_vcs, "run_command") as remote:
                result = board_vcs.execute(run_dir, 0)

            self.assertEqual(result["phase"], "manifest_validation")
            self.assertTrue(any("vcs_compile_plan is missing" in error for error in result["errors"]))
            remote.assert_not_called()

    def test_incomplete_compile_plan_source_coverage_fails_before_remote_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            plan = manifest["vcs_compile_plan"]
            del plan["ordered_commands"][2]
            plan["ordered_commands"][-1]["order"] = 2
            plan_sha256 = board_vcs.canonical_contract_sha256(plan)
            manifest["vcs_compile_plan_sha256"] = plan_sha256
            write_json(
                run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(plan_sha256=plan_sha256),
            ), patch.object(board_vcs, "run_command") as remote:
                result = board_vcs.execute(run_dir, 0)

            self.assertEqual(result["phase"], "manifest_validation")
            self.assertTrue(
                any("source ID exactly once" in error for error in result["errors"]),
                result["errors"],
            )
            remote.assert_not_called()

    def test_compile_plan_source_order_mismatch_fails_before_remote_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            plan = manifest["vcs_compile_plan"]
            commands = plan["ordered_commands"]
            commands[0], commands[1] = commands[1], commands[0]
            commands[0]["order"] = 0
            commands[1]["order"] = 1
            plan_sha256 = board_vcs.canonical_contract_sha256(plan)
            manifest["vcs_compile_plan_sha256"] = plan_sha256
            write_json(
                run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(plan_sha256=plan_sha256),
            ), patch.object(board_vcs, "run_command") as remote:
                result = board_vcs.execute(run_dir, 0)

            self.assertEqual(result["phase"], "manifest_validation")
            self.assertTrue(
                any("source token order" in error for error in result["errors"]),
                result["errors"],
            )
            remote.assert_not_called()

    def test_malformed_elaboration_argv_fails_closed_before_remote_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            plan = manifest["vcs_compile_plan"]
            plan["ordered_commands"][-1]["argv"] = {"command": "vcs board_tb"}
            plan_sha256 = board_vcs.canonical_contract_sha256(plan)
            manifest["vcs_compile_plan_sha256"] = plan_sha256
            write_json(
                run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json",
                manifest,
            )
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(plan_sha256=plan_sha256),
            ), patch.object(board_vcs, "run_command") as remote:
                result = board_vcs.execute(run_dir, 0)

            self.assertEqual(result["phase"], "manifest_validation")
            self.assertTrue(any(".argv is empty" in error for error in result["errors"]))
            remote.assert_not_called()

    def test_structured_monitor_violation_overrides_pass_regex(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            successful = self.successful_remote_mock(run_dir, calls)

            def remote(argv: list[str], timeout: int | None = None) -> subprocess.CompletedProcess[str]:
                result = successful(argv, timeout)
                if argv and argv[0] == "scp" and argv[-2].endswith("/axi_monitor.json"):
                    Path(argv[-1]).write_text(
                        json.dumps(
                            {
                                "schema_version": "spatialaccagent.axi_monitor.v1",
                                "status": "fail",
                                "violations": [{"kind": "valid_stability"}],
                                "transaction_counts": {"aw": 1, "w": 1, "b": 1, "ar": 1, "r": 1},
                            }
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                return result

            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(board_vcs, "run_command", remote), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)
            self.assertTrue(result["pass_regex_matched"])
            self.assertFalse(result["structured_monitors_passed"])
            self.assertEqual(result["status"], "fail")

    def test_post_run_acceptance_failure_does_not_promote_preflight_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(False),
            ), patch.object(
                board_vcs,
                "run_command",
                self.successful_remote_mock(run_dir, calls),
            ), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)
            self.assertFalse(result["exact_board_acceptance_passed"])
            self.assertEqual(result["status"], "fail")
            preflight = json.loads(
                (run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(preflight["status"], "ready")

    def test_completed_exact_remote_job_is_harvested_without_setup_or_relaunch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            recovered = {
                "recovery_state": "recovered",
                "remote_dir": "/remote/board/exact_job",
                "compile": {"status": "pass", "returncode": 0},
                "simulate": {"status": "pass", "returncode": 0},
                "identity": {"identity_source": "full_remote_job_contract"},
            }
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=recovered,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(
                board_vcs,
                "run_command",
                self.successful_remote_mock(run_dir, calls),
            ), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)
            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["remote_job_reuse"]["real_tool_was_not_relaunched"])
            self.assertEqual(result["remote_workdir"], "/remote/board/exact_job")
            self.assertEqual(detached_calls, [])
            self.assertFalse(
                any(argv and argv[0] == "ssh" for argv, _ in calls),
                calls,
            )
            self.assertFalse(
                any(argv and argv[0] == "scp" and argv[-2].endswith("vcs_stage.tar.gz") for argv, _ in calls),
                calls,
            )
            self.assertFalse(
                (
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "vcs_stage.tar.gz"
                ).exists()
            )

    def test_proven_semantic_stall_reuses_live_progress_without_full_log_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, manifest = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            fingerprint = "f" * 64
            remote_workdir = "/remote/board/exact_job"
            write_json(
                run_dir
                / "verification"
                / "board_simulation"
                / "vcs_stage"
                / board_vcs.REMOTE_SEMANTIC_JOB_CONTRACT,
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "remote_stage_root": "/remote/board",
                    "source_identity_sha256": manifest["source_identity_sha256"],
                    "source_closure_sha256": manifest["source_closure_sha256"],
                    "compile_source_set_sha256": manifest[
                        "compile_source_set_sha256"
                    ],
                    "preflight_manifest_projection_sha256": (
                        board_vcs.preflight_manifest_projection_sha256(manifest)
                    ),
                    "payload": [{"path": "sealed-input"}],
                    "execution_outputs": manifest["execution_outputs"],
                },
            )
            live_dir = run_dir / "verification" / "vcs" / "active_exact_job"
            live_raw = live_dir / "progress_events.jsonl"
            live_raw.parent.mkdir(parents=True, exist_ok=True)
            live_raw.write_text(
                json.dumps(progress_event(0, "semantic_progress", True)) + "\n",
                encoding="utf-8",
            )
            write_json(
                live_dir / "live_progress.json",
                {
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "adaptive_semantic_stall_evidence": {
                        "status": "proven_semantic_stall"
                    },
                },
            )
            recovered = {
                "recovery_state": "recovered",
                "remote_dir": remote_workdir,
                "compile": {"status": "pass", "returncode": 0},
                "simulate": {
                    "status": "fail",
                    "returncode": 65,
                    "failure_class": "adaptive_semantic_stall",
                    "adaptive_semantic_stall_evidence": {
                        "status": "proven_semantic_stall"
                    },
                },
                "identity": {"identity_source": "full_remote_job_contract"},
            }
            def bounded_log_tail(
                argv: list[str], destination: Path, timeout_sec: int
            ) -> subprocess.CompletedProcess[str]:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("VCS semantic-stall tail\n", encoding="utf-8")
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=recovered,
            ), patch.object(
                board_vcs,
                "run_command",
                self.successful_remote_mock(run_dir, calls),
            ), patch.object(
                board_vcs,
                "run_stream_transfer_command",
                side_effect=bounded_log_tail,
            ):
                result = board_vcs.execute(run_dir, 0)

            progress_output = result["outputs"]["progress_event_log"]
            simulation_output = result["outputs"]["simulation_log"]
            progress_transfers = [
                argv
                for argv, _ in calls
                if argv
                and argv[0] == "scp"
                and (
                    "progress_event_log.jsonl" in str(argv[-2])
                    or "simulation.log" in str(argv[-2])
                )
            ]

        self.assertEqual(result["status"], "fail")
        self.assertEqual(progress_output["transfer"], "reused_bound_live_progress")
        self.assertFalse(progress_output["full_remote_log_downloaded"])
        self.assertEqual(simulation_output["transfer"], "bounded_remote_log_tail")
        self.assertFalse(simulation_output["full_remote_log_downloaded"])
        self.assertEqual(progress_transfers, [])

    def test_indeterminate_remote_identity_never_prepares_or_relaunches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            recovered = {
                "recovery_state": "indeterminate",
                "status": "fail",
                "failure_class": "remote_semantic_recovery_indeterminate",
                "remote_job_preserved": True,
                "summary": "candidate probe transport is indeterminate",
            }
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=recovered,
            ), patch.object(board_vcs, "run_command") as remote, patch.object(
                board_vcs,
                "run_remote_background_command",
            ) as relaunch:
                result = board_vcs.execute(run_dir, 0)
            self.assertEqual(result["phase"], "remote_recovery_indeterminate")
            self.assertEqual(result["status"], "fail")
            self.assertEqual(len(result["input_fingerprint_sha256"]), 64)
            remote.assert_not_called()
            relaunch.assert_not_called()

    def test_unbounded_timeout_adds_no_remote_or_local_wall_clock_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, _, _ = self.make_run(Path(tmp))
            calls: list[tuple[list[str], int | None]] = []
            detached_calls: list[tuple[str, int, str]] = []
            with patch.object(
                board_vcs,
                "validate_exact_board_preflight",
                return_value=self.exact_board_preflight(),
            ), patch.object(
                board_vcs,
                "recover_exact_remote_semantic_job",
                return_value=None,
            ), patch.object(
                board_vcs,
                "validate_exact_board_acceptance",
                return_value=self.exact_board_acceptance(),
            ), patch.object(board_vcs, "run_command", self.successful_remote_mock(run_dir, calls)), patch.object(
                board_vcs,
                "run_remote_background_command",
                self.successful_detached_mock(detached_calls),
            ):
                result = board_vcs.execute(run_dir, 0)
            self.assertEqual(result["status"], "pass")
            self.assertEqual([row[1] for row in detached_calls], [0, 0])
            self.assertTrue(all("timeout " not in row[2] for row in detached_calls))

    def test_cctg_progress_contract_binds_split_board_and_certificate_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            certificate = run_dir / "verification" / "certificates" / "single.json"
            certificate.parent.mkdir(parents=True, exist_ok=True)
            certificate.write_text("{}\n", encoding="utf-8")
            write_json(
                run_dir / "verification" / "single_layer" / "single_layer_sim_stats.json",
                {
                    "status": "pass",
                    "input_beats": 8,
                    "output_beats": 8,
                    "expected_beats": 8,
                    "cycles": 100,
                },
            )
            integration = {
                "source_closure_sha256": "a" * 64,
                "scheduler": {"accepted_output_beats_per_layer": 8},
                "intra_layer_spatial_pipeline": {
                    "status": "ready",
                    "preserved": True,
                    "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                    "different_tokens_overlap_across_required_dataflow": True,
                    "serial_leaf_execution": False,
                },
            }
            write_json(
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json",
                {
                    "multilayer_harness": {
                        "single_layer_promotion_certificate": {
                            "path": str(certificate)
                        }
                    },
                    "board_integration_contract": integration,
                },
            )

            contract = board_vcs.cctg_progress_contract(
                run_dir, {"board_integration_contract": integration}
            )

        self.assertEqual(contract["target_input_beats"], 8)
        self.assertEqual(contract["target_output_beats"], 8)
        self.assertEqual(contract["single_layer_cycles"], 100)
        self.assertTrue(contract["intra_layer_pipeline_contract"]["required"])
        self.assertEqual(contract["source_closure_sha256"], "a" * 64)


if __name__ == "__main__":
    unittest.main()
