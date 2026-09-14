# SpatialAccAgent Model Input Spec v0

> Superseded note, 2026-06-24:
>
> 本文是早期“模型输入与当前模板兼容性”讨论记录，不再作为当前 `model_config.json` 的有效 schema。
> 当前有效规格已经收窄为硬件生成最小字段，见：
>
> ```text
> accagent/docs/hf_model_config_extraction_spec_v0.md
> ```
>
> 后续不要把本文中的 tokenizer、generation、完整 source/provenance、diagnostics、template compatibility / `needs_new_template` 等内容放入主 `model_config.json`。

## 0. 目的

本文档只回答一个问题：

```text
基于当前 src/ 目录中的硬件模板，SpatialAccAgent 为了确定加速器架构，
最少需要模型输入提供哪些信息，格式应该是什么？
```

这里的“模型输入”不是完整 checkpoint，也不是权重文件本身，而是：

> 能让 agent 判断目标模型能否绑定到当前硬件模板，并为模板参数生成提供依据的模型结构描述。

当前阶段先不要把 remote VCS、DDR image、board runtime、Vivado 等内容放进模型输入。那些属于后续验证/部署输入。

---

## 1. 当前硬件模板实际支持什么

阅读 `/home/remote/workspace/Qwen2-Accelerator/src/main/scala` 后，当前活跃硬件模板更接近一个 **OPT-style pre-LN decoder block**，主流水在 `Top.scala` 中固定为：

```text
LNAddrGen
-> LayerNormQ
-> QKVLinear
-> Atten
   -> DM1FP32
   -> SoftmaxPipFP32
   -> VCache
   -> DM2Quant
-> OutLinearFP32
-> ResAddFP32
-> LayerNormQ
-> FFNUp
-> FFNDownFP32
-> ResAdd2FP32
```

从模板代码看，当前架构隐含这些模型假设：

- block 是 decoder-only Transformer block；
- block order 是 pre-LN：
  - `LN1 -> SelfAttention -> Residual1 -> LN2 -> FFN -> Residual2`；
- attention 是 MHA，而不是 GQA/MQA；
- `num_heads = 12`；
- `head_dim = 64`；
- `hidden_size = 768`；
- fused QKV projection 输出维度是 `3 * hidden_size = 2304`；
- output projection 是 `hidden_size -> hidden_size`；
- FFN 是两层 dense：
  - up: `hidden_size -> intermediate_size`
  - down: `intermediate_size -> hidden_size`
- 当前 FFNUp 模板里 fused activation 是 ReLU/clamp-negative-to-zero 风格；
- LayerNorm 是 LayerNorm，不是 RMSNorm；
- LayerNorm epsilon 当前硬编码为 `1.0e-5`；
- 当前模板没有直接实现 RoPE；
- 当前模板没有直接实现 SwiGLU/gated MLP；
- 当前模板大量参数是 short-seq：
  - `MAX_SEQLEN = 16`
  - `BATCHSIZE = 16`
  - attention `TILE_SEQLEN = 16`

因此，模型输入第一版的核心不是“描述任意 LLM”，而是描述一个模型 block 是否能落到这套模板上。

---

## 2. 模型输入必须回答的架构问题

为了确定当前加速器架构，agent 至少需要模型输入回答 8 类问题。

### 2.1 模型/block 类型

需要知道：

- 模型名；
- block 类型；
- layer 数量；
- 是否 decoder-only；
- 是否 pre-LN；
- block 内部 op 顺序。

原因：

`Top.scala` 的流水顺序是固定的。如果模型是 post-LN、RMSNorm-first、parallel residual、SwiGLU block、MoE block，都不能直接绑定当前模板。

### 2.2 基本维度

需要知道：

- `hidden_size`
- `num_attention_heads`
- `num_kv_heads`
- `head_dim`
- `intermediate_size`

原因：

这些字段直接决定：

