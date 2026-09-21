# SpatialAccAgent 方法设计文档

## 0. 文档状态

本文档保留为早期方法讨论和问题审计档案。它不定义当前运行流程，也不应作为
Stage 编号、DSE 语义、验证闭环或后端通过条件的执行依据。

当前正式方法和唯一可执行的连续 Stage 0--7 定义位于
`accagent/docs/methodology.md` 与 `accagent/framework/workflow_contract.py`。
本文后续出现的独立 Stage 8/9、first-candidate DSE、旧 checkpoint/hash gate 或
历史缺口描述均属于已归档的历史状态，不能与当前正式框架并列引用。

当前范围：

- 目标 workload：decoder-only Transformer block；
- 主要 case study：当前 OPT-125M FPGA spatial accelerator；
- 目标产物：可部署的 FPGA 加速器设计包，而不是零散 RTL 片段；
- 核心方法：SACG 控制、模板约束、证据驱动的设计闭环。

明确非目标：

- 不声称从自然语言生成任意芯片；
- 不声称“第一个 agent 设计 accelerator”；
- 不声称架构性能 SOTA，除非后续实验建立了严格公平的对比范围；
- 不把自由生成 RTL 作为主要机制。

## 1. 相关工作格局与证据边界

现有相关工作大致可以分成四类。

| 类别 | 代表系统 | 已经证明了什么 | 对我们问题的不足 |
| --- | --- | --- | --- |
| 通用 agent 框架 | AutoGen、MetaGPT、LangGraph、SWE-agent、OpenHands | 多 agent 角色、状态图、工具调用、代码仓库操作、checkpoint | 不表达硬件专用的 stream、beat、AXI、memory、timing、board 约束 |
| RTL / EDA agent | MAGE、RTLSquad、GPT4AIGChip | LLM 可以辅助 RTL/HLS 生成、仿真修复、多 agent 设计审查、候选代码生成 | 多数任务偏局部 RTL/HLS/模块级，不能闭合完整 FPGA 加速器设计包 |
| 长流程芯片 agent | Design Conductor 2.0 | 长时间运行的 agent harness 可以构建非平凡 inference accelerator case study | 贡献偏 broad automation，不等于针对 LLM spatial accelerator 的可复现实验方法 |
| 加速器编译器 / ADL | StreamTensor、Allo、Spatial、HeteroCL、ScaleHLS | 显式 IR、schedule、stream layout、HLS 生成、kernel fusion、runtime 生成很重要 | 通常假设输入已经是结构化 compiler IR，不管理文档、模板、日志、修复历史、后端报告、板上证据这些异构状态 |

本文档中使用的证据标签：

- `supported_by_source`：由本地论文、项目文档或公开论文/项目页面直接支持；
- `inference`：由多个来源推导出的设计判断；
- `speculation`：合理但需要实验验证的判断；
- `unknown`：目前还没有验证。

关键证据判断：

- `supported_by_source`：MAGE 使用多个专门 agent 和仿真/checkpoint 证据来提升 RTL 生成，但其 benchmark 主要是 RTL 模块级任务，不是完整 FPGA accelerator deployment。
- `supported_by_source`：RTLSquad 使用多 agent 角色和显式设计/评估讨论来提升 RTL 设计可解释性和 PPA 推理。
- `supported_by_source`：GPT4AIGChip 报告了 LLM 容易丢失长依赖、误解变量、忽略关键硬件细节，因此使用分解模板和 prompt demonstration。
- `supported_by_source`：Design Conductor 2.0 证明长流程 agentic accelerator construction 是可行的，同时也显示 verification、timing、数值差异处理和 human review 是主要瓶颈。
- `supported_by_source`：StreamTensor 说明普通 tensor shape 不足以表达 LLM dataflow accelerator，需要显式表达 stream layout、FIFO、DMA/runtime 和 kernel connectivity。
- `inference`：SpatialAccAgent 不应该定位成“更多 agent 生成更好 RTL”。更强的主张是：领域专用的约束状态可以防止、定位和修复 LLM spatial accelerator 设计中的跨层一致性漂移。

## 2. 研究问题

SpatialAccAgent 解决的是 agentic LLM spatial accelerator design 中的跨层一致性问题。

给定：

- 模型/架构说明；
- 量化策略；
- Chisel 算子模板；
- FPGA board 约束；
- DDR / AXI 接口约束；
- 真实 weights、activations、traces 和 runtime images；
- 仿真、综合、实现、板上运行日志；

如何让 agentic system 在以下 lowering 过程中保持约束一致：

```text
model semantics
-> spatial pipeline
-> Chisel / RTL modules
-> stream interconnect
-> DDR / AXI image
-> host runtime
-> simulation / backend / board evidence
```

并最终完成一个可部署 FPGA LLM accelerator 的设计闭环？

核心失败模式是 **consistency drift，一致性漂移**。

一致性漂移指的是：某个局部生成或修复步骤看似修好了当前 artifact，却悄悄破坏了另一个层级的假设。

典型例子：

- 修改 QKV 参数修复了某个模块，但破坏了 KV-cache memory layout；
- stream reorder 修复了 stage trace，但让 top-level consumer 的顺序解释失效；
- 为了 timing 插入 register，但没有同步延迟 `valid`、`last` 或 residual path；
- 放宽 tolerance 让 numeric compare 通过，但隐藏了错误 scale layout；
- 修 AXI base address 时修好了一个 window，却让另一个 DDR region overlap。

因此方法必须把这些隐含假设显式化、可检查化、可修复化。

## 3. 核心命题

SpatialAccAgent 是一个 SACG-controlled design closure system。

核心命题是：

```text
对 LLM FPGA spatial accelerator 而言，LLM agent 本身不能被信任为设计状态。
真正的设计状态必须是结构化设计约束图 + 绑定代码/配置产物 + 可执行验证证据。
```

因此框架状态定义为：

```text
S_t = (G_t, A_t, R_t)
```

其中：

- `G_t`：Spatial Accelerator Constraint Graph，也就是类型化设计状态；
- `A_t`：artifact set，包括 Chisel、生成 RTL、配置文件、trace、脚本、报告、board 资源；
- `R_t`：evidence set，包括 checker reports、tool logs、repair records、human approvals、benchmark records。

每个 agent 动作都是受约束的状态转换：

```text
S_t --action--> S_{t+1}
```

一个 transition 合法，必须声明：

- 它读取哪些 constraints；
- 它触碰哪些 constraints；
- 它创建或 invalidates 哪些 artifacts；
- promotion 之前需要哪些 checker/tool evidence；
- 如果是 repair action，它属于哪个 repair scope。

这使 SpatialAccAgent 区别于：

- 依赖 chat history 的 agent；
- 自由生成 RTL 的 agent；
- 纯 compiler IR lowering；
- 一次性 case-study automation。

## 4. SACG 作为控制平面

SACG 是框架的主动控制平面，不是被动日志。

