# HuggingFace Model Config Extraction Spec v0 - Minimal Hardware Fields

## 0. Scope Correction

This document defines only the minimal `model_config.json` fields needed to generate or bind the current spatial accelerator hardware.

The previous broader idea of storing `source`, `raw_config_summary`, `token_embedding`, `generation`, full diagnostics, and available files inside `model_config.json` is no longer the active design. Those fields are useful for audit, but they are not hardware inputs.

The split is:

```text
model_config.json
  Minimal hardware-facing model facts only.

model_config_extraction_report.json
  Source path, raw HF fields, defaults, warnings, dropped fields, and audit details.
```

The current stage still only reads model configuration from HuggingFace / local model directories. It does not judge whether a hardware template exists, and it does not output `needs_new_template`.

## 1. Hardware-Derived Minimality Rule

A field may enter `model_config.json` only if it can change at least one of these hardware-visible decisions:

- Chisel matrix dimensions;
- attention head structure;
- KV-cache / softmax / sequence buffer sizing;
- normalization template or constants;
- MLP template or activation;
- bias memory / input ports;
- weight packing layout needed by the hardware data path;
- layer scheduling for the full accelerator.

Everything else must be dropped from `model_config.json`.

The current `src/main/scala` hardware confirms this:

| Model field | Hardware use |
| --- | --- |
| `num_layers` | full-model layer loop, per-layer weight scheduling, double-buffer preload plan |
| `hidden_size` | `LayerNormQ.Param.VECTOR`, `QKVLinear.Param.ROW_W`, `OutLinear.Param.ROW_W/COL_W`, residual vector size |
| `num_q_heads` | `QKVLinear.Param.HEAD_NUM`, `OutLinear.Param.HEAD_NUM`, attention batch/head traversal |
| `num_kv_heads` | distinguishes MHA/GQA/MQA; required for LLaMA/Qwen/Gemma3 even though OPT/GPT2 use MHA |
| `head_dim` | `QKVLinear.Param.HEAD_DIM`, `OutLinear.Param.HEAD_DIM`, `DM.Param.HEAD_VECNUM` |
| `intermediate_size` | `FFNUp.Param.COL_W`, `FFNDown.Param.ROW_W` |
| `target_max_seq_len` | `MAX_SEQLEN`, `TILE_SEQLEN`, `Softmax.Param.SEQ_LEN`, KV-cache/score buffer bounds |
| `norm.type` | selects LayerNorm vs RMSNorm-style normalization template |
| `norm.position` | selects pre-norm vs post-norm top-level block wiring |
| `norm.eps` | normalization constant when the template exposes it |
| `norm.has_bias` | whether beta exists; current `LayerNormQ` loads beta then gamma |
| `attention.causal` | softmax mask semantics |
| `attention.position_encoding` | whether RoPE/absolute/no position logic is needed before attention |
| `attention.qkv_bias`, `attention.out_bias` | QKV/out bias memories and ports |
| `mlp.type` | dense MLP vs gated MLP data path |
| `mlp.activation` | fused FFN activation; current `FFNUp` fuses ReLU |
| `mlp.up_bias`, `mlp.down_bias` | FFN bias memories and ports |
| `weight_layout.*` | tells the packer whether HF weights are separate or fused; not a Chisel dimension by itself |

The following are not model configuration inputs for hardware generation:

- `vocab_size`;
- tokenizer files;
- BOS/EOS/PAD IDs;
- `generation_config.json`;
- dropout fields;
- initializer fields;
- `torch_dtype`;
- `tie_word_embeddings`;
- `architectures`;
- full tensor file list;
- full source/provenance metadata;
- all runtime quantization scale names;
- Chisel-only template parameters such as `LANES`, `ROW`, `COL`, bank count, FIFO depth, AXI width.

Those belong either to the extraction report, the hardware template library, or the design target card, not to the minimal model config.

## 2. Minimal `model_config.json`

The active minimal schema is:

```json
{
  "model_type": "opt",
  "num_layers": 12,
  "hidden_size": 768,
  "target_max_seq_len": 16,
  "attention": {
    "kind": "mha",
    "num_q_heads": 12,
    "num_kv_heads": 12,
    "head_dim": 64,
    "causal": true,
    "position_encoding": {
      "type": "learned_absolute"
    },
    "qkv_bias": true,
    "out_bias": true
  },
  "norm": {
    "type": "layer_norm",
    "position": "pre",
    "eps": 0.00001,
    "has_bias": true
  },
  "mlp": {
    "type": "dense",
    "intermediate_size": 3072,
    "activation": "relu",
    "up_bias": true,
    "down_bias": true
  },
  "weight_layout": {
    "qkv": "separate_q_k_v",
    "out_proj": "dense",
    "mlp": "fc1_fc2",
    "norm": "weight_bias"
  }
}
```

`target_max_seq_len` is the only design-target field allowed in this file because it directly drives hardware buffer and softmax/KV-cache bounds. It is not a pure HF model fact. The extractor should take it from a CLI/task-card override. The extraction report may separately record the HF context limit for validation.

