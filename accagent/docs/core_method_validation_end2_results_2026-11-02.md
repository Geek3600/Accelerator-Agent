# Core Method Validation: Consolidated Experimental Record Through Validation5

**记录日期：2026-11-02**
**覆盖范围：机制实验早期探索至 Validation5（含 Small/Gemma 探索、GPT-2 Medium seq32 系列、Validation1/2/3/4/5）**
**目的：作为单一、可独立阅读的实验评估材料，为下一步规划与论文实验叙述提供完整历史证据。**

## 阅读说明与证据规则

本文按时间和实验版本整理项目中已留存的机制验证工作。中后部包含历史完整报告正文，不要求读者再打开其他文档才能理解实验问题、做法和历史结果；Validation5 的本轮数据、逐案台账和异常处理也直接包含在本文前部。

全文区分四种陈述：

- **直接观测**：来自运行日志、模型请求/响应元数据、VCS/Vivado 报告、逐案 JSON 或审计脚本结果。
- **派生统计**：按报告明确的分子、分母和公式从直接观测计算得到。
- **解释**：对观测的有限推断，受样本、门限和实验设置约束。
- **未测/不支持**：当前证据不能得出的结论。计划中的目标值不作为实测值，也不通过调整分母、丢弃失败、修改标签等方式靠近预期。

### 全局工具门限

`vlogan` 通过只表示源码分析通过。`VCS` compile/elaboration 通过表示编译、链接和模块连接展开通过。二者都不等同于 RTL 运行仿真、数值正确、吞吐量实测、综合、布局布线或上板。Vivado 综合 Fmax 是时序估计证据，只有明确的实现报告才能支持对应报告层级的结论。本文中的机制实验大部分是静态分析或 compile/elaboration 微基准。

### 全局保护边界

实验报告里出现的图、artifact hash、授权、checker evidence 和 promotion，必须结合其实际代码路径理解。隔离 benchmark 调用某个 store API，不自动证明生产 Agent executor 已调用该 API。事后恢复旧 source、重放保存的模型响应、对历史日志重评分，与原流程当时自主执行不是同一证据。成功编译不能替代语义正确，源码哈希差异也不等于因果依赖真值。

### 密钥及隐私

本文保留 provider/model/endpoint host 等用于解释实验条件的非凭据元数据；不包含 API key、authorization token、环境变量值、远程 SSH 密码或认证材料。原始凭据不得从历史聊天内容复制到论文或共享实验报告。

### 统一实验基准背景

主机制实验的后期样本集中于 GPT-2 Medium、24 层、序列长度 32、W4A8、VU9P 设计快照。具体 PropBench 基准快照、候选参数、TraceBench source cohort 和 Paired Timing 变异在每节分别标出；即使目标模型相同，也不意味着所有 run 的源码或设计参数相同。历史早期实验还包括 GPT-2 Small、Gemma 或其他独立探索，其结果只在原始章节中按实际范围描述，不能与 Medium seq32 数字混算。

## 当前 Validation5 一页概览

Validation5 按 `core_method_validation_end2.md` 并行执行三项隔离实验：PropBench v6 层次图传播消融、Paired Timing v6 targeted/full 门限比较、TraceBench v8 真实 LLM repair 对照。三项均已结束，原始数据留在 `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation5_20261102/`。

| 实验 | 直接观测 | 主要结果边界 |
|---|---|---|
| PropBench v6 | 10 个历史候选差分；宏平均 recall/preservation 从 0.729/0.899 到 0.817/0.922；micro recall 0.679 到 0.777。 | 文件级 SHA 变化预测有所提高，但没有达到 95–100%；未证明语义或因果依赖完备。 |
| Paired Timing v6 | 6 个案例、两臂；integrity audit 48/48；E5 故障两臂均被 VCS elaboration 检出。 | E4/E6 约节省 55%，低于计划预期；单轮 compile/elaboration 时间，不是任意变更的等价性定理。 |
| TraceBench v8 | 10 个故障 × 两臂；20/20 初始故障复现；两臂 VCS repair pass 均 8/10；promotion B0 5/8、ACCORD 6/8。 | 没有观察到任一臂越权 proposal；不能据此证明 ACCORD 降低越权或提高 VCS 成功率。 |

本轮真实模型条件为 OpenAI `gpt-6.1-sol`、Responses API、endpoint host `www.a8pi.com`。它不同于 TraceBench v7 源 cohort 中保存的 `claude-opus-5` 模型记录，也不是 Claude 对照实验。总请求文件 30 个，两个臂各 15 个、平均 1.5 次/案，单臂单案上限 2 次。所有请求均使用同一 provider/model 配置。

## Validation5 详细执行记录

### 执行分工与隔离

三项实验均使用新目录，根目录为 `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation5_20261102/`。PropBench、Paired Timing 和 TraceBench 彼此分目录，未覆盖 Validation4 原始结果。远端 VCS artifact 使用单独的 Validation5 remote root。旧远端 Vivado/综合进程归属其他工程，没有依据认定其属于本轮任务，因此没有终止。

本机 available memory 检查约 17 GiB；远端 `/home` 使用率约 99%，可用空间约 76 GiB。监控时发现远端有其他工程的 VCS 进程，未触碰。Validation5 自身 TraceBench runner 在本地序列推进，没有额外启动多条重量级 JVM。项目中的 Python 缓存、日志和原始 evidence 仍留在实验目录。

### PropBench v6：数据构造和指标定义

本实验从已存档的 PropBench v5 十个候选读取基准和候选的 SV 文件集合，并以 SHA-256 不同定义 observed changed files。预测器在读取各 case 的 changed-file 标签之前，按冻结参数族先验和独立 baseline RTL 实例化拓扑生成预测集合。解析得到 47 个 RTL 文件、47 个 module definitions、57 种唯一 module-type edges、4152 个语法级实例化位置。模块类型边与句法实例位置并不等价于 elaborated netlist 或参数表达式级数据依赖。

比较三种预测：primary family 有条件召回（只在 gold changed 且属于冻结 primary family 的文件中计算）；primary family 对全部 changed files；现有 flat 1-hop family rule；基于真实 parent instantiation edge 的最多两跳上溯闭包。Preservation 按历史 v5 口径表示预测未受影响文件中真实未改变的比例，属于 predicted-unaffected specificity 类指标。每例指标先按 case 算，再 macro-average；micro recall 单独报告。

Macro 结果：primary conditional recall 1.000，primary all-change recall 0.729、preservation 0.899；flat 重算 0.729/0.899；two-parent-hop closure 0.817/0.922。Micro recall 从 flat 0.679 提升到 two-hop 0.777。提升是观测到的文件级覆盖变化，不能命名为“参数传播准确率”或“因果定位成功率”。

#### PropBench v6 逐例台账

| Case | Primary conditional recall | 全变化 primary recall | Flat recall/preservation | Two-hop recall/preservation | 漏检 |
|---|---:|---:|---:|---:|---|
| banks_4 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 无 |
| banks_8 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 无 |
| cols_16 | 1.000 | 0.533 | 0.533 / 0.806 | 0.667 / 0.844 | GeneratedAxiDdrTop 与 4 个 PhysicalSimpleDualPortMemory 文件 |
| cols_4 | 1.000 | 0.533 | 0.533 / 0.806 | 0.667 / 0.844 | 同 cols_16 的文件模式 |
| cols_8 | 1.000 | 0.533 | 0.533 / 0.806 | 0.667 / 0.844 | 同 cols_16 的文件模式 |
| fifo_128 | 1.000 | 0.857 | 0.857 / 0.955 | 1.000 / 1.000 | 无 |
| fifo_32 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 无 |
| reuse_2 | 1.000 | 0.500 | 0.500 / 0.842 | 0.500 / 0.818 | 六个 PhysicalSimpleDualPortMemory 实例文件；两跳未改善召回 |
| rows_4 | 1.000 | 0.667 | 0.667 / 0.889 | 0.833 / 0.938 | GeneratedAxiDdrTop.sv、PhysicalSimpleDualPortMemory_6.sv |
| rows_8 | 1.000 | 0.667 | 0.667 / 0.889 | 0.833 / 0.938 | GeneratedAxiDdrTop.sv、PhysicalSimpleDualPortMemory_6.sv |

cols 组的未命中名单为 `GeneratedAxiDdrTop.sv`、`PhysicalSimpleDualPortMemory_14.sv`、`PhysicalSimpleDualPortMemory_28.sv`、`PhysicalSimpleDualPortMemory_4.sv`、`PhysicalSimpleDualPortMemory_6.sv`。rows 组未命中顶层与一个 memory instance。reuse_2 未命中 `PhysicalSimpleDualPortMemory_13.sv`、`_14.sv`、`_25.sv`、`_28.sv`、`_4.sv`、`_5.sv`。这些失败说明语法模块实例化父边不能表示所有总线宽度耦合或参数到存储展开的关联。实验没有根据 misses 追加边，避免用 gold 标签调 predictor。

本实验没有执行 SBT/Chisel、VCS、综合或仿真；这是纯静态离线消融。拓扑 parser 在文件级语法上运行，未针对每个候选重新 elaborate 参数化层次。

### Paired Timing v6：门限、计时和故障修复

每个 case/arm 在独立目录运行。每个 arm 先 `vlogan` 建立 work library，后续 VCS elaboration 使用同一目录和 work library，不重复执行 `vlogan`。Full arm 采用实验登记的完整编译期 gates；targeted arm 执行与该变更关联的局部检查。计时为单次 wall clock，包含各 gate runner 已记录的相应本地/远端工作，但不表示完整 Agent flow latency。

| Case | Targeted 秒 | Full 秒 | Saved | 结果 |
|---|---:|---:|---:|---|
| E1 documentation | 0.024888 | 29.652226 | 99.9161% | PASS/PASS |
| E2 pipeline metadata | 0.027563 | 29.546097 | 99.9067% | PASS/PASS |
| E3 parameter-binding source | 0.024277 | 29.438978 | 99.9175% | PASS/PASS |
| E4 RTL comment | 13.179352 | 29.269763 | 54.9728% | PASS/PASS |
| E5 Activation port mismatch | 6.866355 | 7.725732 | 11.1236% | expected FAIL/FAIL |
| E6 Activation repair | 13.179090 | 29.347668 | 55.0932% | PASS/PASS |

E1–E3 的 targeted 只有被登记的文档/metadata/binding checker，因此小到约 25 ms；full suite 约 29.4–29.7 秒。E4 是 Activation comment change，局部 elaboration 仍耗时约 13.18 秒。E5 中生产者 `Activation.sv` 端口失配：两臂 `vlogan_returncode=0`，完整消费者 VCS elaboration `VCS=255`，日志有 `Error-[UPIMI-E]`，表明仅源码分析看不出消费者命名端口不匹配。两臂均检测，因此这例结果一致。E6 修复生产端口，两臂均返回 0。

E4/E6 节省约 55%，而计划中 ≥70% 是预计而非已验证目标；E5 两臂都失败，只有约 11% 墙钟差。E1–E3 高节省与非常窄的 targeted gate 相关，不可外推为任意源码变化平均可省时。总审计 48/48 通过的是运行记录完整性，不是硬件功能 correctness test。

来源路径异常：第一轮 runner 读的是 `tracebench_v6_rtl_v4/F6_Activation`，计划指定 v7 fixture。团队逐字节核对 v7 `Activation.sv`、diagnosed fault、fault tar member、repair source、pair source hash 和修复 archive，确认本次实际 fixture 内容与 v7 case 等价，并把最初误指向、等价证据、runner source hash 和结果关联写入 `fixture_provenance.json`。没有悄悄把 v6 目录名称重命名成 v7，也没有因结果通过而隐去错误。

### TraceBench v8：比较条件、调用与计分

十个 F1–F10 故障快照从 TraceBench v7 RTL case archive 分别展开到 B0 和 ACCORD 两个隔离工作区。每个工作区先通过远端 VCS 重现自己的故障，再发模型请求、应用模型提出的补丁（如有），再把变更源码打包上传远端进行 VCS compile/elaboration。B0只接收 raw failure log 与局部消费者 source context，不提供 DCG producer projection 或文件授权；ACCORD接收相同局部源片段，另附 DCG 静态上下文和允许修改文件清单。两臂都没有向 LLM 提供不同的 RTL source excerpts。每个 case/arm最多两次请求；本机中断但已发起的请求仍计入上限。

此比较执行的是当前 env-resolved `OpenAI/gpt-6.1-sol`，API wire 为 Responses，host 为 `www.a8pi.com`。历史 fixture来自 Claude Opus 5 run；本次并未调用 Claude，因此不是跨 provider 测试，也不能拿来解释 Claude 线能力。认证只通过环境注入，密钥未写入报告。

汇总计数：B0初始故障10/10、repair VCS pass 8/10、promotion 5/8 attempted、15请求、1.5请求/案、scope violation 0/10、consumer edit 0/10。ACCORD初始故障10/10、repair VCS pass 8/10、promotion 6/8 attempted、15请求、1.5请求/案、scope violation 0/10、consumer edit 0/10。全体 20/20 初始故障真实重现。integrity audit 记录完整 arm-case rows、请求次数上限、远端 VCS 绑定及 provider/model 一致性，30 个请求文件。

#### TraceBench v8 逐案汇总

| Case | B0 状态 | B0 请求 | ACCORD 状态 | ACCORD 请求 | 关键记录 |
|---|---|---:|---|---:|---|
| F1 DenseFFN | no_patch | 2 | no_patch | 2 | B0缺少准确 producer port declaration；ACCORD两次超上下文窗口，未形成补丁 |
| F2 GeneratedAcceleratorTop | repair_pass | 2 | repair_pass | 2 | 两臂多补丁回复先被旧 executor 拒绝；后对保存回复分别重放和 VCS，ACCORD promotion通过 |
| F3 Attention | no_patch | 2 | repair_pass | 1 | ACCORD VCS pass，但缺 codegen_compile_gate，promotion未过 |
| F4 IntegerAttention | repair_pass | 2 | no_patch | 2 | B0 VCS pass但promotion缺 codegen_compile_gate |
| F5 Linear | repair_pass | 2 | repair_pass | 2 | 两臂修复两处精确标识符；B0首轮不唯一匹配，第二次准确 patch |
| F6 Activation | repair_pass | 1 | repair_pass | 2 | 两臂 VCS pass，但都缺 codegen_compile_gate 而未晋升 |
| F7 ResidualAdd | repair_pass | 1 | repair_pass | 1 | 两臂 VCS pass，ACCORD promotion通过 |
| F8 PhysicalStreamFifo | repair_pass | 1 | repair_pass | 1 | 两臂 VCS pass；B0缺 gate evidence 未 promotion，ACCORD promotion通过 |
| F9 WeightTileCache | repair_pass | 1 | repair_pass | 1 | 两臂 VCS pass，ACCORD/B0均 promotion通过 |
| F10 QKVProjection | repair_pass | 1 | repair_pass | 1 | 两臂 VCS pass，ACCORD/B0均 promotion通过 |

逐案中 B0 无 patch 的只有 F1/F3；ACCORD 无 patch 的为 F1/F4；其余每臂八例 VCS pass。promotion失败的 B0 F4/F6/F8 与 ACCORD F3/F6，不是 VCS failure，而是状态晋升所需 checker evidence `codegen_compile_gate` 不存在。因此不得把 8/10 compile pass写成8/10 promotion，也不得说promotion失败就一定是硬件功能错误。

F1 两臂均不能修复：B0 两次真实响应指出只给出消费者端上下文，缺少 DenseFFN.sv producer port declaration，无法无猜测地构造精确替换。ACCORD 首版上下文把完整 generated producer RTL 与全量 graph 放进 prompt，大小约3.92 MB；两次 HTTP 502 response body 明确报告超过模型 context window。这是请求内容过大，不是 API key/余额错误，也不是切换 provider。之后 runner 改成围绕报告端口与消费者实例的 bounded snippets，两臂共享同一源 excerpt，ACCORD只增加图信息和 authorized-file list；旧失败和请求额度均保留。F1在固定两请求预算内仍 no_patch。

F2 两臂模型都给出真实多 patch 回复。旧 executor 的实现只接受单 patch，拒绝模型提案，留下 attempt application failed 记录。后续修正多 patch exact-search executor 后，未再请求模型，而是读取已保存响应执行 post-hoc replay；每个 patch 都要求精确搜索唯一匹配，应用后生成 diff、source manifest，再远端 VCS。两个分支均 `vlogan=0,VCS=0`，ACCORD调用本地 `SACGStore.promote()` 后状态 promoted。保存回复重放 audit 2/2通过，但这不是原始 live loop 首次返回后自动成功；报告将其独立描述为 executor correction/replay。响应哈希、重放 executor hash、diff、manifest、remote VCS source hash 与 promotion evidence 全部保留。

F3 ACCORD/F6两臂是典型计分边界：VCS compile/elaboration通过，但 native promotion要求的 `codegen_compile_gate` evidence缺失，因此promotion拒绝。不能通过放宽报告语言将它们变成“完全修复成功”。同理，VCS通过只表示当前编译/展开门限通过，不验证数据流运行、数值、位宽语义之外的协议、模型输出或硬件性能。

#### TraceBench scope violation 口径

脚本分别记录 `scope_violation`（是否提出超授权文件）与 `consumer_corruption`（是否实际应用对消费者文件的更改）。两臂均为0/10、0/10。ACCORD启用写范围约束，但本批次未出现能区分两臂的越界模型提案。B0没有 write lock，但并不等于B0“尝试过越界”；因此结果不能支持“ACCORD阻止了B0会犯的错误”。在论文中可报告本样本 observed violation zero for both arms，并把对锁的实际拒绝行为作为尚未被触发/验证的功能。

#### TraceBench completeness 与 replay 审计

最终 `llm_ablation_summary.json` 有20条 arm-case rows；`metrics.json`为聚合值；`integrity_audit.json`检查20行完整、每案请求≤2、初始故障均重现、所有被算为 pass 的 case 有新远端 VCS 记录及源绑定、全部 request metadata provider/model一致，request_count=30。`saved_response_replay_audit.json`记录F2 B0/ACCORD各一条，pass=2、fail=0。audit的“pass”只说明重放过程的 source application、VCS和关联审计成功；不是额外2次LLM请求，也不是 replay前旧executor原始通过。

### Validation5 的进程问题与修正记录

| 事件 | 当时现象 | 根因/判断 | 已做处置 | 对结果影响 |
|---|---|---|---|---|
| TraceBench初始F1 ACCORD 502 | 连续两次 HTTP 502 | response body 明示输入超过context window；首版请求约3.92MB | 保存失败；缩短为局部 source excerpt；同一修改同时适用于两臂 | 两次计入预算；F1最终no_patch，未改provider |
| TraceBench F2 patch应用拒绝 | 模型回复有效，但 executor拒绝 | executor假定exactly one patch，忽略合法多patch响应 | 修复临时实验runner的multi-patch精确应用，基于原响应离线重放 | 作为post-hoc correction单独披露，不伪装live首轮成功 |
| Paired fixture路径误读 | runner初读v6目录而计划指v7 | 实验fixture路径引用错误 | 与v7源码/archive逐字节及hash核验；写fixture provenance | 纳入结果但披露路径错误及核验；不重命名数据来源 |
| PropBench预期值未达到 | 两跳 recall仅0.817，低于计划95–100% | 静态图仅两条parent edges且无宽度耦合memory关系 | 不扩图、不按gold补边；保留 misses | 真实反映方法边界，不对指标进行调参 |
| Paired Timing节省率低于预计 | E4/E6约55%；E5约11% | full suite和局部 elaboration耗时差距有限；E5均失败 | 保留原始时间与共同门限状态 | 论文不能照搬计划70%预测 |
| VCS pass未触发promotion | 若干案例 VCS 0却 promotion fail | 缺少`codegen_compile_gate` evidence | 将VCS pass与promotion分开计数 | 不能把compile pass描述成状态晋升/完整修复 |

## Validation5 的最终可支持结论

1. 在这十组历史 byte-diff 候选中，按独立静态模块父边最多上溯两跳的 predictor 比旧 flat rule 有更高的 macro/micro recall 和 macro preservation；仍遗漏顶层及 width-coupled memory变化，未证明语义依赖完整。
2. 在本轮选定的六种变异上，targeted和full均在E5检出Activation端口连接故障且在E6通过；单轮时间显示E1–E3 metadata/document targeted gates极快，E4/E6约55%节省。结果并不能确立普遍 gate-equivalence，也不包括运行仿真。
3. B0和ACCORD在真实模型调用下每臂各8/10达到VCS compile/elaboration pass，未观察到pass率差异；本轮没有越权proposal，两臂都零consumer edit，不能证明DCG/scope限制减少了越权风险。
4. promotion evidence gate确实在若干VCS pass后拒绝晋升缺少指定 checker evidence的候选。此处是evidence completeness拒绝，不能混为工具编译失败。
5. 所有计划中预期值（PropBench95–100%、Paired E4≥70%、ACCORD明显优于B0、scope violation近零而B0更高）必须与实测分开，不能写成实验结论。

## 下一步评估时应保留的判定维度

- 将 byte-diff coverage、contract checker detection、graph candidate ranking、LLM repair application、remote compile/elaboration、native promotion、runtime simulation、synthesis timing分别计数。不要用一个“成功率”混合多个阶段。
- B0和ACCORD比较应固定模型provider/model、prompt source context、source tree、fault injection、请求预算和 VCS gate；同时报告请求数、错误响应、no_patch、patch application reject、VCS失败、promotion拒绝。
- 若研究“scope-bounded repair避免越权”，需要一个真实发生越界的proposal，或者有可审计的policy denial/feedback事件；纯零越界不能证明拦截效果。
- 若研究“图引导根因定位”，需区分候选集合覆盖、Top-1唯一命中、多候选爆炸半径准确度、实际选择用于修复的节点以及最终功能/编译验证。不要将静态候选数直接说成root cause accuracy。
- 若研究“targeted revalidation效率”，需要多轮重复测量或至少说明single trial；固定计时边界、同一snapshot、同一工作库策略、相同返回码和gate结果，并记录targeted选择器实际消费了变异文件。
- 若后续需要更强的语义结论，必须增加真实 RTL runtime testbench/运行门限或完整模型激励；compile-only的论文表述不能越过证据层级。

## 实验原始产物相对关系

Validation5 raw data directories are preserved in the repository. The following source reports are included in full below, rather than referenced as substitute indexes:

- Validation1/2-era complete chronology and mechanism history.
- Validation3 complete experiment narrative and Validation4 full detailed extension.
- Validation4 concise final result record.
- Validation5 current summary plus per-case evidence ledger above.

The embedded historic reports may repeat some contextual conclusions. Repetition is retained to preserve original chronology and avoid silently rewriting past interpretations. When historical phrasing differs, the later date-tagged checkpoint and raw JSON/log are authoritative for the run it describes; this report does not delete old wording or erase the correction history.

## TraceBench v8 detailed case ledger: B0 raw-log only

### F10_QKVProjection

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=QKVProjection.sv. Model rationale recorded: Restore the expected QKVProjection input port name and its internal connection while preserving the signal width and behavior. Rerun VCS compilation, elaboration, and linking to verify the repair; no tool rerun is evidenced here.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `39ccd3887361ea13f040871a17bbea7cfaad6830bca9fbcfe9f589ed7e1c020e`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F10_QKVProjection/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F1_DenseFFN

- Final runner status: `no_patch`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=False; executor_reason=expected exactly one patch proposal. Model rationale recorded: The raw log proves that GPT2PreLNBlock instantiates DenseFFN with io_upWeight_bits_addr, but the supplied evidence does not include DenseFFN.sv contents or its actual port declaration. Therefore the existing DenseFFN port name cannot be identified, and an exact search/replace patch cannot be proposed without guessing. No VCS rerun evidence is available.
  - Attempt 2: response status `response`; applied=False; executor_reason=expected exactly one patch proposal. Model rationale recorded: The log identifies the missing DenseFFN port, but the supplied evidence does not include DenseFFN.sv source. The existing port name and its internal references cannot be established, so an exact behavior-preserving search/replace patch cannot be proposed safely. Inspect DenseFFN.sv, restore the named port and any affected references, then rerun VCS compilation, elaboration, and linking.
- Post-repair VCS: not run because no patch reached that step. Recorded request errors: none in this aggregate row.
- Native promotion: not attempted because no repair passed the post-repair stage.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F1_DenseFFN/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F2_GeneratedAcceleratorTop

- Final runner status: `repair_pass`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 2: response status `response`; applied=False; executor_reason=expected exactly one patch proposal. Model rationale recorded: Restore the named output port expected by GeneratedAxiDdrTop and preserve its internal connection. VCS compilation, elaboration, and linking must be rerun; no tool rerun is evidenced here.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `f1a6e8049794b7c9c279e8cf2cbf6cfa706da26ce78c8a95f4e37b827a023520`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F2_GeneratedAcceleratorTop/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F3_Attention

- Final runner status: `no_patch`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 2: response status `response`; applied=False; executor_reason=search text must match exactly once; proposed_file=Attention.sv. Model rationale recorded: Restore the Attention input port name expected by GPT2PreLNBlock and update its internal connection without changing its width or behavior. A VCS compilation, elaboration, and linking rerun is required to verify the repair.
- Post-repair VCS: not run because no patch reached that step. Recorded request errors: none in this aggregate row.
- Native promotion: not attempted because no repair passed the post-repair stage.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F3_Attention/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F4_IntegerAttention

- Final runner status: `repair_pass`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=False; executor_reason=search text must match exactly once; proposed_file=IntegerAttention.sv. Model rationale recorded: Replace every occurrence of the faulted identifier in IntegerAttention.sv. This restores the named input port expected by Attention and preserves its internal uses. Compilation, elaboration, and linking must be rerun; no tool rerun is evidenced here.
  - Attempt 2: response status `response`; applied=True; files=IntegerAttention.sv. Model rationale recorded: Restore the named input port expected by Attention while retaining the existing internal signal name through a wire alias. A VCS compilation, elaboration, and linking rerun is required to verify the repair.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `5916b53ba227c4b9dc13f352c96689c7cd003e01e7265ed769554eb0b37b56be`.
- Native promotion: `not_promoted`; reason: transition missing passing checker evidence: ['codegen_compile_gate'].
- Changed SV files relative to pristine: IntegerAttention.sv.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F4_IntegerAttention/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F5_Linear

- Final runner status: `repair_pass`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=False; executor_reason=search text must match exactly once; proposed_file=Linear.sv. Model rationale recorded: The QKVProjection instance connects the named port io_weight_bits_addr, but Linear.sv declares and references the same address signal with an erroneous _tracebench_fault suffix. Renaming that identifier throughout Linear.sv restores the expected port and preserves the existing signal behavior. No tool rerun evidence was supplied, so compilation success is not claimed.
  - Attempt 2: response status `response`; applied=True; files=Linear.sv. Model rationale recorded: Restore the expected Linear port name and its internal reference without changing the weight-loading logic. A VCS compilation, elaboration, and linking rerun is required to verify the repair.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `094156d6d9c0e6865176123fdc2136aea0b5b6db1099cca4bded88d11e4c7655`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F5_Linear/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F6_Activation

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=Activation.sv. Model rationale recorded: Restore the named input port expected by DenseFFN while retaining the existing internal references through an equivalent wire. VCS compilation, elaboration, and linking must be rerun; no pass is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `77032f56d8aa8ea2da8ec9d683d85339a1d6f5213569b3ecceafc7211529765b`.
- Native promotion: `not_promoted`; reason: transition missing passing checker evidence: ['codegen_compile_gate'].
- Changed SV files relative to pristine: Activation.sv.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F6_Activation/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F7_ResidualAdd

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=ResidualAdd.sv. Model rationale recorded: Both failing instances connect io_residual_bits_data, but ResidualAdd declares the renamed io_residual_bits_data_tracebench_fault. Restore the expected port name and its FIFO connection, preserving the 128-bit width and existing behavior without changing either caller. This is a proposed repair only; successful VCS compilation, elaboration, and linking must be confirmed by a tool rerun. No simulation execution is required.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `ef21d41bdf265f6154deb72d78c24a1d540d3ea666bfc145ddaca8013cf0d15f`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F7_ResidualAdd/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F8_PhysicalStreamFifo

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=PhysicalStreamFifo.sv. Model rationale recorded: The VCS errors show both ResidualAdd instances connect the named port io_enq_bits_data, while PhysicalStreamFifo declares the same 128-bit input with an unintended _tracebench_fault suffix. Renaming only the declaration restores the expected module port without changing width, behavior, or interfaces. No tool rerun evidence was supplied, so compilation success is not claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `c2069c977694be082f74f53adb754c9eacac42d6f520be0dbfa9679cada6a4ee`.
- Native promotion: `not_promoted`; reason: transition missing passing checker evidence: ['codegen_compile_gate'].
- Changed SV files relative to pristine: PhysicalStreamFifo.sv.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F8_PhysicalStreamFifo/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F9_WeightTileCache

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=WeightTileCache.sv. Model rationale recorded: The VCS error identifies a named-port mismatch: Linear connects io_tileRequest_bits_routeId, but WeightTileCache declares the fault-suffixed name. Restore the expected name in both the output declaration and its assignment, preserving the 16-bit width and missRouteId driver without changing consumer wiring or behavior. This is a proposed repair only; successful VCS compilation, elaboration, and linking must be confirmed by a tool rerun.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `dfcefe02d137d420032a03d65b42fd0748470cf27bbd01eafb37f79bf89bda7a`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/B0_raw_log/F9_WeightTileCache/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).


## TraceBench v8 detailed case ledger: ACCORD DCG-bounded

### F10_QKVProjection

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=QKVProjection.sv. Model rationale recorded: The consumer connects the authorized port name io_weight_bits_addr, while the producer declaration and its internal WeightTileServiceMux connection use an unauthorized tracebench_fault suffix. Renaming both producer-side occurrences restores the exact named port without changing width, direction, behavior, or interface semantics. No VCS rerun evidence was supplied, so compilation/elaboration success is not claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `d6f212e85c052a0b0023bf88858a533741d9422a436534d87f90a46678433e0f`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F10_QKVProjection/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F1_DenseFFN

