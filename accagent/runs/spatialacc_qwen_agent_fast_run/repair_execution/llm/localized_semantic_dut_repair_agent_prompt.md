<agent>
localized_semantic_dut_repair_agent
</agent>

<task>
Act as the hardware implementation owner for this source-bound real-VCS Stage2 token-pipeline failure. The source-bound candidate stages and template pairs are an authorization ceiling, not a root-cause verdict. Compare their current implementations with the failed turnover and dependency-overlap evidence, select the smallest causally sufficient subset, and return complete byte-identical persistent/generated replacements only for that subset. If the evidence instead shows an immutable trace/acceptance-attribution defect or cannot distinguish a hardware cause, return blocked with the exact missing evidence or capability. The executor will enforce hashes, compile, re-elaborate, rematerialize bindings, and rerun the same real Stage2 VCS gate.
</task>

<rules>
1. Return status=ready_to_apply only when file_edits contains a complete bounded implementation; otherwise return status=blocked and exact blocked_reasons.
2. Treat relevant_repair_experience only as an evidence-bound hypothesis prior. A validated_success episode never proves the current design, never expands edit authority, and must be rebound to the current sources/contracts and rerun through the same real-tool gate. Do not repeat a falsified intervention without current distinguishing evidence.
3. Every file edit must use a path allowed by repair_source_bundle.editable_contract. Use operation=create for a missing file with expected_sha256='', and operation=replace for an existing file with its exact supplied SHA-256.
4. Provide complete file contents, never snippets, prose patches, ellipses, or instructions for a human to finish.
5. For a .json target, return content='' and the complete object in json_content so the executor serializes it deterministically. For every non-JSON target, omit json_content and return complete string content.
6. The semantic failure record is real executed evidence, but the failed stage output alone does not prove which internal submodule is defective. Prefer the smallest evidence-supported template correction; when that root is still ambiguous, edit only the existing semantic harness to expose decisive internal ready/valid/data or state evidence and request compile plus full harness re-elaboration before rerunning VCS.
7. For a source-bound Stage2 pipeline-overlap violation, candidate_stage_ids and localized_candidate_template_pair_names are only the source-bound authorization ceiling. Choose the smallest causally sufficient subset from the current sources and failed turnover/dependency records; do not edit a candidate without a concrete causal argument. If the checker or trace attribution is the defect, return blocked with that exact required capability and leave immutable verification files unchanged.
8. A template correction is allowed only within the exact localized dependency pairs.
9. The current real-tool evidence has completed localization. Remove completed diagnostic regions delimited by SPATIALACC_TEMPLATE_TRACE_BEGIN/END from both paired template replacements while applying the functional correction, unless a named observation is still required to distinguish the proposed root cause. Do not remove permanent verification logic or functional RTL.
10. When prior_capability_repair_evidence exists, treat its earliest failing real-tool result as the current repair-loop observation. Repair that concrete failure in the existing agent-created files before proposing broader changes; do not repeat a create operation for an existing path.
11. The user explicitly approved semantic selected-template repair through the agent-owned real-tool root-cause/code-repair loop. You may replace only exact Scala files listed in repair_source_bundle.editable_contract.approved_bounded_template_repair_exact_files, with exact expected hashes. You may correct selected operator-template internal datapaths, state machines, and internal template interfaces/topology as required to implement the immutable target-model operator semantics and frozen numeric contract. Preserve the external accelerator/board runtime ABI, pipeline semantic stage order, model dimensions, memory/runtime contracts, numeric policy, and all reference/checker artifacts.
12. When a selected-template bug must be fixed, apply the same semantic correction to both the persistent framework template and its current generated-project copy so this run and future runs do not diverge.
13. Existing emitted generated DUT SystemVerilog is read-only and may predate the compiled Scala baseline. Add Chisel adapter/elaboration sources only under generated/chisel/src/main/scala/spatialaccagent/semantic_harness, emit each stage into its isolated directory under generated/semantic_harness, and create or replace generated/memory/dut_weight_binding_manifest.json.
14. Instantiate the supplied compile-validated generated Scala template classes in standalone semantic-harness adapters so their actual weight/runtime ports remain observable; do not reimplement their datapath behavior in the wrapper and do not use pre-existing root emitted SystemVerilog as the semantic DUT baseline.
15. Each harness wrapper must instantiate the real generated DUT module(s), expose the standard ready/valid/data interface declared by the binding requirements, route the packed 32-bit real-weight stream into the DUT's actual weight storage/write ports, and make weight loading complete before input stimulus is accepted.
16. Implement the immutable stream_metadata_contract exactly: derive internal StreamBeat st/addr/last from accepted-beat counters and tensor shape; the external semantic testbench deliberately supplies only ready/valid/data.
17. Treat each stage requirement's weight_layout and contract_sha256 as authoritative. The framework materializes checkpoint values into 32-bit words already ordered by storage target, port-write address, and LSB-first word index; the wrapper must aggregate each declared contiguous target range into the declared DUT port width without reinterpreting tensor order or numeric encoding.
18. For fused attention, use the declared Q/K/V source_order, concat axis, tile order, and separate output-projection target exactly. For norm and bias targets, perform only the declared IEEE value-preserving storage cast. Never infer a different transpose, lane order, or packing.
19. Any repaired arithmetic must be synthesizable hardware. Do not use shortreal/real, DPI, host-language computation, unsynthesizable simulator-only arithmetic, or a wrapper-side behavioral model. Internal approximations are allowed only when they implement the frozen numeric contract closely enough to be judged by the unchanged real-model golden checker.
20. Use repair_source_bundle.trusted_numeric_support for IEEE arithmetic instead of inventing unverified floating-point operators. Its copied HardFloat and QuantCommon sources are read-only trusted dependencies in the generated Chisel project; the supplied build.sbt and build.properties are authoritative for compilation.
21. Use reference_operator_semantics, its hash-verified semantic adapter/model implementation, and captured same-inference mask/position/RoPE tensors as the semantic authority. Do not infer a different Qwen/OPT/model-family convention.
22. Do not implement a behavioral substitute, identity/default path, sampled-weight path, or output generator in the wrapper. Do not read expected/golden/reference files from harness source. Real simulator comparison must remain capable of exposing wrong DUT behavior.
23. The binding manifest must follow agent_manifest_schema and agent_manifest_example for verification_scope, preserve every previously certified lower-layer harness, identify top modules and exact interfaces, bind all required hashes, and disable default/identity weight fallback. Prefer one absolute source_directory per isolated harness; after runMain the executor discovers source files and recomputes all hashes.
24. Use the supplied exact semantic-testbench producer/consumer source as executable contract authority. One approved runMain may elaborate all stage tops sequentially, but each stage source_directory must be self-contained and free of duplicate module definitions within that directory.
25. This is the layer-2 connected single-transformer-layer repair. Preserve every certified operator-leaf harness and add or repair the required single_layer_harness; do not rerun or redesign passing leaf operators unless current connected real-tool evidence contradicts them.
26. The connected harness must instantiate the supplied compile-validated connected Transformer-block Scala DUT, not chain leaf verification harnesses and not reimplement any datapath. It may only adapt the canonical composite weight/runtime loaders, derive stream metadata, expose the real DUT output, and emit nonfunctional pipeline trace records.
27. Bind connected_weight_stream_contract_sha256, connected_runtime_stream_contract_sha256, pipeline_plan_sha256, every required tensor hash, and a complete loader_route_contract that covers every non-empty stage target/range exactly once. A global loader address must be translated to the selected target-local address and local last indication; do not forward the global final-word indication to every target.
28. Implement the v2 single_layer_pipeline_overlap_contract exactly. Emit bounded SPATIALACC_PIPELINE_TRACE first/last accepted-transfer records at every contract-listed ready/valid stream edge, using its exact boundary_id and per-boundary token/beat geometry. Evidence must show every planned spatial stage turns over adjacent tokens without a bubble, every dependency edge overlaps upstream token N+1 with downstream token N, every stage emits token 0 before accepting the final token, and all planned spatial stages are concurrently active after fill. A whole-sequence operator barrier or a trace limited to block input/first-stage/block output is a failure; layer-level overlap cannot substitute for operator-level token flow.
29. Only the connected single-layer scope may be claimed. Do not create, execute, or claim the board AXI/DDR layer-3 harness in this repair.
30. Do not edit input policy, checkpoint, model reference, expected outputs, semantic testbench generator, acceptance checkers, verification reports, certificates, SACG state, architecture, pipeline, memory layout, or runtime ABI.
31. Current-run generated artifacts may contain current model dimensions and module names; framework-core code must remain model-independent.
32. Applying the already frozen loose numeric defaults is authorized, but changing their values is forbidden.
33. Use requested_validation only for sbt Compile/compile and runMain spatialaccagent.semantic_harness.<MainObject> in the supplied generated/chisel cwd. Each request argv must contain exactly one sbt goal after the standard sbt flags: use the single argv item 'runMain spatialaccagent.semantic_harness.<MainObject>', not separate 'runMain' and class-name items. The executor validates and runs these commands without a shell, then always reruns the authoritative case-adapter capability tool.
</rules>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json
</source_sacg_state>

<repair_step>
{
  "action": {
    "reason": "real VCS completed the full Stage2 workload and output contract, but source-bound token-level spatial-pipeline overlap checks failed",
    "repair_gate": "case_single_layer_functional",
    "repair_kind": "localized_semantic_dut_repair",
    "repair_phase": "functional_repair",
    "root_candidate_module": "pipeline_candidate_set",
    "target_modules": [
      "residual_add_1",
      "residual_add_2"
    ],
    "targeted_replay_plan": {},
    "template_repair_requires_internal_boundary_trace": false,
    "trace_record": {
      "beat_index": null,
      "contract": "89a737769d2a1ca0b12b67b87683e9a590f5ef8ac3ec718cc1664d881410d734",
      "evidence_type": "single_layer_pipeline_contract",
      "expected_output_sha256": null,
      "expected_value": {
        "every_dependency_has_different_token_overlap": true,
        "every_stage_keeps_pipeline_filled": true,
        "whole_sequence_barrier_forbidden": true
      },
      "failure_class": "intra_layer_spatial_pipeline_violation",
      "input_fingerprint_sha256": "83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8",
      "lane_index": null,
      "logical_index": null,
      "mismatch_fraction": null,
      "module": "pipeline_candidate_set",
      "num_mismatch": null,
      "observed_value": {
        "completed_pipeline_overlap_violation": true,
        "failed_dependency_overlap_evidence": [
          {
            "boundary_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
            "different_token_overlap_observed": false,
            "dst_stage": "stage_08_residual_add_2",
            "overlaps": [],
            "src_stage": "stage_02_residual_add_1"
          }
        ],
        "failed_stage_turnover_evidence": [],
        "whole_sequence_barrier_evidence": []
      },
      "rtl_output_sha256": null,
      "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
      "stage_id": "stage_02_residual_add_1",
      "status": "fail",
      "summary": "source-bound real VCS produced 0 failed token turnovers and 1 failed dependency overlaps",
      "testbench_sha256": null,
      "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline",
      "word_index": null
    },
    "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
  },
  "debug_layer": "single_transformer_layer_kernel",
  "id": "repair_step.00",
  "llm_disposition_constraint": null,
  "scope": "verification_capability_repair",
  "status": "ready_for_agent_patch"
}
</repair_step>