形式化定义：

```text
G = (V, E, C, I, A)
```

其中：

- `V`：设计实体；
- `E`：跨实体关系；
- `C`：附着在节点和边上的 constraints；
- `I`：跨 transition 必须保持的 invariants；
- `A`：artifact bindings。

必要节点类型：

- `model_op`：LayerNorm、QKV、RoPE、attention、FFN、residual；
- `template`：可信 Chisel template 及 metadata；
- `processing_unit`：实例化硬件计算单元；
- `pipeline_stage`：空间流水线 stage；
- `stream_adapter`：FIFO、layout converter、reorder buffer；
- `memory_task`：DDR image、weight loading、KV-cache、output region；
- `runtime_task`：config register、host script、start/done protocol；
- `verification_task`：stage/top/system/board test；
- `backend_task`：synthesis、implementation、report parsing；
- `deployment_task`：bitstream loading 和 board benchmark。

必要边类型：

- `model_semantic`；
- `shape`；
- `numeric`；
- `template_binding`；
- `stream`；
- `beat`；
- `memory_layout`；
- `runtime`；
- `control`；
- `residual`；
- `kv_cache`；
- `liveness`；
- `backend`；
- `deployment`。

SACG promotion 规则：

一个 artifact 不能被视为当前有效产物，除非它影响到的所有 invariants 满足以下条件之一：

- 已经通过 checker；
- 明确标记为 `not_run`，并且当前状态不是 final claim；
- 被缺少工具、缺少 board、需要 human approval 等条件阻塞，并且阻塞被结构化记录。

对于论文中的最终成功 claim，`not_run` 不能算有效证据。

## 5. 设计约束集合

SACG 需要把关键设计约束表达成可以被 checker 直接消费的可审计对象。这里不用新的术语，直接用清楚的「约束」名词。

### 5.1 Model Rule

记录模型语义，避免误绑定。

- 模型族：OPT、GPT-2、LLaMA、Qwen、Gemma-like；
- block 结构：pre-norm / post-norm、residual 放置；
- attention 类型：MHA、GQA、MQA；
- position encoding：learned absolute、RoPE、sliding/local；
- MLP 类型：dense、GELU、ReLU、gated SiLU、gated GELU；
- bias 规则。

典型错误：

- 把 Qwen 的 GQA 当成 OPT 的 MHA。

### 5.2 Shape Rule

记录形状/规模约束。

- hidden size；
- intermediate size；
- layer 数；
- sequence length；
- Q/KV 头数与 head_dim；
- tile / lane 尺寸；
- stage window size。

典型错误：

- `num_heads % num_kv_heads != 0`；
- FFN 中间维度在 pipeline plan 里被吞掉；
- hidden/head/head_dim 在 model、template、runtime 中不一致。

### 5.3 Numeric Rule

记录数值格式和精度边界。

- activation dtype；
- weight dtype；
- accumulation dtype；
- output dtype；
- scale 布局；
- zero-point；
- bias domain；
- rounding 与 saturation；
- tolerance 策略；
- golden/output 期望。

典型错误：

- W4 scale stride 与数据打包一致，但 RTL address generator 不一致。

### 5.4 Template-Implementation Rule

记录算子到模板到代码实例化的连接规则。

- 哪个 template 实现哪个 model op；
- template 参数支持范围；
- 已绑定参数；
- IO 语义；
- latency / II 假设；
- 可改动范围；
- 禁止修改项；
- 必须通过的 checkers。

典型错误：

- 把 OPT 的 `QKVLinear` 直接用于 GQA，但没有表达 `num_kv_heads`。

### 5.5 Dataflow Sequence Rule

这是硬件设计的关键约束。

- token 顺序；
- head 顺序；
- tile 顺序；
- lane 顺序；
- `valid/ready` fire 关系；
- `st` / `last` 布局；
- data/address/control 对齐；
- producer-consumer 速率；
- FIFO 深度；
- residual / bypass path 的时延关系。

这个约束是区分通用文本 agent 与 spatial accelerator 工程的核心。系统必须知道每一次 `fire` 到底是哪一个 token、哪一个 head、哪个 lane。

典型错误：

- producer 按 head-major 发序列，consumer 按 token-major 解释；
- timing 修复改了 data 没改 `last`；
- residual path 比主 path 慢一个 token window。

### 5.6 Memory/Runtime Rule

记录外部可见内存和运行时约束。

- DDR 区域基址和大小；
- 对齐要求；
- burst 长度；
- 数据打包；
- bank/channel 映射；
- AXI ID 和总线宽度；
- runtime 寄存器布局；
- input/output window 偏移；
- board 可见的 start/done/status 语义。

典型错误：

- 阶段 golden pass 正常，但 board runtime 读到的是 stale DDR 区域。

### 5.7 Backend/Deployment Rule

记录综合到板卡部署的约束。

- 目标 FPGA part；
- 目标频率；
- 资源预算；
- 时序异常策略；
- synthesis / implementation 参数；
- 布局假设；
- bitstream 与 board smoke-test 要求。

典型错误：

- 为了修 timing 复制了大 buffer，导致 BRAM/URAM 超预算。

## 6. Agent 角色设计

Agent 必须是有边界的状态转换器，不是自由聊天协作者。

| Agent | 输入 | 输出 | 禁止行为 |
| --- | --- | --- | --- |
| Objective Agent | task spec、model family、target board | acceptance boundary、initial objective constraints | 偷偷降低 spatial pipeline 或 correctness criteria |
| Spec Extractor | docs、model config、quant spec | 初始 model/shape/numeric SACG | 只做自然语言 summary，不产出结构化 constraints |
| Template Librarian | template metadata、已有 Chisel | template binding candidates、template coverage gaps | 隐式使用 template 不支持的假设 |
| Spatial Architect | SACG、template candidates、board limits | pipeline stages、stream order、residual/KV plan | 把空间流水线退化成软件式顺序执行 |
| Parameter Binder / DSE Agent | design space、constraints、QoR target | legal parameter candidates 和资源/性能预测 | 随便取第一个值，不做 legality evidence |
| Memory/Runtime Planner | memory/runtime rule、board spec、runtime ABI | DDR image map、AXI windows、host config map | 修改 layout 但不更新 RTL/runtime/checkers |
| Chisel Composer | selected templates、binding plan | generated Chisel/top/wrapper artifacts | 自由重写可信 compute core |
| Verification Planner | SACG invariants、artifacts | stage/top/system/board verification tasks | 只测最新 symptom |
| Evidence Classifier | logs、traces、checker reports | failure class、violated constraints、root-cause hypothesis | 把 raw log 当成最终诊断 |
| Repair Planner | violation record、allowed scope | minimal patch plan 和 invalidation set | 大范围乱改、放宽 tolerance、未审批修改 golden |
| Backend Closure Agent | reports、constraints、tool scripts | timing/resource/board closure evidence | 不关联 constraints 地盲调 TCL |

