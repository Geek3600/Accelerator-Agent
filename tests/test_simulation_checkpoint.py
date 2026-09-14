from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from accagent.framework.simulation_checkpoint import (
    CHECKPOINT_MANIFEST_SCHEMA_VERSION,
    activate_checkpoint_for_debug_episode,
    apply_checkpoint_retention_plan,
    checkpoint_framework_adapter_artifacts,
    checkpoint_debug_episode_path,
    checkpoint_cut_reachability,
    checkpoint_reuse_decision,
    close_checkpoint_debug_episode,
    framework_equivalence_certificate,
    checkpoint_request_errors,
    checkpoint_retention_plan,
    heavy_job_lease,
    prepare_checkpoint_debug_episode,
    prepare_checkpoint_request,
    read_checkpoint_cut_records,
    rebind_checkpoint_framework_adapter_artifacts,
    resource_admission,
    select_semantic_checkpoint_cut,
    semantic_checkpoint_cut_sha256,
    simulation_execution_identity,
)


def progress_event(sequence: int, cycle: int, phase: str) -> dict:
    return {
        "schema_version": "spatialaccagent.board_progress_event.v1",
        "sequence": sequence,
        "cycle": cycle,
        "event_kind": "semantic_progress",
        "phase": phase,
        "semantic_progress": True,
        "progress_epoch": sequence + 1,
        "layer": 0,
        "token": 0,
        "beat": 0,
        "stage_or_boundary": "pipeline_boundary.block_output",
        "axi_read": {},
        "axi_write": {},
        "active_boundary_observation": {},
    }


