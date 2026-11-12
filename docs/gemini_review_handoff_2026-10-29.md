# SpatialAccAgent 独立评估交接材料

**快照时间：2026-10-29 22:43 CST**
**目的：**交给不了解本仓库的 Gemini，供其独立评估 SpatialAccAgent 的机制实现、已取得的实验结果、证据缺口和低成本后续实验。本文按本地 run、实验报告和源码核对，不把实验计划中的设想当成观测结果。

## 1. 阅读说明与结论摘要

本项目研究的是面向 FPGA LLM Transformer 空间加速器的领域工作流，不是通用聊天型 multi-agent 框架。LLM 负责解析规格、在结构化约束下提出参数/流水线/修复动作并解释工具输出；Python 框架保存设计状态、调用真实工具、检查合同、执行有限范围的 patch 并决定是否允许进入下一阶段。

框架有较多机制实现，核心包括 Spatial Accelerator Contract Graph（SACG）、参数与资源/周期 DSE、分层验证与修复循环、SACG/CCTG 失败定位接口、版本绑定的验证证据、run-local 时序优化和可恢复的 run 状态。当前机制实验只形成了部分可报告证据：真实 SACG 前向轨迹、Stage-4 单字段参数物化 pilot、一次 compile-fault 诊断、证据合同变异夹具和一次真实报告副本受控重放。

最重要的实际发现是：

1. 1A 有真实 Stage-0 到 Stage-3 图演进数据，但没有对照实验。
2. 原 1B 六种 seq32 参数变化的候选物化正确，但全部被同一个静态调度风险检查在 Stage-4 阻断，故下游传播指标未测。
3. 域外补充 T7 reuse=1 的 ACCORD/B0 两条隔离流程最终通过 Stage-6 exact-board VCS compile-only；只证明本案例编译、elaboration 和 link 成功，不证明仿真或功能正确。
4. 2A 的受控 VCS 编译故障被 analyzer 正确分类，但 CCTG 没有得到所需 runtime 证据，明确返回 insufficient_evidence。不能把这次 analyzer 诊断记成 CCTG 图引导根因定位成功。
5. 2B 的 checker 对指定变异的行为已由夹具和受控重放验证，但没有 targeted-vs-full 的配对计时，不能报告效率收益。
6. GPT-6.1 与 DeepSeek 的 seq32 GPT-2 Medium 候选已达到综合后 Fmax 150 MHz 目标；Claude 的时序线仍在新的 Vivado synthesis attempt 中，当前没有该源码的新 QoR。

实验计划文件 accagent/docs/new_core_method_eval.md 里有计划样本量、建议性结果表达和拟议实验，不是事实记录。请以本文链接的 REPORT.md、README.md、VCS/Vivado JSON 与日志作为结果依据。原始计划和实测结果必须分开。

## 2. 问题定义、实验边界与术语

### 2.1 研究对象

系统目标是：根据目标 Transformer 模型、数值策略和 FPGA 板卡，自动建立空间并行数据流设计，选择可信算子模板和物理参数，生成 Chisel/RTL，执行验证与后端综合，并在综合时序不足时继续做当前 run 的关键路径优化。

DUT 聚焦 Transformer block 内部，不默认包含 tokenizer、embedding、final norm、LM head、logits 或采样。主要研究约束不是让 LLM 任意生成 RTL，而是让 LLM 的决策受模型语义、硬件合同、模板/IP、DSE 合法域和真实工具结果约束。

### 2.2 当前横向硬件比较 envelope

| 条目 | 固定设置 |
|---|---|
| 目标模型 | Hugging Face openai-community/gpt2-medium，24 decoder layers，hidden=1024，16 heads，MLP=4096 |
| 工作负载 | batch=1，sequence length=32 |
| 数据格式 | signed W4 权重、signed A8 激活、INT32 累加和 bias、integer DSP datapath |
| FPGA | MIMIC Computer v6.0，xcvu9p_CIV-flgb2104-2-i |
| DDR 接口 | 512-bit refill；目标板 AXI/DDR wrapper 进入 exact-board compile 集合 |
| Stage-6 当前接受标准 | vcs_compile_only，即真实 VCS compile/elaboration/link 成功；当前 run 跳过仿真 |
| Stage-7 目标 | source-bound Vivado post-synthesis Fmax >=150 MHz；不是 place-and-route 或实板时钟验收 |

