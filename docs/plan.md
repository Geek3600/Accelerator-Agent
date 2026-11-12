## 2026-10-26 GPT-2 目标模型范围更新

- 用户已将后续所有 GPT-2 目标实验从 GPT-2 Small 改为 GPT-2 Medium。新目标固定为 `openai-community/gpt2-medium`、24 层、hidden=1024、16 heads、MLP=4096；实验 campaign 与映射清单位于 `accagent/experiments/gpt2_medium_20261026/medium_mechanism_inventory.md`。
- 既有 GPT-2 Small 的 DCG revision、E1-E4 evidence-binding、生成源码、参数、DSE、QoR 与时序数据继续作为 Small 历史记录保存，不得重标为 Medium，也不得作为 Medium 的参数或性能证据。历史 Gemma CCTG 案例不属于 GPT-2 Small，不在该模型替换范围内。
- ACCORD 机制实验需从新 Medium run 的真实 Stage-1/2/3 状态记录前向传播；Stage-4 返回合法 DSE 结果后即可立即启动配对的 Stage-4/5，不必等待主线 Stage-6 或 Vivado。Small 实验里的参数值不能复制，任务意图要依据 Medium 的合法候选域重建。确定性 E1-E4 测试在 Medium RTL、model config、XDC 与文档生成后即可运行，不必等待综合。
- 已准备 campaign runner `accagent/experiments/gpt2_medium_20261026/run_mechanism_pairs.py`：默认只观察/准备；显式 `--watch --execute` 时等待 GPT-6.1 Medium Stage-4 ready，然后按相同输入/profile差异启动五组 ACCORD/B0 Stage-4/5，最多并行两个。进程从指定 agent-only W8API 环境文件取路由配置，并清除继承的 LLM 环境/密钥，避免父 shell 的 Toska 污染。
- 本节是当前后续执行范围的覆盖项；下方按时间记录的 Small 实验材料仍是原始历史，未被改写为 Medium 结果。Medium forward capture 和 E1-E4 分别只等待实际 Stage-1/2/3 图状态与 Stage-5 文件；配对 revision 等待 Stage-4 的合法 DSE 候选。

## 2026-10-26 compile-only 快速实验结果（用户确认的当前口径）

- 当前可供论文写作使用的 pilot 汇总见 [accord_experiment_results_compile_only_2026-10-26.md](accord_experiment_results_compile_only_2026-10-26.md)。将 Stage-6 gate 放宽为真实 VCS compile/elaboration/link pass；不要求数值仿真。对应 Gemma 当前 run 已通过 compute-slot AXI compile-only gate。
- E2 的 GPT-2 cache tile、activation banks、cross-token reuse 三组主要 revision 均完成 ACCORD/B0 参数物化与 Stage-5 Chisel compile/elaboration；reuse 配对另有双方 VCS compile-only pass。另核实两组历史 lanes=8 ACCORD/B0 Stage-4/5 配对（每组双方 6/6 参数检查、6/6 编译命令通过），作为补充描述性 pilot；没有 VCS 或 QoR。各配对选出的候选相同，当前数据不支持 DCG 的比较优势。
- Evidence Binding 的四种 artifact mutation 确定性测试为 4/4 pass，stale evidence acceptance=0，false invalidation=0；这是逻辑检查，不含 Agent 或 EDA 工具运行。
- E3 有一项 Gemma B2 真实 compile failure -> Agent repair -> VCS compile-only pass 案例（33 modules、return code 0）。它没有运行仿真且没有非空 hash-bound CCTG causal slice，故仅作为 compile-time repair pilot；不能报告为 CCTG graph-guided diagnosis 收益。
- 本轮接受的 compile-only 口径不把 compile pass 等同于完整功能/runtime pass。Gemma gate 的顶层为 `sacg_board_compile_tb`、模式为 `compute_slot_axi`，manifest 虽记录 26 层/338 个权重 hashes，但 `compiled_sample_source_ids=0`、`artifacts={}`，没有运行时权重消费证据。
- 论文撰写可立即采用上述 pilot 的绝对计数及工具耗时，但应标明单次/小样本和无仿真范围。原计划中的多案例对照、重复统计以及 CCTG 因果比较仍未完成，不得沿用原计划指标推导相对收益。

## 最新执行复核（2026-10-26T17:30:48+08:00）

- 正式实验状态没有改变：E2/E3 formal score 仍为0。E2现有三组 GPT-2 revision 只证明参数物化与阶段流程 pilot，ACCORD/B0 没有可归因的差异；E3 仍缺 exact-board DDR runtime、有效 progress/DDR 事件和非空 hash-bound CCTG 诊断/修复闭环。
- 在同一 Gemma E3 run `accagent/experiments/accord/results/e3_gemma_exact_runtime_20261026/run/` 修复并验证了两处通用框架问题。`regenerate_target_model_reference()` 现在即使 DUT 权重绑定 materialization 为 `incomplete`，也会继续重跑 `case_semantic_testbench`，将 materialization 后的新诊断写入 repair package；此前该分支跳过复检，导致 Agent 重复读取 15:51 的旧 provenance mismatch。17:24 的 fresh report 已移除四项旧 hash mismatch，当前真实 blocker 是 DUT binding incomplete、缺少13项权重 tensor hash 和11个 operator-stage harness、未证明 DUT 消费权重且 identity fallback 未关闭。
- operator-leaf prompt compaction 曾把 `stage_repair_execute.py` 误识别为 pipeline stage `stage_repair_execute`，随后把全部大 Q31 scale 数组过滤掉。`_operator_leaf_stage_ids()` 现在只识别带数字序号的真实 stage ID。对本次 Gemma requirements 实测，compaction 保留5组、共17,664个通道 scale 值；完整 payload仍以其原始 hash-bound requirements 为准。
- 回归验证：`test_operator_leaf_prompt_compaction`、`test_reference_regeneration_refresh` 和已有 reference-regeneration 单测通过；`tests.test_stage_agent` 为34/34，`tests.test_repair_execution_feedback` 为30/30；`py_compile` 与 `git diff --check` 通过。`tests.test_repair_patch_execution` 的46项中有2项既有 board-manifest fixture 用例仍失败，因为当前检查要求 board source identity 和 functional-verification tool profile；本次 reference-refresh 用例通过。
- 迭代64的旧 Agent 响应及日志已保存在原 run。当前 Stage-6 已从同一 `verification/sacg_state.json` 重启，log 为 `run/debug_loop/e3_gemma_stage6_scale_compaction_fix_20261026.log`，进程配置固定为 W8API `gpt-6.1-sol`。目前尚无新 source patch、VCS 或 runtime 结果；E3 仍记为未完成。不得将本次 framework 修复或 reference report 更新写成硬件验证通过。

## 较早执行复核（2026-10-26T12:03:23+08:00）

- E2 复核了三组同起点 GPT-2 W4A8 revision 配对：`cache_tile_words 256→512`、`activation_banks 4→2`、`cross_token_reuse_tokens 8→4`。三组中 ACCORD 与 B0 都正确物化请求的参数且 Stage-4/5 全部通过（双方各3/3）；reuse 配对双方另有 Stage-6 VCS 编译/展开/链接通过。该组所有观察结果相同，且没有功能仿真或对称的综合 QoR 对照，因此只作为参数传播与流程闭环 pilot，不构成 DCG 相对收益；正式 E2 因果分数不提升。
- E3 的真实 Gemma 输入材料已备妥，但仍未完成 runtime/CCTG 实验。更精确的代码阻塞为 `scripts/verification/case_board_vcs_functional.py::validate_manifest()` 无条件走 compile-only validator，冷启动路径只运行 VCS compile/elaborate，simulation 固定写为 `not_run`；`accagent/framework/stage_repair_execute.py::board_integration_prompt_rules()` 也无条件告诉 Agent compile-only。虽然 `prepare_exact_board_memory_runtime_inputs()` 支持非 compile-only 分支，现有 Stage-7 Agent 与 runner 没有贯通这条路径。当前没有合法的 runtime progress log 或 CCTG causal slice。
- 当前 shell 的 `resolve_llm_cfg()` 实际解析到 `https://api.toskaxy.xyz/v1`，与既有实验声明的 W8API-only 路由不一致。任何后续实验 Agent 进程必须通过进程级 `SPATIALACC_LLM_BASE_URL=https://www.a8pi.com/v1` 固定 W8API；本轮未启动 LLM Agent，也未更改全局/CXA 配置。
- 当前无 E2/E3 Agent 或 VCS 运行；远端 Vivado 进程均为其他工程作业，未触碰。本轮结论仍是：E2 有描述性 pilot、E3 仍阻塞，不能将二者记成正式完成。

## 最新执行复核（2026-10-26T11:50:14+08:00）

- E2/E3 正式实验仍未完成、正式分数仍为0。本轮继续推进 E3 Gemma 输入准备；没有 E2/E3 Agent、VCS 或 Vivado 任务正在运行，也没有启动硬件仿真。
- 在 `accagent/experiments/accord/results/e3_gemma_runtime_prep_20261026/verification/model_reference/` 生成真实目标模型参考数据：`status=ready`，架构 `Gemma3ForCausalLM`，checkpoint revision `dcc83ea841ab6100d6b47a070329e1ba4cf78752`，26/26 层捕获、42个模块记录、首层13个真实权重绑定；随机输入和全层 decoder 输出 shape 均为 `[1,16,1152]`。checkpoint fingerprint=`829d4d90933483bf4f6112cac8afee7ae90d0259b0d01b891942cc91c442520f`，Transformer-block catalog SHA-256=`c8a8eeb5748e6d345e51bac00bb6422655df7416ad9eebbdc5c9632e5068ee7c`。完整生成文件约111 MiB；日志位于同实验目录 `model_reference_capture.log`。这些是模型参考捕获数据，不等于 DUT/DDR runtime 结果。
- reference 捕获期间修复了两个通用工具问题：语义记录跨算子复用时，模块路径推断优先匹配目标模型实际存在的同名子模块，避免 `post_feedforward_layernorm` 被 MLP 与 RMSNorm 两种权重前缀误判为冲突；Transformers 4.51.3 模型加载参数从不兼容的 `dtype=` 改为 `torch_dtype=`。`tests.test_target_model_reference` 5/5通过，`py_compile` 与 `git diff --check`通过。两个失败尝试均发生在reference完成前，原因和输出记录在实验日志。
- 现有 `accagent/runs/gemma3_gpt61_20261020` 仍不能承载本次 E3 runtime：其 board manifest 为 `validation_mode=compute_slot_axi` / `sacg_board_compile_tb` 且 `artifacts={}`；DUT weight binding 显示 `dut_consumes_bound_weights=false`、`scope_coverage_complete=false`；没有 weight-binding requirements、workload image plan、runtime capture 或 DDR stimulus。`case_board_vcs_functional.py::validate_manifest()` 仍只调用 compile-only validator。
- 下一步继续从通用 Agent/verification 路径确认 reference capture 到 DUT binding、完整 DDR workload image、exact-board runtime 的可执行闭环；只有真实 VCS runtime 事件产生并被 Agent 消费，才可计入 CCTG/E3。当前 E2 仍是三组单次 GPT-2 revision pilot（ACCORD/B0结果相同），E3仍有 Gemma compile-only fail-to-pass pilot；不可将任何一项升格为正式完成结果。

## 最新执行复核（2026-10-26T11:38:20+08:00）

- 为继续物化 E3 workload，检查项目 `scripts/verification/target_model_reference.py`：其 reference 生成需要 PyTorch 和 Transformers，并以 `dtype=torch.float32` 加载完整模型。当前本机 Python 有 PyTorch但没有 `transformers`；远端系统 Python 没有 PyTorch，且未发现可用的远端 Python 环境。当前本机约10 GiB可用内存、6 GiB swap 已满，因此没有启动 FP32 Gemma 模型加载，以免挤压 WSL 会话内存。
- 目前新增的 Gemma 26层/338张量 catalog 是 hash-bound checkpoint 编目，尚未生成 golden activation、runtime capture、weight binding 或 DDR image。现有 Gemma run 仍是 `compute_slot_axi` compile-only top 且不消费权重；E3 runtime/CCTG 未完成，正式 score 保持0。
- E2 仍为3个单次 revision pilot、6/6 Stage-4/5 目标参数物化通过；ACCORD 与 B0 结果相同，只有 reuse 配对有 VCS compile-only 记录。可作为描述性 pilot，不计正式因果 score。
- 本轮没有 E2/E3 Agent、VCS 或 Vivado 任务运行。继续推进所需的是在远端准备兼容的 PyTorch/Transformers 环境及 checkpoint，或用低内存的通用 reference capture 路径生成真实 Gemma 输入/激活，再由 runtime-enabled Agent 路径生成并运行 exact-board DDR fixture；不能将 catalog 状态冒充硬件实验结果。

## 最新执行复核（2026-10-26T11:29:48+08:00）

- E2 当前可报告的是3个 GPT-2 revision pilot：ACCORD/B0 共6个 profile-task 均物化请求参数并通过 Stage-4/5；其中只有 cross-token reuse 配对执行了 Stage-6 VCS compile/elaboration/link，未运行仿真。三个 task 的设计结果两侧一致，因此这是可复核的跨阶段物化 pilot，不是 DCG 相对 B0 的因果优势；正式 E2 score 仍为0。
- 新增 E3 输入准备产物：使用本地 Gemma 3 1B checkpoint 和项目通用 `target_model_weight_catalog.py`，在独立目录 `accagent/experiments/accord/results/e3_gemma_runtime_prep_20261026/model_weights/` 生成了真实 Transformer-block 权重 catalog。checkpoint fingerprint 为 `829d4d90933483bf4f6112cac8afee7ae90d0259b0d01b891942cc91c442520f`；catalog 覆盖26层、每层13个、共338个 tensor，完整性状态为 `pass`，catalog SHA-256 为 `c8a8eeb5748e6d345e51bac00bb6422655df7416ad9eebbdc5c9632e5068ee7c`。该步骤只生成目录和哈希清单，没有改动已有 Gemma run。
- 该 catalog 尚不能启动真实板级 runtime：现有 `gemma3_gpt61_20261020` 的板级 manifest 仍使用 `validation_mode=compute_slot_axi`、顶层 `sacg_board_compile_tb`，`artifacts` 为空；其 weight binding 明确为 `dut_consumes_bound_weights=false`，且没有可用的 weight-binding requirements、workload-image plan、runtime capture 或 DDR stimulus。因此 E3 仍只有真实 VCS compile fail-to-pass pilot，尚无 Agent 消费的非空 CCTG causal slice，也没有完整 exact-board runtime 结果，正式 E3 score 保持0。
- GPT-2 旧 reference capture 不可替代完整模型负载：虽有12层 golden activation，但只保留 layer-0 的12个权重绑定，manifest 引用的旧 checkpoint/catalog 路径已不存在。没有用它伪装成完整12层权重。
- 本轮没有 E2/E3 Agent、VCS 或 Vivado 任务在运行；没有启动新的硬件验证。下一步是让通用 Agent 流程在完整模型权重 catalog 上物化 DUT binding、DDR workload image 与 exact-board runtime stimulus，再由框架实际执行 VCS runtime 并生成/消费 CCTG evidence；不能把本轮 catalog preparation 当作已完成的 E3。

## 最新执行复核（2026-10-26T10:47:20+08:00）

