# SACG 在 SpatialAccAgent 框架中的作用

## 0. 文档目的

本文档明确 **Spatial Accelerator Constraint Graph (SACG)** 在 SpatialAccAgent 框架中的职责位置。

当前框架已经初步定义为：

```text
template-constrained + state-guided + checker-verified
```

但这句话本身还不够。必须进一步明确：

- SACG 在框架中由谁创建；
- 哪些 agent 读取 SACG；
- 哪些 agent 修改 SACG；
- checker 如何把 evidence 回写到 SACG；
- repair 如何由 SACG 约束；
- human approval 如何与 SACG 连接；
- 为什么 SACG 才是解决 Cross-Layer Consistency Problem 的核心，而不是普通日志、prompt 或 checker 列表。

核心结论：

> SACG 是 SpatialAccAgent 的共享设计状态和动作约束中心。Agent 不是直接围绕文件自由行动，而是围绕 SACG 做 constraint-state transition；checker 不是只输出 pass/fail，而是把 evidence 回写到 SACG；repair 不是局部 patch，而是恢复 SACG invariant 的受限状态转换。

进一步说，SACG 是 SpatialAccAgent 解决跨层一致性问题的核心贡献之一，也是证明 agent 框架能够自动设计出可用硬件加速器的可信来源之一。

它的论文意义不是“保存更多状态”，而是让 LLM agent 在长设计流程中持续感知其他阶段的状态和行为：

- 在生成时，agent 不只看到当前 template 或当前文件，而是看到 model、pipeline、stream、memory、runtime、verification、backend 之间的共享约束；
- 在查错时，agent 不只局限于本 stage 的 log，而是能把 symptom 映射到跨 stage 的 violated constraints；
- 在修复时，agent 不只让当前 test pass，而是通过 SACG 知道这个 patch 是否会影响其他 stage、runtime、memory layout、backend timing 或 regression；
- 在论文证明上，SACG 提供了比 agent 自述更可信的 evidence chain：constraint state、checker evidence、repair record、regression result 和 approval record。

因此，SACG 的价值是把 long-horizon LLM agent 从“局部文件编辑器”提升为“跨阶段设计状态维护者”。这正是 SpatialAccAgent 能提高最终 accelerator 可用程度的核心原因。

---

## 1. SACG 在框架中的一句话定位

SACG 在 SpatialAccAgent 中的角色是：

> **the shared design-state control plane for template-constrained, checker-verified agentic design closure**

中文：

> **SACG 是 template-constrained、checker-verified agentic design closure 的共享设计状态控制层。**

它承担三件事：

1. **State**：记录当前 accelerator design 应满足的跨层约束；
2. **Control**：约束 agent 每一步能做什么、必须声明什么、需要检查什么；
3. **Evidence binding**：把 checker/tool 证据绑定回具体 node、edge、constraint、artifact 和 repair。

因此，SACG 不是附属资料，而是框架的核心运行对象。

---

## 2. SACG 不是什么

为了避免框架设计跑偏，先明确 SACG 不是以下对象。

### 2.1 SACG 不是 agent

SACG 不自己生成代码、不自己修 bug、不自己调用工具。

Agent 使用 SACG 来决定：

- 应该生成什么 artifact；
- 哪些 constraints 会被触碰；
- 哪些 checker 必须运行；
- failure 应该定位到哪一类 constraint；
- repair 是否允许自动执行。

### 2.2 SACG 不是 prompt memory

聊天历史、自然语言总结、agent reasoning 都不能作为稳定设计状态。

只有写入 SACG 的 model constraint、template binding、stream edge、memory layout、checker result、repair record 才是框架可依赖的设计事实。

### 2.3 SACG 不是 checker

Checker 是执行检查的工具。SACG 是 checker 要检查的目标和 evidence 的归宿。

关系是：

```text
SACG invariant
-> checker task
-> tool/checker evidence
-> checker report
-> update SACG status
```

### 2.4 SACG 不是 artifact database

SACG 会记录 artifacts，但它不是简单文件索引。

Artifact 只有在绑定到 node、edge、constraint、checker 或 repair 时才有框架意义。例如：

- `QKVLinear.scala` 绑定到 `model_op.qkv`、`template.linear_qkv`、`constraint.numeric.qkv`；
- `qkv_stage_trace.csv` 绑定到 `edge.qkv_to_attention` 和 `constraint.stream.qkv_to_attention`；
- `ddr_image.bin` 绑定到 `constraint.memory.ddr_layout` 和 `constraint.runtime.buffer_map`。

### 2.5 SACG 不是论文里的静态图

SACG 必须随设计过程变化。

它应该支持：