当前 pre-stage safety gate 应定位为 policy gate。它可以判断某个 transition 是否违反 forbidden actions 或是否需要 human approval，但它不能成为设计正确性的来源。真正的 truth source 是 SACG 加 checker/tool evidence。

planning stage 可以在自身 checker evidence 还不存在时运行。它们的职责是产生 candidate artifacts。最终 promotion 必须依赖证据。

## 7. 端到端方法流程

### Stage 0：目标和边界定义

输出：

- target model family；
- sequence length；
- quantization policy；
- target FPGA/board；
- correctness oracle；
- forbidden simplifications；
- final-claim boundary。

对当前项目，默认边界是：

- 全模型、全层数；
- sequence length 先固定为 16；
- 保持现有 spatial pipeline semantics；
- 使用真实 weights 和真实数据；
- 保持对应型号板卡的 DDR/AXI-compatible flow；
- 默认要求不卡死且有有效输出，不要求和 floating-point 模型 bit-exact。

并且，在 `input_preparation` 阶段，板卡、量化和外部工具信息直接来自本次运行的固定输入材料目录：

- 板卡输入材料目录：`accagent/framework/input_materials/board/`
- 量化输入材料目录：`accagent/framework/input_materials/quantization/`
- 外部工具输入材料目录：`accagent/framework/input_materials/tools/`

这三个目录不是长期资料库，也不是默认背景知识。它们就是一次框架运行的输入材料。框架每运行一次就必须基于这些材料设计一个加速器，因此用户可以在每次运行前替换目录内容，表达不同模型、不同板卡、不同量化策略和不同工具环境。

当前 Stage 0 不再设置另一套独立的数值说明文件或板卡说明文件。量化目录中的全部内容就是 `numeric_policy_agent` 的输入；板卡目录中的全部内容就是 `board_profile_agent` 的输入；工具目录中的全部内容就是 `tool_profile_agent` 的输入。如果同一目录内的材料互相冲突，Stage 0 必须把冲突记录在 notes/errors 中，不能静默猜测。

这些目录是用户输入，不是框架常量。不同用户可以按自己的实验资源写入 Markdown、docx、PDF、样例工程说明或脚本说明。Stage 0 的子 agent 必须从这些材料中提取结构化信息：

- `target_board_profile.json`：板卡、FPGA part、DDR/AXI、runtime、远端环境；
- `numeric_policy.json`：量化策略，若没有资料则使用默认 FP16 权重/激活/scale 和 FP32 accumulation；
- `tool_profile.json`：VCS、Verilator、Vivado 等工具的位置、scope、host、executable、env、限制；
- `tool_protocols.json`：根据 `tool_profile.json` 生成后续可执行验证/综合命令。

框架不能把某个用户的服务器 IP、EDA 安装路径或 license 环境写死成默认事实。若资料没有给出某个字段，结构化结果应保持 `null` 或 pending evidence，而不是猜测。LLM 是 Stage 0 的必要能力：如果 LLM provider、endpoint、key、model 或调用结果不可用，Stage 0 必须停止并输出错误，不能用 deterministic fallback 冒充 agent 理解。

这些是默认必须满足的要求，后续阶段不能再把它们当成可选项，也不能用简化流程替代。若量化目录里没有新资料，系统按默认精度（FP16）运行。

### Stage 1：SACG 提取

输入：

- model config；
- architecture docs；
- quantization docs；
- template metadata；
- board specs；
- verification cases；
- existing runtime scripts。

输出：

- initial SACG；
- missing-field report；
- 需要 human approval 的 assumptions。

### Stage 2：模板覆盖和绑定

输入：

- SACG model ops；
- trusted template library；
- existing OPT Chisel modules。

输出：

- supported bindings；
- unsupported bindings；
- required adapters；
- template parameter ranges；
- forbidden edits。

对 OPT，baseline binding 应该是：

```text
LayerNorm -> LayerNormQ
QKV projection -> QKVLinear
Attention -> DM1 / Softmax / VCache / DM2
Output projection -> OutLinearFP32
Residual -> ResAddFP32 / ResAdd2FP32
FFN up -> FFNUp
FFN down -> FFNDownFP32
```

对 LLaMA/Qwen-like block，预期缺口包括：

- RMSNorm；
- RoPE；
- GQA/MQA head mapping；
- gated MLP；
- SiLU/GELU variants；
- bias-policy variants。

### Stage 3：空间架构规划

输出：

- processing-unit partition；
- stage schedule；
- token/tile/head/lane mapping；
- stream graph；
- residual alignment；
- KV-cache plan；
- double-buffering plan；
- initial resource and throughput hypothesis。

重要约束：

规划必须保持空间流水线。一个 token 进入后级 stage 后，后续 token 应该可以进入前级 stage，不能退化成等一个 token 完整跑完 block 后再启动下一个 token，除非某个显式依赖禁止 overlap。

### Stage 4：参数绑定和 DSE

输出：

- 合法 lane/tile/FIFO/buffer candidates；
- resource estimate；
- performance estimate；
- selected candidate；
- rejected candidate log。

Binder 不应该简单选择 design space 里的第一个值。它需要检查：

- template parameter legality；
- shape divisibility；
- stream/order consistency；
- memory alignment；
- FIFO/liveness constraints；
- resource budget；
- timing risk。

这里可以使用 multi-candidate generation。候选多样性可以由 LLM 提出，但 scoring 必须由 checker/QoR evidence 驱动，而不是由 LLM 偏好驱动。

### Stage 5：代码生成（Code Generation）

输出：

- Chisel 模块、加速器 top-level glue 代码；
- FPGA AXI/DDR-facing top wrapper；
- wrapper 输入/输出规则和板级接口连接规则；
- 由模板和参数绑定生成的加速器硬件代码包；
- code generation manifest。

规则：

Agent 可以生成 glue、wrapper、template instantiation、加速器顶层连接代码和 FPGA AXI/DDR-facing top wrapper。这里的 wrapper 属于加速器硬件代码的一部分，用来承接后续真实 DDR/AXI、顶层控制和板级 shell。真实 DDR image、runtime、testbench、backend 脚本放到后续验证和板级阶段生成或绑定。可信 arithmetic core 只有在显式 repair scope 下才能被修改。

### Stage 6：分层真实 workload 验证与修复

验证层级：

1. SACG lint；
2. template-binding check；
3. shape/numeric static check；
4. stage-level real data verification（每个模块独立，可并行）；
5. stream-trace and sequence-order verification；
6. DDR address-map verification；
7. stage 合并后的 top-level integration verification（逐层收敛）；
8. system-level DDR/AXI runtime verification；
9. functional simulation evidence：VCS 或 Verilator 至少一个真实工具通过；
10. Vivado synthesis / implementation；
11. board runtime smoke / benchmark。

必要性质：

