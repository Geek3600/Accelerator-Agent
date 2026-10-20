from argparse import Namespace
import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.fpga_ip_contract import simulation_source_contract
from accagent.framework.semantic_simulator import (
    LeafSemanticProgressObserver,
    MAX_VCS_COMPILE_JOBS,
    MEMORY_INIT_DEFINE,
    REMOTE_ARTIFACT_RECEIPT,
    REMOTE_JOB_RETRY_REQUEST,
    SEMANTIC_STALL_EXIT_CODE,
    ZERO_TIME_LIVELOCK_EXIT_CODE,
    adaptive_stall_evidence_from_progress_callback,
    configured_vcs,
    normalized_exit_signal,
    parse_remote_job_state_probe,
    persistent_remote_artifact_root,
    persistent_remote_tool_workdir,
    progress_callback_observation,
    prepare_remote_artifact_acknowledgment_retry,
    finalize_remote_artifact_acknowledgment_retry,
    persist_remote_artifact_receipt,
    recover_exact_remote_semantic_job,
    remote_job_state_probe_command,
    reusable_semantic_execution,
    remote_stage_cleanup_command,
    remote_stage_prune_command,
    remote_artifact_keep_completed,
    run_remote_background_command,
    run_remote_vcs_semantic_harness,
    run_configured_chisel_top_compile,
    semantic_input_fingerprint,
    semantic_memory_init_payload,
    semantic_fpga_ip_static_binding,
    semantic_remote_job_contract,
    semantic_stall_termination_label_allowed,
    semantic_vcs_compile_jobs,
    semantic_vcs_compile_define_args,
    semantic_vcs_parallel_compile_args,
    sha256_file,
    ssh_options,
    wall_timeout,
    diagnostic_testbench_overlay,
    harness_control_probe_signals,
)
from accagent.framework.debug_closure import load_trace_records, localize_failure, targeted_replay_plan
from accagent.framework.live_state import activate_live_state_slot, read_live_state
from accagent.framework.stage_debug_loop import stage6_scope_env
from scripts.verification.case_leaf_operator_verify import (
    execute_stage_reports as execute_case_stage_reports,
    internal_trace_records as case_internal_trace_records,
)
from scripts.verification.qwen_leaf_operator_verify import (
    aggregate_report,
    execute_stage_reports,
    internal_trace_records,
    numeric_compare,
    semantic_sim_timeout_sec,
    semantic_stage_max_workers,
    semantic_stage_report,
)
from scripts.verification.case_single_layer_stream_sim import functional_mode as single_layer_functional_mode


