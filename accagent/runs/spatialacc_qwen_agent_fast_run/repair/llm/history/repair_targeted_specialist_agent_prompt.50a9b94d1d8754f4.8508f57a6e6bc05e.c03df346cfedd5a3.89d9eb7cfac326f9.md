<agent>
repair_targeted_specialist_agent
</agent>

<task>
Review only the routed repair ambiguity using the current CCTG slice, SACG evidence, current-layer gate states, and human boundary. Identify the earliest violated contract and the smallest legal repair. Do not reopen lower layers without a bound contradiction or run higher-layer tools before current closure.
</task>

<rules>
1. Review only the supplied artifact summary and named constraints.
2. If inputs include subtask.role_assignment, act as that chip-design-team specialist: stay inside its mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope boundaries.
3. For sub-agent work, make observations, risks, approval_required_for, and executable_actions usable by peer agents through the declared handoff_to and acceptance_checkers; do not silently assume another specialist's responsibility.
4. Treat sacg_memory as the shared long-context design memory: preserve design goals, failure lessons, retry requests, backtrack requests, and contamination barriers.
5. Treat sacg_memory_truth as the authoritative current blocker set: only active_contamination_barriers and open retry/backtrack requests listed there are current SACG-memory blockers.
6. Do not infer active blockers from historical, closed, superseded, rejected, or recently summarized records when sacg_memory_truth shows the corresponding active/open count is zero.
7. If sacg_memory contains open backtrack_requests or contamination_barriers relevant to this stage, address them explicitly in observations and executable_actions.
8. If inputs include a retry_reconciliation_contract for the current stage, distinguish previous failed artifacts from the candidate retry artifacts: same-stage retry requests/barriers are downstream-consumption blockers until promotion, but they are not independent blockers for approving a refined current-stage contract that explicitly supersedes them after all current-stage checks pass.
9. If inputs include stage_gate_policy, use it to classify current-stage blocking risks versus later-stage actions.
10. If inputs include role_slice_policy or presence_summary, do not infer a field is missing merely because detailed rows were omitted from a compact/role-specific prompt slice.
11. When presence_summary says an artifact class exists, report missing-detail concerns as handoff/action items unless the visible checker status proves a current-stage blocker.
12. Report cross-layer consistency risks across model, shape, numeric policy, data order, memory, runtime, implementation, and board facts.
13. Keep actions bounded and executable by later tools/checkers.
14. Populate executable_actions with concrete next tool/repair actions; each action must name consumed artifacts, produced artifacts, tool roles, acceptance checkers, failure handling, and approval need.
15. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
16. For backend/app-shell target discovery, treat the LLM as the adaptive board-integration engineer: convert supplied board materials and real Vivado evidence into target_discovery_policy updates with cited artifacts; if evidence is ambiguous, require bounded approval instead of guessing names.
17. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name> and state the implementation gap in rationale.
18. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
19. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
20. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
21. When hierarchical_learning_context is supplied, treat it as live hash-validated lower-layer knowledge rather than informal history. Reuse its certified invariants, and reopen a lower layer only for a current trace that explicitly contradicts a named invariant.
22. When hierarchical_learning_context supplies connected-kernel timing knowledge, preserve its elastic variable-latency token-pipeline semantics: required boundary order and cross-token overlap matter, while strict same-cycle start/end across unequal-latency stages is not required.
23. At board scope, distinguish independent AXI/prefetch progress from output or lifecycle-frontier progress. A current frontier stall localizes what to observe next, but is neither a pass claim nor a preselected RTL root cause.
24. A board output-frontier symptom alone cannot reopen a certified connected kernel. Require a current hash-bound lower-layer contradiction with direct core start, ingress, egress, named causal-boundary, and current-certificate evidence before scheduling lower-layer revalidation.
25. Before any functional pass, require a complete target-checkpoint tensor catalog, deterministic or real input provenance, target-model inference expected outputs for the same input/checkpoint, a resolved numeric comparison tolerance (current-run values first, otherwise frozen framework loose defaults), generated semantic testbench hashes, and proof that the DUT consumed every required bound weight.
26. Applying the recorded framework loose defaults for initially missing atol, rtol, or max_mismatch_fraction is authorized and is not a repair-time tolerance change. Never derive or loosen those values from DUT output.
27. A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.
28. During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.
29. At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.
30. Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.
31. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
32. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
</rules>

<routing_trigger>
board_wrapper_or_pipeline_integration
</routing_trigger>

