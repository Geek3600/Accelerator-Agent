# OPT + Office 项目内容总结

## 1. 项目定位

本项目面向“OPT + Office”应用场景，完成从应用算法分析、算核抽取构建、硬件构件生成、应用部署到应用运行的完整链路。

这里的重点不是论文方法，也不是 agent 框架，而是当前项目已经形成的工程内容：

- 面向 OPT-125M / PYJM 口令生成任务的 FPGA 硬件加速器；
- 面向 Office2010 口令验证任务的板卡运行流程；
- 从模型算子到 Chisel/RTL/IP，再到 bitstream、DDR image、host runtime、Office 测试程序的部署链路；
- 支持单卡和 8 卡并行运行的应用脚本。

## 2. PPT 可以讲的主流程

建议按照以下主线组织 PPT：

```text
应用算法分析
-> 算核抽取构建
-> 构件生成
-> 应用部署
-> 应用运行
```

结合本项目实际，对应关系如下。

| 流程阶段 | 本项目内容 | 关键产物 |
| --- | --- | --- |
| 应用算法分析 | 分析 OPT/PYJM 口令生成和 Office2010 口令验证应用 | pattern 分布、口令生成任务、Office mask 验证流程 |
| 算核抽取构建 | 从 OPT-125M Transformer block 中抽取硬件算核 | LayerNorm、QKV、Attention、Softmax、OutLinear、Residual、FFN 等算核 |
| 构件生成 | 用 Chisel 构建算核库、Top、AXI/DDR wrapper 和 Vivado IP | `src/main/scala`、`generated/Top.sv`、`deliverables/vivado_opt_acc_core_ip` |
| 应用部署 | 打包 bitstream、DDR image、host 工具、Office runtime 和部署脚本 | `pyjm12_demo` runtime package、board deploy scripts |
| 应用运行 | 先用 OPT 加速器生成候选口令，再转 Office hcmask 并调用 Office2010 FPGA 验证 | `run_pyjm_office2010_single_card.sh`、`run_pyjm_office2010_multi_card.sh` |

## 3. 应用算法分析：OPT + Office 的任务拆解

### 3.1 OPT / PYJM 口令生成任务

项目中的 OPT 加速器用于 PYJM 口令生成场景。输入是口令模式 pattern，例如：

```text
L8
L6
L7
N7
L6 N2
```

这些 pattern 来自统计分布文件：

```text
pipeline/patterns.txt
```

运行时按照 pattern 的比例分配总生成数量，例如生成 10000 个候选口令。板卡端程序对每个 pattern 发起一次 OPT/PYJM FPGA 推理，读回候选 password。

关键脚本：

```text
scripts/board/pyjm_fpga_batch_gen.py
scripts/board/pyjm_fpga_demo.c
scripts/board/run_pyjm_batch_demo.sh
```

### 3.2 Office2010 口令验证任务

OPT/PYJM 生成出的候选口令需要转换成 Office2010 能直接验证的 mask 格式。

转换脚本：

```text
scripts/board/pyjm_passwords_to_hcmask.py
```

转换逻辑：

```text
pattern<TAB>password
-> exact Office hcmask
```

例如 password 为 `abc123` 时，转换成逐字符精确 mask：

```text
#a#b#c#1#2#3
```

随后烧写 Office2010 bitstream，并调用 Office2010 测试程序批量验证 mask。

关键脚本：

```text
scripts/board/run_pyjm_office2010_single_card.sh
scripts/board/run_pyjm_office2010_multi_card.sh
```

## 4. 算核抽取构建：从 OPT block 到硬件算核库

当前加速器围绕 OPT-125M Transformer block 构建，核心结构是：

```text
LN1
-> QKVLinear
-> Attention(DM1 -> Softmax -> VCache -> DM2)
-> OutLinear
-> ResAdd1
-> LN2
-> FFNUp(ReLU fused)
-> FFNDown
-> ResAdd2
```

基础模型参数：

| 项目 | 数值 |
| --- | --- |
| hidden size | 768 |
| head 数 | 12 |
| head dim | 64 |
| 每拍 lane 数 | 12 |
| 一个 token 向量 beat 数 | 64 |
| full-seq token 数 | 912 |
| full-seq 最终输出 beat 数 | 912 * 64 = 58368 |

### 4.1 已形成的算核库

