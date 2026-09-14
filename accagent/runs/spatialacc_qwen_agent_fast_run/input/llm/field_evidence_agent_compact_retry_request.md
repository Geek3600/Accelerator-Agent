<agent>
field_evidence_agent_compact_retry
</agent>

<task>
The full Stage 0 LLM request failed during provider transport. Produce the same schema-bound JSON using this compacted current-run candidate evidence. This is still a mandatory LLM semantic review; do not copy values blindly if the compact evidence is insufficient.
</task>

<rules>
1. Return exactly one valid JSON object matching the output schema.
2. Keep used_fallback false by producing a real LLM decision; do not claim tool or checker pass.
3. If compact evidence is insufficient for a field, omit that field or record the conflict instead of inventing it.
4. Every evidence item that remains must cite its source and excerpt from the compacted candidate evidence.
</rules>

<full_prompt_transport_error>
[Errno 104] Connection reset by peer
</full_prompt_transport_error>

<compacted_candidate_evidence>
{
  "evidence": [
    {
      "chunk_id": "board:000004",
      "excerpt": "10.12.133.23\u670d\u52a1\u5668\u4e0a\uff0c\u76ee\u5f55\u4f4d\u7f6e\u662f/home/share/v6.0_9p_cnn_2slr_4core_yolov8 * \u91cc\u9762\u6709ddr\u548caxi wrapper\u7684\u6837\u4f8b\u5de5\u7a0b\uff0c\u53ef\u4ee5\u53c2\u8003 * \u6837\u4f8b\u5de5\u7a0b Vivado project \u4e2d\u7684\u5177\u4f53 part \u662f `xcvu9p_CIV-flgb2104-2-i`\uff0c\u6765\u6e90\u662f\uff1a * `/home/share/v6.0_\n... truncated 99 chars ...",
      "field": "board.fpga_part",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md",
      "value": "xcvu9p_CIV-flgb2104-2-i"
    },
    {
      "chunk_id": "board:000004",
      "excerpt": "gb2104-2-i`\uff0c\u6765\u6e90\u662f\uff1a * `/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr` * `<Option Name=\"Part\" Val=\"xcvu9p_CIV-flgb2104-2-i\"/>` * Stage 0 \u5fc5\u987b\u63d0\u53d6\u5177\u4f53 FPGA part\n... truncated 96 chars ...",
      "field": "board.fpga_part",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md",
      "value": "xcvu9p_CIV-flgb2104-2-i"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "## \u771f\u5b9e\u677f\u7ea7DDR/AXI\u63a5\u53e3 * \u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\n... truncated 95 chars ...",
      "field": "memory_system.ddr_word_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 512
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199\n... truncated 96 chars ...",
      "field": "memory_system.ddr_word_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 512
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "m12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin` ## memory_system\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `ddr_channels`: 1 * `ddr_word_width_bits`: 512 * `axi_data_bytes`: 64 * `\n... truncated 103 chars ...",
      "field": "memory_system.ddr_word_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 512
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199\n... truncated 96 chars ...",
      "field": "memory_system.axi_data_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 512
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "DR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 *\n... truncated 101 chars ...",
      "field": "memory_system.axi_data_bytes",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 64
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "tion_done_signal`: `c0_init_calib_complete` ## \u6ce8\u610f `verification/rtl/AxiBoardSystemTop.sv` \u4e2d\u8fd8\u6709\u4e00\u4e2a\u7528\u4e8e\u529f\u80fd\u4eff\u771f scaffold \u7684 64-bit AXI \u63a5\u53e3\uff0c`AXI_BEAT_BYTES = 8`\u3002\u5b83\u4e0d\u80fd\u4ee3\u8868\u771f\u5b9e app_shell \u677f\u7ea7 DDR/AXI \u63a5\u53e3\u3002\n... truncated 96 chars ...",
      "field": "memory_system.axi_data_bytes",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 8
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin` ## memory_system\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `ddr_channels`: 1 * `ddr_word_width_bits`: 512 * `axi_data_bytes`: 64 * `axi_addr_width_bits`: 37 * `a\n... truncated 97 chars ...",
      "field": "memory_system.axi_data_bytes",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 64
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "lt`: `/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin` ## memory_system\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `ddr_channels`: 1 * `ddr_word_width_bits`: 512 * `axi\n... truncated 94 chars ...",
      "field": "memory_system.ddr_channels",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 1
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "ification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]`\n... truncated 95 chars ...",
      "field": "memory_system.axi_addr_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 37
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "at \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_axi_araddr[36:0]`\u3002 * AXI ID \u5bbd\u5ea6\uff1a4 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awid[3:0]` \u548c \n... truncated 95 chars ...",
      "field": "memory_system.axi_id_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 4
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "r4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002 * AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002 * AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002 * AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002 * AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c\n... truncated 102 chars ...",
      "field": "memory_system.axi_wstrb_width_bits",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 64
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "_board_profile.memory_system` \u548c `target_board_profile.runtime_interface`\u3002 ## \u771f\u5b9e\u677f\u7ea7DDR/AXI\u63a5\u53e3 * \u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/c\n... truncated 99 chars ...",
      "field": "memory_system.core_side_interface_name",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_ddr4_s_axi_*"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "word_width_bits`: 512 * `axi_data_bytes`: 64 * `axi_addr_width_bits`: 37 * `axi_id_width_bits`: 4 * `axi_wstrb_width_bits`: 64 * `axi_clock`: `c0_ddr4_s_axi_clk` * `axi_reset`: `c0\n... truncated 108 chars ...",
      "field": "memory_system.axi_clock",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_ddr4_s_axi_clk"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "0_ddr4_s_axi_awid[3:0]` \u548c `c0_ddr4_s_axi_arid[3:0]`\u3002 * AXI burst length \u5bbd\u5ea6\uff1a8 bit\u3002 * \u5f53\u524d\u6838\u5fc3\u4f7f\u7528\u4e00\u4e2a DDR AXI channel\uff1a`c0_ddr4_s_axi_*`\u3002 * DDR UI / AXI clock\uff1a`c0_ddr4_s_axi_clk`\u3002 * DDR rese\n... truncated 118 chars ...",
      "field": "memory_system.axi_clock",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_ddr4_s_axi_clk"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "ytes`: 64 * `axi_addr_width_bits`: 37 * `axi_id_width_bits`: 4 * `axi_wstrb_width_bits`: 64 * `axi_clock`: `c0_ddr4_s_axi_clk` * `axi_reset`: `c0_ddr4_s_axi_rst_n` * `calibration_d\n... truncated 110 chars ...",
      "field": "memory_system.axi_reset",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_ddr4_s_axi_rst_n"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "rid[3:0]`\u3002 * AXI burst length \u5bbd\u5ea6\uff1a8 bit\u3002 * \u5f53\u524d\u6838\u5fc3\u4f7f\u7528\u4e00\u4e2a DDR AXI channel\uff1a`c0_ddr4_s_axi_*`\u3002 * DDR UI / AXI clock\uff1a`c0_ddr4_s_axi_clk`\u3002 * DDR reset\uff1a`c0_ddr4_s_axi_rst_n`\u3002 * DDR calibration\n... truncated 110 chars ...",
      "field": "memory_system.axi_reset",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_ddr4_s_axi_rst_n"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "* `axi_id_width_bits`: 4 * `axi_wstrb_width_bits`: 64 * `axi_clock`: `c0_ddr4_s_axi_clk` * `axi_reset`: `c0_ddr4_s_axi_rst_n` * `calibration_done_signal`: `c0_init_calib_complete` \n... truncated 126 chars ...",
      "field": "memory_system.calibration_done_signal",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_init_calib_complete"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "* \u5f53\u524d\u6838\u5fc3\u4f7f\u7528\u4e00\u4e2a DDR AXI channel\uff1a`c0_ddr4_s_axi_*`\u3002 * DDR UI / AXI clock\uff1a`c0_ddr4_s_axi_clk`\u3002 * DDR reset\uff1a`c0_ddr4_s_axi_rst_n`\u3002 * DDR calibration done\uff1a`c0_init_calib_complete`\u3002 * \u677f\u7ea7 flo\n... truncated 118 chars ...",
      "field": "memory_system.calibration_done_signal",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "c0_init_calib_complete"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "em` \u548c `target_board_profile.runtime_interface`\u3002 ## \u771f\u5b9e\u677f\u7ea7DDR/AXI\u63a5\u53e3 * \u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002 * \u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002 * \u6570\u636e\u4f4d\u5bbd\uff1a`C_DAT\n... truncated 115 chars ...",
      "field": "memory_system.real_board_reference_rtl",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "verification/rtl/cnn_core.sv"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "ma${XDMA_ID}_h2c_0` \u5199\u63a7\u5236\u5bc4\u5b58\u5668\u548c DDR\uff0c\u901a\u8fc7 `/dev/xdma${XDMA_ID}_c2h_0` \u8bfb\u53d6\u72b6\u6001\u5bc4\u5b58\u5668\u548c\u8f93\u51fa\u6570\u636e\u3002 ## board runtime command \u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a ```bash scripts/board/run_pyjm12_smoke.sh ``` \u5efa\u8bae Stage 0 \u63d0\u53d6\u4e3a\uff1a\n... truncated 106 chars ...",
      "field": "runtime_interface.board_run_command",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "scripts/board/run_pyjm12_smoke.sh"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u53d6\u72b6\u6001\u5bc4\u5b58\u5668\u548c\u8f93\u51fa\u6570\u636e\u3002 ## board runtime command \u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a ```bash scripts/board/run_pyjm12_smoke.sh ``` \u5efa\u8bae Stage 0 \u63d0\u53d6\u4e3a\uff1a ```bash scripts/board/run_pyjm12_smoke.sh ``` \u8be5\u547d\u4ee4\u4f1a\uff1a * \u68c0\u67e5 `/home\n... truncated 106 chars ...",
      "field": "runtime_interface.board_run_command",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "scripts/board/run_pyjm12_smoke.sh"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u53d8\u5316\u548c\u6709\u6548\u8f93\u51fa\u8bfb\u56de\u4f5c\u4e3a smoke pass \u6761\u4ef6\u3002 ## runtime_interface\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `control_protocol`: `xdma_raw_register_and_ddr` * `board_run_command`: `scripts/board/run_pyjm12_smoke.sh` * `remote_host`: \n... truncated 111 chars ...",
      "field": "runtime_interface.board_run_command",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "scripts/board/run_pyjm12_smoke.sh"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "`\uff1b * \u5199\u63a7\u5236\u5bc4\u5b58\u5668\u542f\u52a8\u63a8\u7406\uff1b * \u8f6e\u8be2\u72b6\u6001\u5bc4\u5b58\u5668\uff1b * \u4ece `OUTPUT_ABS` \u8bfb\u53d6\u8f93\u51fa\u5934\u90e8\uff1b * \u4ee5 result status \u53d8\u5316\u548c\u6709\u6548\u8f93\u51fa\u8bfb\u56de\u4f5c\u4e3a smoke pass \u6761\u4ef6\u3002 ## runtime_interface\u5e94\u63d0\u53d6\u7684\u5b57\u6bb5 * `control_protocol`: `xdma_raw_register_and_ddr` * `bo\n... truncated 123 chars ...",
      "field": "runtime_interface.control_protocol",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "xdma_raw_register_and_ddr"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "ma_raw_register_and_ddr` * `board_run_command`: `scripts/board/run_pyjm12_smoke.sh` * `remote_host`: \u5982\u679c\u901a\u8fc7\u8fdc\u7aef\u670d\u52a1\u5668\u6267\u884c\u5de5\u5177\u6216\u677f\u5361\u6d41\u7a0b\uff0c\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u677f\u5361 runtime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\n... truncated 99 chars ...",
      "field": "runtime_interface.remote_host",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "hyyuan@10.12.133.23"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002 * \u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002 * \u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /home/test/mimic_driver_c6`\u3002 host runt\n... truncated 116 chars ...",
      "field": "runtime_interface.mimic_dir",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "/home/test/mimic_driver_c6"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "ard/run_pyjm12_smoke.sh` * `remote_host`: \u5982\u679c\u901a\u8fc7\u8fdc\u7aef\u670d\u52a1\u5668\u6267\u884c\u5de5\u5177\u6216\u677f\u5361\u6d41\u7a0b\uff0c\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u677f\u5361 runtime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\u6599\u4e2d\u66ff\u6362\u3002 * `mimic_dir`: `/home/test/mimic_driver_c6` * `xdma_i\n... truncated 119 chars ...",
      "field": "runtime_interface.mimic_dir",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "/home/test/mimic_driver_c6"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002 * \u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002 * \u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /\n... truncated 90 chars ...",
      "field": "runtime_interface.xdma_id_default",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 1
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u901a\u8fc7\u8fdc\u7aef\u670d\u52a1\u5668\u6267\u884c\u5de5\u5177\u6216\u677f\u5361\u6d41\u7a0b\uff0c\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u677f\u5361 runtime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\u6599\u4e2d\u66ff\u6362\u3002 * `mimic_dir`: `/home/test/mimic_driver_c6` * `xdma_id_default`: `1` * `ctrl_base`: `0x3000000000\n... truncated 100 chars ...",
      "field": "runtime_interface.xdma_id_default",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": 1
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "DDR/AXI-compatible\uff0c\u4e0d\u80fd\u7528\u53ea\u542b\u7b80\u5355\u5185\u5b58\u6a21\u578b\u7684 64-bit \u4eff\u771f scaffold \u4ee3\u66ff\u771f\u5b9e\u677f\u7ea7\u63a5\u53e3\u3002 ## host\u4fa7\u5730\u5740\u548cruntime\u63a7\u5236 \u5f53\u524d\u677f\u7ea7\u8c03\u8bd5\u811a\u672c\u4f7f\u7528 XDMA raw \u5730\u5740\u8bbf\u95ee\u3002\u5173\u952e\u5730\u5740\u5982\u4e0b\uff1a * \u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002 * DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x\n... truncated 101 chars ...",
      "field": "runtime_interface.ctrl_base",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "0x3000000000"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "`hyyuan@10.12.133.23`\uff1b\u677f\u5361 runtime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\u6599\u4e2d\u66ff\u6362\u3002 * `mimic_dir`: `/home/test/mimic_driver_c6` * `xdma_id_default`: `1` * `ctrl_base`: `0x3000000000` * `ddr_base`: `0x2800000\n... truncated 104 chars ...",
      "field": "runtime_interface.ctrl_base",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "0x3000000000"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u771f scaffold \u4ee3\u66ff\u771f\u5b9e\u677f\u7ea7\u63a5\u53e3\u3002 ## host\u4fa7\u5730\u5740\u548cruntime\u63a7\u5236 \u5f53\u524d\u677f\u7ea7\u8c03\u8bd5\u811a\u672c\u4f7f\u7528 XDMA raw \u5730\u5740\u8bbf\u95ee\u3002\u5173\u952e\u5730\u5740\u5982\u4e0b\uff1a * \u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002 * DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002 * \u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = \n... truncated 100 chars ...",
      "field": "runtime_interface.ddr_base",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "0x2800000000"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "ime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\u6599\u4e2d\u66ff\u6362\u3002 * `mimic_dir`: `/home/test/mimic_driver_c6` * `xdma_id_default`: `1` * `ctrl_base`: `0x3000000000` * `ddr_base`: `0x2800000000` * `output_abs`: `0x28092\n... truncated 104 chars ...",
      "field": "runtime_interface.ddr_base",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "0x2800000000"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "\u63a7\u5236 \u5f53\u524d\u677f\u7ea7\u8c03\u8bd5\u811a\u672c\u4f7f\u7528 XDMA raw \u5730\u5740\u8bbf\u95ee\u3002\u5173\u952e\u5730\u5740\u5982\u4e0b\uff1a * \u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002 * DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002 * \u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = 0x28092f1000`\u3002 * \u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/ho\n... truncated 103 chars ...",
      "field": "runtime_interface.output_abs",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "0x28092f1000"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "`mimic_dir`: `/home/test/mimic_driver_c6` * `xdma_id_default`: `1` * `ctrl_base`: `0x3000000000` * `ddr_base`: `0x2800000000` * `output_abs`: `0x28092f1000` * `ddr_image_default`: \n... truncated 104 chars ...",
      "field": "runtime_interface.output_abs",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "0x28092f1000"
    },
    {
      "chunk_id": "board:000003",
      "excerpt": "_driver_c6` * `xdma_id_default`: `1` * `ctrl_base`: `0x3000000000` * `ddr_base`: `0x2800000000` * `output_abs`: `0x28092f1000` * `ddr_image_default`: `/home/test/pyjm12_alllayers_9\n... truncated 193 chars ...",
      "field": "runtime_interface.ddr_image_default",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "value": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin"
    },
    {
      "chunk_id": "tools:000002",
      "excerpt": "me/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md offset:0-637 ```text # VCS\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u529f\u80fd\u9a8c\u8bc1\u9636\u6bb5\uff0c\u7528\u4e8e\u7f16\u8bd1\u548c\u8fd0\u884c SystemVeril\n... truncated 96 chars ...",
      "field": "tool.vcs.host",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
      "value": "hyyuan@10.12.133.23"
    },
    {
      "chunk_id": "tools:000002",
      "excerpt": "bin/vcs -ID` * Stage 0 \u5fc5\u987b\u901a\u8fc7 SSH \u5b9e\u9645\u63a2\u6d4b\u8be5\u547d\u4ee4\u53ef\u8c03\u7528\uff0c\u4e0d\u80fd\u53ea\u56e0\u4e3a\u6587\u6863\u91cc\u5199\u4e86\u8def\u5f84\u5c31\u8ba4\u4e3a VCS \u53ef\u7528\u3002 * \u8fd0\u884c VCS \u65f6\u9700\u8981\u8bbe\u7f6e\uff1a * `VCS_TARGET_ARCH=linux64` * `REMOTE_HOST=hyyuan@10.12.133.23` * `REMOTE_VCS_HOME=/home/EDA/Soft\n... truncated 91 chars ...",
      "field": "tool.vcs.host",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vcs.md",
      "value": "hyyuan@10.12.133.23"
    },
    {
      "chunk_id": "tools:000004",
      "excerpt": "ote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md offset:0-539 ```text # Vivado\u5de5\u5177\u4f4d\u7f6e\u548c\u4f7f\u7528\u65b9\u5f0f * \u6240\u5728\u673a\u5668\uff1ahyyuan@10.12.133.23 * \u7528\u9014\uff1a\u7efc\u5408\u3001\u5e03\u5c40\u5e03\u7ebf\u3001\u751f\u6210 bitstream\u3002 * \u53ef\u6267\n... truncated 96 chars ...",
      "field": "tool.vcs.host",
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools/vivado.md",
      "value": "hyyuan@10.12.133.23"
    },
    {
      "_omitted_items": 12
    }
  ],
  "policy": {
    "candidate_only": true,
    "critical_fields_must_match_evidence_when_present": true,
    "llm_output_is_not_accepted_as_evidence_without_source": true,
    "llm_semantic_confirmation_required": true,
    "regex_is_not_semantic_ground_truth": true
  },
  "schema_version": "spatialaccagent.field_evidence_candidates.v0"
}
</compacted_candidate_evidence>

<candidate_policy>
Deterministic candidates are hints and source excerpts, not accepted evidence. Return only fields supported by the compacted evidence, and preserve uncertainty or conflicts.
</candidate_policy>

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
