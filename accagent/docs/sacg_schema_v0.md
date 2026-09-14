# SACG Schema v0

本文档定义第一版可落地的 Spatial Accelerator Contract Graph schema。目标不是一次性覆盖所有细节，而是先让 SACG 可以被 checker、artifact builder、verification harness 和 repair log 共同引用。

## 设计原则

SACG v0 必须满足：

1. 能表达 decoder-only Transformer block 的主要算子和空间流水结构；
2. 每个 node/edge 都有稳定 ID，方便 trace、checker、repair log 回指；
3. 合同分层清楚：model、shape、numeric、stream、memory、liveness、deployment；
4. artifact 必须绑定到 graph，而不是只存在文件系统里；
5. checker 结果和 repair 结果必须能回写到 graph。

## 顶层结构

建议用 YAML 或 JSON 表示。YAML 更适合人工阅读，JSON 更适合工具处理。v0 可以先维护 YAML，再由工具转 JSON。

```yaml
sacg_version: 0.1
design_id: opt_block_w8a8_v0
target:
  model_family: OPT
  block_style: opt_gpt2
  sequence_length: 912
  batch_size: 1
  precision: W8A8
  platform: VU9P
  clock_target_mhz: 100

nodes: []
edges: []
contracts: {}
invariants: []
artifacts: []
check_reports: []
repair_records: []
```

## Node schema

Node 表示设计实体。v0 中 node 类型只保留必要集合：

- `model_op`：模型算子；
- `pu`：processing unit；
- `pipeline_stage`：流水级；
- `memory_task`：DDR/on-chip memory task；
- `runtime_task`：host/runtime task；
- `verification_task`：testbench 或验证任务；
- `deployment_task`：synthesis/implementation/board task。

示例：

```yaml
- id: node.qkv
  type: pu
  name: QKVLinear
  op: qkv_projection
  stage_index: 2
  template: templates.linear_int8
  contracts:
    model: contract.model.qkv
    shape: contract.shape.qkv
    numeric: contract.numeric.qkv
    stream_out: contract.stream.qkv_to_attn
  artifacts:
    - artifact.chisel.qkv
    - artifact.trace.qkv_stage
```

必须字段：

- `id`
- `type`
- `name`

推荐字段：

- `op`
- `stage_index`
- `template`
- `contracts`
- `artifacts`

## Edge schema

Edge 表示 node 之间的 contract-bearing relationship。

Edge 类型：

- `stream`
- `memory`
- `control`
- `residual`
- `kv_cache`
- `deployment`

示例：

```yaml
- id: edge.qkv_to_attn
  type: stream
  src: node.qkv
  dst: node.attn
  contracts:
    shape: contract.shape.qkv_to_attn
    stream: contract.stream.qkv_to_attn
    numeric: contract.numeric.qkv_to_attn
  artifacts:
    - artifact.trace.qkv_to_attn
```

必须字段：

- `id`
- `type`
- `src`
- `dst`

## Contract schema

Contracts 使用 map 存储，key 是 contract ID。

### Model contract

```yaml
contract.model.attn_gqa:
  type: model
  op: attention
  hidden_size: 896
  num_heads: 14
  num_kv_heads: 2
  head_dim: 64
  mapping:
    query_head_to_kv_head: floor_div
  mask: causal
  rope:
    enabled: true
    layout: interleaved_even_odd
```

### Shape contract

```yaml
contract.shape.qkv:
  type: shape
  inputs:
    x:
      shape: [batch, seq, hidden]
      dtype: int8
      layout: token_major
  outputs:
    q:
      shape: [batch, seq, num_heads, head_dim]
      dtype: int8
    k:
      shape: [batch, seq, num_kv_heads, head_dim]
      dtype: int8
    v:
      shape: [batch, seq, num_kv_heads, head_dim]
      dtype: int8
  tile:
    lane: 12
    beat_order: token_head_lane
```

### Numeric contract

```yaml
contract.numeric.qkv:
  type: numeric
  activation_dtype: int8
  weight_dtype: int8
  accumulation_dtype: int32
  output_dtype: int8
  scales:
    q: artifact.scale.q
    k: artifact.scale.k
    v: artifact.scale.v
  zero_points:
    input: 0
    output: 0
  rounding: nearest_even
  saturation: int8
  tolerance:
    kind: int_abs
    value: 2
```

### Stream contract