项目的最终产品目标比当前实验 run 的快速验收范围更强：期望 exact-board AXI/DDR 下完成全层推理、算子级 token 重叠、不卡死并产生有效输出。当前三线的 VCS compile-only 证据不能代替这些最终目标。

### 2.3 用词定义

| 标签 | 当前含义 |
|---|---|
| 参数物化通过 | 候选字段绑定到设计参数产物并通过对应静态检查 |
| VCS compile-only 通过 | 对指定 source/input fingerprint，VCS 编译、elaboration、link 返回成功；simulation skipped |
| 综合后 Fmax | Vivado 对特定 RTL/source archive 的综合时序估计 |
| DSE estimated tok/s | 由估算周期数和综合频率计算出的预测吞吐，不是周期计数器或板上数据 |
| CCTG causal slice | 失败证据能够映射到 graph frontier、失败边界和候选根因的证据切片；编译错误分类本身不等于 causal slice |

## 3. 实现架构与机制细节

### 3.1 一次 run 的状态与执行分工

可把一次 run 的持久化状态抽象为 S_t=(G_t,A_t,R_t)：

- G_t：SACG 图，包含节点、边、约束、不变量、阶段状态与来源关联。
- A_t：输入规范化、模板绑定、pipeline plan、参数绑定、Chisel/RTL、verification plan、board adapter、backend 等 artifact。
- R_t：LLM 请求/响应、checker 结果、VCS/Vivado 命令及报告、修复动作、patch 前后状态、checkpoint 和 flow events。

TopAgent 位于 accagent/framework/agent.py。它恢复 checkpoint 并依次调度 Stage 0–7；stage agent/团队根据角色生成结构化动作；框架和 checker 检查动作、运行本地或远端工具、物化结果并记录证据。LLM 的“我认为通过”不能代替 VCS、Vivado 或合同检查。

团队层按任务拆分模型形状、数值/模板、数据与存储、验证修复、实现部署等专业角色。任务结果通过 JSON/schema 和阶段合同回传。LLM provider 统一经 llm_config.py、llm_io.py、stage_llm.py 接入；run 记录模型、请求、响应和重试。该文档不包含 API key、认证 token 或其他凭证。

### 3.2 SACG：跨抽象层设计合同图

源码入口：

- accagent/framework/stage_constraints.py：build_design_graph_nodes_edges、build_initial_design_graph、extract_constraints。
- accagent/framework/sacg_store.py：SACGStore、state/reference 检查及持久化操作。
- accagent/framework/sacg_utils.py：节点/边/约束更新、artifact 状态与受限历史/经验摘要。

图中的节点覆盖 model/layer/operator、shape、numeric policy、template/IP、PE/lane/reduction、pipeline stage、ready/valid stream、DDR/cache/runtime、verification 和 backend/deployment。边覆盖 semantic、shape、numeric、model order、stream/backpressure、AXI beat、memory layout、control/liveness、runtime 与 backend 依赖。合同和 invariant 将目标语义连接到参数、RTL、工具证据。

核心 invariant 包括：Transformer block 拓扑和算子先后关系不被无意删除或串行化；W4A8 映射到整数 DSP；完整权重由 DDR 保存、片上只保留有界工作缓存；512-bit refill 与缓存布局一致；active/shadow 权重预取和 activation ping-pong 保持；ready/valid 回压允许不同 token 在不同算子级重叠；exact-board wrapper 不被简化接口替换。

Stage 间的 graph update 应传播约束并指明依赖产物/需要重验的 checker。对于机制评估，必须区分图结构被更新、参数绑定成功、受影响产物被重新生成，以及下游工具通过；它们是不同观测指标。

### 3.3 CCTG：失败证据到修复边界

源码入口：accagent/framework/sacg_cctg_causal_slice.py 中的 build_sacg_cctg_causal_slice、_frontier、_select_graph；修复计划和执行分别在 stage_repair.py、stage_repair_execute.py、stage_debug_loop.py。

典型目标链路：真实工具失败 -> failure classifier -> SACG/CCTG frontier -> 失败合同/边界 -> 候选根因与允许修改范围 -> LLM repair action -> patch checker/原子文件应用 -> 同层真实工具重验 -> 更新 SACG 和记忆。

CCTG 的关键不是“LLM 看日志猜对了”，而是从当前证据选择受影响图切片并限制 repair scope。当前 builder 的主要 causal frontier 依赖 structured runtime progress events、executed manifest 和 board/layer 边界证据。编译器语法错误没有运行期 progress/manifest，所以 compile-only pilot 中 builder 合理返回 insufficient_evidence。当前设计没有把这个结果扩写成图定位成功。

