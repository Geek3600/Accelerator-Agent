import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from accagent.framework.stage_verification import (
    check_case_functional_sim_preconditions,
    build_stage7_gate_execution_plan,
    gate_tool_roles,
    reusable_exact_board_identity_evidence,
    reusable_stage7_certificate_evidence,
    reusable_dependency_tool_role_evidence,
    reusable_provider_gate_for_role,
    stage7_selector_blockers,
    stage7_selected_gate_names,
)
from accagent.framework.stage_verification_plan import (
    build_hierarchical_verification_plan,
    build_verification_gate_dag,
    stage6_gate_tool_roles,
    stage_worker_errors,
    write_stage6_refinement_artifacts,
)


class ThirdLayerProducerOrderTest(TestCase):
    def test_validated_exact_board_identity_reuses_only_discovery_gate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
            identity_path.parent.mkdir(parents=True)
            identity_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            adapter = {"evidence_gates": {"board_interface_discovery": "custom_board_discovery"}}
            nodes = [
                {"name": "custom_board_discovery", "phase": "board_interface_discovery"},
                {"name": "functional_sim", "phase": "functional_simulation"},
            ]
            selector = {"gates": nodes}
            contract = {"verification_gate_dag": {"nodes": nodes}}
            tool_protocols = run_dir / "tool_protocols.json"
            tool_protocols.write_text(json.dumps({"tools": []}), encoding="utf-8")

            def selected_closure(_state, roots, satisfied_gates=None):
                return set(roots)

            with patch(
                "accagent.framework.board_acceptance_contract.validate_exact_board_identity",
                return_value={"status": "pass", "schema_version": "identity.v1"},
            ), patch(
                "accagent.framework.stage_verification.stage6_verification_contract",
                return_value=contract,
            ), patch(
                "accagent.framework.stage_verification.stage7_selector_contract",
                return_value=selector,
            ), patch(
                "accagent.framework.stage_verification.case_adapter_for_state",
                return_value=adapter,
            ), patch(
                "accagent.framework.stage_verification.write_debug_closure_artifacts",
                return_value={},
            ), patch(
                "accagent.framework.stage_verification.artifact_path",
                return_value=tool_protocols,
            ), patch(
                "accagent.framework.stage_verification.stage7_selected_gate_names",
                return_value=["custom_board_discovery", "functional_sim"],
            ), patch(
                "accagent.framework.stage_verification.reusable_stage7_certificate_evidence",
                return_value={"gates": [], "certificates": [], "rejected_certificates": []},
            ), patch(
                "accagent.framework.stage_verification.lower_layer_certificate_scaffold_bridge",
                return_value={"status": "not_applicable"},
            ), patch(
                "accagent.framework.stage_verification.selected_gate_dependency_closure",
                side_effect=selected_closure,
            ), patch(
                "accagent.framework.stage_verification.gate_tool_roles",
                return_value=[],
            ), patch(
                "accagent.framework.stage_verification.stage7_selector_blockers",
                return_value=[],
            ):
                plan = build_stage7_gate_execution_plan({}, run_dir)

        self.assertEqual(plan["selected_gates"], ["functional_sim"])
        self.assertEqual(plan["reused_certified_gates"][0]["name"], "custom_board_discovery")
        self.assertEqual(
            plan["reused_certified_gates"][0]["evidence_source"],
            "validated_exact_board_identity",
        )

    def test_missing_or_invalid_exact_board_identity_is_not_reused(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            self.assertIsNone(reusable_exact_board_identity_evidence(run_dir, {}))

            identity_path = run_dir / "verification" / "board_interface" / "board_source_identity.json"
            identity_path.parent.mkdir(parents=True)
            identity_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            with patch(
                "accagent.framework.board_acceptance_contract.validate_exact_board_identity",
                return_value={"status": "fail"},
            ):
                self.assertIsNone(reusable_exact_board_identity_evidence(run_dir, {}))

    def test_scope_entry_certificate_prevents_shared_manifest_drift_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            certificate_path = Path(temp_dir) / "leaf_certificate.json"
            certificate_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            state = {
                "artifacts": [
                    {
                        "id": "artifact.stage7.operator_leaf_promotion_certificate",
                        "path": str(certificate_path),
                        "trust_status": "validated",
                    }
                ]
            }
            selector = {
                "operator_leaf_promotion_certificate": {
                    "required_artifact": "artifact.stage7.operator_leaf_promotion_certificate",
                    "required_gates": ["case_leaf_functional"],
                    "blocks_until_present": ["case_board_interface_discovery"],
                    "evidence_contract": {"version": "current"},
                }
            }
            nodes = [
                {"name": "case_leaf_functional", "phase": "operator_leaf_functional"},
                {"name": "case_board_interface_discovery", "phase": "board_interface_discovery"},
            ]
            with patch.dict(
                "os.environ",
                {"SPATIALACC_DEBUG_LOOP_REUSED_SCOPES": "operator_leaf_closure"},
            ), patch(
                "accagent.framework.stage_verification.certificate_contract_errors",
                return_value=["shared manifest hash drift"],
            ), patch(
                "accagent.framework.stage_verification.stage6_gate_dependency_map",
                return_value={},
            ):
                evidence = reusable_stage7_certificate_evidence(
                    state,
                    selector,
                    ["case_board_interface_discovery"],
                    nodes,
                )
                blockers = stage7_selector_blockers(
                    state,
                    ["case_board_interface_discovery"],
                    selector,
                )

        self.assertEqual(evidence["rejected_certificates"], [])
        self.assertIn("case_leaf_functional", evidence["gate_names"])
        self.assertEqual(blockers, [])

    def test_current_scope_semantic_contract_files_are_checked_after_production(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            manifest = run_dir / "semantic_testbench_manifest.json"
            requirements = run_dir / "dut_weight_binding_requirements.json"
            manifest.write_text(
                json.dumps({"target_model_inference": True, "dut_weight_binding": True}),
                encoding="utf-8",
            )
            requirements.write_text(json.dumps({"numeric_policy_sha256": "abc"}), encoding="utf-8")
            adapter = {
                "status": "ready",
                "case_id": "generic_case",
                "preconditions": {
                    "testbench_artifact_loading": {
                        "files": [str(manifest), str(requirements)],
                        "required_tokens": [
                            "target_model_inference",
                            "dut_weight_binding",
                            "numeric_policy_sha256",
                        ],
                    }
                },
            }
            plan = {
                "selected_gates": ["case_semantic_testbench"],
                "steps": [
                    {
                        "gate": "case_semantic_testbench",
                        "phase": "semantic_testbench_generation",
                        "tools": [
                            {
                                "name": "case_semantic_testbench",
                                "produces": [str(manifest), str(requirements)],
                            }
                        ],
                    }
                ],
            }
            with patch(
                "accagent.framework.stage_verification.case_adapter_for_state",
                return_value=adapter,
            ), patch(
                "accagent.framework.stage_verification.stage6_gate_dependency_map",
                return_value={},
            ):
                status, summary = check_case_functional_sim_preconditions({}, run_dir, plan)

        self.assertEqual(status, "pass", summary)

    def test_real_model_semantic_preparation_precedes_leaf_verification(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dag = build_verification_gate_dag({}, Path(temp_dir))

        phases = [node["phase"] for node in dag["nodes"]]
        self.assertLess(phases.index("real_weight_catalog"), phases.index("target_model_reference"))
        self.assertLess(phases.index("target_model_reference"), phases.index("semantic_testbench_generation"))
        self.assertLess(phases.index("semantic_testbench_generation"), phases.index("operator_leaf_functional"))
        self.assertTrue(dag["policy"]["real_model_inference_golden_required"])
        self.assertTrue(dag["policy"]["complete_transformer_block_weight_scope_required"])
        self.assertTrue(dag["policy"]["transformer_blocks_are_the_only_accelerator_scope"])
        self.assertTrue(dag["policy"]["explicit_numeric_comparison_policy_required"])
        self.assertTrue(dag["policy"]["rtl_derived_or_random_expected_output_forbidden"])

    def test_leaf_gates_do_not_repeat_the_global_testbench_producer(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            pipeline_dir = run_dir / "pipeline_planning"
            pipeline_dir.mkdir(parents=True)
            (pipeline_dir / "pipeline_plan.json").write_text(
                json.dumps({"stages": [{"stage_id": "stage_generic", "op": "generic_op", "kind": "compute"}]}),
                encoding="utf-8",
            )
            dag = build_verification_gate_dag({}, run_dir)

        leaf_nodes = [node for node in dag["nodes"] if node["name"].startswith("leaf_stage.")]
        self.assertGreater(len(leaf_nodes), 0)
        self.assertTrue(all(node["tool_roles"] == ["stage_leaf_static"] for node in leaf_nodes))
        self.assertEqual(stage6_gate_tool_roles({}, "case_stage_leaf_static"), ["stage_leaf_static"])
        self.assertEqual(gate_tool_roles({}, "leaf_stage.stage_generic"), ["stage_leaf_static"])
        self.assertEqual(gate_tool_roles({}, "case_stage_leaf_static"), ["stage_leaf_static"])

    def test_only_non_board_consumers_can_reuse_certified_semantic_producer(self) -> None:
        adapter: dict = {}
        self.assertEqual(
            reusable_provider_gate_for_role(adapter, "case_tb_scaffold", "tb_scaffold_generate"),
            "case_semantic_testbench",
        )
        self.assertEqual(
            reusable_provider_gate_for_role(adapter, "single_transformer_layer", "tb_scaffold_generate"),
            "case_semantic_testbench",
        )
        self.assertEqual(
            reusable_provider_gate_for_role(
                adapter,
                "case_single_layer_golden_compare",
                "single_layer_golden_reference_builder",
            ),
            "case_target_model_reference",
        )
        self.assertEqual(gate_tool_roles(adapter, "case_multilayer_pipeline"), ["multilayer_pipeline"])
        self.assertIsNone(
            reusable_provider_gate_for_role(adapter, "case_axi_ddr_interface", "tb_scaffold_generate")
        )

    def test_duplicate_producer_reuse_requires_certified_provider_in_dependency_closure(self) -> None:
        evidence = {
            "case_semantic_testbench": {
                "name": "case_semantic_testbench",
                "evidence_source": "promotion_certificate",
                "certificate_artifact": "artifact.stage7.operator_leaf_promotion_certificate",
                "certificate_path": "/tmp/operator_leaf_promotion_certificate.json",
            }
        }
        reused = reusable_dependency_tool_role_evidence(
            {},
            "case_tb_scaffold",
            "tb_scaffold_generate",
            {"case_tb_scaffold", "case_semantic_testbench"},
            evidence,
        )
        self.assertIsNotNone(reused)
        self.assertEqual(reused["provider_gate"], "case_semantic_testbench")
        self.assertEqual(
            reused["certificate_artifact"],
            "artifact.stage7.operator_leaf_promotion_certificate",
        )
        self.assertIsNone(
            reusable_dependency_tool_role_evidence(
                {},
                "case_tb_scaffold",
                "tb_scaffold_generate",
                {"case_tb_scaffold"},
                evidence,
            )
        )
        self.assertIsNone(
            reusable_dependency_tool_role_evidence(
                {},
                "case_tb_scaffold",
                "tb_scaffold_generate",
                {"case_tb_scaffold", "case_semantic_testbench"},
                {},
            )
        )

    def test_real_simulation_precedes_all_derived_checkers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dag = build_verification_gate_dag({}, Path(temp_dir))

        nodes = dag["nodes"]
        index = {node["phase"]: position for position, node in enumerate(nodes)}
        expected_order = [
            "board_interface_discovery",
            "multilayer_pipeline",
            "board_wrapper_interface",
            "functional_simulation",
            "multilayer_functional",
            "multilayer_deadlock_liveness",
            "axi_protocol_check",
            "ddr_image_roundtrip",
            "board_semantic_aggregate",
        ]

        self.assertEqual(dag["policy"]["layer3_board_axi_ddr_wrapper_closure"], expected_order)
        self.assertEqual(
            [phase for phase in dag["policy"]["hierarchical_order"] if phase in expected_order],
            expected_order,
        )
        self.assertTrue(all(index["functional_simulation"] < index[phase] for phase in expected_order[4:]))

    def test_hierarchy_and_tool_roles_match_the_real_producer_order(self) -> None:
        hierarchy = build_hierarchical_verification_plan({"stages": []}, {})
        gate_order = [gate["name"] for gate in hierarchy["evidence_gates"]]
        expected_gates = [
            "case_board_interface_discovery",
            "case_multilayer_pipeline",
            "case_axi_ddr_interface",
            "functional_sim",
            "case_multilayer_functional",
            "case_pipeline_deadlock_check",
            "case_axi_protocol_check",
            "case_ddr_image_roundtrip",
            "case_board_semantic_evidence",
        ]

        self.assertEqual([gate for gate in gate_order if gate in expected_gates], expected_gates)
        self.assertEqual(
            stage6_gate_tool_roles({}, "case_axi_ddr_interface"),
            ["axi_ddr_interface"],
        )

    def test_board_scope_selects_complete_third_layer_and_stops_before_vivado(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dag = build_verification_gate_dag({}, Path(temp_dir))

        contract = {"verification_gate_dag": dag}
        selector = {"gates": dag["nodes"]}
        with patch.dict("os.environ", {"SPATIALACC_STAGE7_GATE_SCOPE": "board_axi_ddr_closure"}):
            selected = stage7_selected_gate_names(contract, selector)

        self.assertEqual(selected[-1], "case_board_semantic_evidence")
        self.assertIn("functional_sim", selected)
        self.assertIn("case_multilayer_functional", selected)
        self.assertIn("case_pipeline_deadlock_check", selected)
        self.assertIn("case_axi_protocol_check", selected)
        self.assertNotIn("case_vivado_synthesis", selected)

    def test_lower_layer_scopes_end_at_semantic_aggregate_gates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dag = build_verification_gate_dag({}, Path(temp_dir))

        contract = {"verification_gate_dag": dag}
        selector = {"gates": dag["nodes"]}
        with patch.dict("os.environ", {"SPATIALACC_STAGE7_GATE_SCOPE": "operator_leaf_closure"}):
            operator_selected = stage7_selected_gate_names(contract, selector)
        with patch.dict("os.environ", {"SPATIALACC_STAGE7_GATE_SCOPE": "single_layer_closure"}):
            single_selected = stage7_selected_gate_names(contract, selector)

        self.assertEqual(operator_selected[-1], "case_operator_leaf_semantic_evidence")
        self.assertEqual(single_selected[-1], "case_single_layer_semantic_evidence")

    def test_semantic_and_report_tools_are_mandatory_and_backend_has_no_bypass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dag = build_verification_gate_dag({}, Path(temp_dir))

        nodes = {node["name"]: node for node in dag["nodes"]}
        self.assertEqual(nodes["case_operator_leaf_semantic_evidence"]["tool_roles"], ["operator_leaf_semantic_evidence"])
        self.assertEqual(nodes["case_single_layer_semantic_evidence"]["tool_roles"], ["single_layer_semantic_evidence"])
        self.assertEqual(nodes["case_board_semantic_evidence"]["tool_roles"], ["board_semantic_evidence"])
        self.assertEqual(
            nodes["functional_sim"]["tool_roles"],
            ["vcs_functional_sim", "vcs_evidence_analyzer", "deadlock_axi_check"],
        )
        self.assertIn("vivado_synthesis_report_check", nodes["case_vivado_synthesis"]["tool_roles"])
        self.assertIn("vivado_implementation_report_check", nodes["case_vivado_implementation"]["tool_roles"])
        self.assertTrue(
            {
                "case_multilayer_pipeline",
                "case_board_interface_discovery",
                "case_axi_ddr_interface",
                "functional_sim",
                "case_multilayer_functional",
                "case_pipeline_deadlock_check",
                "case_axi_protocol_check",
                "case_ddr_image_roundtrip",
                "case_board_semantic_evidence",
            }.issubset(set(nodes["case_vivado_synthesis"]["depends_on"]))
        )

    def test_specific_stage6_refinement_actions_require_real_materialization(self) -> None:
        actions = [
            {"id": "stage6.semantic", "stage": "verification_artifacts", "action_type": "cross_layer_semantic_gate_refinement"},
            {"id": "stage6.board", "stage": "verification_artifacts", "action_type": "board_functional_gate_dag_refinement"},
            {"id": "stage6.backend", "stage": "verification_artifacts", "action_type": "downstream_tool_gate_hardening"},
            {"id": "stage6.repair", "stage": "verification_artifacts", "action_type": "repair_boundary_contract_review"},
            {"id": "stage6.selector", "stage": "verification_artifacts", "action_type": "stage7_gate_selector_contract_refinement"},
            {"id": "stage6.promote", "stage": "verification_artifacts", "action_type": "verification_contract_promotion"},
        ]
        planner_output = {
            "status": "refinement_required_before_stage7_third_layer",
            "risks": ["Current Stage6 contract risk is covered by the materialized refinement artifacts."],
            "executable_actions": actions,
        }
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "verification_artifacts"
            dag = build_verification_gate_dag({}, Path(temp_dir))
            contract = {
                "verification_gate_dag": dag,
                "functional_sim_candidates": [
                    {"name": "case_vcs_liveness", "kind": "vcs_liveness_not_acceptance"},
                    {"name": "case_vcs_functional_sim", "kind": "vcs_real_functional_sim"},
                ],
                "debug_closure_contract": {},
            }
            materialization = write_stage6_refinement_artifacts(
                out_dir,
                {},
                {},
                contract,
                planner_output,
                {"status": "ready"},
                {},
            )
            self.assertEqual(materialization["status"], "ready")
            errors = stage_worker_errors(planner_output, {}, materialization)
            self.assertEqual(errors, [], Path(materialization["manifest"]).read_text(encoding="utf-8"))

    def test_current_planner_refinement_types_mutate_and_validate_canonical_dag(self) -> None:
        planner_output = {
            "status": "refinement_required_before_stage7_consumption",
            "risks": [
                "A policy-only requirement needs explicit certificate inputs.",
                "The single-layer alias needs an explicit one-to-one binding.",
                "Exact board source identity must flow through backend and runtime.",
            ],
            "executable_actions": [
                {
                    "id": "stage6.materialize_semantic_lineage_and_stage7_selector",
                    "stage": "verification_artifacts",
                    "action_type": "verification_gate_dag_refinement",
                },
                {
                    "id": "stage6.materialize_exact_board_backend_runtime_lineage",
                    "stage": "verification_artifacts",
                    "action_type": "board_and_backend_gate_dag_refinement",
                },
                {
                    "id": "stage6.validate_and_promote_refined_contract",
                    "stage": "verification_artifacts",
                    "action_type": "stage_contract_validation",
                },
            ],
        }
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "verification_artifacts"
            dag = build_verification_gate_dag({}, Path(temp_dir))
            contract = {
                "verification_gate_dag": dag,
                "functional_sim_candidates": [
                    {"name": "case_vcs_functional_sim", "kind": "vcs_real_functional_sim"}
                ],
                "debug_closure_contract": {},
            }
            materialization = write_stage6_refinement_artifacts(
                out_dir,
                {},
                {},
                contract,
                planner_output,
                {"status": "ready"},
                {},
            )

            nodes = {node["name"]: node for node in contract["verification_gate_dag"]["nodes"]}
            runtime_identity = {
                "case_real_weight_artifacts",
                "case_target_model_reference",
                "case_semantic_testbench",
                "case_board_interface_discovery",
                "case_axi_ddr_interface",
                "case_board_semantic_evidence",
            }
            self.assertTrue(
                {"case_real_weight_artifacts", "case_target_model_reference", "case_semantic_testbench"}.issubset(
                    set(nodes["case_single_layer_golden_compare"]["depends_on"])
                )
            )
            self.assertTrue(runtime_identity.issubset(set(nodes["case_runtime_bitstream"]["depends_on"])))
            self.assertTrue(runtime_identity.issubset(set(nodes["board_runtime"]["depends_on"])))
            self.assertEqual(materialization["status"], "ready")
            self.assertEqual(stage_worker_errors(planner_output, {}, materialization), [])
            coverage = json.loads(
                Path(materialization["artifacts"]["stage6_action_materialization_coverage"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(coverage["status"], "ready")
            self.assertTrue(all(row["status"] == "pass" for row in coverage["actions"]))

    def test_unknown_stage6_refinement_action_cannot_be_claimed_materialized(self) -> None:
        planner_output = {
            "status": "refinement_required_before_stage7",
            "risks": [],
            "executable_actions": [
                {"id": "stage6.unknown", "stage": "verification_artifacts", "action_type": "unknown_contract_change"}
            ],
        }
        with TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir) / "verification_artifacts"
            dag = build_verification_gate_dag({}, Path(temp_dir))
            materialization = write_stage6_refinement_artifacts(
                out_dir,
                {},
                {},
                {
                    "verification_gate_dag": dag,
                    "functional_sim_candidates": [
                        {"name": "case_vcs_functional_sim", "kind": "vcs_real_functional_sim"}
                    ],
                    "debug_closure_contract": {},
                },
                planner_output,
                {"status": "ready"},
                {},
            )

        self.assertEqual(materialization["status"], "incomplete")
        self.assertTrue(stage_worker_errors(planner_output, {}, materialization))
