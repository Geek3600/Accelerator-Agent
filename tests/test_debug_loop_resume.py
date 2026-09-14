import json
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
)


class DebugLoopResumeTest(TestCase):
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
                        "id": "artifact.stage7.operator_leaf_promotion_certificate",
                        "path": str(leaf_path),
                        "trust_status": "validated",
                    },
                    {
                        "id": "artifact.stage7.single_layer_promotion_certificate",
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
                    {"id": "artifact.stage8.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(execution_path),
                    },
                ]
            }

            resume = pending_repair_execution_resume(state)

        self.assertIsNotNone(resume)
        assert resume is not None
        self.assertEqual(resume["repair_plan"], plan_path)

    def test_environment_only_block_reenters_stage7(self) -> None:
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
                    {"id": "artifact.stage8.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage8.repair_execution_report",
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
                    {"id": "artifact.stage8.repair_plan", "path": str(plan_path)},
                    {
                        "id": "artifact.stage8.repair_execution_report",
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

    def test_agent_owned_capability_reenters_stage7(self) -> None:
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
