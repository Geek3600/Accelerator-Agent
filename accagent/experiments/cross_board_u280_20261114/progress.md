# GPT-2 Medium seq32 跨板卡实验：Alveo U280

更新时间：2026-11-14T13:28:26.669881+08:00

## 实验控制条件

- 独立变量：目标板卡由 MIMIC Computer v6.0 / VU9P 改为 Alveo U280。
- 器件由 `xcvu9p_CIV-flgb2104-2-i` 改为 `xcu280-fsvh2892-2L-e`。后者已核对 LoopQuant 原始 U280 Vivado 脚本。
- 目标模型仍为 `openai-community/gpt2-medium`，revision `6dcaa7a952f72f9298047fd5137cd6e4f05f41da`，24 层，hidden 1024，16 头，FFN 4096。
- batch=1、seq=32、W4A8、I32 累加/偏置、Transformer block 范围不变。
- 上游模型 `gpt-6.1-sol`，route `https://www.a8pi.com/v1/responses`，与现有 GPT seq32 基线报告一致；禁用其他模型/提供商 fallback。凭据仅由现有进程环境继承，没有写入实验文件。
- 验证仍为 `vcs_compile_only`；Vivado 2021.1 / VCS 2022.06 不变；run-local 时序优化目标为 Fmax≥150 MHz。
- 保留 512-bit 核侧逻辑 refill；物理 U280 HBM 的 256-bit 接口适配属于板卡变化的派生设计，由 Agent 生成。
- 保留 active/shadow 权重缓存、下一层预取与计算重叠、activation ping-pong、算子/token 流水及 ready/valid 回压。
- 不将 VU9P 的 DSE 结果、RTL、检查报告、时序结果或性能估算作为新 U280 的结果；板卡变化允许 DSE 派生设计选择变化。

## 已完成的准备与启动

1. 独立实验目录：`/home/remote/workspace/Qwen2-Accelerator/accagent/experiments/cross_board_u280_20261114`。
2. 独立 run：`/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_medium_seq32_u280_gpt61_20261114`。
3. 复用已有完整 GPT-2 Medium 缓存，没有下载或复制模型权重。
4. 从 LoopQuant 只读复制硬件参考，共 326 个文件，2,312,178 字节；未修改 LoopQuant 工程。
5. 同步到远端 `hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/board_references/cross_board_u280_20261114`，326 项逐一 SHA256 核对通过。
6. 板卡输入含原始 U280 shell、HBM IP 生成 Tcl 及接口说明。完整冻结硬件工程供后续 Agent 从源文件提取依赖。
7. 对照条件检查通过：24 层、1024 hidden、16 头、seq32 与旧 GPT 基线一致；当前 board materials 只解析出一个正确的新远端样例根目录。
8. 2026-11-14T13:27:19.837710+08:00 启动原生 `accagent.framework.agent`，PID 3311722。默认断点续跑，不重置已有阶段。
9. 当前日志已进入 `input_preparation`，`field_evidence_board_agent` 正式 LLM 请求进行中。此时尚未返回首个板卡解析结果。

## 运行及内存状态

- 仅新增一个轻量 TopAgent 控制进程及其当前 Stage worker。
- Stage-6 独占本地工作槽；RSS / 虚拟地址限制各 6144 MiB，SBT heap 2048 MiB。
- VCS / Vivado 使用远端 EDA 工具，未启动本地综合。启动后本地 available 约 15 GiB、swap 已用约 479 MiB。
- 已有 VU9P 实验和 LoopQuant 的其他任务未重启、未终止、未改动。

## 当前证据边界与下一步

- 本次 U280 尚无 DSE、RTL、VCS 或 Vivado QoR 结果。
- 样例 U280 shell 的 HBM / gamma memory master 端口为读端口；它不是完整的物理 PCIe/HBM 控制器顶层，也未证明包含目标 GPT 的输出写回路径。该事实已作为输入明确交给 Agent，不包装为已完成板级集成。
- 后续检查 Stage-0 是否正确提取 U280 part、HBM 与 gamma 的不同 AXI 宽度、时钟域和 Vivado 实际资源预算，且未继承 VU9P/XDMA 地址与信号。
- 继续原流程生成/编译 U280 设计，再进行源绑定的时序优化。达到 150 MHz 且资源合法/compile-only 门槛通过后停止并保存最好吞吐率候选及完整历史。
- Fmax/资源按真实综合报告登记；周期/吞吐/延迟按来源标注为估算或实测，当前没有 U280 性能数值。

## 2026-11-14T14:04:26+08:00 — Stage-0 通过并进入约束提取

