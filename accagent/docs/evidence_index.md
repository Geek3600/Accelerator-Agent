# 证据索引

本文档把 SpatialAccAgent 论文故事中的 claim 映射到长期上下文文档中的证据。长期上下文文档是 evidence source，不是论文方法本身。

主要来源：

- `docs/context_2026-03-27.md`

## 最新研究抽象

相关章节：

- `19. 2026-06-21 研究定位更新：Spatial Accelerator 设计 Agent`
- `20. 2026-06-21 从长期上下文记录中抽象出的 SpatialAgent 自动化框架`
- `21. 2026-06-21 课题问题定义与 SpatialAgent 方法论边界更新`
- `21.13 DAC best-paper 目标下的 SpatialAccAgent 重新定位`

可支撑的 evidence：

- 项目应被 framing 为 spatial accelerator design automation；
- 方法不应被 framing 为 generic Verilog generation；
- OPT 是第一个完整 case，LLaMA/Qwen 用于后续泛化；
- Chisel 是 primary generation target；
- 最新 DAC 主线应聚焦 contract-preserving design closure；
- SACG、contract-state transition、evidence-guided repair 是主方法 claim；
- multi-agent flow 和 structured messages 是支撑机制，不是最高层 novelty；
- real data artifact 属于 hierarchical verification 内部，而不是独立主阶段。

## Stage-Level Real-Workload Verification

相关章节：

- `14. 2026-03-28 后续验证进展（fc2 修复通过）`
- `14.10 2026-03-28 晚些时候新增进展（fc1 / FFNUp 修复通过）`
- `15. 2026-03-28 继续推进进展（QKVLinear 已通过）`
- `16. 2026-03-28 继续推进进展（DM1FP32 已补执行层并通过）`
- `17. 2026-03-28 继续推进进展（SoftmaxPipFP32 已通过）`
- `18. 2026-03-28 继续推进进展（DM2Quant 已通过）`
- `19. 2026-03-28 继续推进进展（OutLinearFP32 已通过）`

可支撑的 evidence：

- stage-level verification 使用真实 weights、activations、quantization parameters、golden outputs；
- complex LLM block 可以先 stage by stage 验证，再进入 top/system closure；
- repair 由 first-failure evidence 驱动，而不是随机试错；
- 验证必须考虑 hardware timing、valid/data/address alignment、quantization semantics。

典型 failure/repair evidence：

- `FFNDown`：12-cycle input cadence 下 `psum_last` 必须用 `data_in_valid` gating。
- `FFNUp`：runtime semantics 和 verification data mapping 必须一起对齐。
- `QKVLinear`：Q/K/V 需要独立 scale/bias 处理，并修复 multi-token collection。
- `Softmax`：valid/data/address alignment 和 numerical approximation path 都影响正确性。
- `DM2`：ctx/value read-side pairing 必须正确连接。
- `OutLinear`：input cadence 和 StoreUnit address semantics 必须一致。

这些证据后续应被重写为 SACG contract violation，而不是只作为工程 bug list。

## System Wrapper 和 DDR/AXI Evidence

相关章节：

- `20. 2026-03-28 新增：SystemTop / DDR 模式整链路验证起步`
- `21. 2026-03-28 新增：板级规划、912 场景判断与后续验证决策`
- `42. 2026-03-31 新增：转入“本地 Chisel，远端 Verilator”的 full-seq system 方案`

可支撑的 evidence：

- accelerator package 不只是 core RTL；
- compute core、system wrapper、DDR/MIG-like interface、board wrapper、runtime、verification scripts 必须分层；
- long-sequence setting 迫使 system-level 和 dataflow-level reasoning；
- local Chisel generation 和 remote simulation/synthesis flow 是 reproducible deployment closure 的一部分。

## Hierarchical Validation Evidence

上下文中的 evidence 类别：

- stage-level module verification；
- top-level integration；
- system-level DDR-backed wrapper validation；
- remote VCS/Verilator validation；
- board/runtime deployment。

论文使用方式：

这些证据支撑一个核心观点：可信的 spatial accelerator agent 必须生成并验证完整 design package，而不是孤立 Chisel/Verilog snippet。在最新 DAC framing 中，每个验证层级都应被解释为检查 SACG contracts 的不同子集。

## Failure Taxonomy

相关章节：

- `20.6 从上下文记录中可以提炼的典型 failure taxonomy`

候选 failure classes：

- memory occupancy / bank state；
- ready/valid deadlock；
- first-beat loss；
- output address mismatch；
- quantization semantic mismatch；
- multi-token collection bug；
- attention pairing bug；
- harness / protocol bug；
- system wrapper bug；
- board runtime issue。

论文使用方式：

该 taxonomy 可以支撑 Evidence-Guided Contract Repair。每个 failure 应尽可能重写为 violated contract 或 violated invariant，并在 fault injection / repair evaluation 中量化 detection、localization、repair success。

## Deployment and Board-Level Evidence

相关 evidence 类别：

- remote VCS/Verilator scripts；
- synthesis/P&R runs；
- board wrapper 和 runtime package；
- single-card / multi-card smoke 或 demo flow；
- status 和 deployment packaging。

论文抽象方式：

这些应被描述为 deployment portability、board-level closure、runtime integration evidence。具体服务器名、卡数、package 名、UI status file 不应作为方法贡献。

## Evidence-to-Paper Translation Rule

上下文细节应这样翻译：

- specific remote nodes -> deployment portability and clean toolchain management；
- specific full-sequence cases -> hierarchical real-workload verification over SACG contracts；
- specific bug fixes -> evidence-guided contract repair loop；
- specific board demos -> deployment-contract closure；
- specific scripts -> reproducible accelerator design package；
- specific Chisel files -> template-bound Chisel construction evidence；
- specific traces/logs -> evidence records linked to SACG nodes and edges。

不要把每个工程步骤直接搬进论文。论文需要 abstraction、baselines、metrics、ablations。

## DAC Update

最新目标是 DAC best-paper level positioning：

```text
SpatialAccAgent: Contract-Guided Agentic Design Closure for LLM Spatial Accelerators
```

当前最高优先级研究 artifact：

- `accagent/sacg.md`：SACG definition、contracts、invariants、checkers；
- `accagent/methodology.md`：contract-state transition flow；
- `accagent/evaluation_plan.md`：end-to-end、ablation、fault-injection、QoR plan；
- `accagent/dac_plan.md`：paper structure、figures/tables、risks、roadmap。
