# Checker Spec v0

本文档定义 SACG v0 对应的最小 checker suite。目标是让 SACG 不是静态 schema，而是能产生可量化证据的 EDA artifact。

## 总体原则

每个 checker 都必须：

1. 读取 SACG；
2. 读取必要 artifacts，例如 trace、DDR image、golden、config；
3. 输出结构化 `CheckerReport`；
4. report 中必须回指到 invariant、contract、node/edge、artifact；
5. 能用于 ablation / fault injection 的统计指标。

## CheckerReport 通用格式

```yaml
id: report.stream.0001
checker: stream-trace-check
status: fail
severity: error
invariant: inv.qkv_to_attn_stream_order
contracts:
  - contract.stream.qkv_to_attn
nodes:
  - node.qkv
  - node.attn
edges:
  - edge.qkv_to_attn
artifacts:
  - artifact.trace.qkv_to_attn
evidence:
  first_violation: {}
metrics: {}
recommendation:
  failure_class: stream_order_mismatch
  repair_hint: adjust producer order or insert reorder buffer
```

`status` 可取：

- `pass`
- `fail`
- `unknown`
- `not_run`

## 1. `sacc-lint`

### 目的

静态检查 SACG 自身是否合法，并检查 model/shape/numeric contract 的基本一致性。

### 输入

- SACG YAML/JSON；
- 可选 model config，例如 hidden size、num heads、num kv heads。

### 检查内容

Schema 检查：

- node/edge/contract/artifact ID 唯一；
- edge 的 `src` / `dst` 存在；
- artifact 绑定对象存在；
- invariant 引用的 checker 存在。

Shape 检查：

- hidden size 能被 head count 整除；
- GQA/MQA 下 `num_heads % num_kv_heads == 0`；
- Q/K/V head_dim 一致；
- producer output shape 与 consumer input shape 兼容；
- tile/lane/beat_count 表达式可解析。

Numeric 检查：

- dtype 合法；
- scale artifact 存在；
- bias domain 与 accumulation/output dtype 兼容；
- tolerance 类型与 dtype 匹配。

### 输出 metrics

- `num_nodes`
- `num_edges`
- `num_contracts`
- `num_schema_errors`
- `num_shape_errors`
- `num_numeric_errors`

### 可抓的典型问题

- GQA KV-head 映射维度不合法；
- hidden/head/head_dim 不一致；
- output dtype 和 tolerance 不匹配；
- artifact 没有绑定到任何 contract；
- verification task 引用不存在的 golden。

### 抓不到的问题

- cycle-level missing beat；
- 实际 RTL 地址生成错误；
- timing violation；
- 数值近似误差过大。

## 2. `stream-trace-check`

### 目的

检查 producer/consumer stream order 是否满足 stream contract。

### 输入

- SACG；
- stream contract；
- producer trace；
- consumer trace，可选；
- trace format spec。

### Trace v0 格式

CSV 或 JSONL 均可。最小字段：

```text
cycle,valid,ready,fire,st,last,addr,token,head,beat,lane,data_hash
```

其中：

- `fire = valid && ready`；
- `data_hash` 用于不暴露大规模 data 的轻量比较；
- `token/head/beat/lane` 可以由 checker 根据 `addr` 和 contract 反推，也可以由 trace 直接给出。

### 检查内容

- fire sequence 是否符合 order；
- `st` 是否只在 contract 指定位置出现；
- `last` 是否只在 contract 指定位置出现；
- producer fire sequence 与 consumer read sequence 是否一致；
- 是否出现 token/head/beat/lane 跳跃、重复、反序。

### 输出 metrics

- `num_fire`
- `num_order_violations`
- `first_bad_cycle`
- `expected_tuple`
- `observed_tuple`
- `producer_consumer_distance`

### 可抓的典型问题

- token order 反；
- head-major / token-major 搞反；
- GQA KV-head broadcast 顺序错；
- reorder buffer 缺失；
- producer 和 consumer 对 addr 解释不一致。

### 抓不到的问题

- data 数值错但顺序对；
- DDR region overlap；
- FIFO 太小导致 long-run deadlock，除非 trace 覆盖到。

## 3. `beat-count-check`

### 目的

检查 valid-ready transaction 数量是否满足 beat-count invariant，避免 missing beat / extra beat。

### 输入

- SACG；
- stream contract；
- transaction trace。

### 检查内容

- 期望 beat count 是否等于 trace fire count；
- 每个 token/head/stage 的 beat count 是否正确；
- `last` 出现次数是否正确；
- 是否存在 `valid` 高但长期无 `ready`；
- 是否存在 `ready` 高但 producer 不再产生 expected data。

### 输出 metrics

- `expected_beats`
- `observed_beats`
- `missing_beats`
- `extra_beats`
- `last_count_expected`
- `last_count_observed`
- `max_valid_without_ready_cycles`

