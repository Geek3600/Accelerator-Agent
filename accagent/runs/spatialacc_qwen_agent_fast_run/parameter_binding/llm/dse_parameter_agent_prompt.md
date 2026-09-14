<agent>
dse_parameter_agent
</agent>

<task>
Review the first architecture parameter binding point, team decomposition, and DSE risks.
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
21. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
22. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
</rules>

<candidate_parameter_binding>
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
  "resource_estimates": [
    {
      "activation_elements": 14336,
      "compute_ops": 14336,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "rms_norm_1",
      "stage_id": "stage_00_rms_norm_1",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 896
    },
    {
      "activation_elements": 14336,
      "compute_ops": 243712,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "self_attention",
      "stage_id": "stage_01_self_attention",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 1835008
    },
    {
      "activation_elements": 14336,
      "compute_ops": 14336,
      "datapath_bits": 256,
      "elem_bits": 32,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "residual_add_1",
      "stage_id": "stage_02_residual_add_1",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 0
    },
    {
      "activation_elements": 14336,
      "compute_ops": 14336,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "rms_norm_2",
      "stage_id": "stage_03_rms_norm_2",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 896
    },
    {
      "activation_elements": 77824,
      "compute_ops": 69730304,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "mlp_gate_proj",
      "stage_id": "stage_04_mlp_gate_proj",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 4358144
    },
    {
      "activation_elements": 77824,
      "compute_ops": 69730304,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "mlp_up_proj",
      "stage_id": "stage_05_mlp_up_proj",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 4358144
    },
    {
      "activation_elements": 77824,
      "compute_ops": 77824,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "activation_mul",
      "stage_id": "stage_06_activation_mul",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 0
    },
    {
      "activation_elements": 14336,
      "compute_ops": 69730304,
      "datapath_bits": 128,
      "elem_bits": 16,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "mlp_down_proj",
      "stage_id": "stage_07_mlp_down_proj",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 4358144
    },
    {
      "activation_elements": 14336,
      "compute_ops": 14336,
      "datapath_bits": 256,
      "elem_bits": 32,
      "estimate_kind": "symbolic_first_order",
      "lanes": 8,
      "op": "residual_add_2",
      "stage_id": "stage_08_residual_add_2",
      "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
      "weight_elements": 0
    }
  ],
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
</candidate_parameter_binding>

<stage_gate_policy>
{
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
}
</stage_gate_policy>

<checker_results>
[
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
]
</checker_results>

<checker_summary>
{
  "errors": [],
  "failed": 0,
  "passed": 6,
  "warnings": []
}
</checker_summary>

<parameter_static_checks>
{
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
  "schema_version": "spatialaccagent.parameter_static_checks.v0",
  "stage": "parameter_binding",
  "status": "pass",
  "summary": {
    "errors": [],
    "failed": 0,
    "passed": 6,
    "warnings": []
  }
}
</parameter_static_checks>

