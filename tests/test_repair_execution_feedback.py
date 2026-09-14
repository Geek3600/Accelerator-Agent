import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.stage_repair import (
    REPAIR_FEEDBACK_ARTIFACT_REF_SCHEMA_VERSION,
    build_repair_workflow,
    build_repair_plan,
    diagnosis_applicability_report,
    diagnosis_prompt_projection,
    prior_repair_execution_feedback,
    rematerialized_lower_layer_capability_evidence,
    required_capability_repair_actions,
)
from accagent.framework.stage_repair_execute import (
    board_axi_protocol_failure_eligible,
    board_integration_prompt_rules,
    bind_authoritative_workload_image_identity,
    bind_authoritative_physical_cfg_value_sources,
    complete_internal_signal_binding_plan,
    _current_pipeline_boundary_observation_authority,
    _stage_internal_signal_binding_check,
    execute_causal_slice_repair,
    execute_verification_capability_repair,
    exact_board_vcs_rerun_command_error,
    _is_internal_data_boundary_observation,
    localize_vcs_timescale_error_provenance,
    normalize_connected_kernel_boundary_signal_map_source_refs,
    _matching_cached_boundary_signal_map_record,
    preserve_vcs_compile_diagnostic_provenance,
    prior_capability_producer_evidence,
    reconcile_exact_board_lifecycle_cctg_observation_contract,
    rebase_stale_single_layer_compile_agent_output,
    rebind_exact_board_vcs_rerun_step,
    record_exact_board_rerun_agent_handoff,
    repair_loop_disposition,
    run_board_semantic_rtl_single_layer_gate,
    reuse_existing_single_layer_gate_for_board_repair,
    single_layer_compile_failure_repair_context,
    supported_required_capability_handoff,
    validate_connected_kernel_boundary_signal_map,
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


class WorkloadImageIdentityBindingTest(TestCase):
    def test_binds_only_authoritative_image_identity_fields(self) -> None:
        plan = {
            "status": "pass",
            "input_identity": {
                "stage_weight_layout_contract_sha256s": ["old"],
                "unrelated": "preserve",
            },
            "memory": {"weight_bank_capacity_bytes": 123},
        }
        required = {
            "stage_weight_layout_contract_sha256s": ["new"],
            "canonical_weight_layout_set_sha256": "set-new",
            "transformer_block_weight_catalog_sha256": "catalog-new",
        }

        bound, report = bind_authoritative_workload_image_identity(plan, required)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["bound_field_count"], 3)
        self.assertEqual(
            bound["input_identity"],
            {
                "stage_weight_layout_contract_sha256s": ["new"],
                "canonical_weight_layout_set_sha256": "set-new",
                "transformer_block_weight_catalog_sha256": "catalog-new",
                "unrelated": "preserve",
            },
        )
        self.assertEqual(bound["memory"], {"weight_bank_capacity_bytes": 123})
        self.assertEqual(
            plan["input_identity"]["stage_weight_layout_contract_sha256s"],
            ["old"],
        )


class SingleLayerCompileRepairContextTest(TestCase):
    def test_routes_real_compile_error_to_only_diagnostic_semantic_rtl_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            semantic_root = run_dir / "generated" / "semantic_harness" / "single_layer"
            gated_mlp = semantic_root / "GatedMLP.sv"
            linear_4 = semantic_root / "Linear_4.sv"
            gated_mlp.parent.mkdir(parents=True)
            gated_mlp.write_text(
                "module GatedMLP;\n"
                "  Linear_4 down(.io_in_bits_addr(addr), .io_in_bits_last(last));\n"
                "endmodule\n",
                encoding="utf-8",
            )
            linear_4.write_text(
                "module Linear_4(input logic clock, input logic reset);\n"
                "endmodule\n",
                encoding="utf-8",
            )
            log = (
                run_dir
                / "verification"
                / "operator_leaf_vcs"
                / "single_transformer_layer_kernel"
                / "vcs.log"
            )
            log.parent.mkdir(parents=True)
            log.write_text(
                "Error-[UPIMI-E] Undefined port in module instantiation\n"
                "GatedMLP.sv, 2\n"
                "  Port \"io_in_bits_addr\" is not defined in module 'Linear_4' defined in \"Linear_4.sv\".\n"
                "Error-[UPIMI-E] Undefined port in module instantiation\n"
                "GatedMLP.sv, 2\n"
                "  Port \"io_in_bits_last\" is not defined in module 'Linear_4' defined in \"Linear_4.sv\".\n",
                encoding="utf-8",
            )
            report = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
            write_json(
                report,
                {
                    "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
                    "status": "fail",
                    "stats": {
                        "stage_id": "single_transformer_layer_kernel",
                        "top_module": "semantic_single_transformer_layer_kernel_tb",
                        "vcs_log": str(log),
                        "source_files": [str(gated_mlp), str(linear_4)],
                        "compile": {"status": "fail", "returncode": 1},
                        "run": {"status": "not_run"},
                    },
                },
            )

            context = single_layer_compile_failure_repair_context(
                run_dir,
                {"id": "repair_step.00"},
            )

            self.assertEqual(context["status"], "ready")
            self.assertEqual(
                {Path(value).name for value in context["editable_paths"]},
                {"GatedMLP.sv"},
            )
            self.assertEqual(
                context["diagnostic"]["missing_ports"],
                [
                    {"port": "io_in_bits_addr", "module": "Linear_4"},
                    {"port": "io_in_bits_last", "module": "Linear_4"},
                ],
            )
            contract = context["source_bundle"]["editable_contract"]
            self.assertTrue(contract["require_exact_source_sha256"])
            self.assertEqual(
                contract["forbidden_targets"],
                [
                    "board_wrapper",
                    "testbench",
                    "axi_ddr",
                    "weights",
                    "runtime_image",
                    "golden",
                    "checker",
                    "framework",
                ],
            )
            self.assertTrue(
                context["authority"]["board_authority_deferred_until_single_layer_pass"]
            )

    def test_rejects_non_compile_or_simulated_single_layer_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report = run_dir / "verification" / "single_layer" / "single_layer_functional_report.json"
            write_json(
                report,
                {
                    "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
                    "status": "fail",
                    "stats": {
                        "compile": {"status": "pass", "returncode": 0},
                        "run": {"status": "fail"},
                    },
                },
            )

            context = single_layer_compile_failure_repair_context(
                run_dir,
                {"id": "repair_step.00"},
            )

            self.assertEqual(context["status"], "blocked")
            self.assertIn(
                "single-layer report does not prove a failed VCS compile",
                context["blockers"],
            )


class SingleLayerCompileSourceRebaseTest(TestCase):
    def _context(self, run_dir: Path, source: Path) -> dict:
        return {
            "diagnostic": {
                "error": "Error-[UPIMI-E] Undefined port in module instantiation",
                "source_path": str(source),
                "missing_ports": [
                    {"port": "io_in_bits_addr", "module": "Linear_4"},
                    {"port": "io_in_bits_last", "module": "Linear_4"},
                ],
            }
        }

    def test_rebases_stale_complete_replacement_to_current_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = run_dir / "generated" / "semantic_harness" / "single_layer" / "GatedMLP.sv"
            source.parent.mkdir(parents=True)
            old = (
                "module GatedMLP;\n"
                "  wire old_signal;\n"
                "  Linear_4 down (\n"
                "    .io_in_bits_data(data),\n"
                "    .io_in_bits_addr(addr),\n"
                "    .io_in_bits_last(last),\n"
                "    .io_out_valid(out)\n"
                "  );\n"
                "endmodule\n"
            )
            current = old.replace("wire old_signal;", "wire retained_signal;")
            proposed = old.replace(
                "    .io_in_bits_addr(addr),\n", ""
            ).replace("    .io_in_bits_last(last),\n", "")
            source.write_text(current, encoding="ascii")
            old_hash = hashlib.sha256(old.encode("ascii")).hexdigest()
            current_hash = hashlib.sha256(current.encode("ascii")).hexdigest()
            report_path = run_dir / "repair_execution" / "loop" / "iteration_0988" / "00_agent_patch_application_agent_patch_application.json"
            write_json(
                report_path,
                {
                    "status": "pass",
                    "blockers": [],
                    "files": [{
                        "path": str(source),
                        "before_sha256": old_hash,
                        "after_sha256": current_hash,
                    }],
                },
            )
            output = {
                "status": "ready_to_apply",
                "file_edits": [{
                    "path": str(source),
                    "operation": "replace",
                    "expected_sha256": old_hash,
                    "content": proposed,
                    "rationale": "remove the two undefined Linear_4 input ports",
                }],
            }

            rebased, report = rebase_stale_single_layer_compile_agent_output(
                output, self._context(run_dir, source), run_dir
            )

            self.assertEqual(report["status"], "pass", report)
            edit = rebased["file_edits"][0]
            self.assertEqual(edit["operation"], "replace_text")
            self.assertEqual(edit["expected_sha256"], current_hash)
            self.assertEqual(edit["content"], "")
            self.assertEqual(len(edit["text_replacements"]), 2)
            self.assertIn("wire retained_signal;", current)
            self.assertNotIn("io_in_bits_addr", proposed)
            self.assertNotIn("io_in_bits_last", proposed)

    def test_does_not_rebase_without_recorded_direct_parent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = run_dir / "generated" / "semantic_harness" / "single_layer" / "GatedMLP.sv"
            source.parent.mkdir(parents=True)
            current = (
                "module GatedMLP;\n"
                "  .io_in_bits_addr(addr),\n"
                "  .io_in_bits_last(last),\n"
                "endmodule\n"
            )
            source.write_text(current, encoding="ascii")
            output = {
                "status": "ready_to_apply",
                "file_edits": [{
                    "path": str(source),
                    "operation": "replace",
                    "expected_sha256": "1" * 64,
                    "content": "module GatedMLP;\nendmodule\n",
                    "rationale": "remove undefined ports",
                }],
            }

            rebased, report = rebase_stale_single_layer_compile_agent_output(
                output,
                {
                    "diagnostic": {
                        "error": "Error-[UPIMI-E] Undefined port in module instantiation",
                        "source_path": str(source),
                        "missing_ports": [
                            {"port": "io_in_bits_addr", "module": "Linear_4"},
                            {"port": "io_in_bits_last", "module": "Linear_4"},
                        ],
                    }
                },
                run_dir,
            )

            self.assertEqual(report["status"], "blocked")
            self.assertIs(rebased, output)
            self.assertIn("direct parent", " ".join(report["blockers"]))


