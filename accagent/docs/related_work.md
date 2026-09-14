# 相关工作定位

## 一句话定位

SpatialAccAgent 不直接和 compiler 抢 kernel/dataflow optimization，不和手工 accelerator 抢 peak architecture performance，也不和 broad chip-design agent 抢 “agent 能做芯片” 这个大叙事。它抢的是：

```text
contract-preserving agentic design closure for LLM spatial accelerators
```

## Prior-Work Matrix

| 类别 | 代表工作 | 已解决什么 | SpatialAccAgent 解决什么 |
| --- | --- | --- | --- |
| ADL / HLS productivity | Allo, Spatial, HeteroCL, ScaleHLS | kernel customization、schedule composition、HLS codegen | 从 heterogeneous documents/specs/templates 到 deployable artifacts 的 contract-preserving closure |
| Dataflow compiler | StreamTensor, Stream-HLS | stream layout IR、kernel fusion、FIFO sizing、runtime generation | SACG extraction、artifact binding、hierarchical verification、contract repair |
| Agentic chip design | Design Conductor 2.0 | long-horizon autonomous chip construction case studies | domain-specific contract IR、controlled ablation、failure taxonomy、reproducible benchmark |
| FPGA LLM accelerators | DFX, Hummingbird, FlightLLM 等 | high-performance accelerator architecture | automated design closure and repair methodology |
| LLM RTL/code-generation agents | 通用 HDL generation agents | 从 prompt 生成或编辑代码 | 与 contract/checker 绑定的 bounded template-based Chisel generation |

## Design Conductor 2.0

论文：

- `docs/papers/Team 等 - 2026 - Design Conductor 2.0 An agent builds a TurboQuant inference accelerator in 80 hours.pdf`

威胁：

- long-horizon multi-agent chip design；
- concept-to-layout；
- architecture、implementation、verification、timing optimization、FPGA mapping；
- LLM inference accelerator case study。

启示：

不要 claim “第一个 agent 设计 accelerator” 或 “第一个 concept-to-RTL agent”。

定位差异：

```text
Design Conductor 2.0 demonstrates broad long-horizon agentic chip construction. SpatialAccAgent contributes a domain-specific, contract-driven, reproducibly evaluated methodology for LLM spatial accelerator design closure, with SACG, checkers, ablation, fault injection, and evidence-guided repair.
```

## StreamTensor

论文：

- `docs/papers/Ye和Chen - 2025 - StreamTensor Make Tensors Stream in Dataflow Accelerators for LLMs.pdf`

威胁：

- PyTorch-to-device dataflow compiler；
- itensor stream-layout type system；
- stream-based kernel fusion；
- layout converter generation；
- LP-based FIFO sizing；
- resource allocation；
- HLS/connectivity/runtime generation；
- GPT-2、Qwen、LLaMA、Gemma evaluation。

启示：

不能只把 novelty 写成“自动生成 dataflow accelerator”。

定位差异：

```text
StreamTensor assumes the design state can be represented in compiler/type-system structures for dataflow generation. SpatialAccAgent starts from heterogeneous model/design documents and closes the loop through Chisel artifacts, verification artifacts, memory/runtime contracts, evidence classification, and deployment closure.
```

## Allo 和 ADL/HLS 系统

Allo 以及相关 ADL/HLS 系统，是 algorithm specification 与 hardware customization 分离、schedule composition、accelerator productivity 方面的强 baseline。

启示：

不要把 schedule composition 或 HLS productivity 作为中心 novelty。它们可以作为 baseline 或 adjacent tools。

## FPGA LLM Accelerators

DFX、Hummingbird、FlightLLM 等手工或 compiler-assisted FPGA LLM accelerators 定义了 architecture/performance 背景。

启示：

除非实验充分证明，否则不要 claim 更强 architecture novelty。主 claim 应是 automated design closure and repair methodology。

## 对实验设计的影响

相关工作应支撑以下实验：

- end-to-end artifact generation and verification；
- no-SACG / no-contract ablation；
- fault injection 证明 failure-space coverage；
- 与相关 compiler/GPU/FPGA baseline 做 QoR sanity comparison；
- human-intervention accounting，避免被看成 prompt engineering。