项目中已经形成了以 Chisel 实现的算核库，主要位于：

```text
src/main/scala
```

主要算核如下。

| 算核类别 | 代码目录 / 模块 | 功能 |
| --- | --- | --- |
| LayerNorm | `LayerNormQ`、`LayerNorm` | 归一化，支持 FP32 输入、INT8 输出量化 |
| QKV 投影 | `QKVLinear` | 生成 Q/K/V，支持 INT8 权重和 INT8 激活 |
| Attention QK | `DM` | Q·K 点积，INT8 输入、FP32 输出 |
| Softmax | `Softmax` | FP32 softmax |
| Attention PV | `DM2` | P·V 计算，softmax 输出量化后与 V 计算 |
| 输出投影 | `OutLinear` | attention output projection |
| 残差加法 | `ResAdd`、`ResAdd2` | attention 后和 FFN 后 residual add |
| FFN 升维 | `FFNUp` | H -> 4H，ReLU 融合 |
| FFN 降维 | `FFNDown` | 4H -> H |
| 量化公共库 | `QuantCommon` | FP32、INT8、pack、linear epilogue、Xilinx 兼容辅助 |
| 输入/地址适配 | `TempAdapter` | token/beat 地址和输入流控制 |
| Attention history | `ResMEM` | attention 长序列历史数据支撑 |
| 顶层集成 | `Top.scala` | 串接完整 Transformer block 主链 |

### 4.2 量化策略

项目采用混合精度策略：

| 模块 | 输入精度 | 权重精度 | 输出精度 |
| --- | --- | --- | --- |
| LayerNorm1 | FP32 | - | INT8 |
| QKVLinear | INT8 | INT8 | INT8 |
| Q·K / DM1 | INT8 x INT8 | - | FP32 |
| Softmax | FP32 | - | FP32 |
| P·V / DM2 | INT8 x INT8 | - | INT8 |
| OutLinear | INT8 | INT8 | FP32 |
| ResAdd1 | FP32 | - | FP32 |
| LayerNorm2 | FP32 | - | INT8 |
| FFNUp + ReLU | INT8 | INT8 | INT8 |
| FFNDown | INT8 | INT8 | FP32 |
| ResAdd2 | FP32 | - | FP32 |

对应文档：

```text
docs/opt_quan.md
```

## 5. 构件生成：从算核库到 FPGA 构件

### 5.1 Chisel 到 RTL

硬件主体用 Chisel 编写，通过 Scala/Chisel 工具链生成 Verilog/SystemVerilog。

主要构建配置：

```text
build.sbt
build.mill
src/main/scala
src/test/scala
```

主要顶层：

```text
src/main/scala/Top.scala
```

### 5.2 系统级 AXI/DDR wrapper

为了将算核接入真实板卡运行，项目中实现了 AXI/DDR wrapper。

关键文件：

```text
verification/rtl/AxiBoardSystemTop.sv
```

它负责：

- 从 DDR 读取 input、weight、bias、scale 等数据；
- 将权重装载到 core；
- 按 token / layer 调度 12 层运行；
- 处理 full-seq attention 所需的长序列历史；
- 将最终输出写回 DDR；
- 通过 AXI 接口与板卡 shell 对接。

### 5.3 Vivado IP 交付件

项目已整理出 standalone Vivado IP 交付目录：

```text
deliverables/vivado_opt_acc_core_ip
```

目录中包括：

```text
hdl/opt_acc_core.sv
hdl/Top_vivado.sv
opt_acc_core_resources.xdc
README.txt
```

推荐 IP identity：

```text
Vendor  = user.org
Library = user
Name    = opt_acc_core
Version = 1.0
```

说明：不要把该 IP 打包成 `cnn_core`，避免和原始 sample BD 中的 `cnn_core_1` 冲突。

## 6. 工具链：验证、综合、运行支撑

### 6.1 真实数据验证工具链

主脚本：

```text
scripts/verification/opt125m_e2e.py
```

它负责：

- 解析 PyTorch / torch text dump；
- 抽取 named tensor；
- 生成 metadata 和 binary artifact；
- 生成 DDR image；
- 生成 golden；
- 组织 Verilator / VCS 仿真；
- 支持 stage-level、window-level、full-seq 验证。

典型 case：

```text
verification/cases/opt125m_stage_full
verification/cases/opt125m_9p_fullseq
verification/cases/pyjm_9p_fullseq
```

