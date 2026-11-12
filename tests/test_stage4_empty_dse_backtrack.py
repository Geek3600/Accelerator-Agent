import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.sacg_store import SACGStore
from accagent.framework.stage_params import (
    close_resolved_empty_dse_backtracks,
    record_empty_dse_eligibility_backtrack,
    write_empty_dse_failure_report,
)


def _constraint_report(candidate_count: int, blocked_count: int) -> dict:
    return {
        "status": "fail",
        "candidate_count": candidate_count,
        "feasible_candidate_count": 0,
        "policy": {
            "candidate_universe_is_complete_and_unsampled": True,
            "deterministic_evaluator_enforces_hard_constraints": True,
        },
        "infeasible_candidates": [
            {"candidate_id": f"arch_{index}", "hard_constraint_errors": ["schedule contract is infeasible"]}
            for index in range(blocked_count)
        ],
    }


def _store(tmp_path: Path) -> SACGStore:
    state_path = tmp_path / "sacg_state.json"
    state_path.write_text(json.dumps({"design_id": "test"}), encoding="utf-8")
    return SACGStore(state_path)


class EmptyDseBacktrackTest(unittest.TestCase):
    def test_complete_empty_legal_set_records_pipeline_replan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            store = _store(tmp_path)
            request = record_empty_dse_eligibility_backtrack(
                store,
                _constraint_report(2, 2),
                constraint_report_path=tmp_path / "dse_constraint_report.json",
                candidate_records_path=tmp_path / "dse_candidate_records.jsonl",
            )

            self.assertIsNotNone(request)
            assert request is not None
            self.assertEqual(request["stage"], "stage4.parameter_binding")
            self.assertEqual(request["target_stage"], "stage3.pipeline_planning")
            self.assertEqual(request["verification_scope"], "formal_dse_campaign")
            self.assertEqual(
                request["evidence"],
                [
                    str(tmp_path / "dse_constraint_report.json"),
                    str(tmp_path / "dse_candidate_records.jsonl"),
                ],
            )
            self.assertEqual(request["status"], "open")

    def test_incomplete_candidate_projection_does_not_backtrack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            store = _store(tmp_path)

            request = record_empty_dse_eligibility_backtrack(
                store,
                _constraint_report(2, 1),
                constraint_report_path=tmp_path / "dse_constraint_report.json",
                candidate_records_path=tmp_path / "dse_candidate_records.jsonl",
            )

            self.assertIsNone(request)
            self.assertEqual(store.state["memory"]["backtrack_requests"], [])

    def test_stage4_candidate_binding_closes_only_matching_empty_dse_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            store = _store(tmp_path)
            request = record_empty_dse_eligibility_backtrack(
                store,
                _constraint_report(2, 2),
                constraint_report_path=tmp_path / "old_dse_constraint_report.json",
                candidate_records_path=tmp_path / "old_dse_candidate_records.jsonl",
            )
            assert request is not None
            unrelated = store.record_backtrack_request(
                stage="stage4.parameter_binding",
                target_stage="stage3.pipeline_planning",
                reason="unrelated pipeline contract remains open",
                evidence=["other-evidence.json"],
                context={"verification_scope": "single_layer_closure"},
            )

            closed = close_resolved_empty_dse_backtracks(
                store,
                transition_id="transition.stage4.current_run",
                selected_candidate_id="arch_current_run",
            )

        self.assertEqual(closed, 1)
        self.assertEqual(request["status"], "closed")
        self.assertEqual(request["closed_by_transition"], "transition.stage4.current_run")
        self.assertIn("arch_current_run", request["resolution_summary"])
        self.assertEqual(unrelated["status"], "open")

    def test_empty_universe_writes_failed_report_and_replan_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source_state = tmp_path / "pipeline_planning" / "sacg_state.json"
            source_state.parent.mkdir()
            source_state.write_text(json.dumps({"design_id": "test"}), encoding="utf-8")
            state_path = tmp_path / "parameter_binding" / "sacg_state.json"
            report_path = tmp_path / "parameter_binding" / "parameter_binding_report.json"
            report_path.parent.mkdir()
            constraint_path = tmp_path / "dse_constraint_report.json"
            candidate_path = tmp_path / "dse_candidate_records.jsonl"
            search_path = tmp_path / "dse_search_space.json"
            pareto_path = tmp_path / "dse_pareto_frontier.json"
            measurements_path = tmp_path / "dse_measurements.jsonl"

            _, report = write_empty_dse_failure_report(
                source_state=source_state,
                state_path=state_path,
                report_path=report_path,
                constraint_report=_constraint_report(2, 2),
                constraint_report_path=constraint_path,
                candidate_records_path=candidate_path,
                dse_search_path=search_path,
                dse_pareto_path=pareto_path,
                dse_measurements_path=measurements_path,
                llm={"result_path": tmp_path / "llm_result.json", "output": {"status": "blocked"}},
            )

            persisted = SACGStore(state_path).state
            self.assertEqual(report["status"], "incomplete")
            self.assertEqual(report["dse_constraint_summary"]["feasible_candidate_count"], 0)
            self.assertFalse(report["formal_dse_campaign"]["selected_candidate_requires_exact_measurement"])
            self.assertEqual(len(persisted["memory"]["backtrack_requests"]), 1)
            self.assertEqual(
                persisted["memory"]["backtrack_requests"][0]["target_stage"],
                "stage3.pipeline_planning",
            )