- 仍是原生 TopAgent PID3311722、原 U280 run；截至该检查点只有一个 U280 Stage worker，RAM available 约18.8 GiB，swap使用361 MiB。没有启动新 controller，没有碰旧实验线。
- 13:46:53 对同 run 的 Stage-0 worker PID3329185作有记录的同阶段重载，保留 TopAgent 与此前抽取缓存。旧 worker 的板卡输出将 `canonical_axi_data_width_bits` 当成 downstream 字段别名，且把 256-bit 单 HBM channel 当成 512-bit 核侧 refill 的约束，DSE 错误地只留8 lanes；compile-only 仍被旧 `board_runtime`协议设成 required。这是 Stage-0输入/协议绑定故障，不是硬件设计失败。
- `stage_input.py`的通用提示/schema修订明确区分 `memory_system.axi_data_width_bits`（pipeline/DSE 使用的核侧 refill，经板边界适配后仍为512）与 `physical_interfaces.hbm`每通道256-bit事实，并要求两者不可混淆、不得因此缩窄核心 lanes。保留实际待实现的宽度/时钟适配，不声称已经验证。compile-only的host命令继续非必需，完整runtime策略不变。
- 13:56左右新 board-profile Agent返回 `axi_data_width_bits=512`、`axi_data_bytes=64`、`hbm_channels=32`，记录physical HBM256-bit、gamma512-bit及独立clock域；14:00左右design-space Agent返回完整物理候选域，lanes合法值恢复为 `[8,16]`。它一度遇HTTP502，既有无限重试/SSE切换最终成功，error=null且未fallback。
- 第三次 Stage-0输入团队审核与真实工具探测通过，`input/prepared_inputs.json`于14:03:31更新为`status=ready`、errors为空。VCS、Vivado、Verilator探测均通过；Vivado识别资源容量仍为器件容量而非本加速器utilization：LUT1303680/FF2607360/DSP9024/BRAM36 2016/BRAM18 4032/URAM960。
- 14:03之后已启动 Stage-1 `constraint_extraction`，`constraint_extraction/initial_design_graph.json`已生成；此时没有U280 DSE点、RTL、VCS编译或QoR数据。
- 板卡profile中的control AXI-Lite有源证据；compile-only下board_run_command/物理runtime ABI未知且不要求。32 HBM pseudo-channels各自的读接口、gamma读接口、核心512-bit refill、时钟域与物理adapter均分开记录。
- 这次通用修复代码位置：`accagent/framework/stage_input.py`；新增定向测试后共31项通过，目标文件`git diff --check`通过。仓库全局diff-check仍会报告用户现有`docs/草稿4.tex`的尾随空白，本轮未改该文件。
- 历史保护目录：`agent/monitoring/stage0_framework_reload_20261114_134653/`及`agent/monitoring/stage0_refill_binding_reload_20261114_135217/`，含旧轮输出、prompt、prepared输入、manifest、团队输出、代码差异和worker重载记录。失败尝试仅留作审计，没有伪造pass或覆写失败历史。
- 下一步继续观察Stage-1图抽取/约束校验与现有控制器晋级。任何板级宽度/clock适配仍需设计Agent在后续硬件流程完成；当前 profile 中pending状态不是实现证据。

## 2026-11-14T13:30:33.494342+08:00 — 第一个正式请求已返回

- `field_evidence_board_agent` 在 106.9 秒后成功返回，选出的板卡为 AMD/Xilinx Alveo U280，exact part 为 `xcu280-fsvh2892-2L-e`。已继续 `field_evidence_tool_agent`，不是仅配置了未调用的实验。
- 实际 `sample_project_index.json` 中，新远端样例 root 读取成功，列出 326 个文件。扫描器还将 indexed-material chunk 头中的两个本地路径误认为远端路径，两项读取失败；真实的远端引用没有失败。该信息目前为非阻塞 warning，未回退/重启 Stage 0，未修改框架。
- 没有 .xpr 的 Tcl 源码样例使 sample part probe 为空；part 已由原始 U280 Tcl 和板卡证据 LLM 正确读取，后续仍由现有 Vivado probe 验证资源预算。
- 检查全部 11 项冻结输入 SHA256 仍与启动前 manifest 一致。上游未切换，没有再次启动控制器。

## 2026-11-14T13:42:59.418467+08:00 — 远端探测完成及输入证据传递修复

