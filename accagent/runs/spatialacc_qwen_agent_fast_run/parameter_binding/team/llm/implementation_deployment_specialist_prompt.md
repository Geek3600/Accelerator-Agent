<agent>
implementation_deployment_specialist
</agent>

<task>
Review first-order compute, weight, activation, datapath, tile, lane, and clock assumptions to ensure risks are classified accurately and no symbolic estimate is promoted to synthesis, timing, or board-pass evidence.
</task>

<rules>
1. Review only the supplied artifact summary and named constraints.
2. Treat sacg_memory as the shared long-context design memory: preserve design goals, failure lessons, retry requests, backtrack requests, and contamination barriers.
3. If sacg_memory contains open backtrack_requests or contamination_barriers relevant to this stage, address them explicitly in observations and executable_actions.
4. If inputs include a retry_reconciliation_contract for the current stage, distinguish previous failed artifacts from the candidate retry artifacts: same-stage retry requests/barriers are downstream-consumption blockers until promotion, but they are not independent blockers for approving a refined current-stage contract that explicitly supersedes them after all current-stage checks pass.
5. If inputs include stage_gate_policy, use it to classify current-stage blocking risks versus later-stage actions.
6. If inputs include role_slice_policy or presence_summary, do not infer a field is missing merely because detailed rows were omitted from a compact/role-specific prompt slice.
7. When presence_summary says an artifact class exists, report missing-detail concerns as handoff/action items unless the visible checker status proves a current-stage blocker.
8. Report cross-layer consistency risks across model, shape, numeric policy, data order, memory, runtime, implementation, and board facts.
9. Keep actions bounded and executable by later tools/checkers.
10. Populate executable_actions with concrete next tool/repair actions; each action must name consumed artifacts, produced artifacts, tool roles, acceptance checkers, failure handling, and approval need.
11. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
12. For backend/app-shell target discovery, treat the LLM as the adaptive board-integration engineer: convert supplied board materials and real Vivado evidence into target_discovery_policy updates with cited artifacts; if evidence is ambiguous, require bounded approval instead of guessing names.
13. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name> and state the implementation gap in rationale.
14. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
15. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
16. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
17. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
18. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
</rules>

<team_context>
{
  "objective": "Bind template parameters and audit DSE/resource risks without changing model or numeric semantics.",
  "paper_alignment": {
    "method": "SACG-guided, template-constrained, checker-verified design closure",
    "problem": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design"
  },
  "stage": "parameter_binding",
  "team_rules": [
    "Act as an AI chip design team for FPGA spatial accelerator automatic design, not as isolated static scripts.",
    "Stay inside the SpatialAccAgent paper story: cross-layer consistency for LLM spatial accelerators.",
    "Treat SACG as the design team's shared memory and evidence ledger; do not rely on natural-language memory as correctness evidence.",
    "Use trusted templates and bounded glue code; do not propose free-form RTL rewrites outside approved repair boundaries.",
    "Map every observation to model, shape, numeric precision, data order, transfer unit, memory, runtime, implementation, or deployment constrai...<len=144>",
    "Do not bypass checkers, modify golden outputs, loosen tolerance, or claim hardware pass without tool evidence.",
    "For board/app-shell integration, use LLM reasoning to synthesize profile/contract policy from user-supplied materials and real tool evidence...<len=199>"
  ]
}
</team_context>

