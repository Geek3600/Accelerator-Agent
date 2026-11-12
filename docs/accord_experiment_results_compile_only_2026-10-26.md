# ACCORD 实验结果：compile-only 快速口径（2026-10-26）

## 结论

当前可立即用于论文实验部分的，是三组主要 GPT-2 设计修订 pilot、两组补充的 lanes=8 Stage-4/5 pilot、四项证据失效传播确定性实验，以及一项 Gemma VCS compile-only gate 和一项 Gemma 编译失败到通过的 Agent 修复 pilot。它们提供了真实运行记录，支持“参数/证据能跨阶段传播”和“Agent 可依据真实编译诊断修复并重新通过编译”这类有限结论；它们不支持 ACCORD 相对 baseline 的性能或修复成功率优势，也不证明完整 DDR runtime 或 CCTG 图引导根因定位。

本页按 2026-10-26 用户确认的宽松实验口径整理：Stage-6 当前只要求真实 VCS 编译、展开和链接通过，不要求 RTL 数值仿真。compile-only 的通过只能表述为编译级结果。

## E2：跨阶段参数修订

固定目标为 GPT-2 W4A8；每项修订均从同一设计 checkpoint 派生 ACCORD 与 B0 两个 profile。ACCORD 获得 SACG/DCG 上下文，B0 的 profile 过滤图上下文；两者接收相同任务和硬件规格。

| 修订任务 | 参数变化 | ACCORD | B0 | 编译证据 |
|---|---|---|---|---|
| cache tile | `cache_tile_words: 256 -> 512` | Stage-4 选出 512；6/6 参数检查通过；Stage-5 Chisel compile/elaboration 6/6 命令通过 | 同左 | Stage-5 编译通过；未运行 VCS |
| activation banks | `activation_banks: 4 -> 2` | 绑定为 2；6/6 参数检查通过；Stage-5 6/6 命令通过 | 同左 | Stage-5 编译通过；未运行 VCS |
| cross-token reuse | `cross_token_reuse_tokens: 8 -> 4` | 绑定为 4；6/6 参数检查通过；Stage-5 6/6 命令通过 | 同左 | Stage-5 编译通过；另有真实远端 VCS compile/elaboration/link pass |

所有配对均保留 `lanes=8`、8x8 计算阵列、512-bit refill 与 W4A8 整数 DSP 配置。参数绑定报告的 6 项检查均为 pass、0 errors。ACCORD 与 B0 在 Stage-4/5 选择相同候选并通过编译；cache-tile 配对的 134 个源文件 SHA-256 全部相同，activation-banks 配对的 121 个源文件亦全部相同。cross-token reuse 配对的 Stage-6 VCS 仅 compile-only pass，双方均未运行仿真。该配对之后 ACCORD 做过额外 run-local timing 修复而 B0 没有，因此不比较该后续 QoR，也不把它归因于 DCG。

因此当前 E2 可报告为 **3/3 设计修订案例完成参数绑定与 Chisel 展开；ACCORD 3/3、B0 3/3；cross-token reuse 的 VCS compile-only 为 2/2 pass**。这是机制可执行性和阶段产物一致性的 pilot。由于 baseline 在同一任务上也得到相同参数，当前数据不能声称 DCG 带来相对 B0 的准确率、QoR 或效率提升。

### 补充：GPT-2 lanes=8 参数传播与 Stage-5 pilot

额外复核了两组历史任务目录。两组都以 GPT-2、MIMIC Computer v6.0（VU9P）、W4A8_INT32_DSP 为条件，从 lanes=16 的冻结设计请求 lanes=8；ACCORD 与 B0 的 model config、board profile、numeric policy 和 task card 在各自配对内逐字节一致。两个 profile 都选择同一候选 `arch_7ad3a71d15fd`（fingerprint `7ad3a71d15fdac846e139b91d5aa7233ca445177ef2faa7e49c1cc1ce051359f`），物化为 8 lanes、8x8 compute array、512-bit refill、4 activation banks、8-token reuse、W4A8 integer DSP。