- Final runner status: `no_patch`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `error`; no application metadata. Model rationale recorded: (no rationale recorded)
  - Attempt 2: response status `error`; no application metadata. Model rationale recorded: (no rationale recorded)
- Post-repair VCS: not run because no patch reached that step. Recorded request errors: HTTP Error 502: Bad Gateway; response_body={"error":{"message":"Your input exceeds the context window of this model. Please adjust your input and try again.","type":"upstream_error"}} | HTTP Error 502: Bad Gateway; response_body={"error":{"message":"Your input exceeds the context window of this model. Please adjust your input and try again.","type":"upstream_error"}}.
- Native promotion: not attempted because no repair passed the post-repair stage.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F1_DenseFFN/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F2_GeneratedAcceleratorTop

- Final runner status: `repair_pass`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=False; executor_reason=expected exactly one patch proposal. Model rationale recorded: Restore the named output port expected by the wrapper and retain its existing internal driver connection. VCS compilation, elaboration, and linking must be rerun on the patched sources; no pass is claimed.
  - Attempt 2: response status `response`; applied=False; executor_reason=search text must match exactly once; proposed_file=GeneratedAcceleratorTop.sv. Model rationale recorded: Restore the named output port and its internal connection to the name used by GeneratedAxiDdrTop, without changing the signal width or data path. A VCS compilation, elaboration, and linking rerun is required; no pass is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `358b53c937c9cae59b9ad0b71ad53c63266451d1350ede6e4ef05e85766953f7`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F2_GeneratedAcceleratorTop/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F3_Attention

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=Attention.sv. Model rationale recorded: The DCG context identifies Attention.sv as the sole authorized producer source. Its declared input is the fault-renamed 192-bit io_in_bits_data_tracebench_fault, while GPT2PreLNBlock instantiates the intended 128-bit named port io_in_bits_data. Restoring the producer declaration and its internal connection to the expected 128-bit port preserves the consumer interface and dataflow. No VCS rerun evidence was supplied, so compilation/elaboration success is not claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `3902dd18d7b05fdb47686189ce5f67d12d4afbbc5267ce3f0956a3ee007bce65`.
- Native promotion: `not_promoted`; reason: transition missing passing checker evidence: ['codegen_compile_gate'].
- Changed SV files relative to pristine: Attention.sv.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F3_Attention/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F4_IntegerAttention

- Final runner status: `no_patch`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=False; executor_reason=search text must match exactly once; proposed_file=IntegerAttention.sv. Model rationale recorded: Replace every occurrence of the fault-renamed identifier in the authorized producer file, restoring both the 192-bit input port expected by Attention.core and its existing internal references. The DCG producer/consumer projection localizes this compile-time mismatch to self-attention; no datapath, scheduling, width, or other interface changes are needed. This is an unverified repair proposal: acceptance requires rerunning real VCS compilation, elaboration, and linking on the patched sources, without running the simulation executable.
  - Attempt 2: response status `error`; no application metadata. Model rationale recorded: (no rationale recorded)
- Post-repair VCS: not run because no patch reached that step. Recorded request errors: The read operation timed out.
- Native promotion: not attempted because no repair passed the post-repair stage.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F4_IntegerAttention/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F5_Linear

- Final runner status: `repair_pass`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `error`; no application metadata. Model rationale recorded: (no rationale recorded)
  - Attempt 2: response status `response`; applied=True; files=Linear.sv. Model rationale recorded: Restore the named input expected by QKVProjection and its internal reference without changing the weight-ready logic. VCS compilation, elaboration, and linking must be rerun; no pass is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `d1c668edf4d2f46466cfe6655e52afa811b1e1d93e5a0879a9f92da93e826bc3`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F5_Linear/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F6_Activation

- Final runner status: `repair_pass`. Actual request files: 2. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=False; executor_reason=search text must match exactly once; proposed_file=Activation.sv. Model rationale recorded: The Activation producer declares its input as io_in_bits_data_tracebench_fault while DenseFFN legally connects the intended io_in_bits_data port. Renaming this identifier throughout the authorized producer source restores the named-port interface and keeps all internal references connected to the same 128-bit input datapath without changing behavior. A VCS compile/elaboration rerun is required before claiming success.
  - Attempt 2: response status `response`; applied=True; files=Activation.sv. Model rationale recorded: Restore the named 128-bit input expected by DenseFFN and retain the existing internal datapath through a wire alias. A real VCS compilation, elaboration, and link rerun is required; no pass is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `da9f77fb2da3319d7ad3dece32ffaf836e6074bd875d627a1a0ad59453976510`.
- Native promotion: `not_promoted`; reason: transition missing passing checker evidence: ['codegen_compile_gate'].
- Changed SV files relative to pristine: Activation.sv.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F6_Activation/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F7_ResidualAdd

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=ResidualAdd.sv. Model rationale recorded: Restore the named input expected by both ResidualAdd instances and retain its existing FIFO data connection. VCS compilation, elaboration, and linking must be rerun on the patched sources; no pass is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `15b3119dad5affd39f3e9d31c83f369b12c865b15d73ede494130761d88d3032`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F7_ResidualAdd/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F8_PhysicalStreamFifo

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=PhysicalStreamFifo.sv. Model rationale recorded: Restore the named 128-bit enqueue port expected by both ResidualAdd instances and update its internal memory write reference without changing the FIFO datapath. VCS compilation, elaboration, and linking must be rerun; no successful rerun is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `cfa8ba1a441a059b8e8eafb0b172ad3f602d3cb2524bef50f1afeb766fd24bdd`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F8_PhysicalStreamFifo/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).

### F9_WeightTileCache

- Final runner status: `repair_pass`. Actual request files: 1. Initial injected fault reproduced: `True`. Scope violation: `False`. Consumer corruption: `False`.
- Model/executor attempts:
  - Attempt 1: response status `response`; applied=True; files=WeightTileCache.sv. Model rationale recorded: Restore the named output port expected by Linear and retain its existing missRouteId driver. A VCS compilation, elaboration, and linking rerun is required; no pass is claimed.
- Post-repair remote VCS: SSH rc `0`, `vlogan` rc `0`, VCS rc `0`, source binding match `True`. Log SHA-256: `9ceeda5bc4726b1298c1f1f45c11fa895468c33c3e9eb08cca56d494ef76c669`.
- Native promotion: `promoted`; reason: no rejection reason recorded.
- Changed SV files relative to pristine: none; restored source matches pristine package byte-for-byte.
- Per-case evidence directory: `tracebench_v8_agent_ablation/ACCORD_dcg_bounded/F9_WeightTileCache/` (contains request/response records when issued, failure report, patch, source bundle, VCS log, checker reports and promotion record as applicable).



# Embedded complete source report: Historical full chronology: early mechanism experiments through Validation2

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









# Embedded complete source report: Validation3 and Validation4 detailed execution report

# 核心机制实验：validation3 执行记录

日期：2026-11-01。本文记录 `core_method_validation3.md` 对应实验的实际执行结果；计划中的预期值不是测量结果。原始输入、日志、控制组和机器可读结果均保留在 `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation_20261031/`。

本文已经扩充为可独立阅读的详细结果报告：开头保留关键统计，后文展开逐例操作、版本演进、失败原因、实现路径、复核方式和下一步判断依据。详细内容直接写在正文中，无需依赖其他进展文档才能理解。此次扩充是对已保存实验的整理与复核，没有额外重跑三条硬件性能线。

## 实验设置及术语

- 受控基准为 GPT-2 Medium、24 层、序列长度 32、W4A8、VU9P，使用已有 T7/R2 设计快照；不同任务的基准及候选路径见各自的机器可读结果。
- `vlogan` 指 VCS 源文件分析；`VCS elaboration` 指编译和模块连接展开。两者不等价于运行仿真、数值正确、板级验证或上板结果。
- 模拟故障是受控注入，不是自主 Agent 自然遇到的全部故障分布。定点脚本修复不能替代 LLM 端到端自主修复的评价。
- 新增候选展开时，本地串行启动单个 SBT/JVM，最大堆 3 GiB、可见处理器数 2；观察到最低可用内存约 14.6 GiB。远端负责 VCS。

## PropBench v4：参数变化与产物

### 设计与执行

以 T7 同一基准为参照，构造 10 组单参数候选：rows 16→8、cols 32→16、FIFO 64→128、activation banks 2→4、rows 16→4、cols 32→8、cols 32→4、FIFO 64→32、activation banks 2→8、reuse 1→2。

前 4 组是历史独立 Stage-4/5 候选，后 6 组在隔离目录手工修改参数并实际进行独立 Chisel 展开，不是 6 次自主 Agent 或 DSE 运行。每个候选与基准对比的 21 个 Scala 文件中，仅参数文件变化。对 reuse=2 的直接物理配置和 case-class 参数也作了同步检查。

每组比较三个分支：完整候选；候选参数配旧 Stage-5 Scala/SV 的 stale 对照；候选参数与 Scala 配一个旧 SV 的 partial-update 对照。各分支执行参数物化检查与远端 `vlogan`，30 次源码分析均返回 0。

| 分支 | 参数检查通过 | 参数检查检测失配 | `vlogan` 通过 |
|---|---:|---:|---:|
| 完整候选 | 10/10 | 0/10 | 10/10 |
| Stale Stage-5 | 0/10 | 10/10 | 10/10 |
| Partial update | 10/10 | 0/10 | 10/10 |

检查器比对所选参数与 Scala 绑定，因此能发现构造的 stale 失配，但未检查 SV 是否与 Scala 一致。不能将本表描述成 partial update 也被该检查器拦截。

完整顶层 `GeneratedAcceleratorTop` 又对 4 个历史候选及其 partial 分支各运行一次 VCS 展开，共 8 次，均返回 0。rows=8 的 partial 分支出现 6 条端口位宽警告、cols=16 出现 10 条，完整候选均无对应警告；FIFO=128 和 banks=4 的两臂均无该类警告。VCS 将其作为警告，当前 compile-only 门限未将它们转为失败；这不是 4/4 局部失配检测成功。未运行仿真或 exact-board wrapper。

每组分别保存独立展开日志、输入参数、逐 SV 文件 SHA-256、变更集合、三个控制分支和工具日志。详细数据见 `propbench_v4/RESULTS.md` 与 `propbench_v4/combined_summary.json`。

### 尚未测得的指标

当前 SACG 把 Stage-5 生成源码作为整个包绑定，没有完整的逐参数到逐 SV 文件的独立依赖图。因此基准/候选的文件哈希变化是实测的文件差异，却不是独立的 graph-derived must-update / unrelated 真值。候选与自身的哈希匹配属于构造性相等，不能作为 `Affected-Artifact Sync Recall` 或 `Unrelated-Artifact Preservation` 的独立准确率。两个指标目前均为未测量。

## TraceBench v6：契约与真实端口失配

### 流水线契约元数据实验

对 10 条既有流水线边，分别在隔离计划中注入生产者输出宽度与流元素宽度失配。生产 `check_edge_contracts()` 给出包含边 ID 和字段的错误，静态上下文根据该边给出上下游端点。每案调用图绑定文件授权，对被授权的计划工作副本做定点字段修复，重跑 Stage-3 静态检查并调用远端 `vlogan`。

- 10/10 故障由契约检查器报告；10/10 报告边的上下游端点映射命中对应边端点。
- 10/10 执行了基准脚本中的精确文件授权，无观察到的作用域越界；10/10 修复后静态检查通过、10/10 未修改 RTL 源包的 `vlogan` 通过。
- 0/10 transition 完成 promotion，缺少 `data_order_trace_check`、`stream_plan_check` 的通过证据。

这是检查器已经明确指出违约边时的图端点投影；不是从未知 RTL 故障盲推根因的 10/10 成功率。修复由确定性脚本执行，远端编译的 RTL 未被修改，不能证明 RTL 实现了该契约。见 `tracebench_v6_final/summary.json` 与各 case 的故障计划、诊断、授权、补丁及日志。

源码身份校验经独立复核：故障副本的哈希必须与报告匹配，实际分析 source 内容须与故障副本一致，origin 必须能关联图内 artifact；没有副本字段的历史调用继续兼容。图状态和故障副本单独记录哈希。

### 真实 RTL 端口试点

在隔离的 `Activation.sv` 中重命名生产端口及模块内部引用，保留 `DenseFFN` 中原有消费者连接。故障包 `vlogan` 返回 0，而加载真实 XPM 依赖后的 VCS 展开返回 255，报告端口不存在；图投影给出 activation 级。对单一授权文件定点恢复后，同一门限 `vlogan` 和 VCS 展开均返回 0。修复文件哈希与基准一致。

该试点说明源分析和连接展开有不同检测能力；它是受控脚本修复，不是自主 Agent 修复，也不是功能仿真。transition 因缺少五项规定 checker 证据未 promotion；新 `SACGStore` 文件授权接口当前由基准调用，尚未证明生产 `stage_repair_execute` 使用该接口。机器结果为 `tracebench_v6_rtl_pilot_xpm/summary.json`。

### 真实 RTL 扩展最终结果

最终有效运行保存在 `tracebench_v6_rtl_v5/`；这里的 v5 是 TraceBench v6 的 RTL 补充实验第五次 runner 修订，不是历史 TraceBench v5。10 个请求案例中，9 个存在源码闭包内的实际消费者并执行，1 个顶层没有现成消费者而未运行，没有为凑分母构造新 harness。

每例首先改名生产模块端口及其本模块引用，保留子模块 named-port 标签。故障时所有 SV 先经 `vlogan` 分析，再对其真实直接消费者进行 VCS 展开。修复器只读取 VCS 缺失端口报告、报告指定的生产者源码和消费者实例连接；仅当端口声明与实例连接存在唯一缺失和唯一多余端口时才生成定点 token patch。它不读取 scoring sidecar 或注入时的端口变量。工具诊断文件由 VCS 报告路径选择，再建立故障副本与图中源产物的关系。

| 注入模块 | 结果 | 图候选数 | 故障 VCS | 修复 VCS |
|---|---|---:|---:|---:|
| GeneratedAxiDdrTop | 无现成消费者，未运行 | — | — | — |
| GeneratedAcceleratorTop | 通过 | 2 | 255 | 0 |
| Attention | 通过 | 1 | 255 | 0 |
| IntegerAttention | 通过 | 1 | 255 | 0 |
| Linear | 通过 | 2 | 255 | 0 |
| Activation | 通过 | 2 | 255 | 0 |
| ResidualAdd | 通过 | 2 | 255 | 0 |
| PhysicalStreamFifo | 通过 | 8 | 255 | 0 |
| WeightTileCache | 通过 | 8 | 255 | 0 |
| QKVProjection | 通过 | 1 | 255 | 0 |

已执行 9/9 故障的源码分析返回 0、消费者范围 VCS 展开失败；9/9 修复后源码分析和 VCS 展开返回 0。9/9 调用了基准中的精确文件授权，无观察到的 patch 越界。部分共享模块映射至全部八级；Activation 的两个候选包含模型算子与流水级的两种图表示。候选数不能转写成节点 Top-1 全部命中，文件修复成功也不能替代未知根因诊断成功率。

修复文件由编译器报告选择，图提供拥有者候选与代码包范围约束；当前授权允许相关代码包内请求的具体文件，不能称图独立缩小出了最小修复范围。它仍是确定性的接口修复微基准，不是自主 LLM 修复、runtime CCTG 因果追踪或生产 transition promotion。VCS 展开范围是每个模块的直接消费者，不是九次完整板级顶层验证。

每次 fault/repair 使用唯一远端目录，并记录本地工作源码、上传 tar 成员、远端实际解包源码的逐文件 SHA-256，上传包与远端包摘要也须相同；这些绑定及 SSH、工具返回码共同决定 PASS。独立审计核对全部九例的故障/修复 tar、manifest 和诊断副本，还通过 SSH 抽查三例远端实际文件；均一致。对应 18 项 focused 测试通过。最终 runner、helper、图投影、store 及测试副本保存在 `implementation_snapshot/`。

首个扩展版本错误地连带重命名子模块端口，产生非预期故障；后续又发现注入变量参与修复及修复前筛选的问题，这些版本全部保留，不混入最终有效分母。首次缺 XPM 模型的试点及一次 SSH 中断也保留原始日志。最终版加载真实 XPM、保留 named-port 标签、去除注入真值前置筛选并记录三方文件身份。没有因此修改实际硬件设计或放宽现有硬件验证门限。

## Paired Timing v4：编译期重验证

Full suite 明确定义为 constraint、template binding、pipeline plan、DSE materialization、package static 和远端 `vlogan` 六项编译期检查。基准六项均通过；4 个案例的 targeted 和 full 都使用各自同一个变异快照，六项 full 均实际执行。

实验采用显式 gate 输入依赖清单，将基准与变异快照对应内容 SHA-256 的变化转为 invalidation，并调用生产 `resolve_revalidation_gates()`。针对首次实现发现的问题，已补充新增/删除 Scala、SV 文件的依赖集合并集，并将图中模型配置和 case adapter 路径在内存中绑定到对应快照。实际静态读取审计确认共享模板库和 semantic adapter 是外部输入，前后哈希保持一致。新增/删除及路径重绑定的 2 项回归通过。

| 变化类型 | Targeted，含 hash 和 resolver（秒） | Full（秒） | 节省 |
|---|---:|---:|---:|
| README 注释 | 0.0216 | 3.6732 | 99.41% |
| 流水线元数据 | 0.0243 | 3.7092 | 99.34% |
| 参数 Scala 注释 | 0.0237 | 3.7028 | 99.36% |
| RTL 注释 | 3.7205 | 3.7620 | 1.10% |

这是各案例一次配对测量的微基准，包含内容哈希和 resolver 耗时，但不包含快照构建或预存基准哈希；网络和远端负载可能影响秒数。空 targeted 集合对应 README 未触发列出的硬件 gate，不等于任何设计更改都可跳过验证。变更只是注释或元数据，不能据此证明语义错误检出或整个 Agent 设计流程的加速。依赖清单由实验显式定义，不能声称生产环境已经自动推导完整依赖闭包。结果、实际读取审计、回归日志与运行脚本快照在 `paired_timing_v4_snapshot_audit/`。

## 代码、测试与论文草稿

- 新增静态故障到图节点的别名投影、故障副本身份校验，以及 `SACGStore.authorize_repair_artifacts()`；当前基准直接调用授权接口，尚未证明其在生产 repair executor 中运行。
- 独立轻量回归：SACG、evidence 和 DSE 相关共 44 项通过；paired runner 增删文件和输入绑定 2 项通过。
- 真实端口注入/修复器及其图投影、授权的 18 项 focused 测试通过；该数字与前一项有重叠，不能相加作为独立总测试数。
- 扩大测试曾运行 45 项，44 项通过、1 项旧用例失败：其断言依赖 `PhysicalFp32Mul` 实例，而当前设计为 W4A8 整数乘法。此项没有因为实验而修改或跳过。
- `docs/草稿4.tex` 已修正 `constraints` 拼写并将指定描述改成实际的编译和综合时序证据，明确这些结果本身不证明数值正确或 post-route 收敛。仓库缺少该草稿引用的图片和 bibliography 文件，未能构建完整 PDF。

## 目前可得与仍需完成

现有结果支持：在本组控制性 stale 绑定条件下，Scala 参数检查发现 10/10 失步，而源码分析均通过；十条显式报边的流契约失配可映射到图端点并定点修复；九组有效真实 RTL 端口失配可在消费者范围 VCS 展开后经证据驱动的确定性脚本修复；显式依赖清单下小范围变更的编译期重验证有上述实测时间。

仍未得到独立文件级 SACG 传播召回率、partial SV 失步的通用生产检查、完整生产依赖自动推导、生产修复执行器的新增图授权闭环、以及无答案泄露的自主 LLM RTL 修复成功率。不能将这些未测结果写成既有的 100%。

## 保存记录的一致性复核

`audit_validation3_results.py` 对上述四个最终汇总重新计算计数、检查原始日志摘要、比对配对实验的选中 gate、实际变异字节和耗时算术，以及 RTL fault/repair tar 的全部成员摘要与远端记录，并检查 patch 是否落在授权集合内。106 项记录一致性检查全部通过，结果为 `validation3_integrity_audit.json`；这不是 106 项硬件正确性测试，也不消除前述方法学限制。

截至本轮结束，已完成所记录的编译期受控实验和必要复核；计划所设定的两个文件级图指标及完整生产修复闭环没有凭空补成成功，保留为明确的未完成能力。无需重新运行此前三条性能线来复用本轮记录。

## 独立阅读指南：本轮要回答什么

本报告将计划、执行、失败、修正和最终观测放在一起，供后续评估和制定实验计划使用。
这里的“本轮”指 2026-11-01 执行的 validation3，而不是此前所有性能线或全部机制实验的重新运行。
三项主实验共用已有 GPT-2 Medium、24 层、seq=32、W4A8 和 VU9P 的设计背景，但各自操作不同的隔离快照。
PropBench 的共同参数基准来自 T7；TraceBench 与 Paired Timing 使用已有 R2 快照，均处于 reuse=1 的同一实验族。
T7 的列数为 32，R2 是相对 T7 把列数改为 16 的历史候选；两者不是同一份参数配置。
因此，PropBench 的单变量变化应相对于 T7 理解，不能误以为十组都相对 R2 的 cols=16 再改变。
这里的参数变化、元数据变更和故障注入是为了测量机制而设计的实验操作。
它们并不意味着相同频率地出现在真实用户的设计过程中。
原计划中的“100%”和预估耗时属于希望获得的结果，不构成实际测量。
本报告优先记录保存的运行结果以及对运行脚本和数据的复核。
任何作为后续实验依据的数字都应连同实验对象、分母、检查门限和未覆盖范围一起使用。

### 三个问题、三类实验

第一个问题：架构参数变化以后，已有的设计参数检查能否发现 Stage-4 和 Stage-5 之间不一致？
PropBench v4 用独立展开候选、完整候选、冻结 Scala 的 stale 对照和回退部分 SV 的 partial 对照回答其中一部分。
它还观察 Chisel/SV 实际文件差异，并检查生产图能否给出独立的文件级依赖依据。
第二个问题：在明确的流契约错误或受控 RTL 端口错误下，静态图投影、授权和补丁能否配合工具检查？
TraceBench v6 分别运行十条元数据边失配和一组真实源码接口失配。
两者的触发条件、修复目标以及检查器覆盖层次不同，不能合并成一个统一的自主修复成功率。
第三个问题：对于不同范围的变更，按照声明的证据依赖选择检查，是否比完整编译期套件节省时间？
Paired Timing v4 对同一变异快照执行 targeted 与 full 两臂，并将本地哈希及 resolver 成本计入 targeted 时间。
这一实验回答显式登记依赖下的编译期检查成本，不直接回答完整工程维护成本或完整 Agent 运行时间。

### 最终数据与统计分母

PropBench 的 10 组候选是 10 种相对相同基准的配置，并非 10 个自然发生的生产事故。
前三臂各 10 组，因此 `vlogan` 的分母是 30 次源码分析，不是 30 次独立硬件生成流程。
完整候选参数检查通过 10/10；冻结旧 Scala 的 stale 失配检出 10/10。
partial 分支把一个相关 SV 换回旧版本，当前 Scala 绑定检查未发现 10/10。
partial 的 10/10 源码分析通过也不等于硬件正确。
额外的完整生成顶层展开只覆盖 4 组候选及其 4 个 partial 分支，分母是 8 次。
其中 2 个 partial 出现位宽警告，所有展开返回码仍为 0。
未构造图推导的独立文件级真值，因此文件级 recall 和 preservation 均未测。

TraceBench 的元数据部分分母是 10 条独立受控流边。
检查器先明确报错边与字段，图再投影边端点；对应端点命中为 10/10。
定点修复元数据后静态检查通过为 10/10，但没有改变用于编译的 RTL。
缺少规定 evidence 导致 promotion 为 0/10，不应将静态检查通过等同于正式状态晋升。
RTL 扩展共请求 10 个注入目标，但一个顶层没有现成消费者，因此实际执行分母为 9。
9/9 故障源码分析返回 0、直接消费者 VCS 展开失败；修复后 9/9 两项返回 0。
修复是确定性脚本根据工具报告与连接信息生成的 token patch，不是 LLM 逐例自主分析得到的结果。
图候选数为 1、2 或 8；不宜汇总为 9/9 的 graph Top-1 根因定位。

Paired Timing 的分母是 4 个变更案例，各案例各有一次 targeted 与一次 full 计时。
full 是六项编译期门限的约定集合，而不是所有可能验证、综合或上板步骤。
四案例的节省分别为 99.41%、99.34%、99.36%、1.10%。
这些百分比对应单次配对微基准，既不是多次重复实验的统计区间，也不是端到端全流程的平均加速。
前 3 个变动非常轻，第四个 RTL 注释仍触发远端源码分析，因而两臂耗时接近。
实验依赖关系由显式 gate 输入登记表提供，实际读取审计帮助检查这次实验；不能推断通用自动依赖发现已完成。

### 工具、行为与证据含义

Scala 参数绑定检查比较候选参数与 Scala 实现配置，能够捕获本实验构造的旧 Scala 值。
这一检查没有证明生成的每个 SV 文件与 Scala 保持一致。
Chisel elaboration 根据配置生成硬件描述；独立 SV 树哈希差异说明生成文件存在变化。
哈希差异本身不提供“哪些文件必须变化”的独立图真值，也不能单独证明语义正确。
`vlogan` 对源码做语法和分析，是本实验的一项 compile-only 检查。
完整或局部 VCS elaboration 还检查选定顶层的模块引用和连接。
本轮部分实验以不同的消费者模块作为 elaboration 顶层，不能称为全部通过同一板级顶层。
编译返回 0 可以与警告同时出现；只有实际将警告纳入 gate 判错规则时才会导致门限失败。
运行仿真需要执行仿真器和测试场景；编译或展开通过不等于实际运行。
本轮没有据此证明模型数值正确、真实 DDR 数据流正确或 FPGA 上板成功。
Vivado 综合时序属于不同实验的证据，也不能仅由本轮编译结果推断布局布线时序收敛。

### 为什么保留失败和中间版本

保留失败不是把旧结果与最终结果混为一谈，而是为了准确解释为什么最终版本采用当前口径。
旧 PropBench v3 将同一 SV 树链接到多个候选，不能作为十组独立展开的证据。
本轮 v4 对新增六组运行独立 Chisel 展开，并结合四组历史独立候选。
但独立展开解决的是“候选是否实际生成”问题，并不会自动产生逐文件 graph oracle。
旧 TraceBench 语法错误与契约失配是两种不同故障，不能只调整打分名称就视为同一种验证。
新的元数据和端口实验分别给出静态契约与连接错误的真实受控案例。
其间错误注入、未加载库、输入真值泄露风险以及 SSH 终止，均应按对应版本单独解释。
旧 Paired Timing v3 的 full 静态检查读取原始目录，因此无法直接支持同快照配对结论。
v4 的第一轮审计又发现新增文件和绝对路径的问题，故最终仅引用修正后的 snapshot-audit 运行。
各次修订使实验问题更容易定位，但修复脚本缺陷不等于已经证明完整生产机制的全部指标。

### 核心机制和实验之间的关系

SACG 保存模型、流水线、产物和相关约束的图表示；图数据与工具报告需要通过明确映射关联。
在本轮 PropBench 快照中，生成源码以包粒度绑定，因而无法独立枚举每个参数必须改变的 SV 文件。
在本轮元数据实验中，违规边由契约检查器先确定，图投影为这条边提供关联端点。
在 RTL 扩展中，编译器报告提供源文件和端口线索，静态投影提供相关候选节点。
不同模块在图中可能对应单个节点、多个节点或共享资源，因此候选集合大小存在差异。
`authorize_repair_artifacts()` 可检查基准所请求文件的授权范围，但生产修复执行路径是否调用仍未证明。
只证明在本实验的请求与授权集合中未观察到越界，不能推断图已自动形成全局最小修复集。
transition 声明、补丁授权、evidence 校验和 promotion 是不同步骤。
某一步通过不意味着后续步骤自动通过；本轮元数据案例的 promotion 就因缺证据而未通过。
重验证 resolver 将已失效证据及声明依赖映射为 gate，效果取决于输入依赖声明是否覆盖真实读取。
本轮为提高可复核性而明确记录依赖，并审计外部模板及 adapter 的实际读取和哈希。

### 本轮结论可以怎样用于下一步

如果目标是修复传播机制，优先区分“参数值绑定错误”和“生成源部分回退”两类缺陷。
前者已在本案例中被现有检查器发现；后者未被同一检查器或源码分析阻断。
要计算真正的文件级传播 recall，需要先定义并验证独立于候选结果的 must-update 真值。
如果目标是改善故障定位，应区别静态违约边映射、编译器诊断驱动的接口修复和运行时未知故障追踪。
这些实验的观测入口与难度不同，不能通过更改指标名称合并。
要评估生产闭环，应确认生产 executor 确实调用授权接口，再记录补丁、工具复验与 promotion 所需证据。
要评估 targeted revalidation 的泛化，应加入语义变化和缺陷检出场景，并对实际 gate 依赖作可复核的完整性检查。
对性能结论，应分别标注综合频率、周期估计、RTL 仿真或上板测量的来源，不把本轮机制数据当性能测量。
以上是根据既有结果可提出的后续工作，不表示这些额外实验已经完成。

## PropBench v4 完整实验记录与分析

### 研究目的、范围和证据等级

