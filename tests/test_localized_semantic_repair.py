import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.repair_loop import failure_kind
from accagent.framework.stage_repair import build_repair_actions, reconcile_repair_workflow_with_llm
from accagent.framework.stage_repair_execute import authorize_localized_semantic_repair_bundle
from accagent.framework.stage_repair_execute import (
    broad_semantic_phase_requested,
    localized_template_instrumentation_already_collected,
    localized_template_instrumentation_requested,
    semantic_harness_validation_output,
)


class LocalizedSemanticRepairTest(TestCase):
    def test_localized_action_is_not_hijacked_by_broad_semantic_phase_progress(self) -> None:
        with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
            self.assertFalse(
                broad_semantic_phase_requested(
                    {"repair_kind": "localized_semantic_dut_repair"},
                    {"status": "not_run"},
                )
            )
            self.assertTrue(
                broad_semantic_phase_requested(
                    {"repair_kind": "semantic_template_repair"},
                    {"status": "not_run"},
                )
            )
            self.assertFalse(
                broad_semantic_phase_requested(
                    {"repair_kind": "semantic_loader_harness_binding"},
                    {"status": "not_run"},
                )
            )

    def trace_record(self) -> dict:
        return {
            "status": "fail",
            "evidence_type": "semantic_numeric_compare",
            "failure_class": "unknown_logic_value",
            "stage_id": "stage_arbitrary",
            "module": "ArbitraryHarness",
            "beat_index": 9,
            "lane_index": 2,
            "observed_value": {"packed_literal": "xxxxxxxx"},
            "expected_value": {"ieee_value": 1.25},
        }

    def localization(self) -> dict:
        trace = self.trace_record()
        return {
            "status": "localized",
            "root_candidate_module": "ArbitraryHarness",
            "violated_contract": "target_model_operator_semantics",
            "failure_signature": {"summary": "RTL output contains unknown values"},
            "failed_boundaries": [trace],
            "minimal_repair_context": {
                "root_candidate_module": "ArbitraryHarness",
                "violated_contract": "target_model_operator_semantics",
                "trace_record": trace,
            },
            "targeted_replay_plan": {"status": "ready"},
        }

    def internal_localization(self) -> dict:
        numeric = self.trace_record()
        internal = {
            "status": "fail",
            "evidence_type": "semantic_internal_boundary_trace",
            "failure_class": "unknown_logic_value",
            "stage_id": "stage_arbitrary",
            "module": "InternalProducer",
            "cycle": 101,
            "beat_index": 9,
            "observed_value": {"valid": 1, "ready": 1, "packed_literal": "xx11"},
        }
        return {
            "status": "localized",
            "root_candidate_module": "InternalProducer",
            "violated_contract": "internal_submodule_known_value_when_valid",
            "failure_signature": {"summary": "internal producer emitted unknown data"},
            "failed_boundaries": [internal, numeric],
            "minimal_repair_context": {
                "root_candidate_module": "InternalProducer",
                "violated_contract": "internal_submodule_known_value_when_valid",
                "trace_record": internal,
            },
            "targeted_replay_plan": {"status": "ready"},
        }

    def test_real_semantic_failure_precedes_missing_aggregate_capability(self) -> None:
        verification = {
            "results": [
                {
                    "checker": "real_tool.case_leaf_golden_compare",
                    "kind": "case_leaf_golden_compare",
                    "status": "fail",
                    "summary": "current independent golden numeric comparison failed",
                },
                {
                    "checker": "real_tool.case_operator_leaf_semantic_evidence",
                    "status": "fail",
                    "summary": "semantic evidence report is incomplete because golden failed",
                }
            ]
        }

        self.assertEqual(
            failure_kind(self.localization(), verification),
            "hardware_value_mismatch",
        )

    def test_leaf_numeric_failure_routes_to_agent_owned_localized_repair(self) -> None:
        repair_loop = {
            "failure_kind": "hardware_value_mismatch",
            "current_layer": {"id": "operator_leaf_modules"},
            "failed_current_layer_gates": [
                {"name": "case_leaf_golden_compare", "status": "fail"}
            ],
            "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
        }

        actions = build_repair_actions(
            failures=[],
            diagnosis=None,
            case_adapter={},
            debug_localization=self.localization(),
            repair_loop=repair_loop,
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], "localized_semantic_dut_repair")
        self.assertEqual(actions[0]["target_modules"], ["ArbitraryHarness"])
        self.assertEqual(
            actions[0]["minimal_repair_context"]["trace_record"]["beat_index"],
            9,
        )

    def test_internal_trace_routes_exact_producer_to_localized_template_repair(self) -> None:
        repair_loop = {
            "failure_kind": "hardware_value_mismatch",
            "current_layer": {"id": "operator_leaf_modules"},
            "failed_current_layer_gates": [
                {"name": "case_leaf_golden_compare", "status": "fail"}
            ],
            "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
        }

        actions = build_repair_actions(
            failures=[],
            diagnosis=None,
            case_adapter={},
            debug_localization=self.internal_localization(),
            repair_loop=repair_loop,
        )

        self.assertEqual(actions[0]["repair_kind"], "localized_semantic_dut_repair")
        self.assertEqual(actions[0]["target_modules"], ["InternalProducer"])
        self.assertEqual(
            actions[0]["corroborating_semantic_numeric_failure"]["evidence_type"],
            "semantic_numeric_compare",
        )

    def test_authorization_opens_only_hash_identical_template_pairs(self) -> None:
        persistent = (
            Path.cwd()
            / "accagent"
            / "framework"
            / "templates"
            / "operator_chisel"
            / "Common.scala"
        )
        self.assertTrue(persistent.is_file())
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Common.scala"
            )
            generated.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            bundle = {
                "documents": [],
                "editable_contract": {"read_only_template_sources": [str(generated)]},
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                localized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    {**self.trace_record(), "module": "StageConfig"},
                )

            editable = localized["editable_contract"]
            self.assertTrue(editable["localized_semantic_repair_authorized"])
            self.assertEqual(editable["localized_template_pair_names"], ["Common.scala"])
            self.assertEqual(
                set(editable["approved_bounded_template_repair_exact_files"]),
                {str(persistent.relative_to(Path.cwd())), str(generated)},
            )
            self.assertEqual(editable["localized_authorization_errors"], [])

    def test_internal_trace_authorization_requires_same_stage_numeric_failure(self) -> None:
        persistent = (
            Path.cwd()
            / "accagent"
            / "framework"
            / "templates"
            / "operator_chisel"
            / "Common.scala"
        )
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Common.scala"
            )
            generated.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            bundle = {
                "documents": [],
                "editable_contract": {"read_only_template_sources": [str(generated)]},
            }
            localization = self.internal_localization()
            internal = {
                **localization["minimal_repair_context"]["trace_record"],
                "module": "StageConfig",
            }
            numeric = {**localization["failed_boundaries"][1], "module": "StageConfig"}

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                rejected = authorize_localized_semantic_repair_bundle(bundle, run_dir, internal)
                authorized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    internal,
                    corroborating_numeric_failure=numeric,
                )

            self.assertFalse(rejected["editable_contract"]["localized_semantic_repair_authorized"])
            self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])

    def test_blocked_agent_can_request_localized_template_instrumentation(self) -> None:
        trace = self.internal_localization()["minimal_repair_context"]["trace_record"]
        prior = {
            "output": {
                "status": "blocked",
                "file_edits": [],
                "summary": (
                    "InternalProducer is localized, but the first internal divergence is not yet observed."
                ),
                "root_cause": "InternalProducer needs a bounded internal trace.",
                "blocked_reasons": ["Missing observation at the producer's internal state boundary."],
            }
        }

        self.assertTrue(localized_template_instrumentation_requested(prior, trace))

    def test_fresh_instrumentation_boundary_prevents_repeating_old_request(self) -> None:
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            report = {
                "step_results": [
                    {
                        "result": {
                            "instrumentation_evidence_collected": True,
                            "leaf_stage_report": "/tmp/stage_01_self_attention.json",
                            "instrumentation_evidence": {
                                "status": "pass",
                                "stage_id": "stage_01_self_attention",
                                "new_internal_boundaries": ["softmax_to_context"],
                                "new_internal_modules": ["Softmax"],
                            },
                        }
                    }
                ]
            }
            (out_dir / "repair_execution_report.json").write_text(
                json.dumps(report),
                encoding="utf-8",
            )

            self.assertTrue(
                localized_template_instrumentation_already_collected(
                    out_dir,
                    {
                        "stage_id": "stage_01_self_attention",
                        "boundary_id": "softmax_to_context",
                        "module": "Softmax",
                    },
                )
            )
            self.assertFalse(
                localized_template_instrumentation_already_collected(
                    out_dir,
                    {
                        "stage_id": "stage_06_activation_mul",
                        "boundary_id": "softmax_to_context",
                        "module": "Softmax",
                    },
                )
            )

    def test_stage_golden_trace_preserves_instrumentation_checkpoint_across_report_overwrite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            report_dir = run_dir / "verification" / "operator_leaf_golden"
            out_dir.mkdir(parents=True)
            report_dir.mkdir(parents=True)
            (out_dir / "repair_execution_report.json").write_text(
                json.dumps({"status": "incomplete", "step_results": []}),
                encoding="utf-8",
            )
            (report_dir / "stage_01_self_attention.json").write_text(
                json.dumps(
                    {
                        "internal_boundary_trace": [
                            {
                                "status": "fail",
                                "evidence_type": "semantic_internal_boundary_trace",
                                "stage_id": "stage_01_self_attention",
                                "boundary_id": "softmax_to_context",
                                "module": "Softmax",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            self.assertTrue(
                localized_template_instrumentation_already_collected(
                    out_dir,
                    {
                        "stage_id": "stage_01_self_attention",
                        "boundary_id": "different_normalized_boundary",
                        "module": "Softmax",
                    },
                )
            )

    def test_template_instrumentation_opens_only_root_declaring_pair(self) -> None:
        persistent_root = (
            Path.cwd() / "accagent" / "framework" / "templates" / "operator_chisel"
        )
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
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
            generated_root.mkdir(parents=True)
            generated_paths = []
            for name in ("Attention.scala", "Common.scala"):
                generated = generated_root / name
                generated.write_bytes((persistent_root / name).read_bytes())
                generated_paths.append(generated)
            trace = {
                **self.internal_localization()["minimal_repair_context"]["trace_record"],
                "module": "AttentionGQA",
            }
            numeric = {
                **self.trace_record(),
                "module": "AttentionGQA",
            }
            bundle = {
                "documents": [
                    {
                        "path": str(path),
                        "content": path.read_text(encoding="utf-8"),
                    }
                    for path in generated_paths
                ]
                + [
                    {
                        "path": "scripts/verification/semantic_testbench_generator.py",
                        "content": "unrelated producer body",
                    },
                    {
                        "path": (
                            "verification/operator_leaf_golden/"
                            f"{trace['stage_id']}.json"
                        ),
                        "content": "{}",
                    },
                ],
                "editable_contract": {
                    "read_only_template_sources": [str(path) for path in generated_paths]
                },
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                authorized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    trace,
                    template_instrumentation_only=True,
                    corroborating_numeric_failure=numeric,
                )

            editable = authorized["editable_contract"]
            approved = {
                (Path(path) if Path(path).is_absolute() else Path.cwd() / path).resolve()
                for path in editable["approved_bounded_template_repair_exact_files"]
            }
            self.assertTrue(editable["localized_template_instrumentation_approved"])
            self.assertEqual(editable["localized_template_instrumentation_pair_names"], ["Attention.scala"])
            self.assertEqual(
                approved,
                {(persistent_root / "Attention.scala").resolve(), (generated_root / "Attention.scala").resolve()},
            )
            self.assertIn(str(generated_root / "Common.scala"), editable["read_only_template_sources"])
            document_paths = {str(row["path"]) for row in authorized["documents"]}
            self.assertIn(str(generated_root / "Attention.scala"), document_paths)
            self.assertIn(str(generated_root / "Common.scala"), document_paths)
            self.assertNotIn("scripts/verification/semantic_testbench_generator.py", document_paths)

    def test_functional_localized_repair_opens_only_root_declaring_template_pair(self) -> None:
        persistent_root = Path.cwd() / "accagent" / "framework" / "templates" / "operator_chisel"
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
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
            generated_root.mkdir(parents=True)
            generated_paths = []
            for name in ("Attention.scala", "Common.scala"):
                generated = generated_root / name
                generated.write_bytes((persistent_root / name).read_bytes())
                generated_paths.append(generated)
            trace = {
                **self.internal_localization()["minimal_repair_context"]["trace_record"],
                "module": "AttentionGQA",
            }
            numeric = {**self.trace_record(), "module": "AttentionGQA"}
            bundle = {
                "documents": [
                    {"path": str(path), "content": path.read_text(encoding="utf-8")}
                    for path in generated_paths
                ],
                "editable_contract": {
                    "read_only_template_sources": [str(path) for path in generated_paths]
                },
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                authorized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    trace,
                    corroborating_numeric_failure=numeric,
                )

            editable = authorized["editable_contract"]
            approved = {
                (Path(path) if Path(path).is_absolute() else Path.cwd() / path).resolve()
                for path in editable["approved_bounded_template_repair_exact_files"]
            }
            self.assertTrue(editable["localized_semantic_repair_authorized"])
            self.assertEqual(editable["localized_template_pair_names"], ["Attention.scala"])
            self.assertEqual(
                approved,
                {
                    (persistent_root / "Attention.scala").resolve(),
                    (generated_root / "Attention.scala").resolve(),
                },
            )
            self.assertIn(str(generated_root / "Common.scala"), editable["read_only_template_sources"])

    def test_large_localized_report_is_replaced_by_decision_complete_projection(self) -> None:
        persistent = Path.cwd() / "accagent" / "framework" / "templates" / "operator_chisel" / "Common.scala"
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Common.scala"
            )
            generated.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            boundary_id = "boundary.internal.generic"
            traces = []
            for beat in range(100):
                failed = beat >= 2
                traces.append(
                    {
                        "status": "fail" if failed else "diagnostic_seed",
                        "evidence_type": "semantic_internal_boundary_trace",
                        "failure_class": "unknown_logic_value" if failed else None,
                        "stage_id": "stage_arbitrary",
                        "module": "StageConfig",
                        "boundary_id": boundary_id,
                        "beat_index": beat,
                        "observed_value": {
                            "valid": 1,
                            "ready": 1,
                            "packed_literal": ("x" if failed else "1") * 2048,
                        },
                        "violated_contract": "known_when_valid" if failed else None,
                    }
                )
            report = {
                "schema_version": "semantic.report.v1",
                "gate": "leaf_golden_compare",
                "mode": "golden",
                "stage_id": "stage_arbitrary",
                "status": "fail",
                "summary": "unknown values",
                "module_results": [
                    {
                        "stage_id": "stage_arbitrary",
                        "status": "pass",
                        "input_fingerprint_sha256": "a" * 64,
                        "rtl_output_sha256": "b" * 64,
                    }
                ],
                "internal_boundary_trace": traces,
                "debug_closure": {"failure_slice": [row for row in traces if row["status"] == "fail"]},
                "semantic_comparison": {"status": "fail", "numeric_metrics": {"num_mismatch": 98}},
            }
            report_content = json.dumps(report, indent=2)
            report_path = "verification/operator_leaf_golden/stage_arbitrary.json"
            bundle = {
                "documents": [
                    {"path": str(generated), "content": generated.read_text(encoding="utf-8")},
                    {"path": report_path, "content": report_content, "truncated": False},
                ],
                "editable_contract": {"read_only_template_sources": [str(generated)]},
            }
            trace = {**traces[2], "summary": "first unknown value"}
            numeric = {
                **self.trace_record(),
                "stage_id": "stage_arbitrary",
                "module": "StageConfig",
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                localized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    trace,
                    corroborating_numeric_failure=numeric,
                )

            documents = {str(row["path"]): row for row in localized["documents"]}
            projection_path = f"{report_path}#localized_semantic_decision_projection"
            self.assertNotIn(report_path, documents)
            self.assertIn(projection_path, documents)
            projection = json.loads(documents[projection_path]["content"])
            self.assertEqual(projection["raw_evidence_counts"]["internal_trace_records"], 100)
            self.assertEqual(projection["representative_internal_failures"][0]["equivalent_failure_count"], 98)
            self.assertEqual(
                [row["beat_index"] for row in projection["selected_internal_trace_window"]],
                [0, 1, 2],
            )
            self.assertEqual(projection["raw_report"]["bytes"], len(report_content.encode("utf-8")))
            self.assertLess(documents[projection_path]["bytes"], len(report_content.encode("utf-8")))

    def test_localized_prompt_keeps_failed_memory_contract_and_excludes_passed_report(self) -> None:
        persistent = Path.cwd() / "accagent" / "framework" / "templates" / "operator_chisel" / "Common.scala"
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Common.scala"
            )
            stage_root = run_dir / "generated" / "semantic_harness" / "stage_arbitrary"
            resource = run_dir / "generated" / "chisel" / "src" / "main" / "resources" / "table.memh"
            generated.parent.mkdir(parents=True)
            stage_root.mkdir(parents=True)
            resource.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            resource.write_text("00000001\n", encoding="ascii")
            root_sv = stage_root / "StageConfig.sv"
            memory_sv = stage_root / "table_1x32.sv"
            root_sv.write_text("module StageConfig; endmodule\n", encoding="ascii")
            memory_sv.write_text(
                "module table_1x32;\n"
                "  reg [31:0] Memory [0:0];\n"
                "`ifdef ENABLE_INITIAL_MEM_\n"
                '  initial $readmemh("src/main/resources/table.memh", Memory);\n'
                "`endif\n"
                "endmodule\n",
                encoding="ascii",
            )
            passed_report = "verification/operator_leaf_golden/stage_passed.json"
            bundle = {
                "documents": [
                    {"path": str(generated), "content": generated.read_text(encoding="utf-8")},
                    {"path": str(root_sv), "content": root_sv.read_text(encoding="utf-8")},
                    {"path": str(memory_sv), "content": memory_sv.read_text(encoding="utf-8")},
                    {"path": passed_report, "content": json.dumps({"status": "pass"})},
                ],
                "editable_contract": {"read_only_template_sources": [str(generated)]},
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                localized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    {**self.trace_record(), "module": "StageConfig"},
                )

            documents = {str(row["path"]): row for row in localized["documents"]}
            projection_path = (
                "localized_semantic_repair/stage_arbitrary"
                "#semantic_memory_initialization_contract"
            )
            self.assertNotIn(passed_report, documents)
            self.assertIn(projection_path, documents)
            projection = json.loads(documents[projection_path]["content"])
            self.assertEqual(projection["vcs_compile_args"], ["+define+ENABLE_INITIAL_MEM_"])
            self.assertEqual(
                projection["dependencies"][0]["remote_relative_path"],
                "src/main/resources/table.memh",
            )
            self.assertIn("first repair the simulator", projection["decision_rule"])

    def test_template_instrumentation_validation_is_mandatory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            harness = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "semantic_harness"
                / "Harness.scala"
            )
            harness.parent.mkdir(parents=True)
            harness.write_text(
                "object ElaborateGenericHarnesses extends App { emitSystemVerilog() }\n",
                encoding="utf-8",
            )

            output, errors = semantic_harness_validation_output(
                {"requested_validation": []},
                run_dir,
                require_elaboration=True,
            )

            self.assertEqual(errors, [])
            self.assertEqual(
                [request["argv"][-1] for request in output["requested_validation"]],
                [
                    "Compile/compile",
                    "runMain spatialaccagent.semantic_harness.ElaborateGenericHarnesses",
                ],
            )

    def test_stage_scope_selects_required_elaboration_main(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
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

            output, errors = semantic_harness_validation_output(
                {"requested_validation": []},
                run_dir,
                require_elaboration=True,
                required_elaboration_main="ElaborateSingleLayerClosure",
            )

            self.assertEqual(errors, [])
            self.assertEqual(
                [request["argv"][-1] for request in output["requested_validation"]],
                [
                    "Compile/compile",
                    "runMain spatialaccagent.semantic_harness.ElaborateSingleLayerClosure",
                ],
            )

    def test_exact_internal_trace_is_not_reconverted_to_instrumentation(self) -> None:
        repair_plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "status": "ready_for_agent_patch",
                        "action": {
                            "repair_kind": "localized_semantic_dut_repair",
                            "minimal_repair_context": self.internal_localization()[
                                "minimal_repair_context"
                            ],
                        },
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            }
        }
        llm_output = {
            "status": "needs_current_layer_localization",
            "summary": "The exact internal producer is localized; patch that producer.",
            "executable_actions": [],
        }

        reconciled = reconcile_repair_workflow_with_llm(repair_plan, llm_output)

        self.assertFalse(
            reconciled["repair_workflow"]["llm_disposition"][
                "converted_to_instrumentation_first"
            ]
        )

    def test_llm_localization_request_converts_patch_to_instrumentation_first(self) -> None:
        repair_plan = {
            "repair_workflow": {
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "status": "ready_for_agent_patch",
                        "action": {"repair_kind": "localized_semantic_dut_repair"},
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            }
        }
        llm_output = {
            "status": "needs_checker_repair_then_current_layer_localization_no_promotion",
            "summary": "Reject the candidate plan's immediate template patch; perform targeted boundary replay first.",
            "executable_actions": [],
        }

        reconciled = reconcile_repair_workflow_with_llm(repair_plan, llm_output)
        workflow = reconciled["repair_workflow"]
        step = workflow["steps"][0]

        self.assertEqual(workflow["status"], "ready")
        self.assertFalse(workflow["llm_disposition"]["vetoed_pre_llm_execution"])
        self.assertTrue(workflow["llm_disposition"]["converted_to_instrumentation_first"])
        self.assertEqual(step["status"], "ready_for_agent_patch")
        self.assertEqual(step["action"]["repair_phase"], "instrumentation_first")

    def test_instrumentation_first_keeps_template_pairs_read_only(self) -> None:
        persistent = (
            Path.cwd()
            / "accagent"
            / "framework"
            / "templates"
            / "operator_chisel"
            / "Common.scala"
        )
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            generated = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "templates"
                / "Common.scala"
            )
            harness = generated.parent.parent / "semantic_harness" / "Harness.scala"
            generated.parent.mkdir(parents=True)
            harness.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            harness.write_text("class Harness\n", encoding="utf-8")
            bundle = {
                "documents": [],
                "editable_contract": {"read_only_template_sources": [str(generated)]},
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                localized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    self.trace_record(),
                    instrumentation_only=True,
                )

            editable = localized["editable_contract"]
            self.assertTrue(editable["localized_semantic_repair_authorized"])
            self.assertTrue(editable["localized_instrumentation_only"])
            self.assertFalse(editable["semantic_template_repair_approved"])
            self.assertEqual(editable["approved_bounded_template_repair_exact_files"], [])
            self.assertIn(str(harness), editable["localized_allowed_exact_files"])
            self.assertNotIn(str(generated), editable["localized_allowed_exact_files"])
