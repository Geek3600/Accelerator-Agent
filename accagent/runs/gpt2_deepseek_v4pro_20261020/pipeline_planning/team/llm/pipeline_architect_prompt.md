<agent>
pipeline_architect
</agent>

<task>
Verify that the planned stages preserve GPT-2 decoder operator order and expose correct residual, attention, norm, and MLP template boundaries without free-form RTL generation.
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

<team_context>
{
  "collaboration_contract": {
    "coordination_policy": [
      "parallel specialists may disagree, but disagreement must be surfaced as bounded risks or handoff actions",
      "auditor/evidence-gate roles consume specialist outputs and must not silently rewrite them",
      "downstream stages consume the aggregate only after all required specialist roles completed without fallback"
    ],
    "rule": "Each sub-agent owns its explicit role_assignment and hands off only checker-grounded observations, risks, approval needs, and executable actions.",
    "schema_version": "spatialaccagent.team_collaboration_contract.v0",
    "team_model": "chip_design_team"
  },
  "objective": "Plan and audit the spatial pipeline as a set of SACG stream, beat, memory, and liveness constraints.",
  "paper_alignment": {
    "method": "SACG-guided, template-constrained, checker-verified design closure",
    "problem": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design"
  },
  "stage": "pipeline_planning",
  "team_rules": [
    "Act as an AI chip design team for FPGA spatial accelerator automatic design, not as isolated static scripts.",
    "Stay inside the SpatialAccAgent paper story: cross-layer consistency for LLM spatial accelerators.",
    "Treat SACG as the design team's shared memory and evidence ledger; do not rely on natural-language memory as correctness evidence.",
    "Treat sacg_memory_truth as the authoritative current blocker set; closed, superseded, or historical memory records are recovery evidence onl...<len=142>",
    "Use trusted templates and bounded glue code; do not propose free-form RTL rewrites outside approved repair boundaries.",
    "Map every observation to model, shape, numeric precision, data order, transfer unit, memory, runtime, implementation, or deployment constrai...<len=144>",
    "Do not bypass checkers, modify golden outputs, loosen tolerance, or claim hardware pass without tool evidence.",
    "All verification layers pass when the current hardware sources compile, elaborate, and link successfully in real VCS; repair compiler errors...<len=191>",
    "Do not require simulation execution, runtime weight loading, golden comparisons, signal traces, output dumps, or numerical correctness. Hist...<len=207>",
    "Require the exact user sample-project wrapper and source identity at board level, and keep model/board/example names out of framework-core d...<len=149>",
    "The accelerator scope is Transformer blocks only; exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT we...<len=169>",
    "For board/app-shell integration, use LLM reasoning to synthesize profile/contract policy from user-supplied materials and real tool evidence...<len=199>",
    "Use hash-validated hierarchical learning context to preserve certified lower-layer timing invariants; only a current named trace contradicti...<len=168>",
    "At board scope, keep independent AXI/prefetch progress separate from output/lifecycle-frontier progress, and treat a frontier stall as local...<len=196>",
    "Do not reopen a certified lower layer from a board output symptom alone; require current hash-bound direct core start/ingress/egress evidenc...<len=216>"
  ]
}
</team_context>

