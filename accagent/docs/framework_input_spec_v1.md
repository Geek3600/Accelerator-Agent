# SpatialAccAgent Framework Input Specification v1

## 0. 文档目的

本文档回答一个具体问题：

```text
为了让 SpatialAccAgent 复现 docs/context_2026-03-27.md 中记录的真实加速器设计过程，
并且能浮现出当前仓库中的真实加速器代码，框架到底需要什么输入，输入格式应该是什么样的？
```

核心结论是：

> SpatialAccAgent 的输入不能只是一个自然语言 prompt，也不能只是一个极简 task card。对于当前项目，它必须是一个可审计的 **Design Reproduction Package**，同时包含目标任务、上下文过程、当前代码事实、真实数据 case、工具协议、平台部署信息、人工审批边界和 SACG seed 规则。

这个输入包的目标不是描述一个 toy accelerator，而是支撑下面两件事：

1. **复现过程**：把 `docs/context_2026-03-27.md` 中记录的真实设计、验证、修复、综合、上板闭环变成可执行流程。
2. **浮现代码**：把当前仓库中的 `Top.scala`、各 stage 模块、SystemTop/AXI wrapper、verification case、remote tool scripts、synthesis/board scripts 索引进 SACG，使 agent 能从现有代码事实出发检查和复现真实 accelerator。

---

## 1. 当前阅读得到的输入事实

### 1.1 上下文文档给出的目标过程

`docs/context_2026-03-27.md` 是框架开发的设计过程来源。它记录的不是普通聊天，而是一条真实 accelerator design closure trace：

```text
任务定义
-> Chisel/RTL 修改
-> stage-level 验证
-> top-level 验证
-> system-level DDR/AXI 验证
-> remote Verilator/VCS
-> Vivado synthesis / implementation
-> board runtime / debug register / smoke run
-> bug 定位、修复、回归
```

因此框架输入必须保留：

- 每个阶段的目标；
- 当时操作过的 artifact；
- 使用的工具命令；
- pass/fail evidence；
- failure symptom；
- broken constraint；
- repair action；
- regression result；
- human approval 或 manual decision。

### 1.2 当前代码给出的实现事实

当前仓库中的加速器不是单个 RTL 文件，而是一组强耦合 artifact。

最核心代码入口是：

```text
src/main/scala/Top.scala
```

它实例化的主流水为：

```text
LNAddrGen
-> LayerNormQ
-> QKVLinear
-> Atten
   -> DM1
   -> Softmax
   -> VCache / DM2
-> OutLinearFP32
-> ResAddFP32
-> LayerNormQ
-> FFNUp
-> FFNDownFP32
-> ResAdd2FP32
```

`Top.scala` 同时暴露了大量跨层接口：

- `cfg_seqlen/cfg_prefill/cfg_valid`；
- attention 独立配置口 `attn_cfg_*`；
- long-seq history tap 和 override 口；
- weight init / active bank / preload bank；
- qkv/out/ffn weight preload 地址和数据口；
- scale / zero point / bias scale；
- `valid/ready/st/last/addr` stream 协议；
- `res/res_st/res_addr/res_valid/res_last/res_ready` 输出协议。

这说明框架输入必须记录顶层 IO contract，而不能只记录模型 shape。

### 1.3 当前参数事实与目标事实存在冲突

上下文目标和验收目标中有：

```text
OPT-125M
12 layers
full sequence 912
VU9P board run
```

但当前很多 Scala 参数文件中仍是 short-seq 配置，例如：

```text
MAX_SEQLEN = 16
BATCHSIZE = 16
TILE_SEQLEN = 16
```

同时 `scripts/verification/opt125m_e2e.py` 中仍有历史常量：

```text
CURRENT_CORE_MAX_SEQLEN = 26
CURRENT_CORE_MAX_PREFILL = 8
```

而 `verification/cases/opt125m_9p_fullseq/case.json` 又记录：

```text
token_count_full = 912
ddr_word_width_bits = 512
ddr_total_beats = 258906
```

因此输入格式必须显式区分：

- `target_behavior`：上下文/任务要求最终复现的目标，例如 12 层、912 token、board run；
- `current_code_facts`：当前仓库真实代码参数，例如 short-seq `MAX_SEQLEN=16`；
- `historical_trace_facts`：上下文中某一阶段曾经成立的状态，例如 `26` 或 `912` 验证路径；
- `tool_evidence`：工具实际跑出来的 pass/fail 证据。

框架不能把这些事实静默合并。冲突必须进入 SACG，等待 checker 或 human decision 消解。

---

## 2. 顶层输入对象：Design Reproduction Package

建议框架读取一个顶层 JSON 文件：

```text
<run_dir>/input/input_package.json
```

顶层 schema 名称：

```text
spatialaccagent.input.v1
```

最小结构：

