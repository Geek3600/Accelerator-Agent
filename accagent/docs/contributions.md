# 论文贡献

## 面向 DAC 的贡献层级

### 1. Spatial Accelerator Contract Graph

第一贡献是 SACG：一个用于 LLM spatial accelerator design closure 的可检查、可传播、可修复中间表示。

SACG 定义为：

```text
G = (V, E, C, I, A)
```

其中 node 覆盖 processing unit、pipeline stage、memory task、runtime task、verification/deployment task；edge 覆盖 stream、memory、control、residual、KV 关系；contracts 和 invariants 描述 lowering 过程中必须保持的语义；artifacts 把 Chisel、RTL、trace、DDR image、host code、script、board log 绑定回 graph。

这比 operator graph 或 stream-layout schema 更强，因为它包含 artifact 和 deployment contracts。

### 2. Contract-State Agentic Design Closure

第二贡献是受控 agentic design loop：

```text
S_t = (G_t, A_t, R_t)
S_t -> S_{t+1} = (G_{t+1}, A_{t+1}, R_{t+1})
```

Agent 是 contract transformer 和 repairer。每次 transition 更新 SACG/artifacts/evidence，并通过 lint、trace checking、simulation、regression 或 backend closure 检查。

这把“multi-agent design”重写为 contract-state transition system，而不是 agent orchestration。

### 3. Evidence-Guided Contract Repair

第三贡献是面向 LLM spatial accelerator failure 的 repair methodology：

```text
symptom -> evidence -> violated contract -> patch -> regression result
```

核心 claim：多数 generated hardware artifact 的失败不是 syntax error，而是 shape、numeric policy、stream order、beat count、memory layout、liveness、deployment assumption 等 contract violation。

论文必须用 failure taxonomy、repair logs、ablation 和 fault injection 支撑这一点。

### 4. 多 decoder-only block 的端到端评估

系统应在多类 decoder block 上评估：

- OPT/GPT-2 style：LayerNorm + MHA + GELU/FFN；
- LLaMA style：RMSNorm + RoPE + SwiGLU；
- Qwen style：RMSNorm + RoPE + GQA + SwiGLU。

评估应报告 generated artifacts、stage/top/system verification、repair iterations、checker catch rate、bug escape rate、human intervention 和 QoR。

## 次级支撑贡献

### Chisel-Template-Bound Generation

Chisel 生成重要，但不应作为第一 novelty。它支撑 contract-guided flow，使生成硬件参数化、可检查、可修复。

### Structured Message / State Records

原来的 SDMP 思路应重写为 replayable SACG transition 的 state/message records。这是支撑基础设施，不是最高层贡献。

### Competitive Performance

性能可以用来证明 deployability 和 competitive QoR。但除非对比条件严格公平，否则不要让性能 claim 压过 design closure claim。

## 应避免的 claim

避免声称：

- 第一个 agent 设计芯片；
- 通用任意 RTL 生成；
- 通用 PyTorch-to-FPGA compilation；
- 所有 FPGA LLM inference 的 universal SOTA；
- 直接 Verilog 生成是核心 artifact；
- 贡献只是 prompt engineering。

## DAC 需要的最小证据

每个主贡献都需要定量证据：

- SACG：抓到多少 violations，用了哪些 checkers，bug escape 减少多少。
- Contract-state flow：success rate、repair iterations、human intervention count。
- Evidence-guided repair：localization accuracy、repair success、regression stability。
- End-to-end closure：generated artifacts、verification levels passed、synthesis/implementation results、QoR。
