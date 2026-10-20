import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.repair_loop import failure_kind
from accagent.framework.stage_llm import compact_verification_capability_repair_package
from accagent.framework.debug_closure import build_debug_closure_artifacts
from accagent.framework.stage_repair import (
    _llm_observation_workflow_action,
    build_repair_actions,
    build_repair_workflow,
    reconcile_repair_workflow_with_llm,
)
from accagent.framework.stage_repair_execute import authorize_localized_semantic_repair_bundle
from accagent.framework.stage_repair_execute import (
    broad_semantic_phase_requested,
    capability_repair_source_bundle,
    compact_localized_semantic_report_documents,
    leaf_observation_followup,
    localized_template_instrumentation_already_collected,
    localized_template_instrumentation_allowed,
    localized_template_instrumentation_requested,
    semantic_harness_validation_output,
)


class LocalizedSemanticRepairTest(TestCase):
    def test_functional_observations_survive_localized_prompt_compaction(self) -> None:
        trace = {
            "stage_id": "stage_primary", "module": "ArbitraryHarness",
            "boundary_id": "semantic_input_progress", "evidence_type": "semantic_liveness",
        }
        observations = [{
            "stage_id": "stage_primary", "module": "InternalReduction",
            "boundary_id": "reduction.completion_count", "cycle": 2625,
            "status": "diagnostic_seed", "observed_value": {"packed_literal": "00000000"},
        }]
        report = {
            "stage_id": "stage_primary", "status": "fail",
            "module_results": [{"status": "fail", "failure_class": "adaptive_semantic_stall"}],
            "internal_boundary_trace": observations,
        }
        documents = compact_localized_semantic_report_documents([{
            "path": "/run/verification/operator_leaf_functional/stage_primary.json",
            "content": json.dumps(report),
        }], trace, None)
        compact = compact_verification_capability_repair_package({
            "verification_scope": "operator_leaf_closure",
            "repair_source_bundle": {"documents": documents, "editable_contract": {}},
        })
        projection = compact["repair_source_bundle"]["documents"][0]["json_content"]
        self.assertEqual(projection["internal_boundary_trace"], observations)
        self.assertEqual(projection["selected_internal_trace_window"], [])
        self.assertEqual(projection["module_execution"][0]["failure_class"], "adaptive_semantic_stall")

    def test_failed_observation_returns_current_functional_report_for_replanning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "current_leaf.json"
            report_path.write_text(json.dumps({
                "stage_id": "stage_primary",
                "status": "fail",
                "module_results": [{"status": "fail", "failure_class": "adaptive_semantic_stall"}],
                "internal_boundary_trace": [{"module": "ArbitraryOperator", "cycle": 512}],
            }), encoding="utf-8")
            probe = {"status": "fail", "produced_reports": [
                {"stage_id": "other_stage", "path": str(report_path)},
                {"stage_id": "stage_primary", "path": str(Path(temp_dir) / "absent_golden.json")},
                {"stage_id": "stage_primary", "path": str(report_path)},
            ]}
            feedback = leaf_observation_followup(probe, "stage_primary")
            self.assertTrue(feedback["requires_agent_followup"])
            self.assertEqual(feedback["leaf_stage_report"], str(report_path))
            self.assertFalse(feedback["stage_passed"])
            self.assertEqual(leaf_observation_followup(probe, "missing_stage"), {})

    def test_leaf_compile_log_keeps_diagnostic_after_large_simulator_banner(self) -> None:
        diagnostic = (
            "Error-[STASKEC_USF] Undefined system function\n"
            "PassiveMonitor.sv, 48\n"
            "  System function call '$getenv' is not defined.\n"
            "  Please correct and recompile.\n"
        )
        log = "Parsing vendor simulation library\n" * 1500 + diagnostic
        compact = compact_verification_capability_repair_package({
            "verification_scope": "operator_leaf_closure",
            "repair_source_bundle": {
                "documents": [{"path": "/run/verification/vcs.log", "content": log}],
                "editable_contract": {},
            },
        })
        document = compact["repair_source_bundle"]["documents"][0]
        excerpt = document["causal_log_excerpt"]
        self.assertIn(diagnostic, excerpt["excerpt"])
        self.assertEqual(excerpt["text_sha256"], hashlib.sha256(log.encode("utf-8")).hexdigest())
        self.assertTrue(excerpt["full_log_omitted_from_prompt_only"])
        self.assertNotIn("content_head", document)

    def test_missing_leaf_harness_keeps_complete_creation_sources_and_contracts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            scala_root = run_dir / "generated/chisel/src/main/scala/spatialaccagent"
            template = scala_root / "templates/Common.scala"
            template.parent.mkdir(parents=True)
            persistent_template = Path.cwd() / "accagent/framework/templates/operator_chisel/Common.scala"
            template.write_bytes(persistent_template.read_bytes())
            parameters = scala_root / "generated/GeneratedDesignParams.scala"
            parameters.parent.mkdir()
            parameters.write_text("package spatialaccagent.generated\nobject GeneratedDesignParams { val lanes = 4 }\n", encoding="utf-8")
            requirements_path = run_dir / "verification/semantic_testbench/dut_weight_binding_requirements.json"
            requirements_path.parent.mkdir(parents=True)
            stage_ids = ["stage_00_primary", "stage_01_secondary"]
            requirements = {
                "stage_requirements": [{"stage_id": stage_id} for stage_id in stage_ids],
                "agent_manifest_schema": {"required": ["stage_harnesses"]},
                "stream_metadata_contract": {"row_last_required": True},
            }
            requirements_path.write_text(json.dumps(requirements), encoding="utf-8")
            binding_path = run_dir / "generated/memory/dut_weight_binding_manifest.json"
            binding_path.parent.mkdir()
            binding = {"stage_harnesses": {stage_id: {"top_module": stage_id} for stage_id in stage_ids}}
            binding_path.write_text(json.dumps(binding), encoding="utf-8")
            report_path = run_dir / "verification/operator_leaf_functional/stage_00_primary.json"
            report_path.parent.mkdir()
            report_path.write_text(json.dumps({
                "status": "fail", "stage_id": stage_ids[0], "module_results": [{"status": "fail"}],
                "semantic_contract_path": str(run_dir / "missing_contract.json"),
            }), encoding="utf-8")
            source_bundle = {
                "documents": [{"path": str(persistent_template), "content": persistent_template.read_text(encoding="utf-8")}],
                "editable_contract": {"read_only_template_sources": [str(persistent_template)]},
            }
            bundle = capability_repair_source_bundle(source_bundle, run_dir, run_dir / "repair_execution", focus_stage_ids={stage_ids[0]})
            record = {
                "status": "fail", "stage_id": stage_ids[0], "module": "ArbitraryHarness",
                "evidence_type": "semantic_liveness", "failure_class": "semantic_ingress_stall",
                "input_fingerprint_sha256": "a" * 64,
                "liveness_evidence": {
                    "status": "proven_semantic_stall", "stage_id": stage_ids[0],
                    "heartbeat": {"input_accepted": {"input_0_accepted": 12}, "output_beats": 0},
                    "heartbeat_contract": {"input_beat_targets": {"input_0_accepted": 120}},
                },
            }
            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "0"}):
                authorized = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
            documents = {document["path"]: document["content"] for document in authorized["documents"]}
            self.assertEqual(documents[str(template)], template.read_text(encoding="utf-8"))
            self.assertEqual(documents[str(parameters)], parameters.read_text(encoding="utf-8"))
            projected_requirements = json.loads(documents[f"{requirements_path}#operator_leaf_closure_requirements_projection"])
            self.assertEqual(projected_requirements["stage_requirements"], requirements["stage_requirements"])
            self.assertEqual(projected_requirements["agent_manifest_schema"], requirements["agent_manifest_schema"])
            self.assertEqual(projected_requirements["stream_metadata_contract"], requirements["stream_metadata_contract"])
            projected_binding = json.loads(documents[f"{binding_path}#operator_leaf_closure_binding_projection"])
            self.assertEqual(projected_binding["stage_harnesses"], binding["stage_harnesses"])
            self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])
            self.assertFalse(authorized["editable_contract"]["bounded_template_repair_approved"])
            self.assertIn(str(scala_root / "semantic_harness/SemanticHarnesses.scala"), authorized["editable_contract"]["localized_allowed_exact_files"])
            compact = compact_verification_capability_repair_package({
                "verification_scope": "operator_leaf_closure", "repair_source_bundle": authorized,
            })
            compact_documents = {document["path"]: document for document in compact["repair_source_bundle"]["documents"]}
            self.assertEqual(compact_documents[str(template)]["content"], documents[str(template)])
            for path in [
                f"{requirements_path}#operator_leaf_closure_requirements_projection",
                f"{binding_path}#operator_leaf_closure_binding_projection",
            ]:
                self.assertEqual(compact_documents[path]["json_content"], json.loads(documents[path]))
            harness_source = scala_root / "semantic_harness/SemanticHarnesses.scala"
            harness_source.parent.mkdir()
            harness_source.write_text(
                "class SharedHarness { val cfg = new StageConfig(4) }\n"
                "class DelegatingHarness extends SharedHarness\n"
                "class LaterHarness { val core = new UnrelatedModule }\n",
                encoding="utf-8",
            )
            contract_path = run_dir / "semantic_contract.json"
            contract_path.write_text(json.dumps({"dut_harness": {"top_module": "DelegatingHarness"}}), encoding="utf-8")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["semantic_contract_path"] = str(contract_path)
            report_path.write_text(json.dumps(report), encoding="utf-8")
            existing_bundle = capability_repair_source_bundle(source_bundle, run_dir, run_dir / "repair_execution", focus_stage_ids={stage_ids[0]})
            existing_documents = {document["path"]: document["content"] for document in existing_bundle["documents"]}
            self.assertEqual(existing_documents[str(template)], documents[str(template)])
            self.assertEqual(existing_documents[str(parameters)], documents[str(parameters)])

    def test_leaf_implementation_receives_bound_observation_sources_through_compaction(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            stage_id = "stage_arbitrary"
            source_root = run_dir / "generated/semantic_harness" / stage_id
            sources = {
                "ArbitraryHarness.sv": "module ArbitraryHarness(input clock); Core core(); endmodule\n",
                "Core.sv": "module Core; Inner inner(); endmodule\n",
                "Inner.sv": "module Inner; wire transfer; endmodule\n",
                "verification/ArbitraryHarness_Verification.sv": (
                    "module ArbitraryHarness_Verification(input clock);\n"
                    'always @(posedge clock) $display("STATE=%d", clock);\n'
                    "endmodule\n"
                ),
                "verification/layers-ArbitraryHarness-Verification.sv": (
                    "bind ArbitraryHarness ArbitraryHarness_Verification observer(.clock(clock));\n"
                ),
            }
            source_rows = []
            for name, content in sources.items():
                path = source_root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                source_rows.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            mismatched_source = source_root / "Untrusted.sv"
            mismatched_source.write_text("module Untrusted; endmodule\n", encoding="utf-8")
            source_rows.append({"path": str(mismatched_source), "sha256": "0" * 64})
            contract_path = run_dir / "testbench_contract.json"
            contract_path.write_text(json.dumps({
                "dut_harness": {"top_module": "ArbitraryHarness", "source_files": source_rows},
            }), encoding="utf-8")
            adapter_path = run_dir / "semantic_adapter.json"
            adapter_path.write_text(json.dumps({"operators": {"normalize": "GenericNorm"}}), encoding="utf-8")
            model_path = run_dir / "model.py"
            model_content = "class GenericNorm:\n    pass\n"
            model_path.write_text(model_content, encoding="utf-8")
            reference_semantics = {
                "semantic_adapter": {"path": str(adapter_path), "sha256": hashlib.sha256(adapter_path.read_bytes()).hexdigest()},
                "model_implementation": {"source_path": str(model_path), "source_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest()},
            }
            requirements_path = run_dir / "verification/semantic_testbench/dut_weight_binding_requirements.json"
            requirements_path.parent.mkdir(parents=True)
            requirements_path.write_text(json.dumps({"reference_operator_semantics": reference_semantics}), encoding="utf-8")
            report_path = run_dir / "verification/operator_leaf_functional" / f"{stage_id}.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(json.dumps({
                "status": "fail", "stage_id": stage_id,
                "module_results": [{"status": "fail"}],
                "semantic_contract_path": str(contract_path),
            }), encoding="utf-8")
            fpga_closure = {"status": "pass", "required_ip_modules": ["declared_fp_module"]}
            generated_template = run_dir / "generated/chisel/src/main/scala/spatialaccagent/templates/Common.scala"
            generated_template.parent.mkdir(parents=True)
            generated_template.write_bytes((Path.cwd() / "accagent/framework/templates/operator_chisel/Common.scala").read_bytes())
            source_bundle = {
                "documents": [],
                "editable_contract": {"read_only_template_sources": [str(generated_template)]},
                "fpga_ip_repair_closure": fpga_closure,
            }
            bundle = capability_repair_source_bundle(
                source_bundle,
                run_dir,
                run_dir / "repair_execution",
                focus_stage_ids={stage_id},
            )
            record = {
                "status": "fail", "stage_id": stage_id, "module": "ArbitraryHarness",
                "evidence_type": "semantic_liveness", "failure_class": "semantic_ingress_stall",
                "input_fingerprint_sha256": "a" * 64,
                "liveness_evidence": {
                    "status": "proven_semantic_stall", "stage_id": stage_id,
                    "heartbeat": {"input_accepted": {"input_0_accepted": 12}, "output_beats": 0},
                    "heartbeat_contract": {"input_beat_targets": {"input_0_accepted": 120}},
                },
            }
            bundle = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
            self.assertTrue(bundle["editable_contract"]["localized_semantic_repair_authorized"])
            compact = compact_verification_capability_repair_package({
                "verification_scope": "operator_leaf_closure", "repair_source_bundle": bundle,
            })
            documents = {row["path"]: row for row in compact["repair_source_bundle"]["documents"]}
            for name, content in sources.items():
                self.assertEqual(documents[str(source_root / name)]["content"], content)
            self.assertNotIn(str(mismatched_source), documents)
            self.assertEqual(documents[str(adapter_path)]["json_content"], json.loads(adapter_path.read_text()))
            self.assertEqual(documents[str(model_path)]["content"], model_content)
            self.assertEqual(compact["repair_source_bundle"]["reference_operator_semantics"], reference_semantics)
            self.assertEqual(compact["repair_source_bundle"]["fpga_ip_repair_closure"], fpga_closure)
            self.assertFalse(compact["repair_source_bundle"]["compaction_policy"].get(
                "tools_must_read_hash_bound_source_files_for_execution", False,
            ))
            reference_semantics["model_implementation"]["source_sha256"] = "0" * 64
            requirements_path.write_text(json.dumps({"reference_operator_semantics": reference_semantics}), encoding="utf-8")
            mismatched_bundle = capability_repair_source_bundle(
                source_bundle, run_dir, run_dir / "repair_execution", focus_stage_ids={stage_id},
            )
            self.assertNotIn(str(model_path), {row["path"] for row in mismatched_bundle["documents"]})

    def test_proven_leaf_stall_reaches_instrumentation_owner_without_golden_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            report_path = run_dir / "leaf.json"
            proof = {
                "status": "proven_semantic_stall",
                "stage_id": "stage_arbitrary",
                "heartbeat": {"cycles": 7000, "input_accepted": {"input_0_accepted": 12}, "output_beats": 0},
                "heartbeat_contract": {"input_beat_targets": {"input_0_accepted": 120}, "expected_output_beats": 120},
            }
            report_path.write_text(json.dumps({
                "stage_id": "stage_arbitrary",
                "first_failed_module": "ArbitraryHarness",
                "module_results": [{"adaptive_semantic_stall_evidence": proof, "input_fingerprint_sha256": "a" * 64}],
                "debug_closure": {"boundary_trace": [{
                    "status": "fail",
                    "evidence_type": "semantic_output_shape",
                    "failure_class": "simulator_fatal_or_output_shape_mismatch",
                    "stage_id": "stage_arbitrary",
                    "module": "ArbitraryHarness",
                    "summary": "RTL output capture is missing",
                }]},
            }), encoding="utf-8")
            localization = build_debug_closure_artifacts({}, run_dir, trace_paths=[report_path])["failure_localization"]

        self.assertEqual(localization["minimal_repair_context"]["trace_record"]["evidence_type"], "semantic_liveness")
        kind = failure_kind(localization, {})
        self.assertEqual(kind, "hardware_liveness_or_handshake")
        actions = build_repair_actions([], None, {}, localization, {
            "failure_kind": kind,
            "current_layer": {"id": "operator_leaf_modules"},
            "failed_current_layer_gates": [{"name": "case_leaf_functional", "status": "fail"}],
        })
        self.assertEqual(actions[0]["repair_kind"], "localized_semantic_dut_repair")
        self.assertEqual(actions[0]["repair_gate"], "case_leaf_functional")
        plan = {"repair_actions": actions, "repair_workflow": {
            "status": "ready",
            "steps": [{"status": "ready_for_agent_patch", "scope": "verification_capability_repair", "action": actions[0]}],
        }}
        reconciled = reconcile_repair_workflow_with_llm(plan, {
            "status": "needs_boundary_trace",
            "executable_actions": [{
                "action_type": "bounded_same_layer_instrumented_observation",
                "requires_approval": False,
                "tool_roles": ["targeted_replay", "case_leaf_functional"],
                "targeted_replay_plan": {
                    "stage_id": "stage_arbitrary", "probes": ["source-bound internal progress"],
                    "rerun_env": {"SPATIALACC_TARGET_BOUNDARY": "boundary.internal_weight_ready"},
                },
            }],
        })
        step = reconciled["repair_workflow"]["steps"][0]
        self.assertEqual(step["scope"], "verification_capability_repair")
        self.assertEqual(step["action"]["repair_phase"], "instrumentation_first")
        self.assertEqual(step["action"]["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"], "boundary.internal_weight_ready")
        rerun_action = {
            "action_type": "conditional_leaf_trace_rerun_and_localization",
            "requires_approval": False,
            "tool_roles": ["boundary_trace_rerun", "case_leaf_functional"],
            "targeted_replay_plan": {"stage_id": "stage_arbitrary"},
        }
        reconciled = reconcile_repair_workflow_with_llm(plan, {
            "status": "needs_repair", "executable_actions": [rerun_action],
        })
        self.assertEqual(reconciled["repair_workflow"]["steps"][0]["action"]["repair_phase"], "instrumentation_first")
        reconciled = reconcile_repair_workflow_with_llm(plan, {
            "status": "needs_boundary_trace",
            "executable_actions": [{**rerun_action, "action_type": "conditional_current_layer_trace"}],
        })
        self.assertEqual(reconciled["repair_workflow"]["steps"][0]["action"]["repair_phase"], "instrumentation_first")

    def test_liveness_authority_requires_real_partial_input_stall_proof(self) -> None:
        persistent = Path.cwd() / "accagent/framework/templates/operator_chisel/Common.scala"
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            generated = run_dir / "generated/chisel/src/main/scala/spatialaccagent/templates/Common.scala"
            generated.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            bundle = {"documents": [], "editable_contract": {"read_only_template_sources": [str(generated)]}}
            record = {
                "status": "fail", "stage_id": "stage_arbitrary", "module": "ArbitraryHarness",
                "evidence_type": "semantic_liveness", "failure_class": "semantic_ingress_stall",
                "input_fingerprint_sha256": "a" * 64,
                "liveness_evidence": {
                    "status": "proven_semantic_stall", "stage_id": "stage_arbitrary",
                    "heartbeat": {"input_accepted": {"input_0_accepted": 12}, "output_beats": 0},
                    "heartbeat_contract": {"input_beat_targets": {"input_0_accepted": 120}},
                },
            }
            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "0"}):
                authorized = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])
                self.assertFalse(authorized["editable_contract"]["bounded_template_repair_approved"])
                record["liveness_evidence"]["heartbeat"]["input_accepted"]["input_0_accepted"] = 0
                record["liveness_evidence"]["heartbeat"]["phase"] = "reset_release"
                rejected = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertFalse(rejected["editable_contract"]["localized_semantic_repair_authorized"])
                record["liveness_evidence"]["heartbeat"]["phase"] = "streaming"
                authorized = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])
                record["liveness_evidence"]["heartbeat"]["input_accepted"]["input_0_accepted"] = 120
                rejected = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertFalse(rejected["editable_contract"]["localized_semantic_repair_authorized"])
                record["liveness_evidence"]["heartbeat"]["phase"] = "loading_weights"
                record["liveness_evidence"]["heartbeat"]["loader_accepted"] = {"weight_accepted": 12}
                record["liveness_evidence"]["heartbeat_contract"]["loader_word_targets"] = {"weight_accepted": 120}
                authorized = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])
                record["liveness_evidence"]["heartbeat"]["loader_accepted"]["weight_accepted"] = 0
                authorized = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])
                record["liveness_evidence"]["heartbeat_contract"].pop("loader_word_targets")
                rejected = authorize_localized_semantic_repair_bundle(bundle, run_dir, record, instrumentation_only=True)
                self.assertFalse(rejected["editable_contract"]["localized_semantic_repair_authorized"])

    def test_repair_observation_preserves_same_stage_specialist_execution_settings(self) -> None:
        workflow = {"steps": [{"action": {"debug_layer": "operator_leaf_modules"}}]}
        review = {
            "debug_layer": "operator_leaf_modules",
            "output": {"executable_actions": [{
                "action_type": "same_layer_targeted_observation",
                "requires_approval": False,
                "targeted_replay_plan": {
                    "stage_id": "stage_arbitrary",
                    "effective_trace_env": {
                        "SPATIALACC_BOUNDARY_TRACE": "1",
                        "SPATIALACC_TARGET_BOUNDARY": "boundary.output",
                    },
                },
            }]},
        }
        action = {
            "action_type": "debug_trace_rerun",
            "requires_approval": False,
            "targeted_replay_plan": {"stage_id": "stage_arbitrary", "probes": ["DUT progress"]},
        }
        routed, error = _llm_observation_workflow_action(action, workflow, {}, review)
        self.assertIsNone(error)
        self.assertEqual(routed["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"], "boundary.output")
        self.assertEqual(routed["targeted_replay_plan"]["probes"], ["DUT progress"])

        action["targeted_replay_plan"]["target_boundary"] = "boundary.internal"
        routed, error = _llm_observation_workflow_action(action, workflow, {}, review)
        self.assertIsNone(error)
        self.assertEqual(routed["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"], "boundary.internal")

        action["targeted_replay_plan"].pop("target_boundary")
        for field, value in [("debug_layer", "board_axi_ddr_wrapped_system"), ("stage_id", "stage_other")]:
            with self.subTest(field=field):
                other_review = json.loads(json.dumps(review))
                if field == "debug_layer":
                    other_review[field] = value
                else:
                    other_review["output"]["executable_actions"][0]["targeted_replay_plan"][field] = value
                routed, error = _llm_observation_workflow_action(action, workflow, {}, other_review)
                self.assertIsNone(error)
                self.assertNotIn("rerun_env", routed["targeted_replay_plan"])

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

    def test_internal_unknown_trace_routes_to_functional_repair_without_numeric_output(self) -> None:
        localization = self.internal_localization()
        localization["failed_boundaries"] = [localization["minimal_repair_context"]["trace_record"]]
        actions = build_repair_actions(
            failures=[],
            diagnosis=None,
            case_adapter={},
            debug_localization=localization,
            repair_loop={
                "failure_kind": "hardware_value_mismatch",
                "current_layer": {"id": "operator_leaf_modules"},
                "failed_current_layer_gates": [
                    {"name": "case_leaf_functional", "status": "fail"}
                ],
                "lower_layer_evidence_challenge": {"status": "no_lower_layer_challenge"},
            },
        )

        self.assertEqual(actions[0]["scope"], "verification_capability_repair")
        self.assertEqual(actions[0]["repair_kind"], "localized_semantic_dut_repair")
        self.assertEqual(actions[0]["repair_gate"], "case_leaf_functional")
        self.assertIsNone(actions[0].get("corroborating_semantic_numeric_failure"))

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

    def test_bounded_template_approval_opens_hash_identical_template_pairs(self) -> None:
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

            with patch.dict(
                os.environ,
                {
                    "SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "0",
                    "SPATIALACC_APPROVE_BOUNDED_TEMPLATE_REPAIR": "1",
                },
            ):
                localized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    {**self.trace_record(), "module": "StageConfig"},
                )

            editable = localized["editable_contract"]
            self.assertTrue(editable["localized_semantic_repair_authorized"])
            self.assertTrue(editable["bounded_template_repair_approved"])
            self.assertEqual(editable["localized_template_pair_names"], ["Common.scala"])
            self.assertEqual(
                set(editable["approved_bounded_template_repair_exact_files"]),
                {str(persistent.relative_to(Path.cwd())), str(generated)},
            )

    def test_internal_trace_authorization_accepts_source_bound_unknown_without_numeric_failure(self) -> None:
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
                authorized_without_numeric = authorize_localized_semantic_repair_bundle(
                    bundle, run_dir, internal
                )
                authorized = authorize_localized_semantic_repair_bundle(
                    bundle,
                    run_dir,
                    internal,
                    corroborating_numeric_failure=numeric,
                )

            self.assertTrue(
                authorized_without_numeric["editable_contract"]["localized_semantic_repair_authorized"]
            )
            self.assertTrue(authorized["editable_contract"]["localized_semantic_repair_authorized"])

    def test_existing_harness_is_editable_when_template_repair_is_not_approved(self) -> None:
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
            harness = (
                run_dir
                / "generated"
                / "chisel"
                / "src"
                / "main"
                / "scala"
                / "spatialaccagent"
                / "semantic_harness"
                / "SemanticHarnesses.scala"
            )
            generated.parent.mkdir(parents=True)
            harness.parent.mkdir(parents=True)
            generated.write_bytes(persistent.read_bytes())
            harness.write_text(
                "package spatialaccagent.semantic_harness\n"
                "object SemanticHarnesses { val observed = true }\n",
                encoding="utf-8",
            )
            bundle = {
                "documents": [
                    {"path": str(generated), "content": generated.read_text(encoding="utf-8")},
                    {"path": str(harness), "content": harness.read_text(encoding="utf-8")},
                ],
                "editable_contract": {"read_only_template_sources": [str(generated)]},
            }
            record = {
                "status": "fail",
                "stage_id": "stage_arbitrary",
                "module": "InternalProducer",
                "evidence_type": "semantic_internal_boundary_trace",
                "failure_class": "unknown_logic_value",
                "observed_value": {"valid": 1, "packed_literal": "xx11"},
            }

            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "0"}):
                authorized = authorize_localized_semantic_repair_bundle(
                    bundle, run_dir, record
                )

            editable = authorized["editable_contract"]
            self.assertTrue(editable["localized_semantic_repair_authorized"])
            self.assertFalse(editable["semantic_template_repair_approved"])
            self.assertEqual(editable["localized_template_pair_names"], [])
            self.assertIn(str(harness), editable["localized_allowed_exact_files"])
            self.assertNotIn(str(generated), editable["localized_allowed_exact_files"])
            documents = {str(row["path"]): row for row in authorized["documents"]}
            self.assertEqual(documents[str(harness)]["content"], harness.read_text(encoding="utf-8"))

            compact = compact_verification_capability_repair_package({
                "verification_scope": "operator_leaf_closure",
                "repair_source_bundle": authorized,
            })
            compact_documents = {
                str(row["path"]): row
                for row in compact["repair_source_bundle"]["documents"]
            }
            self.assertEqual(
                compact_documents[str(harness)]["content"],
                harness.read_text(encoding="utf-8"),
            )

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

        with TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "0"}):
                self.assertFalse(
                    localized_template_instrumentation_allowed(prior, trace, Path(temp_dir))
                )
            with patch.dict(os.environ, {"SPATIALACC_APPROVE_SEMANTIC_TEMPLATE_REPAIR": "1"}):
                self.assertTrue(
                    localized_template_instrumentation_allowed(prior, trace, Path(temp_dir))
                )

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

    def test_repeated_targeted_observation_escalates_once_to_functional_repair(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "verification" / "case_leaf_operator_verify.py"
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        stage_id = "stage_arbitrary"
        fingerprint = "a" * 64
        trace_env = {
            "SPATIALACC_BOUNDARY_TRACE": "1",
            "SPATIALACC_CHECKPOINT_REPLAY": "1",
            "SPATIALACC_TARGETED_REPLAY": "1",
            "SPATIALACC_TARGET_BOUNDARY": "boundary.internal_progress",
        }
        repair_plan = {
            "repair_workflow": {
                "run_dir": "/run",
                "status": "ready",
                "steps": [{
                    "id": "repair_step.00",
                    "scope": "verification_capability_repair",
                    "status": "ready_for_agent_patch",
                    "action": {
                        "repair_kind": "localized_semantic_dut_repair",
                        "debug_layer": "operator_leaf_modules",
                        "approval_required": False,
                        "minimal_repair_context": {
                            "trace_record": {
                                "stage_id": stage_id,
                                "module": "ArbitraryHarness",
                                "status": "fail",
                                "evidence_type": "semantic_liveness",
                                "input_fingerprint_sha256": fingerprint,
                            }
                        },
                        "targeted_replay_plan": {
                            "stage_id": stage_id,
                            "semantic_input_fingerprint_sha256": fingerprint,
                            "rerun_env": trace_env,
                        },
                    },
                }],
                "blockers": [],
                "approval_steps": [],
            }
        }
        llm_output = {
            "status": "needs_boundary_trace",
            "executable_actions": [{
                "action_type": "same_layer_targeted_observation",
                "requires_approval": False,
                "debug_layer": "operator_leaf_modules",
                "stage_id": stage_id,
                "targeted_replay_plan": {
                    "stage_id": stage_id,
                    "semantic_input_fingerprint_sha256": fingerprint,
                    "rerun_env": trace_env,
                },
            }],
        }
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            first = reconcile_repair_workflow_with_llm(
                json.loads(json.dumps(repair_plan)),
                llm_output,
                case_adapter=case_adapter,
                state={},
                run_dir=run_dir,
            )
            first_workflow = first["repair_workflow"]
            self.assertTrue(first_workflow["llm_disposition"]["converted_to_instrumentation_first"])
            self.assertFalse(first_workflow["llm_disposition"]["repeated_targeted_observation_escalated"])
            self.assertEqual(first_workflow["steps"][0]["action"]["repair_phase"], "instrumentation_first")

            ledger_path = run_dir / "verification" / "debug_closure" / "targeted_replay_ledger.json"
            ledger_path.parent.mkdir(parents=True)
            ledger_path.write_text(json.dumps({
                "schema_version": "spatialaccagent.targeted_leaf_trace_ledger.v1",
                "completed": {
                    "b" * 64: {
                        "execution_input": {
                            "schema_version": "spatialaccagent.targeted_leaf_trace_execution_input.v3",
                            "stage_id": stage_id,
                            "trace_env": trace_env,
                            "semantic_input_fingerprint_sha256": fingerprint,
                        },
                        "input": {"testbench_contract": {"sha256": "c" * 64}},
                        "result_status": "fail",
                        "completed_at_unix_sec": 1,
                    }
                },
            }), encoding="utf-8")
            repeated = reconcile_repair_workflow_with_llm(
                json.loads(json.dumps(repair_plan)),
                llm_output,
                case_adapter=case_adapter,
                state={},
                run_dir=run_dir,
            )
            repeated_workflow = repeated["repair_workflow"]
            self.assertFalse(repeated_workflow["llm_disposition"]["converted_to_instrumentation_first"])
            self.assertTrue(repeated_workflow["llm_disposition"]["repeated_targeted_observation_escalated"])
            self.assertEqual(repeated_workflow["steps"][0]["scope"], "verification_capability_repair")
            self.assertEqual(repeated_workflow["steps"][0]["action"]["repair_phase"], "functional_repair")

    def test_llm_current_layer_replay_replaces_stale_causal_repair(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "verification" / "case_leaf_operator_verify.py"
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        repair_plan = {
            "repair_actions": [{"scope": "causal_slice_repair", "root_candidate_module": "StaleHarness"}],
            "repair_workflow": {
                "run_dir": str(Path.cwd()),
                "status": "ready",
                "steps": [
                    {
                        "id": "repair_step.00",
                        "scope": "causal_slice_repair",
                        "status": "ready_for_agent_patch",
                        "action": {
                            "scope": "causal_slice_repair",
                            "debug_layer": "operator_leaf_modules",
                            "root_candidate_module": "StaleHarness",
                            "minimal_repair_context": {
                                "trace_record": {"stage_id": "stage_00_rms_norm_1"}
                            },
                        },
                    }
                ],
                "blockers": [],
                "approval_steps": [],
            },
        }
        llm_output = {
            "status": "needs_bounded_diagnostic_replay",
            "summary": "Collect a fresh current-layer boundary trace before any repair.",
            "executable_actions": [
                {
                    "id": "repair_action.stage00_boundary_trace_localization",
                    "action_type": "current_layer_diagnostic_replay",
                    "requires_approval": False,
                    "debug_layer": "operator_leaf_modules",
                    "stage_id": "stage_00_rms_norm_1",
                    "environment": {
                        "SPATIALACC_TARGET_BOUNDARY": "boundary.input_to_stage00"
                    },
                    "targeted_replay_plan": {
                        "probe_sequence": ["boundary.input_to_stage00"],
                    },
                },
                {
                    "id": "repair_action.stage00_causal_repair",
                    "action_type": "bounded_causal_slice_repair",
                    "requires_approval": False,
                },
            ],
        }

        reconciled = reconcile_repair_workflow_with_llm(
            repair_plan,
            llm_output,
            case_adapter=case_adapter,
            state={},
            run_dir=Path.cwd(),
        )
        workflow = reconciled["repair_workflow"]
        self.assertEqual(reconciled["repair_actions"][0]["scope"], "debug_trace_rerun")
        self.assertEqual(len(workflow["steps"]), 1)
        step = workflow["steps"][0]
        self.assertEqual(step["scope"], "debug_trace_rerun")
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["trace_target"]["stage_id"], "stage_00_rms_norm_1")
        self.assertEqual(
            step["action"]["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"],
            "boundary.input_to_stage00",
        )
        self.assertEqual(
            step["execution"]["argv"][-2:],
            ["--stage-id", "stage_00_rms_norm_1"],
        )
        self.assertEqual(
            workflow["observation_replan"]["deferred_llm_actions"][0]["action_type"],
            "bounded_causal_slice_repair",
        )

    def test_llm_replay_without_stage_id_fails_closed(self) -> None:
        repair_plan = {
            "repair_workflow": {
                "run_dir": str(Path.cwd()),
                "status": "ready",
                "steps": [{
                    "id": "repair_step.00",
                    "scope": "causal_slice_repair",
                    "status": "ready_for_agent_patch",
                    "action": {
                        "debug_layer": "operator_leaf_modules",
                        "minimal_repair_context": {},
                    },
                }],
                "blockers": [],
                "approval_steps": [],
            }
        }
        reconciled = reconcile_repair_workflow_with_llm(
            repair_plan,
            {
                "status": "needs_bounded_diagnostic_replay",
                "summary": "A stage-specific observation is required.",
                "executable_actions": [{
                    "action_type": "targeted_boundary_replay",
                    "requires_approval": False,
                    "debug_layer": "operator_leaf_modules",
                }],
            },
            case_adapter={},
            state={},
            run_dir=Path.cwd(),
        )
        workflow = reconciled["repair_workflow"]
        self.assertEqual(workflow["status"], "blocked")
        self.assertTrue(workflow["llm_disposition"]["observation_route_error"])
        self.assertEqual(workflow["steps"][0]["scope"], "causal_slice_repair")

    def test_llm_debug_trace_action_accepts_target_stage_plan(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "verification" / "case_leaf_operator_verify.py"
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        repair_plan = {
            "repair_actions": [{"scope": "causal_slice_repair"}],
            "repair_workflow": {
                "run_dir": str(Path.cwd()),
                "status": "ready",
                "steps": [{
                    "id": "repair_step.00",
                    "scope": "causal_slice_repair",
                    "status": "ready_for_agent_patch",
                    "action": {
                        "debug_layer": "operator_leaf_modules",
                        "minimal_repair_context": {
                            "trace_record": {"stage_id": "stage_00_rms_norm_1"}
                        },
                    },
                }],
                "blockers": [],
                "approval_steps": [],
            },
        }
        reconciled = reconcile_repair_workflow_with_llm(
            repair_plan,
            {
                "status": "needs_same_layer_trace",
                "summary": "Run the selected current-layer boundary trace.",
                "executable_actions": [
                    {
                        "id": "repair_action.01_targeted_leaf_boundary_replay",
                        "action_type": "debug_trace_rerun",
                        "requires_approval": False,
                        "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                        "targeted_replay_plan": {
                            "target_stage": "stage_00_rms_norm_1",
                            "environment": {
                                "SPATIALACC_TARGET_BOUNDARY": "boundary.stage00_input"
                            },
                        },
                    },
                    {
                        "id": "repair_action.02_conditional_causal_slice_repair",
                        "action_type": "bounded_causal_repair",
                        "requires_approval": False,
                    },
                ],
            },
            case_adapter=case_adapter,
            state={},
            run_dir=Path.cwd(),
        )
        workflow = reconciled["repair_workflow"]
        step = workflow["steps"][0]
        self.assertEqual(step["scope"], "debug_trace_rerun")
        self.assertEqual(step["status"], "ready_to_execute")
        self.assertEqual(step["trace_target"]["stage_id"], "stage_00_rms_norm_1")
        self.assertEqual(
            step["action"]["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"],
            "boundary.stage00_input",
        )
        self.assertEqual(
            workflow["observation_replan"]["deferred_llm_actions"][0]["action_type"],
            "bounded_causal_repair",
        )

    def test_llm_same_layer_diagnostic_aliases_route_by_tool_role(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "verification" / "case_leaf_operator_verify.py"
        case_adapter = {
            "tools": {
                "leaf_functional_sim": {
                    "name": "case_leaf_functional",
                    "kind": "case_leaf_functional",
                    "argv": ["python3", str(script), "--run-dir", "/run", "--mode", "functional"],
                    "capabilities": [
                        "operator_leaf_functional_sim",
                        "targeted_leaf_replay",
                        "boundary_trace",
                        "boundary_trace_rerun",
                    ],
                    "targeted_replay": {"stage_id_arg": "--stage-id", "scope": "operator_leaf_stage"},
                }
            }
        }
        for action_type in (
            "same_layer_diagnostic_replay",
            "same_layer_targeted_diagnostic_replay",
            "diagnostic_targeted_replay",
        ):
            with self.subTest(action_type=action_type):
                repair_plan = {
                    "repair_actions": [{"scope": "causal_slice_repair"}],
                    "repair_workflow": {
                        "run_dir": str(Path.cwd()),
                        "status": "ready",
                        "steps": [{
                            "id": "repair_step.00",
                            "scope": "causal_slice_repair",
                            "status": "ready_for_agent_patch",
                            "action": {
                                "debug_layer": "operator_leaf_modules",
                                "minimal_repair_context": {
                                    "trace_record": {"stage_id": "stage_00_rms_norm_1"}
                                },
                            },
                        }],
                        "blockers": [],
                        "approval_steps": [],
                    },
                }
                reconciled = reconcile_repair_workflow_with_llm(
                    repair_plan,
                    {
                        "status": "needs_same_layer_trace",
                        "executable_actions": [{
                            "id": f"repair_action.{action_type}",
                            "action_type": action_type,
                            "requires_approval": False,
                            "tool_roles": ["boundary_trace_rerun", "targeted_replay"],
                            "targeted_replay_plan": {
                                "stage_id": "stage_00_rms_norm_1",
                                "environment": {
                                    "SPATIALACC_TARGET_BOUNDARY": "boundary.stage00_input"
                                },
                            },
                        }],
                    },
                    case_adapter=case_adapter,
                    state={},
                    run_dir=Path.cwd(),
                )
                workflow = reconciled["repair_workflow"]
                step = workflow["steps"][0]
                self.assertEqual(
                    workflow["llm_disposition"]["routed_observation_action_id"],
                    f"repair_action.{action_type}",
                )
                self.assertEqual(step["scope"], "debug_trace_rerun")
                self.assertEqual(step["trace_target"]["stage_id"], "stage_00_rms_norm_1")
                self.assertEqual(
                    step["action"]["targeted_replay_plan"]["rerun_env"]["SPATIALACC_TARGET_BOUNDARY"],
                    "boundary.stage00_input",
                )

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