- 初始化；
- template selection；
- parameter binding；
- artifact generation；
- checker result update；
- failure localization；
- repair transition；
- approval record；
- regression promotion；
- backend/board closure。

---

## 3. SACG 的六个框架职责

### 3.1 设计事实的唯一可信状态

SACG 是框架中的 source of truth。

例如：

- 当前模型是否是 MHA/GQA/MQA；
- hidden/head/head_dim 是多少；
- 每个 model op 绑定哪个 template；
- 每条 stream edge 的 token/head/beat order；
- DDR region 的 base/stride/packing；
- runtime config 字段如何映射到硬件寄存器；
- 哪个 checker 已经通过；
- 哪个 repair 被保留或回退。

这些不能只存在于 prompt、注释或文件名中。

### 3.2 生成动作的约束输入

Agent 生成任何 artifact 之前，都必须先查询 SACG。

例如 Template Binding Agent 生成 QKV stage 时，输入不是一句“生成 QKVLinear”，而是：

```text
model_op.qkv
template.linear_qkv_int8
constraint.shape.qkv
constraint.numeric.qkv
constraint.stream.qkv_out
constraint.memory.qkv_weight_layout
```

因此生成过程是：

```text
SACG constraints + template spec -> generated artifact
```

不是：

```text
natural language prompt -> free-form Chisel
```

### 3.3 checker 的检查目标和 evidence 回写中心

Checker 不应该只返回一段 log。Checker report 必须回写到 SACG：

```text
checker report
-> invariant
-> constraint
-> node/edge
-> artifact
-> pass/fail/unknown
```

例如 `beat-count-check` 失败时，报告必须说明：

- 哪个 stream edge；
- 哪个 beat-count constraint；
- expected beats；
- observed beats；
- first missing/extra beat；
- 相关 artifact；
- candidate repair scope。

### 3.4 failure localization 的索引图

普通 agent 看到的是 symptom：

```text
output mismatch
simulation timeout
missing beat
wrong address
timing violation
```

SACG 的作用是把 symptom 映射为 violated constraint candidates：

```text
symptom -> evidence -> candidate constraints -> affected nodes/edges/artifacts
```

这使 agent 不再只按最近的代码位置猜 root cause。

### 3.5 repair 的边界和审批门

SACG 决定某个 repair 是：

- auto-allowed local repair；
- approval-required design change；
- forbidden action。

例如：

- 修 valid delay：通常是 auto-allowed，但必须 rerun stream/beat regression；
- 改 tile size：必须 human approval；
- 改 golden output：forbidden；
- 改 memory packing：必须 approval，并且要同步更新 DDR image、runtime map、addr checker。

Repair Agent 的输出必须是：

```text
violated constraint -> bounded patch -> required checker -> regression plan
```

而不是：

```text
test failed -> edit code
```

### 3.6 回归和实验统计的依据

SACG 还用于产生论文实验指标：

- detection rate；
- localization accuracy；
- repair success rate；
- repair iterations；
- regression failures；
- bug escape level；
- human approval count；
- changed constraints；
- changed artifacts；
- design closure success。

这些指标都必须从 SACG transition、checker report、repair record 中统计，而不是从自然语言复盘中人工估计。

---

## 4. SACG 与各 Agent 的关系

| Framework component | Reads from SACG | Writes to SACG | Main responsibility |
| --- | --- | --- | --- |
| Controller Agent | current graph status, open failures, stale artifacts | transition intent, scheduling decision | 决定下一步做什么 |
| Model and Constraint Agent | task card, model docs | model/shape/numeric constraints | 建立初始设计状态 |
| Template Binding Agent | model constraints, template specs | template binding constraints | 选择并绑定可信模板 |
| Pipeline Planner | model/template constraints, platform limits | pipeline nodes, stream/memory/control edges | 形成 spatial pipeline 计划 |
| Artifact Generator | template bindings, parameters, edge constraints | artifact bindings, stale artifact list | 生成 Chisel、Top、wrapper、scripts |
| Verification Agent | invariants, target constraints, artifact refs | checker task records, pass/fail evidence | 派生并运行验证任务 |
| Evidence Classifier | checker reports, graph topology | failure classification, candidate violated constraints | 把 symptom 定位到 constraints |
| Repair Agent | violated constraints, repair rules, approval rules | repair proposal, patch record, regression result | 执行受限修复 |
| Backend Closure Agent | backend/QoR constraints, artifacts | timing/resource evidence, backend repair records | 处理综合实现和 QoR 证据 |
| Human Approval Gate | approval-required transitions | approval/rejection records | 控制高风险设计修改 |

