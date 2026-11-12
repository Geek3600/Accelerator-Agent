# 机制实验进展、问题与下一步评估

**快照时间：** 2026-10-31（Asia/Shanghai）  
**范围：** `new_core_method_eval.md` 所定义的机制实验 1A、1B、2A、2B。  
**证据原则：** 本文只把现有 run 目录中的执行记录、机器可读结果和真实工具日志作为观测证据。计划文字、目标值、受控 probe 和假设性耗时分别标注，不能互相替代。`vcs_compile_only` 只证明编译、展开和链接门通过，不等于 RTL 运行仿真、周期计数、数值正确性或上板运行。

## 1. 快速状态总表

| 实验 | 目的 | 实际已执行 | 当前结果 | 证据强度 | 主要缺口 |
|---|---|---|---|---|---|
| 1A 前向图构建 | 观察模型、模板、pipeline 和契约边的建立 | GPT-2 Medium seq32，单个 ACCORD run 的 Stage-0/1/2/3 | 图边数 `7 → 7 → 18`；最终 7 条模型顺序边、11 条 stream 边；Stage-3 checker `11 pass / 0 fail / 0 error` | 单 run、真实持久化状态 | 无匹配 baseline cohort，无法估计传播准确率、违反率或 first-pass 集成率 |
| 1B 参数传播 | 比较 ACCORD 与 B0 对单字段修改的下游传播 | preregistered T1–T6，ACCORD/B0 各 1 次，共 12 个 Stage-4 job；另有 reuse=1 补充 T7、R1–R4 | T1–T6 全部在 Stage-4 eligibility 因 `cyclic_stream_wait` 返回码 2；T7 到 Stage-5，R1–R4 到 Stage-5/部分 compile-only 检查，但 Stage-6 仍被板级 manifest/AXI-DDR 前置条件挡住 | T1–T6 是真实 Stage-4 记录；补充组是受控扩展 | 没有 T1–T6 的 Stage-5/6 配对结果；没有可计算的传播召回率、无关产物保持率或 Pass@1 |
| 2A 故障追踪与修复 | 验证依赖图切片、根因定位和有界修复 | 2 个静态 compile fault probe；1 个 T7 B0 编译诊断修复 episode | Attention probe 目标节点唯一命中；Activation probe 候选含正确节点但有歧义；没有 probe repair/revalidation；T7 有一次 adapter/manifest 编译诊断修复并重新编译通过 | 真实远端 VCS 日志和 hash-bound SACG snapshot | 没有 runtime CCTG；没有 8 个独立样本；没有 8/8 定位、scope 或修复成功率 |
| 2B 证据失效与重验证代价 | 验证证据绑定、失效检测和重验证成本 | GPT-2 Small/Medium 各 E1–E4 deterministic fixtures；1 个真实 report copy replay；单次 Stage-3/6/7 gate timing | Fixtures 8/8 产生预期 mutation outcome；追加空白字节的隔离 report 被 hash drift 拒绝；gate timing 已测但来自不同 source fingerprint | fixture/replay 和真实工具墙钟记录 | 没有同源码、同输入的 targeted/full 配对实验，不能声称实测 speedup 或因果效率收益 |

**当前运行状态：** 机制实验目录没有正在执行的机制 runner。系统中可见的 `stage_backend`/Vivado 进程属于 `gpt2_medium_seq32_claude_opus5_20261027` 的旁支综合流程，不应混入 1A–2B 机制结果。

## 2. 实验定义与控制边界

这组实验的目标是分别检查两个机制：

1. **前向约束/参数传播（1A/1B）**：设计状态由模型和板卡约束开始，经模板选择、pipeline 规划、参数绑定和产物生成，依赖图应能指出受影响的下游节点，并保留不相关产物。
2. **依赖引导故障处理与证据管理（2A/2B）**：工具失败应绑定到当前图快照和源码/报告证据；系统应提供受限的故障上下文和重验证范围；证据变化后旧报告不能被继续接受。

ACCORD 是带图传播的流程；B0 是受控对照配置，用于模拟局部修改而不触发完整的下游依赖更新。对照并不代表一个已经完成的传统系统实现，只有在同一候选、同一输入和同一 gate 下完成配对运行时，才能计算差异。