### 3.4 Revision-bound verification evidence

源码入口：accagent/framework/verification_evidence_contract.py 中的 promotion_evidence_binding_errors、certificate_contract_errors；关联身份逻辑在 contract_identity.py、trace_identity.py。

验证证据按当前层级、所需 gates、输入/RTL/工具报告等身份关联。对一个具体 scope，promotion certificate 不能覆盖不匹配的当前源码/报告；低层已通过证书可按合同复用，但不能用旧的更高层结果跳过当前必需 gate。compile-only policy 只接受当前所需 VCS 工具的真实通过报告，不会把 simulation/runtime capability label 当作已执行仿真。

机制目标是避免 stale evidence 被晋级、避免无关输入变化误伤仍有效的低层证据，并在修复后只重跑受影响范围。当前的 checker 通过/拒绝 fixture 已验证局部合同逻辑；实际耗时收益仍需 paired revalidation。

### 3.5 Stage 0–7 控制流

| 阶段 | 主要实现/动作 | 产物与 gate |
|---|---|---|
| Stage 0 输入准备 | stage_input.py、case_adapter.py；归一化模型配置、板卡、量化、工具、目标 | task card/model profile/board profile；来源事实和输入相互一致 |
| Stage 1 约束抽取 | stage_constraints.py 与 SACG store | 初始 SACG、constraints/invariants；引用和合同检查 |
| Stage 2 模板/IP | stage_templates.py | 绑定可信 Chisel 算子和器件 IP；保留数值语义、接口和 provenance |
| Stage 3 流水规划 | stage_pipeline.py | operator stream graph、token flow、ready/valid、FIFO、shape/连线 contract |
| Stage 4 DSE/参数 | stage_params.py、dse_candidates.py、dse_estimator.py、dse_ledger.py | 合法参数候选、物理绑定、周期/资源 proxy、选定候选与测量队列 |
| Stage 5 代码生成 | stage_code_generation.py | Chisel/Verilog、编译/展开报告、包静态检查、verification artifact plan |
| Stage 6 验证/修复 | stage_verification.py、stage_verification_plan.py、stage_debug_loop.py、stage_repair.py、stage_repair_execute.py | 分层 leaf/single-layer/board gates；当前主实验 policy 是 exact-board vcs_compile_only |
| Stage 7 后端 | stage_backend.py、codegen_source_repair.py | Vivado synthesis/timing/resource、run-local critical-path repair、source archive 与 QoR ledger |

阶段可因直接的当前证据请求回到所需 scope 重验；哈希漂移、上游 API 错误或框架控制问题本身不应被包装成设计失败或无证据回退。framework 中仍有复杂的恢复/审查/证据分支，是这次 Gemini 评估可检查的工程风险。

### 3.6 DSE 周期和资源 proxy

入口包括 stage_params.build_dse_search()/bind_parameters() 和 dse_estimator.cost_features()/estimate()/rank_candidates()。DSE 将参数空间物化为候选，执行形状、算子、缓存、带宽和资源合法性检查，并估算 operator service cycles、pipeline cycles 和资源 proxy，供候选筛选和排序使用。

它是结构估算，不是 RTL 仿真模型；当前吞吐使用 N_tokens × post-synthesis Fmax / DSE estimated cycles。当前 GPT-2 Medium seq32 的报告使用 14,969,236 estimated cycles。没有 cycle counter 仿真、实板 latency 或实测吞吐。DSE 的合法候选检查也有一个目前显著影响 1B 的 schedule 风险拦截，见第 6 节。

### 3.7 修复循环、时序优化和运行记忆

Stage-6 repair 由工具报告驱动：分析当前 failure、读取 graph/context、确定允许修改的文件和验收 gate，生成 patch，检查 patch 范围后原子应用，再对同层运行真实工具。stage_repair_execute.py 承担大量能力，是当前最大的单体模块（约 38,423 行）；stage_repair.py 约 5,240 行，stage_backend.py 约 4,200 行。这是理解和维护框架时的重要复杂度风险。

Stage-7 时序优化使用当前 source archive 绑定的 Vivado 关键路径，codegen_source_repair.py 将层级端点映射回当前 Scala/RTL 信号与源码上下文，Agent 提出 run-local 修改；随后重跑适用的 Chisel/Scala 检查、VCS compile-only 与 Vivado。保持每个 archive 对应自己的 Fmax/WNS/资源，不把旧报告转绑到新源。已有最佳候选应单独保存，不因较差的新候选被覆盖。