```json
{
  "schema_version": "spatialaccagent.input.v1",
  "run_id": "opt125m_reproduce_2026_06_24",
  "mode": "index_existing_code_and_replay_context",
  "objective": {
    "primary": "reproduce_real_accelerator_design_process",
    "secondary": ["surface_existing_code", "seed_sacg", "prepare_stagewise_framework"]
  },
  "source_of_truth": {
    "context_doc": "docs/context_2026-03-27.md",
    "codebase_root": ".",
    "git_revision": "73c930a",
    "conflict_policy": "record_context_target_and_code_fact_separately"
  },
  "refs": {
    "context_sources": "sources/context_sources.json",
    "codebase_manifest": "sources/codebase_manifest.json",
    "target_model": "model/target_model.json",
    "numeric_policy": "model/numeric_policy.json",
    "template_library": "templates/template_library.json",
    "pipeline_seed": "hardware/pipeline_seed.json",
    "current_param_inventory": "hardware/current_param_inventory.json",
    "top_io_contract": "hardware/top_io_contract.json",
    "verification_inputs": "verification/verification_inputs.json",
    "memory_runtime_layout": "runtime/memory_runtime_layout.json",
    "tool_protocols": "tools/tool_protocols.json",
    "reproduction_targets": "targets/reproduction_targets.json",
    "human_agent_boundary": "boundary/human_agent_boundary.json",
    "sacg_seed_rules": "sacg/sacg_seed_rules.json"
  }
}
```

`mode` 建议允许四类：

| mode | 作用 |
| --- | --- |
| `index_existing_code` | 只把当前代码、case、工具链索引进 SACG |
| `replay_context_trace` | 按上下文文档恢复历史设计闭环事件 |
| `regenerate_from_scratch` | 从 task/model/template 开始重新生成 artifact |
| `index_existing_code_and_replay_context` | 当前最需要的模式：同时对齐上下文过程和现有代码 |

---

## 3. 输入文件布局

建议一个 run 的输入目录为：

```text
<run_dir>/input/
  input_package.json
  sources/
    context_sources.json
    codebase_manifest.json
  model/
    target_model.json
    numeric_policy.json
  templates/
    template_library.json
  hardware/
    pipeline_seed.json
    current_param_inventory.json
    top_io_contract.json
  verification/
    verification_inputs.json
  runtime/
    memory_runtime_layout.json
    board_deployment.json
  tools/
    tool_protocols.json
  targets/
    reproduction_targets.json
  boundary/
    human_agent_boundary.json
  sacg/
    sacg_seed_rules.json
```

其中：

- `sources/` 说明事实来自哪里；
- `model/` 说明目标模型和数值策略；
- `templates/` 说明 agent 可以使用哪些可信模板；
- `hardware/` 说明当前代码结构、参数、顶层 IO；
- `verification/` 说明真实数据、golden、DDR case、window case；
- `runtime/` 说明 DDR/AXI/board/runtime layout；
- `tools/` 说明命令如何运行、如何判断 pass/fail；
- `targets/` 说明本次要复现到哪个层级；
- `boundary/` 说明哪些修复能自动做，哪些需要 human approval；
- `sacg/` 说明如何把以上输入转成 SACG。

---

## 4. `context_sources.json`

上下文输入用于恢复真实设计过程。

建议格式：

```json
{
  "context_doc": {
    "path": "docs/context_2026-03-27.md",
    "role": "design_closure_trace",
    "priority": "highest_for_process_reproduction"
  },
  "supporting_docs": [
    {
      "path": "docs/architecture.md",
      "role": "current_architecture_fact_doc"
    },
    {
      "path": "docs/opt_quan.md",
      "role": "numeric_policy_doc"
    },
    {
      "path": "docs/e2e_verification.md",
      "role": "verification_data_protocol_doc"
    },
    {
      "path": "accagent/docs/sacg.md",
      "role": "sacg_method_definition"
    },
    {
      "path": "accagent/docs/sacg_role_in_agent_framework.md",
      "role": "sacg_runtime_role_definition"
    }
  ],
  "extraction_policy": {
    "latest_context_sections_override_older_context_sections": true,
    "current_user_prompt_overrides_context": true,
    "do_not_treat_unverified_agent_guess_as_root_cause": true,
    "every_extracted_fact_requires_source_ref": true
  }
}
```

每条从上下文抽取的事实都应带 `source_ref`：

```json
{
  "fact_id": "trace.fact.remote_vcs_fullseq",
  "kind": "historical_trace_fact",
  "claim": "validate-9p-fullseq-vcs was used for remote full-seq system validation",
  "source_ref": {
    "path": "docs/context_2026-03-27.md",
    "section": "remote VCS fullseq validation"
  }
}
```

---

## 5. `codebase_manifest.json`

代码输入用于浮现当前仓库中的真实 artifact。

建议格式：

```json
{
  "repo_root": ".",
  "git_revision": "73c930a",
  "build": {
    "sbt_file": "build.sbt",
    "scala_version": "2.13.16",
    "chisel_version": "7.0.0"
  },
  "top": {
    "source": "src/main/scala/Top.scala",
    "module": "Top",
    "generator": "AttenTopGen",
    "generation_command": "sbt \"runMain AttenTopGen\"",
    "generated_outputs": [
      "generated/Top.sv",
      "generated/Top_vivado.sv",
      "deliverables/vivado_opt_acc_core_ip/hdl/Top_vivado.sv"
    ]
  },
  "system_wrappers": [
    "verification/rtl/NinePSystemTop.sv",
    "verification/rtl/AxiBoardSystemTop.sv",
    "verification/rtl/MigSystemTop.sv",
    "deliverables/vivado_opt_acc_core_ip/hdl/opt_acc_core.sv"
  ],
  "verification_scripts": [
    "scripts/verification/opt125m_e2e.py",
    "scripts/verification/remote_vcs.sh",
    "scripts/verification/remote_verilator.sh"
  ],
  "synthesis_scripts": [
    "scripts/synthesis/remote_fix_opt_acc_core_ooc_23.sh",
    "scripts/synthesis/resume_top_impl_23.tcl",
    "scripts/synthesis/launch_project_synth_23.tcl"
  ],
  "board_scripts": [
    "scripts/board/run_pyjm12_smoke.sh",
    "scripts/board/README_debug_regs.md"
  ]
}
```

