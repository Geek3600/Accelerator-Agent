# SpatialAccAgent 当前框架与实验进展

> 状态快照：2026-10-29 10:37 CST。本文面向实验计划评估和论文写作；它记录本轮可核验的代码、run 与工具证据，不覆盖或替代 [`agent_framework_design.md`](agent_framework_design.md) 中的完整方法说明。

## 1. 当前结论

SpatialAccAgent 已有一条完整的自动设计控制流实现：从模型、量化和板卡输入出发，建立 SACG，绑定可信算子/IP 模板，规划空间流水线，运行 DSE，生成 Chisel/RTL，执行验证与 repair，再进入 Vivado 综合及 run-local 时序优化。框架的核心不是让 LLM 自由写 RTL，而是让 LLM 在模型语义、SACG 契约、模板、候选参数和真实工具反馈约束下作结构化决策。

当前可以确认的运行事实：

- GPT-2 Medium、24 层、batch=1、seq=32、W4A8、VU9P、512-bit DDR 的三个上游 LLM run 共用同一实验 envelope。GPT-6.1 和 DeepSeek 已分别得到 155.448 MHz、152.742 MHz 的 Vivado **综合后时钟估计**；Claude 当前最佳已完成候选是 27.376 MHz，新的 `IntegerVectorNorm` 时序修复正在综合。
- 三条线的资源来自生成内核综合报告；吞吐字段使用 DSE 结构周期估算换算。它们不是 RTL 仿真计数器、place-and-route 结果或上板测量。
- 新核心机制实验尚未按原计划全部完成。当前有真实 SACG 前向轨迹、若干 Medium Stage-4/5 ACCORD/B0 成对试验、evidence-binding 确定性 fixture，以及一个真实 compile-fail-to-pass 单案例；这些材料的证据等级和适用主张不同，不能合并成一个“机制实验已完成”的结论。
- 论文当前最重要的证据缺口是：1A 的三组受控首轮比较、按 seq32 Medium 合法 DSE 候选重新设计并计分的 1B、带 ground truth 与有效 CCTG 诊断的多样本 2A、以及真实 EDA 重验耗时对照 2B。

## 2. 当前受控设计条件

| 维度 | 当前实验条件 |
|---|---|
| 目标模型 | Hugging Face `openai-community/gpt2-medium`，24 decoder layers，hidden=1024，16 heads，MLP=4096 |
| 工作负载 | batch=1，sequence length=32；不混用 GPT-2 Small 或 seq=16 结果 |
| 数值格式 | signed W4 权重、signed A8 激活、INT32 累加与 bias、integer DSP datapath |
| 板卡 | MIMIC Computer v6.0，part `xcvu9p_CIV-flgb2104-2-i` |
| 内存/接口 | 512-bit DDR refill；完整模型权重位于 DDR；片上为有界工作缓存，含 active/shadow 预取与 activation ping-pong |
| Stage-6 当前运行 gate | `vcs_compile_only`。它证明当前证据绑定的设计可编译/elaborate/link，不证明仿真运行、数据有效、无死锁或功能数值正确 |
| Stage-7 当前频率目标 | source-bound Vivado post-synthesis Fmax >= 150 MHz；本目标不等价于布局布线时序闭合或实板频率 |

固定设置依据：[`task_spec.md`](../accagent/experiments/gpt2_medium_seq32_20261027/task_spec.md)。

## 3. 框架状态模型与职责边界

### 3.1 一次 run 的状态

框架将运行状态组织为：

```text
S_t = (G_t, A_t, R_t)
```

- `G_t` 是 Spatial Accelerator Contract Graph（SACG），记录模型/硬件设计节点、依赖边、约束、不变量和证据关联。
- `A_t` 是 artifact 集合，包括规范化输入、模板绑定、pipeline plan、参数绑定、Chisel/RTL、验证计划、板级适配与后端材料。
- `R_t` 是运行证据，包括 LLM 结构化响应、checker、命令、工具日志、VCS/Vivado 报告、repair episode、flow event 和 checkpoint。

阶段迁移应由结构化状态、checker 和真实工具结果共同决定。LLM 输出本身不能代替编译器、VCS、Vivado 或硬约束检查。

### 3.2 SACG 与 CCTG

SACG 是跨抽象层的设计合同图，不只是模型计算图或 RTL module graph。其节点覆盖模型/shape/numeric policy、template/IP、PE/处理阵列、pipeline stage、stream adapter、DDR/cache/runtime、verification 和 backend/deployment；边表达 semantic、shape、numeric、stream/ready-valid、AXI beat、memory layout、liveness、control、board runtime 与后端依赖。

典型不变量包括：W4A8 与整数 DSP 语义保持；完整权重在 DDR、有界权重缓存参与当前层计算和下一层预取；512-bit refill 与缓存布局一致；不同 token 可在算子级流水中重叠且 ready/valid 可回压；exact-board AXI/DDR wrapper 不被替换成简化接口；参数改变后受影响的 artifact 和检查必须重新验证。

CCTG/SACG causal slice 的目标是把真实失败证据映射到违反的合同、候选根因边界和允许修改的范围，再交给 repair agent。仅有某个模块编译失败、或事后知道哪个文件被改过，并不自动构成“CCTG 已定位根因”的证据；必须能在同一 episode 中找到 failure record、图切片/根因候选、repair action、source patch 和重验结果。

### 3.3 Agent 与真实工具

顶层 `TopAgent` 负责启动/恢复 run、读取阶段状态、调用阶段 agent/tool、记录 flow event 并决定继续当前阶段、repair 或进入下一阶段。需要跨专业工作时，team layer 按任务拆解角色、交付和 checker。LLM 负责解释非结构化输入与工具反馈、提出有 schema 的设计/修复动作；确定性代码负责参数和格式处理、contract checking、源码事务校验、工具执行及证据收集。

常用实现入口：

| 职责 | 主要模块 |
|---|---|
| 控制器、阶段恢复和 run 状态 | `accagent/framework/agent.py`, `agent_common.py`, `flow_action_handoff.py` |
| LLM provider 与统一请求 | `llm_config.py`, `llm_io.py`, `stage_llm.py` |
| 输入规范化与模型/板卡事实 | `stage_input.py`, `case_adapter.py`, `case_adapters/` |
| SACG 建立、持久化与约束传播 | `stage_constraints.py`, `sacg_store.py`, `sacg_utils.py`, `trace_identity.py`, `contract_identity.py` |
| 模板、pipeline、参数/DSE | `stage_templates.py`, `stage_pipeline.py`, `stage_params.py`, `dse_candidates.py`, `dse_estimator.py`, `dse_ledger.py`, `dse_calibration.py` |
| 生成、验证计划、证据合同 | `stage_code_generation.py`, `stage_verification_plan.py`, `stage_verification.py`, `verification_evidence_contract.py` |
| Stage-6 诊断与 repair | `stage_debug_loop.py`, `stage_repair.py`, `stage_repair_execute.py`, `sacg_cctg_causal_slice.py` |
| Vivado 后端和时序优化 | `stage_backend.py`, `codegen_source_repair.py` |

源码文件较大且部分职责集中，特别是 `stage_repair_execute.py` 同时包含多层验证链、repair execution、证据处理和恢复路径。论文描述应概括真实职责，不宜把模块数量本身当作方法贡献。

### 3.4 Stage agent 与 team layer

单个阶段通常调用专职 agent，并要求结构化 JSON 输出，包含摘要、证据引用、约束更新、下一动作和验收 checker。当前阶段角色主要包括：

| 角色 | 责任 |
|---|---|
| `model_config_agent` / `task_card_agent` | 抽取模型事实、目标 DUT、输入输出与运行边界 |
| `numeric_policy_agent` | 规范化精度、符号、scale、舍入、饱和和 accumulator policy |
| `board_profile_agent` / `design_space_agent` | 抽取 part、AXI/DDR、时钟复位、板级边界及合法搜索域 |
| `sacg_builder_agent` | 从输入事实建立模型/硬件契约图及来源关系 |
| `template_selection_agent` / `pipeline_architect_agent` | 选择可信 operator/IP 实现并规划算子级 stream graph |
| `dse_parameter_agent` | 在合法候选域内选择物理参数并解释性能/资源权衡 |
| `code_generation_agent` / `verification_planner_agent` | 物化硬件包并生成分层验证计划/证据合同 |
| `evidence_classifier_agent` / `repair_agent` | 分类当前工具证据、提出有边界的修复动作 |
| `backend_closure_agent` | 解释 Vivado 报告、选择 timing/QoR 后续操作 |

Team layer 由 `team_decomposer` 按任务按需拆分专家，而不是要求每个阶段固定并行所有角色。常用专家域为 `model_shape`、`numeric_template`、`data_memory_runtime`、`verification_repair` 和 `implementation_deployment`。子任务带有期望 artifact、验收 checker、handoff 和并行组；无依赖任务可并行，有依赖的审计工作在前项完成后执行。team 输出和事件保存于阶段目录的 `team/` 下，便于复现实际角色、prompt 和聚合结果。

### 3.5 LLM 消息、恢复与持久化

`llm_config.py` 解析 provider/model/wire protocol 配置；`llm_io.py` 与 `stage_llm.py` 统一发请求、记录 provider/model、耗时、重试状态和 schema 响应。请求上下文包括当前阶段任务、SACG/开放约束、材料摘要、工具证据、输出 schema 和禁止越界事项。网络 502/503、瞬时容量错误应在当前 stage 重试；不属于硬件失败，不能据此回退设计流程。

每个 run 的 `agent/flow_state.json`、`flow_events/`、阶段报告和 checkpoint 记录当前在哪一步、为什么迁移/重试、消费了哪份 SACG 和产物。LLM prompt/result、工具命令、日志、checker 和 source archive 写到持久 run/experiment 目录；`/tmp` 仅适合可重建的锁或短暂传输临时文件。对论文有用的最小 episode 是“输入/失败证据 → agent action → source/artifact 变化 → 实际 gate → 结果”，而不是只有最终成功文字。

## 4. Stage 0–7 实际流程

公开阶段编号为 Stage 0–7。内部的子步骤不会产生新的公开 stage 编号。