<candidate_repair_plan>
{
  "case_adapter": {
    "case_id": "qwen2_hf_case",
    "model_family": "qwen2",
    "source": "built_in_case_adapter",
    "status": "ready"
  },
  "diagnostics": {
    "case_vcs_functional": {
      "applicability_binding": {
        "applicable_rerun_gates": [
          "case_vcs_functional_sim",
          "case_vcs_evidence_analyzer"
        ],
        "diagnosed_failure_class": "vcs_compile_failure",
        "input_fingerprint_sha256": "28d8a1712be807c2a22361ed911ebc1b7354469a771eed47080a240256ebe7d6",
        "origin_gates": [
          "case_vcs_functional_sim"
        ],
        "origin_layer": "board_axi_ddr_wrapped_system",
        "policy": {
          "cross_layer_reuse_is_read_only_without_an_explicit_targeted_backtrack": true,
          "current_failed_gate_must_match_origin_or_target_rerun_gate": true,
          "live_source_artifact_hashes_must_match": true
        },
        "preflight_manifest_projection_sha256": "0e516113a4e85ef083f0366346fe66dbd5d53a100fa361770e48e40a4345d2fa",
        "schema_version": "spatialaccagent.diagnosis_applicability_binding.v1",
        "source_artifacts": [
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
            "role": "board_vcs_runner_report",
            "sha256": "276af7db3989312445969053d31ba4eb58c0c236f1d712dc27072f2d5f712864"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json",
            "role": "board_simulation_manifest",
            "sha256": "ec987156b5da237655d6cc8a29e630f9ff7d9e95372e48eaef0370ad85d1bac6"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/board_source_identity.json",
            "role": "board_source_identity",
            "sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
            "role": "semantic_testbench_manifest",
            "sha256": "3fc2032bd34d9fe1d295cf54ff106c1d7d4be2fc7cbd0195b027443d9c1b37a7"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
            "role": "dut_weight_binding_manifest",
            "sha256": "ad6e14c1317c656c107b3ff64cdafbc941456a2f36754b95ded6098183be91be"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_executed_manifest.json",
            "role": "executed_board_manifest",
            "sha256": "85dbe4cdd75123ecb109a6279d0e115bc34cff46ff6c0190529007a3d14558e1"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
            "role": "sacg_cctg_causal_slice",
            "sha256": "1142355918920e199b71ef10fa5cb2f79adf2caa0098a3045389d891e044e307"
          }
        ],
        "source_identity_sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66",
        "target_layer": "board_axi_ddr_wrapped_system"
      },
      "blockers": [
        "vcs_compile_failure: Error-[XMRE] Cross-module reference resolution error"
      ],
      "board_wrapper_identity": {
        "axi_interfaces_sha256": "5ace0c653616c888ab1dd5734256787e5cee5edc35566dd17eab602f7ef3cf60",
        "complete_identity_bound_by_path_and_sha256": true,
        "compute_slot_abi_sha256": "dac5c980fa4cb0ae1719e575c78ede9bff33fc35f9aaeec60cc8baa9b0c9836b",
        "exact_user_sample_wrapper": true,
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/board_source_identity.json",
        "schema_version": "spatialaccagent.exact_sample_board_source_identity.v2",
        "selected_simulation_source_closure_sha256": "6665a9df4e0b86fdbd47c48e76b63137069f4c2505d914d6ceee233447a1c5c5",
        "sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66",
        "simulation_hashes_match_source": true,
        "status": "pass",
        "timing_contract_sha256": "3e151369b174741fa9fe817608c812a8c9cd873102151752443688be4faab342",
        "vivado_facts_sha256": "70b9ea0e70c4c32d19248d7ccf5f1324865b9379c22ce6c364887587835758df"
      },
      "debug_closure": {
        "boundary_trace_failed_count": 6,
        "boundary_trace_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
        "boundary_trace_record_count": 77,
        "live_progress": {
          "history": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress_history.jsonl",
          "latest": {},
          "raw_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
          "snapshot": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress.json",
          "status": "pending_first_flushed_event",
          "zero_time_livelock_evidence": {}
        },
        "progress_event_summary": {},
        "status": "trace_ready"
      },
      "diagnosis_status": "ready",
      "failure_class": "vcs_compile_failure",
      "failure_evidence": {
        "adaptive_semantic_stall_evidence": {},
        "board_to_lower_layer_contradiction_evidence": {
          "required_observation_contract": {
            "current_trace_and_lower_certificate_hashes_required": true,
            "earliest_causal_owner_must_match_target_layer": true,
            "kernel_egress_ready_required": true,
            "kernel_ingress_complete_required": true,
            "kernel_start_accepted_required": true,
            "named_earliest_causal_boundary_required": true
          },
          "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
          "status": "insufficient_evidence",
          "target_debug_layer": "single_transformer_layer_kernel",
          "validation_errors": [
            "board trace contains no explicit lower-layer contradiction evidence"
          ]
        },
        "checkpoint_artifacts": {
          "mode": "disabled",
          "status": "not_run",
          "summary": "checkpoint execution was not requested"
        },
        "checkpoint_execution": {
          "acceptance_eligible": true,
          "candidate_screening": false,
          "enabled": false,
          "mode": "disabled",
          "policy": null,
          "request_path": null,
          "request_sha256": null,
          "status": "pass"
        },
        "checkpoint_runtime_execution_failure": {},
        "compile": {
          "duration_sec": 43.75482978101354,
          "failure_class": "remote_tool_failure",
          "remote_state": "done",
          "returncode": 1,
          "status": "fail"
        },
        "failure_class": "vcs_compile_failure",
        "first_real_error": "Error-[XMRE] Cross-module reference resolution error",
        "intra_layer_pipeline_violation_evidence": {},
        "live_progress": {
          "history": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress_history.jsonl",
          "latest": {},
          "raw_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
          "snapshot": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress.json",
          "status": "pending_first_flushed_event",
          "zero_time_livelock_evidence": {}
        },
        "log_tail": " design file '../sources/Queue4_StreamBeat.sv'\nParsing design file '../sources/Queue4_StreamBeat_2.sv'\nParsing design file '../sources/RMSNorm.sv'\nParsing design file '../sources/RecFNToIN_e8_s24_i16.sv'\nParsing design file '../sources/RecFNToRecFN.sv'\nParsing design file '../sources/RecFNToRecFN_8.sv'\nParsing design file '../sources/ResidualAdd.sv'\nParsing design file '../sources/RoPE.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie5_is11_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie6_is25_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie7_is36_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is24_oe5_os11.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is26_oe8_os24.sv'\nParsing design file '../sources/RoundRawFNToRecFN_e8_s24.sv'\nParsing design file '../sources/SingleLayerSemanticHarness.sv'\nParsing design file '../sources/Softmax.sv'\nParsing design file '../sources/VectorNorm.sv'\nParsing design file '../sources/expTable_2048x26.sv'\nParsing design file '../sources/ram_113x269.sv'\nParsing design file '../sources/ram_1792x269.sv'\nParsing design file '../sources/ram_2x144.sv'\nParsing design file '../sources/ram_2x269.sv'\nParsing design file '../sources/ram_4x144.sv'\nParsing design file '../sources/sigmoidTable_129x19.sv'\nParsing design file '../sources/ConnectedObservableLlamaStyleBlock_Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nParsing included file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'.\nParsing design file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'\nParsing design file '../sources/app_shell_9p_cnn_core_0_1.v'\nParsing design file '../sources/spatialacc_exact_board_multilayer_tb.sv'\nParsing design file '../sources/spatialacc_axi_protocol_monitor.sv'\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nCPU time: 19.496 seconds to compile\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nDoing common elaboration \nsh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n                         Chronologic VCS (TM)\n         Version S-2021.09_Full64 -- Thu Sep 10 06:11:56 2026\n\n                    Copyright (c) 1991 - 2021 Synopsys, Inc.\n   This software and the associated documentation are proprietary to Synopsys,\n Inc. This software may only be used in accordance with the terms and conditions\n of a written license agreement with Synopsys, Inc. All other use, reproduction,\n   or distribution of this software is strictly prohibited.  Licensed Products\n     communicate with Synopsys servers for the purpose of providing software\n    updates, detecting software piracy and verifying that customers are using\n    Licensed Products in conformity with the applicable License Key for such\n  Licensed Products. Synopsys will use information gathered in connection with\n    this process to deliver software updates and pursue software pirates and\n                                   infringers.\n\n Inclusivity & Diversity - Visit SolvNetPlus to read the \"Synopsys Statement on\n            Inclusivity and Diversity\" (Refer to article 000036315 at\n                        https://solvnetplus.synopsys.com)\n\nsh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nTop Level Modules:\n       spatialacc_exact_board_multilayer_tb\nNo TimeScale specified\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 313\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_gate_io_in_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[6] = \n  dut.spatialacc_single_kernel.core.mlp_gate_io_in_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 316\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_up_io_in_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[7] = \n  dut.spatialacc_single_kernel.core.mlp_up_io_in_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 319\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_gate_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[8] = \n  dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 322\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_up_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[9] = \n  dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 325\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_mul_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[10] = \n  dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 328\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_down_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[11] = \n  dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_data__bore;\n  \n\n6 errors\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nCPU time: 4.268 seconds to compile\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n\n common elaboration failed\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
        "progress_event_summary": {
          "adaptive_semantic_stall_evidence": {
            "fixed_cycle_timeout": false,
            "fixed_wall_clock_timeout": false,
            "policy": {
              "heartbeat_multiplier": 16384,
              "minimum_stall_snapshot_count": 8,
              "semantic_gap_multiplier": 32,
              "target_work_multiplier": 512
            },
            "reason": "no complete progress events",
            "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
            "status": "observing"
          },
          "causal_event_tail": [],
          "first_stalled_boundary": null,
          "heartbeat_event_count": 0,
          "intra_layer_pipeline_violation_evidence": {
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "fixed_cycle_timeout": false,
            "fixed_wall_clock_timeout": false,
            "reason": "complete token-input geometry is not yet observable",
            "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
            "status": "observing"
          },
          "last_complete_record": {},
          "last_cycle": null,
          "last_semantic_progress_cycle": null,
          "last_semantic_progress_event": {},
          "latest_event_by_kind": {},
          "latest_stall_snapshot": {},
          "policy": {
            "heartbeat_proves_clock_activity_not_semantic_progress": true,
            "wall_clock_elapsed_never_classifies_a_hardware_stall": true
          },
          "progress_epoch": 0,
          "record_count": 0,
          "schema_version": "spatialaccagent.board_live_progress_summary.v1",
          "semantic_progress_event_count": 0,
          "silent_cycles": null,
          "status": "observing",
          "terminal_event_seen": false,
          "validation_errors": []
        },
        "related_source_ids": [
          "certified_kernel.0028.bc6c3a1512b4cdcc",
          "certified_kernel.0029.e28bb26e3f4d07ed",
          "certified_kernel.0030.423624e2b3a2cf82",
          "certified_kernel.0031.93d84deb44695ccd",
          "certified_kernel.0032.b7627d43fcf3d968",
          "certified_kernel.0033.6283b71b5dd93db2",
          "certified_kernel.0034.fff321245d139c9a",
          "certified_kernel.0035.c337024af70fe224",
          "certified_kernel.0036.9ccc10c190e7c663",
          "certified_kernel.0037.0b393161c147493f",
          "certified_kernel.0038.4a81f71c5e3e8694",
          "certified_kernel.0039.bcf9e75ab35fa0a9",
          "certified_kernel.0040.4523c49935ae674e",
          "certified_kernel.0041.f16ba7437f6426cc",
          "certified_kernel.0042.4ce4890e9101c62e",
          "certified_kernel.0043.0140f3ba6a856368",
          "certified_kernel.0044.6737169741922866",
          "certified_kernel.0045.13dc26d729b5db6d",
          "certified_kernel.0046.d62b861bbdf6aa58",
          "certified_kernel.0047.dbfb0e992ff81f9b",
          "certified_kernel.0048.60495b714b32137e",
          "certified_kernel.0049.041b2747a0e21a65",
          "certified_kernel.0050.4c1c4e82a212507a",
          "certified_kernel.0051.c57a64b4bf72d070",
          "certified_kernel.0052.f3a4e84fbfb7564f",
          "certified_kernel.0053.2e4a6ca180b7989c",
          "certified_kernel.0054.14ed4e7f18671d70",
          "certified_kernel.0055.14549c6d0d0411b1",
          "certified_kernel.0056.18642537333ecc6c",
          "certified_kernel.0057.1295b1eccfd57a74",
          "certified_kernel.0058.9f6f7cd74bfb7999",
          "certified_kernel.0059.fda2ea5872b1567e",
          "certified_kernel.0060.14f9fb972e98522e",
          "certified_kernel.0061.6c89abc693126950",
          "certified_kernel.0062.d3e25305dc97cddd",
          "generated-board-source:compute_slot_adapter",
          "generated-board-source:exact_multilayer_tb",
          "generated-board-source:axi_protocol_monitor"
        ],
        "repair_scope": "generated_source_or_compile_plan",
        "runner_phase": "remote_vcs",
        "sacg_cctg_causal_slice": {
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
          "sha256": "1142355918920e199b71ef10fa5cb2f79adf2caa0098a3045389d891e044e307",
          "value": {
            "failure_class": "vcs_compile_failure",
            "input_fingerprint_sha256": "28d8a1712be807c2a22361ed911ebc1b7354469a771eed47080a240256ebe7d6",
            "llm_analysis_contract": {
              "must_not_edit_hardware_for_transport_or_tool_environment_failure": true,
              "must_not_reuse_a_prior_fingerprint_runtime_slice": true,
              "use_earliest_real_tool_error_before_runtime_graph": true
            },
            "reason": "SACG/CCTG runtime frontier selection requires a completed VCS compile and an attempted simulator execution",
            "remote_workdir": "/home/hyyuan/workspace/spatialaccagent_artifacts/board_vcs/spatialacc_qwen_agent_fast_run/28d8a1712be8_12470299663893081060349601635849053884099861832889245104859094",
            "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
            "schema_version": "spatialaccagent.sacg_cctg_causal_slice.v1",
            "status": "not_applicable_before_runtime_execution"
          }
        },
        "simulation": {
          "status": "not_run",
          "summary": "remote VCS compile failed"
        },
        "structured_failures": {
          "elaborated_hierarchy": {
            "report_valid": false
          },
          "exact_board_acceptance_checks": [
            {
              "blockers": [
                "simulation.status is not pass"
              ],
              "name": "simulation_identity_binding",
              "status": "fail"
            },
            {
              "blockers": [
                "debug observability contract schema_version is invalid",
                "debug observability implementation is not simulation/testbench only",
                "debug observability contract lacks current-DAG pipeline boundary observation declaration"
              ],
              "name": "exact_sample_testbench_contract",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.dynamic_evidence_records[1] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
                "simulation.dynamic_evidence_records[2] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/progress_event_log.jsonl",
                "simulation.dynamic_evidence_records[3] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
                "simulation.dynamic_evidence_records[5] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/runtime_loader_report.json",
                "simulation.dynamic_evidence_records[6] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json"
              ],
              "name": "dynamic_real_tool_evidence",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.execution_evidence.status is not pass",
                "simulation.execution_evidence.compile.exit_code is not zero",
                "simulation.execution_evidence.simulation.exit_code is not zero",
                "simulation execution did not complete with its manifest-bound pass marker",
                "simulation.execution_evidence.simulation.log artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
                "simulation.execution_evidence.elaborated_hierarchy_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/hierarchy_report.json",
                "simulation.execution_evidence.elaborated_hierarchy_report.evidence_refs must be a non-empty list"
              ],
              "name": "real_tool_execution_identity_and_logs",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.elaborated_hierarchy.evidence_refs must be a non-empty list",
                "simulation.elaborated_hierarchy is not a successful real-tool elaboration",
                "simulation.elaborated_hierarchy.elaboration_tool is missing",
                "elaborated hierarchy does not bind the exact sample source closure hash",
                "elaborated hierarchy does not bind the simulator compile source set hash",
                "elaborated hierarchy does not bind the compute-slot ABI hash",
                "simulation.elaborated_hierarchy.elaboration_log is missing",
                "simulation.elaborated_hierarchy.instances is empty"
              ],
              "name": "elaborated_exact_top_and_accelerator_binding",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.protocol_monitor_results is not pass for all AXI interfaces",
                "protocol monitor result is not pass for AXI interface: c0_ddr4_s_axi",
                "protocol monitor result has violations or lacks an explicit empty list: c0_ddr4_s_axi",
                "protocol monitor result lacks positive five-channel transaction counts: c0_ddr4_s_axi",
                "simulation.protocol_monitor_results[c0_ddr4_s_axi].structured_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json"
              ],
              "name": "dynamic_axi_protocol_monitor_results",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.pipeline_overlap_results.status is not pass",
                "pipeline overlap results do not bind elastic rate-insensitive semantics",
                "pipeline overlap results do not cover every required dataflow dependency",
                "pipeline overlap results do not involve every planned stage in required different-token overlap",
                "pipeline overlap results do not preserve token order",
                "pipeline overlap results permit serialized leaf execution",
                "pipeline overlap results incorrectly make stage turnover gaps functional gates",
                "pipeline overlap results incorrectly require all stages in the same cycle",
                "pipeline overlap results permit a whole-sequence operator barrier",
                "pipeline overlap results do not observe the complete planned stage count",
                "pipeline overlap results have no different-token overlap witness",
                "simulation.pipeline_overlap_results.structured_trace_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json"
              ],
              "name": "dynamic_intra_layer_spatial_pipeline_overlap",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.runtime_loader_results.status is not pass",
                "runtime loader results do not bind runtime_plan_contract_sha256",
                "runtime loader results do not bind runtime_image_manifest_contract_sha256",
                "runtime loader results do not bind runtime_image_sha256",
                "runtime loader results do not bind loader_abi_sha256",
                "runtime loader results do not bind load_schedule_sha256",
                "runtime loader results target_layer_count differs from the runtime authority",
                "runtime loader results do not prove every layer was loaded exactly once",
                "runtime loader results observed or did not exclude an early kernel start",
                "runtime loader results do not contain every target layer exactly once in order",
                "simulation.runtime_loader_results.layers[0] is missing",
                "simulation.runtime_loader_results.structured_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/runtime_loader_report.json"
              ],
              "name": "dynamic_runtime_loader_consumption",
              "status": "fail"
            }
          ],
          "pipeline_overlap": {
            "all_planned_stages_participate_in_required_overlap": null,
            "all_spatial_stages_concurrent_observed": null,
            "all_stages_same_cycle_concurrency_required": null,
            "diagnostic_maximum_concurrent_stage_count": null,
            "observed_different_token_overlap_count": null,
            "pipeline_semantics": null,
            "report_valid": false,
            "required_dependency_overlap_complete": null,
            "serial_leaf_execution_observed": null,
            "stage_turnover_gaps_are_diagnostic": null,
            "status": null,
            "structured_trace_report": {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
              "relative_path": "reports/pipeline_overlap_report.json",
              "sha256": null
            },
            "token_order_preserved": null,
            "whole_sequence_barrier_observed": null
          },
          "protocol_monitors": [
            {
              "copied": false,
              "interface": "c0_ddr4_s_axi",
              "missing_required_fields": [
                "status",
                "transaction_counts",
                "violations"
              ],
              "monitor_id": "monitor.c0_ddr4_s_axi",
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json",
              "reported_status": null,
              "schema_version": null,
              "sha256": null,
              "status": null,
              "structured_report": {
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json",
                "relative_path": "reports/axi_protocol_report.json",
                "sha256": null
              },
              "transaction_counts": null,
              "violation_count": null,
              "violations": null
            }
          ]
        },
        "supplemental_observation_artifacts": [
          {
            "artifact_kind": "jsonl_observation",
            "byte_count": 0,
            "copied": false,
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/connected_kernel_delta_transition.jsonl",
            "relative_path": "reports/connected_kernel_delta_transition.jsonl",
            "sha256": null,
            "status": "missing",
            "summary": {}
          }
        ],
        "termination_provenance": {
          "causal_classification": {
            "classification": "external_or_unattributed_termination",
            "deterministic_hdl_or_testbench_failure_proven": false,
            "simulator_infrastructure_failure_proven": false,
            "source_semantic_repair_eligible": false
          },
          "cycle_budget": {
            "configured_cycle_limit": null,
            "fixed_cycle_timeout": false,
            "last_observed_cycle": null
          },
          "exact_source_replay_fingerprint_sha256": "28d8a1712be807c2a22361ed911ebc1b7354469a771eed47080a240256ebe7d6",
          "exit_code": null,
          "final_committed_progress_event": {},
          "framework_termination": {
            "adaptive_semantic_stall": null,
            "zero_time_livelock": null
          },
          "missing_completion_reports_causal_classification": "termination_indeterminate",
          "observed_duration_sec": null,
          "raw_terminal_log_tail": "",
          "remote_state": "unknown",
          "runner_failure_class": null,
          "runner_process_provenance": {},
          "schema_version": "spatialaccagent.simulation_termination_provenance.v1",
          "signal_number": null,
          "simulator_terminal_log": {
            "failure_lines": [],
            "matched_lines": [],
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
            "schema_version": "spatialaccagent.simulation_runtime_failure_evidence.v1",
            "simulator_crash_lines": [],
            "status": "missing",
            "tail_lines": []
          },
          "status": "indeterminate",
          "terminal_progress_event_seen": false,
          "termination_source": "unclassified_termination",
          "testbench_observation_activity": {},
          "wall_clock_budget": {
            "configured_timeout_sec": null,
            "expired": false,
            "fixed_wall_clock_timeout": false,
            "unbounded": true
          }
        },
        "vcs_native_loop_report": {
          "artifact_count": 0,
          "enabled": false,
          "loop_detection_enabled_observed": false,
          "matched_simulation_log_markers": [],
          "native_loop_detected": false
        },
        "zero_time_livelock_evidence": {}
      },
      "real_weight_provenance": {
        "all_target_layers": false,
        "all_validation_layers": true,
        "binding_manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
        "board_validation_scope": {
          "errors": [],
          "scope": {
            "contract_sha256": "9a2654a4f96cf7b75af90baa28af9a55aed99aebb2d7131e2ba333802f68dffa",
            "covers_full_model": false,
            "mode": "configurable_prefix_pipeline_liveness",
            "model_layer_count": 24,
            "reference_output_layer_index": 0,
            "requires_next_layer_prefetch": false,
            "schema_version": "spatialaccagent.board_validation_scope.v1",
            "validation_layer_count": 1,
            "validation_layer_indices": [
              0
            ]
          },
          "status": "pass"
        },
        "consumed_tensor_hash_source": "dut_weight_binding_manifest.board_consumed_tensor_hashes",
        "consumed_tensor_hashes": [
          "0d0c2e986b79337c0af626b4696e2c5bfdbfea3ae899aad066b1224706b7e875",
          "1921a2d5bf9e6daa33c6030c52f132c9f8f5ee18527b762a98fcaa442a2b3fc6",
          "1fb9fda61dbaaeaa7f69ac5bca11cc5b3998264adead65c8af82ab53a620f545",
          "593585723059315bd94fa8e1ece653278448b30e895bc422db5053f6e32e072f",
          "7299b2470e85c07bead7e0472fa737f7c04821d666a10f261a391eedcacf6cfc",
          "7a311aab27e9aeef0934a1e37021060a03301a372f8b7e0f15a9c221a0c43142",
          "a515fc5f05e4cc898596d09bfcec7a04e8329dd88d1b9c1672af0f2f89b05028",
          "a7f1f3b0d91c595e9d81b7d9ebff9e3519786fb0741a9e1ea864082ffb403761",
          "bab918b63853c1da0f0796b6078b5249ad2a37122942ae1aa7d1ac6c06cd8b73",
          "bd43be7fb745d3091761ec97647df27bddf63c28007642d1100d577a5139ab81",
          "c439582c80056cff1002ea2a307eb0f28ad3b35618fd93fdef16584e216e3804",
          "de65160719848918e6b24ec9172371309fd74f9a9e7497316568f77d581abe51"
        ]
      },
      "repair_handoff": {
        "acceptance_contracts_to_revalidate": [],
        "acceptance_reminder": "Keep checkpoint, random input, golden, numeric policy, and exact sample wrapper hashes unchanged during repair.",
        "agent_should_apply_code_changes": true,
        "board_to_lower_layer_contradiction_evidence": {
          "required_observation_contract": {
            "current_trace_and_lower_certificate_hashes_required": true,
            "earliest_causal_owner_must_match_target_layer": true,
            "kernel_egress_ready_required": true,
            "kernel_ingress_complete_required": true,
            "kernel_start_accepted_required": true,
            "named_earliest_causal_boundary_required": true
          },
          "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
          "status": "insufficient_evidence",
          "target_debug_layer": "single_transformer_layer_kernel",
          "validation_errors": [
            "board trace contains no explicit lower-layer contradiction evidence"
          ]
        },
        "debug_layer": "board_axi_ddr_wrapped_system",
        "failure_class": "vcs_compile_failure",
        "first_real_error": "Error-[XMRE] Cross-module reference resolution error",
        "log_tail": " design file '../sources/Queue4_StreamBeat.sv'\nParsing design file '../sources/Queue4_StreamBeat_2.sv'\nParsing design file '../sources/RMSNorm.sv'\nParsing design file '../sources/RecFNToIN_e8_s24_i16.sv'\nParsing design file '../sources/RecFNToRecFN.sv'\nParsing design file '../sources/RecFNToRecFN_8.sv'\nParsing design file '../sources/ResidualAdd.sv'\nParsing design file '../sources/RoPE.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie5_is11_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie6_is25_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie7_is36_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is24_oe5_os11.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is26_oe8_os24.sv'\nParsing design file '../sources/RoundRawFNToRecFN_e8_s24.sv'\nParsing design file '../sources/SingleLayerSemanticHarness.sv'\nParsing design file '../sources/Softmax.sv'\nParsing design file '../sources/VectorNorm.sv'\nParsing design file '../sources/expTable_2048x26.sv'\nParsing design file '../sources/ram_113x269.sv'\nParsing design file '../sources/ram_1792x269.sv'\nParsing design file '../sources/ram_2x144.sv'\nParsing design file '../sources/ram_2x269.sv'\nParsing design file '../sources/ram_4x144.sv'\nParsing design file '../sources/sigmoidTable_129x19.sv'\nParsing design file '../sources/ConnectedObservableLlamaStyleBlock_Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nParsing included file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'.\nParsing design file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'\nParsing design file '../sources/app_shell_9p_cnn_core_0_1.v'\nParsing design file '../sources/spatialacc_exact_board_multilayer_tb.sv'\nParsing design file '../sources/spatialacc_axi_protocol_monitor.sv'\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nCPU time: 19.496 seconds to compile\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nDoing common elaboration \nsh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n                         Chronologic VCS (TM)\n         Version S-2021.09_Full64 -- Thu Sep 10 06:11:56 2026\n\n                    Copyright (c) 1991 - 2021 Synopsys, Inc.\n   This software and the associated documentation are proprietary to Synopsys,\n Inc. This software may only be used in accordance with the terms and conditions\n of a written license agreement with Synopsys, Inc. All other use, reproduction,\n   or distribution of this software is strictly prohibited.  Licensed Products\n     communicate with Synopsys servers for the purpose of providing software\n    updates, detecting software piracy and verifying that customers are using\n    Licensed Products in conformity with the applicable License Key for such\n  Licensed Products. Synopsys will use information gathered in connection with\n    this process to deliver software updates and pursue software pirates and\n                                   infringers.\n\n Inclusivity & Diversity - Visit SolvNetPlus to read the \"Synopsys Statement on\n            Inclusivity and Diversity\" (Refer to article 000036315 at\n                        https://solvnetplus.synopsys.com)\n\nsh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nTop Level Modules:\n       spatialacc_exact_board_multilayer_tb\nNo TimeScale specified\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 313\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_gate_io_in_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[6] = \n  dut.spatialacc_single_kernel.core.mlp_gate_io_in_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 316\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_up_io_in_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[7] = \n  dut.spatialacc_single_kernel.core.mlp_up_io_in_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 319\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_gate_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[8] = \n  dut.spatialacc_single_kernel.core.mlp_gate_io_out_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 322\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_up_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[9] = \n  dut.spatialacc_single_kernel.core.mlp_up_io_out_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 325\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_mul_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[10] = \n  dut.spatialacc_single_kernel.core.mlp_mul_io_out_bits_data__bore;\n  \n\n\nError-[XMRE] Cross-module reference resolution error\n../sources/spatialacc_exact_board_multilayer_tb.sv, 328\n  Error found while trying to resolve cross-module reference.\n  token 'mlp_down_io_out_bits_data__bore'.  Originating module \n  'spatialacc_exact_board_multilayer_tb'.\n  Source info: assign current_dag_boundary_payload[11] = \n  dut.spatialacc_single_kernel.core.mlp_down_io_out_bits_data__bore;\n  \n\n6 errors\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nCPU time: 4.268 seconds to compile\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n\n common elaboration failed\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
        "must_rerun": [
          "case_vcs_functional_sim",
          "case_vcs_evidence_analyzer"
        ],
        "next_stage": "repair",
        "related_source_ids": [
          "certified_kernel.0028.bc6c3a1512b4cdcc",
          "certified_kernel.0029.e28bb26e3f4d07ed",
          "certified_kernel.0030.423624e2b3a2cf82",
          "certified_kernel.0031.93d84deb44695ccd",
          "certified_kernel.0032.b7627d43fcf3d968",
          "certified_kernel.0033.6283b71b5dd93db2",
          "certified_kernel.0034.fff321245d139c9a",
          "certified_kernel.0035.c337024af70fe224",
          "certified_kernel.0036.9ccc10c190e7c663",
          "certified_kernel.0037.0b393161c147493f",
          "certified_kernel.0038.4a81f71c5e3e8694",
          "certified_kernel.0039.bcf9e75ab35fa0a9",
          "certified_kernel.0040.4523c49935ae674e",
          "certified_kernel.0041.f16ba7437f6426cc",
          "certified_kernel.0042.4ce4890e9101c62e",
          "certified_kernel.0043.0140f3ba6a856368",
          "certified_kernel.0044.6737169741922866",
          "certified_kernel.0045.13dc26d729b5db6d",
          "certified_kernel.0046.d62b861bbdf6aa58",
          "certified_kernel.0047.dbfb0e992ff81f9b",
          "certified_kernel.0048.60495b714b32137e",
          "certified_kernel.0049.041b2747a0e21a65",
          "certified_kernel.0050.4c1c4e82a212507a",
          "certified_kernel.0051.c57a64b4bf72d070",
          "certified_kernel.0052.f3a4e84fbfb7564f",
          "certified_kernel.0053.2e4a6ca180b7989c",
          "certified_kernel.0054.14ed4e7f18671d70",
          "certified_kernel.0055.14549c6d0d0411b1",
          "certified_kernel.0056.18642537333ecc6c",
          "certified_kernel.0057.1295b1eccfd57a74",
          "certified_kernel.0058.9f6f7cd74bfb7999",
          "certified_kernel.0059.fda2ea5872b1567e",
          "certified_kernel.0060.14f9fb972e98522e",
          "certified_kernel.0061.6c89abc693126950",
          "certified_kernel.0062.d3e25305dc97cddd",
          "generated-board-source:compute_slot_adapter",
          "generated-board-source:exact_multilayer_tb",
          "generated-board-source:axi_protocol_monitor"
        ],
        "repair_patterns": [],
        "repair_scope": "generated_source_or_compile_plan",
        "runner_phase": "remote_vcs",
        "sacg_cctg_causal_frontier": {
          "artifact_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
          "artifact_sha256": "1142355918920e199b71ef10fa5cb2f79adf2caa0098a3045389d891e044e307",
          "earliest_unproven_frontier": {},
          "hierarchical_certificate_projection": {},
          "status": "not_applicable_before_runtime_execution"
        },
        "structured_failures": {
          "elaborated_hierarchy": {
            "report_valid": false
          },
          "exact_board_acceptance_checks": [
            {
              "blockers": [
                "simulation.status is not pass"
              ],
              "name": "simulation_identity_binding",
              "status": "fail"
            },
            {
              "blockers": [
                "debug observability contract schema_version is invalid",
                "debug observability implementation is not simulation/testbench only",
                "debug observability contract lacks current-DAG pipeline boundary observation declaration"
              ],
              "name": "exact_sample_testbench_contract",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.dynamic_evidence_records[1] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
                "simulation.dynamic_evidence_records[2] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/progress_event_log.jsonl",
                "simulation.dynamic_evidence_records[3] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
                "simulation.dynamic_evidence_records[5] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/runtime_loader_report.json",
                "simulation.dynamic_evidence_records[6] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json"
              ],
              "name": "dynamic_real_tool_evidence",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.execution_evidence.status is not pass",
                "simulation.execution_evidence.compile.exit_code is not zero",
                "simulation.execution_evidence.simulation.exit_code is not zero",
                "simulation execution did not complete with its manifest-bound pass marker",
                "simulation.execution_evidence.simulation.log artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
                "simulation.execution_evidence.elaborated_hierarchy_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/hierarchy_report.json",
                "simulation.execution_evidence.elaborated_hierarchy_report.evidence_refs must be a non-empty list"
              ],
              "name": "real_tool_execution_identity_and_logs",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.elaborated_hierarchy.evidence_refs must be a non-empty list",
                "simulation.elaborated_hierarchy is not a successful real-tool elaboration",
                "simulation.elaborated_hierarchy.elaboration_tool is missing",
                "elaborated hierarchy does not bind the exact sample source closure hash",
                "elaborated hierarchy does not bind the simulator compile source set hash",
                "elaborated hierarchy does not bind the compute-slot ABI hash",
                "simulation.elaborated_hierarchy.elaboration_log is missing",
                "simulation.elaborated_hierarchy.instances is empty"
              ],
              "name": "elaborated_exact_top_and_accelerator_binding",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.protocol_monitor_results is not pass for all AXI interfaces",
                "protocol monitor result is not pass for AXI interface: c0_ddr4_s_axi",
                "protocol monitor result has violations or lacks an explicit empty list: c0_ddr4_s_axi",
                "protocol monitor result lacks positive five-channel transaction counts: c0_ddr4_s_axi",
                "simulation.protocol_monitor_results[c0_ddr4_s_axi].structured_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json"
              ],
              "name": "dynamic_axi_protocol_monitor_results",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.pipeline_overlap_results.status is not pass",
                "pipeline overlap results do not bind elastic rate-insensitive semantics",
                "pipeline overlap results do not cover every required dataflow dependency",
                "pipeline overlap results do not involve every planned stage in required different-token overlap",
                "pipeline overlap results do not preserve token order",
                "pipeline overlap results permit serialized leaf execution",
                "pipeline overlap results incorrectly make stage turnover gaps functional gates",
                "pipeline overlap results incorrectly require all stages in the same cycle",
                "pipeline overlap results permit a whole-sequence operator barrier",
                "pipeline overlap results do not observe the complete planned stage count",
                "pipeline overlap results have no different-token overlap witness",
                "simulation.pipeline_overlap_results.structured_trace_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json"
              ],
              "name": "dynamic_intra_layer_spatial_pipeline_overlap",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.runtime_loader_results.status is not pass",
                "runtime loader results do not bind runtime_plan_contract_sha256",
                "runtime loader results do not bind runtime_image_manifest_contract_sha256",
                "runtime loader results do not bind runtime_image_sha256",
                "runtime loader results do not bind loader_abi_sha256",
                "runtime loader results do not bind load_schedule_sha256",
                "runtime loader results target_layer_count differs from the runtime authority",
                "runtime loader results do not prove every layer was loaded exactly once",
                "runtime loader results observed or did not exclude an early kernel start",
                "runtime loader results do not contain every target layer exactly once in order",
                "simulation.runtime_loader_results.layers[0] is missing",
                "simulation.runtime_loader_results.structured_report artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/runtime_loader_report.json"
              ],
              "name": "dynamic_runtime_loader_consumption",
              "status": "fail"
            }
          ],
          "pipeline_overlap": {
            "all_planned_stages_participate_in_required_overlap": null,
            "all_spatial_stages_concurrent_observed": null,
            "all_stages_same_cycle_concurrency_required": null,
            "diagnostic_maximum_concurrent_stage_count": null,
            "observed_different_token_overlap_count": null,
            "pipeline_semantics": null,
            "report_valid": false,
            "required_dependency_overlap_complete": null,
            "serial_leaf_execution_observed": null,
            "stage_turnover_gaps_are_diagnostic": null,
            "status": null,
            "structured_trace_report": {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
              "relative_path": "reports/pipeline_overlap_report.json",
              "sha256": null
            },
            "token_order_preserved": null,
            "whole_sequence_barrier_observed": null
          },
          "protocol_monitors": [
            {
              "copied": false,
              "interface": "c0_ddr4_s_axi",
              "missing_required_fields": [
                "status",
                "transaction_counts",
                "violations"
              ],
              "monitor_id": "monitor.c0_ddr4_s_axi",
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json",
              "reported_status": null,
              "schema_version": null,
              "sha256": null,
              "status": null,
              "structured_report": {
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json",
                "relative_path": "reports/axi_protocol_report.json",
                "sha256": null
              },
              "transaction_counts": null,
              "violation_count": null,
              "violations": null
            }
          ]
        },
        "termination_causal_classification": {
          "classification": "external_or_unattributed_termination",
          "deterministic_hdl_or_testbench_failure_proven": false,
          "simulator_infrastructure_failure_proven": false,
          "source_semantic_repair_eligible": false
        }
      },
      "root_cause_class": "vcs_compile_failure",
      "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
      "runner_phase": "remote_vcs",
      "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v4",
      "semantic_comparison": {
        "consumed_tensor_hash_source": "dut_weight_binding_manifest.board_consumed_tensor_hashes",
        "consumed_tensor_hashes": [
          "0d0c2e986b79337c0af626b4696e2c5bfdbfea3ae899aad066b1224706b7e875",
          "1921a2d5bf9e6daa33c6030c52f132c9f8f5ee18527b762a98fcaa442a2b3fc6",
          "1fb9fda61dbaaeaa7f69ac5bca11cc5b3998264adead65c8af82ab53a620f545",
          "593585723059315bd94fa8e1ece653278448b30e895bc422db5053f6e32e072f",
          "7299b2470e85c07bead7e0472fa737f7c04821d666a10f261a391eedcacf6cfc",
          "7a311aab27e9aeef0934a1e37021060a03301a372f8b7e0f15a9c221a0c43142",
          "a515fc5f05e4cc898596d09bfcec7a04e8329dd88d1b9c1672af0f2f89b05028",
          "a7f1f3b0d91c595e9d81b7d9ebff9e3519786fb0741a9e1ea864082ffb403761",
          "bab918b63853c1da0f0796b6078b5249ad2a37122942ae1aa7d1ac6c06cd8b73",
          "bd43be7fb745d3091761ec97647df27bddf63c28007642d1100d577a5139ab81",
          "c439582c80056cff1002ea2a307eb0f28ad3b35618fd93fdef16584e216e3804",
          "de65160719848918e6b24ec9172371309fd74f9a9e7497316568f77d581abe51"
        ],
        "expected_output_sha256": "92fc53de80c8caca6ea04cc69ab768a1f6db0e55a2ab0ebbd9ac0adc6e3c85b4",
        "expected_output_source": "target_model_inference",
        "numeric_metrics": {
          "not_run_reason": "exact-board VCS execution did not complete",
          "passed": false
        },
        "passed": false,
        "rtl_output_sha256": "4f81904a9b06c58572a0e5769b3b4ffb99e7bd4be88ee8c2b64a804f483d9dc6",
        "status": "not_run",
        "testbench_sha256": "86443e241e463282b272875abb0f1eb8c72c027641c2053f9d6880aecc8149c3"
      },
      "sim_pass": false,
      "sources": [
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/board_source_identity.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/compile.log",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_executed_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/boundary_trace.jsonl",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/adaptive_semantic_stall.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json"
      ],
      "status": "needs_repair",
      "summary": "vcs_compile_failure: Error-[XMRE] Cross-module reference resolution error"
    },
    "case_vcs_functional_applicability": {
      "applicable_rerun_gates": [
        "case_vcs_evidence_analyzer",
        "case_vcs_functional_sim"
      ],
      "current_failed_gates": [
        "functional_sim"
      ],
      "current_layer": "board_axi_ddr_wrapped_system",
      "executable": true,
      "origin_gates": [
        "case_vcs_functional_sim"
      ],
      "origin_layer": "board_axi_ddr_wrapped_system",
      "reason": "diagnosis is bound to the current source artifact, hierarchy layer, and failed gate",
      "relation": "current_board_functional_aggregate",
      "schema_version": "spatialaccagent.diagnosis_applicability_report.v1",
      "status": "applicable",
      "target_layer": "board_axi_ddr_wrapped_system",
      "validation_errors": []
    },
    "completed_lower_layer_capabilities": [
      {
        "capability_id": "connected_kernel_cctg_contradiction_targeted_replay",
        "cctg_boundary_replay": {
          "accepted_trace_record_count": 416,
          "boundary_liveness_status": "pass",
          "fresh_remote_vcs_execution_observed": true,
          "status": "pass"
        },
        "context_package": {
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_step_00_current_layer_causal_repair_context_package.json",
          "sha256": "da18894b3b2f02f0af7de57c05072b5d69d4e9fe90eff2bc36d8ceca98c87adc"
        },
        "direct_lifecycle": {
          "egress_accepted_count": 1792,
          "egress_complete": true,
          "expected_ingress_beats": 1792,
          "ingress_complete": true,
          "start_witness": {
            "record": {
              "accepted": 1,
              "beat": 0,
              "cycle": 7681068,
              "fire": 1,
              "kind": "core_ingress",
              "last": 0,
              "ready": 1,
              "st": 1,
              "token": 0,
              "valid": 1
            },
            "source": "first_accepted_core_ingress"
          },
          "terminal_egress_last": true
        },
        "planning_policy": "This completed lower-layer experiment is closed evidence. Do not request or rerun the same connected-kernel replay unless a new current trace explicitly contradicts a named certified invariant; choose only the next causally distinct board AXI/DDR action.",
        "schema_version": "spatialaccagent.rematerialized_lower_layer_capability_evidence.v1",
        "source_debug_layer": "single_transformer_layer_kernel",
        "source_verification_scope": "single_transformer_layer_kernel",
        "status": "pass"
      }
    ],
    "contract_guided_debug_closure": {
      "causal_path": {
        "boundary_order": [
          "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
          "boundary.edge_data_block_input_to_stage_02_residual_add_1_residual_skip",
          "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
          "boundary.edge_data_stage_01_self_attention_to_stage_02_residual_add_1_main",
          "boundary.edge_data_stage_02_residual_add_1_to_stage_03_rms_norm_2_main",
          "boundary.edge_data_stage_02_residual_add_1_to_stage_08_residual_add_2_residual_skip",
          "boundary.edge_data_stage_03_rms_norm_2_to_stage_04_mlp_gate_proj_mlp_gate_branch",
          "boundary.edge_data_stage_03_rms_norm_2_to_stage_05_mlp_up_proj_mlp_up_branch",
          "boundary.edge_data_stage_04_mlp_gate_proj_to_stage_06_activation_mul_mlp_gate_to_mul",
          "boundary.edge_data_stage_05_mlp_up_proj_to_stage_06_activation_mul_mlp_up_to_mul",
          "boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main",
          "boundary.edge_data_stage_07_mlp_down_proj_to_stage_08_residual_add_2_main",
          "boundary.edge_data_stage_08_residual_add_2_to_block_output_output"
        ],
        "path_id": "default_pipeline_path",
        "stages": [
          "block_input",
          "stage_00_rms_norm_1",
          "stage_01_self_attention",
          "stage_02_residual_add_1",
          "stage_03_rms_norm_2",
          "stage_04_mlp_gate_proj",
          "stage_05_mlp_up_proj",
          "stage_06_activation_mul",
          "stage_07_mlp_down_proj",
          "stage_08_residual_add_2",
          "block_output"
        ]
      },
      "current_layer_failure_context": {},
      "failed_boundaries": [
        {
          "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
          "contract": "kernel_start_precedes_stage0_input",
          "cycle": 20572946,
          "equivalent_failure_count": 1,
          "evidence_kind": "boundary_trace",
          "expected_value": {
            "kernel_start_to_core": "1",
            "stage0_input_requires_started_lifecycle": true
          },
          "logical_index": 0,
          "observed_value": {
            "core_egress_accepted_count": 0,
            "core_ingress_accepted_count_before_fire": 0,
            "kernel_reset": 0,
            "kernel_start_to_core": 0,
            "observational_only": true,
            "observed_start_pulse_count_before_fire": 0,
            "probe_id": "probe.connected_kernel_stage0_prestart_start_level.18",
            "probe_revision": 18,
            "source_marker": "connected_kernel_stage0_prestart_start_level_r18",
            "stage0_input_accepted_count_before_fire": 0,
            "stage0_input_fire": 1,
            "stage0_input_ready": 1,
            "stage0_input_valid": 1
          },
          "schema_version": "spatialaccagent.boundary_trace.v1",
          "status": "fail",
          "tile_id": -1,
          "tx_id": 0
        },
        {
          "boundary_id": "connected_kernel_input_to_output",
          "contract": "kernel_start_precedes_direct_core_ingress",
          "cycle": 20572946,
          "equivalent_failure_count": 2,
          "evidence_kind": "boundary_trace",
          "expected_value": {
            "first_core_ingress_requires_started_lifecycle": true,
            "kernel_start_to_core": "1"
          },
          "logical_index": 0,
          "observed_value": {
            "core_egress_accepted_count": 0,
            "core_ingress_accepted_count_before_fire": 0,
            "core_ingress_fire": 1,
            "core_ingress_ready": 1,
            "core_ingress_valid": 1,
            "kernel_reset": 0,
            "kernel_start_q": 0,
            "kernel_start_to_core": 0,
            "observational_only": true,
            "probe_id": "probe.connected_kernel_first_direct_ingress_start_level.17",
            "probe_revision": 17,
            "source_marker": "connected_kernel_first_direct_ingress_start_level_r17"
          },
          "schema_version": "spatialaccagent.boundary_trace.v1",
          "status": "fail",
          "tile_id": -1,
          "tx_id": 0
        },
        {
          "boundary_id": "connected_kernel_input_to_output",
          "contract": "connected_kernel_input_to_output",
          "cycle": 20805738,
          "equivalent_failure_count": 3,
          "evidence_kind": "boundary_trace",
          "expected_value": {
            "availability": "direct_core_boundary_liveness",
            "required_input_accepted_count": 1792,
            "required_output_accepted_count": 1792
          },
          "logical_index": 1792,
          "observed_value": {
            "core_egress_accepted_count": 0,
            "core_egress_ready": 1,
            "core_egress_valid": 0,
            "core_ingress_accepted_count": 1792,
            "core_ingress_ready": 0,
            "core_ingress_valid": 0,
            "outer_ingress_accepted_count": 1792,
            "output_accept_count": 0,
            "probe_id": "probe.connected_kernel_direct_frontier_contradiction.13",
            "probe_revision": 13,
            "source_marker": "connected_kernel_direct_frontier_contradiction_r13",
            "stage0_accepted_count": 1680
          },
          "schema_version": "spatialaccagent.boundary_trace.v1",
          "status": "fail",
          "tile_id": -1,
          "tx_id": 1792
        }
      ],
      "failing_transaction": {
        "beat_index": null,
        "expected_value": {
          "first_core_ingress_requires_started_lifecycle": true,
          "kernel_start_to_core": "1"
        },
        "input_fingerprint_sha256": null,
        "lane_index": null,
        "logical_index": 0,
        "module": null,
        "observed_value": {
          "core_egress_accepted_count": 0,
          "core_ingress_accepted_count_before_fire": 0,
          "core_ingress_fire": 1,
          "core_ingress_ready": 1,
          "core_ingress_valid": 1,
          "kernel_reset": 0,
          "kernel_start_q": 0,
          "kernel_start_to_core": 0,
          "observational_only": true,
          "probe_id": "probe.connected_kernel_first_direct_ingress_start_level.17",
          "probe_revision": 17,
          "source_marker": "connected_kernel_first_direct_ingress_start_level_r17"
        },
        "rtl_output_sha256": null,
        "source": "boundary_trace",
        "stage_id": null,
        "tile_id": -1,
        "tx_id": 0,
        "word_index": null
      },
      "failure_record_count": 6,
      "failure_signature": {
        "boundary": "block_input->stage_00_rms_norm_1",
        "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
        "expected_value": {
          "kernel_start_to_core": "1",
          "stage0_input_requires_started_lifecycle": true
        },
        "integration_summary": null,
        "observed_value": {
          "core_egress_accepted_count": 0,
          "core_ingress_accepted_count_before_fire": 0,
          "kernel_reset": 0,
          "kernel_start_to_core": 0,
          "observational_only": true,
          "observed_start_pulse_count_before_fire": 0,
          "probe_id": "probe.connected_kernel_stage0_prestart_start_level.18",
          "probe_revision": 18,
          "source_marker": "connected_kernel_stage0_prestart_start_level_r18",
          "stage0_input_accepted_count_before_fire": 0,
          "stage0_input_fire": 1,
          "stage0_input_ready": 1,
          "stage0_input_valid": 1
        },
        "status": "fail",
        "summary": null
      },
      "lower_layer_evidence_challenge": {
        "lower_layer_pass_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence",
          "single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_single_layer_semantic_evidence"
        ],
        "reason": "localized trace does not explicitly contradict lower-layer pass evidence",
        "status": "no_lower_layer_challenge"
      },
      "minimal_repair_context": {
        "boundary_contract": {
          "boundary": "block_input->stage_00_rms_norm_1",
          "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
          "debug_policy": {
            "check_only_boundary_transactions": true,
            "trace_only_failing_transaction_by_default": true
          },
          "dst_stage": "stage_00_rms_norm_1",
          "edge_id": "edge_data_block_input_to_stage_00_rms_norm_1_input",
          "expected_invariants": [
            "transaction_id_preserved",
            "valid_ready_order_preserved",
            "tile_id_preserved_when_present",
            "logical_index_mapping_matches_stage_contract",
            "output_valid_within_declared_latency_window",
            "numeric_policy_matches_stage_binding",
            "memory_address_range_matches_runtime_layout_when_present"
          ],
          "src_stage": "block_input",
          "trace_fields": [
            "cycle",
            "boundary_id",
            "tx_id",
            "tile_id",
            "logical_index",
            "observed_value",
            "expected_value",
            "contract",
            "status"
          ]
        },
        "current_layer_failure_context": {},
        "lower_layer_evidence_challenge": {
          "lower_layer_pass_evidence": [
            "case_real_weight_artifacts",
            "case_target_model_reference",
            "case_semantic_testbench",
            "case_stage_leaf_static",
            "boundary_contract_check",
            "case_leaf_functional",
            "case_leaf_golden_compare",
            "case_operator_leaf_semantic_evidence",
            "single_transformer_layer",
            "case_single_layer_functional",
            "case_single_layer_golden_compare",
            "case_single_layer_semantic_evidence"
          ],
          "reason": "localized trace does not explicitly contradict lower-layer pass evidence",
          "status": "no_lower_layer_challenge"
        },
        "repair_scope": "causal_slice",
        "root_candidate_module": "block_input",
        "trace_record": {
          "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
          "contract": "kernel_start_precedes_stage0_input",
          "cycle": 20572946,
          "evidence_kind": "boundary_trace",
          "expected_value": {
            "kernel_start_to_core": "1",
            "stage0_input_requires_started_lifecycle": true
          },
          "logical_index": 0,
          "observed_value": {
            "core_egress_accepted_count": 0,
            "core_ingress_accepted_count_before_fire": 0,
            "kernel_reset": 0,
            "kernel_start_to_core": 0,
            "observational_only": true,
            "observed_start_pulse_count_before_fire": 0,
            "probe_id": "probe.connected_kernel_stage0_prestart_start_level.18",
            "probe_revision": 18,
            "source_marker": "connected_kernel_stage0_prestart_start_level_r18",
            "stage0_input_accepted_count_before_fire": 0,
            "stage0_input_fire": 1,
            "stage0_input_ready": 1,
            "stage0_input_valid": 1
          },
          "schema_version": "spatialaccagent.boundary_trace.v1",
          "status": "fail",
          "tile_id": -1,
          "tx_id": 0
        },
        "violated_contract": "kernel_start_precedes_stage0_input"
      },
      "policy": {
        "do_not_patch_output_module_only_because_symptom_is_downstream": true,
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
        "if_status_needs_boundary_trace_rerun_stage7_with_boundary_monitors": true,
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "repair_agent_should_use_causal_slice_only": true,
        "verification_capability_gap_must_be_repaired_before_hardware_trace": true
      },
      "recommended_trace_gate": null,
      "representative_failure_count": 3,
      "root_candidate_module": "block_input",
      "schema_version": "spatialaccagent.debug_closure.v0",
      "status": "localized",
      "strategy": "contract_guided_boundary_failure_slice",
      "targeted_replay_plan": {
        "acceptance": {
          "checkpoint_replay_is_screening_only": true,
          "earliest_failed_boundary_identified": true,
          "failed_stage_identified": false,
          "full_cold_exact_board_vcs_required_before_stage_pass": true,
          "repair_context_must_reference_boundary_contract": true
        },
        "failed_boundary_index": 0,
        "probe_sequence": [
          {
            "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
            "method": "golden_boundary_compare_or_injection",
            "probe_id": "targeted_replay.boundary_00",
            "purpose": "bisect failing transaction path before applying RTL repair"
          }
        ],
        "rerun_env": {
          "SPATIALACC_BOUNDARY_TRACE": "1",
          "SPATIALACC_CHECKPOINT_REPLAY": "1",
          "SPATIALACC_TARGETED_REPLAY": "1",
          "SPATIALACC_TARGET_BOUNDARY": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input"
        },
        "schema_version": "spatialaccagent.targeted_replay_plan.v1",
        "simulation_checkpoint_replay": {
          "capture_scope": [
            "complete_simulator_state",
            "testbench_external_state",
            "axi_ddr_transaction_state"
          ],
          "cut_selection": "latest_committed_semantic_event_before_active_cctg_frontier",
          "max_heavy_jobs": 1,
          "persistent_content_addressed_storage": true,
          "reuse_modes": [
            "native_exact_model",
            "portable_cross_revision_with_schema_causal_cut_and_equivalence_certificates"
          ],
          "status": "requested",
          "unsafe_reuse_action": "cold_capture"
        },
        "status": "ready",
        "strategy": "boundary_level_binary_search_then_earliest_violation"
      },
      "violated_contract": "kernel_start_precedes_stage0_input"
    },
    "hierarchical_repair_loop": {
      "agent_runtime_llm_blocker": false,
      "current_layer": {
        "id": "board_axi_ddr_wrapped_system",
        "missing_or_failed": [
          "case_multilayer_functional=not_run",
          "case_pipeline_deadlock_check=not_run",
          "case_axi_protocol_check=not_run",
          "case_ddr_image_roundtrip=not_run",
          "functional_sim=fail",
          "case_board_semantic_evidence=not_run"
        ],
        "order": 2,
        "promotion_target": "backend_bitstream_and_board_runtime",
        "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
        "repair_loop": "board_wrapper_tool_run__cctg_axi_ddr_slice__bounded_wrapper_or_runtime_repair__rerun",
        "required_gates": [
          {
            "name": "case_board_interface_discovery",
            "status": "pass"
          },
          {
            "name": "case_multilayer_pipeline",
            "status": "pass"
          },
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
            "status": "pass"
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
        "status": "needs_repair"
      },
      "debug_loop_contract": {
        "anti_spin_policy": {
          "current_layer_failure_after_lower_pass_means": "debug current-layer integration, interconnect, wrapper, scheduler, data order, or boundary contract first",
          "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace": true,
          "lower_layer_pass_evidence_is_reusable_not_absolute": true,
          "passed_lower_layer_can_be_challenged_by_current_layer_trace": true,
          "reopening_lower_layer_requires": [
            "a current-layer boundary trace record that directly contradicts lower-layer pass evidence",
            "or a SACG-approved design-contract change invalidating the previous lower-layer evidence"
          ],
          "when_reopened": [
            "record the contradicted lower-layer gate/module and source trace in SACG",
            "rerun only the challenged lower-layer scope with expanded boundary stimuli or corrected contract",
            "after lower-layer revalidation, rerun the failed current layer before any higher-layer promotion"
          ]
        },
        "cctg_policy": {
          "first_action_when_trace_missing": "debug_trace_rerun for the failed current-layer gate",
          "localized_action": "causal_slice_repair over the localized boundary or current-layer integration slice",
          "purpose": "speed root-cause localization by mapping real-tool symptoms to the earliest violated contract/boundary",
          "required_on_failure": true,
          "trace_schema_is_case_adapter_driven": true
        },
        "layer_order": [
          "operator_leaf_modules",
          "single_transformer_layer_kernel",
          "board_axi_ddr_wrapped_system"
        ],
        "layers": [
          {
            "entry_condition": "Stage6 verification gate DAG and real case-adapter tools are available",
            "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
            "failure_loop": [
              "run current-layer real tool",
              "collect CCTG boundary trace or failure localization evidence",
              "classify earliest violated boundary/current-layer contract",
              "apply only bounded repair permitted by SACG/human-boundary rules",
              "rerun the same current layer until pass before promotion"
            ],
            "id": "operator_leaf_modules",
            "order": 0,
            "promotion_target": "single_transformer_layer_kernel",
            "purpose": "Debug every spatially parallel operator module before integration.",
            "required_gates": [
              "case_real_weight_artifacts",
              "case_target_model_reference",
              "case_semantic_testbench",
              "case_stage_leaf_static",
              "boundary_contract_check",
              "case_leaf_functional",
              "case_leaf_golden_compare",
              "case_operator_leaf_semantic_evidence"
            ]
          },
          {
            "entry_condition": "all lower debug layers have pass evidence",
            "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
            "failure_loop": [
              "run current-layer real tool",
              "collect CCTG boundary trace or failure localization evidence",
              "classify earliest violated boundary/current-layer contract",
              "apply only bounded repair permitted by SACG/human-boundary rules",
              "rerun the same current layer until pass before promotion"
            ],
            "id": "single_transformer_layer_kernel",
            "order": 1,
            "promotion_target": "board_axi_ddr_wrapped_system",
            "purpose": "Debug the connected one-layer transformer spatial kernel after leaf modules pass.",
            "required_gates": [
              "single_transformer_layer",
              "case_single_layer_functional",
              "case_single_layer_golden_compare",
              "case_single_layer_semantic_evidence"
            ]
          },
          {
            "entry_condition": "all lower debug layers have pass evidence",
            "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
            "failure_loop": [
              "run current-layer real tool",
              "collect CCTG boundary trace or failure localization evidence",
              "classify earliest violated boundary/current-layer contract",
              "apply only bounded repair permitted by SACG/human-boundary rules",
              "rerun the same current layer until pass before promotion"
            ],
            "id": "board_axi_ddr_wrapped_system",
            "order": 2,
            "promotion_target": "backend_bitstream_and_board_runtime",
            "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
            "required_gates": [
              "case_board_interface_discovery",
              "case_multilayer_pipeline",
              "case_multilayer_functional",
              "case_pipeline_deadlock_check",
              "case_axi_ddr_interface",
              "case_axi_protocol_check",
              "case_ddr_image_roundtrip",
              "functional_sim",
              "case_board_semantic_evidence"
            ]
          }
        ],
        "promotion_policy": {
          "backend_or_board_runtime_requires_all_three_debug_layers_to_pass": true,
          "dependency_skipped_or_smoke_evidence_cannot_promote": true,
          "next_layer_requires_current_layer_certificate": true
        },
        "schema_version": "spatialaccagent.hierarchical_debug_loop_contract.v0"
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
      "failure_kind": "board_wrapper_or_pipeline_integration",
      "layers": [
        {
          "id": "operator_leaf_modules",
          "missing_or_failed": [],
          "order": 0,
          "promotion_target": "single_transformer_layer_kernel",
          "purpose": "Debug every spatially parallel operator module before integration.",
          "repair_loop": "module_tool_run__cctg_localize__bounded_module_or_checker_repair__rerun",
          "required_gates": [
            {
              "name": "case_real_weight_artifacts",
              "status": "pass"
            },
            {
              "name": "case_target_model_reference",
              "status": "pass"
            },
            {
              "name": "case_semantic_testbench",
              "status": "pass"
            },
            {
              "name": "case_stage_leaf_static",
              "status": "pass"
            },
            {
              "name": "boundary_contract_check",
              "status": "pass"
            },
            {
              "name": "case_leaf_functional",
              "status": "pass"
            },
            {
              "name": "case_leaf_golden_compare",
              "status": "pass"
            },
            {
              "name": "case_operator_leaf_semantic_evidence",
              "status": "pass"
            }
          ],
          "status": "pass"
        },
        {
          "id": "single_transformer_layer_kernel",
          "missing_or_failed": [],
          "order": 1,
          "promotion_target": "board_axi_ddr_wrapped_system",
          "purpose": "Debug the connected one-layer transformer spatial kernel after leaf modules pass.",
          "repair_loop": "layer_tool_run__cctg_failure_slice__bounded_interconnect_or_module_repair__rerun",
          "required_gates": [
            {
              "name": "single_transformer_layer",
              "status": "pass"
            },
            {
              "name": "case_single_layer_functional",
              "status": "pass"
            },
            {
              "name": "case_single_layer_golden_compare",
              "status": "pass"
            },
            {
              "name": "case_single_layer_semantic_evidence",
              "status": "pass"
            }
          ],
          "status": "pass"
        },
        {
          "id": "board_axi_ddr_wrapped_system",
          "missing_or_failed": [
            "case_multilayer_functional=not_run",
            "case_pipeline_deadlock_check=not_run",
            "case_axi_protocol_check=not_run",
            "case_ddr_image_roundtrip=not_run",
            "functional_sim=fail",
            "case_board_semantic_evidence=not_run"
          ],
          "order": 2,
          "promotion_target": "backend_bitstream_and_board_runtime",
          "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
          "repair_loop": "board_wrapper_tool_run__cctg_axi_ddr_slice__bounded_wrapper_or_runtime_repair__rerun",
          "required_gates": [
            {
              "name": "case_board_interface_discovery",
              "status": "pass"
            },
            {
              "name": "case_multilayer_pipeline",
              "status": "pass"
            },
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
              "status": "pass"
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
          "status": "needs_repair"
        }
      ],
      "lower_layer_evidence_challenge": {
        "lower_layer_pass_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence",
          "single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_single_layer_semantic_evidence"
        ],
        "reason": "challenge object is present but does not assert a contradiction",
        "status": "no_lower_layer_challenge"
      },
      "lower_layer_pass_evidence": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_stage_leaf_static",
        "boundary_contract_check",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence",
        "single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "case_single_layer_semantic_evidence"
      ],
      "out_of_order_executed_higher_layer_gates": [],
      "policy": {
        "cctg_required_for_root_cause_localization": true,
        "current_layer_failure_after_lower_pass_means_integration_boundary_debug": true,
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
        "failed_layer_must_repair_before_next_layer": true,
        "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "no_stage_promotion_from_smoke_or_dependency_skipped_evidence": true,
        "three_layer_debug_order_is_mandatory": true,
        "tool_output_then_llm_analysis_then_bounded_patch_then_rerun": true
      },
      "root_candidate_module": "block_input",
      "schema_version": "spatialaccagent.hierarchical_repair_loop.v0",
      "status": "needs_repair",
      "violated_contract": "kernel_start_precedes_stage0_input"
    },
    "prior_repair_execution_feedback": {
      "blockers": [
        "The VCS report gives the XMRE error class but omits the failing source path, line, unresolved internal name, declaration context, and compile order.",
        "The compiled declarations below dut.spatialacc_single_kernel.core are not supplied as complete source bodies, so actual valid, ready, fire, received-count, and data expressions for the twelve incomplete boundaries cannot be proved from the editable testbench alone.",
        "Simulation did not run, so no current internal data-boundary transfer supports a functional source repair."
      ],
      "deterministic_feedback": [],
      "execution_errors": [],
      "input_fingerprint_sha256": "b4e16e16a5e1db8a297eabeb68370889be06b812c2445e2ea04d56b56f56d94f",
      "llm_records": [
        {
          "agent": "exact_board_integration_generation_agent",
          "blockers": [
            "The VCS report gives the XMRE error class but omits the failing source path, line, unresolved internal name, declaration context, and compile order.",
            "The compiled declarations below dut.spatialacc_single_kernel.core are not supplied as complete source bodies, so actual valid, ready, fire, received-count, and data expressions for the twelve incomplete boundaries cannot be proved from the editable testbench alone.",
            "Simulation did not run, so no current internal data-boundary transfer supports a functional source repair."
          ],
          "deterministic_feedback": [],
          "input_fingerprint_sha256": "6bcc792c4b4a332a34f35bd86d08a0cb67ca63404f74d13b7e91357142fee3c4",
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/llm/exact_board_integration_generation_agent_result.json",
          "repair_execution_context": {
            "debug_layer": "board_axi_ddr_wrapped_system",
            "repair_scope": "verification_capability_repair",
            "repair_step_id": "repair_step.00",
            "schema_version": "spatialaccagent.repair_execution_agent_context.v1",
            "verification_scope": "board_axi_ddr_closure"
          },
          "required_capabilities": [
            {
              "capability_id": "vcs_compile_diagnostic_source_provenance",
              "debug_layer": "board_axi_ddr_wrapped_system",
              "producer_scope": "real_board_vcs_compile_provenance",
              "rationale": "Read the preserved exact-source compile artifacts without rerunning VCS. Identify the first unresolved internal reference and the declaration that should bind it, so the next response can use one exact, smallest testbench replacement and can bind every required data-boundary observation without guessing.",
              "required_evidence": [
                "The first complete XMRE diagnostic with source path, line, column, and unresolved reference name",
                "Unique surrounding source text for the failing reference",
                "The matching compiled module declaration and instance path, including the actual valid, ready, and data names when the failure is in a boundary probe",
                "The exact VCS command, source order, include paths, defines, and source fingerprint used by the failed compile"
              ],
              "target_modules": [
                "spatialacc_exact_board_multilayer_tb",
                "app_shell_9p_cnn_core_0_1",
                "SingleLayerSemanticHarness",
                "LlamaStyleBlock"
              ]
            }
          ],
          "scope": "verification_capability_repair",
          "sha256": "0a509abc9a35f9edda35cada3bc3bac34afc163a7ad50b92bdd7f23a3c28eca9",
          "stage": "repair_execution",
          "status": "blocked",
          "step_id": "repair_step.00",
          "summary": "Blocked before source repair: exact-board preflight passed, but VCS compile returned 1 on an unresolved internal reference and simulation was not run. No file is changed because the failing path, line, signal name, declaration context, and compile order are missing. Retrieve those facts from the preserved compile artifacts before making a bounded testbench-only repair."
        }
      ],
      "repair_execution_status": "incomplete",
      "report": {
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_execution_report.json",
        "schema_version": "spatialaccagent.repair_execution_report.v0",
        "sha256": "d6a1b319e8a8bba3d39a283e8387a68c512fb2b0c7431e2359b5ed30491fdbc1"
      },
      "required_capabilities": [
        {
          "capability_id": "vcs_compile_diagnostic_source_provenance",
          "debug_layer": "board_axi_ddr_wrapped_system",
          "producer_scope": "real_board_vcs_compile_provenance",
          "rationale": "Read the preserved exact-source compile artifacts without rerunning VCS. Identify the first unresolved internal reference and the declaration that should bind it, so the next response can use one exact, smallest testbench replacement and can bind every required data-boundary observation without guessing.",
          "required_evidence": [
            "The first complete XMRE diagnostic with source path, line, column, and unresolved reference name",
            "Unique surrounding source text for the failing reference",
            "The matching compiled module declaration and instance path, including the actual valid, ready, and data names when the failure is in a boundary probe",
            "The exact VCS command, source order, include paths, defines, and source fingerprint used by the failed compile"
          ],
          "target_modules": [
            "spatialacc_exact_board_multilayer_tb",
            "app_shell_9p_cnn_core_0_1",
            "SingleLayerSemanticHarness",
            "LlamaStyleBlock"
          ]
        }
      ],
      "schema_version": "spatialaccagent.prior_repair_execution_feedback.v1",
      "scope_selection": {
        "excluded_unbound_or_other_layer_record_count": 0,
        "policy": "Only prior Stage8 LLM records with an explicit matching debug layer are reusable. Historical unbound or other-layer records remain on disk but are not repair-planning evidence.",
        "required_debug_layer": "board_axi_ddr_wrapped_system",
        "selected_record_count": 1
      },
      "status": "blocked",
      "summary": "Blocked before source repair: exact-board preflight passed, but VCS compile returned 1 on an unresolved internal reference and simulation was not run. No file is changed because the failing path, line, signal name, declaration context, and compile order are missing. Retrieve those facts from the preserved compile artifacts before making a bounded testbench-only repair.",
      "validation": {
        "errors": [],
        "status": "pass"
      }
    }
  },
  "failures": [
    {
      "acceptance_role": "functional_sim_candidate",
      "checker": "real_tool.case_vcs_functional_sim",
      "command": "python3 scripts/verification/case_board_vcs_functional.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
      "execution_fingerprint_sha256": "d0c3c662891d4d7b41809760e15ee23b9fd6487ee46789b1ec16471c6029f59c",
      "failure_class": "runtime_harness",
      "kind": "vcs_real_functional_sim",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_vcs_functional_sim.json",
      "produced_reports": [
        {
          "blockers": [],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
          "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
          "status": "fail",
          "summary": null
        },
        {
          "blockers": [],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
          "schema_version": "spatialaccagent.normalized_boundary_trace.v1",
          "status": "ready",
          "summary": null
        }
      ],
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "required": true,
      "required_group": "functional_sim",
      "reused_existing_result": false,
      "status": "fail",
      "summary": "returncode=1",
      "tool_report_blockers": [],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
      "tool_report_status": "fail",
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_deadlock_axi_check",
      "command": "python3 scripts/verification/case_deadlock_axi_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/deadlock_axi_check.json --rtl-wrapper /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/sample_project_sources/wrapper.v --testbench /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/board_integration/spatialacc_exact_board_multilayer_tb.sv",
      "execution_fingerprint_sha256": "6f26642a6481eaf76bcd319ab145f80ceceacf891d15e91e3a6bf89035c7f4f0",
      "failure_class": "runtime_harness",
      "kind": "case_deadlock_axi_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_deadlock_axi_check.json",
      "produced_reports": [
        {
          "blockers": [
            "case_vcs_functional_sim did not pass",
            "real DDR functional pass line is missing",
            "VCS diagnosis is not a clean functional pass",
            "real DDR input/weight/output counters are not all positive",
            "output beats are smaller than runtime shape expectation: expected 1792",
            "RTL/TB AXI interface missing token io_m_axi_arvalid",
            "RTL/TB AXI interface missing token io_m_axi_arready",
            "RTL/TB AXI interface missing token io_m_axi_rvalid",
            "RTL/TB AXI interface missing token io_m_axi_rready",
            "RTL/TB AXI interface missing token io_m_axi_awvalid",
            "RTL/TB AXI interface missing token io_m_axi_awready",
            "RTL/TB AXI interface missing token io_m_axi_wvalid",
            "RTL/TB AXI interface missing token io_m_axi_wready",
            "RTL/TB AXI interface missing token io_m_axi_bvalid",
            "RTL/TB AXI interface missing token io_m_axi_bready",
            "RTL/TB AXI interface missing token io_input_base_addr",
            "RTL/TB AXI interface missing token io_weight_base_addr",
            "RTL/TB AXI interface missing token io_output_base_addr",
            "testbench missing token INPUT_MEMH",
            "testbench missing token WEIGHT_MEMH",
            "testbench missing token NO_PROGRESS",
            "testbench missing token TIMEOUT",
            "testbench missing token PASS real functional ddr path"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/deadlock_axi_check.json",
          "schema_version": "spatialaccagent.case_deadlock_axi_check.v0",
          "status": "fail",
          "summary": "23 blocker(s)"
        }
      ],
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "fail",
      "summary": "returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
      "tool_report_blockers": [
        "case_vcs_functional_sim did not pass",
        "real DDR functional pass line is missing",
        "VCS diagnosis is not a clean functional pass",
        "real DDR input/weight/output counters are not all positive",
        "output beats are smaller than runtime shape expectation: expected 1792",
        "RTL/TB AXI interface missing token io_m_axi_arvalid",
        "RTL/TB AXI interface missing token io_m_axi_arready",
        "RTL/TB AXI interface missing token io_m_axi_rvalid",
        "RTL/TB AXI interface missing token io_m_axi_rready",
        "RTL/TB AXI interface missing token io_m_axi_awvalid",
        "RTL/TB AXI interface missing token io_m_axi_awready",
        "RTL/TB AXI interface missing token io_m_axi_wvalid",
        "RTL/TB AXI interface missing token io_m_axi_wready",
        "RTL/TB AXI interface missing token io_m_axi_bvalid",
        "RTL/TB AXI interface missing token io_m_axi_bready",
        "RTL/TB AXI interface missing token io_input_base_addr",
        "RTL/TB AXI interface missing token io_weight_base_addr",
        "RTL/TB AXI interface missing token io_output_base_addr",
        "testbench missing token INPUT_MEMH",
        "testbench missing token WEIGHT_MEMH",
        "testbench missing token NO_PROGRESS",
        "testbench missing token TIMEOUT",
        "testbench missing token PASS real functional ddr path"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/deadlock_axi_check.json",
      "tool_report_status": "fail",
      "tool_report_summary": "23 blocker(s)"
    },
    {
      "checker": "required_real_tool_evidence_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']"
    },
    {
      "checker": "real_weight_semantic_evidence_check",
      "failure_class": "framework_consistency",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
    },
    {
      "checker": "hierarchical_verification_maturity_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
    },
    {
      "checker": "verification_agent_decision_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
    }
  ],
  "note": "Failing checkers are classified; not_run real tools are evidence gaps, not automatic repair failures.",
  "pending_evidence": [
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_multilayer_functional",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate multilayer_functional",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_multilayer_functional",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_multilayer_functional.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_pipeline_deadlock_check",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate pipeline_deadlock",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_pipeline_deadlock_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_pipeline_deadlock_check.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_multilayer_functional']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_axi_protocol_check",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate axi_protocol",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_axi_protocol_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_axi_protocol_check.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_ddr_image_roundtrip",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate ddr_image_roundtrip",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_ddr_image_roundtrip",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_ddr_image_roundtrip.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_axi_protocol_check']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_board_semantic_evidence",
      "command": "python3 scripts/verification/semantic_evidence_assembler.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --level axi_ddr_functional --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "semantic_evidence_assemble",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_board_semantic_evidence.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_multilayer_functional', 'case_pipeline_deadlock_check', 'case_axi_protocol_check', 'case_ddr_image_roundtrip']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    }
  ],
  "repair_actions": [
    {
      "approval_required": false,
      "debug_layer": "board_axi_ddr_wrapped_system",
      "reason": "Read the preserved exact-source compile artifacts without rerunning VCS. Identify the first unresolved internal reference and the declaration that should bind it, so the next response can use one exact, smallest testbench replacement and can bind every required data-boundary observation without guessing.",
      "repair_gate": "case_vcs_functional_sim",
      "repair_kind": "vcs_compile_diagnostic_source_provenance",
      "repair_tool_role": "exact_board_vcs_compile_provenance",
      "requested_capability_id": "vcs_compile_diagnostic_source_provenance",
      "requested_producer_scope": "real_board_vcs_compile_provenance",
      "required_evidence": [
        "The first complete XMRE diagnostic with source path, line, column, and unresolved reference name",
        "Unique surrounding source text for the failing reference",
        "The matching compiled module declaration and instance path, including the actual valid, ready, and data names when the failure is in a boundary probe",
        "The exact VCS command, source order, include paths, defines, and source fingerprint used by the failed compile"
      ],
      "scope": "verification_capability_repair",
      "source": "prior_nonfallback_llm_required_capability",
      "source_feedback_fingerprint_sha256": "b4e16e16a5e1db8a297eabeb68370889be06b812c2445e2ea04d56b56f56d94f",
      "target_modules": [
        "spatialacc_exact_board_multilayer_tb",
        "app_shell_9p_cnn_core_0_1",
        "SingleLayerSemanticHarness",
        "LlamaStyleBlock"
      ]
    }
  ],
  "repair_routing_priority": {
    "reason": "no proven current board-to-lower-layer contradiction",
    "schema_version": "spatialaccagent.repair_routing_priority.v1",
    "status": "not_applicable"
  },
  "repair_workflow": {
    "approval_steps": [],
    "blockers": [],
    "case_adapter": {
      "case_id": "qwen2_hf_case",
      "model_family": "qwen2",
      "status": "ready"
    },
    "policy": {
      "cctg_boundary_trace_or_localization_required_before_code_repair": true,
      "do_not_apply_unbounded_code_changes": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace": true,
      "do_not_rerun_smoke_as_acceptance": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "regression_reruns_must_use_case_tool_protocols": true,
      "repair_output_must_return_to_stage7": true,
      "same_debug_layer_must_rerun_until_functionally_correct_before_promotion": true,
      "targeted_lower_layer_backtrack_requires_contradicting_current_layer_trace": true
    },
    "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
    "schema_version": "spatialaccagent.repair_workflow.v0",
    "status": "ready",
    "steps": [
      {
        "action": {
          "approval_required": false,
          "debug_layer": "board_axi_ddr_wrapped_system",
          "reason": "Read the preserved exact-source compile artifacts without rerunning VCS. Identify the first unresolved internal reference and the declaration that should bind it, so the next response can use one exact, smallest testbench replacement and can bind every required data-boundary observation without guessing.",
          "repair_gate": "case_vcs_functional_sim",
          "repair_kind": "vcs_compile_diagnostic_source_provenance",
          "repair_tool_role": "exact_board_vcs_compile_provenance",
          "requested_capability_id": "vcs_compile_diagnostic_source_provenance",
          "requested_producer_scope": "real_board_vcs_compile_provenance",
          "required_evidence": [
            "The first complete XMRE diagnostic with source path, line, column, and unresolved reference name",
            "Unique surrounding source text for the failing reference",
            "The matching compiled module declaration and instance path, including the actual valid, ready, and data names when the failure is in a boundary probe",
            "The exact VCS command, source order, include paths, defines, and source fingerprint used by the failed compile"
          ],
          "scope": "verification_capability_repair",
          "source": "prior_nonfallback_llm_required_capability",
          "source_feedback_fingerprint_sha256": "b4e16e16a5e1db8a297eabeb68370889be06b812c2445e2ea04d56b56f56d94f",
          "target_modules": [
            "spatialacc_exact_board_multilayer_tb",
            "app_shell_9p_cnn_core_0_1",
            "SingleLayerSemanticHarness",
            "LlamaStyleBlock"
          ]
        },
        "approval_required": false,
        "debug_layer": "board_axi_ddr_wrapped_system",
        "id": "repair_step.00",
        "repair_context": {},
        "scope": "verification_capability_repair",
        "source": "prior_nonfallback_llm_required_capability",
        "status": "ready_for_agent_patch",
        "target_modules": [
          "spatialacc_exact_board_multilayer_tb",
          "app_shell_9p_cnn_core_0_1",
          "SingleLayerSemanticHarness",
          "LlamaStyleBlock"
        ]
      }
    ]
  },
  "schema_version": "spatialaccagent.repair_plan.v0",
  "stage": "repair",
  "status": "needs_repair",
  "verification_status": "fail"
}
</candidate_repair_plan>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/sacg_state.json
</source_sacg_state>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "configured_model": "gpt-5.6-sol",
  "endpoint_configured": true,
  "enforce": true,
  "mode": "llm",
  "model": "gpt-5.6-sol",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0354",
      "last_observed_at": "2026-09-09T10:35:54+00:00",
      "observation_count": 2,
      "observed_transition_ids": [
        "transition.2495",
        "transition.2505"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-06T05:44:16+00:00",
      "transition_id": "transition.2495",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0355",
      "last_observed_at": "2026-09-09T17:04:58+00:00",
      "observation_count": 3,
      "observed_transition_ids": [
        "transition.2513",
        "transition.2516",
        "transition.2519"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-09T16:53:03+00:00",
      "transition_id": "transition.2513",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0356",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "observed_transition_ids": [
        "transition.2520",
        "transition.2523",
        "transition.2526",
        "transition.2529"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "status": "active",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "transition_id": "transition.2520",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0357",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "observed_transition_ids": [
        "transition.2520",
        "transition.2523",
        "transition.2526",
        "transition.2529"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "status": "active",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "transition_id": "transition.2520",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0358",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "observed_transition_ids": [
        "transition.2520",
        "transition.2523",
        "transition.2526",
        "transition.2529"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "status": "active",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "transition_id": "transition.2520",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0359",
      "last_observed_at": "2026-09-10T09:29:23+00:00",
      "observation_count": 8,
      "observed_transition_ids": [
        "transition.2521",
        "transition.2524",
        "transition.2527",
        "transition.2530",
        "transition.2547",
        "transition.2552",
        "transition.2555",
        "transition.2557"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-09-09T17:34:25+00:00",
      "transition_id": "transition.2521",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0360",
      "last_observed_at": "2026-09-09T17:55:26+00:00",
      "observation_count": 3,
      "observed_transition_ids": [
        "transition.2522",
        "transition.2525",
        "transition.2528"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-09T17:34:58+00:00",
      "transition_id": "transition.2522",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0361",
      "last_observed_at": "2026-09-10T10:19:51+00:00",
      "observation_count": 27,
      "observed_transition_ids": [
        "transition.2531",
        "transition.2532",
        "transition.2533",
        "transition.2534",
        "transition.2535",
        "transition.2536",
        "transition.2537",
        "transition.2538",
        "transition.2539",
        "transition.2540",
        "transition.2541",
        "transition.2542",
        "transition.2543",
        "transition.2544",
        "transition.2545",
        "transition.2546",
        "transition.2548",
        "transition.2549",
        "transition.2550",
        "transition.2551",
        "transition.2553",
        "transition.2554",
        "transition.2556",
        "transition.2558",
        "transition.2559",
        "transition.2560",
        "transition.2561"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-09-09T18:27:05+00:00",
      "transition_id": "transition.2531",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "debug_layer": "board_axi_ddr_wrapped_system",
  "omitted_unscoped_cross_layer_or_limit_counts": {
    "backtrack_requests": 1,
    "contamination_barriers": 19,
    "failure_lessons": 234,
    "retry_requests": 0,
    "stage_outcomes": 245
  },
  "open_backtrack_requests": [],
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0136",
      "last_observed_at": "2026-09-09T17:04:22+00:00",
      "observation_count": 11,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
        "3013ac2f2886a4bb0e21b0ddcc54c82cffbbdd09e2328421291a438ce8b90e02",
        "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0140",
      "last_observed_at": "2026-09-09T17:04:23+00:00",
      "observation_count": 11,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0141",
      "last_observed_at": "2026-09-01T15:47:55+00:00",
      "observation_count": 3,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
        "efda18fd733bdb42026f8f508143b6cf03763d66ceddd826a75bb87fbd192357",
        "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0142",
      "last_observed_at": "2026-09-01T15:51:29+00:00",
      "observation_count": 6,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "retry_request.0143",
      "last_observed_at": "2026-09-02T13:04:16+00:00",
      "observation_count": 21,
      "observed_source_fingerprint_sha256s": [
        "6f79d3af2a76861b4372a0fd1a6cd00cb5ecc192bca91dd73cdd629da6708b28",
        "c951d2ee708694ff68c2a999b41676974884c1365ffc72998e29f1b5b3182a4b",
        "082a6eeef0e71e2d7e0fd421ae866cfe1993bd5dff7b26db7a530cb05510e5e2",
        "95b72bf31433286e640fa36319cc9596500a6de71ba75f2a68d01f1fc871571c",
        "44f5c7d691ea8d52c42121b934e2c52e18340318d92d12519de5fa6111b21353",
        "56c0cd51d731f4779da7740951e73c43f75c2faa5fa4d8ba39824ce8d9c8e488",
        "1fe929b448ef2f95a69599bb6dd45ee16d60ec4ba02b894f949c57fccbc62e18",
        "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-27T12:56:18+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "retry_request.0144",
      "last_observed_at": "2026-09-09T10:04:51+00:00",
      "observation_count": 43,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-27T12:59:36+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "retry_request.0145",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "retry_request.0146",
      "last_observed_at": "2026-09-10T09:29:23+00:00",
      "observation_count": 8,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-09-09T17:34:25+00:00",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "policy": "Only hierarchy-bound records matching this prompt scope are operational context. Omitted records remain persisted recovery history; sacg_memory_truth separately carries the complete authoritative current blocker set.",
  "recent_failure_lessons": [
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0235",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "stage": "stage7.verification",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative fail-closed Stage7 decision: board_axi_ddr_closure is not promotable. The exact-board identity, multilayer-pipeline preparation, and AXI/DDR-interface preparation gates passed, and certified operator-leaf and connected single-layer evidence remains reusable. However, the required exact-wrapper VCS functional simulation failed (returncode=1); its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, while all dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. The analyzer execution success is diagnostic only because its report is needs_repair, not a functional pass. The block_input / kernel_start_precedes_stage0_input finding is an earliest-boundary localization candidate, not a proven RTL root cause; conflicting source-token findings require hash-bound replay and CCTG reconciliation. No board-level target-model numeric comparison, data-order, output-count, DDR-roundtrip, protocol, liveness, or complete-scope board weight-consumption pass exists. Active same-scope contamination barriers and retry requests remain downstream-consumption and promotion blockers; retry reconciliation is not_ready. Do not run backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime.",
      "timestamp": "2026-09-09T17:54:50+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0236",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative fail-closed Stage7 decision: board_axi_ddr_closure is not promotable. The exact-board identity, multilayer-pipeline preparation, and AXI/DDR-interface preparation gates passed, and certified operator-leaf and connected single-layer evidence remains reusable. However, the required exact-wrapper VCS functional simulation failed (returncode=1); its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, while all dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. The analyzer execution success is diagnostic only because its report is needs_repair, not a functional pass. The block_input / kernel_start_precedes_stage0_input finding is an earliest-boundary localization candidate, not a proven RTL root cause; conflicting source-token findings require hash-bound replay and CCTG reconciliation. No board-level target-model numeric comparison, data-order, output-count, DDR-roundtrip, protocol, liveness, or complete-scope board weight-consumption pass exists. Active same-scope contamination barriers and retry requests remain downstream-consumption and promotion blockers; retry reconciliation is not_ready. Do not run backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime.",
      "timestamp": "2026-09-09T17:54:51+00:00",
      "verification_scope": "board_axi_ddr_closure",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0237",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "stage": "stage7.verification",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages.",
      "timestamp": "2026-09-09T18:18:23+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0238",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages.",
      "timestamp": "2026-09-09T18:23:51+00:00",
      "verification_scope": "board_axi_ddr_closure",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0239",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages.",
      "timestamp": "2026-09-10T00:40:35+00:00",
      "verification_scope": "board_axi_ddr_closure",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0240",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages.",
      "timestamp": "2026-09-10T05:07:49+00:00",
      "verification_scope": "board_axi_ddr_closure",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0241",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages.",
      "timestamp": "2026-09-10T09:10:43+00:00",
      "verification_scope": "board_axi_ddr_closure",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0242",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_vcs_functional_sim: returncode=1; real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages.",
      "timestamp": "2026-09-10T09:29:23+00:00",
      "verification_scope": "board_axi_ddr_closure",
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
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative fail-closed Stage7 decision: board_axi_ddr_closure is not promotable. The exact-board identity, multilayer-pipeline preparation, and AXI/DDR-interface preparation gates passed, and certified operator-leaf and connected single-layer evidence remains reusable. However, the required exact-wrapper VCS functional simulation failed (returncode=1); its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, while all dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. The analyzer execution success is diagnostic only because its report is needs_repair, not a functional pass. The block_input / kernel_start_precedes_stage0_input finding is an earliest-boundary localization candidate, not a proven RTL root cause; conflicting source-token findings require hash-bound replay and CCTG reconciliation. No board-level target-model numeric comparison, data-order, output-count, DDR-roundtrip, protocol, liveness, or complete-scope board weight-consumption pass exists. Active same-scope contamination barriers and retry requests remain downstream-consumption and promotion blockers; retry reconciliation is not_ready. Do not run backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0246",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-09-09T17:54:50+00:00",
      "transition_id": "transition.2526",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative fail-closed Stage7 decision: board_axi_ddr_closure is not promotable. The exact-board identity, multilayer-pipeline preparation, and AXI/DDR-interface preparation gates passed, and certified operator-leaf and connected single-layer evidence remains reusable. However, the required exact-wrapper VCS functional simulation failed (returncode=1); its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, while all dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. The analyzer execution success is diagnostic only because its report is needs_repair, not a functional pass. The block_input / kernel_start_precedes_stage0_input finding is an earliest-boundary localization candidate, not a proven RTL root cause; conflicting source-token findings require hash-bound replay and CCTG reconciliation. No board-level target-model numeric comparison, data-order, output-count, DDR-roundtrip, protocol, liveness, or complete-scope board weight-consumption pass exists. Active same-scope contamination barriers and retry requests remain downstream-consumption and promotion blockers; retry reconciliation is not_ready. Do not run backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0247",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-09T17:54:51+00:00",
      "transition_id": "transition.2527",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0248",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-09-09T18:18:23+00:00",
      "transition_id": "transition.2529",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0249",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-09T18:23:51+00:00",
      "transition_id": "transition.2530",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0250",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-10T00:40:35+00:00",
      "transition_id": "transition.2547",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0251",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-10T05:07:49+00:00",
      "transition_id": "transition.2552",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0252",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-10T09:10:43+00:00",
      "transition_id": "transition.2555",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_vcs_functional_sim: returncode=1",
        "real_tool.case_deadlock_axi_check: returncode=1 report_status=fail report_summary=23 blocker(s) report_status=fail blockers=case_vcs_functional_sim did not pass; real DDR functional pass line is missing; VCS diagnosis is not a clean functional pass; real DDR input/weight/output counters are not all positive",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_deadlock_axi_check=fail, functional_sim: need one real functional pass; smoke/liveness candidates are not acceptance evidence [case_vcs_functional_sim=fail]; dependency_blocked=['case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: fail closed at the board_axi_ddr_wrapped_system layer. The exact-board identity, multilayer-pipeline preparation, AXI/DDR-interface preparation, immutable target-model reference, semantic testbench, complete lower-scope weight evidence, and certified operator-leaf/single-layer closures are reusable prerequisites. They do not establish board correctness. The required exact-board VCS functional simulation failed with returncode=1; its executed analyzer reports that all 16 input tokens completed by cycle 20805737 while zero ready-kernel output beats were accepted. The required deadlock/AXI diagnostic also failed, and dependent multilayer-functional, liveness, AXI-protocol, DDR-roundtrip, and board-semantic gates are not_run. No deterministic board-level target-model numeric, data-order, output-count, DDR-roundtrip, protocol, lifecycle, or complete-scope DUT weight-consumption pass exists. block_input / kernel_start_precedes_stage0_input is a current CCTG localization candidate, not a proven RTL root cause, because source-token diagnostic findings conflict with the passed elaborated interface evidence. The conditional specialist review is consistent with this decision but cannot replace failing real-tool evidence. Do not promote to synthesis, implementation, bitstream, runtime-ABI, or board-runtime stages."
      ],
      "failed_gates": [
        "functional_sim"
      ],
      "id": "stage_outcome.0253",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-10T09:29:23+00:00",
      "transition_id": "transition.2557",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "schema_version": "spatialaccagent.scoped_sacg_memory.v1",
  "source_schema_version": "spatialaccagent.sacg_memory.v0",
  "verification_scope": "board_axi_ddr_closure"
}
</sacg_memory>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 24,
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0329",
      "last_observed_at": "2026-09-09T17:04:22+00:00",
      "observation_count": 11,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
        "3013ac2f2886a4bb0e21b0ddcc54c82cffbbdd09e2328421291a438ce8b90e02",
        "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250",
        "transition.2506",
        "transition.2514",
        "transition.2517"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0330",
      "last_observed_at": "2026-09-09T17:04:22+00:00",
      "observation_count": 11,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
        "3013ac2f2886a4bb0e21b0ddcc54c82cffbbdd09e2328421291a438ce8b90e02",
        "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250",
        "transition.2506",
        "transition.2514",
        "transition.2517"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0331",
      "last_observed_at": "2026-09-09T17:04:22+00:00",
      "observation_count": 11,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
        "3013ac2f2886a4bb0e21b0ddcc54c82cffbbdd09e2328421291a438ce8b90e02",
        "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250",
        "transition.2506",
        "transition.2514",
        "transition.2517"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0341",
      "last_observed_at": "2026-09-09T17:04:23+00:00",
      "observation_count": 11,
      "observed_transition_ids": [
        "transition.0231",
        "transition.0237",
        "transition.0239",
        "transition.0241",
        "transition.0244",
        "transition.0246",
        "transition.0248",
        "transition.0251",
        "transition.2507",
        "transition.2515",
        "transition.2518"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "transition_id": "transition.0231",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0342",
      "last_observed_at": "2026-09-09T15:18:20+00:00",
      "observation_count": 1882,
      "observed_transition_ids": [
        "transition.2095",
        "transition.2096",
        "transition.2097",
        "transition.2098",
        "transition.2099",
        "transition.2100",
        "transition.2101",
        "transition.2102",
        "transition.2103",
        "transition.2104",
        "transition.2105",
        "transition.2106",
        "transition.2107",
        "transition.2108",
        "transition.2109",
        "transition.2110",
        "transition.2111",
        "transition.2112",
        "transition.2113",
        "transition.2114",
        "transition.2115",
        "transition.2116",
        "transition.2117",
        "transition.2118",
        "transition.2119",
        "transition.2120",
        "transition.2121",
        "transition.2508",
        "transition.2509",
        "transition.2510",
        "transition.2511",
        "transition.2512"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-24T08:56:30+00:00",
      "transition_id": "transition.0232",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0343",
      "last_observed_at": "2026-09-01T15:47:55+00:00",
      "observation_count": 3,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
        "efda18fd733bdb42026f8f508143b6cf03763d66ceddd826a75bb87fbd192357",
        "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd"
      ],
      "observed_transition_ids": [
        "transition.0233",
        "transition.2358",
        "transition.2390"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0344",
      "last_observed_at": "2026-09-01T15:47:55+00:00",
      "observation_count": 3,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
        "efda18fd733bdb42026f8f508143b6cf03763d66ceddd826a75bb87fbd192357",
        "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd"
      ],
      "observed_transition_ids": [
        "transition.0233",
        "transition.2358",
        "transition.2390"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0345",
      "last_observed_at": "2026-09-01T15:47:55+00:00",
      "observation_count": 3,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
        "efda18fd733bdb42026f8f508143b6cf03763d66ceddd826a75bb87fbd192357",
        "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd"
      ],
      "observed_transition_ids": [
        "transition.0233",
        "transition.2358",
        "transition.2390"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0346",
      "last_observed_at": "2026-09-01T15:51:29+00:00",
      "observation_count": 6,
      "observed_transition_ids": [
        "transition.0234",
        "transition.2359",
        "transition.2360",
        "transition.2361",
        "transition.2362",
        "transition.2391"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "transition_id": "transition.0234",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0347",
      "last_observed_at": "2026-09-01T14:37:03+00:00",
      "observation_count": 2,
      "observed_transition_ids": [
        "transition.0235",
        "transition.2389"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T17:25:58+00:00",
      "transition_id": "transition.0235",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0348",
      "last_observed_at": "2026-09-02T13:04:16+00:00",
      "observation_count": 21,
      "observed_source_fingerprint_sha256s": [
        "6f79d3af2a76861b4372a0fd1a6cd00cb5ecc192bca91dd73cdd629da6708b28",
        "c951d2ee708694ff68c2a999b41676974884c1365ffc72998e29f1b5b3182a4b",
        "082a6eeef0e71e2d7e0fd421ae866cfe1993bd5dff7b26db7a530cb05510e5e2",
        "95b72bf31433286e640fa36319cc9596500a6de71ba75f2a68d01f1fc871571c",
        "44f5c7d691ea8d52c42121b934e2c52e18340318d92d12519de5fa6111b21353",
        "56c0cd51d731f4779da7740951e73c43f75c2faa5fa4d8ba39824ce8d9c8e488",
        "1fe929b448ef2f95a69599bb6dd45ee16d60ec4ba02b894f949c57fccbc62e18",
        "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8"
      ],
      "observed_transition_ids": [
        "transition.2122",
        "transition.2128",
        "transition.2131",
        "transition.2134",
        "transition.2137",
        "transition.2140",
        "transition.2143",
        "transition.2146",
        "transition.2149",
        "transition.2152",
        "transition.2155",
        "transition.2158",
        "transition.2167",
        "transition.2170",
        "transition.2173",
        "transition.2180",
        "transition.2191",
        "transition.2194",
        "transition.2219",
        "transition.2350",
        "transition.2395"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8",
      "status": "active",
      "timestamp": "2026-07-27T12:56:18+00:00",
      "transition_id": "transition.2122",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0349",
      "last_observed_at": "2026-09-02T13:04:16+00:00",
      "observation_count": 21,
      "observed_source_fingerprint_sha256s": [
        "6f79d3af2a76861b4372a0fd1a6cd00cb5ecc192bca91dd73cdd629da6708b28",
        "c951d2ee708694ff68c2a999b41676974884c1365ffc72998e29f1b5b3182a4b",
        "082a6eeef0e71e2d7e0fd421ae866cfe1993bd5dff7b26db7a530cb05510e5e2",
        "95b72bf31433286e640fa36319cc9596500a6de71ba75f2a68d01f1fc871571c",
        "44f5c7d691ea8d52c42121b934e2c52e18340318d92d12519de5fa6111b21353",
        "56c0cd51d731f4779da7740951e73c43f75c2faa5fa4d8ba39824ce8d9c8e488",
        "1fe929b448ef2f95a69599bb6dd45ee16d60ec4ba02b894f949c57fccbc62e18",
        "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8"
      ],
      "observed_transition_ids": [
        "transition.2122",
        "transition.2128",
        "transition.2131",
        "transition.2134",
        "transition.2137",
        "transition.2140",
        "transition.2143",
        "transition.2146",
        "transition.2149",
        "transition.2152",
        "transition.2155",
        "transition.2158",
        "transition.2167",
        "transition.2170",
        "transition.2173",
        "transition.2180",
        "transition.2191",
        "transition.2194",
        "transition.2219",
        "transition.2350",
        "transition.2395"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8",
      "status": "active",
      "timestamp": "2026-07-27T12:56:18+00:00",
      "transition_id": "transition.2122",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0350",
      "last_observed_at": "2026-09-02T13:04:16+00:00",
      "observation_count": 21,
      "observed_source_fingerprint_sha256s": [
        "6f79d3af2a76861b4372a0fd1a6cd00cb5ecc192bca91dd73cdd629da6708b28",
        "c951d2ee708694ff68c2a999b41676974884c1365ffc72998e29f1b5b3182a4b",
        "082a6eeef0e71e2d7e0fd421ae866cfe1993bd5dff7b26db7a530cb05510e5e2",
        "95b72bf31433286e640fa36319cc9596500a6de71ba75f2a68d01f1fc871571c",
        "44f5c7d691ea8d52c42121b934e2c52e18340318d92d12519de5fa6111b21353",
        "56c0cd51d731f4779da7740951e73c43f75c2faa5fa4d8ba39824ce8d9c8e488",
        "1fe929b448ef2f95a69599bb6dd45ee16d60ec4ba02b894f949c57fccbc62e18",
        "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8"
      ],
      "observed_transition_ids": [
        "transition.2122",
        "transition.2128",
        "transition.2131",
        "transition.2134",
        "transition.2137",
        "transition.2140",
        "transition.2143",
        "transition.2146",
        "transition.2149",
        "transition.2152",
        "transition.2155",
        "transition.2158",
        "transition.2167",
        "transition.2170",
        "transition.2173",
        "transition.2180",
        "transition.2191",
        "transition.2194",
        "transition.2219",
        "transition.2350",
        "transition.2395"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8",
      "status": "active",
      "timestamp": "2026-07-27T12:56:18+00:00",
      "transition_id": "transition.2122",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0351",
      "last_observed_at": "2026-09-09T10:04:51+00:00",
      "observation_count": 43,
      "observed_transition_ids": [
        "transition.2159",
        "transition.2168",
        "transition.2171",
        "transition.2174",
        "transition.2181",
        "transition.2192",
        "transition.2195",
        "transition.2220",
        "transition.2351",
        "transition.2396",
        "transition.2398",
        "transition.2400",
        "transition.2403",
        "transition.2433",
        "transition.2436",
        "transition.2438",
        "transition.2440",
        "transition.2442",
        "transition.2453",
        "transition.2455",
        "transition.2465",
        "transition.2478",
        "transition.2480",
        "transition.2494",
        "transition.2497",
        "transition.2498",
        "transition.2499",
        "transition.2500",
        "transition.2501",
        "transition.2502",
        "transition.2503",
        "transition.2504"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-27T12:59:36+00:00",
      "transition_id": "transition.2123",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0352",
      "last_observed_at": "2026-09-06T15:05:27+00:00",
      "observation_count": 281,
      "observed_transition_ids": [
        "transition.2460",
        "transition.2461",
        "transition.2462",
        "transition.2463",
        "transition.2464",
        "transition.2466",
        "transition.2467",
        "transition.2468",
        "transition.2469",
        "transition.2470",
        "transition.2471",
        "transition.2472",
        "transition.2473",
        "transition.2474",
        "transition.2475",
        "transition.2476",
        "transition.2477",
        "transition.2479",
        "transition.2481",
        "transition.2482",
        "transition.2483",
        "transition.2484",
        "transition.2485",
        "transition.2486",
        "transition.2487",
        "transition.2488",
        "transition.2489",
        "transition.2490",
        "transition.2491",
        "transition.2492",
        "transition.2493",
        "transition.2496"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-27T15:00:13+00:00",
      "transition_id": "transition.2124",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0353",
      "last_observed_at": "2026-09-02T11:05:50+00:00",
      "observation_count": 29,
      "observed_transition_ids": [
        "transition.2363",
        "transition.2364",
        "transition.2365",
        "transition.2366",
        "transition.2367",
        "transition.2368",
        "transition.2369",
        "transition.2370",
        "transition.2371",
        "transition.2372",
        "transition.2373",
        "transition.2374",
        "transition.2375",
        "transition.2376",
        "transition.2377",
        "transition.2378",
        "transition.2379",
        "transition.2380",
        "transition.2381",
        "transition.2382",
        "transition.2383",
        "transition.2384",
        "transition.2385",
        "transition.2386",
        "transition.2387",
        "transition.2388",
        "transition.2392",
        "transition.2393",
        "transition.2394"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-08-31T07:46:01+00:00",
      "transition_id": "transition.2363",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "contamination_barrier.0354",
      "last_observed_at": "2026-09-09T10:35:54+00:00",
      "observation_count": 2,
      "observed_transition_ids": [
        "transition.2495",
        "transition.2505"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-06T05:44:16+00:00",
      "transition_id": "transition.2495",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0355",
      "last_observed_at": "2026-09-09T17:04:58+00:00",
      "observation_count": 3,
      "observed_transition_ids": [
        "transition.2513",
        "transition.2516",
        "transition.2519"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-09T16:53:03+00:00",
      "transition_id": "transition.2513",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0356",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "observed_transition_ids": [
        "transition.2520",
        "transition.2523",
        "transition.2526",
        "transition.2529"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "status": "active",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "transition_id": "transition.2520",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0357",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "observed_transition_ids": [
        "transition.2520",
        "transition.2523",
        "transition.2526",
        "transition.2529"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "status": "active",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "transition_id": "transition.2520",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0358",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "observed_transition_ids": [
        "transition.2520",
        "transition.2523",
        "transition.2526",
        "transition.2529"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "status": "active",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "transition_id": "transition.2520",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0359",
      "last_observed_at": "2026-09-10T09:29:23+00:00",
      "observation_count": 8,
      "observed_transition_ids": [
        "transition.2521",
        "transition.2524",
        "transition.2527",
        "transition.2530",
        "transition.2547",
        "transition.2552",
        "transition.2555",
        "transition.2557"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-09-09T17:34:25+00:00",
      "transition_id": "transition.2521",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0360",
      "last_observed_at": "2026-09-09T17:55:26+00:00",
      "observation_count": 3,
      "observed_transition_ids": [
        "transition.2522",
        "transition.2525",
        "transition.2528"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-09T17:34:58+00:00",
      "transition_id": "transition.2522",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "contamination_barrier.0361",
      "last_observed_at": "2026-09-10T10:19:51+00:00",
      "observation_count": 27,
      "observed_transition_ids": [
        "transition.2531",
        "transition.2532",
        "transition.2533",
        "transition.2534",
        "transition.2535",
        "transition.2536",
        "transition.2537",
        "transition.2538",
        "transition.2539",
        "transition.2540",
        "transition.2541",
        "transition.2542",
        "transition.2543",
        "transition.2544",
        "transition.2545",
        "transition.2546",
        "transition.2548",
        "transition.2549",
        "transition.2550",
        "transition.2551",
        "transition.2553",
        "transition.2554",
        "transition.2556",
        "transition.2558",
        "transition.2559",
        "transition.2560",
        "transition.2561"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-09-09T18:27:05+00:00",
      "transition_id": "transition.2531",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "active_contamination_barriers_truncated": false,
  "debug_layer": "board_axi_ddr_wrapped_system",
  "global_persisted_blocker_counts": {
    "active_contamination_barriers": 27,
    "open_backtrack_requests": 1,
    "open_retry_requests": 8
  },
  "omitted_unscoped_or_cross_layer_blocker_counts": {
    "active_contamination_barriers": 3,
    "open_backtrack_requests": 1,
    "open_retry_requests": 0
  },
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 8,
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0136",
      "last_observed_at": "2026-09-09T17:04:22+00:00",
      "observation_count": 11,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
        "3013ac2f2886a4bb0e21b0ddcc54c82cffbbdd09e2328421291a438ce8b90e02",
        "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "afb85285384f56405c8cac1a5b1b8c83709c82fefd27ff3d28817fb7e0e04212",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0140",
      "last_observed_at": "2026-09-09T17:04:23+00:00",
      "observation_count": 11,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0141",
      "last_observed_at": "2026-09-01T15:47:55+00:00",
      "observation_count": 3,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
        "efda18fd733bdb42026f8f508143b6cf03763d66ceddd826a75bb87fbd192357",
        "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "0e1c0b6ed8b95b87869fb645c94f02583f5cf9b7da441c7490b90595524dcccd",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0142",
      "last_observed_at": "2026-09-01T15:51:29+00:00",
      "observation_count": 6,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "retry_request.0143",
      "last_observed_at": "2026-09-02T13:04:16+00:00",
      "observation_count": 21,
      "observed_source_fingerprint_sha256s": [
        "6f79d3af2a76861b4372a0fd1a6cd00cb5ecc192bca91dd73cdd629da6708b28",
        "c951d2ee708694ff68c2a999b41676974884c1365ffc72998e29f1b5b3182a4b",
        "082a6eeef0e71e2d7e0fd421ae866cfe1993bd5dff7b26db7a530cb05510e5e2",
        "95b72bf31433286e640fa36319cc9596500a6de71ba75f2a68d01f1fc871571c",
        "44f5c7d691ea8d52c42121b934e2c52e18340318d92d12519de5fa6111b21353",
        "56c0cd51d731f4779da7740951e73c43f75c2faa5fa4d8ba39824ce8d9c8e488",
        "1fe929b448ef2f95a69599bb6dd45ee16d60ec4ba02b894f949c57fccbc62e18",
        "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "291294b739734a6327a2e1b4885b791bf3307d137aedd0a79ef4843e1a86acb8",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-27T12:56:18+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "retry_request.0144",
      "last_observed_at": "2026-09-09T10:04:51+00:00",
      "observation_count": 43,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-27T12:59:36+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "retry_request.0145",
      "last_observed_at": "2026-09-09T18:18:23+00:00",
      "observation_count": 4,
      "observed_source_fingerprint_sha256s": [
        "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "04f55ea712a42a4af50bf0f413e5c219623ab1b9e1168c3442a391ec2551f9ba",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-09-09T17:34:24+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "functional_sim"
      ],
      "id": "retry_request.0146",
      "last_observed_at": "2026-09-10T09:29:23+00:00",
      "observation_count": 8,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-09-09T17:34:25+00:00",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "open_retry_requests_truncated": false,
  "policy": "This is the authoritative current blocker set for the named hierarchy scope. Unscoped and cross-layer blockers remain persisted in SACG and are enforced by their owning layer or downstream promotion gates, but they are not executable blockers for this repair prompt.",
  "schema_version": "spatialaccagent.scoped_sacg_memory_truth.v1",
  "truth_source": "source_sacg_state.memory",
  "verification_scope": "board_axi_ddr_closure"
}
</sacg_memory_truth>

<hierarchical_learning_context>
{
  "debug_layer": "board_axi_ddr_wrapped_system",
  "decision_policy": {
    "accepted_input_handshake_required_before_kernel_lifecycle_start": true,
    "current_output_or_lifecycle_frontier_evidence_required_for_board_liveness_claim": true,
    "current_scope_tools_and_exact_board_wrapper_remain_required": true,
    "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": true,
    "frontier_stall_is_localization_evidence_not_a_root_cause_or_pass_claim": true,
    "independent_prefetch_or_axi_progress_is_not_output_frontier_progress": true,
    "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": true,
    "lower_layer_reopen_requires_current_trace_named_contradiction": true,
    "repeat_repair_class_requires_fresh_intervention_response_evidence": true,
    "resolved_artifact_identity_lessons_are_not_rtl_failures": true,
    "use_only_live_validated_lower_layer_evidence": true
  },
  "kernel_timing_knowledge": [
    {
      "accepted_trace_record_count": 416,
      "all_planned_stages_concurrent_observed": true,
      "all_planned_stages_participate_in_required_overlap": true,
      "all_planned_stages_same_cycle_concurrency_required": false,
      "boundary_order_summary": {
        "all_first_token_order_preserved": true,
        "all_last_token_order_preserved": true,
        "boundary_count": 13,
        "complete_count": 13
      },
      "contract_sha256": "496fc6b3c907d9401a2156dc906f39f7a7ade964fa60f682fff0be5f31b5b393",
      "evidence_schema_version": "spatialaccagent.single_layer_pipeline_overlap_evidence.v3",
      "file_sha256": "8475614f6ff71fd6b7ccb2c80a307fa12ed0ed6517b0eb71ac74b010b19f748f",
      "kind": "connected_kernel_pipeline_timing",
      "lesson": "The connected kernel is an elastic, variable-latency token pipeline. Preserve verified boundary order and required adjacent-stage cross-token overlap; do not diagnose unequal stage durations as a failure merely because all stages do not start or finish on the same cycle.",
      "maximum_concurrent_stage_count": 9,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/d2d2039720d94e9aab7ffb152d15ef57/evidence/single_layer_functional/0095_case_single_layer_functional_single_layer_functional_report.json",
      "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
      "planned_stage_count": 9,
      "required_dependency_overlap_complete": true,
      "required_direct_dependency_overlap_summary": {
        "all_different_token_overlap_observed": true,
        "boundary_count": 9
      },
      "stage_turnover_gaps_are_diagnostic": true,
      "trace_record_count": 416,
      "trace_sha256": "3440370152a8584f86283bcd39924aa04050e9a0694a763ad12accc3242095b1"
    }
  ],
  "resolved_evidence_lessons": [
    {
      "file_sha256": "e5ed97138e1dbecd4fd1ed4cf28508674196e0bf46084e72656d0dbd25006813",
      "kind": "lower_scope_certificate_continuity",
      "lesson": "A higher-scope binding update was proven not to alter certified leaf evidence; do not replay or reopen leaf operators without a current contradictory trace.",
      "live_operator_leaf_file_count": 245,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/b5b9c90c11d5d96e420eddb259419e622e571608abd1e42d2a58d56a36dfed0a/operator_leaf_certificate_scope_continuity.json"
    },
    {
      "file_sha256": "b73f60137fa39f8a598938527be69488287821e4e6f8f0326926ac1543d2bfce",
      "kind": "lower_scope_certificate_continuity",
      "lesson": "A higher-scope binding update was proven not to alter certified leaf evidence; do not replay or reopen leaf operators without a current contradictory trace.",
      "live_operator_leaf_file_count": 245,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/59e7c1304b51eee277b082f508c70402f44da1eec56b80af5b05f1142304638e/operator_leaf_certificate_scope_continuity.json"
    },
    {
      "file_sha256": "927189885346bfb8788316b9d7fb599f8c17d41836c68a40cf98c161f6823d36",
      "kind": "lower_scope_certificate_continuity",
      "lesson": "A higher-scope binding update was proven not to alter certified leaf evidence; do not replay or reopen leaf operators without a current contradictory trace.",
      "live_operator_leaf_file_count": 245,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/e48dd4983acaab3d92ca6250954e0f6f595d3a00650f990e21eda2b30850523c/operator_leaf_certificate_scope_continuity.json"
    },
    {
      "bridge_fingerprint_sha256": "507a9946e13853f25266c5c8fa7847fa9618050add8e19c26618881308961430",
      "file_sha256": "0d269796162c045964d9caa52ef7049ad0bd395a6d34e813dc47fb57b25d9021",
      "kind": "lower_layer_certificate_scaffold_bridge",
      "lesson": "The connected-layer scaffold has a live lower-layer certificate bridge; do not regenerate certified leaf testbenches merely to satisfy a legacy scaffold checker.",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/d2d2039720d94e9aab7ffb152d15ef57/evidence/single_layer_functional/0000_case_tb_scaffold_tb_scaffold.json"
    }
  ],
  "schema_version": "spatialaccagent.hierarchical_learning_context.v1",
  "status": "pass",
  "status_bar_contract": {
    "covers_only_live_validated_lower_layer_certificates": true,
    "does_not_replace_current_scope_tool_results": true,
    "maintainer": "framework_deterministic_hash_bound_projection",
    "not_an_llm_generated_history_summary": true,
    "raw_evidence_remains_retrievable_by_path_and_sha256": true
  },
  "validated_lower_layer_certificates": [
    {
      "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
      "claim": "Every selected operator leaf passed target-model semantic comparison with real target weights, auditable input provenance, and an independent expected output, and may be reused as lower-layer evidence for single-transformer-layer verification.",
      "debug_layer": "operator_leaf_modules",
      "derivation_kind": "lower_scope_continuity_after_higher_scope_binding_update",
      "does_not_claim": [
        "full end-to-end model semantic correctness",
        "single-transformer-layer integration correctness",
        "board AXI/DDR wrapper correctness",
        "backend, bitstream, or board-runtime readiness"
      ],
      "evidence_binding_file_count": 810,
      "evidence_binding_roles": {
        "evidence_artifact": 12,
        "gate_log": 8,
        "input_artifact": 324,
        "lower_scope_certificate_continuity_proof": 13,
        "operator_leaf_continuity_bound_weight_tensor": 12,
        "operator_leaf_continuity_golden_output": 9,
        "operator_leaf_continuity_input_vector": 12,
        "operator_leaf_continuity_materialized_runtime_stream": 1,
        "operator_leaf_continuity_materialized_runtime_stream_source": 4,
        "operator_leaf_continuity_materialized_weight_stream": 6,
        "operator_leaf_continuity_semantic_harness_source": 191,
        "operator_leaf_continuity_semantic_testbench": 9,
        "operator_leaf_continuity_target_model_reference": 1,
        "produced_report": 9,
        "selector_contract": 8,
        "source_file": 191
      },
      "evidence_binding_sha256": "1d48c4345b67e5ba960b6ead7e0679d2b9b59cd2bece33c1f21c4f3f59b6776f",
      "file_sha256": "6ff8e9b1b1abcc938042795e816e2ddf728f8c27773586b2afcc162a724f3a5e",
      "level_id": "operator_leaf_functional",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/operator_leaf_promotion_certificate.json",
      "required_gates": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_stage_leaf_static",
        "boundary_contract_check",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence"
      ],
      "scope": "operator_leaf_closure"
    },
    {
      "artifact_id": "artifact.stage7.single_layer_promotion_certificate",
      "claim": null,
      "debug_layer": "single_transformer_layer_kernel",
      "derivation_kind": null,
      "does_not_claim": [],
      "evidence_binding_file_count": 182,
      "evidence_binding_roles": {
        "evidence_artifact": 7,
        "gate_log": 5,
        "input_artifact": 101,
        "produced_report": 7,
        "selector_contract": 5,
        "source_file": 57
      },
      "evidence_binding_sha256": "aca81fec6b2bbaa488813c14c5631fa3f7b740b32aec2d5116617a301ff20e1f",
      "file_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7",
      "level_id": "single_layer_functional",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/single_layer_promotion_certificate.json",
      "required_gates": [
        "case_tb_scaffold",
        "single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "case_single_layer_semantic_evidence"
      ],
      "scope": "single_layer_closure"
    }
  ],
  "verification_scope": "board_axi_ddr_closure"
}
</hierarchical_learning_context>

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
    "connected_kernel_targeted_replay_check",
    "connected_kernel_cctg_contradiction_reconciliation_check",
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
    "connected_kernel_cctg_contradiction_targeted_replay",
    "connected_kernel_targeted_replay_check",
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
    "agent": {
      "type": "string"
    },
    "approval_required_for": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "executable_actions": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "acceptance_checkers": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "action_type": {
            "type": "string"
          },
          "consumes": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "id": {
            "type": "string"
          },
          "on_failure": {
            "type": "string"
          },
          "produces": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "rationale": {
            "type": "string"
          },
          "requires_approval": {
            "type": "boolean"
          },
          "stage": {
            "type": "string"
          },
          "tool_roles": {
            "items": {
              "type": "string"
            },
            "type": "array"
          }
        },
        "required": [
          "id",
          "stage",
          "action_type",
          "rationale",
          "consumes",
          "produces",
          "tool_roles",
          "acceptance_checkers",
          "on_failure",
          "requires_approval"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "observations": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "proposed_actions": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "risks": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "sacg_focus": {
      "additionalProperties": true,
      "properties": {
        "artifacts": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "constraints": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "edges": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "nodes": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "nodes",
        "edges",
        "constraints",
        "artifacts"
      ],
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    },
    "stage": {
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
    "sacg_focus",
    "observations",
    "risks",
    "proposed_actions",
    "executable_actions",
    "approval_required_for"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
