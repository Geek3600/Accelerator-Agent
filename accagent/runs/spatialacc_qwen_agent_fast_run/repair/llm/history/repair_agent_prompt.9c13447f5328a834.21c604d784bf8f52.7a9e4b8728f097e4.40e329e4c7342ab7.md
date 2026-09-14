<agent>
repair_agent
</agent>

<task>
Make the authoritative bounded-repair decision from verification failures, SACG/CCTG evidence, and the conditional specialist review when one was triggered, without bypassing checkers. Respect the hierarchical repair loop: if lower layers already passed and the current layer failed, request current-layer boundary trace/targeted replay first; reopen lower-layer modules only when the trace explicitly contradicts their pass evidence.
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
        "input_fingerprint_sha256": "132a6632389ced2e1b46d5ec506110b28e3b4cb4eb50592710d5270a73f61d73",
        "origin_gates": [
          "case_vcs_functional_sim"
        ],
        "origin_layer": "board_axi_ddr_wrapped_system",
        "policy": {
          "cross_layer_reuse_is_read_only_without_an_explicit_targeted_backtrack": true,
          "current_failed_gate_must_match_origin_or_target_rerun_gate": true,
          "live_source_artifact_hashes_must_match": true
        },
        "preflight_manifest_projection_sha256": "290fa0e2e5e1c5eb4bea56c3fc0c5f2172aa46f3c009de08cba984208a8f7126",
        "schema_version": "spatialaccagent.diagnosis_applicability_binding.v1",
        "source_artifacts": [
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
            "role": "board_vcs_runner_report",
            "sha256": "98971b9e2f83590aa32ce0a07fbde64a6a3d62d1cfe4048bb8a766b4e35bc6d1"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json",
            "role": "board_simulation_manifest",
            "sha256": "5f0f8f6d3362c44f074aef7c5f38f4093ecababb802dbdb6672be57903579272"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/board_source_identity.json",
            "role": "board_source_identity",
            "sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
            "role": "semantic_testbench_manifest",
            "sha256": "45adbf89e7954e69f04138976b2ab49a7f90e069aa2bba61c80106126effc645"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
            "role": "dut_weight_binding_manifest",
            "sha256": "96e2a14ffb8961644d4fc0836e6f8a8c44d05295cff0fbb7f6b41ac0c70a1188"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_executed_manifest.json",
            "role": "executed_board_manifest",
            "sha256": "ce1acfbb458d747e6b51cf480475d22c66ca05ab50b27d10956add90a4c34d2b"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
            "role": "sacg_cctg_causal_slice",
            "sha256": "0c734734b891dfb00355f84a3a7a59774c173f313b4ebe7579830b78dcc82139"
          }
        ],
        "source_identity_sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66",
        "target_layer": "board_axi_ddr_wrapped_system"
      },
      "blockers": [
        "vcs_compile_failure: Error-[IND] Identifier not declared"
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
        "boundary_trace_failed_count": 0,
        "boundary_trace_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
        "boundary_trace_record_count": 16,
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
          "duration_sec": 43.38040123499377,
          "failure_class": "remote_tool_failure",
          "remote_state": "done",
          "returncode": 1,
          "status": "fail"
        },
        "failure_class": "vcs_compile_failure",
        "first_real_error": "Error-[IND] Identifier not declared",
        "intra_layer_pipeline_violation_evidence": {},
        "live_progress": {
          "history": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress_history.jsonl",
          "latest": {},
          "raw_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
          "snapshot": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress.json",
          "status": "pending_first_flushed_event",
          "zero_time_livelock_evidence": {}
        },
        "log_tail": "/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n                         Chronologic VCS (TM)\n         Version S-2021.09_Full64 -- Fri Sep  4 13:40:01 2026\n\n                    Copyright (c) 1991 - 2021 Synopsys, Inc.\n   This software and the associated documentation are proprietary to Synopsys,\n Inc. This software may only be used in accordance with the terms and conditions\n of a written license agreement with Synopsys, Inc. All other use, reproduction,\n   or distribution of this software is strictly prohibited.  Licensed Products\n     communicate with Synopsys servers for the purpose of providing software\n    updates, detecting software piracy and verifying that customers are using\n    Licensed Products in conformity with the applicable License Key for such\n  Licensed Products. Synopsys will use information gathered in connection with\n    this process to deliver software updates and pursue software pirates and\n                                   infringers.\n\n Inclusivity & Diversity - Visit SolvNetPlus to read the \"Synopsys Statement on\n            Inclusivity and Diversity\" (Refer to article 000036315 at\n                        https://solvnetplus.synopsys.com)\n\nsh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nParsing design file '../sources/Activation.sv'\nParsing design file '../sources/AddRawFN.sv'\nParsing design file '../sources/AddRecFN.sv'\nParsing design file '../sources/AttentionGQA.sv'\nParsing design file '../sources/CompareRecFN.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_1.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_2.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_3.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_5.sv'\nParsing design file '../sources/ConnectedObservableLlamaStyleBlock.sv'\nParsing design file '../sources/ConnectedStreamIngress.sv'\nParsing design file '../sources/ConnectedWeightLoader.sv'\nParsing design file '../sources/DivSqrtRawFN_small_e8_s24.sv'\nParsing design file '../sources/DivSqrtRecFMToRaw_small_e8_s24.sv'\nParsing design file '../sources/DivSqrtRecFM_small_e8_s24.sv'\nParsing design file '../sources/ElementwiseMul.sv'\nParsing design file '../sources/GatedMLP.sv'\nParsing design file '../sources/INToRecFN_i25_e8_s24.sv'\nParsing design file '../sources/INToRecFN_i36_e8_s24.sv'\nParsing design file '../sources/Linear.sv'\nParsing design file '../sources/Linear_1.sv'\nParsing design file '../sources/Linear_2.sv'\nParsing design file '../sources/Linear_3.sv'\nParsing design file '../sources/Linear_4.sv'\nParsing design file '../sources/MulFullRawFN.sv'\nParsing design file '../sources/MulRawFN.sv'\nParsing design file '../sources/MulRecFN.sv'\nParsing design file '../sources/QKVProjection.sv'\nParsing design file '../sources/Queue113_StreamBeat.sv'\nParsing design file '../sources/Queue1792_StreamBeat.sv'\nParsing design file '../sources/Queue2_StreamBeat.sv'\nParsing design file '../sources/Queue2_StreamBeat_1.sv'\nParsing design file '../sources/Queue4_StreamBeat.sv'\nParsing design file '../sources/Queue4_StreamBeat_2.sv'\nParsing design file '../sources/RMSNorm.sv'\nParsing design file '../sources/RecFNToIN_e8_s24_i16.sv'\nParsing design file '../sources/RecFNToRecFN.sv'\nParsing design file '../sources/RecFNToRecFN_8.sv'\nParsing design file '../sources/ResidualAdd.sv'\nParsing design file '../sources/RoPE.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie5_is11_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie6_is25_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie7_is36_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is24_oe5_os11.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is26_oe8_os24.sv'\nParsing design file '../sources/RoundRawFNToRecFN_e8_s24.sv'\nParsing design file '../sources/SingleLayerSemanticHarness.sv'\nParsing design file '../sources/Softmax.sv'\nParsing design file '../sources/VectorNorm.sv'\nParsing design file '../sources/expTable_2048x26.sv'\nParsing design file '../sources/ram_113x269.sv'\nParsing design file '../sources/ram_1792x269.sv'\nParsing design file '../sources/ram_2x144.sv'\nParsing design file '../sources/ram_2x269.sv'\nParsing design file '../sources/ram_4x144.sv'\nParsing design file '../sources/sigmoidTable_129x19.sv'\nParsing design file '../sources/ConnectedObservableLlamaStyleBlock_Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nParsing included file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'.\nParsing design file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'\nParsing design file '../sources/app_shell_9p_cnn_core_0_1.v'\nParsing design file '../sources/spatialacc_exact_board_multilayer_tb.sv'\n\nError-[IND] Identifier not declared\n../sources/spatialacc_exact_board_multilayer_tb.sv, 2578\n  Identifier 'ACTIVATION_AXI_BEATS_PER_TOKEN' has not been declared yet. If \n  this error is not expected, please check if you have set `default_nettype to\n  none.\n  \n\nParsing design file '../sources/spatialacc_axi_protocol_monitor.sv'\n1 error\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nCPU time: 15.235 seconds to compile\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
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
          "certified_kernel.0000.793c663cab4c2493",
          "certified_kernel.0001.b6e7401e9ba54fe7",
          "certified_kernel.0002.e30b913a4fcbf712",
          "certified_kernel.0003.ce2ed5a48d6925e4",
          "certified_kernel.0004.814f90c0d54776d0",
          "certified_kernel.0005.549dfbf4d406e113",
          "certified_kernel.0006.02ed8639f6abfaa9",
          "certified_kernel.0007.0e59ca9664473372",
          "certified_kernel.0008.f3881db839805370",
          "certified_kernel.0009.c7867a9c5dc80117",
          "certified_kernel.0010.7403a7f048b7838a",
          "certified_kernel.0011.586749abab288c0a",
          "certified_kernel.0012.31c41e3b52b51e0e",
          "certified_kernel.0013.36544e04d9b73705",
          "certified_kernel.0014.e7082c31ca17c857",
          "certified_kernel.0015.d6c5273532b22e2e",
          "certified_kernel.0016.77cabc8da0382228",
          "certified_kernel.0017.2b227d4de39b8fad",
          "certified_kernel.0018.8ecf314ffd508688",
          "certified_kernel.0019.38e37b277c02a765",
          "certified_kernel.0020.9912819dd3fae37e",
          "certified_kernel.0021.c7f97e407c087a90",
          "certified_kernel.0022.6d8306c120a79038",
          "certified_kernel.0023.85be27c74f6523cb",
          "certified_kernel.0024.0c835c2614fb651a",
          "certified_kernel.0025.36d990d3717ff7a0",
          "certified_kernel.0026.4649532c4e1e62ea",
          "certified_kernel.0027.14615abf8650a1fe",
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
          "sha256": "0c734734b891dfb00355f84a3a7a59774c173f313b4ebe7579830b78dcc82139",
          "value": {
            "failure_class": "vcs_compile_failure",
            "input_fingerprint_sha256": "132a6632389ced2e1b46d5ec506110b28e3b4cb4eb50592710d5270a73f61d73",
            "llm_analysis_contract": {
              "must_not_edit_hardware_for_transport_or_tool_environment_failure": true,
              "must_not_reuse_a_prior_fingerprint_runtime_slice": true,
              "use_earliest_real_tool_error_before_runtime_graph": true
            },
            "reason": "SACG/CCTG runtime frontier selection requires a completed VCS compile and an attempted simulator execution",
            "remote_workdir": "/home/hyyuan/workspace/spatialaccagent_artifacts/board_vcs/spatialacc_qwen_agent_fast_run/132a6632389c_381133731991988262521510101793642845858115963945250296234909043",
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
                "simulation.dynamic_evidence_records[1] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
                "simulation.dynamic_evidence_records[2] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/progress_event_log.jsonl",
                "simulation.dynamic_evidence_records[3] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
                "simulation.dynamic_evidence_records[4] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/runtime_loader_report.json",
                "simulation.dynamic_evidence_records[5] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json"
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
                "simulation.runtime_loader_results.layers[1] is missing",
                "simulation.runtime_loader_results.layers[2] is missing",
                "simulation.runtime_loader_results.layers[3] is missing",
                "simulation.runtime_loader_results.layers[4] is missing",
                "simulation.runtime_loader_results.layers[5] is missing",
                "simulation.runtime_loader_results.layers[6] is missing",
                "simulation.runtime_loader_results.layers[7] is missing",
                "simulation.runtime_loader_results.layers[8] is missing",
                "simulation.runtime_loader_results.layers[9] is missing",
                "simulation.runtime_loader_results.layers[10] is missing",
                "simulation.runtime_loader_results.layers[11] is missing",
                "simulation.runtime_loader_results.layers[12] is missing",
                "simulation.runtime_loader_results.layers[13] is missing",
                "simulation.runtime_loader_results.layers[14] is missing",
                "simulation.runtime_loader_results.layers[15] is missing",
                "simulation.runtime_loader_results.layers[16] is missing",
                "simulation.runtime_loader_results.layers[17] is missing",
                "simulation.runtime_loader_results.layers[18] is missing",
                "simulation.runtime_loader_results.layers[19] is missing",
                "simulation.runtime_loader_results.layers[20] is missing",
                "simulation.runtime_loader_results.layers[21] is missing",
                "simulation.runtime_loader_results.layers[22] is missing",
                "simulation.runtime_loader_results.layers[23] is missing",
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
          "exact_source_replay_fingerprint_sha256": "132a6632389ced2e1b46d5ec506110b28e3b4cb4eb50592710d5270a73f61d73",
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
        "all_target_layers": true,
        "binding_manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
        "consumed_tensor_hash_source": "dut_weight_binding_manifest.board_consumed_tensor_hashes",
        "consumed_tensor_hashes": [
          "00b8f989c23bf94a55af6a62745731b51431dbe0a6f0f3772606a558b266a46a",
          "0124f2b929672c802bdc1322ff5c90c3bfb9a9ea40f4abac6f269f9f08ae137a",
          "0179c720566efb6ec86df085d04bfc780891e437592975d8e28c06a01cb9e0e8",
          "01c0dae0fdd06200a18e5b9991fb22ce96eac74c4976598e7ef8d49266cfe619",
          "02061e3683742bc0151134c4bfe46e4e0e4b36efa2f6d336fc8dddc8fd8bd635",
          "0209b3fda843d0be42900fe58fbd4d49df8539f10f55907ab9adf440ff6bb498",
          "024578a764476fa46c5e60265095f655f0cc65ddc82750a1918f7af2e5d90413",
          "0345185fd11b1818dfe5e6e4dcd6f23113a32fab70409bcc34588b2593117530",
          "0398c41adf8fa9c8a1bc757216612bf2ec50a5e0d1882717fd85eb309035ab0a",
          "045c6cd32c96ea0041025a6e746bdaf0cd5dc60f302a026e7b11e1f0df282f81",
          "04b03173f20a48285638cbacb9d2f30fb778c766f99e9dc3b8f7f196d2c121fc",
          "0626fd310bf61f4d14eab176d124a88f7810032e6814c3fe2604af03986c9270",
          "07c9d7c21eb480569babfc4e60e48055056844aad4dae587202427826dc116f7",
          "0836ce4568d43b91720aeec77c5c3cf5da973402c3a594d5d4e7e78f3f1b456b",
          "08f3438e1d7046e1ca763c9f9101a5c9d267a476d479f56ac2339916e1df8225",
          "091d2981a666699d6f48c23946e2d5e4f100b16174c75efb89d23b7dfe842bf1",
          "0abf7d122d6b86639abb9fd4959e1ff71cf8bdce341ef2eae9bfa81d9b889c95",
          "0af69214964204bcb46ac4bc8714b38682df5cb52c442197b0c44e5fa7c176e5",
          "0c811d068c4535b8ee8d5098d1a576cd57139e285c3af8d4bacf2680210c5b52",
          "0d09d8a07e58c70c1afcdf8ff77326db4ebe4e7356c56d2c4f39d016d24109ff",
          "0d0c2e986b79337c0af626b4696e2c5bfdbfea3ae899aad066b1224706b7e875",
          "0d9a7d0849ef52a844e49d7d5b5bb7882c3a6cacb4393ed8635ee8edbae2ee90",
          "0ed64ab14304fa3264d818007c8dae90fcbb0c6abc090c354bdba82e164cbc23",
          "0ee8b903526f560c1934b92cbf2976d6b07c750e0eb327fb5fd8bcd3ec27b9c5",
          "1131e30699fbaba9e392894aa9deb7afd790f172c8363f48207ad2f19aa13177",
          "119a498fe1b98488cf145914025198583b4e8717602f392989b8ffcae3234cf5",
          "13d57fec399ae74a7a44c1a545de166705d11f511dd7dfe33fd58316b8cf737e",
          "1541d3f2080089624a3b32babc9cd27178d18bb9b3b9e128d7ff28c55a2de8d1",
          "15d1132dffd54e362485d225d6a40e6193c412a930a93b57815097e752a8f0a1",
          "1610dd561ae03b13a4fd758d9e2ba5b1d52131144041a38d3dcac9a7be94df29",
          "1737eabd8fdf744885b74f99dee50926be20963b7030f1963da37f7906b06619",
          "17a2860fe1d997e08bd88ea8e979a16bc7fcb8258edbca17558925a212fbe6d5",
          "1921a2d5bf9e6daa33c6030c52f132c9f8f5ee18527b762a98fcaa442a2b3fc6",
          "197a44cc486cfa1b8753e8027ede352db839d80fbf7fae5add0ef9f0f3b6ba2a",
          "1a00b42e429cd9cb90bbe25dd2649f0f8b2b0f3ab0435f05eda15d55912083b0",
          "1a698b69dfb8f87752eca0d95d2e8727db0b99d79dca955a95b79578d3e9e00d",
          "1b102cf40a35e4c5ccd49bee2d1da9cb7a14bade57f6f6253ac6c53b149e954d",
          "1b8fc11b559a4933f6ab70a022163e58dd3e42083f56de6c1ccbf4b32bdc7d0d",
          "1bd7aaa1aa43ebfb1fa3ae1b19a0e9fa2a17c7fb223d993e81dbdecc16a5ac5b",
          "1decc3dd0897c9a113d1e86b106eb5ab7a07502c411229ff8bd0b83ddbdc0175",
          "1e2831c122eb62745700cf81e30dd61e5e45598979f648c83e4064a18cadefde",
          "1e7d59ab3675143dafe924bc9a468e2cca0b77ca28f502059a0e17bd9aaa26a2",
          "1f2ca270874299297f9ee4f4082f59520cff15c291ad3c17b7cc0264b378d315",
          "1fb9fda61dbaaeaa7f69ac5bca11cc5b3998264adead65c8af82ab53a620f545",
          "1ff9e60ba643bb1beff31f0e1c352400335f07db20919c9fc44a081ffb24146b",
          "1ffa1a455563fdd99c5e7e65ccff30afe8dd464c2b6f2d39e537a371bcb024d7",
          "1ffa4e9fb661c5f46a63bf97d4e72b6f846897ed90518e15a92a1bbe1283bec9",
          "20f069f21809f8efd97121d72e21c62a0a605de0f7e1aa72fccb6e4405f03173",
          "2322e74d06def44377e70cdc4e55a8e288d581f9ed3f7364582972ead81a133c",
          "242d0ba5f68dd1c380ec270558f56b9259cfa8c64eda0eaf9172d218f136d3f9",
          "256ebf62b7b97a90ccc9bd443559e7ac38e80e5f01d01f3c9a706d7489422661",
          "262752e9ca19e527941e488e8602f3e8185f060f40a8c550fc6f544fdda84721",
          "2736051bc5ead9abf8d200f6f4c4b164a1d5ac1bd04560b0e495f7e52e4d1f0a",
          "283f65732ee4b3aff22a13913701d530ee43f34da448dece512e958f68d2c234",
          "287afd359de170598bb9f43f3036e8cc281f3cc88aae3050aa95f9b21a20b6a5",
          "2a50b9897b95ab438ab7415d4f45518ba007dc53a4f5fa36b7ea310dc19cbce5",
          "2ac752e961cf6966c2206f8e60b29f395ddbd86fe467be619e0c8466152e632e",
          "2aed51f9c0c64581ca0a4bafdc208a86320bbb8b397274abb1b825ba0c87c3cd",
          "2bbf50df5749f22374d855bce9ee7f22bd3a9fd15b79ef6453fa85034de30716",
          "2d5434ce8ec904191b4ba128bb81da443efae53d0c6bb3095fb3d0bdb562d84d",
          "2e938fa28a213e9ed4fa6a30d9b5df258ca6f4a90552584b64525b9abfcfa03b",
          "30ac399e735534fd8c9487b2f254efbf53d7ab03db18ec2960f4d9c520332c71",
          "328c77f4522c0989b6524606255778d1499039cda005a03749dcff7ff2b42e07",
          "336095cd67196d54898f48e96ca324a2a762390c5d02592d3f12397277f06b36",
          "33b3c029d36bad5cd0b87282a093badb88b6114d781404c43e6c83c374947458",
          "346eda969599f584be47a7cd73af5301d39717def5fa43cbfff407297fbc78d9",
          "356ad673958c64f61fb0554044a316a40cdcf15c5532df5fe8a433243461f781",
          "35715ffde9ddff0945982622c4e035214a8716048e291e3ccf94de8015f10e48",
          "358f5765420b07a66d3e1ddccc210d73ac1731000e1fe60f30e711aa88f0ce6a",
          "38d6356bea686b676e69a0f79234c65f4f43fb65d4b6d9abd927d6048ee3d43e",
          "39640d57143079e39d21cc119b11204231a20816aaf55ae410bf00bf2e3cbc8a",
          "3a5109104cc76c897c9ae89e5c66d09dd05836f14a24f03280cd6e972a8db92f",
          "3a56f563486166261373302094ce6428e79159caa89b9f9ca4e80791263deed3",
          "3ae517f12c305b425f14356d96d6be262e2f869655555f7634e8fab50a581476",
          "3bda6ffa2249e33dc69266ba5e29dff70cc86bd37e354d98f7a0db759f854f1d",
          "3c12f111214fea28c2ae1539490616a3106294ee5eb72f5cdcca6aa8c1efabdd",
          "3d3fa3fd741314f77833fd5bb1e717327f99153473978d772811d8ab95810b40",
          "3eb99408afcd2cc3a0ebca0bc424067fc81c58e733ff46f29c0a02fb8d5a52e8",
          "3fae75ecbf6b3b7f7a5ba5b31281869f395287f21a7f767a85df627bf787858e",
          "3fdaa932ce0ada56ae61a8a7a2fb26da24fa84768963cff42952e9fb9234fc3b",
          "40a3a31c1a1ad85dfae807d9d5e37fd6bf592528018ecb543638b53d980ec001",
          "40b4ebf2b3b016ecfb6bd0abfd0b4b5f20ef387e8e30297fc38622763e1302bf",
          "41c9267cf82815ec8f16ba32ca458ad2096ca592aa8a13af8f1cf7066275a419",
          "41cecdcb0e10de99dd1838eb201e1b6ba5c3f5233b836efa04b600868e9c3c6f",
          "424cc7f6748b0800e8b3d6694a35cd1dfef74ca0d2825e2c1863cef5e0f0273e",
          "452fa3bd5795ec51e4fa75a2b577cfc90f36548a66c7a168b5233a7e63bda5f7",
          "453d88499d3f43d1e2bbc90bc6e980cf2fefcccbd6074d587f768d71e644c389",
          "453e08737e168d8d1a58e67c561cc4f8aacae36fa5346198306c4d144d9c1b20",
          "46736f006bb8c6573b3dd4d2f55de1e0c00dceb72cdfc854308b6fc5faefbc99",
          "4926a90e00fd4c655276af101aa7a27bc446847eb89d74f2662b1d18063b1b16",
          "49e9411b14f054960bcb14b9ec7d826f87a84daab73eec3540615c3e4944f577",
          "4b00f8df9ba3132af84ec18ebf3d370ab23175a08d178bc44d28fcaea5ef8beb",
          "4b10af0ab9fa379926ecb08a8a6a9b04898e9cb88dbc59f7d41c078626b5e36c",
          "4bcaca67c5d870af95f3d0968fb686b1bc90dc134867ce303abd0387bce92895",
          "4c068b86aa33cebfc1f886c5c2e6dce2ad74ffee6affd76838274afb77523e09",
          "4ce1e927850e540191b28d4bc1731f7137a13275ff81f94e5152b078d8c334ae",
          "4d4ec00fa94a66db256aa8ed1d2539ec0e154ef761e677bcb818d82cb3ad625b",
          "4d551581cfe2338168eed493445c3a9e4ba783fe5116166fbff5a027945e7893",
          "4f282358ecb3aae0fe7794566d97408e59314b930082a39a55bbfd03a03b4890",
          "4f8f1006e93a36e43be7f9ea59a51580f4515df45ea368d49c34fb590574d8a2",
          "503df63c06e6f0fceb602df23d13afe14dc939d36539f2d09de3462422afb2b0",
          "504ba3ef7b4b3a8682523475773506741afcf7102431830e88c7614db78e3978",
          "508831601517b543a38e1fb4e6a117c07670e5ff0475267b6ae1e4d73638576f",
          "54a125eb6a82938cc602587fae48a752e381b2378204f0221953c4e08985e493",
          "54ebb23ed52a09335b39641fa38f8723912f94bd9ff02574e84db8ef5be5ea7c",
          "593585723059315bd94fa8e1ece653278448b30e895bc422db5053f6e32e072f",
          "5a96f28f1b659e5a64275d55556af46ac50b29665867a8cfdab6271f91033647",
          "5bc22664f305bce7a64817228a5709e10b7ee8e5ace0317cc25f9be077a30845",
          "5befc3caff3185df73b86e5e1eebbf7340dec471d6d20835d35bc613a339485a",
          "5c2f9712778817c6b51d2950e006eea89ce75c6f1bc359ec69e953d987e85e8d",
          "5d651384e238dc4f6cf0e513472d1a7f8a66f740b2bca790f59a4e20f51e930b",
          "5e5eea45bbb3754c9ed8f2a6391dfc117793be524652abc9ae7209c58136facb",
          "5e7b861bb3071e449b40ebb37bb1aa951c708463560930fdfd1a86ba954125fa",
          "5f0008d0e232193367262859dc84095c807c90c329df039a69158f1f1ddbdf39",
          "5f2d8dcdd11e30d3e28a8d0c948af46aaceef4a0e7ad0bce23a1ad1a7362b4db",
          "5f393a7efdff36c497db1e1e684d9260ed2db2d8e67744c568a14fc3b1dff275",
          "5f9dad92b2e0d92482c2bd89290a9a62f90b84052a0affd91f9322ec7d0fd7c6",
          "628f685e8bc4c7c9e71b90393fdcf2b47ecccdda384867c82d15084685fdcff0",
          "633cc7fcd3af4651517aa3f36f5105d6ffc4852551a981dae6e40e7dce6bc69e",
          "657c4a837c27bb2f34ddf32dac2aafe37c6ac936b8ab68218e8683871d43c4bd",
          "673d1165a3b0c75a375ac3352d19d3a0150ecb412a992325d4de93ceadb51341",
          "67e83384b9253a2e0eff15b7fca9f0241f9d9c0253dc3cd4de2e9971386a6db0",
          "68ae8a85320ff442b00d94dfddd1c232a861cca9cabc256c1f5cee3d6ef5c5e9",
          "6a0ce038e9af4656ff0dd3ad3327ea6ef52b4e9481990fd8217a2d0899d6a4f8",
          "6adea6352b66a3d4922961c5f3f91c931b6598f84483de80567aff82029a8586",
          "6d2703d47b9e40e03d0da0294dba0ffe38f1fe15ff266525cef83f030010833e",
          "6f12a062cfcb9497a36b3258ccefb4d540af8e303710be114549ea720a5eb6f6",
          "7270b4a28ba9b7113e8a178a7f31b71bc2f76274c6279dec6a80a483b28c6762",
          "7299b2470e85c07bead7e0472fa737f7c04821d666a10f261a391eedcacf6cfc",
          "72b17ab9e8f7c455499c9ff7b7e2118b78020ded82d1efb6e665bf506be639e7",
          "7348af56ad795e540d150ebc614dad65b55c77e7023ff2ef640f8ce3fc275e8a",
          "73833aefa6eb8caf654148f0ce685a0a021c474577ef7c7134a3b5194705f480",
          "73d2364d0131077ca702a68cec253af0edbeb9ee4fded97739b077d94da2cc49",
          "7446c6b053472aff2930aa79a78d98b7bf5db25453de9048b9f455d2aa18138e",
          "74919f9109f50c490094b9fe70566d775aa3ea292eb0945a4f4b47edb73e7398",
          "7540d25c28e2d52c46503645d63b0850244d6aa203a8383e05a9abde5c30d1f0",
          "76582fa02353655f0d1c1139b9b51fe1606f7d19d51f3fb0cba33aff3f1cd4b7",
          "765e9484c556a22f49f969e3ca8593ab56d4578851f774f80da069df7ee43ce4",
          "76b66b6a2102d83aa670d2b95df6c995163cdec4256a0cb781aa9b4600293ab4",
          "779bdf13f127b8d33c66677369eaa51a8146886c6cac9de74c23cbb63a0a7b81",
          "780b275dba9051c51f45246b69614e6287f4566c3bc03655a1099c240ee81041",
          "788ad084181fa988848164f1829e7b5b27e95e763f81c117ce086770534ba4a4",
          "78e421f67f158ab7545ea19ba44aa1e1c0bd557539201bb60b61df562fa87525",
          "79dcc54e5fee67b5a09df7928b2b4cf2d672f04e2236ee834abed28df46bee4e",
          "7a311aab27e9aeef0934a1e37021060a03301a372f8b7e0f15a9c221a0c43142",
          "7a61e6b9cd855a55ef758bc2210d41e187d628f84c7b27b9948b72100b88dbd1",
          "7adb5cfe4f2bc2f585926ba5d4f1584104a7cd9a7fa090417349b840d23f888c",
          "7aec180152c440d141be264590696a3029664b0f3fc2bb7bfc7f0a26911b909b",
          "7b94538fcff886b1076c17db4571c049afe429016d523d89aa40ef7c21557fb7",
          "7c3e8979b7368450f6e798e7d4b3ead8f08bdfb01757dade4e1754c54803167c",
          "7c45ca6b0f28ae30284a8277234c2fbfc8d21e71543bf11e773ea7590fe77a16",
          "7c6b14e7a36b7f1021a86f1282f4729b128d9f7d61f08dbfd9bbc1017ffd3a81",
          "81d45e548911e58862cf5e755495a3dc2899d00b673e57bc74080cdc9f389a35",
          "81ea0a4b15e68a1bec78744a75d6a89bd7b6dadd7db49f8f8a96725d8812f8be",
          "822f610bd7e30668b29f91fc0c91ea6b8f63a5b3f27a0b5ad0e2e071dab8062c",
          "84e2b5659857f7f5f454e596132fe8d19a7eacc0992394d3a2f322217a608d5b",
          "86536a32e46a0e2aaff32c975a2c336931cee4f233172e29b4ab0c0e57d2ef53",
          "882c9748528e10535b77169e75695e394494c216300944c0b613c5ede915c157",
          "886341a27a1bd7ed45df51acdf06fe0bc0a1f7555d425110e2fbeb137166878e",
          "893ee729f3007a1b545122d769e7d61a2f389745b24e0f67c85dbf2bf9b79b5c",
          "89bca230cdb98dc540895f8d6303c4458ca17c9fdfc084da72566e26fb7f444a",
          "8ae36d62177f10fe3666c96a752a0ff4d1cd46d46253f499d1c68f3d1e007e44",
          "8aeb79b70176bc55a5b52a6198b4fece6031ca97ebdc1b5e914556799ef01cfe",
          "8b1ca9ec87a64a8c40c7682a9179789a3974aa1ab7414c0661155ba13761409c",
          "8b824492957f9a98f1d27d1c64d028c31da7d256aba2cfed34e837936cacf99f",
          "8c0b95bc9f825fd2df665468216139566eff5c7a002ee345a35c0bd8a1ecc8b3",
          "8e80a324fb462d50c2e86c42d453476054d42f7a4c5cdc400d00c8effc101dec",
          "8ef8cda50859c3aaa4ff9d6315ff3bdeba716eacc5e448e1e812d76c6bc183ae",
          "8fd78112f356ee7e9b977fdae32fe4287bf2266baa191f17b60402609629b14a",
          "91ead3cd8f60e41791a19353223dcb61ca996b6613e11bc6bd08db571f7c6be7",
          "93498ae965109d4dd77fe90df722e19890cc054ad0d52a748be6b429346fea42",
          "950087b85607116920dbfc46a69a60135e101625a27cd9489a01d1086efa618c",
          "9583fa4ff4858e7eb7b34b5081aeaacc2368674d38b6ada2a4e827640d21966a",
          "97ca9b3c7e820d7a0daabe3ba921e1190f2516a0e58c9c5560f11b4bca8dcf61",
          "97cddbbf055888b01fd8338f7e1b8c6589019eb15223bbb00b215f9a891a1b78",
          "98feb69ecb32d40e0de282bcc12808b807b2c3356407b3417eacbf84ef4e193b",
          "9b1600802a2a36fc102cc4059009c9fdd69b06492e3a777e0769a19684161795",
          "9b4a523020fc83bf3d0cb96bf8fcf3094598013ce84c57d4bf663ff8daa92578",
          "9dae0b166dc84a0d0aacf525358dfa23aae64d57a9135ddc11c0e3e6493c7b02",
          "9ecef8b1a2e38343b1a30b845ca647c63b8eaf9aae9e7b5d9038916d1458d5f5",
          "9f609adad7e840c41c1ea1dafb431c680a4b941d83b9b179e1fa1fe56a6578d7",
          "a0fefe7eb3ba6fc7ecb1e94a160f3b22bb8ed797147491c4c1bbc13010947b32",
          "a1596254c92cab06db27925543e8595477ab606d9b2f482d015365ec3dad27da",
          "a184174f9b4cb6defd5056940d0dea1771d134c30bc38c648f6546988361834f",
          "a26148ecfdc920fa9f92c439abcd1039ab5e4507171bf64edaedbb33243f0a6e",
          "a295769ce219e2c13733406ee1ab5ed373d3b43e17d50eaac35a490e1f88d904",
          "a29d2a799245b9f8756a394c80aa5ce8e70c3013387d01ed8a166c98563ee752",
          "a41880d3546ebc3438f4c0c47f90ac59dcb0db1d8f9853ea74d9797912ac9b8f",
          "a4660e1d6e6f06cfb4e9294de73043ddf176b7374154c32a75700de46690fd05",
          "a515fc5f05e4cc898596d09bfcec7a04e8329dd88d1b9c1672af0f2f89b05028",
          "a5e45951530bea99fcafc8ff4b4fd7aec2a74976a68cbad1b893c678b03a7760",
          "a60523993af86ec3fd931559b48cd613615bb867a67ca0951ed1198ef47eb071",
          "a60b89f81890c90112acdef58c39c5dfe3a4b4540fc0d7bcd24bbd24eb76ce1c",
          "a63469758ce85ad85b158f71aa0747528b76bce9b7ebfa151de3178922afe4bf",
          "a6c25585e3105bef0c4caeff9d031096f45499208ea2157d309e93b2a3006843",
          "a7f1f3b0d91c595e9d81b7d9ebff9e3519786fb0741a9e1ea864082ffb403761",
          "ab65f39ea9ed34d354add351a3e2438eed0de981cea066df16f61177781d3af7",
          "ab97a8c1069d8d1534a2b67de2130d22beffe35ed05ae8622f74872b660561c7",
          "adb82ff3f518ceabc89ef6cb11f687fab7ba6021916156c750e9cb5c62bda514",
          "ae0f0497f2e2e1214640f2cd8a45ba5a19bb04a39ee6d4499d8a233050168cde",
          "ae8cc7dbf4144a080aac358c28f1182737259f8382630100cc02a06d8df77927",
          "af07055d66349ced4c7431c3bc55b7e3303efbeb772153b5e55b876644e39838",
          "af93d7b75999aeb63b92d65e5f8ddc7daaf8abfae0dac843399a35127303dd64",
          "b19c85f3caa7e8e7140ef87ea0c19d7f2d6c4e2b5f64c07ce730728b8f17238a",
          "b1df42ad58bef15516a2e57540484228282492602b0646319a1f2bde0799e108",
          "b3dad8a37866e2f7d60410d818e06de9d8e4dbbd5d97aa7057a5da561de59134",
          "b40262d8f849f7b1f147d8749cffd0c32e5d48e0d6c5c6bf1fdafbe83e8aacfd",
          "b58de935e101201bfc1350f333936ffbc9de545a063e11cb8ef6afdb98c92272",
          "b6bc791f03d349937dcd3e6bc539fdc4107e40001bb4b4bb120835c973c960c6",
          "b7cb71ce65305f9403b4ba934b7cda238a0c69e4d4f4c18e9a3589e031fb3239",
          "b7f25ee4e778d51348b3821b5468ef6ae377c06fb5925974e61fdef2cb8d5836",
          "b81c900a1d6bff58610b85a4d5d00f603815e908de909cfb3bff52a07bcf3948",
          "b83cb398c3b13d0c54ea9b090b68c8391305f2f944c346afef58d431f2e1faf8",
          "b8f97a781f7bac790dddbfbce6e969484f57b31a41fc0335ebc350c9f362eb1c",
          "b99e160d488dfd95e6e169672b825b58ffa0d382b700cf32868af464c5904f19",
          "b9f809cff4f8cd231f9d79bac0c58dfd7c748a2539cb070051faef7bfb15c2a4",
          "bab918b63853c1da0f0796b6078b5249ad2a37122942ae1aa7d1ac6c06cd8b73",
          "bc3a370ad58a53693f6e2e32badbea411218464cb339bb93d07206b609a8a601",
          "bcbe9777f48526838ab8f951571ac8eaf97a1bb9d9fe31f1795633dea0270b6a",
          "bd43be7fb745d3091761ec97647df27bddf63c28007642d1100d577a5139ab81",
          "bed88db7b12d7699a21ae9536153ee7c28d72b89e3195f59477d3f802f52cdea",
          "c0f6048fac76efbb755897c8af60a46bb746d84a2ee2c54cdc2034f451263e83",
          "c218dc6ded18adee2509c82db335f1a1e8008e86a6827950155ec6b7c3ed68bb",
          "c36a56df700e328eeb5133c591c51628b71f2ec59d0598665f4055da22e541d4",
          "c41169ef586ff986b5220386ff08fbf07d1e8e62ab429d631093a6dc637e9e3d",
          "c439582c80056cff1002ea2a307eb0f28ad3b35618fd93fdef16584e216e3804",
          "c4ff6337f1bc14712defb1cea78abb4224b12175a443eced18c96f71585cdc11",
          "c6526002a665a7ed1e7611729be0aee4757f407bcdf2b471966de3e8d1e6706a",
          "c6a5df641664e6db2951ee4683eb67ca2bd192f19ad3dc1c84d6e9110715b0bc",
          "c7c177d6195e774c9adc1e13b264acc753912abb44980cdddd8faec3afa6d77b",
          "c7c1e308f675366f98fe2855d8914a048c1b3f06aaa22c5b932e735112893cc6",
          "c7c8bbbbcfa1cfac3851e8c0d3475c25d323d73cd03268b36fb987dd1f35737c",
          "c9b3e10f4b8fc516802078655b642ce49feeb597f9f6c597aa319873d023d3fa",
          "caf5fcdd0747295444c48341bc8133a9ea524a289ff11e10736fbf949a1a281a",
          "cb37c4e80da6302631b1999b2d256b470396c995d760ce7b7974cb45019a7bd3",
          "cbc6cb0b07b8b73b71368f1ab6e8e9d6a46fef06a1598c17eefea877056cd6f9",
          "cbc98dc5ed8cd31fa4736a006fce7844b025baf73cbd8ccddaf2a99376ebdabe",
          "cc61e49b5a06a791b2fa7c8287204ae3d961fce36ab4280e22c566ddc73885ce",
          "cce567fdc6c222c600097dbd2397881ba950e1572c71c1a75801512f16d84d78",
          "cce7fd0b3d3e9ae8288510d20ea735bfe2c0c0fffeed0db9b2d2484846f34e3b",
          "cd98a4557485ad02289d59c81cc1471a65b0e23e598cc0a90df4169be4dce8c5",
          "ce60b0c1bcbb2f1abfc54c5bdb60e9cd4fa3656eaabd44080af056a6e89c7540",
          "cfc502ff967250eee82b22947d93f5b65957b2d2a75527e09d61d1ccfee1baa7",
          "d3a94c41169a8a8cf11287eb68024acb8425ed8da22ad35a3a9877bc903dab3c",
          "d3dfc273dd3559f792141ad131b75e2a8871bb94063381954aac089aa48d3081",
          "d48b6a5bb778857b50e0dac08ed317a4d4460f97f31faea8b81ec1d0757dce25",
          "d5862fd3278342a4ed5b869664fcb38c8468834bbc08b0e67970dc9152234a4f",
          "d6277b55d67d24bbcabee466565984683afd6108eb5b637df4b617382bc221cc",
          "da8f0e64804501bb820afd26e225ddfb06c0f43ad898a0482e2a0852da415ef5",
          "db52e9e3e47bd5db1765c3bdd018217d9f975a2a22f5d96b08dd36017cf3f233",
          "db57dabfd78e8c158881cb17355098624f63d9558581fd82762ec4ecf932ab08",
          "dcab9b0b5e2cd856b204fb45361bc3f338fb0fdba06a354baaa2762ca95a8ceb",
          "dd4ecf60730e8467005b797e1b40ddba1b6ea7e79edb715209b4c83c98e69144",
          "dd9ca25d6be04f6869b98b73fd25e8da60b1fdb353c9cde0158a1f72aea7083a",
          "de65160719848918e6b24ec9172371309fd74f9a9e7497316568f77d581abe51",
          "df38998da62acf901233b4efee531ed8c24be808dc96b759c088a924e2fe28fb",
          "e2180b190d70faa74fca66f6e3f84182aa22fb66bb9e2a4c7639a942c32b6c6d",
          "e29e9df3203f76510b4ea2cf47a484a099a9fd0b136ab08dad78faf19311be68",
          "e2e9303c7b2d5f0626c152c676f0bb3d42a90ac8de49028d8bfb56e9499106f4",
          "e39f0c1f039a65809449b2193abdde7cf692d2fab35627be35e041e1fdc157aa",
          "e3ab991d15adce9f51ed5d2c7e612c640083ccd98e2545b7bb47c493e516abf1",
          "e63099e7b6757fe5d586ab283729032a7e2a051794b55517d4dd6b26758e7727",
          "e7981f4889ce9bcbd1c098dbd672a1768bbab8780ff5ebe2aff6e8c5b3c6f5ea",
          "e9b766603ac408f68a07279bdf535f7fe8dacbd98836eb9f20d86debc2a9a150",
          "ea54cf79bb3f81f65bdf0c426c11ab8968db1c16eb2fc76e8cade686999eab1d",
          "eb9cf52086f1f5a60df55993ecb63e06ce1db99e371e878b607c6399cb5412ca",
          "ebf9b8961ba950a3e6ef778b1579deb18b679d53493028c61d20e1f173676566",
          "ec58b8ee4431296c9ead69ccfe57d9d1222e3db74b8afc07934b4ffbd7bcc93e",
          "ec5ab9e4e7011e27ea2e69a70b98497fec996d0c0363b408f9dba54fb6442ab9",
          "ee1a3ec668115a84528bfb43cab70025aa9d077a97059bd5c222e9f0ba2b59f7",
          "ee768b442b7a3f686caf29f10dc25d2c1387e9e3f7948156f7242c9eb59a5824",
          "ef94117562adaf005d5a3aa6c4981bc29b0fce01f861dc9196128698eeaf8530",
          "efb892c665e8fe26857553076b528c1f9d78729cc1b43ca0ab87562f867cdd6a",
          "f0ce669d5e5c05a4e01a37e1ccdbeab7a2a540f5c2eed31c5c6c6ff11d5410fd",
          "f40329857784d7b2f3ea6e750db8211a0aa0dd1e6d7f4beb174b070f0dd2d29f",
          "f478e2bd22fa25749f26f1d21614c86546196d9e792871b0a332ac4ec414ea9b",
          "f69484aab1cadff6f01baa49521f39986a5f9388fe4a4a325ea98f6791200a1a",
          "f74c1c2ebbd12186aae6c6210a506970c32cfe45fd200ded9acea4a8ef3663d5",
          "f8217203dfc731bf5e13a232629e9816f2da29762c6f8ba2ce1898be55017a58",
          "f8882f727e257f144e944a117bb48d89cc2f51bc4caf4feb369835b118dbd3c1",
          "f965a3c613825034aa114f1f1e345b1bea14799f841f5bfe81b28028422d96e5",
          "f9b024e2539e7fb2a5a3029ebb941a3613ccbdc44c383f97c9f95f73a67cf510",
          "fb5f6540286e2b09b1072508a75d7ce59617a3744fdd4484b5a6221b975e0d97",
          "fc2e018a68a8d738a4a5c24451e783168bbcaa2be8fa91b2d20d365d8a386d0a",
          "fd688243ebd3bcda50c0c360532d2d73034c21d8783c29d55e222e5d3f60aa23",
          "fd7e274f70139443c39ea77ebff1f97d29db37e5f278c495a0b6ae085e5e5a07",
          "fd7e41a168a1a22bf9d1eea93b785f988e755f65f7e2387f1ebe88452798b719",
          "ffcb7df5ea54f35047d9f927f3b1e75c52bce40978a0cacbce5fc3576f5a1069"
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
        "first_real_error": "Error-[IND] Identifier not declared",
        "log_tail": "/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n                         Chronologic VCS (TM)\n         Version S-2021.09_Full64 -- Fri Sep  4 13:40:01 2026\n\n                    Copyright (c) 1991 - 2021 Synopsys, Inc.\n   This software and the associated documentation are proprietary to Synopsys,\n Inc. This software may only be used in accordance with the terms and conditions\n of a written license agreement with Synopsys, Inc. All other use, reproduction,\n   or distribution of this software is strictly prohibited.  Licensed Products\n     communicate with Synopsys servers for the purpose of providing software\n    updates, detecting software piracy and verifying that customers are using\n    Licensed Products in conformity with the applicable License Key for such\n  Licensed Products. Synopsys will use information gathered in connection with\n    this process to deliver software updates and pursue software pirates and\n                                   infringers.\n\n Inclusivity & Diversity - Visit SolvNetPlus to read the \"Synopsys Statement on\n            Inclusivity and Diversity\" (Refer to article 000036315 at\n                        https://solvnetplus.synopsys.com)\n\nsh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nParsing design file '../sources/Activation.sv'\nParsing design file '../sources/AddRawFN.sv'\nParsing design file '../sources/AddRecFN.sv'\nParsing design file '../sources/AttentionGQA.sv'\nParsing design file '../sources/CompareRecFN.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_1.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_2.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_3.sv'\nParsing design file '../sources/ConnectedCanonicalWordPacker_5.sv'\nParsing design file '../sources/ConnectedObservableLlamaStyleBlock.sv'\nParsing design file '../sources/ConnectedStreamIngress.sv'\nParsing design file '../sources/ConnectedWeightLoader.sv'\nParsing design file '../sources/DivSqrtRawFN_small_e8_s24.sv'\nParsing design file '../sources/DivSqrtRecFMToRaw_small_e8_s24.sv'\nParsing design file '../sources/DivSqrtRecFM_small_e8_s24.sv'\nParsing design file '../sources/ElementwiseMul.sv'\nParsing design file '../sources/GatedMLP.sv'\nParsing design file '../sources/INToRecFN_i25_e8_s24.sv'\nParsing design file '../sources/INToRecFN_i36_e8_s24.sv'\nParsing design file '../sources/Linear.sv'\nParsing design file '../sources/Linear_1.sv'\nParsing design file '../sources/Linear_2.sv'\nParsing design file '../sources/Linear_3.sv'\nParsing design file '../sources/Linear_4.sv'\nParsing design file '../sources/MulFullRawFN.sv'\nParsing design file '../sources/MulRawFN.sv'\nParsing design file '../sources/MulRecFN.sv'\nParsing design file '../sources/QKVProjection.sv'\nParsing design file '../sources/Queue113_StreamBeat.sv'\nParsing design file '../sources/Queue1792_StreamBeat.sv'\nParsing design file '../sources/Queue2_StreamBeat.sv'\nParsing design file '../sources/Queue2_StreamBeat_1.sv'\nParsing design file '../sources/Queue4_StreamBeat.sv'\nParsing design file '../sources/Queue4_StreamBeat_2.sv'\nParsing design file '../sources/RMSNorm.sv'\nParsing design file '../sources/RecFNToIN_e8_s24_i16.sv'\nParsing design file '../sources/RecFNToRecFN.sv'\nParsing design file '../sources/RecFNToRecFN_8.sv'\nParsing design file '../sources/ResidualAdd.sv'\nParsing design file '../sources/RoPE.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie5_is11_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie6_is25_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie7_is36_oe8_os24.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is24_oe5_os11.sv'\nParsing design file '../sources/RoundAnyRawFNToRecFN_ie8_is26_oe8_os24.sv'\nParsing design file '../sources/RoundRawFNToRecFN_e8_s24.sv'\nParsing design file '../sources/SingleLayerSemanticHarness.sv'\nParsing design file '../sources/Softmax.sv'\nParsing design file '../sources/VectorNorm.sv'\nParsing design file '../sources/expTable_2048x26.sv'\nParsing design file '../sources/ram_113x269.sv'\nParsing design file '../sources/ram_1792x269.sv'\nParsing design file '../sources/ram_2x144.sv'\nParsing design file '../sources/ram_2x269.sv'\nParsing design file '../sources/ram_4x144.sv'\nParsing design file '../sources/sigmoidTable_129x19.sv'\nParsing design file '../sources/ConnectedObservableLlamaStyleBlock_Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nParsing included file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assert.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Assume.sv'.\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'\nParsing included file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'.\nBack to file '../sources/layers-SingleLayerSemanticHarness-Verification-Cover.sv'.\nParsing design file '../sources/layers-ConnectedObservableLlamaStyleBlock-Verification.sv'\nParsing design file '../sources/layers-SingleLayerSemanticHarness-Verification.sv'\nParsing design file '../sources/app_shell_9p_cnn_core_0_1.v'\nParsing design file '../sources/spatialacc_exact_board_multilayer_tb.sv'\n\nError-[IND] Identifier not declared\n../sources/spatialacc_exact_board_multilayer_tb.sv, 2578\n  Identifier 'ACTIVATION_AXI_BEATS_PER_TOKEN' has not been declared yet. If \n  this error is not expected, please check if you have set `default_nettype to\n  none.\n  \n\nParsing design file '../sources/spatialacc_axi_protocol_monitor.sv'\n1 error\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nCPU time: 15.235 seconds to compile\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
        "must_rerun": [
          "case_vcs_functional_sim",
          "case_vcs_evidence_analyzer"
        ],
        "next_stage": "repair",
        "related_source_ids": [
          "certified_kernel.0000.793c663cab4c2493",
          "certified_kernel.0001.b6e7401e9ba54fe7",
          "certified_kernel.0002.e30b913a4fcbf712",
          "certified_kernel.0003.ce2ed5a48d6925e4",
          "certified_kernel.0004.814f90c0d54776d0",
          "certified_kernel.0005.549dfbf4d406e113",
          "certified_kernel.0006.02ed8639f6abfaa9",
          "certified_kernel.0007.0e59ca9664473372",
          "certified_kernel.0008.f3881db839805370",
          "certified_kernel.0009.c7867a9c5dc80117",
          "certified_kernel.0010.7403a7f048b7838a",
          "certified_kernel.0011.586749abab288c0a",
          "certified_kernel.0012.31c41e3b52b51e0e",
          "certified_kernel.0013.36544e04d9b73705",
          "certified_kernel.0014.e7082c31ca17c857",
          "certified_kernel.0015.d6c5273532b22e2e",
          "certified_kernel.0016.77cabc8da0382228",
          "certified_kernel.0017.2b227d4de39b8fad",
          "certified_kernel.0018.8ecf314ffd508688",
          "certified_kernel.0019.38e37b277c02a765",
          "certified_kernel.0020.9912819dd3fae37e",
          "certified_kernel.0021.c7f97e407c087a90",
          "certified_kernel.0022.6d8306c120a79038",
          "certified_kernel.0023.85be27c74f6523cb",
          "certified_kernel.0024.0c835c2614fb651a",
          "certified_kernel.0025.36d990d3717ff7a0",
          "certified_kernel.0026.4649532c4e1e62ea",
          "certified_kernel.0027.14615abf8650a1fe",
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
          "artifact_sha256": "0c734734b891dfb00355f84a3a7a59774c173f313b4ebe7579830b78dcc82139",
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
                "simulation.dynamic_evidence_records[1] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
                "simulation.dynamic_evidence_records[2] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/progress_event_log.jsonl",
                "simulation.dynamic_evidence_records[3] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
                "simulation.dynamic_evidence_records[4] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/runtime_loader_report.json",
                "simulation.dynamic_evidence_records[5] artifact is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/axi_protocol_report.json"
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
                "simulation.runtime_loader_results.layers[1] is missing",
                "simulation.runtime_loader_results.layers[2] is missing",
                "simulation.runtime_loader_results.layers[3] is missing",
                "simulation.runtime_loader_results.layers[4] is missing",
                "simulation.runtime_loader_results.layers[5] is missing",
                "simulation.runtime_loader_results.layers[6] is missing",
                "simulation.runtime_loader_results.layers[7] is missing",
                "simulation.runtime_loader_results.layers[8] is missing",
                "simulation.runtime_loader_results.layers[9] is missing",
                "simulation.runtime_loader_results.layers[10] is missing",
                "simulation.runtime_loader_results.layers[11] is missing",
                "simulation.runtime_loader_results.layers[12] is missing",
                "simulation.runtime_loader_results.layers[13] is missing",
                "simulation.runtime_loader_results.layers[14] is missing",
                "simulation.runtime_loader_results.layers[15] is missing",
                "simulation.runtime_loader_results.layers[16] is missing",
                "simulation.runtime_loader_results.layers[17] is missing",
                "simulation.runtime_loader_results.layers[18] is missing",
                "simulation.runtime_loader_results.layers[19] is missing",
                "simulation.runtime_loader_results.layers[20] is missing",
                "simulation.runtime_loader_results.layers[21] is missing",
                "simulation.runtime_loader_results.layers[22] is missing",
                "simulation.runtime_loader_results.layers[23] is missing",
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
          "00b8f989c23bf94a55af6a62745731b51431dbe0a6f0f3772606a558b266a46a",
          "0124f2b929672c802bdc1322ff5c90c3bfb9a9ea40f4abac6f269f9f08ae137a",
          "0179c720566efb6ec86df085d04bfc780891e437592975d8e28c06a01cb9e0e8",
          "01c0dae0fdd06200a18e5b9991fb22ce96eac74c4976598e7ef8d49266cfe619",
          "02061e3683742bc0151134c4bfe46e4e0e4b36efa2f6d336fc8dddc8fd8bd635",
          "0209b3fda843d0be42900fe58fbd4d49df8539f10f55907ab9adf440ff6bb498",
          "024578a764476fa46c5e60265095f655f0cc65ddc82750a1918f7af2e5d90413",
          "0345185fd11b1818dfe5e6e4dcd6f23113a32fab70409bcc34588b2593117530",
          "0398c41adf8fa9c8a1bc757216612bf2ec50a5e0d1882717fd85eb309035ab0a",
          "045c6cd32c96ea0041025a6e746bdaf0cd5dc60f302a026e7b11e1f0df282f81",
          "04b03173f20a48285638cbacb9d2f30fb778c766f99e9dc3b8f7f196d2c121fc",
          "0626fd310bf61f4d14eab176d124a88f7810032e6814c3fe2604af03986c9270",
          "07c9d7c21eb480569babfc4e60e48055056844aad4dae587202427826dc116f7",
          "0836ce4568d43b91720aeec77c5c3cf5da973402c3a594d5d4e7e78f3f1b456b",
          "08f3438e1d7046e1ca763c9f9101a5c9d267a476d479f56ac2339916e1df8225",
          "091d2981a666699d6f48c23946e2d5e4f100b16174c75efb89d23b7dfe842bf1",
          "0abf7d122d6b86639abb9fd4959e1ff71cf8bdce341ef2eae9bfa81d9b889c95",
          "0af69214964204bcb46ac4bc8714b38682df5cb52c442197b0c44e5fa7c176e5",
          "0c811d068c4535b8ee8d5098d1a576cd57139e285c3af8d4bacf2680210c5b52",
          "0d09d8a07e58c70c1afcdf8ff77326db4ebe4e7356c56d2c4f39d016d24109ff",
          "0d0c2e986b79337c0af626b4696e2c5bfdbfea3ae899aad066b1224706b7e875",
          "0d9a7d0849ef52a844e49d7d5b5bb7882c3a6cacb4393ed8635ee8edbae2ee90",
          "0ed64ab14304fa3264d818007c8dae90fcbb0c6abc090c354bdba82e164cbc23",
          "0ee8b903526f560c1934b92cbf2976d6b07c750e0eb327fb5fd8bcd3ec27b9c5",
          "1131e30699fbaba9e392894aa9deb7afd790f172c8363f48207ad2f19aa13177",
          "119a498fe1b98488cf145914025198583b4e8717602f392989b8ffcae3234cf5",
          "13d57fec399ae74a7a44c1a545de166705d11f511dd7dfe33fd58316b8cf737e",
          "1541d3f2080089624a3b32babc9cd27178d18bb9b3b9e128d7ff28c55a2de8d1",
          "15d1132dffd54e362485d225d6a40e6193c412a930a93b57815097e752a8f0a1",
          "1610dd561ae03b13a4fd758d9e2ba5b1d52131144041a38d3dcac9a7be94df29",
          "1737eabd8fdf744885b74f99dee50926be20963b7030f1963da37f7906b06619",
          "17a2860fe1d997e08bd88ea8e979a16bc7fcb8258edbca17558925a212fbe6d5",
          "1921a2d5bf9e6daa33c6030c52f132c9f8f5ee18527b762a98fcaa442a2b3fc6",
          "197a44cc486cfa1b8753e8027ede352db839d80fbf7fae5add0ef9f0f3b6ba2a",
          "1a00b42e429cd9cb90bbe25dd2649f0f8b2b0f3ab0435f05eda15d55912083b0",
          "1a698b69dfb8f87752eca0d95d2e8727db0b99d79dca955a95b79578d3e9e00d",
          "1b102cf40a35e4c5ccd49bee2d1da9cb7a14bade57f6f6253ac6c53b149e954d",
          "1b8fc11b559a4933f6ab70a022163e58dd3e42083f56de6c1ccbf4b32bdc7d0d",
          "1bd7aaa1aa43ebfb1fa3ae1b19a0e9fa2a17c7fb223d993e81dbdecc16a5ac5b",
          "1decc3dd0897c9a113d1e86b106eb5ab7a07502c411229ff8bd0b83ddbdc0175",
          "1e2831c122eb62745700cf81e30dd61e5e45598979f648c83e4064a18cadefde",
          "1e7d59ab3675143dafe924bc9a468e2cca0b77ca28f502059a0e17bd9aaa26a2",
          "1f2ca270874299297f9ee4f4082f59520cff15c291ad3c17b7cc0264b378d315",
          "1fb9fda61dbaaeaa7f69ac5bca11cc5b3998264adead65c8af82ab53a620f545",
          "1ff9e60ba643bb1beff31f0e1c352400335f07db20919c9fc44a081ffb24146b",
          "1ffa1a455563fdd99c5e7e65ccff30afe8dd464c2b6f2d39e537a371bcb024d7",
          "1ffa4e9fb661c5f46a63bf97d4e72b6f846897ed90518e15a92a1bbe1283bec9",
          "20f069f21809f8efd97121d72e21c62a0a605de0f7e1aa72fccb6e4405f03173",
          "2322e74d06def44377e70cdc4e55a8e288d581f9ed3f7364582972ead81a133c",
          "242d0ba5f68dd1c380ec270558f56b9259cfa8c64eda0eaf9172d218f136d3f9",
          "256ebf62b7b97a90ccc9bd443559e7ac38e80e5f01d01f3c9a706d7489422661",
          "262752e9ca19e527941e488e8602f3e8185f060f40a8c550fc6f544fdda84721",
          "2736051bc5ead9abf8d200f6f4c4b164a1d5ac1bd04560b0e495f7e52e4d1f0a",
          "283f65732ee4b3aff22a13913701d530ee43f34da448dece512e958f68d2c234",
          "287afd359de170598bb9f43f3036e8cc281f3cc88aae3050aa95f9b21a20b6a5",
          "2a50b9897b95ab438ab7415d4f45518ba007dc53a4f5fa36b7ea310dc19cbce5",
          "2ac752e961cf6966c2206f8e60b29f395ddbd86fe467be619e0c8466152e632e",
          "2aed51f9c0c64581ca0a4bafdc208a86320bbb8b397274abb1b825ba0c87c3cd",
          "2bbf50df5749f22374d855bce9ee7f22bd3a9fd15b79ef6453fa85034de30716",
          "2d5434ce8ec904191b4ba128bb81da443efae53d0c6bb3095fb3d0bdb562d84d",
          "2e938fa28a213e9ed4fa6a30d9b5df258ca6f4a90552584b64525b9abfcfa03b",
          "30ac399e735534fd8c9487b2f254efbf53d7ab03db18ec2960f4d9c520332c71",
          "328c77f4522c0989b6524606255778d1499039cda005a03749dcff7ff2b42e07",
          "336095cd67196d54898f48e96ca324a2a762390c5d02592d3f12397277f06b36",
          "33b3c029d36bad5cd0b87282a093badb88b6114d781404c43e6c83c374947458",
          "346eda969599f584be47a7cd73af5301d39717def5fa43cbfff407297fbc78d9",
          "356ad673958c64f61fb0554044a316a40cdcf15c5532df5fe8a433243461f781",
          "35715ffde9ddff0945982622c4e035214a8716048e291e3ccf94de8015f10e48",
          "358f5765420b07a66d3e1ddccc210d73ac1731000e1fe60f30e711aa88f0ce6a",
          "38d6356bea686b676e69a0f79234c65f4f43fb65d4b6d9abd927d6048ee3d43e",
          "39640d57143079e39d21cc119b11204231a20816aaf55ae410bf00bf2e3cbc8a",
          "3a5109104cc76c897c9ae89e5c66d09dd05836f14a24f03280cd6e972a8db92f",
          "3a56f563486166261373302094ce6428e79159caa89b9f9ca4e80791263deed3",
          "3ae517f12c305b425f14356d96d6be262e2f869655555f7634e8fab50a581476",
          "3bda6ffa2249e33dc69266ba5e29dff70cc86bd37e354d98f7a0db759f854f1d",
          "3c12f111214fea28c2ae1539490616a3106294ee5eb72f5cdcca6aa8c1efabdd",
          "3d3fa3fd741314f77833fd5bb1e717327f99153473978d772811d8ab95810b40",
          "3eb99408afcd2cc3a0ebca0bc424067fc81c58e733ff46f29c0a02fb8d5a52e8",
          "3fae75ecbf6b3b7f7a5ba5b31281869f395287f21a7f767a85df627bf787858e",
          "3fdaa932ce0ada56ae61a8a7a2fb26da24fa84768963cff42952e9fb9234fc3b",
          "40a3a31c1a1ad85dfae807d9d5e37fd6bf592528018ecb543638b53d980ec001",
          "40b4ebf2b3b016ecfb6bd0abfd0b4b5f20ef387e8e30297fc38622763e1302bf",
          "41c9267cf82815ec8f16ba32ca458ad2096ca592aa8a13af8f1cf7066275a419",
          "41cecdcb0e10de99dd1838eb201e1b6ba5c3f5233b836efa04b600868e9c3c6f",
          "424cc7f6748b0800e8b3d6694a35cd1dfef74ca0d2825e2c1863cef5e0f0273e",
          "452fa3bd5795ec51e4fa75a2b577cfc90f36548a66c7a168b5233a7e63bda5f7",
          "453d88499d3f43d1e2bbc90bc6e980cf2fefcccbd6074d587f768d71e644c389",
          "453e08737e168d8d1a58e67c561cc4f8aacae36fa5346198306c4d144d9c1b20",
          "46736f006bb8c6573b3dd4d2f55de1e0c00dceb72cdfc854308b6fc5faefbc99",
          "4926a90e00fd4c655276af101aa7a27bc446847eb89d74f2662b1d18063b1b16",
          "49e9411b14f054960bcb14b9ec7d826f87a84daab73eec3540615c3e4944f577",
          "4b00f8df9ba3132af84ec18ebf3d370ab23175a08d178bc44d28fcaea5ef8beb",
          "4b10af0ab9fa379926ecb08a8a6a9b04898e9cb88dbc59f7d41c078626b5e36c",
          "4bcaca67c5d870af95f3d0968fb686b1bc90dc134867ce303abd0387bce92895",
          "4c068b86aa33cebfc1f886c5c2e6dce2ad74ffee6affd76838274afb77523e09",
          "4ce1e927850e540191b28d4bc1731f7137a13275ff81f94e5152b078d8c334ae",
          "4d4ec00fa94a66db256aa8ed1d2539ec0e154ef761e677bcb818d82cb3ad625b",
          "4d551581cfe2338168eed493445c3a9e4ba783fe5116166fbff5a027945e7893",
          "4f282358ecb3aae0fe7794566d97408e59314b930082a39a55bbfd03a03b4890",
          "4f8f1006e93a36e43be7f9ea59a51580f4515df45ea368d49c34fb590574d8a2",
          "503df63c06e6f0fceb602df23d13afe14dc939d36539f2d09de3462422afb2b0",
          "504ba3ef7b4b3a8682523475773506741afcf7102431830e88c7614db78e3978",
          "508831601517b543a38e1fb4e6a117c07670e5ff0475267b6ae1e4d73638576f",
          "54a125eb6a82938cc602587fae48a752e381b2378204f0221953c4e08985e493",
          "54ebb23ed52a09335b39641fa38f8723912f94bd9ff02574e84db8ef5be5ea7c",
          "593585723059315bd94fa8e1ece653278448b30e895bc422db5053f6e32e072f",
          "5a96f28f1b659e5a64275d55556af46ac50b29665867a8cfdab6271f91033647",
          "5bc22664f305bce7a64817228a5709e10b7ee8e5ace0317cc25f9be077a30845",
          "5befc3caff3185df73b86e5e1eebbf7340dec471d6d20835d35bc613a339485a",
          "5c2f9712778817c6b51d2950e006eea89ce75c6f1bc359ec69e953d987e85e8d",
          "5d651384e238dc4f6cf0e513472d1a7f8a66f740b2bca790f59a4e20f51e930b",
          "5e5eea45bbb3754c9ed8f2a6391dfc117793be524652abc9ae7209c58136facb",
          "5e7b861bb3071e449b40ebb37bb1aa951c708463560930fdfd1a86ba954125fa",
          "5f0008d0e232193367262859dc84095c807c90c329df039a69158f1f1ddbdf39",
          "5f2d8dcdd11e30d3e28a8d0c948af46aaceef4a0e7ad0bce23a1ad1a7362b4db",
          "5f393a7efdff36c497db1e1e684d9260ed2db2d8e67744c568a14fc3b1dff275",
          "5f9dad92b2e0d92482c2bd89290a9a62f90b84052a0affd91f9322ec7d0fd7c6",
          "628f685e8bc4c7c9e71b90393fdcf2b47ecccdda384867c82d15084685fdcff0",
          "633cc7fcd3af4651517aa3f36f5105d6ffc4852551a981dae6e40e7dce6bc69e",
          "657c4a837c27bb2f34ddf32dac2aafe37c6ac936b8ab68218e8683871d43c4bd",
          "673d1165a3b0c75a375ac3352d19d3a0150ecb412a992325d4de93ceadb51341",
          "67e83384b9253a2e0eff15b7fca9f0241f9d9c0253dc3cd4de2e9971386a6db0",
          "68ae8a85320ff442b00d94dfddd1c232a861cca9cabc256c1f5cee3d6ef5c5e9",
          "6a0ce038e9af4656ff0dd3ad3327ea6ef52b4e9481990fd8217a2d0899d6a4f8",
          "6adea6352b66a3d4922961c5f3f91c931b6598f84483de80567aff82029a8586",
          "6d2703d47b9e40e03d0da0294dba0ffe38f1fe15ff266525cef83f030010833e",
          "6f12a062cfcb9497a36b3258ccefb4d540af8e303710be114549ea720a5eb6f6",
          "7270b4a28ba9b7113e8a178a7f31b71bc2f76274c6279dec6a80a483b28c6762",
          "7299b2470e85c07bead7e0472fa737f7c04821d666a10f261a391eedcacf6cfc",
          "72b17ab9e8f7c455499c9ff7b7e2118b78020ded82d1efb6e665bf506be639e7",
          "7348af56ad795e540d150ebc614dad65b55c77e7023ff2ef640f8ce3fc275e8a",
          "73833aefa6eb8caf654148f0ce685a0a021c474577ef7c7134a3b5194705f480",
          "73d2364d0131077ca702a68cec253af0edbeb9ee4fded97739b077d94da2cc49",
          "7446c6b053472aff2930aa79a78d98b7bf5db25453de9048b9f455d2aa18138e",
          "74919f9109f50c490094b9fe70566d775aa3ea292eb0945a4f4b47edb73e7398",
          "7540d25c28e2d52c46503645d63b0850244d6aa203a8383e05a9abde5c30d1f0",
          "76582fa02353655f0d1c1139b9b51fe1606f7d19d51f3fb0cba33aff3f1cd4b7",
          "765e9484c556a22f49f969e3ca8593ab56d4578851f774f80da069df7ee43ce4",
          "76b66b6a2102d83aa670d2b95df6c995163cdec4256a0cb781aa9b4600293ab4",
          "779bdf13f127b8d33c66677369eaa51a8146886c6cac9de74c23cbb63a0a7b81",
          "780b275dba9051c51f45246b69614e6287f4566c3bc03655a1099c240ee81041",
          "788ad084181fa988848164f1829e7b5b27e95e763f81c117ce086770534ba4a4",
          "78e421f67f158ab7545ea19ba44aa1e1c0bd557539201bb60b61df562fa87525",
          "79dcc54e5fee67b5a09df7928b2b4cf2d672f04e2236ee834abed28df46bee4e",
          "7a311aab27e9aeef0934a1e37021060a03301a372f8b7e0f15a9c221a0c43142",
          "7a61e6b9cd855a55ef758bc2210d41e187d628f84c7b27b9948b72100b88dbd1",
          "7adb5cfe4f2bc2f585926ba5d4f1584104a7cd9a7fa090417349b840d23f888c",
          "7aec180152c440d141be264590696a3029664b0f3fc2bb7bfc7f0a26911b909b",
          "7b94538fcff886b1076c17db4571c049afe429016d523d89aa40ef7c21557fb7",
          "7c3e8979b7368450f6e798e7d4b3ead8f08bdfb01757dade4e1754c54803167c",
          "7c45ca6b0f28ae30284a8277234c2fbfc8d21e71543bf11e773ea7590fe77a16",
          "7c6b14e7a36b7f1021a86f1282f4729b128d9f7d61f08dbfd9bbc1017ffd3a81",
          "81d45e548911e58862cf5e755495a3dc2899d00b673e57bc74080cdc9f389a35",
          "81ea0a4b15e68a1bec78744a75d6a89bd7b6dadd7db49f8f8a96725d8812f8be",
          "822f610bd7e30668b29f91fc0c91ea6b8f63a5b3f27a0b5ad0e2e071dab8062c",
          "84e2b5659857f7f5f454e596132fe8d19a7eacc0992394d3a2f322217a608d5b",
          "86536a32e46a0e2aaff32c975a2c336931cee4f233172e29b4ab0c0e57d2ef53",
          "882c9748528e10535b77169e75695e394494c216300944c0b613c5ede915c157",
          "886341a27a1bd7ed45df51acdf06fe0bc0a1f7555d425110e2fbeb137166878e",
          "893ee729f3007a1b545122d769e7d61a2f389745b24e0f67c85dbf2bf9b79b5c",
          "89bca230cdb98dc540895f8d6303c4458ca17c9fdfc084da72566e26fb7f444a",
          "8ae36d62177f10fe3666c96a752a0ff4d1cd46d46253f499d1c68f3d1e007e44",
          "8aeb79b70176bc55a5b52a6198b4fece6031ca97ebdc1b5e914556799ef01cfe",
          "8b1ca9ec87a64a8c40c7682a9179789a3974aa1ab7414c0661155ba13761409c",
          "8b824492957f9a98f1d27d1c64d028c31da7d256aba2cfed34e837936cacf99f",
          "8c0b95bc9f825fd2df665468216139566eff5c7a002ee345a35c0bd8a1ecc8b3",
          "8e80a324fb462d50c2e86c42d453476054d42f7a4c5cdc400d00c8effc101dec",
          "8ef8cda50859c3aaa4ff9d6315ff3bdeba716eacc5e448e1e812d76c6bc183ae",
          "8fd78112f356ee7e9b977fdae32fe4287bf2266baa191f17b60402609629b14a",
          "91ead3cd8f60e41791a19353223dcb61ca996b6613e11bc6bd08db571f7c6be7",
          "93498ae965109d4dd77fe90df722e19890cc054ad0d52a748be6b429346fea42",
          "950087b85607116920dbfc46a69a60135e101625a27cd9489a01d1086efa618c",
          "9583fa4ff4858e7eb7b34b5081aeaacc2368674d38b6ada2a4e827640d21966a",
          "97ca9b3c7e820d7a0daabe3ba921e1190f2516a0e58c9c5560f11b4bca8dcf61",
          "97cddbbf055888b01fd8338f7e1b8c6589019eb15223bbb00b215f9a891a1b78",
          "98feb69ecb32d40e0de282bcc12808b807b2c3356407b3417eacbf84ef4e193b",
          "9b1600802a2a36fc102cc4059009c9fdd69b06492e3a777e0769a19684161795",
          "9b4a523020fc83bf3d0cb96bf8fcf3094598013ce84c57d4bf663ff8daa92578",
          "9dae0b166dc84a0d0aacf525358dfa23aae64d57a9135ddc11c0e3e6493c7b02",
          "9ecef8b1a2e38343b1a30b845ca647c63b8eaf9aae9e7b5d9038916d1458d5f5",
          "9f609adad7e840c41c1ea1dafb431c680a4b941d83b9b179e1fa1fe56a6578d7",
          "a0fefe7eb3ba6fc7ecb1e94a160f3b22bb8ed797147491c4c1bbc13010947b32",
          "a1596254c92cab06db27925543e8595477ab606d9b2f482d015365ec3dad27da",
          "a184174f9b4cb6defd5056940d0dea1771d134c30bc38c648f6546988361834f",
          "a26148ecfdc920fa9f92c439abcd1039ab5e4507171bf64edaedbb33243f0a6e",
          "a295769ce219e2c13733406ee1ab5ed373d3b43e17d50eaac35a490e1f88d904",
          "a29d2a799245b9f8756a394c80aa5ce8e70c3013387d01ed8a166c98563ee752",
          "a41880d3546ebc3438f4c0c47f90ac59dcb0db1d8f9853ea74d9797912ac9b8f",
          "a4660e1d6e6f06cfb4e9294de73043ddf176b7374154c32a75700de46690fd05",
          "a515fc5f05e4cc898596d09bfcec7a04e8329dd88d1b9c1672af0f2f89b05028",
          "a5e45951530bea99fcafc8ff4b4fd7aec2a74976a68cbad1b893c678b03a7760",
          "a60523993af86ec3fd931559b48cd613615bb867a67ca0951ed1198ef47eb071",
          "a60b89f81890c90112acdef58c39c5dfe3a4b4540fc0d7bcd24bbd24eb76ce1c",
          "a63469758ce85ad85b158f71aa0747528b76bce9b7ebfa151de3178922afe4bf",
          "a6c25585e3105bef0c4caeff9d031096f45499208ea2157d309e93b2a3006843",
          "a7f1f3b0d91c595e9d81b7d9ebff9e3519786fb0741a9e1ea864082ffb403761",
          "ab65f39ea9ed34d354add351a3e2438eed0de981cea066df16f61177781d3af7",
          "ab97a8c1069d8d1534a2b67de2130d22beffe35ed05ae8622f74872b660561c7",
          "adb82ff3f518ceabc89ef6cb11f687fab7ba6021916156c750e9cb5c62bda514",
          "ae0f0497f2e2e1214640f2cd8a45ba5a19bb04a39ee6d4499d8a233050168cde",
          "ae8cc7dbf4144a080aac358c28f1182737259f8382630100cc02a06d8df77927",
          "af07055d66349ced4c7431c3bc55b7e3303efbeb772153b5e55b876644e39838",
          "af93d7b75999aeb63b92d65e5f8ddc7daaf8abfae0dac843399a35127303dd64",
          "b19c85f3caa7e8e7140ef87ea0c19d7f2d6c4e2b5f64c07ce730728b8f17238a",
          "b1df42ad58bef15516a2e57540484228282492602b0646319a1f2bde0799e108",
          "b3dad8a37866e2f7d60410d818e06de9d8e4dbbd5d97aa7057a5da561de59134",
          "b40262d8f849f7b1f147d8749cffd0c32e5d48e0d6c5c6bf1fdafbe83e8aacfd",
          "b58de935e101201bfc1350f333936ffbc9de545a063e11cb8ef6afdb98c92272",
          "b6bc791f03d349937dcd3e6bc539fdc4107e40001bb4b4bb120835c973c960c6",
          "b7cb71ce65305f9403b4ba934b7cda238a0c69e4d4f4c18e9a3589e031fb3239",
          "b7f25ee4e778d51348b3821b5468ef6ae377c06fb5925974e61fdef2cb8d5836",
          "b81c900a1d6bff58610b85a4d5d00f603815e908de909cfb3bff52a07bcf3948",
          "b83cb398c3b13d0c54ea9b090b68c8391305f2f944c346afef58d431f2e1faf8",
          "b8f97a781f7bac790dddbfbce6e969484f57b31a41fc0335ebc350c9f362eb1c",
          "b99e160d488dfd95e6e169672b825b58ffa0d382b700cf32868af464c5904f19",
          "b9f809cff4f8cd231f9d79bac0c58dfd7c748a2539cb070051faef7bfb15c2a4",
          "bab918b63853c1da0f0796b6078b5249ad2a37122942ae1aa7d1ac6c06cd8b73",
          "bc3a370ad58a53693f6e2e32badbea411218464cb339bb93d07206b609a8a601",
          "bcbe9777f48526838ab8f951571ac8eaf97a1bb9d9fe31f1795633dea0270b6a",
          "bd43be7fb745d3091761ec97647df27bddf63c28007642d1100d577a5139ab81",
          "bed88db7b12d7699a21ae9536153ee7c28d72b89e3195f59477d3f802f52cdea",
          "c0f6048fac76efbb755897c8af60a46bb746d84a2ee2c54cdc2034f451263e83",
          "c218dc6ded18adee2509c82db335f1a1e8008e86a6827950155ec6b7c3ed68bb",
          "c36a56df700e328eeb5133c591c51628b71f2ec59d0598665f4055da22e541d4",
          "c41169ef586ff986b5220386ff08fbf07d1e8e62ab429d631093a6dc637e9e3d",
          "c439582c80056cff1002ea2a307eb0f28ad3b35618fd93fdef16584e216e3804",
          "c4ff6337f1bc14712defb1cea78abb4224b12175a443eced18c96f71585cdc11",
          "c6526002a665a7ed1e7611729be0aee4757f407bcdf2b471966de3e8d1e6706a",
          "c6a5df641664e6db2951ee4683eb67ca2bd192f19ad3dc1c84d6e9110715b0bc",
          "c7c177d6195e774c9adc1e13b264acc753912abb44980cdddd8faec3afa6d77b",
          "c7c1e308f675366f98fe2855d8914a048c1b3f06aaa22c5b932e735112893cc6",
          "c7c8bbbbcfa1cfac3851e8c0d3475c25d323d73cd03268b36fb987dd1f35737c",
          "c9b3e10f4b8fc516802078655b642ce49feeb597f9f6c597aa319873d023d3fa",
          "caf5fcdd0747295444c48341bc8133a9ea524a289ff11e10736fbf949a1a281a",
          "cb37c4e80da6302631b1999b2d256b470396c995d760ce7b7974cb45019a7bd3",
          "cbc6cb0b07b8b73b71368f1ab6e8e9d6a46fef06a1598c17eefea877056cd6f9",
          "cbc98dc5ed8cd31fa4736a006fce7844b025baf73cbd8ccddaf2a99376ebdabe",
          "cc61e49b5a06a791b2fa7c8287204ae3d961fce36ab4280e22c566ddc73885ce",
          "cce567fdc6c222c600097dbd2397881ba950e1572c71c1a75801512f16d84d78",
          "cce7fd0b3d3e9ae8288510d20ea735bfe2c0c0fffeed0db9b2d2484846f34e3b",
          "cd98a4557485ad02289d59c81cc1471a65b0e23e598cc0a90df4169be4dce8c5",
          "ce60b0c1bcbb2f1abfc54c5bdb60e9cd4fa3656eaabd44080af056a6e89c7540",
          "cfc502ff967250eee82b22947d93f5b65957b2d2a75527e09d61d1ccfee1baa7",
          "d3a94c41169a8a8cf11287eb68024acb8425ed8da22ad35a3a9877bc903dab3c",
          "d3dfc273dd3559f792141ad131b75e2a8871bb94063381954aac089aa48d3081",
          "d48b6a5bb778857b50e0dac08ed317a4d4460f97f31faea8b81ec1d0757dce25",
          "d5862fd3278342a4ed5b869664fcb38c8468834bbc08b0e67970dc9152234a4f",
          "d6277b55d67d24bbcabee466565984683afd6108eb5b637df4b617382bc221cc",
          "da8f0e64804501bb820afd26e225ddfb06c0f43ad898a0482e2a0852da415ef5",
          "db52e9e3e47bd5db1765c3bdd018217d9f975a2a22f5d96b08dd36017cf3f233",
          "db57dabfd78e8c158881cb17355098624f63d9558581fd82762ec4ecf932ab08",
          "dcab9b0b5e2cd856b204fb45361bc3f338fb0fdba06a354baaa2762ca95a8ceb",
          "dd4ecf60730e8467005b797e1b40ddba1b6ea7e79edb715209b4c83c98e69144",
          "dd9ca25d6be04f6869b98b73fd25e8da60b1fdb353c9cde0158a1f72aea7083a",
          "de65160719848918e6b24ec9172371309fd74f9a9e7497316568f77d581abe51",
          "df38998da62acf901233b4efee531ed8c24be808dc96b759c088a924e2fe28fb",
          "e2180b190d70faa74fca66f6e3f84182aa22fb66bb9e2a4c7639a942c32b6c6d",
          "e29e9df3203f76510b4ea2cf47a484a099a9fd0b136ab08dad78faf19311be68",
          "e2e9303c7b2d5f0626c152c676f0bb3d42a90ac8de49028d8bfb56e9499106f4",
          "e39f0c1f039a65809449b2193abdde7cf692d2fab35627be35e041e1fdc157aa",
          "e3ab991d15adce9f51ed5d2c7e612c640083ccd98e2545b7bb47c493e516abf1",
          "e63099e7b6757fe5d586ab283729032a7e2a051794b55517d4dd6b26758e7727",
          "e7981f4889ce9bcbd1c098dbd672a1768bbab8780ff5ebe2aff6e8c5b3c6f5ea",
          "e9b766603ac408f68a07279bdf535f7fe8dacbd98836eb9f20d86debc2a9a150",
          "ea54cf79bb3f81f65bdf0c426c11ab8968db1c16eb2fc76e8cade686999eab1d",
          "eb9cf52086f1f5a60df55993ecb63e06ce1db99e371e878b607c6399cb5412ca",
          "ebf9b8961ba950a3e6ef778b1579deb18b679d53493028c61d20e1f173676566",
          "ec58b8ee4431296c9ead69ccfe57d9d1222e3db74b8afc07934b4ffbd7bcc93e",
          "ec5ab9e4e7011e27ea2e69a70b98497fec996d0c0363b408f9dba54fb6442ab9",
          "ee1a3ec668115a84528bfb43cab70025aa9d077a97059bd5c222e9f0ba2b59f7",
          "ee768b442b7a3f686caf29f10dc25d2c1387e9e3f7948156f7242c9eb59a5824",
          "ef94117562adaf005d5a3aa6c4981bc29b0fce01f861dc9196128698eeaf8530",
          "efb892c665e8fe26857553076b528c1f9d78729cc1b43ca0ab87562f867cdd6a",
          "f0ce669d5e5c05a4e01a37e1ccdbeab7a2a540f5c2eed31c5c6c6ff11d5410fd",
          "f40329857784d7b2f3ea6e750db8211a0aa0dd1e6d7f4beb174b070f0dd2d29f",
          "f478e2bd22fa25749f26f1d21614c86546196d9e792871b0a332ac4ec414ea9b",
          "f69484aab1cadff6f01baa49521f39986a5f9388fe4a4a325ea98f6791200a1a",
          "f74c1c2ebbd12186aae6c6210a506970c32cfe45fd200ded9acea4a8ef3663d5",
          "f8217203dfc731bf5e13a232629e9816f2da29762c6f8ba2ce1898be55017a58",
          "f8882f727e257f144e944a117bb48d89cc2f51bc4caf4feb369835b118dbd3c1",
          "f965a3c613825034aa114f1f1e345b1bea14799f841f5bfe81b28028422d96e5",
          "f9b024e2539e7fb2a5a3029ebb941a3613ccbdc44c383f97c9f95f73a67cf510",
          "fb5f6540286e2b09b1072508a75d7ce59617a3744fdd4484b5a6221b975e0d97",
          "fc2e018a68a8d738a4a5c24451e783168bbcaa2be8fa91b2d20d365d8a386d0a",
          "fd688243ebd3bcda50c0c360532d2d73034c21d8783c29d55e222e5d3f60aa23",
          "fd7e274f70139443c39ea77ebff1f97d29db37e5f278c495a0b6ae085e5e5a07",
          "fd7e41a168a1a22bf9d1eea93b785f988e755f65f7e2387f1ebe88452798b719",
          "ffcb7df5ea54f35047d9f927f3b1e75c52bce40978a0cacbce5fc3576f5a1069"
        ],
        "expected_output_sha256": "b4285af317ea4e3a31fe2f73b37bf4dbe54c277343a4e305cde3492bf13800de",
        "expected_output_source": "target_model_inference",
        "numeric_metrics": {
          "not_run_reason": "exact-board VCS execution did not complete",
          "passed": false
        },
        "passed": false,
        "rtl_output_sha256": "4f81904a9b06c58572a0e5769b3b4ffb99e7bd4be88ee8c2b64a804f483d9dc6",
        "status": "not_run",
        "testbench_sha256": "4f6801c52ff94c38fd50c3aa1209bd0e4a3d8f58a6731c2e9ae4c350fc652645"
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
      "summary": "vcs_compile_failure: Error-[IND] Identifier not declared"
    },
    "case_vcs_functional_applicability": {
      "applicable_rerun_gates": [
        "case_vcs_evidence_analyzer",
        "case_vcs_functional_sim"
      ],
      "current_failed_gates": [
        "case_axi_ddr_interface",
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
      "failed_boundaries": [],
      "failing_transaction": {
        "checker": "real_tool.case_axi_ddr_interface",
        "source": "verification_result",
        "summary": "returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export"
      },
      "failure_record_count": 0,
      "failure_signature": {
        "boundary": null,
        "boundary_id": null,
        "expected_value": null,
        "integration_summary": null,
        "observed_value": null,
        "status": null,
        "summary": null
      },
      "lower_layer_evidence_challenge": {
        "reason": "no localized trace record with lower-layer pass evidence is available",
        "status": "no_lower_layer_challenge"
      },
      "minimal_repair_context": {
        "boundary_contract": {},
        "current_layer_failure_context": {},
        "lower_layer_evidence_challenge": {
          "reason": "no localized trace record with lower-layer pass evidence is available",
          "status": "no_lower_layer_challenge"
        },
        "repair_scope": "verification_capability_repair",
        "root_candidate_module": null,
        "trace_record": {},
        "violated_contract": "verification_semantic_capability_contract"
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
      "representative_failure_count": 0,
      "root_candidate_module": null,
      "schema_version": "spatialaccagent.debug_closure.v0",
      "status": "verification_capability_gap",
      "strategy": "contract_guided_boundary_failure_slice",
      "targeted_replay_plan": {
        "reason": "repair semantic testbench, loader/weight binding, numeric contract, or checker capability before requesting a hardware boundary trace",
        "status": "blocked_by_verification_capability_gap"
      },
      "violated_contract": "verification_semantic_capability_contract"
    },
    "hierarchical_repair_loop": {
      "agent_runtime_llm_blocker": false,
      "current_layer": {
        "id": "board_axi_ddr_wrapped_system",
        "missing_or_failed": [
          "case_multilayer_functional=not_run",
          "case_pipeline_deadlock_check=not_run",
          "case_axi_ddr_interface=fail",
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
      "failure_kind": "verification_capability_gap",
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
            "case_axi_ddr_interface=fail",
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
      "root_candidate_module": null,
      "schema_version": "spatialaccagent.hierarchical_repair_loop.v0",
      "status": "needs_repair",
      "violated_contract": "verification_semantic_capability_contract"
    },
    "prior_repair_execution_feedback": {
      "blockers": [
        "The only compiler diagnostic preserved is \"Error-[IND] Identifier not declared\"; it omits the declaring source path, line/column, identifier spelling, declaration context, and compilation order. An RTL or testbench edit would therefore be speculative and could modify the wrong agent-owned source.",
        "The compile failed before simulation, so no SACG/CCTG runtime frontier exists and no simulation-only observability repair is causally supported."
      ],
      "deterministic_feedback": [],
      "execution_errors": [],
      "input_fingerprint_sha256": "09fe818ea42c0365d3cc2c480ab90dfb2a9e7d7269e30f1ca60729d03ac92d21",
      "llm_records": [
        {
          "agent": "exact_board_integration_generation_agent",
          "blockers": [
            "The only compiler diagnostic preserved is \"Error-[IND] Identifier not declared\"; it omits the declaring source path, line/column, identifier spelling, declaration context, and compilation order. An RTL or testbench edit would therefore be speculative and could modify the wrong agent-owned source.",
            "The compile failed before simulation, so no SACG/CCTG runtime frontier exists and no simulation-only observability repair is causally supported."
          ],
          "deterministic_feedback": [],
          "input_fingerprint_sha256": "023a93c0cca41e56857e9c9119e8b1abeb1fd8b861be6aa9cc0616e992b15b69",
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
              "rationale": "Current feedback proves a real VCS compile failure with return code 1, but preserves only the error class and generic first-error text. Rule 19 requires source provenance rather than a speculative source edit when path/line, declaration context, or compile order are absent. This capability reads preserved artifacts and does not authorize an unchanged-source VCS replay.",
              "required_evidence": [
                "The raw VCS compiler diagnostic containing the undeclared identifier spelling and absolute source path with line and column.",
                "A bounded source excerpt containing the failing reference and its relevant declaration or instance context.",
                "The exact ordered VCS compilation source list, include directories, defines, and language modes sufficient to determine whether the identifier is unavailable because of compile ordering, missing inclusion, or local source syntax."
              ],
              "target_modules": [
                "spatialacc_exact_board_multilayer_tb",
                "app_shell_9p_cnn_core_0_1",
                "spatialacc_axi4_protocol_monitor",
                "SingleLayerSemanticHarness",
                "Activation",
                "AttentionGQA",
                "ElementwiseMul",
                "GatedMLP",
                "GeneratedAcceleratorTop",
                "GeneratedAxiDdrTop",
                "Linear",
                "Linear_1",
                "Linear_2",
                "Linear_4",
                "LlamaStyleBlock",
                "QKVProjection",
                "Queue1792_StreamBeat",
                "Queue4_StreamBeat",
                "QwenLayerPipelineTop",
                "QwenMultiLayerSystemTop",
                "RMSNorm",
                "ResidualAdd",
                "RoPE",
                "VectorNorm",
                "ram_1792x256",
                "ram_4x129"
              ]
            }
          ],
          "scope": "verification_capability_repair",
          "sha256": "608346ca980fe1a145d16a53a7162258170bc29a7d95d4143b4fd5cb5c31bb76",
          "stage": "repair_execution",
          "status": "blocked",
          "step_id": "repair_step.00",
          "summary": ""
        }
      ],
      "repair_execution_status": "incomplete",
      "report": {
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_execution_report.json",
        "schema_version": "spatialaccagent.repair_execution_report.v0",
        "sha256": "5f99041fb87c19d7d65e0dc8e0ff6c3c0a8de8cc1e30b1f0b96c516a4e2d9328"
      },
      "required_capabilities": [
        {
          "capability_id": "vcs_compile_diagnostic_source_provenance",
          "debug_layer": "board_axi_ddr_wrapped_system",
          "producer_scope": "real_board_vcs_compile_provenance",
          "rationale": "Current feedback proves a real VCS compile failure with return code 1, but preserves only the error class and generic first-error text. Rule 19 requires source provenance rather than a speculative source edit when path/line, declaration context, or compile order are absent. This capability reads preserved artifacts and does not authorize an unchanged-source VCS replay.",
          "required_evidence": [
            "The raw VCS compiler diagnostic containing the undeclared identifier spelling and absolute source path with line and column.",
            "A bounded source excerpt containing the failing reference and its relevant declaration or instance context.",
            "The exact ordered VCS compilation source list, include directories, defines, and language modes sufficient to determine whether the identifier is unavailable because of compile ordering, missing inclusion, or local source syntax."
          ],
          "target_modules": [
            "spatialacc_exact_board_multilayer_tb",
            "app_shell_9p_cnn_core_0_1",
            "spatialacc_axi4_protocol_monitor",
            "SingleLayerSemanticHarness",
            "Activation",
            "AttentionGQA",
            "ElementwiseMul",
            "GatedMLP",
            "GeneratedAcceleratorTop",
            "GeneratedAxiDdrTop",
            "Linear",
            "Linear_1",
            "Linear_2",
            "Linear_4",
            "LlamaStyleBlock",
            "QKVProjection",
            "Queue1792_StreamBeat",
            "Queue4_StreamBeat",
            "QwenLayerPipelineTop",
            "QwenMultiLayerSystemTop",
            "RMSNorm",
            "ResidualAdd",
            "RoPE",
            "VectorNorm",
            "ram_1792x256",
            "ram_4x129"
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
      "summary": "",
      "validation": {
        "errors": [],
        "status": "pass"
      }
    }
  },
  "failures": [
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_axi_ddr_interface",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate axi_ddr_interface",
      "execution_fingerprint_sha256": "cd434e6349597b223066ff96bd7e3e3af4fb6ba94b789afdaf039edbb59ff9f1",
      "failure_class": "runtime_harness",
      "kind": "case_axi_ddr_interface",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_axi_ddr_interface.json",
      "produced_reports": [
        {
          "blockers": [
            "simulation.source_identity_sha256 does not bind the current identity document",
            "simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts",
            "simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
            "simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
            "simulation.vcs_compile_plan.ordered_commands[1].authority_refs do not bind exact Vivado export contexts",
            "simulation.vcs_compile_plan.ordered_commands[1].executable is not authorized by current tool_profile or referenced Vivado export",
            "failed checks: simulation_identity_binding, canonical_vcs_compile_plan"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/axi_ddr_interface.json",
          "schema_version": "spatialaccagent.qwen_hierarchical_check.v0",
          "status": "fail",
          "summary": null
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
      "summary": "returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
      "tool_report_blockers": [
        "simulation.source_identity_sha256 does not bind the current identity document",
        "simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts",
        "simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "simulation.vcs_compile_plan.ordered_commands[1].authority_refs do not bind exact Vivado export contexts",
        "simulation.vcs_compile_plan.ordered_commands[1].executable is not authorized by current tool_profile or referenced Vivado export",
        "failed checks: simulation_identity_binding, canonical_vcs_compile_plan"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/axi_ddr_interface.json",
      "tool_report_status": "fail",
      "tool_report_summary": null
    },
    {
      "checker": "required_real_tool_evidence_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']"
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
      "summary": "multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
    },
    {
      "checker": "verification_agent_decision_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
    }
  ],
  "note": "Failing checkers are classified; not_run real tools are evidence gaps, not automatic repair failures.",
  "pending_evidence": [
    {
      "acceptance_role": "functional_sim_candidate",
      "checker": "real_tool.case_vcs_functional_sim",
      "command": "python3 scripts/verification/case_board_vcs_functional.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
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
      "required": true,
      "required_group": "functional_sim",
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_axi_ddr_interface']",
      "tool_report_blockers": [],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
      "tool_report_status": "fail",
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_vcs_evidence_analyzer",
      "command": "python3 scripts/verification/qwen_vcs_evidence_analyzer.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "vcs_evidence_analyzer",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_vcs_evidence_analyzer.json",
      "produced_reports": [
        {
          "blockers": [
            "vcs_compile_failure: Error-[IND] Identifier not declared"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
          "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v4",
          "status": "needs_repair",
          "summary": "vcs_compile_failure: Error-[IND] Identifier not declared"
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
      "python_environment_group": "target_model_oracle",
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_axi_ddr_interface'] report_status=needs_repair blockers=vcs_compile_failure: Error-[IND] Identifier not declared",
      "tool_report_blockers": [
        "vcs_compile_failure: Error-[IND] Identifier not declared"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
      "tool_report_status": "needs_repair",
      "tool_report_summary": "vcs_compile_failure: Error-[IND] Identifier not declared"
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_deadlock_axi_check",
      "command": "python3 scripts/verification/case_deadlock_axi_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/deadlock_axi_check.json --rtl-wrapper /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/sample_project_sources/wrapper.v --testbench /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/board_integration/spatialacc_exact_board_multilayer_tb.sv",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_deadlock_axi_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_deadlock_axi_check.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_axi_ddr_interface']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
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
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_axi_ddr_interface']",
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
      "reason": "Current feedback proves a real VCS compile failure with return code 1, but preserves only the error class and generic first-error text. Rule 19 requires source provenance rather than a speculative source edit when path/line, declaration context, or compile order are absent. This capability reads preserved artifacts and does not authorize an unchanged-source VCS replay.",
      "repair_gate": "case_vcs_functional_sim",
      "repair_kind": "vcs_compile_diagnostic_source_provenance",
      "repair_tool_role": "exact_board_vcs_compile_provenance",
      "requested_capability_id": "vcs_compile_diagnostic_source_provenance",
      "requested_producer_scope": "real_board_vcs_compile_provenance",
      "required_evidence": [
        "The raw VCS compiler diagnostic containing the undeclared identifier spelling and absolute source path with line and column.",
        "A bounded source excerpt containing the failing reference and its relevant declaration or instance context.",
        "The exact ordered VCS compilation source list, include directories, defines, and language modes sufficient to determine whether the identifier is unavailable because of compile ordering, missing inclusion, or local source syntax."
      ],
      "scope": "verification_capability_repair",
      "source": "prior_nonfallback_llm_required_capability",
      "source_feedback_fingerprint_sha256": "09fe818ea42c0365d3cc2c480ab90dfb2a9e7d7269e30f1ca60729d03ac92d21",
      "target_modules": [
        "spatialacc_exact_board_multilayer_tb",
        "app_shell_9p_cnn_core_0_1",
        "spatialacc_axi4_protocol_monitor",
        "SingleLayerSemanticHarness",
        "Activation",
        "AttentionGQA",
        "ElementwiseMul",
        "GatedMLP",
        "GeneratedAcceleratorTop",
        "GeneratedAxiDdrTop",
        "Linear",
        "Linear_1",
        "Linear_2",
        "Linear_4",
        "LlamaStyleBlock",
        "QKVProjection",
        "Queue1792_StreamBeat",
        "Queue4_StreamBeat",
        "QwenLayerPipelineTop",
        "QwenMultiLayerSystemTop",
        "RMSNorm",
        "ResidualAdd",
        "RoPE",
        "VectorNorm",
        "ram_1792x256",
        "ram_4x129"
      ]
    }
  ],
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
          "reason": "Current feedback proves a real VCS compile failure with return code 1, but preserves only the error class and generic first-error text. Rule 19 requires source provenance rather than a speculative source edit when path/line, declaration context, or compile order are absent. This capability reads preserved artifacts and does not authorize an unchanged-source VCS replay.",
          "repair_gate": "case_vcs_functional_sim",
          "repair_kind": "vcs_compile_diagnostic_source_provenance",
          "repair_tool_role": "exact_board_vcs_compile_provenance",
          "requested_capability_id": "vcs_compile_diagnostic_source_provenance",
          "requested_producer_scope": "real_board_vcs_compile_provenance",
          "required_evidence": [
            "The raw VCS compiler diagnostic containing the undeclared identifier spelling and absolute source path with line and column.",
            "A bounded source excerpt containing the failing reference and its relevant declaration or instance context.",
            "The exact ordered VCS compilation source list, include directories, defines, and language modes sufficient to determine whether the identifier is unavailable because of compile ordering, missing inclusion, or local source syntax."
          ],
          "scope": "verification_capability_repair",
          "source": "prior_nonfallback_llm_required_capability",
          "source_feedback_fingerprint_sha256": "09fe818ea42c0365d3cc2c480ab90dfb2a9e7d7269e30f1ca60729d03ac92d21",
          "target_modules": [
            "spatialacc_exact_board_multilayer_tb",
            "app_shell_9p_cnn_core_0_1",
            "spatialacc_axi4_protocol_monitor",
            "SingleLayerSemanticHarness",
            "Activation",
            "AttentionGQA",
            "ElementwiseMul",
            "GatedMLP",
            "GeneratedAcceleratorTop",
            "GeneratedAxiDdrTop",
            "Linear",
            "Linear_1",
            "Linear_2",
            "Linear_4",
            "LlamaStyleBlock",
            "QKVProjection",
            "Queue1792_StreamBeat",
            "Queue4_StreamBeat",
            "QwenLayerPipelineTop",
            "QwenMultiLayerSystemTop",
            "RMSNorm",
            "ResidualAdd",
            "RoPE",
            "VectorNorm",
            "ram_1792x256",
            "ram_4x129"
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
          "spatialacc_axi4_protocol_monitor",
          "SingleLayerSemanticHarness",
          "Activation",
          "AttentionGQA",
          "ElementwiseMul",
          "GatedMLP",
          "GeneratedAcceleratorTop",
          "GeneratedAxiDdrTop",
          "Linear",
          "Linear_1",
          "Linear_2",
          "Linear_4",
          "LlamaStyleBlock",
          "QKVProjection",
          "Queue1792_StreamBeat",
          "Queue4_StreamBeat",
          "QwenLayerPipelineTop",
          "QwenMultiLayerSystemTop",
          "RMSNorm",
          "ResidualAdd",
          "RoPE",
          "VectorNorm",
          "ram_1792x256",
          "ram_4x129"
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

<design_team>
{
  "completed_subtasks": 0,
  "decomposer_used_fallback": false,
  "decomposition_source": "deterministic_conditional_router",
  "errors": [],
  "executable_actions": [],
  "reason": "deterministic failure class is unambiguous; the primary repair agent owns the bounded action decision",
  "routing_mode": "conditional",
  "schema_version": "spatialaccagent.conditional_review_summary.v0",
  "stage": "repair",
  "status": "no_split",
  "subtask_count": 0,
  "used_fallback_count": 0
}
</design_team>

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
      "last_observed_at": "2026-09-04T16:14:03+00:00",
      "observation_count": 31,
      "observed_transition_ids": [
        "transition.2123",
        "transition.2129",
        "transition.2132",
        "transition.2135",
        "transition.2138",
        "transition.2141",
        "transition.2144",
        "transition.2147",
        "transition.2150",
        "transition.2153",
        "transition.2156",
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
        "transition.2455"
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
      "last_observed_at": "2026-09-04T17:41:23+00:00",
      "observation_count": 251,
      "observed_transition_ids": [
        "transition.2423",
        "transition.2424",
        "transition.2425",
        "transition.2426",
        "transition.2427",
        "transition.2428",
        "transition.2429",
        "transition.2430",
        "transition.2431",
        "transition.2432",
        "transition.2434",
        "transition.2435",
        "transition.2437",
        "transition.2439",
        "transition.2441",
        "transition.2443",
        "transition.2444",
        "transition.2445",
        "transition.2446",
        "transition.2447",
        "transition.2448",
        "transition.2449",
        "transition.2450",
        "transition.2451",
        "transition.2452",
        "transition.2454",
        "transition.2456",
        "transition.2457",
        "transition.2458",
        "transition.2459",
        "transition.2460",
        "transition.2461"
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
    }
  ],
  "debug_layer": "board_axi_ddr_wrapped_system",
  "omitted_unscoped_cross_layer_or_limit_counts": {
    "backtrack_requests": 1,
    "contamination_barriers": 11,
    "failure_lessons": 204,
    "retry_requests": 0,
    "stage_outcomes": 215
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
      "last_observed_at": "2026-07-25T04:03:12+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
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
      "last_observed_at": "2026-07-25T04:09:24+00:00",
      "observation_count": 8,
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
      "last_observed_at": "2026-09-04T16:14:03+00:00",
      "observation_count": 31,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-27T12:59:36+00:00",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "policy": "Only hierarchy-bound records matching this prompt scope are operational context. Omitted records remain persisted recovery history; sacg_memory_truth separately carries the complete authoritative current blocker set.",
  "recent_failure_lessons": [
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0205",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-02T13:51:17+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0206",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T07:21:12+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0207",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T11:07:48+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0208",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T11:17:53+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0209",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T11:21:43+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0210",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T11:26:29+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0211",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T16:09:55+00:00",
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
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0212",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-04T16:14:03+00:00",
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
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0216",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-02T13:51:17+00:00",
      "transition_id": "transition.2403",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0217",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T07:21:12+00:00",
      "transition_id": "transition.2433",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0218",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T11:07:48+00:00",
      "transition_id": "transition.2436",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0219",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T11:17:53+00:00",
      "transition_id": "transition.2438",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0220",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T11:21:43+00:00",
      "transition_id": "transition.2440",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0221",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T11:26:29+00:00",
      "transition_id": "transition.2442",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0222",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T16:09:55+00:00",
      "transition_id": "transition.2453",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence."
      ],
      "failed_gates": [
        "case_axi_ddr_interface",
        "functional_sim"
      ],
      "id": "stage_outcome.0223",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-04T16:14:03+00:00",
      "transition_id": "transition.2455",
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
  "active_contamination_barrier_count": 16,
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0329",
      "last_observed_at": "2026-07-25T04:03:12+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
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
      "last_observed_at": "2026-07-25T04:03:12+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
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
      "last_observed_at": "2026-07-25T04:03:12+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
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
      "last_observed_at": "2026-07-25T04:09:24+00:00",
      "observation_count": 8,
      "observed_transition_ids": [
        "transition.0231",
        "transition.0237",
        "transition.0239",
        "transition.0241",
        "transition.0244",
        "transition.0246",
        "transition.0248",
        "transition.0251"
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
      "last_observed_at": "2026-07-27T12:31:00+00:00",
      "observation_count": 1877,
      "observed_transition_ids": [
        "transition.2090",
        "transition.2091",
        "transition.2092",
        "transition.2093",
        "transition.2094",
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
        "transition.2121"
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
      "last_observed_at": "2026-09-04T16:14:03+00:00",
      "observation_count": 31,
      "observed_transition_ids": [
        "transition.2123",
        "transition.2129",
        "transition.2132",
        "transition.2135",
        "transition.2138",
        "transition.2141",
        "transition.2144",
        "transition.2147",
        "transition.2150",
        "transition.2153",
        "transition.2156",
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
        "transition.2455"
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
      "last_observed_at": "2026-09-04T17:41:23+00:00",
      "observation_count": 251,
      "observed_transition_ids": [
        "transition.2423",
        "transition.2424",
        "transition.2425",
        "transition.2426",
        "transition.2427",
        "transition.2428",
        "transition.2429",
        "transition.2430",
        "transition.2431",
        "transition.2432",
        "transition.2434",
        "transition.2435",
        "transition.2437",
        "transition.2439",
        "transition.2441",
        "transition.2443",
        "transition.2444",
        "transition.2445",
        "transition.2446",
        "transition.2447",
        "transition.2448",
        "transition.2449",
        "transition.2450",
        "transition.2451",
        "transition.2452",
        "transition.2454",
        "transition.2456",
        "transition.2457",
        "transition.2458",
        "transition.2459",
        "transition.2460",
        "transition.2461"
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
    }
  ],
  "active_contamination_barriers_truncated": false,
  "debug_layer": "board_axi_ddr_wrapped_system",
  "global_persisted_blocker_counts": {
    "active_contamination_barriers": 19,
    "open_backtrack_requests": 1,
    "open_retry_requests": 6
  },
  "omitted_unscoped_or_cross_layer_blocker_counts": {
    "active_contamination_barriers": 3,
    "open_backtrack_requests": 1,
    "open_retry_requests": 0
  },
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 6,
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
      "last_observed_at": "2026-07-25T04:03:12+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
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
      "last_observed_at": "2026-07-25T04:09:24+00:00",
      "observation_count": 8,
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
      "last_observed_at": "2026-09-04T16:14:03+00:00",
      "observation_count": 31,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-27T12:59:36+00:00",
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
      "evidence_binding_file_count": 812,
      "evidence_binding_roles": {
        "evidence_artifact": 12,
        "gate_log": 8,
        "input_artifact": 330,
        "lower_scope_certificate_continuity_proof": 9,
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
      "evidence_binding_sha256": "6e6d0ab26664b3af3f894cfcf69c0cd56b4c8a52203232a3f0ea9105347e5c2a",
      "file_sha256": "2bbc6880205155cbc1119882b2503281c2cb43b4b3c0d40a1754acb1e3a20569",
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
