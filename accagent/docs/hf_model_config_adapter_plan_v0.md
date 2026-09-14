# HuggingFace Model Config Adapter Plan v0

> Scope correction, 2026-06-24:
>
> 当前阶段只做 HuggingFace / 本地模型目录的模型配置读取与 canonical `model_config.json` 生成。
> 模板兼容性判断、`needs_new_template`、硬件模板缺失分析放到后续阶段。
> 最新聚焦规格见 `accagent/docs/hf_model_config_extraction_spec_v0.md`。
> 本文后续保留的 `model_spec.json`、compatibility report、宽字段 schema 内容是历史规划记录，不作为当前实现依据。

## 0. 目标

本功能用于把已经下载到本地的 HuggingFace 模型配置：

```text
<model_dir>/config.json
```

转换成 SpatialAccAgent 内部统一使用的结构化模型输入：

```text
model_spec.json
```

第一批目标模型：

```text
OPT-125M
GPT2
```

后续扩展：

```text
LLaMA
Qwen / Qwen2
```

核心原则：

> HuggingFace config 是外部模型事实来源；`model_spec.json` 是 agent 框架内部 canonical model spec；硬件模板兼容性检查只读取 canonical spec，不直接读取不同 family 的 config 字段。

---

## 1. 为什么不能直接用 transformers pipeline

当前已有：

```text
accagent/framework/model/opt125m.py
accagent/framework/model/gpt2.py
```

它们目前只是：

```python
from transformers import pipeline

pipe = pipeline("text-generation", model="facebook/opt-125m")
```

这不适合作为 SpatialAccAgent 的模型输入抽取逻辑，原因是：

- 它会加载完整模型，太重；
- 它依赖 `transformers` runtime，不适合作为最小框架基础；
- 它不输出结构化 accelerator design constraints；
- 它无法直接告诉硬件模板：hidden size、head 数、FFN 维度、norm 类型、activation、RoPE/GQA 等关键架构事实；
- 它没有记录字段来源和 compatibility conflicts。

因此第一版 adapter 应只使用 Python 标准库读取 JSON。

---

## 2. 功能边界

### 2.1 输入

最小输入是一个 HF source 描述文件，建议命名：

```text
hf_source.json
```

格式：

```json
{
  "schema_version": "spatialaccagent.hf_source.v0",
  "source": {
    "type": "huggingface_config",
    "model_id": "facebook/opt-125m",
    "model_dir": "/path/to/facebook/opt-125m",
    "config_path": "/path/to/facebook/opt-125m/config.json",
    "local_only": true
  },
  "adapter": {
    "family": "auto"
  },
  "workload_overrides": {
    "target_sequence_lengths": [16],
    "prefill": true,
    "decode_single_query": true,
    "requires_kv_cache": true
  },
  "numeric_policy": {
    "name": "current_mixed_int8_fp32"
  }
}
```

说明：

- `config_path` 是唯一必须能读取的文件；
- `model_dir` 用于记录来源，不要求 adapter 扫描权重；
- `family=auto` 时由 config 中的 `model_type` 或 `architectures` 判断；
- `workload_overrides` 不来自 HF config，是我们要生成 accelerator 时的目标 workload；
- `numeric_policy` 不来自 HF config，是硬件/量化策略。

也可以允许命令行直接输入：

```bash
python3 -m accagent.framework.model.hf_config_adapter \
  --config /path/to/config.json \
  --model-id facebook/opt-125m \
  --target-seq 16 \
  --out accagent/runs/opt125m/model_spec.json
```

### 2.2 输出

adapter 输出两个文件：

```text
model_spec.json
model_config_adapter_report.json
```

`model_spec.json` 是后续 agent 框架输入。

`model_config_adapter_report.json` 记录：

- 原始 config 路径；
- 识别出的 family；
- 字段映射；
- 派生字段；
- 缺失字段；
- 默认值；
- 需要 human 确认的字段。

---

## 3. Canonical `model_spec.json`

adapter 输出的 `model_spec.json` 应符合：

```json
{
  "schema_version": "spatialaccagent.model.v0",
  "source": {
    "type": "huggingface_config",
    "model_id": "facebook/opt-125m",
    "config_path": "/path/to/config.json",
    "model_type": "opt",
    "architectures": ["OPTForCausalLM"]
  },
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
    "intermediate_size": 3072,
    "max_position_embeddings": 2048
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
      "qkv_projection": "fused_or_logically_fused",
      "qkv_has_bias": true,
      "out_projection_has_bias": true,
      "position_encoding": "learned_absolute",
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
  "workload": {
    "target_sequence_lengths": [16],
    "prefill": true,
    "decode_single_query": true,
    "requires_kv_cache": true
  },
  "numeric_policy": {
    "name": "current_mixed_int8_fp32"
  },
  "weights": {
    "per_layer": true,
    "required_tensors": []
  }
}
```

