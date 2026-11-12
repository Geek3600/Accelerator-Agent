# SpatialAccAgent 核心机制实验全量进展报告

**报告日期：** 2026-11-01（Asia/Shanghai）

**报告目的：** 将机制实验从最初的 ACCORD/DCG/CCTG pilot 到最新的 TraceBench v5、PropBench v3 和 Paired Timing v3 全部整理在同一份可独立阅读的正文中。

**阅读约定：** 本文不要求读者再打开其他文档才能理解实验过程、结果、阻塞和结论边界。

**数据原则：** 观测结果来自真实持久化 run、机器可读 JSON、远端 VCS 日志、Vivado 报告和框架单测输出。

**状态原则：** 计划目标、实验假设、受控 fixture、真实工具结果和作者推断分开叙述。

**不确定性原则：** 没有执行的指标写为“未测量”，不把缺失结果写成零。

**证据原则：** `vcs_compile_only` 证明源文件编译、展开和链接层面的结构闭合，不证明 RTL 数值仿真、DDR 权重消费、周期计数或上板运行。

**时间原则：** 文档按实验发生顺序说明演进，但最终结论以同一实验的最新、未被作废的机器结果为准。

**源码原则：** 历史实验绑定各自的 source archive、source fingerprint、SACG snapshot 和工具报告，不能把当前工作树的修改自动转绑到历史结果。

**范围原则：** 本文讨论的是面向 FPGA Transformer 空间加速器的领域 agent 工作流，而不是通用聊天型 multi-agent 系统。

**核心机制范围：** 机制实验围绕前向约束传播、跨阶段参数物化、依赖引导故障诊断、证据失效检测和针对性重验证五个相互关联的能力展开。

**实验编号说明：** 早期计划使用 E1/E2/E3/E4 表示证据绑定、参数修订和编译修复等 pilot；后续控制计划使用 1A、1B、2A、2B 表示更细的机制问题。

**报告口径：** 同名实验在不同版本中的数字不强行合并；每一轮的 runner policy、输入快照和评分方式都在正文中说明。

**最重要的总判断：** 当前已经有真实、可追溯的机制实现和多个有限 pilot 证据，但尚未形成能支持所有原计划统计主张的完整端到端对照 cohort。

**最重要的正面结果：** 真实 SACG 前向图状态可持久化，参数物化检查能捕获冻结 Stage-5 binding 造成的 stale mismatch，静态生成源投影能在部分样本上给出候选范围，证据 hash drift 能被拒绝。

**最重要的未完成项：** 1B 原始 T1-T6 被同一个 `cyclic_stream_wait` Stage-4 风险门阻断；PropBench v3 十行实际共享同一套 SV；TraceBench v5 的原始上游 anchor Top-1 为 2/10，但两个命中来自 shared-resource 候选排序；Paired Timing v3 的四个 full suites 都有失败，且其静态检查传入原 run，没有完整使用变异副本。

**最重要的证据缺口：** 没有 runtime CCTG 事件闭环，没有完整修复授权和补丁越界统计，没有同快照且 full suite 全绿的生产重验证效率对照。

**当前文档不是论文中的宣传稿：** 它保留失败、作废、重复运行、策略变化和未完成状态，方便后续评估和实验规划。

## 1. 研究对象和机制问题

SpatialAccAgent 的输入是目标 Transformer 模型、量化策略、目标 FPGA、板卡样例工程和设计目标。

系统先抽取模型尺寸、算子语义、层间关系、数据类型和板卡接口约束。

系统再把这些事实组织为结构化的 Spatial Accelerator Contract Graph，即 SACG。

SACG 记录设计节点、约束节点、产物节点、模板绑定和跨阶段依赖边。

系统使用语言模型负责理解规格、提出候选、解释工具报告和生成受限动作。

系统使用确定性框架负责状态保存、候选物化、源码生成、工具调用、证据绑定和阶段门控制。

这种分工的目的不是让 LLM 自由生成任意 RTL。

LLM 的输出必须被当前设计事实、候选参数域、模板接口和工具证据约束。

框架需要知道某一次设计修改会影响哪些参数、文件、适配器、权重清单和验证门。

这就是前向依赖传播机制要回答的问题。

框架还需要从下游 VCS、契约检查或 Vivado 时序错误反向找出可能受影响的设计节点。

这就是依赖引导故障追踪机制要回答的问题。

框架还需要知道旧报告在源码或配置变化后是否还能复用。

这就是 evidence binding 和 targeted revalidation 机制要回答的问题。

实验没有把这些能力合成一个单一指标。

每个机制都分别检查其输入、状态变化、工具动作和可复核的输出。

## 2. 统一硬件和实验环境

Medium 主实验的目标模型是 `openai-community/gpt2-medium`。

该模型配置为 24 层。

隐藏维度为 1024。

注意力头数为 16。

MLP 中间维度为 4096。

batch size 为 1。

seq16 和 seq32 两类历史运行都被保留。

当前机制主 run 使用 GPT-2 Medium seq32。

数值策略是 W4A8。

乘法和累加路径采用整数 DSP 方案。

实验板卡 profile 是 VU9P 目标环境。

DDR refill 宽度是 512 bit。

权重的逻辑主存储位置是 DDR。

片上仍保留受限的 active/shadow 权重 cache。

cache 用于计算期间的复用和下一层预取。

激活路径使用 ping-pong 或双缓冲语义。

FIFO、weight cache、activation bank 和 stream adapter 都属于物化后的硬件产物。

目标数据流是 operator-level token overlap。

该目标不要求每个 stage 在同一个周期开始和结束。

ready/valid 和 backpressure 才是不同 token 重叠运行的必要条件。

机制实验阶段没有将完整 RTL 数值仿真作为每个 pilot 的强制门。

当前主实验 policy 是 `vcs_compile_only`。

这个 policy 允许快速验证 Chisel 展开、Verilog 编译、参数展开、端口和链接结构。

这个 policy 不会产生 runtime `progress_event_log.jsonl`。

这个 policy 也不会产生 `board_simulation_executed_manifest.json`。

因此 runtime CCTG builder 在没有额外证据时必须返回 `insufficient_evidence`。

这不是工具错误，而是当前验证 policy 的直接结果。

## 3. Agent 全流程与机制挂接位置

Stage 0 负责归一化模型、量化、板卡、工具和任务输入。

Stage 0 的关键产物是 task card、model profile、board profile 和输入事实记录。

Stage 1 负责约束抽取并初始化 SACG。

Stage 1 把模型维度、量化策略、接口限制和资源上限变成结构化约束。

Stage 2 负责可信模板和器件 IP 的选择。

Stage 2 为模型算子绑定 Chisel/RTL 模板。

Stage 2 还记录模板 provenance、接口和数值语义。

Stage 3 负责流水线规划和 stream graph 构造。

Stage 3 记录 operator stage、token stream、FIFO、shape、ready/valid 和边界契约。

Stage 4 负责 DSE 候选生成、参数绑定和资源/周期估算。

Stage 4 是原始 T1-T6 的阻塞位置。

Stage 5 负责 Chisel/Verilog 生成、编译、展开和 materialization check。

Stage 5 是 PropBench v2/v3 的主要执行层。

Stage 6 负责 leaf、single-layer、multilayer、AXI/DDR 和 board compile gate。

Stage 6 的 compile-only 分支是 T7、Gemma 和部分 R1-R4 的主要证据来源。

Stage 6 的 debug loop 负责读取真实工具错误、准备 repair action 和重新执行同层 gate。

Stage 7 负责 Vivado synthesis、timing、resource 和时序优化。

Stage 7 的结果被用于硬件 QoR，不自动成为 2A CCTG 样本。

阶段之间不是简单的串行脚本调用。

每个阶段都需要读取前一阶段持久化的 SACG、artifact、evidence 和 checkpoint。

当设计字段变化时，框架应沿图边刷新受影响产物。

当工具错误发生时，框架应沿证据和依赖边生成诊断上下文。

当源码 hash 变化时，旧验证证据必须按契约失效或重新绑定。

## 4. SACG、DCG 和 CCTG 的实现含义

SACG 的节点包括模型算子节点、流水线节点、设计空间节点、模板节点和产物节点。

SACG 的边包括模型顺序边、stream/dataflow 边、约束边、物化边和依赖边。

输入归一化与 Stage-1 初始图主要表达模型和硬件约束。

Stage-2 图增加模板和产物关系。

Stage-3 图增加 stream topology 和 token-level pipeline 关系。

Stage-4 图把候选参数和 DSE 结果关联到设计节点。

Stage-5 图把 GeneratedDesignParams、Scala、SV、adapter 和 manifest 关联起来。

Stage-6 图把 source、tool log、verification report 和 gate certificate 绑定起来。

Stage-7 图把 timing endpoint、source closure、Vivado report 和 QoR 记录绑定起来。

前向传播是从上游事实和参数节点走向下游模板、流、RTL 和证据节点。

反向投影是从 failure source 或 failure boundary 走入图并沿 incoming edge 找候选依赖。

旧版本把这种反向投影称为 CCTG，但当前代码明确区分静态 projection 和 runtime causal slice。

`build_static_failure_context()` 首先读取 SACG JSON。

它计算当前 SACG 文件的 SHA-256。

它要求 failure report 中声明的 SACG hash 与当前 snapshot 完全一致。

如果 hash 不匹配，它返回 blocker 而不猜测根因。

它根据 failure class 区分 compile-time、contract 和 synthesis_timing 域。

它读取 failure report 中的 source_file、affected_source_paths 和 failure_symbols。

它把 source path 与 SACG artifact path 做精确绑定。

它使用 pipeline node 记录的 source、template_id、op、kind 和 stage_id 生成 aliases。

它用 generated source module stem 与这些 aliases 做保守匹配。

它为 wrapper 和 shared physical resource 返回候选集合，而不是强行指定单一根因。

它沿边回溯 upstream dependency context。

它可以形成 candidate repair scope。

它不会直接授予 `authorized_repair_scope`。

实际修改权限必须经过独立的 repair authorization gate。

因此静态 projection 的候选范围和可写范围是两个不同字段。

runtime CCTG 需要真实事件序列、执行 manifest、token progress 和边界交叉证据。

没有这些文件时，代码将 `runtime_causal_claim` 置为 false。

这一区分是本次实验报告中反复出现的关键边界。

## 5. Evidence binding 和 revalidation resolver

证据合同把 functional、backend、runtime 和 promotion report 绑定到源码与工具环境。

证据记录包含 source hash、tool log hash、输入 fingerprint 和 gate identity。

RTL 行为变化通常会使 functional 和 backend 证据失效。

XDC clock period 变化通常只使 backend timing 证据失效。

模型参数变化通常会使 functional 和 backend 证据失效。

与构建无关的文档变化应继续复用硬件证据。

E1-E4 fixture 就是对这四类规则的确定性检查。

旧版本的 Paired Timing v2 使用实验脚本内的手选 targeted gate。

这导致它可以记录命令墙钟差，但不能证明 production resolver 的选择行为。

后续新增 `resolve_revalidation_gates()`。

resolver 从 invalidated evidence records 读取 gate、provider_gate、required_gates 和 dependency closure。

resolver 对声明的依赖递归展开。

resolver 接受可用 gate 集合作为执行计划过滤器。

不可用的声明 gate 被放入 unavailable_declared_gates。

不可用 gate 不会被静默删除。

没有 invalidated evidence 时，resolver 返回 empty。

有 evidence 但没有可执行 gate 时，resolver 可返回 blocked。

Paired Timing v3 使用 production resolver，而不是为每个案例硬编码 targeted gate。

但 resolver 正确接入并不代表每个 mutation 都会产生 targeted gate。

文档型和某些 operator RTL mutation 在当前 case adapter 记录中没有 production invalidation。

这些案例的 targeted gate 数量是零。

这正是 v3 没有输出虚假的 100% reduction 的原因。

## 6. 实验计划的原始意图

最早的计划希望用多个 baseline 和重复样本证明机制收益。

计划中的 B0 是没有 SACG/DCG 自动传播的 handoff-only baseline。

计划中的 B1 是有静态图但不自动传播的消融。

计划中的 B2 是保留 DCG 但移除 guided repair 的 baseline。

ACCORD 是拥有图传播、契约检查、证据和 repair scope 的完整 profile。

1A 的目标是观察模型到 template、pipeline 和 RTL 的前向图构建。

1B 的目标是比较单字段修改后的受影响产物同步和无关产物保持。

2A 的目标是从故障表象追踪依赖、生成受限范围并同层重验。

2B 的目标是检查证据变化后的失效判断和 targeted/full 重验证代价。

早期计划曾提出较大的重复次数和严格统计指标。

受限于实际 agent、VCS、板级输入和远端工具条件，项目先执行代表性 pilot。

pilot 结果不能自动升级成原计划完整评分。

后续计划文件还提出过将 compile-only 结果作为主要结构门。

这可以支持结构一致性结论，但不能替代 runtime 功能证据。

## 7. 时间线总览

2026-10-23 首先整理了 Small 设计上的 DCG 和 CCTG 快速案例。

2026-10-23 的策略是先拿已有真实材料做轻量、可解释的机制案例。

2026-10-23 的 lanes 16 到 8 案例形成了早期 ACCORD/B0 Stage-4/5 pilot。

2026-10-23 的 Gemma CCTG 案例从真实 VCS 编译故障开始。

2026-10-24 完成 cache tile 和 activation banks 的 Small revision pilot。

2026-10-24 完成 cross-token reuse 的重新绑定和 compile-only 检查。

2026-10-24 形成一次 B2 prompt-isolated replay。

2026-10-26 启动 GPT-2 Medium 机制迁移和 evidence-binding 重跑。

2026-10-26 完成 Medium E1-E4 deterministic fixture。

2026-10-26 Gemma B2 compile failure 到 pass 案例被整理为 compile-time repair pilot。

2026-10-27 GPT-2 Medium seq32 主 run 形成 1A 前向快照和 1B T1-T6 pilot。

2026-10-29 形成 2A/2B 的静态 probe、report replay 和 gate timing 目录。

2026-10-29 形成 `current_framework_and_experiment_status_2026-10-29.md`。

2026-10-29 形成 `gemini_review_handoff_2026-10-29.md`。

2026-10-30 修正 VCS evidence analyzer 与静态 SACG source mapping。

2026-10-30 修正了若干 2A 诊断字段和证据绑定细节。

2026-10-31 TraceBench v5、PropBench v3 和 Paired Timing v3 完成。

2026-10-31 创建了机制实验状态摘要，但该摘要不是本报告的替代品。

2026-11-01 将所有历史尝试合并成本文的连续正文。

## 8. Small 时代的早期 DCG 参数修订

Small 时代的第一个主要案例是 compute parallelism 的变化。

显式 lanes 16 到 8 的请求由 ACCORD 和 B0 各执行一次。

该案例在 Stage-4/5 都选择了相同的 8-lane、8x8 candidate。

两侧都通过了六项参数检查。

两侧都通过了六个 Chisel compile/elaboration 命令。

该案例没有 VCS 或 Vivado QoR。

因此它只说明两个 profile 在这一输入上都能生成目标结构。

它没有显示 DCG 和 B0 的行为差异。

inferred lanes 16 到 8 的请求把阵列几何交给约束推导。

该案例同样形成 ACCORD/B0 配对。

两侧也选择了相同 candidate fingerprint `7ad3a71d15fd...`。

两侧 Stage-4 参数检查都为 6/6 pass。

两侧 Stage-5 compile/elaboration 都完成。

ACCORD 和 B0 的 Stage-5 wall time 分别约为 161.203 秒和 156.440 秒。

该时间差没有被设计成方法收益指标。

任务卡明确只要求 Stage-4/5 pilot。

该 case 没有 VCS、综合或性能数据。

Small cache tile revision 的第一份目录由于 stale constraint snapshot 被标记 invalid setup。

它没有被计入有效 revision 样本。

随后建立了 v2 目录重新固定 checkpoint 和输入。

cache tile 从 256 words 改为 512 words。

ACCORD 绑定了 512。

B0 也绑定了 512。

两侧 Stage-4 参数检查都是 6/6 pass。

两侧 Stage-5 Chisel compile/elaboration 都是 6/6 pass。

两侧在去除 cache、日志和 simulation metadata 后有 134 个源级文件 hash 一致。

这个结果显示当 baseline 也能读取相同任务和参数时，ACCORD 并没有在该 case 中形成可测选择差异。

该 case 没有 VCS、仿真、综合或 QoR。

Small activation banks revision 把 activation banks 从 4 改为 2。

ACCORD 和 B0 都绑定到 2。

两侧 Stage-4 都为 6/6 pass。

两侧 Stage-5 都为 6/6 pass。

两侧有 121 个源级生成文件 hash 一致。