1. 本实验关注参数变化之后，生成设计相关产物是否同步变化。
2. 对照还考察旧 Stage-5 产物以及部分更新造成的失配是否会被现有检查发现。
3. 基准是一份既有的 GPT-2 Medium 设计快照，模型为 24 层，序列长度 32。
4. 该基准采用 W4A8 和 VU9P 配置。
5. 参数快照来自 `T7-cross-token-reuse-1/ACCORD/run`。
6. 阵列行数基准值为 16。
7. 阵列列数基准值为 32。
8. FIFO 深度基准值为 64。
9. activation bank 数基准值为 2。
10. 跨 token 复用参数基准值为 1。
11. 同一物理基准也包含 16 lanes 和 512-bit refill 配置。
12. 六组新增试验不是 Agent 新生成六套硬件的端到端实验。
13. 它们是实验脚本在隔离工程内修改参数，再真正运行 Chisel 展开的探针。
14. 前四组使用已有的独立 Stage-4/Stage-5 候选记录。
15. 每个候选与共同基准仅变化一个所测参数字段。
16. 对现有 21 个 Scala 文件逐个比较哈希后，每个候选只有 `GeneratedDesignParams.scala` 与基准不同。
17. 这个源码审计有助排除模板源码变化导致的混杂。
18. 它本身不是 RTL 语义等价性证明。
19. `vlogan` 表示 VCS SystemVerilog 源文件分析。
20. `vcs GeneratedAcceleratorTop` 则对指定生成顶层进行模块连接展开。
21. 这两种结果均不能自动说明运行时正确性。
22. 这两种结果也都没有直接给出频率、周期数或吞吐量。
23. 本实验没有开展 exact-board wrapper 的仿真。
24. 本实验没有对每个参数候选进行资源可行性或时序可行性论证。
25. 本实验也没有通过 runtime 比较真实权重及输出数值。

### 数据来源、计数和文件身份

1. 初始四个候选来自既存的 Stage-5 生成产物。
2. 后续六个候选来自各自隔离的 SBT/Chisel 项目。
3. 候选一共有十种参数取值。
4. 源码一致性审计统计到十个不同的候选 SV 树身份。
5. 每个 SV 树身份是对已排序的文件名与逐文件 SHA-256 映射序列化后再取 SHA-256。
6. 这证实十份文件集合并非同一份字节内容重复计数。
7. 字节不同不能单独证明每个候选的计算语义都正确。
8. 不同输出文件名或生成器重编号也可能增加差异文件数。
9. 比较时以基准与候选各自目录中的顶层 `*.sv` 名称为键。
10. 哈希不同、只在一侧存在的文件都记为观测变化文件。
11. 两边同名且 SHA-256 相等的文件记为观测未变化文件。
12. 差异集合由输出比较得到，不是预先独立标注的因果依赖真值。
13. 整个受控实验包含十个候选和三个分支，合计 30 次远端源码分析。
14. 所有 30 次 `vlogan` 返回码均为 0。
15. 其中前四候选的完整候选与 partial 分支另做八次顶层 VCS 展开。
16. 八次展开均返回码 0，返回 0 的结果仍可能含警告。
17. 四个 stale 分支和新增六个候选没有计入这八次完整顶层展开。
18. 单个结果目录保留传输包、工具输出及哈希。
19. 实验汇总同时保存候选来源类别、参数变化和每个分支的检查结果。
20. 原始历史 run 没有被实验覆盖。

### 六组新增候选如何展开

1. 对每个新增案例，新建各自的隔离 Chisel 工程目录。
2. 从 T7 复制 Scala 源码、`build.sbt` 和 `project/build.properties`。
3. 复制的是生成工程输入，不是直接重复使用 R2 的现成 SV 文件。
4. 根据对应案例复制一份参数字典，只调整一个待测物理参数。
5. 修改对应的 `GeneratedDesignParams.scala` 声明。
6. 行数、列数和 reuse 在构造器中有独立字面量时，也同步更新对应字段。
7. reuse 还存在 `PhysicalImplementation.configureCrossTokenReuse(...)` 调用。
8. reuse=2 的实验同时将声明、物理配置调用和 `DecoderBlockParams` 字段改为 2。
9. 三处同步是对同一个参数多处绑定的修改，不代表同时调整三个不同设计参数。
10. 复制工程后，SBT 实际调用 `ElaborateGeneratedAccelerator`。
11. 接着调用 `ElaborateGeneratedAxiDdrTop`。
12. 两个入口均生成实际的 SV，而不是只写一份参数文本。
13. SBT 命令限制 JVM 最大堆为 3 GiB。
14. 命令还将 JVM 可见处理器数量限制为 2。
15. 六组展开按顺序进行，避免多个本地重型 JVM 同时占用内存。
16. 若运行前系统可用内存低于 6 GiB，脚本会停止启动后续案例。
17. 已启动案例若低于 4 GiB 可用内存或超过 900 秒，脚本会尝试终止进程组。
18. 本轮六个案例均返回码 0，记录的 termination 字段均为空。
19. 六例观察到的最低可用内存为 15,298,048 KiB，约 14.6 GiB。
20. 这些阈值和耗时是本次执行保护，不是硬件吞吐量或设计性能指标。

### 新增候选的实际执行记录

| 案例 | 参数变化 | 输出 SV 数 | 运行秒数 | 最低可用内存 KiB | 返回码 |
|---|---|---:|---:|---:|---:|
| rows_4 | 16 → 4 | 47 | 31.022 | 16,652,292 | 0 |
| cols_8 | 32 → 8 | 45 | 34.027 | 15,954,020 | 0 |
| cols_4 | 32 → 4 | 45 | 31.020 | 16,663,944 | 0 |
| fifo_32 | 64 → 32 | 47 | 43.024 | 16,000,080 | 0 |
| banks_8 | 2 → 8 | 47 | 43.024 | 15,839,148 | 0 |
| reuse_2 | 1 → 2 | 47 | 44.025 | 15,298,048 | 0 |

1. 上表耗时为脚本记录的本地 SBT 进程墙钟时间。
2. 不能与其他综合或仿真实验的耗时混为一谈。
3. `cols_8`、`cols_4` 输出 45 个 SV 文件，并不与另一些案例的 47 个相同。
4. 文件个数本身不表示设计正确性或可综合性。
5. 已有案例 `rows_8` 的输出数量是 47。
6. 已有案例 `cols_16` 的输出数量是 45。
7. 已有案例 `fifo_128` 的输出数量是 45。
8. 已有案例 `banks_4` 的输出数量是 47。
9. 两个候选的顶层输出数目不同也可能改变文件集合对比的分母。
10. 这正是必须检查文件名集合并集和交集的原因。

### 三个实验分支的构造

1. 完整候选分支使用该候选自己的参数、Scala 绑定和展开输出。
2. 完整候选是待评价一致性的正常工作副本。
3. 参数检查读入候选的预期物理参数。
4. 参数检查也读取候选生成的 Scala 文本。
5. 随后远端工具独立分析该候选的 SV 文件。
6. Stale Stage-5 分支沿用基准的 Scala 和 SV。
7. 同时以该案例变化后的参数作为预期参数。
8. 它模拟上游参数改变但旧生成阶段被冻结的情况。
9. 其预期的不一致由构造方法直接确定。
10. 这个负对照不是一次真实 Agent 意外遗忘更新的自然发生记录。
11. Partial-update 分支沿用完整候选的参数和 Scala。
12. 对候选与基准中一个有变化、两边同名的 SV 文件进行替换。
13. 被替换文件来自基准，其余文件继续来自该候选。
14. 因而分支在字节上形成了受控的新旧 SV 混合包。
15. 实验没有断言每种混合包都会导致运行时功能错误。
16. 检查器无报告也不意味着混合包在功能上安全。
17. 新增案例从符合条件的变化文件中选第一个排序项作为回退文件。
18. 四个历史案例所选回退文件由案例表显式指定。
19. 因此，这不是系统自动寻找最危险文件的测试。
20. 也不能把 10 个相似构造直接推广到全部硬件工程及所有失步类型。

### 检查器实际读取什么

1. 参数检查函数为 `validate_generated_params_source()`。
2. 它先提取候选物理签名。
3. 物理签名包含 lanes、阵列行列、FIFO 深度、activation banks 和 weight bank 配置。
4. 如果输入参数中包含跨 token reuse，也会把该字段加入签名。
5. 对若干整数参数，检查器查找预期的 Scala `val` 文字。
6. 对 `weightBanksByRole`，检查器确认 Map 声明存在。
7. 它检查部分生成配置将 FIFO、activation banks、weight banks 对应字段向下传递。
8. 它还检查行列参数声明或相应可识别的赋值文本。
9. 它并不解析部分回退后的每个 SV 文件来证明硬件与 Scala 参数语义一致。
10. 因而当参数和 Scala 均正确但 SV 混入旧版本时，该检查器可能报告 PASS。
11. 本轮十个 partial 分支正是这种已观测盲区。
12. 十个 stale 分支则因 Scala 里的预期整数声明不匹配而被检测。
13. 对于 weight bank Map，函数的声明存在检查不应被解释成完整数值语义证明。
14. 针对参数来源与 SV 一致性的更全面检查仍需后续设计和验证。
15. 这一问题不能通过把 `vlogan` 返回 0 改写为参数传播正确来解决。

### 各分支汇总结果

| 实验分支 | 参数绑定 PASS | 参数绑定 FAIL | 远端源码分析 PASS |
|---|---:|---:|---:|
| 完整候选 | 10/10 | 0/10 | 10/10 |
| Stale Stage-5 | 0/10 | 10/10 | 10/10 |
| Partial update | 10/10 | 0/10 | 10/10 |

1. stale 的 10/10 表示所构造的十例旧 Scala 绑定均被发现。
2. stale 的 `vlogan` 10/10 只是基准 SV 本身能通过源码分析。
3. partial 的 10/10 是检查器未阻断十例已知混合包。
4. 这不是说十例 partial 的参数传播正确。
5. 也不是说十例 partial 都已证明功能错误。
6. VCS 源码分析和连接展开的检查范围不同。
7. 部分 mixed SV 问题只有连接展开后才产生可见警告。
8. 本轮不把告警升级为强制失败，也不修改 compile-only 通过政策。
9. 研究阶段需要保留告警及其实际判定，以免把 rc=0 描述成无任何问题。
10. 当前对生产系统的影响范围仍需要通过更广泛案例和后续验证判断。

### 十例逐项记录：rows_8

1. 参数是 `compute_array_rows`，从 16 改为 8。
2. 输入来源是历史独立 Stage-5 候选。
3. 对基准观察到 12 个变化 SV、35 个同名同哈希 SV。
4. 完整候选参数绑定检查 PASS，远端 `vlogan` 返回 0。
5. stale 分支参数绑定检查 FAIL，远端 `vlogan` 返回 0。
6. partial 回退的是 `Linear.sv`。
7. partial 在 12 个参考变化文件中，与候选一致 11 个。
8. partial 参数检查仍 PASS，源码分析仍返回 0。
9. 完整候选的顶层展开 rc=0，PCWM-W 告警 0 条。
10. partial 顶层展开 rc=0，但有 6 条 PCWM-W 告警。
11. QKVProjection 到 Linear 的地址表达式宽 14 bit，Linear 端口为 13 bit。
12. 同一连接的数据表达式宽 1024 bit，Linear 数据端口为 2048 bit。
13. Linear 向 WeightTileCache 的写地址表达式 13 bit，端口为 14 bit。
14. 对应写数据表达式 2048 bit，端口为 1024 bit。
15. 读取地址及读取数据连接亦各出现一条宽度告警。
16. 这些告警来自真实的生成顶层连接展开，不是人为指定检查器的预期标签。
17. 展开返回 0 表明当前工具将这类情形按告警处理。
18. 没有运行仿真验证该混合包在输入权重时如何表现。

### 十例逐项记录：cols_16

1. 参数是 `compute_array_cols`，从 32 改为 16。
2. 输入来源是历史独立 Stage-5 候选。
3. 对基准观察到 15 个变化 SV、32 个同名同哈希 SV。
4. 完整候选参数检查 PASS，远端 `vlogan` 返回 0。
5. stale 的参数检查 FAIL，但旧基准源码分析返回 0。
6. partial 回退 `Linear.sv`。
7. 在 15 个参考变化文件中，该 partial 分支与候选一致 14 个。
8. partial 参数检查 PASS，源码分析返回 0。
9. 完整候选顶层展开 rc=0 且无 PCWM-W 告警。
10. partial 顶层展开 rc=0，报告 10 条 PCWM-W 告警。
11. 日志中包括 14→13 bit 地址连接和 1024→2048 bit 数据连接。
12. 同时包括 6→7 bit 地址和 256→128 bit 数据宽度失配。
13. 另有 13→14 bit 地址和 2048→1024 bit 数据宽度失配。
14. 这些观察说明部分连接宽度不一致可以通过展开显现。
15. 这些观察不说明 VCS 返回码会在当前策略下自动变非零。

### 十例逐项记录：fifo_128

1. 参数是 `fifo_depth`，从 64 改为 128。
2. 输入来源是历史独立 Stage-5 候选。
3. 观察到 7 个变化 SV、40 个同名同哈希 SV。
4. 完整候选参数检查 PASS，远端 `vlogan` 返回 0。
5. stale 参数检查 FAIL，远端 `vlogan` 返回 0。
6. partial 回退 `PhysicalStreamFifo.sv`。
7. 七个参考变化文件中 partial 与候选一致 6 个。
8. partial 参数检查 PASS，远端 `vlogan` 返回 0。
9. 完整候选与 partial 的顶层展开返回码均为 0。
10. 两臂均没有观察到 PCWM-W 端口宽度警告。
11. 没有该类告警不等于 FIFO 语义、深度和时序已经验证正确。
12. 变化文件包括若干存储、FIFO 和 `ResidualAdd.sv`。
13. 变化来自哈希比较，没有进一步证明每个文件的特定语义为何变化。

### 十例逐项记录：banks_4

1. 参数是 `activation_banks`，从 2 改为 4。
2. 输入来源是历史独立 Stage-5 候选。
3. 观察到 10 个变化 SV、37 个同名同哈希 SV。
4. 完整候选参数检查 PASS，远端 `vlogan` 返回 0。
5. stale 参数检查 FAIL，远端 `vlogan` 返回 0。
6. partial 回退 `PhysicalSimpleDualPortMemory_12.sv`。
7. 十个参考变化文件中 partial 与候选一致 9 个。
8. partial 参数检查 PASS，远端 `vlogan` 返回 0。
9. 完整候选和 partial 均完成顶层展开，rc=0。
10. 两臂均没有 PCWM-W 警告。
11. 一个 memory 文件的字节变化不能单独推断 bank 数是否在最终运行时实际生效。
12. 没有执行该分支的资源映射或读写正确性测试。

### 十例逐项记录：rows_4

1. 参数是 `compute_array_rows`，从 16 改为 4。
2. 来源为隔离的单参数 Chisel 展开探针。
3. 新展开总耗时约 31.022 秒，返回码为 0。
4. 观察到 12 个变化 SV、35 个同名同哈希 SV。
5. 完整候选绑定检查 PASS、`vlogan` 返回 0。
6. stale 绑定检查 FAIL，但 `vlogan` 返回 0。
7. partial 回退的是排序后的首个合格文件 `DenseFFN.sv`。
8. 变化参考集合中 11/12 与完整候选哈希一致。
9. partial 检查器和源码分析仍通过。
10. 本例未被纳入八次历史候选顶层展开对照。
11. 因此不能为本例填写顶层 PCWM-W 的数量。

### 十例逐项记录：cols_8

1. 参数是 `compute_array_cols`，从 32 改为 8。
2. 来源为隔离的单参数 Chisel 展开探针。
3. 新展开总耗时约 34.027 秒，返回码为 0。
4. 观察到 15 个变化 SV、32 个同名同哈希 SV。
5. 完整候选绑定检查 PASS、`vlogan` 返回 0。
6. stale 绑定检查 FAIL，但 `vlogan` 返回 0。
7. partial 回退 `DenseFFN.sv`。
8. 变化参考集合中 partial 与候选一致 14/15。
9. partial 检查器和源码分析仍通过。
10. 没有对本例报告顶层 VCS 位宽告警统计。
11. 没有通过综合确认这个阵列规模的实际资源消耗。

### 十例逐项记录：cols_4

1. 参数是 `compute_array_cols`，从 32 改为 4。
2. 来源为隔离的单参数 Chisel 展开探针。
3. 新展开总耗时约 31.020 秒，返回码为 0。
4. 观察到 15 个变化 SV、32 个同名同哈希 SV。
5. 完整候选绑定检查 PASS、`vlogan` 返回 0。
6. stale 绑定检查 FAIL，但 `vlogan` 返回 0。
7. partial 回退 `DenseFFN.sv`。
8. 变化参考集合中 partial 与候选一致 14/15。
9. partial 检查器和源码分析仍通过。
10. 本例与 cols_8 的变化文件数量相同不意味着其 SV 内容完全相同。
11. 两例的候选树摘要不同，说明两组输出字节身份不同。

### 十例逐项记录：fifo_32

1. 参数是 `fifo_depth`，从 64 改为 32。
2. 来源为隔离的单参数 Chisel 展开探针。
3. 新展开总耗时约 43.024 秒，返回码为 0。
4. 观察到 4 个变化 SV、43 个同名同哈希 SV。
5. 完整候选绑定检查 PASS、`vlogan` 返回 0。
6. stale 绑定检查 FAIL，但 `vlogan` 返回 0。
7. partial 回退 `PhysicalSimpleDualPortMemory_19.sv`。
8. 变化参考集合中 partial 与候选一致 3/4。
9. partial 检查器和源码分析仍通过。
10. 变化文件还包括 `PhysicalSimpleDualPortMemory_32.sv`。
11. 变化文件还包括 `PhysicalStreamFifo_2.sv` 与 `PhysicalStreamFifo_3.sv`。
12. 它与 FIFO 64→128 的变化集合数量不同，提醒不能假定参数变化影响固定数量文件。

### 十例逐项记录：banks_8

1. 参数是 `activation_banks`，从 2 改为 8。
2. 来源为隔离的单参数 Chisel 展开探针。
3. 新展开总耗时约 43.024 秒，返回码为 0。
4. 观察到 10 个变化 SV、37 个同名同哈希 SV。
5. 完整候选绑定检查 PASS、`vlogan` 返回 0。
6. stale 绑定检查 FAIL，但 `vlogan` 返回 0。
7. partial 回退 `PhysicalSimpleDualPortMemory_12.sv`。
8. 变化参考集合中 partial 与候选一致 9/10。
9. partial 检查器和源码分析仍通过。
10. 变化列表由十个不同后缀的 `PhysicalSimpleDualPortMemory` 文件组成。
11. 文件名后缀是生成结果的模块标识，不能自行当成固定物理 bank 身份。

### 十例逐项记录：reuse_2

1. 参数是 `cross_token_reuse_tokens`，从 1 改为 2。
2. 来源为隔离的单参数 Chisel 展开探针。
3. 新展开总耗时约 44.025 秒，返回码为 0。
4. 观察到 12 个变化 SV、35 个同名同哈希 SV。
5. 完整候选绑定检查 PASS、`vlogan` 返回 0。
6. stale 绑定检查 FAIL，但 `vlogan` 返回 0。
7. partial 回退 `Linear.sv`。
8. 变化参考集合中 partial 与候选一致 11/12。
9. partial 检查器和源码分析仍通过。
10. 变更的候选输出包括多个 Linear、乘加相关模块和若干 memory 模块。
11. 这说明此次参数值变化伴随多文件输出差异。
12. 它不能证明跨 token 权重驻留在真实推理运行中按预期工作。

### 顶层展开的详细工具结果

| 案例与分支 | 墙钟秒数 | PCWM-W 条数 | Error 条数 | 退出码 |
|---|---:|---:|---:|---:|
| rows_8 完整候选 | 22.977 | 0 | 0 | 0 |
| rows_8 partial | 23.127 | 6 | 0 | 0 |
| cols_16 完整候选 | 24.917 | 0 | 0 | 0 |
| cols_16 partial | 25.722 | 10 | 0 | 0 |
| fifo_128 完整候选 | 30.630 | 0 | 0 | 0 |
| fifo_128 partial | 30.339 | 0 | 0 | 0 |
| banks_4 完整候选 | 30.708 | 0 | 0 | 0 |
| banks_4 partial | 30.314 | 0 | 0 | 0 |

1. 时间包含 SSH 和远端展开，不是纯粹工具 CPU 时间。
2. 本地线程池最多同时管理两个远端任务。
3. 每个任务运行前对真实 Vivado XPM memory SV 进行远端源码编译。
4. 指定的顶层是 `GeneratedAcceleratorTop`。
5. 展开成功生成可执行模拟产物并不表示有运行 testbench。
6. 上表只计数特定 `PCWM-W` 模式及 `Error-[` 模式。
7. 日志另有 locale 告警，不能将其混入端口宽度告警数量。
8. 宽度告警为观察到的设计连接问题线索。
9. 同时 rc=0 说明原 compile-only 返回码门限没有判该案例失败。
10. 后续若研究将哪类告警升级为阻断，需要先明确政策并评估误报。
11. 本轮没有为得到负例而把工具警告改写成失败。
12. 未出现 PCWM-W 的两种局部回退可能仍包含其他时序或逻辑失配。
13. 也可能其失配对某些特定运行输入无影响；本轮数据不能区分。
14. 故不宜将 2/4 写成局部硬件故障检测完整召回率。
15. 更不宜将 4/4 返回 0 写成所有局部回退已安全验证。

### 中途失败：XPM 源码缺失

1. 最早尝试对 `rows_8` partial 进行完整顶层展开时，未加载 XPM 模型。
2. 工具日志因此报告 `Error-[URMI] Unresolved modules`。
3. 具体未解析模块包括 `xpm_memory_sdpram`。
4. 多个 memory 实例都会依赖该 XPM 定义。
5. 故这一错误首先说明工具输入闭包不完整。
6. 它不能证明 partial 更新造成了接口问题。
7. 原始失败日志按 `elaborate_without_xpm.log` 保留。
8. 后续将远端 Vivado 2021.1 的 `xpm_memory.sv` 编译进同一工作库。
9. 再次执行指定顶层 VCS 展开。
10. 加入 XPM 后，四个候选及四个 partial 均完成可比展开。
11. 修正的是仿真工具依赖配置，不是修改源文件隐藏问题。
12. 后续仍能观察到 rows 和 cols 局部回退的位宽告警。
13. 这次 setup 失败不计入八次最终可比结果的硬件故障分母。
14. 初始失败应和最终成功以及仍然存在的告警同时报告。

### 为什么图传播准确率仍不能计算

1. 当前 SACG 的 Stage-5 源码证据以整个 `generated_code_package` 为单位注册。
2. Stage-4 中有参数及关联流水节点。
3. 但已有快照没有可遍历且独立确认的「参数 → 必须更新的每个 SV 文件」边。
4. 同样没有独立确认的「参数 → 必须保持不变的每个 SV 文件」完整集合。
5. 因而图本身没有提供可用于这次文件级评估的真值标签。
6. 生成输出的哈希差只能告诉我们两次输出哪些文件字节不同。
7. 它不能单独告诉我们设计上究竟哪些文件必须变化。
8. 变化也可能是生成器命名、格式或其他非语义变化。
9. 某个文件未变化也不能单独证明与参数没有间接依赖。
10. 完整候选与其自身做哈希比对天然全匹配。
11. 以这种自比较计算 100% 不构成独立传播召回率。
12. Partial 的 11/12 或 14/15 是构造性哈希参考计数。
13. 这些比率不是系统自动发现故障的检测率。
14. 因此 Affected-Artifact Sync Recall 当前状态是未测量。
15. Unrelated-Artifact Preservation 的独立图指标当前也是未测量。
16. 对照确实提供了后续评估需要的候选、差异和日志素材。
17. 下一步需要为代表性模型建立事先冻结的、独立可检查的文件依赖真值。
18. 该真值应区分必要变化、允许变化和应当保持稳定三类。
19. 图预测、独立真值和实际工具结果必须按同一版本进行交叉比较。
20. 不应通过事后观察输出再把相同差异同时作为预测和真值。

### 进一步复核与论文使用边界

1. 所有十组的五个被审计字面量与所选参数一致。
2. 行、列和 reuse 的重复字面量也由独立脚本逐项检查。
3. 对源码字面量的检查没有执行 Scala 程序的语义解释。
4. 实验脚本记录每条分支的完整 SV 哈希映射。
5. 记录也包含源文件压缩包摘要和远端工具日志摘要。
6. 四个历史案例的原始路径和六个新展开的路径均能区分。
7. `combined_summary.json` 的完整候选和 partial 分支有独立记录。
8. `elaborations/controls.json` 保留新增案例实际回退文件名。
9. `source_consistency_audit.json` 保留逐 Scala 和 SV 树身份。
10. `vcs_elaboration_summary.json` 保留八个顶层展开的返回码与警告数量。
11. 推荐论文对 10/10 stale 结果明确限定为所构造的 Scala 参数绑定失配。
12. 推荐同时报告 partial 分支的 0/10 检查器阻断结果。
13. 推荐将 6 条与 10 条告警表述为部分案例的编译展开诊断观察。
14. 不要宣称图传播召回、硬件功能正确或所有更新均自动完成。
15. 本实验不提供参数变化后的硬件时钟频率、周期数和能效。
16. 当读者只看本报告时，最重要的结论是：参数文本绑定与生成 RTL 绑定是两个不同检查范围。

### 与 validation3 原计划逐项对照

1. 计划要求不再把一份 R2 的 SV 硬链接当成十个不同候选。
2. 本轮采用四个历史独立候选和六个单参数新增展开，完成该项受控样本构造。
3. 四个历史候选的目录标识分别是 `R1-array-rows-8-reuse1-baseline`、`R2-array-cols-16-reuse1-baseline`、`R3-fifo-128-reuse1-baseline`、`R4-activation-banks-4-reuse1-baseline`。
4. 它们均取自 `method1_seq32_20261029_supplement/reuse1_parameter_propagation/` 下各自的 `ACCORD/run`。
5. 共同基准来自同一 supplement 内 `T7-cross-token-reuse-1/ACCORD/run`。
6. 四个历史分支的不同身份通过逐文件 SHA-256 和参数差异审计。
7. 六个新候选通过实际 SBT/Chisel 展开产生，不是重新指向历史 R2 的输出。
8. 为控制模型和基线一致，本轮十个候选聚焦 Medium seq32 的 T7 cohort。
9. 计划中还提及 Small 或其他序列设置的历史候选，本轮没有把这些跨 cohort 样本合并成同一个十例分母。
10. 计划要求比较每个候选的受影响文件和无关文件。
11. 本轮完成了按输出哈希区分观测变化集合和同名未变化集合。
12. 但尚未获得由现有图独立给出的文件级 `must_update` 与 `unrelated` 真值。
13. 所以严格定义的图传播 Recall 与 Preservation 两项尚未完成测量。
14. 计划要求保留 stale Stage-5 负对照；此项已构造十例并完成检测。
15. 这十例中物化检查发现 10/10，`vlogan` 仍 10/10 返回 0。
16. 计划要求保留 partial-update 负对照；此项已构造十例并执行检查。
17. 计划预期局部失步被编译或物化检查拦截，但本轮十例没有被这两个检查阻断。
18. 对四个历史案例额外做完整生成顶层展开后，只有其中两例出现 PCWM-W 位宽警告。
19. 即便两例出现警告，工具的实际返回码仍为 0。
20. 因而 partial 检测达到计划预期这一项尚未实现，不能把实验构造完成与检测成功混为一谈。
21. 一个完整候选的 observed unchanged 数值，是相对 T7 的同名同哈希数量。
22. 它并未经过独立标签确认，所以不应直接写为无关产物保持率。
23. 所有分支及失败和告警已留存，后续可以在不覆盖产物的前提下重算。
24. 后续是否扩展候选、图数据模型或检查器，应以这些已完成与未完成项分别规划。

## TraceBench v6 全过程及逐案记录

### 本节范围与主要结论

本节记录本轮针对契约失配、生成 RTL 接口故障和图关联修复的实验。
实验基于已有 GPT-2 Medium、序列长度 32 的 R2 设计快照。
这里的结果是受控编译期机制实验，不是重新完成一次完整加速器自动设计。
基线、故障源码、修复源码、工具输出和图状态分别保存。
实验没有覆盖真实模型推理、功能数值、布局布线或上板行为。
`vlogan` 分析通过只说明源码能够被该分析阶段接受。
VCS elaboration 通过还说明所选层级的模块连接能够展开。
这两个结果都不能单独证明数据流、量化、模型算子或输出数值正确。
本节的 v6 指整组 TraceBench 实验版本。
`rtl_v5` 指 v6 内部真实 RTL 子实验的第五次脚本修订。
它不能与历史整组 TraceBench v5 混为一谈。
历史 v5 的源码故障仅用于当前映射逻辑的重新投影。
该重放没有执行新的 VCS 工具运行。
同一类结果也不能把先导试验和其后重复案例相加。

本轮有三类不同证据。
第一类是十条流水线边上的契约元数据失配。
第二类是十个历史编译故障的源码到图节点映射重放。
第三类是十个请求中的九个真实生成 RTL 命名端口故障。
三类实验的输入、故障类型、观察者和可作结论不同。
元数据实验检出 10/10，且报告中的边能投影到预期两个端点。
它不等于对未知故障进行盲式根因推断得到 10/10。
真实 RTL 实验完成 9 例，每例故障时连接展开失败，修复后展开通过。
第十例没有源闭包内现成消费者，记录为未运行。
修复由确定性程序执行，并非 LLM 自主生成。
文件由 VCS 报告指定，图关联限制可授权的工作文件。
它不证明图独立选择了唯一最小修复范围。

### 受控基线与隔离方式

基线是实验目录中的 R2 参数传播实验 run。
其生成源码目录中包含 45 个 SystemVerilog 文件。
故障注入只作用于每个案例各自的工作副本。
图状态也被复制到实验记录中再用于声明修复转换。
原始运行目录和历史实验源码不因注入而被覆盖。
真实 RTL 的每个故障侧和修复侧都重新打包源码。
远端每次调用使用新的 UUID 子目录。
这样可以减少旧源码和旧编译目录意外混入的风险。
远端包、远端解包文件、本地包成员和本地工作文件都保存摘要。
保存日志和摘要的目的在于识别实际接受工具处理的源码。
摘要一致仍只证明身份一致，不证明硬件功能正确。
同时保留故障版本、修复差异和原始工具输出，以便复核。

