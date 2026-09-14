<agent>
template_selection_agent
</agent>

<task>
Review strict template bindings, source/interface checks, attention semantics, team decomposition, and cross-layer gate risks. Apply candidate_template_selection.stage_gate_policy exactly: report only unresolved current Stage 2 blockers in risks, move later simulation/synthesis/code-generation/board bring-up obligations to proposed_actions or approval_required_for, and return status='ready' with risks=[] only when all current Stage 2 blocks are closed.
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

<candidate_template_selection>
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
      "evidence": {
        "missing_ops": [],
        "required_ops": 9
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_parameter_binding_check",
      "errors": [],
      "evidence": {
        "binding_count": 12
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_source_and_interface_check",
      "errors": [],
      "evidence": {
        "checked_templates": 12
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "attention_semantic_expansion_check",
      "errors": [],
      "evidence": {
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
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "cross_layer_trace_check",
      "errors": [],
      "evidence": {
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
      "status": "pass",
      "warnings": []
    }
  ],
  "constraints_touched": [
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.numeric.policy",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.deployment.board",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.cross_layer.input_consistency"
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
        "input_bits": {
          "dtype": "fp32",
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
        "output_bits": {
          "dtype": "fp32",
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
      "matched_op": "qwen2_block",
      "missing_params": [],
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
      "legality_errors": [],
      "matched_op": "rms_norm",
      "missing_params": [],
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
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "self_attention",
      "missing_params": [],
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
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "residual_add_1",
      "missing_params": [],
      "op": "residual_add_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "role": "operator",
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
      "legality_errors": [],
      "matched_op": "rms_norm",
      "missing_params": [],
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
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "mlp_gate_proj",
      "missing_params": [],
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
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "mlp_up_proj",
      "missing_params": [],
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
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "activation_mul",
      "missing_params": [],
      "op": "activation_mul",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "role": "operator",
      "source": "Elementwise.scala",
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "mlp_down_proj",
      "missing_params": [],
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
      "status": "ready",
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
      "legality_errors": [],
      "matched_op": "residual_add_2",
      "missing_params": [],
      "op": "residual_add_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "status": "ready",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
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
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "matched_op": "softmax",
      "missing_params": [],
      "op": "softmax",
      "required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "role": "attention_submodule",
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
      "matched_op": "causal_mask",
      "missing_params": [],
      "op": "causal_mask",
      "required_params": [
        "seq_len",
        "causal"
      ],
      "role": "attention_submodule",
      "source": "Mask.scala",
      "status": "ready",
      "template_id": "mask"
    }
  ],
  "required_adapters": [],
  "schema_version": "spatialaccagent.template_selection.v0",
  "selected_template_ids": [
    "attention",
    "decoder_block",
    "elementwise",
    "ffn",
    "mask",
    "norm",
    "residual",
    "softmax"
  ],
  "selected_templates": [
    {
      "candidate_template_ids": [
        "decoder_block"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "runtime"
      ],
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
      "candidate_template_ids": [
        "norm"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
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
      "candidate_template_ids": [
        "attention"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "liveness"
      ],
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
      "candidate_template_ids": [
        "residual"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
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
      "candidate_template_ids": [
        "norm"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
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
      "candidate_template_ids": [
        "ffn"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
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
      "candidate_template_ids": [
        "ffn"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
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
      "candidate_template_ids": [
        "elementwise"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
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
      "candidate_template_ids": [
        "ffn"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
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
      "candidate_template_ids": [
        "residual"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
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
      "candidate_template_ids": [
        "softmax"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
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
      "candidate_template_ids": [
        "mask"
      ],
      "constraints_emitted": [
        "shape",
        "stream",
        "beat"
      ],
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
  "supported_bindings": [
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
        "input_bits": {
          "dtype": "fp32",
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
        "output_bits": {
          "dtype": "fp32",
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
      "op": "qwen2_block",
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
      "op": "rms_norm_1",
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
      "op": "self_attention",
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
      "op": "residual_add_1",
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
      "op": "rms_norm_2",
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
      "op": "mlp_gate_proj",
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
      "op": "mlp_up_proj",
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
      "op": "activation_mul",
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
      "op": "mlp_down_proj",
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
      "op": "residual_add_2",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "fp16",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 16
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
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "op": "softmax",
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
      "op": "causal_mask",
      "template_id": "mask"
    }
  ],
  "template_source_checks": [
    {
      "case_class": "LlamaStyleBlockParams",
      "constructor_params": [
        {
          "has_default": true,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "qHeads"
        },
        {
          "has_default": true,
          "name": "kvHeads"
        },
        {
          "has_default": true,
          "name": "headDim"
        },
        {
          "has_default": true,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "inputBits"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "ropeTheta"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
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
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "qwen2_block",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/DecoderBlock.scala",
      "sha256": "29b3b78cbb573e047a74761ec43996fa141a83be3fbdda92e6fd83fa9c11aec2",
      "source": "DecoderBlock.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "decoder_block",
      "warnings": []
    },
    {
      "case_class": "RMSNormParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "inputBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "eps"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "rms_norm_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "a3bcafab8c07f683696fa23b68f139af92b121eebc29b711be7b0db288981476",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm",
      "warnings": []
    },
    {
      "case_class": "AttentionParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "qHeads"
        },
        {
          "has_default": false,
          "name": "kvHeads"
        },
        {
          "has_default": false,
          "name": "headDim"
        },
        {
          "has_default": false,
          "name": "seqLen"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "qkvElemsPerBeat"
        },
        {
          "has_default": true,
          "name": "batchSize"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "self_attention",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Attention.scala",
      "sha256": "d94b29bbf3329e108ccebacf6f3afcabb2d582419981187352fb7b9123dd6b15",
      "source": "Attention.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "attention",
      "warnings": []
    },
    {
      "case_class": "ResidualParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "51b1114e8c133055f04aa516b6e27e4a840b87f598069535df0d4ca543d17059",
      "source": "Residual.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "residual",
      "warnings": []
    },
    {
      "case_class": "RMSNormParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "inputBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "eps"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "rms_norm_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "a3bcafab8c07f683696fa23b68f139af92b121eebc29b711be7b0db288981476",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm",
      "warnings": []
    },
    {
      "case_class": "GatedMLPParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "tileM"
        },
        {
          "has_default": true,
          "name": "tileN"
        },
        {
          "has_default": true,
          "name": "tileK"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "activation"
        },
        {
          "has_default": true,
          "name": "hasBias"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_gate_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "3be3df816e484ee847e8cdfdab01d4f9dcf5b8eaccdb66e3a2d157f89383d1b1",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn",
      "warnings": []
    },
    {
      "case_class": "GatedMLPParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "tileM"
        },
        {
          "has_default": true,
          "name": "tileN"
        },
        {
          "has_default": true,
          "name": "tileK"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "activation"
        },
        {
          "has_default": true,
          "name": "hasBias"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_up_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "3be3df816e484ee847e8cdfdab01d4f9dcf5b8eaccdb66e3a2d157f89383d1b1",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn",
      "warnings": []
    },
    {
      "case_class": "ElementwiseMulParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "activation_mul",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Elementwise.scala",
      "sha256": "b876ae4da79745cd56f747aadcb9dae234718a1d822277a9e172f830818f74e1",
      "source": "Elementwise.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "elementwise",
      "warnings": []
    },
    {
      "case_class": "GatedMLPParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "tileM"
        },
        {
          "has_default": true,
          "name": "tileN"
        },
        {
          "has_default": true,
          "name": "tileK"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "activation"
        },
        {
          "has_default": true,
          "name": "hasBias"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "tile_m",
        "tile_n",
        "tile_k",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_down_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "3be3df816e484ee847e8cdfdab01d4f9dcf5b8eaccdb66e3a2d157f89383d1b1",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn",
      "warnings": []
    },
    {
      "case_class": "ResidualParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "51b1114e8c133055f04aa516b6e27e4a840b87f598069535df0d4ca543d17059",
      "source": "Residual.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "residual",
      "warnings": []
    },
    {
      "case_class": "SoftmaxParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "seqLen"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "fracBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "causal"
        },
        {
          "has_default": true,
          "name": "slidingWindow"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "softmax",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Softmax.scala",
      "sha256": "a9221da8536731d475a36e3eb1bee5ccbaf87f5ffbb22de4691280cf54339d48",
      "source": "Softmax.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "softmax",
      "warnings": []
    },
    {
      "case_class": "AttentionMaskParams",
      "constructor_params": [
        {
          "has_default": false,
          "name": "seqLen"
        },
        {
          "has_default": true,
          "name": "causal"
        },
        {
          "has_default": true,
          "name": "slidingWindow"
        },
        {
          "has_default": true,
          "name": "globalEvery"
        }
      ],
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "seq_len",
        "causal"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "causal_mask",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Mask.scala",
      "sha256": "bfb70e48641d60c25100b8240d5fef461aa954847c5fe5777b7fbb5445fc0e0a",
      "source": "Mask.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "mask",
      "warnings": []
    }
  ],
  "unsupported_bindings": [],
  "warnings": []
}
</candidate_template_selection>

<design_team>
{
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/team/team_aggregate.json",
  "approval_required_for": [
    "Changing KV-cache scope from not_required to enabled, or introducing any KV-cache memory/runtime layout.",
    "Changing attention architecture parameters after promotion, including num_q_heads, num_kv_heads, head_dim, seq_len, rope_theta, GQA grouping, or lanes.",
    "Changing numeric policy or bound widths, including activation elem_bits, accumulator/input_bits, or decoder residual output_bits.",
    "Replacing trusted attention templates, modifying template internals, changing data order, or adding free-form RTL for QKV projection, RoPE, softmax, mask, output projection, or GQA mapping.",
    "future architecture/design-space changes that alter lanes or tile sizes",
    "future major template substitutions, new required adapters, or edits to trusted template internals",
    "future memory layout, data-order, board memory, or board runtime assumption changes",
    "future numeric policy, precision, tolerance, or residual-stream width changes"
  ],
  "completed_subtasks": 4,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "template_binding_static_check"
      ],
      "action_type": "stage_gate_promotion",
      "consumes": [
        "candidate_stage_artifact",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "constraint.model.decoder",
        "constraint.shape.model",
        "constraint.numeric.policy",
        "constraint.template.library",
        "constraint.cross_layer.input_consistency",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.deployment.board"
      ],
      "id": "template_selection.promote_attention_semantic_binding",
      "on_failure": "Block promotion to cross_layer_gate_engineer, record the failed constraint edge in SACG memory, and open a bounded template_selection retry rather than modifying templates or golden outputs.",
      "produces": [
        "attention_semantic_expansion_review",
        "head_mapping_consistency_decision",
        "attention_submodule_template_coverage_decision",
        "template_selection.cross_layer_gate_handoff"
      ],
      "rationale": "All supplied current-stage deterministic checker results pass, attention submodule coverage is complete or explicitly not_required, and parameter bindings are sourced from SACG constraints rather than implicit defaults.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "boundary_contract_check",
        "human_boundary_check"
      ],
      "action_type": "handoff_guard",
      "consumes": [
        "candidate_stage_artifact.attention_semantics",
        "constraint.model.decoder",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "template_selection.record_kv_cache_scope_guard",
      "on_failure": "Treat any attempted KV-cache enablement or hidden cache allocation as a memory-layout/architecture change requiring explicit approval before downstream consumption.",
      "produces": [
        "template_selection.kv_cache_scope_guard",
        "memory_runtime_plan.kv_cache_not_required_constraint"
      ],
      "rationale": "The supplied attention semantics explicitly mark KV-cache as not_required. This scope must be preserved for memory/runtime planning so later stages do not allocate or depend on cache state without approved architecture and memory-layout changes.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "memory_runtime_plan_check",
        "boundary_contract_check",
        "human_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "code_generation_manifest_static_check",
        "codegen_contract_check",
        "artifact_hash_check"
      ],
      "action_type": "codegen_contract_check",
      "consumes": [
        "attention_semantic_expansion_review",
        "head_mapping_consistency_decision",
        "attention_submodule_template_coverage_decision",
        "candidate_stage_artifact.template_source_checks",
        "candidate_stage_artifact.parameter_bindings"
      ],
      "id": "code_generation.preserve_attention_template_bindings",
      "on_failure": "Stop code generation promotion, localize the mismatched template/source/parameter edge, and route to bounded_template_repair with repair_boundary_check; do not alter trusted template internals without approval.",
      "produces": [
        "code_generation.attention_binding_manifest",
        "code_generation.attention_template_hash_manifest"
      ],
      "rationale": "The current approval depends on trusted template and embedded-submodule coverage. Code generation must preserve source/template IDs, parameter values, and artifact hashes for attention modules rather than generating free-form replacement RTL.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "code_generation_manifest_static_check",
        "codegen_contract_check",
        "artifact_hash_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "numeric_compare",
        "data_order_trace_check"
      ],
      "action_type": "downstream_verification_plan",
      "consumes": [
        "attention_semantic_expansion_review",
        "head_mapping_consistency_decision",
        "attention_submodule_template_coverage_decision",
        "artifact.input.case_adapter",
        "verification_artifact_contract",
        "generated_attention_or_decoder_artifacts"
      ],
      "id": "verification.plan_attention_numeric_compare",
      "on_failure": "Do not promote to multilayer or board verification. Apply the three-layer repair loop: localize first at attention/operator leaf modules, then the connected single-transformer-layer kernel, and only after those pass proceed toward board-accurate AXI/DDR wrapping.",
      "produces": [
        "verification.attention_leaf_numeric_compare_report",
        "verification.single_layer_attention_numeric_compare_report",
        "verification.attention_data_order_trace_report"
      ],
      "rationale": "numeric_compare is not part of the supplied template-selection evidence and must be executed only after generated artifacts, verification contracts, and golden/reference tensors exist. This validates the semantic binding at leaf and connected single-layer levels before any board-accurate promotion.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "numeric_compare",
        "data_order_trace_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_coverage_check",
        "template_binding_static_check",
        "sacg_reference_check"
      ],
      "action_type": "stage_gate_validation_and_promotion",
      "consumes": [
        "candidate_stage_artifact",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.input.target_board_profile",
        "state_summary.constraints"
      ],
      "id": "template_selection.finalize_operator_coverage_review",
      "on_failure": "Do not promote to cross-layer gate. Localize the failed operator, parameter, source file, or SACG edge; if the gap is within approved template metadata/binding repair bounds route to bounded_template_repair, otherwise raise stage_backtrack_request rather than using free-form RTL.",
      "produces": [
        "operator_template_coverage_review",
        "coverage_gap_or_pass_decision",
        "SACG constraint references for every covered operator"
      ],
      "rationale": "Finalize the current candidate as a bounded operator-template coverage artifact by checking SACG references, selected template coverage, and template parameter/source binding using the registered acceptance checkers before cross-layer gate consumption.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "sacg_static_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "template_coverage_check",
        "template_binding_static_check"
      ],
      "action_type": "handoff_package_generation",
      "consumes": [
        "operator_template_coverage_review",
        "coverage_gap_or_pass_decision",
        "candidate_stage_artifact.cross_layer_trace",
        "candidate_stage_artifact.forbidden_edits"
      ],
      "id": "template_selection.handoff_coverage_to_cross_layer_gate",
      "on_failure": "Keep the artifact in template_selection and regenerate the handoff package with missing SACG references or explicit blocker classification; do not rely on human memory or downstream inference to recover coverage evidence.",
      "produces": [
        "template_selection.cross_layer_gate_handoff",
        "operator_coverage_sacg_focus"
      ],
      "rationale": "Package the ready coverage decision for template_selection.cross_layer_gate_engineer while preserving the no-free-form-RTL barrier and all model, shape, numeric, memory, runtime, deployment, and cross-layer references needed for the next gate.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "team_aggregate",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "template_binding_static_check",
        "artifact_hash_check",
        "repair_boundary_check"
      ],
      "action_type": "static_gate_promotion",
      "consumes": [
        "candidate_stage_artifact",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.input.target_board_profile",
        "artifact.input.human_agent_boundary",
        "state_summary.sacg_memory"
      ],
      "id": "template_selection.promote_template_binding_static_gate",
      "on_failure": "Block promotion to the cross-layer gate; localize the failed binding/source/hash/boundary evidence, emit a bounded same-stage retry request, and do not edit golden outputs, loosen tolerance, or modify template internals without required approval.",
      "produces": [
        "artifact.template_selection.template_parameter_binding_review",
        "artifact.template_selection.template_source_interface_review",
        "artifact.template_selection.forbidden_edit_boundary_decision",
        "artifact.template_selection.promoted_template_selection_contract"
      ],
      "rationale": "Seal the reviewed candidate as the promoted template-selection contract using registry-grounded static gates for SACG trace, numeric policy, parameter binding, template binding, source hash evidence, and repair boundaries. This preserves the current pass evidence and prevents downstream consumption of an unsealed retry or mutated artifact.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "sacg_static_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "artifact_hash_check",
        "repair_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_binding_static_check",
        "repair_boundary_check"
      ],
      "action_type": "handoff",
      "consumes": [
        "artifact.template_selection.promoted_template_selection_contract",
        "artifact.template_selection.template_parameter_binding_review",
        "artifact.template_selection.template_source_interface_review",
        "artifact.template_selection.forbidden_edit_boundary_decision",
        "candidate_stage_artifact.checker_results"
      ],
      "id": "template_selection.handoff_to_cross_layer_gate_engineer",
      "on_failure": "Keep the artifact in template_selection; rerun the failed static checker with the same SACG constraints and route any concrete contradiction to bounded_template_repair or stage_backtrack_request before downstream consumption.",
      "produces": [
        "artifact.template_selection.cross_layer_gate_handoff_packet"
      ],
      "rationale": "The stage_gate_policy allows ready status when deterministic checker results pass and no current-stage blocks remain. Handoff should give the cross-layer gate engineer the sealed template binding and forbidden-edit decision while keeping later simulation/backend actions out of the current-stage risk set.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "team_aggregate",
        "sacg_validate"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_memory_check",
        "stage_artifact_trust_barrier_check"
      ],
      "action_type": "sacg_memory_update",
      "consumes": [
        "candidate_stage_artifact",
        "artifact.template_selection.promoted_template_selection_contract",
        "state_summary.sacg_memory"
      ],
      "id": "template_selection.record_ready_outcome_in_sacg_memory",
      "on_failure": "Do not create a false pass memory record; keep the promoted contract as the authoritative artifact and rerun sacg_memory_update before later-stage aggregation.",
      "produces": [
        "artifact.sacg_memory.template_selection_ready_outcome"
      ],
      "rationale": "Record the ready outcome, absence of open barriers/backtracks/retries, and forbidden-edit boundaries in SACG memory so downstream agents do not rely on natural-language memory or stale failed artifacts.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "sacg_memory_update",
        "stage_artifact_trust_barrier"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "template_binding_static_check",
        "memory_runtime_plan_check",
        "addr_map_check",
        "deployment_board_check",
        "human_boundary_check"
      ],
      "action_type": "stage_gate_evidence_audit",
      "consumes": [
        "candidate_stage_artifact.cross_layer_trace",
        "candidate_stage_artifact.checker_results",
        "candidate_stage_artifact.stage_gate_policy",
        "candidate_stage_artifact.selected_templates",
        "candidate_stage_artifact.parameter_bindings",
        "candidate_stage_artifact.template_source_checks",
        "candidate_stage_artifact.forbidden_edits",
        "state_summary.constraints",
        "state_summary.sacg_memory"
      ],
      "id": "template_selection.final_cross_layer_gate_audit",
      "on_failure": "Block promotion to code_generation, localize the failure to the missing or contradictory constraint/template/parameter/source/board fact, and issue a bounded repair request; do not reclassify absent VCS, Vivado, runtime, or board-run evidence as a template-selection failure.",
      "produces": [
        "template_selection_stage_gate_audit",
        "cross_layer_trace_decision",
        "repair_or_ready_classification"
      ],
      "rationale": "Aggregate the supplied checker evidence and stage_gate_policy to confirm that the required numeric, memory-board, runtime-board, deployment-board, and input-consistency constraints are present in the template-selection trace without claiming later hardware or simulation success.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "sacg_static_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "memory_runtime_plan_check",
        "addr_map_check",
        "deployment_board_check",
        "human_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "code_generation_manifest_static_check",
        "codegen_contract_check",
        "codegen_package_static_check",
        "sacg_reference_check"
      ],
      "action_type": "handoff_contract_generation",
      "consumes": [
        "template_selection_stage_gate_audit",
        "candidate_stage_artifact.selected_templates",
        "candidate_stage_artifact.parameter_bindings",
        "candidate_stage_artifact.template_source_checks",
        "candidate_stage_artifact.cross_layer_trace",
        "candidate_stage_artifact.forbidden_edits"
      ],
      "id": "code_generation.prepare_bound_template_contract",
      "on_failure": "Hold at code_generation and return the bounded mismatch to the template-selection/codegen contract owner; do not modify golden outputs, loosen tolerance, or change numeric, memory, runtime, board, or template policy without approval.",
      "produces": [
        "artifact.next_stage.code_generation_manifest",
        "artifact.next_stage.codegen_contract",
        "artifact.next_stage.sacg_reference_map"
      ],
      "rationale": "The next stage should materialize a code-generation contract from trusted selected templates while preserving SACG references for model shape, numeric policy, memory board, runtime board, deployment board, and input-consistency facts.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "code_generation_manifest_static_check",
        "codegen_contract_check",
        "codegen_package_static_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_action_audit_check",
        "verification_plan_static_check",
        "tool_protocol_check",
        "human_boundary_check"
      ],
      "action_type": "stage_boundary_annotation",
      "consumes": [
        "template_selection_stage_gate_audit",
        "candidate_stage_artifact.stage_gate_policy",
        "candidate_stage_artifact.cross_layer_trace_decision"
      ],
      "id": "stage_orchestrator.record_later_stage_gap_classification",
      "on_failure": "Keep the handoff annotation unresolved and require orchestrator correction; do not add a current-stage risk unless a checker reports a concrete contradiction against the template-selection artifact or named SACG constraints.",
      "produces": [
        "artifact.stage_boundary.not_current_stage_gap_classification"
      ],
      "rationale": "Record that missing implementation, simulation, backend, runtime, and board-bring-up evidence is classified by the supplied stage_gate_policy as later-stage work so it is not misreported as a current template-selection failure.",
      "requires_approval": false,
      "stage": "stage_orchestrator",
      "tool_roles": [
        "team_aggregate",
        "verification_action_audit",
        "verification_plan_static_check",
        "tool_protocol_check",
        "human_boundary_check"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 12,
    "max_duration_sec": 459.0332762219987,
    "max_prompt_bytes": 54951,
    "result_count": 4,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 1181.1690842299977,
    "total_prompt_bytes": 218715
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 4,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/constraint_extraction/initial_design_graph.json
</source_sacg_state>

<stage_gate_policy>
{
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
}
</stage_gate_policy>

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