| Stage | 主要工作与产物 | 主要 gate / 当前注意点 |
|---|---|---|
| 0 输入准备 | 从模型配置/权重、用户任务、数值策略、板卡样例、工具和目标中建立 machine-readable task card 与 board/model profile。 | 事实需有来源；shape、量化、板卡和工具冲突应被发现，不应以另一模型默认值补齐。 |
| 1 SACG 抽取 | 把 decoder block 拓扑、shape、numeric、stream、memory、runtime、verification 和 backend contract 转成初始图。 | 保存来源和初始图；本阶段有真实 GPT-2 Medium seq32 状态快照，见第 8 节。 |
| 2 模板/IP 绑定 | 把模型算子语义绑定至可信 Chisel/operator 模板、整数 DSP 与 FPGA IP。 | 保留模板 provenance、位宽、signedness、量化/舍入和端口契约；不是任意 RTL 生成。 |
| 3 空间 pipeline 规划 | 将 transformer block 展开成 operator-stage 流水，规划 ready/valid、FIFO、缓冲和跨 token 复用。 | 目标语义是不同 token 在不同算子级时间重叠、由 backpressure 正确调度，不是整序列 barrier。当前 `vcs_compile_only` 不能证明运行时确有这种重叠。 |
| 4 DSE/参数绑定 | 在合法参数域内搜索阵列、lane、tile、FIFO、bank、缓存/DDR 等参数；用资源/周期 proxy 排序并写入绑定。 | `selected_architecture.json` 应与实际生成 RTL 参数一致。Proxy 只供估算/排序，不能当作综合资源或 RTL 精确周期。 |
| 5 Chisel/代码生成 | 物化模板与参数、生成 DUT/顶层/脚本和 IP、做增量编译和结构/contract 检查，并准备验证 artifacts。 | 通过表示设计可被生成及 elaboration，不等于 Stage-6 仿真或板级功能通过。 |
| 6 分层验证与 repair | 设计目标为 leaf operator → connected kernel → exact-board AXI/DDR wrapper 的逐层验证；失败时收集工具证据、形成 diagnosis/scope、patch，再同层重验。 | 当前三条 seq32 设计采用 `vcs_compile_only`：不运行仿真，不产出有效数据或完整 runtime CCTG；论文需将其写成 compile/elaboration/link 证据。 |
| 7 Vivado/QoR 与 timing loop | 真实综合、报告资源和关键路径；run-local 修改源代码，重新编译/验证/综合，并将每个 QoR 与源码 archive 对齐。 | 当前可引用的是 post-synthesis timing/resource；尚不能称为 place-and-route、板上频率或板上性能。 |

阶段实现与更多细节见 [`agent_framework_design.md`](agent_framework_design.md) 第 6–18、24 节。论文中的“完整功能正确/板级闭环”表述必须以实际执行的 gate 为准，不能仅引用计划文件或 verification plan。

### 4.1 Repair/evidence 的实际决策顺序

典型单轮修复从当前真实工具输出开始：分类失败类型及边界 → SACG/CCTG 形成违反合同和可疑上游范围 → repair agent 提交结构化 patch/action → 执行器检查 schema、作用域和源码事务 → 对修改后的源重跑当前层所需 gate → 保存可复核的 outcome。若工具诊断不足，系统需要基于当前 frontier 选择观测信号或更小范围 replay；经验库只提供相似故障先验，不直接套用旧 patch。

证据失效判断服务于“哪些旧验证仍适用于当前 artifact”；它不是硬件架构变化，也不应独自触发 Stage-0/1/4 回退。源码改变后需要刷新该源码对应的 gate，是为了证明当前版本仍可构建；图节点/物理参数只有在当前设计证据确实指出它们不满足目标时才应改变。一次修复的论文证据至少应保留同一 episode 的 failure record、因果分析（如声称 graph-guided）、修复动作、source diff、重验输入和真实返回状态。

## 5. 硬件架构和性能估算口径

当前目标硬件采用 W4A8 integer-DSP datapath。完整层权重由 DDR 提供，片上存储只承担有限工作集；active cache 服务当前层，shadow cache 可预取下一层，激活侧使用 ping-pong 缓冲。DDR refill、宽数据写入缓存、并行读出、token 驻留复用和流水 overlap 都是架构/DSE 的性能因素。它们不是“全模型权重存 BRAM/URAM”。

当前 GPT-2 Medium seq32 选定候选（GPT-6.1 run 的 `selected_architecture.json`）：`compute_array_rows=16`、`compute_array_cols=32`、`lanes=16`、`cross_token_reuse_tokens=16`、`cache_refill_data_width_bits=512`、`cache_tile_count=2`、`cache_tile_words=256`、`fifo_depth=64`、`activation_banks=2`、`compute_backend=integer_dsp`。权重物理角色由 DDR/片上缓存映射合同管理；Vivado 的最终资源报告才是实际资源口径。

当前合法搜索域还包括 lanes 8/16、PE rows 4/8/16、cols 4/8/16/32、FIFO 深度 32/64/128、activation banks 2/4、受物理布局约束的 weight bank/tile 组合，以及由 schedule/capacity 约束的 cross-token reuse。DSE 的目标是在 VU9P 硬限制下提高吞吐，不是单纯选 LUT/URAM 最少的候选；候选只有在真实地绑定到 RTL/XPM/DSP/AXI/layout 后才算物理参数。当前 seq32 DSE 记录包含 360 个 feasible candidates，但可用于实验任务的“只改一个字段”备选取决于具体当前候选，并非所有字段都能独立变化。

当前 `performance_tokens_per_second` 的计算口径为：

```text
estimated_tokens_per_second
  = processed_tokens * synthesized_Fmax_hz / DSE_estimated_total_cycles
```

其中 32 个 token 和 Fmax 取自当前实验设置/综合报告，周期来自 `dse_structural_cycle_estimate`。当前结果中的 14,969,236 cycles 是估算，不是 RTL 仿真 counter，也不是板上计时。由于估算模型对调度边界、DDR 与运行时 backpressure 仍有假设，论文应把“综合频率”和“估算吞吐”分别标注。

## 6. 三条 GPT-2 Medium seq32 时序线

共同条件为第 2 节列出的模型、W4A8、VU9P、512-bit DDR、Stage-6 compile-only。三条 `selected_architecture.json` 的 `candidate_fingerprint` 均为 `31c1198760c03c7072c82cbb38fe8498922aef8d4aa17dbcf070e3818ebab8bc`，核心候选参数也相同（rows=16、cols=32、lanes=16）。因此当前横向对比固定目标模型、板卡、量化和 DSE 候选，只改变上游 LLM。表中的频率、资源和 TPS 绑定于每行对应的 source archive。功耗字段为空；三个 run 均为 `measurement_scope=generated_kernel_synthesis`。

| 上游 LLM | 最新已完成 archive | Post-synthesis Fmax / WNS | 资源 LUT / FF / DSP / URAM / BRAM36 / BRAM18 | TPS 字段 | 状态 |
|---|---|---:|---:|---:|---|
| GPT-6.1-Sol | `46b2af1f0573493a7a39fb2e39e3b0c60d72e824a171ea80784d53ad85bba0f9` | 155.448 MHz / +0.234 ns | 634,930 / 197,332 / 4,232 / 208 / 180 / 12 | 332.30 estimated tok/s | 已达到 150 MHz 综合目标；非 place-and-route 或上板结果 |
| DeepSeek-V4-Pro | `f6c22379ec95b77f5374384554e0256523a3ab9709bf3b1cfb5eb41f5200f8f9` | 152.742 MHz / +0.120 ns | 614,273 / 177,448 / 3,074 / 208 / 180 / 12 | 326.52 estimated tok/s | 已达到 150 MHz 综合目标；非 place-and-route 或上板结果 |
| Claude Opus 5 | `7a0ff04e48380b8ee833815bd3476e8a09b0ae0ccf787bd5361154caced9b0ae` | 27.376 MHz / -29.861 ns | 652,234 / 162,054 / 4,130 / 208 / 180 / 12 | 58.52 estimated tok/s | 未达目标；新时序修复的综合正在运行 |

**Claude 当前增量。** 已完成候选的关键路径是 IntegerVectorNorm 的 `denominatorReg` 到 `outputReg` DSP 输入，报告为 262 逻辑级、36.196 ns 数据路径延迟。Claude Agent 对 run-local `Norm.scala` 提出 3 个中间寄存阶段 `sRecipPipe1/2/3`；增量 Scala compile、contract check、两种 AXI/DDR 顶层 elaboration 返回 0。随后当前源码的 exact-board `vcs_compile_only` 也通过，证据为 `verification/vcs/case_board_vcs_functional.json`，flow event 337 标记 `proceed_verified_stage6`。该 gate 仍只是 compile/elaboration/link，不包含仿真。

本轮 agent framework 的通用 timing prompt 已加强：`codegen_source_repair.py` 会把 Vivado timing endpoint 映射为当前源码中的候选声明、行号、所属类和局部源码上下文；当多个实现含同名信号时，要求 LLM 结合层级/配置选目标。提示还明确：在未切分的组合算子前后单纯加寄存器，不能缩短该算子内部的组合关键路径。改动是 run-local repair 能力增强，没有改共享硬件模板；`tests.test_codegen_source_repair` 6 项通过。

远端 Vivado 新 attempt `attempt_1576525_1793239275387074203` 正在 RTL Optimization/DSP report 阶段，尚未生成新 timing 报告。10:37 CST 远端主进程 PID 48006 已运行约 37 分钟，CPU 约 100%、RSS 约 5.28 GB；attempt 目录尚无 timing/utilization report，Vivado 日志最后仍是 XPM RAM 时序提示，没有报错。尝试复用旧 attempt `1267373` 的报告时，源码/RTL fingerprint 不匹配而被拒绝；旧 Fmax 没有绑定到新源码。当前唯一可引用的 Claude 数字仍是 27.376 MHz。`backend_board_report.json` 的汇总仍滞后并保留了先前的 `stage6_refresh_required` 状态；更新判断以较新的 Stage-6 flow event 337 和对应 VCS artifact 为准。父 Agent 沿原 run 继续时序优化，没有重启整个设计流程。

上游 API 间歇失败、repair source anchor 不匹配和框架/证据状态问题，属于 agent/tool 流程问题；它们不应导致丢弃已有设计候选或无证据地回退到 Stage 0–5。Stage 7 每轮应保存 source archive、patch、当前源码 compile/VCS 证据、Vivado report、Fmax/资源与晋级决定。

## 7. 核心机制实验计划与实际证据

原始实验定义在 [`new_core_method_eval.md`](../accagent/docs/new_core_method_eval.md)。该文件中出现的 `N=24/30`、`M=36/40`、`2.5x–4.0x`、预期的高准确率/低修复轮次和绘图曲线均为**计划建议或示例主张**，不是已有结果。

