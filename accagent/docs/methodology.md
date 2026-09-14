# 方法论

## 核心命题

LLM spatial accelerator design 的困难在于跨越多个 lowering boundary 的 contract preservation：

```text
model semantics
-> spatial pipeline
-> Chisel/RTL modules
-> stream interconnect
-> DDR/AXI image
-> host runtime
-> simulation and board execution
```

SpatialAccAgent 是一个 contract-guided design closure system。它的 agent 不是 free-form code generator，而是在 SACG、artifacts、evidence logs 上工作的 contract transformer 和 repairer。

## 设计状态

每一步设计都作用在：

```text
S_t = (G_t, A_t, R_t)
```

其中：

- `G_t` 是当前 SACG；
- `A_t` 是当前 artifact set；
- `R_t` 是当前 evidence/report/log set。

Agent transition 是：

```text
(G_t, A_t, R_t) -> (G_{t+1}, A_{t+1}, R_{t+1})
```

每一次 transition 都必须更新 SACG 或 artifacts，并通过相应的 checker、simulation、regression 或 backend closure step。

## 七阶段流程

### 1. Objective and Contract Boundary

定义 model family、block structure、precision、sequence length、target platform、comparison scope、correctness oracle，以及不能简化的 spatial semantics。

输出：

- design objective；
- acceptance criteria；
- initial contract boundary。

### 2. SACG Extraction

读取 model documents、quantization documents、template metadata、interface documents 和 platform constraints，构建初始 SACG：

- model contracts；
- shape contracts；
- numeric contracts；
- stream contracts；
- memory contracts；
- deployment contracts。

输出：

- `G_0 = (V, E, C, I, A)`；
- initial checker report。

### 3. Contract-Preserving Spatial Architecture

生成 PU partitioning、pipeline stages、stage schedule、tile/lane/head mapping、buffer/queue placement、residual/KV path、DDR/AXI schedule，同时保持 SACG invariants。

输出：

- 更新后的 SACG；
- spatial pipeline plan；
- performance/resource hypothesis。

### 4. Template-Bound Chisel Construction

实例化 verified Chisel templates，填参数，连接 modules，生成 wrapper，并把 artifact IDs 绑定回 SACG node/edge。

Agent 不应被评估为 free-form RTL generator。Chisel 是主要可编辑硬件 artifact；Verilog/SystemVerilog 是后端生成物或 system/board integration artifact。

输出：

- Chisel modules；
- top-level connections；
- wrapper contracts；
- artifact-to-contract binding。

### 5. Hierarchical Real-Workload Verification

在验证阶段内部生成或选择真实 workload artifacts：

- weights；
- activations；
- bias；
- scale / zero-point；
- RoPE / mask / KV-cache data；
- golden traces；
- DDR image 和 window configs。

运行 stage/top/system/board verification，并把 failure 关联回 SACG contract。

输出：

- verification tasks；
- pass/fail matrix；
- trace evidence；
- 尽可能定位到 first violated invariant。

### 6. Evidence-Guided Repair

把 failure 分类为 contract violation，并修复最小受影响 artifact 或 SACG contract。

Repair record：

```text
symptom -> evidence -> violated_contract -> patch -> regression_result
```

输出：

- failure class；
- suspected / confirmed root cause；
- minimal patch；
- regression result；
- 更新后的 SACG 和 artifact set。

### 7. Deployment Closure and Benchmarking

运行 synthesis、implementation、board/runtime integration 和 benchmark。Deployment 问题应被表示为 deployment-contract violation，而不是散落在工程日志之外。

输出：

- timing/resource/power reports；
- latency/throughput/DDR-efficiency metrics；
- board/runtime status；
- automation 和 repair metrics。

## Agent 角色

| Agent | 不是做什么 | 真正做什么 |
| --- | --- | --- |
| Specification Agent | summarize 文档 | 把 model/platform/precision constraints 转成 initial SACG |
| Spatial Architect Agent | 随便画架构 | 生成 PU partitioning、schedule、parallelism、pipeline/stream contracts |
| Memory/Runtime Agent | 只是写 host code | 生成 DDR layout、AXI windows、weight packing、runtime buffer map |
| Template Agent | free-form RTL generation | 实例化 verified Chisel templates，并绑定 contract IDs |
| Verification Agent | 只是跑 test | 构造 SACG-derived stage/top/system artifacts 和 verification tasks |
| Evidence Classifier | 读 log 讲故事 | 把 evidence 分类为 contract violation 类型 |
| Repair Agent | 大改代码 | 生成恢复某个 invariant 的 minimal patch |
| Backend Closure Agent | 盲调 Vivado | 区分 RTL、floorplan/routing、TCL、backend option 问题 |
| Benchmark Agent | 打印性能 | 生成可审计 QoR、automation、repair reports |

## 方法的科学性

方法论不是“有很多 agent”。真正的方法是：

- 显式 SACG；
- 可机械检查的 invariants 和 checkers；
- 在 contract/artifact/evidence 上做 state transition；
- 分层验证关联到 contract violation；
- invariant-directed repair；
- 通过 ablation 和 fault injection 证明 contract 有用。