共享 repair experience 和 SACG memory 可给后续 Agent 提供已观察经验，但只是候选假设；旧 patch 或旧证据不能覆盖当前源码、当前图和当前工具报告。

### 3.8 目标硬件组织

当前 GPT-2 Medium 三线的选定物理候选参数为 rows=16、cols=32、lanes=16、cross-token reuse=16、FIFO depth=64、activation banks=2、512-bit cache refill、cache tile count=2、cache tile words=256、integer DSP。三条线的 candidate fingerprint 相同：31c1198760c03c7072c82cbb38fe8498922aef8d4aa17dbcf070e3818ebab8bc。

权重不全放 BRAM/URAM。完整 Transformer block 权重位于 DDR；片上使用受限 active/shadow cache，当前层计算期间预取下一层权重；512-bit DDR refill 与缓存侧宽写入/并行读出用于减轻窄通路瓶颈；激活使用 ping-pong。目标 stream 不是“每一级相同周期、零气泡”，而是 ready/valid 正确回压下不同 token 可在不同算子阶段重叠，无整序列 barrier。

需要区分目标架构约束与实现证据：综合资源来自具体 generated-kernel synthesis，不能据此称 full-board P&R 完成；compile-only 没有证明 DDR runtime 数据路径已运行。

## 4. 当前三条 GPT-2 Medium 硬件线

三条上游 LLM 使用同一 GPT-2 Medium seq32、W4A8、VU9P、512-bit DDR 和同一 DSE candidate fingerprint。表格数据绑定各自 source archive。

| 上游 LLM | 已记录最佳 archive | Post-synthesis Fmax / WNS | LUT / FF / DSP / URAM / BRAM36 / BRAM18 | DSE estimated throughput | 说明 |
|---|---|---:|---:|---:|---|
| GPT-6.1-Sol | 46b2af1f0573493a7a39fb2e39e3b0c60d72e824a171ea80784d53ad85bba0f9 | 155.448 MHz / +0.234 ns | 634,930 / 197,332 / 4,232 / 208 / 180 / 12 | 332.30 tok/s | 达到综合 Fmax 目标 |
| DeepSeek-V4-Pro | f6c22379ec95b77f5374384554e0256523a3ab9709bf3b1cfb5eb41f5200f8f9 | 152.742 MHz / +0.120 ns | 614,273 / 177,448 / 3,074 / 208 / 180 / 12 | 326.52 tok/s | 达到综合 Fmax 目标 |
| Claude Opus 5 | 历史最佳 archive 7a0ff04e48380b8ee833815bd3476e8a09b0ae0ccf787bd5361154caced9b0ae | 27.376 MHz / -29.861 ns | 652,234 / 162,054 / 4,130 / 208 / 180 / 12 | 58.52 tok/s | 未达目标；旧最佳保留 |

边界：吞吐字段以 32 tokens、综合 Fmax 和 DSE 14,969,236 estimated cycles 计算，不是 RTL cycle counter、仿真测量、place-and-route timing 或上板吞吐。资源和频率也只代表各自 archive 的 generated-kernel synthesis scope。

Claude 的最新已完成候选与历史最佳不同：新完成的 f9c3055697... archive 报告 Fmax 26.062 MHz、WNS -31.703 ns、estimated 55.713 tok/s，未超过 27.376 MHz 历史最佳。当前 attempt 为 attempt_2232879_1793282470409500674，source closure SHA-256 为 f02763cc802f028e7161ceb9c27747be86fefe0481ed2ea6743ccaaa883bd5da。22:43 CST 检查时远端 Vivado PID 2512 运行约 41 分钟、CPU 100%、RSS 约 5.95 GiB，仍在 synthesis/XPM memory mapping 阶段并有 optional output-register timing warnings；未见最终当前 attempt 的 timing/utilization report。因此目前没有新的 Fmax/WNS/QoR，不能拿旧数字代表当前源码。WSL 本地约 18 GiB available；综合主要跑在远端。

DeepSeek 与 Claude 的 timing history 是同一设计的连续候选轨迹，不是独立样本集合。Method 2 报告举例：DeepSeek 从 archive 4c17d704... 的 121.832 MHz 经过 Norm reduction pipeline、QKV identity-requantization bypass 等 repair，到 archive f6c22379... 的 152.742 MHz；该轨迹可用于描述时序优化过程，但不能计入 CCTG 故障定位样本。

