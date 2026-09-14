<agent>
pipeline_architect_agent
</agent>

<task>
Review the candidate spatial pipeline plan and team decomposition before it is committed into SACG.
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

<candidate_pipeline_plan>
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
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_block_input_to_stage_02_residual_add_1_residual_skip",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_01_self_attention_to_stage_02_residual_add_1_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_03_rms_norm_2_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_08_residual_add_2_residual_skip",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_03_rms_norm_2_to_stage_04_mlp_gate_proj_mlp_gate_branch",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_03_rms_norm_2_to_stage_05_mlp_up_proj_mlp_up_branch",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_04_mlp_gate_proj_to_stage_06_activation_mul_mlp_gate_to_mul",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_05_mlp_up_proj_to_stage_06_activation_mul_mlp_up_to_mul",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_07_mlp_down_proj_to_stage_08_residual_add_2_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_08_residual_add_2_to_block_output_output",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
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
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_00_rms_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "skip",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "block_input",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_rms_norm_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 448,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 28672,
        "transfer_count_bytes": 28672,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "main",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_01_self_attention",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_03_rms_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "skip",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_04_mlp_gate_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "flow_control": "ready_valid",
      "kind": "mlp_gate_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 448,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 28672,
        "transfer_count_bytes": 28672,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_05_mlp_up_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "flow_control": "ready_valid",
      "kind": "mlp_up_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 448,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 28672,
        "transfer_count_bytes": 28672,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "lhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "flow_control": "ready_valid",
      "kind": "mlp_gate_to_mul",
      "src_port": "out",
      "src_stage": "stage_04_mlp_gate_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 2432,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 4864
        },
        "transfer_count_aligned_bytes": 155648,
        "transfer_count_bytes": 155648,
        "transfer_count_elements": 77824,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "rhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "flow_control": "ready_valid",
      "kind": "mlp_up_to_mul",
      "src_port": "out",
      "src_stage": "stage_05_mlp_up_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 2432,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 4864
        },
        "transfer_count_aligned_bytes": 155648,
        "transfer_count_bytes": 155648,
        "transfer_count_elements": 77824,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_07_mlp_down_proj",
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_activation_mul",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 2432,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 4864
        },
        "transfer_count_aligned_bytes": 155648,
        "transfer_count_bytes": 155648,
        "transfer_count_elements": 77824,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "main",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_07_mlp_down_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_08_residual_add_2.to.block_output.output",
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_08_residual_add_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    }
  ],
  "design_space_refs": [
    "axi_ddr",
    "bank_counts",
    "clocking",
    "fifo_depths",
    "fixed_model_binding",
    "implementation_sweep",
    "lanes",
    "numeric_widths",
    "tile_sizes"
  ],
  "flow_control": {
    "deadlock_rule": "directed graph must be acyclic, or every cycle must include a bounded buffer and a checker-backed ready path proof",
    "join_policy": "all_required_inputs_valid_before_fire",
    "protocol": "ready_valid",
    "split_policy": "source beat is duplicated into all branch FIFOs atomically; branch dequeue observes downstream ready independently"
  },
  "memory_policy": {
    "activation_policy": "stream_between_stages",
    "board_memory_constraints": [
      "constraint.memory.board",
      "constraint.runtime.board"
    ],
    "weight_policy": "template_bound"
  },
  "memory_schedule": {
    "activation_buffers": [
      "activation_ping",
      "activation_pong"
    ],
    "activation_flow": "input DDR read -> block pipeline -> output DDR write",
    "axi_ddr_requirements": [
      "preserve board-provided data width and alignment",
      "all read/write transfer counts must be derived from tensor shape and element width",
      "host/runtime commands must use the board profile from Stage 0",
      "exact base addresses are assigned by Stage 5 memory_layout and must remain aligned to board_axi.alignment_bytes"
    ],
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
    "board_memory_refs": {
      "memory_system": {
        "address_map": {
          "control_registers": "0x3000000000",
          "ddr_base": "0x2800000000",
          "output_abs": "0x28092f1000"
        },
        "alignment_requirement_bytes": null,
        "axi_addr_width_bits": 37,
        "axi_clock": "c0_ddr4_s_axi_clk",
        "axi_clock_frequency_hz": null,
        "axi_data_bytes": 64,
        "axi_data_width_bits": 512,
        "axi_id_width_bits": 4,
        "axi_protocol": "AXI",
        "axi_protocol_version": null,
        "axi_reset": "c0_ddr4_s_axi_rst_n",
        "axi_reset_polarity": null,
        "axi_wstrb_width_bits": 64,
        "board_axi_prefix": "c0_ddr4_s_axi",
        "burst_length_policy": null,
        "calibration_done_signal": "c0_init_calib_complete",
        "core_side_interface_name": "c0_ddr4_s_axi_*",
        "ddr_capacity_bytes": null,
        "ddr_channels": 1,
        "ddr_type": "DDR4",
        "ddr_word_width_bits": 512,
        "endianness": null,
        "evidence": [
          {
            "chunk_id": "board:000003",
            "excerpt": "\u5f53\u524d\u6838\u5fc3\u4f7f\u7528\u4e00\u4e2a DDR AXI channel\uff1a`c0_ddr4_s_axi_*`\u3002... `ddr_channels`: 1",
            "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
          },
          {
            "chunk_id": "board:000003",
            "excerpt": "\u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002* AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002... `ddr_word_width_bits`: 512",
            "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
          },
          {
            "chunk_id": "board:000003",
            "excerpt": "AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002",
            "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
          },
          {
            "chunk_id": "board:000003",
            "excerpt": "AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_axi_araddr[36:0]`\u3002",
            "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
          },
          {
            "chunk_id": "board:000003",
            "excerpt": "AXI ID \u5bbd\u5ea6\uff1a4 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awid[3:0]` \u548c `c0_ddr4_s_axi_arid[3:0]`\u3002",
            "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
          },
          {
            "chunk_id": "board:000003",
            "excerpt": "DDR UI / AXI clock\uff1a`c0_ddr4_s_axi_clk`\u3002DDR reset\uff1a`c0_ddr4_s_axi_rst_n`\u3002DDR calibration done\uff1a`c0_init_calib_complete`\u3002",
            "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
          }
        ],
        "real_board_reference_rtl": "verification/rtl/cnn_core.sv"
      },
      "runtime_fields": [
        "board_run_command",
        "control_base_address",
        "control_protocol",
        "ctrl_base",
        "ddr_base",
        "ddr_base_address",
        "ddr_image_default",
        "ddr_image_path_default",
        "device_id_default",
        "evidence",
        "mimic_dir",
        "output_abs",
        "output_address_abs",
        "output_size_bytes",
        "register_map",
        "remote_host",
        "remote_port",
        "runtime_dir",
        "xdma_id_default"
      ]
    },
    "num_layers": 24,
    "per_layer_weight_bytes": 29826048,
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
    "target_seq_len": 16,
    "weight_buffers": [
      "weight_buffer_a",
      "weight_buffer_b"
    ],
    "weight_flow": "while layer N computes, prefetch layer N+1 weights into the inactive weight buffer"
  },
  "model_type": "qwen2",
  "multi_layer_execution": {
    "layer_order": "sequential_layers_with_inter_layer_streaming",
    "num_layers": 24,
    "pipeline_overlap": "next token may enter stage_0 when backpressure allows; do not serialize whole-token full-block execution unless forced by dependencies",
    "weight_prefetch": "double_buffer_next_layer_weights"
  },
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
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-06
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "input_bits": {
          "dtype": "fp32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "output_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 0,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "norm",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "rms_norm_1",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps"
      ],
      "source": "Norm.scala",
      "stage_id": "stage_00_rms_norm_1",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 64
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "num_kv_heads": {
          "source": "constraint.shape.model.num_kv_heads",
          "status": "bound",
          "value": 2
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 14
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "liveness"
      ],
      "index": 1,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "attention",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "self_attention",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "source": "Attention.scala",
      "stage_id": "stage_01_self_attention",
      "template_id": "attention"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 2,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "residual",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "residual_add_1",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "source": "Residual.scala",
      "stage_id": "stage_02_residual_add_1",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-06
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "input_bits": {
          "dtype": "fp32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "output_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 3,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "norm",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "rms_norm_2",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps"
      ],
      "source": "Norm.scala",
      "stage_id": "stage_03_rms_norm_2",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 4864
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "tile_k": {
          "candidate_values": [
            128,
            64
          ],
          "divides": 896,
          "legal_values": [
            128,
            64
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_k_candidates",
          "status": "bound",
          "value": 128
        },
        "tile_m": {
          "candidate_values": [
            16,
            1,
            2,
            4,
            8
          ],
          "divides": 16,
          "legal_values": [
            16,
            1,
            2,
            4,
            8
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_m_candidates",
          "status": "bound",
          "value": 16
        },
        "tile_n": {
          "candidate_values": [
            128,
            64,
            256
          ],
          "divides": 4864,
          "legal_values": [
            128,
            64,
            256
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_n_candidates",
          "status": "bound",
          "value": 128
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "index": 4,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "mlp",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "mlp_gate_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "source": "FFN.scala",
      "stage_id": "stage_04_mlp_gate_proj",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 4864
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "tile_k": {
          "candidate_values": [
            128,
            64
          ],
          "divides": 896,
          "legal_values": [
            128,
            64
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_k_candidates",
          "status": "bound",
          "value": 128
        },
        "tile_m": {
          "candidate_values": [
            16,
            1,
            2,
            4,
            8
          ],
          "divides": 16,
          "legal_values": [
            16,
            1,
            2,
            4,
            8
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_m_candidates",
          "status": "bound",
          "value": 16
        },
        "tile_n": {
          "candidate_values": [
            128,
            64,
            256
          ],
          "divides": 4864,
          "legal_values": [
            128,
            64,
            256
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_n_candidates",
          "status": "bound",
          "value": 128
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "index": 5,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "mlp",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "mlp_up_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "source": "FFN.scala",
      "stage_id": "stage_05_mlp_up_proj",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 4864
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 6,
      "input_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "kind": "activation",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "activation_mul",
      "output_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "source": "Elementwise.scala",
      "stage_id": "stage_06_activation_mul",
      "template_id": "elementwise"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 4864
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "tile_k": {
          "candidate_values": [
            128,
            64
          ],
          "divides": 4864,
          "legal_values": [
            128,
            64
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down.tile_k_candidates",
          "status": "bound",
          "value": 128
        },
        "tile_m": {
          "candidate_values": [
            16,
            1,
            2,
            4,
            8
          ],
          "divides": 16,
          "legal_values": [
            16,
            1,
            2,
            4,
            8
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down.tile_m_candidates",
          "status": "bound",
          "value": 16
        },
        "tile_n": {
          "candidate_values": [
            128,
            64
          ],
          "divides": 896,
          "legal_values": [
            128,
            64
          ],
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down.tile_n_candidates",
          "status": "bound",
          "value": 128
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "index": 7,
      "input_shape": {
        "seq_len": 16,
        "width": 4864
      },
      "kind": "mlp",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "mlp_down_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "source": "FFN.scala",
      "stage_id": "stage_07_mlp_down_proj",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 896
        },
        "lanes": {
          "candidate_values": [
            8,
            16,
            32
          ],
          "legal_values": [
            8,
            16,
            32
          ],
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 8,
      "input_shape": {
        "seq_len": 16,
        "width": 896
      },
      "kind": "residual",
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
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 16
      },
      "op": "residual_add_2",
      "output_shape": {
        "seq_len": 16,
        "width": 896
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "source": "Residual.scala",
      "stage_id": "stage_08_residual_add_2",
      "template_id": "residual"
    }
  ],
  "status": "ready",
  "stream_edges": [
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_00_rms_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_rms_norm_1.input",
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "skip",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "block_input",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_rms_norm_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 448,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 28672,
        "transfer_count_bytes": 28672,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "main",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_01_self_attention",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_03_rms_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "skip",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_04_mlp_gate_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
      "flow_control": "ready_valid",
      "kind": "mlp_gate_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 448,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 28672,
        "transfer_count_bytes": 28672,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_05_mlp_up_proj",
      "edge_id": "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
      "flow_control": "ready_valid",
      "kind": "mlp_up_branch",
      "src_port": "out",
      "src_stage": "stage_03_rms_norm_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 448,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 28672,
        "transfer_count_bytes": 28672,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "lhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
      "flow_control": "ready_valid",
      "kind": "mlp_gate_to_mul",
      "src_port": "out",
      "src_stage": "stage_04_mlp_gate_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 2432,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 4864
        },
        "transfer_count_aligned_bytes": 155648,
        "transfer_count_bytes": 155648,
        "transfer_count_elements": 77824,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "rhs",
      "dst_stage": "stage_06_activation_mul",
      "edge_id": "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
      "flow_control": "ready_valid",
      "kind": "mlp_up_to_mul",
      "src_port": "out",
      "src_stage": "stage_05_mlp_up_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 2432,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 4864
        },
        "transfer_count_aligned_bytes": 155648,
        "transfer_count_bytes": 155648,
        "transfer_count_elements": 77824,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_07_mlp_down_proj",
      "edge_id": "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_activation_mul",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 2432,
        "axi_data_width_bits": 512,
        "dst_input_bits": 16,
        "element_bits": 16,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 16,
        "stream_beat_bits": 128,
        "stream_beats_per_axi_beat": 4,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 4864
        },
        "transfer_count_aligned_bytes": 155648,
        "transfer_count_bytes": 155648,
        "transfer_count_elements": 77824,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "main",
      "dst_stage": "stage_08_residual_add_2",
      "edge_id": "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_07_mlp_down_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    },
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_08_residual_add_2.to.block_output.output",
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_08_residual_add_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 896,
        "axi_data_width_bits": 512,
        "dst_input_bits": 32,
        "element_bits": 32,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 32,
        "stream_beat_bits": 256,
        "stream_beats_per_axi_beat": 2,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 896
        },
        "transfer_count_aligned_bytes": 57344,
        "transfer_count_bytes": 57344,
        "transfer_count_elements": 14336,
        "valid_byte_policy": "full_beats_only"
      },
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ]
    }
  ]
}
</candidate_pipeline_plan>

<stage_gate_policy>
{
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
}
</stage_gate_policy>

<checker_results>
[
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
]
</checker_results>

<checker_summary>
{
  "errors": [],
  "failed": 0,
  "passed": 10,
  "warnings": []
}
</checker_summary>

<pipeline_static_checks>
{
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
  "schema_version": "spatialaccagent.pipeline_static_checks.v0",
  "stage": "pipeline_planning",
  "status": "pass",
  "summary": {
    "errors": [],
    "failed": 0,
    "passed": 10,
    "warnings": []
  }
}
</pipeline_static_checks>

<design_team>
{
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/team_aggregate.json",
  "approval_required_for": [
    "Accepting or changing final DDR/MMIO physical base addresses, region offsets, or non-overlap memory layout.",
    "Any architecture or pipeline-topology change beyond the accepted 9-stage operator_stream_pipeline plan.",
    "Any architecture, pipeline, numeric policy, or major template change proposed as a memory/runtime repair.",
    "Any attempted waiver of required specialist evidence, checker evidence, or Stage 3 prohibition on hardware/timing/bitstream/board-pass claims.",
    "Any change to 16-bit/32-bit data-edge element_bits that affects AXI packing, transfer counts, residual joins, or memory/runtime contracts.",
    "Any change to GQA head mapping, including num_q_heads, num_kv_heads, gqa_group_size, head_dim, causal flag, RoPE policy, or seq_len_bound.",
    "Any change to Qwen2 decoder operator order or stage boundary grouping.",
    "Any change to activation_bits, weight_bits, scale_bits, accumulator_bits, rounding mode, or saturation policy.",
    "Any change to residual skip topology, MLP branch/join topology, pairing_key semantics, or transfer_order semantics.",
    "Any change to tensor width contracts for hidden_size=896, intermediate_size=4864, or seq_len=16.",
    "Any downstream change to operator order, edge topology, transfer_order, AXI full-beat policy, FIFO implementation template, FIFO depth outside the accepted bounded set, memory base address assignment, numeric width policy, or introduction of unsupported flow-control primitives.",
    "Any major template change, free-form RTL generation, or buffer-depth policy change beyond trusted_queue_template bounded ready/valid FIFOs with allowed depths 32 and 64.",
    "Any memory layout, base-address assignment, or runtime ABI change beyond the current planning handoff.",
    "Any numeric policy change from activation_bits=16, weight_bits=16, scale_bits=16, accumulator_bits=32, nearest_even rounding, and saturation=false.",
    "Any numeric policy or memory-layout change, which is outside this role and requires the appropriate specialist approval.",
    "Any pipeline repartitioning or change to stage input/output/internal bit widths.",
    "Any repair that changes attention GQA parameters, FFN dimensions, hidden_size, intermediate_size, target sequence bound, or lane count rather than merely binding already-approved parameters.",
    "Any replacement of a trusted template, addition of a new template, or introduction of free-form RTL generation.",
    "Any replacement of trusted template bindings with new templates or free-form RTL obligations.",
    "Changing AXI data width, address width, alignment, wstrb width, DDR channel/interface assumptions, or calibration-gating assumptions.",
    "Changing activation ping/pong policy, weight buffer count/size policy, or adding external KV-cache DDR regions.",
    "Changing boundary element widths or host packing rules for input_tokens, output_tokens, or intermediate activation transfers.",
    "Changing target_seq_len, legal runtime sequence-length policy, valid-byte policy, or host transfer-count semantics.",
    "Overriding XDMA device templates, xdma_id_default, or board target selection when discovery evidence is ambiguous."
  ],
  "completed_subtasks": 5,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "transfer_count_check",
        "tool_protocol_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "memory_runtime_plan_review",
      "consumes": [
        "candidate_stage_artifact.memory_schedule",
        "candidate_stage_artifact.data_edges",
        "candidate_stage_artifact.stream_edges",
        "candidate_stage_artifact.checker_results",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols"
      ],
      "id": "pipeline_planning.emit_memory_runtime_handoff_audit",
      "on_failure": "Route the failed region, sequence, or tool-protocol finding to pipeline_planning.memory_runtime_repair; do not allow evidence_gate_auditor to promote the plan as memory/runtime complete.",
      "produces": [
        "memory_runtime_handoff_audit_report.json",
        "ddr_region_size_alignment_matrix.json",
        "runtime_sequence_contract_findings.json",
        "later_stage_evidence_obligations.json"
      ],
      "rationale": "Create the expected handoff artifacts and bind the visible planning contract to registered memory/runtime, transfer-count, tool-protocol, and real-evidence-boundary checks without claiming implementation or deployment pass.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "memory_runtime_plan_check",
        "transfer_count_check",
        "tool_protocol_check",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "boundary_contract_check"
      ],
      "action_type": "memory_runtime_contract_annotation",
      "consumes": [
        "candidate_stage_artifact.memory_schedule.runtime_config_requirements",
        "candidate_stage_artifact.memory_schedule.required_regions",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols"
      ],
      "id": "pipeline_planning.clarify_stage3_address_semantics",
      "on_failure": "Hold the current stage at the evidence gate; if final addresses are intended, require memory-layout approval and an accepted addr_map_check result before code generation consumes them.",
      "produces": [
        "candidate_stage_artifact.memory_schedule.address_semantics_annotation",
        "memory_runtime_handoff_audit_report.json.address_semantics_findings"
      ],
      "rationale": "The artifact contains concrete-looking hex bases while the stage policy says final base assignment belongs to Stage 5. Annotate or repair the contract so these bases are treated as board/runtime target hints unless an accepted memory-layout artifact is cited.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "memory_runtime_repair",
        "memory_runtime_plan_check",
        "addr_map_check",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "addr_map_check",
        "boundary_contract_check",
        "tool_protocol_check",
        "codegen_contract_check"
      ],
      "action_type": "addr_map_generation_and_check",
      "consumes": [
        "memory_runtime_handoff_audit_report.json",
        "ddr_region_size_alignment_matrix.json",
        "candidate_stage_artifact.memory_schedule",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols"
      ],
      "id": "stage5.generate_checked_memory_layout_from_handoff",
      "on_failure": "Return a bounded memory_runtime_repair finding or memory-layout approval request; do not generate code with unresolved, overlapping, or unapproved physical regions.",
      "produces": [
        "artifact.stage5.accepted_memory_layout",
        "addr_map_check_report.json",
        "runtime_region_manifest.json",
        "generated/chisel/runtime/runtime_config.json"
      ],
      "rationale": "Translate the logical required_regions into concrete aligned, non-overlapping DDR/MMIO region assignments for code generation and runtime, using the Stage 3 handoff only as a contract source, not as final placement evidence.",
      "requires_approval": true,
      "stage": "memory_layout_codegen",
      "tool_roles": [
        "addr_map_check",
        "boundary_contract_generate",
        "tool_protocol_check",
        "codegen_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "transfer_count_check",
        "boundary_contract_check",
        "tool_protocol_check",
        "codegen_contract_check"
      ],
      "action_type": "runtime_sequence_contract_generation",
      "consumes": [
        "runtime_sequence_contract_findings.json",
        "candidate_stage_artifact.data_edges",
        "candidate_stage_artifact.memory_schedule.sequence_semantics",
        "generated/chisel/runtime/runtime_config.json"
      ],
      "id": "stage5.bind_runtime_sequence_contract",
      "on_failure": "Block runtime packaging and codegen consumption; route the violated sequence or packing rule to memory_runtime_repair instead of inferring transfer counts manually in host code.",
      "produces": [
        "runtime_sequence_contract.json",
        "host_transfer_manifest.json",
        "boundary_contract.runtime_abi.json"
      ],
      "rationale": "Make target_seq_len, legal runtime sequence lengths, per-edge transfer counts, full-beat policy, and boundary element widths explicit for host XDMA and generated-kernel interaction.",
      "requires_approval": false,
      "stage": "memory_layout_codegen",
      "tool_roles": [
        "transfer_count_check",
        "boundary_contract_generate",
        "tool_protocol_check",
        "codegen_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_real_weight_artifacts",
        "artifact_hash_check",
        "transfer_count_check",
        "addr_map_check"
      ],
      "action_type": "weight_buffer_manifest_generation",
      "consumes": [
        "candidate_stage_artifact.memory_schedule.required_regions",
        "candidate_stage_artifact.memory_schedule.num_layers",
        "candidate_stage_artifact.stages",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.stage5.accepted_memory_layout"
      ],
      "id": "stage5.generate_weight_buffer_manifest_for_double_buffering",
      "on_failure": "Keep codegen/runtime packaging blocked and return a bounded manifest or layout repair; do not resize weight buffers or alter numeric policy without approval.",
      "produces": [
        "verification/case_real_weights/packed_weight_manifest.json",
        "runtime_weight_prefetch_schedule.json",
        "weight_buffer_offset_alignment_report.json"
      ],
      "rationale": "The planning artifact provides per-layer weight buffer sizes but not per-tensor offsets, hashes, padding, or prefetch order. Generate a checked manifest so the double-buffered 24-layer runtime policy is executable.",
      "requires_approval": false,
      "stage": "memory_layout_codegen",
      "tool_roles": [
        "case_weight_manifest_generate",
        "artifact_hash_check",
        "transfer_count_check",
        "addr_map_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_axi_ddr_interface",
        "real_tool.case_axi_protocol_check",
        "real_tool.case_ddr_image_roundtrip",
        "real_tool.case_runtime_abi_check",
        "real_tool.board_runtime",
        "required_real_tool_evidence_check"
      ],
      "action_type": "real_tool_evidence_sequence",
      "consumes": [
        "artifact.stage5.accepted_memory_layout",
        "generated/chisel/runtime/runtime_config.json",
        "runtime_sequence_contract.json",
        "verification/case_real_weights/packed_weight_manifest.json",
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage9.bitstream_or_app_shell_integration_contract"
      ],
      "id": "verification_board.collect_memory_runtime_real_tool_evidence",
      "on_failure": "Localize the earliest liveness, value, order, or protocol boundary and follow the three-layer repair loop: operator/leaf modules first, then connected single-transformer-layer kernel, then board-accurate AXI/DDR wrapper. Do not promote or skip to a higher layer after a failed lower layer.",
      "produces": [
        "verification/case_diagnostics/axi_ddr_interface.json",
        "verification/case_diagnostics/axi_protocol.json",
        "verification/case_diagnostics/ddr_image_roundtrip.json",
        "backend_board/case_diagnostics/runtime_abi_check.json",
        "backend_board/case_diagnostics/board_runtime.json"
      ],
      "rationale": "Planning artifacts deliberately do not prove hardware correctness. After codegen and static gates pass, collect real evidence for AXI/DDR, runtime ABI, and board execution before any deployment claim.",
      "requires_approval": false,
      "stage": "verification_backend_board",
      "tool_roles": [
        "case_axi_ddr_interface",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_runtime_abi_check",
        "board_runtime",
        "real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "model_config_check",
        "stream_plan_check",
        "template_binding_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_stage_artifact.stages",
        "candidate_stage_artifact.attention_contract",
        "candidate_stage_artifact.branch_join_contracts",
        "candidate_stage_artifact.stream_edges",
        "candidate_stage_artifact.data_edges",
        "candidate_stage_artifact.checker_results",
        "artifact.input.model_config",
        "artifact.stage2.template_selection",
        "artifact.input.template_library"
      ],
      "id": "pipeline_planning.model_shape_sacg_acceptance_pack",
      "on_failure": "Do not promote to aggregate evidence gate. Map each violation to constraint.model.decoder, constraint.shape.model, constraint.template.library, or constraint.cross_layer.input_consistency, then invoke bounded pipeline repair without editing golden outputs or introducing free-form RTL.",
      "produces": [
        "model_pipeline_audit_report.json",
        "operator_shape_attention_findings.json",
        "sacg_constraint_coverage_delta.json"
      ],
      "rationale": "Package and verify the model-shape audit evidence for decoder order, residual and branch semantics, GQA values, tensor shapes, stream order, and no free-form RTL using the named acceptance checkers before evidence-gate promotion.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "sacg_validate",
        "sacg_static_check",
        "model_config_check",
        "stream_plan_check",
        "template_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "template_coverage_check",
        "model_config_check",
        "template_binding_static_check"
      ],
      "action_type": "parameter_binding_handoff",
      "consumes": [
        "model_pipeline_audit_report.json",
        "operator_shape_attention_findings.json",
        "candidate_stage_artifact.stages",
        "candidate_stage_artifact.attention_contract",
        "candidate_stage_artifact.branch_join_contracts",
        "candidate_stage_artifact.stream_edges",
        "artifact.input.model_config",
        "artifact.stage2.template_selection",
        "artifact.input.template_metadata"
      ],
      "id": "parameter_binding.freeze_qwen2_model_shape_contract",
      "on_failure": "Return to pipeline_planning bounded repair or template-selection review with the violated SACG constraint; do not generate code and do not substitute a free-form RTL implementation.",
      "produces": [
        "artifact.stage4.parameter_binding_contract",
        "artifact.stage4.operator_shape_attention_binding_manifest",
        "artifact.stage4.template_parameter_delta"
      ],
      "rationale": "Stage 4 must bind the reviewed plan into template parameters while preserving the GQA head mapping, seq_len bound, residual paths, branch/join keys, stream order, and tensor widths; this action is static binding and does not claim RTL or hardware correctness.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "parameter_binding_static_check",
        "template_coverage_check",
        "model_config_check",
        "template_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "sacg_static_check",
        "model_config_check",
        "stream_plan_check",
        "template_binding_static_check"
      ],
      "action_type": "bounded_repair",
      "consumes": [
        "model_pipeline_audit_report.json",
        "operator_shape_attention_findings.json",
        "sacg_constraint_coverage_delta.json",
        "candidate_stage_artifact",
        "artifact.input.model_config",
        "artifact.stage2.template_selection"
      ],
      "id": "pipeline_planning.bounded_repair_on_model_shape_checker_failure",
      "on_failure": "Open a stage_retry_request or stage_backtrack_request and block promotion. Do not bypass checkers, change golden outputs, loosen tolerance, or introduce unapproved RTL/template changes.",
      "produces": [
        "candidate_stage_artifact.repaired_pipeline_plan",
        "repair_boundary_report.json",
        "updated_sacg_constraint_coverage_delta.json"
      ],
      "rationale": "If the evidence-gate or Stage 4 static binding detects a semantic, shape, attention, residual-path, or template-boundary violation, repair must stay inside the trusted operator-stream pipeline contract and rerun the named checkers.",
      "requires_approval": true,
      "stage": "pipeline_planning",
      "tool_roles": [
        "pipeline_repair",
        "repair_boundary_check",
        "sacg_validate",
        "stream_plan_check",
        "template_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "template_binding_static_check"
      ],
      "action_type": "template_binding_review",
      "consumes": [
        "candidate_stage_artifact.stages",
        "candidate_stage_artifact.numeric_stream_policy",
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.data_edges",
        "candidate_stage_artifact.attention_contract",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.stage2.template_selection"
      ],
      "id": "pipeline_planning.run_numeric_template_acceptance_audit",
      "on_failure": "Block evidence-gate promotion, attach failed checker evidence to the SACG record, and route only the failed template/numeric slices to bounded_template_repair; do not loosen numeric tolerance or introduce free-form RTL.",
      "produces": [
        "numeric_template_audit_report.json",
        "stage_template_numeric_matrix.json",
        "parameter_binding_readiness_notes.json"
      ],
      "rationale": "Complete the subtask acceptance evidence set by checking the visible stage/template matrix against the trusted template library, Stage 2 template selection, numeric policy, and parameter-binding requirements.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "template_binding_static_check"
      ],
      "action_type": "bounded_template_repair",
      "consumes": [
        "numeric_template_audit_report.json",
        "stage_template_numeric_matrix.json",
        "parameter_binding_readiness_notes.json",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.numeric_policy",
        "artifact.input.design_space",
        "candidate_stage_artifact.stages",
        "candidate_stage_artifact.numeric_stream_policy"
      ],
      "id": "pipeline_planning.bounded_template_numeric_repair_on_failed_audit",
      "on_failure": "Create a stage retry request and trust barrier for the unresolved numeric/template slice; do not promote to Stage 4 or Stage 5 until the failing checker is rerun and passes.",
      "produces": [
        "candidate_stage_artifact.refined_stages",
        "candidate_stage_artifact.refined_numeric_stream_policy",
        "numeric_template_audit_report.retry.json",
        "stage_template_numeric_matrix.retry.json"
      ],
      "rationale": "If the audit finds an untrusted template, incompatible width, missing accumulator policy, or unbound numeric parameter, repair only within trusted template and numeric-policy boundaries.",
      "requires_approval": true,
      "stage": "pipeline_planning",
      "tool_roles": [
        "bounded_template_repair",
        "repair_boundary_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "numeric_policy_check",
        "template_coverage_check",
        "code_generation_manifest_static_check",
        "codegen_contract_check",
        "sacg_reference_check"
      ],
      "action_type": "parameter_binding_handoff",
      "consumes": [
        "stage_template_numeric_matrix.json",
        "parameter_binding_readiness_notes.json",
        "candidate_stage_artifact.stages",
        "candidate_stage_artifact.attention_contract",
        "candidate_stage_artifact.numeric_stream_policy",
        "artifact.input.template_metadata",
        "artifact.input.design_space"
      ],
      "id": "parameter_binding.prepare_stage4_template_parameters",
      "on_failure": "Return the specific unbound parameter or incompatible template instance to pipeline_planning for bounded_template_repair; do not proceed to code generation with defaults.",
      "produces": [
        "artifact.stage4.parameter_binding_contract",
        "artifact.stage4.codegen_manifest_seed"
      ],
      "rationale": "Turn the accepted numeric/template matrix into explicit Stage 4 template parameters so later template-constrained code generation cannot infer widths, rounding, saturation, or attention/FFN dimensions implicitly.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "codegen_contract_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "stream_plan_check",
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog",
        "boundary_contract_check"
      ],
      "action_type": "cross_layer_rule_review",
      "consumes": [
        "candidate_stage_artifact.stream_edges",
        "candidate_stage_artifact.data_edges",
        "candidate_stage_artifact.flow_control",
        "candidate_stage_artifact.buffer_plan",
        "candidate_stage_artifact.branch_join_contracts",
        "candidate_stage_artifact.checker_results",
        "constraint.stream.order",
        "constraint.beat.pipeline",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "pipeline_planning.emit_stream_liveness_handoff_artifacts",
      "on_failure": "Block evidence-gate promotion and route the specific failing edge, buffer, splitter, or join to bounded pipeline_repair; do not relax transfer counts, reorder streams, or claim hardware pass.",
      "produces": [
        "stream_liveness_audit_report.json",
        "edge_transfer_count_matrix.json",
        "branch_join_buffer_liveness_findings.json"
      ],
      "rationale": "Convert the accepted static stream/liveness review into the expected handoff artifacts for the evidence gate, preserving exact edge mirrors, transfer counts, full-beat policy, branch/join contracts, and FIFO bindings.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "stream_plan_check",
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "template_binding_static_check",
        "boundary_contract_check",
        "stream_plan_check"
      ],
      "action_type": "contract_handoff",
      "consumes": [
        "stream_liveness_audit_report.json",
        "edge_transfer_count_matrix.json",
        "branch_join_buffer_liveness_findings.json",
        "candidate_stage_artifact.stages",
        "artifact.input.template_library",
        "artifact.input.template_metadata"
      ],
      "id": "parameter_binding.lock_ready_valid_stream_contract",
      "on_failure": "Return to bounded pipeline_repair for only the affected edge, FIFO depth, splitter, or join. Require explicit approval before changing architecture, memory layout, numeric policy, or supported template primitives.",
      "produces": [
        "artifact.stage4.stream_fifo_join_parameter_bindings",
        "artifact.stage4.boundary_stream_contract"
      ],
      "rationale": "Ensure the next stage binds the static plan to trusted templates without changing the ready/valid protocol, full-beat AXI assumptions, transfer order, FIFO depths, atomic split behavior, or all-valid join behavior.",
      "requires_approval": false,
      "stage": "parameter_binding",
      "tool_roles": [
        "parameter_binding_static_check",
        "boundary_contract_generate",
        "stream_plan_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "boundary_contract_check",
        "data_order_trace_check",
        "transfer_count_check",
        "deadlock_watchdog"
      ],
      "action_type": "verification_plan_static_handoff",
      "consumes": [
        "stream_liveness_audit_report.json",
        "edge_transfer_count_matrix.json",
        "branch_join_buffer_liveness_findings.json",
        "artifact.stage4.boundary_stream_contract"
      ],
      "id": "verification_planning.require_stream_order_deadlock_evidence",
      "on_failure": "Keep verification planning blocked until the missing order/count/deadlock obligations are restored; do not proceed to real simulation, Vivado, or board runtime without these requirements.",
      "produces": [
        "artifact.stage6.stream_liveness_verification_requirements"
      ],
      "rationale": "Record that later generated RTL must be checked with data-order traces, transfer-count checks, and deadlock watchdogs before any implementation or hardware pass can be claimed.",
      "requires_approval": false,
      "stage": "verification_planning",
      "tool_roles": [
        "verification_plan_static_check",
        "hierarchical_verification_plan_check",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "model_config_check",
        "stream_plan_check",
        "numeric_policy_check",
        "template_coverage_check",
        "memory_runtime_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "human_boundary_check"
      ],
      "action_type": "evidence_completion",
      "consumes": [
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.checker_summary",
        "candidate_stage_artifact.stage_gate_policy",
        "candidate_stage_artifact.stages",
        "candidate_stage_artifact.stream_edges",
        "candidate_stage_artifact.memory_schedule",
        "artifact.stage2.template_selection",
        "state_summary.sacg_memory_truth"
      ],
      "id": "pipeline_planning.complete_specialist_evidence_pack",
      "on_failure": "Keep Stage 3 blocked. Record which report or checker is missing or contradictory, then route only the implicated model, stream, numeric, template, or memory/runtime slice to the bounded repair action.",
      "produces": [
        "model_pipeline_audit_report.json",
        "stream_liveness_audit_report.json",
        "numeric_template_audit_report.json",
        "memory_runtime_handoff_audit_report.json",
        "checker_evidence_ledger.json"
      ],
      "rationale": "The visible candidate checker_results pass, but the role-required specialist audit report artifacts were not supplied; the evidence gate must not assume peer-specialist findings before promotion.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "team_aggregate",
        "model_config_check",
        "stream_plan_check",
        "numeric_policy_check",
        "template_coverage_check",
        "memory_runtime_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_action_audit_check",
        "verification_artifact_contract_check",
        "repair_boundary_check",
        "human_boundary_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "evidence_gate_decision",
      "consumes": [
        "model_pipeline_audit_report.json",
        "stream_liveness_audit_report.json",
        "numeric_template_audit_report.json",
        "memory_runtime_handoff_audit_report.json",
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.stage_gate_policy",
        "state_summary.sacg_memory_truth"
      ],
      "id": "pipeline_planning.publish_gate_decision_after_evidence_pack",
      "on_failure": "Block promotion. If the failure is missing evidence, return to evidence completion; if it is a checker-backed design inconsistency, route to the smallest valid repair boundary and rerun the failed checker before reconsidering promotion.",
      "produces": [
        "pipeline_planning_stage_gate_decision.json",
        "checker_evidence_ledger.json",
        "bounded_repair_or_promotion_decision.json"
      ],
      "rationale": "Promotion is allowed only after the completed evidence pack binds all pass/fail evidence to SACG constraints and verifies that Stage 3 makes no hardware, timing, bitstream, or board-pass claim.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "team_aggregate",
        "verification_action_audit",
        "repair_boundary_check",
        "required_real_tool_evidence_check",
        "human_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "failure_localization_check",
        "causal_repair_context_check",
        "repair_boundary_check",
        "targeted_failed_checker_rerun",
        "stream_plan_check",
        "memory_runtime_plan_check",
        "template_binding_static_check"
      ],
      "action_type": "bounded_repair",
      "consumes": [
        "checker_evidence_ledger.json",
        "pipeline_planning_stage_gate_decision.json",
        "candidate_stage_artifact"
      ],
      "id": "pipeline_planning.bound_repair_on_specialist_or_checker_failure",
      "on_failure": "Escalate only with a specific violated SACG constraint via stage_retry_request or stage_backtrack_request; do not modify golden outputs, loosen tolerances, introduce free-form RTL, or promote to Stage 4.",
      "produces": [
        "refined_pipeline_plan.json",
        "targeted_failed_checker_rerun_report.json",
        "bounded_repair_or_promotion_decision.json"
      ],
      "rationale": "If the completed evidence pack exposes a current Stage 3 failure, repair must be localized to the earliest violated SACG boundary and remain within trusted templates and checker-backed contracts.",
      "requires_approval": true,
      "stage": "pipeline_planning",
      "tool_roles": [
        "failure_slice_localization",
        "causal_repair_context_pack",
        "pipeline_repair",
        "memory_runtime_repair",
        "bounded_template_repair",
        "targeted_failed_checker_rerun"
      ]
    },
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "template_coverage_check",
        "boundary_contract_check",
        "sacg_reference_check"
      ],
      "action_type": "parameter_binding",
      "consumes": [
        "bounded_repair_or_promotion_decision.json",
        "candidate_stage_artifact",
        "artifact.stage2.template_selection",
        "constraint.model.decoder",
        "constraint.shape.model",
        "constraint.numeric.policy",
        "constraint.template.library"
      ],
      "id": "stage4.bind_parameters_after_stage3_promotion",
      "on_failure": "Block code generation and route mismatched parameters to bounded_template_repair or pipeline_repair, then rerun the failed parameter or boundary checker.",
      "produces": [
        "artifact.stage4.parameter_binding_contract",
        "artifact.stage4.bound_template_parameter_manifest"
      ],
      "rationale": "After the Stage 3 gate passes, bind final per-template parameters from the accepted pipeline contract while preserving model shape, numeric policy, stream order, and template boundaries.",
      "requires_approval": false,
      "stage": "Stage 4 parameter binding",
      "tool_roles": [
        "parameter_binding_static_check",
        "template_coverage_check",
        "boundary_contract_generate",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "tool_protocol_check",
        "human_boundary_check"
      ],
      "action_type": "memory_runtime_binding",
      "consumes": [
        "artifact.stage4.parameter_binding_contract",
        "candidate_stage_artifact.memory_schedule",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols"
      ],
      "id": "stage5.bind_memory_runtime_layout_and_abi",
      "on_failure": "Route to memory_runtime_repair with the failing address, transfer-count, or tool-protocol evidence; do not claim board readiness.",
      "produces": [
        "artifact.stage5.memory_layout",
        "generated/chisel/runtime/runtime_config.json"
      ],
      "rationale": "The Stage 3 memory_schedule is a handoff contract; a later stage must assign concrete base addresses and runtime ABI artifacts and recheck transfer counts before implementation or board work.",
      "requires_approval": true,
      "stage": "memory_runtime_handoff",
      "tool_roles": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "tool_protocol_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_plan_static_check",
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check",
        "human_boundary_check"
      ],
      "action_type": "verification_plan",
      "consumes": [
        "artifact.stage4.parameter_binding_contract",
        "artifact.stage5.memory_layout",
        "generated/chisel/runtime/runtime_config.json",
        "candidate_stage_artifact.stage_gate_policy"
      ],
      "id": "stage6.create_hierarchical_verification_plan_no_hardware_claims",
      "on_failure": "Block simulator, Vivado, and board promotion until the verification plan or missing checker capability is repaired; do not skip layers or reinterpret missing verifier capability as hardware correctness.",
      "produces": [
        "artifact.stage6.hierarchical_verification_plan",
        "artifact.stage6.verification_artifact_contract"
      ],
      "rationale": "Real hardware correctness is outside Stage 3. The downstream verification plan must enforce the three-layer loop: operator/leaf modules, connected single-transformer-layer kernel, then board-accurate AXI/DDR wrapped system, with no promotion past a failed layer.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "hierarchical_verification_plan_check",
        "verification_plan_static_check",
        "required_real_tool_evidence_check",
        "human_boundary_check"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 21,
    "max_duration_sec": 631.1046200010023,
    "max_prompt_bytes": 69688,
    "result_count": 5,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 1521.0235076460085,
    "total_prompt_bytes": 347396
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 5,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/sacg_state.json
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
