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
18. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or action_grounding_registry.acceptance_checkers, or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
19. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
20. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
21. When hierarchical_learning_context is supplied, treat it as live hash-validated lower-layer knowledge rather than informal history. Reuse its certified invariants, and reopen a lower layer only for a current trace that explicitly contradicts a named invariant.
22. When hierarchical_learning_context supplies connected-kernel timing knowledge, preserve its elastic variable-latency token-pipeline semantics: required boundary order and cross-token overlap matter, while strict same-cycle start/end across unequal-latency stages is not required.
23. At board scope, distinguish independent AXI/prefetch progress from output or lifecycle-frontier progress. A current frontier stall localizes what to observe next, but is neither a pass claim nor a preselected RTL root cause.
24. A board output-frontier symptom alone cannot reopen a certified connected kernel. Require a current hash-bound lower-layer contradiction with direct core start, ingress, egress, named causal-boundary, and current-certificate evidence before scheduling lower-layer revalidation.
25. At every verification layer, use successful current-source VCS compilation, elaboration, and linking as the sole acceptance standard. Repair actual compiler errors; do not add runtime, golden-output, waveform, or weight-consumption prerequisites.
26. The action_grounding_registry.verification_execution_policy documents the existing compile-only modes of the leaf, connected-kernel and exact-board tools. These modes already execute real VCS compile/elaboration/link without running simulation. A functional_sim role name does not imply simulation must execute. Reuse these existing roles rather than declaring a planned_tool capability gap solely from their names. At verification_artifacts planning, future VCS certificates are downstream obligations; actual execution still requires them in bottom-up order before backend synthesis.
27. Applying the recorded framework loose defaults for initially missing atol, rtol, or max_mismatch_fraction is authorized and is not a repair-time tolerance change. Never derive or loosen those values from DUT output.
28. A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.
29. During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.
30. At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.
31. Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.
32. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
33. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
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
        "summary": "board runtime evidence is required for final closure and is not claimed by Stage 5"
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
    "stage_agent_count": 8,
    "strategy": "three_layer_repair_loop: operator_leaf_modules -> single_transformer_layer_kernel -> board_axi_ddr_wrapped_system"
  },
  "schema_version": "spatialaccagent.verification_plan.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {},
  "status": "ready",
  "verification_execution_policy": {
    "acceptance": "Real current-source VCS compilation, elaboration and linking; simulator execution and numerical comparison are not acceptance prerequisites.",
    "executor": "accagent/framework/stage_verification.py: compile_only_stage_gates and compile_only_required_gates_by_level select the existing layer tools in bottom-up order",
    "existing_tool_modes": {
      "case_leaf_functional": "scripts/verification/case_leaf_operator_verify.py: current-source VCS compile-only evidence for operator leaves",
      "case_single_layer_functional": "scripts/verification/case_single_layer_stream_sim.py: current-source VCS compile-only evidence for the connected kernel",
      "case_vcs_functional_sim": "scripts/verification/case_board_vcs_functional.py: compile-only VCS evidence for the exact discovered board wrapper; simulation is not invoked"
    },
    "planning_boundary": "Historical functional/golden DAG nodes describe optional diagnostic capabilities. Missing runtime/golden results and layer certificates are downstream execution obligations during verification_artifacts planning, not missing compile-only capabilities. Use existing tool roles; do not invent another compile-only runner merely because a role retains a functional_sim name.",
    "validation_policy": "vcs_compile_only"
  }
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
    "target_stage": "stage5.verification_artifacts",
    "trigger_conditions": {
      "_size": 6,
      "_type": "list"
    }
  },
  "case_adapter": {
    "case_id": "gpt2_hf_case",
    "model_family": "gpt2",
    "source": "built_in_case_adapter",
    "status": "ready"
  },
  "debug_closure_contract": {
    "boundary_count": 11,
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
      "localization": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/verification/debug_closure/failure_localization.json",
      "manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/verification/debug_closure/trace_manifest.json",
      "trace": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/verification/debug_closure/boundary_trace.json"
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
      "leaf_stage.stage_00_layer_norm_1",
      "leaf_stage.stage_01_self_attention",
      "leaf_stage.stage_02_residual_add_1",
      "leaf_stage.stage_03_layer_norm_2",
      "leaf_stage.stage_04_mlp_fc",
      "leaf_stage.stage_05_activation",
      "leaf_stage.stage_06_mlp_proj",
      "leaf_stage.stage_07_residual_add_2",
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
      "case_board_bringup_ready",
      "case_vivado_synthesis",
      "case_vivado_implementation",
      "case_runtime_bitstream",
      "case_runtime_abi_check",
      "board_runtime"
    ],
    "phases": [
      "axi_protocol_check",
      "board_bringup",
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
  "existing_stage5_refinements": {
    "artifacts": {},
    "schema_version": "spatialaccagent.stage5_existing_refinements.v0",
    "status": "missing"
  },
  "functional_sim_candidates": [
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
      "_size": 33,
      "_type": "list"
    },
    "functional_sim_bound": true,
    "functional_sim_candidates": {
      "_size": 1,
      "_type": "list"
    },
    "leaf_aggregate_covers_all_leaf_stages": true,
    "leaf_aggregate_dependencies": {
      "_size": 8,
      "_type": "list"
    },
    "leaf_aggregate_dependency_count": 8,
    "leaf_aggregate_gate": "case_stage_leaf_static",
    "leaf_stage_count": 8,
    "leaf_stage_names": {
      "_size": 8,
      "_type": "list"
    },
    "required_gate_count": 27,
    "required_gate_names": {
      "_size": 27,
      "_type": "list"
    },
    "schema_version": "spatialaccagent.stage5_gate_protocol_coverage.v0"
  },
  "policy": {
    "board_runtime_required_for_final_pass": true,
    "complete_transformer_block_weight_consumption_required": true,
    "contract_guided_debug_closure_required": true,
    "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
    "downstream_failure_requires_failure_slice": true,
    "explicit_numeric_comparison_policy_required": true,
    "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
    "later_stage_missing_gate_or_tool_requires_stage5_backtrack": true,
    "lower_layer_pass_evidence_is_reusable_not_absolute": true,
    "random_or_rtl_derived_expected_output_forbidden": true,
    "real_axi_ddr_runtime_required": true,
    "real_functional_sim_required": true,
    "real_target_model_reference_required": true,
    "real_weight_artifacts_required": true,
    "same_stage_retry_can_supersede_prior_stage5_barriers_after_promotion": true,
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
      "kind": "target_model_weight_catalog_generate",
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
      "kind": "exact_app_shell_vivado",
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
      "kind": "exact_app_shell_vivado",
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
    "stage": "stage5.verification_artifacts"
  },
  "schema_version": "spatialaccagent.verification_artifact_contract.v0",
  "stage5_refinement_materialization": {},
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
          "leaf_stage.stage_00_layer_norm_1",
          "leaf_stage.stage_01_self_attention",
          "leaf_stage.stage_02_residual_add_1",
          "leaf_stage.stage_03_layer_norm_2",
          "leaf_stage.stage_04_mlp_fc",
          "leaf_stage.stage_05_activation",
          "leaf_stage.stage_06_mlp_proj",
          "leaf_stage.stage_07_residual_add_2"
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
          "case_single_layer_semantic_evidence",
          "case_board_interface_discovery",
          "functional_sim"
        ],
        "evidence_status": "required_pending_execution",
        "name": "case_board_bringup_ready",
        "phase": "board_bringup",
        "required_maturity": null,
        "tool_roles": []
      },
      {
        "depends_on": [
          "case_board_bringup_ready"
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
          "case_board_bringup_ready"
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
          "case_board_bringup_ready",
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
    "edge_count": 80,
    "leaf_node_count": 8,
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
      "board_bringup",
      "vivado_synthesis",
      "vivado_implementation",
      "vivado_bitstream",
      "runtime_abi",
      "board_runtime"
    ],
    "policy": {
      "_more_keys": 19,
      "all_gate_tool_roles_must_pass": true,
      "backend_discovery_before_vivado_bitstream": true,
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
        "_size": 28,
        "_type": "list"
      },
      "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
      "layer1_operator_leaf_closure": {
        "_size": 8,
        "_type": "list"
      },
      "layer2_single_layer_kernel_closure": {
        "_size": 5,
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
      "summary": "completed 6 compile/elaboration command(s)"
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
      "summary": "Stage 5 plan declares checker list, leaf stage agents, and merge agents"
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
      "summary": "board runtime evidence is required for final closure and is not claimed by Stage 5"
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
        "summary": "board runtime evidence is required for final closure and is not claimed by Stage 5"
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
  "parameter_binding_count": 8,
  "schema_version": "spatialaccagent.verification_artifacts_review.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {
    "current_certificate_validation": {
      "evidence_contract_version": "spatialaccagent.real_weight_semantic_evidence.v2",
      "policy": "Artifact presence is not certificate validity. Reuse is allowed only when the current validator returns current_contract_valid=true.",
      "schema_version": "spatialaccagent.current_certificate_validation_summary.v0",
      "scopes": [
        {
          "artifact_id": "artifact.stage6.operator_leaf_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "operator_leaf_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage6.single_layer_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "single_layer_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage6.board_axi_ddr_promotion_certificate",
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
      "verification_artifact_contract must pass before the Stage 5 transition can be promoted",
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
        "passed": 11,
        "warnings": []
      },
      "data_edge_count": 11,
      "stage_count": 8,
      "status": "ready",
      "stream_edge_count": 11
    },
    "stage4_parameter_binding": {
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 6,
        "warnings": []
      },
      "global_params": {
        "acc_bits": 32,
        "activation_banks": 4,
        "activation_memory": "xpm_bram",
        "burst_beats": 1,
        "cache_refill_data_width_bits": 512,
        "cache_tile_count": 2,
        "cache_tile_words": 256,
        "clock_target_mhz": null,
        "compute_array_cols": 32,
        "compute_array_rows": 16,
        "compute_backend": "integer_dsp",
        "cross_token_reuse_tokens": 8,
        "elem_bits": 8,
        "fifo_depth": 128,
        "fifo_memory": "xpm_bram",
        "input_bits": 8,
        "integer_mode": true,
        "lanes": 16,
        "large_cache_memory": "xpm_uram",
        "output_bits": 8,
        "pipeline_depth": 1,
        "rounding": "nearest_even",
        "saturation": true,
        "scale_bits": 32,
        "scale_shift": 31,
        "weight_banks": 1,
        "weight_banks_by_role": {
          "weight": 1,
          "weight_attn_out": 1,
          "weight_attn_out_bias": 1,
          "weight_mlp_down": 1,
          "weight_mlp_down_bias": 1,
          "weight_mlp_up": 1,
          "weight_mlp_up_bias": 1,
          "weight_qkv": 1,
          "weight_qkv_bias": 1
        },
        "weight_bits": 4,
        "weight_memory": "xpm_uram"
      },
      "numeric_binding_plan": {
        "acc_dtype": "int32",
        "accumulator_bits": 32,
        "activation_bits": 8,
        "activation_dtype": "int8",
        "cast_points": [
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "layer_norm_1",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_00_layer_norm_1"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "self_attention",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_01_self_attention"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "residual_add_1",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": 8,
            "stage_id": "stage_02_residual_add_1"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "layer_norm_2",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_03_layer_norm_2"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "mlp_fc",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_04_mlp_fc"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "activation",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_05_activation"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "mlp_proj",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_06_mlp_proj"
          },
          {
            "input_bits": 8,
            "input_cast": "none",
            "internal_elem_bits": 8,
            "op": "residual_add_2",
            "output_bits": 8,
            "output_cast": "none",
            "residual_precision": 8,
            "stage_id": "stage_07_residual_add_2"
          }
        ],
        "eps_source": "constraint.model.decoder.norm_type/default eps from template binding",
        "fixed_point_contract": {
          "binary_exponent_is_consumed_by_requantizer": true,
          "binary_exponent_width_bits": 8,
          "fractional_bits": 31,
          "multiplier_bits": 32,
          "multiplier_dtype": "int32",
          "representation": "unsigned_q31_multiplier_times_signed_per_tensor_or_per_channel_binary_exponent",
          "rounding": "nearest_even",
          "saturation": true,
          "shift_is_explicit": true
        },
        "policy_id": "current_run_numeric_policy",
        "rounding": "nearest_even",
        "saturation": true,
        "scale_bits": 32,
        "scale_dtype": "int32",
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4,
        "weight_dtype": "int4"
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
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
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
              "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
            ],
            "returncode": 0,
            "status": "pass"
          }
        ],
        "summary": "completed 6 compile/elaboration command(s)"
      },
      "contract_check": {
        "errors": [],
        "status": "pass",
        "summary": "all code generation contracts passed"
      },
      "generated_files_count": 457,
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
  "stage": "stage5.verification_artifacts"
}
</retry_reconciliation_contract>

