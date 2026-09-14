<agent>
team_decomposer
</agent>

<task>
Decide whether this stage should be decomposed into parallel specialist sub-agents, then produce the subtask plan.
</task>

<rules>
1. Use split_required=false only when the stage is atomic and no independent specialist can add value.
2. If split_required=true, create 2 to 6 subtasks. Put independent specialists in parallel_group=0 and optional auditors/evidence gates in parallel_group=1.
3. Each subtask must have a chip-design-team role and a bounded objective.
4. Each subtask must explicitly define role_profile and role_assignment: mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope.
5. Each subtask must declare action_type, expected_artifacts, acceptance_checkers, handoff_to, and handoff_rule.
6. Role assignments must make cooperation explicit: what this sub-agent consumes, what it produces, which downstream agents/tools consume its output, and which checker accepts it.
7. Every subtask must focus on cross-layer consistency, template binding, checker evidence, implementation/deployment evidence, or repair boundaries.
8. Ground acceptance_checkers and tool-oriented roles in action_grounding_registry. Use exact canonical names whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
9. Use state_summary.sacg_memory_truth, not historical memory text, to decide whether retry requests, backtrack requests, or contamination barriers are currently active blockers.
10. If a required checker/tool is missing, mark the subtask handoff as requiring planned_tool.<short_name> or planned_checker.<short_name> implementation.
11. Do not create agents for generic brainstorming, paper writing, marketing, or unrelated code cleanup.
12. Use the reference subtask plan as a formatting and role-coverage guide; the actual split decision must come from the LLM response.
</rules>

<stage>
parameter_binding
</stage>

<objective>
Bind template parameters and audit DSE/resource risks without changing model or numeric semantics.
</objective>

<paper_problem_definition>
Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design
</paper_problem_definition>

<method_boundary>
SACG-guided, template-constrained, checker-verified design closure; not free-form RTL generation.
</method_boundary>

