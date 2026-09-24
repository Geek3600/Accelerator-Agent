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
