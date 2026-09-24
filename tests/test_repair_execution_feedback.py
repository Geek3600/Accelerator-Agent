"""Current Stage-6 feedback semantics."""

from __future__ import annotations

import hashlib
import json
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from accagent.framework.stage_repair_execute import (
    capability_agent_consumed_materialization_feedback,
    current_repair_action_execution_frontier,
    mark_repair_action_execution_frontier_consumed,
    post_validation_materialization_feedback,
    repair_step_checkpoint,
    board_integration_prompt_rules,
    repair_loop_disposition,
    resume_prior_resource_failed_validation,
    run_repair_loop,
)


class RepairExecutionFeedbackTest(unittest.TestCase):
    def _post_validation_fixture(
        self,
        root: Path,
        *,
        materialization_status: str,
    ) -> tuple[Path, Path, dict[str, object]]:
        run_dir = root / "run"
        out_dir = run_dir / "repair_execution"
        source_path = run_dir / "generated" / "semantic_harness.txt"
        manifest_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
        requirements_path = (
            run_dir
            / "verification"
            / "semantic_testbench"
            / "dut_weight_binding_requirements.json"
        )
        for path in (out_dir, source_path.parent, manifest_path.parent, requirements_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        source_path.write_text("current harness source\n", encoding="utf-8")
        manifest_path.write_text('{"status": "incomplete"}\n', encoding="utf-8")
        requirements_path.write_text(
            '{"stage_requirements": [{"stage_id": "stage_00"}]}\n',
            encoding="utf-8",
        )
        step: dict[str, object] = {
            "id": "repair_step.00",
            "scope": "verification_capability_repair",
            "action": {
                "repair_kind": "semantic_loader_harness_binding",
                "violated_contract": "verification_capability_must_execute",
            },
        }
        (out_dir / "agent_patch_application.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "files": [
                        {
                            "path": str(source_path),
                            "after_sha256": hashlib.sha256(
                                source_path.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                    "repair_checkpoint": repair_step_checkpoint(step),
                }
            ),
            encoding="utf-8",
        )
        (out_dir / "agent_requested_validation.json").write_text(
            '{"status": "pass", "results": []}\n', encoding="utf-8"
        )
        blockers = (
            []
            if materialization_status == "pass"
            else ["stage_00: harness top does not declare required input valid port"]
        )
        (out_dir / "dut_weight_binding_materialization.json").write_text(
            json.dumps(
                {
                    "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                    "status": materialization_status,
                    "blockers": blockers,
                    "manifest": str(manifest_path),
                    "stage_harness_count": 0,
                    "single_layer_harness_materialized": False,
                }
            ),
            encoding="utf-8",
        )
        return run_dir, out_dir, step

    def _write_repair_action_disposition(
        self,
        run_dir: Path,
        step: dict[str, object],
        actions: list[dict[str, object]],
    ) -> None:
        repair_path = run_dir / "repair" / "repair_plan.json"
        repair_path.parent.mkdir(parents=True, exist_ok=True)
        repair_path.write_text(
            json.dumps(
                {
                    "repair_workflow": {
                        "status": "ready",
                        "steps": [{"id": step["id"]}],
                        "llm_disposition": {
                            "status": "ready",
                            "summary": "checker-bound current-layer repair",
                            "executable_actions": actions,
                            "approval_action_ids": [],
                            "active_approval_action_ids": [],
                            "deferred_approval_action_ids": [],
                        },
                    }
                }
            ),
            encoding="utf-8",
        )

    def _current_action_frontier(
        self,
        run_dir: Path,
        step: dict[str, object],
        *,
        summary: str = "reconcile current leaf evidence",
    ) -> dict[str, object]:
        self._write_repair_action_disposition(
            run_dir,
            step,
            [
                {
                    "id": "repair.current_leaf",
                    "summary": summary,
                    "requires_approval": False,
                    "acceptance_checkers": ["case_stage_leaf_static"],
                }
            ],
        )
        frontier = current_repair_action_execution_frontier(
            run_dir,
            step,
            "operator_leaf_closure",
        )
        self.assertIsNotNone(frontier)
        assert frontier is not None
        return frontier

    def test_new_post_validation_materialization_failure_requires_fresh_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="incomplete"
            )

            result = resume_prior_resource_failed_validation(
                run_dir, out_dir, 0, step=step
            )

        feedback = result["post_validation_materialization_feedback"]
        self.assertEqual(result["status"], "not_run")
        self.assertEqual(feedback["status"], "ready")
        self.assertEqual(len(feedback["feedback_frontier_sha256"]), 64)
        self.assertEqual(len(feedback["patch_application"]["sha256"]), 64)
        self.assertEqual(len(feedback["requested_validation"]["sha256"]), 64)
        self.assertEqual(len(feedback["materialization"]["sha256"]), 64)
        self.assertEqual(len(feedback["binding_manifest"]["sha256"]), 64)
        self.assertEqual(len(feedback["binding_requirements"]["sha256"]), 64)

    def test_consumed_post_validation_materialization_failure_blocks_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="incomplete"
            )
            feedback = post_validation_materialization_feedback(run_dir, out_dir, step)
            result_path = out_dir / "llm" / "verification_capability_repair_agent_result.json"
            result_path.parent.mkdir()
            result_path.write_text(
                json.dumps(
                    {
                        "agent": "verification_capability_repair_agent",
                        "capability_repair_context": {
                            "repair_step_id": step["id"],
                        },
                        "post_validation_materialization_feedback": feedback,
                    }
                ),
                encoding="utf-8",
            )
            result = resume_prior_resource_failed_validation(
                run_dir, out_dir, 0, step=step
            )

            self.assertTrue(
                capability_agent_consumed_materialization_feedback(
                    out_dir, step, feedback
                )
            )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["post_validation_materialization_feedback_consumed"])

    def test_passing_materialization_keeps_validation_resume(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )

            result = resume_prior_resource_failed_validation(
                run_dir, out_dir, 0, step=step
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["applied_patch_checkpoint_reused"])

    def test_fresh_checker_bound_action_frontier_invalidates_validation_cache(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            frontier = self._current_action_frontier(run_dir, step)

            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=frontier,
            )

        self.assertEqual(result["status"], "not_run")
        self.assertEqual(
            result["fresh_action_execution_frontier"]["identity_sha256"],
            frontier["identity_sha256"],
        )

    def test_consumed_action_frontier_reuses_validation_cache(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            frontier = self._current_action_frontier(run_dir, step)
            mark_repair_action_execution_frontier_consumed(
                out_dir,
                frontier,
                {"status": "fail", "summary": "current probe failed"},
            )

            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=frontier,
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["applied_patch_checkpoint_reused"])

    def test_changed_action_frontier_requires_one_new_probe(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            initial_frontier = self._current_action_frontier(run_dir, step)
            mark_repair_action_execution_frontier_consumed(
                out_dir,
                initial_frontier,
                {"status": "fail", "summary": "initial probe failed"},
            )
            changed_frontier = self._current_action_frontier(
                run_dir,
                step,
                summary="reconcile current leaf evidence after new CCTG slice",
            )

            result = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
                action_execution_frontier=changed_frontier,
            )

        self.assertNotEqual(
            initial_frontier["identity_sha256"],
            changed_frontier["identity_sha256"],
        )
        self.assertEqual(result["status"], "not_run")

    def test_approval_or_malformed_action_cannot_invalidate_validation_cache(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step = self._post_validation_fixture(
                Path(temp_dir), materialization_status="pass"
            )
            for action in (
                {
                    "id": "repair.requires_approval",
                    "requires_approval": True,
                    "acceptance_checkers": ["case_stage_leaf_static"],
                },
                {
                    "id": "repair.malformed",
                    "requires_approval": False,
                    "acceptance_checkers": [],
                },
            ):
                self._write_repair_action_disposition(run_dir, step, [action])
                frontier = current_repair_action_execution_frontier(
                    run_dir,
                    step,
                    "operator_leaf_closure",
                )
                result = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    0,
                    step=step,
                    action_execution_frontier=frontier,
                )
                self.assertIsNone(frontier)
                self.assertEqual(result["status"], "pass")

    def test_incomplete_empty_report_blocks_without_spinning(self) -> None:
        result = repair_loop_disposition({"status": "incomplete", "step_results": []})

        self.assertEqual(result["status"], "blocked")

    def test_unchanged_failure_without_new_observation_blocks(self) -> None:
        result = repair_loop_disposition(
            {
                "status": "incomplete",
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "result": {
                            "status": "fail",
                            "summary": "unchanged applied patch replay did not pass",
                            "llm_record": None,
                            "post_patch_capability_probe_log": None,
                            "capability_reports": [],
                            "instrumentation_evidence_collected": False,
                            "instrumentation_evidence": {"status": "not_run"},
                        },
                    }
                ],
            }
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["no_progress_failures"], ["unchanged applied patch replay did not pass"])

    def test_repeated_failed_probe_uses_content_not_runtime_duration(self) -> None:
        with TemporaryDirectory() as temp_dir:
            probe_path = Path(temp_dir) / "resource_resume.json"

            def write_probe(*, duration_sec: float, stderr_tail: str) -> None:
                probe_path.write_text(
                    json.dumps(
                        {
                            "argv": ["python3", "case_hierarchical_check.py"],
                            "case_adapter_tool": "case_stage_leaf_static",
                            "duration_sec": duration_sec,
                            "returncode": 1,
                            "status": "fail",
                            "summary": "returncode=1",
                            "stderr_tail": stderr_tail,
                        }
                    ),
                    encoding="utf-8",
                )

            report = {
                "status": "incomplete",
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "verification_capability_repair",
                        "result": {
                            "status": "fail",
                            "summary": "unchanged applied patch replay did not pass",
                            "post_patch_capability_probe_log": str(probe_path),
                            "llm_record": None,
                            "capability_reports": [],
                        },
                    }
                ],
            }
            write_probe(duration_sec=0.01, stderr_tail="same failure")
            first = repair_loop_disposition(report)

            write_probe(duration_sec=0.99, stderr_tail="same failure")
            repeated = repair_loop_disposition(
                report,
                prior_failure_frontiers=first["observed_failure_frontiers"],
            )

            write_probe(duration_sec=0.02, stderr_tail="new failure observation")
            changed = repair_loop_disposition(
                report,
                prior_failure_frontiers=first["observed_failure_frontiers"],
            )

        self.assertEqual(first["status"], "continue")
        self.assertEqual(repeated["status"], "blocked")
        self.assertEqual(changed["status"], "continue")

    def test_repair_loop_reconstructs_legacy_archived_probe_frontier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            report_path = run_dir / "repair_execution" / "repair_execution_report.json"
            loop_record_path = (
                run_dir
                / "repair_execution"
                / "loop"
                / "iteration_0001"
                / "iteration_record.json"
            )
            snapshot_path = loop_record_path.parent / "00_post_patch_probe.json"
            state_path.parent.mkdir(parents=True)
            report_path.parent.mkdir(parents=True)
            loop_record_path.parent.mkdir(parents=True)
            state_path.write_text("{}", encoding="utf-8")
            snapshot_path.write_text(
                json.dumps(
                    {
                        "argv": ["python3", "case_hierarchical_check.py"],
                        "case_adapter_tool": "case_stage_leaf_static",
                        "duration_sec": 0.01,
                        "returncode": 1,
                        "status": "fail",
                        "summary": "returncode=1",
                        "stderr_tail": "same failure",
                    }
                ),
                encoding="utf-8",
            )
            current_probe = run_dir / "repair_execution" / "resource_resume.json"
            current_probe.write_text(
                json.dumps(
                    {
                        "argv": ["python3", "case_hierarchical_check.py"],
                        "case_adapter_tool": "case_stage_leaf_static",
                        "duration_sec": 0.99,
                        "returncode": 1,
                        "status": "fail",
                        "summary": "returncode=1",
                        "stderr_tail": "same failure",
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "status": "incomplete",
                "errors": ["repair_step.00: unchanged replay"],
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "verification_capability_repair",
                        "result": {
                            "status": "fail",
                            "summary": "unchanged replay",
                            "post_patch_capability_probe_log": str(current_probe),
                            "llm_record": None,
                            "capability_reports": [],
                        },
                    }
                ],
            }
            loop_record_path.write_text(
                json.dumps(
                    {
                        "repair_execution_report": report,
                        "evidence_snapshots": [
                            {
                                "role": "post_patch_capability_probe_log",
                                "snapshot_path": str(snapshot_path),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(report_path, report),
            ) as execute_mock, patch(
                "accagent.framework.stage_repair_execute.archive_repair_loop_iteration",
                return_value=run_dir / "iteration_record.json",
            ):
                _, result = run_repair_loop(
                    Namespace(sacg_state=state_path, max_loop_iters=0)
                )

        execute_mock.assert_called_once()
        self.assertEqual(result["repair_loop_disposition"]["status"], "blocked")

    def test_repair_loop_stops_after_unchanged_failure_without_new_observation(self) -> None:
        report = {
            "status": "incomplete",
            "errors": ["repair_step.00: unchanged replay"],
            "step_results": [
                {
                    "step_id": "repair_step.00",
                    "result": {
                        "status": "fail",
                        "summary": "unchanged replay",
                        "llm_record": None,
                        "post_patch_capability_probe_log": None,
                        "capability_reports": [],
                        "instrumentation_evidence_collected": False,
                        "instrumentation_evidence": {"status": "not_run"},
                    },
                }
            ],
        }
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state_path = run_dir / "verification_artifacts" / "sacg_state.json"
            report_path = run_dir / "repair_execution" / "repair_execution_report.json"
            state_path.parent.mkdir()
            report_path.parent.mkdir()
            state_path.write_text("{}", encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(report_path, report),
            ) as execute_mock, patch(
                "accagent.framework.stage_repair_execute.archive_repair_loop_iteration",
                return_value=run_dir / "iteration_record.json",
            ):
                _, result = run_repair_loop(
                    Namespace(sacg_state=state_path, max_loop_iters=0)
                )

        execute_mock.assert_called_once()
        self.assertEqual(result["repair_loop_disposition"]["status"], "blocked")

    def test_stage6_prompt_keeps_current_epoch_and_excludes_old_signal_values(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("repair"))

        self.assertIn("Each new Layer-3 run is a fresh signal epoch", rules)
        self.assertIn("never use old signal values as current evidence", rules)
        self.assertIn("at least 300 real scalar signals", rules)


if __name__ == "__main__":
    unittest.main()