同样没有出现可归因的图传播选择差异。

Small cross-token reuse revision 原意是从 8 改为 4。

第一轮目录因为 task/design-space input binding mismatch 被作废。

重新建立的 v2 记录固定了输入 hash。

该 case 两侧进入 Stage-4。

后续记录显示双方在 compile-only 口径下可以形成 VCS 结构闭合。

其中后续 ACCORD 进行了额外的 run-local timing repair。

B0 没有对称进行相同 timing repair。

所以不能把后续 QoR 差异归因于 DCG。

## 9. Small 时代的 evidence binding 实验

Small E1 使用 RTL 行为变化作为 mutation。

预期是 functional 和 backend 证据都失效。

实际 checker 符合预期。

Small E2 使用 XDC clock period 变化。

预期是 backend 证据失效而较低层 functional 证据继续复用。

实际 checker 符合预期。

Small E3 使用模型参数变化。

预期是 functional 和 backend 证据失效。

实际 checker 符合预期。

Small E4 使用与构建无关的文档变化。

预期是硬件证据继续复用。

实际 checker 符合预期。

Small E1-E4 结果是 4/4 expected outcomes。

Small fixtures 的 stale-evidence acceptance 是 0。

Small fixtures 的 false invalidation 是 0。

这些用例没有调用 Agent。

这些用例没有调用 VCS。

这些用例没有调用 Vivado。

因此它们证明的是证据合同的确定性逻辑，而不是端到端硬件实验。

Small 早期还有一次 E1-E4 初始尝试只完成 2/4。

该初始尝试被保留为 debugging record。

后续 4/4 结果才是有效的 Small fixture 结果。

初始 2/4 不能被重复计数为独立样本。

## 10. Gemma 编译故障和 B2 replay

Gemma 案例来自真实 board compute-slot VCS compile failure。

编译器报告 `Error-[IND] Identifier not declared`。

报告涉及 `write_busy` 的使用早于声明。

相同的声明顺序问题也影响 `rstate`。

相同的声明顺序问题也影响 `read_kind`。

Agent 根据 compiler diagnostic 将声明移动到首次使用之前。

Agent 删除了后续重复声明。

修复只作用于 run-local `compute_slot.sv`。

修复没有改变 kernel interface。

修复没有改变 AXI route。

修复没有改变数值算法。

修复没有改变 pipeline stage 语义。

第一次 patch action 因已有 weight-binding manifest 使用 `create` 而被拒绝。

该次拒绝没有写入源码。

对应 iteration 4 的 generation 调用耗时约 735.4 秒。

后续 patch action 改为对已有文件执行 `replace`。

replace patch 成功应用。

对应 iteration 5 的 generation 调用约 87.7 秒，另有 repair-agent 调用约 75.7 秒。

这些是不同角色的调用耗时，不应相加后称为独立 VCS CPU time。

修复前源码 SHA-256 是 `2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`。

修复后源码 SHA-256 是 `6d2d3192a7628bde1956c5e39bb0076f4503cd9921e1df82872b2c5110fe12c0`。

原始记录中的修复后 hash 以对应 run report 为准。

修复后 VCS compile 返回码是 0。

修复后 VCS elaboration 返回码是 0。

修复后 VCS link 返回码是 0。

编译闭环涉及 33 个模块。

VCS compile CPU 时间约为 67.761 秒。

VCS elaboration CPU 时间约为 1.630 秒。

VCS link CPU 时间约为 0.403 秒。

仿真按 compile-only policy 跳过。

因此这是一次真实 compile failure 到 compile-only pass。

它不是 runtime CCTG 诊断成功率样本。

失败报告没有非空 hash-bound CCTG causal slice。

该案例的错误也可以由 compiler diagnostic 直接提示。

因此该案例不能证明图引导相对普通日志读取的因果收益。

B2 prompt-isolated replay 的目的，是观察移除 guided repair 文案后 Agent 是否仍能完成同一局部修复。

原始 B2 prompt 仍有过残留的通用 causally affected interface family 文案。

后续审计把这条通用文案加入过滤范围。

含残留文案的早期 replay 不能被称为完全干净的 CCTG 消融计分。

后续 `cctg_b2_prompt_clean_20261024T1105+0800` 是另一轮实际完成的 compile-only replay。

该轮过滤后实际 repair/generation prompt 的 CCTG policy、因果修复指引与历史修复词组审查均为零次命中。

它从同一 faulty compute_slot hash 开始，复用已验证的 leaf/single-layer closure。

它的 manifest 标为 completed_compile_only，但仍只是单个 exploratory case。

修复 prompt SHA 为 `2f8ce5d06f37223d66aa1de3c679af59323e65d4208d12986b4fa16c747be311`。

成功 generation prompt SHA 为 `aa1b766edd3aa39d80a28488beab257f7f8b312aa275d35fa3b419a6642c3239`。

该 clean replay 可以作为 B2 文案隔离修复后的记录，仍没有历史 ACCORD 的非空 hash-bound causal slice，因此不能建立 CCTG 的因果收益。

## 11. Gemma exact-board compile-only gate

Gemma `e3_gemma_exact_runtime_20261026/run/` 还记录了一次 Stage-6 compile-only gate。

debug loop report 标为 pass。

AXI/DDR interface compile gate 标为 pass。

远端 VCS compile、elaboration 和 link 返回码为 0。

总 wall time 约为 108.313 秒。

VCS compile CPU time 约为 72.041 秒。

VCS elaboration CPU time 约为 1.610 秒。

VCS link CPU time 约为 0.431 秒。

输入清单包含 51 个 source IDs。

VCS 实际报告编译 34 个 modules。

顶层是 `sacg_board_compile_tb`。

模式是 `compute_slot_axi`。

manifest 记录 26 层和 338 个模型权重 hash 项。

但是 compiled sample source IDs 为 0。

报告中的 artifacts 为空。

因此 manifest 记录不等于 DUT 已经消费权重。

simulation_skipped 为 true。

exact_board_acceptance_passed 为 false。

pipeline_overlap_passed 没有运行时证据。

这个 gate 只能证明 generated kernel 和 compute-slot adapter 在 compile-only 结构层闭合。

## 12. Medium 迁移准备

GPT-2 Small 的历史实验不能直接改名为 GPT-2 Medium。

Medium inventory 明确将 Small run 保持为 immutable historical evidence。

Medium 的参数候选必须从 Medium Stage-4 合法表重新产生。

Medium 的模型配置和 hidden size 不能复用 Small 的事实。

Medium 的机制迁移包含 explicit lanes、inferred lanes、cache tile、activation banks 和 cross-token reuse。

Medium E1-E4 从 Medium generated RTL、model config、XDC 和 documentation 重新建立。

Medium 机制 runner 的目标是最多同时执行两个 profile job。

runner 使用 GPT-6.1 agent-only 环境文件。

runner 会清理继承的其他 LLM route 和 credential 环境变量。

这样做是为了避免上游 endpoint 混用污染实验。

Medium inventory 说明 Stage-6 和 Vivado 不是启动 Stage-4/5 机制 pilot 的前置条件。

Medium 机制 pilot 先验证参数物化和代码生成。

Medium 的正式 QoR 仍需要独立 Stage-7 source-bound reports。

Medium inventory 也保留了 stale-state lanes 目录。

stale-state 目录没有被当作新的独立样本。

第一轮 cross-token reuse input mismatch 目录同样被排除。

## 13. GPT-2 Medium seq32 的 1A 前向实验

主 run 目录是 `accagent/experiments/gpt2_medium_seq32_20261027`。

1A 使用该 run 的真实 Stage-0、Stage-1、Stage-2 和 Stage-3 状态。

Stage-1 constraint extraction 快照的图边数是 7。

Stage-2 template selection 快照的图边数仍是 7。

Stage-3 pipeline planning 快照的图边数是 18。

`7 -> 7 -> 18` 对应这三个持久化阶段；不能误写为三个不同的 Stage-0 输入快照。

最终图中有 7 条 model-order edges。

最终图中有 11 条 stream/dataflow edges。

Template Selection 快照有 20 个 nodes。

Template Selection 快照有 7 条 edges。

Template Selection 快照有 16 个 constraints。

Template Selection 快照有 16 个 artifacts。

Pipeline Planning 快照有 30 个 nodes。

Pipeline Planning 快照有 18 条 edges。

Pipeline Planning 快照有 23 个 constraints。

Pipeline Planning 快照有 18 个 artifacts。

Stage-3 pipeline checker 报告 11 pass。

Stage-3 pipeline checker 报告 0 fail。

Stage-3 pipeline checker 报告 0 error。

这一条 run 说明 SACG 会随着模板和流水线阶段增加关系。

这一条 run 说明 stream edge 不是仅由模型顺序边复制出来的。

这一条 run 说明图状态被持久化到 JSON。

这一条 run 没有 B0 或 Flat-Config matched cohort。

这一条 run 没有 Unstructured-History matched cohort。

这一条 run 没有 Stage-7 first-pass integration comparison。

因此它不能给出参数传播 accuracy。

它不能给出 first-pass integration rate。

它不能给出相对违例率下降。

它不能给出 DCG 相对 baseline 的因果收益。

1A 最适合被描述为真实 forward graph construction case。

1A 不是一个统计对照实验。

## 14. GPT-2 Medium seq32 的 1B T1-T6 原始实验

1B 的六个任务从源 run 的 360-row Stage-4 表选择候选。

T1 将 compute array rows 从 16 改为 8。

T1 的 candidate ID 是 `arch_b927f500990e`。

T2 将 compute array cols 从 32 改为 16。

T2 的 candidate ID 是 `arch_755a0908dcb3`。

T3 将 stream FIFO depth 从 64 改为 128。

T3 的 candidate ID 是 `arch_3fd8f432a88e`。

T4 将 activation banks 从 2 改为 4。

T4 的 candidate ID 是 `arch_63e2712b0d8c`。

T5 将 cross-token reuse 从 16 改为 8。

T5 的 candidate ID 是 `arch_3fedd13a9880`。

T6 将 cross-token reuse 从 16 改为 4。

T6 的 candidate ID 是 `arch_6226a7032ff5`。

ACCORD 运行 T1-T6 各一份。

B0 运行 T1-T6 各一份。

总数是 12 个 Stage-4 jobs。

12 个 jobs 的 candidate materialization.status 都是 pass。

12 个 jobs 都没有 materialization errors。

因此物化动作本身不是阻塞原因。

每个 job 都重新计算了单候选 DSE。

每个 job 都在 eligibility 阶段看到 `cycle_model_status=blocked`。

每个 job 都命中了 `cyclic_stream_wait`。

每个 job 都得到 zero feasible candidate。

每个 job 最终返回码是 2。

没有任何 T1-T6 进入 Stage-5 Chisel generation。

没有任何 T1-T6 进入 Stage-6 VCS compile-only。

没有任何 T1-T6 产生 Stage-5/6 propagation score。

阻塞并不是 VCS syntax error。

阻塞也不是 Chisel elaboration error。

阻塞发生在候选选择之前。

`stage_params.bind_parameters()` 调用了 `build_dse_search()`。

`build_dse_search()` 先物化 candidate fields。

`cost_features()` 再计算 cycle model 状态。

blocked 状态被转换为 record.feasible=false。

硬约束错误被追加到候选记录。

最终 eligible set 为空。

候选选择器抛出 no eligible candidate。

源码模式检查关注 Attention output-projection wait。

源码模式检查也关注 Linear input-chunk collection wait。

它推断 chunk 大于一时可能存在结构性循环等待风险。

它没有运行 RTL simulation。

它没有运行 formal deadlock proof。

所以它不是 runtime deadlock 的独立证明。

但它也不是简单的“缺少周期数据”。

它确实识别了当前模板调度结构中的静态风险。

T1-T6 的下游指标必须写成 not measured。

affected artifact recall 在 T1-T6 中是 not measured。

unrelated artifact preservation 在 T1-T6 中是 not measured。

contract check rate 在 T1-T6 中是 not measured。

Stage-5 Pass@1 在 T1-T6 中是 not measured。

Stage-6 Pass@1 在 T1-T6 中是 not measured。

这些指标不是零。

它们只是因为流程没有越过 Stage-4 而没有分母。

## 15. T7 reuse=1 扩展案例

T7 将 cross-token reuse 从 16 改为 1。

T7 不属于原始 preregistered domain `[4, 8, 16]`。

因此 T7 必须单独标为 domain-extension exploratory case。

T7 的 candidate ID 是 `arch_218334c128b1`。

T7 candidate fingerprint 是 `218334c128b1706852d811e722c585eb22ec0b8efc0fdd9f5052ddad71c04253`。

T7 的 reuse=1 使静态 schedule-risk gate 得以通过。

ACCORD 和 B0 都完成 Stage-4。

ACCORD 和 B0 都形成 Stage-5 code-generation reports。

T7 中 Linear.scala 第 459 行曾触发 Chisel W004。

原因是 tokenTileSize==1 时仍使用 1-bit dynamic index。

修复为 tokenTileSize==1 分支使用常量索引。

修复后 package checks 通过。

修复后 warning-free 目标达成。

T7 后续有 exact-board VCS compile-only pass。

ACCORD 的 compile-only report 为 pass。

B0 的 compile-only report 也为 pass。

这说明在该修复闭环中两边最终都能完成结构编译。

B0 曾出现 `k_in_ready_unused` 未声明。

B0 曾出现 kernel instance 不完整。

B0 曾出现 weight manifest 与生成源码不一致。

repair loop 对 adapter 和 weight-binding manifest 做了局部修复。

修复后 VCS compile/elaboration/link 返回码为 0。

但 T7 的 board top 是 compile testbench。

T7 的 simulation_skipped 为 true。

T7 的 run_status 是 not_run。

T7 的 exact_board_acceptance_passed 是 false。

T7 没有 runtime DDR event。

T7 没有 nonzero input/weight/output counter。

T7 没有 pipeline overlap runtime proof。

因此 T7 只能证明一个域外 compile-only parameter/adapter repair case。

T7 不能证明原始 DSE 域的泛化。

T7 不能证明 runtime function。

T7 不能证明 CCTG root-cause localization。

## 16. reuse=1 R1-R4 补充参数实验

R1 将 rows 从 16 改为 8，并固定 reuse=1。

R2 将 cols 从 32 改为 16，并固定 reuse=1。

R3 将 FIFO depth 从 64 改为 128，并固定 reuse=1。

R4 将 activation banks 从 2 改为 4，并固定 reuse=1。

R1 的 ACCORD Stage-4 和 Stage-5 通过。

R1 的 leaf、single-layer 和 multilayer compile-only 报告通过。

R1 的 AXI/DDR preflight fail。

R1 因此没有执行 exact-board VCS。

R2 的 ACCORD Stage-4 和 Stage-5 通过。

R2 的 leaf、single-layer 和 multilayer compile-only 报告通过。

R2 的 board preflight 在 exact-board VCS 前失败。

R3 的 ACCORD Stage-4 和 Stage-5 通过。

R3 的 lower-level compile gates 通过。

R3 的 AXI/DDR contract 没有完成。

R3 没有 exact-board VCS evidence。

R4 的 ACCORD Stage-4 和 Stage-5 通过。

R4 的 lower-level compile gates 通过。

R4 的 AXI/DDR contract 没有完成。

R4 没有 exact-board VCS evidence。

R1-R4 的共同 blocker 是 candidate-local board simulation manifest 缺失或不完整。

R1-R4 还缺 DDR refill 到 weight/bias stream 的完整映射。

R1-R4 还缺 configuration transport 的完整映射。

R1-R4 还缺 layer scheduler 的完整映射。

R1-R4 的 lower-level pass 不能升级为 Stage-6 pass。

R1-R4 的记录没有实现新的 local-only B0 intervention。

所以不能用它们计算 ACCORD versus B0 的传播 recall。

## 17. PropBench v2 frozen-artifact probe

PropBench v2 从 R1 rows=8 和 R2 cols=16 快照开始。

它的核心控制是让 B0 修改 Stage-4 selected parameter。

B0 同时冻结已经生成的 Stage-5 SV tree。

ACCORD 使用与候选一致的 generated parameter。

R1 的 ACCORD materialization check 通过。

R1 的 ACCORD remote `vlogan` 返回码为 0。

R1 的 B0 materialization checker 发现 rows mismatch。

R1 的 B0 source-only `vlogan` 仍返回码为 0。

R2 的 ACCORD materialization check 通过。

R2 的 ACCORD remote `vlogan` 返回码为 0。

R2 的 B0 materialization checker 发现 cols mismatch。

R2 的 B0 source-only `vlogan` 仍返回码为 0。

PropBench v2 metrics 是 ACCORD binding/compile pass 2。

