import json
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.stage_debug_loop import validated_scope_certificate
from accagent.framework.stage_verification import (
    append_stage6_agent_gate_checks,
    build_promotion_evidence_binding,
    build_results,
    check_required_real_tool_evidence,
    run_verification,
    stage6_selector_blockers,
)
from accagent.framework.stage_verification_plan import current_certificate_validation_summary
from accagent.framework.verification_evidence_contract import (
    PROMOTION_CERTIFICATE_SCHEMA_VERSION,
    PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
    certificate_contract_errors,
    certificate_contract_fingerprint,
    evidence_contract_for_level,
    promotion_evidence_binding_fingerprint,
    promotion_evidence_binding_errors,
    semantic_evidence_report_errors,
    selector_contract_matches_certificate,
    sha256_file,
    tool_environment_contract,
    tool_evidence_contract_errors,
)


def live_evidence_binding(root: Path, gates: list[str]) -> dict:
    rows = []
    for index, gate in enumerate(gates):
        path = root / f"evidence_{index}.json"
        path.write_text(json.dumps({"gate": gate}), encoding="utf-8")
        rows.append(
            {
                "gate": gate,
                "path": str(path),
                "sha256": sha256_file(path),
                "role": "source_file",
            }
        )
    binding = {
        "schema_version": PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
        "required_gates": sorted(gates),
        "file_bindings": rows,
        "fingerprints": [],
    }
    binding["binding_sha256"] = promotion_evidence_binding_fingerprint(binding)
    return binding