- 九项 Stage-0 LLM 解析均成功（error=null、used_fallback=false），当前同一 PID3311722 的输入团队正在完成审核。
- 远端真实 VCS 最小编译探测通过；Vivado 2021.1 对 exact U280 器件的实际综合探测通过。探测所得容量：LUT 1,303,680，FF 2,607,360，DSP 9,024，BRAM36 2,016，BRAM18 4,032，URAM 960。这里记录器件容量，不是本次加速器资源使用。
- 发现真实框架缺陷：field_evidence 已含 HBM/gamma 两套接口宽度、通道和 clock/reset，但 `prompt_field_evidence_summary` 固定白名单只保留了 `board.fpga_part`，使 board_profile_agent 看不到其余已确认字段。旧 board profile 因而 memory_system 几乎为空。
- 最小通用修复：证据摘要保留所有已脱敏的字段；板卡 prompt 要求保留各具名接口与物理/逻辑区别；验证接受有真实证据的 DDR 或 HBM 通道和 AXI/存储字宽；在 compile-only 下不强制缺少的板卡运行脚本。完整 runtime 策略仍要求运行脚本。没有修改硬件、共享模板、模型、量化、流水/预取机制或工具通过证据。
- 28 项有针对性的测试通过，包括 HBM 证据保留、compile-only 无 host 脚本、runtime 仍强制 host 脚本以及通道拓扑缺失仍失败；diff whitespace 检查通过。
- 当前旧 worker 尚未载入本次修复；等待同一 Stage-0 审核边界，在原 run 继续，并保留所有可复用 LLM 结果与真实工具报告。尚未进入 DSE/生成 RTL/时序优化。

## 2026-11-14T14:42:00+08:00 — Stage-3 修复、晋级与断点恢复

- Stage-3 首轮失败的三个字段已定位为通用流程契约问题：`board_axi_contract()`没有读取 `memory_system.accelerator_facing_interface.name`，且 `check_memory_runtime_contract()`在 `vcs_compile_only` 下错误地强制要求没有源证据的 H2C/C2H 设备模板。
- `accagent/framework/stage_pipeline.py` 最小修复：接口名按 `core_side_interface_name`、`ddr_channel_prefix`、`accelerator_facing_interface.name` 顺序回退；始终检查控制协议和命令序列，只有 `full_semantic_simulation` 才要求 H2C/C2H device template。没有生成或猜测 `/dev/xdma*`，没有修改硬件架构、逻辑512-bit refill、物理HBM256-bit事实、流水、双缓冲、预取或数值策略。
- 新增三个定向测试：U280风格 `logical_core_refill` 接口回退、compile-only 缺少 H2C/C2H 时通过、full runtime 缺少 H2C/C2H 时仍失败。Python 3.13 下 Stage-3 全部13项测试和 Stage-0 31项测试通过；目标文件 `git diff --check` 通过。
- 原 TopAgent 在 Stage-3 首次失败后按既有策略记录 `retry_replan`，载入新代码的同阶段 worker 重新生成计划；当前 `pipeline_plan.json` 的 `board_axi.core_side_interface_name=logical_core_refill`，H2C/C2H 为明确 `null`，11/11 静态检查通过，SACG transition `0004` promoted，Stage-3 report 为 `ready`。
- Stage-3 通过后，TopAgent 进入 Stage-4 前暴露一个与U280无关的框架兼容故障：Python 3.10 导入 `datetime.UTC` 失败。`accagent/framework/dse_ledger.py` 已改为优先使用 Python 3.11+ 的 `UTC`，否则回退到等价的 `timezone.utc`；`tests/test_dse_ledger.py` 增加 UTC `Z` 后缀回归测试。Python 3.10 和 3.13 下 DSE ledger 各9项测试均通过，定向 Stage-3/Stage-0 回归仍通过。
- 2026-11-14T14:39:28+08:00 使用原实验 `launch.py` 断点恢复同一 run，冻结上游仍为 `gpt-6.1-sol` / `https://www.a8pi.com/v1/responses`，策略仍为 `vcs_compile_only`，没有启动第二个控制器或重跑前序阶段。Stage-0～Stage-3 均通过 checkpoint 复用，Stage-4 `parameter_binding` 已通过，当前唯一 TopAgent PID为3375965，Stage-5 `code_generation` 正在执行。
- Stage-4 当前选点已记录为 `arch_0f48af2aff62`：lanes=16、compute_array=16x32、fifo_depth=128、cache_refill_data_width_bits=512、权重/大缓存使用URAM、activation/fifo使用BRAM；6项参数检查通过。该选点是DSE/绑定结果，不是最终QoR。
- 恢复后的本地内存约17 GiB可用、swap约361 MiB；当前只有一个U280 TopAgent和一个Stage-5 worker，未启动本地Vivado。下一步继续原流程到代码生成、VCS compile-only、Vivado源绑定Fmax/资源和≥150 MHz时序优化；当前仍没有U280最终QoR或吞吐量结果。

