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
# Gemma FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied Gemma checkpoint and its complete decoder Transformer-block workload. Derive the model architecture, tensor shapes, layer count, sequence length, checkpoint tensor names, and operator order from the supplied model source and checkpoint; do not substitute GPT-2 or fixed project dimensions.

Run the complete public Stage 0--7 workflow with real tools and the supplied VU9P board sample project. Preserve the established OPT-aligned architecture and schedule: W4A8 signed INT4 weights, INT8 activations, INT32 accumulation and integer DSP MACs; complete weights in external DDR; 512-bit DDR loader and refill; bounded active/shadow weight caches; prefetch of the next layer/tile; activation ping-pong; ready/valid backpressure; token-level operator overlap; and the exact board AXI/DDR wrapper and compute-slot behavior. Do not use floating-point IP for the elaborated W4A8 datapath.

Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe with real synthesis evidence. Select for highest end-to-end throughput within discovered VU9P resource and timing limits, rather than minimum resource usage. Analytical estimates may prioritize candidates but cannot replace measured QoR. Report estimates separately from measured results.

Use the established hierarchical verification policy: real model weights and inputs, operator/leaf validation, connected single-layer validation, then the exact board AXI/DDR wrapper with real DDR weight loading, active/shadow switching, prefetch, activation ping-pong, and final writeback. Valid nonzero output and no deadlock satisfy the stated functional acceptance when the real tool gates pass; preserve full layer computation and pipeline overlap.

The upstream LLM for this experiment is gpt-6.1-sol. This experiment changes only the target model to Gemma; do not alter shared templates, numeric policy, board materials, or the generic agent workflow for this campaign.

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
  "model_dir": "/home/remote/.cache/huggingface/hub/models--google--gemma-3-1b-it/snapshots/dcc83ea841ab6100d6b47a070329e1ba4cf78752",
  "model_type": "gemma3_text",
  "norm": {
    "eps": 1e-06,
    "has_bias": false,
    "position": "pre",
    "type": "rms_norm"
  },
  "notes": [
    "Extracted model architecture and operator order from the supplied model_config.json; the deterministic extractor candidate is consistent with that source.",
    "The supplied source does not include checkpoint tensor names or checkpoint contents, so those cannot be specified here.",
    "The source specifies hidden_size=1152 and 4 query heads with head_dim=256 (query projection width 1024); both source values are preserved."
  ],
  "num_layers": 26,
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
