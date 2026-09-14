# 结构化状态与消息记录

早先的 “Spatial Design Message Protocol” 不应作为论文最高层贡献，而应作为 SACG state transition 的支撑基础设施。

## 目的

结构化记录的作用是让 agentic design flow 可回放、可审计。Agent 的决策必须落到 SACG、artifact、evidence、repair log 中，而不是只存在于聊天历史里。

## 状态

每个设计状态定义为：

```text
S_t = (G_t, A_t, R_t)
```

其中：

- `G_t`：当前 SACG；
- `A_t`：artifact set；
- `R_t`：evidence、reports、logs、benchmark records。

每条 transition record 必须标明：

- agent role；
- input state hash 或 ID；
- 更新了哪些 SACG nodes / edges / contracts；
- 生成或修改了哪些 artifacts；
- 调用了哪些 checker / regression；
- pass/fail 结果；
- next state ID。

## 核心记录类型

### DesignObjective

定义一次 run 的范围和 acceptance criteria。

字段：

- `model_family`
- `block_style`
- `sequence_length`
- `batch_size`
- `precision`
- `target_fpga`
- `target_clock`
- `resource_budget`
- `correctness_oracle`
- `performance_target`
- `deployment_target`
- `comparison_scope`

### SACGRecord

存储当前 graph。

字段：

- `nodes`
- `edges`
- `contracts`
- `invariants`
- `artifacts`
- `checker_status`
- `version`

### ArchitectureTransition

记录 PU / stage / pipeline 修改。

字段：

- `changed_nodes`
- `changed_edges`
- `stage_schedule`
- `parallelism`
- `stream_contract_updates`
- `memory_contract_updates`
- `resource_estimate`
- `checker_results`

### ChiselArtifactRecord

把 generated / modified Chisel 绑定到 SACG。

字段：

- `template`
- `parameters`
- `generated_chisel_files`
- `modified_chisel_files`
- `bound_contract_ids`
- `backend_outputs`
- `lint_or_compile_result`

### VerificationTask

定义一次验证动作。

字段：

- `target_level`：`stage`、`top`、`system` 或 `board`
- `target_contract_ids`
- `workload_window`
- `real_weight_source`
- `real_activation_source`
- `scale_bias_golden_source`
- `ddr_image_source`
- `reset_sequence`
- `config_sequence`
- `expected_outputs`
- `tolerances`
- `timeout_or_cycle_budget`
- `required_logs`

### VerificationReport

记录一次验证产生的 evidence。

字段：

- `task_id`
- `pass_fail`
- `first_mismatch`
- `deadlock`
- `missing_beat`
- `extra_beat`
- `wrong_address`
- `violated_contract_candidate`
- `trace_summary`
- `probe_summary`
- `pass_matrix_update`
- `artifact_paths`

### RepairRecord

记录 invariant-directed repair。

字段：

- `failure_class`
- `symptom`
- `evidence`
- `violated_contract`
- `affected_node_or_edge`
- `affected_artifacts`
- `minimal_patch_description`
- `expected_behavior_change`
- `regression_tests`
- `regression_result`
- `keep_or_revert_decision`

### DeploymentBenchmarkReport

记录 closure 和 benchmark 结果。

字段：

- `synthesis_result`
- `place_route_result`
- `timing_result`
- `resource_result`
- `power_or_energy_result`
- `board_runtime_status`
- `latency`
- `throughput`
- `ddr_bandwidth_efficiency`
- `pipeline_utilization`
- `design_time`
- `automation_rate`
- `repair_iterations`
- `baseline_metadata`

## 科学作用

这些记录支持：

- replayable transitions；
- human-intervention accounting；
- ablation；
- fault-injection evaluation；
- artifact packaging。

但它们不能替代 SACG checker。一个 record 只有在能链接到 executable checker、trace、regression 或 artifact 时，才有科学价值。
