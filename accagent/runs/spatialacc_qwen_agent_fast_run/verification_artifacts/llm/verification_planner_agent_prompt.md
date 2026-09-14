<agent>
verification_planner_agent
</agent>

<task>
Review and refine the checker/tool gate DAG for real hierarchical verification; if later stages would lack coverage, propose bounded Stage6 contract updates before Stage7 runs real tools.
</task>

<rules>
1. Review only the supplied artifact summary and named constraints.
2. If inputs include subtask.role_assignment, act as that chip-design-team specialist: stay inside its mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope boundaries.
3. For sub-agent work, make observations, risks, approval_required_for, and executable_actions usable by peer agents through the declared handoff_to and acceptance_checkers; do not silently assume another specialist's responsibility.
4. Treat sacg_memory as the shared long-context design memory: preserve design goals, failure lessons, retry requests, backtrack requests, and contamination barriers.
5. Treat sacg_memory_truth as the authoritative current blocker set: only active_contamination_barriers and open retry/backtrack requests listed there are current SACG-memory blockers.
6. Do not infer active blockers from historical, closed, superseded, rejected, or recently summarized records when sacg_memory_truth shows the corresponding active/open count is zero.
7. If sacg_memory contains open backtrack_requests or contamination_barriers relevant to this stage, address them explicitly in observations and executable_actions.
8. If inputs include a retry_reconciliation_contract for the current stage, distinguish previous failed artifacts from the candidate retry artifacts: same-stage retry requests/barriers are downstream-consumption blockers until promotion, but they are not independent blockers for approving a refined current-stage contract that explicitly supersedes them after all current-stage checks pass.
9. If inputs include stage_gate_policy, use it to classify current-stage blocking risks versus later-stage actions.
10. If inputs include role_slice_policy or presence_summary, do not infer a field is missing merely because detailed rows were omitted from a compact/role-specific prompt slice.
11. When presence_summary says an artifact class exists, report missing-detail concerns as handoff/action items unless the visible checker status proves a current-stage blocker.
12. Report cross-layer consistency risks across model, shape, numeric policy, data order, memory, runtime, implementation, and board facts.
13. Keep actions bounded and executable by later tools/checkers.
14. Populate executable_actions with concrete next tool/repair actions; each action must name consumed artifacts, produced artifacts, tool roles, acceptance checkers, failure handling, and approval need.
15. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
16. For backend/app-shell target discovery, treat the LLM as the adaptive board-integration engineer: convert supplied board materials and real Vivado evidence into target_discovery_policy updates with cited artifacts; if evidence is ambiguous, require bounded approval instead of guessing names.
17. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name> and state the implementation gap in rationale.
18. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
19. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
20. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
21. Before any functional pass, require a complete target-checkpoint tensor catalog, deterministic or real input provenance, target-model inference expected outputs for the same input/checkpoint, a resolved numeric comparison tolerance (current-run values first, otherwise frozen framework loose defaults), generated semantic testbench hashes, and proof that the DUT consumed every required bound weight.
22. Applying the recorded framework loose defaults for initially missing atol, rtol, or max_mismatch_fraction is authorized and is not a repair-time tolerance change. Never derive or loosen those values from DUT output.
23. A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.
24. During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.
25. At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.
26. Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.
27. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
28. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
</rules>

<candidate_verification_plan>
{
  "checker_plan": [
    {
      "checker": "task_card_check",
      "constraints": [
        "constraint.task.goal"
      ]
    },
    {
      "checker": "model_config_check",
      "constraints": [
        "constraint.model.decoder",
        "constraint.shape.model"
      ]
    },
    {
      "checker": "numeric_policy_check",
      "constraints": [
        "constraint.numeric.policy"
      ]
    },
    {
      "checker": "template_coverage_check",
      "constraints": [
        "constraint.template.library",
        "constraint.codegen.package"
      ]
    },
    {
      "checker": "stream_plan_check",
      "constraints": [
        "constraint.stream.order",
        "constraint.beat.pipeline"
      ]
    },
    {
      "checker": "parameter_binding_static_check",
      "constraints": [
        "constraint.parameter.binding"
      ]
    },
    {
      "checker": "code_generation_manifest_static_check",
      "constraints": [
        "constraint.codegen.package"
      ]
    },
    {
      "checker": "codegen_package_static_check",
      "constraints": [
        "constraint.codegen.package"
      ]
    },
    {
      "checker": "verification_plan_static_check",
      "constraints": [
        "constraint.verification.plan"
      ]
    },
    {
      "checker": "tool_protocol_check",
      "constraints": [
        "constraint.tool.protocols"
      ]
    },
    {
      "checker": "human_boundary_check",
      "constraints": [
        "constraint.human.boundary"
      ]
    },
    {
      "checker": "memory_runtime_plan_check",
      "constraints": [
        "constraint.memory.board",
        "constraint.runtime.board"
      ]
    },
    {
      "checker": "hierarchical_verification_plan_check",
      "constraints": [
        "constraint.verification.hierarchy",
        "constraint.pipeline.structure"
      ]
    },
    {
      "checker": "verification_artifact_contract_check",
      "constraints": [
        "constraint.verification.artifacts"
      ]
    },
    {
      "checker": "required_real_tool_evidence_check",
      "constraints": [
        "constraint.verification.hierarchy",
        "constraint.tool.protocols",
        "constraint.deployment.board"
      ]
    },
    {
      "checker": "sacg_reference_check",
      "constraints": [
        "constraint.pipeline.structure"
      ]
    },
    {
      "checker": "data_order_trace_check",
      "constraints": [
        "constraint.stream.order",
        "constraint.beat.pipeline"
      ]
    },
    {
      "checker": "deadlock_watchdog",
      "constraints": [
        "constraint.verification.hierarchy",
        "constraint.tool.protocols"
      ]
    },
    {
      "checker": "implementation_package_static",
      "constraints": [
        "constraint.backend.package",
        "constraint.deployment.board"
      ]
    },
    {
      "checker": "board_runtime",
      "constraints": [
        "constraint.deployment.board",
        "constraint.human.boundary"
      ]
    }
  ],
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 19,
    "pending": [
      {
        "checker": "deadlock_watchdog",
        "execution_status": "not_run_required_downstream",
        "summary": "deadlock watchdog is required through the downstream functional_sim gate and must emit tool evidence"
      },
      {
        "checker": "implementation_package_static",
        "execution_status": "not_run_required_downstream",
        "summary": "implementation package evidence is required through the case_runtime_bitstream downstream gate"
      },
      {
        "checker": "board_runtime",
        "execution_status": "not_run_required_downstream",
        "summary": "board runtime evidence is required for final closure and is not claimed by Stage 6"
      }
    ],
    "pending_downstream": 3,
    "warnings": []
  },
  "constraints_referenced": [
    "constraint.beat.pipeline",
    "constraint.codegen.package",
    "constraint.deployment.board",
    "constraint.human.boundary",
    "constraint.memory.board",
    "constraint.model.decoder",
    "constraint.numeric.policy",
    "constraint.parameter.binding",
    "constraint.pipeline.structure",
    "constraint.runtime.board",
    "constraint.shape.model",
    "constraint.stream.order",
    "constraint.task.goal",
    "constraint.template.library",
    "constraint.tool.protocols",
    "constraint.verification.artifacts",
    "constraint.verification.hierarchy",
    "constraint.verification.plan"
  ],
  "constraints_touched": [
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.verification.artifacts"
  ],
  "hierarchical_verification": {
    "evidence_gate_names": [
      "case_real_weight_artifacts",
      "case_target_model_reference",
      "case_semantic_testbench",
      "case_stage_leaf_static",
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_tb_scaffold",
      "single_transformer_layer",
      "case_single_layer_functional",
      "case_single_layer_golden_compare",
      "case_single_layer_semantic_evidence",
      "case_board_interface_discovery",
      "case_multilayer_pipeline",
      "case_axi_ddr_interface",
      "functional_sim",
      "case_multilayer_functional",
      "case_pipeline_deadlock_check",
      "case_axi_protocol_check",
      "case_ddr_image_roundtrip",
      "case_board_semantic_evidence",
      "case_vivado_synthesis",
      "case_vivado_implementation",
      "case_runtime_abi_check",
      "case_runtime_bitstream",
      "board_runtime"
    ],
    "maturity_levels": [
      {
        "id": "operator_leaf_functional",
        "required_before": "single_transformer_layer_kernel",
        "required_gates": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
        ],
        "required_tool_roles": [
          "weight_manifest_generate",
          "target_model_reference_generate",
          "semantic_testbench_generate",
          "stage_leaf_static",
          "boundary_contract_check",
          "leaf_functional_sim",
          "leaf_golden_compare",
          "operator_leaf_semantic_evidence"
        ]
      },
      {
        "id": "single_layer_functional",
        "required_before": "board_axi_ddr_wrapped_system",
        "required_gates": [
          "case_tb_scaffold",
          "single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_single_layer_semantic_evidence"
        ],
        "required_tool_roles": [
          "single_layer_kernel",
          "single_layer_functional_sim",
          "single_layer_golden_compare",
          "single_layer_semantic_evidence"
        ]
      },
      {
        "id": "multilayer_pipeline_functional",
        "required_before": "board_axi_ddr_wrapped_system_promotion",
        "required_gates": [
          "case_multilayer_pipeline",
          "functional_sim",
          "case_multilayer_functional",
          "case_pipeline_deadlock_check"
        ],
        "required_tool_roles": [
          "multilayer_pipeline",
          "vcs_functional_sim",
          "vcs_evidence_analyzer",
          "multilayer_functional_sim",
          "pipeline_deadlock_check"
        ]
      },
      {
        "id": "axi_ddr_functional",
        "required_before": "backend_board",
        "required_gates": [
          "case_board_interface_discovery",
          "case_axi_ddr_interface",
          "functional_sim",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_board_semantic_evidence"
        ],
        "required_tool_roles": [
          "board_interface_discovery",
          "axi_ddr_interface",
          "vcs_functional_sim",
          "vcs_evidence_analyzer",
          "deadlock_axi_check",
          "axi_protocol_check",
          "ddr_image_roundtrip",
          "board_semantic_evidence"
        ]
      },
      {
        "id": "contract_guided_debug_closure",
        "required_before": "repair_or_backend_handoff",
        "required_gates": [
          "boundary_contract_check"
        ],
        "required_tool_roles": [
          "boundary_contract_check",
          "failure_slice_localization",
          "boundary_trace_rerun",
          "targeted_replay"
        ]
      }
    ],
    "merge_agent_count": 6,
    "policy": {
      "board_axi_ddr_functional_before_backend": true,
      "contract_guided_debug_closure_required_for_repair": true,
      "debug_layers": [
        "operator_leaf_modules",
        "single_transformer_layer_kernel",
        "board_axi_ddr_wrapped_system"
      ],
      "do_not_claim_final_pass_with_pending_or_failed_required_gate": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
      "do_not_use_default_generated_weights_as_real_weight_evidence": true,
      "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "merge_order": "operator_leaf_modules_then_single_transformer_layer_kernel_then_board_axi_ddr_wrapped_system_then_backend",
      "operator_leaf_functional_before_single_layer": true,
      "single_layer_functional_before_board_axi_ddr_wrapper": true,
      "stage_agents_parallel": true,
      "strict_bottom_up_functional_closure_before_backend": true
    },
    "stage_agent_count": 9,
    "strategy": "three_layer_repair_loop: operator_leaf_modules -> single_transformer_layer_kernel -> board_axi_ddr_wrapped_system"
  },
  "schema_version": "spatialaccagent.verification_plan.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {},
  "status": "ready"
}
</candidate_verification_plan>