`required_tensors` 可以在第二步由 family-specific tensor planner 补齐；第一版 adapter 可以先生成结构字段。

---

## 4. Family adapter 设计

代码结构建议：

```text
accagent/framework/model/
  __init__.py
  hf_config_adapter.py
  model_spec.py
  template_compatibility.py
  families/
    __init__.py
    opt.py
    gpt2.py
    llama.py
    qwen.py
```

职责：

| 文件 | 职责 |
| --- | --- |
| `hf_config_adapter.py` | CLI 入口，读取 config，选择 family adapter，写出 model_spec/report |
| `model_spec.py` | canonical spec 构造、校验、默认值、JSON 写出 |
| `template_compatibility.py` | 检查 canonical spec 是否能绑定当前硬件模板 |
| `families/opt.py` | OPT config -> canonical spec |
| `families/gpt2.py` | GPT2 config -> canonical spec |
| `families/llama.py` | LLaMA config -> canonical spec |
| `families/qwen.py` | Qwen/Qwen2 config -> canonical spec |

第一版可以只实现：

```text
hf_config_adapter.py
families/opt.py
families/gpt2.py
```

LLaMA/Qwen 先在 adapter 中识别并输出 `needs_new_template`，后续再补。

---

## 5. Family 识别规则

优先级：

```text
config["model_type"]
-> config["architectures"][0]
-> model_id / config_path basename
-> explicit --family
```

初始规则：

| family | detection |
| --- | --- |
| OPT | `model_type == "opt"` 或 architecture 包含 `OPT` |
| GPT2 | `model_type == "gpt2"` 或 architecture 包含 `GPT2` |
| LLaMA | `model_type in ["llama", "mistral"]` 或 architecture 包含 `Llama` |
| Qwen/Qwen2 | `model_type` 包含 `qwen` 或 architecture 包含 `Qwen` |

如果识别失败：

```json
{
  "status": "unsupported_family",
  "reason": "cannot infer family from model_type/architectures/model_id"
}
```

---

## 6. OPT adapter

### 6.1 读取字段

OPT 常见字段：

```text
model_type
architectures
num_hidden_layers
hidden_size
num_attention_heads
ffn_dim
activation_function
do_layer_norm_before
max_position_embeddings
layerdrop
dropout
attention_dropout
word_embed_proj_dim
```

### 6.2 映射规则

```text
num_layers             = num_hidden_layers
hidden_size            = hidden_size
num_attention_heads    = num_attention_heads
num_kv_heads           = num_attention_heads
head_dim               = hidden_size / num_attention_heads
intermediate_size      = ffn_dim
norm.type              = layer_norm
norm.epsilon           = layer_norm_eps if present else 1e-5
norm.positions         = pre_attention/pre_ffn if do_layer_norm_before else post_attention/post_ffn
attention.type         = mha
attention.rope         = false
attention.position_encoding = learned_absolute
mlp.activation         = activation_function
mlp.gated              = false
```

### 6.3 OPT-125M 当前预期

对 `facebook/opt-125m`，预期 canonical spec：

```text
hidden_size = 768
num_attention_heads = 12
num_kv_heads = 12
head_dim = 64
intermediate_size = 3072
num_layers = 12
attention.type = mha
norm.type = layer_norm
mlp.activation = relu
```

这与当前 `src/main/scala` 模板最接近。

---

## 7. GPT2 adapter

### 7.1 读取字段

GPT2 常见字段：

```text
model_type
architectures
n_layer
n_embd
n_head
n_inner
activation_function
layer_norm_epsilon
n_positions
scale_attn_weights
use_cache
```

### 7.2 映射规则

```text
num_layers             = n_layer
hidden_size            = n_embd
num_attention_heads    = n_head
num_kv_heads           = n_head
head_dim               = n_embd / n_head
intermediate_size      = n_inner if not null else 4 * n_embd
norm.type              = layer_norm
norm.epsilon           = layer_norm_epsilon
norm.positions         = pre_attention/pre_ffn
attention.type         = mha
attention.rope         = false
attention.position_encoding = learned_absolute
mlp.activation         = activation_function
mlp.gated              = false
```

### 7.3 GPT2 当前预期

对 `openai-community/gpt2` / GPT2-small，预期：

```text
hidden_size = 768
num_attention_heads = 12
head_dim = 64
intermediate_size = 3072
num_layers = 12
attention.type = mha
norm.type = layer_norm
mlp.activation = gelu_new 或 gelu
```

它和当前模板的主要冲突是：

