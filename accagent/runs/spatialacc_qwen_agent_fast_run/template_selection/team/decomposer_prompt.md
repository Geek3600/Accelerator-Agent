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
4. Each subtask must declare action_type, expected_artifacts, acceptance_checkers, handoff_to, and handoff_rule.
5. Every subtask must focus on cross-layer consistency, template binding, checker evidence, implementation/deployment evidence, or repair boundaries.
6. Ground acceptance_checkers and tool-oriented roles in action_grounding_registry. Use exact canonical names whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
7. If a required checker/tool is missing, mark the subtask handoff as requiring planned_tool.<short_name> or planned_checker.<short_name> implementation.
8. Do not create agents for generic brainstorming, paper writing, marketing, or unrelated code cleanup.
9. Use the reference subtask plan as a formatting and role-coverage guide; the actual split decision must come from the LLM response.
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
        "required": true,
        "source": "DecoderBlock.scala",
        "status": "covered"
      },
      {
        "component": "rope",
        "evidence_pattern": "Module(new RoPE",
        "required": true,
        "source": "DecoderBlock.scala",
        "status": "covered"
      },
      {
        "component": "gqa_head_mapping",
        "evidence_pattern": "kvGroupSize",
        "gqa_group_size": 7,
        "params": {
          "num_kv_heads": 2,
          "num_q_heads": 14
        },
        "required": true,
        "source": "QKVProjection.scala",
        "status": "covered"
      },
      {
        "component": "softmax",
        "evidence_pattern": "template_id=softmax",
        "required": true,
        "source": "Softmax.scala",
        "status": "covered"
      },
      {
        "component": "output_projection",
        "evidence_pattern": "Module(new Linear(p.outLinear)",
        "required": true,
        "source": "DecoderBlock.scala",
        "status": "covered"
      },
      {
        "component": "kv_cache",
        "evidence_pattern": "Module(new KVCache",
        "required": false,
        "source": "DecoderBlock.scala",
        "status": "not_required"
      },
      {
        "component": "causal_mask",
        "evidence_pattern": "template_id=mask",
        "required": true,
        "source": "Mask.scala",
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
      "errors": [],
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_source_and_interface_check",
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
    "covered_ops": 9,
    "has_block_wrapper": true,
    "required_ops": 9
  },
  "cross_layer_trace": {
    "constraints": [
      {
        "constraint": "constraint.numeric.policy",
        "fact_keys": [
          "_llm_provenance",
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
  "errors": [],
  "forbidden_edits": [
    "Do not close missing template coverage with free-form RTL.",
    "Do not rely on Chisel default constructor values when a model, numeric, or board value is available.",
    "Do not change template internals, data order, memory layout, numeric policy, or board/runtime assumptions without approval."
  ],
  "library_id": "spatialaccagent_chisel_templates_v0",
  "missing_ops": [],
  "model_type": "qwen2",
  "operator_sequence": [
    "rms_norm_1",
    "self_attention",
    "residual_add_1",
    "rms_norm_2",
    "mlp_gate_proj",
    "mlp_up_proj",
    "activation_mul",
    "mlp_down_proj",
    "residual_add_2"
  ],
  "parameter_bindings": [
    {
      "bound_params": {
        "elem_bits": {
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
        "input_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 4864
        },
        "lanes": {
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
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype (decoder block residual stream)",
          "status": "bound",
          "value": 32
        },
        "rope_theta": {
          "source": "constraint.model.decoder.position_encoding.rope_theta",
          "status": "bound",
          "value": 1000000.0
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "qwen2_block",
      "source": "DecoderBlock.scala",
      "status": "ready",
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
          "value": 896
        },
        "input_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "rms_norm_1",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "elem_bits": {
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
      "legality_errors": [],
      "missing_params": [],
      "op": "self_attention",
      "source": "Attention.scala",
      "status": "ready",
      "template_id": "attention"
    },
    {
      "bound_params": {
        "elem_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
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
          "value": 896
        },
        "input_bits": {
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "output_bits": {
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "missing_params": [],
      "op": "rms_norm_2",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "elem_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "tile_k": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_k_candidates",
          "status": "bound",
          "value": 128
        },
        "tile_m": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_m_candidates",
          "status": "bound",
          "value": 16
        },
        "tile_n": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_n_candidates",
          "status": "bound",
          "value": 128
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
        "elem_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "tile_k": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_k_candidates",
          "status": "bound",
          "value": 128
        },
        "tile_m": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_m_candidates",
          "status": "bound",
          "value": 16
        },
        "tile_n": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up.tile_n_candidates",
          "status": "bound",
          "value": 128
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
          "value": 16
        },
        "hidden_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 4864
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
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
        "elem_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
        },
        "tile_k": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down.tile_k_candidates",
          "status": "bound",
          "value": 128
        },
        "tile_m": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down.tile_m_candidates",
          "status": "bound",
          "value": 16
        },
        "tile_n": {
          "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down.tile_n_candidates",
          "status": "bound",
          "value": 128
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
        "elem_bits": {
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
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
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
          "value": 16
        },
        "lanes": {
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "bound",
          "value": 8
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
      "matched_op": "qwen2_block",
      "op": "qwen2_block",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "input_bits",
        "elem_bits",
        "output_bits",
        "rope_theta"
      ],
      "role": "block_wrapper",
      "source": "DecoderBlock.scala",
      "template_id": "decoder_block"
    },
    {
      "matched_op": "rms_norm",
      "op": "rms_norm_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps"
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
        "elem_bits"
      ],
      "role": "operator",
      "source": "Attention.scala",
      "template_id": "attention"
    },
    {
      "matched_op": "residual_add_1",
      "op": "residual_add_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "template_id": "residual"
    },
    {
      "matched_op": "rms_norm",
      "op": "rms_norm_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps"
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
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
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
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
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
        "elem_bits"
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
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "template_id": "ffn"
    },
    {
      "matched_op": "residual_add_2",
      "op": "residual_add_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
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
    "classification_rule": "Put only unresolved current_stage_blocks in risks. Put not_current_stage_blocks in proposed_actions or approval_required_for. If all deterministic checker_results pass and no current_stage_blocks remain, return status='ready' and risks=[].",
    "current_stage_blocks": [
      "any decoder operator has no trusted selected template or explicit required adapter",
      "any selected template required parameter is unbound, illegal, or only supplied by an implicit constructor default when model/numeric/board input has a value",
      "any selected template source file is missing or its metadata required parameters do not match the Chisel case-class constructor",
      "self_attention lacks selected or embedded coverage for Q/K/V projection, RoPE when required, GQA/MQA head mapping, softmax, output projection, required KV-cache behavior, or causal mask",
      "numeric policy, board memory, board runtime, board deployment, or cross-layer input-consistency constraints are absent from the template-selection trace",
      "LLM sub-agent output reports a concrete contradiction in the candidate selection for this stage"
    ],
    "not_current_stage_blocks": [
      "VCS/Verilator simulation has not been run yet",
      "Vivado synthesis, implementation, timing closure, or bitstream generation has not been run yet",
      "final generated accelerator code has not been emitted yet",
      "runtime driver, board wrapper, or full DDR/AXI top-level integration has not been generated yet",
      "later-stage numeric accuracy or board bring-up evidence is not present yet"
    ],
    "schema_version": "spatialaccagent.stage2_gate_policy.v0"
  },
  "status": "ready",
  "template_source_checks": [
    {
      "case_class": "LlamaStyleBlockParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "qwen2_block",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/DecoderBlock.scala",
      "sha256": "29b3b78cbb573e047a74761ec43996fa141a83be3fbdda92e6fd83fa9c11aec2",
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
      "op": "rms_norm_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "a3bcafab8c07f683696fa23b68f139af92b121eebc29b711be7b0db288981476",
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
      "sha256": "d94b29bbf3329e108ccebacf6f3afcabb2d582419981187352fb7b9123dd6b15",
      "source": "Attention.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "attention"
    },
    {
      "case_class": "ResidualParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "51b1114e8c133055f04aa516b6e27e4a840b87f598069535df0d4ca543d17059",
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
      "op": "rms_norm_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "a3bcafab8c07f683696fa23b68f139af92b121eebc29b711be7b0db288981476",
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
      "sha256": "3be3df816e484ee847e8cdfdab01d4f9dcf5b8eaccdb66e3a2d157f89383d1b1",
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
      "sha256": "3be3df816e484ee847e8cdfdab01d4f9dcf5b8eaccdb66e3a2d157f89383d1b1",
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
      "sha256": "b876ae4da79745cd56f747aadcb9dae234718a1d822277a9e172f830818f74e1",
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
      "sha256": "3be3df816e484ee847e8cdfdab01d4f9dcf5b8eaccdb66e3a2d157f89383d1b1",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn"
    },
    {
      "case_class": "ResidualParams",
      "errors": [],
      "exists": true,
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "51b1114e8c133055f04aa516b6e27e4a840b87f598069535df0d4ca543d17059",
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
      "sha256": "a9221da8536731d475a36e3eb1bee5ccbaf87f5ffbb22de4691280cf54339d48",
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
  "unsupported_bindings": []
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
    "title": "Review attention semantic expansion"
  },
  {
    "acceptance_checkers": [
      "addr_map_check",
      "implementation_package_static",
      "numeric_compare",
      "real_tool_evidence_check",
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
