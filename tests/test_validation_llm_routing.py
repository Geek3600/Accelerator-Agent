import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.debug_closure import localize_failure
from accagent.framework.repair_loop import build_repair_loop_report, failure_kind
from accagent.framework.stage_repair_execute import run_optional_post_execution_review
from accagent.framework.stage_repair import (
    authoritative_repair_routing_priority,
    boundary_trace_scope_error,
    build_repair_actions,
    completed_board_lower_layer_recheck,
    diagnosis_applicability_report,
    exact_localized_repair_route,
    load_vcs_diagnosis,
    record_board_lower_layer_recheck,
    reconcile_repair_workflow_with_llm,
    restore_persisted_read_only_capability_steps,
    repair_specialist_trigger,
    run_repair_review_team,
)
from accagent.framework.stage_team import team_failure_errors
from accagent.framework.stage_verification import (
    exact_failed_stage7_route,
    no_split_review_summary,
    run_verification_review_team,
    verification_specialist_trigger,
)


class ValidationLlmRoutingTest(TestCase):
    def test_board_multilayer_capability_gap_routes_board_integration_agent(self) -> None:
        failures = [
            {
                "checker": "real_tool.case_multilayer_pipeline",
                "status": "fail",
                "summary": "hash-verified multi-layer pipeline harness is missing",
            }
        ]
        localization = {"status": "verification_capability_gap"}
        loop = {
            "failure_kind": "verification_capability_gap",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "case_multilayer_pipeline", "status": "fail"}
            ],
        }

        actions = build_repair_actions(failures, None, {}, localization, loop)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], "exact_board_integration_harness")
        self.assertEqual(actions[0]["debug_layer"], "board_axi_ddr_wrapped_system")

    def test_repairable_board_vcs_failures_route_same_exact_board_agent(self) -> None:
        repairable = (
            ("vcs_compile_failure", "generated_source_or_compile_plan"),
            ("vcs_elaboration_failure", "board_binding_or_generated_rtl"),
            ("vcs_runtime_failure", "board_rtl_or_testbench"),
            ("elaborated_hierarchy_failure", "board_binding_or_generated_rtl"),
            ("protocol_monitor_failure", "board_rtl_or_testbench"),
            ("pipeline_overlap_failure", "board_rtl_or_testbench"),
            ("rtl_semantic_mismatch", "board_rtl_or_testbench"),
        )
        loop = {
            "failure_kind": "board_wrapper_or_pipeline_integration",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "arbitrary_board_gate", "status": "fail"}
            ],
        }
        for failure_class, repair_scope in repairable:
            with self.subTest(failure_class=failure_class):
                diagnosis = {
                    "status": "needs_repair",
                    "failure_class": failure_class,
                    "summary": "current structured board failure",
                    "repair_handoff": {
                        "agent_should_apply_code_changes": True,
                        "repair_scope": repair_scope,
                    },
                }
                actions = build_repair_actions(
                    [{"checker": "real_tool.arbitrary_board_gate", "status": "fail"}],
                    diagnosis,
                    {},
                    {"status": "localized"},
                    loop,
                )

                self.assertEqual(len(actions), 1)
                self.assertEqual(
                    actions[0]["repair_kind"],
                    "exact_board_integration_harness",
                )
                self.assertEqual(actions[0]["source"], "case_vcs_functional_diagnosis")

    def test_board_pipeline_contradiction_backtracks_to_single_layer(self) -> None:
        loop = {
            "failure_kind": "board_wrapper_or_pipeline_integration",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "case_vcs_functional_sim", "status": "fail"}
            ],
        }
        diagnosis = {
            "status": "needs_repair",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "summary": "all inputs completed with zero output",
            "failure_evidence": {
                "board_to_lower_layer_contradiction_evidence": {
                    "schema_version": (
                        "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1"
                    ),
                    "status": "proven",
                    "target_debug_layer": "single_transformer_layer_kernel",
                    "source_binding": {
                        "input_fingerprint_sha256": "a" * 64,
                        "board_trace_sha256": "b" * 64,
                        "lower_layer_certificate_sha256": "c" * 64,
                    },
                    "direct_kernel_boundary_observations": {
                        "kernel_start_accepted": True,
                        "kernel_ingress_complete": True,
                        "kernel_egress_ready": True,
                    },
                    "causal_localization": {
                        "earliest_causal_owner": "single_transformer_layer_kernel",
                        "named_contract_boundary_id": "edge.kernel.output",
                    },
                }
            },
            "repair_handoff": {
                "agent_should_apply_code_changes": True,
                "repair_scope": "board_axi_ddr_wrapped_system",
                "debug_layer": "board_axi_ddr_wrapped_system",
            },
        }

        actions = build_repair_actions(
            [{"checker": "real_tool.case_vcs_functional_sim", "status": "fail"}],
            diagnosis,
            {},
            {"status": "localized"},
            loop,
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "case_single_layer_functional")
        self.assertEqual(
            actions[0]["debug_layer"], "single_transformer_layer_kernel"
        )
        self.assertEqual(actions[0]["repair_gate"], "case_single_layer_functional")
        contradiction = actions[0]["minimal_repair_context"][
            "current_board_to_lower_layer_contradiction"
        ]
        self.assertEqual(contradiction["status"], "proven")
        self.assertEqual(
            contradiction["evidence"]["causal_localization"][
                "named_contract_boundary_id"
            ],
            "edge.kernel.output",
        )

    def test_completed_board_recheck_returns_to_board_only_for_same_binding(self) -> None:
        loop = {
            "failure_kind": "board_wrapper_or_pipeline_integration",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "case_vcs_functional_sim", "status": "fail"}
            ],
        }
        contradiction = {
            "status": "proven",
            "target_debug_layer": "single_transformer_layer_kernel",
            "evidence": {
                "status": "proven",
                "source_binding": {
                    "input_fingerprint_sha256": "a" * 64,
                    "board_trace_sha256": "b" * 64,
                    "lower_layer_certificate_sha256": "c" * 64,
                },
                "direct_kernel_boundary_observations": {
                    "kernel_start_accepted": True,
                    "kernel_ingress_complete": True,
                    "kernel_egress_ready": True,
                },
                "causal_localization": {
                    "earliest_causal_owner": "single_transformer_layer_kernel",
                    "named_contract_boundary_id": "edge.kernel.output",
                },
            },
        }
        diagnosis = {
            "status": "needs_repair",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "failure_evidence": {
                "board_to_lower_layer_contradiction_evidence": contradiction
            },
            "repair_handoff": {"agent_should_apply_code_changes": True},
        }
        with TemporaryDirectory(dir=Path.cwd()) as temporary:
            run_dir = Path(temporary)
            report_path = run_dir / "single_layer_report.json"
            report_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
                        "status": "pass",
                    }
                ),
                encoding="utf-8",
            )
            ledger = record_board_lower_layer_recheck(
                run_dir,
                contradiction,
                capability_reports=[
                    {
                        "path": str(report_path),
                        "status": "pass",
                    }
                ],
            )
            self.assertEqual(ledger["status"], "pass")
            self.assertEqual(
                completed_board_lower_layer_recheck(run_dir, contradiction)["status"],
                "pass",
            )
            with patch(
                "accagent.framework.stage_repair.board_to_lower_layer_contradiction_from_diagnosis",
                return_value=contradiction,
            ):
                consumed_actions = build_repair_actions(
                    [{"checker": "real_tool.case_vcs_functional_sim", "status": "fail"}],
                    diagnosis,
                    {},
                    {"status": "localized"},
                    loop,
                    run_dir,
                    {"executable": True},
                )

            changed_contradiction = json.loads(json.dumps(contradiction))
            changed_contradiction["evidence"]["source_binding"][
                "board_trace_sha256"
            ] = "d" * 64
            with patch(
                "accagent.framework.stage_repair.board_to_lower_layer_contradiction_from_diagnosis",
                return_value=changed_contradiction,
            ):
                changed_actions = build_repair_actions(
                    [{"checker": "real_tool.case_vcs_functional_sim", "status": "fail"}],
                    diagnosis,
                    {},
                    {"status": "localized"},
                    loop,
                    run_dir,
                    {"executable": True},
                )

        self.assertEqual(
            consumed_actions[0]["repair_kind"], "board_semantic_rtl_repair"
        )
        self.assertEqual(
            consumed_actions[0]["debug_layer"], "board_axi_ddr_wrapped_system"
        )
        self.assertEqual(
            consumed_actions[0]["minimal_repair_context"][
                "completed_board_lower_layer_recheck"
            ]["status"],
            "pass",
        )
        self.assertIsNone(
            consumed_actions[0]["minimal_repair_context"][
                "current_board_to_lower_layer_contradiction"
            ]
        )
        self.assertEqual(
            changed_actions[0]["repair_kind"], "case_single_layer_functional"
        )
        self.assertEqual(
            changed_actions[0]["debug_layer"], "single_transformer_layer_kernel"
        )

    def test_current_board_contradiction_overrides_stale_board_audit_routing(self) -> None:
        loop = {
            "failure_kind": "board_wrapper_or_pipeline_integration",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "case_axi_ddr_interface", "status": "fail"},
                {"name": "case_vcs_functional_sim", "status": "fail"},
            ],
        }
        diagnosis = {
            "status": "needs_repair",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "summary": "full ingress with no output",
            "failure_evidence": {
                "board_to_lower_layer_contradiction_evidence": {
                    "schema_version": (
                        "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1"
                    ),
                    "status": "proven",
                    "target_debug_layer": "single_transformer_layer_kernel",
                    "source_binding": {
                        "input_fingerprint_sha256": "a" * 64,
                        "board_trace_sha256": "b" * 64,
                        "lower_layer_certificate_sha256": "c" * 64,
                    },
                    "direct_kernel_boundary_observations": {
                        "kernel_start_accepted": True,
                        "kernel_ingress_complete": True,
                        "kernel_egress_ready": True,
                    },
                    "causal_localization": {
                        "earliest_causal_owner": "single_transformer_layer_kernel",
                        "named_contract_boundary_id": "edge.kernel.output",
                    },
                }
            },
            "repair_handoff": {
                "agent_should_apply_code_changes": True,
                "repair_scope": "board_axi_ddr_wrapped_system",
            },
        }
        actions = build_repair_actions(
            [{"checker": "real_tool.case_axi_ddr_interface", "status": "fail"}],
            diagnosis,
            {},
            {"status": "localized"},
            loop,
        )
        plan = {"repair_actions": actions}

        priority = authoritative_repair_routing_priority(plan)

        self.assertEqual(priority["status"], "authoritative")
        self.assertEqual(
            priority["required_repair_action"]["debug_layer"],
            "single_transformer_layer_kernel",
        )
        self.assertEqual(priority["proof"]["earliest_boundary"], "edge.kernel.output")
        self.assertTrue(exact_localized_repair_route(plan))

    def test_persisted_cross_layer_diagnosis_is_history_not_operator_action(self) -> None:
        failures = [
            {
                "checker": "real_tool.case_semantic_testbench",
                "status": "fail",
                "summary": "semantic testbench harness is missing",
            }
        ]
        diagnosis = {
            "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
            "status": "needs_repair",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "repair_handoff": {
                "debug_layer": "single_transformer_layer_kernel",
                "repair_scope": "single_transformer_layer_kernel",
                "must_rerun": [
                    "case_single_layer_functional",
                    "single_layer_pipeline_overlap",
                    "case_vcs_functional_sim",
                ],
            },
        }
        loop = {
            "failure_kind": "verification_capability_gap",
            "current_layer": {"id": "operator_leaf_modules"},
            "failed_current_layer_gates": [
                {"name": "case_semantic_testbench", "status": "fail"}
            ],
        }

        actions = build_repair_actions(
            failures,
            diagnosis,
            {},
            {"status": "verification_capability_gap"},
            loop,
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "semantic_loader_harness_binding")
        self.assertEqual(actions[0]["source"], "hierarchical_repair_loop")

    def test_source_bound_board_diagnosis_requires_live_hash_and_current_gate(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temporary:
            run_dir = Path(temporary)
            runner_path = run_dir / "verification" / "vcs" / "runner.json"
            runner_path.parent.mkdir(parents=True)
            runner_path.write_text('{"status":"fail"}\n', encoding="utf-8")
            diagnosis = {
                "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v3",
                "status": "needs_repair",
                "failure_class": "vcs_compile_failure",
                "repair_handoff": {
                    "agent_should_apply_code_changes": True,
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "repair_scope": "generated_source_or_compile_plan",
                    "must_rerun": ["case_vcs_functional_sim"],
                },
                "applicability_binding": {
                    "schema_version": "spatialaccagent.diagnosis_applicability_binding.v1",
                    "origin_layer": "board_axi_ddr_wrapped_system",
                    "target_layer": "board_axi_ddr_wrapped_system",
                    "origin_gates": ["case_vcs_functional_sim"],
                    "applicable_rerun_gates": ["case_vcs_functional_sim"],
                    "diagnosed_failure_class": "vcs_compile_failure",
                    "source_artifacts": [
                        {
                            "role": "board_vcs_runner_report",
                            "path": str(runner_path),
                            "sha256": hashlib.sha256(runner_path.read_bytes()).hexdigest(),
                        }
                    ],
                },
            }
            loop = {
                "failure_kind": "board_wrapper_or_pipeline_integration",
                "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                "failed_current_layer_gates": [
                    {"name": "case_vcs_functional_sim", "status": "fail"}
                ],
            }

            current = diagnosis_applicability_report(
                diagnosis, loop, run_dir=run_dir
            )
            runner_path.write_text('{"status":"different"}\n', encoding="utf-8")
            stale = diagnosis_applicability_report(
                diagnosis, loop, run_dir=run_dir
            )

        self.assertTrue(current["executable"])
        self.assertEqual(current["relation"], "current_origin_failure")
        self.assertFalse(stale["executable"])
        self.assertIn(
            "source_artifacts[0] live sha256 changed", stale["validation_errors"]
        )

    def test_diagnosis_reruns_only_current_failed_gate(self) -> None:
        diagnosis = {
            "status": "needs_repair",
            "root_cause_class": "pipeline_failure",
            "repair_handoff": {
                "debug_layer": "single_transformer_layer_kernel",
                "must_rerun": [
                    "case_single_layer_functional",
                    "single_layer_pipeline_overlap",
                    "case_vcs_functional_sim",
                ],
            },
        }
        loop = {
            "failure_kind": "integration_boundary_or_layer_interconnect",
            "current_layer": {"id": "single_transformer_layer_kernel"},
            "failed_current_layer_gates": [
                {"name": "case_single_layer_functional", "status": "fail"}
            ],
        }

        actions = build_repair_actions(
            [{"checker": "real_tool.case_single_layer_functional", "status": "fail"}],
            diagnosis,
            {},
            None,
            loop,
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "regression_rerun")
        self.assertEqual(actions[0]["tool"], "case_single_layer_functional")

    def test_repo_relative_diagnosis_path_is_not_prefixed_twice(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temporary:
            root = Path(temporary)
            diagnosis_path = root / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
            diagnosis_path.parent.mkdir(parents=True)
            diagnosis_path.write_text(
                json.dumps({"status": "needs_repair", "failure_class": "intra_layer_spatial_pipeline_violation"}),
                encoding="utf-8",
            )
            repo_relative = Path(os.path.relpath(diagnosis_path, Path.cwd()))
            adapter = {"diagnosis": {"path": str(repo_relative)}}
            with patch(
                "accagent.framework.stage_repair.case_adapter_for_state",
                return_value=adapter,
            ):
                loaded = load_vcs_diagnosis({}, root)

        self.assertEqual(
            loaded["failure_class"], "intra_layer_spatial_pipeline_violation"
        )

    def test_board_transport_tool_library_and_environment_failures_never_route_rtl(self) -> None:
        non_rtl = (
            (
                "remote_transport_failure",
                "remote_transport_retry",
                "remote_tool_transport_contract",
            ),
            (
                "tool_resolution_failure",
                "verification_capability",
                "tool_runtime_environment_contract",
            ),
            (
                "vcs_library_resolution_failure",
                "simulation_environment",
                "tool_runtime_environment_contract",
            ),
        )
        loop = {
            "failure_kind": "board_wrapper_or_pipeline_integration",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "arbitrary_board_gate", "status": "fail"}
            ],
        }
        for failure_class, repair_scope, expected_kind in non_rtl:
            with self.subTest(failure_class=failure_class):
                actions = build_repair_actions(
                    [{"checker": "real_tool.arbitrary_board_gate", "status": "fail"}],
                    {
                        "status": "needs_repair",
                        "failure_class": failure_class,
                        "repair_handoff": {
                            "agent_should_apply_code_changes": True,
                            "repair_scope": repair_scope,
                        },
                    },
                    {},
                    {"status": "localized"},
                    loop,
                )

                self.assertEqual(len(actions), 1)
                self.assertEqual(actions[0]["repair_kind"], expected_kind)
                self.assertNotEqual(
                    actions[0]["repair_kind"],
                    "exact_board_integration_harness",
                )

    def test_prelaunch_board_environment_failure_retries_same_vcs_chain(self) -> None:
        loop = {
            "failure_kind": "board_wrapper_or_pipeline_integration",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "case_vcs_functional_sim", "status": "fail"}
            ],
        }
        diagnosis = {
            "status": "needs_repair",
            "failure_class": "vcs_execution_environment_failure",
            "failure_evidence": {"repair_scope": "execution_environment_retry"},
        }
        actions = build_repair_actions(
            [],
            diagnosis,
            {},
            {"status": "localized"},
            loop,
            diagnosis_applicability={"executable": False},
        )
        self.assertEqual(actions[0]["scope"], "regression_rerun")
        self.assertEqual(actions[0]["tool"], "case_vcs_functional_sim")
        self.assertEqual(actions[0]["repair_kind"], "exact_board_environment_retry")

    def test_board_discovery_gap_routes_discovery_agent_without_rtl_repair(self) -> None:
        failures = [
            {
                "checker": "real_tool.case_board_interface_discovery",
                "status": "fail",
                "summary": "Vivado fact bundle could not be validated",
            }
        ]
        localization = {"status": "verification_capability_gap"}
        loop = {
            "failure_kind": "verification_capability_gap",
            "current_layer": {"id": "board_axi_ddr_wrapped_system"},
            "failed_current_layer_gates": [
                {"name": "case_board_interface_discovery", "status": "fail"}
            ],
        }

        actions = build_repair_actions(failures, None, {}, localization, loop)

        self.assertEqual(actions[0]["repair_kind"], "exact_board_interface_discovery")
        self.assertIn("without editing dut", actions[0]["reason"].lower())

    def test_cctg_repeated_internal_beats_do_not_crowd_out_numeric_evidence(self) -> None:
        traces = [
            {
                "status": "fail",
                "evidence_type": "semantic_internal_boundary_trace",
                "failure_class": "unknown_logic_value",
                "stage_id": "stage_01_self_attention",
                "boundary_id": "softmax_to_context",
                "module": "Softmax",
                "violated_contract": "internal_submodule_known_value_when_valid",
                "cycle": beat,
                "beat_index": beat,
            }
            for beat in range(24)
        ]
        traces.append(
            {
                "status": "fail",
                "evidence_type": "semantic_numeric_compare",
                "failure_class": "unknown_output_word",
                "stage_id": "stage_01_self_attention",
                "module": "Softmax",
                "violated_contract": "target_model_operator_semantics",
            }
        )

        localization = localize_failure({}, {"status": "fail", "results": []}, traces)

        self.assertEqual(localization["failure_record_count"], 25)
        self.assertEqual(localization["representative_failure_count"], 2)
        self.assertEqual(
            {row["evidence_type"] for row in localization["failed_boundaries"]},
            {"semantic_internal_boundary_trace", "semantic_numeric_compare"},
        )
        internal = localization["failed_boundaries"][0]
        self.assertEqual(internal["beat_index"], 0)
        self.assertEqual(internal["equivalent_failure_count"], 24)
        current_failure = {
            "results": [
                {
                    "checker": "real_tool.case_leaf_golden_compare",
                    "kind": "case_leaf_golden_compare",
                    "status": "fail",
                    "summary": "current independent golden numeric compare failed",
                }
            ]
        }
        self.assertEqual(failure_kind(localization, current_failure), "hardware_value_mismatch")

    def test_stale_numeric_localization_cannot_override_current_prerequisite_failure(self) -> None:
        localization = {
            "failed_boundaries": [
                {
                    "status": "fail",
                    "evidence_type": "semantic_numeric_compare",
                    "failure_class": "unknown_logic_value",
                    "stage_id": "stage_01_self_attention",
                    "module": "Softmax",
                }
            ]
        }
        current = {
            "results": [
                {
                    "checker": "real_tool.case_target_model_reference",
                    "kind": "target_model_reference_generate",
                    "status": "fail",
                    "summary": "required Python environment unavailable: No module named transformers",
                },
                {
                    "checker": "real_tool.case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "status": "not_run",
                    "summary": "skipped because dependency gate(s) are not pass: ['case_target_model_reference']",
                },
            ]
        }

        self.assertEqual(failure_kind(localization, current), "verification_capability_gap")

    def test_remote_transport_failure_cannot_reopen_stale_rtl_localization(self) -> None:
        localization = {
            "failed_boundaries": [
                {
                    "status": "fail",
                    "evidence_type": "semantic_numeric_compare",
                    "failure_class": "unknown_logic_value",
                    "stage_id": "stage_01_self_attention",
                    "module": "Softmax",
                }
            ]
        }
        current = {
            "results": [
                {
                    "checker": "real_tool.case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "status": "fail",
                    "summary": "remote VCS transport failed before a hardware verdict was available",
                }
            ]
        }

        self.assertEqual(failure_kind(localization, current), "verification_tool_transport_failure")

    def test_conditional_mode_skips_post_execution_review_without_decision_value(self) -> None:
        with TemporaryDirectory() as td, patch.dict(
            "os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}
        ), patch("accagent.framework.stage_repair_execute.run_stage_agent") as llm:
            record = run_optional_post_execution_review(
                agent="causal_slice_repair_agent",
                task="classify an already executed replay",
                inputs={"replay": {"status": "fail"}},
                out_dir=Path(td),
                fallback_summary="review unavailable",
                deterministic_summary="real replay status determines this execution step",
            )
            self.assertTrue(Path(record["result_path"]).is_file())

        llm.assert_not_called()
        self.assertTrue(record["llm_skipped"])
        self.assertEqual(record["mode"], "deterministic_conditional_route")

    def test_full_mode_keeps_post_execution_review(self) -> None:
        expected = {"result_path": "full-review.json", "output": {"status": "ready"}}
        with TemporaryDirectory() as td, patch.dict(
            "os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "full"}
        ), patch(
            "accagent.framework.stage_repair_execute.run_stage_agent", return_value=expected
        ) as llm:
            record = run_optional_post_execution_review(
                agent="causal_slice_repair_agent",
                task="classify an already executed replay",
                inputs={"replay": {"status": "fail"}},
                out_dir=Path(td),
                fallback_summary="review unavailable",
                deterministic_summary="unused in full mode",
            )

        llm.assert_called_once()
        self.assertEqual(record, expected)

    def test_semantic_binding_hash_mismatch_is_capability_gap_not_hardware_mismatch(self) -> None:
        result = {
            "results": [
                {
                    "checker": "real_tool.case_semantic_testbench",
                    "status": "fail",
                    "summary": (
                        "DUT weight-binding manifest status is not pass; "
                        "source_checkpoint_sha256 does not match verification preparation; "
                        "explicit numeric comparison atol/rtol/max_mismatch_fraction is missing"
                    ),
                }
            ]
        }

        self.assertEqual(failure_kind({}, result), "verification_capability_gap")
        localization = localize_failure({"boundaries": []}, result | {"status": "fail"}, [])
        self.assertEqual(localization["status"], "verification_capability_gap")
        self.assertEqual(
            localization["minimal_repair_context"]["repair_scope"],
            "verification_capability_repair",
        )

    def test_operator_layer_report_includes_semantic_preparation_and_aggregate(self) -> None:
        result = {
            "hierarchical_gate_summary": {
                "required_gates": [
                    {"name": "case_real_weight_artifacts", "status": "pass"},
                    {"name": "case_target_model_reference", "status": "pass"},
                    {"name": "case_semantic_testbench", "status": "fail"},
                    {"name": "boundary_contract_check", "status": "pass"},
                ]
            },
            "results": [
                {
                    "checker": "real_tool.case_semantic_testbench",
                    "status": "fail",
                    "summary": "semantic testbench manifest status is incomplete",
                }
            ],
        }

        report = build_repair_loop_report(verification_result=result, debug_localization={})

        self.assertEqual(report["current_layer"]["id"], "operator_leaf_modules")
        self.assertEqual(report["failure_kind"], "verification_capability_gap")
        names = {row["name"] for row in report["failed_current_layer_gates"]}
        self.assertIn("case_semantic_testbench", names)
        self.assertIn("case_operator_leaf_semantic_evidence", names)

    def test_completed_leaf_scope_does_not_route_pending_higher_layers_to_repair(self) -> None:
        leaf_gates = [
            "case_real_weight_artifacts",
            "case_target_model_reference",
            "case_semantic_testbench",
            "case_stage_leaf_static",
            "boundary_contract_check",
            "case_leaf_functional",
            "case_leaf_golden_compare",
            "case_operator_leaf_semantic_evidence",
        ]
        single_layer_gates = [
            "single_transformer_layer",
            "case_single_layer_functional",
            "case_single_layer_golden_compare",
            "case_single_layer_semantic_evidence",
        ]
        board_gates = [
            "case_board_interface_discovery",
            "case_multilayer_pipeline",
            "case_multilayer_functional",
            "case_pipeline_deadlock_check",
            "case_axi_ddr_interface",
            "case_axi_protocol_check",
            "case_ddr_image_roundtrip",
            "functional_sim",
            "case_board_semantic_evidence",
        ]
        verification = {
            "gate_execution_scope": "operator_leaf_closure",
            "hierarchical_gate_summary": {
                "required_gates": [
                    *({"name": gate, "status": "pass"} for gate in leaf_gates),
                    *(
                        {"name": gate, "status": "pending_later_stage"}
                        for gate in [*single_layer_gates, *board_gates]
                    ),
                ]
            },
            "results": [],
        }

        report = build_repair_loop_report(verification_result=verification, debug_localization={})

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["failure_kind"], "none")
        self.assertEqual(report["current_layer"]["id"], "operator_leaf_modules")
        self.assertEqual(
            [layer["status"] for layer in report["layers"]],
            ["pass", "pending_later_stage", "pending_later_stage"],
        )
        self.assertEqual(report["failed_current_layer_gates"], [])
        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertIsNone(
                verification_specialist_trigger(
                    verification | {"hierarchical_repair_loop": report}
                )
            )

    def test_board_trace_tool_is_rejected_for_lower_debug_layers(self) -> None:
        capability = {
            "capabilities": [
                "boundary_trace",
                "all_target_layers",
                "board_wrapper_functional_sim",
                "exact_sample_board_wrapper_simulation",
            ]
        }

        self.assertIsNotNone(boundary_trace_scope_error("operator_leaf_modules", capability))
        self.assertIsNotNone(boundary_trace_scope_error("single_transformer_layer_kernel", capability))
        self.assertIsNone(boundary_trace_scope_error("board_axi_ddr_wrapped_system", capability))

    def test_unambiguous_capability_gap_skips_fixed_specialist_fanout(self) -> None:
        verification = {
            "gate_execution_scope": "operator_leaf_closure",
            "hierarchical_repair_loop": {
                "failure_kind": "verification_capability_gap",
                "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
            },
        }
        repair = {
            "diagnostics": {
                "hierarchical_repair_loop": {
                    "failure_kind": "verification_capability_gap",
                    "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
                }
            }
        }
        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertIsNone(verification_specialist_trigger(verification))
            self.assertIsNone(repair_specialist_trigger(repair))
        self.assertEqual(team_failure_errors(no_split_review_summary("verification", "unambiguous")), [])

    def test_board_capability_gap_skips_targeted_specialist(self) -> None:
        verification = {
            "gate_execution_scope": "board_axi_ddr_closure",
            "hierarchical_repair_loop": {
                "failure_kind": "verification_capability_gap",
                "lower_layer_evidence_challenge": {
                    "status": "no_lower_layer_challenge"
                },
            },
        }

        with patch.dict(
            "os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}
        ):
            self.assertIsNone(verification_specialist_trigger(verification))

    def test_complex_or_board_evidence_routes_one_targeted_specialist(self) -> None:
        verification = {
            "gate_execution_scope": "board_axi_ddr_closure",
            "hierarchical_repair_loop": {
                "failure_kind": "board_wrapper_or_pipeline_integration",
                "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
            },
        }
        repair = {
            "diagnostics": {
                "hierarchical_repair_loop": {
                    "failure_kind": "hardware_value_mismatch",
                    "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
                }
            }
        }
        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertEqual(verification_specialist_trigger(verification), "board_wrapper_or_pipeline_integration")
            self.assertEqual(repair_specialist_trigger(repair), "hardware_value_mismatch")

    def test_targeted_verification_specialist_receives_source_state_for_learning_context(self) -> None:
        results = {
            "execution_scope": "board_axi_ddr_closure",
            "hierarchical_repair_loop": {
                "failure_kind": "board_wrapper_or_pipeline_integration",
                "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
            },
        }
        worker_result = {
            "output": {"executable_actions": []},
            "used_fallback": False,
            "result_path": "/persistent/verification_targeted_specialist.json",
            "error": None,
        }
        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            with patch(
                "accagent.framework.stage_verification.run_stage_agent",
                return_value=worker_result,
            ) as worker:
                run_verification_review_team(
                    {},
                    results,
                    Path("/persistent/out"),
                    source_sacg_state=Path("/persistent/verification/sacg_state.json"),
                )

        self.assertEqual(
            worker.call_args.kwargs["inputs"]["source_sacg_state"],
            "/persistent/verification/sacg_state.json",
        )

    def test_targeted_repair_specialist_receives_source_state_for_learning_context(self) -> None:
        repair_plan = {
            "diagnostics": {
                "hierarchical_repair_loop": {
                    "failure_kind": "hardware_value_mismatch",
                    "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
                }
            }
        }
        worker_result = {
            "output": {"status": "ready", "executable_actions": []},
            "used_fallback": False,
            "result_path": "/persistent/repair_targeted_specialist.json",
            "error": None,
        }
        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            with patch(
                "accagent.framework.stage_repair.run_stage_agent",
                return_value=worker_result,
            ) as worker:
                run_repair_review_team(
                    {},
                    repair_plan,
                    Path("/persistent/out"),
                    source_sacg_state=Path("/persistent/repair/sacg_state.json"),
                )

        self.assertEqual(
            worker.call_args.kwargs["inputs"]["source_sacg_state"],
            "/persistent/repair/sacg_state.json",
        )

    def test_localized_leaf_semantic_action_skips_redundant_repair_specialist(self) -> None:
        repair = {
            "diagnostics": {
                "hierarchical_repair_loop": {
                    "failure_kind": "hardware_value_mismatch",
                    "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
                }
            },
            "repair_actions": [
                {
                    "scope": "verification_capability_repair",
                    "repair_kind": "localized_semantic_dut_repair",
                }
            ],
        }

        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertIsNone(repair_specialist_trigger(repair))

    def test_single_layer_pipeline_backtrack_skips_redundant_repair_review(self) -> None:
        repair = {
            "diagnostics": {
                "hierarchical_repair_loop": {
                    "failure_kind": "board_wrapper_or_pipeline_integration",
                    "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
                }
            },
            "repair_actions": [
                {
                    "scope": "verification_capability_repair",
                    "repair_kind": "case_single_layer_functional",
                    "debug_layer": "single_transformer_layer_kernel",
                    "approval_required": False,
                }
            ],
        }

        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertIsNone(repair_specialist_trigger(repair))
            self.assertFalse(exact_localized_repair_route(repair))

    def test_exact_failed_stage7_route_skips_only_impossible_promotion_review(self) -> None:
        result = {
            "status": "fail",
            "hierarchical_repair_loop": {
                "status": "needs_repair",
                "failure_kind": "hardware_value_mismatch",
                "root_candidate_module": "AttentionGQA",
                "violated_contract": "internal_submodule_ready_valid_data",
                "agent_runtime_llm_blocker": False,
                "current_layer": {"status": "needs_repair"},
                "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
            },
        }

        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertTrue(exact_failed_stage7_route(result))
        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "full"}):
            self.assertFalse(exact_failed_stage7_route(result))
        self.assertFalse(exact_failed_stage7_route({**result, "status": "pass"}))

    def test_exact_localized_repair_route_requires_internal_and_numeric_evidence(self) -> None:
        trace = {
            "status": "fail",
            "evidence_type": "semantic_internal_boundary_trace",
            "stage_id": "stage_01_self_attention",
            "module": "AttentionGQA",
            "boundary_id": "attention_out",
            "violated_contract": "internal_submodule_known_value_when_valid",
        }
        plan = {
            "diagnostics": {
                "hierarchical_repair_loop": {
                    "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"}
                }
            },
            "repair_actions": [
                {
                    "scope": "verification_capability_repair",
                    "repair_kind": "localized_semantic_dut_repair",
                    "approval_required": False,
                    "minimal_repair_context": {"trace_record": trace},
                    "corroborating_semantic_numeric_failure": {
                        "status": "fail",
                        "evidence_type": "semantic_numeric_compare",
                        "stage_id": "stage_01_self_attention",
                    },
                }
            ],
        }

        with patch.dict("os.environ", {"SPATIALACC_VALIDATION_LLM_TEAM_MODE": "conditional"}):
            self.assertTrue(exact_localized_repair_route(plan))
            plan["repair_actions"][0]["corroborating_semantic_numeric_failure"] = {}
            self.assertFalse(exact_localized_repair_route(plan))

    def test_exact_board_compile_failure_routes_directly_to_implementation_agent(self) -> None:
        plan = {
            "repair_actions": [{
                "repair_kind": "exact_board_integration_harness",
                "scope": "verification_capability_repair",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "approval_required": False,
            }],
            "diagnostics": {
                "case_vcs_functional": {
                    "failure_class": "vcs_compile_failure",
                    "failure_evidence": {
                        "first_real_error": "Error-[IND] Identifier not declared",
                    },
                },
            },
        }

        self.assertTrue(exact_localized_repair_route(plan))

    def test_llm_approval_disposition_freezes_precompiled_workflow(self) -> None:
        plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [{"id": "repair_step.00", "status": "ready_to_execute", "scope": "debug_trace_rerun"}],
                "blockers": [],
                "approval_steps": [],
            }
        }
        output = {
            "status": "blocked_pending_approved_stage6_backtrack",
            "summary": "First obtain approval for an immutable numeric contract; reject the candidate plan.",
            "executable_actions": [
                {
                    "id": "stage8.request_numeric_policy_backtrack",
                    "action_type": "numeric_policy_approval_backtrack_request",
                    "requires_approval": True,
                }
            ],
        }

        reconciled = reconcile_repair_workflow_with_llm(plan, output)
        workflow = reconciled["repair_workflow"]

        self.assertEqual(workflow["status"], "approval_required")
        self.assertEqual(workflow["steps"][0]["status"], "blocked_by_llm_disposition")
        self.assertTrue(workflow["llm_disposition"]["vetoed_pre_llm_execution"])

    def test_read_only_vcs_provenance_approval_cannot_block_its_producer(self) -> None:
        plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [{
                    "id": "repair_step.00",
                    "status": "ready_for_agent_patch",
                    "scope": "verification_capability_repair",
                    "action": {
                        "repair_kind": "vcs_compile_diagnostic_source_provenance",
                        "approval_required": False,
                    },
                }],
                "blockers": [],
                "approval_steps": [],
            }
        }
        output = {
            "status": "needs_repair",
            "summary": "Read the preserved compile diagnostic before choosing any source repair.",
            "executable_actions": [{
                "id": "repair_step.01_vcs_compile_diagnostic_source_provenance",
                "action_type": "verification_capability_repair",
                "requires_approval": True,
            }],
        }

        workflow = reconcile_repair_workflow_with_llm(plan, output)["repair_workflow"]

        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(workflow["steps"][0]["status"], "ready_for_agent_patch")
        self.assertFalse(workflow["llm_disposition"]["vetoed_pre_llm_execution"])
        self.assertEqual(
            workflow["llm_disposition"]["auto_executable_read_only_capability_action_ids"],
            ["repair_step.01_vcs_compile_diagnostic_source_provenance"],
        )

    def test_persisted_read_only_vcs_provenance_veto_is_recovered(self) -> None:
        plan = {
            "repair_workflow": {
                "status": "approval_required",
                "blockers": ["stale veto"],
                "approval_steps": ["repair_step.01_vcs_compile_diagnostic_source_provenance"],
                "steps": [{
                    "status": "blocked_by_llm_disposition",
                    "pre_llm_status": "ready_for_agent_patch",
                    "scope": "verification_capability_repair",
                    "action": {
                        "repair_kind": "vcs_compile_diagnostic_source_provenance",
                        "approval_required": False,
                    },
                }],
                "llm_disposition": {
                    "summary": "stale veto",
                    "active_approval_action_ids": ["repair_step.01_vcs_compile_diagnostic_source_provenance"],
                    "executable_actions": [{
                        "id": "repair_step.01_vcs_compile_diagnostic_source_provenance",
                        "action_type": "verification_capability_repair",
                        "requires_approval": True,
                    }],
                },
            }
        }

        self.assertTrue(restore_persisted_read_only_capability_steps(plan))
        workflow = plan["repair_workflow"]
        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(workflow["steps"][0]["status"], "ready_for_agent_patch")
        self.assertEqual(workflow["llm_disposition"]["active_approval_action_ids"], [])

    def test_exact_action_id_approval_unblocks_only_that_action(self) -> None:
        action_id = "approval.implement_vcs_termination_provenance_capability"
        plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "status": "ready_to_execute",
                        "scope": "verification_capability_repair",
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            }
        }
        output = {
            "status": "blocked_pending_human",
            "summary": "First obtain approval for the system capability.",
            "executable_actions": [
                {
                    "id": action_id,
                    "action_type": "system_capability_gap",
                    "requires_approval": True,
                }
            ],
        }

        with patch.dict(
            os.environ,
            {"SPATIALACC_APPROVED_REPAIR_ACTION_IDS": action_id},
        ):
            workflow = reconcile_repair_workflow_with_llm(plan, output)[
                "repair_workflow"
            ]

        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(workflow["steps"][0]["status"], "ready_to_execute")
        self.assertEqual(
            workflow["llm_disposition"]["approved_action_ids"], [action_id]
        )
        self.assertEqual(
            workflow["llm_disposition"]["active_approval_action_ids"], []
        )
        self.assertEqual(
            workflow["llm_disposition"]["deferred_approval_action_ids"], []
        )
        self.assertFalse(
            workflow["llm_disposition"]["vetoed_pre_llm_execution"]
        )

    def test_conditional_approval_does_not_block_current_repair(self) -> None:
        plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "status": "ready_to_execute",
                        "scope": "verification_capability_repair",
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            }
        }
        output = {
            "status": "needs_repair",
            "summary": "Repair current discovery first; no approval is currently requested.",
            "executable_actions": [
                {
                    "id": "repair.board_target_ambiguity_approval",
                    "action_type": "conditional_human_boundary_approval",
                    "requires_approval": True,
                }
            ],
        }

        reconciled = reconcile_repair_workflow_with_llm(plan, output)
        workflow = reconciled["repair_workflow"]

        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(workflow["steps"][0]["status"], "ready_to_execute")
        self.assertFalse(workflow["llm_disposition"]["vetoed_pre_llm_execution"])
        self.assertEqual(
            workflow["llm_disposition"]["executable_actions"],
            output["executable_actions"],
        )
        self.assertEqual(
            workflow["llm_disposition"]["deferred_approval_action_ids"],
            ["repair.board_target_ambiguity_approval"],
        )

    def test_approval_waits_for_explicit_current_plan_dependency(self) -> None:
        plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "status": "ready_for_agent_patch",
                        "scope": "verification_capability_repair",
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            }
        }
        output = {
            "status": "needs_repair",
            "summary": "Repair the current gate before requesting a new tool capability.",
            "executable_actions": [
                {
                    "id": "repair.rerun_current_axi_ddr_interface_gate",
                    "action_type": "targeted_failed_checker_rerun",
                    "requires_approval": False,
                },
                {
                    "id": "repair.establish_remote_vcs_termination_provenance",
                    "action_type": "system_capability_gap",
                    "consumes": [
                        "pass report from repair.rerun_current_axi_ddr_interface_gate"
                    ],
                    "requires_approval": True,
                },
            ],
        }

        workflow = reconcile_repair_workflow_with_llm(plan, output)[
            "repair_workflow"
        ]

        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(workflow["steps"][0]["status"], "ready_for_agent_patch")
        self.assertEqual(
            workflow["llm_disposition"]["active_approval_action_ids"], []
        )
        self.assertEqual(
            workflow["llm_disposition"]["deferred_approval_action_ids"],
            ["repair.establish_remote_vcs_termination_provenance"],
        )

    def test_approval_waits_for_pending_produced_artifact(self) -> None:
        plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "status": "ready_to_execute",
                        "scope": "verification_capability_repair",
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            }
        }
        output = {
            "status": "needs_repair",
            "summary": "Run evidence collection before any conditional repair.",
            "executable_actions": [
                {
                    "id": "repair.collect_current_causal_slice",
                    "action_type": "contract_guided_localization",
                    "produces": ["artifact.stage8.causal_repair_context"],
                    "requires_approval": False,
                },
                {
                    "id": "repair.apply_future_causal_slice",
                    "action_type": "causal_slice_repair",
                    "consumes": ["artifact.stage8.causal_repair_context"],
                    "requires_approval": True,
                },
            ],
        }

        workflow = reconcile_repair_workflow_with_llm(plan, output)[
            "repair_workflow"
        ]

        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(
            workflow["llm_disposition"]["active_approval_action_ids"], []
        )
        self.assertEqual(
            workflow["llm_disposition"]["deferred_approval_action_ids"],
            ["repair.apply_future_causal_slice"],
        )