| 实验 | 原计划要求 | 当前实际证据 | 当前能支持的表述 |
|---|---|---|---|
| 1A 前向一致性 | 同一任务三配置（Unstructured History、Flat Config、ACCORD），冻结首次 Stage-7，统计四类跨阶段违例及 first-pass integration rate。 | GPT-2 Medium seq32 有真实 Stage 0/1/2/3 SACG/状态快照：Stage 1/2/3 ready，相关图边数 7/7/18，记录在 `core_method_1b_prepare_20261029/forward/observed_results.json`。没有三配置受控运行、违例计数或首次 Stage-7 通过率。 | 可作为 ACCORD 单组前向传播的真实案例/图示材料；不能称为 1A 对照结果或 DCG 降低违例率的定量证据。 |
| 1B 变更传播 | N=24/30 个有 ground truth 的设计变更任务，计算受影响文件/检查 Recall、Precision、unrelated preservation 和 Pass@1。 | GPT-2 Medium seq16 旧实验中 explicit lanes、inferred lanes、cross-token reuse 的 ACCORD/B0 成对 Stage-4/5 都完成；来源为 `mechanism_pairs_retry_20261026/execution_summary.json`。不能转标为 seq32。当前 seq32 有 360 个 feasible DSE 记录；单字段合法备选包括 rows 4/8、cols 4/8/16、FIFO 32/128、activation banks 4、reuse 4/8。旧的五类 seq32 task 过滤器均未找到可执行备选，因为其键约束与当前合法候选域不匹配；cache tile 独立变化缺失。 | 可说明旧 seq16 配对流程曾跑通 Stage-4/5；当前 seq32 候选域支持重构小规模 pilot。不能宣称 N=24/30、seq32 参数传播召回率或 Pass@1 已测出。 |
| 2A CCTG 定位/限界修复 | M=36/40 个跨阶段故障快照，标注根因节点和修复范围，比较 local repair、unbounded tracing、ACCORD。 | 唯一可复用真实 case 是 Gemma compile error → Agent 修改 `compute_slot.sv` → exact-board VCS compile-only pass（33 modules）。同一 episode 的 `failure_localization.json` 为 `verification_capability_gap`，`failure_record_count=0`、无 failed boundary、root candidate 或有效 causal slice。 | 可报告为 compile-fail-to-compile-pass 单案例；不能报告 CCTG root-cause accuracy、causal repair gain、多样本成功率、运行时死锁修复。 |
| 2B evidence invalidation / targeted revalidation | 三策略比较 stale evidence、full rerun 与 targeted rerun；测 false closure 和真实工具总耗时。 | GPT-2 Medium evidence-binding E1–E4 deterministic fixture 4/4 pass；false invalidation=0、stale-evidence acceptance=0。Small 也有各 4 个 fixture pass。Runner 明确声明 no Agent/VCS/Vivado/RTL simulation/board execution。 | 可作为 evidence-contract 实现的 mutation/unit-test 证据；不能外推真实 false closure rate=0 或 2.5x–4.0x EDA 节省。 |

### 7.1 已有局部运行和测试

- 旧 Medium Stage-4/5 ACCORD/B0 pair：explicit lanes、inferred lanes、cross-token reuse 各一类成对任务完成；其目标规格为 seq16，不能与当前 seq32 QoR 混合。完整摘要：[`execution_summary.json`](../accagent/experiments/gpt2_medium_20261026/mechanism_pairs_retry_20261026/execution_summary.json)。
- Medium evidence-binding fixture：4/4 pass，false invalidation=0、stale evidence acceptance=0；详见 [`summary.json`](../accagent/experiments/gpt2_medium_20261026/evidence_binding_medium_20261027/results/summary.json)。
- Gemma B2 修复案例：只能称为 compile-only 单案例。完整边界和产物见 [`experiment_manifest.json`](../accagent/experiments/accord/results/cctg_b2_prompt_clean_20261024T1105+0800/experiment_manifest.json)。
- `python -m unittest tests.test_sacg_cctg_causal_slice -v`：5/5 pass；`python -m unittest tests.test_verification_evidence_contract -v`：26/26 pass。这些是实现级测试，不是机制效果 benchmark。
- 1B 的 seq32 准备文件 [`status.json`](../accagent/experiments/gpt2_medium_seq32_20261027/core_method_1b_prepare_20261029/status.json) 只表示旧五个变更模板没有匹配到合法候选，不表示 Medium 没有任何设计变化空间。独立候选检查已找到其他单字段合法变化，说明需要调整实验任务定义/runner 过滤器，而不是借用 Small 值或放宽硬约束。

## 8. 对实验计划的针对性调整建议

以下是为了让计划与现有可运行流程和证据边界一致的建议；本文件没有替用户改写 [`new_core_method_eval.md`](../accagent/docs/new_core_method_eval.md)。

1. **把 1A 的当前结果降为 descriptive case，不虚构缺失的两个对照组。** 若必须量化 DCG 贡献，应使用同一 GPT-2 Medium seq32 输入，固定工具/板卡/参数域，分别运行 ACCORD 与去边/去传播 profile，并只统计真实首次集成 gate 的 contract/VCS 结果。若来不及完成三臂，就把论文主张限制为真实 SACG 前向追踪和 checker 设计，不给 violation-rate 数字。
2. **把 1B 先改成 N=6 seq32 pilot。** 从已存在的 360 个 feasible candidate 中选至少 6 个相互独立的单字段合法变更（row/column parallelism、FIFO depth、activation bank、cross-token reuse 等），为每例预先登记 expected changed nodes/files/checks，再用相同输入做 ACCORD/B0 Stage-4/5 配对。报告样本数、参数合法性、affected-file/check precision/recall 和 Pass@1；若没有独立 ground truth 或未执行同层重验，只报告流程观察，不套用原计划 N=24/30 的 benchmark 结论。避免把同一个参数候选复制多次当独立样本。
3. **将 2A 范围收窄到当前可观测的 compile-time failure。** 可以另建带真实 VCS diagnostic、已知 source/module ground truth 的小规模 compile-failure corpus，比较 local-source context 与 SACG/CCTG-guided diagnosis，并记录修复 patch 和 compile-only 重验。当前没有 runtime trace，因此本轮不纳入数据错误、FIFO deadlock、板级运行时故障；没有真实图切片的 Gemma B2 只做案例背景，不作 CCTG 定位计分。
4. **将 2B 拆成两个 claim。** 现有 E1–E4 只支持“revision-bound evidence contract 能对指定 mutation 作 stale/reusable 判定”；要声称真实重验时间节省或零假闭环，必须另跑带相同源码 mutation 和同一 checker 集的 targeted/full-recheck 对照并记录墙钟/工具耗时。不能用 fixture 的零计数替代运行时假闭环率。
5. **从正文和图表中移除计划文案里的预设结果。** 在实际完成前，不写死 2.5x–4.0x 节省、高根因准确率、修复迭代下降、单调收敛曲线或 WNS 改善数字。计划中的示例应明确标为示意值，不能画成观察数据。

## 9. 当前证据等级和不应混写的数字

| 标签 | 代表什么 | 当前例子 | 不代表什么 |
|---|---|---|---|
| `implemented` | 框架代码/contract/runner 中存在该逻辑 | SACG store、repair scope、revision-bound evidence contract | 该机制已在受控对照中获益 |
| `unit-tested` | fixture/test 通过 | E1–E4 mutation、CCTG causal-slice tests | Agent 实际定位能力或 EDA 时间节省 |
| `compile-verified` | 对具体 source binding，编译/elaboration/link gate 返回成功 | 三条设计的 `vcs_compile_only` policy；Gemma repair 单案例 | 仿真 PASS、完整模型运行、非零输出或数值正确 |
| `synthesis-measured` | Vivado 对具体综合输入报告时序/资源 | GPT-6.1、DeepSeek、Claude 最新已完成 QoR | post-route timing、功耗已知或上板结果 |
| `DSE-estimated` | 参数/周期模型估算 | 14,969,236 estimated cycles 及 TPS 字段 | RTL counter 或 measured latency |

任何论文表格都应在指标旁标出证据级别，并把源 archive、report、参数和周期来源一并保留。尤其不能把 `332.30 tok/s`、`326.52 tok/s` 或 `58.52 tok/s` 简写成“实测吞吐”。

## 10. 论文素材与当前 run 路径

| 用途 | 路径 |
|---|---|
| 完整方法/实现说明 | [`agent_framework_design.md`](agent_framework_design.md) |
| 核心机制实验原计划 | [`new_core_method_eval.md`](../accagent/docs/new_core_method_eval.md) |
| 当前 GPT-2 Medium seq32 固定任务设置 | [`task_spec.md`](../accagent/experiments/gpt2_medium_seq32_20261027/task_spec.md) |
| 真实 Stage 0–3 前向图记录 | [`observed_results.json`](../accagent/experiments/gpt2_medium_seq32_20261027/core_method_1b_prepare_20261029/forward/observed_results.json) |
| 当前 seq32 1B 旧任务准备状态 | [`status.json`](../accagent/experiments/gpt2_medium_seq32_20261027/core_method_1b_prepare_20261029/status.json) |
| Medium 机制迁移/候选限制说明 | [`medium_mechanism_inventory.md`](../accagent/experiments/gpt2_medium_20261026/medium_mechanism_inventory.md) |
| Medium E1–E4 结果 | [`summary.json`](../accagent/experiments/gpt2_medium_20261026/evidence_binding_medium_20261027/results/summary.json) |
| Gemma B2 compile-only case | [`experiment_manifest.json`](../accagent/experiments/accord/results/cctg_b2_prompt_clean_20261024T1105+0800/experiment_manifest.json) |
| GPT-6.1 当前 run | `accagent/runs/gpt2_medium_seq32_gpt61_20261027/` |
| DeepSeek 当前 run | `accagent/runs/gpt2_medium_seq32_deepseek_v4pro_20261027/` |
| Claude 当前 run | `accagent/runs/gpt2_medium_seq32_claude_opus5_20261027/` |

## 11. 仍待完成的工作

- Claude attempt `1576525` 已完成并生成当前源码绑定的 report：archive SHA256 `dd1a9cc62a9dd457bb73c40ea7fa471c32763c53297bde6fe903116e1c1a0f34`，Fmax 27.347 MHz、WNS -29.900 ns，未超过历史最佳 27.376 MHz。新路径仍是 LayerNorm 265 级逻辑链。Claude Agent 在原 run 内继续优化，目前上游 API 返回 502，按原配置退避重试；没有切换 provider 或回退早期阶段。
- seq32 1B 的 N=6 配对 pilot 已执行；ACCORD/B0 的 12 个 Stage-4 job 全被当前 schedule eligibility gate 阻断，没有进入 Stage-5/6。继续前需先用通用方式解决 schedule 风险并重跑配对，不能绕过 gate 或把旧 runner 五个固定任务原样重跑。
- 2A 单个隔离 compile-fault pilot 已执行：VCS/analyzer 能识别语法错误，但当前 compile-only 输入不含 CCTG 所需 runtime progress/executed manifest。若严格按原计划继续 CCTG 定位实验，需要能产生该运行期证据且 source/SACG/CCTG 快照匹配的故障样本；重复注入同类 compile-only 语法错误不会补足此证据。
- 若本轮只保留低成本实验证据，则在论文中把 E1–E4 作为 checker contract test，把 SACG 记录与 Gemma 修复作为 case study，把 GPT-2 Medium 多 LLM 时序结果作为跨上游 LLM 的设计结果，并逐项注明综合与估算边界。
- 后续新增实验/时序结果继续写入 [`context_2026-03-27.md`](context_2026-03-27.md)，并将源码、报告、candidate fingerprint 和测量口径成对保存。

## 12. 2026-10-29 11:23 CST 增量

