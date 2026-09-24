"""Minimal current Stage-6 LLM execution-contract regressions."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from accagent.framework.stage_repair_execute import (
    capability_repair_source_bundle,
    layer3_required_code_edit_errors,
    repair_loop_disposition,
    repair_source_bundle,
)


class RepairPatchExecutionTest(unittest.TestCase):
    def test_evidence_gap_accepts_runtime_observation_without_speculative_rtl_edit(self) -> None:
        output = {
            "status": "ready_to_apply",
            "blocked_reasons": [],
            "file_edits": [],
            "adaptive_observation_decision": {"mode": "deepen_simulation_observation"},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = layer3_required_code_edit_errors(
                output,
                Path(temp_dir),
                current_signal_epoch=True,
            )

        self.assertEqual(errors, [])

    def test_missing_action_is_rejected_before_a_vcs_replay(self) -> None:
        output = {"status": "ready_to_apply", "blocked_reasons": [], "file_edits": []}
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = layer3_required_code_edit_errors(
                output,
                Path(temp_dir),
                current_signal_epoch=True,
            )

        self.assertTrue(any("observation" in error for error in errors))

    def test_blocked_step_is_turned_into_a_continue_disposition(self) -> None:
        result = repair_loop_disposition(
            {"step_results": [{"result": {"status": "blocked", "summary": "need a deeper signal plan"}}]}
        )

        self.assertEqual(result["status"], "continue")
        self.assertTrue(result["observation_replan_required"])

    def test_hash_changing_agent_patch_continues_current_layer_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "files": [
                            {
                                "path": "generated/semantic_harness.scala",
                                "before_sha256": "before",
                                "after_sha256": "after",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = repair_loop_disposition(
                {
                    "status": "incomplete",
                    "step_results": [
                        {
                            "result": {
                                "status": "fail",
                                "llm_record": "fresh-agent-result.json",
                                "agent_patch_application": str(patch_path),
                            }
                        }
                    ],
                }
            )

        self.assertEqual(result["status"], "continue")
        self.assertEqual(result["applied_files"][0]["path"], "generated/semantic_harness.scala")

    def test_source_bundle_reads_repair_closure_from_explicit_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir()
            closure = {"status": "ready", "scope": "operator_leaf_modules"}
            (out_dir / "fpga_ip_repair_closure.json").write_text(
                json.dumps(closure), encoding="utf-8"
            )

            bundle = repair_source_bundle({}, run_dir, out_dir)

        self.assertEqual(bundle["fpga_ip_repair_closure"], closure)

    def test_capability_bundle_preserves_earliest_failed_real_tool_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            out_dir = run_dir / "repair_execution"
            tool_dir = run_dir / "local_tools"
            verification_dir = run_dir / "verification"
            real_tools_dir = verification_dir / "real_tools"
            input_dir = run_dir / "input"
            pipeline_dir = run_dir / "pipeline_planning"
            for path in (out_dir, tool_dir, real_tools_dir, input_dir, pipeline_dir):
                path.mkdir(parents=True, exist_ok=True)

            script_path = tool_dir / "weight_catalog.py"
            argv_input_path = tool_dir / "semantic_adapter.json"
            output_path = verification_dir / "model_weights" / "partial_report.json"
            case_adapter_path = input_dir / "case_adapter.json"
            pipeline_plan_path = pipeline_dir / "pipeline_plan.json"
            script_path.write_text("print('catalog')\n", encoding="utf-8")
            argv_input_path.write_text('{"adapter": "current"}\n', encoding="utf-8")
            output_path.parent.mkdir()
            output_path.write_text('{"status": "partial"}\n', encoding="utf-8")
            case_adapter_path.write_text('{"case": "current"}\n', encoding="utf-8")
            pipeline_plan_path.write_text('{"pipeline": "current"}\n', encoding="utf-8")

            tool_record_path = real_tools_dir / "weight_catalog.json"
            tool_record_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "returncode": 1,
                        "summary": "returncode=1",
                        "stderr_tail": "no tensor matched\n",
                        "execution": {
                            "cwd": str(run_dir),
                            "argv": [
                                "python3",
                                str(script_path.relative_to(run_dir)),
                                "--semantic-adapter",
                                str(argv_input_path.relative_to(run_dir)),
                            ],
                        },
                        "execution_fingerprint": {
                            "payload": {"scripts": [{"path": str(script_path)}]}
                        },
                        "output_fingerprints": {
                            "artifacts": [{"path": str(output_path)}]
                        },
                    }
                ),
                encoding="utf-8",
            )
            verification_result_path = verification_dir / "verification_result.json"
            verification_result_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "status": "fail",
                                "checker": "real_tool.weight_catalog",
                                "log_path": str(tool_record_path),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            bundle = capability_repair_source_bundle({}, run_dir, out_dir)

        document_paths = {document["path"] for document in bundle["documents"]}
        self.assertTrue(
            {
                str(verification_result_path),
                str(tool_record_path),
                str(script_path),
                str(argv_input_path),
                str(output_path),
                str(case_adapter_path),
                str(pipeline_plan_path),
            }.issubset(document_paths)
        )
        context = bundle["earliest_failed_real_tool_context"]
        self.assertEqual(context["tool_record"], str(tool_record_path))
        self.assertEqual(context["file_valued_argv_inputs"], [str(script_path), str(argv_input_path)])
        self.assertEqual(context["produced_reports"], [str(output_path)])
        self.assertEqual(
            {entry["path"] for entry in context["semantic_authority"]},
            {str(case_adapter_path), str(pipeline_plan_path)},
        )


if __name__ == "__main__":
    unittest.main()
