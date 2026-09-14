import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    hierarchy_memory_context,
    sacg_memory_truth,
    scoped_sacg_memory_summary,
    scoped_sacg_memory_truth,
)
from accagent.framework.stage_llm import stage_agent_memory_scope
from accagent.framework.stage_team import compact_state_summary
from accagent.framework.stage_verification import (
    stage7_retry_source_fingerprint,
    stage7_agent_decision_blockers,
    stage7_retry_reconciliation_contract,
)


class SacgMemoryScopeTest(TestCase):
    def test_operational_memory_is_layer_scoped_without_hiding_global_truth(self) -> None:
        leaf = {
            "id": "leaf",
            "verification_scope": "operator_leaf_closure",
            "debug_layer": "operator_leaf_modules",
        }
        board = {
            "id": "board",
            "verification_scope": "board_axi_ddr_closure",
            "debug_layer": "board_axi_ddr_wrapped_system",
        }
        unscoped = {"id": "legacy"}
        state = {
            "memory": {
                "schema_version": "spatialaccagent.sacg_memory.v0",
                "stage_outcomes": [leaf, board, unscoped],
                "failure_lessons": [leaf, board, unscoped],
                "retry_requests": [
                    leaf | {"status": "open"},
                    board | {"status": "open"},
                    unscoped | {"status": "open"},
                    leaf | {"id": "closed", "status": "closed"},
                ],
                "backtrack_requests": [
                    leaf | {"status": "open"},
                    board | {"status": "open"},
                ],
                "contamination_barriers": [
                    leaf | {"status": "active"},
                    board | {"status": "active"},
                    unscoped,
                ],
            }
        }

        scoped = scoped_sacg_memory_summary(
            state,
            verification_scope="operator_leaf_closure",
            debug_layer="operator_leaf_modules",
        )
        truth = sacg_memory_truth(state)
        scoped_truth = scoped_sacg_memory_truth(
            state,
            verification_scope="operator_leaf_closure",
            debug_layer="operator_leaf_modules",
        )

        self.assertEqual([row["id"] for row in scoped["recent_stage_outcomes"]], ["leaf"])
        self.assertEqual([row["id"] for row in scoped["recent_failure_lessons"]], ["leaf"])
        self.assertEqual([row["id"] for row in scoped["open_retry_requests"]], ["leaf"])
        self.assertEqual([row["id"] for row in scoped["open_backtrack_requests"]], ["leaf"])
        self.assertEqual([row["id"] for row in scoped["active_contamination_barriers"]], ["leaf"])
        self.assertEqual(truth["open_retry_request_count"], 3)
        self.assertEqual(truth["active_contamination_barrier_count"], 3)
        self.assertEqual(scoped_truth["open_retry_request_count"], 1)
        self.assertEqual(scoped_truth["active_contamination_barrier_count"], 1)
        self.assertEqual(
            scoped_truth["global_persisted_blocker_counts"]["open_retry_requests"],
            3,
        )

    def test_hierarchy_context_canonicalizes_scope_and_failed_gates(self) -> None:
        context = hierarchy_memory_context(
            verification_scope="leaf",
            failed_gates=[
                {"name": "case_semantic_testbench", "status": "fail"},
                {"name": "higher_layer", "status": "not_run"},
                "case_semantic_testbench",
            ],
            source_fingerprint_sha256="A" * 64,
        )

        self.assertEqual(context["verification_scope"], "operator_leaf_closure")
        self.assertEqual(context["debug_layer"], "operator_leaf_modules")
        self.assertEqual(context["failed_gates"], ["case_semantic_testbench"])
        self.assertEqual(context["source_fingerprint_sha256"], "a" * 64)

    def test_repair_prompt_scope_is_derived_from_repair_step(self) -> None:
        scope = stage_agent_memory_scope(
            {
                "repair_step": {
                    "action": {"debug_layer": "single_transformer_layer_kernel"}
                }
            }
        )

        self.assertEqual(
            scope,
            {
                "verification_scope": "single_layer_closure",
                "debug_layer": "single_transformer_layer_kernel",
            },
        )

    def test_explicit_board_scope_is_available_to_specialized_agent_inputs(self) -> None:
        scope = stage_agent_memory_scope(
            {
                "verification_scope": "board_axi_ddr_closure",
                "debug_layer": "board_axi_ddr_wrapped_system",
            }
        )

        self.assertEqual(
            scope,
            {
                "verification_scope": "board_axi_ddr_closure",
                "debug_layer": "board_axi_ddr_wrapped_system",
            },
        )

    def test_verification_prompt_and_team_scope_are_derived_from_current_result(self) -> None:
        verification_result = {
            "execution_scope": "operator_leaf_closure",
            "hierarchical_repair_loop": {
                "current_layer": {"id": "operator_leaf_modules"}
            },
        }
        state = {
            "constraints": [],
            "artifacts": [],
            "invariants": [],
            "memory": {
                "failure_lessons": [
                    {
                        "id": "leaf",
                        "verification_scope": "operator_leaf_closure",
                        "debug_layer": "operator_leaf_modules",
                    },
                    {
                        "id": "board",
                        "verification_scope": "board_axi_ddr_closure",
                        "debug_layer": "board_axi_ddr_wrapped_system",
                    },
                ]
            },
        }

        prompt_scope = stage_agent_memory_scope(
            {"verification_result": verification_result}
        )
        team_summary = compact_state_summary(state, verification_result)

        self.assertEqual(prompt_scope["verification_scope"], "operator_leaf_closure")
        self.assertEqual(prompt_scope["debug_layer"], "operator_leaf_modules")
        self.assertEqual(
            [row["id"] for row in team_summary["sacg_memory"]["recent_failure_lessons"]],
            ["leaf"],
        )

    def test_repair_planner_prompt_scope_is_derived_from_candidate_plan(self) -> None:
        scope = stage_agent_memory_scope(
            {
                "candidate_repair_plan": {
                    "diagnostics": {
                        "hierarchical_repair_loop": {
                            "current_layer": {"id": "operator_leaf_modules"}
                        }
                    }
                }
            }
        )

        self.assertEqual(
            scope,
            {
                "verification_scope": "operator_leaf_closure",
                "debug_layer": "operator_leaf_modules",
            },
        )

    def test_rejected_transition_barrier_inherits_hierarchy_binding(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sacg.json"
            path.write_text(
                json.dumps(
                    {
                        "design_id": "test",
                        "sacg_version": "test",
                        "nodes": [],
                        "edges": [],
                        "constraints": [{"id": "constraint.test"}],
                        "artifacts": [],
                        "invariants": [],
                        "evidence": [],
                        "transitions": [],
                        "approvals": [],
                        "memory": {},
                    }
                ),
                encoding="utf-8",
            )
            store = SACGStore(path)
            context = hierarchy_memory_context(
                debug_layer="operator_leaf_modules",
                failed_gates=["case_semantic_testbench"],
            )
            transition = store.declare_transition(
                action_type="verification",
                touched_nodes=[],
                touched_edges=[],
                touched_constraints=["constraint.test"],
                context=context,
            )
            store.bind_artifact(
                "artifact.test",
                "/run/test.json",
                "test",
                [],
                [],
                ["constraint.test"],
                transition["id"],
            )
            store.reject(transition["id"], "current layer failed")

            barrier = store.state["memory"]["contamination_barriers"][-1]

        self.assertEqual(barrier["verification_scope"], "operator_leaf_closure")
        self.assertEqual(barrier["debug_layer"], "operator_leaf_modules")
        self.assertEqual(barrier["failed_gates"], ["case_semantic_testbench"])

    def test_retry_requests_are_idempotent_per_current_failure_identity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sacg.json"
            path.write_text(
                json.dumps(
                    {
                        "design_id": "test",
                        "sacg_version": "test",
                        "nodes": [],
                        "edges": [],
                        "constraints": [],
                        "artifacts": [],
                        "invariants": [],
                        "evidence": [],
                        "transitions": [],
                        "approvals": [],
                        "memory": {},
                    }
                ),
                encoding="utf-8",
            )
            store = SACGStore(path)
            context = hierarchy_memory_context(
                verification_scope="board_axi_ddr_closure",
                debug_layer="board_axi_ddr_wrapped_system",
                failed_gates=["case_multilayer_pipeline", "functional_sim"],
                source_fingerprint_sha256="a" * 64,
            )
            first = store.record_retry_request(
                stage="stage7.verification",
                reason="current board gate failed",
                target_stage="stage7.verification",
                required_inputs=["artifact.stage6.contract"],
                blocked_artifacts=["artifact.stage7.verification_result"],
                context=context,
            )
            repeated = store.record_retry_request(
                stage="stage7.verification",
                reason="current board gate failed",
                target_stage="stage7.verification",
                required_inputs=["artifact.stage6.contract"],
                blocked_artifacts=["artifact.stage7.verification_result"],
                context=context | {"source_fingerprint_sha256": "b" * 64},
            )

        self.assertEqual(first["id"], repeated["id"])
        retries = store.state["memory"]["retry_requests"]
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0]["observation_count"], 2)
        self.assertEqual(
            retries[0]["observed_source_fingerprint_sha256s"],
            ["a" * 64, "b" * 64],
        )

    def test_rejected_transition_deduplicates_active_barriers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sacg.json"
            path.write_text(
                json.dumps(
                    {
                        "design_id": "test",
                        "sacg_version": "test",
                        "nodes": [],
                        "edges": [],
                        "constraints": [{"id": "constraint.test"}],
                        "artifacts": [],
                        "invariants": [],
                        "evidence": [],
                        "transitions": [],
                        "approvals": [],
                        "memory": {},
                    }
                ),
                encoding="utf-8",
            )
            store = SACGStore(path)
            context = hierarchy_memory_context(
                verification_scope="board_axi_ddr_closure",
                debug_layer="board_axi_ddr_wrapped_system",
                failed_gates=["case_multilayer_pipeline", "functional_sim"],
            )
            for _ in range(2):
                transition = store.declare_transition(
                    action_type="verification",
                    touched_nodes=[],
                    touched_edges=[],
                    touched_constraints=["constraint.test"],
                    context=context,
                )
                store.bind_artifact(
                    "artifact.stage7.verification_result",
                    "/run/verification_result.json",
                    "test",
                    [],
                    [],
                    ["constraint.test"],
                    transition["id"],
                )
                store.reject(transition["id"], "same current failure")

        barriers = [
            row
            for row in store.state["memory"]["contamination_barriers"]
            if row.get("status") == "active"
        ]
        self.assertEqual(len(barriers), 1)
        self.assertEqual(barriers[0]["observation_count"], 2)
        self.assertEqual(len(barriers[0]["observed_transition_ids"]), 2)

    def test_legacy_active_duplicates_are_compacted_before_a_new_loop(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sacg.json"
            common = {
                "verification_scope": "board_axi_ddr_closure",
                "debug_layer": "board_axi_ddr_wrapped_system",
                "failed_gates": ["case_multilayer_pipeline", "functional_sim"],
            }
            path.write_text(
                json.dumps(
                    {
                        "design_id": "test",
                        "sacg_version": "test",
                        "nodes": [],
                        "edges": [],
                        "constraints": [],
                        "artifacts": [],
                        "invariants": [],
                        "evidence": [],
                        "transitions": [],
                        "approvals": [],
                        "memory": {
                            "retry_requests": [
                                {
                                    "id": "retry.1",
                                    "status": "open",
                                    "stage": "stage7.verification",
                                    "target_stage": "stage7.verification",
                                    "reason": "same failure",
                                    "required_inputs": ["artifact.stage6.contract"],
                                    "blocked_artifacts": ["artifact.stage7.result"],
                                    **common,
                                },
                                {
                                    "id": "retry.2",
                                    "status": "open",
                                    "stage": "stage7.verification",
                                    "target_stage": "stage7.verification",
                                    "reason": "same failure",
                                    "required_inputs": ["artifact.stage6.contract"],
                                    "blocked_artifacts": ["artifact.stage7.result"],
                                    **common,
                                },
                            ],
                            "contamination_barriers": [
                                {
                                    "id": "barrier.1",
                                    "status": "active",
                                    "artifact_id": "artifact.stage7.result",
                                    "reason": "same failure",
                                    **common,
                                },
                                {
                                    "id": "barrier.2",
                                    "status": "active",
                                    "artifact_id": "artifact.stage7.result",
                                    "reason": "same failure",
                                    **common,
                                },
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            store = SACGStore(path)
            report = store.deduplicate_active_memory_records()

        self.assertTrue(report["changed"])
        self.assertEqual(
            [row["id"] for row in store.state["memory"]["retry_requests"] if row["status"] == "open"],
            ["retry.1"],
        )
        self.assertEqual(
            [
                row["id"]
                for row in store.state["memory"]["contamination_barriers"]
                if row["status"] == "active"
            ],
            ["barrier.1"],
        )
        self.assertEqual(store.state["memory"]["retry_requests"][1]["deduplicated_into"], "retry.1")
        self.assertEqual(
            store.state["memory"]["contamination_barriers"][1]["deduplicated_into"],
            "barrier.1",
        )

    def test_stage7_retry_fingerprint_ignores_identity_audit_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            identity_path = (
                run_dir
                / "verification"
                / "board_interface"
                / "board_source_identity.json"
            )
            identity_path.parent.mkdir(parents=True)
            identity = {
                "selected_simulation_source_closure_sha256": "1" * 64,
                "compute_slot_abi_sha256": "2" * 64,
                "timing_contract_sha256": "3" * 64,
                "axi_interfaces_sha256": "4" * 64,
                "discovery_provenance": {"timestamp": "first"},
            }
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            for relative in (
                "input/model_config.json",
                "generated/memory/dut_weight_binding_manifest.json",
                "verification/semantic_testbench/semantic_testbench_manifest.json",
            ):
                path = run_dir / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{"status":"ready"}', encoding="utf-8")
            result = {
                "results": [
                    {"checker": "real_tool.case_multilayer_pipeline", "status": "fail"}
                ],
                "gate_execution_plan": {"selected_gates": ["case_multilayer_pipeline"]},
            }
            first = stage7_retry_source_fingerprint(
                result,
                run_dir,
                execution_scope="board_axi_ddr_closure",
                debug_layer="board_axi_ddr_wrapped_system",
            )
            identity["discovery_provenance"] = {"timestamp": "second"}
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            second = stage7_retry_source_fingerprint(
                result,
                run_dir,
                execution_scope="board_axi_ddr_closure",
                debug_layer="board_axi_ddr_wrapped_system",
            )
            identity["selected_simulation_source_closure_sha256"] = "5" * 64
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            changed = stage7_retry_source_fingerprint(
                result,
                run_dir,
                execution_scope="board_axi_ddr_closure",
                debug_layer="board_axi_ddr_wrapped_system",
            )

        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_reconciliation_contract_is_scope_bound_and_allows_llm_bounded_decision(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certificate = Path(temp_dir) / "operator_leaf.json"
            certificate.write_text('{"status":"pass"}', encoding="utf-8")
            result = {
                "execution_scope": "operator_leaf_closure",
                "hierarchical_repair_loop": {
                    "current_layer": {"id": "operator_leaf_modules"}
                },
                "results": [{"checker": "real_tool.case_leaf_functional", "status": "pass"}],
                "promotion_certificates": {
                    "artifact.stage7.operator_leaf_promotion_certificate": str(certificate)
                },
            }
            state = {
                "transitions": [
                    {"id": "transition.leaf", "status": "rejected"},
                    {"id": "transition.board", "status": "rejected"},
                ],
                "memory": {
                    "contamination_barriers": [
                        {
                            "id": "barrier.leaf",
                            "artifact_id": "artifact.stage7.verification_result",
                            "transition_id": "transition.leaf",
                            "status": "active",
                            "verification_scope": "operator_leaf_closure",
                            "debug_layer": "operator_leaf_modules",
                        },
                        {
                            "id": "barrier.board",
                            "artifact_id": "artifact.stage7.verification_result",
                            "transition_id": "transition.board",
                            "status": "active",
                            "verification_scope": "board_axi_ddr_closure",
                            "debug_layer": "board_axi_ddr_wrapped_system",
                        },
                        {
                            "id": "barrier.legacy",
                            "artifact_id": "artifact.stage7.verification_result",
                            "transition_id": "transition.leaf",
                            "status": "active",
                        },
                    ],
                    "retry_requests": [
                        {
                            "id": "retry.leaf",
                            "target_stage": "stage7.verification",
                            "status": "open",
                            "verification_scope": "operator_leaf_closure",
                            "debug_layer": "operator_leaf_modules",
                        },
                        {
                            "id": "retry.board",
                            "target_stage": "stage7.verification",
                            "status": "open",
                            "verification_scope": "board_axi_ddr_closure",
                            "debug_layer": "board_axi_ddr_wrapped_system",
                        },
                    ],
                },
            }

            contract = stage7_retry_reconciliation_contract(state, result)
            self.assertEqual(contract["status"], "ready")
            self.assertEqual(contract["eligible_contamination_barrier_ids"], ["barrier.leaf"])
            self.assertEqual(contract["eligible_retry_request_ids"], ["retry.leaf"])
            result["retry_reconciliation_contract"] = contract
            blockers = stage7_agent_decision_blockers(
                {
                    "output": {
                        "status": "blocked",
                        "summary": "bounded reconciliation is required before promotion",
                    }
                },
                results=result,
            )
            self.assertEqual(blockers, [])
            self.assertEqual(
                result["sacg_reconciliation"]["contract"]["eligible_retry_request_ids"],
                ["retry.leaf"],
            )

    def test_explicit_reconciliation_never_closes_cross_layer_records(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sacg.json"
            path.write_text(
                json.dumps(
                    {
                        "design_id": "test",
                        "sacg_version": "test",
                        "nodes": [],
                        "edges": [],
                        "constraints": [],
                        "artifacts": [],
                        "invariants": [],
                        "evidence": [],
                        "transitions": [],
                        "approvals": [],
                        "memory": {
                            "retry_requests": [
                                {"id": "retry.leaf", "status": "open", "target_stage": "stage7.verification"},
                                {"id": "retry.board", "status": "open", "target_stage": "stage7.verification"},
                            ],
                            "contamination_barriers": [
                                {"id": "barrier.leaf", "status": "active", "artifact_id": "artifact.stage7.verification_result"},
                                {"id": "barrier.board", "status": "active", "artifact_id": "artifact.stage7.verification_result"},
                            ],
                        },
                    }
                ),
                encoding="utf-8",
            )
            store = SACGStore(path)
            store.reconcile_retry_and_barriers(
                "transition.current",
                target_stage="stage7.verification",
                superseded_artifacts=["artifact.stage7.verification_result"],
                retry_request_ids=["retry.leaf"],
                contamination_barrier_ids=["barrier.leaf"],
                reason="scope-bound current certificate",
            )

            retries = {row["id"]: row["status"] for row in store.state["memory"]["retry_requests"]}
            barriers = {row["id"]: row["status"] for row in store.state["memory"]["contamination_barriers"]}

        self.assertEqual(retries, {"retry.leaf": "closed", "retry.board": "open"})
        self.assertEqual(barriers, {"barrier.leaf": "superseded", "barrier.board": "active"})