### 可抓的典型问题

- valid 少打一拍；
- output length short；
- output length 多一拍；
- loop bound 错；
- `last` 提前或滞后；
- `st`/`last` 与 data 不同拍。

## 4. `addr-map-check`

### 目的

检查 DDR image layout、runtime config、RTL address trace 是否一致。

### 输入

- SACG；
- memory contract；
- DDR image metadata；
- window/config file；
- optional RTL address trace。

### 检查内容

静态：

- DDR regions 是否重叠；
- region base 是否满足 alignment；
- region size 是否覆盖 artifact；
- config 中 base/size 是否与 SACG 一致。

动态：

- RTL address trace 是否只访问合法 region；
- burst 是否越界；
- stride 是否符合 packing；
- 读写覆盖是否完整；
- output region 是否与 input/weight region disjoint。

### 输出 metrics

- `num_regions`
- `num_overlap_errors`
- `num_alignment_errors`
- `num_oob_accesses`
- `coverage_ratio`
- `first_bad_address`

### 可抓的典型问题

- DDR base address 偏移；
- Wq/Wk/Wv packing 顺序和 RTL stride 不一致；
- AXI burst length 错；
- output 写到错误 window；
- runtime buffer offset 错。

## 5. `numeric-compare`

### 目的

检查 stage/top 输出是否满足 numeric contract 和 tolerance policy。

### 输入

- SACG；
- numeric contract；
- observed output；
- golden output；
- optional scale/zero-point metadata。

### 检查内容

- dtype 是否一致；
- output shape 是否一致；
- tolerance 是否满足；
- 错误是否呈现 bias、scale、saturation、rounding 等模式；
- 可选：按 token/head/lane 聚合误差。

### 输出 metrics

- `num_elements`
- `num_mismatch`
- `max_abs_error`
- `mean_abs_error`
- `max_rel_error`
- `bias_estimate`
- `saturation_count`
- `first_mismatch_index`

### 可抓的典型问题

- scale stride 错；
- zero-point 错；
- rounding policy 不一致；
- bias domain 错；
- saturation 顺序错；
- W4/W8 packing 解码错。

### 抓不到的问题

- 数值刚好在 tolerance 内但语义仍错；
- 纯 liveness bug；
- DDR 地址错但输出恰好相近。

## 6. `deadlock-watchdog`

### 目的

检查 pipeline-liveness contract，定位 ready/valid deadlock 和 FIFO occupancy 异常。

### 输入

- SACG；
- liveness contract；
- cycle-level trace；
- FIFO occupancy trace，可选。

### 检查内容

- 每个 stage 是否在 max cycles 内产生输出；
- valid without ready 是否超过阈值；
- ready without valid 是否超过阈值；
- FIFO occupancy 是否长期为 0 或 full；
- 是否存在 cyclic backpressure。

### 输出 metrics

- `timeout`
- `max_stall_cycles`
- `stall_edge`
- `fifo_full_cycles`
- `fifo_empty_cycles`
- `last_progress_cycle`

### 可抓的典型问题

- ready/valid 死锁；
- FIFO depth 太小；
- consumer 不释放 ready；
- producer 不产生 valid；
- shared ready 组合环或鸡生蛋。

## 7. `repair-log-check`

### 目的

保证 repair 科学可审计，避免“改了代码但不知道修了什么”。

### 输入

- repair record；
- checker reports；
- git diff 或 patch summary；
- regression results。

### 检查内容

- 是否有 symptom；
- 是否引用 evidence；
- 是否指定 violated contract；
- 是否列出 affected artifacts；
- 是否有 minimal patch description；
- 是否有 regression tasks 和 result；
- 是否明确 keep/revert decision。

### 输出 metrics

- `num_missing_fields`
- `has_evidence`
- `has_regression`
- `patch_size_lines`
- `repair_iteration_index`

## Checker 与实验指标的关系

Checker 结果直接支撑 DAC 实验：

- Detection rate：fault injection 后 checker 是否 fail；
- Localization accuracy：checker 报告的 contract/node/edge 是否命中 root cause；
- Bug escape rate：未被早期 checker 抓到、逃到 top/system/board 的数量；
- Repair iterations：同一 violated contract 修复到 pass 的轮数；
- Human intervention count：需要人类解释或手工 patch 的次数。

## v0 实现顺序

建议顺序：

1. `sacc-lint`
2. `numeric-compare`
3. `beat-count-check`
4. `stream-trace-check`
5. `addr-map-check`
6. `deadlock-watchdog`
7. `repair-log-check`

原因：

- 前两个最容易直接复用已有验证 artifact；
- beat/stream checker 能覆盖大量真实 RTL bug；
- addr-map 和 watchdog 对 system/board closure 最关键；
- repair-log-check 用于论文证据闭环。