### 6.2 远程验证工具链

远端 VCS / Verilator 脚本：

```text
scripts/verification/remote_vcs.sh
scripts/verification/remote_verilator.sh
scripts/verification/run_vcs_server.sh
scripts/verification/run_verilator_server.sh
```

用途：

- 同步本地代码到远端服务器；
- 调用 VCS 或 Verilator；
- 运行 full-seq 和 board-level 验证；
- 统一输出验证日志和结果。

### 6.3 后端与板卡调试工具

板卡运行和调试相关工具：

```text
scripts/board/debug_regs_check.c
scripts/board/measure_pyjm12_latency.c
scripts/board/run_pyjm12_smoke.sh
scripts/board/README_debug_regs.md
```

用途：

- 检查 debug register magic；
- 写配置寄存器；
- 启动 accelerator；
- 轮询 status；
- 测量 host-observed latency；
- 做短流程 board smoke test。

## 7. 应用部署：OPT + Office runtime package

部署目标路径：

```text
/home/hyyuan/pyjm12_demo
```

部署包构建脚本：

```text
scripts/board/deploy/build_runtime_package.sh
```

节点初始化脚本：

```text
scripts/board/deploy/init_node.sh
```

部署前检查脚本：

```text
scripts/board/deploy/preflight_check.sh
```

部署包包含：

- OPT/PYJM bitstream；
- OPT/PYJM DDR image；
- pattern 分布表；
- host runtime C 程序；
- batch 生成脚本；
- Office hcmask 转换脚本；
- Office2010 runtime；
- Office2010 bitstream；
- Mimic SDK 依赖库；
- 单卡和多卡运行脚本；
- app status 前端状态更新脚本。

注意：bitstream、DDR image、Office runtime tar、模型压缩包体积较大，本 PPT 材料包不直接包含这些大文件，只列出它们在正式部署包中的名称和用途。

## 8. 应用运行：单卡和 8 卡流程

### 8.1 单卡流程

入口脚本：

```text
scripts/board/run_pyjm_office2010_single_card.sh
```

流程：

```text
1. OPT/PYJM FPGA 生成候选口令
2. 将候选口令转换成 Office2010 exact hcmask
3. 烧写 Office2010 bitstream
4. Office2010 测试程序批量验证 hcmask
5. 若命中，输出 password；若未命中，返回 exhausted 状态
```

### 8.2 多卡流程

入口脚本：

```text
scripts/board/run_pyjm_office2010_multi_card.sh
```

功能：

- 支持 8 卡并行；
- 每张卡建立独立 runtime 目录；
- 自动映射 card id 到 xdma id；
- 支持并行或顺序运行；
- 支持应用状态 JSON 更新；
- 汇总每张卡日志。

默认卡配置：

```text
cards = 0,1,2,3,4,5,6,7
```

典型正式运行命令：

```bash
PYJM_SUDO_PASSWORD=<sudo-password> ./run_pyjm_office2010_multi_card.sh \
  --cards 0,1,2,3,4,5,6,7 \
  --parallel \
  --total-generate 10000 \
  --poll-timeout-ms 5000
```

返回码含义：

```text
exit=0  Office2010 找到 password
exit=4  流程正常完成，但没有命中
其他     真实错误，需要检查日志
```

## 9. PPT 中建议强调的项目成果

可以概括成四句话：

1. 已经形成一套面向 OPT-125M / PYJM 应用的 FPGA Transformer block 加速器算核库。
2. 已经形成从 Chisel 算核、RTL 顶层、AXI/DDR wrapper 到 Vivado IP 的硬件构件生成链路。
3. 已经形成真实数据验证、VCS/Verilator 远程验证、板卡 debug/latency 测试的工具链。
4. 已经形成 OPT 口令生成 + Office2010 口令验证的单卡/8卡应用部署和运行流程。

## 10. 当前边界

为避免 PPT 过度表述，建议使用以下边界：

- 当前 PPT 只讲项目工程链路，不讲论文方法和 agent framework。
- OPT 加速器是面向 PYJM/口令生成应用的硬件加速核心。
- Office2010 是下游验证应用，用于展示候选口令生成后的应用级闭环。
- 大文件如 bitstream、DDR image、Office runtime 不进入本材料压缩包，但已经在部署脚本和部署包构建脚本中被明确管理。