这个文件不只列文件名，还要说明每个文件在 SACG 中属于哪类 artifact：

| artifact | SACG role |
| --- | --- |
| `src/main/scala/Top.scala` | top-level Chisel integration artifact |
| `src/main/scala/*/Param.scala` | hardware parameter source artifact |
| `verification/rtl/NinePSystemTop.sv` | DDR-only system wrapper artifact |
| `verification/rtl/AxiBoardSystemTop.sv` | board-style AXI wrapper artifact |
| `scripts/verification/opt125m_e2e.py` | data/case/checker/tool protocol artifact |
| `scripts/verification/remote_vcs.sh` | remote VCS execution artifact |
| `verification/cases/*/case.json` | verification case metadata artifact |
| `verification/cases/*/window.cfg` | runtime/config binding artifact |
| `scripts/synthesis/*.tcl` | backend closure artifact |
| `scripts/board/*.sh` | board deployment/runtime artifact |

---

## 6. `target_model.json`

目标模型输入描述设计目标，而不是当前代码已经做到什么。

当前项目建议至少记录：

```json
{
  "model_id": "opt125m_12layer",
  "family": "OPT",
  "scope": "decoder_block_and_12_layer_pipeline",
  "hidden_size": 768,
  "num_attention_heads": 12,
  "head_dim": 64,
  "ffn_hidden_size": 3072,
  "attention_type": "MHA",
  "layer_count_target": 12,
  "sequence_targets": [
    {
      "name": "short_sequence_acceptance",
      "tokens": 26,
      "source": "project_goal"
    },
    {
      "name": "full_sequence_acceptance",
      "tokens": 912,
      "source": "project_goal_and_case_json"
    },
    {
      "name": "current_code_short_sequence",
      "tokens": 16,
      "source": "current_param_inventory"
    }
  ],
  "semantic_constraints": [
    "do_not_change_model_semantics",
    "do_not_change_attention_type_without_approval",
    "do_not_change_layer_count_without_approval"
  ]
}
```

注意：`target_model.json` 不能被当前代码参数覆盖。当前代码参数应进入 `current_param_inventory.json`。

---

## 7. `numeric_policy.json`

数值策略输入必须同时记录文档策略和代码 IO 对应关系。

当用户没有提供定量比较阈值时，框架使用宽松默认值
`atol=0.1`、`rtol=0.1`、`max_mismatch_fraction=0.05`。用户明确提供的值逐项优先；
解析结果及其来源必须在仿真前冻结，且不得根据 DUT 输出动态放宽。

建议格式：

```json
{
  "policy_id": "opt125m_mixed_int8_fp32",
  "source_docs": ["docs/opt_quan.md"],
  "default_rules": {
    "weight_dtype": "int8",
    "activation_dtype": "mixed_int8_fp32",
    "accum_dtype": "int32_or_fp32_by_stage",
    "tolerance_policy": "must_come_from_numeric_policy_not_agent_guess"
  },
  "stages": [
    {
      "stage_id": "ln1",
      "op": "LayerNorm",
      "input_dtype": "fp32",
      "output_dtype": "int8",
      "top_io": ["ln1_out_inv_scale", "ln1_out_zero_point"]
    },
    {
      "stage_id": "qkv",
      "op": "QKVLinear",
      "input_dtype": "int8",
      "weight_dtype": "int8",
      "output_dtype": "int8",
      "top_io": [
        "q_out_inv_scale",
        "k_out_inv_scale",
        "v_out_inv_scale",
        "q_bias_scale",
        "k_bias_scale",
        "v_bias_scale"
      ]
    },
    {
      "stage_id": "dm1_softmax_dm2",
      "op": "Attention",
      "input_dtype": "int8",
      "internal_dtype": "fp32_or_quantized_context",
      "top_io": ["dm1_out_scale", "dm2_ctx_inv_scale", "dm2_ctx_zero_point", "dm2_out_inv_scale"]
    },
    {
      "stage_id": "out_linear",
      "op": "OutLinear",
      "input_dtype": "int8",
      "output_dtype": "fp32",
      "top_io": ["out_out_scale"]
    },
    {
      "stage_id": "ffn",
      "op": "FFNUp_FFNDown",
      "input_dtype": "int8",
      "output_dtype": "fp32",
      "top_io": ["ffnup_out_inv_scale", "ffnup_bias_scale", "ffndown_out_scale"]
    }
  ]
}
```

这个输入会生成 SACG 中的 `numeric` constraints。任何放宽 tolerance、修改 golden、修改 scale layout 的行为都必须被 SACG 标为 high-risk 或 forbidden。

---

## 8. `pipeline_seed.json`

流水输入用于把当前 `Top.scala` 中的真实模块连接浮现成 SACG node/edge。

建议格式：