Claude 原 run 的 Vivado attempt `attempt_1576525_1793239275387074203` 已完成 generated-kernel OOC synthesis。当前-source 证据绑定为 synthesis archive SHA256 `dd1a9cc62a9dd457bb73c40ea7fa471c32763c53297bde6fe903116e1c1a0f34`，measurement 为 `backend_board/measurements/dd1a9cc62a9dd457bb73c40ea7fa471c32763c53297bde6fe903116e1c1a0f34/`。该候选 Fmax **27.347061558 MHz**、WNS **-29.900 ns**、最长路径 delay **36.235 ns**、265 级逻辑；路径从 `reciprocalDividendReg_reg[1]` 到 LayerNorm 输出 DSP 输入。资源 LUT/FF/DSP/URAM/BRAM36/BRAM18 为 **654589/161067/4282/208/180/12**。source archive 和 QoR metrics 已绑定，Vivado report SHA256 为 `d5ceb033313d5cc43f55c82bf907af213bcf585cf025280b46cd14ff8baae7d2`。该候选没有超过历史最佳 **27.376259307 MHz**（archive `7a0ff04e...`），最佳记录未被覆盖。吞吐字段 58.460 tok/s 仍由 14,969,236 个 DSE estimated cycles 推导，不是 RTL 周期测量或上板数据。

时序优化仍在 Claude 原 GPT-2 Medium seq32 run 中继续，目标为综合 Fmax ≥150 MHz；没有重启 Stage-0/5 或人工修改 RTL。最新报告显示三段 LayerNorm pipeline patch 没有打断主关键路径；Agent 已进入下一轮修复请求，但截至 checkpoint 上游连续返回 HTTP 502，正在原 provider 上按退避策略重试。

核心机制实验现已启动独立工作批次，实验计划原文未改。1A/1B 在 `eval_audit` 工作线，2A/2B 在 `eval_trace` 工作线；各自需要在隔离目录保存配置、ground truth、执行记录和指标。预期优先完成计划最后行动项规定的 seq32 N=6 参数更新 pilot、M=8–10 编译/接口/时序故障 corpus，以及已有 1A/2B 证据的可追溯汇总。报告须分别标识真实 run、unit fixture、历史 seq16 和新 seq32 pilot，不得合并成统一证据等级。Claude 时序工作由 `claude_timing` 在原 run 继续。本次启动时本地内存为 23 GiB 总量、7.3 GiB 已用、约 15 GiB available；仅增加两条轻量实验编排线，没有新增 Vivado 本地进程。

## 13. 2026-10-29 12:04 CST 增量

### 核心机制实验执行结果

- 1A/1B 的真实执行记录在 [`method1_seq32_20261029/REPORT.md`](../accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/REPORT.md)。1A 有同一 GPT-2 Medium seq32 run 的 Stage 0–3 前向图演进：SACG 边数为 7→7→18，Stage-3 pipeline checker 11 pass、0 fail、0 errors。没有三配置对照数据，因此只作真实前向 case，不报告分类违例率或 first-pass 集成率。
- 1B 已预登记 6 个单字段设计参数变化，ACCORD/B0 共运行 12 个独立 Stage-4 job。候选物理参数物化均通过，但 12/12 在 Stage-4 被 `cyclic_stream_wait` schedule blocker 拒绝；Stage-5/6 没有执行。这不是 VCS 编译失败，也不是 compile pass 率为 0。阻塞由当前 Chisel 模板模式检测产生，未通过 RTL 仿真或形式方法证成真实死锁；没有绕过 Stage-4 gate。
- 2A 的现存 GPT-2 Medium timing-history 不足以生成匹配历史源码、SACG 和 CCTG 的故障样本；当前 GPT-2 Stage-6 是 compile-only，因此没有 runtime trace。`eval_trace` 正在隔离目录构造单个受控 compile-failure pilot，尚未收到真实 VCS/analyzer 结果。计划文件中提到的某个历史 Claude stale-report 拒绝事件未在原始 event 中核实，不直接引用为观察结论。
- 2B 新增一次真实 run evidence replay：[`result.json`](../accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/2b_stale_report_replay_20261029/result.json)。使用 Claude candidate certificate SHA256 `7ba1e3d1ef7485ae30920c8ad304f205111f1f6b3fa00870737af459609961b1` 与其真实 Stage-6 VCS evidence report（原 SHA256 `cc22c6f5474c938e31a74b8ea47c08e72db783d27077439991f8685c69964b69`）。隔离副本基线检查通过；只对副本追加一个空白字节后，生产 `certificate_contract_errors()` 返回 `promotion certificate live evidence hash drift`。原 run 未改动。该项是一个受控 stale-evidence replay，不是自然运行错误率或重验证提速对照。
- 1A/1B 汇总：[`final_report.json`](../accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/final_report.json)；2A/2B 状态：[`README.md`](../accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/README.md)。原始 [`new_core_method_eval.md`](../accagent/docs/new_core_method_eval.md) 保持未修改；其计划中预设的示例数字和历史事件名称不作为实验结果。

### Claude timing run

- Claude 原 run `gpt2_medium_seq32_claude_opus5_20261027` 仍由 PID 366210 执行，Stage-Backend PID 1576489 在原流程中处理当前 Vivado 结果并重试下一轮 LLM 请求。上一轮综合 source archive `dd1a9cc62a9dd457bb73c40ea7fa471c32763c53297bde6fe903116e1c1a0f34` 的 Fmax 为 27.347 MHz，低于未覆盖的最佳记录 27.376 MHz。
- 新一轮 repair 请求仍收到 HTTP 502（返回文字为 upstream access forbidden），transaction 记录为 34 次 attempt、33 次 retry、`inflight`，使用模型 `claude-opus-5`；流程未重启、未切换 provider，也没有产生新 patch。按原配置继续等待/重试。
- 本次读取的实验和 run 报告均为只读；新增内容仅为隔离的 2B replay 脚本/结果和本节记录。1B 参数变更因正常 Stage-4 schedule gate 阻断，后续要继续必须先解决当前设计/检测器对应的通用 schedule 问题，不能把手工越过 gate 的 Stage-5/6 结果混进配对数据。

## 14. 2026-10-29 12:20 CST 增量

### 核心机制实验复核

- 1A 结果不变：真实 GPT-2 Medium seq32 Stage 0–3 SACG 前向记录为 7→7→18 条边，Stage-3 checker 11 pass、0 fail、0 errors；没有对照组，不能据此计算违例率或 first-pass 集成率。
- 1B 六个单字段候选的硬件参数物化均通过，但 ACCORD/B0 共 12 个 Stage-4 作业全部被 DSE schedule gate 拒绝。T1 报告明确指出：`IntegerAttention` 要等 output-projection 结果后才能推进下一 row，而 output `Linear` 要先收集 16-token tile；这被记为 `cyclic_stream_wait`。该结果是静态 schedule eligibility blocker，不是 VCS 编译失败，也没有 RTL 仿真或形式证明它是实际运行死锁。未手动越过 gate，Stage-5/6 未运行。细节与原始记录见 [`method1_seq32_20261029/REPORT.md`](../accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/REPORT.md) 及各 task `dse_constraint_report.json`。
- 2A 隔离 compile-fault pilot 已完成真实远端 VCS 编译和 analyzer 检查。VCS 将受控单行语法错误报为 `vcs_compile_failure`，analyzer 找到首个真实编译错误；CCTG 因 `vcs_compile_only` 没有产生 runtime progress log 与 executed manifest，返回 `insufficient_evidence`，没有因果 frontier、根因节点或修复 episode。未启动 repair。它只支持 compile-failure detection 能力，不支持 CCTG 图定位或 repair-effect 主张。详见 [`compile_fault_pilot_20261029/RESULT.md`](../accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/compile_fault_pilot_20261029/RESULT.md)。
- 2B 新增的单次 controlled live-checker replay 结果保持有效：真实 Claude run 的证书及 VCS 报告复制到隔离目录后，未修改副本通过；只在副本报告追加空白字节后，生产 checker 拒绝并报 `promotion certificate live evidence hash drift`。README 已将旧表述改为“没有自然发生的 stale-report rejection”；本次受控 replay 不表示 Agent 自然事件率、targeted-vs-full 重验时间节省或假闭环率。GPT-2 Small/Medium E1–E4 仍是各 4/4 的 deterministic fixtures，不计作真实 Agent/VCS/Vivado 样本。
- 本轮未重跑已知 pilot、未改实验计划或共享框架。当前 1B 和 2A 的缺口分别是 Stage-4 schedule eligibility 以及 compile-only 缺运行期 CCTG 输入；用绕过 gate 或把静态上下文伪装成 causal slice 都会改变证据性质，因此不这样计分。

### Claude 原 run

- Claude GPT-2 Medium seq32 原 run `gpt2_medium_seq32_claude_opus5_20261027` 的 parent PID 366210 与 Stage-Backend PID 1576489 仍存活。当前可用的最新 Vivado measurement 仍绑定 source archive SHA256 `dd1a9cc62a9dd457bb73c40ea7fa471c32763c53297bde6fe903116e1c1a0f34`：Fmax 27.347061558 MHz、WNS -29.900 ns；历史最佳 27.376259307 MHz 仍保留。尚无新 patch 或综合结果。
- 截至 12:17:54 CST，原 run 内 repair transaction 最新请求仍返回 HTTP 502 `Upstream access forbidden`，按现有 90 秒退避继续重试；transaction 记录 `attempt_count=47`、`retry_count=46`，最后可见请求 attempt 45 已失败并安排重试。没有切换 provider、重启 stage 或手工修改 RTL。
- 12:22:17 CST follow-up：同一 transaction 仍为 `inflight`，累计 `attempt_count=50`、`retry_count=49`；attempt 48 再次返回同一 HTTP 502，已继续安排 90 秒退避。两个进程仍存活，源码 archive 和已完成 QoR 均未变化。
- 12:23:44 CST follow-up：attempt 49 仍返回 HTTP 502，并再次安排 90 秒退避；transaction `attempt_count=51`、`retry_count=50`。parent/backend 仍存活，无新 patch 或 QoR。
- 12:26:41 CST follow-up：attempt 51 仍返回相同 HTTP 502，已继续安排 90 秒退避；transaction `attempt_count=53`、`retry_count=52`。parent/backend 仍存活，无新 patch、综合或 QoR。

### 当前执行边界

- 现有数据可以报告 1A 前向 SACG trace、1B 的 Stage-4 阻塞现象、2A 的 VCS 编译错误识别边界，以及 2B 的受控证据哈希拒绝。按原计划定义，1B 的参数传播配对与 2A 的 CCTG 定位/修复对照尚未完成；因此新机制实验总体仍未完成，不能写成完整对照实验结论。
- 后续仅在同一 Claude run 的重试产生真实修复补丁后继续其原有 Stage-6/7 验证；核心机制线若推进，需先通过原 Stage-4 合法性门，再保存各 profile 的执行与源码绑定结果。原始 [`new_core_method_eval.md`](../accagent/docs/new_core_method_eval.md) 未修改。

## 15. 2026-10-29 13:09 CST 增量

