import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.verification.case_single_layer_stream_sim import (
    SingleLayerPipelineProgressObserver,
    cctg_boundary_replay_evidence,
    pipeline_overlap_evidence,
)
from scripts.verification.semantic_testbench_generator import (
    single_layer_pipeline_overlap_contract,
)


class SingleLayerPipelineContractTest(TestCase):
    def test_v3_classifies_transitive_bypass_as_diagnostic(self) -> None:
        def edge(edge_id: str, src: str, dst: str, kind: str = "main") -> dict:
            return {
                "edge_id": edge_id,
                "src_stage": src,
                "dst_stage": dst,
                "kind": kind,
                "flow_control": "ready_valid",
                "stream_contract": {
                    "transfer_count_elements": 8,
                    "element_bits": 16,
                    "stream_beat_bits": 32,
                },
            }

        pipeline = {
            "stages": [
                {"stage_id": "stage_0"},
                {"stage_id": "stage_1"},
                {"stage_id": "stage_2"},
            ],
            "stream_edges": [
                edge("edge.input", "block_input", "stage_0"),
                edge("edge.0_to_1", "stage_0", "stage_1"),
                edge("edge.0_to_1.operand_b", "stage_0", "stage_1", "operand_b"),
                edge("edge.1_to_2", "stage_1", "stage_2"),
                edge("edge.0_to_2.skip", "stage_0", "stage_2", "residual_skip"),
                edge("edge.output", "stage_2", "block_output"),
            ],
        }

        contract = single_layer_pipeline_overlap_contract(
            {"tensor_shape": [2, 4], "lanes": 2},
            pipeline,
            "pipeline-plan-sha256",
        )

        self.assertEqual(
            contract["schema_version"],
            "spatialaccagent.single_layer_pipeline_overlap_contract.v3",
        )
        dependencies = {
            row["boundary_id"]: row for row in contract["dependency_edges"]
        }
        self.assertEqual(
            dependencies["edge.0_to_2.skip"]["overlap_requirement"],
            "diagnostic",
        )
        self.assertEqual(
            dependencies["edge.0_to_2.skip"]["relationship"],
            "transitive_bypass",
        )
        self.assertTrue(
            all(
                dependencies[edge_id]["overlap_requirement"] == "required"
                for edge_id in (
                    "edge.0_to_1",
                    "edge.0_to_1.operand_b",
                    "edge.1_to_2",
                )
            )
        )
        self.assertTrue(contract["acceptance"]["stage_turnover_gaps_are_diagnostic"])
        self.assertFalse(
            contract["acceptance"][
                "all_planned_stages_same_cycle_concurrency_required"
            ]
        )
        self.assertEqual(len(contract["compatible_trace_contract_sha256s"]), 2)


