<agent>
design_space_agent
</agent>

<task>
Act as the design-space exploration engineer. Create the initial hardware design_space JSON for this model/template/board triplet.
</task>

<rules>
1. The design space must be compatible with the extracted model facts, template library, numeric policy, and target board profile.
2. Search parameters must be hardware parameters, not model semantics.
3. Declare a finite, complete candidate universe containing only parameters that genuinely change generated RTL, Vivado FP IP, XPM BRAM/URAM topology, or board behavior. Exclude metadata-only tile, burst, pipeline-depth, and clock-target fields until they are wired into generated hardware.
4. Include lanes, compute_array.rows, compute_array.cols, physical FIFO depth, activation-bank count, and optional physical_weight_layout_candidates. The two compute_array values are physical MAC PE dimensions that change generated hardware. Keep compute_array.cols power-of-two; rows must divide selected vector lanes, while columns may divide lanes or combine a whole number of lane groups, as supported by the current wide-column template. When supplied, each layout must bind every model-semantic weight-storage term declared by the current semantic adapter to a positive XPM URAM bank count. Do not use another model family's role names. If no explicit layouts are supplied, Stage 4 derives the complete all-URAM baseline from the same semantic contract.
5. For every numeric stream element width declared by the semantic_stream_contract, declare at least one lane candidate whose lane payload is no wider than the board AXI beat and divides that AXI width exactly. The contract may contain both activation and accumulator/residual streams; checking only the activation dtype is invalid. Candidates that cannot pack a declared stream width are ineligible and must not be described as legal, and the framework will reject a domain with no valid lane for any required width.
6. The supplied explicit_task_qor_targets are immutable user constraints. Repeat them accurately, but do not add, delete, weaken, or replace them.
7. Bind physical arithmetic to the supplied numeric policy: integer/fixed-point DSP MACs for integer quantization, Vivado floating-point IP only for a floating-point policy. Keep XPM physical memories and reject software arithmetic or ideal-memory backends. Never require floating-point IP for an integer-only design.
8. Do not choose parameters that require changing model semantics or bypassing DDR/AXI/runtime constraints.
9. framework_physical_domain_seed is read-only framework topology evidence. It is not a selected architecture, QoR estimate, or automatic fallback promotion. Return a complete current design-space universe; when current model/board/template evidence has no more specific PE geometry, state explicit legal tuples or correlated pairs from this seed rather than only a candidate count.
10. For the physical domain, retain the exact supplied framework_physical_domain_seed JSON structure and key names: search_params.candidate_universe.candidate_dimensions with lanes.legal_values, compute_array.legal_row_col_pairs, physical_fifo_depth.legal_values, and activation_bank_count.legal_values. Filter values using current evidence as necessary; do not rename or relocate these keys. Put explanatory constraints alongside the data.
11. Do not provide resource, power, frequency, or performance estimates. Stage 4 will use only real target-board app-shell Vivado and hardware-counter measurements for those four metrics.
</rules>

<model_config>
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
</model_config>

<template_metadata_summary>
{
  "library_id": "spatialaccagent_chisel_templates_v0",
  "templates": [
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "source": "Activation.scala",
      "supported_ops": [
        "activation",
        "relu",
        "gelu",
        "gelu_new",
        "silu",
        "gelu_tanh"
      ],
      "template_id": "activation"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "liveness"
      ],
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
      "source": "Attention.scala",
      "supported_ops": [
        "self_attention",
        "mha_attention",
        "gqa_attention",
        "mqa_attention"
      ],
      "template_id": "attention"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "runtime"
      ],
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "num_q_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "input_bits",
        "elem_bits",
        "output_bits"
      ],
      "source": "DecoderBlock.scala",
      "supported_ops": [
        "decoder_block",
        "opt_block",
        "gpt2_block",
        "llama_block",
        "qwen2_block",
        "gemma3_text_block"
      ],
      "template_id": "decoder_block"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "source": "Elementwise.scala",
      "supported_ops": [
        "elementwise_mul",
        "activation_mul"
      ],
      "template_id": "elementwise"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "source": "FFN.scala",
      "supported_ops": [
        "dense_ffn",
        "dense_mlp",
        "gated_mlp",
        "mlp_fc",
        "mlp_proj",
        "mlp_fc1",
        "mlp_fc2",
        "mlp_gate_proj",
        "mlp_up_proj",
        "mlp_down_proj"
      ],
      "template_id": "ffn"
    },
    {
      "constraints_emitted": [
        "shape",
        "stream",
        "beat",
        "memory",
        "runtime"
      ],
      "required_params": [
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes"
      ],
      "source": "KVCache.scala",
      "supported_ops": [
        "kv_cache",
        "k_cache",
        "v_cache"
      ],
      "template_id": "kv_cache"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "required_params": [
        "in_features",
        "out_features",
        "lanes"
      ],
      "source": "Linear.scala",
      "supported_ops": [
        "linear",
        "q_proj",
        "k_proj",
        "v_proj",
        "out_proj",
        "fc1",
        "fc2",
        "gate_proj",
        "up_proj",
        "down_proj"
      ],
      "template_id": "linear"
    },
    {
      "constraints_emitted": [
        "shape",
        "stream",
        "beat"
      ],
      "required_params": [
        "seq_len",
        "causal"
      ],
      "source": "Mask.scala",
      "supported_ops": [
        "attention_mask",
        "causal_mask",
        "sliding_window_mask"
      ],
      "template_id": "mask"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "source": "Norm.scala",
      "supported_ops": [
        "layer_norm",
        "rms_norm",
        "qk_norm"
      ],
      "template_id": "norm"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "lanes",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "source": "QKVProjection.scala",
      "supported_ops": [
        "qkv_projection",
        "q_proj",
        "k_proj",
        "v_proj",
        "fused_qkv"
      ],
      "template_id": "qkv_projection"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "source": "Residual.scala",
      "supported_ops": [
        "residual_add",
        "residual_add_1",
        "residual_add_2"
      ],
      "template_id": "residual"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "required_params": [
        "head_dim",
        "lanes",
        "rope_theta"
      ],
      "source": "RoPE.scala",
      "supported_ops": [
        "rope",
        "rotary_position_embedding"
      ],
      "template_id": "rope"
    },
    {
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "source": "Softmax.scala",
      "supported_ops": [
        "softmax",
        "masked_softmax"
      ],
      "template_id": "softmax"
    }
  ]
}
</template_metadata_summary>