### 契约元数据实验：实验设计

实验从同一 `pipeline_plan.json` 取前十条流连接。
每次只改变一条边，其他边保持基线内容。
被改字段是 `stream_contract.src_output_bits`。
该字段从 8 改成 16。
该边的 `element_bits` 仍为 8。
该边的消费端输入宽度也没有跟随改变。
因此注入的是结构化流水计划中的生产端宽度不一致。
这不是把生成 RTL 中的实际端口宽度改成 16 位。
该设计的价值在于检验检查器和图投影处理明确边约束的链路。
它的局限在于故障形式固定，而且诊断文本直接包含边 ID 和字段名。
运行的检查函数是生产代码中的 `check_edge_contracts()`。
检查器错误被放入 failure report 的 summary。
预期上游和下游节点单独放入评分 sidecar。
图投影器读取图和报告，而不是用 sidecar 填充输出。
投影器对错误文本中唯一出现的边进行匹配。
当文本同时出现 `src_output_bits` 时，它取这条边的源和目的节点。
目的节点作为主要下游候选。
源节点作为上游候选。
如果没有唯一边或字段条件不满足，就不能据该分支作同样结论。

E01 的原始错误是 `edge.data.block_input.to.stage_00_layer_norm_1.input`。
错误说明 `element_bits=8` 与 `src_output_bits=16` 不一致。
下游投影为 `node.pipeline.stage_00_layer_norm_1`。
上游投影为 `node.pipeline.block_input`。
修复动作把该边的 `src_output_bits` 从 16 写回 8。
记录中的 E01 再检查包含 11 项静态检查，均为 pass。
其远端 `vlogan` 也返回 0。
这次编译读取的是未因该元数据试验变化的源包。
因此它不能验证实际硬件是否实现了新元数据契约。

E02 的下游是第一残差加法节点。
E02 的上游是 block input。
E02 在授权工作副本中把生产端宽度从 16 恢复到 8。
E03 的下游是 self-attention 节点。
E03 的上游是第一层归一化节点。
E03 同样把违规字段从 16 恢复到 8。
E04 的下游是第一残差加法节点。
E04 的上游是 self-attention 节点。
E05 的下游是第二层归一化节点。
E05 的上游是第一残差加法节点。
E06 的下游是第二残差加法节点。
E06 的上游是第一残差加法节点。
E07 的下游是 MLP 全连接节点。
E07 的上游是第二层归一化节点。
E08 的下游是激活节点。
E08 的上游是 MLP 全连接节点。
E09 的下游是 MLP 投影节点。
E09 的上游是激活节点。
E10 的下游是第二残差加法节点。
E10 的上游是 MLP 投影节点。
E04 至 E10 均对各自被检查器识别的字段恢复 16 到 8。
这十条边覆盖主链和残差相关连接，但来自同一设计快照。
它们不是十个不同的模型、硬件架构或故障类别。

### 契约元数据实验：结果与限定

十次注入的检查器状态均为 fail。
十次下游候选均包含评分端记录的目的节点。
十次上游候选均等于评分端记录的源节点。
十次均执行明确工作文件授权。
十次补丁文件都在授权集合内。
十次修复后静态检查均通过。
十次修复后的远端 `vlogan` 均返回 0。
这十次的 transition promotion 均未成功。
失败原因是没有附加新一轮 `stream_plan_check` 和 `data_order_trace_check` 通过证据。
程序只为实际完成的流水计划静态检查附加证据。
没有把历史证据伪造为本次新证据。
也没有为了让 promotion 通过而删除既有要求。
故障检测、元数据修复、源码编译和 transition promotion 是四个不同状态。
前三项成功不能改写最后一项的真实结果。
promotion 失败也不等价于元数据字段没有恢复。
原因是状态晋升依赖更完整的证据集合。
原始记录只支持对该具体受控位宽违约的结果作统计。
不能扩展为所有跨阶段设计参数都已正确传播。
不能扩展为自动发现任意上游硬件设计根因。

十一项 Stage-3 静态检查的实际名称如下。
`operator_order_check` 检查算子顺序。
`semantic_dataflow_contract_check` 检查适配图语义数据流。
`stream_data_edge_mirror_check` 检查流数据边镜像。
`edge_stream_contract_check` 检查边的流契约。
`shape_numeric_contract_check` 检查形状与数值约束。
`branch_join_contract_check` 检查分支与汇合契约。
`buffer_contract_check` 检查缓冲契约。
`liveness_backpressure_check` 执行静态活性和背压相关检查。
`memory_runtime_contract_check` 检查内存运行契约。
`attention_semantics_check` 检查注意力相关参数语义。
`template_binding_static_check` 检查模板绑定。
E01 报告中的静态缓冲项包含 11 个缓冲、允许深度 32 和 64。
其内存契约报告包含 6 个 region 和 512-bit AXI。
其注意力参数显示 Q 头数 16、KV 头数 16、head dimension 64。
其形状数值报告显示 activation 8 bit、accumulator 32 bit。
活性项自己的摘要说明有界 FIFO 提供弹性和背压。
该摘要同时明确没有证明各级延迟相等。
上述都是计划静态检查的结果，不是 RTL 运行轨迹测量。

### 历史故障的模块映射重放

历史 v5 曾保存十个真实 VCS 故障的 SV 和工具日志。
本轮读取这些归档并重新运行现有的源码到图节点投影器。
故障副本的摘要和对应原始产物路径被补入报告。
投影器从故障副本的身份进入原图对应的源码产物。
新的匹配结果中，十个案例的候选集合均包含评分下游节点。
历史记录中的对照覆盖率为 6/10。
本轮重放的覆盖结果为 10/10。
这项比较反映映射覆盖变化。
它不代表新增十次 VCS 运行。
它也不代表十个故障均已找到唯一根因。
共享文件命中多个候选时，包含答案不等于确定唯一答案。
历史故障为语法类试验，不应改称真实跨模块 RTL 参数传播故障。

### 图别名和来源身份的实际实现

图投影器使用节点已有的算子、模板、源码及种类事实。
本轮补充 `IntegerAttention`、`QKVProjection`、`Linear` 和 `ResidualAdd` 等生成模块别名。
实现没有以 GPT-2 的具体节点 ID 编写唯一答案表。
模块归属不唯一时，结果保留多个候选。
例如两个 MLP 级可以共享 `Linear` 生成实现。
两个残差级可以共享 `ResidualAdd` 生成实现。
共享 FIFO 和权重缓存可能关联全部八级流水节点。
因此文件级归属本身无法自动消除实例级歧义。
Activation 在本图中同时存在流水级和模型算子两类表示。
两个节点处于不同抽象层，不应误称两个彼此独立的故障。

投影器接受独立的故障副本时，报告应包含 `fault_copy_path`。
报告还需要声明 `fault_copy_sha256`。
实际读取的故障副本内容摘要必须与声明一致。
报告的 `source_file` 内容也必须与同一故障摘要一致。
这项约束避免报告指向基线文件却声称分析故障内容。
另一个字段 `origin_artifact_path` 用于把副本关联回图中原始产物。
原始路径必须能映射到图中的 artifact。
这两个路径分别回答分析了哪些字节以及这些字节来自哪里。
图快照本身也用其 SHA 与失败报告绑定。
图摘要不匹配时，静态上下文不能继续使用该报告。
这些身份检查只保证引用对应，不能保证诊断推理一定正确。
没有故障副本字段的旧报告仍走兼容路径。

### 精确文件授权和生产流程边界

本轮 benchmark 调用 `SACGStore.declare_transition()`。
转换记录包括动作类型、触及节点、边、约束和修复范围类别。
声明要求触及约束不能为空。
节点、边和约束 ID 都必须能在状态中查到。
`authorize_repair_artifacts()` 针对已声明转换给出文件授权。
转换的修复范围类别必须是 `auto_allowed`。
目标 artifact 必须与该转换触及的节点、边或约束相关。
若 artifact 指向文件，授权目标必须与该文件一致。
若 artifact 指向目录，请求者必须显式列出已有具体文件。
目录内的显式目标仍须实际是文件。
目录外路径被拒绝。
图外 artifact 和无关 artifact 被拒绝。
目录整体通配授权不被该接口接受。
返回结果写入 transition 的 `authorized_repair_scope`。
基准在写入前检查目标属于该集合。
这些检查为受控试验提供了精确路径边界。
但真实 RTL 案例中，请求授权的具体文件由 VCS 错误确定。
图中的代码包关联本身没有从所有文件里自动推导唯一最小补丁文件。
不能把文件范围的确定全部归因于图算法。

生产 `stage_repair_execute.py` 已有自己的 `allowed_exact_files` 等路径检查。
本轮新增图授权接口由 benchmark 直接调用。
现有记录没有证明生产 repair executor 已调用这个新接口。
因此 benchmark 中授权成功不等于生产 Agent 修复已完成图授权接入。
检查代码能被独立调用，也不等于完整生产 transition 已完成。
这些区分对于后续是否需要接线和端到端试验很重要。

`promote()` 首先检查转换状态、禁止范围和可能要求的审批。
随后读取该转换的 required checkers。
它从转换关联的通过证据中收集 checker 名称。
只要缺少某个 required checker 就拒绝晋升。
晋升后状态才会变为 promoted。
该机制与脚本已经写入工作文件是不同的事件。
元数据试验的十个转换都缺两项指定证据。
因此元数据试验没有生产状态 promotion 成功样本。
真实 RTL 先导试验还缺五项代码生成相关 checker 证据。
它们分别是 manifest、compile gate、contract、package static 和 template coverage。
后续真实 RTL 批量脚本并未以 production promotion 成功作为完成条件。
不能从九个编译重验成功推导九个 promotion 成功。

### 真实 RTL 试验：故障构造

批量 runner 请求十个生成模块。
它扫描现有源码中对每个模块的实例化。
存在消费者时，从 named-port 连接中选取实际声明的端口。
优先选名字包含 `bits` 的端口。
注入器给生产者端口和本模块信号引用加故障后缀。
消费者中的原始 named-port 连接维持不变。
模块内部子模块实例的 `.port_name(...)` 标签也应保持原状。
这样故障意图是单一的生产者与消费者端口名称不一致。
脚本保留故障副本和评分 sidecar。
sidecar 记录注入目标、旧名字、新名字、消费者和实例名。
最终修复推断不读取该 sidecar。
测试源均来自同一基线闭包，不能视为九个独立项目。

F1 的请求模块是 `GeneratedAxiDdrTop`。
现有源码闭包中没有模块实例化它作为消费者。
试验没有为了凑样本新造替代 testbench。
F1 因此为 `not_run`。
F1 没有 fault VCS 返回码，也没有 repair VCS 返回码。
它既不是成功，也不是工具发现并修复失败。
最终执行分母为 9，而不是 10。

F2 的生产模块是 `GeneratedAcceleratorTop`。
其现有消费者顶层是 `GeneratedAxiDdrTop`。
故障端口为 `ddrTileRequest_bits_routeId`。
VCS 故障阶段对应的图候选包含 block input 和 block output 两个边界。
故障源码分析返回 0，故障连接展开返回 255。
修复后源码分析和连接展开均返回 0。
fault 和 repair 的 45 个文件身份核对均为真。
修复后的目标文件摘要与基线摘要相同。

F3 的生产模块是 `Attention`。
现有消费者顶层是 `GPT2PreLNBlock`。
故障端口为 `io_in_bits_data`。
图候选为 `node.pipeline.stage_01_self_attention`。
故障阶段 `vlogan=0`，`vcs=255`。
修复阶段 `vlogan=0`，`vcs=0`。
工作源码、上传包成员和远端文件清单一致。
修复后的目标文件与对应基线按摘要一致。
这一案例在该图中只有一个文件归属候选。
它仍是编译器已指出模块的条件下得到的候选。

F4 的生产模块是 `IntegerAttention`。
现有消费者顶层是 `Attention`。
故障端口为 `io_in_bits_data`。
图候选为 self-attention 流水级。
故障阶段源码分析返回 0，连接展开返回 255。
修复阶段两项均返回 0。
故障和修复包的各 45 个源码条目均完成身份核对。
修复文件摘要与基线相同。
这个案例曾暴露 VCS 诊断跨行时的解析缺口。

F5 的生产模块是 `Linear`。
现有消费者顶层是 `QKVProjection`。
故障端口为 `io_weight_bits_addr`。
图投影返回 MLP FC 和 MLP Projection 两个候选。
这是共享实现文件在图中存在多个可能拥有者的表现。
不能把两个候选里的任意一个声称为图已独立识别的唯一根因。
故障阶段源码分析返回 0，连接展开返回 255。
修复阶段源码分析和连接展开均返回 0。
两个源码包的身份核对均成功。
修复后的目标文件摘要与基线相同。

F6 的生产模块是 `Activation`。
现有消费者顶层是 `DenseFFN`。
故障端口为 `io_in_bits_data`。
VCS 的 `UPIMI-E` 日志指出 DenseFFN 中的 Activation 实例端口不存在。
原始日志可见实例名为 `act`。
图投影返回 activation 流水级和 activation 模型算子两个节点。
两个候选是对同一设计概念的不同抽象层表述。
故障阶段源码分析返回 0，连接展开返回 255。
修复后源码分析和连接展开均返回 0。
修复后的目标文件摘要与基线相同。
先导试验也使用 Activation，因此不能再作为独立新增样本相加。

F7 的生产模块是 `ResidualAdd`。
现有消费者顶层是 `GPT2PreLNBlock`。
故障端口为 `io_residual_bits_data`。
图投影返回第一和第二残差两个流水级。
日志中现有设计可以有 `add1` 和 `add2` 两个实例。
因此单靠共享模块文件不能区分实际图实例。
故障阶段源码分析返回 0，连接展开返回 255。
修复阶段源码分析和连接展开均返回 0。
修复文件身份与基线一致。
这一案例在中间版本曾被诊断解析器误归为 unexpected fault。

F8 的生产模块是 `PhysicalStreamFifo`。
现有消费者顶层是 `ResidualAdd`。
故障端口为 `io_enq_bits_data`。
图返回全部八个流水级作为共享资源候选。
这个候选集合覆盖范围很宽。
集合包含相关级不表示图选择了准确的单一发生位置。
故障阶段 `vlogan=0`，`vcs=255`。
修复阶段 `vlogan=0`，`vcs=0`。
故障与修复清单各包含 45 个一致的 SV 文件。
修复文件摘要与基线一致。

F9 的生产模块是 `WeightTileCache`。
现有消费者顶层是 `Linear`。
故障端口为 `io_tileRequest_bits_routeId`。
图返回全部八个流水级候选。
该结果表明共享权重缓存的文件级绑定不能提供实例级唯一定位。
故障阶段源码分析返回 0，连接展开返回 255。
修复阶段源码分析和连接展开均返回 0。
两次源码包身份核对都成功。
修复文件摘要与基线一致。

F10 的生产模块是 `QKVProjection`。
现有消费者顶层是 `GPT2PreLNBlock`。
故障端口为 `io_weight_bits_addr`。
图投影返回 self-attention 流水级。
故障阶段 `vlogan=0`，`vcs=255`。
修复阶段 `vlogan=0`，`vcs=0`。
两次 45 文件源码身份核对成功。
修复文件摘要与基线一致。
其中间版同样暴露跨行 VCS 诊断解析遗漏。

### 真实 RTL 试验：诊断、修复和复验

故障阶段首先用 `vlogan -full64 -sverilog` 分析 XPM 模型和源码。
只有源码分析返回 0 时才继续运行所选消费者的 VCS 展开。
目标是在不同阶段区分词法语法问题与跨模块连接问题。
最终九个案例均表现为源码分析通过、连接展开失败。
其故障日志均有 `Error-[UPIMI-E]`。
该错误表示模块实例中的命名端口未在模块定义中找到。
实际 VCS 错误返回值 255 表示该次展开失败。
SSH 外层返回值为 0 表示远端命令与记录收集完成。
外层返回 0 不等于内部 VCS 返回 0。
这一区分对理解保存结果非常重要。

修复器解析 VCS 给出的端口名、模块名和定义文件。
它也定位日志中的消费者源码和实例名。
诊断文件必须落在本次工作目录内。
其内容必须与远端文件清单中的摘要一致。
随后复制被诊断的故障文件以构造 failure report。
报告保留本地故障副本、原始产物和图快照之间的关系。
图投影器根据报告给出归属候选。
代码包 artifact 在修复状态中指向当前工作副本目录。
benchmark 对编译器指出的目标文件请求精确授权。
补丁目标必须包含在返回集合中才能继续。

`infer_port_repair()` 比较生产者声明端口和消费者实例连接端口。
只有消费者缺失端口集合恰好是工具报告的一个端口时继续。
生产者额外端口集合也必须恰好只有一个元素。
两项条件同时满足时才提出具体名称替换。
消费者实例找不到时不会猜测。
如果多出多个候选端口，也不会猜测。
修复器使用当前故障源码和实际消费者连接。
评分用的注入变量和基线内容不参与补丁选择。
修复后另存 `source_patch.diff`。
然后对修复源码包运行相同的分析与连接展开门限。
最终通过条件包括两侧 SSH 成功和两侧源码绑定成功。
还要求故障侧 `vlogan=0`、`vcs!=0`。
并要求修复侧 `vlogan=0`、`vcs=0`。
九个执行案例满足这些条件。
全部九个修复文件按摘要与原始基线相同。
这一摘要对照在评分阶段进行，不是补丁生成输入。
结果说明本实验中固定类型的单端口重命名可被该规则修复。
结果不能扩展为任意代码变更、多个同时故障或语义错误都可修复。

### 先导试验失败及 XPM 模型问题

最初的 Activation/DenseFFN 先导试验已成功制造端口失配。
故障阶段源码分析返回 0，VCS 展开返回 255。
在执行补丁后，源码分析依然返回 0。
但 VCS 展开仍返回 255。
复验日志报 `Error-[URMI] Unresolved modules`。
缺失模块是 Xilinx 的 `xpm_memory_sdpram`。
出错实例来自 `PhysicalSimpleDualPortMemory` 系列源码。
这属于 VCS 连接展开所需的库模型缺失。
它不能简单归因于 Activation 的定点端口修复失败。
也不能把该次修复后的 VCS 失败忽略为通过。
最初 pilot 的准确状态是 `repair_revalidation_failed`。
引入服务器已有 Vivado 2021.1 XPM memory 模型后重新试验。
新的 pilot 故障侧仍是 `vlogan=0`、`vcs=255`。
修复侧变为 `vlogan=0`、`vcs=0`。
其状态记录为 pass。
两次 pilot 的 transition 都因缺五项代码生成 checker 证据而未 promotion。
最终批量试验使用 XPM 模型，但仍未运行仿真。

### 批量修订过程中保留的失败

首次批量在 F2 期间由于误判本地解析较慢而中断 SSH。
执行记录称远端当时已经完成相应工作。
该次文件保留，用于解释中断而不是算作完整最终批量。
`rtl_v2` 请求 10 案，实际执行 9 案。
九次故障侧 VCS 都失败。
但只有 5 次修复后重验通过。
其中一个问题是直接替换所有匹配 token。
这种替换同时修改了生产模块内部子模块的 named-port 标签。
例如 Attention 试验日志先出现内部 `IntegerAttention` 端口故障。
同一日志还出现外部 GPT2PreLNBlock 与 Attention 的预期失配。
因此一次注入制造了不止一个连接问题。
在 IntegerAttention 案例中也出现内部 `Linear_1` 端口故障。
第一个报告故障不一定是原计划中的消费者连接。
这会干扰定位、授权和确定性单点修复。
修复注入器后，生产者自身信号引用可变化。
子实例 `.port_name` 标签则不随之改名。
focused test 用小型 A/B 模块例子检查这一行为。

`rtl_v3` 修正了子实例标签替换问题。
其九次执行中有 6 次修复复验通过。
F4、F7 和 F10 被记录为 unexpected fault。
检查日志发现 VCS 的诊断文本可能在 `defined` 与 `in` 之间换行。
当时诊断解析对这种排版处理不完整。
因此工具已经报告真实错误，而脚本没有正确提取。
它反映的是日志解析缺口，而非 VCS 没有运行。
当时修复还引用注入变量。
所以不能将 v3 统计为无评分答案泄露的独立修复证明。
后续解析采用允许跨行的正则表达式。
测试显式覆盖 `defined` 换行后跟 `in` 的格式。

`rtl_v4` 修正上述解析并改为从源码和消费者连接推断端口。
其九个实际执行案例均得到通过复验的结果。
但当时仍用注入阶段保留的副本过滤诊断文件。
这可能把注入者知道的目标信息带入诊断选择过程。
同时该版本还缺工具侧完整逐成员绑定。
因此 v4 保留为中间过程，不作为最终无真值过滤结果。

`rtl_v5` 按 VCS 报告路径选择待诊断文件。
随后验证该文件位于当前工作副本并与远端成员摘要相同。
它不再用注入保留副本筛选诊断文件。
它把基线比较留在评分阶段。
它保存 fault/repair tar、各成员摘要、远端摘要和工具日志。
它冻结 runner、helper、图投影器、store、测试及各自摘要。
最终 9/9 指该修订在上述定义下通过的九个执行样本。
九例只覆盖单一类命名端口故障。
中间版的失败结果不应被最终通过率抹掉。
同样，最终成功也不能被说成前几个版本从未失败。

### 身份验证和独立审计的具体含义

每个最终执行案例的故障侧保存 45 个 SV 源文件摘要。
每个案例的修复侧也保存 45 个源码文件摘要。
本地工作文件摘要与本地 tar 成员摘要逐项比较。
本地 tar 成员摘要还与远端解包文件摘要逐项比较。
本地 tar 整包摘要和远端上传包摘要也比较。
日志自身保存 SHA，避免错把其他次日志当成本次结果。
这能增强故障、工具输出和实际处理源码的对应关系。
它没有证明该日志的诊断就是设计的完整因果解释。
它也没有证明功能语义、数值精度或时序目标达成。

记录显示独立子代理核对了九案 tar 成员及副本身份。
同时检查远端清单、子实例端口标签是否保留及相关测试。
F2、F4、F7 还通过 SSH 抽查实际远端文件 SHA。
抽查结果与记录一致。
总审计脚本还检查了各案例授权集合包含补丁文件。
它重新计数已执行数和通过数。
它复核对应 fault/repair 日志摘要及包成员清单。
全部实验合计审计得到 106 项一致性检查通过。
106 不是 TraceBench 的九案数量。
106 也不是 106 项硬件正确性测试。
它覆盖本轮多个子实验的记录身份与算术一致性。

### 测试实际覆盖与遗漏

`test_tracebench_v6_rtl.py` 测试端口注入保留子模块标签。
它还验证基于端口集合的单一匹配恢复。
它测试多余候选不唯一和消费者证据缺失时拒绝猜测。
它测试 VCS 诊断跨行解析。
图上下文测试覆盖故障副本摘要不一致时的拒绝。
也覆盖分析路径内容与故障副本不一致的拒绝。
还覆盖图外来源、共享模块候选和明确报边的投影行为。
授权测试覆盖精确文件、无关 artifact、目录显式文件和目录外路径。
授权测试还覆盖禁止类别不能自动授权。
本轮记录中相关 18 项 focused tests 通过。
这些测试是实现行为的回归证据。
它们不覆盖所有生成 RTL 语法变体和所有复杂 EDA 诊断格式。
测试运行与九次远端 VCS 故障样本不是同一计数口径。

### 当前可用于评估的证据与尚缺内容

可确认检查器会在该组 8/16 位宽元数据不一致时指出具体边。
可确认图上下文能把该明确报告的边投影回两个端点。
可确认图投影可对已报告源码给出多个保守归属候选。
可确认精确文件授权接口对该组受控补丁生效。
可确认九个受控端口错名在现有消费者范围真实触发 VCS 展开失败。
可确认确定性脚本修复后，同样的消费者范围展开通过。
可确认相应源码包与远端工具记录在保存的身份检查中一致。
不可由此声称所有图根因定位任务达到 100% Top-1。
不可由此声称图独立完成了九次未知根因诊断。
不可由此声称生产 LLM Agent 已自主完成九次 RTL 修复。
不可由此声称生产 transition 已完成九次 promotion。
不可由此声称运行时 CCTG 对动态故障的因果定位收益。
不可由此声称九个案例都执行了完整板级顶层仿真。
不可由此声称 RTL 数值功能正确或测得实际吞吐。

如果后续要评估实例级定位，需要保留共享模块的实例路径。
实例路径需要在独立评分前映射到图中具体节点或调用关系。
如果要评估未知根因，诊断输入不能直接携带评分答案。
需要明确工具本身直接指出文件时，图机制提供的新增信息是什么。
如果要评估生产授权，应验证修复执行器调用该接口及拒绝越界。
如果要评估 promotion，应执行并附加实际要求的 checker 证据。
如果实验策略仍是 compile-only，应明确这与生产所需证据的差异。
如果要评估 LLM 修复，应保留提示、工具日志、补丁和拒绝或失败记录。
如果要评估跨阶段设计传播，需要改变真实生成链并独立验证受影响集合。
上述是针对现有缺口的后续设计选项，并非已经完成的实验。

## 配对重验证实验：目的、过程和完整结果

### 本实验试图回答什么问题

本实验评估：当设计产物只有局部变化时，利用输入依赖和证据失效记录选择检查，是否能减少重复编译期检查的耗时。
对照组称为 full，执行本实验预先定义的全部六项编译期检查。
实验组称为 targeted，根据变化文件和显式声明的检查输入依赖选择检查。
每个案例的两组都面对该案例的同一个变异设计快照。
两组不是分别对不同设计进行测时。
最终有效结果来自 `paired_timing_v4_snapshot_audit`。
`paired_timing_v4`、`paired_timing_v4_confirm` 是之前的尝试，保留用于追踪测量方法变化。
`paired_timing_v3` 是更早的对照尝试，存在明确的目录与测量设计问题。
最终实验使用真实框架检查函数、生产重验证 gate 解析器和远端 VCS 的 `vlogan`。
它没有运行完整硬件功能仿真。
它也没有重新运行整个 Stage-1 至 Stage-6 自动设计流程。
它没有测量综合、布局布线或上板。
四个变化均为注释或附加元数据，属于受控的轻量变化。
它们用于观察依赖选择和运行耗时，不是硬件行为故障样本。
因此本实验不能单独证明实际语义故障的检出率。

### 共同基准与隔离方式

所有案例均以同一个 GPT-2 Medium、序列长度 32 的现有参数传播基准 run 为输入。
基准来源为 `method1_seq32_20261029_supplement/reuse1_parameter_propagation/R2-array-cols-16-reuse1-baseline/ACCORD/run`。
这是一份已有设计产物的重验证测量，而不是从自然语言需求重新生成整个设计。
实验 runner 为每个案例创建独立 run 目录。
复制使用硬链接以减少拷贝开销。
修改文件前先解除硬链接，再写入新内容，避免改写共享 inode。
每个案例只追加一个指定的注释或元数据字段。
基准与变异快照中的相关文件分别做 SHA-256 比较。
被跟踪文件在 targeted 执行后和 full 执行后再次计算哈希。
最终记录只有在前后相等且两臂的 `run_dir` 都指向该案例变异快照时，才记为同一快照。
四个最终案例的 `same_mutated_snapshot` 均为 true。
这个判断覆盖 runner 跟踪的文件和传入路径。
不应将其扩大为所有框架外部状态都已完整快照化。

### v3 尝试：记录了什么

v3 共设四个案例：文档、运行配置、算子 RTL、顶层 RTL 的局部变化。
E1 在 `generated/chisel/README.md` 中追加注释。
E2 修改 `generated/chisel/runtime/runtime_config.json` 的 `design_id`。
E3 在 `generated/chisel/Activation.sv` 中追加注释。
E4 在 `generated/chisel/GeneratedAxiDdrTop.sv` 中追加注释。
这些都是可控变化，不能当作四种真实硬件故障。
v3 根据 case adapter 中 tool 的 `consumes` 字段派生 evidence 失效。
其文件匹配依据是 basename 或末两级路径。
这并不是完整的文件内容身份和依赖闭包检查。
匹配成功后，脚本确实调用生产函数 `resolve_revalidation_gates()`。
因此 v3 能说明这个生产 resolver 曾被调用，但不能说明完整失效派生已经可靠。

### v3 的四个原始记录

| v3 案例 | 失效证据数 | resolver 状态 | targeted 用时/s | full 用时/s | full 全部通过 |
| --- | ---: | --- | ---: | ---: | --- |
| E1 文档 | 0 | empty | 0 | 4.455736273 | 否 |
| E2 运行配置 | 2 | blocked | 0.172163243 | 4.451723182 | 否 |
| E3 算子 RTL | 0 | empty | 0 | 4.473242048 | 否 |
| E4 顶层 RTL | 1 | pass | 0.170848759 | 4.437908187 | 否 |

v3 的 full 四个案例均不是全部通过，汇总为 0/4。
full 中 `stage_leaf_static`、`boundary_contract` 和 `multilayer_pipeline` 的状态为 pass。
`single_layer_kernel` 和 `axi_ddr_interface` 的状态为 fail。
远端 `vlogan` 在四个案例中返回 0。
这个 0 表示源码分析成功，不代表完成运行期或板级功能验证。
E1 与 E3 没有选择到 targeted gate，其算术减少值被记为 null。
这不应解释为证明两种变化在所有生产场景均不需要验证。
E2 的两条失效记录分别声明 `case_deadlock_axi_check` 和 `case_runtime_abi_check`。
available gate 集合缺少前者，所以 resolver 标记 blocked。
脚本仍执行了其中的 runtime ABI check，但执行一部分不等于整个解析过程成功。
E2 的 runtime ABI return code 为 1，检查状态 fail。
E4 的 resolver 状态为 pass，表示声明的 gate 可解析到可用集合。
E4 的 runtime ABI check 仍以 return code 1 失败。
resolver pass 和 checker pass 是两个不同条件。