class SingleLayerPipelineOverlapEvidenceTest(TestCase):
    def _section(self) -> dict:
        return {
            "pipeline_overlap_contract": {
                "schema_version": "spatialaccagent.single_layer_pipeline_overlap_contract.v2",
                "contract_sha256": "test-contract-sha256",
                "token_count": 2,
                "beats_per_token": 2,
                "stage_order": ["stage_0", "stage_1"],
                "required_boundaries": [
                    "edge.input",
                    "edge.stage_0_to_stage_1",
                    "edge.output",
                ],
                "boundary_contracts": [
                    {
                        "boundary_id": "edge.input",
                        "src_stage": "block_input",
                        "dst_stage": "stage_0",
                        "beats_per_token": 2,
                    },
                    {
                        "boundary_id": "edge.stage_0_to_stage_1",
                        "src_stage": "stage_0",
                        "dst_stage": "stage_1",
                        "beats_per_token": 2,
                    },
                    {
                        "boundary_id": "edge.output",
                        "src_stage": "stage_1",
                        "dst_stage": "block_output",
                        "beats_per_token": 2,
                    },
                ],
                "stage_activity_contracts": [
                    {
                        "stage_id": "stage_0",
                        "input_boundaries": ["edge.input"],
                        "output_boundaries": ["edge.stage_0_to_stage_1"],
                    },
                    {
                        "stage_id": "stage_1",
                        "input_boundaries": ["edge.stage_0_to_stage_1"],
                        "output_boundaries": ["edge.output"],
                    },
                ],
                "dependency_edges": [
                    {
                        "boundary_id": "edge.stage_0_to_stage_1",
                        "src_stage": "stage_0",
                        "dst_stage": "stage_1",
                    }
                ],
                "block_output_boundary": "edge.output",
                "acceptance": {
                    "maximum_next_token_stage_entry_gap_cycles": 1,
                    "minimum_concurrent_stage_count": 2,
                },
            }
        }

    def _v3_section(self) -> dict:
        section = copy.deepcopy(self._section())
        contract = section["pipeline_overlap_contract"]
        contract["schema_version"] = (
            "spatialaccagent.single_layer_pipeline_overlap_contract.v3"
        )
        contract["pipeline_semantics"] = "elastic_rate_insensitive_token_pipeline"
        contract["required_dependency_count"] = 1
        contract["dependency_edges"][0].update(
            {
                "relationship": "direct_dataflow",
                "overlap_requirement": "required",
            }
        )
        contract["acceptance"] = {
            "token_order_is_preserved_at_every_required_boundary": True,
            "every_stage_emits_token_0_before_accepting_the_final_token": True,
            "every_required_dependency_overlaps_on_different_tokens": True,
            "every_planned_stage_participates_in_required_overlap": True,
            "minimum_concurrent_stage_count": 2,
            "stage_turnover_gaps_are_diagnostic": True,
            "all_planned_stages_same_cycle_concurrency_required": False,
            "whole_sequence_barrier_forbidden": True,
        }
        return section

    @staticmethod
    def _trace(boundary: str, token: int, first_cycle: int, last_cycle: int) -> list[str]:
        boundary = {
            "block_input": "edge.input",
            "stage_0_output": "edge.stage_0_to_stage_1",
            "block_output": "edge.output",
        }.get(boundary, boundary)
        return [
            (
                f"SPATIALACC_PIPELINE_TRACE boundary={boundary} cycle={first_cycle} "
                f"token={token} beat=0 st=1 last=0 valid=1 ready=1"
            ),
            (
                f"SPATIALACC_PIPELINE_TRACE boundary={boundary} cycle={last_cycle} "
                f"token={token} beat=1 st=0 last=1 valid=1 ready=1"
            ),
        ]

    def _evaluate(
        self,
        lines: list[str],
        *,
        output_lines: int = 4,
        pass_beats: int = 4,
        run_status: str = "pass",
        returncode: int = 0,
    ) -> dict:
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            sim_log.write_text(
                "\n".join(
                    [
                        *lines,
                        f"PASS semantic harness real-weight execution beats={pass_beats} cycles=123",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            output = Path(temp_dir) / "rtl_output.memh"
            output.write_text("00000000\n" * output_lines, encoding="ascii")
            return pipeline_overlap_evidence(
                {
                    "status": "pass",
                    "run": {"status": run_status, "returncode": returncode},
                    "sim_log": str(sim_log),
                    "output_capture": str(output),
                },
                self._section(),
            )

    def _evaluate_v3(
        self,
        lines: list[str],
        *,
        section: dict | None = None,
        output_lines: int = 4,
        pass_beats: int = 4,
    ) -> dict:
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            sim_log.write_text(
                "\n".join(
                    [
                        *lines,
                        f"PASS semantic harness real-weight execution beats={pass_beats} cycles=123",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            output = Path(temp_dir) / "rtl_output.memh"
            output.write_text("00000000\n" * output_lines, encoding="ascii")
            return pipeline_overlap_evidence(
                {
                    "status": "pass",
                    "run": {"status": "pass", "returncode": 0},
                    "sim_log": str(sim_log),
                    "output_capture": str(output),
                },
                section or self._v3_section(),
            )

    def test_immediate_next_token_overlap_passes(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        lines += self._trace("stage_0_output", 1, 17, 18)
        lines += self._trace("block_output", 0, 15, 16)
        lines += self._trace("block_output", 1, 25, 26)

        evidence = self._evaluate(lines)

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["blockers"], [])
        self.assertEqual(len(evidence["transition_evidence"]), 1)
        self.assertTrue(evidence["transition_evidence"][0]["overlapped"])
        self.assertEqual(evidence["transition_evidence"][0]["gap_cycles"], 1)
        self.assertFalse(evidence["terminal_trace_flush_inferred"])

    def test_v3_heterogeneous_stage_gaps_are_diagnostic(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 30, 31)
        lines += self._trace("stage_0_output", 1, 60, 61)
        lines += self._trace("block_output", 0, 50, 51)
        lines += self._trace("block_output", 1, 100, 101)

        evidence = self._evaluate_v3(lines)

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["blockers"], [])
        self.assertTrue(evidence["stage_turnover_gaps_are_diagnostic"])
        self.assertTrue(
            any(row["idle_cycles"] > 0 for row in evidence["stage_turnover_evidence"])
        )
        self.assertTrue(evidence["required_dependency_overlap_complete"])
        self.assertTrue(
            evidence["all_planned_stages_participate_in_required_overlap"]
        )

    def test_v3_serial_cross_stage_execution_still_fails(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_output", 0, 40, 50)
        lines += self._trace("block_input", 1, 60, 61)
        lines += self._trace("stage_0_output", 1, 100, 101)
        lines += self._trace("block_output", 1, 120, 121)

        evidence = self._evaluate_v3(lines)

        self.assertEqual(evidence["status"], "fail")
        self.assertFalse(evidence["required_dependency_overlap_complete"])
        self.assertTrue(
            any("required dataflow stages" in item for item in evidence["blockers"])
        )

    def test_v3_diagnostic_dependency_does_not_authorize_failure(self) -> None:
        section = self._v3_section()
        contract = section["pipeline_overlap_contract"]
        contract["dependency_edges"].append(
            {
                "boundary_id": "edge.diagnostic_stage_0_turnover",
                "src_stage": "stage_0",
                "dst_stage": "stage_0",
                "relationship": "diagnostic_only",
                "overlap_requirement": "diagnostic",
            }
        )
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 30, 31)
        lines += self._trace("stage_0_output", 1, 60, 61)
        lines += self._trace("block_output", 0, 50, 51)
        lines += self._trace("block_output", 1, 100, 101)

        evidence = self._evaluate_v3(lines, section=section)

        self.assertEqual(evidence["status"], "pass")
        diagnostic = next(
            row
            for row in evidence["dependency_overlap_evidence"]
            if row["overlap_requirement"] == "diagnostic"
        )
        self.assertFalse(
            diagnostic["different_token_overlap_observed"]
        )
        self.assertFalse(diagnostic["required_for_acceptance"])

    def test_padded_numeric_trace_fields_are_parsed(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        lines += self._trace("stage_0_output", 1, 17, 18)
        lines += self._trace("block_output", 0, 15, 16)
        lines += self._trace("block_output", 1, 25, 26)
        padded = [
            line.replace("cycle=", "cycle=        ")
            .replace("token=", "token=  ")
            .replace("beat=", "beat=   ")
            .replace("st=", "st= ")
            .replace("last=", "last= ")
            .replace("valid=", "valid= ")
            .replace("ready=", "ready= ")
            for line in lines
        ]

        evidence = self._evaluate(padded)

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["trace_record_count"], 12)

    def test_only_terminal_block_output_flush_may_be_inferred(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        lines += self._trace("stage_0_output", 1, 17, 18)
        lines += self._trace("block_output", 0, 15, 16)
        lines += self._trace("block_output", 1, 25, 26)[:1]

        evidence = self._evaluate(lines)

        self.assertEqual(evidence["status"], "pass")
        self.assertTrue(evidence["terminal_trace_flush_inferred"])
        flush = evidence["terminal_trace_flush_evidence"]
        self.assertTrue(flush["inferred"])
        self.assertEqual(
            flush["missing_required_trace_positions"],
            [{"boundary": "edge.output", "token": 1, "beat": 1}],
        )

    def test_terminal_flush_inference_requires_exact_output_and_pass_counts(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        lines += self._trace("stage_0_output", 1, 17, 18)
        lines += self._trace("block_output", 0, 15, 16)
        lines += self._trace("block_output", 1, 25, 26)[:1]

        wrong_output = self._evaluate(lines, output_lines=3)
        wrong_pass = self._evaluate(lines, pass_beats=3)
        failed_exit = self._evaluate(lines, run_status="fail", returncode=1)

        self.assertEqual(wrong_output["status"], "fail")
        self.assertFalse(wrong_output["terminal_trace_flush_inferred"])
        self.assertFalse(
            wrong_output["terminal_trace_flush_evidence"]["checks"]["output_line_count_matches"]
        )
        self.assertEqual(wrong_pass["status"], "fail")
        self.assertFalse(wrong_pass["terminal_trace_flush_inferred"])
        self.assertFalse(
            wrong_pass["terminal_trace_flush_evidence"]["checks"]["single_matching_sim_pass_declaration"]
        )
        self.assertEqual(failed_exit["status"], "fail")
        self.assertFalse(failed_exit["terminal_trace_flush_inferred"])
        self.assertFalse(
            failed_exit["terminal_trace_flush_evidence"]["checks"]["remote_exit_status_pass"]
        )

    def test_nonterminal_or_additional_trace_gap_is_not_inferred(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        lines += self._trace("stage_0_output", 1, 17, 18)[:1]
        lines += self._trace("block_output", 0, 15, 16)
        lines += self._trace("block_output", 1, 25, 26)[:1]

        evidence = self._evaluate(lines)

        self.assertEqual(evidence["status"], "fail")
        self.assertFalse(evidence["terminal_trace_flush_inferred"])
        self.assertEqual(
            len(evidence["terminal_trace_flush_evidence"]["missing_required_trace_positions"]),
            2,
        )

    def test_malformed_terminal_trace_is_not_treated_as_an_unflushed_trace(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        lines += self._trace("stage_0_output", 1, 17, 18)
        lines += self._trace("block_output", 0, 15, 16)
        lines += self._trace("block_output", 1, 25, 26)[:1]
        lines.append(
            "SPATIALACC_PIPELINE_TRACE boundary=edge.output cycle=26 "
            "token=1 beat=1 st=0 last=1 valid=x ready=1"
        )

        evidence = self._evaluate(lines)

        self.assertEqual(evidence["status"], "fail")
        self.assertFalse(evidence["terminal_trace_flush_inferred"])
        self.assertEqual(
            evidence["terminal_trace_flush_evidence"]["unparsed_pipeline_trace_line_count"],
            1,
        )

    def test_next_token_after_prior_block_output_fails(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_output", 0, 100, 101)
        lines += self._trace("block_input", 1, 102, 103)
        lines += self._trace("stage_0_output", 1, 110, 111)
        lines += self._trace("block_output", 1, 200, 201)

        evidence = self._evaluate(lines)

        self.assertEqual(evidence["status"], "fail")
        self.assertFalse(evidence["transition_evidence"][0]["overlapped"])
        self.assertTrue(any("stage stage_0 left" in item for item in evidence["blockers"]))

    def test_missing_trace_fails(self) -> None:
        evidence = self._evaluate([])

        self.assertEqual(evidence["status"], "fail")
        self.assertEqual(evidence["trace_record_count"], 0)
        self.assertTrue(any("does not contain exactly one first/last" in item for item in evidence["blockers"]))
        self.assertTrue(
            any(
                "pipeline trace does not cover every adjacent-token turnover" in item
                for item in evidence["blockers"]
            )
        )

    def test_cctg_replay_requires_fresh_remote_vcs_but_preserves_frontier(self) -> None:
        lines = []
        lines += self._trace("block_input", 0, 1, 2)
        lines += self._trace("stage_0_output", 0, 10, 11)
        lines += self._trace("block_input", 1, 12, 13)
        # The first CCTG frontier is intentionally incomplete: the producer
        # must give this to the LLM rather than discard it as a failed replay.
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sim_log = root / "sim.log"
            sim_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            execution = {
                "status": "pass",
                "simulator": "vcs",
                "tool_scope": "remote",
                "fresh_remote_vcs_execution_required": True,
                "remote_job_reuse": {"real_tool_was_not_relaunched": False},
                "run": {"status": "pass"},
                "sim_log": str(sim_log),
                "remote_workdir": "/remote/fresh-cctg",
            }
            evidence = cctg_boundary_replay_evidence(execution, self._section())
            cached = cctg_boundary_replay_evidence(
                {
                    **execution,
                    "remote_job_reuse": {"real_tool_was_not_relaunched": True},
                },
                self._section(),
            )

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["boundary_liveness_status"], "fail")
        self.assertEqual(evidence["first_incomplete_boundary"], "edge.stage_0_to_stage_1")
        self.assertTrue(evidence["fresh_remote_vcs_execution_observed"])
        self.assertEqual(cached["status"], "fail")
        self.assertTrue(
            any("fresh completed remote VCS" in item for item in cached["blockers"])
        )

    def test_cctg_replay_accepts_complete_endpoint_coverage(self) -> None:
        section = copy.deepcopy(self._section())
        for boundary in section["pipeline_overlap_contract"]["boundary_contracts"]:
            boundary["beats_per_token"] = 4
        lines = []
        for boundary in section["pipeline_overlap_contract"]["required_boundaries"]:
            for token in range(2):
                lines.extend(
                    [
                        (
                            f"SPATIALACC_PIPELINE_TRACE boundary={boundary} "
                            f"cycle={token * 10 + 1} token={token} beat=0 "
                            "st=1 last=0 valid=1 ready=1"
                        ),
                        (
                            f"SPATIALACC_PIPELINE_TRACE boundary={boundary} "
                            f"cycle={token * 10 + 4} token={token} beat=3 "
                            "st=0 last=1 valid=1 ready=1"
                        ),
                    ]
                )
        with TemporaryDirectory() as temp_dir:
            sim_log = Path(temp_dir) / "sim.log"
            sim_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            evidence = cctg_boundary_replay_evidence(
                {
                    "status": "pass",
                    "simulator": "vcs",
                    "tool_scope": "remote",
                    "fresh_remote_vcs_execution_required": True,
                    "remote_job_reuse": {"real_tool_was_not_relaunched": False},
                    "run": {"status": "pass"},
                    "sim_log": str(sim_log),
                    "remote_workdir": "/remote/fresh-cctg",
                },
                section,
            )

        self.assertEqual(evidence["status"], "pass")
        self.assertEqual(evidence["boundary_liveness_status"], "pass")
        for boundary in evidence["boundary_records"]:
            self.assertEqual(boundary["status"], "pass")
            self.assertEqual(boundary["accepted_trace_observation_count"], 4)
            self.assertEqual(
                boundary["expected_endpoint_trace_observation_count"], 4
            )
            self.assertEqual(boundary["expected_data_beat_count"], 8)
            self.assertEqual(boundary["missing_first_token_ids"], [])
            self.assertEqual(boundary["missing_terminal_token_ids"], [])

    def test_live_observer_closes_only_an_irreversible_whole_sequence_barrier(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            observer = SingleLayerPipelineProgressObserver(root, self._section())
            observer.fingerprint = "f" * 64
            lines = [
                *self._trace("stage_0_output", 1, 90, 100),
                self._trace("block_output", 0, 101, 102)[0],
            ]
            observer(
                {
                    "state": "running",
                    "pid": 7,
                    "poll_attempt": 1,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "progress_log_tail": "\n".join(lines),
                }
            )
            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))

        evidence = snapshot["adaptive_semantic_stall_evidence"]
        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(
            evidence["failure_class"], "intra_layer_spatial_pipeline_violation"
        )
        self.assertEqual(
            evidence["whole_sequence_barrier_evidence"][0]["stage_id"],
            "stage_1",
        )
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertFalse(evidence["fixed_cycle_timeout"])

    def test_live_observer_closes_an_irreversible_stage_turnover_gap(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            observer = SingleLayerPipelineProgressObserver(root, self._section())
            observer.fingerprint = "f" * 64
            lines = [
                *self._trace("block_input", 0, 1, 2),
                *self._trace("stage_0_output", 0, 10, 11),
                *self._trace("block_input", 1, 20, 21),
            ]
            observer(
                {
                    "state": "running",
                    "pid": 7,
                    "poll_attempt": 1,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "progress_log_tail": "\n".join(lines),
                }
            )
            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))

        evidence = snapshot["adaptive_semantic_stall_evidence"]
        aggregate = self._evaluate(
            lines,
            output_lines=0,
            pass_beats=0,
            run_status="fail",
            returncode=86,
        )
        self.assertEqual(snapshot["status"], "fail")
        self.assertEqual(evidence["status"], "proven_semantic_stall")
        self.assertEqual(evidence["irreversible_violation_kind"], "stage_turnover")
        self.assertEqual(evidence["candidate_stage_ids"], ["stage_0", "stage_1"])
        self.assertEqual(
            evidence["failed_stage_turnover_evidence"],
            [
                {
                    "stage_id": "stage_0",
                    "prior_token": 0,
                    "next_token": 1,
                    "prior_token_active_end_cycle": 11,
                    "next_token_active_start_cycle": 20,
                    "gap_cycles": 9,
                    "keeps_pipeline_filled": False,
                    "overlapped": False,
                }
            ],
        )
        self.assertFalse(evidence["fixed_wall_clock_timeout"])
        self.assertFalse(evidence["fixed_cycle_timeout"])
        self.assertEqual(
            aggregate["irreversible_stage_turnover_evidence"]
            ["failed_stage_turnover_evidence"],
            evidence["failed_stage_turnover_evidence"],
        )

    def test_v3_live_observer_keeps_heterogeneous_turnover_gap_running(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            observer = SingleLayerPipelineProgressObserver(root, self._v3_section())
            lines = [
                *self._trace("block_input", 0, 1, 2),
                *self._trace("stage_0_output", 0, 10, 11),
                *self._trace("block_input", 1, 20, 21),
            ]
            observer(
                {
                    "state": "running",
                    "pid": 7,
                    "poll_attempt": 1,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "progress_log_tail": "\n".join(lines),
                }
            )
            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))

        evidence = snapshot["adaptive_semantic_stall_evidence"]
        self.assertEqual(snapshot["status"], "observing")
        self.assertEqual(evidence["status"], "observing")
        self.assertNotIn("irreversible_violation_kind", evidence)

    def test_live_observer_does_not_close_a_barrier_free_partial_trace(self) -> None:
        with TemporaryDirectory() as temp_dir:
            observer = SingleLayerPipelineProgressObserver(
                Path(temp_dir), self._section()
            )
            lines = [
                self._trace("block_output", 0, 50, 51)[0],
                *self._trace("stage_0_output", 1, 90, 100),
            ]
            observer(
                {
                    "state": "running",
                    "pid": 7,
                    "poll_attempt": 1,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "progress_log_tail": "\n".join(lines),
                }
            )
            snapshot = json.loads(observer.snapshot_path.read_text(encoding="utf-8"))

        self.assertEqual(snapshot["status"], "observing")
        self.assertEqual(
            snapshot["adaptive_semantic_stall_evidence"]["status"], "observing"
        )