每个 checker report 都必须回指 node IDs、edge IDs、constraints、invariants 和 artifacts。

这一阶段是框架里最耗时、最关键的一段：

- 先把每个 pipeline stage 当独立模块并行验证；
- 每层通过后再按依赖顺序合并上行层级；
- 验证通过的模块不允许被后续修复无约束改动，任何修改都必须有清晰的跨层影响声明；
- 若要改代码，优先保留原始模板结构，只在绑定、接口、时序对齐、adapter/runner/参数设置层面修正。

### Stage 7：证据驱动修复

每条 repair record 必须使用以下格式：

```text
symptom
-> evidence
-> violated_constraint
-> affected_artifacts
-> allowed_patch_scope
-> patch
-> invalidated_artifacts
-> regression_result
```

Repair scope：

- `auto_allowed`：glue code、config maps、generated tests、adapter insertion、bounded parameter changes；
- `approval_required`：golden changes、oracle changes、tolerance changes、compute-core edits、model semantics changes；
- `forbidden`：删除测试、绕过 checker、缺少必要证据却 claim final pass、削弱目标 spatial semantics。

### Stage 7：Vivado 实现与 QoR 闭环

对外输出仅保留四项 QoR 指标：`resources`、`power_w`、
`clock_frequency_mhz` 和 `performance_tokens_per_second`。Vivado 原始报告
仅作为这些指标的证据，不构成额外对外阶段产物。

Backend failures 应该转换成 backend/deployment rule violations，而不是散落在 Vivado log 中。

例子：

- QKV fanout timing fail -> 关联到对应 processing unit 和 stream edge 的 backend constraint；
- URAM 超预算 -> resource constraint violation；
- board timeout -> runtime/liveness/deployment rule violation。

## 8. OPT-125M Case Study 计划

现有 OPT accelerator 应该作为 empirical seed，而不是一堆非结构化文件。

### 8.1 反向结构化当前设计

为以下对象创建 SACG：

- 12-layer OPT model structure；
- 11-stage spatial pipeline；
- current stage windows；
- stream order 和 beat counts；
- DDR regions；
- weight packing；
- runtime configs；
- existing VCS/Verilator/Vivado scripts；
- board shell assumptions。

### 8.2 把当前 Chisel/RTL 绑定成模板

每个可复用模块都需要：

- template ID；
- template spec；
- bound parameters；
- IO rule；
- latency / II hypothesis；
- required checkers；
- known hardcoded assumptions。

### 8.3 复现现有流程

第一个成功标准不是生成全新架构，而是：

```text
给定结构化 OPT SACG，SpatialAccAgent 能复现现有设计包，
并运行相同验证/后端流程，同时产生可追踪证据。
```

### 8.4 使用真实故障测试修复能力

然后使用实际 OPT debug 历史和 fault injection 测试框架是否能：

- 分类 failure type；
- 指向正确 SACG constraint；
- 提出 minimal repair；
- 重新运行必要 regression；
- 避免 consistency drift。

这样方法才是实验驱动，而不是概念驱动。

## 9. 泛化计划

OPT 之后的泛化路线：

| 任务 | 目的 | 需要新增能力 |
| --- | --- | --- |
| GPT-2-small | 和 OPT 接近，但 activation / QKV layout 不同 | fused QKV layout adapter、GELU |
| LLaMA-like | 架构有实质差异 | RMSNorm、RoPE、GQA、gated MLP |
| Qwen2-like | 更难的 GQA 和参数变化 | 非 2 的幂 head count、qkv bias policy、大 RoPE theta |
| Quantization variant | 压力测试 numeric rules | W8/W4 scale layout、tolerance、packing |
| Platform variant | 压力测试 deployment rules | DDR width、AXI windows、board config |

论文不应该在至少一个非 OPT family 达到有意义的分层验证之前，声称广泛模型族支持。

## 10. 评估计划

### 10.1 端到端闭环

指标：

- generated artifacts；
- generated LOC vs human-edited LOC；
- stage/top/system/board pass status；
- real workload coverage；
- design time；
- agent transitions 数量；
- checker invocations 数量；
- human approvals 数量；
- final resource/timing/throughput metrics。

最低可信结果：

- OPT design package 被复现或生成，并带有真实验证证据；
- 至少一个结构不同的模型族达到 stage/top-level evidence；
- primary case 收集 backend/tool evidence。

### 10.2 Ablation

Ablation：

- no SACG；
- no dataflow sequence rule；
- no memory/runtime rule；
- no numeric rule；
- no evidence classifier；
- single-agent baseline；
- free-form RTL baseline；
- tests-only repair baseline。

指标：

- success rate；
- repair iterations；
- first-failure localization accuracy；
- patch size；
- regression failures；
- bugs escaping to later verification levels；
- human intervention count。

### 10.3 Fault Injection

注入错误：

- RoPE offset；
- GQA KV-head mapping error；
- W4 scale stride error；
- stream tile order reversal；
- missing beat；
- `last` delayed one cycle；
- FIFO depth too small；
- residual bypass misalignment；
- DDR base offset；
- AXI burst overrun；
- output window size mismatch；
- timing-register valid/data misalignment。

输出：

- detection rate；
- localization accuracy；
- repair success rate；
- average iterations。

### 10.4 QoR 和部署可行性

报告：

- Fmax；
- LUT / FF / DSP / BRAM / URAM；
- latency；
- throughput；
- DDR bandwidth efficiency；
- board power，如果可获得；
- board runtime status。

定位：

QoR 的作用是证明生成设计是真实、可部署的。除非对比严格公平，否则主 claim 仍然是 design-closure robustness 和 productivity，不是 peak accelerator performance。

## 11. 实现路线图

### Phase 0：证据和相关工作矩阵

交付物：

- prior-work table；
- threat matrix；
- claims allowed / not allowed；
- local evidence index。

### Phase 1：SACG Schema 强化

交付物：

- stable SACG JSON/YAML schema；
- structured design-rule objects；
- artifact freshness and invalidation model；
- transition record format；
- promotion rules。

### Phase 2：OPT 设计反向结构化

交付物：

- 当前 OPT accelerator 的 SACG；
- 当前模块的 template specs；
- 从 traces 中提取 stream order 和 transfer-count rules；
- 从现有 cases 中提取 DDR/runtime rules；
- 从 scripts/reports 中提取 backend/board rules。

### Phase 3：Checker Suite

交付物：

- SACG lint；
- template-binding check；
- stream-trace check；
- transfer-count check；
- addr-map check；
- numeric compare；
- liveness/deadlock check；
- backend report parser。

### Phase 4：模板约束生成

交付物：

- template instantiation generator；
- Chisel top composer；
- stream adapter generator；
- DDR/runtime config generator；
- verification artifact generator。

### Phase 5：证据驱动修复

交付物：

- failure taxonomy implementation；
- evidence classifier；
- repair scope policy；
- minimal patch planner；
- regression scheduler；
- repair record database。