<role_catalog>
[
  {
    "capabilities": [
      "extract model semantics",
      "audit shape and head mapping",
      "track residual/operator order"
    ],
    "constraint_focus": [
      "constraint.model.decoder",
      "constraint.shape.model"
    ],
    "family": "model_shape",
    "keywords": [
      "model",
      "shape",
      "graph",
      "operator",
      "intake"
    ]
  },
  {
    "capabilities": [
      "bind trusted templates",
      "audit numeric policy",
      "check resource-risk assumptions"
    ],
    "constraint_focus": [
      "constraint.numeric.policy",
      "constraint.template.library",
      "constraint.parameter.binding"
    ],
    "family": "numeric_template",
    "keywords": [
      "numeric",
      "template",
      "parameter",
      "dse",
      "resource"
    ]
  },
  {
    "capabilities": [
      "audit data order",
      "check transfer-count/liveness risks",
      "bind DDR/runtime layout"
    ],
    "constraint_focus": [
      "constraint.stream.order",
      "constraint.beat.pipeline",
      "constraint.memory.board",
      "constraint.runtime.board"
    ],
    "family": "data_memory_runtime",
    "keywords": [
      "data order",
      "transfer",
      "memory",
      "runtime",
      "dataflow",
      "stream",
      "beat"
    ]
  },
  {
    "capabilities": [
      "classify evidence",
      "map failures to violated constraints",
      "enforce repair boundaries"
    ],
    "constraint_focus": [
      "constraint.verification.plan",
      "constraint.human.boundary"
    ],
    "family": "verification_repair",
    "keywords": [
      "verification",
      "checker",
      "failure",
      "repair",
      "boundary",
      "auditor",
      "gate"
    ]
  },
  {
    "capabilities": [
      "prepare implementation handoff",
      "audit timing/board evidence",
      "block unsupported pass claims"
    ],
    "constraint_focus": [
      "constraint.backend_board.plan",
      "constraint.backend.package",
      "constraint.deployment.board"
    ],
    "family": "implementation_deployment",
    "keywords": [
      "backend",
      "synthesis",
      "implementation",
      "timing",
      "board",
      "deployment"
    ]
  }
]
</role_catalog>

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
  },
  "sacg_memory_truth": {
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

<reference_subtask_plan_if_split_is_needed>
[
  {
    "acceptance_checkers": [
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "bindings",
      "global_params"
    ],
    "constraints": [
      "constraint.parameter.binding",
      "constraint.shape.model",
      "constraint.template.library"
    ],
    "id": "parameter_binding.template_parameter_engineer",
    "objective": "Check that every selected stage receives required shape, attention, lane, tile, FIFO, and clock parameters.",
    "parallel_group": 0,
    "role": "template parameter engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 2,
          "_type": "list"
        },
        "consumes": {
          "_keys": [
            "artifact_focus",
            "constraints"
          ],
          "_size": 2,
          "_type": "dict"
        },
        "handoff_to": {
          "_size": 3,
          "_type": "list"
        },
        "produces": {
          "_size": 5,
          "_type": "list"
        }
      },
      "decision_authority": {
        "_size": 3,
        "_type": "list"
      },
      "mission": "Check that every selected stage receives required shape, attention, lane, tile, FIFO, and clock parameters.",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "numeric_template"
    },
    "role_profile": {
      "capabilities": [
        "bind trusted templates",
        "audit numeric policy",
        "check resource-risk assumptions"
      ],
      "constraint_focus": [
        "constraint.numeric.policy",
        "constraint.template.library",
        "constraint.parameter.binding"
      ],
      "family": "numeric_template"
    },
    "title": "Review template parameter binding"
  },
  {
    "acceptance_checkers": [
      "implementation_package_static",
      "numeric_compare",
      "real_tool_evidence_check",
      "sacg_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "binding_policy",
      "global_params"
    ],
    "constraints": [
      "constraint.arch.design_space",
      "constraint.numeric.policy",
      "constraint.deployment.board"
    ],
    "id": "parameter_binding.dse_resource_engineer",
    "objective": "Check whether first-point DSE choices have explicit resource/timing risks and do not silently change model or numeric semantics.",
    "parallel_group": 0,
    "role": "dse resource engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 4,
          "_type": "list"
        },
        "consumes": {
          "_keys": [
            "artifact_focus",
            "constraints"
          ],
          "_size": 2,
          "_type": "dict"
        },
        "handoff_to": {
          "_size": 3,
          "_type": "list"
        },
        "produces": {
          "_size": 5,
          "_type": "list"
        }
      },
      "decision_authority": {
        "_size": 3,
        "_type": "list"
      },
      "mission": "Check whether first-point DSE choices have explicit resource/timing risks and do not silently change model or numeric se...<len=128>",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "numeric_template"
    },
    "role_profile": {
      "capabilities": [
        "bind trusted templates",
        "audit numeric policy",
        "check resource-risk assumptions"
      ],
      "constraint_focus": [
        "constraint.numeric.policy",
        "constraint.template.library",
        "constraint.parameter.binding"
      ],
      "family": "numeric_template"
    },
    "title": "Review design-space risks"
  }
]
</reference_subtask_plan_if_split_is_needed>

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
    "reason": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "split_required": {
      "type": "boolean"
    },
    "stage": {
      "type": "string"
    },
    "subtasks": {
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
          "agent": {
            "type": "string"
          },
          "artifact_focus": {
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
          "expected_artifacts": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "handoff_required": {
            "type": "boolean"
          },
          "handoff_rule": {
            "additionalProperties": true,
            "type": "object"
          },
          "handoff_to": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "id": {
            "type": "string"
          },
          "objective": {
            "type": "string"
          },
          "parallel_group": {
            "type": "integer"
          },
          "role": {
            "type": "string"
          },
          "role_assignment": {
            "additionalProperties": true,
            "type": "object"
          },
          "role_profile": {
            "additionalProperties": true,
            "type": "object"
          },
          "title": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "agent",
          "role",
          "title",
          "objective",
          "constraints",
          "artifact_focus",
          "parallel_group",
          "handoff_required"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "schema_version",
    "stage",
    "split_required",
    "reason",
    "subtasks"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
