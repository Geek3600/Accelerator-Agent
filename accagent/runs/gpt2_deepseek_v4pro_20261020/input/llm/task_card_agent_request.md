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
# GPT-2 FPGA Spatial Accelerator Campaign

Design a complete FPGA-runnable spatial accelerator for the supplied GPT-2 checkpoint and its complete Transformer-block workload. Derive model architecture, tensor shapes, layer count, sequence length, checkpoint tensor names, and operator order from the supplied model source and checkpoint; do not substitute fixed project dimensions.

Run the complete public Stage 0--7 workflow with real tools and the supplied VU9P board sample project. Preserve the established OPT-aligned architecture and schedule: W4A8 signed INT4 weights, INT8 activations, INT32 accumulation and integer DSP MACs; complete weights in external DDR; 512-bit DDR loader and refill; bounded active/shadow weight caches; prefetch of the next layer/tile; activation ping-pong; ready/valid backpressure; token-level operator overlap; and the exact board AXI/DDR wrapper and compute-slot behavior. Do not use floating-point IP for the elaborated W4A8 datapath.

Stage 4 must enumerate and measure the complete legal FPGA-effective DSE candidate universe with real synthesis evidence. Select for highest end-to-end throughput within discovered VU9P resource and timing limits, rather than minimum resource usage. Analytical estimates may prioritize candidates but cannot replace measured QoR. Report estimates separately from measured results. The throughput objective is 200 token/s; if a selected design misses it, continue the normal DSE/optimization flow within the physical limits. Preserve source-bound timing and throughput history for every measured candidate.

Use the established hierarchical verification policy: real model weights and inputs, operator/leaf validation, connected single-layer validation, then the exact board AXI/DDR wrapper with real DDR weight loading, active/shadow switching, prefetch, activation ping-pong, and final writeback. Valid nonzero output and no deadlock satisfy the stated functional acceptance when the real tool gates pass; preserve full layer computation and pipeline overlap.

These two runs use this exact same target-model task, board, numeric policy, templates, and workflow. Their sole experimental variable is the upstream LLM model, recorded in each run's LLM configuration. Start each run from Stage 0 in an independent run directory; do not reuse generated RTL, DSE results, or verification evidence from another run.

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
  "model_dir": "/home/remote/.cache/huggingface/hub/models--openai-community--gpt2/snapshots/607a30d783dfa663caf39e06633721c8d4cfcd7e",
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