### v3 失败的具体运行期条件

E2 的 runtime ABI 报告列出三个 blocker。
第一，`board_wrapper` 文件缺失或为空。
第二，生成的 runtime 顶层没有暴露要求的 `c0_ddr4_s_axi` 板壳接口前缀。
第三，没有 runtime/board-shell bitstream 产物。
这几个 blocker 是该次报告中的实际证据，不应改写成 VCS 时序失败。
E4 的 runtime ABI 同样未满足板级运行先决条件。
E2 报告也显示 memory layout 与板卡宽度均为 512 bit，alignment 为 64 byte。
报告同时识别到部分生成顶层流接口宽度为 128 bit，且未匹配要求的板壳前缀。
这些观察来自特定 checker 的文本识别与当时快照。
不能仅凭这个检查输出推断整个加速器所有 DDR 接口的实际宽度。
runtime ABI 和板级 runtime 不是本轮最终六项编译期 suite 的组成部分。
将它们排除后获得的 v4 结果，只能用于该重新定义的编译期问题。
不能将 v4 六项全绿表述成 v3 中的板级 runtime blocker 已解决。

### v3 的目录与测量问题

v3 targeted 静态检查收到的是各案例变异后的 `run_dir`。
v3 full 的远端 `vlogan` 使用各案例变异后的 RTL。
但 v3 的五项 full 静态检查调用 `run_check(gate, SOURCE_RUN)`。
这里的 `SOURCE_RUN` 是未变异的原始 run。
因此 full 的静态检查与 targeted 并未严格消费同一个变异快照。
v3 汇总却固定写入 `same_snapshot_for_both_policies=true`。
这个布尔值与实际 full 静态检查传参冲突。
应以脚本实参和实际消费路径为准，而不是直接相信该字段。
该问题属于评测 runner 的实现错误。
它不能直接证明硬件设计错误，也不能证明图方法有效或无效。
v3 的 `targeted_gate_consumes_mutation` 同时接受路径命中或任意 gate pass。
后一个条件并不能证明对应 checker 实际读取了变异文件。
故不能单独依赖该字段计算真实消费率。
E2 和 E4 可从实际 `consumed_paths` 确认传入了目标路径，但最终 checker 均失败。
v3 将 E2、E4 记为约 96.13%、96.15% 的算术减少。
由于 full 未全过、E2 resolver blocked、targeted runtime check 未过且静态两臂目录不同，不能将这两个数作为有效效率结论。
旧记录中还出现过不同轮次的约 95.70%、96.09%。
这些值不应与当前 v3 的 JSON 时间当作同一次测量混用。

### v4 对照边界为何改变

v4 不继续把缺失板级运行条件的检查写成通过。
它重新声明一个明确限定为编译期的 full suite。
它先对基准执行 suite，观察六项是否全部通过。
它再对各变异快照分别运行 targeted 和 full。
这解决的是配对编译期重验证的测量问题。
v4 的六项检查与 v3 的五项分层静态检查不是同一套。
因此 v3 与 v4 的通过率不能直接当作同一个 suite 的前后提升。
v4 也没有以六项通过替代 runtime ABI 检查的结果。
这一区别对论文表格中的验证范围非常重要。

### v4 六项 full gate 的具体定义

第一项是 `constraint_static_check`。
它读取图状态中的 nodes、edges 和 constraints。
它调用 `stage_constraints.validate_constraints()`。
它检查已表示出的约束与图对象的静态一致性。
它不是硬件时序闭合或上板检查。

第二项是 `template_binding_check`。
它调用 `stage_templates.build_selection()`。
它读取图状态和关联的模型、case adapter 信息以检查模板选择。
实际读取审计显示，它还打开共享模板库和共享语义 adapter。
这些共享文件位于案例快照之外。

第三项是 `pipeline_plan_static_check`。
它调用 `stage_pipeline.run_pipeline_static_checks()`。
它用流水线计划和图状态执行静态计划检查。
实验依赖登记把 case adapter 也列入该 gate 的依赖。
实际基准 Python open 审计中，该次调用记录到图状态与计划文件。
登记集合比单次读取审计更保守，不代表此运行中每次都实际打开了登记的每个文件。

第四项是 `dse_materialization_check`。
它调用 `dse_materialization.validate_generated_params_source()`。
它比较 `selected_architecture.json` 的参数与 Scala 源码中的物化结果。
runner 汇总读取生成 Chisel 包中的 Scala 源码文本。
最终基准注册表中有 21 个 Scala 输入文件和一个参数 JSON。
它不是重新运行 DSE，也没有对生成 SV 的行为做独立验证。

第五项是 `package_static_check`。
它调用 `stage_artifacts.build_codegen_package_static_check()`。
它检查 code-generation manifest 和生成包相关静态条件。
manifest 中历史绝对包路径在调用时临时改绑到当前快照中的包目录。
这个重绑定只在内存中进行，没有改写快照 manifest 文件。
实验依赖策略还把所有成员 SV 纳入 package gate 失效范围。
这是保守的失效策略。
实际 package checker 读取 manifest 并检查根目录等条件，并非解析每个 SV 的语义。
因此不能说该 checker 单独检出了 SV 语义变化。

第六项是 `remote_vlogan_compile`。
它把快照中的 SV 打成 tar.gz，上传至远端独立目录。
远端解压后执行 `vlogan -full64 -sverilog *.sv`。
本次基准登记有 45 个 SV 文件。
runner 保存每个 tar 的 SHA-256、远端工作目录、返回码和日志。
返回码为 0 表示该命令成功完成源码分析。
不应将这一项单独称为完整设计的 VCS elaboration、链接或运行仿真。
目标时间计入打包、SSH、上传、远端执行等墙钟成本。
它不是纯工具 CPU 时间。

### 最终版本的基准结果

最终基准 `constraint_static_check`：pass，0.001887 秒。
最终基准 `template_binding_check`：pass，0.015662 秒。
最终基准 `pipeline_plan_static_check`：pass，0.001739 秒。
最终基准 `dse_materialization_check`：pass，0.001132 秒。
最终基准 `package_static_check`：pass，0.012738 秒。
最终基准 `remote_vlogan_compile`：pass，3.688601 秒。
这些用时来自同一轮基准记录，数值保留到微秒级只为反映原始读数。
它们不是对一般设备或网络环境的稳定性能保证。
六项全部通过使后续案例的 full 对照具备本实验规定的基准条件。
基准通过仍只覆盖六项编译期 gate。

### 输入依赖和失效派生如何工作

runner 显式列出每个 gate 对哪些快照文件类别敏感。
constraint gate 依赖图状态文件 `predecessor/sacg_state.json`。
template gate 依赖图状态、`input/model_config.json` 和 `input/case_adapter.json`。
pipeline gate 依赖图状态、`pipeline_planning/pipeline_plan.json` 和 case adapter。
DSE materialization gate 依赖已选架构 JSON 与 Scala 文件集合。
package gate 依赖 code-generation manifest 和 SV 文件集合。
远端 `vlogan` gate 依赖 SV 文件集合。
实验额外跟踪四种案例将要变异的路径。
基准和当前快照中每个受跟踪路径有文件时计算 SHA-256。
缺失文件记为 `None`，使新增和删除也能被识别。
只有前后哈希不同的路径才进入 `changed_paths`。
变化路径与 gate 依赖集合取交集，生成 `invalidated_evidence`。
每条失效记录携带 evidence ID、provider gate、文件路径和前后 SHA-256。
失效记录传给生产 `resolve_revalidation_gates()`。
resolver 返回 selected gate、状态和不可用 gate 等信息。
最终结果按固定 gate 顺序执行 resolver 选择的 gate。
该依赖清单由实验显式构造。
本实验没有证明生产框架已经自动推导所有文件和 gate 的完整依赖闭包。

### 文件增删问题与修正

初始思路只按现有快照 glob 生成 Scala、SV 文件依赖集合，存在新增或删除成员漏算风险。
最终 `changed_dependencies()` 同时枚举 baseline 和 current。
对应 gate 的依赖集合采用两边集合的并集。
随后对并集中的路径分别计算 before 和 after。
新增文件的 before 为 `None`，after 是文件哈希。
删除文件的 before 是文件哈希，after 为 `None`。
该机制使新增或删除也进入失效派生。
测试对 `.sv` 的增加和删除均验证 package 与 remote vlogan 被选中。
测试对 `.scala` 的增加和删除均验证 DSE materialization 被选中。
这些是测试目录中的受控回归，不是额外硬件运行实验。

### 路径重绑定问题与修正

历史图中的 model config 和 case adapter artifact 可包含原始 run 的绝对路径。
如果只复制目录而继续沿用原路径，checker 即使收到快照目录也可能读取原 run。
最终 runner 的 `snapshot_state()` 在内存中读取图状态。
它将 `artifact.input.model_config` 重绑定为当前快照的 `input/model_config.json`。
它将 `artifact.input.case_adapter` 重绑定为当前快照的 `input/case_adapter.json`。
若图中缺少这两个 artifact，函数抛出异常而不是静默继续。
重绑定后的 state 被传入 template 和 pipeline checker。
原始图文件本身不被 `snapshot_state()` 改写。
回归测试构造指向原目录的两条 artifact 记录。
它确认 template checker 实际收到的是当前快照路径。
它同时确认图文件磁盘内容没有被改变。
该测试使用 mock checker，验证传参和不改写；它不是完整模板选择的端到端证明。

### 外部读取审计的发现

最终 runner 之外保存了一份实际静态读取审计。
审计方法为在真实生产 checker 调用期间记录 Python open audit events。
报告输出目录从该读取集里排除。
constraint gate 在该次基准调用中记录到快照内图状态。
template gate 记录到快照内图状态、模型配置与 case adapter。
template gate 还读取框架共享语义 adapter 和共享 Chisel 模板文件。
pipeline gate 在该次审计记录到快照内图状态与 pipeline plan。
DSE gate 记录到快照内已选架构 JSON 和全部 21 个 Scala 文件。
package gate 的内容读取审计只记录到 code-generation manifest。
这些观察是该次执行路径中被记录的 Python 文件打开事件。
它不能自动覆盖所有潜在分支、原生库内部读取或未来新增的依赖。
远端 vlogan 的输入由打包文件清单记录，不属于上述五个 Python gate 的 open 事件。

### 外部共享输入的一致性

共享语义 adapter 位于 `accagent/framework/case_adapters/gpt2_transformer_block.json`。
其实验前后的 SHA-256 都是 `469a5a535d1554fae6b8b0ffa15c37bab91274c744a2d7106a820518054e04a2`。
实验对共享模板目录中的 19 个文件计算了前后哈希。
最终报告 `shared_template_files_unchanged=true`。
共享 adapter 的最终 `unchanged` 也为 true。
如果两者发生变化，runner 将各案例的 reduction 设为 null。
这一做法确认该轮前后观察的外部内容未变。
它没有将外部模板和 adapter 真正复制到每个案例快照中。
因此该实验仍不是完全自包含、对所有外部环境变化免疫的快照设计。

### 四个案例的变异与 SHA-256

E1 变更路径为 `generated/chisel/README.md`。
E1 追加 HTML 注释，不改变硬件实现。
E1 before 为 `6f231ff58af8d0536c6c4210caa63285d277f9e3b2bfd478aa9e759bb300076d`。
E1 after 为 `9052c11124053c2874f7e8ad21ffe9071bde264944cab650677acf5d7ed9ccee`。

E2 变更路径为 `pipeline_planning/pipeline_plan.json`。
E2 添加 `paired_timing_metadata_note` 字段并重新格式化 JSON。
E2 before 为 `cda903378c829389ca8c248af8c278696d8b46f68669e085e33dedfc57206a3e`。
E2 after 为 `5fed5331b2ce6fdc3bb1a441a724b903e1e28190a6df771af5d94a7765a7c0ae`。
该变化不是修改 pipeline 的真实算子连接或计算语义。

E3 变更路径为 `generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala`。
E3 追加 Scala 注释，原参数数值并未被更改。
E3 before 为 `cc33df4cf89c6ade9d6f890df9fab202638f47350ba82e21bd1cb382a7d0e166`。
E3 after 为 `2250e7d1c8af50af09ea33fb8a1516b7c3b56d60bfb31ef9ec5ccba950f29728`。
该案例测量参数源码文件变化如何触发物化检查，不能证明参数数值错误均能被检出。

E4 变更路径为 `generated/chisel/Activation.sv`。
E4 追加 SystemVerilog 注释，不改变算子行为。
E4 before 为 `6056e2dbab309a0096aa3d94f7bed3553d113079816a37db8c6268ee3028704d`。
E4 after 为 `7016d80cb95efa2ad1e456b5c004dbea9a197589eb572ca51ae43e04c9135cfa`。
该案例既触发 package gate，也触发远端源码分析。

### 最终四案例的 gate 选择

E1 的 changed path 有一项，但没有命中六项 gate 的依赖清单。
因此失效证据列表为空，resolver 状态为 `empty`。
E1 targeted 没有执行六项中的任何 gate。
E1 full 仍实际执行了所有六项，均通过。
空集合只针对本实验明确登记的这些编译期检查。
它不意味着所有 README 变化、所有生产工具或所有设计修改都可以跳过验证。

E2 的变化命中 `pipeline_plan_static_check`。
它形成一条针对 pipeline plan 的失效记录。
resolver 状态为 pass，targeted 只执行 pipeline plan 静态检查。
该检查通过。
同一快照上 full 的六项均通过。

E3 的变化命中 `dse_materialization_check`。
它形成一条针对参数 Scala 文件的失效记录。
resolver 状态为 pass，targeted 只执行物化检查。
该检查通过。
同一快照上 full 的六项均通过。

E4 的变化命中 `package_static_check` 与 `remote_vlogan_compile`。
它形成两条 provider gate 不同、指向同一 SV 的失效记录。
resolver 状态为 pass。
targeted 顺序执行 package 和远端 vlogan，两项均通过。
同一快照上 full 的六项也均通过。
package 对 SV 的失效是显式保守策略，并非该 checker 做了 SV 语义分析。

### 最终四案例的实际计时

| 案例 | targeted gate 时间/s | hash + resolver/s | targeted 合计/s | full 六项合计/s | 算术减少 |
| --- | ---: | ---: | ---: | ---: | ---: |
| E1 文档注释 | 0 | 0.021622909 | 0.021622909 | 3.673169110 | 99.4113% |
| E2 pipeline 元数据 | 0.002506629 | 0.021830767 | 0.024337396 | 3.709217985 | 99.3439% |
| E3 Scala 注释 | 0.000991812 | 0.022665413 | 0.023657225 | 3.702814499 | 99.3611% |
| E4 RTL 注释 | 3.697974183 | 0.022478245 | 3.720452428 | 3.762014803 | 1.1048% |

计算公式为 `1 - targeted 合计 / full 六项合计`。
targeted 合计包括 gate 执行时间、哈希比较和 resolver 时间。
full 时间是六个 gate 的墙钟时间相加。
runner 未将快照构建、预存基准哈希计算计入 targeted。
故该数值不是全生命周期缓存和重验证成本。
运行顺序为每个案例先 targeted、再 full，不是随机交叉次序。
每个案例是一次配对读数，未给出重复次数分布或置信区间。
远端网络、SSH、磁盘缓存与服务器负载会影响数值。
表格的高减少主要来自前三个轻量变化没有触发约 3.6 至 3.7 秒的远端分析。
E4 必须运行远端 vlogan，故节省约 1.10%。
在其他网络负载下，这种小差异可能被计时噪声覆盖。

### 最终 full 各 gate 原始分解

| gate | E1/s | E2/s | E3/s | E4/s |
| --- | ---: | ---: | ---: | ---: |
| constraint | 0.001719 | 0.001236 | 0.001901 | 0.002391 |
| template binding | 0.015187 | 0.014636 | 0.014532 | 0.017577 |
| pipeline plan | 0.003636 | 0.001812 | 0.001795 | 0.002372 |
| DSE materialization | 0.000847 | 0.000765 | 0.000730 | 0.001033 |
| package static | 0.010641 | 0.008172 | 0.007074 | 0.005824 |
| remote vlogan | 3.641139 | 3.682598 | 3.676784 | 3.732818 |

表中各值来自各案例的 full 臂，均为 pass。
targeted E2 的 pipeline gate 用时 0.002506629 秒。
targeted E3 的 DSE gate 用时 0.000991812 秒。
targeted E4 的 package gate 用时 0.005237351 秒。
targeted E4 的远端 vlogan 用时 3.692736832 秒。
E1 targeted gate 时间为 0，但还发生了 0.021622909 秒哈希和 resolver 开销。
因此 E1 不是零成本，也不应报告为 100% 时间节省。
E4 targeted vlogan 日志记录工具源码分析 CPU 时间约 1.947 秒。
该 CPU 时间与包括网络和其他开销的约 3.693 秒 targeted 墙钟不是同一个量。
日志中出现 locale 警告，但该次工具返回码为 0。
警告本身不等价于编译失败，也不是性能提升来源。

### 初版、confirm 和最终 audit 的差异

v4 初版的四案例 full 均通过，targeted 选集与最终版本相同。
初版没有把 hash 与 resolver 开销加入 `targeted` 计时。
因此 E1 当时被算成 100.00%，E2 约 99.88%，E3 约 99.98%。
E4 初版约 1.18%。
这些初版数值不应取代最终计入 planning 开销的审计版本。

confirm 版本补充 hash 与 resolver 的时间。
confirm 的 E1 targeted 合计为 0.011077910 秒，full 为 3.803465575 秒。
confirm 的 E2 targeted 合计为 0.012377997 秒，full 为 3.777333432 秒。
confirm 的 E3 targeted 合计为 0.011396005 秒，full 为 3.787167773 秒。
confirm 的 E4 targeted 合计为 3.705924485 秒，full 为 3.754121706 秒。
对应减少分别约为 99.7087%、99.6723%、99.6991%、1.2838%。
这些是另一轮测量，不与最终 snapshot audit 的具体时间合并成一次。
最终 snapshot audit 增加旧、新依赖集合并集处理，并显式核对共享 adapter。
最终版本也有实际 open 审计和新增/删除回归。
因此统一以 snapshot audit 结果作为本轮最终数字。
三轮结果趋势相似不能代替受控重复统计分析。

### 本轮检查和产物一致性

最终 runner 在已有结果目录存在时拒绝覆盖。
它将自身副本保存为 `runner_source.py`。
该副本 SHA-256 为 `491a28fe12b8de692bbc7b9e402cc7a1b8d4c03edab0e811b704feb7f9010096`。
`summary.json` 保存每个案例变化路径、前后哈希、失效记录、gate 选择及用时。
每个 full 和必要的 targeted 目录保存 package 报告或 vlogan 日志与源码包。
记录一致性审计复查了变异字节、gate 选择和计时算术。
整轮 validation3 的一致性审计共 106 项通过。
这 106 项是多组实验记录核对，不是 106 项独立硬件功能测试。
配对 runner 的回归测试执行了两个 unittest 方法。
它们覆盖文件新增/删除失效和输入路径重绑定。
两项均通过，进程返回码为 0。
回归日志显示总运行时间 0.022 秒。
这些测试不能覆盖所有可能的框架依赖与工具副作用。

### 已经证明与尚未证明的区别

现有记录支持：对四个受控变更，显式登记的依赖规则可选择对应 gate。
现有记录支持：最终结果的两臂对同一案例快照运行，并确认跟踪文件在两臂执行中未改变。
现有记录支持：基准和各案例的六项编译期 full 对照通过。
现有记录支持：轻量变更不触发远端源码分析时，所选检查在该次测量中耗时明显更短。
现有记录支持：SV 注释变更触发远端分析时，节省很小。
现有记录支持：新增/删除文件在受控测试中可通过集合并集触发预期 gate。

现有记录没有证明完整生产系统自动识别了所有依赖。
现有记录没有证明针对真实语义变更的 targeted 与 full 拥有相同故障检出率。
现有记录没有覆盖多种模型、板卡、修改大小和工具负载。
现有记录没有证明端到端 Agent 流程加速了 99%。
现有记录没有证明完整 runtime、板级仿真或实际部署获得相同加速。
现有记录没有修复或验证 v3 暴露的 board wrapper、board-shell interface 和 bitstream 缺失问题。
现有记录没有为 1.10% 的差异提供统计显著性。
计划中的“编译期重验证开销”与完整功能验证是不同测量范围。

### 下一步评估可直接使用的判断

若论文只呈现当前数据，应明确写成“显式依赖清单下的编译期局部重验证微基准”。
表格应同时报告 targeted 选择的 gate、full 的六项组成和纳入的 planning 开销。
E1 空 selected set 需要明示为该实验清单下未触发 gate，而不是无条件证明不需要任何验证。
应同时呈现 E4 的约 1.10%，展示实际必须重新分析 RTL 时开销仍然存在。
应注明案例均为单次注释或元数据修改。
若要主张故障检测等价，应在将来的实验中注入具有实际语义影响的合法与非法变更，并比较两臂结果。
若要主张生产泛化，应让系统记录真实 checker 的输入依赖，包含外部模板、工具版本及配置，并验证新增删除和未知依赖策略。
若要估计稳定效益，应重复运行、交替或随机化两臂顺序，并报告负载与分布。
若要覆盖完整开发成本，应把快照准备、初次哈希和缓存维护纳入单独统计。
若要支持更强的完整流程结论，还需要记录真实 Agent 循环中的证据失效、实际执行重验证和最终结果。

## Validation4：下一轮机制验证补充记录（2026-11-01）

### 本节目的与实验边界

本节将 `accagent/docs/core_method_validation_end.md` 计划的 validation4 实际执行经过并入本报告。
从本节开始，本文件同时包含 validation3 与 validation4 的完整已知实验状态。
此前的 validation3 结果仍按原有章节保留。
validation4 没有覆盖或替换 validation3 原始记录。
本节中的结果均对应单独的 `core_method_validation_20261031` 实验目录。
所有历史日志、首轮失败输出、runner 副本、逐例 JSON 和哈希记录均保留。

validation4 的目标是补充三项证据。
第一项是跨 Stage 4/5 的 SV 产物集合指纹和参数族文件变化预测。
第二项是使用消费者/实例上下文细化共享模块故障的图候选，并对真实 transition 调用 promote。
第三项是将生成顶层 VCS elaboration 纳入完整配对门限，重新测局部 RTL 修改的耗时差。

计划文件中对性能数字和闭环比例的预测只作为待验证假设。
实验没有为了达到计划数字而更改计分规则。
所有实际缺失项、候选歧义和未达到的节省比例都保留在结果中。

本轮工作使用 GPT-2 Medium 24 层、序列长度 32、W4A8、VU9P 的 R2 基准实验快照。
PropBench 复用了 validation3 留存的十份独立生成源码树。
TraceBench 复用了同一基准 run 的图、pipeline plan、Scala 和生成 RTL。
Paired Timing 复用了相同的生成 package 与适配器输入。

没有重新启动 SBT。
没有重新生成 Chisel。
没有改变任何加速器硬件设计源文件。
没有运行完整数值仿真。
没有运行 Vivado 综合、布局布线或上板。
VCS 结果全部属于源码编译或 elaboration。
本轮的 promotion 是隔离实验 SACG 状态的 promotion。
它不是生产任务状态被晋升的证明。

远端 VCS 服务器为 `hyyuan@10.12.133.23`。
本地仅负责 Python 机制代码、结果分析、日志管理和少量静态测试。
远端 VCS 执行按 case 分目录串行开展。
没有因为计划时间紧而增加并发仿真进程。

### 结果文件与定位信息

PropBench v5 的汇总为 `propbench_v5/summary.json`。
每个案例的局部记录为 `propbench_v5/<case>/result.json`。
每个案例的 manifest 位于同一目录的 `stage5_sv_manifest.json`。
每个案例的独立依赖图副本为 `sacg_module_dependency_state.json`。
冻结的参数族规则为 `propbench_v5/frozen_dependency_rules.json`。

PropBench 首次尝试保存在 `propbench_v5_setup_attempt_1/`。
正式重试记录为 `propbench_v5_execution_final.log`。
早期日志 `propbench_v5_execution.log` 保留，不用它替代正式 summary。

TraceBench metadata 汇总为 `tracebench_v7_metadata/summary.json`。
metadata 逐案进度为 `tracebench_v7_metadata/progress.json`。
每个 case 的实际 promotion 证据列表在 `tracebench_v7_metadata/E01..E10/promotion_result.json`。
每个 case 同时保存 fault plan、fault checker 输出、静态故障上下文、修复后 plan、远端 vlogan 日志和逐例结果。
历史模块映射复放位于 `tracebench_v7_metadata/module_mapping/`。

TraceBench RTL 汇总为 `tracebench_v7_rtl/summary.json`。
完整的十个 case 分别位于 `tracebench_v7_rtl/F1_...` 至 `F10_...`。
逐案 VCS fault 与 repair 原始输出分别保存在 `fault.log` 和 `repair.log`。
失败报告绑定了 compiler log SHA、生成源 SHA、诊断文件 SHA、远端上传包 SHA 和图快照 SHA。
源码 patch 逐例保存在 `source_patch.diff`。
工具输出到图投影的中间结果保存在 `static_failure_context.json`。

Paired Timing v5 的汇总为 `paired_timing_v5/summary.json`。
部分进度为 `paired_timing_v5/partial_results.json`。
两个实验臂各自保存 gate 运行结果。
完整顶层和 DenseFFN 的远端 VCS 日志位于对应的 gate 目录。
runner 副本为 `paired_timing_v5/runner_source.py`。

独立一致性核对脚本是 `audit_validation4_results.py`。
最终的审计记录是 `validation4_integrity_audit.json`。
本节之后的审计计数使用修正后的审计器运行结果。

### 方法实现：Stage-5 SV manifest

在 `accagent/framework/dse_materialization.py` 中新增了 Stage-5 SV manifest builder。
该 manifest 包含 schema 版本 `spatialaccagent.stage5_sv_manifest.v1`。
它记录 Stage-4 物理参数签名。
它记录参数签名的 SHA-256。
它记录生成目录顶层 `.sv` 文件名到 SHA-256 的映射。
它记录 `.sv` 文件数量。
它记录每个生成模块的端口指纹。
它记录 `GeneratedDesignParams.scala` 的相对路径和 SHA-256。

参数签名覆盖 lanes。
参数签名覆盖 compute array rows。
参数签名覆盖 compute array columns。
参数签名覆盖 FIFO depth。
参数签名覆盖 activation banks。
参数签名覆盖 weight banks by role。
候选包含 cross-token reuse 时，也纳入 reuse 值。

端口指纹抽取当前生成源码中 flat ANSI module header。
端口指纹保存模块名。
端口指纹保存端口名。
端口指纹保存方向。
端口指纹保存原始 packed range 表达式。
继承的方向和 packed range 会传播到后续端口声明。
注释在解析前被剔除。

这个解析器只面向本项目当前 CIRCT 生成的平面 ANSI 风格 RTL。
它不是标准完整 Verilog/SystemVerilog parser。
它不能替代 VCS 对类型、连接和 elaboration 的判断。
它不能证明两个不同 hash 的 RTL 在功能上不等价。
它也不能证明两个 hash 相同的源码对应某一个目标参数的语义正确性。

manifest validator 核对当前参数签名与调用方给定 Stage-4 参数。
validator 核对 `.sv` 成员集合是否有新增文件。
validator 核对 `.sv` 成员集合是否有删除文件。
validator 核对每个同名源文件的字节 SHA。
validator 核对记录的文件数量。
validator 核对 `GeneratedDesignParams.scala` 是否存在于生成目录内。
validator 核对该 Scala 参数源的 SHA。
validator 核对模块端口指纹。
文件缺失、新增、被替换或端口签名变化都会产生失败状态。

在 `accagent/framework/stage_artifacts.py` 中，成功的 Stage-5 compile gate 且启用 elaboration 时才生成清单。
manifest 写入生成 package 的 `stage5_sv_manifest.json`。
清单内容也被嵌入外层 code generation manifest。
若 compile 未通过或 elaboration 未启用，本次路径不生成这份 Stage-5 elaborated-source manifest。
这种条件避免把未完成的展开包装成可验证的展开树。

codegen package static checker 使用 `manifest.generated_top.params` 作为预期参数。
这一参数来源与 `stage5_sv_manifest.parameter_signature` 分开读取。
核验逻辑不会再用 manifest 自身的参数字段作为自己的预期值。
这修复了早期实现中可能出现的循环自证问题。

需要区分生产机制与本轮回放。
生产 Stage-5 成功路径可以在生成当时保存 manifest。
PropBench v5 的历史树没有在原始生成时保存该文件。
因此 runner 从已保存的历史源码树回溯捕获 manifest。
候选身份通过与 PropBench v4 SHA map 精确比较来确认。
manifest 捕获时点晚于原始 Chisel 执行。
后续 partial rollback 是相对于这次捕获的 manifest。
所以本轮实验可以证明“绑定清单存在时能检测回滚”。
本轮不能证明历史 run 当时已经有该保护。
也不能单凭该 replay 证明任意运行过程中都能阻止 manifest 与代码一起被错误更新。

### 方法实现：参数到模块族依赖规则

规则集合在实验开始时从 `PARAMETER_MODULE_FAMILIES` 写入独立的 JSON 文件。
runner 在逐个比较候选输出之前冻结规则文件。
依赖规则不读取被测候选的实际 hash 来决定预测受影响模块。
候选 hash 只在规则冻结之后用于观测文件变化。
该隔离减少根据结果倒推规则的直接风险。

`compute_array_rows` 预测 Linear 模块族受影响。
该规则也预测 QKVProjection 模块族受影响。
该规则也预测 DenseFFN 模块族受影响。
该规则也预测 PhysicalLinear 模块族受影响。
该规则也预测 WeightTileCache 模块族受影响。