```json
{
  "pipeline_id": "opt125m_current_top_pipeline",
  "source": "src/main/scala/Top.scala",
  "stages": [
    {
      "stage_id": "s0_ln_addr_gen",
      "module": "LNAddrGen",
      "source_files": ["src/main/scala/TempAdapter/LNAddrGen.scala", "src/main/scala/TempAdapter/Param.scala"],
      "role": "input_address_generation"
    },
    {
      "stage_id": "s1_ln1",
      "module": "LayerNormQ",
      "source_files": ["src/main/scala/LayerNormQ/LayerNormQ.scala", "src/main/scala/LayerNormQ/Param.scala"],
      "role": "layernorm1"
    },
    {
      "stage_id": "s2_qkv",
      "module": "QKVLinear",
      "source_files": ["src/main/scala/QKVLinear/QKVLinear.scala", "src/main/scala/QKVLinear/Param.scala"],
      "role": "qkv_projection"
    },
    {
      "stage_id": "s3_s6_attention",
      "module": "Atten",
      "source_files": [
        "src/main/scala/Attention.scala",
        "src/main/scala/DM/Top.scala",
        "src/main/scala/Softmax/Top.scala",
        "src/main/scala/DM2/Top.scala"
      ],
      "role": "attention"
    },
    {
      "stage_id": "s7_out_linear",
      "module": "OutLinearFP32",
      "source_files": ["src/main/scala/OutLinear/OutLinear.scala", "src/main/scala/OutLinear/Param.scala"],
      "role": "output_projection"
    },
    {
      "stage_id": "s7_resadd1",
      "module": "ResAddFP32",
      "source_files": ["src/main/scala/ResAdd/ResAddFP32.scala", "src/main/scala/ResAdd/FP32Param.scala"],
      "role": "residual_add_1"
    },
    {
      "stage_id": "s8_ln2",
      "module": "LayerNormQ",
      "source_files": ["src/main/scala/LayerNormQ/LayerNormQ.scala"],
      "role": "layernorm2"
    },
    {
      "stage_id": "s9_ffn_up",
      "module": "FFNUp",
      "source_files": ["src/main/scala/FFNUp/FFNUp.scala", "src/main/scala/FFNUp/Param.scala"],
      "role": "ffn_up_relu"
    },
    {
      "stage_id": "s10_ffn_down",
      "module": "FFNDownFP32",
      "source_files": ["src/main/scala/FFNDown/FFNDownFP32.scala", "src/main/scala/FFNDown/Param.scala"],
      "role": "ffn_down"
    },
    {
      "stage_id": "s11_resadd2",
      "module": "ResAdd2FP32",
      "source_files": ["src/main/scala/ResAdd2/ResAdd2FP32.scala", "src/main/scala/ResAdd2/FP32Param.scala"],
      "role": "residual_add_2"
    }
  ],
  "edges": [
    {
      "edge_id": "edge.ln1_to_qkv",
      "src": "s1_ln1",
      "dst": "s2_qkv",
      "protocol": "valid_ready_st_last_addr"
    },
    {
      "edge_id": "edge.qkv_to_attention",
      "src": "s2_qkv",
      "dst": "s3_s6_attention",
      "protocol": "queue_depth_2_valid_ready_head_addr_last"
    },
    {
      "edge_id": "edge.attention_to_out_linear",
      "src": "s3_s6_attention",
      "dst": "s7_out_linear",
      "protocol": "queue_depth_head_num"
    },
    {
      "edge_id": "edge.out_linear_to_resadd1",
      "src": "s7_out_linear",
      "dst": "s7_resadd1",
      "protocol": "queue_depth_res_mem_depth"
    },
    {
      "edge_id": "edge.resadd1_to_ln2_and_resadd2",
      "src": "s7_resadd1",
      "dst": "s8_ln2",
      "protocol": "fork_with_backpressure"
    },
    {
      "edge_id": "edge.ffn_down_to_resadd2",
      "src": "s10_ffn_down",
      "dst": "s11_resadd2",
      "protocol": "queue_depth_res_mem_depth"
    }
  ]
}
```

这些 edge 会直接生成 stream、beat、liveness、residual alignment constraints。

---

## 9. `current_param_inventory.json`

参数输入用于记录当前代码事实，并给后续参数绑定、checker 和修复提供来源。

建议每个参数都记录：

```json
{
  "param_id": "qkv.MAX_SEQLEN",
  "module": "QKVLinear",
  "source_file": "src/main/scala/QKVLinear/Param.scala",
  "symbol": "MAX_SEQLEN",
  "value": 16,
  "unit": "tokens",
  "constraint_classes": ["shape", "memory", "beat"],
  "status": "current_code_fact"
}
```

当前最需要记录的参数摘要如下：

