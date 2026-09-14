# Hardware Operator Template Requirements v0

本文档梳理 SpatialAccAgent 为支持当前目标模型族所需的硬件算子模板。

范围只覆盖当前 `model_config.json` 最小字段已经能表达、且会直接影响硬件结构的内容：

- OPT-125M
- GPT2-small
- TinyLlama / LLaMA-family
- Qwen2
- Gemma3Text

本文档不是模型配置格式说明，也不是硬件实现计划。它的作用是回答：

> 给定这些最小模型配置，SpatialAccAgent 的 trusted Chisel template library 至少需要哪些算子模板，当前 `src/main/scala` 已有模板能覆盖哪些，缺口在哪里？

## 1. 当前硬件模板库存

当前硬件代码位于 `src/main/scala`，顶层流水大致是：

```text
LNAddrGen
-> LayerNormQ
-> QKVLinear
-> Atten(DM1 -> Softmax -> VCache -> DM2)
-> OutLinearFP32
-> ResAddFP32
-> LayerNormQ
-> FFNUp(ReLU fused)
-> FFNDownFP32
-> ResAdd2FP32
```

这是一条 OPT-style pre-LayerNorm decoder block 的空间流水线。

### 1.1 已有可复用模板

| 当前模块 | 当前语义 | 可复用性 |
|---|---|---|
| `LayerNormQ` | FP32 input, gamma/beta LayerNorm, INT8 output | 可覆盖 OPT/GPT2 LayerNorm；不能覆盖 RMSNorm |
| `QKVLinear` | fixed `hidden=768`, `q_heads=kv_heads=12`, `head_dim=64`, output Q/K/V stream | 可覆盖 OPT/GPT2 MHA 形态；不能覆盖 GQA/MQA |
| `Atten` / `DM1FP32` / `SoftmaxPipFP32` / `VCache` / `DM2Quant` | MHA attention datapath, QK softmax PV, fixed short-seq parameters | 算术核心可复用；head mapping、RoPE、GQA/MQA、mask 需要新模板化 |
| `OutLinearFP32` | attention output projection `H -> H`, FP32 output, bias add | MAC/weight path 可复用；需要参数化 hidden/head/bias |
| `ResAddFP32`, `ResAdd2FP32` | FP32 vector residual add | 基本可复用；需要和 block wiring 模板绑定 |
| `FFNUp` | dense up projection, bias, ReLU fused, INT8 output | 可覆盖 OPT ReLU FFN；不能覆盖 GPT2 GELU 或 gated MLP |
| `FFNDownFP32` | dense down projection, bias, FP32 output | MAC core 可复用；需要参数化和 bias optional |
| `QuantCommon` | FP32/int8 primitive, scale/bias/quant helper | 可作为各模板基础 primitive |

### 1.2 当前模板硬编码假设

这些假设不能隐藏在代码里，后续必须进入 template spec 和 SACG：

| 维度 | 当前假设 |
|---|---|
| hidden size | 768 |
| attention kind | MHA, `num_q_heads == num_kv_heads` |
| heads | 12 |
| head dim | 64 |
| QKV output dim | `3 * hidden_size = 2304` |
| max/tile seq len | 16 |
| norm | LayerNorm with gamma/beta |
| MLP | dense `H -> 4H -> H`, ReLU |
| bias | QKV/out/FFN bias generally assumed present |
| position encoding | no hardware RoPE module; learned absolute position is outside current block |

## 2. Model-Family Template Requirements

### 2.1 OPT-125M

Minimal config:

```text
model_type = opt
hidden_size = 768
num_layers = 12
attention = MHA, q_heads=12, kv_heads=12, head_dim=64
position_encoding = learned_absolute
norm = LayerNorm, eps=1e-5, bias=true
mlp = dense, intermediate=3072, activation=relu
weight_layout.qkv = separate_q_k_v
```

Required templates:

| Model op | Required template | Current status |
|---|---|---|
| LayerNorm | `LayerNormQ` | existing |
| Q/K/V projection | MHA QKV linear `H -> 3H` | existing for OPT dimensions |
| Attention score | QK dot product per head | existing core |
| Softmax | causal softmax over seq | existing core |
| Attention value | softmax-V matmul | existing core |
| Output projection | dense `H -> H` | existing for OPT dimensions |
| Residual add | FP32 vector add | existing |
| MLP up | dense `H -> 4H` + ReLU | existing |
| MLP down | dense `4H -> H` | existing |

OPT 是当前硬件代码最接近的目标。后续 agent 复现当前设计过程时，OPT path 应作为 baseline template binding。

### 2.2 GPT2-small

Minimal config:

```text
model_type = gpt2
hidden_size = 768
num_layers = 12
attention = MHA, q_heads=12, kv_heads=12, head_dim=64
position_encoding = learned_absolute
norm = LayerNorm, eps=1e-5, bias=true
mlp = dense, intermediate=3072, activation=gelu_new
weight_layout.qkv = fused_qkv
```

Required templates:

| Model op | Required template | Current status |
|---|---|---|
| LayerNorm | `LayerNormQ` | existing |
| Q/K/V projection | MHA QKV linear with fused GPT2 `c_attn` layout adapter | needs weight-layout adapter |
| Attention | same MHA attention core as OPT | mostly reusable |
| Output projection | dense `H -> H` | reusable after layout binding |
| MLP up | dense `H -> 4H` without ReLU fusion | needs activation-separated FFN up |
| Activation | `gelu_new` / GELU approximation | missing |
| MLP down | dense `4H -> H` | reusable after parameter/bias binding |
| Residual add | FP32 vector add | existing |

GPT2 不需要 RMSNorm、RoPE、GQA/MQA。它主要暴露两个模板缺口：

1. QKV weight layout: HuggingFace GPT2 uses fused `c_attn`.
2. MLP activation: `gelu_new` cannot be represented by current ReLU-fused `FFNUp`.

### 2.3 TinyLlama / LLaMA-family

Minimal TinyLlama config:

```text
model_type = llama
hidden_size = 2048
num_layers = 22
attention = GQA, q_heads=32, kv_heads=4, head_dim=64
position_encoding = RoPE, rope_theta=10000
norm = RMSNorm, eps=1e-5, bias=false
mlp = gated, intermediate=5632, activation=silu
weight_layout.qkv = separate_q_k_v
weight_layout.mlp = gate_up_down
```

Required templates:

| Model op | Required template | Current status |
|---|---|---|
| RMSNorm | `RMSNormQ` or RMSNorm + quant epilogue | missing |
| Q projection | linear `H -> q_heads * head_dim` | current QKVLinear must be generalized |
| K/V projection | linear `H -> kv_heads * head_dim` | current QKVLinear assumes `kv_heads=q_heads` |
| RoPE | apply RoPE to Q/K streams | missing |
| GQA head mapping | map each Q head to shared KV head | missing |
| Attention | QK/softmax/PV with GQA | current arithmetic reusable, control missing |
| Output projection | dense `H -> H`, bias optional false | reusable after parameter/bias binding |
| Gated MLP | `gate_proj`, `up_proj`, `silu(gate) * up`, `down_proj` | missing |
| Residual add | FP32 vector add | existing |

LLaMA-family 的关键不是单个新算子，而是 block pattern 改变：

```text
rms_norm_1
-> self_attention(Q/K/V + RoPE + GQA)
-> residual_add_1
-> rms_norm_2
-> gate_proj + up_proj + silu(gate) * up
-> down_proj
-> residual_add_2
```

### 2.4 Qwen2

Minimal Qwen2-0.5B config:

```text
model_type = qwen2
hidden_size = 896
num_layers = 24
attention = GQA, q_heads=14, kv_heads=2, head_dim=64
position_encoding = RoPE, rope_theta=1000000
norm = RMSNorm, eps=1e-6, bias=false
mlp = gated, intermediate=4864, activation=silu
qkv_bias = true
out_bias = false
```

Required templates are mostly the same as LLaMA, with these parameter differences:

| Requirement | Qwen2-specific point |
|---|---|
| RMSNorm | eps is `1e-6` |
| RoPE | theta is `1000000` |
| GQA | q/kv head ratio is `14 / 2 = 7` |
| QKV projection | q/k/v bias is present |
| Out projection | output bias is absent |
| MLP | gated SiLU, no up/down bias |

Qwen2 therefore requires the same template family as LLaMA, but template specs must support:

- non-power-of-two q head count (`14`);
- q/kv ratio that is not 2/4/8 only;
- QKV bias true while output projection bias false.

### 2.5 Gemma3Text

Minimal Gemma3Text config:

```text
model_type = gemma3_text
hidden_size = 1152
num_layers = 26
attention = MQA, q_heads=4, kv_heads=1, head_dim=256
position_encoding = RoPE, rope_theta=1000000, rope_local_base_freq=10000
qk_norm = true
sliding_window = 512
sliding_window_pattern = 6
norm = RMSNorm, eps=1e-6, bias=false
mlp = gated, intermediate=6912, activation=gelu_pytorch_tanh
```

Required templates:

| Model op | Required template | Current status |
|---|---|---|
| Input RMSNorm | RMSNorm | missing |
| Q/K/V projection | MQA-capable projection | missing |
| Q/K norm | per-head Q/K RMSNorm before attention | missing |
| RoPE | global/local RoPE parameter support | missing |
| Sliding attention mask | local/global mask generator | missing |
| MQA attention | Q heads share one KV head | missing control/template |
| Post-attention RMSNorm | RMSNorm after attention output, before residual | missing wiring pattern |
| Pre-FFN RMSNorm | RMSNorm before gated MLP | missing |
| Gated MLP | gated GELU tanh activation | missing |
| Post-FFN RMSNorm | RMSNorm after MLP, before residual | missing wiring pattern |
| Residual add | FP32 vector add | existing core |

Gemma3Text is the largest template gap. It should not be treated as only "LLaMA with different dimensions" because it adds:

- MQA;
- q/k norm;
- extra post-attention and post-FFN RMSNorms;
- sliding-window/local-global attention behavior;
- gated GELU tanh activation.

## 3. Minimal Common Template Library

To support the five model families above, the smallest useful template library should contain the following template classes.

### 3.1 Normalization Templates

| Template | Required by | Parameters |
|---|---|---|
| `LayerNormQ` | OPT, GPT2 | hidden_size, lanes, eps, has_beta, output quant policy |
| `RMSNormQ` | LLaMA, Qwen2, Gemma3Text | hidden_size, lanes, eps, has_beta=false, output quant policy |
| `QKNorm` | Gemma3Text | head_dim, q_heads, kv_heads, eps, placement before RoPE/attention |

Current code only has LayerNorm semantics. RMSNorm must not be approximated by LayerNorm because RMSNorm has no mean subtraction and no beta in the standard target models.

### 3.2 Linear Projection Templates

| Template | Required by | Parameters |
|---|---|---|
| `ParametricLinearInt8ToInt8` | QKV, FFN up/gate, some quantized intermediates | in_dim, out_dim, row_parallel, col_parallel, bias, scale policy, weight layout |
| `ParametricLinearInt8ToFP32` | out projection, FFN down | in_dim, out_dim, row_parallel, col_parallel, bias, output scale policy |
| `QKVProjector` | all models | q_dim, kv_dim, q_heads, kv_heads, head_dim, qkv_bias, qkv layout, stream order |

`QKVProjector` is not just a linear layer. Its template spec must define output stream order, head order, token order, beat count, and downstream attention mapping.

### 3.3 Attention Templates

| Template | Required by | Parameters |
|---|---|---|
| `RoPEApply` | LLaMA, Qwen2, Gemma3Text | head_dim, theta, optional local theta, position index, stream order |
| `AttentionMHA` | OPT, GPT2 | q_heads=kv_heads, head_dim, seq/tile, causal mask |
| `AttentionGQA` | LLaMA, Qwen2 | q_heads, kv_heads, q_to_kv mapping, head_dim, seq/tile, causal mask |
| `AttentionMQA` | Gemma3Text | q_heads, kv_heads=1, head_dim, seq/tile, mask mode |
| `AttentionMask` | all causal models; Gemma needs sliding mode | causal, sliding_window, local/global pattern |
| `KVCache` | attention with history | kv_heads, head_dim, seq capacity, layout, bank policy |

The existing `DM1FP32`, `SoftmaxPipFP32`, `VCache`, and `DM2Quant` can remain arithmetic subtemplates, but the agent needs a higher-level attention template that binds them to model-level head semantics.

### 3.4 Activation and MLP Templates

| Template | Required by | Parameters |
|---|---|---|
| `ActivationReLU` | OPT | data width, quant policy |
| `ActivationGELUNew` | GPT2 | approximation policy, latency |
| `ActivationSiLU` | LLaMA, Qwen2 | sigmoid/exp approximation policy, latency |
| `ActivationGELUTanh` | Gemma3Text | tanh approximation policy, latency |
| `DenseMLP` | OPT, GPT2 | hidden_size, intermediate_size, activation, bias |
| `GatedMLP` | LLaMA, Qwen2, Gemma3Text | hidden_size, intermediate_size, gate/up/down layout, activation, bias |
| `ElementwiseMul` | gated MLP | vector width, stream alignment, latency |

Current `FFNUp` fuses ReLU into the up projection. For template reuse, the next abstraction should separate:

```text
linear up/gate projection
-> activation
-> optional elementwise multiply
-> linear down projection
```

### 3.5 Block Wiring Templates

Different model families do not only select different kernels; they place norms and residuals differently.