这个表说明：SACG 是所有 agent 的共享工作对象。不同 agent 不是各自维护一套私有上下文，而是围绕同一个 SACG 做受控更新。

---

## 5. SACG 在完整执行流程中的位置

### 5.1 Stage 0：Task Card

Human 输入 task boundary。

SACG 作用：

- 固化目标模型、平台、数值策略、模板库、toolchain；
- 记录哪些字段是 agent 不可擅自改变的 boundary；
- 生成初始 approval rules 和 forbidden rules。

### 5.2 Stage 1：Model Constraint Extraction

Agent 读取模型配置和文档。

SACG 作用：

- 创建 model nodes；
- 创建 model/shape/numeric constraints；
- 标出缺失信息或 ambiguous semantics。

### 5.3 Stage 2：Template Selection

Agent 从可信 Chisel template library 选择模板。

SACG 作用：

- 记录 candidate templates；
- 记录 selected template；
- 检查 template coverage；
- 记录 template 不支持的 shape/numeric/platform 条件。

### 5.4 Stage 3：Pipeline Planning

Agent 规划 spatial pipeline。

SACG 作用：

- 创建 pipeline_stage nodes；
- 创建 stream/residual/control/memory/liveness edges；
- 记录 producer-consumer order、FIFO/buffer assumptions、runtime movement assumptions。

### 5.5 Stage 4：Parameter Binding

Agent 绑定模板参数。

SACG 作用：

- 把 model constraints 映射到 concrete Chisel parameters；
- 检查参数是否来自合法 constraint；
- 防止 agent 临时发明参数值。

### 5.6 Stage 5：Artifact Generation

Agent 生成 Chisel、Top、wrapper、testbench、scripts。

SACG 作用：

- 记录 artifact 与 node/edge/constraint 的绑定；
- 标记受影响 artifacts；
- 派生必须运行的 checker。

### 5.7 Stage 6：Verification Artifact Generation

Agent 生成真实数据窗口、golden、trace、DDR image、runtime config。

SACG 作用：

- 确保验证数据使用同一组 shape/numeric/layout/runtime constraints；
- 防止 stage/top/system 使用不同语义的 golden 或 data packing。

### 5.8 Stage 7：Stage/Top/System Verification

Verification Agent 运行 checker 和仿真。

SACG 作用：

- 为每次验证定义 target constraints；
- 接收 checker reports；
- 更新 invariant pass/fail/unknown；
- 记录 first failing boundary。

### 5.9 Stage 8：Repair and Regression

Repair Agent 处理 failure。

SACG 作用：

- 将 symptom 映射到 violated constraints；
- 判断 repair scope；
- 记录 patch 与 affected constraints；
- 派生 regression set；
- 决定 state promotion 或 rejection。

### 5.10 Stage 9：Backend and Board Closure

Backend/Deployment Agent 运行 synthesis、implementation、board run。

SACG 作用：

- 绑定 timing/resource/board evidence；
- 判断 timing repair 是否影响 stream/pipeline semantics；
- 记录 board runtime status 和 benchmark；
- 完成 deployment constraints 的 closure。

---

## 6. SACG 的控制流接口

后续 framework runtime 至少应提供以下 SACG 操作。

### 6.1 Query

用于 agent 查询当前设计状态：

```text
get_node(id)
get_edge(id)
get_constraint(id)
get_constraints_by_artifact(path)
get_artifacts_by_constraint(id)
get_open_failures()
get_stale_artifacts()
get_required_checkers(touched_constraints)
get_approval_requirement(touched_constraints)
```

### 6.2 Transition Declaration

用于 agent 声明一次动作：

```text
declare_transition(action_type, touched_nodes, touched_edges, touched_constraints)
```

框架必须拒绝没有 touched constraints 的状态修改。

### 6.3 Artifact Binding

用于把文件变成可追踪 design artifact：

```text
bind_artifact(path, artifact_type, nodes, edges, constraints, producer)
mark_artifact_stale(path, reason)
mark_artifact_fresh(path, evidence_id)
```

### 6.4 Evidence Attachment

用于 checker/tool 回写证据：

```text
attach_evidence(checker, status, invariant, constraints, artifacts, log_path)
```

### 6.5 Failure Localization

用于把 report 转成候选 broken constraints：

```text
localize_failure(report_id) -> candidate_constraints
```

### 6.6 Repair Gate

用于判断修复权限：

```text
classify_repair_scope(touched_constraints) -> auto_allowed | approval_required | forbidden
```

### 6.7 State Promotion

用于接受或拒绝状态更新：

```text
promote_transition(transition_id)
reject_transition(transition_id, reason)
```

Promotion 条件：