| 模型字段 | 硬件模板参数 |
| --- | --- |
| `hidden_size` | `LayerNormQ.VECTOR`, `QKVLinear.ROW_W`, `OutLinear.COL_W`, `ResAdd.VECTOR` |
| `num_attention_heads` | `QKVLinear.HEAD_NUM`, `OutLinear.HEAD_NUM`, attention head loop |
| `head_dim` | `QKVLinear.HEAD_DIM`, `OutLinear.HEAD_DIM`, `DM/DM2.HEAD_VECNUM` |
| `intermediate_size` | `FFNUp.COL_W`, `FFNDown.ROW_W` |
| `3 * hidden_size` | `QKVLinear.COL_W` |

当前模板要求：

```text
hidden_size == num_attention_heads * head_dim
intermediate_size == 4 * hidden_size
num_kv_heads == num_attention_heads
```

### 2.3 Attention 语义

需要知道：

- attention 类型：`mha | gqa | mqa`
- 是否 causal self-attention；
- 是否使用 RoPE；
- 是否使用 ALiBi；
- Q/K/V projection 是否 fused；
- Q/K/V projection 是否有 bias；
- output projection 是否有 bias。

原因：

当前 `QKVLinear` 假设 fused QKV，并把 `2304` 维输出拆成 Q/K/V。`Atten` 假设 Q/K/V 都是 12 heads、每头 64 维。GQA 会改变 KV head 数、KV-cache layout 和 Q-to-KV head mapping；RoPE 会插入额外位置编码计算；这些当前模板没有直接覆盖。

### 2.4 Norm 语义

需要知道：

- norm 类型：`layer_norm | rms_norm`
- norm 数量；
- norm 位置；
- epsilon；
- 是否有 gamma/beta。

原因：

当前 `LayerNormQ` 模板实现的是 LayerNorm：

```text
mean = sum(x) / hidden_size
var = mean(x^2) - mean(x)^2
inv_std = 1 / sqrt(var + 1e-5)
y = (x - mean) * inv_std * gamma + beta
```

它需要 FP32 gamma/beta，并输出 INT8。RMSNorm 没有 mean，也通常没有 beta，不能直接用同一模板。

### 2.5 FFN/MLP 语义

需要知道：

- FFN 类型：`dense_relu | dense_gelu | swiglu | geglu`
- up projection 维度；
- down projection 维度；
- activation 函数；
- 是否 gated；
- bias 是否存在。

原因：

当前 `FFNUp` 模板是：

```text
Linear(H -> 4H) + bias + scale + ReLU-like clamp
```

当前 `FFNDownFP32` 模板是：

```text
Linear(4H -> H) + FP32 bias
```

如果模型是 SwiGLU，需要 two-up projections 和 elementwise gate，当前模板不够。

### 2.6 数值/量化策略

需要知道：

- 输入/输出 dtype；
- weight dtype；
- activation dtype；
- 每个 stage 的 scale/zero-point 语义；
- q/k/v 是否独立 scale；
- bias scale 是否独立；
- attention score / softmax / context 的 dtype。

原因：

当前 `Top.scala` 暴露了这些量化参数接口：

```text
ln1_out_inv_scale
ln1_out_zero_point
q_out_inv_scale
k_out_inv_scale
v_out_inv_scale
q_bias_scale
k_bias_scale
v_bias_scale
dm1_out_scale
dm2_ctx_inv_scale
dm2_ctx_zero_point
dm2_out_inv_scale
out_out_scale
ln2_out_inv_scale
ln2_out_zero_point
ffnup_out_inv_scale
ffnup_bias_scale
ffndown_out_scale
```

模型输入不一定包含具体数值数据，但必须声明这些 scale 的语义来源，否则后续权重/数据打包无法和硬件对齐。

### 2.7 序列和推理模式

需要知道：

- 目标最大 sequence length；
- 是否支持 prefill；
- 是否支持 decode/single-query；
- 是否需要 KV-cache；
- 目标 layer count。

原因：

这些字段虽然不完全是“模型结构”，但会决定硬件架构：

- `MAX_SEQLEN/TILE_SEQLEN`；
- Softmax mask 规模；
- K/V cache 深度；
- DDR/片上缓存策略；
- wrapper 是否需要 long-seq history override；
- 12 层权重是否需要 layer-by-layer preload。