class SemanticSimulatorTest(TestCase):
    def test_generated_chisel_top_compile_uses_remote_vcs_without_running_simv(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            chisel_dir = run_dir / "generated" / "chisel"
            (chisel_dir / "runtime").mkdir(parents=True)
            (chisel_dir / "runtime" / "runtime_config.json").write_text(
                json.dumps({"chisel_top": "TinyBlock"}), encoding="utf-8"
            )
            (chisel_dir / "filelist.f").write_text("TinyBlock.sv\nTinyLeaf.sv\n", encoding="utf-8")
            (chisel_dir / "TinyBlock.sv").write_text(
                "module TinyBlock(input clock, input reset); TinyLeaf leaf(); endmodule\n", encoding="utf-8"
            )
            (chisel_dir / "TinyLeaf.sv").write_text(
                "module TinyLeaf; endmodule\n", encoding="utf-8"
            )

            def fake_copy(_host, _port, _remote, local_path, _cwd, _timeout):
                local_path.write_text("VCS elaboration succeeded\n", encoding="utf-8")
                return {"status": "pass"}

            with patch(
                "accagent.framework.semantic_simulator.configured_vcs",
                return_value=(
                    {
                        "name": "vcs",
                        "scope": "remote",
                        "host": "vcs-host",
                        "port": 22,
                        "executable": "/tools/vcs/bin/vcs",
                        "env": {},
                    },
                    [],
                ),
            ), patch(
                "accagent.framework.semantic_simulator.semantic_fpga_ip_static_binding",
                return_value=({"status": "not_required"}, []),
            ), patch(
                "accagent.framework.semantic_simulator.semantic_memory_init_payload",
                return_value=([], [], []),
            ), patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value={"status": "pass", "returncode": 0},
            ), patch(
                "accagent.framework.semantic_simulator.run_remote_background_command",
                return_value={"status": "pass", "returncode": 0, "summary": "compiled"},
            ) as remote_compile, patch(
                "accagent.framework.semantic_simulator.copy_remote_file",
                side_effect=fake_copy,
            ):
                report = run_configured_chisel_top_compile(run_dir, 60)
                leaf_report = run_configured_chisel_top_compile(run_dir, 60, compile_leaf_modules=True)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["compile_evidence"]["top_module"], "TinyBlock")
        self.assertEqual(report["simulation"]["status"], "not_run")
        self.assertIn("-top TinyBlock", report["compile_evidence"]["command"])
        self.assertEqual(leaf_report["compile_evidence"]["top_modules"], ["TinyBlock", "TinyLeaf"])
        self.assertIn("-top TinyLeaf", leaf_report["compile_evidence"]["command"])
        self.assertNotIn("-top TinyLeaf", report["compile_evidence"]["command"])
        self.assertEqual(leaf_report["verification_layer"], "layer1_operator_leaf_modules")
        self.assertEqual(remote_compile.call_count, 2)
        self.assertNotIn("./simv", remote_compile.call_args.args[2])

    def test_single_layer_compile_only_does_not_require_semantic_scaffold(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
        ), patch(
            "scripts.verification.case_single_layer_stream_sim.run_configured_chisel_top_compile",
            return_value={
                "status": "pass",
                "top_module": "TinyBlock",
                "source_fingerprint_sha256": "a" * 64,
                "compile_evidence": {"status": "pass", "log_sha256": "b" * 64},
            },
        ) as compiler:
            run_dir = Path(temp_dir)
            status = single_layer_functional_mode(Namespace(run_dir=run_dir))
            report = json.loads(
                (run_dir / "verification" / "single_layer" / "single_layer_functional_report.json").read_text()
            )

        self.assertEqual(status, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["validation_policy"], "vcs_compile_only")
        self.assertEqual(report["simulation"]["status"], "not_run")
        self.assertFalse((run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json").exists())
        compiler.assert_called_once_with(run_dir, 0)

    def test_leaf_compile_only_does_not_require_semantic_scaffold(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
        ), patch(
            "scripts.verification.case_leaf_operator_verify.run_configured_chisel_top_compile",
            return_value={
                "status": "pass",
                "compile_evidence": {"status": "pass", "top_modules": ["Norm", "Attention"]},
            },
        ) as compiler, patch(
            "scripts.verification.case_leaf_operator_verify.semantic_stage_report",
            side_effect=AssertionError("compile-only must not use a semantic testbench"),
        ):
            run_dir = Path(temp_dir)
            manifest = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"status": "incomplete"}), encoding="utf-8")
            reports = execute_case_stage_reports(
                run_dir,
                [{"stage_id": "stage_00_norm"}, {"stage_id": "stage_01_attention"}],
                "functional", 60, "compile-test", run_dir / "leaf",
            )

        self.assertEqual([report["status"] for report in reports], ["pass", "pass"])
        self.assertTrue(all(report["validation_policy"] == "vcs_compile_only" for report in reports))
        self.assertTrue(all(report["simulation"]["status"] == "not_run" for report in reports))
        compiler.assert_called_once_with(run_dir, 60, compile_leaf_modules=True)

    def test_leaf_compile_only_preserves_compiler_failure(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ, {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
        ), patch(
            "scripts.verification.case_leaf_operator_verify.run_configured_chisel_top_compile",
            return_value={"status": "fail", "blockers": ["VCS unresolved module"]},
        ):
            run_dir = Path(temp_dir)
            reports = execute_case_stage_reports(
                run_dir, [{"stage_id": "stage_00_norm"}], "functional", 60,
                "compile-test", run_dir / "leaf",
            )

        self.assertEqual(reports[0]["status"], "fail")
        self.assertEqual(reports[0]["blockers"], ["VCS unresolved module"])

    def test_harness_control_probe_signals_recurse_into_generated_dut(self) -> None:
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "Harness.sv"
            source.write_text(
                """module Harness;
  Child dut();
endmodule
module Child;
  reg [4:0] state;
  wire io_in_ready;
  GrandChild core();
endmodule
module GrandChild;
  wire io_out_valid;
endmodule
""",
                encoding="ascii",
            )
            probes = harness_control_probe_signals(
                {
                    "top_module": "Harness",
                    "source_files": [{"path": str(source)}],
                },
                include_descendant_controls=True,
            )

        self.assertIn("dut.state", probes)
        self.assertIn("dut.core.io_out_valid", probes)

    def test_diagnostic_testbench_overlay_emits_generic_leaf_boundary_records(self) -> None:
        source = """module semantic_stage_tb;
  reg clock = 0;
  reg reset = 1;
  reg input_0_valid = 0;
  wire input_0_ready;
  reg [31:0] input_0_data = 0;
  integer input_0_accepted = 0;
  reg weight_valid = 0;
  wire weight_ready;
  reg [31:0] weight_data = 0;
  integer weight_accepted = 0;
  wire output_valid;
  reg output_ready = 1;
  reg [31:0] output_data = 0;
  integer output_produced = 0;
  integer output_fd;
  integer cycles = 0;
  initial begin
    output_fd = $fopen("out", "w");
    if (!output_fd) $fatal(1, "cannot open semantic RTL output capture");
    reset = 0;
    if (input_0_valid && input_0_ready) input_0_accepted = input_0_accepted + 1;
    if (weight_valid && weight_ready) begin
      weight_accepted = weight_accepted + 1;
    end
    if (output_valid && output_ready) begin
      output_produced = output_produced + 1;
    end
    $fclose(output_fd);
  end
endmodule
"""
        overlay, metadata = diagnostic_testbench_overlay(
            source,
            "stage_00_norm",
            ["_dut_io_in_ready"],
        )
        self.assertEqual(metadata["status"], "ready")
        self.assertIn("boundary=tb.reset_release", overlay)
        self.assertIn("boundary=tb.input_0", overlay)
        self.assertIn("boundary=tb.weight", overlay)
        self.assertIn("boundary=tb.output", overlay)
        self.assertIn("boundary=tb.capture_close", overlay)
        self.assertIn("boundary=harness._dut_io_in_ready", overlay)
        self.assertIn(
            "    if (input_0_valid && input_0_ready) begin\n"
            "      input_0_accepted = input_0_accepted + 1;\n"
            "      $display(\"SPATIALACC_INTERNAL_TRACE stage=stage_00_norm boundary=tb.input_0",
            overlay,
        )
        self.assertIn(
            "    if (!reset && heartbeat_phase == \"streaming\" &&\n"
            "        (cycles % HEARTBEAT_PERIOD_CYCLES) == 0) begin\n"
            "      $display(\"SPATIALACC_INTERNAL_TRACE stage=stage_00_norm boundary=tb.input_0_snapshot",
            overlay,
        )
        self.assertNotEqual(overlay, source)

    def test_diagnostic_overlay_binds_targeted_boundary_and_descendant_probe(self) -> None:
        source = """module semantic_stage_tb;
  reg clock = 0;
  reg reset = 1;
  integer input_0_accepted = 0;
  initial begin
    reset = 0;
  end
endmodule
"""
        overlay, metadata = diagnostic_testbench_overlay(
            source,
            "stage_00_norm",
            ["dut.state"],
            "boundary.edge_input_to_stage_00",
        )

        self.assertIn("target=", overlay)
        self.assertIn("dut.state", overlay)
        self.assertEqual(metadata["target_boundary"], "boundary.edge_input_to_stage_00")

    def test_diagnostic_overlay_qualifies_harness_relative_descendant_probe(self) -> None:
        source = """module semantic_stage_tb;
  reg clock = 0;
  reg reset = 1;
  integer input_0_accepted = 0;
  initial begin
    reset = 0;
  end
endmodule
"""
        overlay, metadata = diagnostic_testbench_overlay(
            source,
            "stage_00_norm",
            ["dut.state"],
            "boundary.edge_input_to_stage_00",
            probe_paths_relative_to_harness=True,
        )

        self.assertIn("dut.dut.state", overlay)
        self.assertTrue(metadata["probe_paths_relative_to_harness"])

    def test_diagnostic_overlay_reports_missing_probe_sites(self) -> None:
        source = "module semantic_tb; initial begin end endmodule\n"
        overlay, metadata = diagnostic_testbench_overlay(source, "stage")
        self.assertEqual(metadata["status"], "no_supported_probe_sites")
        self.assertEqual(overlay, source)

    @staticmethod
    def leaf_observation(log_tail: str, poll_attempt: int = 1) -> dict:
        return {
            "state": "running",
            "pid": 41,
            "poll_attempt": poll_attempt,
            "remote_workdir": "/remote/leaf-job",
            "progress_log_tail": log_tail,
            "process_snapshot": {
                "simulator_like_process_observed": True,
                "processes": [{"pid": 42, "command": "simv"}],
            },
        }

    def test_leaf_progress_observer_proves_zero_time_livelock_from_cpu_and_log(self) -> None:
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            "VCS warning at time 1 ps\n",
                            poll_attempt,
                        )
                    )

            evidence = observer.zero_time_livelock_evidence
            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))

        self.assertEqual(evidence["status"], "proven_zero_time_livelock")
        self.assertEqual(evidence["simulation_time"], {"status": "observed", "value": "1", "unit": "ps"})
        self.assertEqual(evidence["consecutive_unchanged_running_snapshots"], 3)
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertEqual(snapshot["status"], "fail")

    def test_leaf_progress_observer_does_not_stop_when_simulation_time_advances(self) -> None:
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt, sim_time in enumerate((1, 2, 3, 4), start=1):
                    observer(
                        self.leaf_observation(
                            f"VCS warning at time {sim_time} ps\n",
                            poll_attempt,
                        )
                    )

        self.assertEqual(observer.zero_time_livelock_evidence, {})

    def test_leaf_progress_observer_reads_generated_heartbeat_time(self) -> None:
        heartbeat = (
            "SPATIALACC_LEAF_HEARTBEAT at time 10240 ps "
            "phase=streaming cycles=1024 input_0_accepted=1024 output_beats=0\n"
        )

        self.assertEqual(
            LeafSemanticProgressObserver._simulation_time(heartbeat),
            {"status": "observed", "value": "10240", "unit": "ps"},
        )

    def test_leaf_progress_observer_does_not_stop_advancing_contract_heartbeat(self) -> None:
        contract = {
            "input_vectors": [{"beats": 4096}],
            "expected_output": {"beats": 4096},
        }
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
                heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt, accepted in enumerate((256, 512, 768, 1024), start=1):
                    observer(
                        self.leaf_observation(
                            "SPATIALACC_LEAF_HEARTBEAT at time "
                            f"{poll_attempt * 10240} ps phase=streaming "
                            f"cycles={poll_attempt * 1024} "
                            f"input_0_accepted={accepted} output_beats=0\n",
                            poll_attempt,
                        )
                    )

        self.assertEqual(observer.adaptive_semantic_stall_evidence, {})

    def test_leaf_progress_observer_proves_contract_bound_heartbeat_stall(self) -> None:
        contract = {
            "input_vectors": [{"beats": 4096}],
            "expected_output": {"beats": 4096},
        }
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
                heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            "SPATIALACC_LEAF_HEARTBEAT at time "
                            f"{poll_attempt * 10240} ps phase=streaming "
                            f"cycles={poll_attempt * 1024} "
                            "input_0_accepted=256 output_beats=0\n",
                            poll_attempt,
                        )
                    )

            evidence = observer.adaptive_semantic_stall_evidence
            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))
            callback_evidence = adaptive_stall_evidence_from_progress_callback(
                observer,
                "/remote/leaf-job",
            )

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["heartbeat"]["input_accepted"], {"input_0_accepted": 256})
        self.assertEqual(evidence["heartbeat_contract"]["expected_output_beats"], 4096)
        self.assertEqual(evidence["consecutive_heartbeat_stall_snapshots"], 3)
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertEqual(snapshot["status"], "fail")
        self.assertEqual(callback_evidence["status"], "proven_semantic_stall")

    def test_leaf_loader_heartbeat_distinguishes_progress_from_partial_stall(self) -> None:
        for phase, counter, stream_key in (
            ("loading_weights", "weight_accepted", "real_weight_stream"),
            ("loading_runtime", "runtime_accepted", "runtime_constant_stream"),
        ):
            for counts, stalled in (([12, 24, 36, 48], False), ([12, 12, 12, 12], True), ([120, 120, 120, 120], False)):
                with self.subTest(phase=phase, counts=counts), TemporaryDirectory() as temp_dir:
                    observer = LeafSemanticProgressObserver(
                        run_dir=Path(temp_dir), stage_id="stage_leaf", host="user@host", port=22,
                        heartbeat_contract={
                            "input_vectors": [{"beats": 4096}], "expected_output": {"beats": 4096},
                            stream_key: {"word_count": 120},
                        },
                    )
                    observer.fingerprint = "f" * 64
                    with patch.object(observer, "_simulator_cpu_probe", side_effect=[
                        {"status": "observed", "total_ticks": tick, "processes": []}
                        for tick in (100, 120, 140, 160)
                    ]):
                        for poll_attempt, count in enumerate(counts, start=1):
                            observer(self.leaf_observation(
                                "SPATIALACC_LEAF_HEARTBEAT at time "
                                f"{poll_attempt * 10240} ps phase={phase} cycles={poll_attempt * 1024} "
                                f"input_0_accepted=0 {counter}={count} output_beats=0\n",
                                poll_attempt,
                            ))
                    evidence = observer.adaptive_semantic_stall_evidence
                    self.assertEqual(evidence.get("status") == "proven_semantic_stall", stalled)
                    if stalled:
                        self.assertEqual(evidence["heartbeat"]["loader_accepted"], {counter: 12})
                        self.assertEqual(evidence["heartbeat_contract"]["loader_word_targets"], {counter: 120})

    def test_completed_leaf_recovery_restores_only_same_job_stall_history(self) -> None:
        contract = {"input_vectors": [{"beats": 4096}], "expected_output": {"beats": 4096}}
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            observer = LeafSemanticProgressObserver(
                run_dir=run_dir, stage_id="stage_leaf", host="user@host", port=22, heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(observer, "_simulator_cpu_probe", side_effect=[
                {"status": "observed", "total_ticks": tick, "processes": []}
                for tick in (100, 120, 140, 160)
            ]):
                for poll_attempt in range(1, 5):
                    observer(self.leaf_observation(
                        "SPATIALACC_LEAF_HEARTBEAT at time "
                        f"{poll_attempt * 10240} ps phase=streaming cycles={poll_attempt * 1024} "
                        "input_0_accepted=256 output_beats=0\n", poll_attempt,
                    ))
            proven_stall = observer.adaptive_semantic_stall_evidence
            completed = self.leaf_observation("") | {"state": "done", "process_snapshot": {}}
            observer.fingerprint = "b" * 64
            observer(completed | {"remote_workdir": "/remote/other-job"})
            observer.fingerprint = "f" * 64
            observer(completed)
            self.assertEqual(observer.adaptive_semantic_stall_evidence, {})
            self.assertEqual(adaptive_stall_evidence_from_progress_callback(observer, "/remote/leaf-job"), proven_stall)
            self.assertEqual(adaptive_stall_evidence_from_progress_callback(observer, "/remote/other-job"), {})
            observer.fingerprint = "c" * 64
            self.assertEqual(adaptive_stall_evidence_from_progress_callback(observer, "/remote/leaf-job"), {})
            observer.fingerprint = "f" * 64
            with patch.object(observer, "_simulator_cpu_probe", return_value={"status": "observed", "total_ticks": 200, "processes": []}):
                observer(self.leaf_observation(
                    "SPATIALACC_LEAF_HEARTBEAT at time 51200 ps phase=streaming cycles=5120 "
                    "input_0_accepted=512 output_beats=0\n",
                ))
            self.assertEqual(adaptive_stall_evidence_from_progress_callback(observer, "/remote/leaf-job"), {})

    def test_leaf_progress_observer_does_not_stop_without_trusted_heartbeat(self) -> None:
        contract = {
            "input_vectors": [{"beats": 4096}],
            "expected_output": {"beats": 4096},
        }
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
                heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            f"VCS warning at time {poll_attempt} ps\n",
                            poll_attempt,
                        )
                    )

        self.assertEqual(observer.adaptive_semantic_stall_evidence, {})

    def test_leaf_progress_observer_requires_cpu_progress_for_heartbeat_stall(self) -> None:
        contract = {
            "input_vectors": [{"beats": 4096}],
            "expected_output": {"beats": 4096},
        }
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
                heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                return_value={"status": "observed", "total_ticks": 100, "processes": []},
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            "SPATIALACC_LEAF_HEARTBEAT at time "
                            f"{poll_attempt * 10240} ps phase=streaming "
                            f"cycles={poll_attempt * 1024} "
                            "input_0_accepted=256 output_beats=0\n",
                            poll_attempt,
                        )
                    )

        self.assertEqual(observer.adaptive_semantic_stall_evidence, {})

    def test_leaf_progress_observer_tracks_all_contract_inputs(self) -> None:
        contract = {
            "input_vectors": [{"beats": 4096}, {"beats": 4096}],
            "expected_output": {"beats": 4096},
        }
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
                heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            "SPATIALACC_LEAF_HEARTBEAT at time "
                            f"{poll_attempt * 10240} ps phase=streaming "
                            f"cycles={poll_attempt * 1024} "
                            "input_0_accepted=256 input_1_accepted=0 output_beats=0\n",
                            poll_attempt,
                        )
                    )

            evidence = observer.adaptive_semantic_stall_evidence

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(
            evidence["heartbeat"]["input_accepted"],
            {"input_0_accepted": 256, "input_1_accepted": 0},
        )

    def test_leaf_progress_observer_detects_stall_before_first_input(self) -> None:
        contract = {
            "input_vectors": [{"beats": 1792}],
            "expected_output": {"beats": 1792},
        }
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
                heartbeat_contract=contract,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                side_effect=[
                    {"status": "observed", "total_ticks": tick, "processes": []}
                    for tick in (100, 120, 140, 160)
                ],
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            "SPATIALACC_LEAF_HEARTBEAT at time "
                            f"{poll_attempt * 10240} ps phase=streaming "
                            f"cycles={poll_attempt * 1024} "
                            "input_0_accepted=0 output_beats=0\n",
                            poll_attempt,
                        )
                    )

            evidence = observer.adaptive_semantic_stall_evidence

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["heartbeat"]["input_accepted"], {"input_0_accepted": 0})

    def test_leaf_progress_observer_requires_cpu_or_native_loop_witness(self) -> None:
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
            )
            observer.fingerprint = "f" * 64
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                return_value={"status": "observed", "total_ticks": 100, "processes": []},
            ):
                for poll_attempt in range(1, 5):
                    observer(
                        self.leaf_observation(
                            "VCS warning at time 1 ps\n",
                            poll_attempt,
                        )
                    )

        self.assertEqual(observer.zero_time_livelock_evidence, {})

    def test_leaf_progress_observer_marks_terminal_job_completed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            observer = LeafSemanticProgressObserver(
                run_dir=Path(temp_dir),
                stage_id="stage_leaf",
                host="user@host",
                port=22,
            )
            observer.fingerprint = "f" * 64
            observation = self.leaf_observation("", poll_attempt=2)
            observation["state"] = "done"
            observation["process_snapshot"]["simulator_like_process_observed"] = False
            with patch.object(
                observer,
                "_simulator_cpu_probe",
                return_value={"status": "not_observed", "processes": []},
            ):
                observer(observation)

            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))

        self.assertEqual(snapshot["process_state"], "done")
        self.assertEqual(snapshot["status"], "completed")

    def test_progress_callback_reads_only_an_opted_in_remote_log_tail(self) -> None:
        class Callback:
            remote_progress_log_name = "sim.stderr.log"

        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            return_value={
                "status": "pass",
                "returncode": 0,
                "stdout_tail": "SPATIALACC_PIPELINE_TRACE boundary=edge.input",
            },
        ) as invoke:
            observation = progress_callback_observation(
                Callback(),
                host="user@host",
                port=22,
                remote_dir="/remote/exact-fingerprint",
                cwd=Path(temp_dir),
                state="running",
                pid=7,
                poll_attempt=3,
                label="vcs_simulate",
            )

        self.assertIn("SPATIALACC_PIPELINE_TRACE", observation["progress_log_tail"])
        self.assertEqual(observation["progress_log_transport"]["status"], "pass")
        self.assertIn("tail -c 12000", invoke.call_args.args[0][-1])

    def test_leaf_progress_reads_detached_stdout_when_sim_log_is_empty(self) -> None:
        class Callback:
            remote_progress_log_name = "sim.log"

        def local_command(argv, cwd, timeout_sec):
            result = subprocess.run(["bash", "-c", argv[-1]], cwd=cwd, capture_output=True, text=True, timeout=timeout_sec)
            return {"status": "pass", "returncode": result.returncode, "stdout_tail": result.stdout}

        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result", side_effect=local_command,
        ):
            workdir = Path(temp_dir)
            stdout = "SPATIALACC_LEAF_HEARTBEAT at time 75000 ps phase=reset_release cycles=0 input_0_accepted=0 output_beats=0\n"
            (workdir / ".spatialacc_vcs_simulate.stdout.log").write_text(stdout, encoding="utf-8")
            for named_log in ("", "SPATIALACC_LEAF_HEARTBEAT at time 95000 ps phase=streaming cycles=2 input_0_accepted=1 output_beats=0\n"):
                with self.subTest(named_log_empty=not named_log):
                    (workdir / "sim.log").write_text(named_log, encoding="utf-8")
                    observation = progress_callback_observation(
                        Callback(), host="user@host", port=22, remote_dir=temp_dir,
                        cwd=workdir, state="running", pid=7, poll_attempt=3, label="vcs_simulate",
                    )
                    self.assertEqual(observation["progress_log_tail"], named_log or stdout)
                    self.assertEqual(observation["progress_log_transport"]["returncode"], 0)

    def test_semantic_stall_termination_allows_only_board_simulation_namespaces(
        self,
    ) -> None:
        self.assertTrue(semantic_stall_termination_label_allowed("vcs_simulate"))
        self.assertTrue(
            semantic_stall_termination_label_allowed("vcs_fast_replay_restore")
        )
        self.assertTrue(
            semantic_stall_termination_label_allowed("vcs_fast_replay_recapture")
        )
        self.assertTrue(
            semantic_stall_termination_label_allowed(
                "vcs_checkpoint_equivalence_simulate_oracle_v2_deadbeef"
            )
        )
        self.assertFalse(
            semantic_stall_termination_label_allowed("vcs_compile_deadbeef")
        )
        self.assertFalse(
            semantic_stall_termination_label_allowed("arbitrary_remote_job")
        )

    def test_zero_real_tool_wall_budget_is_unbounded(self) -> None:
        self.assertIsNone(wall_timeout(0))
        self.assertIsNone(wall_timeout(-1))
        self.assertEqual(wall_timeout(60), 60)

    def test_remote_ssh_transport_has_long_run_keepalive(self) -> None:
        options = ssh_options(22)
        self.assertIn("ServerAliveInterval=30", options)
        self.assertIn("ServerAliveCountMax=240", options)
        self.assertIn("TCPKeepAlive=yes", options)

    def test_remote_job_probe_captures_bounded_simulator_session_tree(self) -> None:
        command = remote_job_state_probe_command(
            "/remote/run", ".spatialacc_vcs_simulate.pid", ".spatialacc_vcs_simulate.exit"
        )
        syntax = subprocess.run(
            ["bash", "-n", "-c", command],
            check=False,
            capture_output=True,
            text=True,
        )
        parsed = parse_remote_job_state_probe(
            "\n".join(
                [
                    "SPATIALACC_REMOTE_JOB_STATUS state=running pid=71",
                    "SPATIALACC_REMOTE_JOB_PROCESS pid=71 ppid=1 pgid=71 sid=71 stat=Ss comm=bash",
                    "SPATIALACC_REMOTE_JOB_PROCESS pid=75 ppid=71 pgid=71 sid=71 stat=R comm=simv",
                    "SPATIALACC_REMOTE_JOB_PROCESS_SUMMARY count=2 truncated=false",
                ]
            )
        )

        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertEqual(parsed["state"], "running")
        self.assertEqual(parsed["pid"], 71)
        self.assertEqual(parsed["process_snapshot"]["reported_process_count"], 2)
        self.assertTrue(
            parsed["process_snapshot"]["simulator_like_process_observed"]
        )
        self.assertEqual(
            parsed["process_snapshot"]["simulator_process_commands"], ["simv"]
        )
        self.assertEqual(normalized_exit_signal(139), 11)
        self.assertEqual(normalized_exit_signal(-11), 11)

    def test_remote_job_probe_observes_a_real_detached_session(self) -> None:
        with TemporaryDirectory() as temp_dir:
            process = subprocess.Popen(
                ["setsid", "sleep", "30"],
                cwd=temp_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                Path(temp_dir, ".probe.pid").write_text(
                    f"{process.pid}\n", encoding="utf-8"
                )
                command = remote_job_state_probe_command(
                    temp_dir, ".probe.pid", ".probe.exit"
                )
                result = subprocess.run(
                    ["bash", "-lc", command],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                parsed = parse_remote_job_state_probe(result.stdout)
            finally:
                process.terminate()
                process.wait(timeout=5)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(parsed["state"], "running")
        self.assertGreaterEqual(
            parsed["process_snapshot"]["reported_process_count"], 1
        )
        self.assertTrue(parsed["process_snapshot"]["processes"])
        self.assertEqual(
            parsed["process_snapshot"]["processes"][0]["pid"], process.pid
        )

    def test_remote_runner_records_simulator_signal_ownership(self) -> None:
        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            side_effect=[
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=71",
                },
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "\n".join(
                        [
                            "SPATIALACC_REMOTE_JOB_STATUS state=running pid=71",
                            "SPATIALACC_REMOTE_JOB_PROCESS pid=71 ppid=1 pgid=71 sid=71 stat=Ss comm=bash",
                            "SPATIALACC_REMOTE_JOB_PROCESS pid=75 ppid=71 pgid=71 sid=71 stat=R comm=simv",
                            "SPATIALACC_REMOTE_JOB_PROCESS_SUMMARY count=2 truncated=false",
                        ]
                    ),
                },
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "\n".join(
                        [
                            "SPATIALACC_REMOTE_JOB_STATUS state=running pid=71",
                            "SPATIALACC_REMOTE_JOB_PROCESS_SUMMARY count=0 truncated=false",
                        ]
                    ),
                },
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=done rc=139",
                },
            ],
        ), patch(
            "accagent.framework.semantic_simulator.copy_remote_file",
            return_value={"status": "pass", "returncode": 0},
        ), patch("accagent.framework.semantic_simulator.time.sleep"):
            result = run_remote_background_command(
                "user@host",
                22,
                "./vcs_work/simv +INPUT=input.memh",
                "/remote/run",
                Path(temp_dir),
                60,
                "vcs_simulate",
            )

        provenance = result["runner_process_provenance"]
        self.assertEqual(result["returncode"], 139)
        self.assertEqual(provenance["signal_number"], 11)
        self.assertEqual(
            provenance["attribution"],
            "runner_owned_simulator_process_signal_exit",
        )
        self.assertTrue(
            provenance["last_running_process_snapshot"]["simulator_like_process_observed"]
        )
        self.assertEqual(provenance["last_simulator_process_commands"], ["simv"])

    def test_remote_background_job_tolerates_transient_poll_disconnect(self) -> None:
        observations = []
        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            side_effect=[
                {"status": "pass", "returncode": 0, "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=10"},
                {"status": "fail", "returncode": 255, "stderr_tail": "connection reset"},
                {"status": "pass", "returncode": 0, "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=running pid=10"},
                {"status": "pass", "returncode": 0, "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=done rc=0"},
            ],
        ), patch(
            "accagent.framework.semantic_simulator.copy_remote_file",
            return_value={"status": "pass", "returncode": 0},
        ), patch("accagent.framework.semantic_simulator.time.sleep"):
            result = run_remote_background_command(
                "user@host",
                22,
                "./simv",
                "/remote/run",
                Path(temp_dir),
                60,
                "simulation",
                observations.append,
            )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["poll_transport_failures"], 1)
        self.assertEqual(result["transport"], "detached_remote_job_with_short_ssh_polling")
        self.assertEqual(
            [row["state"] for row in observations], ["running", "done"]
        )
        self.assertEqual(observations[0]["pid"], 10)

    def test_remote_background_job_closes_only_a_proven_adaptive_semantic_stall(self) -> None:
        class ProgressCallback:
            def __init__(self, root: Path) -> None:
                self.snapshot_path = root / "live_progress.json"
                self.raw_path = root / "progress.jsonl"
                self.fingerprint = "f" * 64

            def __call__(self, observation: dict) -> None:
                self.snapshot_path.write_text(
                    json.dumps(
                        {
                            "input_fingerprint_sha256": self.fingerprint,
                            "remote_workdir": observation["remote_workdir"],
                            "adaptive_semantic_stall_evidence": {
                                "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                                "status": "proven_semantic_stall",
                                "fixed_wall_clock_timeout": False,
                                "fixed_cycle_timeout": False,
                            },
                        }
                    ),
                    encoding="utf-8",
                )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            callback = ProgressCallback(root)
            with patch(
                "accagent.framework.semantic_simulator.command_result",
                side_effect=[
                    {"status": "pass", "returncode": 0, "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=10"},
                    {"status": "pass", "returncode": 0, "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=running pid=10"},
                    {
                        "status": "pass",
                        "returncode": 0,
                        "stdout_tail": (
                            "SPATIALACC_ADAPTIVE_SEMANTIC_STALL_TERMINATED "
                            "state=terminated pid=10 rc=86"
                        ),
                    },
                    {"status": "pass", "returncode": 0, "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=done rc=86"},
                ],
            ) as invoke, patch(
                "accagent.framework.semantic_simulator.copy_remote_file",
                return_value={"status": "pass", "returncode": 0},
            ), patch("accagent.framework.semantic_simulator.time.sleep"):
                result = run_remote_background_command(
                    "user@host",
                    22,
                    "./simv",
                    "/remote/run",
                    root,
                    0,
                    "vcs_simulate",
                    callback,
                )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["returncode"], SEMANTIC_STALL_EXIT_CODE)
        self.assertEqual(result["failure_class"], "adaptive_semantic_stall")
        self.assertEqual(
            result["adaptive_semantic_stall_termination"]["status"], "pass"
        )
        termination_argv = invoke.call_args_list[2].args[0]
        self.assertIn('kill -TERM -- "-$pid"', termination_argv[-1])
        self.assertFalse(
            result["adaptive_semantic_stall_termination"]["fixed_wall_clock_timeout"]
        )

    def test_remote_background_job_closes_a_proven_zero_time_livelock(self) -> None:
        class ProgressCallback:
            def __init__(self) -> None:
                self.zero_time_livelock_evidence = {
                    "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                    "status": "proven_zero_time_livelock",
                    "remote_workdir": "/remote/run",
                    "fixed_wall_clock_timeout": False,
                    "fixed_cycle_timeout": False,
                }

            def __call__(self, observation: dict) -> None:
                return None

        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            side_effect=[
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=10",
                },
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=running pid=10",
                },
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": (
                        "SPATIALACC_ZERO_TIME_LIVELOCK_TERMINATED "
                        "state=terminated pid=10 rc=87"
                    ),
                },
                {
                    "status": "pass",
                    "returncode": 0,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=done rc=87",
                },
            ],
        ), patch(
            "accagent.framework.semantic_simulator.copy_remote_file",
            return_value={"status": "pass", "returncode": 0},
        ), patch("accagent.framework.semantic_simulator.time.sleep"):
            result = run_remote_background_command(
                "user@host",
                22,
                "./simv",
                "/remote/run",
                Path(temp_dir),
                0,
                "vcs_simulate",
                ProgressCallback(),
            )

        self.assertEqual(result["returncode"], ZERO_TIME_LIVELOCK_EXIT_CODE)
        self.assertEqual(result["failure_class"], "zero_time_simulation_livelock")
        self.assertEqual(result["zero_time_livelock_termination"]["status"], "pass")
        self.assertFalse(
            result["zero_time_livelock_termination"]["fixed_wall_clock_timeout"]
        )

    def test_remote_compile_enforces_stage_single_instance_before_prune_and_launch(self) -> None:
        passed = {"status": "pass", "returncode": 0, "stdout_tail": ""}
        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            side_effect=[
                {
                    **passed,
                    "stdout_tail": "SPATIALACC_REMOTE_STAGE_CLEANUP pids=101 102",
                },
                {
                    **passed,
                    "stdout_tail": (
                        "SPATIALACC_REMOTE_STAGE_PRUNE deleted=0 active=0 "
                        "retained=0 unacknowledged=1"
                    ),
                },
                {
                    **passed,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=10",
                },
                {
                    **passed,
                    "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=done rc=0",
                },
            ],
        ) as invoke, patch(
            "accagent.framework.semantic_simulator.copy_remote_file",
            return_value=passed,
        ):
            result = run_remote_background_command(
                "user@host",
                22,
                "vcs -full64",
                "/remote/run/fingerprint_1",
                Path(temp_dir),
                60,
                "vcs_compile",
            )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["remote_stage_cleanup"]["status"], "pass")
        self.assertEqual(result["remote_stage_prune"]["status"], "pass")
        commands = [row.args[0][-1] for row in invoke.call_args_list]
        self.assertIn("SPATIALACC_REMOTE_STAGE_CLEANUP", commands[0])
        self.assertIn("SPATIALACC_REMOTE_STAGE_PRUNE", commands[1])
        self.assertIn("SPATIALACC_REMOTE_JOB_STARTED", commands[2])

    def test_remote_compile_never_launches_when_single_instance_cleanup_fails(self) -> None:
        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            return_value={
                "status": "fail",
                "returncode": 255,
                "stdout_tail": "",
                "stderr_tail": "connection reset",
            },
        ) as invoke, patch(
            "accagent.framework.semantic_simulator.copy_remote_file"
        ) as copy:
            result = run_remote_background_command(
                "user@host",
                22,
                "vcs -full64",
                "/remote/run/fingerprint_1",
                Path(temp_dir),
                60,
                "vcs_compile",
            )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["failure_class"], "remote_stage_cleanup_failure")
        self.assertEqual(result["launch"]["status"], "not_run")
        self.assertEqual(invoke.call_count, 1)
        copy.assert_not_called()

    def test_remote_compile_continues_when_artifact_prune_budget_expires(self) -> None:
        passed = {"status": "pass", "returncode": 0, "stdout_tail": ""}
        with TemporaryDirectory() as temp_dir, patch(
            "accagent.framework.semantic_simulator.command_result",
            side_effect=[
                {**passed, "stdout_tail": "SPATIALACC_REMOTE_STAGE_CLEANUP pids="},
                {"status": "fail", "returncode": 124, "stdout_tail": "", "stderr_tail": ""},
                {**passed, "stdout_tail": "SPATIALACC_REMOTE_JOB_STARTED pid=10"},
                {**passed, "stdout_tail": "SPATIALACC_REMOTE_JOB_STATUS state=done rc=0"},
            ],
        ) as invoke, patch(
            "accagent.framework.semantic_simulator.copy_remote_file",
            return_value=passed,
        ):
            result = run_remote_background_command(
                "user@host",
                22,
                "vcs -full64",
                "/remote/run/fingerprint_1",
                Path(temp_dir),
                60,
                "vcs_compile",
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["remote_stage_prune"]["nonblocking"])
        self.assertIn("maintenance budget", result["remote_stage_prune"]["summary"])
        commands = [row.args[0][-1] for row in invoke.call_args_list]
        self.assertIn("SPATIALACC_REMOTE_JOB_STARTED", commands[2])

    def test_remote_job_contract_binds_full_fingerprint_and_payload(self) -> None:
        with TemporaryDirectory() as temp_dir:
            staging = Path(temp_dir)
            source = staging / "Harness.sv"
            source.write_text("module Harness; endmodule\n", encoding="ascii")

            contract, payload = semantic_remote_job_contract(
                staging,
                fingerprint="a" * 64,
                stage_id="single_layer",
                top_module="semantic_single_layer_tb",
                tool_profile={"host": "builder", "executable": "/eda/vcs"},
                compile_defines=["ENABLE_INITIAL_MEM_"],
                source_names=["Harness.sv"],
                plusargs=["+OUTPUT_MEMH=rtl_output.memh"],
            )

            self.assertEqual(contract["input_fingerprint_sha256"], "a" * 64)
            self.assertEqual(payload, [{"path": "Harness.sv", "sha256": sha256_file(source)}])

    def test_exact_completed_remote_job_is_recovered_without_relaunch(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_path = root / ".spatialacc_semantic_job.json"
            contract_path.write_text("{}\n", encoding="utf-8")
            done = {"state": "done", "returncode": 0, "probe": {"status": "pass"}}
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                return_value=["/remote/stage/abcdefabcdef_1"],
            ), patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches",
                return_value=(True, {"identity_source": "full_remote_job_contract"}),
            ), patch(
                "accagent.framework.semantic_simulator.remote_background_job_state",
                side_effect=[done, done],
            ), patch(
                "accagent.framework.semantic_simulator.run_remote_background_command"
            ) as relaunch, patch(
                "accagent.framework.semantic_simulator.wait_for_existing_remote_job"
            ) as reattach:
                recovered = recover_exact_remote_semantic_job(
                    "builder",
                    22,
                    "/remote/stage",
                    "abcdefabcdef" + "0" * 52,
                    root,
                    contract_path,
                    [],
                    0,
                    "./simv",
                )

            self.assertEqual(recovered["compile"]["status"], "pass")
            self.assertEqual(recovered["simulate"]["status"], "pass")
            relaunch.assert_not_called()
            reattach.assert_not_called()

    def test_compile_only_recovers_remote_compile_without_simulation(self) -> None:
        for remote_state in ("running", "done"):
            with self.subTest(remote_state=remote_state), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                contract_path = root / ".spatialacc_semantic_job.json"
                contract_path.write_text("{}\n", encoding="utf-8")
                with patch(
                    "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                    return_value=["/remote/stage/abcdefabcdef_1"],
                ), patch(
                    "accagent.framework.semantic_simulator.remote_semantic_payload_matches",
                    return_value=(True, {"status": "pass"}),
                ), patch(
                    "accagent.framework.semantic_simulator.remote_background_job_state",
                    return_value={
                        "state": remote_state,
                        "returncode": 0 if remote_state == "done" else None,
                        "probe": {"status": "pass"},
                    },
                ) as state, patch(
                    "accagent.framework.semantic_simulator.wait_for_existing_remote_job",
                    return_value={"status": "pass", "returncode": 0},
                ) as reattach, patch(
                    "accagent.framework.semantic_simulator.run_remote_background_command"
                ) as relaunch:
                    recovered = recover_exact_remote_semantic_job(
                        "builder", 22, "/remote/stage", "abcdefabcdef" + "0" * 52,
                        root, contract_path, [], 0, "./simv",
                    )

                self.assertEqual(recovered["compile"]["status"], "pass")
                self.assertEqual(recovered["simulate"]["status"], "not_run")
                state.assert_called_once()
                self.assertEqual(state.call_args.args[4], "vcs_compile")
                relaunch.assert_not_called()
                if remote_state == "running":
                    reattach.assert_called_once_with(
                        "builder", 22, "/remote/stage/abcdefabcdef_1", root, 0, "vcs_compile"
                    )
                else:
                    reattach.assert_not_called()

    def test_compile_only_preserves_recovered_compile_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                return_value=["/remote/stage/abcdefabcdef_1"],
            ), patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches",
                return_value=(True, {"status": "pass"}),
            ), patch(
                "accagent.framework.semantic_simulator.remote_background_job_state",
                return_value={"state": "done", "returncode": 1, "probe": {"status": "pass"}},
            ) as state, patch(
                "accagent.framework.semantic_simulator.run_remote_background_command"
            ) as relaunch:
                recovered = recover_exact_remote_semantic_job(
                    "builder", 22, "/remote/stage", "abcdefabcdef" + "0" * 52,
                    root, root / ".spatialacc_semantic_job.json", [], 0, "./simv",
                )

            self.assertEqual(recovered["compile"]["status"], "fail")
            self.assertEqual(recovered["compile"]["returncode"], 1)
            self.assertEqual(recovered["simulate"]["status"], "not_run")
            state.assert_called_once()
            relaunch.assert_not_called()

    def test_remote_job_payload_mismatch_cannot_be_recovered(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_path = root / ".spatialacc_semantic_job.json"
            contract_path.write_text("{}\n", encoding="utf-8")
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                return_value=["/remote/stage/abcdefabcdef_1"],
            ), patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches",
                return_value=(False, {"status": "fail"}),
            ), patch(
                "accagent.framework.semantic_simulator.remote_background_job_state"
            ) as state:
                recovered = recover_exact_remote_semantic_job(
                    "builder",
                    22,
                    "/remote/stage",
                    "abcdefabcdef" + "0" * 52,
                    root,
                    contract_path,
                    [],
                    0,
                    "./simv",
                )

            self.assertIsNone(recovered)
            state.assert_not_called()

    def test_running_exact_remote_simulation_is_reattached(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_path = root / ".spatialacc_semantic_job.json"
            contract_path.write_text("{}\n", encoding="utf-8")
            compile_done = {"state": "done", "returncode": 0, "probe": {"status": "pass"}}
            simulation_running = {"state": "running", "returncode": None, "probe": {"status": "pass"}}
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                return_value=["/remote/stage/abcdefabcdef_1"],
            ), patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches",
                return_value=(True, {"identity_source": "legacy_full_payload_sha256_compatibility"}),
            ), patch(
                "accagent.framework.semantic_simulator.remote_background_job_state",
                side_effect=[compile_done, simulation_running],
            ), patch(
                "accagent.framework.semantic_simulator.wait_for_existing_remote_job",
                return_value={"status": "pass", "returncode": 0},
            ) as reattach, patch(
                "accagent.framework.semantic_simulator.run_remote_background_command"
            ) as relaunch:
                recovered = recover_exact_remote_semantic_job(
                    "builder",
                    22,
                    "/remote/stage",
                    "abcdefabcdef" + "0" * 52,
                    root,
                    contract_path,
                    [],
                    0,
                    "./simv",
                )

            self.assertEqual(recovered["simulate"]["status"], "pass")
            reattach.assert_called_once()
            relaunch.assert_not_called()

    def test_remote_recovery_retries_transport_uncertainty_at_every_probe_phase(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_path = root / ".spatialacc_semantic_job.json"
            contract_path.write_text("{}\n", encoding="utf-8")
            remote_dir = "/remote/stage/abcdefabcdef_1"
            indeterminate_identity = {
                "status": "indeterminate",
                "failure_class": "remote_transport_failure",
            }
            indeterminate_state = {
                "state": "unknown",
                "certainty": "indeterminate",
                "probe": {"status": "fail", "returncode": 255},
            }
            done = {
                "state": "done",
                "certainty": "determinate",
                "returncode": 0,
                "probe": {"status": "pass"},
            }
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                side_effect=[
                    (None, {"status": "indeterminate"}),
                    ([remote_dir], {"status": "pass"}),
                ],
            ) as discover, patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches",
                side_effect=[
                    (None, indeterminate_identity),
                    (True, {"status": "pass", "identity_source": "full_remote_job_contract"}),
                ],
            ) as identify, patch(
                "accagent.framework.semantic_simulator.remote_background_job_state",
                side_effect=[indeterminate_state, done, done],
            ) as state, patch(
                "accagent.framework.semantic_simulator.run_remote_background_command"
            ) as relaunch, patch(
                "accagent.framework.semantic_simulator.time.sleep"
            ) as retry_sleep:
                recovered = recover_exact_remote_semantic_job(
                    "builder",
                    22,
                    "/remote/stage",
                    "abcdefabcdef" + "0" * 52,
                    root,
                    contract_path,
                    [],
                    60,
                    "./simv",
                )

            self.assertEqual(recovered["recovery_state"], "recovered")
            self.assertEqual(recovered["simulate"]["status"], "pass")
            self.assertEqual(discover.call_count, 2)
            self.assertEqual(identify.call_count, 2)
            self.assertEqual(state.call_count, 3)
            self.assertEqual(retry_sleep.call_count, 3)
            relaunch.assert_not_called()

    def test_finite_indeterminate_recovery_preserves_remote_and_blocks_fresh_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            payload_dir = run_dir / "payload"
            payload_dir.mkdir()
            testbench = payload_dir / "semantic_tb.sv"
            source = payload_dir / "Harness.sv"
            input_vector = payload_dir / "input.memh"
            output = payload_dir / "rtl_output.memh"
            testbench.write_text("module semantic_tb; endmodule\n", encoding="ascii")
            source.write_text("module Harness; endmodule\n", encoding="ascii")
            input_vector.write_text("00000001\n", encoding="ascii")
            contract = {
                "testbench": str(testbench),
                "testbench_sha256": sha256_file(testbench),
                "dut_harness": {
                    "top_module": "semantic_tb",
                    "source_files": [{"path": str(source), "sha256": sha256_file(source)}],
                },
                "input_vectors": [
                    {"path": str(input_vector), "sha256": sha256_file(input_vector)}
                ],
                "rtl_output_capture": str(output),
            }
            tool = {
                "name": "vcs",
                "role": "functional_verification",
                "scope": "remote",
                "host": "builder",
                "port": 22,
                "executable": "/eda/vcs/bin/vcs",
            }
            uncertain = {
                "recovery_state": "indeterminate",
                "status": "fail",
                "failure_class": "remote_semantic_recovery_indeterminate",
                "phase": "candidate_discovery",
                "remote_job_preserved": True,
                "summary": "candidate discovery transport remained indeterminate",
            }
            with patch(
                "accagent.framework.semantic_simulator.recover_exact_remote_semantic_job",
                return_value=uncertain,
            ), patch(
                "accagent.framework.semantic_simulator.command_result"
            ) as remote_cleanup_or_setup, patch(
                "accagent.framework.semantic_simulator.run_remote_background_command"
            ) as vcs_launch, patch(
                "accagent.framework.semantic_simulator.copy_remote_file"
            ) as download:
                report = run_remote_vcs_semantic_harness(
                    run_dir,
                    "stage_generic",
                    contract,
                    tool,
                    1,
                )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(
                report["failure_class"], "remote_semantic_recovery_indeterminate"
            )
            self.assertTrue(report["remote_job_reuse"]["remote_job_preserved"])
            self.assertEqual(report["remote_stage_cleanup"]["status"], "not_run")
            self.assertEqual(report["compile"]["status"], "not_run")
            self.assertEqual(report["run"]["status"], "not_run")
            remote_cleanup_or_setup.assert_not_called()
            vcs_launch.assert_not_called()
            download.assert_not_called()

    def test_remote_runner_preserves_adaptive_stall_from_nested_simulation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            payload_dir = run_dir / "payload"
            payload_dir.mkdir()
            testbench = payload_dir / "semantic_tb.sv"
            source = payload_dir / "Harness.sv"
            input_vector = payload_dir / "input.memh"
            output = payload_dir / "rtl_output.memh"
            testbench.write_text("module semantic_tb; endmodule\n", encoding="ascii")
            source.write_text("module Harness; endmodule\n", encoding="ascii")
            input_vector.write_text("00000001\n", encoding="ascii")
            contract = {
                "testbench": str(testbench),
                "testbench_sha256": sha256_file(testbench),
                "dut_harness": {
                    "top_module": "semantic_tb",
                    "source_files": [{"path": str(source), "sha256": sha256_file(source)}],
                },
                "input_vectors": [
                    {"path": str(input_vector), "sha256": sha256_file(input_vector)}
                ],
                "rtl_output_capture": str(output),
            }
            tool = {
                "name": "vcs",
                "role": "functional_verification",
                "scope": "remote",
                "host": "builder",
                "port": 22,
                "executable": "/eda/vcs/bin/vcs",
            }
            stall_evidence = {
                "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                "status": "proven_semantic_stall",
                "stage_id": "stage_generic",
            }
            stall_termination = {
                "schema_version": "spatialaccagent.adaptive_semantic_stall_termination.v1",
                "status": "pass",
            }
            compile_result = {"status": "pass", "returncode": 0}
            simulate_result = {
                "status": "fail",
                "returncode": SEMANTIC_STALL_EXIT_CODE,
                "failure_class": "adaptive_semantic_stall",
                "adaptive_semantic_stall_evidence": stall_evidence,
                "adaptive_semantic_stall_termination": stall_termination,
            }

            def download(*args):
                destination = Path(args[3])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("", encoding="ascii")
                return {"status": "pass", "returncode": 0}

            with patch(
                "accagent.framework.semantic_simulator.recover_exact_remote_semantic_job",
                return_value=None,
            ), patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value={"status": "pass", "returncode": 0},
            ), patch(
                "accagent.framework.semantic_simulator.run_remote_background_command",
                side_effect=[compile_result, simulate_result],
            ) as launch, patch(
                "accagent.framework.semantic_simulator.copy_remote_file",
                side_effect=download,
            ), patch(
                "accagent.framework.semantic_simulator.persist_remote_artifact_receipt",
                return_value={"status": "pass"},
            ):
                report = run_remote_vcs_semantic_harness(
                    run_dir,
                    "stage_generic",
                    contract,
                    tool,
                    60,
                )

            self.assertIn("+vcs+flush+log", launch.call_args_list[1].args[2])
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["failure_class"], "adaptive_semantic_stall")
        self.assertEqual(report["returncode"], SEMANTIC_STALL_EXIT_CODE)
        self.assertEqual(report["adaptive_semantic_stall_evidence"], stall_evidence)
        self.assertEqual(
            report["adaptive_semantic_stall_termination"], stall_termination
        )
        self.assertIn("proved an adaptive semantic stall", report["summary"])

    def test_remote_upload_transport_failure_is_not_reported_as_hardware_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            payload_dir = run_dir / "payload"
            payload_dir.mkdir()
            testbench = payload_dir / "semantic_tb.sv"
            source = payload_dir / "Harness.sv"
            input_vector = payload_dir / "input.memh"
            output = payload_dir / "rtl_output.memh"
            for path, text in (
                (testbench, "module semantic_tb; endmodule\n"),
                (source, "module Harness; endmodule\n"),
                (input_vector, "00000001\n"),
            ):
                path.write_text(text, encoding="ascii")
            contract = {
                "testbench": str(testbench),
                "testbench_sha256": sha256_file(testbench),
                "dut_harness": {
                    "source_files": [
                        {"path": str(source), "sha256": sha256_file(source)}
                    ]
                },
                "input_vectors": [
                    {"path": str(input_vector), "sha256": sha256_file(input_vector)}
                ],
                "rtl_output_capture": str(output),
            }
            tool = {
                "name": "vcs",
                "role": "functional_verification",
                "scope": "remote",
                "host": "builder",
                "port": 22,
                "executable": "/eda/vcs/bin/vcs",
            }
            passed = {"status": "pass", "returncode": 0, "stdout_tail": ""}
            upload_failed = {
                "status": "fail",
                "returncode": 255,
                "stdout_tail": "",
                "stderr_tail": "scp: Connection closed",
            }
            download_failed = {
                "status": "fail",
                "returncode": 255,
                "stdout_tail": "",
                "stderr_tail": "Connection closed by builder port 22",
            }
            with patch(
                "accagent.framework.semantic_simulator.recover_exact_remote_semantic_job",
                return_value=None,
            ), patch(
                "accagent.framework.semantic_simulator.command_result",
                side_effect=[passed, passed, upload_failed],
            ), patch(
                "accagent.framework.semantic_simulator.copy_remote_file",
                return_value=download_failed,
            ), patch(
                "accagent.framework.semantic_simulator.persist_remote_artifact_receipt",
                return_value={"status": "pass"},
            ):
                report = run_remote_vcs_semantic_harness(
                    run_dir,
                    "stage_generic",
                    contract,
                    tool,
                    60,
                )

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["failure_class"], "remote_transport_failure")
        self.assertIn("transport failed", report["summary"])

    def test_finite_candidate_discovery_budget_exhaustion_is_indeterminate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract_path = root / ".spatialacc_semantic_job.json"
            contract_path.write_text("{}\n", encoding="utf-8")
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                return_value=(
                    None,
                    {
                        "status": "indeterminate",
                        "failure_class": "remote_transport_failure",
                    },
                ),
            ), patch(
                "accagent.framework.semantic_simulator.time.monotonic",
                side_effect=[0.0, 0.0, 2.0],
            ), patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches"
            ) as identify, patch(
                "accagent.framework.semantic_simulator.remote_background_job_state"
            ) as state, patch(
                "accagent.framework.semantic_simulator.run_remote_background_command"
            ) as relaunch:
                recovered = recover_exact_remote_semantic_job(
                    "builder",
                    22,
                    "/remote/stage",
                    "abcdefabcdef" + "0" * 52,
                    root,
                    contract_path,
                    [],
                    1,
                    "./simv",
                )

            self.assertEqual(recovered["recovery_state"], "indeterminate")
            self.assertEqual(recovered["phase"], "candidate_discovery")
            self.assertTrue(recovered["remote_job_preserved"])
            identify.assert_not_called()
            state.assert_not_called()
            relaunch.assert_not_called()

    def test_remote_stage_cleanup_is_generic_single_stage_and_shell_valid(self) -> None:
        root = "/tmp/model run/stage_01"
        command = remote_stage_cleanup_command(root)

        syntax = subprocess.run(
            ["bash", "-n", "-c", command],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertIn("stage_root='/tmp/model run/stage_01'", command)
        self.assertIn("/proc/[0-9]*", command)
        self.assertIn("SPATIALACC_REMOTE_STAGE_CLEANUP", command)

    def test_remote_stage_prune_is_scoped_and_preserves_current_workdir(self) -> None:
        root = "/tmp/spatialaccagent_board_vcs_run"
        current = f"{root}/{'a' * 12}_123"
        command = remote_stage_prune_command(root, current, keep_completed=2)

        syntax = subprocess.run(
            ["bash", "-n", "-c", command],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertIn(f"stage_root={root}", command)
        self.assertIn(f"keep={current}", command)
        self.assertIn("[ \"$path\" = \"$keep\" ] && continue", command)
        self.assertIn(REMOTE_ARTIFACT_RECEIPT, command)
        self.assertIn("unacknowledged_count", command)
        self.assertIn("SPATIALACC_REMOTE_STAGE_PRUNE", command)

    def test_remote_stage_prune_deletes_only_old_acknowledged_jobs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "persistent"
            root.mkdir()
            current = root / f"{'a' * 12}_1"
            newest = root / f"{'b' * 12}_2"
            second = root / f"{'c' * 12}_3"
            oldest = root / f"{'d' * 12}_4"
            unacknowledged = root / f"{'e' * 12}_5"
            failed_acknowledgment = root / f"{'f' * 12}_6"
            for path in (
                current,
                newest,
                second,
                oldest,
                unacknowledged,
                failed_acknowledgment,
            ):
                path.mkdir()
            for path in (newest, second, oldest):
                (path / REMOTE_ARTIFACT_RECEIPT).write_text(
                    '{"status": "pass"}\n', encoding="utf-8"
                )
            (failed_acknowledgment / REMOTE_ARTIFACT_RECEIPT).write_text(
                '{"status": "fail"}\n', encoding="utf-8"
            )
            for timestamp, path in enumerate(
                (
                    oldest,
                    second,
                    newest,
                    unacknowledged,
                    failed_acknowledgment,
                    current,
                ),
                start=1,
            ):
                os.utime(path, (timestamp, timestamp))

            command = remote_stage_prune_command(
                str(root), str(current), keep_completed=2
            )
            completed = subprocess.run(
                ["bash", "-c", command],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(current.is_dir())
            self.assertTrue(newest.is_dir())
            self.assertTrue(second.is_dir())
            self.assertFalse(oldest.exists())
            self.assertTrue(unacknowledged.is_dir())
            self.assertTrue(failed_acknowledgment.is_dir())
            self.assertIn("deleted=1", completed.stdout)
            self.assertIn("retained=2", completed.stdout)
            self.assertIn("unacknowledged=2", completed.stdout)

    def test_remote_artifact_root_is_persistent_and_configurable(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            root = persistent_remote_artifact_root("builder@fpga.example")
            self.assertEqual(
                root,
                "/home/builder/workspace/spatialaccagent_artifacts",
            )
            self.assertNotIn("/tmp", root)
            self.assertEqual(remote_artifact_keep_completed(), 2)
            self.assertEqual(
                persistent_remote_tool_workdir(
                    "builder@fpga.example", "vivado board", "model/run"
                ),
                "/home/builder/workspace/spatialaccagent_artifacts/"
                "vivado_board/model_run",
            )
        with patch.dict(
            os.environ,
            {
                "SPATIALACC_REMOTE_ARTIFACT_ROOT": "/data/agent evidence",
                "SPATIALACC_REMOTE_ARTIFACT_KEEP_COMPLETED": "5",
            },
            clear=True,
        ):
            self.assertEqual(
                persistent_remote_artifact_root("builder"),
                "/data/agent evidence",
            )
            self.assertEqual(remote_artifact_keep_completed(), 5)

    def test_remote_artifact_receipt_requires_local_evidence_before_ack(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            contract = run_dir / "job.json"
            evidence = run_dir / "reports" / "sim.log"
            source = run_dir / "sources" / "BoardTop.sv"
            fingerprint = "a" * 64
            remote_root = "/home/builder/workspace/spatialaccagent_artifacts/board"
            remote_dir = f"{remote_root}/{fingerprint[:12]}_1"
            source.parent.mkdir(parents=True)
            evidence.parent.mkdir(parents=True)
            source.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            evidence.write_text("real tool evidence\n", encoding="utf-8")
            contract.write_text(
                json.dumps(
                    {
                        "input_fingerprint_sha256": fingerprint,
                        "remote_workdir": remote_dir,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            upload = {
                "status": "pass",
                "returncode": 0,
                "stdout_tail": "",
                "stderr_tail": "",
            }
            with patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value=upload,
            ) as command:
                result = persist_remote_artifact_receipt(
                    host="builder@fpga.example",
                    port=22,
                    run_dir=run_dir,
                    namespace="board_vcs",
                    remote_stage_root=remote_root,
                    remote_dir=remote_dir,
                    fingerprint=fingerprint,
                    job_contract_path=contract,
                    evidence_paths=[evidence],
                    required_evidence_paths=[evidence],
                    source_identity_paths=[source],
                    snapshot_source_paths=[source],
                    timeout_sec=0,
                )

            self.assertEqual(result["status"], "pass")
            receipt = Path(result["receipt"])
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["input_fingerprint_sha256"], fingerprint)
            self.assertEqual(len(payload["evidence_files"]), 1)
            archived_evidence = Path(payload["evidence_files"][0]["path"])
            self.assertTrue(archived_evidence.is_file())
            self.assertNotEqual(archived_evidence, evidence.resolve())
            self.assertEqual(len(payload["source_snapshots"]), 1)
            self.assertTrue(Path(payload["source_snapshots"][0]["snapshot_path"]).is_file())
            self.assertTrue(command.called)
            self.assertTrue(Path(result["remote_acknowledgment"]).is_file())
            self.assertEqual(
                json.loads(
                    Path(result["remote_acknowledgment"]).read_text(
                        encoding="utf-8"
                    )
                )["status"],
                "pass",
            )
            self.assertTrue(
                command.call_args.args[0][-1].endswith(REMOTE_ARTIFACT_RECEIPT)
            )

            evidence.unlink()
            self.assertEqual(
                archived_evidence.read_text(encoding="utf-8"),
                "real tool evidence\n",
            )
            with patch(
                "accagent.framework.semantic_simulator.command_result"
            ) as command:
                failed = persist_remote_artifact_receipt(
                    host="builder@fpga.example",
                    port=22,
                    run_dir=run_dir,
                    namespace="board_vcs_missing",
                    remote_stage_root=remote_root,
                    remote_dir=remote_dir,
                    fingerprint=fingerprint,
                    job_contract_path=contract,
                    evidence_paths=[],
                    required_evidence_paths=[evidence],
                    source_identity_paths=[source],
                    timeout_sec=0,
                )
            self.assertEqual(failed["status"], "fail")
            command.assert_not_called()

    def test_v1_remote_job_contract_binds_fingerprint_derived_workdir(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            contract = run_dir / "job.json"
            evidence = run_dir / "reports" / "sim.log"
            source = run_dir / "sources" / "Harness.sv"
            fingerprint = "a" * 64
            remote_root = "/remote/semantic/stage"
            remote_dir = f"{remote_root}/{fingerprint[:12]}_123"
            evidence.parent.mkdir(parents=True)
            source.parent.mkdir(parents=True)
            evidence.write_text("real semantic evidence\n", encoding="utf-8")
            source.write_text("module Harness; endmodule\n", encoding="ascii")
            contract.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.remote_semantic_job.v1",
                        "input_fingerprint_sha256": fingerprint,
                        "payload": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            with patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value={"status": "pass", "returncode": 0},
            ):
                result = persist_remote_artifact_receipt(
                    host="builder@fpga.example",
                    port=22,
                    run_dir=run_dir,
                    namespace="semantic_vcs",
                    remote_stage_root=remote_root,
                    remote_dir=remote_dir,
                    fingerprint=fingerprint,
                    job_contract_path=contract,
                    evidence_paths=[evidence],
                    required_evidence_paths=[evidence],
                    source_identity_paths=[source],
                    timeout_sec=0,
                )

            self.assertEqual(result["status"], "pass")
            receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["job_contract_identity"]["binding_mode"],
                "fingerprint_derived_remote_workdir",
            )
            self.assertEqual(receipt["job_contract_identity"]["status"], "pass")

            with patch(
                "accagent.framework.semantic_simulator.command_result"
            ) as command:
                mismatch = persist_remote_artifact_receipt(
                    host="builder@fpga.example",
                    port=22,
                    run_dir=run_dir,
                    namespace="semantic_vcs_mismatch",
                    remote_stage_root=remote_root,
                    remote_dir=f"{remote_root}/{'b' * 12}_123",
                    fingerprint=fingerprint,
                    job_contract_path=contract,
                    evidence_paths=[evidence],
                    required_evidence_paths=[evidence],
                    source_identity_paths=[source],
                    timeout_sec=0,
                )
            self.assertEqual(mismatch["status"], "fail")
            command.assert_not_called()

    def test_failed_upload_can_retry_from_immutable_archive(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            contract = run_dir / "job.json"
            evidence = run_dir / "reports" / "sim.log"
            source = run_dir / "sources" / "BoardTop.sv"
            fingerprint = "9" * 64
            remote_root = "/home/builder/workspace/spatialaccagent_artifacts/board"
            remote_dir = f"{remote_root}/{fingerprint[:12]}_1"
            source.parent.mkdir(parents=True)
            evidence.parent.mkdir(parents=True)
            source.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            evidence.write_text("real tool evidence\n", encoding="utf-8")
            contract.write_text(
                json.dumps(
                    {
                        "input_fingerprint_sha256": fingerprint,
                        "remote_workdir": remote_dir,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value={"status": "fail", "returncode": 255},
            ):
                failed = persist_remote_artifact_receipt(
                    host="builder@fpga.example",
                    port=22,
                    run_dir=run_dir,
                    namespace="board_vcs",
                    remote_stage_root=remote_root,
                    remote_dir=remote_dir,
                    fingerprint=fingerprint,
                    job_contract_path=contract,
                    evidence_paths=[evidence],
                    required_evidence_paths=[evidence],
                    source_identity_paths=[source],
                    snapshot_source_paths=[source],
                    timeout_sec=0,
                )
            self.assertEqual(failed["status"], "fail")
            receipt_path = Path(failed["receipt"])
            evidence.unlink()
            source.unlink()

            prepared = prepare_remote_artifact_acknowledgment_retry(receipt_path)
            self.assertEqual(prepared["status"], "ready")
            acknowledgment = Path(prepared["remote_acknowledgment"])
            self.assertEqual(
                json.loads(acknowledgment.read_text(encoding="utf-8"))["status"],
                "pass",
            )
            mismatch = finalize_remote_artifact_acknowledgment_retry(
                receipt_path, "0" * 64
            )
            self.assertEqual(mismatch["status"], "fail")
            finalized = finalize_remote_artifact_acknowledgment_retry(
                receipt_path, prepared["remote_acknowledgment_sha256"]
            )
            self.assertEqual(finalized["status"], "pass")
            self.assertEqual(
                json.loads(receipt_path.read_text(encoding="utf-8"))["status"],
                "pass",
            )

    def test_retry_request_discards_completed_exact_job_before_relaunch(self) -> None:
        with TemporaryDirectory() as temp_dir:
            cwd = Path(temp_dir)
            fingerprint = "a" * 64
            remote_root = "/tmp/spatialaccagent_board_vcs_run"
            remote_dir = f"{remote_root}/{fingerprint[:12]}_123"
            runner_path = cwd / "case_board_vcs_functional.json"
            runner_path.write_text(
                json.dumps({"status": "fail", "input_fingerprint_sha256": fingerprint}),
                encoding="utf-8",
            )
            retry_path = cwd / REMOTE_JOB_RETRY_REQUEST
            retry_path.write_text(
                json.dumps(
                    {
                        "status": "ready",
                        "action": (
                            "discard_completed_remote_workdir_and_retry_same_fingerprint"
                        ),
                        "input_fingerprint_sha256": fingerprint,
                        "remote_workdir": remote_dir,
                        "runner_report_path": str(runner_path),
                    }
                ),
                encoding="utf-8",
            )
            runner_path.write_text(
                json.dumps({"status": "pending", "input_fingerprint_sha256": fingerprint}),
                encoding="utf-8",
            )
            job_contract = cwd / ".spatialacc_semantic_job.json"
            job_contract.write_text("{}\n", encoding="utf-8")
            with patch(
                "accagent.framework.semantic_simulator.remote_semantic_job_candidates",
                return_value=([remote_dir], {"status": "pass"}),
            ), patch(
                "accagent.framework.semantic_simulator.cleanup_retryable_remote_job",
                return_value={"status": "pass", "cleanup_state": "removed"},
            ) as cleanup, patch(
                "accagent.framework.semantic_simulator.remote_semantic_payload_matches"
            ) as identify:
                recovered = recover_exact_remote_semantic_job(
                    "builder",
                    22,
                    remote_root,
                    fingerprint,
                    cwd,
                    job_contract,
                    [],
                    1,
                    "./simv",
                )

            self.assertIsNone(recovered)
            self.assertFalse(retry_path.exists())
            cleanup.assert_called_once()
            identify.assert_not_called()

    def test_semantic_vcs_parallel_compile_jobs_are_explicit_and_bounded(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(semantic_vcs_compile_jobs(), 1)
            self.assertEqual(semantic_vcs_parallel_compile_args(), [])
        with patch.dict(os.environ, {"SPATIALACC_VCS_COMPILE_JOBS": "8"}, clear=True):
            self.assertEqual(semantic_vcs_compile_jobs(), 8)
            self.assertEqual(semantic_vcs_parallel_compile_args(), ["-j8"])
        with patch.dict(os.environ, {"SPATIALACC_VCS_COMPILE_JOBS": "999"}, clear=True):
            self.assertEqual(semantic_vcs_compile_jobs(), MAX_VCS_COMPILE_JOBS)
        with patch.dict(os.environ, {"SPATIALACC_VCS_COMPILE_JOBS": "invalid"}, clear=True):
            self.assertEqual(semantic_vcs_compile_jobs(), 1)

    def test_semantic_memory_initialization_is_hash_bound_and_compile_enabled(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            project_root = run_dir / "generated" / "chisel"
            payload_dir = run_dir / "payload"
            resource = project_root / "src" / "main" / "resources" / "table.memh"
            source = payload_dir / "LookupTable.sv"
            testbench = payload_dir / "semantic_tb.sv"
            input_vector = payload_dir / "input.memh"
            resource.parent.mkdir(parents=True)
            payload_dir.mkdir(parents=True)
            resource.write_text("00000001\n", encoding="ascii")
            source.write_text(
                "module LookupTable;\n"
                "  reg [31:0] Memory [0:0];\n"
                f"`ifdef {MEMORY_INIT_DEFINE}\n"
                '  initial $readmemh("src/main/resources/table.memh", Memory);\n'
                "`endif\n"
                "endmodule\n",
                encoding="ascii",
            )
            testbench.write_text("module semantic_tb; endmodule\n", encoding="ascii")
            input_vector.write_text("00000000\n", encoding="ascii")
            contract = {
                "testbench": str(testbench),
                "testbench_sha256": sha256_file(testbench),
                "dut_harness": {
                    "source_files": [{"path": str(source), "sha256": sha256_file(source)}]
                },
                "input_vectors": [
                    {"path": str(input_vector), "sha256": sha256_file(input_vector)}
                ],
            }

            defines, dependencies, errors = semantic_memory_init_payload(run_dir, [source])
            fingerprint_before, fingerprint_errors = semantic_input_fingerprint(contract, run_dir)
            with patch.dict(
                os.environ,
                {
                    "SPATIALACC_PYTHON_ENVIRONMENT_FINGERPRINT": "a" * 64,
                    "SPATIALACC_PYTHON_ENVIRONMENT_GROUP": "target_model_oracle",
                },
            ):
                environment_bound_fingerprint, environment_errors = semantic_input_fingerprint(contract, run_dir)
            resource.write_text("00000002\n", encoding="ascii")
            fingerprint_after, changed_errors = semantic_input_fingerprint(contract, run_dir)

            self.assertEqual(errors, [])
            self.assertEqual(fingerprint_errors, [])
            self.assertEqual(environment_errors, [])
            self.assertEqual(changed_errors, [])
            self.assertEqual(defines, [MEMORY_INIT_DEFINE])
            self.assertEqual(
                semantic_vcs_compile_define_args(defines),
                [f"+define+{MEMORY_INIT_DEFINE}"],
            )
            self.assertEqual(dependencies[0]["remote_relative_path"], "src/main/resources/table.memh")
            self.assertEqual(fingerprint_before, environment_bound_fingerprint)
            self.assertNotEqual(fingerprint_before, fingerprint_after)

    def test_semantic_memory_initialization_includes_xpm_parameter_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            project_root = run_dir / "generated" / "chisel"
            resource = (
                project_root
                / "src"
                / "main"
                / "resources"
                / "spatialaccagent"
                / "numeric"
                / "lookup.mem"
            )
            source = run_dir / "PhysicalRom.sv"
            resource.parent.mkdir(parents=True)
            resource.write_text("00000001\n", encoding="ascii")
            source.write_text(
                "xpm_memory_sprom #(\n"
                '  .MEMORY_INIT_FILE("src/main/resources/spatialaccagent/numeric/lookup.mem")\n'
                ") rom ();\n",
                encoding="ascii",
            )

            defines, dependencies, errors = semantic_memory_init_payload(
                run_dir,
                [source],
            )
            resource_sha256 = sha256_file(resource)

        self.assertEqual(defines, [])
        self.assertEqual(errors, [])
        self.assertEqual(len(dependencies), 1)
        self.assertEqual(
            dependencies[0]["remote_relative_path"],
            "src/main/resources/spatialaccagent/numeric/lookup.mem",
        )
        self.assertEqual(dependencies[0]["sha256"], resource_sha256)

    def test_semantic_memory_initialization_ignores_disabled_xpm_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source = run_dir / "PhysicalRam.sv"
            source.write_text(
                "xpm_memory_sdpram #(\n"
                '  .MEMORY_INIT_FILE("none"),\n'
                "  .USE_MEM_INIT(0)\n"
                ") ram ();\n",
                encoding="ascii",
            )

            defines, dependencies, errors = semantic_memory_init_payload(run_dir, [source])

        self.assertEqual(defines, [])
        self.assertEqual(dependencies, [])
        self.assertEqual(errors, [])

    def test_integer_dsp_sources_bind_xpm_closure_without_fpga_ip_tcl(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            simulation_dir = run_dir / "generated" / "chisel" / "simulation"
            simulation_dir.mkdir(parents=True)
            manifest = simulation_dir / "fpga_ip_modules.txt"
            manifest.write_text("", encoding="ascii")
            closure = {
                "status": "ready",
                "compute_backend": "integer_dsp",
                "policy": simulation_source_contract("integer_dsp"),
                "ip_generation_tcl": "",
                "ip_module_manifest": str(manifest),
                "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
                "required_ip_modules": [],
                "vcs_compile_requirements": {
                    "generated_ip_simulation_sources": "not required for integer DSP",
                    "xpm_library": "xpm",
                    "unisims_library": "unisims_ver",
                    "global_module": "glbl.v",
                },
            }
            (simulation_dir / "fpga_ip_simulation_closure.json").write_text(
                json.dumps(closure), encoding="utf-8"
            )
            source = run_dir / "GeneratedTop.sv"
            source.write_text("module Top; xpm_memory_sdpram mem(); endmodule\n", encoding="ascii")

            binding, errors = semantic_fpga_ip_static_binding(run_dir, [source])

        self.assertEqual(errors, [])
        self.assertEqual(binding["status"], "ready")
        self.assertEqual(binding["compute_backend"], "integer_dsp")
        self.assertNotIn("fpga_ip/gen_xilinx_fp_ips.tcl", binding["staged_payload"])
        self.assertEqual(binding["runtime_protocol"]["protocol_version"], "integer_dsp_xpm_source_v1")

    def test_physical_semantic_sources_bind_generated_ip_closure_into_remote_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            input_dir = run_dir / "input"
            simulation_dir = run_dir / "generated" / "chisel" / "simulation"
            scripts_dir = run_dir / "generated" / "chisel" / "scripts"
            payload_dir = run_dir / "payload"
            for path in (input_dir, simulation_dir, scripts_dir, payload_dir):
                path.mkdir(parents=True, exist_ok=True)
            generator = scripts_dir / "gen_xilinx_fp_ips_23.tcl"
            manifest = simulation_dir / "fpga_ip_modules.txt"
            generator.write_text("puts generated-ip\n", encoding="ascii")
            manifest.write_text("fp_add_sp_12\n", encoding="ascii")
            closure = {
                "status": "ready",
                "policy": {
                    "compute_models": "generated Vivado floating_point IP simulation models",
                    "memory_models": "Xilinx XPM simulation library",
                    "required_libraries": ["unisims_ver", "xpm"],
                    "required_sources": ["glbl.v", "generated_ip_simulation_sources"],
                    "same_module_names_as_implementation": True,
                    "same_interface_and_cycle_latency_as_implementation": True,
                    "behavioral_fallback_allowed": False,
                },
                "ip_generation_tcl": str(generator),
                "ip_output_dir": str(simulation_dir / "vivado_ip"),
                "ip_project_dir": str(simulation_dir / "vivado_ip_project"),
                "ip_module_manifest": str(manifest),
                "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
                "required_ip_modules": ["fp_add_sp_12"],
                "vcs_compile_requirements": {
                    "generated_ip_simulation_sources": "generated sources",
                    "xpm_library": "xpm",
                    "unisims_library": "unisims_ver",
                    "global_module": "glbl.v",
                },
            }
            (simulation_dir / "fpga_ip_simulation_closure.json").write_text(
                json.dumps(closure), encoding="utf-8"
            )
            (input_dir / "tool_profile.json").write_text(
                json.dumps(
                    {
                        "tools": [
                            {
                                "name": "vcs",
                                "role": "functional_verification",
                                "scope": "remote",
                                "host": "builder",
                                "port": 22,
                                "executable": "/eda/vcs/bin/vcs",
                            },
                            {
                                "name": "vivado",
                                "role": "synthesis_implementation_bitstream_generation",
                                "scope": "remote",
                                "host": "builder",
                                "port": 22,
                                "executable": "/eda/vivado/bin/vivado",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            source = payload_dir / "Harness.sv"
            testbench = payload_dir / "semantic_tb.sv"
            vector = payload_dir / "input.memh"
            output = payload_dir / "rtl_output.memh"
            source.write_text(
                "module Harness; fp_add_sp_12 ip(); endmodule\n",
                encoding="ascii",
            )
            testbench.write_text(
                "module semantic_stage_physical_tb; endmodule\n",
                encoding="ascii",
            )
            vector.write_text("00000000\n", encoding="ascii")
            contract = {
                "testbench": str(testbench),
                "testbench_sha256": sha256_file(testbench),
                "dut_harness": {"source_files": [{"path": str(source), "sha256": sha256_file(source)}]},
                "input_vectors": [{"path": str(vector), "sha256": sha256_file(vector)}],
                "rtl_output_capture": str(output),
            }
            tool = {
                "name": "vcs",
                "role": "functional_verification",
                "scope": "remote",
                "host": "builder",
                "port": 22,
                "executable": "/eda/vcs/bin/vcs",
            }
            binding, errors = semantic_fpga_ip_static_binding(run_dir, [source])
            self.assertEqual(errors, [])
            self.assertEqual(binding["status"], "ready")

            def download(*args):
                destination = Path(args[3])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text("00000001\n", encoding="ascii")
                return {"status": "pass", "returncode": 0}

            passed = {"status": "pass", "returncode": 0, "stdout_tail": "", "stderr_tail": ""}
            with patch(
                "accagent.framework.semantic_simulator.recover_exact_remote_semantic_job",
                return_value=None,
            ), patch(
                "accagent.framework.semantic_simulator.command_result",
                return_value=passed,
            ), patch(
                "accagent.framework.semantic_simulator.run_remote_background_command",
                return_value=passed,
            ) as launch, patch(
                "accagent.framework.semantic_simulator.copy_remote_file",
                side_effect=download,
            ), patch(
                "accagent.framework.semantic_simulator.persist_remote_artifact_receipt",
                return_value={"status": "pass"},
            ):
                report = run_remote_vcs_semantic_harness(
                    run_dir,
                    "stage_physical",
                    contract,
                    tool,
                    60,
                )

        self.assertEqual(report["status"], "pass")
        compile_command = launch.call_args_list[0].args[2]
        self.assertIn("gen_xilinx_fp_ips.tcl", compile_command)
        self.assertIn("export_vcs_file_info.tcl", compile_command)
        self.assertIn("bash fpga_ip/compile_ip_models.sh", compile_command)
        self.assertIn("source fpga_ip/vcs_runtime.env", compile_command)
        self.assertIn("mapfile -t fpga_ip_elab_args", compile_command)
        self.assertIn('\"${fpga_ip_elab_args[@]}\" -o simv', compile_command)
        self.assertEqual(report["fpga_ip_simulation_binding"]["binding"]["status"], "ready")

    def test_missing_semantic_memory_initialization_dependency_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source = run_dir / "LookupTable.sv"
            source.write_text(
                f"`ifdef {MEMORY_INIT_DEFINE}\n"
                'initial $readmemh("src/main/resources/missing.memh", Memory);\n'
                "`endif\n",
                encoding="ascii",
            )

            defines, dependencies, errors = semantic_memory_init_payload(run_dir, [source])

            self.assertEqual(defines, [MEMORY_INIT_DEFINE])
            self.assertEqual(dependencies, [])
            self.assertIn("dependency is missing", " ".join(errors))

    def test_standard_internal_trace_marks_valid_unknown_boundary_as_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            sim_log.write_text(
                "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=producer_out "
                "module=Producer cycle=41 beat=6 valid=1 ready=1 data=0011\n"
                "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=consumer_out "
                "module=Consumer cycle=42 beat=7 valid=1 ready=1 data=xx11\n",
                encoding="utf-8",
            )

            records = internal_trace_records(sim_log, "stage_generic")

            self.assertEqual([record["status"] for record in records], ["diagnostic_seed", "fail"])
            self.assertEqual(records[1]["module"], "Consumer")
            self.assertEqual(records[1]["beat_index"], 7)
            self.assertEqual(
                records[1]["boundary_id"],
                "boundary.internal_stage_generic_consumer_out",
            )
            self.assertEqual(records[1]["observed_value"]["packed_literal"], "xx11")

    def test_scalar_internal_probe_has_no_ready_valid_semantics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            sim_log.write_text(
                "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=state "
                "module=Producer probe_kind=scalar cycle=42 scalar_value=0\n"
                "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=inactive_fp_ready "
                "module=Producer probe_kind=scalar cycle=0 scalar_value=x\n",
                encoding="utf-8",
            )

            records = internal_trace_records(sim_log, "stage_generic")
            case_records = case_internal_trace_records(sim_log, "stage_generic")

        for parsed in (records, case_records):
            self.assertEqual(len(parsed), 2)
            self.assertEqual(parsed[0]["evidence_type"], "semantic_internal_scalar_probe")
            self.assertEqual(parsed[0]["probe_kind"], "scalar")
            self.assertNotIn("valid", parsed[0]["observed_value"])
            self.assertNotIn("ready", parsed[0]["observed_value"])
            self.assertEqual(parsed[0]["status"], "diagnostic_seed")
            self.assertEqual(parsed[1]["status"], "diagnostic_seed")
            self.assertIsNone(parsed[1]["failure_class"])
            self.assertIsNone(parsed[1]["violated_contract"])
            self.assertEqual(parsed[1]["observed_value"]["scalar_value"], "x")

    def test_internal_trace_reads_vcs_stderr_and_deduplicates_tail_fallback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            stderr_log = Path(temp_dir) / "sim.stderr.log"
            trace = (
                "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=producer_out "
                "module=Producer cycle=              42 beat=  7 valid=1 ready=1 data=xx11\n"
            )
            sim_log.write_text("PASS semantic harness\n", encoding="utf-8")
            stderr_log.write_text(trace, encoding="utf-8")

            records = internal_trace_records(
                sim_log,
                "stage_generic",
                supplemental_paths=[stderr_log],
                supplemental_texts=[("run.stderr_tail", trace)],
            )

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["source"], str(stderr_log))
            self.assertEqual(records[0]["failure_class"], "unknown_logic_value")
            self.assertEqual(records[0]["cycle"], 42)
            self.assertEqual(records[0]["beat_index"], 7)

    def test_case_internal_trace_preserves_late_boundary_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            rows = [
                f"SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=weight "
                f"module=Harness cycle=0 beat={beat} valid=1 ready=1 data={beat:08x}"
                for beat in range(300)
            ]
            rows.extend(
                [
                    "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=input_snapshot "
                    "module=Harness cycle=0 beat=0 valid=1 ready=0 data=00000001",
                    "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=input_snapshot "
                    "module=Harness cycle=4096 beat=0 valid=1 ready=0 data=00000001",
                    "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=producer_out "
                    "module=Producer cycle=4097 beat=0 valid=1 ready=1 data=xx11",
                    "SPATIALACC_INTERNAL_TRACE stage=stage_generic boundary=input_snapshot "
                    "module=Harness cycle=0 beat=1 valid=1 ready=1 data=00000002",
                ]
            )
            sim_log.write_text("\n".join(rows) + "\n", encoding="utf-8")

            records = case_internal_trace_records(sim_log, "stage_generic", limit=12)

        self.assertLessEqual(len(records), 12)
        self.assertTrue(any(row["cycle"] == 4096 for row in records))
        self.assertTrue(any(
            row["boundary_id"] == "boundary.internal_stage_generic_producer_out"
            and row["status"] == "fail"
            for row in records
        ))
        self.assertTrue(any(
            row["boundary_id"] == "boundary.internal_stage_generic_input_snapshot"
            and row["beat_index"] == 1
            for row in records
        ))

    def test_cctg_passes_internal_observations_without_declaring_failure(self) -> None:
        observations = [
            {
                "status": "diagnostic_seed",
                "evidence_type": "semantic_internal_boundary_trace",
                "stage_id": "stage_generic",
                "boundary_id": "boundary.internal_stage_generic_input_snapshot",
                "module": "Harness",
                "cycle": cycle,
                "observed_value": {"valid": 1, "ready": 0},
                "source": "/run/sim.log",
            }
            for cycle in (0, 4096)
        ]
        output_failure = {
            "status": "fail",
            "evidence_type": "semantic_output_shape",
            "stage_id": "stage_generic",
            "module": "Harness",
            "contract": "semantic_output",
        }

        localized = localize_failure(
            {"boundaries": []},
            {"status": "fail", "results": []},
            [*observations, output_failure],
        )

        self.assertEqual(localized["violated_contract"], "semantic_output")
        self.assertEqual(localized["failure_record_count"], 1)
        self.assertEqual(
            [row["cycle"] for row in localized["minimal_repair_context"]["diagnostic_observations"]],
            [0, 4096],
        )

    def test_cctg_prefers_earliest_internal_failure_within_earlier_stage(self) -> None:
        contracts = {
            "boundaries": [
                {
                    "boundary_id": "boundary.stage01_to_stage02",
                    "src_stage": "stage_01",
                    "dst_stage": "stage_02",
                },
                {
                    "boundary_id": "boundary.stage06_to_stage07",
                    "src_stage": "stage_06",
                    "dst_stage": "stage_07",
                },
            ]
        }
        traces = [
            {
                "status": "fail",
                "evidence_type": "semantic_internal_boundary_trace",
                "failure_class": "unknown_logic_value",
                "stage_id": "stage_06",
                "module": "LaterStageModule",
                "cycle": 1,
            },
            {
                "status": "fail",
                "evidence_type": "semantic_internal_boundary_trace",
                "failure_class": "unknown_logic_value",
                "stage_id": "stage_01",
                "module": "QKVProjection",
                "cycle": 100,
                "violated_contract": "internal_submodule_known_value_when_valid",
            },
            {
                "status": "fail",
                "evidence_type": "semantic_internal_boundary_trace",
                "failure_class": "unknown_logic_value",
                "stage_id": "stage_01",
                "module": "AttentionGQA",
                "boundary_id": "boundary.stage01_to_stage02",
                "cycle": 200,
            },
            {
                "status": "fail",
                "evidence_type": "semantic_numeric_compare",
                "failure_class": "unknown_logic_value",
                "stage_id": "stage_01",
                "module": "Stage01Harness",
            },
        ]

        localized = localize_failure(contracts, {"status": "fail", "results": []}, traces)

        self.assertEqual(localized["root_candidate_module"], "QKVProjection")
        self.assertEqual(
            localized["minimal_repair_context"]["trace_record"]["evidence_type"],
            "semantic_internal_boundary_trace",
        )
        self.assertEqual(
            localized["violated_contract"],
            "internal_submodule_known_value_when_valid",
        )

    def test_cctg_deduplicates_same_internal_trace_from_functional_and_golden(self) -> None:
        with TemporaryDirectory() as temp_dir:
            trace = {
                "status": "fail",
                "evidence_type": "semantic_internal_boundary_trace",
                "stage_id": "stage_generic",
                "boundary_id": "boundary.internal",
                "module": "Producer",
                "cycle": 42,
                "beat_index": 7,
                "observed_value": {"valid": 1, "ready": 1, "packed_literal": "xx11"},
            }
            paths = []
            for name in ("functional.json", "golden.json"):
                path = Path(temp_dir) / name
                path.write_text(json.dumps({"boundary_trace": [trace]}), encoding="utf-8")
                paths.append(path)

            records = load_trace_records(paths)

            self.assertEqual(len(records), 1)

    def canonical_fixture(self, run_dir: Path) -> tuple[dict, Path, Path]:
        input_dir = run_dir / "input"
        payload_dir = run_dir / "payload"
        report_dir = run_dir / "verification" / "operator_leaf_functional"
        for path in (input_dir, payload_dir, report_dir):
            path.mkdir(parents=True, exist_ok=True)
        (input_dir / "tool_profile.json").write_text(
            json.dumps(
                {
                    "tools": [
                        {
                            "name": "vcs",
                            "role": "functional_verification",
                            "scope": "remote",
                            "host": "builder@example",
                            "port": 22,
                            "executable": "/eda/vcs/bin/vcs",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        testbench = payload_dir / "semantic_tb.sv"
        source = payload_dir / "Harness.sv"
        input_vector = payload_dir / "input.memh"
        weight = payload_dir / "weight.memh"
        output = payload_dir / "output.memh"
        vcs_log = payload_dir / "vcs.log"
        sim_log = payload_dir / "sim.log"
        for path, content in (
            (testbench, "module semantic_tb; endmodule\n"),
            (source, "module Harness; endmodule\n"),
            (input_vector, "00000001\n"),
            (weight, "00000002\n"),
            (output, "00000003\n"),
            (vcs_log, "compile pass\n"),
            (sim_log, "simulation pass\n"),
        ):
            path.write_text(content, encoding="ascii")
        contract = {
            "testbench": str(testbench),
            "testbench_sha256": sha256_file(testbench),
            "dut_harness": {
                "source_files": [{"path": str(source), "sha256": sha256_file(source)}]
            },
            "input_vectors": [{"path": str(input_vector), "sha256": sha256_file(input_vector)}],
            "real_weight_stream": {"path": str(weight), "sha256": sha256_file(weight)},
            "rtl_output_capture": str(output),
        }
        fingerprint, errors = semantic_input_fingerprint(contract, run_dir)
        self.assertEqual(errors, [])
        report_path = report_dir / "stage_generic.json"
        report_path.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "mode": "functional",
                    "stage_id": "stage_generic",
                    "canonical_run_id": "canonical-test-run",
                    "module_results": [
                        {
                            "schema_version": "spatialaccagent.semantic_simulator_execution.v1",
                            "status": "pass",
                            "stage_id": "stage_generic",
                            "input_fingerprint_sha256": fingerprint,
                            "output_capture": str(output),
                            "rtl_output_sha256": sha256_file(output),
                            "vcs_log": str(vcs_log),
                            "sim_log": str(sim_log),
                            "tool_profile": {
                                "name": "vcs",
                                "role": "functional_verification",
                                "scope": "remote",
                                "host": "builder@example",
                                "port": 22,
                                "executable": "/eda/vcs/bin/vcs",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return contract, report_path, input_vector

    def test_configured_vcs_comes_from_current_run_tool_profile(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            input_dir = run_dir / "input"
            input_dir.mkdir()
            (input_dir / "tool_profile.json").write_text(
                json.dumps(
                    {
                        "tools": [
                            {
                                "name": "vcs",
                                "role": "functional_verification",
                                "scope": "remote",
                                "host": "builder@example",
                                "port": 2222,
                                "executable": "/eda/vcs/bin/vcs",
                            },
                            {
                                "name": "verilator",
                                "role": "functional_verification_alternative_unconfigured",
                                "scope": None,
                                "host": None,
                                "executable": None,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            tool, errors = configured_vcs(run_dir)

            self.assertEqual(errors, [])
            self.assertEqual(tool["host"], "builder@example")
            self.assertEqual(tool["port"], 2222)
            self.assertEqual(tool["executable"], "/eda/vcs/bin/vcs")

    def test_configured_vcs_normalizes_role_separators(self) -> None:
        for role in (
            "Functional Verification",
            "functional-verification",
            "functional_verification_compile_and_run_systemverilog_testbenches",
        ):
            with self.subTest(role=role), TemporaryDirectory() as temp_dir:
                run_dir = Path(temp_dir)
                input_dir = run_dir / "input"
                input_dir.mkdir()
                (input_dir / "tool_profile.json").write_text(
                    json.dumps(
                        {
                            "tools": [
                                {
                                    "name": "vcs",
                                    "role": role,
                                    "scope": "remote",
                                    "host": "builder@example",
                                    "port": 22,
                                    "executable": "/eda/vcs/bin/vcs",
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

                tool, errors = configured_vcs(run_dir)

                self.assertEqual(errors, [])
                self.assertEqual(tool["role"], role)

    def test_configured_vcs_excludes_declared_alternatives(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            input_dir = run_dir / "input"
            input_dir.mkdir()
            (input_dir / "tool_profile.json").write_text(
                json.dumps(
                    {
                        "tools": [
                            {
                                "name": "vcs",
                                "role": "functional_verification_alternative_unconfigured",
                                "scope": "remote",
                                "host": "builder@example",
                                "port": 22,
                                "executable": "/eda/vcs/bin/vcs",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            tool, errors = configured_vcs(run_dir)

        self.assertEqual(tool, {})
        self.assertIn("exactly one functional VCS", " ".join(errors))

    def test_missing_production_vcs_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            input_dir = run_dir / "input"
            input_dir.mkdir()
            (input_dir / "tool_profile.json").write_text(
                json.dumps({"tools": [{"name": "verilator", "role": "alternative"}]}),
                encoding="utf-8",
            )

            tool, errors = configured_vcs(run_dir)

            self.assertEqual(tool, {})
            self.assertIn("exactly one functional VCS", " ".join(errors))

    def test_golden_can_reuse_exact_hash_bound_functional_execution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            contract, report_path, _ = self.canonical_fixture(run_dir)

            execution, errors = reusable_semantic_execution(
                run_dir,
                "stage_generic",
                contract,
                report_path,
            )

            self.assertEqual(errors, [])
            self.assertEqual(execution["canonical_reuse"]["canonical_run_id"], "canonical-test-run")
            self.assertTrue(execution["canonical_reuse"]["real_tool_was_not_relaunched"])

    def test_golden_can_reuse_exact_execution_from_prior_failed_golden_compare(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            contract, report_path, _ = self.canonical_fixture(run_dir)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["status"] = "fail"
            report["mode"] = "golden"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            execution, errors = reusable_semantic_execution(
                run_dir,
                "stage_generic",
                contract,
                report_path,
            )

            self.assertEqual(errors, [])
            self.assertEqual(execution["canonical_reuse"]["source"], "same-contract golden real-tool execution")
            self.assertEqual(execution["canonical_reuse"]["source_report_status"], "fail")
            self.assertTrue(execution["canonical_reuse"]["real_tool_was_not_relaunched"])

    def test_golden_prefers_prior_same_contract_golden_execution_before_functional(self) -> None:
        stage = {"stage_id": "stage_generic", "op": "linear", "kind": "operator"}
        execution = {
            "status": "pass",
            "stage_id": "stage_generic",
            "canonical_reuse": {"canonical_run_id": "prior-golden-run"},
            "rtl_output_sha256": "a" * 64,
        }
        manifest = {
            "status": "ready",
            "real_weight_source": {"source_checkpoint_sha256": "b" * 64},
            "random_input": {"seed": 1},
            "numeric_comparison_policy": {},
        }
        contract = {
            "status": "ready",
            "path": "/tmp/contract.json",
            "rtl_output_capture": "/tmp/output.memh",
            "expected_output": {"sha256": "c" * 64},
            "dut_harness": {"top_module": "Harness", "consumed_tensor_hashes": []},
        }
        with patch(
            "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
            return_value=(manifest, contract),
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.reusable_semantic_execution",
            return_value=(execution, []),
        ) as reusable, patch(
            "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness"
        ) as simulator, patch(
            "scripts.verification.qwen_leaf_operator_verify.numeric_compare",
            return_value={"passed": True},
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.semantic_output_evidence",
            return_value={"status": "pass", "blockers": []},
        ):
            report = semantic_stage_report(Path("/tmp/run"), stage, "golden", 60, "new-run")

        simulator.assert_not_called()
        self.assertEqual(reusable.call_count, 1)
        self.assertIn("operator_leaf_golden", str(reusable.call_args.args[3]))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["canonical_run_id"], "prior-golden-run")
        self.assertEqual(report["execution_source"], "canonical_previous_semantic_real_tool_run")

    def test_golden_relaunches_when_functional_input_hash_is_stale(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            contract, report_path, input_vector = self.canonical_fixture(run_dir)
            input_vector.write_text("00000004\n", encoding="ascii")

            execution, errors = reusable_semantic_execution(
                run_dir,
                "stage_generic",
                contract,
                report_path,
            )

            self.assertIsNone(execution)
            self.assertIn("hash mismatch", " ".join(errors))

    def test_semantic_simulator_uses_outer_tool_budget_without_fixed_five_minute_cap(self) -> None:
        with patch.dict(os.environ, {"SPATIALACC_TOOL_TIMEOUT_SEC": "7200"}):
            os.environ.pop("SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC", None)
            self.assertEqual(semantic_sim_timeout_sec(), 7200)
        with patch.dict(
            os.environ,
            {
                "SPATIALACC_TOOL_TIMEOUT_SEC": "7200",
                "SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC": "3600",
            },
        ):
            self.assertEqual(semantic_sim_timeout_sec(), 3600)

        with patch.dict(
            os.environ,
            {
                "SPATIALACC_TOOL_TIMEOUT_SEC": "0",
                "SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC": "0",
            },
        ):
            self.assertEqual(semantic_sim_timeout_sec(), 0)

    def test_debug_loop_propagates_and_restores_stage7_tool_budget(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPATIALACC_TOOL_TIMEOUT_SEC": "111",
                "SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC": "222",
            },
        ):
            with stage6_scope_env("operator_leaf_closure", 7200):
                self.assertEqual(os.environ["SPATIALACC_TOOL_TIMEOUT_SEC"], "7200")
                self.assertEqual(os.environ["SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC"], "7200")
            self.assertEqual(os.environ["SPATIALACC_TOOL_TIMEOUT_SEC"], "111")
            self.assertEqual(os.environ["SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC"], "222")

    def test_debug_loop_explicit_zero_overrides_stale_finite_tool_budget(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPATIALACC_TOOL_TIMEOUT_SEC": "7200",
                "SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC": "7200",
            },
        ):
            with stage6_scope_env("single_layer_closure", 0):
                self.assertEqual(os.environ["SPATIALACC_TOOL_TIMEOUT_SEC"], "0")
                self.assertEqual(os.environ["SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC"], "0")
            self.assertEqual(os.environ["SPATIALACC_TOOL_TIMEOUT_SEC"], "7200")
            self.assertEqual(os.environ["SPATIALACC_SEMANTIC_SIM_TIMEOUT_SEC"], "7200")

    def test_semantic_stage_parallelism_is_explicit_and_bounded(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(semantic_stage_max_workers(9), 1)
        with patch.dict(os.environ, {"SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS": "3"}):
            self.assertEqual(semantic_stage_max_workers(9), 3)
            self.assertEqual(semantic_stage_max_workers(2), 2)

    def test_semantic_stage_rejects_zero_exit_fatal_and_wrong_output_shape(self) -> None:
        stage = {"stage_id": "stage_generic", "op": "linear", "kind": "operator"}
        manifest = {"status": "ready", "real_weight_source": {}, "random_input": {}}
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "rtl_output.memh"
            sim_log = root / "sim.log"
            sim_stderr = root / "sim.stderr.log"
            output.write_text("00000000\n00000001\n", encoding="ascii")
            sim_log.write_text('Fatal: "semantic_tb.sv", 71: output shape mismatch\n', encoding="utf-8")
            sim_stderr.write_text("", encoding="utf-8")
            contract = {
                "status": "ready",
                "path": str(root / "contract.json"),
                "rtl_output_capture": str(output),
                "expected_output": {"beats": 2},
                "dut_harness": {"top_module": "Harness", "consumed_tensor_hashes": []},
            }
            execution = {
                "status": "pass",
                "stage_id": "stage_generic",
                "sim_log": str(sim_log),
                "sim_stderr_log": str(sim_stderr),
                "output_capture": str(output),
                "run": {"status": "pass", "returncode": 0, "stdout_tail": "", "stderr_tail": ""},
            }
            with patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
                return_value=(manifest, contract),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness",
                return_value=execution,
            ):
                fatal_report = semantic_stage_report(
                    root, stage, "functional", 60, "fatal-zero-exit"
                )

            self.assertEqual(fatal_report["status"], "fail")
            self.assertEqual(fatal_report["output_evidence"]["actual_beats"], 2)
            self.assertTrue(fatal_report["output_evidence"]["fatal_lines"])
            self.assertIn("semantic simulator reported a fatal assertion", " ".join(fatal_report["blockers"]))

            sim_log.write_text("", encoding="utf-8")
            output.write_text("00000000\n", encoding="ascii")
            with patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
                return_value=(manifest, contract),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness",
                return_value=execution,
            ):
                shape_report = semantic_stage_report(
                    root, stage, "functional", 60, "wrong-output-shape"
                )
            self.assertEqual(shape_report["status"], "fail")
            self.assertEqual(shape_report["output_evidence"]["actual_beats"], 1)
            self.assertIn("expected 2, observed 1", " ".join(shape_report["blockers"]))

            output.write_text("00000000\n00000001\n", encoding="ascii")
            with patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
                return_value=(manifest, contract),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness",
                return_value=execution,
            ):
                pass_report = semantic_stage_report(
                    root, stage, "functional", 60, "complete-output"
                )
            self.assertEqual(pass_report["status"], "pass")
            self.assertEqual(pass_report["output_evidence"]["actual_beats"], 2)

            output.write_text("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n" * 2, encoding="ascii")
            with patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
                return_value=(manifest, contract),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness",
                return_value=execution,
            ):
                unknown_report = semantic_stage_report(
                    root, stage, "functional", 60, "unknown-output"
                )
            self.assertEqual(unknown_report["status"], "fail")
            self.assertEqual(unknown_report["output_evidence"]["unknown_word_count"], 2)
            self.assertIn("unknown/high-impedance", " ".join(unknown_report["blockers"]))
            self.assertEqual(
                unknown_report["debug_closure"]["failure_slice"][-1]["failure_class"],
                "unknown_logic_value",
            )

    def test_functional_stage_reuse_requires_exact_canonical_execution(self) -> None:
        stage = {"stage_id": "stage_generic", "op": "linear", "kind": "operator"}
        execution = {
            "status": "pass",
            "stage_id": "stage_generic",
            "canonical_reuse": {"canonical_run_id": "canonical-test-run"},
            "rtl_output_sha256": "a" * 64,
        }
        manifest = {
            "status": "ready",
            "real_weight_source": {"source_checkpoint_sha256": "b" * 64},
            "random_input": {"seed": 1},
        }
        contract = {
            "status": "ready",
            "path": "/tmp/contract.json",
            "dut_harness": {"top_module": "Harness", "consumed_tensor_hashes": []},
        }
        with patch.dict(os.environ, {"SPATIALACC_REUSE_SEMANTIC_STAGE_RESULTS": "1"}):
            with patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
                return_value=(manifest, contract),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.reusable_semantic_execution",
                return_value=(execution, []),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness"
            ) as simulator, patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_output_evidence",
                return_value={"status": "pass", "blockers": []},
            ):
                report = semantic_stage_report(Path("/tmp/run"), stage, "functional", 60, "new-run")

        simulator.assert_not_called()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["canonical_run_id"], "canonical-test-run")
        self.assertEqual(report["execution_source"], "canonical_previous_semantic_real_tool_run")

    def test_functional_stage_reuse_falls_back_to_exact_prior_golden_execution(self) -> None:
        stage = {"stage_id": "stage_generic", "op": "linear", "kind": "operator"}
        execution = {
            "status": "pass",
            "stage_id": "stage_generic",
            "canonical_reuse": {"canonical_run_id": "prior-golden-run"},
            "rtl_output_sha256": "a" * 64,
        }
        manifest = {
            "status": "ready",
            "real_weight_source": {"source_checkpoint_sha256": "b" * 64},
            "random_input": {"seed": 1},
        }
        contract = {
            "status": "ready",
            "path": "/tmp/contract.json",
            "dut_harness": {"top_module": "Harness", "consumed_tensor_hashes": []},
        }
        with patch.dict(os.environ, {"SPATIALACC_REUSE_SEMANTIC_STAGE_RESULTS": "1"}), patch(
            "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
            return_value=(manifest, contract),
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.reusable_semantic_execution",
            side_effect=[(None, ["functional fingerprint is stale"]), (execution, [])],
        ) as reusable, patch(
            "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness"
        ) as simulator, patch(
            "scripts.verification.qwen_leaf_operator_verify.semantic_output_evidence",
            return_value={"status": "pass", "blockers": []},
        ):
            report = semantic_stage_report(Path("/tmp/run"), stage, "functional", 60, "new-run")

        simulator.assert_not_called()
        self.assertEqual(reusable.call_count, 2)
        self.assertIn("operator_leaf_functional", str(reusable.call_args_list[0].args[3]))
        self.assertIn("operator_leaf_golden", str(reusable.call_args_list[1].args[3]))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["canonical_run_id"], "prior-golden-run")
        self.assertEqual(report["execution_source"], "canonical_previous_semantic_real_tool_run")

    def test_functional_stage_reuse_mismatch_relaunches_real_simulator(self) -> None:
        stage = {"stage_id": "stage_generic", "op": "linear", "kind": "operator"}
        manifest = {"status": "ready", "real_weight_source": {}, "random_input": {}}
        contract = {
            "status": "ready",
            "path": "/tmp/contract.json",
            "dut_harness": {"top_module": "Harness", "consumed_tensor_hashes": []},
        }
        fresh_execution = {
            "status": "pass",
            "stage_id": "stage_generic",
            "rtl_output_sha256": "c" * 64,
        }
        with patch.dict(os.environ, {"SPATIALACC_REUSE_SEMANTIC_STAGE_RESULTS": "1"}):
            with patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
                return_value=(manifest, contract),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.reusable_semantic_execution",
                return_value=(None, ["canonical functional execution input fingerprint is stale"]),
            ), patch(
                "scripts.verification.qwen_leaf_operator_verify.run_semantic_harness",
                return_value=fresh_execution,
            ) as simulator, patch(
                "scripts.verification.qwen_leaf_operator_verify.semantic_output_evidence",
                return_value={"status": "pass", "blockers": []},
            ):
                report = semantic_stage_report(Path("/tmp/run"), stage, "functional", 60, "new-run")

        simulator.assert_called_once()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["canonical_run_id"], "new-run")
        self.assertEqual(report["execution_source"], "fresh_real_tool_run")
        self.assertIn("fingerprint is stale", " ".join(report["canonical_reuse_errors"]))

    def test_parallel_stage_execution_preserves_plan_order_and_reports(self) -> None:
        stages = [
            {"stage_id": "stage_02"},
            {"stage_id": "stage_00"},
            {"stage_id": "stage_01"},
        ]

        def fake_stage_report(_run_dir, stage, mode, _timeout, _invocation):
            return {
                "stage_id": stage["stage_id"],
                "mode": mode,
                "status": "pass",
                "blockers": [],
            }

        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS": "3"},
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.stage_report",
            side_effect=fake_stage_report,
        ):
            root = Path(temp_dir)
            reports = execute_stage_reports(root, stages, "functional", 60, "run", root / "reports")

            self.assertEqual([row["stage_id"] for row in reports], ["stage_02", "stage_00", "stage_01"])
            self.assertTrue((root / "reports" / "stage_00.json").is_file())

    def test_sequential_leaf_execution_stops_at_first_failure(self) -> None:
        stages = [{"stage_id": "stage_00"}, {"stage_id": "stage_01"}]

        def fake_stage_report(_run_dir, stage, mode, _timeout, _invocation):
            return {
                "stage_id": stage["stage_id"],
                "mode": mode,
                "status": "fail" if stage["stage_id"] == "stage_00" else "pass",
                "blockers": ["real leaf failure"] if stage["stage_id"] == "stage_00" else [],
            }

        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS": "1"},
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.stage_report",
            side_effect=fake_stage_report,
        ) as stage_runner:
            root = Path(temp_dir)
            reports = execute_stage_reports(root, stages, "functional", 60, "run", root / "reports")
            aggregate = aggregate_report(
                root,
                reports,
                "functional",
                [stage["stage_id"] for stage in stages],
            )
            self.assertEqual(stage_runner.call_count, 1)
            self.assertEqual([row["stage_id"] for row in reports], ["stage_00"])
            self.assertTrue((root / "reports" / "stage_00.json").is_file())
            self.assertFalse((root / "reports" / "stage_01.json").exists())
            self.assertEqual(aggregate["status"], "fail")
            self.assertEqual(aggregate["completed_stage_ids"], ["stage_00"])
            self.assertEqual(aggregate["not_run_stage_ids"], ["stage_01"])
            self.assertTrue(aggregate["stopped_after_failure"])

    def test_case_adapter_sequential_leaf_execution_stops_at_first_failure(self) -> None:
        stages = [{"stage_id": "stage_00"}, {"stage_id": "stage_01"}]

        def fake_stage_report(_run_dir, stage, mode, _timeout, _invocation):
            return {
                "stage_id": stage["stage_id"],
                "mode": mode,
                "status": "fail" if stage["stage_id"] == "stage_00" else "pass",
                "blockers": ["real leaf failure"] if stage["stage_id"] == "stage_00" else [],
            }

        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS": "1"},
        ), patch(
            "scripts.verification.case_leaf_operator_verify.stage_report",
            side_effect=fake_stage_report,
        ) as stage_runner:
            root = Path(temp_dir)
            reports = execute_case_stage_reports(
                root,
                stages,
                "functional",
                60,
                "run",
                root / "reports",
            )
            self.assertEqual(stage_runner.call_count, 1)
            self.assertEqual([row["stage_id"] for row in reports], ["stage_00"])
            self.assertTrue((root / "reports" / "stage_00.json").is_file())
            self.assertFalse((root / "reports" / "stage_01.json").exists())

    def test_leaf_execution_updates_live_state_with_current_layer_one_stage(self) -> None:
        stages = [{"stage_id": "stage_04"}]

        def fake_stage_report(_run_dir, stage, mode, _timeout, _invocation):
            return {
                "stage_id": stage["stage_id"],
                "mode": mode,
                "status": "pass",
                "blockers": [],
            }

        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS": "1"},
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.stage_report",
            side_effect=fake_stage_report,
        ):
            root = Path(temp_dir)
            binding = "operator-leaf:test"
            activate_live_state_slot(root, "execution", {}, binding=binding)

            execute_stage_reports(
                root,
                stages,
                "functional",
                60,
                "run",
                root / "reports",
                live_binding=binding,
            )

            execution = read_live_state(root)["execution"]["data"]

        self.assertEqual(execution["verification_layer"], "layer1_operator_leaf")
        self.assertEqual(execution["verification_scope"], "operator_leaf_closure")
        self.assertEqual(execution["current_stage_id"], "stage_04")
        self.assertEqual(execution["last_completed_stage_status"], "pass")

    def test_parallel_stage_exception_writes_current_structured_failure(self) -> None:
        stages = [{"stage_id": "stage_good"}, {"stage_id": "stage_bad"}]

        def fake_stage_report(_run_dir, stage, mode, _timeout, _invocation):
            if stage["stage_id"] == "stage_bad":
                raise ValueError("invalid capture")
            return {"stage_id": stage["stage_id"], "mode": mode, "status": "pass", "blockers": []}

        with TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"SPATIALACC_SEMANTIC_STAGE_MAX_WORKERS": "2"},
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.stage_report",
            side_effect=fake_stage_report,
        ):
            root = Path(temp_dir)
            reports = execute_stage_reports(root, stages, "golden", 60, "run", root / "reports")

            self.assertEqual([row["status"] for row in reports], ["pass", "fail"])
            failed = json.loads((root / "reports" / "stage_bad.json").read_text(encoding="utf-8"))
            self.assertIn("ValueError", failed["blockers"][0])

    def test_numeric_compare_reports_verilog_unknowns_as_hard_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            actual = root / "actual.memh"
            expected = root / "expected.memh"
            actual.write_text("0000\nxxxx\n", encoding="ascii")
            expected.write_text("0000\n0000\n", encoding="ascii")

            metrics = numeric_compare(
                actual,
                {
                    "path": str(expected),
                    "sha256": sha256_file(expected),
                    "bits": 16,
                    "lanes": 1,
                },
                {"atol": 0.1, "rtol": 0.1, "max_mismatch_fraction": 0.05},
            )

            self.assertFalse(metrics["passed"])
            self.assertEqual(metrics["actual_decode"]["unknown_word_count"], 1)
            self.assertEqual(metrics["actual_decode"]["first_unknown_word_index"], 1)
            self.assertEqual(metrics["first_failed_word_index"], 1)
            self.assertEqual(metrics["expected_word"]["lanes"][0]["ieee_value"], 0.0)
            self.assertEqual(metrics["actual_output_sha256"], sha256_file(actual))

    def test_golden_unknown_diagnostics_are_exposed_to_debug_closure(self) -> None:
        stage = {"stage_id": "stage_generic", "op": "attention", "kind": "operator"}
        metrics = {
            "passed": False,
            "error": "RTL output contains Verilog unknown/high-impedance values",
            "failure_class": "unknown_logic_value",
            "first_mismatch_index": 8,
            "first_failed_word_index": 1,
            "first_failed_beat_index": 1,
            "first_failed_lane_index": 0,
            "first_actual_value": None,
            "first_expected_value": 1.5,
            "first_absolute_error": None,
            "first_relative_error": None,
            "num_mismatch": 8,
            "mismatch_fraction": 0.5,
            "actual_decode": {"first_unknown_literal": "x" * 32},
            "expected_word": {"status": "pass", "word_index": 1},
        }
        execution = {
            "status": "pass",
            "stage_id": "stage_generic",
            "rtl_output_sha256": "a" * 64,
            "input_fingerprint_sha256": "b" * 64,
            "canonical_reuse": {"canonical_run_id": "canonical-run"},
        }
        manifest = {
            "status": "ready",
            "numeric_comparison_policy": {"atol": 0.1, "rtol": 0.1, "max_mismatch_fraction": 0.05},
            "real_weight_source": {},
            "random_input": {},
        }
        contract = {
            "status": "ready",
            "path": "/tmp/contract.json",
            "testbench_sha256": "c" * 64,
            "expected_output": {"sha256": "d" * 64},
            "real_weight_bindings": [],
            "dut_harness": {"top_module": "StageGenericHarness", "consumed_tensor_hashes": []},
        }
        with patch(
            "scripts.verification.qwen_leaf_operator_verify.semantic_contract",
            return_value=(manifest, contract),
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.reusable_semantic_execution",
            return_value=(execution, []),
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.numeric_compare",
            return_value=metrics,
        ), patch(
            "scripts.verification.qwen_leaf_operator_verify.semantic_output_evidence",
            return_value={"status": "pass", "blockers": []},
        ):
            report = semantic_stage_report(Path("/tmp/run"), stage, "golden", 60, "new-run")

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["first_failed_module"], "StageGenericHarness")
        trace = report["debug_closure"]["boundary_trace"][0]
        self.assertEqual(trace["word_index"], 1)
        self.assertEqual(trace["lane_index"], 0)
        self.assertEqual(trace["observed_value"]["packed_literal"], "x" * 32)
        self.assertEqual(trace["expected_value"]["ieee_value"], 1.5)
        self.assertEqual(trace["rtl_output_sha256"], "a" * 64)

    def test_targeted_replay_without_exact_boundary_uses_failed_stage_neighbors(self) -> None:
        contracts = {
            "causal_paths": [
                {
                    "boundary_order": [
                        "boundary.in_to_stage01",
                        "boundary.stage01_to_out",
                        "boundary.unrelated",
                    ]
                }
            ],
            "boundaries": [
                {
                    "boundary_id": "boundary.in_to_stage01",
                    "src_stage": "stage_00",
                    "dst_stage": "stage_01",
                },
                {
                    "boundary_id": "boundary.stage01_to_out",
                    "src_stage": "stage_01",
                    "dst_stage": "stage_02",
                },
                {
                    "boundary_id": "boundary.unrelated",
                    "src_stage": "stage_03",
                    "dst_stage": "stage_04",
                },
            ],
        }

        plan = targeted_replay_plan(
            contracts,
            {"stage_id": "stage_01", "status": "fail"},
            "localized",
        )

        self.assertEqual(plan["strategy"], "failed_stage_adjacent_boundary_replay")
        self.assertEqual(
            [row["boundary_id"] for row in plan["probe_sequence"]],
            ["boundary.in_to_stage01", "boundary.stage01_to_out"],
        )
        self.assertEqual(plan["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"], "boundary.in_to_stage01")
        self.assertFalse(plan["acceptance"]["earliest_failed_boundary_identified"])
    internal_trace_records,
