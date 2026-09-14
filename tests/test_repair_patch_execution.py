import argparse
import copy
import json
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.board_validation_scope import (
    PREFIX_MODEL_MODE,
    resolve_board_validation_scope,
)
from accagent.framework.stage_repair_execute import (
    BOARD_INTEGRATION_REPAIR_SCHEMA,
    BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA,
    IMPLEMENTATION_REPAIR_SCHEMA,
    SEMANTIC_TEMPLATE_REPAIR_PHASES,
    _attested_exact_board_generation_provenance,
    _board_lower_layer_recheck_required,
    _incomplete_output_frontier_boundary,
    _exact_board_simulator_compile_input,
    all_applied_semantic_source_hash_changes,
    applied_semantic_source_hash_changes,
    apply_agent_file_edits,
    begin_existing_adaptive_observation_probe_replay,
    adaptive_observation_routing_state,
    canonical_contract_sha256,
    canonicalize_exact_board_manifest_declarations,
    archived_exact_board_vcs_feedback,
    authoritative_board_weight_artifact,
    add_external_fixture_sources_to_repair_bundle,
    authorize_localized_semantic_repair_bundle,
    bind_framework_vcs_compile_plan,
    board_harness_bootstrap_required,
    current_exact_board_bootstrap_generation_applied,
    board_integration_repair_context,
    board_integration_prompt_rules,
    board_kernel_lifecycle_generation_authority,
    capability_scope_prompt_rules,
    capability_repair_source_bundle,
    checkpoint_hook_prompt_rules,
    checkpoint_hook_specialist_package,
    checkpoint_framework_authority_rebind_status,
    checkpoint_specialist_route_required,
    completed_template_instrumentation_cleanup_plan,
    connected_binding_requirements_ready,
    configured_sbt_heap_mb,
    current_agent_patch_application_feedback,
    current_board_runtime_frontier_static_repair_guard,
    current_fresh_exact_source_provenance_replay_feedback,
    current_repair_agent_disposition,
    current_board_evidence_postdates_applied_patch,
    current_exact_board_preflight_execution_authority,
    current_exact_board_preflight_supersedes_manifest_failure,
    current_exact_board_validation_evidence,
    exact_board_vcs_feedback,
    exact_board_agent_task,
    exact_board_probe_agent_handoff_identity,
    exact_board_probe_requires_agent_continuation,
    exact_board_preflight_feedback,
    exact_board_repair_attempt_history,
    exact_board_repair_execution_projection_sha256,
    exact_board_source_state,
    exact_board_vcs_runner_feedback_is_current,
    enforce_board_observation_only_validation,
    existing_board_manifest_refresh_ready,
    finalize_dut_weight_binding_manifest,
    frozen_compute_slot_repair_compile_authority,
    frozen_failed_runner_matches_current_execution_semantics,
    has_interface_data_identity_path,
    harness_contract_errors,
    legal_direct_observation_stop,
    localized_instrumentation_probe_evidence,
    localized_single_layer_repair_route,
    matching_failed_exact_board_attempt,
    matching_failed_exact_board_functional_state,
    materialize_declared_template_documents,
    materialize_adaptive_observation_evidence,
    normalize_harness_sources,
    optional_checkpoint_reclassification_required,
    prepare_external_simulation_fixture_context,
    persist_adaptive_observation_request,
    pending_checkpoint_specialist_executor_retry,
    prefer_archived_exact_board_source_provenance,
    rebind_changed_source_hashes_in_manifest,
    rebind_applied_semantic_source_manifests,
    prepare_stage3_checkpoint_probe_environment,
    prior_resource_validation_resume_allowed,
    persist_current_exact_board_failed_attempt,
    repair_step_checkpoint,
    repair_loop_evidence_paths,
    repair_loop_disposition,
    recover_certified_frozen_compute_slot_authority,
    recover_archived_exact_board_source_provenance,
    rebind_manifest_checkpoint_framework_authority,
    reconcile_operator_leaf_certificate_scope_continuity,
    reusable_operator_leaf_promotion_certificate,
    scoped_capability_probe_paths,
    retryable_current_exact_board_generation_record,
    retryable_current_checkpoint_specialist_record,
    resume_prior_resource_failed_validation,
    run_repair_loop,
    run_local_tool,
    run_agent_requested_validation,
    run_exact_board_validation_chain,
    select_changed_input_dependency_producer,
    select_capability_tool,
    select_exact_board_validation_tools,
    select_trusted_exact_board_generation_record,
    semantic_phase_source_bundle,
    semantic_phase_prerequisite_errors,
    semantic_trace_report_snapshot,
    sha256_file,
    existing_adaptive_observation_probe_replay_ready,
    single_layer_probe_agent_handoff,
    single_layer_pipeline_trace_record,
    skip_initial_exact_board_pre_patch,
    snapshot_current_real_tool_failure,
    stale_static_board_authority_repair_blockers,
    summarize_leaf_report,
    trace_record_from_step,
    trusted_exact_board_generation_record,
    validate_adaptive_observation_decision,
    verification_scope_for_step,
)
from accagent.framework.stage_repair_execute import (
    _loop_counter_observation_binding_check,
    _diagnostic_signal_binding_check,
)

from accagent.framework.stage_repair_execute import execute_repair
from accagent.framework.llm_io import validate_schema
from accagent.framework.semantic_simulator import SEMANTIC_STALL_EXIT_CODE
from accagent.framework.stage_llm import compact_verification_capability_repair_package
from accagent.framework.verification_evidence_contract import (
    PROMOTION_CERTIFICATE_SCHEMA_VERSION,
    PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
    certificate_contract_errors,
    certificate_contract_fingerprint,
    evidence_contract_for_level,
    promotion_evidence_binding_fingerprint,
    tool_environment_contract,
)
from scripts.verification.semantic_testbench_generator import dut_binding_errors
from scripts.verification.case_board_vcs_functional import (
    preflight_manifest_projection_sha256,
)


BOARD_VCS_RUNNER_SHA256 = hashlib.sha256(
    (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "verification"
        / "case_board_vcs_functional.py"
    ).read_bytes()
).hexdigest()


class RepairPatchExecutionTest(TestCase):
    def test_optional_diagnostic_signal_bindings_must_be_materialized(self) -> None:
        bindings = {
            "edge.output": {
                "diagnostic_sources": [
                    {
                        "name": "mlp_state",
                        "role": "state",
                        "expression": "dut.mlp_state",
                    },
                    {
                        "name": "queue_count",
                        "role": "queue",
                        "expression": "dut.queue_count",
                    },
                ]
            }
        }

        valid = _diagnostic_signal_binding_check(
            bindings,
            {"edge.output"},
            ["logic mlp_state; logic queue_count; dut.mlp_state dut.queue_count"],
        )
        invalid = _diagnostic_signal_binding_check(
            bindings,
            {"edge.output"},
            ["logic mlp_state;"],
        )

        self.assertEqual(valid["status"], "pass")
        self.assertEqual(valid["binding_count"], 2)
        self.assertEqual(valid["direct_signal_count"], 2)
        self.assertEqual(invalid["status"], "blocked")
        self.assertTrue(any("queue_count" in value for value in invalid["blockers"]))

    def test_missing_diagnostic_signal_bindings_force_a_fresh_observation(self) -> None:
        result = _diagnostic_signal_binding_check(
            {"edge.output": {}},
            {"edge.output"},
            ["logic dut_ready;"],
        )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["binding_count"], 0)
        self.assertTrue(any("at least" in value for value in result["blockers"]))

    def test_lower_layer_recheck_is_required_only_for_explicit_board_contradiction(self) -> None:
        self.assertFalse(
            _board_lower_layer_recheck_required(
                {"status": "insufficient_evidence"},
                {"status": "not_found"},
            )
        )
        self.assertTrue(
            _board_lower_layer_recheck_required(
                {"status": "proven"},
                {"status": "not_found"},
            )
        )
        self.assertFalse(
            _board_lower_layer_recheck_required(
                {"status": "proven"},
                {"status": "pass"},
            )
        )

    def test_incomplete_output_frontier_is_a_stopped_boundary(self) -> None:
        boundary = {
            "boundary_id": "edge.output",
            "kind": "output",
            "transfer_observed": True,
        }
        causal_slice = {
            "earliest_unproven_frontier": {
                "frontier_id": "kernel_output_stream_completion",
                "status": "earliest_unproven",
                "observed": {"output_started": 1, "output_completed": 0},
            }
        }

        stopped = _incomplete_output_frontier_boundary(boundary, causal_slice)

        self.assertEqual(stopped["boundary_id"], "edge.output")
        self.assertEqual(stopped["status"], "incomplete_output_stream")
        self.assertEqual(
            stopped["stopped_by"], "hash_bound_sacg_cctg_frontier"
        )
        self.assertIsNone(
            _incomplete_output_frontier_boundary(
                boundary,
                {
                    "earliest_unproven_frontier": {
                        "frontier_id": "kernel_output_stream_completion",
                        "status": "earliest_unproven",
                        "observed": {"output_started": 1, "output_completed": 1},
                    }
                },
            )
        )

    def test_incomplete_transferring_boundary_routes_to_observation_only(self) -> None:
        package = {
            "current_board_vcs_feedback": {
                "status": "ready",
                "diagnosis": {
                    "value": {
                        "failure_evidence": {
                            "pipeline_boundary_observation": {
                                "status": "incomplete",
                                "required_boundary_count": 1,
                                "observed_boundary_count": 1,
                                "incomplete_boundary_ids": ["edge.input.to.output"],
                                "missing_boundary_ids": [],
                                "boundary_summaries": [
                                    {
                                        "boundary_id": "edge.input.to.output",
                                        "transfer_observed": True,
                                        "accepted_count_max": 0,
                                        "accepted_count_lower_bound": 1,
                                        "observation_complete": False,
                                    }
                                ],
                            }
                        }
                    }
                },
            }
        }

        routing = adaptive_observation_routing_state(package)

        self.assertEqual(
            routing["status"], "complete_boundary_coverage_required"
        )
        self.assertEqual(
            routing["incomplete_boundary_ids"], ["edge.input.to.output"]
        )

    def test_observation_only_rejects_rtl_edit_and_empty_probe_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            testbench = board_dir / "BoardTb.sv"
            wrapper = board_dir / "BoardAdapter.v"
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            wrapper.write_text("module BoardAdapter; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            passed_validation = {
                "status": "pass",
                "mode": "deepen_simulation_observation",
                "blockers": [],
            }
            rtl_edit = enforce_board_observation_only_validation(
                passed_validation,
                {
                    "file_edits": [{"path": str(wrapper)}],
                    "adaptive_observation_decision": {
                        "mode": "deepen_simulation_observation"
                    },
                },
                run_dir,
            )
            empty_replay = enforce_board_observation_only_validation(
                passed_validation,
                {
                    "file_edits": [],
                    "adaptive_observation_decision": {
                        "mode": "deepen_simulation_observation"
                    },
                },
                run_dir,
            )

        self.assertEqual(rtl_edit["status"], "blocked")
        self.assertTrue(
            any("declared testbench, monitor, or manifest" in value for value in rtl_edit["blockers"])
        )
        self.assertEqual(empty_replay["status"], "blocked")
        self.assertTrue(
            any("replaying an old probe" in value for value in empty_replay["blockers"])
        )

    def test_repair_ready_with_edit_is_executable(self) -> None:
        from accagent.framework.stage_repair_execute import (
            normalized_implementation_agent_status,
        )

        output = {
            "status": "repair_ready",
            "approval_required_for": [],
            "blocked_reasons": [],
            "file_edits": [{"path": "ElementwiseMul.sv", "operation": "replace_text"}],
        }
        self.assertEqual(
            normalized_implementation_agent_status(output), "ready_to_apply"
        )

    def test_repair_ready_without_edit_or_with_blocker_is_not_executable(self) -> None:
        from accagent.framework.stage_repair_execute import (
            normalized_implementation_agent_status,
        )

        no_edit = {
            "status": "repair_ready",
            "approval_required_for": [],
            "blocked_reasons": [],
            "file_edits": [],
        }
        blocked = {
            "status": "repair_ready",
            "approval_required_for": [],
            "blocked_reasons": ["missing evidence"],
            "file_edits": [{"path": "ElementwiseMul.sv", "operation": "replace_text"}],
        }
        self.assertEqual(normalized_implementation_agent_status(no_edit), "repair_ready")
        self.assertEqual(normalized_implementation_agent_status(blocked), "repair_ready")

    def test_repair_execution_skip_cannot_report_ready(self) -> None:
        disposition = repair_loop_disposition(
            {
                "status": "incomplete",
                "errors": ["repair_step.00: blocked by planner"],
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "result": {
                            "status": "skip",
                            "summary": "step status/scope not executable: blocked_by_llm_disposition/verification_capability_repair",
                        },
                    }
                ],
            }
        )
        self.assertEqual(disposition["status"], "blocked")
        self.assertIn("did not pass", disposition["summary"])

    def test_current_repair_agent_disposition_binds_current_step(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            repair_dir = run_dir / "repair"
            repair_dir.mkdir()
            repair_plan = {
                "repair_workflow": {
                    "status": "ready",
                    "steps": [
                        {
                            "id": "repair_step.00",
                            "scope": "verification_capability_repair",
                        }
                    ],
                    "llm_disposition": {
                        "status": "needs_repair",
                        "summary": "regenerate current board metadata",
                        "executable_actions": [
                            {
                                "id": "repair.board_metadata",
                                "action_type": "verification_capability_repair",
                            }
                        ],
                        "approval_action_ids": [],
                        "active_approval_action_ids": [],
                        "deferred_approval_action_ids": [],
                    },
                }
            }
            (repair_dir / "repair_plan.json").write_text(
                json.dumps(repair_plan), encoding="utf-8"
            )

            disposition = current_repair_agent_disposition(
                run_dir,
                {
                    "id": "repair_step.00",
                    "scope": "verification_capability_repair",
                },
                "board_axi_ddr_closure",
            )

            self.assertIsNotNone(disposition)
            assert disposition is not None
            self.assertEqual(disposition["repair_step_id"], "repair_step.00")
            self.assertEqual(
                disposition["executable_actions"],
                repair_plan["repair_workflow"]["llm_disposition"]["executable_actions"],
            )
            self.assertTrue(disposition["repair_plan"]["sha256"])
            self.assertIsNone(
                current_repair_agent_disposition(
                    run_dir,
                    {"id": "repair_step.01"},
                    "board_axi_ddr_closure",
                )
            )

    def test_resolved_lower_certificate_supersedes_old_agent_rejection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "debug_layer": "single_transformer_layer_kernel",
                "action": {"repair_kind": "case_single_layer_functional"},
            }
            report_path = out_dir / "agent_patch_application.json"
            report_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "blockers": [
                            "single_layer: passing operator-leaf promotion certificate is unavailable for scoped single-layer reuse"
                        ],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_repair_execute.reusable_operator_leaf_promotion_certificate",
                return_value={"status": "pass"},
            ):
                feedback = current_agent_patch_application_feedback(
                    out_dir, step, run_dir=run_dir
                )

        self.assertEqual(feedback["status"], "not_run")
        self.assertIn("revalidated lower-layer certificate", feedback["summary"])

    def test_resolved_certificate_does_not_hide_real_hardware_probe_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            probe = out_dir / "repair_step_00_verification_capability_probe_pre_patch.json"
            probe.write_text(
                json.dumps(
                    {
                        "probe_context": {
                            "verification_scope": "single_layer_closure"
                        },
                        "summary": "board_output_lifecycle_frontier_violation",
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_repair_execute.reusable_operator_leaf_promotion_certificate",
                return_value={"status": "pass"},
            ):
                selected, selection = scoped_capability_probe_paths(
                    out_dir, "single_layer_closure", run_dir
                )

        self.assertEqual(selected, [probe])
        self.assertEqual(selection["excluded_resolved_certificate_probe_count"], 0)

    def test_resolved_certificate_excludes_only_old_certificate_probe(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            probe = out_dir / "repair_step_00_verification_capability_probe_pre_patch.json"
            probe.write_text(
                json.dumps(
                    {
                        "probe_context": {
                            "verification_scope": "single_layer_closure"
                        },
                        "case_adapter_role": "semantic_testbench_generate",
                        "status": "fail",
                        "blockers": [
                            "single_layer: passing operator-leaf promotion certificate is unavailable for scoped single-layer reuse"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_repair_execute.reusable_operator_leaf_promotion_certificate",
                return_value={"status": "pass"},
            ):
                selected, selection = scoped_capability_probe_paths(
                    out_dir, "single_layer_closure", run_dir
                )

        self.assertEqual(selected, [])
        self.assertEqual(selection["excluded_resolved_certificate_probe_count"], 1)

    def test_capability_compaction_preserves_repair_agent_disposition(self) -> None:
        disposition = {
            "schema_version": "spatialaccagent.current_repair_agent_disposition.v1",
            "repair_plan": {"path": "/run/repair/repair_plan.json", "sha256": "a" * 64},
            "repair_step_id": "repair_step.00",
            "verification_scope": "board_axi_ddr_closure",
            "status": "needs_repair",
            "summary": "current repair direction",
            "executable_actions": [
                {"action_type": "verification_capability_repair"}
            ],
        }
        compact = compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                "current_repair_agent_disposition": disposition,
            }
        )
        changed = copy.deepcopy(disposition)
        changed["repair_plan"]["sha256"] = "b" * 64
        changed_compact = compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                "current_repair_agent_disposition": changed,
            }
        )

        self.assertEqual(compact["current_repair_agent_disposition"], disposition)
        self.assertNotEqual(compact, changed_compact)

    def test_board_compaction_preserves_task_card_acceptance_policy(self) -> None:
        policy = {
            "board_validation_mode": "full_model_pipeline_liveness",
            "numeric_golden_match_required": False,
        }
        compact = compact_verification_capability_repair_package(
            {
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "task_card": {
                            "path": "/run/input/task_card.json",
                            "sha256": "a" * 64,
                            "value": {"acceptance_policy": policy},
                        }
                    }
                }
            }
        )

        task_card = compact["exact_board_integration_repair_context"][
            "adaptive_design_inputs"
        ]["task_card"]
        self.assertEqual(task_card["value"]["acceptance_policy"], policy)

    def test_implementation_schema_rejects_semantic_subtask_as_stage(self) -> None:
        output = {
            "schema_version": "spatialaccagent.exact_board_integration_generation.v1",
            "agent": "exact_board_integration_generation_agent",
            "stage": "simulation_checkpoint_hook_generation",
            "status": "ready_to_apply",
            "summary": "checkpoint hook patch",
            "root_cause": "missing hook",
            "file_edits": [],
            "requested_validation": [],
            "blocked_reasons": [],
            "approval_required_for": [],
        }

        with self.assertRaisesRegex(
            ValueError,
            "output.stage does not equal the required constant",
        ):
            validate_schema(output, IMPLEMENTATION_REPAIR_SCHEMA)

    def test_board_schema_omits_empty_control_fields(self) -> None:
        validate_schema(
            {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "file_edits": [],
                "blocked_reasons": [],
            },
            BOARD_INTEGRATION_REPAIR_SCHEMA,
        )

    def test_board_signal_analysis_schema_requires_signal_to_repair_record(self) -> None:
        output = {
            "agent": "exact_board_integration_generation_agent",
            "stage": "repair_execution",
            "status": "ready_to_apply",
            "summary": "input completed but output did not advance",
            "root_cause": "the current evidence identifies the first stopped data boundary",
            "causal_prediction": {
                "intervention_family": "bounded_test_repair",
                "target_frontier_id": "frontier.current",
                "expected_progress_changes": [
                    {
                        "metric": "output_received_count",
                        "relation": "increase_from_baseline",
                        "value": None,
                    }
                ],
                "falsified_if": "output received count remains unchanged",
                "evidence_refs": ["current-board-evidence"],
            },
            "adaptive_observation_decision": {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "direct_executed_contradiction",
                "frontier_id": "frontier.current",
                "evidence_refs": ["current-board-evidence"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/input_count",
                        "observed_value": 16,
                        "semantic_role": "counter",
                        "interpretation": "all expected input windows were received",
                    },
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                        "observed_value": 0,
                        "semantic_role": "counter",
                        "interpretation": "no output window was received",
                    },
                ],
                "rationale": "the next source edit is tied to the observed stopped boundary",
            },
            "file_edits": [],
            "requested_validation": [],
            "blocked_reasons": [],
            "approval_required_for": [],
        }
        validate_schema(output, BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA)

        missing_signal = copy.deepcopy(output)
        missing_signal["adaptive_observation_decision"]["field_observations"] = [
            missing_signal["adaptive_observation_decision"]["field_observations"][0]
        ]
        with self.assertRaisesRegex(ValueError, "fewer than 2 items"):
            validate_schema(missing_signal, BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA)

        missing_root_cause = copy.deepcopy(output)
        missing_root_cause["root_cause"] = ""
        with self.assertRaisesRegex(ValueError, "root_cause is shorter"):
            validate_schema(missing_root_cause, BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA)

        missing_prediction = copy.deepcopy(output)
        missing_prediction["causal_prediction"]["expected_progress_changes"] = []
        with self.assertRaisesRegex(ValueError, "fewer than 1 items"):
            validate_schema(missing_prediction, BOARD_SIGNAL_ANALYSIS_REPAIR_SCHEMA)

    def test_repair_loop_archives_hash_bound_sacg_cctg_causal_slice(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            causal_path = root / "sacg_cctg_causal_slice.json"
            diagnosis_path = root / "vcs_functional_diagnosis.json"
            causal_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.sacg_cctg_causal_slice.v1",
                        "status": "ready",
                    }
                ),
                encoding="utf-8",
            )
            causal_sha256 = hashlib.sha256(causal_path.read_bytes()).hexdigest()
            diagnosis_path.write_text(
                json.dumps(
                    {
                        "failure_evidence": {
                            "sacg_cctg_causal_slice": {
                                "path": str(causal_path),
                                "sha256": causal_sha256,
                                "value": {"status": "ready"},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "step_results": [
                    {
                        "result": {
                            "capability_reports": [{"path": str(diagnosis_path)}]
                        }
                    }
                ]
            }

            evidence = repair_loop_evidence_paths(report)
            self.assertIn(
                ("sacg_cctg_causal_slice", causal_path.resolve()), evidence
            )

            causal_path.write_text("tampered", encoding="utf-8")
            evidence = repair_loop_evidence_paths(report)
            self.assertNotIn(
                ("sacg_cctg_causal_slice", causal_path.resolve()), evidence
            )

    def test_stage8_repair_loop_continues_after_patch_then_completes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "files": [
                            {
                                "path": str(run_dir / "generated" / "board_tb.sv"),
                                "before_sha256": "a" * 64,
                                "after_sha256": "b" * 64,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            first_path = out_dir / "first_report.json"
            second_path = out_dir / "second_report.json"
            first_report = {
                "status": "incomplete",
                "errors": ["VCS still fails"],
                "step_results": [
                    {
                        "result": {
                            "status": "fail",
                            "agent_patch_application": str(patch_path),
                            "llm_record": str(out_dir / "fresh_agent_result.json"),
                        }
                    }
                ],
            }
            second_report = {"status": "ready", "errors": [], "step_results": []}
            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )

            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=[(first_path, first_report), (second_path, second_report)],
            ) as execute:
                report_path, report = run_repair_loop(args)

            self.assertEqual(execute.call_count, 2)
            self.assertEqual(report_path, second_path)
            self.assertEqual(report["repair_loop_disposition"]["status"], "complete")
            records = sorted((out_dir / "loop").glob("iteration_*/iteration_record.json"))
            self.assertEqual(len(records), 2)
            first_record = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertEqual(first_record["disposition"]["status"], "continue")
            self.assertTrue(first_record["evidence_snapshots"])
            self.assertEqual(
                first_record["board_source_state"]["schema_version"],
                "spatialaccagent.exact_board_source_state.v1",
            )

    def test_stage8_repair_loop_stops_when_agent_makes_no_progress(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            report_path = out_dir / "repair_execution_report.json"
            incomplete_report = {
                "status": "incomplete",
                "errors": ["agent returned no patch"],
                "step_results": [{"result": {"status": "fail"}}],
            }
            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )

            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(report_path, incomplete_report),
            ) as execute:
                _, report = run_repair_loop(args)

            self.assertEqual(execute.call_count, 1)
            self.assertEqual(report["repair_loop_disposition"]["status"], "blocked")
            self.assertIn("no new applied agent patch", report["repair_loop_disposition"]["summary"])

    def test_stage8_repair_loop_continues_after_resumed_validation_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            first_path = out_dir / "first_report.json"
            second_path = out_dir / "second_report.json"
            first_report = {
                "status": "incomplete",
                "errors": ["new real VCS failure"],
                "step_results": [
                    {
                        "result": {
                            "status": "fail",
                            "summary": "new exact-board semantic stall",
                            "new_current_real_tool_failure_requires_agent": True,
                        }
                    }
                ],
            }
            second_report = {"status": "ready", "errors": [], "step_results": []}
            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )

            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=[(first_path, first_report), (second_path, second_report)],
            ) as execute:
                report_path, report = run_repair_loop(args)

            self.assertEqual(execute.call_count, 2)
            self.assertEqual(report_path, second_path)
            self.assertEqual(report["repair_loop_disposition"]["status"], "complete")
            first_record = json.loads(
                sorted((out_dir / "loop").glob("iteration_*/iteration_record.json"))[0]
                .read_text(encoding="utf-8")
            )
            self.assertEqual(first_record["disposition"]["status"], "continue")
            self.assertTrue(
                first_record["disposition"][
                    "new_current_real_tool_failure_requires_agent"
                ]
            )

    def test_stage8_repair_loop_replans_agent_after_current_board_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            (out_dir / "sacg_state.json").write_text("{}\n", encoding="utf-8")
            replanned_state = out_dir / "replanned_sacg_state.json"
            replanned_state.write_text("{}\n", encoding="utf-8")
            replanned_plan = out_dir / "replanned_repair_plan.json"
            replanned_plan.write_text(
                json.dumps(
                    {
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [
                                {
                                    "id": "repair_step.00",
                                    "status": "ready_for_agent_patch",
                                    "source": "current_exact_board_failure",
                                }
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            replanned_report = out_dir / "replanned_repair_report.json"
            replanned_report.write_text("{}\n", encoding="utf-8")
            first_report = {
                "status": "incomplete",
                "errors": ["new real VCS failure"],
                "step_results": [
                    {
                        "result": {
                            "status": "fail",
                            "summary": "new exact-board semantic stall",
                            "new_current_real_tool_failure_requires_agent": True,
                            "new_current_real_tool_failure_identity_sha256": "a" * 64,
                            "current_board_vcs_feedback": {"status": "ready"},
                        }
                    }
                ],
            }
            second_report = {"status": "ready", "errors": [], "step_results": []}
            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=[
                    (out_dir / "first_report.json", first_report),
                    (out_dir / "second_report.json", second_report),
                ],
            ) as execute, patch(
                "accagent.framework.stage_repair.plan_repair",
                return_value=(
                    replanned_report,
                    {
                        "outputs": {
                            "repair_report": str(replanned_report),
                            "repair_plan": str(replanned_plan),
                            "sacg_state": str(replanned_state),
                        }
                    },
                ),
            ) as plan:
                _, report = run_repair_loop(args)

        self.assertEqual(execute.call_count, 2)
        self.assertEqual(plan.call_count, 1)
        self.assertEqual(report["repair_loop_disposition"]["status"], "complete")

    def test_stage8_repair_loop_recovers_recorded_exact_board_handoff_before_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair_execution" / "sacg_state.json"
            loop_dir = run_dir / "repair_execution" / "loop" / "iteration_0001"
            source_state.parent.mkdir(parents=True)
            loop_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            (loop_dir / "iteration_record.json").write_text(
                json.dumps(
                    {
                        "disposition": {
                            "status": "blocked",
                            "duplicate_unconsumed_real_tool_failure": True,
                            "exact_board_failure_handoff": True,
                            "new_current_real_tool_failure_identity_sha256": "a" * 64,
                        }
                    }
                ),
                encoding="utf-8",
            )
            replanned_state = run_dir / "repair_execution" / "replanned_sacg_state.json"
            replanned_state.write_text("{}\n", encoding="utf-8")
            replanned_plan = run_dir / "repair_execution" / "replanned_repair_plan.json"
            replanned_plan.write_text(
                json.dumps(
                    {
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [
                                {
                                    "id": "repair_step.00",
                                    "status": "ready_for_agent_patch",
                                    "source": "current_exact_board_failure",
                                }
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            replanned_report = run_dir / "repair_execution" / "replanned_repair_report.json"
            replanned_report.write_text("{}\n", encoding="utf-8")
            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                return_value=(
                    run_dir / "repair_execution" / "repair_execution_report.json",
                    {"status": "ready", "errors": [], "step_results": []},
                ),
            ) as execute, patch(
                "accagent.framework.stage_repair.plan_repair",
                return_value=(
                    replanned_report,
                    {
                        "outputs": {
                            "repair_report": str(replanned_report),
                            "repair_plan": str(replanned_plan),
                            "sacg_state": str(replanned_state),
                        }
                    },
                ),
            ) as plan:
                _, report = run_repair_loop(args)

        self.assertEqual(plan.call_count, 1)
        self.assertEqual(execute.call_count, 1)
        self.assertEqual(report["repair_loop_disposition"]["status"], "complete")

    def test_stage8_repair_loop_continues_on_duplicate_unconsumed_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            report_path = out_dir / "repair_execution_report.json"
            identity = "f" * 64
            repeated_report = {
                "status": "incomplete",
                "errors": ["same real-tool failure"],
                "step_results": [
                    {
                        "result": {
                            "status": "fail",
                            "summary": "same exact-board semantic stall",
                            "new_current_real_tool_failure_requires_agent": True,
                            "new_current_real_tool_failure_identity_sha256": identity,
                        }
                    }
                ],
            }
            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )

            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=[
                    (report_path, repeated_report),
                    (out_dir / "repair_execution_report_2.json", {
                        "status": "ready",
                        "errors": [],
                        "step_results": [],
                    }),
                ],
            ) as execute:
                _, report = run_repair_loop(args)

            self.assertEqual(execute.call_count, 2)
            disposition = report["repair_loop_disposition"]
            self.assertEqual(disposition["status"], "complete")
            self.assertTrue(
                disposition["duplicate_unconsumed_real_tool_failure"]
            )

    def test_stage8_repair_loop_keeps_repeating_failure_in_the_loop(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            report_path = out_dir / "repair_execution_report.json"

            def report(identity: str) -> dict[str, object]:
                return {
                    "status": "incomplete",
                    "errors": ["same hardware failure"],
                    "step_results": [
                        {
                            "result": {
                                "status": "fail",
                                "summary": "same exact-board semantic stall",
                                "new_current_real_tool_failure_requires_agent": True,
                                "new_current_real_tool_failure_identity_sha256": (
                                    identity
                                ),
                            }
                        }
                    ],
                }

            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=[
                    (report_path, report("a" * 64)),
                    (report_path, report("b" * 64)),
                    (report_path, report("b" * 64)),
                ],
            ) as execute:
                _, result = run_repair_loop(args)

            self.assertEqual(execute.call_count, 3)
            records = sorted(
                (out_dir / "loop").glob("iteration_*/iteration_record.json")
            )
            self.assertEqual(
                [
                    json.loads(path.read_text(encoding="utf-8"))["disposition"][
                        "status"
                    ]
                    for path in records
                ],
                ["continue", "continue", "complete"],
            )
            self.assertTrue(
                result["repair_loop_disposition"][
                    "duplicate_unconsumed_real_tool_failure"
                ]
            )

    def test_exact_board_probe_requires_actionable_agent_handoff(self) -> None:
        probe = {
            "status": "fail",
            "current_board_vcs_feedback": {
                "status": "ready",
                "runner_report": {"value": {"status": "fail"}},
                "diagnosis": {
                    "value": {
                        "status": "needs_repair",
                        "repair_handoff": {
                            "agent_should_apply_code_changes": True,
                        },
                    }
                },
            },
        }

        self.assertTrue(exact_board_probe_requires_agent_continuation(probe))
        probe["current_board_vcs_feedback"]["diagnosis"]["value"][
            "repair_handoff"
        ]["agent_should_apply_code_changes"] = False
        self.assertFalse(exact_board_probe_requires_agent_continuation(probe))
        self.assertTrue(
            exact_board_probe_requires_agent_continuation(
                probe,
                completed_agent_experiment=True,
            )
        )
        self.assertRegex(
            str(
                exact_board_probe_agent_handoff_identity(
                    probe,
                    completed_agent_experiment=True,
                )
            ),
            r"^[0-9a-f]{64}$",
        )

    def test_exact_board_handoff_identity_ignores_mutable_artifact_paths(self) -> None:
        probe = {
            "status": "fail",
            "current_board_vcs_feedback": {
                "status": "ready",
                "runner_report": {
                    "path": "/mutable/runner-a.json",
                    "sha256": "a" * 64,
                    "value": {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "input_fingerprint_sha256": "b" * 64,
                        "run": {"failure_class": "adaptive_semantic_stall"},
                    },
                },
                "diagnosis": {
                    "path": "/mutable/diagnosis-a.json",
                    "sha256": "c" * 64,
                    "value": {
                        "status": "needs_repair",
                        "summary": "layer zero made no output progress",
                        "repair_handoff": {
                            "agent_should_apply_code_changes": True,
                            "debug_layer": "board_axi_ddr_wrapped_system",
                            "failure_class": "vcs_runtime_semantic_stall",
                        },
                    },
                },
            },
        }
        changed_audit_paths = copy.deepcopy(probe)
        changed_audit_paths["current_board_vcs_feedback"]["runner_report"].update(
            {"path": "/mutable/runner-b.json", "sha256": "d" * 64}
        )
        changed_audit_paths["current_board_vcs_feedback"]["diagnosis"].update(
            {"path": "/mutable/diagnosis-b.json", "sha256": "e" * 64}
        )

        first = exact_board_probe_agent_handoff_identity(probe)
        second = exact_board_probe_agent_handoff_identity(changed_audit_paths)

        self.assertEqual(first, second)
        self.assertRegex(str(first), r"^[0-9a-f]{64}$")

    def test_exact_board_handoff_identity_tracks_new_simulator_provenance(self) -> None:
        probe = {
            "status": "fail",
            "current_board_vcs_feedback": {
                "status": "ready",
                "runner_report": {
                    "value": {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "input_fingerprint_sha256": "b" * 64,
                        "run": {
                            "failure_class": "remote_tool_failure",
                            "termination_provenance": {
                                "causal_classification": {
                                    "classification": (
                                        "external_or_unattributed_termination"
                                    )
                                },
                                "termination_source": "nonzero_process_exit",
                                "runner_failure_class": "remote_tool_failure",
                                "runner_process_provenance": {
                                    "status": "observed",
                                    "attribution": (
                                        "runner_owned_nonzero_process_exit"
                                    ),
                                    "last_running_process_snapshot": {},
                                    "last_simulator_process_commands": [],
                                },
                            },
                        },
                    }
                },
                "diagnosis": {
                    "value": {
                        "status": "needs_repair",
                        "summary": "pipeline overlap report is invalid",
                        "failure_class": "vcs_runtime_unclassified_exit",
                        "repair_handoff": {
                            "agent_should_apply_code_changes": True,
                            "debug_layer": "board_axi_ddr_wrapped_system",
                            "failure_class": "vcs_runtime_unclassified_exit",
                        },
                    }
                },
            },
        }
        observed = copy.deepcopy(probe)
        process_provenance = observed["current_board_vcs_feedback"][
            "runner_report"
        ]["value"]["run"]["termination_provenance"][
            "runner_process_provenance"
        ]
        process_provenance["last_running_process_snapshot"] = {
            "simulator_like_process_observed": True,
            "simulator_process_commands": ["simv"],
        }
        process_provenance["last_simulator_process_commands"] = ["simv"]

        empty_identity = exact_board_probe_agent_handoff_identity(probe)
        observed_identity = exact_board_probe_agent_handoff_identity(observed)

        self.assertNotEqual(empty_identity, observed_identity)
        self.assertEqual(
            observed_identity,
            exact_board_probe_agent_handoff_identity(copy.deepcopy(observed)),
        )

    def test_single_layer_handoff_requires_source_bound_v2_barrier_evidence(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "single_layer_functional_report.json"
            report = {
                "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
                "status": "fail",
                "stats": {
                    "input_fingerprint_sha256": "a" * 64,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "remote_job_reuse": {"real_tool_was_not_relaunched": True},
                    "run": {
                        "failure_class": "adaptive_semantic_stall",
                        "returncode": SEMANTIC_STALL_EXIT_CODE,
                        "adaptive_semantic_stall_evidence": {
                            "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                            "status": "proven_semantic_stall",
                            "proof_mode": "single_layer_pipeline_contract",
                            "failure_class": "intra_layer_spatial_pipeline_violation",
                            "contract_sha256": "b" * 64,
                        },
                        "adaptive_semantic_stall_termination": {
                            "status": "pass",
                            "remote_exit_code": SEMANTIC_STALL_EXIT_CODE,
                            "fixed_wall_clock_timeout": False,
                            "fixed_cycle_timeout": False,
                        },
                    },
                },
                "pipeline_overlap_evidence": {
                    "status": "fail",
                    "contract_sha256": "b" * 64,
                    "trace_sha256": "c" * 64,
                    "whole_sequence_barrier_evidence": [
                        {
                            "stage_id": "stage_1",
                            "whole_sequence_barrier_observed": True,
                        }
                    ],
                },
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            probe = {
                "status": "fail",
                "produced_reports": [{"path": str(report_path)}],
            }

            handoff = single_layer_probe_agent_handoff(probe)
            report["pipeline_overlap_evidence"]["contract_sha256"] = "d" * 64
            report_path.write_text(json.dumps(report), encoding="utf-8")
            mismatched = single_layer_probe_agent_handoff(probe)

        self.assertIsNotNone(handoff)
        self.assertEqual(handoff["debug_layer"], "single_transformer_layer_kernel")
        self.assertTrue(handoff["agent_should_apply_code_changes"])
        self.assertRegex(handoff["failure_identity_sha256"], r"^[0-9a-f]{64}$")
        self.assertIsNone(mismatched)

    def test_single_layer_handoff_accepts_source_bound_early_turnover_evidence(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "single_layer_functional_report.json"
            turnover = {
                "stage_id": "stage_02_residual_add_1",
                "prior_token": 0,
                "next_token": 1,
                "prior_token_active_end_cycle": 100,
                "next_token_active_start_cycle": 120,
                "gap_cycles": 20,
                "keeps_pipeline_filled": False,
                "overlapped": False,
            }
            report = {
                "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
                "status": "fail",
                "stats": {
                    "input_fingerprint_sha256": "a" * 64,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "run": {
                        "failure_class": "adaptive_semantic_stall",
                        "returncode": SEMANTIC_STALL_EXIT_CODE,
                        "adaptive_semantic_stall_evidence": {
                            "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
                            "status": "proven_semantic_stall",
                            "proof_mode": "single_layer_pipeline_contract",
                            "failure_class": "intra_layer_spatial_pipeline_violation",
                            "contract_sha256": "b" * 64,
                            "irreversible_violation_kind": "stage_turnover",
                            "failed_stage_turnover_evidence": [
                                copy.deepcopy(turnover)
                            ],
                            "candidate_stage_ids": [
                                "stage_01_self_attention",
                                "stage_02_residual_add_1",
                                "stage_03_rms_norm_2",
                            ],
                        },
                        "adaptive_semantic_stall_termination": {
                            "status": "pass",
                            "remote_exit_code": SEMANTIC_STALL_EXIT_CODE,
                            "fixed_wall_clock_timeout": False,
                            "fixed_cycle_timeout": False,
                        },
                    },
                },
                "pipeline_overlap_evidence": {
                    "status": "fail",
                    "contract_sha256": "b" * 64,
                    "trace_sha256": "c" * 64,
                    "irreversible_stage_turnover_evidence": {
                        "status": "fail",
                        "failed_stage_turnover_evidence": [
                            copy.deepcopy(turnover)
                        ],
                        "candidate_stage_ids": [
                            "stage_01_self_attention",
                            "stage_02_residual_add_1",
                            "stage_03_rms_norm_2",
                        ],
                    },
                    "whole_sequence_barrier_evidence": [],
                },
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            probe = {
                "status": "fail",
                "produced_reports": [{"path": str(report_path)}],
            }

            handoff = single_layer_probe_agent_handoff(probe)
            report["pipeline_overlap_evidence"][
                "irreversible_stage_turnover_evidence"
            ]["failed_stage_turnover_evidence"][0]["gap_cycles"] = 21
            report_path.write_text(json.dumps(report), encoding="utf-8")
            mismatched = single_layer_probe_agent_handoff(probe)

        self.assertIsNotNone(handoff)
        self.assertEqual(
            handoff["failure_mode"],
            "irreversible_stage_turnover_violation",
        )
        self.assertEqual(
            handoff["candidate_stage_ids"],
            [
                "stage_01_self_attention",
                "stage_02_residual_add_1",
                "stage_03_rms_norm_2",
            ],
        )
        self.assertEqual(handoff["failed_stage_turnover_evidence"], [turnover])
        self.assertIsNone(mismatched)

    def test_completed_single_layer_overlap_failure_requires_complete_real_trace(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "single_layer_functional_report.json"
            terminal_checks = {
                "all_required_trace_records_are_accepted": True,
                "execution_status_pass": True,
                "only_terminal_block_output_trace_is_missing": False,
                "output_line_count_matches": True,
                "remote_exit_status_pass": True,
                "required_boundaries_are_valid": True,
                "single_matching_sim_pass_declaration": True,
                "trace_positions_are_unique_and_well_formed": True,
            }
            report = {
                "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
                "status": "fail",
                "stats": {
                    "status": "pass",
                    "input_fingerprint_sha256": "a" * 64,
                    "remote_workdir": "/remote/exact-fingerprint",
                    "remote_artifact_persistence": {"status": "pass"},
                    "remote_job_reuse": {
                        "status": "not_run",
                        "real_tool_was_not_relaunched": False,
                    },
                    "run": {
                        "status": "pass",
                        "returncode": 0,
                        "remote_state": "done",
                    },
                },
                "real_weight_execution": {"verified": True},
                "pipeline_overlap_evidence": {
                    "schema_version": (
                        "spatialaccagent.single_layer_pipeline_overlap_evidence.v2"
                    ),
                    "status": "fail",
                    "contract_sha256": "b" * 64,
                    "trace_sha256": "c" * 64,
                    "accepted_trace_record_count": 2,
                    "trace_record_count": 2,
                    "terminal_trace_flush_inferred": False,
                    "blockers": ["stage_a left a pipeline bubble"],
                    "stage_activity_evidence": [
                        {"stage_id": "stage_a"},
                        {"stage_id": "stage_b"},
                    ],
                    "stage_turnover_evidence": [
                        {
                            "stage_id": "stage_a",
                            "prior_token": 0,
                            "next_token": 1,
                            "prior_token_active_end_cycle": 10,
                            "next_token_active_start_cycle": 12,
                            "gap_cycles": 2,
                            "overlapped": False,
                            "keeps_pipeline_filled": False,
                        }
                    ],
                    "dependency_overlap_evidence": [
                        {
                            "boundary_id": "edge.a.to.b",
                            "src_stage": "stage_a",
                            "dst_stage": "stage_b",
                            "different_token_overlap_observed": False,
                            "overlaps": [],
                        }
                    ],
                    "whole_sequence_barrier_evidence": [
                        {
                            "stage_id": "stage_a",
                            "whole_sequence_barrier_observed": False,
                        }
                    ],
                    "terminal_trace_flush_evidence": {
                        "checks": terminal_checks,
                        "inferred": False,
                        "required_trace_position_count": 2,
                        "observed_required_trace_position_count": 2,
                        "actual_output_line_count": 4,
                        "expected_output_line_count": 4,
                        "duplicate_required_trace_position_count": 0,
                        "malformed_required_trace_position_count": 0,
                        "missing_required_trace_position_count": 0,
                        "unexpected_required_trace_position_count": 0,
                        "unparsed_pipeline_trace_line_count": 0,
                        "sim_pass_declarations": [{"beats": 4, "cycles": 20}],
                    },
                },
            }
            report_path.write_text(json.dumps(report), encoding="utf-8")
            probe = {
                "status": "fail",
                "produced_reports": [{"path": str(report_path)}],
            }

            handoff = single_layer_probe_agent_handoff(probe)
            report["pipeline_overlap_evidence"]["terminal_trace_flush_evidence"][
                "checks"
            ]["execution_status_pass"] = False
            report_path.write_text(json.dumps(report), encoding="utf-8")
            incomplete = single_layer_probe_agent_handoff(probe)
            report["pipeline_overlap_evidence"]["terminal_trace_flush_evidence"][
                "checks"
            ]["execution_status_pass"] = True
            overlap = report["pipeline_overlap_evidence"]
            overlap["schema_version"] = (
                "spatialaccagent.single_layer_pipeline_overlap_evidence.v3"
            )
            overlap["pipeline_semantics"] = (
                "elastic_rate_insensitive_token_pipeline"
            )
            overlap["stage_turnover_evidence"][0]["acceptance_role"] = "diagnostic"
            overlap["dependency_overlap_evidence"][0].update(
                {
                    "relationship": "transitive_bypass",
                    "overlap_requirement": "diagnostic",
                    "required_for_acceptance": False,
                }
            )
            report_path.write_text(json.dumps(report), encoding="utf-8")
            diagnostic_only = single_layer_probe_agent_handoff(probe)
            overlap["dependency_overlap_evidence"][0].update(
                {
                    "relationship": "direct_dataflow",
                    "overlap_requirement": "required",
                    "required_for_acceptance": True,
                }
            )
            report_path.write_text(json.dumps(report), encoding="utf-8")
            v3_required_failure = single_layer_probe_agent_handoff(probe)

        self.assertIsNotNone(handoff)
        self.assertEqual(
            handoff["failure_mode"], "completed_pipeline_overlap_violation"
        )
        self.assertEqual(handoff["candidate_stage_ids"], ["stage_a", "stage_b"])
        self.assertIsNone(incomplete)
        self.assertIsNone(diagnostic_only)
        self.assertIsNotNone(v3_required_failure)
        self.assertEqual(
            v3_required_failure["pipeline_semantics"],
            "elastic_rate_insensitive_token_pipeline",
        )
        self.assertEqual(
            v3_required_failure["failed_stage_turnover_evidence"], []
        )

    def test_pipeline_barrier_opens_only_its_pipeline_plan_template_pair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            pipeline_plan_path = run_dir / "pipeline_planning" / "pipeline_plan.json"
            semantic_manifest_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "semantic_testbench_manifest.json"
            )
            generated_template = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Attention.scala"
            )
            persistent_template = (
                Path.cwd()
                / "accagent"
                / "framework"
                / "templates"
                / "operator_chisel"
                / "Attention.scala"
            )
            pipeline_plan_path.parent.mkdir(parents=True)
            semantic_manifest_path.parent.mkdir(parents=True)
            generated_template.parent.mkdir(parents=True)
            pipeline_plan_path.write_text(
                json.dumps(
                    {
                        "stages": [
                            {
                                "stage_id": "stage_1",
                                "source": "Attention.scala",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            generated_template.write_bytes(persistent_template.read_bytes())
            semantic_manifest_path.write_text(
                json.dumps(
                    {
                        "single_layer": {
                            "pipeline_overlap_contract": {
                                "contract_sha256": "b" * 64,
                                "pipeline_plan_sha256": sha256_file(
                                    pipeline_plan_path
                                ),
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            handoff = {
                "report": {"path": str(run_dir / "failure.json")},
                "input_fingerprint_sha256": "a" * 64,
                "pipeline_contract_sha256": "b" * 64,
                "pipeline_trace_sha256": "c" * 64,
                "whole_sequence_barrier_evidence": [
                    {
                        "stage_id": "stage_1",
                        "final_token_last_input_cycle": 10,
                        "token_0_first_output_cycle": 11,
                        "whole_sequence_barrier_observed": True,
                    }
                ],
            }
            trace = single_layer_pipeline_trace_record(run_dir, handoff)
            self.assertIsNotNone(trace)
            with patch.dict(
                os.environ,
                {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"},
            ):
                authorized = authorize_localized_semantic_repair_bundle(
                    {
                        "documents": [
                            {
                                "path": str(generated_template),
                                "content": generated_template.read_text(
                                    encoding="utf-8"
                                ),
                            }
                        ],
                        "editable_contract": {
                            "read_only_template_sources": [
                                str(generated_template)
                            ]
                        },
                    },
                    run_dir,
                    trace,
                )

        editable = authorized["editable_contract"]
        self.assertTrue(editable["localized_semantic_repair_authorized"])
        self.assertTrue(editable["semantic_template_repair_approved"])
        self.assertEqual(editable["localized_authorization_errors"], [])
        self.assertEqual(
            set(editable["approved_bounded_template_repair_exact_files"]),
            {
                str(generated_template),
                str(persistent_template.relative_to(Path.cwd())),
            },
        )

    def test_completed_pipeline_failure_opens_only_plan_bound_candidate_pairs(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            pipeline_plan_path = run_dir / "pipeline_planning" / "pipeline_plan.json"
            semantic_manifest_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "semantic_testbench_manifest.json"
            )
            generated_root = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
            )
            persistent_root = (
                Path.cwd()
                / "accagent"
                / "framework"
                / "templates"
                / "operator_chisel"
            )
            pipeline_plan_path.parent.mkdir(parents=True)
            semantic_manifest_path.parent.mkdir(parents=True)
            generated_root.mkdir(parents=True)
            pipeline_plan_path.write_text(
                json.dumps(
                    {
                        "stages": [
                            {
                                "stage_id": "stage_a",
                                "index": 0,
                                "op": "residual_a",
                                "kind": "residual",
                                "template_id": "residual",
                                "source": "Residual.scala",
                            },
                            {
                                "stage_id": "stage_b",
                                "index": 1,
                                "op": "norm_b",
                                "kind": "norm",
                                "template_id": "norm",
                                "source": "Norm.scala",
                            },
                            {
                                "stage_id": "stage_c",
                                "index": 2,
                                "op": "residual_c",
                                "kind": "residual",
                                "template_id": "residual",
                                "source": "Residual.scala",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            for name in ("Residual.scala", "Norm.scala", "Attention.scala"):
                (generated_root / name).write_bytes((persistent_root / name).read_bytes())
            semantic_manifest_path.write_text(
                json.dumps(
                    {
                        "single_layer": {
                            "pipeline_overlap_contract": {
                                "contract_sha256": "b" * 64,
                                "pipeline_plan_sha256": sha256_file(
                                    pipeline_plan_path
                                ),
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            report_path = run_dir / "completed_failure.json"
            report_path.write_text("{}\n", encoding="utf-8")
            handoff = {
                "failure_mode": "completed_pipeline_overlap_violation",
                "report": {
                    "path": str(report_path),
                    "sha256": sha256_file(report_path),
                },
                "input_fingerprint_sha256": "a" * 64,
                "pipeline_contract_sha256": "b" * 64,
                "pipeline_trace_sha256": "c" * 64,
                "candidate_stage_ids": ["stage_a", "stage_b", "stage_c"],
                "failed_stage_turnover_evidence": [
                    {
                        "stage_id": "stage_a",
                        "keeps_pipeline_filled": False,
                    }
                ],
                "failed_dependency_overlap_evidence": [
                    {
                        "boundary_id": "edge.a.to.b",
                        "src_stage": "stage_a",
                        "dst_stage": "stage_b",
                        "different_token_overlap_observed": False,
                        "overlaps": [],
                    },
                    {
                        "boundary_id": "edge.b.to.c",
                        "src_stage": "stage_b",
                        "dst_stage": "stage_c",
                        "different_token_overlap_observed": False,
                        "overlaps": [],
                    },
                ],
                "whole_sequence_barrier_evidence": [],
            }
            trace = single_layer_pipeline_trace_record(run_dir, handoff)
            self.assertIsNotNone(trace)
            early_handoff = copy.deepcopy(handoff)
            early_handoff["failure_mode"] = (
                "irreversible_stage_turnover_violation"
            )
            early_handoff["candidate_stage_ids"] = ["stage_a", "stage_b"]
            early_handoff["failed_dependency_overlap_evidence"] = []
            early_trace = single_layer_pipeline_trace_record(
                run_dir, early_handoff
            )
            self.assertIsNotNone(early_trace)
            self.assertEqual(
                early_trace["failure_mode"],
                "irreversible_stage_turnover_violation",
            )
            self.assertEqual(
                early_trace["candidate_stage_ids"], ["stage_a", "stage_b"]
            )
            mismatched_handoff = copy.deepcopy(handoff)
            mismatched_handoff["report"]["sha256"] = "d" * 64
            self.assertIsNone(
                single_layer_pipeline_trace_record(run_dir, mismatched_handoff)
            )
            with patch.dict(
                os.environ,
                {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"},
            ):
                repair_bundle = {
                    "documents": [
                        {
                            "path": str(generated_root / name),
                            "content": (generated_root / name).read_text(
                                encoding="utf-8"
                            ),
                        }
                        for name in (
                            "Residual.scala",
                            "Norm.scala",
                            "Attention.scala",
                        )
                    ],
                    "editable_contract": {
                        "read_only_template_sources": [
                            str(generated_root / name)
                            for name in (
                                "Residual.scala",
                                "Norm.scala",
                                "Attention.scala",
                            )
                        ]
                    },
                }
                authorized = authorize_localized_semantic_repair_bundle(
                    repair_bundle,
                    run_dir,
                    trace,
                )
                early_authorized = authorize_localized_semantic_repair_bundle(
                    repair_bundle,
                    run_dir,
                    early_trace,
                )

        editable = authorized["editable_contract"]
        self.assertTrue(editable["localized_semantic_repair_authorized"])
        self.assertEqual(editable["localized_authorization_errors"], [])
        self.assertEqual(editable["localized_template_pair_names"], [])
        self.assertEqual(
            editable["localized_candidate_template_pair_names"],
            ["Norm.scala", "Residual.scala"],
        )
        self.assertEqual(
            set(editable["approved_bounded_template_repair_exact_files"]),
            {
                str(generated_root / "Norm.scala"),
                str(generated_root / "Residual.scala"),
                str((persistent_root / "Norm.scala").relative_to(Path.cwd())),
                str((persistent_root / "Residual.scala").relative_to(Path.cwd())),
            },
        )
        self.assertNotIn(
            str(generated_root / "Attention.scala"),
            editable["localized_allowed_exact_files"],
        )
        early_editable = early_authorized["editable_contract"]
        self.assertTrue(early_editable["localized_semantic_repair_authorized"])
        self.assertEqual(early_editable["localized_authorization_errors"], [])
        self.assertEqual(
            early_editable["localized_candidate_template_pair_names"],
            ["Norm.scala", "Residual.scala"],
        )
        self.assertEqual(
            set(early_editable["approved_bounded_template_repair_exact_files"]),
            {
                str(generated_root / "Norm.scala"),
                str(generated_root / "Residual.scala"),
                str((persistent_root / "Norm.scala").relative_to(Path.cwd())),
                str((persistent_root / "Residual.scala").relative_to(Path.cwd())),
            },
        )

    def test_completed_pipeline_route_binds_source_step_and_failure(self) -> None:
        step = {
            "id": "repair_step.00",
            "scope": "verification_capability_repair",
            "debug_layer": "single_transformer_layer_kernel",
            "action": {
                "repair_kind": "case_single_layer_functional",
                "repair_gate": "case_single_layer_functional",
                "debug_layer": "single_transformer_layer_kernel",
                "violated_contract": (
                    "all_spatial_operators_must_form_a_token_level_pipeline"
                ),
            },
        }
        record = {
            "stage_id": "stage_02_residual_add_1",
            "module": "pipeline_candidate_set",
            "candidate_stage_ids": ["stage_02_residual_add_1"],
            "candidate_stages": [
                {
                    "stage_id": "stage_02_residual_add_1",
                    "op": "residual_add_1",
                }
            ],
            "candidate_template_sources": ["Residual.scala"],
            "violated_contract": (
                "all_spatial_operators_must_form_a_token_level_pipeline"
            ),
            "input_fingerprint_sha256": "a" * 64,
        }
        handoff = {
            "summary": "source-bound Stage2 overlap failure",
            "failure_identity_sha256": "b" * 64,
        }

        _, routed_step, _, _ = localized_single_layer_repair_route(
            step["action"], step, record, handoff
        )
        checkpoint = repair_step_checkpoint(routed_step)

        self.assertEqual(
            checkpoint["schema_version"],
            "spatialaccagent.repair_step_checkpoint.v2",
        )
        self.assertTrue(checkpoint["dynamic_source_bound_route"])
        self.assertEqual(
            checkpoint["source_repair_checkpoint_fingerprint_sha256"],
            repair_step_checkpoint(step)["fingerprint_sha256"],
        )
        self.assertEqual(
            checkpoint["source_bound_failure_identity_sha256"], "b" * 64
        )
        self.assertEqual(
            checkpoint["source_bound_input_fingerprint_sha256"], "a" * 64
        )

    def test_stage8_repair_loop_disposition_stops_explicit_agent_block(self) -> None:
        disposition = repair_loop_disposition(
            {
                "status": "incomplete",
                "errors": ["missing capability"],
                "step_results": [
                    {"result": {"status": "blocked", "summary": "missing exact board fact"}}
                ],
            }
        )

        self.assertEqual(disposition["status"], "blocked")
        self.assertEqual(disposition["summary"], "missing exact board fact")

    def test_stage8_repair_loop_replans_capability_before_blocked_handoff(self) -> None:
        capability = {
            "capability_id": "vcs_timescale_error_localization",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "real_board_vcs_compile_provenance",
            "target_modules": ["spatialacc_exact_board_multilayer_tb"],
            "required_evidence": ["hash-bound compile provenance"],
            "rationale": "localize the compiler diagnostic before another edit",
        }

        disposition = repair_loop_disposition(
            {
                "status": "incomplete",
                "errors": ["upstream provenance required"],
                "step_results": [
                    {
                        "result": {
                            "status": "blocked",
                            "summary": "implementation agent requires an upstream capability",
                            "framework_action_required": True,
                            "required_capabilities": [capability],
                            "agent_patch_application": "/nonexistent/blocked_handoff.json",
                        }
                    }
                ],
            }
        )

        self.assertEqual(disposition["status"], "continue")
        self.assertTrue(disposition["upstream_capability_replan_required"])
        self.assertEqual(disposition["required_capabilities"], [capability])

    def test_stage8_repair_loop_replans_after_read_only_capability_producer(self) -> None:
        disposition = repair_loop_disposition(
            {
                "status": "incomplete",
                "errors": ["producer requires implementation Agent followup"],
                "step_results": [
                    {
                        "step_id": "repair_step.01",
                        "repair_execution_context": {
                            "debug_layer": "board_axi_ddr_wrapped_system"
                        },
                        "result": {
                            "status": "pass",
                            "repair_kind": "generic_read_only_producer",
                            "requires_agent_followup": True,
                            "capability_reports": ["/evidence/producer.json"],
                        },
                    }
                ],
            }
        )

        self.assertEqual(disposition["status"], "continue")
        self.assertTrue(disposition["capability_producer_replan_required"])
        self.assertEqual(
            disposition["completed_capability_producers"][0]["repair_kind"],
            "generic_read_only_producer",
        )

    def test_stage8_repair_loop_replans_supported_vivado_authority_request(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            (out_dir / "sacg_state.json").write_text("{}\n", encoding="utf-8")
            first_path = out_dir / "first_report.json"
            second_path = out_dir / "second_report.json"
            capability = {
                "capability_id": "exact_board_vivado_identity_authority_refresh.v1",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "producer_scope": (
                    "real_vivado_exact_sample_project_discovery_selector_"
                    "and_compile_authority"
                ),
                "target_modules": ["vivado_board_facts", "board_source_identity"],
                "required_evidence": ["executed exact-project Vivado fact bundle"],
                "rationale": "current immutable board authority is stale",
            }
            first_report = {
                "status": "incomplete",
                "errors": ["upstream authority required"],
                "step_results": [
                    {
                        "result": {
                            "status": "blocked",
                            "summary": "real Vivado authority refresh required",
                            "required_capabilities": [capability],
                            "framework_action_required": True,
                        }
                    }
                ],
            }
            second_report = {"status": "ready", "errors": [], "step_results": []}
            repair_dir = run_dir / "repair"
            repair_report_path = repair_dir / "repair_report.json"
            repair_plan_path = repair_dir / "repair_plan.json"
            replanned_state = repair_dir / "replanned_sacg_state.json"

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value) + "\n", encoding="utf-8")

            def fake_plan(_args: argparse.Namespace):
                write(
                    repair_plan_path,
                    {
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [
                                {
                                    "id": "repair_step.00",
                                    "status": "ready_for_agent_patch",
                                    "source": "prior_nonfallback_llm_required_capability",
                                }
                            ],
                        }
                    },
                )
                write(replanned_state, {})
                repair_report = {
                    "outputs": {
                        "repair_plan": str(repair_plan_path),
                        "sacg_state": str(replanned_state),
                    }
                }
                write(repair_report_path, repair_report)
                return repair_report_path, repair_report

            executed_states: list[Path] = []

            def fake_execute(iteration_args: argparse.Namespace):
                executed_states.append(iteration_args.sacg_state)
                return (
                    (first_path, first_report)
                    if len(executed_states) == 1
                    else (second_path, second_report)
                )

            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=True,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=fake_execute,
            ), patch(
                "accagent.framework.stage_repair.plan_repair",
                side_effect=fake_plan,
            ) as replan:
                _, report = run_repair_loop(args)

            self.assertEqual(replan.call_count, 1)
            self.assertEqual(executed_states, [source_state.resolve(), replanned_state.resolve()])
            self.assertEqual(report["repair_loop_disposition"]["status"], "complete")
            first_record = json.loads(
                sorted((out_dir / "loop").glob("iteration_*/iteration_record.json"))[0]
                .read_text(encoding="utf-8")
            )
            self.assertEqual(first_record["disposition"]["status"], "continue")
            self.assertEqual(
                first_record["disposition"]["upstream_capability_replan"]["status"],
                "pass",
            )
            self.assertTrue(
                any(
                    row["role"] == "upstream_capability_replan"
                    for row in first_record["evidence_snapshots"]
                )
            )

    def test_stage8_repair_loop_accepts_fresh_plan_superseding_capability_request(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source_state.write_text("{}\n", encoding="utf-8")
            (out_dir / "sacg_state.json").write_text("{}\n", encoding="utf-8")
            first_path = out_dir / "first_report.json"
            second_path = out_dir / "second_report.json"
            replanned_state = run_dir / "repair" / "replanned_sacg_state.json"
            repair_report_path = run_dir / "repair" / "repair_report.json"
            repair_plan_path = run_dir / "repair" / "repair_plan.json"
            capability = {
                "capability_id": "vcs_timescale_error_localization",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "producer_scope": "real_board_vcs_compile_provenance",
                "target_modules": ["exact_board_compile"],
                "required_evidence": ["fresh compile provenance"],
                "rationale": "the current board compile needs bounded provenance",
            }

            first_report = {
                "status": "incomplete",
                "errors": ["upstream capability required"],
                "step_results": [
                    {
                        "result": {
                            "status": "blocked",
                            "summary": "implementation agent requires an upstream capability",
                            "framework_action_required": True,
                            "required_capabilities": [capability],
                        }
                    }
                ],
            }
            second_report = {"status": "ready", "errors": [], "step_results": []}

            def write(path: Path, value: dict) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value) + "\n", encoding="utf-8")

            def fake_plan(_args: argparse.Namespace):
                write(
                    repair_plan_path,
                    {
                        "status": "needs_repair",
                        "repair_workflow": {
                            "status": "ready",
                            "steps": [
                                {
                                    "id": "repair_step.00",
                                    "status": "ready_for_agent_patch",
                                    "source": "hierarchical_repair_loop",
                                }
                            ],
                        },
                    },
                )
                write(replanned_state, {})
                report = {
                    "outputs": {
                        "repair_plan": str(repair_plan_path),
                        "sacg_state": str(replanned_state),
                    }
                }
                write(repair_report_path, report)
                return repair_report_path, report

            executed_states: list[Path] = []

            def fake_execute(iteration_args: argparse.Namespace):
                executed_states.append(iteration_args.sacg_state)
                return (
                    (first_path, first_report)
                    if len(executed_states) == 1
                    else (second_path, second_report)
                )

            args = argparse.Namespace(
                sacg_state=source_state,
                execute_reruns=True,
                include_remote=False,
                timeout_sec=0,
                loop_until_pass=True,
                max_loop_iters=0,
            )
            with patch(
                "accagent.framework.stage_repair_execute.execute_repair",
                side_effect=fake_execute,
            ), patch(
                "accagent.framework.stage_repair.plan_repair",
                side_effect=fake_plan,
            ):
                _, report = run_repair_loop(args)

            self.assertEqual(
                executed_states,
                [source_state.resolve(), replanned_state.resolve()],
            )
            self.assertEqual(report["repair_loop_disposition"]["status"], "complete")
            first_record = json.loads(
                sorted((out_dir / "loop").glob("iteration_*/iteration_record.json"))[0]
                .read_text(encoding="utf-8")
            )
            self.assertEqual(
                first_record["disposition"]["upstream_capability_replan"]["status"],
                "pass",
            )
            self.assertTrue(
                first_record["disposition"]["upstream_capability_replan"]
                ["superseded_capability_request"]
            )

    def test_stage8_repair_loop_retries_agent_without_vcs_after_failed_source_rejection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "files": [],
                        "blockers": ["prior real-VCS failed source state"],
                        "retry_agent_without_real_tool": True,
                        "rejected_prior_failed_board_attempt": {"iteration": 4},
                    }
                ),
                encoding="utf-8",
            )

            disposition = repair_loop_disposition(
                {
                    "status": "incomplete",
                    "errors": ["agent patch was rejected"],
                    "step_results": [
                        {
                            "result": {
                                "status": "blocked",
                                "summary": "candidate restores iteration 4",
                                "agent_patch_application": str(patch_path),
                            }
                        }
                    ],
                }
            )

        self.assertEqual(disposition["status"], "continue")
        self.assertTrue(disposition["retry_agent_without_real_tool"])
        self.assertEqual(disposition["applied_files"], [])

    def test_direct_observation_stop_does_not_retry_agent_or_request_capability(self) -> None:
        output = {
            "status": "blocked",
            "blocked_reasons": [
                "current direct evidence has no authorized source edit or new probe"
            ],
            "file_edits": [],
            "required_capabilities": [],
        }
        validation = {
            "status": "pass",
            "mode": "direct_executed_contradiction",
        }
        self.assertTrue(legal_direct_observation_stop(output, validation))
        self.assertFalse(
            legal_direct_observation_stop(
                {
                    **output,
                    "required_capabilities": [
                        {"capability_id": "current_runner_provenance"}
                    ],
                },
                validation,
            )
        )

        with TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "files": [],
                        "retry_agent_without_real_tool": False,
                        "agent_decision_stop": {
                            "status": "recorded",
                            "mode": "direct_executed_contradiction",
                        },
                    }
                ),
                encoding="utf-8",
            )
            disposition = repair_loop_disposition(
                {
                    "status": "incomplete",
                    "errors": ["Agent recorded a direct-evidence decision stop"],
                    "step_results": [
                        {
                            "result": {
                                "status": "blocked",
                                "summary": "Agent recorded a direct-evidence decision stop",
                                "agent_patch_application": str(patch_path),
                            }
                        }
                    ],
                }
            )

        self.assertEqual(disposition["status"], "blocked")
        self.assertNotIn("retry_agent_without_real_tool", disposition)

    def test_exact_board_vcs_runner_feedback_invalidates_after_runner_change(self) -> None:
        with TemporaryDirectory() as temp_dir:
            runner = Path(temp_dir) / "runner.py"
            runner.write_text("print(1)\n", encoding="utf-8")
            feedback = {
                "runner_report": {
                    "value": {
                        "runner_implementation_sha256": hashlib.sha256(
                            runner.read_bytes()
                        ).hexdigest()
                    }
                }
            }
            spec = {"argv": ["python3", str(runner)]}
            self.assertTrue(
                exact_board_vcs_runner_feedback_is_current(feedback, spec)
            )
            runner.write_text("print(2)\n", encoding="utf-8")
            self.assertFalse(
                exact_board_vcs_runner_feedback_is_current(feedback, spec)
            )

    def test_exact_board_vcs_runner_feedback_binds_current_validation_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runner = root / "runner.py"
            manifest_path = root / "board_simulation_manifest.json"
            runner.write_text("print(1)\n", encoding="utf-8")
            manifest = {
                "schema_version": "spatialaccagent.board_simulation_manifest.v1",
                "status": "ready",
                "validation_mode": "compute_slot_axi",
                "top_module": "GeneratedBoardTb",
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            feedback = {
                "runner_report": {
                    "value": {
                        "runner_implementation_sha256": hashlib.sha256(
                            runner.read_bytes()
                        ).hexdigest(),
                        "validation_mode": "compute_slot_axi",
                        "preflight_manifest_projection_sha256": (
                            preflight_manifest_projection_sha256(manifest)
                        ),
                    }
                }
            }
            spec = {"argv": ["python3", str(runner)]}

            self.assertTrue(
                exact_board_vcs_runner_feedback_is_current(
                    feedback, spec, manifest_path
                )
            )
            manifest["top_module"] = "ChangedBoardTb"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertFalse(
                exact_board_vcs_runner_feedback_is_current(
                    feedback, spec, manifest_path
                )
            )
            manifest["top_module"] = "GeneratedBoardTb"
            manifest["validation_mode"] = "exact_sample_physical_ddr"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertFalse(
                exact_board_vcs_runner_feedback_is_current(
                    feedback, spec, manifest_path
                )
            )

    def test_current_exact_board_failure_is_reused_before_another_vcs_run(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            runner_implementation = root / "runner.py"
            runner_report = run_dir / "reports" / "runner.json"
            diagnosis_report = run_dir / "reports" / "diagnosis.json"
            manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            runner_implementation.write_text("print(1)\n", encoding="utf-8")
            manifest = {
                "status": "ready",
                "validation_mode": "compute_slot_axi",
                "top_module": "GeneratedBoardTb",
                "source_files": [{"source_id": "board.tb", "sha256": "1" * 64}],
                "frozen_compute_slot_identity_attestation": {
                    "status": "pass",
                    "source_identity_sha256": "2" * 64,
                    "prior_vcs_runner_report": {
                        "path": "/cert/old.json",
                        "sha256": "3" * 64,
                    },
                },
            }
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            runner = {
                "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
                "status": "fail",
                "phase": "remote_vcs",
                "runner_implementation_sha256": hashlib.sha256(
                    runner_implementation.read_bytes()
                ).hexdigest(),
                "validation_mode": "compute_slot_axi",
                "preflight_manifest_projection_sha256": (
                    preflight_manifest_projection_sha256(manifest)
                ),
            }
            runner_report.parent.mkdir(parents=True)
            runner_report.write_text(json.dumps(runner), encoding="utf-8")
            diagnosis = {
                "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
                "status": "needs_repair",
                "diagnosis_status": "ready",
                "summary": "scheduler made no semantic progress",
                "sources": [str(runner_report)],
                "repair_handoff": {"agent_should_apply_code_changes": True},
            }
            diagnosis_report.write_text(json.dumps(diagnosis), encoding="utf-8")
            feedback = {
                "status": "ready",
                "blockers": [],
                "runner_report": {
                    "path": str(runner_report),
                    "sha256": hashlib.sha256(runner_report.read_bytes()).hexdigest(),
                    "value": runner,
                },
                "diagnosis": {
                    "path": str(diagnosis_report),
                    "sha256": hashlib.sha256(diagnosis_report.read_bytes()).hexdigest(),
                    "value": diagnosis,
                },
            }
            spec = {"argv": ["python3", str(runner_implementation)]}

            with patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value=feedback,
            ):
                reused = current_exact_board_validation_evidence(
                    {}, run_dir, spec, {}, manifest_path
                )

            self.assertIsNotNone(reused)
            self.assertEqual(reused["status"], "fail")
            self.assertTrue(reused["real_tool_was_not_relaunched"])
            self.assertEqual(
                reused["current_board_vcs_feedback"]["runner_report"]["sha256"],
                feedback["runner_report"]["sha256"],
            )

            precomputed_attempt = {
                "iteration": 5,
                "iteration_record": {
                    "path": "/archive/iteration_0005/iteration_record.json",
                    "sha256": "a" * 64,
                    "iteration": 5,
                },
                "board_source_state": {"canonical_sha256": "b" * 64},
                "runner_report": feedback["runner_report"],
                "diagnosis": feedback["diagnosis"],
            }
            transport_feedback = json.loads(json.dumps(feedback))
            transport_feedback["diagnosis"]["value"]["summary"] = (
                "latest duplicate runner ended in transport failure"
            )
            transport_feedback["diagnosis"]["value"]["repair_handoff"] = {
                "agent_should_apply_code_changes": False
            }
            with (
                patch(
                    "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                    return_value=transport_feedback,
                ),
                patch(
                    "accagent.framework.stage_repair_execute.matching_failed_exact_board_attempt",
                    side_effect=AssertionError(
                        "preparation-time mutable manifests must not rematch the source"
                    ),
                ),
            ):
                precomputed_reuse = current_exact_board_validation_evidence(
                    {},
                    run_dir,
                    spec,
                    {},
                    manifest_path,
                    content_addressed_failed_attempt=precomputed_attempt,
                )

            self.assertIsNotNone(precomputed_reuse)
            self.assertTrue(
                precomputed_reuse[
                    "content_addressed_failed_source_evidence_reused"
                ]
            )
            self.assertEqual(
                precomputed_reuse["current_board_vcs_feedback"][
                    "source_iteration_record"
                ]["iteration"],
                5,
            )

            completed_experiment_diagnosis = copy.deepcopy(diagnosis)
            completed_experiment_diagnosis["summary"] = (
                "the Agent observation experiment ended in a simulator crash"
            )
            completed_experiment_diagnosis["repair_handoff"] = {
                "agent_should_apply_code_changes": False,
                "repair_scope": "simulation_environment",
            }
            completed_experiment_path = (
                run_dir / "reports" / "completed_experiment_diagnosis.json"
            )
            completed_experiment_path.write_text(
                json.dumps(completed_experiment_diagnosis), encoding="utf-8"
            )
            completed_experiment_attempt = copy.deepcopy(precomputed_attempt)
            completed_experiment_attempt["diagnosis"] = {
                "path": str(completed_experiment_path),
                "sha256": hashlib.sha256(
                    completed_experiment_path.read_bytes()
                ).hexdigest(),
                "value": completed_experiment_diagnosis,
            }
            with patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value=transport_feedback,
            ):
                completed_experiment_reuse = current_exact_board_validation_evidence(
                    {},
                    run_dir,
                    spec,
                    {},
                    manifest_path,
                    content_addressed_failed_attempt=(
                        completed_experiment_attempt
                    ),
                )

            self.assertIsNotNone(completed_experiment_reuse)
            self.assertTrue(
                completed_experiment_reuse[
                    "content_addressed_failed_source_evidence_reused"
                ]
            )
            self.assertFalse(
                completed_experiment_reuse["current_board_vcs_feedback"][
                    "diagnosis"
                ]["value"]["repair_handoff"][
                    "agent_should_apply_code_changes"
                ]
            )

            changed = json.loads(json.dumps(manifest))
            changed["source_files"][0]["sha256"] = "5" * 64
            manifest_path.write_text(json.dumps(changed), encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value=feedback,
            ):
                self.assertIsNone(
                    current_exact_board_validation_evidence(
                        {}, run_dir, spec, {}, manifest_path
                    )
                )

    def test_current_exact_board_recovers_compact_failed_history_snapshot(self) -> None:
        """A restart must not replace a current post-patch failure with stale live reports."""

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            reports = run_dir / "reports"
            repair_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            reports.mkdir(parents=True)
            repair_dir.mkdir(parents=True)
            manifest = {
                "status": "ready",
                "validation_mode": "compute_slot_axi",
                "board_simulation_preflight_plan": {
                    "vcs_compile_plan_sha256": "c" * 64,
                },
            }
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            runner_path = reports / "runner.json"
            diagnosis_path = reports / "diagnosis.json"
            stale_runner = {
                "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
                "status": "fail",
                "phase": "remote_vcs",
                "input_fingerprint_sha256": "a" * 64,
                "validation_mode": "compute_slot_axi",
                "vcs_compile_plan_sha256": "c" * 64,
                "preflight_manifest_projection_sha256": (
                    preflight_manifest_projection_sha256(manifest)
                ),
            }
            stale_diagnosis = {
                "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
                "status": "needs_repair",
                "diagnosis_status": "ready",
                "summary": "stale board failure",
                "sources": [str(runner_path)],
                "repair_handoff": {
                    "agent_should_apply_code_changes": False,
                    "repair_scope": "simulation_environment",
                },
            }
            runner_path.write_text(json.dumps(stale_runner), encoding="utf-8")
            diagnosis_path.write_text(
                json.dumps(stale_diagnosis), encoding="utf-8"
            )
            current_runner = {
                **stale_runner,
                "input_fingerprint_sha256": "b" * 64,
            }
            current_diagnosis = {
                **stale_diagnosis,
                "summary": "post-patch board failure with internal observation",
                "failure_class": "vcs_runtime_zero_time_livelock",
            }
            current_feedback = {
                "schema_version": "spatialaccagent.exact_board_vcs_feedback.v1",
                "status": "ready",
                "blockers": [],
                "runner_report": {
                    "path": str(runner_path),
                    "sha256": hashlib.sha256(
                        json.dumps(current_runner).encode("utf-8")
                    ).hexdigest(),
                    "value": current_runner,
                },
                "diagnosis": {
                    "path": str(diagnosis_path),
                    "sha256": hashlib.sha256(
                        json.dumps(current_diagnosis).encode("utf-8")
                    ).hexdigest(),
                    "value": current_diagnosis,
                },
            }
            probe_path = (
                repair_dir
                / "repair_step_00_verification_capability_probe_post_patch.json"
            )
            probe_path.write_text(
                json.dumps({"current_board_vcs_feedback": current_feedback}),
                encoding="utf-8",
            )
            compact_attempt = {
                "iteration": "recent:current",
                "board_source_state": {"canonical_sha256": "d" * 64},
                "runner_identity": {
                    "input_fingerprint_sha256": "b" * 64,
                    "vcs_compile_plan_sha256": "c" * 64,
                },
            }
            stale_feedback = {
                **current_feedback,
                "runner_report": {
                    **current_feedback["runner_report"],
                    "value": stale_runner,
                },
                "diagnosis": {
                    **current_feedback["diagnosis"],
                    "value": stale_diagnosis,
                },
            }

            with patch(
                "accagent.framework.stage_repair_execute.exact_board_vcs_feedback",
                return_value=stale_feedback,
            ):
                evidence = current_exact_board_validation_evidence(
                    {},
                    run_dir,
                    {},
                    {},
                    manifest_path,
                    content_addressed_failed_attempt=compact_attempt,
                )

            self.assertIsNotNone(evidence)
            self.assertTrue(evidence["content_addressed_failed_source_evidence_reused"])
            feedback = evidence["current_board_vcs_feedback"]
            self.assertEqual(
                feedback["runner_report"]["value"]["input_fingerprint_sha256"],
                "b" * 64,
            )
            self.assertEqual(
                feedback["content_addressed_durable_snapshot"]["path"],
                str(probe_path),
            )

    def test_post_patch_snapshot_recovers_only_same_zero_time_vcs_job(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            reports = run_dir / "reports"
            repair_dir = run_dir / "repair_execution"
            reports.mkdir(parents=True)
            repair_dir.mkdir(parents=True)
            fingerprint = "a" * 64
            remote_workdir = "/remote/job-a"
            runner_path = reports / "runner.json"
            diagnosis_path = reports / "diagnosis.json"
            generic_runner = {
                "status": "fail",
                "phase": "remote_vcs",
                "input_fingerprint_sha256": fingerprint,
                "run": {
                    "status": "fail",
                    "returncode": 87,
                    "remote_workdir": remote_workdir,
                    "failure_class": "remote_tool_failure",
                },
            }
            generic_diagnosis = {
                "status": "needs_repair",
                "diagnosis_status": "ready",
                "failure_class": "vcs_runtime_failure",
                "root_cause_class": "vcs_runtime_failure",
                "repair_handoff": {"agent_should_apply_code_changes": True},
            }
            runner_path.write_text(json.dumps(generic_runner), encoding="utf-8")
            diagnosis_path.write_text(
                json.dumps(generic_diagnosis), encoding="utf-8"
            )
            evidence = {
                "schema_version": "spatialaccagent.zero_time_livelock_evidence.v1",
                "status": "proven_zero_time_livelock",
                "remote_workdir": remote_workdir,
            }
            termination = {
                "schema_version": "spatialaccagent.zero_time_livelock_termination.v1",
                "status": "pass",
                "remote_exit_code": 87,
                "remote_workdir": remote_workdir,
                "evidence": evidence,
            }
            archived_runner = copy.deepcopy(generic_runner)
            archived_runner["run"].update(
                failure_class="zero_time_simulation_livelock",
                zero_time_livelock_evidence=evidence,
                zero_time_livelock_termination=termination,
            )
            archived_diagnosis = copy.deepcopy(generic_diagnosis)
            archived_diagnosis.update(
                failure_class="vcs_runtime_zero_time_livelock",
                root_cause_class="vcs_runtime_zero_time_livelock",
            )
            archived_diagnosis["repair_handoff"]["failure_class"] = (
                "vcs_runtime_zero_time_livelock"
            )
            archived_feedback = {
                "status": "ready",
                "blockers": [],
                "runner_report": {
                    "path": str(runner_path),
                    "sha256": hashlib.sha256(
                        json.dumps(archived_runner).encode("utf-8")
                    ).hexdigest(),
                    "value": archived_runner,
                },
                "diagnosis": {
                    "path": str(diagnosis_path),
                    "sha256": hashlib.sha256(
                        json.dumps(archived_diagnosis).encode("utf-8")
                    ).hexdigest(),
                    "value": archived_diagnosis,
                },
            }
            probe_path = (
                repair_dir
                / "repair_step_00_verification_capability_probe_post_patch.json"
            )
            probe_path.write_text(
                json.dumps({"current_board_vcs_feedback": archived_feedback}),
                encoding="utf-8",
            )
            adapter = {"diagnosis": {"path": str(diagnosis_path)}}
            vcs_spec = {"produces": [str(runner_path)]}
            analyzer_spec = {"produces": [str(diagnosis_path)]}

            recovered = exact_board_vcs_feedback(
                adapter, run_dir, vcs_spec, analyzer_spec
            )

            self.assertEqual(
                recovered["diagnosis"]["value"]["failure_class"],
                "vcs_runtime_zero_time_livelock",
            )
            self.assertEqual(
                recovered["runner_report"]["value"]["run"]["failure_class"],
                "zero_time_simulation_livelock",
            )
            self.assertEqual(
                recovered["post_patch_zero_time_livelock_recovery"]["status"],
                "ready",
            )

            archived_feedback["runner_report"]["value"]["run"][
                "remote_workdir"
            ] = "/remote/job-b"
            probe_path.write_text(
                json.dumps({"current_board_vcs_feedback": archived_feedback}),
                encoding="utf-8",
            )
            unrecovered = exact_board_vcs_feedback(
                adapter, run_dir, vcs_spec, analyzer_spec
            )
            self.assertEqual(
                unrecovered["diagnosis"]["value"]["failure_class"],
                "vcs_runtime_failure",
            )

    def test_repair_projection_ignores_only_rolling_frozen_certificate_links(self) -> None:
        plan = {
            "status": "ready",
            "validation_mode": "compute_slot_axi",
            "top_module": "board_tb",
            "source_files": [{"source_id": "board.tb", "sha256": "1" * 64}],
            "frozen_compute_slot_identity_attestation": {
                "status": "pass",
                "source_identity_sha256": "2" * 64,
                "attested_vivado_facts_sha256": "3" * 64,
                "vcs_compile_plan_sha256": "4" * 64,
                "prior_executed_manifest": {"path": "/cert/a", "sha256": "a" * 64},
                "prior_vcs_job_contract": {"path": "/cert/b", "sha256": "b" * 64},
                "prior_vcs_runner_report": {"path": "/cert/c", "sha256": "c" * 64},
            },
        }
        rolled = json.loads(json.dumps(plan))
        attestation = rolled["frozen_compute_slot_identity_attestation"]
        attestation["prior_executed_manifest"] = {
            "path": "/cert/d",
            "sha256": "d" * 64,
        }
        attestation["prior_vcs_job_contract"] = {
            "path": "/cert/e",
            "sha256": "e" * 64,
        }
        attestation["prior_vcs_runner_report"] = {
            "path": "/cert/f",
            "sha256": "f" * 64,
        }
        self.assertEqual(
            exact_board_repair_execution_projection_sha256(plan),
            exact_board_repair_execution_projection_sha256(rolled),
        )

        changed_fact = json.loads(json.dumps(rolled))
        changed_fact["frozen_compute_slot_identity_attestation"][
            "attested_vivado_facts_sha256"
        ] = "5" * 64
        self.assertNotEqual(
            exact_board_repair_execution_projection_sha256(plan),
            exact_board_repair_execution_projection_sha256(changed_fact),
        )

        changed_source = json.loads(json.dumps(rolled))
        changed_source["source_files"][0]["sha256"] = "6" * 64
        self.assertNotEqual(
            exact_board_repair_execution_projection_sha256(plan),
            exact_board_repair_execution_projection_sha256(changed_source),
        )

    def test_certified_failed_evidence_survives_rolling_attestation_links(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "current_manifest.json"
            executed_path = root / "executed_manifest.json"
            runner_path = root / "runner_report.json"
            job_path = root / "job_contract.json"
            fingerprint = "7" * 64
            stable_attestation = {
                "schema_version": "spatialaccagent.frozen_compute_slot_identity_attestation.v1",
                "status": "pass",
                "source_identity_sha256": "1" * 64,
                "attested_vivado_facts_sha256": "2" * 64,
                "vcs_compile_plan_sha256": "3" * 64,
                "prior_executed_manifest": {
                    "path": "/prior/executed.json",
                    "sha256": "4" * 64,
                },
                "prior_vcs_job_contract": {
                    "path": "/prior/job.json",
                    "sha256": "5" * 64,
                },
                "prior_vcs_runner_report": {
                    "path": "/prior/runner.json",
                    "sha256": "6" * 64,
                },
            }
            executed = {
                "status": "fail",
                "validation_mode": "compute_slot_axi",
                "top_module": "board_tb",
                "source_files": [{"source_id": "board.tb", "sha256": "8" * 64}],
                "frozen_compute_slot_identity_attestation": stable_attestation,
            }
            runner = {
                "status": "fail",
                "validation_mode": "compute_slot_axi",
                "input_fingerprint_sha256": fingerprint,
            }
            job = {"input_fingerprint_sha256": fingerprint}
            executed_path.write_text(json.dumps(executed), encoding="utf-8")
            runner_path.write_text(json.dumps(runner), encoding="utf-8")
            job_path.write_text(json.dumps(job), encoding="utf-8")
            current = json.loads(json.dumps(executed))
            current["status"] = "ready"
            current_attestation = current[
                "frozen_compute_slot_identity_attestation"
            ]
            for name, path in (
                ("prior_executed_manifest", executed_path),
                ("prior_vcs_job_contract", job_path),
                ("prior_vcs_runner_report", runner_path),
            ):
                current_attestation[name] = {
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            manifest_path.write_text(json.dumps(current), encoding="utf-8")
            feedback = {
                "runner_report": {
                    "path": str(runner_path),
                    "sha256": hashlib.sha256(runner_path.read_bytes()).hexdigest(),
                    "value": runner,
                }
            }

            self.assertTrue(
                frozen_failed_runner_matches_current_execution_semantics(
                    feedback,
                    manifest_path,
                )
            )

            feedback["runner_report"]["value"] = {**runner, "status": "pass"}
            self.assertFalse(
                frozen_failed_runner_matches_current_execution_semantics(
                    feedback,
                    manifest_path,
                )
            )

    def test_archived_board_feedback_requires_a_hash_bound_same_iteration_pair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            iteration_dir = (
                run_dir
                / "repair_execution"
                / "loop"
                / "iteration_0007"
            )
            iteration_dir.mkdir(parents=True)
            runner_snapshot = iteration_dir / "runner_case_board_vcs_functional.json"
            diagnosis_snapshot = iteration_dir / "diagnosis_vcs_functional_diagnosis.json"
            runner_snapshot.write_text(
                json.dumps({"status": "fail", "phase": "remote_vcs"}),
                encoding="utf-8",
            )
            diagnosis_snapshot.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "diagnosis_status": "ready",
                        "repair_handoff": {"agent_should_apply_code_changes": True},
                    }
                ),
                encoding="utf-8",
            )
            record_path = iteration_dir / "iteration_record.json"
            record_path.write_text(
                json.dumps(
                    {
                        "iteration": 7,
                        "evidence_snapshots": [
                            {
                                "role": "capability_report",
                                "snapshot_path": str(runner_snapshot),
                                "source_path": "/run/current/runner.json",
                                "source_sha256": hashlib.sha256(
                                    runner_snapshot.read_bytes()
                                ).hexdigest(),
                            },
                            {
                                "role": "capability_report",
                                "snapshot_path": str(diagnosis_snapshot),
                                "source_path": "/run/current/diagnosis.json",
                                "source_sha256": hashlib.sha256(
                                    diagnosis_snapshot.read_bytes()
                                ).hexdigest(),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            feedback = archived_exact_board_vcs_feedback(run_dir)
            self.assertEqual(len(feedback), 1)
            self.assertEqual(
                feedback[0]["source_iteration_record"]["iteration"],
                7,
            )
            self.assertEqual(
                feedback[0]["runner_report"]["source_path"],
                "/run/current/runner.json",
            )

            diagnosis_snapshot.write_text("{}", encoding="utf-8")
            self.assertEqual(archived_exact_board_vcs_feedback(run_dir), [])

    def test_interrupted_live_compile_uses_latest_completed_board_feedback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            live_dir = run_dir / "verification"
            archive_dir = run_dir / "repair_execution" / "loop" / "iteration_0007"
            live_dir.mkdir(parents=True)
            archive_dir.mkdir(parents=True)

            live_runner = live_dir / "case_board_vcs_functional.json"
            live_diagnosis = live_dir / "vcs_functional_diagnosis.json"
            live_runner.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "compile": {
                            "status": "fail",
                            "transport": "recovered_exact_fingerprint_detached_remote_job",
                        },
                        "run": {
                            "status": "not_run",
                            "summary": "recovered compile did not pass",
                            "termination_provenance": {
                                "status": "indeterminate",
                                "terminal_progress_event_seen": False,
                                "simulator_terminal_log": {"status": "missing"},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            live_diagnosis.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "diagnosis_status": "ready",
                        "failure_class": "vcs_elaboration_failure",
                        "repair_handoff": {"agent_should_apply_code_changes": True},
                    }
                ),
                encoding="utf-8",
            )

            archived_runner = archive_dir / "08_case_board_vcs_functional.json"
            archived_diagnosis = archive_dir / "10_vcs_functional_diagnosis.json"
            archived_runner.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "phase": "remote_vcs",
                        "compile": {"status": "pass", "returncode": 0},
                        "run": {"status": "fail", "returncode": 86},
                    }
                ),
                encoding="utf-8",
            )
            archived_diagnosis.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "diagnosis_status": "ready",
                        "failure_class": "intra_layer_spatial_pipeline_violation",
                        "repair_handoff": {"agent_should_apply_code_changes": True},
                    }
                ),
                encoding="utf-8",
            )
            record = archive_dir / "iteration_record.json"
            record.write_text(
                json.dumps(
                    {
                        "iteration": 7,
                        "evidence_snapshots": [
                            {
                                "role": "capability_report",
                                "snapshot_path": str(archived_runner),
                                "source_path": str(live_runner),
                                "source_sha256": sha256_file(archived_runner),
                            },
                            {
                                "role": "capability_report",
                                "snapshot_path": str(archived_diagnosis),
                                "source_path": str(live_diagnosis),
                                "source_sha256": sha256_file(archived_diagnosis),
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            feedback = exact_board_vcs_feedback(
                {"diagnosis": {"path": str(live_diagnosis)}},
                run_dir,
                {"produces": [str(live_runner)]},
                {"produces": [str(live_diagnosis)]},
            )

            self.assertEqual(
                feedback["diagnosis"]["value"]["failure_class"],
                "intra_layer_spatial_pipeline_violation",
            )
            self.assertEqual(
                feedback["replaced_incomplete_interrupted_feedback"]["status"],
                "ready",
            )

    def implementation_output(self, path: Path, content: str) -> dict:
        return {
            "status": "ready_to_apply",
            "approval_required_for": [],
            "file_edits": [
                {
                    "path": str(path),
                    "operation": "create",
                    "expected_sha256": "",
                    "content": content,
                    "rationale": "test harness",
                }
            ],
            "requested_validation": [],
        }

    def test_board_patch_rejects_prior_real_vcs_failed_source_before_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "board_integration"
                / "GeneratedBoardTop.sv"
            )
            target.parent.mkdir(parents=True)
            original = "module GeneratedBoardTop; wire current; endmodule\n"
            failed = "module GeneratedBoardTop; wire prior_failed; endmodule\n"
            target.write_text(original, encoding="utf-8")
            output = self.implementation_output(target, failed)
            output["file_edits"][0].update(
                {
                    "operation": "replace",
                    "expected_sha256": hashlib.sha256(
                        original.encode("utf-8")
                    ).hexdigest(),
                }
            )
            prior_attempt = {
                "iteration": 7,
                "iteration_record": {
                    "path": "/archive/iteration_0007/iteration_record.json",
                    "sha256": "a" * 64,
                },
                "board_source_state": {"rows": []},
                "board_source_edits": [],
                "agent_hypothesis": {"root_cause": "prior hypothesis"},
                "behavior_signature": {
                    "failure_class": "vcs_runtime_semantic_stall",
                    "canonical_sha256": "b" * 64,
                },
                "runner_identity": {"vcs_compile_plan_sha256": "c" * 64},
            }

            with patch(
                "accagent.framework.stage_repair_execute.matching_failed_exact_board_attempt",
                return_value=prior_attempt,
            ) as match:
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allow_board_integration=True,
                )

            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report["retry_agent_without_real_tool"])
            self.assertEqual(report["files"], [])
            self.assertEqual(
                report["rejected_prior_failed_board_attempt"]["iteration"], 7
            )
            self.assertEqual(target.read_text(encoding="utf-8"), original)
            candidate_state = match.call_args.args[1]
            self.assertEqual(
                candidate_state["candidate_changed_paths"],
                ["generated/board_integration/GeneratedBoardTop.sv"],
            )

    def test_legacy_failed_source_match_allows_novel_additional_board_edit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            board_dir.mkdir(parents=True)
            wrapper = board_dir / "GeneratedBoardTop.sv"
            testbench = board_dir / "GeneratedBoardTb.sv"
            wrapper.write_text("wrapper current\n", encoding="utf-8")
            testbench.write_text("tb current\n", encoding="utf-8")
            failed_wrapper = "wrapper failed\n"
            failed_sha = hashlib.sha256(failed_wrapper.encode("utf-8")).hexdigest()
            attempt = {
                "iteration": 3,
                "board_source_state": {
                    "rows": [
                        {
                            "path": "generated/board_integration/GeneratedBoardTop.sv",
                            "sha256": failed_sha,
                        }
                    ],
                    "legacy_tracked_sources_only": True,
                },
                "runner_identity": {
                    "runner_implementation_sha256": BOARD_VCS_RUNNER_SHA256,
                },
            }

            with patch(
                "accagent.framework.stage_repair_execute.exact_board_repair_attempt_records",
                return_value=[attempt],
            ):
                exact_reversal = exact_board_source_state(
                    run_dir,
                    staged_contents={wrapper: failed_wrapper},
                )
                novel_repair = exact_board_source_state(
                    run_dir,
                    staged_contents={
                        wrapper: failed_wrapper,
                        testbench: "tb with new agent-selected probes\n",
                    },
                )
                self.assertEqual(
                    matching_failed_exact_board_attempt(run_dir, exact_reversal)[
                        "iteration"
                    ],
                    3,
                )
                self.assertIsNone(
                    matching_failed_exact_board_attempt(run_dir, novel_repair)
                )

            stale_runner_attempt = json.loads(json.dumps(attempt))
            stale_runner_attempt["runner_identity"][
                "runner_implementation_sha256"
            ] = "0" * 64
            with patch(
                "accagent.framework.stage_repair_execute.exact_board_repair_attempt_records",
                return_value=[stale_runner_attempt],
            ):
                self.assertEqual(
                    matching_failed_exact_board_attempt(
                        run_dir, exact_reversal
                    )["iteration"],
                    3,
                )

    def test_legacy_partial_failed_source_does_not_match_live_resume_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            board_dir.mkdir(parents=True)
            wrapper = board_dir / "GeneratedBoardTop.sv"
            testbench = board_dir / "GeneratedBoardTb.sv"
            wrapper.write_text("wrapper failed\n", encoding="utf-8")
            testbench.write_text("tb changed after legacy iteration\n", encoding="utf-8")
            attempt = {
                "iteration": 3,
                "board_source_state": {
                    "rows": [
                        {
                            "path": "generated/board_integration/GeneratedBoardTop.sv",
                            "sha256": hashlib.sha256(
                                wrapper.read_bytes()
                            ).hexdigest(),
                        }
                    ],
                    "legacy_tracked_sources_only": True,
                },
                "runner_identity": {
                    "runner_implementation_sha256": BOARD_VCS_RUNNER_SHA256,
                },
            }

            with patch(
                "accagent.framework.stage_repair_execute.exact_board_repair_attempt_records",
                return_value=[attempt],
            ):
                self.assertIsNone(
                    matching_failed_exact_board_attempt(run_dir)
                )

    def test_exact_board_attempt_history_excludes_transport_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            loop_dir = run_dir / "repair_execution" / "loop"
            board_source = (
                run_dir / "generated" / "board_integration" / "BoardTop.sv"
            )
            board_source.parent.mkdir(parents=True)
            board_source.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            source_sha = hashlib.sha256(board_source.read_bytes()).hexdigest()

            def write_attempt(
                iteration: int,
                *,
                agent_should_repair: bool,
                failure_class: str,
                runner_source_sha: str | None = None,
            ) -> None:
                iteration_dir = loop_dir / f"iteration_{iteration:04d}"
                iteration_dir.mkdir(parents=True)
                artifacts = {
                    "agent_patch_application": (
                        iteration_dir / "00_agent_patch_application.json",
                        {
                            "status": "pass",
                            "files": [
                                {
                                    "path": str(board_source),
                                    "before_sha256": "0" * 64,
                                    "after_sha256": source_sha,
                                }
                            ],
                        },
                    ),
                    "runner": (
                        iteration_dir / "01_case_board_vcs_functional.json",
                        {
                            "status": "fail",
                            "runner_implementation_sha256": BOARD_VCS_RUNNER_SHA256,
                            "vcs_compile_plan_sha256": "1" * 64,
                            "checkpoint_execution": {
                                "execution_identity": {
                                    "compiled_model": {
                                        "source_rows": [
                                            {
                                                "source_id": "generated-board-source:BoardTop",
                                                "sha256": runner_source_sha
                                                or source_sha,
                                            }
                                        ]
                                    }
                                }
                            },
                        },
                    ),
                    "diagnosis": (
                        iteration_dir / "02_vcs_functional_diagnosis.json",
                        {
                            "status": "needs_repair",
                            "root_cause_class": failure_class,
                            "failure_evidence": {
                                "adaptive_semantic_stall_evidence": {
                                    "latest_stall_snapshot": {
                                        "active_boundary_observation": {
                                            "input_axi_index": 896,
                                            "output_accept_count": 127,
                                            "output_valid": 0,
                                            "output_ready": 1,
                                        }
                                    }
                                },
                                "sacg_cctg_causal_slice": {
                                    "sha256": "2" * 64,
                                    "value": {
                                        "status": "ready",
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "kernel_rearm_to_next_output",
                                            "causal_domain": "board_lifecycle",
                                            "observed": {
                                                "input_completed": 16,
                                                "output_started": 2,
                                                "output_completed": 1,
                                            },
                                        },
                                        "hierarchical_certificate_projection": {
                                            "current_board_evidence_contradicts_lower_certificate": False
                                        },
                                    },
                                }
                            },
                            "repair_handoff": {
                                "agent_should_apply_code_changes": agent_should_repair
                            },
                        },
                    ),
                    "llm_record": (
                        iteration_dir / "03_agent_result.json",
                        {
                            "output": {
                                "summary": f"attempt {iteration}",
                                "root_cause": failure_class,
                            }
                        },
                    ),
                }
                snapshots = []
                for role, (path, value) in artifacts.items():
                    path.write_text(json.dumps(value), encoding="utf-8")
                    snapshot_role = (
                        "capability_report"
                        if role in {"runner", "diagnosis"}
                        else role
                    )
                    snapshots.append(
                        {
                            "role": snapshot_role,
                            "source_path": f"/live/{path.name}",
                            "snapshot_path": str(path),
                            "source_sha256": hashlib.sha256(
                                path.read_bytes()
                            ).hexdigest(),
                        }
                    )
                record = {
                    "iteration": iteration,
                    "board_source_state": exact_board_source_state(run_dir),
                    "evidence_snapshots": snapshots,
                }
                (iteration_dir / "iteration_record.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )

            write_attempt(
                1,
                agent_should_repair=True,
                failure_class="vcs_runtime_semantic_stall",
            )
            write_attempt(
                2,
                agent_should_repair=False,
                failure_class="remote_transport_failure",
            )
            write_attempt(
                3,
                agent_should_repair=True,
                failure_class="vcs_runtime_semantic_stall",
                runner_source_sha="0" * 64,
            )

            history = exact_board_repair_attempt_history(run_dir)

        self.assertEqual(history["status"], "ready")
        self.assertEqual(
            [row["iteration"] for row in history["attempts"]],
            [1],
        )
        behavior = history["attempts"][0]["behavior_signature"]
        self.assertEqual(
            behavior["sacg_cctg_frontier_id"],
            "kernel_rearm_to_next_output",
        )
        self.assertEqual(behavior["sacg_cctg_causal_domain"], "board_lifecycle")
        self.assertFalse(behavior["lower_layer_certificate_contradicted"])
        self.assertEqual(
            behavior["causal_progress_projection"]["frontier_observed"][
                "output_started"
            ],
            2,
        )
        self.assertEqual(
            behavior["causal_progress_projection"][
                "active_boundary_observation"
            ]["output_accept_count"],
            127,
        )

    def test_exact_board_history_binds_intervention_to_quantitative_response(self) -> None:
        def behavior(frontier: str, output_beats: int) -> dict:
            progress = {
                "frontier_observed": {
                    "input_completed": 16,
                    "output_started": 2 if output_beats > 112 else 1,
                    "output_completed": 1,
                },
                "active_boundary_observation": {
                    "input_axi_index": 896,
                    "output_accept_count": output_beats,
                },
            }
            progress["canonical_sha256"] = hashlib.sha256(
                json.dumps(progress, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            result = {
                "sacg_cctg_frontier_id": frontier,
                "causal_progress_projection": progress,
            }
            result["canonical_sha256"] = hashlib.sha256(
                json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            return result

        state_b = {
            "schema_version": "spatialaccagent.exact_board_source_state.v1",
            "rows": [
                {
                    "path": "generated/board_integration/BoardTop.sv",
                    "sha256": "b" * 64,
                }
            ],
        }
        state_c = {
            "schema_version": "spatialaccagent.exact_board_source_state.v1",
            "rows": [
                {
                    "path": "generated/board_integration/BoardTop.sv",
                    "sha256": "c" * 64,
                }
            ],
        }
        state_d = {
            "schema_version": "spatialaccagent.exact_board_source_state.v1",
            "rows": [
                {
                    "path": "generated/board_integration/BoardTop.sv",
                    "sha256": "d" * 64,
                }
            ],
        }
        attempts = [
            {
                "iteration": 4,
                "board_source_state": state_b,
                "board_source_edits": [
                    {
                        "path": "generated/board_integration/BoardTop.sv",
                        "before_sha256": "a" * 64,
                        "after_sha256": "b" * 64,
                    }
                ],
                "agent_hypothesis": {"summary": "bounded continuation window"},
                "behavior_signature": behavior(
                    "kernel_output_stream_completion", 113
                ),
            },
            {
                "iteration": 5,
                "board_source_state": state_c,
                "board_source_edits": [
                    {
                        "path": "generated/board_integration/BoardTop.sv",
                        "before_sha256": "b" * 64,
                        "after_sha256": "c" * 64,
                    }
                ],
                "agent_hypothesis": {
                    "summary": "next bounded experiment",
                    "causal_prediction": {
                        "intervention_family": "bounded continuation",
                        "target_frontier_id": "kernel_output_stream_completion",
                        "expected_progress_changes": [
                            {
                                "metric": "active_boundary_observation.output_accept_count",
                                "relation": "increase_from_baseline",
                                "value": None,
                            }
                        ],
                        "falsified_if": "accepted output does not increase",
                        "evidence_refs": ["cctg-frontier-sha"],
                    },
                },
                "behavior_signature": behavior(
                    "kernel_output_stream_completion", 127
                ),
            },
            {
                "iteration": 6,
                "board_source_state": state_d,
                "board_source_edits": [
                    {
                        "path": "generated/board_integration/BoardTop.sv",
                        "before_sha256": "c" * 64,
                        "after_sha256": "d" * 64,
                    }
                ],
                "agent_hypothesis": {
                    "summary": "plateauing bounded experiment",
                    "causal_prediction": {
                        "intervention_family": "bounded continuation refinement",
                        "target_frontier_id": "kernel_output_stream_completion",
                        "expected_progress_changes": [
                            {
                                "metric": "active_boundary_observation.output_accept_count",
                                "relation": "increase_from_baseline",
                                "value": None,
                            }
                        ],
                        "falsified_if": "accepted output remains at the prior frontier",
                        "evidence_refs": ["cctg-frontier-sha"],
                    },
                },
                "behavior_signature": behavior(
                    "kernel_output_stream_completion", 127
                ),
            },
        ]

        with patch(
            "accagent.framework.stage_repair_execute.exact_board_repair_attempt_records",
            return_value=attempts,
        ):
            history = exact_board_repair_attempt_history(Path("/unused"))

        transitions = history["intervention_response_history"]["transitions"]
        self.assertEqual(len(transitions), 3)
        self.assertEqual(transitions[0]["status"], "completed_real_tool_response")
        self.assertEqual(transitions[0]["intervention_iteration"], 4)
        self.assertEqual(transitions[0]["response_iteration"], 4)
        self.assertIsNone(transitions[0]["baseline_response"])
        self.assertEqual(
            transitions[1]["observed_response"]["numeric_progress_metrics"][
                "active_boundary_observation.output_accept_count"
            ],
            127,
        )
        self.assertEqual(
            transitions[1]["observed_response"][
                "nonzero_numeric_deltas_from_baseline"
            ]["active_boundary_observation.output_accept_count"],
            14,
        )
        self.assertEqual(transitions[1]["baseline_iteration"], 4)
        self.assertEqual(
            transitions[1]["causal_prediction_evaluation"]["status"],
            "supported",
        )
        self.assertEqual(
            transitions[2]["causal_prediction_evaluation"]["status"],
            "falsified",
        )
        frontier_summary = history["intervention_response_history"][
            "frontier_response_summary"
        ]
        output_series = next(
            row
            for row in frontier_summary["varying_metric_series"]
            if row["metric"]
            == "active_boundary_observation.output_accept_count"
        )
        self.assertEqual(
            [row["value"] for row in output_series["values"]],
            [113, 127, 127],
        )
        self.assertTrue(frontier_summary["latest_response_repeats_prior_plateau"])
        self.assertEqual(frontier_summary["latest_matching_prior_iterations"], [5])
        self.assertEqual(
            frontier_summary["repeated_response_plateaus"][0]["iterations"],
            [5, 6],
        )

    def test_recent_exact_board_failure_survives_controller_restart(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            board_source = (
                run_dir / "generated" / "board_integration" / "BoardTop.sv"
            )
            board_source.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            before = hashlib.sha256(b"module BoardTop; wire before; endmodule\n").hexdigest()
            board_source.write_text(
                "module BoardTop; wire after; endmodule\n", encoding="utf-8"
            )
            after = sha256_file(board_source)
            fingerprint = "f" * 64
            runner = {
                "status": "fail",
                "input_fingerprint_sha256": fingerprint,
                "execution_identity": {
                    "compiled_model": {"source_rows": [{"sha256": after}]}
                },
            }
            diagnosis = {
                "status": "needs_repair",
                "root_cause_class": "vcs_runtime_zero_time_livelock",
                "failure_evidence": {
                    "failure_class": "vcs_runtime_zero_time_livelock",
                    "first_real_error": "simulation time stopped advancing",
                    "zero_time_livelock_evidence": {
                        "status": "proven_zero_time_livelock",
                        "last_cycle": 456,
                        "last_progress_event_count": 12,
                    },
                },
                "repair_handoff": {"agent_should_apply_code_changes": True},
            }
            runner_path = out_dir / "runner.json"
            diagnosis_path = out_dir / "diagnosis.json"
            runner_path.write_text(json.dumps(runner), encoding="utf-8")
            diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
            feedback = {
                "runner_report": {
                    "path": str(runner_path),
                    "sha256": sha256_file(runner_path),
                    "value": runner,
                },
                "diagnosis": {
                    "path": str(diagnosis_path),
                    "sha256": sha256_file(diagnosis_path),
                    "value": diagnosis,
                },
            }
            patch_application = {
                "status": "pass",
                "agent": "exact_board_integration_generation_agent",
                "files": [
                    {
                        "path": str(board_source),
                        "before_sha256": before,
                        "after_sha256": after,
                    }
                ],
            }
            llm_record = {
                "agent": "exact_board_integration_generation_agent",
                "output": {
                    "status": "ready_to_apply",
                    "summary": "change lifecycle ordering",
                    "root_cause": "start and input overlapped",
                },
            }

            persisted = persist_current_exact_board_failed_attempt(
                run_dir,
                feedback,
                patch_application=patch_application,
                llm_record=llm_record,
            )
            history = exact_board_repair_attempt_history(run_dir)
            matched = matching_failed_exact_board_attempt(run_dir)

        self.assertEqual(persisted["status"], "pass")
        self.assertEqual(history["status"], "ready")
        self.assertEqual(history["attempts"][-1]["iteration"], "recent:ffffffffffff")
        self.assertEqual(
            history["intervention_response_history"]["transitions"][-1][
                "observed_response"
            ]["zero_time_livelock"]["last_cycle"],
            456,
        )
        self.assertIsNotNone(matched)

    def test_exact_board_attempt_history_preserves_validation_only_resume(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            loop_dir = run_dir / "repair_execution" / "loop"
            iteration_dir = loop_dir / "iteration_0009"
            board_source = (
                run_dir / "generated" / "board_integration" / "BoardTop.sv"
            )
            board_source.parent.mkdir(parents=True)
            iteration_dir.mkdir(parents=True)
            board_source.write_text(
                "module BoardTop; wire resumed_failure; endmodule\n",
                encoding="utf-8",
            )
            runner_path = iteration_dir / "00_case_board_vcs_functional.json"
            diagnosis_path = iteration_dir / "01_vcs_functional_diagnosis.json"
            runner_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "runner_implementation_sha256": BOARD_VCS_RUNNER_SHA256,
                    }
                ),
                encoding="utf-8",
            )
            diagnosis_path.write_text(
                json.dumps(
                    {
                        "status": "needs_repair",
                        "root_cause_class": "vcs_runtime_semantic_stall",
                        "repair_scope": "simulation_environment",
                        "failure_evidence": {},
                        "repair_handoff": {
                            "agent_should_apply_code_changes": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            snapshots = []
            for path in (runner_path, diagnosis_path):
                snapshots.append(
                    {
                        "role": "capability_report",
                        "source_path": f"/live/{path.name}",
                        "snapshot_path": str(path),
                        "source_sha256": hashlib.sha256(
                            path.read_bytes()
                        ).hexdigest(),
                    }
                )
            record = {
                "iteration": 9,
                "board_source_state": exact_board_source_state(run_dir),
                "evidence_snapshots": snapshots,
            }
            (iteration_dir / "iteration_record.json").write_text(
                json.dumps(record), encoding="utf-8"
            )

            history = exact_board_repair_attempt_history(run_dir)
            matched = matching_failed_exact_board_attempt(run_dir)

        self.assertEqual(history["status"], "ready")
        self.assertEqual([row["iteration"] for row in history["attempts"]], [9])
        self.assertEqual(history["attempts"][0]["board_source_edits"], [])
        self.assertIsNotNone(matched)
        self.assertEqual(matched["iteration"], 9)

    def test_failed_functional_state_cannot_hide_behind_new_observation_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_root = run_dir / "generated" / "board_integration"
            adapter = board_root / "BoardAdapter.sv"
            testbench = board_root / "BoardTb.sv"
            manifest = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            adapter.parent.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            adapter.write_text("module BoardAdapter; wire window3; endmodule\n", encoding="utf-8")
            testbench.write_text("module BoardTb; wire scalar_probe; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"source": {"path": str(testbench)}}
                        }
                    }
                ),
                encoding="utf-8",
            )
            failed_adapter = "module BoardAdapter; wire full_window; endmodule\n"
            failed_state = exact_board_source_state(
                run_dir,
                staged_contents={adapter.resolve(): failed_adapter},
            )
            attempt = {"iteration": 7, "board_source_state": failed_state}
            candidate = exact_board_source_state(
                run_dir,
                staged_contents={
                    adapter.resolve(): failed_adapter,
                    testbench.resolve(): (
                        "module BoardTb; wire payload_probe; endmodule\n"
                    ),
                },
            )
            observation_only = exact_board_source_state(
                run_dir,
                staged_contents={
                    testbench.resolve(): (
                        "module BoardTb; wire payload_probe; endmodule\n"
                    )
                },
            )

            with patch(
                "accagent.framework.stage_repair_execute.exact_board_repair_attempt_records",
                return_value=[attempt],
            ):
                repeated = matching_failed_exact_board_functional_state(
                    run_dir, candidate
                )
                pure_observation = matching_failed_exact_board_functional_state(
                    run_dir, observation_only
                )

        self.assertEqual(repeated["iteration"], 7)
        self.assertIsNone(pure_observation)

    def test_compact_repair_package_preserves_failed_attempt_history(self) -> None:
        history = {
            "schema_version": "spatialaccagent.exact_board_repair_attempt_history.v1",
            "status": "ready",
            "attempts": [
                {
                    "iteration": 4,
                    "board_source_state": {"canonical_sha256": "a" * 64},
                    "behavior_signature": {"canonical_sha256": "b" * 64},
                }
            ],
        }
        observation_state = {
            "schema_version": "spatialaccagent.adaptive_observation_state.v1",
            "status": "pending_real_tool_evidence",
            "frontier_id": "frontier.current",
            "required_event_fields": ["adaptive_probe.valid"],
        }

        compact = compact_verification_capability_repair_package(
            {
                "exact_board_repair_attempt_history": history,
                "adaptive_observation_state": observation_state,
            }
        )

        self.assertEqual(compact["exact_board_repair_attempt_history"], history)
        self.assertEqual(compact["adaptive_observation_state"], observation_state)

    def finalized_manifest_resume_fixture(
        self,
        root: Path,
    ) -> tuple[Path, Path, dict, Path, Path, Path, Path]:
        run_dir = root / "run"
        out_dir = run_dir / "repair_execution"
        manifest_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
        requirements_path = (
            run_dir
            / "verification"
            / "semantic_testbench"
            / "dut_weight_binding_requirements.json"
        )
        out_dir.mkdir(parents=True)
        manifest_path.parent.mkdir(parents=True)
        requirements_path.parent.mkdir(parents=True)
        requirements_path.write_text('{"required":"contract"}\n', encoding="utf-8")
        manifest_path.write_text('{"single_layer_harness":{"agent":true}}\n', encoding="utf-8")
        agent_manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        step = {
            "id": "repair_step_00",
            "scope": "verification_capability_repair",
            "action": {
                "debug_layer": "single_transformer_layer_kernel",
                "repair_kind": "verification_capability_gap",
            },
        }
        patch_path = out_dir / "agent_patch_application.json"
        patch_path.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "blockers": [],
                    "repair_checkpoint": repair_step_checkpoint(step),
                    "files": [
                        {
                            "path": str(manifest_path),
                            "after_sha256": agent_manifest_sha,
                        }
                    ],
                    "requested_validation": [],
                }
            ),
            encoding="utf-8",
        )
        validation_path = out_dir / "agent_requested_validation.json"
        validation_path.write_text(
            json.dumps({"status": "pass", "results": [], "blockers": []}),
            encoding="utf-8",
        )
        finalized_manifest = {
            "status": "pass",
            "single_layer_harness": {"framework_validated": True},
            "materialization": {
                "source": "agent_file_edits_plus_framework_hash_validation",
                "requirements": str(requirements_path),
                "requirements_sha256": hashlib.sha256(requirements_path.read_bytes()).hexdigest(),
                "verification_scope": "single_layer_closure",
            },
            "materialization_blockers": [],
        }
        manifest_path.write_text(json.dumps(finalized_manifest), encoding="utf-8")
        materialization_path = out_dir / "dut_weight_binding_materialization.json"
        materialization_path.write_text(
            json.dumps(
                {
                    "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                    "status": "pass",
                    "manifest": str(manifest_path),
                    "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                    "single_layer_harness_materialized": True,
                    "blockers": [],
                    "source_patch_application": str(patch_path),
                    "source_patch_application_sha256": hashlib.sha256(
                        patch_path.read_bytes()
                    ).hexdigest(),
                    "source_agent_manifest": str(manifest_path),
                    "source_agent_manifest_sha256": agent_manifest_sha,
                }
            ),
            encoding="utf-8",
        )
        os.utime(patch_path, ns=(1_000_000_000, 1_000_000_000))
        os.utime(validation_path, ns=(2_000_000_000, 2_000_000_000))
        os.utime(materialization_path, ns=(3_000_000_000, 3_000_000_000))
        return (
            run_dir,
            out_dir,
            step,
            manifest_path,
            requirements_path,
            validation_path,
            materialization_path,
        )

    def test_verification_scope_uses_action_debug_layer_for_single_layer(self) -> None:
        step = {
            "scope": "verification_capability_repair",
            "action": {"debug_layer": "single_transformer_layer_kernel"},
        }

        self.assertEqual(verification_scope_for_step(step), "single_layer_closure")

    def test_existing_board_manifest_refresh_requires_real_sources_and_ready_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            source = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            source.parent.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            source.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            manifest = {
                "multilayer_harness": {
                    "source_files": [{"path": str(source)}],
                },
                "board_simulation_preflight_plan": {"top_module": "BoardTb"},
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value={"status": "ready"},
            ):
                self.assertTrue(
                    existing_board_manifest_refresh_ready(run_dir, out_dir)
                )

            source.unlink()
            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value={"status": "ready"},
            ):
                self.assertFalse(
                    existing_board_manifest_refresh_ready(run_dir, out_dir)
                )

    def test_capability_scope_prompt_rules_distinguish_leaf_and_single_layer(self) -> None:
        single_layer_rules = "\n".join(
            capability_scope_prompt_rules("single_layer_closure")
        ).lower()
        self.assertIn("single_layer_harness", single_layer_rules)
        self.assertNotIn("deferred", single_layer_rules)
        self.assertNotIn("layer-1", single_layer_rules)

        leaf_rules = "\n".join(
            capability_scope_prompt_rules("operator_leaf_closure")
        ).lower()
        self.assertIn("deferred", leaf_rules)

    def test_completed_template_instrumentation_cleanup_is_pair_bound_and_mechanical(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            persistent_root = root / "persistent"
            generated_root = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
            )
            persistent_root.mkdir(parents=True)
            generated_root.mkdir(parents=True)
            source = (
                "class Example extends Module {\n"
                "  val preserved = true.B\n"
                "// SPATIALACC_TEMPLATE_TRACE_BEGIN diagnostic\n"
                "  when(io.out.valid) { printf(p\"SPATIALACC_INTERNAL_TRACE data=${io.out.bits}\\n\") }\n"
                "// SPATIALACC_TEMPLATE_TRACE_END diagnostic\n"
                "}\n"
            )
            for path in (persistent_root / "Example.scala", generated_root / "Example.scala"):
                path.write_text(source, encoding="utf-8")

            plan = completed_template_instrumentation_cleanup_plan(
                run_dir,
                framework_template_root=persistent_root,
            )

            self.assertEqual(plan["status"], "ready_to_apply")
            self.assertEqual(plan["pair_names"], ["Example.scala"])
            self.assertEqual(len(plan["file_edits"]), 2)
            self.assertTrue(all("SPATIALACC_TEMPLATE_TRACE" not in row["content"] for row in plan["file_edits"]))
            self.assertTrue(all("val preserved = true.B" in row["content"] for row in plan["file_edits"]))

    def test_trace_record_uses_stage8_action_minimal_repair_context(self) -> None:
        record = {
            "stage_id": "stage_01_self_attention",
            "module": "AttentionGQA",
            "status": "fail",
        }

        self.assertEqual(
            trace_record_from_step(
                {
                    "action": {
                        "minimal_repair_context": {
                            "trace_record": record,
                        }
                    }
                }
            ),
            record,
        )

    def test_agent_patch_can_create_only_generated_harness_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "semantic_harness" / "LeafHarness.sv"

            report = apply_agent_file_edits(
                self.implementation_output(target, "module LeafHarness; endmodule\n"),
                run_dir,
                out_dir,
            )

            self.assertEqual(report["status"], "pass")
            self.assertTrue(target.is_file())
            self.assertEqual(len(report["files"]), 1)

    def test_agent_patch_normalizes_guarded_actionable_status_and_absent_create_aliases(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            for index, alias in enumerate(("ready", "ready_for_materialization", "pass")):
                with self.subTest(alias=alias):
                    target = (
                        run_dir
                        / "generated"
                        / "semantic_harness"
                        / f"AliasHarness{index}.sv"
                    )
                    output = self.implementation_output(
                        target,
                        f"module AliasHarness{index}; endmodule\n",
                    )
                    output["status"] = alias
                    output["file_edits"][0]["expected_sha256"] = "absent"

                    report = apply_agent_file_edits(output, run_dir, out_dir)

                    self.assertEqual(report["status"], "pass")
                    self.assertEqual(report["agent_status"], "ready_to_apply")
                    self.assertEqual(report["raw_agent_status"], alias)
                    self.assertTrue(target.is_file())
                    self.assertEqual(len(report["protocol_normalizations"]), 2)

    def test_agent_patch_serializes_structured_json_content(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            value = {
                "schema_version": "example.manifest.v1",
                "status": "generated_pending_validation",
                "nested": {"complete": True},
            }
            output = self.implementation_output(target, "placeholder")
            output["file_edits"][0]["content"] = ""
            output["file_edits"][0]["json_content"] = value

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), value)
            self.assertTrue(
                any(
                    row.get("operation") == "serialize_structured_json_content"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_agent_patch_deep_merges_hash_bound_json_without_dropping_siblings(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            target.parent.mkdir(parents=True)
            original = {
                "schema_version": "spatialaccagent.dut_weight_binding_manifest.v1",
                "immutable_model_binding": {
                    "checkpoint_sha256": "a" * 64,
                    "tensor_hashes": ["b" * 64, "c" * 64],
                },
                "board_simulation_preflight_plan": {
                    "validation_mode": "compute_slot_axi",
                    "testbench": {
                        "source": {"path": "generated/board_integration/tb.sv"},
                        "existing_observability": {"status": "ready"},
                    },
                },
            }
            target.write_text(
                json.dumps(original, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            contract = {
                "schema_version": "spatialaccagent.simulation_checkpoint_contract.v1",
                "status": "ready",
            }
            output = self.implementation_output(target, "placeholder")
            output["file_edits"][0].update(
                {
                    "operation": "merge_json",
                    "expected_sha256": hashlib.sha256(
                        target.read_bytes()
                    ).hexdigest(),
                    "content": "",
                    "json_content": {
                        "board_simulation_preflight_plan": {
                            "testbench": {
                                "simulation_checkpoint_contract": contract
                            }
                        }
                    },
                }
            )

            report = apply_agent_file_edits(output, run_dir, out_dir)
            materialized = json.loads(target.read_text(encoding="utf-8"))

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                materialized["immutable_model_binding"],
                original["immutable_model_binding"],
            )
            testbench = materialized["board_simulation_preflight_plan"]["testbench"]
            self.assertEqual(
                testbench["existing_observability"], {"status": "ready"}
            )
            self.assertEqual(testbench["simulation_checkpoint_contract"], contract)
            merge_record = next(
                row
                for row in report["protocol_normalizations"]
                if row.get("operation") == "materialize_hash_bound_deep_json_merge"
            )
            self.assertIn(
                "/board_simulation_preflight_plan/testbench/"
                "simulation_checkpoint_contract/status",
                merge_record["patched_leaf_paths"],
            )

    def test_agent_patch_rejects_stale_json_merge_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            target.parent.mkdir(parents=True)
            original = '{"preserved": true}\n'
            target.write_text(original, encoding="utf-8")
            output = self.implementation_output(target, "placeholder")
            output["file_edits"][0].update(
                {
                    "operation": "merge_json",
                    "expected_sha256": "0" * 64,
                    "content": "",
                    "json_content": {"new_contract": {"status": "ready"}},
                }
            )

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "blocked")
            self.assertIn("expected hash does not match", "\n".join(report["blockers"]))
            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_agent_patch_materializes_unique_text_replacements_without_hash(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "semantic_harness" / "TraceHarness.sv"
            target.parent.mkdir(parents=True)
            original = "module TraceHarness;\n  wire keep;\nendmodule\n"
            target.write_text(original, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace_text",
                        "content": "",
                        "text_replacements": [
                            {
                                "old_text": "  wire keep;\n",
                                "new_text": "  wire keep;\n  wire observed;\n",
                            }
                        ],
                        "rationale": "add an agent-selected observation",
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "module TraceHarness;\n  wire keep;\n  wire observed;\nendmodule\n",
            )
            self.assertEqual(
                report["files"][0]["before_sha256"],
                hashlib.sha256(original.encode("utf-8")).hexdigest(),
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "materialize_unique_text_replacements"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_agent_patch_rejects_ambiguous_text_anchor_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "semantic_harness" / "TraceHarness.sv"
            target.parent.mkdir(parents=True)
            original = "marker\nmarker\n"
            target.write_text(original, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            original.encode("utf-8")
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "marker\n", "new_text": "changed\n"}
                        ],
                        "rationale": "ambiguous test anchor",
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "blocked")
            self.assertIn("must match exactly once", "\n".join(report["blockers"]))
            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_agent_patch_anchors_are_bound_to_pre_edit_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "semantic_harness" / "TraceHarness.sv"
            target.parent.mkdir(parents=True)
            original = "first\nsecond\n"
            target.write_text(original, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            original.encode("utf-8")
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "first\n", "new_text": "first\nsecond\n"},
                            {"old_text": "second\n", "new_text": "third\n"},
                        ],
                        "rationale": "anchors refer to the original source",
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(target.read_text(encoding="utf-8"), "first\nsecond\nthird\n")

    def test_agent_patch_rejects_overlapping_text_anchors_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "semantic_harness" / "TraceHarness.sv"
            target.parent.mkdir(parents=True)
            original = "abcdef\n"
            target.write_text(original, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            original.encode("utf-8")
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "abc", "new_text": "ABC"},
                            {"old_text": "cde", "new_text": "CDE"},
                        ],
                        "rationale": "overlap test",
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "blocked")
            self.assertIn("anchors overlap", "\n".join(report["blockers"]))
            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_agent_patch_rejects_duplicate_target_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "semantic_harness" / "TraceHarness.sv"
            target.parent.mkdir(parents=True)
            original = "module TraceHarness; endmodule\n"
            target.write_text(original, encoding="utf-8")
            digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
            edit = {
                "path": str(target),
                "operation": "replace_text",
                "expected_sha256": digest,
                "content": "",
                "text_replacements": [
                    {"old_text": "TraceHarness", "new_text": "ChangedHarness"}
                ],
                "rationale": "duplicate target test",
            }
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [edit, dict(edit)],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "blocked")
            self.assertIn("duplicates an earlier resolved target", "\n".join(report["blockers"]))
            self.assertEqual(target.read_text(encoding="utf-8"), original)

    def test_agent_patch_requires_every_atomic_exact_target_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            first = run_dir / "generated" / "semantic_harness" / "First.sv"
            second = run_dir / "generated" / "semantic_harness" / "Second.sv"
            output = self.implementation_output(first, "module First; endmodule\n")

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allowed_exact_files={first.resolve(), second.resolve()},
                required_exact_files={first.resolve(), second.resolve()},
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn(
                "missing a required atomic edit target",
                "\n".join(report["blockers"]),
            )
            self.assertFalse(first.exists())
            self.assertFalse(second.exists())

    def test_board_patch_rebinds_same_batch_generated_source_hashes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            board_root = run_dir / "generated" / "board_integration"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            adapter = board_root / "DynamicSlot.v"
            testbench = board_root / "DynamicBoardTb.sv"
            monitor = board_root / "DynamicMonitor.sv"
            source_contents = {
                adapter: "module DynamicSlot; endmodule\n",
                testbench: "module DynamicBoardTb; endmodule\n",
                monitor: "module DynamicMonitor; endmodule\n",
            }
            source_rows = {
                "adapter": {
                    "source_id": "generated:adapter",
                    "role": "compute_slot_adapter",
                    "path": str(adapter),
                    "sha256": "0" * 64,
                },
                "testbench": {
                    "source_id": "generated:testbench",
                    "role": "testbench",
                    "path": str(testbench),
                },
                "monitor": {
                    "source_id": "generated:monitor",
                    "role": "protocol_monitor",
                    "path": str(monitor),
                    "sha256": "1" * 64,
                },
            }
            manifest = {
                "multilayer_harness": {
                    "source_files": [source_rows["adapter"]],
                },
                "board_simulation_preflight_plan": {
                    "multilayer_harness": {
                        "source_files": [source_rows["adapter"]],
                    },
                    "source_replacements": [
                        {
                            "generated_source_id": "generated:adapter",
                            "generated_source_path": str(adapter),
                            "generated_source_sha256": "2" * 64,
                            "source": source_rows["adapter"],
                        }
                    ],
                    "testbench": {
                        "source": source_rows["testbench"],
                        "forbidden_construct_scan": {"status": "planned"},
                    },
                    "protocol_monitor_contract": {
                        "monitors": [{"source_files": [source_rows["monitor"]]}],
                    },
                    "generated_evidence_records": [
                        {"source_id": source_rows[name]["source_id"]}
                        for name in ("adapter", "testbench", "monitor")
                    ],
                },
            }
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "create",
                        "expected_sha256": "",
                        "content": "",
                        "json_content": manifest,
                    },
                    *[
                        {
                            "path": str(path),
                            "operation": "create",
                            "expected_sha256": "",
                            "content": content,
                        }
                        for path, content in source_contents.items()
                    ],
                ],
                "requested_validation": [],
            }

            for prerequisite in (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json",
                run_dir
                / "verification"
                / "board_interface"
                / "external_simulation_fixture.json",
                run_dir / "input" / "tool_profile.json",
            ):
                prerequisite.parent.mkdir(parents=True, exist_ok=True)
                prerequisite.write_text("{}\n", encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.bind_framework_vcs_compile_plan",
                side_effect=lambda value, *_: (
                    value,
                    {
                        "status": "pass",
                        "blockers": [],
                        "ordered_command_count": 0,
                        "compile_source_count": 0,
                    },
                ),
            ):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allow_board_integration=True,
                )
            materialized = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected = {
                name: hashlib.sha256(source_contents[path].encode("utf-8")).hexdigest()
                for name, path in (
                    ("adapter", adapter),
                    ("testbench", testbench),
                    ("monitor", monitor),
                )
            }
            plan = materialized["board_simulation_preflight_plan"]

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                materialized["multilayer_harness"]["source_files"][0]["sha256"],
                expected["adapter"],
            )
            self.assertEqual(
                plan["source_replacements"][0]["generated_source_sha256"],
                expected["adapter"],
            )
            self.assertEqual(
                plan["testbench"]["source"]["sha256"], expected["testbench"]
            )
            self.assertEqual(
                plan["testbench"]["forbidden_construct_scan"]["source_sha256"],
                expected["testbench"],
            )
            evidence_hashes = {
                row["source_id"]: row["source_sha256"]
                for row in plan["generated_evidence_records"]
            }
            self.assertEqual(evidence_hashes["generated:adapter"], expected["adapter"])
            self.assertEqual(evidence_hashes["generated:testbench"], expected["testbench"])
            self.assertEqual(evidence_hashes["generated:monitor"], expected["monitor"])
            self.assertTrue(
                any(
                    row.get("operation") == "bind_agent_owned_board_source_hashes"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_board_text_patch_deterministically_rebinds_existing_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            board_root = run_dir / "generated" / "board_integration"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench = board_root / "BoardTb.sv"
            testbench.parent.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            original = "module BoardTb;\n  wire progress;\nendmodule\n"
            testbench.write_text(original, encoding="utf-8")
            source = {
                "source_id": "generated:testbench",
                "role": "testbench",
                "path": str(testbench),
                "sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
            }
            manifest = {
                "multilayer_harness": {"source_files": []},
                "board_simulation_preflight_plan": {
                    "validation_mode": "compute_slot_axi",
                    "testbench": {
                        "source": source,
                        "forbidden_construct_scan": {"status": "planned"},
                    },
                    "generated_evidence_records": [
                        {"source_id": "generated:testbench"}
                    ],
                },
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            for prerequisite in (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json",
                run_dir / "input" / "tool_profile.json",
            ):
                prerequisite.parent.mkdir(parents=True, exist_ok=True)
                prerequisite.write_text("{}\n", encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(testbench),
                        "operation": "replace_text",
                        "expected_sha256": source["sha256"],
                        "content": "",
                        "text_replacements": [
                            {
                                "old_text": "  wire progress;\n",
                                "new_text": "  wire progress;\n  wire heartbeat;\n",
                            }
                        ],
                        "rationale": "add board observability",
                    }
                ],
                "requested_validation": [],
            }
            generation_record_path = out_dir / "llm" / "generation_result.json"
            generation_record = {
                "agent": "exact_board_integration_generation_agent",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
            }
            trusted_generation = {
                "status": "pass",
                "sha256": "a" * 64,
                "prompt_path": str(out_dir / "llm" / "prompt.md"),
                "prompt_sha256": "b" * 64,
            }

            with patch(
                "accagent.framework.stage_repair_execute.bind_framework_vcs_compile_plan",
                side_effect=lambda value, *_: (
                    value,
                    {
                        "status": "pass",
                        "blockers": [],
                        "ordered_command_count": 0,
                        "compile_source_count": 0,
                    },
                ),
            ), patch(
                "accagent.framework.stage_repair_execute."
                "select_trusted_exact_board_generation_record",
                return_value=(
                    generation_record_path,
                    generation_record,
                    trusted_generation,
                ),
            ):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allow_board_integration=True,
                )

            materialized = json.loads(manifest_path.read_text(encoding="utf-8"))
            final_hash = hashlib.sha256(testbench.read_bytes()).hexdigest()
            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                materialized["board_simulation_preflight_plan"]["testbench"][
                    "source"
                ]["sha256"],
                final_hash,
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "stage_existing_manifest_for_board_source_hash_rebinding"
                    for row in report["protocol_normalizations"]
                )
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "bind_exact_board_llm_generation_provenance"
                    for row in report["protocol_normalizations"]
                )
            )
            self.assertEqual(
                materialized["multilayer_harness"]["generation_provenance"][
                    "model"
                ],
                "gpt-test-board",
            )

    def test_semantic_rtl_patch_rebinds_shared_manifests_only_for_changed_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            source = (
                run_dir
                / "generated"
                / "semantic_harness"
                / "single_layer"
                / "GatedMLP.sv"
            )
            semantic_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "semantic_testbench_manifest.json"
            )
            binding_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            source.parent.mkdir(parents=True)
            semantic_path.parent.mkdir(parents=True)
            binding_path.parent.mkdir(parents=True)
            original = "module GatedMLP;\n  wire old_signal;\nendmodule\n"
            updated = "module GatedMLP;\n  wire new_signal;\nendmodule\n"
            source.write_text(original, encoding="utf-8")
            old_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
            new_hash = hashlib.sha256(updated.encode("utf-8")).hexdigest()
            unrelated_hash = "f" * 64
            source_row = {"path": str(source), "sha256": old_hash}
            semantic_path.write_text(
                json.dumps(
                    {
                        "single_layer": {"dut_harness": {"source_files": [source_row]}},
                        "unrelated": {"path": str(source.parent / "Other.sv"), "sha256": unrelated_hash},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            binding_path.write_text(
                json.dumps(
                    {
                        "single_layer_harness": {"source_files": [source_row]},
                        "multilayer_harness": {"source_files": []},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(source),
                        "operation": "replace_text",
                        "expected_sha256": old_hash,
                        "content": "",
                        "text_replacements": [
                            {
                                "old_text": "wire old_signal;",
                                "new_text": "wire new_signal;",
                            }
                        ],
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
                allowed_semantic_rtl_files={source.resolve()},
                require_exact_source_hash=True,
            )

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(sha256_file(source), new_hash)
            semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            self.assertEqual(
                semantic["single_layer"]["dut_harness"]["source_files"][0]["sha256"],
                new_hash,
            )
            self.assertEqual(
                binding["single_layer_harness"]["source_files"][0]["sha256"],
                new_hash,
            )
            self.assertEqual(semantic["unrelated"]["sha256"], unrelated_hash)
            operations = {
                row.get("operation") for row in report["protocol_normalizations"]
            }
            self.assertIn("stage_manifest_for_semantic_source_hash_rebinding", operations)
            self.assertIn("rebind_changed_source_hashes_in_manifest", operations)

    def test_changed_source_manifest_rebind_rejects_wrong_applied_bytes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = run_dir / "generated" / "semantic_harness" / "single_layer" / "Kernel.sv"
            source.parent.mkdir(parents=True)
            source.write_text("module Kernel; endmodule\n", encoding="utf-8")
            actual = sha256_file(source)
            manifest = {"source_files": [{"path": str(source), "sha256": "0" * 64}]}

            _, report = rebind_changed_source_hashes_in_manifest(
                manifest,
                run_dir,
                {source.resolve(): ("0" * 64, "1" * 64)},
                require_match=True,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("does not match its recorded after hash", "\n".join(report["blockers"]))
            self.assertEqual(manifest["source_files"][0]["sha256"], "0" * 64)

    def test_interrupted_board_semantic_patch_rebinds_shared_manifests(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = (
                run_dir
                / "generated"
                / "semantic_harness"
                / "single_layer"
                / "GatedMLP.sv"
            )
            source.parent.mkdir(parents=True)
            old = "module GatedMLP; wire old_signal; endmodule\n"
            new = "module GatedMLP; wire new_signal; endmodule\n"
            source.write_text(new, encoding="ascii")
            old_hash = hashlib.sha256(old.encode("ascii")).hexdigest()
            new_hash = hashlib.sha256(new.encode("ascii")).hexdigest()
            semantic_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "semantic_testbench_manifest.json"
            )
            binding_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            board_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            for path, payload in (
                (
                    semantic_path,
                    {"single_layer": {"dut_harness": {"source_files": [
                        {"path": str(source), "sha256": old_hash}
                    ]}}},
                ),
                (
                    binding_path,
                    {"single_layer_harness": {"source_files": [
                        {"path": str(source), "sha256": old_hash}
                    ]}},
                ),
                (
                    board_path,
                    {"single_layer_harness": {"source_files": [
                        {"path": str(source), "sha256": old_hash}
                    ]}},
                ),
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload), encoding="utf-8")

            patch_report = {
                "status": "pass",
                "blockers": [],
                "files": [{
                    "path": str(source),
                    "before_sha256": old_hash,
                    "after_sha256": new_hash,
                }],
            }
            changes = applied_semantic_source_hash_changes(patch_report, run_dir)
            result = rebind_applied_semantic_source_manifests(run_dir, changes)

            self.assertEqual(result["status"], "pass", result)
            self.assertEqual(
                json.loads(semantic_path.read_text(encoding="utf-8"))[
                    "single_layer"
                ]["dut_harness"]["source_files"][0]["sha256"],
                new_hash,
            )
            self.assertEqual(
                json.loads(binding_path.read_text(encoding="utf-8"))[
                    "single_layer_harness"
                ]["source_files"][0]["sha256"],
                new_hash,
            )
            self.assertEqual(
                json.loads(board_path.read_text(encoding="utf-8"))[
                    "single_layer_harness"
                ]["source_files"][0]["sha256"],
                new_hash,
            )

    def test_recovery_collects_current_and_historical_applied_semantic_patches(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_root = run_dir / "generated" / "semantic_harness" / "single_layer"
            elementwise = source_root / "ElementwiseMul.sv"
            gated = source_root / "GatedMLP.sv"
            source_root.mkdir(parents=True)
            elementwise.write_text("module ElementwiseMul; new endmodule\n", encoding="ascii")
            gated.write_text("module GatedMLP; current endmodule\n", encoding="ascii")
            elementwise_hash = sha256_file(elementwise)
            gated_hash = sha256_file(gated)
            history_root = run_dir / "repair_execution" / "loop"
            history_root.mkdir(parents=True)

            def write_patch(iteration: str, rows: list[dict[str, str]]) -> None:
                path = history_root / iteration / (
                    "00_agent_patch_application_agent_patch_application.json"
                )
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps({"status": "pass", "blockers": [], "files": rows}),
                    encoding="utf-8",
                )

            write_patch(
                "iteration_0973",
                [{
                    "path": str(elementwise),
                    "before_sha256": "1" * 64,
                    "after_sha256": elementwise_hash,
                }],
            )
            write_patch(
                "iteration_0988",
                [{
                    "path": str(gated),
                    "before_sha256": "2" * 64,
                    "after_sha256": gated_hash,
                }],
            )
            write_patch(
                "iteration_0990",
                [{
                    "path": str(elementwise),
                    "before_sha256": "3" * 64,
                    "after_sha256": "4" * 64,
                }],
            )
            current_patch = {
                "status": "pass",
                "blockers": [],
                "files": [{
                    "path": str(gated),
                    "before_sha256": "5" * 64,
                    "after_sha256": gated_hash,
                }],
            }

            changes = all_applied_semantic_source_hash_changes(current_patch, run_dir)

            self.assertEqual(
                changes,
                {
                    elementwise.resolve(): ("1" * 64, elementwise_hash),
                    gated.resolve(): ("5" * 64, gated_hash),
                },
            )

    def test_recovery_rejects_historical_semantic_patch_when_current_bytes_changed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = (
                run_dir
                / "generated"
                / "semantic_harness"
                / "single_layer"
                / "ElementwiseMul.sv"
            )
            source.parent.mkdir(parents=True)
            source.write_text("module ElementwiseMul; changed endmodule\n", encoding="ascii")
            history = (
                run_dir
                / "repair_execution"
                / "loop"
                / "iteration_0973"
                / "00_agent_patch_application_agent_patch_application.json"
            )
            history.parent.mkdir(parents=True)
            history.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                        "files": [{
                            "path": str(source),
                            "before_sha256": "1" * 64,
                            "after_sha256": "2" * 64,
                        }],
                    }
                ),
                encoding="utf-8",
            )

            changes = all_applied_semantic_source_hash_changes({}, run_dir)

            self.assertEqual(changes, {})

    def test_interrupted_board_semantic_patch_reuses_passed_single_layer_gate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            source = run_dir / "generated" / "semantic_harness" / "Kernel.sv"
            source.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            source.write_text("module Kernel; endmodule\n", encoding="ascii")
            source_hash = sha256_file(source)
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "action": {"repair_kind": "board_semantic_rtl_repair"},
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                        "repair_checkpoint": repair_step_checkpoint(step),
                        "files": [{
                            "path": str(source),
                            "before_sha256": "0" * 64,
                            "after_sha256": source_hash,
                        }],
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "agent_requested_validation.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            certificate = (
                run_dir
                / "verification"
                / "single_layer"
                / "single_layer_functional_report.json"
            )
            certificate.parent.mkdir(parents=True)
            certificate.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.rebind_applied_semantic_source_manifests",
                return_value={"status": "pass", "blockers": []},
            ), patch(
                "accagent.framework.stage_repair_execute.run_board_semantic_rtl_single_layer_gate",
                return_value={"status": "pass", "summary": "gate passed"},
            ) as gate, patch(
                "accagent.framework.stage_repair_execute.run_agent_requested_validation",
                return_value={"status": "pass", "requests": 0, "blockers": []},
            ):
                result = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    0,
                    step=step,
                    case_adapter={"case_id": "test"},
                )

            self.assertEqual(result["status"], "pass", result)
            self.assertTrue(result["force_board_manifest_finalization"])
            self.assertTrue(
                result["board_semantic_rtl_single_layer_gate"]["reused_existing_certificate"]
            )
            gate.assert_not_called()

    def test_board_manifest_materializer_binds_validated_framework_vcs_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            for path in (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json",
                run_dir
                / "verification"
                / "board_interface"
                / "external_simulation_fixture.json",
                run_dir / "input" / "tool_profile.json",
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            compile_authority = {
                "vivado_facts_path": "/facts.json",
                "vivado_facts_sha256": "1" * 64,
                "simulator_export_context_sha256s": ["2" * 64],
                "external_fixture_contract_sha256": "3" * 64,
                "external_fixture_export_context_sha256s": ["4" * 64],
            }
            plan = {
                "schema_version": "spatialaccagent.vcs_compile_plan.v1",
                "status": "ready",
                "tool_binding": {
                    "role": "functional_verification",
                    "name": "vcs",
                    "host": "dynamic.test",
                    "port": 22,
                    "executable": "vcs",
                    "env": {},
                },
                "compile_authority": compile_authority,
                "top_module": "DynamicBoardTb",
                "ordered_commands": [
                    {
                        "order": 0,
                        "phase": "compile",
                        "tool_role": "functional_verification",
                        "executable": "vlogan",
                        "argv": [
                            "-work",
                            "xil_defaultlib",
                            {"source_id": "generated:testbench"},
                        ],
                        "source_ids": ["generated:testbench"],
                        "cwd": "vcs_work",
                        "env": {},
                        "shell": False,
                        "authority_refs": ["2" * 64],
                    },
                    {
                        "order": 1,
                        "phase": "elaborate",
                        "tool_role": "functional_verification",
                        "executable": "vcs",
                        "argv": ["DynamicBoardTb", "-o", "simv"],
                        "source_ids": [],
                        "cwd": "vcs_work",
                        "env": {},
                        "shell": False,
                        "authority_refs": ["2" * 64, "4" * 64],
                    },
                ],
                "output": "simv",
            }
            authority = {
                "expanded_source_authority": {
                    "vcs_command_rewrite_authority": {
                        "counts": {"total_sources": 1},
                        "ordered_source_ids": ["generated:testbench"],
                        "manifest_ready_vcs_compile_plan": plan,
                    }
                }
            }
            manifest = {
                "status": "ready",
                "multilayer_harness": {"top_module": "DynamicBoardTop"},
                "board_simulation_preflight_plan": {
                    "top_module": "DynamicBoardTb",
                    "testbench": {"top_module": "DynamicBoardTb"},
                },
            }
            output = self.implementation_output(
                manifest_path, json.dumps(manifest)
            )

            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value=authority,
            ):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allow_board_integration=True,
                )

            materialized = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                materialized["board_simulation_preflight_plan"]["vcs_compile_plan"],
                plan,
            )
            self.assertTrue(
                any(
                    row.get("operation") == "bind_framework_vcs_compile_plan"
                    for row in report["protocol_normalizations"]
                )
            )
            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value=authority,
            ):
                bound_once, first_binding = bind_framework_vcs_compile_plan(
                    manifest,
                    run_dir,
                    out_dir,
                    manifest_path,
                )
                bound_twice, second_binding = bind_framework_vcs_compile_plan(
                    bound_once,
                    run_dir,
                    out_dir,
                    manifest_path,
                )
            self.assertEqual(first_binding["status"], "pass")
            self.assertEqual(second_binding["status"], "pass")
            self.assertEqual(bound_once, bound_twice)
            self.assertEqual(
                first_binding["vcs_compile_plan_sha256"],
                second_binding["vcs_compile_plan_sha256"],
            )
            module_alias_manifest = copy.deepcopy(manifest)
            module_alias_manifest["board_simulation_preflight_plan"][
                "testbench"
            ] = {"module": "DynamicBoardTb"}
            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value=authority,
            ):
                alias_bound, alias_binding = bind_framework_vcs_compile_plan(
                    module_alias_manifest,
                    run_dir,
                    out_dir,
                    manifest_path,
                )
            self.assertEqual(alias_binding["status"], "pass")
            self.assertEqual(
                alias_bound["board_simulation_preflight_plan"]["testbench"][
                    "top_module"
                ],
                "DynamicBoardTb",
            )
            invalid_authority = json.loads(json.dumps(authority))
            invalid_authority["expanded_source_authority"][
                "vcs_command_rewrite_authority"
            ]["manifest_ready_vcs_compile_plan"]["ordered_commands"].pop()
            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value=invalid_authority,
            ):
                _, rejected = bind_framework_vcs_compile_plan(
                    manifest,
                    run_dir,
                    out_dir,
                    manifest_path,
                )
            self.assertEqual(rejected["status"], "blocked")
            self.assertTrue(rejected["blockers"])

            reordered_authority = json.loads(json.dumps(authority))
            reordered_plan = reordered_authority["expanded_source_authority"][
                "vcs_command_rewrite_authority"
            ]["manifest_ready_vcs_compile_plan"]
            reordered_plan["ordered_commands"][0]["argv"][-1][
                "source_id"
            ] = "generated:other"
            reordered_plan["ordered_commands"][0]["source_ids"] = [
                "generated:other"
            ]
            with patch(
                "accagent.framework.stage_repair_execute.board_manifest_lossless_rewrite_authority",
                return_value=reordered_authority,
            ):
                _, rejected = bind_framework_vcs_compile_plan(
                    manifest,
                    run_dir,
                    out_dir,
                    manifest_path,
                )
            self.assertEqual(rejected["status"], "blocked")
            self.assertTrue(
                any("source order differs" in value for value in rejected["blockers"])
            )

    def test_board_manifest_binding_fails_closed_without_authority_inputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            manifest = {
                "board_simulation_preflight_plan": {
                    "top_module": "DynamicBoardTb",
                    "testbench": {"top_module": "DynamicBoardTb"},
                }
            }

            report = apply_agent_file_edits(
                self.implementation_output(manifest_path, json.dumps(manifest)),
                run_dir,
                out_dir,
                allow_board_integration=True,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertFalse(manifest_path.exists())
            self.assertTrue(
                any(
                    "framework VCS-plan binding prerequisites are missing" in value
                    for value in report["blockers"]
                )
            )

    def test_authoritative_board_weight_artifact_keeps_complete_segment_integrity(self) -> None:
        manifest = {
            "status": "pass",
            "path": "/dynamic/weights.bin",
            "image_sha256": "a" * 64,
            "total_bytes": 16,
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "packed_tensor_hashes": ["b" * 64],
            "layer_segments": [
                {
                    "layer": 0,
                    "sha256": "c" * 64,
                    "payload_sha256": "d" * 64,
                    "stage_segments": [{"sha256": "e" * 64}],
                }
            ],
        }

        artifact = authoritative_board_weight_artifact(manifest)

        self.assertEqual(artifact["path"], manifest["path"])
        self.assertEqual(artifact["sha256"], manifest["image_sha256"])
        self.assertEqual(artifact["layer_segments"], manifest["layer_segments"])

    def test_agent_patch_rejects_structured_json_for_non_json_target(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            output = self.implementation_output(target, "")
            output["file_edits"][0]["json_content"] = {"module": "BoardTop"}

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertFalse(target.exists())
            self.assertIn("allowed only for .json", " ".join(report["blockers"]))

    def test_generation_record_uses_the_same_guarded_ready_alias_contract(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_path = root / "prompt.md"
            prompt_path.write_text("bound prompt\n", encoding="utf-8")
            record_path = root / "generation.json"
            base_output = {
                "agent": "board_agent",
                "stage": "repair_execution",
                "status": "ready_for_materialization",
                "approval_required_for": [],
                "blocked_reasons": [],
                "file_edits": [{"path": "generated/board.sv"}],
            }

            def write_record(output: dict) -> None:
                record_path.write_text(
                    json.dumps(
                        {
                            "agent": "board_agent",
                            "stage": "repair_execution",
                            "mode": "llm",
                            "used_fallback": False,
                            "error": None,
                            "result_path": str(record_path),
                            "request_path": str(prompt_path),
                            "prompt_hash": hashlib.sha256(
                                prompt_path.read_bytes()
                            ).hexdigest(),
                            "raw_text": json.dumps(output),
                            "output": output,
                        }
                    ),
                    encoding="utf-8",
                )

            write_record(base_output)
            trusted = trusted_exact_board_generation_record(
                record_path,
                expected_agent="board_agent",
                expected_status="ready_to_apply",
            )
            self.assertEqual(trusted["status"], "pass")

            for mutation in (
                {"approval_required_for": ["human"]},
                {"blocked_reasons": ["missing evidence"]},
                {"file_edits": []},
            ):
                with self.subTest(mutation=mutation):
                    output = {**base_output, **mutation}
                    write_record(output)
                    rejected = trusted_exact_board_generation_record(
                        record_path,
                        expected_agent="board_agent",
                        expected_status="ready_to_apply",
                    )
                    self.assertEqual(rejected["status"], "invalid")

    def test_generation_record_recovers_current_hash_bound_loop_snapshot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "repair_execution"
            llm_dir = out_dir / "llm"
            iteration_dir = out_dir / "loop" / "iteration_0006"
            llm_dir.mkdir(parents=True)
            iteration_dir.mkdir(parents=True)
            live_record_path = (
                llm_dir / "exact_board_integration_generation_agent_result.json"
            )
            live_prompt_path = (
                llm_dir
                / "exact_board_integration_generation_agent_compact_retry_prompt.md"
            )
            live_record_path.write_text(
                json.dumps({"error": "later transport failure"}), encoding="utf-8"
            )
            live_prompt_path.write_text("later prompt", encoding="utf-8")
            archived_prompt_path = (
                iteration_dir
                / "02_request_path_exact_board_integration_generation_agent_compact_retry_prompt.md"
            )
            archived_prompt_path.write_text("successful prompt", encoding="utf-8")
            prompt_sha256 = hashlib.sha256(
                archived_prompt_path.read_bytes()
            ).hexdigest()
            edited_path = Path(temp_dir) / "generated" / "board.sv"
            relative_edited_path = os.path.relpath(edited_path, Path.cwd())
            output = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "approval_required_for": [],
                "blocked_reasons": [],
                "file_edits": [
                    {
                        "path": relative_edited_path,
                        "operation": "replace_text",
                    }
                ],
            }
            archived_record = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(live_record_path),
                "compact_retry_request_path": str(live_prompt_path),
                "compact_retry_prompt_hash": prompt_sha256,
                "output": output,
                "raw_text": json.dumps(output),
            }
            archived_record_path = (
                iteration_dir
                / "01_llm_record_exact_board_integration_generation_agent_result.json"
            )
            archived_record_path.write_text(
                json.dumps(archived_record), encoding="utf-8"
            )
            patch_report = {
                "status": "pass",
                "blockers": [],
                "files": [{"path": str(edited_path), "after_sha256": "a" * 64}],
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(json.dumps(patch_report), encoding="utf-8")
            archived_patch_path = (
                iteration_dir / "00_agent_patch_application_agent_patch_application.json"
            )
            archived_patch_path.write_text(
                json.dumps(patch_report), encoding="utf-8"
            )

            def evidence(
                role: str,
                snapshot_path: Path,
                source_path: Path,
            ) -> dict:
                return {
                    "role": role,
                    "snapshot_path": str(snapshot_path),
                    "source_path": str(source_path),
                    "source_sha256": hashlib.sha256(
                        snapshot_path.read_bytes()
                    ).hexdigest(),
                }

            iteration_path = iteration_dir / "iteration_record.json"
            iteration_path.write_text(
                json.dumps(
                    {
                        "iteration": 6,
                        "evidence_snapshots": [
                            evidence(
                                "llm_record",
                                archived_record_path,
                                live_record_path,
                            ),
                            evidence(
                                "request_path",
                                archived_prompt_path,
                                live_prompt_path,
                            ),
                            evidence(
                                "agent_patch_application",
                                archived_patch_path,
                                patch_path,
                            ),
                        ],
                    }
                ),
                encoding="utf-8",
            )

            selected_path, _, trusted = (
                select_trusted_exact_board_generation_record(
                    out_dir,
                    expected_status="ready_to_apply",
                )
            )
            self.assertEqual(selected_path, archived_record_path)
            self.assertEqual(trusted["status"], "pass")
            self.assertEqual(
                trusted["source_iteration_record"]["iteration"],
                6,
            )

            archived_prompt_path.write_text("tampered", encoding="utf-8")
            _, _, rejected = select_trusted_exact_board_generation_record(
                out_dir,
                expected_status="ready_to_apply",
            )
            self.assertEqual(rejected["status"], "absent")

    def test_board_integration_write_boundary_requires_explicit_layer3_scope(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "board_integration" / "BoardScheduler.sv"
            output = self.implementation_output(target, "module BoardScheduler; endmodule\n")

            blocked = apply_agent_file_edits(output, run_dir, out_dir)
            applied = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )

            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(applied["status"], "pass")
            self.assertTrue(target.is_file())

    def test_board_manifest_replace_preserves_certified_lower_layer_bindings(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            target.parent.mkdir(parents=True)
            certified = {
                "status": "pass",
                "stage_harnesses": {"stage_dynamic": {"top_module": "LeafTop"}},
                "single_layer_harness": {"top_module": "ConnectedTop"},
            }
            target.write_text(json.dumps(certified), encoding="utf-8")
            agent_manifest = {
                "status": "ready",
                "stage_harnesses": {},
                "single_layer_harness": {"top_module": "Truncated"},
                "multilayer_harness": {"top_module": "BoardTop"},
            }
            output = self.implementation_output(
                target,
                json.dumps(agent_manifest),
            )
            output["file_edits"][0]["operation"] = "replace"
            output["file_edits"][0]["expected_sha256"] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )
            materialized = json.loads(target.read_text(encoding="utf-8"))

            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                materialized["stage_harnesses"], certified["stage_harnesses"]
            )
            self.assertEqual(
                materialized["single_layer_harness"],
                certified["single_layer_harness"],
            )
            self.assertEqual(
                materialized["multilayer_harness"],
                agent_manifest["multilayer_harness"],
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "preserve_certified_lower_layer_bindings"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_board_manifest_replace_binds_current_llm_generation_provenance(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            llm_dir.mkdir(parents=True)
            prompt_path = llm_dir / "exact_board_prompt.md"
            prompt_path.write_text("generate exact board integration\n", encoding="utf-8")
            prompt_sha = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
            record_path = llm_dir / "exact_board_integration_generation_agent_result.json"
            llm_output = {
                "schema_version": "spatialaccagent.exact_board_integration_generation_agent.v1",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "approval_required_for": [],
                "blocked_reasons": [],
                "file_edits": [],
            }
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "compact_retry_request_path": str(prompt_path),
                "compact_retry_prompt_hash": prompt_sha,
                "output": llm_output,
                "raw_text": json.dumps(llm_output, sort_keys=True),
            }
            record_path.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            target.parent.mkdir(parents=True)
            certified = {
                "status": "pass",
                "stage_harnesses": {"stage_dynamic": {"top_module": "LeafTop"}},
                "single_layer_harness": {"top_module": "ConnectedTop"},
            }
            target.write_text(json.dumps(certified), encoding="utf-8")
            agent_manifest = {
                "status": "ready",
                "multilayer_harness": {
                    "top_module": "BoardTop",
                    "generation_provenance": {
                        "mode": "llm",
                        "prompt_sha256": None,
                        "model": "stale",
                    },
                },
            }
            output = self.implementation_output(target, json.dumps(agent_manifest))
            output["file_edits"][0]["operation"] = "replace"
            output["file_edits"][0]["expected_sha256"] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )
            materialized = json.loads(target.read_text(encoding="utf-8"))
            provenance = materialized["multilayer_harness"]["generation_provenance"]

            self.assertEqual(report["status"], "pass")
            self.assertEqual(provenance["agent_id"], "exact_board_integration_generation_agent")
            self.assertEqual(provenance["model"], "gpt-test-board")
            self.assertFalse(provenance["used_fallback"])
            self.assertEqual(provenance["prompt_sha256"], prompt_sha)
            self.assertEqual(provenance["prompt_path"], str(prompt_path))
            self.assertEqual(provenance["record_path"], str(record_path))
            self.assertEqual(
                provenance["record_sha256"],
                hashlib.sha256(record_path.read_bytes()).hexdigest(),
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "bind_exact_board_llm_generation_provenance"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_board_provenance_only_noop_result_is_reused_and_hash_bound(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            llm_dir.mkdir(parents=True)
            prompt_path = llm_dir / "exact_board_prompt.md"
            prompt_path.write_text("bind exact board provenance\n", encoding="utf-8")
            prompt_sha = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest = {
                "status": "ready",
                "multilayer_harness": {
                    "top_module": "BoardTop",
                    "generation_provenance": {
                        "agent_id": "exact_board_integration_generation_agent",
                        "mode": "llm",
                        "used_fallback": False,
                    },
                },
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            provenance_intent = {
                "multilayer_harness": {
                    "generation_provenance": {
                        "agent_id": "exact_board_integration_generation_agent",
                        "mode": "llm",
                        "used_fallback": False,
                    }
                }
            }
            output = {
                "schema_version": "spatialaccagent.exact_board_integration_generation_agent.v1",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "summary": "bind the current exact-board Agent provenance",
                "root_cause": "derived hashes are framework-owned",
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": provenance_intent,
                        "rationale": "request only the trusted provenance bind",
                    }
                ],
                "requested_validation": [],
                "blocked_reasons": [],
                "approval_required_for": [],
            }
            record_path = (
                llm_dir / "exact_board_integration_generation_agent_result.json"
            )
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "compact_retry_request_path": str(prompt_path),
                "compact_retry_prompt_hash": prompt_sha,
                "output": output,
                "raw_text": json.dumps(output, sort_keys=True),
            }
            record_path.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            step = {
                "id": "repair_step_0",
                "scope": "verification",
                "action": {
                    "repair_kind": "exact_board_integration_harness",
                    "violated_contract": "exact board provenance must be bound",
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch = {
                "schema_version": "spatialaccagent.agent_patch_application.v1",
                "status": "blocked",
                "blockers": [
                    f"file_edits[0] merge_json leaves the JSON object unchanged: {manifest_path}"
                ],
                "files": [],
                "repair_checkpoint": repair_step_checkpoint(step),
            }
            patch_path.write_text(json.dumps(patch), encoding="utf-8")

            reused = retryable_current_exact_board_generation_record(
                out_dir,
                run_dir,
                step,
            )
            self.assertIsNotNone(reused)
            self.assertTrue(reused["executor_retry_reused"])
            report = apply_agent_file_edits(
                reused["output"],
                run_dir,
                out_dir,
                repair_checkpoint=repair_step_checkpoint(step),
                allow_board_integration=True,
            )
            materialized = json.loads(manifest_path.read_text(encoding="utf-8"))
            provenance = materialized["multilayer_harness"][
                "generation_provenance"
            ]

            self.assertEqual(report["status"], "pass")
            self.assertEqual(provenance["prompt_sha256"], prompt_sha)
            self.assertEqual(provenance["record_path"], str(record_path))
            self.assertEqual(
                provenance["record_sha256"],
                hashlib.sha256(record_path.read_bytes()).hexdigest(),
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "bind_exact_board_llm_generation_provenance"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_board_generation_reuses_current_testbench_module_alias_result(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            llm_dir.mkdir(parents=True)
            prompt_path = llm_dir / "exact_board_prompt.md"
            prompt_path.write_text("generate exact board shell\n", encoding="utf-8")
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text("{}\n", encoding="utf-8")
            output = {
                "schema_version": "spatialaccagent.exact_board_integration_generation.v1",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "summary": "bind the exact board testbench",
                "root_cause": "board shell is missing",
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": {
                            "board_simulation_preflight_plan": {
                                "top_module": "DynamicBoardTb",
                                "testbench": {"module": "DynamicBoardTb"},
                            }
                        },
                        "rationale": "bind generated testbench",
                    }
                ],
                "requested_validation": [],
                "blocked_reasons": [],
                "approval_required_for": [],
            }
            record_path = (
                llm_dir / "exact_board_integration_generation_agent_result.json"
            )
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "compact_retry_request_path": str(prompt_path),
                "compact_retry_prompt_hash": hashlib.sha256(
                    prompt_path.read_bytes()
                ).hexdigest(),
                "repair_execution_context": {
                    "repair_step_id": "repair_step.00"
                },
                "output": output,
                "raw_text": json.dumps(output, sort_keys=True),
            }
            record_path.write_text(json.dumps(record), encoding="utf-8")
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "agent_status": "ready_to_apply",
                        "agent_transaction_rejection": None,
                        "blockers": [
                            "agent board manifest top_module does not exactly match "
                            "testbench.top_module"
                        ],
                        "files": [],
                    }
                ),
                encoding="utf-8",
            )
            reused = retryable_current_exact_board_generation_record(
                out_dir,
                run_dir,
                {"id": "repair_step.00"},
            )
            self.assertIsNotNone(reused)
            self.assertEqual(
                reused["executor_retry_reason"],
                "canonical_testbench_module_alias",
            )

    def test_board_generation_reuses_hash_current_adaptive_observation_retry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            board_dir = run_dir / "generated" / "board_integration"
            llm_dir.mkdir(parents=True)
            board_dir.mkdir(parents=True)
            prompt_path = llm_dir / "exact_board_prompt.md"
            prompt_path.write_text("add a read-only board probe\n", encoding="utf-8")
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text("{}\n", encoding="utf-8")
            testbench_path = board_dir / "BoardTb.sv"
            testbench_path.write_text(
                "module BoardTb; wire observed; endmodule\n",
                encoding="utf-8",
            )
            output = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "file_edits": [
                    {
                        "path": str(testbench_path),
                        "operation": "replace_text",
                        "content": "",
                        "text_replacements": [
                            {
                                "old_text": "wire observed;",
                                "new_text": "wire observed; wire probe_only;",
                            }
                        ],
                        "rationale": "observe without changing DUT behavior",
                    }
                ],
                "blocked_reasons": [],
            }
            record_path = (
                llm_dir / "exact_board_integration_generation_agent_result.json"
            )
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "compact_retry_request_path": str(prompt_path),
                "compact_retry_prompt_hash": hashlib.sha256(
                    prompt_path.read_bytes()
                ).hexdigest(),
                "repair_execution_context": {
                    "repair_step_id": "repair_step.00"
                },
                "output": output,
                "raw_text": json.dumps(output, sort_keys=True),
            }
            record_path.write_text(json.dumps(record), encoding="utf-8")
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "exact_board_integration_harness"
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "agent_status": "ready_to_apply",
                        "files": [],
                        "retry_agent_without_real_tool": True,
                        "repair_checkpoint": repair_step_checkpoint(step),
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "failure_class": "adaptive_observation_decision_contract",
                            "real_tool_replay_required_before_retry": False,
                            "unchanged_pre_edit_files": [
                                {
                                    "path": str(testbench_path),
                                    "sha256": hashlib.sha256(
                                        testbench_path.read_bytes()
                                    ).hexdigest(),
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            reused = retryable_current_exact_board_generation_record(
                out_dir,
                run_dir,
                step,
            )

        self.assertIsNotNone(reused)
        assert reused is not None
        self.assertTrue(reused["executor_retry_reused"])
        self.assertEqual(
            reused["executor_retry_reason"],
            "adaptive_observation_contract",
        )

    def test_board_generation_does_not_reuse_stale_adaptive_observation_retry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            board_dir = run_dir / "generated" / "board_integration"
            llm_dir.mkdir(parents=True)
            board_dir.mkdir(parents=True)
            prompt_path = llm_dir / "exact_board_prompt.md"
            prompt_path.write_text("add a read-only board probe\n", encoding="utf-8")
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text("{}\n", encoding="utf-8")
            testbench_path = board_dir / "BoardTb.sv"
            testbench_path.write_text(
                "module BoardTb; wire observed; endmodule\n",
                encoding="utf-8",
            )
            output = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "adaptive_observation_decision": {
                    "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                    "mode": "deepen_simulation_observation",
                    "frontier_id": "connected_kernel_input_to_output",
                    "evidence_refs": [],
                    "field_observations": [],
                    "rationale": "observe the previous current boundary",
                },
                "file_edits": [
                    {
                        "path": str(testbench_path),
                        "operation": "replace_text",
                        "content": "",
                        "text_replacements": [
                            {
                                "old_text": "wire observed;",
                                "new_text": "wire observed; wire probe_only;",
                            }
                        ],
                        "rationale": "observe without changing DUT behavior",
                    }
                ],
                "blocked_reasons": [],
            }
            record_path = (
                llm_dir / "exact_board_integration_generation_agent_result.json"
            )
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "compact_retry_request_path": str(prompt_path),
                "compact_retry_prompt_hash": hashlib.sha256(
                    prompt_path.read_bytes()
                ).hexdigest(),
                "repair_execution_context": {
                    "repair_step_id": "repair_step.00"
                },
                "output": output,
                "raw_text": json.dumps(output, sort_keys=True),
            }
            record_path.write_text(json.dumps(record), encoding="utf-8")
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "exact_board_integration_harness"
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "agent_status": "ready_to_apply",
                        "files": [],
                        "retry_agent_without_real_tool": True,
                        "repair_checkpoint": repair_step_checkpoint(step),
                        "agent_transaction_rejection": {
                            "status": "ready_for_agent_retry",
                            "failure_class": "adaptive_observation_decision_contract",
                            "real_tool_replay_required_before_retry": False,
                            "unchanged_pre_edit_files": [
                                {
                                    "path": str(testbench_path),
                                    "sha256": hashlib.sha256(
                                        testbench_path.read_bytes()
                                    ).hexdigest(),
                                }
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )

            reused = retryable_current_exact_board_generation_record(
                out_dir,
                run_dir,
                step,
                adaptive_observation_decision_lock={
                    "schema_version": (
                        "spatialaccagent.adaptive_observation_decision_lock.v1"
                    ),
                    "status": "required",
                    "frontier_id": "kernel_output_stream_completion",
                    "allowed_modes": ["deepen_simulation_observation"],
                },
            )

        self.assertIsNone(reused)

    def test_retryable_transaction_is_not_superseded_by_older_semantic_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "repair_execution"
            out_dir.mkdir()
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {"repair_kind": "exact_board_integration_harness"},
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "blockers": ["frontier alias validation was corrected"],
                        "retry_agent_without_real_tool": True,
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            runner_path = out_dir / "case_board_vcs_functional.json"
            runner_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "run": {"status": "fail", "returncode": 86},
                    }
                ),
                encoding="utf-8",
            )
            os.utime(runner_path, ns=(1, 1))
            os.utime(patch_path, ns=(2, 2))

            feedback = current_agent_patch_application_feedback(
                out_dir,
                step,
                superseding_result_path=runner_path,
            )

        self.assertEqual(feedback["status"], "ready")
        self.assertEqual(
            feedback["summary"], "frontier alias validation was corrected"
        )

    def test_unrelated_noop_json_merge_remains_blocked(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"status": "ready"}), encoding="utf-8")
            output = self.implementation_output(target, "")
            output["file_edits"][0].update(
                {
                    "operation": "merge_json",
                    "expected_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                    "json_content": {"status": "ready"},
                }
            )

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertTrue(
                any(
                    "merge_json leaves the JSON object unchanged" in blocker
                    for blocker in report["blockers"]
                )
            )

    def test_noop_json_merge_is_omitted_when_paired_source_changes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            source = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "semantic_harness"
                / "ConnectedSingleLayerHarness.scala"
            )
            manifest.parent.mkdir(parents=True)
            source.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps({"single_layer_harness": {"status": "ready"}}) + "\n",
                encoding="utf-8",
            )
            source.write_text("class Before\n", encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "file_edits": [
                    {
                        "path": str(source),
                        "operation": "replace_text",
                        "expected_sha256": sha256_file(source),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "Before", "new_text": "After"}
                        ],
                    },
                    {
                        "path": str(manifest),
                        "operation": "merge_json",
                        "expected_sha256": sha256_file(manifest),
                        "content": "",
                        "json_content": {
                            "single_layer_harness": {"status": "ready"}
                        },
                    },
                ],
                "blocked_reasons": [],
                "approval_required_for": [],
            }

            report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(source.read_text(encoding="utf-8"), "class After\n")
            self.assertEqual(len(report["files"]), 1)
            self.assertTrue(
                any(
                    row.get("operation") == "omit_hash_bound_noop_json_merge"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_manifest_checkpoint_binding_repairs_framework_owned_hash(self) -> None:
        malformed = "a" * 68
        manifest = {
            "board_simulation_preflight_plan": {
                "testbench": {
                    "simulation_checkpoint_contract": {
                        "portable_state_capsule": {
                            "dut_state_root": "AdaptiveBoardTb.dut",
                            "framework_adapter_artifacts": [
                                {
                                    "kind": "vpi_source",
                                    "path": "copied-by-agent",
                                    "sha256": malformed,
                                    "framework_owned_read_only": True,
                                }
                            ],
                            "preserved": True,
                        }
                    }
                }
            }
        }

        report = rebind_manifest_checkpoint_framework_authority(manifest)
        portable = manifest["board_simulation_preflight_plan"]["testbench"][
            "simulation_checkpoint_contract"
        ]["portable_state_capsule"]

        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["changed"])
        self.assertEqual(
            [row["kind"] for row in portable["framework_adapter_artifacts"]],
            ["vpi_source", "vpi_table"],
        )
        self.assertTrue(
            all(len(row["sha256"]) == 64 for row in portable["framework_adapter_artifacts"])
        )
        self.assertEqual(portable["dut_state_root"], "AdaptiveBoardTb.dut")
        self.assertTrue(portable["preserved"])

    def test_checkpoint_framework_rebind_is_detected_before_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {
                                "simulation_checkpoint_contract": {
                                    "portable_state_capsule": {
                                        "dut_state_root": "AdaptiveBoardTb.dut",
                                        "framework_adapter_artifacts": [
                                            {
                                                "kind": "vpi_source",
                                                "path": "copied-by-agent",
                                                "sha256": "a" * 68,
                                                "framework_owned_read_only": True,
                                            }
                                        ],
                                    }
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            status = checkpoint_framework_authority_rebind_status(run_dir)

            self.assertEqual(status["status"], "ready")
            self.assertTrue(status["required"])
            self.assertTrue(
                status["policy"][
                    "framework_owned_identity_is_not_an_llm_repair"
                ]
            )
            persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                persisted["board_simulation_preflight_plan"]["testbench"][
                    "simulation_checkpoint_contract"
                ]["portable_state_capsule"]["framework_adapter_artifacts"][0][
                    "sha256"
                ],
                "a" * 68,
            )

    def test_checkpoint_manifest_agent_copy_is_rebound_to_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir / "generated" / "semantic_harness" / "BoardTb.sv"
            )
            manifest_path.parent.mkdir(parents=True)
            testbench_path.parent.mkdir(parents=True)
            authority_patch = {
                "board_simulation_preflight_plan": {
                    "testbench": {
                        "simulation_checkpoint_contract": {
                            "portable_state_capsule": {
                                "framework_adapter_artifacts": [
                                    {
                                        "kind": "vpi_source",
                                        "sha256": "a" * 64,
                                    }
                                ]
                            }
                        }
                    }
                }
            }
            agent_patch = copy.deepcopy(authority_patch)
            agent_patch["board_simulation_preflight_plan"]["testbench"][
                "simulation_checkpoint_contract"
            ]["portable_state_capsule"]["framework_adapter_artifacts"][0][
                "sha256"
            ] = "a" * 68
            manifest_path.write_text(
                json.dumps({"preserved": True}), encoding="utf-8"
            )
            testbench_path.write_text(
                "module BoardTb; wire old_hook; endmodule\n", encoding="utf-8"
            )
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "blocked_reasons": [],
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": agent_patch,
                    },
                    {
                        "path": str(testbench_path),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            testbench_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "old_hook", "new_text": "fixed_hook"}
                        ],
                    },
                ],
                "requested_validation": [],
            }
            required = {manifest_path.resolve(), testbench_path.resolve()}

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allowed_exact_files=required,
                required_exact_files=required,
                required_noop_json_merges={
                    manifest_path.resolve(): authority_patch
                },
            )
            materialized = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(report["status"], "pass", report["blockers"])
            self.assertEqual(
                materialized["board_simulation_preflight_plan"]["testbench"][
                    "simulation_checkpoint_contract"
                ],
                authority_patch["board_simulation_preflight_plan"]["testbench"][
                    "simulation_checkpoint_contract"
                ],
            )
            self.assertTrue(materialized["preserved"])
            self.assertIn(
                "fixed_hook", testbench_path.read_text(encoding="utf-8")
            )
            self.assertTrue(
                any(
                    row.get("operation")
                    == "bind_framework_owned_checkpoint_contract_authority"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_checkpoint_manifest_noop_is_acknowledged_only_with_material_pair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir / "generated" / "semantic_harness" / "BoardTb.sv"
            )
            manifest_path.parent.mkdir(parents=True)
            testbench_path.parent.mkdir(parents=True)
            checkpoint_patch = {
                "board_simulation_preflight_plan": {
                    "testbench": {
                        "simulation_checkpoint_contract": {
                            "schema_version": "checkpoint.v1",
                            "status": "ready",
                        }
                    }
                }
            }
            manifest_path.write_text(
                json.dumps({**checkpoint_patch, "preserved": True}),
                encoding="utf-8",
            )
            original_testbench = "module BoardTb; wire old_hook; endmodule\n"
            testbench_path.write_text(original_testbench, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": checkpoint_patch,
                    },
                    {
                        "path": str(testbench_path),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            testbench_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "old_hook", "new_text": "fixed_hook"}
                        ],
                    },
                ],
                "requested_validation": [],
            }
            required = {manifest_path.resolve(), testbench_path.resolve()}

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allowed_exact_files=required,
                required_exact_files=required,
                required_noop_json_merges={
                    manifest_path.resolve(): checkpoint_patch
                },
            )

            self.assertEqual(report["status"], "pass")
            self.assertIn("fixed_hook", testbench_path.read_text(encoding="utf-8"))
            self.assertTrue(json.loads(manifest_path.read_text())["preserved"])
            self.assertTrue(
                any(
                    row.get("operation")
                    == "acknowledge_authority_exact_checkpoint_contract"
                    for row in report["protocol_normalizations"]
                )
            )

    def test_checkpoint_manifest_noop_without_material_pair_remains_blocked(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            checkpoint_patch = {"checkpoint": {"status": "ready"}}
            original = json.dumps(checkpoint_patch)
            manifest_path.write_text(original, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": checkpoint_patch,
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allowed_exact_files={manifest_path.resolve()},
                required_exact_files={manifest_path.resolve()},
                required_noop_json_merges={
                    manifest_path.resolve(): checkpoint_patch
                },
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIn(
                "requires a materially changed paired atomic edit target",
                "\n".join(report["blockers"]),
            )
            self.assertEqual(manifest_path.read_text(encoding="utf-8"), original)

    def test_checkpoint_overlapping_text_transaction_retries_agent_without_tool(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir / "generated" / "semantic_harness" / "BoardTb.sv"
            )
            manifest_path.parent.mkdir(parents=True)
            testbench_path.parent.mkdir(parents=True)
            checkpoint_patch = {
                "board_simulation_preflight_plan": {
                    "testbench": {
                        "simulation_checkpoint_contract": {
                            "schema_version": "checkpoint.v1",
                            "status": "ready",
                        }
                    }
                }
            }
            manifest_path.write_text(
                json.dumps({**checkpoint_patch, "preserved": True}),
                encoding="utf-8",
            )
            original_testbench = "module BoardTb; abcdef; endmodule\n"
            testbench_path.write_text(original_testbench, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "blocked_reasons": [],
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": checkpoint_patch,
                    },
                    {
                        "path": str(testbench_path),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            testbench_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "abc", "new_text": "ABC"},
                            {"old_text": "cde", "new_text": "CDE"},
                        ],
                    },
                ],
                "requested_validation": [],
            }
            required = {manifest_path.resolve(), testbench_path.resolve()}

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allowed_exact_files=required,
                required_exact_files=required,
                required_noop_json_merges={
                    manifest_path.resolve(): checkpoint_patch
                },
            )

            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report["retry_agent_without_real_tool"])
            self.assertEqual(report["files"], [])
            self.assertEqual(
                report["agent_transaction_rejection"]["failure_class"],
                "checkpoint_atomic_replace_text_contract",
            )
            self.assertFalse(
                report["agent_transaction_rejection"][
                    "real_tool_replay_required_before_retry"
                ]
            )
            self.assertEqual(
                testbench_path.read_text(encoding="utf-8"), original_testbench
            )

            disposition = repair_loop_disposition(
                {
                    "status": "incomplete",
                    "errors": ["agent transaction was rejected"],
                    "step_results": [
                        {
                            "result": {
                                "status": "blocked",
                                "summary": "overlapping replace_text anchors",
                                "agent_patch_application": report["path"],
                            }
                        }
                    ],
                }
            )
            self.assertEqual(disposition["status"], "continue")
            self.assertTrue(disposition["retry_agent_without_real_tool"])
            self.assertEqual(
                disposition["retry_reason"], "agent_transaction_contract"
            )

    def test_plain_replace_text_anchor_miss_retries_agent_without_tool(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            target.parent.mkdir(parents=True)
            original = "module BoardTop; wire ready; endmodule\n"
            target.write_text(original, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "blocked_reasons": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            target.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {
                                "old_text": "wire stale;",
                                "new_text": "wire repaired;",
                            }
                        ],
                    }
                ],
                "requested_validation": [],
            }

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report["retry_agent_without_real_tool"])
            self.assertEqual(report["files"], [])
            self.assertEqual(
                report["agent_transaction_rejection"]["failure_class"],
                "atomic_replace_text_contract",
            )
            self.assertFalse(
                report["agent_transaction_rejection"][
                    "real_tool_replay_required_before_retry"
                ]
            )
            self.assertEqual(
                report["agent_transaction_rejection"]["rejected_file_edits"],
                [
                    {
                        "path": str(target),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            target.read_bytes()
                        ).hexdigest(),
                        "text_replacements": [
                            {
                                "old_text": "wire stale;",
                                "new_text": "wire repaired;",
                            }
                        ],
                    }
                ],
            )
            self.assertEqual(target.read_text(encoding="utf-8"), original)

            disposition = repair_loop_disposition(
                {
                    "status": "incomplete",
                    "errors": ["agent transaction was rejected"],
                    "step_results": [
                        {
                            "result": {
                                "status": "blocked",
                                "summary": "replace_text anchor did not match",
                                "agent_patch_application": report["path"],
                            }
                        }
                    ],
                }
            )
            self.assertEqual(disposition["status"], "continue")
            self.assertTrue(disposition["retry_agent_without_real_tool"])
            self.assertEqual(
                disposition["retry_reason"], "agent_transaction_contract"
            )

    def test_checkpoint_specialist_noop_reuses_only_hash_current_agent_record(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            llm_dir.mkdir(parents=True)
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir / "generated" / "board_integration" / "BoardTb.sv"
            )
            manifest_path.parent.mkdir(parents=True)
            testbench_path.parent.mkdir(parents=True)
            checkpoint_patch = {
                "board_simulation_preflight_plan": {
                    "testbench": {
                        "simulation_checkpoint_contract": {
                            "schema_version": "checkpoint.v1",
                            "status": "ready",
                        }
                    }
                }
            }
            manifest_path.write_text(
                json.dumps({**checkpoint_patch, "preserved": True}),
                encoding="utf-8",
            )
            testbench_path.write_text("module BoardTb; old_hook; endmodule\n")
            output = {
                "schema_version": "spatialaccagent.test.repair_execution.v1",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "summary": "repair checkpoint hook",
                "root_cause": "runtime trigger mismatch",
                "file_edits": [
                    {
                        "path": str(manifest_path),
                        "operation": "merge_json",
                        "expected_sha256": hashlib.sha256(
                            manifest_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "json_content": checkpoint_patch,
                        "rationale": "acknowledge the authority contract",
                    },
                    {
                        "path": str(testbench_path),
                        "operation": "replace_text",
                        "expected_sha256": hashlib.sha256(
                            testbench_path.read_bytes()
                        ).hexdigest(),
                        "content": "",
                        "text_replacements": [
                            {"old_text": "old_hook", "new_text": "fixed_hook"}
                        ],
                        "rationale": "repair the generated simulation hook",
                    },
                ],
                "requested_validation": [],
                "blocked_reasons": [],
                "approval_required_for": [],
            }
            prompt_path = llm_dir / "exact_board_prompt.md"
            prompt_path.write_text("checkpoint specialist prompt\n")
            prompt_sha = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
            record_path = (
                llm_dir / "exact_board_integration_generation_agent_result.json"
            )
            record = {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "request_path": str(prompt_path),
                "prompt_hash": prompt_sha,
                "output": output,
                "raw_text": json.dumps(output, sort_keys=True),
            }
            record_path.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "exact_board_integration_harness",
                    "violated_contract": "exact_board_real_vcs_and_analyzer_must_pass",
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "blockers": [
                            "file_edits[0] merge_json leaves the JSON object "
                            f"unchanged: {manifest_path.resolve()}",
                            "implementation patch is missing a required atomic edit "
                            f"target: {manifest_path.resolve()}",
                        ],
                        "files": [],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            required = {manifest_path.resolve(), testbench_path.resolve()}
            authority = {manifest_path.resolve(): checkpoint_patch}

            reused = retryable_current_checkpoint_specialist_record(
                out_dir,
                step,
                required_exact_files=required,
                required_noop_json_merges=authority,
            )

            self.assertIsNotNone(reused)
            self.assertEqual(
                reused["executor_retry_reason"],
                "required_checkpoint_manifest_noop_acknowledgement",
            )
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "blockers": [
                            "file_edits[0] merge_json leaves the JSON object "
                            f"unchanged: {manifest_path.resolve()}",
                        ],
                        "files": [],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            self.assertIsNotNone(
                retryable_current_checkpoint_specialist_record(
                    out_dir,
                    step,
                    required_exact_files=required,
                    required_noop_json_merges=authority,
                )
            )
            testbench_path.write_text("module BoardTb; drifted; endmodule\n")
            self.assertIsNone(
                retryable_current_checkpoint_specialist_record(
                    out_dir,
                    step,
                    required_exact_files=required,
                    required_noop_json_merges=authority,
                )
            )

    def test_checkpoint_gap_never_overrides_hardware_without_explicit_maintenance(self) -> None:
        gap = {
            "status": "ready_for_capability_repair",
            "runtime_execution_failure": {"status": "ready"},
        }
        self.assertFalse(
            checkpoint_specialist_route_required(
                gap,
                "vcs_runtime_semantic_stall",
            )
        )
        self.assertFalse(
            checkpoint_specialist_route_required(
                {
                    "status": "ready_for_capability_repair",
                    "runtime_execution_failure": {"status": "stale"},
                },
                "simulation_checkpoint_capability_missing_or_invalid",
            )
        )
        self.assertTrue(
            checkpoint_specialist_route_required(
                gap,
                "simulation_checkpoint_capability_missing_or_invalid",
                explicit_checkpoint_maintenance=True,
            )
        )
        self.assertFalse(
            checkpoint_specialist_route_required(
                {
                    "status": "ready",
                    "runtime_execution_failure": {"status": "ready"},
                },
                "vcs_runtime_semantic_stall",
                explicit_checkpoint_maintenance=True,
            )
        )

    def test_uncertified_checkpoint_request_falls_back_to_cold_repair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            request_path = run_dir / "verification" / "checkpoint_request.json"
            request_path.parent.mkdir(parents=True)
            request = {
                "status": "ready",
                "request_sha256": "a" * 64,
                "replay_decision": {"mode": "cold_capture"},
            }
            request_path.write_text(json.dumps(request), encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_debug_episode",
                return_value={"status": "active", "episode_id": "episode.1"},
            ), patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_request",
                return_value=request,
            ), patch(
                "accagent.framework.stage_repair_execute.persist_checkpoint_request",
                return_value=request_path,
            ):
                result = prepare_stage3_checkpoint_probe_environment(
                    run_dir,
                    label="repair_step_00",
                )

        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["checkpoint_enabled"])
        self.assertTrue(result["cold_fallback"])
        self.assertFalse(result["remote_tool_must_not_start"])
        self.assertNotIn("SPATIALACC_CHECKPOINT_REQUIRED", result["env"])
        self.assertNotIn("SPATIALACC_CHECKPOINT_REPLAY", result["env"])

    def test_pending_checkpoint_executor_retry_precedes_real_tool_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir / "generated" / "board_integration" / "BoardTb.sv"
            )
            manifest_path.parent.mkdir(parents=True)
            testbench_path.parent.mkdir(parents=True)
            manifest_path.write_text('{"status":"ready"}\n')
            testbench_path.write_text("module BoardTb; endmodule\n")
            manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            testbench_sha = hashlib.sha256(testbench_path.read_bytes()).hexdigest()
            package = {
                "status": "ready",
                "blockers": [],
                "capability_gap": {"status": "ready_for_capability_repair"},
                "checkpoint_authority": {"status": "ready"},
                "atomic_edit_contract": {
                    "allowed_and_required_paths": [
                        str(manifest_path),
                        str(testbench_path),
                    ],
                    "manifest": {
                        "path": str(manifest_path),
                        "expected_sha256": manifest_sha,
                    },
                    "testbench": {
                        "path": str(testbench_path),
                        "expected_sha256": testbench_sha,
                    },
                },
                "current_testbench_source": {
                    "path": str(testbench_path),
                    "sha256": testbench_sha,
                    "complete_current_source": True,
                },
            }
            package_path = out_dir / "checkpoint_hook_specialist_package.json"
            out_dir.mkdir(parents=True, exist_ok=True)
            package_path.write_text(json.dumps(package))
            authority = {manifest_path.resolve(): {"checkpoint": "authority"}}
            record = {"output": {"status": "ready_to_apply"}}

            with patch(
                "accagent.framework.stage_repair_execute."
                "checkpoint_specialist_required_noop_json_merges",
                return_value=authority,
            ), patch(
                "accagent.framework.stage_repair_execute."
                "retryable_current_checkpoint_specialist_record",
                return_value=record,
            ):
                pending = pending_checkpoint_specialist_executor_retry(
                    out_dir,
                    run_dir,
                    {"id": "repair_step.00"},
                )

            self.assertIsNotNone(pending)
            self.assertEqual(pending["status"], "ready")
            self.assertEqual(pending["llm_record"], record)
            testbench_path.write_text("module BoardTb; wire drifted; endmodule\n")
            self.assertIsNone(
                pending_checkpoint_specialist_executor_retry(
                    out_dir,
                    run_dir,
                    {"id": "repair_step.00"},
                )
            )

    def test_board_generation_reuses_hash_bound_patch_attestation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "dut_weight_binding_manifest.json"
            patch_path = root / "agent_patch_application.json"
            source_manifest_sha = "a" * 64
            prompt_sha = "b" * 64
            record_sha = "c" * 64
            record_path = root / "llm" / "exact_board_agent_result.json"
            patch_report = {
                "schema_version": "spatialaccagent.agent_patch_application.v1",
                "status": "pass",
                "blockers": [],
                "files": [
                    {
                        "path": str(manifest_path),
                        "after_sha256": source_manifest_sha,
                    }
                ],
                "protocol_normalizations": [
                    {
                        "operation": "bind_exact_board_llm_generation_provenance",
                        "prompt_sha256": prompt_sha,
                        "trusted_generation_record": str(record_path),
                        "trusted_generation_record_sha256": record_sha,
                    }
                ],
            }
            patch_path.write_text(
                json.dumps(patch_report, sort_keys=True), encoding="utf-8"
            )
            patch_sha = hashlib.sha256(patch_path.read_bytes()).hexdigest()
            harness = {
                "generation_provenance": {
                    "mode": "llm",
                    "agent_id": "exact_board_integration_generation_agent",
                    "model": "gpt-test-board",
                    "used_fallback": False,
                    "prompt_sha256": None,
                }
            }

            provenance = _attested_exact_board_generation_provenance(
                harness,
                {
                    "source_patch_application": str(patch_path),
                    "source_patch_application_sha256": patch_sha,
                    "source_agent_manifest": str(manifest_path),
                    "source_agent_manifest_sha256": source_manifest_sha,
                },
            )

            self.assertIsNotNone(provenance)
            self.assertEqual(provenance["prompt_sha256"], prompt_sha)
            self.assertEqual(provenance["record_sha256"], record_sha)
            self.assertEqual(provenance["attestation"], "agent_patch_application")

    def test_board_generation_recovers_immutable_loop_provenance(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            iteration_dir = out_dir / "loop" / "iteration_0001"
            llm_dir = out_dir / "llm"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            iteration_dir.mkdir(parents=True)
            llm_dir.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            source_record_path = llm_dir / "exact_board_agent_result.json"
            source_prompt_path = llm_dir / "exact_board_agent_prompt.md"
            archived_record_path = iteration_dir / "00_llm_record.json"
            archived_prompt_path = iteration_dir / "01_request_path.md"
            archived_patch_path = iteration_dir / "02_agent_patch_application.json"
            prompt_text = "immutable exact-board prompt\n"
            archived_prompt_path.write_text(prompt_text, encoding="utf-8")
            prompt_sha = hashlib.sha256(
                archived_prompt_path.read_bytes()
            ).hexdigest()
            output = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "ready_to_apply",
                "file_edits": [{"path": str(manifest_path)}],
                "blocked_reasons": [],
                "approval_required_for": [],
            }
            record = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "model": "gpt-test-board",
                "used_fallback": False,
                "error": None,
                "result_path": str(source_record_path),
                "compact_retry_request_path": str(source_prompt_path),
                "compact_retry_prompt_hash": prompt_sha,
                "output": output,
                "raw_text": json.dumps(output),
            }
            archived_record_path.write_text(
                json.dumps(record, sort_keys=True), encoding="utf-8"
            )
            record_sha = hashlib.sha256(
                archived_record_path.read_bytes()
            ).hexdigest()
            applied_manifest_sha = "d" * 64
            archived_patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                        "files": [
                            {
                                "path": str(manifest_path),
                                "after_sha256": applied_manifest_sha,
                            }
                        ],
                        "protocol_normalizations": [
                            {
                                "operation": (
                                    "bind_exact_board_llm_generation_provenance"
                                ),
                                "prompt_sha256": prompt_sha,
                                "trusted_generation_record": str(
                                    source_record_path
                                ),
                                "trusted_generation_record_sha256": record_sha,
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            patch_sha = hashlib.sha256(
                archived_patch_path.read_bytes()
            ).hexdigest()
            manifest = {
                "multilayer_harness": {
                    "generation_provenance": {
                        "mode": "llm",
                        "agent_id": "exact_board_integration_generation_agent",
                        "model": "gpt-test-board",
                        "used_fallback": False,
                        "prompt_sha256": prompt_sha,
                        "record_sha256": record_sha,
                    }
                }
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            iteration_record_path = iteration_dir / "iteration_record.json"
            iteration_record_path.write_text(
                json.dumps(
                    {
                        "iteration": 1,
                        "evidence_snapshots": [
                            {
                                "role": "llm_record",
                                "snapshot_path": str(archived_record_path),
                                "source_path": str(source_record_path),
                                "source_sha256": record_sha,
                            },
                            {
                                "role": "request_path",
                                "snapshot_path": str(archived_prompt_path),
                                "source_path": str(source_prompt_path),
                                "source_sha256": prompt_sha,
                            },
                            {
                                "role": "agent_patch_application",
                                "snapshot_path": str(archived_patch_path),
                                "source_path": str(
                                    out_dir / "agent_patch_application.json"
                                ),
                                "source_sha256": patch_sha,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            source = recover_archived_exact_board_source_provenance(
                manifest,
                manifest_path,
                out_dir,
            )
            preferred_source = prefer_archived_exact_board_source_provenance(
                manifest,
                manifest_path,
                out_dir,
                {
                    "source_patch_application": "rolling-materializer.json",
                    "source_agent_manifest_sha256": "e" * 64,
                },
            )
            provenance = _attested_exact_board_generation_provenance(
                manifest["multilayer_harness"],
                source,
            )
            recovery_status = checkpoint_framework_authority_rebind_status(
                run_dir
            )

            self.assertEqual(
                source["source_agent_manifest_sha256"], applied_manifest_sha
            )
            self.assertEqual(preferred_source, source)
            self.assertIsNotNone(provenance)
            self.assertEqual(
                provenance["record_path"], str(archived_record_path)
            )
            self.assertEqual(
                provenance["prompt_path"], str(archived_prompt_path)
            )
            self.assertEqual(
                provenance["attestation"], "archived_agent_patch_application"
            )
            self.assertTrue(recovery_status["required"])
            self.assertFalse(recovery_status["adapter_rebind_required"])
            self.assertTrue(
                recovery_status[
                    "archived_generation_provenance_rebind_required"
                ]
            )

            manifest["multilayer_harness"]["generation_provenance"] = provenance
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            settled_status = checkpoint_framework_authority_rebind_status(
                run_dir
            )
            self.assertFalse(settled_status["required"])
            self.assertFalse(
                settled_status[
                    "archived_generation_provenance_rebind_required"
                ]
            )

    def test_board_manifest_repair_preserves_attested_incomplete_lower_layers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            requirements = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "dut_weight_binding_requirements.json"
            )
            target.parent.mkdir(parents=True)
            requirements.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            requirements.write_text(
                json.dumps({"stage_requirements": [{"stage_id": "dynamic"}]}),
                encoding="utf-8",
            )
            blockers = ["board_preflight: generated board top is incomplete"]
            certified = {
                "status": "incomplete",
                "stage_harnesses": {"dynamic": {"top_module": "LeafTop"}},
                "single_layer_harness": {"top_module": "ConnectedTop"},
                "multilayer_harness": {"top_module": "OldBoardTop"},
                "materialization": {
                    "source": "agent_file_edits_plus_framework_hash_validation",
                    "requirements": str(requirements),
                    "requirements_sha256": hashlib.sha256(
                        requirements.read_bytes()
                    ).hexdigest(),
                    "verification_scope": "board_axi_ddr_closure",
                },
                "materialization_blockers": blockers,
            }
            target.write_text(json.dumps(certified), encoding="utf-8")
            (out_dir / "dut_weight_binding_materialization.json").write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                        "status": "incomplete",
                        "manifest": str(target),
                        "manifest_sha256": hashlib.sha256(
                            target.read_bytes()
                        ).hexdigest(),
                        "stage_harness_count": 1,
                        "single_layer_harness_materialized": True,
                        "blockers": blockers,
                    }
                ),
                encoding="utf-8",
            )
            agent_manifest = {
                "status": "ready",
                "stage_harnesses": {},
                "single_layer_harness": {"top_module": "WrongTop"},
                "multilayer_harness": {"top_module": "RepairedBoardTop"},
            }
            output = self.implementation_output(target, json.dumps(agent_manifest))
            output["file_edits"][0].update(
                {
                    "operation": "replace",
                    "expected_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            )

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
            )
            materialized = json.loads(target.read_text(encoding="utf-8"))

            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                materialized["stage_harnesses"], certified["stage_harnesses"]
            )
            self.assertEqual(
                materialized["single_layer_harness"],
                certified["single_layer_harness"],
            )
            self.assertEqual(
                materialized["multilayer_harness"]["top_module"],
                "RepairedBoardTop",
            )

    def test_runtime_frontier_guard_rejects_only_stale_compile_authority_merge(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            testbench = run_dir / "generated" / "board_integration" / "BoardTb.sv"
            manifest.parent.mkdir(parents=True)
            testbench.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "vcs_compile_plan": {"commands": ["vcs"]},
                            "testbench": {"path": str(testbench)},
                        }
                    }
                ),
                encoding="utf-8",
            )
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            before_manifest = manifest.read_text(encoding="utf-8")
            package = {
                "current_board_vcs_feedback": {
                    "runner_report": {
                        "sha256": "a" * 64,
                        "value": {
                            "input_fingerprint_sha256": "d" * 64,
                            "exact_board_preflight_passed": True,
                            "exact_board_preflight": {"status": "pass"},
                            "compile": {"status": "pass"},
                            "run": {
                                "status": "fail",
                                "returncode": SEMANTIC_STALL_EXIT_CODE,
                            },
                        },
                    },
                    "diagnosis": {
                        "sha256": "b" * 64,
                        "value": {
                            "failure_class": (
                                "board_output_lifecycle_frontier_violation"
                            ),
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": (
                                                "connected_kernel_input_to_output"
                                            )
                                        }
                                    },
                                },
                            },
                        },
                    },
                }
            }
            guard = current_board_runtime_frontier_static_repair_guard(package)
            stale_output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(manifest),
                        "operation": "merge_json",
                        "expected_sha256": sha256_file(manifest),
                        "content": "",
                        "json_content": {
                            "board_simulation_preflight_plan": {
                                "vcs_compile_plan": {
                                    "simulator_authority": "already-closed"
                                }
                            }
                        },
                    }
                ],
                "requested_validation": [],
            }

            blockers = stale_static_board_authority_repair_blockers(
                stale_output,
                run_dir,
                guard,
            )
            report = apply_agent_file_edits(
                stale_output,
                run_dir,
                out_dir,
                allow_board_integration=True,
                agent_contract_blockers=blockers,
                agent_contract_failure_class=(
                    "stale_static_board_authority_repair_after_runtime_frontier"
                ),
                agent_contract_retry_on_blocked=True,
            )
            testbench_output = {
                "status": "ready_to_apply",
                "file_edits": [
                    {
                        "path": str(testbench),
                        "operation": "replace_text",
                        "text_replacements": [
                            {
                                "old_text": "module BoardTb; endmodule\n",
                                "new_text": "module BoardTb; initial $display(\"probe\"); endmodule\n",
                            }
                        ],
                    }
                ],
            }
            manifest_unchanged = (
                manifest.read_text(encoding="utf-8") == before_manifest
            )

        self.assertEqual(guard["status"], "active")
        self.assertEqual(
            guard["frontier_id"], "connected_kernel_input_to_output"
        )
        self.assertEqual(len(blockers), 1)
        self.assertIn("manifest-only VCS compile-authority", blockers[0])
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["retry_agent_without_real_tool"])
        self.assertEqual(
            report["agent_transaction_rejection"]["failure_class"],
            "stale_static_board_authority_repair_after_runtime_frontier",
        )
        self.assertTrue(manifest_unchanged)
        self.assertEqual(
            stale_static_board_authority_repair_blockers(
                testbench_output,
                run_dir,
                guard,
            ),
            [],
        )

    def test_adaptive_observation_accepts_explicit_cctg_frontier_alias(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            testbench = board_dir / "BoardTb.sv"
            manifest.parent.mkdir(parents=True)
            board_dir.mkdir(parents=True)
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "a" * 64},
                    "diagnosis": {
                        "sha256": "b" * 64,
                        "value": {
                            "failure_class": (
                                "board_output_lifecycle_frontier_violation"
                            ),
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": (
                                                "cctg_boundary_invariant_failure"
                                            ),
                                            "failed_boundary_ids": [
                                                "connected_kernel_input_to_output"
                                            ],
                                            "prior_runtime_frontier": {
                                                "frontier_id": (
                                                    "connected_kernel_input_to_output"
                                                )
                                            },
                                        }
                                    },
                                },
                            }
                        },
                    },
                }
            }
            output = {
                "adaptive_observation_decision": {
                    "schema_version": (
                        "spatialaccagent.adaptive_observation_decision.v1"
                    ),
                    "mode": "deepen_simulation_observation",
                    "frontier_id": "connected_kernel_input_to_output",
                    "evidence_refs": [
                        "/current_board_vcs_feedback/diagnosis/value/failure_class"
                    ],
                    "field_observations": [
                        {
                            "evidence_pointer": (
                                "/current_board_vcs_feedback/diagnosis/value/"
                                "failure_class"
                            ),
                            "observed_value": (
                                "board_output_lifecycle_frontier_violation"
                            ),
                            "semantic_role": "error",
                            "interpretation": "the current board frontier is runtime-level",
                        }
                    ],
                    "probe_plan": {
                        "target_boundary": "connected_kernel_input_to_output",
                        "add_or_update_probe_ids": ["probe.frontier.alias.1"],
                        "retire_probe_ids": [],
                        "required_event_fields": ["probe_id"],
                        "event_match": {"status": "fail"},
                        "trigger_condition": "current frontier is observed",
                        "bounded_window": "one frontier event",
                    },
                    "rationale": "use the explicit failed CCTG boundary alias",
                },
                "file_edits": [
                    {
                        "path": str(testbench),
                        "operation": "replace_text",
                        "text_replacements": [
                            {
                                "old_text": "module BoardTb; endmodule\n",
                                "new_text": "module BoardTb; initial $display(\"probe\"); endmodule\n",
                            }
                        ],
                    }
                ],
            }

            result = validate_adaptive_observation_decision(
                output,
                package,
                run_dir,
            )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["frontier_id"], "cctg_boundary_invariant_failure")

    def test_current_observation_frontier_lock_rejects_historical_frontier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            testbench = board_dir / "BoardTb.sv"
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_class": "board_output_lifecycle_frontier_violation",
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "kernel_output_stream_completion"
                                        }
                                    },
                                }
                            },
                        },
                    },
                },
                "adaptive_observation_routing": {
                    "status": "unconstrained"
                },
                "adaptive_observation_decision_lock": {
                    "schema_version": "spatialaccagent.adaptive_observation_decision_lock.v1",
                    "status": "required",
                    "frontier_id": "kernel_output_stream_completion",
                    "allowed_modes": ["deepen_simulation_observation"],
                },
            }
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "connected_kernel_input_to_output",
                "evidence_refs": [
                    "/current_board_vcs_feedback/diagnosis/value/failure_class"
                ],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/failure_class",
                        "observed_value": "board_output_lifecycle_frontier_violation",
                        "semantic_role": "error",
                        "interpretation": "the current board run stopped before output completion",
                    }
                ],
                "probe_plan": {
                    "target_boundary": "current output boundary",
                    "add_or_update_probe_ids": ["probe.current.frontier"],
                    "retire_probe_ids": [],
                    "required_event_fields": ["boundary_trace"],
                    "event_match": {"event_kind": "boundary_trace"},
                    "trigger_condition": "the current run stops",
                    "bounded_window": "one terminal record",
                },
                "rationale": "the current output boundary needs one bounded observation",
            }

            result = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": decision,
                    "file_edits": [
                        {
                            "path": str(testbench),
                            "operation": "replace_text",
                            "text_replacements": [
                                {
                                    "old_text": "module BoardTb; endmodule\n",
                                    "new_text": (
                                        "module BoardTb; initial $display(\"probe\"); "
                                        "endmodule\n"
                                    ),
                                }
                            ],
                        }
                    ],
                },
                package,
                run_dir,
            )

        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            any(
                "must exactly copy the current decision lock" in blocker
                for blocker in result["blockers"]
            )
        )

    def test_adaptive_observation_direct_evidence_is_pointer_bound(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}\n", encoding="utf-8")
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                },
                            },
                            "runtime": {
                                "boundary": {
                                    "start": 0,
                                    "accepted_count": 16,
                                }
                            },
                        },
                    },
                }
            }
            output = {
                "adaptive_observation_decision": {
                    "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                    "mode": "direct_executed_contradiction",
                    "frontier_id": "frontier.current",
                    "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
                    "field_observations": [
                        {
                            "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/boundary/start",
                            "observed_value": 0,
                            "semantic_role": "control",
                            "interpretation": "the launch control is absent",
                        },
                        {
                            "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/boundary/accepted_count",
                            "observed_value": 16,
                            "semantic_role": "counter",
                            "interpretation": "all input transactions were accepted",
                        },
                    ],
                    "probe_plan": {
                        "target_boundary": "frontier.current",
                        "add_or_update_probe_ids": [],
                        "retire_probe_ids": [],
                        "required_event_fields": [],
                        "event_match": {},
                        "trigger_condition": "not required",
                        "bounded_window": "not required",
                    },
                    "rationale": "current executed fields expose the contradiction",
                },
                "file_edits": [],
            }

            result = validate_adaptive_observation_decision(
                output, package, run_dir
            )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["mode"], "direct_executed_contradiction")
        self.assertEqual(len(result["valid_field_observations"]), 2)

    def test_board_signal_analysis_requires_an_internal_boundary_fact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            },
                            "runtime": {
                                "input_count": 16,
                                "output_count": 0,
                                "boundaries": {
                                    "norm_to_attention": {"ready": False}
                                },
                            },
                        },
                    },
                }
            }
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "direct_executed_contradiction",
                "frontier_id": "frontier.current",
                "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/input_count",
                        "observed_value": 16,
                        "semantic_role": "control",
                        "interpretation": "all input records were received",
                    },
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                        "observed_value": 0,
                        "semantic_role": "counter",
                        "interpretation": "no final output record was received",
                    },
                ],
                "rationale": "locate the first stopped internal data boundary",
            }
            count_only = validate_adaptive_observation_decision(
                {"adaptive_observation_decision": decision, "file_edits": []},
                package,
                run_dir,
                require_signal_analysis=True,
            )
            decision["field_observations"].append(
                {
                    "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/boundaries/norm_to_attention/ready",
                    "observed_value": False,
                    "semantic_role": "handshake",
                    "interpretation": "the normalization output is waiting at the attention input",
                }
            )
            with_boundary = validate_adaptive_observation_decision(
                {"adaptive_observation_decision": decision, "file_edits": []},
                package,
                run_dir,
                require_signal_analysis=True,
            )

        self.assertEqual(count_only["status"], "blocked")
        self.assertTrue(
            any("internal data-boundary signal" in value for value in count_only["blockers"])
        )
        self.assertEqual(with_boundary["status"], "pass")
        self.assertEqual(
            len(with_boundary["internal_boundary_field_observations"]), 1
        )

    def test_compile_failure_observation_uses_non_runtime_frontier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {
                        "sha256": "b" * 64,
                        "value": {"compile": {"status": "fail", "returncode": 1}},
                    },
                    "diagnosis": {
                        "sha256": "a" * 64,
                        "value": {
                            "failure_class": "vcs_compile_failure",
                            "failure_evidence": {
                                "failure_class": "vcs_compile_failure",
                                "first_real_error": "Error-[ITSFM] Illegal `timescale for module",
                                "compile": {"status": "fail", "returncode": 1},
                                "sacg_cctg_causal_slice": {
                                    "value": {
                                        "failure_class": "vcs_compile_failure",
                                        "status": "not_applicable_before_runtime_execution",
                                    }
                                },
                            },
                        },
                    },
                }
            }
            output = {
                "adaptive_observation_decision": {
                    "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                    "mode": "direct_tool_failure",
                    "frontier_id": "vcs_compile_failure",
                    "evidence_refs": [
                        "/current_board_vcs_feedback/diagnosis/value/failure_evidence/first_real_error",
                        "/current_board_vcs_feedback/runner_report/value/compile/returncode",
                    ],
                    "field_observations": [
                        {
                            "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/failure_evidence/first_real_error",
                            "observed_value": "Error-[ITSFM] Illegal `timescale for module",
                            "semantic_role": "error",
                            "interpretation": "the compiler failed before runtime execution",
                        },
                        {
                            "evidence_pointer": "/current_board_vcs_feedback/runner_report/value/compile/returncode",
                            "observed_value": 1,
                            "semantic_role": "contract",
                            "interpretation": "runtime evidence is unavailable until compile provenance is collected",
                        },
                    ],
                    "rationale": "collect exact compile provenance before any source repair",
                },
                "file_edits": [],
            }
            result = validate_adaptive_observation_decision(output, package, run_dir)

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["frontier_id"], "vcs_compile_failure")

    def test_bound_probe_compile_fix_reuses_runtime_frontier_and_existing_counter(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench = board_dir / "BoardTb.sv"
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            old_bindings = (
                "  assign boundary_valid[0] = dut.core.missing_valid;\n"
                "  assign boundary_ready[0] = dut.core.missing_ready;\n"
                "  assign boundary_fire[0] = boundary_valid[0] && boundary_ready[0];\n"
                "  assign boundary_payload[0] = dut.core.missing_payload;\n"
            )
            new_bindings = (
                "  assign boundary_valid[0] = dut.core.io_in_valid;\n"
                "  assign boundary_ready[0] = dut.core.io_in_ready;\n"
                "  assign boundary_fire[0] = (dut.core.io_in_valid) && (dut.core.io_in_ready);\n"
                "  assign boundary_payload[0] = dut.core.io_in_bits_data;\n"
            )
            testbench.write_text(
                "module BoardTb;\n"
                "  wire [0:0] boundary_valid, boundary_ready, boundary_fire;\n"
                "  wire [31:0] boundary_payload [0:0];\n"
                "  longint unsigned boundary_count [0:0];\n"
                + old_bindings
                + "  always @(posedge clk) begin\n"
                "    integer boundary_index;\n"
                "    if (boundary_fire[boundary_index] === 1'b1) begin\n"
                "      boundary_count[boundary_index] <= boundary_count[boundary_index] + 1;\n"
                "    end\n"
                "  end\n"
                "endmodule\n",
                encoding="utf-8",
            )
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            package = {
                "generation_phase_contract": {
                    "status": "repair_existing_board_sources",
                    "current_vcs_feedback_ready": True,
                },
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": "a" * 64,
                        "value": {
                            "failure_class": "vcs_compile_failure",
                            "failure_evidence": {
                                "failure_class": "vcs_compile_failure",
                                "first_real_error": "Error-[XMRE] missing_payload",
                                "compile": {"status": "fail", "returncode": 1},
                                "simulation": {"status": "not_run"},
                            },
                        },
                    },
                },
                "adaptive_observation_routing": {
                    "schema_version": "spatialaccagent.adaptive_observation_routing.v1",
                    "status": "complete_boundary_coverage_required",
                    "incomplete_boundary_ids": ["edge.input.to.norm"],
                    "required_boundary_count": 1,
                    "observed_boundary_count": 0,
                    "boundary_observation_status": "incomplete",
                    "proven_contradiction": False,
                    "policy": {
                        "one_next_run_covers_all_incomplete_boundaries": True,
                        "required_fields": [
                            "valid",
                            "ready",
                            "fire",
                            "accepted_count",
                            "first_accepted_payload_digest",
                            "last_accepted_payload_digest",
                        ],
                        "single_point_observation_is_insufficient": True,
                    },
                },
                "adaptive_observation_state": {
                    "status": "fail",
                    "compiled_probe_sources_bound": True,
                    "board_source_edits": [
                        {
                            "path": str(testbench),
                            "after_sha256": sha256_file(testbench),
                        }
                    ],
                    "decision": {
                        "frontier_id": "connected_kernel_input_to_output"
                    },
                },
            }
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "connected_kernel_input_to_output",
                "evidence_refs": [
                    "/current_board_vcs_feedback/diagnosis/value/failure_evidence/first_real_error",
                    "/current_board_vcs_feedback/diagnosis/value/failure_evidence/compile/returncode",
                ],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/failure_evidence/first_real_error",
                        "observed_value": "Error-[XMRE] missing_payload",
                        "semantic_role": "error",
                        "interpretation": "the installed read-only probe has a missing name",
                    },
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/failure_evidence/compile/returncode",
                        "observed_value": 1,
                        "semantic_role": "counter",
                        "interpretation": "simulation did not start",
                    },
                ],
                "boundary_coverage_plan": {
                    "boundary_ids": ["edge.input.to.norm"],
                    "required_fields": [
                        "valid",
                        "ready",
                        "fire",
                        "accepted_count",
                        "first_accepted_payload_digest",
                        "last_accepted_payload_digest",
                    ],
                },
                "signal_binding_plan": [
                    {
                        "boundary_id": "edge.input.to.norm",
                        "valid_source": "dut.core.io_in_valid",
                        "ready_source": "dut.core.io_in_ready",
                        "fire_source": "(dut.core.io_in_valid) && (dut.core.io_in_ready)",
                        "accepted_count_source": "boundary_count[0]",
                        "payload_source": "dut.core.io_in_bits_data",
                    }
                ],
                "probe_plan": {
                    "target_boundary": "edge.input.to.norm",
                    "add_or_update_probe_ids": ["probe.edge.input.to.norm"],
                    "retire_probe_ids": [],
                    "required_event_fields": [
                        "valid",
                        "ready",
                        "fire",
                        "accepted_count",
                        "first_accepted_payload_digest",
                        "last_accepted_payload_digest",
                    ],
                    "event_match": {"probe_id": "probe.edge.input.to.norm"},
                    "trigger_condition": "the current input sequence completes",
                    "bounded_window": "first and last accepted record",
                },
                "rationale": "repair the installed read-only probe and rerun it",
            }
            output = {
                "adaptive_observation_decision": decision,
                "file_edits": [
                    {
                        "path": str(testbench),
                        "operation": "replace_text",
                        "text_replacements": [
                            {"old_text": old_bindings, "new_text": new_bindings}
                        ],
                    }
                ],
            }
            compact_package = compact_verification_capability_repair_package(
                package
            )
            accepted = validate_adaptive_observation_decision(
                output,
                compact_package,
                run_dir,
                require_signal_analysis=True,
            )
            unbound_package = copy.deepcopy(package)
            unbound_package["adaptive_observation_state"][
                "compiled_probe_sources_bound"
            ] = False
            compact_unbound_package = (
                compact_verification_capability_repair_package(unbound_package)
            )
            rejected = validate_adaptive_observation_decision(
                output,
                compact_unbound_package,
                run_dir,
                require_signal_analysis=True,
            )

        self.assertEqual(accepted["status"], "pass")
        self.assertTrue(accepted["bound_observation_compile_repair"])
        self.assertEqual(accepted["frontier_id"], "vcs_compile_failure")
        self.assertEqual(accepted["blockers"], [])
        self.assertIn("adaptive_observation_state", compact_package)
        self.assertEqual(rejected["status"], "blocked")
        self.assertFalse(rejected["bound_observation_compile_repair"])
        self.assertTrue(
            any("frontier_id does not match" in value for value in rejected["blockers"])
        )

    def test_fresh_exact_source_provenance_replay_is_no_edit_and_current_evidence_bound(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {
                        "sha256": "b" * 64,
                        "value": {
                            "simulation_termination_provenance": {
                                "causal_classification": (
                                    "external_or_unattributed_termination"
                                )
                            }
                        },
                    },
                    "diagnosis": {
                        "sha256": "a" * 64,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            }
                        },
                    },
                }
            }
            decision = {
                "schema_version": (
                    "spatialaccagent.adaptive_observation_decision.v1"
                ),
                "mode": "fresh_exact_source_provenance_replay",
                "frontier_id": "frontier.current",
                "evidence_refs": [
                    "/verification_capability_repair_package/"
                    "current_board_vcs_feedback/runner_report/value"
                ],
                "field_observations": [
                    {
                        "evidence_pointer": (
                            "/verification_capability_repair_package/"
                            "current_board_vcs_feedback/runner_report/value/"
                            "simulation_termination_provenance/causal_classification"
                        ),
                        "observed_value": "external_or_unattributed_termination",
                        "semantic_role": "error",
                        "interpretation": (
                            "the runner ended without a deterministic HDL event"
                        ),
                    }
                ],
                "rationale": (
                    "rerun the unchanged exact source once for fresh runner provenance"
                ),
            }
            output = {
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "status": "blocked",
                "adaptive_observation_decision": decision,
                "file_edits": [],
                "blocked_reasons": ["fresh runner evidence is required"],
            }

            validate_schema(output, BOARD_INTEGRATION_REPAIR_SCHEMA)
            invalid_mode = copy.deepcopy(output)
            invalid_mode["adaptive_observation_decision"]["mode"] = (
                "fresh_probe_replay"
            )
            with self.assertRaises(ValueError):
                validate_schema(invalid_mode, BOARD_INTEGRATION_REPAIR_SCHEMA)
            relative_pointer = copy.deepcopy(output)
            relative_pointer["adaptive_observation_decision"][
                "field_observations"
            ][0]["evidence_pointer"] = (
                "/runner_report/value/simulation_termination_provenance/"
                "causal_classification"
            )
            with self.assertRaises(ValueError):
                validate_schema(
                    relative_pointer, BOARD_INTEGRATION_REPAIR_SCHEMA
                )
            accepted = validate_adaptive_observation_decision(
                output,
                package,
                run_dir,
            )
            rejected = validate_adaptive_observation_decision(
                {**output, "file_edits": [{"path": "BoardTb.sv"}]},
                package,
                run_dir,
            )

        self.assertEqual(accepted["status"], "pass")
        self.assertEqual(
            accepted["mode"], "fresh_exact_source_provenance_replay"
        )
        self.assertEqual(len(accepted["valid_field_observations"]), 1)
        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(
            any(
                "must not include file_edits" in value
                for value in rejected["blockers"]
            )
        )

    def test_fresh_replay_ignores_only_redundant_invalid_observations(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {
                        "sha256": "b" * 64,
                        "value": {
                            "simulation_termination_provenance": {
                                "causal_classification": (
                                    "external_or_unattributed_termination"
                                )
                            }
                        },
                    },
                    "diagnosis": {
                        "sha256": "a" * 64,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            }
                        },
                    },
                }
            }
            valid_observation = {
                "evidence_pointer": (
                    "/current_board_vcs_feedback/runner_report/value/"
                    "simulation_termination_provenance/causal_classification"
                ),
                "observed_value": "external_or_unattributed_termination",
                "semantic_role": "error",
                "interpretation": "the current runner has no attributed HDL event",
            }
            redundant_observation = {
                "evidence_pointer": (
                    "/current_board_vcs_feedback/runner_report/value/"
                    "nonexistent_redundant_detail"
                ),
                "observed_value": "invented",
                "semantic_role": "contract",
                "interpretation": "redundant detail",
            }
            decision = {
                "schema_version": (
                    "spatialaccagent.adaptive_observation_decision.v1"
                ),
                "mode": "fresh_exact_source_provenance_replay",
                "frontier_id": "frontier.current",
                "evidence_refs": [
                    "/current_board_vcs_feedback/runner_report/value"
                ],
                "field_observations": [
                    valid_observation,
                    redundant_observation,
                ],
                "rationale": "replay unchanged exact sources for fresh provenance",
            }
            output = {
                "adaptive_observation_decision": decision,
                "file_edits": [],
            }

            accepted = validate_adaptive_observation_decision(
                output,
                package,
                run_dir,
            )
            rejected = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": {
                        **decision,
                        "field_observations": [redundant_observation],
                    },
                    "file_edits": [],
                },
                package,
                run_dir,
            )

        self.assertEqual(accepted["status"], "pass")
        self.assertEqual(accepted["valid_field_observations"], [valid_observation])
        self.assertEqual(
            accepted["decision"]["field_observations"],
            [valid_observation],
        )
        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(
            any(
                "requires an exact current error or contract observation" in value
                for value in rejected["blockers"]
            )
        )

    def test_adaptive_observation_missing_decision_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": "a" * 64,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            }
                        },
                    },
                }
            }

            result = validate_adaptive_observation_decision(
                {"file_edits": []}, package, run_dir
            )

        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            any("schema_version" in blocker for blocker in result["blockers"])
        )

    def test_auxiliary_observation_fields_do_not_block_a_source_repair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {"sha256": "a" * 64, "value": {}},
                },
                "adaptive_observation_state": {
                    "status": "pending_real_tool_evidence"
                },
            }
            result = validate_adaptive_observation_decision(
                {
                    "file_edits": [{"path": "generated/board_integration/BoardTb.sv"}],
                    "adaptive_observation_decision": {
                        "mode": "direct_tool_failure",
                        "field_observations": [{"evidence_pointer": "/wrong"}],
                        "probe_plan": {
                            "add_or_update_probe_ids": ["auxiliary.label"],
                            "required_event_fields": ["auxiliary.field"],
                        },
                    },
                },
                package,
                run_dir,
            )

        self.assertEqual(result["status"], "not_required")
        self.assertEqual(result["blockers"], [])

    def test_adaptive_observation_deepening_allows_only_simulation_sources(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            testbench = board_dir / "BoardTb.sv"
            wrapper = board_dir / "BoardAdapter.v"
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            wrapper.write_text("module BoardAdapter; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            },
                            "runtime": {"output_count": 0},
                        },
                    },
                }
            }
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "frontier.current",
                "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                        "observed_value": 0,
                        "semantic_role": "counter",
                        "interpretation": "the current output counter is insufficient to localize the producer",
                    }
                ],
                "probe_plan": {
                    "target_boundary": "frontier.current",
                    "add_or_update_probe_ids": ["probe.frontier.current.deep.1"],
                    "retire_probe_ids": [],
                    "required_event_fields": [
                        "adaptive_probe.valid",
                        "adaptive_probe.ready",
                        "adaptive_probe.payload_digest",
                    ],
                    "event_match": {
                        "event_kind": "stall_snapshot",
                        "adaptive_probe.probe_id": "probe.frontier.deep.1",
                    },
                    "trigger_condition": "output count remains zero",
                    "bounded_window": "first failing transaction and predecessor",
                },
                "rationale": "the next causal edge requires new observations",
            }
            rejected = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": decision,
                    "file_edits": [{"path": str(wrapper)}],
                },
                package,
                run_dir,
            )
            accepted = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": decision,
                    "file_edits": [{"path": str(testbench)}],
                },
                package,
                run_dir,
            )

        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(
            any("not a declared testbench" in value for value in rejected["blockers"])
        )
        self.assertEqual(accepted["status"], "pass")

    def test_adaptive_observation_incomplete_boundaries_require_one_full_plan(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            testbench = board_dir / "BoardTb.sv"
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                },
                                "pipeline_boundary_observation": {
                                    "status": "incomplete",
                                    "required_boundary_count": 2,
                                    "observed_boundary_count": 1,
                                    "incomplete_boundary_ids": [
                                        "edge.input.to.norm",
                                        "edge.norm.to.output",
                                    ],
                                },
                            },
                            "runtime": {"output_count": 0},
                        },
                    },
                }
            }
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "frontier.current",
                "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                        "observed_value": 0,
                        "semantic_role": "counter",
                        "interpretation": "the output count is still zero",
                    }
                ],
                "probe_plan": {
                    "target_boundary": "frontier.current",
                    "add_or_update_probe_ids": ["probe.all.incomplete.boundaries"],
                    "retire_probe_ids": [],
                    "required_event_fields": ["boundary_trace"],
                    "event_match": {"event_kind": "boundary_trace"},
                    "trigger_condition": "the current run stops before output",
                    "bounded_window": "first and last accepted record per boundary",
                },
                "rationale": "collect all missing current data-boundary facts in one run",
            }
            incomplete_plan = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": decision,
                    "file_edits": [{"path": str(testbench)}],
                },
                package,
                run_dir,
            )
            complete_decision = copy.deepcopy(decision)
            complete_decision["boundary_coverage_plan"] = {
                "boundary_ids": [
                    "edge.input.to.norm",
                    "edge.norm.to.output",
                ],
                "required_fields": [
                    "valid",
                    "ready",
                    "fire",
                    "accepted_count",
                    "first_accepted_payload_digest",
                    "last_accepted_payload_digest",
                ],
            }
            complete_decision["signal_binding_plan"] = [
                {
                    "boundary_id": "edge.input.to.norm",
                    "valid_source": "input_valid",
                    "ready_source": "input_ready",
                    "fire_source": "input_fire",
                    "accepted_count_source": "input_count",
                    "payload_source": "input_payload",
                },
                {
                    "boundary_id": "edge.norm.to.output",
                    "valid_source": "output_valid",
                    "ready_source": "output_ready",
                    "fire_source": "output_fire",
                    "accepted_count_source": "output_count",
                    "payload_source": "output_payload",
                },
            ]
            observation_source = (
                "module BoardTb;\n"
                "  wire input_valid, input_ready, input_fire;\n"
                "  wire [31:0] input_count, input_payload;\n"
                "  wire output_valid, output_ready, output_fire;\n"
                "  wire [31:0] output_count, output_payload;\n"
                "endmodule\n"
            )
            complete_plan = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": complete_decision,
                    "file_edits": [
                        {
                            "path": str(testbench),
                            "operation": "replace_text",
                            "text_replacements": [
                                {
                                    "old_text": "module BoardTb; endmodule\n",
                                    "new_text": observation_source,
                                }
                            ],
                        }
                    ],
                },
                package,
                run_dir,
            )
            placeholder_decision = copy.deepcopy(complete_decision)
            placeholder_decision["signal_binding_plan"][0]["valid_source"] = "null"
            placeholder_plan = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": placeholder_decision,
                    "file_edits": [
                        {
                            "path": str(testbench),
                            "operation": "replace_text",
                            "text_replacements": [
                                {
                                    "old_text": "module BoardTb; endmodule\n",
                                    "new_text": observation_source,
                                }
                            ],
                        }
                    ],
                },
                package,
                run_dir,
            )
            array_decision = copy.deepcopy(complete_decision)
            array_decision["signal_binding_plan"] = [
                {
                    "boundary_id": "edge.input.to.norm",
                    "valid_source": "boundary_valid[0] = input_valid",
                    "ready_source": "boundary_ready[0] = input_ready",
                    "fire_source": "boundary_fire[0]",
                    "accepted_count_source": "boundary_count[0]",
                    "payload_source": "boundary_payload[0] = input_payload",
                },
                {
                    "boundary_id": "edge.norm.to.output",
                    "valid_source": "boundary_valid[1] = output_valid",
                    "ready_source": "boundary_ready[1] = output_ready",
                    "fire_source": "boundary_fire[1]",
                    "accepted_count_source": "boundary_count[1]",
                    "payload_source": "boundary_payload[1] = output_payload",
                },
            ]
            array_observation_source = (
                "module BoardTb;\n"
                "  wire input_valid, input_ready;\n"
                "  wire output_valid, output_ready;\n"
                "  wire [31:0] input_payload, output_payload;\n"
                "  wire [1:0] boundary_valid, boundary_ready, boundary_fire;\n"
                "  wire [31:0] boundary_payload [0:1];\n"
                "  longint unsigned boundary_count [0:1];\n"
                "  assign boundary_valid[0] = input_valid;\n"
                "  assign boundary_ready[0] = input_ready;\n"
                "  assign boundary_payload[0] = input_payload;\n"
                "  assign boundary_valid[1] = output_valid;\n"
                "  assign boundary_ready[1] = output_ready;\n"
                "  assign boundary_payload[1] = output_payload;\n"
                "  assign boundary_fire = boundary_valid & boundary_ready;\n"
                "  task automatic emit_boundary(\n"
                "    input integer boundary_index,\n"
                "    input string boundary_id\n"
                "  );\n"
                "    begin\n"
                "      $display(\"%s %0d %0d\", boundary_id,\n"
                "        boundary_fire[boundary_index],\n"
                "        boundary_count[boundary_index]);\n"
                "    end\n"
                "  endtask\n"
                "  always @(posedge input_valid) begin\n"
                "    integer sample_index;\n"
                "    if (boundary_fire[sample_index] === 1'b1) begin\n"
                "      boundary_count[sample_index] <=\n"
                "        boundary_count[sample_index] + 1;\n"
                "    end\n"
                "    emit_boundary(0, \"edge.input.to.norm\");\n"
                "    emit_boundary(1, \"edge.norm.to.output\");\n"
                "  end\n"
                "endmodule\n"
            )
            array_plan = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": array_decision,
                    "file_edits": [
                        {
                            "path": str(testbench),
                            "operation": "replace_text",
                            "text_replacements": [
                                {
                                    "old_text": "module BoardTb; endmodule\n",
                                    "new_text": array_observation_source,
                                }
                            ],
                        }
                    ],
                },
                package,
                run_dir,
            )
            unguarded_array_source = array_observation_source.replace(
                "if (boundary_fire[sample_index] === 1'b1)",
                "if (1'b1)",
            )
            unguarded_array_plan = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": array_decision,
                    "file_edits": [
                        {
                            "path": str(testbench),
                            "operation": "replace_text",
                            "text_replacements": [
                                {
                                    "old_text": "module BoardTb; endmodule\n",
                                    "new_text": unguarded_array_source,
                                }
                            ],
                        }
                    ],
                },
                package,
                run_dir,
            )

        self.assertEqual(incomplete_plan["status"], "blocked")
        self.assertTrue(
            any(
                "boundary_coverage_plan" in blocker
                for blocker in incomplete_plan["blockers"]
            )
        )
        self.assertEqual(
            complete_plan["adaptive_observation_routing"]["status"],
            "complete_boundary_coverage_required",
        )
        self.assertEqual(complete_plan["status"], "pass")
        self.assertEqual(placeholder_plan["status"], "blocked")
        self.assertTrue(
            any("lacks a direct valid_source" in value for value in placeholder_plan["blockers"])
        )
        self.assertEqual(array_plan["status"], "pass")
        self.assertEqual(unguarded_array_plan["status"], "blocked")
        self.assertTrue(
            any(
                "must increment only when" in value
                for value in unguarded_array_plan["blockers"]
            )
        )

    def test_dynamic_boundary_loop_materializes_fixed_count_bindings(self) -> None:
        source = (
            "module BoardTb;\n"
            "  wire [1:0] boundary_fire;\n"
            "  longint unsigned boundary_count [0:1];\n"
            "  assign boundary_fire[0] = dut.a_valid && dut.a_ready;\n"
            "  assign boundary_fire[1] = dut.b_valid && dut.b_ready;\n"
            "  task automatic emit_boundary(input integer boundary_index);\n"
            "    begin\n"
            "      $display(\"%0d %0d\", boundary_fire[boundary_index],\n"
            "        boundary_count[boundary_index]);\n"
            "    end\n"
            "  endtask\n"
            "  always @(posedge clk) begin\n"
            "    integer boundary_sample_index;\n"
            "    for (boundary_sample_index = 0; boundary_sample_index < 2;\n"
            "         boundary_sample_index = boundary_sample_index + 1) begin\n"
            "      if (boundary_fire[boundary_sample_index] === 1'b1) begin\n"
            "        emit_boundary(boundary_sample_index);\n"
            "        boundary_count[boundary_sample_index] <=\n"
            "          boundary_count[boundary_sample_index] + 1;\n"
            "      end\n"
            "    end\n"
            "  end\n"
            "endmodule\n"
        )
        bindings = {
            "edge.a": {
                "fire_source": "boundary_fire[0]",
                "accepted_count_source": "boundary_count[0]",
            },
            "edge.b": {
                "fire_source": "boundary_fire[1]",
                "accepted_count_source": "boundary_count[1]",
            },
        }

        result = _loop_counter_observation_binding_check(
            bindings,
            set(bindings),
            [source],
        )

        self.assertEqual(result["blockers"], [])
        self.assertEqual(
            result["materialized"],
            {
                ("edge.a", "accepted_count_source"),
                ("edge.b", "accepted_count_source"),
            },
        )

    def test_adaptive_observation_complete_trace_requires_repair_or_blocker(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            testbench = board_dir / "BoardTb.sv"
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                },
                                "pipeline_boundary_observation": {
                                    "status": "complete",
                                    "required_boundary_count": 2,
                                    "observed_boundary_count": 2,
                                    "incomplete_boundary_ids": [],
                                    "missing_boundary_ids": [],
                                },
                                "board_to_lower_layer_contradiction_evidence": {
                                    "status": "proven"
                                },
                            },
                            "runtime": {"output_count": 0},
                        },
                    },
                }
            }
            result = validate_adaptive_observation_decision(
                {
                    "adaptive_observation_decision": {
                        "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                        "mode": "deepen_simulation_observation",
                        "frontier_id": "frontier.current",
                        "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
                        "field_observations": [
                            {
                                "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                                "observed_value": 0,
                                "semantic_role": "counter",
                                "interpretation": "the output count is still zero",
                            }
                        ],
                        "boundary_coverage_plan": {
                            "boundary_ids": ["edge.input.to.norm"],
                            "required_fields": ["valid"],
                        },
                        "probe_plan": {
                            "target_boundary": "frontier.current",
                            "add_or_update_probe_ids": ["probe.unneeded"],
                            "retire_probe_ids": [],
                            "required_event_fields": ["boundary_trace"],
                            "event_match": {"event_kind": "boundary_trace"},
                            "trigger_condition": "the current run stops before output",
                            "bounded_window": "one record",
                        },
                        "rationale": "request another observation",
                    },
                    "file_edits": [{"path": str(testbench)}],
                },
                package,
                run_dir,
            )

        self.assertEqual(
            result["adaptive_observation_routing"]["status"],
            "functional_repair_or_explicit_blocker_required",
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            any("smallest functional repair" in blocker for blocker in result["blockers"])
        )

    def test_adaptive_observation_existing_probe_replay_is_hash_bound(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "generated" / "board_integration"
            manifest = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            board_dir.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            testbench = board_dir / "BoardTb.sv"
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            manifest.write_text(
                json.dumps(
                    {
                        "board_simulation_preflight_plan": {
                            "testbench": {"path": str(testbench)}
                        }
                    }
                ),
                encoding="utf-8",
            )
            patch_record = run_dir / "repair_execution" / "agent_patch_application.json"
            patch_record.parent.mkdir(parents=True)
            patch_record.write_text("{}\n", encoding="utf-8")
            diagnosis_sha = "a" * 64
            package = {
                "current_board_vcs_feedback": {
                    "status": "ready",
                    "runner_report": {"sha256": "b" * 64},
                    "diagnosis": {
                        "sha256": diagnosis_sha,
                        "value": {
                            "failure_evidence": {
                                "sacg_cctg_causal_slice": {
                                    "sha256": "c" * 64,
                                    "value": {
                                        "earliest_unproven_frontier": {
                                            "frontier_id": "frontier.current"
                                        }
                                    },
                                }
                            },
                            "runtime": {"output_count": 0},
                        },
                    },
                }
            }
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "frontier.current",
                "evidence_refs": [f"diagnosis#sha256={diagnosis_sha}"],
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/output_count",
                        "observed_value": 0,
                        "semantic_role": "counter",
                        "interpretation": "the current output counter requires a fresh probe replay",
                    }
                ],
                "probe_plan": {
                    "target_boundary": "frontier.current",
                    "add_or_update_probe_ids": ["probe.frontier.current.deep.1"],
                    "retire_probe_ids": [],
                    "required_event_fields": [
                        "adaptive_probe.valid",
                        "adaptive_probe.ready",
                    ],
                    "event_match": {
                        "event_kind": "stall_snapshot",
                        "adaptive_probe.probe_id": "probe.frontier.deep.1",
                    },
                    "trigger_condition": "output count remains zero",
                    "bounded_window": "first failing transaction and predecessor",
                },
                "rationale": "the existing probe must be rerun with fresh board evidence",
            }
            state_path = run_dir / "verification" / "adaptive_observation" / "current.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.adaptive_observation_state.v1",
                        "status": "fail",
                        "decision_sha256": canonical_contract_sha256(decision),
                        "decision": decision,
                        "required_event_fields": decision["probe_plan"][
                            "required_event_fields"
                        ],
                        "event_match": decision["probe_plan"]["event_match"],
                        "probe_ids": decision["probe_plan"]["add_or_update_probe_ids"],
                        "compiled_probe_sources_bound": True,
                        "board_source_edits": [
                            {
                                "path": str(testbench),
                                "after_sha256": sha256_file(testbench),
                            }
                        ],
                        "source_patch_application": {
                            "path": str(patch_record),
                            "sha256": sha256_file(patch_record),
                        },
                    }
                ),
                encoding="utf-8",
            )

            accepted = validate_adaptive_observation_decision(
                {"adaptive_observation_decision": decision, "file_edits": []},
                package,
                run_dir,
                allow_existing_probe_replay=True,
            )
            replay = begin_existing_adaptive_observation_probe_replay(
                run_dir, accepted
            )
            self.assertEqual(accepted["status"], "pass")
            self.assertEqual(replay["status"], "pending_real_tool_evidence")
            self.assertEqual(replay["replay_count"], 1)

            testbench.write_text("module BoardTb; wire stale; endmodule\n", encoding="utf-8")
            rejected = existing_adaptive_observation_probe_replay_ready(
                run_dir, decision
            )

        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(
            any("board-source edit" in blocker for blocker in rejected["blockers"])
        )

    def test_agent_contract_rejection_retries_without_write_or_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            target.parent.mkdir(parents=True)
            target.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            output = self.implementation_output(
                target, "module BoardTop; wire changed; endmodule\n"
            )

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
                agent_contract_blockers=[
                    "adaptive observation decision is missing"
                ],
                agent_contract_failure_class=(
                    "adaptive_observation_decision_contract"
                ),
            )

            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report["retry_agent_without_real_tool"])
            self.assertEqual(
                report["agent_transaction_rejection"]["failure_class"],
                "adaptive_observation_decision_contract",
            )
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "module BoardTop; endmodule\n",
            )

    def test_blocked_agent_contract_rejection_retries_without_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            output = {
                "status": "blocked",
                "file_edits": [],
                "blocked_reasons": ["need a direct observation"],
                "approval_required_for": [],
            }

            report = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allow_board_integration=True,
                agent_contract_blockers=[
                    "adaptive observation decision mode is invalid"
                ],
                agent_contract_failure_class=(
                    "adaptive_observation_decision_contract"
                ),
                agent_contract_retry_on_blocked=True,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report["retry_agent_without_real_tool"])
            self.assertEqual(
                report["agent_transaction_rejection"]["failure_class"],
                "adaptive_observation_decision_contract",
            )

    def test_adaptive_probe_request_requires_fresh_bound_real_tool_event(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            testbench = (
                run_dir / "generated" / "board_integration" / "BoardTb.sv"
            )
            testbench.parent.mkdir(parents=True)
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            testbench_sha = hashlib.sha256(testbench.read_bytes()).hexdigest()
            patch_path = run_dir / "repair_execution" / "agent_patch_application.json"
            patch_path.parent.mkdir(parents=True)
            patch_application = {
                "status": "pass",
                "path": str(patch_path),
                "files": [
                    {
                        "path": str(testbench),
                        "before_sha256": "d" * 64,
                        "after_sha256": testbench_sha,
                    }
                ],
            }
            patch_path.write_text(
                json.dumps(patch_application), encoding="utf-8"
            )
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "frontier.current",
                "evidence_refs": ["diagnosis#sha256=" + "a" * 64],
                "field_observations": [],
                "probe_plan": {
                    "target_boundary": "frontier.current",
                    "add_or_update_probe_ids": ["probe.frontier.deep.1"],
                    "retire_probe_ids": [],
                    "required_event_fields": [
                        "adaptive_probe.valid",
                        "adaptive_probe.ready",
                        "adaptive_probe.payload_digest",
                    ],
                    "event_match": {
                        "event_kind": "stall_snapshot",
                        "adaptive_probe.probe_id": "probe.frontier.deep.1",
                    },
                    "trigger_condition": "output remains absent",
                    "bounded_window": "one failing transaction",
                },
                "rationale": "collect the next causal edge",
            }
            validation = {
                "status": "pass",
                "mode": "deepen_simulation_observation",
                "frontier_id": "frontier.current",
                "decision_sha256": hashlib.sha256(
                    json.dumps(decision, sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "decision": decision,
            }
            pending = persist_adaptive_observation_request(
                run_dir, validation, patch_application
            )
            progress_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "reports"
                / "progress_event_log.jsonl"
            )
            progress_path.parent.mkdir(parents=True)
            progress_path.write_text(
                json.dumps(
                    {
                        "event_kind": "stall_snapshot",
                        "adaptive_probe": {
                            "probe_id": "wrong.probe",
                            "valid": 1,
                            "ready": 0,
                            "payload_digest": "wrong-payload",
                        },
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "event_kind": "stall_snapshot",
                        "adaptive_probe": {
                            "probe_id": "probe.frontier.deep.1",
                            "valid": 1,
                            "ready": 0,
                            "payload_digest": "01234567",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            executed_manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_executed_manifest.json"
            )
            source_identity_sha256 = "b" * 64
            source_closure_sha256 = "c" * 64
            vcs_compile_plan_sha256 = "f" * 64
            executed_manifest_path.write_text(
                json.dumps(
                    {
                        "source_files": [
                            {
                                "source_id": "generated-board-source:testbench",
                                "sha256": testbench_sha,
                            }
                        ],
                        "source_identity_sha256": source_identity_sha256,
                        "source_closure_sha256": source_closure_sha256,
                        "vcs_compile_plan_sha256": vcs_compile_plan_sha256,
                        "execution_evidence": {
                            "source_identity_sha256": source_identity_sha256,
                            "source_closure_sha256": source_closure_sha256,
                            "vcs_compile_plan_sha256": vcs_compile_plan_sha256,
                        },
                    }
                ),
                encoding="utf-8",
            )
            feedback = {
                "status": "ready",
                "runner_report": {
                    "path": "runner.json",
                    "sha256": "e" * 64,
                    "value": {
                        "source_identity_bound": True,
                        "executed_manifest": str(executed_manifest_path),
                        "vcs_compile_plan_sha256": vcs_compile_plan_sha256,
                    },
                },
            }

            result = materialize_adaptive_observation_evidence(
                run_dir, feedback
            )

        self.assertEqual(pending["status"], "pending_real_tool_evidence")
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["compiled_probe_sources_bound"])
        self.assertEqual(
            result["matched_event_fields"]["adaptive_probe.payload_digest"],
            "01234567",
        )

    def test_failed_adaptive_observation_recheck_is_hash_bound(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            board_dir = run_dir / "verification" / "board_simulation"
            reports_dir = board_dir / "reports"
            generated_dir = run_dir / "generated" / "board_integration"
            semantic_dir = run_dir / "verification" / "semantic_testbench"
            repair_dir = run_dir / "repair_execution"
            reports_dir.mkdir(parents=True)
            generated_dir.mkdir(parents=True)
            semantic_dir.mkdir(parents=True)
            repair_dir.mkdir(parents=True)

            testbench = generated_dir / "BoardTb.sv"
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            semantic = semantic_dir / "semantic.json"
            semantic.write_text(
                json.dumps(
                    {
                        "single_layer": {
                            "pipeline_overlap_contract": {
                                "boundary_contracts": [
                                    {
                                        "boundary_id": "edge.input.to.output",
                                        "src_stage": "input",
                                        "dst_stage": "output",
                                        "kind": "stream",
                                        "flow_control": "ready_valid",
                                        "beats_per_token": 1,
                                    }
                                ],
                                "required_boundaries": ["edge.input.to.output"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            trace = board_dir / "boundary_trace.jsonl"
            record = {
                "event_kind": "boundary_trace",
                "probe_id": "probe.current",
                "boundary_id": "edge.input.to.output",
                "valid": 1,
                "ready": 1,
                "fire": True,
                "accepted_count": 1,
                "first_accepted_payload_digest": "first",
                "last_accepted_payload_digest": "last",
            }
            trace.write_text(json.dumps(record) + "\n", encoding="utf-8")
            simulation_log = reports_dir / "simulation.log"
            simulation_log.write_text("\n", encoding="utf-8")
            from scripts.verification.case_board_vcs_functional import (
                summarize_boundary_trace_observations,
            )

            testbench_row = {
                "path": str(testbench),
                "sha256": sha256_file(testbench),
                "source_id": "generated-board-source:testbench",
            }
            semantic_ref = {"path": str(semantic), "sha256": sha256_file(semantic)}
            summary = summarize_boundary_trace_observations(
                trace, semantic_ref, testbench_row, simulation_log
            )
            summary_path = board_dir / "pipeline_boundary_observation_summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            manifest = board_dir / "board_simulation_executed_manifest.json"
            source_identity = "a" * 64
            source_closure = "b" * 64
            compile_plan = "c" * 64
            compile_set = "d" * 64
            fingerprint = "e" * 64
            remote_workdir = "/remote/current-job"
            manifest.write_text(
                json.dumps(
                    {
                        "validation_mode": "compute_slot_axi",
                        "boundary_trace_file": "reports/boundary_trace.jsonl",
                        "semantic_testbench_manifest": semantic_ref,
                        "testbench": testbench_row,
                        "source_identity_sha256": source_identity,
                        "source_closure_sha256": source_closure,
                        "vcs_compile_plan_sha256": compile_plan,
                        "source_files": [testbench_row],
                        "execution_evidence": {
                            "status": "fail",
                            "job_id": remote_workdir,
                            "source_identity_sha256": source_identity,
                            "source_closure_sha256": source_closure,
                            "vcs_compile_plan_sha256": compile_plan,
                            "compile_source_set_sha256": compile_set,
                            "pipeline_boundary_observation": {
                                "summary": {
                                    "path": str(summary_path),
                                    "sha256": sha256_file(summary_path),
                                }
                            },
                            "simulation": {
                                "log": {
                                    "path": str(simulation_log),
                                    "sha256": sha256_file(simulation_log),
                                },
                                "termination_provenance": {
                                    "exact_source_replay_fingerprint_sha256": fingerprint
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            def feedback_with_runner(plan: str = compile_plan) -> dict[str, object]:
                runner_path = repair_dir / "runner.json"
                runner = {
                    "source_identity_bound": True,
                    "executed_manifest": str(manifest),
                    "vcs_compile_plan_sha256": plan,
                    "input_fingerprint_sha256": fingerprint,
                    "remote_workdir": remote_workdir,
                    "simulation_execution_identity": {
                        "compiled_model": {
                            "source_closure_sha256": source_closure,
                            "vcs_compile_plan_sha256": plan,
                            "compile_source_set_sha256": compile_set,
                            "source_rows": [{"sha256": sha256_file(testbench)}],
                        }
                    },
                }
                runner_path.write_text(json.dumps(runner), encoding="utf-8")
                return {
                    "status": "ready",
                    "runner_report": {
                        "path": str(runner_path),
                        "sha256": sha256_file(runner_path),
                        "value": runner,
                    },
                }

            patch = repair_dir / "agent_patch_application.json"
            patch.write_text("{}\n", encoding="utf-8")
            decision = {
                "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                "mode": "deepen_simulation_observation",
                "frontier_id": "frontier.current",
                "probe_plan": {
                    "event_match": {
                        "event_kind": "boundary_trace",
                        "probe_id": "probe.current",
                    },
                    "required_event_fields": ["valid", "ready"],
                },
            }

            def write_failed_state() -> None:
                state_path = run_dir / "verification" / "adaptive_observation" / "current.json"
                state_path.parent.mkdir(parents=True, exist_ok=True)
                state_path.write_text(
                    json.dumps(
                        {
                            "schema_version": "spatialaccagent.adaptive_observation_state.v1",
                            "status": "fail",
                            "decision_sha256": canonical_contract_sha256(decision),
                            "decision": decision,
                            "required_event_fields": ["valid", "ready"],
                            "event_match": decision["probe_plan"]["event_match"],
                            "board_source_edits": [
                                {
                                    "path": str(testbench),
                                    "after_sha256": sha256_file(testbench),
                                }
                            ],
                            "source_patch_application": {
                                "path": str(patch),
                                "sha256": sha256_file(patch),
                            },
                            "runner_report": {
                                "path": str(repair_dir / "old_runner.json"),
                                "sha256": "f" * 64,
                            },
                            "created_at_unix_sec": 0,
                            "created_at_unix_ns": 0,
                            "pre_request_progress_logs": [],
                        }
                    ),
                    encoding="utf-8",
                )

            write_failed_state()
            accepted = materialize_adaptive_observation_evidence(
                run_dir, feedback_with_runner()
            )
            self.assertEqual(accepted["status"], "pass")
            self.assertTrue(accepted["rechecked_failed_state"])

            trace.write_text(json.dumps({**record, "accepted_count": 2}) + "\n", encoding="utf-8")
            write_failed_state()
            stale_trace = materialize_adaptive_observation_evidence(
                run_dir, feedback_with_runner()
            )
            self.assertEqual(stale_trace["status"], "fail")
            self.assertTrue(
                any(
                    "boundary trace" in blocker
                    for blocker in stale_trace["failed_state_recheck"]["blockers"]
                )
            )

            trace.write_text(json.dumps(record) + "\n", encoding="utf-8")
            write_failed_state()
            mismatched_runner = materialize_adaptive_observation_evidence(
                run_dir, feedback_with_runner("9" * 64)
            )
            self.assertEqual(mismatched_runner["status"], "fail")
            self.assertTrue(
                any(
                    "vcs_compile_plan_sha256" in blocker
                    for blocker in mismatched_runner["failed_state_recheck"]["blockers"]
                )
            )

            write_failed_state()
            testbench.write_text("module BoardTb; wire changed; endmodule\n", encoding="utf-8")
            changed_source = materialize_adaptive_observation_evidence(
                run_dir, feedback_with_runner()
            )
            self.assertEqual(changed_source["status"], "fail")
            self.assertTrue(
                any(
                    "testbench source" in blocker
                    for blocker in changed_source["failed_state_recheck"]["blockers"]
                )
            )

    def test_adaptive_observation_aggregates_current_boundary_records(self) -> None:
        def run_case(records: list[dict[str, object]]) -> dict[str, object]:
            with TemporaryDirectory() as temp_dir:
                run_dir = Path(temp_dir) / "run"
                testbench = (
                    run_dir / "generated" / "board_integration" / "BoardTb.sv"
                )
                testbench.parent.mkdir(parents=True)
                testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
                testbench_sha = sha256_file(testbench)
                patch_path = run_dir / "repair_execution" / "agent_patch_application.json"
                patch_path.parent.mkdir(parents=True)
                patch_path.write_text("{}\n", encoding="utf-8")
                boundary_ids = [
                    "boundary.edge_data_a_to_b",
                    "edge.data.c.to.d",
                ]
                decision = {
                    "schema_version": "spatialaccagent.adaptive_observation_decision.v1",
                    "mode": "deepen_simulation_observation",
                    "frontier_id": "frontier.current",
                    "boundary_coverage_plan": {
                        "boundary_ids": boundary_ids,
                        "required_fields": [
                            "valid",
                            "ready",
                            "fire",
                            "accepted_count",
                            "first_accepted_payload_digest",
                            "last_accepted_payload_digest",
                        ],
                    },
                    "probe_plan": {
                        "target_boundary": "frontier.current",
                        "add_or_update_probe_ids": ["probe.multi.1"],
                        "retire_probe_ids": [],
                        "required_event_fields": [
                            "schema_version",
                            "evidence_kind",
                            "cycle",
                            "boundary_id",
                            "tx_id",
                            "tile_id",
                            "logical_index",
                            "observed_value",
                            "expected_value",
                            "contract",
                            "status",
                        ],
                        "event_match": {"probe_id": "probe.multi.1"},
                        "trigger_condition": "the current boundary trace is emitted",
                        "bounded_window": "current boundary records",
                    },
                    "evidence_refs": [],
                    "field_observations": [],
                    "rationale": "aggregate the current boundary records",
                }
                validation = {
                    "status": "pass",
                    "mode": decision["mode"],
                    "frontier_id": decision["frontier_id"],
                    "decision_sha256": canonical_contract_sha256(decision),
                    "decision": decision,
                }
                patch_application = {
                    "status": "pass",
                    "path": str(patch_path),
                    "files": [
                        {
                            "path": str(testbench),
                            "before_sha256": "d" * 64,
                            "after_sha256": testbench_sha,
                        }
                    ],
                }
                persist_adaptive_observation_request(
                    run_dir, validation, patch_application
                )
                trace = (
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "boundary_trace.jsonl"
                )
                trace.parent.mkdir(parents=True)
                trace.write_text(
                    "".join(json.dumps(record) + "\n" for record in records),
                    encoding="utf-8",
                )
                manifest = (
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "board_simulation_executed_manifest.json"
                )
                manifest.parent.mkdir(parents=True, exist_ok=True)
                manifest.write_text(
                    json.dumps(
                        {
                            "source_files": [
                                {
                                    "source_id": "generated-board-source:testbench",
                                    "sha256": testbench_sha,
                                }
                            ],
                            "source_identity_sha256": "b" * 64,
                            "source_closure_sha256": "c" * 64,
                            "vcs_compile_plan_sha256": "f" * 64,
                            "execution_evidence": {
                                "source_identity_sha256": "b" * 64,
                                "source_closure_sha256": "c" * 64,
                                "vcs_compile_plan_sha256": "f" * 64,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                feedback = {
                    "status": "ready",
                    "runner_report": {
                        "path": "runner.json",
                        "sha256": "e" * 64,
                        "value": {
                            "source_identity_bound": True,
                            "executed_manifest": str(manifest),
                            "vcs_compile_plan_sha256": "f" * 64,
                        },
                    },
                }
                return materialize_adaptive_observation_evidence(run_dir, feedback)

        def event(boundary_id: str, cycle: int, observed: dict[str, object]) -> dict[str, object]:
            return {
                "schema_version": "spatialaccagent.boundary_trace.v1",
                "evidence_kind": "boundary_trace",
                "cycle": cycle,
                "boundary_id": boundary_id,
                "tx_id": cycle,
                "tile_id": -1,
                "logical_index": cycle,
                "observed_value": {"probe_id": "probe.multi.1", **observed},
                "expected_value": {},
                "contract": "valid_ready_order_preserved",
                "status": "diagnostic_seed",
            }

        common = {
            "valid": 1,
            "ready": 1,
            "fire": True,
            "accepted_count": 4,
        }
        complete = run_case(
            [
                event("edge.data.a.to.b", 1, common),
                event(
                    "boundary.edge_data_a_to_b",
                    2,
                    {
                        "first_accepted_payload_digest": "first-a",
                        "last_accepted_payload_digest": "last-a",
                    },
                ),
                event(
                    "edge.data.c.to.d",
                    3,
                    {
                        **common,
                        "first_accepted_payload_digest": "first-c",
                        "last_accepted_payload_digest": "last-c",
                    },
                ),
            ]
        )
        incomplete = run_case(
            [
                event("edge.data.a.to.b", 1, common),
                event(
                    "edge.data.c.to.d",
                    2,
                    {
                        **common,
                        "first_accepted_payload_digest": "first-c",
                        "last_accepted_payload_digest": "last-c",
                    },
                ),
            ]
        )

        self.assertEqual(complete["status"], "pass")
        self.assertEqual(complete["aggregation_mode"], "multi_event_boundary_records")
        self.assertEqual(complete["matched_event_count"], 3)
        self.assertEqual(
            complete["matched_event_fields_by_boundary"]["boundary.edge_data_a_to_b"][
                "last_accepted_payload_digest"
            ],
            "last-a",
        )
        self.assertEqual(incomplete["status"], "fail")
        self.assertTrue(
            any("missing required fields by boundary" in blocker for blocker in incomplete["blockers"])
        )

    def test_board_repair_prompt_stays_on_the_real_tool_loop(self) -> None:
        prompt_rules = board_integration_prompt_rules("repair")
        rules = "\n".join(prompt_rules).lower()

        self.assertLessEqual(len(prompt_rules), 11)
        self.assertIn("real vcs/analyzer failure", rules)
        self.assertIn("sacg/cctg", rules)
        self.assertIn("smallest evidence-supported file_edits", rules)
        self.assertIn("implement the probes in the editable generated testbench in this same response", rules)
        self.assertIn("executor does not generate probes from probe_plan", rules)
        self.assertIn("not read-only testbench observation edits", rules)
        self.assertIn("exact discovered compute-slot abi", rules)
        self.assertIn("complete axi/ddr", rules)
        self.assertIn("one certified connected transformer-block kernel", rules)
        self.assertIn("elastic ready/valid token pipeline", rules)
        self.assertIn("two atomic weight banks", rules)
        self.assertIn("activation ping-pong", rules)
        self.assertIn("full_model_pipeline_liveness", rules)
        self.assertIn("current-contract-derived completion of every target layer", rules)
        self.assertIn("never hard-code a model family or layer count", rules)
        self.assertIn("passed lower-layer certificates closed", rules)
        self.assertIn("replace_text", rules)
        self.assertIn("merge_json", rules)
        self.assertIn("adaptive_observation_decision", rules)
        self.assertIn("fresh_exact_source_provenance_replay", rules)
        self.assertIn(
            "current_fresh_exact_source_provenance_replay.status=ready",
            rules,
        )
        self.assertIn("completed agent experiment", rules)
        self.assertIn("do not request the same unchanged replay again", rules)
        self.assertIn("never convert a simulator crash", rules)
        self.assertIn("file_edits=[]", rules)
        self.assertIn("added read-only observations alone", rules)
        self.assertIn("cold exact-board vcs/axi/ddr", rules)
        self.assertNotIn("exact json pointer", rules)
        self.assertIn("causal_prediction", rules)
        self.assertIn("at least two current scalar signal facts", rules)
        self.assertIn("checkpoint_impact", rules)
        self.assertIn("framework-owned optional acceleration", rules)
        self.assertIn("never a functional gate", rules)
        self.assertNotIn("expanded_source_authority", rules)

    def test_board_bootstrap_prompt_excludes_historical_repair_protocol(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("bootstrap")).lower()

        self.assertIn("before any current vcs evidence exists", rules)
        self.assertIn("exact unique replace_text anchors", rules)
        self.assertIn("two atomic weight banks", rules)
        self.assertIn("compute_slot_axi", rules)
        self.assertNotIn("adaptive_observation_decision", rules)
        self.assertNotIn("checkpoint replay is candidate", rules)

    def test_board_bootstrap_compaction_drops_stale_repair_feedback(self) -> None:
        compact = compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                "generation_phase_contract": {
                    "status": "generation_required_before_probe"
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "exact_board_repair_attempt_history": {"status": "ready"},
                "adaptive_observation_state": {"status": "pass"},
                "current_patch_application_feedback": {"status": "ready"},
                "repair_source_bundle": {
                    "schema_version": "spatialaccagent.repair_source_bundle.v1",
                    "documents": [],
                    "document_count": 0,
                    "document_chars": 0,
                    "editable_contract": {},
                },
                "exact_board_integration_repair_context": {
                    "schema_version": (
                        "spatialaccagent.exact_board_integration_repair_context.v1"
                    ),
                    "status": "ready",
                    "adaptive_design_inputs": {},
                },
            }
        )

        self.assertNotIn("current_board_vcs_feedback", compact)
        self.assertNotIn("exact_board_repair_attempt_history", compact)
        self.assertNotIn("adaptive_observation_state", compact)
        self.assertNotIn("current_patch_application_feedback", compact)

    def test_board_preflight_compaction_keeps_only_current_boundary(self) -> None:
        compact = compact_verification_capability_repair_package(
            {
                "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                "generation_mode": "preflight_repair",
                "generation_phase_contract": {
                    "status": "repair_deterministic_preflight"
                },
                "current_board_preflight_feedback": {
                    "status": "ready",
                    "blockers": ["current manifest source row is incomplete"],
                },
                "current_board_vcs_feedback": {"status": "ready"},
                "exact_board_repair_attempt_history": {"status": "ready"},
                "adaptive_observation_state": {"status": "pass"},
                "capability_probe": {"status": "not_run"},
                "capability_reports": [{"path": "/stale-report"}],
                "relevant_repair_experience": {"selected_count": 1},
                "relevant_project_knowledge": {"selected_count": 1},
                "repair_source_bundle": {
                    "schema_version": "spatialaccagent.repair_source_bundle.v1",
                    "documents": [],
                    "document_count": 0,
                    "document_chars": 0,
                    "editable_contract": {},
                },
                "exact_board_integration_repair_context": {
                    "schema_version": (
                        "spatialaccagent.exact_board_integration_repair_context.v1"
                    ),
                    "status": "ready",
                    "adaptive_design_inputs": {},
                },
            }
        )

        self.assertEqual(
            compact["generation_phase_contract"]["status"],
            "repair_deterministic_preflight",
        )
        self.assertEqual(
            compact["current_board_preflight_feedback"]["blockers"],
            ["current manifest source row is incomplete"],
        )
        for key in (
            "generation_mode",
            "current_board_vcs_feedback",
            "exact_board_repair_attempt_history",
            "adaptive_observation_state",
            "capability_probe",
            "capability_reports",
            "relevant_repair_experience",
            "relevant_project_knowledge",
        ):
            self.assertNotIn(key, compact)

    def test_board_preflight_prompt_excludes_post_vcs_debug_protocol(self) -> None:
        rules = "\n".join(board_integration_prompt_rules("preflight_repair")).lower()

        self.assertIn("deterministic exact-board preflight repair", rules)
        self.assertIn("complete editable board sources", rules)
        self.assertNotIn("adaptive_observation_decision", rules)
        self.assertNotIn("checkpoint replay is candidate", rules)

    def test_framework_canonicalizes_mechanical_board_manifest_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            board_dir = run_dir / "generated" / "board_integration"
            board_dir.mkdir(parents=True)
            (run_dir / "input").mkdir(parents=True)
            catalog_dir = run_dir / "verification" / "model_weights"
            catalog_dir.mkdir(parents=True)
            memory_dir = run_dir / "generated" / "chisel" / "memory"
            memory_dir.mkdir(parents=True)
            identity_dir = run_dir / "verification" / "board_interface"
            identity_dir.mkdir(parents=True)

            adapter = board_dir / "adapter.sv"
            testbench = board_dir / "tb.sv"
            monitor = board_dir / "monitor.sv"
            adapter.write_text("module BoardAdapter; endmodule\n", encoding="utf-8")
            testbench.write_text("module BoardTb; endmodule\n", encoding="utf-8")
            monitor.write_text("module BoardMonitor; endmodule\n", encoding="utf-8")
            (run_dir / "input" / "model_config.json").write_text(
                json.dumps({"num_layers": 2}), encoding="utf-8"
            )
            tensor_hashes = ["1" * 64, "2" * 64]
            (catalog_dir / "transformer_block_weight_catalog.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "target_layer_count": 2,
                        "tensors": [
                            {"source_slice_sha256": value}
                            for value in tensor_hashes
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (memory_dir / "memory_layout.json").write_text(
                json.dumps({"layout": "current"}), encoding="utf-8"
            )
            (identity_dir / "board_source_identity.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "selected_simulation_source_closure_sha256": "a" * 64,
                        "compute_slot_abi_sha256": "b" * 64,
                        "compute_slot_abi": {"slot_module": "BoardAdapter"},
                        "timing_contract_sha256": "c" * 64,
                        "axi_interfaces_sha256": "d" * 64,
                    }
                ),
                encoding="utf-8",
            )

            manifest = {
                "board_consumed_tensor_hashes": {
                    "kind": "complete_transformer_block_tensor_hash_binding"
                },
                "board_integration_contract": {
                    "scheduler": {
                        "status": "ready",
                        "layer_count": 2,
                        "target_layer_count": 2,
                    },
                    "double_weight_buffer": {
                        "status": "ready",
                        "bank_count": 2,
                        "atomic_switch_after_prefetch_complete": True,
                    },
                    "activation_ping_pong": {
                        "status": "ready",
                        "bank_count": 2,
                        "committed_activation_output_required_before_bank_ownership_change": True,
                    },
                    "background_prefetch": {
                        "status": "ready",
                        "overlaps_current_layer_compute": True,
                        "prefetch_scope": "next_layer_weights",
                    },
                    "final_writeback": {
                        "status": "ready",
                        "only_final_layer": True,
                        "starts_after_final_layer_completion": True,
                    },
                    "intra_layer_spatial_pipeline": {
                        "status": "ready",
                        "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                        "different_tokens_overlap_across_required_dataflow": True,
                        "heterogeneous_stage_latency_supported": True,
                        "stage_turnover_gaps_are_diagnostic": True,
                        "serial_leaf_execution": False,
                        "evidence_refs": ["generated-board-source:tb"],
                    },
                    "runtime_constants": {
                        "enabled": True,
                        "all_target_layers": True,
                        "required_before_every_kernel_start": True,
                        "evidence_refs": ["generated-board-source:adapter"],
                    },
                },
                "multilayer_harness": {
                    "top_module": "BoardAdapter",
                    "instance_path": "dut",
                    "source_files": [
                        {
                            "path": str(adapter),
                            "source_id": "generated-board-source:adapter",
                            "role": "adapter_alias",
                        },
                        {
                            "path": str(testbench),
                            "source_id": "generated-board-source:tb",
                            "role": "testbench",
                        },
                        {
                            "path": str(monitor),
                            "source_id": "generated-board-source:monitor",
                            "role": "axi_protocol_monitor",
                        },
                        {
                            "path": str(root / "certified.sv"),
                            "source_id": "certified_kernel.0",
                            "role": "generated_kernel",
                        },
                    ],
                },
                "board_simulation_preflight_plan": {
                    "top_module": "BoardTb",
                    "execution_outputs": {
                        "progress_event_log": {
                            "path": "reports/progress.jsonl",
                            "schema_version": "spatialaccagent.board_progress_event.v1",
                        }
                    },
                    "testbench": {
                        "source": {
                            "path": str(testbench),
                            "source_id": "generated-board-source:tb",
                        },
                        "debug_observability_contract": {},
                    },
                    "protocol_monitor_contract": {
                        "monitors": [
                            {
                                "source_id": "generated-board-source:monitor",
                                "bound_instance_path": "tb.monitor",
                                "source_files": [
                                    {
                                        "path": str(monitor),
                                        "source_id": "generated-board-source:monitor",
                                        "role": "axi_protocol_monitor",
                                    }
                                ],
                            }
                        ]
                    },
                    "generated_evidence_records": [
                        {
                            "source_id": "generated-board-source:tb",
                            "source_sha256": "stale",
                        }
                    ],
                },
            }

            canonical = canonicalize_exact_board_manifest_declarations(
                manifest,
                run_dir,
                root / "repair_execution",
            )

            self.assertEqual(canonical["board_consumed_tensor_hashes"], tensor_hashes)
            self.assertTrue(canonical["all_target_layers"])
            self.assertEqual(canonical["bound_layer_count"], 2)
            integration = canonical["board_integration_contract"]
            self.assertTrue(integration["scheduler"]["enabled"])
            self.assertTrue(integration["double_weight_buffer"]["atomic_layer_switch"])
            self.assertTrue(integration["activation_ping_pong"]["inter_layer_chaining"])
            self.assertTrue(integration["background_prefetch"]["enabled"])
            self.assertTrue(integration["final_writeback"]["only_after_last_layer"])
            self.assertTrue(integration["intra_layer_spatial_pipeline"]["preserved"])
            self.assertTrue(integration["runtime_constants"]["complete_before_kernel_start"])
            self.assertNotEqual(
                integration["intra_layer_spatial_pipeline"]["evidence_refs"][0],
                "generated-board-source:tb",
            )
            self.assertNotEqual(
                integration["runtime_constants"]["evidence_refs"][0],
                "generated-board-source:adapter",
            )
            self.assertEqual(
                [row["role"] for row in canonical["multilayer_harness"]["source_files"]],
                ["compute_slot_adapter"],
            )
            plan = canonical["board_simulation_preflight_plan"]
            self.assertEqual(
                plan["protocol_monitor_contract"]["monitors"][0]["source_files"][0]["role"],
                "protocol_monitor",
            )
            self.assertEqual(
                plan["protocol_monitor_contract"]["monitors"][0]["bound_instance_path"],
                "dut",
            )
            self.assertEqual(
                plan["testbench"]["debug_observability_contract"]["progress_event_log"],
                plan["execution_outputs"]["progress_event_log"],
            )
            self.assertEqual(
                plan["generated_evidence_records"][0]["source_sha256"],
                sha256_file(testbench),
            )
            evidence_ids = {
                str(row.get("evidence_id") or "")
                for row in plan["generated_evidence_records"]
                if isinstance(row, dict) and str(row.get("evidence_id") or "")
            }
            self.assertIn(
                integration["intra_layer_spatial_pipeline"]["evidence_refs"][0],
                evidence_ids,
            )
            self.assertIn(
                integration["runtime_constants"]["evidence_refs"][0],
                evidence_ids,
            )

    def test_exact_board_compile_input_excludes_headers_and_runtime_auxiliaries(self) -> None:
        self.assertTrue(
            _exact_board_simulator_compile_input(
                {"path": "/sample/design.sv", "file_type": "SystemVerilog"}
            )
        )
        self.assertFalse(
            _exact_board_simulator_compile_input(
                {"path": "/sample/defs.svh", "file_type": "SystemVerilog Header"}
            )
        )
        self.assertFalse(
            _exact_board_simulator_compile_input(
                {"path": "/sample/runtime.elf", "file_type": "ELF"}
            )
        )

    def test_exact_board_task_distinguishes_first_create_from_repair(self) -> None:
        create_task = exact_board_agent_task("create").lower()
        repair_task = exact_board_agent_task("repair").lower()

        self.assertIn("first-create generation phase", create_task)
        self.assertIn("repair phase", repair_task)
        self.assertNotIn("first-create", repair_task)
        self.assertIn("vcs runner report and analyzer diagnosis", repair_task)
        self.assertIn("resolve every mutually consistent blocker", repair_task)
        self.assertIn("do not serialize independent manifest corrections", repair_task)
        self.assertIn("earliest causal vcs/analyzer failure", repair_task)
        self.assertIn("independently proven simulation-only observability", repair_task)
        self.assertIn("never weaken its schema or analyzer", repair_task)

    def test_exact_board_validation_selects_real_vcs_and_analyzer_not_static_gate(self) -> None:
        case_adapter = {
            "tools": {
                "static_gate": {
                    "name": "arbitrary_static_gate",
                    "capabilities": ["gate_checker_only", "multilayer_pipeline_static_check"],
                },
                "real_board_sim": {
                    "name": "arbitrary_real_board_sim",
                    "capabilities": [
                        "real_functional_sim",
                        "board_wrapper_functional_sim",
                        "exact_sample_board_wrapper_simulation",
                        "all_target_layers",
                    ],
                },
                "evidence_reader": {
                    "name": "arbitrary_evidence_reader",
                    "capabilities": [
                        "vcs_evidence_analyzer",
                        "semantic_comparison_evidence",
                    ],
                },
            }
        }
        step = {
            "action": {
                "repair_kind": "exact_board_integration_harness",
                "repair_gate": "arbitrary_static_gate",
            }
        }

        selected_role, selected_spec = select_capability_tool(step, case_adapter)
        vcs_role, vcs_spec, analyzer_role, analyzer_spec = (
            select_exact_board_validation_tools(case_adapter)
        )

        self.assertEqual(selected_role, "real_board_sim")
        self.assertIs(selected_spec, vcs_spec)
        self.assertEqual(vcs_role, "real_board_sim")
        self.assertEqual(analyzer_role, "evidence_reader")
        self.assertEqual(analyzer_spec["name"], "arbitrary_evidence_reader")

    def test_exact_board_validation_runs_vcs_then_analyzer_and_uses_diagnosis_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            out_dir = run_dir / "repair_execution"
            runner_path = run_dir / "reports" / "runner.json"
            diagnosis_path = run_dir / "reports" / "diagnosis.json"
            out_dir.mkdir(parents=True)
            vcs_spec = {
                "name": "arbitrary_real_board_sim",
                "produces": [str(runner_path)],
            }
            analyzer_spec = {
                "name": "arbitrary_evidence_reader",
                "consumes": [str(runner_path)],
                "produces": [str(diagnosis_path)],
            }
            case_adapter = {
                "case_id": "arbitrary_case",
                "diagnosis": {"path": str(diagnosis_path)},
            }
            calls = []

            def probe(**kwargs):
                calls.append(
                    (
                        kwargs["spec_role"],
                        dict(kwargs.get("extra_env") or {}),
                    )
                )
                if kwargs["spec_role"] == "real_board_sim":
                    runner_path.parent.mkdir(parents=True, exist_ok=True)
                    runner_path.write_text(
                        json.dumps(
                            {
                                "schema_version": "arbitrary.board_vcs_functional_run.v1",
                                "status": "pass",
                                "phase": "remote_vcs",
                                "compile": {"status": "pass"},
                                "run": {"status": "pass"},
                            }
                        ),
                        encoding="utf-8",
                    )
                else:
                    diagnosis_path.write_text(
                        json.dumps(
                            {
                                "schema_version": "arbitrary.vcs_diagnosis.v1",
                                "status": "pass",
                                "diagnosis_status": "ready",
                                "summary": "passed",
                                "sources": [str(runner_path)],
                                "repair_handoff": {
                                    "agent_should_apply_code_changes": False,
                                    "repair_scope": "none",
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                return {"status": "pass", "produced_reports": []}

            with patch(
                "accagent.framework.stage_repair_execute.run_capability_probe",
                side_effect=probe,
            ):
                result = run_exact_board_validation_chain(
                    case_adapter=case_adapter,
                    vcs_role="real_board_sim",
                    vcs_spec=vcs_spec,
                    analyzer_role="evidence_reader",
                    analyzer_spec=analyzer_spec,
                    run_dir=run_dir,
                    step={"id": "repair_step.00"},
                    out_dir=out_dir,
                    timeout_sec=0,
                    label="post_patch",
                    checkpoint_env={
                        "SPATIALACC_FRESH_EXACT_BOARD_REPLAY_GENERATION_SHA256": (
                            "d" * 64
                        )
                    },
                )

        self.assertEqual(
            [role for role, _ in calls],
            ["real_board_sim", "evidence_reader"],
        )
        self.assertEqual(
            calls[0][1][
                "SPATIALACC_FRESH_EXACT_BOARD_REPLAY_GENERATION_SHA256"
            ],
            "d" * 64,
        )
        self.assertNotIn(
            "SPATIALACC_FRESH_EXACT_BOARD_REPLAY_GENERATION_SHA256",
            calls[1][1],
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["current_board_vcs_feedback"]["status"], "ready")

    def test_exact_board_preflight_feedback_requires_the_current_manifest_hash(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            preflight_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_preflight_materialization.json"
            )
            manifest_path.parent.mkdir(parents=True)
            preflight_path.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            manifest_path.write_text('{"status":"incomplete"}\n', encoding="utf-8")
            preflight_path.write_text(
                '{"status":"incomplete","blockers":["compile plan missing"]}\n',
                encoding="utf-8",
            )
            materialization_path = out_dir / "dut_weight_binding_materialization.json"
            materialization = {
                "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                "status": "incomplete",
                "manifest": str(manifest_path),
                "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "blockers": ["board_preflight: compile plan missing"],
            }
            materialization_path.write_text(
                json.dumps(materialization), encoding="utf-8"
            )

            current = exact_board_preflight_feedback(run_dir, out_dir)
            self.assertEqual(current["status"], "ready")
            self.assertEqual(current["blockers"], materialization["blockers"])

            manifest_path.write_text('{"status":"changed"}\n', encoding="utf-8")
            stale = exact_board_preflight_feedback(run_dir, out_dir)
            self.assertEqual(stale["status"], "incomplete")

    def test_exact_board_preflight_feedback_routes_validation_boundary_migration_before_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest_path = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            manifest_path.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.dut_weight_binding_manifest.v1",
                        "board_simulation_preflight_plan": {
                            "validation_mode": "vendor_physical_memory_model"
                        },
                    }
                ),
                encoding="utf-8",
            )

            feedback = exact_board_preflight_feedback(run_dir, out_dir)

            self.assertEqual(feedback["status"], "ready")
            self.assertEqual(
                feedback["evidence_kind"],
                "deterministic_board_validation_boundary_migration",
            )
            self.assertEqual(feedback["required_validation_mode"], "compute_slot_axi")
            self.assertTrue(feedback["repair_handoff"]["skip_prior_boundary_vcs"])
            self.assertEqual(
                feedback["manifest"]["sha256"],
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )

    def test_current_hash_bound_preflight_pass_routes_vcs_past_historical_manifest_block(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            binding_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            board_manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            identity_path = (
                run_dir / "verification" / "board_interface" / "board_source_identity.json"
            )
            preflight_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_preflight_materialization.json"
            )
            for path in (
                binding_path.parent,
                board_manifest_path.parent,
                identity_path.parent,
                out_dir,
            ):
                path.mkdir(parents=True, exist_ok=True)
            binding_path.write_text('{"status":"pass"}\n', encoding="utf-8")
            board_manifest_path.write_text(
                '{"status":"ready","validation_mode":"compute_slot_axi"}\n',
                encoding="utf-8",
            )
            identity_path.write_text('{"status":"pass"}\n', encoding="utf-8")
            binding_sha256 = sha256_file(binding_path)
            board_manifest_sha256 = sha256_file(board_manifest_path)
            materialization = {
                "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                "status": "pass",
                "manifest": str(binding_path),
                "manifest_sha256": binding_sha256,
                "board_integration_harness_materialized": True,
                "board_simulation_preflight_materialized": True,
                "board_simulation_preflight_manifest": str(board_manifest_path),
                "board_simulation_preflight_manifest_sha256": board_manifest_sha256,
            }
            (out_dir / "dut_weight_binding_materialization.json").write_text(
                json.dumps(materialization), encoding="utf-8"
            )
            preflight_path.write_text(
                json.dumps(
                    {
                        "schema_version": (
                            "spatialaccagent.board_simulation_preflight_materialization.v1"
                        ),
                        "status": "pass",
                        "manifest": str(board_manifest_path),
                        "manifest_sha256": board_manifest_sha256,
                        "exact_board_preflight": {
                            "status": "pass",
                            "blockers": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            historical_manifest_block = {
                "status": "ready",
                "blockers": [
                    "manifest_validation_failure: board weight image does not contain every tensor hash"
                ],
            }

            with patch(
                "accagent.framework.stage_repair_execute.validate_exact_board_preflight",
                return_value={"status": "pass", "blockers": []},
            ):
                authority = current_exact_board_preflight_execution_authority(
                    run_dir,
                    out_dir,
                    historical_manifest_block,
                )

            self.assertEqual(authority["status"], "pass")
            self.assertEqual(authority["route"], "case_vcs_functional_sim")
            self.assertTrue(authority["supersedes_historical_manifest_feedback"])
            self.assertTrue(
                current_exact_board_preflight_supersedes_manifest_failure(
                    authority,
                    {
                        "current_board_vcs_feedback": {
                            "diagnosis": {
                                "value": {
                                    "failure_class": (
                                        "manifest_validation_failure"
                                    )
                                }
                            }
                        }
                    },
                )
            )

            binding_path.write_text('{"status":"changed"}\n', encoding="utf-8")
            with patch(
                "accagent.framework.stage_repair_execute.validate_exact_board_preflight",
                return_value={"status": "pass", "blockers": []},
            ):
                stale = current_exact_board_preflight_execution_authority(
                    run_dir,
                    out_dir,
                    historical_manifest_block,
                )
            self.assertEqual(stale["status"], "incomplete")
            self.assertIsNone(stale["route"])
            self.assertFalse(
                current_exact_board_preflight_supersedes_manifest_failure(
                    stale,
                    {
                        "current_board_vcs_feedback": {
                            "diagnosis": {
                                "value": {
                                    "failure_class": (
                                        "manifest_validation_failure"
                                    )
                                }
                            }
                        }
                    },
                )
            )

    def test_current_patch_application_feedback_is_repair_step_bound(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "exact_board_integration_harness",
                    "violated_contract": "board preflight",
                },
            }
            report_path = out_dir / "agent_patch_application.json"
            report_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "blockers": ["manifest is invalid JSON"],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )

            current = current_agent_patch_application_feedback(out_dir, step)
            self.assertEqual(current["status"], "ready")
            self.assertEqual(current["summary"], "manifest is invalid JSON")
            self.assertEqual(
                current["patch_application"]["sha256"],
                hashlib.sha256(report_path.read_bytes()).hexdigest(),
            )

            stale_step = {**step, "id": "repair_step.01"}
            self.assertEqual(
                current_agent_patch_application_feedback(out_dir, stale_step)[
                    "status"
                ],
                "not_run",
            )

    def test_completed_fresh_replay_supersedes_old_transaction_rejection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "repair_execution"
            out_dir.mkdir()
            manifest_path = Path(temp_dir) / "board_simulation_manifest.json"
            manifest = {"validation_mode": "compute_slot_axi"}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "exact_board_integration_harness",
                    "violated_contract": "board VCS must pass",
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": (
                            "spatialaccagent.agent_patch_application.v1"
                        ),
                        "status": "blocked",
                        "blockers": ["prior replay request schema was invalid"],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            runner_path = Path(temp_dir) / "runner.json"
            diagnosis_path = Path(temp_dir) / "diagnosis.json"
            runner = {
                "status": "fail",
                "input_fingerprint_sha256": "4" * 64,
                "validation_mode": "compute_slot_axi",
                "preflight_manifest_projection_sha256": (
                    preflight_manifest_projection_sha256(manifest)
                ),
            }
            diagnosis = {
                "status": "needs_repair",
                "summary": "simv terminated with a segmentation fault",
                "repair_handoff": {
                    "agent_should_apply_code_changes": False,
                    "repair_scope": "simulation_environment",
                },
            }
            runner_path.write_text(json.dumps(runner), encoding="utf-8")
            diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
            decision = {
                "schema_version": (
                    "spatialaccagent.adaptive_observation_decision.v1"
                ),
                "mode": "fresh_exact_source_provenance_replay",
                "frontier_id": "connected_kernel_input_to_output",
                "field_observations": [
                    {
                        "evidence_pointer": "/current_board_vcs_feedback/cycle",
                        "observed_value": 20788597,
                        "semantic_role": "counter",
                        "interpretation": "last committed progress cycle",
                    }
                ],
                "rationale": "replay the unchanged exact source once",
            }
            replay_path = out_dir / "fresh_exact_source_provenance_replay.json"
            replay_path.write_text(
                json.dumps(
                    {
                        "schema_version": (
                            "spatialaccagent.fresh_exact_source_provenance_replay.v1"
                        ),
                        "status": "fail",
                        "execution_generation_sha256": "9" * 64,
                        "decision": decision,
                        "real_tool_probe": {
                            "status": "fail",
                            "summary": "VCS simulator process crashed",
                            "current_board_vcs_feedback": {
                                "status": "ready",
                                "runner_report": {
                                    "path": str(runner_path),
                                    "sha256": hashlib.sha256(
                                        runner_path.read_bytes()
                                    ).hexdigest(),
                                    "value": runner,
                                },
                                "diagnosis": {
                                    "path": str(diagnosis_path),
                                    "sha256": hashlib.sha256(
                                        diagnosis_path.read_bytes()
                                    ).hexdigest(),
                                    "value": diagnosis,
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            os.utime(patch_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(replay_path, ns=(2_000_000_000, 2_000_000_000))

            replay_feedback = (
                current_fresh_exact_source_provenance_replay_feedback(
                    out_dir,
                    manifest_path,
                )
            )
            patch_feedback = current_agent_patch_application_feedback(
                out_dir,
                step,
                superseding_result_path=replay_path,
            )

        self.assertEqual(replay_feedback["status"], "ready")
        self.assertEqual(replay_feedback["replay_status"], "fail")
        self.assertEqual(replay_feedback["decision"], decision)
        self.assertNotIn("real_tool_probe", replay_feedback)
        self.assertEqual(patch_feedback["status"], "not_run")
        self.assertIn("superseded", patch_feedback["summary"])

    def test_newer_current_board_result_supersedes_old_transaction_rejection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "repair_execution"
            out_dir.mkdir()
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {"repair_kind": "exact_board_integration_harness"},
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "blockers": ["old environment failure"],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            runner_path = out_dir / "current_board_vcs.json"
            runner_path.write_text("{}\n", encoding="utf-8")
            os.utime(patch_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(runner_path, ns=(2_000_000_000, 2_000_000_000))
            feedback = current_agent_patch_application_feedback(
                out_dir,
                step,
                superseding_result_path=runner_path,
            )

        self.assertEqual(feedback["status"], "not_run")
        self.assertIn("superseded", feedback["summary"])

    def test_completed_current_board_semantic_failure_supersedes_rewritten_old_rejection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "repair_execution"
            out_dir.mkdir()
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {"repair_kind": "exact_board_integration_harness"},
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "blocked",
                        "blockers": ["old remote prune failure"],
                        "repair_checkpoint": repair_step_checkpoint(step),
                    }
                ),
                encoding="utf-8",
            )
            runner_path = out_dir / "case_board_vcs_functional.json"
            runner_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "run": {"status": "fail", "returncode": 86},
                    }
                ),
                encoding="utf-8",
            )
            os.utime(runner_path, ns=(1, 1))
            os.utime(patch_path, ns=(2, 2))
            feedback = current_agent_patch_application_feedback(
                out_dir,
                step,
                superseding_result_path=runner_path,
            )

        self.assertEqual(feedback["status"], "not_run")
        self.assertIn("superseded", feedback["summary"])

    def test_checkpoint_specialist_preserves_current_patch_feedback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest_path = (
                run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            )
            testbench_path = (
                run_dir / "generated" / "board_integration" / "BoardTb.sv"
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
            manifest_path.write_text('{"status":"ready"}\n', encoding="utf-8")
            testbench_path.write_text(
                "module BoardTb; wire hook; endmodule\n", encoding="utf-8"
            )
            board_manifest_path.write_text(
                json.dumps(
                    {
                        "top_module": "BoardTb",
                        "testbench": {
                            "path": str(testbench_path),
                            "sha256": hashlib.sha256(
                                testbench_path.read_bytes()
                            ).hexdigest(),
                            "sole_dut_instance": "dut",
                        },
                    }
                ),
                encoding="utf-8",
            )
            feedback = {
                "schema_version": (
                    "spatialaccagent.current_agent_patch_application_feedback.v1"
                ),
                "status": "ready",
                "blockers": [
                    "file_edits[1] replace_text anchors overlap in the pre-edit source"
                ],
                "patch_application": {
                    "path": "agent_patch_application.json",
                    "sha256": "a" * 64,
                },
            }
            package = {
                "current_patch_application_feedback": feedback,
                "exact_board_integration_repair_context": {
                    "adaptive_design_inputs": {
                        "simulation_checkpoint_authority": {
                            "status": "ready",
                            "required_manifest_contract": {"status": "ready"},
                            "agent_owned": {},
                            "framework_owned": {},
                            "current_request": {},
                        },
                        "simulation_checkpoint_capability_gap": {
                            "runtime_execution_failure": {"status": "ready"},
                            "atomic_manifest_merge": {
                                "target_path": str(manifest_path),
                                "expected_sha256": hashlib.sha256(
                                    manifest_path.read_bytes()
                                ).hexdigest(),
                                "json_pointer": (
                                    "/board_simulation_preflight_plan/testbench/"
                                    "simulation_checkpoint_contract"
                                ),
                            },
                        },
                    }
                },
            }

            specialist = checkpoint_hook_specialist_package(package, run_dir)

            self.assertEqual(specialist["status"], "ready")
            self.assertEqual(
                specialist["current_patch_application_feedback"], feedback
            )
            self.assertTrue(
                any(
                    "current_patch_application_feedback.status=ready" in rule
                    for rule in checkpoint_hook_prompt_rules()
                )
            )
            self.assertTrue(
                any(
                    "restored_semantic_suffix_materialization.status=fail" in rule
                    for rule in checkpoint_hook_prompt_rules()
                )
            )
            self.assertTrue(
                any(
                    "semantic_record_diff.status=different" in rule
                    for rule in checkpoint_hook_prompt_rules()
                )
            )
            self.assertTrue(
                any(
                    "live_state_witness_diff.status=different" in rule
                    for rule in checkpoint_hook_prompt_rules()
                )
            )
            self.assertTrue(
                any(
                    "restore_runtime_failure_evidence.status=observed" in rule
                    for rule in checkpoint_hook_prompt_rules()
                )
            )

    def test_board_repair_bundle_and_compaction_preserve_every_editable_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            board_root = run_dir / "generated" / "board_integration"
            out_dir.mkdir(parents=True)
            board_root.mkdir(parents=True)
            sources = {
                board_root / "scheduler.sv": "module scheduler; endmodule\n",
                board_root / "nested" / "adapter.v": "module adapter; endmodule\n",
            }
            for path, content in sources.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            manifest_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest = {
                "schema_version": "spatialaccagent.dut_weight_binding_manifest.v1",
                "status": "incomplete",
                "single_layer_harness": {
                    "source_files": [
                        {
                            "source_id": f"single_layer_source_{index}",
                            "path": f"/generated/kernel/source_{index}.sv",
                            "sha256": hashlib.sha256(str(index).encode("utf-8")).hexdigest(),
                        }
                        for index in range(1200)
                    ]
                },
                "board_simulation_preflight_plan": {
                    "testbench": {
                        "source": {
                            "source_id": "generated.testbench",
                            "role": "testbench",
                            "path": "/generated/board/testbench.sv",
                            "sha256": "f" * 64,
                        }
                    }
                },
                "stage_harnesses": {},
                "raw_manifest_marker": "must remain editable in compact repair prompts",
            }
            manifest_content = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            self.assertGreater(len(manifest_content), 80_000)
            manifest_path.write_text(manifest_content, encoding="utf-8")
            manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            tensor_hashes = [
                hashlib.sha256(f"tensor-{index}".encode("utf-8")).hexdigest()
                for index in range(2)
            ]
            catalog_path = (
                run_dir
                / "verification"
                / "model_weights"
                / "transformer_block_weight_catalog.json"
            )
            catalog_path.parent.mkdir(parents=True)
            catalog_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "accelerator_scope": "transformer_blocks_only",
                        "scope_coverage_complete": True,
                        "tensors": [
                            {"source_slice_sha256": value}
                            for value in reversed(tensor_hashes)
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            board_identity_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json"
            )
            board_identity_path.parent.mkdir(parents=True)
            board_identity_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "compute_slot_abi": {
                            "replaced_source_ids": ["sample.replace"]
                        },
                        "selected_simulation_source_closure": {
                            "source_files": [
                                {
                                    "source_id": "sample.keep",
                                    "path": "sample_keep.sv",
                                    "file_type": "SystemVerilog",
                                },
                                {
                                    "source_id": "sample.replace",
                                    "path": "sample_replace.sv",
                                    "file_type": "SystemVerilog",
                                },
                            ]
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            fixture_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "external_simulation_fixture.json"
            )
            fixture_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "compile_authority": {
                            "compile_sources": [
                                {"source_id": "fixture.memory_model"}
                            ]
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            stale_probe_path = (
                out_dir / "repair_step_00_verification_capability_probe_pre_patch.json"
            )
            stale_probe_path.write_text(
                json.dumps({"summary": "obsolete physical DDR failure"}),
                encoding="utf-8",
            )
            stale_execution_report = out_dir / "repair_execution_report.json"
            stale_execution_report.write_text(
                json.dumps({"summary": "obsolete physical DDR failure"}),
                encoding="utf-8",
            )
            tool_profile = {
                "schema_version": "spatialaccagent.tool_profile.v1",
                "tools": [
                    {
                        "role": "functional_verification",
                        "host": "hyyuan@10.12.133.23",
                        "port": 22,
                        "executable": "vcs",
                    }
                ],
            }
            bundle = capability_repair_source_bundle(
                {"documents": [], "editable_contract": {}},
                run_dir,
                out_dir,
                verification_scope="board_axi_ddr_closure",
            )
            feedback = {
                "schema_version": "spatialaccagent.exact_board_vcs_feedback.v1",
                "status": "ready",
                "diagnosis": {"path": "/diagnosis.json", "sha256": "a" * 64, "value": {"status": "needs_repair"}},
                "runner_report": {"path": "/runner.json", "sha256": "b" * 64, "value": {"phase": "remote_vcs"}},
            }
            preflight_feedback = {
                "schema_version": "spatialaccagent.exact_board_preflight_feedback.v1",
                "status": "ready",
                "blockers": [
                    "board_integration: source row is incomplete",
                    "board_preflight: compile plan is incomplete",
                ],
                "preflight": {
                    "path": "/preflight.json",
                    "sha256": "c" * 64,
                    "value": {
                        "status": "incomplete",
                        "blockers": ["compile plan is incomplete"],
                        "exact_board_preflight": {
                            "verified_compile_source_ids": ["source.0", "source.1"],
                            "checks": [
                                {
                                    "name": "source_closure",
                                    "status": "fail",
                                    "blockers": ["compile plan is incomplete"],
                                    "root_source_ids": ["source.0", "source.1"],
                                }
                            ],
                        },
                    },
                },
            }
            patch_feedback = {
                "schema_version": "spatialaccagent.current_agent_patch_application_feedback.v1",
                "status": "ready",
                "blockers": ["manifest is invalid JSON"],
                "patch_application": {
                    "path": "/patch.json",
                    "sha256": "d" * 64,
                    "value": {"status": "blocked"},
                },
            }
            compact = compact_verification_capability_repair_package(
                {
                    "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
                    "repair_source_bundle": bundle,
                    "exact_board_integration_repair_context": {
                        "schema_version": "spatialaccagent.exact_board_integration_repair_context.v1",
                        "status": "ready",
                        "adaptive_design_inputs": {
                            "certified_single_layer_binding": {
                                "path": str(manifest_path),
                                "sha256": manifest_sha,
                                "value": manifest,
                            },
                            "current_tool_profile": {
                                "path": str(run_dir / "input" / "tool_profile.json"),
                                "sha256": hashlib.sha256(
                                    json.dumps(tool_profile, sort_keys=True).encode("utf-8")
                                ).hexdigest(),
                                "value": tool_profile,
                            },
                        },
                    },
                    "current_board_vcs_feedback": feedback,
                    "current_board_preflight_feedback": preflight_feedback,
                    "current_patch_application_feedback": patch_feedback,
                }
            )

        inventory = bundle["editable_contract"]["current_board_source_files"]
        self.assertEqual({row["path"] for row in inventory}, {str(path) for path in sources})
        bundle_document_paths = {
            str(row.get("path")) for row in bundle.get("documents", [])
        }
        self.assertNotIn(str(stale_probe_path), bundle_document_paths)
        self.assertNotIn(str(stale_execution_report), bundle_document_paths)
        self.assertEqual(
            bundle["editable_contract"]["current_board_manifest_file"]["path"],
            str(manifest_path),
        )
        rewrite_authority = bundle["editable_contract"][
            "board_manifest_rewrite_authority"
        ]
        self.assertEqual(
            rewrite_authority["agent_file_edit_contract"]["path"],
            str(manifest_path),
        )
        self.assertIn(
            "stage_harnesses",
            rewrite_authority["executor_preservation_contract"][
                "mechanically_preserved_fields"
            ],
        )
        self.assertEqual(
            rewrite_authority["complete_transformer_block_tensor_hashes"]["hashes"],
            sorted(tensor_hashes),
        )
        self.assertEqual(
            rewrite_authority["compile_source_coverage_authority"][
                "preserved_sample_compile_source_ids"
            ],
            [],
        )
        self.assertEqual(
            rewrite_authority["compile_source_coverage_authority"][
                "replaced_sample_source_ids"
            ],
            ["sample.replace"],
        )
        coverage = rewrite_authority["compile_source_coverage_authority"]
        self.assertIn("generated.testbench", coverage["current_generated_source_ids"])
        self.assertEqual(
            coverage["certified_kernel_source_ids"][0],
            "certified_kernel.0000." + hashlib.sha256(b"0").hexdigest()[:16],
        )
        self.assertEqual(
            coverage["vcs_argv_token_contract"]["source_token_shape"],
            {"source_id": "<resolved source ID>"},
        )
        expanded = rewrite_authority["expanded_source_authority"]
        self.assertEqual(expanded["counts"]["sample_total"], 1)
        self.assertEqual(expanded["counts"]["sample_preserved_compiler_inputs"], 0)
        self.assertEqual(expanded["counts"]["external_fixture_compile_sources"], 0)
        self.assertEqual(expanded["counts"]["certified_kernel_sources"], 1200)
        self.assertTrue(
            expanded["ownership_contract"][
                "certified_kernel_rows_must_not_be_copied_into_agent_multilayer_source_files"
            ]
        )
        documents = {str(row.get("path")): row for row in compact["repair_source_bundle"]["documents"]}
        self.assertEqual(documents[str(manifest_path)]["json_content"], manifest)
        self.assertIn(
            "complete JSON object is selected",
            documents[str(manifest_path)]["content_preservation"],
        )
        self.assertNotIn("content", documents[str(manifest_path)])
        duplicate_manifest_docs = [
            path
            for path in documents
            if path.startswith(str(manifest_path) + "#")
        ]
        self.assertEqual(duplicate_manifest_docs, [])
        self.assertTrue(
            compact["repair_source_bundle"][
                "documents_omitted_as_current_editable_manifest_duplicates"
            ]["document_count"]
        )
        self.assertEqual(
            compact["exact_board_integration_repair_context"]["adaptive_design_inputs"][
                "certified_single_layer_binding"
            ]["editable_manifest_document"]["path"],
            str(manifest_path),
        )
        for path, content in sources.items():
            self.assertEqual(documents[str(path)]["content"], content)
            self.assertEqual(
                documents[str(path)]["sha256"],
                hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        self.assertNotIn("current_board_vcs_feedback", compact)
        compact_preflight = compact["current_board_preflight_feedback"]
        self.assertEqual(compact_preflight["blockers"], preflight_feedback["blockers"])
        self.assertEqual(compact_preflight["preflight"]["sha256"], "c" * 64)
        source_projection = compact_preflight["preflight"]["value"][
            "exact_board_preflight"
        ]["verified_compile_source_ids"]
        self.assertEqual(source_projection["row_count"], 2)
        self.assertNotIn("source.0", json.dumps(source_projection))
        self.assertEqual(
            compact["current_patch_application_feedback"], patch_feedback
        )
        self.assertEqual(
            compact["exact_board_integration_repair_context"]["adaptive_design_inputs"][
                "current_tool_profile"
            ]["value"]["tools"][0]["host"],
            "hyyuan@10.12.133.23",
        )
        compact_authority = compact["repair_source_bundle"]["editable_contract"][
            "board_manifest_rewrite_authority"
        ]
        self.assertEqual(
            compact_authority["complete_transformer_block_tensor_hashes"]["count"],
            2,
        )
        self.assertTrue(
            compact_authority["agent_file_edit_contract"][
                "preserved_lower_layer_fields_may_be_omitted_from_json_content"
            ]
        )

    def test_board_kernel_lifecycle_authority_keeps_dynamic_proof_pending(self) -> None:
        interface = {
            "clock_port": "clk",
            "reset_port": "rst",
            "start_port": "start",
            "weight_loader": {
                key: key for key in ("valid_port", "ready_port", "data_port", "addr_port", "last_port")
            },
            "runtime_loader": {
                key: key for key in ("valid_port", "ready_port", "data_port", "addr_port", "last_port")
            },
            "output": {"valid_port": "out_valid", "ready_port": "out_ready"},
        }
        authority, blockers = board_kernel_lifecycle_generation_authority(
            {
                "status": "pass",
                "single_layer_harness": {
                    "top_module": "CurrentRunKernel",
                    "interface": interface,
                },
            },
            {"status": "pass"},
            {"board": {"expected_target_layers": 3, "expected_output": {"beats": 17}}},
            {"num_layers": 3},
        )

        self.assertEqual(blockers, [])
        self.assertEqual(authority["status"], "ready")
        self.assertEqual(authority["accepted_output_beats_per_layer"], 17)
        self.assertEqual(authority["validation_boundary"]["dynamic_validation"], "pending")
        self.assertFalse(authority["validation_boundary"]["hardware_pass_claimed"])

        resumed_authority, resumed_blockers = (
            board_kernel_lifecycle_generation_authority(
                {
                    "status": "incomplete",
                    "single_layer_harness": {
                        "top_module": "CurrentRunKernel",
                        "interface": interface,
                    },
                },
                {"status": "pass"},
                {
                    "board": {
                        "expected_target_layers": 3,
                        "expected_output": {"beats": 17},
                    }
                },
                {"num_layers": 3},
                certified_binding_attested=True,
            )
        )
        self.assertEqual(resumed_blockers, [])
        self.assertEqual(resumed_authority["status"], "ready")

    def test_board_kernel_lifecycle_authority_uses_task_scope_over_stale_testbench(self) -> None:
        interface = {
            "clock_port": "clk",
            "reset_port": "rst",
            "start_port": "start",
            "weight_loader": {
                key: key for key in ("valid_port", "ready_port", "data_port", "addr_port", "last_port")
            },
            "runtime_loader": {
                key: key for key in ("valid_port", "ready_port", "data_port", "addr_port", "last_port")
            },
            "output": {"valid_port": "out_valid", "ready_port": "out_ready"},
        }
        scope = resolve_board_validation_scope(
            {
                "acceptance_policy": {
                    "board_validation_mode": PREFIX_MODEL_MODE,
                    "board_validation_layer_count": 1,
                }
            },
            {"num_layers": 24},
        )

        authority, blockers = board_kernel_lifecycle_generation_authority(
            {
                "status": "pass",
                "single_layer_harness": {
                    "top_module": "CurrentRunKernel",
                    "interface": interface,
                },
            },
            {"status": "pass"},
            {
                "board": {
                    "model_layer_count": 24,
                    "expected_target_layers": 24,
                    "validation_layer_indices": list(range(24)),
                    "expected_output": {"beats": 17},
                }
            },
            {"num_layers": 24},
            validation_scope=scope,
        )

        self.assertEqual(blockers, [])
        self.assertEqual(authority["target_layer_count"], 1)
        self.assertEqual(authority["validation_layer_indices"], [0])
        self.assertFalse(authority["requires_next_layer_prefetch"])

    def test_first_exact_board_create_skips_only_unexecutable_pre_patch_probe(self) -> None:
        self.assertTrue(
            skip_initial_exact_board_pre_patch(
                board_integration_repair=True,
                resource_resume_status="not_run",
                existing_replay_ready=False,
            )
        )
        self.assertFalse(
            skip_initial_exact_board_pre_patch(
                board_integration_repair=True,
                resource_resume_status="not_run",
                existing_replay_ready=True,
            )
        )
        self.assertFalse(
            skip_initial_exact_board_pre_patch(
                board_integration_repair=True,
                resource_resume_status="pass",
                existing_replay_ready=False,
            )
        )
        self.assertFalse(
            skip_initial_exact_board_pre_patch(
                board_integration_repair=False,
                resource_resume_status="not_run",
                existing_replay_ready=False,
            )
        )

    def test_missing_current_harness_overrides_stale_board_source_readiness(self) -> None:
        action = {
            "failed_current_layer_gates": [
                {"name": "case_multilayer_pipeline", "status": "fail"},
                {"name": "case_vcs_functional_sim", "status": "not_run"},
                {"name": "case_vcs_evidence_analyzer", "status": "not_run"},
            ]
        }

        self.assertTrue(
            board_harness_bootstrap_required(
                action,
                existing_replay_ready=True,
            )
        )
        self.assertFalse(
            board_harness_bootstrap_required(
                action,
                existing_replay_ready=False,
                bootstrap_generation_applied=True,
            )
        )

        repair_rules = board_integration_prompt_rules("repair")
        self.assertTrue(
            any(
                "do not treat it as a mechanical anchor error" in rule.lower()
                for rule in repair_rules
            )
        )
        self.assertFalse(
            board_harness_bootstrap_required(
                action,
                existing_replay_ready=False,
                current_real_vcs_failure_ready=True,
            )
        )
        action["failed_current_layer_gates"][1]["status"] = "fail"
        self.assertFalse(
            board_harness_bootstrap_required(
                action,
                existing_replay_ready=True,
            )
        )

    def test_current_applied_board_bootstrap_exits_generation_phase(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            source = (
                run_dir
                / "generated"
                / "board_integration"
                / "GeneratedBoardAdapter.sv"
            )
            source.parent.mkdir(parents=True)
            source.write_text("module GeneratedBoardAdapter; endmodule\n", encoding="utf-8")
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                        "agent": "exact_board_integration_generation_agent",
                        "repair_execution_context": {
                            "repair_step_id": "repair_step.00"
                        },
                        "files": [
                            {
                                "path": str(source),
                                "after_sha256": hashlib.sha256(
                                    source.read_bytes()
                                ).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            self.assertTrue(
                current_exact_board_bootstrap_generation_applied(
                    run_dir,
                    out_dir,
                    {"id": "repair_step.00"},
                )
            )
            source.write_text("module DriftedBoardAdapter; endmodule\n", encoding="utf-8")
            self.assertFalse(
                current_exact_board_bootstrap_generation_applied(
                    run_dir,
                    out_dir,
                    {"id": "repair_step.00"},
                )
            )

            source.write_text(
                "module GeneratedBoardAdapter; endmodule\n", encoding="utf-8"
            )
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "exact_board_integration_harness",
                    "violated_contract": (
                        "current_verification_capability_must_execute_before_hardware_repair"
                    ),
                },
            }
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                        "repair_checkpoint": repair_step_checkpoint(step),
                        "files": [
                            {
                                "path": str(source),
                                "after_sha256": hashlib.sha256(
                                    source.read_bytes()
                                ).hexdigest(),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            llm_dir = out_dir / "llm"
            llm_dir.mkdir(parents=True)
            (llm_dir / "exact_board_integration_generation_agent_result.json").write_text(
                json.dumps({"status": "failed", "error": "later Agent attempt failed"}),
                encoding="utf-8",
            )

            self.assertTrue(
                current_exact_board_bootstrap_generation_applied(
                    run_dir,
                    out_dir,
                    step,
                )
            )

    def test_current_applied_patch_resumes_without_duplicate_vcs_analysis(self) -> None:
        baseline = {
            "resource_resume_status": "pass",
            "resume_requires_board_repair": False,
            "has_pending_checkpoint_executor_retry": False,
            "has_pending_checkpoint_calibration": False,
            "has_current_checkpoint_calibration_failure": False,
            "has_current_source_validation_evidence": False,
        }
        self.assertTrue(prior_resource_validation_resume_allowed(**baseline))
        current_failure = dict(baseline)
        current_failure["has_current_source_validation_evidence"] = True
        self.assertFalse(
            prior_resource_validation_resume_allowed(**current_failure)
        )
        for gate in (
            "resume_requires_board_repair",
            "has_pending_checkpoint_executor_retry",
            "has_pending_checkpoint_calibration",
            "has_current_checkpoint_calibration_failure",
        ):
            guarded = dict(baseline)
            guarded[gate] = True
            self.assertFalse(
                prior_resource_validation_resume_allowed(**guarded),
                gate,
            )
        no_resume = dict(baseline)
        no_resume["resource_resume_status"] = "not_run"
        self.assertFalse(prior_resource_validation_resume_allowed(**no_resume))

    def test_board_evidence_must_follow_the_applied_patch(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "repair_execution"
            out_dir.mkdir(parents=True)
            runner_path = Path(temp_dir) / "case_board_vcs_functional.json"
            runner_path.write_text('{"status":"fail"}\n', encoding="utf-8")
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text('{"status":"pass"}\n', encoding="utf-8")
            evidence = {
                "current_board_vcs_feedback": {
                    "runner_report": {"path": str(runner_path)}
                }
            }

            os.utime(runner_path, (1, 1))
            os.utime(patch_path, (2, 2))
            self.assertFalse(
                current_board_evidence_postdates_applied_patch(
                    evidence, out_dir
                )
            )
            os.utime(runner_path, (3, 3))
            self.assertTrue(
                current_board_evidence_postdates_applied_patch(
                    evidence, out_dir
                )
            )

    def test_board_context_fails_closed_without_runtime_and_weight_image(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_debug_episode",
                side_effect=AssertionError(
                    "ordinary hardware context must not enter checkpoint maintenance"
                ),
            ):
                context = board_integration_repair_context(
                    {}, Path(temp_dir) / "run"
                )

        self.assertEqual(context["status"], "blocked")
        blockers = "\n".join(context["blockers"])
        self.assertIn("memory/runtime", blockers)
        self.assertIn("weight image", blockers)
        adaptive = context["adaptive_design_inputs"]
        self.assertNotIn("simulation_checkpoint_authority", adaptive)
        self.assertNotIn("simulation_checkpoint_capability_gap", adaptive)
        self.assertEqual(
            adaptive["simulation_checkpoint_policy"]["status"],
            "optional_acceleration",
        )

    def test_explicit_checkpoint_context_retains_specialist_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch(
                "accagent.framework.stage_repair_execute.prepare_checkpoint_debug_episode",
                return_value={"status": "not_admitted"},
            ), patch(
                "accagent.framework.stage_repair_execute.checkpoint_generation_authority",
                return_value={"status": "ready"},
            ):
                context = board_integration_repair_context(
                    {},
                    Path(temp_dir) / "run",
                    explicit_checkpoint_maintenance=True,
                )

        adaptive = context["adaptive_design_inputs"]
        self.assertIn("simulation_checkpoint_authority", adaptive)
        self.assertIn("simulation_checkpoint_capability_gap", adaptive)
        self.assertTrue(
            adaptive["simulation_checkpoint_policy"][
                "explicit_maintenance_requested"
            ]
        )

    def test_checkpoint_reclassification_runs_only_for_legacy_diagnosis(self) -> None:
        common = {
            "explicit_checkpoint_maintenance": False,
            "has_pending_checkpoint_calibration": True,
            "has_checkpoint_calibration_failure": False,
        }
        self.assertTrue(
            optional_checkpoint_reclassification_required(
                **common,
                current_feedback_failure=(
                    "simulation_checkpoint_capability_missing_or_invalid"
                ),
            )
        )
        self.assertFalse(
            optional_checkpoint_reclassification_required(
                **common,
                current_feedback_failure="vcs_runtime_semantic_stall",
            )
        )
        self.assertFalse(
            optional_checkpoint_reclassification_required(
                **{
                    **common,
                    "explicit_checkpoint_maintenance": True,
                },
                current_feedback_failure=(
                    "simulation_checkpoint_capability_missing_or_invalid"
                ),
            )
        )

    def test_frozen_compute_slot_compile_authority_is_single_and_fail_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            identity_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json"
            )
            manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            certificate_dir = identity_path.parent / "certificates"
            certificate_dir.mkdir(parents=True)
            manifest_path.parent.mkdir(parents=True)
            identity = {
                "simulator_compile_authority": {
                    "path": str(identity_path.parent / "mutable_authority.json"),
                    "sha256": "8" * 64,
                    "status": "pass",
                }
            }
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            identity_sha256 = hashlib.sha256(identity_path.read_bytes()).hexdigest()
            plan = {
                "schema_version": "spatialaccagent.vcs_compile_plan.v1",
                "status": "ready",
                "compile_authority": {
                    "vivado_facts_sha256": "1" * 64,
                    "simulator_export_context_sha256s": ["2" * 64],
                },
                "ordered_commands": [],
            }
            plan_sha256 = hashlib.sha256(
                json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            stable_attestation = {
                "status": "pass",
                "source_identity_sha256": identity_sha256,
                "attested_vivado_facts_sha256": "1" * 64,
                "attested_simulator_export_context_sha256s": ["2" * 64],
                "vcs_compile_plan_sha256": plan_sha256,
                "prior_executed_manifest": {"path": "/old/a", "sha256": "a" * 64},
                "prior_vcs_job_contract": {"path": "/old/b", "sha256": "b" * 64},
                "prior_vcs_runner_report": {"path": "/old/c", "sha256": "c" * 64},
            }
            prior = {
                "status": "fail",
                "validation_mode": "compute_slot_axi",
                "source_identity_sha256": identity_sha256,
                "source_files": [
                    {"source_id": "generated:board", "sha256": "4" * 64}
                ],
                "vcs_compile_plan": plan,
                "vcs_compile_plan_sha256": plan_sha256,
                "frozen_compute_slot_identity_attestation": stable_attestation,
            }
            prior_path = certificate_dir / "prior.json"
            job_path = certificate_dir / "job.json"
            runner_path = certificate_dir / "runner.json"
            prior_path.write_text(json.dumps(prior), encoding="utf-8")
            job_path.write_text(json.dumps({"job": "bound"}), encoding="utf-8")
            runner_path.write_text(json.dumps({"runner": "bound"}), encoding="utf-8")
            current_attestation = json.loads(json.dumps(stable_attestation))
            for name, path in (
                ("prior_executed_manifest", prior_path),
                ("prior_vcs_job_contract", job_path),
                ("prior_vcs_runner_report", runner_path),
            ):
                current_attestation[name] = {
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            current = {
                **prior,
                "status": "ready",
                "source_files": [
                    {"source_id": "generated:board", "sha256": "5" * 64}
                ],
                "frozen_compute_slot_identity_attestation": current_attestation,
            }
            manifest_path.write_text(json.dumps(current), encoding="utf-8")

            with patch(
                "accagent.framework.stage_repair_execute.validate_frozen_compute_slot_identity_attestation",
                return_value=(True, [], {}),
            ):
                authority, blockers = frozen_compute_slot_repair_compile_authority(
                    run_dir,
                    identity_path,
                    identity,
                )
                self.assertEqual(blockers, [])
                self.assertEqual(authority["status"], "pass")
                self.assertEqual(
                    authority["source"],
                    "frozen_compute_slot_identity_attestation",
                )
                self.assertEqual(
                    authority["compile_authority"],
                    plan["compile_authority"],
                )

                job_path.write_text(json.dumps({"job": "tampered"}), encoding="utf-8")
                rejected, rejected_blockers = (
                    frozen_compute_slot_repair_compile_authority(
                        run_dir,
                        identity_path,
                        identity,
                    )
                )
                self.assertEqual(rejected, {})
                self.assertTrue(rejected_blockers)

            current["validation_mode"] = "exact_sample_physical_ddr"
            manifest_path.write_text(json.dumps(current), encoding="utf-8")
            rejected, rejected_blockers = frozen_compute_slot_repair_compile_authority(
                run_dir,
                identity_path,
                identity,
            )
            self.assertEqual(rejected, {})
            self.assertIn("compute_slot_axi", rejected_blockers[0])

    def test_frozen_compute_slot_certificate_recovery_requires_one_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            identity_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json"
            )
            certificate_dir = identity_path.parent / "certificates"
            certificate_dir.mkdir(parents=True)
            identity = {"status": "pass"}
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            attestation = {
                "status": "pass",
                "source_identity_sha256": hashlib.sha256(
                    identity_path.read_bytes()
                ).hexdigest(),
                "attested_vivado_facts_sha256": "1" * 64,
                "attested_simulator_export_context_sha256s": ["2" * 64],
            }
            plan = {
                "schema_version": "spatialaccagent.vcs_compile_plan.v1",
                "status": "ready",
                "compile_authority": {
                    "vivado_facts_sha256": "1" * 64,
                    "simulator_export_context_sha256s": ["2" * 64],
                },
            }

            def add_certificate(value: dict) -> Path:
                payload = json.dumps(value).encode()
                digest = hashlib.sha256(payload).hexdigest()
                path = certificate_dir / f"executed_manifest_{digest}.json"
                path.write_bytes(payload)
                return path

            add_certificate(
                {
                    "frozen_compute_slot_identity_attestation": attestation,
                    "vcs_compile_plan": plan,
                }
            )
            with patch(
                "accagent.framework.stage_repair_execute.validate_frozen_compute_slot_identity_attestation",
                return_value=(True, [], {}),
            ):
                recovered, recovered_plan, recovery, blockers = (
                    recover_certified_frozen_compute_slot_authority(
                        run_dir,
                        identity_path,
                        identity,
                    )
                )
                self.assertEqual(blockers, [])
                self.assertEqual(recovered, attestation)
                self.assertEqual(recovered_plan, plan)
                self.assertEqual(recovery["matching_certificate_count"], 1)

                equivalent = json.loads(json.dumps(attestation))
                equivalent["prior_vcs_runner_report"] = {
                    "path": "/certificate/rolling",
                    "sha256": "3" * 64,
                }
                add_certificate(
                    {
                        "frozen_compute_slot_identity_attestation": equivalent,
                        "vcs_compile_plan": plan,
                    }
                )
                _, _, recovery, blockers = (
                    recover_certified_frozen_compute_slot_authority(
                        run_dir,
                        identity_path,
                        identity,
                    )
                )
                self.assertEqual(blockers, [])
                self.assertEqual(recovery["matching_certificate_count"], 2)

                changed_plan = json.loads(json.dumps(plan))
                changed_plan["top_module"] = "DifferentTop"
                add_certificate(
                    {
                        "frozen_compute_slot_identity_attestation": attestation,
                        "vcs_compile_plan": changed_plan,
                    }
                )
                rejected = recover_certified_frozen_compute_slot_authority(
                    run_dir,
                    identity_path,
                    identity,
                )
                self.assertEqual(rejected[0], {})
                self.assertIn("disagree", rejected[3][0])

    def test_board_context_excludes_replaced_mutable_compile_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            interface_dir = run_dir / "verification" / "board_interface"
            interface_dir.mkdir(parents=True)
            mutable_path = interface_dir / "vivado_vcs_compile_authority.json"
            mutable_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "source": "vivado_export_simulation_vcs",
                        "generation": "replaced",
                    }
                ),
                encoding="utf-8",
            )
            identity_path = interface_dir / "board_source_identity.json"
            identity_path.write_text(
                json.dumps(
                    {
                        "simulator_compile_authority": {
                            "path": str(mutable_path),
                            "sha256": "8" * 64,
                        }
                    }
                ),
                encoding="utf-8",
            )
            frozen = {
                "schema_version": (
                    "spatialaccagent.frozen_compute_slot_vcs_compile_authority.v1"
                ),
                "status": "pass",
                "source": "frozen_compute_slot_identity_attestation",
            }
            with patch(
                "accagent.framework.stage_repair_execute.frozen_compute_slot_repair_compile_authority",
                return_value=(frozen, []),
            ):
                context = board_integration_repair_context({}, run_dir)

            self.assertEqual(
                context["adaptive_design_inputs"]["vivado_vcs_compile_authority"],
                frozen,
            )
            self.assertFalse(
                any(
                    "compile authority is unavailable" in blocker
                    for blocker in context["blockers"]
                )
            )
            self.assertNotIn(
                hashlib.sha256(mutable_path.read_bytes()).hexdigest(),
                json.dumps(context, sort_keys=True),
            )

    def test_external_fixture_is_bound_from_the_persisted_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "external_simulation_fixture.json"
            )
            report = {
                "schema_version": "spatialaccagent.external_simulation_fixture.v1",
                "status": "pass",
                "compile_authority": {"status": "pass"},
                "blockers": [],
            }

            def materialize(_run_dir: Path, *, timeout: int = 0) -> dict:
                self.assertEqual(_run_dir, run_dir)
                self.assertEqual(timeout, 0)
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps(report), encoding="utf-8")
                return {**report, "cache_reused": True}

            with patch(
                "accagent.framework.stage_repair_execute.materialize_external_simulation_fixture",
                side_effect=materialize,
            ):
                prepared = prepare_external_simulation_fixture_context(run_dir)

        self.assertEqual(prepared["status"], "pass")
        self.assertEqual(prepared["artifact"]["value"], report)
        self.assertEqual(
            prepared["artifact"]["sha256"],
            hashlib.sha256(json.dumps(report).encode("utf-8")).hexdigest(),
        )

    def test_failed_external_fixture_blocks_exact_board_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            context = board_integration_repair_context(
                {},
                Path(temp_dir) / "run",
                {
                    "status": "blocked",
                    "blockers": ["configured provider export is incomplete"],
                },
            )

        self.assertEqual(context["status"], "blocked")
        self.assertIn(
            "external simulation fixture: configured provider export is incomplete",
            context["blockers"],
        )
        self.assertNotIn(
            "external_simulation_fixture",
            context["adaptive_design_inputs"],
        )

    def test_external_fixture_sources_bind_structural_example_top(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            top = root / "fixture_top.sv"
            child = root / "fixture_child.sv"
            top.write_text(
                "module dynamic_example_top(input logic clk); fixture_if bus(); endmodule\n",
                encoding="utf-8",
            )
            child.write_text(
                "interface fixture_if; logic ready; endinterface\n",
                encoding="utf-8",
            )
            sources = [
                {
                    "source_id": f"fixture:{path.stem}",
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "language": "SystemVerilog",
                }
                for path in (top, child)
            ]
            fixture = {
                "providers": [
                    {"filesets": [{"top": "dynamic_example_top", "sources": sources}]}
                ],
                "compile_authority": {"compile_sources": sources},
            }

            bundle, blockers = add_external_fixture_sources_to_repair_bundle(
                {"documents": []},
                {"sha256": "a" * 64, "value": fixture},
            )

        self.assertEqual(blockers, [])
        self.assertEqual(bundle["document_count"], 2)
        top_document = next(
            row for row in bundle["documents"] if row["path"] == str(top)
        )
        self.assertEqual(
            top_document["external_fixture_example_tops"],
            ["dynamic_example_top"],
        )

    def test_agent_patch_cannot_write_verification_or_golden_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "verification" / "semantic_evidence" / "operator_leaf.json"

            report = apply_agent_file_edits(
                self.implementation_output(target, '{"status":"pass"}\n'),
                run_dir,
                out_dir,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertFalse(target.exists())

    def test_agent_validation_rejects_shell_or_untrusted_commands(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = run_dir / "generated" / "chisel"
            generated.mkdir(parents=True)
            output = {
                "requested_validation": [
                    {
                        "purpose": "unsafe command",
                        "argv": ["sh", "-c", "touch forbidden"],
                        "cwd": str(generated),
                    }
                ]
            }

            report = run_agent_requested_validation(
                output,
                run_dir,
                run_dir / "repair_execution",
                10,
            )

            self.assertEqual(report["status"], "fail")
            self.assertEqual(report["results"], [])

    def test_agent_validation_cleans_only_declared_isolated_output_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = run_dir / "generated" / "chisel"
            semantic_root = run_dir / "generated" / "semantic_harness"
            leaf_dir = semantic_root / "stage_leaf"
            single_dir = semantic_root / "single_layer"
            generated.mkdir(parents=True)
            leaf_dir.mkdir(parents=True)
            single_dir.mkdir(parents=True)
            leaf_marker = leaf_dir / "Leaf.sv"
            single_marker = single_dir / "Stale.sv"
            leaf_marker.write_text("module Leaf; endmodule\n", encoding="utf-8")
            single_marker.write_text("module Stale; endmodule\n", encoding="utf-8")
            output = {
                "file_edits": [
                    {
                        "json_content": {
                            "single_layer_harness": {
                                "source_directory": str(single_dir)
                            }
                        }
                    }
                ],
                "requested_validation": [
                    {
                        "purpose": "elaborate connected layer",
                        "argv": [
                            "sbt",
                            "--no-server",
                            "runMain spatialaccagent.semantic_harness.ElaborateSingleLayer",
                        ],
                        "cwd": str(generated),
                    }
                ],
            }

            with patch(
                "accagent.framework.stage_repair_execute.run_local_tool",
                return_value={"status": "pass", "returncode": 0},
            ):
                report = run_agent_requested_validation(
                    output,
                    run_dir,
                    run_dir / "repair_execution",
                    10,
                )

            self.assertEqual(report["status"], "pass")
            self.assertTrue(leaf_marker.is_file())
            self.assertTrue(single_dir.is_dir())
            self.assertFalse(single_marker.exists())
            self.assertEqual(
                report["results"][0]["cleaned_output_roots"],
                [str(single_dir.resolve())],
            )

    def test_connected_requirements_and_leaf_certificate_are_reusable_only_when_complete(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            requirements_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "dut_weight_binding_requirements.json"
            )
            certificate_path = (
                run_dir
                / "verification"
                / "certificates"
                / "operator_leaf_promotion_certificate.json"
            )
            requirements_path.parent.mkdir(parents=True)
            certificate_path.parent.mkdir(parents=True)
            live_source = run_dir / "generated" / "CurrentLeaf.sv"
            live_source.parent.mkdir(parents=True)
            live_source.write_text("module CurrentLeaf; endmodule\n", encoding="utf-8")
            requirements_path.write_text(
                json.dumps(
                    {
                        "connected_weight_stream_contract": {
                            "status": "pass",
                            "contract_sha256": "a" * 64,
                        },
                        "connected_runtime_stream_contract": {
                            "status": "pass",
                            "contract_sha256": "b" * 64,
                        },
                    }
                ),
                encoding="utf-8",
            )
            required_gates = ["leaf"]
            evidence_binding = {
                "schema_version": PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
                "required_gates": required_gates,
                "file_bindings": [
                    {
                        "gate": "leaf",
                        "path": str(live_source),
                        "sha256": sha256_file(live_source),
                        "role": "source_file",
                    }
                ],
                "fingerprints": [],
            }
            evidence_binding["binding_sha256"] = promotion_evidence_binding_fingerprint(
                evidence_binding
            )
            certificate_path.write_text(
                json.dumps(
                    {
                        "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                        "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
                        "gate_execution_scope": "operator_leaf_closure",
                        "status": "pass",
                        "required_gates": [{"name": "leaf", "status": "pass"}],
                        "evidence_contract": evidence_contract_for_level(
                            "operator_leaf_functional"
                        ),
                        "evidence_contract_fingerprint": certificate_contract_fingerprint(
                            "operator_leaf_functional", required_gates
                        ),
                        "tool_environment_contract": tool_environment_contract(
                            {"target_model_oracle": "test"}
                        ),
                        "evidence_binding": evidence_binding,
                        "policy": {
                            "lower_layer_pass_evidence_is_reusable_not_absolute": True
                        },
                    }
                ),
                encoding="utf-8",
            )

            self.assertTrue(connected_binding_requirements_ready(run_dir))
            certificate = reusable_operator_leaf_promotion_certificate(run_dir)
            self.assertEqual(certificate["status"], "pass")
            self.assertEqual(certificate["sha256"], sha256_file(certificate_path))
            live_source.write_text("module CurrentLeaf; wire changed; endmodule\n", encoding="utf-8")
            self.assertEqual(
                reusable_operator_leaf_promotion_certificate(run_dir)["status"],
                "incomplete",
            )

            requirements = json.loads(requirements_path.read_text(encoding="utf-8"))
            requirements["connected_runtime_stream_contract"] = None
            requirements_path.write_text(json.dumps(requirements), encoding="utf-8")
            self.assertFalse(connected_binding_requirements_ready(run_dir))

    def _operator_leaf_continuity_fixture(self, root: Path) -> dict[str, Path]:
        run_dir = root / "run"
        out_dir = run_dir / "repair_execution"
        semantic_dir = run_dir / "verification" / "semantic_testbench"
        certificate_dir = run_dir / "verification" / "certificates"
        snapshot_dir = certificate_dir / "snapshot"
        harness_dir = run_dir / "generated" / "semantic_harness" / "stage_00"
        data_dir = semantic_dir / "stages" / "stage_00"
        reference_dir = run_dir / "verification" / "model_reference"
        memory_dir = run_dir / "generated" / "memory"
        for directory in (
            out_dir,
            semantic_dir,
            snapshot_dir,
            harness_dir,
            data_dir,
            reference_dir,
            memory_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        source = harness_dir / "LeafHarness.sv"
        testbench = data_dir / "semantic_tb.sv"
        input_vector = data_dir / "input.memh"
        expected_output = data_dir / "expected.memh"
        weight_stream = data_dir / "weights.memh"
        weight_tensor = reference_dir / "weight.pt"
        reference_manifest = reference_dir / "reference_manifest.json"
        source.write_text("module LeafHarness; endmodule\n", encoding="ascii")
        testbench.write_text("module semantic_stage_00_tb; endmodule\n", encoding="ascii")
        input_vector.write_text("00000000\n", encoding="ascii")
        expected_output.write_text("00000000\n", encoding="ascii")
        weight_stream.write_text("00000000\n", encoding="ascii")
        weight_tensor.write_bytes(b"real-weight")
        reference_manifest.write_text('{"status":"ready"}\n', encoding="ascii")
        weight_hash = sha256_file(weight_tensor)
        layout_hash = "a" * 64
        stage_contract = {
            "schema_version": "spatialaccagent.operator_semantic_testbench_contract.v1",
            "status": "ready",
            "stage_id": "stage_00",
            "op": "norm",
            "input_vectors": [
                {"path": str(input_vector), "sha256": sha256_file(input_vector)}
            ],
            "expected_output": {
                "path": str(expected_output),
                "sha256": sha256_file(expected_output),
            },
            "real_weight_bindings": [
                {
                    "path": str(weight_tensor),
                    "file_sha256": weight_hash,
                    "sha256": weight_hash,
                }
            ],
            "weight_layout_contract_sha256": layout_hash,
            "weight_layout": {"contract_sha256": layout_hash},
            "real_weight_stream": {
                "path": str(weight_stream),
                "sha256": sha256_file(weight_stream),
            },
            "runtime_constant_stream": None,
            "runtime_constant_contract_sha256": None,
            "dut_harness": {
                "top_module": "LeafHarness",
                "consumed_tensor_hashes": [weight_hash],
                "source_files": [
                    {"path": str(source), "sha256": sha256_file(source)}
                ],
            },
            "testbench": str(testbench),
            "testbench_sha256": sha256_file(testbench),
            "numeric_contract": {"weight_bits": 16},
            "source_reference_manifest": str(reference_manifest),
            "source_reference_sha256": sha256_file(reference_manifest),
        }
        requirements = {
            "accelerator_scope": "transformer_blocks_only",
            "accelerator_weight_catalog_sha256": "b" * 64,
            "canonical_weight_stream_contract": {"status": "pass"},
            "model_semantic_adapter_sha256": "c" * 64,
            "numeric_policy_sha256": "d" * 64,
            "pipeline_plan_sha256": "e" * 64,
            "reference_operator_semantics": {"status": "pass"},
            "semantic_runtime_constant_contract": {"status": "pass"},
            "source_checkpoint_sha256": "f" * 64,
            "source_reference_sha256": sha256_file(reference_manifest),
            "stage_requirements": [
                {
                    "stage_id": "stage_00",
                    "required_tensors": [{"sha256": weight_hash}],
                    "weight_layout_contract_sha256": layout_hash,
                    "runtime_constant_contract_sha256": None,
                }
            ],
            "stream_metadata_contract": {"status": "pass"},
            "transcendental_approximation_contract": {"status": "pass"},
        }
        prior_semantic_manifest = {"status": "ready", "stage_contracts": [stage_contract]}
        snapshot_semantic = snapshot_dir / "semantic_testbench_manifest.json"
        snapshot_requirements = snapshot_dir / "dut_weight_binding_requirements.json"
        snapshot_semantic.write_text(
            json.dumps(prior_semantic_manifest), encoding="utf-8"
        )
        snapshot_requirements.write_text(json.dumps(requirements), encoding="utf-8")

        binding_manifest = memory_dir / "dut_weight_binding_manifest.json"
        semantic_manifest = semantic_dir / "semantic_testbench_manifest.json"
        requirements_path = semantic_dir / "dut_weight_binding_requirements.json"
        binding_manifest.write_text('{"legacy":"leaf-only"}\n', encoding="ascii")
        semantic_manifest.write_text(json.dumps(prior_semantic_manifest), encoding="utf-8")
        requirements_path.write_text(json.dumps(requirements), encoding="utf-8")
        required_gates = ["case_semantic_testbench"]
        evidence_binding = {
            "schema_version": PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
            "required_gates": required_gates,
            "file_bindings": [
                {
                    "gate": "case_semantic_testbench",
                    "path": str(binding_manifest),
                    "sha256": sha256_file(binding_manifest),
                    "role": "input_artifact",
                },
                {
                    "gate": "case_semantic_testbench",
                    "path": str(semantic_manifest),
                    "sha256": sha256_file(semantic_manifest),
                    "role": "input_artifact",
                },
                {
                    "gate": "case_semantic_testbench",
                    "path": str(snapshot_semantic),
                    "sha256": sha256_file(snapshot_semantic),
                    "role": "produced_report",
                    "source_path": str(semantic_manifest),
                },
                {
                    "gate": "case_semantic_testbench",
                    "path": str(snapshot_requirements),
                    "sha256": sha256_file(snapshot_requirements),
                    "role": "produced_report",
                    "source_path": str(requirements_path),
                },
            ],
            "fingerprints": [],
        }
        evidence_binding["binding_sha256"] = promotion_evidence_binding_fingerprint(
            evidence_binding
        )
        certificate = certificate_dir / "operator_leaf_promotion_certificate.json"
        certificate.write_text(
            json.dumps(
                {
                    "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                    "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
                    "gate_execution_scope": "operator_leaf_closure",
                    "status": "pass",
                    "required_gates": [
                        {"name": "case_semantic_testbench", "status": "pass"}
                    ],
                    "evidence_contract": evidence_contract_for_level(
                        "operator_leaf_functional"
                    ),
                    "evidence_contract_fingerprint": certificate_contract_fingerprint(
                        "operator_leaf_functional", required_gates
                    ),
                    "tool_environment_contract": tool_environment_contract(
                        {"target_model_oracle": "test"}
                    ),
                    "evidence_binding": evidence_binding,
                    "policy": {
                        "lower_layer_pass_evidence_is_reusable_not_absolute": True
                    },
                }
            ),
            encoding="utf-8",
        )
        binding_manifest.write_text(
            json.dumps(
                {
                    "status": "pass",
                    "scope_coverage_complete": True,
                    "dut_consumes_bound_weights": True,
                    "default_or_identity_weight_fallback_disabled": True,
                    "stage_harnesses": {
                        "stage_00": {
                            "top_module": "LeafHarness",
                            "consumed_tensor_hashes": [weight_hash],
                            "default_or_identity_weight_fallback_disabled": True,
                            "weight_layout_contract_sha256": layout_hash,
                            "source_files": [
                                {"path": str(source), "sha256": sha256_file(source)}
                            ],
                        }
                    },
                    "single_layer_harness": {"top_module": "ConnectedHarness"},
                }
            ),
            encoding="utf-8",
        )
        current_contract = copy.deepcopy(stage_contract)
        current_contract["dut_harness"]["source_files"] = []
        current_contract["testbench"] = None
        current_contract["testbench_sha256"] = None
        semantic_manifest.write_text(
            json.dumps(
                {
                    "status": "incomplete",
                    "requested_verification_scope": "single_layer_closure",
                    "stage_contracts": [current_contract],
                }
            ),
            encoding="utf-8",
        )
        return {
            "certificate": certificate,
            "out_dir": out_dir,
            "run_dir": run_dir,
            "source": source,
        }

    def test_operator_leaf_certificate_continuity_reuses_only_unchanged_leaf_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = self._operator_leaf_continuity_fixture(Path(temp_dir))
            result = reconcile_operator_leaf_certificate_scope_continuity(
                paths["run_dir"], paths["out_dir"]
            )

            self.assertEqual(result["status"], "not_required")
            certificate = json.loads(paths["certificate"].read_text(encoding="utf-8"))
            self.assertEqual(
                certificate_contract_errors(
                    certificate,
                    "operator_leaf_functional",
                    ["case_semantic_testbench"],
                ),
                [],
            )
            self.assertEqual(
                reusable_operator_leaf_promotion_certificate(paths["run_dir"])[
                    "status"
                ],
                "pass",
            )
            self.assertNotIn("continuity_proof", result)

    def test_operator_leaf_certificate_continuity_rejects_changed_leaf_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = self._operator_leaf_continuity_fixture(Path(temp_dir))
            original_certificate_hash = sha256_file(paths["certificate"])
            paths["source"].write_text(
                "module LeafHarness; wire changed; endmodule\n", encoding="ascii"
            )
            result = reconcile_operator_leaf_certificate_scope_continuity(
                paths["run_dir"], paths["out_dir"]
            )

            self.assertEqual(result["status"], "incomplete")
            self.assertTrue(
                any("semantic_harness_source" in error for error in result["continuity_errors"])
            )
            self.assertEqual(sha256_file(paths["certificate"]), original_certificate_hash)

    def test_operator_leaf_certificate_continuity_reuses_after_higher_scope_vector_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            paths = self._operator_leaf_continuity_fixture(Path(temp_dir))
            board_vector = (
                paths["run_dir"]
                / "verification"
                / "semantic_testbench"
                / "board"
                / "expected.memh"
            )
            board_vector.parent.mkdir(parents=True)
            board_vector.write_text("00000000\n", encoding="ascii")
            certificate = json.loads(paths["certificate"].read_text(encoding="utf-8"))
            binding = certificate["evidence_binding"]
            binding["file_bindings"].append(
                {
                    "gate": "case_semantic_testbench",
                    "path": str(board_vector),
                    "sha256": sha256_file(board_vector),
                    "role": "input_artifact",
                }
            )
            binding["fingerprints"].append(
                {
                    "name": "tensor_sha256",
                    "value": "a" * 64,
                    "source": "test#board_expected",
                    "kind": "declared_nonbyte_content_identity",
                    "artifact_path": str(board_vector),
                }
            )
            binding["binding_sha256"] = promotion_evidence_binding_fingerprint(binding)
            paths["certificate"].write_text(json.dumps(certificate), encoding="utf-8")
            board_vector.write_text("11111111\n", encoding="ascii")

            result = reconcile_operator_leaf_certificate_scope_continuity(
                paths["run_dir"], paths["out_dir"]
            )

            self.assertEqual(result["status"], "pass")
            self.assertEqual(
                result["removed_higher_scope_semantic_artifact_gates"],
                ["case_semantic_testbench"],
            )
            certificate = json.loads(paths["certificate"].read_text(encoding="utf-8"))
            self.assertEqual(
                certificate_contract_errors(
                    certificate,
                    "operator_leaf_functional",
                    ["case_semantic_testbench"],
                ),
                [],
            )

    def test_repair_loop_does_not_reannounce_persistent_patch_without_fresh_agent_record(self) -> None:
        with TemporaryDirectory() as temp_dir:
            patch_path = Path(temp_dir) / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "files": [
                            {
                                "path": "/generated/Harness.scala",
                                "before_sha256": "a" * 64,
                                "after_sha256": "b" * 64,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            disposition = repair_loop_disposition(
                {
                    "status": "incomplete",
                    "errors": ["unchanged patch replay made no progress"],
                    "step_results": [
                        {
                            "result": {
                                "status": "fail",
                                "summary": "unchanged patch replay made no progress",
                                "agent_patch_application": str(patch_path),
                                "llm_record": None,
                            }
                        }
                    ],
                }
            )

            self.assertEqual(disposition["status"], "blocked")
            self.assertEqual(disposition["applied_files"], [])

    def test_zero_return_code_with_jvm_fatal_output_is_failure(self) -> None:
        result = run_local_tool(
            ["bash", "-c", "printf 'java.lang.OutOfMemoryError: Java heap space\\n' >&2"],
            Path.cwd(),
            os.environ.copy(),
            10,
        )

        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["fatal_output_pattern"], "java.lang.OutOfMemoryError")

    def test_sbt_heap_override_is_explicit_and_bounded(self) -> None:
        with patch.dict(os.environ, {"SPATIALACC_SBT_HEAP_MB": "6144"}):
            self.assertEqual(configured_sbt_heap_mb(), 6144)
        with patch.dict(os.environ, {"SPATIALACC_SBT_HEAP_MB": "512"}):
            with self.assertRaises(ValueError):
                configured_sbt_heap_mb()

    def test_interrupted_applied_patch_resumes_validation_without_another_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            target = run_dir / "generated" / "chisel" / "Attention.scala"
            target.parent.mkdir(parents=True)
            target.write_text("instrumented\n", encoding="utf-8")
            validation_path = out_dir / "agent_requested_validation.json"
            validation_path.write_text('{"status":"pass"}\n', encoding="utf-8")
            os.utime(validation_path, (1, 1))
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "files": [
                            {
                                "path": str(target),
                                "after_sha256": hashlib.sha256(b"instrumented\n").hexdigest(),
                            }
                        ],
                        "requested_validation": [
                            {
                                "purpose": "resume exact applied patch",
                                "argv": ["sbt", "--no-server", "Compile/compile"],
                                "cwd": str(run_dir / "generated" / "chisel"),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stale_resume = out_dir / "agent_requested_validation_resource_resume.json"
            stale_resume.write_text('{"status":"pass"}\n', encoding="utf-8")

            with patch(
                "accagent.framework.stage_repair_execute.run_agent_requested_validation"
            ) as validation:
                validation.return_value = {
                    "status": "pass",
                    "path": str(stale_resume),
                    "results": [],
                    "blockers": [],
                }
                report = resume_prior_resource_failed_validation(run_dir, out_dir, 120)

            self.assertTrue(validation.called)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                report["resource_failure_pattern"],
                "interrupted_before_validation_report",
            )
            self.assertEqual(
                report["source_patch_application_sha256"],
                hashlib.sha256(patch_path.read_bytes()).hexdigest(),
            )

    def test_interrupted_board_patch_with_empty_requested_validation_resumes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            target.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            target.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "files": [
                            {
                                "path": str(target),
                                "after_sha256": hashlib.sha256(
                                    target.read_bytes()
                                ).hexdigest(),
                            }
                        ],
                        "requested_validation": [],
                    }
                ),
                encoding="utf-8",
            )

            report = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["requests"], 0)
            self.assertEqual(
                report["resource_failure_pattern"],
                "interrupted_before_validation_report",
            )

    def test_board_patch_ignores_optional_agent_gate_suggestions(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = run_dir / "generated" / "board_integration" / "BoardTop.sv"
            target.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            target.write_text("module BoardTop; endmodule\n", encoding="utf-8")
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "action": {
                    "repair_kind": "exact_board_integration_harness",
                },
            }
            (out_dir / "agent_patch_application.json").write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "repair_checkpoint": repair_step_checkpoint(step),
                        "files": [
                            {
                                "path": str(target),
                                "after_sha256": hashlib.sha256(
                                    target.read_bytes()
                                ).hexdigest(),
                            }
                        ],
                        "requested_validation": [
                            {
                                "cwd": str(run_dir),
                                "argv": ["case_vcs_functional_sim"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "agent_requested_validation.json").write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "blockers": ["optional Agent gate suggestion is not a command"],
                    }
                ),
                encoding="utf-8",
            )

            with patch(
                "accagent.framework.stage_repair_execute.run_agent_requested_validation",
                return_value={"status": "pass", "requests": 0, "blockers": []},
            ) as validation:
                report = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    0,
                    step=step,
                )

            self.assertEqual(report["status"], "pass")
            self.assertIn("mandatory preflight", report["summary"])
            self.assertEqual(
                validation.call_args.args[0], {"requested_validation": []}
            )

    def test_current_step_patch_reuses_passing_validation_without_another_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            target = run_dir / "generated" / "chisel" / "Attention.scala"
            target.parent.mkdir(parents=True)
            target.write_text("instrumented\n", encoding="utf-8")
            step = {
                "id": "repair_step_00",
                "scope": "verification_capability_repair",
                "action": {
                    "repair_kind": "localized_semantic_dut_repair",
                    "minimal_repair_context": {
                        "trace_record": {
                            "stage_id": "stage_01_self_attention",
                            "module": "AttentionGQA",
                            "boundary_id": "attention_out",
                            "status": "fail",
                        }
                    },
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "repair_checkpoint": repair_step_checkpoint(step),
                        "files": [
                            {
                                "path": str(target),
                                "after_sha256": hashlib.sha256(b"instrumented\n").hexdigest(),
                            }
                        ],
                        "requested_validation": [],
                    }
                ),
                encoding="utf-8",
            )
            validation_path = out_dir / "agent_requested_validation.json"
            validation_path.write_text(
                json.dumps({"status": "pass", "results": [], "blockers": []}),
                encoding="utf-8",
            )

            with patch(
                "accagent.framework.stage_repair_execute.run_agent_requested_validation"
            ) as validation:
                report = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    120,
                    step=step,
                )

            validation.assert_not_called()
            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["applied_patch_checkpoint_reused"])
            self.assertEqual(
                report["repair_checkpoint"]["stage_id"],
                "stage_01_self_attention",
            )

    def test_routed_stage2_patch_resumes_only_missing_layer_elaboration(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            generated_template = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Residual.scala"
            )
            persistent_template = run_dir / "persistent" / "Residual.scala"
            generated_template.parent.mkdir(parents=True)
            persistent_template.parent.mkdir(parents=True)
            generated_template.write_text("repaired\n", encoding="utf-8")
            persistent_template.write_text("repaired\n", encoding="utf-8")
            harness_root = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "semantic_harness"
            )
            harness_root.mkdir(parents=True)
            (harness_root / "Leaf.scala").write_text(
                "object ElaborateSemanticHarnesses extends App { emitSystemVerilog() }\n",
                encoding="utf-8",
            )
            (harness_root / "Layer.scala").write_text(
                "object ElaborateSingleLayerClosure extends App { emitSystemVerilog() }\n",
                encoding="utf-8",
            )
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "debug_layer": "single_transformer_layer_kernel",
                "action": {
                    "repair_kind": "case_single_layer_functional",
                    "repair_gate": "case_single_layer_functional",
                    "debug_layer": "single_transformer_layer_kernel",
                    "violated_contract": (
                        "all_spatial_operators_must_form_a_token_level_pipeline"
                    ),
                },
            }
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "repair_checkpoint": {
                            "schema_version": (
                                "spatialaccagent.repair_step_checkpoint.v1"
                            ),
                            "fingerprint_sha256": "9" * 64,
                            "step_id": "repair_step.00",
                            "scope": "verification_capability_repair",
                            "repair_kind": "localized_semantic_dut_repair",
                            "repair_phase": "functional_repair",
                            "stage_id": "stage_02_residual_add_1",
                            "module": "pipeline_candidate_set",
                            "violated_contract": (
                                "all_spatial_operators_must_form_a_token_level_pipeline"
                            ),
                        },
                        "policy": {
                            "semantic_selected_template_repair_approved": True,
                            "template_instrumentation_blocks_are_mechanically_non_functional": False,
                        },
                        "files": [
                            {
                                "path": str(generated_template),
                                "after_sha256": hashlib.sha256(b"repaired\n").hexdigest(),
                            },
                            {
                                "path": str(persistent_template),
                                "after_sha256": hashlib.sha256(b"repaired\n").hexdigest(),
                            },
                        ],
                        "requested_validation": [
                            {
                                "purpose": "agent compile",
                                "argv": ["sbt", "--no-server", "Compile/compile"],
                                "cwd": str(run_dir / "generated" / "chisel"),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            validation_path = out_dir / "agent_requested_validation.json"
            validation_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "results": [
                            {
                                "status": "pass",
                                "argv": [
                                    "sbt",
                                    "--no-server",
                                    "Compile/compile",
                                ],
                            }
                        ],
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            resume_path = out_dir / "agent_requested_validation_resource_resume.json"

            with patch(
                "accagent.framework.stage_repair_execute.run_agent_requested_validation"
            ) as validation:
                validation.return_value = {
                    "status": "pass",
                    "path": str(resume_path),
                    "results": [
                        {
                            "status": "pass",
                            "argv": [
                                "sbt",
                                "--no-server",
                                "runMain spatialaccagent.semantic_harness.ElaborateSingleLayerClosure",
                            ],
                        }
                    ],
                    "blockers": [],
                }
                report = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    120,
                    step=step,
                )

            validation.assert_called_once()
            requested = validation.call_args.args[0]["requested_validation"]
            self.assertEqual(len(requested), 1)
            self.assertEqual(
                requested[0]["argv"][-1],
                "runMain spatialaccagent.semantic_harness.ElaborateSingleLayerClosure",
            )
            self.assertEqual(report["status"], "pass")
            self.assertEqual(
                report["resource_failure_pattern"],
                "mandatory_template_elaboration_contract_upgrade",
            )

    def test_framework_finalized_manifest_reuses_current_step_validation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, step, *_ = self.finalized_manifest_resume_fixture(
                Path(temp_dir)
            )

            with patch(
                "accagent.framework.stage_repair_execute.run_agent_requested_validation"
            ) as validation:
                report = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    120,
                    step=step,
                )

            validation.assert_not_called()
            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["applied_patch_checkpoint_reused"])

    def test_repeated_finalization_preserves_hash_verified_agent_provenance(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir, out_dir, _, _, _, _, _ = self.finalized_manifest_resume_fixture(
                Path(temp_dir)
            )

            first = finalize_dut_weight_binding_manifest(run_dir, out_dir)
            second = finalize_dut_weight_binding_manifest(run_dir, out_dir)

            for field in (
                "source_patch_application",
                "source_patch_application_sha256",
                "source_agent_manifest",
                "source_agent_manifest_sha256",
            ):
                self.assertTrue(first.get(field), field)
                self.assertEqual(second.get(field), first.get(field), field)

    def test_board_only_incomplete_finalization_reuses_lower_layer_checkpoint(self) -> None:
        with TemporaryDirectory() as temp_dir:
            (
                run_dir,
                out_dir,
                step,
                manifest_path,
                requirements_path,
                validation_path,
                materialization_path,
            ) = self.finalized_manifest_resume_fixture(Path(temp_dir))
            step["action"].update(
                {
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "repair_kind": "exact_board_integration_harness",
                }
            )
            patch_path = out_dir / "agent_patch_application.json"
            patch_report = json.loads(patch_path.read_text(encoding="utf-8"))
            patch_report["repair_checkpoint"] = repair_step_checkpoint(step)
            patch_path.write_text(json.dumps(patch_report), encoding="utf-8")
            agent_manifest_sha = patch_report["files"][0]["after_sha256"]
            requirements_path.write_text(
                json.dumps({"stage_requirements": [{"stage_id": "stage_dynamic"}]}),
                encoding="utf-8",
            )
            blockers = ["board_preflight: ordered compile plan is incomplete"]
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "status": "incomplete",
                    "stage_harnesses": {
                        "stage_dynamic": {"top_module": "LeafHarness"}
                    },
                    "materialization_blockers": blockers,
                }
            )
            manifest["materialization"].update(
                {
                    "requirements_sha256": hashlib.sha256(
                        requirements_path.read_bytes()
                    ).hexdigest(),
                    "verification_scope": "board_axi_ddr_closure",
                }
            )
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            materialization = {
                "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                "status": "incomplete",
                "manifest": str(manifest_path),
                "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "stage_harness_count": 1,
                "single_layer_harness_materialized": True,
                "board_integration_harness_materialized": False,
                "blockers": blockers,
                "source_patch_application": str(patch_path),
                "source_patch_application_sha256": hashlib.sha256(
                    patch_path.read_bytes()
                ).hexdigest(),
                "source_agent_manifest": str(manifest_path),
                "source_agent_manifest_sha256": agent_manifest_sha,
            }
            materialization_path.write_text(
                json.dumps(materialization), encoding="utf-8"
            )
            os.utime(patch_path, ns=(1_000_000_000, 1_000_000_000))
            os.utime(validation_path, ns=(2_000_000_000, 2_000_000_000))
            os.utime(materialization_path, ns=(3_000_000_000, 3_000_000_000))

            report = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
            )
            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["applied_patch_checkpoint_reused"])

            manifest["materialization_blockers"] = [
                "single_layer: lower-layer contract changed"
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            materialization.update(
                {
                    "manifest_sha256": hashlib.sha256(
                        manifest_path.read_bytes()
                    ).hexdigest(),
                    "blockers": ["single_layer: lower-layer contract changed"],
                }
            )
            materialization_path.write_text(
                json.dumps(materialization), encoding="utf-8"
            )
            os.utime(materialization_path, ns=(4_000_000_000, 4_000_000_000))
            rejected = resume_prior_resource_failed_validation(
                run_dir,
                out_dir,
                0,
                step=step,
            )
            self.assertEqual(rejected["status"], "blocked")

    def test_framework_finalized_manifest_attestation_fails_closed(self) -> None:
        cases = (
            "schema",
            "status",
            "blockers",
            "manifest_path",
            "manifest_sha",
            "report_time",
            "validation_time",
            "materialization_source",
            "requirements_missing",
            "requirements_sha",
            "verification_scope",
            "single_layer_harness",
            "provenance",
            "other_patch_file",
        )
        for case in cases:
            with self.subTest(case=case), TemporaryDirectory() as temp_dir:
                (
                    run_dir,
                    out_dir,
                    step,
                    manifest_path,
                    requirements_path,
                    validation_path,
                    materialization_path,
                ) = self.finalized_manifest_resume_fixture(Path(temp_dir))
                report = json.loads(materialization_path.read_text(encoding="utf-8"))
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if case == "schema":
                    report["schema_version"] = "spatialaccagent.dut_weight_binding_materialization.v0"
                elif case == "status":
                    report["status"] = "incomplete"
                elif case == "blockers":
                    report["blockers"] = ["not trusted"]
                elif case == "manifest_path":
                    report["manifest"] = str(run_dir / "elsewhere.json")
                elif case == "manifest_sha":
                    report["manifest_sha256"] = "0" * 64
                elif case == "materialization_source":
                    manifest["materialization"]["source"] = "agent_only"
                elif case == "requirements_missing":
                    requirements_path.unlink()
                elif case == "requirements_sha":
                    manifest["materialization"]["requirements_sha256"] = "0" * 64
                elif case == "verification_scope":
                    manifest["materialization"]["verification_scope"] = "operator_leaf_closure"
                elif case == "single_layer_harness":
                    report["single_layer_harness_materialized"] = False
                elif case == "provenance":
                    report.update(
                        {
                            "source_patch_application": str(
                                out_dir / "agent_patch_application.json"
                            ),
                            "source_patch_application_sha256": "0" * 64,
                            "source_agent_manifest": str(manifest_path),
                            "source_agent_manifest_sha256": "1" * 64,
                        }
                    )
                elif case == "other_patch_file":
                    other_path = run_dir / "generated" / "chisel" / "Connected.scala"
                    other_path.parent.mkdir(parents=True)
                    other_path.write_text("changed\n", encoding="utf-8")
                    patch_path = out_dir / "agent_patch_application.json"
                    patch_report = json.loads(patch_path.read_text(encoding="utf-8"))
                    patch_report["files"].append(
                        {
                            "path": str(other_path),
                            "after_sha256": hashlib.sha256(b"agent version\n").hexdigest(),
                        }
                    )
                    patch_path.write_text(json.dumps(patch_report), encoding="utf-8")
                    os.utime(patch_path, ns=(1_000_000_000, 1_000_000_000))
                if case in {
                    "materialization_source",
                    "requirements_sha",
                    "verification_scope",
                }:
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    report["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                materialization_path.write_text(json.dumps(report), encoding="utf-8")
                os.utime(materialization_path, ns=(3_000_000_000, 3_000_000_000))
                if case == "report_time":
                    os.utime(materialization_path, ns=(1_500_000_000, 1_500_000_000))
                elif case == "validation_time":
                    os.utime(validation_path, ns=(500_000_000, 500_000_000))

                result = resume_prior_resource_failed_validation(
                    run_dir,
                    out_dir,
                    120,
                    step=step,
                )

                self.assertEqual(result["status"], "blocked", result)
                self.assertTrue(result["blockers"], result)

    def test_instrumentation_accepts_fresh_new_internal_boundary_without_stage_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "stage_01_self_attention.json"
            old_trace = {
                "evidence_type": "semantic_internal_boundary_trace",
                "stage_id": "stage_01_self_attention",
                "boundary_id": "attention_out",
                "module": "AttentionGQA",
                "beat_index": 112,
                "cycle": 100,
                "observed_value": {"packed_literal": "xxxx"},
                "status": "fail",
            }
            report_path.write_text(
                json.dumps({"status": "fail", "internal_boundary_trace": [old_trace]}),
                encoding="utf-8",
            )
            before = semantic_trace_report_snapshot(report_path)
            new_trace = {
                **old_trace,
                "boundary_id": "softmax_to_context",
                "module": "Softmax",
                "cycle": 90,
                "observed_value": {"packed_literal": "3c00"},
                "status": "diagnostic_seed",
            }
            report_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "internal_boundary_trace": [old_trace, new_trace],
                    }
                ),
                encoding="utf-8",
            )

            evidence = localized_instrumentation_probe_evidence(
                report_path,
                before,
                "stage_01_self_attention",
            )

            self.assertEqual(evidence["status"], "pass")
            self.assertEqual(evidence["new_internal_trace_count"], 1)
            self.assertEqual(evidence["new_internal_modules"], ["Softmax"])

    def test_explicit_bounded_template_approval_allows_exact_generated_copy_repair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Norm.scala"
            )
            target.parent.mkdir(parents=True)
            old = "object NormOld\n"
            target.write_text(old, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace",
                        "expected_sha256": hashlib.sha256(old.encode("utf-8")).hexdigest(),
                        "content": "object NormFixed\n",
                        "rationale": "implement existing weight contract",
                    }
                ],
                "requested_validation": [],
            }

            with patch.dict(
                "os.environ",
                {"SPATIALACC_APPROVE_BOUNDED_TEMPLATE_REPAIR": "1"},
            ):
                report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "pass")
            self.assertEqual(target.read_text(encoding="utf-8"), "object NormFixed\n")

    def test_semantic_template_approval_includes_bounded_exact_template_edits(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Attention.scala"
            )
            target.parent.mkdir(parents=True)
            old = "object AttentionShell\n"
            target.write_text(old, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace",
                        "expected_sha256": hashlib.sha256(old.encode("utf-8")).hexdigest(),
                        "content": "object AttentionSemantic\n",
                        "rationale": "repair selected operator semantics",
                    }
                ],
                "requested_validation": [],
            }

            with patch.dict(
                "os.environ",
                {
                    "SPATIALACC_APPROVE_BOUNDED_TEMPLATE_REPAIR": "0",
                    "SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1",
                },
            ):
                report = apply_agent_file_edits(output, run_dir, out_dir)

            self.assertEqual(report["status"], "pass")
            self.assertTrue(report["policy"]["semantic_selected_template_repair_approved"])
            self.assertEqual(target.read_text(encoding="utf-8"), "object AttentionSemantic\n")

    def test_capability_step_keeps_templates_read_only_after_semantic_baseline(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Attention.scala"
            )
            target.parent.mkdir(parents=True)
            old = "object AttentionBaseline\n"
            target.write_text(old, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace",
                        "expected_sha256": hashlib.sha256(old.encode("utf-8")).hexdigest(),
                        "content": "object AttentionChanged\n",
                        "rationale": "must wait for real localized failure",
                    }
                ],
                "requested_validation": [],
            }

            with patch.dict("os.environ", {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allow_template_repair=False,
                )

            self.assertEqual(report["status"], "blocked")
            self.assertEqual(target.read_text(encoding="utf-8"), old)

    def test_semantic_phase_requires_byte_identical_persistent_and_generated_template_edits(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Norm.scala"
            )
            target.parent.mkdir(parents=True)
            old = "object NormOld\n"
            target.write_text(old, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace",
                        "expected_sha256": hashlib.sha256(old.encode("utf-8")).hexdigest(),
                        "content": "object NormFixed\n",
                        "rationale": "phase-local semantic repair",
                    }
                ],
                "requested_validation": [],
            }

            with patch.dict("os.environ", {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allowed_exact_files={target.resolve()},
                    required_template_pairs={"Norm.scala"},
                    report_name="phase_patch.json",
                )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("both persistent/generated copies", " ".join(report["blockers"]))
            self.assertEqual(target.read_text(encoding="utf-8"), old)

    def test_template_instrumentation_pair_allows_only_marked_printf_observation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_dir = repo_root / "run"
            out_dir = run_dir / "repair_execution"
            persistent = repo_root / "accagent" / "framework" / "templates" / "operator_chisel" / "Attention.scala"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Attention.scala"
            )
            persistent.parent.mkdir(parents=True)
            generated.parent.mkdir(parents=True)
            old = "class Attention {\n  val observed = io.out.bits\n}\n"
            trace = (
                "class Attention {\n"
                "  // SPATIALACC_TEMPLATE_TRACE_BEGIN output-boundary\n"
                "  when (io.out.valid && io.out.ready) {\n"
                "    printf(p\"SPATIALACC_INTERNAL_TRACE stage=stage_01 boundary=attention_out "
                "module=Attention cycle=0 beat=112 valid=1 ready=1 data=${io.out.bits}\\n\")\n"
                "  }\n"
                "  // SPATIALACC_TEMPLATE_TRACE_END output-boundary\n"
                "  val observed = io.out.bits\n"
                "}\n"
            )
            for path in (persistent, generated):
                path.write_text(old, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(path),
                        "operation": "replace",
                        "expected_sha256": hashlib.sha256(old.encode("utf-8")).hexdigest(),
                        "content": trace,
                    }
                    for path in (persistent, generated)
                ],
                "requested_validation": [],
            }

            with patch("accagent.framework.stage_repair_execute.Path.cwd", return_value=repo_root):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allowed_exact_files={persistent.resolve(), generated.resolve()},
                    required_template_pairs={"Attention.scala"},
                    instrumentation_only_template_pairs={"Attention.scala"},
                    allow_template_repair=True,
                )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(persistent.read_text(encoding="utf-8"), trace)
            self.assertEqual(generated.read_text(encoding="utf-8"), trace)

    def test_template_instrumentation_rejects_functional_or_state_change_before_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            run_dir = repo_root / "run"
            out_dir = run_dir / "repair_execution"
            persistent = repo_root / "accagent" / "framework" / "templates" / "operator_chisel" / "Attention.scala"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Attention.scala"
            )
            persistent.parent.mkdir(parents=True)
            generated.parent.mkdir(parents=True)
            old = "class Attention {\n  io.out.bits := io.in.bits\n}\n"
            changed = (
                "class Attention {\n"
                "  // SPATIALACC_TEMPLATE_TRACE_BEGIN bad-state\n"
                "  val debugCounter = RegInit(0.U)\n"
                "  printf(p\"SPATIALACC_INTERNAL_TRACE stage=s boundary=b module=Attention "
                "cycle=0 beat=0 valid=1 ready=1 data=0\\n\")\n"
                "  // SPATIALACC_TEMPLATE_TRACE_END bad-state\n"
                "  io.out.bits := 0.U\n"
                "}\n"
            )
            for path in (persistent, generated):
                path.write_text(old, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(path),
                        "operation": "replace",
                        "expected_sha256": hashlib.sha256(old.encode("utf-8")).hexdigest(),
                        "content": changed,
                    }
                    for path in (persistent, generated)
                ],
                "requested_validation": [],
            }

            with patch("accagent.framework.stage_repair_execute.Path.cwd", return_value=repo_root):
                report = apply_agent_file_edits(
                    output,
                    run_dir,
                    out_dir,
                    allowed_exact_files={persistent.resolve(), generated.resolve()},
                    required_template_pairs={"Attention.scala"},
                    instrumentation_only_template_pairs={"Attention.scala"},
                    allow_template_repair=True,
                )

            self.assertEqual(report["status"], "blocked")
            self.assertIn("outside marked instrumentation blocks changed", " ".join(report["blockers"]))
            self.assertIn("functional/state-changing token", " ".join(report["blockers"]))
            self.assertEqual(persistent.read_text(encoding="utf-8"), old)
            self.assertEqual(generated.read_text(encoding="utf-8"), old)

    def test_semantic_phase_bundle_removes_unrelated_large_stage_documents(self) -> None:
        source_bundle = {
            "documents": [
                {"path": "pipeline_plan.json", "content": "x" * 1000},
                {
                    "path": "dut_weight_binding_requirements.json#operator_leaf_projection",
                    "content": json.dumps(
                        {
                            "reference_operator_semantics": {
                                "semantic_adapter": {"path": "/tmp/custom_family_adapter.json"},
                                "model_implementation": {"source_path": "/tmp/modeling_custom.py"},
                            }
                        }
                    ),
                },
                {"path": "/tmp/custom_family_adapter.json", "content": "adapter"},
                {"path": "/tmp/modeling_custom.py", "content": "implementation"},
                {"path": "generated/templates/Norm.scala", "content": "norm"},
                {"path": "generated/templates/Attention.scala", "content": "attention"},
                {"path": "generated/QuantCommon/FP32.scala", "content": "fp"},
            ],
            "trusted_numeric_support": {"status": "pass"},
            "editable_contract": {
                "approved_bounded_template_repair_exact_files": [
                    "generated/templates/Norm.scala",
                    "generated/templates/Attention.scala",
                ],
                "read_only_template_sources": [],
            },
        }

        phase_bundle = semantic_phase_source_bundle(source_bundle, SEMANTIC_TEMPLATE_REPAIR_PHASES[0])
        paths = {row["path"] for row in phase_bundle["documents"]}

        self.assertIn("generated/templates/Norm.scala", paths)
        self.assertIn("dut_weight_binding_requirements.json#operator_leaf_projection", paths)
        self.assertIn("generated/QuantCommon/FP32.scala", paths)
        self.assertIn("/tmp/custom_family_adapter.json", paths)
        self.assertIn("/tmp/modeling_custom.py", paths)
        self.assertNotIn("generated/templates/Attention.scala", paths)
        self.assertNotIn("pipeline_plan.json", paths)

    def test_semantic_phase_bundle_keeps_dependencies_read_only(self) -> None:
        source_bundle = {
            "documents": [
                {"path": "generated/templates/Attention.scala", "content": "attention"},
                {"path": "framework/templates/Attention.scala", "content": "attention"},
                {"path": "generated/templates/Linear.scala", "content": "linear"},
                {"path": "framework/templates/Linear.scala", "content": "linear"},
                {"path": "generated/templates/Softmax.scala", "content": "softmax"},
                {"path": "framework/templates/Softmax.scala", "content": "softmax"},
                {"path": "generated/templates/FFN.scala", "content": "ffn"},
            ],
            "trusted_numeric_support": {"status": "pass"},
            "editable_contract": {
                "approved_bounded_template_repair_exact_files": [
                    "generated/templates/Attention.scala",
                    "framework/templates/Attention.scala",
                    "generated/templates/Linear.scala",
                    "framework/templates/Linear.scala",
                    "generated/templates/Softmax.scala",
                    "framework/templates/Softmax.scala",
                ],
                "read_only_template_sources": [],
            },
        }

        phase = SEMANTIC_TEMPLATE_REPAIR_PHASES[2]
        phase_bundle = semantic_phase_source_bundle(source_bundle, phase)
        paths = {row["path"] for row in phase_bundle["documents"]}
        approved = set(
            phase_bundle["editable_contract"]["approved_bounded_template_repair_exact_files"]
        )

        self.assertIn("generated/templates/Linear.scala", paths)
        self.assertIn("generated/templates/Softmax.scala", paths)
        self.assertNotIn("generated/templates/FFN.scala", paths)
        self.assertEqual(
            phase_bundle["read_only_dependency_template_files"],
            ["Linear.scala", "Softmax.scala"],
        )
        self.assertIn("generated/templates/Attention.scala", approved)
        self.assertNotIn("generated/templates/Linear.scala", approved)
        self.assertNotIn("generated/templates/Softmax.scala", approved)

    def test_declared_template_pairs_are_rehydrated_from_live_complete_sources(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            persistent = root / "framework" / "templates" / "Norm.scala"
            generated = root / "run" / "generated" / "templates" / "Norm.scala"
            persistent.parent.mkdir(parents=True)
            generated.parent.mkdir(parents=True)
            persistent_content = "object PersistentNorm { val source = 1 }\n"
            generated_content = "object GeneratedNorm { val source = 2 }\n"
            persistent.write_text(persistent_content, encoding="utf-8")
            generated.write_text(generated_content, encoding="utf-8")
            source_bundle = {
                "documents": [
                    {
                        "path": str(persistent),
                        "content": persistent_content[:8],
                        "truncated": True,
                        "sha256": "0" * 64,
                    },
                    {"path": "unrelated/old_board.sv", "content": "x" * 900_000},
                ],
                "editable_contract": {
                    "read_only_template_sources": [str(persistent)],
                    "approved_bounded_template_repair_exact_files": [str(generated)],
                },
            }

            documents = materialize_declared_template_documents(
                source_bundle,
                {"Norm.scala"},
            )
            norm_rows = [
                row for row in documents if Path(str(row.get("path"))).name == "Norm.scala"
            ]

            self.assertEqual(len(norm_rows), 2)
            self.assertEqual(
                {row["content"] for row in norm_rows},
                {persistent_content, generated_content},
            )
            self.assertTrue(all(row.get("truncated") is False for row in norm_rows))
            self.assertTrue(
                all(
                    row.get("sha256")
                    == hashlib.sha256(row["content"].encode("utf-8")).hexdigest()
                    for row in norm_rows
                )
            )

            phase = {
                "id": "test_pair",
                "template_files": ["Norm.scala"],
                "dependency_template_files": [],
                "required_template_files": ["Norm.scala"],
                "required_bundle_paths": [],
            }
            phase_bundle = semantic_phase_source_bundle(source_bundle, phase)
            self.assertEqual(semantic_phase_prerequisite_errors(phase_bundle, phase), [])

    def test_semantic_phase_rejects_a_missing_live_template_pair_member(self) -> None:
        with TemporaryDirectory() as temp_dir:
            persistent = Path(temp_dir) / "framework" / "templates" / "Norm.scala"
            persistent.parent.mkdir(parents=True)
            persistent.write_text("object Norm {}\n", encoding="utf-8")
            missing_generated = Path(temp_dir) / "generated" / "templates" / "Norm.scala"
            source_bundle = {
                "documents": [],
                "editable_contract": {
                    "read_only_template_sources": [str(persistent)],
                    "approved_bounded_template_repair_exact_files": [
                        str(missing_generated)
                    ],
                },
            }
            phase = {
                "id": "test_missing_pair",
                "template_files": ["Norm.scala"],
                "dependency_template_files": [],
                "required_template_files": ["Norm.scala"],
                "required_bundle_paths": [],
            }

            errors = semantic_phase_prerequisite_errors(
                semantic_phase_source_bundle(source_bundle, phase),
                phase,
            )

            self.assertTrue(any("persistent/generated template pair Norm.scala" in row for row in errors))

    def test_harness_source_directory_is_discovered_after_elaboration(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            stage_dir = run_dir / "generated" / "semantic_harness" / "stage_generic"
            stage_dir.mkdir(parents=True)
            (stage_dir / "Dependency.sv").write_text("module Dependency; endmodule\n", encoding="utf-8")
            (stage_dir / "Harness.sv").write_text(
                "module Harness; Dependency dut(); endmodule\n",
                encoding="utf-8",
            )

            rows, source, blockers = normalize_harness_sources(
                {"source_directory": str(stage_dir)},
                run_dir,
            )

            self.assertEqual(blockers, [])
            self.assertEqual(len(rows), 2)
            self.assertIn("module Harness", source)
            self.assertTrue(all(row["sha256"] for row in rows))

    def test_harness_source_directory_rejects_duplicate_modules_within_stage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            stage_dir = run_dir / "generated" / "semantic_harness" / "stage_generic"
            stage_dir.mkdir(parents=True)
            (stage_dir / "A.sv").write_text("module Duplicate; endmodule\n", encoding="utf-8")
            (stage_dir / "B.sv").write_text("module Duplicate; endmodule\n", encoding="utf-8")

            _, _, blockers = normalize_harness_sources(
                {"source_directory": str(stage_dir)},
                run_dir,
            )

            self.assertIn("declares module Duplicate more than once", " ".join(blockers))

    def test_harness_source_directory_must_include_instantiated_dut_modules(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            stage_dir = run_dir / "generated" / "semantic_harness" / "stage_generic"
            stage_dir.mkdir(parents=True)
            (stage_dir / "Harness.sv").write_text(
                "module Harness(input clock, input reset, input in_valid, output in_ready, "
                "input [31:0] in_data, output out_valid, input out_ready, output [31:0] out_data); "
                "FakeDut dut(); endmodule\n",
                encoding="utf-8",
            )
            harness = {
                "top_module": "Harness",
                "source_directory": str(stage_dir),
                "interface": {
                    "clock_port": "clock",
                    "reset_port": "reset",
                    "inputs": [
                        {
                            "valid_port": "in_valid",
                            "ready_port": "in_ready",
                            "data_port": "in_data",
                            "data_width_bits": 32,
                        }
                    ],
                    "output": {
                        "valid_port": "out_valid",
                        "ready_port": "out_ready",
                        "data_port": "out_data",
                        "data_width_bits": 32,
                    },
                },
            }

            _, blockers = harness_contract_errors(
                harness,
                set(),
                "",
                "",
                run_dir,
                {"FakeDut"},
            )

            self.assertIn("source set is not self-contained", " ".join(blockers))

    def test_harness_contract_rejects_manifest_ports_missing_from_top_module(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            stage_dir = run_dir / "generated" / "semantic_harness" / "stage_generic"
            stage_dir.mkdir(parents=True)
            (stage_dir / "Harness.sv").write_text(
                "module Harness(input clock, input reset, input io_in_valid, output io_in_ready, "
                "input [31:0] io_in_data, output io_out_valid, input io_out_ready, "
                "output [31:0] io_out_data); FakeDut dut(); endmodule\n",
                encoding="utf-8",
            )
            (stage_dir / "FakeDut.sv").write_text("module FakeDut; endmodule\n", encoding="utf-8")
            harness = {
                "top_module": "Harness",
                "source_directory": str(stage_dir),
                "interface": {
                    "clock_port": "clock",
                    "reset_port": "reset",
                    "inputs": [
                        {
                            "valid_port": "in_valid",
                            "ready_port": "in_ready",
                            "data_port": "in_data",
                            "data_width_bits": 32,
                        }
                    ],
                    "output": {
                        "valid_port": "out_valid",
                        "ready_port": "out_ready",
                        "data_port": "out_data",
                        "data_width_bits": 32,
                    },
                },
            }

            _, blockers = harness_contract_errors(
                harness,
                set(),
                "",
                "",
                run_dir,
                {"FakeDut"},
            )

            self.assertIn(
                "semantic harness top module does not declare input 0 valid_port: in_valid",
                blockers,
            )
            self.assertIn(
                "semantic harness top module does not declare output data_port: out_data",
                blockers,
            )

    def test_wrapper_policy_scan_does_not_treat_dut_dependencies_as_bypasses(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            stage_dir = run_dir / "generated" / "semantic_harness" / "stage_generic"
            stage_dir.mkdir(parents=True)
            (stage_dir / "Harness.sv").write_text(
                "module Harness(input clock, input reset, input in_valid, output in_ready, "
                "input [31:0] in_data, output out_valid, input out_ready, output [31:0] out_data); "
                "FakeDut dut(); endmodule\n",
                encoding="utf-8",
            )
            (stage_dir / "FakeDut.sv").write_text(
                "module FakeDut; initial $readmemh(\"numeric_lut.memh\", table); "
                "assign io_out_valid = io_in_valid; endmodule\n",
                encoding="utf-8",
            )
            harness = {
                "top_module": "Harness",
                "source_directory": str(stage_dir),
                "interface": {
                    "clock_port": "clock",
                    "reset_port": "reset",
                    "inputs": [
                        {
                            "valid_port": "in_valid",
                            "ready_port": "in_ready",
                            "data_port": "in_data",
                            "data_width_bits": 32,
                        }
                    ],
                    "output": {
                        "valid_port": "out_valid",
                        "ready_port": "out_ready",
                        "data_port": "out_data",
                        "data_width_bits": 32,
                    },
                },
            }

            _, blockers = harness_contract_errors(
                harness,
                set(),
                "",
                "",
                run_dir,
                {"FakeDut"},
            )

            self.assertEqual(blockers, [])

    def test_capability_bundle_is_complete_focused_and_deduplicated(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            manifest_dir = run_dir / "verification" / "semantic_testbench"
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "semantic_testbench_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "test",
                        "status": "incomplete",
                        "stage_contracts": [],
                        "blockers": ["harness missing"],
                    }
                ),
                encoding="utf-8",
            )
            (out_dir / "agent_requested_validation.json").write_text(
                json.dumps({"status": "fail", "results": [{"returncode": 1}]}),
                encoding="utf-8",
            )
            duplicate_content = "package templates\nobject GenericOperator\n"
            source_bundle = {
                "documents": [
                    {
                        "path": "run/input/model_config.json",
                        "content": "{}",
                        "truncated": False,
                    },
                    {
                        "path": "run/generated/chisel/src/main/scala/spatialaccagent/templates/Generic.scala",
                        "content": duplicate_content,
                        "truncated": False,
                    },
                    {
                        "path": "framework/templates/Generic.scala",
                        "content": duplicate_content,
                        "truncated": False,
                    },
                    {
                        "path": "run/generated/chisel/Stale.sv",
                        "content": "module Stale; endmodule\n",
                        "truncated": False,
                    },
                    {
                        "path": "run/pipeline_plan.json",
                        "content": "x" * 1000,
                        "truncated": False,
                    },
                ],
                "generated_module_inventory": [{"path": "run/generated/chisel/Stale.sv"}],
                "trusted_numeric_support": {"status": "pass"},
                "editable_contract": {
                    "semantic_template_repair_approved": True,
                    "approved_bounded_template_repair_exact_files": ["framework/templates/Generic.scala"],
                },
            }

            bundle = capability_repair_source_bundle(source_bundle, run_dir, out_dir)
            paths = [str(row["path"]) for row in bundle["documents"]]
            contents = [str(row["content"]) for row in bundle["documents"]]

            self.assertTrue(bundle["all_documents_complete"])
            self.assertEqual(contents.count(duplicate_content), 1)
            self.assertFalse(any(path.endswith(".sv") for path in paths))
            self.assertTrue(any(path.endswith("semantic_testbench_generator.py") for path in paths))
            self.assertTrue(any("exact_capability_consumer_functions" in path for path in paths))
            self.assertTrue(any(path.endswith("agent_requested_validation.json") for path in paths))
            self.assertEqual(
                bundle["editable_contract"]["approved_bounded_template_repair_exact_files"],
                [],
            )
            self.assertTrue(
                bundle["editable_contract"]["template_repair_deferred_until_real_localized_failure"]
            )

    def test_capability_gap_excludes_historical_unexecuted_leaf_failures(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            failed_dir = run_dir / "verification" / "operator_leaf_functional"
            failed_dir.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            stale_report = failed_dir / "stage_old_attention.json"
            stale_report.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "stage_id": "stage_old_attention",
                        "module_results": [{"summary": "historical numeric mismatch"}],
                    }
                ),
                encoding="utf-8",
            )
            source_bundle = {
                "documents": [],
                "generated_module_inventory": [],
                "trusted_numeric_support": {"status": "pass"},
                "editable_contract": {
                    "read_only_template_sources": [],
                    "approved_bounded_template_repair_exact_files": [],
                },
            }

            bundle = capability_repair_source_bundle(
                source_bundle,
                run_dir,
                out_dir,
                verification_scope="operator_leaf_closure",
                include_operator_leaf_failure_context=False,
            )

            self.assertEqual(bundle["focused_real_tool_failure_context"], {})
            self.assertFalse(
                any(
                    str(row.get("path") or "").endswith(stale_report.name)
                    for row in bundle["documents"]
                )
            )

    def test_capability_bundle_excludes_cross_scope_probe_and_agent_feedback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            llm_dir = out_dir / "llm"
            llm_dir.mkdir(parents=True)
            current_probe = (
                out_dir / "repair_step_00_verification_capability_probe_pre_patch.json"
            )
            stale_board_probe = (
                out_dir
                / "repair_step_00_verification_capability_probe_board_history.json"
            )
            current_probe.write_text(
                json.dumps(
                    {
                        "probe_context": {
                            "schema_version": "spatialaccagent.verification_capability_probe_context.v1",
                            "verification_scope": "single_layer_closure",
                        },
                        "summary": "current connected-harness capability failure",
                    }
                ),
                encoding="utf-8",
            )
            stale_board_probe.write_text(
                json.dumps(
                    {
                        "probe_context": {
                            "schema_version": "spatialaccagent.verification_capability_probe_context.v1",
                            "verification_scope": "board_axi_ddr_closure",
                        },
                        "summary": "historical board checkpoint failure",
                    }
                ),
                encoding="utf-8",
            )
            stale_agent_result = (
                llm_dir / "verification_capability_repair_agent_result.json"
            )
            stale_agent_result.write_text(
                json.dumps(
                    {
                        "capability_repair_context": {
                            "schema_version": "spatialaccagent.verification_capability_repair_agent_context.v1",
                            "verification_scope": "board_axi_ddr_closure",
                        },
                        "output": {
                            "status": "blocked",
                            "summary": "historical board checkpoint failure",
                        },
                    }
                ),
                encoding="utf-8",
            )

            bundle = capability_repair_source_bundle(
                {"documents": [], "editable_contract": {}},
                run_dir,
                out_dir,
                verification_scope="single_layer_closure",
            )
            paths = {str(row["path"]) for row in bundle["documents"]}

            self.assertIn(str(current_probe), paths)
            self.assertNotIn(str(stale_board_probe), paths)
            self.assertFalse(
                any("prior_agent_feedback_projection" in path for path in paths)
            )
            selection = bundle["capability_probe_scope_selection"]
            self.assertEqual(selection["selected_probe_count"], 1)
            self.assertEqual(selection["excluded_other_scope_probe_count"], 1)
            self.assertEqual(selection["excluded_prior_agent_result_count"], 1)

    def test_capability_bundle_includes_editable_source_and_focused_real_tool_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            scala_dir = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "semantic_harness"
            )
            stage_dir = run_dir / "generated" / "semantic_harness" / "stage_generic"
            report_dir = run_dir / "verification" / "operator_leaf_functional"
            contract_dir = run_dir / "verification" / "semantic_testbench" / "stages" / "stage_generic"
            vcs_dir = run_dir / "verification" / "operator_leaf_vcs" / "stage_generic"
            for path in (out_dir, scala_dir, stage_dir, report_dir, contract_dir, vcs_dir):
                path.mkdir(parents=True, exist_ok=True)

            scala_path = scala_dir / "SemanticHarnesses.scala"
            scala_content = "package spatialaccagent.semantic_harness\n" + "// complete source\n" * 3000
            scala_path.write_text(scala_content, encoding="utf-8")
            top_path = stage_dir / "Harness.sv"
            top_path.write_text(
                "module Harness(input clock); Loader loader(); FakeDut dut(); HugeDut huge(); endmodule\n",
                encoding="utf-8",
            )
            loader_path = stage_dir / "Loader.sv"
            loader_path.write_text("module Loader; endmodule\n", encoding="utf-8")
            dut_path = stage_dir / "FakeDut.sv"
            dut_path.write_text("module FakeDut; endmodule\n", encoding="utf-8")
            huge_dut_path = stage_dir / "HugeDut.sv"
            huge_dut_path.write_text(
                "module HugeDut; endmodule\n" + ("// generated dependency body\n" * 12000),
                encoding="utf-8",
            )
            tb_path = contract_dir / "semantic_tb.sv"
            tb_path.write_text("module semantic_tb; Harness dut(); endmodule\n", encoding="utf-8")
            vcs_log = vcs_dir / "vcs.log"
            vcs_log.write_text("Undefined port in module instantiation\n", encoding="utf-8")
            contract_path = contract_dir / "testbench_contract.json"
            contract_path.write_text(
                json.dumps(
                    {
                        "dut_harness": {
                            "top_module": "Harness",
                            "source_files": [
                                {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                                for path in (top_path, loader_path, dut_path, huge_dut_path)
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            report_path = report_dir / "stage_generic.json"
            report_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "semantic_contract_path": str(contract_path),
                        "module_results": [
                            {
                                "status": "fail",
                                "testbench": str(tb_path),
                                "vcs_log": str(vcs_log),
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            probe_path = out_dir / "repair_step_00_verification_capability_probe_pre_patch.json"
            probe_path.write_text(
                json.dumps(
                    {
                        "probe_context": {
                            "schema_version": "spatialaccagent.verification_capability_probe_context.v1",
                            "verification_scope": "operator_leaf_closure",
                        },
                        "produced_reports": [
                            {"path": str(report_path), "status": "fail"}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            bundle = capability_repair_source_bundle(
                {"documents": [], "editable_contract": {}},
                run_dir,
                out_dir,
            )
            documents = {str(row["path"]): row for row in bundle["documents"]}

            self.assertEqual(documents[str(scala_path)]["content"], scala_content)
            for path in (report_path, contract_path, tb_path, vcs_log, top_path, loader_path, dut_path):
                self.assertIn(str(path), documents)
            self.assertNotIn(str(huge_dut_path), documents)
            huge_inventory = next(
                row
                for row in bundle["focused_real_tool_failure_context"]["emitted_causal_source_inventory"]
                if row["path"] == str(huge_dut_path)
            )
            self.assertFalse(huge_inventory["body_included"])
            self.assertEqual(huge_inventory["declared_modules"], ["HugeDut"])
            self.assertEqual(huge_inventory["sha256"], hashlib.sha256(huge_dut_path.read_bytes()).hexdigest())
            self.assertEqual(
                bundle["focused_real_tool_failure_context"]["failed_report"],
                str(report_path),
            )

    def test_leaf_summary_falls_back_to_semantic_numeric_failure(self) -> None:
        report = {
            "status": "fail",
            "stage_id": "stage_arbitrary",
            "summary": "semantic comparison failed",
            "first_failed_module": "ArbitraryHarness",
            "first_failed_summary": "unknown output",
            "semantic_comparison": {
                "status": "fail",
                "numeric_metrics": {
                    "failure_class": "unknown_logic_value",
                    "first_failed_beat_index": 7,
                    "first_failed_lane_index": 3,
                    "actual_decode": {"first_unknown_literal": "xxxxxxxx"},
                },
            },
            "module_results": [{"module": "ArbitraryHarness", "status": "pass"}],
            "blockers": ["numeric contract failed"],
        }

        summary = summarize_leaf_report(report, "ArbitraryHarness")

        self.assertEqual(summary["target_failure_diagnostics"]["first_failed_beat_index"], 7)
        self.assertEqual(summary["target_failure_diagnostics"]["first_failed_lane_index"], 3)
        self.assertEqual(summary["first_failed_module"], "ArbitraryHarness")
        self.assertEqual(summary["first_failed_summary"], "unknown output")

    def test_capability_bundle_prioritizes_current_golden_failures_and_read_only_templates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            scala_root = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
            )
            harness_dir = scala_root / "semantic_harness"
            template_dir = scala_root / "templates"
            golden_dir = run_dir / "verification" / "operator_leaf_golden"
            contract_root = run_dir / "verification" / "semantic_testbench" / "stages"
            generated_root = run_dir / "generated" / "semantic_harness"
            for path in (out_dir, harness_dir, template_dir, golden_dir, contract_root, generated_root):
                path.mkdir(parents=True, exist_ok=True)

            harness_path = harness_dir / "SemanticHarnesses.scala"
            harness_path.write_text(
                "class Stage01Harness extends Module { val a = Module(new AttentionGQA(null)) }\n"
                "class Stage06Harness extends Module { val a = Module(new Activation(null)); val m = Module(new ElementwiseMul(null)) }\n",
                encoding="utf-8",
            )
            template_contents = {
                "Attention.scala": "class AttentionGQA(p: Any) extends Module { val s = Module(new Softmax(null)) }\n",
                "Softmax.scala": "class Softmax(p: Any) extends Module\n",
                "Activation.scala": "class Activation(p: Any) extends Module\n",
                "Elementwise.scala": "class ElementwiseMul(p: Any) extends Module\n",
                "Common.scala": "class StreamBeat extends Bundle\n",
                "Unrelated.scala": "class Unrelated extends Module\n",
            }
            for name, content in template_contents.items():
                (template_dir / name).write_text(content, encoding="utf-8")

            report_paths = []
            for stage_id, top_module in (
                ("stage_01", "Stage01Harness"),
                ("stage_06", "Stage06Harness"),
            ):
                stage_contract_dir = contract_root / stage_id
                stage_source_dir = generated_root / stage_id
                stage_contract_dir.mkdir(parents=True)
                stage_source_dir.mkdir(parents=True)
                top_source = stage_source_dir / f"{top_module}.sv"
                top_source.write_text(f"module {top_module}; endmodule\n", encoding="utf-8")
                contract_path = stage_contract_dir / "testbench_contract.json"
                contract_path.write_text(
                    json.dumps(
                        {
                            "dut_harness": {
                                "top_module": top_module,
                                "source_files": [
                                    {
                                        "path": str(top_source),
                                        "sha256": hashlib.sha256(top_source.read_bytes()).hexdigest(),
                                    }
                                ],
                            }
                        }
                    ),
                    encoding="utf-8",
                )
                report_path = golden_dir / f"{stage_id}.json"
                report_payload = {
                            "status": "fail",
                            "stage_id": stage_id,
                            "gate": "leaf_golden_compare",
                            "semantic_contract_path": str(contract_path),
                            "first_failed_module": top_module,
                            "first_failed_summary": "unknown output",
                            "module_results": [
                                {
                                    "status": "pass",
                                    "rtl_output_sha256": "a" * 64,
                                    "input_fingerprint_sha256": "b" * 64,
                                }
                            ],
                        }
                if stage_id == "stage_01":
                    report_payload["semantic_comparison"] = {
                        "status": "fail",
                        "numeric_metrics": {
                            "failure_class": "unknown_logic_value",
                            "first_failed_beat_index": 11,
                            "first_failed_lane_index": 2,
                        },
                    }
                else:
                    report_payload["target_failure_diagnostics"] = {
                        "failure_class": "unknown_logic_value",
                        "first_failed_beat_index": 0,
                    }
                report_path.write_text(json.dumps(report_payload), encoding="utf-8")
                report_paths.append(report_path)

            stale_snapshot = out_dir / "focused_real_tool_failure_snapshot.json"
            stale_snapshot.write_text(json.dumps({"status": "fail", "stage_id": "old"}), encoding="utf-8")

            bundle = capability_repair_source_bundle(
                {"documents": [], "editable_contract": {}},
                run_dir,
                out_dir,
            )
            paths = {str(row["path"]) for row in bundle["documents"]}

            for report_path in report_paths:
                self.assertIn(str(report_path), paths)
            for name in ("Attention.scala", "Softmax.scala", "Activation.scala", "Elementwise.scala", "Common.scala"):
                self.assertIn(str(template_dir / name), paths)
            self.assertNotIn(str(template_dir / "Unrelated.scala"), paths)
            self.assertNotIn(str(stale_snapshot), paths)
            self.assertEqual(
                bundle["focused_real_tool_failure_context"]["failed_stage_ids"],
                ["stage_01", "stage_06"],
            )
            summaries = {
                row["stage_id"]: row
                for row in bundle["focused_real_tool_failure_context"]["current_failed_reports"]
            }
            self.assertEqual(
                summaries["stage_01"]["target_failure_diagnostics"]["first_failed_beat_index"],
                11,
            )
            self.assertTrue(
                all(
                    str(template_dir / name) in bundle["editable_contract"]["read_only_template_sources"]
                    for name in ("Attention.scala", "Activation.scala", "Elementwise.scala")
                )
            )

    def test_changed_binding_selects_direct_semantic_producer_before_leaf_consumer(self) -> None:
        binding = "/run/generated/memory/dut_weight_binding_manifest.json"
        semantic_manifest = "/run/verification/semantic_testbench/semantic_testbench_manifest.json"
        producer = {
            "name": "case_semantic_testbench",
            "consumes": [binding],
            "produces": [semantic_manifest],
        }
        consumer = {
            "name": "case_leaf_functional",
            "consumes": [semantic_manifest, binding],
            "produces": ["/run/verification/operator_leaf_functional"],
        }
        adapter = {
            "tools": {
                "semantic_testbench_generate": producer,
                "leaf_functional_sim": consumer,
            }
        }

        role, selected = select_changed_input_dependency_producer(
            adapter,
            consumer,
            Path(binding),
        )

        self.assertEqual(role, "semantic_testbench_generate")
        self.assertIs(selected, producer)

    def test_real_tool_failure_snapshot_survives_later_report_replacement(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            report_dir = run_dir / "verification" / "operator_leaf_functional"
            out_dir.mkdir(parents=True)
            report_dir.mkdir(parents=True)
            report_path = report_dir / "stage_generic.json"
            original = {
                "status": "fail",
                "stage_id": "stage_generic",
                "module_results": [{"status": "fail", "compile": {"returncode": 1}}],
            }
            report_path.write_text(json.dumps(original), encoding="utf-8")

            snapshot_path = snapshot_current_real_tool_failure(
                run_dir,
                out_dir,
                "stage_generic",
            )
            report_path.write_text(
                json.dumps({"status": "fail", "module_results": []}),
                encoding="utf-8",
            )
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

            self.assertEqual(snapshot["module_results"], original["module_results"])
            self.assertEqual(snapshot["failure_snapshot_source_path"], str(report_path))

    def test_manifest_materializer_binds_real_sources_and_required_hashes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            generated = run_dir / "generated" / "chisel"
            harness_dir = run_dir / "generated" / "semantic_harness"
            requirements_dir = run_dir / "verification" / "semantic_testbench"
            memory_dir = run_dir / "generated" / "memory"
            for path in (generated, harness_dir, requirements_dir, memory_dir):
                path.mkdir(parents=True, exist_ok=True)

            dut = generated / "FakeDut.sv"
            dut.write_text("module FakeDut(input clock, input reset); endmodule\n", encoding="utf-8")
            harness = harness_dir / "LeafHarness.sv"
            harness.write_text(
                "module LeafHarness(\n"
                "  input clock, input reset,\n"
                "  input in_valid, output in_ready, input [31:0] in_data,\n"
                "  output out_valid, input out_ready, output [31:0] out_data,\n"
                "  input weight_valid, output weight_ready, input [31:0] weight_data,\n"
                "  input [15:0] weight_addr, input weight_last);\n"
                "  FakeDut core(.clock(clock), .reset(reset));\n"
                "  assign in_ready = 1'b1; assign out_valid = in_valid; assign out_data = in_data + 1'b1;\n"
                "  assign weight_ready = 1'b1;\n"
                "endmodule\n",
                encoding="utf-8",
            )
            tensor_hash = "a" * 64
            requirements = {
                "source_checkpoint_sha256": "b" * 64,
                "source_reference_sha256": "c" * 64,
                "numeric_policy_sha256": "d" * 64,
                "model_semantic_adapter_sha256": "e" * 64,
                "stage_requirements": [
                    {
                        "stage_id": "stage_00",
                        "required_tensors": [{"sha256": tensor_hash}],
                        "weight_layout_contract_sha256": "f" * 64,
                    }
                ],
                "single_layer_required_tensors": [{"sha256": tensor_hash}],
            }
            (requirements_dir / "dut_weight_binding_requirements.json").write_text(
                json.dumps(requirements), encoding="utf-8"
            )
            manifest = {
                "stage_harnesses": {
                    "stage_00": {
                        "top_module": "LeafHarness",
                        "source_files": [str(harness), str(dut)],
                        "consumed_tensor_hashes": [tensor_hash],
                        "default_or_identity_weight_fallback_disabled": True,
                        "weight_layout_contract_sha256": "f" * 64,
                        "interface": {
                            "clock_port": "clock",
                            "reset_port": "reset",
                            "inputs": [
                                {
                                    "valid_port": "in_valid",
                                    "ready_port": "in_ready",
                                    "data_port": "in_data",
                                    "data_width_bits": 32,
                                }
                            ],
                            "output": {
                                "valid_port": "out_valid",
                                "ready_port": "out_ready",
                                "data_port": "out_data",
                                "data_width_bits": 32,
                            },
                            "weight_loader": {
                                "valid_port": "weight_valid",
                                "ready_port": "weight_ready",
                                "data_port": "weight_data",
                                "data_width_bits": 32,
                                "addr_port": "weight_addr",
                                "addr_width_bits": 16,
                                "last_port": "weight_last",
                            },
                        },
                    }
                }
            }
            (memory_dir / "dut_weight_binding_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            source_manifest_sha = hashlib.sha256(
                (memory_dir / "dut_weight_binding_manifest.json").read_bytes()
            ).hexdigest()
            patch_path = out_dir / "agent_patch_application.json"
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            patch_path.write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.agent_patch_application.v1",
                        "status": "pass",
                        "blockers": [],
                        "files": [
                            {
                                "path": str(memory_dir / "dut_weight_binding_manifest.json"),
                                "after_sha256": source_manifest_sha,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = finalize_dut_weight_binding_manifest(run_dir, out_dir)
            materialized = json.loads(
                (memory_dir / "dut_weight_binding_manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(report["status"], "pass")
            self.assertEqual(materialized["status"], "pass")
            self.assertEqual(materialized["consumed_tensor_hashes"], [tensor_hash])
            self.assertEqual(
                materialized["stage_harnesses"]["stage_00"]["generated_dut_modules"],
                ["FakeDut"],
            )
            self.assertEqual(report["source_patch_application"], str(patch_path))
            self.assertEqual(
                report["source_patch_application_sha256"],
                hashlib.sha256(patch_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(report["source_agent_manifest_sha256"], source_manifest_sha)

    def test_manifest_materializer_replaces_stale_rows_from_isolated_source_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            generated = run_dir / "generated" / "chisel"
            harness_dir = run_dir / "generated" / "semantic_harness" / "stage_00"
            requirements_dir = run_dir / "verification" / "semantic_testbench"
            memory_dir = run_dir / "generated" / "memory"
            for path in (generated, harness_dir, requirements_dir, memory_dir):
                path.mkdir(parents=True, exist_ok=True)

            dut_source = "module FakeDut(input clock, input reset); endmodule\n"
            generated_dut = generated / "FakeDut.sv"
            generated_dut.write_text(dut_source, encoding="utf-8")
            dut = harness_dir / "FakeDut.sv"
            dut.write_text(dut_source, encoding="utf-8")
            harness = harness_dir / "LeafHarness.sv"
            harness.write_text(
                "module LeafHarness(\n"
                "  input clock, input reset,\n"
                "  input in_valid, output in_ready, input [31:0] in_data,\n"
                "  output out_valid, input out_ready, output [31:0] out_data,\n"
                "  input weight_valid, output weight_ready, input [31:0] weight_data,\n"
                "  input [15:0] weight_addr, input weight_last);\n"
                "  FakeDut core(.clock(clock), .reset(reset));\n"
                "  assign in_ready = 1'b1; assign out_valid = in_valid; assign out_data = in_data + 1'b1;\n"
                "  assign weight_ready = 1'b1;\n"
                "endmodule\n",
                encoding="utf-8",
            )
            tensor_hash = "a" * 64
            requirements = {
                "source_checkpoint_sha256": "b" * 64,
                "source_reference_sha256": "c" * 64,
                "numeric_policy_sha256": "d" * 64,
                "model_semantic_adapter_sha256": "e" * 64,
                "stage_requirements": [
                    {
                        "stage_id": "stage_00",
                        "required_tensors": [{"sha256": tensor_hash}],
                        "weight_layout_contract_sha256": "f" * 64,
                    }
                ],
                "single_layer_required_tensors": [{"sha256": tensor_hash}],
            }
            (requirements_dir / "dut_weight_binding_requirements.json").write_text(
                json.dumps(requirements), encoding="utf-8"
            )
            stale_source = harness_dir / "verification" / "RemovedInstrumentation.sv"
            manifest = {
                "stage_harnesses": {
                    "stage_00": {
                        "top_module": "LeafHarness",
                        "source_directory": str(harness_dir),
                        "source_files": [str(harness), str(dut), str(stale_source)],
                        "consumed_tensor_hashes": [tensor_hash],
                        "default_or_identity_weight_fallback_disabled": True,
                        "weight_layout_contract_sha256": "f" * 64,
                        "interface": {
                            "clock_port": "clock",
                            "reset_port": "reset",
                            "inputs": [
                                {
                                    "valid_port": "in_valid",
                                    "ready_port": "in_ready",
                                    "data_port": "in_data",
                                    "data_width_bits": 32,
                                }
                            ],
                            "output": {
                                "valid_port": "out_valid",
                                "ready_port": "out_ready",
                                "data_port": "out_data",
                                "data_width_bits": 32,
                            },
                            "weight_loader": {
                                "valid_port": "weight_valid",
                                "ready_port": "weight_ready",
                                "data_port": "weight_data",
                                "data_width_bits": 32,
                                "addr_port": "weight_addr",
                                "addr_width_bits": 16,
                                "last_port": "weight_last",
                            },
                        },
                    }
                }
            }
            (memory_dir / "dut_weight_binding_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            report = finalize_dut_weight_binding_manifest(run_dir, out_dir)
            materialized = json.loads(
                (memory_dir / "dut_weight_binding_manifest.json").read_text(encoding="utf-8")
            )

            self.assertEqual(report["status"], "pass", report["blockers"])
            sources = materialized["stage_harnesses"]["stage_00"]["source_files"]
            self.assertEqual({row["path"] for row in sources}, {str(dut), str(harness)})
            self.assertNotIn(str(stale_source), {row["path"] for row in sources})

    def test_board_preflight_failure_marks_binding_materialization_incomplete(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            requirements_path = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "dut_weight_binding_requirements.json"
            )
            binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
            requirements_path.parent.mkdir(parents=True, exist_ok=True)
            binding_path.parent.mkdir(parents=True, exist_ok=True)
            requirements_path.write_text(
                json.dumps(
                    {
                        "source_checkpoint_sha256": "a" * 64,
                        "source_reference_sha256": "b" * 64,
                        "numeric_policy_sha256": "c" * 64,
                        "model_semantic_adapter_sha256": "d" * 64,
                        "stage_requirements": [],
                        "single_layer_required_tensors": [],
                    }
                ),
                encoding="utf-8",
            )
            binding_path.write_text(
                json.dumps({"single_layer_harness": {}, "multilayer_harness": {}}),
                encoding="utf-8",
            )
            normalized_single_layer = {"top_module": "CertifiedKernel", "source_files": []}
            normalized_multilayer = {"top_module": "BoardHarness", "source_files": []}
            failed_preflight = {
                "status": "incomplete",
                "manifest": str(
                    run_dir / "verification" / "board_simulation" / "board_simulation_manifest.json"
                ),
                "manifest_sha256": "e" * 64,
                "vcs_compile_plan_sha256": "f" * 64,
                "path": str(
                    run_dir
                    / "verification"
                    / "board_simulation"
                    / "board_simulation_preflight_materialization.json"
                ),
                "blockers": ["ordered compile plan is incomplete"],
            }

            with (
                patch(
                    "accagent.framework.stage_repair_execute.connected_harness_contract_errors",
                    return_value=(normalized_single_layer, []),
                ),
                patch(
                    "accagent.framework.stage_repair_execute.board_integration_binding_errors",
                    return_value=(normalized_multilayer, []),
                ),
                patch(
                    "accagent.framework.stage_repair_execute.materialize_exact_board_preflight_manifest",
                    return_value=failed_preflight,
                ),
            ):
                report = finalize_dut_weight_binding_manifest(
                    run_dir,
                    out_dir,
                    require_board=True,
                )

            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "incomplete")
            self.assertEqual(binding["status"], "incomplete")
            self.assertFalse(report["board_simulation_preflight_materialized"])
            self.assertIn(
                "board_preflight: ordered compile plan is incomplete",
                report["blockers"],
            )

    def test_identity_path_checker_ignores_internal_identifier_substrings(self) -> None:
        source = (
            "assign attention_io_out_bits_data = core_data;\n"
            "assign output_data = attention_io_out_bits_data;\n"
        )

        self.assertFalse(
            has_interface_data_identity_path(source, {"input_data"}, "output_data")
        )

    def test_identity_path_checker_detects_interface_alias_chain(self) -> None:
        source = (
            "wire [31:0] passthrough = input_data;\n"
            "assign output_data = passthrough;\n"
        )

        self.assertTrue(
            has_interface_data_identity_path(source, {"input_data"}, "output_data")
        )

    def test_operator_leaf_binding_does_not_require_single_layer_harness(self) -> None:
        binding = {
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "source_checkpoint_sha256": "a",
            "source_reference_sha256": "b",
            "numeric_policy_sha256": "c",
            "model_semantic_adapter_sha256": "d",
            "scope_coverage_complete": True,
            "dut_consumes_bound_weights": True,
            "default_or_identity_weight_fallback_disabled": True,
            "consumed_tensor_hashes": [],
            "stage_harnesses": {"stage_00": {}},
        }
        requirements = {
            "source_checkpoint_sha256": "a",
            "source_reference_sha256": "b",
            "numeric_policy_sha256": "c",
            "model_semantic_adapter_sha256": "d",
            "single_layer_required_tensors": [],
            "stage_requirements": [{"stage_id": "stage_00"}],
        }

        self.assertEqual(
            dut_binding_errors(binding, requirements, require_single_layer=False), []
        )
        self.assertIn(
            "DUT binding has no connected single-layer semantic harness",
            dut_binding_errors(binding, requirements),
        )