当前模板事实是 short-seq `16`，所以如果模型输入目标是 `912`，这必须被标成 architecture gap，而不是直接假设模板支持。

### 2.8 权重张量清单和 shape

需要知道每层有哪些权重，以及 shape：

```text
ln1.gamma      [H]
ln1.beta       [H]
qkv.weight     [H, 3H]
qkv.bias       [3H]
out.weight     [H, H]
out.bias       [H]
ln2.gamma      [H]
ln2.beta       [H]
ffn_up.weight  [H, I]
ffn_up.bias    [I]
ffn_down.weight[I, H]
ffn_down.bias  [H]
```

其中：

```text
H = hidden_size
I = intermediate_size
```

原因：

这些 shape 决定权重打包、`WMEM_DEPTH`、bias memory 深度和 stage manifest。

---

## 3. 不应该放进模型输入的内容

第一版模型输入不要放：

- 远端服务器地址；
- VCS/Vivado 命令；
- board register 地址；
- DDR region base；
- 具体 DDR image 路径；
- 具体 simulation log；
- 具体 repair history。

这些是 verification/runtime/deployment 输入，不是模型输入。

也不要让模型输入直接指定硬件微架构参数，例如：

- `ROW`
- `COL`
- FIFO depth
- bank 数
- `MEM_DEPTH`
- `WMEM_DEPTH`

这些应由硬件模板根据模型维度和设计目标派生，或者由 architecture policy 指定。模型输入只提供模型事实。

---

## 4. 推荐的最小格式：`model_spec.json`

第一版建议只使用一个 JSON 文件：

```text
model_spec.json
```

格式如下：

```json
{
  "schema_version": "spatialaccagent.model.v0",
  "model": {
    "name": "OPT-125M",
    "family": "OPT",
    "block_type": "opt_decoder_preln",
    "decoder_only": true,
    "num_layers": 12
  },
  "dimensions": {
    "hidden_size": 768,
    "num_attention_heads": 12,
    "num_kv_heads": 12,
    "head_dim": 64,
    "intermediate_size": 3072
  },
  "block_structure": {
    "norm": {
      "type": "layer_norm",
      "epsilon": 1e-5,
      "affine": true,
      "has_bias": true,
      "positions": ["pre_attention", "pre_ffn"]
    },
    "attention": {
      "type": "mha",
      "causal": true,
      "qkv_projection": "fused",
      "qkv_has_bias": true,
      "out_projection_has_bias": true,
      "position_encoding": "none",
      "rope": false,
      "alibi": false
    },
    "mlp": {
      "type": "dense_relu",
      "intermediate_size": 3072,
      "activation": "relu",
      "gated": false,
      "up_has_bias": true,
      "down_has_bias": true
    },
    "residual": {
      "residual_after_attention": true,
      "residual_after_mlp": true
    }
  },
  "numeric_policy": {
    "input_dtype": "fp32",
    "output_dtype": "fp32",
    "weight_dtype": "int8",
    "linear_activation_dtype": "int8",
    "softmax_dtype": "fp32",
    "attention_context_quant_dtype": "uint8",
    "required_runtime_scales": [
      "ln1_out_inv_scale",
      "ln1_out_zero_point",
      "q_out_inv_scale",
      "k_out_inv_scale",
      "v_out_inv_scale",
      "q_bias_scale",
      "k_bias_scale",
      "v_bias_scale",
      "dm1_out_scale",
      "dm2_ctx_inv_scale",
      "dm2_ctx_zero_point",
      "dm2_out_inv_scale",
      "out_out_scale",
      "ln2_out_inv_scale",
      "ln2_out_zero_point",
      "ffnup_out_inv_scale",
      "ffnup_bias_scale",
      "ffndown_out_scale"
    ]
  },
  "workload": {
    "target_sequence_lengths": [16],
    "prefill": true,
    "decode_single_query": true,
    "requires_kv_cache": true
  },
  "weights": {
    "per_layer": true,
    "required_tensors": [
      { "name": "ln1.gamma", "shape": ["hidden_size"], "dtype": "fp32" },
      { "name": "ln1.beta", "shape": ["hidden_size"], "dtype": "fp32" },
      { "name": "qkv.weight", "shape": ["hidden_size", "3*hidden_size"], "dtype": "int8" },
      { "name": "qkv.bias", "shape": ["3*hidden_size"], "dtype": "int8_or_quantized_bias" },
      { "name": "out.weight", "shape": ["hidden_size", "hidden_size"], "dtype": "int8" },
      { "name": "out.bias", "shape": ["hidden_size"], "dtype": "fp32" },
      { "name": "ln2.gamma", "shape": ["hidden_size"], "dtype": "fp32" },
      { "name": "ln2.beta", "shape": ["hidden_size"], "dtype": "fp32" },
      { "name": "ffn_up.weight", "shape": ["hidden_size", "intermediate_size"], "dtype": "int8" },
      { "name": "ffn_up.bias", "shape": ["intermediate_size"], "dtype": "int8_or_quantized_bias" },
      { "name": "ffn_down.weight", "shape": ["intermediate_size", "hidden_size"], "dtype": "int8" },
      { "name": "ffn_down.bias", "shape": ["hidden_size"], "dtype": "fp32" }
    ]
  }
}
```