PropBench v2 metrics 是 B0 changed-parameter mismatch detected 2。

PropBench v2 metrics 是 B0 generated SV tree unchanged 2。

PropBench v2 metrics 是 B0 vlogan compiles 2。

这个结果回答了一个窄问题。

窄问题是局部源编译通过时是否仍可能存在 stale parameter binding。

答案是会存在。

materialization checker 能捕获这个 stale binding。

它不能回答完整图上的所有产物是否刷新。

它不能回答 unrelated artifact 是否保留。

它不能回答整个 Stage-6 是否通过。

它不能回答 runtime 或 QoR 是否改善。

## 18. TraceBench v1 和 v2 的问题

TraceBench v1 运行了十个隔离 source compile fault。

v1 的 fault compile failures 是 10/10。

v1 的 candidate scope/source package matches 是 10/10。

v1 的 top1 localization hits 被记录为 10/10。

v1 的 repair revalidation passes 只有 2/10。

v1 的 runtime causal claim 明确为 false。

v1 记录中的修复输出不适合直接作为全面修复成功率。

TraceBench v2 基本复用了相同输入和策略。

v2 也有 10/10 fault compile failure。

v2 也有 10/10 source package match。

v2 的 top1 仍记录为 10/10。

v2 的 repair revalidation 仍记录为 2/10。

v1/v2 的主要问题不是工具没有报错。

主要问题是评分输入和 repair path 没有清楚地区分投影与真值。

后续审计发现更早版本把 ground-truth node id 直接写进了诊断输入。

如果 projector 能读取该字段，10/10 就不是独立定位结果。

该版本结果因此不能用于论文的命中率。

原始目录保持不变以保留 provenance。

## 19. TraceBench v3 的作废原因和结果

TraceBench v3 修改为 remote `vlogan` source compile analysis。

v3 的历史机器汇总曾记录 10/10 Top-1，但复核发现 runner 把 ground-truth node ID 写进了诊断输入。

该输入泄露使 projector 能接触评分答案，所以 v3 的定位结果作废。

把真值限制为事后 scoring-only sidecar 是后续 v4/v5 的修正，不能倒写为 v3 已具备的条件。

v3 的 fault compile failure 是 10/10。

v3 的 same-gate repair revalidation 是 10/10。

v3 的 source package scope match 是 10/10。

v3 的工具编译日志仍可作为真实编译记录保留，但其 root hit 统计不具备独立性。

除标签泄露外，后续 v4 还暴露了当前 R2 SACG 的 source-to-pipeline mapping 不完整。

Attention 和 Activation 的映射存在。

其他 generated source 的 pipeline binding 不完整。

v3 的部分命中不能自动推广到所有模块。

v3 仍明确没有 runtime CCTG。

v3 仍没有 top-level elaboration claim。

v3 仍没有 simulation claim。

v3 仍没有 exact-board acceptance claim。

v3 不是完全无效的工具执行。

它证明 remote `vlogan` 可以对十个隔离 source package 复现 failure 和 pristine pass。

但其 10/10 localization 不应被保留为最终定位统计。

## 20. TraceBench v4 的修正结果

TraceBench v4 修正评分逻辑，不让 ground-truth anchor 参与 projection。

v4 仍运行十个 remote VCS source compile faults。

v4 fault compile failure 是 10/10。

v4 same-gate revalidation 是 10/10。

v4 candidate scope/source package match 是 10/10。

v4 upstream Top-1 localization 只有 2/10。

命中的主要是 Attention 和 Activation。

其余模块缺少精确 pipeline node binding。

v4 repair authorization granted 是 0。

v4 没有调用 production repair authorization gate。

因此 v4 不能报告 authorized repair scope。

v4 的 10/10 revalidation 是恢复 pristine source 再同门限编译。

它不是 Agent 生成 patch 后的 10/10 repair success。

v4 的事实暴露了 source mapping 的工程缺口。

该缺口比单纯补一个命中率脚本更重要。

它说明 SACG 必须完整记录每个 generated module 的 materialization edge。

## 21. TraceBench v5 的最终静态投影

TraceBench v5 进一步改成 downstream integration fault。

注入 fault 的 source 是下游 generated source。

预期 upstream anchor 只保留在 scoring sidecar。

projector 输入只包含 downstream source 和 VCS report。

v5 共有 10 个案例。

v5 fault compile failure 是 10/10。

v5 pristine same-gate revalidation 是 10/10。

v5 downstream scope hits 是 6/10。

v5 upstream anchor Top-1 hits 是 2/10。

v5 repair authorizations invoked 是 0。

v5 runtime causal claim 是 false。

v5 的十个案例分别覆盖 AXI wrapper、compute top、Attention、IntegerAttention、Linear、Activation、Residual、FIFO、weight cache 和 QKV 等 source package。

AXI wrapper 的候选范围落在 block input/block output integration boundary。

compute top 同样落在 integration boundary candidate set。

Attention 能映射到 stage 01 self attention。

IntegerAttention 在当前 snapshot 没有稳定的精确 candidate。

Linear 在当前 snapshot 没有稳定的精确 candidate。

Activation 同时出现 pipeline stage 和 model-op 候选。

Residual 当前没有唯一 pipeline candidate。

FIFO 作为 shared physical resource 映射到多个 stage candidate。

weight cache 作为 shared physical resource 映射到多个 stage candidate。

QKV 当前 source-to-node mapping 不完整。

v5 的 downstream scope hit 不能写成 root-cause hit。

v5 的 same-gate revalidation 不能写成 Agent repair pass。

原因是 repair bundle 是 pristine source restoration。

production repair authorization 没有被调用。

v5 只能支持“静态 generated-source materialization projection 和受限同门限恢复编译”。

它不能支持“runtime CCTG graph-guided diagnosis”。

它不能支持“两跳 upstream root cause success rate”。

它不能支持“授权 patch scope violation rate”。

它不能支持“LLM repair success rate”。

## 22. TraceBench 每个案例的细节

F1_axi_wrapper 在 fault package 中触发 downstream compile fault。

F1 的候选是 block_input 和 block_output。

F1 的 upstream anchor Top-1 判定为 false；primary 是 block_input，评分 anchor 是 stage_07_residual_add_2。

F1 的 same-gate pristine recompile 返回 0。

F2_compute_top 也命中 block_input 和 block_output 候选。

F2 没有唯一 upstream root。

F2 的 same-gate pristine recompile 返回 0。

F3_attention 命中 stage_01_self_attention。

F3 的 downstream source fault compile 返回 255。

F3 的 pristine source compile 返回 0。

F3 仍没有 repair authorization。

F4_integer_attention 没有 candidate node。

F4 的 source mapping 缺失不能被补成命中。

F4 的 pristine recompile 返回 0 只说明 source restoration 有效。

F5_linear 没有 candidate node。

F5 说明 generated Linear alias 没有在该 snapshot 中形成 pipeline binding。

F6_activation 有两个候选。

F6 的候选包括 stage_05_activation。

F6 的候选还包括 model_op.05_activation。

F6 的排序 primary 是 stage_05_activation，但评分要求的 upstream anchor 是 stage_04_mlp_fc，因此 upstream Top-1 为 false；不能把 pipeline 优先排序解释为上游根因正确。

F7_residual 没有 candidate root。

F7 仍能同门限恢复 source 并通过 VCS。

F8_fifo 的 shared resource 候选覆盖八个 pipeline stage。

F8 的宽候选是保守行为。

F8 的宽候选不等价于根因定位成功。

F9_weight_cache 也覆盖八个 pipeline stage。

F9 说明 shared physical resource 需要更细的 producer/consumer contract。

F10_qkv 没有 candidate root。

F10 说明 QKV materialization facts 尚未完整记录。

十个案例的 VCS failure 都是真实远端 `vlogan` 返回非零。

十个案例的 repair 包都恢复了 pristine source。

但没有一个案例进入生产 repair authorization。

## 23. PropBench v3 的实验设计

PropBench v3 选择 reuse=1 作为 schedule-risk-admitted domain。

它没有启用 warning-only feasibility policy。

它没有修改默认 `record.feasible` 语义。

它共有十个候选。

P1 是 rows 16 到 8。

P2 是 rows 16 到 4。

P3 是 cols 32 到 16。

P4 是 cols 32 到 8。

P5 是 cols 32 到 4。

P6 是 lanes 16 到 8，同时耦合 rows 和 cols 到 8。

P7 是 FIFO 64 到 32。

P8 是 FIFO 64 到 128。

P9 是 activation banks 2 到 4。

P10 是 reuse 16 到 1。

四行复用了已有 Stage-4/5 snapshot。

六行是隔离 Stage-5 generated binding snapshot replay。

这六行不是 cold Agent Stage-4/5 run。

P6 不是单字段变化，因为 lanes、rows、cols 同时变化。

这个事实必须在任何论文表格中保留。

每个 ACCORD row 都生成或改写一个 `GeneratedDesignParams.scala` binding 文本。

这句话不能理解为每个 row 都重新执行了完整 Chisel 生成。

`run_propbench_v3.py::materialize_small_package()` 从固定的 R2 generated source directory 复制或 hard-link SV 文件。

它随后只对 Scala generated parameter source 做候选值替换。

它没有调用 Chisel elaboration 重新生成十套独立的 SV。

十个 row 的 generated SV 相对路径集合均为 45 个文件。

十个 row 的 SV hash map 相同，hash map 的序列化摘要前缀为 `e50bcf0456d346d1`。

所以 ACCORD 的 10/10 VCS pass 实际证明的是同一套 SV source package 在十组 binding/check 任务下可以被远端 `vlogan` 接受。

它没有证明十个不同硬件实现都经过 Chisel 重新展开。

P1、P3、P8、P9 的 `source_case` 指向历史 R1/R2/R3/R4 参数目录。

P2、P4、P5、P6、P7、P10 在 R2 SV 基础上做局部 Scala binding replay。

四行读取不同历史参数，不改变所有行统一取用 R2 SV 的执行事实。

每个 ACCORD row 都运行 materialization checker 和 source-only VCS analysis。

B0 arm 冻结 generated Stage-5 package。

B0 arm 修改 Stage-4 parameter record。

B0 arm 不刷新 generated package。

因此 B0 用于构造 stale materialization mismatch。

这个 B0 是受控 frozen artifact probe。

它不是完整的无图 Agent flow。

## 24. PropBench v3 的十个结果

P1 ACCORD materialization pass。

P1 ACCORD VCS source analysis pass。

P1 B0 materialization mismatch detected。

P1 B0 source-only VCS analysis pass。

P2 ACCORD materialization pass。

P2 ACCORD VCS source analysis pass。

P2 B0 materialization mismatch detected。

P2 B0 source-only VCS analysis pass。

P3 ACCORD materialization pass。

P3 ACCORD VCS source analysis pass。

P3 B0 materialization mismatch detected。

P3 B0 source-only VCS analysis pass。

P4 ACCORD materialization pass。

P4 ACCORD VCS source analysis pass。

P4 B0 materialization mismatch detected。

P4 B0 source-only VCS analysis pass。

P5 ACCORD materialization pass。

P5 ACCORD VCS source analysis pass。

P5 B0 materialization mismatch detected。

P5 B0 source-only VCS analysis pass。

P6 ACCORD materialization pass。

P6 ACCORD VCS source analysis pass。

P6 B0 materialization mismatch detected。

P6 B0 source-only VCS analysis pass。

P7 ACCORD materialization pass。

P7 ACCORD VCS source analysis pass。

P7 B0 materialization mismatch detected。

P7 B0 source-only VCS analysis pass。

P8 ACCORD materialization pass。

P8 ACCORD VCS source analysis pass。

P8 B0 materialization mismatch detected。

P8 B0 source-only VCS analysis pass。

P9 ACCORD materialization pass。

P9 ACCORD VCS source analysis pass。

P9 B0 materialization mismatch detected。

P9 B0 source-only VCS analysis pass。

P10 ACCORD materialization pass。

P10 ACCORD VCS source analysis pass。

P10 B0 materialization mismatch detected。

P10 B0 source-only VCS analysis pass。

最终 ACCORD materialization passes 是 10/10。

最终 ACCORD VCS passes 是 10/10。

最终 B0 mismatch detections 是 10/10。

最终 B0 source-only VCS passes 是 10/10。

这个结果很清楚地展示了“编译通过不等于参数物化一致”。

它也展示了跨阶段 checker 可以发现冻结产物与 Stage-4 参数的不一致。

但该实验的 VCS pass 不能被解释成十个真实硬件候选的 VCS pass。

它们共享同一 SV source hash，变化主要发生在检查器读取的 Scala binding 文本和 Stage-4 record。

`unrelated_sv_preserved = bool(source_hashes)` 也不是 preservation measurement。

这个字段只判断 source hash dictionary 非空。

它没有把变异前 hash map 与变异后 hash map 做逐文件比较。

它没有拿理论 unaffected set 或 oracle artifact set 计算 precision/recall。

因此 PropBench v3 的机器结果中没有合法的 `Affected-Artifact Sync Recall` 或 `Unrelated-Artifact Preservation` 数值。

`expected_changed_artifact_classes` 由 runner 固定为两个路径类别，也不是从 SACG 图遍历得到的实际 affected set。

P6 同时改变 lanes、compute_array_rows 和 compute_array_cols，不能作为单字段传播样本。

P2、P7、P10 的候选实际继承 R2 的 cols=16，不能仅按任务名称假定它们都以 cols=32 为 source baseline。

但是它没有测量全 SACG artifact recall。

它没有测量 unrelated artifact preservation。

它没有测量 full Agent propagation。

它没有测量 synthesis feasibility。

它没有测量 runtime function。

它没有测量 performance impact。

它没有测量 ACCORD 的完整 B0 端到端差异。

## 25. PropBench v3 的 checker 修复

早期 materialization checker 没有检查 reuse 字段。

这会让 B0 的 reuse 失步可能漏检。

修复在 `dse_materialization.py` 增加 optional `cross_token_reuse_tokens` binding。

该字段映射到 `GeneratedDesignParams.crossTokenReuseTokens`。

修复保留了旧 fixture 不含该字段时的兼容性。

修复后 P10 reuse=1 mismatch 被捕获。

这是一次真实的 checker blind spot 修复。

修复后 PropBench v3 重新运行。

修复不是硬件性能优化。

修复提高了证据检查的完整性。

修复对应的 focused tests 被执行。

## 26. Paired Timing v1 的尝试

Paired Timing 的初衷是量化 targeted revalidation 相对 full re-run 的时间差。

第一轮使用同一 per-case mutated snapshot。

第一轮每个案例预选一个 targeted gate。

第一轮 full arm 使用多个静态检查和远端 `vlogan`。

v1 E1 documentation 的 targeted/full 时间为 0.134459/6.204545 秒，arithmetic reduction 约为 97.8329%。

v1 E2 config 的 targeted/full 时间为 0.108755/5.884068 秒，arithmetic reduction 约为 98.1517%。

v1 E3 operator RTL 的 targeted/full 时间为 4.809108/5.812796 秒，arithmetic reduction 约为 17.2669%。

v1 E4 top RTL 的 targeted/full 时间为 4.660467/5.302902 秒，arithmetic reduction 约为 12.1148%。

97.7%、98.6%、11.7%、9.3% 是后续 v2 的数值，不能倒填进 v1。

这些数字来自同一案例内的命令墙钟差。

但 targeted gate mapping 是实验脚本手选。

targeted gate 没有从 production evidence contract 派生。

E1/E2 的 targeted checker 没有读取对应的 mutation。

full arm 的 single-layer kernel gate 仍有失败。

full arm 的 AXI/DDR gate 仍有失败。

因此 v1 数字只能叫 selected-gate timing pilot。

它们不能叫 production targeted revalidation speedup。

它们不能支持普适 61x 或 77x 加速。

它们没有被删除。

原始 v1 JSON、日志和同快照目录继续保留。

## 27. Paired Timing v2 的修正

v2 保留同一 mutated snapshot 的 targeted/full 配对结构。

v2 继续采用相同的 selected full gate set。

v2 仍然不是完整 Stage-1 到 Stage-6 replay。

v2 仍然不是 exact-board elaboration。

v2 仍然不是 simulation。

v2 的 E1 targeted wall time 约 0.120553 秒。

v2 的 E1 full wall time 约 5.355425 秒。

v2 的 E1 arithmetic reduction 为 0.9774895。

v2 的 E2 targeted wall time 约 0.072252 秒。

v2 的 E2 full wall time 约 5.336105 秒。

v2 的 E2 arithmetic reduction 为 0.9864599。

v2 的 E3 targeted wall time 约 4.706325 秒。

v2 的 E3 full wall time 约 5.330533 秒。

v2 的 E3 arithmetic reduction 为 0.1171006。

