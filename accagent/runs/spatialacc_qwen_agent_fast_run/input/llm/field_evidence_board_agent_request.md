<agent>
field_evidence_board_agent
</agent>

<task>
Act as the source-evidence engineer for the board input domain. Review compact current-run candidate excerpts and return only evidence supported by those excerpts.
</task>

<rules>
1. Deterministic regex candidates are hints only, not ground truth.
2. Accept a field only when the cited excerpt semantically supports it.
3. Each evidence item must cite source, chunk_id when available, and a short excerpt from the supplied candidate summary.
4. Reject false positives, stale sample/scaffold interfaces, generic paths, or contradicted values.
5. If compact evidence is insufficient for a field, omit it rather than inventing it.
</rules>

<material_corpus_summary>
{
  "complete_domain_material_is_supplied": true,
  "domain": "board",
  "material_chars": 6113
}
</material_corpus_summary>

<domain_materials_text>
### chunk:board:000001 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/README.md offset:0-463
```text
# Board Input Materials

Place the target FPGA board materials for the current accelerator design run here.
Stage 0 treats this directory as the board input for this run.

Supported inputs:
- docs (`.md`, `.rst`, `.txt`)
- shell/project files (`.tcl`, `.xdc`, `.sdc`, `.sv`, `.v`, `.sh`, `.py`, `.json`, etc.)
- `.docx` and `.pdf` documents
- README/metadata files from sample board projects

These files are scanned recursively and fed to the board-profile LLM.

```

### chunk:board:000002 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0板卡使用文档.docx offset:0-1760
```text
帝江 FPGA卡 example design说明手册 板卡形态 图（1）： 帝江 FPGA卡实物图 本example design 基于帝江 FPGA卡，由一片Zynq MPSo C Ultrascale + XCZU 7 EV和一片 Ultrascale + XCVU 9 P（芯片型号xcvu 9p_CIV-flgb2104-2-i ）构成，板卡实物图如图（1）所示。在物理上，PCIE跟7EV连接，9P与7EV之间通过高速 串行总线实现互连，在逻辑设计上，PCIE与7EV的互连、7EV与9P的互连功能已经设计好并固化在7EV的位流中。7EV的位流固化在板卡的flash上，并在板卡上电后自动加载，而9P的功能需要根据设计者的需求进行定制。 为了方便设计者对9P的使用，本文档给出了9P的一个基础example design，包含两片 32 G DDR 4 以及一个block ram，主要用于演示如何通过PCIE对9P进行的存储设备实现DMA读写以及寄存器读写操作。 E xample design互连结构 图（2）：参考设计的互连结构 例子工程提供的XCVU 9 P结构如图（2）所示。两个Aurora Chip 2 Chip模块输出的两路AXI 4 总线经一个AXI互连模块，与两片3 2 G的DDR 4 互连，此外，为了展示寄存器读写的功能， AXI互连模块还跟一个3 2 bit 位宽的 Block RAM控制器连接。这样，通过已经固化好的7EV结构，就可以借助Aurora 片间互连 ，实现通过PCIE访问9P的DDR 4 以及Block RAM，实现PCIE的DMA操作以及寄存器读写功能。 地址空间映射 在example design中，两片3 2 G的DDR 4 以及BRAM均通过两路Aurora Chip 2 Chip映射到PCIE的地址空间中。在9P中，两片DDR 4 和BRAM的地址空间分配为： 而在7EV中，两路Aurora Chip 2 Chip分配的固定地址为： 起始地址 大小 结束地址 Au rora Chip2Chip channel 0 0x 2000000000 1 28 G 0x 3FFFFFFFFF Au rora Chip2Chip channel 1 0x 4 000000000 1 28 G 0x 5 FFFFFFFFF 那么在PCIE看来，如果通过 Au rora Chip2Chip channel 0 对9P 进行读写操作，那么 9P的DDR 4 _ 0 的起始地址便为： 0x 2000000000 + 0 x 0800000000 = 0x2800000000 。也就是说，9P上存储器在PCIE的地址需要是存储器在9P上分配的基地址加上Aurora 片间互连 的基地址。至于是 0x 2000000000 还是 0x 4000000000 ，取决于顶层通过 那个片间互连 通道实现对9P存储器的读写访问。 顶层驱动 帝江 FPGA卡在Xilinx的 xdma 驱动的基础上进行了二次开发，并设计了基于C /C++ 的API接口，包括如下功能： 功能名 API函数接口 名 说明 系统复位 sys_reset 实现对9P的复位，驱动example design中的 sys_rst_n 信号，持续1秒钟 pcie 复位 pcie_reset 实现对PCIE系统的复位，主要用于对 xdma 通路因非法访问而导致的通路挂掉之后的复原操作。 9P位流下载 program_fpga 实现对9P的位流下载 9P位流清除 program_fpga_clear 实现对9P的位流清除 板卡温度读取 temperature_ detect 检测板卡当前温度 板卡功耗读取 power_monitor 读取板卡当前功耗 9P的 dma 读操作 mm_dma_read 以DMA的方式对9P进行读取操作 9P的 dma 写操作 m m_dma_write 以DMA的方式对9P进行写操作 9P的寄存器读操作 m m_ fpga _read 以寄存器的方式对9P进行读操作 9P的寄存器写操作 m m_ fpga _ write 以寄存器的方 式对9P进行写操作
```

