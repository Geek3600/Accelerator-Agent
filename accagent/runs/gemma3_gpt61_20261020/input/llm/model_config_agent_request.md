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
# Gemma FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied Gemma checkpoint and its complete decoder Transformer-block workload. Derive the model architecture, tensor shapes, layer count, sequence length, checkpoint tensor names, and operator order from the supplied model source and checkpoint; do not substitute GPT-2 or fixed project dimensions.

Run the complete public Stage 0--7 workflow with real tools and the supplied VU9P board sample project. Preserve the established OPT-aligned architecture and schedule: W4A8 signed INT4 weights, INT8 activations, INT32 accumulation and integer DSP MACs; complete weights in external DDR; 512-bit DDR loader and refill; bounded active/shadow weight caches; prefetch of the next layer/tile; activation ping-pong; ready/valid backpressure; token-level operator overlap; and the exact board AXI/DDR wrapper and compute-slot behavior. Do not use floating-point IP for the elaborated W4A8 datapath.

Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe with real synthesis evidence. Select for highest end-to-end throughput within discovered VU9P resource and timing limits, rather than minimum resource usage. Analytical estimates may prioritize candidates but cannot replace measured QoR. Report estimates separately from measured results.

Use the established hierarchical verification policy: real model weights and inputs, operator/leaf validation, connected single-layer validation, then the exact board AXI/DDR wrapper with real DDR weight loading, active/shadow switching, prefetch, activation ping-pong, and final writeback. Valid nonzero output and no deadlock satisfy the stated functional acceptance when the real tool gates pass; preserve full layer computation and pipeline overlap.

The upstream LLM for this experiment is gpt-6.1-sol. This experiment changes only the target model to Gemma; do not alter shared templates, numeric policy, board materials, or the generic agent workflow for this campaign.

</human_task_spec>

<model_source_path>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/gemma3_1b_it/model_config.json
</model_source_path>

<model_source_content>
{
  "model_type": "gemma3_text",
  "num_layers": 26,
  "hidden_size": 1152,
  "target_max_seq_len": 16,
  "block": {
    "type": "decoder",
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
    ]
  },
  "attention": {
    "kind": "mqa",
    "num_q_heads": 4,
    "num_kv_heads": 1,
    "head_dim": 256,
    "causal": true,
    "position_encoding": {
      "type": "rope",
      "rope_theta": 1000000,
      "rope_local_base_freq": 10000
    },
    "qkv_bias": false,
    "out_bias": false,
    "qk_norm": true,
    "sliding_window": 512,
    "sliding_window_pattern": 6
  },
  "norm": {
    "type": "rms_norm",
    "position": "pre",
    "eps": 1e-06,
    "has_bias": false
  },
  "mlp": {
    "type": "gated",
    "intermediate_size": 6912,
    "activation": "gelu_pytorch_tanh",
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
    "head_dim": 256,
    "kind": "mqa",
    "num_kv_heads": 1,
    "num_q_heads": 4,
    "out_bias": false,
    "position_encoding": {
      "rope_local_base_freq": 10000,
      "rope_theta": 1000000,
      "type": "rope"
    },
    "qk_norm": true,
    "qkv_bias": false,
    "sliding_window": 512,
    "sliding_window_pattern": 6
  },
  "block": {
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
    "type": "decoder"
  },
  "hidden_size": 1152,
  "mlp": {
    "activation": "gelu_pytorch_tanh",
    "down_bias": false,
    "intermediate_size": 6912,
    "type": "gated",
    "up_bias": false
  },
  "model_type": "gemma3_text",
  "norm": {
    "eps": 1e-06,
    "has_bias": false,
    "position": "pre",
    "type": "rms_norm"
  },
  "num_layers": 26,
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
    "model_dir": {
      "type": "string"
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