`head_dim` is derivable from `hidden_size / num_q_heads`, but it is kept because the hardware uses it directly and because some model families expose it explicitly. The extractor must verify consistency.

`schema_version` is intentionally not part of `model_config.json`: it is framework metadata, not a hardware model fact. If needed, version/provenance information belongs in `model_config_extraction_report.json`.

## 3. Required Extraction Mapping

### 3.1 OPT

Minimal mapping from HF config and weight directory:

```text
model_type              <- config.model_type
num_layers              <- config.num_hidden_layers
hidden_size             <- config.hidden_size
target_max_seq_len      <- CLI/task-card override
attention.kind          <- "mha"
attention.num_q_heads   <- config.num_attention_heads
attention.num_kv_heads  <- config.num_attention_heads
attention.head_dim      <- hidden_size / num_q_heads
attention.causal        <- true
attention.position_encoding.type <- "learned_absolute"
attention.qkv_bias      <- detected from q_proj/k_proj/v_proj bias tensors
attention.out_bias      <- detected from out_proj bias tensor
norm.type               <- "layer_norm"
norm.position           <- "pre" if do_layer_norm_before else "post"
norm.eps                <- config.layer_norm_eps or 1e-5
norm.has_bias           <- detected from final/input layer norm bias tensors
mlp.type                <- "dense"
mlp.intermediate_size   <- config.ffn_dim
mlp.activation          <- config.activation_function
mlp.up_bias             <- detected from fc1 bias tensor
mlp.down_bias           <- detected from fc2 bias tensor
weight_layout.qkv       <- "separate_q_k_v"
weight_layout.mlp       <- "fc1_fc2"
weight_layout.norm      <- "weight_bias"
```

### 3.2 GPT2

Minimal mapping from HF config and weight directory:

```text
model_type              <- config.model_type
num_layers              <- config.n_layer
hidden_size             <- config.n_embd
target_max_seq_len      <- CLI/task-card override
attention.kind          <- "mha"
attention.num_q_heads   <- config.n_head
attention.num_kv_heads  <- config.n_head
attention.head_dim      <- hidden_size / num_q_heads
attention.causal        <- true
attention.position_encoding.type <- "learned_absolute"
attention.qkv_bias      <- detected from c_attn bias tensor
attention.out_bias      <- detected from c_proj bias tensor
norm.type               <- "layer_norm"
norm.position           <- "pre"
norm.eps                <- config.layer_norm_epsilon or 1e-5
norm.has_bias           <- detected from ln_* bias tensors
mlp.type                <- "dense"
mlp.intermediate_size   <- config.n_inner or 4 * hidden_size
mlp.activation          <- config.activation_function
mlp.up_bias             <- detected from c_fc bias tensor
mlp.down_bias           <- detected from mlp c_proj bias tensor
weight_layout.qkv       <- "fused_qkv"
weight_layout.mlp       <- "c_fc_c_proj"
weight_layout.norm      <- "weight_bias"
```

### 3.3 LLaMA / Qwen / Gemma3 Later

The same minimal schema is sufficient for later LLaMA/Qwen/Gemma3 support:

```text
attention.kind          <- "mha" | "gqa" | "mqa"
attention.num_kv_heads  <- config.num_key_value_heads
attention.position_encoding.type <- "rope"
attention.position_encoding.rope_theta <- config.rope_theta
attention.position_encoding.rope_scaling <- config.rope_scaling if present
norm.type               <- "rms_norm"
norm.eps                <- config.rms_norm_eps
norm.has_bias           <- false for standard RMSNorm
mlp.type                <- "gated"
mlp.activation          <- config.hidden_act
weight_layout.mlp       <- "gate_up_down"
```

Only add RoPE subfields when `position_encoding.type == "rope"`.

For Gemma3 text blocks, keep the same minimal family shape, with two extra facts from the HF config:

```text
attention.qkv_bias <- config.attention_bias
attention.qk_norm <- true
```

## 4. Minimal Validation Rules

The extractor must reject or report invalid configs when:

```text
hidden_size % num_q_heads != 0
head_dim != hidden_size / num_q_heads
num_q_heads % num_kv_heads != 0
target_max_seq_len <= 0
intermediate_size <= 0
num_layers <= 0
```

If the HF context limit is available, the report should warn when:

```text
target_max_seq_len > hf_context_limit
```

This warning belongs to `model_config_extraction_report.json`; the hardware-facing config still only stores `target_max_seq_len`.

## 5. Extraction Report Contents

`model_config_extraction_report.json` may contain anything needed for debugging and audit, including:

- model directory and config path;
- whether `transformers.AutoConfig` or raw JSON was used;
- raw HF identifying fields;
- HF context length;
- dropped fields;
- missing fields and defaults;
- tensor files inspected;
- bias detection evidence;
- validation warnings.

The report is not consumed by the hardware parameter binder unless explicitly requested.

## 6. Current Conda Environment

The intended environment for this extractor is:

```bash
conda run -n diff python ...
```

The local `diff` environment currently has `transformers` available, so the first implementation can use `AutoConfig.from_pretrained(..., local_files_only=True)` with raw JSON fallback.