- 对三组 GPT-2 revision pilot 的冻结 predecessor、两侧绑定结果和生成 Scala/SystemVerilog 做了独立文件审计。ACCORD 与 B0 各自都在三个任务中选中并物化请求值；6/6 profile-task 均通过 Stage-4/5，但这仍是三组单次 pilot，不等价于预注册重复实验，也不显示 ACCORD 相对 B0 的结果优势。

| Revision case | 目标参数 | predecessor 到生成 Chisel/RTL 的变化 | 工具证据与边界 |
| --- | --- | --- | --- |
| `dcg_cache_tile_revision_20261024T0110+0800_v2` | `cache_tile_words: 256 -> 512` | ACCORD/B0 的 `GeneratedDesignParams.scala` 均为 512；相对冻结的 `dcg_lanes8_inferred_20261023T2115+0800`，两侧各有 11/121 个 Scala/SV 文件改变 | Stage-4/5 双侧通过；未做 VCS runtime 或 Vivado 综合 |
| `dcg_activation_banks_revision_20261024T122503+0800` | `activation_banks: 4 -> 2` | 两侧生成参数均为 2；相对 cache-tile predecessor，两侧各有 15/121 个 Scala/SV 文件改变，主要是激活存储实例 | Stage-4/5 双侧通过；未做 VCS runtime 或 Vivado 综合 |
| `dcg_cross_token_reuse_revision_20261024T164300+0800_v2` | `cross_token_reuse_tokens: 8 -> 4` | 两侧生成参数均为 4；相对 reuse=8 predecessor，ACCORD 有 29 个共同文件改变、另新增2个文件，B0 有19个共同文件改变、另新增2个文件 | Stage-4/5 双侧通过，Stage-6 为 compile/elaboration/link only。ACCORD 后续 timing repair 与 B0 不对称，不能归因于 DCG |

- reuse case 另有 ACCORD OOC post-synthesis Fmax estimate 153.680652 MHz，以及 source-calibrated DSE estimate 9,086,656 cycles / 270.604546 token/s（16 tokens、12层）。这些不是 RTL 实测周期、post-route 时钟或板上吞吐，也不能作为 E2 的 ACCORD-vs-B0 收益。
- 本轮补查到远端旧 `semantic_vcs/formal_20260922_r434_gpt2` 仅有 MLP-FC 与 MLP-projection 的叶级 `weight.memh`，没有找到可绑定到现有 exact-board runtime 的完整 GPT-2/Gemma Transformer-block DDR image、模型输入和输出 fixture。故 E3 仍不能运行真实 runtime/CCTG 闭环；Gemma B2 仍只可记作 33 模块 VCS compile fail-to-pass pilot。正式 E2/E3 causal score 均保持 0。
- 当前无 E2/E3 Agent 或 VCS 进程；本轮做的是既有运行产物的独立参数/源文件审计，没有启动新综合或仿真，也未改变 run 目录。

## 最新执行复核（2026-10-26T10:07:40+08:00）

- E1–E4 evidence-binding 回归为 4/4 通过。E2 当前有 3 组完成的 ACCORD/B0 revision pilot：`cache_tile_words 256→512`、`activation_banks 4→2`、`cross_token_reuse_tokens 8→4`；三组双方均通过 Stage-4/5，但都属于单候选探索数据，没有独立 oracle 计分。前两组未做综合；第三组 ACCORD 后续 timing repair 未在 B0 上等价执行，因此其 QoR 不能用于 DCG 因果比较。正式 E2 score 仍为 0。
- E3 Gemma B2 的可用结果仍是 compile-only fail-to-pass：`compute_slot.sv` 声明顺序错误经 Agent 修复后，33 个模块 VCS compile/elaboration/link 通过。没有运行仿真，不能声称 CCTG 引导根因定位或 runtime repair 成功；正式 E3 score 仍为 0。
- 本次审计了实验与 Agent run 中 16 个 `board_simulation_manifest.json`：均无 DDR/runtime artifacts；关联权重绑定均未声明 DUT 消费模型权重。B2 testbench 是 `board_compile_tb.sv`。exact-board runner 的 manifest dispatch 固定为 `validate_compile_only_manifest()`，`semantic_simulator.py` 也将 VCS 仿真固定记作 `not_run`。因此当前没有可直接续跑的真实 DDR runtime fixture，也不能据旧 compile log 补造 CCTG 切片。
- 当前没有 E2/E3 Agent 或 VCS 进程。远端检测到的长期 Vivado 作业与本实验无关，保持未触碰。下一步有效 E3 数据需要通用 runtime manifest/执行路径、真实目标权重及输入、exact-board AXI/DDR stimulus，再由 Agent 消费真实运行期 CCTG slice、修复并同层复验；在此之前保留现有 pilot 口径，不计正式分数。

## 最新实验进度（2026-10-26T09:48:14+08:00）

### 2026-10-26T09:48:14+08:00 当前实验状态复核

- 实验尚未全部完成，当前没有运行中的 E2/E3 Agent 或 VCS 进程。E1–E4 evidence-binding 回归已有4/4通过；E2 revision case 仍是探索性结果，正式 E2/E3 score 仍为0。
- E2 可复核数据仍为 GPT-2 `cross_token_reuse_tokens: 8 -> 4` 配对 pilot：ACCORD/B0 参数传播、Stage-4检查、Stage-5 Chisel编译均完成；Stage-6仅 VCS compile/elaboration/link 通过，未仿真。两边参数选择一致，后端QoR受ACCORD额外run-local时序改动影响，不构成DCG因果对照。
- E3 的 Gemma B2 pilot 有真实 VCS 编译失败和 Agent 修复轨迹。诊断记录在 `run/repair_execution/loop/iteration_0004/05_capability_report_vcs_functional_diagnosis.json`，Agent 修复提案在 `run/repair_execution/loop/iteration_0005/04_llm_record_exact_board_integration_generation_agent_result.json`；修复后 VCS 编译、展开和链接通过，33个模块，返回码0。该pilot仍是compile-only，未执行仿真；没有生成或消费非空 hash-bound CCTG causal slice，不能计为E3完成。
- `vcs_fault_repro.log` 只是指向失败报告的短记录，不是原始VCS日志；当前 `run/verification/board_simulation/reports/vcs_compile.log` 是修复后的通过日志。论文材料需用 iteration 中保留的原始失败诊断和修复前源码快照配对，不能把当前通过日志当作失败日志。
- 通用阻塞仍在验证框架：`semantic_simulator.py` 将新执行的 simulation 写为 `not_run`，并固定报告 `simulation skipped by vcs_compile_only verification policy`；`qwen_vcs_evidence_analyzer.py` 仅在编译通过且 simulator 已尝试运行后调用 runtime CCTG slice builder。现有产物不能补造运行时 frontier。本次核查没有改动 run 产物或硬件源码。
- 下一项工作应继续恢复通用 exact-board runtime 验证路径及真实 DDR 数据绑定，再在同一故障 run 内完成运行时观察、CCTG切片、Agent消费、修复和同层复验；不把 E2 QoR 或 B2 compile-only结果计作E3。

### Experiment 2：已有一组可复核的 revision case 数据

- Case：`dcg_cross_token_reuse_revision_20261024T164300+0800_v2`，GPT-2 W4A8，唯一设计修改 `cross_token_reuse_tokens: 8 -> 4`；array=8x8、lanes=8、activation banks=4、FIFO=128、cache tile=512x2、DDR refill=512-bit。
- ACCORD 参数绑定的真实 SACG 事件是 `parameter_binding/sacg_state.json` 中 `transition.0003`：promoted，触及4项约束、11条边、9个节点，生成9项 Stage-4 参数绑定产物。Stage-4 6/6 检查通过。Stage-5 六条 Chisel compile/elaboration 命令返回0，用时119.842 s。
- B0 使用同一 task card 与设计空间，Stage-4 6/6 检查通过；Stage-5 六条 compile/elaboration 命令返回0，用时115.621 s。双方有效参数相同；`GeneratedDesignParams.scala` 仅 `designId` 标签不同。
- 两边随后都达到 Stage-6 exact-board VCS compile/elaboration/link compile-only pass；没有执行仿真，因此不能称为完整硬件功能验证。`transition.0006` 不是参数传播事件，而是 `verification_artifacts` 的 rejected transition，未触及图节点或边。此前文档把它记作参数传播的说法已更正。
- ACCORD 的后续 run-local timing repairs 使其当前 Attention、Linear、Norm、QKVProjection 源码与 B0 当前快照不同，故两边后端 QoR 不能作为 DCG 的因果对照。ACCORD 当前 QoR=153.680652 MHz、9,086,656 source-calibrated DSE cycles、270.604546 estimated token/s；B0 QoR=17.057278 MHz、8,702,008 DSE cycles、31.362469 estimated token/s。两组 cycles 都不是 RTL 实测，且源码修复历史不同，性能差值不得归因于 DCG。
- 该 case 可作为“合法 revision 已传播到参数绑定并通过当前 compile gates”的探索性记录；没有证明 ACCORD 相对 B0 的 QoR 优势。E2 正式 score 仍记0，直到按协议完成独立 oracle 和 runtime 验收。

### Experiment 3：runtime 实验证据尚不可用

- 当前没有正在运行的 E2/E3 agent 或 VCS job。全仓 `sacg_cctg_causal_slice.json`、`progress_event_log.jsonl`、`board_simulation_executed_manifest.json` 数量均为0；E3 正式 score 仍为0。
- 阻塞来自当前工具路径的 compile-only 限制，而非 W8API：`case_board_vcs_functional.py` 的 `validate_manifest()` 固定调用 `validate_compile_only_manifest()`，VCS runner 将 simulation 记为 `not_run`；当前 GPT-2 `dut_weight_binding_manifest.json` 的 `dut_consumes_bound_weights=false`、tensor hashes 为空，board manifest 的 `artifacts` 为空。其 `board_vcs_tb.sv` 只驱动时钟/复位并在2 us后 `$finish`，没有 DDR stimulus 或运行时 load。
- 因此本轮不能从现有 compile-only 产物补造 CCTG frontier。按当前项目要求，下一步须在独立实验 run 中恢复通用的 exact-board runtime path，绑定真实 GPT-2 权重、输入和输出，再执行同一 runtime failure -> 非空 hash-bound slice -> ACCORD repair proposal -> patch -> exact-board recheck 闭环；不修改已有 compile-only run，不以旧时序 QoR 替代 E3。

## 最新执行状态（2026-10-26T02:57:38+08:00）

同一 DCG revision pilot：`dcg_cross_token_reuse_revision_20261024T164300+0800_v2`。固定参数仍为 GPT-2 W4A8、8×8、8 lanes、512-bit refill、cross-token reuse=4；没有新建 run、回退 DSE 参数或修改共享模板。QKV 时序候选通过 150 MHz 门槛，时序优化在此停止。

| 指标 | 当前状态 |
| --- | --- |
| 最新 Stage-6 | exact-board VCS compile/elaboration/link 通过，return code 0；compile-only，仿真跳过 |
| 当前源码 source-cycle analysis | 16 tokens、12层；source schedule=8,856,360 cycles；steady-state II=29,376，final-token tail=495,987；编译快照SHA-256=`fc0fc066a48a8b2b15b9801b092bad6f48d5ddb8926c2bc8e90e1f55ae3edf6c` |
| 当前源码 Vivado QoR | archive `0db1767022fb11079fef37c5fdd96fe29d26cb02de097159a7e79a8a6f7fdff9`；OOC post-synthesis Fmax估计=153.680652 MHz；source-calibrated DSE=9,086,656 cycles、估算吞吐=270.604546 token/s |
| 资源 | LUT/FF/DSP=229,531/80,672/1,600；BRAM36/BRAM18/URAM=123/21/97 |
| 关键路径 | FFN up outputMem BRAM写时钟到 FFN Q memory RAM 输入；data path delay=6.165 ns，4 ns XDC下 slack=-2.507 ns |
| 时序目标 | 用户设定的150 MHz门槛已达到；timing history measurement index 8，`new_best_clock=true` |
| 正式 Experiment 2/3 score | `formal_score_runs_completed=0`；当前DCG revision仍为pilot，不能声称DCG因果性能收益 |
| Evidence binding E1–E4 | 第二次运行4/4通过；stale-evidence acceptance=0，false invalidation=0；首轮失败记录保留 |

153.680652 MHz 与 9,086,656 estimated cycles、270.604546 token/s 均绑定 archive `0db1767022fb11079fef37c5fdd96fe29d26cb02de097159a7e79a8a6f7fdff9`。吞吐按 `153.680652 MHz × 16 tokens / 9,086,656 cycles` 计算；周期来自 source schedule 加 DSE refill 校准，不是 RTL 仿真或板上计数。schedule假设weights resident、无外部 backpressure；DDR miss/refill等待和board-shell开销未实测。Vivado明确提示 OOC 时钟端口未设置 `HD.CLK_SRC`，因此该结果不是post-route时钟树/clock-skew结果；timing report中的4 ns目标仍有负slack。它只表示OOC post-synthesis Fmax估计达到150 MHz，不代表250 MHz约束时序闭合。

Run-local QKVProjection 修改将整数 Q/K/V requantization 放入带valid跟踪的流水路径，使同步 projected-memory 读取先进入capture register，再完成原有定点表达式；最终标量排空后才允许输出。增量 Chisel compile、contract check、两个顶层 elaboration 及 Stage-6 exact-board VCS compile/elaboration/link 通过，仿真跳过。相较前一 archive `318c3a...`（119.502868 MHz、11,985,808 estimated cycles、159.525823 token/s），当前Fmax提高约28.6%；周期模型也随源码重新分析，因此吞吐变化不能单独归因于频率。关键路径已从QKV requant化路径移到FFN up输出存储器至Q存储器写入路径。

报告与源码快照位于 `ACCORD/run/backend_board/measurements/0db1767022fb11079fef37c5fdd96fe29d26cb02de097159a7e79a8a6f7fdff9/`；实验根目录的 `accagent/experiments/accord/results/dcg_cross_token_reuse_revision_20261024T164300+0800_v2/observed_results.json` 与 `experiment_manifest.json` 已同步测量摘要和证据哈希。相关执行日志为 `ACCORD/stage6_after_qkv_requant_timing_patch_w8api_20261026.log` 和 `ACCORD/stage7_after_qkv_requant_timing_patch_w8api_20261026.log`。

正式Experiment 2/3仍未计分。现有B2 prompt-clean故障修复有真实VCS fail-to-pass记录，但没有非空hash-bound CCTG causal slice；不能将其标成CCTG图引导根因定位的完成证据。下一步应继续补最小可审计的E2设计约束更新与E3故障定位/修复案例，并把timing QoR与机制因果证据分开报告。

实验起点（按用户2026-10-23最新决定）：本轮直接采用现有 GPT-2 与 Gemma 归档 QoR 作为可用实验数据和冻结起始设计，不等待额外仿真或实现运行。GPT-2/GPT-6.1-Sol 采用 `w4a8_20261018_gpt2` 的 source-calibrated throughput-best 归档 `d2fd445acbc87db4f04b5a6edc09a7134b6a9babffcd6bdf45f3495bb1f1ced8`（175.223410 MHz、3,147,140 cycles、890.832488 token/s）；Gemma/GPT-6.1-Sol 采用 `gemma3_gpt61_20261020` 的 source-calibrated throughput-best 归档 `256a109738f6e99b16b12d8d980d337db41dce612b94d838b17859d34a3416cd`（121.832359 MHz、15,536,482 cycles、125.467126 token/s）。每组数值必须与其自身源码归档绑定；历史报告记录的证据类型继续保留，不能将不同归档的时钟、周期和吞吐拼成同一个候选。以下案例、验收门槛、消融配置和预算保持不变。

