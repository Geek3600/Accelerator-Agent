# Failure Taxonomy 与 Repair Science

本文档定义 SpatialAccAgent 的 failure taxonomy。目标是把“工程 debug 记录”改写成 DAC 论文可用的 contract violation 科学框架。

核心记录格式：

```text
symptom -> evidence -> violated_contract -> patch -> regression_result
```

## Failure class 总表

| Failure class | 典型 symptom | Violated contract | 主要 checker | Repair action |
| --- | --- | --- | --- | --- |
| Shape mismatch | output dimension wrong、head/tile 不一致 | shape / model contract | `sacc-lint` | 修改 tensor shape、module parameter、tile schedule |
| Quant mismatch | stage output 接近但整体偏置或 scale 错 | numeric contract | `numeric-compare` | 修 scale layout、rounding、zero-point、bias domain |
| Stream order mismatch | 值正确但顺序错 | stream contract | `stream-trace-check` | 插入 reorder buffer、调整 tile/head/token schedule |
| Missing beat | output length short、少输出 | beat-count invariant | `beat-count-check` | 修 loop bound、valid gating、last/st 时序 |
| Extra beat | output length 多、重复输出 | beat-count invariant | `beat-count-check` | 修 done 条件、valid hold、state transition |
| Deadlock | simulation timeout、FIFO full/empty | liveness contract | `deadlock-watchdog` | resize FIFO、打破 cyclic backpressure、修 ready 释放 |
| Wrong address | system output garbage、region 错 | memory contract | `addr-map-check` | 修 DDR offset、burst stride、bank map、runtime config |
| Residual/KV bug | attention/residual 输出异常 | model edge / stream contract | `stream-trace-check` + `numeric-compare` | 修 bypass、KV cache mapping、head pairing |
| Harness/protocol bug | standalone 过、top/system 不过 | verification/deployment contract | `repair-log-check` + targeted checker | 修 reset/config/weight preload/protocol sequence |
| Timing violation | WNS negative、P&R fail | pipeline/backend contract | backend report checker | 插 register、降 fanout、调整 floorplan 或 backend option |
| Resource congestion | routing fail、LUT/BRAM/URAM 超限 | resource/deployment contract | QoR report checker | 降 parallelism、remap buffer、模板参数调整 |

## 详细 failure class

### 1. Shape mismatch

表现：

- tensor rank 或 dimension 不一致；
- hidden/head/head_dim 不匹配；
- GQA/MQA 下 KV-head 映射非法；
- module parameter 和 model config 不一致。

常见根因：

- 从 model doc 抽取 config 错；
- block style 判断错；
- template parameter 没同步；
- tile/lane 约束没有传播。

修复：

- 更新 SACG shape contract；
- 修 module parameter；
- 修 stage schedule；
- 修 artifact builder 中 shape 解释。

实验注入：

- 把 `num_kv_heads` 改错；
- 把 head_dim 改错；
- 把 output tile size 改成不整除。

### 2. Quant mismatch

表现：

- 输出大体趋势正确，但整体偏大/偏小；
- 某些 lane 系统性偏置；
- saturation count 异常；
- W4/W8 版本差异巨大。

常见根因：

- scale stride 错；
- bias domain 错；
- zero-point 错；
- rounding policy 错；
- 先裁剪再加 bias，顺序错；
- q/k/v 共用 scale，实际应独立。

修复：

- 更新 numeric contract；
- 修 scale artifact builder；
- 修 Chisel epilogue；
- 调整 tolerance policy，但不能用放宽 tolerance 掩盖 contract violation。

实验注入：

- W4 scale stride 偏移；
- zero-point 改错；
- q/k/v scale 交换；
- bias 直接用原始 dump 而非 hardware-domain bias。

### 3. Stream order mismatch

表现：

- 数值集合看起来接近，但 token/head 顺序错；
- standalone stage 过，top attention 不过；
- consumer 读到上一 token/head 的数据；
- multi-token 时混入不同 token。

常见根因：

- producer 是 head-major，consumer 假设 token-major；
- store unit address 语义与 CU 输出顺序不一致；
- multi-token collect buffer 没按 token 分 bank；
- GQA KV-head broadcast 顺序错。

修复：

- 更新 stream contract；
- 插入 reorder buffer；
- 修 output address mapping；
- 修 collect buffer 维度。

实验注入：

- 交换 token/head loop order；
- 把 `collect_addr / COLLECT_NUM` 和 `%` 逻辑改反；
- GQA query-head 到 KV-head 映射偏移 1。

### 4. Missing beat / extra beat

表现：

- output beats 少；
- output beats 多；
- first beat 被吞；
- last beat 没出；
- `last` 提前或滞后。

常见根因：

- valid/data/address/last 不同拍；
- `psum_last` 没有用 `data_in_valid` gating；
- state machine done 条件持续多拍；
- reset/config 时序污染 FSM。

修复：

- 修 valid gating；
- 将 data/addr/last 同拍寄存；
- 修 loop bound；
- 修 reset/config/preload sequence。