class SimulationCheckpointTest(unittest.TestCase):
    def test_framework_adapter_binding_repairs_copied_identity(self) -> None:
        authoritative = checkpoint_framework_adapter_artifacts()
        self.assertEqual(
            [row["kind"] for row in authoritative],
            ["vpi_source", "vpi_table"],
        )
        self.assertTrue(
            all(
                isinstance(row["sha256"], str)
                and len(row["sha256"]) == 64
                and row["framework_owned_read_only"] is True
                for row in authoritative
            )
        )
        contract = {
            "portable_state_capsule": {
                "dut_state_root": "AdaptiveBoardTb.dut",
                "framework_adapter_artifacts": [
                    {
                        **authoritative[0],
                        "sha256": authoritative[0]["sha256"] + "ea38",
                    },
                    authoritative[1],
                ],
                "preserved": True,
            }
        }

        rebound, report = rebind_checkpoint_framework_adapter_artifacts(contract)

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["changed"])
        self.assertEqual(
            rebound["portable_state_capsule"]["framework_adapter_artifacts"],
            authoritative,
        )
        self.assertEqual(
            rebound["portable_state_capsule"]["dut_state_root"],
            "AdaptiveBoardTb.dut",
        )
        self.assertTrue(rebound["portable_state_capsule"]["preserved"])
        self.assertEqual(
            len(
                contract["portable_state_capsule"][
                    "framework_adapter_artifacts"
                ][0]["sha256"]
            ),
            68,
        )

    def board_manifest(self, source_hash: str = "a" * 64) -> dict:
        return {
            "top_module": "board_tb",
            "validation_mode": "compute_slot_axi",
            "source_closure_sha256": "b" * 64,
            "compile_source_set_sha256": source_hash,
            "vcs_compile_plan_sha256": "c" * 64,
            "compile_source_files": [
                {
                    "source_id": "generated.wrapper",
                    "sha256": source_hash,
                    "role": "generated_board_source",
                }
            ],
            "artifacts": {
                "input": {"path": "input.memh", "sha256": "d" * 64},
                "weight_image": {
                    "path": "weights.bin",
                    "sha256": "e" * 64,
                    "byte_count": 1024,
                },
            },
            "vcs": {"runtime_plusargs": {"INPUT": "input"}},
            "compute_slot_abi_sha256": "f" * 64,
            "timing_contract_sha256": "1" * 64,
            "axi_interfaces_sha256": "2" * 64,
            "target_layer_count": 24,
        }

    def checkpoint_manifest(
        self,
        root: Path,
        identity: dict,
        *,
        state_schema_sha256: str = "3" * 64,
        frontier_id: str = "kernel_output_token_sequence_continuation",
    ) -> dict:
        state = root / "state.chk"
        state.write_bytes(b"checkpoint")
        cold_progress = root / "cold_progress.jsonl"
        restored_progress = root / "restored_progress.jsonl"
        progress_row = progress_event(5, 500, "kernel_output_token_complete")
        live_row = {
            **progress_event(6, 600, "semantic_progress_watch"),
            "event_kind": "heartbeat",
            "semantic_progress": False,
        }
        progress_payload = (
            json.dumps(progress_row) + "\n" + json.dumps(live_row) + "\n"
        ).encode()
        cold_progress.write_bytes(progress_payload)
        restored_progress.write_bytes(progress_payload)
        comparison_rows = []
        for kind in ("rtl_output", "boundary_trace"):
            cold = root / f"cold_{kind}.bin"
            restored = root / f"restored_{kind}.bin"
            cold.write_bytes(kind.encode())
            restored.write_bytes(kind.encode())
            comparison_rows.append(
                {
                    "kind": kind,
                    "cold_path": str(cold),
                    "cold_sha256": hashlib.sha256(cold.read_bytes()).hexdigest(),
                    "restored_path": str(restored),
                    "restored_sha256": hashlib.sha256(
                        restored.read_bytes()
                    ).hexdigest(),
                    "match": True,
                }
            )
        request_sha256 = "5" * 64
        reachability = {
            "schema_version": "spatialaccagent.checkpoint_cut_reachability.v1",
            "status": "pass",
            "future_cctg_nodes": ["wrapper.continuation"],
        }
        semantic_cut = {
            "status": "ready",
            "frontier_id": frontier_id,
            "future_cctg_nodes": ["wrapper.continuation"],
            "causal_reachability": reachability,
        }
        semantic_cut["cut_sha256"] = semantic_checkpoint_cut_sha256(semantic_cut)
        cut_sha256 = semantic_cut["cut_sha256"]
        equivalence = framework_equivalence_certificate(
            request_sha256=request_sha256,
            execution_identity=identity,
            semantic_cut={"cut_sha256": cut_sha256},
            capture_report={
                "captured_sequence": 5,
                "captured_cycle": 500,
                "state_schema": {"sha256": state_schema_sha256},
            },
            restore_report={
                "schema_version": (
                    "spatialaccagent.simulation_checkpoint_restore_report.v1"
                ),
                "status": "pass",
                "mode": "portable_cross_revision",
                "same_source_equivalence_probe": True,
                "request_sha256": request_sha256,
                "semantic_cut_sha256": cut_sha256,
                "runtime_state_schema_match": True,
                "runtime_state_schema_sha256": state_schema_sha256,
                "restored_sequence": 5,
                "restored_cycle": 500,
                "complete_testbench_external_state_restored": True,
                "pending_transactions_and_responses_restored": True,
                "immutable_files_reopened_at_captured_offsets": True,
                "event_queue_quiescent_after_restore": True,
            },
            cold_progress_path=cold_progress,
            restored_progress_path=restored_progress,
            cold_required_artifacts={
                row["kind"]: Path(row["cold_path"])
                for row in comparison_rows
            },
            restored_required_artifacts={
                row["kind"]: Path(row["restored_path"])
                for row in comparison_rows
            },
            cold_terminal={"returncode": 0, "failure_class": None},
            restored_terminal={"returncode": 0, "failure_class": None},
        )

        return {
            "schema_version": CHECKPOINT_MANIFEST_SCHEMA_VERSION,
            "status": "pass",
            "checkpoint_id": "checkpoint-1",
            "created_at_unix_sec": 100.0,
            "request_sha256": request_sha256,
            "execution_identity": identity,
            "semantic_cut": semantic_cut,
            "state_artifacts": [
                {
                    "path": str(state),
                    "sha256": hashlib.sha256(state.read_bytes()).hexdigest(),
                }
            ],
            "state_schema": {"sha256": state_schema_sha256},
            "portable_state_capsule": {"status": "pass"},
            "native_simulator_snapshot": {"status": "pass"},
            "causal_cut_certificate": {
                "status": "pass",
                "future_cctg_nodes": ["wrapper.continuation"],
                "reachability": reachability,
                "external_state_quiescent": True,
                "semantic_cut_sha256": cut_sha256,
            },
            "equivalence_certificate": equivalence,
            "total_state_bytes": state.stat().st_size,
            "remote_acknowledgment_status": "pass",
        }

    def write_debug_episode_evidence(
        self,
        run_dir: Path,
        *,
        duration_sec: float,
        frontier_id: str = "pipeline.output",
    ) -> None:
        board_dir = run_dir / "verification" / "board_simulation"
        vcs_dir = run_dir / "verification" / "vcs"
        diagnosis_dir = run_dir / "verification" / "case_diagnostics"
        board_dir.mkdir(parents=True)
        vcs_dir.mkdir(parents=True)
        diagnosis_dir.mkdir(parents=True)
        manifest = self.board_manifest()
        (board_dir / "board_simulation_manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        (board_dir / "board_simulation_executed_manifest.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        (vcs_dir / "case_board_vcs_functional.json").write_text(
            json.dumps(
                {
                    "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
                    "status": "fail",
                    "phase": "remote_vcs",
                    "input_fingerprint_sha256": "4" * 64,
                    "run": {"duration_sec": duration_sec},
                    "checkpoint_execution": {"candidate_screening": False},
                }
            ),
            encoding="utf-8",
        )
        diagnosis = {
            "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
            "status": "needs_repair",
            "failure_class": "vcs_runtime_semantic_stall",
        }
        causal = {
            "schema_version": "spatialaccagent.sacg_cctg_causal_slice.v1",
            "status": "ready",
            "earliest_unproven_frontier": {
                "status": "earliest_unproven",
                "frontier_id": frontier_id,
                "failure_class": "vcs_runtime_semantic_stall",
            },
        }
        diagnosis_path = diagnosis_dir / "vcs_functional_diagnosis.json"
        causal_path = diagnosis_dir / "sacg_cctg_causal_slice.json"
        diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
        causal_path.write_text(json.dumps(causal), encoding="utf-8")
        loop_dir = run_dir / "repair_execution" / "loop"
        for iteration in (1, 2):
            iteration_dir = loop_dir / f"iteration_{iteration:04d}"
            iteration_dir.mkdir(parents=True)
            diagnosis_snapshot = iteration_dir / "00_vcs_functional_diagnosis.json"
            causal_snapshot = iteration_dir / "01_sacg_cctg_causal_slice.json"
            diagnosis_snapshot.write_text(json.dumps(diagnosis), encoding="utf-8")
            causal_snapshot.write_text(json.dumps(causal), encoding="utf-8")
            record = {
                "schema_version": "spatialaccagent.stage8_repair_loop_iteration.v1",
                "iteration": iteration,
                "repair_execution_report": {"status": "incomplete"},
                "evidence_snapshots": [
                    {
                        "role": "capability_report",
                        "snapshot_path": str(diagnosis_snapshot),
                        "source_sha256": hashlib.sha256(
                            diagnosis_snapshot.read_bytes()
                        ).hexdigest(),
                    },
                    {
                        "role": "sacg_cctg_causal_slice",
                        "snapshot_path": str(causal_snapshot),
                        "source_sha256": hashlib.sha256(
                            causal_snapshot.read_bytes()
                        ).hexdigest(),
                    },
                ],
            }
            (iteration_dir / "iteration_record.json").write_text(
                json.dumps(record),
                encoding="utf-8",
            )

    def test_debug_episode_requires_long_reproduction_and_repeated_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=120.0)
            short = prepare_checkpoint_debug_episode(run_dir)
            (run_dir / "verification" / "vcs" / "case_board_vcs_functional.json").write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "input_fingerprint_sha256": "4" * 64,
                        "run": {"duration_sec": 1200.0},
                        "checkpoint_execution": {"candidate_screening": False},
                    }
                ),
                encoding="utf-8",
            )
            admitted = prepare_checkpoint_debug_episode(run_dir)

        self.assertEqual(short["status"], "not_admitted")
        self.assertEqual(admitted["status"], "active")
        self.assertTrue(admitted["checkpoint_required"])

    def test_debug_episode_survives_adaptive_frontier_movement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=1200.0)
            opened = prepare_checkpoint_debug_episode(run_dir)
            causal_path = (
                run_dir
                / "verification"
                / "case_diagnostics"
                / "sacg_cctg_causal_slice.json"
            )
            causal = json.loads(causal_path.read_text(encoding="utf-8"))
            causal["earliest_unproven_frontier"]["frontier_id"] = "pipeline.deeper"
            causal_path.write_text(json.dumps(causal), encoding="utf-8")
            continued = prepare_checkpoint_debug_episode(run_dir)

        self.assertEqual(continued["status"], "active")
        self.assertEqual(continued["episode_id"], opened["episode_id"])
        self.assertEqual(
            continued["latest_observation"]["frontier_id"],
            "pipeline.deeper",
        )
        self.assertEqual(continued["current_frontier_id"], "pipeline.deeper")
        self.assertEqual(
            [row["frontier_id"] for row in continued["frontier_history"]],
            ["pipeline.output", "pipeline.deeper"],
        )

    def test_active_episode_checkpoint_request_fails_closed_without_current_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=1200.0)
            episode = prepare_checkpoint_debug_episode(run_dir)
            reports_dir = run_dir / "verification" / "board_simulation" / "reports"
            reports_dir.mkdir(parents=True)
            (reports_dir / "progress_event_log.jsonl").write_text(
                json.dumps(progress_event(1, 100, "kernel_input_token_complete"))
                + "\n",
                encoding="utf-8",
            )
            causal_path = (
                run_dir
                / "verification"
                / "case_diagnostics"
                / "sacg_cctg_causal_slice.json"
            )
            causal = json.loads(causal_path.read_text(encoding="utf-8"))
            causal["earliest_unproven_frontier"] = {}
            causal_path.write_text(json.dumps(causal), encoding="utf-8")

            request = prepare_checkpoint_request(
                run_dir,
                debug_episode=episode,
            )

        binding = request["debug_episode_frontier_binding"]
        self.assertEqual(request["status"], "blocked")
        self.assertEqual(binding["status"], "fail")
        self.assertEqual(binding["expected_frontier_id"], "pipeline.output")
        self.assertIsNone(binding["observed_frontier_id"])
        self.assertTrue(
            any("frontier" in blocker for blocker in request["replay_decision"]["blockers"])
        )

    def test_active_episode_checkpoint_request_binds_current_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=1200.0)
            episode = prepare_checkpoint_debug_episode(run_dir)
            reports_dir = run_dir / "verification" / "board_simulation" / "reports"
            reports_dir.mkdir(parents=True)
            (reports_dir / "progress_event_log.jsonl").write_text(
                json.dumps(progress_event(1, 100, "kernel_input_token_complete"))
                + "\n",
                encoding="utf-8",
            )

            request = prepare_checkpoint_request(
                run_dir,
                debug_episode=episode,
            )

        binding = request["debug_episode_frontier_binding"]
        self.assertEqual(request["status"], "ready")
        self.assertEqual(binding["status"], "pass")
        self.assertEqual(request["semantic_cut"]["frontier_id"], "pipeline.output")
        self.assertEqual(checkpoint_request_errors(request), [])

    def test_debug_episode_activates_once_and_closes_after_full_cold_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=1200.0)
            episode = prepare_checkpoint_debug_episode(run_dir)
            checkpoint_dir = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "certified"
            )
            checkpoint_dir.mkdir(parents=True)
            identity = simulation_execution_identity(self.board_manifest())
            manifest = self.checkpoint_manifest(
                checkpoint_dir,
                identity,
                frontier_id=episode["initial_frontier_id"],
            )
            manifest["debug_episode"] = {
                "episode_id": episode["episode_id"],
                "initial_frontier_id": episode["initial_frontier_id"],
                "current_frontier_id": episode["current_frontier_id"],
            }
            manifest["debug_episode_id"] = episode["episode_id"]
            manifest_path = checkpoint_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            activated = activate_checkpoint_for_debug_episode(
                run_dir,
                manifest_path,
            )
            closed = close_checkpoint_debug_episode(
                run_dir,
                reason="full cold pass",
            )
            final_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            current = json.loads(
                checkpoint_debug_episode_path(run_dir).read_text(encoding="utf-8")
            )

        self.assertEqual(episode["status"], "active")
        self.assertEqual(activated["status"], "pass")
        self.assertEqual(closed["status"], "pass")
        self.assertFalse(final_manifest["active"])
        self.assertEqual(current["status"], "closed")

    def test_debug_episode_rejects_checkpoint_from_unbound_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=1200.0)
            episode = prepare_checkpoint_debug_episode(run_dir)
            checkpoint_dir = (
                run_dir
                / "verification"
                / "simulation_checkpoints"
                / "wrong_frontier"
            )
            checkpoint_dir.mkdir(parents=True)
            identity = simulation_execution_identity(self.board_manifest())
            manifest = self.checkpoint_manifest(
                checkpoint_dir,
                identity,
                frontier_id="unrelated.frontier",
            )
            manifest["debug_episode"] = {
                "episode_id": episode["episode_id"],
                "initial_frontier_id": episode["initial_frontier_id"],
            }
            manifest["debug_episode_id"] = episode["episode_id"]
            manifest_path = checkpoint_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            activation = activate_checkpoint_for_debug_episode(run_dir, manifest_path)

        self.assertEqual(activation["status"], "fail")
        self.assertTrue(
            any("frontier" in blocker for blocker in activation["blockers"])
        )

    def test_debug_episode_recovers_interrupted_close_from_full_cold_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            self.write_debug_episode_evidence(run_dir, duration_sec=1200.0)
            opened = prepare_checkpoint_debug_episode(run_dir)
            runner_path = (
                run_dir
                / "verification"
                / "vcs"
                / "case_board_vcs_functional.json"
            )
            runner_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "phase": "remote_vcs",
                        "stage_pass_eligible": True,
                        "run": {"duration_sec": 1200.0},
                        "checkpoint_execution": {"candidate_screening": False},
                    }
                ),
                encoding="utf-8",
            )

            recovered = prepare_checkpoint_debug_episode(run_dir)

        self.assertEqual(opened["status"], "active")
        self.assertEqual(recovered["status"], "closed")
        self.assertIn("interrupted", recovered["close_reason"])

    def test_cut_uses_latest_committed_semantic_event_before_frontier(self) -> None:
        rows = [
            progress_event(0, 100, "runtime_load_complete"),
            progress_event(1, 200, "kernel_output_token_complete"),
            progress_event(2, 300, "weight_prefetch_complete"),
        ]
        causal = {
            "earliest_unproven_frontier": {
                "frontier_id": "kernel_output_token_sequence_continuation",
                "observed": {"last_frontier_cycle": 250},
            }
        }

        cut = select_semantic_checkpoint_cut(rows, causal)

        self.assertEqual(cut["status"], "ready")
        self.assertEqual(cut["trigger"]["cycle"], 200)
        self.assertFalse(cut["portable_state_quiescent"])
        self.assertTrue(cut["portable_state_blockers"])

    def test_portable_cut_requires_explicit_external_quiescence(self) -> None:
        row = progress_event(0, 100, "kernel_output_token_complete")
        row["axi_read"] = {"outstanding": 0, "pending_response": False}
        row["axi_write"] = {"outstanding": 0, "pending_response": False}
        row["active_boundary_observation"] = {"event_queue_quiescent": True}

        cut = select_semantic_checkpoint_cut(
            [row],
            {
                "earliest_unproven_frontier": {
                    "frontier_id": "output_continuation",
                    "observed": {"last_frontier_cycle": 100},
                }
            },
        )

        self.assertTrue(cut["portable_state_quiescent"])
        self.assertEqual(cut["portable_state_blockers"], [])

    def test_cut_prefers_earlier_complete_quiescent_boundary(self) -> None:
        stable = progress_event(0, 100, "runtime_load_complete")
        stable["stage_or_boundary"] = "scheduler.pre_run_configuration"
        stable["axi_read"] = {"outstanding": 0, "pending_response": False}
        stable["axi_write"] = {"outstanding": 0, "pending_response": False}
        stable["active_boundary_observation"] = {
            "event_queue_quiescent": True
        }
        later = progress_event(1, 200, "kernel_output_token_complete")
        causal = {
            "earliest_unproven_frontier": {
                "frontier_id": "kernel_output_token_sequence_continuation",
                "observed": {"last_frontier_cycle": 250},
            }
        }

        cut = select_semantic_checkpoint_cut([stable, later], causal)

        self.assertEqual(cut["trigger"]["cycle"], 100)
        self.assertTrue(cut["portable_state_quiescent"])
        self.assertEqual(cut["selection_mode"], "complete_quiescent_boundary")

    def test_cut_reachability_contains_only_strict_downstream_graph(self) -> None:
        graph = {
            "sacg_nodes": [
                {"id": "node.pipeline.input", "name": "input"},
                {"id": "node.pipeline.middle", "name": "middle"},
                {"id": "node.pipeline.output", "name": "output"},
            ],
            "sacg_edges": [
                {
                    "id": "edge.input.middle",
                    "src": "node.pipeline.input",
                    "dst": "node.pipeline.middle",
                },
                {
                    "id": "edge.middle.output",
                    "src": "node.pipeline.middle",
                    "dst": "node.pipeline.output",
                },
            ],
            "cctg_boundaries": [
                {
                    "boundary_id": "boundary.input.middle",
                    "edge_id": "edge_input_middle",
                    "src_stage": "input",
                    "dst_stage": "middle",
                },
                {
                    "boundary_id": "boundary.middle.output",
                    "edge_id": "edge_middle_output",
                    "src_stage": "middle",
                    "dst_stage": "output",
                },
            ],
        }
        result = checkpoint_cut_reachability(
            {
                "status": "ready",
                "trigger": {
                    "phase": "middle_complete",
                    "stage_or_boundary": "pipeline_boundary.middle",
                },
            },
            graph,
        )

        self.assertEqual(result["status"], "pass")
        self.assertIn("node.pipeline.output", result["future_cctg_nodes"])
        self.assertNotIn("node.pipeline.input", result["future_cctg_nodes"])
        self.assertNotIn("node.pipeline.middle", result["future_cctg_nodes"])
        self.assertNotIn("edge.input.middle", result["future_cctg_nodes"])

    def test_cut_reachability_fails_closed_for_unknown_anchor(self) -> None:
        result = checkpoint_cut_reachability(
            {
                "status": "ready",
                "trigger": {
                    "phase": "runtime_load_complete",
                    "stage_or_boundary": "unmapped.external.scheduler",
                },
            },
            {
                "sacg_nodes": [
                    {"id": "node.pipeline.output", "name": "output"}
                ]
            },
        )

        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["future_cctg_nodes"], [])
        self.assertTrue(result["errors"])

    def test_execution_identity_separates_model_and_workload(self) -> None:
        first = simulation_execution_identity(self.board_manifest("a" * 64))
        second = simulation_execution_identity(self.board_manifest("9" * 64))

        self.assertNotEqual(
            first["compiled_model_sha256"], second["compiled_model_sha256"]
        )
        self.assertEqual(first["workload_sha256"], second["workload_sha256"])

    def test_execution_identity_uses_real_source_files_field(self) -> None:
        first_manifest = self.board_manifest("a" * 64)
        second_manifest = self.board_manifest("9" * 64)
        first_manifest["source_files"] = first_manifest.pop("compile_source_files")
        second_manifest["source_files"] = second_manifest.pop("compile_source_files")

        first = simulation_execution_identity(first_manifest)
        second = simulation_execution_identity(second_manifest)

        self.assertNotEqual(
            first["compiled_model_sha256"], second["compiled_model_sha256"]
        )

    def test_streaming_cut_reader_ignores_partial_tail_and_keeps_latest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "progress.jsonl"
            rows = [
                progress_event(0, 100, "runtime_load_complete"),
                progress_event(1, 200, "kernel_output_token_complete"),
                progress_event(2, 300, "kernel_output_token_complete"),
            ]
            path.write_bytes(
                b"".join((json.dumps(row) + "\n").encode() for row in rows)
                + b'{"partial":'
            )

            result = read_checkpoint_cut_records(
                path,
                {
                    "earliest_unproven_frontier": {
                        "observed": {"last_frontier_cycle": 250}
                    }
                },
            )

        self.assertTrue(result["streaming_read"])
        self.assertEqual(result["committed_record_count"], 3)
        self.assertEqual(result["records"][-1]["cycle"], 200)
        self.assertGreater(result["trailing_partial_byte_count"], 0)

    def test_streaming_reader_preserves_earlier_complete_quiescent_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "progress.jsonl"
            stable = progress_event(0, 100, "runtime_load_complete")
            stable["stage_or_boundary"] = "scheduler.pre_run_configuration"
            stable["axi_read"] = {
                "outstanding": 0,
                "pending_response": False,
            }
            stable["axi_write"] = {
                "outstanding": 0,
                "pending_response": False,
            }
            stable["active_boundary_observation"] = {
                "event_queue_quiescent": True
            }
            later = progress_event(1, 200, "kernel_output_token_complete")
            path.write_text(
                json.dumps(stable) + "\n" + json.dumps(later) + "\n",
                encoding="utf-8",
            )
            causal = {
                "earliest_unproven_frontier": {
                    "frontier_id": "kernel_output_token_sequence_continuation",
                    "observed": {"last_frontier_cycle": 250},
                }
            }

            records = read_checkpoint_cut_records(path, causal)
            cut = select_semantic_checkpoint_cut(records["records"], causal)

        self.assertEqual(cut["trigger"]["cycle"], 100)
        self.assertEqual(cut["selection_mode"], "complete_quiescent_boundary")
        self.assertIn(
            "latest_complete_quiescent",
            records["constant_memory_candidate_classes"],
        )

    def test_framework_builds_equivalence_only_from_matching_executed_suffixes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cold_progress = root / "cold.jsonl"
            restored_progress = root / "restored.jsonl"
            semantic = progress_event(10, 100, "kernel_output_token_complete")
            live = {
                **progress_event(11, 200, "semantic_progress_watch"),
                "event_kind": "heartbeat",
                "semantic_progress": False,
            }
            cold_progress.write_text(
                json.dumps(semantic)
                + "\n"
                + json.dumps(live)
                + "\n",
                encoding="utf-8",
            )
            restored_progress.write_text(
                json.dumps(semantic) + "\n" + json.dumps(live) + "\n",
                encoding="utf-8",
            )
            cold_rtl = root / "cold_rtl.bin"
            restored_rtl = root / "restored_rtl.bin"
            cold_boundary = root / "cold_boundary.json"
            restored_boundary = root / "restored_boundary.json"
            for path, payload in (
                (cold_rtl, b"rtl"),
                (restored_rtl, b"rtl"),
                (cold_boundary, b"boundary"),
                (restored_boundary, b"boundary"),
            ):
                path.write_bytes(payload)
            identity = simulation_execution_identity(self.board_manifest())
            request_sha256 = "7" * 64
            cut = {"cut_sha256": "8" * 64}
            capture = {
                "captured_sequence": 10,
                "captured_cycle": 100,
                "state_schema": {"sha256": "9" * 64},
            }
            restore = {
                "schema_version": (
                    "spatialaccagent.simulation_checkpoint_restore_report.v1"
                ),
                "status": "pass",
                "mode": "portable_cross_revision",
                "same_source_equivalence_probe": True,
                "request_sha256": request_sha256,
                "semantic_cut_sha256": cut["cut_sha256"],
                "runtime_state_schema_match": True,
                "runtime_state_schema_sha256": "9" * 64,
                "restored_sequence": 10,
                "restored_cycle": 100,
                "complete_testbench_external_state_restored": True,
                "pending_transactions_and_responses_restored": True,
                "immutable_files_reopened_at_captured_offsets": True,
                "event_queue_quiescent_after_restore": True,
            }

            certificate = framework_equivalence_certificate(
                request_sha256=request_sha256,
                execution_identity=identity,
                semantic_cut=cut,
                capture_report=capture,
                restore_report=restore,
                cold_progress_path=cold_progress,
                restored_progress_path=restored_progress,
                cold_required_artifacts={
                    "rtl_output": cold_rtl,
                    "boundary_trace": cold_boundary,
                },
                restored_required_artifacts={
                    "rtl_output": restored_rtl,
                    "boundary_trace": restored_boundary,
                },
                cold_terminal={"returncode": 86, "failure_class": "stall"},
                restored_terminal={"returncode": 86, "failure_class": "stall"},
            )

            cold_semantic = {
                **semantic,
                "scheduler_state": 30,
                "prefetch_progress": {
                    "accepted_beats": 466104,
                    "target_beats": 466104,
                },
                "active_boundary_observation": {
                    "input_axi_index": 896,
                    "output_ready": 1,
                },
            }
            restored_semantic = {
                **cold_semantic,
                "scheduler_state": 0,
                "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104,
                },
                "active_boundary_observation": {
                    "input_axi_index": 0,
                    "output_ready": 0,
                },
            }
            cold_progress.write_text(
                json.dumps(cold_semantic) + "\n" + json.dumps(live) + "\n",
                encoding="utf-8",
            )
            restored_progress.write_text(
                json.dumps(restored_semantic) + "\n" + json.dumps(live) + "\n",
                encoding="utf-8",
            )
            semantic_rejected = framework_equivalence_certificate(
                request_sha256=request_sha256,
                execution_identity=identity,
                semantic_cut=cut,
                capture_report=capture,
                restore_report=restore,
                cold_progress_path=cold_progress,
                restored_progress_path=restored_progress,
                cold_required_artifacts={
                    "rtl_output": cold_rtl,
                    "boundary_trace": cold_boundary,
                },
                restored_required_artifacts={
                    "rtl_output": restored_rtl,
                    "boundary_trace": restored_boundary,
                },
                cold_terminal={"returncode": 86, "failure_class": "stall"},
                restored_terminal={"returncode": 86, "failure_class": "stall"},
            )

            barrier = {
                **semantic,
                "phase": "checkpoint_quiescent_barrier",
            }
            cold_live = {
                **live,
                "scheduler_state": 30,
                "prefetch_progress": {
                    "accepted_beats": 466104,
                    "target_beats": 466104,
                },
                "active_boundary_observation": {"input_axi_index": 896},
            }
            restored_live = {
                **cold_live,
                "scheduler_state": 0,
                "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104,
                },
                "active_boundary_observation": {"input_axi_index": 0},
            }
            cold_progress.write_text(
                json.dumps(barrier) + "\n" + json.dumps(cold_live) + "\n",
                encoding="utf-8",
            )
            restored_progress.write_text(
                json.dumps(barrier) + "\n" + json.dumps(restored_live) + "\n",
                encoding="utf-8",
            )
            live_rejected = framework_equivalence_certificate(
                request_sha256=request_sha256,
                execution_identity=identity,
                semantic_cut=cut,
                capture_report=capture,
                restore_report=restore,
                cold_progress_path=cold_progress,
                restored_progress_path=restored_progress,
                cold_required_artifacts={
                    "rtl_output": cold_rtl,
                    "boundary_trace": cold_boundary,
                },
                restored_required_artifacts={
                    "rtl_output": restored_rtl,
                    "boundary_trace": restored_boundary,
                },
                cold_terminal={"returncode": 86, "failure_class": "stall"},
                restored_terminal={"returncode": 86, "failure_class": "stall"},
            )

            cold_progress.write_text(
                json.dumps(semantic) + "\n" + json.dumps(live) + "\n",
                encoding="utf-8",
            )
            restored_progress.write_text(
                json.dumps(semantic) + "\n" + json.dumps(live) + "\n",
                encoding="utf-8",
            )

            restored_rtl.write_bytes(b"changed")
            rejected = framework_equivalence_certificate(
                request_sha256=request_sha256,
                execution_identity=identity,
                semantic_cut=cut,
                capture_report=capture,
                restore_report=restore,
                cold_progress_path=cold_progress,
                restored_progress_path=restored_progress,
                cold_required_artifacts={
                    "rtl_output": cold_rtl,
                    "boundary_trace": cold_boundary,
                },
                restored_required_artifacts={
                    "rtl_output": restored_rtl,
                    "boundary_trace": restored_boundary,
                },
                cold_terminal={"returncode": 86, "failure_class": "stall"},
                restored_terminal={"returncode": 86, "failure_class": "stall"},
            )

        self.assertEqual(certificate["status"], "pass")
        self.assertEqual(
            certificate["same_source_cold_suffix_sha256"],
            certificate["restored_suffix_sha256"],
        )
        self.assertEqual(certificate["semantic_record_diff"]["status"], "match")
        self.assertEqual(semantic_rejected["status"], "fail")
        semantic_diff = semantic_rejected["semantic_record_diff"]
        self.assertEqual(semantic_diff["status"], "different")
        self.assertEqual(semantic_diff["differing_record_count"], 1)
        field_paths = {
            row["path"]
            for row in semantic_diff["record_differences"][0][
                "field_differences"
            ]
        }
        self.assertTrue(
            {
                "/scheduler_state",
                "/prefetch_progress/accepted_beats",
                "/active_boundary_observation/input_axi_index",
                "/active_boundary_observation/output_ready",
            }.issubset(field_paths)
        )
        self.assertEqual(live_rejected["status"], "fail")
        self.assertFalse(live_rejected["live_state_witness_match"])
        live_diff = live_rejected["live_state_witness_diff"]
        self.assertEqual(live_diff["status"], "different")
        live_field_paths = {
            row["path"] for row in live_diff["field_differences"]
        }
        self.assertTrue(
            {
                "/scheduler_state",
                "/prefetch_progress/accepted_beats",
                "/active_boundary_observation/input_axi_index",
            }.issubset(live_field_paths)
        )
        self.assertEqual(rejected["status"], "fail")
        self.assertTrue(any("rtl_output" in error for error in rejected["errors"]))

    def test_equivalence_accepts_matching_absence_for_failed_run_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cold_progress = root / "cold.jsonl"
            restored_progress = root / "restored.jsonl"
            semantic = progress_event(10, 100, "kernel_output_token_complete")
            live = {
                **progress_event(11, 200, "semantic_progress_watch"),
                "event_kind": "heartbeat",
                "semantic_progress": False,
            }
            payload = json.dumps(semantic) + "\n" + json.dumps(live) + "\n"
            cold_progress.write_text(payload, encoding="utf-8")
            restored_progress.write_text(payload, encoding="utf-8")
            cold_boundary = root / "cold_boundary.json"
            restored_boundary = root / "restored_boundary.json"
            cold_boundary.write_bytes(b"boundary")
            restored_boundary.write_bytes(b"boundary")
            request_sha256 = "7" * 64
            cut = {"cut_sha256": "8" * 64}
            capture = {
                "captured_sequence": 10,
                "captured_cycle": 100,
                "state_schema": {"sha256": "9" * 64},
            }
            restore = {
                "schema_version": (
                    "spatialaccagent.simulation_checkpoint_restore_report.v1"
                ),
                "status": "pass",
                "mode": "portable_cross_revision",
                "same_source_equivalence_probe": True,
                "request_sha256": request_sha256,
                "semantic_cut_sha256": cut["cut_sha256"],
                "runtime_state_schema_match": True,
                "runtime_state_schema_sha256": "9" * 64,
                "restored_sequence": 10,
                "restored_cycle": 100,
                "complete_testbench_external_state_restored": True,
                "pending_transactions_and_responses_restored": True,
                "immutable_files_reopened_at_captured_offsets": True,
                "event_queue_quiescent_after_restore": True,
            }
            certificate = framework_equivalence_certificate(
                request_sha256=request_sha256,
                execution_identity=simulation_execution_identity(
                    self.board_manifest()
                ),
                semantic_cut=cut,
                capture_report=capture,
                restore_report=restore,
                cold_progress_path=cold_progress,
                restored_progress_path=restored_progress,
                cold_required_artifacts={
                    "rtl_output": root / "cold_missing.bin",
                    "boundary_trace": cold_boundary,
                },
                restored_required_artifacts={
                    "rtl_output": root / "restored_missing.bin",
                    "boundary_trace": restored_boundary,
                },
                cold_terminal={"returncode": 86, "failure_class": "stall"},
                restored_terminal={"returncode": 86, "failure_class": "stall"},
            )

        missing = next(
            row
            for row in certificate["required_artifact_comparisons"]
            if row["kind"] == "rtl_output"
        )
        self.assertEqual(certificate["status"], "pass")
        self.assertFalse(missing["cold_present"])
        self.assertFalse(missing["restored_present"])
        self.assertTrue(missing["match"])

    def test_exact_model_checkpoint_uses_native_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity = simulation_execution_identity(self.board_manifest())
            manifest = self.checkpoint_manifest(Path(temp_dir), identity)

            decision = checkpoint_reuse_decision(manifest, identity)

        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "native_exact_model")
        self.assertTrue(decision["final_acceptance_requires_full_cold_run"])

    def test_exact_model_native_restart_still_requires_same_source_equivalence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity = simulation_execution_identity(self.board_manifest())
            manifest = self.checkpoint_manifest(Path(temp_dir), identity)
            manifest["equivalence_certificate"] = {}

            decision = checkpoint_reuse_decision(manifest, identity)

        self.assertEqual(decision["status"], "cold_capture_required")
        self.assertTrue(any("same-source" in row for row in decision["blockers"]))

    def test_exact_model_portable_capsule_reuses_without_repair_impact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity = simulation_execution_identity(self.board_manifest())
            manifest = self.checkpoint_manifest(Path(temp_dir), identity)
            manifest["native_simulator_snapshot"] = {"status": "not_captured"}

            decision = checkpoint_reuse_decision(manifest, identity)

        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "portable_cross_revision")

    def test_cross_revision_checkpoint_fails_closed_without_impact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prior = simulation_execution_identity(self.board_manifest("a" * 64))
            current = simulation_execution_identity(self.board_manifest("9" * 64))
            current["state_schema_sha256"] = "3" * 64
            manifest = self.checkpoint_manifest(Path(temp_dir), prior)

            decision = checkpoint_reuse_decision(manifest, current)

        self.assertEqual(decision["mode"], "cold_capture")
        self.assertTrue(
            any("impact" in blocker for blocker in decision["blockers"])
        )

    def test_cross_revision_checkpoint_requires_all_certificates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prior = simulation_execution_identity(self.board_manifest("a" * 64))
            current = simulation_execution_identity(self.board_manifest("9" * 64))
            current["state_schema_sha256"] = "3" * 64
            manifest = self.checkpoint_manifest(Path(temp_dir), prior)
            impact = {
                "status": "ready",
                "state_schema_change": "compatible",
                "affected_cctg_nodes": ["wrapper.continuation"],
            }

            decision = checkpoint_reuse_decision(
                manifest,
                current,
                repair_impact=impact,
            )

        self.assertEqual(decision["status"], "ready")
        self.assertEqual(decision["mode"], "portable_cross_revision")

    def test_cross_revision_checkpoint_requires_directed_reachability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prior = simulation_execution_identity(self.board_manifest("a" * 64))
            current = simulation_execution_identity(self.board_manifest("9" * 64))
            current["state_schema_sha256"] = "3" * 64
            manifest = self.checkpoint_manifest(Path(temp_dir), prior)
            manifest["causal_cut_certificate"]["reachability"] = {}
            decision = checkpoint_reuse_decision(
                manifest,
                current,
                repair_impact={
                    "status": "ready",
                    "state_schema_change": "compatible",
                    "affected_cctg_nodes": ["wrapper.continuation"],
                },
            )

        self.assertEqual(decision["mode"], "cold_capture")
        self.assertTrue(
            any("reachability" in blocker for blocker in decision["blockers"])
        )

    def test_forged_future_set_without_cut_rehash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prior = simulation_execution_identity(self.board_manifest("a" * 64))
            current = simulation_execution_identity(self.board_manifest("9" * 64))
            current["state_schema_sha256"] = "3" * 64
            manifest = self.checkpoint_manifest(Path(temp_dir), prior)
            forged = ["upstream.before_cut"]
            manifest["semantic_cut"]["future_cctg_nodes"] = forged
            manifest["semantic_cut"]["causal_reachability"][
                "future_cctg_nodes"
            ] = forged
            manifest["causal_cut_certificate"]["future_cctg_nodes"] = forged
            manifest["causal_cut_certificate"]["reachability"][
                "future_cctg_nodes"
            ] = forged
            decision = checkpoint_reuse_decision(
                manifest,
                current,
                repair_impact={
                    "status": "ready",
                    "state_schema_change": "compatible",
                    "affected_cctg_nodes": forged,
                },
            )

        self.assertEqual(decision["mode"], "cold_capture")
        self.assertTrue(
            any("semantic cut hash" in blocker for blocker in decision["blockers"])
        )

    def test_equal_but_forged_equivalence_digests_are_recomputed_and_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            prior = simulation_execution_identity(self.board_manifest("a" * 64))
            current = simulation_execution_identity(self.board_manifest("9" * 64))
            current["state_schema_sha256"] = "3" * 64
            manifest = self.checkpoint_manifest(Path(temp_dir), prior)
            manifest["equivalence_certificate"][
                "same_source_cold_suffix_sha256"
            ] = "0" * 64
            manifest["equivalence_certificate"]["restored_suffix_sha256"] = (
                "0" * 64
            )
            decision = checkpoint_reuse_decision(
                manifest,
                current,
                repair_impact={
                    "status": "ready",
                    "state_schema_change": "compatible",
                    "affected_cctg_nodes": ["wrapper.continuation"],
                },
            )

        self.assertEqual(decision["mode"], "cold_capture")
        self.assertTrue(any("equivalence" in row for row in decision["blockers"]))

    def test_retention_keeps_active_and_newest_per_frontier_within_budget(self) -> None:
        rows = [
            (
                Path("old-a/manifest.json"),
                {
                    "created_at_unix_sec": 1,
                    "total_state_bytes": 10,
                    "remote_acknowledgment_status": "pass",
                    "semantic_cut": {"frontier_id": "a"},
                },
            ),
            (
                Path("new-a/manifest.json"),
                {
                    "created_at_unix_sec": 3,
                    "total_state_bytes": 10,
                    "remote_acknowledgment_status": "pass",
                    "semantic_cut": {"frontier_id": "a"},
                },
            ),
            (
                Path("active-b/manifest.json"),
                {
                    "created_at_unix_sec": 2,
                    "total_state_bytes": 10,
                    "remote_acknowledgment_status": "pending",
                    "semantic_cut": {"frontier_id": "b"},
                },
            ),
        ]

        plan = checkpoint_retention_plan(rows, max_count=2, max_bytes=20)

        self.assertIn("new-a/manifest.json", plan["keep"])
        self.assertIn("active-b/manifest.json", plan["keep"])
        self.assertIn("old-a/manifest.json", plan["prune"])

    def test_retention_bounds_distinct_frontiers_globally(self) -> None:
        rows = [
            (
                Path(f"checkpoint-{created}/manifest.json"),
                {
                    "created_at_unix_sec": created,
                    "total_state_bytes": 10,
                    "remote_acknowledgment_status": "pass",
                    "semantic_cut": {"frontier_id": frontier},
                },
            )
            for created, frontier in ((1, "a"), (2, "b"), (3, "c"))
        ]

        plan = checkpoint_retention_plan(rows, max_count=2, max_bytes=20)

        self.assertEqual(
            plan["keep"],
            ["checkpoint-3/manifest.json", "checkpoint-2/manifest.json"],
        )
        self.assertEqual(plan["prune"], ["checkpoint-1/manifest.json"])
        self.assertEqual(plan["kept_bytes"], 20)
        self.assertFalse(plan["budget_overflow"])

    def test_retention_keeps_only_latest_when_one_checkpoint_exceeds_bytes(self) -> None:
        rows = [
            (
                Path("older/manifest.json"),
                {
                    "created_at_unix_sec": 1,
                    "total_state_bytes": 5,
                    "remote_acknowledgment_status": "pass",
                    "semantic_cut": {"frontier_id": "older"},
                },
            ),
            (
                Path("latest/manifest.json"),
                {
                    "created_at_unix_sec": 2,
                    "total_state_bytes": 25,
                    "remote_acknowledgment_status": "pass",
                    "semantic_cut": {"frontier_id": "latest"},
                },
            ),
        ]

        plan = checkpoint_retention_plan(rows, max_count=2, max_bytes=20)

        self.assertEqual(plan["keep"], ["latest/manifest.json"])
        self.assertEqual(plan["prune"], ["older/manifest.json"])
        self.assertTrue(plan["budget_overflow"])
        self.assertIn("alone exceeds", plan["budget_overflow_reasons"][0])

    def test_retention_does_not_add_prunable_state_after_protected_overflow(self) -> None:
        rows = [
            (
                Path("protected/manifest.json"),
                {
                    "created_at_unix_sec": 1,
                    "total_state_bytes": 25,
                    "remote_acknowledgment_status": "pending",
                    "semantic_cut": {"frontier_id": "protected"},
                },
            ),
            (
                Path("usable/manifest.json"),
                {
                    "created_at_unix_sec": 2,
                    "total_state_bytes": 5,
                    "remote_acknowledgment_status": "pass",
                    "semantic_cut": {"frontier_id": "usable"},
                },
            ),
        ]

        plan = checkpoint_retention_plan(rows, max_count=1, max_bytes=20)

        self.assertEqual(plan["keep"], ["protected/manifest.json"])
        self.assertEqual(plan["prune"], ["usable/manifest.json"])
        self.assertTrue(plan["budget_overflow"])

    def test_retention_execution_deletes_only_acknowledged_planned_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            root = run_dir / "verification" / "simulation_checkpoints"
            old = root / "old" / "manifest.json"
            new = root / "new" / "manifest.json"
            for path, created in ((old, 1), (new, 2)):
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps(
                        {
                            "created_at_unix_sec": created,
                            "total_state_bytes": 1,
                            "remote_acknowledgment_status": "pass",
                            "semantic_cut": {"frontier_id": "output"},
                        }
                    ),
                    encoding="utf-8",
                )
            plan = checkpoint_retention_plan(
                [(old, json.loads(old.read_text())), (new, json.loads(new.read_text()))],
                max_count=1,
                max_bytes=1,
            )

            result = apply_checkpoint_retention_plan(run_dir, plan)

            self.assertEqual(result["status"], "pass")
            self.assertFalse(old.parent.exists())
            self.assertTrue(new.parent.exists())

    def test_resource_admission_reserves_memory_for_one_job(self) -> None:
        admitted = resource_admission(
            purpose="vcs",
            estimated_peak_bytes=2,
            minimum_available_bytes=3,
            observed_available_bytes=5,
        )
        waiting = resource_admission(
            purpose="vcs",
            estimated_peak_bytes=3,
            minimum_available_bytes=3,
            observed_available_bytes=5,
        )

        self.assertEqual(admitted["status"], "pass")
        self.assertEqual(waiting["status"], "wait")
        self.assertEqual(admitted["max_heavy_jobs"], 1)

    def test_heavy_job_lease_rejects_a_second_nonblocking_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            with heavy_job_lease(run_dir, purpose="first", wait=False):
                with self.assertRaises(RuntimeError):
                    with heavy_job_lease(run_dir, purpose="second", wait=False):
                        pass

    def test_prepare_request_never_calls_missing_hook_a_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            board_dir = run_dir / "verification" / "board_simulation"
            diagnosis_dir = run_dir / "verification" / "case_diagnostics"
            reports_dir = board_dir / "reports"
            reports_dir.mkdir(parents=True)
            diagnosis_dir.mkdir(parents=True)
            (board_dir / "board_simulation_manifest.json").write_text(
                json.dumps(self.board_manifest()), encoding="utf-8"
            )
            (diagnosis_dir / "sacg_cctg_causal_slice.json").write_text(
                json.dumps(
                    {
                        "earliest_unproven_frontier": {
                            "frontier_id": "output_continuation",
                            "observed": {"last_frontier_cycle": 100},
                        }
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "progress_event_log.jsonl").write_text(
                json.dumps(progress_event(0, 100, "kernel_output_token_complete"))
                + "\n",
                encoding="utf-8",
            )

            request = prepare_checkpoint_request(run_dir)

            self.assertEqual(checkpoint_request_errors(request), [])
            request["semantic_cut"]["trigger"]["cycle"] += 1
            self.assertIn(
                "checkpoint request hash does not match its semantic projection",
                checkpoint_request_errors(request),
            )

        self.assertEqual(request["status"], "ready")
        self.assertEqual(
            request["checkpoint_contract_status"], "missing_or_invalid"
        )
        self.assertEqual(request["replay_decision"]["mode"], "cold_capture")
        self.assertTrue(
            request["acceptance_policy"][
                "full_cold_exact_board_vcs_required_before_stage_pass"
            ]
        )


if __name__ == "__main__":
    unittest.main()
