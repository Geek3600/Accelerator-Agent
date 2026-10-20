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
# GPT-2 FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied GPT-2 checkpoint and its complete Transformer-block workload. Derive model architecture, tensor shapes, layer count, sequence length, checkpoint tensor names, and operator order from the supplied model source and checkpoint; do not substitute fixed project dimensions.

Run the complete public Stage 0--7 workflow with real tools and the supplied VU9P board sample project. Preserve the established OPT-aligned architecture and schedule: W4A8 signed INT4 weights, INT8 activations, INT32 accumulation and integer DSP MACs; complete weights in external DDR; 512-bit DDR loader and refill; bounded active/shadow weight caches; prefetch of the next layer/tile; activation ping-pong; ready/valid backpressure; token-level operator overlap; and the exact board AXI/DDR wrapper and compute-slot behavior. Do not use floating-point IP for the elaborated W4A8 datapath.

Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe with real synthesis evidence. Select for highest end-to-end throughput within discovered VU9P resource and timing limits, rather than minimum resource usage. Analytical estimates may prioritize candidates but cannot replace measured QoR. Report estimates separately from measured results. The throughput objective is 200 token/s; if a selected design misses it, continue the normal DSE/optimization flow within the physical limits. Preserve source-bound timing and throughput history for every measured candidate.

Use the established hierarchical verification policy: real model weights and inputs, operator/leaf validation, connected single-layer validation, then the exact board AXI/DDR wrapper with real DDR weight loading, active/shadow switching, prefetch, activation ping-pong, and final writeback. Valid nonzero output and no deadlock satisfy the stated functional acceptance when the real tool gates pass; preserve full layer computation and pipeline overlap.

These two runs use this exact same target-model task, board, numeric policy, templates, and workflow. Their sole experimental variable is the upstream LLM model, recorded in each run's LLM configuration. Start each run from Stage 0 in an independent run directory; do not reuse generated RTL, DSE results, or verification evidence from another run.

</human_task_spec>

<model_source_path>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/gpt2/model_config.json
</model_source_path>

<model_source_content>
{
  "model_type": "gpt2",
  "num_layers": 12,
  "hidden_size": 768,
  "target_max_seq_len": 16,
  "block": {
    "type": "decoder",
    "operator_sequence": [
      "layer_norm_1",
      "self_attention",
      "residual_add_1",
      "layer_norm_2",
      "mlp_fc",
      "activation",
      "mlp_proj",
      "residual_add_2"
    ]
  },
  "attention": {
    "kind": "mha",
    "num_q_heads": 12,
    "num_kv_heads": 12,
    "head_dim": 64,
    "causal": true,
    "position_encoding": {
      "type": "learned_absolute"
    },
    "qkv_bias": true,
    "out_bias": true
  },
  "norm": {
    "type": "layer_norm",
    "position": "pre",
    "eps": 1e-05,
    "has_bias": true
  },
  "mlp": {
    "type": "dense",
    "intermediate_size": 3072,
    "activation": "gelu_new",
    "up_bias": true,
    "down_bias": true
  },
  "weight_layout": {
    "qkv": "fused_qkv",
    "out_proj": "dense",
    "mlp": "c_fc_c_proj",
    "norm": "weight_bias"
  }
}

</model_source_content>

<deterministic_extractor_candidate>
{
  "attention": {
    "causal": true,
    "head_dim": 64,
    "kind": "mha",
    "num_kv_heads": 12,
    "num_q_heads": 12,
    "out_bias": true,
    "position_encoding": {
      "type": "learned_absolute"
    },
    "qkv_bias": true
  },
  "block": {
    "operator_sequence": [
      "layer_norm_1",
      "self_attention",
      "residual_add_1",
      "layer_norm_2",
      "mlp_fc",
      "activation",
      "mlp_proj",
      "residual_add_2"
    ],
    "type": "decoder"
  },
  "hidden_size": 768,
  "mlp": {
    "activation": "gelu_new",
    "down_bias": true,
    "intermediate_size": 3072,
    "type": "dense",
    "up_bias": true
  },
  "model_type": "gpt2",
  "norm": {
    "eps": 1e-05,
    "has_bias": true,
    "position": "pre",
    "type": "layer_norm"
  },
  "num_layers": 12,
  "target_max_seq_len": 16,
  "weight_layout": {
    "mlp": "c_fc_c_proj",
    "norm": "weight_bias",
    "out_proj": "dense",
    "qkv": "fused_qkv"
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