```text
当前 FFNUp 是 ReLU/clamp 风格；
GPT2 通常使用 GELU/GELU_NEW。
```

因此 compatibility report 应输出：

```json
{
  "result": "needs_new_template",
  "conflicts": [
    {
      "field": "block_structure.mlp.activation",
      "model_value": "gelu_new",
      "template_supported": ["relu"],
      "required_action": "add_gelu_ffn_template_or_approve_relu_approximation"
    }
  ]
}
```

---

## 8. Compatibility check 输出

adapter 可以只生成 canonical spec；但建议同一 CLI 顺手生成 compatibility report。

当前硬件模板名：

```text
opt_preln_current_top
```

硬件模板支持条件：

```text
family roughly OPT/GPT-style
decoder_only == true
block order == pre-LN
norm.type == layer_norm
attention.type == mha
rope == false
hidden_size == 768
num_attention_heads == 12
num_kv_heads == 12
head_dim == 64
intermediate_size == 3072
mlp.gated == false
mlp.activation == relu
target_sequence_length <= 16
```

输出格式：

```json
{
  "schema_version": "spatialaccagent.compatibility.v0",
  "model_spec": "model_spec.json",
  "template": "opt_preln_current_top",
  "result": "accepted",
  "bound_params": {
    "hidden_size": 768,
    "num_heads": 12,
    "num_kv_heads": 12,
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
    "LayerNormQ",
    "FFNUp",
    "FFNDownFP32",
    "ResAdd2FP32"
  ],
  "conflicts": [],
  "warnings": []
}
```

结果枚举：

| result | 含义 |
| --- | --- |
| `accepted` | 可直接绑定当前模板 |
| `accepted_with_warnings` | 可绑定，但存在近似或需要确认的字段 |
| `needs_new_template` | 模型结构与当前模板不兼容，需要新模板 |
| `rejected` | config 缺失关键字段或字段非法 |

---

## 9. CLI 规划

建议第一版 CLI：

```bash
python3 -m accagent.framework.model.hf_config_adapter \
  --config /path/to/config.json \
  --model-id facebook/opt-125m \
  --family auto \
  --target-seq 16 \
  --numeric-policy current_mixed_int8_fp32 \
  --out-dir accagent/runs/opt125m_model_input
```

生成：

```text
accagent/runs/opt125m_model_input/
  model_spec.json
  model_config_adapter_report.json
  template_compatibility_report.json
```

可选输入：

```bash
--target-seq 16,912
--prefill true
--decode-single-query true
--requires-kv-cache true
--strict
```

`--strict` 表示任何不兼容都输出 `needs_new_template`，不允许近似替换。

---

## 10. 测试计划

第一版只需要三个 smoke tests：

### 10.1 OPT-125M config

输入：

```text
facebook/opt-125m/config.json
```

期望：

```text
family = OPT
hidden_size = 768
num_attention_heads = 12
head_dim = 64
intermediate_size = 3072
num_layers = 12
compatibility result = accepted
```

### 10.2 GPT2 config

输入：

```text
openai-community/gpt2/config.json
```

期望：

```text
family = GPT2
hidden_size = 768
num_attention_heads = 12
head_dim = 64
intermediate_size = 3072
num_layers = 12
compatibility result = needs_new_template
conflict includes mlp.activation = gelu/gelu_new
```

### 10.3 Missing field config

构造一个缺少 `hidden_size/n_embd` 的 fake config。

期望：

```text
result = rejected
missing_fields includes hidden_size
```

---

## 11. 近期实现顺序

最小实现顺序：

1. 新增 `accagent/framework/model/__init__.py`。
2. 新增 `model_spec.py`，定义 canonical spec helper 和 JSON writer。
3. 新增 `hf_config_adapter.py`，实现 CLI 和 family auto-detection。
4. 新增 OPT adapter。
5. 新增 GPT2 adapter。
6. 新增 `template_compatibility.py`，先硬编码当前 `opt_preln_current_top` 模板支持条件。
7. 用用户下载的 OPT-125M/GPT2 `config.json` 生成两个 `model_spec.json` 和两个 compatibility report。

当前用户还需要提供或确认本地模型路径，因为本轮在当前仓库和 `/home/remote/workspace` 下没有找到 OPT/GPT2 的 `config.json`。

---

## 12. 一句话总结

这个功能的本质是：

```text
把 HuggingFace 各 family 的 config.json 归一化为 SpatialAccAgent 的 canonical model_spec.json，
然后用当前硬件模板的支持条件生成 accepted / needs_new_template / rejected 的兼容性报告。
```

第一版不加载模型权重、不运行 inference、不依赖 transformers，只读 `config.json`。
