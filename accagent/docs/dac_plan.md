# DAC Best-Paper 计划

## 暂定标题

```text
SpatialAccAgent: Contract-Guided Agentic Design Closure for LLM Spatial Accelerators
```

## 论文灵魂

```text
LLM spatial accelerator design 的瓶颈不是 RTL generation，而是跨越 model semantics、streaming protocol、numeric policy、memory layout、pipeline timing、verification artifact、deployment interface 的 contract preservation。SpatialAccAgent 把这个隐式、人工维护的跨层约束系统显式化为 Spatial Accelerator Contract Graph，并用 contract-guided agents 完成 design closure。
```

## 故事主线

论文应从 design failure 的本质开始，而不是从 agent 能力开始。

一个 decoder-only Transformer block 会经历多层语义下降：

```text
PyTorch/HuggingFace model
-> operator graph
-> tiled spatial pipeline
-> Chisel/RTL modules
-> stream interconnect
-> AXI/DDR image
-> host runtime
-> simulation/board execution
```

每一层下降都会引入隐式 contract：

- RoPE dimension order；
- GQA query-head 到 KV-head 的映射；
- W4A8 scale layout；
- stream token/head/beat order；
- FIFO 和 backpressure 行为；
- DDR burst packing；
- AXI address window；
- runtime buffer offset；
- verification tolerance 和 oracle。

现有 compiler/ADL 在设计状态已经被形式化之后，自动化 structured transformation。SpatialAccAgent 解决的是更早和更晚的问题：从 heterogeneous model/design documents 到 deployable FPGA artifacts，并通过 contract-preserving synthesis 和 evidence-guided repair 完成 stage/top/system/board 级 design closure。

## 论文结构

### 1. Introduction

核心逻辑：

1. LLM spatial accelerators 很有价值，但设计很难。
2. 现有 compiler/ADL 可以自动化 structured transformation，但真正 design closure 需要维护 cross-layer contracts。
3. LLM agents 能帮忙，但 unconstrained generation 不安全，也难评估。
4. 关键 insight：多数 failure 是 contract violation。
5. SpatialAccAgent 结合 SACG、contract-state transition、hierarchical verification 和 evidence-guided repair。

### 2. Motivation

用两个具体 cross-layer failure 打动审稿人。

Motivation example 1：Qwen-like GQA block。

- 文档写 `num_heads != num_kv_heads`。
- Q/K/V projection shape 看起来正确。
- Stage-level GEMM 也可能通过。
- Top-level attention 失败，因为 KV-cache head mapping 错。
- Free-form agent 可能误修 softmax 或 quantization。
- SACG 能定位到 model-edge contract violation。

Motivation example 2：DDR/system layout。

- Stage-level 和 top-level tests 通过。
- System-level output 错。
- 根因是 packed DDR layout 或 stride 与 RTL address generation 不一致。
- SACG memory contract 能定位 violated memory edge。

### 3. Spatial Accelerator Contract Graph

正式定义：

- `G = (V, E, C, I, A)`；
- contract types；
- invariants；
- checkers；
- artifact binding；
- repair records。

### 4. Contract-Guided Agentic Design Flow

把 agent 表述成 contract-state transformer：

```text
S_t = (G_t, A_t, R_t)
S_t -> S_{t+1} = (G_{t+1}, A_{t+1}, R_{t+1})
```

不要画 agent 聊天图。应该画 state machine：

```text
Spec -> Contract -> Architecture -> Artifacts -> Evidence -> Repair -> Regression -> Deployment
```

### 5. Hierarchical Verification and Evidence-Guided Repair

覆盖：

- stage/top/system/board verification；
- real workload artifact generation；
- failure taxonomy；
- evidence classifier；
- invariant-directed repair；
- regression protocol。

### 6. Implementation

描述：

- SACG schema 和 checker implementation；
- Chisel template library；
- trace dumper；
- DDR image builder；
- verification harness generation；
- Vivado/VCS/Verilator flow；
- agent runtime；
- logging 和 replay format。

### 7. Evaluation

四组实验：

- end-to-end design closure；
- ablation；
- fault injection；
- QoR sanity and competitive performance。

### 8. Related Work

分开讨论：

- ADL/HLS productivity；
- dataflow compilers；
- agentic chip design；
- FPGA LLM accelerators；
- LLM RTL/code-generation agents。

### 9. Conclusion

重新强调 contract-preserving design closure，而不是 generic agent automation。

## 必须有的图和表

### Figure 1: Problem Figure

展示从 model documents 到 board artifacts 的 contract loss：

```text
Model semantics -> Spatial pipeline -> Chisel/RTL -> AXI/DDR -> Verification -> Board
```

标注典型 failure：

- wrong KV mapping；
- stream order mismatch；
- wrong scale stride；
- missing beat；
- deadlock；
- wrong DDR address；
- timing violation。

### Figure 2: SACG

画一个 decoder block graph：

- QKV projection；
- RoPE；
- QK；
- softmax；
- AV；
- MLP；
- residual；
- DDR/runtime tasks。

Edge 上标 model、streaming、numeric、memory、deployment contracts。

### Figure 3: Contract-State Machine

展示：

```text
Spec -> Contract -> Architecture -> Artifacts -> Evidence -> Repair -> Regression -> Deployment
```