<target_board_profile>
{
  "_llm_provenance": {
    "mode": "llm",
    "sub_agent": "board_profile_agent",
    "used_fallback": false
  },
  "board": {
    "board_document_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0\u677f\u5361\u4f7f\u7528\u6587\u6863.docx",
    "board_name": "mimic_computer_v6.0",
    "fpga_part": "xcvu9p_CIV-flgb2104-2-i"
  },
  "board_pass_criteria": {},
  "memory_system": {
    "address_map": {
      "control_registers": "0x3000000000",
      "ddr_base": "0x2800000000",
      "output_abs": "0x28092f1000"
    },
    "axi_addr_width_bits": 37,
    "axi_clock": "c0_ddr4_s_axi_clk",
    "axi_data_bytes": 64,
    "axi_data_width_bits": 512,
    "axi_id_width_bits": 4,
    "axi_reset": "c0_ddr4_s_axi_rst_n",
    "axi_wstrb_width_bits": 64,
    "calibration_done_signal": "c0_init_calib_complete",
    "core_side_interface_name": "c0_ddr4_s_axi_*",
    "ddr_channels": 1,
    "ddr_type": "DDR4",
    "ddr_word_width_bits": 512,
    "real_board_reference_rtl": "verification/rtl/cnn_core.sv"
  },
  "notes": [
    "Field evidence values for FPGA part, DDR/AXI width, runtime command/addresses, and control protocol were copied from the provided field_evidence_summary and are traceable to board/runtime_axi_ddr.md and board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md.",
    "Board name 'mimic_computer_v6.0' is inferred from the provided board document file name; no formal board product name was independently confirmed in the excerpts.",
    "No explicit board pass/fail criteria or resource utilization numbers were present in the supplied board materials, so board_pass_criteria.explicit_criteria is null.",
    "The remote host and runtime execution machine are captured from runtime_axi_ddr.md; source notes indicate the board runtime execution machine may be replaced by the user.",
    "Some remote sample probes failed with locale warnings and returned no file content; only the app_shell_9p.xpr FPGA part evidence from the successful sample project probe was used."
  ],
  "runtime_interface": {
    "board_run_command": "scripts/board/run_pyjm12_smoke.sh",
    "c2h_device_template": "/dev/xdma${XDMA_ID}_c2h_0",
    "control_protocol": "xdma_raw_register_and_ddr",
    "ctrl_base": "0x3000000000",
    "ddr_base": "0x2800000000",
    "ddr_image_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
    "h2c_device_template": "/dev/xdma${XDMA_ID}_h2c_0",
    "mimic_dir": "/home/test/mimic_driver_c6",
    "output_abs": "0x28092f1000",
    "remote_host": "hyyuan@10.12.133.23",
    "xdma_id_default": 1
  },
  "schema_version": "spatialaccagent.board_profile.v0",
  "shell": {
    "core_ddr_axi_interface": "c0_ddr4_s_axi_*",
    "core_side_interface_name": "c0_ddr4_s_axi_*",
    "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
    "init_calibration_done_signal": "c0_init_calib_complete",
    "project_name": "app_shell_9p",
    "project_path": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr",
    "real_board_axi_reference_rtl": "verification/rtl/cnn_core.sv",
    "reference_rtl": "verification/rtl/cnn_core.sv"
  }
}
</target_board_profile>