## 5. 核心机制实验：原始结果与边界

实验原计划：accagent/docs/new_core_method_eval.md。已执行报告：

- Method 1：accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/REPORT.md
- Method 2：accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/README.md
- compile-fault pilot：accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/compile_fault_pilot_20261029/RESULT.md
- 截至本快照的组合状态：docs/current_framework_and_experiment_status_2026-10-29.md

### 5.1 1A：SACG 前向约束传播

真实 GPT-2 Medium seq32 GPT-6.1 run 的 Stage-0/1/2/3 SACG 快照边数为 7、7、18。最终图有 7 条 model-order 边与 11 条 stream 边；约束数从 16 增至 23。Stage-3 pipeline checker 为 11 pass、0 fail、0 error。报告和快照有源文件/状态 hash。

这是一次真实前向 trace，可以说明 graph 随模板选择和 pipeline 构造发生了什么变化。它没有匹配 B0/Flat-Config/Unstructured-History 首轮对照，也没有 Stage-7 first-pass cohort；不能由此推导相对违例率或 first-pass 提升。

### 5.2 1B：T1–T6 单字段参数变化

预登记的六个参数变化均来自原 GPT-2 Medium seq32 Stage-4 持久化候选表；ACCORD/B0 各运行一次，共 12 个独立 Stage-4 job：

| Task | 预登记变化 |
|---|---|
| T1 | compute_array_rows 16→8 |
| T2 | compute_array_cols 32→16 |
| T3 | fifo_depth 64→128 |
| T4 | activation_banks 2→4 |
| T5 | cross_token_reuse_tokens 16→8 |
| T6 | cross_token_reuse_tokens 16→4 |

12/12 报告显示 candidate_materialization.status=pass，且每项的单字段变化与预登记 candidate 对应。但在 Stage-4 候选 eligibility 阶段，重新计算的 schedule status 均被 cyclic_stream_wait 阻止，feasible set 变为空，作业以 return code 2 结束。Stage-5/Stage-6 未运行。

阻塞来自 dse_estimator.py 的静态源码模式检查：IntegerAttention 在拿到当前 output-projection 行结果前不推进下一行；输出 Linear 要先收齐 token_tile_size 输入 token 才启动输出。两边在当前 chunk 大于 1 的模式下构成结构性等待环。它是源码/调度风险分析，不是 RTL 仿真或 formal 的运行时死锁证明。

因此，可报告“本 pilot 的 Stage-4 单字段参数物化 12/12 通过”，不能报告完整跨阶段 propagation accuracy、affected-file precision/recall、contract rerun recall 或 Stage-5/6 Pass@1。这些指标未测，不是零。

### 5.3 1B 扩展域补充 T7

独立补充 candidate 是 cross_token_reuse_tokens 16→1，超出原搜索域 [4,8,16]，不能并入 T1–T6。ACCORD/B0 Stage-4 都选中相同 candidate arch_218334c128b1，candidate fingerprint 218334c128b1706852d811e722c585eb22ec0b8efc0fdd9f5052ddad71c04253。Stage-5 最终 code-generation reports 为 ready；T7 过程中曾遇到 Linear.scala:459 的 Chisel W004（Vec size=1 使用 1-bit 动态索引），在 tokenTileSize==1 分支改用常量索引后 warning-free/package checks 通过。

Stage-6 标准 debug loop 在 ACCORD/B0 均为 pass；两边 exact-board VCS compile-only report 均为 pass，fingerprint 59ec1e4c937953bee76d8ef48d106be60da7f1e341ecfe095bf30bc451a4aaa9。B0 经由 repair loop 修复了 board adapter 和 weight-binding manifest，真实失败报告及前后 hash 保留。

该 top 是 board_compute_slot_compile_tb；simulation_skipped=true、run_status=not_run、exact_board_acceptance_passed=false、pipeline_overlap_passed=false。修复后 failure_localization 为 no_failure，没有 CCTG causal slice。T7 是一项域外、compile-only 参数变更与 adapter repair 案例，不证明原 DSE 域泛化、运行时功能或 CCTG 定位能力。

### 5.4 2A：失败定位与有界修复

在隔离复制的 exact-board compile closure 中，testbench 被故意插入单行语法错误：this_is_a_compile_fault @;。真实远端 VCS 返回 syntax error；case_vcs_evidence_analyzer 正确识别 failure_class=vcs_compile_failure、first_real_error=Error-[SE] Syntax error、repair_scope=generated_source_or_compile_plan。

