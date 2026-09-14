from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from accagent.framework.stage_repair_execute import (
    board_integration_prompt_rules,
    checkpoint_hook_specialist_package,
    prepare_stage3_checkpoint_probe_environment,
    run_current_layer_causal_replay,
    run_exact_board_checkpoint_analyzer_only,
    run_exact_board_validation_chain,
    run_rerun_step,
    simulation_checkpoint_runtime_capability_failure,
)


class CheckpointRepairIntegrationTest(unittest.TestCase):
    def test_checkpoint_calibration_failure_runs_analyzer_without_vcs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            analyzer_result = {
                "status": "pass",
                "produced_reports": [{"path": "diagnosis.json"}],
            }
            feedback = {
                "status": "ready",
                "diagnosis": {
                    "value": {
                        "status": "needs_repair",
                        "summary": "checkpoint restore suffix diverged",
                    }
                },
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_capability_probe",
                return_value=analyzer_result,
            ) as probe, patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value=feedback,
            ):
                result = run_exact_board_checkpoint_analyzer_only(
                    case_adapter={"case_id": "case"},
                    analyzer_role="vcs_evidence_analyzer",
                    analyzer_spec={"name": "analyzer"},
                    vcs_spec={"name": "vcs"},
                    run_dir=run_dir,
                    step={"id": "repair.board.checkpoint"},
                    out_dir=out_dir,
                    timeout_sec=0,
                    label="checkpoint_failure",
                )

        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["vcs"]["real_board_vcs_was_not_rerun"])
        self.assertEqual(result["summary"], "checkpoint restore suffix diverged")
        probe.assert_called_once()
        self.assertEqual(
            probe.call_args.kwargs["label"],
            "checkpoint_failure_analyzer_only",
        )

    def test_projected_calibration_failure_survives_new_checkpoint_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            runner = (
                run_dir
                / "verification"
                / "vcs"
                / "case_board_vcs_functional.json"
            )
            runner.parent.mkdir(parents=True)
            projected = {
                "status": "ready",
                "source": "factual_same_source_restore_equivalence_calibration",
                "request_sha256": "a" * 64,
                "semantic_cut_sha256": "b" * 64,
                "failure_class": "simulation_checkpoint_capability_missing_or_invalid",
            }
            runner.write_text(
                json.dumps({"checkpoint_runtime_execution_failure": projected}),
                encoding="utf-8",
            )
            result = simulation_checkpoint_runtime_capability_failure(
                run_dir,
                {
                    "request_sha256": "c" * 64,
                    "semantic_cut": {"cut_sha256": "d" * 64},
                },
            )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["request_sha256"], "a" * 64)
        self.assertEqual(result["current_request_sha256"], "c" * 64)
        self.assertTrue(result["state_reuse_was_not_authorized_by_this_projection"])

    def test_runtime_checkpoint_gap_requires_current_request_and_observed_cut(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            runner_path = (
                run_dir
                / "verification"
                / "vcs"
                / "case_board_vcs_functional.json"
            )
            progress_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "reports"
                / "progress_event_log.jsonl"
            )
            runner_path.parent.mkdir(parents=True)
            progress_path.parent.mkdir(parents=True)
            trigger = {
                "sequence": 41,
                "cycle": 1234,
                "phase": "kernel_output_token_complete",
                "event_kind": "semantic_progress",
                "layer": 0,
                "token": 0,
                "beat": 111,
                "stage_or_boundary": "pipeline_boundary.block_output",
            }
            request = {
                "request_sha256": "a" * 64,
                "semantic_cut": {"trigger": trigger},
            }
            runner_path.write_text(
                json.dumps(
                    {
                        "phase": "remote_vcs",
                        "input_fingerprint_sha256": "b" * 64,
                        "remote_workdir": "/remote/job",
                        "checkpoint_execution": {
                            "enabled": True,
                            "mode": "cold_capture",
                            "request_sha256": request["request_sha256"],
                        },
                        "checkpoint_artifacts": {
                            "status": "fail",
                            "mode": "cold_capture",
                            "errors": ["capture report is missing"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            progress_path.write_text(json.dumps(trigger) + "\n", encoding="utf-8")

            current = simulation_checkpoint_runtime_capability_failure(
                run_dir,
                request,
            )
            stale = simulation_checkpoint_runtime_capability_failure(
                run_dir,
                {**request, "request_sha256": "c" * 64},
            )

        self.assertEqual(current["status"], "ready")
        self.assertEqual(
            current["trigger_observation"]["status"], "observed"
        )
        self.assertTrue(current["remote_tool_was_started"])
        self.assertEqual(current["checkpoint_artifact_errors"], ["capture report is missing"])
        self.assertEqual(stale["status"], "stale")

    def test_runtime_checkpoint_gap_reuses_only_unchanged_hook_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            testbench_path = run_dir / "generated" / "board" / "AdaptiveBoardTb.sv"
            manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            testbench_path.parent.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            testbench_path.write_text("module AdaptiveBoardTb; endmodule\n", encoding="utf-8")
            testbench_sha256 = hashlib.sha256(testbench_path.read_bytes()).hexdigest()
            manifest_path.write_text(
                json.dumps(
                    {
                        "testbench": {
                            "path": str(testbench_path),
                            "sha256": testbench_sha256,
                        }
                    }
                ),
                encoding="utf-8",
            )
            trigger = {
                "sequence": 41,
                "cycle": 1234,
                "phase": "kernel_output_token_complete",
                "event_kind": "semantic_progress",
                "layer": 0,
                "token": 0,
                "beat": 111,
                "stage_or_boundary": "pipeline_boundary.block_output",
            }
            current_request = {
                "request_sha256": "c" * 64,
                "semantic_cut": {
                    "cut_sha256": "d" * 64,
                    "trigger": trigger,
                },
            }
            fingerprint = "f" * 64
            iteration_report = (
                run_dir
                / "repair_execution"
                / "loop"
                / "iteration_0063"
                / "02_capability_report_case_board_vcs_functional.json"
            )
            artifact_root = (
                run_dir
                / "verification"
                / "remote_artifacts"
                / "board_vcs"
                / fingerprint
            )
            progress_path = artifact_root / "evidence" / "003_progress_event_log.jsonl"
            iteration_report.parent.mkdir(parents=True)
            progress_path.parent.mkdir(parents=True)
            iteration_report.write_text(
                json.dumps(
                    {
                        "phase": "remote_vcs",
                        "input_fingerprint_sha256": fingerprint,
                        "remote_workdir": "/remote/job",
                        "checkpoint_execution": {
                            "enabled": True,
                            "mode": "cold_capture",
                            "request_sha256": "a" * 64,
                        },
                        "checkpoint_artifacts": {
                            "status": "fail",
                            "mode": "cold_capture",
                            "errors": ["capture report is missing"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            progress_path.write_text(json.dumps(trigger) + "\n", encoding="utf-8")
            repo_root = Path(__file__).resolve().parents[1]
            adapter_payload = []
            for name in (
                "vcs_state_checkpoint_vpi.c",
                "vcs_state_checkpoint_vpi.tab",
            ):
                path = repo_root / "accagent" / "framework" / "simulator_adapters" / name
                adapter_payload.append(
                    {
                        "path": f"checkpoint/adapter/{name}",
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
            (artifact_root / "job_contract.json").write_text(
                json.dumps(
                    {
                        "simulate_command": (
                            "./vcs_work/simv "
                            f"+SPATIALACC_CHECKPOINT_REQUEST_SHA256={'a' * 64} "
                            f"+SPATIALACC_CHECKPOINT_SEMANTIC_CUT_SHA256={'d' * 64} "
                            "+SPATIALACC_CHECKPOINT_CUT_SEQUENCE=41 "
                            "+SPATIALACC_CHECKPOINT_CUT_CYCLE=1234 "
                            "+SPATIALACC_CHECKPOINT_CUT_LAYER=0 "
                            "+SPATIALACC_CHECKPOINT_CUT_TOKEN=0 "
                            "+SPATIALACC_CHECKPOINT_CUT_BEAT=111 "
                            "+SPATIALACC_CHECKPOINT_CUT_PHASE=kernel_output_token_complete"
                        ),
                        "payload": [
                            {
                                "path": f"sources/{testbench_path.name}",
                                "sha256": testbench_sha256,
                            },
                            *adapter_payload,
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reusable = simulation_checkpoint_runtime_capability_failure(
                run_dir,
                current_request,
            )
            changed_cut_request = {
                **current_request,
                "semantic_cut": {
                    "cut_sha256": "e" * 64,
                    "trigger": {
                        **trigger,
                        "sequence": 99,
                        "cycle": 9999,
                        "phase": "kernel_input_token_complete",
                    },
                },
            }
            reusable_after_cut_change = (
                simulation_checkpoint_runtime_capability_failure(
                    run_dir,
                    changed_cut_request,
                )
            )
            testbench_path.write_text(
                "module AdaptiveBoardTb; wire hook_fixed; endmodule\n",
                encoding="utf-8",
            )
            invalidated = simulation_checkpoint_runtime_capability_failure(
                run_dir,
                current_request,
            )

        self.assertEqual(reusable["status"], "ready")
        self.assertEqual(
            reusable["source"], "content_addressed_historical_hook_identity"
        )
        self.assertEqual(reusable["trigger_observation"]["status"], "observed")
        self.assertEqual(reusable_after_cut_change["status"], "ready")
        self.assertEqual(
            reusable_after_cut_change["historical_semantic_cut_sha256"],
            "d" * 64,
        )
        self.assertEqual(
            reusable_after_cut_change["current_semantic_cut_sha256"],
            "e" * 64,
        )
        self.assertNotEqual(invalidated["status"], "ready")

    def test_stage3_checkpoint_preparation_uses_only_certified_replay_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            request = {
                "schema_version": "spatialaccagent.simulation_checkpoint_request.v1",
                "status": "ready",
                "request_sha256": "a" * 64,
                "replay_decision": {"mode": "native_restore"},
            }
            with patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_debug_episode",
                return_value={
                    "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode.v1",
                    "status": "active",
                    "episode_id": "episode-1",
                },
            ), patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_request",
                return_value=request,
            ):
                result = prepare_stage3_checkpoint_probe_environment(
                    run_dir,
                    label="pre_patch",
                )

            request_path = Path(result["request_path"])
            request_persisted = request_path.is_file()

        self.assertEqual(result["status"], "pass")
        self.assertTrue(request_persisted)
        self.assertNotIn("SPATIALACC_CHECKPOINT_REQUIRED", result["env"])
        self.assertEqual(result["env"]["SPATIALACC_CHECKPOINT_REPLAY"], "1")
        self.assertEqual(
            result["env"]["SPATIALACC_CHECKPOINT_REQUEST"],
            str(request_path),
        )

    def test_stage3_checkpoint_preparation_keeps_short_bug_on_cold_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            with patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_debug_episode",
                return_value={
                    "schema_version": "spatialaccagent.simulation_checkpoint_debug_episode.v1",
                    "status": "not_admitted",
                    "checkpoint_required": False,
                },
            ):
                result = prepare_stage3_checkpoint_probe_environment(
                    run_dir,
                    label="short_bug",
                )

        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["checkpoint_enabled"])
        self.assertIsNone(result["request_path"])
        self.assertNotIn("SPATIALACC_CHECKPOINT_REQUIRED", result["env"])
        self.assertNotIn("SPATIALACC_CHECKPOINT_REPLAY", result["env"])

    def test_direct_board_rerun_automatically_binds_checkpoint_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            captured_env: dict[str, str] = {}
            preparation = {
                "status": "pass",
                "summary": "prepared",
                "request_path": str(run_dir / "request.json"),
                "request_sha256": "b" * 64,
                "remote_tool_must_not_start": False,
                "env": {
                    "SPATIALACC_CHECKPOINT_REQUIRED": "1",
                    "SPATIALACC_CHECKPOINT_REPLAY": "1",
                    "SPATIALACC_CHECKPOINT_REQUEST": str(run_dir / "request.json"),
                    "SPATIALACC_MAX_HEAVY_JOBS": "1",
                },
            }
            step = {
                "id": "repair.board.rerun",
                "scope": "regression_rerun",
                "tool": "case_vcs_functional_sim",
                "execution": {
                    "argv": [
                        "python3",
                        "scripts/verification/case_board_vcs_functional.py",
                        "--run-dir",
                        str(run_dir),
                    ],
                    "cwd": str(run_dir),
                },
            }

            def invoke(argv, **kwargs):
                captured_env.update(kwargs["env"])
                return subprocess.CompletedProcess(argv, 0, "", "")

            with patch(
                "accagent.framework.stage_repair_execute.prepare_stage3_checkpoint_probe_environment",
                return_value=preparation,
            ), patch(
                "accagent.framework.stage_repair_execute.subprocess.run",
                side_effect=invoke,
            ):
                result = run_rerun_step(
                    step,
                    out_dir,
                    include_remote=True,
                    timeout_sec=0,
                )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(captured_env["SPATIALACC_CHECKPOINT_REQUIRED"], "1")
        self.assertEqual(captured_env["SPATIALACC_CHECKPOINT_REPLAY"], "1")
        self.assertEqual(
            result["checkpoint_request_preparation"]["request_sha256"],
            "b" * 64,
        )

    def test_checkpoint_hook_specialist_package_contains_only_current_hook_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir
                / "generated"
                / "board_integration"
                / "AdaptiveBoardTb.sv"
            )
            board_manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            testbench_path.parent.mkdir(parents=True)
            board_manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                '{"board_simulation_preflight_plan":{"testbench":{}}}\n',
                encoding="utf-8",
            )
            testbench_text = (
                "module AdaptiveBoardTb;\n"
                "  AdaptiveDut dut();\n"
                "endmodule\n"
            )
            testbench_path.write_text(testbench_text, encoding="utf-8")
            testbench_sha256 = hashlib.sha256(
                testbench_text.encode("utf-8")
            ).hexdigest()
            board_manifest_path.write_text(
                json.dumps(
                    {
                        "top_module": "AdaptiveBoardTb",
                        "validation_mode": "compute_slot_axi",
                        "rtl_output_file": "reports/rtl_output.bin",
                        "boundary_trace_file": "reports/boundary_trace.json",
                        "testbench": {
                            "path": str(testbench_path),
                            "sha256": testbench_sha256,
                            "source_id": "generated:testbench",
                            "top_module": "AdaptiveBoardTb",
                            "sole_dut_instance": "dut",
                            "axi_transaction_memory_model": {"status": "ready"},
                            "debug_observability_contract": {
                                "progress_event_log": {
                                    "path": "reports/progress.jsonl"
                                },
                                "required_event_fields": ["cycle"],
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            manifest_sha256 = hashlib.sha256(
                manifest_path.read_bytes()
            ).hexdigest()
            package = {
                "current_board_vcs_feedback": {
                    "diagnosis": {
                        "value": {
                            "failure_class": (
                                "simulation_checkpoint_capability_missing_or_invalid"
                            ),
                            "failure_evidence": {
                                "runner_phase": "checkpoint_contract_validation",
                                "first_real_error": "contract missing",
                            },
                        }
                    }
                },
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "simulation_checkpoint_authority": {
                            "schema_version": "authority.v1",
                            "status": "ready",
                            "required_manifest_contract": {
                                "schema_version": "checkpoint_contract.v1"
                            },
                            "agent_owned": {"framework_runtime_plusarg_abi": {}},
                            "framework_owned": {"derive_suffix": True},
                            "current_request": {"request_sha256": "a" * 64},
                        },
                        "simulation_checkpoint_capability_gap": {
                            "status": "ready_for_capability_repair",
                            "atomic_manifest_merge": {
                                "target_path": str(manifest_path),
                                "expected_sha256": manifest_sha256,
                                "json_pointer": (
                                    "/board_simulation_preflight_plan/testbench/"
                                    "simulation_checkpoint_contract"
                                ),
                            },
                        },
                    }
                },
                "repair_source_bundle": {"documents": ["unrelated large evidence"]},
            }

            specialist = checkpoint_hook_specialist_package(package, run_dir)

        self.assertEqual(specialist["status"], "ready", specialist["blockers"])
        self.assertEqual(
            specialist["current_testbench_source"]["content"], testbench_text
        )
        self.assertEqual(
            specialist["current_board_testbench_contract"][
                "derived_current_dut_state_root"
            ],
            "AdaptiveBoardTb.dut",
        )
        self.assertEqual(
            set(
                specialist["atomic_edit_contract"][
                    "allowed_and_required_paths"
                ]
            ),
            {str(manifest_path.resolve()), str(testbench_path.resolve())},
        )
        self.assertNotIn("repair_source_bundle", specialist)
        self.assertLess(len(json.dumps(specialist).encode("utf-8")), 100_000)

    def test_board_current_layer_replay_persists_request_and_sets_runner_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            step = {
                "id": "repair.board.output",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "targeted_replay_plan": {"status": "ready"},
                "action": {
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "checkpoint_impact": {
                        "status": "ready",
                        "state_schema_change": "none",
                        "affected_cctg_nodes": ["node.output"],
                    },
                },
            }
            request = {
                "schema_version": "spatialaccagent.simulation_checkpoint_request.v1",
                "status": "ready",
                "request_sha256": "a" * 64,
                "replay_decision": {"mode": "cold_capture"},
            }
            captured_env: dict[str, str] = {}

            def run_tool(argv, cwd, env, timeout_sec):
                captured_env.update(env)
                return {"status": "pass", "returncode": 0}

            with patch(
                "accagent.framework.stage_repair_execute.case_adapter_for_state",
                return_value={"case_id": "case"},
            ), patch(
                "accagent.framework.stage_repair_execute.select_current_layer_replay_tool",
                return_value=(
                    "vcs_functional_sim",
                    {"name": "case_vcs_functional_sim", "argv": ["runner"], "produces": []},
                ),
            ), patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_request",
                return_value=request,
            ), patch(
                "accagent.framework.stage_repair_execute.run_local_tool",
                side_effect=run_tool,
            ):
                result = run_current_layer_causal_replay(
                    state={},
                    run_dir=run_dir,
                    step=step,
                    out_dir=out_dir,
                    timeout_sec=0,
                )

            request_path = Path(captured_env["SPATIALACC_CHECKPOINT_REQUEST"])

        self.assertEqual(result["status"], "pass")
        self.assertEqual(captured_env["SPATIALACC_CHECKPOINT_REPLAY"], "1")
        self.assertEqual(captured_env["SPATIALACC_MAX_HEAVY_JOBS"], "1")
        self.assertTrue(request_path.name.endswith("_current_layer.json"))

    def test_candidate_pass_is_followed_by_serial_full_cold_vcs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            runner_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
            runner_path.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            labels: list[str] = []

            def probe(**kwargs):
                label = kwargs["label"]
                labels.append(label)
                if label.endswith("_vcs") and not label.endswith("_full_cold_vcs"):
                    self.assertEqual(
                        kwargs["extra_env"]["SPATIALACC_CHECKPOINT_REQUIRED"],
                        "1",
                    )
                    runner_path.write_text(
                        '{"status":"candidate_pass","stage_pass_eligible":false}\n',
                        encoding="utf-8",
                    )
                elif label.endswith("_full_cold_vcs"):
                    self.assertEqual(
                        kwargs["extra_env"]["SPATIALACC_CHECKPOINT_FINAL_COLD"],
                        "1",
                    )
                    self.assertNotIn(
                        "SPATIALACC_CHECKPOINT_REQUIRED",
                        kwargs["extra_env"],
                    )
                    runner_path.write_text(
                        '{"status":"pass","stage_pass_eligible":true}\n',
                        encoding="utf-8",
                    )
                return {"status": "pass", "produced_reports": []}

            feedback = {
                "status": "ready",
                "diagnosis": {"value": {"status": "pass", "summary": "pass"}},
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_capability_probe",
                side_effect=probe,
            ), patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value=feedback,
            ):
                result = run_exact_board_validation_chain(
                    case_adapter={"case_id": "case"},
                    vcs_role="vcs_functional_sim",
                    vcs_spec={"name": "case_vcs_functional_sim"},
                    analyzer_role="vcs_evidence_analyzer",
                    analyzer_spec={"name": "case_vcs_evidence_analyzer"},
                    run_dir=run_dir,
                    step={"id": "repair.board.output"},
                    out_dir=out_dir,
                    timeout_sec=0,
                    label="post_patch",
                    checkpoint_env={
                        "SPATIALACC_CHECKPOINT_REQUIRED": "1",
                        "SPATIALACC_CHECKPOINT_REPLAY": "1",
                    },
                )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            labels,
            [
                "post_patch_vcs",
                "post_patch_full_cold_vcs",
                "post_patch_analyzer",
            ],
        )
        self.assertTrue(result["full_cold_vcs_required_after_screening"])
        self.assertTrue(result["final_runner_stage_pass_eligible"])

    def test_board_agent_prompt_keeps_checkpoint_optional_and_nonaccepting(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("repair")).lower()

        self.assertIn("checkpoint_impact", rules)
        self.assertIn("operation=merge_json", rules)
        self.assertIn("framework-owned optional acceleration", rules)
        self.assertIn("never a functional gate", rules)
        self.assertIn("without a checkpoint agent turn", rules)
        self.assertIn("explicit_checkpoint_maintenance_requested=true", rules)
        self.assertIn("complete cold exact-board vcs", rules)


if __name__ == "__main__":
    unittest.main()