### Phase 6：OPT 端到端闭环

交付物：

- full OPT real-workload verification run；
- remote VCS/Verilator evidence；
- Vivado synthesis/implementation evidence；
- board smoke evidence，如果可获得；
- design-time and repair metrics report。

### Phase 7：非 OPT 泛化实验

交付物：

- GPT-2 和 LLaMA/Qwen template gap closure；
- 至少一个非 OPT hierarchical verification result；
- ablation 和 fault-injection results。

## 12. 当前原型评估

当前 `accagent/framework` 有一些有价值的脚手架：

- staged agent execution；
- stage reports；
- LLM worker I/O；
- pre-stage safety gate hook；
- initial SACG store；
- tool-runner abstraction；
- template metadata；
- static checker skeleton。

但它还不是本文档定义的方法。

主要缺口：

- pipeline planning 太线性，没有真实表达 residual/KV/memory/liveness；
- parameter binding 不是真正的 DSE；
- code generation 目前主要生成 Chisel/package scaffold，还不是完整可上板代码生成闭环；
- verification 在真实工具未接入时主要是静态检查；
- template specs 不完整，很多算术模板还是 placeholder；
- artifact freshness 和 invalidation 需要系统性强制执行；
- current pre-stage safety gate behavior 不应决定设计正确性。

因此后续工程推进应该以“是否更接近 SACG-controlled design closure”为标准，而不是以 superficial stage list 是否 pass 为标准。

### 12.1 代码审计范围和结论快照（2026-06-28）

本小节记录的是当前源码的实际行为，而不是本文档前面章节中的目标设计。审计范围包括：

- 顶层编排：`accagent/framework/agent.py`、`stage_agent.py`、`agent_common.py`、`config.py`；
- SACG 状态和阶段入口：`sacg_store.py`、`sacg_utils.py`、`stage_entry.py`；
- 11 个当前阶段：`stage_input.py`、`stage_constraints.py`、`stage_templates.py`、`stage_pipeline.py`、`stage_params.py`、`stage_artifacts.py`、`stage_verification_plan.py`、`stage_verification.py`、`stage_repair.py`、`stage_backend.py`、`SACGValidationAgent`；
- LLM 和 team 层：`stage_llm.py`、`stage_team.py`、`llm_io.py`、`llm_client.py`；
- 工具执行：`tool_runner.py`；
- 模板库：`accagent/framework/templates/chisel/`。

当前框架已经具备一个“可串起来跑”的 agent/SACG/报告系统，但还不能被描述为已经完成硬件设计闭环。最重要的现实结论是：

- 当前流程是固定 11 个软件阶段，不是已经实现了目标硬件中的 11 级流水线；
- 当前 `pipeline_planning` 是按模板匹配结果生成一串算子 stage，对 Qwen 配置通常是一层 decoder block 内的若干 operator stage，不是 12 层模型的真实流水线调度；
- 当前真实工具证据可以被记录，但失败/缺失证据不会可靠阻断后续阶段，因为多个阶段的报告仍然写 `status: "ready"`；
- 当前 SACG 可以检查引用完整性，但还没有强制“最终 pass 必须有所有 required checker evidence”；
- 当前 Qwen real-weight 支撑只到 manifest/static gate/scaffold 层面，还不是“VCS 使用真实权重完成真实接口功能验证”；
- 当前 backend/board 阶段主要生成 handoff scaffold，不代表 Vivado、bitstream、board runtime 已闭环。

因此，目前可以合理声称的是：

- 框架有 staged orchestration、run-local report、SACG JSON 状态、transition/evidence/repair record 的基础结构；
- 框架能从 task/model/numeric/board/template 输入生成一版 SACG seed、模板选择、pipeline plan、参数绑定和 Chisel package scaffold；
- 框架能执行静态 checker 和配置在 tool protocol 里的外部命令，并把结果写成 evidence；
- 框架能识别一部分失败/未运行工具，并在 report 中记录。

目前不能声称的是：

- 已经完成真实权重的端到端功能仿真；
- 已经完成 12 层模型真实流水线推理验证；
- 已经完成与上板一致的 DDR AXI 读写流程验证；
- 已经完成自动修复闭环；
- 已经完成 Vivado 综合、布局布线、bitstream、板上 runtime 闭环；
- stage list 最终走完就等价于设计正确。

### 12.2 当前实际运行入口和状态流

当前入口是：

```bash
python3 -m accagent.framework.agent
```

`TopAgent` 不解析命令行参数。所有运行配置直接来自 `accagent/framework/config.py`。当前配置模型包括：

- `out`：run 输出目录；
- `design`：设计 ID；
- `task_spec`、`model_source`、`board_materials_dir`、`quantization_materials_dir`、`tool_materials_dir`、`template_dir`；
- `run_real_tools` 和 `tool_timeout_sec`；
- LLM 模式、endpoint、model、enforce policy。

这带来两个工程风险：

- 配置不可复现实验参数主要靠改 Python 源码，不适合多次实验对比；
- `config.py` 当前包含 API key 字段，应改成只从环境变量或本地 secret 文件读取，不能把真实 key 作为源码配置的一部分。

顶层控制流固定如下：

```text
input_preparation
constraint_extraction
template_selection
pipeline_planning
parameter_binding
code_generation
verification_artifacts
verification
repair
backend_board
sacg_validate
```

前 10 个阶段通过 `StageResult` 串联：

- 每个阶段写自己的 `report.json`；
- 每个阶段输出下一版 `sacg_state.json`；
- 后一阶段接收前一阶段的 `sacg_state.json`；
- 顶层最后写 `agent/agent_run_report.json`。

当前 pass 判定的关键问题在这里：

- `GenericStageAgent` 主要看阶段脚本返回码和 report 里的 `status == "ready"`；
- `run_sacg_stage()` 只把 `report["errors"]` 当成命令失败依据；
- `verification` 阶段即使 `result_status == "fail"`，顶层 report 仍可能是 `status: "ready"`；
- `repair` 阶段即使只是生成 repair plan、没有真正修复，也会写 `status: "ready"`；
- `backend_board` 阶段即使 `final_design_pass == false`，也会写 `status: "ready"` 并继续推进。

也就是说，当前“agent 跑完”只能说明阶段程序执行完毕，不等于设计 pass。

### 12.3 当前每个阶段实际做什么

