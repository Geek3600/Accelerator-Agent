<agent>
board_profile_agent
</agent>

<task>
Act as the FPGA board/platform engineer. Extract the target_board_profile JSON from current-run board/platform materials.
</task>

<rules>
1. Treat the board materials directory as the complete current-run board input.
2. Field evidence summary is the source-of-truth audit trail. Critical FPGA part, DDR/AXI, runtime command, and control protocol fields must match evidence when evidence exists.
3. The downstream accelerator must keep DDR/AXI-compatible board flow, so DDR channels, AXI width, control protocol, runtime command, remote host, and FPGA part are critical.
4. Put all FPGA board, shell, memory, runtime, and pass/fail fields inside the schema sections.
5. Use null for unknown board facts and record uncertainty in notes.
6. Do not invent resource numbers that are not present in the source information.
7. If sample projects or scripts imply board flow, use only the summarized evidence and do not repeat long file listings.
8. Extract runtime ABI fields such as control base, DDR base, output address, device id, runtime directory, image path, board AXI prefix, clock/reset, and calibration signal only when they appear in source evidence.
</rules>

<board_materials_summary>
{
  "chunk_count": 4,
  "file_count": 4,
  "files": [
    {
      "chars": 463,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/README.md",
      "suffix": ".md"
    },
    {
      "chars": 1760,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0\u677f\u5361\u4f7f\u7528\u6587\u6863.docx",
      "suffix": ".docx"
    },
    {
      "chars": 2767,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "suffix": ".md"
    },
    {
      "chars": 489,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md",
      "suffix": ".md"
    }
  ],
  "label": "board",
  "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board",
  "schema_version": "spatialaccagent.material_index_summary.v0",
  "skipped": [],
  "skipped_count": 0
}
</board_materials_summary>