<subtask>
{
  "acceptance_checkers": [
    "sacg_static_check",
    "template_binding_static_check",
    "boundary_contract_check"
  ],
  "action_type": "sacg_constraint_review",
  "agent": "pipeline_architect",
  "artifact_focus": [
    "stages",
    "attention_contract",
    "branch_join_contracts",
    "buffer_plan"
  ],
  "constraints": [
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.cross_layer.input_consistency"
  ],
  "expected_artifacts": [
    "artifact.stage3.pipeline_architect_review"
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
    "pipeline_planning.data_transfer_engineer",
    "pipeline_planning.memory_dataflow_engineer",
    "team_aggregate"
  ],
  "id": "pipeline_planning.pipeline_architect",
  "objective": "Verify that the planned stages preserve GPT-2 decoder operator order and expose correct residual, attention, norm, and MLP template boundaries without free-form RTL generation.",
  "role": "pipeline architect",
  "role_assignment": {
    "collaboration_interfaces": {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_binding_static_check",
        "boundary_contract_check"
      ],
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.stage2.template_selection",
        "candidate stage plan stages/attention_contract/branch_join_contracts"
      ],
      "handoff_to": [
        "pipeline_planning.data_transfer_engineer",
        "pipeline_planning.memory_dataflow_engineer",
        "team_aggregate"
      ],
      "produces": [
        "artifact.stage3.pipeline_architect_review"
      ]
    },
    "decision_authority": [
      "May flag Stage-3 planning blockers for model/shape/template boundary inconsistencies.",
      "May request bounded artifact correction within pipeline_planning.",
      "May not promote later-stage hardware timing, throughput, or board readiness claims."
    ],
    "mission": "Check whether pipeline stages preserve decoder operator order and expose residual, attention, and template boundaries.",
    "out_of_scope": [
      "Do not assign concrete DDR base addresses or XDMA ABI address translation.",
      "Do not synthesize or simulate RTL.",
      "Do not treat symbolic first-order latency as timing evidence."
    ],
    "primary_responsibilities": [
      "Audit artifact.stage3.pipeline_plan stages against constraint.model.decoder operator order.",
      "Audit attention/qkv/head mapping and position encoding boundary against constraint.shape.model.",
      "Confirm every stage is bound to a trusted template id and no free-form RTL claim exists.",
      "Detect residual-skip and branch/join boundary mismatches between the semantic graph and SACG constraints."
    ]
  },
  "role_profile": {
    "capabilities": [
      "extract model semantics",
      "audit shape and head mapping",
      "track residual/operator order"
    ],
    "constraint_focus": [
      "constraint.model.decoder",
      "constraint.shape.model"
    ],
    "family": "model_shape"
  },
  "title": "Review decoder stage decomposition and template boundaries"
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
  "design_id": "gpt2_deepseek_v4pro_20261020",
  "edges": 7,
  "failed_invariants": [],
  "hierarchical_learning_context": {
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
  },
  "nodes": 20,
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
      "depth": 64,
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
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
      "buffer_id": "buffer.edge_data_stage_00_layer_norm_1_to_stage_01_self_attention_main",
      "depth": 32,
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_01_self_attention_to_stage_02_residual_add_1_main",
      "depth": 64,
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_03_layer_norm_2_main",
      "depth": 64,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_02_residual_add_1_to_stage_07_residual_add_2_residual_skip",
      "depth": 64,
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_03_layer_norm_2_to_stage_04_mlp_fc_main",
      "depth": 32,
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_04_mlp_fc_to_stage_05_activation_main",
      "depth": 32,
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_05_activation_to_stage_06_mlp_proj_main",
      "depth": 32,
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "decouple adjacent pipeline stages",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_06_mlp_proj_to_stage_07_residual_add_2_main",
      "depth": 64,
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "implementation": "trusted_queue_template",
      "kind": "bounded_ready_valid_fifo",
      "purpose": "preserve branch token order under backpressure",
      "resource_class": "on_chip_fifo"
    },
    {
      "buffer_id": "buffer.edge_data_stage_07_residual_add_2_to_block_output_output",
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
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_00_layer_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "skip",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_layer_norm_1",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "main",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_01_self_attention",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_03_layer_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "skip",
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_04_mlp_fc",
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_03_layer_norm_2",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 768,
      "dst_port": "in",
      "dst_stage": "stage_05_activation",
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_04_mlp_fc",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 3072
      },
      "transfer_count_bytes": 49152,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 768,
      "dst_port": "in",
      "dst_stage": "stage_06_mlp_proj",
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_05_activation",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 3072
      },
      "transfer_count_bytes": 49152,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "main",
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_mlp_proj",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_07_residual_add_2.to.block_output.output",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_07_residual_add_2",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
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
    "num_layers": 12,
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
    "target_seq_len": 16
  },
  "model_type": "gpt2",
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
      "index": 0,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
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
        "output_bits": 8
      },
      "op": "layer_norm_1",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "source": "Norm.scala",
      "stage_id": "stage_00_layer_norm_1",
      "template_id": "norm"
    },
    {
      "index": 1,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
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
        "output_bits": 8
      },
      "op": "self_attention",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "source": "Attention.scala",
      "stage_id": "stage_01_self_attention",
      "template_id": "attention"
    },
    {
      "index": 2,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
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
        "output_bits": 8
      },
      "op": "residual_add_1",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "source": "Residual.scala",
      "stage_id": "stage_02_residual_add_1",
      "template_id": "residual"
    },
    {
      "index": 3,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
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
        "output_bits": 8
      },
      "op": "layer_norm_2",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "source": "Norm.scala",
      "stage_id": "stage_03_layer_norm_2",
      "template_id": "norm"
    },
    {
      "index": 4,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
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
        "output_bits": 8
      },
      "op": "mlp_fc",
      "output_shape": {
        "seq_len": 16,
        "width": 3072
      },
      "source": "FFN.scala",
      "stage_id": "stage_04_mlp_fc",
      "template_id": "ffn"
    },
    {
      "index": 5,
      "input_shape": {
        "seq_len": 16,
        "width": 3072
      },
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
        "output_bits": 8
      },
      "op": "activation",
      "output_shape": {
        "seq_len": 16,
        "width": 3072
      },
      "source": "Activation.scala",
      "stage_id": "stage_05_activation",
      "template_id": "activation"
    },
    {
      "index": 6,
      "input_shape": {
        "seq_len": 16,
        "width": 3072
      },
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
        "output_bits": 8
      },
      "op": "mlp_proj",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "source": "FFN.scala",
      "stage_id": "stage_06_mlp_proj",
      "template_id": "ffn"
    },
    {
      "index": 7,
      "input_shape": {
        "seq_len": 16,
        "width": 768
      },
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
        "output_bits": 8
      },
      "op": "residual_add_2",
      "output_shape": {
        "seq_len": 16,
        "width": 768
      },
      "source": "Residual.scala",
      "stage_id": "stage_07_residual_add_2",
      "template_id": "residual"
    }
  ],
  "status": "ready",
  "stream_edges": [
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_00_layer_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "input",
      "src_port": "out",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "skip",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "block_input",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_00_layer_norm_1",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "main",
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_01_self_attention",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_03_layer_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "skip",
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "residual_skip",
      "src_port": "residual",
      "src_stage": "stage_02_residual_add_1",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "stage_04_mlp_fc",
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_03_layer_norm_2",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 768,
      "dst_port": "in",
      "dst_stage": "stage_05_activation",
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_04_mlp_fc",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 3072
      },
      "transfer_count_bytes": 49152,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 768,
      "dst_port": "in",
      "dst_stage": "stage_06_mlp_proj",
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_05_activation",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 3072
      },
      "transfer_count_bytes": 49152,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "main",
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "main",
      "src_port": "out",
      "src_stage": "stage_06_mlp_proj",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
      "transfer_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "valid_byte_policy": "full_beats_only"
    },
    {
      "axi_beats": 192,
      "dst_port": "in",
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_07_residual_add_2.to.block_output.output",
      "element_bits": 8,
      "flow_control": "ready_valid",
      "kind": "output",
      "src_port": "out",
      "src_stage": "stage_07_residual_add_2",
      "stream_beats_per_axi_beat": 8,
      "tensor": {
        "seq_len": 16,
        "width": 768
      },
      "transfer_count_bytes": 12288,
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
{}
</sacg_memory>

<sacg_memory_truth>
{}
</sacg_memory_truth>

<hierarchical_learning_context>
{}
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