<subtask>
{
  "acceptance_checkers": [
    "sacg_static_check",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "required_real_tool_evidence_check"
  ],
  "action_type": "sacg_constraint_review",
  "agent": "implementation_deployment_specialist",
  "artifact_focus": [
    "bindings.resource_estimate",
    "bandwidth_estimate.used_for",
    "stage_gate_policy",
    "global_params.clock_target_mhz",
    "artifact.input.target_board_profile",
    "artifact.input.tool_availability"
  ],
  "constraints": [
    "constraint.arch.design_space",
    "constraint.resource.estimate",
    "constraint.deployment.board",
    "constraint.tool.profile",
    "constraint.tool.protocols",
    "constraint.backend_board.plan"
  ],
  "expected_artifacts": [
    "parameter_binding.dse_resource_risk_report",
    "non_evidence_claims_audit",
    "later_stage_tool_obligation_list"
  ],
  "handoff_rule": {
    "completion_criteria": [],
    "evidence_rule": "Do not claim pass unless evidence is bound to SACG constraints or explicitly recorded as not_run.",
    "produces": [
      "sacg_focus",
      "observations",
      "risks",
      "proposed_actions",
      "approval_required_for"
    ]
  },
  "handoff_to": [
    "parameter_binding.evidence_gate_auditor"
  ],
  "id": "parameter_binding.dse_resource_engineer",
  "objective": "Review first-order compute, weight, activation, datapath, tile, lane, and clock assumptions to ensure risks are classified accurately and no symbolic estimate is promoted to synthesis, timing, or board-pass evidence.",
  "role": "DSE resource risk engineer",
  "title": "Classify symbolic resource and implementation risks"
}
</subtask>

<state_summary>
{
  "artifacts": [
    {
      "id": "artifact.input.material_index",
      "type": "input.material_index"
    },
    {
      "id": "artifact.input.sample_project_index",
      "type": "input.sample_project_index"
    },
    {
      "id": "artifact.input.field_evidence",
      "type": "input.field_evidence"
    },
    {
      "id": "artifact.input.task_card",
      "type": "input.task_card"
    },
    {
      "id": "artifact.input.model_config",
      "type": "input.model_config"
    },
    {
      "id": "artifact.input.numeric_policy",
      "type": "input.numeric_policy"
    },
    {
      "id": "artifact.input.template_library",
      "type": "input.template_library"
    },
    {
      "id": "artifact.input.template_metadata",
      "type": "input.template_metadata"
    },
    {
      "id": "artifact.input.design_space",
      "type": "input.design_space"
    },
    {
      "id": "artifact.input.target_board_profile",
      "type": "input.target_board_profile"
    },
    {
      "id": "artifact.input.tool_profile",
      "type": "input.tool_profile"
    },
    {
      "id": "artifact.input.tool_availability",
      "type": "input.tool_availability"
    },
    {
      "id": "artifact.input.tool_protocols",
      "type": "input.tool_protocols"
    },
    {
      "id": "artifact.input.case_adapter",
      "type": "input.case_adapter"
    },
    {
      "id": "artifact.input.human_agent_boundary",
      "type": "input.human_agent_boundary"
    },
    {
      "id": "artifact.stage2.template_selection",
      "type": "stage.template_selection"
    },
    {
      "id": "artifact.stage3.pipeline_plan",
      "type": "stage.pipeline_plan"
    },
    {
      "id": "artifact.stage3.pipeline_static_checks",
      "type": "stage.pipeline_static_checks"
    }
  ],
  "constraints": [
    {
      "id": "constraint.source.materials",
      "type": "source_materials"
    },
    {
      "id": "constraint.source.evidence",
      "type": "source_evidence"
    },
    {
      "id": "constraint.task.goal",
      "type": "task"
    },
    {
      "id": "constraint.model.decoder",
      "type": "model"
    },
    {
      "id": "constraint.shape.model",
      "type": "shape"
    },
    {
      "id": "constraint.numeric.policy",
      "type": "numeric"
    },
    {
      "id": "constraint.template.library",
      "type": "template"
    },
    {
      "id": "constraint.arch.design_space",
      "type": "architecture"
    },
    {
      "id": "constraint.deployment.board",
      "type": "deployment"
    },
    {
      "id": "constraint.memory.board",
      "type": "memory"
    },
    {
      "id": "constraint.runtime.board",
      "type": "runtime"
    },
    {
      "id": "constraint.tool.profile",
      "type": "tool_profile"
    },
    {
      "id": "constraint.tool.protocols",
      "type": "tool"
    },
    {
      "id": "constraint.case.adapter",
      "type": "verification_case_adapter"
    },
    {
      "id": "constraint.human.boundary",
      "type": "human_boundary"
    },
    {
      "id": "constraint.cross_layer.input_consistency",
      "type": "cross_layer_consistency"
    },
    {
      "id": "constraint.pipeline.structure",
      "type": "pipeline"
    },
    {
      "id": "constraint.stream.order",
      "type": "data_order"
    },
    {
      "id": "constraint.beat.pipeline",
      "type": "transfer_alignment"
    },
    {
      "id": "constraint.buffering.pipeline",
      "type": "buffering"
    },
    {
      "id": "constraint.flow_control.pipeline",
      "type": "flow_control"
    },
    {
      "id": "constraint.memory_schedule.pipeline",
      "type": "memory_schedule"
    },
    {
      "id": "constraint.liveness.pipeline",
      "type": "liveness"
    }
  ],
  "design_id": "qwen2_spatialacc_agent_run",
  "edges": 21,
  "failed_invariants": [],
  "nodes": 32,
  "sacg_memory": {
    "active_contamination_barriers": [],
    "open_backtrack_requests": [],
    "open_retry_requests": [],
    "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
    "recent_contamination_barriers": [],
    "recent_failure_lessons": [],
    "recent_stage_outcomes": [],
    "schema_version": "spatialaccagent.sacg_memory.v0"
  }
}
</state_summary>