## 最新执行状态（2026-10-25T19:11:15+08:00）

当前优先完成用户批准的代表案例；81次重复运行保留为扩展计划，不作为这些结果的前置条件。当前DCG revision case为 `dcg_cross_token_reuse_revision_20261024T164300+0800_v2`，只将reuse从8改为4，阵列8×8、8 lanes、4个activation bank、512-bit refill等保持不变。机器可读汇总：`accagent/experiments/accord/results/dcg_cross_token_reuse_revision_20261024T164300+0800_v2/observed_results.json`。

| 已完成项目 | ACCORD | B0 |
| --- | --- | --- |
| Stage-4参数传播检查 | 6/6通过，reuse=4 | 6/6通过，reuse=4 |
| Stage-5 Chisel编译/展开 | 6条命令，返回0；119.842 s | 6条命令，返回0；115.621 s |
| exact-board VCS编译/展开/链接 | 待完成；selector、source review、board identity通过；manifest executor已修复，Agent正在补齐完整board adapter | 已通过，返回0 |
| 生成完整顶层的Vivado综合 | 待完成（首次adapter patch锚点0次匹配，原run重试） | 已完成，0 errors/0 critical warnings |
| 综合Fmax估计 | 待测 | 17.057278 MHz |
| DSE结构周期估计（16 tokens、12层） | 待记录 | 8,702,008 cycles |
| 综合频率与DSE周期计算的吞吐率 | 待测 | 31.362469 token/s |
| 资源LUT / FF / DSP | 待测 | 239,753 / 29,777 / 1,650 |
| 资源BRAM36 / BRAM18 / URAM | 待测 | 123 / 21 / 97 |

B0原始报告和对应源码已保存到 `B0/run/backend_board/measurements/b7405a947a50121ab896f1220d20c4c186a31336683aeefe31bbf65ef3cca019/`。这是固定8×8候选的机制实验结果，与历史175.223MHz的最终GPT-2设计为不同归档，不能混用。周期与吞吐按既有DSE估算口径记录，仿真未运行。

已纠正执行范围：额外完整控制器继承旧task_spec的100MHz/200token/s目标并请求DSE回退，已在任何参数修改前停止该控制器。固定revision不进入改变阵列/缓存的额外设计搜索；ACCORD仍在原run继续验证，之后用单stage入口完成一次后端测量。

其他已完成材料继续保留：E1–E4确定性证据绑定测试4/4通过；Gemma同一声明顺序故障的B2 prompt-clean重放已完成真实VCS fail-to-compile-pass。后者与历史ACCORD iteration41均有真实工具和patch，但历史episode没有非空hash-bound CCTG causal slice，因此可报告修复行为，不把它改写为已完成的图引导根因定位优势实验。

## 最新状态（2026-10-24 17:43 +0800）

- 论文计划中的 Experiment 2（DCG 跨阶段一致性）与 Experiment 3（DCG/CCTG 故障追踪修复）尚未完成，正式 `formal_score_runs_completed` 仍为0。当前多组 DCG 与 CCTG 运行属于 pilot，不能据此宣称核心机制已得到验证。
- E1–E4 确定性 evidence-binding 测试已完成4/4：stale-evidence acceptance=0、false invalidation=0。该测试只验证证据失效/保留规则，不包含 Agent run、VCS 或 Vivado 结果。
- DCG pilot 已完成若干 GPT-2 ACCORD/B0 Stage-4/5 对照；近期 revision 的候选域各只有一个合法候选、DSE测量为0，ACCORD/B0 生成参数和核心 RTL 相同。因此它们只证明参数传播/编译闭环可运行，没有证明 DCG 带来选型或 QoR 收益。
- CCTG 的 Gemma 同故障 B2 replay 已修复声明顺序问题并恢复 exact-board VCS compile/elaboration/link，返回码0；仿真未运行。该 episode 没有非空、hash-bound 的 CCTG causal slice，属于 compile-only 修复 pilot，不是 graph-guided failure-tracing 的直接证据。
- GPT-2 DeepSeek 与 Gemma/GPT-6.1 两个 run 的 `case_vcs_functional_sim.json` 虽为 `status=pass`、returncode=0，但各自工具报告明确写明“exact-board VCS compile and elaboration passed; simulation intentionally skipped”。按证据内容二者只能记为 compile/elaboration pass，不能计作 VCS 功能仿真通过或第三层完整闭环。
- GPT-2 Claude/Fable51 run 仍卡在 `case_multilayer_pipeline`，repair transaction `0027fe75716a45c892d0dd5612f88950` 当前 `inflight`；最新上游返回 HTTP 403 `insufficient_user_quota`，框架按既有900秒退避重试。该线尚无本轮修复 patch 或 Stage-6 通过结果。
- 对 `dcg_activation_banks_revision_20261024T122503+0800` 的独立源级复核确认：revision 为 `activation_banks: 4 -> 2`；ACCORD/B0 都将2写入 `GeneratedDesignParams.scala`，各121个 Scala/RTL文件之间哈希完全一致。相对activation_banks=4基线，121个文件中15个发生变化，限于生成参数及activation-memory模块；`GeneratedAcceleratorTop.sv` 与 `GeneratedAxiDdrTop.sv` 未变化。双方Stage-4均6/6检查通过，Stage-5均6条Chisel编译/展开通过。该案例支持“约束更新可传播至下游产物”的机制闭环观察，但ACCORD/B0结果相同、DSE为1个合法候选且0个测量值，不能声称DCG的比较优势或QoR收益。
- 进一步审计历史运行报告时，扫描到的 `causal_slice_sha256` 与 `sacg_cctg_causal_slice_sha256` 字段均为空。历史 exact-board VCS fail->pass轨迹（包括 Gemma 声明顺序修复和 GPT-2/Llama 编译错误）有真实工具诊断/源码修复，但没有非空 hash-bound causal slice；所以不能用作 CCTG 图引导定位的已完成证据。当前CCTG材料仍仅为 compile-only B2 pilot。
- Claude transaction 最新状态为 `attempt_count=54`、`retry_count=53`，最后一次403在16:24左右；报告显示多层 harness 缺失/compile-only scope未绑定，AXI/DDR与VCS依赖门因此未运行。当前额度重试窗口仍在等待；本轮没有新patch、VCS、仿真或QoR结果。
- 修正后的 DCG cross-token-reuse 配对 case `dcg_cross_token_reuse_revision_20261024T164300+0800_v2` 的 ACCORD/B0 Stage-4 仍在原 transaction 中等待 W8API：截至17:43，重试数分别为38和31，最新均为 HTTP 503 `No available channel for model gpt-6.1-sol`。各自只有1条预处理候选、0条 DSE measurement；该候选不是 Agent 已选结果，Stage-5 尚未启动，所以本轮没有新 DSE、QoR、资源或性能数据。
- 对 `weight_memory=xpm_uram` 的含义已用已接受基线产物复核：该字段表示 bounded `WeightTileCache` 的 XPM primitive。基线 `memory_layout.json` 中 `weight_buffer_a/b` 各为3,568,128 bytes，位于 DDR 双缓冲；DSE 的 tile-cache 容量按 bounded cache 计算。因此它不表示完整模型权重驻留片上，也不构成本次实验架构偏离。修正 case 的目标仍仅是 cross-token-reuse 8→4，且只要求 Stage-4/5 compile gate。
- 17:54 复核：ACCORD/B0 仍为同一 Stage-4 transaction，重试计数已分别达到44/38，最新均为W8API 503；没有新增参数绑定或测量文件。继续等待服务恢复，不能把预处理候选或重试次数作为实验结果。
- 19:40 复核：同一事务的重试计数已分别达到116/109，最新仍为W8API 503；两个 Stage-4 进程存活，但尚无 `parameter_binding.json`、Agent result 或 DSE measurement，Stage-5 及后续工具门未启动。
- 19:52 复核：ACCORD/B0 重试计数已分别达到123/117，最新仍为W8API 503；Claude exact-board generation transaction 为68/67，仍为403额度错误。Claude 的多层 harness gate 仍失败，依赖门未运行；三条活动进程均存活，正式 Experiment 2/3 计分不变。
- 20:08 复核：ACCORD/B0 重试计数已分别达到135/128，Claude exact-board generation transaction 为69/68；错误和依赖门状态均未改变，尚无新 Stage-4/Stage-5 或正式 Experiment 2/3 证据。
- 21:46 复核：ACCORD/B0 重试计数已分别达到200/194，Claude exact-board generation transaction 为76/75；仍无新绑定、DSE measurement、VCS 或正式 Experiment 2/3 结果。
- 23:13 复核：ACCORD/B0 重试计数已分别达到261/254，短暂等待后仍为W8API 503；Claude transaction为82/81且仍为403额度错误。Stage-4没有完成文件，Stage-5及后续工具门未启动，正式Experiment 2/3不计分。

## 最新实验状态（2026-10-24 11:40 +0800）

- 新的干净 B2 replay 位于 `accagent/experiments/accord/results/cctg_b2_prompt_clean_20261024T1105+0800/`，以 Gemma 同一声明顺序故障为输入；冻结 `compute_slot.sv` SHA-256 为 `2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`。Repair prompt 与成功 patch 的 exact-board generation prompt 已做实际产物审计，过滤运行目录路径后，CCTG 专用字段及因果/历史修复引导词均未命中。
- Agent 将 scheduler/AXI bookkeeping 声明移到首次引用前；最终源码 SHA-256 为 `6d2d3192a7628bde1956c5e39bb0076f4503cd9921e1df82872b2c5110fe12c0`。一次较早响应把已有 binding manifest 标成 `create`，事务被拒且没有写文件；下一次 Agent 响应提交源码编辑，框架重绑 manifest 后应用通过。
- 远端 exact-board VCS compile/elaboration/link 返回码 `0`，报告 `compile_only_pass`，33个模块完成编译；编译、展开、链接 CPU 时间分别为67.761、1.630、0.403秒。Stage-6/debug loop `board_axi_ddr_closure` 通过；simulation 为 `not_run`，不能称为完整功能仿真通过。
- 该配对探索案例显示：在这一个声明顺序故障上，未接收 CCTG 专用引导的 B2 Agent 也修复并恢复编译，因此不能据此声称 CCTG 的普遍优势，也不能用单案例否定其对复杂故障的作用。正式扩展评分仍为0；本案例没有QoR、资源、时序、周期或吞吐数据。

## 较早实验快照（2026-10-23 21:33 +0800）

## 既有实验快照（2026-10-24 01:58 +0800）

- CCTG B2 replay 在真实 exact-board VCS compile-only gate 上通过：初始 `compute_slot.sv` SHA-256 为 `2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`；Agent 第一次修改后为 `fb5490b3...`，第二次修改后为 `cc0df1846be97980e00f879ab2e6ef7803b2629e02c2b9513f91a0aed524a0f9`。最终报告 `status=pass`、VCS return code `0`、simulation `not_run`，只算编译/展开/链接通过，不算功能仿真通过。
- 有效日志为 `accagent/experiments/accord/results/b2_prompt_isolated_replay_20261024T001017+0800/b2_stage6_clean_v2.log`。复核后更正此前“提示已完全隔离”的判断：旧补丁结论和 CCTG 专用字段已从提示中移除，但还残留一条“causally affected interface family”通用修复指引。本轮可以作为 B2 compile-positive replay 记录，不作为完全干净的 CCTG 消融计分。已将该指引加入 B2 静态提示过滤；`tests.test_accord_experiment_profile` 5/5 通过，`py_compile` 与 `git diff --check` 通过。该过滤修复待后续 B2 run 真实生成提示后再验证。
- 已有 GPT-2 `lanes 16→8` ACCORD/B0 配对仍是中性 Stage-4/5 pilot：双方选择与生成的核心 RTL相同，六条 Chisel 编译/展开通过，但无实测 DSE 候选或 QoR 数据，不能声称 DCG 收益。
- GPT-2 weight-cache tile revision 配对实验 `dcg_cache_tile_revision_20261024T0110+0800_v2` 已完成 ACCORD/B0 Stage-4/5。共同 checkpoint SHA-256 为 `d9f226a2dfe53125c512cbd15398838b90c4dc5733040595ae1fe99d69f85b37`；两边均选择 `arch_2003908986b3`，绑定 8×8、W4A8/I32、`cache_tile_words=512`、2 个 tile、512-bit refill、8-token reuse、integer DSP。两边各有1个合法候选、0个实测候选，Stage-4 静态检查6/6通过。
- 两边 Stage-5 报告均为 `ready`；6条 Chisel 编译/展开命令均 return code 0，代码生成契约、package static 与 physical binding 检查均通过。剔除 build cache、日志和 run-local simulation metadata 后，134个源级生成文件的 SHA-256 全部一致。日志分别位于该 case 的 `ACCORD/stage4_parameter_binding.log`、`ACCORD/stage5_codegen.log`、`B0/stage4_parameter_binding.log`、`B0/stage5_codegen.log`。

## 2026-10-24 17:07 +0800 修正 case 运行状态

- 无效的 `dcg_cross_token_reuse_revision_20261024T132813+0800` 已排除：其设计空间错误地把 `activation_banks` 限制为2，和只修改 reuse 的 task card 不一致。
- 已建立修正配对 case `dcg_cross_token_reuse_revision_20261024T164300+0800_v2`。输入哈希已固定，`activation_banks=4`，唯一 revision 为 `cross_token_reuse_tokens: 8 -> 4`；ACCORD/B0 均从无 Stage-4 工件的 GPT-2 Stage-3 checkpoint 开始。
- ACCORD/B0 Stage-4 都已启动，尚未进入 Stage-5。W8API 当前对 `gpt-6.1-sol` 返回 503 `model_not_found`，两边事务按既有退避策略重试；本 case 当前 `formal_score_counted=false`、DSE measurements=0、VCS/simulation/QoR 均 `not_run`。不把等待中的事务写成完成结果。
- 由于候选域只有一个合法点，这组结果是跨阶段状态传播/生成闭环的中性 pilot，不能证明 DCG 提升选型能力，也不能说明 tile=512 的 QoR 更好。未运行 VCS/功能仿真或 Vivado；没有新增资源、频率、周期、吞吐数据；不计入正式81-run评分。原先使用旧约束快照的首版目录保留并标记无效，不纳入本配对结果。

原 `formal_score_runs_completed=0` 仍表示正式扩展评分尚未累计；本页后续记录的快速案例是实际运行证据，但不自动转成正式分数。

| 机制 | 已运行案例 | 真实工具结果 | 当前结论 |
| --- | --- | --- | --- |
| DCG | GPT-2 ACCORD/B0 配对；请求 lanes 16→8，阵列形状由 Agent 在4个合法候选中选择 | 两组均完成 Stage-4/5；6条 Chisel 编译/展开命令全部返回0；两组均选择8×8，核心参数及顶层 RTL 相同 | 流程 pilot；本案例未观察到组间差异，不能称为DCG收益 |
| DCG | GPT-2 ACCORD/B0 cache-tile revision；共同 checkpoint 请求 `cache_tile_words 256→512` | 两组均完成 Stage-4/5；各自1个合法候选、0个DSE测量；6/6静态检查和6条编译/展开通过；134个源级生成文件哈希一致 | 中性编译闭环 pilot；单候选使其不能区分机制选型收益；无仿真、QoR或性能数据 |
| CCTG | Gemma 相同 VCS 故障快照；历史 ACCORD iteration 41 与干净提示 B2 replay `cctg_b2_prompt_clean_20261024T1105+0800` | 两组 exact-board VCS compile/elaboration/link 均通过；B2 33个模块、返回码0；仿真未运行；B2 实际提示审计未检出 CCTG 专用引导 | 单案例配对探索：此声明顺序故障无需 CCTG 专用引导即可修复；不构成普遍或统计因果结论 |

