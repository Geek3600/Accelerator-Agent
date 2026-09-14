<agent>
task_card_agent
</agent>

<task>
Act as the design-run coordinator. Create the task_card JSON for a complete board-runnable spatial accelerator design run.
</task>

<rules>
1. The task card is the handoff from the human request to the chip-design team.
2. The top-level object is the task card itself.
3. Do not wrap the task card in a task_card, result, or output field.
4. The run target is a complete accelerator through board execution, not a partial simulation-only run.
5. Required outputs should include generated accelerator code, tool evidence, bitstream evidence, and board-valid output evidence when applicable.
6. Acceptance policy should reflect no-deadlock and valid-output requirements unless the task explicitly asks for bit-exact numeric matching.
</rules>

<human_task_spec>
Design a complete board-runnable spatial accelerator for a Qwen2-style decoder-only LLM.

The target model source is Qwen2-0.5B style: 24 decoder layers, hidden_size 896, grouped-query attention
with 14 query heads and 2 KV heads, head_dim 64, RoPE, RMSNorm, and gated SiLU MLP. The first automation
target uses target_max_seq_len 16 from the model_config.

The framework must generate a Qwen spatial accelerator design package from trusted Chisel templates, elaborate
SystemVerilog, run real Vivado synthesis/implementation/bitstream generation on server 23 for the VU9P board part,
and record all tool evidence. Do not run OPT full-sequence verification as Qwen evidence, and do not claim board
runtime pass until a Qwen AXI/DDR board wrapper is connected and checked.

</human_task_spec>

<hardware_model_facts>
{
  "_llm_provenance": {
    "mode": "llm",
    "sub_agent": "model_config_agent",
    "used_fallback": false
  },
  "attention": {
    "causal": true,
    "head_dim": 64,
    "kind": "gqa",
    "num_kv_heads": 2,
    "num_q_heads": 14,
    "out_bias": false,
    "position_encoding": {
      "rope_theta": 1000000.0,
      "type": "rope"
    },
    "qkv_bias": true
  },
  "block": {
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
    "type": "decoder"
  },
  "hidden_size": 896,
  "mlp": {
    "activation": "silu",
    "down_bias": false,
    "intermediate_size": 4864,
    "type": "gated",
    "up_bias": false
  },
  "model_type": "qwen2",
  "norm": {
    "eps": 1e-06,
    "has_bias": false,
    "position": "pre",
    "type": "rms_norm"
  },
  "num_layers": 24,
  "target_max_seq_len": 16,
  "weight_layout": {
    "mlp": "gate_up_down",
    "norm": "weight_only",
    "out_proj": "dense",
    "qkv": "separate_q_k_v"
  }
}
</hardware_model_facts>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "acceptance_policy": {
      "additionalProperties": true,
      "type": "object"
    },
    "design_goal": {
      "type": "string"
    },
    "human_inputs": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "notes": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "required_outputs": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "schema_version": {
      "type": "string"
    },
    "target_layers": {
      "type": "integer"
    },
    "target_model": {
      "type": "string"
    },
    "target_seq_len": {
      "type": "integer"
    }
  },
  "required": [
    "schema_version",
    "target_model",
    "target_layers",
    "target_seq_len",
    "design_goal",
    "human_inputs",
    "notes"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