<candidate_verification_artifact_contract>
{
  "backtrack_contract": {
    "policy": {
      "do_not_broadly_reopen_all_lower_layers": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "targeted_lower_layer_backtrack_requires_contradicting_current_layer_trace": true,
      "unbound_lower_layer_contradiction_requires_debug_trace_rerun": true
    },
    "required_action": "Record a SACG backtrack_request with the missing contract/tool/evidence facts or the explicit contradicted lower-layer gate/module. Rerun only the challenged lower-layer scope when...<len=344>",
    "target_stage": "stage6.verification_artifacts",
    "trigger_conditions": {
      "_size": 6,
      "_type": "list"
    }
  },
  "case_adapter": {
    "case_id": "qwen2_hf_case",
    "model_family": "qwen2",
    "source": "built_in_case_adapter",
    "status": "ready"
  },
  "debug_closure_contract": {
    "boundary_count": 13,
    "causal_path_count": 1,
    "contract_type": "boundary_contract_failure_slice_targeted_replay",
    "instrumentation_modes": [
      "failing_transaction_first",
      "target_boundary_replay",
      "full_boundary_trace_when_requested"
    ],
    "instrumentation_monitor_points": [
      "module_boundary_valid_ready",
      "transaction_and_tile_identity",
      "logical_index_and_lane_mapping",
      "declared_latency_window",
      "numeric_policy_and_tolerance",
      "runtime_memory_address_range"
    ],
    "policy": {
      "do_not_patch_downstream_symptom_without_upstream_localization": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "not_a_general_rtl_debugger": true,
      "production_goal_not_toy_trace": true,
      "repair_agent_receives_compact_causal_slice": true,
      "tool_trace_schema_must_be_case_adapter_independent": true,
      "uses_agent_generated_dataflow_knowledge": true
    },
    "repair_handoff_required_fields": [
      "root_candidate_module",
      "violated_contract",
      "failure_signature",
      "causal_path",
      "targeted_replay_plan",
      "minimal_repair_context"
    ],
    "schema_version": "spatialaccagent.debug_boundary_contracts.v0",
    "targeted_replay_strategy": "boundary_bisection_then_earliest_violation",
    "trace_paths": {
      "localization": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/failure_localization.json",
      "manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/trace_manifest.json",
      "trace": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json"
    },
    "trace_required_fields": [
      "cycle",
      "boundary_id",
      "tx_id",
      "tile_id",
      "logical_index",
      "observed_value",
      "expected_value",
      "contract",
      "status"
    ]
  },
  "errors": [],
  "evidence_path_requirements_summary": {
    "count": 36,
    "gate_names": [
      "case_real_weight_artifacts",
      "case_target_model_reference",
      "case_semantic_testbench",
      "boundary_contract_check",
      "leaf_stage.stage_00_rms_norm_1",
      "leaf_stage.stage_01_self_attention",
      "leaf_stage.stage_02_residual_add_1",
      "leaf_stage.stage_03_rms_norm_2",
      "leaf_stage.stage_04_mlp_gate_proj",
      "leaf_stage.stage_05_mlp_up_proj",
      "leaf_stage.stage_06_activation_mul",
      "leaf_stage.stage_07_mlp_down_proj",
      "leaf_stage.stage_08_residual_add_2",
      "case_stage_leaf_static",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_tb_scaffold",
      "single_transformer_layer",
      "case_single_layer_functional",
      "case_single_layer_golden_compare",
      "case_single_layer_semantic_evidence",
      "case_board_interface_discovery",
      "case_multilayer_pipeline",
      "case_axi_ddr_interface",
      "functional_sim",
      "case_multilayer_functional",
      "case_pipeline_deadlock_check",
      "case_axi_protocol_check",
      "case_ddr_image_roundtrip",
      "case_board_semantic_evidence",
      "case_vivado_synthesis",
      "case_vivado_implementation",
      "case_runtime_bitstream",
      "case_runtime_abi_check",
      "board_runtime"
    ],
    "phases": [
      "axi_protocol_check",
      "board_interface_discovery",
      "board_runtime",
      "board_semantic_aggregate",
      "board_wrapper_interface",
      "ddr_image_roundtrip",
      "debug_boundary_contract",
      "functional_simulation",
      "multilayer_deadlock_liveness",
      "multilayer_functional",
      "multilayer_pipeline",
      "operator_leaf_aggregate",
      "operator_leaf_functional",
      "operator_leaf_golden_compare",
      "operator_leaf_module",
      "operator_leaf_semantic_aggregate",
      "real_weight_catalog",
      "runtime_abi",
      "semantic_testbench_generation",
      "single_layer_functional",
      "single_layer_golden_compare",
      "single_layer_kernel",
      "single_layer_semantic_aggregate",
      "target_model_reference",
      "testbench_scaffold",
      "vivado_bitstream",
      "vivado_implementation",
      "vivado_synthesis"
    ]
  },
  "existing_stage6_refinements": {
    "artifacts": {},
    "schema_version": "spatialaccagent.stage6_existing_refinements.v0",
    "status": "missing"
  },
  "functional_sim_candidates": [
    {
      "acceptance_role": "required_real_functional_sim_gate_not_smoke_acceptance",
      "kind": "vcs_liveness_not_acceptance",
      "name": "case_vcs_liveness",
      "scope": "remote"
    },
    {
      "acceptance_role": "required_real_functional_sim_gate_not_smoke_acceptance",
      "kind": "vcs_real_functional_sim",
      "name": "case_vcs_functional_sim",
      "scope": "remote"
    }
  ],
  "gate_protocol_coverage": {
    "board_runtime_bound": true,
    "configured_tool_protocol_names": {
      "_size": 34,
      "_type": "list"
    },
    "functional_sim_bound": true,
    "functional_sim_candidates": {
      "_size": 2,
      "_type": "list"
    },
    "leaf_aggregate_covers_all_leaf_stages": true,
    "leaf_aggregate_dependencies": {
      "_size": 9,
      "_type": "list"
    },
    "leaf_aggregate_dependency_count": 9,
    "leaf_aggregate_gate": "case_stage_leaf_static",
    "leaf_stage_count": 9,
    "leaf_stage_names": {
      "_size": 9,
      "_type": "list"
    },
    "required_gate_count": 27,
    "required_gate_names": {
      "_size": 27,
      "_type": "list"
    },
    "schema_version": "spatialaccagent.stage6_gate_protocol_coverage.v0"
  },
  "policy": {
    "board_runtime_required_for_final_pass": true,
    "complete_transformer_block_weight_consumption_required": true,
    "contract_guided_debug_closure_required": true,
    "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
    "downstream_failure_requires_failure_slice": true,
    "explicit_numeric_comparison_policy_required": true,
    "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
    "later_stage_missing_gate_or_tool_requires_stage6_backtrack": true,
    "lower_layer_pass_evidence_is_reusable_not_absolute": true,
    "random_or_rtl_derived_expected_output_forbidden": true,
    "real_axi_ddr_runtime_required": true,
    "real_functional_sim_required": true,
    "real_target_model_reference_required": true,
    "real_weight_artifacts_required": true,
    "same_stage_retry_can_supersede_prior_stage6_barriers_after_promotion": true,
    "smoke_is_not_acceptance": true,
    "transformer_blocks_are_the_only_accelerator_scope": true
  },
  "required_evidence_gate_names": [
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_operator_leaf_semantic_evidence",
    "case_tb_scaffold",
    "single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "case_single_layer_semantic_evidence",
    "case_board_interface_discovery",
    "case_multilayer_pipeline",
    "case_axi_ddr_interface",
    "functional_sim",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_board_semantic_evidence",
    "case_vivado_synthesis",
    "case_vivado_implementation",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "board_runtime"
  ],
  "required_tool_protocols": [
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_weight_manifest_generate",
      "name": "case_weight_manifest_generate",
      "role": "weight_manifest_generate",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "target_model_reference_generate",
      "name": "case_target_model_reference",
      "role": "target_model_reference_generate",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "semantic_testbench_generate",
      "name": "case_semantic_testbench",
      "role": "semantic_testbench_generate",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_tb_scaffold_generate",
      "name": "case_tb_scaffold_generate",
      "role": "tb_scaffold_generate",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_tb_scaffold",
      "name": "case_tb_scaffold",
      "role": "tb_scaffold",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_stage_leaf_static",
      "name": "case_stage_leaf_static",
      "role": "stage_leaf_static",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "boundary_contract_check",
      "name": "boundary_contract_check",
      "role": "boundary_contract_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_leaf_functional",
      "name": "case_leaf_functional",
      "role": "leaf_functional_sim",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_leaf_golden_compare",
      "name": "case_leaf_golden_compare",
      "role": "leaf_golden_compare",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "semantic_evidence_assemble",
      "name": "case_operator_leaf_semantic_evidence",
      "role": "operator_leaf_semantic_evidence",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_real_weight_artifacts",
      "name": "case_real_weight_artifacts",
      "role": "real_weight_artifacts",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_single_transformer_layer",
      "name": "case_single_transformer_layer",
      "role": "single_layer_kernel",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_single_layer_functional",
      "name": "case_single_layer_functional",
      "role": "single_layer_functional_sim",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_single_layer_golden_reference_builder",
      "name": "case_single_layer_golden_reference_builder",
      "role": "single_layer_golden_reference_builder",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_single_layer_golden_compare",
      "name": "case_single_layer_golden_compare",
      "role": "single_layer_golden_compare",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "semantic_evidence_assemble",
      "name": "case_single_layer_semantic_evidence",
      "role": "single_layer_semantic_evidence",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_multilayer_pipeline",
      "name": "case_multilayer_pipeline",
      "role": "multilayer_pipeline",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_multilayer_functional",
      "name": "case_multilayer_functional",
      "role": "multilayer_functional_sim",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_pipeline_deadlock_check",
      "name": "case_pipeline_deadlock_check",
      "role": "pipeline_deadlock_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_board_interface_discovery",
      "name": "case_board_interface_discovery",
      "role": "board_interface_discovery",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_axi_ddr_interface",
      "name": "case_axi_ddr_interface",
      "role": "axi_ddr_interface",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_axi_protocol_check",
      "name": "case_axi_protocol_check",
      "role": "axi_protocol_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_ddr_image_roundtrip",
      "name": "case_ddr_image_roundtrip",
      "role": "ddr_image_roundtrip",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "vcs_real_functional_sim",
      "name": "case_vcs_functional_sim",
      "role": "vcs_functional_sim",
      "scope": "remote"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "vcs_evidence_analyzer",
      "name": "case_vcs_evidence_analyzer",
      "role": "vcs_evidence_analyzer",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_deadlock_axi_check",
      "name": "case_deadlock_axi_check",
      "role": "deadlock_axi_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "semantic_evidence_assemble",
      "name": "case_board_semantic_evidence",
      "role": "board_semantic_evidence",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "vivado_synthesis",
      "name": "case_vivado_synthesis",
      "role": "vivado_synthesis",
      "scope": "remote"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "vivado_report_check",
      "name": "case_vivado_synthesis_report_check",
      "role": "vivado_synthesis_report_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "vivado_implementation",
      "name": "case_vivado_implementation",
      "role": "vivado_implementation",
      "scope": "remote"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "vivado_report_check",
      "name": "case_vivado_implementation_report_check",
      "role": "vivado_implementation_report_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_runtime_abi_check",
      "name": "case_runtime_abi_check",
      "role": "runtime_abi_check",
      "scope": "local"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "case_runtime_bitstream",
      "name": "case_runtime_bitstream",
      "role": "runtime_bitstream",
      "scope": "remote"
    },
    {
      "configured": true,
      "evidence_status": "required_pending_execution",
      "kind": "board_runtime",
      "name": "board_runtime",
      "role": "board_runtime",
      "scope": "board"
    }
  ],
  "retry_reconciliation_contract": {
    "promotion_preconditions": {
      "_size": 6,
      "_type": "list"
    },
    "same_stage_retry_policy": "Open retry requests and active contamination barriers produced by prior rejected Stage6 transitions are expected inputs to a Stage6 retry. They are blockers for downstream Stage7 c...<len=484>",
    "schema_version": "spatialaccagent.stage_retry_reconciliation.v0",
    "source_active_contamination_barriers": {
      "_size": 0,
      "_type": "list"
    },
    "source_open_retry_requests": {
      "_size": 0,
      "_type": "list"
    },
    "stage": "stage6.verification_artifacts"
  },
  "schema_version": "spatialaccagent.verification_artifact_contract.v0",
  "stage6_refinement_materialization": {},
  "status": "pass",
  "summary": "all verification artifact contracts are satisfiable",
  "verification_gate_dag": {
    "critical_nodes": [
      {
        "depends_on": [],
        "evidence_status": "required_pending_execution",
        "name": "case_real_weight_artifacts",
        "phase": "real_weight_catalog",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "weight_manifest_generate",
          "real_weight_artifacts"
        ]
      },
      {
        "depends_on": [
          "case_real_weight_artifacts"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_target_model_reference",
        "phase": "target_model_reference",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "target_model_reference_generate"
        ]
      },
      {
        "depends_on": [
          "case_target_model_reference"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_semantic_testbench",
        "phase": "semantic_testbench_generation",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "semantic_testbench_generate"
        ]
      },
      {
        "depends_on": [],
        "evidence_status": "required_pending_execution",
        "name": "boundary_contract_check",
        "phase": "debug_boundary_contract",
        "required_maturity": "contract_guided_debug_closure",
        "tool_roles": [
          "boundary_contract_check"
        ]
      },
      {
        "depends_on": [
          "leaf_stage.stage_00_rms_norm_1",
          "leaf_stage.stage_01_self_attention",
          "leaf_stage.stage_02_residual_add_1",
          "leaf_stage.stage_03_rms_norm_2",
          "leaf_stage.stage_04_mlp_gate_proj",
          "leaf_stage.stage_05_mlp_up_proj",
          "leaf_stage.stage_06_activation_mul",
          "leaf_stage.stage_07_mlp_down_proj",
          "leaf_stage.stage_08_residual_add_2"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_stage_leaf_static",
        "phase": "operator_leaf_aggregate",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "stage_leaf_static"
        ]
      },
      {
        "depends_on": [
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_leaf_functional",
        "phase": "operator_leaf_functional",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "leaf_functional_sim"
        ]
      },
      {
        "depends_on": [
          "case_leaf_functional",
          "boundary_contract_check",
          "case_target_model_reference",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_leaf_golden_compare",
        "phase": "operator_leaf_golden_compare",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "leaf_golden_compare"
        ]
      },
      {
        "depends_on": [
          "case_leaf_golden_compare",
          "case_leaf_functional",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_target_model_reference",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_operator_leaf_semantic_evidence",
        "phase": "operator_leaf_semantic_aggregate",
        "required_maturity": "operator_leaf_functional",
        "tool_roles": [
          "operator_leaf_semantic_evidence"
        ]
      },
      {
        "depends_on": [
          "case_operator_leaf_semantic_evidence",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_tb_scaffold",
        "phase": "testbench_scaffold",
        "required_maturity": null,
        "tool_roles": [
          "tb_scaffold_generate",
          "tb_scaffold"
        ]
      },
      {
        "depends_on": [
          "case_operator_leaf_semantic_evidence",
          "case_tb_scaffold",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "single_transformer_layer",
        "phase": "single_layer_kernel",
        "required_maturity": "single_layer_functional",
        "tool_roles": [
          "tb_scaffold_generate",
          "stage_leaf_static",
          "leaf_functional_sim",
          "leaf_golden_compare",
          "tb_scaffold",
          "single_layer_kernel"
        ]
      },
      {
        "depends_on": [
          "single_transformer_layer",
          "case_operator_leaf_semantic_evidence",
          "case_tb_scaffold",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_single_layer_functional",
        "phase": "single_layer_functional",
        "required_maturity": "single_layer_functional",
        "tool_roles": [
          "single_layer_functional_sim"
        ]
      },
      {
        "depends_on": [
          "case_single_layer_functional"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_single_layer_golden_compare",
        "phase": "single_layer_golden_compare",
        "required_maturity": "single_layer_functional",
        "tool_roles": [
          "single_layer_golden_reference_builder",
          "single_layer_golden_compare"
        ]
      },
      {
        "depends_on": [
          "case_single_layer_golden_compare",
          "case_single_layer_functional",
          "case_operator_leaf_semantic_evidence",
          "case_target_model_reference",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_single_layer_semantic_evidence",
        "phase": "single_layer_semantic_aggregate",
        "required_maturity": "single_layer_functional",
        "tool_roles": [
          "single_layer_semantic_evidence"
        ]
      },
      {
        "depends_on": [
          "case_single_layer_semantic_evidence"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_board_interface_discovery",
        "phase": "board_interface_discovery",
        "required_maturity": "axi_ddr_functional",
        "tool_roles": [
          "board_interface_discovery"
        ]
      },
      {
        "depends_on": [
          "case_single_layer_semantic_evidence",
          "case_semantic_testbench",
          "case_board_interface_discovery"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_multilayer_pipeline",
        "phase": "multilayer_pipeline",
        "required_maturity": null,
        "tool_roles": [
          "tb_scaffold_generate",
          "single_layer_kernel",
          "single_layer_functional_sim",
          "single_layer_golden_compare",
          "multilayer_pipeline"
        ]
      },
      {
        "depends_on": [
          "case_multilayer_pipeline",
          "case_board_interface_discovery"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_axi_ddr_interface",
        "phase": "board_wrapper_interface",
        "required_maturity": null,
        "tool_roles": [
          "axi_ddr_interface"
        ]
      },
      {
        "depends_on": [
          "case_semantic_testbench",
          "case_single_layer_semantic_evidence",
          "case_multilayer_pipeline",
          "case_board_interface_discovery",
          "case_axi_ddr_interface"
        ],
        "evidence_status": "required_pending_execution",
        "name": "functional_sim",
        "phase": "functional_simulation",
        "required_maturity": null,
        "tool_roles": [
          "vcs_functional_sim",
          "vcs_evidence_analyzer",
          "deadlock_axi_check"
        ]
      },
      {
        "depends_on": [
          "functional_sim",
          "case_multilayer_pipeline"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_multilayer_functional",
        "phase": "multilayer_functional",
        "required_maturity": "multilayer_pipeline_functional",
        "tool_roles": [
          "multilayer_functional_sim"
        ]
      },
      {
        "depends_on": [
          "functional_sim",
          "case_multilayer_functional"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_pipeline_deadlock_check",
        "phase": "multilayer_deadlock_liveness",
        "required_maturity": "multilayer_pipeline_functional",
        "tool_roles": [
          "pipeline_deadlock_check"
        ]
      },
      {
        "depends_on": [
          "functional_sim",
          "case_axi_ddr_interface",
          "case_board_interface_discovery"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_axi_protocol_check",
        "phase": "axi_protocol_check",
        "required_maturity": "axi_ddr_functional",
        "tool_roles": [
          "axi_protocol_check"
        ]
      },
      {
        "depends_on": [
          "functional_sim",
          "case_axi_protocol_check",
          "case_real_weight_artifacts"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_ddr_image_roundtrip",
        "phase": "ddr_image_roundtrip",
        "required_maturity": "axi_ddr_functional",
        "tool_roles": [
          "ddr_image_roundtrip"
        ]
      },
      {
        "depends_on": [
          "functional_sim",
          "case_multilayer_functional",
          "case_pipeline_deadlock_check",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_board_interface_discovery",
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_board_semantic_evidence",
        "phase": "board_semantic_aggregate",
        "required_maturity": "axi_ddr_functional",
        "tool_roles": [
          "board_semantic_evidence"
        ]
      },
      {
        "depends_on": [
          "case_multilayer_pipeline",
          "case_board_interface_discovery",
          "case_axi_ddr_interface",
          "functional_sim",
          "case_multilayer_functional",
          "case_pipeline_deadlock_check",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_board_semantic_evidence"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_vivado_synthesis",
        "phase": "vivado_synthesis",
        "required_maturity": null,
        "tool_roles": [
          "vivado_synthesis",
          "vivado_synthesis_report_check"
        ]
      },
      {
        "depends_on": [
          "case_vivado_synthesis"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_vivado_implementation",
        "phase": "vivado_implementation",
        "required_maturity": null,
        "tool_roles": [
          "vivado_implementation",
          "vivado_implementation_report_check"
        ]
      },
      {
        "depends_on": [
          "case_vivado_implementation",
          "functional_sim",
          "case_axi_ddr_interface",
          "case_multilayer_pipeline"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_runtime_bitstream",
        "phase": "vivado_bitstream",
        "required_maturity": null,
        "tool_roles": [
          "runtime_bitstream"
        ]
      },
      {
        "depends_on": [
          "case_runtime_bitstream"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_runtime_abi_check",
        "phase": "runtime_abi",
        "required_maturity": null,
        "tool_roles": [
          "runtime_abi_check"
        ]
      },
      {
        "depends_on": [
          "case_runtime_bitstream",
          "case_runtime_abi_check",
          "functional_sim",
          "case_real_weight_artifacts"
        ],
        "evidence_status": "required_pending_execution",
        "name": "board_runtime",
        "phase": "board_runtime",
        "required_maturity": null,
        "tool_roles": [
          "board_runtime"
        ]
      }
    ],
    "edge_count": 88,
    "leaf_node_count": 9,
    "node_count": 36,
    "phase_order": [
      "real_weight_catalog",
      "target_model_reference",
      "semantic_testbench_generation",
      "operator_leaf_module",
      "debug_boundary_contract",
      "operator_leaf_functional",
      "operator_leaf_golden_compare",
      "operator_leaf_semantic_aggregate",
      "testbench_scaffold",
      "single_layer_kernel",
      "single_layer_functional",
      "single_layer_golden_compare",
      "single_layer_semantic_aggregate",
      "board_interface_discovery",
      "multilayer_pipeline",
      "board_wrapper_interface",
      "functional_simulation",
      "multilayer_functional",
      "multilayer_deadlock_liveness",
      "axi_protocol_check",
      "ddr_image_roundtrip",
      "board_semantic_aggregate",
      "vivado_synthesis",
      "vivado_implementation",
      "vivado_bitstream",
      "runtime_abi",
      "board_runtime"
    ],
    "policy": {
      "_more_keys": 18,
      "all_gate_tool_roles_must_pass": true,
      "backend_discovery_before_vivado_bitstream": true,
      "backend_requires_all_third_layer_subgates": true,
      "board_axi_ddr_functional_before_backend": true,
      "board_runtime_after_bitstream": true,
      "complete_transformer_block_weight_scope_required": true,
      "do_not_promote_final_design_with_pending_required_node": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
      "dut_real_weight_consumption_proof_required": true,
      "each_spatial_operator_module_must_have_leaf_gate": true,
      "explicit_numeric_comparison_policy_required": true,
      "functional_sim_before_backend": true,
      "functional_sim_before_derived_third_layer_checkers": true,
      "hierarchical_order": {
        "_size": 27,
        "_type": "list"
      },
      "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
      "layer1_operator_leaf_closure": {
        "_size": 8,
        "_type": "list"
      }
    }
  },
  "warnings": []
}
</candidate_verification_artifact_contract>

<candidate_verification_review_artifact>
{
  "attention_semantics_present": true,
  "checker_results": [
    {
      "checker": "task_card_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "task goal constraint is present in SACG"
    },
    {
      "checker": "model_config_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "model, shape, and attention semantics are visible"
    },
    {
      "checker": "numeric_policy_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 4 numeric binding plan and global params are visible"
    },
    {
      "checker": "template_coverage_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 5 template provenance and package static check are visible"
    },
    {
      "checker": "stream_plan_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 3 stream/data-edge plan passed static checks"
    },
    {
      "checker": "parameter_binding_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 4 parameter binding static checks passed"
    },
    {
      "checker": "code_generation_manifest_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 5 manifest targets the current case artifact set"
    },
    {
      "checker": "codegen_package_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "generated package manifest is structurally complete"
    },
    {
      "checker": "codegen_compile_gate",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "completed 4 compile/elaboration command(s)"
    },
    {
      "checker": "codegen_contract_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "all code generation contracts passed"
    },
    {
      "checker": "verification_plan_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 6 plan declares checker list, leaf stage agents, and merge agents"
    },
    {
      "checker": "tool_protocol_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "all required verification tool protocols are configured; planned evidence paths are declared for downstream execution"
    },
    {
      "checker": "human_boundary_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "human-boundary policy forbids smoke-only acceptance and requires board runtime before final pass"
    },
    {
      "checker": "memory_runtime_plan_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "generated code package, memory layout, and runtime config exist for verification handoff"
    },
    {
      "checker": "hierarchical_verification_plan_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "three-layer repair-loop hierarchy and anti-spin debug contract are declared"
    },
    {
      "checker": "verification_artifact_contract_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "all verification artifact contracts are satisfiable"
    },
    {
      "checker": "required_real_tool_evidence_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "real weights, functional simulation, bitstream, and board runtime are required downstream gates; no final pass is claimed"
    },
    {
      "checker": "sacg_reference_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 3, Stage 4, and Stage 5 artifacts referenced by SACG are ready/promoted inputs"
    },
    {
      "checker": "data_order_trace_check",
      "errors": [],
      "evidence_phase": "current_stage_static_trace_ledger",
      "execution_status": "static_only_downstream_sim_required",
      "status": "pass",
      "summary": "Stage 3 stream order and numeric stream policy are available for downstream trace checks"
    },
    {
      "checker": "deadlock_watchdog",
      "errors": [],
      "evidence_phase": "downstream_gate_declared",
      "execution_status": "not_run_required_downstream",
      "status": "pending_downstream",
      "summary": "deadlock watchdog is required through the downstream functional_sim gate and must emit tool evidence"
    },
    {
      "checker": "implementation_package_static",
      "errors": [],
      "evidence_phase": "downstream_gate_declared",
      "execution_status": "not_run_required_downstream",
      "status": "pending_downstream",
      "summary": "implementation package evidence is required through the case_runtime_bitstream downstream gate"
    },
    {
      "checker": "board_runtime",
      "errors": [],
      "evidence_phase": "downstream_gate_declared",
      "execution_status": "not_run_required_downstream",
      "status": "pending_downstream",
      "summary": "board runtime evidence is required for final closure and is not claimed by Stage 6"
    }
  ],
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 19,
    "pending": [
      {
        "checker": "deadlock_watchdog",
        "execution_status": "not_run_required_downstream",
        "summary": "deadlock watchdog is required through the downstream functional_sim gate and must emit tool evidence"
      },
      {
        "checker": "implementation_package_static",
        "execution_status": "not_run_required_downstream",
        "summary": "implementation package evidence is required through the case_runtime_bitstream downstream gate"
      },
      {
        "checker": "board_runtime",
        "execution_status": "not_run_required_downstream",
        "summary": "board runtime evidence is required for final closure and is not claimed by Stage 6"
      }
    ],
    "pending_downstream": 3,
    "warnings": []
  },
  "constraints_referenced": [
    "constraint.beat.pipeline",
    "constraint.codegen.package",
    "constraint.deployment.board",
    "constraint.human.boundary",
    "constraint.memory.board",
    "constraint.model.decoder",
    "constraint.numeric.policy",
    "constraint.parameter.binding",
    "constraint.pipeline.structure",
    "constraint.runtime.board",
    "constraint.shape.model",
    "constraint.stream.order",
    "constraint.task.goal",
    "constraint.template.library",
    "constraint.tool.protocols",
    "constraint.verification.artifacts",
    "constraint.verification.hierarchy",
    "constraint.verification.plan"
  ],
  "constraints_touched": [
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.verification.artifacts"
  ],
  "parameter_binding_count": 9,
  "schema_version": "spatialaccagent.verification_artifacts_review.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {
    "current_certificate_validation": {
      "evidence_contract_version": "spatialaccagent.real_weight_semantic_evidence.v2",
      "policy": "Artifact presence is not certificate validity. Reuse is allowed only when the current validator returns current_contract_valid=true.",
      "schema_version": "spatialaccagent.current_certificate_validation_summary.v0",
      "scopes": [
        {
          "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "operator_leaf_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage7.single_layer_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "single_layer_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage7.board_axi_ddr_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "board_axi_ddr_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        }
      ]
    },
    "current_stage_acceptance": [
      "verification_plan must declare the three debug/repair layers: operator leaf modules, single transformer-layer kernel, and board AXI/DDR wrapped system",
      "verification_artifact_contract must pass before the Stage 6 transition can be promoted",
      "required tool protocols and generated handoff artifacts must be configured and present",
      "upstream Stage 3, Stage 4, and Stage 5 static gates must be visible as evidence",
      "lower-layer pass evidence is reusable but can be challenged by a bound current-layer CCTG/boundary trace"
    ],
    "later_stage_obligations": [
      "Stage7 executes real tools for the three-layer verification closures; Vivado synthesis/implementation, timing, bitstream, and board runtime are downstream after verification closure",
      "smoke or default generated weights cannot be used as functional correctness acceptance"
    ],
    "risk_classification_rule": "If verification_artifact_contract_check and upstream static gates pass, do not report later VCS/Vivado/board execution obligations as current-stage risks; keep them as required gates or proposed_actions."
  },
  "status": "ready",
  "upstream_evidence": {
    "stage3_pipeline_plan": {
      "attention_semantics_present": true,
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 10,
        "warnings": []
      },
      "data_edge_count": 13,
      "stage_count": 9,
      "status": "ready",
      "stream_edge_count": 13
    },
    "stage4_parameter_binding": {
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 6,
        "warnings": []
      },
      "global_params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "input_bits": 32,
        "lanes": 8,
        "output_bits": 32,
        "tile_k": 8,
        "tile_m": 8,
        "tile_n": 24
      },
      "numeric_binding_plan": {
        "acc_dtype": "fp32",
        "activation_dtype": "fp16",
        "cast_points": [
          {
            "input_bits": 32,
            "input_cast": "32_to_16",
            "internal_elem_bits": 16,
            "op": "rms_norm_1",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_00_rms_norm_1"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "self_attention",
            "output_bits": 32,
            "output_cast": "16_to_32",
            "residual_precision": null,
            "stage_id": "stage_01_self_attention"
          },
          {
            "input_bits": 32,
            "input_cast": "none",
            "internal_elem_bits": 32,
            "op": "residual_add_1",
            "output_bits": 32,
            "output_cast": "none",
            "residual_precision": 32,
            "stage_id": "stage_02_residual_add_1"
          },
          {
            "input_bits": 32,
            "input_cast": "32_to_16",
            "internal_elem_bits": 16,
            "op": "rms_norm_2",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_03_rms_norm_2"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "mlp_gate_proj",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_04_mlp_gate_proj"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "mlp_up_proj",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_05_mlp_up_proj"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "activation_mul",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_06_activation_mul"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "mlp_down_proj",
            "output_bits": 32,
            "output_cast": "16_to_32",
            "residual_precision": null,
            "stage_id": "stage_07_mlp_down_proj"
          },
          {
            "input_bits": 32,
            "input_cast": "none",
            "internal_elem_bits": 32,
            "op": "residual_add_2",
            "output_bits": 32,
            "output_cast": "none",
            "residual_precision": 32,
            "stage_id": "stage_08_residual_add_2"
          }
        ],
        "eps_source": "constraint.model.decoder.norm_type/default eps from template binding",
        "policy_id": "current_run_numeric_policy.md",
        "rounding": "nearest_even",
        "saturation": false,
        "source": "constraint.numeric.policy.default_rules",
        "weight_dtype": "fp16"
      },
      "status": "ready"
    },
    "stage5_code_generation": {
      "compile_gate": {
        "status": "pass",
        "steps": [
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "Compile/compile"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.GeneratedContractCheck"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
            ],
            "returncode": 0,
            "status": "pass"
          }
        ],
        "summary": "completed 4 compile/elaboration command(s)"
      },
      "contract_check": {
        "errors": [],
        "status": "pass",
        "summary": "all code generation contracts passed"
      },
      "generated_files_count": 273,
      "package_static_check": {
        "errors": [],
        "status": "pass",
        "summary": "generated package manifest is structurally complete"
      },
      "status": "ready"
    }
  }
}
</candidate_verification_review_artifact>

<retry_reconciliation_contract>
{
  "promotion_preconditions": [
    "verification_plan_static_check passes",
    "hierarchical_verification_plan_check passes",
    "verification_artifact_contract_check passes",
    "verification_action_audit_check passes",
    "llm_io_quality_check passes",
    "LLM/team outputs do not report current-stage blockers after seeing this reconciliation contract"
  ],
  "same_stage_retry_policy": "Open retry requests and active contamination barriers produced by prior rejected Stage6 transitions are expected inputs to a Stage6 retry. They are blockers for downstream Stage7 consumption, but they are not independent blockers for promoting the refined Stage6 transition when all current Stage6 contract, LLM, action-audit, and quality checks pass. SACG promotion of the new Stage6 transition closes matching retry requests and supersedes barriers for regenerated Stage6 artifacts.",
  "schema_version": "spatialaccagent.stage_retry_reconciliation.v0",
  "source_active_contamination_barriers": [],
  "source_open_retry_requests": [],
  "stage": "stage6.verification_artifacts"
}
</retry_reconciliation_contract>

<stage6_gate_dag_refinement_policy>
{
  "anti_spin_rule": "Do not treat lower-layer pass evidence as absolute, and do not broadly reopen lower layers without bound contradictory trace evidence.",
  "backtrack_rule": "Later stages may request a Stage6 contract backtrack when a missing gate/tool/evidence path is discovered. A passed lower verification layer may be reopened only when the current-layer CCTG/boundary trace explicitly contradicts that pass evidence and binds the contradiction to a challenged lower-layer gate or module; otherwise rerun the failed current-layer trace first.",
  "downstream_after_three_layer_closure": [
    "Vivado bitstream",
    "board runtime log"
  ],
  "llm_role": "Use current SACG memory, generated artifacts, case adapter, and tool protocols to find missing real-world verification gates. If coverage is incomplete, return executable_actions that update Stage6 gate/tool contracts rather than allowing Stage7 to run with a weak plan.",
  "materializable_action_contract": {
    "policy": "Every executable action that requests current Stage6 contract materialization must use the exact stage, ID prefix, and one supported action_type above; do not invent aliases. Conditional future or approval-required actions are proposed_actions, not current Stage6 materialization actions.",
    "required_id_prefix": "stage6.",
    "required_stage": "verification_artifacts",
    "supported_action_types": [
      "cross_layer_semantic_gate_refinement",
      "board_functional_gate_dag_refinement",
      "downstream_tool_gate_hardening",
      "repair_boundary_contract_review",
      "stage7_gate_selector_contract_refinement",
      "verification_gate_dag_refinement",
      "board_and_backend_gate_dag_refinement",
      "verification_artifact_contract_refinement",
      "gate_enablement_check",
      "sacg_constraint_review",
      "verification_contract_promotion",
      "stage_contract_validation"
    ]
  },
  "required_order": [
    "operator leaf modules",
    "single transformer-layer LLM compute kernel",
    "real target-board AXI/DDR wrapped system"
  ],
  "third_layer_internal_subgates": [
    "LLM interpretation of Vivado-exported exact sample-project board facts",
    "model-adaptive multi-layer spatial scheduler generation, ordering, and liveness",
    "target-board AXI/DDR wrapper and protocol checks",
    "DDR image roundtrip",
    "remote VCS/Verilator functional simulation with real input/weight/runtime artifacts"
  ]
}
</stage6_gate_dag_refinement_policy>

<design_team>
{
  "approval_required_for": [
    "Any ambiguous selection among multiple sample-project wrappers, simulation source sets, clocks, AXI/DDR interfaces, Vivado targets, or app-shell targets after evidence-based discov...<len=184>",
    "Any architecture, multi-layer pipeline structure, memory layout, runtime ABI/register-map, or major trusted-template change required for closure.",
    "Any architecture, pipeline structure, memory layout, numeric policy, or major template change proposed after a failed checker.",
    "Any architecture-level or major trusted-template change proposed after localization.",
    "Any broad lower-layer backtrack not justified by a contradictory higher-layer trace bound to the same immutable semantic run identity.",
    "Any change to numeric policy, cast points, rounding, saturation, resolved atol, rtol, or max_mismatch_fraction during the repair loop.",
    "Any change to residual buffering policy, pipeline structure, stream ordering, transfer layout, or memory layout rather than a bounded implementation correction that restores the ex...<len=196>",
    "Any change to the approved decoder-block architecture or operator order."
  ],
  "completed_subtasks": 5,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "executable_actions": [
    {
      "acceptance_checkers": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_tb_scaffold",
        "real_weight_semantic_evidence_check",
        "numeric_policy_check",
        "artifact_hash_check"
      ],
      "action_type": "verification_evidence_preparation",
      "consumes_count": 9,
      "id": "board_axi_ddr.prepare_immutable_semantic_inputs",
      "on_failure": "Classify absent or invalid checkpoint coverage, reference inference, tolerance, harness, or serialization evidence as a checker/golden-reference or loader capability failure. Do no...<len=298>",
      "produces_count": 13,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_weight_manifest_generate",
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_tb_scaffold_generate",
        "case_tb_scaffold",
        "numeric_policy_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_board_interface_discovery",
        "real_tool.case_board_interface_discovery",
        "llm_semantic_extraction_check",
        "no_static_keyword_semantic_matching_check",
        "artifact_hash_check"
      ],
      "action_type": "board_interface_discovery",
      "consumes_count": 8,
      "id": "board_axi_ddr.discover_exact_sample_project_interface",
      "on_failure": "Keep case_multilayer_pipeline, wrapper generation, simulation, and backend blocked. If more than one interface target remains plausible, emit cited alternatives and request bounded...<len=271>",
      "produces_count": 7,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_board_interface_discovery",
        "llm_semantic_extraction",
        "no_static_keyword_semantic_matching",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_axi_ddr_interface",
        "real_tool.case_axi_ddr_interface",
        "real_tool.case_board_shell_wrapper_generate",
        "addr_map_check",
        "data_order_trace_check",
        "transfer_count_check",
        "memory_runtime_plan_check",
        "artifact_hash_check"
      ],
      "action_type": "axi_ddr_wrapper_contract_generation",
      "consumes_count": 12,
      "id": "board_axi_ddr.bind_exact_wrapper_address_and_order_contract",
      "on_failure": "Reject unsupported wrapper assumptions and retain the exact sample-project sources unchanged. Route a pipeline-contract mismatch to the pipeline specialist and a memory/runtime mis...<len=379>",
      "produces_count": 10,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_board_shell_wrapper_generate",
        "case_axi_ddr_interface",
        "addr_map_check",
        "data_order_trace_check",
        "transfer_count_check",
        "memory_runtime_plan_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "functional_sim",
        "real_tool.case_vcs_functional_sim",
        "deadlock_watchdog",
        "required_real_tool_evidence_check",
        "artifact_hash_check"
      ],
      "action_type": "real_tool_execution",
      "consumes_count": 16,
      "id": "board_axi_ddr.run_canonical_board_wrapped_simulation",
      "on_failure": "Do not classify hardware correctness or proceed to Vivado. Preserve all immutable identity inputs, send the real simulator trace to the contract-guided localization action, and rep...<len=281>",
      "produces_count": 10,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "functional_sim_contract_check",
        "case_vcs_functional_sim",
        "case_vcs_evidence_analyzer",
        "functional_sim",
        "deadlock_watchdog",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "case_axi_protocol_check",
        "real_tool.case_axi_protocol_check",
        "deadlock_watchdog",
        "addr_map_check",
        "data_order_trace_check",
        "transfer_count_check"
      ],
      "action_type": "dynamic_protocol_classification",
      "consumes_count": 11,
      "id": "board_axi_ddr.classify_dynamic_pipeline_and_axi_evidence",
      "on_failure": "Identify the earliest failing transaction and boundary before proposing code changes. Invoke contract-guided localization; preserve lower-layer certificates unless a contradictory ...<len=282>",
      "produces_count": 6,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "case_axi_protocol_check",
        "case_deadlock_axi_check",
        "deadlock_watchdog",
        "addr_map_check",
        "data_order_trace_check",
        "transfer_count_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_ddr_image_roundtrip",
        "real_tool.case_ddr_image_roundtrip",
        "real_weight_semantic_evidence_check",
        "numeric_compare",
        "transfer_count_check",
        "artifact_hash_check",
        "output_validity_check"
      ],
      "action_type": "ddr_image_roundtrip_classification",
      "consumes_count": 15,
      "id": "board_axi_ddr.verify_ddr_image_roundtrip_and_consumption",
      "on_failure": "Do not alter expected output or tolerance. Localize whether the first mismatch is image generation, loader binding, AXI address/order, DUT consumption, output serialization, or DUT...<len=266>",
      "produces_count": 6,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_ddr_image_roundtrip",
        "numeric_compare",
        "transfer_count_check",
        "artifact_hash_check",
        "real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_board_semantic_evidence",
        "functional_sim",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "addr_map_check",
        "data_order_trace_check",
        "real_weight_semantic_evidence_check",
        "required_real_tool_evidence_check",
        "verification_action_audit_check",
        "artifact_hash_check"
      ],
      "action_type": "board_semantic_aggregation",
      "consumes_count": 18,
      "id": "board_axi_ddr.aggregate_board_semantic_certificate_and_backend_boundary",
      "on_failure": "Keep case_vivado_synthesis and all later backend, bitstream, ABI, and board-runtime actions blocked. Return the failed or missing subgate and canonical identity to its owner; do no...<len=253>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_board_semantic_evidence",
        "team_aggregate",
        "required_real_tool_evidence_check",
        "verification_action_audit",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "failure_localization_check",
        "targeted_replay_check",
        "causal_repair_context_check",
        "repair_boundary_check",
        "stage_backtrack_request_check"
      ],
      "action_type": "contract_guided_failure_localization",
      "consumes_count": 8,
      "id": "board_axi_ddr.localize_failed_third_layer_evidence",
      "on_failure": "Keep the failed layer and all higher layers blocked. Do not patch a downstream symptom. If localization cannot distinguish multiple roots, request bounded diagnostic approval or ad...<len=235>",
      "produces_count": 5,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "failure_slice_localization",
        "targeted_replay",
        "causal_repair_context_pack",
        "repair_boundary_check",
        "stage_backtrack_request"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "targeted_failed_checker_rerun",
        "verification_action_audit_check",
        "artifact_hash_check"
      ],
      "action_type": "bounded_repair_and_targeted_rerun",
      "consumes_count": 7,
      "id": "board_axi_ddr.apply_bounded_contract_preserving_repair",
      "on_failure": "Keep promotion blocked and return to localization. If repair requires architecture, pipeline, memory-layout, runtime-ABI, numeric-policy, tolerance, major-template, or exact sample...<len=334>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "bounded_template_repair",
        "memory_runtime_repair",
        "targeted_failed_checker_rerun",
        "repair_boundary_check",
        "verification_action_audit",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "boundary_contract_check",
        "case_multilayer_pipeline"
      ],
      "action_type": "verification_gate_dag_refinement",
      "consumes_count": 6,
      "id": "refine.third_layer_pipeline_liveness_subgraph",
      "on_failure": "Keep the refined third-layer contract unpromoted. Report the missing dependency, instrumentation field, or noncanonical-evidence barrier to verification_artifacts.cross_layer_evide...<len=290>",
      "produces_count": 5,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "boundary_contract_generate"
      ]
    },
    {
      "acceptance_checkers": [
        "case_single_layer_semantic_evidence",
        "case_board_interface_discovery",
        "case_axi_ddr_interface",
        "functional_sim",
        "real_tool.case_vcs_functional_sim",
        "artifact_hash_check",
        "numeric_compare",
        "real_weight_semantic_evidence_check",
        "boundary_contract_check"
      ],
      "action_type": "real_tool_execution",
      "consumes_count": 11,
      "id": "execute.canonical_exact_wrapper_board_functional_sim",
      "on_failure": "If an immutable identity, real target-model reference, complete in-scope weight binding, exact-wrapper hash, or simulator capability is absent, classify the result as a verificatio...<len=380>",
      "produces_count": 8,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "functional_sim_contract_check",
        "case_vcs_functional_sim",
        "functional_sim",
        "artifact_hash_check",
        "numeric_compare"
      ]
    },
    {
      "acceptance_checkers": [
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "boundary_contract_check"
      ],
      "action_type": "canonical_evidence_classification",
      "consumes_count": 7,
      "id": "derive.same_run_pipeline_order_transfer_and_liveness_views",
      "on_failure": "Emit a failed classifier with the canonical run identity and earliest observed violating transaction or no-progress interval. Do not rerun an isolated smoke test, reinterpret wrong...<len=334>",
      "produces_count": 7,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_vcs_evidence_analyzer",
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_board_semantic_evidence",
        "required_real_tool_evidence_check",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "real_weight_semantic_evidence_check",
        "numeric_compare"
      ],
      "action_type": "semantic_evidence_aggregation",
      "consumes_count": 12,
      "id": "aggregate.canonical_board_pipeline_semantic_evidence",
      "on_failure": "Do not issue or reuse a board promotion certificate and do not enable backend handoff. Identify the stale, missing, cross-run, out-of-scope, smoke-only, or failed evidence item and...<len=265>",
      "produces_count": 3,
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_board_semantic_evidence",
        "required_real_tool_evidence_check",
        "real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "failure_localization_check",
        "targeted_replay_check",
        "causal_repair_context_check",
        "boundary_contract_check",
        "repair_boundary_check"
      ],
      "action_type": "contract_guided_failure_localization",
      "consumes_count": 6,
      "id": "localize.failed_board_pipeline_trace",
      "on_failure": "Keep the third layer failed and preserve the canonical evidence. Do not speculate about a code fix, reopen a lower layer, or label the failure pipeline-local without an earliest ca...<len=227>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification_repair",
      "tool_roles": [
        "failure_slice_localization",
        "targeted_replay",
        "boundary_trace_rerun",
        "causal_repair_context_pack"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "codegen_compile_gate_check",
        "codegen_contract_check",
        "case_multilayer_pipeline",
        "functional_sim",
        "numeric_compare",
        "real_weight_semantic_evidence_check",
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "targeted_failed_checker_rerun"
      ],
      "action_type": "bounded_pipeline_repair",
      "consumes_count": 8,
      "id": "repair.approved_pipeline_local_failure_and_rerun_board_layer",
      "on_failure": "Keep the repair unpromoted, retain the original immutable checkpoint, stimulus, reference, numeric policy, tolerance, testbench, expected-transfer contract, and wrapper hashes, and...<len=323>",
      "produces_count": 5,
      "requires_approval": true,
      "stage": "verification_repair",
      "tool_roles": [
        "pipeline_repair",
        "repair_boundary_check",
        "codegen_compile_gate",
        "codegen_contract_check",
        "case_multilayer_pipeline",
        "case_vcs_functional_sim",
        "case_vcs_evidence_analyzer",
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "targeted_failed_checker_rerun"
      ]
    },
    {
      "acceptance_checkers": [
        "stage_backtrack_request_check",
        "causal_repair_context_check",
        "boundary_contract_check"
      ],
      "action_type": "targeted_lower_layer_backtrack",
      "consumes_count": 4,
      "id": "route.trace_supported_single_layer_contradiction",
      "on_failure": "Keep the board layer blocked and do not reopen or repair the single-layer or operator-leaf layer from an unsupported board symptom. Require a checker-valid earliest-boundary contra...<len=208>",
      "produces_count": 2,
      "requires_approval": false,
      "stage": "verification_repair",
      "tool_roles": [
        "stage_backtrack_request",
        "causal_repair_context_pack"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "repair_boundary_check"
      ],
      "action_type": "verification_gate_dag_refinement",
      "consumes_count": 8,
      "id": "operator_leaf.01_refine_gate_contract",
      "on_failure": "Keep Stage 7 operator-leaf execution blocked, report the exact cyclic, unbound, or out-of-scope edge, and revise only the operator-leaf contract; do not alter generated RTL, golden...<len=212>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "repair_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_real_weight_artifacts",
        "real_tool.case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "artifact_hash_check"
      ],
      "action_type": "verification_evidence_preparation",
      "consumes_count": 8,
      "id": "operator_leaf.02_prepare_immutable_semantic_root",
      "on_failure": "Classify missing catalog coverage, target-model execution, tolerance resolution, or semantic harness support as a checker/golden-reference capability blocker. Do not launch leaf si...<len=279>",
      "produces_count": 9,
      "requires_approval": false,
      "stage": "verification.operator_leaf",
      "tool_roles": [
        "case_weight_manifest_generate",
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_stage_leaf_static",
        "template_binding_static_check",
        "code_generation_manifest_static_check",
        "parameter_binding_static_check",
        "artifact_hash_check"
      ],
      "action_type": "generated_leaf_static_binding",
      "consumes_count": 7,
      "id": "operator_leaf.03_bind_all_generated_leaf_modules",
      "on_failure": "Regenerate or rebind only the affected leaf from its selected trusted template and upstream parameters. Reject arbitrary replacement RTL and keep all functional and promotion gates...<len=203>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification.operator_leaf",
      "tool_roles": [
        "case_stage_leaf_static",
        "template_binding_static_check",
        "code_generation_manifest_static_check",
        "parameter_binding_static_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "boundary_contract_check",
        "stream_plan_check",
        "artifact_hash_check"
      ],
      "action_type": "boundary_contract_generation",
      "consumes_count": 6,
      "id": "operator_leaf.04_materialize_boundary_contracts",
      "on_failure": "Repair the boundary-contract materialization before freezing the leaf run. Once the semantic run begins, do not mutate the boundary or testbench contract; stop and request a new ru...<len=225>",
      "produces_count": 3,
      "requires_approval": false,
      "stage": "verification.operator_leaf",
      "tool_roles": [
        "boundary_contract_generate",
        "boundary_contract_check",
        "stream_plan_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_leaf_functional",
        "real_tool.case_leaf_functional",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "operator_leaf_real_tool_execution",
      "consumes_count": 7,
      "id": "operator_leaf.05_run_all_leaf_functional_simulations",
      "on_failure": "Do not run the failed leaf's golden-promotion step or any single-layer gate. Route its real tool log and boundary trace to operator_leaf.08_slice_failed_leaf; keep unrelated passed...<len=248>",
      "produces_count": 7,
      "requires_approval": false,
      "stage": "verification.operator_leaf",
      "tool_roles": [
        "case_leaf_functional",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_leaf_golden_compare",
        "real_tool.case_leaf_golden_compare",
        "numeric_compare",
        "artifact_hash_check"
      ],
      "action_type": "operator_leaf_golden_comparison",
      "consumes_count": 6,
      "id": "operator_leaf.06_compare_all_leaves_to_target_model",
      "on_failure": "Preserve checkpoint, stimulus, model reference, tolerance, numeric policy, testbench, and boundary hashes. Send the failing transaction and earliest divergent boundary to operator_...<len=259>",
      "produces_count": 3,
      "requires_approval": false,
      "stage": "verification.operator_leaf",
      "tool_roles": [
        "case_leaf_golden_compare",
        "numeric_compare",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_operator_leaf_semantic_evidence",
        "real_weight_semantic_evidence_check",
        "required_real_tool_evidence_check",
        "artifact_hash_check"
      ],
      "action_type": "semantic_promotion_certificate_assembly",
      "consumes_count": 8,
      "id": "operator_leaf.07_issue_single_immutable_promotion_certificate",
      "on_failure": "Keep case_tb_scaffold, single_transformer_layer, and all higher layers blocked. Reopen only the failed certificate input identified by the checker; do not mint partial certificates...<len=220>",
      "produces_count": 3,
      "requires_approval": false,
      "stage": "verification.operator_leaf",
      "tool_roles": [
        "case_operator_leaf_semantic_evidence",
        "real_tool_evidence_check",
        "required_real_tool_evidence_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "failure_localization_check",
        "targeted_replay_check",
        "causal_repair_context_check",
        "repair_boundary_check"
      ],
      "action_type": "contract_guided_failure_slicing",
      "consumes_count": 6,
      "id": "operator_leaf.08_slice_failed_leaf",
      "on_failure": "Expand instrumentation only along the failing causal path, up to the requested full boundary trace for that path. Do not guess a code fix, reopen unrelated leaves, or promote while...<len=229>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification.operator_leaf_repair",
      "tool_roles": [
        "failure_slice_localization",
        "boundary_trace_rerun",
        "targeted_replay",
        "causal_repair_context_pack"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "case_stage_leaf_static",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "targeted_failed_checker_rerun"
      ],
      "action_type": "bounded_leaf_repair",
      "consumes_count": 7,
      "id": "operator_leaf.09_apply_bounded_repair_and_replay",
      "on_failure": "Repeat localization only for the same implicated causal slice. If the required change crosses architecture, pipeline, memory-layout, numeric-policy, frozen-contract, or major-templ...<len=263>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification.operator_leaf_repair",
      "tool_roles": [
        "bounded_template_repair",
        "case_stage_leaf_static",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "targeted_failed_checker_rerun"
      ]
    },
    {
      "acceptance_checkers": [
        "human_boundary_check",
        "repair_boundary_check",
        "stage_backtrack_request_check"
      ],
      "action_type": "approval_boundary_escalation",
      "consumes_count": 4,
      "id": "operator_leaf.10_request_unbounded_change_approval",
      "on_failure": "Keep the implicated leaf, aggregate operator-leaf certificate, single-layer gate, and higher layers blocked; do not make the unapproved change or silently broaden repair scope.",
      "produces_count": 2,
      "requires_approval": true,
      "stage": "verification.operator_leaf_repair",
      "tool_roles": [
        "architecture_review",
        "human_boundary_check",
        "stage_backtrack_request"
      ]
    },
    {
      "acceptance_checkers": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "numeric_policy_check",
        "artifact_hash_check"
      ],
      "action_type": "verification_evidence_preparation",
      "consumes_count": 8,
      "id": "single_layer.freeze_semantic_identity",
      "on_failure": "Classify missing target-model execution, unresolved initial tolerance, incomplete block tensor scope, or semantic-harness generation as a checker/golden-reference capability blocke...<len=342>",
      "produces_count": 8,
      "requires_approval": false,
      "stage": "stage7.verification.single_layer",
      "tool_roles": [
        "case_weight_manifest_generate",
        "case_target_model_reference",
        "case_semantic_testbench",
        "artifact_hash_check",
        "numeric_policy_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_stage_leaf_static",
        "case_leaf_functional",
        "real_tool.case_leaf_functional",
        "case_leaf_golden_compare",
        "real_tool.case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence",
        "real_weight_semantic_evidence_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "lower_layer_certificate_validation",
      "consumes_count": 7,
      "id": "single_layer.validate_leaf_prerequisite",
      "on_failure": "Keep layer 2 blocked and hand the failing leaf checker evidence to the operator-leaf verification owner. Do not perform independent leaf repair in this role and do not create a reu...<len=239>",
      "produces_count": 2,
      "requires_approval": false,
      "stage": "stage7.verification.operator_leaf_prerequisite",
      "tool_roles": [
        "case_stage_leaf_static",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence",
        "real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "boundary_contract_check",
        "case_tb_scaffold",
        "case_single_transformer_layer",
        "single_transformer_layer",
        "data_order_trace_check",
        "stream_plan_check",
        "artifact_hash_check"
      ],
      "action_type": "connected_kernel_contract_materialization",
      "consumes_count": 7,
      "id": "single_layer.materialize_merge_contract",
      "on_failure": "Block simulation and localize the contract discrepancy against the approved Stage 3 and Stage 4 artifacts. Do not change model order, residual source, activation semantics, stream ...<len=246>",
      "produces_count": 6,
      "requires_approval": false,
      "stage": "stage7.verification.single_layer",
      "tool_roles": [
        "boundary_contract_generate",
        "case_tb_scaffold_generate",
        "case_tb_scaffold",
        "case_single_transformer_layer",
        "single_transformer_layer",
        "stream_plan_check",
        "data_order_trace_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_single_layer_functional",
        "real_tool.case_single_layer_functional",
        "real_tool.case_vcs_functional_sim",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "real_weight_semantic_evidence_check"
      ],
      "action_type": "real_tool_execution",
      "consumes_count": 9,
      "id": "single_layer.run_real_functional_simulation",
      "on_failure": "Do not promote and do not proceed to board integration. Send the real simulator log, first failing transaction, boundary trace, and immutable run identity to the contract-guided lo...<len=277>",
      "produces_count": 8,
      "requires_approval": false,
      "stage": "stage7.verification.single_layer",
      "tool_roles": [
        "case_single_layer_functional",
        "case_vcs_functional_sim",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_single_layer_golden_compare",
        "real_tool.case_single_layer_golden_compare",
        "numeric_compare",
        "data_order_trace_check",
        "artifact_hash_check"
      ],
      "action_type": "immutable_numeric_comparison",
      "consumes_count": 6,
      "id": "single_layer.compare_target_boundary",
      "on_failure": "Preserve checkpoint, stimulus, target reference, policy, atol, rtol, max_mismatch_fraction, testbench hashes, and boundary contract. Route the first ordered mismatch to causal loca...<len=239>",
      "produces_count": 3,
      "requires_approval": false,
      "stage": "stage7.verification.single_layer",
      "tool_roles": [
        "numeric_compare",
        "case_single_layer_golden_compare",
        "data_order_trace_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "failure_localization_check",
        "targeted_replay_check",
        "causal_repair_context_check",
        "repair_boundary_check",
        "stage_retry_request_check",
        "stage_backtrack_request_check"
      ],
      "action_type": "contract_guided_failure_localization",
      "consumes_count": 9,
      "id": "single_layer.localize_contradicting_trace",
      "on_failure": "Keep both promotion and higher-layer execution blocked. Do not guess a module or reopen all leaves; request additional bounded boundary instrumentation if the earliest causal viola...<len=207>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "stage8.repair.single_layer",
      "tool_roles": [
        "failure_slice_localization",
        "targeted_replay",
        "causal_repair_context_pack",
        "repair_boundary_check",
        "stage_retry_request",
        "stage_backtrack_request"
      ]
    }
  ],
  "llm_io_metrics": {
    "executable_action_count": 44,
    "max_duration_sec": 250.88729494700965,
    "max_prompt_bytes": 89879,
    "result_count": 5,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 1135.4679508789995,
    "total_prompt_bytes": 435915
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 5,
  "used_fallback_count": 0
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/sacg_state.json
</source_sacg_state>

<sacg_memory>
{
  "active_contamination_barriers": [],
  "open_backtrack_requests": [],
  "open_retry_requests": [],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [],
  "recent_failure_lessons": [],
  "recent_stage_outcomes": [
    {
      "artifacts": [
        "artifact.stage4.parameter_binding",
        "artifact.stage4.parameter_static_checks"
      ],
      "errors": [],
      "id": "stage_outcome.0001",
      "next_actions": [],
      "retryable": false,
      "stage": "stage4.parameter_binding",
      "status": "ready",
      "summary": "parameter static checks passed",
      "timestamp": "2026-07-09T09:23:00+00:00",
      "transition_id": "transition.0003"
    },
    {
      "artifacts": [
        "artifact.stage5.design_artifact_manifest",
        "artifact.stage5.generated_code_package",
        "artifact.stage5.memory_layout",
        "artifact.stage5.runtime_config"
      ],
      "errors": [],
      "id": "stage_outcome.0002",
      "next_actions": [],
      "retryable": false,
      "stage": "stage5.code_generation",
      "status": "ready",
      "summary": "completed 4 compile/elaboration command(s)",
      "timestamp": "2026-07-09T11:11:05+00:00",
      "transition_id": "transition.0004"
    }
  ],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 0,
  "active_contamination_barriers": [],
  "active_contamination_barriers_truncated": false,
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 0,
  "open_retry_requests": [],
  "open_retry_requests_truncated": false,
  "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
  "schema_version": "spatialaccagent.sacg_memory_truth.v0",
  "truth_source": "source_sacg_state.memory"
}
</sacg_memory_truth>

<action_grounding_registry>
{
  "acceptance_checkers": [
    "sacg_static_check",
    "task_card_check",
    "model_config_check",
    "numeric_policy_check",
    "template_coverage_check",
    "parameter_binding_static_check",
    "code_generation_manifest_static_check",
    "stream_plan_check",
    "memory_runtime_plan_check",
    "boundary_contract_check",
    "failure_localization_check",
    "targeted_replay_check",
    "causal_repair_context_check",
    "template_binding_static_check",
    "repair_boundary_check",
    "verification_plan_static_check",
    "tool_protocol_check",
    "human_boundary_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "sacg_reference_check",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "single_transformer_layer",
    "case_multilayer_pipeline",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_operator_leaf_semantic_evidence",
    "case_single_layer_semantic_evidence",
    "case_board_semantic_evidence",
    "real_weight_semantic_evidence_check",
    "case_tb_scaffold",
    "case_board_interface_discovery",
    "case_axi_ddr_interface",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "board_runtime",
    "functional_sim",
    "deadlock_watchdog",
    "data_order_trace_check",
    "transfer_count_check",
    "addr_map_check",
    "numeric_compare",
    "artifact_hash_check",
    "codegen_compile_gate_check",
    "codegen_contract_check",
    "codegen_package_static_check",
    "verification_artifact_contract_check",
    "required_real_tool_evidence_check",
    "real_tool.case_real_weight_artifacts",
    "real_tool.boundary_contract_check",
    "real_tool.case_leaf_functional",
    "real_tool.case_leaf_golden_compare",
    "real_tool.case_tb_scaffold",
    "real_tool.case_single_transformer_layer",
    "real_tool.case_single_layer_functional",
    "real_tool.case_single_layer_golden_compare",
    "real_tool.case_multilayer_functional",
    "real_tool.case_pipeline_deadlock_check",
    "real_tool.case_vcs_functional_sim",
    "real_tool.case_verilator_functional_sim",
    "real_tool.case_deadlock_axi_check",
    "real_tool.case_board_interface_discovery",
    "real_tool.case_axi_ddr_interface",
    "real_tool.case_axi_protocol_check",
    "real_tool.case_ddr_image_roundtrip",
    "real_tool.case_vivado_synthesis",
    "real_tool.case_vivado_synthesis_report_check",
    "real_tool.case_vivado_implementation",
    "real_tool.case_vivado_implementation_report_check",
    "real_tool.case_board_shell_wrapper_generate",
    "real_tool.case_runtime_abi_check",
    "real_tool.case_runtime_bitstream",
    "real_tool.app_shell_target_discovery_contract",
    "real_tool.app_shell_target_hint_synthesis",
    "real_tool.app_shell_target_discovery_after_hint",
    "real_tool.board_runtime",
    "real_tool.app_shell_runtime_bitstream",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "output_validity_check",
    "targeted_failed_checker_rerun",
    "verification_action_audit_check",
    "llm_io_quality_check",
    "llm_semantic_extraction_check",
    "no_static_keyword_semantic_matching_check",
    "sacg_memory_check",
    "stage_retry_request_check",
    "stage_backtrack_request_check",
    "stage_artifact_trust_barrier_check",
    "backend_app_shell_integration_contract_static_check",
    "backend_app_shell_target_discovery_check",
    "backend_app_shell_target_hint_synthesis_check",
    "backend_bounded_recovery_action_check",
    "backend_recovery_approval_ingest_check"
  ],
  "policy": "Executable actions should use these tool/checker names when applicable. If a required capability is missing, name it as planned_tool.<short_name> and make the rationale say that multi-agent system capability implementation is required.",
  "schema_version": "spatialaccagent.action_grounding_registry.v0",
  "tool_roles": [
    "sacg_validate",
    "sacg_static_check",
    "task_card_check",
    "model_config_check",
    "numeric_policy_check",
    "template_coverage_check",
    "template_binding_static_check",
    "parameter_binding_static_check",
    "code_generation_manifest_static_check",
    "stream_plan_check",
    "memory_runtime_plan_check",
    "repair_boundary_check",
    "boundary_contract_generate",
    "failure_slice_localization",
    "boundary_trace_rerun",
    "targeted_replay",
    "causal_repair_context_pack",
    "verification_plan_static_check",
    "tool_protocol_check",
    "human_boundary_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "sacg_reference_check",
    "codegen_compile_gate",
    "codegen_contract_check",
    "codegen_package_static_check",
    "verification_artifact_contract_check",
    "required_real_tool_evidence_check",
    "real_tool_evidence_check",
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_operator_leaf_semantic_evidence",
    "case_single_layer_semantic_evidence",
    "case_board_semantic_evidence",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "single_transformer_layer",
    "case_multilayer_pipeline",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_tb_scaffold",
    "case_vcs_functional_sim",
    "functional_sim",
    "functional_sim_contract_check",
    "case_verilator_functional_sim",
    "case_weight_manifest_generate",
    "case_tb_scaffold_generate",
    "case_vcs_evidence_analyzer",
    "deadlock_watchdog",
    "data_order_trace_check",
    "transfer_count_check",
    "addr_map_check",
    "numeric_compare",
    "artifact_hash_check",
    "case_deadlock_axi_check",
    "case_board_interface_discovery",
    "case_axi_ddr_interface",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_vivado_synthesis",
    "case_vivado_synthesis_report_check",
    "case_vivado_implementation",
    "case_vivado_implementation_report_check",
    "case_board_shell_wrapper_generate",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "app_shell_target_discovery_contract",
    "app_shell_target_hint_synthesis",
    "app_shell_target_discovery_after_hint",
    "backend_bounded_recovery_action",
    "backend_recovery_approval_ingest",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "board_runtime",
    "output_validity_check",
    "targeted_failed_checker_rerun",
    "bounded_template_repair",
    "pipeline_repair",
    "memory_runtime_repair",
    "architecture_review",
    "team_aggregate",
    "verification_action_audit",
    "llm_io_quality_check",
    "llm_semantic_extraction",
    "no_static_keyword_semantic_matching",
    "sacg_memory_update",
    "stage_retry_request",
    "stage_backtrack_request",
    "stage_artifact_trust_barrier",
    "app_shell_runtime_bitstream"
  ]
}
</action_grounding_registry>

<action_contract_examples>
[
  {
    "acceptance_checkers": [
      "case_real_weight_artifacts",
      "case_target_model_reference",
      "case_semantic_testbench"
    ],
    "action_type": "verification_evidence_preparation",
    "consumes": [
      "artifact.input.model_config",
      "artifact.input.numeric_policy",
      "artifact.stage3.pipeline_plan",
      "current case-adapter target checkpoint",
      "generated/memory/dut_weight_binding_manifest.json"
    ],
    "id": "example.prepare_real_model_semantic_verification",
    "on_failure": "treat missing reference, explicit tolerance, semantic harness, or DUT weight consumption as a verification-capability/code-generation blocker; do not run a legacy fallback test or promote the layer.",
    "produces": [
      "verification/real_weights/full_tensor_catalog.json",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "verification/semantic_testbench/dut_weight_binding_requirements.json"
    ],
    "rationale": "Build immutable semantic evidence from the current case adapter before any hardware correctness claim.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_weight_manifest_generate",
      "case_target_model_reference",
      "case_semantic_testbench"
    ]
  },
  {
    "acceptance_checkers": [
      "functional_sim",
      "data_order_trace_check",
      "deadlock_watchdog",
      "real_weight_semantic_evidence_check"
    ],
    "action_type": "real_tool_execution",
    "consumes": [
      "artifact.stage6.verification_artifact_contract",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "generated/memory/dut_weight_binding_manifest.json",
      "verification/board_simulation/board_simulation_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to Stage8 repair with the violated SACG constraints; do not proceed to Vivado.",
    "produces": [
      "verification/vcs/case_functional_sim.log",
      "verification/board_simulation/rtl_output.memh",
      "verification/debug_closure/boundary_trace.json",
      "verification/case_diagnostics/vcs_functional_diagnosis.json",
      "verification/semantic_evidence/board_axi_ddr.json"
    ],
    "rationale": "Run a real simulator after static hierarchy and artifact gates pass.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_vcs_functional_sim",
      "case_vcs_evidence_analyzer",
      "case_board_semantic_evidence"
    ]
  },
  {
    "acceptance_checkers": [
      "planned_checker.formal_axi_property_check"
    ],
    "action_type": "system_capability_gap",
    "consumes": [
      "artifact.stage6.verification_plan"
    ],
    "id": "example.declare_missing_capability",
    "on_failure": "block promotion until the planned checker is implemented or an approved equivalent exists.",
    "produces": [
      "planned checker implementation task"
    ],
    "rationale": "The design team needs a checker not yet implemented by the multi-agent system.",
    "requires_approval": true,
    "stage": "verification",
    "tool_roles": [
      "planned_tool.formal_axi_property_runner"
    ]
  },
  {
    "acceptance_checkers": [
      "backend_app_shell_target_hint_synthesis_check",
      "backend_bounded_recovery_action_check",
      "human_boundary_check"
    ],
    "action_type": "bounded_recovery",
    "consumes": [
      "artifact.stage9.app_shell_integration_contract",
      "artifact.stage9.app_shell_target_selection_decision",
      "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json"
    ],
    "id": "example.ambiguous_backend_target_recovery",
    "on_failure": "keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval",
    "produces": [
      "artifact.stage9.backend_bounded_recovery_actions"
    ],
    "rationale": "Real backend evidence produced multiple plausible shell integration targets, so the design team must not guess.",
    "requires_approval": true,
    "stage": "backend_board",
    "tool_roles": [
      "app_shell_target_hint_synthesis",
      "app_shell_target_discovery_after_hint"
    ]
  }
]
</action_contract_examples>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "endpoint_configured": true,
  "enforce": true,
  "locked_model": "gpt-5.6-sol",
  "mode": "llm",
  "model": "gpt-5.6-sol",
  "model_override_approval_path": "",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "xhigh",
  "requested_model_override": "",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "agent": {
      "type": "string"
    },
    "approval_required_for": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "executable_actions": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "acceptance_checkers": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "action_type": {
            "type": "string"
          },
          "consumes": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "id": {
            "type": "string"
          },
          "on_failure": {
            "type": "string"
          },
          "produces": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "rationale": {
            "type": "string"
          },
          "requires_approval": {
            "type": "boolean"
          },
          "stage": {
            "type": "string"
          },
          "tool_roles": {
            "items": {
              "type": "string"
            },
            "type": "array"
          }
        },
        "required": [
          "id",
          "stage",
          "action_type",
          "rationale",
          "consumes",
          "produces",
          "tool_roles",
          "acceptance_checkers",
          "on_failure",
          "requires_approval"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "observations": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "proposed_actions": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "risks": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "sacg_focus": {
      "additionalProperties": true,
      "properties": {
        "artifacts": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "constraints": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "edges": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "nodes": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "nodes",
        "edges",
        "constraints",
        "artifacts"
      ],
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    },
    "stage": {
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "summary": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "agent",
    "stage",
    "status",
    "summary",
    "sacg_focus",
    "observations",
    "risks",
    "proposed_actions",
    "executable_actions",
    "approval_required_for"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