随后 CCTG builder 返回 status=insufficient_evidence、frontier=runtime_evidence_unavailable。缺失的关键证据为 progress_event_log.jsonl 和 board_simulation_executed_manifest.json；因此没有 graph-backed runtime frontier、causal slice、root cause node 或 repair episode。实验按 pilot 设计在诊断后停止，没有启动 repair。

这证明 VCS compile failure detection/first-error extraction 对这个受控故障有效，不证明 CCTG 图引导定位。历史 Gemma compile-fail-to-pass 中 Agent 将声明移到使用点前，33 modules compile/elaboration/link 通过；但 failure_localization 没有非空 causal slice，且模型/run 不同，不计作本 2A 样本。

### 5.5 2B：证据失效和重验证

确定性 E1–E4 fixtures：GPT-2 Small 4/4，GPT-2 Medium 4/4。变异类别为 RTL、XDC、model configuration、documentation-only。两组均报告预期判定正确、stale-evidence acceptance=0、false invalidation=0。它们是 evidence-contract 单元/fixture 测试，没有运行 Agent、VCS、Vivado、RTL simulation 或 board。

真实报告受控重放：取 Claude run 的真实 promotion certificate 和 VCS report 复制到隔离目录；未修改副本通过 production certificate_contract_errors()；只给副本 report 追加一个空白字节后，checker 以 promotion certificate live evidence hash drift 拒绝。原 run 未改。它是人为 mutation replay，不是自然 stale-event 率或 Agent end-to-end 故障率。

单次墙钟记录包括 Stage-3 multilayer pipeline checker wrapper 0.101 s；exact-board VCS compile-only 62.696 s（其中 compile/elaboration 58.957 s）；Attention patch 后另一版 exact-board VCS 78.775 s（compile/elaboration 74.944 s）；一次 generated-kernel OOC synthesis 4,786.196 s。它们不是相同 source 的 targeted/full paired rerun，不能算效率提升倍数或节省时间。

### 5.6 当前已复跑的定向单测

本次文档整理前运行：

- python3 -m unittest tests.test_sacg_cctg_causal_slice tests.test_verification_evidence_contract -v：31 tests passed（CCTG slice 5，evidence contract 26）。

这些测试验证确定性代码路径，不代表真实故障 corpus 的命中率或 end-to-end 收益。历史上下文另记录过相邻测试集的不完整结果：test_compile_only_board_discovery 25/26、test_repair_patch_execution 49/51、test_llm_retry_paths 115/116；失败分别涉及 fixture 的 weight manifest/board identity 等前置条件或 prompt sentinel。它们未在本次重新运行，不能写成当前通过，也不能据此说整个仓库全量测试通过。

## 6. 近期遇到的问题、修复与剩余风险

### 6.1 Stage-4 共享调度阻塞

T1–T6 不论改阵列、FIFO、bank 还是 reuse，都命中同一 cyclic_stream_wait。继续重复同样的 Stage-4 pilot 不会增加信息。正确的工程路径是审查 Linear/Attention 的生产调度语义，解决增量输出/行推进等待关系，或在单独、明确预登记的合法配置中改变调度并重跑；不能关闭 gate 或把无 feasible candidate 说成 downstream pass。

### 6.2 T7 的 Stage-5 与 exact-board adapter 修复

T7 首次遇到 W004 warning-free gate 失败，之后按 tokenTileSize==1 使用常量索引并重新通过 codegen checks。ACCORD 的 exact-board adapter 初次 VCS 有未声明信号/声明顺序错误；B0 早期出现不完整 adapter（k_in_ready_unused 未声明、缺 kernel instance/end marker），repair loop 曾多轮没有有效 patch。Agent 后续在隔离 run 中修改 adapter 和 weight manifest，最终 ACCORD/B0 compile-only 通过。修复过程/报告不能从成功总结中删掉，因为它们是 bounded repair 案例，但其 failure_localization=no_failure 不能作为 CCTG causal episode。

### 6.3 框架自身的 repair-loop 缺陷

T7 暴露过几类不是硬件设计错误的通用问题：