实验验证策略采用当前 run 的 `vcs_compile_only` 政策。它可验证 Chisel 展开、生成源码、端口/位宽/链接等编译期结构，但没有执行 runtime VCS 仿真，也没有真实输入/权重/输出计数。因此所有“功能正确”“周期精确”“死锁已排除”“上板可运行”等结论都超出本组证据。

## 3. 1A：前向图构建

### 3.1 观测到的状态

来源为 GPT-2 Medium、seq32 的单个 ACCORD run。复制的 SACG 状态在 Stage-0、Stage-1、Stage-2/3 记录的边数为 `7、7、18`。最终状态包含：

- 7 条模型顺序边；
- 11 条 stream/数据流边；
- Template Selection 快照：20 nodes、7 edges、16 constraints、16 artifacts；
- Pipeline Planning 快照：30 nodes、18 edges、23 constraints、18 artifacts；
- Stage-3 pipeline checker：11 pass、0 fail、0 error。

这表明在这一条前向轨迹中，图状态从模型顺序关系扩展到了流拓扑和阶段产物，并且当前 pipeline 检查器没有报告错误。

### 3.2 能支持的结论

可以报告：该 run 实际生成并持久化了跨阶段图状态；图中存在模型顺序边和 stream 边；Stage-3 的 11 项检查在该快照上通过。

### 3.3 不能支持的结论

这不是 cohort 实验。没有 Unstructured-History、Flat-Config 和 ACCORD 的匹配对照，也没有多 run 统计。因此不能从这一条 run 推导：

- 参数传播准确率或召回率；
- 相对 baseline 的 first-pass integration rate；
- 违反率下降；
- 图传播对设计质量或性能的因果收益。

原始报告：[method1 REPORT](../experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/REPORT.md)，机器结果位于同目录的 `forward/observed_results.json`、`final_report.json` 和 `status.json`。

## 4. 1B：参数传播

### 4.1 preregistered T1–T6

六个候选来自源 run 持久化的 360-row Stage-4 表，每个相对所选 baseline 只改变一个 DSE 字段：

| 任务 | 单字段变化 | candidate |
|---|---|---|
| T1 | array rows `16 → 8` | `arch_b927f500990e` |
| T2 | array cols `32 → 16` | `arch_755a0908dcb3` |
| T3 | FIFO depth `64 → 128` | `arch_3fd8f432a88e` |
| T4 | activation banks `2 → 4` | `arch_63e2712b0d8c` |
| T5 | cross-token reuse `16 → 8` | `arch_3fedd13a9880` |
| T6 | cross-token reuse `16 → 4` | `arch_6226a7032ff5` |

ACCORD 和 B0 各执行一遍，共 12 个隔离 Stage-4 job。**12/12 candidate materialization 为 pass**，没有 materialization error；但每个重算的单候选 DSE 报告都在 `cyclic_stream_wait` schedule blocker 后得到零个 feasible candidate，返回码为 2，未进入 Stage-5 Chisel 生成和 Stage-6 VCS compile-only。

这不是 VCS 编译失败。`stage_params.bind_parameters()` 调用 `build_dse_search()`；候选字段先完成物化，随后 `cost_features()` 报告 `cycle_model_status=blocked`，代码把该状态转换为 `record.feasible=false` 并追加硬约束错误，候选选择因此得到空集并退出。检测器依据 Attention output-projection wait 和 Linear input-chunk collection wait 的模板源码模式识别结构性循环等待风险；它没有执行 RTL 仿真或形式化 deadlock proof。因此该结果既不是“缺少周期数据”这么简单，也不是运行时死锁的独立证明。

由于下游没有运行，以下指标应记为 **not measured**，不能写成 0：affected-artifact/node recall、unrelated-artifact preservation、contract-check rate、Stage-5/6 Pass@1、ACCORD/B0 的传播差异。

### 4.2 T7 与 reuse=1 补充组

