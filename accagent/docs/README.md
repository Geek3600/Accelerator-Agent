# AccAgent 研究工作区

这个目录用于存放 SpatialAccAgent / AccAgent 课题相关的研究材料，包括论文想法、方法抽象、contract 定义、协议草案、相关工作笔记、实验计划，以及从长期上下文文档中提炼出的证据。

长期上下文文档仍然是 empirical trace：

- `docs/context_2026-03-27.md`

`accagent/` 中的文件不应该复刻所有项目工程细节，而应该把这些细节抽象成一套可写成 DAC 论文的方法论。

## 当前核心定位

暂定论文标题：

```text
SpatialAccAgent: Contract-Guided Agentic Design Closure for LLM Spatial Accelerators
```

DAC 级核心命题：

```text
LLM spatial accelerator design 的真正瓶颈不是 RTL 生成，而是跨越 model semantics、streaming protocol、numeric policy、memory layout、pipeline timing、verification artifact、deployment interface 的 contract preservation。SpatialAccAgent 的贡献是把这个隐式、人工维护的跨层约束系统显式化为 Spatial Accelerator Contract Graph，并用 contract-guided agents 完成 design closure。
```

目标对象是 decoder-only Transformer block 的 spatial accelerator design closure，不是任意 Verilog 生成，不是任意 PyTorch 编译，也不只是追求峰值性能的 accelerator architecture。

最终输出应是一套完整 accelerator design package，包括 Chisel 源码、top-level 连接、DDR/AXI wrapper contract、验证脚本、真实 workload artifact、部署脚本、repair log 和可复现实验证据。

## 文件说明

- `problem_definition.md`：问题定义、范围边界、目标、非目标、成功标准。
- `sacg.md`：Spatial Accelerator Contract Graph (SACG)、invariant、checker、repair record。
- `sacg_schema_v0.md`：第一版可落地 SACG YAML/JSON schema，包括 node、edge、contract、artifact、invariant、checker report、repair record。
- `checker_spec_v0.md`：第一版 checker suite 规格，包括 `sacc-lint`、`stream-trace-check`、`beat-count-check`、`addr-map-check`、`numeric-compare`、`deadlock-watchdog`、`repair-log-check`。
- `failure_taxonomy.md`：failure class、violated contract、checker、repair action、fault injection 设计。
- `methodology.md`：contract-state design flow 和 contract-guided agent 角色。
- `message_protocol.md`：结构化 state/message record，用于让 agent transition 可复现。
- `contributions.md`：面向 DAC 的贡献层级。
- `evaluation_plan.md`：end-to-end、ablation、fault injection、QoR 四组实验。
- `dac_plan.md`：论文故事线、关键图表、风险、MVP 和 6 个月路线图。
- `related_work.md`：Design Conductor 2.0、StreamTensor、Allo 等相关工作定位。
- `evidence_index.md`：长期上下文文档中可以支撑论文 claim 的证据索引。

## 工作规则

新的课题决策优先更新 `accagent/` 中的对应文件。如果该决策对会话恢复很重要，再向 `docs/context_2026-03-27.md` 追加一个短恢复指针。
