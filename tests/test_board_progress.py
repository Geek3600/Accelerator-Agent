from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.board_progress import (
    BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
    REQUIRED_PROGRESS_EVENT_FIELDS,
    adaptive_semantic_stall_evidence,
    intra_layer_pipeline_violation_evidence,
    normalize_adaptive_semantic_stall_evidence,
    pipeline_boundary_observation_authority,
    read_pipeline_trace_log,
    stage_internal_records_from_boundary_observations,
    summarize_stage_internal_observations,
    read_complete_jsonl,
    summarize_pipeline_boundary_observations,
    summarize_progress_events,
)


def event(
    sequence: int,
    cycle: int,
    event_kind: str,
    semantic_progress: bool,
) -> dict:
    row = {field: None for field in REQUIRED_PROGRESS_EVENT_FIELDS}
    row.update(
        {
            "schema_version": BOARD_PROGRESS_EVENT_SCHEMA_VERSION,
            "sequence": sequence,
            "cycle": cycle,
            "event_kind": event_kind,
            "phase": "compute",
            "semantic_progress": semantic_progress,
            "progress_epoch": int(semantic_progress),
            "last_semantic_progress_cycle": 10,
            "scheduler_state": "compute",
            "layer": 0,
            "token": 0,
            "beat": 0,
            "stage_or_boundary": "block_input",
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
    return row


class BoardProgressTest(unittest.TestCase):
    def test_stage_snapshots_are_projected_for_every_current_compute_stage(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.input", "edge.output"],
                    "boundary_contracts": [
                        {
                            "boundary_id": "edge.input",
                            "src_stage": "block_input",
                            "dst_stage": "stage_a",
                        },
                        {
                            "boundary_id": "edge.output",
                            "src_stage": "stage_a",
                            "dst_stage": "block_output",
                        },
                    ],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "edge.output",
                "cycle": 10,
                "token": 0,
                "beat": 0,
                "status": "first_transfer",
                "observed_value": {
                    "stage_a": {"operator_state": 1, "queue_count": 2}
                },
            },
            {
                "boundary_id": "edge.output",
                "cycle": 20,
                "token": 0,
                "beat": 1,
                "status": "terminal",
                "observed_value": {
                    "stage_a": {"operator_state": 2, "queue_count": 0}
                },
            },
        ]

        projected = stage_internal_records_from_boundary_observations(
            records, authority
        )
        summary = summarize_stage_internal_observations(projected, authority)

        self.assertEqual(len(projected), 4)
        self.assertEqual(summary["observed_stage_count"], 1)
        stage = summary["stage_summaries"][0]
        self.assertEqual(stage["signal_names"], ["operator_state", "queue_count"])
        self.assertEqual(stage["first_cycle"], 10)
        self.assertEqual(stage["last_cycle"], 20)

    def test_stage_trace_log_parses_scalar_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "simulation.log"
            path.write_text(
                "SPATIALACC_STAGE_TRACE stage=stage_a cycle=10 token=0 beat=1 "
                "event=first_transfer signal=queue_count value=3\n",
                encoding="utf-8",
            )
            parsed = read_pipeline_trace_log(path)

        self.assertEqual(parsed["stage_unparsed"], 0)
        self.assertEqual(parsed["stage_records"][0]["stage_id"], "stage_a")
        self.assertEqual(parsed["stage_records"][0]["signal"], "queue_count")
        self.assertEqual(parsed["stage_records"][0]["value"], 3)

    def test_boundary_observation_authority_is_derived_from_current_pipeline(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "contract_sha256": "a" * 64,
                    "trace_contract_sha256": "b" * 64,
                    "pipeline_plan_sha256": "c" * 64,
                    "token_count": 2,
                    "beats_per_token": 2,
                    "required_boundaries": ["edge.input", "edge.output"],
                    "boundary_contracts": [
                        {
                            "boundary_id": "edge.input",
                            "src_stage": "block_input",
                            "dst_stage": "stage_a",
                            "kind": "main",
                            "flow_control": "ready_valid",
                            "beats_per_token": 2,
                        },
                        {
                            "boundary_id": "edge.output",
                            "src_stage": "stage_a",
                            "dst_stage": "block_output",
                            "kind": "main",
                            "flow_control": "ready_valid",
                            "beats_per_token": 2,
                        },
                    ],
                }
            }
        }

        authority = pipeline_boundary_observation_authority(
            manifest,
            testbench_source={"source_id": "tb", "sha256": "d" * 64},
        )

        self.assertEqual(authority["status"], "ready")
        self.assertEqual(
            [row["stage_id"] for row in authority["required_stages"]],
            ["stage_a"],
        )
        self.assertEqual(
            [row["boundary_id"] for row in authority["required_boundaries"]],
            ["edge.input", "edge.output"],
        )
        self.assertEqual(authority["required_fields"][:3], ["valid", "ready", "fire"])
        self.assertEqual(authority["expected_token_count"], 2)
        self.assertEqual(authority["expected_beats_per_token"], 2)
        self.assertIn("current_payload_digest", authority["optional_diagnostic_fields"])
        self.assertTrue(
            authority["record_policy"]["extra_internal_signal_snapshots_are_optional"]
        )
        self.assertTrue(authority["authority_sha256"])

    def test_boundary_summary_keeps_extra_internal_signal_snapshots_bounded(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.output"],
                    "boundary_contracts": [{"boundary_id": "edge.output"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "edge.output",
                "cycle": 10,
                "token": 0,
                "beat": 0,
                "observed_value": {
                    "valid": 1,
                    "ready": 1,
                    "fire": 1,
                    "accepted_count": 1,
                    "current_payload_unknown": False,
                    "current_payload_digest": "first",
                    "scheduler_state": "run",
                    "mlp_down_output": {
                        "valid": 1,
                        "ready": 1,
                        "accepted_count": 1,
                    },
                    "event": "first_accepted_beat",
                },
            },
            {
                "boundary_id": "edge.output",
                "cycle": 20,
                "token": 0,
                "beat": 1,
                "observed_value": {
                    "valid": 1,
                    "ready": 1,
                    "fire": 1,
                    "accepted_count": 2,
                    "current_payload_unknown": False,
                    "current_payload_digest": "last",
                    "scheduler_state": "drain",
                    "mlp_down_output": {
                        "valid": 0,
                        "ready": 1,
                        "accepted_count": 2,
                    },
                    "event": "last_accepted_beat",
                },
            },
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        boundary = summary["boundary_summaries"][0]
        self.assertEqual(summary["status"], "complete")
        self.assertTrue(boundary["extra_signal_observed"])
        self.assertIn("mlp_down_output.valid", boundary["extra_signal_names"])
        self.assertIn("scheduler_state", boundary["extra_signal_names"])
        self.assertEqual(len(boundary["extra_signal_snapshots"]), len(records))
        for snapshot in boundary["extra_signal_snapshots"]:
            self.assertGreater(len(snapshot["signals"]), 0)

    def test_boundary_summary_keeps_all_declared_key_scalar_signals(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.output"],
                    "boundary_contracts": [{"boundary_id": "edge.output"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        key_signals = {f"internal_state_{index}": index for index in range(96)}
        records = [
            {
                "boundary_id": "edge.output",
                "cycle": 1,
                "token": 0,
                "beat": 0,
                "valid": 1,
                "ready": 1,
                "fire": 1,
                "accepted_count": 1,
                "payload_digest": "first",
                "observed_value": key_signals,
            }
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        boundary = summary["boundary_summaries"][0]
        self.assertTrue(boundary["extra_signal_observed"])
        self.assertTrue(
            set(key_signals).issubset(set(boundary["extra_signal_names"]))
        )
        self.assertEqual(
            len(boundary["extra_signal_snapshots"][0]["signals"]),
            len(boundary["extra_signal_names"]),
        )

    def test_progress_summary_keeps_scheduler_bank_and_axi_snapshots(self) -> None:
        row = event(1, 20, "semantic_progress", True)
        row.update(
            {
                "scheduler_state": "write_output",
                "active_weight_bank": "weight_a",
                "activation_write_bank": "activation_pong",
                "final_writeback_progress": {"accepted_beats": 21, "target_beats": 896},
                "axi_write": {"outstanding": 1, "awvalid": 1, "wvalid": 1},
                "active_boundary_observation": {
                    "output_valid": 1,
                    "output_ready": 1,
                    "output_accept_count": 21,
                },
            }
        )

        summary = summarize_progress_events([row])

        self.assertIn("scheduler_state", summary["extra_signal_names"])
        self.assertIn("axi_write.outstanding", summary["extra_signal_names"])
        self.assertIn(
            "final_writeback_progress.accepted_beats",
            summary["extra_signal_names"],
        )
        self.assertTrue(summary["extra_signal_snapshots"])

    def test_boundary_observation_summary_is_bounded_and_reports_incomplete_data(self) -> None:
        manifest = {
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
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "boundary.edge_input",
                "cycle": index,
                "valid": 1,
                "ready": 1,
                "fire": 1,
                "accepted_count": index + 1,
                "payload_digest": f"{index:08x}",
            }
            for index in range(3)
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        self.assertEqual(summary["status"], "complete")
        boundary = summary["boundary_summaries"][0]
        self.assertEqual(boundary["accepted_record_count"], 3)
        self.assertEqual(boundary["first_accepted_payload_digest"], "00000000")
        self.assertEqual(boundary["last_accepted_payload_digest"], "00000002")
        self.assertEqual(summary["unexpected_boundary_ids"], [])

        incomplete = summarize_pipeline_boundary_observations(
            [{"boundary_id": "edge.input", "valid": 1}], authority
        )
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertIn("edge.input", incomplete["incomplete_boundary_ids"])

    def test_boundary_snapshot_reuses_explicit_first_and_last_digests(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [{"boundary_id": "edge.input"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "boundary.edge_input",
                "observed_value": {
                    "valid": 0,
                    "ready": 1,
                    "fire": 0,
                    "accepted_count": 3,
                    "first_accepted_payload_digest": "first",
                    "first_accepted_payload_digest_unknown": False,
                    "last_accepted_payload_digest": "last",
                    "last_accepted_payload_digest_unknown": False,
                },
            }
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        self.assertEqual(summary["status"], "incomplete")
        boundary = summary["boundary_summaries"][0]
        self.assertEqual(boundary["first_accepted_payload_digest"], "first")
        self.assertEqual(boundary["last_accepted_payload_digest"], "last")
        self.assertFalse(boundary["temporal_observation_complete"])

    def test_boundary_snapshot_accepts_known_zero_transfer_endpoint(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.output"],
                    "boundary_contracts": [{"boundary_id": "edge.output"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "boundary.edge_output",
                "cycle": 100,
                "token": 0,
                "beat": 0,
                "observed_value": {
                    "core_egress_valid": 0,
                    "core_egress_ready": 1,
                    "core_egress_accepted_count": 0,
                    "current_payload_digest": "xxxxxxxx",
                    "current_payload_unknown": True,
                    "observation_phase": "post_input_stall",
                },
                "status": "stalled",
            },
            {
                "boundary_id": "boundary.edge_output",
                "cycle": 200,
                "token": 0,
                "beat": 0,
                "observed_value": {
                    "core_egress_valid": 0,
                    "core_egress_ready": 1,
                    "core_egress_accepted_count": 0,
                    "current_payload_digest": "xxxxxxxx",
                    "current_payload_unknown": True,
                    "observation_phase": "final_waiting_summary",
                },
                "status": "terminal",
            }
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        self.assertEqual(summary["status"], "complete")
        boundary = summary["boundary_summaries"][0]
        self.assertEqual(boundary["accepted_count_max"], 0)
        self.assertTrue(boundary["payload_absent_due_to_zero_transfers"])
        self.assertIsNone(boundary["first_accepted_payload_digest"])
        self.assertTrue(
            boundary["zero_transfer_waiting_coverage"]["complete"]
        )

    def test_bound_token_contract_requires_first_and_last_record_for_each_token(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "token_count": 2,
                    "beats_per_token": 2,
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [
                        {"boundary_id": "edge.input", "beats_per_token": 2}
                    ],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = []
        for token in range(2):
            for beat in (0, 1):
                records.append(
                    {
                        "boundary_id": "edge.input",
                        "cycle": token * 10 + beat,
                        "token": token,
                        "beat": beat,
                        "valid": 1,
                        "ready": 1,
                        "fire": 1,
                        "accepted_count": token * 2 + beat + 1,
                        "payload_digest": f"t{token}b{beat}",
                    }
                )

        summary = summarize_pipeline_boundary_observations(records, authority)

        self.assertEqual(summary["status"], "complete")
        coverage = summary["boundary_summaries"][0]["token_coverage"]
        self.assertEqual(coverage["missing_token_ids"], [])
        self.assertEqual(
            coverage["token_summaries"][1]["last_accepted_payload_digest"],
            "t1b1",
        )

    def test_bound_token_contract_rejects_single_transfer_without_last_beat(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "token_count": 1,
                    "beats_per_token": 2,
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [
                        {"boundary_id": "edge.input", "beats_per_token": 2}
                    ],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        summary = summarize_pipeline_boundary_observations(
            [
                {
                    "boundary_id": "edge.input",
                    "cycle": 10,
                    "token": 0,
                    "beat": 0,
                    "valid": 1,
                    "ready": 1,
                    "fire": 1,
                    "accepted_count": 1,
                    "payload_digest": "t0b0",
                }
            ],
            authority,
        )

        self.assertEqual(summary["status"], "incomplete")
        boundary = summary["boundary_summaries"][0]
        self.assertEqual(boundary["token_coverage"]["missing_token_ids"], [0])
        self.assertIn("edge.input", summary["incomplete_boundary_ids"])

    def test_missing_later_tokens_are_functional_progress_not_missing_observation(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "token_count": 2,
                    "beats_per_token": 4,
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [
                        {"boundary_id": "edge.input", "beats_per_token": 4}
                    ],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        summary = summarize_pipeline_boundary_observations(
            [
                {
                    "boundary_id": "edge.input",
                    "cycle": 10,
                    "token": 0,
                    "beat": 0,
                    "valid": 1,
                    "ready": 1,
                    "fire": 1,
                    "accepted_count": 1,
                    "payload_digest": "first",
                },
                {
                    "boundary_id": "edge.input",
                    "cycle": 20,
                    "token": 0,
                    "beat": 2,
                    "valid": 1,
                    "ready": 1,
                    "fire": 1,
                    "accepted_count": 3,
                    "payload_digest": "last-observed",
                },
            ],
            authority,
        )

        self.assertEqual(summary["status"], "complete")
        coverage = summary["boundary_summaries"][0]["token_coverage"]
        self.assertEqual(coverage["absent_token_ids"], [1])
        self.assertEqual(coverage["partial_token_ids"], [0])
        self.assertEqual(coverage["incomplete_observed_token_ids"], [])

    def test_ready_valid_fire_is_not_erased_by_an_early_zero_counter_snapshot(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [{"boundary_id": "edge.input"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "edge.input",
                "valid": 0,
                "ready": 1,
                "fire": 0,
                "accepted_count": 0,
            },
            {
                "boundary_id": "edge.input",
                "valid": 1,
                "ready": 1,
                "fire": 1,
                "cycle": 10,
                "token": 0,
                "beat": 0,
                "payload_digest": "first",
            },
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        boundary = summary["boundary_summaries"][0]
        self.assertEqual(boundary["accepted_count_max"], 0)
        self.assertEqual(boundary["accepted_count_lower_bound"], 1)
        self.assertEqual(boundary["accepted_count_source"], "counter_and_ready_valid_fire")
        self.assertTrue(boundary["transfer_observed"])
        self.assertFalse(boundary["payload_absent_due_to_zero_transfers"])
        self.assertEqual(boundary["first_accepted_payload_digest"], "first")

    def test_boundary_snapshot_records_unknown_payload_as_observed(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [{"boundary_id": "edge.input"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "boundary.edge_input",
                "observed_value": {
                    "valid": 1,
                    "ready": 1,
                    "fire": 1,
                    "accepted_count": 3,
                    "first_accepted_payload_seen": True,
                    "first_accepted_payload_digest": "xxxxxxxx",
                    "first_accepted_payload_digest_unknown": True,
                    "last_accepted_payload_seen": True,
                    "last_accepted_payload_digest": "xxxxxxxx",
                    "last_accepted_payload_digest_unknown": True,
                },
            }
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        self.assertEqual(summary["status"], "complete")
        boundary = summary["boundary_summaries"][0]
        self.assertTrue(boundary["payload_unavailable_due_to_unknown_bits"])
        self.assertIsNone(boundary["first_accepted_payload_digest"])

    def test_one_time_counter_snapshot_is_not_complete_temporal_coverage(self) -> None:
        manifest = {
            "single_layer": {
                "pipeline_overlap_contract": {
                    "required_boundaries": ["edge.input"],
                    "boundary_contracts": [{"boundary_id": "edge.input"}],
                }
            }
        }
        authority = pipeline_boundary_observation_authority(manifest)
        records = [
            {
                "boundary_id": "edge.input",
                "observed_value": {
                    "valid": 0,
                    "ready": 1,
                    "fire": 0,
                    "accepted_count": 8,
                    "first_accepted_payload_digest": "first",
                    "first_accepted_payload_digest_unknown": False,
                    "last_accepted_payload_digest": "last",
                    "last_accepted_payload_digest_unknown": False,
                },
            }
        ]

        summary = summarize_pipeline_boundary_observations(records, authority)

        self.assertEqual(summary["status"], "incomplete")
        boundary = summary["boundary_summaries"][0]
        self.assertFalse(boundary["temporal_transfer_observed"])
        self.assertFalse(boundary["observation_complete"])

    def test_recovered_orphaned_stall_is_normalized_for_diagnosis(self) -> None:
        recovered = {
            "schema_version": "spatialaccagent.orphaned_board_job_semantic_stall_recovery.v1",
            "status": "proven_semantic_stall",
            "last_semantic_event": {"cycle": 100, "phase": "prefetch_complete"},
            "latest_complete_remote_event": {"cycle": 1_000, "phase": "watch"},
            "observed_silent_cycles": 900,
            "observed_stall_snapshot_count": 8,
            "adaptive_bound": {
                "cycles": 400,
                "fixed_cycle_timeout": False,
                "fixed_wall_clock_timeout": False,
            },
        }

        normalized = normalize_adaptive_semantic_stall_evidence(recovered)

        self.assertEqual(
            normalized["schema_version"],
            "spatialaccagent.adaptive_semantic_stall_evidence.v1",
        )
        self.assertEqual(normalized["last_semantic_event_cycle"], 100)
        self.assertEqual(normalized["latest_cycle"], 1_000)
        self.assertEqual(normalized["adaptive_silent_cycle_bound"], 400)

    def cctg_frontier_rows(self) -> tuple[list[dict], dict]:
        rows = [
            event(0, 100, "semantic_progress", True),
            event(1, 101, "semantic_progress", True),
        ]
        rows[0]["phase"] = "runtime_load_complete"
        rows[1]["phase"] = "kernel_start"
        for token, cycle in enumerate((200, 210, 220, 230), start=0):
            row = event(2 + token, cycle, "semantic_progress", True)
            row["phase"] = "kernel_input_token_complete"
            row["token"] = token
            row["beat"] = 1
            rows.append(row)
        output_start = event(6, 1000, "semantic_progress", True)
        output_start["phase"] = "kernel_output_token_start"
        output_start["token"] = 0
        output_start["active_boundary_observation"] = {
            "output_accept_count": 0,
            "output_ready": 1,
            "output_valid": 1,
            "output_payload_unknown": False,
            "output_payload_digest": "a",
        }
        output_complete = event(7, 1100, "semantic_progress", True)
        output_complete["phase"] = "kernel_output_token_complete"
        output_complete["token"] = 0
        output_complete["beat"] = 1
        output_complete["active_boundary_observation"] = {
            "output_accept_count": 1,
            "output_ready": 1,
            "output_valid": 1,
            "output_payload_unknown": False,
            "output_payload_digest": "b",
        }
        rows.extend((output_start, output_complete))
        prefetch_complete = event(8, 3000, "semantic_progress", True)
        prefetch_complete["phase"] = "weight_prefetch_complete"
        prefetch_complete["active_boundary_observation"] = {
            "output_accept_count": 1,
            "output_ready": 1,
        }
        prefetch_complete["prefetch_progress"] = {
            "accepted_beats": 100,
            "target_beats": 100,
        }
        rows.append(prefetch_complete)
        for offset in range(8):
            row = event(9 + offset, 7500 + offset * 100, "stall_snapshot", False)
            row["phase"] = "bounded_deep_trace"
            row["active_boundary_observation"] = {
                "output_accept_count": 1,
                "output_ready": 1,
                "output_valid": 0,
                "output_payload_unknown": True,
                "output_payload_digest": "x",
            }
            row["prefetch_progress"] = {
                "accepted_beats": offset,
                "target_beats": 100,
            }
            row["prefetch_progress"]["accepted_beats"] = 100
            rows.append(row)
        contract = {
            "schema_version": "spatialaccagent.cctg_progress_budget_contract.v1",
            "target_input_beats": 8,
            "target_output_beats": 8,
            "single_layer_cycles": 100,
            "certificate_sha256": "a" * 64,
            "single_layer_stats_sha256": "b" * 64,
        }
        for row in rows:
            row["last_semantic_progress_cycle"] = 3000
        return rows, contract

    def test_partial_tail_is_not_committed_or_reported_as_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.jsonl"
            first = event(0, 10, "semantic_progress", True)
            path.write_bytes(
                (json.dumps(first) + "\n" + '{"schema_version":').encode("utf-8")
            )
            parsed = read_complete_jsonl(path)

        self.assertEqual(parsed["records"], [first])
        self.assertFalse(parsed["invalid_records"])
        self.assertGreater(parsed["trailing_partial_byte_count"], 0)

    def test_heartbeat_does_not_advance_semantic_progress(self) -> None:
        summary = summarize_progress_events(
            [
                event(0, 10, "semantic_progress", True),
                event(1, 100, "heartbeat", False),
            ]
        )

        self.assertEqual(summary["semantic_progress_event_count"], 1)
        self.assertEqual(summary["heartbeat_event_count"], 1)
        self.assertEqual(summary["last_semantic_progress_cycle"], 10)
        self.assertEqual(summary["silent_cycles"], 90)
        self.assertEqual(summary["status"], "observing")
        self.assertFalse(summary["validation_errors"])

    def test_wall_time_is_never_used_to_classify_a_stall(self) -> None:
        summary = summarize_progress_events(
            [event(0, 1_000_000, "heartbeat", False)]
        )

        self.assertEqual(summary["status"], "observing")
        self.assertTrue(
            summary["policy"]["wall_clock_elapsed_never_classifies_a_hardware_stall"]
        )

    def test_input_drain_with_zero_ready_output_proves_pipeline_violation(self) -> None:
        rows = []
        for token, cycle in enumerate((100, 200, 300, 400)):
            row = event(token, cycle, "semantic_progress", True)
            row["phase"] = "kernel_input_token_complete"
            row["token"] = token
            row["beat"] = 1
            row["active_boundary_observation"] = {
                "output_accept_count": 0,
                "output_ready": 1,
            }
            rows.append(row)
        contract = {
            "target_input_beats": 8,
            "target_output_beats": 8,
            "intra_layer_pipeline_contract": {
                "required": True,
                "first_output_no_later_than_final_input": True,
            },
        }

        evidence = intra_layer_pipeline_violation_evidence(rows, contract)

        self.assertEqual(evidence["status"], "proven_pipeline_violation")
        self.assertEqual(evidence["completed_input_tokens"], 4)
        self.assertEqual(evidence["observed_output_beats"], 0)
        self.assertEqual(evidence["final_input_cycle"], 400)

    def test_pipeline_violation_enters_existing_semantic_repair_path(self) -> None:
        rows = []
        for token, cycle in enumerate((100, 200, 300, 400)):
            row = event(token, cycle, "semantic_progress", True)
            row["phase"] = "kernel_input_token_complete"
            row["token"] = token
            row["beat"] = 1
            row["last_semantic_progress_cycle"] = cycle
            row["active_boundary_observation"] = {
                "output_accept_count": 0,
                "output_ready": 1,
            }
            rows.append(row)
        contract = {
            "target_input_beats": 8,
            "target_output_beats": 8,
            "intra_layer_pipeline_contract": {
                "required": True,
                "first_output_no_later_than_final_input": True,
            },
        }

        evidence = adaptive_semantic_stall_evidence(rows, contract)

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["proof_mode"], "intra_layer_pipeline_contract")
        self.assertEqual(
            evidence["failure_class"], "intra_layer_spatial_pipeline_violation"
        )
        self.assertEqual(
            evidence["intra_layer_pipeline_violation_evidence"]["status"],
            "proven_pipeline_violation",
        )
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertFalse(evidence["fixed_cycle_timeout"])

    def test_output_before_final_input_does_not_prove_pipeline_violation(self) -> None:
        rows = []
        for token, cycle in enumerate((100, 200, 300, 400)):
            row = event(token, cycle, "semantic_progress", True)
            row["phase"] = "kernel_input_token_complete"
            row["token"] = token
            row["beat"] = 1
            row["active_boundary_observation"] = {
                "output_accept_count": int(token >= 2),
                "output_ready": 1,
            }
            rows.append(row)
        output = event(5, 350, "semantic_progress", True)
        output["phase"] = "kernel_output_token_start"
        output["active_boundary_observation"] = {
            "output_accept_count": 1,
            "output_ready": 1,
        }
        rows.append(output)
        rows.sort(key=lambda row: row["cycle"])
        contract = {
            "target_input_beats": 8,
            "target_output_beats": 8,
            "intra_layer_pipeline_contract": {
                "required": True,
                "first_output_no_later_than_final_input": True,
            },
        }

        evidence = intra_layer_pipeline_violation_evidence(rows, contract)

        self.assertEqual(
            evidence["status"], "contract_not_violated_by_this_observation"
        )

    def test_adaptive_stall_requires_stable_state_beyond_observed_work_bound(self) -> None:
        rows = []
        for sequence, cycle in enumerate((100, 200, 400)):
            row = event(sequence, cycle, "semantic_progress", True)
            row["progress_epoch"] = sequence + 1
            row["last_semantic_progress_cycle"] = cycle
            rows.append(row)
        for offset, cycle in enumerate((500, 1500, 2500, 3500, 4500, 5500, 6500, 7000), start=3):
            row = event(offset, cycle, "stall_snapshot", False)
            row["progress_epoch"] = 3
            row["last_semantic_progress_cycle"] = 400
            rows.append(row)

        evidence = adaptive_semantic_stall_evidence(rows)

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["adaptive_silent_cycle_bound"], 6400)
        self.assertGreaterEqual(evidence["stable_state_cycles"], 6400)
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertFalse(evidence["fixed_cycle_timeout"])

    def test_adaptive_stall_uses_one_observed_semantic_gap(self) -> None:
        rows = []
        for sequence, cycle in enumerate((100, 400)):
            row = event(sequence, cycle, "semantic_progress", True)
            row["progress_epoch"] = sequence + 1
            row["last_semantic_progress_cycle"] = cycle
            rows.append(row)
        for offset, cycle in enumerate(
            (500, 2_000, 3_500, 5_000, 6_500, 8_000, 9_500, 11_000),
            start=2,
        ):
            row = event(offset, cycle, "stall_snapshot", False)
            row["progress_epoch"] = 2
            row["last_semantic_progress_cycle"] = 400
            rows.append(row)

        evidence = adaptive_semantic_stall_evidence(rows)

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["semantic_event_count"], 2)
        self.assertEqual(evidence["max_observed_semantic_gap"], 300)
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertFalse(evidence["fixed_cycle_timeout"])

    def test_adaptive_stall_rejects_a_new_cumulative_axi_transfer(self) -> None:
        rows = []
        for sequence, cycle in enumerate((100, 200, 400)):
            row = event(sequence, cycle, "semantic_progress", True)
            row["progress_epoch"] = sequence + 1
            row["last_semantic_progress_cycle"] = cycle
            rows.append(row)
        for offset, cycle in enumerate((500, 1500, 2500, 3500, 4500, 5500, 6500, 7000), start=3):
            row = event(offset, cycle, "stall_snapshot", False)
            row["progress_epoch"] = 3
            row["last_semantic_progress_cycle"] = 400
            rows.append(row)
        rows[-1]["axi_read"]["accepted"] = 2

        evidence = adaptive_semantic_stall_evidence(rows)

        self.assertEqual(evidence["status"], "observing")
        self.assertEqual(evidence["stable_state_cycles"], 0)

    def test_cctg_frontier_budget_ignores_independent_prefetch_progress(self) -> None:
        rows, contract = self.cctg_frontier_rows()

        evidence = adaptive_semantic_stall_evidence(rows, contract)

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["proof_mode"], "cctg_frontier")
        frontier = evidence["cctg_frontier_stall_evidence"]
        self.assertEqual(frontier["status"], "proven_frontier_stall")
        self.assertEqual(frontier["observed_output_beats"], 1)
        self.assertEqual(frontier["adaptive_frontier_cycle_bound"], 3200)

    def test_cctg_zero_output_frontier_localizes_input_to_output_stall(self) -> None:
        rows, contract = self.cctg_frontier_rows()
        for row in rows:
            active = row.get("active_boundary_observation")
            active = active if isinstance(active, dict) else {}
            active["output_accept_count"] = 0
            active.setdefault("output_ready", 1)
            row["active_boundary_observation"] = active

        evidence = adaptive_semantic_stall_evidence(rows, contract)

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["proof_mode"], "cctg_frontier")
        frontier = evidence["cctg_frontier_stall_evidence"]
        self.assertEqual(frontier["status"], "proven_frontier_stall")
        self.assertEqual(frontier["frontier_id"], "connected_kernel_input_to_output")
        self.assertEqual(frontier["frontier_type"], "zero_output_input_to_output")
        self.assertEqual(frontier["observed_output_beats"], 0)
        self.assertIsNone(frontier["first_output_frontier_cycle"])
        self.assertEqual(frontier["adaptive_frontier_cycle_bound"], 3200)

    def test_cctg_continuation_budget_excludes_pre_output_startup_latency(self) -> None:
        rows, contract = self.cctg_frontier_rows()
        for row in rows[:6]:
            row["active_boundary_observation"] = {
                "output_accept_count": 0,
                "output_ready": 1,
            }
        rows[0]["cycle"] = 10
        rows[1]["cycle"] = 20
        rows[2]["cycle"] = 30
        rows[3]["cycle"] = 40
        rows[4]["cycle"] = 50
        rows[5]["cycle"] = 60
        rows[6]["cycle"] = 50_000
        rows[7]["cycle"] = 50_100
        rows[8]["cycle"] = 53_300
        for index, row in enumerate(rows[9:], start=0):
            row["cycle"] = 57_000 + index * 100
        for row in rows:
            row["last_semantic_progress_cycle"] = 53_300

        evidence = adaptive_semantic_stall_evidence(rows, contract)
        frontier = evidence["cctg_frontier_stall_evidence"]

        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(frontier["adaptive_frontier_cycle_bound"], 3200)
        self.assertEqual(frontier["first_output_frontier_cycle"], 50_000)
        self.assertEqual(frontier["startup_latency_cycles"], 49_980)
        self.assertTrue(
            frontier["startup_latency_excluded_from_continuation_budget"]
        )

    def test_cctg_frontier_budget_does_not_classify_backpressure_as_stall(self) -> None:
        rows, contract = self.cctg_frontier_rows()
        rows[-1]["active_boundary_observation"]["output_ready"] = 0

        evidence = adaptive_semantic_stall_evidence(rows, contract)

        self.assertNotEqual(evidence["status"], "proven_semantic_stall")
        self.assertNotEqual(
            evidence["cctg_frontier_stall_evidence"]["status"],
            "proven_frontier_stall",
        )

    def test_cctg_frontier_requires_hash_bound_lower_certificate(self) -> None:
        rows, contract = self.cctg_frontier_rows()
        contract.pop("certificate_sha256")

        evidence = adaptive_semantic_stall_evidence(rows, contract)

        self.assertNotEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(
            evidence["cctg_frontier_stall_evidence"]["status"],
            "unavailable",
        )


if __name__ == "__main__":
    unittest.main()