T7 将 reuse `16 → 1`，超出原 preregistered `[4, 8, 16]` 范围，因此是补充案例，不应与 T1–T6 混写成预注册结果。T7 的 ACCORD/B0 到达 Stage-5，且 exact-board VCS compile-only 通过；runtime simulation skipped。B0 在一个编译诊断 episode 中暴露出 adapter 的 `k_in_ready_unused` 未声明、kernel/权重 manifest 等跨阶段问题，修复后再次 compile/elaboration 返回 0（记录耗时约 27.221 s）。该 episode 没有精确 SACG binding，也没有 causal slice SHA，因而只能作为描述性 compile-diagnostic repair，不能作为 graph-guided localization 证据。

reuse=1 的 R1–R4 是另一个补充扩展：

| 组 | 参数变化 | 观察结果 |
|---|---|---|
| R1 | rows `16 → 8` | ACCORD/B0 Stage-4/5 与 leaf/single-layer/multilayer compile-only 通过；exact-board VCS 未执行 |
| R2 | cols `32 → 16` | 同上；Stage-6 因 candidate-local board manifest/AXI-DDR preflight 未通过 |
| R3 | FIFO `64 → 128` | 两侧均卡在缺少 DDR refill 到 weight/bias streams、配置 transport、layer scheduler 的完整映射；未形成可重验 adapter/manifest |
| R4 | activation banks `2 → 4` | 两侧 loop 到 iteration 2 blocked，原因同类；未形成可重验 adapter/manifest |

R3/R4 的记录没有提供 ACCORD 与 B0 的传播差异。ACCORD 曾出现 `cfg_done` 方向诊断，但源码和 identity 都显示 input，不能把该诊断包装为已确认的 RTL 端口错误。相同候选重复跑 Stage-4/5 没有新增信息；只有板级集成证据变化后才有理由从 Stage-6 恢复。

主要材料：

- [T1–T6 报告](../experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/REPORT.md)
- [T7 补充目录](../experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/T7-cross-token-reuse-1/)
- [R1–R4 执行摘要](../experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/reuse1_parameter_propagation/)

## 5. 2A：故障追踪、静态依赖投影与修复

### 5.1 受控 compile-fault pilot

在隔离副本的 `Attention.sv` 末尾注入一行 `this_is_a_compile_fault @;`，原始生成源码未修改。远端 VCS 真实返回 255，并报告 `Error-[SE] Syntax error`（`Attention.sv:4213`）。故障报告绑定 R2 Stage-5 SACG snapshot：

`e03bc2c76f4a5fe71fe1c52fb170838348fa6d1b5d81234a0ea64edeb7b951ad`

静态投影根据精确 artifact/source/template 映射和图入边得到唯一候选 `node.pipeline.stage_01_self_attention`，与预注册目标一致，属于 **1/1 controlled sample hit**。没有执行 repair 或 post-repair compile，所以 scope violation 为 not applicable，不能计算 repair success。

### 5.2 Activation probe

第二个受控注入针对 `Activation.sv`。候选集合同时包含正确的 `node.pipeline.stage_05_activation` 和 `node.model_op.05_activation`，结果存在歧义，因此不计为 top-1 命中。该 probe 同样没有 repair/revalidation。

现有目录中的记录对 focused/static tests 总数出现“6 个”和“12 个”两种文字表述；机器结果实际提供的是上述两个端到端 controlled probe。汇总时保留该冲突，不能擅自把它合并成 6、12 或 2 个样本的准确率。

### 5.3 T7 B0 编译诊断修复

T7 B0 是一个真实的 bounded compile-diagnostic-driven repair episode：第一次 VCS 报告 `k_in_ready_unused` 未声明；iteration 0015 对 adapter 做 patch 并刷新 weight manifest，后续 compile/elaboration 返回 0，约 27.221 s。simulation skipped。故障诊断没有 `sacg_state_sha256`，`causal_slice_sha256=null`，所以应描述为“编译诊断驱动的局部修复”，不能称为 CCTG graph-guided root-cause localization。

### 5.4 静态切片实现的边界

`accagent/framework/sacg_cctg_causal_slice.py::build_static_failure_context()` 是独立的静态 compile/contract/timing projection：要求 failure report 绑定精确 SACG SHA，按 source/artifact 映射和 incoming edges 输出影响上下文；没有 graph-bound root ID 时不臆测 root；`authorized_repair_scope` 在缺证据时留空并返回 insufficient。它扩展了 compile-time 诊断的可追溯性，但不替代 runtime CCTG，也不证明实际修复闭环。

