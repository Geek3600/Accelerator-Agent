<agent>
field_evidence_agent
</agent>

<task>
Act as the source-evidence engineer. Convert current-run board, tool, and quantization materials into field_evidence JSON for the chip-design team.
</task>

<rules>
1. You are the adaptive semantic extractor; deterministic regex candidates are hints only, not ground truth.
2. Do not use a fixed keyword list as the reason for accepting a value. Accept a field only when the cited excerpt semantically supports it.
3. Each evidence item must cite source, chunk_id when available, and a short excerpt from the supplied materials.
4. Reject false positives from regex candidates, especially generic paths, sample/scaffold interfaces, stale board names, or values that are contradicted by nearby text.
5. If several values conflict, include the competing evidence items and explain the conflict in policy or reason fields; do not silently choose one.
6. For board/app-shell target fields, produce candidate evidence only; do not select an integration target unless the materials explicitly name it.
7. Unknown fields should be omitted from evidence rather than invented.
</rules>

<material_corpus_summary>
{
  "board_material_chars": 6113,
  "quantization_material_chars": 691,
  "source_excerpts_are_embedded_in": "deterministic_regex_candidate_summary.selected_fields[].evidence[].excerpt",
  "tool_material_chars": 1914
}
</material_corpus_summary>

<deterministic_regex_candidate_summary>
{
  "policy": {
    "candidate_only": true,
    "critical_fields_must_match_evidence_when_present": true,
    "llm_output_is_not_accepted_as_evidence_without_source": true,
    "llm_semantic_confirmation_required": true,
    "regex_is_not_semantic_ground_truth": true
  },
  "schema_version": "spatialaccagent.field_evidence_summary.v0",
  "selected_fields": [
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000004",
          "excerpt": "10.12.133.23\u670d\u52a1\u5668\u4e0a\uff0c\u76ee\u5f55\u4f4d\u7f6e\u662f/home/share/v6.0_9p_cnn_2slr_4core_yolov8 * \u91cc\u9762\u6709ddr\u548caxi wrapper\u7684\u6837\u4f8b\u5de5\u7a0b\uff0c\u53ef\u4ee5\u53c2\u8003 * \u6837\u4f8b\u5de5\u7a0b Vivado project \u4e2d\u7684\u5177\u4f53 part \u662f `xcvu9p_CIV-flgb2104-2-i`\uff0c\u6765\u6e90\u662f\uff1a * `/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v08",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md",
          "value": "xcvu9p_CIV-flgb2104-2-i"
        }
      ],
      "field": "board.fpga_part"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "lt`: `/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin` ## memory_system\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `ddr_channels`: 1 * `ddr_word_width_bits`: 512 * `axi_data_bytes`: 64 * `axi_addr_width_bits`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 1
        }
      ],
      "field": "memory_system.ddr_channels"
    },
    {
      "count": 3,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "## \u771f\u5b9e\u677f\u7ea7DDR/AXI\u63a5\u53e3 * \u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 *",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 512
        }
      ],
      "field": "memory_system.ddr_word_width_bits"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 512
        }
      ],
      "field": "memory_system.axi_data_width_bits"
    },
    {
      "count": 3,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "DR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_aw",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 64
        },
        {
          "chunk_id": "board:000003",
          "excerpt": "tion_done_signal`: `c0_init_calib_complete` ## \u6ce8\u610f `verification/rtl/AxiBoardSystemTop.sv` \u4e2d\u8fd8\u6709\u4e00\u4e2a\u7528\u4e8e\u529f\u80fd\u4eff\u771f scaffold \u7684 64-bit AXI \u63a5\u53e3\uff0c`AXI_BEAT_BYTES = 8`\u3002\u5b83\u4e0d\u80fd\u4ee3\u8868\u771f\u5b9e app_shell \u677f\u7ea7 DDR/AXI \u63a5\u53e3\u3002Stage 0 \u5982\u679c\u540c\u65f6\u8bfb\u5230\u8fd9\u4e24\u4e2a\u53e3\u5f84\uff0c\u5fc5\u987b\u4f18\u5148\u91c7\u7528\u771f\u5b9e\u677f\u7ea7 `cnn_core",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 8
        }
      ],
      "field": "memory_system.axi_data_bytes"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "ification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_axi_araddr[36:0]`\u3002 * AXI I",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 37
        }
      ],
      "field": "memory_system.axi_addr_width_bits"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "at \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_axi_araddr[36:0]`\u3002 * AXI ID \u5bbd\u5ea6\uff1a4 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awid[3:0]` \u548c `c0_ddr4_s_axi_arid[3:0]`\u3002 * AXI burst l",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 4
        }
      ],
      "field": "memory_system.axi_id_width_bits"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "r4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 64
        }
      ],
      "field": "memory_system.axi_wstrb_width_bits"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "_board_profile.memory_system` \u548c `target_board_profile.runtime_interface`\u3002 ## \u771f\u5b9e\u677f\u7ea7DDR/AXI\u63a5\u53e3 * \u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_ddr4_s_axi_*"
        }
      ],
      "field": "memory_system.core_side_interface_name"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "word_width_bits`: 512 * `axi_data_bytes`: 64 * `axi_addr_width_bits`: 37 * `axi_id_width_bits`: 4 * `axi_wstrb_width_bits`: 64 * `axi_clock`: `c0_ddr4_s_axi_clk` * `axi_reset`: `c0_ddr4_s_axi_rst_n` * `calibration_done_s",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_ddr4_s_axi_clk"
        }
      ],
      "field": "memory_system.axi_clock"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "ytes`: 64 * `axi_addr_width_bits`: 37 * `axi_id_width_bits`: 4 * `axi_wstrb_width_bits`: 64 * `axi_clock`: `c0_ddr4_s_axi_clk` * `axi_reset`: `c0_ddr4_s_axi_rst_n` * `calibration_done_signal`: `c0_init_calib_complete` ##",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_ddr4_s_axi_rst_n"
        }
      ],
      "field": "memory_system.axi_reset"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "* `axi_id_width_bits`: 4 * `axi_wstrb_width_bits`: 64 * `axi_clock`: `c0_ddr4_s_axi_clk` * `axi_reset`: `c0_ddr4_s_axi_rst_n` * `calibration_done_signal`: `c0_init_calib_complete` ## \u6ce8\u610f `verification/rtl/AxiBoardSystemTo",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_init_calib_complete"
        }
      ],
      "field": "memory_system.calibration_done_signal"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "em` \u548c `target_board_profile.runtime_interface`\u3002 ## \u771f\u5b9e\u677f\u7ea7DDR/AXI\u63a5\u53e3 * \u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AX",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "verification/rtl/cnn_core.sv"
        }
      ],
      "field": "memory_system.real_board_reference_rtl"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "`\uff1b * \u5199\u63a7\u5236\u5bc4\u5b58\u5668\u542f\u52a8\u63a8\u7406\uff1b * \u8f6e\u8be2\u72b6\u6001\u5bc4\u5b58\u5668\uff1b * \u4ece `OUTPUT_ABS` \u8bfb\u53d6\u8f93\u51fa\u5934\u90e8\uff1b * \u4ee5 result status \u53d8\u5316\u548c\u6709\u6548\u8f93\u51fa\u8bfb\u56de\u4f5c\u4e3a smoke pass \u6761\u4ef6\u3002 ## runtime_interface\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `control_protocol`: `xdma_raw_register_and_ddr` * `board_run_command`: `scripts/board/run_pyj",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "xdma_raw_register_and_ddr"
        }
      ],
      "field": "runtime_interface.control_protocol"
    },
    {
      "count": 3,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "ma${XDMA_ID}_h2c_0` \u5199\u63a7\u5236\u5bc4\u5b58\u5668\u548c DDR\uff0c\u901a\u8fc7 `/dev/xdma${XDMA_ID}_c2h_0` \u8bfb\u53d6\u72b6\u6001\u5bc4\u5b58\u5668\u548c\u8f93\u51fa\u6570\u636e\u3002 ## board runtime command \u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a ```bash scripts/board/run_pyjm12_smoke.sh ``` \u5efa\u8bae Stage 0 \u63d0\u53d6\u4e3a\uff1a ```bash scripts/board/run_pyjm12_smoke.",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "scripts/board/run_pyjm12_smoke.sh"
        }
      ],
      "field": "runtime_interface.board_run_command"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "ma_raw_register_and_ddr` * `board_run_command`: `scripts/board/run_pyjm12_smoke.sh` * `remote_host`: \u5982\u679c\u901a\u8fc7\u8fdc\u7aef\u670d\u52a1\u5668\u6267\u884c\u5de5\u5177\u6216\u677f\u5361\u6d41\u7a0b\uff0c\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u677f\u5361 runtime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\u6599\u4e2d\u66ff\u6362\u3002 * `mimic_dir`: `/home/test/mimic_d",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "runtime_interface.remote_host"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002 * \u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002 * \u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /home/test/mimic_driver_c6`\u3002 host runtime \u4f1a\u901a\u8fc7 `/dev/xdma${XDMA_ID}_h2c_0` \u5199\u63a7\u5236\u5bc4",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "/home/test/mimic_driver_c6"
        }
      ],
      "field": "runtime_interface.mimic_dir"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002 * \u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002 * \u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /home/test/mimic_driver_c6`\u3002 host runtime",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 1
        }
      ],
      "field": "runtime_interface.xdma_id_default"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "DDR/AXI-compatible\uff0c\u4e0d\u80fd\u7528\u53ea\u542b\u7b80\u5355\u5185\u5b58\u6a21\u578b\u7684 64-bit \u4eff\u771f scaffold \u4ee3\u66ff\u771f\u5b9e\u677f\u7ea7\u63a5\u53e3\u3002 ## host\u4fa7\u5730\u5740\u548cruntime\u63a7\u5236 \u5f53\u524d\u677f\u7ea7\u8c03\u8bd5\u811a\u672c\u4f7f\u7528 XDMA raw \u5730\u5740\u8bbf\u95ee\u3002\u5173\u952e\u5730\u5740\u5982\u4e0b\uff1a * \u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002 * DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002 * \u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = ",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "0x3000000000"
        }
      ],
      "field": "runtime_interface.ctrl_base"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u771f scaffold \u4ee3\u66ff\u771f\u5b9e\u677f\u7ea7\u63a5\u53e3\u3002 ## host\u4fa7\u5730\u5740\u548cruntime\u63a7\u5236 \u5f53\u524d\u677f\u7ea7\u8c03\u8bd5\u811a\u672c\u4f7f\u7528 XDMA raw \u5730\u5740\u8bbf\u95ee\u3002\u5173\u952e\u5730\u5740\u5982\u4e0b\uff1a * \u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002 * DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002 * \u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = 0x28092f1000`\u3002 * \u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/hom",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "0x2800000000"
        }
      ],
      "field": "runtime_interface.ddr_base"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u63a7\u5236 \u5f53\u524d\u677f\u7ea7\u8c03\u8bd5\u811a\u672c\u4f7f\u7528 XDMA raw \u5730\u5740\u8bbf\u95ee\u3002\u5173\u952e\u5730\u5740\u5982\u4e0b\uff1a * \u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002 * DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002 * \u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = 0x28092f1000`\u3002 * \u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/home/test/pyjm12_alllayers_9p_fullseq/pyjm",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "0x28092f1000"
        }
      ],
      "field": "runtime_interface.output_abs"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "_driver_c6` * `xdma_id_default`: `1` * `ctrl_base`: `0x3000000000` * `ddr_base`: `0x2800000000` * `output_abs`: `0x28092f1000` * `ddr_image_default`: `/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/ar",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin"
        }
      ],
      "field": "runtime_interface.ddr_image_default"
    },
    {
      "count": 4,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "me/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md offset:0-637 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVerilog testbench\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vcs.host"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "tools/vcs.md offset:0-637 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVerilog testbench\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs * \u7248\u672c\u63a2\u6d4b\u547d\u4ee4\uff1a * `VCS_TARGET_ARCH=li",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs"
        }
      ],
      "field": "tool.vcs.executable"
    },
    {
      "count": 4,
      "evidence": [
        {
          "chunk_id": "tools:000002",
          "excerpt": "me/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md offset:0-637 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVerilog testbench\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Software",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "tool.vivado.host"
    },
    {
      "count": 3,
      "evidence": [
        {
          "chunk_id": "tools:000004",
          "excerpt": "t_materials/tools/vivado.md offset:0-539 ```text # Vivado\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u7efc\u5408\u3001\u5e03\u5c40\u5e03\u7ebf\u3001\u751f\u6210 bitstream\u3002 * \u53ef\u6267\u884c\u6587\u4ef6\uff1a/home/EDA/Xilinx/Vivado/2021.1/bin/vivado * \u7248\u672c\u63a2\u6d4b\u547d\u4ee4\uff1a * `/home/EDA/Xilinx/Vivado/2021.1/bin/v",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
          "value": "/home/EDA/Xilinx/Vivado/2021.1/bin/vivado"
        }
      ],
      "field": "tool.vivado.executable"
    },
    {
      "count": 2,
      "evidence": [
        {
          "chunk_id": "quantization:000001",
          "excerpt": "ric notes or benchmark requirements If no policy file is provided, the framework uses the fallback policy: - weight/activation = FP16 - accumulation = FP32 - scale = FP16 - valid-output requirement and no-deadlock check.",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization/README.md",
          "value": "fp16"
        }
      ],
      "field": "numeric_policy.default_precision"
    }
  ]
}
</deterministic_regex_candidate_summary>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "evidence": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "chunk_id": {
            "type": [
              "string",
              "null"
            ]
          },
          "confidence": {
            "type": [
              "string",
              "number",
              "null"
            ]
          },
          "excerpt": {
            "type": "string"
          },
          "field": {
            "type": "string"
          },
          "reason": {
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
          "value": {}
        },
        "required": [
          "field",
          "value",
          "source",
          "chunk_id",
          "excerpt"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "policy": {
      "additionalProperties": true,
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "policy",
    "evidence"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