v2 的 E4 targeted wall time 约 4.686369 秒。

v2 的 E4 full wall time 约 5.166513 秒。

v2 仍没有 production resolver evidence。

v2 仍有 selected full gate failures。

v2 仍不能支撑生产策略效率收益。

## 28. Paired Timing v3 的 production resolver

v3 接入 `verification_evidence_contract.resolve_revalidation_gates()`。

v3 从 case adapter 的 tool-consumption records 推导 invalidated evidence。

v3 不在 runner 中嵌入 per-case targeted gate list。

v3 使用同一 source run 生成每个 case 的隔离副本，并使用同一 selected full gate 名称集合。

但是 runner 的 targeted gate 使用 mutated `run_dir`。

runner 的 full static checks 明确调用 `run_check(gate, SOURCE_RUN)`，即传入原始生产 source run，而不是当前 case 的 mutated snapshot。

只有 full `remote_vlogan` 调用使用 `run_dir / "generated/chisel"`。

因此 `same_snapshot_for_both_policies=true` 是 runner 写入的 summary 字段，不能当作完整执行事实。

静态 full gate 与 targeted gate 并非都在同一 mutated snapshot 上执行。

v3 的 full arm 不是完整 Stage-1 到 Stage-6 replay。

v3 的 full arm 也不包含 Stage-7 synthesis。

E1 documentation invalidated evidence 是空。

E1 targeted gate 数是 0。

E1 targeted gate 没有消费 mutation。

E1 selected full all gates pass 是 false。

E1 full wall time 约 4.455736 秒。

E1 arithmetic reduction 是 null。

E2 runtime config invalidated evidence 数是 2。

E2 invalidated gates 包括 deadlock AXI check。

E2 invalidated gates 包括 runtime ABI check。

E2 available targeted gates 最终只有 runtime ABI check。

E2 targeted gate 消费 mutation。

E2 targeted gate返回码是 1。

E2 targeted blocker 是缺少 board wrapper、board-shell interface 和 runtime bitstream。

E2 targeted wall time 约 0.172163 秒。

E2 full wall time 约 4.451723 秒。

E2 arithmetic reduction 约 96.1327%。

E2 selected full all gates pass 是 false。

E3 operator RTL invalidated evidence 是空。

E3 targeted gate 数是 0。

E3 selected full all gates pass 是 false。

E3 full wall time 约 4.473242 秒。

E3 arithmetic reduction 是 null。

E4 top RTL invalidated evidence 数是 1。

E4 targeted gate 是 runtime ABI check。

E4 targeted gate 消费 mutation。

E4 targeted gate返回码是 1。

E4 targeted blocker 同样是缺少 board runtime prerequisites。

E4 targeted wall time 约 0.170849 秒。

E4 full wall time 约 4.437908 秒。

E4 arithmetic reduction 约 96.1502%。

E4 selected full all gates pass 是 false。

v3 metrics 是 case_count=4。

v3 metrics 是 selected_full_all_pass=0。

v3 metrics 是 targeted_resolver_nonempty=2。

v3 metrics 是 targeted_consumed_mutation=2。

因此 v3 只能支持 resolver 已被生产路径调用并且在适用案例执行了声明的 runtime ABI checker。

v3 不能支持生产 revalidation efficiency claim。

此外，`derive_invalidated_evidence()` 不是完整的 production hash invalidation engine。

它遍历 `case_adapter.json` 中工具的 `consumes` 字段。

它用 mutation basename 或最后两个路径片段做 suffix match。

它没有逐个比较生产 artifact 的完整 content hash、source identity 和 tool input fingerprint。

resolver 本身是 production function，但 runner 输入给它的是这种 basename/suffix 派生的 invalidation 集合。

`targeted_gate_consumes_mutation` 还包含“任一 targeted status 为 pass”这一宽松兜底条件。

这意味着该布尔字段不能单独当作严格的 mutation-consumption proof。

E1、E3 的 comment-only mutation 没有触发 production invalidation。

E2 只修改 runtime config 的 `design_id` 字段。

E4 对 `GeneratedAxiDdrTop.sv` 追加 comment。

这些变异不是改变 RTL 计算语义的硬件故障。

所以 v3 的 96.13% 和 96.15% 只能描述当前 runner 的命令墙钟差和 resolver 选择行为，不能写成经过完整证据失效、同快照全绿和生产重验证证明的效率收益。

## 29. 2A 早期静态 probe

在第一轮 exact-board syntax pilot 之后，2A 又在 Attention.sv 注入 `this_is_a_compile_fault @;`，开展 generated-source 静态 probe。

注入发生在隔离 generated source package。

原始 source run 没有被修改。

远端 VCS 返回码是 255。

VCS 报告 `Error-[SE] Syntax error`。

错误位置在 Attention.sv 约 4213 行。

failure report 绑定 SACG SHA `e03bc2c76f4a5fe71fe1c52fb170838348fa6d1b5d81234a0ea64edeb7b951ad`。

静态 projection 得到唯一 pipeline node `node.pipeline.stage_01_self_attention`。

该 probe 的候选和预注册目标一致。

该 probe 没有执行 repair。

该 probe 没有执行 post-repair compile。

因此 repair scope violation 是 not applicable。

第二个 probe 在 Activation.sv 注入受控 source fault。

Activation probe 候选包括 `node.pipeline.stage_05_activation`。

Activation probe 还包括 `node.model_op.05_activation`。

这说明 pipeline node 和 model-op node 的命名/映射存在歧义。

Activation probe 没有执行 repair。

Activation probe 没有执行 post-repair compile。

因此两个早期 probe 不能形成修复成功率。

它们支持的是静态 source-to-node projection 的有限观察。

## 30. 2B evidence replay 和 gate timing

2B 重新使用 Small E1-E4 fixture。

2B 也重新使用 Medium E1-E4 fixture。

Small 组是 4/4 expected outcomes。

Medium 组是 4/4 expected outcomes。

两组都不是 Agent run。

两组都不是 VCS run。

两组都不是 Vivado run。

另有一次真实 promotion certificate copy replay。

未修改的隔离 report copy 被 production checker 接受。

对 copy 追加一个空白字节。

checker 检测到 live-evidence hash drift。

checker 拒绝变异后的 copy。

原始 run report 没有被修改。

这个 replay 不是自然 stale acceptance rate。

这个 replay 不是 false invalidation rate。

Stage-3 multilayer pipeline check 一次 wall time 是 0.101 秒。

Stage-6 exact-board VCS compile/elaboration 一次 wall time 是 62.696 秒。

Attention patch 后另一次 exact-board VCS wall time 是 78.775 秒。

Stage-7 generated-kernel OOC synthesis 一次 wall time 是 4786.196 秒。

该 synthesis 不是 place-and-route。

把不同 source revision 的时间相加得到 4848.993 秒只是算术场景。

该算术场景不构成 targeted/full 配对。

因此 98.707% 和 99.998% 只能作为假设性时间量级说明。

它们不能写成实测生产提速。

## 31. 代码实现变更与对应实验影响

`verification_evidence_contract.py` 增加 production gate resolver。

resolver 只读取 evidence invalidation 和 declared dependencies。

resolver 不创建 case-specific gate。

resolver 不修改文件。

resolver 不赋予 repair authorization。

`sacg_cctg_causal_slice.py` 增加 generated-source materialization candidate projection。

projection 读取 recorded pipeline facts。

projection 对 wrapper 和 shared resource 使用保守候选集合。

projection 保持 `authorized_repair_scope` 为空。

`dse_materialization.py` 增加 cross-token reuse binding check。

新增 check 对旧 fixture 保持 optional compatibility。

`run_paired_timing_v3.py` 改为 hard-linked complete run snapshot。

v3 runner 调用真实 runtime ABI checker。

v3 runner 对合法 JSON runtime mutation 执行检查。

v3 runner 在 targeted gate 为空时把 reduction 设置为 null。

`case_vcs_evidence_analyzer.py` 增加 SACG snapshot path 和 SHA 绑定。

analyzer 使用 exact-board manifest source rows 和 VCS log 关联 source ID。

没有唯一 source path 时 analyzer 不猜测。

相关测试覆盖 analyzer 到 static projection 的集成。

代码变更改善了实验可追溯性。

代码变更没有制造新的硬件 QoR。

代码变更没有证明 runtime CCTG。

## 32. 框架自身暴露的工程问题

早期 repair loop 可能因 endpoint/credential 环境继承而混用错误上游 API。

该问题会把 API 503 误认为硬件实验失败。

后续 runner 强制使用 agent-only environment file。

后续 runner 清空父 shell 的 route 和 key 变量。

相同 no-progress evidence 可能重复触发新的 repair planning。

重复 planning 会造成 iteration 增长而没有新工具证据。

后续策略要求新 planning 必须有新 evidence、new patch、new capability 或 new observation。

Stage-4 schedule blocker 也曾被误解成 VCS failure。

报告后来明确区分 eligibility rejection 和 compile failure。

一些旧 runner 将 ground truth 写入 diagnostic input。

这会造成标签泄露。

TraceBench v4/v5 改为 scoring-only sidecar。

早期 checker 没有验证 reuse binding。

PropBench v3 增加该字段检查。

stage_llm 的 Verilog module interface compaction 对参数化 ANSI header 识别不完整。

该问题会使 repair prompt 生成异常。

后续增加嵌套括号和字符串处理。

exact-board compaction 曾按错误 cwd 解析相对路径。

后续改为 repository-root 解析。

patch executor 曾在 ready_to_apply 和 blocked_reasons 同时出现时进入写入路径。

后续 patch normalization 要求带 blocker 的 patch 原子拒绝。

这些是框架稳定性问题，不是硬件设计失败。

它们必须修框架而不能让流程回退到更早的设计阶段。

## 33. 机制实验中明确排除的误判

T1-T6 return code 2 不是 VCS compile error。

`cyclic_stream_wait` 不是 RTL deadlock proof。

T7 B0 compile repair 不是 graph-guided CCTG localization。

VCS compile pass 不是 numerical simulation pass。

VCS compile pass 不是 DDR weight consumption。

VCS compile pass 不是 cycle count measurement。

VCS compile pass 不是 board bring-up。

旧 Claude timing report 不能绑定到新的 source closure。

不同 run 的 Vivado timing 不能拼成配对 QoR。

不同源码 fingerprint 的 gate time 不能拼成实测 speedup。

PropBench v3 10/10 不是 full propagation recall。

TraceBench v5 10/10 revalidation 不是 Agent patch success。

TraceBench v5 2/10 upstream Top-1 也不是 runtime CCTG success rate。

Small 和 Medium fixtures 不能合并成 8/8 EDA run。

seq16 和 seq32 不能无条件合并为同一 cohort。

P6 lanes=8 同时改变三个字段，不能称单字段样本。

T7 reuse=1 不在原始 preregistered domain。

Gemma 模型的 compile repair 不能改称 GPT-2 Medium CCTG result。

算术 reduction 不能在 full suite fail 时写成 production efficiency。

## 34. 当前可以支持的机制结论

可以说真实 Medium seq32 run 持久化了 Stage-0 到 Stage-3 的 SACG 演进。

可以说该 run 的图边从 7、7 增长到 18。

可以说最终图包含 7 条模型顺序边和 11 条 stream 边。

可以说 Stage-3 pipeline checker 在该 run 上 11/11 通过。

可以说 T1-T6 的 12 个候选都完成了 Stage-4 candidate materialization。

可以说 T1-T6 的下游阶段都因同一个 static schedule-risk blocker 未测。

可以说 T7 是 reuse=1 域外的 compile-only parameter/adapter case。

可以说 PropBench v2 的 2/2 stale parameter mismatch 在 source-only VCS 仍通过时被发现。

可以说 PropBench v3 的 10/10 ACCORD materialization checks 通过。

可以说 PropBench v3 的 10/10 B0 stale binding mismatch 被发现。

可以说 PropBench v3 的 10/10 source-only VCS compile 分别返回 0。

可以说 TraceBench v5 产生了 10/10 真实 source compile failures。

可以说 TraceBench v5 恢复 pristine source 后同 gate 10/10 返回 0。

可以说 TraceBench v5 的静态 downstream scope hit 是 6/10。

可以说 TraceBench v5 的 upstream anchor Top-1 是 2/10。

可以说 TraceBench v5 没有调用 production repair authorization。

可以说 v5 明确关闭 runtime causal claim。

可以说 evidence fixtures 在 Small 和 Medium 各自都是 4/4。

可以说真实 report copy 的 hash drift 被拒绝。

可以说 Paired Timing v3 的 resolver 在 2/4 case 非空。

可以说其中 2/4 targeted gate 消费了 mutation。

可以说四个 selected full suites 都没有全绿通过。

## 35. 当前不能支持的机制结论

不能说已经测得参数传播准确率。

不能说已经测得 affected-artifact recall。

不能说已经测得 unrelated-artifact preservation 的全图统计。

不能说已经证明 ACCORD 相对 B0 的 QoR 优势。

不能说已经证明 ACCORD 相对 B0 的性能优势。

不能说已经证明 runtime CCTG graph-guided root-cause localization。

不能说已经证明 two-hop root-cause Top-1 rate。

不能说已经证明 authorized repair scope violation rate 为零。

不能说已经证明 LLM patch repair success rate。

不能说已经证明 targeted revalidation production speedup。

不能说已经证明完整 AXI/DDR runtime。

不能说已经证明真实 DDR 输入、权重和输出计数非零。

不能说已经证明周期精确 DSE。

不能说已经证明 runtime deadlock 被排除。

不能说已经证明完整模型数值正确。

不能说已经证明上板成功。

不能说把 compile-only policy 换一个术语就能扩大证据范围。

不能把实验计划中的目标比率写成 observation。

## 36. 论文结果表的安全写法

1A 可以作为真实 forward graph construction case。

1A 表格应列 7、7、18 edge counts。

1A 表格应列 11/11 Stage-3 checks。

1A 脚注应说明没有 matched baseline。

1B T1-T6 可以作为 Stage-4 materialization pilot。

1B 表格应列 12/12 materialization pass。

1B 表格应列 12/12 schedule-blocked before Stage-5。

1B 表格应把 downstream score 写为 not measured。

T7 应单独标成 domain extension。

T7 应注明 compile-only。

T7 应注明 simulation skipped。

T7 应注明没有 CCTG slice。

PropBench v3 可以作为 cross-stage binding consistency benchmark。

PropBench v3 应明确 B0 是 frozen Stage-5 artifact control。

PropBench v3 应明确 source-only VCS pass 不代表 exact-board pass。

TraceBench v5 可以作为 static generated-source projection benchmark。

TraceBench v5 应同时呈现 6/10 downstream scope 和 2/10 upstream Top-1。

TraceBench v5 应明确 repair authorization=0。

TraceBench v5 应明确 same-gate restoration 不等于 patch repair。

2B 应把 fixture 和 real replay 分开展示。

2B 应将 timing 作为 command-level observations。

2B 不应显示一个未经配对验证的 speedup headline。

任何硬件 QoR 表都不能把机制 pilot 的 compile-only 结果当成 timing QoR。

## 37. 后续实验优先级

第一优先级是补齐 T1-T6 的明确 policy 和同一候选 ACCORD/B0 下游比较。

如果保留 cyclic_stream_wait 阻断，必须把结果标为 schedule-risk prevention。

如果建立 warning-only 评估分支，必须与生产默认 policy 分开记录。

warning-only 分支不能把 blocked candidate 写成 runtime feasible。

第二优先级是补全所有 generated source 到 pipeline node 的 materialization facts。

补全应从实际 Stage-5 artifacts 和 source closure 生成。

不能在 fault input 中手工泄露目标 node。

补全后再运行 TraceBench 的不同故障类型。

第三优先级是让 repair authorization gate 真正接入 TraceBench。

每个案例需要 proposal、authorized scope、patch path 和 same-gate revalidation。

source restoration 只能作为 revalidation control。

第四优先级是建立同一 source/input/tool snapshot 的 targeted/full paired timing。

full suite 必须先在未变异 snapshot 上定义并记录。

如果 full suite 本身不全绿，不能计算 production efficiency。

targeted gate 必须消费对应 mutation。

第五优先级是构造 runtime-enabled board simulation。

runtime CCTG 需要 progress event。

runtime CCTG 需要 executed manifest。

runtime CCTG 需要真实 input/weight/output event。

没有这些证据时继续使用 static projection 术语。

第六优先级是控制实验重复过程中的内存和进程数量。

本地 WSL 只保留少量 runner。

远端 VCS/Vivado 可使用更多资源。

每次启动新任务前检查旧进程和输出目录。

每次得到新结果立即追加 context checkpoint。

## 38. 证据保存和可恢复性要求

每个实验目录必须保存 task spec。

