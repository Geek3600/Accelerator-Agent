import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.stage_debug_loop import (
    agent_transaction_retry_key,
    deterministic_repair_followup_key,
    pending_repair_execution_resume,
    repair_execution_requires_fresh_agent_planning,
    repair_execution_has_new_real_tool_evidence,
    reusable_scope_checkpoint_prefix,
    run_stage6_verification,
)


class DebugLoopResumeTest(TestCase):
    def test_initial_layer3_verification_receives_required_checkpoint_environment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "sacg_state.json"
            request = root / "checkpoint_request.json"
            observed: dict[str, str | None] = {}

            def fake_run_verification(_args):
                observed["required"] = os.environ.get(
                    "SPATIALACC_CHECKPOINT_REQUIRED"
                )
                observed["request"] = os.environ.get(
                    "SPATIALACC_CHECKPOINT_REQUEST"
                )
                return root / "verification_report.json", {"status": "ready"}

            with patch(
                "accagent.framework.stage_debug_loop.prepare_stage3_checkpoint_probe_environment",
                return_value={
                    "status": "pass",
                    "summary": "prepared cold capture",
                    "request_path": str(request),
                    "checkpoint_enabled": True,
                    "cold_fallback": False,
                    "remote_tool_must_not_start": False,
                    "env": {
                        "SPATIALACC_CHECKPOINT_REQUIRED": "1",
                        "SPATIALACC_CHECKPOINT_REQUEST": str(request),
                    },
                },
            ), patch(
                "accagent.framework.stage_debug_loop.run_verification",
                side_effect=fake_run_verification,
            ):
                verification_path, verification_report, preparation = (
                    run_stage6_verification(
                        current_state=state,
                        run_dir=root,
                        active_scope="board_axi_ddr_closure",
                        timeout_sec=0,
                        reused_scopes=[
                            "operator_leaf_closure",
                            "single_layer_closure",
                        ],
                        iteration_index=0,
                    )
                )

        self.assertEqual(verification_path, root / "verification_report.json")
        self.assertEqual(verification_report, {"status": "ready"})
        self.assertEqual(preparation["status"], "pass")
        self.assertEqual(observed["required"], "1")
        self.assertEqual(observed["request"], str(request))

    def test_layer3_checkpoint_preparation_failure_prevents_verification(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch(
                "accagent.framework.stage_debug_loop.prepare_stage3_checkpoint_probe_environment",
                return_value={
                    "status": "fail",
                    "summary": "checkpoint request is not ready",
                    "env": {"SPATIALACC_CHECKPOINT_REQUIRED": "1"},
                    "remote_tool_must_not_start": True,
                },
            ), patch(
                "accagent.framework.stage_debug_loop.run_verification"
            ) as run_verification_mock:
                verification_path, verification_report, preparation = (
                    run_stage6_verification(
                        current_state=root / "sacg_state.json",
                        run_dir=root,
                        active_scope="board_axi_ddr_closure",
                        timeout_sec=0,
                        reused_scopes=[],
                        iteration_index=0,
                    )
                )

        self.assertIsNone(verification_path)
        self.assertIsNone(verification_report)
        self.assertEqual(preparation["status"], "fail")
        run_verification_mock.assert_not_called()

    def test_lower_layer_verification_does_not_prepare_checkpoint(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for index, scope in enumerate(
                ("operator_leaf_closure", "single_layer_closure")
            ):
                with self.subTest(scope=scope), patch(
                    "accagent.framework.stage_debug_loop.prepare_stage3_checkpoint_probe_environment"
                ) as prepare_mock, patch(
                    "accagent.framework.stage_debug_loop.run_verification",
                    return_value=(
                        root / f"verification_report_{index}.json",
                        {"status": "ready"},
                    ),
                ) as run_verification_mock:
                    verification_path, verification_report, preparation = (
                        run_stage6_verification(
                            current_state=root / "sacg_state.json",
                            run_dir=root,
                            active_scope=scope,
                            timeout_sec=0,
                            reused_scopes=[],
                            iteration_index=index,
                        )
                    )

                prepare_mock.assert_not_called()
                run_verification_mock.assert_called_once()
                self.assertIsNotNone(verification_path)
                self.assertEqual(verification_report, {"status": "ready"})
                self.assertEqual(preparation["status"], "not_required")

    def test_recovers_scope_entry_certificates_without_replaying_lower_tools(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            debug_dir = run_dir / "debug_loop"
            debug_dir.mkdir()
            leaf_path = run_dir / "leaf_certificate.json"
            single_path = run_dir / "single_certificate.json"
            leaf_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            single_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            (debug_dir / "debug_loop_report.json").write_text(
                json.dumps(
                    {
                        "target_scope": "board_axi_ddr_closure",
                        "reused_scopes": [
                            "operator_leaf_closure",
                            "single_layer_closure",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage6.operator_leaf_promotion_certificate",
                        "path": str(leaf_path),
                        "trust_status": "validated",
                    },
                    {
                        "id": "artifact.stage6.single_layer_promotion_certificate",
                        "path": str(single_path),
                        "trust_status": "validated",
                    },
                ]
            }

            recovered = reusable_scope_checkpoint_prefix(
                state,
                run_dir,
                "board_axi_ddr_closure",
                [
                    "operator_leaf_closure",
                    "single_layer_closure",
                    "board_axi_ddr_closure",
                ],
            )

        self.assertEqual(recovered, [
            "operator_leaf_closure",
            "single_layer_closure",
        ])

    def test_resumes_executable_plan_without_replanning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "repair_plan.json"
            execution_path = root / "repair_execution.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["executor must retry after framework update"],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state)

        self.assertIsNotNone(resume)
        assert resume is not None
        self.assertEqual(resume["repair_plan"], plan_path)

    def test_environment_only_block_reenters_stage6(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = root / "repair_plan.json"
            execution_path = root / "repair_execution.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [{"id": "repair_step.00"}],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["implementation agent requires an upstream capability"],
                        "step_results": [
                            {
                                "result": {
                                    "framework_action_required": True,
                                    "required_capabilities": [
                                        {
                                            "producer_scope": "framework_execution_environment"
                                        }
                                    ],
                                }
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state)

        self.assertIsNone(resume)

    def test_validated_identity_supersedes_stale_discovery_repair_resume(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            plan_path = run_dir / "repair_plan.json"
            execution_path = run_dir / "repair_execution.json"
            identity_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json"
            )
            identity_path.parent.mkdir(parents=True)
            identity_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            plan_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [
                                {
                                    "id": "repair_step.00",
                                    "action": {
                                        "repair_kind": "exact_board_interface_discovery"
                                    },
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            execution_path.write_text(
                json.dumps(
                    {
                        "stage": "repair_execution",
                        "status": "incomplete",
                        "errors": ["historical discovery failure"],
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {"id": "artifact.stage6.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage6.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }
            with patch(
                "accagent.framework.board_acceptance_contract.validate_exact_board_identity",
                return_value={"status": "pass"},
            ):
                resume = pending_repair_execution_resume(state, run_dir)

        self.assertIsNone(resume)

    def test_does_not_resume_completed_or_new_tool_execution(self) -> None:
        report = {
            "step_results": [
                {
                    "result": {
                        "new_current_real_tool_failure_requires_agent": True,
                    }
                }
            ]
        }

        self.assertTrue(repair_execution_has_new_real_tool_evidence(report))
        self.assertFalse(repair_execution_has_new_real_tool_evidence({}))

    def test_agent_owned_capability_reenters_stage6(self) -> None:
        report = {
            "step_results": [
                {
                    "result": {
                        "status": "blocked",
                        "framework_action_required": True,
                        "required_capabilities": [
                            {
                                "producer_scope": (
                                    "generated board-integration simulation "
                                    "observability"
                                )
                            }
                        ],
                    }
                }
            ]
        }

        self.assertTrue(repair_execution_requires_fresh_agent_planning(report))
        self.assertFalse(
            repair_execution_requires_fresh_agent_planning(
                {
                    "step_results": [
                        {
                            "result": {
                                "status": "blocked",
                                "framework_action_required": True,
                                "required_capabilities": [
                                    {
                                        "producer_scope": (
                                            "framework_execution_environment"
                                        )
                                    }
                                ],
                            }
                        }
                    ]
                }
            )
        )

    def test_recognizes_only_new_applied_deterministic_preflight_feedback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            patch_path = root / "agent_patch_application.json"
            materialization_path = root / "dut_weight_binding_materialization.json"
            patch_path.write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            materialization_path.write_text(
                json.dumps(
                    {
                        "status": "incomplete",
                        "manifest_sha256": "a" * 64,
                        "blockers": ["current preflight contract is incomplete"],
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "step_results": [
                    {
                        "result": {
                            "agent_patch_application": str(patch_path),
                            "dut_weight_binding_materialization": str(
                                materialization_path
                            ),
                        }
                    }
                ]
            }

            key = deterministic_repair_followup_key(report)

            self.assertIsNotNone(key)
            self.assertIn("manifest_sha256", key)
            patch_path.write_text(
                json.dumps({"status": "blocked"}), encoding="utf-8"
            )
            self.assertIsNone(deterministic_repair_followup_key(report))

    def test_identifies_only_no_tool_agent_transaction_rejections(self) -> None:
        with TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "retry_agent_without_real_tool": True,
                        "files": [],
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "real_tool_replay_required_before_retry": False,
                            "failure_class": "agent_transaction_contract",
                            "blockers": ["missing required edit metadata"],
                            "unchanged_pre_edit_files": ["board_tb.sv"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "step_results": [
                    {"result": {"agent_patch_application": str(patch_path)}}
                ]
            }

            key = agent_transaction_retry_key(report)
            self.assertIsNotNone(key)

            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "retry_agent_without_real_tool": True,
                        "files": [],
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "real_tool_replay_required_before_retry": False,
                            "failure_class": "agent_transaction_contract",
                            "blockers": ["a different invalid field"],
                            "unchanged_pre_edit_files": ["board_tb.sv"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(key, agent_transaction_retry_key(report))

            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "retry_agent_without_real_tool": True,
                        "files": ["board_tb.sv"],
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "real_tool_replay_required_before_retry": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertIsNone(agent_transaction_retry_key(report))


if __name__ == "__main__":
    import unittest

    unittest.main()