---

## 5. 用这个模型输入如何选择硬件模板

agent 读取 `model_spec.json` 后，先做 compatibility check。

### 5.1 当前模板可直接接受的条件

```text
block_type == opt_decoder_preln
norm.type == layer_norm
norm.epsilon == 1e-5
attention.type == mha
num_kv_heads == num_attention_heads
position_encoding == none
hidden_size == 768
num_attention_heads == 12
head_dim == 64
intermediate_size == 3072
mlp.type == dense_relu
mlp.gated == false
```

满足这些条件时，可以绑定当前模板：

| 模型语义 | 当前模板 |
| --- | --- |
| pre-attention LayerNorm | `LayerNormQ` |
| fused QKV projection | `QKVLinear` |
| QK score | `DM1FP32` |
| causal softmax | `SoftmaxPipFP32` |
| PV/context | `DM2Quant` |
| output projection | `OutLinearFP32` |
| residual 1 | `ResAddFP32` |
| pre-FFN LayerNorm | `LayerNormQ` |
| FFN up + ReLU | `FFNUp` |
| FFN down | `FFNDownFP32` |
| residual 2 | `ResAdd2FP32` |

### 5.2 需要新模板或 human approval 的条件

下面这些模型输入不能静默绑定当前模板：

| 模型字段 | 当前模板问题 |
| --- | --- |
| `norm.type == rms_norm` | `LayerNormQ` 计算 mean/variance，不是 RMSNorm |
| `attention.type == gqa/mqa` | KV head 数和 Q-to-KV mapping 不同 |
| `rope == true` | 当前 attention 前没有 RoPE 模块 |
| `mlp.type == swiglu/geglu` | 当前 FFN 不是 gated MLP |
| `activation == gelu` | 当前 `FFNUp` 是 ReLU/clamp 风格 |
| `hidden_size != 768` | 多个模板常量固定 768 |
| `num_heads != 12` | attention、OutLinear head buffer 固定 12 heads |
| `head_dim != 64` | DM/DM2/VCache 固定 64 |
| `intermediate_size != 3072` | FFNUp/FFNDown 常量固定 3072 |
| `target_sequence_length > 16` | 当前 active params 多处固定 16 |

这些情况应生成 SACG conflict，而不是让 agent 直接改代码。

---

## 6. 字段到硬件参数的映射

模型输入到当前硬件模板的第一版映射如下：