```yaml
contract.stream.qkv_to_attn:
  type: stream
  protocol: ready_valid
  fields:
    data: true
    valid: true
    ready: true
    st: true
    last: true
    addr: true
  order:
    - token
    - head
    - beat
    - lane
  beat_count:
    expression: seq * num_heads * beats_per_head
  st_rule: first_beat_per_token_head
  last_rule: last_beat_per_token_head
```

### Memory contract

```yaml
contract.memory.ddr_weights:
  type: memory
  space: ddr
  data_width_bits: 512
  regions:
    - name: qkv_weight
      base: 0x00000000
      size_bytes: 1048576
      packing: qkv_interleaved_u32
      alignment_bytes: 64
    - name: out_weight
      base: 0x00100000
      size_bytes: 524288
      packing: row_major_u32
      alignment_bytes: 64
  checks:
    disjoint_regions: true
    coverage_required: true
```

### Liveness contract

```yaml
contract.liveness.top:
  type: liveness
  max_cycles_per_token: 200000
  max_stall_cycles:
    qkv_to_attn: 4096
    attn_to_out: 8192
  fifo_occupancy:
    edge.qkv_to_attn:
      min: 0
      max: 32
```

### Deployment contract

```yaml
contract.deployment.board_runtime:
  type: deployment
  top_io: artifact.top_io
  ddr_map: contract.memory.ddr_weights
  runtime_config: artifact.window_cfg
  host_buffers:
    input: ddr_input_base
    output: ddr_output_base
  board:
    name: VU9P
    interface: XDMA
```

## Artifact schema

Artifact 需要绑定到 node/edge/contract。

```yaml
- id: artifact.chisel.qkv
  type: chisel
  path: src/main/scala/QKVLinear/QKVLinear.scala
  binds:
    - node.qkv
    - contract.numeric.qkv

- id: artifact.trace.qkv_stage
  type: trace
  path: verification/results/qkv_trace.csv
  format: stream_trace_v0
  binds:
    - edge.qkv_to_attn

- id: artifact.ddr_image
  type: ddr_image
  path: verification/cases/opt_block/artifacts/ddr_image.u32.bin
  binds:
    - contract.memory.ddr_weights
```

Artifact 类型 v0：

- `chisel`
- `generated_rtl`
- `testbench`
- `trace`
- `golden`
- `ddr_image`
- `config`
- `script`
- `synthesis_report`
- `board_log`

## Invariant schema

Invariant 是 checker 要验证的目标。

```yaml
- id: inv.qkv_shape
  type: shape
  contracts:
    - contract.shape.qkv
  checker: sacc-lint
  severity: error

- id: inv.qkv_to_attn_stream_order
  type: stream_order
  contracts:
    - contract.stream.qkv_to_attn
  checker: stream-trace-check
  severity: error

- id: inv.ddr_regions_disjoint
  type: memory_layout
  contracts:
    - contract.memory.ddr_weights
  checker: addr-map-check
  severity: error
```

Severity v0：

- `error`：必须修复；
- `warning`：可以继续，但必须记录；
- `info`：用于报告和统计。

## Checker report schema

```yaml
- id: report.0007
  checker: stream-trace-check
  invariant: inv.qkv_to_attn_stream_order
  status: fail
  evidence:
    trace: artifact.trace.qkv_stage
    first_violation:
      cycle: 12800
      expected: {token: 0, head: 1, beat: 0}
      observed: {token: 1, head: 0, beat: 0}
  candidate_contract:
    - contract.stream.qkv_to_attn
  timestamp: 2026-06-21T00:00:00Z
```

Status：

- `pass`
- `fail`
- `unknown`
- `not_run`

## Repair record schema

```yaml
- id: repair.0012
  symptom: top-level attention output mismatch
  failure_class: stream_order_mismatch
  evidence:
    - report.0007
  violated_contract:
    - contract.stream.qkv_to_attn
  affected_nodes:
    - node.qkv
    - node.attn
  affected_artifacts:
    - artifact.chisel.qkv
  patch:
    description: adjust QKV output reorder buffer to token-head-beat order
    files:
      - src/main/scala/QKVLinear/QKVLinear.scala
  regression:
    tasks:
      - verify.qkv_stage
      - verify.top_attention
    result: pass
  decision: keep
```

## v0 范围边界

v0 先不追求：

- 自动证明所有 invariant；
- 覆盖完整多层 LLM；
- 表达所有 possible tensor layout；
- 完成复杂 theorem proving。

v0 必须做到：

- 能描述一个 decoder block；
- 能绑定 Chisel、trace、DDR image、verification task；
- 能支持至少 shape、stream、beat-count、memory、numeric 五类 checker；
- 能记录 repair 并回指到 violated contract。