class VerificationEvidenceContractTest(TestCase):
    def test_compile_only_pass_reconciles_only_the_supplied_current_scope_contract(self) -> None:
        contract = {
            "status": "ready",
            "target_stage": "stage6.verification",
            "verification_scope": "board_axi_ddr_closure",
            "eligible_contamination_barrier_ids": ["contamination_barrier.0005"],
            "eligible_retry_request_ids": ["retry_request.0002"],
        }
        results = {
            "status": "pass",
            "results": [{"checker": "real_tool.case_vcs_functional_sim", "status": "pass"}],
            "retry_reconciliation_contract": contract,
        }

        errors = append_stage6_agent_gate_checks(
            results, {}, {"mode": "deterministic_compile_only"}
        )

        self.assertEqual(errors, [])
        self.assertEqual(results["status"], "pass")
        self.assertEqual(
            results["sacg_reconciliation"]["contract"], contract
        )
        self.assertEqual(
            results["sacg_reconciliation"]["source"], "compile_only_policy"
        )

    def test_compile_only_failure_does_not_reconcile_stage6_barriers(self) -> None:
        results = {
            "status": "pass",
            "results": [{"checker": "real_tool.case_vcs_functional_sim", "status": "fail"}],
            "retry_reconciliation_contract": {
                "status": "ready",
                "eligible_contamination_barrier_ids": ["contamination_barrier.0005"],
            },
        }

        errors = append_stage6_agent_gate_checks(
            results, {}, {"mode": "deterministic_compile_only"}
        )

        self.assertEqual(errors, [])
        self.assertEqual(results["status"], "fail")
        self.assertNotIn("sacg_reconciliation", results)

    def test_all_levels_have_one_standard_regardless_of_environment(self) -> None:
        levels = (
            "operator_leaf_functional", "single_layer_functional",
            "multilayer_pipeline_functional", "axi_ddr_functional",
        )
        for setting in ("", "full_semantic_simulation", "vcs_compile_only"):
            with self.subTest(setting=setting), patch.dict(
                "os.environ", {"SPATIALACC_VERIFICATION_POLICY": setting}
            ):
                for level in levels:
                    contract = evidence_contract_for_level(level)
                    self.assertTrue(contract["vcs_compile_and_elaboration_required"])
                    self.assertFalse(contract["simulation_execution_required"])
                    self.assertFalse(contract["functional_semantics_claimed"])
                    self.assertNotIn("dut_weight_consumption_proof_required", contract)

    def test_compile_only_accepts_only_a_passing_required_vcs_tool(self) -> None:
        passed = [{
            "checker": "real_tool.case_vcs_functional_sim",
            "status": "pass",
            "required": True,
            "required_group": "functional_sim",
            "acceptance_role": "functional_sim_candidate",
        }]
        failed = [{**passed[0], "status": "fail"}]
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}):
            self.assertEqual(check_required_real_tool_evidence(passed)[0], "pass")
            self.assertEqual(check_required_real_tool_evidence(failed)[0], "fail")

    def test_retired_environment_setting_cannot_restore_old_acceptance_rules(self) -> None:
        result = [{
            "checker": "real_tool.case_vcs_functional_sim",
            "status": "pass",
            "required": True,
            "required_group": "functional_sim",
            "acceptance_role": "scaffold_liveness_not_functional_acceptance",
        }]
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "full_semantic_simulation"}):
            self.assertEqual(check_required_real_tool_evidence(result)[0], "pass")

    def test_promotion_binding_tracks_current_rtl_from_real_tool_report(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "CurrentDut.sv"
            source.write_text("module CurrentDut; endmodule\n", encoding="utf-8")
            report = root / "functional_report.json"
            report.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "execution": {
                            "input_fingerprint_sha256": "a" * 64,
                            "source_files": [str(source)],
                        },
                    }
                ),
                encoding="utf-8",
            )
            tool_log = root / "tool.json"
            tool_log.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "log_path": str(tool_log),
                        "produced_reports": [{"path": str(report), "status": "pass"}],
                    }
                ),
                encoding="utf-8",
            )
            selector = root / "selector.json"
            selector.write_text("{}", encoding="utf-8")
            gate = "case_single_layer_functional"
            binding, errors = build_promotion_evidence_binding(
                {"required_gates": [{"name": gate, "status": "pass", "log_path": str(tool_log)}]},
                [{"log_path": str(tool_log)}],
                [gate],
                root,
                selector,
                root / "certificate_snapshots",
            )
            self.assertEqual(errors, [])
            self.assertTrue(
                any(row["role"] == "source_file" and row["path"] == str(source) for row in binding["file_bindings"])
            )
            self.assertTrue(
                any(row["name"] == "input_fingerprint_sha256" for row in binding["fingerprints"])
            )
            payload = {
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "evidence_binding": binding,
            }
            self.assertEqual(promotion_evidence_binding_errors(payload, [gate]), [])
            tool_log.write_text('{"status":"later-stage-overwrite"}', encoding="utf-8")
            report.write_text('{"status":"later-stage-overwrite"}', encoding="utf-8")
            self.assertEqual(promotion_evidence_binding_errors(payload, [gate]), [])
            source.write_text("module CurrentDut; wire changed; endmodule\n", encoding="utf-8")
            self.assertTrue(promotion_evidence_binding_errors(payload, [gate]))

    def test_compile_only_manifest_runtime_refresh_uses_runner_projection_binding(self) -> None:
        from scripts.verification.case_board_vcs_functional import (
            preflight_manifest_projection_sha256,
        )

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "verification/board_simulation/board_simulation_manifest.json"
            manifest_path.parent.mkdir(parents=True)
            original_manifest = {
                "status": "ready",
                "source_closure_sha256": "a" * 64,
                "runtime_loader_results": [],
            }
            manifest_path.write_text(json.dumps(original_manifest), encoding="utf-8")
            original_sha = sha256_file(manifest_path)
            refreshed_manifest = {
                **original_manifest,
                "runtime_loader_results": [{"status": "ready"}],
            }
            manifest_path.write_text(json.dumps(refreshed_manifest), encoding="utf-8")
            projection = preflight_manifest_projection_sha256(refreshed_manifest)

            runner_report = root / "verification/vcs/case_board_vcs_functional.json"
            runner_report.parent.mkdir(parents=True)
            runner_report.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "hardware_validation_status": "compile_only_pass",
                        "exact_board_preflight_passed": True,
                        "preflight_manifest_projection_sha256": projection,
                        "compile": {"status": "pass", "returncode": 0},
                    }
                ),
                encoding="utf-8",
            )
            tool_log = root / "tool.json"
            tool_document = {
                "status": "pass",
                "log_path": str(tool_log),
                "execution_fingerprint": {
                    "payload": {
                        "consumes": [
                            {"path": str(manifest_path), "sha256": original_sha}
                        ]
                    }
                },
                "produced_reports": [
                    {"path": str(runner_report), "status": "pass"}
                ],
            }
            tool_log.write_text(json.dumps(tool_document), encoding="utf-8")
            selector = root / "selector.json"
            selector.write_text("{}", encoding="utf-8")
            gate = "case_vcs_functional_sim"

            binding, errors = build_promotion_evidence_binding(
                {"required_gates": [{"name": gate, "status": "pass", "log_path": str(tool_log)}]},
                [tool_document],
                [gate],
                root,
                selector,
            )

            self.assertEqual(errors, [])
            self.assertTrue(
                any(
                    row["path"] == str(manifest_path)
                    and row["sha256"] == sha256_file(manifest_path)
                    for row in binding["file_bindings"]
                )
            )
            self.assertTrue(
                any(
                    row["name"] == "board_manifest_preflight_projection_sha256"
                    and row["value"] == projection
                    for row in binding["fingerprints"]
                )
            )

            refreshed_manifest["source_closure_sha256"] = "b" * 64
            manifest_path.write_text(json.dumps(refreshed_manifest), encoding="utf-8")
            _, errors = build_promotion_evidence_binding(
                {"required_gates": [{"name": gate, "status": "pass", "log_path": str(tool_log)}]},
                [tool_document],
                [gate],
                root,
                selector,
            )
            self.assertTrue(any("live evidence hash already drifted" in error for error in errors))

    def test_promotion_binding_separates_tensor_content_identity_from_file_bytes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tensor = root / "weight.pt"
            tensor.write_bytes(b"serialized-tensor-bytes")
            report = root / "reference_manifest.json"
            report.write_text(
                json.dumps(
                    {
                        "weights": [
                            {
                                "path": str(tensor),
                                "file_sha256": sha256_file(tensor),
                                "sha256": "a" * 64,
                                "shape": [4, 8],
                                "dtype": "torch.float32",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            tool_log = root / "tool.json"
            tool_log.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "log_path": str(tool_log),
                        "produced_reports": [{"path": str(report), "status": "pass"}],
                    }
                ),
                encoding="utf-8",
            )
            selector = root / "selector.json"
            selector.write_text("{}", encoding="utf-8")
            gate = "case_leaf_functional"

            binding, errors = build_promotion_evidence_binding(
                {"required_gates": [{"name": gate, "status": "pass", "log_path": str(tool_log)}]},
                [{"log_path": str(tool_log)}],
                [gate],
                root,
                selector,
                root / "certificate_snapshots",
            )

            self.assertEqual(errors, [])
            tensor_row = next(row for row in binding["file_bindings"] if row["path"] == str(tensor))
            self.assertEqual(tensor_row["sha256"], sha256_file(tensor))
            self.assertTrue(
                any(
                    row["kind"] == "declared_nonbyte_content_identity"
                    and row["value"] == "a" * 64
                    and row["artifact_path"] == str(tensor)
                    for row in binding["fingerprints"]
                )
            )
            payload = {
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "evidence_binding": binding,
            }
            self.assertEqual(promotion_evidence_binding_errors(payload, [gate]), [])
            tensor.write_bytes(b"mutated-tensor-bytes")
            self.assertTrue(promotion_evidence_binding_errors(payload, [gate]))

    def test_operator_leaf_binding_excludes_later_scope_generated_vectors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            board_vector = (
                root / "verification" / "semantic_testbench" / "board" / "expected.memh"
            )
            board_vector.parent.mkdir(parents=True)
            board_vector.write_text("00000000\n", encoding="ascii")
            report = root / "semantic_manifest.json"
            report.write_text(
                json.dumps(
                    {
                        "board_output": {
                            "path": str(board_vector),
                            "file_sha256": sha256_file(board_vector),
                            "tensor_sha256": "a" * 64,
                        }
                    }
                ),
                encoding="utf-8",
            )
            tool_log = root / "tool.json"
            tool_log.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "log_path": str(tool_log),
                        "produced_reports": [{"path": str(report), "status": "pass"}],
                    }
                ),
                encoding="utf-8",
            )
            selector = root / "selector.json"
            selector.write_text("{}", encoding="utf-8")

            binding, errors = build_promotion_evidence_binding(
                {
                    "required_gates": [
                        {
                            "name": "case_semantic_testbench",
                            "status": "pass",
                            "log_path": str(tool_log),
                        }
                    ]
                },
                [{"log_path": str(tool_log)}],
                ["case_semantic_testbench"],
                root,
                selector,
                root / "certificate_snapshots",
                current_promotion_artifact_id=(
                    "artifact.stage6.operator_leaf_promotion_certificate"
                ),
            )

            self.assertEqual(errors, [])
            self.assertFalse(
                any(
                    row["path"] == str(board_vector)
                    for row in binding["file_bindings"]
                )
            )
            self.assertFalse(
                any(
                    row.get("artifact_path") == str(board_vector)
                    for row in binding["fingerprints"]
                )
            )

    def test_derived_input_manifest_drift_does_not_invalidate_lower_layer_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = root / "semantic_testbench_manifest.json"
            manifest.write_text('{"scope":"single_layer"}', encoding="utf-8")
            evidence = root / "immutable_functional_report.json"
            evidence.write_text('{"status":"pass"}', encoding="utf-8")
            gate = "case_single_layer_functional"
            binding = {
                "schema_version": PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
                "required_gates": [gate],
                "file_bindings": [
                    {
                        "gate": gate,
                        "path": str(evidence),
                        "sha256": sha256_file(evidence),
                        "role": "evidence_artifact",
                    },
                    {
                        "gate": gate,
                        "path": str(manifest),
                        "sha256": sha256_file(manifest),
                        "role": "input_artifact",
                    },
                ],
                "fingerprints": [],
            }
            binding["binding_sha256"] = promotion_evidence_binding_fingerprint(binding)
            payload = {
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "evidence_binding": binding,
            }

            manifest.write_text('{"scope":"board"}', encoding="utf-8")

            self.assertEqual(promotion_evidence_binding_errors(payload, [gate]), [])

    def test_promotion_binding_excludes_same_scope_prior_certificate_but_keeps_lower_scope_input(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            previous_certificate = root / "operator_leaf_promotion_certificate.json"
            previous_certificate.write_text(
                json.dumps(
                    {
                        "artifact_id": "artifact.stage6.operator_leaf_promotion_certificate",
                        "status": "pass",
                    }
                ),
                encoding="utf-8",
            )
            report = root / "semantic_testbench_manifest.json"
            report.write_text(
                json.dumps(
                    {
                        "reused_operator_leaf_promotion_certificate": {
                            "path": str(previous_certificate),
                            "sha256": sha256_file(previous_certificate),
                        }
                    }
                ),
                encoding="utf-8",
            )
            tool_log = root / "tool.json"
            tool_log.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "log_path": str(tool_log),
                        "produced_reports": [{"path": str(report), "status": "pass"}],
                    }
                ),
                encoding="utf-8",
            )
            selector = root / "selector.json"
            selector.write_text("{}", encoding="utf-8")
            gate = "case_semantic_testbench"
            gate_summary = {"required_gates": [{"name": gate, "status": "pass", "log_path": str(tool_log)}]}
            tool_results = [{"log_path": str(tool_log)}]

            same_scope, errors = build_promotion_evidence_binding(
                gate_summary,
                tool_results,
                [gate],
                root,
                selector,
                root / "same_scope_snapshots",
                current_promotion_artifact_id="artifact.stage6.operator_leaf_promotion_certificate",
            )
            self.assertEqual(errors, [])
            self.assertFalse(
                any(row["path"] == str(previous_certificate) for row in same_scope["file_bindings"])
            )
            self.assertEqual(
                same_scope["excluded_same_scope_promotion_certificates"][0]["artifact_id"],
                "artifact.stage6.operator_leaf_promotion_certificate",
            )
            lower_scope, errors = build_promotion_evidence_binding(
                gate_summary,
                tool_results,
                [gate],
                root,
                selector,
                root / "lower_scope_snapshots",
                current_promotion_artifact_id="artifact.stage6.single_layer_promotion_certificate",
            )
            self.assertEqual(errors, [])
            self.assertTrue(
                any(row["path"] == str(previous_certificate) for row in lower_scope["file_bindings"])
            )
            same_scope_payload = {
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "evidence_binding": same_scope,
            }
            previous_certificate.write_text('{"artifact_id":"artifact.stage6.operator_leaf_promotion_certificate","status":"replacement"}', encoding="utf-8")
            self.assertEqual(promotion_evidence_binding_errors(same_scope_payload, [gate]), [])

    def test_old_certificate_cannot_cover_current_real_weight_contract(self) -> None:
        gates = ["case_leaf_functional", "case_leaf_golden_compare"]
        old = {
            "status": "pass",
            "required_gates": [{"name": gate, "status": "pass"} for gate in gates],
        }

        self.assertTrue(certificate_contract_errors(old, "operator_leaf_functional", gates))

        with TemporaryDirectory() as temp_dir:
            current = {
                **old,
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
                "evidence_contract_fingerprint": certificate_contract_fingerprint(
                    "operator_leaf_functional", gates
                ),
                "tool_environment_contract": tool_environment_contract({"target_model_oracle": "abc"}),
                "evidence_binding": live_evidence_binding(Path(temp_dir), gates),
            }
            self.assertEqual(certificate_contract_errors(current, "operator_leaf_functional", gates), [])

    def test_debug_loop_rejects_stale_certificate_and_accepts_current_one(self) -> None:
        gates = ["case_leaf_functional", "case_leaf_golden_compare"]
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cert_path = root / "operator_leaf.json"
            selector_path = root / "selector.json"
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage6.operator_leaf_promotion_certificate",
                        "path": str(cert_path),
                        "producer_transition": "transition.0001",
                        "trust_status": "validated",
                    },
                    {
                        "id": "artifact.stage5.stage6_gate_selector_contract",
                        "path": str(selector_path),
                    },
                ],
                "transitions": [{"id": "transition.0001", "status": "promoted"}],
            }
            selector = {
                "operator_leaf_promotion_certificate": {
                    "required_gates": gates,
                    "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
                }
            }
            selector_path.write_text(json.dumps(selector), encoding="utf-8")
            cert_path.write_text(
                json.dumps(
                    {
                        "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                        "status": "pass",
                        "required_gates": [{"name": gate, "status": "pass"} for gate in gates],
                    }
                ),
                encoding="utf-8",
            )
            self.assertIsNone(validated_scope_certificate(state, "operator_leaf_closure"))
            self.assertFalse(
                current_certificate_validation_summary(state)["scopes"][0]["current_contract_valid"]
            )

            cert_path.write_text(
                json.dumps(
                    {
                        "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                        "status": "pass",
                        "required_gates": [{"name": gate, "status": "pass"} for gate in gates],
                        "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
                        "evidence_contract_fingerprint": certificate_contract_fingerprint(
                            "operator_leaf_functional", gates
                        ),
                        "tool_environment_contract": tool_environment_contract({"target_model_oracle": "abc"}),
                        "evidence_binding": live_evidence_binding(root, gates),
                    }
                ),
                encoding="utf-8",
            )
            self.assertIsNotNone(validated_scope_certificate(state, "operator_leaf_closure"))
            self.assertTrue(
                current_certificate_validation_summary(state)["scopes"][0]["current_contract_valid"]
            )
            board_selector = {
                "operator_leaf_promotion_certificate": {
                    "required_artifact": "artifact.stage6.operator_leaf_promotion_certificate",
                    "required_gates": gates,
                    "blocks_until_present": ["board_gate"],
                    "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
                }
            }
            self.assertEqual(stage6_selector_blockers(state, ["board_gate"], board_selector), [])

            evidence_path = Path(
                json.loads(cert_path.read_text(encoding="utf-8"))["evidence_binding"]["file_bindings"][0]["path"]
            )
            evidence_path.write_text("changed source bytes", encoding="utf-8")
            self.assertIsNone(validated_scope_certificate(state, "operator_leaf_closure"))
            self.assertTrue(stage6_selector_blockers(state, ["board_gate"], board_selector))

    def test_compile_only_scope_reuses_single_layer_certificate(self) -> None:
        with TemporaryDirectory() as temp_dir, patch.dict(
            "os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}
        ):
            root = Path(temp_dir)
            certificate_path = root / "verification" / "certificates" / "single_layer.json"
            selector_path = root / "verification_artifacts" / "selector.json"
            gate = "case_single_layer_functional"
            certificate_path.parent.mkdir(parents=True)
            selector_path.parent.mkdir(parents=True)
            selector_path.write_text(
                json.dumps(
                    {
                        "single_layer_promotion_certificate": {
                            "required_gates": [
                                "case_tb_scaffold",
                                gate,
                                "case_single_layer_golden_compare",
                            ],
                            "evidence_contract": {
                                "legacy_full_simulation_contract": True
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            certificate_path.write_text(
                json.dumps(
                    {
                        "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                        "status": "pass",
                        "validation_policy": "vcs_compile_only",
                        "functional_semantics_claimed": False,
                        "evidence_contract": evidence_contract_for_level(
                            "single_layer_functional"
                        ),
                        "evidence_contract_fingerprint": certificate_contract_fingerprint(
                            "single_layer_functional", [gate]
                        ),
                        "tool_environment_contract": tool_environment_contract({}),
                        "required_gates": [{"name": gate, "status": "pass"}],
                        "evidence_binding": live_evidence_binding(root, [gate]),
                    }
                ),
                encoding="utf-8",
            )
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage6.single_layer_promotion_certificate",
                        "path": str(certificate_path),
                        "producer_transition": "transition.0001",
                        "trust_status": "validated",
                    },
                    {
                        "id": "artifact.stage5.stage6_gate_selector_contract",
                        "path": str(selector_path),
                    },
                ],
                "transitions": [{"id": "transition.0001", "status": "promoted"}],
            }
            adapter = {
                "evidence_gates": {"single_layer_functional": gate},
            }
            with patch(
                "accagent.framework.stage_debug_loop.case_adapter_for_state",
                return_value=adapter,
            ):
                self.assertIsNotNone(
                    validated_scope_certificate(state, "single_layer_closure")
                )

    def test_report_requires_successful_current_vcs_receipt(self) -> None:
        import hashlib

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            log = root / "compile.log"
            log.write_text("VCS compilation and elaboration complete\n", encoding="utf-8")
            report = {
                "status": "pass",
                "validation_policy": "vcs_compile_only",
                "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
                "compile_evidence": {
                    "status": "pass",
                    "compile": {"status": "pass", "returncode": 0},
                    "logs": [{"path": str(log), "sha256": hashlib.sha256(log.read_bytes()).hexdigest()}],
                },
            }
            path = root / "report.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(semantic_evidence_report_errors(path, "operator_leaf_functional"), [])
            report["compile_evidence"]["compile"]["returncode"] = 1
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertTrue(semantic_evidence_report_errors(path, "operator_leaf_functional"))
            report["compile_evidence"]["compile"]["returncode"] = 0
            log.write_text("Error-[SE] Syntax error\n", encoding="utf-8")
            report["compile_evidence"]["logs"][0]["sha256"] = hashlib.sha256(log.read_bytes()).hexdigest()
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertTrue(any("contains errors" in error for error in semantic_evidence_report_errors(path, "operator_leaf_functional")))

    def test_old_board_semantic_receipt_cannot_bypass_compilation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "board.json"
            path.write_text(json.dumps({
                "status": "pass",
                "evidence_contract": evidence_contract_for_level("axi_ddr_functional"),
                "semantic_provenance": {"comparison": {"passed": True}},
            }), encoding="utf-8")
            errors = semantic_evidence_report_errors(path, "axi_ddr_functional")
        self.assertTrue(any("compile/elaboration" in error for error in errors))

    def test_verification_does_not_require_retired_weight_or_golden_capabilities(self) -> None:
        spec = {"capabilities": [], "consumes": ["current RTL"], "produces": ["VCS compile report"]}
        for role in ("leaf_functional_sim", "leaf_golden_compare", "single_layer_functional_sim", "vcs_functional_sim"):
            with self.subTest(role=role):
                self.assertEqual(tool_evidence_contract_errors(role, spec), [])

    def test_compile_only_contract_uses_compile_reports_not_stale_capability_labels(self) -> None:
        with patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}):
            compiler_spec = {
                "capabilities": [],
                "consumes": ["real model weights", "random input"],
                "produces": ["operator semantic report"],
                "python_modules": ["torch"],
                "python_environment_group": "oracle",
            }
            self.assertEqual(tool_evidence_contract_errors("leaf_functional_sim", compiler_spec), [])

            golden_spec = {
                "capabilities": [],
                "consumes": ["real model weights input golden"],
                "produces": ["operator semantic golden report"],
                "python_modules": ["torch"],
                "python_environment_group": "oracle",
            }
            self.assertEqual(tool_evidence_contract_errors("leaf_golden_compare", golden_spec), [])

            evidence_spec = {
                "capabilities": [],
                "consumes": ["reference binding leaf output"],
                "produces": ["semantic operator report"],
            }
            self.assertEqual(
                tool_evidence_contract_errors("operator_leaf_semantic_evidence", evidence_spec),
                [],
            )

            compile_contract = evidence_contract_for_level("operator_leaf_functional")
            stale_selector_contract = {"level_id": "operator_leaf_functional"}
            certificate = {
                "validation_policy": "vcs_compile_only",
                "functional_semantics_claimed": False,
                "evidence_contract": compile_contract,
            }
            self.assertTrue(
                selector_contract_matches_certificate(
                    stale_selector_contract, certificate, "operator_leaf_functional"
                )
            )
            certificate["functional_semantics_claimed"] = True
            self.assertFalse(
                selector_contract_matches_certificate(
                    stale_selector_contract, certificate, "operator_leaf_functional"
                )
            )

    def test_compile_only_pass_skips_redundant_llm_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "sacg_state.json"
            source_state.write_text("{}", encoding="utf-8")
            run_dir = root / "run"
            run_dir.mkdir()
            results = {
                "status": "pass",
                "results": [{"checker": "real_tool.case_leaf_functional", "status": "pass"}],
                "gate_execution_scope": "operator_leaf_closure",
                "execution_scope": "operator_leaf_closure",
            }
            with (
                patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}),
                patch("accagent.framework.stage_verification.run_dir_from_state", return_value=run_dir),
                patch("accagent.framework.stage_verification.build_results", return_value=results),
                patch("accagent.framework.stage_verification.run_verification_review_team", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.run_stage_agent", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.update_sacg", return_value="transition"),
            ):
                report_path, report = run_verification(Namespace(sacg_state=source_state))

            self.assertTrue(report_path.is_file())
            self.assertEqual(report["status"], "ready")
            self.assertFalse(report["llm_review_routing"]["primary_agent_required"])
            self.assertTrue(report["llm_review_routing"]["compile_only_pass_skips_llm_review"])
            self.assertTrue(
                any(row["checker"] == "compile_only_policy_acceptance" for row in results["results"])
            )

    def test_compile_only_failure_skips_review_and_remains_repairable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_state = root / "sacg_state.json"
            source_state.write_text("{}", encoding="utf-8")
            run_dir = root / "run"
            run_dir.mkdir()
            results = {
                "status": "fail",
                "results": [{"checker": "real_tool.case_leaf_functional", "status": "fail", "summary": "VCS compile failed"}],
                "gate_execution_scope": "operator_leaf_closure",
                "execution_scope": "operator_leaf_closure",
            }
            with (
                patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}),
                patch("accagent.framework.stage_verification.run_dir_from_state", return_value=run_dir),
                patch("accagent.framework.stage_verification.build_results", return_value=results),
                patch("accagent.framework.stage_verification.run_verification_review_team", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.run_stage_agent", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.update_sacg", return_value="transition"),
            ):
                _, report = run_verification(Namespace(sacg_state=source_state))

            self.assertEqual(report["status"], "needs_repair")
            self.assertTrue(report["llm_review_routing"]["compile_only_skips_llm_review"])
            self.assertEqual(report["llm_agent"]["status"], "not_required")
            self.assertEqual(results["status"], "fail")

    def test_compile_only_build_results_uses_only_real_compile_gate_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "run"
            run_dir.mkdir()
            gate_plan = {
                "status": "pass",
                "selected_gates": ["operator_leaf_functional"],
                "steps": [{"gate": "operator_leaf_functional", "tools": [{"name": "case_leaf_functional", "required": True}]}],
                "reused_certified_gates": [],
            }
            tool_results = [{
                "checker": "real_tool.case_leaf_functional",
                "status": "pass",
                "required": True,
                "summary": "VCS compile/elaboration passed",
                "command": "vcs -full64",
                "log_path": str(run_dir / "verification" / "real_tools" / "case_leaf_functional.json"),
            }]
            with (
                patch.dict("os.environ", {"SPATIALACC_VERIFICATION_POLICY": "vcs_compile_only"}),
                patch("accagent.framework.stage_verification.build_stage6_gate_execution_plan", return_value=gate_plan),
                patch("accagent.framework.stage_verification.real_tool_evidence", return_value=tool_results),
                patch("accagent.framework.stage_verification.check_task_card", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.check_stage6_action_audit", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.check_scope_semantic_evidence", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.check_real_tool_log_consistency", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.check_python_environment_contract", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.check_case_functional_sim_preconditions", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.build_hierarchical_gate_summary", return_value={"required_gates": []}),
                patch("accagent.framework.stage_verification.build_hierarchical_maturity_report", return_value={"status": "pass", "backend_ready": False, "blockers": []}),
                patch("accagent.framework.stage_verification.build_board_bringup_readiness", side_effect=AssertionError),
                patch("accagent.framework.stage_verification.write_board_bringup_certificate", return_value=root / "board.json"),
                patch("accagent.framework.stage_verification.write_stage6_promotion_certificates", return_value=({}, [])),
                patch("accagent.framework.stage_verification.write_debug_closure_artifacts", return_value={}),
                patch("accagent.framework.stage_verification.build_repair_loop_report", return_value={"status": "pass", "current_layer": {"id": "operator_leaf_modules"}}),
                patch("accagent.framework.stage_verification.stage6_retry_reconciliation_contract", return_value={}),
            ):
                results = build_results({}, run_dir)

            self.assertEqual(results["status"], "pass")
            checkers = {row["checker"] for row in results["results"]}
            self.assertNotIn("verification_action_audit_check", checkers)
            self.assertNotIn("real_weight_semantic_evidence_check", checkers)
            self.assertIn("required_real_tool_evidence_check", checkers)
