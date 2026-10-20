<agent>
pipeline_architect_agent
</agent>

<task>
Decide the current Stage-3 promotion using only the supplied candidate, executed deterministic checker records, and completed specialist-review bundle. The listed executable actions are later implementation suggestions, not missing evidence by themselves. If every current checker passes, the bundle has no errors, and no displayed model/numeric/stream contradiction exists, return status='ready' and risks=[]. Do not block Stage 3 for Stage-4 DSE selection, exact wrapper address discovery, output-header allocation, semantic testbench construction, VCS, or Vivado; those belong in proposed_actions. Treat policy_id='unknown' as an identity-label omission when the supplied numeric values agree, not as a numeric-policy mismatch.
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

<candidate_pipeline_plan>
{
  "attention_contract": {
    "attention_kind": "mha",
    "causal": true,
    "gqa_group_size": 1,
    "head_dim": 64,
    "kv_storage_policy": "bounded by target_max_seq_len inside the generated block; external KV-cache materialization requires a later memory-layout artifact",
    "num_kv_heads": 12,
    "num_q_heads": 12,
    "position_encoding": {
      "type": "learned_absolute"
    },
    "position_encoding_scope": {
      "dut_operation": "none",
      "dut_weight_binding": "forbidden",
      "placement": "pre_dut_input_boundary",
      "reference_requirement": "compose learned position contribution before the Transformer-block DUT input boundary"
    },
    "seq_len_bound": 16,
    "stage_boundary": "logical self_attention stage covers QKV projection, causal attention, and output projection; learned absolute positional embeddings are pre-DUT input/reference composition and are excluded from DUT weights and operations"
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
          "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
          "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main"
        ],
        "node": "stage_07_residual_add_2",
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
        "node": "block_input",
        "output_edges": [
          "edge.data.block_input.to.stage_00_layer_norm_1.input",
          "edge.data.block_input.to.stage_02_residual_add_1.residual_skip"
        ],
        "source_accept_rule": "source beat is accepted only when all branch FIFOs can enqueue the same token/tile/lane/word"
      },
      {
        "branch_dequeue_rule": "after duplication each branch observes its own downstream ready",
        "duplicator": "ready_valid_broadcast_with_per_output_fifo",
        "node": "stage_02_residual_add_1",
        "output_edges": [
          "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
          "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip"
        ],
        "source_accept_rule": "source beat is accepted only when all branch FIFOs can enqueue the same token/tile/lane/word"
      }
    ]
  },
  "buffer_plan": [
    {
      "buffer_id": "buffer.edge_data_block_input_to_stage_00_layer_norm_1_input",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
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
      "buffer_id": "buffer.edge_data_stage_00_layer_norm_1_to_stage_01_self_attention_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_01_self_attention_to_stage_02_residual_add_1_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_03_layer_norm_2_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_07_residual_add_2_residual_skip",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_03_layer_norm_2_to_stage_04_mlp_fc_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_04_mlp_fc_to_stage_05_activation_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_05_activation_to_stage_06_mlp_proj_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_06_mlp_proj_to_stage_07_residual_add_2_main",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 64,
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_07_residual_add_2_to_block_output_output",
      "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
      "depth": 32,
      "edge_id": "edge.data.stage_07_residual_add_2.to.block_output.output",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    }
  ],
  "checker_results": [
    {
      "checker": "operator_order_check",
      "errors": [],
      "status": "pass",
      "summary": "operator_order=['layer_norm_1', 'self_attention', 'residual_add_1', 'layer_norm_2', 'mlp_fc', 'activation', 'mlp_proj', 'residual_add_2']",
      "warnings": []
    },
    {
      "checker": "semantic_dataflow_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "adapter_graph_edges=11",
      "warnings": []
    },
    {
      "checker": "stream_data_edge_mirror_check",
      "errors": [],
      "status": "pass",
      "summary": "edges=11",
      "warnings": []
    },
    {
      "checker": "edge_stream_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "checked_edges=11",
      "warnings": []
    },
    {
      "checker": "shape_numeric_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "stages=8, activation_bits=8, accumulator_bits=32",
      "warnings": []
    },
    {
      "checker": "branch_join_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "splits=2, joins=2",
      "warnings": []
    },
    {
      "checker": "buffer_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "buffers=11, allowed_depths=[32, 64]",
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
      "summary": "q=12, kv=12, head_dim=64",
      "warnings": []
    },
    {
      "checker": "template_binding_static_check",
      "errors": [],
      "status": "pass",
      "summary": "stages=8, free_form_rtl_generation=false",
      "warnings": []
    }
  ],
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 11,
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
      "dst_stage": "stage_00_layer_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_layer_norm_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_03_layer_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_04_mlp_fc",
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_03_layer_norm_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_05_activation",
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_04_mlp_fc",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 768,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 3072
        },
        "transfer_count_aligned_bytes": 49152,
        "transfer_count_bytes": 49152,
        "transfer_count_elements": 49152,
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
      "dst_stage": "stage_06_mlp_proj",
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_05_activation",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 768,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 3072
        },
        "transfer_count_aligned_bytes": 49152,
        "transfer_count_bytes": 49152,
        "transfer_count_elements": 49152,
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
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_mlp_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "edge_id": "edge.data.stage_07_residual_add_2.to.block_output.output",
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_07_residual_add_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
    "candidate_universe",
    "constraints"
  ],
  "flow_control": {
    "deadlock_rule": "directed graph must be acyclic, or every cycle must include a bounded buffer and a checker-backed ready path proof",
    "join_policy": "all_required_inputs_valid_before_fire",
    "protocol": "ready_valid",
    "split_policy": "source beat is duplicated into all branch FIFOs atomically; branch dequeue observes downstream ready independently"
  },
  "implementation_contract": {
    "disabled_weight_ports": [],
    "loader_ports": [
      "norm1Weight",
      "qkvWeight",
      "qkvBias",
      "attentionOutWeight",
      "attentionOutBias",
      "norm2Weight",
      "ffnUpWeight",
      "ffnUpBias",
      "ffnDownWeight",
      "ffnDownBias"
    ],
    "params": {
      "bindings": {
        "batchSize": "token_count",
        "computeArrayCols": "compute_array_cols",
        "computeArrayRows": "compute_array_rows",
        "elemBits": "elem_bits",
        "headDim": "head_dim",
        "hiddenSize": "hidden_size",
        "inputBits": "input_bits",
        "intermediateSize": "intermediate_size",
        "lanes": "lanes",
        "maxSeqLen": "max_seq_len",
        "numHeads": "num_q_heads",
        "outputBits": "output_bits"
      },
      "class": "DecoderBlockParams"
    },
    "requires_position_input": false,
    "top_class": "GPT2PreLNBlock"
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
        "axi_addr_width_bits": 37,
        "axi_clock": "c0_ddr4_s_axi_clk",
        "axi_data_bytes": 64,
        "axi_data_width_bits": 512,
        "axi_id_width_bits": 4,
        "axi_reset": "c0_ddr4_s_axi_rst_n",
        "axi_wstrb_width_bits": 64,
        "calibration_done_signal": "c0_init_calib_complete",
        "core_side_interface_name": "c0_ddr4_s_axi_*",
        "ddr_channels": 1,
        "ddr_type": "DDR4",
        "ddr_word_width_bits": 512,
        "real_board_reference_rtl": "verification/rtl/cnn_core.sv"
      },
      "runtime_fields": [
        "board_run_command",
        "c2h_device_template",
        "control_protocol",
        "ctrl_base",
        "ddr_base",
        "ddr_image_default",
        "h2c_device_template",
        "mimic_dir",
        "output_abs",
        "remote_host",
        "xdma_id_default"
      ]
    },
    "num_layers": 12,
    "per_layer_weight_bytes": 3568128,
    "policy": "double_buffered_weights_and_streamed_activations",
    "required_regions": [
      {
        "alignment_bytes": 64,
        "name": "input_tokens",
        "role": "activation_input",
        "size_bytes": 12288,
        "size_bytes_formula": "semantic block-input tensor elements * declared block-input bits / 8"
      },
      {
        "alignment_bytes": 64,
        "name": "output_tokens",
        "role": "activation_output",
        "size_bytes": 12288,
        "size_bytes_formula": "semantic block-output tensor elements * declared block-output bits / 8"
      },
      {
        "alignment_bytes": 64,
        "name": "activation_ping",
        "role": "activation_buffer",
        "size_bytes": 49152,
        "size_bytes_formula": "max(declared semantic stage input/output tensor bytes)"
      },
      {
        "alignment_bytes": 64,
        "name": "activation_pong",
        "role": "activation_buffer",
        "size_bytes": 49152,
        "size_bytes_formula": "same as activation_ping"
      },
      {
        "alignment_bytes": 64,
        "name": "weight_buffer_a",
        "role": "weight_buffer",
        "size_bytes": 3568128,
        "size_bytes_formula": "sum(model-semantic weight_storage_terms)"
      },
      {
        "alignment_bytes": 64,
        "name": "weight_buffer_b",
        "role": "weight_buffer",
        "size_bytes": 3568128,
        "size_bytes_formula": "same as weight_buffer_a"
      }
    ],
    "runtime_config_requirements": {
      "c2h_device_template": "/dev/xdma${XDMA_ID}_c2h_0",
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
      "h2c_device_template": "/dev/xdma${XDMA_ID}_h2c_0",
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
    "weight_flow": "while layer N computes, prefetch layer N+1 weights into the inactive weight buffer",
    "weight_storage_terms": [
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_1_weight",
        "physical_role": "weight",
        "stage": "layer_norm_1"
      },
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_1_bias",
        "physical_role": "weight",
        "stage": "layer_norm_1"
      },
      {
        "bytes": 884736,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 1769472,
        "factors": [
          "hidden_size",
          3,
          "num_q_heads",
          "head_dim"
        ],
        "id": "attn_c_attn_weight",
        "physical_role": "weight_qkv",
        "stage": "self_attention"
      },
      {
        "bytes": 9216,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 2304,
        "factors": [
          3,
          "num_q_heads",
          "head_dim"
        ],
        "id": "attn_c_attn_bias",
        "physical_role": "weight_qkv_bias",
        "stage": "self_attention"
      },
      {
        "bytes": 294912,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 589824,
        "factors": [
          "hidden_size",
          "hidden_size"
        ],
        "id": "attn_c_proj_weight",
        "physical_role": "weight_attn_out",
        "stage": "self_attention"
      },
      {
        "bytes": 3072,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "attn_c_proj_bias",
        "physical_role": "weight_attn_out_bias",
        "stage": "self_attention"
      },
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_2_weight",
        "physical_role": "weight",
        "stage": "layer_norm_2"
      },
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_2_bias",
        "physical_role": "weight",
        "stage": "layer_norm_2"
      },
      {
        "bytes": 1179648,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 2359296,
        "factors": [
          "hidden_size",
          "intermediate_size"
        ],
        "id": "mlp_c_fc_weight",
        "physical_role": "weight_mlp_up",
        "stage": "mlp_fc"
      },
      {
        "bytes": 12288,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 3072,
        "factors": [
          "intermediate_size"
        ],
        "id": "mlp_c_fc_bias",
        "physical_role": "weight_mlp_up_bias",
        "stage": "mlp_fc"
      },
      {
        "bytes": 1179648,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 2359296,
        "factors": [
          "intermediate_size",
          "hidden_size"
        ],
        "id": "mlp_c_proj_weight",
        "physical_role": "weight_mlp_down",
        "stage": "mlp_proj"
      },
      {
        "bytes": 3072,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "mlp_c_proj_bias",
        "physical_role": "weight_mlp_down_bias",
        "stage": "mlp_proj"
      }
    ]
  },
  "model_type": "gpt2",
  "multi_layer_execution": {
    "layer_order": "sequential_layers_with_inter_layer_streaming",
    "num_layers": 12,
    "pipeline_overlap": "next token may enter stage_0 when backpressure allows; do not serialize whole-token full-block execution unless forced by dependencies",
    "weight_prefetch": "double_buffer_next_layer_weights"
  },
  "numeric_stream_policy": {
    "accumulator_bits": 32,
    "activation_bits": 8,
    "integer_mode": true,
    "matrix_mac_contract": "signed_int4_x_signed_int8_to_signed_int32",
    "policy_id": "current_run_numeric_policy",
    "rounding": "nearest_even",
    "saturation": true,
    "scale_bits": 32,
    "scale_representation": "signed_int32_multiplier_with_explicit_shift",
    "source": "constraint.numeric.policy.default_rules",
    "stream_accumulator_bits": 8,
    "weight_bits": 4
  },
  "pipeline_style": "operator_stream_pipeline",
  "schema_version": "spatialaccagent.pipeline_plan.v0",
  "semantic_dataflow": {
    "adapter_path": "accagent/framework/case_adapters/gpt2_transformer_block.json",
    "boundary_numeric": {
      "input": "accumulator",
      "output": "accumulator"
    },
    "declared_edges": [
      {
        "destination": "layer_norm_1",
        "kind": "input",
        "source": "block_input"
      },
      {
        "destination": "residual_add_1",
        "destination_port": "skip",
        "kind": "residual_skip",
        "source": "block_input",
        "source_port": "residual"
      },
      {
        "destination": "self_attention",
        "source": "layer_norm_1"
      },
      {
        "destination": "residual_add_1",
        "destination_port": "main",
        "source": "self_attention"
      },
      {
        "destination": "layer_norm_2",
        "source": "residual_add_1"
      },
      {
        "destination": "residual_add_2",
        "destination_port": "skip",
        "kind": "residual_skip",
        "source": "residual_add_1",
        "source_port": "residual"
      },
      {
        "destination": "mlp_fc",
        "source": "layer_norm_2"
      },
      {
        "destination": "activation",
        "source": "mlp_fc"
      },
      {
        "destination": "mlp_proj",
        "source": "activation"
      },
      {
        "destination": "residual_add_2",
        "destination_port": "main",
        "source": "mlp_proj"
      },
      {
        "destination": "block_output",
        "kind": "output",
        "source": "residual_add_2"
      }
    ],
    "schema_version": "spatialaccagent.pipeline_dataflow.v1",
    "stage_metadata": {
      "activation": {
        "latency_kind": "pointwise_intermediate",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "activation"
        },
        "shape": {
          "input": "intermediate",
          "output": "intermediate"
        }
      },
      "layer_norm_1": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "activation"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "layer_norm_2": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "activation"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "mlp_fc": {
        "latency_kind": "linear_hidden_to_intermediate",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "activation"
        },
        "shape": {
          "input": "hidden",
          "output": "intermediate"
        }
      },
      "mlp_proj": {
        "latency_kind": "linear_intermediate_to_hidden",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "accumulator"
        },
        "shape": {
          "input": "intermediate",
          "output": "hidden"
        }
      },
      "residual_add_1": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "accumulator"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "residual_add_2": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "accumulator"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "self_attention": {
        "latency_kind": "self_attention",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "accumulator"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      }
    }
  },
  "stage": "pipeline_planning",
  "stage_gate_policy": {
    "current_stage_acceptance": [
      "operator order, edge graph, stream order, tensor shape, element width, branch/join, buffer, liveness, attention, template, memory/runtime handoff contracts must be checker-backed",
      "symbolic_first_order latency is only planning metadata and must not be used as throughput, timing, or hardware pass evidence",
      "stream_edges must mirror data_edges including block_input, residual-skip, and block_output boundary edges",
      "buffer implementations must be concrete bounded ready/valid FIFOs; ping-pong buffers are reserved for memory layout artifacts",
      "the supplied deterministic checker records and completed specialist-review bundle are executed current Stage-3 evidence; do not demand a duplicate evidence-gate run when they pass",
      "a resolved numeric value set with an unspecified source policy label is traceable planning metadata, not a Stage-3 numeric contradiction unless a displayed value conflicts with constraint.numeric.policy",
      "concrete host/core address translation, region base assignment, and output-header allocation are deferred to exact wrapper discovery and code generation; they are not Stage-3 blockers unless this plan claims an unverified concrete address or ABI"
    ],
    "later_stage_obligations": [
      "Stage 4 binds final per-template parameters from this contract",
      "Stage 5 assigns concrete memory base addresses and generates/elaborates template-bound Chisel",
      "Stage 6+ supplies real VCS/Verilator/Vivado/board evidence; Stage 3 must not claim hardware pass"
    ],
    "risk_classification_rule": "If checker_results pass and the completed specialist bundle has no error, return ready with risks=[]; do not turn unexecuted action suggestions or later-stage obligations into current risks. Put later-stage obligations in proposed_actions unless a current Stage 3 checker failed or the displayed plan directly contradicts an immutable input contract."
  },
  "stages": [
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-05
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
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
      "index": 0,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
      "kind": "norm",
      "latency": {
        "cycles": 1536,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "pointwise_hidden",
          "seq_len": 16,
          "stream_width": 768
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "layer_norm_1",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "activation"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "source": "Norm.scala",
      "stage_id": "stage_00_layer_norm_1",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 64
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "num_kv_heads": {
          "source": "constraint.shape.model.num_kv_heads",
          "status": "bound",
          "value": 12
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 12
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
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
        "width": 768
      },
      "kind": "attention",
      "latency": {
        "cycles": 26112,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "self_attention",
          "seq_len": 16,
          "stream_width": 768
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "self_attention",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "self_attention",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "accumulator"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "source": "Attention.scala",
      "stage_id": "stage_01_self_attention",
      "template_id": "attention"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
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
        "width": 768
      },
      "kind": "residual",
      "latency": {
        "cycles": 1536,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "pointwise_hidden",
          "seq_len": 16,
          "stream_width": 768
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "residual_add_1",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "accumulator"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "source": "Residual.scala",
      "stage_id": "stage_02_residual_add_1",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-05
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
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
      "index": 3,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
      "kind": "norm",
      "latency": {
        "cycles": 1536,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "pointwise_hidden",
          "seq_len": 16,
          "stream_width": 768
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "layer_norm_2",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "activation"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "source": "Norm.scala",
      "stage_id": "stage_03_layer_norm_2",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
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
        "width": 768
      },
      "kind": "mlp",
      "latency": {
        "cycles": 4718592,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "linear_hidden_to_intermediate",
          "seq_len": 16,
          "stream_width": 3072
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "mlp_fc",
      "output_shape": {
        "seq_len": 16,
        "width": 3072
      },
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "linear_hidden_to_intermediate",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "activation"
        },
        "shape": {
          "input": "hidden",
          "output": "intermediate"
        }
      },
      "source": "FFN.scala",
      "stage_id": "stage_04_mlp_fc",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 5,
      "input_shape": {
        "seq_len": 16,
        "width": 3072
      },
      "kind": "activation",
      "latency": {
        "cycles": 6144,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "pointwise_intermediate",
          "seq_len": 16,
          "stream_width": 3072
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "activation",
      "output_shape": {
        "seq_len": 16,
        "width": 3072
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "pointwise_intermediate",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "activation"
        },
        "shape": {
          "input": "intermediate",
          "output": "intermediate"
        }
      },
      "source": "Activation.scala",
      "stage_id": "stage_05_activation",
      "template_id": "activation"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "index": 6,
      "input_shape": {
        "seq_len": 16,
        "width": 3072
      },
      "kind": "mlp",
      "latency": {
        "cycles": 4718592,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "linear_intermediate_to_hidden",
          "seq_len": 16,
          "stream_width": 768
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "mlp_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "linear_intermediate_to_hidden",
        "numeric": {
          "input": "activation",
          "internal": "activation",
          "output": "accumulator"
        },
        "shape": {
          "input": "intermediate",
          "output": "hidden"
        }
      },
      "source": "FFN.scala",
      "stage_id": "stage_06_mlp_proj",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "index": 7,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
      "kind": "residual",
      "latency": {
        "cycles": 1536,
        "estimate_kind": "symbolic_first_order",
        "formula_inputs": {
          "hidden_size": 768,
          "intermediate_size": 3072,
          "lanes": 8,
          "latency_kind": "pointwise_hidden",
          "seq_len": 16,
          "stream_width": 768
        },
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence"
      },
      "numeric_contract": {
        "accumulator_bits": 32,
        "input_bits": 8,
        "internal_elem_bits": 8,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy",
        "output_bits": 8,
        "source": "constraint.numeric.policy.default_rules",
        "weight_bits": 4
      },
      "op": "residual_add_2",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "semantic_metadata": {
        "latency_kind": "pointwise_hidden",
        "numeric": {
          "input": "accumulator",
          "internal": "accumulator",
          "output": "accumulator"
        },
        "shape": {
          "input": "hidden",
          "output": "hidden"
        }
      },
      "source": "Residual.scala",
      "stage_id": "stage_07_residual_add_2",
      "template_id": "residual"
    }
  ],
  "status": "ready",
  "stream_edges": [
    {
      "backpressure": "dst_ready_propagates_to_src",
      "dst_port": "in",
      "dst_stage": "stage_00_layer_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_layer_norm_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_03_layer_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_04_mlp_fc",
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_03_layer_norm_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "dst_stage": "stage_05_activation",
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_04_mlp_fc",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 768,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 3072
        },
        "transfer_count_aligned_bytes": 49152,
        "transfer_count_bytes": 49152,
        "transfer_count_elements": 49152,
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
      "dst_stage": "stage_06_mlp_proj",
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_05_activation",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 768,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 3072
        },
        "transfer_count_aligned_bytes": 49152,
        "transfer_count_bytes": 49152,
        "transfer_count_elements": 49152,
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
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_mlp_proj",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
      "edge_id": "edge.data.stage_07_residual_add_2.to.block_output.output",
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_07_residual_add_2",
      "stream_contract": {
        "axi_alignment_bytes": 64,
        "axi_beats": 192,
        "axi_data_width_bits": 512,
        "dst_input_bits": 8,
        "element_bits": 8,
        "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        "src_output_bits": 8,
        "stream_beat_bits": 64,
        "stream_beats_per_axi_beat": 8,
        "stream_order": [
          "token",
          "tile",
          "lane",
          "word"
        ],
        "tensor": {
          "seq_len": 16,
          "width": 768
        },
        "transfer_count_aligned_bytes": 12288,
        "transfer_count_bytes": 12288,
        "transfer_count_elements": 12288,
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
    "buffer implementations must be concrete bounded ready/valid FIFOs; ping-pong buffers are reserved for memory layout artifacts",
    "the supplied deterministic checker records and completed specialist-review bundle are executed current Stage-3 evidence; do not demand a duplicate evidence-gate run when they pass",
    "a resolved numeric value set with an unspecified source policy label is traceable planning metadata, not a Stage-3 numeric contradiction unless a displayed value conflicts with constraint.numeric.policy",
    "concrete host/core address translation, region base assignment, and output-header allocation are deferred to exact wrapper discovery and code generation; they are not Stage-3 blockers unless this plan claims an unverified concrete address or ABI"
  ],
  "later_stage_obligations": [
    "Stage 4 binds final per-template parameters from this contract",
    "Stage 5 assigns concrete memory base addresses and generates/elaborates template-bound Chisel",
    "Stage 6+ supplies real VCS/Verilator/Vivado/board evidence; Stage 3 must not claim hardware pass"
  ],
  "risk_classification_rule": "If checker_results pass and the completed specialist bundle has no error, return ready with risks=[]; do not turn unexecuted action suggestions or later-stage obligations into current risks. Put later-stage obligations in proposed_actions unless a current Stage 3 checker failed or the displayed plan directly contradicts an immutable input contract."
}
</stage_gate_policy>

