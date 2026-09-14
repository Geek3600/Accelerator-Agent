import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.board_backtrack_evidence import (
    BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION,
    board_to_lower_layer_contradiction_from_diagnosis,
    board_to_lower_layer_contradiction_from_runner,
)
from accagent.framework.stage_repair import (
    diagnosis_applicability_report,
    diagnosis_target_layer,
    exact_board_diagnosis_repair_kind,
)


class BoardBacktrackEvidenceTest(TestCase):
    target_layer = "single_transformer_layer_kernel"
    input_fingerprint = "a" * 64
    trace_sha = "b" * 64

    def proof(self, certificate_sha: str) -> dict:
        return {
            "schema_version": BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION,
            "status": "proven",
            "target_debug_layer": self.target_layer,
            "source_binding": {
                "input_fingerprint_sha256": self.input_fingerprint,
                "board_trace_sha256": self.trace_sha,
                "lower_layer_certificate_sha256": certificate_sha,
            },
            "direct_kernel_boundary_observations": {
                "kernel_start_accepted": True,
                "kernel_ingress_complete": True,
                "kernel_egress_ready": True,
            },
            "causal_localization": {
                "earliest_causal_owner": self.target_layer,
                "named_contract_boundary_id": "contract.edge.core_output",
            },
        }

    def diagnosis(self, proof: dict | None) -> dict:
        return {
            "status": "needs_repair",
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "applicability_binding": {
                "origin_layer": "board_axi_ddr_wrapped_system",
                "input_fingerprint_sha256": self.input_fingerprint,
            },
            "failure_evidence": {
                "board_to_lower_layer_contradiction_evidence": proof,
            },
            "repair_handoff": {
                "agent_should_apply_code_changes": True,
                "debug_layer": self.target_layer,
                "repair_scope": self.target_layer,
            },
        }

    def test_requires_current_certificate_and_direct_core_observations(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certificate = Path(temp_dir) / "single_layer_certificate.json"
            certificate.write_text("certificate-v1", encoding="utf-8")
            certificate_sha = hashlib.sha256(certificate.read_bytes()).hexdigest()
            proof = self.proof(certificate_sha)
            diagnosis = self.diagnosis(proof)

            accepted = board_to_lower_layer_contradiction_from_diagnosis(
                diagnosis,
                target_debug_layer=self.target_layer,
                expected_lower_layer_certificate_path=certificate,
            )
            certificate.write_text("certificate-v2", encoding="utf-8")
            rejected = board_to_lower_layer_contradiction_from_diagnosis(
                diagnosis,
                target_debug_layer=self.target_layer,
                expected_lower_layer_certificate_path=certificate,
            )

        self.assertEqual(accepted["status"], "proven")
        self.assertEqual(rejected["status"], "insufficient_evidence")
        self.assertIn(
            "current lower-layer certificate",
            " ".join(rejected["validation_errors"]),
        )

    def test_diagnosis_accepts_validated_proof_envelope(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certificate = Path(temp_dir) / "single_layer_certificate.json"
            certificate.write_text("certificate-v1", encoding="utf-8")
            proof = self.proof(hashlib.sha256(certificate.read_bytes()).hexdigest())
            diagnosis = self.diagnosis(
                {
                    "schema_version": (
                        BOARD_TO_LOWER_LAYER_CONTRADICTION_SCHEMA_VERSION
                    ),
                    "status": "proven",
                    "target_debug_layer": self.target_layer,
                    "evidence": proof,
                }
            )
            result = board_to_lower_layer_contradiction_from_diagnosis(
                diagnosis,
                target_debug_layer=self.target_layer,
                expected_lower_layer_certificate_path=certificate,
            )

        self.assertEqual(result["status"], "proven")
        self.assertEqual(
            result["evidence"]["source_binding"]["lower_layer_certificate_sha256"],
            proof["source_binding"]["lower_layer_certificate_sha256"],
        )

    def test_output_symptom_alone_cannot_route_back_to_lower_layer(self) -> None:
        runner = {
            "input_fingerprint_sha256": self.input_fingerprint,
            "progress_event_summary": {
                "intra_layer_pipeline_violation_evidence": {
                    "status": "proven_pipeline_violation"
                }
            },
        }
        evidence = board_to_lower_layer_contradiction_from_runner(
            runner, target_debug_layer=self.target_layer
        )
        diagnosis = self.diagnosis(None)

        self.assertEqual(evidence["status"], "insufficient_evidence")
        self.assertEqual(
            exact_board_diagnosis_repair_kind(diagnosis),
            "exact_board_integration_harness",
        )

    def test_proven_direct_contradiction_routes_back_to_single_layer(self) -> None:
        proof = self.proof("c" * 64)
        diagnosis = self.diagnosis(proof)

        self.assertEqual(
            exact_board_diagnosis_repair_kind(diagnosis),
            "single_layer_spatial_pipeline_backtrack",
        )

    def test_current_proof_overrides_stale_board_handoff(self) -> None:
        proof = self.proof("c" * 64)
        diagnosis = self.diagnosis(proof)
        diagnosis["repair_handoff"] = {
            "agent_should_apply_code_changes": True,
            "debug_layer": "board_axi_ddr_wrapped_system",
            "repair_scope": "board_axi_ddr_wrapped_system",
        }

        self.assertEqual(
            exact_board_diagnosis_repair_kind(diagnosis),
            "single_layer_spatial_pipeline_backtrack",
        )
        self.assertEqual(
            diagnosis_target_layer(diagnosis),
            self.target_layer,
        )

    def test_current_proof_overrides_stale_board_binding_in_applicability(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            certificate = (
                root
                / "verification"
                / "certificates"
                / "single_layer_promotion_certificate.json"
            )
            certificate.parent.mkdir(parents=True)
            certificate.write_text("certificate-v1", encoding="utf-8")
            runner = root / "board_runner.json"
            runner.write_text("{}", encoding="utf-8")
            diagnosis = self.diagnosis(self.proof(hashlib.sha256(certificate.read_bytes()).hexdigest()))
            diagnosis["applicability_binding"] = {
                "schema_version": "spatialaccagent.diagnosis_applicability_binding.v1",
                "origin_layer": "board_axi_ddr_wrapped_system",
                "target_layer": "board_axi_ddr_wrapped_system",
                "diagnosed_failure_class": diagnosis["failure_class"],
                "origin_gates": ["case_vcs_functional_sim"],
                "applicable_rerun_gates": ["case_vcs_functional_sim"],
                "input_fingerprint_sha256": self.input_fingerprint,
                "source_artifacts": [
                    {
                        "role": "board_vcs_runner_report",
                        "path": str(runner),
                        "sha256": hashlib.sha256(runner.read_bytes()).hexdigest(),
                    }
                ],
            }
            applicability = diagnosis_applicability_report(
                diagnosis,
                {
                    "current_layer": {"id": "board_axi_ddr_wrapped_system"},
                    "failed_current_layer_gates": [
                        {"name": "case_vcs_functional_sim", "status": "fail"}
                    ],
                },
                run_dir=root,
            )

        self.assertTrue(applicability["executable"])
        self.assertEqual(applicability["target_layer"], self.target_layer)
        self.assertEqual(applicability["relation"], "current_targeted_backtrack")

    def test_current_runner_evidence_builds_hash_bound_contradiction(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            trace = root / "boundary_trace.jsonl"
            trace.write_text('{"boundary_id":"kernel.core_ingress"}\n', encoding="utf-8")
            certificate = root / "single_layer_certificate.json"
            certificate.write_text("certificate-v1", encoding="utf-8")
            executed_manifest = root / "executed_manifest.json"
            certificate_sha = hashlib.sha256(certificate.read_bytes()).hexdigest()
            executed_manifest.write_text(
                json.dumps(
                    {
                        "multilayer_harness": {
                            "single_layer_promotion_certificate": {
                                "path": str(certificate),
                                "sha256": certificate_sha,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            runner = {
                "input_fingerprint_sha256": self.input_fingerprint,
                "executed_manifest": str(executed_manifest),
                "pipeline_boundary_observation_summary": {
                    "trace_path": str(trace),
                    "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
                    "status": "incomplete",
                    "record_count": 1,
                    "required_boundary_count": 2,
                    "observed_boundary_count": 1,
                },
                "progress_event_summary": {
                    "latest_stall_snapshot": {
                        "connected_kernel_inner_cone_observation": {
                            "all_outer_ingress_accepted": True,
                            "outer_input_accepted_count": 8,
                            "mlp_down_input_accepted_count": 4,
                            "mlp_down_output_accepted_count": 0,
                            "mlp_down_output_ready": 1,
                        },
                        "connected_kernel_internal_pipeline_observation": {
                            "start_edge_count": 1,
                            "core_ingress_accepted_count": 8,
                            "core_egress_accepted_count": 0,
                            "core_egress_ready": 1,
                        },
                    }
                },
            }
            runner_path = root / "runner.json"
            runner_path.write_text(json.dumps(runner), encoding="utf-8")
            diagnosis = {
                "applicability_binding": {
                    "input_fingerprint_sha256": self.input_fingerprint,
                    "source_artifacts": [
                        {
                            "role": "board_vcs_runner_report",
                            "path": str(runner_path),
                            "sha256": hashlib.sha256(runner_path.read_bytes()).hexdigest(),
                        }
                    ],
                },
                "failure_evidence": {},
                "repair_handoff": {},
            }

            from_runner = board_to_lower_layer_contradiction_from_runner(
                runner,
                target_debug_layer=self.target_layer,
            )
            from_diagnosis = board_to_lower_layer_contradiction_from_diagnosis(
                diagnosis,
                target_debug_layer=self.target_layer,
                expected_lower_layer_certificate_path=certificate,
            )
            trace.write_text('{"boundary_id":"changed"}\n', encoding="utf-8")
            stale_trace = board_to_lower_layer_contradiction_from_runner(
                runner,
                target_debug_layer=self.target_layer,
            )

        self.assertEqual(from_runner["status"], "proven")
        self.assertEqual(from_diagnosis["status"], "proven")
        self.assertEqual(
            from_runner["evidence"]["causal_localization"][
                "named_contract_boundary_id"
            ],
            "kernel.mlp_down.output",
        )
        self.assertEqual(stale_trace["status"], "insufficient_evidence")