- Claude 原 run 收到上游恢复后的新 `Norm.scala` 修复，当前源码 SHA256 为 `ad986b9ab9e873a67aa6ea6a9b1f7135ac4a476ebe11ad7196d7bc56f97dadc8`。Stage-6 exact-board `vcs_compile_only` 通过，input fingerprint 为 `233f515e005ebb9a8cfea6e0cee4de132a9f14c964c76a3fd037d5e7dbc644ca`；本轮 Vivado attempt `1738110_1793249440199274930` 的 source archive SHA256 为 `1188233dccb136a6c88d2f088a74fe6c47d8e0e0e9db63c8205f541731f4ffd6`，归档内 `Norm.scala` hash 与当前源码一致。远端 Vivado 仍在运行，尚无该 archive 的新时序/资源结果；最近已完成候选仍为 27.347061558 MHz、WNS -29.900 ns，历史最佳 27.376259307 MHz 保留。
- 为 2B 固化 Claude run 中三项真实墙钟记录：Stage-3 multilayer check wrapper 0.101191891 s；Stage-6 exact-board VCS wrapper 62.695989754 s，其中 compile/elaboration 为 58.956681986 s，simulation skipped；Stage-7 generated-kernel OOC synthesis 4,786.196206344 s（79.770 min），对应旧 archive `dd1a9cc6...`。原始 JSON 和 timing/resource report 快照、SHA256 与边界说明在 [`2b_gate_timing_20261029/`](../accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/2b_gate_timing_20261029/)。这些是同一逻辑 run 不同源码版本上的单次耗时，不是 targeted-versus-full 重验对照；Stage-7 是 OOC 综合，不是 P&R/上板。
- 1A/1B/2A 的状态没有变化：1A 是真实前向 trace；1B 六任务 ACCORD/B0 共 12 次 Stage-4 schedule gate 拒绝、未进入 Stage-5/6；2A compile-only pilot 被 analyzer 识别为 compile failure，但 CCTG 因缺 runtime progress/executed manifest 返回 `insufficient_evidence`，没有图定位或 repair 样本。没有绕过 gate，也没有把先前计划中的估计或示例数据写成观察值。

## 16. 2026-10-29 15:29 CST 增量

### Claude 原 run 时序优化

- 原 run `gpt2_medium_seq32_claude_opus5_20261027` 和父 Agent PID 366210 仍在原流程中运行。上一份已完成的 Vivado measurement 绑定 archive SHA256 `1188233dccb136a6c88d2f088a74fe6c47d8e0e0e9db63c8205f541731f4ffd6`，Fmax **26.979630 MHz**、WNS **-30.398 ns**、路径延迟 **36.757 ns / 145 级逻辑**；关键路径从 `maximumScoreReg_reg[1]` 到 `probabilities_01/DSP_A_B_DATA_INST/B[0]`。时序报告 SHA256 为 `9595e2f570134a3205518203de8531cf556eac8d14a2cdb6099ecab5f7ff0aea`。资源为 LUT/FF/DSP/URAM/BRAM36/BRAM18 = **654655/160183/4234/208/180/12**。该值低于历史最佳 **27.376259 MHz**，未覆盖最佳记录。
- Claude Agent 对新 Attention 关键路径的第一份补丁因重复定义 `sSoftmaxPipe3` 及非法枚举算术未通过增量编译，未作为验证通过的候选。Agent 在原 Stage-7 修复源码后通过增量编译和 exact-board Stage-6 `vcs_compile_only`，随后启动远端 Vivado attempt `attempt_1832318_1793258077670432062`；远端进程仍运行，当前没有新综合结果。该 attempt 的结果尚未形成 source-bound QoR，不能从上一候选推断新频率。
- 当前 Stage-6 compile-only 结果：exact-board 顶层 `app_shell_9p_wrapper`，状态 pass，返回码 0，policy `vcs_compile_only`，仿真未运行。Stage-6 外层 real-tool wrapper 为 **78.775 s**，远端 VCS compile/elaboration 为 **74.944 s**；输入 fingerprint `d4c0729d954a59062f3dc204dd66caf21a8d40ee11dd2ba36c95609bc0e56af6`，VCS log SHA256 `072bfa0cdb2a15c4ed747661ca6807950b5f43d4dc5b806dc59c2d50bde54955`，wrapper execution fingerprint `eb6fa8bb3502a24f2d708744358c6aa227e2b0f02d48dbcd121785d652c74e2c`。`Attention.scala` 当前 SHA256 `80955e9c0970e691d2d65c03de1017f12d2ce126e568e5c9669a4500f672e3d2`。这些时间是单次观察，不构成 targeted/full revalidation 对照。

### 框架阻塞修复

- 新 attempt 的 Stage-7 repair 状态读取曾因合法的 null 字段触发框架异常：`incremental_compile=null` 或 `agent_transaction_rejection=null` 时直接调用 `.get()`。在 `codegen_source_repair.py` 中将这两个可选记录归一为空对象；没有改 run-local RTL、共享硬件模板或 agent流程门限。添加 `test_timing_repair_handles_null_compile_and_rejection_records` 回归用例。
- `python3 -m unittest tests.test_codegen_source_repair -v` 通过，7 项通过。修复已被现有 Claude run 的 Stage-7 子进程使用：此前的空值异常不再出现，Agent 能返回“需要刷新当前源码 Stage-6 VCS”的正常 handoff 并继续原流程。

### 新核心机制实验状态

- 1A 仍为单次真实 Stage 0–3 SACG 前向演进（边数 7/7/18，Stage-3 checker 11 pass/0 fail），没有对照组。
- 1B 的 seq32 六任务 ACCORD/B0 共 12 次 Stage-4 都被 `cyclic_stream_wait` 阻止，未运行 Stage-5/6。旧 seq16 lanes 记录没有 VCS；reuse 8→4 配对含额外 cache 参数和不对称 timing repair，因此不作为干净单变量比较。没有绕过 gate，也没有将未测的下游指标记为零。
- 2A 的单次隔离 VCS 编译故障被分类为 `vcs_compile_failure`，但 compile-only 缺 runtime progress log 与 executed manifest，CCTG 为 `insufficient_evidence`；仍无 graph-guided localization/repair 对照或 M=8–10 corpus。
- 2B 在原有 E1–E4 deterministic fixtures（GPT-2 Small/Medium 各 4/4）和受控 stale-report replay 之外，增加一条真实 Stage-6 compile-only wall-clock 观察，见 `method2_2a_2b_20261029/README.md`。它不表示 targeted/full 重验加速比或自然假闭环率。

原实验计划 `accagent/docs/new_core_method_eval.md` 未修改。当前能报告的是真实 gate 与工具观察，核心机制实验整体尚未按文档完成；1B 和 2A 仍有明确缺口。

## 17. 2026-10-29 15:37 CST 增量

### Claude 原 run

- 原 run `gpt2_medium_seq32_claude_opus5_20261027` 继续沿 Stage-7 时序优化推进，没有重启。远端 attempt `attempt_1832318_1793258077670432062` 仍在 Vivado 综合；15:35 CST 检查时远端 Vivado PID 32305 已运行约 20 分钟、CPU 100%、RSS 约 3.9 GiB，日志仍在 DSP/BRAM/URAM 映射阶段，尚无 timing/utilization report。
- 随后确认该 attempt 输入 closure archive SHA256 为 `42f490eca705395cf98336a9ea177ead5392d4e3a8e9d7970f8332bc10c92fc3`，与提交到远端的归档逐字节一致；归档和当前源码中的 `Attention.scala` SHA256 均为 `80955e9c0970e691d2d65c03de1017f12d2ce126e568e5c9669a4500f672e3d2`，`Norm.scala` 均为 `ad986b9ab9e873a67aa6ea6a9b1f7135ac4a476ebe11ad7196d7bc56f97dadc8`。因此待综合候选具有明确 source binding，但综合完成前没有新 Fmax、资源或关键路径结果。
- 目前最近完成的结果仍是 archive `1188233dccb136a6c88d2f088a74fe6c47d8e0e0e9db63c8205f541731f4ffd6`：26.979630 MHz、WNS -30.398 ns；历史最佳 27.376259 MHz 未覆盖。Stage-6 对当前候选的 exact-board `vcs_compile_only` 通过，输入 fingerprint `d4c0729d954a59062f3dc204dd66caf21a8d40ee11dd2ba36c95609bc0e56af6`，wrapper 78.775 s、VCS compile/elaboration 74.944 s，仿真跳过。

### 核心机制实验

- 1A、1B、2A、2B 继续按 `accagent/docs/new_core_method_eval.md` 的原始指标和已执行证据边界统计；原计划文件未改。
- 1B 的 GPT-2 Medium seq32 六个预登记单字段任务已完成 ACCORD/B0 共 12 次 Stage-4 尝试，全部因同一个 `cyclic_stream_wait` 阻塞而未到 Stage-5/6。它是静态 source-pattern schedule gate 结果，不是 VCS 失败或 RTL/formal 运行时死锁证明；未绕过 gate。受影响文件传播、contract pass rate 和 Stage-5/6 Pass@1 仍为未测。
- 已审计历史 seq16 explicit/inferred-lanes ACCORD/B0 Stage-4/5 快照：缺少完整 isolated Stage-6 输入，SACG artifact 路径指向共享 legacy run `accagent/runs/w4a8_20261018_gpt2`，标准 Stage-6 入口可能对错误的共享 run 读写证据。没有在这些目录里直接启动 VCS，也没有用手工编译代替标准 gate。审计记录为 [`NEXT_ACTION_AUDIT_20261029.md`](../accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/NEXT_ACTION_AUDIT_20261029.md)。
- 2A 的隔离 compile-fault pilot 已按标准 exact-board `vcs_compile_only` 执行并识别为 `vcs_compile_failure`；因运行期 progress log 和 executed manifest 不存在，CCTG 返回 `insufficient_evidence`。对仓库现存 GPT-2/Gemma/formal failure-localization 记录的只读检索也没有找到非空根因记录或匹配的 runtime progress/executed manifest。重复 compile-only 故障注入不会生成所缺运行期证据；目前不能报告 CCTG 图定位、根因命中率或 bounded-repair 对照。
- 2B 已有 Small/Medium E1-E4 deterministic fixture 各 4/4、一条真实报告副本的受控 stale-hash replay，以及单次真实 gate 耗时。尚无自然 stale-certificate 拒绝或 targeted-vs-full 重验对照；现有数据不支持其加速比/真实 false-closure 率主张。
- 本轮没有启动新的实验/VCS/Vivado，也没有改变计划、RTL 或共享模板。工作区本地约 15 GiB 可用内存；远端当前 Claude 综合继续运行。核心机制实验整体仍未按原文完成。

## 18. 2026-10-29 15:47 CST 增量

### Claude Stage-7 与资源状态

- Claude 原 run `gpt2_medium_seq32_claude_opus5_20261027` 仍在原 Stage-7 attempt `attempt_1832318_1793258077670432062`。15:46 CST 远端 PID 32305 仍活动，Vivado 已通过 `Finished Timing Optimization` 并进入 `Technology Mapping`，CPU 约 100%、RSS 约 7.3 GiB；当前 attempt 目录仍未产生 timing/utilization report。
- 本轮 archive SHA256 `42f490eca705395cf98336a9ea177ead5392d4e3a8e9d7970f8332bc10c92fc3` 与提交的源闭包一致，`Attention.scala`/`Norm.scala` 分别为 `80955e9c...`/`ad986b9a...`。报告完成前不登记新的 Fmax、WNS 或资源；最近完成值仍为 26.979630 MHz / -30.398 ns，历史最佳 27.376259 MHz 保留。Stage-6 exact-board `vcs_compile_only` 已通过，仿真未运行。

