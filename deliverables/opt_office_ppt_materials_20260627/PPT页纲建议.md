# OPT + Office PPT 页纲建议

## 第 1 页：项目目标与完整流程

标题建议：

```text
OPT + Office 应用加速全流程
```

核心图：

```text
应用算法分析
-> 算核抽取构建
-> 构件生成
-> 应用部署
-> 应用运行
```

要点：

- 以 OPT/PYJM 口令生成和 Office2010 口令验证为应用示例；
- 展示从算法到 FPGA 上板运行的完整工程链路；
- 当前材料只讲项目，不讲论文和 agent 框架。

## 第 2 页：应用算法分析

标题建议：

```text
应用算法分析：OPT 生成候选口令，Office 验证口令
```

内容：

- 输入：口令 pattern 分布表；
- OPT/PYJM 加速器：根据 pattern 生成候选 password；
- 转换：password 转 Office exact hcmask；
- Office2010 FPGA runtime：批量验证 mask；
- 输出：命中 password 或完成无命中。

可放流程：

```text
patterns.txt
-> OPT/PYJM FPGA
-> 10^4_fpga.txt
-> pyjm_passwords_to_hcmask.py
-> 1.hcmask
-> Office2010 FPGA test
```

## 第 3 页：算核抽取与算核库

标题建议：

```text
算核抽取构建：从 OPT Transformer Block 到硬件算核库
```

内容：

```text
LN1 -> QKVLinear -> Attention(DM1/Softmax/VCache/DM2)
-> OutLinear -> ResAdd1 -> LN2 -> FFNUp -> FFNDown -> ResAdd2
```

关键参数：

- hidden size = 768；
- head 数 = 12；
- head dim = 64；
- 每 token = 64 beat；
- full-seq = 912 token；
- full-seq 输出 = 58368 beat。

算核库目录：

```text
src/main/scala
```

## 第 4 页：硬件构件生成

标题建议：

```text
构件生成：Chisel 算核到 Vivado IP
```

内容：

- Chisel 算核库；
- `Top.scala` 完成 Transformer block 集成；
- `AxiBoardSystemTop.sv` 完成 AXI/DDR 系统封装；
- Vivado IP 交付目录 `deliverables/vivado_opt_acc_core_ip`；
- IP 名称建议 `opt_acc_core`。

可放流程：

```text
Chisel 算核库
-> Top.scala
-> generated Top.sv / Top_vivado.sv
-> opt_acc_core.sv wrapper
-> Vivado IP
-> bitstream
```

## 第 5 页：验证与工具链

标题建议：

```text
工具链：真实数据验证、远程仿真、板卡调试
```

内容：

- 真实数据 case 生成：`opt125m_e2e.py`；
- stage-level / full-seq case；
- VCS / Verilator 远程验证；
- board debug regs；
- latency 测量；
- deployment preflight check。

可放工具链表：

| 类别 | 文件 |
| --- | --- |
| Chisel 构建 | `build.sbt`、`build.mill` |
| 验证生成 | `scripts/verification/opt125m_e2e.py` |
| 远程仿真 | `remote_vcs.sh`、`remote_verilator.sh` |
| 系统 wrapper | `verification/rtl/AxiBoardSystemTop.sv` |
| 板卡调试 | `debug_regs_check.c`、`measure_pyjm12_latency.c` |

## 第 6 页：应用部署

标题建议：

```text
应用部署：OPT/PYJM + Office2010 Runtime Package
```

内容：

- 部署目录：`/home/hyyuan/pyjm12_demo`；
- 部署包构建：`build_runtime_package.sh`；
- 节点初始化：`init_node.sh`；
- 部署前检查：`preflight_check.sh`；
- 包含 bitstream、DDR image、host tool、Office runtime、SDK libs、运行脚本。

注意：

- PPT 材料包不放大文件；
- 正式部署包脚本负责检查文件尺寸和依赖。

## 第 7 页：应用运行

标题建议：

```text
应用运行：单卡和 8 卡并行 Office 验证流程
```

内容：

单卡入口：

```text
run_pyjm_office2010_single_card.sh
```

多卡入口：

```text
run_pyjm_office2010_multi_card.sh
```

运行流程：

```text
1. 烧 OPT/PYJM bitstream
2. 加载 DDR image
3. OPT/PYJM 生成候选口令
4. 转 Office hcmask
5. 烧 Office2010 bitstream
6. Office2010 批量验证
7. 输出 password 或 no-hit 状态
```

多卡能力：

- 默认 8 卡：`0,1,2,3,4,5,6,7`；
- 每卡独立日志；
- 支持 app status JSON 更新；
- 支持 parallel / sequential。

## 第 8 页：项目成果总结

标题建议：

```text
当前已形成的项目资产
```

四类成果：

1. 算核库：OPT Transformer block 各级硬件算核；
2. 构件链：Chisel -> RTL -> AXI/DDR wrapper -> Vivado IP；
3. 工具链：真实数据、仿真、综合、板卡调试；
4. 部署链：OPT/PYJM 口令生成 + Office2010 验证的单卡/8卡运行流程。

最后一句：

```text
该项目已经从单个算子开发推进到“应用级 FPGA 运行闭环”的工程阶段。
```