每个实验目录必须保存 source snapshot 或 archive。

每个实验目录必须保存 input fingerprint。

每个实验目录必须保存 SACG snapshot hash。

每个实验目录必须保存参数绑定报告。

每个实验目录必须保存工具原始日志。

每个实验目录必须保存 return code。

每个实验目录必须保存报告 hash。

每个 experiment summary 必须注明 policy。

每个 experiment summary 必须注明 gate scope。

每个 experiment summary 必须注明 simulation 是否执行。

每个 repair episode 必须同时保留 failure source 和 repaired source。

每个 repair episode 必须保存 patch action。

每个 repair episode 必须保存 repair authorization 状态。

每个 repair episode 必须保存同门限 revalidation log。

每个 evidence replay 必须写清原始 run 是否被修改。

每个 stale report 变异必须只发生在隔离副本。

每次 source hash 变化必须创建新 archive identity。

旧报告不能覆盖新报告。

历史最佳 QoR 不能被较差候选覆盖。

作废的 runner 结果要保留并明确作废原因。

重复的相同 no-progress loop 不应被计为新实验。

## 39. 结果核对方法与历史记录冲突

本文同时核对历史上下文、实验计划、逐轮状态说明、机器汇总以及实际 runner 源码。

状态说明中的“已完成”首先表示指定命令已经退出，不自动表示其所有 gate 通过。

机器汇总中的 `status=pass` 只按其具体 gate 的语义解释，不跨层扩展。

当文字摘要与当前 JSON 的耗时不一致时，本文保留摘要当时数字，同时用当前 JSON 给出可重算的精确数值。

当 JSON 声明的 `same_snapshot` 与 runner 实际传参不一致时，正文另行说明实现差异。

当 fixture、probe、snapshot replay 和正式 Agent 运行共享同一个任务名字时，分别保留实验类别。

这种核对方式保证读者能在本文内判断每个数字测量了什么，而不用先了解仓库目录布局。

## 40. 结论和评估起点

当前机制实现不是空壳。

SACG 的跨阶段状态在真实 Medium run 中被建立和持久化。

Stage-3 pipeline checker 在该 run 上完成 11/11 pass。

参数 materialization checker 能区分 candidate 与 generated source。

PropBench v3 证明冻结 Stage-5 package 会被 stale binding checker 发现。

source-only VCS pass 与跨阶段一致性 pass 的差异是实际观察到的。

静态 failure projection 已经能读取 source、artifact 和 graph facts。

TraceBench v5 也清楚显示当前 mapping coverage 还不足。

TraceBench v5 的 2/10 upstream Top-1 是需要修复的真实工程信号。

evidence contract fixture 的 4/4 结果说明失效分类的确定性逻辑可运行。

production resolver 的 2/4 nonempty 说明其接入路径已工作但 case metadata 仍不完整。

Paired Timing v3 的 full suite 0/4 显示效率实验尚未闭环。

这些结果同时说明机制设计方向和实现缺口。

真正需要补齐的不是重新包装旧数字。

需要补齐的是 source-to-node coverage、repair authorization、同快照 full green gate 和 runtime evidence。

如果论文只需要有限的 compile-time mechanism demonstration，现有数据可以形成诚实的 pilot 表。

如果论文要声称统计意义上的传播准确率、CCTG 成功率或生产重验证加速，现有数据还不足。

所有后续规划都应该以这条边界为起点。

本文记录的最终状态是截至 2026-11-01 的已观测状态。

后续新运行必须在本文末尾追加时间戳、source fingerprint、policy、结果和边界。

不能直接覆盖本报告中的历史数字。

## 41. Medium seq16 迁移配对的完整状态

在 GPT-2 Medium seq32 主 run 之前，Medium campaign 曾先建立 seq16 的机制配对准备目录。

该 campaign 采用同一 Medium 模型配置和同一 W4A8/I32/VU9P envelope。

E2-lanes-explicit 的目标是显式把 lanes 从 16 改到 8。

E2-lanes-explicit 的合法候选同时把 compute array 调整为 8x8。

ACCORD Stage-4 return code 是 0。

ACCORD Stage-4 wall time 约为 75.947 秒。

ACCORD Stage-5 return code 是 0。

ACCORD Stage-5 wall time 约为 323.889 秒。

B0 Stage-4 return code 是 0。

B0 Stage-4 wall time 约为 44.354 秒。

B0 Stage-5 return code 是 0。

B0 Stage-5 wall time 约为 419.612 秒。

两侧都得到 stage4_stage5_complete。

该案例没有完整 Stage-6 board gate。

该案例没有 Vivado QoR。

该案例没有性能差异结论。

E2-lanes-inferred 的目标同样是 lanes 16 到 8。

E2-lanes-inferred 不在任务正文中固定所有阵列维度。

ACCORD Stage-4 return code 是 0。

ACCORD Stage-4 wall time 约为 81.805 秒。

ACCORD Stage-5 return code 是 0。

ACCORD Stage-5 wall time 约为 1279.593 秒。

B0 Stage-4 return code 是 0。

B0 Stage-4 wall time 约为 49.748 秒。

B0 Stage-5 return code 是 0。

B0 Stage-5 wall time 约为 1151.412 秒。

两侧都得到 stage4_stage5_complete。

该案例同样没有完整 Stage-6 board gate。

该案例同样没有 QoR 或性能数据。

E2-cross-token-reuse 的目标是 reuse 由 8 改到 4。

ACCORD Stage-4 return code 是 0。

ACCORD Stage-4 wall time 约为 35.092 秒。

ACCORD Stage-5 return code 是 0。

ACCORD Stage-5 wall time 约为 636.739 秒。

B0 Stage-4 return code 是 0。

B0 Stage-4 wall time 约为 85.876 秒。

B0 Stage-5 return code 是 0。

B0 Stage-5 wall time 约为 770.776 秒。

该案例的 lower-stage paired compile evidence 可保留。

该案例没有形成可归因的 DCG performance gain。

E2-activation-banks 的 Medium 目标是检查当前 Medium candidate 中 activation bank 绑定。

该目录不是 Small activation-banks revision 的目录。

ACCORD 和 B0 都得到 candidate `arch_fe61cdad7cf2`。

该 candidate 的 lanes 是 16。

compute array 是 16x32。

FIFO depth 是 128。

activation banks 是 2。

cross-token reuse 是 8。

cache tile 是 256 words x 2 tiles。

refill width 是 512 bit。

compute backend 是 integer DSP。

ACCORD 和 B0 的 parameter binding report 都记录该同一 candidate fingerprint。

ACCORD 的 six-command Stage-5 compile gate 返回 0。

B0 的 six-command Stage-5 compile gate 返回 0。

ACCORD 的 compile gate duration 约为 176.1313 秒。

B0 的 compile gate duration 约为 184.4067 秒。

ACCORD 和 B0 都没有 measured DSE QoR。

两侧的 source-level design selection 没有形成分歧。

该 Medium activation-banks 记录只说明 lower-stage parameter binding、Chisel compile 和 top-level elaboration gate 可执行。

它没有形成 Small 版本的 `activation_banks: 4 -> 2` 因果差异。

它没有提供独立 Vivado timing、resource 或 throughput 结果。

Small 版本的 `arch_e10408d1ed8e`、61.8/104.5 秒 Stage-4 时间以及 128.8401/104.2175 秒 Stage-5 时间不能复制到此 Medium subsection。

E2-cache-tile 在 Medium candidate domain 中没有合法 alternative。

该状态是 no_legal_alternative_in_medium_candidate_domain。

它不是 Agent 失败。

它也不是 DCG 传播失败。

它表示该 Medium DSE candidate domain 没有满足任务变化的可用候选。

Medium seq16 runner 的 prepared 状态不能当作完成状态。

prepared 只说明 task card、profile 和起始路径已准备。

stage4_stage5_complete 才表示对应命令已经返回 0。

这些 seq16 记录和 seq32 记录不能直接合并成一个样本分母。

它们的 sequence length、source checkpoint 和 runner policy 不完全相同。

它们可以作为 Medium 迁移的历史背景。

它们不能替代 seq32 的正式机制结果。

## 42. Early evidence-binding failure and recovery details

2026-10-23 的第一轮 evidence-binding fixture 有 4 个 mutation。

第一轮只通过 2 个案例。

第一轮 stale-evidence acceptance 是 0。

第一轮 false-invalidation count 是 2。

第一轮 E1 的 observed stale 范围符合预期。

第一轮 E2 错误地把 functional evidence 也判为 stale。

第一轮 E3 的 observed stale 范围符合预期。

第一轮 E4 错误地让 functional evidence 失效。

该结果暴露了 evidence dependency 分类错误。

后续修正了 mutation 到 evidence provider 的映射。

2026-10-23T16:41 的第二轮重新执行四个 fixture。

第二轮 4/4 通过。

第二轮 stale-evidence acceptance 是 0。

第二轮 false-invalidation count 是 0。

2026-10-26 compile-policy 目录再次保存了同一逻辑的 4/4 pass。

第二轮和第三轮不是两个独立算法版本的统计重复。

它们是同一确定性机制在不同实验 campaign 下的复核记录。

论文中应选定一个 canonical fixture 结果。

另一个结果作为复现或修复历史说明。

不要把 2/4 和 4/4 平均成 3/4。

2/4 是旧版本失败记录。

4/4 是修复后的有效记录。

## 43. 当前机制实验的总数分母

1A 的有效 forward trace 分母是 1 个 run。

1A 没有 matched baseline denominator。

1B 原始 T1-T6 的 Stage-4 job 分母是 12。

1B T1-T6 的 materialization pass numerator 是 12。

1B T1-T6 的 Stage-5 execution numerator 是 0。

1B T1-T6 的 Stage-6 execution numerator 是 0。

T7 是单独的 domain-extension case，不能并入 T1-T6 denominator。

R1-R4 是四个 reuse=1 supplement cases。

R1-R4 的 lower-stage compile evidence 已存在。

R1-R4 的 exact-board VCS denominator 没有完整形成。

PropBench v2 的 case denominator 是 2。

PropBench v2 的 ACCORD materialization pass numerator 是 2。

PropBench v2 的 B0 mismatch detection numerator 是 2。

PropBench v3 的 case denominator 是 10。

PropBench v3 的 ACCORD materialization pass numerator 是 10。

PropBench v3 的 ACCORD source VCS pass numerator 是 10。

PropBench v3 的 B0 mismatch detection numerator 是 10。

PropBench v3 的 B0 source VCS pass numerator 是 10。

TraceBench v4/v5 的 fault denominator 是 10。

TraceBench v4/v5 的 pristine same-gate revalidation numerator 是 10。

TraceBench v5 的 downstream scope hit numerator 是 6。

TraceBench v5 的 upstream anchor Top-1 numerator 是 2。

TraceBench v5 的 repair authorization numerator 是 0。

Paired Timing v3 的 case denominator 是 4。

Paired Timing v3 的 resolver nonempty numerator 是 2。

Paired Timing v3 的 mutation-consuming targeted numerator 是 2。

Paired Timing v3 的 selected full all-pass numerator 是 0。

Small evidence fixture 的 case denominator 是 4。

Medium evidence fixture 的 case denominator 是 4。

真实 stale report replay 只有 1 个 controlled copy mutation。

不同分母不能合并成“机制总体准确率”。

## 44. 每个阶段的工具和证据边界

Stage-0 只证明输入归一化成功。

Stage-1 只证明约束抽取和初始图状态形成。

Stage-2 只证明模板/IP 绑定信息形成。

Stage-3 只证明 pipeline graph 和结构检查。

Stage-4 只证明候选物化、合法性和 DSE 选择。

Stage-4 的 return code 2 表示没有 eligible candidate。

Stage-5 compile pass 只证明生成源码和编译期结构。

Stage-6 leaf pass 只证明对应层级的 compile-only gate。

Stage-6 exact-board pass 只在 board wrapper 和 manifest 真实可用时成立。

Stage-6 `functional` 文件名不能替代 simulation execution flag。

Stage-7 OOC synthesis 只证明 generated kernel scope 的综合和报告。

Stage-7 OOC synthesis 不等于 full app-shell implementation。

Stage-7 timing estimate 不等于 post-route timing。

Stage-7 DSE cycles 不等于 RTL cycle counter。

Stage-7 derived token/s 是估算值。

Evidence certificate 只在 source、input 和 tool identity 一致时可复用。

Static SACG projection 只在 hash-bound source 和 graph snapshot 一致时可执行。

Runtime CCTG 需要 compile-only 之外的事件证据。

Repair authorization 需要正式 proposal 和 scope gate。

任何较低层 pass 都不能自动覆盖更高层缺失的证据。
## 45. 第一轮 exact-board 编译故障 pilot 的完整过程

这轮 pilot 早于 Attention/Activation 静态 probe，不能遗漏或合并为同一次实验。
它位于 `method2_2a_2b_20261029/compile_fault_pilot_20261029`。
输入来自 Claude GPT-2 Medium seq32 run 的隔离副本。
实验意图是打通真实板级故障、EDA 日志、诊断分析与 CCTG 的接口。
实验只提交过一次标准 VCS runner invocation。

注入前，`validate_exact_board_identity` 通过。
注入前，复制的 manifest 通过 `validate_exact_board_preflight`。
48 个 compile-source rows 被重新绑定到隔离副本内的文件。
样例工程源闭包内容未改变，其 SHA-256 为 `6665a9df4e0b86fdbd47c48e76b63137069f4c2505d914d6ceee233447a1c5c5`。
唯一的 RTL 改动是向 `generated/board_integration/app_shell_9p_wrapper_tb.sv` 注入一行。
注入内容为 `this_is_a_compile_fault @;`。
该行是 syntax fault，不是端口、参数或 token schedule 失配。
原 production run 没有被改写。

标准调用为 `python scripts/verification/case_board_vcs_functional.py --run-dir <pilot-copy> --timeout-sec 1800`。
policy 显式为 `vcs_compile_only`。
exact-board top 为 `app_shell_9p_wrapper`。
VCS 在远端 23 服务器执行。
input fingerprint 为 `f6988643ff41f708726b78c3a8926ce17d2675c138a52aa8ee45846e2b29bce9`。
工具真实报告 `Error-[SE] Syntax error`。
报错文件是 `app_shell_9p_wrapper_tb.sv`，第 2 行，token 为 `@`。
日志总计 10 warnings、1 error。
compile CPU time 为 1.258 秒。
由于编译失败，没有生成 elaborated simulator executable。
runner summary 中的 missing executable 是这个 syntax error 的后果，不能误归因为缺少 VCS 安装。
compile log 已成功下载并验证 hash。

随后执行 `case_vcs_evidence_analyzer.py`，退出码为 0。
analyzer 写出 `diagnosis_status=ready`。
`failure_class=vcs_compile_failure`。
`first_real_error=Error-[SE] Syntax error`。
`repair_scope=generated_source_or_compile_plan`。
这说明真实工具故障能被 diagnosis path 识别。

同一次分析产生的 CCTG 输出为 `status=insufficient_evidence`。
frontier 为 `runtime_evidence_unavailable`。
runtime event 数为 0。
缺少 `progress_event_log.jsonl`。
也缺少 `board_simulation_executed_manifest.json`。
这与 compile-only policy 一致：仿真未执行，就不会有 runtime progress。
因此可以描述它为“compile diagnosis 成功、runtime causal slice 无输入”。
不能把它写成 CCTG 错误定位了某个 runtime boundary。

本轮没有 LLM repair、source repair、授权补丁或 post-repair VCS。
本轮没有运行 Vivado，也没有更改 shared template 或 framework。
第一轮结果暴露的是实验入口选择不匹配：compile-time fault 被送入需要 runtime evidence 的分析分支。
后续引入 static failure context，是对这个问题的分层处理。
它不需要为了测 compile-time graph projection 而强制开启全模型数值仿真。
但 static context 与 runtime CCTG 的实证结论仍应分开。

| 证据对象 | 本轮实际值或 SHA-256 |
| --- | --- |
| 原 testbench | `3aa1be3360c7362fe0bc53bc0ec7b6ff4b03fa7091ebe55f420dc5139a51ffa6` |
| 注入后的 testbench | `fee076eb15194310195450bc62e89fc2cfd415751c27ebb3b29b29f0a30e3b6e` |
| board identity | `49cbb1f1a72c6b9f829bdb160d0e2d14a337339c9d1d3b46da95937448caa9ba` |
| board manifest | `adf4933d7054337897675a7df779bbb6ffa8df3fbc8ae17468a2ecae3f390a9a` |
| VCS compile log | `e23e4a8c64aaf1ae370387305e4da8dd7ee3cc71dd57a765d8972d60596d758a` |
| VCS runner report | `55d015264e6dc376f5076939eae91ff6e0f02d3b6501fb36f31a0d89231f5b4b` |
| compile diagnosis | `f0c55275795d09d0a4008df6fee0be34ad10291fc6d5836f871715a09990cb77` |
| CCTG result | `c606ce084561f3485170a9dc5e9fe9bd5786705b0eeeb80028d382c496654b6b` |