### 新核心机制实验复核

- 1A 仍有真实 Stage 0–3 SACG 图演进 7→7→18 边，Stage-3 checker 11 pass/0 fail/0 errors；它没有匹配对照组。
- 1B 的六项预登记参数变更 ACCORD/B0 共 12 次 Stage-4 都被同一个 `cyclic_stream_wait` 静态模板模式拒绝，未进入 Stage-5/6。额外只读检查确认当前 DSE 的 `cross_token_reuse_tokens` 候选域为 `[4, 8, 16]`，没有能使 `token_tile_size=1` 的合法单字段候选；不再重复同类 Stage-4 尝试，也不绕过该 gate。此检测是静态 schedule 风险，不是 RTL 仿真或形式证明的运行时死锁。
- 2A 受控 VCS compile-fault 仍只支持 `vcs_compile_failure` 首错识别。`sacg_cctg_causal_slice.py` 将缺少 structured progress events 或 SACG/CCTG边界输入的结果标为 `insufficient_evidence`；compile-only 不运行仿真，不能为 M=8–10 的 CCTG 根因/修复统计提供 runtime frontier。当前没有 CCTG 根因命中率或 bounded-repair 对照数据。
- 2B 已存在 GPT-2 Small 与 Medium 各 4/4 的 deterministic E1–E4 evidence-contract fixtures（两组均 0 false invalidation、0 stale-evidence acceptance）。另有一次隔离副本真实 checker replay：原证书/报告副本通过，追加一个空白字节后以 live-evidence hash drift 拒绝。它不表示自然运行错误率、真实 Agent 样本或 targeted-vs-full 重验加速比。实际 gate wall-clock 单次数据另见 `method2_2a_2b_20261029/2b_gate_timing_20261029/`。
- 新核心机制实验整体仍未按计划完成。`accagent/docs/new_core_method_eval.md` 未修改；本轮没有启动新的 VCS/Vivado，也没有更改共享框架或硬件模板。WSL available memory 约 16 GiB。

### 15:52 CST follow-up

- 同一 Claude attempt 已运行约 37 分钟，远端 PID 32305 仍以约 100% CPU 运行，RSS 约 5.1 GiB；Vivado 位于 `Technology Mapping`，日志仍在输出 URAM optional output register 未合并的 `Synth 8-7052` 时序提示，没有 ERROR，也没有报告。不能将该提示解读为综合失败或新频率；source-bound QoR 仍待最终报告。
- 本地 WSL available memory 约 14 GiB。没有增加本地验证或 Vivado 进程；Claude timing 由现有子任务继续监控。

### 15:58 CST follow-up

- 远端 attempt elapsed 约 44 分钟，Vivado PID 32305 仍以 100% CPU 运行、RSS 约 5.8 GiB。主 `vivado.log` 自 15:48 左右未更新，但 `.Xil/Vivado-32305/.../realtime/tmp` 文件时间持续更新；据此判断作业仍在执行映射内部计算，并未退出。仍未生成 timing/utilization report 或新的 source-bound QoR。

### 16:01 CST follow-up

- 同一 attempt 从 `Technology Mapping` 进入 `Finished Flattening Before IO Insertion` / `Start Final Netlist Cleanup`，PID 32305 仍活动、CPU 约 100%、RSS 约 5.6 GiB；尚未产生 timing/utilization report。原 Claude 时序线未重启、未并行启动第二个综合。
- 1B 已完成的 6-task ACCORD/B0 pilot 保持原始结果和预登记不变。另行检查是否有合法且可按标准 Stage-4/5/6 执行的补充候选，限定在隔离的补充实验中，不绕过候选 gate、不手改共享模板。

## 19. 2026-10-29 16:16 CST 增量

### Claude 原 run Stage-7

- 原 attempt `attempt_1832318_1793258077670432062` 仍在远端运行。Vivado synthesis 报告 `Synthesis finished with 0 errors, 0 critical warnings and 458 warnings`，正进行 synthesized-netlist translation；已输出阶段性资源单元计数 LUT4/5/6 115,372/123,819/244,131、RAMB36 180、RAMB18 12、URAM 208、FDRE 160,497。该 attempt 尚无最终 timing/utilization report，阶段性单元计数不作为正式 QoR 或 Fmax/WNS。主进程 PID 32305 与两个 parallel-synthesis worker 仍活动，本轮未重启或另开综合。

### 1B 独立补充候选 T7

- 隔离补充实验目录为 `accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/T7-cross-token-reuse-1/`，独立预登记 `cross_token_reuse_tokens=16->1`。它不在原 DSE 域 `[4,8,16]`，只作扩展域探索性补充，不并入原六任务统计或原候选域结论。
- 标准 Stage-4 ACCORD/B0 均返回 0、parameter-binding report ready，选中候选 `arch_218334c128b1` 且 feasible；耗时分别约35.878s、30.390s。证据均写在 T7 隔离目录。
- ACCORD Stage-5 仍在运行（约6分钟）；完整 Chisel RTL 以及 `compile_check.json`、`codegen_contract_check.json`、`codegen_package_static_check.json` 已开始生成，但 Stage-5 汇总/返回码仍未落盘，不能判为通过。B0 Stage-5 和 Stage-6 VCS 均未启动。
- 已核实 Stage-6 标准 repair-loop 入口为 `python3 -m accagent.framework.stage_debug_loop --sacg-state <Stage5 run/code_generation/sacg_state.json>`；裸 `stage_verification` 不能接管 repair-loop。Stage-5 ACCORD/B0 均确认通过后，再按 ACCORD、B0 顺序执行 Stage-6 `vcs_compile_only`，失败时由标准 debug-loop 接管。未绕过 gate、未改 RTL/框架/共享模板。

### 其余核心机制实验

- 1A 仍只有真实 Stage 0–3 SACG 前向记录，无三配置对照；2A compile-fault pilot 的 CCTG 仍为 `insufficient_evidence`；2B 仍只有 Small/Medium E1–E4 fixtures、一次 controlled stale-report replay 和真实 gate 单次耗时。原计划中的其余对照指标尚未得到新的执行证据，不能宣称已完成。
- `accagent/docs/new_core_method_eval.md` 未修改；原六项 1B 预登记及其 12 次 Stage-4 拒绝保持原样。

## 20. 2026-10-29 16:29 CST 增量

### Claude 原 run Stage-7 attempt

- Claude GPT-2 Medium seq32 仍在同一 Stage-7 attempt `attempt_1832318_1793258077670432062`，输入 source closure archive SHA-256 `42f490eca705395cf98336a9ea177ead5392d4e3a8e9d7970f8332bc10c92fc3`。远端 Vivado PID 32305 已运行约71分钟，约105% CPU、RSS约10.9 GiB，仍在 `report_timing_summary`；`app_shell_synth_timing.rpt` 尚未生成。当前只有 OOC `HD.CLK_SRC` 未设置的 warning，不能据此计算 Fmax/WNS，也不能说 attempt 已卡死或失败。
- utilization report 已生成，Design `GeneratedAxiDdrTop`、器件 `xcvu9p_CIVflgb2104-2`、状态 Synthesized。资源为 LUT 650,915、FF 161,154、DSP 4,234、URAM 208、RAMB36 180、RAMB18 12；远端原始报告 SHA-256 `2e357a761a2bef61c537b72463aa4685a9b4d895c4b1e3700cc6e18c778ede97`。这是综合资源数据，不是 P&R 或上板结果；最终 Fmax/WNS 待 timing report。

### 1B T7 补充 Stage-5 配对

- 隔离 T7 `cross_token_reuse_tokens=16->1` 的 Stage-4 ACCORD/B0 均通过并选中 feasible candidate `arch_218334c128b1`；该值不属于原 DSE 域 `[4,8,16]`，只记为扩展域探索性结果，不并入原六项统计。
- ACCORD Stage-5 返回码1、report `incomplete`，耗时524.17秒；B0 Stage-5 返回码1、report `incomplete`，耗时540.35秒。两侧六条 SBT compile/elaboration 命令均返回0，`compile_check` 为 pass；两侧 `codegen_contract_check` 均因16个 warning markers 失败，`codegen_package_static_check` 随之失败。原始 warning 定位到 `Linear.scala:459:27` 的 Chisel W004：对 size-1 Vec `beatValues(writeToken)` 以1-bit动态索引 `outputLane` 读取，预期索引宽度为0。这是 warning-free contract gate failure，不是 VCS compile failure；Stage-6 尚未运行。
- 两个隔离 profile 已安排按 ACCORD、B0 顺序进入框架自带 `stage_debug_loop` 处理该 Stage-5 gate 失败，再依据各自标准 gate 决定是否进入 exact-board `vcs_compile_only`。不手工改 RTL、不放宽 warning gate、不单独调用 VCS。原六项 1B 的12次 Stage-4 `cyclic_stream_wait` 拒绝不变，1A/2A/2B 本 checkpoint 无新执行结果。
- 本地 available memory 约16 GiB；没有增加本地 Vivado/VCS 进程。实验计划、共享 RTL/template 和框架代码未修改。

## 21. 2026-10-29 16:48 CST 增量

### Claude 时序线

- 原 run `gpt2_medium_seq32_claude_opus5_20261027` 已由 agent 在新 run-local Attention 候选上完成 Stage-6 `vcs_compile_only`：33 个模块完成，`simv` 链接成功，VCS 返回码 0。此 gate 只证明编译/elaboration/link，不代表仿真运行或数值功能正确。
- Stage-7 新 attempt `attempt_1918679_1793262899199950352` 使用源码闭包 SHA-256 `0089cf93ec7a070e2ca95caf401963719bb1b3e1ce0c4a516d248d2a116b0abb`，归档内 Attention SHA 前缀 `1dedc9bc`、Norm SHA 前缀 `ad986b9a`。16:47 CST 远端 Vivado 已完成 RTL Optimization Phase 2，正在将 XPM memories 映射为级联 BRAM；仍在运行，尚无本 attempt 的 timing/utilization 最终报告。此前完成候选 Fmax 26.062 MHz、WNS -31.703 ns；历史最佳 27.376259 MHz 继续保留。不得把旧候选 QoR 绑定到新源码。

### 新核心机制实验复核