- touched constraints 已声明；
- artifact binding 已更新；
- required checker 已执行；
- evidence 已绑定；
- required regression 已通过；
- approval 已记录；
- forbidden action 未发生。

---

## 7. SACG 生命周期

SACG 在一次 design run 中经历以下版本：

```text
G_0_task
  task boundary and initial assumptions

G_1_model
  model, shape, numeric constraints

G_2_template
  template candidates and selected bindings

G_3_pipeline
  pipeline stages and stream/memory/control edges

G_4_artifact
  generated Chisel, wrappers, scripts, verification artifacts

G_5_verified
  stage/top/system checker evidence

G_6_repaired
  repair records and regression evidence

G_7_closed
  backend, board, benchmark evidence
```

这些不是必须存成七个独立文件，但 runtime 需要能通过 transition ledger 回放每个版本。

---

## 8. 一个典型 failure 如何经过 SACG

假设 top-level attention output mismatch。

普通 agent 可能直接改 `Attention.scala`。

SACG-guided flow 是：

```text
1. Verification report:
   top attention mismatch at token/head/beat

2. Evidence binding:
   report binds to edge.qkv_to_attention, edge.softmax_to_dm2, edge.dm2_to_out

3. Localization:
   stage-level QKV pass
   stage-level Softmax pass
   top mismatch starts at attention edge
   candidate constraints:
     constraint.stream.qkv_to_attention
     constraint.numeric.softmax_ctx_scale
     constraint.beat.dm2_output

4. Repair proposal:
   if evidence shows wrong ctx scale:
     violated = constraint.numeric.softmax_ctx_scale
     patch = update top verification config / RTL scale binding
     approval = not required if numeric policy unchanged

5. Regression:
   rerun affected stage/top checkers
   rerun prior passing attention path regression

6. Promotion:
   update SACG evidence and repair record
```

关键是：SACG 迫使 agent 先定位 violated constraint，再 patch。

---

## 9. SACG 如何解决论文定义的问题

Cross-Layer Consistency Problem 的根因是：

```text
constraints are implicit, scattered, and easy to drift
```

SACG 的回答是：

```text
make constraints explicit, linked, executable, and repairable
```

对应关系：

| Problem symptom | SACG role |
| --- | --- |
| agent 不知道当前设计状态 | SACG 是 shared design state |
| artifact 之间隐式假设丢失 | constraints 显式绑定 node/edge/artifact |
| checker 只有 log，没有语义 | evidence 回写到 invariant/constraint |
| failure 不知道该修哪一层 | graph localization 映射到 violated constraints |
| repair 容易过大或修错层 | repair gate 和 approval rules 限制 patch scope |
| repair 后破坏旧功能 | regression set 从 touched constraints 派生 |
| 论文无法量化 agent 价值 | transition/evidence/repair records 产出实验指标 |

因此，SACG 是框架解决问题的“机制”，而不是方法旁边的一个数据结构。

---

## 10. 最小实现要求

第一版框架代码不需要先实现完整 autonomous agent。更重要的是先实现 SACG runtime。

最小实现应包括：

- load SACG file；
- validate node/edge/constraint/artifact references；
- query touched constraints；
- declare transition；
- bind artifact；
- attach checker evidence；
- classify repair scope；
- record approval；
- promote/reject transition；
- export run report。

换句话说，第一版可执行框架应该先证明：

> 没有 SACG transition，agent 不能合法修改设计状态；没有 checker evidence，transition 不能 promotion；没有 approval，boundary-changing repair 不能执行。

---

## 11. 与后续文档的关系

本文档定义 SACG 在 agent 框架中的职责。

后续应继续落地：

```text
accagent/docs/sacg_schema_v1.md
accagent/docs/template_spec_v1.md
accagent/docs/checker_binding_v1.md
accagent/docs/transition_protocol_v1.md
accagent/docs/repair_protocol_v1.md
```

其中：

- `sacg_schema_v1.md` 定义 SACG 文件格式；
- `template_spec_v1.md` 定义 template node 和 template-binding constraints；
- `checker_binding_v1.md` 定义 checker report 如何回写 SACG；
- `transition_protocol_v1.md` 定义 agent action 如何变成合法 transition；
- `repair_protocol_v1.md` 定义 repair 如何被 SACG gate 和 regression gate 控制。

---

## 12. 一句话总结

SACG 在 SpatialAccAgent 中的作用是：

> **把所有 agent、templates、artifacts、checkers、repairs、approvals 和 reports 统一到同一个显式设计状态中，使 agent 的每一步都成为可检查、可追踪、可拒绝、可修复的 constraint-state transition。**