## 46. TraceBench v5 的源码执行路径和评分问题

v5 的名称与计划中的“下游表象—上游根因”相似，但实际 fault construction 仍有差距。
`make_bundle()` 从 R2 的 generated SV tree 构造隔离 source package。
它找到选定 module 的最后一个 `endmodule`。
它在该位置前插入 `assign tracebench_contract_fault = ;`。
它没有修改 upstream producer 的位宽。
它没有修改 GeneratedDesignParams。
它没有修改图中的 upstream contract。
因此本轮没有真正创造“上游错误引起下游报错”的硬件条件。

failure report 只包含 downstream source、fault source SHA、VCS log SHA、failure symbols 和 SACG SHA。
upstream anchor 留在 scoring-only sidecar，不传入 projector。
这修复了 v3 的标签泄露。
但是“不泄露答案”本身并不能保证 scoring label 就是本次 fault 的真实因果根。
v5 的 upstream anchor 是预先希望回溯到的节点，并非通过上游变异与工具反应建立的 root cause。

静态函数先将 source 路径绑定到 graph artifact。
若 source 属于 generated package，会读取节点 facts 中的 source/template/op/kind/stage_id。
module stem 与这些事实形成 alias matching。
wrapper 被归为 integration boundary，保留 block input/output 候选。
physical FIFO 和 weight cache 被归为 shared physical resource，可落在多个 pipeline stage。
它沿图入边收集 upstream context，但 primary root candidate 的选择另有排序规则。

排序函数 `_static_node_specificity()` 先排 pipeline，再排 stream、design-space、model-op。
同类节点按 node id 字典序打破平局。
`upstream_dependency_context` 是 BFS 得到的背景集合。
`primary_root_cause_candidate` 是 root candidates 经上述 specificity 排序的第一个。
BFS 收集背景与因果证据排序不是同一件事。
当前代码不能保证最先排序的节点就是 upstream root。

| v5 case | primary candidate | 候选数 | downstream scope hit | upstream anchor hit |
| --- | --- | ---: | --- | --- |
| F1 AXI wrapper | block_input | 2 | true | false |
| F2 compute top | block_input | 2 | true | false |
| F3 Attention | stage_01_self_attention | 1 | true | false |
| F4 IntegerAttention | 空 | 0 | false | false |
| F5 Linear | 空 | 0 | false | false |
| F6 Activation | stage_05_activation | 2 | true | false |
| F7 ResidualAdd | 空 | 0 | false | false |
| F8 PhysicalStreamFifo | stage_00_layer_norm_1 | 8 | true | true |
| F9 WeightTileCache | stage_00_layer_norm_1 | 8 | true | true |
| F10 QKVProjection | 空 | 0 | false | false |

F1 的 scoring anchor 是 stage_07_residual_add_2。
F2 的 scoring anchor 是 stage_06_mlp_proj。
F3 的 scoring anchor 是 stage_00_layer_norm_1。
F6 的 scoring anchor 是 stage_04_mlp_fc。
F8/F9 的 anchor 都是 stage_00_layer_norm_1。
F8/F9 的八个候选都来自 shared resource 的保守映射。
stage_00 由于字典序排在前面，恰好与其 anchor 相同。
所以 raw 2/10 应保留，但不能解释成两次已经证实的 upstream causal diagnosis。

十个 fault compile 均返回 255。
十个 pristine source recompile 均返回 0。
恢复过程从原始 SOURCE_RUN 重新复制 source，属于 restoration control。
没有 Agent 从工具报告自主生成 repair proposal。
没有 production authorization gate。
没有 authorized patch scope。
因此 scope violation rate 没有适用分母。
它不是 0%，而是没有测量。
同门重编译通过率可以写 10/10，但应同时注明“恢复原始 source”。

本轮有价值的已观测能力是静态 generated-source 映射覆盖。
下游 scope 6/10 表示部分 source 已可落到 graph candidates。
四个空映射说明 IntegerAttention、Linear、Residual 和 QKV 的 ownership facts 仍不足。
宽 shared-resource scope 说明 artifact ownership 的粒度过粗。
后续应补的是生产生成路径的精确 materialization facts，而非评分脚本中的人工 module-to-answer 表。

## 47. PropBench v3 的十组实际参数和控制臂细节

以下表格直接按最新 `candidate_parameters` 展开，而不是只按 case 名称推断。
所有行的 reuse 都固定为 1。
这使它们避开当前静态 chunk wait 风险域，但没有形成 runtime 可运行证明。
四行参数取自历史 R1/R2/R3/R4，六行取自 R2 再进行 isolated binding rewrite。
所有行的 SV 实际统一从固定 R2 source tree 取用。

| case | lanes | rows | cols | FIFO | banks | reuse | 参数来源 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| P1 rows8 | 16 | 8 | 32 | 64 | 2 | 1 | R1 |
| P2 rows4 | 16 | 4 | 16 | 64 | 2 | 1 | R2 + rewrite |
| P3 cols16 | 16 | 16 | 16 | 64 | 2 | 1 | R2 |
| P4 cols8 | 16 | 16 | 8 | 64 | 2 | 1 | R2 + rewrite |
| P5 cols4 | 16 | 16 | 4 | 64 | 2 | 1 | R2 + rewrite |
| P6 lanes8 | 8 | 8 | 8 | 64 | 2 | 1 | R2 + coupled rewrite |
| P7 FIFO32 | 16 | 16 | 16 | 32 | 2 | 1 | R2 + rewrite |
| P8 FIFO128 | 16 | 16 | 32 | 128 | 2 | 1 | R3 |
| P9 banks4 | 16 | 16 | 32 | 64 | 4 | 1 | R4 |
| P10 reuse1 | 16 | 16 | 16 | 64 | 2 | 1 | R2 + rewrite |

P2、P7、P10 的 cols 是 16，不是统一 baseline 描述中的 32。
这不是新的综合结果，而是 source snapshot inheritance 的事实。
P6 除 lanes 外还改变 rows 和 cols，因此是 coupled multi-field case。
不能将十个 case 全部标为单字段 full Agent revision。

runner 的生成函数主要做三个动作。
第一，从 R2 目录 hard-link 45 个 SV。
第二，hard-link 非参数 Scala source。
第三，新写 GeneratedDesignParams.scala，并替换六个 parameter field 和对应 constructor binding。
没有 SBT/Chisel elaboration 命令。
没有重新生成 candidate-specific SV。
没有 candidate-specific board adapter update。

十个 `generated_sv_hashes` 字典完全相同。
将该字典排序序列化后得到的 SHA-256 前缀为 `e50bcf0456d346d1`。
这意味着十个 VCS source analysis jobs 测的是同一套 SV。
不能把它们描述成“十种架构都完成真实 Chisel 生成并编译”。
仍可描述为十组参数绑定的一致性检查与共享 SV 编译复核。

B0 控制的动作也要明确。
它不是重新运行一个无图 Agent。
它读取与 ACCORD 相同的 source package。
它把受控字段改回 `BASELINE_PARAMS` 中的值。
然后把这个 parameter dict 传给 materialization checker。
因此错误是“期望参数与 frozen generated parameter text 不一致”。
对于 P1，checker 期望 rows16，但文本为 rows8。
对于 P3，checker 期望 cols32，但文本为 cols16。
对于 P10，checker 期望 reuse16，但文本为 reuse1。

P6 的内部 baseline dict 把 lanes、rows、cols 全部恢复为 baseline。
但是 summary 的 `stage4_parameter_override` 只记录第一个键 lanes。
checker 实际错误中仍有 rows 和 cols mismatch。
因此复核不能只看这个 summary override 字段。
应同时保留 `stage4_intervention_fields` 和 checker error list。

P1 错误同时覆盖 generated constant 与 accelerator constructor rows binding。
P3 错误同时覆盖 generated constant 与 accelerator constructor cols binding。
P7/P8 的错误是 FIFO depth constant 不匹配。
P9 的错误是 activationBanks constant 不匹配。
P10 修复前可能因 checker 不检查 reuse 而漏检。
增加 optional reuse binding 后，P10 的 mismatch 被发现。

`expected_changed_artifact_classes` 是 runner 固定写入的两个类别。
它们是 selected_architecture.json 与 GeneratedDesignParams.scala。
runner 未从图计算完整 expected affected set。
`unrelated_sv_preserved` 只等于 hash 字典是否非空。
它没有 before/after comparison，也没有 unrelated oracle。
因此当前这两个字段不能导出 artifact recall 或 preservation score。
计划要求的 B0-PartialUpdate 臂没有实现结果。
当前有结果的只是 B0-StaleStage5 binding control。

## 48. Paired Timing v3 的测量路径与报告字段差异

v3 的四个 mutation 都是轻量变异。
E1 在文档文件后追加 comment。
E2 修改 runtime_config.json 的 design_id。
E3 在 Activation RTL 后追加 comment。
E4 在 GeneratedAxiDdrTop RTL 后追加 comment。
这些设置可用于观察声明依赖是否被触发，但不是四个真实硬件行为故障。

case adapter 中每个 tool 的 `consumes` 用于派生 invalidated evidence。
runner 使用 basename 或末两段 path suffix 匹配 mutation。
这一步不等于生产证据合同的完整 hash invalidation。
它没有逐条验证完整 source/input/tool identity 的变化。
resolver 本身确实调用 production `resolve_revalidation_gates()`。
因此 v3 证明的是 resolver 接口的集成，而不是整条 invalidation pipeline 已经完成实验闭环。

| case | invalidated evidence | resolver | targeted 秒 | full 秒 | 算术减少 | full 全通过 |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| E1 documentation | 0 | empty | 0 | 4.455736273 | null | false |
| E2 runtime config | 2 | blocked | 0.172163243 | 4.451723182 | 96.1326606% | false |
| E3 operator RTL | 0 | empty | 0 | 4.473242048 | null | false |
| E4 top RTL | 1 | pass | 0.170848759 | 4.437908187 | 96.1502412% | false |

E2 声明了 case_deadlock_axi_check 和 case_runtime_abi_check。
available set 不包含前者，resolver 将其列为 unavailable。
即使仍执行了 runtime ABI，resolver status 也保持 blocked。
这保留了缺失 gate，不会无声丢弃它。
E4 的 resolver pass 只表示声明的 gate 可供选择。
它不表示所选择的 checker 执行通过。

E2 与 E4 targeted runtime ABI return code 都为 1。
检查失败涉及 board wrapper、board-shell interface 和 runtime bitstream 缺失。
它们不是新的 timing failure。
selected full 中 leaf static、boundary contract、multilayer pipeline 通过。
single-layer kernel 和 AXI/DDR evidence checks 失败。
因此所有 case 的 full all-pass 都为 false。

v3 runner 建立 complete hard-linked case snapshot。
targeted gate 使用 case snapshot。
full remote VCS 也使用 case snapshot 的 generated source。
但是五个 full static gate 的调用为 `run_check(gate, SOURCE_RUN)`。
它们读取的是原 run，而不是 mutation run。
所以 summary 中 `same_snapshot_for_both_policies=true` 与静态调用实参不一致。
这是 runner bug/measurement design gap，不是硬件性能结论。

`targeted_gate_consumes_mutation` 的判断包含路径命中。
它还包含“任意 targeted gate status 为 pass”的 OR 分支。
后一分支不保证 checker 读取过 mutation。
当前 E2/E4 可结合 consumed_paths 说明读过目标路径。
但后续不应单独用这个宽松布尔值计量有效消费。

旧 EXPERIMENT_STATUS 曾写 E2/E4 约 95.70%/96.09%。
当前 summary 的实际值为 96.1326606%/96.1502412%。
两份文字对应不同轮次或未同步摘要，不应无说明地混为同一次测量。
本文保留当前 JSON 的精确时间作为当前数字。
时间仍包含 Python 启动、source 打包、SSH/scp、远端编译及取回日志等 runner 开销。
不能把约四秒墙钟全部称为纯 VCS CPU time。

空 targeted case 的 reduction 改为 null 是正确的报告修复。
它防止“没有执行 gate”被记成 100% speedup。
但要测真实 skipping benefit，需要先证明证据可合法复用、full baseline 可全绿和 correctness outcome 一致。
当前三个条件没有同时成立。
因此本轮保留为 production-resolver integration/timing pilot。

## 49. 早期无效 setup、重试目录与正式实验口径

历史目录多，并不意味着独立完成了同样多次实验。
有些目录记录一次输入准备或继承错误，有些记录相同状态的重试。
下面逐一说明这些尝试做了什么、为何保留、为何不算新增有效样本。

### 49.1 lanes 旧状态污染与 clean pair

`dcg_lanes8_20261023T1926` 包含从旧 run 复制来的 Stage-6/repair-loop 状态。
旧 VCS fingerprint 前缀是 `4a8dc870...`，旧 log hash 前缀是 `24aadf1f...`。
目录中的 252 legal / 0 measured 候选不等于新增 VCS 结果。
它没有产生独立的新编译证据，所以没有作为新的 lanes revision 计分。
后来用只读冻结归档创建 `dcg_lanes8_case_20261023T193854+0800`。
该 clean pair 的任务显式给出 lanes8 与 array8x8。
ACCORD/B0 都有一个合法候选，因而相同选择是预期行为。
两侧六条 SBT compile/elaboration 命令通过。
Stage-5 wall time 分别约 136.781 / 134.382 秒。
这证明 clean paired execution 能完成，不证明图带来更好选型。

`dcg_lanes8_inferred_20261023T2115+0800` 进一步只要求 lanes16→8，不固定阵列几何。
其 lanes8 域中有四种合法阵列。
两侧最终仍选择同一 candidate，fingerprint 前缀 `7ad3a71d15fd`。
35 个 manifest generated files 中 33 个逐文件 hash 相同。
另两项差异涉及 run-local 路径与相应自校验 metadata。
核心参数、accelerator top 与 AXI/DDR top 的 hash 相同。
ACCORD/B0 Stage-5 时间为 161.203 / 156.440 秒。
B0 首次 API TLS EOF 后在相同路由重试成功，不能将该网络耗时解释成设计质量。
该案例是中性 pilot：普通 handoff 在小候选域内也能推导同一结构。

### 49.2 cache tile 的 stale constraint setup

第一轮 `dcg_cache_tile_revision_20261024T0110+0800` 的共享 input 要求 cache_tile_words=512。
复用的 SACG constraint facts 却仍记录旧的 256-word domain。
Stage-4 于是选择了旧 256 candidate。
manifest status 为 `invalid_setup_stale_constraint_snapshot`。
这个失败发生在 setup binding，不能计为 ACCORD 或 B0 的硬件传播失败。
它也不能作为“512-word cache 编译通过”的证据。

`...0110+0800_v2` 重新固定输入与 checkpoint 后，两侧都选择 512。
candidate 为 `arch_2003908986b3`。
两侧各一个 eligible candidate、零个 measured candidate。
两侧 Stage-4 参数检查 6/6，Stage-5 compile/elaboration 6/6。
codegen contract、package static 与 physical binding checks 均 pass。
去除 cache/log/simulation metadata 后，134 个源级文件的两侧 hash 一致。
这是有效 Stage-4/5 pilot，未执行 VCS、Vivado 或 runtime。
原 first attempt 保留为 setup diagnosis，不额外增加样本量。

### 49.3 activation banks 的真实源级变化

Small activation-banks case 为 `...122503+0800`。
请求只改 banks4→2。
固定 lanes8、array8x8、cache512x2、refill512、reuse8。
两侧 candidate 为 `arch_e10408d1ed8e`。
两侧各 121 个 Scala/RTL 文件的最终 hash 一致。
相对 banks4 起点，121 个文件中有 15 个发生变化。
变化集中在 generated params 与 activation memory。
两个 generated top 的内容没有变化。
这是比单纯“6/6 pass”更具体的变化范围观察。
但该 15-file 集合来自源级复核，没有独立全图 must_update oracle。
因此不能直接称为 100% propagation recall。

### 49.4 reuse 输入失配与只写输入的重试

`dcg_cross_token_reuse_revision_20261024T132813+0800` 的 task card 认为 baseline banks=4。
误复用的 design-space input 却只允许 banks=2。
Stage-4 选择 banks2，暴露 `invalid_setup_input_binding_mismatch`。
该尝试在 B0 与 Stage-5 执行前终止。
它没有 paired completion，也没有可比较硬件结果。
`...133600+0800` 是 input-authoring-only retry。
它只记录准备工作，没有新增完整 paired evidence。
有效的新起点是 `...164300+0800_v2`。
v2 固定输入 hash，执行 reuse8→4，其结果另见下一节。

