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
pipeline_planning
</stage>

<objective>
Plan and audit the spatial pipeline as a set of SACG stream, beat, memory, and liveness constraints.
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
    }
  ],
  "design_id": "qwen2_spatialacc_agent_run",
  "edges": 8,
  "failed_invariants": [],
  "nodes": 21,
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
  "attention_contract": {
    "attention_kind": "gqa",
    "causal": true,
    "gqa_group_size": 7,
    "head_dim": 64,
    "kv_storage_policy": "bounded by target_max_seq_len inside the generated block; external KV-cache materialization requires a later memory-layout artifact",
    "num_kv_heads": 2,
    "num_q_heads": 14,
    "position_encoding": {
      "rope_theta": 1000000.0,
      "type": "rope"
    },
    "seq_len_bound": 16,
    "stage_boundary": "logical self_attention stage covers QKV projection, RoPE, causal GQA attention, and output projection for decoder-block planning"
  },
  "branch_join_contracts": {
    "join_contracts": [
      {
        "fire_rule": "all required inputs valid before fire",
        "input_edges": [
          "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
          "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main"
        ],
        "node": "stage_02_residual_add_1",
        "pairing_key": [
          "token",
          "tile",
          "lane",
          "word"
        ]
      },
      {
        "fire_rule": "all required inputs valid before fire",
        "input_edges": [
          "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
          "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul"
        ],
        "node": "stage_06_activation_mul",
        "pairing_key": [
          "token",
          "tile",
          "lane",
          "word"
        ]
      },
      {
        "fire_rule": "all required inputs valid before fire",
        "input_edges": [
          "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
          "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main"
        ],
        "node": "stage_08_residual_add_2",
        "pairing_key": [
          "token",
          "tile",
          "lane",
          "word"
        ]
      }
    ],
    "split_contracts": [
      {
        "branch_dequeue_rule": "after duplication each branch observes its own downstream ready",
        "duplicator": "ready_valid_broadcast_with_per_output_fifo",
        "node": "stage_03_rms_norm_2",
        "output_edges": [
          "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
          "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch"
        ],
        "source_accept_rule": "source beat is accepted only when all branch FIFOs can enqueue the same token/tile/lane/word"
      }
    ]
  },
  "buffer_plan": [
    {
      "buffer_id": "buffer.edge_data_block_input_to_stage_00_rms_norm_1_input",
      "depth": 32,
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_block_input_to_stage_02_residual_add_1_residual_skip",
      "depth": 64,
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
      "depth": 32,
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_01_self_attention_to_stage_02_residual_add_1_main",
      "depth": 32,
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_03_rms_norm_2_main",
      "depth": 32,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_08_residual_add_2_residual_skip",
      "depth": 64,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_03_rms_norm_2_to_stage_04_mlp_gate_proj_mlp_gate_branch",
      "depth": 64,
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_03_rms_norm_2_to_stage_05_mlp_up_proj_mlp_up_branch",
      "depth": 64,
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_04_mlp_gate_proj_to_stage_06_activation_mul_mlp_gate_to_mul",
      "depth": 32,
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_05_mlp_up_proj_to_stage_06_activation_mul_mlp_up_to_mul",
      "depth": 32,
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main",
      "depth": 32,
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_07_mlp_down_proj_to_stage_08_residual_add_2_main",
      "depth": 32,
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_08_residual_add_2_to_block_output_output",
      "depth": 32,
      "edge_id": "edge.data.stage_08_residual_add_2.to.block_output.output",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    }
  ],
  "checker_results": [
    {
      "checker": "operator_order_check",
      "errors": [],
      "status": "pass",
      "summary": "operator_order=['rms_norm_1', 'self_attention', 'residual_add_1', 'rms_norm_2', 'mlp_gate_proj', 'mlp_up_proj', 'activation_mul', 'mlp_down_proj', 'residual_add_2']",
      "warnings": []
    },
    {
      "checker": "stream_data_edge_mirror_check",
      "errors": [],
      "status": "pass",
      "summary": "edges=13",
      "warnings": []
    },
    {
      "checker": "edge_stream_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "checked_edges=13",
      "warnings": []
    },
    {
      "checker": "shape_numeric_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "elem_bits=16, accumulator_bits=32",
      "warnings": []
    },
    {
      "checker": "branch_join_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "splits=1, joins=3",
      "warnings": []
    },
    {
      "checker": "buffer_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "buffers=13, allowed_depths=[32, 64]",
      "warnings": []
    },
    {
      "checker": "liveness_backpressure_check",
      "errors": [],
      "status": "pass",
      "summary": "directed graph is acyclic; bounded FIFOs provide elasticity and backpressure, not latency-equality proof",
      "warnings": []
    },
    {
      "checker": "memory_runtime_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "regions=6, axi_bits=512",
      "warnings": []
    },
    {
      "checker": "attention_semantics_check",
      "errors": [],
      "status": "pass",
      "summary": "q=14, kv=2, head_dim=64",
      "warnings": []
    },
    {
      "checker": "template_binding_static_check",
      "errors": [],
      "status": "pass",
      "summary": "stages=9, free_form_rtl_generation=false",
      "warnings": []
    }
  ],
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 10,
    "warnings": []
  },
  "constraints_touched": [
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.cross_layer.input_consistency"
  ],
  "data_edges": [
    {
      "axi_beats": 896,
      "dst_port": "in",
      "dst_stage": "stage_00_rms_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "skip",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 448,
      "dst_port": "in",
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_rms_norm_1",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 28672,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "main",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_01_self_attention",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "in",
      "dst_stage": "stage_03_rms_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "skip",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 448,
      "dst_port": "in",
      "dst_stage": "stage_04_mlp_gate_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_gate_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 28672,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 448,
      "dst_port": "in",
      "dst_stage": "stage_05_mlp_up_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_up_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 28672,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 2432,
      "dst_port": "lhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_gate_to_mul",
      "src_port": "out",
      "src_stage": "stage_04_mlp_gate_proj",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 4864
      },
      "transfer_count_bytes": 155648,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 2432,
      "dst_port": "rhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_up_to_mul",
      "src_port": "out",
      "src_stage": "stage_05_mlp_up_proj",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 4864
      },
      "transfer_count_bytes": 155648,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 2432,
      "dst_port": "in",
      "dst_stage": "stage_07_mlp_down_proj",
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_activation_mul",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 4864
      },
      "transfer_count_bytes": 155648,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "main",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_07_mlp_down_proj",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "in",
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_08_residual_add_2.to.block_output.output",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_08_residual_add_2",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    }
  ],
  "flow_control": {
    "deadlock_rule": "directed graph must be acyclic, or every cycle must include a bounded buffer and a checker-backed ready path proof",
    "join_policy": "all_required_inputs_valid_before_fire",
    "protocol": "ready_valid",
    "split_policy": "source beat is duplicated into all branch FIFOs atomically; branch dequeue observes downstream ready independently"
  },
  "memory_schedule": {
    "board_axi": {
      "addr_width_bits": 37,
      "alignment_bytes": 64,
      "calibration_done_signal": "c0_init_calib_complete",
      "core_side_interface_name": "c0_ddr4_s_axi_*",
      "data_bytes": 64,
      "data_width_bits": 512,
      "ddr_channels": 1,
      "ddr_type": "DDR4",
      "id_width_bits": 4,
      "protocol": "AXI",
      "source": "constraint.memory.board.memory_system",
      "wstrb_width_bits": 64
    },
    "num_layers": 24,
    "policy": "double_buffered_weights_and_streamed_activations",
    "required_regions": [
      {
        "alignment_bytes": 64,
        "name": "input_tokens",
        "role": "activation_input",
        "size_bytes": 57344,
        "size_bytes_formula": "seq_len * hidden_size * block_input_bits / 8"
      },
      {
        "alignment_bytes": 64,
        "name": "output_tokens",
        "role": "activation_output",
        "size_bytes": 57344,
        "size_bytes_formula": "seq_len * hidden_size * block_output_bits / 8"
      },
      {
        "alignment_bytes": 64,
        "name": "activation_ping",
        "role": "activation_buffer",
        "size_bytes": 155648,
        "size_bytes_formula": "max(seq_len * hidden_size * block_bits, seq_len * intermediate_size * elem_bits) / 8"
      },
      {
        "alignment_bytes": 64,
        "name": "activation_pong",
        "role": "activation_buffer",
        "size_bytes": 155648,
        "size_bytes_formula": "same as activation_ping"
      },
      {
        "alignment_bytes": 64,
        "name": "weight_buffer_a",
        "role": "weight_buffer",
        "size_bytes": 29826048,
        "size_bytes_formula": "per_layer(qkv + out_proj + gate + up + down + norms)"
      },
      {
        "alignment_bytes": 64,
        "name": "weight_buffer_b",
        "role": "weight_buffer",
        "size_bytes": 29826048,
        "size_bytes_formula": "same as weight_buffer_a"
      }
    ],
    "runtime_config_requirements": {
      "c2h_device_template": "/dev/xdma1_c2h_0",
      "c2h_read_targets": [
        {
          "base": "0x3000000000",
          "name": "status_registers",
          "role": "status polling"
        },
        {
          "base": "0x28092f1000",
          "name": "output_tokens",
          "role": "output data reads"
        }
      ],
      "command_sequence": [
        "write input and first-layer weights through XDMA H2C into DDR/control regions",
        "write start/control register",
        "prefetch next-layer weights into inactive weight buffer while active layer computes",
        "poll status register through XDMA C2H until done/status changes",
        "read output header/data from output DDR region"
      ],
      "control_protocol": "xdma_raw_register_and_ddr",
      "device_template_source": "constraint.runtime.board.control_protocol + constraint.runtime.board.xdma_id_default",
      "h2c_device_template": "/dev/xdma1_h2c_0",
      "h2c_write_targets": [
        {
          "base": "0x3000000000",
          "name": "control_registers",
          "role": "start/config writes"
        },
        {
          "base": "0x2800000000",
          "name": "ddr_input_and_weights",
          "role": "input activations and weight image writes"
        }
      ],
      "xdma_id_default": 1
    },
    "sequence_semantics": {
      "runtime_cfg_rule": "runtime sequence length must be <= target_max_seq_len; transfer counts derive from the configured sequence length",
      "target_seq_len_role": "compile-time maximum and default fixed tile bound for generated artifacts"
    },
    "target_seq_len": 16
  },
  "model_type": "qwen2",
  "numeric_stream_policy": {
    "accumulator_bits": 32,
    "activation_bits": 16,
    "policy_id": "current_run_numeric_policy.md",
    "rounding": "nearest_even",
    "saturation": false,
    "scale_bits": 16,
    "source": "constraint.numeric.policy.default_rules",
    "weight_bits": 16
  },
  "pipeline_style": "operator_stream_pipeline",
  "schema_version": "spatialaccagent.pipeline_plan.v0",
  "stage": "pipeline_planning",
  "stage_gate_policy": {
    "current_stage_acceptance": [
      "operator order, edge graph, stream order, tensor shape, element width, branch/join, buffer, liveness, attention, template, memory/runtime handoff contracts must be checker-backed",
      "symbolic_first_order latency is only planning metadata and must not be used as throughput, timing, or hardware pass evidence",
      "stream_edges must mirror data_edges including block_input, residual-skip, and block_output boundary edges",
      "buffer implementations must be concrete bounded ready/valid FIFOs; ping-pong buffers are reserved for memory layout artifacts"
    ],
    "later_stage_obligations": [
      "Stage 4 binds final per-template parameters from this contract",
      "Stage 5 assigns concrete memory base addresses and generates/elaborates template-bound Chisel",
      "Stage 6+ supplies real VCS/Verilator/Vivado/board evidence; Stage 3 must not claim hardware pass"
    ],
    "risk_classification_rule": "If checker_results pass, do not list those resolved current-stage items as risks. Put later-stage obligations in proposed_actions unless a current Stage 3 checker failed."
  },
  "stages": [
    {
      "index": 0,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 1792,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 896
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 32,
        "internal_elem_bits": 32,
        "output_bits": 16
      },
      "op": "rms_norm_1",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "source": "Norm.scala",
      "stage_id": "stage_00_rms_norm_1",
      "template_id": "norm"
    },
    {
      "index": 1,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 30464,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 896
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 16,
        "internal_elem_bits": 16,
        "output_bits": 32
      },
      "op": "self_attention",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "source": "Attention.scala",
      "stage_id": "stage_01_self_attention",
      "template_id": "attention"
    },
    {
      "index": 2,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 1792,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 896
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 32,
        "internal_elem_bits": 32,
        "output_bits": 32
      },
      "op": "residual_add_1",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "source": "Residual.scala",
      "stage_id": "stage_02_residual_add_1",
      "template_id": "residual"
    },
    {
      "index": 3,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 1792,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 896
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 32,
        "internal_elem_bits": 32,
        "output_bits": 16
      },
      "op": "rms_norm_2",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "source": "Norm.scala",
      "stage_id": "stage_03_rms_norm_2",
      "template_id": "norm"
    },
    {
      "index": 4,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 8716288,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 4864
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 16,
        "internal_elem_bits": 16,
        "output_bits": 16
      },
      "op": "mlp_gate_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "source": "FFN.scala",
      "stage_id": "stage_04_mlp_gate_proj",
      "template_id": "ffn"
    },
    {
      "index": 5,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 8716288,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 4864
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 16,
        "internal_elem_bits": 16,
        "output_bits": 16
      },
      "op": "mlp_up_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "source": "FFN.scala",
      "stage_id": "stage_05_mlp_up_proj",
      "template_id": "ffn"
    },
    {
      "index": 6,
      "input_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "latency": {
        "cycles": 9728,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 4864
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 16,
        "internal_elem_bits": 16,
        "output_bits": 16
      },
      "op": "activation_mul",
      "output_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "source": "Elementwise.scala",
      "stage_id": "stage_06_activation_mul",
      "template_id": "elementwise"
    },
    {
      "index": 7,
      "input_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "latency": {
        "cycles": 8716288,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 896
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 16,
        "internal_elem_bits": 16,
        "output_bits": 32
      },
      "op": "mlp_down_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "source": "FFN.scala",
      "stage_id": "stage_07_mlp_down_proj",
      "template_id": "ffn"
    },
    {
      "index": 8,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "latency": {
        "cycles": 1792,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 896,
          "intermediate_size": 4864,
          "lanes": 8,
          "seq_len": 16,
          "stream_width": 896
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 32,
        "internal_elem_bits": 32,
        "output_bits": 32
      },
      "op": "residual_add_2",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "source": "Residual.scala",
      "stage_id": "stage_08_residual_add_2",
      "template_id": "residual"
    }
  ],
  "status": "ready",
  "stream_edges": [
    {
      "axi_beats": 896,
      "dst_port": "in",
      "dst_stage": "stage_00_rms_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "skip",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 448,
      "dst_port": "in",
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_rms_norm_1",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 28672,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "main",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_01_self_attention",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "in",
      "dst_stage": "stage_03_rms_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "skip",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 448,
      "dst_port": "in",
      "dst_stage": "stage_04_mlp_gate_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_gate_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 28672,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 448,
      "dst_port": "in",
      "dst_stage": "stage_05_mlp_up_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_up_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 28672,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 2432,
      "dst_port": "lhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_gate_to_mul",
      "src_port": "out",
      "src_stage": "stage_04_mlp_gate_proj",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 4864
      },
      "transfer_count_bytes": 155648,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 2432,
      "dst_port": "rhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "mlp_up_to_mul",
      "src_port": "out",
      "src_stage": "stage_05_mlp_up_proj",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 4864
      },
      "transfer_count_bytes": 155648,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 2432,
      "dst_port": "in",
      "dst_stage": "stage_07_mlp_down_proj",
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "element_bits": 16,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_activation_mul",
      "stream_beats_per_axi_beat": 4,
      "tensor": {
        "seq_len": 16,
        "width": 4864
      },
      "transfer_count_bytes": 155648,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "main",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_07_mlp_down_proj",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 896,
      "dst_port": "in",
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_08_residual_add_2.to.block_output.output",
      "element_bits": 32,
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_08_residual_add_2",
      "stream_beats_per_axi_beat": 2,
      "tensor": {
        "seq_len": 16,
        "width": 896
      },
      "transfer_count_bytes": 57344,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
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
      "stages"
    ],
    "constraints": [
      "constraint.pipeline.structure",
      "constraint.model.decoder",
      "constraint.template.library"
    ],
    "id": "pipeline_planning.pipeline_architect",
    "objective": "Check whether pipeline stages preserve decoder operator order and expose residual, attention, and template boundaries.",
    "parallel_group": 0,
    "role": "pipeline architect",
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
      "mission": "Check whether pipeline stages preserve decoder operator order and expose residual, attention, and template boundaries.",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 4,
        "_type": "list"
      },
      "professional_family": "stage_specialist"
    },
    "role_profile": {
      "capabilities": [
        "audit stage-local artifact",
        "map observations to SACG constraints"
      ],
      "constraint_focus": [],
      "family": "stage_specialist"
    },
    "title": "Review stage decomposition"
  },
  {
    "acceptance_checkers": [
      "addr_map_check",
      "data_order_trace_check",
      "deadlock_watchdog",
      "sacg_static_check",
      "transfer_count_check"
    ],
    "action_type": "cross_layer_rule_review",
    "artifact_focus": [
      "data_order_edges",
      "memory_policy"
    ],
    "constraints": [
      "constraint.stream.order",
      "constraint.beat.pipeline",
      "constraint.liveness.pipeline"
    ],
    "id": "pipeline_planning.data_transfer_engineer",
    "objective": "Check token/tile/lane/transfer-unit order, valid/ready assumptions, and producer-consumer handoff risks.",
    "parallel_group": 0,
    "role": "data transfer engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 5,
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
      "mission": "Check token/tile/lane/transfer-unit order, valid/ready assumptions, and producer-consumer handoff risks.",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "data_memory_runtime"
    },
    "role_profile": {
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
      "family": "data_memory_runtime"
    },
    "title": "Review data order and transfer-unit constraints"
  },
  {
    "acceptance_checkers": [
      "addr_map_check",
      "implementation_package_static",
      "real_tool_evidence_check",
      "sacg_static_check"
    ],
    "action_type": "cross_layer_rule_review",
    "artifact_focus": [
      "memory_policy",
      "stages"
    ],
    "constraints": [
      "constraint.memory.board",
      "constraint.runtime.board"
    ],
    "id": "pipeline_planning.memory_dataflow_engineer",
    "objective": "Check that pipeline planning leaves explicit hooks for weights, activations, DDR layout, runtime config, and later implementation evidence.",
    "parallel_group": 0,
    "role": "memory dataflow engineer",
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
      "mission": "Check that pipeline planning leaves explicit hooks for weights, activations, DDR layout, runtime config, and later imple...<len=139>",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "data_memory_runtime"
    },
    "role_profile": {
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
      "family": "data_memory_runtime"
    },
    "title": "Review memory/runtime dataflow implications"
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
