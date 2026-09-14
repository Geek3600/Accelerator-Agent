import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.sacg_utils import hierarchical_learning_context
from accagent.framework.stage_llm import (
    compact_for_retry,
)
from accagent.framework.verification_evidence_contract import (
    PROMOTION_CERTIFICATE_SCHEMA_VERSION,
    PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
    certificate_contract_fingerprint,
    evidence_contract_for_level,
    promotion_evidence_binding_fingerprint,
    sha256_file,
    tool_environment_contract,
)


class HierarchicalLearningContextTest(TestCase):
    def write_json(self, path: Path, payload: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return path

    def state_with_live_single_layer_certificate(self, root: Path) -> tuple[dict, Path]:
        report = self.write_json(
            root / "single_layer_functional_report.json",
            {
                "schema_version": "example.single_layer_functional_report.v1",
                "status": "pass",
                "pipeline_overlap_evidence": {
                    "schema_version": "example.pipeline_overlap.v1",
                    "status": "pass",
                    "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
                    "accepted_trace_record_count": 12,
                    "trace_record_count": 12,
                    "planned_stage_count": 3,
                    "maximum_concurrent_stage_count": 3,
                    "all_planned_stages_concurrent_observed": True,
                    "all_planned_stages_participate_in_required_overlap": True,
                    "all_planned_stages_same_cycle_concurrency_required": False,
                    "required_dependency_overlap_complete": True,
                    "stage_turnover_gaps_are_diagnostic": True,
                    "boundary_order_evidence": [
                        {
                            "complete": True,
                            "token_first_transfer_order_preserved": True,
                            "token_last_transfer_order_preserved": True,
                        }
                    ],
                    "dependency_overlap_evidence": [
                        {
                            "relationship": "direct_dataflow",
                            "required_for_acceptance": True,
                            "different_token_overlap_observed": True,
                        }
                    ],
                    "trace_sha256": "a" * 64,
                    "contract_sha256": "b" * 64,
                },
            },
        )
        gate = "case_single_layer_functional"
        binding = {
            "schema_version": PROMOTION_EVIDENCE_BINDING_SCHEMA_VERSION,
            "required_gates": [gate],
            "file_bindings": [
                {
                    "gate": gate,
                    "path": str(report),
                    "sha256": sha256_file(report),
                    "role": "evidence_artifact",
                    "source_path": str(report),
                }
            ],
            "fingerprints": [],
            "excluded_same_scope_promotion_certificates": [],
        }
        binding["binding_sha256"] = promotion_evidence_binding_fingerprint(binding)
        certificate = self.write_json(
            root / "single_layer_promotion_certificate.json",
            {
                "schema_version": PROMOTION_CERTIFICATE_SCHEMA_VERSION,
                "status": "pass",
                "evidence_contract": evidence_contract_for_level("single_layer_functional"),
                "evidence_contract_fingerprint": certificate_contract_fingerprint(
                    "single_layer_functional", [gate]
                ),
                "tool_environment_contract": tool_environment_contract({}),
                "required_gates": [{"name": gate, "status": "pass"}],
                "evidence_binding": binding,
                "evidence_semantics": {
                    "claim": "connected single-layer functional evidence",
                    "does_not_claim": ["board acceptance"],
                },
            },
        )
        state = {
            "artifacts": [
                {
                    "id": "artifact.stage7.single_layer_promotion_certificate",
                    "path": str(certificate),
                    "trust_status": "validated",
                    "producer_transition": "transition.single_layer",
                }
            ],
            "transitions": [{"id": "transition.single_layer", "status": "promoted"}],
        }
        return state, report

    def test_projects_live_certified_timing_for_board_reasoning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            state, _ = self.state_with_live_single_layer_certificate(Path(temp_dir))

            context = hierarchical_learning_context(
                state, verification_scope="board_axi_ddr_closure"
            )

            self.assertEqual(context["status"], "pass")
            self.assertEqual(
                context["status_bar_contract"]["maintainer"],
                "framework_deterministic_hash_bound_projection",
            )
            self.assertTrue(
                context["status_bar_contract"]["does_not_replace_current_scope_tool_results"]
            )
            self.assertEqual(
                [row["scope"] for row in context["validated_lower_layer_certificates"]],
                ["single_layer_closure"],
            )
            timing = context["kernel_timing_knowledge"]
            self.assertEqual(len(timing), 1)
            self.assertEqual(
                timing[0]["pipeline_semantics"],
                "elastic_rate_insensitive_token_pipeline",
            )
            self.assertFalse(timing[0]["all_planned_stages_same_cycle_concurrency_required"])
            self.assertTrue(
                timing[0]["required_direct_dependency_overlap_summary"][
                    "all_different_token_overlap_observed"
                ]
            )
            self.assertTrue(
                context["decision_policy"][
                    "independent_prefetch_or_axi_progress_is_not_output_frontier_progress"
                ]
            )

    def test_rejects_drifted_timing_report_before_prompt_reuse(self) -> None:
        with TemporaryDirectory() as temp_dir:
            state, report = self.state_with_live_single_layer_certificate(Path(temp_dir))
            report.write_text("{}", encoding="utf-8")

            context = hierarchical_learning_context(
                state, verification_scope="board_axi_ddr_closure"
            )

            self.assertEqual(context["status"], "no_validated_lower_layer_evidence")
            self.assertEqual(context["kernel_timing_knowledge"], [])

    def test_compact_retry_retains_hierarchical_learning_context(self) -> None:
        compact = compact_for_retry(
            {
                "agent": "verification_agent",
                "stage": "verification",
                "candidate_verification_plan": {},
                "candidate_verification_artifact_contract": {},
                "candidate_verification_review_artifact": {},
                "design_team": {},
                "gate_execution_plan": {},
                "hierarchical_gate_summary": {},
                "source_sacg_state": "/persistent/state.json",
                "verification_capability_repair_package": {},
                "repair_step": {},
                "stage_gate_policy": {},
                "verification_result": {},
                "hierarchical_learning_context": {
                    "status": "pass",
                    "kernel_timing_knowledge": ["hash-bound timing summary"],
                },
            }
        )

        self.assertIn("hierarchical_learning_context", compact)