<design_team>
{
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/parameter_binding/team/team_aggregate.json",
  "approval_required_for": [
    "Any Stage 5 memory layout, base-address, DDR partition, or runtime ABI assignment/change before promotion of memory/runtime artifacts",
    "Any architecture or pipeline topology change beyond the checked Stage 3 pipeline structure",
    "Any architecture, pipeline, major template, or board-integration change, and any attempt to treat symbolic estimates as synthesis, timing, resource, or board-pass evidence.",
    "Any architecture, pipeline, numeric bit-width/cast policy, AXI packing, lane-count, or template change proposed to repair later transfer-count, liveness, protocol, or memory-layout failures.",
    "Any board/app-shell target, shell clock, or deployment binding chosen from ambiguous evidence",
    "Any change to Stage 3 edge FIFO buffer depths or FIFO ownership; Stage 4 fifo_depth must remain only a local template default unless explicitly reapproved.",
    "Any change to Stage 3 stream order, edge dtype widths, residual/branch dataflow, or producer/consumer bit contracts.",
    "Any change to accumulator dtype fp32, activation/weight dtype fp16, rounding=nearest_even, saturation=false, cast points, or residual_precision=32.",
    "Any change to model architecture, operator order, tensor dimensions, hidden_size, intermediate_size, seq_len, head_dim, num_q_heads, or num_kv_heads.",
    "Any change to model dimensions, head structure, tensor shapes, or operation semantics to make a DSE choice fit.",
    "Any major template implementation change outside trusted template parameters and bounded glue code",
    "Any memory layout or pipeline repair that would alter stream order, branch precision, residual precision, or transfer-unit interpretation.",
    "Any numeric-policy change to dtype, cast points, rounding, saturation, residual precision, or comparison tolerance",
    "Any numeric-policy change, including precision, cast points, rounding, saturation, residual precision, or RMSNorm epsilon.",
    "Any rebinding of lanes, tile sizes, datapath widths, FIFO semantics, or global-versus-per-stage parameter precedence outside the checked design space.",
    "Any replacement of selected trusted template families or addition of new template parameters that changes numeric/model semantics.",
    "Concrete Stage 5 memory layout decisions such as base addresses, DDR channel mapping, or changes to transfer externalization policy.",
    "Stage 5 concrete DDR base-address, non-overlap memory layout, or runtime ABI assignment decisions."
  ],
  "completed_subtasks": 4,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/parameter_binding/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "parameter_binding_static_check",
        "implementation_package_static",
        "timing_resource_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "artifact.input.design_space",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.bindings.resource_estimate",
        "candidate_stage_artifact.bandwidth_estimate",
        "candidate_stage_artifact.global_params",
        "candidate_stage_artifact.global_param_scope",
        "candidate_stage_artifact.numeric_binding_plan",
        "candidate_stage_artifact.stage_gate_policy",
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.stream_contract_trace"
      ],
      "id": "parameter_binding.dse.emit_legality_resource_audits",
      "on_failure": "Block parameter_binding evidence-gate promotion; issue a bounded parameter-binding retry for any illegal lane/tile/bit-width/FIFO scope or for any unscoped claim of implementation, timing, or board evidence.",
      "produces": [
        "dse_parameter_legality_audit.json",
        "symbolic_resource_risk_register.json",
        "tile_lane_divisibility_report.json",
        "later_stage_evidence_obligation_list.json"
      ],
      "rationale": "Materialize the DSE handoff artifacts from the candidate binding and bind each lane, tile, datapath, FIFO, resource, and bandwidth statement to the supplied design-space, numeric, board AXI, resource, and stage-gate constraints. The action must record implementation, timing, and real-tool evidence as not_run/later-stage when no real tool artifacts are supplied.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "sacg_validate",
        "parameter_binding_static_check",
        "implementation_package_static",
        "timing_resource_check",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "parameter_binding_static_check",
        "sacg_memory_check",
        "stage_artifact_trust_barrier_check"
      ],
      "action_type": "evidence_gate_handoff",
      "consumes": [
        "candidate_stage_artifact",
        "dse_parameter_legality_audit.json",
        "symbolic_resource_risk_register.json",
        "tile_lane_divisibility_report.json",
        "later_stage_evidence_obligation_list.json",
        "sacg_memory_truth"
      ],
      "id": "parameter_binding.evidence_gate.consume_dse_audits",
      "on_failure": "Do not promote the candidate artifact; create an explicit retry or trust-barrier record naming the failed SACG constraint and the contaminated artifact boundary.",
      "produces": [
        "artifact.stage4.parameter_binding_evidence_gate_audit",
        "artifact.stage4.parameter_binding_promotion_decision"
      ],
      "rationale": "Let the evidence-gate auditor consume the DSE audit outputs without rewriting them, verify SACG linkage and trust barriers, and decide whether the current parameter_binding artifact can be promoted with later-stage obligations preserved.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "team_aggregate",
        "sacg_validate",
        "parameter_binding_static_check",
        "stage_artifact_trust_barrier"
      ]
    },
    {
      "acceptance_checkers": [
        "codegen_contract_check",
        "codegen_package_static_check",
        "stream_plan_check",
        "transfer_count_check"
      ],
      "action_type": "static_contract_enforcement",
      "consumes": [
        "artifact.stage2.template_selection",
        "artifact.stage3.pipeline_plan",
        "artifact.stage3.pipeline_static_checks",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.numeric_binding_plan",
        "candidate_stage_artifact.stream_contract_trace",
        "candidate_stage_artifact.global_param_scope",
        "dse_parameter_legality_audit.json",
        "tile_lane_divisibility_report.json"
      ],
      "id": "later_stage.codegen.preserve_parameter_scope",
      "on_failure": "Localize the mismatch to template binding or codegen contract; request bounded template/codegen repair and do not change model dimensions, numeric policy, lanes, or tiles without approval.",
      "produces": [
        "artifact.stage5.codegen_parameter_scope_contract",
        "artifact.stage5.codegen_manifest_with_bound_params"
      ],
      "rationale": "Prevent later generated code from silently changing DSE or numeric semantics by enforcing per-stage parameter precedence, checked tile overrides, local FIFO-default scope, stream bit widths, and numeric cast points.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "codegen_contract_check",
        "codegen_package_static_check",
        "stream_plan_check",
        "transfer_count_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "deployment_board_check"
      ],
      "action_type": "memory_runtime_plan",
      "consumes": [
        "candidate_stage_artifact.bandwidth_estimate",
        "candidate_stage_artifact.stream_contract_trace",
        "artifact.input.target_board_profile",
        "artifact.stage3.pipeline_plan",
        "symbolic_resource_risk_register.json",
        "later_stage_evidence_obligation_list.json"
      ],
      "id": "later_stage.memory_runtime.assign_addresses_and_reconcile_transfers",
      "on_failure": "Keep runtime and backend promotion blocked; repair the memory/runtime plan within the existing parameter contract or request approved re-binding if the memory layout cannot satisfy constraints.",
      "produces": [
        "artifact.stage5.memory_runtime_plan",
        "artifact.stage5.address_map",
        "artifact.stage5.transfer_count_audit"
      ],
      "rationale": "Convert the symbolic bandwidth estimate into a concrete memory/runtime plan with base addresses, 64-byte alignment, non-overlap, AXI beat counts, and explicit treatment of multi-input residual and activation streams.",
      "requires_approval": true,
      "stage": "memory_runtime_planning",
      "tool_roles": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "deployment_board_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_vivado_synthesis",
        "real_tool.case_vivado_synthesis_report_check",
        "real_tool.case_vivado_implementation",
        "real_tool.case_vivado_implementation_report_check",
        "timing_resource_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "artifact.stage5.codegen_manifest_with_bound_params",
        "artifact.stage5.memory_runtime_plan",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "symbolic_resource_risk_register.json",
        "later_stage_evidence_obligation_list.json"
      ],
      "id": "later_stage.backend.collect_real_resource_timing_evidence",
      "on_failure": "Use real tool output for contract-guided localization and bounded repair; do not claim timing/resource pass, do not loosen numeric tolerance, and do not skip verification layers before promotion.",
      "produces": [
        "backend_board/case_diagnostics/vivado_synthesis_report.json",
        "backend_board/case_diagnostics/vivado_implementation_report.json",
        "backend_board/case_diagnostics/timing_resource_evidence.json"
      ],
      "rationale": "After code generation and memory/runtime static gates pass, collect real Vivado synthesis, implementation, timing, and resource evidence so symbolic estimates are not mistaken for hardware feasibility.",
      "requires_approval": false,
      "stage": "backend_board",
      "tool_roles": [
        "case_vivado_synthesis",
        "case_vivado_synthesis_report_check",
        "case_vivado_implementation",
        "case_vivado_implementation_report_check",
        "timing_resource_check",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "stream_plan_check",
        "data_order_trace_check",
        "transfer_count_check",
        "memory_runtime_plan_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "artifact.stage3.pipeline_plan",
        "artifact.stage3.pipeline_static_checks",
        "candidate_stage_artifact.stream_contract_trace",
        "candidate_stage_artifact.bandwidth_estimate",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.global_param_scope",
        "artifact.input.target_board_profile"
      ],
      "id": "parameter_binding.materialize_stream_memory_contract_audits",
      "on_failure": "Block parameter-binding aggregate promotion; localize the mismatch to dtype binding, stream order, AXI packing, transfer count, or FIFO authority, then route to bounded parameter-binding repair or Stage 3 backtrack without changing golden outputs or loosening tolerance.",
      "produces": [
        "stream_dtype_binding_trace.json",
        "axi_packing_transfer_count_audit.json",
        "fifo_authority_audit.json",
        "memory_runtime_risk_notes.json"
      ],
      "rationale": "Generate the expected audit artifacts from the supplied Stage 3 contracts, bound parameters, board AXI facts, and symbolic transfer counts so downstream agents consume checker-bound evidence rather than natural-language conclusions.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "sacg_validate",
        "parameter_binding_static_check",
        "stream_plan_check",
        "data_order_trace_check",
        "transfer_count_check",
        "memory_runtime_plan_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check"
      ],
      "action_type": "later_stage_memory_layout_elaboration",
      "consumes": [
        "axi_packing_transfer_count_audit.json",
        "memory_runtime_risk_notes.json",
        "candidate_stage_artifact.bandwidth_estimate",
        "artifact.input.target_board_profile",
        "artifact.stage3.pipeline_plan"
      ],
      "id": "memory_runtime.assign_checked_ddr_layout_from_symbolic_counts",
      "on_failure": "Keep memory/runtime planning blocked; request bounded memory_runtime_repair or explicit architecture/memory-layout approval if non-overlap, address width, or 64-byte alignment cannot be satisfied without changing stream widths or order.",
      "produces": [
        "artifact.stage5.memory_runtime_plan",
        "artifact.stage5.addr_map_alignment_audit",
        "artifact.stage5.transfer_count_reconciliation"
      ],
      "rationale": "Concrete DDR base addresses and runtime layout are outside this role, but the later planner must preserve the verified 512-bit AXI packing, 64-byte alignment, transfer counts, and stream contracts when assigning memory regions.",
      "requires_approval": true,
      "stage": "memory_runtime_planning",
      "tool_roles": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "data_order_trace_check",
        "functional_sim",
        "deadlock_watchdog",
        "case_axi_protocol_check",
        "failure_localization_check"
      ],
      "action_type": "hierarchical_real_tool_verification_plan",
      "consumes": [
        "stream_dtype_binding_trace.json",
        "fifo_authority_audit.json",
        "axi_packing_transfer_count_audit.json",
        "artifact.stage5.memory_runtime_plan",
        "artifact.stage6.verification_artifact_contract"
      ],
      "id": "verification.verify_stream_order_liveness_protocol_hierarchy",
      "on_failure": "Do not promote to the next hierarchy layer; convert tool output into CCTG/contract-guided localization at the earliest causal boundary, apply bounded repair, and rerun the failed layer before any higher-layer or board claim.",
      "produces": [
        "verification/leaf_stream_order_liveness_reports",
        "verification/single_layer_stream_order_liveness_report",
        "verification/board_axi_ddr_protocol_report"
      ],
      "rationale": "Static Stage 4 evidence cannot prove runtime liveness, data-order preservation through RTL, or AXI protocol correctness; later verification must follow the required leaf-to-single-layer-to-board-wrapped hierarchy.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "case_stage_leaf_static",
        "case_leaf_functional",
        "case_single_transformer_layer",
        "case_single_layer_functional",
        "case_deadlock_axi_check",
        "case_axi_protocol_check",
        "failure_slice_localization"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_action_audit_check",
        "sacg_memory_check"
      ],
      "action_type": "team_handoff",
      "consumes": [
        "stream_dtype_binding_trace.json",
        "axi_packing_transfer_count_audit.json",
        "fifo_authority_audit.json",
        "memory_runtime_risk_notes.json",
        "candidate_stage_artifact.checker_results"
      ],
      "id": "parameter_binding.handoff_stream_memory_audit_to_peer_agents",
      "on_failure": "Keep the team aggregate pending until the handoff packet cites the required artifacts, preserves checker status and caveats, and does not silently assume another specialist's authority.",
      "produces": [
        "parameter_binding.stream_memory_contract_handoff_packet"
      ],
      "rationale": "Make the stream/memory contract findings consumable by the DSE resource-risk engineer and evidence-gate auditor without transferring unverified memory-layout or hardware-pass claims.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "team_aggregate",
        "verification_action_audit"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "numeric_policy_check",
        "template_binding_static_check",
        "parameter_binding_static_check"
      ],
      "action_type": "checker_grounded_audit_materialization",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.stage2.template_selection",
        "artifact.stage3.pipeline_plan",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.numeric_binding_plan",
        "candidate_stage_artifact.global_params",
        "candidate_stage_artifact.global_param_scope",
        "candidate_stage_artifact.checker_results"
      ],
      "id": "parameter_binding.materialize_template_numeric_audit",
      "on_failure": "Block parameter_binding promotion and route only missing or illegal template parameters to bounded_template_repair; require approval before any repair changes model shape, operator order, template family, accumulator dtype, rounding policy, saturation, cast points, or residual precision.",
      "produces": [
        "template_numeric_binding_audit.json",
        "per_stage_parameter_completeness_matrix.json",
        "numeric_cast_contract_trace.json",
        "binding_legality_findings.json"
      ],
      "rationale": "Produce the role-owned audit artifacts and bind the candidate per-stage parameters, numeric cast trace, global default scope, and checker evidence to the named SACG constraints before aggregate promotion.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "sacg_validate",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "stream_plan_check",
        "memory_runtime_plan_check",
        "transfer_count_check"
      ],
      "action_type": "handoff_contract_validation",
      "consumes": [
        "candidate_stage_artifact.stream_contract_trace",
        "candidate_stage_artifact.numeric_binding_plan",
        "candidate_stage_artifact.bandwidth_estimate",
        "artifact.stage3.pipeline_plan"
      ],
      "id": "parameter_binding.handoff_numeric_stream_contracts",
      "on_failure": "Classify failures as stream/memory contract issues and return them to parameter_binding.stream_memory_contract_engineer; do not repair by changing numeric precision, cast points, stream order, or model semantics without approval.",
      "produces": [
        "stream_memory_numeric_handoff.json",
        "transfer_width_branch_precision_findings.json"
      ],
      "rationale": "Ensure peer stream/memory planning consumes the same bit-width and cast contract, especially 32-bit residual skip paths, 16-bit MLP branch streams into activation_mul, and AXI packing assumptions, without changing numeric semantics.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "stream_plan_check",
        "memory_runtime_plan_check",
        "transfer_count_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_action_audit_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "evidence_gate_handoff",
      "consumes": [
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.bandwidth_estimate",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.global_param_scope"
      ],
      "id": "parameter_binding.record_static_evidence_limits",
      "on_failure": "Keep hardware-pass, timing-pass, and board-pass claims blocked until later stages provide required real tool evidence; do not loosen numeric tolerance or modify golden outputs to obtain a pass.",
      "produces": [
        "parameter_binding_static_evidence_limits.json",
        "evidence_gate_numeric_binding_decision.json"
      ],
      "rationale": "Prevent downstream consumers from treating symbolic resource or bandwidth estimates, clock_target_mhz=0, or static checker passes as simulation, synthesis, timing, or board evidence.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "verification_action_audit",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "parameter_binding_static_check",
        "verification_artifact_contract_check",
        "repair_boundary_check",
        "human_boundary_check",
        "stage_retry_request_check",
        "stage_backtrack_request_check",
        "stage_artifact_trust_barrier_check"
      ],
      "action_type": "verification_evidence_gate",
      "consumes": [
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.checker_summary",
        "candidate_stage_artifact.stage_gate_policy",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.numeric_binding_plan",
        "candidate_stage_artifact.stream_contract_trace",
        "candidate_stage_artifact.bandwidth_estimate",
        "state_summary.sacg_memory_truth"
      ],
      "id": "parameter_binding.finalize_stage_gate_bundle",
      "on_failure": "Block promotion; emit a bounded retry, backtrack, or trust-barrier recommendation naming the failed checker and violated constraints. Do not alter golden outputs, loosen tolerance, or claim hardware pass.",
      "produces": [
        "parameter_binding_stage_gate_decision.json",
        "checker_evidence_matrix.json",
        "cross_layer_consistency_closure_report.json",
        "bounded_repair_routing_if_needed.json",
        "sacg_memory_update_recommendation.json"
      ],
      "rationale": "The visible candidate satisfies current-stage criteria, but downstream consumption needs a materialized gate bundle and standard SACG/artifact-boundary checks rather than relying on prose evidence.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "sacg_validate",
        "parameter_binding_static_check",
        "verification_artifact_contract_check",
        "repair_boundary_check",
        "human_boundary_check",
        "stage_retry_request",
        "stage_backtrack_request",
        "stage_artifact_trust_barrier"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "code_generation_manifest_static_check",
        "sacg_static_check"
      ],
      "action_type": "later_stage_handoff",
      "consumes": [
        "parameter_binding_stage_gate_decision.json",
        "candidate_stage_artifact.bandwidth_estimate",
        "candidate_stage_artifact.stream_contract_trace",
        "artifact.stage3.pipeline_plan",
        "artifact.stage3.pipeline_static_checks",
        "artifact.input.target_board_profile"
      ],
      "id": "parameter_binding.handoff_stage5_memory_runtime_obligations",
      "on_failure": "Keep memory/runtime handoff blocked; localize to address map, transfer count, memory schedule, or elaboration contract. Route to memory_runtime_repair, and require approval for any memory-layout or board-memory partition change.",
      "produces": [
        "memory_runtime_plan.json",
        "addr_map.json",
        "transfer_count_reconciliation.json",
        "chisel_elaboration_manifest.json"
      ],
      "rationale": "The candidate exposes static transfer counts and board AXI facts only; Stage 5 must assign concrete memory layout, address ranges, non-overlap/alignment, and elaboration evidence before runtime use.",
      "requires_approval": true,
      "stage": "memory_runtime_planning",
      "tool_roles": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "code_generation_manifest_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "codegen_contract_check",
        "codegen_compile_gate_check",
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "data_order_trace_check",
        "numeric_compare"
      ],
      "action_type": "later_stage_handoff",
      "consumes": [
        "parameter_binding_stage_gate_decision.json",
        "candidate_stage_artifact.bindings",
        "candidate_stage_artifact.numeric_binding_plan",
        "candidate_stage_artifact.stream_contract_trace",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.numeric_policy",
        "artifact.input.tool_protocols"
      ],
      "id": "parameter_binding.handoff_codegen_numeric_stream_obligations",
      "on_failure": "Do not proceed to simulation, synthesis, or board steps; localize the failure to template binding, cast/rounding behavior, stream order, or generated-code contract. Numeric-policy or major template changes require approval.",
      "produces": [
        "code_generation_manifest.json",
        "generated_chisel_parameter_manifest.json",
        "verification_artifact_contract.json",
        "numeric_data_order_obligation_trace.json"
      ],
      "rationale": "Generated implementation must preserve the checked parameter bindings, dtype casts, stream order, and numeric policy; current evidence is static and does not prove functional simulation or hardware correctness.",
      "requires_approval": false,
      "stage": "code_generation_verification",
      "tool_roles": [
        "codegen_contract_check",
        "codegen_compile_gate",
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "data_order_trace_check",
        "numeric_compare"
      ]
    },
    {
      "acceptance_checkers": [
        "targeted_failed_checker_rerun",
        "failure_localization_check",
        "causal_repair_context_check",
        "parameter_binding_static_check",
        "template_binding_static_check",
        "stream_plan_check",
        "transfer_count_check",
        "repair_boundary_check",
        "stage_retry_request_check",
        "stage_backtrack_request_check",
        "stage_artifact_trust_barrier_check"
      ],
      "action_type": "bounded_repair_routing",
      "consumes": [
        "checker_evidence_matrix.json",
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.stage_gate_policy",
        "state_summary.sacg_memory_truth"
      ],
      "id": "parameter_binding.route_failed_binding_evidence",
      "on_failure": "Keep parameter_binding unpromoted; create an active contamination barrier if evidence cannot be trusted, or a backtrack request if model, numeric, architecture, pipeline, memory layout, or template semantics would need to change.",
      "produces": [
        "bounded_repair_routing_if_needed.json",
        "stage_retry_request_if_failed.json",
        "stage_backtrack_request_if_semantic_change_needed.json",
        "stage_artifact_trust_barrier_if_contaminated.json"
      ],
      "rationale": "No current failed checker is visible, but the gate must define a bounded route for any failed meta-checker or targeted rerun without unbounded repair or semantic redesign.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "targeted_failed_checker_rerun",
        "failure_slice_localization",
        "causal_repair_context_pack",
        "parameter_binding_static_check",
        "template_binding_static_check",
        "stream_plan_check",
        "transfer_count_check",
        "bounded_template_repair",
        "stage_retry_request",
        "stage_backtrack_request",
        "stage_artifact_trust_barrier"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 16,
    "max_duration_sec": 545.516513170005,
    "max_prompt_bytes": 55376,
    "result_count": 4,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 1331.020743703004,
    "total_prompt_bytes": 220077
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 4,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/parameter_binding/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

<current_sacg_memory_truth>
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
</current_sacg_memory_truth>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/sacg_state.json
</source_sacg_state>

<sacg_memory>
{
  "active_contamination_barriers": [],
  "open_backtrack_requests": [],
  "open_retry_requests": [],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [],
  "recent_failure_lessons": [],
  "recent_stage_outcomes": [],
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
