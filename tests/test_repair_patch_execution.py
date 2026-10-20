"""Minimal current Stage-6 LLM execution-contract regressions."""

from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from accagent.framework.stage_repair import required_capability_repair_actions
from accagent.framework.stage_llm import compact_verification_capability_repair_package
from accagent.framework.stage_repair_execute import (
    available_target_model_reference_regeneration_capabilities,
    apply_agent_file_edits,
    board_integration_prompt_rules,
    board_kernel_lifecycle_generation_authority,
    canonicalize_exact_board_manifest_declarations,
    capability_repair_source_bundle,
    certified_stage_harness_metadata_errors,
    execute_verification_capability_repair,
    exact_board_agent_task,
    prepare_exact_board_memory_runtime_inputs,
    exact_board_preflight_feedback,
    finalize_dut_weight_binding_manifest,
    localize_vcs_timescale_error_provenance,
    layer3_required_code_edit_errors,
    materialization_failure_projection,
    validation_failure_projection,
    normalize_semantic_harness_capability_aliases,
    reconcile_stale_operator_leaf_codegen_step,
    repair_loop_disposition,
    repair_source_bundle,
    semantic_harness_source_contract,
    semantic_harness_validation_output,
    _compiler_timescale_option,
    stage2_compile_only_authority,
    run_agent_requested_validation,
    run_capability_probe,
    validation_only_repair_request,
)
from accagent.framework.weight_layout import build_stage_weight_layout, sha256_json
from accagent.framework.verification_evidence_contract import (
    promotion_evidence_binding_fingerprint,
)