<numeric_policy>
{
  "_llm_provenance": {
    "mode": "llm",
    "sub_agent": "numeric_policy_agent",
    "used_fallback": false
  },
  "_numeric_comparison_resolution": {
    "default_policy_id": "spatialaccagent.loose_numeric_compare.v1",
    "defaulted_fields": [
      "atol",
      "rtol",
      "max_mismatch_fraction"
    ],
    "defaults": {
      "atol": 0.1,
      "max_mismatch_fraction": 0.05,
      "rtol": 0.1
    },
    "dut_outputs_used_for_resolution": false,
    "field_sources": {
      "atol": "framework_default",
      "max_mismatch_fraction": "framework_default",
      "rtol": "framework_default"
    },
    "provided_values_take_precedence": true,
    "resolved": {
      "atol": 0.1,
      "max_mismatch_fraction": 0.05,
      "rtol": 0.1
    },
    "schema_version": "spatialaccagent.numeric_comparison_resolution.v1"
  },
  "default_rules": {
    "acc_dtype": "int32",
    "activation_dtype": "int8",
    "rounding": "nearest_even",
    "saturation": true,
    "scale_dtype": "int32",
    "weight_dtype": "int4"
  },
  "notes": [
    "Explicit numeric policy found in current_run_numeric_policy.md: W4A8 signed INT4 weights, signed INT8 activations, INT32 accumulators/bias, INT32 scale dtype, nearest-even rounding, saturating INT8 outputs.",
    "Quantitative tolerance comparison values (atol, rtol, max_mismatch_fraction) are intentionally omitted by the current-run input; framework deterministic loose defaults will apply after extraction.",
    "This policy supersedes the previous floating-point policy and preserves non-quantization architecture; pack 8 INT4 weights per 32-bit word and 128 per 512-bit beat.",
    "Important integer invariants: QK/PV operands are signed INT8; Softmax probabilities must be requantized into the activation domain before PV multiplication; zero-extend UINT8 fixed-point sigmoid/Softmax coefficients before signed multiplication.",
    "Accumulator and DSP accounting must match the declared INT32 attention datapath; no floating-point modules may be instantiated in the integer elaboration hierarchy.",
    "Missing or invalid quantitative comparison values use spatialaccagent.loose_numeric_compare.v1; current-run provided values take precedence."
  ],
  "policy_id": "current_run_numeric_policy",
  "schema_version": "1.0",
  "tolerance": {
    "comparison": {
      "atol": 0.1,
      "default_policy_id": "spatialaccagent.loose_numeric_compare.v1",
      "max_mismatch_fraction": 0.05,
      "rtol": 0.1,
      "source": "framework_default"
    },
    "stage": "functional_or_shape",
    "system": "valid_output_required"
  }
}
</numeric_policy>

<semantic_stream_contract>
{
  "axi_data_width_bits": 512,
  "packing_rule": "lanes * stream_element_bits must be <= AXI width and divide it exactly",
  "required_numeric_roles": [
    "accumulator",
    "activation"
  ],
  "required_stream_bits": [
    8,
    32
  ],
  "status": "ready"
}
</semantic_stream_contract>

<explicit_task_qor_targets>
{
  "power_report_required": false,
  "source": "task_spec"
}
</explicit_task_qor_targets>

<framework_physical_domain_seed>
{
  "candidate_universe": {
    "candidate_dimensions": {
      "activation_bank_count": {
        "legal_values": [
          2,
          4
        ]
      },
      "compute_array": {
        "legal_row_col_pairs": [
          {
            "cols": 4,
            "rows": 4
          },
          {
            "cols": 8,
            "rows": 4
          },
          {
            "cols": 16,
            "rows": 4
          },
          {
            "cols": 32,
            "rows": 4
          },
          {
            "cols": 4,
            "rows": 8
          },
          {
            "cols": 8,
            "rows": 8
          },
          {
            "cols": 16,
            "rows": 8
          },
          {
            "cols": 32,
            "rows": 8
          },
          {
            "cols": 4,
            "rows": 16
          },
          {
            "cols": 8,
            "rows": 16
          },
          {
            "cols": 16,
            "rows": 16
          },
          {
            "cols": 32,
            "rows": 16
          }
        ]
      },
      "lanes": {
        "legal_values": [
          8,
          16
        ]
      },
      "physical_fifo_depth": {
        "legal_values": [
          32,
          64,
          128
        ]
      }
    }
  }
}
</framework_physical_domain_seed>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "hard_constraints": {
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
    "objectives": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "schema_version": {
      "type": "string"
    },
    "search_params": {
      "additionalProperties": true,
      "type": "object"
    },
    "sources": {
      "additionalProperties": true,
      "type": "object"
    },
    "status": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "status",
    "sources",
    "search_params",
    "objectives",
    "hard_constraints",
    "notes"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