| module | key params from current code |
| --- | --- |
| `LayerNormQ` | `VECTOR=768`, `LANE_NUM/SUBVEC=12`, `VECTOR_BEATS=64`, `BATCHSIZE=16`, `MEM_DEPTH=2048` |
| `TempAdapter` | `HEAD_DIM=64`, `LOAD_VECNUM=2`, `BATCHSIZE=16`, `MAX_SEQLEN=16`, `COLLECT_NUM=64`, `OUTPUT_NUM=32` |
| `QKVLinear` | `DATAW=8`, `BATCHSIZE=16`, `MAX_SEQLEN=16`, `ROW=12`, `COL=36`, `ROW_W=768`, `COL_W=2304`, `ROWBLOCK=64`, `COLBLOCK=64`, `MEM_WIDTH=96`, `WMEM_WIDTH=288`, `WMEM_DEPTH=49152`, `HEAD_NUM=12`, `HEAD_DIM=64` |
| `DM1` | `SINGLE_QUERY_BATCH=12`, `LBANCHNUM=4`, `LBATCHSIZE=48`, `LOAD_VECNUM=2`, `HEAD_VECNUM=64`, `MAX_SEQLEN=16`, `TILE_SEQLEN=16`, `MULNUM=32`, `MEM_DEPTH=512` |
| `Softmax` | `SINGLE_QUERY_BATCH=12`, `BATCHSIZE=12`, `TILE_SEQLEN=16`, `MEM_WIDTH=128`, `MEM_DEPTH=2048`, `WMEM_WIDTH=16`, `WMEM_DEPTH=2048` |
| `DM2` | `SINGLE_QUERY_BATCH=12`, `BATCHSIZE=12`, `LBATCHSIZE=48`, `HEAD_VECNUM=64`, `MAX_SEQLEN=16`, `TILE_SEQLEN=16`, `MULNUM=32`, `MEM_DEPTH=12` |
| `OutLinear` | `DATAW=8`, `BATCHSIZE=16`, `ROW=12`, `COL=36`, `ROW_W=768`, `COL_W=768`, `COLBLOCK=22`, `WMEM_DEPTH=16896`, `HEAD_NUM=12`, `HEAD_DIM=64` |
| `ResAdd` | `SUBVEC=12`, `VECTOR=768`, `BATCHSIZE=16`, `MAX_SEQLEN=16`, `COLLECT_NUM=64`, `MEM_DEPTH=1024` in int8 param, FP32 mem depth from `FP32Param` |
| `FFNUp` | `DATAW=8`, `BATCHSIZE=16`, `ROW=12`, `COL=36`, `ROW_W=768`, `COL_W=3072`, `ROWBLOCK=64`, `COLBLOCK=86`, `WMEM_DEPTH=66048` |
| `FFNDown` | `DATAW=8`, `BATCHSIZE=16`, `ROW=12`, `COL=36`, `ROW_W=3072`, `COL_W=768`, `ROWBLOCK=256`, `COLBLOCK=22`, `WMEM_DEPTH=67584` |
| `ResAdd2` | `SUBVEC=12`, `BATCHSIZE=16`, `MAX_SEQLEN=16`, `MEM_DEPTH=2048` |

参数输入必须支持 `derived_from`：

```json
{
  "param_id": "qkv.WMEM_DEPTH",
  "symbol": "WMEM_DEPTH",
  "value": 49152,
  "derived_from": "ROW * ROWBLOCK * COLBLOCK",
  "source_file": "src/main/scala/QKVLinear/Param.scala"
}
```

这会让 agent 能在修改 `ROW/COL/COL_W` 时知道哪些派生参数和 memory layout 需要同步更新。

---

## 10. `top_io_contract.json`

顶层 IO 输入用于把 `Top.scala` 的跨层接口显式化。

建议按类别记录：

```json
{
  "top_module": "Top",
  "source": "src/main/scala/Top.scala",
  "io_groups": [
    {
      "group": "control",
      "signals": ["layer_st", "cfg_seqlen", "cfg_prefill", "cfg_valid"]
    },
    {
      "group": "attention_long_seq_control",
      "signals": ["attn_cfg_seqlen", "attn_cfg_prefill", "attn_cfg_valid", "attn_cfg_single_query"]
    },
    {
      "group": "weight_double_buffer",
      "signals": ["weight_init_mode", "weight_active_bank", "weight_preload_bank"]
    },
    {
      "group": "qkv_weight_preload",
      "signals": ["qkv_w_addr", "qkv_w_preload_valid", "qkv_w_preload_addr", "qkv_w_preload_data"]
    },
    {
      "group": "long_seq_history_tap_override",
      "signals": [
        "attn_tap_data",
        "attn_tap_head",
        "attn_tap_addr",
        "attn_tap_valid",
        "attn_tap_last",
        "attn_dm1_override_enable",
        "attn_dm2_v_override_enable"
      ]
    },
    {
      "group": "output_stream",
      "signals": ["res", "res_st", "res_addr", "res_valid", "res_last", "res_ready"]
    }
  ]
}
```

这个文件是后续 wrapper/runtime/checker 的桥。没有它，agent 很容易只改 `Top.scala` 内部逻辑，却忘记同步 `NinePSystemTop`、`AxiBoardSystemTop`、testbench、case builder 和 host runtime。

---

## 11. `template_library.json`

模板输入定义 agent 能使用的 trusted code surface。

建议格式：

```json
{
  "library_id": "qwen2_accelerator_current_chisel_templates",
  "policy": {
    "free_form_rtl_generation": false,
    "template_internal_rewrite_requires_approval": true,
    "parameter_binding_allowed": true,
    "top_connection_allowed": true
  },
  "templates": [
    {
      "template_id": "template.layernormq",
      "name": "LayerNormQ",
      "source_files": ["src/main/scala/LayerNormQ/LayerNormQ.scala", "src/main/scala/LayerNormQ/Param.scala"],
      "supported_ops": ["layernorm_quantized"],
      "required_constraints": ["shape.hidden_768", "numeric.ln_quant", "stream.vector_64_beats"]
    },
    {
      "template_id": "template.qkv_linear",
      "name": "QKVLinear",
      "source_files": ["src/main/scala/QKVLinear/QKVLinear.scala", "src/main/scala/QKVLinear/Param.scala"],
      "supported_ops": ["qkv_projection_mha"],
      "required_constraints": ["shape.qkv_768_to_2304", "numeric.qkv_int8", "memory.qkv_weight_layout"]
    },
    {
      "template_id": "template.attention",
      "name": "Atten",
      "source_files": ["src/main/scala/Attention.scala", "src/main/scala/DM/Top.scala", "src/main/scala/Softmax/Top.scala", "src/main/scala/DM2/Top.scala"],
      "supported_ops": ["mha_attention"],
      "required_constraints": ["stream.qkv_order", "memory.kv_history", "beat.attention_output"]
    }
  ]
}
```