| 阶段 | 主要源码 | 当前实际行为 | 当前缺口 |
|---|---|---|---|
| Stage 0 input_preparation | `stage_input.py` | 并行读取本次输入材料，生成 task card、model config、numeric policy、board profile、tool profile、template library、design space、tool protocols、human boundary。LLM 是必需能力，LLM 不可用时 Stage 0 停止。 | tool protocol 已有结构化 `execution.argv/cwd/env`，`script_exists` 会检查首个 executable/script；Stage 0 现在强制检查 VCS/Verilator、Vivado、board runtime、AXI/DDR 关键字段；pre-stage safety gate 和 team 输出不能替代 checker/tool evidence。 |
| Stage 1 constraint_extraction | `stage_constraints.py` | 从 Stage 0 输入生成 SACG seed：model/task/numeric/template/architecture/deployment/memory/runtime/tools/human constraints。 | 初始 invariants 为空；很多后续 transition 因此没有真实 checker gating。 |
| Stage 2 template_selection | `stage_templates.py` | 根据 template metadata 的 supported ops 匹配模型算子，生成 template selection artifact。 | 只做静态匹配；没有验证模板接口、吞吐、资源、numeric 兼容性。 |
| Stage 3 pipeline_planning | `stage_pipeline.py` | 按 selected operator 顺序生成 pipeline stages 和相邻 stream edges。 | 不是目标硬件 11 级流水线；不是 12 层 token 流水；没有表达 KV cache、DDR 双缓冲、layer overlap、token N/N+1 重叠执行。 |
| Stage 4 parameter_binding | `stage_params.py` | 从 design space 里取第一个 candidate 绑定参数。 | 不是真正 DSE；没有资源/时序/带宽反馈；没有比较多个点。 |
| Stage 5 code_generation | `stage_artifacts.py` | 复制 Chisel template，生成 `GeneratedDesignParams.scala`、`GeneratedAcceleratorTop.scala`、`GeneratedAxiDdrTop.scala` 和 code package metadata。 | 当前生成加速器硬件代码包，包括算核 top 和 FPGA AXI/DDR-facing top wrapper；不负责真实 DDR image、runtime、testbench 或 backend 产物；仍需后续验证和工具证据证明可综合、可运行。 |
| Stage 6 verification_artifacts | `stage_verification_plan.py` | 生成 checker plan、hierarchical verification plan、Qwen-specific evidence gate 列表。 | checker plan 比真实 checker 更强；`qwen_real_weight_artifacts` 名称容易误导，因为当前只检查 artifact/manifest 层，不证明真实权重参与功能仿真。 |
| Stage 7 verification | `stage_verification.py` | 执行静态检查和 tool protocol 命令，把结果写 evidence；如果 hard result 全 pass，则 verification result pass。 | `result_status=fail` 不会让阶段 report 变成 failed；顶层继续进入 repair/backend。 |
| Stage 8 repair | `stage_repair.py` | 根据 verification result 生成 repair plan，失败时写 generic regression rerun action。 | 不真正改代码、不重新验证；`needs_repair` 仍通过 `status: "ready"` 让顶层继续。 |
| Stage 9 backend_board | `stage_backend.py` | 生成 Vivado/backend/board handoff scaffold，统计 pending/failed tools 和 blockers，给出 `final_design_pass`。 | 即使 blockers 存在也 promote transition；没有实际 Vivado report parser、bitstream gate、board runtime closure。 |
| Stage 10 sacg_validate | `stage_agent.py` + `sacg_store.py` | 调 `sacg_store validate` 检查 SACG 引用完整性，然后运行 design team summary。 | 只保证 references 自洽，不保证 evidence 完整、checker 全 pass、backend final pass。 |

### 12.4 SACG 当前机制与证据传播问题

当前 SACG store 的核心对象包括：

- `nodes`：任务、模型算子、pipeline stage、tool 等；
- `edges`：模型算子顺序、stream 连接等；
- `constraints`：shape/numeric/template/pipeline/tool/runtime/backend 等约束；
- `invariants`：checker 与 constraints 的绑定；
- `artifacts`：每个阶段产生的 JSON、代码包、脚本等；
- `evidence`：checker 或外部工具输出；
- `failures`、`repairs`、`approvals`；
- `transitions`：阶段状态变迁记录。

设计目标是：

```text
touched constraints -> required checkers -> evidence -> transition promotion
```

当前实现中需要特别注意两点。

第一，多个阶段是在 `promote_transition()` 之后才把新 invariants 写入 SACG。对于新创建的 constraint，transition promotion 时通常还没有对应 checker，因此 `required_checkers` 为空，promotion 会在没有真实证据的情况下发生。这和本文档前面“无 required checker evidence，不 promotion”的方法原则不一致。

第二，最终的 `sacg_validate` 主要做引用完整性检查，例如 node/edge/constraint/artifact 引用是否存在。它不会系统性检查：

- 是否存在 failed invariant；
- required evidence 是否全部存在且 pass；
- real tools 是否全部执行；
- `final_design_pass` 是否为 true；
- placeholder artifact 是否仍在最终路径中；
- backend/board/runtime 是否真实闭环。

因此 SACG 现在更像“结构化状态账本 + 部分 gating”，还不是完整的 correctness control plane。

### 12.5 LLM/team 层当前实际作用

当前框架有三类 LLM 相关机制：

- Stage 0 的输入准备 sub-agent；
- 每个主要阶段前后的 stage-local LLM worker / pre-stage safety gate；
- `stage_team.py` 里的 team decomposer 和并行 specialist subtask。

这些机制对论文叙事有价值，因为它们能记录多 agent 角色、handoff、review 和风险提示。但从当前代码行为看：

- Stage 0 已改为 LLM required，LLM 不可用时直接停止；
- 后续 team/stage worker 中仍保留 fallback 记录结构用于错误日志，但正式实验应以 enforce=true 运行，不能把 fallback 当作 formal multi-agent evidence；
- team / pre-stage safety gate 结果大多作为报告字段和风险提示，不是硬件正确性的强 gate；
- 真正的 pass/fail 仍应来自 checker 和真实工具 evidence。

因此，目前不能把“LLM/team 说可以继续”解释成硬件设计通过。它只能作为辅助审查层。

### 12.6 Tool protocol 和真实工具证据现状

Stage 0 会把工具注册到 `tool_protocols.json`，Stage 7 通过 `tool_runner.py` 执行。当前机制：

- `SPATIALACC_RUN_REAL_TOOLS` 控制是否执行真实工具；
- command 为空时记录 `not_run`；
- command 指向 `.c` 文件时记录 `not_run`；
- 每个 tool entry 包含结构化 `execution.argv`、`execution.cwd`、`execution.env`、`consumes`、`produces`，并保留派生的 `command` 字段用于兼容；
- ToolRunner 优先用结构化 argv/env/cwd 执行，旧 command 字符串只是兼容路径；
- stdout/stderr tail 会进入 tool evidence；
- Stage 7 的 required real-tool evidence checker 会把缺失或失败的 required tool 判为 fail。

主要问题：