原 `formal_score_runs_completed=0` 只表示扩展81-run评分尚未累计，不表示没有实验运行。以上快速案例已有真实 Agent 和工具轨迹；tile revision pilot 未完成完整DSE、仿真或新一轮Vivado实现，也没有产生新增QoR/吞吐数据。各配对输入、哈希、调用和日志路径见相应时间检查点及实验目录 manifest。

## 快速推进口径（2026-10-23）

按用户最新决定，原方案中的 81 次重复运行和完整 B0/B1/B2 设施是扩展评测目标，不再是启动实验的前置门槛。先各取一个有现成真实材料的代表案例，做轻量、可解释的机制案例研究；先运行先报告，之后有时间再扩展重复次数和案例数。每个案例记录实际输入、源码版本、Agent 输出和实际工具结果即可，不要求先搭完整 benchmark 平台或严格隔离式评分器。

- DCG 案例候选：使用冻结 GPT-2 设计，将合法 compute parallelism 从 16 改到 8。比较默认 ACCORD 与 `B0` 提示上下文消融，检查 Agent 是否把新决策应用到相关配置和生成结果。`B0` 仅从 Agent 提示中移除 SACG/DCG 状态及派生记忆；任务规格、模型参数、工具报告和系统确定性 gate 保留。因此结果只解释图上下文对 Agent 决策的作用，不声称关闭了框架内部 gate。
- CCTG 案例：复用 Gemma `gemma3_gpt61_20261020` 的 Stage-6 iteration 41。原始 VCS `Error-[IND]` 指向生成的 `compute_slot.sv` 前向引用；GPT-6.1-Sol 将问题定位为 `write_busy`、`rstate`、`read_kind` 的声明顺序，局部调整后 exact-board VCS compile/elaboration 返回 0。该结果是已有 ACCORD 轨迹；若可从该轮保存的失败前 repair bundle 快速恢复，则补跑一次相同输入的 `B2` 对照。不能恢复时先把 ACCORD 轨迹作为单案例机制证据报告，明确尚无配对消融，不因此阻塞 DCG 案例或全流程。
- 快速结果按案例报告首次诊断、修改范围、关键 gate 结果和调用/耗时；不把单案例写成统计显著性或普遍泛化结论。保留原定 81-run 协议供后续扩展，但不等其全部准备完成才开始。

### 快速案例执行状态（2026-10-23 19:24 +0800）

- CCTG B2 replay 已启动：从 Gemma iteration 41 的保存 repair package 恢复原始 `compute_slot.sv`，SHA-256 为 `2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`。输入副本和所有新输出位于 `accagent/experiments/accord/results/cctg_b2_20261023T190653+0800/`，未修改原 Gemma run。
- 路由记录已纠正：首次 Stage-6 repair loop 启动时只显式设置了 `B2` profile，继承了 shell 中的 Toska endpoint；该轮9次 HTTP 503 属于 Toska，不能计为 W8API 结果。当前进程已退出，尚无该次请求的 Agent 修复或最终 VCS 结果。
- DCG `lanes: 16 -> 8` 的 ACCORD/B0 运行尚未启动。快速案例不是完整正式计分，正式对照计数仍为 0；81-run 仍是后续扩展规模。

### 路由纠正与恢复状态（2026-10-23 20:55 +0800）

- 更正 20:45 检查点：B2 repair 请求进程继承了 `https://api.toskaxy.xyz/v1`，不是 W8API；其9次 `model_not_found` HTTP 503 只能归因于 Toska 路由状态，不能作为 W8API 可用性或实验效果证据。没有修改 RTL，也没有得到该请求的修复结果。
- W8API 配置源 `/home/remote/.config/codex/ciykj-api.env.pre_toska_20261017` 已核验为 `https://www.a8pi.com/v1`、`gpt-6.1-sol`，fallback endpoint/key 为空；后续必须在启动 shell 中显式 source 该文件并清空 fallback，再运行同一个隔离 B2 run。
- Stage-6 初始 exact-board compile-only 已在固定故障 `compute_slot.sv` 上复现 `write_busy`、`rstate`、`read_kind` 未声明；当前验证和修复报告保留在 B2 run 下。活动 PID `619546` 已不在运行；GPT-2/Claude PID `144785` 与本实验无关，保持原状。
- 恢复时从 `run/verification/sacg_state.json`、`B2`、`board_axi_ddr_closure` 继续，远端 VCS 仍为 compile-only；不新建或覆盖 B2 run。GPT-2 DCG 的 ACCORD/B0 仍是单候选流程 pilot，尚无 DSE 测量或可归因的 DCG 收益。

### CCTG快速案例结果（2026-10-23 21:01 +0800）

- 已在同一 Gemma B2 隔离 run 中恢复流程。进程环境实测为 W8API `https://www.a8pi.com/v1/responses`、`gpt-6.1-sol`，fallback 为空；本轮两次 Agent 调用均一次成功，没有 Toska 请求或重试。
- W8API repair Agent 用约41.7秒读取当前 Stage-6 证据并选择 exact-board compile repair；随后 exact-board integration generation Agent 用约39.2秒，将 `compute_slot.sv` 中 `write_busy`、`rstate`、`read_kind` 声明移到首次引用之前并移除重复声明。修复前源码 SHA-256 为 `2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`，Agent patch application 为 `pass`，修复后 SHA-256 为 `cc0df1846be97980e00f879ab2e6ef7803b2629e02c2b9513f91a0aed524a0f9`。
- 真实远端 exact-board VCS compile/elaboration/link 返回码为0，报告 `compile_only_pass`，33个模块完成编译；Stage-6 loop 对 `board_axi_ddr_closure` 为 `pass`。本实验按 compile-only policy 跳过仿真，不能据此声称全功能仿真通过。
- 这证明该 B2 单案例能根据真实编译器报错完成局部修复并恢复编译，但不构成 CCTG 优势的因果证据：B2 同样修复成功，且当前 B2 prompt 仍可能残留通用 guided-repair 文案。需将其与 Gemma iteration 41 的 ACCORD 轨迹按同一故障、修复范围、调用次数、耗时和 VCS结果并列；对机制差异只作有限案例观察。
- 完整运行日志：`accagent/experiments/accord/results/cctg_b2_20261023T190653+0800/run/experiments/b2_stage6_w8api_recovery_20261023T2056+0800.log`。下一项工作转向一个更有判别力的轻量 DCG 对照：用户只给高层修改意图，依赖参数留给 Agent 推导，再观察跨阶段状态与生成硬件是否一致；不启动81次扩展评测。

对于 Experiment 2 和 Experiment 3，我建议建立一套统一的 Controlled Cross-Stage Evaluation：从经过验证的真实加速器设计出发，构造具有明确设计依赖或已知根因的测试任务，让 ACCORD 和消融版本在相同条件下完成任务，并通过独立工具判断结果。

这里有一个特别重要的区分：

|            | Experiment 2：Consistency | Experiment 3：Failure Tracing |
| ---------- | ------------------------ | ---------------------------- |
| 核心问题       | 已有设计决策能否在各阶段保持一致？        | 观察到下游失败后，能否找到正确的修复位置？        |
| 提供给 Agent  | 设计规格或明确的修改请求             | 真实 EDA 失败及工具报告               |
| 不提供给 Agent | 受影响组件的完整答案               | 预先标注的根因和正确补丁                 |
| 主要机制       | DCG 的约束传递、依赖更新与检查        | DCG/CCTG 的依赖回溯与限定范围修复        |
| 成功标准       | 所有受影响组件与当前设计决策一致         | 根因得到修复，原失败消失，已有正确行为未被破坏      |

尤其是 Experiment 2 的反向修改测试，不要让 Agent 自己先定位故障根因。例如，直接给出“根据 backend refinement 的结果，将 compute parallelism 从 16 改为 8”的正式修改请求，然后检查它能否正确更新所有相关设计状态和硬件产物。

反过来，Experiment 3 才应只给出 timing report，让 Agent 自己判断到底应该修改 architecture、RTL 还是 backend constraints。

这样能够把两个贡献的作用分开，避免实验结果混杂，导致无法判断究竟是哪个机制带来了改善。

下面给出可以直接用于实现实验 harness、组织 benchmark 和生成论文结果的执行协议。

## 一、统一实验设置：先保证结果具有因果解释力

### 1.1 两个实验使用相同的设计基础

建议选取已经通过真实功能与 FPGA 实现验证的两个设计：

| 项目                 | 设置                                 |
| ------------------ | ---------------------------------- |
| Target Models      | GPT-2 117M、Gemma 3 1B IT           |
| Numerical Policy   | 现有 W4A8                            |
| FPGA               | 现有 VU9P 板卡                         |
| Hardware Templates | 相同的 Chisel 模板库                     |
| Tools              | 相同版本的 Chisel/SBT、VCS、Vivado        |
| Upstream LLM       | 固定一个模型，优先 GPT-6.1-Sol              |
| Starting Point     | 同一个已验证的 design snapshot/checkpoint |
| Evaluation         | 独立 checker + 真实功能仿真 + 必要的综合/实现     |

不建议这两个实验同时比较 GPT-6.1、DeepSeek 和 Claude。先固定 LLM，才能把差异归因于 ACCORD 的设计机制，而不是上游模型能力。

可以从现有 checkpoint 开始执行局部任务，以降低重复设计成本。但每个测试任务的起始源码、设计参数、工具报告和运行上下文必须完全一致。

### 1.2 首先确定两个公平的 Baseline

我建议不要只使用一个笼统的 `w/o DCG`。两个实验分别需要不同的消融，才能准确识别机制作用。

| 配置                    | Cross-Stage DCG | Forward Propagation | Dependency-Guided Repair | Evidence Binding |
| --------------------- | --------------- | ------------------- | ------------------------ | ---------------- |
| B0: Handoff-Only      | 无               | Agent 自主处理          | Agent 根据日志自主处理           | 保留基本运行记录         |
| B1: Static DCG        | 有               | 无自动依赖传播             | 无依赖引导                    | 有                |
| B2: w/o Guided Repair | 有               | 有                   | 无                        | 有                |
| ACCORD                | 有               | 有                   | 有                        | 有                |

其中：

Experiment 2： 主要比较 `B0` 与 `ACCORD`。对于迭代修改任务，再增加 `B1`，检验收益是否来自依赖传播，而不仅是将约束放进一张图。

Experiment 3： 主要比较 `B2` 与 `ACCORD`。两者都拥有相同的 DCG、设计历史及合法工具访问权限，唯一区别是能否利用依赖关系进行根因追踪和修复范围选择。

这比在 Experiment 3 中比较没有 DCG 的 B0 与完整 ACCORD 更有说服力，因为后者同时改变多个机制。

#### Baseline 的实现要求

B0 仍应获得与 ACCORD 相同的设计事实、已有生成源码、工具日志及阶段交接记录。可以用普通 JSON/Markdown handoff 保存这些信息，但不提供跨阶段依赖边、自动受影响范围计算和跨阶段 contract gate。

B1 拥有静态图和检查能力，但修改后不自动查找依赖闭包、通知受影响阶段或触发相应更新；Agent 仍可以通过正常读取资料和工具反馈自行完成修改。

B2 保留 DCG 和所有已有检查器，但不提供 CCTG 的 causal frontier、候选根因排序与依赖限定的可编辑范围。Repair Agent 可以自主查看完整仓库和真实工具报告，不能人为禁止它修改正确的文件。

这里还需要处理一个工程细节：如果直接禁用 DCG 会使现有 Stage Controller 无法执行，那么必须为 baseline 增加一个仅用于保持工作流可运行的适配层。不能让 baseline 因缺少某个字段直接崩溃，再把这种失败算作 ACCORD 的优势。

### 1.3 如何获得独立的 Ground Truth？

这是整个实验可信度的关键。

ACCORD 的 DCG 和 checker 不能同时充当被评价对象和唯一的正确答案来源。否则容易出现一种循环论证：

> ACCORD 声称某些组件受到影响，ACCORD 自己更新这些组件，ACCORD 的 checker 判断全部正确，因此 ACCORD 有效。

我建议为每个测试案例准备两份彼此隔离的文件：

Public Task

所有对照 Agent 都能读取。包括起始 checkpoint、正式规格或修改请求、工具报告、允许的操作和统一预算。

Private Oracle

仅评测程序能够读取。包括权威约束、正确的受影响范围、已知根因、验证条件以及可以接受的最终设计状态。

Private Oracle 应由独立的模型配置/量化材料、实际硬件源文件依赖、工具输入清单，以及人工核对的参考修改共同建立。

对于 Experiment 2，需要分别标注：

- `must_update`：必须发生实际修改的设计组件；
- `must_revalidate`：内容未必需要修改，但之前的验证结果已经不能覆盖当前版本；
- `unaffected`：不应受到本次修改影响的组件。

这三个集合不能混为一谈。因为\*\*“需要重新验证”不等于“必须修改源码”\*\*。

对于 Experiment 3，Private Oracle 则记录已知根因和可以接受的修复集合。不能只允许某一个固定补丁，因为真实硬件故障可能存在多种合法修复方式。

## 二、Experiment 2：Cross-Stage Design Consistency

### 2.1 建议将测试集划分为 Forward 与 Revision 两类

我建议正式实验使用 6 个案例：3 个 Forward + 3 个 Revision。

| ID | 类型       | 测试任务                                        | 主要跨阶段依赖                                        |
| -- | -------- | ------------------------------------------- | ---------------------------------------------- |
| F1 | Forward  | GQA Q/KV head mapping 与下游 projection 绑定不一致  | Model → Template → Pipeline → RTL              |
| F2 | Forward  | 早期 W4A8 signedness/rounding 约束与下游实现不一致      | Numeric Policy → Template → RTL                |
| F3 | Forward  | 512-bit AXI/DDR 约束与下游 cache/refill 配置不一致    | Board → Memory → RTL                           |
| B1 | Revision | 已确定将 compute parallelism 从一个合法配置改为另一个合法配置   | DSE → Compute Array → Buffer/Stream → RTL      |
| B2 | Revision | 修改 FIFO depth 或 pipeline buffer 参数          | Pipeline → FIFO/IP → RTL/Resource              |
| B3 | Revision | 修改 weight-cache tile geometry，要求更新相关访存与调度配置 | Memory Schedule → Cache → Address/Layout → RTL |

这里的具体参数值必须从你现有框架真正支持、并经过检查的合法候选中选取，而不是为了构造实验随意写入新硬件参数。

例如 B1 可以采用 `lanes: 16 → 8`，但前提是两端配置均属于当前设计空间，且修改后存在可以通过相关设计约束的实现。

F1 则优先选择实际存在 Q/KV head 数量差异、且模型配置与权重可独立核对的目标模型。

### 2.2 Forward 实验怎样构造才严谨？

Forward 的本质是：

上游正确决策已经存在，但后续设计状态没有正确遵守这个决策。

我建议每个 F 案例执行下面的流程。