class PhysicalCfgValueSourceBindingTest(TestCase):
    def test_binds_reset_value_source_to_exact_physical_field_index(self) -> None:
        identity = {
            "compute_slot_abi": {
                "control_abi": {
                    "configuration_fields": [
                        {
                            "field_id": "first",
                            "fact_port_id": "port",
                            "register": "cfg_data",
                            "reset_value": 0,
                        },
                        {
                            "field_id": "slv_reg21",
                            "fact_port_id": "port",
                            "register": "cfg_data",
                            "reset_value": 0,
                        },
                    ]
                }
            }
        }
        plan = {
            "physical_cfg_bindings": [
                {
                    "binding_id": "reserved",
                    "field_id": "slv_reg21",
                    "fact_port_id": "port",
                    "register": "cfg_data",
                    "value": {
                        "resolved_value": 0,
                        "source": {
                            "artifact": "identity",
                            "kind": "artifact_ref",
                            "path": "/compute_slot_abi/control_abi/configuration_fields/22/reset_value",
                        },
                    },
                }
            ]
        }

        bound, report = bind_authoritative_physical_cfg_value_sources(plan, identity)

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["bound_field_count"], 1)
        self.assertEqual(
            bound["physical_cfg_bindings"][0]["value"]["source"]["path"],
            "/compute_slot_abi/control_abi/configuration_fields/1/reset_value",
        )
        self.assertEqual(
            plan["physical_cfg_bindings"][0]["value"]["source"]["path"],
            "/compute_slot_abi/control_abi/configuration_fields/22/reset_value",
        )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_passing_connected_kernel_replay_package(
    run_dir: Path,
    *,
    trace_sha256: str | None = None,
) -> Path:
    """Create one hash-bound completed Layer-2 replay package for planner tests."""

    evidence_dir = run_dir / "verification" / "debug_closure"
    diagnosis_dir = run_dir / "verification" / "case_diagnostics"
    trace_path = evidence_dir / "connected_kernel_cctg_targeted_replay_trace.json"
    context_path = diagnosis_dir / "connected_kernel_targeted_replay_causal_context.json"
    reconciliation_path = (
        diagnosis_dir / "connected_kernel_cctg_contradiction_reconciliation.json"
    )
    write_json(
        trace_path,
        {
            "schema_version": "spatialaccagent.connected_kernel_cctg_targeted_replay_trace.v1",
            "status": "pass",
            "start_witness": {"source": "first_accepted_core_ingress"},
            "expected_ingress_beats": 4,
            "lifecycle": {
                "ingress_complete": True,
                "egress_accepted_count": 4,
                "egress_complete": True,
                "terminal_egress_last": True,
            },
        },
    )
    write_json(
        context_path,
        {
            "schema_version": "spatialaccagent.connected_kernel_targeted_replay_causal_context.v1",
            "status": "pass",
        },
    )
    write_json(
        reconciliation_path,
        {
            "schema_version": "spatialaccagent.connected_kernel_cctg_contradiction_reconciliation.v1",
            "status": "pass",
        },
    )
    package_path = (
        run_dir
        / "repair_execution"
        / "repair_step_00_current_layer_causal_repair_context_package.json"
    )
    write_json(
        package_path,
        {
            "schema_version": "spatialaccagent.current_layer_causal_repair_context_package.v0",
            "status": "pass",
            "capability_id": "connected_kernel_cctg_contradiction_targeted_replay",
            "run_dir": str(run_dir.resolve()),
            "debug_layer": "single_transformer_layer_kernel",
            "current_layer_replay": {"debug_layer": "single_layer_closure"},
            "cctg_boundary_replay_evidence": {
                "schema_version": "spatialaccagent.cctg_boundary_replay.v1",
                "status": "pass",
                "fresh_remote_vcs_execution_observed": True,
                "boundary_liveness_status": "pass",
                "accepted_trace_record_count": 12,
            },
            "connected_kernel_cctg_targeted_replay_trace": {
                "path": str(trace_path),
                "sha256": trace_sha256 or sha256(trace_path),
            },
            "connected_kernel_targeted_replay_causal_context": {
                "path": str(context_path),
                "sha256": sha256(context_path),
            },
            "connected_kernel_cctg_contradiction_reconciliation": {
                "path": str(reconciliation_path),
                "sha256": sha256(reconciliation_path),
            },
        },
    )
    return package_path