### 49.5 其他目录的实验性质

`cctg_b2_20261023T190653+0800` 是 Gemma B2 早期启动。
`b2_prompt_isolated_replay_20261024T001017+0800` 保存同故障的 prompt-isolation 尝试。
`cctg_b2_prompt_clean_20261024T1105+0800` 保存进一步清理 CCTG 文案后的 replay。
这些目录不能自动算作三个独立故障类别。
`e3_gemma_runtime_prep_20261026` 是 runtime 准备尝试，没有 runtime 完成结果。
`e3_gemma_exact_runtime_20261026` 虽名称含 runtime，实际最终 gate 是 compile-only。
`fig3_materials_20261024` 是材料整理与打包，不是新实验。
Medium inventory 将这些 setup/lineage-only attempts 单独标记。
Small 的结果只能作为历史，不可改名加入 Medium 的分母。

## 50. Small reuse 案例的后端尝试、失败及最终数据

reuse8→4 的固定 revision 最后确实产生过真实后端数据。
这些数据没有被删除，但它们与图机制的因果收益必须区分。
两臂 Stage-4 参数检查均为 6/6，reuse=4。
ACCORD Stage-5 compile duration 为 119.841574 秒。
B0 Stage-5 compile duration 为 115.621 秒左右。
每侧均执行六条 compile/elaboration 命令。
后续 ACCORD 有额外 run-local timing repair；B0 没有对称执行相同优化。
因此后端 QoR 可用于展示 implementation refinement 历史，不能用作公平 DCG ablation。

| 结果阶段 | source archive 标识 | Fmax MHz | 周期或吞吐说明 |
| --- | --- | ---: | --- |
| B0 固定 revision | `b7405a947a50121ab896f1220d20c4c186a31336683aeefe31bbf65ef3cca019` | 17.057278 | 8,702,008 DSE cycles；31.362469 estimated token/s |
| ACCORD 中间结果 | `91c0101b730558e0a04e63545ad384dc08af3ed4125db129b427332c43a542b6` | 84.983 左右 | 后续 source schedule analysis 检出 noncompleting schedule |
| ACCORD 后续候选 | archive 前缀 `318c3a...` | 119.502868 | 11,985,808 estimated cycles；159.525823 estimated token/s |
| ACCORD 最终本案例归档 | `0db1767022fb11079fef37c5fdd96fe29d26cb02de097159a7e79a8a6f7fdff9` | 153.680652 | 9,086,656 source-calibrated DSE cycles；270.604546 estimated token/s |

B0 LUT=239,753，FF=29,777，DSP=1,650。
B0 RAMB36=123，RAMB18=21，URAM=97。
B0 scope 是 generated top，不含完整 board shell。
ACCORD 84.983 MHz 中间结果 LUT=246,508，FF=43,180，DSP=1,666。
该中间结果关键路径从 FFN-up writeToken 到 outputMem BRAM data。
报告有 57 logic levels、11.438 ns data path、-7.767 ns slack。
随后 source-cycle analysis 指出 IntegerAttention output projection 与 Linear chunk4 的闭合等待。
所以该中间 source 不能简单配一个有限 estimated cycles。
这是 source-schedule 分析发现，并非 RTL simulation 已复现的死锁。

一次 QoR router 因继承旧 100 MHz/200 token/s 目标而提出 DSE 回退。
这个建议与固定参数机制实验冲突。
控制器在实际参数变更前停止，未按该建议改阵列或缓存。
这属于实验目标与主流程任务目标未隔离的框架问题。
后续采用单 stage 后端入口与固定 revision scope。

还有一次 patch 已应用但 Chisel elaboration 失败。
这类失败属于真实 implementation attempt，不能从时序优化轨迹中抹掉。
后续在原 run 修复并重验，不需要重建所有上游模型阶段。
一次 Stage-7 恢复还继承了 Toska route，违背当时只用 W8API 的要求。
该错误路由被定向停止，原 run 用 agent-only environment 恢复。
错误 endpoint 的 503 不应归因为 hardware repair 失败。

最终 ACCORD source 的 LUT=229,531，FF=80,672，DSP=1,600。
RAMB36=123，RAMB18=21，URAM=97。
Fmax estimate=153.680651606 MHz。
critical path 是 FFN-up output memory 到 Q memory 写入端。
data path delay=6.165 ns。
timing report 中 constraint period 仍为 4.0 ns，slack=-2.507 ns。
由 4.0-(-2.507)=6.507 ns 得到约 153.68 MHz 的估计。
因此它达到了请求的 150 MHz 估计阈值，但没有闭合该报告中的 250 MHz XDC。
这两种“目标”不能混为一谈。
OOC 模式还提示未设置 HD.CLK_SRC，不能当作完整 clock tree/post-route 结果。

最终周期记录分为 compute schedule 与 DDR 初始填充。
source_schedule_latency_cycles=8,856,360。
initial_ddr_refill_cycles=230,296。
相加 latency_cycles=9,086,656。
processed_tokens=16，model_layers=12。
后续层 overlapping refill stall 在该模型内记为 0。
270.604546 token/s 由该频率和周期估算计算。
RTL cycle counter 没有执行。
DDR 外部等待、真实 miss/refill 和 board latency 没有实测。
所以该数值必须标为 estimated throughput。
它也是 Small seq16 的历史结果，不能用于当前 Medium seq32 主表。

## 51. 原始计划如何演变为当前微基准

最初 `docs/plan.md` 的 Experiment 2 是跨阶段一致性。
Experiment 3 是 dependency-guided failure tracing and repair。
计划中的多个 Forward 与 Revision case 从冻结 checkpoint 启动，并非每次都重跑 Stage0–7。
推荐规模是 Experiment2 主要对照 6 cases×2 configurations×3 repeats=36。
Static DCG 追加 3 cases×1 configuration×3 repeats=9。
Experiment3 为 6×2×3=36。
另有四个 deterministic evidence fixtures。
合计 81 个 Agent evaluation runs 加四个确定性测试。
这个完整 formal cohort 尚未跑完；历史 `formal_score_runs_completed=0` 指的是这一口径。
它不表示 VCS、Chisel、pilot 或微基准“什么都没做”。

原 B0 定义为 handoff-only。
它应获得相同设计事实、源码、工具日志与任务预算，只移除图依赖传播和跨阶段 graph gate。
原 B1 是 static graph：可以看图和检查，但不自动计算 affected closure/通知更新。
原 B2 保留 DCG 与工具，移除 CCTG frontier、root ranking 和依赖限定编辑范围。
baseline 不应因缺一个内部 graph 字段而崩溃，更不能将这种框架崩溃计成方法优势。

后来的 PropBench B0 定义变为 frozen Stage5 artifact control。
它刻意创建 stale binding，用于验证 checker 能否识别。
这是合理的受控负例，但已经不是原计划的自主 handoff-only Agent。
TraceBench 的 raw-log baseline 更窄，只记录报错文件并把 root_node 留空。
它没有执行一个同预算的自主 log-only repair Agent。
因此 raw baseline root=none 不能推导“所有 log-only Agent 的根因命中率为0”。

`new_core_method_eval.md` 将重点转到 compile-time/static/timing。
文档提出 T7 或 warning-only policy 来绕开原 T1-T6 阻塞。
它还提出合并 seq16 revision 和构造八个 repair cases。
这些是计划，不是已观测结果。
实际未启用 T1-T6 的 warning-only feasibility 分支。
默认 `record.feasible` 语义没有被改成“blocked 也可行”。

`core_method_validation.md` 进一步要求 snapshot microbench。
它希望用十个参数变更、十个故障和同快照配对计时取代外围完整板级重跑。
这种范围划分本身可行：测参数绑定不必先跑真实 DDR runtime。
但每个微基准仍需真实执行它宣称的操作。
后来 v3 PropBench 没有重新 Chisel 展开，v5 TraceBench 没有真实 upstream fault，正是与计划不同的地方。

`core_method_validation2.md` 计划补齐三项缺口。
第一，真实 Stage4→5 propagation、artifact hash diff 与 B0-PartialUpdate。
第二，真实跨阶段 2-hop fault、生产 materialization edges 与 repair authorization。
第三，production invalidation/resolver 加 same-snapshot full-green timing。
当前已完成 reuse checker、static candidate projection 和 resolver 的通用代码接入。
当前还没有完成上述三项的全部评估条件。
不能把文档中“10/10”“100% recall”“0% scope violation”等期望值直接填入 observed results。

这也解释为何不同日期的进展文档看起来反复变化。
一部分是合法的实验 scope 从端到端转为快照。
一部分是 baseline intervention 定义变化。
一部分是 runner 修复后发现原指标未测到原机制。
还有一部分是新 summary 没同步旧状态摘要。
下一步应先固定每个 benchmark 的测量对象，再决定需要追加哪些运行。

## 52. 指标的准确分母、当前值与缺失环节

Consistency Pass Rate 的单位是一个完成了预定义适用 checks 的运行。
分母应包含失败、超预算与未完成的任务。
它不能只在成功 candidates 中计算。
目前 T1-T6 没到 Stage5/6，因此没有下游 full consistency rate。
candidate materialization 12/12 pass 是较窄指标，可直接使用但必须标明阶段。

Violation Escape Rate 指系统宣称成功后，独立检查仍发现失配的运行比例。
被 checker 拦住的 stale binding 不是 violation escape。
PropBench 的 B0 mismatch 是拦截成功，不是系统错误晋级后逃逸。
若要测 VER，还需要记录晋级决策与独立验收的成对结果。

Propagation Recall 的常用定义为正确处理的必要依赖/全部必要依赖。
必须先给每个 mutation 定义 `must_update` 和 `must_revalidate` 两个 oracle。
更新文件不等于重新检查文件，两个 recall 不能混算。
Propagation Precision 为正确处理的依赖/实际触及的依赖。
Unrelated Preservation 需对 oracle 外 artifact 做前后内容或语义比较。
当前 PropBench v3 没有这些完整集合，所以不能从“10/10 binding pass”反推 recall=100%。

Root-Cause Top-1 需要独立 root label 与不接触 label 的诊断。
v3 违反后一条件，所以其 10/10 score 作废。
v4/v5 改成 scoring sidecar，修复泄露。
v5 仍没有从 upstream 实际变异确认 root label，所以其 2/10 是 anchor agreement。
不能称为 runtime CCTG localization accuracy。
候选覆盖范围命中、Top-1 命中、工具重新通过是三个不同指标。

Repair Success Rate 需要在统一预算内提交实际修复并过预定义验收。
pristine restoration 可以作为 harness control，不等于 Agent 自主修复。
Scope Violation Rate 需要生产授权门、补丁 touched paths 和明确授权范围。
authorization=0 时，没有合法的“零越界”比例。
Repair Iterations 应分别报告成功样本的轮数与失败样本耗尽预算。
API retry、manifest重绑、编译失败与已提交 source patch 应分别计数。

Targeted speedup=T_full/T_targeted。
Reduction=1-T_targeted/T_full。
前者是倍数，后者是百分比，不能互换。
若 targeted 没运行 gate，reduction 不应自动记100%。
若 full 早期失败，与成功 targeted 的耗时不能简单当作完成同一任务的加速。
若 full static 读取原 run 而 targeted 读取 mutation，比较还存在 snapshot 不一致。
v3 的当前数据只适合列 command wall-clock observation。

硬件吞吐另一个常用计算是 tokens×F_MHz×10^6/cycles。
这要求 tokens、cycles 与频率对应同一 source revision 和 workload。
频率是综合估计时，最终值仍是基于综合和周期模型的估算。
模型从 Small12层换成 Medium24层后不能沿用旧 cycles。
序列从16换成32后也不能只复制旧吞吐。
这些硬件口径与机制 pass rate 没有共同分母。

## 53. 1A 的真实图内容：足以独立理解的前向案例

真实 Pipeline Planning snapshot 有30 nodes、18 edges、23 constraints、18 artifacts。
此外有1个 invariant、1条 evidence 和2条 transitions。
Template Selection snapshot 是20 nodes、7 edges、16 constraints、16 artifacts。
三份保存快照分别是约束提取、模板选择与流水线规划。
其 SHA-256 分别为以下值。

约束提取：`7813110fd560b68dfd2b79cdcfce8d2ba1bafd045db9d503b0fbffeadde752c9`。
模板选择：`ab54f9da9f12899c52a767f4037a30d7f17f40501f155eba5641458996d4d1f6`。
流水线规划：`97d4fc27e1ce18e2182db4bd3492187268f847072cb6cc18b2f8c52554736778`。
这些 hash 绑定的是历史 graph bytes，不是当前任意后续 SACG。

八个算子 stage 构成一个 pre-LN GPT-2 Transformer block。
它们不是将24层全部空间展开为24个独立block。
下面是该图实际记录的11条 stream relation。

| producer | consumer | 支路语义 |
| --- | --- | --- |
| block_input | stage_00_layer_norm_1 | 输入 |
| block_input | stage_02_residual_add_1 | 第一残差 skip |
| stage_00_layer_norm_1 | stage_01_self_attention | main |
| stage_01_self_attention | stage_02_residual_add_1 | main |
| stage_02_residual_add_1 | stage_03_layer_norm_2 | main |
| stage_02_residual_add_1 | stage_07_residual_add_2 | 第二残差 skip |
| stage_03_layer_norm_2 | stage_04_mlp_fc | main |
| stage_04_mlp_fc | stage_05_activation | main |
| stage_05_activation | stage_06_mlp_proj | main |
| stage_06_mlp_proj | stage_07_residual_add_2 | main |
| stage_07_residual_add_2 | block_output | 输出 |

这11条不是简单线性 model order 的复制，因为它们包含两个 residual branches。
每条 stream edge 关联源/目标 port、流顺序、tensor shape、element width 和 backpressure。
典型 hidden edge 的 tensor 是 seq32×1024，8-bit elements，共32768 bytes。
典型 MLP intermediate edge 是 seq32×4096，共131072 bytes。
板侧512-bit AXI 每拍64 bytes，所以分别为512和2048个AXI beats。
Stage3 的 provisional stream width 使用8 lanes×8 bits=64 bits。
因此 stream_beats_per_axi_beat 为8。
它不能被误写成最终 Stage4 选定 lanes16 的 stream contract。

stage_04_mlp_fc 的 graph node type 是 `pipeline_stage`。
template_id 是 `ffn`，source 是 `FFN.scala`。
input shape 是 seq32×1024，output 是seq32×4096。
hidden_size=1024、intermediate_size=4096 已 bound。
weight_bits=4、elem_bits=8、acc_bits=32、integer_mode=true 已 bound。
lanes 的 status 是 `candidate_bound`。
legal_values=[8,16]。
planning_value=8。
value=null。
这表示设计空间已约束，但最终并行度未选定。
把该状态写成“Stage3已确定最终8lane或16lane”都会丢失语义。

该 stage 的 symbolic first-order latency=16,777,216 cycles。
报告明确标为 planning estimate only。
它不能替代后续 source-calibrated cycles。
它也不证明该算子真实执行时延。
图能保存一个估算，不意味着这个估算已被 VCS 或板卡验证。

buffering constraint 为每条支路选择 bounded ready/valid FIFO。
部分 branch FIFO depth64，普通相邻stage示例depth32。
正确性注释指出深度是 elasticity/resource choice，不是为了等化各级 latency。
flow-control split policy 要求源 beat 原子复制到所有 branch FIFO。
各 branch dequeue 独立遵循 downstream ready。
join policy 是所有 required inputs valid 才 fire。
因此“token级重叠”并不要求各stage同时开始结束，也不承诺无气泡。

memory schedule 保存 activation_ping/activation_pong。
板侧参数包括37-bit address、512-bit data、64-bit WSTRB、4-bit ID、64-byte alignment。
物理 channel 数为1。
Stage5 再分配具体 aligned base address。
weight主存、cache与bank切换的目标约束可以在图里表达。
这仍是规划事实，非运行时 DDR 输入/输出计数。
liveness facts 明确写 producer/consumer rates 由后续验证测量，不由 symbolic latency 证明。

template-selection transition 标记 `action_type=template_selection`，生成 template artifact。
pipeline-planning transition 标记 `action_type=pipeline_planning`。
后者关联11条 touched stream edges、多个 pipeline nodes 和 pipeline static evidence。
required checker 是 `pipeline_plan_static_check`。
该 transition promoted 与11/11 static checks对应。
这是一个可追踪的前向状态变化案例，可用于机制图。
它没有匹配baseline，所以不能据此单独估计相对收益。

## 54. 图存储、参数检查、授权和失效之间的真实实现关系