| 历史任务 | ACCORD Stage-4/5 | B0 Stage-4/5 | Stage-5 编译耗时 | VCS / QoR |
|---|---|---|---|---|
| `dcg_lanes8_case_20261023T193854+0800`：显式请求 lanes 16→8、阵列 16x32→8x8 | 参数检查 6/6；6 个 Chisel compile/elaboration 命令通过 | 参数检查 6/6；6 个 Chisel compile/elaboration 命令通过 | 136.781 s / 134.382 s | 无 VCS；无综合或性能测量 |
| `dcg_lanes8_inferred_20261023T2115+0800`：请求 lanes 16→8，由约束推导阵列几何 | 参数检查 6/6；6 个 Chisel compile/elaboration 命令通过 | 参数检查 6/6；6 个 Chisel compile/elaboration 命令通过 | 161.203 s / 156.440 s | 无 VCS；无综合或性能测量 |

两组 task card 明确限定只运行 Stage-4/5，并要求不报告 QoR/性能。它们没有顶层 experiment manifest，compile gate 也没有记录源文件 hash，因此仅作为补充性的历史阶段闭环数据，不作为主要 E2 的独立统计重复，不改变 E2 的正式分数。ACCORD 与 B0 都得到相同候选与 pass 结果，不能据此声称图上下文带来选型或性能收益。

另一个目录 `dcg_lanes8_20261023T1926/` 未纳入新增 VCS 数据：其 ACCORD/B0 两份 board VCS 报告具有相同 input fingerprint `4a8dc870...2ec2d0f` 和相同 compile-log SHA-256 `24aadf1f...79d78`，manifest 与 source-identity 路径都指向旧 run `accagent/runs/w4a8_20261018_gpt2/`。该目录的 252 个 DSE 合法候选中测量数为 0，agent run report 仍为 `running`。因此不能把这份旧 run 的 VCS pass 重复算成两个新 profile 的验证结果，也不能将其 DSE proxy 当成测量 QoR。

## Evidence Binding：证据失效与复用

同一冻结 GPT-2 baseline 上运行四个确定性 artifact mutation 案例：

| 案例 | 修改 | 预期行为 | 观察结果 |
|---|---|---|---|
| E1 | RTL 行为 | functional 与 backend 证据失效 | 符合 |
| E2 | XDC clock period | 仅 backend 证据失效 | 符合 |
| E3 | 模型参数 | functional 与 backend 证据失效 | 符合 |
| E4 | 与构建无关的文档 | 两类硬件证据继续复用 | 符合 |

结果为 **4/4 pass、0 次 stale-evidence acceptance、0 次 false invalidation**。这是证据绑定逻辑的确定性检查，不包含 Agent、VCS 或 Vivado 执行；论文中应作为 evidence invalidation/reuse 的机制测试报告，而不是硬件实验。

## E3：编译诊断与修复 pilot

### Gemma B2 fail-to-pass

真实 Gemma board compute-slot 源在远端 VCS 编译时报告 `Error-[IND] Identifier not declared`：`write_busy` 在使用后才声明，同一声明顺序问题也影响 `rstate`、`read_kind`。Agent 根据该工具错误，将相关声明移到首次引用之前，并删除后续重复声明；硬件源码修改仅在 run-local `compute_slot.sv`，并通过 `replace` 更新已有 DUT weight-binding manifest。没有改 kernel 接口、AXI 路由、数值或 pipeline 行为。

- 修复前源码 SHA-256：`2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`
- 修复后源码 SHA-256：`6d2d3192a7628bde1956c5e39bb0076f4503cd9921e1df82872b2c5110fe12c0`
- Agent 修复提案：第 4 次尝试因既有 manifest 使用了 `create` 而被事务检查拒绝，未写入文件；第 5 次改为对既有文件执行 replace，源码 patch 成功应用。
- 真实远端 VCS：修复后 compile、elaboration、link 全部通过，退出码 0，共 33 个模块；编译 CPU 67.761 s、展开 1.630 s、链接 0.403 s。仿真按 compile-only policy 跳过。

