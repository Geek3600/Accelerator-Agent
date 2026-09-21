# 方法论

## 核心命题

LLM spatial accelerator design 的困难在于跨越多个 lowering boundary 的 contract preservation：

```text
model semantics
-> spatial pipeline
-> Chisel/RTL modules
-> stream interconnect
-> DDR/AXI image
-> host runtime
-> simulation and board execution
```

SpatialAccAgent 是一个 contract-guided design closure system。它的 agent 不是 free-form code generator，而是在 SACG、artifacts、evidence logs 上工作的 contract transformer 和 repairer。

## 设计状态

每一步设计都作用在：

```text
S_t = (G_t, A_t, R_t)
```

其中：

- `G_t` 是当前 SACG；
- `A_t` 是当前 artifact set；
- `R_t` 是当前 evidence/report/log set。

Agent transition 是：

```text
(G_t, A_t, R_t) -> (G_{t+1}, A_{t+1}, R_{t+1})
```

每一次 transition 都必须更新 SACG 或 artifacts，并通过相应的 checker、simulation、regression 或 backend closure step。

## 规范化运行阶段

框架对外只有连续的 Stage 0--7。内部的 `verification_artifacts`、
`debug_loop`、`repair_execution`、快速重放和报告解析只是对应阶段内的执行
模块，不是额外阶段。

### Stage 0. Objective and Input Preparation

读取自然语言任务、目标模型、量化方案、板卡样例工程与工具资料，定义 model
family、block structure、precision、sequence length、target platform、四项 QoR
目标，以及不可改变的空间数据流语义。

输出最小的结构化 model、board、numeric、tool、design-space 输入与初始 contract
boundary。

### Stage 1. SACG Extraction

把 Stage 0 输入构造成初始 SACG：model、shape、numeric、stream、memory、runtime
和 deployment contracts，并记录各事实的来源。

### Stage 2. Trusted Templates and FPGA IP Binding

将模型算子映射到可信空间硬件模板，并把每一个计算和存储角色绑定到目标 FPGA
的真实实现：浮点/计算使用 Vivado floating-point/DSP IP；权重和大容量
attention/KV cache 使用 XPM URAM；activation、FIFO 和常量 ROM 使用 XPM BRAM。

Stage 2 同时定义与实现一致的 VCS 闭包：生成的 Vivado IP 仿真模型、XPM、
`unisims_ver` 和 `glbl.v` 必须以同一模块接口和同一周期延迟参与仿真。不得使用
HardFloat、`SyncReadMem`、Chisel `Queue`、推断通用 `Mem` 或 simulation-only
arithmetic/memory fallback 替代目标 FPGA 资源。

### Stage 3. Model-Derived Spatial Pipeline

从目标模型算子图推导空间并行算子、stage 边界、tile/lane/head mapping、buffer
placement、residual/KV path 和 DDR/AXI schedule。流水级数量由模型结构决定，
不是固定为 11；所有可并行的算子必须保持 token 级重叠执行和正确 ready/valid
回压。

### Stage 4. DSE and Parameter Binding

在 Stage 2/3 固定的语义和物理实现约束内，DSE 精确枚举当前模型、板卡和用户约束
定义的全部合法离散候选。当前进入候选空间的维度仅包括已经改变生成 RTL/IP 的
`lanes`、全局物理 PE 阵列 `compute_array_rows × compute_array_cols`、XPM FIFO depth、
activation XPM bank 数，以及每个权重角色的 BRAM/URAM bank layout。该阵列维度对
所有 Linear/QKV/FFN projection 统一生效；每个 PE 对应一个 DSP-backed Vivado
`fp_mul_sp_*` IP，精确 DSP48 消耗以 Stage 7 Vivado 报告为准。未物理绑定的 tile、
burst 或 pipeline metadata 不得进入搜索或作为
QoR 代理；未来只能在其先绑定到 RTL、IP 或 XDC 后加入。