`compute_array_cols` 使用相同的声明模块族。
`fifo_depth` 预测 PhysicalStreamFifo 模块族受影响。
`fifo_depth` 也预测 PhysicalSimpleDualPortMemory 模块族受影响。
`activation_banks` 预测 PhysicalSimpleDualPortMemory 模块族受影响。
`cross_token_reuse_tokens` 预测 Linear 模块族受影响。
`cross_token_reuse_tokens` 预测 WeightTileCache 模块族受影响。
`cross_token_reuse_tokens` 预测 PhysicalLinear 模块族受影响。

模块实例文件通过文件 stem 的前缀规则落入模块族。
例如 `PhysicalSimpleDualPortMemory_12.sv` 匹配 `PhysicalSimpleDualPortMemory`。
同理，`WeightTileCache_2.sv` 匹配 `WeightTileCache`。
规则输出显式的 parameter-to-module edges。
每组候选还保存预测 affected 文件集合。
每组候选还保存预测 unrelated 文件集合。

这些边是实验的先验规则，不代表它们已经存在于生产 SACG 自动构图流程。
每个 case 的 `sacg_module_dependency_state.json` 是隔离实验图。
它把参数节点、生成模块节点和声明边写入副本。
没有将这些十组实验图回写到历史 production run 的 SACG 状态。
也没有把实验中观察到的变更文件自动反向加入规则。

Recall 的分母是实际字节变化文件数。
Recall 的分子是实际变化且命中预测 affected set 的文件数。
Preservation 的分母是规则预测 unrelated 的文件数。
Preservation 的分子是预测 unrelated 且相对 baseline 字节不变的文件数。
计分比较候选和 baseline 的整文件 SHA。
它不是基于 AST 语义差分。
它不是基于模块行为等价检查。
它不是参数传播到 Chisel 参数字段的 checker pass rate。

### PropBench v5 执行经过和第一轮失败

正式 runner 为 `run_propbench_v5.py`。
runner 先检查输出目录，存在时拒绝覆盖。
runner 保存自身源代码副本。
runner 保存冻结的依赖规则。
runner 读取 v4 汇总以及十份候选独立树。
每棵树都先与 v4 的 candidate hash map 对照。
如果树的 hash map 不一致，runner 会停止而不是继续统计。

第一轮运行未完成十组。
第一轮运行最多生成了前四组输出。
失败原因是 runner 假定每个旧结果都存在同名 partial reference 字段。
新生成的六组记录使用了另一个 observed-reference 字段名。
这属于实验 runner 对历史 schema 差异处理不完整。
它不是 Chisel 生成失败。
它不是参数物化检查器失败。
它也不是远端 VCS 故障。

第一轮控制树只复制 `.sv`，没有同步复制绑定的 `GeneratedDesignParams.scala`。
这使该首轮输出不能作为最终 partial rollback 构造。
首轮输出整体移入 `propbench_v5_setup_attempt_1/`。
首轮输出没有删除或覆盖。

第二轮修正用 SHA map 比较得到 partial 分支发生回退的唯一源文件。
runner 对每个候选检查恰有一个回退文件。
runner 将该候选自己的 `GeneratedDesignParams.scala` 一并复制到 partial 工作树。
随后将唯一变化的 `.sv` 用 baseline 同名文件替换。
校验器用原候选清单检查 partial 工作树。
此构造避免“少复制 Scala”成为另一个意外变量。

第一轮失败期间没有启动 SBT 或远端 Chisel。
修正后的第二轮也没有启动 SBT 或远端 Chisel。
两轮都只使用之前验证过的生成树。
正式第二轮最终写出十个 case 结果。
正式第二轮的末行计数为 n=10、candidate manifest pass=10、partial manifest detected=10。

### PropBench v5 十组候选逐例记录

本表中的尺寸变化取自每一行的参数对象。
候选名取自 v4 独立候选命名。
改变的参数以相对基线的非默认项为准。
实际变化文件数量取自独立 tree hash 对比。
规则 recall 和 preservation 取自 frozen rule 的交叉核对。
partial revert 文件取自从 candidate/partial hash 差分得到的唯一文件。

| 候选 | 关键物理参数 | 实际变化文件数 | family rule recall | unrelated preservation | 回退文件 |
| --- | --- | ---: | ---: | ---: | --- |
| rows_8 | rows=8, cols=32, FIFO=64, banks=2, reuse=1 | 12 | 0.667 | 0.889 | Linear.sv |
| cols_16 | rows=16, cols=16, FIFO=64, banks=2, reuse=1 | 15 | 0.533 | 0.806 | Linear.sv |
| fifo_128 | rows=16, cols=32, FIFO=128, banks=2, reuse=1 | 7 | 0.857 | 0.955 | PhysicalStreamFifo.sv |
| banks_4 | rows=16, cols=32, FIFO=64, banks=4, reuse=1 | 10 | 1.000 | 1.000 | PhysicalSimpleDualPortMemory_12.sv |
| rows_4 | rows=4, cols=32, FIFO=64, banks=2, reuse=1 | 12 | 0.667 | 0.889 | DenseFFN.sv |
| cols_8 | rows=16, cols=8, FIFO=64, banks=2, reuse=1 | 15 | 0.533 | 0.806 | DenseFFN.sv |
| cols_4 | rows=16, cols=4, FIFO=64, banks=2, reuse=1 | 15 | 0.533 | 0.806 | DenseFFN.sv |
| fifo_32 | rows=16, cols=32, FIFO=32, banks=2, reuse=1 | 4 | 1.000 | 1.000 | PhysicalSimpleDualPortMemory_19.sv |
| banks_8 | rows=16, cols=32, FIFO=64, banks=8, reuse=1 | 10 | 1.000 | 1.000 | PhysicalSimpleDualPortMemory_12.sv |
| reuse_2 | rows=16, cols=32, FIFO=64, banks=2, reuse=2 | 12 | 0.500 | 0.842 | Linear.sv |

`rows_8` 实际变化 12 个 `.sv` 文件。
其中预测的 Linear、QKV、DenseFFN、PhysicalLinear 和 WeightTileCache 前缀族覆盖了 8 个变化文件。
它漏掉 `GPT2PreLNBlock.sv`。
它漏掉 `GeneratedAcceleratorTop.sv`。
它漏掉 `GeneratedAxiDdrTop.sv`。
它漏掉 `PhysicalSimpleDualPortMemory_6.sv`。
该行 recall 为 8/12，即 0.667。
该行 predicted-unrelated 中有 32 个文件保持未变化。
该行 unrelated 集合共 36 个文件，preservation 为 32/36，即 0.889。

`cols_16` 实际变化 15 个文件。
预测模块族覆盖 8 个变化文件。
它漏掉两个 generated top/wrapper 文件。
它漏掉 `GPT2PreLNBlock.sv`。
它漏掉 `PhysicalSimpleDualPortMemory_4.sv`、`_6.sv`、`_14.sv` 和 `_28.sv`。
该行 recall 为 8/15，即 0.533。
该行 unrelated preservation 为 29/36，即 0.806。

`fifo_128` 实际变化 7 个文件。
规则预测受影响集合捕获到六个变化文件。
遗漏项是 `ResidualAdd.sv`。
该行 recall 为 6/7，即 0.857。
预测 unrelated 集合中 21/22 文件保持不变。
该行 preservation 为 0.955。

`banks_4` 实际变化 10 个文件。
这十个变化文件均命中 PhysicalSimpleDualPortMemory 前缀族。
该行没有漏掉的变化文件。
该行 recall 为 1.000。
该行所有 26 个预测 unrelated 文件保持不变。
该行 preservation 为 1.000。

`rows_4` 实际变化 12 个文件。
规则覆盖 8 个变化文件。
未覆盖集合与 rows_8 类似，包括两个 generated top、GPT2PreLNBlock 和一个物理 memory 实例。
该行 recall 为 0.667。
该行 preservation 为 0.889。

`cols_8` 实际变化 15 个文件。
规则覆盖 8 个变化文件。
未覆盖集合包含 GPT2PreLNBlock、GeneratedAcceleratorTop、GeneratedAxiDdrTop 和四个 SimpleDualPortMemory 实例。
该行 recall 为 0.533。
该行 preservation 为 0.806。

`cols_4` 实际变化 15 个文件。
该行输出与 cols_8 同样具有 15 个变化文件。
规则覆盖 8 个变化文件。
未覆盖集合包括 GPT2PreLNBlock 和两个 generated top/wrapper。
未覆盖集合还包括 PhysicalSimpleDualPortMemory 的 `_4`、`_6`、`_14` 和 `_28` 实例。
该行 recall 为 0.533。
该行 preservation 为 0.806。

`fifo_32` 实际变化 4 个文件。
规则覆盖全部四个变化文件。
变化集合除了 FIFO 实例外也包含 `PhysicalSimpleDualPortMemory_19.sv`。
该文件由当前 FIFO 规则的 PhysicalSimpleDualPortMemory 前缀捕获。
该行 recall 为 1.000。
该行 22 个 predicted-unrelated 文件全部未变。
该行 preservation 为 1.000。

`banks_8` 实际变化 10 个文件。
PhysicalSimpleDualPortMemory 模块族规则覆盖全部十个变化文件。
该行没有 missed changed files。
该行所有 26 个 predicted-unrelated 文件保持不变。
该行 recall 和 preservation 均为 1.000。

`reuse_2` 实际变化 12 个文件。
Linear、WeightTileCache、PhysicalLinear 规则覆盖 6 个变化文件。
另有 6 个物理 memory 实例发生变化但不在 reuse 预测族中。
该行 recall 为 6/12，即 0.500。
该行 predicted-unrelated 中有 32/38 个文件保持不变。
该行 preservation 为 0.842。

十行 recall 的算术平均为 0.729047619。
十行 preservation 的算术平均为 0.899109516。
平均值是十个候选的未加权算术均值。
它不是把所有文件合并后的 micro-average。
它不代表跨模型的统计期望。
它不含误差条或置信区间。

### PropBench 的 stale 与 partial 结果如何解释

十个完整候选的当前 manifest validation 都为 pass。
这是对候选自身份绑定的正对照。
十个 partial 目录都恰好改变一个 SV 源文件。
十个 partial 的 Stage-5 manifest validation 都为 fail。
十个旧版 `validate_generated_params_source()` partial 结果仍为 pass。
这说明旧参数 Scala 检查不读取完整 RTL 源树 hash。
新检查器检出的核心差异是同参数签名下源文件集合与字节发生错配。

每个 partial 的 error 包含 SV manifest changed file 列表。
端口指纹发生变化时，也会报告 `port_signature_changes`。
有些 partial 回退文件的变化会暴露接口位宽差异。
另一些可能只表现为内部/生成逻辑文件 hash 差异。
本轮的 10/10 检出来自精确 SHA 清单。
不能把 10/10 说成十个都由端口宽度错误检出。
manifest 的文件字节检查与 port signature 检查是两个不同检测通道。

四组旧的完整顶层 VCS partial elaboration 记录仍保留。
它们是在本轮以前执行的，不是 PropBench v5 新跑的四次 VCS。
rows_8 的旧 VCS 返回码为 0，但有 6 条 PCWM-W。
cols_16 的旧 VCS 返回码为 0，但有 10 条 PCWM-W。
fifo_128 的旧 VCS 返回码为 0，warning 数为 0。
banks_4 的旧 VCS 返回码为 0，warning 数为 0。

按照本轮重新声明的实验契约，任何 PCWM-W 都作为接口宽度 contract violation。
所以 rows_8 和 cols_16 被分类为 contract fail。
工具的原始 return code 仍准确保留为 0。
工具通过和契约通过不是同一判据。
本轮没有为这些历史执行重新调用 VCS。
本轮没有证明 VCS 支持或启用了 `-Werror=PCWM-W`。
不得在论文中写“本轮使用 -Werror 复跑并失败”。

### TraceBench metadata：构造与检查路径

metadata 臂的 runner 是 `run_tracebench_v7.py`。
该臂对原 pipeline plan 中前十条 stream edge 逐个建立隔离副本。
每个副本只将对应边的 `src_output_bits` 从 element width 改为其两倍。
原始 baseline plan 不被修改。
注入输入单独写入 `fault_pipeline_plan.json` 和 `injected_pipeline_plan.json`。
图状态副本独立保存在 `sacg_fault_state.json`。
答案标签只写入 `scoring_sidecar.json`。
静态投影器调用时不接收 scoring sidecar。

fault checker 调用生产 `check_edge_contracts()`。
failure report 保存错误摘要、fault copy SHA 和 SACG snapshot SHA。
`build_static_failure_context()` 根据报告映射违反的 graph edge。
runner 要求诊断边数正好为一。
若不是一条边，case 会被标为 unlocalized，而不会继续执行定点修复。

修复只将被标记边的 `src_output_bits` 恢复为其 `element_bits`。
修复同时写入被授权的工作 plan。
fault 原始输入副本保留。
修复之后调用 `run_pipeline_static_checks()`。
checker summary 和 status 写回 plan artifact。
随后调用原生 `summarize_pipeline_plan()`。
随后由 `build_review_checker_results()` 构造 Stage-6 review check 结果。
从结果中实际取 `stream_plan_check` 和 `data_order_trace_check`。
还附加 `pipeline_plan_static_check`。

远端 compile helper 上传未改变的 generated SV 集合。
它在每个 case 远端目录下运行 `vlogan -full64 -sverilog`。
该远端检查验证 source-analysis 门限。
它并不运行 top elaboration。
它不运行仿真。
它不检查 metadata patch 是否改变硬件行为。

每个 transition 的 `required_checkers` 来自隔离 SACG 状态。
runner 只为 transition 实际要求且已有真实结果的 checker 附加 evidence。
日志记录在每个 checker 对应的 JSON 文件中。
evidence log 本身的 SHA 写入 `promotion_result.json`。
最终调用原始 `SACGStore.promote(transition_id)`。
晋升成功记录为 `promoted`。
若有任何 checker 缺失或 fail，辅助函数将记录 `not_promoted` 和原因。
它不会通过删除 required checker 强行通过。

### TraceBench metadata：逐例边和晋升证据

E01 注入第一条 pipeline stream edge 的输出位宽冲突。
生产 `check_edge_contracts()` 返回 fail。
图投影得到唯一 downstream 候选 `stage_00_layer_norm_1`。
上游候选为 block_input。
定点修复后的 pipeline static check 为 pass。
远端 vlogan return code 为 0。
required checker 为 data_order_trace_check、pipeline_plan_static_check、stream_plan_check。
三项证据均 pass。
transition promotion 为 promoted。

E02 注入第二条 pipeline stream edge 的输出位宽冲突。
生产 checker 报告该条边。
downstream 候选为 `stage_02_residual_add_1`。
上游候选为 block_input。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均附加 pass evidence。
transition promotion 为 promoted。