- stage_llm.py 的 Verilog 模块接口 compaction 未正确识别带 parameter 的 ANSI module header，repair prompt 生成时异常；之后增加嵌套括号/字符串处理和回归测试。
- exact_board_compact_request_errors 在不同工作目录下解析相对路径错误，造成授权 source path 不匹配；之后改为以 repository root 解析并加跨 cwd 回归。
- LLM 同时返回 ready_to_apply 和非空 blocked_reasons 时，旧 patch executor 曾错误进入写入路径；之后归一化状态并要求 patch 原子门拒绝带 blocker 的 patch。
- 相同 no-progress evidence/frontier 可反复触发 fresh planning，造成 repair loop 空转；之后要求新规划必须有新工具/能力/patch/观测证据，并在重复无进展时停止为 blocked/needs_repair。

这些修复改善 harness 稳定性，不能算硬件性能提升；旧的 compile fail 与后来的 pass 均应保留。当前 worktree 仍有大量 framework/template/run 改动未提交或未跟踪；历史 report 与当前工作树不一定同一源码版本。审阅时应以每个 report 的 source archive/fingerprint 为单位，不要把现有树上的最新版代码默认等同于过去生成结果的源码。

### 6.4 Claude 时序 repair 的 Scala 编译回归

在 Stage-7 时序修复中，Attention 状态 Enum 改动曾出现重复状态定义和 Scala 编译错误（包括 sSoftmaxPipe3 重复定义、object <none> 编译错误）。Agent 多次调整后，当前 attempt 已进入 Vivado synthesis；它前置的当前源码 VCS compile-only 被记录为通过。新 synthesis 尚未结束，因此仍需等与该 closure 一致的报告，不能将旧报告绑定到新源码。

### 6.5 源码与测量边界

stage_repair_execute.py 超过 38k 行，Stage-6 的职责、恢复和证据逻辑高度集中；这是全面代码评估的重要可维护性风险。当前 run 也会保存大量 prompt、event、repair iteration、source archive 和生成产物。任何清理动作必须先确认不是最新源码、历史最佳 QoR、故障原始报告、修复前 evidence 或上下文恢复资料。

## 7. 适合快速补齐的实验计划

以下是供 Gemini 审核的候选计划，不是已执行结果。

### P0：立即可写的已有数字

1. 将 1A 写成真实前向 SACG case：边数 7→7→18、Stage-3 checker 11/11 pass，同时说明无对照。
2. 将 1B 现有数据窄化为“12/12 Stage-4 单字段候选物化通过；12/12 后续均被 schedule gate 阻断”。不要把它包装成传播准确率。
3. 单列 T7 为域外 exploratory case：ACCORD/B0 Stage-4/Stage-5/Stage-6 compile-only 通过；仿真未运行，不并入 T1–T6。
4. 2B 仅报告 2 组 fixture 判定和 1 个真实证据副本 mutation replay，明确没有效率对照。

### P1：低成本机制收益补充

**参数传播：**若希望有 propagated artifact 指标，先处理 T1–T6 共用的 schedule blocker，使合法候选在同一正常流程下能到 Stage-5/6。每例预先登记预期 SACG 节点、产物和 checker；跑一组小规模 ACCORD/B0 配对即可。也可另立一个 T7-style 扩展域 pilot，但应报告样本数和域外属性。参数绑定正确、SACG 边更新、下游文件刷新、compile pass 是四个不同 outcome。

**compile-only CCTG：**无需为了当前论文马上做全功能仿真，也不要把 compile error 冒充 runtime fault。可把子问题明确定义为 compile-fault graph localization：在注入前登记故障模块/合同为 ground truth，输入真实 VCS compiler diagnostic 和当前 SACG，要求 builder 输出可核对的 causal slice 和授权修复范围；修复后同一 exact-board VCS compile-only 重验。先用现有单故障形成 end-to-end case；若要报 hit rate，再加少量不同错误类型并逐例列 numerator/denominator。

**targeted revalidation：**选一个当前源码 patch，固定 source snapshot、机器、工具版本和输入。分别执行框架选中的 targeted gates 与预定义 full gate set，记录每一个 gate 的墙钟时间和结果。单组配对足以写“在该 case 中观测到 X 秒/比例”，但不能写一般化平均提速或 2.5x–4x。昂贵 Vivado synthesis 可先排除在 claim 外，只研究 compile/check gate。

### P2：需要更多时间的实验

1A 的因果收益需要同输入的 ACCORD 与无图传播基线；当前单次 run 无法补出对照。2A 的运行时 deadlock/root-cause claim 则需要 runtime-enabled exact-board simulation、真实 DDR 输入和 progress/executed manifest；当前 compile-only policy 不提供这些输入。