class RepairPatchExecutionTest(unittest.TestCase):
    def test_stale_board_generation_step_runs_discovery_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run = Path(temp_dir)
            step = {"id": "repair_step.00", "action": {
                "repair_kind": "exact_board_integration_harness",
                "debug_layer": "board_axi_ddr_wrapped_system",
            }}
            with patch(
                "accagent.framework.stage_repair_execute.execute_verification_capability_repair",
                return_value={"status": "fail", "stage_passed": False},
            ) as prerequisite:
                result = execute_verification_capability_repair(
                    step, run / "state.json", run, run / "repair_execution", 30
                )
            rebound = prerequisite.call_args.args[0]["action"]
            self.assertEqual(rebound["repair_kind"], "exact_board_interface_discovery")
            self.assertEqual(rebound["repair_tool_role"], "board_interface_discovery")
            self.assertEqual(step["action"]["repair_kind"], "exact_board_integration_harness")
            self.assertEqual(result["status"], "fail")
            self.assertFalse(result["stage_passed"])
            self.assertTrue(result["requires_agent_followup"])

    def test_board_manifest_finalization_records_default_policy_without_name_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            report = finalize_dut_weight_binding_manifest(
                run_dir, run_dir / "repair_execution", require_board=True,
            )
            manifest = json.loads(Path(report["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(manifest["materialization"]["validation_policy"], "vcs_compile_only")
        self.assertTrue(report["blockers"])

    def test_compiler_timescale_accepts_pair_in_timescale_field(self) -> None:
        self.assertEqual(
            _compiler_timescale_option(
                {"timescale": "1ps/1ps", "timeprecision": "1ps"}
            ),
            "-timescale=1ps/1ps",
        )
        self.assertEqual(
            _compiler_timescale_option(
                {"timescale": "1ns", "timeprecision": "1ps"}
            ),
            "-timescale=1ns/1ps",
        )

    def test_timescale_provenance_uses_compile_only_manifest_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            staged_source = (
                run_dir
                / "verification"
                / "board_simulation"
                / "vcs_stage"
                / "sources"
                / "board_tb.sv"
            )
            manifest_path = (
                run_dir
                / "verification"
                / "board_simulation"
                / "board_simulation_manifest.json"
            )
            runner_path = (
                run_dir / "verification" / "vcs" / "case_board_vcs_functional.json"
            )
            compile_log = (
                run_dir
                / "verification"
                / "board_simulation"
                / "reports"
                / "vcs_compile.log"
            )
            staged_source.parent.mkdir(parents=True)
            runner_path.parent.mkdir(parents=True)
            compile_log.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            staged_source.write_text(
                "module board_tb;\n`timescale 1ns/1ps\nendmodule\n",
                encoding="utf-8",
            )
            source_hash = hashlib.sha256(staged_source.read_bytes()).hexdigest()
            manifest_path.write_text(
                json.dumps(
                    {
                        "source_files": [
                            {
                                "source_id": "generated-board-source:testbench:board_tb",
                                "path": "generated/board_tb.sv",
                                "sha256": source_hash,
                            }
                        ],
                        "vcs_compile_plan": {
                            "ordered_commands": [
                                {
                                    "executable": "vlogan",
                                    "source_ids": [
                                        "generated-board-source:testbench:board_tb"
                                    ],
                                    "argv": [],
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            runner_path.write_text(json.dumps({"status": "fail"}), encoding="utf-8")
            compile_log.write_text(
                "Error-[ITSFM] Illegal `timescale for module\n"
                "../sources/board_tb.sv, 2\n",
                encoding="utf-8",
            )

            result = localize_vcs_timescale_error_provenance(
                run_dir=run_dir,
                out_dir=out_dir,
                step={"id": "board_timescale", "action": {"target_modules": []}},
            )
            package = json.loads(Path(result["context_package"]).read_text())

        self.assertEqual(result["status"], "pass")
        self.assertEqual(package["diagnostic"]["logged_source"], "../sources/board_tb.sv")
        self.assertEqual(package["source"]["classification"], "immutable_certified_or_sample_source")
        self.assertEqual(package["input_bindings"]["executed_manifest"]["path"], str(manifest_path))

    def test_current_board_materialization_blocker_is_preflight_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
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
                        "board_simulation_preflight_plan": {
                            "validation_mode": "compute_slot_axi"
                        }
                    }
                ),
                encoding="utf-8",
            )
            materialization = {
                "schema_version": "spatialaccagent.dut_weight_binding_materialization.v1",
                "status": "incomplete",
                "manifest": str(manifest_path),
                "manifest_sha256": hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest(),
                "blockers": [
                    "DUT binding has no agent-generated connected single-layer harness"
                ],
            }
            (out_dir / "dut_weight_binding_materialization.json").write_text(
                json.dumps(materialization),
                encoding="utf-8",
            )

            feedback = exact_board_preflight_feedback(run_dir, out_dir)
            self.assertEqual(feedback["status"], "ready")
            self.assertEqual(
                feedback["evidence_kind"],
                "deterministic_board_manifest_and_preflight_failure",
            )

            manifest_path.write_text(
                json.dumps({"board_simulation_preflight_plan": {"validation_mode": "compute_slot_axi"}, "changed": True}),
                encoding="utf-8",
            )
            stale_feedback = exact_board_preflight_feedback(run_dir, out_dir)

        self.assertEqual(stale_feedback["status"], "incomplete")

    def test_board_manifest_replace_preserves_available_lower_layer_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            target.parent.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            stage_harnesses = {
                "stage_00_norm": {"top_module": "Stage00Harness"}
            }
            prior_content = json.dumps(
                {"status": "pass", "stage_harnesses": stage_harnesses}
            )
            target.write_text(prior_content, encoding="utf-8")
            output = {
                "status": "ready_to_apply",
                "approval_required_for": [],
                "file_edits": [
                    {
                        "path": str(target),
                        "operation": "replace",
                        "content": json.dumps(
                            {
                                "status": "incomplete",
                                "multilayer_harness": {"top_module": "BoardHarness"},
                            }
                        ),
                        "expected_sha256": hashlib.sha256(
                            prior_content.encode("utf-8")
                        ).hexdigest(),
                    }
                ],
            }

            result = apply_agent_file_edits(
                output,
                run_dir,
                out_dir,
                allowed_exact_files={target},
                allow_board_integration=True,
            )
            written = json.loads(target.read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "pass")
        self.assertEqual(written["stage_harnesses"], stage_harnesses)
        self.assertNotIn("single_layer_harness", written)
        preservation = next(
            row
            for row in result["protocol_normalizations"]
            if row.get("operation") == "preserve_certified_lower_layer_bindings"
        )
        self.assertEqual(preservation["preserved_fields"], ["stage_harnesses"])

    def test_missing_board_manifest_can_be_initialized_with_merge_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            out_dir.mkdir(parents=True)
            payload = {
                "schema_version": "spatialaccagent.exact_board_binding_manifest.v1",
                "multilayer_harness": {"top_module": "BoardHarness"},
            }

            result = apply_agent_file_edits(
                {
                    "status": "ready_to_apply",
                    "approval_required_for": [],
                    "file_edits": [
                        {
                            "path": str(manifest),
                            "operation": "merge_json",
                            "content": "",
                            "json_content": payload,
                        }
                    ],
                },
                run_dir,
                out_dir,
                allowed_exact_files={manifest},
                allow_board_integration=True,
            )

            self.assertEqual(result["status"], "pass", result["blockers"])
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8")), payload)
            self.assertTrue(
                any(
                    row.get("operation") == "initialize_missing_json_manifest_for_merge"
                    for row in result["protocol_normalizations"]
                )
            )

    def test_compile_only_board_runtime_materialization_is_deferred_before_binding_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            out_dir.mkdir(parents=True)
            with (
                patch.dict(
                    "os.environ",
                    {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"},
                ),
                patch(
                    "accagent.framework.stage_repair_execute.refresh_semantic_board_scope_artifacts",
                    return_value=({"status": "pass"}, []),
                ),
                patch(
                    "accagent.framework.stage_repair_execute.exact_board_memory_runtime_authority",
                    side_effect=AssertionError("compile-only must not require runtime weight authorities"),
                ),
                patch(
                    "accagent.framework.stage_repair_execute.prepare_board_runtime_artifacts",
                    side_effect=AssertionError("runtime materialization must be deferred"),
                ),
            ):
                result = prepare_exact_board_memory_runtime_inputs(
                    run_dir / "repair" / "sacg_state.json",
                    run_dir,
                    out_dir,
                )

            report = json.loads(
                (out_dir / "exact_board_memory_runtime_preparation.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["runtime_materialization_deferred"])
        self.assertEqual(report["artifacts"], {})
        self.assertTrue(report["generation_pending"]["status"] == "pending")

    def test_compile_only_board_agent_prompt_targets_only_real_vcs_compile(self) -> None:
        with patch.dict(
            "os.environ",
            {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"},
        ):
            prompt = "\n".join(
                [
                    exact_board_agent_task("bootstrap"),
                    *board_integration_prompt_rules("bootstrap"),
                ]
            )

        self.assertIn("VCS parse, elaboration, and link", prompt)
        self.assertIn("exact sample-board wrapper", prompt)
        self.assertIn("not compile-only prerequisites", prompt)
        self.assertIn("stage2_vcs_compile_authority", prompt)
        self.assertIn("status=ready_to_apply", prompt)
        self.assertIn("normal next step, not blockers", prompt)
        self.assertNotIn("target-model golden comparison", prompt)
        self.assertNotIn("300 real scalar", prompt)
        self.assertNotIn("full real-weight/runtime artifacts", prompt)

    def test_compile_only_board_canonicalizes_flat_testbench_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            testbench_path = (
                run_dir
                / "generated"
                / "board_integration"
                / "board_tb.sv"
            )
            testbench_path.parent.mkdir(parents=True)
            testbench_path.write_text(
                "module BoardTb; endmodule\n", encoding="utf-8"
            )
            expected_sha256 = hashlib.sha256(
                testbench_path.read_bytes()
            ).hexdigest()
            manifest = {
                "board_simulation_preflight_plan": {
                    "top_module": "BoardTb",
                    "testbench": {
                        "path": str(testbench_path),
                        "sha256": "0" * 64,
                        "source_id": "generated-board-source:testbench:board_tb",
                        "top_module": "BoardTb",
                    },
                }
            }

            with patch.dict(
                "os.environ",
                {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"},
            ):
                normalized = canonicalize_exact_board_manifest_declarations(
                    manifest,
                    run_dir,
                    out_dir,
                )

        testbench = normalized["board_simulation_preflight_plan"]["testbench"]
        self.assertEqual(testbench["sha256"], expected_sha256)
        self.assertEqual(testbench["declared_modules"], ["BoardTb"])

    def test_compile_only_board_canonicalizes_nested_testbench_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            testbench_path = (
                run_dir
                / "generated"
                / "board_integration"
                / "board_tb.sv"
            )
            testbench_path.parent.mkdir(parents=True)
            testbench_path.write_text(
                "module BoardTb; endmodule\n", encoding="utf-8"
            )
            expected_sha256 = hashlib.sha256(
                testbench_path.read_bytes()
            ).hexdigest()
            manifest = {
                "board_simulation_preflight_plan": {
                    "testbench": {
                        "source": {
                            "path": str(testbench_path),
                            "sha256": "0" * 64,
                            "source_id": "generated-board-source:testbench:board_tb",
                        },
                        "top_module": "BoardTb",
                    }
                }
            }

            with patch.dict(
                "os.environ",
                {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"},
            ):
                normalized = canonicalize_exact_board_manifest_declarations(
                    manifest,
                    run_dir,
                    out_dir,
                )

        testbench = normalized["board_simulation_preflight_plan"]["testbench"]
        self.assertEqual(testbench["source"]["sha256"], expected_sha256)
        self.assertEqual(testbench["sha256"], expected_sha256)
        self.assertEqual(testbench["declared_modules"], ["BoardTb"])

    def test_compile_only_board_rebinds_testbench_top_from_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            testbench_path = (
                run_dir
                / "generated"
                / "board_integration"
                / "board_tb.sv"
            )
            testbench_path.parent.mkdir(parents=True)
            testbench_path.write_text(
                "module BoardTb;\n  SampleWrapper dut();\nendmodule\n",
                encoding="utf-8",
            )
            manifest = {
                "board_simulation_preflight_plan": {
                    "top_module": "SampleWrapper",
                    "testbench": {
                        "path": str(testbench_path),
                        "sha256": "0" * 64,
                        "source_id": "generated-board-source:testbench:board_tb",
                        "top_module": "SampleWrapper",
                    },
                }
            }

            with patch.dict(
                "os.environ",
                {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"},
            ):
                normalized = canonicalize_exact_board_manifest_declarations(
                    manifest,
                    run_dir,
                    out_dir,
                )

        plan = normalized["board_simulation_preflight_plan"]
        testbench = plan["testbench"]
        self.assertEqual(plan["top_module"], "BoardTb")
        self.assertEqual(testbench["top_module"], "BoardTb")
        self.assertEqual(testbench["declared_modules"], ["BoardTb"])

    def test_stage2_compile_authority_includes_declared_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report_path = (
                run_dir
                / "verification"
                / "single_layer"
                / "single_layer_functional_report.json"
            )
            certificate_path = (
                run_dir
                / "verification"
                / "certificates"
                / "single_layer_promotion_certificate.json"
            )
            source_path = run_dir / "generated" / "BoardKernel.sv"
            filelist_path = run_dir / "generated" / "sources.f"
            source_path.parent.mkdir(parents=True)
            report_path.parent.mkdir(parents=True)
            certificate_path.parent.mkdir(parents=True)
            source_path.write_text(
                "module BoardKernel(input logic clk); endmodule\n",
                encoding="utf-8",
            )
            filelist_path.write_text(str(source_path) + "\n", encoding="utf-8")
            source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            filelist_hash = hashlib.sha256(filelist_path.read_bytes()).hexdigest()
            report_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "validation_policy": "vcs_compile_only",
                        "top_module": "BoardKernel",
                        "compile_evidence": {
                            "elaboration_output_check": {
                                "status": "pass",
                                "returncode": 0,
                            },
                            "source_files": [
                                {"path": str(source_path), "sha256": source_hash}
                            ],
                            "filelist_path": str(filelist_path),
                            "filelist_sha256": filelist_hash,
                        },
                    }
                ),
                encoding="utf-8",
            )
            binding = {
                "schema_version": "spatialaccagent.promotion_evidence_binding.v1",
                "required_gates": [],
                "file_bindings": [
                    {
                        "path": str(source_path.resolve()),
                        "sha256": source_hash,
                        "role": "source_file",
                    },
                    {
                        "path": str(filelist_path.resolve()),
                        "sha256": filelist_hash,
                        "role": "input_artifact",
                    },
                ],
                "fingerprints": [],
                "excluded_same_scope_promotion_certificates": [],
            }
            binding["binding_sha256"] = promotion_evidence_binding_fingerprint(
                binding
            )
            certificate_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "validation_policy": "vcs_compile_only",
                        "evidence_binding": binding,
                    }
                ),
                encoding="utf-8",
            )

            authority = stage2_compile_only_authority(run_dir)

        self.assertEqual(authority["status"], "ready")
        self.assertEqual(
            authority["source_files"][0]["declared_modules"], ["BoardKernel"]
        )

    def test_compile_only_stage2_source_authority_unblocks_board_generation(self) -> None:
        source_authority = {
            "status": "ready",
            "top_module": "CompiledKernel",
            "module_declaration": "module CompiledKernel(input logic clk);",
            "source_files": [
                {
                    "source_id": "certified_kernel.0000.0123456789abcdef",
                    "path": "/run/generated/CompiledKernel.sv",
                    "sha256": "0" * 64,
                }
            ],
        }
        semantic_testbench = {
            "board": {
                "board_validation_scope": {
                    "mode": "full_model_pipeline_liveness",
                    "validation_layer_indices": list(range(12)),
                },
                "model_layer_count": 12,
                "expected_target_layers": 12,
                "expected_output": {"beats": 64},
            }
        }
        with patch.dict(
            "os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
        ):
            authority, blockers = board_kernel_lifecycle_generation_authority(
                {},
                {"status": "pass"},
                semantic_testbench,
                {"num_hidden_layers": 12},
                certified_binding_attested=False,
                compile_only_source_authority=source_authority,
            )

        self.assertEqual(blockers, [])
        self.assertEqual(authority["status"], "ready")
        self.assertEqual(authority["kernel_top_module"], "CompiledKernel")
        self.assertEqual(
            authority["connected_kernel_binding_status"], "generation_pending"
        )
        self.assertEqual(authority["kernel_source_authority"], source_authority)

    def test_current_static_codegen_failure_replaces_stale_semantic_repair_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report_path = run_dir / "verification" / "case_hierarchy" / "stage_leaf_static.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "blockers": [
                            "required RTL file missing: generated/chisel/GeneratedAxiDdrTop.sv"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "status": "ready_for_agent_patch",
                "action": {
                    "debug_layer": "operator_leaf_modules",
                    "repair_kind": "semantic_loader_harness_binding",
                },
            }

            repaired, reconciliation = reconcile_stale_operator_leaf_codegen_step(
                step,
                run_dir,
            )

        self.assertEqual(
            repaired["action"]["repair_kind"],
            "code_generation_package_recovery",
        )
        self.assertEqual(repaired["stale_repair_kind"], "semantic_loader_harness_binding")
        self.assertEqual(reconciliation["status"], "reconciled")

    def test_current_functional_failure_does_not_replace_leaf_repair_step(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            report_path = run_dir / "verification" / "case_hierarchy" / "stage_leaf_static.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "blockers": [],
                    }
                ),
                encoding="utf-8",
            )
            step = {
                "id": "repair_step.00",
                "scope": "verification_capability_repair",
                "status": "ready_for_agent_patch",
                "action": {
                    "debug_layer": "operator_leaf_modules",
                    "repair_kind": "semantic_loader_harness_binding",
                },
            }

            repaired, reconciliation = reconcile_stale_operator_leaf_codegen_step(
                step,
                run_dir,
            )

        self.assertIsNone(reconciliation)
        self.assertEqual(
            repaired["action"]["repair_kind"],
            "semantic_loader_harness_binding",
        )

    def test_replace_rejects_unchanged_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            target = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            target.parent.mkdir(parents=True)
            content = '{"schema_version": "test"}\n'
            target.write_text(content, encoding="utf-8")

            result = apply_agent_file_edits(
                {
                    "status": "ready_to_apply",
                    "approval_required_for": [],
                    "file_edits": [
                        {
                            "path": str(target),
                            "operation": "replace",
                            "content": content,
                            "expected_sha256": "old-version",
                        }
                    ],
                },
                run_dir,
                out_dir,
                allowed_exact_files={target},
            )
            current_content = target.read_text(encoding="utf-8")

        self.assertNotEqual(result["status"], "pass")
        self.assertIn("replace leaves the file unchanged", result["blockers"][0])
        self.assertEqual(current_content, content)

    def test_empty_json_replace_text_noop_does_not_reject_other_agent_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = (
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
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            source.parent.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            source.write_text('object Harness { val probe = "old" }\n', encoding="utf-8")
            manifest_content = '{"schema_version": "test"}\n'
            manifest.write_text(manifest_content, encoding="utf-8")

            result = apply_agent_file_edits(
                {
                    "status": "ready_to_apply",
                    "approval_required_for": [],
                    "file_edits": [
                        {
                            "path": str(source),
                            "operation": "replace_text",
                            "content": "",
                            "text_replacements": [
                                {"old_text": 'probe = "old"', "new_text": 'probe = "new"'}
                            ],
                        },
                        {
                            "path": str(manifest),
                            "operation": "replace_text",
                            "content": "",
                            "rationale": "No manifest change is required.",
                        },
                    ],
                },
                run_dir,
                run_dir / "repair_execution",
                allowed_exact_files={source, manifest},
            )
            self.assertEqual(result["status"], "pass")
            self.assertEqual([row["path"] for row in result["files"]], [str(source)])
            self.assertTrue(
                any(
                    row.get("operation") == "discard_empty_noop_json_edit"
                    for row in result["protocol_normalizations"]
                )
            )
            self.assertEqual(
                source.read_text(encoding="utf-8"),
                'object Harness { val probe = "new" }\n',
            )
            self.assertEqual(manifest.read_text(encoding="utf-8"), manifest_content)

    def test_nonempty_json_replace_text_still_rejects_the_atomic_edit_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source = run_dir / "generated" / "semantic_harness" / "Harness.scala"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            source.parent.mkdir(parents=True)
            manifest.parent.mkdir(parents=True)
            source.write_text('object Harness { val probe = "old" }\n', encoding="utf-8")
            manifest.write_text('{"schema_version": "test"}\n', encoding="utf-8")
            before_source = source.read_text(encoding="utf-8")

            result = apply_agent_file_edits(
                {
                    "status": "ready_to_apply",
                    "approval_required_for": [],
                    "file_edits": [
                        {
                            "path": str(source),
                            "operation": "replace_text",
                            "content": "",
                            "text_replacements": [
                                {"old_text": 'probe = "old"', "new_text": 'probe = "new"'}
                            ],
                        },
                        {
                            "path": str(manifest),
                            "operation": "replace_text",
                            "content": "",
                            "text_replacements": [
                                {"old_text": "test", "new_text": "changed"}
                            ],
                        },
                    ],
                },
                run_dir,
                run_dir / "repair_execution",
                allowed_exact_files={source, manifest},
            )
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(
                any(
                    "replace_text is not allowed for JSON" in item
                    for item in result["blockers"]
                )
            )
            self.assertTrue(
                result["agent_transaction_rejection"]["file_edits_were_not_applied"]
            )
            self.assertEqual(source.read_text(encoding="utf-8"), before_source)

    def test_batch_with_only_empty_json_replace_text_is_not_a_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            manifest = (
                run_dir
                / "generated"
                / "memory"
                / "dut_weight_binding_manifest.json"
            )
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"schema_version": "test"}\n', encoding="utf-8")

            result = apply_agent_file_edits(
                {
                    "status": "ready_to_apply",
                    "approval_required_for": [],
                    "file_edits": [
                        {
                            "path": str(manifest),
                            "operation": "replace_text",
                            "content": "",
                        }
                    ],
                },
                run_dir,
                run_dir / "repair_execution",
                allowed_exact_files={manifest},
            )

        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "implementation agent returned no effective file edits; all JSON replace_text entries were empty",
            result["blockers"],
        )

    def test_semantic_harness_capability_aliases_use_bounded_existing_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
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
                / "SemanticHarnesses.scala"
            )
            harness.parent.mkdir(parents=True)
            harness.write_text(
                "object ElaborateSemanticHarnesses extends App {\n"
                "  emitSystemVerilog()\n"
                "}\n",
                encoding="utf-8",
            )
            output, errors = normalize_semantic_harness_capability_aliases(
                {
                    "status": "blocked",
                    "file_edits": [],
                    "approval_required_for": [],
                    "requested_validation": [],
                    "required_capabilities": [
                        {
                            "capability_id": "stage5_target_model_reference_rebind",
                            "debug_layer": "operator_leaf_modules",
                            "producer_scope": (
                                "executor-supported upstream reference producer; "
                                "not an agent file edit"
                            ),
                        },
                        {
                            "capability_id": (
                                "operator_leaf_harness_elaboration_and_materialization"
                            ),
                            "debug_layer": "operator_leaf_modules",
                            "producer_scope": (
                                "authorized generated/chisel compilation and "
                                "semantic-harness elaboration"
                            ),
                        },
                    ],
                },
                run_dir,
                verification_scope="operator_leaf_closure",
            )

        self.assertEqual(errors, [])
        self.assertEqual(
            output["required_capabilities"],
            [
                {
                    "capability_id": (
                        "stage5_target_model_reference_rebind_and_intermediate_capture"
                    ),
                    "debug_layer": "reference_preparation",
                    "producer_scope": "case_target_model_reference",
                    "target_modules": [
                        "case_target_model_reference",
                        "case_semantic_testbench",
                    ],
                    "required_evidence": [
                        "current independent-reference provenance"
                    ],
                    "rationale": (
                        "regenerate the immutable target-model reference before "
                        "semantic-harness repair"
                    ),
                }
            ],
        )
        self.assertEqual(
            [request["argv"][-1] for request in output["requested_validation"]],
            [
                "Compile/compile",
                "runMain spatialaccagent.semantic_harness.ElaborateSemanticHarnesses",
            ],
        )
        self.assertTrue(
            validation_only_repair_request(
                output,
                board_integration_repair=False,
            )
        )
        self.assertEqual(
            len(
                required_capability_repair_actions(
                    {
                        "status": "blocked",
                        "validation": {"status": "pass"},
                        "required_capabilities": output["required_capabilities"],
                    }
                )
            ),
            1,
        )

    def test_materialization_failure_projection_keeps_stage_local_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            (out_dir / "dut_weight_binding_materialization.json").write_text(
                json.dumps(
                    {
                        "schema_version": (
                            "spatialaccagent.dut_weight_binding_materialization.v1"
                        ),
                        "status": "incomplete",
                        "manifest": "generated/memory/dut_weight_binding_manifest.json",
                        "manifest_sha256": "a" * 64,
                        "stage_harness_count": 2,
                        "blockers": [
                            "stage_00_layer_norm: source_directory does not exist after elaboration",
                            "stage_00_layer_norm: harness top module is not declared by its source files",
                            "stage_01_attention: semantic harness does not instantiate a generated DUT module",
                            "stage_01_attention: semantic harness interface is missing connected clock_port: clock",
                            "unscoped materialization prerequisite failed",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            projection = materialization_failure_projection(out_dir)
            compact = compact_verification_capability_repair_package(
                {"materialization_failure_projection": projection}
            )

        self.assertEqual(projection["status"], "incomplete")
        self.assertEqual(projection["blocker_count"], 5)
        self.assertEqual(projection["omitted_blocker_count"], 0)
        self.assertEqual(
            [row["stage_id"] for row in projection["stage_diagnostics"]],
            ["stage_00_layer_norm", "stage_01_attention"],
        )
        self.assertIn(
            "source_directory does not exist after elaboration",
            projection["stage_diagnostics"][0]["blockers"],
        )
        self.assertIn(
            "unscoped materialization prerequisite failed",
            projection["unscoped_blockers"],
        )
        self.assertEqual(
            compact["materialization_failure_projection"], projection
        )

    def test_validation_failure_projection_keeps_compiler_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            (out_dir / "agent_requested_validation.json").write_text(
                json.dumps(
                    {
                        "status": "fail",
                        "requests": 2,
                        "blockers": ["Compile/compile failed"],
                        "results": [
                            {
                                "purpose": "compile semantic harnesses",
                                "argv": ["sbt", "Compile/compile"],
                                "cwd": "/tmp/generated/chisel",
                                "status": "fail",
                                "returncode": 1,
                                "stdout_tail": (
                                    "[error] SemanticHarnesses.scala:106: "
                                    "private class WordPacker escapes its defining scope"
                                ),
                                "stderr_tail": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            projection = validation_failure_projection(out_dir)
            compact = compact_verification_capability_repair_package(
                {"validation_failure_projection": projection}
            )

        self.assertEqual(projection["status"], "fail")
        self.assertEqual(projection["failed_result_count"], 1)
        self.assertEqual(
            projection["failed_results"][0]["argv"], ["sbt", "Compile/compile"]
        )
        self.assertIn(
            "WordPacker escapes",
            projection["failed_results"][0]["stdout_tail"],
        )
        self.assertEqual(compact["validation_failure_projection"], projection)

    def test_created_semantic_harness_forces_compile_and_elaboration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_path = (
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
            output, errors = semantic_harness_validation_output(
                {
                    "file_edits": [
                        {
                            "path": str(source_path),
                            "operation": "create",
                            "content": (
                                "object ElaborateSemanticHarnesses extends App { "
                                "emitSystemVerilog() }\n"
                            ),
                        }
                    ],
                    "requested_validation": [],
                },
                run_dir,
                require_elaboration=True,
                required_elaboration_main="ElaborateSemanticHarnesses",
            )

        self.assertEqual(errors, [])
        self.assertEqual(
            [request["argv"][-1] for request in output["requested_validation"]],
            [
                "Compile/compile",
                "runMain spatialaccagent.semantic_harness.ElaborateSemanticHarnesses",
            ],
        )

    def test_semantic_harness_validation_uses_framework_generated_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
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
            (harness_root / "SemanticHarnesses.scala").write_text(
                "object ElaborateSemanticHarnesses extends App { "
                "emitSystemVerilog() }\n",
                encoding="utf-8",
            )
            output, errors = semantic_harness_validation_output(
                {
                    "requested_validation": [
                        {
                            "argv": ["sbt", "--no-server", "Compile/compile"],
                            "cwd": "/incorrect/generated/chisel",
                        }
                    ]
                },
                run_dir,
                require_elaboration=True,
                required_elaboration_main="ElaborateSemanticHarnesses",
            )

        self.assertEqual(errors, [])
        self.assertTrue(
            all(
                request["cwd"] == str(run_dir / "generated" / "chisel")
                for request in output["requested_validation"]
            )
        )

    def test_blocked_capability_response_can_request_validation_without_edits(self) -> None:
        response = {
            "status": "blocked",
            "file_edits": [],
            "approval_required_for": [],
            "requested_validation": [
                {
                    "argv": ["sbt", "-batch", "Compile/compile"],
                    "cwd": "/run/generated/chisel",
                }
            ],
        }

        self.assertTrue(
            validation_only_repair_request(
                response,
                board_integration_repair=False,
            )
        )
        self.assertFalse(
            validation_only_repair_request(
                response,
                board_integration_repair=True,
            )
        )
        self.assertFalse(
            validation_only_repair_request(
                {**response, "approval_required_for": ["sbt validation"]},
                board_integration_repair=False,
            )
        )

    def test_requested_sbt_validation_accepts_common_flags_and_normalizes_compile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            generated_root = run_dir / "generated" / "chisel"
            out_dir = run_dir / "repair_execution"
            generated_root.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            output = {
                "requested_validation": [
                    {
                        "argv": ["sbt", "-batch", "--no-colors", "-error", "Compile"],
                        "cwd": str(generated_root),
                        "purpose": "compile the semantic harness",
                    },
                    {
                        "argv": [
                            "sbt",
                            "--no-server",
                            "--supershell=false",
                            "runMain spatialaccagent.semantic_harness.ElaborateSemanticHarnesses",
                        ],
                        "cwd": str(generated_root),
                        "purpose": "elaborate semantic harnesses",
                    },
                ]
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_local_tool",
                return_value={"status": "pass", "returncode": 0},
            ) as runner:
                report = run_agent_requested_validation(
                    output, run_dir, out_dir, timeout_sec=30
                )

        self.assertEqual(report["status"], "pass")
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(
            runner.call_args_list[0].args[0],
            ["sbt", "-batch", "-no-colors", "-error", "Compile/compile"],
        )
        self.assertEqual(
            runner.call_args_list[1].args[0],
            [
                "sbt",
                "--no-server",
                "--supershell=false",
                "runMain spatialaccagent.semantic_harness.ElaborateSemanticHarnesses",
            ],
        )

    def test_requested_sbt_validation_reports_unknown_options_before_goal_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            generated_root = run_dir / "generated" / "chisel"
            out_dir = run_dir / "repair_execution"
            generated_root.mkdir(parents=True)
            out_dir.mkdir(parents=True)
            output = {
                "requested_validation": [
                    {
                        "argv": ["sbt", "-batch", "--unsafe", "Compile/compile"],
                        "cwd": str(generated_root),
                        "purpose": "invalid option must not execute",
                    }
                ]
            }
            with patch(
                "accagent.framework.stage_repair_execute.run_local_tool"
            ) as runner:
                report = run_agent_requested_validation(
                    output, run_dir, out_dir, timeout_sec=30
                )

        self.assertEqual(report["status"], "fail")
        self.assertIn("disallowed sbt option: --unsafe", report["blockers"][0])
        runner.assert_not_called()

    def test_capability_probe_resolves_declared_target_model_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            out_dir = root / "out"
            run_dir.mkdir()
            out_dir.mkdir()
            selected_python = root / "model-env" / "bin" / "python3"
            selected_python.parent.mkdir(parents=True)
            selected_python.write_text("", encoding="utf-8")
            spec = {
                "name": "case_target_model_reference",
                "argv": ["python3", "scripts/reference.py"],
                "python_modules": ["torch", "transformers", "safetensors"],
                "python_environment_group": "target_model_oracle",
            }
            step = {"id": "repair_step.00", "debug_layer": "operator_leaf_modules"}
            resolution = {
                "status": "pass",
                "selected_executable": str(selected_python),
            }
            with (
                patch(
                    "accagent.framework.stage_repair_execute.resolve_python_execution",
                    return_value=(
                        [str(selected_python), "scripts/reference.py"],
                        resolution,
                        {"PATH": "model-env/bin"},
                    ),
                ),
                patch(
                    "accagent.framework.stage_repair_execute.run_local_tool",
                    return_value={"status": "pass", "returncode": 0, "summary": "returncode=0"},
                ) as runner,
            ):
                result = run_capability_probe(
                    case_adapter={"case_id": "generic-case"},
                    spec_role="target_model_reference_generate",
                    spec=spec,
                    run_dir=run_dir,
                    step=step,
                    out_dir=out_dir,
                    timeout_sec=30,
                )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["requested_argv"], ["python3", "scripts/reference.py"])
        self.assertEqual(result["argv"], [str(selected_python), "scripts/reference.py"])
        self.assertEqual(result["python_environment"], resolution)
        runner.assert_called_once_with(
            [str(selected_python), "scripts/reference.py"],
            Path.cwd(),
            {"PATH": "model-env/bin"},
            30,
        )

    def test_reference_identity_failure_offers_only_supported_reference_regeneration(self) -> None:
        offer = available_target_model_reference_regeneration_capabilities(
            verification_scope="operator_leaf_closure",
            capability_role="semantic_testbench_generate",
            capability_spec={"name": "case_semantic_testbench"},
            capability_probe={
                "status": "fail",
                "case_adapter_tool": "case_semantic_testbench",
                "stderr_tail": "target-model semantic adapter file/hash mismatch",
            },
            capability_reports=[],
        )

        self.assertEqual(len(offer), 1)
        self.assertEqual(
            offer[0]["capability_id"],
            "stage5_target_model_reference_rebind_and_intermediate_capture",
        )
        self.assertEqual(offer[0]["debug_layer"], "reference_preparation")
        self.assertEqual(
            offer[0]["target_modules"],
            ["case_target_model_reference", "case_semantic_testbench"],
        )
        self.assertEqual(
            available_target_model_reference_regeneration_capabilities(
                verification_scope="single_layer_closure",
                capability_role="semantic_testbench_generate",
                capability_spec={"name": "case_semantic_testbench"},
                capability_probe={
                    "status": "fail",
                    "stderr_tail": "target-model semantic adapter file/hash mismatch",
                },
                capability_reports=[],
            ),
            [],
        )

    def test_reference_regeneration_offer_survives_capability_package_compaction(self) -> None:
        offer = [
            {
                "capability_id": "stage5_target_model_reference_rebind_and_intermediate_capture",
                "debug_layer": "reference_preparation",
                "producer_scope": "case_target_model_reference",
                "target_modules": [
                    "case_target_model_reference",
                    "case_semantic_testbench",
                ],
                "required_evidence": ["current independent-reference provenance"],
                "rationale": "regenerate the immutable target-model reference",
            }
        ]

        compact = compact_verification_capability_repair_package(
            {"available_upstream_capabilities": offer}
        )

        self.assertEqual(compact["available_upstream_capabilities"], offer)

    def test_certified_harness_accepts_only_valid_identity_layout_alias(self) -> None:
        binding = {
            "tensor": "layer.0.proj.weight",
            "parameter_suffix": "proj.weight",
            "shape": [2, 4],
            "sha256": "a" * 64,
        }
        layout = build_stage_weight_layout(
            {
                "stage_id": "projection",
                "op": "mlp_gate_proj",
                "template_id": "linear",
                "bound_params": {"lanes": {"value": 2}},
            },
            {},
            [binding],
            {
                "policy_id": "test",
                "default_rules": {"weight_dtype": "fp16", "acc_dtype": "fp32"},
            },
        )
        layout["storage_targets"][0]["source_transform"] = {"kind": "identity"}
        layout["contract_sha256"] = sha256_json(
            {key: value for key, value in layout.items() if key != "contract_sha256"}
        )
        canonical_layout = deepcopy(layout)
        canonical_layout["storage_targets"] = [
            {
                key: value
                for key, value in target.items()
                if key != "source_transform"
            }
            for target in layout["storage_targets"]
        ]
        requirement = {"required_tensors": [binding], "weight_layout": layout}
        harness = {
            "top_module": "ProjectionHarness",
            "consumed_tensor_hashes": [binding["sha256"]],
            "default_or_identity_weight_fallback_disabled": True,
            "weight_layout_contract_sha256": sha256_json(
                {
                    key: value
                    for key, value in canonical_layout.items()
                    if key != "contract_sha256"
                }
            ),
        }
        self.assertEqual(certified_stage_harness_metadata_errors(harness, requirement), [])
        layout["storage_targets"][0]["source_transform"] = {"kind": "transpose_2d"}
        self.assertTrue(
            any(
                "weight-layout contract hash changed" in error
                for error in certified_stage_harness_metadata_errors(harness, requirement)
            )
        )

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

    def test_semantic_harness_contract_authorizes_missing_source_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            requirements = (
                run_dir
                / "verification"
                / "semantic_testbench"
                / "dut_weight_binding_requirements.json"
            )
            requirements.parent.mkdir(parents=True)
            requirements.write_text("{}", encoding="utf-8")

            contract = semantic_harness_source_contract(run_dir)

        self.assertEqual(contract["status"], "pass")
        self.assertTrue(contract["agent_harness_source"]["creation_required"])
        self.assertTrue(
            contract["agent_harness_source"][
                "creation_authorized_when_contract_passes"
            ]
        )
        self.assertTrue(
            contract["artifact_lifecycle"][
                "generated_testbench_is_not_a_prerequisite_for_harness_creation"
            ]
        )

    def test_compact_capability_package_preserves_semantic_harness_contract(self) -> None:
        contract = {
            "status": "pass",
            "agent_harness_source": {"creation_required": True},
        }
        compact = compact_verification_capability_repair_package(
            {
                "repair_source_bundle": {
                    "schema_version": "spatialaccagent.repair_source_bundle.v1",
                    "documents": [],
                    "semantic_harness_source_contract": contract,
                }
            }
        )

        self.assertEqual(
            compact["repair_source_bundle"]["semantic_harness_source_contract"],
            contract,
        )

    def test_compact_capability_package_preserves_declared_template_source(self) -> None:
        template_path = (
            "run/generated/chisel/src/main/scala/spatialaccagent/templates/"
            "Attention.scala"
        )
        source = "class Attention { val exactPortDefinition = 42 }"
        compact = compact_verification_capability_repair_package(
            {
                "verification_scope": "operator_leaf_closure",
                "repair_source_bundle": {
                    "schema_version": "spatialaccagent.repair_source_bundle.v1",
                    "documents": [
                        {
                            "path": template_path,
                            "content": source,
                            "truncated": False,
                        }
                    ],
                    "editable_contract": {
                        "read_only_template_sources": [template_path]
                    },
                },
            }
        )

        document = compact["repair_source_bundle"]["documents"][0]
        self.assertEqual(document["content"], source)

    def test_reference_regeneration_capability_uses_adapter_tools_in_order(self) -> None:
        capability = {
            "capability_id": "stage5_target_model_reference_rebind_and_intermediate_capture",
            "debug_layer": "reference_preparation",
            "producer_scope": "case_target_model_reference",
            "target_modules": ["case_target_model_reference", "case_semantic_testbench"],
            "required_evidence": ["current independent-reference provenance"],
            "rationale": "rebuild the target-model oracle before semantic harness repair",
        }
        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "required_capabilities": [capability],
            }
        )

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["repair_kind"], "target_model_reference_regeneration")
        self.assertEqual(actions[0]["debug_layer"], "operator_leaf_modules")
        self.assertEqual(actions[0]["requested_debug_layer"], "reference_preparation")
        self.assertEqual(
            actions[0]["producer_tools"],
            [
                "case_weight_manifest_generate",
                "case_target_model_reference",
                "case_semantic_testbench",
                "framework_dut_weight_binding_materialization",
                "case_semantic_testbench",
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            source_state = run_dir / "repair" / "sacg_state.json"
            source_state.parent.mkdir(parents=True)
            source_state.write_text("{}", encoding="utf-8")
            out_dir.mkdir(parents=True)
            adapter = {
                "case_id": "generic-case",
                "tools": {
                    "weight_manifest_generate": {"name": "case_weight_manifest_generate"},
                    "target_model_reference_generate": {"name": "case_target_model_reference"},
                    "semantic_testbench_generate": {"name": "case_semantic_testbench"},
                },
            }
            calls: list[str] = []

            def probe(**kwargs: object) -> dict[str, object]:
                calls.append(str(kwargs["spec_role"]))
                if len(calls) == 3:
                    requirements = (
                        run_dir
                        / "verification"
                        / "semantic_testbench"
                        / "dut_weight_binding_requirements.json"
                    )
                    requirements.parent.mkdir(parents=True, exist_ok=True)
                    requirements.write_text(
                        json.dumps(
                            {
                                "schema_version": (
                                    "spatialaccagent.dut_weight_binding_requirements.v1"
                                ),
                                "status": "requirements",
                            }
                        ),
                        encoding="utf-8",
                    )
                return {"status": "pass", "summary": "returncode=0"}

            step = {
                "id": "repair_step.00",
                "action": actions[0],
            }
            with (
                patch(
                    "accagent.framework.stage_repair_execute.case_adapter_for_state",
                    return_value=adapter,
                ),
                patch(
                    "accagent.framework.stage_repair_execute.run_capability_probe",
                    side_effect=probe,
                ),
                patch(
                    "accagent.framework.stage_repair_execute.finalize_dut_weight_binding_manifest",
                    return_value={"status": "pass", "path": "binding.json"},
                ),
            ):
                result = execute_verification_capability_repair(
                    step,
                    source_state,
                    run_dir,
                    out_dir,
                    timeout_sec=30,
                )

            package = json.loads(Path(result["context_package"]).read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["stage_passed"])
        self.assertFalse(result["requires_agent_followup"])
        self.assertEqual(
            calls,
            [
                "weight_manifest_generate",
                "target_model_reference_generate",
                "semantic_testbench_generate",
                "semantic_testbench_generate",
            ],
        )
        self.assertEqual(package["tool_order"], actions[0]["producer_tools"])

    def test_codegen_package_recovery_capability_uses_frozen_stage5_generator(self) -> None:
        capabilities = [
            (
                "code_generation_package_recovery",
                "current supplied repair action "
                "repair.operator_leaf.codegen_contract_and_output_recovery",
            ),
            (
                "contract_complete_codegen_package_regeneration",
                "existing authorized case-adapter code-generation package producer",
            ),
            ("codegen_output_contract_repair_inputs", "stage5_code_generation_package"),
            (
                "authorized_codegen_package_producer_mapping",
                "repair.localize_codegen_package_precondition",
            ),
            (
                "code_generation_producer_recovery",
                "current generated-code package and output-manifest producer",
            ),
            (
                "operator_leaf_generated_axi_ddr_top_source_closure",
                "authoritative generated/chisel code-generation producer/package configuration, not supplied in the current repair bundle",
            ),
        ]
        for capability_id, producer_scope in capabilities:
            with self.subTest(capability_id=capability_id):
                actions = required_capability_repair_actions(
                    {
                        "status": "blocked",
                        "validation": {"status": "pass"},
                        "required_capabilities": [
                            {
                                "capability_id": capability_id,
                                "debug_layer": "operator_leaf_modules",
                                "producer_scope": producer_scope,
                                "target_modules": [
                                    "GeneratedAxiDdrTop",
                                    "operator_leaf_modules",
                                ],
                                "required_evidence": [
                                    "the bound generator command that emits GeneratedAxiDdrTop.sv",
                                    "a passing code-generation compile/package report",
                                ],
                                "rationale": (
                                    "restore the missing generated AXI/DDR top before "
                                    "leaf replay"
                                ),
                            }
                        ],
                    }
                )

                self.assertEqual(len(actions), 1)
                self.assertEqual(actions[0]["scope"], "verification_capability_repair")
                self.assertEqual(
                    actions[0]["repair_kind"], "code_generation_package_recovery"
                )
                self.assertEqual(
                    actions[0]["frozen_upstream_artifacts"],
                    [
                        "artifact.stage2.template_selection",
                        "artifact.stage3.pipeline_plan",
                        "artifact.stage4.parameter_binding",
                    ],
                )
                self.assertFalse(actions[0]["generated_rtl_edits"])

        actions = required_capability_repair_actions(
            {
                "status": "blocked",
                "validation": {"status": "pass"},
                "required_capabilities": [
                    {
                        "capability_id": "code_generation_package_recovery",
                        "debug_layer": "operator_leaf_modules",
                        "producer_scope": capabilities[0][1],
                        "target_modules": ["GeneratedAxiDdrTop"],
                        "required_evidence": ["fresh compile gate"],
                        "rationale": "recover the declared output",
                    }
                ],
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            source_state = run_dir / "repair" / "sacg_state.json"
            out_dir = run_dir / "repair_execution"
            source_state.parent.mkdir(parents=True)
            source_state.write_text("{}", encoding="utf-8")
            out_dir.mkdir(parents=True)
            step = {"id": "repair_step.00", "action": actions[0]}
            expected = {"status": "pass", "summary": "generated package recovered"}
            with patch(
                "accagent.framework.stage_repair_execute.recover_codegen_package_from_frozen_contract",
                return_value=expected,
            ) as recovery:
                result = execute_verification_capability_repair(
                    step,
                    source_state,
                    run_dir,
                    out_dir,
                    1,
                )

        self.assertEqual(result, expected)
        recovery.assert_called_once_with(
            source_state=source_state,
            run_dir=run_dir,
            out_dir=out_dir,
            step=step,
        )

    def test_immutable_provenance_capability_aliases_use_only_reference_regeneration(
        self,
    ) -> None:
        for capability_id, producer_scope in (
            (
                "case_semantic_testbench_immutable_provenance_reconciliation",
                "authorized upstream case-adapter verification-preparation producer",
            ),
            (
                "case_adapter_immutable_reference_provenance_reconciliation",
                "upstream case-adapter semantic-testbench/reference producer; "
                "no authorized producer invocation is supplied in this repair package",
            ),
        ):
            with self.subTest(capability_id=capability_id):
                actions = required_capability_repair_actions(
                    {
                        "status": "blocked",
                        "validation": {"status": "pass"},
                        "required_capabilities": [
                            {
                                "capability_id": capability_id,
                                "debug_layer": "operator_leaf_modules",
                                "producer_scope": producer_scope,
                                "target_modules": ["case_semantic_testbench"],
                                "required_evidence": [
                                    "new immutable provenance reconciliation artifact"
                                ],
                                "rationale": (
                                    "reconcile immutable verification-preparation "
                                    "provenance before semantic harness repair"
                                ),
                            }
                        ],
                    }
                )

                self.assertEqual(len(actions), 1)
                self.assertEqual(
                    actions[0]["repair_kind"], "target_model_reference_regeneration"
                )
                self.assertEqual(actions[0]["scope"], "verification_capability_repair")
                self.assertEqual(actions[0]["debug_layer"], "operator_leaf_modules")
                self.assertEqual(actions[0]["requested_capability_id"], capability_id)
                self.assertEqual(
                    actions[0]["producer_tools"],
                    [
                        "case_weight_manifest_generate",
                        "case_target_model_reference",
                        "case_semantic_testbench",
                        "framework_dut_weight_binding_materialization",
                        "case_semantic_testbench",
                    ],
                )
                self.assertNotIn("rtl_edit", actions[0])
                self.assertNotIn("golden_edit", actions[0])

        self.assertEqual(
            required_capability_repair_actions(
                {
                    "status": "blocked",
                    "validation": {"status": "pass"},
                    "required_capabilities": [
                        {
                            "capability_id": (
                                "case_adapter_immutable_reference_provenance_"
                                "reconciliation"
                            ),
                            "debug_layer": "operator_leaf_modules",
                            "producer_scope": "unrelated local manifest producer",
                            "target_modules": ["case_semantic_testbench"],
                            "required_evidence": ["immutable provenance artifact"],
                            "rationale": "the producer is not case-adapter upstream scope",
                        }
                    ],
                }
            ),
            [],
        )

    def test_reference_regeneration_stops_before_final_semantic_gate_when_binding_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            out_dir = run_dir / "repair_execution"
            source_state = run_dir / "repair" / "sacg_state.json"
            source_state.parent.mkdir(parents=True)
            source_state.write_text("{}", encoding="utf-8")
            out_dir.mkdir(parents=True)
            adapter = {
                "case_id": "generic-case",
                "tools": {
                    "weight_manifest_generate": {"name": "case_weight_manifest_generate"},
                    "target_model_reference_generate": {
                        "name": "case_target_model_reference"
                    },
                    "semantic_testbench_generate": {"name": "case_semantic_testbench"},
                },
            }
            calls: list[str] = []

            def probe(**kwargs: object) -> dict[str, object]:
                calls.append(str(kwargs["spec_role"]))
                if len(calls) == 3:
                    requirements = (
                        run_dir
                        / "verification"
                        / "semantic_testbench"
                        / "dut_weight_binding_requirements.json"
                    )
                    requirements.parent.mkdir(parents=True, exist_ok=True)
                    requirements.write_text(
                        json.dumps(
                            {
                                "schema_version": (
                                    "spatialaccagent.dut_weight_binding_requirements.v1"
                                ),
                                "status": "requirements",
                            }
                        ),
                        encoding="utf-8",
                    )
                return {"status": "pass", "summary": "returncode=0"}

            step = {
                "id": "repair_step.00",
                "action": {
                    "repair_kind": "target_model_reference_regeneration"
                },
            }
            with (
                patch(
                    "accagent.framework.stage_repair_execute.case_adapter_for_state",
                    return_value=adapter,
                ),
                patch(
                    "accagent.framework.stage_repair_execute.run_capability_probe",
                    side_effect=probe,
                ),
                patch(
                    "accagent.framework.stage_repair_execute.finalize_dut_weight_binding_manifest",
                    return_value={
                        "status": "incomplete",
                        "blockers": ["stage_00: semantic harness is missing"],
                    },
                ),
            ):
                result = execute_verification_capability_repair(
                    step,
                    source_state,
                    run_dir,
                    out_dir,
                    timeout_sec=30,
                )

            package = json.loads(
                Path(result["context_package"]).read_text(encoding="utf-8")
            )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(
            result["failed_tool"], "framework_dut_weight_binding_materialization"
        )
        self.assertEqual(
            calls,
            [
                "weight_manifest_generate",
                "target_model_reference_generate",
                "semantic_testbench_generate",
            ],
        )
        self.assertEqual(len(package["tool_results"]), 4)

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
            checkpoint_inventory_path = verification_dir / "model_weights" / "checkpoint_inventory.json"
            static_report_path = (
                verification_dir / "case_hierarchy" / "stage_leaf_static.json"
            )
            case_adapter_path = input_dir / "case_adapter.json"
            pipeline_plan_path = pipeline_dir / "pipeline_plan.json"
            script_path.write_text("print('catalog')\n", encoding="utf-8")
            argv_input_path.write_text('{"adapter": "current"}\n', encoding="utf-8")
            output_path.parent.mkdir()
            output_path.write_text('{"status": "partial"}\n', encoding="utf-8")
            checkpoint_inventory_path.write_text(
                '{"status": "diagnostic", "header_tensor_names": ["h.0.attn.weight"]}\n',
                encoding="utf-8",
            )
            static_report_path.parent.mkdir()
            static_report_path.write_text(
                '{"status": "fail", "blockers": ["GeneratedAxiDdrTop.sv is missing"]}\n',
                encoding="utf-8",
            )
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
                            "artifacts": [
                                {"path": str(output_path)},
                                {"path": str(checkpoint_inventory_path)},
                            ]
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
                                "checker": "real_tool.case_stage_leaf_static",
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
                str(checkpoint_inventory_path),
                str(static_report_path),
                str(case_adapter_path),
                str(pipeline_plan_path),
            }.issubset(document_paths)
        )
        context = bundle["earliest_failed_real_tool_context"]
        self.assertEqual(context["tool_record"], str(tool_record_path))
        self.assertEqual(context["file_valued_argv_inputs"], [str(script_path), str(argv_input_path)])
        self.assertEqual(
            context["produced_reports"],
            [
                str(output_path),
                str(checkpoint_inventory_path),
                str(static_report_path),
            ],
        )
        self.assertEqual(
            {entry["path"] for entry in context["semantic_authority"]},
            {str(case_adapter_path), str(pipeline_plan_path)},
        )


if __name__ == "__main__":
    unittest.main()