- `script_exists` 已检查首个 executable/script 是否存在，但还没有验证远端工具路径和远端脚本可执行性；
- 部分遗留工具仍依赖派生 command 字段，后续应完全迁移到结构化 execution；
- VCS 和 Verilator 属于同一个 functional simulation evidence group，二者至少一个通过即可满足功能仿真工具要求；
- Vivado synthesis / implementation 仍是后端和 bitstream 证据的必需工具；
- remote VCS、Vivado、board runtime 等关键命令如果缺少 host/path/env，会被记录为 `not_run` 或 failed evidence，不能被猜测为通过；
- 工具结果目前只按返回码和输出尾部记录，没有解析 VCS coverage、仿真成功标志、Vivado timing/resource、bitstream、board output 的结构化含义。

这意味着当前 tool evidence 只能作为“命令是否运行/返回码如何”的基础证据，不足以支撑最终硬件 pass。

近期修正后，工具位置不再由 Stage 0 代码硬编码。Stage 0 先从 `accagent/framework/input_materials/tools/` 和 board 输入材料中提取 `tool_profile.json`，再由 profile 生成 `tool_protocols.json`。当前项目材料可提取到：

- Verilator：local functional verification；
- VCS：remote functional verification；
- Vivado：remote synthesis / implementation / bitstream。

已用真实工具做过最小验证：

- local Verilator 可以编译/link 当前生成的 Qwen AXI board smoke，但仿真运行阶段超时，没有 PASS；
- remote VCS 可以在 `hyyuan@10.12.133.23` 编译并运行同一 smoke，VCS 本身和 `VCS_TARGET_ARCH=linux64` 配置可用，但当前 smoke 仍 TIMEOUT；
- Vivado 远端 executable 可以调用，版本为 Vivado 2021.1；
- 普通 Codex sandbox 内的 ssh/VCS 调用会遇到 `socket: Operation not permitted`，需要在批准的 sandbox 外执行真实远端工具。

因此当前结论是：工具路由已接通，工具能被真实调用；但当前生成系统还没有通过功能仿真，不能把 VCS/Verilator evidence 标成 pass。

### 12.7 Qwen real-weight 和上板一致性边界

近期代码已经把 Qwen 相关工具前置到 Stage 0 tool protocol 中：

- `qwen_weight_manifest_generate`；
- `qwen_board_interface_discovery`；
- `qwen_tb_scaffold_generate`；
- `qwen_hierarchical_static`；
- `qwen_generated_sv_compile`；
- `qwen_generated_tb_static`；
- `qwen_runtime_bitstream`。

这改善了 Qwen-specific gate 的可见性，但当前边界必须写清楚：

- `verification/cases/qwen2_real_weights/resolved_manifest.json` 只能证明找到了真实权重 artifact 的 manifest，不证明仿真使用了这些权重；
- 当前 generated Qwen testbench scaffold 仍可能使用 pattern memory 或占位初始化，不等价于真实 Qwen 权重 DDR image；
- 当前没有完整的 `qwen_real_weight_packer.py`，没有把 HuggingFace/safetensors 权重按真实 DDR AXI 读写布局打包成仿真和上板共用的 image；
- 当前没有把 packed DDR image、window.cfg/runtime config、AXI address map、wrapper 读权重路径统一成一个真实板上流程；
- 因此当前状态不能称为“使用真实权重做功能验证”，只能称为“真实权重 artifact discovery/manifest gate 已开始接入”。

如果目标是满足项目验收的验证约束，必须补齐：

- real-weight packer：从真实模型权重生成 DDR image 和可追踪 manifest；
- board-consistent memory map：仿真和上板使用同一套 AXI address/window/runtime 配置；
- VCS real-weight mode：testbench 从 packed image 初始化 DDR/AXI memory，禁止 fallback pattern memory 冒充 pass；
- output scale check：检查输出 token/layer/hidden-size 规模与真实模型一致；
- 12-layer pipeline check：明确 layer/token 调度不是单 block scaffold；
- remote sync + clean run：每次本地修改后同步到远端，杀掉旧仿真进程，避免误跑旧文件。

### 12.8 与用户预期不一致的关键点

按当前项目目标，用户预期是：真实数据/权重、真实 DDR AXI 接口、12 层模型、流水线式推理、远端 VCS 功能验证、最终 Vivado/bitstream/board 闭环。当前框架与这些预期的差距如下。

1. 软件阶段的 11 steps 不等于硬件 11 级流水线。

   当前 `TopAgent` 的 11 个 stage 是 agent workflow；硬件 pipeline 需要由生成的 RTL/Chisel 和验证 trace 证明。现在 `stage_pipeline.py` 只是算子级 plan，没有证明 token N 进入 stage2 后 token N+1 立即进入 stage1。

2. 当前 pipeline plan 不是 12 层完整模型推理。

   当前 plan 基于 model ops 和 template selection，主要表达单层 decoder block 内部 operator sequence。它没有建模 12 层权重双缓冲、跨层访存重叠、KV/runtime 状态、912 序列全长 liveness。

3. verification fail 仍可能让顶层继续。

   `stage_verification.py` 会计算 `result_status`，但 report 顶层仍写 `status: "ready"`。因此 `GenericStageAgent` 认为阶段通过，继续进入 repair/backend。

4. repair 只是计划，不是修复闭环。

   `stage_repair.py` 会列出 failures/pending 和 generic action，但不修改 RTL/Chisel/testbench，也不触发 rerun。它不能被视为 bug 已解决。

5. backend_board 生成的是 scaffold，不是 backend closure。

   `stage_backend.py` 会生成 Tcl 和 board smoke scaffold，并计算 blockers。但 transition 当前仍会 promote，`status` 仍 ready。它不能代表 Vivado 或板卡通过。

6. `sacg_validate` 不是 final correctness checker。

   它只检查 SACG 引用，不检查所有 invariants/evidence/final_design_pass。因此最终 SACG validation pass 不能解读为硬件 pass。

7. code generation 可能过度乐观。

   当前 artifact manifest 中的一些字段会把目标缺失项隐藏为 scaffold 或空 missing list。实际目标需要区分 generated、placeholder、external_required、verified 四种状态。

8. real-weight gate 命名过强。

   `qwen_real_weight_artifacts` 目前更接近 manifest/static artifact gate，不是 real-weight functional simulation gate。需要拆成 `qwen_real_weight_manifest` 和 `qwen_real_weight_functional_vcs`。

9. remote VCS/board runtime 没有形成强制闭环。

   如果关键 command 为空或 not_run，Stage 7 会记录 fail/pending，但 Stage 8/9 仍会继续生成报告。顶层应该在最终目标模式下硬停。

10. LLM/team fallback 不能作为正式实验证据。

    enforce=false 对调试有用，但论文实验和项目交付不能把 fallback review 当作 agent reasoning evidence。

### 12.9 必须修改的优先级

P0：防止“假通过”。