## 8. 源码与数据索引

| 评估对象 | 仓库路径/主要入口 |
|---|---|
| 主控制器与阶段恢复 | accagent/framework/agent.py、agent_common.py、flow_action_handoff.py |
| LLM provider/协议和调用 | accagent/framework/llm_config.py、llm_io.py、stage_llm.py、stage_team.py |
| 输入和 board adapter | accagent/framework/stage_input.py、case_adapter.py、case_adapters/ |
| SACG 建图与存储 | accagent/framework/stage_constraints.py、sacg_store.py、sacg_utils.py |
| Template 与流水线 | accagent/framework/stage_templates.py、stage_pipeline.py、templates/operator_chisel/ |
| DSE 与参数绑定 | accagent/framework/stage_params.py、dse_candidates.py、dse_estimator.py、dse_ledger.py、dse_calibration.py |
| Chisel/验证计划 | accagent/framework/stage_code_generation.py、stage_verification_plan.py |
| Verification/evidence policy | accagent/framework/stage_verification.py、verification_evidence_contract.py、contract_identity.py、trace_identity.py |
| CCTG/repair | accagent/framework/sacg_cctg_causal_slice.py、stage_debug_loop.py、stage_repair.py、stage_repair_execute.py |
| Vivado/timing repair | accagent/framework/stage_backend.py、codegen_source_repair.py、dse_timing_calibration.py |
| Mechanism tests | tests/test_sacg_cctg_causal_slice.py、tests/test_verification_evidence_contract.py |
| 研究故事和完整流程说明 | docs/agent_framework_design.md |
| 核心机制实验原计划 | accagent/docs/new_core_method_eval.md |
| 固定 GPT-2 Medium seq32 任务设置 | accagent/experiments/gpt2_medium_seq32_20261027/task_spec.md |
| 1A/1B 真实结果 | accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029/REPORT.md、final_report.json、execution_summary.json |
| T7 扩展案例 | accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/T7-cross-token-reuse-1/ |
| 2A/2B 结果与边界 | accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/README.md |
| 2A VCS fault 原始结果 | accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/compile_fault_pilot_20261029/RESULT.md |
| 2B stale-report replay | accagent/experiments/gpt2_medium_seq32_20261027/method2_2a_2b_20261029/2b_stale_report_replay_20261029/result.json |
| 三线 QoR 与上下文进度 | docs/current_framework_and_experiment_status_2026-10-29.md、docs/context_2026-03-27.md |

## 9. 请 Gemini 回答的问题

1. 按当前源码与真实报告，论文的核心技术贡献应如何准确表述？哪些属于已实现能力，哪些有足够实证，哪些目前只能作为设计目标？
2. 1B 的 Stage-4 参数物化和下游 cyclic_stream_wait 阻塞应怎样定义指标，才能既呈现已有工作又不把未测的传播效果说成失败或成功？
3. 在 compile-only 的实际约束下，compile-fault CCTG causal slice 是否可以形成一个有意义、可复核的子机制实验？所需的最小 ground truth 和 graph evidence 是什么？
4. 对 targeted revalidation，最小但可信的配对计时应如何定义 targeted set、full set、相同输入和计时范围？
5. T7 reuse=1 应作为探索性 case 如何报告，才能避免把原 DSE 域外结果混进主 pilot？
6. 当前 repair executor 的高度集中、证据合同和恢复路径有哪些最值得优先简化或测试的通用风险？哪些不应在截稿前大范围重构？
7. 现有 GPT-6.1、DeepSeek、Claude 硬件 QoR 比较在同一 candidate fingerprint 下，论文应如何呈现“上游 LLM 泛化”与 source archive 变化的关系？
8. 请给出截稿前最小的下一步实验顺序，并逐项标出会产生的新数据、预计成本、可支持的 claim 和仍不能支持的 claim。

## 10. 对外传阅时的注意事项

本交接材料不包含任何 API key、token、私有连接凭证或本地模型缓存内容。若将源代码也交给 Gemini，应只选择框架源文件和上述小型报告，不需要模型权重、checkpoint、Vivado 中间数据库或全量生成波形。

本次工作树有大量已修改/未跟踪文件；本次只计划新增本交接文档并在 context 文档追加索引，不清理、不回滚其他文件。结果报告里的 source archive hash、tool report 和实验目录是历史测量身份；请不要仅凭当前工作树源码推断过去 QoR 对应的源码。