<candidate_stage_artifact>
{
  "bandwidth_estimate": {
    "board_axi": {
      "addr_width_bits": 37,
      "alignment_bytes": 64,
      "core_side_interface_name": "c0_ddr4_s_axi_*",
      "data_bytes": 64,
      "data_width_bits": 512,
      "ddr_channels": 1,
      "protocol": "AXI",
      "source": "constraint.memory.board.memory_system"
    },
    "estimate_kind": "symbolic_transfer_count_from_bound_params",
    "notes": [
      "Stage 5 assigns concrete base addresses and checks non-overlap/alignment.",
      "Stage 6+ must provide real simulation, implementation, timing, and board evidence."
    ],
    "per_stage": [
      {
        "aligned_bytes": 87808,
        "axi_beats": 1372,
        "input_activation_bytes": 57344,
        "input_bits": 32,
        "op": "rms_norm_1",
        "output_activation_bytes": 28672,
        "output_bits": 16,
        "stage_id": "stage_00_rms_norm_1",
        "total_bytes": 87808,
        "weight_bits": 16,
        "weight_bytes": 1792
      },
      {
        "aligned_bytes": 3756032,
        "axi_beats": 58688,
        "input_activation_bytes": 28672,
        "input_bits": 16,
        "op": "self_attention",
        "output_activation_bytes": 57344,
        "output_bits": 32,
        "stage_id": "stage_01_self_attention",
        "total_bytes": 3756032,
        "weight_bits": 16,
        "weight_bytes": 3670016
      },
      {
        "aligned_bytes": 114688,
        "axi_beats": 1792,
        "input_activation_bytes": 57344,
        "input_bits": 32,
        "op": "residual_add_1",
        "output_activation_bytes": 57344,
        "output_bits": 32,
        "stage_id": "stage_02_residual_add_1",
        "total_bytes": 114688,
        "weight_bits": 32,
        "weight_bytes": 0
      },
      {
        "aligned_bytes": 87808,
        "axi_beats": 1372,
        "input_activation_bytes": 57344,
        "input_bits": 32,
        "op": "rms_norm_2",
        "output_activation_bytes": 28672,
        "output_bits": 16,
        "stage_id": "stage_03_rms_norm_2",
        "total_bytes": 87808,
        "weight_bits": 16,
        "weight_bytes": 1792
      },
      {
        "aligned_bytes": 8900608,
        "axi_beats": 139072,
        "input_activation_bytes": 28672,
        "input_bits": 16,
        "op": "mlp_gate_proj",
        "output_activation_bytes": 155648,
        "output_bits": 16,
        "stage_id": "stage_04_mlp_gate_proj",
        "total_bytes": 8900608,
        "weight_bits": 16,
        "weight_bytes": 8716288
      },
      {
        "aligned_bytes": 8900608,
        "axi_beats": 139072,
        "input_activation_bytes": 28672,
        "input_bits": 16,
        "op": "mlp_up_proj",
        "output_activation_bytes": 155648,
        "output_bits": 16,
        "stage_id": "stage_05_mlp_up_proj",
        "total_bytes": 8900608,
        "weight_bits": 16,
        "weight_bytes": 8716288
      },
      {
        "aligned_bytes": 311296,
        "axi_beats": 4864,
        "input_activation_bytes": 155648,
        "input_bits": 16,
        "op": "activation_mul",
        "output_activation_bytes": 155648,
        "output_bits": 16,
        "stage_id": "stage_06_activation_mul",
        "total_bytes": 311296,
        "weight_bits": 16,
        "weight_bytes": 0
      },
      {
        "aligned_bytes": 8929280,
        "axi_beats": 139520,
        "input_activation_bytes": 155648,
        "input_bits": 16,
        "op": "mlp_down_proj",
        "output_activation_bytes": 57344,
        "output_bits": 32,
        "stage_id": "stage_07_mlp_down_proj",
        "total_bytes": 8929280,
        "weight_bits": 16,
        "weight_bytes": 8716288
      },
      {
        "aligned_bytes": 114688,
        "axi_beats": 1792,
        "input_activation_bytes": 57344,
        "input_bits": 32,
        "op": "residual_add_2",
        "output_activation_bytes": 57344,
        "output_bits": 32,
        "stage_id": "stage_08_residual_add_2",
        "total_bytes": 114688,
        "weight_bits": 32,
        "weight_bytes": 0
      }
    ],
    "schema_version": "spatialaccagent.parameter_bandwidth_estimate.v0",
    "total_aligned_bytes_per_layer": 31202816,
    "used_for": "static transfer-count and AXI packing sanity only; not board bandwidth or timing pass evidence"
  },
  "binding_policy": "stage2_strict_binding_plus_checked_global_defaults",
  "bindings": [
    {
      "legality_errors": [],
      "op": "rms_norm_1",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "eps": 1e-06,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16
      },
      "resource_estimate": {
        "activation_elements": 14336,
        "compute_ops": 14336,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 896
      },
      "stage_id": "stage_00_rms_norm_1",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "legality_errors": [],
      "op": "self_attention",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "head_dim": 64,
        "hidden_size": 896,
        "input_bits": 16,
        "lanes": 8,
        "num_kv_heads": 2,
        "num_q_heads": 14,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "seq_len": 16
      },
      "resource_estimate": {
        "activation_elements": 14336,
        "compute_ops": 243712,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 1835008
      },
      "stage_id": "stage_01_self_attention",
      "status": "ready",
      "template_id": "attention"
    },
    {
      "legality_errors": [],
      "op": "residual_add_1",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 32,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32
      },
      "resource_estimate": {
        "activation_elements": 14336,
        "compute_ops": 14336,
        "datapath_bits": 256,
        "elem_bits": 32,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 0
      },
      "stage_id": "stage_02_residual_add_1",
      "status": "ready",
      "template_id": "residual"
    },
    {
      "legality_errors": [],
      "op": "rms_norm_2",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "eps": 1e-06,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16
      },
      "resource_estimate": {
        "activation_elements": 14336,
        "compute_ops": 14336,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 896
      },
      "stage_id": "stage_03_rms_norm_2",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "legality_errors": [],
      "op": "mlp_gate_proj",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 16,
        "intermediate_size": 4864,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "tile_k": 128,
        "tile_m": 16,
        "tile_n": 128
      },
      "resource_estimate": {
        "activation_elements": 77824,
        "compute_ops": 69730304,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 4358144
      },
      "stage_id": "stage_04_mlp_gate_proj",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "legality_errors": [],
      "op": "mlp_up_proj",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 16,
        "intermediate_size": 4864,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "tile_k": 128,
        "tile_m": 16,
        "tile_n": 128
      },
      "resource_estimate": {
        "activation_elements": 77824,
        "compute_ops": 69730304,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 4358144
      },
      "stage_id": "stage_05_mlp_up_proj",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "legality_errors": [],
      "op": "activation_mul",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 4864,
        "input_bits": 16,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16
      },
      "resource_estimate": {
        "activation_elements": 77824,
        "compute_ops": 77824,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 0
      },
      "stage_id": "stage_06_activation_mul",
      "status": "ready",
      "template_id": "elementwise"
    },
    {
      "legality_errors": [],
      "op": "mlp_down_proj",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 16,
        "intermediate_size": 4864,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "tile_k": 128,
        "tile_m": 16,
        "tile_n": 128
      },
      "resource_estimate": {
        "activation_elements": 14336,
        "compute_ops": 69730304,
        "datapath_bits": 128,
        "elem_bits": 16,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 4358144
      },
      "stage_id": "stage_07_mlp_down_proj",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "legality_errors": [],
      "op": "residual_add_2",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 32,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32
      },
      "resource_estimate": {
        "activation_elements": 14336,
        "compute_ops": 14336,
        "datapath_bits": 256,
        "elem_bits": 32,
        "estimate_kind": "symbolic_first_order",
        "lanes": 8,
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": 0
      },
      "stage_id": "stage_08_residual_add_2",
      "status": "ready",
      "template_id": "residual"
    }
  ],
  "checker_results": [
    {
      "checker": "parameter_stage_numeric_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "bindings=9",
      "warnings": []
    },
    {
      "checker": "edge_dtype_stream_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "edges=13",
      "warnings": []
    },
    {
      "checker": "tile_override_legality_check",
      "errors": [],
      "status": "pass",
      "summary": "per-stage tile params are authoritative; global tile params are defaults only",
      "warnings": []
    },
    {
      "checker": "stream_packing_axi_check",
      "errors": [],
      "status": "pass",
      "summary": "axi_bits=512",
      "warnings": []
    },
    {
      "checker": "bandwidth_memory_estimate_check",
      "errors": [],
      "status": "pass",
      "summary": "total_aligned_bytes_per_layer=31202816",
      "warnings": []
    },
    {
      "checker": "fifo_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "edge_buffers=13; stage fifo_depth is local default, Stage3 edge buffer depths remain authoritative",
      "warnings": []
    }
  ],
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 6,
    "warnings": []
  },
  "constraints_touched": [
    "constraint.parameter.binding",
    "constraint.resource.estimate",
    "constraint.bandwidth.estimate"
  ],
  "global_param_scope": {
    "clock_target_mhz": "board shell clock is unknown unless non-null; this is not timing evidence",
    "fifo_depth": "local template default only; Stage 3 buffer_plan owns edge FIFO depths",
    "tile_k": "default_only; per-stage tile_k takes precedence",
    "tile_m": "default_only; per-stage tile_m takes precedence",
    "tile_n": "default_only; per-stage tile_n takes precedence"
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
  "legality_errors": [],
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
  "schema_version": "spatialaccagent.parameter_binding.v0",
  "stage": "parameter_binding",
  "stage_gate_policy": {
    "current_stage_acceptance": [
      "per-stage params must match Stage 3 numeric_contract and edge stream_contract bit widths",
      "per-stage tile overrides are authoritative and must divide the corresponding tensor dimensions",
      "lanes and all bound bit widths must pack cleanly into the board AXI data width",
      "bandwidth estimates must expose concrete static transfer counts and explicitly remain non-hardware evidence",
      "Stage 3 edge FIFO contracts remain authoritative; Stage 4 local fifo_depth is a template parameter default"
    ],
    "later_stage_obligations": [
      "Stage 5 assigns concrete memory base addresses and elaborates generated Chisel",
      "Stage 6+ supplies real simulation, synthesis, timing, and board evidence",
      "Numeric rounding remains recorded as unspecified unless a later approved numeric policy binds it"
    ],
    "risk_classification_rule": "If checker_results pass, do not report resolved current-stage consistency items as risks; later-stage tool obligations belong in proposed_actions."
  },
  "status": "ready",
  "stream_contract_trace": [
    {
      "dst_input_bits": 32,
      "dst_stage": "stage_00_rms_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "element_bits": 32,
      "kind": "input",
      "src_output_bits": 32,
      "src_stage": "block_input",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 32,
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "element_bits": 32,
      "kind": "residual_skip",
      "src_output_bits": 32,
      "src_stage": "block_input",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 16,
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "element_bits": 16,
      "kind": "main",
      "src_output_bits": 16,
      "src_stage": "stage_00_rms_norm_1",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 32,
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "element_bits": 32,
      "kind": "main",
      "src_output_bits": 32,
      "src_stage": "stage_01_self_attention",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 32,
      "dst_stage": "stage_03_rms_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "element_bits": 32,
      "kind": "main",
      "src_output_bits": 32,
      "src_stage": "stage_02_residual_add_1",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 32,
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "element_bits": 32,
      "kind": "residual_skip",
      "src_output_bits": 32,
      "src_stage": "stage_02_residual_add_1",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 16,
      "dst_stage": "stage_04_mlp_gate_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "element_bits": 16,
      "kind": "mlp_gate_branch",
      "src_output_bits": 16,
      "src_stage": "stage_03_rms_norm_2",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 16,
      "dst_stage": "stage_05_mlp_up_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "element_bits": 16,
      "kind": "mlp_up_branch",
      "src_output_bits": 16,
      "src_stage": "stage_03_rms_norm_2",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 16,
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "element_bits": 16,
      "kind": "mlp_gate_to_mul",
      "src_output_bits": 16,
      "src_stage": "stage_04_mlp_gate_proj",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 4864
      }
    },
    {
      "dst_input_bits": 16,
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "element_bits": 16,
      "kind": "mlp_up_to_mul",
      "src_output_bits": 16,
      "src_stage": "stage_05_mlp_up_proj",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 4864
      }
    },
    {
      "dst_input_bits": 16,
      "dst_stage": "stage_07_mlp_down_proj",
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "element_bits": 16,
      "kind": "main",
      "src_output_bits": 16,
      "src_stage": "stage_06_activation_mul",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 4864
      }
    },
    {
      "dst_input_bits": 32,
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "element_bits": 32,
      "kind": "main",
      "src_output_bits": 32,
      "src_stage": "stage_07_mlp_down_proj",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    },
    {
      "dst_input_bits": 32,
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_08_residual_add_2.to.block_output.output",
      "element_bits": 32,
      "kind": "output",
      "src_output_bits": 32,
      "src_stage": "stage_08_residual_add_2",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 896
      }
    }
  ]
}
</candidate_stage_artifact>

<sacg_memory>
{}
</sacg_memory>

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
      "functional_sim",
      "data_order_trace_check",
      "deadlock_watchdog"
    ],
    "action_type": "real_tool_execution",
    "consumes": [
      "artifact.stage6.verification_artifact_contract",
      "generated/chisel/runtime/runtime_config.json",
      "verification/case_real_weights/input_manifest.json",
      "verification/case_real_weights/packed_weight_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to Stage8 repair with the violated SACG constraints; do not proceed to Vivado.",
    "produces": [
      "verification/case_diagnostics/vcs_functional_diagnosis.json"
    ],
    "rationale": "Run a real simulator after static hierarchy and artifact gates pass.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_vcs_functional_sim",
      "case_vcs_evidence_analyzer"
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
  "locked_model": "gpt-5.5",
  "mode": "llm",
  "model": "gpt-5.5",
  "model_override_approval_path": "",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
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