每个 transition 由 agent 执行，并由 checker/regression 验证。

### Figure 4: Hierarchical Verification

展示 stage/top/system/board 四层，每层包含：

- input artifacts；
- checker；
- failure class；
- report。

### Table 1: Prior-Work Matrix

比较：

- Allo；
- StreamTensor；
- Design Conductor；
- RTL-generation agents；
- FPGA LLM accelerators；
- SpatialAccAgent。

### Table 2: Failure Taxonomy

列 failure class、symptom、violated contract、repair action。

### Table 3: End-to-End Tasks

列每个 model、precision、platform、generated artifacts、verification level、synthesis/board status。

### Figure 5: Ablation

比较：

- no SACG；
- no stream contract；
- no memory contract；
- single agent；
- full SpatialAccAgent。

指标：

- success rate；
- repair iterations；
- bug escape rate。

### Figure 6: Fault Injection Repair

按 injected bug type 展示 detection、localization、repair success、iterations。

### Table 4: QoR

报告 Fmax、resource、latency、throughput、DDR efficiency、pipeline utilization。

## 最小可行系统

DAC 强论文的 MVP 应闭环一个真实 decoder block，而不是空泛 claim 完整大模型。

必须支持的 model styles：

- GPT-2/OPT style：LayerNorm + MHA + GELU/FFN；
- LLaMA style：RMSNorm + RoPE + SwiGLU；
- Qwen style：RMSNorm + RoPE + GQA + SwiGLU。

必须支持的 precision：

- W8A8 作为稳定 baseline；
- W4A8 作为 numeric-contract stress test，如果时间允许。

必须支持的 verification：

- stage-level；
- top-level；
- system-level DDR/AXI/runtime。

Board-level 是强加分项，但不应成为唯一成败条件。

必须支持的 template library：

- Linear/GEMM；
- RMSNorm/LayerNorm；
- RoPE；
- QK；
- Softmax 或 approximate softmax；
- AV；
- MLP/SwiGLU/GELU；
- residual add；
- FIFO/layout converter；
- AXI/DDR reader 和 writer。

## 最先要做的工具

优先级 1：SACG schema 和 checker。

- `sacc-lint`；
- `stream-trace-check`；
- `beat-count-check`；
- `addr-map-check`；
- `numeric-compare`；
- `deadlock-watchdog`；
- `repair-log-schema`。

优先级 2：real workload artifact builder。

- layer input；
- weight；
- bias；
- scale/zero-point；
- RoPE table；
- attention mask；
- KV cache；
- expected output；
- packed DDR image；
- stage golden traces。

优先级 3：template-bound Chisel generator。

Agent 主要应该做：

- 选择 templates；
- 填 parameters；
- 连接 modules；
- 生成 wrappers；
- 应用小 patch；
- 更新 SACG。

不要把系统评估成 free-form Chisel/Verilog writer。

## 风险与规避

### 风险：被看成 Prompt Engineering

规避：

- 每个 agent output 必须更新 SACG、artifact、checker result 或 repair log；
- 论文展示 contract/state/replayable logs，不展示 prompt。

### 风险：被 Design Conductor 压住 novelty

规避：

- 不 claim 第一个 agent build accelerator；
- claim contract-driven、domain-specific、reproducibly evaluated design closure for LLM spatial accelerators；
- 必须有 ablation 和 failure taxonomy。

### 风险：被 StreamTensor / Allo 认为已经解决

规避：

- 区分 compiler IR/DSE；
- 强调 heterogeneous specs/docs/templates 到 deployable system artifacts；
- 把 StreamTensor/Allo 当 baseline 或 adjacent systems，不要树稻草人。

### 风险：人类干预过多

规避：

- 从第一天记录 human edits；
- 分类 human intervention；
- 诚实报告 automation rate 和 intervention count。

### 风险：性能弱

规避：

- 不 overclaim universal SOTA；
- 目标是合理 pipeline utilization、Fmax、DDR efficiency；
- QoR 是 deployability evidence，design closure productivity 是 primary metric。

## 六个月路线图

### Month 1: Freeze SACG and Templates

交付：

- SACG schema；
- checker v0；
- GPT-2/OPT block contract；
- Linear/Norm/Residual/FIFO/DDR base templates；
- stage-level tests。

### Month 2: First Block Closure

交付：

- OPT/GPT-2 style block；
- real weights/activations；
- stage/top/system pass；
- Chisel/top/wrapper/runtime/testbench/DDR image；
- full design log。

### Month 3: Repair Loop

交付：

- failure taxonomy；
- evidence classifier；
- repair agent；
- initial fault injection；
- 如果可行，至少 30 个 real 或 injected bug records。

### Month 4: Model Generalization

交付：

- LLaMA-like block；
- Qwen-like block；
- RMSNorm/RoPE/GQA/SwiGLU contracts；
- multi-model verification results。

### Month 5: Ablation and QoR

交付：

- single-agent baseline；
- no-contract variants；
- no-stream/no-memory/no-numeric variants；
- free-form RTL baseline，如果可行；
- synthesis 和 implementation reports。

### Month 6: Paper and Artifact

交付：

- DAC paper draft；
- final figures/tables；
- related-work matrix；
- appendix；
- reproducibility package。
