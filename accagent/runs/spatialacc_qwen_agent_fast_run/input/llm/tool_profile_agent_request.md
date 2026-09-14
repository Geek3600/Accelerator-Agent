<agent>
tool_profile_agent
</agent>

<task>
Act as the EDA toolchain engineer. Extract the external EDA tool profile from current-run tool materials.
</task>

<rules>
1. Treat the tool materials directory as the complete current-run tool input.
2. Field evidence summary is the source-of-truth audit trail. Critical host, executable, environment, and script fields must match evidence when evidence exists.
3. The formal framework needs VCS or Verilator for functional verification and Vivado for synthesis, implementation, and bitstream generation.
4. Do not assume a fixed host, path, license server, version, or command unless it appears in the provided documents or target_board_profile.
5. Use common tool names such as vcs, verilator, and vivado when present.
6. Use scope=local for tools on the current machine, scope=remote for tools accessed through ssh, and null when unknown.
7. Put missing host/path/port/env/workdir fields as null or empty objects rather than inventing defaults.
8. Record limitations, license requirements, sandbox restrictions, or version constraints in constraints.
9. For remote tools, record host and any required environment variables. For Vivado, executable must identify the Vivado binary when provided.
</rules>

<tool_materials_summary>
{
  "chunk_count": 4,
  "file_count": 4,
  "files": [
    {
      "chars": 77,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/remote_server.md",
      "suffix": ".md"
    },
    {
      "chars": 637,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
      "suffix": ".md"
    },
    {
      "chars": 62,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/verilator.md",
      "suffix": ".md"
    },
    {
      "chars": 539,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
      "suffix": ".md"
    }
  ],
  "label": "tools",
  "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools",
  "schema_version": "spatialaccagent.material_index_summary.v0",
  "skipped": [],
  "skipped_count": 0
}
</tool_materials_summary>