<stage5_gate_dag_refinement_policy>
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
    "required_id_prefix": "stage5.",
    "required_stage": "verification_artifacts",
    "supported_action_types": [
      "cross_layer_semantic_gate_refinement",
      "board_functional_gate_dag_refinement",
      "downstream_tool_gate_hardening",
      "repair_boundary_contract_review",
      "stage6_gate_selector_contract_refinement",
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
</stage5_gate_dag_refinement_policy>

<design_team>
{
  "approval_required_for": [
    "Accept a board target discovery guess without cited sample-project or Vivado evidence",
    "Change Transformer-block-only scope or golden boundaries to include embedding/tokenization, final model norm, LM head/logits, or sampling",
    "Change numeric comparison policy/tolerance or broaden DUT scope beyond Transformer blocks",
    "Make a major change to board memory layout, runtime config, AXI address map, or numeric tolerance derived from DUT output",
    "Promote case_vivado_synthesis, case_vivado_implementation, case_runtime_bitstream, or board_runtime before current verification closure evidence",
    "Promote layer-2 DAG before the operator-leaf prerequisite validation record is current-contract valid",
    "Reorder functional_sim before case_board_interface_discovery or before case_axi_ddr_interface",
    "Weaken bottom-up gate order or substitute real-weight/target-reference/semantic-testbench dependencies"
  ],
  "completed_subtasks": 4,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "executable_actions": [
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "tool_protocol_check",
        "human_boundary_check",
        "required_real_tool_evidence_check",
        "memory_runtime_plan_check",
        "stream_plan_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 8,
      "id": "stage6.refine_board_axi_ddr_dag",
      "on_failure": "If gate order, downstream/backend separation, exact sample-wrapper identity, or Transformer-block-only scope fails a current-stage static check, edit the DAG/gate contract within p...<len=245>",
      "produces_count": 4,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "tool_protocol_check",
        "human_boundary_check",
        "memory_runtime_plan_check",
        "stream_plan_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_action_audit_check",
        "required_real_tool_evidence_check",
        "sacg_memory_check",
        "hierarchical_verification_plan_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 4,
      "id": "stage6.audit_board_axi_ddr_dag_handoff",
      "on_failure": "If the audit finds missing evidence binding, downstream gate leakage, or out-of-scope claims, return the DAG/gate map to this planner for bounded correction before any auditor prom...<len=186>",
      "produces_count": 2,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_action_audit",
        "required_real_tool_evidence_check",
        "sacg_memory_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_memory_check",
        "verification_action_audit_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 4,
      "id": "stage6.record_board_dag_sacg_memory",
      "on_failure": "If SACG memory update fails or fails sacg_memory_check, keep the stage handoff blocked and rerun the memory update after correcting the stage summary or artifact references.",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "sacg_memory_update",
        "sacg_memory_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 7,
      "id": "build_operator_leaf_verification_dag",
      "on_failure": "Do not promote the operator-leaf DAG; return a bounded verification-plan repair action to remap missing leaf gate bindings or missing upstream references.",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "verification_plan_static_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 4,
      "id": "build_leaf_gate_contract_map",
      "on_failure": "Block layer-1 closure and hand off a bounded action that leaf gate mappings are incomplete to the single-layer and board DAG planners.",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check",
        "sacg_reference_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 4,
      "id": "declare_leaf_evidence_prerequisites",
      "on_failure": "Treat missing real-weight, target-model-reference, or semantic-testbench dependency binding as a verification-capability/blocking contract error; do not create a smoke gate or fall...<len=192>",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_plan_static_check",
        "tool_protocol_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 3,
      "id": "encode_compile_only_vcs_leaf_order",
      "on_failure": "Do not schedule downstream VCS certificate execution if the leaf gate order does not pass planning checks; route to verification_plan_static_check repair and preserve bottom-up lay...<len=189>",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_plan_static_check",
        "tool_protocol_check",
        "hierarchical_verification_plan_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "verification_plan_static_check",
        "stream_plan_check",
        "numeric_policy_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 6,
      "id": "single_layer.emit_refined_verification_dag",
      "on_failure": "Do not hand off to the board_axi_ddr planner; return the violated edge or gate order to the DAG and rerun static checks until current-contract pass.",
      "produces_count": 2,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "stream_plan_check",
        "numeric_policy_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "tool_protocol_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "verification_planning",
      "consumes_count": 5,
      "id": "single_layer.emit_gate_contract_map",
      "on_failure": "Keep single-layer execution queued but blocked; map each unbound tool/protocol/checker back to the contract and rerun verification_artifact_contract_check.",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "tool_protocol_check",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_weight_semantic_evidence_check",
        "case_operator_leaf_semantic_evidence",
        "case_target_model_reference",
        "case_semantic_testbench",
        "required_real_tool_evidence_check"
      ],
      "action_type": "verification_dependency_gate",
      "consumes_count": 5,
      "id": "single_layer.preflight_operator_leaf_closure",
      "on_failure": "Block single-layer promotion and emit a named missing/stale dependency handoff to the operator-leaf, reference, or semantic-testbench owner; do not substitute generated weights or ...<len=236>",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "real_tool_evidence_check",
        "case_operator_leaf_semantic_evidence",
        "case_target_model_reference",
        "case_semantic_testbench",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "tool_protocol_check",
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check",
        "verification_action_audit_check"
      ],
      "action_type": "verification_contract_update",
      "consumes_count": 3,
      "id": "single_layer.validate_compile_only_tool_binding",
      "on_failure": "Do not promote the layer-2 DAG; correct the tool binding so each gate compiles/elaborates/links in real VCS and explicitly does not execute simulation.",
      "produces_count": 1,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "tool_protocol_check",
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check",
        "single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_artifact_contract_check",
        "tool_protocol_check",
        "human_boundary_check",
        "hierarchical_verification_plan_check",
        "sacg_reference_check",
        "required_real_tool_evidence_check",
        "verification_action_audit_check"
      ],
      "action_type": "verification_gate_promotion",
      "consumes_count": 8,
      "id": "audit.promote_verification_artifacts_plan",
      "on_failure": "If a required gate is missing or misordered, or downstream runtime evidence is claimed as a current-stage pass, block promotion and route the failure to Stage 6 contract-guided loc...<len=190>",
      "produces_count": 3,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "verification_artifact_contract_check",
        "tool_protocol_check",
        "human_boundary_check",
        "hierarchical_verification_plan_check",
        "sacg_reference_check",
        "required_real_tool_evidence_check",
        "verification_action_audit"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "verification_action_audit_check"
      ],
      "action_type": "sacg_memory_update",
      "consumes_count": 3,
      "id": "audit.record_downstream_verification_obligations",
      "on_failure": "If the memory update fails or creates an active boundary/backtrack blocker, do not transition to Stage 7; rerun the SACG memory update and surface the blocker to the transition gat...<len=182>",
      "produces_count": 2,
      "requires_approval": false,
      "stage": "verification_artifacts",
      "tool_roles": [
        "sacg_memory_update"
      ]
    }
  ],
  "llm_io_metrics": {
    "executable_action_count": 13,
    "max_duration_sec": 154.24136956199072,
    "max_prompt_bytes": 101072,
    "result_count": 4,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 510.98235316801583,
    "total_prompt_bytes": 386503
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 4,
  "used_fallback_count": 0
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/sacg_state.json
</source_sacg_state>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "configured_model": "gpt-6.1-sol",
  "endpoint_configured": true,
  "enforce": true,
  "mode": "llm",
  "model": "deepseek-v4-pro",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
  "requested_model_override": "deepseek-v4-pro",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

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
        "artifact.stage4.dse_search_space",
        "artifact.stage4.dse_candidate_records",
        "artifact.stage4.dse_constraint_report",
        "artifact.stage4.dse_pareto_frontier",
        "artifact.stage4.dse_measurements",
        "artifact.stage4.selected_architecture",
        "artifact.stage4.dse_selection_rationale",
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
      "timestamp": "2026-10-20T12:57:18+00:00",
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
      "summary": "completed 6 compile/elaboration command(s)",
      "timestamp": "2026-10-20T13:04:51+00:00",
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

<hierarchical_learning_context>
{
  "debug_layer": null,
  "decision_policy": {
    "current_scope_tools_and_exact_board_wrapper_remain_required": true,
    "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": true,
    "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": true,
    "lower_layer_reopen_requires_current_trace_named_contradiction": true,
    "resolved_artifact_identity_lessons_are_not_rtl_failures": true,
    "use_only_live_validated_lower_layer_evidence": true
  },
  "kernel_timing_knowledge": [],
  "resolved_evidence_lessons": [],
  "schema_version": "spatialaccagent.hierarchical_learning_context.v1",
  "status": "no_validated_lower_layer_evidence",
  "status_bar_contract": {
    "covers_only_live_validated_lower_layer_certificates": true,
    "does_not_replace_current_scope_tool_results": true,
    "maintainer": "framework_deterministic_hash_bound_projection",
    "not_an_llm_generated_history_summary": true,
    "raw_evidence_remains_retrievable_by_path_and_sha256": true
  },
  "validated_lower_layer_certificates": [],
  "verification_scope": null
}
</hierarchical_learning_context>

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
    "connected_kernel_targeted_replay_check",
    "connected_kernel_cctg_contradiction_reconciliation_check",
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
    "backend_recovery_approval_ingest",
    "backend_recovery_approval_ingest_check"
  ],
  "policy": "Executable actions should use these tool/checker names when applicable. A registered acceptance checker may also be requested as a validation operation in tool_roles. If a required capability is missing, name it as planned_tool.<short_name> and make the rationale say that multi-agent system capability implementation is required.",
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
    "connected_kernel_cctg_contradiction_targeted_replay",
    "connected_kernel_targeted_replay_check",
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
    "case_compute_slot_adapter_generate",
    "app_shell_target_discovery_contract",
    "app_shell_target_hint_synthesis",
    "app_shell_target_discovery_after_hint",
    "backend_bounded_recovery_action",
    "backend_bounded_recovery",
    "backend_recovery_approval_ingest",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "board_runtime",
    "output_validity_check",
    "case_stage7_metrics",
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
    "sacg_memory_check",
    "stage_retry_request",
    "stage_backtrack_request",
    "stage_artifact_trust_barrier",
    "app_shell_runtime_bitstream"
  ],
  "verification_execution_policy": {
    "acceptance": "Real current-source VCS compilation, elaboration and linking; simulator execution and numerical comparison are not acceptance prerequisites.",
    "executor": "accagent/framework/stage_verification.py: compile_only_stage_gates and compile_only_required_gates_by_level select the existing layer tools in bottom-up order",
    "existing_tool_modes": {
      "case_leaf_functional": "scripts/verification/case_leaf_operator_verify.py: current-source VCS compile-only evidence for operator leaves",
      "case_single_layer_functional": "scripts/verification/case_single_layer_stream_sim.py: current-source VCS compile-only evidence for the connected kernel",
      "case_vcs_functional_sim": "scripts/verification/case_board_vcs_functional.py: compile-only VCS evidence for the exact discovered board wrapper; simulation is not invoked"
    },
    "planning_boundary": "Historical functional/golden DAG nodes describe optional diagnostic capabilities. Missing runtime/golden results and layer certificates are downstream execution obligations during verification_artifacts planning, not missing compile-only capabilities. Use existing tool roles; do not invent another compile-only runner merely because a role retains a functional_sim name.",
    "validation_policy": "vcs_compile_only"
  }
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
      "artifact.stage5.verification_artifact_contract",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "generated/memory/dut_weight_binding_manifest.json",
      "verification/board_simulation/board_simulation_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to the Stage-6 repair loop with the violated SACG constraints; do not proceed to Vivado.",
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
      "artifact.stage5.verification_plan"
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
      "artifact.stage7.app_shell_integration_contract",
      "artifact.stage7.app_shell_target_selection_decision",
      "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json"
    ],
    "id": "example.ambiguous_backend_target_recovery",
    "on_failure": "keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval",
    "produces": [
      "artifact.stage7.backend_bounded_recovery_actions"
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
          "targeted_replay_plan": {
            "additionalProperties": true,
            "type": "object"
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