class RepairExecutionFeedbackTest(TestCase):
    def test_explicit_axi_protocol_diagnostic_allows_bounded_board_repair(self) -> None:
        simulation = {
            "completed": True,
            "exit_code": 0,
            "pass_marker_seen": False,
            "termination_provenance": {
                "status": "complete",
                "termination_source": "normal_process_exit",
                "causal_classification": {
                    "simulator_infrastructure_failure_proven": False,
                    "deterministic_hdl_or_testbench_failure_proven": True,
                },
                "simulator_terminal_log": {
                    "status": "observed",
                    "failure_lines": [
                        "SPATIALACC_AXI_PROTOCOL_VIOLATION",
                    ],
                },
            },
        }

        self.assertEqual(
            board_axi_protocol_failure_eligible(simulation),
            (True, "explicit_axi_protocol_violation_marker"),
        )

    def test_axi_protocol_repair_gate_rejects_crash_or_generic_finish(self) -> None:
        base = {
            "completed": True,
            "pass_marker_seen": False,
            "termination_provenance": {
                "status": "complete",
                "termination_source": "normal_process_exit",
                "causal_classification": {
                    "simulator_infrastructure_failure_proven": False,
                },
                "simulator_terminal_log": {
                    "status": "observed",
                    "failure_lines": ["testbench stopped"],
                },
            },
        }
        self.assertFalse(board_axi_protocol_failure_eligible(base)[0])
        crash = json.loads(json.dumps(base))
        crash["termination_provenance"]["termination_source"] = (
            "runner_owned_simulator_signal_exit"
        )
        crash["termination_provenance"]["simulator_terminal_log"]["failure_lines"] = [
            "SPATIALACC_AXI_PROTOCOL_VIOLATION"
        ]
        self.assertFalse(board_axi_protocol_failure_eligible(crash)[0])

    def test_complete_internal_signal_binding_plan_requires_real_dut_signals(self) -> None:
        decision = {
            "boundary_coverage_plan": {
                "boundary_ids": ["edge.kernel.inner"],
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
                    "boundary_id": "edge.kernel.inner",
                    "valid_source": "dut.core.inner_valid",
                    "ready_source": "dut.core.inner_ready",
                    "fire_source": "(dut.core.inner_valid) && (dut.core.inner_ready)",
                    "accepted_count_source": "inner_accepted_count",
                    "payload_source": "dut.core.inner_payload",
                    "diagnostic_sources": [
                        {
                            "name": "inner_state",
                            "role": "state",
                            "expression": "dut.core.inner_state",
                        },
                        {
                            "name": "inner_queue_count",
                            "role": "queue",
                            "expression": "dut.core.inner_queue_count",
                        },
                    ],
                }
            ],
        }
        source = "\n".join(
            [
                "wire inner_valid = dut.core.inner_valid;",
                "wire inner_ready = dut.core.inner_ready;",
                "wire inner_fire = (dut.core.inner_valid) && (dut.core.inner_ready);",
                "wire [31:0] inner_payload = dut.core.inner_payload;",
                "longint inner_accepted_count;",
                "logic [31:0] first_accepted_payload_digest;",
                "logic [31:0] last_accepted_payload_digest;",
                "logic inner_state;",
                "logic [3:0] inner_queue_count;",
                "dut.core.inner_state dut.core.inner_queue_count",
            ]
        )
        output = {
            "file_edits": [
                {
                    "operation": "create",
                    "path": "BoardObservation.sv",
                    "content": source,
                }
            ]
        }

        accepted = complete_internal_signal_binding_plan(decision, output)
        no_dut = json.loads(json.dumps(decision))
        for field in ("valid_source", "ready_source", "fire_source", "payload_source"):
            no_dut["signal_binding_plan"][0][field] = field
        rejected = complete_internal_signal_binding_plan(no_dut, output)

        self.assertEqual(accepted["status"], "pass")
        self.assertTrue(accepted["uses_internal_dut_signal"])
        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(
            any("direct DUT hierarchy signal" in item for item in rejected["blockers"])
        )

    def test_complete_internal_signal_binding_plan_allows_nested_fire_records(self) -> None:
        decision = {
            "boundary_coverage_plan": {
                "boundary_ids": ["edge.kernel.inner"],
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
                    "boundary_id": "edge.kernel.inner",
                    "valid_source": "dut.core.inner_valid",
                    "ready_source": "dut.core.inner_ready",
                    "fire_source": "(dut.core.inner_valid) && (dut.core.inner_ready)",
                    "accepted_count_source": "inner_accepted_count[0]",
                    "payload_source": "dut.core.inner_payload",
                    "diagnostic_sources": [
                        {
                            "name": "inner_state",
                            "role": "state",
                            "expression": "dut.core.inner_state",
                        },
                        {
                            "name": "inner_queue_count",
                            "role": "queue",
                            "expression": "dut.core.inner_queue_count",
                        },
                    ],
                }
            ],
        }
        source = "\n".join(
            [
                "wire inner_valid [0:0];",
                "wire inner_ready [0:0];",
                "wire inner_fire [0:0];",
                "wire [31:0] inner_payload [0:0];",
                "assign inner_valid[0] = dut.core.inner_valid;",
                "assign inner_ready[0] = dut.core.inner_ready;",
                "assign inner_fire[0] = (dut.core.inner_valid) && (dut.core.inner_ready);",
                "assign inner_payload[0] = dut.core.inner_payload;",
                "longint inner_accepted_count [0:0];",
                "logic [31:0] first_accepted_payload_digest;",
                "logic [31:0] last_accepted_payload_digest;",
                "logic inner_state;",
                "logic [3:0] inner_queue_count;",
                "dut.core.inner_state dut.core.inner_queue_count",
                "always begin",
                "  if (inner_fire[index] === 1'b1) begin",
                "    if (first_seen) begin",
                "      first_accepted_payload_digest <= inner_payload[index];",
                "    end",
                "    inner_accepted_count[index] <= inner_accepted_count[index] + 1;",
                "    last_accepted_payload_digest <= inner_payload[index];",
                "  end",
                "end",
            ]
        )
        accepted = complete_internal_signal_binding_plan(
            decision, {"file_edits": [{"operation": "create", "path": "BoardObservation.sv", "content": source}]}
        )
        outside_guard = source.replace(
            "    inner_accepted_count[index] <= inner_accepted_count[index] + 1;\n",
            "  end\n  inner_accepted_count[index] <= inner_accepted_count[index] + 1;\n",
        )
        rejected = complete_internal_signal_binding_plan(
            decision,
            {"file_edits": [{"operation": "create", "path": "BoardObservation.sv", "content": outside_guard}]},
        )

        self.assertEqual(accepted["status"], "pass")
        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(
            any("must increment only when" in item for item in rejected["blockers"])
        )

    def test_stage_internal_signal_plan_covers_current_graph_without_fixed_stage_names(self) -> None:
        authority = {
            "status": "ready",
            "required_boundaries": [
                {
                    "boundary_id": "edge.input",
                    "src_stage": "block_input",
                    "dst_stage": "compute_a",
                },
                {
                    "boundary_id": "edge.middle",
                    "src_stage": "compute_a",
                    "dst_stage": "compute_b",
                },
                {
                    "boundary_id": "edge.output",
                    "src_stage": "compute_b",
                    "dst_stage": "block_output",
                },
            ],
        }
        decision = {
            "stage_internal_signal_plan": [
                {
                    "stage_id": "compute_a",
                    "input_boundary_ids": ["edge.input"],
                    "output_boundary_ids": ["edge.middle"],
                    "diagnostic_sources": [
                        {
                            "name": "a_state",
                            "role": "state",
                            "expression": "dut.compute_a.state",
                        },
                        {
                            "name": "a_queue_count",
                            "role": "queue",
                            "expression": "dut.compute_a.queue_count",
                        },
                    ],
                },
                {
                    "stage_id": "compute_b",
                    "input_boundary_ids": ["edge.middle"],
                    "output_boundary_ids": ["edge.output"],
                    "diagnostic_sources": [
                        {
                            "name": "b_state",
                            "role": "state",
                            "expression": "dut.compute_b.state",
                        }
                    ],
                },
            ]
        }
        source = " ".join(
            [
                "dut.compute_a.state",
                "dut.compute_a.queue_count",
                "dut.compute_b.state",
                "SPATIALACC_STAGE_TRACE stage=compute_a signal=a_state",
                "SPATIALACC_STAGE_TRACE stage=compute_a signal=a_queue_count",
                "SPATIALACC_STAGE_TRACE stage=compute_b signal=b_state",
            ]
        )
        accepted = _stage_internal_signal_binding_check(
            decision, authority, [source]
        )
        missing_stage = json.loads(json.dumps(decision))
        missing_stage["stage_internal_signal_plan"].pop()
        rejected = _stage_internal_signal_binding_check(
            missing_stage, authority, [source]
        )

        self.assertEqual(accepted["status"], "pass")
        self.assertEqual(accepted["stage_count"], 2)
        self.assertEqual(accepted["signal_count"], 3)
        self.assertEqual(rejected["status"], "blocked")
        self.assertTrue(any("compute_b" in item for item in rejected["blockers"]))

    def test_current_pipeline_authority_unwraps_bound_repair_context(self) -> None:
        authority = {
            "status": "ready",
            "required_stages": [{"stage_id": "stage_a"}],
        }
        package = {
            "exact_board_integration_repair_context": {
                "path": "/tmp/context.json",
                "value": {
                    "adaptive_design_inputs": {
                        "pipeline_boundary_observation_authority": {
                            "sha256": "a" * 64,
                            "value": authority,
                        }
                    }
                },
            }
        }

        self.assertEqual(
            _current_pipeline_boundary_observation_authority(package), authority
        )

    def test_board_semantic_rtl_gate_uses_single_layer_tool_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            out_dir = root / "repair_execution"
            adapter = {
                "tools": {
                    "case_single_layer_functional": {
                        "name": "case_single_layer_functional",
                        "argv": ["single-layer-tool"],
                        "produces": [],
                    }
                }
            }
            step = {
                "id": "repair_step.board_rtl",
                "scope": "verification_capability_repair",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "action": {
                    "repair_kind": "board_semantic_rtl_repair",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "target_modules": ["generated_kernel"],
                },
            }
            single_layer_result = {
                "status": "pass",
                "summary": "single layer passed",
                "produced_reports": [],
                "log_path": str(root / "single_layer_probe.json"),
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_capability_probe",
                return_value=single_layer_result,
            ) as probe:
                result = run_board_semantic_rtl_single_layer_gate(
                    case_adapter=adapter,
                    run_dir=root,
                    step=step,
                    out_dir=out_dir,
                    timeout_sec=1,
                )

            self.assertEqual(result["status"], "pass")
            self.assertFalse(result["board_vcs_started"])
            self.assertEqual(result["single_layer_gate"], "case_single_layer_functional")
            probe.assert_called_once()
            called_step = probe.call_args.kwargs["step"]
            self.assertEqual(
                called_step["action"]["repair_kind"],
                "case_single_layer_functional",
            )
            self.assertEqual(
                called_step["action"]["debug_layer"],
                "single_transformer_layer_kernel",
            )
            self.assertEqual(
                called_step["action"]["target_modules"],
                [
                    "connected_single_transformer_layer_kernel",
                    "single_layer_pipeline_overlap_contract",
                ],
            )

    def test_board_semantic_rtl_gate_failure_forbids_board_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            failed = {
                "status": "fail",
                "summary": "single layer failed",
                "produced_reports": [],
                "log_path": str(root / "single_layer_probe.json"),
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_capability_probe",
                return_value=failed,
            ):
                result = run_board_semantic_rtl_single_layer_gate(
                    case_adapter={
                        "tools": {
                            "case_single_layer_functional": {
                                "name": "case_single_layer_functional",
                                "argv": ["single-layer-tool"],
                                "produces": [],
                            }
                        }
                    },
                    run_dir=root,
                    step={"id": "repair_step.board_rtl", "action": {}},
                    out_dir=root / "repair_execution",
                    timeout_sec=1,
                )

            self.assertEqual(result["status"], "fail")
            self.assertFalse(result["board_vcs_started"])
            self.assertEqual(result["single_layer_gate"], "case_single_layer_functional")

    def test_board_repair_reuses_current_passed_single_layer_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "verification" / "single_layer" / "single_layer_functional_report.json"
            write_json(report, {"status": "pass"})
            self.assertTrue(reuse_existing_single_layer_gate_for_board_repair(root))

    def test_board_repair_keeps_single_layer_gate_for_new_run(self) -> None:
        with TemporaryDirectory() as temp_dir:
            self.assertFalse(
                reuse_existing_single_layer_gate_for_board_repair(Path(temp_dir))
            )

    def test_inner_kernel_boundary_observation_is_not_count_only(self) -> None:
        self.assertTrue(
            _is_internal_data_boundary_observation(
                {
                    "evidence_pointer": (
                        "/current_board_vcs_feedback/diagnosis/value/"
                        "failure_evidence/progress_event_summary/latest_stall_snapshot/"
                        "connected_kernel_inner_cone_observation/mlp_down_input_accepted_count"
                    )
                }
            )
        )
        self.assertTrue(
            _is_internal_data_boundary_observation(
                {
                    "evidence_pointer": (
                        "/current_board_vcs_feedback/diagnosis/value/"
                        "failure_evidence/progress_event_summary/latest_stall_snapshot/"
                        "connected_kernel_internal_pipeline_observation/first_start_cycle"
                    )
                }
            )
        )
        self.assertFalse(
            _is_internal_data_boundary_observation(
                {
                    "evidence_pointer": "/current_board_vcs_feedback/diagnosis/value/runtime/input_count"
                }
            )
        )

    def test_lifecycle_reconciliation_accepts_empty_target_and_does_not_run_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            out_dir = run_dir / "repair_execution"
            evidence = {
                "verification/case_diagnostics/sacg_cctg_causal_slice.json": {
                    "status": "ready",
                    "schema_version": "test.causal_slice.v1",
                },
                "verification/board_simulation/reports/boundary_trace.jsonl": [
                    {
                        "mlp_down_input_accepted_count": 607,
                        "mlp_down_output_accepted_count": 0,
                    }
                ],
                "verification/board_simulation/reports/progress_event_log.jsonl": [
                    {
                        "first_core_ingress_fire_cycle": 20572946,
                        "first_start_cycle": 20572948,
                        "core_ingress_accepted_count": 1792,
                        "core_egress_accepted_count": 0,
                        "output_accept_count": 0,
                    }
                ],
                "verification/board_interface/board_source_identity.json": {
                    "status": "pass"
                },
                "verification/semantic_testbench/semantic_testbench_manifest.json": {
                    "status": "ready"
                },
            }
            refs = []
            for relative, value in evidence.items():
                path = run_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".jsonl":
                    path.write_text(
                        "\n".join(json.dumps(row) for row in value) + "\n",
                        encoding="utf-8",
                    )
                else:
                    write_json(path, value)
                refs.append(f"{relative} sha256={sha256(path)}")

            step = {
                "id": "repair_step.lifecycle",
                "action": {
                    "repair_kind": "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
                    "required_evidence": refs,
                },
            }
            result = reconcile_exact_board_lifecycle_cctg_observation_contract(
                run_dir=run_dir, out_dir=out_dir, step=step
            )

            self.assertEqual(result["status"], "pass")
            self.assertTrue(result["requires_agent_followup"])
            self.assertFalse(result["vcs_started"])
            self.assertFalse(result["source_write"])
            package = json.loads(Path(result["context_package"]).read_text())
            self.assertTrue(package["lifecycle"]["input_before_start"])
            self.assertEqual(
                package["preserved_contract"]["mlp_down_input_accepted_count"],
                607,
            )

    def test_lifecycle_reconciliation_fails_closed_on_sha_mismatch(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            evidence_path = run_dir / "verification" / "one.json"
            write_json(evidence_path, {"first_start_cycle": 2})
            step = {
                "action": {
                    "repair_kind": "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
                    "required_evidence": [
                        "verification/one.json sha256=" + "0" * 64
                    ],
                }
            }
            result = reconcile_exact_board_lifecycle_cctg_observation_contract(
                run_dir=run_dir, out_dir=run_dir / "repair_execution", step=step
            )

            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any("SHA-256 mismatch" in item for item in result["blockers"]))

    def test_lifecycle_capability_dispatches_without_entering_vcs_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source_state = run_dir / "sacg_state.json"
            write_json(source_state, {})
            result = execute_verification_capability_repair(
                {
                    "id": "repair_step.lifecycle",
                    "action": {
                        "repair_kind": "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
                        "required_evidence": [],
                    },
                },
                source_state,
                run_dir,
                run_dir / "repair_execution",
                0,
            )
            self.assertEqual(result["status"], "blocked")
            self.assertIn("no declared evidence list", result["summary"])

    def test_cctg_replay_is_a_capability_producer_not_a_stage_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "sacg_state.json"
            source_state.write_text("{}\n", encoding="utf-8")
            step = {
                "id": "repair_step.cctg",
                "scope": "causal_slice_repair",
                "debug_layer": "single_transformer_layer_kernel",
                "action": {"repair_kind": "cctg_connected_kernel_boundary_replay"},
            }
            replay = {
                "status": "pass",
                "log_path": str(root / "cctg_replay_log.json"),
                "cctg_boundary_replay": {
                    "path": str(root / "cctg_boundary_replay.json"),
                    "status": "pass",
                    "boundary_liveness_status": "fail",
                    "first_incomplete_boundary": "edge.rms1_to_attention",
                    "blockers": [],
                },
            }
            (root / "cctg_boundary_replay.json").write_text(
                json.dumps(
                    {
                        "schema_version": "spatialaccagent.cctg_boundary_replay.v1",
                        "status": "pass",
                        "boundary_records": [
                            {
                                "boundary_id": "edge.rms1_to_attention",
                                "accepted_count": 3,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch(
                "accagent.framework.stage_repair_execute.run_current_layer_causal_replay",
                return_value=replay,
            ):
                result = execute_causal_slice_repair(
                    step, source_state, root, root / "out", 1
                )
            package = json.loads(Path(result["context_package"]).read_text())

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["requires_agent_followup"])
        self.assertFalse(result["stage_passed"])
        self.assertEqual(result["repair_kind"], "cctg_connected_kernel_boundary_replay")
        self.assertEqual(package["status"], "pass")
        self.assertEqual(
            package["cctg_boundary_replay"]["first_incomplete_boundary"],
            "edge.rms1_to_attention",
        )
        self.assertEqual(
            package["cctg_boundary_replay_evidence"]["boundary_records"][0]["boundary_id"],
            "edge.rms1_to_attention",
        )

    def test_board_functional_aggregate_accepts_current_vcs_binding(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            source = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
            source.parent.mkdir(parents=True)
            source.write_text("current board evidence", encoding="utf-8")
            diagnosis = {
                "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v4",
                "status": "needs_repair",
                "failure_class": "board_output_lifecycle_frontier_violation",
                "applicability_binding": {
                    "schema_version": "spatialaccagent.diagnosis_applicability_binding.v1",
                    "origin_layer": "board_axi_ddr_wrapped_system",
                    "target_layer": "board_axi_ddr_wrapped_system",
                    "origin_gates": ["case_vcs_functional_sim"],
                    "applicable_rerun_gates": ["case_vcs_functional_sim"],
                    "diagnosed_failure_class": "board_output_lifecycle_frontier_violation",
                    "source_artifacts": [{"path": str(source), "sha256": sha256(source)}],
                },
            }
            result = diagnosis_applicability_report(
                diagnosis,
                {
                    "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                    "failed_current_layer_gates": [
                        {"name": "functional_sim", "status": "fail"}
                    ],
                },
                run_dir=run_dir,
            )
        self.assertTrue(result["executable"])
        self.assertEqual(result["relation"], "current_board_functional_aggregate")

    def test_exact_board_workflow_prefers_current_adapter_runner(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            protocols = root / "tool_protocols.json"
            write_json(
                protocols,
                {
                    "tools": [
                        {
                            "name": "case_vcs_functional_sim",
                            "script_exists": True,
                            "execution": {
                                "argv": ["scripts/verification/legacy_board_wrapper.sh"],
                            },
                        }
                    ]
                },
            )
            runner = (
                Path(__file__).resolve().parents[1]
                / "scripts"
                / "verification"
                / "case_board_vcs_functional.py"
            )
            workflow = build_repair_workflow(
                [
                    {
                        "scope": "regression_rerun",
                        "tool": "case_vcs_functional_sim",
                    }
                ],
                {
                    "artifacts": [
                        {
                            "id": "artifact.input.tool_protocols",
                            "path": str(protocols),
                        }
                    ]
                },
                root / "run",
                {
                    "tools": {
                        "vcs_functional_sim": {
                            "name": "case_vcs_functional_sim",
                            "argv": ["python3", str(runner), "--run-dir", str(root / "run")],
                        }
                    }
                },
            )
        step = workflow["steps"][0]
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["execution"]["source"], "current_exact_board_case_adapter")
        self.assertIn("case_board_vcs_functional.py", step["execution"]["argv"][1])

    def test_exact_board_vcs_rejects_stale_wrapper_command(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            error = exact_board_vcs_rerun_command_error(
                "case_vcs_functional_sim",
                ["scripts/verification/legacy_board_wrapper.sh", str(run_dir)],
                run_dir,
            )
        self.assertIn("canonical case_board_vcs_functional.py", str(error))

    def test_exact_board_vcs_accepts_current_canonical_runner(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            runner = (
                Path(__file__).resolve().parents[1]
                / "scripts"
                / "verification"
                / "case_board_vcs_functional.py"
            )
            error = exact_board_vcs_rerun_command_error(
                "case_vcs_functional_sim",
                ["python3", str(runner), "--run-dir", str(run_dir)],
                run_dir,
            )
        self.assertIsNone(error)

    def test_persisted_exact_board_rerun_rebinds_to_current_adapter(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            runner = (
                Path(__file__).resolve().parents[1]
                / "scripts"
                / "verification"
                / "case_board_vcs_functional.py"
            )
            persisted = {
                "id": "repair_step.00",
                "scope": "regression_rerun",
                "tool": "case_vcs_functional_sim",
                "execution": {
                    "argv": ["scripts/verification/run_qwen_generated_vcs_functional_23.sh"],
                    "cwd": str(run_dir),
                },
            }
            state = {}
            current_adapter = {
                "tools": {
                    "vcs_functional_sim": {
                        "name": "case_vcs_functional_sim",
                        "argv": ["python3", str(runner), "--run-dir", str(run_dir)],
                    }
                }
            }
            with patch(
                "accagent.framework.stage_repair_execute.case_adapter_for_state",
                return_value=current_adapter,
            ):
                rebound = rebind_exact_board_vcs_rerun_step(
                    persisted,
                    state,
                    run_dir,
                )

        self.assertEqual(rebound["execution"]["source"], "current_exact_board_case_adapter")
        self.assertEqual(rebound["execution"]["argv"][1], str(runner))
        self.assertEqual(rebound["execution"]["argv"][3], str(run_dir))

    def test_exact_board_rerun_failure_is_returned_to_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            runner_path = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
            diagnosis_path = run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
            write_json(
                runner_path,
                {
                    "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
                    "phase": "remote_vcs",
                    "status": "fail",
                    "compile": {"status": "pass"},
                    "run": {"status": "fail", "returncode": 86},
                },
            )
            write_json(
                diagnosis_path,
                {
                    "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v4",
                    "diagnosis_status": "ready",
                    "status": "needs_repair",
                    "failure_class": "board_output_lifecycle_frontier_violation",
                    "sources": [str(runner_path)],
                    "repair_handoff": {"agent_should_apply_code_changes": True},
                },
            )
            adapter = {
                "tools": {
                    "vcs": {
                        "name": "case_vcs_functional_sim",
                        "capabilities": [
                            "real_functional_sim",
                            "board_wrapper_functional_sim",
                            "exact_sample_board_wrapper_simulation",
                            "all_target_layers",
                            "elaborated_hierarchy_binding",
                            "structured_axi_protocol_monitors",
                        ],
                        "produces": [str(runner_path)],
                    },
                    "analyzer": {
                        "name": "case_vcs_evidence_analyzer",
                        "capabilities": [
                            "vcs_evidence_analyzer",
                            "semantic_comparison_evidence",
                            "failure_localization_input",
                        ],
                        "produces": [str(diagnosis_path)],
                    },
                }
            }
            result = record_exact_board_rerun_agent_handoff(
                {"status": "fail", "returncode": 1, "summary": "returncode=1"},
                case_adapter=adapter,
                run_dir=run_dir,
            )

        self.assertTrue(result["new_current_real_tool_failure_requires_agent"])
        self.assertEqual(len(result["new_current_real_tool_failure_identity_sha256"]), 64)

    def test_completed_capability_producer_recovers_from_run_report(self) -> None:
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            package_path = run_dir / "repair_execution" / "compile_provenance.json"
            report_path = run_dir / "repair_execution" / "repair_execution_report.json"
            package = {
                "schema_version": "spatialaccagent.vcs_timescale_error_provenance.v1",
                "status": "pass",
                "diagnostic": {
                    "logged_source": "../sources/exact_board_tb.sv",
                    "line": 1,
                },
            }
            write_json(package_path, package)
            write_json(
                report_path,
                {
                    "stage": "repair_execution",
                    "step_results": [
                        {
                            "repair_execution_context": {
                                "verification_scope": "board_axi_ddr_closure",
                                "debug_layer": "board_axi_ddr_wrapped_system",
                            },
                            "debug_layer": "board_axi_ddr_wrapped_system",
                            "step_id": "repair_step.00",
                            "result": {
                                "repair_kind": "vcs_timescale_error_localization",
                                "requires_agent_followup": True,
                                "capability_reports": [str(package_path)],
                            },
                        }
                    ],
                },
            )
            write_json(
                run_dir / "repair_execution" / "loop" / "status.json",
                {
                    "latest_iteration_record": str(
                        run_dir / "repair_execution" / "loop" / "iteration_0001" / "iteration_record.json"
                    )
                },
            )
            write_json(
                run_dir / "repair_execution" / "loop" / "iteration_0001" / "iteration_record.json",
                {
                    "repair_execution_report": json.loads(report_path.read_text(encoding="utf-8"))
                },
            )
            write_json(
                report_path,
                {
                    "stage": "repair_execution",
                    "step_results": [
                        {
                            "debug_layer": "board_axi_ddr_wrapped_system",
                            "result": {
                                "status": "blocked",
                                "requires_agent_followup": False,
                            },
                        }
                    ],
                },
            )

            evidence = prior_capability_producer_evidence(
                {},
                run_dir=run_dir,
                verification_scope="board_axi_ddr_closure",
            )

            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0]["path"], str(package_path))
            self.assertEqual(evidence[0]["sha256"], sha256(package_path))
            self.assertEqual(evidence[0]["package"], package)

    def test_nonfallback_required_capability_materializes_supported_producer(self) -> None:
        feedback = {
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "f" * 64,
            "required_capabilities": [
                {
                    "capability_id": "certified_reload_lifecycle",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "producer_scope": "verification_capability_repair",
                    "target_modules": ["connected_kernel_lifecycle"],
                    "required_evidence": ["two-layer real-tool replay"],
                    "rationale": "generation requires a proved reload protocol",
                }
            ],
        }

        actions = required_capability_repair_actions(feedback)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "certified_reload_lifecycle")
        self.assertEqual(actions[0]["target_modules"], ["connected_kernel_lifecycle"])
        self.assertEqual(
            actions[0]["source"],
            "prior_nonfallback_llm_required_capability",
        )

    def test_vivado_identity_refresh_routes_to_real_board_discovery(self) -> None:
        feedback = {
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "a" * 64,
            "required_capabilities": [
                {
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
            ],
        }

        actions = required_capability_repair_actions(feedback)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], "exact_board_interface_discovery")
        self.assertEqual(actions[0]["repair_tool_role"], "board_interface_discovery")
        self.assertEqual(
            actions[0]["requested_capability_id"],
            "exact_board_vivado_identity_authority_refresh.v1",
        )

    def test_native_vcs_loop_localization_routes_to_exact_board_runner(self) -> None:
        capability = {
            "capability_id": "exact_board_vcs_zero_time_toggle_cone_localization",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "real_board_vcs_runner_and_failure_analyzer",
            "target_modules": ["connected_kernel"],
            "required_evidence": ["native VCS zero-delay loop report"],
            "rationale": "distinguish slow advancing simulation from a delta-cycle loop",
        }

        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "input_fingerprint_sha256": "b" * 64,
                "required_capabilities": [capability],
            }
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], capability["capability_id"])
        self.assertEqual(
            actions[0]["repair_tool_role"],
            "exact_board_vcs_and_failure_analyzer",
        )

    def test_connected_kernel_targeted_replay_routes_to_causal_replay(self) -> None:
        capability = {
            "capability_id": "connected_kernel_boundary_targeted_replay",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "certified_connected_kernel_real_vcs_targeted_replay",
            "target_modules": ["SingleLayerSemanticHarness", "ConnectedObservableLlamaStyleBlock"],
            "required_evidence": ["per-boundary accepted/ready/last trace"],
            "rationale": "localize the first connected-kernel boundary after complete ingress",
        }
        actions = required_capability_repair_actions({
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "c" * 64,
            "required_capabilities": [capability],
        })
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "causal_slice_repair")
        self.assertEqual(actions[0]["repair_kind"], capability["capability_id"])
        self.assertTrue(actions[0]["targeted_replay"])

    def test_connected_kernel_boundary_signal_map_routes_to_read_only_producer(self) -> None:
        capability = {
            "capability_id": "connected_kernel_current_dag_boundary_port_provenance",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "certified_connected_kernel_hierarchical_port_provenance",
            "target_modules": [
                "SingleLayerSemanticHarness",
                "ConnectedObservableLlamaStyleBlock",
                "spatialacc_exact_board_multilayer_tb",
            ],
            "required_evidence": ["hash-bound current-DAG internal signal map"],
            "rationale": "bind real internal signals before adding a board observer",
        }

        actions = required_capability_repair_actions({
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "d" * 64,
            "required_capabilities": [capability],
        })

        self.assertEqual(len(actions), 1)
        self.assertEqual(
            actions[0]["repair_kind"],
            "connected_kernel_current_dag_boundary_signal_map",
        )
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(
            actions[0]["repair_tool_role"],
            "connected_kernel_boundary_signal_map",
        )
        self.assertTrue(actions[0]["read_only_source_mapping"])

    def test_connected_kernel_signal_provenance_alias_routes_to_same_producer(self) -> None:
        capability = {
            "capability_id": "connected_kernel_current_dag_boundary_signal_provenance",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "certified_connected_kernel_hierarchy_provenance",
            "target_modules": ["SingleLayerSemanticHarness"],
            "required_evidence": ["hash-bound current-DAG internal signal map"],
            "rationale": "bind current internal signals before adding a board observer",
        }
        actions = required_capability_repair_actions({
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "f" * 64,
            "required_capabilities": [capability],
        })
        self.assertEqual(len(actions), 1)
        self.assertEqual(
            actions[0]["repair_kind"],
            "connected_kernel_current_dag_boundary_signal_map",
        )
        self.assertTrue(actions[0]["read_only_source_mapping"])

    def test_lifecycle_reconciliation_capability_allows_empty_target_modules(self) -> None:
        capability = {
            "capability_id": "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "causal_repair_context_pack",
            "target_modules": [],
            "required_evidence": ["five hash-bound current reports"],
            "rationale": "reconcile the recorded input-before-start lifecycle contract",
        }

        actions = required_capability_repair_actions({
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "e" * 64,
            "required_capabilities": [capability],
        })

        self.assertEqual(len(actions), 1)
        self.assertEqual(
            actions[0]["repair_kind"],
            "repair.reconcile_exact_board_lifecycle_cctg_observation_contract",
        )
        self.assertEqual(actions[0]["target_modules"], [])
        self.assertTrue(actions[0]["read_only_evidence_reconciliation"])
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")

        workflow = build_repair_workflow(
            actions,
            {},
            Path("/tmp") / "spatialaccagent-lifecycle-workflow",
            {},
        )
        self.assertEqual(workflow["status"], "ready")
        self.assertEqual(workflow["steps"][0]["status"], "ready_for_agent_patch")
        self.assertEqual(workflow["steps"][0]["target_modules"], [])

    def test_other_verification_capability_without_target_stays_blocked(self) -> None:
        workflow = build_repair_workflow(
            [
                {
                    "scope": "verification_capability_repair",
                    "repair_kind": "ordinary_missing_target_capability",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "target_modules": [],
                    "approval_required": False,
                }
            ],
            {},
            Path("/tmp") / "spatialaccagent-missing-target-workflow",
            {},
        )

        self.assertEqual(workflow["status"], "blocked")
        self.assertEqual(workflow["steps"][0]["status"], "blocked")
        self.assertIn("lacks repair_kind or target_modules", workflow["blockers"][0])

    def test_completed_signal_map_uses_explicit_source_reference_fields(self) -> None:
        source_text = (
            "logic signal_valid;\n"
            "logic signal_ready;\n"
            "logic [7:0] signal_payload;\n"
        )
        source = {
            "path": "generated/ConnectedKernel.sv",
            "sha256": "a" * 64,
            "text": source_text,
        }
        refs = {
            "valid": {
                "path": source["path"],
                "sha256": source["sha256"],
                "line_number": 1,
                "source_line": "logic signal_valid;",
            },
            "ready": {
                "path": source["path"],
                "sha256": source["sha256"],
                "line_number": 2,
                "source_line": "logic signal_ready;",
            },
            "payload": {
                "path": source["path"],
                "sha256": source["sha256"],
                "line_number": 3,
                "source_line": "logic [7:0] signal_payload;",
            },
        }
        boundary_id = "edge.data.input.to.stage.main"
        result = validate_connected_kernel_boundary_signal_map(
            {
                "status": "complete",
                "boundary_signal_map": [
                    {
                        "boundary_id": boundary_id,
                        "valid_source": "dut.core.signal_valid",
                        "ready_source": "dut.core.signal_ready",
                        "payload_source": "dut.core.signal_payload",
                        "fire_expression": "dut.core.signal_valid && dut.core.signal_ready",
                        "accepted_count_name": "accepted_count",
                        "first_payload_name": "first_payload",
                        "last_payload_name": "last_payload",
                        "source_refs": refs,
                    }
                ],
                "unresolved_boundaries": [],
            },
            [boundary_id],
            {"source_files": [source]},
        )

        self.assertEqual(result["status"], "pass")

    def test_signal_map_normalizes_unique_exact_source_line(self) -> None:
        source = {
            "path": "generated/ConnectedKernel.sv",
            "sha256": "a" * 64,
            "text": "line zero\nlogic signal_valid;\nlogic signal_ready;\n",
        }
        output, corrections = normalize_connected_kernel_boundary_signal_map_source_refs(
            {
                "boundary_signal_map": [
                    {
                        "boundary_id": "edge.data.input.to.stage.main",
                        "source_refs": {
                            "valid": {
                                "path": source["path"],
                                "sha256": source["sha256"],
                                "line_number": 1,
                                "source_line": "logic signal_valid;",
                            }
                        },
                    }
                ]
            },
            {"source_files": [source]},
        )

        reference = output["boundary_signal_map"][0]["source_refs"]["valid"]
        self.assertEqual(reference["line_number"], 2)
        self.assertEqual(len(corrections), 1)

    def test_cached_signal_map_reuses_verified_superset_for_current_subset(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_text = (
                "logic signal_valid;\n"
                "logic signal_ready;\n"
                "logic [7:0] signal_payload;\n"
            )
            source_sha = hashlib.sha256(source_text.encode()).hexdigest()
            source = {
                "path": "generated/ConnectedKernel.sv",
                "sha256": source_sha,
                "text": source_text,
            }
            def row(boundary_id: str, suffix: str) -> dict:
                refs = {
                    "valid": {"path": source["path"], "sha256": source_sha, "line_number": 1, "source_line": "logic signal_valid;"},
                    "ready": {"path": source["path"], "sha256": source_sha, "line_number": 2, "source_line": "logic signal_ready;"},
                    "payload": {"path": source["path"], "sha256": source_sha, "line_number": 3, "source_line": "logic [7:0] signal_payload;"},
                }
                return {
                    "boundary_id": boundary_id,
                    "valid_source": f"dut.core.signal_valid_{suffix}",
                    "ready_source": f"dut.core.signal_ready_{suffix}",
                    "payload_source": f"dut.core.signal_payload_{suffix}",
                    "fire_expression": f"dut.core.signal_valid_{suffix} && dut.core.signal_ready_{suffix}",
                    "accepted_count_name": f"accepted_{suffix}",
                    "first_payload_name": f"first_{suffix}",
                    "last_payload_name": f"last_{suffix}",
                    "source_refs": refs,
                }
            # The expressions must contain an identifier present on the cited
            # source line; use the same names as the source for this fixture.
            first = row("edge.first", "")
            first["valid_source"] = "dut.core.signal_valid"
            first["ready_source"] = "dut.core.signal_ready"
            first["payload_source"] = "dut.core.signal_payload"
            first["fire_expression"] = "dut.core.signal_valid && dut.core.signal_ready"
            second = json.loads(json.dumps(first))
            second["boundary_id"] = "edge.second"
            package = {
                "repair_kind": "connected_kernel_current_dag_boundary_signal_map",
                "status": "pass",
                "validation": {"status": "pass"},
                "required_boundary_ids": ["edge.first", "edge.second"],
                "source_bundle": {"source_files": [source, {"path": "unused.sv", "sha256": "a" * 64, "text": "unused\n"}]},
                "elaborated_hierarchy": {"path": str(Path("hierarchy.json").resolve()), "sha256": "b" * 64},
                "boundary_signal_map": [first, second],
                "agent_record": {"path": str(root / "agent.json")},
            }
            record = {"mode": "llm", "used_fallback": False, "output": {
                "status": "complete", "boundary_signal_map": [first, second], "unresolved_boundaries": []
            }}
            write_json(root / "agent.json", record)
            write_json(root / "map.json", package)
            # A later failed retry can overwrite the fixed Agent result path.
            # The passing capability package remains the durable authority.
            write_json(root / "agent.json", {"mode": "llm", "error": "upstream unavailable"})
            request = {
                "required_boundary_ids": ["edge.first"],
                "source_bundle": {"source_files": [source]},
                "elaborated_hierarchy": {"path": "hierarchy.json", "sha256": "b" * 64},
            }
            reused = _matching_cached_boundary_signal_map_record(request, root / "map.json")
            self.assertIsNotNone(reused)
            self.assertEqual(reused["mode"], "validated_capability_cache")
            self.assertEqual(
                [r["boundary_id"] for r in reused["output"]["boundary_signal_map"]],
                ["edge.first"],
            )

    def test_cctg_single_layer_replay_routes_to_read_only_causal_replay(self) -> None:
        capability = {
            "capability_id": "cctg_connected_kernel_boundary_replay",
            "debug_layer": "single_transformer_layer_functional",
            "producer_scope": "real_vcs_single_layer_boundary_localization",
            "target_modules": ["SingleLayerSemanticHarness"],
            "required_evidence": ["real VCS CCTG boundary trace"],
            "rationale": "localize the first contradictory connected-kernel boundary",
        }
        actions = required_capability_repair_actions({
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "c" * 64,
            "required_capabilities": [capability],
        })

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "causal_slice_repair")
        self.assertEqual(actions[0]["debug_layer"], "single_transformer_layer_kernel")
        self.assertTrue(actions[0]["targeted_replay"])
        self.assertEqual(actions[0]["repair_gate"], "case_single_layer_functional")

    def test_board_requested_cctg_replay_routes_to_connected_kernel_scope(self) -> None:
        capability = {
            "capability_id": "connected_kernel_cctg_contradiction_targeted_replay",
            "debug_layer": "single_transformer_layer_connected_kernel",
            "producer_scope": "certified_connected_kernel_current_layer_replay",
            "target_modules": ["ConnectedObservableLlamaStyleBlock"],
            "required_evidence": ["fresh CCTG boundary terminal observations"],
            "rationale": "resolve an explicit board-to-connected-kernel contradiction",
        }

        actions = required_capability_repair_actions({
            "status": "blocked",
            "validation": {"status": "pass"},
            "input_fingerprint_sha256": "c" * 64,
            "required_capabilities": [capability],
        })

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "causal_slice_repair")
        self.assertEqual(
            actions[0]["repair_kind"],
            "connected_kernel_cctg_contradiction_targeted_replay",
        )
        self.assertEqual(actions[0]["debug_layer"], "single_transformer_layer_kernel")
        self.assertTrue(actions[0]["targeted_replay"])

    def test_completed_single_layer_cctg_is_available_to_board_agent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            package = root / "cctg_package.json"
            write_json(
                package,
                {
                    "status": "pass",
                    "cctg_boundary_replay_evidence": {
                        "fresh_remote_vcs_execution_observed": True,
                        "boundary_liveness_status": "pass",
                    },
                },
            )
            record = root / "repair_execution" / "loop" / "iteration_0001" / "iteration_record.json"
            write_json(
                record,
                {
                    "repair_execution_report": {
                        "stage": "repair_execution",
                        "step_results": [
                            {
                                "step_id": "repair_step.cctg",
                                "scope": "causal_slice_repair",
                                "repair_execution_context": {
                                    "debug_layer": "single_transformer_layer_kernel"
                                },
                                "result": {
                                    "requires_agent_followup": True,
                                    "repair_kind": "cctg_connected_kernel_boundary_replay",
                                    "capability_reports": [str(package)],
                                },
                            }
                        ],
                    }
                },
            )

            evidence = prior_capability_producer_evidence(
                {},
                run_dir=root,
                verification_scope="board_axi_ddr_closure",
            )

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["source_verification_scope"], "single_layer_closure")
        self.assertTrue(evidence[0]["cross_layer_promotion"])

    def test_complete_cross_layer_cctg_precedes_without_hiding_board_provenance(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            board_package = root / "board_provenance.json"
            cctg_package = root / "cctg_package.json"
            write_json(board_package, {"status": "pass"})
            write_json(
                cctg_package,
                {
                    "status": "pass",
                    "cctg_boundary_replay_evidence": {
                        "fresh_remote_vcs_execution_observed": True,
                        "boundary_liveness_status": "pass",
                    },
                },
            )
            current_report = root / "repair_execution" / "repair_execution_report.json"
            write_json(
                current_report,
                {
                    "stage": "repair_execution",
                    "step_results": [
                        {
                            "step_id": "repair_step.board_provenance",
                            "scope": "verification_capability_repair",
                            "repair_execution_context": {
                                "debug_layer": "board_axi_ddr_wrapped_system"
                            },
                            "result": {
                                "requires_agent_followup": True,
                                "repair_kind": "vcs_compile_diagnostic_source_provenance",
                                "capability_reports": [str(board_package)],
                            },
                        }
                    ],
                },
            )
            record = root / "repair_execution" / "loop" / "iteration_0001" / "iteration_record.json"
            write_json(
                record,
                {
                    "repair_execution_report": {
                        "stage": "repair_execution",
                        "step_results": [
                            {
                                "step_id": "repair_step.cctg",
                                "scope": "causal_slice_repair",
                                "repair_execution_context": {
                                    "debug_layer": "single_transformer_layer_kernel"
                                },
                                "result": {
                                    "requires_agent_followup": True,
                                    "repair_kind": "cctg_connected_kernel_boundary_replay",
                                    "capability_reports": [str(cctg_package)],
                                },
                            }
                        ],
                    }
                },
            )

            evidence = prior_capability_producer_evidence(
                {}, run_dir=root, verification_scope="board_axi_ddr_closure"
            )

        self.assertEqual(len(evidence), 2)
        self.assertEqual(evidence[0]["path"], str(cctg_package))
        self.assertTrue(evidence[0]["cross_layer_promotion"])
        self.assertEqual(evidence[1]["path"], str(board_package))
        self.assertFalse(evidence[1]["cross_layer_promotion"])

    def test_supported_capability_survives_invalid_observation_metadata(self) -> None:
        capability = {
            "capability_id": "cctg_connected_kernel_boundary_replay",
            "debug_layer": "single_transformer_layer_functional",
            "producer_scope": "real_vcs_single_layer_boundary_localization",
            "target_modules": ["SingleLayerSemanticHarness"],
            "required_evidence": ["real VCS CCTG boundary trace"],
            "rationale": "collect evidence before proposing a lower-layer repair",
        }
        output = {
            "status": "blocked",
            "file_edits": [],
            "required_capabilities": [capability],
            "adaptive_observation_decision": {
                "mode": "direct_executed_contradiction"
            },
        }

        handoff = supported_required_capability_handoff(output)
        disposition = repair_loop_disposition({
            "status": "incomplete",
            "errors": ["observation metadata is stale"],
            "step_results": [{
                "result": {
                    "status": "blocked",
                    "framework_action_required": handoff["supported"],
                    "required_capabilities": handoff["required_capabilities"],
                }
            }],
        })

        self.assertTrue(handoff["supported"])
        self.assertEqual(disposition["status"], "continue")
        self.assertTrue(disposition["upstream_capability_replan_required"])

    def test_completed_board_triggered_lower_layer_recheck_returns_to_board_plan(self) -> None:
        disposition = repair_loop_disposition(
            {
                "status": "ready",
                "errors": [],
                "step_results": [
                    {
                        "result": {
                            "status": "pass",
                            "stage_passed": True,
                            "completed_board_lower_layer_recheck": {
                                "status": "pass",
                                "source_binding": {
                                    "input_fingerprint_sha256": "a" * 64,
                                    "board_trace_sha256": "b" * 64,
                                    "lower_layer_certificate_sha256": "c" * 64,
                                },
                            },
                        }
                    }
                ],
            }
        )

        self.assertEqual(disposition["status"], "continue")
        self.assertTrue(disposition["exact_board_failure_handoff"])
        self.assertEqual(
            disposition["completed_board_lower_layer_rechecks"][0]["status"],
            "pass",
        )

    def test_vcs_timescale_localization_routes_to_read_only_compile_provenance(self) -> None:
        capability = {
            "capability_id": "vcs_timescale_error_localization",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "real_board_vcs_compile_provenance",
            "target_modules": ["spatialacc_exact_board_multilayer_tb"],
            "required_evidence": ["staged source context and ordered VCS argv"],
            "rationale": "the existing compiler diagnostic must be localized before another edit",
        }

        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "input_fingerprint_sha256": "d" * 64,
                "required_capabilities": [capability],
            }
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], "vcs_timescale_error_localization")
        self.assertEqual(actions[0]["repair_tool_role"], "exact_board_vcs_compile_provenance")

    def test_vcs_compile_provenance_alias_routes_to_canonical_read_only_producer(self) -> None:
        capability = {
            "capability_id": "board_vcs_itsfm_source_provenance",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "remote_vcs_runner",
            "target_modules": ["spatialacc_exact_board_multilayer_tb"],
            "required_evidence": ["source path, line, and compile ordering"],
            "rationale": "localize the preserved compiler diagnostic before editing",
        }

        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "input_fingerprint_sha256": "e" * 64,
                "required_capabilities": [capability],
            }
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(
            actions[0]["repair_kind"], "vcs_compile_diagnostic_source_provenance"
        )
        self.assertEqual(
            actions[0]["requested_capability_id"],
            "board_vcs_itsfm_source_provenance",
        )

    def test_remote_stage_pruning_recovery_routes_same_exact_board_vcs_chain(self) -> None:
        capability = {
            "capability_id": "vcs_remote_stage_pruning_environment_recovery",
            "debug_layer": "board_axi_ddr_wrapped_system",
            "producer_scope": "remote_vcs_stage_pruning_environment",
            "target_modules": ["board_tb"],
            "required_evidence": ["remote prune return code"],
            "rationale": "recover remote prune before retrying unchanged sources",
        }
        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "input_fingerprint_sha256": "f" * 64,
                "required_capabilities": [capability],
            }
        )
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "regression_rerun")
        self.assertEqual(actions[0]["tool"], "case_vcs_functional_sim")
        self.assertTrue(actions[0]["environment_recovery_required"])

    def test_vcs_timescale_provenance_is_hash_bound_and_does_not_run_vcs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            verification = run_dir / "verification"
            source = verification / "board_simulation" / "vcs_stage" / "sources" / "BoardTb.sv"
            source.parent.mkdir(parents=True)
            source.write_text(
                "module BoardTb;\n  timeunit 1ns;\n  timeprecision 1ps;\nendmodule\n",
                encoding="utf-8",
            )
            log = verification / "board_simulation" / "reports" / "compile.log"
            log.parent.mkdir(parents=True)
            log.write_text(
                "Parsing design file '../sources/BoardTb.sv'\n\n"
                "Error-[ITSFM] Illegal `timescale for module\n"
                "../sources/BoardTb.sv, 1\n"
                "  Module \"BoardTb\" has `timescale but previous module(s)/package(s) do not.\n",
                encoding="utf-8",
            )
            runner = verification / "vcs" / "case_board_vcs_functional.json"
            write_json(runner, {"compile": {"argv": ["ssh", "remote-vcs"]}})
            executed = verification / "board_simulation" / "board_simulation_executed_manifest.json"
            write_json(
                executed,
                {
                    "compile_command": (
                        "(cd vcs_work && vlogan -full64 ../sources/BoardTb.sv) "
                        ">> reports/compile.log 2>&1; (cd vcs_work && vcs BoardTb)"
                    ),
                    "payload": [
                        {"path": "sources/BoardTb.sv", "sha256": sha256(source)}
                    ],
                },
            )
            manifest = verification / "board_simulation" / "board_simulation_manifest.json"
            write_json(manifest, {"schema_version": "test"})
            generated = run_dir / "generated" / "board_integration" / "BoardTb.sv"
            generated.parent.mkdir(parents=True)
            generated.write_bytes(source.read_bytes())
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir()

            result = localize_vcs_timescale_error_provenance(
                run_dir=run_dir,
                out_dir=out_dir,
                step={"id": "repair_step.01", "action": {"target_modules": ["BoardTb"]}},
            )

            self.assertEqual(result["status"], "pass")
            package = json.loads(Path(result["context_package"]).read_text(encoding="utf-8"))
            self.assertTrue(package["policy"]["read_only"])
            self.assertFalse(package["policy"]["vcs_rerun"])
            self.assertEqual(package["diagnostic"]["line"], 1)
            self.assertEqual(
                package["source"]["classification"], "editable_generated_board_source"
            )
            self.assertEqual(
                package["compile_plan"]["ordered_vlogan_sources"][0]["sha256"],
                sha256(source),
            )

    def test_generic_vcs_provenance_preserves_environment_failure_without_compile_log(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            runner = run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
            diagnosis = run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json"
            write_json(runner, {
                "status": "fail",
                "compile": {"status": "fail", "returncode": 125, "failure_class": "remote_stage_cleanup_failure"},
                "simulation": {"status": "not_run"},
                "remote_stage_cleanup": {"status": "pass"},
                "remote_stage_prune": {"status": "fail", "returncode": 255},
                "remote_workdir": "/remote/workdir",
            })
            write_json(diagnosis, {
                "diagnosis_status": "ready",
                "failure_class": "vcs_execution_environment_failure",
                "failure_evidence": {
                    "first_real_error": "elaborated hierarchy report is invalid",
                    "repair_scope": "execution_environment_retry",
                    "compile": {"status": "fail", "remote_state": "not_run"},
                },
            })
            result = preserve_vcs_compile_diagnostic_provenance(
                run_dir=run_dir,
                out_dir=run_dir / "out",
                step={"id": "repair_step.00", "action": {"target_modules": ["board_tb"]}},
            )
            self.assertEqual(result["status"], "pass")
            package = json.loads(Path(result["context_package"]).read_text(encoding="utf-8"))
            self.assertEqual(package["diagnosis"]["failure_class"], "vcs_execution_environment_failure")
            self.assertEqual(package["runner"]["remote_stage_prune"]["returncode"], 255)

    def test_generic_vcs_provenance_localizes_undeclared_generated_identifier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            verification = run_dir / "verification"
            staged = verification / "board_simulation" / "vcs_stage" / "sources" / "BoardTb.sv"
            staged.parent.mkdir(parents=True)
            staged.write_text(
                "module BoardTb;\n  initial if (index >= BEATS_PER_TOKEN) ;\nendmodule\n",
                encoding="utf-8",
            )
            generated = run_dir / "generated" / "board_integration" / "BoardTb.sv"
            generated.parent.mkdir(parents=True)
            generated.write_bytes(staged.read_bytes())
            log = verification / "board_simulation" / "reports" / "compile.log"
            log.parent.mkdir(parents=True)
            log.write_text(
                "Error-[IND] Identifier not declared\n../sources/BoardTb.sv, 2\n"
                "  Identifier 'BEATS_PER_TOKEN' has not been declared yet.\n",
                encoding="utf-8",
            )
            runner = verification / "vcs" / "case_board_vcs_functional.json"
            write_json(runner, {"status": "fail", "compile": {"status": "fail", "returncode": 1}})
            diagnosis = verification / "case_diagnostics" / "vcs_functional_diagnosis.json"
            write_json(diagnosis, {
                "diagnosis_status": "ready",
                "failure_class": "vcs_compile_failure",
                "failure_evidence": {
                    "first_real_error": "Error-[IND] Identifier not declared",
                    "compile": {"status": "fail", "remote_state": "done"},
                },
            })
            source_id = "generated_tb.0000"
            executed = verification / "board_simulation" / "board_simulation_executed_manifest.json"
            write_json(executed, {
                "source_files": [{
                    "source_id": source_id,
                    "path": str(generated),
                    "role": "generated_board_testbench",
                    "sha256": sha256(staged),
                }],
                "vcs_compile_plan": {"ordered_commands": [{
                    "executable": "vlogan",
                    "argv": ["-full64", "-sverilog", "+incdir+../sources", {"source_id": source_id}],
                    "source_ids": [source_id],
                }]},
            })
            write_json(verification / "board_simulation" / "board_simulation_manifest.json", {"status": "ready"})

            result = preserve_vcs_compile_diagnostic_provenance(
                run_dir=run_dir,
                out_dir=run_dir / "out",
                step={"id": "repair_step.00", "action": {"target_modules": ["BoardTb"]}},
            )

            self.assertEqual(result["status"], "pass")
            package = json.loads(Path(result["context_package"]).read_text(encoding="utf-8"))
            self.assertTrue(package["decision_contract"]["provenance_complete"])
            self.assertEqual(package["compiler_diagnostic"]["identifier"], "BEATS_PER_TOKEN")
            self.assertEqual(package["compiler_diagnostic"]["line"], 2)
            self.assertTrue(package["source_provenance"]["generated_matches_staged"])
            self.assertEqual(package["compile_plan"]["language_modes"], ["-sverilog"])
            self.assertEqual(package["compile_plan"]["ordered_sources"][0]["source_id"], source_id)

    def test_vcs_provenance_reads_xmre_token_as_the_missing_identifier(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            verification = run_dir / "verification"
            staged = (
                verification
                / "board_simulation"
                / "vcs_stage"
                / "sources"
                / "BoardTb.sv"
            )
            generated = run_dir / "generated" / "board_integration" / "BoardTb.sv"
            source = "module BoardTb;\n  assign seen = dut.missing_probe;\nendmodule\n"
            staged.parent.mkdir(parents=True)
            generated.parent.mkdir(parents=True)
            staged.write_text(source, encoding="utf-8")
            generated.write_text(source, encoding="utf-8")
            compile_log = verification / "board_simulation" / "reports" / "compile.log"
            compile_log.parent.mkdir(parents=True)
            compile_log.write_text(
                "Error-[XMRE] Cross-module reference resolution error\n"
                "../sources/BoardTb.sv, 2\n"
                "  token 'missing_probe'. Originating module 'BoardTb'.\n",
                encoding="utf-8",
            )
            write_json(
                verification / "vcs" / "case_board_vcs_functional.json",
                {"status": "fail", "compile": {"status": "fail"}},
            )
            write_json(
                verification / "case_diagnostics" / "vcs_functional_diagnosis.json",
                {
                    "diagnosis_status": "ready",
                    "failure_class": "vcs_compile_failure",
                    "failure_evidence": {
                        "first_real_error": "Error-[XMRE] Cross-module reference resolution error",
                        "compile": {"status": "fail", "remote_state": "done"},
                    },
                },
            )
            source_id = "generated_tb.0000"
            write_json(
                verification
                / "board_simulation"
                / "board_simulation_executed_manifest.json",
                {
                    "source_files": [
                        {
                            "source_id": source_id,
                            "path": str(generated),
                            "role": "generated_board_testbench",
                            "sha256": sha256(staged),
                        }
                    ],
                    "vcs_compile_plan": {
                        "ordered_commands": [
                            {
                                "executable": "vlogan",
                                "argv": ["-sverilog", {"source_id": source_id}],
                                "source_ids": [source_id],
                            }
                        ]
                    },
                },
            )
            write_json(
                verification / "board_simulation" / "board_simulation_manifest.json",
                {"status": "ready"},
            )

            result = preserve_vcs_compile_diagnostic_provenance(
                run_dir=run_dir,
                out_dir=run_dir / "out",
                step={"id": "repair_step.00", "action": {"target_modules": ["BoardTb"]}},
            )

            package = json.loads(
                Path(result["context_package"]).read_text(encoding="utf-8")
            )
            self.assertEqual(package["compiler_diagnostic"]["identifier"], "missing_probe")
            self.assertTrue(package["decision_contract"]["provenance_complete"])

    def make_record(
        self,
        root: Path,
        *,
        name: str = "current",
        summary: str = "current blocked feedback",
        producer_scope: str = "verification_capability_repair",
        target_modules: list[str] | None = None,
        repair_debug_layer: str = "board_axi_ddr_wrapped_system",
    ) -> Path:
        prompt = root / f"{name}_prompt.md"
        prompt.write_text(f"prompt for {name}", encoding="utf-8")
        output = {
            "status": "blocked",
            "summary": summary,
            "blocked_reasons": [f"{name} blocker"],
            "required_capabilities": [
                {
                    "capability_id": f"{name}.capability",
                    "debug_layer": "board_axi_ddr_wrapped_system",
                    "producer_scope": producer_scope,
                    **(
                        {"target_modules": target_modules}
                        if target_modules is not None
                        else {}
                    ),
                    "required_evidence": ["real VCS evidence"],
                    "rationale": "missing certified lifecycle",
                }
            ],
        }
        record_path = root / f"{name}_result.json"
        write_json(
            record_path,
            {
                "schema_version": "spatialaccagent.stage_worker_record.v0",
                "agent": "exact_board_integration_generation_agent",
                "stage": "repair_execution",
                "mode": "llm",
                "used_fallback": False,
                "error": None,
                "result_path": str(record_path),
                "request_path": str(prompt),
                "prompt_hash": sha256(prompt),
                "raw_text": json.dumps(output, sort_keys=True),
                "output": output,
                "repair_execution_context": {
                    "schema_version": "spatialaccagent.repair_execution_agent_context.v1",
                    "debug_layer": repair_debug_layer,
                },
            },
        )
        return record_path

    def make_report(
        self,
        path: Path,
        record_path: Path,
        *,
        repair_feedback_artifacts: list[dict] | None = None,
    ) -> None:
        result = {
            "status": "blocked",
            "llm_record": str(record_path),
        }
        if repair_feedback_artifacts is not None:
            result["repair_feedback_artifacts"] = repair_feedback_artifacts
        write_json(
            path,
            {
                "schema_version": "spatialaccagent.repair_execution_report.v0",
                "stage": "repair_execution",
                "status": "incomplete",
                "errors": ["repair_step.00 blocked"],
                "step_results": [
                    {
                        "step_id": "repair_step.00",
                        "scope": "verification_capability_repair",
                        "result": result,
                    }
                ],
            },
        )

    def make_deterministic_feedback_reference(
        self,
        root: Path,
        *,
        name: str = "preflight",
    ) -> tuple[Path, dict]:
        artifact_path = root / f"{name}.json"
        write_json(
            artifact_path,
            {
                "schema_version": "spatialaccagent.exact_board_memory_runtime_preparation.v1",
                "status": "blocked",
                "summary": "deterministic board runtime contract validation failed",
                "blockers": ["weight image exceeds the selected physical region"],
                "validation_errors": ["final-layer switch must be disabled"],
            },
        )
        context = {
            "schema_version": "spatialaccagent.repair_execution_agent_context.v1",
            "debug_layer": "board_axi_ddr_wrapped_system",
        }
        return artifact_path, {
            "schema_version": REPAIR_FEEDBACK_ARTIFACT_REF_SCHEMA_VERSION,
            "kind": "deterministic_preflight",
            "path": str(artifact_path),
            "sha256": sha256(artifact_path),
            "repair_execution_context": context,
        }

    def test_source_sacg_artifact_wins_over_stale_default_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            current_record = self.make_record(root, name="current")
            current_report = root / "bound" / "current_report.json"
            self.make_report(current_report, current_record)

            stale_record = self.make_record(root, name="stale", summary="stale feedback")
            stale_report = run_dir / "repair_execution" / "repair_execution_report.json"
            self.make_report(stale_report, stale_record)
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(current_report),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(state, run_dir)

            self.assertEqual(feedback["validation"]["status"], "pass")
            self.assertEqual(feedback["report"]["path"], str(current_report.resolve()))
            self.assertEqual(feedback["report"]["sha256"], sha256(current_report))
            self.assertEqual(feedback["summary"], "current blocked feedback")
            self.assertNotIn("stale feedback", json.dumps(feedback))
            self.assertEqual(len(feedback["input_fingerprint_sha256"]), 64)
            record = feedback["llm_records"][0]
            self.assertEqual(record["path"], str(current_record.resolve()))
            self.assertEqual(record["sha256"], sha256(current_record))
            self.assertEqual(len(record["input_fingerprint_sha256"]), 64)
            self.assertEqual(
                feedback["required_capabilities"][0]["capability_id"],
                "current.capability",
            )

    def test_exact_board_self_scope_is_not_migrated_to_generic_producer(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_path = self.make_record(
                root,
                producer_scope="exact_board_integration_generation",
                target_modules=["connected_kernel_lifecycle"],
            )
            report_path = root / "report.json"
            self.make_report(report_path, record_path)
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(state, root)
            actions = required_capability_repair_actions(feedback)

            self.assertEqual(feedback["validation"]["status"], "pass")
            capability = feedback["required_capabilities"][0]
            self.assertEqual(
                capability["producer_scope"], "exact_board_integration_generation"
            )
            self.assertEqual(actions, [])

    def test_prior_feedback_from_another_layer_is_historical_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_path = self.make_record(root, summary="old board blocker")
            report_path = root / "report.json"
            self.make_report(report_path, record_path)
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(
                state,
                root,
                expected_debug_layer="single_transformer_layer_kernel",
            )

            self.assertEqual(feedback["status"], "historical_only")
            self.assertEqual(feedback["blockers"], [])
            self.assertEqual(feedback["required_capabilities"], [])
            self.assertEqual(feedback["llm_records"], [])
            self.assertNotIn("old board blocker", json.dumps(feedback))
            self.assertEqual(
                feedback["scope_selection"]["excluded_unbound_or_other_layer_record_count"],
                1,
            )

    def test_historical_diagnosis_projection_omits_raw_diagnostic_content(self) -> None:
        projection = diagnosis_prompt_projection(
            {
                "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v3",
                "failure_class": "historical_board_failure",
                "board_wrapper_identity": {"secret": "old board evidence"},
            },
            {
                "schema_version": "spatialaccagent.diagnosis_applicability_report.v1",
                "status": "historical_only",
                "executable": False,
                "current_layer": "single_transformer_layer_kernel",
                "reason": "diagnosis is stale",
            },
        )

        self.assertEqual(projection["status"], "historical_only")
        serialized = json.dumps(projection)
        self.assertNotIn("historical_board_failure", serialized)
        self.assertNotIn("old board evidence", serialized)

    def test_board_generation_contract_breaks_pre_evidence_cycle(self) -> None:
        rules = " ".join(board_integration_prompt_rules("bootstrap"))

        self.assertIn("before any current VCS evidence exists", rules)
        self.assertIn("missing preflight, VCS, protocol, or runtime reports", rules)
        self.assertIn("Bind the discovered compute-slot module", rules)
        self.assertIn("exactly one certified connected Transformer-block kernel", rules)
        self.assertIn("elastic ready/valid operator pipeline", rules)
        self.assertIn("two atomic weight banks", rules)
        self.assertIn("next-layer prefetch overlapping current compute", rules)
        self.assertIn("activation ping-pong", rules)
        self.assertIn("complete runtime/weight reload before each kernel start", rules)
        self.assertIn("real discovered compute-slot ABI", rules)
        self.assertIn("all five AXI channels", rules)
        self.assertIn("no fixed completion timeout", rules)

    def test_tampered_llm_output_fails_closed_without_capability_leak(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_path = self.make_record(root)
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["output"]["required_capabilities"][0]["capability_id"] = "tampered"
            write_json(record_path, record)
            report_path = root / "report.json"
            self.make_report(report_path, record_path)
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(state, root)

            self.assertEqual(feedback["status"], "invalid")
            self.assertEqual(feedback["required_capabilities"], [])
            self.assertEqual(feedback["llm_records"], [])
            self.assertIn("differs from raw LLM JSON", " ".join(feedback["blockers"]))

    def test_hash_bound_deterministic_feedback_overrides_ready_llm_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_path = self.make_record(root, name="planner")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["output"]["status"] = "ready"
            record["raw_text"] = json.dumps(record["output"], sort_keys=True)
            write_json(record_path, record)
            _artifact_path, feedback_reference = self.make_deterministic_feedback_reference(root)
            report_path = root / "report.json"
            self.make_report(
                report_path,
                record_path,
                repair_feedback_artifacts=[feedback_reference],
            )
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(
                state,
                root,
                expected_debug_layer="board_axi_ddr_wrapped_system",
            )

            self.assertEqual(feedback["validation"]["status"], "pass")
            self.assertEqual(feedback["status"], "blocked")
            self.assertIn(
                "weight image exceeds the selected physical region",
                feedback["blockers"],
            )
            self.assertIn(
                "final-layer switch must be disabled",
                feedback["execution_errors"],
            )
            self.assertEqual(len(feedback["deterministic_feedback"]), 1)
            self.assertEqual(
                feedback["deterministic_feedback"][0]["kind"],
                "deterministic_preflight",
            )

    def test_tampered_deterministic_feedback_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_path = self.make_record(root)
            artifact_path, feedback_reference = self.make_deterministic_feedback_reference(root)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            artifact["blockers"].append("tampered failure")
            write_json(artifact_path, artifact)
            report_path = root / "report.json"
            self.make_report(
                report_path,
                record_path,
                repair_feedback_artifacts=[feedback_reference],
            )
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(state, root)

            self.assertEqual(feedback["status"], "invalid")
            self.assertIn("SHA-256 does not match", " ".join(feedback["blockers"]))

    def test_missing_referenced_llm_record_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.json"
            self.make_report(report_path, root / "missing_record.json")
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    }
                ]
            }

            feedback = prior_repair_execution_feedback(state, root)

            self.assertEqual(feedback["status"], "invalid")
            self.assertEqual(feedback["required_capabilities"], [])
            self.assertIn("is missing", " ".join(feedback["blockers"]))

    def test_build_repair_plan_replays_exact_board_action_after_self_block(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            verification_path = root / "verification.json"
            write_json(
                verification_path,
                {
                    "status": "fail",
                    "results": [
                        {
                            "checker": "real_tool.case_multilayer_pipeline",
                            "status": "fail",
                            "summary": "multi-layer harness missing",
                        }
                    ],
                },
            )
            record_path = self.make_record(
                root,
                producer_scope="exact_board_integration_generation",
                target_modules=["connected_kernel_lifecycle"],
            )
            report_path = root / "report.json"
            self.make_report(report_path, record_path)
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage7.verification_result",
                        "path": str(verification_path),
                    },
                    {
                        "id": "artifact.stage8.repair_execution_report",
                        "path": str(report_path),
                    },
                ]
            }
            localization = {"status": "verification_capability_gap"}
            loop = {
                "failure_kind": "verification_capability_gap",
                "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                "failed_current_layer_gates": [
                    {"name": "case_multilayer_pipeline", "status": "fail"}
                ],
            }
            with patch(
                "accagent.framework.stage_repair.case_adapter_for_state",
                return_value={},
            ), patch(
                "accagent.framework.stage_repair.enrich_verification_with_tool_reports",
                side_effect=lambda value, _run_dir, _adapter: value,
            ), patch(
                "accagent.framework.stage_repair.load_vcs_diagnosis",
                return_value=None,
            ), patch(
                "accagent.framework.stage_repair.load_debug_closure_localization",
                return_value=localization,
            ), patch(
                "accagent.framework.stage_repair.build_repair_loop_report",
                return_value=loop,
            ):
                plan = build_repair_plan(state, root)

            feedback = plan["diagnostics"]["prior_repair_execution_feedback"]
            self.assertEqual(feedback["status"], "blocked")
            self.assertEqual(feedback["validation"]["status"], "pass")
            self.assertEqual(len(plan["repair_actions"]), 1)
            self.assertEqual(
                plan["repair_actions"][0]["repair_kind"],
                "exact_board_integration_harness",
            )
            self.assertEqual(
                plan["repair_actions"][0]["source"],
                "hierarchical_repair_loop",
            )
            self.assertEqual(plan["repair_workflow"]["status"], "ready")

    def test_rematerialized_lower_layer_capability_is_projected_when_hash_bound(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            package_path = write_passing_connected_kernel_replay_package(run_dir)

            evidence = rematerialized_lower_layer_capability_evidence(run_dir)

        self.assertEqual(len(evidence), 1)
        self.assertEqual(
            evidence[0]["capability_id"],
            "connected_kernel_cctg_contradiction_targeted_replay",
        )
        self.assertEqual(evidence[0]["context_package"]["path"], str(package_path))
        self.assertTrue(evidence[0]["direct_lifecycle"]["egress_complete"])

    def test_rematerialized_lower_layer_capability_rejects_stale_direct_hash(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            write_passing_connected_kernel_replay_package(
                run_dir,
                trace_sha256="0" * 64,
            )

            evidence = rematerialized_lower_layer_capability_evidence(run_dir)

        self.assertEqual(evidence, [])

    def test_repair_plan_omits_completed_connected_kernel_replay_action(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            verification_path = run_dir / "verification.json"
            write_json(
                verification_path,
                {
                    "status": "fail",
                    "results": [
                        {
                            "checker": "real_tool.case_axi_ddr_interface",
                            "status": "fail",
                            "summary": "board authority binding is incomplete",
                        }
                    ],
                },
            )
            write_passing_connected_kernel_replay_package(run_dir)
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage7.verification_result",
                        "path": str(verification_path),
                    }
                ]
            }
            lower_replay = {
                "scope": "causal_slice_repair",
                "repair_kind": "connected_kernel_cctg_contradiction_targeted_replay",
            }
            board_action = {
                "scope": "verification_capability_repair",
                "repair_kind": "exact_board_integration_harness",
            }
            with patch(
                "accagent.framework.stage_repair.case_adapter_for_state",
                return_value={},
            ), patch(
                "accagent.framework.stage_repair.enrich_verification_with_tool_reports",
                side_effect=lambda value, _run_dir, _adapter: value,
            ), patch(
                "accagent.framework.stage_repair.load_vcs_diagnosis",
                return_value=None,
            ), patch(
                "accagent.framework.stage_repair.load_debug_closure_localization",
                return_value={},
            ), patch(
                "accagent.framework.stage_repair.build_repair_loop_report",
                return_value={
                    "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                    "failed_current_layer_gates": [
                        {"name": "case_axi_ddr_interface", "status": "fail"}
                    ],
                },
            ), patch(
                "accagent.framework.stage_repair.prior_repair_execution_feedback",
                return_value={
                    "status": "blocked",
                    "validation": {"status": "pass"},
                    "required_capabilities": [lower_replay],
                },
            ), patch(
                "accagent.framework.stage_repair.required_capability_repair_actions",
                return_value=[lower_replay],
            ), patch(
                "accagent.framework.stage_repair.build_repair_actions",
                return_value=[board_action],
            ), patch(
                "accagent.framework.stage_repair.build_repair_workflow",
                return_value={"status": "ready", "steps": []},
            ):
                plan = build_repair_plan(state, run_dir)

        self.assertEqual(plan["repair_actions"], [board_action])
        self.assertEqual(len(plan["diagnostics"]["completed_lower_layer_capabilities"]), 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