该案例支持一次真实的 **compile failure -> Agent source repair -> compile-only pass**。本次运行 profile 是 B2（无 guided-repair 上下文），诊断来自编译器的直接错误，且没有非空、hash-bound CCTG causal slice。因此它不能作为 CCTG 图引导定位效果的直接证据，也不能声称数值正确或 runtime 修复。

### Gemma 当前 Stage-6 compile-only gate

同一 `e3_gemma_exact_runtime_20261026/run/` 已按显式 `vcs_compile_only` policy 完成 Stage-6：debug loop、`case_axi_ddr_interface`、远端 VCS 以及 board compile promotion certificate 均通过，工具退出码 0。编译用时约 108.313 s；VCS 记录 compile/elaboration/link CPU 时间为 72.041/1.610/0.431 s。输入清单包含 51 个 source IDs，VCS 报告实际完成 34 个模块，顶层为 `sacg_board_compile_tb`，模式为 `compute_slot_axi`。

这条 gate 证明当前 run 的生成 kernel/compute-slot adapter 编译闭合。manifest 有 26 层/338 个模型权重 hash 记录，但 `compiled_sample_source_ids=0` 且 `artifacts={}`；这不证明 DUT 运行时消费这些权重，也不是完整 board DDR runtime。仿真与数值比较未执行。

## 可用于论文的表述范围

建议把 E2 写成三种主要参数修订，加上两组补充 lanes=8 Stage-4/5 pilot 的 cross-stage parameter materialization/compile 数据；把 Evidence Binding 写成 4-case deterministic stale-evidence invalidation test；把 E3 写成单案例 compile-time repair demonstration。明确列出 ACCORD/B0 观察结果相同，并避免用单案例推断统计显著性或机制优越性。

| 当前可报告 | 当前不应声称 |
|---|---|
| 3 个参数修订案例在 ACCORD 与 B0 均绑定目标值并通过 Stage-5 编译 | ACCORD 比 B0 有更高参数正确率、QoR 或吞吐率 |
| 2 组补充 lanes=8 配对 pilot 在 ACCORD/B0 均通过 Stage-4/5（每组 2/2）；仅作描述性阶段数据 | 将补充 pilot 当成独立正式重复，或声称已验证 VCS、综合、资源和性能 |
| 证据绑定逻辑正确区分 4 种变更的证据失效/复用范围 | 4 个确定性用例等价于 Agent/EDA 大规模实验 |
| 一次真实 VCS 编译错误经 Agent 修改后 compile-only 复验通过 | 该 B2 case 证明 CCTG 因果定位收益 |
| Gemma 当前板级 identity 下的 compute-slot AXI compile-only gate 通过 | 完整 AXI/DDR 权重加载、12/26 层运行、无死锁或数值正确 |

## 原始记录索引

- E2 cache tile：`accagent/experiments/accord/results/dcg_cache_tile_revision_20261024T0110+0800_v2/experiment_manifest.json`
- E2 activation banks：`accagent/experiments/accord/results/dcg_activation_banks_revision_20261024T122503+0800/experiment_manifest.json`
- E2 cross-token reuse：`accagent/experiments/accord/results/dcg_cross_token_reuse_revision_20261024T164300+0800_v2/experiment_manifest.json`
- Evidence Binding：`accagent/experiments/accord/results/evidence_binding_20261026_compile_policy/summary.json`
- Gemma B2：`accagent/experiments/accord/results/cctg_b2_prompt_clean_20261024T1105+0800/experiment_manifest.json`
- Gemma Stage-6：`accagent/experiments/accord/results/e3_gemma_exact_runtime_20261026/run/debug_loop/debug_loop_report.json`、`run/verification/vcs/case_board_vcs_functional.json`、`run/verification/certificates/board_axi_ddr_promotion_certificate.json`
- 新增 summary 验证：`test_accord_experiment_profile.py` 5/5、`test_verification_evidence_contract.py` 26/26、`test_debug_loop_resume.py` 27/27 pass。