后续应为每个 template 增加单独 `template_spec`，包含：

- supported op；
- parameter list；
- IO protocol；
- stream order；
- memory layout；
- numeric policy；
- latency/II 估计；
- allowed edits；
- required checkers。

---

## 12. `verification_inputs.json`

验证输入必须覆盖 stage、top、system、board-style AXI 几层。

建议格式：

```json
{
  "stage_manifest": {
    "path": "scripts/verification/opt125m_stage_manifest.json",
    "case_name": "opt125m_stage_dataset",
    "source_roots": ["weight", "verification/cases/opt125m_stage_full"]
  },
  "case_dirs": [
    {
      "case_id": "opt125m_stage_full",
      "path": "verification/cases/opt125m_stage_full",
      "role": "stage_level_real_data"
    },
    {
      "case_id": "opt125m_9p_fullseq",
      "path": "verification/cases/opt125m_9p_fullseq",
      "role": "single_layer_fullseq_ddr_case",
      "case_json": "verification/cases/opt125m_9p_fullseq/case.json"
    },
    {
      "case_id": "pyjm12_alllayers_9p_fullseq",
      "path": "verification/cases/pyjm12_alllayers_9p_fullseq",
      "role": "12_layer_all_layers_case",
      "case_json": "verification/cases/pyjm12_alllayers_9p_fullseq/case.json"
    }
  ],
  "checkers": [
    "shape_check",
    "numeric_check",
    "stream_trace_check",
    "beat_count_check",
    "addr_map_check",
    "deadlock_timeout_check",
    "regression_check"
  ]
}
```

`scripts/verification/opt125m_stage_manifest.json` 中的 label/alias 也必须保留，例如：

- `layernorm1.input/gamma/beta/output`；
- `qkv_proj.q_weight/k_weight/v_weight`；
- `qkv_proj.v_weight_scale` 使用 `k_weight_scale` 的第二个 occurrence；
- `fc1.output`、`fc2.input/output` 使用 tensor occurrence 和 shape occurrence；
- `res_add2` 的 `fc2_output/res_add1_output/output`。

这些细节属于 data extraction constraints。丢掉这些 label 规则，agent 就无法复现真实数据 case。

---

## 13. `memory_runtime_layout.json`

memory/runtime 输入记录 DDR image、AXI 地址、runtime config 和 board register map。

当前 `verification/cases/opt125m_9p_fullseq/case.json` 已经给出一组真实 DDR case fact：

```json
{
  "board_model": "9p-ddr-only",
  "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
  "token_count_full": 912,
  "ddr_word_width_bits": 512,
  "ddr_u32_words_per_beat": 16,
  "ddr_total_beats": 258906,
  "board_axi_c0_window_base_addr": 2147483648,
  "board_axi_c1_window_base_addr": 4294967296
}
```

其中 DDR regions 必须作为 memory constraints：

```json
{
  "regions": [
    { "name": "input", "ddr_base_addr": 0 },
    { "name": "ln1_w", "ddr_base_addr": 58368 },
    { "name": "qkv_w", "ddr_base_addr": 58496 },
    { "name": "qkv_b", "ddr_base_addr": 107648 },
    { "name": "sm", "ddr_base_addr": 107840 },
    { "name": "out_w", "ddr_base_addr": 107866 },
    { "name": "out_b", "ddr_base_addr": 124762 },
    { "name": "ln2_w", "ddr_base_addr": 124826 },
    { "name": "ffnup_w", "ddr_base_addr": 124954 },
    { "name": "ffnup_b", "ddr_base_addr": 191002 },
    { "name": "ffndown_w", "ddr_base_addr": 191258 },
    { "name": "ffndown_b", "ddr_base_addr": 258842 }
  ]
}
```

`pyjm12_alllayers_9p_fullseq/case.json` 则必须记录为 12 层 case fact：

```json
{
  "board_model": "9p-ddr-only",
  "source_mode": "all_layers_raw",
  "layer_count": 12,
  "layer_stride_beats": 200540
}
```

board 输入还应记录：

- control base；
- DDR base；
- XDMA id；
- output absolute address；
- debug register behavior；
- smoke run script；
- `PYJM_SUDO_PASSWORD` 只通过环境变量，不写入仓库。

这些会生成 `memory`、`runtime`、`deployment` constraints。

---

## 14. `tool_protocols.json`

工具输入把命令变成可复用协议，而不是散落在上下文里的命令字符串。

建议格式：