<target_board_profile>
{
  "_llm_provenance": {
    "mode": "llm",
    "sub_agent": "board_profile_agent",
    "used_fallback": false
  },
  "board": {
    "board_model": null,
    "board_name": "mimic_computer_v6.0",
    "board_name_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0\u677f\u5361\u4f7f\u7528\u6587\u6863.docx",
    "board_revision": "v6.0",
    "clock_frequency_hz": null,
    "evidence": [
      {
        "chunk_id": "board:000004",
        "excerpt": "\u6837\u4f8b\u5de5\u7a0b Vivado project \u4e2d\u7684\u5177\u4f53 part \u662f `xcvu9p_CIV-flgb2104-2-i`",
        "field": "fpga_part",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md"
      },
      {
        "excerpt": "<Option Name=\"Part\" Val=\"xcvu9p_CIV-flgb2104-2-i\"/>",
        "field": "fpga_part",
        "source": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr"
      }
    ],
    "fpga_device": "VU9P",
    "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
    "fpga_vendor": null,
    "resource_numbers": null
  },
  "board_pass_criteria": {
    "comparison_tolerance": null,
    "evidence": [
      {
        "chunk_id": "board:000003",
        "excerpt": "\u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a```bash scripts/board/run_pyjm12_smoke.sh ```",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      }
    ],
    "expected_output_address_abs": "0x28092f1000",
    "expected_output_contents_or_checksum": null,
    "expected_success_indicator": null,
    "log_success_regex": null,
    "primary_board_smoke_command": "scripts/board/run_pyjm12_smoke.sh",
    "required_control_protocol": "xdma_raw_register_and_ddr",
    "required_ddr_axi_compatibility": {
      "axi_clock": "c0_ddr4_s_axi_clk",
      "axi_data_bytes": 64,
      "axi_data_width_bits": 512,
      "axi_reset": "c0_ddr4_s_axi_rst_n",
      "calibration_done_signal": "c0_init_calib_complete",
      "core_side_interface_name": "c0_ddr4_s_axi_*",
      "ddr_channels": 1
    },
    "required_fpga_part": "xcvu9p_CIV-flgb2104-2-i",
    "required_runtime_host": "hyyuan@10.12.133.23"
  },
  "memory_system": {
    "address_map": {
      "control_registers": "0x3000000000",
      "ddr_base": "0x2800000000",
      "output_abs": "0x28092f1000"
    },
    "alignment_requirement_bytes": null,
    "axi_addr_width_bits": 37,
    "axi_clock": "c0_ddr4_s_axi_clk",
    "axi_clock_frequency_hz": null,
    "axi_data_bytes": 64,
    "axi_data_width_bits": 512,
    "axi_id_width_bits": 4,
    "axi_protocol": "AXI",
    "axi_protocol_version": null,
    "axi_reset": "c0_ddr4_s_axi_rst_n",
    "axi_reset_polarity": null,
    "axi_wstrb_width_bits": 64,
    "board_axi_prefix": "c0_ddr4_s_axi",
    "burst_length_policy": null,
    "calibration_done_signal": "c0_init_calib_complete",
    "core_side_interface_name": "c0_ddr4_s_axi_*",
    "ddr_capacity_bytes": null,
    "ddr_channels": 1,
    "ddr_type": "DDR4",
    "ddr_word_width_bits": 512,
    "endianness": null,
    "evidence": [
      {
        "chunk_id": "board:000003",
        "excerpt": "\u5f53\u524d\u6838\u5fc3\u4f7f\u7528\u4e00\u4e2a DDR AXI channel\uff1a`c0_ddr4_s_axi_*`\u3002... `ddr_channels`: 1",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "\u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002* AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002... `ddr_word_width_bits`: 512",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_axi_araddr[36:0]`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "AXI ID \u5bbd\u5ea6\uff1a4 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awid[3:0]` \u548c `c0_ddr4_s_axi_arid[3:0]`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "DDR UI / AXI clock\uff1a`c0_ddr4_s_axi_clk`\u3002DDR reset\uff1a`c0_ddr4_s_axi_rst_n`\u3002DDR calibration done\uff1a`c0_init_calib_complete`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      }
    ],
    "real_board_reference_rtl": "verification/rtl/cnn_core.sv"
  },
  "notes": [
    "Critical FPGA part, DDR/AXI, runtime command, control protocol, remote host, device id, base addresses, output address, image path, clock/reset, and calibration fields were populated only from the supplied evidence summaries.",
    "The FPGA part is preserved exactly as `xcvu9p_CIV-flgb2104-2-i`; it was not normalized to another spelling.",
    "The board name/revision is taken from the board document filename `mimic_computer_v6.0\u677f\u5361\u4f7f\u7528\u6587\u6863.docx`; no separate explicit board model/SKU was available in the selected field evidence.",
    "Source evidence warns that a 64-bit AXI interface with `AXI_BEAT_BYTES = 8` is not the real app_shell board-level DDR/AXI interface. This profile uses the real 512-bit, 64-byte `c0_ddr4_s_axi_*` board interface.",
    "No DDR capacity, AXI clock frequency, reset polarity, bitstream path, programming command, resource counts, register map, output size, checksum, pass regex, or numeric comparison tolerance was present in the supplied evidence, so those fields are null.",
    "Only the app_shell_9p Vivado sample project probe was reported as status ok; errored sample-project probes were not used for critical field values."
  ],
  "runtime_interface": {
    "board_run_command": "scripts/board/run_pyjm12_smoke.sh",
    "control_base_address": "0x3000000000",
    "control_protocol": "xdma_raw_register_and_ddr",
    "ctrl_base": "0x3000000000",
    "ddr_base": "0x2800000000",
    "ddr_base_address": "0x2800000000",
    "ddr_image_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
    "ddr_image_path_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
    "device_id_default": 1,
    "evidence": [
      {
        "chunk_id": "board:000003",
        "excerpt": "`control_protocol`: `xdma_raw_register_and_ddr`",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "\u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a```bash scripts/board/run_pyjm12_smoke.sh ```",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /home/test/mimic_driver_c6`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "\u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002\u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002\u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = 0x28092f1000`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "chunk_id": "board:000003",
        "excerpt": "\u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      }
    ],
    "mimic_dir": "/home/test/mimic_driver_c6",
    "output_abs": "0x28092f1000",
    "output_address_abs": "0x28092f1000",
    "output_size_bytes": null,
    "register_map": null,
    "remote_host": "hyyuan@10.12.133.23",
    "remote_port": 22,
    "runtime_dir": "/home/test/mimic_driver_c6",
    "xdma_id_default": 1
  },
  "schema_version": "spatialaccagent.target_board_profile.v0",
  "shell": {
    "bitstream_path": null,
    "core_ddr_axi_interface": "c0_ddr4_s_axi_*",
    "evidence": [
      {
        "chunk_id": "board:000003",
        "excerpt": "\u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002",
        "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
      },
      {
        "excerpt": "sample_project_summary reports this Vivado project as status ok and shows part `xcvu9p_CIV-flgb2104-2-i`.",
        "source": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr"
      }
    ],
    "init_calibration_done_signal": "c0_init_calib_complete",
    "programming_command": null,
    "real_board_axi_reference_rtl": "verification/rtl/cnn_core.sv",
    "reference_project_root": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8",
    "sample_project_file_count": 1608,
    "sample_project_status": "ok",
    "shell_name": "app_shell_9p",
    "shell_type": "app_shell",
    "uses_ddr4_axi_interface": true,
    "vivado_project_part": "xcvu9p_CIV-flgb2104-2-i",
    "vivado_project_path": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr",
    "vivado_version": null
  }
}
</target_board_profile>

<field_evidence_summary>
{
  "policy": {
    "llm_output_is_not_accepted_as_evidence_without_source": true,
    "llm_semantic_confirmation_required": true,
    "regex_candidates_are_not_ground_truth": true,
    "source": "merged_from_domain_llm_agents",
    "split_domain_agents": [
      "board",
      "tool",
      "quantization"
    ]
  },
  "schema_version": "spatialaccagent.field_evidence_summary.v0",
  "selected_fields": [
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "* \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vcs.host"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "* \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs"
        }
      ],
      "field": "tool.vcs.executable"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000004",
          "excerpt": "* \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vivado.host"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "tools:000004",
          "excerpt": "* \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Xilinx/Vivado/2021.1/bin/vivado",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
          "value": "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado"
        }
      ],
      "field": "tool.vivado.executable"
    }
  ]
}
</field_evidence_summary>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "notes": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "schema_version": {
      "type": "string"
    },
    "tools": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "constraints": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "env": {
            "additionalProperties": true,
            "type": "object"
          },
          "executable": {
            "type": [
              "string",
              "null"
            ]
          },
          "host": {
            "type": [
              "string",
              "null"
            ]
          },
          "name": {
            "type": "string"
          },
          "port": {
            "type": [
              "integer",
              "null"
            ]
          },
          "role": {
            "type": "string"
          },
          "scope": {
            "type": [
              "string",
              "null"
            ]
          },
          "source": {
            "type": [
              "string",
              "null"
            ]
          },
          "workdir": {
            "type": [
              "string",
              "null"
            ]
          }
        },
        "required": [
          "name",
          "role",
          "scope",
          "host",
          "port",
          "executable",
          "env",
          "workdir",
          "constraints",
          "source"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "schema_version",
    "tools",
    "notes"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