<checker_results>
[
  {
    "checker": "operator_order_check",
    "errors": [],
    "status": "pass",
    "summary": "operator_order=['layer_norm_1', 'self_attention', 'residual_add_1', 'layer_norm_2', 'mlp_fc', 'activation', 'mlp_proj', 'residual_add_2']",
    "warnings": []
  },
  {
    "checker": "semantic_dataflow_contract_check",
    "errors": [],
    "status": "pass",
    "summary": "adapter_graph_edges=11",
    "warnings": []
  },
  {
    "checker": "stream_data_edge_mirror_check",
    "errors": [],
    "status": "pass",
    "summary": "edges=11",
    "warnings": []
  },
  {
    "checker": "edge_stream_contract_check",
    "errors": [],
    "status": "pass",
    "summary": "checked_edges=11",
    "warnings": []
  },
  {
    "checker": "shape_numeric_contract_check",
    "errors": [],
    "status": "pass",
    "summary": "stages=8, activation_bits=8, accumulator_bits=32",
    "warnings": []
  },
  {
    "checker": "branch_join_contract_check",
    "errors": [],
    "status": "pass",
    "summary": "splits=2, joins=2",
    "warnings": []
  },
  {
    "checker": "buffer_contract_check",
    "errors": [],
    "status": "pass",
    "summary": "buffers=11, allowed_depths=[32, 64]",
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
    "summary": "q=12, kv=12, head_dim=64",
    "warnings": []
  },
  {
    "checker": "template_binding_static_check",
    "errors": [],
    "status": "pass",
    "summary": "stages=8, free_form_rtl_generation=false",
    "warnings": []
  }
]
</checker_results>

