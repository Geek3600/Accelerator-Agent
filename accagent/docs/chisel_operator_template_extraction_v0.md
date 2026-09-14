# Chisel Operator Template Extraction v0

本文记录当前从 `/src` 抽象出的 Chisel operator template 边界。目标不是复制现有 OPT 工程代码，而是把已经验证过的工程结构提炼成可由 SACG 绑定和检查的 trusted template library。

## 当前文件

```text
accagent/framework/templates/chisel/Common.scala
accagent/framework/templates/chisel/Norm.scala
accagent/framework/templates/chisel/Linear.scala
accagent/framework/templates/chisel/QKVProjection.scala
accagent/framework/templates/chisel/Attention.scala
accagent/framework/templates/chisel/Softmax.scala
accagent/framework/templates/chisel/Mask.scala
accagent/framework/templates/chisel/KVCache.scala
accagent/framework/templates/chisel/RoPE.scala
accagent/framework/templates/chisel/Activation.scala
accagent/framework/templates/chisel/Elementwise.scala
accagent/framework/templates/chisel/Residual.scala
accagent/framework/templates/chisel/FFN.scala
accagent/framework/templates/chisel/DecoderBlock.scala
```

## 抽象原则

- 文件名使用通用算子名，不使用 OPT 工程名或 `*Template.scala` 命名。
- 保留 `valid/ready/st/addr/last` stream 约束，因为这些是后续 beat-count、stream-order、liveness checker 的核心。
- 把 hidden size、head 数、head dim、lane 数、seq len、bias presence、activation 等从硬编码常量改为参数。
- 删除 board/runtime/debug/Vivado 特定 glue。
- 不复制当前双缓冲、URAM bank、timing workaround 等工程优化；这些后续应作为 backend/platform template 或参数化 memory template 处理。
- 当前算术可先用结构占位，但必须在文档中明确标注，不能让 agent 把占位实现当作数值正确模板。

## Softmax 边界

现有 `/src/main/scala/Attention.scala` 中的 `Atten` 不是单个普通算子，而是：

```text
DM1(QK score) -> SoftmaxPipFP32 -> VCache -> DM2(PV context)
```

因此模板层不能继续把 softmax 隐藏在 `Attention.scala` 内部。当前处理是：

- `Attention.scala` 保留抽象 attention shell，维持 QKV/V stream contract；
- `Softmax.scala` 独立为 row-level softmax 模板；
- 后续可继续拆分为 `AttentionScore`、`Softmax`、`AttentionValue` 或 `KVCache` 等模板。

当前 `Softmax.scala` 的实现是最小结构模板：

- collect 一整行 score；
- 根据 `cfg.seqlen`、`rowIndex`、`mask`、`causal`、`slidingWindow` 生成 keep 条件；
- emit 与输入一致的 beat/st/addr/last 结构；
- arithmetic core 暂时是 masked max-onehot 近似，不是最终 softmax。

这个边界使 SACG 能显式记录：

```text
score shape
mask shape
row index
causal/sliding-window constraint
softmax input/output beat count
stream order
```

后续将数值核心替换为 exp/sum/normalize 时，不应改变这些外部约束。

## 缺失算子模板补齐

根据 `hardware_operator_template_requirements_v0.md` 中的缺口，本轮已补齐以下最小 Chisel 模板：

```text
RMSNorm / RMSNormQ
QKNorm
ParametricLinearInt8ToInt8
ParametricLinearInt8ToFP32
QKVProjector
RoPE / RoPEApply
AttentionMHA
AttentionGQA
AttentionMQA
AttentionMask
KVCache
ActivationReLU
ActivationGELUNew
ActivationSiLU
ActivationGELUTanh
DenseMLP
GatedMLP
ElementwiseMul
OPTPreLNBlock
GPT2PreLNBlock
LlamaStyleBlock
Gemma3TextBlock
```

这些模板当前优先稳定接口、stream shape、operator placement 和 SACG binding 边界。除 `Linear`、`ResidualAdd` 这类简单算子外，多数新增模板的数值核心仍是最小占位实现，不应作为最终模型精度实现。

## 当前限制

- 模板已通过本地直接 `scalac` 类型检查：

```text
scala 2.13.16
chisel 7.0.0
chisel-plugin 7.0.0
source root: accagent/framework/templates/chisel
```

- 模板尚未通过 sbt/elaboration/FIRRTL 生成验证；当前环境中 sbt 启动被只读 home 和 Unix domain socket 权限阻塞。
- `Attention.scala` 仍不是完整 QK-softmax-PV 实现。
- `Softmax.scala` 当前不是数值正确 softmax。
- `RMSNorm`、`QKNorm`、`RoPE`、GELU/SiLU/GELU-tanh activation 当前是结构模板或低成本近似。
- `DecoderBlock.scala` 仍是 wiring sketch，权重/scale/mask 端口后续需要由 generator lift 到 wrapper。