```json
{
  "tools": [
    {
      "tool_id": "generate_top_sv",
      "kind": "chisel_generation",
      "command_template": "sbt \"runMain AttenTopGen\"",
      "inputs": ["src/main/scala/Top.scala", "src/main/scala/*/Param.scala"],
      "outputs": ["generated/Top.sv", "generated/Top_vivado.sv"],
      "pass_condition": ["exit_code == 0", "generated/Top.sv exists"],
      "related_constraints": ["artifact.generation", "backend.vivado_compat"]
    },
    {
      "tool_id": "prepare_case",
      "kind": "data_generation",
      "command_template": "python scripts/verification/opt125m_e2e.py prepare-case <manifest> --out-dir <case_dir>",
      "inputs": ["scripts/verification/opt125m_stage_manifest.json", "weight/*.json"],
      "outputs": ["verification/cases/opt125m_stage_full"],
      "pass_condition": ["exit_code == 0", "case artifacts generated"]
    },
    {
      "tool_id": "validate_9p_fullseq_vcs",
      "kind": "remote_system_verification",
      "command_template": "./scripts/verification/remote_vcs.sh validate-9p-fullseq-vcs --skip-prepare",
      "inputs": ["generated/Top.sv", "verification/rtl/NinePSystemTop.sv", "verification/cases/opt125m_9p_fullseq"],
      "pass_condition": ["exit_code == 0", "testbench reports PASS"],
      "failure_patterns": ["timeout", "missing beat", "output mismatch", "wrong address"]
    },
    {
      "tool_id": "validate_axi_board_fullseq_vcs",
      "kind": "remote_board_style_axi_verification",
      "command_template": "./scripts/verification/remote_vcs.sh validate-axi-board-fullseq-vcs --skip-prepare",
      "inputs": ["verification/rtl/AxiBoardSystemTop.sv", "testbench/vcs/axiboardsystemtop_tb.sv"],
      "pass_condition": ["exit_code == 0", "AXI wrapper testbench reports PASS"]
    },
    {
      "tool_id": "board_smoke",
      "kind": "board_runtime",
      "command_template": "scripts/board/run_pyjm12_smoke.sh",
      "inputs": ["DDR image", "bitstream", "debug register map"],
      "pass_condition": ["start accepted", "done observed", "valid output bytes read"]
    }
  ]
}
```

每个 tool protocol 都必须绑定：

- 输入 artifact；
- 输出 artifact；
- pass/fail 条件；
- failure patterns；
- related constraints；
- 失败后应该调用的 checker 或 classifier。

---

## 15. `reproduction_targets.json`

复现目标输入决定本轮 run 要跑到哪个闭环层级。

建议按层级定义：

```json
{
  "targets": [
    {
      "level": "L0",
      "name": "index_current_code",
      "success": "current codebase artifacts are indexed into SACG"
    },
    {
      "level": "L1",
      "name": "regenerate_top_rtl",
      "success": "sbt runMain AttenTopGen regenerates Top.sv and Top_vivado.sv"
    },
    {
      "level": "L2",
      "name": "prepare_real_data_cases",
      "success": "stage/fullseq DDR cases are generated or validated"
    },
    {
      "level": "L3",
      "name": "stage_and_top_verification",
      "success": "stage-level and top-level checkers pass on real data"
    },
    {
      "level": "L4",
      "name": "system_and_board_style_axi_verification",
      "success": "remote VCS system or AXI-board validation passes"
    },
    {
      "level": "L5",
      "name": "backend_and_board_closure",
      "success": "Vivado reports and board smoke evidence are attached"
    }
  ],
  "current_run_target": "L0"
}
```

当前框架下一步最现实的目标应是 `L0 -> L1`：

1. 读取 Design Reproduction Package；
2. 自动建立 SACG seed；
3. 索引当前代码 artifact；
4. 跑 `sbt "runMain AttenTopGen"` 或至少声明其 tool protocol；
5. 将生成结果和 evidence 回写 SACG。

---

## 16. `human_agent_boundary.json`

人机边界输入来自已经定义好的人机分工文档。

建议格式：

```json
{
  "auto_allowed_repairs": [
    "signal_connection",
    "parameter_sync",
    "script_path",
    "trace_parser",
    "wrapper_runtime_sync",
    "valid_delay",
    "address_offset",
    "ddr_image_regen",
    "small_fifo_depth",
    "regression_rerun"
  ],
  "approval_required": [
    "pipeline_stage_change",
    "tile_size_change",
    "parallelism_change",
    "memory_layout_change",
    "data_packing_change",
    "numeric_policy_change",
    "major_template_rewrite",
    "timing_pipeline_stage",
    "axi_ddr_access_change",
    "major_buffer_structure"
  ],
  "forbidden": [
    "delete_failing_test",
    "modify_golden_to_pass",
    "loosen_tolerance_without_approval",
    "change_model_semantics",
    "bypass_checker",
    "mark_failed_regression_pass",
    "claim_root_cause_without_evidence"
  ]
}
```

这个输入必须被 SACG runtime 强制执行。当前 `accagent/framework/runtime/store.py` 已经实现了对应的 repair scope gate。

---

## 17. `sacg_seed_rules.json`

SACG seed 输入定义如何把 Design Reproduction Package 转成图。

建议格式：

