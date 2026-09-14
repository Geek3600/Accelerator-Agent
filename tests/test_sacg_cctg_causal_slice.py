from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.sacg_cctg_causal_slice import (
    PROGRESS_SCHEMA_VERSION,
    build_sacg_cctg_causal_slice,
)
from accagent.framework.stage_llm import _compact_board_vcs_feedback


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def event(sequence: int, phase: str, *, layer: int = 0, token: int = -1, beat: int = -1) -> dict:
    return {
        "schema_version": PROGRESS_SCHEMA_VERSION,
        "sequence": sequence,
        "cycle": sequence * 10,
        "event_kind": "semantic_progress",
        "phase": phase,
        "semantic_progress": True,
        "layer": layer,
        "token": token,
        "beat": beat,
        "stage_or_boundary": phase,
        "prefetch_progress": {"accepted_beats": 8, "target_beats": 8},
        "runtime_load_progress": {"accepted_words": 4, "target_words": 4},
        "final_writeback_progress": {"accepted_beats": 0, "target_beats": 4},
    }


class SacgCctgCausalSliceTest(unittest.TestCase):
    def make_run(self, root: Path) -> tuple[Path, Path, dict]:
        run_dir = root / "run"
        write_json(
            run_dir / "repair" / "sacg_state.json",
            {
                "nodes": [
                    {"id": "node.pipeline.block_input", "type": "pipeline_boundary"},
                    {"id": "node.pipeline.stage_00", "type": "pipeline_stage"},
                    {"id": "node.pipeline.block_output", "type": "pipeline_boundary"},
                ],
                "edges": [
                    {
                        "id": "edge.data.block_input.to.stage_00.input",
                        "type": "stream",
                        "src": "node.pipeline.block_input",
                        "dst": "node.pipeline.stage_00",
                        "constraints": ["constraint.stream"],
                        "facts": {"flow_control": "ready_valid"},
                    },
                    {
                        "id": "edge.data.stage_00.to.block_output.output",
                        "type": "stream",
                        "src": "node.pipeline.stage_00",
                        "dst": "node.pipeline.block_output",
                        "constraints": ["constraint.stream"],
                        "facts": {"flow_control": "ready_valid"},
                    },
                ],
                "constraints": [
                    {
                        "id": "constraint.stream",
                        "type": "stream_order",
                        "edges": [
                            "edge.data.block_input.to.stage_00.input",
                            "edge.data.stage_00.to.block_output.output",
                        ],
                        "facts": {
                            "edge_contracts": [
                                {
                                    "edge_id": "edge.data.block_input.to.stage_00.input",
                                    "stream_contract": {"stream_order": ["token", "lane"]},
                                },
                                {
                                    "edge_id": "edge.data.stage_00.to.block_output.output",
                                    "stream_contract": {"stream_order": ["token", "lane"]},
                                },
                            ]
                        },
                    }
                ],
            },
        )
        write_json(
            run_dir / "verification" / "debug_closure" / "boundary_contracts.json",
            {
                "schema_version": "spatialaccagent.debug_boundary_contracts.v0",
                "boundaries": [
                    {
                        "boundary_id": "boundary.edge_data_block_input_to_stage_00_input",
                        "edge_id": "edge_data_block_input_to_stage_00_input",
                        "src_stage": "block_input",
                        "dst_stage": "stage_00",
                    },
                    {
                        "boundary_id": "boundary.edge_data_stage_00_to_block_output_output",
                        "edge_id": "edge_data_stage_00_to_block_output_output",
                        "src_stage": "stage_00",
                        "dst_stage": "block_output",
                    },
                ],
                "causal_paths": [
                    {
                        "path_id": "pipeline",
                        "stages": ["block_input", "stage_00", "block_output"],
                    }
                ],
            },
        )
        write_json(
            run_dir / "verification" / "certificates" / "single_layer_promotion_certificate.json",
            {
                "status": "pass",
                "required_gates": [{"name": "single_transformer_layer", "status": "pass"}],
                "policy": {"lower_layer_pass_evidence_is_reusable_not_absolute": True},
            },
        )
        write_json(
            run_dir / "verification" / "single_layer" / "single_layer_functional_report.json",
            {"pipeline_overlap_evidence": {"status": "pass", "transition_evidence": [{}, {}, {}]}},
        )
        write_json(
            run_dir / "verification" / "single_layer" / "single_layer_sim_stats.json",
            {"status": "pass", "input_beats": 8, "output_beats": 8, "cycles": 100},
        )
        executed_path = (
            run_dir
            / "verification"
            / "board_simulation"
            / "board_simulation_executed_manifest.json"
        )
        executed = {
            "multilayer_harness": {
                "target_layer_count": 2,
                "accepted_input_beats_per_layer": 8,
                "accepted_output_beats_per_layer": 8,
            }
        }
        write_json(executed_path, executed)
        return run_dir, executed_path, executed

    def write_events(self, run_dir: Path, rows: list[dict]) -> Path:
        path = (
            run_dir
            / "verification"
            / "board_simulation"
            / "reports"
            / "progress_event_log.jsonl"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        return path

    def build(self, run_dir: Path, executed_path: Path, executed: dict) -> dict:
        return build_sacg_cctg_causal_slice(
            run_dir=run_dir,
            runner={
                "input_fingerprint_sha256": "a" * 64,
                "remote_workdir": "/remote/exact-job",
            },
            executed_manifest=executed,
            failure_class="vcs_runtime_semantic_stall",
            executed_manifest_path=executed_path,
        )

    def test_rearm_without_next_output_selects_board_lifecycle_frontier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, executed_path, executed = self.make_run(Path(tmp))
            rows = [
                event(1, "runtime_load_complete", beat=3),
                event(2, "kernel_start"),
                *[
                    event(3 + token, "kernel_input_token_complete", token=token, beat=1)
                    for token in range(4)
                ],
                event(7, "kernel_output_token_start", token=0, beat=0),
                event(8, "kernel_output_token_complete", token=0, beat=1),
                event(9, "kernel_token_rearm_after_committed_output_quiescence", token=1),
                event(10, "weight_prefetch_complete", beat=8),
            ]
            self.write_events(run_dir, rows)
            result = self.build(run_dir, executed_path, executed)

        frontier = result["earliest_unproven_frontier"]
        self.assertEqual(frontier["frontier_id"], "kernel_rearm_to_next_output")
        self.assertEqual(frontier["observed"]["expected_output_tokens"], 4)
        self.assertEqual(frontier["observed"]["output_completed"], 1)
        self.assertEqual(frontier["observed"]["rearmed"], 1)
        self.assertEqual(
            len(result["causal_graph_slice"]["cctg_boundaries"]), 1
        )
        self.assertFalse(
            result["hierarchical_certificate_projection"]
            ["current_board_evidence_contradicts_lower_certificate"]
        )

    def test_no_output_selects_complete_connected_kernel_cctg_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, executed_path, executed = self.make_run(Path(tmp))
            rows = [
                event(1, "runtime_load_complete", beat=3),
                event(2, "kernel_start"),
                *[
                    event(3 + token, "kernel_input_token_complete", token=token, beat=1)
                    for token in range(4)
                ],
            ]
            self.write_events(run_dir, rows)
            result = self.build(run_dir, executed_path, executed)

        self.assertEqual(
            result["earliest_unproven_frontier"]["frontier_id"],
            "connected_kernel_input_to_output",
        )
        self.assertEqual(
            len(result["causal_graph_slice"]["cctg_boundaries"]), 2
        )

    def test_missing_rearm_does_not_assume_rearm_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, executed_path, executed = self.make_run(Path(tmp))
            rows = [
                event(1, "runtime_load_complete", beat=3),
                event(2, "kernel_start"),
                *[
                    event(3 + token, "kernel_input_token_complete", token=token, beat=1)
                    for token in range(4)
                ],
                event(7, "kernel_output_token_start", token=0, beat=0),
                event(8, "kernel_output_token_complete", token=0, beat=1),
                event(9, "weight_prefetch_complete", beat=8),
            ]
            self.write_events(run_dir, rows)
            result = self.build(run_dir, executed_path, executed)

        frontier = result["earliest_unproven_frontier"]
        self.assertEqual(
            frontier["frontier_id"],
            "kernel_output_token_sequence_continuation",
        )
        self.assertEqual(frontier["causal_domain"], "kernel_wrapper_lifecycle")
        self.assertIn("autonomous or explicitly rearmed", frontier["reason"])

    def test_explicit_cctg_failure_reopens_lower_layer_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir, executed_path, executed = self.make_run(Path(tmp))
            self.write_events(
                run_dir,
                [
                    event(1, "runtime_load_complete", beat=3),
                    event(2, "kernel_start"),
                    event(3, "kernel_input_token_complete", token=0, beat=1),
                ],
            )
            failed_id = "boundary.edge_data_stage_00_to_block_output_output"
            write_json(
                run_dir / "verification" / "debug_closure" / "boundary_trace.json",
                {"records": [{"boundary_id": failed_id, "status": "fail"}]},
            )
            result = self.build(run_dir, executed_path, executed)

        self.assertEqual(
            result["earliest_unproven_frontier"]["frontier_id"],
            "cctg_boundary_invariant_failure",
        )
        projection = result["hierarchical_certificate_projection"]
        self.assertTrue(
            projection["current_board_evidence_contradicts_lower_certificate"]
        )
        self.assertIn("reopen", projection["lower_layer_reopen_policy"])

    def test_llm_feedback_compaction_preserves_bound_causal_slice(self) -> None:
        causal_slice = {
            "schema_version": "spatialaccagent.sacg_cctg_causal_slice.v1",
            "status": "ready",
            "earliest_unproven_frontier": {"frontier_id": "frontier.x"},
        }
        compact = _compact_board_vcs_feedback(
            {
                "status": "needs_repair",
                "diagnosis": {
                    "path": "/run/diagnosis.json",
                    "sha256": "b" * 64,
                    "value": {
                        "status": "needs_repair",
                        "failure_evidence": {
                            "failure_class": "vcs_runtime_semantic_stall",
                            "sacg_cctg_causal_slice": {
                                "path": "/run/slice.json",
                                "sha256": "c" * 64,
                                "value": causal_slice,
                            },
                        },
                    },
                },
            }
        )

        projected = compact["diagnosis"]["value"]["failure_evidence"]
        self.assertEqual(
            projected["sacg_cctg_causal_slice"]["value"], causal_slice
        )


if __name__ == "__main__":
    unittest.main()
