# Vivado工具位置和使用方式

* 所在机器：hyyuan@10.12.133.23
* 用途：综合、布局布线、生成 bitstream。
* 可执行文件：/home/EDA/Xilinx/Vivado/2021.1/bin/vivado
* 版本探测命令：
  * `/home/EDA/Xilinx/Vivado/2021.1/bin/vivado -version`
* 已确认版本：Vivado v2021.1。
* Stage 0 必须通过 SSH 实际探测该命令可调用，不能只因为文档里写了路径就认为 Vivado 可用。
* 运行 Vivado 时需要设置：
  * `REMOTE_HOST=hyyuan@10.12.133.23`
  * `VIVADO_BIN=/home/EDA/Xilinx/Vivado/2021.1/bin/vivado`
* 当前框架已有的 Qwen Vivado 脚本：
  * `scripts/synthesis/run_qwen_generated_bitstream_23.sh`
* Vivado 是最终综合、实现和 bitstream evidence 的必选工具；缺失或探测失败时 Stage 0 必须失败。
