<agent>
model_config_agent
</agent>

<task>
Act as the model and shape intake engineer. Extract the hardware-facing model_config JSON for accelerator design.
</task>

<rules>
1. You are responsible for preventing wrong-model, wrong-layer-count, wrong-head-count, and wrong-operator-order errors from entering the hardware flow.
2. Keep only fields needed by hardware architecture, template selection, shape constraints, and pipeline sizing.
3. Do not invent hidden model semantics.
4. Use the deterministic extractor candidate when it is consistent with the model source.
5. If the human task and model source disagree, preserve the model source facts and record the conflict in notes or equivalent schema-supported fields.
6. Expose attention kind, q/kv head counts, head_dim, position encoding, norm type, MLP type, intermediate size, bias policy, and weight layout when available.
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

<model_source_path>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/qwen2_0_5b/model_config.json
</model_source_path>

<model_source_content>
{
  "model_type": "qwen2",
  "num_layers": 24,
  "hidden_size": 896,
  "target_max_seq_len": 16,
  "block": {
    "type": "decoder",
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
    ]
  },
  "attention": {
    "kind": "gqa",
    "num_q_heads": 14,
    "num_kv_heads": 2,
    "head_dim": 64,
    "causal": true,
    "position_encoding": {
      "type": "rope",
      "rope_theta": 1000000.0
    },
    "qkv_bias": true,
    "out_bias": false
  },
  "norm": {
    "type": "rms_norm",
    "position": "pre",
    "eps": 1e-06,
    "has_bias": false
  },
  "mlp": {
    "type": "gated",
    "intermediate_size": 4864,
    "activation": "silu",
    "up_bias": false,
    "down_bias": false
  },
  "weight_layout": {
    "qkv": "separate_q_k_v",
    "out_proj": "dense",
    "mlp": "gate_up_down",
    "norm": "weight_only"
  }
}

</model_source_content>

<deterministic_extractor_candidate>
{
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
</deterministic_extractor_candidate>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "attention": {
      "additionalProperties": true,
      "type": "object"
    },
    "block": {
      "additionalProperties": true,
      "required": [
        "operator_sequence"
      ],
      "type": "object"
    },
    "hidden_size": {
      "type": "integer"
    },
    "mlp": {
      "additionalProperties": true,
      "type": "object"
    },
    "model_type": {
      "type": "string"
    },
    "norm": {
      "additionalProperties": true,
      "type": "object"
    },
    "num_layers": {
      "type": "integer"
    },
    "target_max_seq_len": {
      "type": "integer"
    }
  },
  "required": [
    "model_type",
    "num_layers",
    "hidden_size",
    "target_max_seq_len",
    "block",
    "attention",
    "norm",
    "mlp"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