<checker_summary>
{
  "errors": [],
  "failed": 0,
  "passed": 11,
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
      "summary": "operator_order=['layer_norm_1', 'self_attention', 'residual_add_1', 'layer_norm_2', 'mlp_fc', 'activation', 'mlp_proj', 'residual_add_2']",
      "warnings": []
    },
    {
      "checker": "semantic_dataflow_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "adapter_graph_edges=11",
      "warnings": []
    },
    {
      "checker": "stream_data_edge_mirror_check",
      "errors": [],
      "status": "pass",
      "summary": "edges=11",
      "warnings": []
    },
    {
      "checker": "edge_stream_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "checked_edges=11",
      "warnings": []
    },
    {
      "checker": "shape_numeric_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "stages=8, activation_bits=8, accumulator_bits=32",
      "warnings": []
    },
    {
      "checker": "branch_join_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "splits=2, joins=2",
      "warnings": []
    },
    {
      "checker": "buffer_contract_check",
      "errors": [],
      "status": "pass",
      "summary": "buffers=11, allowed_depths=[32, 64]",
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
      "summary": "q=12, kv=12, head_dim=64",
      "warnings": []
    },
    {
      "checker": "template_binding_static_check",
      "errors": [],
      "status": "pass",
      "summary": "stages=8, free_form_rtl_generation=false",
      "warnings": []
    }
  ],
  "schema_version": "spatialaccagent.pipeline_static_checks.v0",
  "stage": "pipeline_planning",
  "status": "pass",
  "summary": {
    "errors": [],
    "failed": 0,
    "passed": 11,
    "warnings": []
  }
}
</pipeline_static_checks>

