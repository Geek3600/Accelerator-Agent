<agent>
model_shape_specialist_compact_retry
</agent>

<task>
Verify every Qwen2 decoder operator and the block wrapper are bound to trusted templates or explicit required adapters, with no hidden missing coverage and no free-form RTL substitution.
</task>

<rules>
1. This is a compact retry after transient provider failures.
2. Use only the compact inputs and named constraints.
3. If compact inputs include checker_results, parameter_bindings, template_source_checks, attention_semantics, or cross_layer_trace, treat those fields as supplied evidence.
4. If compact inputs include candidate_verification_artifact_contract, candidate_verification_plan, retry_reconciliation_contract, or design_team, treat their visible status, summary, policy, node counts, error lists, and checker summaries as supplied Stage6 evidence; do not claim the evidence is absent merely because compact retry omitted full nested details.
5. If compact inputs include stage_gate_policy, report only current-stage blockers in risks and move later-stage obligations to proposed_actions.
6. Return conservative review findings; mark evidence as not_run only when the relevant field is absent from compact inputs.
7. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible.
8. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name>; do not invent free-form tool roles such as verification_planner or tool_runner.
9. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
10. Return one JSON object only.
</rules>

<stage>
template_selection.operator coverage engineer
</stage>

<agent>
model_shape_specialist
</agent>