因此当前 2A 可支持的最强表述是：在一个 Attention 受控编译错误上，静态图投影唯一映射到预注册 pipeline 节点；在一个 Activation probe 上暴露出节点命名歧义；另有一次没有 graph binding 的编译诊断修复。不能报告 8/8 localization、8/8 repair、scope violation=0 或 targeted revalidation 成功率。

材料：[compile-fault pilot](../experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/compile_fault_pilot_20261029/)、[Attention probe](../experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/static_graph_probe_20261030/)、Activation probe 同目录的 `static_graph_probe_activation_20261030/`。

## 6. 2B：证据失效与重验证代价

### 6.1 确定性 fixture

GPT-2 Small 和 GPT-2 Medium 各执行 E1–E4 四个确定性 evidence-contract mutation，共 8 个 fixture。8/8 产生预期 mutation outcome；它们没有启动 Agent、VCS、Vivado 或 RTL simulation，因此是契约逻辑 fixture，不是端到端 EDA 通过率。

### 6.2 真实 report copy replay

复制一次真实 promotion certificate/report：未修改的隔离副本被 checker 接受；对隔离副本追加一个空白字节后，production checker 以 live-evidence hash drift 拒绝。原始 run 未修改。这是一次 controlled replay，不是自然运行中的 stale-acceptance rate，也不能外推误杀率。

### 6.3 已观测门耗时

| Gate | 墙钟时间 | 解释 |
|---|---:|---|
| Stage-3 multilayer pipeline check | 0.101 s | 一次 checker invocation |
| Stage-6 exact-board VCS compile/elaboration | 62.696 s | 一次 compile-only wrapper invocation |
| Stage-6 VCS（Attention patch 后） | 78.775 s | 不同 input/source fingerprint 的另一次 invocation |
| Stage-7 generated-kernel OOC Vivado synthesis | 4,786.196 s（79.77 min） | 一次综合尝试；不是 place-and-route |

把 0.101 s、62.696 s 和 4,786.196 s 相加得到 4,848.993 s，只是把不同 source revision 的观测做算术场景。由此得到的 98.707% 或 99.998% 节省比例不是配对测量，不能写成 targeted-vs-full revalidation speedup。要支持效率因果结论，必须在同一源码快照、同一输入和同一硬件候选上分别运行 targeted 与 full policy。

材料：[2B cost table](../experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/2B_EVIDENCE_AND_COST_TABLE_20261030.md)、`2b_gate_timing_20261029/result.json`、`2b_stale_report_replay_20261029/result.json`。

## 7. 已确认的问题与已排除的误判

### 7.1 已确认的阻塞

1. **T1–T6 的 Stage-4 静态 schedule-risk gate**：不是候选物化失败；是 `cyclic_stream_wait` 将候选标记为不可行，导致没有下游数据。
2. **reuse=1 补充组的板级证据缺口**：主要是 candidate-local `board_simulation_manifest.json`、AXI-DDR preflight、DDR refill/weight-bias stream、配置 transport 和 layer scheduler 映射不完整。
3. **2A runtime 证据缺失**：compile-only 不产生 `progress_event_log` 或 `board_simulation_executed_manifest`，旧 runtime CCTG builder 因证据不足返回 `insufficient_evidence`。
4. **Activation 节点命名歧义**：pipeline node 与 model-op node 同时被候选匹配，不能当作唯一根因定位。
5. **2B 缺配对计时**：现有门耗时不是同一 source/input 的 targeted/full 实验。

### 7.2 不应再采用的解释

- T1–T6 的返回码 2 不能解释成 VCS 或 Chisel 编译错误。
- `cyclic_stream_wait` 静态检测不能解释成已完成的 RTL deadlock proof。
- T7 B0 的一次 adapter 修复不能解释成 graph-guided CCTG localization。
- `vcs_compile_only` 通过不能解释成数值功能、周期计数、runtime DDR 计数或上板成功。
- 不同 run、不同源码指纹的频率/耗时不能拼成配对收益。
- `new_core_method_eval.md` 中的包装性建议、目标数字和“应当 8/8”的计划不是观测结果。

## 8. 目前论文中可安全使用的结论边界

可以安全写：