- Method 1A 仍有一条真实 Stage-0→3 SACG 前向记录：图边数 7→7→18，Stage-3 checker 11 pass/0 fail/0 error。没有三种配置对照或 first-pass cohort，相关比率未测量。
- Method 1B 原预登记 T1–T6 的 ACCORD/B0 共 12 个 Stage-4 invocation 均因 `cyclic_stream_wait` 无 eligible candidate 而退出，未进入 Stage-5/6。只读根因审查确认候选绑定字段正确、六条隔离 run 均从 canonical 模板重算；这是 Attention 等待 output Linear 当前 row 完成、Linear 又等待收齐 token chunk 的高置信静态结构阻塞，非单候选重测误报。该静态判断不是 RTL 仿真或 formal 的实际死锁证明。没有可安全从这些 Stage-4 结果直接续跑的 Stage-5/6 入口；反事实 cycle-break fallback 不会改变 RTL，不能用来放行。
- 补充 T7 `cross_token_reuse_tokens=16→1` 是 DSE 域外探索，不并入 T1–T6。ACCORD/B0 Stage-4 均通过；Stage-5 均 `incomplete`：六条 SBT compile/elaboration 命令返回 0，但 warning-free contract 因 run-local `Linear.scala:459` 的 Chisel W004 拒绝（`Vec(size=1)` 使用 1-bit 动态索引）。Stage-6 未运行。禁止绕过 warning gate。ACCORD Agent 提议的 run-local 修复标记为需负责人批准；T7 另缺少正常 `stage_verification_plan` 产物，先前 debug-loop 因 `artifact.stage5.verification_artifact_contract` 缺失而在 VCS 前报错。详细报告及 hash 在 `accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/T7-cross-token-reuse-1/NEXT_STEP_BLOCKER_20261029.md`。本轮没有改模板/RTL/gate，也没有手工运行 VCS。
- Method 2A 的隔离真实 VCS compile-fault pilot 将语法错误分类为 `vcs_compile_failure`；CCTG 返回 `insufficient_evidence`，因为 `vcs_compile_only` 不产生 runtime progress log 和 executed manifest。它不是 CCTG 图定位或修复闭环，不支持故障定位命中率。Method 2B 保持既有证据：Small/Medium E1–E4 deterministic fixtures、单次 controlled stale-report replay、真实 gate 单次耗时；没有自然 stale-rejection 率或 targeted-vs-full 重验加速数据。
- 原 `accagent/docs/new_core_method_eval.md` 未修改；计划中的 1B 配对成功率、2A 的 8–10 样本定位/修复分数等指标仍未完成，不应当作已取得的数据。

### 16:52 CST follow-up

- Claude 新 attempt `attempt_1918679_1793262899199950352` 仍在同一远端 Vivado 任务中，运行约16分钟；当前处理 `res1Q/res2Q` 等 XPM→BRAM mapping，远端 CPU 100%、RSS 约3.5 GiB。尚无 timing/utilization report，不登记新 QoR，也未并发启动另一综合。

## 22. 2026-10-29 18:20 CST 增量：机制实验 T7 Stage-6

- 隔离扩展候选 T7（`cross_token_reuse_tokens=16→1`，不属于原 DSE 域 `[4,8,16]`）的 Stage-4 ACCORD/B0 已通过；该候选不并入原 T1–T6 配对统计。
- Stage-5 的 `Linear.scala` W004 已按 `tokenTileSize==1` 使用常量索引修复，其他配置继续使用动态索引。warning-free contract 与 package checks 均通过，ACCORD/B0 Stage-5 完成；原失败报告保留。修复后模板 SHA-256：`dfa73bb0ba5896bd9e982ebefa41fced0707bdb5a959f24df435229567c7c033`。框架还补上通用触发条件：编译命令返回 0 但 warning-free contract 失败时，仍调用已有编译定位 Agent。
- ACCORD Stage-6 由标准 `stage_debug_loop` 接管。operator-leaf 与 multilayer pipeline 检查通过；board AXI/DDR gate 在 VCS 前因缺少 run-local `verification/board_simulation/board_simulation_manifest.json` 失败，因此当前没有 VCS 编译结果。repair-loop 已将缺失产物交给 `exact_board_integration_generation_agent`；事务 `3bead15c4ccc490abc1611203d948127` 首次响应触发 schema 修复重试，第二次调用截至本记录仍为 `inflight`。不能将其说成 VCS 失败或 Stage-6 通过。
- 外层 debug-loop session `96638`，worker PID `2022015`，启动器 PID `2022011`。待 Agent 结果返回后检查 manifest 与 contract，再由同一 debug-loop 执行 `vcs_compile_only`；不要重复启动 ACCORD Stage-6。ACCORD 完成后再运行 B0 Stage-6。
- Method 1A/原预登记 1B T1–T6、2A、2B 的证据边界不变；T7 仍是域外探索。只登记实际工具产物，不改写数据迎合预期。实验计划未修改。

### 18:50 CST follow-up

- ACCORD 的第一次 exact-board VCS 编译在真实生成 adapter 上失败，报 9 个未声明标识符/错误声明顺序，包括 `tile_pack_q`、`tile_pack_count_q`、`*_weight_ready` 与 `kernel_out_valid`。CCTG/repair-loop 使用这份 VCS 报告后，Agent 只修改隔离 run 的 `generated/board_integration/board_compute_slot_adapter.sv` 和 `generated/memory/dut_weight_binding_manifest.json`；patch application/hash 检查通过，未改共享 RTL/模板。重跑后 exact-board VCS 完成 33 modules，compile 28.385 s、elaboration 1.599 s、link 0.335 s；Stage-6 hierarchical debug loop pass。运行策略为 `vcs_compile_only`，仿真未运行，不能声称运行时或数值正确。
- 修复上述 repair-loop 中断的通用框架问题：`stage_llm._compact_verilog_module_interface` 原先只接受 `module Name(...)`，对实际带嵌套参数表达式的 ANSI 头 `module Name #(parameter ...) (...)` 抛错。现增加带注释/字符串处理的括号匹配并解析参数化头；新增大型只读 board RTL 投影回归。针对性 3 项测试通过，两个文件 `py_compile` 与相关 `git diff --check` 通过。`test_compile_only_board_discovery` 全模块 26 项中 25 项通过，另 1 项 `test_compile_repair_keeps_kernel_interface_and_scale_design_inputs` 对 `full_weight_image_manifest` 的保留断言失败，尚未追溯；该项不属于参数化头回归。
- B0 已运行 leaf 与 connected single-layer gate，二者通过；单层 VCS compile/elaboration/link 分别约 57.386/4.156/0.422 s。board AXI/DDR gate 因本 run 缺少 `board_simulation_manifest.json` 暂未进入 VCS。`exact_board_integration_generation_agent` 当前请求 transaction `29b55cc3d5524bbabcaf5f104ed8e17c` 仍在途，session `5000`、worker PID `2063048`、启动器 PID `2063047`；当前不要重复启动 B0 Stage-6。结果返回后先检查 manifest/preflight contract，再由原 debug-loop 继续。

### 19:15 CST follow-up

- B0 外层 Stage-6 session 已结束，返回 1；当前无残留 `stage_debug_loop`/B0 VCS 进程。最后的 `debug_loop_report.json` 状态为 `needs_repair`，异常发生在 exact-board VCS 启动前，故 B0 board VCS 尚无结果。
- 追溯到两个通用框架故障。`exact_board_compact_request_errors` 将仓库相对的 `target_file.path` 和 `allowed_exact_files` 按 `Path.cwd()` 解析；Stage-6 从 `accagent/` 工作目录执行时会与绝对的授权 manifest 路径错配。已改为相对仓库根目录解析，并加跨工作目录回归测试；用 B0 当前 repair package 在 `accagent/` 目录重放，preflight 错误列表为空。
- B0 exact-board Agent 曾同时返回 `status=ready_to_apply`、非空 `blocked_reasons`，并明确说明所给 adapter 不完整；旧 patch executor 仍应用了该 15,563-byte RTL。已修复通用状态归一化与原子写入口：带声明 blocker 的 actionable 响应现在归为 blocked，整批文件不写入；增加“ready + blocker 不得落盘”的回归测试。既有不完整 adapter 已在 B0 隔离 run 中，不把它当作有效实现或编译证据。
- 两项定向回归、`py_compile`、相关 `git diff --check` 均通过。完整 `test_repair_patch_execution` 为 49/51；两项既有 manifest 测试因 fixture 缺少 board source identity/tool profile 而触发 VCS-plan prerequisite blocker。完整 `test_llm_retry_paths` 为 115/116；唯一失败是既有 `test_repair_agent_prompt_uses_only_current_hierarchy_memory` 的 `LEAF_MEMORY_SENTINEL` prompt 保留断言，与本次路径/patch 状态修复无关。未改这些无关用例或门限。
- 下一步沿原 Stage-6 状态重新运行 B0 `board_axi_ddr_closure`，保留现有通过的 leaf/single-layer 证据；新结果必须经过当前 manifest/preflight 和 exact-board `vcs_compile_only` gate。B0 VCS 未完成前不登记 Stage-6 pass。T7 仍是原 DSE 域 `[4,8,16]` 外的 `reuse=1` 补充探索，不并入 T1–T6 统计。没有更改 DSE、RTL、共享模板或计划，也未修改观测数据迎合预期。

### 20:43 CST follow-up：T7 B0 Stage-6 编译失败与 no-progress loop

- B0 exact-board `vcs_compile_only` 已真实运行并失败，报告位于 `T7-cross-token-reuse-1/B0/run/verification/vcs/case_board_vcs_functional.json`。远端 `vcs_compile.log` 报 `exact_compute_slot_adapter.sv:308` 的 `k_in_ready_unused` 未声明；当前 adapter 在该处结束，没有 certified-kernel instance 或 `endmodule`。仿真未运行，不能登记 Stage-6 pass。此前 ACCORD 同参数线 exact-board compile 通过；B0 leaf/single-layer 与 Stage-4/5 通过证据保留。
- B0 Stage-6 repair loop 的 iteration 4–11 多次无编辑返回。第 6 轮曾生成连接 patch，但因 repeat-expansion 缺少 `@@QKV_SHIFT@@`、`@@ATTN_SHIFT@@`、`@@UP_SHIFT@@`、`@@DOWN_SHIFT@@` 标记而被原子拒绝，源文件未写入；之后 Agent 多次表示无法安全地局部修复不完整 adapter。
- 根因是 `stage_debug_loop.repair_execution_requires_fresh_agent_planning()` 把 no-progress disposition 无条件当作重新规划信号；即使同一控制/证据 frontier 重复、没有新工具证据，也继续运行 repair planner，形成无进展 API 调用循环。现已移除该分支；只有报告中明确的上游 capability producer 才触发新规划，重复 no-progress disposition 终止为 blocked。改动在 `accagent/framework/stage_debug_loop.py`，回归在 `tests/test_debug_loop_resume.py`。定向测试 27/27 通过，`py_compile` 和 `git diff --check` 通过。
- 旧本地 runner PID 2158233 已中断以停止重复调用；当时没有 VCS 子进程。第 12 轮 transaction `4acfa5d3310a4a68a8a40514381cf932` 随后被框架归档为 `stale_inflight`，没有将其当成成功响应。
- 该修复只改变框架的 no-progress 重规划控制，不放松编译 gate、不改硬件代码或数据。T7 `reuse=1` 仍为域外补充探索，不计入 T1–T6。正式 1B 配对和 2A CCTG 故障定位/修复数据仍未完成；原实验计划不变。