Step 1

选择正确的上游设计状态

例如，从模型配置中确定真实 Q/KV head mapping，并在 Stage 1 的权威模型状态中固定。

Step 2

构造一个真实的下游不一致状态

在合法 checkpoint 的下游 handoff 或待更新 artifact 中保留一处过期绑定。例如，保留旧 Q/KV projection 配置，但不修改权威模型规格。

Step 3

启动两组 Agent

B0 与 ACCORD 获得完全相同的起始设计与任务。ACCORD 可使用 DCG 的跨阶段约束，B0 只能依靠已有材料与正常阶段交接。

Step 4

独立检查最终结果

评测程序核对真实参数绑定、最终源码、功能仿真及相关工具结果，而不只读取 Agent 报告的 PASS。

特别要注意：不要只注入一个字段错误，然后统计 DCG checker 能否发现该字段不同。

这最多证明 checker 可以检测预先定义的约束，却不足以证明整个跨阶段设计工作流更可靠。

因此，建议 F1–F3 都包含一个实际的 downstream handoff/生成阶段，让 Agent 有机会做出正确或错误决策。然后同时统计：

- 是否主动识别了不一致；
- 是否在进入昂贵 EDA 阶段前发现问题；
- 是否真正恢复了正确的下游设计；
- 是否避免错误通过局部验证后仍进入后续阶段。

构造错误时，不能直接把根因写进 Agent 的任务说明，例如“这里的 Q/KV dimension 错了，请修复”。所有方法应只知道当前需要继续完成设计，并能访问通常可见的权威规格和设计产物。

此外，正式 benchmark 不应全部来自手工注入错误。建议尽可能让其中至少一个 Forward 案例来自已有真实设计迭代中曾出现的规格/接口失配；若没有可复现的真实案例，则明确将测试集标为 controlled perturbations，不虚构自然失败来源。

### 2.3 Revision 实验怎样构造？

Revision 的任务是：

某个后期设计阶段确定了一个新的合法决策，系统需要正确更新相关设计状态、实现及验证证据。

建议以 B1 为主要案例。

#### B1：Backend-Triggered Parallelism Revision

初始设计已经完成并验证，具有固定的 architecture、RTL 和 Vivado 报告。

随后模拟后端 refinement 已经作出如下决定：

```
Accepted design revision:
  compute parallelism: 16 -> 8

Unchanged:
  target model
  numerical policy
  FPGA board
  external interface requirements
```

这里的“16 → 8”只是示意；正式实验采用经过预先验证的合法候选值。

这一请求可以由后端阶段发起，但根因判断和参数选择在实验开始前已经确定，不再要求 Agent 自行诊断 timing violation。

ACCORD 应该：

1. 将新的 architecture decision 写入当前设计状态。
2. 沿 DCG 查找需要更新或重新检查的依赖组件。
3. 通知相关 Stage Agent 更新参数绑定、RTL 和必要的 pipeline/memory 配置。
4. 使受影响的旧验证证据失效，并重新执行必要检查。
5. 输出满足新的设计决策和原有硬约束的最终设计。

B0 则可以通过通常的阶段交接、历史文件及工具反馈完成相同任务，但没有显式 DCG 传播机制。

B1、B2、B3 应分别覆盖不同传播范围。特别建议保留一个局部修改案例（例如只改变合法 FIFO depth），检验 ACCORD 是否能够避免不必要的全局修改。

这很重要，因为一个系统如果把所有文件都重新生成、所有验证都重新执行，确实也可能保持设计一致，但不能证明它能够正确识别依赖范围。

### 2.4 Experiment 2 的评价指标

建议把结果分为两个层次：最终正确性与依赖维护质量。

| Metric                        | 定义                       | 解释        |
| ----------------------------- | ------------------------ | --------- |
| Consistency Pass Rate (CPR) ↑ | 最终通过全部独立一致性检查的运行比例       | 最重要的整体指标  |
| Violation Escape Rate (VER) ↓ | 系统宣称成功，但独立检查仍发现约束失配的运行比例 | 量化错误的阶段晋级 |
| Propagation Recall (PR) ↑     | 正确处理的必要依赖项 / 全部必要依赖项     | 是否遗漏受影响组件 |
| Propagation Precision (PP) ↑  | 正确处理的依赖项 / 全部实际触及的依赖项    | 是否过度传播或修改 |
| Design Updates ↓              | 完成任务所需的设计修改轮数            | 辅助效率指标    |

主指标建议采用 CPR。

因为 CPR 直接回答：Agent 是否最终完成了跨阶段一致的设计？

VER 尤其适合验证“局部检查通过，但整体设计不一致”的 Motivation。需要把明确阻止晋级的失败与错误晋级后逃逸的失败分开，不能把两者合并统计。

Propagation Recall 和 Precision 主要用于 Revision 实验。对 `must_update` 和 `must_revalidate` 应分别计算，不能将重新执行一个 checker 当作已经修复对应的硬件组件。

对于某次运行，最终设计一致性可以形式化为：

\\[ \mathrm{Consistent}(r)= \begin{cases} 1,& \text{所有适用的独立约束与验证均通过},\\\ 0,& \text{否则}. \end{cases} \\]

进而：

\\[ \mathrm{CPR} = \frac{\sum\_{r=1}^{N}\mathrm{Consistent}(r)}{N}. \\]

这里的分母包含失败、超预算和未完成的运行，不能只统计最终成功的设计。

### 2.5 Experiment 2 必须增加一个小型消融

建议在 B1–B3 三个 Revision 案例上增加 `Static DCG`：

| 配置           | 保存依赖图 | 检查约束 | 自动传播修改 |
| ------------ | ----- | ---- | ------ |
| Handoff-Only | —     | 局部检查 | —      |
| Static DCG   | ✓     | ✓    | —      |
| ACCORD       | ✓     | ✓    | ✓      |

如果完整 ACCORD 比 Static DCG 有更高的最终一致性或更低的更新成本，就可以进一步支持：

跨阶段一致性不仅需要保存约束，还需要在决策发生变化时正确维护依赖关系。

这与论文中强调的 forward design 和 iterative refinement 两个方向完全对应。

## 三、Experiment 3：Cross-Stage Failure Tracing and Repair

### 3.1 实验目标与变量控制

这组实验最需要避免的错误是：ACCORD 同时拥有更多设计约束、更多上下文、更丰富的日志和更强的验证工具，而 baseline 只有一个简单 Repair Agent。

那样即使 ACCORD 修得更好，也无法证明收益来自 dependency-guided repair。

因此，正式对照应当是：

| 项目                             | B2: w/o Guided Repair | ACCORD |
| ------------------------------ | --------------------- | ------ |
| 初始硬件、源码及故障                     | 相同                    | 相同     |
| Upstream LLM 和 Agent 组织        | 相同                    | 相同     |
| DCG 当前状态                       | 相同                    | 相同     |
| 原始工具报告与运行历史                    | 相同                    | 相同     |
| 可使用的 EDA 工具                    | 相同                    | 相同     |
| Root-cause tracing / CCTG      | 不使用                   | 使用     |
| Dependency-guided repair scope | 不使用                   | 使用     |
| Revision-bound validation      | 保留                    | 保留     |
| 修复预算与最终判定                      | 相同                    | 相同     |

这里 B2 可以自主分析源代码、日志和历史设计决策，也可以自行推断根因。不能只给 ACCORD 完整信息，却限制 baseline 的代码访问。

ACCORD 额外拥有的应该是组织和追踪已有信息的机制，不是人工额外提供的正确答案。

### 3.2 推荐的故障测试集

建议使用 6 个故障案例，覆盖 5 类跨阶段问题和 1 个局部故障对照。

| ID | 真实工具观察到的问题                            | 已知的故障来源                             | 独立修复验收               |
| -- | ------------------------------------- | ----------------------------------- | -------------------- |
| R1 | Timing violation                      | 上游 architecture/parallelism 配置不合适   | 满足原有 timing 和资源约束    |
| R2 | Backend implementation/timing failure | XDC 或 backend script 配置错误           | 恢复正确实现约束并通过工具复核      |
| R3 | Functional simulation stalls          | Pipeline/stream 调度或 backpressure 错误 | 仿真完成、无死锁、数据顺序正确      |
| R4 | AXI/DDR 访问或输出错误                       | 上游 memory layout/stride 与下游实现不一致    | AXI 协议、地址映射及输出检查通过   |
| R5 | Golden-output mismatch                | Numeric policy 与计算模板的绑定错误           | 通过独立固定点 reference 检查 |
| R6 | 局部 RTL 功能错误                           | 当前 RTL 模块内部实现错误                     | 修复该模块并通过回归验证         |

R6 是刻意设置的 negative control。

因为并不是所有下游故障都有跨阶段上游根因。一个可靠的 root-cause tracing 机制应该能够识别局部故障，不能将所有问题都错误地向 architecture 或 model specification 回溯。

此外，R2 必须保留原始设计要求：修复 XDC 的含义是恢复正确约束，而不是放宽 clock period、false path 或其他约束来制造 timing pass。

#### 故障从哪里获得？

我建议采用两种来源。

第一类：真实历史故障。 从你已经完成的 GPT-2/Gemma 设计、仿真和时序优化日志中选取曾真实发生且已经修复的故障。需要保存失败前源码、对应真实工具日志、修复后源码和重新验证结果。

第二类：受控故障注入。 从已验证设计中，通过一个明确的上游设计修改引入故障，然后真正运行 VCS 或 Vivado 获得失败报告。Agent 接收的是失败后的实际设计及 EDA 报告，而不是注入脚本或正确补丁。

我建议优先做到 2 个真实历史故障 + 4 个受控故障。如果现有真实历史故障不足，不需要勉强凑数，但必须清楚披露测试来源。

这种测试组织方式与已有硬件 Agent benchmark 的可复现性思路一致。例如 Phoenix-bench 采用可执行 EDA 检查、预先确认的故障、修复后测试和环境固定，避免仅凭 Agent 自身描述判断修复成功。

