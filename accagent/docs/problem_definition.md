# 问题定义

## 一句话问题

给定异构的模型/设计文档、量化规范、Chisel 模板、FPGA/DDR/AXI 约束、性能目标和分层验证证据，如何让 agentic system 保持跨层 contract，并为 decoder-only Transformer spatial accelerator 完成从 specification 到可部署 FPGA artifact 的 design closure？

## 研究范围

SpatialAccAgent 解决的是 **contract-preserving spatial accelerator design closure**，不是通用 HDL 生成。

目标 workload 是 decoder-only Transformer LLM block，例如 OPT、LLaMA、Qwen。当前 OPT accelerator 是第一个完整 case study 和 empirical trace；LLaMA/Qwen 后续应作为泛化实验，用来证明方法不是围绕 OPT 手工特化的一套脚本。

期望输出是一套完整 accelerator design package：

- processing-unit pipeline；
- Chisel source，作为主要生成和维护的硬件 artifact；
- top-level Chisel connection；
- 由 Chisel 后端生成的 Verilog/SystemVerilog，或用于 system/board integration 的辅助 wrapper；
- DDR/AXI wrapper contract；
- verification scripts 和真实 workload cases；
- deployment / benchmark scripts；
- design decision、failure、repair、regression 的 evidence records。

核心中间对象是 **Spatial Accelerator Contract Graph (SACG)**。它把 model semantics、streaming protocol、numeric policy、memory layout、pipeline timing、verification artifacts 和 deployment interfaces 绑定到同一个可检查的 graph 中。

## 非目标

SpatialAccAgent 不是通用 Verilog chatbot，不能声称从自然语言生成任意电路。

SpatialAccAgent 也不是 PyTorch-to-HLS compiler 的替代品。compiler system 和 EDA tool 应被视为子模块或 baseline。我们的研究问题比 compiler IR transformation 更早开始，也更晚结束：从 heterogeneous model/design documents 到 deployable FPGA artifacts，并在整个过程中保持 contract、利用 evidence 修复。

SpatialAccAgent 不需要在所有部署场景中证明与原始 floating-point 模型 bit-exact。正确性应由目标硬件任务的 oracle 和 acceptance criteria 定义。

## 成功标准

一次 SpatialAccAgent run 成功，意味着它生成的 accelerator 满足：

- 有显式 SACG，并包含可检查的 contracts 和 invariants；
- 保持 spatial pipeline semantics，不退化成完全顺序的软件式执行；
- 能运行真实 weights、activations、quantization parameters 和真实 memory/interface 数据；
- 在定义好的 oracle 下通过 stage-level、top-level、system-level、board-level 验证；
- 根据目标硬件任务标准产生正确或可接受的输出；
- 可综合、可实现、可上板或可部署到目标系统；
- 报告 latency、throughput、energy/power、resource、clock、design time、automation rate、repair iterations、contract violations caught、bug escape rate 和 comparison metadata。

## 性能 claim 边界

SOTA 可以作为主 claim，但必须限定在清楚的 comparison envelope 内：

- model family 和 model size；
- sequence length 和 batch；
- precision / quantization；
- FPGA 或 GPU 平台；
- board/runtime 假设；
- latency、throughput、energy、resource、design-time 等指标。

论文应避免泛泛 claim “所有 FPGA LLM inference 绝对 SOTA”。更稳妥的 claim 是：SpatialAccAgent 在被评估的 model-hardware setting 下达到 SOTA 或 competitive performance，同时显著自动化了原本依赖专家的 spatial accelerator design closure。

## 科学定位

这个项目应被写成科学研究，而不是一次工程交付。长期上下文文档提供了 empirical evidence，说明复杂 spatial accelerator design loop 可以被分解、记录、回放，并逐步 agent 化。论文需要把这个过程抽象成 SACG、contract-state transition、checker、failure taxonomy、repair science、ablation 和 QoR experiment。