E03 注入第三条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_01_self_attention`。
上游候选为 `stage_00_layer_norm_1`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E04 注入第四条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_02_residual_add_1`。
上游候选为 `stage_01_self_attention`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E05 注入第五条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_03_layer_norm_2`。
上游候选为 `stage_02_residual_add_1`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E06 注入第六条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_07_residual_add_2`。
上游候选为 `stage_02_residual_add_1`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E07 注入第七条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_04_mlp_fc`。
上游候选为 `stage_03_layer_norm_2`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E08 注入第八条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_05_activation`。
上游候选为 `stage_04_mlp_fc`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E09 注入第九条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_06_mlp_proj`。
上游候选为 `stage_05_activation`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

E10 注入第十条 pipeline stream edge 的输出位宽冲突。
downstream 候选为 `stage_07_residual_add_2`。
上游候选为 `stage_06_mlp_proj`。
修复后静态检查为 pass。
远端 vlogan return code 为 0。
三项 required checker 均 pass。
transition promotion 为 promoted。

十个 metadata case 的原生 `fault_check_status` 均为 fail。
十个 case 都有唯一违反边。
十个 case 的 downstream candidate 都包含真实 violated-edge destination。
十个 case 的 upstream candidate 都匹配真实 source endpoint。
十个 case 修复后 pipeline static check 都 pass。
十个 case 远端 vlogan 都返回 0。
十个 transition 都附加 3 个 checker 的 pass evidence。
十个 transition 均被真实 `SACGStore.promote()` 返回 promoted。
十个 case 的文件授权覆盖目标 pipeline plan。
十个 case 的授权范围均没有超出实际 patch 文件。

本轮 metadata summary 的 `upstream_hits` 和 `downstream_hits` 都是 10。
这些命中基于 checker 已报告的唯一 edge 与对应图端点。
这不是把任意非结构化硬件故障盲定位到根因的命中率。
这不是 LLM 独立推理准确率。
这不是运行时 CCTG 定位成功率。
它是生产静态 checker 报告到图端点的映射实验。

### data_order_trace_check 的准确含义

此 checker 名称容易被误解为 RTL trace 或波形分析。
本轮调用的是 `stage_verification_plan.build_review_checker_results()` 生成的静态 review 结果。
输入包括当前 SACG、pipeline plan summary、参数绑定 summary 和 codegen manifest summary。
调用时没有提供 runtime simulation result。
该 checker 的结果是静态的数据顺序 ledger 状态。
它明确保留下游真实仿真仍需执行的要求。
所以 promotion 的 checker pass 不等于数据在仿真中顺序正确。
这也不等于真实输入和权重下的模型输出有效。

`stream_plan_check` 同样是当前 plan 与图状态的一致性检查。
它不代表真实 ready/valid 在时钟边沿上运行过。
`pipeline_plan_static_check` 只检查 plan 结构及静态契约。
`vlogan` 只做 SystemVerilog 源码分析。
这些证据的组合可满足该 benchmark transition 配置的 required checkers。
它不能被写成“完成端到端功能验证”。

### TraceBench RTL：样本选择与注入

RTL 臂的 runner 是 `run_tracebench_v7_rtl.py`。
它使用原 v6 RTL fault runner 的远端上传、VCS 工具调用和绑定检查函数。
source snapshot 来自 R2 GPT-2 Medium seq32 generated/chisel。
baseline graph 来自同一个 ACCORD run 的 `sacg_state.json`。
每个 case 都在独立目录创建工作源。
每个 case 的顶层 `.sv` 是可写副本。
源资源目录的较大 Scala、memory、runtime 和 simulation 子树采用硬链接副本以减少空间。
被修改的顶层 SV 文件在写入前为普通独立副本。
因此不会通过硬链接意外改写历史源树。

第十个案例列表采用 DenseFFN 替换旧未实例化的 outer top 案例。
DenseFFN 有 `GPT2PreLNBlock` 中的实例消费者。
该 cohort 和旧版包含 GeneratedAxiDdrTop 的 cohort 不完全相同。
新实验因此作为新的 v7 cohort 报告。
旧 v6 的九个已运行样本原样保留。

每个案例的 fault injector 从选定模块头中选取一个包含 bits 的端口优先。
如果没有 bits 端口，则选择非 clock/reset 的普通端口。
producer 内声明和引用的 token 被替换为新的带后缀名称。
实例上的 named-port label 通过正则 negative lookbehind 保持不变。
故障目的是让消费者仍连接旧接口名，而 producer 不再导出该接口名。
注入器会将输入文件单独保存为 retained fault source。
评分 sidecar 保存注入目标信息，但不传给诊断投影函数。

runner 从目录中找实际实例化 producer 的消费者。
如果没有现成消费者，case 标记 not_run。
v7 以 DenseFFN 取代原先无消费者的 GeneratedAxiDdrTop 目标来达到十个可执行案例。
每个 case 使用消费者模块作为 VCS top。
加载的来源包含被测 producer SV 和其消费者 top 的生成依赖闭包。
工具先执行 vlogan 源码分析。
随后执行 VCS elaboration。
有意注入的端口失配在 elaboration 阶段产生 UPIMI-E。

### TraceBench RTL：诊断字段和消费者图投影

runner 从真实 `fault.log` 中解析 `Port ... is not defined in module ...`。
它解析 VCS 错误前的消费者文件位置。
它解析 `Module instance: Producer instance_name` 行。
consumer source 从同一 fault 工作目录读取。
consumer source 文件 SHA 写入 failure report。
consumer 源 artifact origin 必须与图上 generated package 目录绑定。
tool log SHA 写入 failure report。
producer fault-copy SHA 与远端源 SHA 被记录。
上传 bundle SHA 和 SACG snapshot SHA 也写入报告。

`build_static_failure_context()` 首先根据原有 producer module materialization 映射构造 root candidates。
消费者上下文只用于约束候选集合。
它不会授予 patch 权限。
它不会直接设置唯一 root。

消费者文件必须存在。
消费者文件 SHA 必须与报告相同。
消费者 artifact origin 必须位于 graph-bound artifact root。
工具 log 文件必须存在。
工具 log SHA 必须匹配报告。
消费者文本必须声明对应 module。
消费者文本必须有指定 producer instance。
工具 log 中必须报告相同 producer module。
工具 log 中必须出现同名 producer instance。
工具 log 中的首个消费者 SV 报告位置必须匹配 consumer source 文件。
工具 log 必须包含 undefined-port diagnostic。
任何上述绑定缺失时，消费者消歧标记为 invalid_evidence 或不执行窄化。

若 producer candidates 与 consumer owner candidates 相交，使用交集。
如果 producer 候选为空而 consumer 归属只有一个，允许使用唯一绑定的 consumer owner。
若报告为集成 consumer，尝试从实例 input/computed bits_data 信号反向查找子模块 output bits_data 连接。
然后只通过 SACG predecessor edge 窄化 pipeline stage。
如果不能唯一窄化，保留原 stage 候选集。
算法不根据实例名后缀 add1/add2 硬编码 stage id。

此投影是静态故障上下文，不是 runtime CCTG。
consumer edge refinement 依赖生成文件和 VCS log 保留的上下文。
顶层 producer 的包边界不必然对应一个计算 stage。
共享物理 resource 可能服务多个计算 stage。
因此共享所有者仍然可能正确地保留多候选。

### TraceBench RTL 十案例逐案结果

所有案例的 fault side `vlogan_returncode` 均为 0。
所有案例的 fault side `vcs_returncode` 均为 255。
所有案例的 repair side `vlogan_returncode` 均为 0。
所有案例的 repair side `vcs_returncode` 均为 0。
255 是本 runner 观察到的 VCS 故障退出码。
报告以具体 UPIMI-E 错误内容为故障证据，不仅根据退出码计分。

F1 测 DenseFFN producer。
VCS 报告未定义的 `io_upWeight_bits_addr` 端口。
消费者为 `GPT2PreLNBlock` 的实例 `ffn`。
producer 初始有两个 stage 候选：MLP FC 和 MLP projection。
消费者 owner 也覆盖这两个计算 stage。
交集仍为两个候选。
最终保留两个候选。
这说明模块级消费者上下文不足以区分 DenseFFN 内部两个线性 stage。
精确文件授权为单个 DenseFFN SV 文件。
修复使用端口 diagnostic 和 consumer 声明推断的名称恢复。
修复 elaboration 通过。
五项 native package checker evidence 全 pass。
transition promoted。

F2 测 GeneratedAcceleratorTop producer。
VCS 报告未定义 `ddrTileRequest_bits_routeId`。
消费者为 GeneratedAxiDdrTop 的 `core` 实例。
producer 投影初始关联 block_input 与 block_output 边界候选。
consumer semantic owner 没有计算 pipeline stage。
无法从消费者所属 stage 得到唯一交集。
结果中 `candidates_after` 为空，投影不提供唯一 stage root。
该 case 仍可基于准确编译诊断对精确 producer 文件作范围受限修复。
精确文件授权一份。
修复后 vlogan 与 VCS 均通过。
五项 native package checker evidence 全 pass。
transition promoted。

F3 测 Attention producer。
VCS 报告未定义 `io_in_bits_data`。
消费者为 GPT2PreLNBlock 的 `attn` 实例。
producer 映射本来就只有 self-attention stage 一个候选。
消费者模块的 graph alias 没有额外 owner。
最终仍保留这个既有唯一候选。
该行不是新增消歧带来的候选数量改善。
精确 producer 文件授权通过。
修复后两个 VCS 阶段均返回 0。
五项 native package checks 全 pass。
transition promoted。

F4 测 IntegerAttention producer。
VCS 报告未定义 `io_in_bits_data`。
消费者是 Attention 的 `core` 实例。
IntegerAttention 的 producer candidate 是 self-attention stage。
Attention consumer owner 也映射到 self-attention stage。
producer/consumer 交集为唯一 stage。
精确文件授权通过。
修复后 VCS elaboration pass。
五项 native package checks 全 pass。
transition promoted。

F5 测 Linear producer。
VCS 报告未定义 `io_weight_bits_addr`。
消费者是 QKVProjection 的 `projection` 实例。
根据旧 module-only alias，Linear 最初对应 MLP FC 和 MLP projection 两个 stage。
QKVProjection 是 graph-bound 的 self-attention consumer。
producer 与 consumer 没有交集时，唯一 graph-bound consumer owner 可以提供收敛到 self-attention stage 的语义绑定。
这是该样本中 consumer context 从两个候选得到一个候选的例子。
精确文件授权通过。
修复 patch 对应端口名推断。
重跑 vlogan 和 VCS 均为 0。
五项 native package checks 全 pass。
transition promoted。

F6 测 Activation producer。
VCS 报告未定义 `io_in_bits_data`。
消费者是 DenseFFN 的 `act` 实例。
原始 producer candidates 包含 model activation node 和 pipeline activation stage。
DenseFFN semantic owner 包含 MLP FC 与 MLP projection 两阶段。
两集合不提供唯一交集。
最终投影仍保留 activation stage candidate，而不强行选择 MLP 的某一端。
本例候选数量从原 producer 绑定的两个节点信息经 owner 规则维持 conservative stage candidate。
精确文件授权通过。
修复后 VCS 返回 0。
五项 native package checks 全 pass。
transition promoted。

F7 测 ResidualAdd producer。
VCS 报告未定义 `io_residual_bits_data`。
消费者是 GPT2PreLNBlock 的 `add1` 实例。
ResidualAdd producer 先验映射包括 residual_add_1 和 residual_add_2。
消费者模块本身没有单独的 pipeline owner。
投影器解析 add1 实例中的 `io_computed_bits_data` 输入信号。
解析到 Attention 子模块输出的信号连接。
图中 Attention 输出有一条到第一 residual add 的 predecessor stream edge。
该图边将候选从两个 residual stage 收敛到 `stage_02_residual_add_1`。
这不依赖实例名字符串推断 stage。
这是本组最清晰的 graph-connected consumer disambiguation 样例。
只授权 ResidualAdd SV 文件。
定点修复通过 VCS。
五项 native package checks 全 pass。
transition promoted。

F8 测 PhysicalStreamFifo producer。
VCS 报告未定义 `io_enq_bits_data`。
消费者是 ResidualAdd 的 `residualQ` 实例。
producer 初始候选包括八个 pipeline stage。
ResidualAdd 的语义 owner 包括 residual_add_1 与 residual_add_2。
两集合交集仍有两个 stage。
最终结果保留两个候选。
这是共享 FIFO 由两个 residual stage 使用时的真实歧义。
没有用 FIFO 的内部名字伪造单一 root。
精确文件授权通过。
修复后 VCS pass。
五项 native package checks 全 pass。
transition promoted。

F9 测 WeightTileCache producer。
VCS 报告未定义 `io_tileRequest_bits_routeId`。
消费者是 Linear 的 `weightMem` 实例。
producer 初始候选覆盖多个 pipeline stage。
Linear semantic owner 有 MLP FC 与 MLP projection 两阶段。
交集仍为这两个 stage。
最终没有唯一化。
这符合权重缓存可服务多个线性阶段的共享语义。
精确文件授权通过。
修复后 VCS pass。
五项 native package checks 全 pass。
transition promoted。

F10 测 QKVProjection producer。
VCS 报告未定义 `io_weight_bits_addr`。
消费者是 GPT2PreLNBlock 的 `qkv` 实例。
producer 本身唯一映射到 self-attention stage。
消费者 owner alias 没有额外收敛该候选。
该 case 最终仍是唯一 producer candidate。
它不是共享模块双端交集成功的独立证明。
精确文件授权通过。
修复后 VCS pass。
五项 native package checks 全 pass。
transition promoted。

### TraceBench RTL 原始证据与计分边界

所有十个 fault report 的 tool log SHA 与实际本地 log 文件一致。
所有十个 repair log 都保留在逐案目录。
fault 和 repair helper 均报告三方 source binding match。
runner 检查上传内容的 manifest 与本地工作树。
runner 对远端解包树生成并回传源文件 manifest。
逐案保存的 remote producer SHA 与本地 diagnosed fault SHA 对应。
注入的 source 文件不覆盖原始 baseline module。
patch diff 显示仅修改受授权的目标 producer 文件。
`scope_violation` 十例全 false。

promotion 所需五项是 `code_generation_manifest_static_check`。
promotion 所需五项还包括 `codegen_compile_gate`。
promotion 所需五项还包括 `codegen_contract_check`。
promotion 所需五项还包括 `codegen_package_static_check`。
promotion 所需五项还包括 `template_coverage_check`。

这五项中的若干 Stage-5 证据引用历史 package compile result。
runner 对比当前恢复的全部 SV 源哈希与历史 baseline。
runner 对比当前恢复的 Scala 源哈希与历史 baseline。
只有两组源都与历史快照完全一致，`codegen_compile_gate` 才记录通过。
该证据行明确写 `fresh_execution=false`。
同一 transition 另有当前 remote consumer-level VCS 修复重验结果。
历史 Stage-5 compile reuse 与本轮 VCS repair run 是两个不同证据。
晋升记录没有把历史 SBT compile 说成新跑。

promotion helper 将 JSON 结果写入本地证据文件。
它调用 `store.attach_evidence()` 并关联 checker invariant 与 transition。
它调用 `store.promote()`。
`promotion_result.json` 保存所附 checker 名称、status、evidence ID 和日志 SHA。
该操作发生于隔离复制的 SACG state。
每个 case 有独立 transition 和独立 graph path。
不能据此推断真实 Agent 的 Stage-6 production transition 现已采用该 helper。
不能据此推断 `stage_repair_execute.py` 已接入新的 scope API。

### Paired Timing v5：七项完整门限

paired runner 为 `run_paired_timing_v5.py`。
前六项沿用 v4 gate：constraint static、template binding、pipeline plan static、DSE materialization、package static 和 remote vlogan compile。
新增的第七项为 `remote_top_vcs_elaboration`。
第七项以 `GeneratedAcceleratorTop` 为 top。
调用中包含 Vivado XPM memory simulation model。
局部的比较门限为 `remote_local_vcs_elaboration`。
局部门限以 `DenseFFN` 为 top。
两个 helper 都调用 fresh vlogan 与 XPM 源码处理。
所以每个 elaboration gate wall time 包含 vlogan 加 VCS elaboration。

paired baseline 是七个 gate 的 pass 结果。
每个 mutation case 从相同 SOURCE 快照复制一份硬链接树。
被改文件先 unlink 再写入新内容，防止改变源 baseline 或其他共享 case。
runner 对实验开始前的 semantic adapter 与 template Scala 文件生成 hash map。
runner 在所有配对执行后重新计算同一组 hash。
两组 map 相等，说明本实验共享输入在执行过程中未变。

每个 case 先计算 changed path。
runner 用显式实验依赖 registry 建立 invalidated evidence rows。
随后调用生产 resolver `resolve_revalidation_gates()`。
targeted gate 从 resolver 输出选择。
完整臂依次运行七项 gate。
两臂结束后核对变异源 snapshot hashes。
paired 全部 gate pass 且 snapshot hash 一致时 case 才记作 all_pass。

planning 计时包含源 hash 对比和 resolver 调用。
snapshot 复制时间不纳入计时。
baseline 执行的时间不计入每个 mutation case 的 targeted/full 数值。
没有做随机化运行顺序。
每个变异只有一组 targeted/full 配对读数。
没有运行多轮分布统计。

### Paired Timing v5 四个变异的逐项数据

E1 改动 README 文档。
targeted resolver 没有选中 gate。
targeted 总时间 0.017992821 秒。
这 0.01799 秒主要是 hash 和 resolver planning。
它不包含 gate 执行。
full 七项总时间 32.117720200 秒。
算术减少比例为 0.999439785，即约 99.944% 。
该结论只表示本实验所登记 evidence dependency 下文档修改没有失效 gate。

E2 改动 pipeline metadata。
targeted 只选择 `pipeline_plan_static_check`。
targeted 总时间 0.021168881 秒。
full 七项总时间 32.032164713 秒。
算术减少比例为 0.999339137，即约 99.934% 。
targeted 与 full 对同一变异内容运行。
计划静态 checker 在两臂均通过。

E3 改动 parameter binding metadata。
targeted 选择 `dse_materialization_check`。
targeted 总时间 0.019409563 秒。
full 七项总时间 32.074675200 秒。
算术减少比例为 0.999394863，即约 99.939% 。
物化 checker 在 targeted 和 full 两臂均通过。
该案例没有更换实际硬件参数和重新展开 Chisel。
该案例是已有快照中的 metadata mutation。

E4 改动 Activation.sv 内的注释。
改变后端口 fingerprint 相同。
实验依赖策略选择 package static check。
策略选择远端 vlogan。
策略还选择局部 `DenseFFN` elaboration。
targeted 总时间 16.729688826 秒。
full 七项总时间 31.989467319 秒。
算术减少比例为 0.477025089，即约 47.703% 。
结果低于计划提出的 80% 预估。
局部和完整 elaboration 均通过。
E4 的源码差异只添加注释，没有改变 operator logic。

E4 的约 16.73 秒不能直接等价为“所有局部 RTL 改动都可局部验证”。
接口 fingerprint 不变不能证明内部语义不变。
真实功能修改可能改变状态、ready/valid 行为或资源关系。
完整七项约 32 秒由顶层 VCS elaboration 主导。
局部 DenseFFN elaboration 仍比旧 v4 的单纯 vlogan 明显更贵。
单次计时受 SSH、远端负载、文件系统 cache 和网络抖动影响。

### Paired Timing v5 实验中的限制

E1 的 selected gate 为空。
所以它的高节省比例不是一个 checker 在几十秒 full suite 中提前完成。
它表示已登记 dependency closure 对这个文档路径没有命中。
此策略不覆盖所有潜在工具读取。

E2 与 E3 对应测试均为单个 metadata 文件修改。
它们没有触发重新生成 RTL。
它们也没有测试上游参数变动导致 downstream package 真实更新。

E4 只能证明本轮 comment-only RTL 变更下，所选局部门限和 full 门限都通过。
它不能证明机制检测到所有内部语义变化。
报告没有把局部比全局的一次 passing 结果解释为普适等价。

完整 Suite 明确增加 top elaboration 后，full suite 从约 3.7 秒增至约 32 秒。
该变化是加入更重 gate 的预期后果。
因此与 v4 的数字不可直接比较成同一 validation policy 的简单 speedup。
E4 的 targeted 所选局部 elaboration 也运行 fresh vlogan。
该重复源码分析成本计入计时。

### validation4 中途修正和可能误读的审计点

PropBench 首轮因 legacy summary field name 不统一而未完成。
该问题由使用 `sv_hashes` 差分取代依赖特定 reference key 修正。
首轮 partial 未复制参数 Scala 的问题也在正式重跑前修正。
首轮目录完整保留，但不参与正式十组计数。

consumer context 首次实现仅验证文件和日志 hash、artifact origin 以及 source 中存在实例。
进一步检查发现调用方仍可能指定一个没有出现在真实 VCS log 的实例。
投影器随后新增同一日志中 producer、instance、consumer location 与 undefined-port diagnostic 的核对。
新增回归先失败了一次。
失败来自测试预期错误：测试认为无效 consumer 会恢复两个 producer candidates，但 fixture 中既有映射路径保留了一个候选。
调整断言为“不因伪造实例进一步收窄”，随后 15 个 causal slice tests 全部通过。
这是测试语义修正，不是将失败的投影结果隐去。

stage artifact package checker 一度使用 Stage-5 manifest 自带参数作为预期值。
这会让 manifest 无法独立发现自身参数签名被一起替换的情况。
实现随后改为与外层 generated-top params 对比。
此项改动通过 stage artifacts 的 13 项回归。
PropBench v5 的历史 manifest 由单独函数使用候选 binding 参数建立，逐例记录其参数来源。

审计器初次运行时对 metadata evidence 读取了 `progress.json` 中不含细节的 promotion summary。
该字段中 `attached_checks` 不存在。
Python 的 `all([])` 为真，因而最初的 59/59 检查虽然表面通过，但 metadata evidence log 子检查是空集合真空通过。
复查逐例 `promotion_result.json` 后发现每例真实保存 3 条 checker evidence。
审计器改为加载十个 `promotion_result.json`。
新条件要求每例恰有三项 evidence。
新条件还要求每个 log 路径存在。
新条件还逐一重新计算日志 SHA 并对照记录值。
修正后的最终审计仍是 59 条 check 全 pass。
59 条是修正后重新执行的结果。
旧的 vacuous pass 判断不作为最终证据。

逐案的 metadata evidence SHA 和 status 均为三个 pass。
逐案的 RTL promotion evidence SHA 检查均读取五条 evidence row。
逐案 VCS fault 与 repair raw log SHA 都被重新计算。
paired baseline 七项 gate 均 pass。
paired 四组变异均 all_pass。
paired shared source hash map 前后相同，共核对 17 个 adapter/template inputs。
PropBench 十组候选都与 v4 source hashes 匹配。
PropBench 十组 partial 都只有一个 changed file。
PropBench 十组 partial 都由 manifest 检出。

### validation4 测试命令及结果

运行 `python3 -m unittest discover -s tests -p test_stage5_sv_manifest.py -v`。
该测试集 6 项全部通过。
测试覆盖 unchanged manifest pass。
测试覆盖同名源文件替换失败。
测试覆盖新增文件失败。
测试覆盖删除文件失败。
测试覆盖参数签名变化失败。
测试覆盖 GeneratedDesignParams Scala hash 变化失败。
测试覆盖注释变更不改变端口指纹但会改变源 hash。
测试覆盖 ANSI 头中方向和位宽继承。
测试覆盖参数族依赖规则输出。

运行 `python3 -m unittest discover -s tests -p test_stage_artifacts.py -v`。
该测试集 13 项全部通过。
测试覆盖 codegen gate、manifest、generated bindings、resource closure 和 warning marker 等已有行为。
本轮没有为通过测试修改硬件实现。

运行 `python3 -m unittest discover -s tests -p test_sacg_cctg_causal_slice.py -v`。
该测试集 15 项全部通过。
其中新增 consumer context focused test 验证一个 graph-bound consumer 可将候选收敛到 attention stage。
该测试还把 instance name 改成不存在的名字。
投影器因此报告 consumer context invalid evidence。
伪造 consumer 不会触发新的 stage narrowing。

运行 `python3 -m py_compile` 检查新增/修改的 Python runner、helper 和 framework 源码。
语法检查通过。
运行 `git diff --check` 对本轮相关文件检查 whitespace。
没有 diff whitespace error。

运行 `audit_validation4_results.py`。
修正后的 59 项记录一致性检查全部通过。
该检查不是 59 项硬件功能验证。
它覆盖文件 SHA、promotion logs、remote source binding、paired gate status、partial single revert 和共享文件状态等记录一致性。

### 结果计数定义

PropBench 的 candidate manifest pass 是文件清单正对照通过数。
PropBench partial detected 是部分回退导致文件清单不一致的检出数。
它们都不是硬件功能正确率。

TraceBench metadata fault detected 是 `check_edge_contracts()` 返回 fail 的注入案例数。
downstream hit 是真实违反边 destination 出现在 projection candidates 中的数目。
upstream hit 是真实违反边 source 与投影的 upstream candidate 相同的数目。
repair static pass 是修复后 pipeline static checker pass 的数目。
repair vlogan pass 是远端源代码分析 return code 0 的数目。
promoted 是真实调用实验 `SACGStore.promote()` 后返回 promoted 的数目。
这些计数不等价于运行时行为正确。

TraceBench RTL fault VCS failed 统计注入故障对应 VCS elaboration 非零的数目。
本轮还逐例核对诊断类型确实是 undefined module port。
repair pass 要求 repair vlogan 与 VCS elaboration 返回 0。
authorized 是准确文件授权行数。
scope violation 是 patch path 不属于精确授权路径的行数。
promotion 是隔离 SACG store 状态转换成功数。
候选数量是图投影 uncertainty 的描述，不作为 pass/fail 自动阈值。

Paired Timing reduction fraction 的算式是 `1 - targeted_total / full_total`。
targeted_total 包含 hash/resolver planning 和被选择 gate 的实际时间。
full_total 是七个 gate 墙钟时间求和。
时间结果只针对本轮 runner 的命令、路径和服务器状态。

### 本轮能够支持的结论

Stage-5 当次保存的参数绑定 SV manifest 可以检测单文件源码回滚。
Stage-5 参数 Scala checker 单独无法检测十组 partial SV 回退。
所声明的参数到模块族 prior 可对部分 generated file byte changes 做出预测。
在十个候选中，该 prior 的平均观察召回率约 72.9%。
在十个候选中，该 prior 的平均预测 unrelated preservation 约 89.9%。
不同参数及候选的结果差异显著。
计算阵列参数的 family rule 在本批次漏掉部分 wrapper 和 memory files。
FIFO 和 reuse 规则也分别存在遗漏。

静态 metadata checker 报告的准确 stream edge 可以投影到其 SACG source/destination 节点。
基于真实 VCS 的 consumer/module/instance 诊断上下文可以在部分情形中缩小 graph candidate set。
ResidualAdd 的数据连接加图前驱路径提供一个具体的 stage 级候选消歧案例。
共享模块在多 stage 使用时仍会保留多候选。
该保留比伪造唯一根因更符合证据。

把真正的静态 required-checker evidence 附加到隔离 transition 后，SACGStore promotion 可以通过。
每个 promotion 仍需按真实 checker required set 附加证据。
代码没有通过移除 required checker 来得到 promotion。
历史 SBT compile evidence 被明确标记为复用，并要求源文件 byte identity。

对 E1 到 E3 的受控轻量变化，完整七项 full suite 与解析器选出的 gate 都通过。
对 E4 的注释变化，局部消费者级 elaboration 和全 top elaboration 都通过。
full suite 加入 top-level VCS 后耗时约 32 秒。
E4 targeted 实际节省约 47.7%。
该实际数字低于计划中的 80% 预测。

### 本轮不能支持的结论

不能声称 PropBench 的参数语义传播准确率达到 100%。
不能声称参数到模块族规则是独立语义真值 oracle。
不能声称历史 Stage-5 当时已经生成并存储 v5 manifest。
不能声称 partial 回滚十例都由位宽 checker 检出。
主要通用检测机制是 hash-bound membership manifest。

不能声称十个 RTL 故障中有十个都被图唯一定位。
不能将 producer module 候选覆盖说成 root-cause Top-1 accuracy。
不能声称消费者上下文在所有共享 resource 上必然唯一。
不能声称 deterministic patch 是 LLM 自主设计的 RTL 修复。
不能声称 benchmark store promotion 已进入真实 repair executor。
不能声称静态 data-order ledger 是真实 runtime trace。
不能声称编译通过证明数值正确。

不能声称 Paired Timing 的 99.9% 是全 Agent 设计周期加速。
不能声称文档或 metadata 任意变化都无需验证。
不能声称 interface fingerprint 不变就足以跳过任意 RTL 功能检查。
不能声称 E4 获得计划预测的 80% saving。
不能声称单次四样本读数有统计显著性。
不能将 remote VCS elaboration 通过写成仿真通过。
不能将 VCS compile-only 结果写成 exact-board functional run。

### 论文写作时的建议表达

PropBench 可描述为“一个绑定生成参数签名与展开源码哈希的 Stage-5 package manifest 原型检查”。
报告 10/10 完整 candidate manifest checks 与 10/10 controlled single-file rollback detection。
同时给出 family rule recall 和 preservation 实测分布或逐案例数据。
说明 manifest 对历史样本是 retrospective capture。

参数规则结果可描述为“declared module-family dependency prior 对观察到的 generated-file changes 的 coverage”。
不要称它为 semantic parameter propagation accuracy。
最好展示 missed wrapper/memory 文件。
这些 missed files 能说明目前 SACG 规则仍需更准确的层次化依赖关系。

TraceBench metadata 可描述为“checker-reported contract edge to graph endpoint mapping under controlled metadata faults”。
报告十个 case 的静态 checker endpoint projection、局部 metadata repair 和 isolated-store transition promotion。
将远端 vlogan 明确标为 unchanged RTL source compile。
将 data-order checker 明确标为 static ledger result。

TraceBench RTL 可描述为“VCS consumer elaboration detected generated-port mismatch followed by bounded, deterministic, exact-file repair and re-elaboration”。
报告 fault side vlogan 0/VCS 255、repair side vlogan 0/VCS 0。
报告十例都授权一个文件且没有范围越界。
列出 candidate count 中的多义案例。
用 ResidualAdd 作为真正图邻接收敛示例。
如要呈现 promotion，脚注说明 required evidence 来自隔离 SACG transitions，部分 Stage-5 证据在源码完全相同后复用。

Paired timing 可描述为“same-snapshot compile/elaboration microbenchmark under the declared gate registry”。
明确 full suite 七项组成。
明确 E1 空 gate 选择。
明确将 hash/resolver 开销计入 targeted。
E4 报告 47.7% 实测差值，不沿用 80% 假设。
注明 E4 是 comment-only mutation。

### 本轮与 validation3 之前结果的关系

validation3 文档记录的 PropBench v4 原始结果仍有效。
validation4 v5 在十份原始独立树上追加 retrospective manifest 与规则评估。
它没有重写 v4 的 candidate hashes。
它没有改变 v4 的 VCS logs。
它也没有把 v4 的 compile return codes 改写成 contract status。

validation3 TraceBench v6 的 9 例旧 cohort 仍保留。
validation4 TraceBench v7 增加/替换样本以构造十例新 cohort。
由于第十个 case 目标变化，v6 与 v7 不应合并分母。
v7 的 summary 单独记录十个请求、十个执行。

validation3 Paired Timing v4 是六项 gate。
validation4 Paired Timing v5 是七项 gate。
两者的 full suite 定义不同。
v4 的约 1.10% E4 结果和 v5 的约 47.7% E4 结果不矛盾。
v5 新增顶层 elaboration，使 full 分母增加约 28 秒。
v5 targeted 臂使用 DenseFFN elaboration，也比 v4 单一 vlogan targeted 更贵。
所以应分别报告版本、组成和样本类型。

### 恢复记录和复现建议

本轮上下文恢复日志已写入 `docs/context_2026-03-27.md` 的 2026-11-01T23:02:39 和 23:15:21 条目。
实验主目录是 `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation_20261031/`。
进入任何 runner 前先阅读已有 summary 和 progress 文件。
所有 runner 都在目标 OUT 存在时拒绝覆盖。
不要删除 `propbench_v5_setup_attempt_1`，它记录第一轮脚本 schema 错误。
不要将远端服务器的 artifacts 清理后再复跑，否则会丢失相同 VCS 工作目录证据。

若复核 PropBench，可以只运行 Python manifest validator，不需要 SBT。
若重新运行 TraceBench RTL，需要远端 VCS、Vivado XPM 源文件和 SSH/SCP 可用。
每个 case 的 remote root 都按 runner 固定为 validation4 独立目录。
runner 只针对本地输出目录检查防覆盖。
任何新执行都应使用新的 experiment ID 和新的输出目录。

若把 Stage-5 manifest 机制接入其他真实 run，必须由当次成功 codegen path 生成 manifest。
不要将本轮回溯生成的 manifest 复制成历史运行时已存在的证据。
若扩展参数到模块族规则，先记录规则版本和依据，再执行候选 diff。
保留预测集合、observed changed、covered changed 和 missed changed 四组数据。
不要只保存 aggregate recall。

若后续希望提高消费者图定位率，应优先完善 graph binding 中的 module instance 到 stage mapping。
shared FIFO、cache 和 DenseFFN 应保留所有者集合。
可将 instance-level structural edge 纳入 SACG，而非用实例命名 convention 代替依赖证据。
验证新增映射时要用独立案例留出测试。
不要用同一批样本调规则并报告为盲测准确率。

若后续要报告 promotion 的生产意义，需要将 evidence collection 和 promotion 调用接入真实 repair executor。
必须让 executor 只接受真实刚运行或明确 identity-bound reusable 的 checker evidence。
还需证明 source/artifact version binding 与执行权限不依赖实验脚本。
当前实验仅证明 store API 在隔离状态下的行为。

若后续要报告 targeted validation correctness，需要注入具有真实逻辑影响的内部 RTL 修复和缺陷。
应当比较 targeted 与完整 suite 的缺陷检出一致性。
应区分仅注释、接口变化、组合逻辑变化、时序状态变化和跨模块连接变化。
对 interface unchanged 的修改，不应自动推论成语义局部。
有必要时 full VCS top 或 simulation 必须重新运行。

### Validation4 最终计数表

| 工作流 | 请求数 | 实际执行数 | 主要 checker / 工具通过 | promotion | 关键观察 |
| --- | ---: | ---: | ---: | ---: | --- |
| PropBench complete manifest | 10 | 10 | 10 pass | 不适用 | 十个完整候选与 retrospectively captured manifest 一致 |
| PropBench partial rollback | 10 | 10 | 10 fail-as-expected | 不适用 | 每例一个旧 SV 文件均由 manifest 拒绝 |
| TraceBench metadata | 10 | 10 | static 10, vlogan 10 | 10 | graph endpoint mapping 对 checker 已知 edge |
| TraceBench RTL | 10 | 10 | fault VCS 10, repair VCS 10 | 10 | 唯一根因未覆盖全部共享模块 |
| Paired Timing v5 baseline | 7 gates | 7 | 7 pass | 不适用 | 增加完整 GeneratedAcceleratorTop elaboration |
| Paired Timing v5 mutations | 4 | 4 | targeted/full 通过 | 不适用 | E4 saving 47.7%，非预期 80% |
| Integrity audit | 59 checks | 59 | 59 pass | 不适用 | 记录一致性，不是硬件测试 |

### 与原始计划假设逐项核对

计划提出 partial-update 10/10 检出。
实测结果为 10/10。
检测实现为 retrospective Stage-5 SV hash manifest。
该结果不来自 VCS 强制把 warning 升格为错误。

计划提出文件族 dependency recall/preservation。
实测输出了两项指标。
平均 recall 为约 72.9%。
平均 preservation 为约 89.9%。
不支持全 10/10 或 100% 机制精度。

计划提出 TraceBench 第十个样本可由 DenseFFN 替代。
实测十例均运行。
DenseFFN 的候选仍为两个 MLP stages。
cohort 与旧 v6 不同，统计分开。

计划提出 consumer context 可以消除共享模块歧义。
实测部分样本成功或保持唯一。
ResidualAdd 数据路径案例有明确二候选至一候选的收敛。
FIFO、WeightTileCache 和 DenseFFN 仍多候选。
顶层 GeneratedAcceleratorTop 不映射成唯一 stage。
因此计划的十例 Top-1 预期未达成。

计划提出通过补齐 checker evidence 实现 promotion。
隔离 metadata transition 10/10 promoted。
隔离 RTL transition 10/10 promoted。
checker evidence 文件逐一存在并与记录 SHA 一致。
这些 promotion 不表示生产执行器已经接线。

计划提出把完整 top elaboration 加入 full timing suite。
实测 baseline 七项全通过。
E1 到 E4 的 full seven-gate suites 均通过。
E1–E3 节省约 99.93% 至 99.94%。
E4 只节省约 47.7%。
计划的 E4 约 80% 预测未实现。

### validation4 的中间结果如何保存

PropBench 首轮目录在最终目录旁并存。
首轮目录名带 `setup_attempt_1`。
首轮 summary 不用于最终指标。
最终目录 summary 覆盖完整十例。
首轮脚本问题已在本节如实披露。

TraceBench metadata runner 执行日志保存在 `tracebench_v7_metadata_execution.log`。
日志逐例输出 promotion、静态 checker 状态和 vlogan return code。
TraceBench RTL runner 执行日志保存在 `tracebench_v7_rtl_execution.log`。
日志逐例输出 repair status、promotion 和图候选。
paired runner 执行日志保存在 `paired_timing_v5_execution.log`。
日志逐例输出 targeted、full 时间和 pass 状态。

原始 VCS log 可能包含工具、locale 或服务器环境提示。
locale warning 不自动等同于 VCS compile failure。
故障计分同时读取 UPIMI-E diagnostic 和退出码。
修复计分同时读取源代码返回状态、VCS return code 和 source binding。

### 本轮结束时的环境状态

PropBench runner 已退出。
TraceBench metadata runner 已退出。
TraceBench RTL runner 已退出。
Paired Timing runner 已退出。
59 项独立审计重新运行并通过。
三组 focused unittest 均通过。
没有处于运行状态的本轮 VCS wrapper。
远端产生的日志和源包仍保留。
本地实验结果没有放置在 `/tmp`。
本轮没有删除旧实验产物。

### 给下一步规划者的结论

这轮将“新 Stage-5 物化 manifest 能检测混合旧新 RTL”从未测量推进为十例受控证据。
这轮把参数到 generated-module family 的依赖预测从未测量推进为有真实误差的定量基线。
这轮把 metadata transition promotion 从缺少 checker evidence 推进到隔离 state 下十例真实 API promotion。
这轮将真实 RTL fault cohort 扩展至十例并完成 VCS repair elaboration。
这轮改进了 consumer context 的证据绑定和部分候选细化。
这轮没有完成所有共享资源的唯一根因定位。
这轮没有完成 production repair executor 的 promotion 集成。
这轮提高了 paired full suite 的覆盖并测得更重的完整顶层门限。
这轮的局部 RTL 节省未达到乐观预估。

因此下一步研究价值集中在补齐模型化依赖映射与生产接线。
不应继续把实验规则调到已测案例全匹配再把同一案例当独立证明。
不应为获得唯一根因数字而丢弃共享模块真实多义性。
不应将静态 promotion 改写为运行时设计正确。
后续设计应利用本轮 missed-file 和 ambiguous-node 清单选择独立验证集。
后续性能论文结论应基于实际 gate 组成、完整计时和明确运行条件。




# Embedded complete source report: Validation4 final result supplement

# Core Method Validation End Results — 2026-11-01

## Scope and evidence boundary

This report records execution of `accagent/docs/core_method_validation_end.md` (validation4). It is based on the GPT-2 Medium, sequence-length-32, W4A8, VU9P experiment snapshot used by validation3. The three workstreams were PropBench v5, TraceBench v7, and Paired Timing v5.

The experiment outputs are under `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation_20261031/`. The main machine-readable records are `propbench_v5/summary.json`, `tracebench_v7_metadata/summary.json`, `tracebench_v7_metadata/progress.json`, `tracebench_v7_rtl/summary.json`, `paired_timing_v5/summary.json`, and `validation4_integrity_audit.json`.

No new Chisel/SBT elaboration was run. Existing independent generated SV trees were reused. TraceBench VCS work was run remotely on `10.12.133.23`; local work was limited to Python analysis, hashing, small checks, and report generation. No RTL functional simulation, numerical comparison, synthesis, or board run was part of validation4.

The aspirational values embedded in the plan are not results. The measurements below retain misses, ambiguity, and costs as observed.

## PropBench v5

### Method

The runner reused the ten independent candidate trees already captured by PropBench v4. Before each retrospective manifest capture it checked candidate identity against the v4 record. The Stage-5 SV manifest binds the parameter signature, generated top-level SV membership, per-file SHA-256, generated `GeneratedDesignParams.scala` SHA-256, and a flat ANSI port/direction/range fingerprint. Each candidate's complete tree was then checked against the captured manifest.

For a partial-update negative case, the runner copied the candidate SV tree and its bound Scala source, replaced one changed SV file with the corresponding baseline file, and ran the exact manifest checker. This isolates file-level rollback detection. The manifest is retrospective: it was captured from the historical tree during this experiment and was not present when the historical Chisel run occurred.

Parameter-to-module-family rules were frozen before examining candidate diffs. These rules are template-family priors, not a learned semantic oracle. The measured quantities compare predicted families against actual changed file bytes. A byte change does not prove semantic dependence, and an unchanged byte does not prove semantic independence.

### Results

| Candidate | Changed parameter value | Changed SV files | Family-rule recall | Predicted-unrelated preservation | Partial revert detected |
|---|---:|---:|---:|---:|---|
| `rows_8` | rows 8 | 12 | 0.667 | 0.889 | yes, `Linear.sv` |
| `cols_16` | cols 16 | 15 | 0.533 | 0.806 | yes, `Linear.sv` |
| `fifo_128` | FIFO depth 128 | 7 | 0.857 | 0.955 | yes, `PhysicalStreamFifo.sv` |
| `banks_4` | activation banks 4 | 10 | 1.000 | 1.000 | yes, `PhysicalSimpleDualPortMemory_12.sv` |
| `rows_4` | rows 4 | 12 | 0.667 | 0.889 | yes, `DenseFFN.sv` |
| `cols_8` | cols 8 | 15 | 0.533 | 0.806 | yes, `DenseFFN.sv` |
| `cols_4` | cols 4 | 15 | 0.533 | 0.806 | yes, `DenseFFN.sv` |
| `fifo_32` | FIFO depth 32 | 4 | 1.000 | 1.000 | yes, `PhysicalSimpleDualPortMemory_19.sv` |
| `banks_8` | activation banks 8 | 10 | 1.000 | 1.000 | yes, `PhysicalSimpleDualPortMemory_12.sv` |
| `reuse_2` | cross-token reuse 2 | 12 | 0.500 | 0.842 | yes, `Linear.sv` |

Complete candidate manifests passed **10/10**. One-file partial rollback was rejected **10/10**. The mean declared-family byte-change recall was **0.729** and mean predicted-unrelated preservation was **0.899**. These figures are useful as a first measured dependency-rule baseline; they do not support a claim of 100% parameter propagation accuracy. The compute-array rules miss generated wrapper and memory files, the FIFO family misses a `ResidualAdd` change, and the reuse family misses memory files. Those are real observed gaps, not discarded outliers.

The prior Stage-4/Scala binding checker still passes the partial SV rollback in all ten cases (`old_binding_check.partial=pass`), while the new file manifest rejects each mixed-version tree. This directly shows which error class the file manifest detects. The retrospective manifest's protection depends on recording a trusted manifest at generation time in future production runs; the current benchmark does not retroactively prove that historical Stage-5 artifacts were originally protected.

### PCWM warning policy replay

The existing four top-level elaboration records were re-read under a stricter experiment contract that treats any `PCWM-W` port-width warning as failure even when VCS returns zero. `rows_8` had 6 warnings and `cols_16` had 10, so each is classified as a contract failure under this policy despite historical tool return code 0. `fifo_128` and `banks_4` had zero warnings and remain pass. This is a reclassification of saved VCS evidence, not a fresh `-Werror=PCWM-W` invocation. A VCS command-line warning-promotion flag was not assumed or claimed.

## TraceBench v7

### Metadata-contract arm

Ten prior stream-contract metadata faults were repaired in isolated SACG transitions. Each case ran the native pipeline static checker, native Stage-6 static stream-plan and data-order-ledger checkers, the existing remote `vlogan` source compile, and the actual `SACGStore.promote()` call. Results: **10/10 fault detected, 10/10 downstream and upstream edge endpoints included, 10/10 static repair checks pass, 10/10 remote `vlogan` pass, 10/10 promoted, zero scope violations**. Archived module-to-stage mapping replay also covered 10/10 archived syntax reports; it used no new EDA execution.

The `data_order_trace_check` in these cases is a native static ledger check. It does not run an RTL simulation or establish numerical/data-order behavior at runtime. The injected fault is a metadata mismatch explicitly reported by `check_edge_contracts`; this is checker-assisted repair, not blind root-cause discovery.

### Generated RTL port-fault arm

The ten-module cohort replaced the old uninstantiated outer `GeneratedAxiDdrTop` sample with `DenseFFN`, which has an in-package consumer. Each case independently changed one producer port name while retaining named-port labels in its consumer, ran remote VCS elaboration with the generated source closure, derived the patch from the VCS diagnostic and actual consumer declaration, authorized the exact changed file, then reran VCS and native package checks.

| Case | Producer | Initial graph candidates | Refined candidates | Projection basis | Fault VCS | Repair VCS | Promoted |
|---|---|---:|---:|---|---:|---:|---|
| F1 | `DenseFFN` | 2 | 2 | shared consumer ownership retained | 255 | 0 | yes |
| F2 | `GeneratedAcceleratorTop` | 2 | unresolved / retained original candidates | top-boundary consumer not uniquely stage-mapped | 255 | 0 | yes |
| F3 | `Attention` | 1 | 1 | unique candidate; no consumer owner | 255 | 0 | yes |
| F4 | `IntegerAttention` | 1 | 1 | producer/consumer owner intersection | 255 | 0 | yes |
| F5 | `Linear` | 1 | 1 | unique graph-bound consumer owner | 255 | 0 | yes |
| F6 | `Activation` | 1 | 1 | unique candidate; no consumer owner | 255 | 0 | yes |
| F7 | `ResidualAdd` | 1 | 1 | observed data connection plus graph predecessor | 255 | 0 | yes |
| F8 | `PhysicalStreamFifo` | 2 | 2 | shared producer/consumer ownership retained | 255 | 0 | yes |
| F9 | `WeightTileCache` | 2 | 2 | shared producer/consumer ownership retained | 255 | 0 | yes |
| F10 | `QKVProjection` | 1 | 1 | unique candidate; no consumer owner | 255 | 0 | yes |

Aggregate results: **10/10 executed; 10/10 fault elaborations failed with the intended connection diagnostic; 10/10 repaired elaborations returned 0; 10/10 exact-file authorizations; 0 scope violations; 10/10 native static promotions**. All fault and repair arms also had `vlogan` return 0. The runner checks local, uploaded, and remote source manifests through the existing helper and preserves per-case logs, patch, evidence records, and source hashes.

Consumer context is now accepted only when its source hash and artifact origin bind to the graph and the same hashed tool log contains the reported producer, instance, consumer location, and undefined-port diagnostic. A focused regression test verifies valid narrowing and rejects an invented instance.

The table is not a 10/10 unique-root result. DenseFFN, `PhysicalStreamFifo`, and `WeightTileCache` retain multiple stage candidates; the outer generated top also does not resolve to one stage. Some one-candidate rows were already unique before the consumer projection. The best evidence for actual added disambiguation is `ResidualAdd` F7, where the consumer's connected input and the graph predecessor select the first residual stage without relying on an `add1`/`add2` suffix rule. Repair success is a deterministic benchmark edit from compiler/source evidence, not an autonomous LLM repair. Promotion occurred on isolated benchmark states and does not show integration of the new authorization path into the production repair executor.

## Paired Timing v5

The full suite contains the six prior checks plus a remote `GeneratedAcceleratorTop` VCS elaboration with the XPM simulation source. The local targeted elaboration uses `DenseFFN`. Both elaboration helpers include fresh remote `vlogan` analysis; this cost is included in the measured gate. The four arms use paired, isolated snapshots. Hashing and resolver planning are included in targeted time; snapshot preparation is excluded.

| Mutation | Targeted gates | Targeted seconds | Full 7-gate seconds | Time reduction |
|---|---|---:|---:|---:|
| E1 documentation | none after resolver reports empty invalidation | 0.01799 | 32.11772 | 99.944% |
| E2 pipeline metadata | pipeline static checker | 0.02117 | 32.03216 | 99.934% |
| E3 parameter binding | DSE materialization checker | 0.01941 | 32.07468 | 99.939% |
| E4 Activation SV comment | package static + remote `vlogan` + `DenseFFN` elaboration | 16.72969 | 31.98947 | 47.703% |

Baseline seven gates and every selected/full arm passed; all four cases retained equal before/after source hashes across the paired executions. The `E1` resolver selected no validation gate because the documentation edit invalidated no registered evidence; its 0.018 s is planning/hash overhead, not a checker run. E4 did **not** reach the plan's predicted 80% saving. It is a comment-only RTL mutation and the test compares local `DenseFFN` elaboration with full top elaboration; this does not establish that any arbitrary internal RTL logic change is safe with local-only validation. The timing result is for the explicit experimental dependency registry and these four mutations, not an end-to-end production acceleration guarantee.

## Implementation and validation changes

- Added `build_stage5_sv_manifest()` and `validate_stage5_sv_manifest()` in `accagent/framework/dse_materialization.py`. The checker detects file membership/hash changes, parameter signature mismatch, Scala binding drift, and generated flat ANSI port fingerprint changes. It is not a full SV parser or semantic equivalence checker.
- `generate_code()` records a manifest only after successful Stage-5 compile/elaboration; the package static checker compares it against the independently recorded `generated_top.params` binding. The v5 benchmark's historical manifests remain explicitly retrospective.
- Added predeclared parameter-family rules and byte-change recall/preservation calculations. The rules missed changes as shown above; they remain a baseline for further graph work, not production propagation truth.
- Extended `build_static_failure_context()` to verify consumer source, graph artifact origin, source hash, tool-log hash, and that the same VCS report names the producer/instance/consumer. Valid evidence can narrow candidates; unresolved shared ownership stays unresolved.
- Added `validation4_evidence.py`, which runs native static checkers, records only observed results, and calls the real promotion method. Historical Stage-5 compile evidence is reused only after exact SV and Scala byte identity checks; it is marked `fresh_execution: false`.
- Added remote TraceBench v7 runners and an independent 59-check artifact consistency audit.

## Verification performed

- `tests/test_stage5_sv_manifest.py`: 6/6 passed.
- `tests/test_stage_artifacts.py`: 13/13 passed.
- `tests/test_sacg_cctg_causal_slice.py`: 15/15 passed, including new valid/forged consumer-context cases.
- `audit_validation4_results.py`: **59/59 consistency checks passed** over candidate manifests, partial reverts, promotion evidence-log hashes, remote source bindings, paired timing gates, and shared-source hashes.
- VCS remote executions are compile/elaboration-only; each per-case result and raw log is stored under the experiment output directories.

## Conclusions supported by this run

This run supports the narrower claims that a generation-time SV manifest can detect a later mixed-version file tree; declared parameter-family rules can predict some, but not all, changed generated files; actual compiler consumer diagnostics can support bounded graph candidate refinement; native static evidence can satisfy the isolated SACG transition's required checks; and targeted compile/elaboration work can save time on the tested mutation classes.

It does not support a universal 100% parameter propagation rate, a 10/10 unique graph root-cause localization rate, autonomous LLM repair, runtime CCTG diagnosis, numerical correctness, exact-board simulation, arbitrary-RTL targeted validation safety, a fresh warning-as-error VCS policy run, or production repair-executor promotion integration. These limits should remain visible in any paper table or text.




# Embedded complete source report: Validation5 standalone aggregate result

# Core Method Validation End2: Validation5 Results

Date: 2026-11-02
Experiment root: `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation5_20261102/`

## Executive results

All three planned Validation5 workstreams completed. Their measurements are mixed and do not reach several numeric expectations stated in the planning document. The raw artifacts and per-workstream result pages are retained in this directory.

| Workstream | Main observed result | What it supports |
|---|---|---|
| PropBench v6 hierarchy ablation | Macro recall/preservation rose from 0.729/0.899 for the flat rule to 0.817/0.922 for a static two-parent-hop closure; micro recall rose from 0.679 to 0.777. | This topology-based closure predicted more observed changed files in these ten archived cases, with remaining misses. |
| Paired Timing v6 | E1-E3 metadata/document targeted checks took 0.024-0.028 s versus 29.44-29.65 s full; E4/E6 took about 13.18 s targeted versus 29.27-29.35 s full (about 55% saved); E5 failed in both arms and was detected by VCS elaboration. Integrity audit 48/48. | The tested local compile/elaboration checks were faster for these cases and detected this port-mismatch fixture; they do not establish general gate equivalence. |
| TraceBench v8 LLM ablation | Both B0 and ACCORD reproduced 10/10 faults and passed VCS compile/elaboration on 8/10 repairs. Promotion passed 5/8 attempted B0 repairs and 6/8 attempted ACCORD repairs. Both used 15 requests (1.5/case); no scope-violation proposal or consumer edit occurred in either arm. | Real LLM repair and native promotion were exercised on the archived cases, but the sample shows no VCS pass-rate gain and no evidence that ACCORD prevented unauthorized edits. |

## PropBench v6 hierarchy ablation

The experiment re-scored ten archived PropBench v5 candidate packages using candidate-versus-baseline SHA-256 differences as the observed changed-file labels. The predictor used frozen parameter-family priors and an independently parsed baseline RTL instantiation topology. It emitted predictions before reading per-case gold labels. The two-hop predictor followed instantiating-parent edges from primary seed files to a maximum of two edges; it did not infer width-coupling edges or add edges after inspecting misses.

| Predictor | Macro recall | Macro preservation | Micro recall |
|---|---:|---:|---:|
| Primary family, conditional on changed files in that family | 1.000 | n/a | n/a |
| Primary family, all changed files | 0.729 | 0.899 | n/a |
| Existing flat one-hop rule | 0.729 | 0.899 | 0.679 |
| Static instantiation closure, up to two parent edges | 0.817 | 0.922 | 0.777 |

The gain is +0.088 macro recall and +0.023 macro preservation over the recomputed flat rule. `GeneratedAxiDdrTop.sv` remained beyond the two-hop reach for rows/cols cases, and multiple `PhysicalSimpleDualPortMemory` files changed due to width coupling that the topology did not encode. For reuse=2, the two-hop set did not improve recall and preservation was lower than flat. This is a ten-case byte-difference prediction result, not semantic dependency completeness, causal necessity, or an agent propagation accuracy measurement. No SBT, VCS, synthesis, or runtime simulation was run for this static analysis.

Detailed cases and topology are in `propbench_v6_hierarchy_ablation/RESULT.md`, `summary.json`, `rtl_topology.json`, `predictions.json`, and per-case JSON files.

## Paired Timing v6

Each paired case ran targeted and full gates against its arm-specific source snapshot. The runner reused each arm's `vlogan` work library for its subsequent VCS elaboration, avoiding a second `vlogan`. Full checks took about 29-30 seconds for passing cases. The measured results were:

| Case | Targeted (s) | Full (s) | Saved | Outcome |
|---|---:|---:|---:|---|
| E1 documentation | 0.024888 | 29.652226 | 99.9161% | PASS/PASS |
| E2 pipeline metadata | 0.027563 | 29.546097 | 99.9067% | PASS/PASS |
| E3 parameter-binding source | 0.024277 | 29.438978 | 99.9175% | PASS/PASS |
| E4 RTL comment | 13.179352 | 29.269763 | 54.9728% | PASS/PASS |
| E5 Activation port mismatch | 6.866355 | 7.725732 | 11.1236% | expected FAIL/FAIL |
| E6 Activation repair | 13.179090 | 29.347668 | 55.0932% | PASS/PASS |

E5 returned `vlogan=0`, `VCS=255` and both elaboration logs contained `UPIMI-E`; E6 restored the producer port and both arms returned zero. E6 used E5 as the fault comparison snapshot. A 48-check integrity audit passed. The fixture was initially read from a v6 path; byte-level comparisons and archive hashes established equivalence to the required v7 fixture, with the provenance correction recorded in `paired_timing_v6/fixture_provenance.json`.

These are single wall-clock compile/elaboration trials. E1-E3 have tiny targeted times because only the selected metadata/document gate ran. E4/E6 saved about 55%, below the planning document's unmeasured 70% expectation. E5 did not demonstrate a speed benefit because both policies failed, with only about 11% timing reduction. The experiment does not establish general production dependency resolution, RTL runtime behavior, numerical correctness, synthesis, P&R, or board execution.

Detailed evidence is in `paired_timing_v6/RESULT.md`, `summary.json`, `summary.csv`, per-arm logs/manifests, `integrity_audit.json`, and `fixture_provenance.json`.

## TraceBench v8 real-LLM ablation

Ten archived TraceBench v7 port-mismatch cases were independently unpacked for B0 and ACCORD. Each of 20 arm-case rows reproduced the injected failure through remote VCS. The actual active configuration for both arms was OpenAI `gpt-6.1-sol`, Responses API, endpoint host `www.a8pi.com`. The historical source cohort records `claude-opus-5`; this experiment therefore does not measure Claude behavior.

| Metric | B0 raw-log only | ACCORD DCG-bounded |
|---|---:|---:|
| Initial faults reproduced | 10/10 | 10/10 |
| Post-repair VCS compile/elaboration pass | 8/10 | 8/10 |
| Native `SACGStore.promote()` pass | 5/8 attempted | 6/8 attempted |
| Actual model requests | 15 | 15 |
| Mean requests per case | 1.5 | 1.5 |
| Scope violation proposals observed | 0/10 | 0/10 |
| Consumer edits applied | 0/10 | 0/10 |

No VCS pass-rate improvement was observed for ACCORD. The promotion difference is descriptive for this sample only. Since no B0 or ACCORD response attempted a consumer edit, the experiment does not show that the scope boundary prevented a violation. Some VCS-passing repairs did not satisfy promotion because required `codegen_compile_gate` evidence was missing: B0 F4/F6/F8 and ACCORD F3/F6. VCS elaboration pass must not be reported as semantic correctness or promotion.

Two process incidents affect interpretation. First, both initial F1 ACCORD requests returned HTTP 502 with an explicit context-window error because the request included about 3.92 MB of full RTL/graph context. Those requests count against the cap. The runner then changed to bounded local source excerpts shared by both arms; ACCORD additionally received DCG context and authorized-file information. Second, F2 model responses in both arms were initially rejected by an executor that required exactly one patch. After fixing multi-patch handling, the already saved responses were replayed and VCS was rerun without additional model calls. These post-hoc replays are separately recorded and must not be described as successful live first-pass executions. The replay audit was 2/2.

The machine-readable integrity audit confirms 20 rows, request caps, 20 initial reproductions, VCS/source binding for counted pass rows, consistent provider/model metadata, and 30 request records. The full source patches, model request/response records, initial and post-repair logs, manifests, replay records, static checker results, and promotion reports remain in the per-case directories.

Detailed results are in `tracebench_v8_agent_ablation/RESULT.md`, `llm_ablation_summary.json`, `metrics.json`, `integrity_audit.json`, `saved_response_replay_audit.json`, and the case folders.

## Overall limits and safe claims

- These experiments cover archived GPT-2 Medium seq32 generated-source snapshots. They do not establish generalization to other models, boards, providers, or arbitrary source changes.
- PropBench measures file-level content changes, not semantic or causal dependency truth.
- Paired Timing measures single compile/elaboration wall-clock trials; targeted/full outcome agreement on E1-E6 is a small case set and does not establish a general production gate-equivalence theorem.
- TraceBench uses actual model responses but shows equal B0/ACCORD VCS pass rates, no observed scope violation in either arm, and evidence-contract promotion failures. It does not prove DCG-guided root-cause accuracy or prevented collateral edits.
- None of Validation5 ran RTL runtime simulation, numerical comparison, synthesis, place-and-route, or FPGA board execution.
- Expected metrics and narrative in `core_method_validation_end2.md` remain planning expectations, not measurements. Report the observed values above without tuning definitions or excluding failures after the fact.

## Reproduction and artifact map

- `propbench_v6_hierarchy_ablation/`: static predictor, parsed topology, per-case predictions and scores, result report.
- `paired_timing_v6/`: paired runner, source provenance, command manifests, logs, summary, 48-check audit.
- `tracebench_v8_agent_ablation/`: initial fault reproduction, actual LLM request/response files, patches, remote VCS results, replay audit, promotion reports, final aggregate audit.
- `docs/context_2026-03-27.md`: chronological continuation checkpoint with this round's results and process notes.




# Embedded complete source report: Validation5 TraceBench final case and methodology report

# TraceBench v8 Agent Ablation Results

## Scope and setup

This experiment compared two repair branches over ten archived TraceBench v7 RTL port-mismatch cases (F1-F10): B0 received raw failure-log context and bounded source excerpts without DCG producer projection or write authorization; ACCORD received the same source excerpts plus static DCG context and an authorized-file list. Both used the active framework LLM configuration: provider `OpenAI`, model `gpt-6.1-sol`, Responses API, endpoint host `www.a8pi.com`. This differs from the historical source run, whose saved transaction names `claude-opus-5`; this experiment is not evidence about Claude.

Each branch independently reproduced each injected fault using remote VCS before requesting a repair. The limit was two actual LLM requests per arm and case, counting interrupted requests. The final experiment used 30 requests across 20 arm-case rows, or 1.5 requests per case on average in each arm. All 20 initial faults reproduced. The machine-readable data are in `llm_ablation_summary.json`, `metrics.json`, `integrity_audit.json`, and the per-case directories.

## Aggregate results

| Metric | B0 raw-log only | ACCORD DCG-bounded |
|---|---:|---:|
| Cases | 10 | 10 |
| Initial faults reproduced | 10/10 | 10/10 |
| Post-repair VCS compile/elaboration pass | 8/10 | 8/10 |
| `SACGStore.promote()` pass | 5/8 attempted | 6/8 attempted |
| Actual LLM requests | 15 | 15 |
| Mean requests per case | 1.5 | 1.5 |
| Scope-violation proposals observed | 0/10 | 0/10 |
| Consumer edits applied | 0/10 | 0/10 |

These results do not show a VCS pass-rate advantage for ACCORD in this sample. The one-case promotion difference is descriptive only. Neither arm attempted a consumer-file edit, so this run does not demonstrate that ACCORD prevented unauthorized edits or consumer corruption. B0 had no write lock; the absence of an observed violation is not evidence that unbounded repair is safe.

The cases with no patch were B0 F1/F3 and ACCORD F1/F4. The other eight cases in each arm reached VCS compile/elaboration pass. Passing VCS is not equivalent to a complete semantic repair: B0 F4/F6/F8 and ACCORD F3/F6 did not pass native promotion. Their source patches and checker reports are preserved case by case. Promotion evidence and failure reasons are in each case's `promotion_result.json` and `llm_repair_result.json`.

## Execution incidents and provenance

- **F1 context-window failure:** the initial ACCORD prompt included full generated RTL and graph context, measured at about 3.92 MB. Both real requests returned HTTP 502 with an upstream response explicitly stating that input exceeded the model context window. These calls count against the case budget. The runner was then changed to use bounded local source excerpts; both arms receive the same source excerpts, while ACCORD alone receives the extra DCG context and authorized-file list. The original failures remain recorded.
- **F2 executor correction and replay:** both arms produced real multi-patch model responses, but the original executor accepted only a single patch and rejected the proposals. The executor was corrected to apply multiple patches, and the already-saved model responses were replayed without issuing extra LLM calls. Both replayed repairs passed remote VCS; ACCORD promoted. This is a post-hoc saved-response replay, not a successful first-pass execution of the original live runner. Original rejection records, response hashes, replay audit, patches, manifests, VCS logs, and promotion evidence are retained. The replay audit reports 2/2.
- **Promotion failures after VCS pass:** ACCORD F3 and F6 passed VCS elaboration but failed promotion because the required `codegen_compile_gate` evidence was absent. They must not be described as successful promotion or as fully verified semantic repairs. B0 F4/F6/F8 have the same missing-evidence promotion failure.
- **No provider substitution:** the experiment used the active environment-resolved OpenAI endpoint/model for both arms. It did not use the historical Claude model or change global provider configuration.

## Integrity checks

`integrity_audit.json` records: 20/20 arm-case rows present; each row within the two-request cap; all initial faults reproduced; every row counted as a VCS pass is bound to its new remote VCS result and source manifest; and all request records identify the same provider/model. It records 30 total request files. The audit does not claim semantic correctness, unique root-cause localization, or hardware runtime correctness.

## Interpretation and limits

This is a small ten-case compile/elaboration ablation using archived fault fixtures and one active LLM configuration. The observed equal 8/10 VCS pass rates and zero scope violations in both arms do not support a claim that DCG context improved repair pass rate or that scope bounding prevented consumer corruption. The 5/8 versus 6/8 promotion counts are descriptive and include evidence-contract failures after elaboration; they do not establish a statistically supported benefit. The experiment also does not evaluate Claude, RTL simulation, numerical correctness, synthesis, place-and-route, or board execution.

The strongest supported statements are that (1) all ten archived faults were reproducible independently in both branches, (2) actual LLM-assisted repairs reached VCS compile/elaboration pass in eight cases per branch under the recorded conditions, (3) the framework's native promotion gate rejected several VCS-passing repairs when required evidence was missing, and (4) this sample did not observe any consumer-edit proposal in either arm. Do not substitute the plan's expected outcome for these measured results.




# Embedded complete source report: Validation5 PropBench detailed result report

# PropBench v6: Hierarchy Ablation

## Measurement

This static analysis re-scores the 10 archived PropBench v5 candidate SV packages. No Chisel/SBT generation, VCS, or synthesis was run. Gold changed files are defined only by candidate-versus-baseline SHA-256 differences. The predictor emits its sets from frozen parameter-family priors and the independent baseline RTL module-instantiation graph before it reads the per-case changed-file labels.

Topology source: `/home/remote/workspace/Qwen2-Accelerator/accagent/experiments/gpt2_medium_seq32_20261027/method1_seq32_20261029_supplement/T7-cross-token-reuse-1/ACCORD/run/generated/chisel`. The parser found 47 RTL files, 47 module definitions, 57 unique module-type edges, and 4152 syntactic instantiation sites.

## Results

Macro averages over cases; preservation is specificity among predicted-unaffected files, aligned with v5's convention.

| Predictor | Recall | Preservation |
|---|---:|---:|
| Primary family, conditional on changed primary-family files | 1.000 | — |
| Primary family, all changed files | 0.729 | 0.899 |
| Existing v5 1-hop flat rule (recomputed) | 0.729 | 0.899 |
| RTL topology closure, exactly up to 2 instantiation edges | 0.817 | 0.922 |

The v5 recorded macro values are 0.729 recall and 0.899 preservation. Micro recall is 0.679 for flat rules and 0.777 for two-hop closure.

## Per-case

| Case | Primary conditional recall | Primary all-change recall | Flat recall / preservation | 2-hop recall / preservation | 2-hop misses |
|---|---:|---:|---:|---:|---|
| banks_4 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | none |
| banks_8 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | none |
| cols_16 | 1.000 | 0.533 | 0.533 / 0.806 | 0.667 / 0.844 | GeneratedAxiDdrTop.sv, PhysicalSimpleDualPortMemory_14.sv, PhysicalSimpleDualPortMemory_28.sv, PhysicalSimpleDualPortMemory_4.sv, PhysicalSimpleDualPortMemory_6.sv |
| cols_4 | 1.000 | 0.533 | 0.533 / 0.806 | 0.667 / 0.844 | GeneratedAxiDdrTop.sv, PhysicalSimpleDualPortMemory_14.sv, PhysicalSimpleDualPortMemory_28.sv, PhysicalSimpleDualPortMemory_4.sv, PhysicalSimpleDualPortMemory_6.sv |
| cols_8 | 1.000 | 0.533 | 0.533 / 0.806 | 0.667 / 0.844 | GeneratedAxiDdrTop.sv, PhysicalSimpleDualPortMemory_14.sv, PhysicalSimpleDualPortMemory_28.sv, PhysicalSimpleDualPortMemory_4.sv, PhysicalSimpleDualPortMemory_6.sv |
| fifo_128 | 1.000 | 0.857 | 0.857 / 0.955 | 1.000 / 1.000 | none |
| fifo_32 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | none |
| reuse_2 | 1.000 | 0.500 | 0.500 / 0.842 | 0.500 / 0.818 | PhysicalSimpleDualPortMemory_13.sv, PhysicalSimpleDualPortMemory_14.sv, PhysicalSimpleDualPortMemory_25.sv, PhysicalSimpleDualPortMemory_28.sv, PhysicalSimpleDualPortMemory_4.sv, PhysicalSimpleDualPortMemory_5.sv |
| rows_4 | 1.000 | 0.667 | 0.667 / 0.889 | 0.833 / 0.938 | GeneratedAxiDdrTop.sv, PhysicalSimpleDualPortMemory_6.sv |
| rows_8 | 1.000 | 0.667 | 0.667 / 0.889 | 0.833 / 0.938 | GeneratedAxiDdrTop.sv, PhysicalSimpleDualPortMemory_6.sv |

## Interpretation and limits

Primary-family conditional recall is deliberately reported separately: it answers whether the frozen operator/memory families cover changed files that already lie in those families. It does not describe whole-package recall. The all-change score exposes files outside the primary families.

The hierarchy result uses a hard two-parent-edge maximum from primary seed files. It does not traverse downward to children or sideways to siblings and adds no inferred buffer-coupling edges. The static topology therefore cannot represent width-coupled buffer relationships unless they are reached as true parent edges. It is not expanded after observing misses. Any missed parent above that depth remains a miss, even if an additional graph hop would reach it. This prevents the experiment from being tuned to the observed gold set.

The graph is parsed from an independently selected baseline SV package. Prediction uses only module instantiation structure and frozen parameter-family bindings; no candidate hash or gold changed label is used to add edges. The current static graph does not encode width-expression coupling, so it cannot establish that every syntactically adjacent module must change when a parameter changes.

These metrics are byte-difference prediction metrics on ten archived cases. They do not establish semantic dependency completeness, agent accuracy, functional correctness, or causal necessity. The topology parser is syntactic and file-level; it is not equivalent to VCS elaboration.

Artifacts: `run_propbench_v6.py`, `rtl_topology.json`, `summary.json`, and one JSON result per case.




# Embedded complete source report: Validation5 Paired Timing detailed result report

# Paired Timing v6 Results

Completed 2026-11-02. The isolated runner completed all six cases and the integrity audit passes **48/48** checks. Existing v5 runner/results and global result/context documents were not modified.

| Case | Targeted (s) | Full (s) | Saved | Full/targeted | Result |
|---|---:|---:|---:|---:|---|
| E1 documentation | 0.024888 | 29.652226 | 99.9161% | 1191.416x | PASS/PASS |
| E2 pipeline metadata | 0.027563 | 29.546097 | 99.9067% | 1071.946x | PASS/PASS |
| E3 parameter binding source | 0.024277 | 29.438978 | 99.9175% | 1212.637x | PASS/PASS |
| E4 RTL comment | 13.179352 | 29.269763 | 54.9728% | 2.221x | PASS/PASS |
| E5 Activation port mismatch | 6.866355 | 7.725732 | 11.1236% | 1.125x | expected FAIL/FAIL |
| E6 Activation repair | 13.179090 | 29.347668 | 55.0932% | 2.227x | PASS/PASS |

E5 returns `vlogan=0` in both arms and `VCS=255` in both arms. Both elaboration logs contain `Error-[UPIMI-E]`. E6 restores the producer port; both arms return zero. E6 explicitly uses the E5 fault run as its comparison snapshot.

## Work-library reuse

Within each case and arm, the SV sources and XPM model are analyzed once by `vlogan`. The subsequent `vcs` command uses that same remote case/arm directory and work library; it makes zero additional `vlogan` invocations. Targeted E4/E5/E6 elaborate `DenseFFN`; the full arm elaborates `GeneratedAcceleratorTop`. The arms have separate remote work directories.

## Fixture and executed-source provenance

The first execution read the fixture path `tracebench_v6_rtl_v4/F6_Activation`; the plan requires `tracebench_v7_rtl/F6_Activation`. The two fixtures were compared byte-for-byte before accepting the measured paired cases as v7-source evidence:

- v7 `Activation.sv`, v7 `diagnosed_fault/Activation.sv`, v7 `fault.tar.gz` member, v7 fault tool manifests, and tested E5 Activation manifest: SHA-256 `5bef4c0758cd828c25c5ccc3ab3a2f208ba995c777fbed339e61aae78eba82a6`.
- v7 `working_sources/Activation.sv`, v7 `repair.tar.gz` member, v7 repair tool manifests, tested E6 Activation manifest, and paired baseline Activation: SHA-256 `6056e2dbab309a0096aa3d94f7bed3553d113079816a37db8c6268ee3028704d`.

`fixture_provenance.json` records the required v7 source and result paths, tar hashes, the initially read v6 path, and the content-equivalence evidence. `runner_source_executed.py` is the immutable copy of the runner used for these measurements; its SHA-256 is recorded in `fixture_provenance.json`. `run_paired_timing_v6.py` now points to the v7 fixture for any new reproduction. No completed tool result was relabeled or rerun.

## Files

- `summary.json`, `summary.csv`: paired gate outcomes and measured times.
- `runner.log`: case completion records.
- `baseline/results.json`: seven baseline gates.
- Per-arm JSON/log files: exact command arguments, return codes, stdout/stderr, source manifest bindings, and wall times.
- `E6_semantic_port_repair/source_patch.diff`: concrete port repair.
- `fixture_provenance.json`: source/tar/result/runner hashes and provenance correction.
- `integrity_audit.json`: 48 checks, all passed; `audit_results.py` reproduces the audit.

## Limits

This is one paired trial per case, not a timing distribution. E5 fails in both arms, so its measured reduction is only 11.12%. The E4/E6 saving is about 55%, below the plan's unverified forecast of 70% or more. The dependency registry is explicit and inherited from v5; this does not prove general automatic artifact-to-gate dependency inference. The local elaboration scope is specific to the tested Activation-to-DenseFFN connection. These are compile/elaboration checks only: no RTL runtime simulation, numerical correctness, synthesis, place-and-route, or board test was run.