<sample_project_summary>
{
  "policy": {
    "max_files": 3000,
    "max_grep_matches": 500,
    "read_only_remote_inputs": true,
    "timeout_sec": 60
  },
  "refs": [
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/test/mimic_driver_c6",
      "source_path": "/home/test/mimic_driver_c6/xdma_driver/tools/dma_to_device"
    },
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8",
      "source_path": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr"
    },
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/README.md",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/README.md"
    },
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_"
    },
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
      "source_path": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin"
    },
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
    },
    {
      "host": "hyyuan@10.12.133.23",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0"
    }
  ],
  "samples": [
    {
      "error": "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
      "file_count": 0,
      "file_list_excerpt": [],
      "grep_evidence_excerpt": "",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "",
      "port": 22,
      "root": "/home/test/mimic_driver_c6",
      "source_path": "/home/test/mimic_driver_c6/xdma_driver/tools/dma_to_device",
      "status": "error"
    },
    {
      "error": null,
      "file_count": 1608,
      "file_list_excerpt": [
        "1/9b012c8b6c042c00/9b012c8b6c042c00.xci",
        "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.cache/ip/2021.1/9b012c8b6c042c00/app_shell_9p_xbar_0_stub.v",
        "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.cache/ip/2021.1/9b012c8b6c042c00/app_shell_9p_xbar_0_stub.vhdl",
        "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.cache/ip/2021.1/9b012c8b6c042c00/app_shell_9p_xbar_0_sim_netlist.v",
        "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.cache/ip/2021.1/9b012c8b6c042c00/app_shell_9p_xbar_0_sim_netlist.vhdl"
      ],
      "grep_evidence_excerpt": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.ip_user_files/bd/app_shell_9p/ip/app_shell_9p_util_vector_logic_0_0/sim/app_shell_9p_util_vector_logic_0_0.v:24:// (including loss of data, profits, goodwill, or any type of\n/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.ip_user_files/bd/app_shell_9p/ip/app_shell_9p_util_vector_logic_0_0/sim/app_shell_9p_util_vector_logic_0_0.v:50:// IP VLNV: xilinx.com:ip:util_vector_logic:2.0\n/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.ip_user_files/bd/app_shell_9p/ip/app_shell_9p_vio_0_0/sim/app_shell_9p_vio_0_0.v:24:// (including loss of data, profits, goodwill, or any type of\n/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.ip_user_files/bd/app_shell_9p/ip/app_shell_9p_vio_0_0/app_shell_9p_vio_0_0_sim_netlist.v:283:  (* C_BUS_ADDR_WIDTH = \"17\" *) \n/h",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr:10:    <Option Name=\"Part\" Val=\"xcvu9p_CIV-flgb2104-2-i\"/>\n/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr:231:    <Run Id=\"synth_1\" Type=\"Ft3:Synth\" SrcSet=\"sources_1\" Part=\"xcvu9p_CIV-flgb2104-2-i\" ConstrsSet=\"constrs_1\" Description=\"Vivado Synthesis Defaults\" AutoIncrementalCheckpoint=\"false\" WriteIncrSynthDcp=\"false\" State=\"current\" Dir=\"$PRUNDIR/synth_1\" IncludeInArchive=\"true\" IsChild=\"false\" AutoIncrementalDir=\"$PPRDIR/../../../../v6.0/app_shell_9p/app_shell_9p/app_shell_9p.srcs/uti",
      "port": 22,
      "root": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8",
      "source_path": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr",
      "status": "ok"
    },
    {
      "error": "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
      "file_count": 0,
      "file_list_excerpt": [],
      "grep_evidence_excerpt": "",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/README.md",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/README.md",
      "status": "error"
    },
    {
      "error": "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
      "file_count": 0,
      "file_list_excerpt": [],
      "grep_evidence_excerpt": "",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_",
      "status": "error"
    },
    {
      "error": "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
      "file_count": 0,
      "file_list_excerpt": [],
      "grep_evidence_excerpt": "",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "",
      "port": 22,
      "root": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
      "source_path": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
      "status": "error"
    },
    {
      "error": "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
      "file_count": 0,
      "file_list_excerpt": [],
      "grep_evidence_excerpt": "",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
      "status": "error"
    },
    {
      "error": "bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8); bash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
      "file_count": 0,
      "file_list_excerpt": [],
      "grep_evidence_excerpt": "",
      "host": "hyyuan@10.12.133.23",
      "part_evidence_excerpt": "",
      "port": 22,
      "root": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0",
      "source_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0",
      "status": "error"
    }
  ],
  "schema_version": "spatialaccagent.sample_project_summary.v0"
}
</sample_project_summary>

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
          "chunk_id": "board:000004",
          "excerpt": "\u6837\u4f8b\u5de5\u7a0b Vivado project \u4e2d\u7684\u5177\u4f53 part \u662f `xcvu9p_CIV-flgb2104-2-i`",
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
          "excerpt": "\u5f53\u524d\u6838\u5fc3\u4f7f\u7528\u4e00\u4e2a DDR AXI channel\uff1a`c0_ddr4_s_axi_*`\u3002... `ddr_channels`: 1",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 1
        }
      ],
      "field": "memory_system.ddr_channels"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u6570\u636e\u4f4d\u5bbd\uff1a`C_DATA_WIDTH = 512`\u3002* AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002... `ddr_word_width_bits`: 512",
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
          "excerpt": "AXI \u6570\u636e\u5bbd\u5ea6\uff1a512 bit\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 512
        }
      ],
      "field": "memory_system.axi_data_width_bits"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "AXI beat \u5b57\u8282\u6570\uff1a64 bytes\u3002... 64-bit AXI \u63a5\u53e3\uff0c`AXI_BEAT_BYTES = 8`\u3002\u5b83\u4e0d\u80fd\u4ee3\u8868\u771f\u5b9e app_shell \u677f\u7ea7 DDR/AXI \u63a5\u53e3\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 64
        }
      ],
      "field": "memory_system.axi_data_bytes"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "AXI \u5730\u5740\u5bbd\u5ea6\uff1a37 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awaddr[36:0]` \u548c `c0_ddr4_s_axi_araddr[36:0]`\u3002",
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
          "excerpt": "AXI ID \u5bbd\u5ea6\uff1a4 bit\uff0c\u5178\u578b\u4fe1\u53f7\u4e3a `c0_ddr4_s_axi_awid[3:0]` \u548c `c0_ddr4_s_axi_arid[3:0]`\u3002",
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
          "excerpt": "AXI \u5199 strobe \u5bbd\u5ea6\uff1a64 bit\u3002",
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
          "excerpt": "\u76ee\u6807\u5de5\u7a0b\u4f7f\u7528 app_shell \u91cc\u7684 DDR4 AXI \u63a5\u53e3\uff0c\u6838\u5fc3\u4fa7\u63a5\u53e3\u540d\u662f `c0_ddr4_s_axi_*`\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_ddr4_s_axi_*"
        }
      ],
      "field": "memory_system.core_side_interface_name"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "DDR UI / AXI clock\uff1a`c0_ddr4_s_axi_clk`\u3002... `axi_clock`: `c0_ddr4_s_axi_clk`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_ddr4_s_axi_clk"
        }
      ],
      "field": "memory_system.axi_clock"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "DDR reset\uff1a`c0_ddr4_s_axi_rst_n`\u3002... `axi_reset`: `c0_ddr4_s_axi_rst_n`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "c0_ddr4_s_axi_rst_n"
        }
      ],
      "field": "memory_system.axi_reset"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "DDR calibration done\uff1a`c0_init_calib_complete`\u3002... `calibration_done_signal`: `c0_init_calib_complete`",
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
          "excerpt": "\u53c2\u8003 RTL\uff1a`verification/rtl/cnn_core.sv`\u3002",
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
          "excerpt": "`control_protocol`: `xdma_raw_register_and_ddr`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "xdma_raw_register_and_ddr"
        }
      ],
      "field": "runtime_interface.control_protocol"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a```bash scripts/board/run_pyjm12_smoke.sh ``` \u5efa\u8bae Stage 0 \u63d0\u53d6\u4e3a\uff1a```bash scripts/board/run_pyjm12_smoke.sh ```",
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
          "excerpt": "`remote_host`: \u5982\u679c\u901a\u8fc7\u8fdc\u7aef\u670d\u52a1\u5668\u6267\u884c\u5de5\u5177\u6216\u677f\u5361\u6d41\u7a0b\uff0c\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u677f\u5361 runtime \u5177\u4f53\u6267\u884c\u673a\u5668\u4ee5\u540e\u53ef\u4ee5\u7531\u7528\u6237\u5728\u672c\u76ee\u5f55\u6750\u6599\u4e2d\u66ff\u6362\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "hyyuan@10.12.133.23"
        }
      ],
      "field": "runtime_interface.remote_host"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /home/test/mimic_driver_c6`\u3002... `mimic_dir`: `/home/test/mimic_driver_c6`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "/home/test/mimic_driver_c6"
        }
      ],
      "field": "runtime_interface.mimic_dir"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002... `xdma_id_default`: `1`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": 1
        }
      ],
      "field": "runtime_interface.xdma_id_default"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002... `ctrl_base`: `0x3000000000`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "0x3000000000"
        }
      ],
      "field": "runtime_interface.ctrl_base"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002... `ddr_base`: `0x2800000000`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "0x2800000000"
        }
      ],
      "field": "runtime_interface.ddr_base"
    },
    {
      "count": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "\u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = 0x28092f1000`\u3002... `output_abs`: `0x28092f1000`",
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
          "excerpt": "\u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md",
          "value": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin"
        }
      ],
      "field": "runtime_interface.ddr_image_default"
    }
  ]
}
</field_evidence_summary>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "board": {
      "additionalProperties": true,
      "type": "object"
    },
    "board_pass_criteria": {
      "additionalProperties": true,
      "type": "object"
    },
    "memory_system": {
      "additionalProperties": true,
      "type": "object"
    },
    "notes": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "runtime_interface": {
      "additionalProperties": true,
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    },
    "shell": {
      "additionalProperties": true,
      "type": "object"
    }
  },
  "required": [
    "schema_version",
    "board",
    "shell",
    "memory_system",
    "runtime_interface",
    "board_pass_criteria",
    "notes"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