| model field | hardware field |
| --- | --- |
| `hidden_size` | `LayerNormQ.VECTOR`, `QKVLinear.ROW_W`, `OutLinear.ROW_W/COL_W`, `ResAdd.VECTOR` |
| `num_attention_heads` | `QKVLinear.HEAD_NUM`, `OutLinear.HEAD_NUM`, `DM/DM2.SINGLE_QUERY_BATCH` |
| `head_dim` | `QKVLinear.HEAD_DIM`, `OutLinear.HEAD_DIM`, `DM.HEAD_VECNUM`, `DM2.HEAD_VECNUM` |
| `intermediate_size` | `FFNUp.COL_W`, `FFNDown.ROW_W` |
| `norm.epsilon` | `LayerNormQ` epsilon constant |
| `qkv_projection=fused` | `QKVLinear.COL_W = 3 * hidden_size` |
| `mlp.activation=relu` | `FFNUp` fused post-process |
| `target_sequence_lengths` | `MAX_SEQLEN`, `TILE_SEQLEN`, Softmax mask width, K/V cache depth |
| `numeric_policy.required_runtime_scales` | `Top.scala` scale/zero-point IO |

---

## 7. HuggingFace config 归一化

后续要支持 LLaMA、Qwen、GPT2、OPT 时，模型输入不应该要求用户手写完整 `model_spec.json`。

推荐做法是分两层：

```text
HuggingFace config.json
-> hf_config_adapter
-> canonical model_spec.json
-> template_compatibility_check
```

也就是说，HuggingFace config 是外部输入；`model_spec.json` 是 SpatialAccAgent 内部统一格式。

### 7.1 外部输入格式

最小外部输入可以是：

```json
{
  "schema_version": "spatialaccagent.hf_source.v0",
  "source": {
    "type": "huggingface_config",
    "model_id": "facebook/opt-125m",
    "config_path": "/path/to/config.json",
    "revision": null,
    "local_only": true
  },
  "adapter": {
    "family": "auto"
  },
  "workload_overrides": {
    "target_sequence_lengths": [16],
    "prefill": true,
    "decode_single_query": true
  },
  "numeric_policy": {
    "name": "current_mixed_int8_fp32"
  }
}
```

说明：

- `model_id` 用于记录来源；
- `config_path` 是实际读取的本地 HuggingFace `config.json`；
- `local_only=true` 表示当前框架不依赖联网；
- `workload_overrides` 是项目/硬件目标，不一定来自 HF config；
- `numeric_policy` 也不完全来自 HF config，需要单独声明。

### 7.2 family adapter 字段映射

不同 HuggingFace family 的字段名不同，adapter 负责映射到统一字段。

| family | HF config fields | canonical fields |
| --- | --- | --- |
| GPT2 | `n_layer`, `n_embd`, `n_head`, `n_inner`, `activation_function`, `layer_norm_epsilon`, `n_positions` | `num_layers`, `hidden_size`, `num_attention_heads`, `intermediate_size`, `mlp.activation`, `norm.epsilon`, `max_position_embeddings` |
| OPT | `num_hidden_layers`, `hidden_size`, `num_attention_heads`, `ffn_dim`, `activation_function`, `do_layer_norm_before`, `max_position_embeddings` | `num_layers`, `hidden_size`, `num_attention_heads`, `intermediate_size`, `mlp.activation`, `pre_ln`, `max_position_embeddings` |
| LLaMA | `num_hidden_layers`, `hidden_size`, `intermediate_size`, `num_attention_heads`, `num_key_value_heads`, `head_dim`, `hidden_act`, `rms_norm_eps`, `rope_theta`, `rope_scaling`, `max_position_embeddings` | `num_layers`, `hidden_size`, `intermediate_size`, `num_attention_heads`, `num_kv_heads`, `head_dim`, `mlp.activation`, `norm.epsilon`, `rope`, `max_position_embeddings` |
| Qwen/Qwen2 | `num_hidden_layers`, `hidden_size`, `intermediate_size`, `num_attention_heads`, `num_key_value_heads`, `hidden_act`, `rms_norm_eps`, `rope_theta`, `rope_scaling`, `max_position_embeddings`, `use_sliding_window`, `sliding_window` | same as LLaMA plus optional sliding-window attention fields |

adapter 需要补全派生字段：