- `stage_verification.py`：当 `result_status != "pass"` 时，report 顶层 `status` 必须不是 `ready`，或 `GenericStageAgent` 必须显式检查 `result_status`；
- `stage_repair.py`：当 `repair_status == "needs_repair"` 时，阶段应返回 blocked/failed，除非它真的执行了修复并完成 rerun；
- `stage_backend.py`：当 `final_design_pass == false` 时，不应 promote backend transition，也不应让顶层把 backend 阶段视为 pass；
- `SACGValidationAgent`：最终 validation 应检查 failed invariants、missing required evidence、pending required real tools、placeholder artifacts、backend `final_design_pass`；
- `sacg_store.py`/各 stage：invariant 应在 transition promotion 前创建，或者 transition 需要显式携带本阶段 required checker list，避免空 checker promotion。

P0：补齐真实权重功能验证链路。

- 实现 `qwen_real_weight_packer.py`，从真实模型权重生成 DDR image、layout manifest、checksum；
- 修改 Qwen VCS testbench，使其从 packed DDR image/window config 初始化真实 AXI memory；
- 禁止 pattern/default memory 在 real-weight mode 下通过；
- 增加输出规模 checker，至少验证 batch/sequence/hidden/layer/token 输出数量与目标模型一致；
- 把 `qwen_real_weight_artifacts` 拆成 manifest gate 和 functional VCS gate；
- VCS/Verilator command 必须从 `tool_profile.json` 生成，并在每次运行前 sync/clean，避免旧文件误判。

P0：表达真实 12 层流水线。

- SACG 中需要显式建模 layer dimension、token dimension、stage dimension；
- pipeline plan 需要描述 12 层权重双缓冲、访存/计算重叠、token streaming；
- verification plan 需要有 26 和 912 两种 sequence length 的 full-sequence liveness gate；
- checker 需要验证 token N/N+1 的 stage overlap，而不是只验证单个 token 全路径。

P1：工具协议和配置工程化。

- `tool_protocols.json` 应使用结构化 argv、cwd、env、required、timeout、produces、consumes，而不是只存 command string；
- `script_exists` 应进一步扩展到远端 host/path 检查；
- 对 shell command 增加 allowlist 或显式审计字段；
- `config.py` 应支持 CLI/config file/env override；
- API key 从源码移除，只允许环境变量或未纳入仓库的 secret 文件；
- run report 记录 git hash、dirty status、关键输入 checksum、远端同步版本。

P1：artifact freshness 和 placeholder 管理。

- artifact manifest 必须区分 `generated`、`placeholder`、`external_required`、`verified`；
- 后续阶段不能把 placeholder 当作 final artifact；
- 输入或模板变化后，需要 invalidation 旧 evidence；
- generated SV、testbench、DDR image、runtime config、Vivado Tcl、bitstream report 都应有 checksum 和 producer stage。

P2：DSE、backend 和论文实验增强。

- `parameter_binding` 从 first candidate 改为有资源/带宽/时序反馈的 search；
- backend report parser 解析 timing/resource/utilization/DRC/bitstream；
- board runtime parser 解析有效输出、错误码、DDR transaction summary；
- fault injection 和 ablation 用于证明 SACG/evidence gate 确实能抓 bug；
- 非 OPT/Qwen 的泛化实验应在 checker 和 artifact 状态都可信之后再展开。

### 12.10 下一步推荐执行顺序

为了与当前项目验收目标一致，建议不要先扩展更多 agent 角色，而是按下面顺序收敛：

1. 先修 failure propagation，确保 verification/repair/backend 不能假 ready；
2. 再补 real-weight packer 和 real DDR image testbench；
3. 然后跑远端 VCS real-weight 26 序列 smoke，确认真实权重路径和输出规模；
4. 扩到 912 序列 full-sequence liveness；
5. 再把 12 层流水线/双缓冲/token overlap 变成 SACG constraints 和 checker；
6. 最后接 Vivado/bitstream/board runtime，并把 backend/board evidence 纳入 final validation。

这也是后续论文叙事应该坚持的边界：SpatialAccAgent 的贡献不是“agent 顺序调用很多脚本”，而是把 accelerator design closure 中的结构、约束、证据、修复和后端部署统一放进一个可审计的 SACG 控制平面。当前代码已经有这个框架雏形，但必须先补齐上述 P0 问题，才能把它作为可信系统实验来写。

## 13. Reviewer Stress Test

可能的审稿人质疑：

1. “这只是 multi-agent wrapper。”
   - 必须回应：展示 SACG、结构化设计约束、checker evidence、ablation 和 fault injection。

2. “这只是 accelerator compiler。”
   - 必须回应：展示 heterogeneous inputs、Chisel template binding、runtime/DDR/AXI artifacts、backend/board evidence、repair records，这些超出普通 compiler IR。

3. “这只是一次 OPT 工程故事。”
   - 必须回应：展示 GPT-2/LLaMA/Qwen template coverage，或至少一个非 OPT 的有意义验证证据。

4. “困难部分是人做的。”
   - 必须回应：报告 generated artifacts、human approvals、manual edits、repair iterations 和 automation rate。

5. “Agent 是通过削弱正确性才 pass 的。”
   - 必须回应：禁止未审批修改 oracle/tolerance/golden，并要求 checker-backed promotion。

6. “生成设计不能部署。”
   - 必须回应：提供 synthesis/implementation/board evidence，或者清楚限定 backend evidence 边界。

## 14. 资料和引用指针

本地项目文档：

- `accagent/docs/problem_definition.md`
- `accagent/docs/methodology.md`
- `accagent/docs/sacg.md`
- `accagent/docs/checker_spec_v0.md`
- `accagent/docs/evaluation_plan.md`
- `accagent/docs/hardware_operator_template_requirements_v0.md`
- `accagent/docs/related_work.md`

本地论文：

- `docs/papers/Zhao 等 - 2024 - MAGE A Multi-Agent Engine for Automated RTL Code Generation.pdf`
- `docs/papers/Wang 等 - 2025 - RTLSquad Multi-Agent Based Interpretable RTL Design.pdf`
- `docs/papers/Fu 等 - 2025 - GPT4AIGChip Towards Next-Generation AI Accelerator Design Automation via Large Language Models.pdf`
- `docs/papers/Team 等 - 2026 - Design Conductor 2.0 An agent builds a TurboQuant inference accelerator in 80 hours.pdf`
- `docs/papers/Ye和Chen - 2025 - StreamTensor Make Tensors Stream in Dataflow Accelerators for LLMs.pdf`

公开链接：

- MAGE: https://arxiv.org/abs/2412.07822
- RTLSquad: https://arxiv.org/abs/2501.05470
- GPT4AIGChip: https://arxiv.org/abs/2309.10730
- Design Conductor 2.0: https://arxiv.org/abs/2605.05170
- StreamTensor DOI: https://doi.org/10.1145/3725843.3762817
- AutoGen: https://github.com/microsoft/autogen
- MetaGPT: https://github.com/FoundationAgents/MetaGPT
- LangGraph: https://github.com/langchain-ai/langgraph
- SWE-agent: https://github.com/SWE-agent/SWE-agent
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- Allo: https://github.com/cornell-zhang/allo