| Template | Required by | Pattern |
|---|---|---|
| `OPTPreLNBlock` | OPT | LN -> Attn -> Add -> LN -> DenseMLP -> Add |
| `GPT2PreLNBlock` | GPT2 | LN -> Attn -> Add -> LN -> DenseGELUMLP -> Add |
| `LlamaStyleBlock` | LLaMA, Qwen2 | RMS -> Attn -> Add -> RMS -> GatedMLP -> Add |
| `Gemma3TextBlock` | Gemma3Text | RMS -> Attn -> post-attn RMS -> Add -> pre-FFN RMS -> GatedMLP -> post-FFN RMS -> Add |

This block wiring must be explicit in SACG. If it is implicit in top-level glue code, the agent cannot reliably detect cross-layer consistency bugs.

## 4. Template Coverage Matrix

| Capability | OPT | GPT2 | TinyLlama/LLaMA | Qwen2 | Gemma3Text | Current code |
|---|---:|---:|---:|---:|---:|---|
| LayerNorm | yes | yes | no | no | no | yes |
| RMSNorm | no | no | yes | yes | yes | missing |
| Learned absolute position | yes | yes | no | no | no | outside current block |
| RoPE | no | no | yes | yes | yes | missing |
| MHA | yes | yes | no | no | no | yes, fixed |
| GQA | no | no | yes | yes | no | missing |
| MQA | no | no | no | no | yes | missing |
| Q/K norm | no | no | no | no | yes | missing |
| Dense ReLU MLP | yes | no | no | no | no | yes |
| Dense GELU MLP | no | yes | no | no | no | missing |
| Gated SiLU MLP | no | no | yes | yes | no | missing |
| Gated GELU tanh MLP | no | no | no | no | yes | missing |
| Bias optional per projection | partial | yes | yes | yes | yes | partial |
| Sliding attention mask | no | no | no | no | yes | missing |
| FP32 residual add | yes | yes | yes | yes | yes | yes |

## 5. Minimal Development Priority

The template library should grow in this order:

1. **Template spec for current OPT path.**
   - Document current `LayerNormQ`, `QKVLinear`, `Atten`, `OutLinearFP32`, `ResAdd`, `FFNUp`, `FFNDown`, `ResAdd2`.
   - Bind exact current dimensions and stream rules.
   - This supports reproducing the existing accelerator from `docs/context_2026-03-27.md`.

2. **Parameter binding layer.**
   - Convert `model_config.json` fields into template parameters.
   - First check whether a config is covered by existing templates before generating code.

3. **GPT2 delta templates.**
   - Fused QKV layout adapter.
   - Dense GELU/GELU_NEW activation template.
   - This is the smallest non-OPT extension.

4. **LLaMA/Qwen common templates.**
   - RMSNorm.
   - RoPE.
   - GQA attention control and KV head mapping.
   - Gated SiLU MLP.
   - Bias optional support.

5. **Gemma3Text-specific templates.**
   - Q/K norm.
   - MQA.
   - extra RMSNorm wiring.
   - sliding-window/local-global mask.
   - gated GELU tanh activation.

## 6. Required SACG Bindings

Each selected template must create or update SACG nodes and constraints. At minimum:

| Template area | SACG constraints |
|---|---|
| Normalization | hidden_size, eps, gamma/beta presence, output numeric policy |
| QKV projection | q_dim, k_dim, v_dim, q_heads, kv_heads, bias, weight layout, stream order |
| RoPE | head_dim, theta, position index, Q/K stream alignment |
| Attention | q_to_kv mapping, score shape, mask shape, beat count, liveness |
| KV cache | kv_heads, head_dim, seq capacity, memory layout, runtime map |
| MLP | dense vs gated, activation, intermediate_size, bias, stream alignment |
| Residual | matching address/order/latency between residual input and computed branch |
| Block wiring | operator_sequence, stage order, valid/ready alignment |

This is why SACG is central to the framework: template selection is not a local lookup. A template binding must preserve cross-layer consistency across model config, Chisel parameters, stream traces, DDR/runtime layout, checkers, and repair decisions.

## 7. Immediate Output for the Agent Framework

For the current framework, the next concrete artifact should be a template coverage report generated from a model config:

```json
{
  "model_config": "accagent/runs/model_configs/qwen2_0_5b/model_config.json",
  "covered_templates": [
    "residual_add",
    "linear_mac_core"
  ],
  "missing_templates": [
    "rms_norm",
    "rope_apply",
    "gqa_attention",
    "gated_silu_mlp"
  ],
  "requires_human_approval": [
    "new_attention_template",
    "new_mlp_template"
  ]
}
```

This coverage report is the first minimal implementation target for template selection. It should not attempt to generate unsupported hardware. It should explicitly say which model ops are covered, which are not, and which missing templates block full accelerator generation.