实验注入：

- valid 延迟一拍；
- 去掉 `data_in_valid` gating；
- last 早一拍；
- done condition 持续高电平。

### 5. Deadlock / liveness failure

表现：

- simulation timeout；
- 某 stage 长期 valid=1 ready=0；
- FIFO 长期 full 或 empty；
- top/system 在某 state 不前进。

常见根因：

- shared ready 组合依赖形成环；
- producer/consumer 对 full/empty 语义理解不同；
- bank state 没释放；
- `st` 或 `last` 没触发状态切换。

修复：

- 增加或调整 FIFO；
- 打断 cyclic backpressure；
- 修 bank full/buzy counter；
- 修 layer start / done 传播。

实验注入：

- FIFO depth 改小；
- ready 依赖 consumer output valid；
- full counter 不减；
- state transition 依赖永远不会来的 last。

### 6. Wrong address / memory-layout mismatch

表现：

- stage-level 过，system-level output garbage；
- 某 DDR region 读错；
- runtime window 配置正确但 RTL trace 地址越界；
- output 写回 offset 错。

常见根因：

- DDR base address 错；
- burst length/stride 错；
- weight packing 和 RTL address generator 不一致；
- host runtime buffer offset 错；
- board wrapper config 解析错。

修复：

- 修 memory contract；
- 修 DDR image builder；
- 修 RTL address generator；
- 修 runtime config parser；
- 修 host buffer map。

实验注入：

- region base 偏移；
- Wq/Wk packing 顺序交换；
- burst length 改错；
- output region size 改小。

### 7. Residual/KV/model-edge bug

表现：

- attention 输出不稳定；
- residual add 接入错误旧值；
- token 越深误差越大；
- GQA/MQA 下只有部分 head 错。

常见根因：

- residual bypass 对齐错误；
- KV cache head mapping 错；
- RoPE dim order 错；
- causal mask / prefill / decode 语义错。

修复：

- 修 model edge contract；
- 修 KV cache indexing；
- 修 RoPE layout；
- 修 residual queue；
- 修 attention mask builder。

实验注入：

- RoPE even/odd layout 交换；
- query-head to kv-head 映射偏移；
- residual 延迟一 token；
- causal mask 允许未来 token。

### 8. Harness/protocol bug

表现：

- RTL 可能正确，但 harness 驱动顺序错；
- standalone 与 top 口径不一致；
- weight init 后状态机被污染；
- config 没被正确解析。

常见根因：

- reset/config/weight preload 顺序错；
- stage golden 口径和硬件输出口径不一致；
- testbench parser 不兼容 simulator；
- window artifact 和 contract 不一致。

修复：

- 修 verification task contract；
- 修 harness protocol；
- 修 config parser；
- 修 artifact builder；
- 更新 oracle。

实验注入：

- weight init 后不 reset；
- config 顺序换错；
- golden window 切片错；
- parser 忽略某个 key。

### 9. Timing / backend closure failure

表现：

- synthesis 过但 implementation WNS negative；
- routing fail；
- fanout 过大；
- 某 arithmetic tree 资源/路径过热。

常见根因：

- pipeline register 不足；
- parallelism 过高；
- DSP/BRAM/URAM mapping 不合理；
- floorplan 约束缺失；
- backend option 不匹配。

修复：

- 插 register；
- 降 parallelism；
- remap buffer；
- 使用 DSP；
- 调整 floorplan / XDC / TCL。

实验注入：

- 去掉关键 pipeline register；
- 增大 fanout；
- 强制 LUT 实现大加法树；
- 缩小资源预算。

## Repair record 要求

每个 repair 必须回答：

1. symptom 是什么？
2. first evidence 是什么？
3. 违反了哪个 contract / invariant？
4. 修改了哪个 artifact？
5. 为什么这个 patch 能恢复 invariant？
6. 跑了哪些 regression？
7. regression 结果如何？
8. patch 保留还是回退？

## 与论文实验的关系

Failure taxonomy 支撑三类实验：

1. **真实 bug 归类**：把上下文文档中的历史 bug 映射到上述 failure class。
2. **Fault injection**：每类 failure 人为注入若干实例，测 detection/localization/repair。
3. **Ablation**：去掉对应 contract 或 checker，看 bug 是否更晚暴露、repair iteration 是否增加。

## 当前上下文可映射的真实例子

可从长期上下文中抽象：

- FFNDown `psum_last` gating -> Missing/extra beat；
- FFNUp scale/bias/domain 对齐 -> Quant mismatch；
- QKV multi-token collect buffer -> Stream order mismatch；
- Softmax valid/data/addr 对齐 -> Missing beat / stream contract；
- DM2 ctx/value 接线 -> Residual/KV/model-edge bug；
- SystemTop DDR preload/wrapper -> Memory/deployment contract；
- VCS config parser 问题 -> Harness/protocol bug；
- token43/token44 深序列 x 传播 -> liveness/model-edge/numeric evidence chain。