1. ACCORD 在一个真实 GPT-2 Medium seq32 前向 run 中维护了跨阶段图，并将模型顺序关系扩展为 stream 依赖；Stage-3 的 11 项 pipeline checks 全部通过。
2. 参数变更实验中，12 个 preregistered ACCORD/B0 Stage-4 candidate materialization 均通过，但下游传播指标因静态 schedule-risk gate 而未测得。
3. 静态 compile-diagnostic probe 能在绑定 SACG snapshot 的 Attention 注入错误上得到唯一 pipeline 节点候选；Activation probe 显示了命名歧义这一真实限制。
4. evidence binding fixture 和一次 hash-drift replay 展示了证据变化可被检测；已测 gate 时间说明不同验证层的成本数量级不同。

不能安全写：

- 参数传播准确率、CCTG 图引导根因定位成功率、targeted revalidation 效率收益；
- 8/8 故障定位、8/8 修复或 100% scope-safe repair；
- runtime deadlock 被排除、完整 RTL 功能正确、周期精确或上板运行成功；
- ACCORD 相对 B0 的性能、资源或编译通过率优势；
- targeted policy 比 full rerun 的实测 61×/77× 加速。

## 9. 下一步最小可执行实验排序

按依赖和成本排序，建议只做以下补齐，不重复已经证明无新增信息的候选：

### P0：补齐 1B 的同候选配对

1. 保留原始 T1–T6 记录，不覆盖它们。
2. 新建明确标注的评估分支：将 `cyclic_stream_wait` 作为 schedule-risk warning 记录，而不是伪装成 runtime pass；或者以 preregistered 允许的 reuse 值重新定义候选范围。该分支必须单独标出 policy。
3. 对每个 T1–T6 运行 ACCORD/B0 的 Stage-4→5→6，生成相同 source/input fingerprint 的 artifact manifest。
4. 只计算实际完成的指标：affected artifact sync、unrelated artifact preservation、contract pass、VCS compile pass。未运行项继续记 `not measured`。
5. R1–R4 只有在 board manifest/AXI-DDR preflight 生成能力真正改变后才恢复 Stage-6；不要对相同缺口重复 loop。

### P1：建立可复现的 2A 编译/时序切片样本

1. 为每个受控 failure 固定 SACG SHA、source SHA、tool log SHA 和预注册 ground-truth node。
2. 继续使用静态 compile/contract/timing projection 时，必须把它命名为 static dependency projection；若要声称 runtime CCTG，必须补真实 runtime event/manifest。
3. 至少完成若干独立样本的 repair→same-gate revalidation；统计 hit、ambiguous、miss、scope violation 和 revalidation pass，不能把候选集命中写成 top-1 命中。
4. 修复 Activation 节点命名歧义后再增加样本，避免重复采集同一失败 episode。

### P1：2B 同源码 paired timing

1. 从一个固定 source snapshot 复制 targeted 和 full 两份工作目录。
2. 对同一个 mutation，分别执行 targeted policy 和 full policy，记录相同机器、相同工具版本、相同输入的墙钟时间。
3. 至少重复若干次并报告中位数/离散度；把 Stage-7 OOC synthesis 与 P&R 明确区分。
4. 继续保留 hash-drift replay 作为证据完整性例子，不把它扩展为误杀率。

### P2：1A 配对 cohort

若论文必须呈现传播准确率或 first-pass integration rate，再构造固定输入的 ACCORD/B0/flat-history cohort，并预先定义受影响节点、无关节点和 gate 通过条件。单个 forward run 不能补足该统计量。

## 10. 产物索引

- 机制计划与口径：[`new_core_method_eval.md`](new_core_method_eval.md)
- 1A/1B 主 run：[`method1_seq32_20261029/`](../experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/)
- 1B 补充 run：[`method1_seq32_20261029_supplement/`](../experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/)
- 2A/2B run：[`method2_2a_2b_20261029/`](../experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/)
- 静态切片实现：[`sacg_cctg_causal_slice.py`](../framework/sacg_cctg_causal_slice.py)

本文是评估快照，不替换上述原始报告；后续新实验应新建带时间戳的 run 目录，并在此文档末尾追加状态，而不是覆盖历史证据。