## 2026-11-14T15:13:30+08:00 — Stage-5通过；Stage-6契约修复后正在同阶段重试

- Stage-5 `code_generation` 通过，SBT compile、GeneratedContractCheck、Accelerator/AXI-DDR top及Vivado-target elaboration六个命令均返回码0，耗时260.03秒。它仅是Chisel编译/展开，尚非远端VCS compile-only，也非仿真或QoR。
- Stage-4选点 `arch_0f48af2aff62`：16 lanes、16x32阵列、FIFO128、512-bit逻辑refill。Stage-4生成的`board_axi.core_side_interface_name`仍为null，因为Stage-4在Stage-3通用字段修复之前完成；Stage-5合同通过，但物理HBM适配未验证。
- 首轮Stage-6失败由通用框架缺陷导致：`stage_verification_plan.py`把未配置且`required=false`的`board_runtime`仍算作compile-only必需协议。修复后compile-only延后board runtime；full-semantic仍要求它，未将其伪标成配置/通过，也没有放宽最终运行时门槛。
- 回归测试`tests/test_stage_verification_plan.py`共29项通过，目标文件`py_compile`和`git diff --check`通过。新retry产出的`verification_artifact_contract`为pass，`board_runtime`仍显示configured=false、required=false；执行策略仍为`vcs_compile_only`。
- 同一TopAgent PID3375965和Stage-6 worker PID3391743仍运行。Stage-6 LLM请求第一次HTTP502后按原策略转SSE重试；没有VCS/Vivado进程。当前没有U280 VCS、Fmax、utilization或throughput结果。
- 当前内存available约18 GiB，swap占用约361 MiB。下一步等Stage-6计划复核完成，随后沿原流程跑远端真实VCS compile/elaboration/link；再跑U280 Vivado报告和run-local时序优化，150MHz前不停止。

## 2026-11-14T15:xx:xx+08:00 — Stage-6 board project input repaired from isolated v5 fact export

- The isolated v5 project `/home/hyyuan/workspace/spatialaccagent_artifacts/cross_board_u280_20261114/board_project_v5/u280_board_project.xpr` passed the real Vivado fact export on exact part `xcu280-fsvh2892-2L-e`; its export reports top `rtwsr_plan6_huginn_u280_hbm_shell` and 38 compile sources.
- The active run had an old sample-project index containing only source directories and therefore Stage-6 reported `found []` for `.xpr`. The run input now contains exactly the v5 remote `.xpr` reference; `material_index.json` counts were updated to match this bounded input repair.
- The immutable v5 fact export and provenance are retained at `verification/board_interface/u280_board_project_input_repair_v5.json`; no DUT, wrapper, architecture, pipeline, memory layout, numeric policy, or Stage-0–Stage-5 artifact was changed.
- Stage-6/debug loop is being resumed from the current repaired board-input frontier. Existing lower-layer certificates remain reusable. No U280 VCS, Fmax, resource-utilization, throughput, latency, or board-runtime result exists yet.

## 2026-11-20T14:34 CST — GitHub backup checkpoint

- The newest persisted U280 run files are timestamped 2026-11-19 17:53:39 CST. At the 2026-11-20 inspection, no process matching this run or the framework agent was present; this backup did not start, stop, or resume the experiment.
- `agent/checkpoints/latest.json` records `stage=debug_loop`, `status=fail`. `debug_loop/debug_loop_report.json` records `status=needs_repair` for `board_axi_ddr_closure`; the existing repair execution was blocked and no new flow-controller handoff was consumed.
- `repair_execution/loop/status.json` records `latest_iteration=2699`, `status=blocked`. Its summary says the same no-edit LLM wait decision recurred without new real-tool, capability-producer, patch, or instrumentation evidence. The latest repair step mapped a requested board-layer replay to the leaf-operator verifier, so no tool was started because that command cannot observe the board boundary.
- The tail of `agent_u280.log` contains repeated upstream SSL `UNEXPECTED_EOF_WHILE_READING` retries for the flow-controller request. No completed response or source patch is recorded after this retry state.
- The 2026-11-14 Stage-0 through Stage-5 progress above remains historical evidence; it does not establish a current Stage-6 pass. There is still no exact-board U280 VCS compile result, Vivado timing/utilization report, Fmax, throughput, latency, or board-runtime result. `monitoring_status.json` is an older 2026-11-14 checkpoint and must not be read as current status.
- The concise current checkpoint is retained in `agent/checkpoints/latest.json`, `debug_loop/debug_loop_report.json`, `repair_execution/loop/status.json`, and `repair_execution/loop/iteration_2699/iteration_record.json`; large generated caches and repeated repair snapshots remain in the local run directory and are not part of the GitHub commit.