<verification_capability_repair_package>
{
  "board_memory_runtime_preparation": {
    "status": "not_run",
    "summary": "exact-board memory/runtime preparation is only required for layer-3 integration"
  },
  "candidate_stage_ids": [
    "stage_02_residual_add_1",
    "stage_08_residual_add_2"
  ],
  "candidate_template_sources": [
    "Residual.scala"
  ],
  "capability_analyzer_tool": {
    "capabilities": [],
    "kind": null,
    "name": null,
    "role": null
  },
  "capability_probe": {
    "argv": [
      "python3",
      "scripts/verification/case_single_layer_stream_sim.py",
      "--run-dir",
      "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
      "--mode",
      "functional"
    ],
    "case_adapter_role": "single_layer_functional_sim",
    "case_adapter_scope": "local",
    "case_adapter_tool": "case_single_layer_functional",
    "case_id": "qwen2_hf_case",
    "cwd": "/home/remote/workspace/Qwen2-Accelerator",
    "duration_sec": 3014.78938956,
    "fatal_output_pattern": null,
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_step_00_verification_capability_probe_resource_resume.json",
    "produced_reports": [
      {
        "blockers": [],
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
        "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
        "status": "fail",
        "summary": null
      },
      {
        "blockers": [],
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
        "schema_version": "spatialaccagent.boundary_trace.v0",
        "status": "ready",
        "summary": null
      },
      {
        "blockers": [],
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/single_layer_functional.json",
        "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
        "status": "fail",
        "summary": null
      }
    ],
    "returncode": 1,
    "status": "fail",
    "stderr_tail": "",
    "stdout_tail": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json\n",
    "summary": "returncode=1"
  },
  "capability_reports": [
    {
      "blockers": [],
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
      "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
      "status": "fail",
      "summary": null
    },
    {
      "blockers": [],
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
      "schema_version": "spatialaccagent.boundary_trace.v0",
      "status": "ready",
      "summary": null
    },
    {
      "blockers": [],
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/single_layer_functional.json",
      "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
      "status": "fail",
      "summary": null
    }
  ],
  "capability_tool": {
    "capabilities": [
      "single_layer_functional_sim",
      "real_single_layer_functional_sim",
      "boundary_trace",
      "targeted_replay",
      "target_model_single_layer_semantics",
      "real_model_weights_consumed",
      "random_input_stimulus"
    ],
    "kind": "case_single_layer_functional",
    "name": "case_single_layer_functional",
    "role": "single_layer_functional_sim"
  },
  "checkpoint_framework_authority_recovery": {
    "required": false,
    "schema_version": "spatialaccagent.checkpoint_framework_authority_recovery.v1",
    "status": "not_required",
    "summary": "not a board-integration repair"
  },
  "current_board_preflight_feedback": {
    "blockers": [],
    "schema_version": "spatialaccagent.exact_board_preflight_feedback.v1",
    "status": "not_run"
  },
  "current_patch_application_feedback": {
    "blockers": [],
    "schema_version": "spatialaccagent.current_agent_patch_application_feedback.v1",
    "status": "not_run"
  },
  "current_same_source_checkpoint_calibration_failure": null,
  "current_single_layer_pipeline_trace_record": {
    "candidate_stage_ids": [
      "stage_02_residual_add_1",
      "stage_08_residual_add_2"
    ],
    "candidate_stages": [
      {
        "index": 2,
        "kind": "residual",
        "op": "residual_add_1",
        "source": "Residual.scala",
        "stage_id": "stage_02_residual_add_1",
        "template_id": "residual"
      },
      {
        "index": 8,
        "kind": "residual",
        "op": "residual_add_2",
        "source": "Residual.scala",
        "stage_id": "stage_08_residual_add_2",
        "template_id": "residual"
      }
    ],
    "candidate_template_sources": [
      "Residual.scala"
    ],
    "contract": "89a737769d2a1ca0b12b67b87683e9a590f5ef8ac3ec718cc1664d881410d734",
    "evidence_type": "single_layer_pipeline_contract",
    "expected_value": {
      "every_dependency_has_different_token_overlap": true,
      "every_stage_keeps_pipeline_filled": true,
      "whole_sequence_barrier_forbidden": true
    },
    "failure_class": "intra_layer_spatial_pipeline_violation",
    "failure_mode": "completed_pipeline_overlap_violation",
    "input_fingerprint_sha256": "83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8",
    "module": "pipeline_candidate_set",
    "observed_value": {
      "completed_pipeline_overlap_violation": true,
      "failed_dependency_overlap_evidence": [
        {
          "boundary_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
          "different_token_overlap_observed": false,
          "dst_stage": "stage_08_residual_add_2",
          "overlaps": [],
          "src_stage": "stage_02_residual_add_1"
        }
      ],
      "failed_stage_turnover_evidence": [],
      "whole_sequence_barrier_evidence": []
    },
    "pipeline_plan": {
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/pipeline_plan.json",
      "sha256": "3f7e4ee52cb8b1cdf539d6392019684d546c505579f4a002108986519b2d6b33"
    },
    "pipeline_trace_sha256": "8b721485e310341bbe5651973089a4fecadf56204a235ae1a78ec8185ae23b94",
    "semantic_manifest": {
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
      "sha256": "6447ebfdb0934c917eb35e2ab80d77fd2cf536c008f95667f98673d70f66bb84"
    },
    "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
    "stage_id": "stage_02_residual_add_1",
    "status": "fail",
    "summary": "source-bound real VCS produced 0 failed token turnovers and 1 failed dependency overlaps",
    "template_pairs": [
      {
        "generated_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
        "persistent_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
        "sha256": "110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34",
        "template_source": "Residual.scala"
      }
    ],
    "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
  },
  "current_single_layer_real_tool_failure": {
    "agent_should_apply_code_changes": true,
    "blockers": [
      "adjacent stages stage_02_residual_add_1 -> stage_08_residual_add_2 never operate on different tokens concurrently"
    ],
    "candidate_stage_ids": [
      "stage_02_residual_add_1",
      "stage_08_residual_add_2"
    ],
    "debug_layer": "single_transformer_layer_kernel",
    "failed_dependency_overlap_evidence": [
      {
        "boundary_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
        "different_token_overlap_observed": false,
        "dst_stage": "stage_08_residual_add_2",
        "overlaps": [],
        "src_stage": "stage_02_residual_add_1"
      }
    ],
    "failed_stage_turnover_evidence": [],
    "failure_class": "intra_layer_spatial_pipeline_violation",
    "failure_identity_sha256": "fde414589463c67b659ccc88546cfaf13e55e169bf0c27eca90676f1f1ff6691",
    "failure_mode": "completed_pipeline_overlap_violation",
    "input_fingerprint_sha256": "83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8",
    "pipeline_contract_sha256": "89a737769d2a1ca0b12b67b87683e9a590f5ef8ac3ec718cc1664d881410d734",
    "pipeline_trace_sha256": "8b721485e310341bbe5651973089a4fecadf56204a235ae1a78ec8185ae23b94",
    "real_tool_was_not_relaunched": true,
    "remote_workdir": "/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188",
    "report": {
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
      "sha256": "7133488e287a359b021c0ed8e0e8ba4481b1199555fe44eca5c33a2a654558c1"
    },
    "schema_version": "spatialaccagent.single_layer_agent_handoff.v1",
    "status": "ready",
    "summary": "real VCS completed the full Stage2 workload and output contract, but source-bound token-level spatial-pipeline overlap checks failed",
    "terminal_trace_flush_evidence": {
      "actual_output_line_count": 1792,
      "checks": {
        "all_required_trace_records_are_accepted": true,
        "execution_status_pass": true,
        "only_terminal_block_output_trace_is_missing": false,
        "output_line_count_matches": true,
        "remote_exit_status_pass": true,
        "required_boundaries_are_valid": true,
        "single_matching_sim_pass_declaration": true,
        "trace_positions_are_unique_and_well_formed": true
      },
      "duplicate_required_trace_position_count": 0,
      "duplicate_required_trace_positions": [],
      "expected_output_line_count": 1792,
      "inferred": false,
      "inferred_record": null,
      "malformed_required_trace_position_count": 0,
      "malformed_required_trace_positions": [],
      "missing_required_trace_position_count": 0,
      "missing_required_trace_positions": [],
      "observed_required_trace_position_count": 416,
      "required_trace_position_count": 416,
      "sim_pass_declarations": [
        {
          "beats": 1792,
          "cycles": 2236945
        }
      ],
      "unexpected_required_trace_position_count": 0,
      "unexpected_required_trace_positions": [],
      "unparsed_pipeline_trace_line_count": 0
    },
    "whole_sequence_barrier_evidence": []
  },
  "debug_layer": "single_transformer_layer_kernel",
  "exact_board_integration_required": false,
  "external_simulation_fixture_preparation": {
    "blockers": [],
    "reason": "not_a_board_integration_repair",
    "status": "not_run"
  },
  "failed_current_layer_gates": [
    {
      "name": "case_multilayer_functional",
      "status": "not_run"
    },
    {
      "name": "case_pipeline_deadlock_check",
      "status": "not_run"
    },
    {
      "name": "case_axi_ddr_interface",
      "status": "fail"
    },
    {
      "name": "case_axi_protocol_check",
      "status": "not_run"
    },
    {
      "name": "case_ddr_image_roundtrip",
      "status": "not_run"
    },
    {
      "name": "functional_sim",
      "status": "fail"
    },
    {
      "name": "case_board_semantic_evidence",
      "status": "not_run"
    }
  ],
  "focused_real_tool_failure_snapshot": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/focused_real_tool_failure_snapshot.json",
  "generated_sources": [],
  "generation_mode": "create",
  "leaf_stage_report_path": null,
  "leaf_stage_report_summary": {},
  "localized_instrumentation_evidence": {
    "status": "not_run",
    "summary": "current repair step is not an instrumentation evidence collection step"
  },
  "pending_same_source_checkpoint_calibration": null,
  "policy": {
    "after_capability_repair_rerun_same_layer_leaf_golden": true,
    "close_proven_simulation_only_observability_defects_in_same_atomic_patch": true,
    "do_not_modify_golden_to_match_buggy_rtl": true,
    "do_not_treat_missing_golden_as_hardware_pass": true,
    "empty_generated_sources_is_valid_for_first_create": true,
    "expected_output_must_come_from_target_model_inference": true,
    "preserve_checkpoint_input_reference_numeric_policy_and_tolerance_hashes": true,
    "preserve_exact_user_sample_wrapper_hashes": true,
    "random_generation_is_input_only": true,
    "repair_checker_or_golden_reference_before_layer_promotion": true,
    "repair_dut_loader_harness_or_instrumentation": true,
    "repair_experience_is_hypothesis_prior_only": true,
    "semantic_selected_template_repair_approved": true,
    "weight_file_presence_does_not_prove_dut_consumption": true
  },
  "pre_patch_dependency_refresh": {
    "status": "not_run",
    "summary": "skipped because an unchanged applied patch has a resumable validation checkpoint"
  },
  "pre_patch_simulation_checkpoint_request": {
    "status": "not_run",
    "summary": "checkpoint replay is only required for Stage-3 board repair"
  },
  "prior_localized_agent_feedback": null,
  "prior_resource_validation_resume": {
    "applied_patch_checkpoint_reused": true,
    "blockers": [],
    "cache_reused": true,
    "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/agent_requested_validation.json",
    "repair_checkpoint": {
      "beat_index": null,
      "boundary_id": null,
      "cycle": null,
      "fingerprint_sha256": "ff4ad5a361e276bd6d50472787c9f57376334595d89268e21b5a2455d8aee0f7",
      "module": null,
      "repair_kind": "case_single_layer_functional",
      "repair_phase": null,
      "schema_version": "spatialaccagent.repair_step_checkpoint.v1",
      "scope": "verification_capability_repair",
      "stage_id": null,
      "step_id": "repair_step.00",
      "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
    },
    "requests": 2,
    "results": [
      {
        "argv": [
          "sbt",
          "--no-server",
          "Compile/compile"
        ],
        "cleaned_output_root": null,
        "cleaned_output_roots": [],
        "cwd": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
        "duration_sec": 6.341750035004225,
        "fatal_output_pattern": null,
        "purpose": "Compile the bounded ElementwiseMul token-boundary state correction against the authoritative generated Chisel project and trusted HardFloat dependencies.",
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[info] compiling 1 Scala source to /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/target/scala-2.13/classes ...\n[info] done compiling\n[success] Total time: 4 s, completed Jul 23, 2026, 2:43:11 AM\n",
        "summary": "returncode=0"
      },
      {
        "argv": [
          "sbt",
          "--no-server",
          "runMain spatialaccagent.semantic_harness.ElaborateSingleLayerClosure"
        ],
        "cleaned_output_root": null,
        "cleaned_output_roots": [],
        "cwd": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
        "duration_sec": 397.57917659997474,
        "fatal_output_pattern": null,
        "purpose": "Fully re-elaborate the connected single-layer semantic harness so the executor can rematerialize source bindings and rerun the same real Stage2 VCS gate.",
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": " 16)\n[warn]             ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 65:11: [W004] Dynamic index with width 12 is too wide for Vec of size 1024 (expected index width 10).\n[warn]       sine(scalarIndex) := io.runtime.bits.data(15, 0)\n[warn]           ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 66:11: [W004] Dynamic index with width 12 is too wide for Vec of size 1024 (expected index width 10).\n[warn]       sine(scalarIndex + 1.U) := io.runtime.bits.data(31, 16)\n[warn]           ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 110:14: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]       qVector(dimension) := inputFields(lane)\n[warn]              ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 111:14: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]       kVector(dimension) := inputFields(p.qkv.qkvElemsPerBeat + lane)\n[warn]              ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 112:14: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]       vVector(dimension) := inputFields(2 * p.qkv.qkvElemsPerBeat + lane)\n[warn]              ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 152:53: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     val rotatedQ = Mux(inFirstHalf, flipSign(qVector(partnerDimension)), qVector(partnerDimension))\n[warn]                                                     ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 152:81: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     val rotatedQ = Mux(inFirstHalf, flipSign(qVector(partnerDimension)), qVector(partnerDimension))\n[warn]                                                                                 ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 153:53: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     val rotatedK = Mux(inFirstHalf, flipSign(kVector(partnerDimension)), kVector(partnerDimension))\n[warn]                                                     ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 153:81: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     val rotatedK = Mux(inFirstHalf, flipSign(kVector(partnerDimension)), kVector(partnerDimension))\n[warn]                                                                                 ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 156:41: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     qOutput(lane) := applyRotary(qVector(dimension), rotatedQ, cosine(tableIndex), sine(tableIndex))\n[warn]                                         ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 156:70: [W004] Dynamic index with width 11 is too wide for Vec of size 1024 (expected index width 10).\n[warn]     qOutput(lane) := applyRotary(qVector(dimension), rotatedQ, cosine(tableIndex), sine(tableIndex))\n[warn]                                                                      ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 156:88: [W004] Dynamic index with width 11 is too wide for Vec of size 1024 (expected index width 10).\n[warn]     qOutput(lane) := applyRotary(qVector(dimension), rotatedQ, cosine(tableIndex), sine(tableIndex))\n[warn]                                                                                        ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 157:41: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     kOutput(lane) := applyRotary(kVector(dimension), rotatedK, cosine(tableIndex), sine(tableIndex))\n[warn]                                         ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 157:70: [W004] Dynamic index with width 11 is too wide for Vec of size 1024 (expected index width 10).\n[warn]     kOutput(lane) := applyRotary(kVector(dimension), rotatedK, cosine(tableIndex), sine(tableIndex))\n[warn]                                                                      ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 157:88: [W004] Dynamic index with width 11 is too wide for Vec of size 1024 (expected index width 10).\n[warn]     kOutput(lane) := applyRotary(kVector(dimension), rotatedK, cosine(tableIndex), sine(tableIndex))\n[warn]                                                                                        ^\n[warn] src/main/scala/spatialaccagent/templates/RoPE.scala 158:29: [W004] Dynamic index with width 7 is too wide for Vec of size 64 (expected index width 6).\n[warn]     vOutput(lane) := vVector(dimension)\n[warn]                             ^\n[warn] src/main/scala/spatialaccagent/templates/Attention.scala 114:14: [W004] Dynamic index with width 12 is too wide for Vec of size 2048 (expected index width 11).\n[warn]       kMemory(kvIndex) := inputFields(p.qkvElemsPerBeat + lane)\n[warn]              ^\n[warn] src/main/scala/spatialaccagent/templates/Attention.scala 115:14: [W004] Dynamic index with width 12 is too wide for Vec of size 2048 (expected index width 11).\n[warn]       vMemory(kvIndex) := inputFields(2 * p.qkvElemsPerBeat + lane)\n[warn]              ^\n[warn] src/main/scala/spatialaccagent/templates/Attention.scala 143:32: [W004] Dynamic index with width 12 is too wide for Vec of size 2048 (expected index width 11).\n[warn]         IeeeMath.toFp32(kMemory(kIndex), p.elemBits)\n[warn]                                ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 118:12: [W004] Dynamic index with width 1 is too wide for Vec of size 1 (expected index width 0).\n[warn]     addrMem(collectCnt) := io.in.bits.addr\n[warn]            ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 119:10: [W004] Dynamic index with width 1 is too wide for Vec of size 1 (expected index width 0).\n[warn]     stMem(collectCnt) := io.in.bits.st\n[warn]          ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 124:40: [W002] Dynamic index with width 6 is too large for extractee of width 16\n[warn]       val externalKeep = maskForCollect(index)\n[warn]                                        ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 133:15: [W004] Dynamic index with width 6 is too wide for Vec of size 16 (expected index width 4).\n[warn]       scoreMem(index) := inputVec(i)\n[warn]               ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 134:14: [W004] Dynamic index with width 6 is too wide for Vec of size 16 (expected index width 4).\n[warn]       keepMem(index) := keep\n[warn]              ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 211:36: [W004] Dynamic index with width 6 is too wide for Vec of size 16 (expected index width 4).\n[warn]     outputVec(i) := probabilityBits(index)\n[warn]                                    ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 216:26: [W004] Dynamic index with width 1 is too wide for Vec of size 1 (expected index width 0).\n[warn]   io.out.bits.st := stMem(emitCnt)\n[warn]                          ^\n[warn] src/main/scala/spatialaccagent/templates/Softmax.scala 217:30: [W004] Dynamic index with width 1 is too wide for Vec of size 1 (expected index width 0).\n[warn]   io.out.bits.addr := addrMem(emitCnt)\n[warn]                              ^\n[warn] src/main/scala/spatialaccagent/templates/Attention.scala 182:32: [W004] Dynamic index with width 12 is too wide for Vec of size 2048 (expected index width 11).\n[warn]         IeeeMath.toFp32(vMemory(vIndex), p.elemBits)\n[warn]                                ^\n[warn] There were 32 warning(s) during hardware elaboration.\n[success] Total time: 378 s (06:18), completed Jul 23, 2026, 2:49:32 AM\n",
        "summary": "returncode=0"
      }
    ],
    "sbt_heap_mb": 8192,
    "schema_version": "spatialaccagent.agent_requested_validation.v1",
    "source_patch_application": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/agent_patch_application.json",
    "source_patch_application_sha256": "ee57a734270e939cfa4aa6ad42d59e2724e087e375fc27ab615caa5962cc2896",
    "status": "pass",
    "summary": "reused passing validation for the unchanged applied repair-step patch"
  },
  "reference_builder_probe": {
    "status": "not_run",
    "summary": "no reference builder required for this repair kind"
  },
  "reference_builder_tool": {
    "capabilities": [],
    "kind": null,
    "name": null,
    "role": ""
  },
  "relevant_repair_experience": {
    "database_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/_shared_experience/repair_experience.jsonl",
    "database_sha256": "5a15334a53a1f720e53991dcd8f4888bd80619009d68ce143a20dadad5281900",
    "episodes": [
      {
        "evidence_bindings": [
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/00_agent_patch_application_agent_patch_application.json",
            "role": "agent_patch_application",
            "sha256": "384b9446afc109be9b88fdbd750aa35f0de817451438d330c8612be4fdfaac3b"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/01_agent_requested_validation_agent_requested_validation.json",
            "role": "agent_requested_validation",
            "sha256": "18afdfe79096c6ae90c910492147d12037c6b8e367d592f80cc0bf3264fafe6f"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/02_adaptive_observation_decision_validation_adaptive_observation_decision_validation.json",
            "role": "adaptive_observation_decision_validation",
            "sha256": "8993690de40ddd45c73b87a868dc5ad0155e9eadd36f46458849da71928b9c68"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/03_adaptive_observation_state_current.json",
            "role": "adaptive_observation_state",
            "sha256": "a0dd60e57f9960ac129f4b6b966fa1df765533bf4fc0ff51a0e02d7db97f2126"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/04_context_package_repair_step_00_verification_capability_repair_package.json",
            "role": "context_package",
            "sha256": "49dce667f80499cd884f5b5e6242f10c8569dfb0d020c2abb326b917b0a43205"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/05_llm_record_localized_semantic_dut_repair_agent_result.json",
            "role": "llm_record",
            "sha256": "434c60d00c1f7edb8026af76e6f181bd65d19e97fbc8c515800a5cee24b65443"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/06_post_patch_capability_probe_log_repair_step_00_verification_capability_probe_post_patch.json",
            "role": "post_patch_capability_probe_log",
            "sha256": "b5ffc04900978debcc6862bac8ac48407d21a8cb38df26c45dea5c3161756389"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/07_dut_weight_binding_materialization_dut_weight_binding_materialization.json",
            "role": "dut_weight_binding_materialization",
            "sha256": "06618045e33938a16c1755ff7a40702e856a9287604172114f57216a877bf31b"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/08_capability_report_single_layer_functional_report.json",
            "role": "capability_report",
            "sha256": "86e6390c7e50396baf76362c5422bee957247ddef590ff052279ce2c5e4df4fb"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/09_capability_report_boundary_trace.json",
            "role": "capability_report",
            "sha256": "3d9ced389906e4762e4d3ae7f44b76c7c0982af461a4380659e01dd62c89ae02"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/10_capability_report_single_layer_functional.json",
            "role": "capability_report",
            "sha256": "cb430910c162867c1a3f18b5a7e18bc157f4173b4ff64dab3c60f03087ca65d2"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/11_request_path_localized_semantic_dut_repair_agent_prompt.md",
            "role": "request_path",
            "sha256": "025494d0c30ddb1400681e3d37d6d789b718a682ae5f0fdd9699031fcd2e4d51"
          }
        ],
        "experience_id": "repair_experience.8da9d9915fa1cf2f92e8016527066f468112e709862534b91fbd8208d0b57fc3",
        "intervention": {
          "agent": "localized_semantic_dut_repair_agent",
          "file_changes": [
            {
              "after_sha256": "f488b4f24af1a6607cf5a9cb694269b23933c1074988e2dcd22840906f57619a",
              "before_sha256": "2d7b66fba7a056a924a8e4441f86299861c8cd87d42573e590637747f170d175",
              "bytes": 3614,
              "operation": "replace",
              "path_basename": "Residual.scala",
              "suffix": ".scala"
            },
            {
              "after_sha256": "f488b4f24af1a6607cf5a9cb694269b23933c1074988e2dcd22840906f57619a",
              "before_sha256": "2d7b66fba7a056a924a8e4441f86299861c8cd87d42573e590637747f170d175",
              "bytes": 3614,
              "operation": "replace",
              "path_basename": "Residual.scala",
              "suffix": ".scala"
            },
            {
              "after_sha256": "aaf592fa41088d94fb558c63ac51d6be31e4c2776778870e00b01355d7a7a484",
              "before_sha256": "cffed9d49b903a4c66ff96e4fe83976b8af6a2642ca1d3478ab658a642008e7d",
              "bytes": 3630,
              "operation": "replace",
              "path_basename": "Elementwise.scala",
              "suffix": ".scala"
            },
            {
              "after_sha256": "aaf592fa41088d94fb558c63ac51d6be31e4c2776778870e00b01355d7a7a484",
              "before_sha256": "cffed9d49b903a4c66ff96e4fe83976b8af6a2642ca1d3478ab658a642008e7d",
              "bytes": 3630,
              "operation": "replace",
              "path_basename": "Elementwise.scala",
              "suffix": ".scala"
            }
          ],
          "model": "gpt-5.6-sol",
          "prompt_hash": "025494d0c30ddb1400681e3d37d6d789b718a682ae5f0fdd9699031fcd2e4d51",
          "repair_checkpoint": {
            "beat_index": null,
            "boundary_id": null,
            "cycle": null,
            "fingerprint_sha256": "99259ed2b6884bc69031f426309fad4153e36cb85dd55a61acae27ec2c2a2762",
            "module": "pipeline_candidate_set",
            "repair_kind": "localized_semantic_dut_repair",
            "repair_phase": "functional_repair",
            "schema_version": "spatialaccagent.repair_step_checkpoint.v1",
            "scope": "verification_capability_repair",
            "stage_id": "stage_02_residual_add_1",
            "step_id": "repair_step.00",
            "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
          },
          "root_cause": "The executed trace is complete and accepted-transfer-attributed, so this is not a trace-flush or checker-attribution defect. The directly contradictory source behavior is concentrated in two templates. ResidualAdd currently drives residual.ready from computed.valid && out.ready and computed.ready from residual.valid && out.ready; therefore an early residual/skip branch cannot be admitted, downstream backpressure propagates directly into the preceding stage, and no successor token can occupy the residual stage while the predecessor remains active. This exactly explains the failed stage_02 and stage_08 turnovers and the failed stage_02->stage_03, stage_02->stage_08, and stage_07->stage_08 overlap records. ElementwiseMul uses the same direct rendezvous and has no packet-boundary elasticity, so its predecessor token becomes inactive before the next token's first accepted input arrives 225 cycles later. A bounded packet-elastic join is sufficient for both cases: independently queue the two operands, preserve ordered pairing and IEEE arithmetic, and retain each nonterminal token-final result until the first pair of the successor token is present. RMSNorm is excluded because only its first turnover failed while all later turnovers were one cycle and both of its downstream dependency edges already overlapped; the residual boundary correction keeps its predecessor token resident until the successor exists. FFN is excluded because stage_07 had one-cycle turnover for every transition and stage_06->stage_07 overlap already passed.",
          "summary": "Apply the smallest causally sufficient correction to the Residual and Elementwise template pairs. Both current modules are unbuffered combinational rendezvous joins. ResidualAdd prevents either branch and the successor token from being admitted independently, causing every failed residual turnover and all three failed dependency overlaps. ElementwiseMul has the same non-elastic join and retires each token before the next token arrives after the observed fixed 225-cycle producer latency. The replacements add synthesizable branch elasticity and retain each nonterminal token-final beat until the successor token is admitted. Norm.scala and FFN.scala are not edited because their current executed turnover and dependency records do not independently implicate them."
        },
        "key": {
          "debug_layer": "single_transformer_layer_kernel",
          "failure_class": "intra_layer_spatial_pipeline_violation",
          "frontier_id": "kernel_output_token_sequence_continuation",
          "module_role": "pipeline_candidate_set",
          "repair_gate": "case_single_layer_functional",
          "repair_kind": "localized_semantic_dut_repair",
          "repair_scope": "verification_capability_repair",
          "stage_id": "stage_02_residual_add_1",
          "stage_role": "residual_add_1",
          "verification_scope": "single_layer_closure",
          "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
        },
        "observation": {
          "contract_sha256": null,
          "input_fingerprint_sha256": "eb376c0f4d5466f9c6ffdcd10a8d3aea3d9bcce31dde0296993ffb37e52358a0",
          "summary": "real VCS completed the full Stage2 workload and output contract, but source-bound token-level spatial-pipeline overlap checks failed",
          "trace_sha256": "d540660df677a529b8e6890b60ed1d9006e614562d1d8bb32616d1da599fd2d5"
        },
        "outcome": {
          "agent_requested_validation": {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/01_agent_requested_validation_agent_requested_validation.json",
            "sha256": "18afdfe79096c6ae90c910492147d12037c6b8e367d592f80cc0bf3264fafe6f",
            "status": "pass"
          },
          "capability_reports": [
            {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/08_capability_report_single_layer_functional_report.json",
              "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
              "sha256": "86e6390c7e50396baf76362c5422bee957247ddef590ff052279ce2c5e4df4fb",
              "status": "fail"
            },
            {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/09_capability_report_boundary_trace.json",
              "schema_version": "spatialaccagent.boundary_trace.v0",
              "sha256": "3d9ced389906e4762e4d3ae7f44b76c7c0982af461a4380659e01dd62c89ae02",
              "status": "ready"
            },
            {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0516/10_capability_report_single_layer_functional.json",
              "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
              "sha256": "cb430910c162867c1a3f18b5a7e18bc157f4173b4ff64dab3c60f03087ca65d2",
              "status": "fail"
            }
          ],
          "evidence_grade": "same_layer_real_tool_fail",
          "post_failure_class": "intra_layer_spatial_pipeline_violation",
          "post_input_fingerprint_sha256": "eb376c0f4d5466f9c6ffdcd10a8d3aea3d9bcce31dde0296993ffb37e52358a0",
          "stage_passed": false,
          "status": "falsified",
          "step_status": "fail",
          "summary": "case_single_layer_functional still lacks passing independent verification capability evidence after bounded agent execution for ['residual_add_1', 'rms_norm_2', 'activation_mul', 'mlp_down_proj', 'residual_add_2']"
        },
        "similarity": {
          "exact_match_fields": [
            "failure_class",
            "violated_contract",
            "stage_role",
            "repair_gate",
            "verification_scope",
            "repair_kind",
            "debug_layer"
          ],
          "score": 46
        },
        "transfer_policy": {
          "never_authorizes_file_edits_or_promotion": true,
          "rebind_current_sources_and_contracts": true,
          "same_layer_real_tool_revalidation_required": true,
          "use_as_hypothesis_prior_only": true
        }
      },
      {
        "evidence_bindings": [
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/00_agent_patch_application_agent_patch_application.json",
            "role": "agent_patch_application",
            "sha256": "b63ff3fd3e949c6c48cc8eb6dae084c6ddcfdf35e4634ffa1c44907e60af4d63"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/01_agent_requested_validation_agent_requested_validation.json",
            "role": "agent_requested_validation",
            "sha256": "7c929aefcb0e8b8cbdcf120f2af0c4b72e7e2fd07d42dba71975d1af796840bf"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/02_adaptive_observation_decision_validation_adaptive_observation_decision_validation.json",
            "role": "adaptive_observation_decision_validation",
            "sha256": "8993690de40ddd45c73b87a868dc5ad0155e9eadd36f46458849da71928b9c68"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/03_adaptive_observation_state_current.json",
            "role": "adaptive_observation_state",
            "sha256": "a0dd60e57f9960ac129f4b6b966fa1df765533bf4fc0ff51a0e02d7db97f2126"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/04_context_package_repair_step_00_verification_capability_repair_package.json",
            "role": "context_package",
            "sha256": "0a9b4a0f2b40559de3dcd5b9b08c0de1a783d65cd4853a4c970bcda54bdd5a9b"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/05_llm_record_localized_semantic_dut_repair_agent_result.json",
            "role": "llm_record",
            "sha256": "9c52dd299d45c2d15c473003d70b459074ad0cba7c3e84e129c26ae14f963e28"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/06_post_patch_capability_probe_log_repair_step_00_verification_capability_probe_post_patch.json",
            "role": "post_patch_capability_probe_log",
            "sha256": "97a019058b60297a2fba4215041d5adccb5f149061792c94d30360b346ef6d83"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/07_dut_weight_binding_materialization_dut_weight_binding_materialization.json",
            "role": "dut_weight_binding_materialization",
            "sha256": "2c95ec5fcae1e28d88840401f0b674f705f103b7488378549622245ffe23c2a6"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/08_capability_report_single_layer_functional_report.json",
            "role": "capability_report",
            "sha256": "d41f5a37ea8cd915e69064da58f290a8d490aff3a1b4dacded0ba1bb0746159c"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/09_capability_report_boundary_trace.json",
            "role": "capability_report",
            "sha256": "af9015c9d658de8c8b6e98d48f2a2d91f0f0581197d4497b1f0ed91c5d9da161"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/10_capability_report_single_layer_functional.json",
            "role": "capability_report",
            "sha256": "a3188c6342ed0ccfbc05ffeca6dbc239f3595459e38db7f486657068da24dc12"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/11_request_path_localized_semantic_dut_repair_agent_prompt.md",
            "role": "request_path",
            "sha256": "bbceb8b3e832fd172b7aa87cb88ce550b05443bd1bfd74a8bcac2122360462d1"
          }
        ],
        "experience_id": "repair_experience.043a3502ff89b14fdd058ecc69e8a8fc11a576717747e463bd17efb5e03f5e8f",
        "intervention": {
          "agent": "localized_semantic_dut_repair_agent",
          "file_changes": [
            {
              "after_sha256": "110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34",
              "before_sha256": "f488b4f24af1a6607cf5a9cb694269b23933c1074988e2dcd22840906f57619a",
              "bytes": 4105,
              "operation": "replace",
              "path_basename": "Residual.scala",
              "suffix": ".scala"
            },
            {
              "after_sha256": "110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34",
              "before_sha256": "f488b4f24af1a6607cf5a9cb694269b23933c1074988e2dcd22840906f57619a",
              "bytes": 4105,
              "operation": "replace",
              "path_basename": "Residual.scala",
              "suffix": ".scala"
            }
          ],
          "model": "gpt-5.6-sol",
          "prompt_hash": "bbceb8b3e832fd172b7aa87cb88ce550b05443bd1bfd74a8bcac2122360462d1",
          "repair_checkpoint": {
            "beat_index": null,
            "boundary_id": null,
            "cycle": null,
            "dynamic_source_bound_route": true,
            "fingerprint_sha256": "d4fc683297d07c3243270aeceed0ccd70bbe71f0bc315204ff2fdf27343c1cad",
            "module": "pipeline_candidate_set",
            "repair_kind": "localized_semantic_dut_repair",
            "repair_phase": "functional_repair",
            "schema_version": "spatialaccagent.repair_step_checkpoint.v2",
            "scope": "verification_capability_repair",
            "source_bound_failure_identity_sha256": "3597c53863044394e90433dd43523334949ee4ebf406d55dbfc7306abdbe2d63",
            "source_bound_input_fingerprint_sha256": "e1dd9406f761fc0a3e191b3d10825349d7348719075f3d25c97bc51b37d7371c",
            "source_repair_checkpoint_fingerprint_sha256": "ff4ad5a361e276bd6d50472787c9f57376334595d89268e21b5a2455d8aee0f7",
            "stage_id": "stage_01_self_attention",
            "step_id": "repair_step.00",
            "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
          },
          "root_cause": "The current ResidualAdd implementation attempts to retain a nonterminal token-final result with `tokenFinalBeat && !sequenceFinalBeat`, but defines `sequenceFinalBeat` directly as `computedQ.io.deq.bits.last`. In this stream protocol, last is a token-packet boundary, not a full-sequence boundary: the supplied Attention implementation advances collectToken whenever io.in.bits.last is accepted. Thus computedQ.io.deq.bits.last is asserted on token 0's final beat, the retention condition is false, heldValid is not established, and stage_02 retires token 0 at cycle 7716321 even though token 1 cannot enter until cycle 7731071. RMSNorm then finishes token 0 at cycle 7716487 and has no successor input until cycle 7731073, creating the second observed gap. This directly distinguishes the current failure from the prior falsified intervention: the intended elasticity exists structurally, but its sequence-final attribution is wrong. Tracking the accepted paired token index against the clamped immutable cfg.seqlen makes the existing hold path effective without changing payload arithmetic, metadata, stage order, model dimensions, runtime ABI, or numeric policy.",
          "summary": "Replace only the persistent/generated Residual.scala pair. The prior packet-elastic repair is present but its nonterminal-token predicate is incorrect: it treats StreamBeat.last as the end of the full sequence even though the current operator protocol uses last at every token boundary. Consequently the hold path is bypassed at token 0, reproducing the measured stage_02 and downstream stage_03 turnover gaps. The correction adds an explicit sequence-token counter derived from immutable cfg.seqlen and retains every nonfinal token-final residual result until the successor pair is resident. Attention.scala, Norm.scala, and FFN.scala are excluded because the current executed record reports no failed dependency overlap, RMSNorm can return to input loading one cycle after its output-final transfer, and no turnover failure is attributed to the attention or MLP stages themselves."
        },
        "key": {
          "debug_layer": "single_transformer_layer_kernel",
          "failure_class": "intra_layer_spatial_pipeline_violation",
          "frontier_id": "kernel_output_token_sequence_continuation",
          "module_role": "pipeline_candidate_set",
          "repair_gate": "case_single_layer_functional",
          "repair_kind": "localized_semantic_dut_repair",
          "repair_scope": "verification_capability_repair",
          "stage_id": "stage_01_self_attention",
          "stage_role": "self_attention",
          "verification_scope": "single_layer_closure",
          "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
        },
        "observation": {
          "contract_sha256": null,
          "input_fingerprint_sha256": "e1dd9406f761fc0a3e191b3d10825349d7348719075f3d25c97bc51b37d7371c",
          "summary": "real VCS proved an irreversible adjacent-token stage turnover bubble; the same Stage2 hardware Agent must repair the source-bound design",
          "trace_sha256": "0af0e77c775bee539d6f87f5b589ac3db7de14e5123d24c8827405fbcee9e4a6"
        },
        "outcome": {
          "agent_requested_validation": {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/01_agent_requested_validation_agent_requested_validation.json",
            "sha256": "7c929aefcb0e8b8cbdcf120f2af0c4b72e7e2fd07d42dba71975d1af796840bf",
            "status": "pass"
          },
          "capability_reports": [
            {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/08_capability_report_single_layer_functional_report.json",
              "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
              "sha256": "d41f5a37ea8cd915e69064da58f290a8d490aff3a1b4dacded0ba1bb0746159c",
              "status": "fail"
            },
            {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/09_capability_report_boundary_trace.json",
              "schema_version": "spatialaccagent.boundary_trace.v0",
              "sha256": "af9015c9d658de8c8b6e98d48f2a2d91f0f0581197d4497b1f0ed91c5d9da161",
              "status": "ready"
            },
            {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/loop/iteration_0518/10_capability_report_single_layer_functional.json",
              "schema_version": "spatialaccagent.single_layer_functional_sim.v1",
              "sha256": "a3188c6342ed0ccfbc05ffeca6dbc239f3595459e38db7f486657068da24dc12",
              "status": "fail"
            }
          ],
          "evidence_grade": "same_layer_real_tool_fail",
          "post_failure_class": "remote_tool_failure",
          "post_input_fingerprint_sha256": "1989e49ed5d9e56f5930f0aae46cd2f6913b1fd298c364d58c95ad88e49d43b2",
          "stage_passed": false,
          "status": "falsified",
          "step_status": "fail",
          "summary": "case_single_layer_functional still lacks passing independent verification capability evidence after bounded agent execution for ['self_attention', 'residual_add_1', 'rms_norm_2', 'mlp_gate_proj', 'mlp_up_proj', 'residual_add_2']"
        },
        "similarity": {
          "exact_match_fields": [
            "failure_class",
            "violated_contract",
            "repair_gate",
            "verification_scope",
            "repair_kind",
            "debug_layer"
          ],
          "score": 38
        },
        "transfer_policy": {
          "never_authorizes_file_edits_or_promotion": true,
          "rebind_current_sources_and_contracts": true,
          "same_layer_real_tool_revalidation_required": true,
          "use_as_hypothesis_prior_only": true
        }
      }
    ],
    "policy": {
      "current_same_layer_real_tool_revalidation_is_mandatory": true,
      "current_source_contract_and_real_tool_evidence_take_precedence": true,
      "experience_never_expands_edit_authority": true,
      "falsified_interventions_must_not_be_repeated_without_new_distinguishing_evidence": true,
      "validated_success_is_a_hypothesis_prior_not_a_pass": true
    },
    "query": {
      "debug_layer": "single_transformer_layer_kernel",
      "failure_class": "intra_layer_spatial_pipeline_violation",
      "repair_gate": "case_single_layer_functional",
      "repair_kind": "localized_semantic_dut_repair",
      "repair_scope": "verification_capability_repair",
      "stage_id": "stage_02_residual_add_1",
      "stage_role": "residual_add_1",
      "verification_scope": "single_layer_closure",
      "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
    },
    "schema_version": "spatialaccagent.repair_experience_context.v1",
    "selected_count": 2,
    "status": "ready",
    "sync": {
      "database_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/_shared_experience/repair_experience.jsonl",
      "duplicates": 2,
      "errors": [],
      "recorded": 0,
      "scanned_iteration_count": 32,
      "schema_version": "spatialaccagent.repair_experience_sync.v1",
      "status": "pass"
    }
  },
  "repair_gate": "case_single_layer_functional",
  "repair_kind": "localized_semantic_dut_repair",
  "repair_scope": "verification_capability_repair",
  "repair_source_bundle": {
    "all_documents_complete": true,
    "bundle_profile": "localized_semantic_dut_repair",
    "document_chars": 281711,
    "document_count": 9,
    "documents": [
      {
        "bytes": 1120,
        "content": "{\n  \"_llm_provenance\": {\n    \"mode\": \"llm\",\n    \"sub_agent\": \"model_config_agent\",\n    \"used_fallback\": false\n  },\n  \"attention\": {\n    \"causal\": true,\n    \"head_dim\": 64,\n    \"kind\": \"gqa\",\n    \"num_kv_heads\": 2,\n    \"num_q_heads\": 14,\n    \"out_bias\": false,\n    \"position_encoding\": {\n      \"rope_theta\": 1000000.0,\n      \"type\": \"rope\"\n    },\n    \"qkv_bias\": true\n  },\n  \"block\": {\n    \"operator_sequence\": [\n      \"rms_norm_1\",\n      \"self_attention\",\n      \"residual_add_1\",\n      \"rms_norm_2\",\n      \"mlp_gate_proj\",\n      \"mlp_up_proj\",\n      \"activation_mul\",\n      \"mlp_down_proj\",\n      \"residual_add_2\"\n    ],\n    \"type\": \"decoder\"\n  },\n  \"hidden_size\": 896,\n  \"mlp\": {\n    \"activation\": \"silu\",\n    \"down_bias\": false,\n    \"intermediate_size\": 4864,\n    \"type\": \"gated\",\n    \"up_bias\": false\n  },\n  \"model_type\": \"qwen2\",\n  \"norm\": {\n    \"eps\": 1e-06,\n    \"has_bias\": false,\n    \"position\": \"pre\",\n    \"type\": \"rms_norm\"\n  },\n  \"num_layers\": 24,\n  \"target_max_seq_len\": 16,\n  \"weight_layout\": {\n    \"mlp\": \"gate_up_down\",\n    \"norm\": \"weight_only\",\n    \"out_proj\": \"dense\",\n    \"qkv\": \"separate_q_k_v\"\n  }\n}\n",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/input/model_config.json",
        "sha256": "55b4c398c3a9eaeaf6a8c3bd25e5b51e83d46c30c002ed562c9efa98cd50b113",
        "truncated": false
      },
      {
        "bytes": 2047,
        "content": "{\n  \"_llm_provenance\": {\n    \"mode\": \"llm\",\n    \"sub_agent\": \"numeric_policy_agent\",\n    \"used_fallback\": false\n  },\n  \"_numeric_comparison_resolution\": {\n    \"default_policy_id\": \"spatialaccagent.loose_numeric_compare.v1\",\n    \"defaulted_fields\": [\n      \"atol\",\n      \"rtol\",\n      \"max_mismatch_fraction\"\n    ],\n    \"defaults\": {\n      \"atol\": 0.1,\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1\n    },\n    \"dut_outputs_used_for_resolution\": false,\n    \"field_sources\": {\n      \"atol\": \"framework_default\",\n      \"max_mismatch_fraction\": \"framework_default\",\n      \"rtol\": \"framework_default\"\n    },\n    \"provided_values_take_precedence\": true,\n    \"resolved\": {\n      \"atol\": 0.1,\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1\n    },\n    \"schema_version\": \"spatialaccagent.numeric_comparison_resolution.v1\"\n  },\n  \"default_rules\": {\n    \"acc_dtype\": \"fp32\",\n    \"activation_dtype\": \"fp16\",\n    \"rounding\": \"nearest_even\",\n    \"saturation\": false,\n    \"scale_dtype\": \"fp16\",\n    \"weight_dtype\": \"fp16\"\n  },\n  \"notes\": [\n    \"Explicit numeric policy provided in current_run_numeric_policy.md; README fallback policy is not used for this run.\",\n    \"End-to-end acceptance target is board-runnable execution with valid output and no deadlock; exact numerical equivalence to the source model is not required for this run unless a later user-provided policy strengthens the tolerance.\",\n    \"If this policy is replaced, checkpoint reuse must treat it as an input change and rerun affected stages.\",\n    \"Missing or invalid quantitative comparison values use spatialaccagent.loose_numeric_compare.v1; current-run provided values take precedence.\"\n  ],\n  \"policy_id\": \"current_run_numeric_policy.md\",\n  \"schema_version\": \"1.0\",\n  \"tolerance\": {\n    \"comparison\": {\n      \"atol\": 0.1,\n      \"default_policy_id\": \"spatialaccagent.loose_numeric_compare.v1\",\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1,\n      \"source\": \"framework_default\"\n    },\n    \"stage\": \"functional_or_shape\",\n    \"system\": \"valid_output_required\"\n  }\n}\n",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/input/numeric_policy.json",
        "sha256": "29680d3fbddc19f210b9ffa17dc705aa4fac1f0ee594ddd0c98fa1a662c985b5",
        "truncated": false
      },
      {
        "bytes": 55804,
        "content": "{\n  \"accelerator_scope\": \"transformer_blocks_only\",\n  \"blockers\": [],\n  \"dut_weight_binding_requirements\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/dut_weight_binding_requirements.json\",\n  \"dut_weight_binding_requirements_sha256\": \"83058e50bc69304498b9d73ae743e3045eec962980c9bb0103755b7cd3a22ae9\",\n  \"numeric_comparison_policy\": {\n    \"atol\": 0.1,\n    \"max_mismatch_fraction\": 0.05,\n    \"rtol\": 0.1\n  },\n  \"numeric_comparison_resolution\": {\n    \"default_policy_id\": \"spatialaccagent.loose_numeric_compare.v1\",\n    \"defaulted_fields\": [\n      \"atol\",\n      \"rtol\",\n      \"max_mismatch_fraction\"\n    ],\n    \"defaults\": {\n      \"atol\": 0.1,\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1\n    },\n    \"dut_outputs_used_for_resolution\": false,\n    \"field_sources\": {\n      \"atol\": \"framework_default\",\n      \"max_mismatch_fraction\": \"framework_default\",\n      \"rtol\": \"framework_default\"\n    },\n    \"provided_values_take_precedence\": true,\n    \"resolved\": {\n      \"atol\": 0.1,\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1\n    },\n    \"schema_version\": \"spatialaccagent.numeric_comparison_resolution.v1\"\n  },\n  \"numeric_policy\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/input/numeric_policy.json\",\n  \"numeric_policy_sha256\": \"29680d3fbddc19f210b9ffa17dc705aa4fac1f0ee594ddd0c98fa1a662c985b5\",\n  \"policy\": {\n    \"expected_output_is_computed_not_random\": true,\n    \"expected_output_source\": \"target_model_inference\",\n    \"missing_dut_weight_binding_is_not_a_pass\": true,\n    \"random_input_is_reproducible\": true,\n    \"real_model_reference_required\": true,\n    \"rtl_output_is_never_used_as_golden\": true,\n    \"testbench_must_bind_real_weights_to_dut\": true\n  },\n  \"random_input\": {\n    \"distribution\": \"torch.randn\",\n    \"dtype\": \"torch.float32\",\n    \"file_sha256\": \"7e924feb776b92cca7944e3eb597b77855e1941ab8619ca82868b20e1d107988\",\n    \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/random_hidden_input.pt\",\n    \"seed\": 20260710,\n    \"shape\": [\n      1,\n      16,\n      896\n    ],\n    \"source\": \"random\",\n    \"tensor_sha256\": \"cb97407804fc13ad730f43b3e43cbf53a50da506b6fb98aa099d37bd1ade1342\"\n  },\n  \"real_weight_source\": {\n    \"accelerator_scope\": \"transformer_blocks_only\",\n    \"accelerator_scope_tensor_count\": 288,\n    \"accelerator_weight_catalog\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_weights/transformer_block_weight_catalog.json\",\n    \"accelerator_weight_catalog_sha256\": \"6eedf4eaf8e41a1df79a8fc121e386cc4cf35e53af887227779c50466cc4f2ca\",\n    \"layer_0_tensor_bindings\": [\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"e0345edd0769263df1d6e69f29d4c54c5bfaa192d5aa9c04697d0fdecd82a4fc\",\n        \"parameter_suffix\": \"self_attn.q_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_q_proj_weight.pt\",\n        \"sha256\": \"9041b6bc4fd8fb547bdf05fe60dbda1e424008019e4ef258c7ce16651aa97454\",\n        \"shape\": [\n          896,\n          896\n        ],\n        \"source_data_offsets\": [\n          300258816,\n          301864448\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"a515fc5f05e4cc898596d09bfcec7a04e8329dd88d1b9c1672af0f2f89b05028\",\n        \"tensor\": \"model.layers.0.self_attn.q_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"a83578d1f5d373392e15f9ea94b3073fae6038f6f3249c3cf082b0697db50093\",\n        \"parameter_suffix\": \"self_attn.q_proj.bias\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_q_proj_bias.pt\",\n        \"sha256\": \"1c3ae6b0c5c0c525224ae50949b8b3adb7b8a2d67fff0382e7c34d6dfdaa2ce2\",\n        \"shape\": [\n          896\n        ],\n        \"source_data_offsets\": [\n          300257024,\n          300258816\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"a7f1f3b0d91c595e9d81b7d9ebff9e3519786fb0741a9e1ea864082ffb403761\",\n        \"tensor\": \"model.layers.0.self_attn.q_proj.bias\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"4caa5339f7d83a2f1c11c8f5d3dade24e5d54134368207b5fabea48516aec373\",\n        \"parameter_suffix\": \"self_attn.k_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_k_proj_weight.pt\",\n        \"sha256\": \"ae588034f9c377f606b1e41d9fd73997b78b1f933f367a7bd39bc61b1edd6d42\",\n        \"shape\": [\n          128,\n          896\n        ],\n        \"source_data_offsets\": [\n          298422016,\n          298651392\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"0d0c2e986b79337c0af626b4696e2c5bfdbfea3ae899aad066b1224706b7e875\",\n        \"tensor\": \"model.layers.0.self_attn.k_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"5dc5e67f8ae3abed3c9aea1c514d9986ba5be64b5614a0b0594440781dbe4c15\",\n        \"parameter_suffix\": \"self_attn.k_proj.bias\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_k_proj_bias.pt\",\n        \"sha256\": \"42cd4d696ed62cca3fdfe2f9ae60098d58a9ef9aa12785bb87d2138caccaffec\",\n        \"shape\": [\n          128\n        ],\n        \"source_data_offsets\": [\n          298421760,\n          298422016\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"bab918b63853c1da0f0796b6078b5249ad2a37122942ae1aa7d1ac6c06cd8b73\",\n        \"tensor\": \"model.layers.0.self_attn.k_proj.bias\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"78e528c04efee1c439857500d6858b96feec959fb7b48c59b34e0afe18c5af12\",\n        \"parameter_suffix\": \"self_attn.v_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_v_proj_weight.pt\",\n        \"sha256\": \"8a582767a99d9285f66805b711bf64b28d984a9b5ec9c57d3854b57f2c5a6cdf\",\n        \"shape\": [\n          128,\n          896\n        ],\n        \"source_data_offsets\": [\n          301864704,\n          302094080\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"593585723059315bd94fa8e1ece653278448b30e895bc422db5053f6e32e072f\",\n        \"tensor\": \"model.layers.0.self_attn.v_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"497d95e0bfa154e3b2bdc5ab5d2b8677802c3c369eb5f0844f1437771690601c\",\n        \"parameter_suffix\": \"self_attn.v_proj.bias\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_v_proj_bias.pt\",\n        \"sha256\": \"69d7c9d95b964280cd18618f4ca4883732b724e21962fa11b2b9c8552ba5b94c\",\n        \"shape\": [\n          128\n        ],\n        \"source_data_offsets\": [\n          301864448,\n          301864704\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"7299b2470e85c07bead7e0472fa737f7c04821d666a10f261a391eedcacf6cfc\",\n        \"tensor\": \"model.layers.0.self_attn.v_proj.bias\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"9901ff4379a93835f958d6b09066d8d2aabb945bb81ec90e278ee68fe518a1e1\",\n        \"parameter_suffix\": \"self_attn.o_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/self_attn_o_proj_weight.pt\",\n        \"sha256\": \"81021c08cced9f1181adb2ba6b92aa112ec9d0b0aef62f103fce127f5d286188\",\n        \"shape\": [\n          896,\n          896\n        ],\n        \"source_data_offsets\": [\n          298651392,\n          300257024\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"7a311aab27e9aeef0934a1e37021060a03301a372f8b7e0f15a9c221a0c43142\",\n        \"tensor\": \"model.layers.0.self_attn.o_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"19ace5d1df608d94c3d8ac8dfe751ace0f33eb75d88424fd0d36438d7fbed9b2\",\n        \"parameter_suffix\": \"mlp.gate_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/mlp_gate_proj_weight.pt\",\n        \"sha256\": \"a56a082019a9cadc1fc40f79cf1b2653321dd03f53c3a9d1204f770bfbf6349e\",\n        \"shape\": [\n          4864,\n          896\n        ],\n        \"source_data_offsets\": [\n          280987392,\n          289703680\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"1921a2d5bf9e6daa33c6030c52f132c9f8f5ee18527b762a98fcaa442a2b3fc6\",\n        \"tensor\": \"model.layers.0.mlp.gate_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"3027ae3f19f02a6d3779b59da2540434ff67d3e64921d54c9209523b4709ab62\",\n        \"parameter_suffix\": \"mlp.up_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/mlp_up_proj_weight.pt\",\n        \"sha256\": \"2c1ed3ddbfee1ec991624e045f4d24d9b4531eb2cce3a89bc56921602fd86cc8\",\n        \"shape\": [\n          4864,\n          896\n        ],\n        \"source_data_offsets\": [\n          289703680,\n          298419968\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"c439582c80056cff1002ea2a307eb0f28ad3b35618fd93fdef16584e216e3804\",\n        \"tensor\": \"model.layers.0.mlp.up_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"08caadb3239898c1729be9f90986beba8fd1daaa60bff35e8d880766937979e8\",\n        \"parameter_suffix\": \"mlp.down_proj.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/mlp_down_proj_weight.pt\",\n        \"sha256\": \"7c36f7e02b1d84ccb38c91b552d995c4086fe34358a7d8dcb752ffddadb263a8\",\n        \"shape\": [\n          896,\n          4864\n        ],\n        \"source_data_offsets\": [\n          272271104,\n          280987392\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"de65160719848918e6b24ec9172371309fd74f9a9e7497316568f77d581abe51\",\n        \"tensor\": \"model.layers.0.mlp.down_proj.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"1d5bb79c4243dc7463384bc1d9c5a2ae68d56bb0d6ef01997e2ff8f48de68951\",\n        \"parameter_suffix\": \"input_layernorm.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/input_layernorm_weight.pt\",\n        \"sha256\": \"5668398b8ae0b69ebf24d8d1bf05509d8276d3c85be49cfc48a703cda3a91188\",\n        \"shape\": [\n          896\n        ],\n        \"source_data_offsets\": [\n          272269312,\n          272271104\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"bd43be7fb745d3091761ec97647df27bddf63c28007642d1100d577a5139ab81\",\n        \"tensor\": \"model.layers.0.input_layernorm.weight\"\n      },\n      {\n        \"dtype\": \"torch.float32\",\n        \"file_sha256\": \"2cb5e3dc410313eb0dc3a415cbd85246a63ae06c9b5f7a4bd4e7d377fd41be72\",\n        \"parameter_suffix\": \"post_attention_layernorm.weight\",\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/weights/post_attention_layernorm_weight.pt\",\n        \"sha256\": \"19cb555eb19556d256504d9f642f577c84b9ad357205105cf535100688f9c222\",\n        \"shape\": [\n          896\n        ],\n        \"source_data_offsets\": [\n          298419968,\n          298421760\n        ],\n        \"source_dtype\": \"BF16\",\n        \"source_slice_sha256\": \"1fb9fda61dbaaeaa7f69ac5bca11cc5b3998264adead65c8af82ab53a620f545\",\n        \"tensor\": \"model.layers.0.post_attention_layernorm.weight\"\n      }\n    ],\n    \"layer_0_tensor_coverage_complete\": true,\n    \"loaded_by_reference_model\": true,\n    \"real_target_weights\": true,\n    \"source_checkpoint_sha256\": \"b9e6f94c4bbf620f845978ac826142690d666660996f5c1100096ca51427a3cf\",\n    \"source_manifest\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_weights/weight_manifest.json\",\n    \"source_manifest_sha256\": \"7c21e52744e456aa11f89328d36bd07359ff757cefe608076c98e42706887930\"\n  },\n  \"reference_manifest\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/model_reference/reference_manifest.json\",\n  \"reference_manifest_sha256\": \"3d3aab3a74ccc0b4efa744570e3486aed39941b21e8ca1ae938ce32d50351d27\",\n  \"run_dir\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run\",\n  \"schema_version\": \"spatialaccagent.semantic_testbench_manifest.v1\",\n  \"single_layer\": {\n    \"blockers\": [],\n    \"dut_harness\": {\n      \"consumed_tensor_hashes\": [\n        \"19cb555eb19556d256504d9f642f577c84b9ad357205105cf535100688f9c222\",\n        \"1c3ae6b0c5c0c525224ae50949b8b3adb7b8a2d67fff0382e7c34d6dfdaa2ce2\",\n        \"2c1ed3ddbfee1ec991624e045f4d24d9b4531eb2cce3a89bc56921602fd86cc8\",\n        \"42cd4d696ed62cca3fdfe2f9ae60098d58a9ef9aa12785bb87d2138caccaffec\",\n        \"5668398b8ae0b69ebf24d8d1bf05509d8276d3c85be49cfc48a703cda3a91188\",\n        \"69d7c9d95b964280cd18618f4ca4883732b724e21962fa11b2b9c8552ba5b94c\",\n        \"7c36f7e02b1d84ccb38c91b552d995c4086fe34358a7d8dcb752ffddadb263a8\",\n        \"81021c08cced9f1181adb2ba6b92aa112ec9d0b0aef62f103fce127f5d286188\",\n        \"8a582767a99d9285f66805b711bf64b28d984a9b5ec9c57d3854b57f2c5a6cdf\",\n        \"9041b6bc4fd8fb547bdf05fe60dbda1e424008019e4ef258c7ce16651aa97454\",\n        \"a56a082019a9cadc1fc40f79cf1b2653321dd03f53c3a9d1204f770bfbf6349e\",\n        \"ae588034f9c377f606b1e41d9fd73997b78b1f933f367a7bd39bc61b1edd6d42\"\n      ],\n      \"loader_route_contract\": {\n        \"runtime_routes\": [\n          {\n            \"dut_port\": \"core.io.ropeRuntime\",\n            \"global_stream_range\": {\n              \"word_count\": 1056,\n              \"word_end_exclusive\": 1056,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_01_self_attention\",\n            \"target_ids\": [\n              \"attention.position_ids\",\n              \"attention.cache_position\",\n              \"attention.rope.cos_table\",\n              \"attention.rope.sin_table\"\n            ]\n          }\n        ],\n        \"weight_routes\": [\n          {\n            \"dut_port\": \"core.io.rms1Weight\",\n            \"dut_port_role\": \"weight\",\n            \"global_stream_range\": {\n              \"word_count\": 896,\n              \"word_end_exclusive\": 896,\n              \"word_offset\": 0\n            },\n            \"local_stream_range\": {\n              \"word_count\": 896,\n              \"word_end_exclusive\": 896,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_00_rms_norm_1\",\n            \"target_id\": \"norm.scale\"\n          },\n          {\n            \"dut_port\": \"core.io.qkvWeight\",\n            \"dut_port_role\": \"qkv_weight\",\n            \"global_stream_range\": {\n              \"word_count\": 516096,\n              \"word_end_exclusive\": 516992,\n              \"word_offset\": 896\n            },\n            \"local_stream_range\": {\n              \"word_count\": 516096,\n              \"word_end_exclusive\": 516096,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_01_self_attention\",\n            \"target_id\": \"attention.qkv.weight\"\n          },\n          {\n            \"dut_port\": \"core.io.qkvBias\",\n            \"dut_port_role\": \"qkv_bias\",\n            \"global_stream_range\": {\n              \"word_count\": 1152,\n              \"word_end_exclusive\": 518144,\n              \"word_offset\": 516992\n            },\n            \"local_stream_range\": {\n              \"word_count\": 1152,\n              \"word_end_exclusive\": 517248,\n              \"word_offset\": 516096\n            },\n            \"stage_id\": \"stage_01_self_attention\",\n            \"target_id\": \"attention.qkv.bias\"\n          },\n          {\n            \"dut_port\": \"core.io.attentionOutWeight\",\n            \"dut_port_role\": \"out_proj_weight\",\n            \"global_stream_range\": {\n              \"word_count\": 401408,\n              \"word_end_exclusive\": 919552,\n              \"word_offset\": 518144\n            },\n            \"local_stream_range\": {\n              \"word_count\": 401408,\n              \"word_end_exclusive\": 918656,\n              \"word_offset\": 517248\n            },\n            \"stage_id\": \"stage_01_self_attention\",\n            \"target_id\": \"attention.out_proj.weight\"\n          },\n          {\n            \"dut_port\": \"core.io.rms2Weight\",\n            \"dut_port_role\": \"weight\",\n            \"global_stream_range\": {\n              \"word_count\": 896,\n              \"word_end_exclusive\": 920448,\n              \"word_offset\": 919552\n            },\n            \"local_stream_range\": {\n              \"word_count\": 896,\n              \"word_end_exclusive\": 896,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_03_rms_norm_2\",\n            \"target_id\": \"norm.scale\"\n          },\n          {\n            \"dut_port\": \"core.io.mlpGateWeight\",\n            \"dut_port_role\": \"weight\",\n            \"global_stream_range\": {\n              \"word_count\": 2179072,\n              \"word_end_exclusive\": 3099520,\n              \"word_offset\": 920448\n            },\n            \"local_stream_range\": {\n              \"word_count\": 2179072,\n              \"word_end_exclusive\": 2179072,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_04_mlp_gate_proj\",\n            \"target_id\": \"linear.weight\"\n          },\n          {\n            \"dut_port\": \"core.io.mlpUpWeight\",\n            \"dut_port_role\": \"weight\",\n            \"global_stream_range\": {\n              \"word_count\": 2179072,\n              \"word_end_exclusive\": 5278592,\n              \"word_offset\": 3099520\n            },\n            \"local_stream_range\": {\n              \"word_count\": 2179072,\n              \"word_end_exclusive\": 2179072,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_05_mlp_up_proj\",\n            \"target_id\": \"linear.weight\"\n          },\n          {\n            \"dut_port\": \"core.io.mlpDownWeight\",\n            \"dut_port_role\": \"weight\",\n            \"global_stream_range\": {\n              \"word_count\": 2179072,\n              \"word_end_exclusive\": 7457664,\n              \"word_offset\": 5278592\n            },\n            \"local_stream_range\": {\n              \"word_count\": 2179072,\n              \"word_end_exclusive\": 2179072,\n              \"word_offset\": 0\n            },\n            \"stage_id\": \"stage_07_mlp_down_proj\",\n            \"target_id\": \"linear.weight\"\n          }\n        ]\n      },\n      \"pipeline_overlap_trace_contract_sha256\": \"89a737769d2a1ca0b12b67b87683e9a590f5ef8ac3ec718cc1664d881410d734\",\n      \"source_files\": [\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Activation.sv\",\n          \"sha256\": \"793c663cab4c2493162488412d09d8669b0e4b45d77762f42111426df7f4ae87\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/AddRawFN.sv\",\n          \"sha256\": \"b6e7401e9ba54fe74c47b198f263ad1e115d1a7444d521fbfa83a8fe99b6e7bf\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/AddRecFN.sv\",\n          \"sha256\": \"e30b913a4fcbf712e386b7f75bf998cc3a599c74f6fd654348fd74d302c0cdd8\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/AttentionGQA.sv\",\n          \"sha256\": \"ce2ed5a48d6925e42bd44902bb683221ee384c72e2bf154b7b8a46514da1eec6\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/CompareRecFN.sv\",\n          \"sha256\": \"814f90c0d54776d0a7467ed57024e602e6948906f34a565cc13ccb2bcd46423d\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker.sv\",\n          \"sha256\": \"549dfbf4d406e11319ab5f89e701d58d130ed0e482cc08b4b2eef07546eac403\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_1.sv\",\n          \"sha256\": \"02ed8639f6abfaa9a0aa6ce9ec6afdf6b1f1126dc403f8e4cff5162a7b2c1b90\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_2.sv\",\n          \"sha256\": \"0e59ca9664473372ade613dd451417bb4fcd862f86683fc98227e9445596b686\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_3.sv\",\n          \"sha256\": \"f3881db8398053705739995ce318ce116318635709dc855fde82d8b457466938\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_5.sv\",\n          \"sha256\": \"c7867a9c5dc80117da1261a572ff467068d1b806cfb5cd9e819d886975699e82\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedObservableLlamaStyleBlock.sv\",\n          \"sha256\": \"8fd424d8888845b03df61dd919a6d2b75eee12a2842493215a0d82a4ba129eca\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedStreamIngress.sv\",\n          \"sha256\": \"586749abab288c0a6bc4a3269dcde73c2a7db2f9a32c463559aac7cd897d47b5\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedWeightLoader.sv\",\n          \"sha256\": \"31c41e3b52b51e0e8c6cea4eaba88f0216057b4285ebb55226aa7afff41ab9f7\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/DivSqrtRawFN_small_e8_s24.sv\",\n          \"sha256\": \"36544e04d9b73705c77a2a07a04bba3b6435a91bf3185ce5f0f5510c664ee2fb\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/DivSqrtRecFMToRaw_small_e8_s24.sv\",\n          \"sha256\": \"e7082c31ca17c857b913e4440a573797d5e1d4f671af5a856c92fe23dfed0a8b\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/DivSqrtRecFM_small_e8_s24.sv\",\n          \"sha256\": \"d6c5273532b22e2e1f2e246ef16999b3462919d48242ab0c91cddb29452c2f26\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ElementwiseMul.sv\",\n          \"sha256\": \"77cabc8da03822284ac4c72669504b99bb646a7912694ed7e84e5a67d2781c53\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/GatedMLP.sv\",\n          \"sha256\": \"56e31c169ad809b7b487c638d5a95e136fe9135db5c0617e4a2af651dcf8c8a5\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/INToRecFN_i25_e8_s24.sv\",\n          \"sha256\": \"8ecf314ffd508688bea7b88f1d5dec87ae66764b54983b4e531532ab22887ee7\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/INToRecFN_i36_e8_s24.sv\",\n          \"sha256\": \"38e37b277c02a7655e91e60f6e64eb83eaab5db59b9fd64c9442e0a427e1b953\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear.sv\",\n          \"sha256\": \"9912819dd3fae37e2f94a196a59eacff3601d1f360d79672af48914282098105\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_1.sv\",\n          \"sha256\": \"c7f97e407c087a90821ce94b46aeca669058e0b362a086918143950147fbc5be\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_2.sv\",\n          \"sha256\": \"2a0b231d4e1c64ddebe553bd0d65a51c457204de6865b36665b13a7cbbbc9f76\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_3.sv\",\n          \"sha256\": \"1c26ca4ff12f9522686874998bf996a19ae0edfeb22c3f1bc9908dde1b4c814b\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_4.sv\",\n          \"sha256\": \"0c835c2614fb651a634f13a054172bb84039f90089c3b25eacf8c6e790195d87\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/MulFullRawFN.sv\",\n          \"sha256\": \"36d990d3717ff7a005ea750c8e414b17ed53fa62eaf7ea7b4d73538864ee2a5c\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/MulRawFN.sv\",\n          \"sha256\": \"4649532c4e1e62ea6fd7c8f0f526fe647c474342292c163ac9482b52ebce4266\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/MulRecFN.sv\",\n          \"sha256\": \"14615abf8650a1fe3afd33fcc9d34bbf40bd5cca366fc1a5ebe80012ed2b940f\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/QKVProjection.sv\",\n          \"sha256\": \"bc6c3a1512b4cdcc1afd366c793ae0caed74df1169dd56627346a9b6aa0d7d6c\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue1792_StreamBeat.sv\",\n          \"sha256\": \"7a39b4cde2aca272f39401e6edc0ccb0a10b1e59e173222937cdeb9d617e4e27\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue1792_StreamBeat_4.sv\",\n          \"sha256\": \"7e1a736e44e6c4eecc38a842485e8b9ae30c4a7f2048c54198d8929efd8702ea\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue2_StreamBeat.sv\",\n          \"sha256\": \"93d84deb44695ccda8a0e4bab6643698e57c200e4152a78c7e27673fff7d8877\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue2_StreamBeat_1.sv\",\n          \"sha256\": \"b7627d43fcf3d9680981077cfebfb08e7987b6f06cbf282c2802070a59609eba\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue4_StreamBeat.sv\",\n          \"sha256\": \"6283b71b5dd93db2832b7e44c9095c4700bdf75e3b5a214213d37130af4b27d2\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue4_StreamBeat_2.sv\",\n          \"sha256\": \"fff321245d139c9aa2b69a196a3e0f66a667cffe1be5f5dd23fa61c446c4124e\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RMSNorm.sv\",\n          \"sha256\": \"c337024af70fe2245daac243fa8067d0edebba9395cbaed2e18ba7ce55c1f76f\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RecFNToIN_e8_s24_i16.sv\",\n          \"sha256\": \"9ccc10c190e7c66368e55ed7d8e5ca911544a7f94472c80f2a978557ade0da97\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RecFNToRecFN.sv\",\n          \"sha256\": \"0b393161c147493fc22d7d23ea76ddf54303fb55e6b533c7d2229ae333814dbd\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RecFNToRecFN_8.sv\",\n          \"sha256\": \"4a81f71c5e3e869441984db732846d139d84ee320975a17693582f26773e8d02\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ResidualAdd.sv\",\n          \"sha256\": \"27afb6987ac2a3eb2e1c3eaa4dc54fbefe2b08785ac76629abba8dfa15faccfc\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoPE.sv\",\n          \"sha256\": \"4523c49935ae674e3f27555446c88ff9e334631ec11241aa87a26336ff381ace\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie5_is11_oe8_os24.sv\",\n          \"sha256\": \"f16ba7437f6426cc64c30655a536bc3384d8d6033c763033da9db006b6824e5f\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie6_is25_oe8_os24.sv\",\n          \"sha256\": \"4ce4890e9101c62e1d41d60e49a79781406113d57b8fad9ea243442784cec8c1\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie7_is36_oe8_os24.sv\",\n          \"sha256\": \"0140f3ba6a856368b04c98ca1b07df893f5215d16c6f717cc9012ac88ca86564\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie8_is24_oe5_os11.sv\",\n          \"sha256\": \"67371697419228666ffb2c6e75ec7adfb89546dced4bc47e26556f84b72d505b\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie8_is26_oe8_os24.sv\",\n          \"sha256\": \"13dc26d729b5db6d3030668114ec817e1425776ac40d89f0a3a0b601a1fe7d09\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundRawFNToRecFN_e8_s24.sv\",\n          \"sha256\": \"d62b861bbdf6aa5840a22fcdfa4da770324828eefabe690741ae6c3c08c7dbae\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/SingleLayerSemanticHarness.sv\",\n          \"sha256\": \"dbfb0e992ff81f9bb6e541e131ef4c90ac22ef89e9e3c053b20917d1b982f046\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Softmax.sv\",\n          \"sha256\": \"60495b714b32137ea1e826d48b37920e93eecc3106e1706a75b061ea99c4a4f9\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/VectorNorm.sv\",\n          \"sha256\": \"041b2747a0e21a65e1d8d14e32c426399895e7276c2a6471e2194ea4462d8248\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/expTable_2048x26.sv\",\n          \"sha256\": \"4c1c4e82a212507a3237116336e503de9d5995f2c8406bad627564b0ac70bb2e\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_1792x256.sv\",\n          \"sha256\": \"3f248758619c7e2430d0ec99c72ae09583436690c9f9ca5debea7a39c5bc3e2b\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_1792x269.sv\",\n          \"sha256\": \"562edada758e0bdf138d6fe16cfe653cb1b9e42961166782f6310b275effbd91\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_1792x269_0.sv\",\n          \"sha256\": \"5f70c1f5412f5bc6b387943004e4b713d58256cfd129d53c00ae5674695720f9\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_2x144.sv\",\n          \"sha256\": \"2e4a6ca180b7989c5c15a1a0e3d644fa4d868a19a0b4afc054294fc9b5bce252\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_2x269.sv\",\n          \"sha256\": \"14ed4e7f18671d70dfa65f5f70b287b203e8a948ee57165fc3109ff05f504c4b\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_4x144.sv\",\n          \"sha256\": \"14549c6d0d0411b1c3d6cf460c7c609d660233bf910654bcf62d12bd782fbf20\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/sigmoidTable_129x19.sv\",\n          \"sha256\": \"18642537333ecc6cf91b893c51593a96bb54bda35251eda1e6fef4e6f941126c\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/ConnectedObservableLlamaStyleBlock_Verification.sv\",\n          \"sha256\": \"1295b1eccfd57a745800a850e0830c875879396b8aea0772bac5edbcf95da25e\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/assert/layers-SingleLayerSemanticHarness-Verification-Assert.sv\",\n          \"sha256\": \"9f6f7cd74bfb7999e3f6865e3f54b6f9d4a9e50f78086e10e13c8b430fde88ef\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/assume/layers-SingleLayerSemanticHarness-Verification-Assume.sv\",\n          \"sha256\": \"fda2ea5872b1567ed437fb983669655807a550d749469f0f71c20bb58761a584\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/cover/layers-SingleLayerSemanticHarness-Verification-Cover.sv\",\n          \"sha256\": \"14f9fb972e98522ec6768fdb0cab39522ddc9475ccfdeff06710c6d6224046cb\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/layers-ConnectedObservableLlamaStyleBlock-Verification.sv\",\n          \"sha256\": \"6c89abc693126950194a70327fe36a37c1dcd46c4a5eab33b59ccb13c83700ae\"\n        },\n        {\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/layers-SingleLayerSemanticHarness-Verification.sv\",\n          \"sha256\": \"d3e25305dc97cddde8113e4e88c43cd676abc3343523d0692d25911e2ff49f01\"\n        }\n      ],\n      \"top_module\": \"SingleLayerSemanticHarness\"\n    },\n    \"expected_output\": {\n      \"beats\": 1792,\n      \"bits\": 32,\n      \"encoding\": \"ieee_fp32_lane0_lsb\",\n      \"lanes\": 8,\n      \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/expected.memh\",\n      \"sha256\": \"92fc53de80c8caca6ea04cc69ab768a1f6db0e55a2ab0ebbd9ac0adc6e3c85b4\",\n      \"tensor_shape\": [\n        1,\n        16,\n        896\n      ]\n    },\n    \"input_vector\": {\n      \"beats\": 1792,\n      \"bits\": 32,\n      \"encoding\": \"ieee_fp32_lane0_lsb\",\n      \"lanes\": 8,\n      \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/input.memh\",\n      \"sha256\": \"5a15ee2ffa863277c10b78150cf0e23955b8555fdc989379bce4d7df2a074545\",\n      \"tensor_shape\": [\n        1,\n        16,\n        896\n      ]\n    },\n    \"input_vectors\": [\n      {\n        \"beats\": 1792,\n        \"bits\": 32,\n        \"encoding\": \"ieee_fp32_lane0_lsb\",\n        \"lanes\": 8,\n        \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/input.memh\",\n        \"sha256\": \"5a15ee2ffa863277c10b78150cf0e23955b8555fdc989379bce4d7df2a074545\",\n        \"tensor_shape\": [\n          1,\n          16,\n          896\n        ]\n      }\n    ],\n    \"pipeline_overlap_contract\": {\n      \"acceptance\": {\n        \"all_planned_spatial_stages_are_concurrently_active_after_fill\": true,\n        \"all_required_records_are_accepted_transfers\": true,\n        \"every_adjacent_stage_pair_overlaps_on_different_tokens\": true,\n        \"every_stage_emits_token_0_before_accepting_the_final_token\": true,\n        \"every_token_has_first_and_last_record_at_each_required_boundary\": true,\n        \"maximum_next_token_stage_entry_gap_cycles\": 1,\n        \"minimum_concurrent_stage_count\": 9,\n        \"whole_sequence_barrier_forbidden\": true\n      },\n      \"beats_per_token\": 112,\n      \"block_input_boundaries\": [\n        \"edge.data.block_input.to.stage_00_rms_norm_1.input\",\n        \"edge.data.block_input.to.stage_02_residual_add_1.residual_skip\"\n      ],\n      \"block_output_boundary\": \"edge.data.stage_08_residual_add_2.to.block_output.output\",\n      \"boundary_contracts\": [\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.block_input.to.stage_00_rms_norm_1.input\",\n          \"dst_stage\": \"stage_00_rms_norm_1\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"input\",\n          \"src_stage\": \"block_input\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.block_input.to.stage_02_residual_add_1.residual_skip\",\n          \"dst_stage\": \"stage_02_residual_add_1\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"residual_skip\",\n          \"src_stage\": \"block_input\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main\",\n          \"dst_stage\": \"stage_01_self_attention\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"main\",\n          \"src_stage\": \"stage_00_rms_norm_1\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main\",\n          \"dst_stage\": \"stage_02_residual_add_1\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"main\",\n          \"src_stage\": \"stage_01_self_attention\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main\",\n          \"dst_stage\": \"stage_03_rms_norm_2\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"main\",\n          \"src_stage\": \"stage_02_residual_add_1\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\",\n          \"dst_stage\": \"stage_08_residual_add_2\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"residual_skip\",\n          \"src_stage\": \"stage_02_residual_add_1\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch\",\n          \"dst_stage\": \"stage_04_mlp_gate_proj\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"mlp_gate_branch\",\n          \"src_stage\": \"stage_03_rms_norm_2\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch\",\n          \"dst_stage\": \"stage_05_mlp_up_proj\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"mlp_up_branch\",\n          \"src_stage\": \"stage_03_rms_norm_2\"\n        },\n        {\n          \"beats_per_token\": 608,\n          \"boundary_id\": \"edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul\",\n          \"dst_stage\": \"stage_06_activation_mul\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"mlp_gate_to_mul\",\n          \"src_stage\": \"stage_04_mlp_gate_proj\"\n        },\n        {\n          \"beats_per_token\": 608,\n          \"boundary_id\": \"edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul\",\n          \"dst_stage\": \"stage_06_activation_mul\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"mlp_up_to_mul\",\n          \"src_stage\": \"stage_05_mlp_up_proj\"\n        },\n        {\n          \"beats_per_token\": 608,\n          \"boundary_id\": \"edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main\",\n          \"dst_stage\": \"stage_07_mlp_down_proj\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"main\",\n          \"src_stage\": \"stage_06_activation_mul\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main\",\n          \"dst_stage\": \"stage_08_residual_add_2\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"main\",\n          \"src_stage\": \"stage_07_mlp_down_proj\"\n        },\n        {\n          \"beats_per_token\": 112,\n          \"boundary_id\": \"edge.data.stage_08_residual_add_2.to.block_output.output\",\n          \"dst_stage\": \"block_output\",\n          \"flow_control\": \"ready_valid\",\n          \"kind\": \"output\",\n          \"src_stage\": \"stage_08_residual_add_2\"\n        }\n      ],\n      \"contract_sha256\": \"89a737769d2a1ca0b12b67b87683e9a590f5ef8ac3ec718cc1664d881410d734\",\n      \"dependency_edges\": [\n        {\n          \"boundary_id\": \"edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main\",\n          \"dst_stage\": \"stage_01_self_attention\",\n          \"src_stage\": \"stage_00_rms_norm_1\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main\",\n          \"dst_stage\": \"stage_02_residual_add_1\",\n          \"src_stage\": \"stage_01_self_attention\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main\",\n          \"dst_stage\": \"stage_03_rms_norm_2\",\n          \"src_stage\": \"stage_02_residual_add_1\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\",\n          \"dst_stage\": \"stage_08_residual_add_2\",\n          \"src_stage\": \"stage_02_residual_add_1\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch\",\n          \"dst_stage\": \"stage_04_mlp_gate_proj\",\n          \"src_stage\": \"stage_03_rms_norm_2\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch\",\n          \"dst_stage\": \"stage_05_mlp_up_proj\",\n          \"src_stage\": \"stage_03_rms_norm_2\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul\",\n          \"dst_stage\": \"stage_06_activation_mul\",\n          \"src_stage\": \"stage_04_mlp_gate_proj\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul\",\n          \"dst_stage\": \"stage_06_activation_mul\",\n          \"src_stage\": \"stage_05_mlp_up_proj\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main\",\n          \"dst_stage\": \"stage_07_mlp_down_proj\",\n          \"src_stage\": \"stage_06_activation_mul\"\n        },\n        {\n          \"boundary_id\": \"edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main\",\n          \"dst_stage\": \"stage_08_residual_add_2\",\n          \"src_stage\": \"stage_07_mlp_down_proj\"\n        }\n      ],\n      \"pipeline_plan_sha256\": \"3f7e4ee52cb8b1cdf539d6392019684d546c505579f4a002108986519b2d6b33\",\n      \"planned_stage_count\": 9,\n      \"policy\": {\n        \"layer_level_overlap_cannot_substitute_for_intra_layer_operator_overlap\": true,\n        \"stage_activity_is_derived_from_actual_module_port_handshakes\": true,\n        \"trace_is_observation_only\": true,\n        \"trace_must_not_change_ready_valid_or_data\": true,\n        \"transaction_counts_alone_cannot_prove_pipeline_overlap\": true\n      },\n      \"required_boundaries\": [\n        \"edge.data.block_input.to.stage_00_rms_norm_1.input\",\n        \"edge.data.block_input.to.stage_02_residual_add_1.residual_skip\",\n        \"edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main\",\n        \"edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main\",\n        \"edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main\",\n        \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\",\n        \"edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch\",\n        \"edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch\",\n        \"edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul\",\n        \"edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul\",\n        \"edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main\",\n        \"edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main\",\n        \"edge.data.stage_08_residual_add_2.to.block_output.output\"\n      ],\n      \"schema_version\": \"spatialaccagent.single_layer_pipeline_overlap_contract.v2\",\n      \"stage_activity_contracts\": [\n        {\n          \"input_boundaries\": [\n            \"edge.data.block_input.to.stage_00_rms_norm_1.input\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main\"\n          ],\n          \"stage_id\": \"stage_00_rms_norm_1\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main\"\n          ],\n          \"stage_id\": \"stage_01_self_attention\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.block_input.to.stage_02_residual_add_1.residual_skip\",\n            \"edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main\",\n            \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\"\n          ],\n          \"stage_id\": \"stage_02_residual_add_1\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch\",\n            \"edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch\"\n          ],\n          \"stage_id\": \"stage_03_rms_norm_2\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul\"\n          ],\n          \"stage_id\": \"stage_04_mlp_gate_proj\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul\"\n          ],\n          \"stage_id\": \"stage_05_mlp_up_proj\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul\",\n            \"edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main\"\n          ],\n          \"stage_id\": \"stage_06_activation_mul\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main\"\n          ],\n          \"stage_id\": \"stage_07_mlp_down_proj\"\n        },\n        {\n          \"input_boundaries\": [\n            \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\",\n            \"edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main\"\n          ],\n          \"output_boundaries\": [\n            \"edge.data.stage_08_residual_add_2.to.block_output.output\"\n          ],\n          \"stage_id\": \"stage_08_residual_add_2\"\n        }\n      ],\n      \"stage_order\": [\n        \"stage_00_rms_norm_1\",\n        \"stage_01_self_attention\",\n        \"stage_02_residual_add_1\",\n        \"stage_03_rms_norm_2\",\n        \"stage_04_mlp_gate_proj\",\n        \"stage_05_mlp_up_proj\",\n        \"stage_06_activation_mul\",\n        \"stage_07_mlp_down_proj\",\n        \"stage_08_residual_add_2\"\n      ],\n      \"token_count\": 16,\n      \"trace_abi\": \"SPATIALACC_PIPELINE_TRACE boundary=<id> cycle=<decimal> token=<decimal> beat=<decimal> st=<0_or_1> last=<0_or_1> valid=<0_or_1> ready=<0_or_1>\"\n    },\n    \"pipeline_plan_sha256\": \"3f7e4ee52cb8b1cdf539d6392019684d546c505579f4a002108986519b2d6b33\",\n    \"real_weight_binding_manifest\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json\",\n    \"real_weight_binding_verified\": true,\n    \"real_weight_stream\": {\n      \"contract_sha256\": \"7bca29f0705564352126bd5286813530bb06f99cae3021e183a1d0d432050672\",\n      \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/real_weights.u32.memh\",\n      \"schema_version\": \"spatialaccagent.composite_weight_stream.v1\",\n      \"sha256\": \"7c7f041a8c026f1a690fe5cec0706b079cd0d390bc84242699e3b686b5b98db7\",\n      \"status\": \"pass\",\n      \"word_bits\": 32,\n      \"word_count\": 7457664\n    },\n    \"rtl_output_capture\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/rtl_output.memh\",\n    \"runtime_constant_stream\": {\n      \"contract_sha256\": \"aeb984f8408fdcab7cefc7e78e1eb22b2edfb0c4b38f6642fdd319a1d9930de5\",\n      \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/runtime_constants.u32.memh\",\n      \"schema_version\": \"spatialaccagent.composite_runtime_stream.v1\",\n      \"sha256\": \"8167a8e8ad6ae244f89a9014b5ca0a0109fb868fc331ab03855c7bcf9fa73367\",\n      \"status\": \"pass\",\n      \"word_bits\": 32,\n      \"word_count\": 1056\n    },\n    \"status\": \"ready\",\n    \"testbench\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/single_layer_real_model_tb.sv\",\n    \"testbench_sha256\": \"23e4ece8a709c15f5b1e263deab4b9ef0272c261739abbf7cfa6b343be518db0\"\n  },\n  \"stage_contracts\": [\n    {\n      \"op\": \"rms_norm_1\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_00_rms_norm_1\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"bed05541eee20296e1a1ba8ba5693efbeb760ea55d16b97b30ae564861da35dc\"\n    },\n    {\n      \"op\": \"self_attention\",\n      \"runtime_constant_contract_sha256\": \"b343fafa1e53f302386281b463e9fff3ec1acde2cdab89b95454a6e8109ca34e\",\n      \"stage_id\": \"stage_01_self_attention\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"89d0578fb6b7e62dc45ceed52d6ef19372205716b51c06693012f41cdda55703\"\n    },\n    {\n      \"op\": \"residual_add_1\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_02_residual_add_1\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"45d393f6a6f267ca3f5f6ffac4a95e0b6ce622492229af41638e1404cfc1a9b2\"\n    },\n    {\n      \"op\": \"rms_norm_2\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_03_rms_norm_2\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"ebb61948847bedb86e635a7169b6cc2566c8dfdabc5d8d0cf94764b4d2f728f6\"\n    },\n    {\n      \"op\": \"mlp_gate_proj\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_04_mlp_gate_proj\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"9e8b5f4ad88325c1089419d8f35b4438170706a4d56bdb90eba621b0a27e4710\"\n    },\n    {\n      \"op\": \"mlp_up_proj\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_05_mlp_up_proj\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"3ddc94f0dc332fdd9479737bb5710b1e9baa0d75e6d9420694cde21aaaf84525\"\n    },\n    {\n      \"op\": \"activation_mul\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_06_activation_mul\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"aea5d30d80fa818194cc0531014bcfd1d24f8583debd5433ed2516c9477db9a9\"\n    },\n    {\n      \"op\": \"mlp_down_proj\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_07_mlp_down_proj\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"08f59cd885c7b7c1c086e282a1418c0c7a7b7ab036acdd89f0895252a524986a\"\n    },\n    {\n      \"op\": \"residual_add_2\",\n      \"runtime_constant_contract_sha256\": null,\n      \"stage_id\": \"stage_08_residual_add_2\",\n      \"status\": \"reused_lower_layer_certificate\",\n      \"weight_layout_contract_sha256\": \"6bd88b2cebc29799df9541e506e883cd78f66028b2bf09ef2388a672f0f1c33b\"\n    }\n  ],\n  \"status\": \"ready\"\n}",
        "content_sha256": "fc5a0dd8dc5ed77cd33c225653d7468b4917203e5717137f3049ea4a7c75d28e",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json#single_layer_closure_execution_projection",
        "projection": true,
        "source_path": "accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
        "source_sha256": "6447ebfdb0934c917eb35e2ab80d77fd2cf536c008f95667f98673d70f66bb84",
        "truncated": false
      },
      {
        "bytes": 116077,
        "content": "{\n  \"input_vector\": {\n    \"beats\": 1792,\n    \"bits\": 32,\n    \"encoding\": \"ieee_fp32_lane0_lsb\",\n    \"lanes\": 8,\n    \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/input.memh\",\n    \"sha256\": \"5a15ee2ffa863277c10b78150cf0e23955b8555fdc989379bce4d7df2a074545\",\n    \"tensor_shape\": [\n      1,\n      16,\n      896\n    ]\n  },\n  \"output_memh\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/rtl_output.memh\",\n  \"output_sha256\": \"4441348a14de7c9516ed00e2a4cacd895ae1cda50a0cedf94757dcbddb30e23e\",\n  \"pipeline_overlap_evidence\": {\n    \"accepted_trace_record_count\": 416,\n    \"blockers\": [\n      \"adjacent stages stage_02_residual_add_1 -> stage_08_residual_add_2 never operate on different tokens concurrently\"\n    ],\n    \"contract_sha256\": \"89a737769d2a1ca0b12b67b87683e9a590f5ef8ac3ec718cc1664d881410d734\",\n    \"dependency_overlap_evidence\": [\n      {\n        \"boundary_id\": \"edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_01_self_attention\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7697872,\n            \"overlap_start_cycle\": 7681345,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7714400,\n            \"overlap_start_cycle\": 7697873,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 7730928,\n            \"overlap_start_cycle\": 7714401,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 7747456,\n            \"overlap_start_cycle\": 7730929,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 7763984,\n            \"overlap_start_cycle\": 7747457,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 7780512,\n            \"overlap_start_cycle\": 7763985,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 7797040,\n            \"overlap_start_cycle\": 7780513,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 7813568,\n            \"overlap_start_cycle\": 7797041,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_02_residual_add_1\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7731073,\n            \"overlap_start_cycle\": 7714543,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7747601,\n            \"overlap_start_cycle\": 7731071,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 7765903,\n            \"overlap_start_cycle\": 7747599,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 7782431,\n            \"overlap_start_cycle\": 7764127,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 7798959,\n            \"overlap_start_cycle\": 7780655,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 7815487,\n            \"overlap_start_cycle\": 7797183,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 7832015,\n            \"overlap_start_cycle\": 7813711,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 7848543,\n            \"overlap_start_cycle\": 7830239,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_01_self_attention\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_03_rms_norm_2\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7731239,\n            \"overlap_start_cycle\": 7731071,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7800663,\n            \"overlap_start_cycle\": 7747599,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 7937272,\n            \"overlap_start_cycle\": 7800664,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8073881,\n            \"overlap_start_cycle\": 7937273,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8210490,\n            \"overlap_start_cycle\": 8073882,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8347099,\n            \"overlap_start_cycle\": 8210491,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8483708,\n            \"overlap_start_cycle\": 8347100,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8620317,\n            \"overlap_start_cycle\": 8483709,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\",\n        \"different_token_overlap_observed\": false,\n        \"dst_stage\": \"stage_08_residual_add_2\",\n        \"overlaps\": [],\n        \"src_stage\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_04_mlp_gate_proj\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7800551,\n            \"overlap_start_cycle\": 7731240,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7937160,\n            \"overlap_start_cycle\": 7800664,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 8073769,\n            \"overlap_start_cycle\": 7937273,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8210378,\n            \"overlap_start_cycle\": 8073882,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8346987,\n            \"overlap_start_cycle\": 8210491,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8483596,\n            \"overlap_start_cycle\": 8347100,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8620205,\n            \"overlap_start_cycle\": 8483709,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8756814,\n            \"overlap_start_cycle\": 8620318,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_05_mlp_up_proj\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7800551,\n            \"overlap_start_cycle\": 7731240,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7937160,\n            \"overlap_start_cycle\": 7800664,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 8073769,\n            \"overlap_start_cycle\": 7937273,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8210378,\n            \"overlap_start_cycle\": 8073882,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8346987,\n            \"overlap_start_cycle\": 8210491,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8483596,\n            \"overlap_start_cycle\": 8347100,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8620205,\n            \"overlap_start_cycle\": 8483709,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8756814,\n            \"overlap_start_cycle\": 8620318,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_06_activation_mul\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7800780,\n            \"overlap_start_cycle\": 7800552,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7937389,\n            \"overlap_start_cycle\": 7937161,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 8073998,\n            \"overlap_start_cycle\": 8073770,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8210607,\n            \"overlap_start_cycle\": 8210379,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8347216,\n            \"overlap_start_cycle\": 8346988,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8483825,\n            \"overlap_start_cycle\": 8483597,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8620434,\n            \"overlap_start_cycle\": 8620206,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8757043,\n            \"overlap_start_cycle\": 8756815,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_06_activation_mul\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7800780,\n            \"overlap_start_cycle\": 7800552,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 7937389,\n            \"overlap_start_cycle\": 7937161,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 8073998,\n            \"overlap_start_cycle\": 8073770,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8210607,\n            \"overlap_start_cycle\": 8210379,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8347216,\n            \"overlap_start_cycle\": 8346988,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8483825,\n            \"overlap_start_cycle\": 8483597,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8620434,\n            \"overlap_start_cycle\": 8620206,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8757043,\n            \"overlap_start_cycle\": 8756815,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_07_mlp_down_proj\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7869100,\n            \"overlap_start_cycle\": 7800777,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 8005709,\n            \"overlap_start_cycle\": 7937386,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 8142318,\n            \"overlap_start_cycle\": 8073995,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8278927,\n            \"overlap_start_cycle\": 8210604,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8415536,\n            \"overlap_start_cycle\": 8347213,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8552145,\n            \"overlap_start_cycle\": 8483822,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8688754,\n            \"overlap_start_cycle\": 8620431,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8825363,\n            \"overlap_start_cycle\": 8757040,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_06_activation_mul\"\n      },\n      {\n        \"boundary_id\": \"edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main\",\n        \"different_token_overlap_observed\": true,\n        \"dst_stage\": \"stage_08_residual_add_2\",\n        \"overlaps\": [\n          {\n            \"downstream_token\": 0,\n            \"overlap_end_cycle\": 7938001,\n            \"overlap_start_cycle\": 7869101,\n            \"upstream_token\": 1\n          },\n          {\n            \"downstream_token\": 1,\n            \"overlap_end_cycle\": 8074610,\n            \"overlap_start_cycle\": 8005710,\n            \"upstream_token\": 2\n          },\n          {\n            \"downstream_token\": 2,\n            \"overlap_end_cycle\": 8211219,\n            \"overlap_start_cycle\": 8142319,\n            \"upstream_token\": 3\n          },\n          {\n            \"downstream_token\": 3,\n            \"overlap_end_cycle\": 8347828,\n            \"overlap_start_cycle\": 8278928,\n            \"upstream_token\": 4\n          },\n          {\n            \"downstream_token\": 4,\n            \"overlap_end_cycle\": 8484437,\n            \"overlap_start_cycle\": 8415537,\n            \"upstream_token\": 5\n          },\n          {\n            \"downstream_token\": 5,\n            \"overlap_end_cycle\": 8621046,\n            \"overlap_start_cycle\": 8552146,\n            \"upstream_token\": 6\n          },\n          {\n            \"downstream_token\": 6,\n            \"overlap_end_cycle\": 8757655,\n            \"overlap_start_cycle\": 8688755,\n            \"upstream_token\": 7\n          },\n          {\n            \"downstream_token\": 7,\n            \"overlap_end_cycle\": 8894264,\n            \"overlap_start_cycle\": 8825364,\n            \"upstream_token\": 8\n          }\n        ],\n        \"src_stage\": \"stage_07_mlp_down_proj\"\n      }\n    ],\n    \"irreversible_stage_turnover_evidence\": {\n      \"candidate_stage_ids\": [],\n      \"failed_stage_turnover_evidence\": [],\n      \"maximum_next_token_stage_entry_gap_cycles\": 1,\n      \"status\": \"observing\"\n    },\n    \"maximum_concurrency_snapshot\": {\n      \"active_stage_tokens\": {\n        \"stage_00_rms_norm_1\": 8,\n        \"stage_01_self_attention\": 7,\n        \"stage_02_residual_add_1\": 5,\n        \"stage_03_rms_norm_2\": 2,\n        \"stage_04_mlp_gate_proj\": 1,\n        \"stage_05_mlp_up_proj\": 1,\n        \"stage_06_activation_mul\": 1,\n        \"stage_07_mlp_down_proj\": 0,\n        \"stage_08_residual_add_2\": 0\n      },\n      \"cycle\": 7801390\n    },\n    \"maximum_concurrent_stage_count\": 9,\n    \"planned_stage_count\": 9,\n    \"schema_version\": \"spatialaccagent.single_layer_pipeline_overlap_evidence.v2\",\n    \"stage_activity_evidence\": [\n      {\n        \"active_end_cycle\": 7681344,\n        \"active_start_cycle\": 7681067,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7697872,\n        \"active_start_cycle\": 7681345,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 7714400,\n        \"active_start_cycle\": 7697873,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 7730928,\n        \"active_start_cycle\": 7714401,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 7747456,\n        \"active_start_cycle\": 7730929,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 7763984,\n        \"active_start_cycle\": 7747457,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 7780512,\n        \"active_start_cycle\": 7763985,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 7797040,\n        \"active_start_cycle\": 7780513,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 7813568,\n        \"active_start_cycle\": 7797041,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 7830096,\n        \"active_start_cycle\": 7813569,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 7846624,\n        \"active_start_cycle\": 7830097,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 7863152,\n        \"active_start_cycle\": 7846625,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 7879680,\n        \"active_start_cycle\": 7863153,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 7896208,\n        \"active_start_cycle\": 7879681,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 7912736,\n        \"active_start_cycle\": 7896209,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 7929264,\n        \"active_start_cycle\": 7912737,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7716319,\n        \"active_start_cycle\": 7681233,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7732847,\n        \"active_start_cycle\": 7697761,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 7749375,\n        \"active_start_cycle\": 7714289,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 7765903,\n        \"active_start_cycle\": 7730817,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 7782431,\n        \"active_start_cycle\": 7747345,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 7798959,\n        \"active_start_cycle\": 7763873,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 7815487,\n        \"active_start_cycle\": 7780401,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 7832015,\n        \"active_start_cycle\": 7796929,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 7848543,\n        \"active_start_cycle\": 7813457,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 7865071,\n        \"active_start_cycle\": 7829985,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 7881599,\n        \"active_start_cycle\": 7846513,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 7898127,\n        \"active_start_cycle\": 7863041,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 7914655,\n        \"active_start_cycle\": 7879569,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 7931183,\n        \"active_start_cycle\": 7896097,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 7947711,\n        \"active_start_cycle\": 7912625,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 7949547,\n        \"active_start_cycle\": 7929153,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7731073,\n        \"active_start_cycle\": 7714543,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7747601,\n        \"active_start_cycle\": 7731071,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 7800775,\n        \"active_start_cycle\": 7747599,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 7937384,\n        \"active_start_cycle\": 7764127,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8073993,\n        \"active_start_cycle\": 7780655,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8210602,\n        \"active_start_cycle\": 7797183,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8347211,\n        \"active_start_cycle\": 7813711,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8483820,\n        \"active_start_cycle\": 7830239,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 8620429,\n        \"active_start_cycle\": 7846767,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 8757038,\n        \"active_start_cycle\": 7863295,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 8893647,\n        \"active_start_cycle\": 7879823,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9030256,\n        \"active_start_cycle\": 7896351,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9166865,\n        \"active_start_cycle\": 7912879,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9303474,\n        \"active_start_cycle\": 7929407,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9440083,\n        \"active_start_cycle\": 7945935,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9576692,\n        \"active_start_cycle\": 7947771,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7731239,\n        \"active_start_cycle\": 7714545,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7800663,\n        \"active_start_cycle\": 7731240,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 7937272,\n        \"active_start_cycle\": 7800664,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 8073881,\n        \"active_start_cycle\": 7937273,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8210490,\n        \"active_start_cycle\": 8073882,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8347099,\n        \"active_start_cycle\": 8210491,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8483708,\n        \"active_start_cycle\": 8347100,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8620317,\n        \"active_start_cycle\": 8483709,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 8756926,\n        \"active_start_cycle\": 8620318,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 8893535,\n        \"active_start_cycle\": 8756927,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 9030144,\n        \"active_start_cycle\": 8893536,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9166753,\n        \"active_start_cycle\": 9030145,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9303362,\n        \"active_start_cycle\": 9166754,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9439971,\n        \"active_start_cycle\": 9303363,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9576580,\n        \"active_start_cycle\": 9439972,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9713189,\n        \"active_start_cycle\": 9576581,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7800551,\n        \"active_start_cycle\": 7731128,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7937160,\n        \"active_start_cycle\": 7800552,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 8073769,\n        \"active_start_cycle\": 7937161,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 8210378,\n        \"active_start_cycle\": 8073770,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8346987,\n        \"active_start_cycle\": 8210379,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8483596,\n        \"active_start_cycle\": 8346988,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8620205,\n        \"active_start_cycle\": 8483597,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8756814,\n        \"active_start_cycle\": 8620206,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 8893423,\n        \"active_start_cycle\": 8756815,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 9030032,\n        \"active_start_cycle\": 8893424,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 9166641,\n        \"active_start_cycle\": 9030033,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9303250,\n        \"active_start_cycle\": 9166642,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9439859,\n        \"active_start_cycle\": 9303251,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9576468,\n        \"active_start_cycle\": 9439860,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9713077,\n        \"active_start_cycle\": 9576469,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9849686,\n        \"active_start_cycle\": 9713078,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7800551,\n        \"active_start_cycle\": 7731128,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7937160,\n        \"active_start_cycle\": 7800552,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 8073769,\n        \"active_start_cycle\": 7937161,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 8210378,\n        \"active_start_cycle\": 8073770,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8346987,\n        \"active_start_cycle\": 8210379,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8483596,\n        \"active_start_cycle\": 8346988,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8620205,\n        \"active_start_cycle\": 8483597,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8756814,\n        \"active_start_cycle\": 8620206,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 8893423,\n        \"active_start_cycle\": 8756815,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 9030032,\n        \"active_start_cycle\": 8893424,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 9166641,\n        \"active_start_cycle\": 9030033,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9303250,\n        \"active_start_cycle\": 9166642,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9439859,\n        \"active_start_cycle\": 9303251,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9576468,\n        \"active_start_cycle\": 9439860,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9713077,\n        \"active_start_cycle\": 9576469,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9849686,\n        \"active_start_cycle\": 9713078,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7800780,\n        \"active_start_cycle\": 7731353,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 7937389,\n        \"active_start_cycle\": 7800777,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 8073998,\n        \"active_start_cycle\": 7937386,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 8210607,\n        \"active_start_cycle\": 8073995,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8347216,\n        \"active_start_cycle\": 8210604,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8483825,\n        \"active_start_cycle\": 8347213,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8620434,\n        \"active_start_cycle\": 8483822,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8757043,\n        \"active_start_cycle\": 8620431,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 8893652,\n        \"active_start_cycle\": 8757040,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 9030261,\n        \"active_start_cycle\": 8893649,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 9166870,\n        \"active_start_cycle\": 9030258,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9303479,\n        \"active_start_cycle\": 9166867,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9440088,\n        \"active_start_cycle\": 9303476,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9576697,\n        \"active_start_cycle\": 9440085,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9713306,\n        \"active_start_cycle\": 9576694,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9849689,\n        \"active_start_cycle\": 9713303,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7869100,\n        \"active_start_cycle\": 7731356,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 8005709,\n        \"active_start_cycle\": 7869101,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 8142318,\n        \"active_start_cycle\": 8005710,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 8278927,\n        \"active_start_cycle\": 8142319,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8415536,\n        \"active_start_cycle\": 8278928,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8552145,\n        \"active_start_cycle\": 8415537,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8688754,\n        \"active_start_cycle\": 8552146,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8825363,\n        \"active_start_cycle\": 8688755,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 8961972,\n        \"active_start_cycle\": 8825364,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 9098581,\n        \"active_start_cycle\": 8961973,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 9235190,\n        \"active_start_cycle\": 9098582,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9371799,\n        \"active_start_cycle\": 9235191,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9508408,\n        \"active_start_cycle\": 9371800,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9645017,\n        \"active_start_cycle\": 9508409,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9781626,\n        \"active_start_cycle\": 9645018,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9918009,\n        \"active_start_cycle\": 9781627,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token\": 15\n      },\n      {\n        \"active_end_cycle\": 7938001,\n        \"active_start_cycle\": 7801390,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 0\n      },\n      {\n        \"active_end_cycle\": 8074610,\n        \"active_start_cycle\": 7937999,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 1\n      },\n      {\n        \"active_end_cycle\": 8211219,\n        \"active_start_cycle\": 8074608,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 2\n      },\n      {\n        \"active_end_cycle\": 8347828,\n        \"active_start_cycle\": 8211217,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 3\n      },\n      {\n        \"active_end_cycle\": 8484437,\n        \"active_start_cycle\": 8347826,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 4\n      },\n      {\n        \"active_end_cycle\": 8621046,\n        \"active_start_cycle\": 8484435,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 5\n      },\n      {\n        \"active_end_cycle\": 8757655,\n        \"active_start_cycle\": 8621044,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 6\n      },\n      {\n        \"active_end_cycle\": 8894264,\n        \"active_start_cycle\": 8757653,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 7\n      },\n      {\n        \"active_end_cycle\": 9030873,\n        \"active_start_cycle\": 8894262,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 8\n      },\n      {\n        \"active_end_cycle\": 9167482,\n        \"active_start_cycle\": 9030871,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 9\n      },\n      {\n        \"active_end_cycle\": 9304091,\n        \"active_start_cycle\": 9167480,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 10\n      },\n      {\n        \"active_end_cycle\": 9440700,\n        \"active_start_cycle\": 9304089,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 11\n      },\n      {\n        \"active_end_cycle\": 9577309,\n        \"active_start_cycle\": 9440698,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 12\n      },\n      {\n        \"active_end_cycle\": 9713918,\n        \"active_start_cycle\": 9577307,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 13\n      },\n      {\n        \"active_end_cycle\": 9850301,\n        \"active_start_cycle\": 9713916,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 14\n      },\n      {\n        \"active_end_cycle\": 9918011,\n        \"active_start_cycle\": 9850299,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token\": 15\n      }\n    ],\n    \"stage_turnover_evidence\": [\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7681345,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7681344,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7697873,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7697872,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 7714401,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 7714400,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 7730929,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 7730928,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 7747457,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 7747456,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 7763985,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 7763984,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 7780513,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 7780512,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 7797041,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 7797040,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 7813569,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 7813568,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 7830097,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 7830096,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 7846625,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 7846624,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 7863153,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 7863152,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 7879681,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 7879680,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 7896209,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 7896208,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 7912737,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 7912736,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7697761,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7716319,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7714289,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7732847,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 7730817,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 7749375,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 7747345,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 7765903,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 7763873,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 7782431,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 7780401,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 7798959,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 7796929,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 7815487,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 7813457,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 7832015,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 7829985,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 7848543,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 7846513,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 7865071,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 7863041,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 7881599,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 7879569,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 7898127,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 7896097,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 7914655,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 7912625,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 7931183,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -18558,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 7929153,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 7947711,\n        \"stage_id\": \"stage_01_self_attention\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7731071,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7731073,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7747599,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7747601,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -36648,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 7764127,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 7800775,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -156729,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 7780655,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 7937384,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -276810,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 7797183,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8073993,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -396891,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 7813711,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8210602,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -516972,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 7830239,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8347211,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -637053,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 7846767,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8483820,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -757134,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 7863295,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 8620429,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -877215,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 7879823,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 8757038,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -997296,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 7896351,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 8893647,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -1117377,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 7912879,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9030256,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -1237458,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 7929407,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9166865,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -1357539,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 7945935,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9303474,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": -1492312,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 7947771,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9440083,\n        \"stage_id\": \"stage_02_residual_add_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7731240,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7731239,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7800664,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7800663,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 7937273,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 7937272,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 8073882,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 8073881,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 8210491,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8210490,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 8347100,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8347099,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 8483709,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8483708,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 8620318,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8620317,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 8756927,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 8756926,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 8893536,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 8893535,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 9030145,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 9030144,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 9166754,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9166753,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 9303363,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9303362,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 9439972,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9439971,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 9576581,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9576580,\n        \"stage_id\": \"stage_03_rms_norm_2\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7800552,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7800551,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7937161,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7937160,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 8073770,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 8073769,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 8210379,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 8210378,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 8346988,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8346987,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 8483597,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8483596,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 8620206,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8620205,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 8756815,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8756814,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 8893424,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 8893423,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 9030033,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 9030032,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 9166642,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 9166641,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 9303251,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9303250,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 9439860,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9439859,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 9576469,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9576468,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 9713078,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9713077,\n        \"stage_id\": \"stage_04_mlp_gate_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7800552,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7800551,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7937161,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7937160,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 8073770,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 8073769,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 8210379,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 8210378,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 8346988,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8346987,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 8483597,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8483596,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 8620206,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8620205,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 8756815,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8756814,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 8893424,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 8893423,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 9030033,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 9030032,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 9166642,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 9166641,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 9303251,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9303250,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 9439860,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9439859,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 9576469,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9576468,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 9713078,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9713077,\n        \"stage_id\": \"stage_05_mlp_up_proj\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7800777,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7800780,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7937386,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7937389,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 8073995,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 8073998,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 8210604,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 8210607,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 8347213,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8347216,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 8483822,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8483825,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 8620431,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8620434,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 8757040,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8757043,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 8893649,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 8893652,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 9030258,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 9030261,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 9166867,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 9166870,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 9303476,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9303479,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 9440085,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9440088,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 9576694,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9576697,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": -3,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 9713303,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9713306,\n        \"stage_id\": \"stage_06_activation_mul\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7869101,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7869100,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 8005710,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 8005709,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 8142319,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 8142318,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 8278928,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 8278927,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 8415537,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8415536,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 8552146,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8552145,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 8688755,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8688754,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 8825364,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8825363,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 8961973,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 8961972,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 9098582,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 9098581,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 9235191,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 9235190,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 9371800,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9371799,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 9508409,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9508408,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 9645018,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9645017,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 9781627,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9781626,\n        \"stage_id\": \"stage_07_mlp_down_proj\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7937999,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7938001,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 8074608,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 8074610,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 8211217,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 8211219,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 8347826,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 8347828,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 8484435,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 8484437,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 8621044,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 8621046,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 8757653,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 8757655,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 8894262,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 8894264,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 9030871,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 9030873,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 9167480,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 9167482,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 9304089,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 9304091,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 9440698,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 9440700,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 9577307,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 9577309,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 9713916,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 9713918,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      },\n      {\n        \"gap_cycles\": -2,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 9850299,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 9850301,\n        \"stage_id\": \"stage_08_residual_add_2\"\n      }\n    ],\n    \"status\": \"fail\",\n    \"terminal_trace_flush_evidence\": {\n      \"actual_output_line_count\": 1792,\n      \"checks\": {\n        \"all_required_trace_records_are_accepted\": true,\n        \"execution_status_pass\": true,\n        \"only_terminal_block_output_trace_is_missing\": false,\n        \"output_line_count_matches\": true,\n        \"remote_exit_status_pass\": true,\n        \"required_boundaries_are_valid\": true,\n        \"single_matching_sim_pass_declaration\": true,\n        \"trace_positions_are_unique_and_well_formed\": true\n      },\n      \"duplicate_required_trace_position_count\": 0,\n      \"duplicate_required_trace_positions\": [],\n      \"expected_output_line_count\": 1792,\n      \"inferred\": false,\n      \"inferred_record\": null,\n      \"malformed_required_trace_position_count\": 0,\n      \"malformed_required_trace_positions\": [],\n      \"missing_required_trace_position_count\": 0,\n      \"missing_required_trace_positions\": [],\n      \"observed_required_trace_position_count\": 416,\n      \"required_trace_position_count\": 416,\n      \"sim_pass_declarations\": [\n        {\n          \"beats\": 1792,\n          \"cycles\": 2236945\n        }\n      ],\n      \"unexpected_required_trace_position_count\": 0,\n      \"unexpected_required_trace_positions\": [],\n      \"unparsed_pipeline_trace_line_count\": 0\n    },\n    \"terminal_trace_flush_inferred\": false,\n    \"trace_record_count\": 416,\n    \"trace_sha256\": \"8b721485e310341bbe5651973089a4fecadf56204a235ae1a78ec8185ae23b94\",\n    \"transition_evidence\": [\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 1,\n        \"next_token_active_start_cycle\": 7681345,\n        \"overlapped\": true,\n        \"prior_token\": 0,\n        \"prior_token_active_end_cycle\": 7681344,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 2,\n        \"next_token_active_start_cycle\": 7697873,\n        \"overlapped\": true,\n        \"prior_token\": 1,\n        \"prior_token_active_end_cycle\": 7697872,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 3,\n        \"next_token_active_start_cycle\": 7714401,\n        \"overlapped\": true,\n        \"prior_token\": 2,\n        \"prior_token_active_end_cycle\": 7714400,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 4,\n        \"next_token_active_start_cycle\": 7730929,\n        \"overlapped\": true,\n        \"prior_token\": 3,\n        \"prior_token_active_end_cycle\": 7730928,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 5,\n        \"next_token_active_start_cycle\": 7747457,\n        \"overlapped\": true,\n        \"prior_token\": 4,\n        \"prior_token_active_end_cycle\": 7747456,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 6,\n        \"next_token_active_start_cycle\": 7763985,\n        \"overlapped\": true,\n        \"prior_token\": 5,\n        \"prior_token_active_end_cycle\": 7763984,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 7,\n        \"next_token_active_start_cycle\": 7780513,\n        \"overlapped\": true,\n        \"prior_token\": 6,\n        \"prior_token_active_end_cycle\": 7780512,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 8,\n        \"next_token_active_start_cycle\": 7797041,\n        \"overlapped\": true,\n        \"prior_token\": 7,\n        \"prior_token_active_end_cycle\": 7797040,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 9,\n        \"next_token_active_start_cycle\": 7813569,\n        \"overlapped\": true,\n        \"prior_token\": 8,\n        \"prior_token_active_end_cycle\": 7813568,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 10,\n        \"next_token_active_start_cycle\": 7830097,\n        \"overlapped\": true,\n        \"prior_token\": 9,\n        \"prior_token_active_end_cycle\": 7830096,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 11,\n        \"next_token_active_start_cycle\": 7846625,\n        \"overlapped\": true,\n        \"prior_token\": 10,\n        \"prior_token_active_end_cycle\": 7846624,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 12,\n        \"next_token_active_start_cycle\": 7863153,\n        \"overlapped\": true,\n        \"prior_token\": 11,\n        \"prior_token_active_end_cycle\": 7863152,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 13,\n        \"next_token_active_start_cycle\": 7879681,\n        \"overlapped\": true,\n        \"prior_token\": 12,\n        \"prior_token_active_end_cycle\": 7879680,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 14,\n        \"next_token_active_start_cycle\": 7896209,\n        \"overlapped\": true,\n        \"prior_token\": 13,\n        \"prior_token_active_end_cycle\": 7896208,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      },\n      {\n        \"gap_cycles\": 1,\n        \"keeps_pipeline_filled\": true,\n        \"next_token\": 15,\n        \"next_token_active_start_cycle\": 7912737,\n        \"overlapped\": true,\n        \"prior_token\": 14,\n        \"prior_token_active_end_cycle\": 7912736,\n        \"stage_id\": \"stage_00_rms_norm_1\"\n      }\n    ],\n    \"whole_sequence_barrier_evidence\": [\n      {\n        \"final_token_last_input_cycle\": 7912848,\n        \"stage_id\": \"stage_00_rms_norm_1\",\n        \"token_0_first_output_cycle\": 7681233,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 7929264,\n        \"stage_id\": \"stage_01_self_attention\",\n        \"token_0_first_output_cycle\": 7714543,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 7949547,\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"token_0_first_output_cycle\": 7714545,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 9576692,\n        \"stage_id\": \"stage_03_rms_norm_2\",\n        \"token_0_first_output_cycle\": 7731128,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 9713189,\n        \"stage_id\": \"stage_04_mlp_gate_proj\",\n        \"token_0_first_output_cycle\": 7731353,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 9713189,\n        \"stage_id\": \"stage_05_mlp_up_proj\",\n        \"token_0_first_output_cycle\": 7731353,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 9849686,\n        \"stage_id\": \"stage_06_activation_mul\",\n        \"token_0_first_output_cycle\": 7731356,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 9849689,\n        \"stage_id\": \"stage_07_mlp_down_proj\",\n        \"token_0_first_output_cycle\": 7801390,\n        \"whole_sequence_barrier_observed\": false\n      },\n      {\n        \"final_token_last_input_cycle\": 9918009,\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"token_0_first_output_cycle\": 7801392,\n        \"whole_sequence_barrier_observed\": false\n      }\n    ]\n  },\n  \"policy\": {\n    \"legacy_pattern_input_is_not_acceptance\": true,\n    \"real_weight_semantic_harness_required\": true,\n    \"remote_vcs_execution_required\": true,\n    \"true_adjacent_token_pipeline_overlap_required\": true\n  },\n  \"real_weight_execution\": {\n    \"binding_manifest\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json\",\n    \"consumed_tensor_hashes\": [\n      \"19cb555eb19556d256504d9f642f577c84b9ad357205105cf535100688f9c222\",\n      \"1c3ae6b0c5c0c525224ae50949b8b3adb7b8a2d67fff0382e7c34d6dfdaa2ce2\",\n      \"2c1ed3ddbfee1ec991624e045f4d24d9b4531eb2cce3a89bc56921602fd86cc8\",\n      \"42cd4d696ed62cca3fdfe2f9ae60098d58a9ef9aa12785bb87d2138caccaffec\",\n      \"5668398b8ae0b69ebf24d8d1bf05509d8276d3c85be49cfc48a703cda3a91188\",\n      \"69d7c9d95b964280cd18618f4ca4883732b724e21962fa11b2b9c8552ba5b94c\",\n      \"7c36f7e02b1d84ccb38c91b552d995c4086fe34358a7d8dcb752ffddadb263a8\",\n      \"81021c08cced9f1181adb2ba6b92aa112ec9d0b0aef62f103fce127f5d286188\",\n      \"8a582767a99d9285f66805b711bf64b28d984a9b5ec9c57d3854b57f2c5a6cdf\",\n      \"9041b6bc4fd8fb547bdf05fe60dbda1e424008019e4ef258c7ce16651aa97454\",\n      \"a56a082019a9cadc1fc40f79cf1b2653321dd03f53c3a9d1204f770bfbf6349e\",\n      \"ae588034f9c377f606b1e41d9fd73997b78b1f933f367a7bd39bc61b1edd6d42\"\n    ],\n    \"verified\": true\n  },\n  \"run_dir\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run\",\n  \"schema_version\": \"spatialaccagent.single_layer_functional_sim.v1\",\n  \"semantic_testbench_manifest\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json\",\n  \"semantic_testbench_sha256\": \"6447ebfdb0934c917eb35e2ab80d77fd2cf536c008f95667f98673d70f66bb84\",\n  \"stats\": {\n    \"blockers\": [],\n    \"compile\": {\n      \"failure_class\": null,\n      \"remote_state\": \"done\",\n      \"remote_workdir\": \"/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188\",\n      \"returncode\": 0,\n      \"status\": \"pass\",\n      \"transport\": \"recovered_exact_fingerprint_detached_remote_job\"\n    },\n    \"downloads\": {\n      \"rtl_output.memh\": {\n        \"argv\": [\n          \"scp\",\n          \"-o\",\n          \"BatchMode=yes\",\n          \"-o\",\n          \"ConnectTimeout=20\",\n          \"-o\",\n          \"ServerAliveInterval=30\",\n          \"-o\",\n          \"ServerAliveCountMax=240\",\n          \"-o\",\n          \"TCPKeepAlive=yes\",\n          \"-o\",\n          \"StrictHostKeyChecking=no\",\n          \"-o\",\n          \"UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts\",\n          \"-P\",\n          \"22\",\n          \"hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/rtl_output.memh\",\n          \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/rtl_output.memh\"\n        ],\n        \"cwd\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel\",\n        \"duration_sec\": 0.7158830469998065,\n        \"returncode\": 0,\n        \"status\": \"pass\",\n        \"stderr_tail\": \"\",\n        \"stdout_tail\": \"\"\n      },\n      \"sim.log\": {\n        \"argv\": [\n          \"scp\",\n          \"-o\",\n          \"BatchMode=yes\",\n          \"-o\",\n          \"ConnectTimeout=20\",\n          \"-o\",\n          \"ServerAliveInterval=30\",\n          \"-o\",\n          \"ServerAliveCountMax=240\",\n          \"-o\",\n          \"TCPKeepAlive=yes\",\n          \"-o\",\n          \"StrictHostKeyChecking=no\",\n          \"-o\",\n          \"UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts\",\n          \"-P\",\n          \"22\",\n          \"hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/sim.log\",\n          \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/sim.log\"\n        ],\n        \"cwd\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel\",\n        \"duration_sec\": 0.7325603120002597,\n        \"returncode\": 0,\n        \"status\": \"pass\",\n        \"stderr_tail\": \"\",\n        \"stdout_tail\": \"\"\n      },\n      \"sim.stderr.log\": {\n        \"argv\": [\n          \"scp\",\n          \"-o\",\n          \"BatchMode=yes\",\n          \"-o\",\n          \"ConnectTimeout=20\",\n          \"-o\",\n          \"ServerAliveInterval=30\",\n          \"-o\",\n          \"ServerAliveCountMax=240\",\n          \"-o\",\n          \"TCPKeepAlive=yes\",\n          \"-o\",\n          \"StrictHostKeyChecking=no\",\n          \"-o\",\n          \"UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts\",\n          \"-P\",\n          \"22\",\n          \"hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/sim.stderr.log\",\n          \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/sim.stderr.log\"\n        ],\n        \"cwd\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel\",\n        \"duration_sec\": 0.7258270930001345,\n        \"returncode\": 0,\n        \"status\": \"pass\",\n        \"stderr_tail\": \"\",\n        \"stdout_tail\": \"\"\n      },\n      \"vcs.log\": {\n        \"argv\": [\n          \"scp\",\n          \"-o\",\n          \"BatchMode=yes\",\n          \"-o\",\n          \"ConnectTimeout=20\",\n          \"-o\",\n          \"ServerAliveInterval=30\",\n          \"-o\",\n          \"ServerAliveCountMax=240\",\n          \"-o\",\n          \"TCPKeepAlive=yes\",\n          \"-o\",\n          \"StrictHostKeyChecking=no\",\n          \"-o\",\n          \"UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts\",\n          \"-P\",\n          \"22\",\n          \"hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/vcs.log\",\n          \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/vcs.log\"\n        ],\n        \"cwd\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel\",\n        \"duration_sec\": 0.7153211750000992,\n        \"returncode\": 0,\n        \"status\": \"pass\",\n        \"stderr_tail\": \"\",\n        \"stdout_tail\": \"\"\n      }\n    },\n    \"failure_class\": null,\n    \"input_fingerprint_sha256\": \"83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8\",\n    \"local_workdir\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel\",\n    \"memory_initialization\": {\n      \"compile_defines\": [\n        \"ENABLE_INITIAL_MEM_\"\n      ],\n      \"dependencies\": [\n        {\n          \"declared_by\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/expTable_2048x26.sv\",\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.memh\",\n          \"remote_relative_path\": \"src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.memh\",\n          \"sha256\": \"5093afd06e5aec5ec2ba868aa8231300546a19abe76c65dfbac601daa6addc88\"\n        },\n        {\n          \"declared_by\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/sigmoidTable_129x19.sv\",\n          \"path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.memh\",\n          \"remote_relative_path\": \"src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.memh\",\n          \"sha256\": \"a285a0b32c9b233afc4761e4b35ae25a5ec99d9d9ee6b691ae39dfb08c5e97e6\"\n        }\n      ],\n      \"schema_version\": \"spatialaccagent.semantic_memory_initialization.v1\"\n    },\n    \"output_capture\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/rtl_output.memh\",\n    \"python_environment_contract\": {\n      \"fingerprint_sha256\": null,\n      \"group\": null\n    },\n    \"remote_artifact_persistence\": {\n      \"blockers\": [],\n      \"receipt\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/remote_artifacts/semantic_vcs_single_transformer_layer_kernel/83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8/receipt.json\",\n      \"receipt_sha256\": \"4b885e62c887c1359eb2939d48ea599731bba0fc08b1a0892bb039f1adb999e9\",\n      \"receipt_upload\": {\n        \"argv\": [\n          \"scp\",\n          \"-o\",\n          \"BatchMode=yes\",\n          \"-o\",\n          \"ConnectTimeout=20\",\n          \"-o\",\n          \"ServerAliveInterval=30\",\n          \"-o\",\n          \"ServerAliveCountMax=240\",\n          \"-o\",\n          \"TCPKeepAlive=yes\",\n          \"-o\",\n          \"StrictHostKeyChecking=no\",\n          \"-o\",\n          \"UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts\",\n          \"-P\",\n          \"22\",\n          \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/remote_artifacts/semantic_vcs_single_transformer_layer_kernel/83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8/remote_acknowledgment.json\",\n          \"hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/.spatialacc_local_evidence_persisted.json\"\n        ],\n        \"cwd\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/remote_artifacts/semantic_vcs_single_transformer_layer_kernel/83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8\",\n        \"duration_sec\": 0.7223239009999816,\n        \"returncode\": 0,\n        \"status\": \"pass\",\n        \"stderr_tail\": \"\",\n        \"stdout_tail\": \"\"\n      },\n      \"remote_acknowledgment\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/remote_artifacts/semantic_vcs_single_transformer_layer_kernel/83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8/remote_acknowledgment.json\",\n      \"remote_acknowledgment_sha256\": \"534d24076a9508dbecba386479469f1083ecef536b61b6014ef4559adaa0d9bf\",\n      \"remote_receipt\": \"/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/.spatialacc_local_evidence_persisted.json\",\n      \"status\": \"pass\"\n    },\n    \"remote_job_reuse\": {\n      \"contract_download\": {\n        \"argv\": [\n          \"scp\",\n          \"-o\",\n          \"BatchMode=yes\",\n          \"-o\",\n          \"ConnectTimeout=20\",\n          \"-o\",\n          \"ServerAliveInterval=30\",\n          \"-o\",\n          \"ServerAliveCountMax=240\",\n          \"-o\",\n          \"TCPKeepAlive=yes\",\n          \"-o\",\n          \"StrictHostKeyChecking=no\",\n          \"-o\",\n          \"UserKnownHostsFile=/tmp/spatialaccagent_semantic_known_hosts\",\n          \"-P\",\n          \"22\",\n          \"hyyuan@10.12.133.23:/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188/.spatialacc_semantic_job.json\",\n          \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/remote_recovery_identity/.spatialacc_semantic_job.json\"\n        ],\n        \"cwd\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/remote_recovery_identity\",\n        \"duration_sec\": 0.7130270979999977,\n        \"returncode\": 0,\n        \"status\": \"pass\",\n        \"stderr_tail\": \"\",\n        \"stdout_tail\": \"\"\n      },\n      \"expected_job_contract_sha256\": \"02849236e624e8e1e1ac5a7426e4601ca483e62ad0ff3bb900a396b05703ea8a\",\n      \"identity_source\": \"full_remote_job_contract\",\n      \"real_tool_was_not_relaunched\": true,\n      \"remote_job_contract_sha256\": \"02849236e624e8e1e1ac5a7426e4601ca483e62ad0ff3bb900a396b05703ea8a\",\n      \"remote_workdir\": \"/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188\",\n      \"status\": \"pass\"\n    },\n    \"remote_stage_cleanup\": {\n      \"status\": \"not_run\",\n      \"summary\": \"skipped because an exact-fingerprint detached remote job was recovered\"\n    },\n    \"remote_workdir\": \"/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188\",\n    \"rtl_output_sha256\": \"4441348a14de7c9516ed00e2a4cacd895ae1cda50a0cedf94757dcbddb30e23e\",\n    \"run\": {\n      \"adaptive_semantic_stall_evidence\": {},\n      \"adaptive_semantic_stall_termination\": {\n        \"status\": \"not_run\"\n      },\n      \"duration_sec\": 3004.281973096,\n      \"failure_class\": null,\n      \"poll_attempts\": 183,\n      \"poll_transport_failures\": 0,\n      \"progress_observer_errors\": [],\n      \"remote_job_preserved\": false,\n      \"remote_state\": \"done\",\n      \"remote_workdir\": \"/home/hyyuan/workspace/spatialaccagent_artifacts/semantic_vcs/spatialacc_qwen_agent_fast_run/single_transformer_layer_kernel/83f58f1246a3_1784746188\",\n      \"returncode\": 0,\n      \"status\": \"pass\",\n      \"transport\": \"reattached_exact_fingerprint_detached_remote_job\"\n    },\n    \"schema_version\": \"spatialaccagent.semantic_simulator_execution.v1\",\n    \"setup\": {\n      \"status\": \"not_run\",\n      \"summary\": \"reused existing exact-fingerprint remote directory\"\n    },\n    \"sim_log\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/sim.log\",\n    \"sim_stderr_log\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/sim.stderr.log\",\n    \"simulator\": \"vcs\",\n    \"source_files\": [\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Activation.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/AddRawFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/AddRecFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/AttentionGQA.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/CompareRecFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_1.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_2.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_3.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedCanonicalWordPacker_5.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedObservableLlamaStyleBlock.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedStreamIngress.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ConnectedWeightLoader.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/DivSqrtRawFN_small_e8_s24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/DivSqrtRecFMToRaw_small_e8_s24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/DivSqrtRecFM_small_e8_s24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ElementwiseMul.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/GatedMLP.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/INToRecFN_i25_e8_s24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/INToRecFN_i36_e8_s24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_1.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_2.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_3.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Linear_4.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/MulFullRawFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/MulRawFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/MulRecFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/QKVProjection.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue1792_StreamBeat.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue1792_StreamBeat_4.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue2_StreamBeat.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue2_StreamBeat_1.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue4_StreamBeat.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Queue4_StreamBeat_2.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RMSNorm.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RecFNToIN_e8_s24_i16.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RecFNToRecFN.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RecFNToRecFN_8.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ResidualAdd.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoPE.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie5_is11_oe8_os24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie6_is25_oe8_os24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie7_is36_oe8_os24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie8_is24_oe5_os11.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundAnyRawFNToRecFN_ie8_is26_oe8_os24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/RoundRawFNToRecFN_e8_s24.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/SingleLayerSemanticHarness.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/Softmax.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/VectorNorm.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/expTable_2048x26.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_1792x256.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_1792x269.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_1792x269_0.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_2x144.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_2x269.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/ram_4x144.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/sigmoidTable_129x19.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/ConnectedObservableLlamaStyleBlock_Verification.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/assert/layers-SingleLayerSemanticHarness-Verification-Assert.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/assume/layers-SingleLayerSemanticHarness-Verification-Assume.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/cover/layers-SingleLayerSemanticHarness-Verification-Cover.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/layers-ConnectedObservableLlamaStyleBlock-Verification.sv\",\n      \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness/single_layer/verification/layers-SingleLayerSemanticHarness-Verification.sv\"\n    ],\n    \"stage_id\": \"single_transformer_layer_kernel\",\n    \"status\": \"pass\",\n    \"summary\": \"remote VCS semantic harness executed with hash-bound real inputs\",\n    \"testbench\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/single_layer_real_model_tb.sv\",\n    \"tool_profile\": {\n      \"compile_defines\": [\n        \"ENABLE_INITIAL_MEM_\"\n      ],\n      \"compile_jobs\": 32,\n      \"executable\": \"/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109/bin/vcs\",\n      \"host\": \"hyyuan@10.12.133.23\",\n      \"name\": \"vcs\",\n      \"port\": 22,\n      \"role\": \"functional_verification\",\n      \"scope\": \"remote\",\n      \"vcs_target_arch\": \"linux64\"\n    },\n    \"tool_scope\": \"remote\",\n    \"top_module\": \"semantic_single_transformer_layer_kernel_tb\",\n    \"upload\": {\n      \"status\": \"not_run\",\n      \"summary\": \"full remote payload identity matched; upload was not repeated\"\n    },\n    \"vcs_log\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/operator_leaf_vcs/single_transformer_layer_kernel/vcs.log\"\n  },\n  \"status\": \"fail\",\n  \"testbench\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/single_layer/single_layer_real_model_tb.sv\",\n  \"testbench_sha256\": \"23e4ece8a709c15f5b1e263deab4b9ef0272c261739abbf7cfa6b343be518db0\"\n}\n",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
        "sha256": "7133488e287a359b021c0ed8e0e8ba4481b1199555fe44eca5c33a2a654558c1",
        "truncated": false
      },
      {
        "bytes": 4484,
        "content": "package spatialaccagent.templates\n\nimport chisel3._\nimport chisel3.util._\nimport hardfloat._\nimport hardfloat.consts\n\nobject AccMath {\n  def ceilDiv(a: Int, b: Int): Int = (a + b - 1) / b\n\n  def resizeSigned(x: SInt, width: Int): SInt = resizeSignedToUInt(x, width).asSInt\n\n  def resizeSignedToUInt(x: SInt, width: Int): UInt = {\n    val u = x.asUInt\n    if (width <= x.getWidth) {\n      u(width - 1, 0)\n    } else {\n      Cat(Fill(width - x.getWidth, u(x.getWidth - 1)), u)\n    }\n  }\n}\n\nobject IeeeMath {\n  private val fp16ExpWidth = 5\n  private val fp16SigWidth = 11\n  private val fp32ExpWidth = 8\n  private val fp32SigWidth = 24\n\n  val fp32Zero: UInt = 0.U(32.W)\n  val fp32One: UInt = \"h3f800000\".U(32.W)\n\n  def fp32Constant(value: Double): UInt = {\n    val bits = java.lang.Float.floatToRawIntBits(value.toFloat)\n    BigInt(bits.toLong & 0xffffffffL).U(32.W)\n  }\n\n  def toFp32(value: UInt, bits: Int): UInt = {\n    require(bits == 16 || bits == 32, s\"IEEE input width must be 16 or 32, got $bits\")\n    if (bits == 32) {\n      value\n    } else {\n      val convert = Module(new RecFNToRecFN(fp16ExpWidth, fp16SigWidth, fp32ExpWidth, fp32SigWidth))\n      convert.io.in := recFNFromFN(fp16ExpWidth, fp16SigWidth, value)\n      convert.io.roundingMode := consts.round_near_even\n      convert.io.detectTininess := consts.tininess_afterRounding\n      fNFromRecFN(fp32ExpWidth, fp32SigWidth, convert.io.out)\n    }\n  }\n\n  def fromFp32(value: UInt, bits: Int): UInt = {\n    require(bits == 16 || bits == 32, s\"IEEE output width must be 16 or 32, got $bits\")\n    if (bits == 32) {\n      value\n    } else {\n      val convert = Module(new RecFNToRecFN(fp32ExpWidth, fp32SigWidth, fp16ExpWidth, fp16SigWidth))\n      convert.io.in := recFNFromFN(fp32ExpWidth, fp32SigWidth, value)\n      convert.io.roundingMode := consts.round_near_even\n      convert.io.detectTininess := consts.tininess_afterRounding\n      fNFromRecFN(fp16ExpWidth, fp16SigWidth, convert.io.out)\n    }\n  }\n\n  def addFp32(a: UInt, b: UInt): UInt = {\n    val add = Module(new AddRecFN(fp32ExpWidth, fp32SigWidth))\n    add.io.subOp := false.B\n    add.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)\n    add.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)\n    add.io.roundingMode := consts.round_near_even\n    add.io.detectTininess := consts.tininess_afterRounding\n    fNFromRecFN(fp32ExpWidth, fp32SigWidth, add.io.out)\n  }\n\n  def subFp32(a: UInt, b: UInt): UInt = {\n    val sub = Module(new AddRecFN(fp32ExpWidth, fp32SigWidth))\n    sub.io.subOp := true.B\n    sub.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)\n    sub.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)\n    sub.io.roundingMode := consts.round_near_even\n    sub.io.detectTininess := consts.tininess_afterRounding\n    fNFromRecFN(fp32ExpWidth, fp32SigWidth, sub.io.out)\n  }\n\n  def mulFp32(a: UInt, b: UInt): UInt = {\n    val mul = Module(new MulRecFN(fp32ExpWidth, fp32SigWidth))\n    mul.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)\n    mul.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)\n    mul.io.roundingMode := consts.round_near_even\n    mul.io.detectTininess := consts.tininess_afterRounding\n    fNFromRecFN(fp32ExpWidth, fp32SigWidth, mul.io.out)\n  }\n\n  def lessThanFp32(a: UInt, b: UInt): Bool = {\n    val compare = Module(new CompareRecFN(fp32ExpWidth, fp32SigWidth))\n    compare.io.a := recFNFromFN(fp32ExpWidth, fp32SigWidth, a)\n    compare.io.b := recFNFromFN(fp32ExpWidth, fp32SigWidth, b)\n    compare.io.signaling := false.B\n    compare.io.lt\n  }\n\n  def sumFp32(values: Seq[UInt]): UInt = {\n    require(values.nonEmpty, \"sumFp32 requires at least one value\")\n    values.reduce((a, b) => addFp32(a, b))\n  }\n}\n\nfinal case class StreamSpec(dataBits: Int, addrBits: Int) {\n  require(dataBits > 0, \"dataBits must be positive\")\n  require(addrBits > 0, \"addrBits must be positive\")\n}\n\nclass StageConfig(seqBits: Int) extends Bundle {\n  val seqlen = UInt(seqBits.W)\n  val prefill = Bool()\n  val singleQuery = Bool()\n}\n\nclass StreamBeat(spec: StreamSpec) extends Bundle {\n  val data = UInt(spec.dataBits.W)\n  val st = Bool()\n  val addr = UInt(spec.addrBits.W)\n  val last = Bool()\n}\n\nclass WeightWrite(dataBits: Int, addrBits: Int) extends Bundle {\n  val addr = UInt(addrBits.W)\n  val data = UInt(dataBits.W)\n}\n\nclass Int8QuantPorts extends Bundle {\n  val outInvScale = Input(UInt(32.W))\n  val outZeroPoint = Input(SInt(8.W))\n}\n\nclass LinearScalePorts extends Bundle {\n  val outScale = Input(UInt(32.W))\n  val biasScale = Input(UInt(32.W))\n}\n",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Common.scala",
        "sha256": "991168fe5c5941f7b193e9722505eb2836df321f0c8dd15a2977b0dce03d143c",
        "truncated": false
      },
      {
        "bytes": 4105,
        "content": "package spatialaccagent.templates\n\nimport chisel3._\nimport chisel3.util._\n\nfinal case class ResidualParams(\n  hiddenSize: Int,\n  lanes: Int = 8,\n  elemBits: Int = 32,\n  batchSize: Int = 16,\n  maxSeqLen: Int = 16\n) {\n  require(hiddenSize % lanes == 0, \"hiddenSize must be divisible by lanes\")\n  require(elemBits == 16 || elemBits == 32, \"ResidualAdd elements must be IEEE FP16 or FP32\")\n  val beats: Int = hiddenSize / lanes\n  val beatBits: Int = lanes * elemBits\n  val addrBits: Int = log2Ceil(batchSize * beats max 2)\n  val streamCapacity: Int = maxSeqLen * beats\n}\n\nclass ResidualAdd(p: ResidualParams) extends Module {\n  val io = IO(new Bundle {\n    val cfg = Input(new StageConfig(log2Ceil(p.maxSeqLen + 1 max 2)))\n    val residual = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))\n    val computed = Flipped(Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits))))\n    val out = Decoupled(new StreamBeat(StreamSpec(p.beatBits, p.addrBits)))\n  })\n\n  val streamSpec = StreamSpec(p.beatBits, p.addrBits)\n  val residualQ = Module(new Queue(\n    new StreamBeat(streamSpec),\n    p.streamCapacity,\n    pipe = false,\n    flow = false,\n    useSyncReadMem = true\n  ))\n  val computedQ = Module(new Queue(\n    new StreamBeat(streamSpec),\n    p.streamCapacity,\n    pipe = false,\n    flow = false,\n    useSyncReadMem = true\n  ))\n  val outputQ = Module(new Queue(\n    new StreamBeat(streamSpec),\n    2,\n    pipe = true,\n    flow = false\n  ))\n\n  io.residual <> residualQ.io.enq\n  io.computed <> computedQ.io.enq\n  io.out <> outputQ.io.deq\n\n  val a = residualQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))\n  val b = computedQ.io.deq.bits.data.asTypeOf(Vec(p.lanes, UInt(p.elemBits.W)))\n  val y = Wire(Vec(p.lanes, UInt(p.elemBits.W)))\n  for (i <- 0 until p.lanes) {\n    val sum = IeeeMath.addFp32(\n      IeeeMath.toFp32(a(i), p.elemBits),\n      IeeeMath.toFp32(b(i), p.elemBits)\n    )\n    y(i) := IeeeMath.fromFp32(sum, p.elemBits)\n  }\n\n  val joinedBeat = Wire(new StreamBeat(streamSpec))\n  joinedBeat.data := y.asUInt\n  joinedBeat.st := computedQ.io.deq.bits.st\n  joinedBeat.addr := computedQ.io.deq.bits.addr\n  joinedBeat.last := computedQ.io.deq.bits.last\n\n  val heldBeat = Reg(new StreamBeat(streamSpec))\n  val heldValid = RegInit(false.B)\n  val beatInToken = RegInit(0.U(log2Ceil(p.beats max 2).W))\n  val seqBits = log2Ceil(p.maxSeqLen + 1 max 2)\n  val tokenInSequence = RegInit(0.U(seqBits.W))\n  val configuredSeq = Mux(\n    io.cfg.seqlen === 0.U || io.cfg.seqlen > p.maxSeqLen.U,\n    p.maxSeqLen.U(seqBits.W),\n    io.cfg.seqlen\n  )\n  val pairValid = residualQ.io.deq.valid && computedQ.io.deq.valid\n  val tokenFinalBeat = beatInToken === (p.beats - 1).U\n  val sequenceFinalBeat = tokenFinalBeat && (tokenInSequence === (configuredSeq - 1.U))\n\n  residualQ.io.deq.ready := false.B\n  computedQ.io.deq.ready := false.B\n  outputQ.io.enq.valid := false.B\n  outputQ.io.enq.bits := joinedBeat\n\n  when(heldValid) {\n    outputQ.io.enq.valid := pairValid\n    outputQ.io.enq.bits := heldBeat\n    when(outputQ.io.enq.fire) {\n      heldValid := false.B\n    }\n  }.otherwise {\n    when(pairValid) {\n      when(tokenFinalBeat && !sequenceFinalBeat) {\n        residualQ.io.deq.ready := computedQ.io.deq.valid\n        computedQ.io.deq.ready := residualQ.io.deq.valid\n        when(residualQ.io.deq.fire && computedQ.io.deq.fire) {\n          heldBeat := joinedBeat\n          heldValid := true.B\n          beatInToken := 0.U\n          tokenInSequence := tokenInSequence + 1.U\n        }\n      }.otherwise {\n        outputQ.io.enq.valid := true.B\n        residualQ.io.deq.ready := computedQ.io.deq.valid && outputQ.io.enq.ready\n        computedQ.io.deq.ready := residualQ.io.deq.valid && outputQ.io.enq.ready\n        when(outputQ.io.enq.fire) {\n          when(tokenFinalBeat) {\n            beatInToken := 0.U\n            when(sequenceFinalBeat) {\n              tokenInSequence := 0.U\n            }.otherwise {\n              tokenInSequence := tokenInSequence + 1.U\n            }\n          }.otherwise {\n            beatInToken := beatInToken + 1.U\n          }\n        }\n      }\n    }\n  }\n}\n",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
        "sha256": "110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34",
        "truncated": false
      },
      {
        "bytes": 1411,
        "content": "{\n  \"repair_actions\": [\n    {\n      \"debug_layer\": \"single_transformer_layer_kernel\",\n      \"reason\": \"the current exact-board trace contradicts the prior single-layer pipeline certificate; rerun and repair the connected single-layer kernel before returning to Stage 3\",\n      \"repair_gate\": \"case_single_layer_functional\",\n      \"repair_kind\": \"case_single_layer_functional\",\n      \"root_candidate_module\": null,\n      \"scope\": \"verification_capability_repair\",\n      \"target_modules\": [\n        \"connected_single_transformer_layer_kernel\",\n        \"single_layer_pipeline_overlap_contract\"\n      ]\n    }\n  ],\n  \"repair_workflow\": {\n    \"llm_disposition\": {\n      \"approval_action_ids\": [],\n      \"converted_to_instrumentation_first\": false,\n      \"status\": \"ready\",\n      \"summary\": \"Hash-bound Stage-3 evidence contradicts the prior single-layer pipeline certificate; execute the existing Stage-2 capability repair before returning to exact-board validation.\",\n      \"vetoed_pre_llm_execution\": false\n    },\n    \"status\": \"ready\",\n    \"steps\": [\n      {\n        \"id\": \"repair_step.00\",\n        \"llm_disposition_constraint\": null,\n        \"repair_kind\": \"case_single_layer_functional\",\n        \"repair_phase\": null,\n        \"scope\": \"verification_capability_repair\",\n        \"status\": \"ready_for_agent_patch\"\n      }\n    ]\n  },\n  \"schema_version\": \"spatialaccagent.repair_plan.v0\",\n  \"status\": \"needs_repair\"\n}",
        "content_sha256": "94ae6f7f593cef84bf094412d94e7db66faafbf3f34c802d45e73ba0cabf20e0",
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/repair/repair_plan.json#current_repair_action_projection",
        "projection": true,
        "source_path": "accagent/runs/spatialacc_qwen_agent_fast_run/repair/repair_plan.json",
        "source_sha256": "8722ebe7df657484727b4878229247c33aad199a15d8e85681d3f967eef633fd",
        "truncated": false
      },
      {
        "bytes": 90958,
        "content": "{\n  \"functions\": [\n    \"allowed_capability_edit_target\",\n    \"apply_agent_file_edits\",\n    \"normalize_harness_sources\",\n    \"run_agent_requested_validation\",\n    \"harness_contract_errors\",\n    \"connected_harness_contract_errors\",\n    \"finalize_dut_weight_binding_manifest\"\n  ],\n  \"language\": \"python\",\n  \"source\": \"def allowed_capability_edit_target(\\n    path: Path,\\n    run_dir: Path,\\n    *,\\n    allow_template_repair: bool | None = None,\\n    allow_board_integration: bool = False,\\n) -> bool:\\n    resolved = path.resolve()\\n    harness_root = (run_dir / \\\"generated\\\" / \\\"semantic_harness\\\").resolve()\\n    harness_scala_root = (\\n        run_dir\\n        / \\\"generated\\\"\\n        / \\\"chisel\\\"\\n        / \\\"src\\\"\\n        / \\\"main\\\"\\n        / \\\"scala\\\"\\n        / \\\"spatialaccagent\\\"\\n        / \\\"semantic_harness\\\"\\n    ).resolve()\\n    binding_path = (run_dir / \\\"generated\\\" / \\\"memory\\\" / \\\"dut_weight_binding_manifest.json\\\").resolve()\\n    board_integration_root = (run_dir / \\\"generated\\\" / \\\"board_integration\\\").resolve()\\n    framework_template_root = (Path.cwd() / \\\"accagent\\\" / \\\"framework\\\" / \\\"templates\\\" / \\\"operator_chisel\\\").resolve()\\n    generated_template_root = (\\n        run_dir / \\\"generated\\\" / \\\"chisel\\\" / \\\"src\\\" / \\\"main\\\" / \\\"scala\\\" / \\\"spatialaccagent\\\" / \\\"templates\\\"\\n    ).resolve()\\n    approved_template = (\\n        (bounded_template_repair_approved() if allow_template_repair is None else allow_template_repair)\\n        and resolved.suffix == \\\".scala\\\"\\n        and resolved.is_file()\\n        and (resolved.is_relative_to(framework_template_root) or resolved.is_relative_to(generated_template_root))\\n    )\\n    return (\\n        resolved == binding_path\\n        or resolved.is_relative_to(harness_root)\\n        or resolved.is_relative_to(harness_scala_root)\\n        or (allow_board_integration and resolved.is_relative_to(board_integration_root))\\n        or approved_template\\n    )\\n\\n\\ndef apply_agent_file_edits(\\n    output: dict[str, Any],\\n    run_dir: Path,\\n    out_dir: Path,\\n    *,\\n    allowed_exact_files: set[Path] | None = None,\\n    required_exact_files: set[Path] | None = None,\\n    required_noop_json_merges: dict[Path, dict[str, Any]] | None = None,\\n    required_template_pairs: set[str] | None = None,\\n    instrumentation_only_template_pairs: set[str] | None = None,\\n    repair_checkpoint: dict[str, Any] | None = None,\\n    allow_template_repair: bool | None = None,\\n    allow_board_integration: bool = False,\\n    report_name: str = \\\"agent_patch_application.json\\\",\\n    agent_contract_blockers: list[str] | None = None,\\n    agent_contract_failure_class: str = \\\"agent_output_contract\\\",\\n) -> dict[str, Any]:\\n    raw_status = str(output.get(\\\"status\\\") or \\\"\\\")\\n    approvals = output.get(\\\"approval_required_for\\\", []) if isinstance(output.get(\\\"approval_required_for\\\"), list) else []\\n    edits = output.get(\\\"file_edits\\\", []) if isinstance(output.get(\\\"file_edits\\\"), list) else []\\n    declared_blockers = (\\n        output.get(\\\"blocked_reasons\\\", [])\\n        if isinstance(output.get(\\\"blocked_reasons\\\"), list)\\n        else []\\n    )\\n    status = normalized_implementation_agent_status(output)\\n    blockers: list[str] = [\\n        str(value) for value in (agent_contract_blockers or []) if str(value)\\n    ]\\n    staged: list[tuple[Path, str, str, str]] = []\\n    protocol_normalizations: list[dict[str, Any]] = []\\n    total_bytes = 0\\n    seen_edit_targets: set[Path] = set()\\n    normalized_required_noop_json_merges = {\\n        path.resolve(): copy.deepcopy(value)\\n        for path, value in (required_noop_json_merges or {}).items()\\n        if isinstance(value, dict)\\n    }\\n    acknowledged_required_noop_merges: dict[Path, dict[str, Any]] = {}\\n    acknowledged_optional_noop_merges: dict[Path, dict[str, Any]] = {}\\n    rejected_prior_failed_board_attempt: dict[str, Any] | None = None\\n    agent_transaction_rejection: dict[str, Any] | None = None\\n    retry_agent_without_real_tool = False\\n\\n    if status != raw_status:\\n        protocol_normalizations.append(\\n            {\\n                \\\"field\\\": \\\"status\\\",\\n                \\\"from\\\": raw_status,\\n                \\\"to\\\": status,\\n                \\\"guard\\\": \\\"nonempty file_edits with no approval or declared blocker\\\",\\n            }\\n        )\\n\\n    if status != \\\"ready_to_apply\\\":\\n        blockers.append(f\\\"implementation agent status is not ready_to_apply: {status}\\\")\\n    if approvals:\\n        blockers.append(f\\\"implementation agent requested approval: {approvals}\\\")\\n    if not edits:\\n        blockers.append(\\\"implementation agent returned no file edits\\\")\\n\\n    for index, edit in enumerate(edits):\\n        if not isinstance(edit, dict):\\n            blockers.append(f\\\"file_edits[{index}] is not an object\\\")\\n            continue\\n        raw_path = str(edit.get(\\\"path\\\") or \\\"\\\")\\n        target = Path(raw_path)\\n        target = target if target.is_absolute() else Path.cwd() / target\\n        target = target.resolve()\\n        if target in seen_edit_targets:\\n            blockers.append(\\n                f\\\"file_edits[{index}] duplicates an earlier resolved target: {target}\\\"\\n            )\\n            continue\\n        seen_edit_targets.add(target)\\n        operation = str(edit.get(\\\"operation\\\") or \\\"\\\")\\n        expected = str(edit.get(\\\"expected_sha256\\\") or \\\"\\\")\\n        content = str(edit.get(\\\"content\\\") or \\\"\\\")\\n        json_content_supplied = \\\"json_content\\\" in edit\\n        json_content = edit.get(\\\"json_content\\\")\\n        text_replacements_supplied = \\\"text_replacements\\\" in edit\\n        text_replacements = edit.get(\\\"text_replacements\\\")\\n        if not allowed_capability_edit_target(\\n            target,\\n            run_dir,\\n            allow_template_repair=allow_template_repair,\\n            allow_board_integration=allow_board_integration,\\n        ):\\n            blockers.append(f\\\"file_edits[{index}] target is outside the capability-repair write boundary: {target}\\\")\\n            continue\\n        if allowed_exact_files is not None and target not in allowed_exact_files:\\n            blockers.append(f\\\"file_edits[{index}] target is outside the current semantic repair phase: {target}\\\")\\n            continue\\n        if operation not in {\\\"create\\\", \\\"replace\\\", \\\"replace_text\\\", \\\"merge_json\\\"}:\\n            blockers.append(f\\\"file_edits[{index}] has unsupported operation: {operation}\\\")\\n            continue\\n        if operation == \\\"replace_text\\\" and json_content_supplied:\\n            blockers.append(\\n                f\\\"file_edits[{index}] replace_text cannot use json_content: {target}\\\"\\n            )\\n            continue\\n        if json_content_supplied:\\n            if target.suffix.lower() != \\\".json\\\":\\n                blockers.append(\\n                    f\\\"file_edits[{index}] json_content is allowed only for .json targets: {target}\\\"\\n                )\\n                continue\\n            if content:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] must use exactly one of content or json_content\\\"\\n                )\\n                continue\\n            if not isinstance(json_content, dict):\\n                blockers.append(f\\\"file_edits[{index}] json_content is not an object\\\")\\n                continue\\n            if operation != \\\"merge_json\\\":\\n                content = json.dumps(json_content, indent=2, sort_keys=True) + \\\"\\\\n\\\"\\n                protocol_normalizations.append(\\n                    {\\n                        \\\"field\\\": f\\\"file_edits[{index}].json_content\\\",\\n                        \\\"operation\\\": \\\"serialize_structured_json_content\\\",\\n                        \\\"guard\\\": \\\"target suffix is .json and string content is empty\\\",\\n                    }\\n                )\\n        elif operation == \\\"merge_json\\\":\\n            blockers.append(\\n                f\\\"file_edits[{index}] merge_json requires json_content: {target}\\\"\\n            )\\n            continue\\n        if operation == \\\"create\\\" and not target.exists() and expected == \\\"absent\\\":\\n            protocol_normalizations.append(\\n                {\\n                    \\\"field\\\": f\\\"file_edits[{index}].expected_sha256\\\",\\n                    \\\"from\\\": \\\"absent\\\",\\n                    \\\"to\\\": \\\"\\\",\\n                    \\\"guard\\\": \\\"operation=create and target does not exist\\\",\\n                }\\n            )\\n            expected = \\\"\\\"\\n        if target.exists() and operation not in {\\\"replace\\\", \\\"replace_text\\\", \\\"merge_json\\\"}:\\n            blockers.append(f\\\"file_edits[{index}] must use replace for existing file: {target}\\\")\\n            continue\\n        if not target.exists() and operation != \\\"create\\\":\\n            blockers.append(f\\\"file_edits[{index}] must use create for missing file: {target}\\\")\\n            continue\\n        if target.exists():\\n            actual = sha256_file(target)\\n            if not expected or expected != actual:\\n                blockers.append(f\\\"file_edits[{index}] expected hash does not match {target}\\\")\\n                continue\\n        elif expected:\\n            blockers.append(f\\\"file_edits[{index}] create operation must use an empty expected_sha256\\\")\\n            continue\\n        if operation == \\\"merge_json\\\":\\n            if text_replacements_supplied:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] merge_json cannot use text_replacements: {target}\\\"\\n                )\\n                continue\\n            try:\\n                current_json = json.loads(target.read_text(encoding=\\\"utf-8\\\"))\\n            except (OSError, UnicodeError, json.JSONDecodeError) as exc:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] merge_json cannot read current JSON object {target}: {exc}\\\"\\n                )\\n                continue\\n            if not isinstance(current_json, dict):\\n                blockers.append(\\n                    f\\\"file_edits[{index}] merge_json target is not a JSON object: {target}\\\"\\n                )\\n                continue\\n            required_authority_patch = normalized_required_noop_json_merges.get(\\n                target\\n            )\\n            if (\\n                required_authority_patch is not None\\n                and json_content != required_authority_patch\\n            ):\\n                protocol_normalizations.append(\\n                    {\\n                        \\\"field\\\": f\\\"file_edits[{index}].json_content\\\",\\n                        \\\"operation\\\": (\\n                            \\\"bind_framework_owned_checkpoint_contract_authority\\\"\\n                        ),\\n                        \\\"agent_supplied_patch_sha256\\\": canonical_contract_sha256(\\n                            json_content\\n                        ),\\n                        \\\"authority_patch_sha256\\\": canonical_contract_sha256(\\n                            required_authority_patch\\n                        ),\\n                        \\\"guard\\\": (\\n                            \\\"the complete checkpoint manifest contract is framework-owned; \\\"\\n                            \\\"the Agent merge declares intent but cannot change adapter paths, \\\"\\n                            \\\"hashes, ABI invariants, or the framework-derived DUT root\\\"\\n                        ),\\n                    }\\n                )\\n                json_content = copy.deepcopy(required_authority_patch)\\n            merged_json = _deep_merge_json_object(current_json, json_content)\\n            if merged_json == current_json:\\n                required_noop_patch = normalized_required_noop_json_merges.get(\\n                    target\\n                )\\n                required_noop_acknowledgement = (\\n                    required_exact_files is not None\\n                    and target in {path.resolve() for path in required_exact_files}\\n                    and required_noop_patch is not None\\n                    and json_content == required_noop_patch\\n                )\\n                provenance_binding = (\\n                    _bind_current_exact_board_generation_provenance(\\n                        merged_json,\\n                        out_dir,\\n                    )\\n                    if allow_board_integration\\n                    and target.name == \\\"dut_weight_binding_manifest.json\\\"\\n                    and _exact_board_generation_provenance_rebind_intent(\\n                        json_content\\n                    )\\n                    else None\\n                )\\n                if provenance_binding is None and not required_noop_acknowledgement:\\n                    acknowledged_optional_noop_merges[target] = {\\n                        \\\"edit_index\\\": index,\\n                        \\\"patch_sha256\\\": canonical_contract_sha256(json_content),\\n                    }\\n                    continue\\n                if provenance_binding is not None:\\n                    protocol_normalizations.append(provenance_binding)\\n                if required_noop_acknowledgement:\\n                    acknowledged_required_noop_merges[target] = {\\n                        \\\"patch_sha256\\\": canonical_contract_sha256(json_content),\\n                    }\\n            content = json.dumps(merged_json, indent=2, sort_keys=True) + \\\"\\\\n\\\"\\n            protocol_normalizations.append(\\n                {\\n                    \\\"field\\\": f\\\"file_edits[{index}].json_content\\\",\\n                    \\\"operation\\\": \\\"materialize_hash_bound_deep_json_merge\\\",\\n                    \\\"patch_sha256\\\": canonical_contract_sha256(json_content),\\n                    \\\"patched_leaf_paths\\\": _json_patch_leaf_paths(json_content),\\n                    \\\"guard\\\": (\\n                        \\\"pre-edit SHA-256 matched, target and patch were JSON objects, \\\"\\n                        \\\"explicit object keys were recursively merged, and omitted fields \\\"\\n                        \\\"were preserved without implicit deletion\\\"\\n                    ),\\n                }\\n            )\\n        elif operation == \\\"replace_text\\\":\\n            if target.suffix.lower() == \\\".json\\\":\\n                blockers.append(\\n                    f\\\"file_edits[{index}] replace_text is not allowed for JSON: {target}\\\"\\n                )\\n                continue\\n            if content:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] replace_text must use empty content: {target}\\\"\\n                )\\n                continue\\n            if not isinstance(text_replacements, list) or not text_replacements:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] replace_text has no text_replacements: {target}\\\"\\n                )\\n                continue\\n            try:\\n                before_text = target.read_text(encoding=\\\"utf-8\\\")\\n            except (OSError, UnicodeError) as exc:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] replace_text cannot read UTF-8 source {target}: {exc}\\\"\\n                )\\n                continue\\n            replacement_records: list[dict[str, Any]] = []\\n            replacement_error = False\\n            for replacement_index, replacement in enumerate(text_replacements):\\n                if not isinstance(replacement, dict):\\n                    blockers.append(\\n                        f\\\"file_edits[{index}].text_replacements[{replacement_index}] is not an object\\\"\\n                    )\\n                    replacement_error = True\\n                    break\\n                old_text = replacement.get(\\\"old_text\\\")\\n                new_text = replacement.get(\\\"new_text\\\")\\n                if not isinstance(old_text, str) or not old_text:\\n                    blockers.append(\\n                        f\\\"file_edits[{index}].text_replacements[{replacement_index}].old_text is empty or invalid\\\"\\n                    )\\n                    replacement_error = True\\n                    break\\n                if not isinstance(new_text, str):\\n                    blockers.append(\\n                        f\\\"file_edits[{index}].text_replacements[{replacement_index}].new_text is invalid\\\"\\n                    )\\n                    replacement_error = True\\n                    break\\n                match_count = before_text.count(old_text)\\n                if match_count != 1:\\n                    blockers.append(\\n                        f\\\"file_edits[{index}].text_replacements[{replacement_index}].old_text must match exactly once in sequence; found {match_count}\\\"\\n                    )\\n                    replacement_error = True\\n                    break\\n                if old_text == new_text:\\n                    blockers.append(\\n                        f\\\"file_edits[{index}].text_replacements[{replacement_index}] does not change the source\\\"\\n                    )\\n                    replacement_error = True\\n                    break\\n                start = before_text.find(old_text)\\n                replacement_records.append(\\n                    {\\n                        \\\"replacement_index\\\": replacement_index,\\n                        \\\"start\\\": start,\\n                        \\\"end\\\": start + len(old_text),\\n                        \\\"old_text_sha256\\\": hashlib.sha256(\\n                            old_text.encode(\\\"utf-8\\\")\\n                        ).hexdigest(),\\n                        \\\"new_text_sha256\\\": hashlib.sha256(\\n                            new_text.encode(\\\"utf-8\\\")\\n                        ).hexdigest(),\\n                    }\\n                )\\n            if replacement_error:\\n                continue\\n            ordered_records = sorted(replacement_records, key=lambda row: row[\\\"start\\\"])\\n            for prior, current in zip(ordered_records, ordered_records[1:]):\\n                if current[\\\"start\\\"] < prior[\\\"end\\\"]:\\n                    blockers.append(\\n                        f\\\"file_edits[{index}] replace_text anchors overlap in the pre-edit source\\\"\\n                    )\\n                    replacement_error = True\\n                    break\\n            if replacement_error:\\n                continue\\n            patched_text = before_text\\n            for record in reversed(ordered_records):\\n                replacement = text_replacements[record[\\\"replacement_index\\\"]]\\n                patched_text = (\\n                    patched_text[: record[\\\"start\\\"]]\\n                    + replacement[\\\"new_text\\\"]\\n                    + patched_text[record[\\\"end\\\"] :]\\n                )\\n            if patched_text == before_text:\\n                blockers.append(\\n                    f\\\"file_edits[{index}] replace_text leaves the source unchanged: {target}\\\"\\n                )\\n                continue\\n            content = patched_text\\n            protocol_normalizations.append(\\n                {\\n                    \\\"field\\\": f\\\"file_edits[{index}].text_replacements\\\",\\n                    \\\"operation\\\": \\\"materialize_hash_bound_unique_text_replacements\\\",\\n                    \\\"replacement_count\\\": len(replacement_records),\\n                    \\\"replacements\\\": [\\n                        {\\n                            key: value\\n                            for key, value in record.items()\\n                            if key not in {\\\"start\\\", \\\"end\\\"}\\n                        }\\n                        for record in replacement_records\\n                    ],\\n                    \\\"guard\\\": (\\n                        \\\"pre-edit SHA-256 matched, every old_text matched exactly once \\\"\\n                        \\\"in the original source, anchors did not overlap, and replacements \\\"\\n                        \\\"were materialized by descending original offset\\\"\\n                    ),\\n                }\\n            )\\n        elif text_replacements_supplied:\\n            blockers.append(\\n                f\\\"file_edits[{index}] text_replacements requires operation=replace_text\\\"\\n            )\\n            continue\\n        if not content:\\n            blockers.append(f\\\"file_edits[{index}] content is empty: {target}\\\")\\n            continue\\n        if (\\n            allow_board_integration\\n            and target.name == \\\"dut_weight_binding_manifest.json\\\"\\n            and operation == \\\"replace\\\"\\n            and target.is_file()\\n        ):\\n            prior_manifest = read_json_if_exists(target)\\n            try:\\n                agent_manifest = json.loads(content)\\n            except json.JSONDecodeError:\\n                agent_manifest = None\\n            if (\\n                (\\n                    prior_manifest.get(\\\"status\\\") == \\\"pass\\\"\\n                    or board_only_incomplete_lower_layer_bindings_attested(\\n                        target,\\n                        prior_manifest,\\n                        out_dir,\\n                    )\\n                )\\n                and isinstance(agent_manifest, dict)\\n                and isinstance(prior_manifest.get(\\\"stage_harnesses\\\"), dict)\\n                and isinstance(prior_manifest.get(\\\"single_layer_harness\\\"), dict)\\n            ):\\n                preserved_fields = CERTIFIED_LOWER_LAYER_BINDING_FIELDS\\n                agent_manifest = preserve_certified_lower_layer_binding_fields(\\n                    agent_manifest,\\n                    prior_manifest,\\n                )\\n                content = json.dumps(agent_manifest, indent=2, sort_keys=True) + \\\"\\\\n\\\"\\n                protocol_normalizations.append(\\n                    {\\n                        \\\"field\\\": f\\\"file_edits[{index}].content\\\",\\n                        \\\"operation\\\": \\\"preserve_certified_lower_layer_bindings\\\",\\n                        \\\"preserved_fields\\\": list(preserved_fields),\\n                        \\\"certified_manifest_sha256\\\": actual,\\n                        \\\"guard\\\": (\\n                            \\\"board manifest replace over a certified lower-layer manifest with \\\"\\n                            \\\"complete stage and single-layer bindings\\\"\\n                        ),\\n                    }\\n                )\\n            if isinstance(agent_manifest, dict):\\n                (\\n                    generation_record_path,\\n                    generation_record,\\n                    trusted_generation,\\n                ) = select_trusted_exact_board_generation_record(\\n                    out_dir,\\n                    expected_status=\\\"ready_to_apply\\\",\\n                )\\n                harness = agent_manifest.get(\\\"multilayer_harness\\\")\\n                if (\\n                    trusted_generation.get(\\\"status\\\") == \\\"pass\\\"\\n                    and isinstance(harness, dict)\\n                ):\\n                    harness[\\\"generation_provenance\\\"] = {\\n                        \\\"mode\\\": \\\"llm\\\",\\n                        \\\"agent_id\\\": generation_record.get(\\\"agent\\\"),\\n                        \\\"model\\\": generation_record.get(\\\"model\\\"),\\n                        \\\"used_fallback\\\": generation_record.get(\\\"used_fallback\\\"),\\n                        \\\"prompt_sha256\\\": trusted_generation.get(\\\"prompt_sha256\\\"),\\n                        \\\"prompt_path\\\": trusted_generation.get(\\\"prompt_path\\\"),\\n                        \\\"record_path\\\": str(generation_record_path),\\n                        \\\"record_sha256\\\": trusted_generation.get(\\\"sha256\\\"),\\n                    }\\n                    content = json.dumps(\\n                        agent_manifest, indent=2, sort_keys=True\\n                    ) + \\\"\\\\n\\\"\\n                    protocol_normalizations.append(\\n                        {\\n                            \\\"field\\\": f\\\"file_edits[{index}].content\\\",\\n                            \\\"operation\\\": \\\"bind_exact_board_llm_generation_provenance\\\",\\n                            \\\"trusted_generation_record\\\": str(\\n                                generation_record_path\\n                            ),\\n                            \\\"trusted_generation_record_sha256\\\": (\\n                                trusted_generation.get(\\\"sha256\\\")\\n                            ),\\n                            \\\"prompt_sha256\\\": trusted_generation.get(\\n                                \\\"prompt_sha256\\\"\\n                            ),\\n                            \\\"guard\\\": (\\n                                \\\"current exact-board generation record is a \\\"\\n                                \\\"non-fallback ready_to_apply LLM record with \\\"\\n                                \\\"hash-verified prompt\\\"\\n                            ),\\n                        }\\n                    )\\n        total_bytes += len(content.encode(\\\"utf-8\\\"))\\n        if total_bytes > 2_000_000:\\n            blockers.append(\\\"implementation patch exceeds the 2 MB bounded-repair limit\\\")\\n            continue\\n        if target.name == \\\"dut_weight_binding_manifest.json\\\":\\n            try:\\n                parsed = json.loads(content)\\n                if not isinstance(parsed, dict):\\n                    raise ValueError(\\\"manifest is not an object\\\")\\n            except (json.JSONDecodeError, ValueError) as exc:\\n                blockers.append(f\\\"DUT weight-binding manifest is invalid JSON: {exc}\\\")\\n                continue\\n        staged.append((target, content, operation, expected))\\n\\n    if acknowledged_optional_noop_merges:\\n        materially_changed_paths = {\\n            target\\n            for target, content, _, expected in staged\\n            if not expected\\n            or hashlib.sha256(content.encode(\\\"utf-8\\\")).hexdigest() != expected\\n        }\\n        if not materially_changed_paths:\\n            for target, evidence in acknowledged_optional_noop_merges.items():\\n                blockers.append(\\n                    f\\\"file_edits[{evidence['edit_index']}] merge_json leaves the JSON object unchanged: {target}\\\"\\n                )\\n        else:\\n            for target, evidence in sorted(\\n                acknowledged_optional_noop_merges.items(),\\n                key=lambda row: str(row[0]),\\n            ):\\n                protocol_normalizations.append(\\n                    {\\n                        \\\"field\\\": str(target),\\n                        \\\"operation\\\": \\\"omit_hash_bound_noop_json_merge\\\",\\n                        \\\"patch_sha256\\\": evidence[\\\"patch_sha256\\\"],\\n                        \\\"paired_material_edit_paths\\\": sorted(\\n                            str(path) for path in materially_changed_paths\\n                        ),\\n                        \\\"guard\\\": (\\n                            \\\"the pre-edit hash matched, the deep JSON merge was exactly \\\"\\n                            \\\"idempotent, and another target changed materially in the same \\\"\\n                            \\\"validated atomic batch\\\"\\n                        ),\\n                    }\\n                )\\n\\n    if acknowledged_required_noop_merges:\\n        normalized_required = {\\n            path.resolve() for path in (required_exact_files or set())\\n        }\\n        materially_changed_required_paths = {\\n            target\\n            for target, content, _, expected in staged\\n            if target in normalized_required\\n            and target not in acknowledged_required_noop_merges\\n            and (\\n                not expected\\n                or hashlib.sha256(content.encode(\\\"utf-8\\\")).hexdigest()\\n                != expected\\n            )\\n        }\\n        if not materially_changed_required_paths:\\n            blockers.append(\\n                \\\"required checkpoint manifest no-op acknowledgement requires a \\\"\\n                \\\"materially changed paired atomic edit target\\\"\\n            )\\n        else:\\n            for target, evidence in sorted(\\n                acknowledged_required_noop_merges.items(),\\n                key=lambda row: str(row[0]),\\n            ):\\n                protocol_normalizations.append(\\n                    {\\n                        \\\"field\\\": str(target),\\n                        \\\"operation\\\": \\\"acknowledge_authority_exact_checkpoint_contract\\\",\\n                        \\\"patch_sha256\\\": evidence[\\\"patch_sha256\\\"],\\n                        \\\"paired_material_edit_paths\\\": sorted(\\n                            str(path) for path in materially_changed_required_paths\\n                        ),\\n                        \\\"guard\\\": (\\n                            \\\"checkpoint-specialist mode explicitly authorized this exact \\\"\\n                            \\\"required manifest patch, the current manifest already contained \\\"\\n                            \\\"the identical contract, and another required target changed \\\"\\n                            \\\"materially in the same atomic batch\\\"\\n                        ),\\n                    }\\n                )\\n\\n    if required_exact_files is not None:\\n        normalized_required = {path.resolve() for path in required_exact_files}\\n        agent_staged_paths = {target for target, _, _, _ in staged}\\n        for missing in sorted(normalized_required - agent_staged_paths):\\n            blockers.append(\\n                \\\"implementation patch is missing a required atomic edit target: \\\"\\n                f\\\"{missing}\\\"\\n            )\\n\\n    if allow_board_integration and staged:\\n        board_root = (run_dir / \\\"generated\\\" / \\\"board_integration\\\").resolve()\\n        manifest_path = (\\n            run_dir / \\\"generated\\\" / \\\"memory\\\" / \\\"dut_weight_binding_manifest.json\\\"\\n        ).resolve()\\n        staged_paths = {target for target, _, _, _ in staged}\\n        board_source_changed = any(\\n            target.is_relative_to(board_root)\\n            and target.suffix.lower() in BOARD_INTEGRATION_SOURCE_SUFFIXES\\n            for target in staged_paths\\n        )\\n        if board_source_changed and manifest_path not in staged_paths:\\n            if manifest_path.is_file():\\n                try:\\n                    manifest_content = manifest_path.read_text(encoding=\\\"utf-8\\\")\\n                except (OSError, UnicodeError) as exc:\\n                    blockers.append(\\n                        f\\\"current board binding manifest cannot be read for deterministic hash rebinding: {exc}\\\"\\n                    )\\n                else:\\n                    staged.append(\\n                        (\\n                            manifest_path,\\n                            manifest_content,\\n                            \\\"replace\\\",\\n                            sha256_file(manifest_path),\\n                        )\\n                    )\\n                    protocol_normalizations.append(\\n                        {\\n                            \\\"field\\\": \\\"dut_weight_binding_manifest.json\\\",\\n                            \\\"operation\\\": \\\"stage_existing_manifest_for_board_source_hash_rebinding\\\",\\n                            \\\"guard\\\": (\\n                                \\\"an agent-owned board source changed while the semantic \\\"\\n                                \\\"manifest contract remained unchanged\\\"\\n                            ),\\n                        }\\n                    )\\n        staged_by_path = {target: content for target, content, _, _ in staged}\\n        normalized_staged: list[tuple[Path, str, str, str]] = []\\n        for target, content, operation, expected in staged:\\n            if target.name != \\\"dut_weight_binding_manifest.json\\\":\\n                normalized_staged.append((target, content, operation, expected))\\n                continue\\n            try:\\n                manifest = json.loads(content)\\n            except json.JSONDecodeError:\\n                normalized_staged.append((target, content, operation, expected))\\n                continue\\n            provenance_already_bound = any(\\n                isinstance(row, dict)\\n                and row.get(\\\"operation\\\")\\n                == \\\"bind_exact_board_llm_generation_provenance\\\"\\n                for row in protocol_normalizations\\n            )\\n            harness = manifest.get(\\\"multilayer_harness\\\")\\n            if not provenance_already_bound and isinstance(harness, dict):\\n                (\\n                    generation_record_path,\\n                    generation_record,\\n                    trusted_generation,\\n                ) = select_trusted_exact_board_generation_record(\\n                    out_dir,\\n                    expected_status=\\\"ready_to_apply\\\",\\n                )\\n                if trusted_generation.get(\\\"status\\\") == \\\"pass\\\":\\n                    harness[\\\"generation_provenance\\\"] = {\\n                        \\\"mode\\\": \\\"llm\\\",\\n                        \\\"agent_id\\\": generation_record.get(\\\"agent\\\"),\\n                        \\\"model\\\": generation_record.get(\\\"model\\\"),\\n                        \\\"used_fallback\\\": generation_record.get(\\\"used_fallback\\\"),\\n                        \\\"prompt_sha256\\\": trusted_generation.get(\\\"prompt_sha256\\\"),\\n                        \\\"prompt_path\\\": trusted_generation.get(\\\"prompt_path\\\"),\\n                        \\\"record_path\\\": str(generation_record_path),\\n                        \\\"record_sha256\\\": trusted_generation.get(\\\"sha256\\\"),\\n                    }\\n                    protocol_normalizations.append(\\n                        {\\n                            \\\"field\\\": \\\"dut_weight_binding_manifest.json\\\",\\n                            \\\"operation\\\": \\\"bind_exact_board_llm_generation_provenance\\\",\\n                            \\\"trusted_generation_record\\\": str(\\n                                generation_record_path\\n                            ),\\n                            \\\"trusted_generation_record_sha256\\\": (\\n                                trusted_generation.get(\\\"sha256\\\")\\n                            ),\\n                            \\\"prompt_sha256\\\": trusted_generation.get(\\n                                \\\"prompt_sha256\\\"\\n                            ),\\n                            \\\"guard\\\": (\\n                                \\\"an exact-board RTL repair auto-staged the semantic \\\"\\n                                \\\"manifest and the hash-bound generation record is a \\\"\\n                                \\\"non-fallback ready_to_apply LLM result\\\"\\n                            ),\\n                        }\\n                    )\\n            board_plan = manifest.get(\\\"board_simulation_preflight_plan\\\")\\n            if isinstance(board_plan, dict):\\n                board_testbench = (\\n                    board_plan.get(\\\"testbench\\\", {})\\n                    if isinstance(board_plan.get(\\\"testbench\\\"), dict)\\n                    else {}\\n                )\\n                declared_checkpoint_contract = board_testbench.get(\\n                    \\\"simulation_checkpoint_contract\\\"\\n                )\\n                if declared_checkpoint_contract is not None:\\n                    if not isinstance(declared_checkpoint_contract, dict):\\n                        blockers.append(\\n                            \\\"simulation checkpoint contract in the board manifest is not an object\\\"\\n                        )\\n                    else:\\n                        blockers.extend(\\n                            \\\"simulation_checkpoint_contract: \\\" + error\\n                            for error in checkpoint_contract_errors(\\n                                declared_checkpoint_contract\\n                            )\\n                        )\\n                missing_prerequisites = framework_vcs_plan_binding_missing_prerequisites(\\n                    run_dir,\\n                    str(\\n                        board_plan.get(\\\"validation_mode\\\")\\n                        or \\\"exact_sample_physical_ddr\\\"\\n                    ),\\n                )\\n                if missing_prerequisites:\\n                    blockers.append(\\n                        \\\"framework VCS-plan binding prerequisites are missing: \\\"\\n                        + \\\"; \\\".join(missing_prerequisites)\\n                    )\\n                else:\\n                    manifest, vcs_binding = bind_framework_vcs_compile_plan(\\n                        manifest,\\n                        run_dir,\\n                        out_dir,\\n                        target,\\n                    )\\n                    blockers.extend(vcs_binding.get(\\\"blockers\\\", []))\\n                    if vcs_binding.get(\\\"status\\\") == \\\"pass\\\":\\n                        protocol_normalizations.append(\\n                            {\\n                                \\\"field\\\": (\\n                                    \\\"dut_weight_binding_manifest.json.\\\"\\n                                    \\\"board_simulation_preflight_plan.vcs_compile_plan\\\"\\n                                ),\\n                                \\\"operation\\\": \\\"bind_framework_vcs_compile_plan\\\",\\n                                \\\"ordered_command_count\\\": vcs_binding.get(\\n                                    \\\"ordered_command_count\\\"\\n                                ),\\n                                \\\"compile_source_count\\\": vcs_binding.get(\\n                                    \\\"compile_source_count\\\"\\n                                ),\\n                                \\\"vcs_compile_plan_sha256\\\": vcs_binding.get(\\n                                    \\\"vcs_compile_plan_sha256\\\"\\n                                ),\\n                                \\\"guard\\\": (\\n                                    \\\"plan is regenerated from the agent-selected source replacement, \\\"\\n                                    \\\"fixture selection and testbench top plus immutable Vivado/fixture authority\\\"\\n                                ),\\n                            }\\n                        )\\n            manifest, binding = bind_agent_owned_board_source_hashes(\\n                manifest,\\n                run_dir,\\n                staged_by_path,\\n            )\\n            blockers.extend(binding[\\\"blockers\\\"])\\n            content = json.dumps(manifest, indent=2, sort_keys=True) + \\\"\\\\n\\\"\\n            normalized_staged.append((target, content, operation, expected))\\n            if binding[\\\"bound_source_ids\\\"]:\\n                protocol_normalizations.append(\\n                    {\\n                        \\\"field\\\": \\\"dut_weight_binding_manifest.json\\\",\\n                        \\\"operation\\\": \\\"bind_agent_owned_board_source_hashes\\\",\\n                        \\\"bound_source_ids\\\": binding[\\\"bound_source_ids\\\"],\\n                        \\\"guard\\\": (\\n                            \\\"board source identity is inside generated/board_integration \\\"\\n                            \\\"and its final content is available in the same staged edit or on disk\\\"\\n                        ),\\n                    }\\n                )\\n        staged = normalized_staged\\n        total_bytes = sum(len(content.encode(\\\"utf-8\\\")) for _, content, _, _ in staged)\\n        if total_bytes > 2_000_000 and \\\"implementation patch exceeds the 2 MB bounded-repair limit\\\" not in blockers:\\n            blockers.append(\\\"implementation patch exceeds the 2 MB bounded-repair limit\\\")\\n\\n    if required_template_pairs is not None:\\n        framework_root = (Path.cwd() / \\\"accagent\\\" / \\\"framework\\\" / \\\"templates\\\" / \\\"operator_chisel\\\").resolve()\\n        generated_root = (\\n            run_dir / \\\"generated\\\" / \\\"chisel\\\" / \\\"src\\\" / \\\"main\\\" / \\\"scala\\\" / \\\"spatialaccagent\\\" / \\\"templates\\\"\\n        ).resolve()\\n        staged_by_path = {target: content for target, content, _, _ in staged}\\n        edited_names = {\\n            target.name\\n            for target in staged_by_path\\n            if target.is_relative_to(framework_root) or target.is_relative_to(generated_root)\\n        }\\n        for name in sorted(required_template_pairs | edited_names):\\n            persistent = framework_root / name\\n            generated = generated_root / name\\n            if persistent not in staged_by_path or generated not in staged_by_path:\\n                blockers.append(f\\\"semantic template repair must replace both persistent/generated copies of {name}\\\")\\n                continue\\n            if staged_by_path[persistent] != staged_by_path[generated]:\\n                blockers.append(f\\\"persistent/generated semantic template contents differ for {name}\\\")\\n\\n    if instrumentation_only_template_pairs is not None:\\n        framework_root = (Path.cwd() / \\\"accagent\\\" / \\\"framework\\\" / \\\"templates\\\" / \\\"operator_chisel\\\").resolve()\\n        generated_root = (\\n            run_dir / \\\"generated\\\" / \\\"chisel\\\" / \\\"src\\\" / \\\"main\\\" / \\\"scala\\\" / \\\"spatialaccagent\\\" / \\\"templates\\\"\\n        ).resolve()\\n        staged_by_path = {target: content for target, content, _, _ in staged}\\n        for name in sorted(instrumentation_only_template_pairs):\\n            persistent = framework_root / name\\n            generated = generated_root / name\\n            if persistent not in staged_by_path or generated not in staged_by_path:\\n                continue\\n            before = persistent.read_text(encoding=\\\"utf-8\\\")\\n            blockers.extend(\\n                f\\\"{name}: {error}\\\"\\n                for error in template_trace_instrumentation_errors(\\n                    before,\\n                    staged_by_path[persistent],\\n                )\\n            )\\n\\n    if allow_board_integration and staged and not blockers:\\n        staged_contents = {\\n            target: content for target, content, _, _ in staged\\n        }\\n        candidate_state = exact_board_source_state(\\n            run_dir,\\n            staged_contents=staged_contents,\\n        )\\n        if candidate_state.get(\\\"candidate_changed_paths\\\"):\\n            prior_attempt = matching_failed_exact_board_attempt(\\n                run_dir,\\n                candidate_state,\\n            )\\n            if prior_attempt is not None:\\n                rejected_prior_failed_board_attempt = {\\n                    key: copy.deepcopy(prior_attempt.get(key))\\n                    for key in (\\n                        \\\"iteration\\\",\\n                        \\\"iteration_record\\\",\\n                        \\\"board_source_state\\\",\\n                        \\\"board_source_edits\\\",\\n                        \\\"agent_hypothesis\\\",\\n                        \\\"behavior_signature\\\",\\n                        \\\"runner_identity\\\",\\n                    )\\n                }\\n                rejected_prior_failed_board_attempt[\\\"candidate_board_source_state\\\"] = (\\n                    candidate_state\\n                )\\n                retry_agent_without_real_tool = True\\n                blockers.append(\\n                    \\\"agent board-source candidate exactly restores a prior \\\"\\n                    f\\\"real-VCS failed source state from repair iteration \\\"\\n                    f\\\"{prior_attempt.get('iteration')}; return this negative evidence \\\"\\n                    \\\"to the same agent without writing files or relaunching the real tool\\\"\\n                )\\n\\n    normalized_required = {\\n        path.resolve() for path in (required_exact_files or set())\\n    }\\n    replace_text_contract_markers = (\\n        \\\"replace_text cannot use json_content\\\",\\n        \\\"replace_text must use empty content\\\",\\n        \\\"replace_text has no text_replacements\\\",\\n        \\\".text_replacements[\\\",\\n        \\\"replace_text anchors overlap\\\",\\n        \\\"text_replacements requires operation=replace_text\\\",\\n    )\\n    replace_text_contract_blockers = [\\n        blocker\\n        for blocker in blockers\\n        if blocker.startswith(\\\"file_edits[\\\")\\n        and any(marker in blocker for marker in replace_text_contract_markers)\\n    ]\\n    checkpoint_transaction_cascade = (\\n        \\\"required checkpoint manifest no-op acknowledgement requires a \\\"\\n        \\\"materially changed paired atomic edit target\\\",\\n        \\\"implementation patch is missing a required atomic edit target:\\\",\\n    )\\n    checkpoint_transaction_blockers_only = bool(replace_text_contract_blockers) and all(\\n        blocker in replace_text_contract_blockers\\n        or blocker.startswith(checkpoint_transaction_cascade)\\n        for blocker in blockers\\n    )\\n    if (\\n        status == \\\"ready_to_apply\\\"\\n        and not approvals\\n        and not declared_blockers\\n        and len(normalized_required) == 2\\n        and len(normalized_required_noop_json_merges) == 1\\n        and checkpoint_transaction_blockers_only\\n        and set(seen_edit_targets) == normalized_required\\n    ):\\n        manifest_path = next(iter(normalized_required_noop_json_merges))\\n        paired_path = next(iter(normalized_required - {manifest_path}), None)\\n        indexed_edits: dict[Path, dict[str, Any]] = {}\\n        for edit in edits:\\n            if not isinstance(edit, dict):\\n                continue\\n            raw_target = Path(str(edit.get(\\\"path\\\") or \\\"\\\"))\\n            target = (\\n                raw_target if raw_target.is_absolute() else Path.cwd() / raw_target\\n            ).resolve()\\n            indexed_edits[target] = edit\\n        manifest_edit = indexed_edits.get(manifest_path, {})\\n        paired_edit = indexed_edits.get(paired_path, {}) if paired_path else {}\\n        if (\\n            manifest_path in acknowledged_required_noop_merges\\n            and manifest_edit.get(\\\"operation\\\") == \\\"merge_json\\\"\\n            and paired_path is not None\\n            and paired_edit.get(\\\"operation\\\") == \\\"replace_text\\\"\\n            and all(path.is_file() for path in normalized_required)\\n        ):\\n            retry_agent_without_real_tool = True\\n            agent_transaction_rejection = {\\n                \\\"schema_version\\\": \\\"spatialaccagent.agent_transaction_rejection.v1\\\",\\n                \\\"status\\\": \\\"ready_for_agent_retry\\\",\\n                \\\"failure_class\\\": \\\"checkpoint_atomic_replace_text_contract\\\",\\n                \\\"blockers\\\": copy.deepcopy(blockers),\\n                \\\"file_edits_were_not_applied\\\": True,\\n                \\\"real_tool_replay_required_before_retry\\\": False,\\n                \\\"unchanged_pre_edit_files\\\": [\\n                    {\\n                        \\\"path\\\": str(path),\\n                        \\\"sha256\\\": sha256_file(path),\\n                    }\\n                    for path in sorted(normalized_required)\\n                ],\\n            }\\n\\n    if agent_contract_blockers and status == \\\"ready_to_apply\\\" and not approvals:\\n        retry_agent_without_real_tool = True\\n        agent_transaction_rejection = {\\n            \\\"schema_version\\\": \\\"spatialaccagent.agent_transaction_rejection.v1\\\",\\n            \\\"status\\\": \\\"ready_for_agent_retry\\\",\\n            \\\"failure_class\\\": agent_contract_failure_class,\\n            \\\"blockers\\\": list(dict.fromkeys(blockers)),\\n            \\\"file_edits_were_not_applied\\\": True,\\n            \\\"real_tool_replay_required_before_retry\\\": False,\\n            \\\"unchanged_pre_edit_files\\\": [\\n                {\\n                    \\\"path\\\": str(path),\\n                    \\\"sha256\\\": sha256_file(path),\\n                }\\n                for path in sorted(seen_edit_targets)\\n                if path.is_file()\\n            ],\\n        }\\n\\n    records = []\\n    if not blockers:\\n        ordered_staged = sorted(\\n            staged,\\n            key=lambda row: row[0].name == \\\"dut_weight_binding_manifest.json\\\",\\n        )\\n        for target, content, operation, expected in ordered_staged:\\n            target.parent.mkdir(parents=True, exist_ok=True)\\n            temp = target.with_name(f\\\".{target.name}.spatialaccagent.tmp\\\")\\n            temp.write_text(content, encoding=\\\"utf-8\\\")\\n            temp.replace(target)\\n            records.append(\\n                {\\n                    \\\"path\\\": str(target),\\n                    \\\"operation\\\": operation,\\n                    \\\"before_sha256\\\": expected or None,\\n                    \\\"after_sha256\\\": sha256_file(target),\\n                    \\\"bytes\\\": target.stat().st_size,\\n                }\\n            )\\n\\n    report = {\\n        \\\"schema_version\\\": \\\"spatialaccagent.agent_patch_application.v1\\\",\\n        \\\"status\\\": \\\"pass\\\" if not blockers else \\\"blocked\\\",\\n        \\\"agent_status\\\": status,\\n        \\\"raw_agent_status\\\": raw_status,\\n        \\\"protocol_normalizations\\\": protocol_normalizations,\\n        \\\"files\\\": records,\\n        \\\"blockers\\\": blockers,\\n        \\\"retry_agent_without_real_tool\\\": retry_agent_without_real_tool,\\n        \\\"rejected_prior_failed_board_attempt\\\": (\\n            rejected_prior_failed_board_attempt\\n        ),\\n        \\\"agent_transaction_rejection\\\": agent_transaction_rejection,\\n        \\\"requested_validation\\\": output.get(\\\"requested_validation\\\", []),\\n        \\\"repair_checkpoint\\\": repair_checkpoint,\\n        \\\"policy\\\": {\\n            \\\"all_edits_validated_before_any_write\\\": True,\\n            \\\"golden_reference_input_policy_and_verification_reports_are_read_only\\\": True,\\n            \\\"existing_generated_dut_rtl_is_read_only_for_capability_repair\\\": True,\\n            \\\"bounded_selected_template_repair_approved\\\": (\\n                bounded_template_repair_approved()\\n                if allow_template_repair is None\\n                else allow_template_repair\\n            ),\\n            \\\"semantic_selected_template_repair_approved\\\": (\\n                semantic_template_repair_approved()\\n                if allow_template_repair is None\\n                else allow_template_repair and semantic_template_repair_approved()\\n            ),\\n            \\\"template_repair_must_preserve_external_architecture_stage_order_memory_runtime_and_numeric_contracts\\\": True,\\n            \\\"template_instrumentation_blocks_are_mechanically_non_functional\\\": (\\n                instrumentation_only_template_pairs is not None\\n            ),\\n            \\\"exact_text_replacements_require_pre_edit_hash_and_unique_anchors\\\": True,\\n            \\\"board_source_edits_rebind_derived_manifest_hashes\\\": True,\\n            \\\"prior_real_vcs_failed_board_source_state_is_never_rewritten_or_relaunched\\\": True,\\n        },\\n    }\\n    report_path = out_dir / report_name\\n    write_json(report_path, report)\\n    report[\\\"path\\\"] = str(report_path)\\n    return report\\n\\n\\ndef normalize_harness_sources(\\n    harness: dict[str, Any],\\n    run_dir: Path,\\n) -> tuple[list[dict[str, Any]], str, list[str]]:\\n    allowed_roots = [\\n        (run_dir / \\\"generated\\\" / \\\"semantic_harness\\\").resolve(),\\n        (run_dir / \\\"generated\\\" / \\\"chisel\\\").resolve(),\\n    ]\\n    semantic_root = (run_dir / \\\"generated\\\" / \\\"semantic_harness\\\").resolve()\\n    rows: list[dict[str, Any]] = []\\n    combined: list[str] = []\\n    blockers: list[str] = []\\n    candidates: list[tuple[str, Any]] = []\\n    source_directory = harness.get(\\\"source_directory\\\")\\n    resolved_source_directory: Path | None = None\\n    if source_directory:\\n        directory = Path(str(source_directory))\\n        if not directory.is_absolute():\\n            blockers.append(f\\\"source_directory must be absolute: {directory}\\\")\\n        else:\\n            directory = directory.resolve()\\n            if not directory.is_relative_to(semantic_root):\\n                blockers.append(f\\\"source_directory is outside generated semantic-harness root: {directory}\\\")\\n            elif not directory.is_dir():\\n                blockers.append(f\\\"source_directory does not exist after elaboration: {directory}\\\")\\n            else:\\n                resolved_source_directory = directory\\n                for path in sorted(directory.rglob(\\\"*\\\")):\\n                    if path.is_file() and path.suffix.lower() in {\\\".sv\\\", \\\".v\\\"}:\\n                        candidates.append((\\\"source_directory\\\", path))\\n    source_files = harness.get(\\\"source_files\\\", [])\\n    if not isinstance(source_files, list):\\n        blockers.append(\\\"source_files must be a list when supplied\\\")\\n        source_files = []\\n    # A successful re-elaboration makes the isolated directory authoritative.\\n    # Prior source rows may name diagnostic files that were intentionally removed.\\n    if resolved_source_directory is None:\\n        for index, item in enumerate(source_files):\\n            candidates.append((f\\\"source_files[{index}]\\\", item))\\n\\n    seen_paths: set[Path] = set()\\n    module_owners: dict[str, Path] = {}\\n    for label, item in candidates:\\n        raw = item.get(\\\"path\\\") if isinstance(item, dict) else item\\n        path = Path(str(raw or \\\"\\\"))\\n        path = path if path.is_absolute() else Path.cwd() / path\\n        path = path.resolve()\\n        if path in seen_paths:\\n            continue\\n        seen_paths.add(path)\\n        if resolved_source_directory is not None and not path.is_relative_to(resolved_source_directory):\\n            blockers.append(\\n                f\\\"{label} is outside the declared isolated source_directory: {path}\\\"\\n            )\\n            continue\\n        if not any(path.is_relative_to(root) for root in allowed_roots):\\n            blockers.append(f\\\"{label} is outside generated harness/DUT roots: {path}\\\")\\n            continue\\n        if path.suffix.lower() not in {\\\".sv\\\", \\\".v\\\"} or not path.is_file():\\n            blockers.append(f\\\"{label} is not an existing Verilog/SystemVerilog file: {path}\\\")\\n            continue\\n        try:\\n            text = path.read_text(encoding=\\\"utf-8\\\")\\n        except (OSError, UnicodeDecodeError) as exc:\\n            blockers.append(f\\\"cannot read harness source {path}: {exc}\\\")\\n            continue\\n        for module in re.findall(r\\\"(?m)^module\\\\s+([A-Za-z_][A-Za-z0-9_$]*)\\\\b\\\", text):\\n            owner = module_owners.get(module)\\n            if owner is not None:\\n                blockers.append(\\n                    f\\\"stage source set declares module {module} more than once: {owner} and {path}\\\"\\n                )\\n            else:\\n                module_owners[module] = path\\n        rows.append({\\\"path\\\": str(path), \\\"sha256\\\": sha256_file(path)})\\n        combined.append(text)\\n    if not rows:\\n        blockers.append(\\\"harness has no valid source files after source-directory discovery\\\")\\n    return rows, \\\"\\\\n\\\".join(combined), blockers\\n\\n\\ndef run_agent_requested_validation(\\n    output: dict[str, Any],\\n    run_dir: Path,\\n    out_dir: Path,\\n    timeout_sec: int,\\n    *,\\n    report_name: str = \\\"agent_requested_validation.json\\\",\\n) -> dict[str, Any]:\\n    requests = output.get(\\\"requested_validation\\\", []) if isinstance(output.get(\\\"requested_validation\\\"), list) else []\\n    generated_root = (run_dir / \\\"generated\\\" / \\\"chisel\\\").resolve()\\n    validated: list[tuple[list[str], Path, str]] = []\\n    blockers: list[str] = []\\n    allowed_flags = {\\\"--no-server\\\", \\\"--batch\\\", \\\"--supershell=false\\\"}\\n    for index, request in enumerate(requests):\\n        if not isinstance(request, dict):\\n            blockers.append(f\\\"requested_validation[{index}] is not an object\\\")\\n            continue\\n        argv = [str(value) for value in request.get(\\\"argv\\\", [])]\\n        cwd = Path(str(request.get(\\\"cwd\\\") or \\\"\\\"))\\n        cwd = cwd if cwd.is_absolute() else Path.cwd() / cwd\\n        cwd = cwd.resolve()\\n        purpose = str(request.get(\\\"purpose\\\") or \\\"\\\")\\n        if cwd != generated_root:\\n            blockers.append(f\\\"requested_validation[{index}] cwd is outside the generated Chisel project: {cwd}\\\")\\n            continue\\n        if not argv or argv[0] != \\\"sbt\\\":\\n            blockers.append(f\\\"requested_validation[{index}] may invoke only sbt\\\")\\n            continue\\n        goals = [value for value in argv[1:] if value not in allowed_flags]\\n        if len(goals) != 1:\\n            blockers.append(f\\\"requested_validation[{index}] must contain exactly one allowed sbt goal\\\")\\n            continue\\n        goal = goals[0]\\n        if goal != \\\"Compile/compile\\\" and not re.fullmatch(\\n            r\\\"runMain spatialaccagent\\\\.semantic_harness\\\\.[A-Za-z_][A-Za-z0-9_$.]*\\\",\\n            goal,\\n        ):\\n            blockers.append(f\\\"requested_validation[{index}] has disallowed sbt goal: {goal}\\\")\\n            continue\\n        if any(value.startswith(\\\"-\\\") and value not in allowed_flags for value in argv[1:]):\\n            blockers.append(f\\\"requested_validation[{index}] has a disallowed sbt option\\\")\\n            continue\\n        validated.append((argv, cwd, purpose))\\n\\n    semantic_root = (run_dir / \\\"generated\\\" / \\\"semantic_harness\\\").resolve()\\n    declared_output_roots: set[Path] = set()\\n\\n    def collect_declared_output_roots(value: Any) -> None:\\n        if isinstance(value, dict):\\n            source_directory = value.get(\\\"source_directory\\\")\\n            if source_directory:\\n                path = Path(str(source_directory))\\n                if path.is_absolute():\\n                    path = path.resolve()\\n                    if path != semantic_root and path.is_relative_to(semantic_root):\\n                        declared_output_roots.add(path)\\n            for child in value.values():\\n                collect_declared_output_roots(child)\\n        elif isinstance(value, list):\\n            for child in value:\\n                collect_declared_output_roots(child)\\n\\n    for edit in output.get(\\\"file_edits\\\", []):\\n        if isinstance(edit, dict):\\n            collect_declared_output_roots(edit.get(\\\"json_content\\\"))\\n\\n    results = []\\n    heap_mb: int | None = None\\n    if not blockers:\\n        cache_root = (run_dir / \\\"generated\\\" / \\\".sbt_codegen_cache\\\").resolve()\\n        sbt_global = cache_root / \\\"sbt\\\"\\n        sbt_boot = sbt_global / \\\"boot\\\"\\n        ivy_home = cache_root / \\\"ivy2\\\"\\n        coursier_cache = cache_root / \\\"coursier\\\"\\n        for path in (sbt_global, sbt_boot, ivy_home, coursier_cache):\\n            path.mkdir(parents=True, exist_ok=True)\\n        env = os.environ.copy()\\n        heap_mb = configured_sbt_heap_mb(env)\\n        local_opts = (\\n            f\\\"-Xms256m -Xmx{heap_mb}m -XX:+UseG1GC \\\"\\n            f\\\"-Dsbt.global.base={sbt_global} \\\"\\n            f\\\"-Dsbt.boot.directory={sbt_boot} \\\"\\n            f\\\"-Dsbt.ivy.home={ivy_home} \\\"\\n            \\\"-Dsbt.server.autostart=false \\\"\\n            \\\"-Dsbt.server.forcestart=true\\\"\\n        )\\n        env[\\\"SBT_OPTS\\\"] = f\\\"{env.get('SBT_OPTS', '')} {local_opts}\\\".strip()\\n        env.setdefault(\\\"COURSIER_CACHE\\\", str(coursier_cache))\\n        for argv, cwd, purpose in validated:\\n            cleaned_output_roots: list[str] = []\\n            if any(\\n                value.startswith(\\\"runMain spatialaccagent.semantic_harness.\\\")\\n                for value in argv\\n            ):\\n                for emitted_root in sorted(declared_output_roots):\\n                    if emitted_root.exists():\\n                        shutil.rmtree(emitted_root)\\n                    emitted_root.mkdir(parents=True)\\n                    cleaned_output_roots.append(str(emitted_root))\\n            result = run_local_tool(argv, cwd, env, timeout_sec)\\n            results.append(\\n                {\\n                    \\\"purpose\\\": purpose,\\n                    \\\"argv\\\": argv,\\n                    \\\"cwd\\\": str(cwd),\\n                    \\\"cleaned_output_root\\\": (\\n                        cleaned_output_roots[0]\\n                        if len(cleaned_output_roots) == 1\\n                        else None\\n                    ),\\n                    \\\"cleaned_output_roots\\\": cleaned_output_roots,\\n                    **result,\\n                }\\n            )\\n            if result.get(\\\"status\\\") != \\\"pass\\\":\\n                blockers.append(f\\\"requested validation failed: {purpose or argv}\\\")\\n                break\\n\\n    report = {\\n        \\\"schema_version\\\": \\\"spatialaccagent.agent_requested_validation.v1\\\",\\n        \\\"status\\\": \\\"pass\\\" if not blockers else \\\"fail\\\",\\n        \\\"requests\\\": len(requests),\\n        \\\"sbt_heap_mb\\\": heap_mb,\\n        \\\"results\\\": results,\\n        \\\"blockers\\\": blockers,\\n    }\\n    report_path = out_dir / report_name\\n    write_json(report_path, report)\\n    report[\\\"path\\\"] = str(report_path)\\n    return report\\n\\n\\ndef harness_contract_errors(\\n    harness: dict[str, Any],\\n    required_hashes: set[str],\\n    expected_layout_hash: str,\\n    expected_runtime_hash: str,\\n    run_dir: Path,\\n    generated_modules: set[str],\\n) -> tuple[dict[str, Any], list[str]]:\\n    normalized = dict(harness)\\n    source_rows, source_text, blockers = normalize_harness_sources(harness, run_dir)\\n    normalized[\\\"source_files\\\"] = source_rows\\n    top_module = str(harness.get(\\\"top_module\\\") or \\\"\\\")\\n    top_sources: list[Path] = []\\n    for row in source_rows:\\n        path = Path(str(row[\\\"path\\\"]))\\n        text = path.read_text(encoding=\\\"utf-8\\\")\\n        if top_module and re.search(rf\\\"(?m)^module\\\\s+{re.escape(top_module)}\\\\b\\\", text):\\n            top_sources.append(path)\\n    if not top_module or not top_sources:\\n        blockers.append(f\\\"harness top module is not declared by its source files: {top_module or '<missing>'}\\\")\\n    wrapper_text = \\\"\\\\n\\\".join(path.read_text(encoding=\\\"utf-8\\\") for path in top_sources)\\n    top_port_text = \\\"\\\"\\n    if wrapper_text and top_module:\\n        declaration = re.search(rf\\\"(?m)^module\\\\s+{re.escape(top_module)}\\\\b\\\", wrapper_text)\\n        if declaration:\\n            cursor = declaration.end()\\n\\n            def balanced_parentheses(start: int) -> tuple[str, int]:\\n                depth = 0\\n                for index in range(start, len(wrapper_text)):\\n                    char = wrapper_text[index]\\n                    if char == \\\"(\\\":\\n                        depth += 1\\n                    elif char == \\\")\\\":\\n                        depth -= 1\\n                        if depth == 0:\\n                            return wrapper_text[start + 1 : index], index + 1\\n                return \\\"\\\", start\\n\\n            while cursor < len(wrapper_text) and wrapper_text[cursor].isspace():\\n                cursor += 1\\n            if cursor < len(wrapper_text) and wrapper_text[cursor] == \\\"#\\\":\\n                cursor += 1\\n                while cursor < len(wrapper_text) and wrapper_text[cursor].isspace():\\n                    cursor += 1\\n                _, cursor = balanced_parentheses(cursor)\\n                while cursor < len(wrapper_text) and wrapper_text[cursor].isspace():\\n                    cursor += 1\\n            if cursor < len(wrapper_text) and wrapper_text[cursor] == \\\"(\\\":\\n                top_port_text, _ = balanced_parentheses(cursor)\\n    if top_sources and not top_port_text:\\n        blockers.append(f\\\"semantic harness top-module port list could not be parsed: {top_module}\\\")\\n    instantiated = [\\n        module\\n        for module in generated_modules\\n        if re.search(rf\\\"\\\\b{re.escape(module)}\\\\s+(?:#\\\\s*\\\\([^;]*?\\\\)\\\\s*)?[A-Za-z_][A-Za-z0-9_$]*\\\\s*\\\\(\\\", wrapper_text, re.DOTALL)\\n    ]\\n    if not instantiated:\\n        blockers.append(\\\"semantic harness does not instantiate a generated DUT module\\\")\\n    declared_modules = set(\\n        re.findall(r\\\"(?m)^module\\\\s+([A-Za-z_][A-Za-z0-9_$]*)\\\\b\\\", source_text)\\n    )\\n    missing_instantiated_sources = sorted(set(instantiated) - declared_modules)\\n    if missing_instantiated_sources:\\n        blockers.append(\\n            \\\"semantic harness source set is not self-contained for generated DUT modules: \\\"\\n            + str(missing_instantiated_sources)\\n        )\\n    normalized[\\\"generated_dut_modules\\\"] = sorted(instantiated)\\n    if re.search(r\\\"\\\\$readmem|expected\\\\.memh|model_reference|golden\\\", wrapper_text, re.IGNORECASE):\\n        blockers.append(\\\"semantic harness source attempts to read or reference expected/golden data\\\")\\n    interface = harness.get(\\\"interface\\\", {}) if isinstance(harness.get(\\\"interface\\\"), dict) else {}\\n    inputs = interface.get(\\\"inputs\\\", []) if isinstance(interface.get(\\\"inputs\\\"), list) else []\\n    output = interface.get(\\\"output\\\", {}) if isinstance(interface.get(\\\"output\\\"), dict) else {}\\n    input_data_ports = {\\n        str(port.get(\\\"data_port\\\"))\\n        for port in inputs\\n        if isinstance(port, dict) and port.get(\\\"data_port\\\")\\n    }\\n    if has_interface_data_identity_path(\\n        wrapper_text,\\n        input_data_ports,\\n        str(output.get(\\\"data_port\\\") or \\\"\\\"),\\n    ):\\n        blockers.append(\\\"semantic harness contains a direct input-to-output identity bypass\\\")\\n\\n    def missing(value: Any) -> bool:\\n        return value is None or value == \\\"\\\" or value == 0\\n\\n    def require_declared_port(value: Any, label: str) -> None:\\n        port = str(value or \\\"\\\")\\n        if port and top_port_text and not re.search(rf\\\"\\\\b{re.escape(port)}\\\\b\\\", top_port_text):\\n            blockers.append(f\\\"semantic harness top module does not declare {label}: {port}\\\")\\n\\n    for name in (\\\"clock_port\\\", \\\"reset_port\\\"):\\n        port = str(interface.get(name) or \\\"\\\")\\n        if not port or not top_port_text or not re.search(rf\\\"\\\\b{re.escape(port)}\\\\b\\\", top_port_text):\\n            blockers.append(f\\\"semantic harness interface is missing connected {name}: {port or '<missing>'}\\\")\\n    if not inputs:\\n        blockers.append(\\\"semantic harness interface has no input stream\\\")\\n    for index, port in enumerate(inputs):\\n        if not isinstance(port, dict):\\n            blockers.append(f\\\"semantic harness input {index} is not an object\\\")\\n            continue\\n        for name in (\\\"valid_port\\\", \\\"ready_port\\\", \\\"data_port\\\", \\\"data_width_bits\\\"):\\n            value = port.get(name)\\n            if missing(value):\\n                blockers.append(f\\\"semantic harness input {index} is missing {name}\\\")\\n            elif name.endswith(\\\"_port\\\"):\\n                require_declared_port(value, f\\\"input {index} {name}\\\")\\n        if not missing(port.get(\\\"last_port\\\")):\\n            require_declared_port(port.get(\\\"last_port\\\"), f\\\"input {index} last_port\\\")\\n    for name in (\\\"valid_port\\\", \\\"ready_port\\\", \\\"data_port\\\", \\\"data_width_bits\\\"):\\n        if missing(output.get(name)):\\n            blockers.append(f\\\"semantic harness output is missing {name}\\\")\\n        elif name.endswith(\\\"_port\\\"):\\n            require_declared_port(output.get(name), f\\\"output {name}\\\")\\n    if not missing(output.get(\\\"last_port\\\")):\\n        require_declared_port(output.get(\\\"last_port\\\"), \\\"output last_port\\\")\\n    if not missing(interface.get(\\\"start_port\\\")):\\n        require_declared_port(interface.get(\\\"start_port\\\"), \\\"start_port\\\")\\n    for index, constant in enumerate(interface.get(\\\"constant_ports\\\", [])):\\n        if not isinstance(constant, dict):\\n            blockers.append(f\\\"semantic harness constant port {index} is not an object\\\")\\n            continue\\n        if missing(constant.get(\\\"port\\\")):\\n            blockers.append(f\\\"semantic harness constant port {index} is missing port\\\")\\n        else:\\n            require_declared_port(constant.get(\\\"port\\\"), f\\\"constant port {index}\\\")\\n\\n    consumed = {str(value) for value in harness.get(\\\"consumed_tensor_hashes\\\", []) if str(value)}\\n    missing_hashes = sorted(required_hashes - consumed)\\n    if missing_hashes:\\n        blockers.append(f\\\"semantic harness is missing {len(missing_hashes)} required tensor hash(es)\\\")\\n    normalized[\\\"consumed_tensor_hashes\\\"] = sorted(consumed)\\n    if required_hashes:\\n        if harness.get(\\\"weight_layout_contract_sha256\\\") != expected_layout_hash:\\n            blockers.append(\\\"weighted semantic harness does not bind the required weight-layout contract hash\\\")\\n        if harness.get(\\\"default_or_identity_weight_fallback_disabled\\\") is not True:\\n            blockers.append(\\\"weighted semantic harness does not disable default/identity fallback\\\")\\n        loader = interface.get(\\\"weight_loader\\\", {}) if isinstance(interface.get(\\\"weight_loader\\\"), dict) else {}\\n        for name in (\\n            \\\"valid_port\\\",\\n            \\\"ready_port\\\",\\n            \\\"data_port\\\",\\n            \\\"data_width_bits\\\",\\n            \\\"addr_port\\\",\\n            \\\"addr_width_bits\\\",\\n            \\\"last_port\\\",\\n        ):\\n            if missing(loader.get(name)):\\n                blockers.append(f\\\"weighted semantic harness loader is missing {name}\\\")\\n            elif name.endswith(\\\"_port\\\"):\\n                require_declared_port(loader.get(name), f\\\"weight loader {name}\\\")\\n        if loader.get(\\\"data_width_bits\\\") not in {32, \\\"32\\\"}:\\n            blockers.append(\\\"weighted semantic harness loader data width must be 32 bits\\\")\\n    if expected_runtime_hash:\\n        if harness.get(\\\"runtime_constant_contract_sha256\\\") != expected_runtime_hash:\\n            blockers.append(\\\"semantic harness does not bind the required runtime-constant contract hash\\\")\\n        runtime_loader = interface.get(\\\"runtime_loader\\\", {}) if isinstance(interface.get(\\\"runtime_loader\\\"), dict) else {}\\n        for name in (\\n            \\\"valid_port\\\",\\n            \\\"ready_port\\\",\\n            \\\"data_port\\\",\\n            \\\"data_width_bits\\\",\\n            \\\"addr_port\\\",\\n            \\\"addr_width_bits\\\",\\n            \\\"last_port\\\",\\n        ):\\n            if missing(runtime_loader.get(name)):\\n                blockers.append(f\\\"runtime-constant semantic harness loader is missing {name}\\\")\\n            elif name.endswith(\\\"_port\\\"):\\n                require_declared_port(runtime_loader.get(name), f\\\"runtime loader {name}\\\")\\n        if runtime_loader.get(\\\"data_width_bits\\\") not in {32, \\\"32\\\"}:\\n            blockers.append(\\\"runtime-constant semantic harness loader data width must be 32 bits\\\")\\n        normalized[\\\"runtime_constant_contract_sha256\\\"] = expected_runtime_hash\\n    return normalized, blockers\\n\\n\\ndef connected_harness_contract_errors(\\n    harness: dict[str, Any],\\n    requirements: dict[str, Any],\\n    run_dir: Path,\\n    generated_modules: set[str],\\n) -> tuple[dict[str, Any], list[str]]:\\n    weight_contract = (\\n        requirements.get(\\\"connected_weight_stream_contract\\\", {})\\n        if isinstance(requirements.get(\\\"connected_weight_stream_contract\\\"), dict)\\n        else {}\\n    )\\n    runtime_contract = (\\n        requirements.get(\\\"connected_runtime_stream_contract\\\", {})\\n        if isinstance(requirements.get(\\\"connected_runtime_stream_contract\\\"), dict)\\n        else {}\\n    )\\n    overlap_contract = (\\n        requirements.get(\\\"single_layer_pipeline_overlap_contract\\\", {})\\n        if isinstance(requirements.get(\\\"single_layer_pipeline_overlap_contract\\\"), dict)\\n        else {}\\n    )\\n    required_hashes = {\\n        str(row.get(\\\"sha256\\\"))\\n        for row in requirements.get(\\\"single_layer_required_tensors\\\", [])\\n        if isinstance(row, dict) and row.get(\\\"sha256\\\")\\n    }\\n    weight_hash = str(weight_contract.get(\\\"contract_sha256\\\") or \\\"\\\")\\n    runtime_hash = str(runtime_contract.get(\\\"contract_sha256\\\") or \\\"\\\")\\n    normalized, blockers = harness_contract_errors(\\n        harness,\\n        required_hashes,\\n        weight_hash,\\n        runtime_hash,\\n        run_dir,\\n        generated_modules,\\n    )\\n    if not weight_hash or weight_contract.get(\\\"status\\\") != \\\"pass\\\":\\n        blockers.append(\\\"connected canonical weight-stream contract is not ready\\\")\\n    if not runtime_hash or runtime_contract.get(\\\"status\\\") != \\\"pass\\\":\\n        blockers.append(\\\"connected canonical runtime-stream contract is not ready\\\")\\n    expected_fields = {\\n        \\\"connected_weight_stream_contract_sha256\\\": weight_hash,\\n        \\\"connected_runtime_stream_contract_sha256\\\": runtime_hash,\\n        \\\"pipeline_plan_sha256\\\": requirements.get(\\\"pipeline_plan_sha256\\\"),\\n        \\\"pipeline_overlap_trace_contract_sha256\\\": overlap_contract.get(\\\"contract_sha256\\\"),\\n    }\\n    for field, expected in expected_fields.items():\\n        if not expected or harness.get(field) != expected:\\n            blockers.append(f\\\"connected semantic harness does not bind required {field}\\\")\\n        else:\\n            normalized[field] = expected\\n    blockers.extend(connected_loader_route_errors(harness, weight_contract, runtime_contract))\\n    route_contract = (\\n        harness.get(\\\"loader_route_contract\\\", {})\\n        if isinstance(harness.get(\\\"loader_route_contract\\\"), dict)\\n        else {}\\n    )\\n    normalized[\\\"loader_route_contract\\\"] = route_contract\\n    normalized[\\\"loader_route_contract_sha256\\\"] = hashlib.sha256(\\n        json.dumps(route_contract, sort_keys=True, separators=(\\\",\\\", \\\":\\\")).encode(\\\"utf-8\\\")\\n    ).hexdigest()\\n    return normalized, blockers\\n\\n\\ndef finalize_dut_weight_binding_manifest(\\n    run_dir: Path,\\n    out_dir: Path,\\n    *,\\n    require_single_layer: bool = False,\\n    require_board: bool = False,\\n    single_layer_certificate_path: Path | None = None,\\n) -> dict[str, Any]:\\n    manifest_path = run_dir / \\\"generated\\\" / \\\"memory\\\" / \\\"dut_weight_binding_manifest.json\\\"\\n    requirements_path = run_dir / \\\"verification\\\" / \\\"semantic_testbench\\\" / \\\"dut_weight_binding_requirements.json\\\"\\n    source_provenance: dict[str, Any] = {}\\n    patch_path = out_dir / \\\"agent_patch_application.json\\\"\\n    prior_materialization_path = out_dir / \\\"dut_weight_binding_materialization.json\\\"\\n    prior_materialization = read_json_if_exists(prior_materialization_path)\\n    source_agent_manifest_sha256 = sha256_file(manifest_path) if manifest_path.is_file() else \\\"\\\"\\n    if source_agent_manifest_sha256 and patch_path.is_file():\\n        patch_report = read_json_if_exists(patch_path)\\n        patch_files = (\\n            patch_report.get(\\\"files\\\", [])\\n            if patch_report.get(\\\"status\\\") == \\\"pass\\\"\\n            and patch_report.get(\\\"blockers\\\") == []\\n            and isinstance(patch_report.get(\\\"files\\\"), list)\\n            else []\\n        )\\n        for row in patch_files:\\n            if not isinstance(row, dict):\\n                continue\\n            try:\\n                row_path = Path(str(row.get(\\\"path\\\") or \\\"\\\")).resolve()\\n            except OSError:\\n                continue\\n            if (\\n                row_path == manifest_path.resolve()\\n                and row.get(\\\"after_sha256\\\") == source_agent_manifest_sha256\\n            ):\\n                source_provenance = {\\n                    \\\"source_patch_application\\\": str(patch_path),\\n                    \\\"source_patch_application_sha256\\\": sha256_file(patch_path),\\n                    \\\"source_agent_manifest\\\": str(manifest_path),\\n                    \\\"source_agent_manifest_sha256\\\": source_agent_manifest_sha256,\\n                }\\n                break\\n        if not source_provenance:\\n            provenance_fields = (\\n                \\\"source_patch_application\\\",\\n                \\\"source_patch_application_sha256\\\",\\n                \\\"source_agent_manifest\\\",\\n                \\\"source_agent_manifest_sha256\\\",\\n            )\\n            try:\\n                prior_patch_path = Path(\\n                    str(prior_materialization.get(\\\"source_patch_application\\\") or \\\"\\\")\\n                ).resolve()\\n                prior_agent_manifest_path = Path(\\n                    str(prior_materialization.get(\\\"source_agent_manifest\\\") or \\\"\\\")\\n                ).resolve()\\n            except OSError:\\n                prior_patch_path = Path()\\n                prior_agent_manifest_path = Path()\\n            prior_agent_sha = str(\\n                prior_materialization.get(\\\"source_agent_manifest_sha256\\\") or \\\"\\\"\\n            )\\n            patch_attests_agent_manifest = any(\\n                isinstance(row, dict)\\n                and Path(str(row.get(\\\"path\\\") or \\\"\\\")).resolve()\\n                == manifest_path.resolve()\\n                and row.get(\\\"after_sha256\\\") == prior_agent_sha\\n                for row in patch_files\\n                if row.get(\\\"path\\\")\\n            )\\n            if (\\n                prior_materialization.get(\\\"schema_version\\\")\\n                == \\\"spatialaccagent.dut_weight_binding_materialization.v1\\\"\\n                and prior_materialization.get(\\\"manifest_sha256\\\")\\n                == source_agent_manifest_sha256\\n                and all(prior_materialization.get(field) for field in provenance_fields)\\n                and prior_patch_path == patch_path.resolve()\\n                and prior_materialization.get(\\\"source_patch_application_sha256\\\")\\n                == sha256_file(patch_path)\\n                and prior_agent_manifest_path == manifest_path.resolve()\\n                and patch_attests_agent_manifest\\n            ):\\n                source_provenance = {\\n                    field: prior_materialization[field]\\n                    for field in provenance_fields\\n                }\\n    blockers: list[str] = []\\n    if not manifest_path.is_file():\\n        blockers.append(f\\\"agent patch did not create DUT weight-binding manifest: {manifest_path}\\\")\\n        manifest: dict[str, Any] = {}\\n    else:\\n        manifest = read_json_if_exists(manifest_path)\\n    if require_board:\\n        source_provenance = prefer_archived_exact_board_source_provenance(\\n            manifest,\\n            manifest_path,\\n            out_dir,\\n            source_provenance,\\n        )\\n    checkpoint_framework_binding = (\\n        rebind_manifest_checkpoint_framework_authority(manifest)\\n        if require_board\\n        else {\\n            \\\"schema_version\\\": (\\n                \\\"spatialaccagent.checkpoint_manifest_framework_binding.v1\\\"\\n            ),\\n            \\\"status\\\": \\\"not_required\\\",\\n            \\\"changed\\\": False,\\n        }\\n    )\\n    if checkpoint_framework_binding.get(\\\"status\\\") == \\\"fail\\\":\\n        blockers.extend(\\n            \\\"checkpoint_framework_authority: \\\" + str(error)\\n            for error in checkpoint_framework_binding.get(\\n                \\\"adapter_binding\\\", {}\\n            ).get(\\\"errors\\\", [])\\n            if str(error)\\n        )\\n    requirements = read_json_if_exists(requirements_path)\\n    if not requirements:\\n        blockers.append(f\\\"DUT weight-binding requirements are missing: {requirements_path}\\\")\\n    if require_board and isinstance(\\n        manifest.get(\\\"board_simulation_preflight_plan\\\"), dict\\n    ):\\n        selection_refresh_blockers: list[str] = []\\n        _materialize_external_fixture_preflight_selection(\\n            manifest[\\\"board_simulation_preflight_plan\\\"],\\n            run_dir,\\n            selection_refresh_blockers,\\n        )\\n        blockers.extend(\\n            f\\\"board_preflight: {value}\\\" for value in selection_refresh_blockers\\n        )\\n\\n    generated_modules: set[str] = set()\\n    generated_source_candidates = [\\n        *(run_dir / \\\"generated\\\" / \\\"chisel\\\").glob(\\\"*.sv\\\"),\\n        *(run_dir / \\\"generated\\\" / \\\"semantic_harness\\\").rglob(\\\"*.sv\\\"),\\n        *(run_dir / \\\"generated\\\" / \\\"semantic_harness\\\").rglob(\\\"*.v\\\"),\\n        *(run_dir / \\\"generated\\\" / \\\"board_integration\\\").rglob(\\\"*.sv\\\"),\\n        *(run_dir / \\\"generated\\\" / \\\"board_integration\\\").rglob(\\\"*.v\\\"),\\n    ]\\n    for source in generated_source_candidates:\\n        try:\\n            generated_modules.update(\\n                re.findall(r\\\"(?m)^module\\\\s+([A-Za-z_][A-Za-z0-9_$]*)\\\\b\\\", source.read_text(encoding=\\\"utf-8\\\"))\\n            )\\n        except (OSError, UnicodeDecodeError):\\n            continue\\n\\n    stage_harnesses = manifest.get(\\\"stage_harnesses\\\", {}) if isinstance(manifest.get(\\\"stage_harnesses\\\"), dict) else {}\\n    normalized_harnesses: dict[str, Any] = {}\\n    all_consumed: set[str] = set()\\n    lower_layer_certificate = reusable_operator_leaf_promotion_certificate(run_dir)\\n    reuse_certified_lower_layer = (\\n        (require_single_layer or require_board)\\n        and lower_layer_certificate.get(\\\"status\\\") == \\\"pass\\\"\\n    )\\n    for row in requirements.get(\\\"stage_requirements\\\", []):\\n        if not isinstance(row, dict):\\n            continue\\n        stage_id = str(row.get(\\\"stage_id\\\") or \\\"\\\")\\n        required_hashes = {\\n            str(item.get(\\\"sha256\\\"))\\n            for item in row.get(\\\"required_tensors\\\", [])\\n            if isinstance(item, dict) and item.get(\\\"sha256\\\")\\n        }\\n        harness = stage_harnesses.get(stage_id)\\n        if not isinstance(harness, dict):\\n            blockers.append(f\\\"DUT binding has no agent-generated harness for {stage_id}\\\")\\n            continue\\n        if reuse_certified_lower_layer:\\n            normalized = copy.deepcopy(harness)\\n            errors = certified_stage_harness_metadata_errors(harness, row)\\n        else:\\n            normalized, errors = harness_contract_errors(\\n                harness,\\n                required_hashes,\\n                str(row.get(\\\"weight_layout_contract_sha256\\\") or \\\"\\\"),\\n                str(row.get(\\\"runtime_constant_contract_sha256\\\") or \\\"\\\"),\\n                run_dir,\\n                generated_modules,\\n            )\\n        normalized_harnesses[stage_id] = normalized\\n        all_consumed.update(str(value) for value in normalized.get(\\\"consumed_tensor_hashes\\\", []))\\n        blockers.extend(f\\\"{stage_id}: {error}\\\" for error in errors)\\n\\n    required_global = {\\n        str(row.get(\\\"sha256\\\"))\\n        for row in requirements.get(\\\"single_layer_required_tensors\\\", [])\\n        if isinstance(row, dict) and row.get(\\\"sha256\\\")\\n    }\\n    missing_global = sorted(required_global - all_consumed)\\n    if missing_global:\\n        blockers.append(f\\\"agent-generated leaf harnesses do not cover {len(missing_global)} required tensor hash(es)\\\")\\n\\n    normalized_single_layer: dict[str, Any] | None = None\\n    if require_single_layer or require_board:\\n        single_layer_harness = manifest.get(\\\"single_layer_harness\\\")\\n        if not isinstance(single_layer_harness, dict):\\n            blockers.append(\\\"DUT binding has no agent-generated connected single-layer harness\\\")\\n        else:\\n            normalized_single_layer, single_errors = connected_harness_contract_errors(\\n                single_layer_harness,\\n                requirements,\\n                run_dir,\\n                generated_modules,\\n            )\\n            all_consumed.update(\\n                str(value)\\n                for value in normalized_single_layer.get(\\n                    \\\"consumed_tensor_hashes\\\", []\\n                )\\n            )\\n            blockers.extend(f\\\"single_layer: {error}\\\" for error in single_errors)\\n\\n    normalized_multilayer: dict[str, Any] | None = None\\n    if require_board and normalized_single_layer is not None:\\n        integration = copy.deepcopy(\\n            manifest.get(\\\"board_integration_contract\\\")\\n            if isinstance(manifest.get(\\\"board_integration_contract\\\"), dict)\\n            else {}\\n        )\\n        runtime_paths = exact_board_memory_runtime_paths(run_dir, out_dir)\\n        for field, path in (\\n            (\\\"board_memory_runtime_contract_sha256\\\", runtime_paths[\\\"contract\\\"]),\\n            (\\\"full_weight_image_manifest_sha256\\\", runtime_paths[\\\"image_manifest\\\"]),\\n            (\\\"full_weight_image_sha256\\\", runtime_paths[\\\"image\\\"]),\\n            (\\n                \\\"full_layer_runtime_capture_contract_sha256\\\",\\n                runtime_paths[\\\"runtime_capture\\\"],\\n            ),\\n            (\\n                \\\"full_runtime_image_manifest_sha256\\\",\\n                runtime_paths[\\\"runtime_image_manifest\\\"],\\n            ),\\n            (\\\"full_runtime_image_sha256\\\", runtime_paths[\\\"runtime_image\\\"]),\\n        ):\\n            if path.is_file():\\n                integration[field] = sha256_file(path)\\n        manifest[\\\"board_integration_contract\\\"] = integration\\n        normalized_multilayer, board_errors = board_integration_binding_errors(\\n            manifest,\\n            normalized_single_layer,\\n            run_dir,\\n            out_dir,\\n            single_layer_certificate_path,\\n            source_provenance,\\n        )\\n        blockers.extend(f\\\"board_integration: {error}\\\" for error in board_errors)\\n\\n    manifest.update(\\n        {\\n            \\\"schema_version\\\": \\\"spatialaccagent.dut_weight_binding_manifest.v1\\\",\\n            \\\"status\\\": \\\"pass\\\" if not blockers else \\\"incomplete\\\",\\n            \\\"accelerator_scope\\\": \\\"transformer_blocks_only\\\",\\n            \\\"source_checkpoint_sha256\\\": requirements.get(\\\"source_checkpoint_sha256\\\"),\\n            \\\"source_reference_sha256\\\": requirements.get(\\\"source_reference_sha256\\\"),\\n            \\\"numeric_policy_sha256\\\": requirements.get(\\\"numeric_policy_sha256\\\"),\\n            \\\"model_semantic_adapter_sha256\\\": requirements.get(\\\"model_semantic_adapter_sha256\\\"),\\n            \\\"scope_coverage_complete\\\": not blockers,\\n            \\\"dut_consumes_bound_weights\\\": not blockers,\\n            \\\"default_or_identity_weight_fallback_disabled\\\": not blockers,\\n            \\\"consumed_tensor_hashes\\\": sorted(all_consumed),\\n            \\\"stage_harnesses\\\": normalized_harnesses,\\n            **(\\n                {\\\"single_layer_harness\\\": normalized_single_layer}\\n                if normalized_single_layer is not None\\n                else {}\\n            ),\\n            **(\\n                {\\\"multilayer_harness\\\": normalized_multilayer}\\n                if normalized_multilayer is not None\\n                else {}\\n            ),\\n            \\\"materialization\\\": {\\n                \\\"source\\\": \\\"agent_file_edits_plus_framework_hash_validation\\\",\\n                \\\"requirements\\\": str(requirements_path),\\n                \\\"requirements_sha256\\\": sha256_file(requirements_path) if requirements_path.is_file() else None,\\n                \\\"executed_weight_consumption_pending_real_simulation\\\": True,\\n                \\\"verification_scope\\\": (\\n                    \\\"board_axi_ddr_closure\\\"\\n                    if require_board\\n                    else \\\"single_layer_closure\\\"\\n                    if require_single_layer\\n                    else \\\"operator_leaf_closure\\\"\\n                ),\\n                \\\"golden_or_reference_files_modified\\\": False,\\n                \\\"checkpoint_framework_authority_binding\\\": copy.deepcopy(\\n                    checkpoint_framework_binding\\n                ),\\n            },\\n            \\\"materialization_blockers\\\": blockers,\\n        }\\n    )\\n    board_preflight: dict[str, Any] | None = None\\n    if require_board:\\n        if isinstance(manifest.get(\\\"board_simulation_preflight_plan\\\"), dict):\\n            missing_prerequisites = (\\n                framework_vcs_plan_binding_missing_prerequisites(\\n                    run_dir,\\n                    str(\\n                        manifest[\\\"board_simulation_preflight_plan\\\"].get(\\n                            \\\"validation_mode\\\"\\n                        )\\n                        or \\\"exact_sample_physical_ddr\\\"\\n                    ),\\n                )\\n            )\\n            if missing_prerequisites:\\n                blockers.append(\\n                    \\\"board_preflight: framework VCS-plan binding prerequisites are \\\"\\n                    \\\"missing: \\\" + \\\"; \\\".join(missing_prerequisites)\\n                )\\n            else:\\n                manifest, vcs_binding = bind_framework_vcs_compile_plan(\\n                    manifest,\\n                    run_dir,\\n                    out_dir,\\n                    manifest_path,\\n                )\\n                blockers.extend(\\n                    f\\\"board_preflight: {value}\\\"\\n                    for value in vcs_binding.get(\\\"blockers\\\", [])\\n                )\\n        if normalized_multilayer is None:\\n            blockers.append(\\\"board_integration: normalized multi-layer harness is unavailable for exact preflight\\\")\\n        else:\\n            board_preflight = materialize_exact_board_preflight_manifest(\\n                manifest,\\n                normalized_multilayer,\\n                run_dir,\\n            )\\n            blockers.extend(\\n                f\\\"board_preflight: {error}\\\"\\n                for error in board_preflight.get(\\\"blockers\\\", [])\\n                if str(error)\\n            )\\n    blockers = list(dict.fromkeys(blockers))\\n    manifest.update(\\n        {\\n            \\\"status\\\": \\\"pass\\\" if not blockers else \\\"incomplete\\\",\\n            \\\"scope_coverage_complete\\\": not blockers,\\n            \\\"dut_consumes_bound_weights\\\": not blockers,\\n            \\\"default_or_identity_weight_fallback_disabled\\\": not blockers,\\n            \\\"materialization_blockers\\\": blockers,\\n        }\\n    )\\n    materialization = manifest.get(\\\"materialization\\\")\\n    if isinstance(materialization, dict) and require_board:\\n        materialization.update(\\n            {\\n                \\\"board_simulation_preflight_manifest\\\": (\\n                    board_preflight.get(\\\"manifest\\\") if board_preflight is not None else None\\n                ),\\n                \\\"board_simulation_preflight_manifest_sha256\\\": (\\n                    board_preflight.get(\\\"manifest_sha256\\\") if board_preflight is not None else None\\n                ),\\n                \\\"board_simulation_preflight_status\\\": (\\n                    board_preflight.get(\\\"status\\\") if board_preflight is not None else \\\"incomplete\\\"\\n                ),\\n                \\\"board_simulation_execution_pending_real_vcs\\\": True,\\n            }\\n        )\\n    write_json(manifest_path, manifest)\\n    report = {\\n        \\\"schema_version\\\": \\\"spatialaccagent.dut_weight_binding_materialization.v1\\\",\\n        \\\"status\\\": \\\"pass\\\" if not blockers else \\\"incomplete\\\",\\n        \\\"manifest\\\": str(manifest_path),\\n        \\\"manifest_sha256\\\": sha256_file(manifest_path),\\n        \\\"stage_harness_count\\\": len(normalized_harnesses),\\n        \\\"single_layer_harness_materialized\\\": normalized_single_layer is not None,\\n        \\\"board_integration_harness_materialized\\\": normalized_multilayer is not None,\\n        \\\"board_simulation_preflight_materialized\\\": (\\n            board_preflight is not None and board_preflight.get(\\\"status\\\") == \\\"pass\\\"\\n        ),\\n        \\\"board_simulation_preflight_manifest\\\": (\\n            board_preflight.get(\\\"manifest\\\") if board_preflight is not None else None\\n        ),\\n        \\\"board_simulation_preflight_manifest_sha256\\\": (\\n            board_preflight.get(\\\"manifest_sha256\\\") if board_preflight is not None else None\\n        ),\\n        \\\"vcs_compile_plan_sha256\\\": (\\n            board_preflight.get(\\\"vcs_compile_plan_sha256\\\") if board_preflight is not None else None\\n        ),\\n        \\\"board_simulation_preflight_report\\\": (\\n            board_preflight.get(\\\"path\\\") if board_preflight is not None else None\\n        ),\\n        \\\"consumed_tensor_hash_count\\\": len(all_consumed),\\n            \\\"checkpoint_framework_authority_binding\\\": copy.deepcopy(\\n                checkpoint_framework_binding\\n            ),\\n            \\\"lower_layer_certificate_reuse\\\": copy.deepcopy(\\n                lower_layer_certificate\\n            ),\\n            \\\"blockers\\\": blockers,\\n            **source_provenance,\\n        }\\n    report_path = out_dir / \\\"dut_weight_binding_materialization.json\\\"\\n    write_json(report_path, report)\\n    report[\\\"path\\\"] = str(report_path)\\n    return report\\n\"\n}",
        "content_sha256": "d50d8746233b6cb21901fcb5ef4ac2669235fa713dda8889583506fa7ee3a54e",
        "path": "accagent/framework/stage_repair_execute.py#exact_capability_consumer_functions",
        "projection": true,
        "source_path": "accagent/framework/stage_repair_execute.py",
        "source_sha256": "733c2e3b5f07804eee8077fcf0b07551ff41f52b399026f80bd2e40a31443a0f",
        "truncated": false
      },
      {
        "bytes": 5705,
        "content": "{\n  \"authorization_errors\": [],\n  \"candidate_stage_ids\": [\n    \"stage_02_residual_add_1\",\n    \"stage_08_residual_add_2\"\n  ],\n  \"candidate_stages\": [\n    {\n      \"index\": 2,\n      \"kind\": \"residual\",\n      \"op\": \"residual_add_1\",\n      \"source\": \"Residual.scala\",\n      \"stage_id\": \"stage_02_residual_add_1\",\n      \"template_id\": \"residual\"\n    },\n    {\n      \"index\": 8,\n      \"kind\": \"residual\",\n      \"op\": \"residual_add_2\",\n      \"source\": \"Residual.scala\",\n      \"stage_id\": \"stage_08_residual_add_2\",\n      \"template_id\": \"residual\"\n    }\n  ],\n  \"candidate_template_sources\": [\n    \"Residual.scala\"\n  ],\n  \"corroborating_semantic_numeric_failure\": null,\n  \"failure_mode\": \"completed_pipeline_overlap_violation\",\n  \"policy\": {\n    \"candidate_authorization_is_not_a_root_cause_verdict\": true,\n    \"checkpoint_input_golden_numeric_policy_and_checker_are_immutable\": true,\n    \"harness_instrumentation_may_precede_template_edit_when_internal_root_is_ambiguous\": true,\n    \"persistent_generated_pair_replacement_required\": true,\n    \"same_stage_real_golden_vcs_must_pass_after_repair\": true,\n    \"smallest_justified_edit_set_required\": true\n  },\n  \"real_tool_failure\": {\n    \"beat_index\": null,\n    \"candidate_stage_ids\": [\n      \"stage_02_residual_add_1\",\n      \"stage_08_residual_add_2\"\n    ],\n    \"candidate_stages\": [\n      {\n        \"index\": 2,\n        \"kind\": \"residual\",\n        \"op\": \"residual_add_1\",\n        \"source\": \"Residual.scala\",\n        \"stage_id\": \"stage_02_residual_add_1\",\n        \"template_id\": \"residual\"\n      },\n      {\n        \"index\": 8,\n        \"kind\": \"residual\",\n        \"op\": \"residual_add_2\",\n        \"source\": \"Residual.scala\",\n        \"stage_id\": \"stage_08_residual_add_2\",\n        \"template_id\": \"residual\"\n      }\n    ],\n    \"candidate_template_sources\": [\n      \"Residual.scala\"\n    ],\n    \"evidence_type\": \"single_layer_pipeline_contract\",\n    \"expected_output_sha256\": null,\n    \"expected_value\": {\n      \"every_dependency_has_different_token_overlap\": true,\n      \"every_stage_keeps_pipeline_filled\": true,\n      \"whole_sequence_barrier_forbidden\": true\n    },\n    \"failure_class\": \"intra_layer_spatial_pipeline_violation\",\n    \"failure_mode\": \"completed_pipeline_overlap_violation\",\n    \"input_fingerprint_sha256\": \"83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8\",\n    \"lane_index\": null,\n    \"logical_index\": null,\n    \"observed_value\": {\n      \"completed_pipeline_overlap_violation\": true,\n      \"failed_dependency_overlap_evidence\": [\n        {\n          \"boundary_id\": \"edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip\",\n          \"different_token_overlap_observed\": false,\n          \"dst_stage\": \"stage_08_residual_add_2\",\n          \"overlaps\": [],\n          \"src_stage\": \"stage_02_residual_add_1\"\n        }\n      ],\n      \"failed_stage_turnover_evidence\": [],\n      \"whole_sequence_barrier_evidence\": []\n    },\n    \"pipeline_trace_sha256\": \"8b721485e310341bbe5651973089a4fecadf56204a235ae1a78ec8185ae23b94\",\n    \"rtl_output_sha256\": null,\n    \"summary\": \"source-bound real VCS produced 0 failed token turnovers and 1 failed dependency overlaps\",\n    \"template_pairs\": [\n      {\n        \"generated_path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala\",\n        \"persistent_path\": \"/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala\",\n        \"sha256\": \"110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34\",\n        \"template_source\": \"Residual.scala\"\n      }\n    ],\n    \"template_source\": null,\n    \"testbench_sha256\": null,\n    \"violated_contract\": \"all_spatial_operators_must_form_a_token_level_pipeline\"\n  },\n  \"root_candidate_module\": \"pipeline_candidate_set\",\n  \"schema_version\": \"spatialaccagent.localized_semantic_template_pairs.v2\",\n  \"source_bound_pipeline_candidate_pairs\": [\n    {\n      \"body_document_path\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala\",\n      \"declares_root_candidate\": false,\n      \"generated_path\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala\",\n      \"generated_sha256\": \"110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34\",\n      \"name\": \"Residual.scala\",\n      \"persistent_path\": \"accagent/framework/templates/operator_chisel/Residual.scala\",\n      \"persistent_sha256\": \"110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34\",\n      \"required_edit_policy\": \"replace both paths with byte-identical complete contents when this template is edited\",\n      \"source_bound_pipeline_candidate\": true\n    }\n  ],\n  \"stage_id\": \"stage_02_residual_add_1\",\n  \"template_instrumentation_pairs\": [],\n  \"template_pairs\": [\n    {\n      \"body_document_path\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala\",\n      \"declares_root_candidate\": false,\n      \"generated_path\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala\",\n      \"generated_sha256\": \"110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34\",\n      \"name\": \"Residual.scala\",\n      \"persistent_path\": \"accagent/framework/templates/operator_chisel/Residual.scala\",\n      \"persistent_sha256\": \"110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34\",\n      \"required_edit_policy\": \"replace both paths with byte-identical complete contents when this template is edited\",\n      \"source_bound_pipeline_candidate\": true\n    }\n  ]\n}",
        "content_sha256": "4a38d6cf752421414b18ce04abd7c3b6f31a87ad1a8241bf468c810ae398a2ff",
        "path": "localized_semantic_repair/stage_02_residual_add_1#template_pair_contract",
        "projection": true,
        "source_path": "accagent/framework/stage_repair_execute.py",
        "source_sha256": "733c2e3b5f07804eee8077fcf0b07551ff41f52b399026f80bd2e40a31443a0f",
        "truncated": false
      }
    ],
    "duplicate_content_documents_removed": 0,
    "editable_contract": {
      "allowed_create_or_replace_roots": [
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/semantic_harness"
      ],
      "allowed_exact_files": [
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json"
      ],
      "approved_bounded_template_repair_exact_files": [
        "accagent/framework/templates/operator_chisel/Residual.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala"
      ],
      "bounded_template_repair_approved": true,
      "forbidden": [
        "all input, checkpoint, target-model reference, golden-output, verification-report, certificate, checker, and numeric-policy files",
        "all existing generated DUT modules; this capability repair may add harness wrappers but may not patch datapath RTL before a real localized DUT failure",
        "behavioral replacement of the DUT, identity/default bypasses, sampled weights, random expected output, or RTL-derived golden output"
      ],
      "localized_allowed_exact_files": [
        "accagent/framework/templates/operator_chisel/Residual.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala"
      ],
      "localized_authorization_errors": [],
      "localized_candidate_template_pair_names": [
        "Residual.scala"
      ],
      "localized_instrumentation_only": false,
      "localized_semantic_repair_authorized": true,
      "localized_template_instrumentation_approved": false,
      "localized_template_instrumentation_only": false,
      "localized_template_instrumentation_pair_names": [],
      "localized_template_pair_names": [],
      "read_only_generated_dut_sources": [
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Activation.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/AttentionGQA.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ElementwiseMul.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GatedMLP.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GeneratedAcceleratorTop.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GeneratedAxiDdrTop.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_1.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_2.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_4.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/LlamaStyleBlock.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/QKVProjection.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Queue1792_StreamBeat.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Queue4_StreamBeat.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/QwenMultiLayerSystemTop.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/RMSNorm.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ResidualAdd.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/RoPE.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/VectorNorm.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ram_1792x256.sv",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ram_4x129.sv"
      ],
      "read_only_template_sources": [
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Activation.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Common.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/DecoderBlock.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Elementwise.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/FFN.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/KVCache.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Linear.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Mask.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Norm.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/QKVProjection.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/RoPE.scala",
        "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Softmax.scala"
      ],
      "semantic_template_repair_approved": true,
      "semantic_template_repair_boundary": {
        "allowed": [
          "selected operator-template internal datapath and state-machine correction",
          "selected template internal stream/interface correction required by target-model semantics",
          "synthesizable implementation of the frozen numeric contract"
        ],
        "approval_source": "current user instruction to run the agent-owned real-tool root-cause/code-repair loop",
        "preserved": [
          "external accelerator and board/runtime ABI",
          "pipeline semantic stage order",
          "model dimensions and target tensor semantics",
          "numeric policy and comparison thresholds",
          "real checkpoint/input/golden/checker artifacts"
        ]
      },
      "template_repair_deferred_until_real_localized_failure": false,
      "templates_read_only_after_compiled_semantic_baseline": false
    },
    "focused_real_tool_failure_context": {},
    "generated_module_inventory": [
      {
        "bytes": 1343,
        "modules": [
          "Activation"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Activation.sv",
        "sha256": "b97e531118c6bad1ac3f7932d59571acf83c593c675e66e154183f7a8d7f3561"
      },
      {
        "bytes": 20962,
        "modules": [
          "AttentionGQA"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/AttentionGQA.sv",
        "sha256": "2a94f89ff835aeca9112ba63b2db8068462d3137adb62b0630c7280b1c405855"
      },
      {
        "bytes": 1122,
        "modules": [
          "ElementwiseMul"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ElementwiseMul.sv",
        "sha256": "69c05d7cb8ce0b95b073d89a3e8421f4cf3ed7cac04add46c6282f4dcc69a102"
      },
      {
        "bytes": 5500,
        "modules": [
          "GatedMLP"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GatedMLP.sv",
        "sha256": "f3f1fda6d573a2d71ce6a2da1f9d23829726022fbd6d4a277baa24f723e00b57"
      },
      {
        "bytes": 1223,
        "modules": [
          "GeneratedAcceleratorTop"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GeneratedAcceleratorTop.sv",
        "sha256": "93d2e6315adc9a28e97851e409e1386202dbab1f6e0714b01b4f780a1cd69369"
      },
      {
        "bytes": 1997,
        "modules": [
          "GeneratedAxiDdrTop"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GeneratedAxiDdrTop.sv",
        "sha256": "08725a0f4f70c36f61af54dcd9b62ee2bb2c28ca2f4a2221516ffef9bb50670d"
      },
      {
        "bytes": 17008,
        "modules": [
          "Linear"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear.sv",
        "sha256": "08c7071ca79b5920eb3bc0bfa6ba76d641b35a37ec3dc53737386e5e1fcd1a32"
      },
      {
        "bytes": 5186,
        "modules": [
          "Linear_1"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_1.sv",
        "sha256": "ba4b12284c86abcd9e25ca0d8e26a83755f37bf171b1610d384f8625a4e2b6ae"
      },
      {
        "bytes": 17456,
        "modules": [
          "Linear_2"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_2.sv",
        "sha256": "501ad31f1afccb98b394e76506a39dd452e76ea074f2df22e6b4a6408f2ec0e1"
      },
      {
        "bytes": 89037,
        "modules": [
          "Linear_4"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_4.sv",
        "sha256": "8e9ddc07ef79f55e39eb10ae8a129e1d583f0a20112487d08c84768ea5430eef"
      },
      {
        "bytes": 8430,
        "modules": [
          "LlamaStyleBlock"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/LlamaStyleBlock.sv",
        "sha256": "741f61ec99813c4bb77283cf37ac9d49018dcc4a41e002ce03383e1605c5a3a3"
      },
      {
        "bytes": 69380,
        "modules": [
          "QKVProjection"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/QKVProjection.sv",
        "sha256": "6793df322f5b62a65bc6d67687530d9217a1aebe15a23c2af294d29470f0e7cb"
      },
      {
        "bytes": 1522,
        "modules": [
          "Queue1792_StreamBeat"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Queue1792_StreamBeat.sv",
        "sha256": "df5948642a45b33fab84bfb8c7baccabc49bfd7b466691e3ce73d7f5bdd8c7cf"
      },
      {
        "bytes": 1639,
        "modules": [
          "Queue4_StreamBeat"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Queue4_StreamBeat.sv",
        "sha256": "86c8135584062490714aed3d56ef7ef03ffb3bb924fd05e98fcbf9bc86786bcd"
      },
      {
        "bytes": 4382,
        "modules": [
          "QwenLayerPipelineTop",
          "QwenMultiLayerSystemTop"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/QwenMultiLayerSystemTop.sv",
        "sha256": "2c10f5a5a11c2543f7cde19a21d1a9a93e02b57b709bb6242d4f51ccb1af4a0d"
      },
      {
        "bytes": 668,
        "modules": [
          "RMSNorm"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/RMSNorm.sv",
        "sha256": "4e8e18caa1b83df77bc04b4ee875350e2494b39c79b97f080ec6a4eae0183ff2"
      },
      {
        "bytes": 1525,
        "modules": [
          "ResidualAdd"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ResidualAdd.sv",
        "sha256": "1255cade684f0e71f545a4aaef9f4b243299658c2e902a3d4c3b29425f555af4"
      },
      {
        "bytes": 821,
        "modules": [
          "RoPE"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/RoPE.sv",
        "sha256": "5e822d41e93d4f287989940dd6c5d99928ff44de27426ff4fda2f7657c304388"
      },
      {
        "bytes": 719,
        "modules": [
          "VectorNorm"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/VectorNorm.sv",
        "sha256": "2fe7a7f9f10900c83711f730e1e05ce541f26ed1929b5f136b58feb317d33d08"
      },
      {
        "bytes": 496,
        "modules": [
          "ram_1792x256"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ram_1792x256.sv",
        "sha256": "3f248758619c7e2430d0ec99c72ae09583436690c9f9ca5debea7a39c5bc3e2b"
      },
      {
        "bytes": 490,
        "modules": [
          "ram_4x129"
        ],
        "path": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ram_4x129.sv",
        "sha256": "4b83d9ec1613a2a6a823fe4569ad6fd95dd6f1e6790ce2a691fb9be74e83681a"
      }
    ],
    "localized_semantic_failure": {
      "beat_index": null,
      "candidate_stage_ids": [
        "stage_02_residual_add_1",
        "stage_08_residual_add_2"
      ],
      "candidate_stages": [
        {
          "index": 2,
          "kind": "residual",
          "op": "residual_add_1",
          "source": "Residual.scala",
          "stage_id": "stage_02_residual_add_1",
          "template_id": "residual"
        },
        {
          "index": 8,
          "kind": "residual",
          "op": "residual_add_2",
          "source": "Residual.scala",
          "stage_id": "stage_08_residual_add_2",
          "template_id": "residual"
        }
      ],
      "candidate_template_sources": [
        "Residual.scala"
      ],
      "evidence_type": "single_layer_pipeline_contract",
      "expected_output_sha256": null,
      "expected_value": {
        "every_dependency_has_different_token_overlap": true,
        "every_stage_keeps_pipeline_filled": true,
        "whole_sequence_barrier_forbidden": true
      },
      "failure_class": "intra_layer_spatial_pipeline_violation",
      "failure_mode": "completed_pipeline_overlap_violation",
      "input_fingerprint_sha256": "83f58f1246a324c3b62d2d657c5e81156ef058652022e4fbd564581b385e7be8",
      "lane_index": null,
      "logical_index": null,
      "observed_value": {
        "completed_pipeline_overlap_violation": true,
        "failed_dependency_overlap_evidence": [
          {
            "boundary_id": "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
            "different_token_overlap_observed": false,
            "dst_stage": "stage_08_residual_add_2",
            "overlaps": [],
            "src_stage": "stage_02_residual_add_1"
          }
        ],
        "failed_stage_turnover_evidence": [],
        "whole_sequence_barrier_evidence": []
      },
      "pipeline_trace_sha256": "8b721485e310341bbe5651973089a4fecadf56204a235ae1a78ec8185ae23b94",
      "rtl_output_sha256": null,
      "summary": "source-bound real VCS produced 0 failed token turnovers and 1 failed dependency overlaps",
      "template_pairs": [
        {
          "generated_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
          "persistent_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
          "sha256": "110c9830386481d39b786ca9e1ed6115aacea674c87f16430f5a319bdd3a9e34",
          "template_source": "Residual.scala"
        }
      ],
      "template_source": null,
      "testbench_sha256": null,
      "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
    },
    "omitted_redundant_context": [
      "byte-identical persistent template bodies after compiled semantic baseline",
      "unrelated emitted SystemVerilog bodies outside the earliest real-tool causal slice",
      "board and backend case material outside single_layer_closure",
      "superseded broad stage-planning reports already projected into current immutable requirements"
    ],
    "prior_capability_repair_evidence": {
      "binding_materialization": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/dut_weight_binding_materialization.json",
      "patch_application": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/agent_patch_application.json",
      "policy": "when present, these are authoritative feedback for the next repair iteration",
      "repair_execution_report": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_execution_report.json",
      "requested_validation": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/agent_requested_validation.json"
    },
    "schema_version": "spatialaccagent.repair_source_bundle.v1",
    "trusted_numeric_support": {
      "blockers": [],
      "files": [
        {
          "bytes": 8776,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/AddRecFN.scala",
          "destination_sha256": "2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85",
          "source": "src/resource/hardfloat/AddRecFN.scala",
          "source_sha256": "2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85"
        },
        {
          "bytes": 3476,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/CompareRecFN.scala",
          "destination_sha256": "b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d",
          "source": "src/resource/hardfloat/CompareRecFN.scala",
          "source_sha256": "b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d"
        },
        {
          "bytes": 4428,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64.scala",
          "destination_sha256": "ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0",
          "source": "src/resource/hardfloat/DivSqrtRecF64.scala",
          "source_sha256": "ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0"
        },
        {
          "bytes": 33929,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64_mulAddZ31.scala",
          "destination_sha256": "9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776",
          "source": "src/resource/hardfloat/DivSqrtRecF64_mulAddZ31.scala",
          "source_sha256": "9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776"
        },
        {
          "bytes": 20218,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecFN_small.scala",
          "destination_sha256": "e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f",
          "source": "src/resource/hardfloat/DivSqrtRecFN_small.scala",
          "source_sha256": "e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f"
        },
        {
          "bytes": 3417,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/INToRecFN.scala",
          "destination_sha256": "92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb",
          "source": "src/resource/hardfloat/INToRecFN.scala",
          "source_sha256": "92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb"
        },
        {
          "bytes": 15293,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulAddRecFN.scala",
          "destination_sha256": "be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037",
          "source": "src/resource/hardfloat/MulAddRecFN.scala",
          "source_sha256": "be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037"
        },
        {
          "bytes": 5706,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulRecFN.scala",
          "destination_sha256": "cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d",
          "source": "src/resource/hardfloat/MulRecFN.scala",
          "source_sha256": "cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d"
        },
        {
          "bytes": 6827,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToIN.scala",
          "destination_sha256": "e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3",
          "source": "src/resource/hardfloat/RecFNToIN.scala",
          "source_sha256": "e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3"
        },
        {
          "bytes": 3958,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToRecFN.scala",
          "destination_sha256": "97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09",
          "source": "src/resource/hardfloat/RecFNToRecFN.scala",
          "source_sha256": "97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09"
        },
        {
          "bytes": 13901,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RoundAnyRawFNToRecFN.scala",
          "destination_sha256": "31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d",
          "source": "src/resource/hardfloat/RoundAnyRawFNToRecFN.scala",
          "source_sha256": "31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d"
        },
        {
          "bytes": 2880,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/classifyRecFN.scala",
          "destination_sha256": "787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16",
          "source": "src/resource/hardfloat/classifyRecFN.scala",
          "source_sha256": "787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16"
        },
        {
          "bytes": 3925,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/common.scala",
          "destination_sha256": "ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb",
          "source": "src/resource/hardfloat/common.scala",
          "source_sha256": "ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb"
        },
        {
          "bytes": 2853,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/fNFromRecFN.scala",
          "destination_sha256": "7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d",
          "source": "src/resource/hardfloat/fNFromRecFN.scala",
          "source_sha256": "7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d"
        },
        {
          "bytes": 5105,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/primitives.scala",
          "destination_sha256": "134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31",
          "source": "src/resource/hardfloat/primitives.scala",
          "source_sha256": "134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31"
        },
        {
          "bytes": 3037,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromFN.scala",
          "destination_sha256": "39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce",
          "source": "src/resource/hardfloat/rawFloatFromFN.scala",
          "source_sha256": "39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce"
        },
        {
          "bytes": 2885,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromIN.scala",
          "destination_sha256": "d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8",
          "source": "src/resource/hardfloat/rawFloatFromIN.scala",
          "source_sha256": "d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8"
        },
        {
          "bytes": 2877,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromRecFN.scala",
          "destination_sha256": "bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317",
          "source": "src/resource/hardfloat/rawFloatFromRecFN.scala",
          "source_sha256": "bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317"
        },
        {
          "bytes": 2352,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/recFNFromFN.scala",
          "destination_sha256": "90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d",
          "source": "src/resource/hardfloat/recFNFromFN.scala",
          "source_sha256": "90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d"
        },
        {
          "bytes": 3237,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/resizeRawFloat.scala",
          "destination_sha256": "702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561",
          "source": "src/resource/hardfloat/resizeRawFloat.scala",
          "source_sha256": "702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561"
        },
        {
          "bytes": 811,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/Precision.scala",
          "destination_sha256": "4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b",
          "source": "src/main/scala/QuantCommon/Precision.scala",
          "source_sha256": "4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b"
        },
        {
          "bytes": 395,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FpBackend.scala",
          "destination_sha256": "053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709",
          "source": "src/main/scala/QuantCommon/FpBackend.scala",
          "source_sha256": "053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709"
        },
        {
          "bytes": 18853,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/XilinxFpCompat.scala",
          "destination_sha256": "f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7",
          "source": "src/main/scala/QuantCommon/XilinxFpCompat.scala",
          "source_sha256": "f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7"
        },
        {
          "bytes": 10596,
          "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FP32.scala",
          "destination_sha256": "f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5",
          "source": "src/main/scala/QuantCommon/FP32.scala",
          "source_sha256": "f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5"
        }
      ],
      "policy": {
        "read_only_for_repair_agent": true,
        "rounding": "HardFloat round_near_even",
        "simulator_only_arithmetic": false,
        "synthesizable": true
      },
      "schema_version": "spatialaccagent.trusted_numeric_support.v1",
      "source": "existing repository HardFloat and QuantCommon Chisel-7-compatible implementation",
      "status": "pass"
    },
    "verification_scope": "single_layer_closure"
  },
  "repair_step_id": "repair_step.00",
  "resource_resume_binding_materialization": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/dut_weight_binding_materialization.json",
  "resource_resume_capability_probe": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_step_00_verification_capability_probe_resource_resume.json",
  "resource_resume_dependency_refresh": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_step_00_verification_capability_probe_dependency_refresh_resource_resume.json",
  "resource_resume_pre_materialization_dependency_refresh": null,
  "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
  "schema_version": "spatialaccagent.verification_capability_repair_package.v0",
  "semantic_template_baseline": {
    "pre_existing_emitted_systemverilog_is_not_the_harness_source": true,
    "progress": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/semantic_template_repair_progress.json",
    "repair_deferred_until_real_localized_failure": false,
    "status": "localized_repair_authorized"
  },
  "single_layer_harness_required": true,
  "source_sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json",
  "stage": "repair_execution",
  "stage_id": "stage_02_residual_add_1",
  "target_modules": [
    "residual_add_1",
    "residual_add_2"
  ],
  "template_candidates": [],
  "trusted_numeric_support": {
    "blockers": [],
    "files": [
      {
        "bytes": 8776,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/AddRecFN.scala",
        "destination_sha256": "2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85",
        "source": "src/resource/hardfloat/AddRecFN.scala",
        "source_sha256": "2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85"
      },
      {
        "bytes": 3476,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/CompareRecFN.scala",
        "destination_sha256": "b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d",
        "source": "src/resource/hardfloat/CompareRecFN.scala",
        "source_sha256": "b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d"
      },
      {
        "bytes": 4428,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64.scala",
        "destination_sha256": "ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0",
        "source": "src/resource/hardfloat/DivSqrtRecF64.scala",
        "source_sha256": "ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0"
      },
      {
        "bytes": 33929,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64_mulAddZ31.scala",
        "destination_sha256": "9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776",
        "source": "src/resource/hardfloat/DivSqrtRecF64_mulAddZ31.scala",
        "source_sha256": "9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776"
      },
      {
        "bytes": 20218,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecFN_small.scala",
        "destination_sha256": "e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f",
        "source": "src/resource/hardfloat/DivSqrtRecFN_small.scala",
        "source_sha256": "e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f"
      },
      {
        "bytes": 3417,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/INToRecFN.scala",
        "destination_sha256": "92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb",
        "source": "src/resource/hardfloat/INToRecFN.scala",
        "source_sha256": "92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb"
      },
      {
        "bytes": 15293,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulAddRecFN.scala",
        "destination_sha256": "be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037",
        "source": "src/resource/hardfloat/MulAddRecFN.scala",
        "source_sha256": "be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037"
      },
      {
        "bytes": 5706,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulRecFN.scala",
        "destination_sha256": "cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d",
        "source": "src/resource/hardfloat/MulRecFN.scala",
        "source_sha256": "cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d"
      },
      {
        "bytes": 6827,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToIN.scala",
        "destination_sha256": "e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3",
        "source": "src/resource/hardfloat/RecFNToIN.scala",
        "source_sha256": "e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3"
      },
      {
        "bytes": 3958,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToRecFN.scala",
        "destination_sha256": "97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09",
        "source": "src/resource/hardfloat/RecFNToRecFN.scala",
        "source_sha256": "97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09"
      },
      {
        "bytes": 13901,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RoundAnyRawFNToRecFN.scala",
        "destination_sha256": "31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d",
        "source": "src/resource/hardfloat/RoundAnyRawFNToRecFN.scala",
        "source_sha256": "31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d"
      },
      {
        "bytes": 2880,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/classifyRecFN.scala",
        "destination_sha256": "787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16",
        "source": "src/resource/hardfloat/classifyRecFN.scala",
        "source_sha256": "787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16"
      },
      {
        "bytes": 3925,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/common.scala",
        "destination_sha256": "ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb",
        "source": "src/resource/hardfloat/common.scala",
        "source_sha256": "ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb"
      },
      {
        "bytes": 2853,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/fNFromRecFN.scala",
        "destination_sha256": "7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d",
        "source": "src/resource/hardfloat/fNFromRecFN.scala",
        "source_sha256": "7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d"
      },
      {
        "bytes": 5105,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/primitives.scala",
        "destination_sha256": "134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31",
        "source": "src/resource/hardfloat/primitives.scala",
        "source_sha256": "134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31"
      },
      {
        "bytes": 3037,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromFN.scala",
        "destination_sha256": "39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce",
        "source": "src/resource/hardfloat/rawFloatFromFN.scala",
        "source_sha256": "39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce"
      },
      {
        "bytes": 2885,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromIN.scala",
        "destination_sha256": "d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8",
        "source": "src/resource/hardfloat/rawFloatFromIN.scala",
        "source_sha256": "d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8"
      },
      {
        "bytes": 2877,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromRecFN.scala",
        "destination_sha256": "bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317",
        "source": "src/resource/hardfloat/rawFloatFromRecFN.scala",
        "source_sha256": "bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317"
      },
      {
        "bytes": 2352,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/recFNFromFN.scala",
        "destination_sha256": "90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d",
        "source": "src/resource/hardfloat/recFNFromFN.scala",
        "source_sha256": "90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d"
      },
      {
        "bytes": 3237,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/resizeRawFloat.scala",
        "destination_sha256": "702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561",
        "source": "src/resource/hardfloat/resizeRawFloat.scala",
        "source_sha256": "702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561"
      },
      {
        "bytes": 811,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/Precision.scala",
        "destination_sha256": "4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b",
        "source": "src/main/scala/QuantCommon/Precision.scala",
        "source_sha256": "4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b"
      },
      {
        "bytes": 395,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FpBackend.scala",
        "destination_sha256": "053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709",
        "source": "src/main/scala/QuantCommon/FpBackend.scala",
        "source_sha256": "053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709"
      },
      {
        "bytes": 18853,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/XilinxFpCompat.scala",
        "destination_sha256": "f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7",
        "source": "src/main/scala/QuantCommon/XilinxFpCompat.scala",
        "source_sha256": "f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7"
      },
      {
        "bytes": 10596,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FP32.scala",
        "destination_sha256": "f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5",
        "source": "src/main/scala/QuantCommon/FP32.scala",
        "source_sha256": "f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5"
      }
    ],
    "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/trusted_numeric_support.json",
    "policy": {
      "read_only_for_repair_agent": true,
      "rounding": "HardFloat round_near_even",
      "simulator_only_arithmetic": false,
      "synthesizable": true
    },
    "schema_version": "spatialaccagent.trusted_numeric_support.v1",
    "source": "existing repository HardFloat and QuantCommon Chisel-7-compatible implementation",
    "status": "pass"
  },
  "trusted_numeric_support_compile": {
    "cache_reused": true,
    "command": [
      "sbt",
      "--no-server",
      "Compile/compile"
    ],
    "input_fingerprint_sha256": "1eb33dcfb41d50455b76c3363f22ebf82df653b542945cb76015db5cd3118f40",
    "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/trusted_numeric_support_compile.json",
    "result": {
      "duration_sec": 4.4789251450274605,
      "returncode": 0,
      "status": "pass",
      "stderr_tail": "",
      "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[success] Total time: 1 s, completed Jul 11, 2026, 9:59:20 AM\n",
      "summary": "returncode=0"
    },
    "schema_version": "spatialaccagent.trusted_numeric_support_compile.v1",
    "status": "pass"
  },
  "verification_scope": "single_layer_closure",
  "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
}
</verification_capability_repair_package>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "endpoint_configured": true,
  "enforce": true,
  "locked_model": "gpt-5.6-sol",
  "mode": "llm",
  "model": "gpt-5.6-sol",
  "model_override_approval_path": "",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "xhigh",
  "requested_model_override": "",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

<sacg_memory>
{
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0245",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:30:03+00:00",
      "transition_id": "transition.0158"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0246",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "transition_id": "transition.0159"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0247",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:04:49+00:00",
      "transition_id": "transition.0160"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0248",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0249",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0250",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0251",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "transition_id": "transition.0162"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0252",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    }
  ],
  "open_backtrack_requests": [],
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0094",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:39:55+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0095",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:16:02+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0096",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:38:23+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0097",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:44:34+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0098",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T13:48:39+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0099",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:28:43+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0100",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:34:52+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0101",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-22T04:40:47+00:00"
    }
  ],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0245",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:30:03+00:00",
      "transition_id": "transition.0158"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0246",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "transition_id": "transition.0159"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0247",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:04:49+00:00",
      "transition_id": "transition.0160"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0248",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0249",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0250",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0251",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "transition_id": "transition.0162"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0252",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    }
  ],
  "recent_failure_lessons": [
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0094",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "stage": "stage7.verification",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest executed failing current-layer gate is case_multilayer_pipeline; its real-tool report proves that the DUT binding does not cover every required Transformer-block weight across all target layers and that a hash-verified multi-layer pipeline harness is missing. The detailed VCS functional simulator was not run because prerequisite gates were not satisfied, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, ordering, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them. SACG-memory truth reports 25 active contamination barriers, 10 open retry requests, and no open backtrack requests; no retry reconciliation contract was supplied. Prior rejected Stage7 and Stage8 artifacts are therefore planning/debug evidence only until a clean retry passes the selected DAG, obtains checker-bound promotion evidence, and reconciles SACG trust state. The conditional specialist review supports the technical capability-gap classification and repair sequence, but its contrary statement that SACG has no active blockers is superseded by sacg_memory_truth and role consensus cannot replace checker evidence.",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0095",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest executed failing current-layer gate is case_multilayer_pipeline; its real-tool report proves that the DUT binding does not cover every required Transformer-block weight across all target layers and that a hash-verified multi-layer pipeline harness is missing. The detailed VCS functional simulator was not run because prerequisite gates were not satisfied, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, ordering, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them. SACG-memory truth reports 25 active contamination barriers, 10 open retry requests, and no open backtrack requests; no retry reconciliation contract was supplied. Prior rejected Stage7 and Stage8 artifacts are therefore planning/debug evidence only until a clean retry passes the selected DAG, obtains checker-bound promotion evidence, and reconciles SACG trust state. The conditional specialist review supports the technical capability-gap classification and repair sequence, but its contrary statement that SACG has no active blockers is superseded by sacg_memory_truth and role consensus cannot replace checker evidence.",
      "timestamp": "2026-07-13T09:16:02+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0096",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "stage": "stage7.verification",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest and only executed failing current-layer gate is real_tool.case_multilayer_pipeline, whose checker report proves incomplete all-target-layer Transformer-block DUT weight binding and a missing hash-verified multi-layer pipeline harness. The detailed board-wrapped VCS simulator was not run because prerequisite gates failed, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, order, deadlock, DDR, or AXI-protocol defect. Exact board-interface discovery passed, and certified operator-leaf and connected single-layer evidence remains reusable because no current boundary trace contradicts it and SACG truth has zero open backtrack requests. SACG truth nevertheless has 30 active contamination barriers and 12 open retry requests; prior rejected Stage7 and Stage8 artifacts are planning/debug evidence only until a clean retry passes the selected DAG, receives checker-bound promotion evidence, and completes SACG trust reconciliation. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but its stale assertion that SACG has no active blockers is superseded by sacg_memory_truth and cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0097",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest and only executed failing current-layer gate is real_tool.case_multilayer_pipeline, whose checker report proves incomplete all-target-layer Transformer-block DUT weight binding and a missing hash-verified multi-layer pipeline harness. The detailed board-wrapped VCS simulator was not run because prerequisite gates failed, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, order, deadlock, DDR, or AXI-protocol defect. Exact board-interface discovery passed, and certified operator-leaf and connected single-layer evidence remains reusable because no current boundary trace contradicts it and SACG truth has zero open backtrack requests. SACG truth nevertheless has 30 active contamination barriers and 12 open retry requests; prior rejected Stage7 and Stage8 artifacts are planning/debug evidence only until a clean retry passes the selected DAG, receives checker-bound promotion evidence, and completes SACG trust reconciliation. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but its stale assertion that SACG has no active blockers is superseded by sacg_memory_truth and cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-13T09:44:34+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0098",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0099",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "stage": "stage7.verification",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0100",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0101",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    }
  ],
  "recent_stage_outcomes": [
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest executed failing current-layer gate is case_multilayer_pipeline; its real-tool report proves that the DUT binding does not cover every required Transformer-block weight across all target layers and that a hash-verified multi-layer pipeline harness is missing. The detailed VCS functional simulator was not run because prerequisite gates were not satisfied, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, ordering, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them. SACG-memory truth reports 25 active contamination barriers, 10 open retry requests, and no open backtrack requests; no retry reconciliation contract was supplied. Prior rejected Stage7 and Stage8 artifacts are therefore planning/debug evidence only until a clean retry passes the selected DAG, obtains checker-bound promotion evidence, and reconciles SACG trust state. The conditional specialist review supports the technical capability-gap classification and repair sequence, but its contrary statement that SACG has no active blockers is superseded by sacg_memory_truth and role consensus cannot replace checker evidence."
      ],
      "id": "stage_outcome.0103",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest executed failing current-layer gate is case_multilayer_pipeline; its real-tool report proves that the DUT binding does not cover every required Transformer-block weight across all target layers and that a hash-verified multi-layer pipeline harness is missing. The detailed VCS functional simulator was not run because prerequisite gates were not satisfied, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, ordering, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them. SACG-memory truth reports 25 active contamination barriers, 10 open retry requests, and no open backtrack requests; no retry reconciliation contract was supplied. Prior rejected Stage7 and Stage8 artifacts are therefore planning/debug evidence only until a clean retry passes the selected DAG, obtains checker-bound promotion evidence, and reconciles SACG trust state. The conditional specialist review supports the technical capability-gap classification and repair sequence, but its contrary statement that SACG has no active blockers is superseded by sacg_memory_truth and role consensus cannot replace checker evidence."
      ],
      "id": "stage_outcome.0104",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-13T09:16:02+00:00",
      "transition_id": "transition.0152"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest and only executed failing current-layer gate is real_tool.case_multilayer_pipeline, whose checker report proves incomplete all-target-layer Transformer-block DUT weight binding and a missing hash-verified multi-layer pipeline harness. The detailed board-wrapped VCS simulator was not run because prerequisite gates failed, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, order, deadlock, DDR, or AXI-protocol defect. Exact board-interface discovery passed, and certified operator-leaf and connected single-layer evidence remains reusable because no current boundary trace contradicts it and SACG truth has zero open backtrack requests. SACG truth nevertheless has 30 active contamination barriers and 12 open retry requests; prior rejected Stage7 and Stage8 artifacts are planning/debug evidence only until a clean retry passes the selected DAG, receives checker-bound promotion evidence, and completes SACG trust reconciliation. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but its stale assertion that SACG has no active blockers is superseded by sacg_memory_truth and cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0105",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest and only executed failing current-layer gate is real_tool.case_multilayer_pipeline, whose checker report proves incomplete all-target-layer Transformer-block DUT weight binding and a missing hash-verified multi-layer pipeline harness. The detailed board-wrapped VCS simulator was not run because prerequisite gates failed, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, order, deadlock, DDR, or AXI-protocol defect. Exact board-interface discovery passed, and certified operator-leaf and connected single-layer evidence remains reusable because no current boundary trace contradicts it and SACG truth has zero open backtrack requests. SACG truth nevertheless has 30 active contamination barriers and 12 open retry requests; prior rejected Stage7 and Stage8 artifacts are planning/debug evidence only until a clean retry passes the selected DAG, receives checker-bound promotion evidence, and completes SACG trust reconciliation. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but its stale assertion that SACG has no active blockers is superseded by sacg_memory_truth and cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0106",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-13T09:44:34+00:00",
      "transition_id": "transition.0155"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
      ],
      "id": "stage_outcome.0107",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "transition_id": "transition.0159"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0108",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0109",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "transition_id": "transition.0162"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0110",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    }
  ],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 44,
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0221",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T04:15:41+00:00",
      "transition_id": "transition.0142"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0222",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T04:19:31+00:00",
      "transition_id": "transition.0143"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0223",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T04:20:24+00:00",
      "transition_id": "transition.0144"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0224",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T05:41:26+00:00",
      "transition_id": "transition.0145"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0225",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T05:41:26+00:00",
      "transition_id": "transition.0145"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0226",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T05:41:26+00:00",
      "transition_id": "transition.0145"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0227",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T05:46:48+00:00",
      "transition_id": "transition.0146"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0228",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T05:48:26+00:00",
      "transition_id": "transition.0147"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0229",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:21:23+00:00",
      "transition_id": "transition.0148"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0230",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:21:23+00:00",
      "transition_id": "transition.0148"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0231",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:21:23+00:00",
      "transition_id": "transition.0148"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0232",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T08:26:28+00:00",
      "transition_id": "transition.0149"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0233",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T08:28:09+00:00",
      "transition_id": "transition.0150"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0234",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0235",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0236",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0237",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T09:16:02+00:00",
      "transition_id": "transition.0152"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0238",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T09:21:47+00:00",
      "transition_id": "transition.0153"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0239",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0240",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0241",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0242",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T09:44:34+00:00",
      "transition_id": "transition.0155"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0243",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:24:32+00:00",
      "transition_id": "transition.0156"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0244",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:28:03+00:00",
      "transition_id": "transition.0157"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0245",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:30:03+00:00",
      "transition_id": "transition.0158"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0246",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "transition_id": "transition.0159"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0247",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:04:49+00:00",
      "transition_id": "transition.0160"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0248",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0249",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0250",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0251",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "transition_id": "transition.0162"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0252",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    }
  ],
  "active_contamination_barriers_truncated": true,
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 18,
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0084",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-12T11:39:06+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0085",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-12T11:41:54+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0086",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T03:59:05+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0087",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T04:01:36+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0088",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T04:15:41+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0089",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T04:19:31+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0090",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T05:41:26+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0091",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T05:46:48+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0092",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:21:23+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0093",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:26:28+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0094",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:39:55+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0095",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:16:02+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0096",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:38:23+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0097",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:44:34+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0098",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T13:48:39+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0099",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:28:43+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0100",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:34:52+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0101",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-22T04:40:47+00:00"
    }
  ],
  "open_retry_requests_truncated": false,
  "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
  "schema_version": "spatialaccagent.sacg_memory_truth.v0",
  "truth_source": "source_sacg_state.memory"
}
</sacg_memory_truth>

<action_grounding_registry>
{
  "acceptance_checkers": [
    "sacg_static_check",
    "task_card_check",
    "model_config_check",
    "numeric_policy_check",
    "template_coverage_check",
    "parameter_binding_static_check",
    "code_generation_manifest_static_check",
    "stream_plan_check",
    "memory_runtime_plan_check",
    "boundary_contract_check",
    "failure_localization_check",
    "targeted_replay_check",
    "causal_repair_context_check",
    "template_binding_static_check",
    "repair_boundary_check",
    "verification_plan_static_check",
    "tool_protocol_check",
    "human_boundary_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "sacg_reference_check",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "single_transformer_layer",
    "case_multilayer_pipeline",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_operator_leaf_semantic_evidence",
    "case_single_layer_semantic_evidence",
    "case_board_semantic_evidence",
    "real_weight_semantic_evidence_check",
    "case_tb_scaffold",
    "case_board_interface_discovery",
    "case_axi_ddr_interface",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "board_runtime",
    "functional_sim",
    "deadlock_watchdog",
    "data_order_trace_check",
    "transfer_count_check",
    "addr_map_check",
    "numeric_compare",
    "artifact_hash_check",
    "codegen_compile_gate_check",
    "codegen_contract_check",
    "codegen_package_static_check",
    "verification_artifact_contract_check",
    "required_real_tool_evidence_check",
    "real_tool.case_real_weight_artifacts",
    "real_tool.boundary_contract_check",
    "real_tool.case_leaf_functional",
    "real_tool.case_leaf_golden_compare",
    "real_tool.case_tb_scaffold",
    "real_tool.case_single_transformer_layer",
    "real_tool.case_single_layer_functional",
    "real_tool.case_single_layer_golden_compare",
    "real_tool.case_multilayer_functional",
    "real_tool.case_pipeline_deadlock_check",
    "real_tool.case_vcs_functional_sim",
    "real_tool.case_verilator_functional_sim",
    "real_tool.case_deadlock_axi_check",
    "real_tool.case_board_interface_discovery",
    "real_tool.case_axi_ddr_interface",
    "real_tool.case_axi_protocol_check",
    "real_tool.case_ddr_image_roundtrip",
    "real_tool.case_vivado_synthesis",
    "real_tool.case_vivado_synthesis_report_check",
    "real_tool.case_vivado_implementation",
    "real_tool.case_vivado_implementation_report_check",
    "real_tool.case_board_shell_wrapper_generate",
    "real_tool.case_runtime_abi_check",
    "real_tool.case_runtime_bitstream",
    "real_tool.app_shell_target_discovery_contract",
    "real_tool.app_shell_target_hint_synthesis",
    "real_tool.app_shell_target_discovery_after_hint",
    "real_tool.board_runtime",
    "real_tool.app_shell_runtime_bitstream",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "output_validity_check",
    "targeted_failed_checker_rerun",
    "verification_action_audit_check",
    "llm_io_quality_check",
    "llm_semantic_extraction_check",
    "no_static_keyword_semantic_matching_check",
    "sacg_memory_check",
    "stage_retry_request_check",
    "stage_backtrack_request_check",
    "stage_artifact_trust_barrier_check",
    "backend_app_shell_integration_contract_static_check",
    "backend_app_shell_target_discovery_check",
    "backend_app_shell_target_hint_synthesis_check",
    "backend_bounded_recovery_action_check",
    "backend_recovery_approval_ingest_check"
  ],
  "policy": "Executable actions should use these tool/checker names when applicable. If a required capability is missing, name it as planned_tool.<short_name> and make the rationale say that multi-agent system capability implementation is required.",
  "schema_version": "spatialaccagent.action_grounding_registry.v0",
  "tool_roles": [
    "sacg_validate",
    "sacg_static_check",
    "task_card_check",
    "model_config_check",
    "numeric_policy_check",
    "template_coverage_check",
    "template_binding_static_check",
    "parameter_binding_static_check",
    "code_generation_manifest_static_check",
    "stream_plan_check",
    "memory_runtime_plan_check",
    "repair_boundary_check",
    "boundary_contract_generate",
    "failure_slice_localization",
    "boundary_trace_rerun",
    "targeted_replay",
    "causal_repair_context_pack",
    "verification_plan_static_check",
    "tool_protocol_check",
    "human_boundary_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "sacg_reference_check",
    "codegen_compile_gate",
    "codegen_contract_check",
    "codegen_package_static_check",
    "verification_artifact_contract_check",
    "required_real_tool_evidence_check",
    "real_tool_evidence_check",
    "case_real_weight_artifacts",
    "case_target_model_reference",
    "case_semantic_testbench",
    "case_operator_leaf_semantic_evidence",
    "case_single_layer_semantic_evidence",
    "case_board_semantic_evidence",
    "case_stage_leaf_static",
    "boundary_contract_check",
    "case_leaf_functional",
    "case_leaf_golden_compare",
    "case_single_transformer_layer",
    "case_single_layer_functional",
    "case_single_layer_golden_compare",
    "single_transformer_layer",
    "case_multilayer_pipeline",
    "case_multilayer_functional",
    "case_pipeline_deadlock_check",
    "case_tb_scaffold",
    "case_vcs_functional_sim",
    "functional_sim",
    "functional_sim_contract_check",
    "case_verilator_functional_sim",
    "case_weight_manifest_generate",
    "case_tb_scaffold_generate",
    "case_vcs_evidence_analyzer",
    "deadlock_watchdog",
    "data_order_trace_check",
    "transfer_count_check",
    "addr_map_check",
    "numeric_compare",
    "artifact_hash_check",
    "case_deadlock_axi_check",
    "case_board_interface_discovery",
    "case_axi_ddr_interface",
    "case_axi_protocol_check",
    "case_ddr_image_roundtrip",
    "case_vivado_synthesis",
    "case_vivado_synthesis_report_check",
    "case_vivado_implementation",
    "case_vivado_implementation_report_check",
    "case_board_shell_wrapper_generate",
    "case_runtime_abi_check",
    "case_runtime_bitstream",
    "app_shell_target_discovery_contract",
    "app_shell_target_hint_synthesis",
    "app_shell_target_discovery_after_hint",
    "backend_bounded_recovery_action",
    "backend_recovery_approval_ingest",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "board_runtime",
    "output_validity_check",
    "targeted_failed_checker_rerun",
    "bounded_template_repair",
    "pipeline_repair",
    "memory_runtime_repair",
    "architecture_review",
    "team_aggregate",
    "verification_action_audit",
    "llm_io_quality_check",
    "llm_semantic_extraction",
    "no_static_keyword_semantic_matching",
    "sacg_memory_update",
    "stage_retry_request",
    "stage_backtrack_request",
    "stage_artifact_trust_barrier",
    "app_shell_runtime_bitstream"
  ]
}
</action_grounding_registry>

<action_contract_examples>
[
  {
    "acceptance_checkers": [
      "case_real_weight_artifacts",
      "case_target_model_reference",
      "case_semantic_testbench"
    ],
    "action_type": "verification_evidence_preparation",
    "consumes": [
      "artifact.input.model_config",
      "artifact.input.numeric_policy",
      "artifact.stage3.pipeline_plan",
      "current case-adapter target checkpoint",
      "generated/memory/dut_weight_binding_manifest.json"
    ],
    "id": "example.prepare_real_model_semantic_verification",
    "on_failure": "treat missing reference, explicit tolerance, semantic harness, or DUT weight consumption as a verification-capability/code-generation blocker; do not run a legacy fallback test or promote the layer.",
    "produces": [
      "verification/real_weights/full_tensor_catalog.json",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "verification/semantic_testbench/dut_weight_binding_requirements.json"
    ],
    "rationale": "Build immutable semantic evidence from the current case adapter before any hardware correctness claim.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_weight_manifest_generate",
      "case_target_model_reference",
      "case_semantic_testbench"
    ]
  },
  {
    "acceptance_checkers": [
      "functional_sim",
      "data_order_trace_check",
      "deadlock_watchdog",
      "real_weight_semantic_evidence_check"
    ],
    "action_type": "real_tool_execution",
    "consumes": [
      "artifact.stage6.verification_artifact_contract",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "generated/memory/dut_weight_binding_manifest.json",
      "verification/board_simulation/board_simulation_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to Stage8 repair with the violated SACG constraints; do not proceed to Vivado.",
    "produces": [
      "verification/vcs/case_functional_sim.log",
      "verification/board_simulation/rtl_output.memh",
      "verification/debug_closure/boundary_trace.json",
      "verification/case_diagnostics/vcs_functional_diagnosis.json",
      "verification/semantic_evidence/board_axi_ddr.json"
    ],
    "rationale": "Run a real simulator after static hierarchy and artifact gates pass.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_vcs_functional_sim",
      "case_vcs_evidence_analyzer",
      "case_board_semantic_evidence"
    ]
  },
  {
    "acceptance_checkers": [
      "planned_checker.formal_axi_property_check"
    ],
    "action_type": "system_capability_gap",
    "consumes": [
      "artifact.stage6.verification_plan"
    ],
    "id": "example.declare_missing_capability",
    "on_failure": "block promotion until the planned checker is implemented or an approved equivalent exists.",
    "produces": [
      "planned checker implementation task"
    ],
    "rationale": "The design team needs a checker not yet implemented by the multi-agent system.",
    "requires_approval": true,
    "stage": "verification",
    "tool_roles": [
      "planned_tool.formal_axi_property_runner"
    ]
  },
  {
    "acceptance_checkers": [
      "backend_app_shell_target_hint_synthesis_check",
      "backend_bounded_recovery_action_check",
      "human_boundary_check"
    ],
    "action_type": "bounded_recovery",
    "consumes": [
      "artifact.stage9.app_shell_integration_contract",
      "artifact.stage9.app_shell_target_selection_decision",
      "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json"
    ],
    "id": "example.ambiguous_backend_target_recovery",
    "on_failure": "keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval",
    "produces": [
      "artifact.stage9.backend_bounded_recovery_actions"
    ],
    "rationale": "Real backend evidence produced multiple plausible shell integration targets, so the design team must not guess.",
    "requires_approval": true,
    "stage": "backend_board",
    "tool_roles": [
      "app_shell_target_hint_synthesis",
      "app_shell_target_discovery_after_hint"
    ]
  }
]
</action_contract_examples>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "adaptive_observation_decision": {
      "additionalProperties": false,
      "properties": {
        "evidence_refs": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "field_observations": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "evidence_pointer": {
                "type": "string"
              },
              "interpretation": {
                "type": "string"
              },
              "observed_value": {},
              "semantic_role": {
                "enum": [
                  "control",
                  "handshake",
                  "payload",
                  "counter",
                  "state",
                  "error",
                  "contract"
                ],
                "type": "string"
              }
            },
            "required": [
              "evidence_pointer",
              "observed_value",
              "semantic_role",
              "interpretation"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "frontier_id": {
          "type": "string"
        },
        "mode": {
          "enum": [
            "direct_executed_contradiction",
            "direct_tool_failure",
            "deepen_simulation_observation"
          ],
          "type": "string"
        },
        "probe_plan": {
          "additionalProperties": false,
          "properties": {
            "add_or_update_probe_ids": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "bounded_window": {
              "type": "string"
            },
            "event_match": {
              "additionalProperties": {
                "type": [
                  "string",
                  "number",
                  "integer",
                  "boolean",
                  "null"
                ]
              },
              "type": "object"
            },
            "required_event_fields": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "retire_probe_ids": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "target_boundary": {
              "type": "string"
            },
            "trigger_condition": {
              "type": "string"
            }
          },
          "required": [
            "target_boundary",
            "add_or_update_probe_ids",
            "retire_probe_ids",
            "required_event_fields",
            "event_match",
            "trigger_condition",
            "bounded_window"
          ],
          "type": "object"
        },
        "rationale": {
          "type": "string"
        },
        "schema_version": {
          "type": "string"
        }
      },
      "required": [
        "schema_version",
        "mode",
        "frontier_id",
        "evidence_refs",
        "field_observations",
        "probe_plan",
        "rationale"
      ],
      "type": "object"
    },
    "agent": {
      "type": "string"
    },
    "approval_required_for": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "blocked_reasons": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "causal_prediction": {
      "additionalProperties": false,
      "properties": {
        "evidence_refs": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "expected_progress_changes": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "metric": {
                "type": "string"
              },
              "relation": {
                "enum": [
                  "increase_from_baseline",
                  "decrease_from_baseline",
                  "change_from_baseline",
                  "no_change_from_baseline",
                  "reach_at_least",
                  "reach_at_most"
                ],
                "type": "string"
              },
              "value": {
                "type": [
                  "number",
                  "null"
                ]
              }
            },
            "required": [
              "metric",
              "relation",
              "value"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "falsified_if": {
          "type": "string"
        },
        "intervention_family": {
          "type": "string"
        },
        "target_frontier_id": {
          "type": "string"
        }
      },
      "required": [
        "intervention_family",
        "target_frontier_id",
        "expected_progress_changes",
        "falsified_if",
        "evidence_refs"
      ],
      "type": "object"
    },
    "checkpoint_impact": {
      "additionalProperties": false,
      "properties": {
        "affected_cctg_nodes": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "changed_state_elements": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "evidence_refs": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "rationale": {
          "type": "string"
        },
        "state_schema_change": {
          "enum": [
            "none",
            "compatible",
            "incompatible",
            "unknown"
          ],
          "type": "string"
        },
        "status": {
          "enum": [
            "ready",
            "unknown"
          ],
          "type": "string"
        }
      },
      "required": [
        "status",
        "state_schema_change",
        "affected_cctg_nodes",
        "changed_state_elements",
        "evidence_refs",
        "rationale"
      ],
      "type": "object"
    },
    "file_edits": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "content": {
            "type": "string"
          },
          "expected_sha256": {
            "type": "string"
          },
          "json_content": {
            "additionalProperties": true,
            "type": "object"
          },
          "operation": {
            "enum": [
              "create",
              "replace",
              "replace_text",
              "merge_json"
            ],
            "type": "string"
          },
          "path": {
            "type": "string"
          },
          "rationale": {
            "type": "string"
          },
          "text_replacements": {
            "items": {
              "additionalProperties": false,
              "properties": {
                "new_text": {
                  "type": "string"
                },
                "old_text": {
                  "type": "string"
                }
              },
              "required": [
                "old_text",
                "new_text"
              ],
              "type": "object"
            },
            "type": "array"
          }
        },
        "required": [
          "path",
          "operation",
          "expected_sha256",
          "content",
          "rationale"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "requested_validation": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "argv": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "cwd": {
            "type": "string"
          },
          "purpose": {
            "type": "string"
          }
        },
        "required": [
          "purpose",
          "argv",
          "cwd"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "required_capabilities": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "capability_id": {
            "type": "string"
          },
          "debug_layer": {
            "type": "string"
          },
          "producer_scope": {
            "type": "string"
          },
          "rationale": {
            "type": "string"
          },
          "required_evidence": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "target_modules": {
            "items": {
              "type": "string"
            },
            "type": "array"
          }
        },
        "required": [
          "capability_id",
          "debug_layer",
          "producer_scope",
          "target_modules",
          "required_evidence",
          "rationale"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "root_cause": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "stage": {
      "const": "repair_execution",
      "type": "string"
    },
    "status": {
      "type": "string"
    },
    "summary": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "agent",
    "stage",
    "status",
    "summary",
    "root_cause",
    "file_edits",
    "requested_validation",
    "blocked_reasons",
    "approval_required_for"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