<compact_inputs>
{
  "agent": "model_shape_specialist",
  "candidate_stage_artifact": {
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
        "errors": [
          "qwen2_block/decoder_block: numeric constructor params are not bound despite numeric elem_bits=16: ['elemBits', 'inputBits', 'outputBits']"
        ],
        "status": "fail",
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
    "errors": [
      "qwen2_block/decoder_block: numeric constructor params are not bound despite numeric elem_bits=16: ['elemBits', 'inputBits', 'outputBits']"
    ],
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
          "head_dim": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.head_dim",
            "status": "bound",
            "value": 64
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "intermediate_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.intermediate_size",
            "status": "bound",
            "value": 4864
          },
          "num_kv_heads": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.num_kv_heads",
            "status": "bound",
            "value": 2
          },
          "num_q_heads": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.num_q_heads",
            "status": "bound",
            "value": 14
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "qwen2_block",
        "required_params": [],
        "role": null,
        "source": "DecoderBlock.scala",
        "status": "ready",
        "template_id": "decoder_block"
      },
      {
        "bound_params": {
          "eps": {
            "candidate_values": null,
            "legal_values": null,
            "source": "artifact.input.model_config.norm.eps",
            "status": "bound",
            "value": 1e-06
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "input_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.acc_dtype",
            "status": "bound",
            "value": 32
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "output_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "rms_norm_1",
        "required_params": [],
        "role": null,
        "source": "Norm.scala",
        "status": "ready",
        "template_id": "norm"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "head_dim": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.head_dim",
            "status": "bound",
            "value": 64
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "num_kv_heads": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.num_kv_heads",
            "status": "bound",
            "value": 2
          },
          "num_q_heads": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.num_q_heads",
            "status": "bound",
            "value": 14
          },
          "seq_len": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.target_max_seq_len",
            "status": "bound",
            "value": 16
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "self_attention",
        "required_params": [],
        "role": null,
        "source": "Attention.scala",
        "status": "ready",
        "template_id": "attention"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "residual_add_1",
        "required_params": [],
        "role": null,
        "source": "Residual.scala",
        "status": "ready",
        "template_id": "residual"
      },
      {
        "bound_params": {
          "eps": {
            "candidate_values": null,
            "legal_values": null,
            "source": "artifact.input.model_config.norm.eps",
            "status": "bound",
            "value": 1e-06
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "input_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.acc_dtype",
            "status": "bound",
            "value": 32
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "output_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "rms_norm_2",
        "required_params": [],
        "role": null,
        "source": "Norm.scala",
        "status": "ready",
        "template_id": "norm"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "intermediate_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.intermediate_size",
            "status": "bound",
            "value": 4864
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "tile_k": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.common_matmul_tile_k_candidates",
            "status": "bound",
            "value": 32
          },
          "tile_m": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.seq_tile_m_candidates",
            "status": "bound",
            "value": 1
          },
          "tile_n": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up_tile_n_candidates",
            "status": "bound",
            "value": 32
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "mlp_gate_proj",
        "required_params": [],
        "role": null,
        "source": "FFN.scala",
        "status": "ready",
        "template_id": "ffn"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "intermediate_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.intermediate_size",
            "status": "bound",
            "value": 4864
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "tile_k": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.common_matmul_tile_k_candidates",
            "status": "bound",
            "value": 32
          },
          "tile_m": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.seq_tile_m_candidates",
            "status": "bound",
            "value": 1
          },
          "tile_n": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_gate_up_tile_n_candidates",
            "status": "bound",
            "value": 32
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "mlp_up_proj",
        "required_params": [],
        "role": null,
        "source": "FFN.scala",
        "status": "ready",
        "template_id": "ffn"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.intermediate_size",
            "status": "bound",
            "value": 4864
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "activation_mul",
        "required_params": [],
        "role": null,
        "source": "Elementwise.scala",
        "status": "ready",
        "template_id": "elementwise"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "intermediate_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.intermediate_size",
            "status": "bound",
            "value": 4864
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "tile_k": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.common_matmul_tile_k_candidates",
            "status": "bound",
            "value": 32
          },
          "tile_m": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.seq_tile_m_candidates",
            "status": "bound",
            "value": 1
          },
          "tile_n": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params.tile_sizes.ffn_down_tile_n_candidates",
            "status": "bound",
            "value": 32
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "mlp_down_proj",
        "required_params": [],
        "role": null,
        "source": "FFN.scala",
        "status": "ready",
        "template_id": "ffn"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "hidden_size": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.hidden_size",
            "status": "bound",
            "value": 896
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "residual_add_2",
        "required_params": [],
        "role": null,
        "source": "Residual.scala",
        "status": "ready",
        "template_id": "residual"
      },
      {
        "bound_params": {
          "elem_bits": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.numeric.policy.default_rules.activation_dtype",
            "status": "bound",
            "value": 16
          },
          "lanes": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
            "status": "bound",
            "value": 8
          },
          "seq_len": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.target_max_seq_len",
            "status": "bound",
            "value": 16
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "softmax",
        "required_params": [],
        "role": null,
        "source": "Softmax.scala",
        "status": "ready",
        "template_id": "softmax"
      },
      {
        "bound_params": {
          "causal": {
            "candidate_values": null,
            "legal_values": null,
            "source": "artifact.input.model_config.attention.causal",
            "status": "bound",
            "value": true
          },
          "seq_len": {
            "candidate_values": null,
            "legal_values": null,
            "source": "constraint.shape.model.target_max_seq_len",
            "status": "bound",
            "value": 16
          }
        },
        "legality_errors": [],
        "matched_op": null,
        "missing_params": [],
        "op": "causal_mask",
        "required_params": [],
        "role": null,
        "source": "Mask.scala",
        "status": "ready",
        "template_id": "mask"
      }
    ],
    "required_adapters": [],
    "schema_version": "spatialaccagent.template_selection.v0",
    "selected_template_ids": [],
    "selected_templates": [
      {
        "matched_op": "qwen2_block",
        "op": "qwen2_block",
        "required_params": [
          "hidden_size",
          "intermediate_size",
          "num_q_heads",
          "num_kv_heads",
          "head_dim"
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
    "status": "incomplete",
    "template_source_checks": [
      {
        "case_class": "LlamaStyleBlockParams",
        "errors": [
          "numeric constructor params are not bound despite numeric elem_bits=16: ['elemBits', 'inputBits', 'outputBits']"
        ],
        "exists": true,
        "metadata_required_params": [],
        "missing_required_params_in_constructor": [],
        "numeric_constructor_params_not_bound_by_metadata": [
          "elemBits",
          "inputBits",
          "outputBits"
        ],
        "op": "qwen2_block",
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/DecoderBlock.scala",
        "sha256": "29b3b78cbb573e047a74761ec43996fa141a83be3fbdda92e6fd83fa9c11aec2",
        "source": "DecoderBlock.scala",
        "source_required_params_missing_from_metadata": [],
        "status": "fail",
        "template_id": "decoder_block"
      },
      {
        "case_class": "RMSNormParams",
        "errors": [],
        "exists": true,
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "metadata_required_params": [],
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
        "errors": [
          "numeric constructor params are not bound despite numeric elem_bits=16: ['elemBits', 'inputBits', 'outputBits']"
        ],
        "kind": "template_interface",
        "op": "qwen2_block",
        "template_id": "decoder_block"
      }
    ],
    "warnings": []
  },
  "stage": "template_selection.operator coverage engineer",
  "state_summary": {
    "_more_keys": 6,
    "constraints": {
      "_size": 16,
      "_type": "list"
    }
  },
  "subtask": {
    "_more_keys": 5,
    "acceptance_checkers": {
      "_size": 4,
      "_type": "list"
    },
    "agent": "model_shape_specialist",
    "artifact_focus": {
      "_size": 6,
      "_type": "list"
    },
    "constraints": {
      "_size": 4,
      "_type": "list"
    },
    "objective": "Verify every Qwen2 decoder operator and the block wrapper are bound to trusted templates or explicit required adapters, ...<len=186>",
    "role": "operator coverage engineer",
    "title": "Audit decoder operator-to-template coverage"
  },
  "team_context": {
    "_more_keys": 2,
    "objective": "Strictly bind trusted templates to every model operator, source file, parameter, attention semantic, and cross-layer boa...<len=189>",
    "stage": "template_selection"
  }
}
</compact_inputs>

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