这些机制不是一个函数，也不能由一个 pass 字段互相代替。
`sacg_store.py` 管理设计状态；stage 模块负责产生实际设计产物。
materialization checker 读候选和生成参数；static projector 读图与故障报告。
evidence contract 约束报告可信范围；resolver 把声明失效证据转为 gate 集合。
repair executor 再依据具体动作和授权写文件。
若评估只调用其中一个函数，结果也只覆盖这一段链条。

### 54.1 SACG state 的字段和引用检查

store 初始化 nodes、edges、constraints、invariants、artifacts 和 evidence 集合。
另外保存 failures、repairs、approvals、transitions。
memory 包括 design_goal_trace、stage_outcomes 和 failure_lessons。
还包括 retry_requests、backtrack_requests、contamination_barriers、reconciliation_events。
这让状态可序列化到 JSON，并在会话中断后恢复。
它不是把全部设计事实只放在 LLM 对话窗口。

`validate_references()` 检查每类对象是否有非空、唯一 id。
edge 的 src/dst 必须存在于 nodes。
node 的 constraint/artifact 引用必须存在。
constraint 的 nodes/edges/artifacts 引用必须存在。
invariant 的 latest_evidence 必须存在。
artifact 对 node/edge/constraint 的引用也要存在。
因此“引用闭合”可以确定性检查。
但引用闭合不说明图记录了全部真实硬件依赖。
TraceBench 的空映射就是“图JSON合法，但语义ownership不完整”的例子。

### 54.2 Transition 如何关联设计操作与 checker

`declare_transition()` 要求 touched_constraints 非空。
它验证 touched nodes/edges/constraints 都存在。
transition 保存 action_type、actor、timestamp 和 note。
它记录 repair_scopes 与 scope_class。
它记录 artifacts_changed、artifacts_generated、evidence。
它根据受影响约束所关联的 invariant 找出 required_checkers。
该过程避免只凭“LLM说改完了”就认为设计更新有效。

`promote()` 会拒绝已 rejected 的 transition。
它会拒绝 forbidden repair scope。
需要 approval 的分类必须有 approved record。
required_checkers 必须有 pass evidence。
满足这些条件后，transition 才标记 promoted。
生成 artifact 的 trust_status 改成 validated。
相关旧 contamination barrier 可被 supersede。
这解释1A中为什么 graph、checker和promoted transition能相互关联。

但是 store 不会凭空知道 artifact 内容是否已重新生成。
如果 runner 只改Scala文本、不运行Chisel，promoted或recorded字段不能替代实际生成证据。
当前 PropBench v3 的 `stage4_candidate_recorded=true` 是 runner 填入的布尔值。
它不等于完整 Stage4 agent 被重新调用。
当前 `stage5_snapshot_materialized` 是 source-text checker result。
它不等于 candidate SV 被重新展开。

### 54.3 Materialization checker 的实际强度

`candidate_physical_signature()` 要求 lanes、rows、cols、FIFO、activation banks、weight_banks_by_role。
当 candidate 提供 reuse 时，也把 reuse 纳入 signature。
`validate_generated_params_source()` 在完整 Scala source text 中查找预期声明。
例如 rows8 对应 `val computeArrayRows: Int = 8`。
FIFO128 对应 `val fifoDepth: Int = 128`。
reuse1 对应 `val crossTokenReuseTokens: Int = 1`。
它还检查 FIFO、activation bank 和 weightBanksByRole 的 forwarding markers。
阵列行列允许显式值或 GeneratedDesignParams 引用。

这是有价值的生成参数一致性检查。
它能在仍可编译的源包里识别 expected value 与文本不一致。
但它没有解析完整 Scala AST。
它没有证明所有 constructor 实参最终驱动真实硬件。
它没有对生成 SV/netlist 做物理维度反查。
它对 weightBanksByRole 主要检查声明/forwarding marker，不是完整逐role硬件bank语义证明。
因此“binding checker pass”应与“实际硬件参数一致”分层呈现。
后者需要真实重新展开后的结构证据，不能仅靠 source marker。

### 54.4 静态候选范围与修复权限

static projector 可以输出 candidate_repair_scope。
它始终保留 authorized_repair_scope 为空，等待独立授权。
早期把整个 generated package 写成 authorized scope 的做法已被纠正。
即使候选包包含故障文件，也不说明 Agent 已获准修改整个包。
TraceBench v5 没有提交生产 repair proposal，所以没有授权结果。
因此不能通过把字段名称换成 authorized 来构造零越界比例。
需要实际 proposal、授权决策、touched files 和同gate重验这四类记录。

store 的 scope 分类区分 parameter_sync、signal_connection 等局部动作与 parallelism/memory/numeric 等更大变化。
本报告解释的是框架内部策略实现，不是在当前文档任务上提出额外审批。
用户已经授权的设计目标与运行策略应由任务上下文传入框架。
框架内部元数据错误应修实现，不应自动把硬件流程回退到Stage0或Stage5。

### 54.5 Resolver 的能力和未完成接线

`resolve_revalidation_gates()` 接受 invalidated evidence object 或 list。
它读取 gate、gate_name、provider_gate、targeted_gate。
它也接受 required_gates、depends_on_gates、dependency_closure。
它返回去重 gate 集合及 declared dependencies。
available_gates 不包含的声明 gate 会出现在 unavailable_declared_gates。
无声明时返回 empty；有缺失gate时返回blocked。
函数本身不读文件、不改文件，也不执行 checker。

这使它适合通用 planner 与实验工具复用。
但必须由上游正确产生 invalidated evidence。
Paired Timing v3 的上游目前是 suffix matching，所以不能把整个链写成已验证的content-hash dependency invalidation。
同样，返回 gate 名称也不代表 gate 被成功执行。
当前 E4 resolver pass、runtime ABI fail 正好说明两者不同。

### 54.6 TraceBench source path 与 hash 的另一处绑定缺口

v5 failure report 的 source_file 指向原 SOURCE_RUN 中的 pristine file。
report 的 source_sha256 则来自隔离 fault_sources 中的变异文件。
这是为了沿用原SACG中的artifact路径映射。
但当前 static function 只校验 failure report 的 SACG SHA 与 snapshot SHA。
它没有校验 source_file 当前内容是否等于 source_sha256。
因此“hash-bound SACG”不能扩大为“fault source内容与artifact路径已经严格一致”。

以F3 Attention为例，report source SHA为 `9151b11c1f935bb85d3e469c8fbfe35486a8d4cba7e60b0a763666a27a836fbe`。
隔离 fault source 的实际hash与它相同。
原path的pristine Attention hash为 `534a2943a787d1ab3c42eb3096c905ea9dd7753a16eacbc37d24e7d0ee4feb09`。
两者不同是预期的故障注入结果。
问题是当前报告没有把origin artifact、isolated source和copy mapping严格建模为两个身份。
这不推翻远端VCS真实报错的事实。
它限制的是“exact source-bound projection”这一更强主张。
后续应保留origin mapping并绑定fault copy identity，而不能假称原路径bytes就是fault bytes。

## 55. 网络、内存和重复状态为何影响实验进度

### 55.1 对话API可用不代表Agent使用同一路由

此前用户看到对话正常而Agent连续502/503，存在具体配置层原因。
`SPATIALACC_LLM_*` 进程环境可覆盖配置文件。
某些恢复进程继承Toska base URL，而manifest要求W8API。
因此当时部分503是错误endpoint的结果，不是用户正在使用的对话线路结果。
另一些请求确实在要求的W8API路由遭遇临时channel/model错误。
两类情况要分开，不能笼统写成“余额不足”或“都是Toska”。

后续运行采用agent-only环境文件，并清除父shell的route/fallback覆盖。
启动前读取resolved model/base/wire，启动后核对worker环境。
不改全局CXA配置，不在日志输出secret。
机制对照需要保持相同上游模型，不能为了继续运行而把DeepSeek对照换成GPT。
API请求失败、等待与退避属于execution overhead，不是硬件修复迭代。
没有新patch或新tool result的重试不能算独立repair样本。

### 55.2 WSL OOM的可确认事实和未知部分

2026-10-27本地曾反复全局OOM并导致用户scope退出。
syslog中的Python匿名RSS约20.5–21.0GiB。
其中一次记录匿名RSS=21,986,964KiB。
WSL的init.scope没有可用memory.max硬限制。
因此kernel杀一个大worker后仍可能触发整个会话scope teardown。
这解释了用户观察到“打开WSL过一会又退出”。

API调用并不在本地加载DeepSeek模型权重。
不能把本地大Python进程误称为“DeepSeek模型本身占了21GiB”。
该run有1,927份按事件重复保存的完整SACG JSON，逻辑大小约19.48GB。
最大单份约19.6MB。
事件1938–1941存在相同source SHA的重复快照。
旧恢复代码先逐个打开/校验历史文件，再比较事件source SHA。
这会造成大量重复I/O与状态重建。

但磁盘19.48GB不等于同时驻留19.48GB RSS。
单份19.6MB SACG在受限解析实验中的峰值RSS约66MB。
没有heap/core profile，无法确定失效worker额外RSS的唯一分配点。
报告保留这个不确定性，避免把已发现放大源写成唯一OOM根因。

### 55.3 已实施的通用内存保护

新handoff快照使用原始SACG SHA命名，同状态重试复用。
gzip level1流式复制后原子替换，避免整份read_bytes副本与重复落盘。
旧JSON保持兼容，没有删除历史事件。
恢复先比较事件记录的SHA，仅对匹配候选打开并校验实际快照。
真实run遍历1,941个flow events的只读恢复检查约0.64秒。
峰值RSS约20,200KiB。
19.6MB示例压成353,213bytes，压缩比约55.5倍。

保护最初使用12GiB RSS、3秒TERM宽限。
随后加固为Linux地址空间8GiB与进程组RSS8GiB。
地址空间在worker exec前通过prlimit设置；失败则受控停止。
RSS每100ms采样，超限先TERM，1秒后仍存活则KILL进程组。
锁使多个本地Agent的Stage6 debug worker串行运行。
其他stage及远端EDA不自动套用该限制。
stdout按64KiB块落盘，父进程只保留1MiB tail。
这些改变不删除prompt关键语义，也不改变硬件功能门槛。

历史回归20项先通过，后续加固后的25项通过。
覆盖MemoryError、RSS终止、忽略TERM的后代、stdout有界与跨Agent串行。
这些是框架稳定性结果，不能加入机制实验成功率。
本次编写报告没有再次运行大内存worker或这些tests。

## 56. 已执行的框架验证、未修复测试与记录保存情况

2026-10-31的focused test记录为40项通过。
覆盖verification_evidence_contract与sacg_cctg_causal_slice。
另含两项DSE binding回归：
generated source forwards candidate into FPGA-IP configuration。
generated source rejects dropped FIFO binding。
这40项说明相关确定性逻辑有回归覆盖。
它们不代表40个独立硬件故障repair case。
也不能替代真实VCS或Vivado。

较广的旧 `test_two_legal_candidates_change_emitted_fpga_implementation` 仍有不兼容。
它要求已被integer-DSP方案移除的 `PhysicalFp32Mul` 实例marker。
因此未作为当前机制实验acceptance gate。
这不是“全部测试通过”；报告明确保留该legacy失败。
后续应让测试检查当前整数实现的结构性质，而不是恢复旧浮点实例来满足断言。

TraceBench v4阶段另有12项causal-slice tests通过记录。
它们覆盖static候选排序、授权范围语义等逻辑。
PropBench runner还修过import路径与完整Scala source输入问题。
只读取单个GeneratedDesignParams文件时，forwarding marker可能在其他Scala文件中，造成误报。
后来将整组Scala source合并传给checker后重跑。
这修复的是test harness输入完整性，不是硬件加速器算法。

真实repair episode中还遇到参数化ANSI module header compact失败。
修复使parser处理嵌套括号与字符串，避免prompt构造崩溃。
exact-board相对路径曾按错误cwd解析，改为repository-root解析。
带blocked_reasons的patch曾可能进入ready_to_apply写入分支。
后续normalization让blocked patch原子拒绝。
这些属于framework defects，应原stage修复并继续，不应重启整个设计流程。

2026-10-31曾清理可再生成的本地Verilator obj_dir与Python bytecode。
远端清理结束attempt的VCS work/lib和Vivado .Xil临时数据库。
compile archives、source、logs、exit markers、timing/utilization、best-source archive和bitstream保留。
331份stage.tar.gz和331份VCS compile log仍有记录。
这意味着本报告引用的原始输入/工具结果并未因该次清理被主动删除。
但清理后的已编译数据库不能当作仍在磁盘可直接运行的simulator。
重新执行时可能需要从保留source归档重建。
本次任务没有执行新的清理。

对于未完成或失败attempt，应保留其状态和原因。
保留旧run不等于继续使用旧架构设计新硬件。
immutable历史证据与active设计输入是两种角色。
这是避免旧报告错误绑定新源码、同时防止论文记录丢失的必要区别。
本报告只读提取已有状态，未改变这些角色。

## 57. 面向下一步评估的具体问题清单与最小补齐方案

当前最需要评估的是“实验调用的机制”与“论文希望证明的机制”是否一致。
不需要把每个微基准都扩大为全模型数值仿真。
也不应通过删掉检查结果或重命名字段来获得表面全绿。
下面按实际缺口给出可选择的最小补齐工作；它们是建议，本报告未启动。

| 问题 | 已观察到的影响 | 最小补齐工作 | 完成后可新增的主张 |
| --- | --- | --- | --- |
| v3 PropBench复用同一SV | 十行compile不能说明十种实现 | 每个candidate真实Chisel展开、保留source manifest | candidate-specific generation/compile |
| 缺affected oracle | 没有recall/preservation | 固定must_update/must_revalidate与before/after hashes | 受控artifact同步召回 |
| 缺B0 partial-update | 只有stale文本负例 | 增加局部更新但依赖wrapper未刷新的控制 | 跨模块依赖失配检出 |
| v5是局部syntax fault | 无真实upstream root | 构造producer/consumer契约不一致并确认downstream报错 | compile-time跨阶段回溯 |
| source-node覆盖不全 | 四个v5 case无候选 | Stage5生成时记录精确module ownership/materialization关系 | static mapping coverage |
| shared-resource排序 | F8/F9 Top1偶然命中 | 保留多候选、用独立约束/观测排序，记录置信度 | 更有意义的root ranking |
| 没有production授权 | scope violation无分母 | proposal→授权→patch path检查→同gate复检 | 有界修复过程统计 |
| source路径与hash分离 | fault copy身份不完整 | origin/copy映射与实际bytes identity同时保存 | 严格source-bound projection |
| v3 full静态读原run | targeted/full非完整同快照 | full全部调用mutation snapshot并记录consumed inputs | 合法配对计时 |
| full本身失败 | reduction非同任务完成差值 | 预先定义可通过的适用compile suite并跑基线 | compile期重验耗时收益 |
| invalidation靠suffix | 无完整identity变化验证 | 接入实际evidence/source/input hash变化 | evidence-derived调度 |
| 无runtime events | 不能验证runtime CCTG | 仅若需要该主张，再开runtime-enabled事件捕获 | runtime frontier/causal分析 |

如果只需最短周期补充论文，优先做真实candidate生成与两个真实跨阶段静态失配case。
这不要求更改当前vcs_compile_only主流程。
应把工具判定为warning的width mismatch转成可明确失败的contract check或elaboration约束。
否则“故障已注入但工具仍返回0”无法建立诊断样本。
每个fault先单独确认实际symptom，再让诊断读取去标签的报告。
不要把期望上游节点直接写进failure report。

一个小而完整的repair case比十个pristine restoration更能证明方法。
它应同时展示上游契约、下游symptom、graph path、proposal、授权、source patch和重编译。
如果只用static projection，图示就写static dependency tracing。
如果没有LLM参与修复，图示就不能画Agent autonomously generates patch。
如果没有runtime events，就不画已经运行过的token frontier。

计时也可保持轻量。
固定同一snapshot，先运行适用suite确认基线。
使用同一机器和清楚记录的cache policy配对执行。
保留网络/打包与纯EDA CPU时间的区别。
文档变更可以合法跳过硬件gate，但必须有证据复用规则，而非仅因consumes没列文件。
operator/top变更应触发实际对应检查。
若仍缺board前置条件，可预先将实验范围定义为kernel compile suite；应写清范围，不能称完整板级重验证。

本报告最终保留的进度口径是：真实pilot与微基准已执行多轮，完整原计划尚未闭环。
有数据的结果已在本文逐一展开，包括中性结果、失败、作废与当前有效版本。
所有新发现来自已有源码、JSON、日志和上下文的只读核对。
此次未重启Agent、VCS、Vivado或runtime实验，也未修改原始结果。





