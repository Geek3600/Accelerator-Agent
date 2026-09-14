import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.stage_debug_loop import validated_scope_certificate
from accagent.framework.stage_verification import (
    build_promotion_evidence_binding,
    stage7_selector_blockers,
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
                    "artifact.stage7.operator_leaf_promotion_certificate"
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
                        "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
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
                current_promotion_artifact_id="artifact.stage7.operator_leaf_promotion_certificate",
            )
            self.assertEqual(errors, [])
            self.assertFalse(
                any(row["path"] == str(previous_certificate) for row in same_scope["file_bindings"])
            )
            self.assertEqual(
                same_scope["excluded_same_scope_promotion_certificates"][0]["artifact_id"],
                "artifact.stage7.operator_leaf_promotion_certificate",
            )
            lower_scope, errors = build_promotion_evidence_binding(
                gate_summary,
                tool_results,
                [gate],
                root,
                selector,
                root / "lower_scope_snapshots",
                current_promotion_artifact_id="artifact.stage7.single_layer_promotion_certificate",
            )
            self.assertEqual(errors, [])
            self.assertTrue(
                any(row["path"] == str(previous_certificate) for row in lower_scope["file_bindings"])
            )
            same_scope_payload = {
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "evidence_binding": same_scope,
            }
            previous_certificate.write_text('{"artifact_id":"artifact.stage7.operator_leaf_promotion_certificate","status":"replacement"}', encoding="utf-8")
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
                        "id": "artifact.stage7.operator_leaf_promotion_certificate",
                        "path": str(cert_path),
                        "producer_transition": "transition.0001",
                        "trust_status": "validated",
                    },
                    {
                        "id": "artifact.stage6.stage7_gate_selector_contract",
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
                    "required_artifact": "artifact.stage7.operator_leaf_promotion_certificate",
                    "required_gates": gates,
                    "blocks_until_present": ["board_gate"],
                    "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
                }
            }
            self.assertEqual(stage7_selector_blockers(state, ["board_gate"], board_selector), [])

            evidence_path = Path(
                json.loads(cert_path.read_text(encoding="utf-8"))["evidence_binding"]["file_bindings"][0]["path"]
            )
            evidence_path.write_text("changed source bytes", encoding="utf-8")
            self.assertIsNone(validated_scope_certificate(state, "operator_leaf_closure"))
            self.assertTrue(stage7_selector_blockers(state, ["board_gate"], board_selector))

    def test_semantic_report_requires_real_weight_and_independent_output_provenance(self) -> None:
        report = {
            "status": "pass",
            "evidence_contract": evidence_contract_for_level("operator_leaf_functional"),
            "semantic_provenance": {
                "target_model": {
                    "model_id": "model",
                    "revision": "revision",
                    "accelerator_scope": "transformer_blocks_only",
                },
                "weights": {
                    "real_target_weights": True,
                    "scope_coverage_complete": True,
                    "consumed_by_dut": True,
                    "manifest_sha256": "a",
                    "consumed_tensor_hashes": ["b"],
                },
                "input": {
                    "source": "random",
                    "seed": 7,
                    "dtype": "fp16",
                    "shape": [1, 2, 8],
                    "sha256": "c",
                },
                "reference": {
                    "independent_of_rtl": True,
                    "uses_same_input_and_weights": True,
                    "engine": "target-model-reference",
                    "expected_output_source": "target_model_inference",
                    "oracle_kind": "high_precision_target_model",
                    "expected_output_sha256": "d",
                },
                "numeric_policy": {
                    "policy_sha256": "f",
                    "reference_bound": True,
                    "encoding_bound": True,
                    "comparison_policy": {
                        "atol": 0.01,
                        "rtol": 0.01,
                        "max_mismatch_fraction": 0.0,
                    },
                },
                "testbench": {
                    "manifest_sha256": "g",
                    "testbench_sha256": "h",
                    "loads_real_weights": True,
                },
                "comparison": {
                    "passed": True,
                    "rtl_output_sha256": "e",
                    "expected_output_sha256": "d",
                },
                "operator_coverage_complete": True,
            },
        }
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "semantic.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(semantic_evidence_report_errors(path, "operator_leaf_functional"), [])
            report["semantic_provenance"]["weights"]["consumed_by_dut"] = False
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertIn(
                "DUT consumption of the real weights is not proven",
                semantic_evidence_report_errors(path, "operator_leaf_functional"),
            )

    def test_board_semantic_report_accepts_complete_configured_prefix(self) -> None:
        report = {
            "status": "pass",
            "evidence_contract": evidence_contract_for_level("axi_ddr_functional"),
            "semantic_provenance": {
                "target_model": {
                    "model_id": "model",
                    "revision": "revision",
                    "accelerator_scope": "transformer_blocks_only",
                },
                "weights": {
                    "real_target_weights": True,
                    "scope_coverage_complete": True,
                    "consumed_by_dut": True,
                    "manifest_sha256": "a",
                    "consumed_tensor_hashes": ["b"],
                },
                "input": {"source": "random", "seed": 7, "dtype": "fp16", "shape": [1, 2, 8], "sha256": "c"},
                "reference": {
                    "independent_of_rtl": True,
                    "uses_same_input_and_weights": True,
                    "engine": "target-model-reference",
                    "expected_output_source": "target_model_inference",
                    "oracle_kind": "high_precision_target_model",
                    "expected_output_sha256": "d",
                },
                "numeric_policy": {
                    "policy_sha256": "f",
                    "reference_bound": True,
                    "encoding_bound": True,
                    "comparison_policy": {"atol": 0.01, "rtol": 0.01, "max_mismatch_fraction": 0.0},
                },
                "testbench": {"manifest_sha256": "g", "testbench_sha256": "h", "loads_real_weights": True},
                "comparison": {"passed": True, "rtl_output_sha256": "e", "expected_output_sha256": "d"},
                "validation_scope": {
                    "model_layer_count": 24,
                    "validation_layer_indices": [0],
                    "bound_layer_count": 1,
                    "all_target_layers": False,
                },
                "all_validation_layers": True,
                "all_target_layers": False,
                "board_wrapper": {
                    "exact_user_sample_wrapper": True,
                    "simulation_hashes_match_source": True,
                    "sample_project": "project",
                    "top_module": "board_top",
                    "source_hashes": ["i"],
                },
            },
        }
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "semantic.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(semantic_evidence_report_errors(path, "axi_ddr_functional"), [])
            report["semantic_provenance"]["validation_scope"]["bound_layer_count"] = 2
            path.write_text(json.dumps(report), encoding="utf-8")
            self.assertIn(
                "all configured board validation layers are not proven in the simulated execution",
                semantic_evidence_report_errors(path, "axi_ddr_functional"),
            )

    def test_tool_contract_rejects_default_weight_leaf_verifier(self) -> None:
        weak_spec = {
            "capabilities": ["operator_leaf_golden_compare", "independent_golden_compare"],
            "consumes": ["generated/chisel", "golden_boundary_values.json"],
            "produces": ["leaf_golden_compare.json"],
        }
        errors = tool_evidence_contract_errors("leaf_golden_compare", weak_spec)
        self.assertTrue(any("missing real-weight semantic capabilities" in error for error in errors))
        self.assertTrue(any("declared inputs" in error for error in errors))