LLM 可选择尚未测量的合法候选的测量顺序，并解释完成测量后的 Pareto 选择；资源、
功耗、时钟频率和性能绝不由 LLM、解析模型或预测器估算或排序。每个候选的唯一 QoR
权威是 Stage 7 的真实目标板卡 app-shell Vivado implementation 与硬件周期计数器。
DSE 的唯一优化/约束维度是：`resources`、`power_w`、`clock_frequency_mhz` 和
`performance_tokens_per_second`。

### Stage 5. Hardware Implementation and Verification Preparation

合并生成实现和验证准备，一次性交付最小必要闭包：template-bound Chisel/RTL、
真实 AXI/DDR board-shell binding、运行时 memory/weight/activation 映射、真实目标
模型 reference 和 DDR image、语义 testbench、CCTG、三层验证计划，以及硬件
64-bit 周期计数器。

该阶段还生成 FPGA-IP 仿真闭包，供 Stage 6 使用。板级壳必须绑定用户样例工程的
compute slot、AXI、DDR 和双缓冲调度，不得替换成简化 wrapper。

### Stage 6. Hierarchical Real-Workload Verification and Repair

按层次使用真实权重、输入和板级接口完成独立算子、单 Transformer block、真实
AXI/DDR board-wrapper VCS 验证。Layer 3 内部的循环是：

```text
current real VCS -> current internal signals -> SACG/CCTG frontier
-> LLM RTL repair or deeper runtime observation plan -> next real VCS
```

LLM 只基于当前轮真实信号作硬件判断；历史经验可作为先验，但不能替代当前波形。
快速重放仅加速执行，不能进入 LLM 的根因证据。所有仿真都使用 Stage 2 绑定的
Vivado IP/XPM 时序模型。

### Stage 7. Vivado Implementation and QoR Closure

对 Stage 5 的 exact board-integrated source closure 执行 Vivado synthesis、placement
and routing，并从实现报告和硬件周期计数器输出且仅输出：

```text
resources
power_w
clock_frequency_mhz
performance_tokens_per_second
```

`performance_tokens_per_second` 使用完整任务的硬件周期计数与实际实现频率计算，
不使用软件墙钟时间。

QoR 迭代为两条明确路径：小幅偏差在保留现有实现的前提下走
Stage 5 -> Stage 6 -> Stage 7，修复关键路径或局部硬件实现；明显偏差走
Stage 7 -> Stage 4 -> Stage 5 -> Stage 6 -> Stage 7，由 DSE 增量调整现有设计参数。
时序小幅负裕量是局部优化信号，而不是直接丢弃当前设计的理由。

## Agent 角色

| Agent | 不是做什么 | 真正做什么 |
| --- | --- | --- |
| Specification Agent | summarize 文档 | 把 model/platform/precision constraints 转成 initial SACG |
| Spatial Architect Agent | 随便画架构 | 生成 PU partitioning、schedule、parallelism、pipeline/stream contracts |
| Memory/Runtime Agent | 只是写 host code | 生成 DDR layout、AXI windows、weight packing、runtime buffer map |
| Template Agent | free-form RTL generation | 实例化 verified Chisel templates，并绑定 contract IDs |
| Verification Agent | 只是跑 test | 构造 SACG-derived stage/top/system artifacts 和 verification tasks |
| Evidence Classifier | 读 log 讲故事 | 把 evidence 分类为 contract violation 类型 |
| Repair Agent | 大改代码 | 生成恢复某个 invariant 的 minimal patch |
| Backend Closure Agent | 盲调 Vivado | 区分 RTL、floorplan/routing、TCL、backend option 问题 |
| Benchmark Agent | 打印性能 | 生成可审计 QoR、automation、repair reports |

## 方法的科学性

方法论不是“有很多 agent”。真正的方法是：

- 显式 SACG；
- 可机械检查的 invariants 和 checkers；
- 在 contract/artifact/evidence 上做 state transition；
- 分层验证关联到 contract violation；
- invariant-directed repair；
- 通过 ablation 和 fault injection 证明 contract 有用。