```json
{
  "node_rules": [
    {
      "from": "target_model.semantic_constraints",
      "node_type": "model_op"
    },
    {
      "from": "template_library.templates",
      "node_type": "template"
    },
    {
      "from": "pipeline_seed.stages",
      "node_type": "pipeline_stage"
    },
    {
      "from": "verification_inputs.checkers",
      "node_type": "verification_task"
    },
    {
      "from": "tool_protocols.tools[kind=synthesis]",
      "node_type": "backend_task"
    },
    {
      "from": "tool_protocols.tools[kind=board_runtime]",
      "node_type": "deployment_task"
    }
  ],
  "edge_rules": [
    {
      "from": "pipeline_seed.edges",
      "edge_type": "stream"
    },
    {
      "from": "memory_runtime_layout.regions",
      "edge_type": "memory"
    },
    {
      "from": "top_io_contract.io_groups",
      "edge_type": "runtime_control"
    }
  ],
  "constraint_classes": [
    "shape",
    "numeric",
    "stream",
    "beat",
    "memory",
    "runtime",
    "liveness",
    "backend",
    "deployment"
  ],
  "artifact_binding_rules": [
    {
      "artifact_glob": "src/main/scala/**/*.scala",
      "bind_to": ["template", "pipeline_stage", "shape", "numeric", "stream"]
    },
    {
      "artifact_glob": "verification/cases/**",
      "bind_to": ["verification_task", "memory", "numeric", "golden_data"]
    },
    {
      "artifact_glob": "scripts/verification/**",
      "bind_to": ["tool_protocol", "checker", "runtime"]
    },
    {
      "artifact_glob": "scripts/synthesis/**",
      "bind_to": ["backend_task"]
    },
    {
      "artifact_glob": "scripts/board/**",
      "bind_to": ["deployment_task", "runtime"]
    }
  ]
}
```

SACG seed 的关键规则：

```text
每个 graph fact 必须有 source_ref。
每个 artifact 必须绑定到至少一个 node 或 constraint。
每个 transition 必须声明 touched constraints。
每个 checker evidence 必须回写到 invariant。
每个 conflict 必须保留，不允许 agent 静默覆盖。
```

---

## 18. 输入事实冲突的格式

当前项目一定会遇到上下文目标和当前代码事实不一致的问题。建议统一记录为：

```json
{
  "conflict_id": "conflict.seq_length.current_code_vs_target",
  "topic": "sequence_length",
  "facts": [
    {
      "fact_id": "target.fullseq.912",
      "kind": "target_behavior",
      "value": 912,
      "source_ref": "project_goal_and_opt125m_9p_fullseq_case_json"
    },
    {
      "fact_id": "code.qkv.max_seqlen.16",
      "kind": "current_code_fact",
      "value": 16,
      "source_ref": "src/main/scala/QKVLinear/Param.scala"
    },
    {
      "fact_id": "script.current_core_max_seqlen.26",
      "kind": "historical_script_fact",
      "value": 26,
      "source_ref": "scripts/verification/opt125m_e2e.py"
    }
  ],
  "status": "open",
  "resolution_policy": "do_not_modify_architecture_without_human_approval",
  "required_checker_or_decision": "human_select_reproduction_target_or_agent_index_current_code_only"
}
```

这类 conflict 是 SACG 的重要价值：它让 agent 明确知道哪里是目标和现状的差距，而不是假装已经支持 912。

---

## 19. 最小可执行输入 vs 完整复现输入

单次运行最小输入仍然可以是 task card：

```json
{
  "task_name": "opt125m_fpga_accelerator",
  "target_model": "model/target_model.json",
  "target_platform": "runtime/board_deployment.json",
  "numeric_policy": "model/numeric_policy.json",
  "template_library": "templates/template_library.json",
  "design_goal": "functional_closure"
}
```

但这个最小输入只够启动 agent，不够复现当前真实工程。

对于本项目，真正可用的框架输入必须至少包含：

1. `context_sources.json`
2. `codebase_manifest.json`
3. `target_model.json`
4. `numeric_policy.json`
5. `template_library.json`
6. `pipeline_seed.json`
7. `current_param_inventory.json`
8. `top_io_contract.json`
9. `verification_inputs.json`
10. `memory_runtime_layout.json`
11. `tool_protocols.json`
12. `reproduction_targets.json`
13. `human_agent_boundary.json`
14. `sacg_seed_rules.json`

---

## 20. 对当前框架开发的直接要求

基于上述输入规范，后续框架应按阶段补齐：

### Stage 0: Input Loader

读取 `input_package.json`，校验所有 ref 文件存在，并生成初始 run directory。

### Stage 1: Codebase Indexer

读取 `codebase_manifest.json`、`current_param_inventory.json`、`top_io_contract.json`，把当前代码 artifact 写入 SACG。

### Stage 2: Context Trace Extractor

从 `context_sources.json` 中抽取 design closure events，形成 trace records，并与当前代码 artifact 绑定。

### Stage 3: SACG Seeder

根据 `sacg_seed_rules.json` 生成 nodes、edges、constraints、invariants、artifacts。

### Stage 4: Tool Protocol Binder

把 `tool_protocols.json` 中的命令绑定到 verification/backend/deployment nodes。

### Stage 5: Reproduction Runner

按 `reproduction_targets.json` 从 L0 开始逐级执行：

```text
index current code
-> regenerate Top.sv
-> prepare real data case
-> run checker
-> attach evidence
-> promote/reject transition
```

每一步都必须通过 SACG transition。

---

## 21. 一句话总结

SpatialAccAgent 当前需要的输入不是“请设计一个加速器”这样的自然语言，也不只是一个 task card，而是一个能同时承载 **上下文过程、当前代码事实、真实验证数据、工具协议、平台部署和 SACG seed 规则** 的 Design Reproduction Package。

只有这样，框架才能做到两件事：

```text
从 context_2026-03-27.md 复现真实设计闭环；
从当前仓库代码浮现真实 accelerator artifact 和跨层约束。
```
