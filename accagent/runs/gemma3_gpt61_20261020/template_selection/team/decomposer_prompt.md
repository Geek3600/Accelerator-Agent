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
template_selection
</stage>

<objective>
Strictly bind trusted templates to every model operator, source file, parameter, attention semantic, and cross-layer board/numeric constraint without drifting into free-form RTL generation.
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
  "design_id": "gemma3_gpt61_20261020",
  "edges": 10,
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
  "nodes": 23,
  "sacg_memory": {
    "active_contamination_barriers": [
      {
        "artifact_id": "artifact.stage2.template_selection",
        "id": "contamination_barrier.0001",
        "observation_count": 1,
        "observed_transition_ids": [
          "transition.0001"
        ],
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "strict template binding failed: ['gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024', 'self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024']",
        "status": "active",
        "timestamp": "2026-10-20T13:09:12+00:00",
        "transition_id": "transition.0001"
      }
    ],
    "open_backtrack_requests": [],
    "open_retry_requests": [],
    "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
    "recent_contamination_barriers": [
      {
        "artifact_id": "artifact.stage2.template_selection",
        "id": "contamination_barrier.0001",
        "observation_count": 1,
        "observed_transition_ids": [
          "transition.0001"
        ],
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "strict template binding failed: ['gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024', 'self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024']",
        "status": "active",
        "timestamp": "2026-10-20T13:09:12+00:00",
        "transition_id": "transition.0001"
      }
    ],
    "recent_failure_lessons": [],
    "recent_stage_outcomes": [],
    "schema_version": "spatialaccagent.sacg_memory.v0"
  },
  "sacg_memory_truth": {
    "active_contamination_barrier_count": 1,
    "active_contamination_barriers": [
      {
        "artifact_id": "artifact.stage2.template_selection",
        "id": "contamination_barrier.0001",
        "observation_count": 1,
        "observed_transition_ids": [
          "transition.0001"
        ],
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "strict template binding failed: ['gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024', 'self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024']",
        "status": "active",
        "timestamp": "2026-10-20T13:09:12+00:00",
        "transition_id": "transition.0001"
      }
    ],
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
  "attention_semantics": {
    "components": [
      {
        "component": "qkv_projection",
        "evidence_pattern": "Module(new QKVProjection",
        "evidence_type": "hash_bound_template_source",
        "required": true,
        "source": "DecoderBlock.scala",
        "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
        "status": "covered"
      },
      {
        "component": "rope",
        "evidence_pattern": "Module(new RoPE",
        "evidence_type": "hash_bound_template_source",
        "required": true,
        "source": "DecoderBlock.scala",
        "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
        "status": "covered"
      },
      {
        "component": "gqa_head_mapping",
        "evidence_pattern": "kvGroupSize",
        "evidence_type": "hash_bound_template_source",
        "gqa_group_size": 4,
        "params": {
          "num_kv_heads": 1,
          "num_q_heads": 4
        },
        "required": true,
        "source": "QKVProjection.scala",
        "source_sha256": "3ca84ba8f25c4f151d9bba237fbf61f1c2ca64b572dc02a1e570e8649a546bc1",
        "status": "covered"
      },
      {
        "component": "softmax",
        "evidence_pattern": "template_id=softmax",
        "evidence_type": "hash_bound_template_source",
        "required": true,
        "source": "Softmax.scala",
        "source_sha256": "4f68287b82eab429fa5da62a9d8f3fd1a537f00ef42e364f411e7dd3537e94f2",
        "status": "covered"
      },
      {
        "component": "output_projection",
        "evidence_pattern": "val outputProjection = Module(new Linear(p.outLinear))",
        "evidence_type": "hash_bound_template_source",
        "required": true,
        "source": "Attention.scala",
        "source_sha256": "c3e8bfc0ab0c1c8d4421bb0fe03272f4ea420df3f0e710b6a3c4154843593a7e",
        "status": "covered"
      },
      {
        "component": "kv_cache",
        "evidence_pattern": "Module(new KVCache",
        "evidence_type": "hash_bound_template_source",
        "required": false,
        "source": "DecoderBlock.scala",
        "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
        "status": "not_required"
      },
      {
        "component": "causal_mask",
        "evidence_pattern": "template_id=mask",
        "evidence_type": "hash_bound_template_source",
        "required": true,
        "source": "Mask.scala",
        "source_sha256": "bfb70e48641d60c25100b8240d5fef461aa954847c5fe5777b7fbb5445fc0e0a",
        "status": "covered"
      }
    ],
    "required": true
  },
  "checker_results": [
    {
      "checker": "operator_coverage_check",
      "errors": [],
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_parameter_binding_check",
      "errors": [
        "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024",
        "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "status": "fail",
      "warnings": []
    },
    {
      "checker": "template_source_and_interface_check",
      "errors": [],
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "mandatory_fpga_ip_binding_check",
      "errors": [],
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "attention_semantic_expansion_check",
      "errors": [],
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "cross_layer_trace_check",
      "errors": [],
      "status": "pass",
      "warnings": []
    }
  ],
  "coverage": {
    "covered_ops": 11,
    "has_block_wrapper": true,
    "required_ops": 11
  },
  "cross_layer_trace": {
    "constraints": [
      {
        "constraint": "constraint.numeric.policy",
        "fact_keys": [
          "_llm_provenance",
          "_numeric_comparison_resolution",
          "default_rules",
          "notes",
          "policy_id",
          "schema_version",
          "tolerance"
        ],
        "present": true
      },
      {
        "constraint": "constraint.memory.board",
        "fact_keys": [
          "memory_system"
        ],
        "present": true
      },
      {
        "constraint": "constraint.runtime.board",
        "fact_keys": [
          "board_run_command",
          "c2h_device_template",
          "control_base",
          "control_protocol",
          "ctrl_base",
          "ddr_base",
          "ddr_image_default",
          "device_id",
          "h2c_device_template",
          "image_path",
          "mimic_dir",
          "output_abs",
          "output_address",
          "runtime_directory",
          "xdma_id_default"
        ],
        "present": true
      },
      {
        "constraint": "constraint.deployment.board",
        "fact_keys": [
          "board",
          "board_pass_criteria",
          "shell"
        ],
        "present": true
      },
      {
        "constraint": "constraint.cross_layer.input_consistency",
        "fact_keys": [
          "acceptance_boundary",
          "board",
          "conflict_rules",
          "evidence_by_field",
          "evidence_fields",
          "field_resolution",
          "materials",
          "model",
          "numeric_policy",
          "tools"
        ],
        "present": true
      }
    ],
    "status": "pass"
  },
  "errors": [
    "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024",
    "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
  ],
  "forbidden_edits": [
    "Do not close missing template coverage with free-form RTL.",
    "Do not rely on Chisel default constructor values when a model, numeric, or board value is available.",
    "Do not change template internals, data order, memory layout, numeric policy, or board/runtime assumptions without approval.",
    "Do not use HardFloat, SyncReadMem, or a simulation-only arithmetic/memory backend."
  ],
  "library_id": "spatialaccagent_chisel_templates_v0",
  "missing_ops": [],
  "model_type": "gemma3_text",
  "operator_sequence": [
    "rms_norm_input",
    "self_attention",
    "rms_norm_post_attention",
    "residual_add_1",
    "rms_norm_pre_ffn",
    "mlp_gate_proj",
    "mlp_up_proj",
    "activation_mul",
    "mlp_down_proj",
    "rms_norm_post_ffn",
    "residual_add_2"
  ],
  "parameter_bindings": [
    {
      "bound_params": {
        "acc_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "compute_array_cols": {
          "source": "constraint.arch.design_space.search_params physical candidate universe",
          "status": "candidate_bound",
          "value": null
        },
        "compute_array_rows": {
          "source": "constraint.arch.design_space.search_params physical candidate universe",
          "status": "candidate_bound",
          "value": null
        },
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 256
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "input_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 6912
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "max_seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "num_kv_heads": {
          "source": "constraint.shape.model.num_kv_heads",
          "status": "bound",
          "value": 1
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 4
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "token_count": {
          "source": "constraint.shape.model.target_max_seq_len (one streamed token per sequence position)",
          "status": "bound",
          "value": 16
        },
        "weight_bits": {
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [
        "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "missing_params": [],
      "op": "gemma3_text_block",
      "source": "DecoderBlock.scala",
      "status": "incomplete",
      "template_id": "decoder_block"
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
          "value": 1152
        },
        "input_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "rms_norm_input",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 256
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "num_kv_heads": {
          "source": "constraint.shape.model.num_kv_heads",
          "status": "bound",
          "value": 1
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 4
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "weight_bits": {
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [
        "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "missing_params": [],
      "op": "self_attention",
      "source": "Attention.scala",
      "status": "incomplete",
      "template_id": "attention"
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
          "value": 1152
        },
        "input_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "rms_norm_post_attention",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "residual_add_1",
      "source": "Residual.scala",
      "status": "ready",
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
          "value": 1152
        },
        "input_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "rms_norm_pre_ffn",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 6912
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "mlp_gate_proj",
      "source": "FFN.scala",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "acc_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 6912
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "mlp_up_proj",
      "source": "FFN.scala",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 6912
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "activation_mul",
      "source": "Elementwise.scala",
      "status": "ready",
      "template_id": "elementwise"
    },
    {
      "bound_params": {
        "acc_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 6912
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "mlp_down_proj",
      "source": "FFN.scala",
      "status": "ready",
      "template_id": "ffn"
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
          "value": 1152
        },
        "input_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "rms_norm_post_ffn",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 1152
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "residual_add_2",
      "source": "Residual.scala",
      "status": "ready",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "elem_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "softmax",
      "source": "Softmax.scala",
      "status": "ready",
      "template_id": "softmax"
    },
    {
      "bound_params": {
        "causal": {
          "source": "artifact.input.model_config.attention.causal",
          "status": "bound",
          "value": true
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "causal_mask",
      "source": "Mask.scala",
      "status": "ready",
      "template_id": "mask"
    }
  ],
  "required_adapters": [],
  "schema_version": "spatialaccagent.template_selection.v0",
  "selected_templates": [
    {
      "matched_op": "gemma3_text_block",
      "op": "gemma3_text_block",
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "intermediate_size",
        "lanes",
        "compute_array_rows",
        "compute_array_cols",
        "token_count",
        "max_seq_len",
        "input_bits",
        "elem_bits",
        "output_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "block_wrapper",
      "source": "DecoderBlock.scala",
      "template_id": "decoder_block"
    },
    {
      "matched_op": "rms_norm",
      "op": "rms_norm_input",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "template_id": "norm"
    },
    {
      "matched_op": "self_attention",
      "op": "self_attention",
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
      "role": "operator",
      "source": "Attention.scala",
      "template_id": "attention"
    },
    {
      "matched_op": "rms_norm",
      "op": "rms_norm_post_attention",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "template_id": "norm"
    },
    {
      "matched_op": "residual_add_1",
      "op": "residual_add_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "template_id": "residual"
    },
    {
      "matched_op": "rms_norm",
      "op": "rms_norm_pre_ffn",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "template_id": "norm"
    },
    {
      "matched_op": "mlp_gate_proj",
      "op": "mlp_gate_proj",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "template_id": "ffn"
    },
    {
      "matched_op": "mlp_up_proj",
      "op": "mlp_up_proj",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "template_id": "ffn"
    },
    {
      "matched_op": "activation_mul",
      "op": "activation_mul",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Elementwise.scala",
      "template_id": "elementwise"
    },
    {
      "matched_op": "mlp_down_proj",
      "op": "mlp_down_proj",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "template_id": "ffn"
    },
    {
      "matched_op": "rms_norm",
      "op": "rms_norm_post_ffn",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "template_id": "norm"
    },
    {
      "matched_op": "residual_add_2",
      "op": "residual_add_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "template_id": "residual"
    },
    {
      "matched_op": "softmax",
      "op": "softmax",
      "required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "role": "attention_submodule",
      "source": "Softmax.scala",
      "template_id": "softmax"
    },
    {
      "matched_op": "causal_mask",
      "op": "causal_mask",
      "required_params": [
        "seq_len",
        "causal"
      ],
      "role": "attention_submodule",
      "source": "Mask.scala",
      "template_id": "mask"
    }
  ],
  "stage": "template_selection",
  "stage_gate_policy": {
    "classification_rule": "Put only unresolved current_stage_blocks in risks. Put not_current_stage_blocks in proposed_actions or approval_required_for. The supplied checker evidence is computed from the current source tree: template source/interface records and attention components carry source hashes, while the mandatory FPGA-IP checker scans the complete template directory. Do not require a second future code-generation, simulation, or synthesis audit to accept those current Stage-2 facts. If all deterministic checker_results pass and no concrete contradiction in their current evidence remains, return status='ready' and risks=[].",
    "current_stage_blocks": [
      "any decoder operator has no trusted selected template or explicit required adapter",
      "any selected template required parameter is unbound, illegal, or only supplied by an implicit constructor default when model/numeric/board input has a value",
      "any selected template source file is missing or its metadata required parameters do not match the Chisel case-class constructor",
      "the complete selected template closure contains HardFloat, SyncReadMem, or lacks mandatory Vivado floating-point/XPM bindings",
      "self_attention lacks selected or embedded coverage for Q/K/V projection, RoPE when required, GQA/MQA head mapping, softmax, output projection, required KV-cache behavior, or causal mask",
      "numeric policy, board memory, board runtime, board deployment, or cross-layer input-consistency constraints are absent from the template-selection trace",
      "LLM sub-agent output reports a concrete contradiction in the candidate selection for this stage"
    ],
    "not_current_stage_blocks": [
      "lanes, compute_array_rows, or compute_array_cols has not yet been selected from a Stage-2-validated candidate_bound domain; Stage 4 is the sole concrete DSE selection authority",
      "VCS/Verilator simulation has not been run yet",
      "Vivado synthesis, implementation, timing closure, or bitstream generation has not been run yet",
      "final generated accelerator code has not been emitted yet",
      "runtime driver, board wrapper, or full DDR/AXI top-level integration has not been generated yet",
      "later-stage numeric accuracy or board bring-up evidence is not present yet"
    ],
    "schema_version": "spatialaccagent.stage2_gate_policy.v0"
  },
  "status": "incomplete",
  "template_source_checks": [
    {
      "case_class": "Gemma3TextBlockParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "gemma3_text_block",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/DecoderBlock.scala",
      "sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
      "source": "DecoderBlock.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "decoder_block"
    },
    {
      "case_class": "RMSNormParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "rms_norm_input",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm"
    },
    {
      "case_class": "AttentionParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "self_attention",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Attention.scala",
      "sha256": "c3e8bfc0ab0c1c8d4421bb0fe03272f4ea420df3f0e710b6a3c4154843593a7e",
      "source": "Attention.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "attention"
    },
    {
      "case_class": "RMSNormParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "rms_norm_post_attention",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm"
    },
    {
      "case_class": "ResidualParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "8bef8dac50264c2278438a18e5be48328ed1fd1bfb3f9bbee3c522f11258aca3",
      "source": "Residual.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "residual"
    },
    {
      "case_class": "RMSNormParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "rms_norm_pre_ffn",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm"
    },
    {
      "case_class": "GatedMLPParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_gate_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "1896b7ea12ac548124a1a25266baa7d9ea087af21ee60d57633f6843db91a58c",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn"
    },
    {
      "case_class": "GatedMLPParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_up_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "1896b7ea12ac548124a1a25266baa7d9ea087af21ee60d57633f6843db91a58c",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn"
    },
    {
      "case_class": "ElementwiseMulParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "activation_mul",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Elementwise.scala",
      "sha256": "53f25bee2ff7dc030db606d1842a45ddd856b475c388ee82d6260779d4ec8870",
      "source": "Elementwise.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "elementwise"
    },
    {
      "case_class": "GatedMLPParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_down_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "1896b7ea12ac548124a1a25266baa7d9ea087af21ee60d57633f6843db91a58c",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn"
    },
    {
      "case_class": "RMSNormParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "rms_norm_post_ffn",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm"
    },
    {
      "case_class": "ResidualParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "8bef8dac50264c2278438a18e5be48328ed1fd1bfb3f9bbee3c522f11258aca3",
      "source": "Residual.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "residual"
    },
    {
      "case_class": "SoftmaxParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "softmax",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Softmax.scala",
      "sha256": "4f68287b82eab429fa5da62a9d8f3fd1a537f00ef42e364f411e7dd3537e94f2",
      "source": "Softmax.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "softmax"
    },
    {
      "case_class": "AttentionMaskParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "causal_mask",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Mask.scala",
      "sha256": "bfb70e48641d60c25100b8240d5fef461aa954847c5fe5777b7fbb5445fc0e0a",
      "source": "Mask.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "mask"
    }
  ],
  "unsupported_bindings": [
    {
      "kind": "parameter_binding",
      "legality_errors": [
        "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "missing_params": [],
      "op": "gemma3_text_block",
      "template_id": "decoder_block"
    },
    {
      "kind": "parameter_binding",
      "legality_errors": [
        "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "missing_params": [],
      "op": "self_attention",
      "template_id": "attention"
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
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "selected_templates",
      "missing_ops",
      "coverage",
      "checker_results"
    ],
    "constraints": [
      "constraint.model.decoder",
      "constraint.shape.model",
      "constraint.template.library"
    ],
    "id": "template_selection.operator_coverage_engineer",
    "objective": "Check every decoder operator maps to a trusted template and missing coverage is explicit rather than hidden; verify the coverage matrix is backed by checker results, not only a cou...<len=183>",
    "parallel_group": 0,
    "role": "operator coverage engineer",
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
      "mission": "Check every decoder operator maps to a trusted template and missing coverage is explicit rather than hidden; verify the ...<len=183>",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "model_shape"
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
    "title": "Review operator-template coverage"
  },
  {
    "acceptance_checkers": [
      "numeric_compare",
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "parameter_bindings",
      "template_source_checks",
      "supported_bindings",
      "unsupported_bindings"
    ],
    "constraints": [
      "constraint.shape.model",
      "constraint.numeric.policy",
      "constraint.template.library",
      "constraint.arch.design_space"
    ],
    "id": "template_selection.template_binding_engineer",
    "objective": "Check concrete parameter bindings, source file hashes, constructor/interface matches, unsupported bindings, required adapters, and forbidden edits.",
    "parallel_group": 0,
    "role": "template binding engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 3,
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
      "mission": "Check concrete parameter bindings, source file hashes, constructor/interface matches, unsupported bindings, required ada...<len=147>",
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
    "title": "Review strict template bindings"
  },
  {
    "acceptance_checkers": [
      "numeric_compare",
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "attention_semantics",
      "parameter_bindings",
      "checker_results"
    ],
    "constraints": [
      "constraint.model.decoder",
      "constraint.shape.model",
      "constraint.numeric.policy",
      "constraint.cross_layer.input_consistency"
    ],
    "id": "template_selection.attention_semantic_engineer",
    "objective": "Check Q/K/V projection, RoPE, GQA head mapping, softmax, output projection, KV-cache scope, and causal mask binding before the stage can pass.",
    "parallel_group": 0,
    "role": "attention semantic engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 3,
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
      "mission": "Check Q/K/V projection, RoPE, GQA head mapping, softmax, output projection, KV-cache scope, and causal mask binding befo...<len=142>",
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
    "title": "Review attention semantic expansion"
  },
  {
    "acceptance_checkers": [
      "addr_map_check",
      "implementation_package_static",
      "numeric_compare",
      "required_real_tool_evidence_check",
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "cross_layer_trace",
      "checker_results",
      "template_source_checks"
    ],
    "constraints": [
      "constraint.numeric.policy",
      "constraint.memory.board",
      "constraint.runtime.board",
      "constraint.deployment.board"
    ],
    "id": "template_selection.cross_layer_gate_engineer",
    "objective": "Check numeric, board memory, runtime, deployment, and input-consistency constraints are in the template-binding trace and that unresolved risks block the stage.",
    "parallel_group": 1,
    "role": "cross layer gate engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Check numeric, board memory, runtime, deployment, and input-consistency constraints are in the template-binding trace an...<len=160>",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "verification_repair"
    },
    "role_profile": {
      "capabilities": [
        "classify evidence",
        "map failures to violated constraints",
        "enforce repair boundaries"
      ],
      "constraint_focus": [
        "constraint.verification.plan",
        "constraint.human.boundary"
      ],
      "family": "verification_repair"
    },
    "title": "Review cross-layer template gate"
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

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "configured_model": "gpt-6.1-sol",
  "endpoint_configured": true,
  "enforce": true,
  "mode": "llm",
  "model": "gpt-6.1-sol",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
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
