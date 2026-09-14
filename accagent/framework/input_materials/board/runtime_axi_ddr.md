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