<design_team>
{
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/pipeline_planning/team/team_aggregate.json",
  "approval_required_for": [
    "stage3.memory_runtime_remove_concrete_address_claims"
  ],
  "completed_subtasks": 3,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/pipeline_planning/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "stream_plan_check"
      ],
      "action_type": "cross_layer_rule_review",
      "consumes": [
        "artifact.input.target_board_profile",
        "artifact.input.numeric_policy",
        "candidate_stage_artifact.pipeline_plan"
      ],
      "id": "pipeline_planning.data_transfer_engineer.publish_review",
      "on_failure": "If team_aggregate or a peer identifies a cross-layer contradiction, return the specific edge/order/FIFO/join contract to pipeline_planning and block Stage-4 binding on that edge until corrected.",
      "produces": [
        "artifact.stage3.data_transfer_review"
      ],
      "rationale": "Hand off the ready data-transfer review to team_aggregate so peer specialists consume checker-grounded Stage-3 observations. The reviewed plan has exact data/stream edge mirroring, correct transfer counts and full AXI beat alignment, atomic ready/valid split behavior, all-input join behavior, and bounded acyclic FIFO liveness with no current Stage-3 contradiction.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "team_aggregate",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "boundary_contract_check",
        "sacg_static_check"
      ],
      "action_type": "bounded_repair",
      "consumes": [
        "candidate pipeline_plan memory_schedule",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.deployment.board"
      ],
      "id": "stage3.memory_runtime_remove_concrete_address_claims",
      "on_failure": "Keep pipeline_planning blocked; do not promote to Stage-4 until symbolic region handles replace concrete unverified XDMA/DDR addresses and all listed checkers pass.",
      "produces": [
        "corrected pipeline_plan memory_schedule.runtime_config_requirements",
        "artifact.stage3.memory_runtime_review"
      ],
      "rationale": "The current memory_schedule violates the Stage-3 memory/runtime deferral boundary by embedding concrete c2h/h2c target base addresses and a concrete output_tokens address before exact board-wrapper discovery. The repair must preserve board AXI/XDMA hooks but convert assigned bases into symbolic region handles.",
      "requires_approval": true,
      "stage": "pipeline_planning",
      "targeted_replay_plan": {
        "focus": "runtime_config_requirements concrete base removal",
        "preserve": "board_axi width/protocol facts, required_regions roles, double-buffer/streamed activation policy, target_seq_len compile-time bound"
      },
      "tool_roles": [
        "memory_runtime_repair",
        "memory_runtime_plan_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "boundary_contract_check",
        "sacg_static_check"
      ],
      "action_type": "checker_execution",
      "consumes": [
        "corrected pipeline_plan memory_schedule.runtime_config_requirements",
        "artifact.stage3.memory_runtime_review"
      ],
      "id": "stage3.memory_runtime_checker_gate",
      "on_failure": "Treat any failure as a current pipeline_planning blocker and return the tool output into bounded memory_runtime_repair localization; do not advance to Stage-4.",
      "produces": [
        "checker evidence memory_runtime_plan_check",
        "checker evidence addr_map_check",
        "checker evidence boundary_contract_check"
      ],
      "rationale": "Run the two missing subtask-acceptance checks on the corrected plan to produce checker-backed evidence that no concrete address/ABI assignment remains and the region hooks are valid.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "boundary_contract_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_binding_static_check",
        "boundary_contract_check"
      ],
      "action_type": "specialist_review_handoff",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.stage2.template_selection",
        "candidate_stage_artifact.pipeline_plan"
      ],
      "id": "pipeline_planning.pipeline_architect.review_handoff",
      "on_failure": "Do not aggregate the pipeline plan; return the review to pipeline_planning with the failed checker evidence and preserve the current stage boundary.",
      "produces": [
        "artifact.stage3.pipeline_architect_review"
      ],
      "rationale": "Promote the pipeline architect review as a checker-backed Stage-3 specialist output for downstream specialists and team aggregation.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "architecture_review"
      ]
    },
    {
      "acceptance_checkers": [
        "stream_plan_check",
        "boundary_contract_check"
      ],
      "action_type": "handoff",
      "consumes": [
        "artifact.stage3.pipeline_architect_review",
        "candidate_stage_artifact.pipeline_plan",
        "artifact.input.numeric_policy"
      ],
      "id": "pipeline_planning.data_transfer_engineer.review_stream_edges",
      "on_failure": "Keep data-transfer binding blocked until stream/data edge mirroring, transfer_count_bytes, transfer_order, element_bits, and FIFO depth are reconciled without changing the preserved operator order.",
      "produces": [
        "artifact.stage3.data_transfer_engineer_review"
      ],
      "rationale": "Peer data-transfer specialist must validate stream/data edge mirroring, transfer order, element widths, transfer counts, and FIFO depth before Stage 4 template parameter binding.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "stream_plan_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "boundary_contract_check"
      ],
      "action_type": "handoff",
      "consumes": [
        "artifact.stage3.pipeline_architect_review",
        "candidate_stage_artifact.pipeline_plan",
        "artifact.input.target_board_profile"
      ],
      "id": "pipeline_planning.memory_dataflow_engineer.review_memory_schedule",
      "on_failure": "Do not promote memory/runtime base-address, XDMA ABI, region-base, or output-header allocation claims; defer to exact board-wrapper discovery and code generation.",
      "produces": [
        "artifact.stage3.memory_dataflow_engineer_review"
      ],
      "rationale": "Peer memory/dataflow specialist must reconcile buffer plan, memory regions, double-buffered weights, and board/XDMA address hints while keeping concrete address/ABI claims deferred to exact wrapper discovery.",
      "requires_approval": false,
      "stage": "pipeline_planning",
      "tool_roles": [
        "memory_runtime_plan_check"
      ]
    }
  ],
  "execution_groups": [
    0
  ],
  "llm_io_metrics": {
    "executable_action_count": 6,
    "max_duration_sec": 167.72476451197872,
    "max_prompt_bytes": 76101,
    "result_count": 3,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 386.58881059195846,
    "total_prompt_bytes": 227575
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 3,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/pipeline_planning/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

<current_stage_evidence>
{
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 11,
    "warnings": []
  },
  "deferred_obligations": [
    "Stage 4 binds final per-template parameters from this contract",
    "Stage 5 assigns concrete memory base addresses and generates/elaborates template-bound Chisel",
    "Stage 6+ supplies real VCS/Verilator/Vivado/board evidence; Stage 3 must not claim hardware pass"
  ],
  "deterministic_checkers_executed": true,
  "specialist_bundle_completed": true,
  "specialist_bundle_errors": []
}
</current_stage_evidence>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/template_selection/sacg_state.json
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