### chunk:board:000003 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md offset:0-2767
```text
# VU9P板级运行和DDR/AXI接口材料

本文件描述本次设计需要对齐的板级 runtime、DDR 和 AXI 信息。Stage 0 应把这些内容提取到 `target_board_profile.memory_system` 和 `target_board_profile.runtime_interface`。

## 真实板级DDR/AXI接口

* 目标工程使用 app_shell 里的 DDR4 AXI 接口，核心侧接口名是 `c0_ddr4_s_axi_*`。
* 参考 RTL：`verification/rtl/cnn_core.sv`。
* 数据位宽：`C_DATA_WIDTH = 512`。
* AXI 数据宽度：512 bit。
* AXI beat 字节数：64 bytes。
* AXI 写 strobe 宽度：64 bit。
* AXI 地址宽度：37 bit，典型信号为 `c0_ddr4_s_axi_awaddr[36:0]` 和 `c0_ddr4_s_axi_araddr[36:0]`。
* AXI ID 宽度：4 bit，典型信号为 `c0_ddr4_s_axi_awid[3:0]` 和 `c0_ddr4_s_axi_arid[3:0]`。
* AXI burst length 宽度：8 bit。
* 当前核心使用一个 DDR AXI channel：`c0_ddr4_s_axi_*`。
* DDR UI / AXI clock：`c0_ddr4_s_axi_clk`。
* DDR reset：`c0_ddr4_s_axi_rst_n`。
* DDR calibration done：`c0_init_calib_complete`。
* 板级 flow 必须保持 DDR/AXI-compatible，不能用只含简单内存模型的 64-bit 仿真 scaffold 代替真实板级接口。

## host侧地址和runtime控制

当前板级调试脚本使用 XDMA raw 地址访问。关键地址如下：

* 控制寄存器基地址：`CTRL_BASE = 0x3000000000`。
* DDR 数据基地址：`DDR_BASE = 0x2800000000`。
* 当前示例输出绝对地址：`OUTPUT_ABS = 0x28092f1000`。
* 当前 DDR image 默认位置：`/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`。
* 默认 XDMA id：`XDMA_ID = 1`。
* 默认 MIMIC runtime 目录：`MIMIC_DIR = /home/test/mimic_driver_c6`。

host runtime 会通过 `/dev/xdma${XDMA_ID}_h2c_0` 写控制寄存器和 DDR，通过 `/dev/xdma${XDMA_ID}_c2h_0` 读取状态寄存器和输出数据。

## board runtime command

当前已有板级 smoke 脚本：

```bash
scripts/board/run_pyjm12_smoke.sh
```

建议 Stage 0 提取为：

```bash
scripts/board/run_pyjm12_smoke.sh
```

该命令会：

* 检查 `/home/test/mimic_driver_c6/xdma_driver/tools/dma_to_device` 和 `dma_from_device`；
* 可选地把 DDR image 写入 `DDR_BASE`；
* 写控制寄存器启动推理；
* 轮询状态寄存器；
* 从 `OUTPUT_ABS` 读取输出头部；
* 以 result status 变化和有效输出读回作为 smoke pass 条件。

## runtime_interface应提取的字段

* `control_protocol`: `xdma_raw_register_and_ddr`
* `board_run_command`: `scripts/board/run_pyjm12_smoke.sh`
* `remote_host`: 如果通过远端服务器执行工具或板卡流程，当前工具服务器为 `hyyuan@10.12.133.23`；板卡 runtime 具体执行机器以后可以由用户在本目录材料中替换。
* `mimic_dir`: `/home/test/mimic_driver_c6`
* `xdma_id_default`: `1`
* `ctrl_base`: `0x3000000000`
* `ddr_base`: `0x2800000000`
* `output_abs`: `0x28092f1000`
* `ddr_image_default`: `/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`

## memory_system应提取的字段

* `ddr_channels`: 1
* `ddr_word_width_bits`: 512
* `axi_data_bytes`: 64
* `axi_addr_width_bits`: 37
* `axi_id_width_bits`: 4
* `axi_wstrb_width_bits`: 64
* `axi_clock`: `c0_ddr4_s_axi_clk`
* `axi_reset`: `c0_ddr4_s_axi_rst_n`
* `calibration_done_signal`: `c0_init_calib_complete`

## 注意

`verification/rtl/AxiBoardSystemTop.sv` 中还有一个用于功能仿真 scaffold 的 64-bit AXI 接口，`AXI_BEAT_BYTES = 8`。它不能代表真实 app_shell 板级 DDR/AXI 接口。Stage 0 如果同时读到这两个口径，必须优先采用真实板级 `cnn_core.sv` / app_shell 的 512-bit DDR AXI 口径，并在 notes 中记录 64-bit scaffold 只是仿真辅助。

```

### chunk:board:000004 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_样例工程.md offset:0-489
```text
# xcvu9p fpga板卡的样例工程
* 位置在 hyyuan@10.12.133.23服务器上，目录位置是/home/share/v6.0_9p_cnn_2slr_4core_yolov8
* 里面有ddr和axi wrapper的样例工程，可以参考
* 样例工程 Vivado project 中的具体 part 是 `xcvu9p_CIV-flgb2104-2-i`，来源是：
  * `/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr`
  * `<Option Name="Part" Val="xcvu9p_CIV-flgb2104-2-i"/>`
* Stage 0 必须提取具体 FPGA part，不能只写 VU9P 这种模糊板卡名。
  
# 限制
* 只能读这里的内容，不能修改，因为要保持目录这个作为样例工程的备份
* 不能在/home/share/目录下创建和修改任何新内容，只能在我们自己的用户目录hyyuan/workspace下进行工作

```
</domain_materials_text>

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