[image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

arxiv.org



### 3.3 如何保证注入的故障确实有正确根因？

每个正式 R 案例在加入 benchmark 前都需要完成独立预检：

原始设计可以通过验证。 记录起始版本的功能与实现结果，确认不是本来就存在其他失败。

注入或历史版本能够稳定复现失败。 在相同工具与环境下执行，保存真实日志、波形或 timing report。

已知合法修复可以消除该失败。 使用预先确认的参考修复重新执行真实工具，并通过回归检查。

故障能通过指定工具观察。 如果故障只存在于配置文件、但不会产生可观察的错误，则不适合作为 root-cause repair 测试。

特别是 R1，必须谨慎。

Architecture parallelism 增大后发生 timing violation，并不自动证明根因就是 parallelism。也可能是 RTL 编码、约束、布局或其他因素。

只有通过对照实现和工具复核，确认某个架构决策确实导致该问题，才能将它标注为已知上游原因。对于存在多种有效修复的情况，应允许不同合法方案通过独立验证，不能要求 Agent 必须复现原作者的补丁。

### 3.4 一次 Repair Case 的具体执行步骤

建议按如下流程实现。

① Restore

从同一份不可变的 faulty design snapshot 恢复 B2 和 ACCORD 的工作空间。包括源码、当前设计状态、历史证据以及所需工具环境。

② Reproduce

运行指定的 VCS/Vivado 命令，确认两组看到完全相同的故障现象，并生成相同的初始日志。

③ Diagnose

B2 自主分析已有信息并提出修复；ACCORD 利用 DCG/CCTG 进行依赖回溯，定位候选根因及允许修改的设计范围。

④ Repair

两组在相同预算内修改实际设计文件。记录每次修改的位置、内容、原因、LLM 调用和真实工具检查结果。

⑤ Validate

对每个候选执行与故障类型相对应的工具检查；最终候选还必须通过独立 fail-to-pass、pass-to-pass 及适用的设计约束检查。

⑥ Evaluate

评测程序读取最终源码与工具证据，计算定位准确率、修复成功率、修复轮数及非必要修改情况。

这里建议明确区分两个测试集合。

Fail-to-Pass Tests：原始错误版本无法通过、正确修复后应该通过的测试。

Pass-to-Pass Tests：原始设计已经通过、修复后仍必须保持通过的其他功能和约束测试。

例如，一个 Agent 可能通过关闭部分 pipeline、删除出错的模块、放宽 timing constraint 或修改 golden output，让原来的错误表面消失，但同时破坏设计要求。

所以真正的 Repair Success 必须满足：

\\[ \mathrm{RepairSuccess} = \mathrm{FailToPass} \land \mathrm{PassToPass} \land \mathrm{DesignConstraints}. \\]

对 timing 案例，最后一项包含原始时序目标和 FPGA 资源边界；对数值案例，则必须使用不允许 Agent 修改的独立 golden reference。

### 3.5 如何评价 Root-Cause Localization？

建议不要只依据 Agent 是否提到了正确文件名。

你真正要评价的是跨阶段根因与修复范围。

可以定义两个粒度：

| 指标                           | 判定标准                |
| ---------------------------- | ------------------- |
| Root-Cause Stage Accuracy    | 首次明确诊断是否指出正确的设计阶段   |
| Root-Cause Contract Accuracy | 是否指出正确的约束、参数或相关设计关系 |

例如，R2 的真正问题在 backend XDC，而 Agent 认为原因是 RTL 的 arithmetic pipeline，则属于跨阶段诊断错误。

但如果 Agent 提出的另一种修改方案能够在不改变设计要求的前提下，经过独立验证真正解决故障，则应该将修复成功与原始注入根因定位分开统计，而不是简单否定有效修复。

具体执行时，要求每次诊断都产生结构化记录：

```
diagnosis:
  suspected_stage: ...
  suspected_contracts: ...
  evidence_refs: ...
  proposed_edit_scope: ...
```

两组都输出相同字段；ACCORD 额外可使用 CCTG，但 baseline 不应被要求输出它无法访问的内部 frontier。

Root-Cause Accuracy 使用第一次正式诊断计算，避免 Agent 多轮试错后才猜到正确答案，却仍被计为首次定位成功。

### 3.6 最终评价指标

| Metric                      | 定义                           | 优先级 |
| --------------------------- | ---------------------------- | --- |
| Repair Success Rate (RSR) ↑ | 固定预算内通过完整独立修复验收的案例比例         | 主指标 |
| Root-Cause Accuracy (RCA) ↑ | 首次诊断正确定位根因阶段或约束的比例           | 主指标 |
| Repair Iterations ↓         | 完成修复所需的 patch-and-recheck 轮数 | 主指标 |
| Off-Target Edits ↓          | 修改了与故障及合法修复无关的组件数量           | 辅助  |
| Tool Calls / Repair Time ↓  | 实际修复过程的工具调用与耗时               | 辅助  |

我建议正文主要报告：

RSR、RCA、Repair Iterations。

Off-Target Edits 更适合在一个具体 case study 中展示，例如：

> Baseline 反复修改 RTL，但真正的问题是 backend configuration；ACCORD 追踪依赖后定位并修复对应约束。

不过，只能在实际实验呈现这种现象时使用，不能提前假设它必然发生。

关于 Repair Iterations，要特别注意统计偏差：失败运行没有“成功修复所需轮数”。因此建议同时报告 RSR\@K，其中 K 是固定修复预算；平均或中位修复轮数明确注明仅针对成功运行，并另行报告失败运行耗尽预算的情况。

这样可以防止一个 baseline 因为大多数任务修复失败、只有最简单的任务成功，反而呈现很低的平均迭代次数。

## 四、Evidence-Bound Refinement：单独做一个低成本确定性测试

Evidence binding 属于 ACCORD 修复闭环的重要组成，但我不建议为它增加一大组随机 LLM 实验。

可以使用 4 个受控修改测试：

| ID | 修改内容            | 预期证据处理                                        |
| -- | --------------- | --------------------------------------------- |
| E1 | 修改已验证 RTL 的实际逻辑 | 受影响的 compile、functional 和 backend evidence 失效 |
| E2 | 修改目标时钟或相关 XDC   | 受影响的 timing/implementation evidence 失效        |
| E3 | 修改数值策略或模型参数     | 相关 contract、生成及验证证据失效                         |
| E4 | 修改与构建无关的说明文件    | 相关硬件验证证据仍可保留                                  |

E4 同样重要。因为“每次修改都让所有证据失效”虽然安全保守，却不能证明系统能够判断真正的依赖范围。

需要预先从真实工具的输入文件和当前构建依赖中确认预期受影响集合，然后检查：

\\[ \mathrm{InvalidationRecall} = \frac{\text{正确失效的必要证据}} {\text{所有必须失效的证据}}. \\]

另外报告误失效率，以及是否存在 Stale Evidence Acceptance。

这里必须区分“旧证据没有被错误接受”和“新的必要验证已经实际执行”。两者都成立才能宣称 evidence-bound refinement 有效。

这 4 个案例可以完全依靠确定性状态转换和真实工具报告完成，通常不需要多次 LLM 重复运行。

## 五、正式实验预算与重复次数

以上是测试内容。接下来还需要确定统一的运行协议，否则不同方法的成本和成功率无法公平比较。

### 5.1 推荐实验规模

考虑到 Vivado 的成本，我建议采用以下规模，而不是上来进行大量完整端到端运行。

| 实验                         | 案例数 | 配置数   | 每案例重复 | 总运行数 |
| -------------------------- | --- | ----- | ----- | ---- |
| Experiment 2：主要对照          | 6   | 2     | 3     | 36   |
| Experiment 2：Static DCG 消融 | 3   | 1（额外） | 3     | 9    |
| Experiment 3：Repair 对照     | 6   | 2     | 3     | 36   |
| Evidence Binding           | 4   | 确定性测试 | 1     | 4    |

总计 81 次 Agent 评测运行 + 4 个确定性证据测试。

其中 81 次 Agent 运行不意味着 81 次完整 Stage 0–7 执行，而是从冻结的相应设计 checkpoint 开始的受控任务。

实验应尽量复用模型预处理、已编译的第三方 IP 与只读工具环境，但不能在不同配置之间共享可变设计状态、修复结果或之前失败的答案。

### 5.2 固定修复预算

建议在正式实验开始前，用少量不计入最终结果的 pilot cases 测量典型成本，然后冻结统一预算。

例如：

| 预算维度               | 建议                  |
| ------------------ | ------------------- |
| Repair attempts    | 最多 5 次已提交的修改及复核     |
| LLM budget         | 对照配置使用相同 token/请求预算 |
| VCS                | 每次修改按需要执行，同样的工具权限   |
| Vivado             | 预先规定每案例允许的综合及实现次数   |
| Wall-clock         | 同一案例的所有配置使用相同上限     |
| Human intervention | 禁止对运行中的具体设计进行人工修复   |

不能让 ACCORD 运行五轮、baseline 只允许两轮。也不能允许 ACCORD 自动修改约束，但禁止 baseline 使用 Tcl/Vivado 工具。

建议记录实际 LLM tokens、EDA tool calls 和 wall-clock。完整 DCG 可能增加一定的检查或调用成本，这些也应该如实计入效率结果。

对于 expensive backend cases，建议把完整 place-and-route 作为预先定义的验收阶段，并允许前面的诊断先使用必要的局部分析工具。所有方法的工具权限必须相同，不能因为某个 Agent 选择了更昂贵的诊断路径，就事后为它增加预算。

### 5.3 三次重复怎么做？

每个案例和配置运行三次，且每次从同一份原始 checkpoint 恢复。

要固定：

- 模型与上游 LLM 版本、reasoning effort、temperature 等参数；
- Agent prompt、工具权限和实现版本；
- FPGA/XDC、数值策略、测试输入及 golden；
- 运行预算和实验成功标准。

对于不支持随机种子参数的 LLM API，不能声称通过相同 seed 保证了对应输出。应将其记录为相同配置下的三次独立重复。

报告中建议使用案例作为统计单位，三次重复用于反映 Agent 随机性。不要把同一个故障重复三次后直接当成三个相互独立的故障类别，并据此宣称很强的统计显著性。

为了避免针对测试案例过度调参，建议从每组六个案例中预先保留两个作为 holdout，不用其结果调整 Prompt、checker 规则或 repair 策略。正式报告时包含全部六例，并可标出 holdout 的表现。

## 六、复现性：每次实验到底需要保存什么？

这是我建议你真正落实到评测脚本中的部分。

### 6.1 每个 Case 必须有一个固定的 Manifest

例如对于 B1（compute parallelism revision）：

```
case_id: C-B1
experiment: cross_stage_consistency
case_type: revision

base_snapshot:
  source_commit: <git_commit>
  artifact_sha256: <sha256>
  checkpoint_stage: 4

target:
  model: <model_snapshot>
  fpga: <exact_part>
  numeric_policy: W4A8

task:
  revision_origin: backend_refinement
  parameter: compute_parallelism
  old_value: 16
  new_value: 8

constraints:
  preserve_model_semantics: true
  preserve_numeric_policy: true
  preserve_board_interfaces: true

evaluation:
  require_consistency: true
  require_functional_validation: true
  require_implementation_validation: true

budget:
  max_repair_attempts: 5
  tool_limits: <frozen_limits>
```

这只是推荐的实验数据格式，不代表当前 ACCORD 仓库已经有这些字段或对应命令。

最重要的是：该文件包含公开任务与统一约束，而不是 oracle 中的完整答案。

独立保存一个 Agent 无权访问的 `oracle_private.yaml`：

```
case_id: C-B1

ground_truth:
  required_updates:
    - <affected_artifact_1>
    - <affected_artifact_2>

  required_revalidations:
    - <verification_scope_1>
    - <verification_scope_2>

  unaffected_artifacts:
    - <unrelated_artifact>

  acceptance_tests:
    - <independent_test_1>
    - <independent_test_2>
```

这些 ground-truth 集合必须根据实际设计的依赖关系提前建立，不能在看到 ACCORD 输出后调整。

### 6.2 每个 Run 保存完整的 Input–Action–Evidence

建议最少保存：

| 记录            | 具体内容                                    |
| ------------- | --------------------------------------- |
| Input         | 起始源码、设计规格、任务、可见工具日志                     |
| Configuration | LLM/Agent、消融开关、版本和预算                    |
| Decisions     | 诊断、修改请求、选择的设计参数                         |
| Actions       | 每轮修改文件、patch、工具调用                       |
| Evidence      | VCS/Vivado 报告、仿真、golden comparison、hash |
| Results       | 修复是否成功、违反了哪些约束、实际运行成本                   |

还必须保证每条 evidence 对应明确的源码版本与工具配置，防止将早期综合结果误算为后续 patch 的结果。

对于 Experiment 3，建议每次修复都能恢复以下关联：

\\[ \text{Failure} \rightarrow \text{Diagnosis} \rightarrow \text{Patch} \rightarrow \text{Tool Result}. \\]

正式 benchmark 发布时，应包括故障版本、复现脚本、验证测试、标准答案和去除密钥后的 Agent 轨迹。这些比仅公开最终生成的 RTL 更有助于证明实验可复现。

### 6.3 三个必须避免的实验缺陷

| 潜在缺陷                 | 必须采取的措施                                                       |
| -------------------- | ------------------------------------------------------------- |
| Oracle leakage       | Agent 无法读取故障注入脚本、参考补丁、private oracle 或包含答案的 repair experience |
| Unequal information  | 所有 Agent 拥有相同原始规格、设计历史、源码和 EDA 日志；区别仅在待验证的机制                  |
| Self-evaluation bias | 最终成功必须由独立于 DCG/CCTG 的 reference、工具和测试判断                       |

对于 ACCORD 的共享 repair experience，建议正式基准运行时将其禁用或冻结为各配置完全相同的初始状态。否则后执行的案例可能从之前的修复记录中获取答案。

同样，必须在运行前固定测试案例。不能因为某个 case 中 ACCORD 失败就删除它，或者因为 baseline 意外修复成功就重新定义正确答案。

## 七、最终怎样呈现在 DAC 论文中？

虽然实际执行计划需要比较完整，但论文正文不必展示所有实验步骤。

我建议把两个 Challenge 的结果压缩成两张主要表格 + 一个简短 Case Study。

### Table 1：Cross-Stage Consistency

| Method       | Consistency Pass ↑ | Violation Escape ↓ | Propagation Recall ↑ |
| ------------ | ------------------ | ------------------ | -------------------- |
| Handoff-Only | 待测                 | 待测                 | 待测                   |
| Static DCG   | 待测                 | 待测                 | 待测                   |
| ACCORD       | 待测                 | 待测                 | 待测                   |

表格中需要注明：Static DCG 的测试范围是 Revision 子集；如果它没有执行全部六个案例，就不能把其三例结果与其他方法的六例结果直接作为同一平均值比较。可以通过分组表头或单独列出 Revision 子集来解决。

### Table 2：Failure Tracing and Repair

| Method            | RCA ↑ | Repair\@5 ↑ | Iterations ↓ |
| ----------------- | ----- | ----------- | ------------ |
| w/o Guided Repair | 待测    | 待测          | 待测           |
| ACCORD            | 待测    | 待测          | 待测           |

表下注明工具预算、案例数量、重复次数及 iterations 的统计口径。

建议用配对的逐案例结果计算总体差异，并报告离散程度或置信区间。若案例数量有限，不要只依靠单一平均值或显著性检验掩盖某些故障类型上的失败。

### Case Study：一次真实的跨阶段修复

选择实际结果中最能够展示跨阶段故障定位差异的一个案例。

例如，如果 R2 的实验最终证实：

- 下游报告 implementation/timing failure；
- baseline 将故障归因于 RTL 并尝试修改计算模块；
- ACCORD 根据 CCTG 找到 backend 配置依赖；
- ACCORD 修复对应配置，并通过相同 Vivado 验收；

那么该案例可以直观展示论文提出的 backward failure tracing。

正文中只需要展示：

Reported failure → traced dependency → corrected component → validation outcome

而不需要逐轮列出 Agent 的长篇思考或所有工具日志。

完整测试案例、运行配置、patch 和独立 checker 放入开源仓库即可。

## 八、最终需要执行的实验任务清单

Execution Checklist

1/14 completed

评测基础

[x] 冻结 GPT-2/Gemma 当前设计归档和 QoR 基线（按用户指示作为本轮实验性能数据；来源记录见 `accagent/experiments/accord/baseline_manifest.json`）

[ ] 实现 B0、B1、B2 三个公平的机制消融配置

[ ] 实现 Public Task / Private Oracle 隔离及独立判定程序

Experiment 2

[ ] 建立 F1–F3 三个前向一致性案例

[ ] 建立 B1–B3 三个设计修改传播案例

[ ] 预先确认 must_update、must_revalidate 和 unaffected 集合

[ ] 执行 36 次主要对照与 9 次 Static DCG 消融

Experiment 3

[ ] 筛选或构造 R1–R6 六个真实可复现故障

[ ] 独立确认根因与合法参考修复

[ ] 冻结 fail-to-pass / pass-to-pass 验收集合

[ ] 执行 36 次 dependency-guided repair 对照

证据与论文

[ ] 执行 E1–E4 证据失效测试

[ ] 审计全部 run 的 budget、source hash 和工具结果

[ ] 生成两张对照表及一个 Case Study

## 九、我最强调的三个结论

第一，Experiment 2 必须证明“维护设计一致性”，而不只是“检测字段错误”。 因此，最终一致性、正确更新范围和错误晋级应共同评价；前向约束继承和后期修改传播必须分别覆盖。

第二，Experiment 3 必须隔离 dependency-guided repair 的贡献。 最关键的对照是两个拥有相同 DCG 和真实 EDA 信息、但只有一个使用 CCTG 根因回溯的 Agent。只有这样，才能将修复效果的差异归因于你提出的核心机制。

第三，所有成功都必须接受独立验证。 ACCORD 的 DCG 是设计状态和决策依据，不应成为唯一的正确性裁判。最终依赖真实硬件实现、功能验证、约束检查和版本匹配的工具证据。

如果严格执行上述协议，这两组实验就能形成比较清楚的因果证据链：

Cross-stage dependencies → DCG-based consistency maintenance → fewer inconsistent designs；downstream failures → dependency-guided root-cause tracing → more reliable repairs。

我建议优先投入工程资源实现这套统一的评测 harness 和六类一致性、六类故障案例，再运行消融。它们直接决定 ACCORD 最重要的两项研究主张能否成立，比继续扩大模型数量或增加新的 QoR 曲线更有价值。

### 快速案例最新状态（2026-10-23 19:52 +0800）

- 发现先前 `dcg_lanes8_20261023T1926/` 目录内含旧 Stage-6/repair-loop 历史状态，未作为本轮运行输入；原目录保留。新建干净配对目录 `accagent/experiments/accord/results/dcg_lanes8_case_20261023T193854+0800/{ACCORD,B0}/`，以冻结 GPT-2 Stage-4 状态和源归档 `d2fd445acbc87db4f04b5a6edc09a7134b6a9babffcd6bdf45f3495bb1f1ced8` 为只读起点。
- Stage-4 首次本地构造 DSE 时暴露通用策略问题：`build_dse_search()` 无条件覆盖显式 run-local `campaign_array_policy`，将已接受的 8x8 修订重置为默认16x32，导致候选合法性检查拒绝运行。已调整为先应用当前默认、再由显式运行策略覆盖；未改变未声明策略时的16x32默认行为。新增定向单测 `test_explicit_run_array_policy_overrides_campaign_default`，通过；`git diff --check` 通过。
- 当前配对案例将唯一候选固定为 lanes=8、array=8x8、FIFO=128、activation banks=4、cache tile=256×2、512-bit refill、cross-token reuse=8；其余 W4A8、DDR、缓存、流水和板卡约束不变。两组 task card 与设计空间文件哈希相同，profile 仅为 ACCORD 与 B0。
- ACCORD Stage-4 Agent 已选择唯一候选 `arch_7ad3a71d15fd`（lanes=8、8x8），6/6 参数检查通过，DSE 摘要为1个合法、0个已测量候选。Agent 的下一步动作是精确目标板测量；本案例按预定范围继续 Stage-5，不将该 DSE 选择标为已测 QoR。
- ACCORD Stage-5 实际 Chisel 生成、代码契约/包结构检查通过；6条编译/展开命令返回0。模板、数据内存、部署与验证专员收尾评审正在进行，尚未将 Stage-5 记为完整完成。B0 已启动相同 Stage-4/5 输入，尚无结果。
- B2 CCTG replay 仍在隔离副本运行，Stage-6 已完成 leaf 与 connected single-layer 的编译门，正在发现真实板级接口映射；截至本记录还没有本轮修复结论或最终 exact-board VCS 结果。其 profile 使用 A8PI/W8API、GPT-6.1-Sol，fallback 已从本次 DCG 运行环境中清除。
- 本轮为单案例探索证据，不计入原定81次正式评分；尚无吞吐、资源或综合结论。下次更新需记录 B0 Stage-4/5 与 CCTG B2 的真实工具结果，并核对两组生成参数/源码是否完整反映 lanes=8。

### 快速案例结果更新（2026-10-23 20:06 +0800）

- GPT-2 `lanes=16 -> 8` 配对运行 `dcg_lanes8_case_20261023T193854+0800/{ACCORD,B0}` 均完成 Stage-4/5，`code_generation_report.status=ready`；六条 Chisel compile/elaboration 命令均返回0，package static check 通过。
- 两边输入 task card 与 design space 哈希分别相同（`df014d90...331f0`、`e0156b45...fe353`）。两边输出的 `GeneratedDesignParams.scala`、`GeneratedAcceleratorTop.scala`、`GeneratedAxiDdrTop.scala`、`GeneratedSACGMetadata.scala` SHA-256 全部逐文件相同；`runtime_config.json` SHA-256 同为 `287e9c29...9c0c1`。实际绑定为 W4A8、8 lanes、8x8 阵列、512-bit refill、8-token reuse。
- 此 case 的 task card 明确写入 lanes 与阵列的完整变更，并将设计空间限制为唯一合法候选，故 ACCORD/B0 均选到同一设计是预期结果。这只能作为配对运行和源码/配置传播的可复现 pilot，不能用来声称 DCG 提高了选型质量、性能或降低了成本。DSE 为1个合法候选、0个测量候选；没有新 QoR、资源或吞吐结果，也不计入正式81-run评分。
- Gemma B2 隔离副本的 `case_leaf_functional` 与 `case_single_layer_functional` 仍有既有 VCS compile/elaboration 通过证据。板级 selector 映射分块0–28均已返回，selector 聚合通过；exact-board source-map 3/3通过、23个样例源的review coverage为pass；整合级domain review当前第4次尝试仍在运行，前三次遇到HTTP 502及SSL EOF后由框架自动重试。本轮 exact-board VCS 与 B2 的 repair 结果仍未产生。原 Gemma run 未改动。
- 下一步优先收齐 B2 的 selector/board closure 与 repair 证据；之后将用同一故障源码与历史 ACCORD iteration 41 结果核对可比性。若当前 DCG pilot 没有可观察的组间差异，保留为贯通记录，并补一个只改变上游决策、让下游依赖由 Agent 自行推导的轻量 revision case；不把单候选相同输出写成机制效果。

### 快速案例进展更新（2026-10-23 20:45 +0800）

- 已从 B2 隔离副本最新 `verification/sacg_state.json` 恢复 Stage-6 repair loop，profile 保持 `SPATIALACC_ACCORD_PROFILE=B2`，target scope 为 `board_axi_ddr_closure`，远端工具开启，repair loop 无人为迭代上限。此前 stale identity/manifest 已由 Agent 正常重物化：当前 `board_simulation_preflight_materialization.json` 为 `pass`，manifest 绑定 identity SHA `9c23ccc5...`、ABI/timing/AXI 当前契约以及新 VCS compile plan；selector coverage 29 个 worker 的当前 SHA 均匹配。
- 新一轮 exact-board VCS 真实 compile-only 已运行，确认当前 DUT 是冻结的 faulty snapshot：`compute_slot.sv` 第115行使用未声明 `write_busy`，第142行使用未声明 `rstate`、`read_kind`，均为 `Error-[IND]`。板级 identity、compute-slot ABI、timing、AXI preflight 全部通过；VCS 失败发生于 DUT 源码编译，不是 manifest/工具入口阻塞。当前 VCS 输入包可在 `run/verification/board_simulation/vcs_stage.tar.gz` 和 `run/verification/board_simulation/reports/vcs_compile.log` 复核。
- 修复前 `compute_slot.sv` SHA 仍为 `2498988b15a09e7ea3a5342b9c088b754b8122f766969596f4cfa60af99a2648`，与原 Gemma iteration 41 失败源码相同。lower-layer leaf/single-layer 两张证书作为当前 repair 上下文重用；本轮仿真未运行，符合 compile-only 实验口径。
- B2 Repair Agent 已基于当前 VCS 报告启动，prompt 为 `repair/llm/repair_agent_prompt.md`，记录的模型为 `gpt-6.1-sol`。W8API 端连续返回 HTTP 503 `model_not_found / No available channel for model gpt-6.1-sol under distributor`；截至本记录累计4次请求失败，框架正按指数退避继续同一请求，下一次延时64秒。没有切换上游/模型，也没有人工编辑 RTL；尚无 B2 修复结论或修复后编译结果。
- 此 B2 run 已取得“相同故障快照、相同 exact-board compile-only 门、真实 VCS 复现”的配对前提，但实验结果尚未闭环，不能先报告 B2 的根因准确率、修复成功率或迭代数。继续等当前请求成功，随后只按 Agent 提交的 bounded repair 与真实 VCS 复编结果记分。
- GPT-2 DCG `lanes=16 -> 8` ACCORD/B0 仍仅是 Stage-4/5 编译贯通 pilot：单候选、0个DSE测量，两组输出源码一致，不能声称机制收益。若 CCTG 对照闭环后仍有时间，追加一个只指定上游变化、让Agent自主推导依赖更新的轻量真实案例；不等待完整81-run基准设施。

### 快速案例结果更新（2026-10-23 21:27 +0800）

- CCTG B2 已闭环，详见上面的 21:01 检查点。与历史 Gemma iteration 41 ACCORD 轨迹并列看，两者都针对相同 `compute_slot.sv` 声明顺序故障、各由 Agent 生成一次局部文件修复、exact-board VCS compile/elaboration/link 均返回0且仿真均跳过。历史 ACCORD generation Agent 用时47.7秒，B2 generation Agent用时39.2秒；B2 repair Agent选择后又调用 exact-board generation Agent。该轻量比较未显示通过率差异，且 B2 prompt 的 `cctg_policy` 等通用 CCTG 文本仍有残留，因此不可据此宣称 CCTG 因果收益或迭代效率优势。
- 新 DCG 依赖推导配对目录为 `accagent/experiments/accord/results/dcg_lanes8_inferred_20261023T2115+0800/{ACCORD,B0}`。两组以同一个冻结 GPT-2 基线为起点（基线为 lanes=16、array=16x32），任务只要求 lanes 16→8、明确不指定阵列行列；共同候选域提供 lanes=8 下四种合法阵列，FIFO=128、activation banks=4、cache tile=256×2、512-bit refill、reuse=8等固定项保持相同。B0 的参数 Agent prompt 已移除 source SACG state、SACG memory 与 hierarchical learning context，任务卡/约束/候选域相同。
- W8API/GPT-6.1-Sol 下，两组 Stage-4 Agent 均从4个合法候选中选择 `arch_7ad3a71d15fd`，绑定 lanes=8、array=8x8；其余参数相同。每侧 DSE 为4个合法、0个实测候选；不产生新的QoR、资源、时钟或性能数据。
- 两组 Stage-5 均完成6条 SBT compile/elaboration 命令，全部返回0；codegen contract 与 package static checks 均为 `pass`。35个 manifest生成文件中33个逐文件哈希相同，核心 `GeneratedDesignParams.scala`、`GeneratedAcceleratorTop.sv`、`GeneratedAxiDdrTop.sv` 哈希分别为 `aa90fdf0...`、`cff8af7d...`、`a14d1b6a...` 且两组一致。剩余两项是含 run-local 路径/对应自校验哈希的辅助 JSON，差异仅在各自 ACCORD/B0 路径。
- DCG 结果是“此任务上两种配置都能推导同一合法依赖并编译”，不是机制收益证据；可作为中性 pilot，说明普通交接在这个小而显式的合法域里已足够。B0 Stage-5 上游第一次遇 TLS EOF，框架在同一路由自动重试并成功；实际模型仍为 W8API/GPT-6.1-Sol，无fallback、无 Toska。运行日志各自保存在实验目录的 `stage4_parameter_binding.log`、`stage5_codegen.log`。
- 本轮快速 pilot 不计入原定81次 formal score runs；`baseline_manifest.json` 中 `formal_score_runs_completed` 仍为0。没有跑 full DSE、VCS、simulation、Vivado synthesis/P&R，也没有产生新增性能数据。原来19:52、20:06、20:45各检查点保留为历史记录，以本节为当前状态。

### 2026-10-24 12:44 +0800 DCG activation-bank revision pilot

- 新配对案例 `dcg_activation_banks_revision_20261024T122503+0800` 从已接受的 GPT-2 W4A8 Stage-4 checkpoint 启动，只修订 activation banks `4 -> 2`；lanes=8、array=8x8、cache tile=512x2、512-bit refill、reuse=8 和 DDR/流水/板级约束固定。任务卡与设计空间同一份共享输入，profile 为 ACCORD/B0。
- W8API `gpt-6.1-sol` 下两侧 Stage-4 均选择 `arch_e10408d1ed8e`，6/6 静态检查通过，1个合法候选、0个实测候选；Stage-5 两侧均 `ready`，六条 Chisel compile/elaboration 命令均通过，codegen contract/package static check 均通过。
- Stage-4 DSE Agent 分别耗时61.8秒（ACCORD）和104.5秒（B0）；Stage-5 compile/elaboration gate 分别耗时128.84秒和104.22秒。各 Agent 调用的独立耗时保存在 manifest，团队调用并行时不将各耗时简单相加当作 wall-clock。
- 两组121个源级 Scala/RTL 文件哈希完全一致。与 activation banks=4 基线相比，121个源文件中15个变化，包括 `GeneratedDesignParams.scala` 和7个物理激活存储模块及其 Vivado 副本；Generated Accelerator/AXI-DDR 顶层 wrapper 哈希不变。说明该参数进入实际 Chisel/XPM 生成路径，而非只改 metadata。
- 本案例仍是中性机制 pilot：ACCORD 与 B0 选型、生成和编译结果相同，没有观察到 DCG 的结果差异。实际 B0 prompt 移除了完整 `source_sacg_state`/SACG memory 块，但保留空的 current-memory-truth 摘要（活跃 barrier/retry/backtrack 均为0），此点已写入 manifest，不能把本例描述为完全 state-free baseline。
- 未运行 VCS/功能仿真或 Vivado；DSE 测量为0，故没有资源、Fmax、cycles、吞吐或 QoR 数据。本 pilot 不计入81-run formal score；详细输入、prompt 与输出哈希见 `accagent/experiments/accord/results/dcg_activation_banks_revision_20261024T122503+0800/experiment_manifest.json`。

### 2026-10-25 23:46 +0800 DCG reuse revision ACCORD 综合结果

- 同一固定参数案例 `dcg_cross_token_reuse_revision_20261024T164300+0800_v2` 的 ACCORD 已通过 exact-board VCS compile/elaboration/link（compile-only，未仿真），并完成真实远端 GeneratedAxiDdrTop 生成核综合。参数仍固定为 W4A8、8×8、8 lanes、512-bit refill、active/shadow URAM cache、cross-token reuse=4；没有启动 DSE 回退。
- ACCORD OOC 综合 Fmax 为 **84.983 MHz**，LUT/FF/DSP 为 **246,508 / 43,180 / 1,666**，BRAM36/BRAM18/URAM 为 **123 / 21 / 97**。范围是 generated-kernel synthesis，不是 post-route 或板上频率；关键路径为 FFN-up `writeToken` 到 `outputMem` BRAM 写数据端，57 logic levels、11.438 ns data delay、-7.767 ns slack。源码归档 SHA-256：`91c0101b730558e0a04e63545ad384dc08af3ed4125db129b427332c43a542b6`。
- 现有 8,702,008 cycles、16 tokens/12 layers 推得 156.255 token/s，但最新 Norm 时序 patch 明确增加每个 emitted beat 8 cycles、unstalled emission interval 从3变为11；因此 156.255 是未校准暂估，不作为最终吞吐。正在用仓库内 source-cycle calibration 入口对这份已编译源码估周期，结果落在 ACCORD `backend_board/qor/cycle_reference/`。
- QoR router 第4次 W8API 请求返回成功（此前3次 `429 DAILY_LIMIT_EXCEEDED`），建议因低于继承的 100 MHz/200 token/s 目标而回退 DSE。该建议与本实验固定参数范围冲突，未执行回退。此次 ACCORD 的综合源码含额外 timing repair，而 B0 仍是未经同等时序优化的基线；两者 QoR 不作 DCG 因果对比。`observed_results.json` 和 manifest 已记录结果与周期口径。

### 2026-10-26 00:43 +0800 Agent patch 已应用但 Chisel elaboration 失败

- W8API repair compact retry 在累计六次502后返回 `ready_to_apply`。Agent 将修复限定为本run的 `Attention.scala` 和 `Linear.scala`：允许后续 attention context token 继续填充 `reuse=4` projection chunk，并为整数 Linear 输出scale/乘法/舍入/饱和增加11-cycle lane-parallel pipeline。此为 Agent 的实现意图，暂不代表数值语义或性能已通过验证。
- 执行器两个源文件 patch 均原子应用通过，未改共享模板或 Stage-4 参数。实际 `Compile/compile` 与 `GeneratedContractCheck` 通过；`ElaborateGeneratedAxiDdrTop` 失败于 `ChiselException: Width of Linear.saturated: OpResult[SInt] is unknown`（`AccMath.resizeSignedToUInt(Common.scala:23)`，`Linear.scala:532`）。完整诊断见 `ACCORD/run/backend_board/timing_optimization/3949aab851ef7ab3baab/incremental_compile.log`；application=`compile_failed`。
- ACCORD 仍只有前一源码archive的84.983 MHz及资源综合报告；未发生当前修复源码的VCS刷新或Vivado综合，不能报修复后的时序、周期或吞吐。下一步保持同run，将真实 elaboration compiler error交给同阶段时序修复 Agent，再增量编译/展开，成功后刷新Stage-6 compile-only、综合及source-cycle结果。

### 2026-10-25 23:54 +0800 ACCORD 当前源码周期分析阻塞

- 对 SHA-256=`91c0101b730558e0a04e63545ad384dc08af3ed4125db129b427332c43a542b6` 的综合源码运行仓库自带 source-cycle agent 后，结果为 `noncompleting_hardware_schedule`，而非有限 cycles。报告指出 `IntegerAttention` 每个 context token 只向 `outputProjection` 喂入一组 beat 后就等待投影输出；该 `Linear` 的 chunk size 为4，需等四个 token 输入才启动计算，形成闭合等待。此为源码调度分析，不是 VCS 仿真结论。
- Stage-7 Fmax/资源仍是有效的生成核综合结果；156.255 token/s 只保留为原结构周期假设下的暂估值，当前不报告为有效吞吐。框架已有 `compiled_cycle_followup` 已被启用，`codegen_source_repair_agent` 正在同一 ACCORD run 上修复并保留参数/共享模板；补丁后需增量编译、Stage-6 compile-only 刷新、重新综合和再算有限周期。


### 2026-10-26 00:51 +0800 当前源码 Stage-6 通过，Stage-7 周期分析等待W8API

- ACCORD同一run的修复源码已完成exact-board VCS compile/elaboration/link，`compile_only_pass`、退出码0；仿真跳过。VCS归档中的 `Linear.sv` 与run-local当前源码SHA一致，顶层 `GeneratedAxiDdrTop.sv` 也匹配。
- 已从最新verification SACG state重新启动Stage-7。随后检查发现进程实际继承Toska base URL `https://api.toskaxy.xyz/v1`，并非要求的W8API；此前503是Toska路由结果。已定向停止该错误路由的Stage-7进程，live transaction在停止时为10次调用/9次重试。尚未产生新cycle结果或Vivado综合，因此没有当前源码的有效Fmax、资源或TPS。
- 既有ACCORD 84.983428 MHz/资源只对应旧source archive `91c0101b...`；旧156.255 token/s与8,702,008 cycles不作为当前结果。B0已测量的17.057278 MHz和31.362469 token/s是未作同等时序修复的早期基线，不能据此声称DCG带来性能优势。
- 按原run继续：先恢复并显式配置W8API endpoint/key，再启动source-cycle Agent完成有限周期分析；之后由框架在同一参数下完成需要的修复、Stage-6刷新、当前源码综合和周期重算。禁止沿用Toska全局变量、新建run或DSE backtrack。Stage-6证据、日志与完整输入均保存在实验目录中。


### 2026-10-26 01:01 +0800 W8API周期分析恢复并进入Agent修复

- 已复用本机权限0600的W8API环境文件，显式设置base URL、模型及凭据，关闭fallback；启动前配置解析断言和运行中子进程检查均确认W8API。此前误继承Toska的Stage-7已定向停止并保留独立日志，不计入实验数据。
- W8API source-cycle Agent完成当前源码分析，结果仍为 `noncompleting_hardware_schedule`（16 tokens、12层），因此暂无有效cycles/TPS。Agent按Stage-7既有流程立即启动run-local `codegen_source_repair_agent`（transaction `2055646f687b4789c704`），请求进行中。
- 当前仍无修复后编译、Stage-6刷新或综合数据。保持参数固定、等待Agent提交修复并按同run验证；不使用旧源码的84.983428 MHz或156.255 token/s作为当前性能。


### 2026-10-26 01:07 +0800 时序修复通过当前源码编译与Stage-6

- W8API Agent修改ACCORD run-local `Attention.scala` 与 `Linear.scala`：重新连接sequence完成后的Linear重启，并在输出requantization路径增加一个寄存器边界。Agent报告新增输出延迟1周期且沿用write-drain guard；其余reuse、并行计算、ready/valid、位宽和接口保持。Stage-4候选参数未变，共享模板未修改。
- 增量Scala compile、contract check和两个顶层Chisel elaboration全部通过，source archive=`2055646f687b4789c70412a2a5b14acfb5227ce27891341f293b74e5afa21283`。新源码Stage-6 exact-board VCS compile-only也通过、仿真跳过；输入包中的Attention/Linear源码hash与当前生成源码一致。
- 当前源码已回到同run Stage-7 source-cycle分析，W8API route已校验。此patch尚无新综合或有限周期结果，不能计算TPS；继续等待Agent分析后再综合和校准。无DSE回退。

### 2026-10-26 03:08 +0800 E3 历史候选核查

- 检查 `accagent/runs/formal_20260922_r434_gpt2/debug_loop/flow_actions/028_localize_current_board_interface_causal_slice.json`：它是 flow-controller 的 `retry` 动作记录（event 28、attempt 16），不是已执行的诊断。记录要求生成 `verification/debug_closure/board_interface_causal_slice.json` 和 `repair/current_stage_causal_context.json`，两个文件均不存在。
- 同一 run 的 `verification/debug_closure/failure_localization.json` 为 `needs_boundary_trace`，`failure_record_count=0`、`failed_boundaries=[]`、`root_candidate_module=null`。记录中的失败是 `promotion_certificate_live_evidence_binding_check` 检测到 `board_simulation_manifest.json` 的证据哈希漂移；这不是已定位的硬件/EDA 根因。因此该候选不构成 CCTG diagnosis，也没有可绑定到该切片的 repair episode。
- 对仓库 JSON 产物检索非空 64 位 `causal_slice_sha256` 与 `sacg_cctg_causal_slice_sha256`，未找到匹配项。Gemma iteration 40→41 的真实 exact-board VCS fail-to-pass 仍可作为直接工具反馈修复 pilot，但记录的 `causal_slice_sha256=null`，不能算 graph-guided diagnosis。
- 代码路径复核：`scripts/verification/case_vcs_evidence_analyzer.py` 的 manifest/compile-only 分支只记录编译诊断，不生成 `sacg_cctg_causal_slice`；`build_sacg_cctg_causal_slice()` 需要已尝试运行的 simulator 证据、executed manifest 和运行进度事件。当前仓库没有 `progress_event_log.jsonl`，所以现有 compile-only 产物不能补成真实 CCTG runtime frontier。
- 更正：cross-token reuse `8 -> 4` 的参数绑定事件是 `parameter_binding/sacg_state.json` 中 `transition.0003`（4项约束、11条边、9个节点、9项产物）。`transition.0006` 是被拒绝的 verification-artifact planning event，不是参数传播事件。ACCORD/B0 的参数绑定一致，但 ACCORD 后续 timing repair 改动了 run-local 模板，因此后端性能不能作为 DCG 比较收益。E1–E4 evidence-binding 回归已有4/4 pass；正式 Experiment 2/3 的 `formal_score_runs_completed=0` 不变。
- E3 下一项有效证据必须来自同一真实 run 的完整链：exact-board VCS runtime failure 与 progress event → 非空、hash-bound CCTG slice → Agent 消费该 slice 的 repair proposal → source patch → exact-board VCS recheck。当前没有正在运行的 E2/E3 进程；compile-only 修复和 150 MHz 时序结果均不能替代这条链。

## 最新执行检查点（2026-10-26T12:48:28+08:00）

- E2 结论不变：三组 GPT-2 revision 仅为 ACCORD/B0 pilot，正式因果分数仍为0。
- E3 已复核隔离 B2 run `accagent/experiments/accord/results/cctg_b2_prompt_clean_20261024T1105+0800/run/`。真实 Gemma 3 1B checkpoint/catalog 与 reference 路径均存在，catalog 覆盖26层、338项 tensor，reference 为26层、sequence length 16；这些是输入/reference证据，不代表 DUT 消费或硬件运行。
- 在 `SPATIALACC_VERIFICATION_POLICY=full_semantic_simulation` 下调用当前 exact-board manifest validator，返回9个 preflight blocker：旧 testbench 仍为 `sacg_board_compile_tb`/`compute_slot_axi`，manifest无 hash-bound runtime artifacts、无输入/权重 fixture、DUT权重绑定 `dut_consumes_bound_weights=false`，且缺 simulation/progress/hierarchy/pipeline/runtime-loader 输出。没有启动 VCS，也没有把 compile-only 结果升级为 runtime 结果。
- 当前工作区包含 full-runtime prompt、manifest validation/runner分支及 Stage-6 policy-sensitive checkpoint 变更；既有定向检查记录见上一轮。当前没有本实验本地 Agent/VCS 进程。远端 Vivado 作业属于其他工程，未触碰。
- 下一步从此同一 B2 run 的 `debug_loop` 续跑，进程内显式固定 W8API、`full_semantic_simulation` 与 B2 profile，要求 Agent 生成/修复完整 runtime manifest、真实 DDR fixture 和 exact-board testbench，然后按框架执行远端 VCS。完成前 E3 继续记0；该 B2 control run 不能单独证明 CCTG treatment 效果。
## 最新执行复核（2026-10-26T17:30:48+08:00）

- 正式实验状态没有改变：E2/E3 formal score 仍为0。E2现有三组 GPT-2 revision 只证明参数物化与阶段流程 pilot，ACCORD/B0 没有可归因的差异；E3 仍缺 exact-board DDR runtime、有效 progress/DDR 事件和非空 hash-bound CCTG 诊断/修复闭环。
- 在同一 Gemma E3 run `accagent/experiments/accord/results/e3_gemma_exact_runtime_20261026/run/` 修复并验证了两处通用框架问题。`regenerate_target_model_reference()` 现在即使 DUT 权重绑定 materialization 为 `incomplete`，也会继续重跑 `case_semantic_testbench`，将 materialization 后的新诊断写入 repair package；此前该分支跳过复检，导致 Agent 重复读取 15:51 的旧 provenance mismatch。17:24 的 fresh report 已移除四项旧 hash mismatch，当前真实 blocker 是 DUT binding incomplete、缺少13项权重 tensor hash 和11个 operator-stage harness、未证明 DUT 消费权重且 identity fallback 未关闭。
- operator-leaf prompt compaction 曾把 `stage_repair_execute.py` 误识别为 pipeline stage `stage_repair_execute`，随后把全部大 Q31 scale 数组过滤掉。`_operator_leaf_stage_ids()` 现在只识别带数字序号的真实 stage ID。对本次 Gemma requirements 实测，compaction 保留5组、共17,664个通道 scale 值；完整 payload仍以其原始 hash-bound requirements 为准。
- 回归验证：`test_operator_leaf_prompt_compaction`、`test_reference_regeneration_refresh` 和已有 reference-regeneration 单测通过；`tests.test_stage_agent` 为34/34，`tests.test_repair_execution_feedback` 为30/30；`py_compile` 与 `git diff --check` 通过。`tests.test_repair_patch_execution` 的46项中有2项既有 board-manifest fixture 用例仍失败，因为当前检查要求 board source identity 和 functional-verification tool profile；本次 reference-refresh 用例通过。
- 迭代64的旧 Agent 响应及日志已保存在原 run。当前 Stage-6 已从同一 `verification/sacg_state.json` 重启，log 为 `run/debug_loop/e3_gemma_stage6_scale_compaction_fix_20261026.log`，进程配置固定为 W8API `gpt-6.1-sol`。目前只看到新 repair-agent 请求，尚无新 patch、VCS 或 runtime 结果；E3 仍记为未完成。不得将本次 framework 修复或 reference report 更新写成硬件验证通过。

## 最新执行复核（2026-10-26T12:03:23+08:00）

### 2026-10-26T19:39:42+0800 E3 Gemma compile-only Stage-6 门槛调整

- 用户批准当前 Gemma Stage-6 使用明确的 `vcs_compile_only` policy。此 gate 不运行 RTL 数值仿真，也不要求完整数值正确；通过条件仍是本实验 run 的 exact-board AXI/DDR 当前源码由真实 VCS 编译、展开、链接成功。
- 当前 run 为 `accagent/experiments/accord/results/e3_gemma_exact_runtime_20261026/run/`。operator-leaf（11个pipeline stage）、single-layer compile-only 证书和 `case_multilayer_pipeline` 已通过；AXI/DDR 层仍因 board harness/tool-profile 绑定引用主 Gemma run 而失败，exact-board VCS case 尚未执行。因此本轮目前没有新的 Stage-6 pass 数据。
- W8API `gpt-6.1-sol` 当前反复返回 HTTP 503 `No available channel`；Agent 请求保持框架退避重试。不可切换到 Toska、复用主 run 的证书或将旧报告写成当前实验结果。
- 写作允许将当前 run 后续取得的真实 VCS compile-only 结果作为“编译/展开/链接门槛”的证据；它不代表 runtime/功能或数值正确。E3关于 CCTG 的结果范围需按本 run 实际留下的 Agent diagnosis/action、patch 和 current-source recheck 记录描述；未形成这些记录前，不计为完成的 repair episode或正式因果分数。

### 2026-10-26T21:01:07+08:00 E3 Gemma compile-only gate 复核

- 同一 `e3_gemma_exact_runtime_20261026/run/` 的 `verification_result.json`、`debug_loop_report.json` 与 `board_axi_ddr_promotion_certificate.json` 均为 `pass`；scope=`board_axi_ddr_closure`，policy=`vcs_compile_only`。`case_multilayer_pipeline`、`case_axi_ddr_interface` 和 exact-board VCS compile-only gate 通过；operator-leaf 与 single-layer compile-only 证书重用。
- 真实远端 VCS compile/elaboration/link 返回码为0，完成34个模块；CPU时间为72.041/1.610/0.431秒。编译计划含51个 source IDs。输入 fingerprint=`cef34ae9169b3c402c6cc37fcf2f244ed41fa2dd4533237d3907d736934cd686`，VCS log SHA-256=`1aaf7583c1846f5c49172401ff3933c33b381528acb9691383e188f0084952bb`，board source identity SHA-256=`c8593caa82f9814f18be0f7dc5a4fca139920d9fa32566fe95ebb2d63f7f6a65`。
- 此证据仅支持 exact-board compile/elaboration/link closure。`simulation_skipped=true`、`exact_board_acceptance_passed=false`、`compiled_sample_source_ids=0`、`artifacts={}`；没有真实 runtime、DDR 计数、数值比较或 CCTG causal slice。本次门禁复核不算新的 repair episode，E3 仍为单案例 compile-time repair pilot；正式 E2/E3 score 不变。
- 本次复核没有本地实验 Agent/VCS 进程。此前 W8API 503/SSL EOF 属于 repair-agent 请求，不能算新实验失败结果；当前 Stage-6 compile-only gate 已结束并通过，不重复运行同一编译。

## 2026-10-27T00:43:25+08:00 全部实验状态复核

- GPT-2 Medium / GPT-6.1-Sol：Stage-6 exact-board AXI/DDR VCS compile/elaboration/link 已通过，远端返回码0，simulation按 `vcs_compile_only` 跳过。Stage-7 adapter generation发现 direct adapter/top实例关系不匹配；run-local repair已应用并刷新Stage-6编译证据。VU9P `xcvu9p_CIV-flgb2104-2-i`、150 MHz target 的Vivado synthesis正在运行，尚无Fmax/资源/TPS。
- GPT-2 Medium / DeepSeek-V4-Pro：Stage-6单层compile-only通过，exact-board selector map进度26/29，沿原 discovery worker继续。
- GPT-2 Medium / Claude Opus 5：board identity与29/29 source mapping已完成，Stage-6 multi-layer harness尚缺；generation agent在644,186和645,590字节prompt上两次收到HTTP 400 `invalid_request`。响应体没有给出具体无效字段，不能断言是上下文长度/schema/路由问题。当前继续同run Stage-6 repair，不重跑Stage-0至5。
- Gemma E3 run的exact-board Stage-6 compile-only证据为pass、VCS返回码0，完整范围是compile/elaboration/link；simulation skipped，board runtime readiness未运行，没有CCTG causal slice，故正式E3机制得分仍为0。此前 fail-to-pass compile repair仍只是compile repair pilot。
- Evidence Binding deterministic mutation检查4/4通过，stale-evidence acceptance=0、false invalidation=0；无Agent、VCS、Vivado执行。GPT-2 Medium ACCORD/B0配对的activation banks、lanes explicit/inferred、cross-token reuse目前仍是Stage-4/5 pilot，结果两侧一致；cache-tile因Medium合法域无可替换值跳过。
- Stream-HLS只新增一个packed-W4/I32 `h.0.mlp.c_fc`单算子native MLIR adaptation的pipeline/translation/远端syntax compile通过证据；没有完整模型、DDR/AXI、HLS/Vivado synthesis或QoR。Allo无匹配pinned LLVM/MLIR工具链。
- `monitor_status.json` 与论文汇总已同步。仍无Medium最终性能结果；下一步监控GPT-6.1当前综合，DeepSeek完成剩余map后进入board VCS/综合，Claude沿当前run修复缺失harness并处理请求错误。E2/E3正式因果分数保持0，禁止把compile-only、单算子syntax或estimate写成实测性能/机制收益。