#### 20:47 CST recovery follow-up

- 使用修复后的 Stage-6 runner 从原 B0 `board_axi_ddr_closure` 入口续跑，未重跑 Stage-4/5。框架归档 stale transaction 后重新向 exact-board Agent 请求；transaction `de474a8f254b4a30800b3d9d40ed06ed` 于 20:46 CST 完成，Agent 返回 0 edits，指出当前 adapter 缺少 certified-kernel 连接体和模块闭合，不能通过删除握手或 tie-off 来伪造编译通过。没有源码写入，也没有新的 VCS replay。
- 修复后的 no-progress 行为生效：Stage-6 iteration 12 以 `needs_repair` 停止，无重复规划。当前 B0 board gate 仍是前次真实 VCS `fail`，Stage-6 未通过；VCS log 定位到 `k_in_ready_unused` 未声明及后续 `endmodule` 缺失导致的解析错误。当前无 runner/VCS 进程。
- 下一步需由当前流程 Agent 在完整板级绑定上下文中生成可连接 adapter，再经过原子 patch/materialization checks 和 exact-board VCS 重测。不能直接复制 ACCORD adapter 到 B0，也不能只补 `endmodule`、tie-off handshake 或把旧 VCS 失败改写成 pass。

### 2026-10-29 21:17 CST follow-up：T7 B0 与 Claude 当前状态

- T7 B0 继续使用原 Stage-6 `board_axi_ddr_closure` repair loop，没有重跑 Stage-4/5。`stage_debug_loop` PID `2202174` 存活；exact-board generation transaction `e6c04f61e9d54b27ba302ae0987e2d19` 为 `inflight`，已进入第 2 次请求（第 1 次 retry，21:16:45 CST）。暂无 Agent 响应、源码 patch 或新 VCS 结果；既有 `k_in_ready_unused` 未声明、缺少 kernel 实例和 `endmodule` 的真实 VCS fail 仍是当前 B0 gate 结果。
- Claude GPT-2 Medium seq32 原 run 继续运行：Stage-Backend PID `2186938`、Vivado wrapper PID `2186947`；远端 attempt `attempt_2186947_1793277857728644549` 的 Vivado PID `34910` 在 Technology Mapping，检查时 CPU 100%、RSS 4,980,364 KiB。尚未生成此源码 attempt 的最终 timing/utilization report，因此没有新的 Fmax/WNS 或吞吐率数据；历史最佳 Fmax 27.376259 MHz 保留，不能用旧报告代表当前候选。
- T7 的 `cross_token_reuse_tokens=1` 仍属预登记 DSE 域 `[4,8,16]` 外的探索性候选，不并入 T1–T6。正式 T1–T6 Stage-4 gate 阻塞以及 2A compile-fault pilot 缺少 runtime CCTG 证据的边界均未改变。本次不绕过验证 gate，不按期望筛选或修改实验观测。

### 2026-10-29 21:23 CST follow-up：T7 B0 exact-board compile-only 通过

- B0 Agent 已在隔离 run 内更新 `generated/board_integration/exact_compute_slot_adapter.sv` 和 `generated/memory/dut_weight_binding_manifest.json`；前后 SHA-256 见 `run/repair_execution/agent_patch_application.json`。原 Stage-6 hierarchical debug loop `debug_loop_report.json` 为 `pass`。exact-board VCS 输入 fingerprint `59ec1e4c937953bee76d8ef48d106be60da7f1e341ecfe095bf30bc451a4aaa9`，top `board_compute_slot_compile_tb`，compile returncode 0，报告状态 `pass`。
- 通过范围仅是 `vcs_compile_only`。同一 VCS report 标记 `simulation_skipped=true`、`run_status=not_run`、`exact_board_acceptance_passed=false`、`pipeline_overlap_passed=false`，因此不代表板级运行、算子级流水重叠或功能验收通过。修复前的 VCS fail 原始报告继续保留。
- 修复后 `verification/debug_closure/failure_localization.json` 状态为 `no_failure`，它不是故障 causal slice。该真实 compile repair/recompile 可作为流程案例，但不能计入 CCTG 根因定位/命中率数据。T7 是预登记 DSE 域 `[4,8,16]` 外的候选，不并入 T1–T6 配对统计。
- Claude Vivado attempt `attempt_2186947_1793277857728644549` 检查时仍在 Technology Mapping，远端 PID `34910` CPU 100%、RSS 约 5.2 GiB；日志出现 XPM URAM mapping timing warnings，尚未生成当前源码的最终 timing/utilization 报告。没有新的 Fmax/WNS/吞吐率数据；历史最佳 Fmax 27.376259 MHz 继续保留。

#### 21:31 CST Claude synthesis follow-up

- 当前 Claude Vivado attempt `attempt_2186947_1793277857728644549` 已完成 Technology Mapping（Vivado 日志 elapsed 44:04、peak memory 9667.387 MB），进入 IO Insertion / Final Netlist Cleanup。检查时远端 PID `34910` 仍为 100% CPU、RSS 约 5.6 GiB；远端可用内存充足。输入 closure archive SHA-256：`f9c3055697ece90d85cb9c03fdebb2e6464afc515e4f978c9b951c1091e09c94`。
- 尚无该 attempt 的 timing/utilization report，不产生新 Fmax/WNS 或吞吐率记录；历史 27.376259 MHz 仍是历史最佳，不绑定到当前源码。报告到达后仍需核对 archive identity、QoR、资源及关键路径。

#### 21:33 CST Claude synthesis follow-up

- 同一 attempt `attempt_2186947_1793277857728644549` 已完成 IO Insertion、Final Netlist Cleanup 和 generated-instance renaming。Vivado 日志累计 elapsed 47:12，peak memory 10079.312 MB；远端可用物理内存约 132.6 GiB，PID `34910` 仍活动，没有综合失败。
- 当前仍无最终 timing/utilization report，因此没有新 Fmax/WNS/QoR。输入 closure SHA-256 仍为 `f9c3055697ece90d85cb9c03fdebb2e6464afc515e4f978c9b951c1091e09c94`。

#### 21:36 CST Claude synthesis follow-up

- 同一 Vivado attempt 已进入 `Rebuilding User Hierarchy`，累计约 51 分钟；PID `34910` CPU 100%、RSS 约 6.6 GiB。日志无错误，最终 timing/utilization report 尚未生成，Fmax/WNS/QoR 不变且不更新。

#### 21:40 CST Claude synthesis follow-up

- Attempt `attempt_2186947_1793277857728644549` 已完成 Rebuilding User Hierarchy（阶段 elapsed 53:52），当前开始 `Renaming Generated Ports`。远端 PID `34910` 仍活动，尚无 timing/utilization report 或新 Fmax/WNS/QoR。

#### 21:42 CST Claude synthesis follow-up

- 同一 attempt 的 Vivado synthesis 已完成，elapsed 55:35，状态 `0 errors / 0 critical warnings / 458 warnings`，当前在 synthesized-netlist translation。阶段性 primitive 日志列出 LUT5 119,300、LUT6 244,849、RAMB36 180、RAMB18 12、URAM 208、FDRE 161,035；这些计数不替代最终 utilization report。
- timing/WNS/Fmax report 尚未生成；不计算或登记新的吞吐率，不改变历史最佳。

#### 21:46 CST Claude synthesis follow-up

- 同一 attempt 已完成 73,965 个 Unisim elements 的 netlist replacement，进入 logic optimization preparation。累计约 61 分钟，远端 Vivado PID `34910` CPU 100%、RSS 约 9.6 GiB；仍有超过 130 GiB 可用内存。当前无异常或最终 timing report，Fmax/WNS/QoR 继续待报告。

#### 21:54 CST Claude timing-analysis follow-up

- Vivado `synth_design` 完成（checksum `f40ad7eb`、4234 DSP48E2、0 errors / 0 critical warnings；后续 synth-design summary 报告 260 warnings），当前执行 `report_timing_summary`。日志警告 OOC clock port 的 `HD.CLK_SRC` 未设置，因此 clock delay/skew 未按顶层 clock buffer 位置估计；后续只将结果标为综合时序，不称为 P&R 或上板 Fmax。
- 当前 attempt 仍活动，远端 RSS 约 10.4 GiB、可用内存约 130 GiB；timing/utilization 文件尚未完成，没有新 Fmax/WNS。

### 2026-10-29 22:10 CST follow-up：机制实验与 Claude Stage-7

- 重新核对原预登记 Method 1B T1–T6：ACCORD/B0 12 个 Stage-4 任务均因同一 `cyclic_stream_wait` 静态 schedule blocker 退出；候选物化本身通过，但该 schedule 检查将可行集合置空，因此 Stage-5/6 的更新传播和 compile Pass@1 指标均未测量。该证据不等价于 RTL runtime deadlock，也不能通过绕过候选 gate 来改成通过结果。
- T7 `cross_token_reuse_tokens=16→1` 是独立预登记的扩展域补充，不属于原 DSE 候选域 `[4,8,16]`，不并入 T1–T6。ACCORD/B0 选择同一 feasible candidate `arch_218334c128b1`，fingerprint `218334c128b1706852d811e722c585eb22ec0b8efc0fdd9f5052ddad71c04253`；Stage-5 报告为 `ready`，Stage-6 debug-loop 为 `pass`。双方 exact-board VCS fingerprint `59ec1e4c937953bee76d8ef48d106be60da7f1e341ecfe095bf30bc451a4aaa9`，VCS compile return code 0。
- T7 VCS 使用 `vcs_compile_only`：`simulation_skipped=true`、`run_status=not_run`、`exact_board_acceptance_passed=false`、`pipeline_overlap_passed=false`。该结果只可记作单个参数更新后 exact-board 编译/elaboration/link 通过，不代表完整板级仿真、功能正确性、流水重叠或 CCTG 因果定位。B0 adapter 与 weight-binding manifest 修复的前后 SHA 在 T7 `B0/run/repair_execution/agent_patch_application.json`；真实失败记录保留。
- Claude 新综合 attempt `attempt_2232879_1793282470409500674` 已在原 Stage-Backend 运行；输入 closure archive SHA-256 `f02763cc802f028e7161ceb9c27747be86fefe0481ed2ea6743ccaaa883bd5da`。远端 Vivado PID `2512` 检查时 CPU 99.6%、RSS 4,744,196 KiB，运行约 7 分钟，已完成 RTL elaboration 和 RTL Optimization Phase 1。当前没有该 attempt 的 timing/utilization 报告，不产生新 Fmax/WNS/吞吐量。
- 最近一份已完成 QoR 仍绑定 closure SHA `f9c3055697ece90d85cb9c03fdebb2e6464afc515e4f978c9b951c1091e09c94`：Fmax 26.062 MHz、WNS -31.703 ns、DSE 估算吞吐 55.713 tokens/s；不覆盖历史最佳 27.376259 MHz。待新综合结束后，只按其匹配的源码 closure 报告登记数据。