```text
head_dim = hidden_size / num_attention_heads    如果 HF config 未显式给出
num_kv_heads = num_attention_heads              如果 HF config 未显式给出
intermediate_size = 4 * hidden_size              如果 GPT2 n_inner 为空
attention.type = mha                             如果 num_kv_heads == num_attention_heads
attention.type = gqa                             如果 1 < num_kv_heads < num_attention_heads
attention.type = mqa                             如果 num_kv_heads == 1
```

### 7.3 family 到当前模板的预期结果

adapter 只负责抽取模型事实，不负责假装模板兼容。

归一化后，`template_compatibility_check` 应给出类似结果：

| family | 当前模板预期 |
| --- | --- |
| OPT-125M | 大体可绑定当前 OPT-style 模板，前提是 `hidden=768/head=12/head_dim=64/ffn=3072/activation=relu/seq<=16` |
| GPT2-small | 结构上接近 pre-LN MHA，但通常是 GELU MLP，需要 GELU 或允许近似替换；否则 `needs_new_template` |
| LLaMA | RMSNorm + RoPE + SwiGLU + 可能 GQA，当前模板不直接支持，应为 `needs_new_template` |
| Qwen/Qwen2 | RMSNorm + RoPE + GQA + SwiGLU，当前模板不直接支持，应为 `needs_new_template` |

这正好符合 SACG 的作用：模型 config 进入统一 spec 后，compatibility checker 生成模板绑定或显式 conflict。

### 7.4 canonical spec 中需要保留 HF 来源

由 HF config 生成的 `model_spec.json` 应保留来源字段：

```json
{
  "schema_version": "spatialaccagent.model.v0",
  "source": {
    "type": "huggingface_config",
    "model_id": "facebook/opt-125m",
    "config_path": "/path/to/config.json",
    "architecture": "OPTForCausalLM"
  },
  "model": {
    "name": "OPT-125M",
    "family": "OPT",
    "block_type": "opt_decoder_preln",
    "decoder_only": true,
    "num_layers": 12
  }
}
```

这样后续 trace、checker、论文实验都能说明模型事实来自哪里。

---

## 8. 当前最小实现建议

下一步框架不要先做复杂输入包，先做两个很小的东西：

1. `hf_config_adapter`
2. `model_spec.json` loader
3. `template_compatibility_check`

`template_compatibility_check` 只做三件事：

```text
读取 HuggingFace config 或 model_spec.json
归一化成 canonical model_spec
检查是否能绑定当前 src/main/scala 模板
输出 accepted / rejected / needs_new_template，并列出原因
```

最小输出可以是：

```json
{
  "result": "accepted",
  "selected_template": "opt_preln_current_top",
  "bound_params": {
    "hidden_size": 768,
    "num_heads": 12,
    "head_dim": 64,
    "intermediate_size": 3072,
    "max_seq_len": 16
  },
  "selected_modules": [
    "LayerNormQ",
    "QKVLinear",
    "Atten",
    "OutLinearFP32",
    "ResAddFP32",
    "FFNUp",
    "FFNDownFP32",
    "ResAdd2FP32"
  ],
  "warnings": []
}
```

如果输入是 Qwen/GQA/RoPE/SwiGLU，则应该输出：

```json
{
  "result": "needs_new_template",
  "conflicts": [
    "attention.type=gqa is not supported by current MHA template",
    "rope=true requires a RoPE template before DM1/DM2",
    "mlp.type=swiglu requires gated FFN templates"
  ]
}
```

---

## 9. 一句话总结

当前阶段需要的模型输入格式应是一个小而严格的 `model_spec.json`。

它只需要描述：

```text
模型/block 类型、核心维度、attention 语义、norm 语义、FFN 语义、
数值策略、目标序列模式、权重张量 shape。
```

这些字段足够决定当前硬件模板能不能用、应该选哪些模板、哪些参数能绑定、哪些地方需要新模板或 human approval。

对于 GPT2、OPT、LLaMA、Qwen/Qwen2，外部可以从 HuggingFace `config.json` 读取；框架先通过 `hf_config_adapter` 把 family-specific 字段归一化到同一个 `model_spec.json`，再做硬件模板兼容性检查。
