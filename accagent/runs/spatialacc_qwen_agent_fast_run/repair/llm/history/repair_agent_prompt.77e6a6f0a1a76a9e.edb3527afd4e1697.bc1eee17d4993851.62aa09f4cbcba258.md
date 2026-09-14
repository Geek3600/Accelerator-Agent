<agent>
repair_agent
</agent>

<task>
Make the authoritative bounded-repair decision from verification failures, SACG/CCTG evidence, and the conditional specialist review when one was triggered, without bypassing checkers. Respect the hierarchical repair loop: if lower layers already passed and the current layer failed, request current-layer boundary trace/targeted replay first; reopen lower-layer modules only when the trace explicitly contradicts their pass evidence. The candidate plan contains hash-bound completed lower-layer capability evidence. Treat it as closed: do not request, rerun, or repair the connected-kernel replay unless a new current trace explicitly contradicts its certified invariant. Select only the next causally distinct exact-board AXI/DDR action.
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
        "diagnosed_failure_class": "board_output_lifecycle_frontier_violation",
        "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
        "origin_gates": [
          "case_vcs_functional_sim"
        ],
        "origin_layer": "board_axi_ddr_wrapped_system",
        "policy": {
          "cross_layer_reuse_is_read_only_without_an_explicit_targeted_backtrack": true,
          "current_failed_gate_must_match_origin_or_target_rerun_gate": true,
          "live_source_artifact_hashes_must_match": true
        },
        "preflight_manifest_projection_sha256": "8c0ab5e89d0cbb2d91d577086af43da52d1f466c72cd2101dad802d808bc5368",
        "schema_version": "spatialaccagent.diagnosis_applicability_binding.v1",
        "source_artifacts": [
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
            "role": "board_vcs_runner_report",
            "sha256": "a91cbed0ab510dc494f82a530f5b7c7bb4c587c7dba4203d70bd7245fd141dbc"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json",
            "role": "board_simulation_manifest",
            "sha256": "bdca0583b26b71899e4aa42038850f0c56f35fa2b622d20b681081d2c8c667b0"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/board_source_identity.json",
            "role": "board_source_identity",
            "sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
            "role": "semantic_testbench_manifest",
            "sha256": "6154d406780b2f314c9a7a6c2fcf4d7f987871b5fe462e601d33710d826a19b5"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
            "role": "dut_weight_binding_manifest",
            "sha256": "22bac0663a46ee2fa9e0e3fc5be05ef695ded76a388132d53803c8305282a22d"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_executed_manifest.json",
            "role": "executed_board_manifest",
            "sha256": "f25905c14d7b09fce256013646fb6863b05a0eb566151b930e890417048dca49"
          },
          {
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
            "role": "sacg_cctg_causal_slice",
            "sha256": "afa334f62758d48abaa13070c0d0e5d6a7e16a3224bad419af66752b9fc2436a"
          }
        ],
        "source_identity_sha256": "37ebe27a4d9293741131ba64432dc6e71a10c10570780d03dbec910eee555e66",
        "target_layer": "board_axi_ddr_wrapped_system"
      },
      "blockers": [
        "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
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
        "boundary_trace_failed_count": 5,
        "boundary_trace_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
        "boundary_trace_record_count": 63,
        "live_progress": {
          "history": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress_history.jsonl",
          "latest": {
            "adaptive_semantic_stall_evidence": {
              "failure_class": "intra_layer_spatial_pipeline_violation",
              "fixed_cycle_timeout": false,
              "fixed_wall_clock_timeout": false,
              "intra_layer_pipeline_violation_evidence": {
                "beats_per_input_token": 112,
                "completed_input_tokens": 16,
                "expected_input_tokens": 16,
                "failure_class": "intra_layer_spatial_pipeline_violation",
                "final_input_cycle": 20805737,
                "first_output_cycle": null,
                "fixed_cycle_timeout": false,
                "fixed_wall_clock_timeout": false,
                "observed_output_beats": 0,
                "output_ready": 1,
                "pipeline_contract": {
                  "all_planned_spatial_stages_same_cycle_required": false,
                  "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
                  "first_output_no_later_than_final_input": true,
                  "heterogeneous_stage_latency_supported": true,
                  "required": true,
                  "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
                  "stage_turnover_gaps_are_diagnostic": true,
                  "whole_sequence_operator_barriers_forbidden": true
                },
                "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
                "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
                "status": "proven_pipeline_violation",
                "target_output_beats": 1792
              },
              "last_semantic_event_cycle": 20811776,
              "latest_cycle": 20811776,
              "policy": {
                "all_target_inputs_and_ready_zero_output_required": true,
                "heartbeat_multiplier": 16384,
                "minimum_stall_snapshot_count": 8,
                "pipeline_contract_violation_is_not_a_timeout": true,
                "semantic_gap_multiplier": 32,
                "target_work_multiplier": 512
              },
              "proof_mode": "intra_layer_pipeline_contract",
              "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
              "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
              "status": "proven_semantic_stall"
            },
            "causal_event_tail": [
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20746240,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20739623,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1861,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7343,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20750336,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20739623,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1861,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7344,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20754432,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20739623,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1861,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7345,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20755540,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20755540,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1862,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7346,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 11
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20755541,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20755541,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1863,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7347,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 12
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 727,
                  "input_payload_digest": "fd80dc02",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933898,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933898
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20756183,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7348,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 12
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20758528,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7349,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20762624,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7350,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20766720,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7351,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20770816,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7352,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20772068,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772068,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1865,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7353,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 12
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20772069,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772069,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1866,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7354,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 13
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 783,
                  "input_payload_digest": "fedaaed5",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933954,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933954
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20772707,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7355,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 13
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20774912,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7356,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20779008,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7357,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20783104,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7358,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20787200,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7359,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20788596,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20788596,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1868,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7360,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 13
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20788597,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20788597,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1869,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7361,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 14
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 839,
                  "input_payload_digest": "fff090c1",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934010,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934010
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20789241,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7362,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 14
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20791296,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7363,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20795392,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7364,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20799488,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7365,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20803584,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7366,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20805124,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805124,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1871,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7367,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 14
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20805125,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805125,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1872,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7368,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 15
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 895,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20805737,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7369,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 15
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 895,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 0,
                  "residual1_enqueue_valid": 1,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 0
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 1,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 1,
                  "core_ingress_valid": 1,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 895,
                  "input_count": 1792,
                  "input_fire": 1,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805736,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 1,
                  "stage0_input_ready": 1,
                  "stage0_input_valid": 1,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 0,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 1,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 1,
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "cycle": 20805737,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_all_input_accepted_no_egress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7370,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage0_input_boundary_observation": {
                  "accepted": 1,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 1,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 1792,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 0,
                  "residual1_enqueue_valid": 0,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 0
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 0,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 0,
                  "core_ingress_valid": 0,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 896,
                  "input_count": 1792,
                  "input_fire": 0,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805737,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 0,
                  "stage0_input_ready": 0,
                  "stage0_input_valid": 0,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 0,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "cycle": 20805738,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_direct_core_ingress_complete_no_egress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7371,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage0_input_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 0,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 1680,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 1,
                  "residual1_enqueue_valid": 0,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 1
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 0,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 0,
                  "core_ingress_valid": 0,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 896,
                  "input_count": 1792,
                  "input_fire": 0,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805737,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 0,
                  "stage0_input_ready": 0,
                  "stage0_input_valid": 0,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 1,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "cycle": 20805791,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7372,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "stage0_input_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 0,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20807680,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7373,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20811776,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7374,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              }
            ],
            "committed_byte_count": 10259490,
            "first_stalled_boundary": "connected_kernel_input_to_output",
            "heartbeat_event_count": 5081,
            "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
            "intra_layer_pipeline_violation_evidence": {
              "beats_per_input_token": 112,
              "completed_input_tokens": 16,
              "expected_input_tokens": 16,
              "failure_class": "intra_layer_spatial_pipeline_violation",
              "final_input_cycle": 20805737,
              "first_output_cycle": null,
              "fixed_cycle_timeout": false,
              "fixed_wall_clock_timeout": false,
              "observed_output_beats": 0,
              "output_ready": 1,
              "pipeline_contract": {
                "all_planned_spatial_stages_same_cycle_required": false,
                "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
                "first_output_no_later_than_final_input": true,
                "heterogeneous_stage_latency_supported": true,
                "required": true,
                "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
                "stage_turnover_gaps_are_diagnostic": true,
                "whole_sequence_operator_barriers_forbidden": true
              },
              "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
              "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
              "status": "proven_pipeline_violation",
              "target_output_beats": 1792
            },
            "invalid_jsonl_records": [],
            "last_committed_progress_event": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20811776,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7374,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            "last_complete_record": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20811776,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7374,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            "last_cycle": 20811776,
            "last_semantic_progress_cycle": 20805737,
            "last_semantic_progress_event": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 895,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20805737,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7369,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 15
            },
            "latest_event_by_kind": {
              "heartbeat": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20811776,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7374,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              "lifecycle": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 0,
                  "input_payload_digest": "00000000",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 0,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 0
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 0,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 0,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 279,
                "event_kind": "lifecycle",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 0,
                "layer": 0,
                "phase": "calibrated_configure_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 0,
                "runtime_load_progress": {
                  "accepted_words": 0,
                  "target_words": 1056
                },
                "scheduler_state": 0,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 0,
                "stage_or_boundary": "compute_slot_axi.startup",
                "token": -1
              },
              "semantic_progress": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 895,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20805737,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7369,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 15
              },
              "stall_snapshot": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 1680,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 1,
                  "residual1_enqueue_valid": 0,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 1
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 0,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 0,
                  "core_ingress_valid": 0,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 896,
                  "input_count": 1792,
                  "input_fire": 0,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805737,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 0,
                  "stage0_input_ready": 0,
                  "stage0_input_valid": 0,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 1,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "cycle": 20805791,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7372,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "stage0_input_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 0,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              }
            },
            "latest_stall_snapshot": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 1680,
              "connected_kernel_inner_cone_observation": {
                "all_outer_ingress_accepted": true,
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "mlp_down_input_accepted_count": 607,
                "mlp_down_input_terminal_fire_count": 0,
                "mlp_down_output_accepted_count": 0,
                "mlp_down_output_ready": 1,
                "mlp_down_output_valid": 0,
                "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                "mlp_down_tail_probe_revision": 13,
                "mlp_gate_input_accepted_count": 112,
                "mlp_gate_input_ready": 1,
                "mlp_gate_input_valid": 0,
                "mlp_gate_output_accepted_count": 608,
                "mlp_gate_output_ready": 1,
                "mlp_gate_output_valid": 0,
                "mlp_mul_output_accepted_count": 607,
                "mlp_mul_output_ready": 1,
                "mlp_mul_output_valid": 0,
                "mlp_up_input_accepted_count": 112,
                "mlp_up_input_ready": 1,
                "mlp_up_input_valid": 0,
                "mlp_up_output_accepted_count": 608,
                "mlp_up_output_ready": 1,
                "mlp_up_output_valid": 0,
                "outer_input_accepted_count": 1792,
                "outer_output_accepted_count": 0,
                "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                "probe_revision": 2,
                "qkv_input_accepted_count": 1680,
                "qkv_input_ready": 0,
                "qkv_input_valid": 1,
                "residual1_enqueue_valid": 0,
                "residual2_enqueue_valid": 0,
                "rms2_input_valid": 1,
                "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                "stage0_accepted_count": 1680,
                "stage0_input_accepted_count": 1792,
                "stage0_ready": 0,
                "stage0_valid": 1
              },
              "connected_kernel_internal_pipeline_observation": {
                "axi_read_outstanding": 0,
                "axi_write_outstanding": 0,
                "axi_write_response_pending": false,
                "core_egress_accepted_count": 0,
                "core_egress_current_payload_digest": "xxxxxxxx",
                "core_egress_current_payload_unknown": true,
                "core_egress_fire": 0,
                "core_egress_last_accepted_payload_digest": "00000000",
                "core_egress_last_accepted_payload_unknown": true,
                "core_egress_next_beat": 0,
                "core_egress_next_token": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "core_ingress_current_payload_digest": "00b0baf9",
                "core_ingress_current_payload_unknown": false,
                "core_ingress_fire": 0,
                "core_ingress_last_accepted_payload_digest": "00b0baf9",
                "core_ingress_last_accepted_payload_unknown": false,
                "core_ingress_next_beat": 0,
                "core_ingress_next_token": 16,
                "core_ingress_ready": 0,
                "core_ingress_valid": 0,
                "cycles_since_first_output_token_complete": 0,
                "first_core_ingress_fire_cycle": 20572946,
                "first_core_ingress_precedes_start": true,
                "first_input_fire_cycle": 20572946,
                "first_output_fire_cycle": 0,
                "first_output_token_complete_cycle": 0,
                "first_start_cycle": 20572948,
                "frontier_id": "connected_kernel_input_to_output",
                "input_axi_index": 896,
                "input_count": 1792,
                "input_fire": 0,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "invocation_launched": 1,
                "kernel_reset": 0,
                "last_input_fire_cycle": 20805737,
                "last_output_fire_cycle": 0,
                "lifecycle_start_count": 1,
                "output_count": 0,
                "output_fifo_count": 0,
                "output_fifo_read_index": 0,
                "output_fifo_write_index": 0,
                "output_fire": 0,
                "output_ingress_half": 0,
                "output_pair_valid": 0,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_token_beat_count": 0,
                "output_valid": 0,
                "output_write_index": 0,
                "probe_id": "probe.connected_kernel_internal_pipeline.5",
                "probe_revision": 5,
                "rearm_pending": 0,
                "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                "source_marker": "connected_kernel_internal_pipeline_r5",
                "stage0_accepted_count": 1680,
                "stage0_current_payload_digest": "2df81214",
                "stage0_current_payload_unknown": false,
                "stage0_fire": 0,
                "stage0_input_accepted_count": 1792,
                "stage0_input_fire": 0,
                "stage0_input_ready": 0,
                "stage0_input_valid": 0,
                "stage0_last_accepted_payload_digest": "85d19430",
                "stage0_last_accepted_payload_unknown": false,
                "stage0_next_beat": 0,
                "stage0_next_token": 15,
                "stage0_ready": 0,
                "stage0_valid": 1,
                "start_edge_count": 1,
                "start_precedes_first_core_ingress": false,
                "start_to_core": 0
              },
              "core_ingress_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "kernel.core_ingress",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "00b0baf9",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "00b0baf9",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "cycle": 20805791,
              "event_kind": "stall_snapshot",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7372,
              "stage0_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1680,
                "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "2df81214",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "85d19430",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 1
              },
              "stage0_input_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                "contract": "valid_ready_order_preserved",
                "ready": 0,
                "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage_or_boundary": "connected_kernel_input_to_output",
              "token": 16
            },
            "live_transfer": {
              "final_full_snapshot": false,
              "local_byte_count": 10259490,
              "mode": "incremental_append",
              "prior_byte_count": 10231971,
              "received_byte_count": 27519
            },
            "local_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
            "native_loop_report": {
              "native_loop_detected": false,
              "status": "disabled"
            },
            "observed_unix_time": 1788942451.3104355,
            "policy": {
              "heartbeat_proves_clock_activity_not_semantic_progress": true,
              "native_vcs_loop_detection_required_for_zero_time_livelock": true,
              "observer_never_terminates_the_remote_job": true,
              "simulation_timeout_policy_unchanged": true,
              "unchanged_progress_alone_never_proves_zero_time_livelock": true,
              "wall_clock_elapsed_never_classifies_a_hardware_stall": true
            },
            "poll_attempt": 280,
            "process_state": "running",
            "progress_epoch": 1873,
            "progress_event_log_sha256": "21ebd8eec14dea13c4c32fcdb976232b812e5968471f21bb43559740a4523df3",
            "record_count": 7375,
            "remote_pid": 91927,
            "remote_progress_event_log": "reports/progress_event_log.jsonl",
            "remote_workdir": "/home/hyyuan/workspace/spatialaccagent_artifacts/board_vcs/spatialacc_qwen_agent_fast_run/a201b3dd8cf1_118918560173670353409359971486576231653191064420085494142782630",
            "schema_version": "spatialaccagent.board_live_progress_summary.v1",
            "semantic_progress_event_count": 1873,
            "silent_cycles": 6039,
            "simulation_time_probe": {
              "last_timestamp": null,
              "probes": [],
              "status": "pending"
            },
            "status": "observing",
            "terminal_event_seen": false,
            "testbench_observation_activity": {
              "other_testbench_file_io_callbacks": {
                "status": "not_directly_observable_from_runner"
              },
              "progress_file_io": {
                "committed_byte_count": 10259490,
                "complete_record_count": 7375,
                "last_committed_event": {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 896,
                    "input_payload_digest": "00b0baf9",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 0,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 934066,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 934066
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": -1,
                  "cycle": 20811776,
                  "event_kind": "heartbeat",
                  "evidence_kind": "board_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "last_semantic_progress_cycle": 20805737,
                  "layer": 0,
                  "phase": "semantic_progress_watch",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1873,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 30,
                  "schema_version": "spatialaccagent.board_progress_event.v1",
                  "semantic_progress": false,
                  "sequence": 7374,
                  "stage_or_boundary": "compute_slot_axi",
                  "token": -1
                },
                "write_observed_during_last_observation": true
              },
              "runner_process_snapshot": {
                "processes": [
                  {
                    "command": "bash",
                    "pgid": 91927,
                    "pid": 91927,
                    "ppid": 1,
                    "sid": 91927,
                    "state": "Ss"
                  },
                  {
                    "command": "bash",
                    "pgid": 91927,
                    "pid": 91957,
                    "ppid": 91927,
                    "sid": 91927,
                    "state": "S"
                  },
                  {
                    "command": "simv",
                    "pgid": 91927,
                    "pid": 91979,
                    "ppid": 91957,
                    "sid": 91927,
                    "state": "R"
                  }
                ],
                "reported_process_count": 3,
                "schema_version": "spatialaccagent.remote_process_snapshot.v1",
                "session_leader_pid": 91927,
                "simulator_like_process_observed": true,
                "simulator_process_commands": [
                  "simv"
                ],
                "status": "observed",
                "truncated": false
              },
              "schema_version": "spatialaccagent.testbench_observation_activity.v1",
              "simulator_process_observed": true,
              "testbench_observation_process": "simulator_process",
              "vcd_dumping": {
                "active_during_last_running_observation": false,
                "configured": false,
                "last_timestamp": null,
                "observed": false
              }
            },
            "trailing_partial_byte_count": 0,
            "validation_errors": [],
            "zero_time_livelock_evidence": {}
          },
          "raw_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
          "snapshot": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress.json",
          "status": "ready",
          "zero_time_livelock_evidence": {}
        },
        "progress_event_summary": {},
        "status": "trace_ready"
      },
      "diagnosis_status": "ready",
      "failure_class": "board_output_lifecycle_frontier_violation",
      "failure_evidence": {
        "adaptive_semantic_stall_evidence": {
          "failure_class": "intra_layer_spatial_pipeline_violation",
          "fixed_cycle_timeout": false,
          "fixed_wall_clock_timeout": false,
          "intra_layer_pipeline_violation_evidence": {
            "beats_per_input_token": 112,
            "completed_input_tokens": 16,
            "expected_input_tokens": 16,
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "final_input_cycle": 20805737,
            "first_output_cycle": null,
            "fixed_cycle_timeout": false,
            "fixed_wall_clock_timeout": false,
            "observed_output_beats": 0,
            "output_ready": 1,
            "pipeline_contract": {
              "all_planned_spatial_stages_same_cycle_required": false,
              "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
              "first_output_no_later_than_final_input": true,
              "heterogeneous_stage_latency_supported": true,
              "required": true,
              "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
              "stage_turnover_gaps_are_diagnostic": true,
              "whole_sequence_operator_barriers_forbidden": true
            },
            "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
            "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
            "status": "proven_pipeline_violation",
            "target_output_beats": 1792
          },
          "last_semantic_event_cycle": 20811776,
          "latest_cycle": 20811776,
          "policy": {
            "all_target_inputs_and_ready_zero_output_required": true,
            "heartbeat_multiplier": 16384,
            "minimum_stall_snapshot_count": 8,
            "pipeline_contract_violation_is_not_a_timeout": true,
            "semantic_gap_multiplier": 32,
            "target_work_multiplier": 512
          },
          "proof_mode": "intra_layer_pipeline_contract",
          "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
          "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
          "status": "proven_semantic_stall"
        },
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
          "duration_sec": 1887.3190881389892,
          "failure_class": null,
          "remote_state": "done",
          "returncode": 0,
          "status": "pass"
        },
        "failure_class": "board_output_lifecycle_frontier_violation",
        "first_real_error": "the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel",
        "intra_layer_pipeline_violation_evidence": {
          "beats_per_input_token": 112,
          "completed_input_tokens": 16,
          "expected_input_tokens": 16,
          "failure_class": "intra_layer_spatial_pipeline_violation",
          "final_input_cycle": 20805737,
          "first_output_cycle": null,
          "fixed_cycle_timeout": false,
          "fixed_wall_clock_timeout": false,
          "observed_output_beats": 0,
          "output_ready": 1,
          "pipeline_contract": {
            "all_planned_spatial_stages_same_cycle_required": false,
            "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
            "first_output_no_later_than_final_input": true,
            "heterogeneous_stage_latency_supported": true,
            "required": true,
            "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
            "stage_turnover_gaps_are_diagnostic": true,
            "whole_sequence_operator_barriers_forbidden": true
          },
          "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
          "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
          "status": "proven_pipeline_violation",
          "target_output_beats": 1792
        },
        "live_progress": {
          "history": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress_history.jsonl",
          "latest": {
            "adaptive_semantic_stall_evidence": {
              "failure_class": "intra_layer_spatial_pipeline_violation",
              "fixed_cycle_timeout": false,
              "fixed_wall_clock_timeout": false,
              "intra_layer_pipeline_violation_evidence": {
                "beats_per_input_token": 112,
                "completed_input_tokens": 16,
                "expected_input_tokens": 16,
                "failure_class": "intra_layer_spatial_pipeline_violation",
                "final_input_cycle": 20805737,
                "first_output_cycle": null,
                "fixed_cycle_timeout": false,
                "fixed_wall_clock_timeout": false,
                "observed_output_beats": 0,
                "output_ready": 1,
                "pipeline_contract": {
                  "all_planned_spatial_stages_same_cycle_required": false,
                  "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
                  "first_output_no_later_than_final_input": true,
                  "heterogeneous_stage_latency_supported": true,
                  "required": true,
                  "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
                  "stage_turnover_gaps_are_diagnostic": true,
                  "whole_sequence_operator_barriers_forbidden": true
                },
                "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
                "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
                "status": "proven_pipeline_violation",
                "target_output_beats": 1792
              },
              "last_semantic_event_cycle": 20811776,
              "latest_cycle": 20811776,
              "policy": {
                "all_target_inputs_and_ready_zero_output_required": true,
                "heartbeat_multiplier": 16384,
                "minimum_stall_snapshot_count": 8,
                "pipeline_contract_violation_is_not_a_timeout": true,
                "semantic_gap_multiplier": 32,
                "target_work_multiplier": 512
              },
              "proof_mode": "intra_layer_pipeline_contract",
              "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
              "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
              "status": "proven_semantic_stall"
            },
            "causal_event_tail": [
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20746240,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20739623,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1861,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7343,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20750336,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20739623,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1861,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7344,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20754432,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20739623,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1861,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7345,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20755540,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20755540,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1862,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7346,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 11
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 672,
                  "input_payload_digest": "82c71e6c",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933843,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933843
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20755541,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20755541,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1863,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7347,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 12
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 727,
                  "input_payload_digest": "fd80dc02",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933898,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933898
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20756183,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7348,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 12
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20758528,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7349,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20762624,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7350,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20766720,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7351,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20770816,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20756183,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1864,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7352,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20772068,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772068,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1865,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7353,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 12
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 728,
                  "input_payload_digest": "0321036f",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933899,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933899
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20772069,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772069,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1866,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7354,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 13
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 783,
                  "input_payload_digest": "fedaaed5",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933954,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933954
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20772707,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7355,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 13
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20774912,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7356,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20779008,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7357,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20783104,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7358,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20787200,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20772707,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1867,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7359,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20788596,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20788596,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1868,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7360,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 13
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 784,
                  "input_payload_digest": "ff5657fd",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 933955,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 933955
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20788597,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20788597,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1869,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7361,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 14
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 839,
                  "input_payload_digest": "fff090c1",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934010,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934010
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20789241,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7362,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 14
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20791296,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7363,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20795392,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7364,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20799488,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7365,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20803584,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20789241,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1870,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7366,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20805124,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805124,
                "layer": 0,
                "phase": "connected_kernel_stage0_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1871,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7367,
                "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "token": 14
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 840,
                  "input_payload_digest": "7d16f9de",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934011,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934011
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "cycle": 20805125,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805125,
                "layer": 0,
                "phase": "kernel_input_token_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1872,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 33,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7368,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 15
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 895,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20805737,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7369,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 15
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 895,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 0,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 0,
                  "residual1_enqueue_valid": 1,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 0
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 1,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 1,
                  "core_ingress_valid": 1,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 895,
                  "input_count": 1792,
                  "input_fire": 1,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805736,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 1,
                  "stage0_input_ready": 1,
                  "stage0_input_valid": 1,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 0,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 1,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 1,
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "cycle": 20805737,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_all_input_accepted_no_egress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7370,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage0_input_boundary_observation": {
                  "accepted": 1,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 1,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 1792,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 0,
                  "residual1_enqueue_valid": 0,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 0
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 0,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 0,
                  "core_ingress_valid": 0,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 896,
                  "input_count": 1792,
                  "input_fire": 0,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805737,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 0,
                  "stage0_input_ready": 0,
                  "stage0_input_valid": 0,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 0,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "cycle": 20805738,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_direct_core_ingress_complete_no_egress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7371,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage0_input_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 0,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 1680,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 1,
                  "residual1_enqueue_valid": 0,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 1
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 0,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 0,
                  "core_ingress_valid": 0,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 896,
                  "input_count": 1792,
                  "input_fire": 0,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805737,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 0,
                  "stage0_input_ready": 0,
                  "stage0_input_valid": 0,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 1,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "cycle": 20805791,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7372,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "stage0_input_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 0,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20807680,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7373,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20811776,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7374,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              }
            ],
            "committed_byte_count": 10259490,
            "first_stalled_boundary": "connected_kernel_input_to_output",
            "heartbeat_event_count": 5081,
            "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
            "intra_layer_pipeline_violation_evidence": {
              "beats_per_input_token": 112,
              "completed_input_tokens": 16,
              "expected_input_tokens": 16,
              "failure_class": "intra_layer_spatial_pipeline_violation",
              "final_input_cycle": 20805737,
              "first_output_cycle": null,
              "fixed_cycle_timeout": false,
              "fixed_wall_clock_timeout": false,
              "observed_output_beats": 0,
              "output_ready": 1,
              "pipeline_contract": {
                "all_planned_spatial_stages_same_cycle_required": false,
                "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
                "first_output_no_later_than_final_input": true,
                "heterogeneous_stage_latency_supported": true,
                "required": true,
                "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
                "stage_turnover_gaps_are_diagnostic": true,
                "whole_sequence_operator_barriers_forbidden": true
              },
              "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
              "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
              "status": "proven_pipeline_violation",
              "target_output_beats": 1792
            },
            "invalid_jsonl_records": [],
            "last_committed_progress_event": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20811776,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7374,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            "last_complete_record": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20811776,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7374,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            "last_cycle": 20811776,
            "last_semantic_progress_cycle": 20805737,
            "last_semantic_progress_event": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 895,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20805737,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7369,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 15
            },
            "latest_event_by_kind": {
              "heartbeat": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20811776,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7374,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              "lifecycle": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 0,
                  "input_payload_digest": "00000000",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 0,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 0
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 0,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 0,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 279,
                "event_kind": "lifecycle",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 0,
                "layer": 0,
                "phase": "calibrated_configure_start",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 0,
                "runtime_load_progress": {
                  "accepted_words": 0,
                  "target_words": 1056
                },
                "scheduler_state": 0,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 0,
                "stage_or_boundary": "compute_slot_axi.startup",
                "token": -1
              },
              "semantic_progress": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 1,
                  "input_axi_index": 895,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 1,
                  "input_valid": 1,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 111,
                "cycle": 20805737,
                "event_kind": "semantic_progress",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "kernel_input_token_complete",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 34,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": true,
                "sequence": 7369,
                "stage_or_boundary": "pipeline_boundary.block_input",
                "token": 15
              },
              "stall_snapshot": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 0,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 1,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": 1680,
                "connected_kernel_inner_cone_observation": {
                  "all_outer_ingress_accepted": true,
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "mlp_down_input_accepted_count": 607,
                  "mlp_down_input_terminal_fire_count": 0,
                  "mlp_down_output_accepted_count": 0,
                  "mlp_down_output_ready": 1,
                  "mlp_down_output_valid": 0,
                  "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                  "mlp_down_tail_probe_revision": 13,
                  "mlp_gate_input_accepted_count": 112,
                  "mlp_gate_input_ready": 1,
                  "mlp_gate_input_valid": 0,
                  "mlp_gate_output_accepted_count": 608,
                  "mlp_gate_output_ready": 1,
                  "mlp_gate_output_valid": 0,
                  "mlp_mul_output_accepted_count": 607,
                  "mlp_mul_output_ready": 1,
                  "mlp_mul_output_valid": 0,
                  "mlp_up_input_accepted_count": 112,
                  "mlp_up_input_ready": 1,
                  "mlp_up_input_valid": 0,
                  "mlp_up_output_accepted_count": 608,
                  "mlp_up_output_ready": 1,
                  "mlp_up_output_valid": 0,
                  "outer_input_accepted_count": 1792,
                  "outer_output_accepted_count": 0,
                  "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                  "probe_revision": 2,
                  "qkv_input_accepted_count": 1680,
                  "qkv_input_ready": 0,
                  "qkv_input_valid": 1,
                  "residual1_enqueue_valid": 0,
                  "residual2_enqueue_valid": 0,
                  "rms2_input_valid": 1,
                  "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                  "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                  "stage0_accepted_count": 1680,
                  "stage0_input_accepted_count": 1792,
                  "stage0_ready": 0,
                  "stage0_valid": 1
                },
                "connected_kernel_internal_pipeline_observation": {
                  "axi_read_outstanding": 0,
                  "axi_write_outstanding": 0,
                  "axi_write_response_pending": false,
                  "core_egress_accepted_count": 0,
                  "core_egress_current_payload_digest": "xxxxxxxx",
                  "core_egress_current_payload_unknown": true,
                  "core_egress_fire": 0,
                  "core_egress_last_accepted_payload_digest": "00000000",
                  "core_egress_last_accepted_payload_unknown": true,
                  "core_egress_next_beat": 0,
                  "core_egress_next_token": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "core_ingress_current_payload_digest": "00b0baf9",
                  "core_ingress_current_payload_unknown": false,
                  "core_ingress_fire": 0,
                  "core_ingress_last_accepted_payload_digest": "00b0baf9",
                  "core_ingress_last_accepted_payload_unknown": false,
                  "core_ingress_next_beat": 0,
                  "core_ingress_next_token": 16,
                  "core_ingress_ready": 0,
                  "core_ingress_valid": 0,
                  "cycles_since_first_output_token_complete": 0,
                  "first_core_ingress_fire_cycle": 20572946,
                  "first_core_ingress_precedes_start": true,
                  "first_input_fire_cycle": 20572946,
                  "first_output_fire_cycle": 0,
                  "first_output_token_complete_cycle": 0,
                  "first_start_cycle": 20572948,
                  "frontier_id": "connected_kernel_input_to_output",
                  "input_axi_index": 896,
                  "input_count": 1792,
                  "input_fire": 0,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "invocation_launched": 1,
                  "kernel_reset": 0,
                  "last_input_fire_cycle": 20805737,
                  "last_output_fire_cycle": 0,
                  "lifecycle_start_count": 1,
                  "output_count": 0,
                  "output_fifo_count": 0,
                  "output_fifo_read_index": 0,
                  "output_fifo_write_index": 0,
                  "output_fire": 0,
                  "output_ingress_half": 0,
                  "output_pair_valid": 0,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_token_beat_count": 0,
                  "output_valid": 0,
                  "output_write_index": 0,
                  "probe_id": "probe.connected_kernel_internal_pipeline.5",
                  "probe_revision": 5,
                  "rearm_pending": 0,
                  "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                  "source_marker": "connected_kernel_internal_pipeline_r5",
                  "stage0_accepted_count": 1680,
                  "stage0_current_payload_digest": "2df81214",
                  "stage0_current_payload_unknown": false,
                  "stage0_fire": 0,
                  "stage0_input_accepted_count": 1792,
                  "stage0_input_fire": 0,
                  "stage0_input_ready": 0,
                  "stage0_input_valid": 0,
                  "stage0_last_accepted_payload_digest": "85d19430",
                  "stage0_last_accepted_payload_unknown": false,
                  "stage0_next_beat": 0,
                  "stage0_next_token": 15,
                  "stage0_ready": 0,
                  "stage0_valid": 1,
                  "start_edge_count": 1,
                  "start_precedes_first_core_ingress": false,
                  "start_to_core": 0
                },
                "core_ingress_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "kernel.core_ingress",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "00b0baf9",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "00b0baf9",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "cycle": 20805791,
                "event_kind": "stall_snapshot",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7372,
                "stage0_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1680,
                  "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "contract": "valid_ready_order_preserved",
                  "current_payload_digest": "2df81214",
                  "current_payload_unknown": false,
                  "last_accepted_payload_digest": "85d19430",
                  "last_accepted_payload_unknown": false,
                  "ready": 0,
                  "status": "diagnostic_seed",
                  "valid": 1
                },
                "stage0_input_boundary_observation": {
                  "accepted": 0,
                  "accepted_count": 1792,
                  "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                  "contract": "valid_ready_order_preserved",
                  "ready": 0,
                  "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                  "status": "diagnostic_seed",
                  "valid": 0
                },
                "stage_or_boundary": "connected_kernel_input_to_output",
                "token": 16
              }
            },
            "latest_stall_snapshot": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 1680,
              "connected_kernel_inner_cone_observation": {
                "all_outer_ingress_accepted": true,
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "mlp_down_input_accepted_count": 607,
                "mlp_down_input_terminal_fire_count": 0,
                "mlp_down_output_accepted_count": 0,
                "mlp_down_output_ready": 1,
                "mlp_down_output_valid": 0,
                "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                "mlp_down_tail_probe_revision": 13,
                "mlp_gate_input_accepted_count": 112,
                "mlp_gate_input_ready": 1,
                "mlp_gate_input_valid": 0,
                "mlp_gate_output_accepted_count": 608,
                "mlp_gate_output_ready": 1,
                "mlp_gate_output_valid": 0,
                "mlp_mul_output_accepted_count": 607,
                "mlp_mul_output_ready": 1,
                "mlp_mul_output_valid": 0,
                "mlp_up_input_accepted_count": 112,
                "mlp_up_input_ready": 1,
                "mlp_up_input_valid": 0,
                "mlp_up_output_accepted_count": 608,
                "mlp_up_output_ready": 1,
                "mlp_up_output_valid": 0,
                "outer_input_accepted_count": 1792,
                "outer_output_accepted_count": 0,
                "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                "probe_revision": 2,
                "qkv_input_accepted_count": 1680,
                "qkv_input_ready": 0,
                "qkv_input_valid": 1,
                "residual1_enqueue_valid": 0,
                "residual2_enqueue_valid": 0,
                "rms2_input_valid": 1,
                "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                "stage0_accepted_count": 1680,
                "stage0_input_accepted_count": 1792,
                "stage0_ready": 0,
                "stage0_valid": 1
              },
              "connected_kernel_internal_pipeline_observation": {
                "axi_read_outstanding": 0,
                "axi_write_outstanding": 0,
                "axi_write_response_pending": false,
                "core_egress_accepted_count": 0,
                "core_egress_current_payload_digest": "xxxxxxxx",
                "core_egress_current_payload_unknown": true,
                "core_egress_fire": 0,
                "core_egress_last_accepted_payload_digest": "00000000",
                "core_egress_last_accepted_payload_unknown": true,
                "core_egress_next_beat": 0,
                "core_egress_next_token": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "core_ingress_current_payload_digest": "00b0baf9",
                "core_ingress_current_payload_unknown": false,
                "core_ingress_fire": 0,
                "core_ingress_last_accepted_payload_digest": "00b0baf9",
                "core_ingress_last_accepted_payload_unknown": false,
                "core_ingress_next_beat": 0,
                "core_ingress_next_token": 16,
                "core_ingress_ready": 0,
                "core_ingress_valid": 0,
                "cycles_since_first_output_token_complete": 0,
                "first_core_ingress_fire_cycle": 20572946,
                "first_core_ingress_precedes_start": true,
                "first_input_fire_cycle": 20572946,
                "first_output_fire_cycle": 0,
                "first_output_token_complete_cycle": 0,
                "first_start_cycle": 20572948,
                "frontier_id": "connected_kernel_input_to_output",
                "input_axi_index": 896,
                "input_count": 1792,
                "input_fire": 0,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "invocation_launched": 1,
                "kernel_reset": 0,
                "last_input_fire_cycle": 20805737,
                "last_output_fire_cycle": 0,
                "lifecycle_start_count": 1,
                "output_count": 0,
                "output_fifo_count": 0,
                "output_fifo_read_index": 0,
                "output_fifo_write_index": 0,
                "output_fire": 0,
                "output_ingress_half": 0,
                "output_pair_valid": 0,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_token_beat_count": 0,
                "output_valid": 0,
                "output_write_index": 0,
                "probe_id": "probe.connected_kernel_internal_pipeline.5",
                "probe_revision": 5,
                "rearm_pending": 0,
                "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                "source_marker": "connected_kernel_internal_pipeline_r5",
                "stage0_accepted_count": 1680,
                "stage0_current_payload_digest": "2df81214",
                "stage0_current_payload_unknown": false,
                "stage0_fire": 0,
                "stage0_input_accepted_count": 1792,
                "stage0_input_fire": 0,
                "stage0_input_ready": 0,
                "stage0_input_valid": 0,
                "stage0_last_accepted_payload_digest": "85d19430",
                "stage0_last_accepted_payload_unknown": false,
                "stage0_next_beat": 0,
                "stage0_next_token": 15,
                "stage0_ready": 0,
                "stage0_valid": 1,
                "start_edge_count": 1,
                "start_precedes_first_core_ingress": false,
                "start_to_core": 0
              },
              "core_ingress_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "kernel.core_ingress",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "00b0baf9",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "00b0baf9",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "cycle": 20805791,
              "event_kind": "stall_snapshot",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7372,
              "stage0_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1680,
                "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "2df81214",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "85d19430",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 1
              },
              "stage0_input_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                "contract": "valid_ready_order_preserved",
                "ready": 0,
                "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage_or_boundary": "connected_kernel_input_to_output",
              "token": 16
            },
            "live_transfer": {
              "final_full_snapshot": false,
              "local_byte_count": 10259490,
              "mode": "incremental_append",
              "prior_byte_count": 10231971,
              "received_byte_count": 27519
            },
            "local_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
            "native_loop_report": {
              "native_loop_detected": false,
              "status": "disabled"
            },
            "observed_unix_time": 1788942451.3104355,
            "policy": {
              "heartbeat_proves_clock_activity_not_semantic_progress": true,
              "native_vcs_loop_detection_required_for_zero_time_livelock": true,
              "observer_never_terminates_the_remote_job": true,
              "simulation_timeout_policy_unchanged": true,
              "unchanged_progress_alone_never_proves_zero_time_livelock": true,
              "wall_clock_elapsed_never_classifies_a_hardware_stall": true
            },
            "poll_attempt": 280,
            "process_state": "running",
            "progress_epoch": 1873,
            "progress_event_log_sha256": "21ebd8eec14dea13c4c32fcdb976232b812e5968471f21bb43559740a4523df3",
            "record_count": 7375,
            "remote_pid": 91927,
            "remote_progress_event_log": "reports/progress_event_log.jsonl",
            "remote_workdir": "/home/hyyuan/workspace/spatialaccagent_artifacts/board_vcs/spatialacc_qwen_agent_fast_run/a201b3dd8cf1_118918560173670353409359971486576231653191064420085494142782630",
            "schema_version": "spatialaccagent.board_live_progress_summary.v1",
            "semantic_progress_event_count": 1873,
            "silent_cycles": 6039,
            "simulation_time_probe": {
              "last_timestamp": null,
              "probes": [],
              "status": "pending"
            },
            "status": "observing",
            "terminal_event_seen": false,
            "testbench_observation_activity": {
              "other_testbench_file_io_callbacks": {
                "status": "not_directly_observable_from_runner"
              },
              "progress_file_io": {
                "committed_byte_count": 10259490,
                "complete_record_count": 7375,
                "last_committed_event": {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 896,
                    "input_payload_digest": "00b0baf9",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 0,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 934066,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 934066
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": -1,
                  "cycle": 20811776,
                  "event_kind": "heartbeat",
                  "evidence_kind": "board_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "last_semantic_progress_cycle": 20805737,
                  "layer": 0,
                  "phase": "semantic_progress_watch",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1873,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 30,
                  "schema_version": "spatialaccagent.board_progress_event.v1",
                  "semantic_progress": false,
                  "sequence": 7374,
                  "stage_or_boundary": "compute_slot_axi",
                  "token": -1
                },
                "write_observed_during_last_observation": true
              },
              "runner_process_snapshot": {
                "processes": [
                  {
                    "command": "bash",
                    "pgid": 91927,
                    "pid": 91927,
                    "ppid": 1,
                    "sid": 91927,
                    "state": "Ss"
                  },
                  {
                    "command": "bash",
                    "pgid": 91927,
                    "pid": 91957,
                    "ppid": 91927,
                    "sid": 91927,
                    "state": "S"
                  },
                  {
                    "command": "simv",
                    "pgid": 91927,
                    "pid": 91979,
                    "ppid": 91957,
                    "sid": 91927,
                    "state": "R"
                  }
                ],
                "reported_process_count": 3,
                "schema_version": "spatialaccagent.remote_process_snapshot.v1",
                "session_leader_pid": 91927,
                "simulator_like_process_observed": true,
                "simulator_process_commands": [
                  "simv"
                ],
                "status": "observed",
                "truncated": false
              },
              "schema_version": "spatialaccagent.testbench_observation_activity.v1",
              "simulator_process_observed": true,
              "testbench_observation_process": "simulator_process",
              "vcd_dumping": {
                "active_during_last_running_observation": false,
                "configured": false,
                "last_timestamp": null,
                "observed": false
              }
            },
            "trailing_partial_byte_count": 0,
            "validation_errors": [],
            "zero_time_livelock_evidence": {}
          },
          "raw_progress_event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/progress_events.jsonl",
          "snapshot": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/live_progress.json",
          "status": "ready",
          "zero_time_livelock_evidence": {}
        },
        "log_tail": "49 token=  12 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7354 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20772068 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7355 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20772069 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7356 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20772707 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7357 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20774912 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7358 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20779008 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7359 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20783104 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7360 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20787200 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524466 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524577 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7361 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20788596 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7362 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20788597 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7363 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20789241 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7364 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20791296 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7365 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20795392 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7366 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20799488 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7367 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20803584 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12540994 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12541105 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7368 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20805124 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7369 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20805125 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7370 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7371 event_kind=stall_snapshot phase=connected_kernel_all_input_accepted_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7372 event_kind=stall_snapshot phase=connected_kernel_direct_core_ingress_complete_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805738 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7373 event_kind=stall_snapshot phase=connected_kernel_stage0_valid_asserted_after_full_ingress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805791 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7374 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20807680 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7375 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20811776 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
        "progress_event_summary": {
          "adaptive_semantic_stall_evidence": {
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "fixed_cycle_timeout": false,
            "fixed_wall_clock_timeout": false,
            "intra_layer_pipeline_violation_evidence": {
              "beats_per_input_token": 112,
              "completed_input_tokens": 16,
              "expected_input_tokens": 16,
              "failure_class": "intra_layer_spatial_pipeline_violation",
              "final_input_cycle": 20805737,
              "first_output_cycle": null,
              "fixed_cycle_timeout": false,
              "fixed_wall_clock_timeout": false,
              "observed_output_beats": 0,
              "output_ready": 1,
              "pipeline_contract": {
                "all_planned_spatial_stages_same_cycle_required": false,
                "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
                "first_output_no_later_than_final_input": true,
                "heterogeneous_stage_latency_supported": true,
                "required": true,
                "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
                "stage_turnover_gaps_are_diagnostic": true,
                "whole_sequence_operator_barriers_forbidden": true
              },
              "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
              "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
              "status": "proven_pipeline_violation",
              "target_output_beats": 1792
            },
            "last_semantic_event_cycle": 20811776,
            "latest_cycle": 20811776,
            "policy": {
              "all_target_inputs_and_ready_zero_output_required": true,
              "heartbeat_multiplier": 16384,
              "minimum_stall_snapshot_count": 8,
              "pipeline_contract_violation_is_not_a_timeout": true,
              "semantic_gap_multiplier": 32,
              "target_work_multiplier": 512
            },
            "proof_mode": "intra_layer_pipeline_contract",
            "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
            "schema_version": "spatialaccagent.adaptive_semantic_stall_evidence.v1",
            "status": "proven_semantic_stall"
          },
          "causal_event_tail": [
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 672,
                "input_payload_digest": "82c71e6c",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933843,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933843
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20746240,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20739623,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1861,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7343,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 672,
                "input_payload_digest": "82c71e6c",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933843,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933843
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20750336,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20739623,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1861,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7344,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 672,
                "input_payload_digest": "82c71e6c",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933843,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933843
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20754432,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20739623,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1861,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7345,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 672,
                "input_payload_digest": "82c71e6c",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933843,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933843
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20755540,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20755540,
              "layer": 0,
              "phase": "connected_kernel_stage0_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1862,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7346,
              "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
              "token": 11
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 672,
                "input_payload_digest": "82c71e6c",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933843,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933843
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 0,
              "cycle": 20755541,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20755541,
              "layer": 0,
              "phase": "kernel_input_token_start",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1863,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7347,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 12
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 727,
                "input_payload_digest": "fd80dc02",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933898,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933898
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20756183,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20756183,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1864,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7348,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 12
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 728,
                "input_payload_digest": "0321036f",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933899,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933899
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20758528,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20756183,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1864,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7349,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 728,
                "input_payload_digest": "0321036f",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933899,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933899
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20762624,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20756183,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1864,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7350,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 728,
                "input_payload_digest": "0321036f",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933899,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933899
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20766720,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20756183,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1864,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7351,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 728,
                "input_payload_digest": "0321036f",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933899,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933899
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20770816,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20756183,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1864,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7352,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 728,
                "input_payload_digest": "0321036f",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933899,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933899
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20772068,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772068,
              "layer": 0,
              "phase": "connected_kernel_stage0_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1865,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7353,
              "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
              "token": 12
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 728,
                "input_payload_digest": "0321036f",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933899,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933899
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 0,
              "cycle": 20772069,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772069,
              "layer": 0,
              "phase": "kernel_input_token_start",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1866,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7354,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 13
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 783,
                "input_payload_digest": "fedaaed5",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933954,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933954
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20772707,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772707,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1867,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7355,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 13
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 784,
                "input_payload_digest": "ff5657fd",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933955,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933955
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20774912,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772707,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1867,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7356,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 784,
                "input_payload_digest": "ff5657fd",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933955,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933955
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20779008,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772707,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1867,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7357,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 784,
                "input_payload_digest": "ff5657fd",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933955,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933955
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20783104,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772707,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1867,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7358,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 784,
                "input_payload_digest": "ff5657fd",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933955,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933955
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20787200,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20772707,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1867,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7359,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 784,
                "input_payload_digest": "ff5657fd",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 933955,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933955
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20788596,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20788596,
              "layer": 0,
              "phase": "connected_kernel_stage0_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1868,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7360,
              "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
              "token": 13
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 784,
                "input_payload_digest": "ff5657fd",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 933955,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 933955
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 0,
              "cycle": 20788597,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20788597,
              "layer": 0,
              "phase": "kernel_input_token_start",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1869,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7361,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 14
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 839,
                "input_payload_digest": "fff090c1",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934010,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934010
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20789241,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20789241,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1870,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7362,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 14
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 840,
                "input_payload_digest": "7d16f9de",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934011,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934011
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20791296,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20789241,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1870,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7363,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 840,
                "input_payload_digest": "7d16f9de",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934011,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934011
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20795392,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20789241,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1870,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7364,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 840,
                "input_payload_digest": "7d16f9de",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934011,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934011
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20799488,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20789241,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1870,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7365,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 840,
                "input_payload_digest": "7d16f9de",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934011,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934011
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20803584,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20789241,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1870,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7366,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 840,
                "input_payload_digest": "7d16f9de",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934011,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934011
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20805124,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805124,
              "layer": 0,
              "phase": "connected_kernel_stage0_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1871,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7367,
              "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
              "token": 14
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 840,
                "input_payload_digest": "7d16f9de",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934011,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934011
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 0,
              "cycle": 20805125,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805125,
              "layer": 0,
              "phase": "kernel_input_token_start",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1872,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 33,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7368,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 15
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 895,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20805737,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7369,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 15
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 895,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 0,
              "connected_kernel_inner_cone_observation": {
                "all_outer_ingress_accepted": true,
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "mlp_down_input_accepted_count": 607,
                "mlp_down_input_terminal_fire_count": 0,
                "mlp_down_output_accepted_count": 0,
                "mlp_down_output_ready": 1,
                "mlp_down_output_valid": 0,
                "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                "mlp_down_tail_probe_revision": 13,
                "mlp_gate_input_accepted_count": 112,
                "mlp_gate_input_ready": 1,
                "mlp_gate_input_valid": 0,
                "mlp_gate_output_accepted_count": 608,
                "mlp_gate_output_ready": 1,
                "mlp_gate_output_valid": 0,
                "mlp_mul_output_accepted_count": 607,
                "mlp_mul_output_ready": 1,
                "mlp_mul_output_valid": 0,
                "mlp_up_input_accepted_count": 112,
                "mlp_up_input_ready": 1,
                "mlp_up_input_valid": 0,
                "mlp_up_output_accepted_count": 608,
                "mlp_up_output_ready": 1,
                "mlp_up_output_valid": 0,
                "outer_input_accepted_count": 1792,
                "outer_output_accepted_count": 0,
                "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                "probe_revision": 2,
                "qkv_input_accepted_count": 1680,
                "qkv_input_ready": 0,
                "qkv_input_valid": 0,
                "residual1_enqueue_valid": 1,
                "residual2_enqueue_valid": 0,
                "rms2_input_valid": 1,
                "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                "stage0_accepted_count": 1680,
                "stage0_input_accepted_count": 1792,
                "stage0_ready": 0,
                "stage0_valid": 0
              },
              "connected_kernel_internal_pipeline_observation": {
                "axi_read_outstanding": 0,
                "axi_write_outstanding": 0,
                "axi_write_response_pending": false,
                "core_egress_accepted_count": 0,
                "core_egress_current_payload_digest": "xxxxxxxx",
                "core_egress_current_payload_unknown": true,
                "core_egress_fire": 0,
                "core_egress_last_accepted_payload_digest": "00000000",
                "core_egress_last_accepted_payload_unknown": true,
                "core_egress_next_beat": 0,
                "core_egress_next_token": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "core_ingress_current_payload_digest": "00b0baf9",
                "core_ingress_current_payload_unknown": false,
                "core_ingress_fire": 1,
                "core_ingress_last_accepted_payload_digest": "00b0baf9",
                "core_ingress_last_accepted_payload_unknown": false,
                "core_ingress_next_beat": 0,
                "core_ingress_next_token": 16,
                "core_ingress_ready": 1,
                "core_ingress_valid": 1,
                "cycles_since_first_output_token_complete": 0,
                "first_core_ingress_fire_cycle": 20572946,
                "first_core_ingress_precedes_start": true,
                "first_input_fire_cycle": 20572946,
                "first_output_fire_cycle": 0,
                "first_output_token_complete_cycle": 0,
                "first_start_cycle": 20572948,
                "frontier_id": "connected_kernel_input_to_output",
                "input_axi_index": 895,
                "input_count": 1792,
                "input_fire": 1,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "invocation_launched": 1,
                "kernel_reset": 0,
                "last_input_fire_cycle": 20805736,
                "last_output_fire_cycle": 0,
                "lifecycle_start_count": 1,
                "output_count": 0,
                "output_fifo_count": 0,
                "output_fifo_read_index": 0,
                "output_fifo_write_index": 0,
                "output_fire": 0,
                "output_ingress_half": 0,
                "output_pair_valid": 0,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_token_beat_count": 0,
                "output_valid": 0,
                "output_write_index": 0,
                "probe_id": "probe.connected_kernel_internal_pipeline.5",
                "probe_revision": 5,
                "rearm_pending": 0,
                "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                "source_marker": "connected_kernel_internal_pipeline_r5",
                "stage0_accepted_count": 1680,
                "stage0_current_payload_digest": "2df81214",
                "stage0_current_payload_unknown": false,
                "stage0_fire": 0,
                "stage0_input_accepted_count": 1792,
                "stage0_input_fire": 1,
                "stage0_input_ready": 1,
                "stage0_input_valid": 1,
                "stage0_last_accepted_payload_digest": "85d19430",
                "stage0_last_accepted_payload_unknown": false,
                "stage0_next_beat": 0,
                "stage0_next_token": 15,
                "stage0_ready": 0,
                "stage0_valid": 0,
                "start_edge_count": 1,
                "start_precedes_first_core_ingress": false,
                "start_to_core": 0
              },
              "core_ingress_observation": {
                "accepted": 1,
                "accepted_count": 1792,
                "boundary_id": "kernel.core_ingress",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "00b0baf9",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "00b0baf9",
                "last_accepted_payload_unknown": false,
                "ready": 1,
                "status": "diagnostic_seed",
                "valid": 1
              },
              "cycle": 20805737,
              "event_kind": "stall_snapshot",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "connected_kernel_all_input_accepted_no_egress",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7370,
              "stage0_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1680,
                "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "2df81214",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "85d19430",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage0_input_boundary_observation": {
                "accepted": 1,
                "accepted_count": 1792,
                "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                "contract": "valid_ready_order_preserved",
                "ready": 1,
                "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                "status": "diagnostic_seed",
                "valid": 1
              },
              "stage_or_boundary": "connected_kernel_input_to_output",
              "token": 16
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 1792,
              "connected_kernel_inner_cone_observation": {
                "all_outer_ingress_accepted": true,
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "mlp_down_input_accepted_count": 607,
                "mlp_down_input_terminal_fire_count": 0,
                "mlp_down_output_accepted_count": 0,
                "mlp_down_output_ready": 1,
                "mlp_down_output_valid": 0,
                "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                "mlp_down_tail_probe_revision": 13,
                "mlp_gate_input_accepted_count": 112,
                "mlp_gate_input_ready": 1,
                "mlp_gate_input_valid": 0,
                "mlp_gate_output_accepted_count": 608,
                "mlp_gate_output_ready": 1,
                "mlp_gate_output_valid": 0,
                "mlp_mul_output_accepted_count": 607,
                "mlp_mul_output_ready": 1,
                "mlp_mul_output_valid": 0,
                "mlp_up_input_accepted_count": 112,
                "mlp_up_input_ready": 1,
                "mlp_up_input_valid": 0,
                "mlp_up_output_accepted_count": 608,
                "mlp_up_output_ready": 1,
                "mlp_up_output_valid": 0,
                "outer_input_accepted_count": 1792,
                "outer_output_accepted_count": 0,
                "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                "probe_revision": 2,
                "qkv_input_accepted_count": 1680,
                "qkv_input_ready": 0,
                "qkv_input_valid": 0,
                "residual1_enqueue_valid": 0,
                "residual2_enqueue_valid": 0,
                "rms2_input_valid": 1,
                "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                "stage0_accepted_count": 1680,
                "stage0_input_accepted_count": 1792,
                "stage0_ready": 0,
                "stage0_valid": 0
              },
              "connected_kernel_internal_pipeline_observation": {
                "axi_read_outstanding": 0,
                "axi_write_outstanding": 0,
                "axi_write_response_pending": false,
                "core_egress_accepted_count": 0,
                "core_egress_current_payload_digest": "xxxxxxxx",
                "core_egress_current_payload_unknown": true,
                "core_egress_fire": 0,
                "core_egress_last_accepted_payload_digest": "00000000",
                "core_egress_last_accepted_payload_unknown": true,
                "core_egress_next_beat": 0,
                "core_egress_next_token": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "core_ingress_current_payload_digest": "00b0baf9",
                "core_ingress_current_payload_unknown": false,
                "core_ingress_fire": 0,
                "core_ingress_last_accepted_payload_digest": "00b0baf9",
                "core_ingress_last_accepted_payload_unknown": false,
                "core_ingress_next_beat": 0,
                "core_ingress_next_token": 16,
                "core_ingress_ready": 0,
                "core_ingress_valid": 0,
                "cycles_since_first_output_token_complete": 0,
                "first_core_ingress_fire_cycle": 20572946,
                "first_core_ingress_precedes_start": true,
                "first_input_fire_cycle": 20572946,
                "first_output_fire_cycle": 0,
                "first_output_token_complete_cycle": 0,
                "first_start_cycle": 20572948,
                "frontier_id": "connected_kernel_input_to_output",
                "input_axi_index": 896,
                "input_count": 1792,
                "input_fire": 0,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "invocation_launched": 1,
                "kernel_reset": 0,
                "last_input_fire_cycle": 20805737,
                "last_output_fire_cycle": 0,
                "lifecycle_start_count": 1,
                "output_count": 0,
                "output_fifo_count": 0,
                "output_fifo_read_index": 0,
                "output_fifo_write_index": 0,
                "output_fire": 0,
                "output_ingress_half": 0,
                "output_pair_valid": 0,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_token_beat_count": 0,
                "output_valid": 0,
                "output_write_index": 0,
                "probe_id": "probe.connected_kernel_internal_pipeline.5",
                "probe_revision": 5,
                "rearm_pending": 0,
                "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                "source_marker": "connected_kernel_internal_pipeline_r5",
                "stage0_accepted_count": 1680,
                "stage0_current_payload_digest": "2df81214",
                "stage0_current_payload_unknown": false,
                "stage0_fire": 0,
                "stage0_input_accepted_count": 1792,
                "stage0_input_fire": 0,
                "stage0_input_ready": 0,
                "stage0_input_valid": 0,
                "stage0_last_accepted_payload_digest": "85d19430",
                "stage0_last_accepted_payload_unknown": false,
                "stage0_next_beat": 0,
                "stage0_next_token": 15,
                "stage0_ready": 0,
                "stage0_valid": 0,
                "start_edge_count": 1,
                "start_precedes_first_core_ingress": false,
                "start_to_core": 0
              },
              "core_ingress_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "kernel.core_ingress",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "00b0baf9",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "00b0baf9",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "cycle": 20805738,
              "event_kind": "stall_snapshot",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "connected_kernel_direct_core_ingress_complete_no_egress",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7371,
              "stage0_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1680,
                "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "2df81214",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "85d19430",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage0_input_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                "contract": "valid_ready_order_preserved",
                "ready": 0,
                "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage_or_boundary": "connected_kernel_input_to_output",
              "token": 16
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 1680,
              "connected_kernel_inner_cone_observation": {
                "all_outer_ingress_accepted": true,
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "mlp_down_input_accepted_count": 607,
                "mlp_down_input_terminal_fire_count": 0,
                "mlp_down_output_accepted_count": 0,
                "mlp_down_output_ready": 1,
                "mlp_down_output_valid": 0,
                "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                "mlp_down_tail_probe_revision": 13,
                "mlp_gate_input_accepted_count": 112,
                "mlp_gate_input_ready": 1,
                "mlp_gate_input_valid": 0,
                "mlp_gate_output_accepted_count": 608,
                "mlp_gate_output_ready": 1,
                "mlp_gate_output_valid": 0,
                "mlp_mul_output_accepted_count": 607,
                "mlp_mul_output_ready": 1,
                "mlp_mul_output_valid": 0,
                "mlp_up_input_accepted_count": 112,
                "mlp_up_input_ready": 1,
                "mlp_up_input_valid": 0,
                "mlp_up_output_accepted_count": 608,
                "mlp_up_output_ready": 1,
                "mlp_up_output_valid": 0,
                "outer_input_accepted_count": 1792,
                "outer_output_accepted_count": 0,
                "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                "probe_revision": 2,
                "qkv_input_accepted_count": 1680,
                "qkv_input_ready": 0,
                "qkv_input_valid": 1,
                "residual1_enqueue_valid": 0,
                "residual2_enqueue_valid": 0,
                "rms2_input_valid": 1,
                "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                "stage0_accepted_count": 1680,
                "stage0_input_accepted_count": 1792,
                "stage0_ready": 0,
                "stage0_valid": 1
              },
              "connected_kernel_internal_pipeline_observation": {
                "axi_read_outstanding": 0,
                "axi_write_outstanding": 0,
                "axi_write_response_pending": false,
                "core_egress_accepted_count": 0,
                "core_egress_current_payload_digest": "xxxxxxxx",
                "core_egress_current_payload_unknown": true,
                "core_egress_fire": 0,
                "core_egress_last_accepted_payload_digest": "00000000",
                "core_egress_last_accepted_payload_unknown": true,
                "core_egress_next_beat": 0,
                "core_egress_next_token": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "core_ingress_current_payload_digest": "00b0baf9",
                "core_ingress_current_payload_unknown": false,
                "core_ingress_fire": 0,
                "core_ingress_last_accepted_payload_digest": "00b0baf9",
                "core_ingress_last_accepted_payload_unknown": false,
                "core_ingress_next_beat": 0,
                "core_ingress_next_token": 16,
                "core_ingress_ready": 0,
                "core_ingress_valid": 0,
                "cycles_since_first_output_token_complete": 0,
                "first_core_ingress_fire_cycle": 20572946,
                "first_core_ingress_precedes_start": true,
                "first_input_fire_cycle": 20572946,
                "first_output_fire_cycle": 0,
                "first_output_token_complete_cycle": 0,
                "first_start_cycle": 20572948,
                "frontier_id": "connected_kernel_input_to_output",
                "input_axi_index": 896,
                "input_count": 1792,
                "input_fire": 0,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "invocation_launched": 1,
                "kernel_reset": 0,
                "last_input_fire_cycle": 20805737,
                "last_output_fire_cycle": 0,
                "lifecycle_start_count": 1,
                "output_count": 0,
                "output_fifo_count": 0,
                "output_fifo_read_index": 0,
                "output_fifo_write_index": 0,
                "output_fire": 0,
                "output_ingress_half": 0,
                "output_pair_valid": 0,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_token_beat_count": 0,
                "output_valid": 0,
                "output_write_index": 0,
                "probe_id": "probe.connected_kernel_internal_pipeline.5",
                "probe_revision": 5,
                "rearm_pending": 0,
                "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                "source_marker": "connected_kernel_internal_pipeline_r5",
                "stage0_accepted_count": 1680,
                "stage0_current_payload_digest": "2df81214",
                "stage0_current_payload_unknown": false,
                "stage0_fire": 0,
                "stage0_input_accepted_count": 1792,
                "stage0_input_fire": 0,
                "stage0_input_ready": 0,
                "stage0_input_valid": 0,
                "stage0_last_accepted_payload_digest": "85d19430",
                "stage0_last_accepted_payload_unknown": false,
                "stage0_next_beat": 0,
                "stage0_next_token": 15,
                "stage0_ready": 0,
                "stage0_valid": 1,
                "start_edge_count": 1,
                "start_precedes_first_core_ingress": false,
                "start_to_core": 0
              },
              "core_ingress_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "kernel.core_ingress",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "00b0baf9",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "00b0baf9",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "cycle": 20805791,
              "event_kind": "stall_snapshot",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7372,
              "stage0_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1680,
                "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "2df81214",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "85d19430",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 1
              },
              "stage0_input_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                "contract": "valid_ready_order_preserved",
                "ready": 0,
                "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage_or_boundary": "connected_kernel_input_to_output",
              "token": 16
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20807680,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7373,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20811776,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7374,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            }
          ],
          "first_stalled_boundary": "connected_kernel_input_to_output",
          "heartbeat_event_count": 5081,
          "intra_layer_pipeline_violation_evidence": {
            "beats_per_input_token": 112,
            "completed_input_tokens": 16,
            "expected_input_tokens": 16,
            "failure_class": "intra_layer_spatial_pipeline_violation",
            "final_input_cycle": 20805737,
            "first_output_cycle": null,
            "fixed_cycle_timeout": false,
            "fixed_wall_clock_timeout": false,
            "observed_output_beats": 0,
            "output_ready": 1,
            "pipeline_contract": {
              "all_planned_spatial_stages_same_cycle_required": false,
              "board_integration_contract_sha256": "b4dffb58a5f91736473c76713a43a009797143881094dabd5da6b3443b3df719",
              "first_output_no_later_than_final_input": true,
              "heterogeneous_stage_latency_supported": true,
              "required": true,
              "required_dataflow_edges_must_observe_different_tokens_in_flight": true,
              "stage_turnover_gaps_are_diagnostic": true,
              "whole_sequence_operator_barriers_forbidden": true
            },
            "reason": "all current-layer input tokens completed while the ready output boundary had accepted zero beats",
            "schema_version": "spatialaccagent.intra_layer_pipeline_violation_evidence.v1",
            "status": "proven_pipeline_violation",
            "target_output_beats": 1792
          },
          "last_committed_progress_event": {
            "activation_read_bank": "activation_ping_bank",
            "activation_write_bank": "activation_pong_bank",
            "active_boundary_observation": {
              "event_queue_quiescent": true,
              "input_accepted": 0,
              "input_axi_index": 896,
              "input_payload_digest": "00b0baf9",
              "input_payload_unknown": false,
              "input_ready": 0,
              "input_valid": 0,
              "output_accept_count": 0,
              "output_accepted": 0,
              "output_pair_valid": false,
              "output_payload_digest": "xxxxxxxx",
              "output_payload_unknown": true,
              "output_ready": 1,
              "output_valid": 0,
              "start": 0
            },
            "active_weight_bank": "weight_a",
            "axi_read": {
              "arready": 1,
              "arvalid": 0,
              "beats": 934066,
              "outstanding": 0,
              "pending_response": false,
              "rready": 0,
              "rvalid": 0,
              "transactions": 934066
            },
            "axi_write": {
              "awready": 0,
              "awvalid": 0,
              "beats": 467000,
              "bready": 0,
              "bvalid": 0,
              "outstanding": 0,
              "pending_response": false,
              "transactions": 467000,
              "wready": 0,
              "wvalid": 0
            },
            "beat": -1,
            "cycle": 20811776,
            "event_kind": "heartbeat",
            "evidence_kind": "board_progress",
            "final_writeback_progress": {
              "accepted_beats": 0,
              "target_beats": 896
            },
            "last_semantic_progress_cycle": 20805737,
            "layer": 0,
            "phase": "semantic_progress_watch",
            "prefetch_progress": {
              "accepted_beats": 0,
              "target_beats": 466104
            },
            "preload_weight_bank": "none",
            "progress_epoch": 1873,
            "runtime_load_progress": {
              "accepted_words": 1056,
              "target_words": 1056
            },
            "scheduler_state": 30,
            "schema_version": "spatialaccagent.board_progress_event.v1",
            "semantic_progress": false,
            "sequence": 7374,
            "stage_or_boundary": "compute_slot_axi",
            "token": -1
          },
          "last_complete_record": {
            "activation_read_bank": "activation_ping_bank",
            "activation_write_bank": "activation_pong_bank",
            "active_boundary_observation": {
              "event_queue_quiescent": true,
              "input_accepted": 0,
              "input_axi_index": 896,
              "input_payload_digest": "00b0baf9",
              "input_payload_unknown": false,
              "input_ready": 0,
              "input_valid": 0,
              "output_accept_count": 0,
              "output_accepted": 0,
              "output_pair_valid": false,
              "output_payload_digest": "xxxxxxxx",
              "output_payload_unknown": true,
              "output_ready": 1,
              "output_valid": 0,
              "start": 0
            },
            "active_weight_bank": "weight_a",
            "axi_read": {
              "arready": 1,
              "arvalid": 0,
              "beats": 934066,
              "outstanding": 0,
              "pending_response": false,
              "rready": 0,
              "rvalid": 0,
              "transactions": 934066
            },
            "axi_write": {
              "awready": 0,
              "awvalid": 0,
              "beats": 467000,
              "bready": 0,
              "bvalid": 0,
              "outstanding": 0,
              "pending_response": false,
              "transactions": 467000,
              "wready": 0,
              "wvalid": 0
            },
            "beat": -1,
            "cycle": 20811776,
            "event_kind": "heartbeat",
            "evidence_kind": "board_progress",
            "final_writeback_progress": {
              "accepted_beats": 0,
              "target_beats": 896
            },
            "last_semantic_progress_cycle": 20805737,
            "layer": 0,
            "phase": "semantic_progress_watch",
            "prefetch_progress": {
              "accepted_beats": 0,
              "target_beats": 466104
            },
            "preload_weight_bank": "none",
            "progress_epoch": 1873,
            "runtime_load_progress": {
              "accepted_words": 1056,
              "target_words": 1056
            },
            "scheduler_state": 30,
            "schema_version": "spatialaccagent.board_progress_event.v1",
            "semantic_progress": false,
            "sequence": 7374,
            "stage_or_boundary": "compute_slot_axi",
            "token": -1
          },
          "last_cycle": 20811776,
          "last_semantic_progress_cycle": 20805737,
          "last_semantic_progress_event": {
            "activation_read_bank": "activation_ping_bank",
            "activation_write_bank": "activation_pong_bank",
            "active_boundary_observation": {
              "event_queue_quiescent": true,
              "input_accepted": 1,
              "input_axi_index": 895,
              "input_payload_digest": "00b0baf9",
              "input_payload_unknown": false,
              "input_ready": 1,
              "input_valid": 1,
              "output_accept_count": 0,
              "output_accepted": 0,
              "output_pair_valid": false,
              "output_payload_digest": "xxxxxxxx",
              "output_payload_unknown": true,
              "output_ready": 1,
              "output_valid": 0,
              "start": 0
            },
            "active_weight_bank": "weight_a",
            "axi_read": {
              "arready": 0,
              "arvalid": 0,
              "beats": 934066,
              "outstanding": 0,
              "pending_response": false,
              "rready": 0,
              "rvalid": 0,
              "transactions": 934066
            },
            "axi_write": {
              "awready": 1,
              "awvalid": 0,
              "beats": 467000,
              "bready": 0,
              "bvalid": 0,
              "outstanding": 0,
              "pending_response": false,
              "transactions": 467000,
              "wready": 0,
              "wvalid": 0
            },
            "beat": 111,
            "cycle": 20805737,
            "event_kind": "semantic_progress",
            "evidence_kind": "board_progress",
            "final_writeback_progress": {
              "accepted_beats": 0,
              "target_beats": 896
            },
            "last_semantic_progress_cycle": 20805737,
            "layer": 0,
            "phase": "kernel_input_token_complete",
            "prefetch_progress": {
              "accepted_beats": 0,
              "target_beats": 466104
            },
            "preload_weight_bank": "none",
            "progress_epoch": 1873,
            "runtime_load_progress": {
              "accepted_words": 1056,
              "target_words": 1056
            },
            "scheduler_state": 34,
            "schema_version": "spatialaccagent.board_progress_event.v1",
            "semantic_progress": true,
            "sequence": 7369,
            "stage_or_boundary": "pipeline_boundary.block_input",
            "token": 15
          },
          "latest_event_by_kind": {
            "heartbeat": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 0,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 20811776,
              "event_kind": "heartbeat",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "semantic_progress_watch",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7374,
              "stage_or_boundary": "compute_slot_axi",
              "token": -1
            },
            "lifecycle": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 0,
                "input_payload_digest": "00000000",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 0,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 1,
                "arvalid": 0,
                "beats": 0,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 0
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 0,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 0,
                "wready": 0,
                "wvalid": 0
              },
              "beat": -1,
              "cycle": 279,
              "event_kind": "lifecycle",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 0,
              "layer": 0,
              "phase": "calibrated_configure_start",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 0,
              "runtime_load_progress": {
                "accepted_words": 0,
                "target_words": 1056
              },
              "scheduler_state": 0,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 0,
              "stage_or_boundary": "compute_slot_axi.startup",
              "token": -1
            },
            "semantic_progress": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 1,
                "input_axi_index": 895,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 1,
                "input_valid": 1,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 111,
              "cycle": 20805737,
              "event_kind": "semantic_progress",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "kernel_input_token_complete",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 34,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": true,
              "sequence": 7369,
              "stage_or_boundary": "pipeline_boundary.block_input",
              "token": 15
            },
            "stall_snapshot": {
              "activation_read_bank": "activation_ping_bank",
              "activation_write_bank": "activation_pong_bank",
              "active_boundary_observation": {
                "event_queue_quiescent": true,
                "input_accepted": 0,
                "input_axi_index": 896,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "output_accept_count": 0,
                "output_accepted": 0,
                "output_pair_valid": false,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_valid": 0,
                "start": 0
              },
              "active_weight_bank": "weight_a",
              "axi_read": {
                "arready": 0,
                "arvalid": 0,
                "beats": 934066,
                "outstanding": 0,
                "pending_response": false,
                "rready": 0,
                "rvalid": 0,
                "transactions": 934066
              },
              "axi_write": {
                "awready": 1,
                "awvalid": 0,
                "beats": 467000,
                "bready": 0,
                "bvalid": 0,
                "outstanding": 0,
                "pending_response": false,
                "transactions": 467000,
                "wready": 0,
                "wvalid": 0
              },
              "beat": 1680,
              "connected_kernel_inner_cone_observation": {
                "all_outer_ingress_accepted": true,
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "mlp_down_input_accepted_count": 607,
                "mlp_down_input_terminal_fire_count": 0,
                "mlp_down_output_accepted_count": 0,
                "mlp_down_output_ready": 1,
                "mlp_down_output_valid": 0,
                "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
                "mlp_down_tail_probe_revision": 13,
                "mlp_gate_input_accepted_count": 112,
                "mlp_gate_input_ready": 1,
                "mlp_gate_input_valid": 0,
                "mlp_gate_output_accepted_count": 608,
                "mlp_gate_output_ready": 1,
                "mlp_gate_output_valid": 0,
                "mlp_mul_output_accepted_count": 607,
                "mlp_mul_output_ready": 1,
                "mlp_mul_output_valid": 0,
                "mlp_up_input_accepted_count": 112,
                "mlp_up_input_ready": 1,
                "mlp_up_input_valid": 0,
                "mlp_up_output_accepted_count": 608,
                "mlp_up_output_ready": 1,
                "mlp_up_output_valid": 0,
                "outer_input_accepted_count": 1792,
                "outer_output_accepted_count": 0,
                "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
                "probe_revision": 2,
                "qkv_input_accepted_count": 1680,
                "qkv_input_ready": 0,
                "qkv_input_valid": 1,
                "residual1_enqueue_valid": 0,
                "residual2_enqueue_valid": 0,
                "rms2_input_valid": 1,
                "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
                "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
                "stage0_accepted_count": 1680,
                "stage0_input_accepted_count": 1792,
                "stage0_ready": 0,
                "stage0_valid": 1
              },
              "connected_kernel_internal_pipeline_observation": {
                "axi_read_outstanding": 0,
                "axi_write_outstanding": 0,
                "axi_write_response_pending": false,
                "core_egress_accepted_count": 0,
                "core_egress_current_payload_digest": "xxxxxxxx",
                "core_egress_current_payload_unknown": true,
                "core_egress_fire": 0,
                "core_egress_last_accepted_payload_digest": "00000000",
                "core_egress_last_accepted_payload_unknown": true,
                "core_egress_next_beat": 0,
                "core_egress_next_token": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792,
                "core_ingress_current_payload_digest": "00b0baf9",
                "core_ingress_current_payload_unknown": false,
                "core_ingress_fire": 0,
                "core_ingress_last_accepted_payload_digest": "00b0baf9",
                "core_ingress_last_accepted_payload_unknown": false,
                "core_ingress_next_beat": 0,
                "core_ingress_next_token": 16,
                "core_ingress_ready": 0,
                "core_ingress_valid": 0,
                "cycles_since_first_output_token_complete": 0,
                "first_core_ingress_fire_cycle": 20572946,
                "first_core_ingress_precedes_start": true,
                "first_input_fire_cycle": 20572946,
                "first_output_fire_cycle": 0,
                "first_output_token_complete_cycle": 0,
                "first_start_cycle": 20572948,
                "frontier_id": "connected_kernel_input_to_output",
                "input_axi_index": 896,
                "input_count": 1792,
                "input_fire": 0,
                "input_payload_digest": "00b0baf9",
                "input_payload_unknown": false,
                "input_ready": 0,
                "input_valid": 0,
                "invocation_launched": 1,
                "kernel_reset": 0,
                "last_input_fire_cycle": 20805737,
                "last_output_fire_cycle": 0,
                "lifecycle_start_count": 1,
                "output_count": 0,
                "output_fifo_count": 0,
                "output_fifo_read_index": 0,
                "output_fifo_write_index": 0,
                "output_fire": 0,
                "output_ingress_half": 0,
                "output_pair_valid": 0,
                "output_payload_digest": "xxxxxxxx",
                "output_payload_unknown": true,
                "output_ready": 1,
                "output_token_beat_count": 0,
                "output_valid": 0,
                "output_write_index": 0,
                "probe_id": "probe.connected_kernel_internal_pipeline.5",
                "probe_revision": 5,
                "rearm_pending": 0,
                "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
                "source_marker": "connected_kernel_internal_pipeline_r5",
                "stage0_accepted_count": 1680,
                "stage0_current_payload_digest": "2df81214",
                "stage0_current_payload_unknown": false,
                "stage0_fire": 0,
                "stage0_input_accepted_count": 1792,
                "stage0_input_fire": 0,
                "stage0_input_ready": 0,
                "stage0_input_valid": 0,
                "stage0_last_accepted_payload_digest": "85d19430",
                "stage0_last_accepted_payload_unknown": false,
                "stage0_next_beat": 0,
                "stage0_next_token": 15,
                "stage0_ready": 0,
                "stage0_valid": 1,
                "start_edge_count": 1,
                "start_precedes_first_core_ingress": false,
                "start_to_core": 0
              },
              "core_ingress_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "kernel.core_ingress",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "00b0baf9",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "00b0baf9",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 0
              },
              "cycle": 20805791,
              "event_kind": "stall_snapshot",
              "evidence_kind": "board_progress",
              "final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "last_semantic_progress_cycle": 20805737,
              "layer": 0,
              "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
              "prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "preload_weight_bank": "none",
              "progress_epoch": 1873,
              "runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "scheduler_state": 30,
              "schema_version": "spatialaccagent.board_progress_event.v1",
              "semantic_progress": false,
              "sequence": 7372,
              "stage0_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1680,
                "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                "contract": "valid_ready_order_preserved",
                "current_payload_digest": "2df81214",
                "current_payload_unknown": false,
                "last_accepted_payload_digest": "85d19430",
                "last_accepted_payload_unknown": false,
                "ready": 0,
                "status": "diagnostic_seed",
                "valid": 1
              },
              "stage0_input_boundary_observation": {
                "accepted": 0,
                "accepted_count": 1792,
                "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
                "contract": "valid_ready_order_preserved",
                "ready": 0,
                "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
                "status": "diagnostic_seed",
                "valid": 0
              },
              "stage_or_boundary": "connected_kernel_input_to_output",
              "token": 16
            }
          },
          "latest_stall_snapshot": {
            "activation_read_bank": "activation_ping_bank",
            "activation_write_bank": "activation_pong_bank",
            "active_boundary_observation": {
              "event_queue_quiescent": true,
              "input_accepted": 0,
              "input_axi_index": 896,
              "input_payload_digest": "00b0baf9",
              "input_payload_unknown": false,
              "input_ready": 0,
              "input_valid": 0,
              "output_accept_count": 0,
              "output_accepted": 0,
              "output_pair_valid": false,
              "output_payload_digest": "xxxxxxxx",
              "output_payload_unknown": true,
              "output_ready": 1,
              "output_valid": 0,
              "start": 0
            },
            "active_weight_bank": "weight_a",
            "axi_read": {
              "arready": 0,
              "arvalid": 0,
              "beats": 934066,
              "outstanding": 0,
              "pending_response": false,
              "rready": 0,
              "rvalid": 0,
              "transactions": 934066
            },
            "axi_write": {
              "awready": 1,
              "awvalid": 0,
              "beats": 467000,
              "bready": 0,
              "bvalid": 0,
              "outstanding": 0,
              "pending_response": false,
              "transactions": 467000,
              "wready": 0,
              "wvalid": 0
            },
            "beat": 1680,
            "connected_kernel_inner_cone_observation": {
              "all_outer_ingress_accepted": true,
              "core_egress_accepted_count": 0,
              "core_egress_ready": 1,
              "core_egress_valid": 0,
              "core_ingress_accepted_count": 1792,
              "mlp_down_input_accepted_count": 607,
              "mlp_down_input_terminal_fire_count": 0,
              "mlp_down_output_accepted_count": 0,
              "mlp_down_output_ready": 1,
              "mlp_down_output_valid": 0,
              "mlp_down_tail_probe_id": "probe.connected_kernel_mlp_down_tail_at_full_ingress.13",
              "mlp_down_tail_probe_revision": 13,
              "mlp_gate_input_accepted_count": 112,
              "mlp_gate_input_ready": 1,
              "mlp_gate_input_valid": 0,
              "mlp_gate_output_accepted_count": 608,
              "mlp_gate_output_ready": 1,
              "mlp_gate_output_valid": 0,
              "mlp_mul_output_accepted_count": 607,
              "mlp_mul_output_ready": 1,
              "mlp_mul_output_valid": 0,
              "mlp_up_input_accepted_count": 112,
              "mlp_up_input_ready": 1,
              "mlp_up_input_valid": 0,
              "mlp_up_output_accepted_count": 608,
              "mlp_up_output_ready": 1,
              "mlp_up_output_valid": 0,
              "outer_input_accepted_count": 1792,
              "outer_output_accepted_count": 0,
              "probe_id": "probe.connected_kernel_inner_cone_after_full_ingress.2",
              "probe_revision": 2,
              "qkv_input_accepted_count": 1680,
              "qkv_input_ready": 0,
              "qkv_input_valid": 1,
              "residual1_enqueue_valid": 0,
              "residual2_enqueue_valid": 0,
              "rms2_input_valid": 1,
              "schema_version": "spatialaccagent.connected_kernel_inner_cone_observation.v1",
              "source_marker": "connected_kernel_inner_cone_after_full_ingress_r2",
              "stage0_accepted_count": 1680,
              "stage0_input_accepted_count": 1792,
              "stage0_ready": 0,
              "stage0_valid": 1
            },
            "connected_kernel_internal_pipeline_observation": {
              "axi_read_outstanding": 0,
              "axi_write_outstanding": 0,
              "axi_write_response_pending": false,
              "core_egress_accepted_count": 0,
              "core_egress_current_payload_digest": "xxxxxxxx",
              "core_egress_current_payload_unknown": true,
              "core_egress_fire": 0,
              "core_egress_last_accepted_payload_digest": "00000000",
              "core_egress_last_accepted_payload_unknown": true,
              "core_egress_next_beat": 0,
              "core_egress_next_token": 0,
              "core_egress_ready": 1,
              "core_egress_valid": 0,
              "core_ingress_accepted_count": 1792,
              "core_ingress_current_payload_digest": "00b0baf9",
              "core_ingress_current_payload_unknown": false,
              "core_ingress_fire": 0,
              "core_ingress_last_accepted_payload_digest": "00b0baf9",
              "core_ingress_last_accepted_payload_unknown": false,
              "core_ingress_next_beat": 0,
              "core_ingress_next_token": 16,
              "core_ingress_ready": 0,
              "core_ingress_valid": 0,
              "cycles_since_first_output_token_complete": 0,
              "first_core_ingress_fire_cycle": 20572946,
              "first_core_ingress_precedes_start": true,
              "first_input_fire_cycle": 20572946,
              "first_output_fire_cycle": 0,
              "first_output_token_complete_cycle": 0,
              "first_start_cycle": 20572948,
              "frontier_id": "connected_kernel_input_to_output",
              "input_axi_index": 896,
              "input_count": 1792,
              "input_fire": 0,
              "input_payload_digest": "00b0baf9",
              "input_payload_unknown": false,
              "input_ready": 0,
              "input_valid": 0,
              "invocation_launched": 1,
              "kernel_reset": 0,
              "last_input_fire_cycle": 20805737,
              "last_output_fire_cycle": 0,
              "lifecycle_start_count": 1,
              "output_count": 0,
              "output_fifo_count": 0,
              "output_fifo_read_index": 0,
              "output_fifo_write_index": 0,
              "output_fire": 0,
              "output_ingress_half": 0,
              "output_pair_valid": 0,
              "output_payload_digest": "xxxxxxxx",
              "output_payload_unknown": true,
              "output_ready": 1,
              "output_token_beat_count": 0,
              "output_valid": 0,
              "output_write_index": 0,
              "probe_id": "probe.connected_kernel_internal_pipeline.5",
              "probe_revision": 5,
              "rearm_pending": 0,
              "schema_version": "spatialaccagent.connected_kernel_internal_pipeline_observation.v1",
              "source_marker": "connected_kernel_internal_pipeline_r5",
              "stage0_accepted_count": 1680,
              "stage0_current_payload_digest": "2df81214",
              "stage0_current_payload_unknown": false,
              "stage0_fire": 0,
              "stage0_input_accepted_count": 1792,
              "stage0_input_fire": 0,
              "stage0_input_ready": 0,
              "stage0_input_valid": 0,
              "stage0_last_accepted_payload_digest": "85d19430",
              "stage0_last_accepted_payload_unknown": false,
              "stage0_next_beat": 0,
              "stage0_next_token": 15,
              "stage0_ready": 0,
              "stage0_valid": 1,
              "start_edge_count": 1,
              "start_precedes_first_core_ingress": false,
              "start_to_core": 0
            },
            "core_ingress_observation": {
              "accepted": 0,
              "accepted_count": 1792,
              "boundary_id": "kernel.core_ingress",
              "contract": "valid_ready_order_preserved",
              "current_payload_digest": "00b0baf9",
              "current_payload_unknown": false,
              "last_accepted_payload_digest": "00b0baf9",
              "last_accepted_payload_unknown": false,
              "ready": 0,
              "status": "diagnostic_seed",
              "valid": 0
            },
            "cycle": 20805791,
            "event_kind": "stall_snapshot",
            "evidence_kind": "board_progress",
            "final_writeback_progress": {
              "accepted_beats": 0,
              "target_beats": 896
            },
            "last_semantic_progress_cycle": 20805737,
            "layer": 0,
            "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
            "prefetch_progress": {
              "accepted_beats": 0,
              "target_beats": 466104
            },
            "preload_weight_bank": "none",
            "progress_epoch": 1873,
            "runtime_load_progress": {
              "accepted_words": 1056,
              "target_words": 1056
            },
            "scheduler_state": 30,
            "schema_version": "spatialaccagent.board_progress_event.v1",
            "semantic_progress": false,
            "sequence": 7372,
            "stage0_boundary_observation": {
              "accepted": 0,
              "accepted_count": 1680,
              "boundary_id": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
              "contract": "valid_ready_order_preserved",
              "current_payload_digest": "2df81214",
              "current_payload_unknown": false,
              "last_accepted_payload_digest": "85d19430",
              "last_accepted_payload_unknown": false,
              "ready": 0,
              "status": "diagnostic_seed",
              "valid": 1
            },
            "stage0_input_boundary_observation": {
              "accepted": 0,
              "accepted_count": 1792,
              "boundary_id": "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
              "contract": "valid_ready_order_preserved",
              "ready": 0,
              "source_scope": "dut.spatialacc_single_kernel.core.rms1.io_in",
              "status": "diagnostic_seed",
              "valid": 0
            },
            "stage_or_boundary": "connected_kernel_input_to_output",
            "token": 16
          },
          "policy": {
            "heartbeat_proves_clock_activity_not_semantic_progress": true,
            "wall_clock_elapsed_never_classifies_a_hardware_stall": true
          },
          "progress_epoch": 1873,
          "record_count": 7375,
          "schema_version": "spatialaccagent.board_live_progress_summary.v1",
          "semantic_progress_event_count": 1873,
          "silent_cycles": 6039,
          "status": "observing",
          "terminal_event_seen": false,
          "validation_errors": []
        },
        "related_source_ids": [
          "certified_kernel.0058.9f6f7cd74bfb7999",
          "certified_kernel.0059.fda2ea5872b1567e",
          "certified_kernel.0060.14f9fb972e98522e",
          "certified_kernel.0061.6c89abc693126950",
          "certified_kernel.0062.d3e25305dc97cddd",
          "generated-board-source:compute_slot_adapter",
          "generated-board-source:exact_multilayer_tb",
          "generated-board-source:axi_protocol_monitor"
        ],
        "repair_scope": "board_rtl_or_testbench",
        "runner_phase": "remote_vcs",
        "sacg_cctg_causal_slice": {
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
          "sha256": "afa334f62758d48abaa13070c0d0e5d6a7e16a3224bad419af66752b9fc2436a",
          "value": {
            "causal_graph_slice": {
              "cctg_boundaries": [],
              "cctg_causal_paths": [
                {
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
                }
              ],
              "sacg_constraints": [],
              "sacg_edges": [],
              "sacg_nodes": []
            },
            "earliest_unproven_frontier": {
              "causal_domain": "connected_kernel_boundary",
              "failed_boundary_ids": [
                "connected_kernel_input_to_output"
              ],
              "failure_class": "board_output_lifecycle_frontier_violation",
              "frontier_id": "cctg_boundary_invariant_failure",
              "prior_runtime_frontier": {
                "causal_domain": "connected_kernel_boundary",
                "failure_class": "board_output_lifecycle_frontier_violation",
                "frontier_id": "connected_kernel_input_to_output",
                "observed": {
                  "active_layer": 0,
                  "beats_per_token_inferred_from_trace": 112,
                  "expected_input_tokens": null,
                  "expected_output_tokens": null,
                  "input_completed": 16,
                  "input_started": 16,
                  "kernel_start": 1,
                  "output_completed": 0,
                  "output_started": 0,
                  "rearmed": 0,
                  "runtime_load_complete": 1,
                  "runtime_load_start": 1,
                  "target_layer_count": 1
                },
                "reason": "complete kernel input was observed but no kernel output token started",
                "status": "earliest_unproven"
              },
              "reason": "the current trace explicitly failed one or more CCTG boundary invariants",
              "status": "earliest_unproven"
            },
            "evidence_binding": {
              "cctg_boundary_contracts": {
                "byte_count": 19384,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_contracts.json",
                "sha256": "1847138114a3f5a3e5e7b4c427948dfd4b2aa152a7af6da55f2ee3567359dc3c"
              },
              "executed_manifest": {
                "byte_count": 375884,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_executed_manifest.json",
                "sha256": "f25905c14d7b09fce256013646fb6863b05a0eb566151b930e890417048dca49"
              },
              "progress_event_log": {
                "byte_count": 10259490,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/progress_event_log.jsonl",
                "sha256": "21ebd8eec14dea13c4c32fcdb976232b812e5968471f21bb43559740a4523df3"
              },
              "sacg_state": {
                "byte_count": 16337341,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json",
                "sha256": "cbaa68cc8c221620d19819107834ed20f995fe44b17699de0f988bc0cc680bc9"
              }
            },
            "failure_class": "board_output_lifecycle_frontier_violation",
            "hierarchical_certificate_projection": {
              "current_board_evidence_contradicts_lower_certificate": true,
              "lower_layer_reopen_policy": "reopen the failed CCTG boundary and replay the affected lower layer",
              "single_layer_certificate": {
                "byte_count": 84908,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/single_layer_promotion_certificate.json",
                "policy": {
                  "allows_next_hierarchical_layer": true,
                  "does_not_claim_backend_or_board_readiness": true,
                  "does_not_claim_bitstream_or_board_runtime_readiness": true,
                  "lower_layer_pass_evidence_is_reusable_not_absolute": true,
                  "requires_current_trusted_rerun": true
                },
                "required_gates": [
                  {
                    "name": "case_tb_scaffold",
                    "status": "pass"
                  },
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
                "sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7",
                "status": "pass"
              },
              "single_layer_real_tool_evidence": {
                "cycles": 2212376,
                "functional_report": {
                  "byte_count": 252015,
                  "exists": true,
                  "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
                  "sha256": "d1516fc1f565bc0fd0f860868e461bc5bd45d229af062a95f9165718d20cd3ba"
                },
                "input_beats": 1792,
                "output_beats": 1792,
                "pipeline_overlap_status": "pass",
                "pipeline_transition_count": 15,
                "sim_stats": {
                  "byte_count": 197,
                  "exists": true,
                  "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_sim_stats.json",
                  "sha256": "d5b8e940e45c7d87ae2039dbf747a9ea8e8dc5de86dbd0cb71b48610fb77e619"
                },
                "status": "pass"
              }
            },
            "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
            "llm_analysis_contract": {
              "graph_frontier_is_primary_search_scope": true,
              "may_reopen_lower_layer_only_on_explicit_current_trace_contradiction": true,
              "must_correlate_control_and_payload_at_frontier": true,
              "must_not_edit_hardware_for_transport_or_tool_environment_failure": true,
              "must_rerun_same_hierarchical_layer_with_real_tool_after_repair": true,
              "must_use_complete_hash_bound_source_before_edit": true,
              "preserve_full_model_workload_and_exact_board_axi_ddr_contract": true,
              "root_cause_is_not_pre_decided": true
            },
            "parallel_branch_status": {
              "latest_final_writeback_progress": {
                "accepted_beats": 0,
                "target_beats": 896
              },
              "latest_prefetch_progress": {
                "accepted_beats": 0,
                "target_beats": 466104
              },
              "latest_runtime_load_progress": {
                "accepted_words": 1056,
                "target_words": 1056
              },
              "policy": "independent branch progress is supporting evidence and does not move the primary dataflow frontier"
            },
            "remote_workdir": "/home/hyyuan/workspace/spatialaccagent_artifacts/board_vcs/spatialacc_qwen_agent_fast_run/a201b3dd8cf1_118918560173670353409359971486576231653191064420085494142782630",
            "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
            "runtime_evidence_projection": {
              "invalid_schema_record_count": 0,
              "latest_event": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20811776,
                "event_kind": "heartbeat",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "sequence": 7374,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              "layers": {
                "0": {
                  "input_completed": 16,
                  "input_started": 16,
                  "kernel_start": 1,
                  "output_completed": 0,
                  "output_started": 0,
                  "rearmed": 0,
                  "runtime_load_complete": 1,
                  "runtime_load_start": 1
                }
              },
              "observed_token_completion_beat": 111,
              "phase_counts": {
                "bounded_deep_trace": 413,
                "calibrated_configure_start": 1,
                "connected_kernel_all_input_accepted_no_egress": 1,
                "connected_kernel_direct_core_ingress_complete_no_egress": 1,
                "connected_kernel_first_input_window_complete_no_egress": 1,
                "connected_kernel_first_post_start_core_ingress": 1,
                "connected_kernel_input_token_3_complete_no_egress": 1,
                "connected_kernel_lifecycle_start_after_input": 1,
                "connected_kernel_prestart_direct_ingress": 1,
                "connected_kernel_stage0_first_accepted": 1,
                "connected_kernel_stage0_token_complete": 15,
                "connected_kernel_stage0_valid_asserted_after_full_ingress": 1,
                "kernel_input_token_complete": 16,
                "kernel_input_token_start": 16,
                "kernel_start": 1,
                "runtime_load_complete": 1,
                "runtime_load_start": 1,
                "semantic_progress_watch": 5081,
                "weight_loader_accepted": 1820,
                "weight_loader_final_word_accepted": 1
              },
              "phase_first_event": {
                "bounded_deep_trace": {
                  "beat": -1,
                  "cycle": 20001,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "bounded_deep_trace",
                  "scheduler_state": 4,
                  "sequence": 5,
                  "stage_or_boundary": "compute_slot_axi.stall_snapshot",
                  "token": -1
                },
                "calibrated_configure_start": {
                  "beat": -1,
                  "cycle": 279,
                  "event_kind": "lifecycle",
                  "layer": 0,
                  "phase": "calibrated_configure_start",
                  "scheduler_state": 0,
                  "sequence": 0,
                  "stage_or_boundary": "compute_slot_axi.startup",
                  "token": -1
                },
                "connected_kernel_all_input_accepted_no_egress": {
                  "beat": 0,
                  "cycle": 20805737,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_all_input_accepted_no_egress",
                  "scheduler_state": 34,
                  "sequence": 7370,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 16
                },
                "connected_kernel_direct_core_ingress_complete_no_egress": {
                  "beat": 1792,
                  "cycle": 20805738,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_direct_core_ingress_complete_no_egress",
                  "scheduler_state": 30,
                  "sequence": 7371,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 16
                },
                "connected_kernel_first_input_window_complete_no_egress": {
                  "beat": 56,
                  "cycle": 20573567,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_first_input_window_complete_no_egress",
                  "scheduler_state": 30,
                  "sequence": 7265,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_first_post_start_core_ingress": {
                  "beat": 2,
                  "cycle": 20572949,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "connected_kernel_first_post_start_core_ingress",
                  "scheduler_state": 34,
                  "sequence": 7263,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_input_token_3_complete_no_egress": {
                  "beat": 111,
                  "cycle": 20607400,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_input_token_3_complete_no_egress",
                  "scheduler_state": 34,
                  "sequence": 7285,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 3
                },
                "connected_kernel_lifecycle_start_after_input": {
                  "beat": 1,
                  "cycle": 20572948,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_lifecycle_start_after_input",
                  "scheduler_state": 34,
                  "sequence": 7262,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_prestart_direct_ingress": {
                  "beat": 1,
                  "cycle": 20572948,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_prestart_direct_ingress",
                  "scheduler_state": 34,
                  "sequence": 7260,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_stage0_first_accepted": {
                  "beat": 0,
                  "cycle": 20573621,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "connected_kernel_stage0_first_accepted",
                  "scheduler_state": 33,
                  "sequence": 7266,
                  "stage_or_boundary": "pipeline_boundary.stage_00_rms_norm_1",
                  "token": 0
                },
                "connected_kernel_stage0_token_complete": {
                  "beat": 111,
                  "cycle": 20573732,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "scheduler_state": 33,
                  "sequence": 7267,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 0
                },
                "connected_kernel_stage0_valid_asserted_after_full_ingress": {
                  "beat": 1680,
                  "cycle": 20805791,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
                  "scheduler_state": 30,
                  "sequence": 7372,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 16
                },
                "kernel_input_token_complete": {
                  "beat": 111,
                  "cycle": 20573566,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "scheduler_state": 34,
                  "sequence": 7264,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 0
                },
                "kernel_input_token_start": {
                  "beat": 0,
                  "cycle": 20572946,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "scheduler_state": 33,
                  "sequence": 7259,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 0
                },
                "kernel_start": {
                  "beat": -1,
                  "cycle": 20572948,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "kernel_start",
                  "scheduler_state": 34,
                  "sequence": 7261,
                  "stage_or_boundary": "kernel_lifecycle.start",
                  "token": -1
                },
                "runtime_load_complete": {
                  "beat": 1055,
                  "cycle": 20572939,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "runtime_load_complete",
                  "scheduler_state": 15,
                  "sequence": 7258,
                  "stage_or_boundary": "trace.runtime_load_complete",
                  "token": -1
                },
                "runtime_load_start": {
                  "beat": 0,
                  "cycle": 20571186,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "runtime_load_start",
                  "scheduler_state": 12,
                  "sequence": 7257,
                  "stage_or_boundary": "trace.runtime_load_start",
                  "token": -1
                },
                "semantic_progress_watch": {
                  "beat": -1,
                  "cycle": 4096,
                  "event_kind": "heartbeat",
                  "layer": 0,
                  "phase": "semantic_progress_watch",
                  "scheduler_state": 2,
                  "sequence": 1,
                  "stage_or_boundary": "compute_slot_axi",
                  "token": -1
                },
                "weight_loader_accepted": {
                  "beat": 4096,
                  "cycle": 8270809,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "weight_loader_accepted",
                  "scheduler_state": 10,
                  "sequence": 2433,
                  "stage_or_boundary": "trace.weight_loader_accepted",
                  "token": -1
                },
                "weight_loader_final_word_accepted": {
                  "beat": 7457664,
                  "cycle": 20571184,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "weight_loader_final_word_accepted",
                  "scheduler_state": 10,
                  "sequence": 7256,
                  "stage_or_boundary": "trace.weight_loader_accepted",
                  "token": -1
                }
              },
              "phase_last_event": {
                "bounded_deep_trace": {
                  "beat": -1,
                  "cycle": 8260413,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "bounded_deep_trace",
                  "scheduler_state": 4,
                  "sequence": 2429,
                  "stage_or_boundary": "compute_slot_axi.stall_snapshot",
                  "token": -1
                },
                "calibrated_configure_start": {
                  "beat": -1,
                  "cycle": 279,
                  "event_kind": "lifecycle",
                  "layer": 0,
                  "phase": "calibrated_configure_start",
                  "scheduler_state": 0,
                  "sequence": 0,
                  "stage_or_boundary": "compute_slot_axi.startup",
                  "token": -1
                },
                "connected_kernel_all_input_accepted_no_egress": {
                  "beat": 0,
                  "cycle": 20805737,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_all_input_accepted_no_egress",
                  "scheduler_state": 34,
                  "sequence": 7370,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 16
                },
                "connected_kernel_direct_core_ingress_complete_no_egress": {
                  "beat": 1792,
                  "cycle": 20805738,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_direct_core_ingress_complete_no_egress",
                  "scheduler_state": 30,
                  "sequence": 7371,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 16
                },
                "connected_kernel_first_input_window_complete_no_egress": {
                  "beat": 56,
                  "cycle": 20573567,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_first_input_window_complete_no_egress",
                  "scheduler_state": 30,
                  "sequence": 7265,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_first_post_start_core_ingress": {
                  "beat": 2,
                  "cycle": 20572949,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "connected_kernel_first_post_start_core_ingress",
                  "scheduler_state": 34,
                  "sequence": 7263,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_input_token_3_complete_no_egress": {
                  "beat": 111,
                  "cycle": 20607400,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_input_token_3_complete_no_egress",
                  "scheduler_state": 34,
                  "sequence": 7285,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 3
                },
                "connected_kernel_lifecycle_start_after_input": {
                  "beat": 1,
                  "cycle": 20572948,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_lifecycle_start_after_input",
                  "scheduler_state": 34,
                  "sequence": 7262,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_prestart_direct_ingress": {
                  "beat": 1,
                  "cycle": 20572948,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_prestart_direct_ingress",
                  "scheduler_state": 34,
                  "sequence": 7260,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 0
                },
                "connected_kernel_stage0_first_accepted": {
                  "beat": 0,
                  "cycle": 20573621,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "connected_kernel_stage0_first_accepted",
                  "scheduler_state": 33,
                  "sequence": 7266,
                  "stage_or_boundary": "pipeline_boundary.stage_00_rms_norm_1",
                  "token": 0
                },
                "connected_kernel_stage0_token_complete": {
                  "beat": 111,
                  "cycle": 20805124,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "scheduler_state": 33,
                  "sequence": 7367,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 14
                },
                "connected_kernel_stage0_valid_asserted_after_full_ingress": {
                  "beat": 1680,
                  "cycle": 20805791,
                  "event_kind": "stall_snapshot",
                  "layer": 0,
                  "phase": "connected_kernel_stage0_valid_asserted_after_full_ingress",
                  "scheduler_state": 30,
                  "sequence": 7372,
                  "stage_or_boundary": "connected_kernel_input_to_output",
                  "token": 16
                },
                "kernel_input_token_complete": {
                  "beat": 111,
                  "cycle": 20805737,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "scheduler_state": 34,
                  "sequence": 7369,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 15
                },
                "kernel_input_token_start": {
                  "beat": 0,
                  "cycle": 20805125,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "scheduler_state": 33,
                  "sequence": 7368,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 15
                },
                "kernel_start": {
                  "beat": -1,
                  "cycle": 20572948,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "kernel_start",
                  "scheduler_state": 34,
                  "sequence": 7261,
                  "stage_or_boundary": "kernel_lifecycle.start",
                  "token": -1
                },
                "runtime_load_complete": {
                  "beat": 1055,
                  "cycle": 20572939,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "runtime_load_complete",
                  "scheduler_state": 15,
                  "sequence": 7258,
                  "stage_or_boundary": "trace.runtime_load_complete",
                  "token": -1
                },
                "runtime_load_start": {
                  "beat": 0,
                  "cycle": 20571186,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "runtime_load_start",
                  "scheduler_state": 12,
                  "sequence": 7257,
                  "stage_or_boundary": "trace.runtime_load_start",
                  "token": -1
                },
                "semantic_progress_watch": {
                  "beat": -1,
                  "cycle": 20811776,
                  "event_kind": "heartbeat",
                  "layer": 0,
                  "phase": "semantic_progress_watch",
                  "scheduler_state": 30,
                  "sequence": 7374,
                  "stage_or_boundary": "compute_slot_axi",
                  "token": -1
                },
                "weight_loader_accepted": {
                  "beat": 7454720,
                  "cycle": 20566236,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "weight_loader_accepted",
                  "scheduler_state": 10,
                  "sequence": 7254,
                  "stage_or_boundary": "trace.weight_loader_accepted",
                  "token": -1
                },
                "weight_loader_final_word_accepted": {
                  "beat": 7457664,
                  "cycle": 20571184,
                  "event_kind": "semantic_progress",
                  "layer": 0,
                  "phase": "weight_loader_final_word_accepted",
                  "scheduler_state": 10,
                  "sequence": 7256,
                  "stage_or_boundary": "trace.weight_loader_accepted",
                  "token": -1
                }
              },
              "record_count": 7375,
              "semantic_event_count": 1873,
              "semantic_event_tail": [
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 615,
                    "input_payload_digest": "0037ba30",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 933786,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933786
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20723122,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1858,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 34,
                  "sequence": 7334,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 10
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 616,
                    "input_payload_digest": "045c15eb",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 933787,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933787
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20739012,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1859,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7339,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 10
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 616,
                    "input_payload_digest": "045c15eb",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 933787,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933787
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 0,
                  "cycle": 20739013,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1860,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7340,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 11
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 671,
                    "input_payload_digest": "017101b3",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 933842,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933842
                  },
                  "axi_write": {
                    "awready": 1,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20739623,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1861,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 34,
                  "sequence": 7341,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 11
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 672,
                    "input_payload_digest": "82c71e6c",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 933843,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933843
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20755540,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1862,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7346,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 11
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 672,
                    "input_payload_digest": "82c71e6c",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 933843,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933843
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 0,
                  "cycle": 20755541,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1863,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7347,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 12
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 727,
                    "input_payload_digest": "fd80dc02",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 933898,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933898
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20756183,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1864,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 34,
                  "sequence": 7348,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 12
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 728,
                    "input_payload_digest": "0321036f",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 933899,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933899
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20772068,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1865,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7353,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 12
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 728,
                    "input_payload_digest": "0321036f",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 933899,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933899
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 0,
                  "cycle": 20772069,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1866,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7354,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 13
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 783,
                    "input_payload_digest": "fedaaed5",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 933954,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933954
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20772707,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1867,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 34,
                  "sequence": 7355,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 13
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 784,
                    "input_payload_digest": "ff5657fd",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 933955,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933955
                  },
                  "axi_write": {
                    "awready": 1,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20788596,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1868,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7360,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 13
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 784,
                    "input_payload_digest": "ff5657fd",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 933955,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 933955
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 0,
                  "cycle": 20788597,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1869,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7361,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 14
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 839,
                    "input_payload_digest": "fff090c1",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 934010,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 934010
                  },
                  "axi_write": {
                    "awready": 1,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20789241,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1870,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 34,
                  "sequence": 7362,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 14
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 0,
                    "input_axi_index": 840,
                    "input_payload_digest": "7d16f9de",
                    "input_payload_unknown": false,
                    "input_ready": 0,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 934011,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 934011
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20805124,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "connected_kernel_stage0_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1871,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7367,
                  "stage_or_boundary": "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
                  "token": 14
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 840,
                    "input_payload_digest": "7d16f9de",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 1,
                    "arvalid": 0,
                    "beats": 934011,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 934011
                  },
                  "axi_write": {
                    "awready": 0,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 0,
                  "cycle": 20805125,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_start",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1872,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 33,
                  "sequence": 7368,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 15
                },
                {
                  "activation_read_bank": "activation_ping_bank",
                  "activation_write_bank": "activation_pong_bank",
                  "active_boundary_observation": {
                    "event_queue_quiescent": true,
                    "input_accepted": 1,
                    "input_axi_index": 895,
                    "input_payload_digest": "00b0baf9",
                    "input_payload_unknown": false,
                    "input_ready": 1,
                    "input_valid": 1,
                    "output_accept_count": 0,
                    "output_accepted": 0,
                    "output_pair_valid": false,
                    "output_payload_digest": "xxxxxxxx",
                    "output_payload_unknown": true,
                    "output_ready": 1,
                    "output_valid": 0,
                    "start": 0
                  },
                  "active_weight_bank": "weight_a",
                  "axi_read": {
                    "arready": 0,
                    "arvalid": 0,
                    "beats": 934066,
                    "outstanding": 0,
                    "pending_response": false,
                    "rready": 0,
                    "rvalid": 0,
                    "transactions": 934066
                  },
                  "axi_write": {
                    "awready": 1,
                    "awvalid": 0,
                    "beats": 467000,
                    "bready": 0,
                    "bvalid": 0,
                    "outstanding": 0,
                    "pending_response": false,
                    "transactions": 467000,
                    "wready": 0,
                    "wvalid": 0
                  },
                  "beat": 111,
                  "cycle": 20805737,
                  "event_kind": "semantic_progress",
                  "final_writeback_progress": {
                    "accepted_beats": 0,
                    "target_beats": 896
                  },
                  "layer": 0,
                  "phase": "kernel_input_token_complete",
                  "prefetch_progress": {
                    "accepted_beats": 0,
                    "target_beats": 466104
                  },
                  "preload_weight_bank": "none",
                  "progress_epoch": 1873,
                  "runtime_load_progress": {
                    "accepted_words": 1056,
                    "target_words": 1056
                  },
                  "scheduler_state": 34,
                  "sequence": 7369,
                  "stage_or_boundary": "pipeline_boundary.block_input",
                  "token": 15
                }
              ],
              "status": "ready"
            },
            "runtime_targets_from_executed_manifest": {
              "accepted_input_beats_per_layer": null,
              "accepted_output_beats_per_layer": null,
              "target_layer_count": 1
            },
            "schema_version": "spatialaccagent.sacg_cctg_causal_slice.v1",
            "status": "ready"
          }
        },
        "simulation": {
          "duration_sec": 4459.8196780520375,
          "failure_class": "adaptive_semantic_stall",
          "remote_state": "done",
          "returncode": 86,
          "status": "fail"
        },
        "structured_failures": {
          "elaborated_hierarchy": {},
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
                "simulation.dynamic_evidence_records[5].schema_version is missing"
              ],
              "name": "dynamic_real_tool_evidence",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.execution_evidence.status is not pass",
                "simulation.execution_evidence.simulation.exit_code is not zero",
                "simulation execution did not complete with its manifest-bound pass marker"
              ],
              "name": "real_tool_execution_identity_and_logs",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.elaborated_hierarchy is not a successful real-tool elaboration",
                "elaborated hierarchy does not bind the exact sample source closure hash",
                "elaborated hierarchy does not bind the simulator compile source set hash",
                "simulation.elaborated_hierarchy.elaboration_log is missing",
                "elaborated hierarchy does not contain exactly one generated accelerator instance",
                "elaborated hierarchy does not contain exactly one compute-slot instance",
                "elaborated hierarchy does not contain exactly one multilayer harness instance",
                "elaborated hierarchy does not contain exactly one verified connected-layer kernel instance",
                "simulation.elaborated_hierarchy.compute_slot_binding is missing",
                "simulation.elaborated_hierarchy.unresolved_modules must be an explicit empty list",
                "simulation.elaborated_hierarchy.blackboxes must be an explicit empty list"
              ],
              "name": "elaborated_exact_top_and_accelerator_binding",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.pipeline_overlap_results.status is not pass",
                "pipeline overlap results do not cover every required dataflow dependency",
                "pipeline overlap results do not involve every planned stage in required different-token overlap",
                "pipeline overlap results do not preserve token order",
                "pipeline overlap results do not observe the complete planned stage count",
                "pipeline overlap results have no different-token overlap witness"
              ],
              "name": "dynamic_intra_layer_spatial_pipeline_overlap",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.runtime_loader_results.status is not pass",
                "runtime loader results do not bind runtime_plan_contract_sha256",
                "runtime loader results do not bind runtime_image_manifest_contract_sha256",
                "runtime loader results do not bind loader_abi_sha256",
                "runtime loader results do not bind load_schedule_sha256",
                "runtime loader results do not prove every layer was loaded exactly once",
                "runtime loader results observed or did not exclude an early kernel start",
                "simulation.runtime_loader_results.layers[0].accepted_word_count differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].accepted_address_count differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].first_accepted_address differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].last_accepted_address differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].address_sequence_contiguous is not true",
                "simulation.runtime_loader_results.layers[0].address_sequence_unique is not true",
                "simulation.runtime_loader_results.layers[0].data_matches_image_segment is not true",
                "simulation.runtime_loader_results.layers[0].last_asserted_on_final_accept is not true",
                "simulation.runtime_loader_results.layers[0] does not prove load_complete_cycle < kernel_start_cycle"
              ],
              "name": "dynamic_runtime_loader_consumption",
              "status": "fail"
            }
          ],
          "pipeline_overlap": {
            "all_planned_stages_participate_in_required_overlap": false,
            "all_spatial_stages_concurrent_observed": false,
            "all_stages_same_cycle_concurrency_required": false,
            "diagnostic_maximum_concurrent_stage_count": 9,
            "observed_different_token_overlap_count": 0,
            "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
            "report_valid": false,
            "required_dependency_overlap_complete": false,
            "serial_leaf_execution_observed": false,
            "stage_turnover_gaps_are_diagnostic": true,
            "status": "fail",
            "structured_trace_report": {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
              "relative_path": "reports/pipeline_overlap_report.json",
              "sha256": "37e1f22f78fb0093f91d6e96ba02d5e7a358548bdc0e7367c67d536aab18dd38"
            },
            "token_order_preserved": false,
            "whole_sequence_barrier_observed": false
          },
          "protocol_monitors": []
        },
        "supplemental_observation_artifacts": [
          {
            "artifact_kind": "jsonl_observation",
            "byte_count": 3086,
            "copied": true,
            "evidence_id": "runtime.supplemental_observation.connected_kernel_delta_transition.cbed70a96ff20cc8",
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/connected_kernel_delta_transition.jsonl",
            "relative_path": "reports/connected_kernel_delta_transition.jsonl",
            "sha256": "cbed70a96ff20cc836430cb7854b98511d8cbe7698ecf75f67320fbf614628ba",
            "status": "ready",
            "summary": {
              "first_scalar_record": {
                "evidence_kind": "boundary_trace",
                "observational_only": true,
                "probe_id": "probe.connected_kernel_mlp_tail_convergence.11",
                "probe_revision": 11,
                "schema_version": "spatialaccagent.connected_kernel_delta_transition.v1",
                "sequence": 0,
                "source_marker": "connected_kernel_mlp_tail_convergence_r11",
                "status": "waiting_for_post_full_ingress_mlp_tail_without_core_egress"
              },
              "invalid_record_count": 0,
              "last_scalar_record": {
                "core_egress.accepted_count": 0,
                "core_egress.fire": 0,
                "core_egress.ready": 1,
                "core_egress.valid": 0,
                "core_ingress_accepted_count": 1792,
                "cycle": 20805791,
                "evidence_kind": "boundary_trace",
                "kernel_reset": 0,
                "mlp_down_input.accepted_count": 607,
                "mlp_down_input.fire": 0,
                "mlp_down_input.last": 0,
                "mlp_down_input.ready": 1,
                "mlp_down_input.valid": 0,
                "mlp_down_output.accepted_count": 0,
                "mlp_down_output.fire": 0,
                "mlp_down_output.last": 0,
                "mlp_down_output.ready": 1,
                "mlp_down_output.valid": 0,
                "mlp_gate_output.accepted_count": 608,
                "mlp_gate_output.fire": 0,
                "mlp_gate_output.last": 0,
                "mlp_gate_output.ready": 1,
                "mlp_gate_output.valid": 0,
                "mlp_mul_output.accepted_count": 607,
                "mlp_mul_output.fire": 0,
                "mlp_mul_output.last": 0,
                "mlp_mul_output.ready": 1,
                "mlp_mul_output.valid": 0,
                "mlp_up_output.accepted_count": 608,
                "mlp_up_output.fire": 0,
                "mlp_up_output.last": 0,
                "mlp_up_output.ready": 1,
                "mlp_up_output.valid": 0,
                "probe_id": "probe.connected_kernel_mlp_tail_convergence.11",
                "probe_revision": 11,
                "residual2_enqueue_valid": 0,
                "same_time_index": 1,
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.connected_kernel_delta_transition.v1",
                "sequence": 3,
                "simulation_time": 83223162000,
                "source_marker": "connected_kernel_mlp_tail_convergence_r11",
                "stage0_accepted_count": 1680
              },
              "probe_ids": [
                "probe.connected_kernel_mlp_tail_convergence.11"
              ],
              "probe_revisions": [
                11
              ],
              "record_count": 4,
              "schema_versions": [
                "spatialaccagent.connected_kernel_delta_transition.v1"
              ],
              "status": "ready",
              "tail_scalar_records": [
                {
                  "evidence_kind": "boundary_trace",
                  "observational_only": true,
                  "probe_id": "probe.connected_kernel_mlp_tail_convergence.11",
                  "probe_revision": 11,
                  "schema_version": "spatialaccagent.connected_kernel_delta_transition.v1",
                  "sequence": 0,
                  "source_marker": "connected_kernel_mlp_tail_convergence_r11",
                  "status": "waiting_for_post_full_ingress_mlp_tail_without_core_egress"
                },
                {
                  "core_egress.accepted_count": 0,
                  "core_egress.fire": 0,
                  "core_egress.ready": 1,
                  "core_egress.valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "cycle": 20805738,
                  "evidence_kind": "boundary_trace",
                  "kernel_reset": 0,
                  "mlp_down_input.accepted_count": 607,
                  "mlp_down_input.fire": 0,
                  "mlp_down_input.last": 0,
                  "mlp_down_input.ready": 1,
                  "mlp_down_input.valid": 0,
                  "mlp_down_output.accepted_count": 0,
                  "mlp_down_output.fire": 0,
                  "mlp_down_output.last": 0,
                  "mlp_down_output.ready": 1,
                  "mlp_down_output.valid": 0,
                  "mlp_gate_output.accepted_count": 608,
                  "mlp_gate_output.fire": 0,
                  "mlp_gate_output.last": 0,
                  "mlp_gate_output.ready": 1,
                  "mlp_gate_output.valid": 0,
                  "mlp_mul_output.accepted_count": 607,
                  "mlp_mul_output.fire": 0,
                  "mlp_mul_output.last": 0,
                  "mlp_mul_output.ready": 1,
                  "mlp_mul_output.valid": 0,
                  "mlp_up_output.accepted_count": 608,
                  "mlp_up_output.fire": 0,
                  "mlp_up_output.last": 0,
                  "mlp_up_output.ready": 1,
                  "mlp_up_output.valid": 0,
                  "probe_id": "probe.connected_kernel_mlp_tail_convergence.11",
                  "probe_revision": 11,
                  "residual2_enqueue_valid": 0,
                  "same_time_index": 0,
                  "scheduler_state": 30,
                  "schema_version": "spatialaccagent.connected_kernel_delta_transition.v1",
                  "sequence": 1,
                  "simulation_time": 83222950000,
                  "source_marker": "connected_kernel_mlp_tail_convergence_r11",
                  "stage0_accepted_count": 1680
                },
                {
                  "core_egress.accepted_count": 0,
                  "core_egress.fire": 0,
                  "core_egress.ready": 1,
                  "core_egress.valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "cycle": 20805791,
                  "evidence_kind": "boundary_trace",
                  "kernel_reset": 0,
                  "mlp_down_input.accepted_count": 607,
                  "mlp_down_input.fire": 0,
                  "mlp_down_input.last": 0,
                  "mlp_down_input.ready": 1,
                  "mlp_down_input.valid": 0,
                  "mlp_down_output.accepted_count": 0,
                  "mlp_down_output.fire": 0,
                  "mlp_down_output.last": 0,
                  "mlp_down_output.ready": 1,
                  "mlp_down_output.valid": 0,
                  "mlp_gate_output.accepted_count": 608,
                  "mlp_gate_output.fire": 0,
                  "mlp_gate_output.last": 0,
                  "mlp_gate_output.ready": 1,
                  "mlp_gate_output.valid": 0,
                  "mlp_mul_output.accepted_count": 607,
                  "mlp_mul_output.fire": 0,
                  "mlp_mul_output.last": 0,
                  "mlp_mul_output.ready": 1,
                  "mlp_mul_output.valid": 0,
                  "mlp_up_output.accepted_count": 608,
                  "mlp_up_output.fire": 0,
                  "mlp_up_output.last": 0,
                  "mlp_up_output.ready": 1,
                  "mlp_up_output.valid": 0,
                  "probe_id": "probe.connected_kernel_mlp_tail_convergence.11",
                  "probe_revision": 11,
                  "residual2_enqueue_valid": 0,
                  "same_time_index": 0,
                  "scheduler_state": 30,
                  "schema_version": "spatialaccagent.connected_kernel_delta_transition.v1",
                  "sequence": 2,
                  "simulation_time": 83223162000,
                  "source_marker": "connected_kernel_mlp_tail_convergence_r11",
                  "stage0_accepted_count": 1680
                },
                {
                  "core_egress.accepted_count": 0,
                  "core_egress.fire": 0,
                  "core_egress.ready": 1,
                  "core_egress.valid": 0,
                  "core_ingress_accepted_count": 1792,
                  "cycle": 20805791,
                  "evidence_kind": "boundary_trace",
                  "kernel_reset": 0,
                  "mlp_down_input.accepted_count": 607,
                  "mlp_down_input.fire": 0,
                  "mlp_down_input.last": 0,
                  "mlp_down_input.ready": 1,
                  "mlp_down_input.valid": 0,
                  "mlp_down_output.accepted_count": 0,
                  "mlp_down_output.fire": 0,
                  "mlp_down_output.last": 0,
                  "mlp_down_output.ready": 1,
                  "mlp_down_output.valid": 0,
                  "mlp_gate_output.accepted_count": 608,
                  "mlp_gate_output.fire": 0,
                  "mlp_gate_output.last": 0,
                  "mlp_gate_output.ready": 1,
                  "mlp_gate_output.valid": 0,
                  "mlp_mul_output.accepted_count": 607,
                  "mlp_mul_output.fire": 0,
                  "mlp_mul_output.last": 0,
                  "mlp_mul_output.ready": 1,
                  "mlp_mul_output.valid": 0,
                  "mlp_up_output.accepted_count": 608,
                  "mlp_up_output.fire": 0,
                  "mlp_up_output.last": 0,
                  "mlp_up_output.ready": 1,
                  "mlp_up_output.valid": 0,
                  "probe_id": "probe.connected_kernel_mlp_tail_convergence.11",
                  "probe_revision": 11,
                  "residual2_enqueue_valid": 0,
                  "same_time_index": 1,
                  "scheduler_state": 30,
                  "schema_version": "spatialaccagent.connected_kernel_delta_transition.v1",
                  "sequence": 3,
                  "simulation_time": 83223162000,
                  "source_marker": "connected_kernel_mlp_tail_convergence_r11",
                  "stage0_accepted_count": 1680
                }
              ],
              "trailing_partial_byte_count": 0
            }
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
            "last_observed_cycle": 20811776
          },
          "exact_source_replay_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
          "exit_code": 86,
          "final_committed_progress_event": {
            "activation_read_bank": "activation_ping_bank",
            "activation_write_bank": "activation_pong_bank",
            "active_boundary_observation": {
              "event_queue_quiescent": true,
              "input_accepted": 0,
              "input_axi_index": 896,
              "input_payload_digest": "00b0baf9",
              "input_payload_unknown": false,
              "input_ready": 0,
              "input_valid": 0,
              "output_accept_count": 0,
              "output_accepted": 0,
              "output_pair_valid": false,
              "output_payload_digest": "xxxxxxxx",
              "output_payload_unknown": true,
              "output_ready": 1,
              "output_valid": 0,
              "start": 0
            },
            "active_weight_bank": "weight_a",
            "axi_read": {
              "arready": 1,
              "arvalid": 0,
              "beats": 934066,
              "outstanding": 0,
              "pending_response": false,
              "rready": 0,
              "rvalid": 0,
              "transactions": 934066
            },
            "axi_write": {
              "awready": 0,
              "awvalid": 0,
              "beats": 467000,
              "bready": 0,
              "bvalid": 0,
              "outstanding": 0,
              "pending_response": false,
              "transactions": 467000,
              "wready": 0,
              "wvalid": 0
            },
            "beat": -1,
            "cycle": 20811776,
            "event_kind": "heartbeat",
            "evidence_kind": "board_progress",
            "final_writeback_progress": {
              "accepted_beats": 0,
              "target_beats": 896
            },
            "last_semantic_progress_cycle": 20805737,
            "layer": 0,
            "phase": "semantic_progress_watch",
            "prefetch_progress": {
              "accepted_beats": 0,
              "target_beats": 466104
            },
            "preload_weight_bank": "none",
            "progress_epoch": 1873,
            "runtime_load_progress": {
              "accepted_words": 1056,
              "target_words": 1056
            },
            "scheduler_state": 30,
            "schema_version": "spatialaccagent.board_progress_event.v1",
            "semantic_progress": false,
            "sequence": 7374,
            "stage_or_boundary": "compute_slot_axi",
            "token": -1
          },
          "framework_termination": {
            "adaptive_semantic_stall": "pass",
            "zero_time_livelock": "not_run"
          },
          "missing_completion_reports_causal_classification": "process_ended_before_terminal_event",
          "observed_duration_sec": 4459.8196780520375,
          "raw_terminal_log_tail": "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12507938 token=  12 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12508049 token=  12 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7354 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20772068 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7355 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20772069 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7356 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20772707 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7357 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20774912 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7358 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20779008 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7359 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20783104 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7360 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20787200 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524466 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524577 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7361 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20788596 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7362 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20788597 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7363 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20789241 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7364 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20791296 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7365 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20795392 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7366 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20799488 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7367 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20803584 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12540994 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12541105 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7368 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20805124 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7369 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20805125 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7370 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7371 event_kind=stall_snapshot phase=connected_kernel_all_input_accepted_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7372 event_kind=stall_snapshot phase=connected_kernel_direct_core_ingress_complete_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805738 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7373 event_kind=stall_snapshot phase=connected_kernel_stage0_valid_asserted_after_full_ingress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805791 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7374 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20807680 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7375 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20811776 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
          "remote_state": "done",
          "runner_failure_class": "adaptive_semantic_stall",
          "runner_process_provenance": {
            "attribution": "runner_owned_nonzero_process_exit",
            "command_sha256": "7fbc6d272577ddec00db8a52a78359640c09fea30fa94fed225cbd8ccd752ee4",
            "detached_runner_session": true,
            "deterministic_hdl_or_testbench_event_observed": false,
            "exit_code": 86,
            "label": "vcs_simulate",
            "last_running_process_count": 3,
            "last_running_process_snapshot": {
              "processes": [
                {
                  "command": "bash",
                  "pgid": 91927,
                  "pid": 91927,
                  "ppid": 1,
                  "sid": 91927,
                  "state": "Ss"
                },
                {
                  "command": "bash",
                  "pgid": 91927,
                  "pid": 91957,
                  "ppid": 91927,
                  "sid": 91927,
                  "state": "S"
                },
                {
                  "command": "simv",
                  "pgid": 91927,
                  "pid": 91979,
                  "ppid": 91957,
                  "sid": 91927,
                  "state": "R"
                }
              ],
              "reported_process_count": 3,
              "schema_version": "spatialaccagent.remote_process_snapshot.v1",
              "session_leader_pid": 91927,
              "simulator_like_process_observed": true,
              "simulator_process_commands": [
                "simv"
              ],
              "status": "observed",
              "truncated": false
            },
            "last_simulator_process_commands": [
              "simv"
            ],
            "launch_pid": 91927,
            "reattached_existing_job": false,
            "schema_version": "spatialaccagent.remote_runner_process_provenance.v1",
            "signal_number": null,
            "source_semantic_repair_eligible": false,
            "status": "observed"
          },
          "schema_version": "spatialaccagent.simulation_termination_provenance.v1",
          "signal_number": null,
          "simulator_terminal_log": {
            "byte_count": 1490183,
            "checkpoint_markers": [],
            "checkpoint_markers_truncated": false,
            "failure_lines": [],
            "matched_lines": [],
            "matched_lines_truncated": false,
            "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
            "schema_version": "spatialaccagent.simulation_runtime_failure_evidence.v1",
            "sha256": "87da073d5875500e978f425935f8bbf51b54db2a8386a5b82869ba2f88080112",
            "simulator_crash_lines": [],
            "simulator_crash_lines_truncated": false,
            "status": "not_observed",
            "tail_lines": [
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12507938 token=  12 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12508049 token=  12 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7354 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20772068 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7355 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20772069 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7356 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20772707 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7357 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20774912 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7358 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20779008 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7359 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20783104 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7360 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20787200 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524466 token=  13 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524577 token=  13 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7361 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20788596 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7362 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20788597 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7363 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20789241 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7364 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20791296 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7365 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20795392 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7366 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20799488 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7367 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20803584 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12540994 token=  14 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12541105 token=  14 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7368 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20805124 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7369 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20805125 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1",
              "SPATIALACC_BOARD_PROGRESS sequence=7370 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7371 event_kind=stall_snapshot phase=connected_kernel_all_input_accepted_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7372 event_kind=stall_snapshot phase=connected_kernel_direct_core_ingress_complete_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805738 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7373 event_kind=stall_snapshot phase=connected_kernel_stage0_valid_asserted_after_full_ingress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805791 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7374 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20807680 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1",
              "SPATIALACC_BOARD_PROGRESS sequence=7375 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20811776 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1"
            ],
            "tail_lines_truncated": true,
            "termination_markers": [],
            "termination_markers_truncated": false
          },
          "status": "complete",
          "terminal_progress_event_seen": false,
          "termination_source": "framework_adaptive_semantic_stall_termination",
          "testbench_observation_activity": {
            "other_testbench_file_io_callbacks": {
              "status": "not_directly_observable_from_runner"
            },
            "progress_file_io": {
              "committed_byte_count": 10259490,
              "complete_record_count": 7375,
              "last_committed_event": {
                "activation_read_bank": "activation_ping_bank",
                "activation_write_bank": "activation_pong_bank",
                "active_boundary_observation": {
                  "event_queue_quiescent": true,
                  "input_accepted": 0,
                  "input_axi_index": 896,
                  "input_payload_digest": "00b0baf9",
                  "input_payload_unknown": false,
                  "input_ready": 0,
                  "input_valid": 0,
                  "output_accept_count": 0,
                  "output_accepted": 0,
                  "output_pair_valid": false,
                  "output_payload_digest": "xxxxxxxx",
                  "output_payload_unknown": true,
                  "output_ready": 1,
                  "output_valid": 0,
                  "start": 0
                },
                "active_weight_bank": "weight_a",
                "axi_read": {
                  "arready": 1,
                  "arvalid": 0,
                  "beats": 934066,
                  "outstanding": 0,
                  "pending_response": false,
                  "rready": 0,
                  "rvalid": 0,
                  "transactions": 934066
                },
                "axi_write": {
                  "awready": 0,
                  "awvalid": 0,
                  "beats": 467000,
                  "bready": 0,
                  "bvalid": 0,
                  "outstanding": 0,
                  "pending_response": false,
                  "transactions": 467000,
                  "wready": 0,
                  "wvalid": 0
                },
                "beat": -1,
                "cycle": 20811776,
                "event_kind": "heartbeat",
                "evidence_kind": "board_progress",
                "final_writeback_progress": {
                  "accepted_beats": 0,
                  "target_beats": 896
                },
                "last_semantic_progress_cycle": 20805737,
                "layer": 0,
                "phase": "semantic_progress_watch",
                "prefetch_progress": {
                  "accepted_beats": 0,
                  "target_beats": 466104
                },
                "preload_weight_bank": "none",
                "progress_epoch": 1873,
                "runtime_load_progress": {
                  "accepted_words": 1056,
                  "target_words": 1056
                },
                "scheduler_state": 30,
                "schema_version": "spatialaccagent.board_progress_event.v1",
                "semantic_progress": false,
                "sequence": 7374,
                "stage_or_boundary": "compute_slot_axi",
                "token": -1
              },
              "write_observed_during_last_observation": true
            },
            "runner_process_snapshot": {
              "processes": [
                {
                  "command": "bash",
                  "pgid": 91927,
                  "pid": 91927,
                  "ppid": 1,
                  "sid": 91927,
                  "state": "Ss"
                },
                {
                  "command": "bash",
                  "pgid": 91927,
                  "pid": 91957,
                  "ppid": 91927,
                  "sid": 91927,
                  "state": "S"
                },
                {
                  "command": "simv",
                  "pgid": 91927,
                  "pid": 91979,
                  "ppid": 91957,
                  "sid": 91927,
                  "state": "R"
                }
              ],
              "reported_process_count": 3,
              "schema_version": "spatialaccagent.remote_process_snapshot.v1",
              "session_leader_pid": 91927,
              "simulator_like_process_observed": true,
              "simulator_process_commands": [
                "simv"
              ],
              "status": "observed",
              "truncated": false
            },
            "schema_version": "spatialaccagent.testbench_observation_activity.v1",
            "simulator_process_observed": true,
            "testbench_observation_process": "simulator_process",
            "vcd_dumping": {
              "active_during_last_running_observation": false,
              "configured": false,
              "last_timestamp": null,
              "observed": false
            }
          },
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
        "binding_manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
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
        "failure_class": "board_output_lifecycle_frontier_violation",
        "first_real_error": "the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel",
        "log_tail": "49 token=  12 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7354 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20772068 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508050 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7355 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20772069 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12508688 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7356 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20772707 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7357 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20774912 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7358 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20779008 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7359 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20783104 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7360 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20787200 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524466 token=  13 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12524577 token=  13 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7361 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20788596 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12524578 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7362 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20788597 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12525222 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7363 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20789241 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7364 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20791296 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7365 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20795392 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7366 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20799488 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7367 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20803584 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12540994 token=  14 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main cycle=            12541105 token=  14 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7368 event_kind=semantic_progress phase=connected_kernel_stage0_token_complete layer=0 cycle=20805124 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541106 token=  15 beat=  0 st=1 last=0 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7369 event_kind=semantic_progress phase=kernel_input_token_start layer=0 cycle=20805125 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_00_rms_norm_1.input cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_PIPELINE_TRACE boundary=edge.data.block_input.to.stage_02_residual_add_1.residual_skip cycle=            12541718 token=  15 beat=111 st=0 last=1 valid=1 ready=1\nSPATIALACC_BOARD_PROGRESS sequence=7370 event_kind=semantic_progress phase=kernel_input_token_complete layer=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7371 event_kind=stall_snapshot phase=connected_kernel_all_input_accepted_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805737 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7372 event_kind=stall_snapshot phase=connected_kernel_direct_core_ingress_complete_no_egress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805738 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7373 event_kind=stall_snapshot phase=connected_kernel_stage0_valid_asserted_after_full_ingress layer=0 input_count=1792 output_count=0 fifo_count=0 cycle=20805791 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7374 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20807680 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nSPATIALACC_BOARD_PROGRESS sequence=7375 event_kind=heartbeat phase=semantic_progress_watch layer=0 cycle=20811776 evidence_kind=board_progress schema_version=spatialaccagent.board_progress_event.v1\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\nbash: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)\n/bin/sh: warning: setlocale: LC_ALL: cannot change locale (C.UTF-8)",
        "must_rerun": [
          "case_vcs_functional_sim",
          "case_vcs_evidence_analyzer"
        ],
        "next_stage": "repair",
        "related_source_ids": [
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
        "repair_scope": "board_rtl_or_testbench",
        "runner_phase": "remote_vcs",
        "sacg_cctg_causal_frontier": {
          "artifact_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
          "artifact_sha256": "afa334f62758d48abaa13070c0d0e5d6a7e16a3224bad419af66752b9fc2436a",
          "earliest_unproven_frontier": {
            "causal_domain": "connected_kernel_boundary",
            "failed_boundary_ids": [
              "connected_kernel_input_to_output"
            ],
            "failure_class": "board_output_lifecycle_frontier_violation",
            "frontier_id": "cctg_boundary_invariant_failure",
            "prior_runtime_frontier": {
              "causal_domain": "connected_kernel_boundary",
              "failure_class": "board_output_lifecycle_frontier_violation",
              "frontier_id": "connected_kernel_input_to_output",
              "observed": {
                "active_layer": 0,
                "beats_per_token_inferred_from_trace": 112,
                "expected_input_tokens": null,
                "expected_output_tokens": null,
                "input_completed": 16,
                "input_started": 16,
                "kernel_start": 1,
                "output_completed": 0,
                "output_started": 0,
                "rearmed": 0,
                "runtime_load_complete": 1,
                "runtime_load_start": 1,
                "target_layer_count": 1
              },
              "reason": "complete kernel input was observed but no kernel output token started",
              "status": "earliest_unproven"
            },
            "reason": "the current trace explicitly failed one or more CCTG boundary invariants",
            "status": "earliest_unproven"
          },
          "hierarchical_certificate_projection": {
            "current_board_evidence_contradicts_lower_certificate": true,
            "lower_layer_reopen_policy": "reopen the failed CCTG boundary and replay the affected lower layer",
            "single_layer_certificate": {
              "byte_count": 84908,
              "exists": true,
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/single_layer_promotion_certificate.json",
              "policy": {
                "allows_next_hierarchical_layer": true,
                "does_not_claim_backend_or_board_readiness": true,
                "does_not_claim_bitstream_or_board_runtime_readiness": true,
                "lower_layer_pass_evidence_is_reusable_not_absolute": true,
                "requires_current_trusted_rerun": true
              },
              "required_gates": [
                {
                  "name": "case_tb_scaffold",
                  "status": "pass"
                },
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
              "sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7",
              "status": "pass"
            },
            "single_layer_real_tool_evidence": {
              "cycles": 2212376,
              "functional_report": {
                "byte_count": 252015,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_functional_report.json",
                "sha256": "d1516fc1f565bc0fd0f860868e461bc5bd45d229af062a95f9165718d20cd3ba"
              },
              "input_beats": 1792,
              "output_beats": 1792,
              "pipeline_overlap_status": "pass",
              "pipeline_transition_count": 15,
              "sim_stats": {
                "byte_count": 197,
                "exists": true,
                "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/single_layer/single_layer_sim_stats.json",
                "sha256": "d5b8e940e45c7d87ae2039dbf747a9ea8e8dc5de86dbd0cb71b48610fb77e619"
              },
              "status": "pass"
            }
          },
          "status": "ready"
        },
        "structured_failures": {
          "elaborated_hierarchy": {},
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
                "simulation.dynamic_evidence_records[5].schema_version is missing"
              ],
              "name": "dynamic_real_tool_evidence",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.execution_evidence.status is not pass",
                "simulation.execution_evidence.simulation.exit_code is not zero",
                "simulation execution did not complete with its manifest-bound pass marker"
              ],
              "name": "real_tool_execution_identity_and_logs",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.elaborated_hierarchy is not a successful real-tool elaboration",
                "elaborated hierarchy does not bind the exact sample source closure hash",
                "elaborated hierarchy does not bind the simulator compile source set hash",
                "simulation.elaborated_hierarchy.elaboration_log is missing",
                "elaborated hierarchy does not contain exactly one generated accelerator instance",
                "elaborated hierarchy does not contain exactly one compute-slot instance",
                "elaborated hierarchy does not contain exactly one multilayer harness instance",
                "elaborated hierarchy does not contain exactly one verified connected-layer kernel instance",
                "simulation.elaborated_hierarchy.compute_slot_binding is missing",
                "simulation.elaborated_hierarchy.unresolved_modules must be an explicit empty list",
                "simulation.elaborated_hierarchy.blackboxes must be an explicit empty list"
              ],
              "name": "elaborated_exact_top_and_accelerator_binding",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.pipeline_overlap_results.status is not pass",
                "pipeline overlap results do not cover every required dataflow dependency",
                "pipeline overlap results do not involve every planned stage in required different-token overlap",
                "pipeline overlap results do not preserve token order",
                "pipeline overlap results do not observe the complete planned stage count",
                "pipeline overlap results have no different-token overlap witness"
              ],
              "name": "dynamic_intra_layer_spatial_pipeline_overlap",
              "status": "fail"
            },
            {
              "blockers": [
                "simulation.runtime_loader_results.status is not pass",
                "runtime loader results do not bind runtime_plan_contract_sha256",
                "runtime loader results do not bind runtime_image_manifest_contract_sha256",
                "runtime loader results do not bind loader_abi_sha256",
                "runtime loader results do not bind load_schedule_sha256",
                "runtime loader results do not prove every layer was loaded exactly once",
                "runtime loader results observed or did not exclude an early kernel start",
                "simulation.runtime_loader_results.layers[0].accepted_word_count differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].accepted_address_count differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].first_accepted_address differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].last_accepted_address differs from the runtime load schedule",
                "simulation.runtime_loader_results.layers[0].address_sequence_contiguous is not true",
                "simulation.runtime_loader_results.layers[0].address_sequence_unique is not true",
                "simulation.runtime_loader_results.layers[0].data_matches_image_segment is not true",
                "simulation.runtime_loader_results.layers[0].last_asserted_on_final_accept is not true",
                "simulation.runtime_loader_results.layers[0] does not prove load_complete_cycle < kernel_start_cycle"
              ],
              "name": "dynamic_runtime_loader_consumption",
              "status": "fail"
            }
          ],
          "pipeline_overlap": {
            "all_planned_stages_participate_in_required_overlap": false,
            "all_spatial_stages_concurrent_observed": false,
            "all_stages_same_cycle_concurrency_required": false,
            "diagnostic_maximum_concurrent_stage_count": 9,
            "observed_different_token_overlap_count": 0,
            "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
            "report_valid": false,
            "required_dependency_overlap_complete": false,
            "serial_leaf_execution_observed": false,
            "stage_turnover_gaps_are_diagnostic": true,
            "status": "fail",
            "structured_trace_report": {
              "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/pipeline_overlap_report.json",
              "relative_path": "reports/pipeline_overlap_report.json",
              "sha256": "37e1f22f78fb0093f91d6e96ba02d5e7a358548bdc0e7367c67d536aab18dd38"
            },
            "token_order_preserved": false,
            "whole_sequence_barrier_observed": false
          },
          "protocol_monitors": []
        },
        "termination_causal_classification": {
          "classification": "external_or_unattributed_termination",
          "deterministic_hdl_or_testbench_failure_proven": false,
          "simulator_infrastructure_failure_proven": false,
          "source_semantic_repair_eligible": false
        }
      },
      "root_cause_class": "board_output_lifecycle_frontier_violation",
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
        "testbench_sha256": "09f29e894f2fdaff4c4b5aa1be0bbc72085b2093c3f212f02b9c498cea204dec"
      },
      "sim_pass": false,
      "sources": [
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/board_source_identity.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/compile.log",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/simulation.log",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_executed_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/boundary_trace.jsonl",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/live/adaptive_semantic_stall.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/sacg_cctg_causal_slice.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/reports/connected_kernel_delta_transition.jsonl"
      ],
      "status": "needs_repair",
      "summary": "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
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
      "relation": "current_targeted_backtrack",
      "schema_version": "spatialaccagent.diagnosis_applicability_report.v1",
      "status": "applicable",
      "target_layer": "single_transformer_layer_kernel",
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
        "The real VCS compile passed, but simulation terminated through framework adaptive-semantic-stall handling with external_or_unattributed_termination; deterministic HDL or testbench failure was not proven and source_semantic_repair_eligible is false.",
        "Current direct lifecycle evidence already shows the connected-kernel output frontier contradiction: all 896 activation input beats were consumed while output_accept_count remained zero. A behavioral adapter or certified-kernel repair is therefore not authorized in this repair turn.",
        "No causally distinct simulation-only observation edit is justified: the supplied testbench already contains source-bound direct-core lifecycle, inner-cone, MLP-tail, and current-DAG boundary probes, and unchanged-source replay would repeat the completed experiment."
      ],
      "deterministic_feedback": [],
      "execution_errors": [],
      "input_fingerprint_sha256": "247eb2b7dd9e7e30cf3fefd9eba601f11e062199a7ceebdf69b3ad54596b6802",
      "llm_records": [
        {
          "agent": "exact_board_integration_generation_agent",
          "blockers": [
            "The real VCS compile passed, but simulation terminated through framework adaptive-semantic-stall handling with external_or_unattributed_termination; deterministic HDL or testbench failure was not proven and source_semantic_repair_eligible is false.",
            "Current direct lifecycle evidence already shows the connected-kernel output frontier contradiction: all 896 activation input beats were consumed while output_accept_count remained zero. A behavioral adapter or certified-kernel repair is therefore not authorized in this repair turn.",
            "No causally distinct simulation-only observation edit is justified: the supplied testbench already contains source-bound direct-core lifecycle, inner-cone, MLP-tail, and current-DAG boundary probes, and unchanged-source replay would repeat the completed experiment."
          ],
          "deterministic_feedback": [],
          "input_fingerprint_sha256": "62573731541762515d206d24a4569f96cf79d84b426571713fa8e33642ae0c51",
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/llm/exact_board_integration_generation_agent_result.json",
          "repair_execution_context": {
            "debug_layer": "board_axi_ddr_wrapped_system",
            "repair_scope": "verification_capability_repair",
            "repair_step_id": "repair_step.00",
            "schema_version": "spatialaccagent.repair_execution_agent_context.v1",
            "verification_scope": "board_axi_ddr_closure"
          },
          "required_capabilities": [],
          "scope": "verification_capability_repair",
          "sha256": "e14b635069cd531619531251c450f667b3978908696b3f29e49c34ae45c0ef5e",
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
        "sha256": "a9a29ac21112c3951ef0f1752aed9654be6e3db0b7b123124b156ca1f2d7fa90"
      },
      "required_capabilities": [],
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
            "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
          "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v4",
          "status": "needs_repair",
          "summary": "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
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
      "summary": "skipped because dependency gate(s) are not pass: ['case_axi_ddr_interface'] report_status=needs_repair blockers=board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel",
      "tool_report_blockers": [
        "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
      "tool_report_status": "needs_repair",
      "tool_report_summary": "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
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
      "debug_layer": "single_transformer_layer_kernel",
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
      "failure_signature": {
        "current_board_to_lower_layer_contradiction": {
          "evidence": {
            "causal_localization": {
              "earliest_causal_owner": "single_transformer_layer_kernel",
              "localization_basis": "first_direct_boundary_with_accepted_input_and_ready_zero_output",
              "named_contract_boundary_id": "kernel.mlp_down.output"
            },
            "direct_kernel_boundary_observations": {
              "kernel_egress_ready": true,
              "kernel_ingress_complete": true,
              "kernel_start_accepted": true
            },
            "observation_context": {
              "direct_kernel_observation_fields": {
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792
              },
              "pipeline_boundary_observation": {
                "incomplete_boundary_ids": [
                  "edge.data.block_input.to.stage_00_rms_norm_1.input",
                  "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                  "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
                  "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                  "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                  "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
                  "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
                  "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
                  "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
                  "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
                  "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
                  "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
                  "edge.data.stage_08_residual_add_2.to.block_output.output"
                ],
                "missing_boundary_ids": [
                  "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                  "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                  "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                  "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip"
                ],
                "observed_boundary_count": 9,
                "record_count": 63,
                "required_boundary_count": 13,
                "status": "incomplete"
              }
            },
            "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
            "source_binding": {
              "board_trace_sha256": "a9beca5ed422e60dd2f416e50ae6db3ec92a75c1783e0440dc09c5d7d641ae35",
              "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
              "lower_layer_certificate_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7"
            },
            "status": "proven",
            "target_debug_layer": "single_transformer_layer_kernel"
          },
          "required_observation_contract": {
            "current_trace_and_lower_certificate_hashes_required": true,
            "earliest_causal_owner_must_match_target_layer": true,
            "kernel_egress_ready_required": true,
            "kernel_ingress_complete_required": true,
            "kernel_start_accepted_required": true,
            "named_earliest_causal_boundary_required": true
          },
          "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
          "status": "proven",
          "target_debug_layer": "single_transformer_layer_kernel",
          "validation_errors": []
        },
        "failure_class": "board_output_lifecycle_frontier_violation",
        "repair_scope": "board_rtl_or_testbench",
        "summary": "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
      },
      "minimal_repair_context": {
        "current_board_to_lower_layer_contradiction": {
          "evidence": {
            "causal_localization": {
              "earliest_causal_owner": "single_transformer_layer_kernel",
              "localization_basis": "first_direct_boundary_with_accepted_input_and_ready_zero_output",
              "named_contract_boundary_id": "kernel.mlp_down.output"
            },
            "direct_kernel_boundary_observations": {
              "kernel_egress_ready": true,
              "kernel_ingress_complete": true,
              "kernel_start_accepted": true
            },
            "observation_context": {
              "direct_kernel_observation_fields": {
                "core_egress_accepted_count": 0,
                "core_egress_ready": 1,
                "core_egress_valid": 0,
                "core_ingress_accepted_count": 1792
              },
              "pipeline_boundary_observation": {
                "incomplete_boundary_ids": [
                  "edge.data.block_input.to.stage_00_rms_norm_1.input",
                  "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                  "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
                  "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                  "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                  "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
                  "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
                  "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
                  "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
                  "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
                  "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
                  "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
                  "edge.data.stage_08_residual_add_2.to.block_output.output"
                ],
                "missing_boundary_ids": [
                  "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                  "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                  "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                  "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip"
                ],
                "observed_boundary_count": 9,
                "record_count": 63,
                "required_boundary_count": 13,
                "status": "incomplete"
              }
            },
            "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
            "source_binding": {
              "board_trace_sha256": "a9beca5ed422e60dd2f416e50ae6db3ec92a75c1783e0440dc09c5d7d641ae35",
              "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
              "lower_layer_certificate_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7"
            },
            "status": "proven",
            "target_debug_layer": "single_transformer_layer_kernel"
          },
          "required_observation_contract": {
            "current_trace_and_lower_certificate_hashes_required": true,
            "earliest_causal_owner_must_match_target_layer": true,
            "kernel_egress_ready_required": true,
            "kernel_ingress_complete_required": true,
            "kernel_start_accepted_required": true,
            "named_earliest_causal_boundary_required": true
          },
          "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
          "status": "proven",
          "target_debug_layer": "single_transformer_layer_kernel",
          "validation_errors": []
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
        "vcs_diagnosis_status": "needs_repair",
        "vcs_failure_class": "board_output_lifecycle_frontier_violation"
      },
      "reason": "the current exact-board trace contradicts the prior single-layer pipeline certificate; rerun and repair the connected single-layer kernel before returning to Stage 3",
      "repair_gate": "case_single_layer_functional",
      "repair_kind": "case_single_layer_functional",
      "root_candidate_module": null,
      "scope": "verification_capability_repair",
      "source": "case_vcs_functional_diagnosis",
      "target_modules": [
        "connected_single_transformer_layer_kernel",
        "single_layer_pipeline_overlap_contract"
      ],
      "tool": null,
      "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
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
          "debug_layer": "single_transformer_layer_kernel",
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
          "failure_signature": {
            "current_board_to_lower_layer_contradiction": {
              "evidence": {
                "causal_localization": {
                  "earliest_causal_owner": "single_transformer_layer_kernel",
                  "localization_basis": "first_direct_boundary_with_accepted_input_and_ready_zero_output",
                  "named_contract_boundary_id": "kernel.mlp_down.output"
                },
                "direct_kernel_boundary_observations": {
                  "kernel_egress_ready": true,
                  "kernel_ingress_complete": true,
                  "kernel_start_accepted": true
                },
                "observation_context": {
                  "direct_kernel_observation_fields": {
                    "core_egress_accepted_count": 0,
                    "core_egress_ready": 1,
                    "core_egress_valid": 0,
                    "core_ingress_accepted_count": 1792
                  },
                  "pipeline_boundary_observation": {
                    "incomplete_boundary_ids": [
                      "edge.data.block_input.to.stage_00_rms_norm_1.input",
                      "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                      "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
                      "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                      "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                      "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
                      "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
                      "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
                      "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
                      "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
                      "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
                      "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
                      "edge.data.stage_08_residual_add_2.to.block_output.output"
                    ],
                    "missing_boundary_ids": [
                      "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                      "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                      "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                      "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip"
                    ],
                    "observed_boundary_count": 9,
                    "record_count": 63,
                    "required_boundary_count": 13,
                    "status": "incomplete"
                  }
                },
                "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
                "source_binding": {
                  "board_trace_sha256": "a9beca5ed422e60dd2f416e50ae6db3ec92a75c1783e0440dc09c5d7d641ae35",
                  "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
                  "lower_layer_certificate_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7"
                },
                "status": "proven",
                "target_debug_layer": "single_transformer_layer_kernel"
              },
              "required_observation_contract": {
                "current_trace_and_lower_certificate_hashes_required": true,
                "earliest_causal_owner_must_match_target_layer": true,
                "kernel_egress_ready_required": true,
                "kernel_ingress_complete_required": true,
                "kernel_start_accepted_required": true,
                "named_earliest_causal_boundary_required": true
              },
              "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
              "status": "proven",
              "target_debug_layer": "single_transformer_layer_kernel",
              "validation_errors": []
            },
            "failure_class": "board_output_lifecycle_frontier_violation",
            "repair_scope": "board_rtl_or_testbench",
            "summary": "board_output_lifecycle_frontier_violation: the board trace completed current-layer ingress while the ready output frontier accepted zero beats; direct core-boundary contradiction evidence is still required before reopening the connected kernel"
          },
          "minimal_repair_context": {
            "current_board_to_lower_layer_contradiction": {
              "evidence": {
                "causal_localization": {
                  "earliest_causal_owner": "single_transformer_layer_kernel",
                  "localization_basis": "first_direct_boundary_with_accepted_input_and_ready_zero_output",
                  "named_contract_boundary_id": "kernel.mlp_down.output"
                },
                "direct_kernel_boundary_observations": {
                  "kernel_egress_ready": true,
                  "kernel_ingress_complete": true,
                  "kernel_start_accepted": true
                },
                "observation_context": {
                  "direct_kernel_observation_fields": {
                    "core_egress_accepted_count": 0,
                    "core_egress_ready": 1,
                    "core_egress_valid": 0,
                    "core_ingress_accepted_count": 1792
                  },
                  "pipeline_boundary_observation": {
                    "incomplete_boundary_ids": [
                      "edge.data.block_input.to.stage_00_rms_norm_1.input",
                      "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                      "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
                      "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                      "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                      "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
                      "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
                      "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
                      "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
                      "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
                      "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
                      "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
                      "edge.data.stage_08_residual_add_2.to.block_output.output"
                    ],
                    "missing_boundary_ids": [
                      "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                      "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                      "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                      "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip"
                    ],
                    "observed_boundary_count": 9,
                    "record_count": 63,
                    "required_boundary_count": 13,
                    "status": "incomplete"
                  }
                },
                "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
                "source_binding": {
                  "board_trace_sha256": "a9beca5ed422e60dd2f416e50ae6db3ec92a75c1783e0440dc09c5d7d641ae35",
                  "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
                  "lower_layer_certificate_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7"
                },
                "status": "proven",
                "target_debug_layer": "single_transformer_layer_kernel"
              },
              "required_observation_contract": {
                "current_trace_and_lower_certificate_hashes_required": true,
                "earliest_causal_owner_must_match_target_layer": true,
                "kernel_egress_ready_required": true,
                "kernel_ingress_complete_required": true,
                "kernel_start_accepted_required": true,
                "named_earliest_causal_boundary_required": true
              },
              "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
              "status": "proven",
              "target_debug_layer": "single_transformer_layer_kernel",
              "validation_errors": []
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
            "vcs_diagnosis_status": "needs_repair",
            "vcs_failure_class": "board_output_lifecycle_frontier_violation"
          },
          "reason": "the current exact-board trace contradicts the prior single-layer pipeline certificate; rerun and repair the connected single-layer kernel before returning to Stage 3",
          "repair_gate": "case_single_layer_functional",
          "repair_kind": "case_single_layer_functional",
          "root_candidate_module": null,
          "scope": "verification_capability_repair",
          "source": "case_vcs_functional_diagnosis",
          "target_modules": [
            "connected_single_transformer_layer_kernel",
            "single_layer_pipeline_overlap_contract"
          ],
          "tool": null,
          "violated_contract": "all_spatial_operators_must_form_a_token_level_pipeline"
        },
        "approval_required": false,
        "debug_layer": "single_transformer_layer_kernel",
        "id": "repair_step.00",
        "repair_context": {
          "current_board_to_lower_layer_contradiction": {
            "evidence": {
              "causal_localization": {
                "earliest_causal_owner": "single_transformer_layer_kernel",
                "localization_basis": "first_direct_boundary_with_accepted_input_and_ready_zero_output",
                "named_contract_boundary_id": "kernel.mlp_down.output"
              },
              "direct_kernel_boundary_observations": {
                "kernel_egress_ready": true,
                "kernel_ingress_complete": true,
                "kernel_start_accepted": true
              },
              "observation_context": {
                "direct_kernel_observation_fields": {
                  "core_egress_accepted_count": 0,
                  "core_egress_ready": 1,
                  "core_egress_valid": 0,
                  "core_ingress_accepted_count": 1792
                },
                "pipeline_boundary_observation": {
                  "incomplete_boundary_ids": [
                    "edge.data.block_input.to.stage_00_rms_norm_1.input",
                    "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                    "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
                    "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                    "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                    "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
                    "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
                    "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
                    "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
                    "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
                    "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
                    "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
                    "edge.data.stage_08_residual_add_2.to.block_output.output"
                  ],
                  "missing_boundary_ids": [
                    "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
                    "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
                    "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
                    "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip"
                  ],
                  "observed_boundary_count": 9,
                  "record_count": 63,
                  "required_boundary_count": 13,
                  "status": "incomplete"
                }
              },
              "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
              "source_binding": {
                "board_trace_sha256": "a9beca5ed422e60dd2f416e50ae6db3ec92a75c1783e0440dc09c5d7d641ae35",
                "input_fingerprint_sha256": "a201b3dd8cf14a00d1d33f294f3bce74cca1cb93fd2ac8a483fbdd67f50ccca6",
                "lower_layer_certificate_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7"
              },
              "status": "proven",
              "target_debug_layer": "single_transformer_layer_kernel"
            },
            "required_observation_contract": {
              "current_trace_and_lower_certificate_hashes_required": true,
              "earliest_causal_owner_must_match_target_layer": true,
              "kernel_egress_ready_required": true,
              "kernel_ingress_complete_required": true,
              "kernel_start_accepted_required": true,
              "named_earliest_causal_boundary_required": true
            },
            "schema_version": "spatialaccagent.board_to_lower_layer_contradiction_evidence.v1",
            "status": "proven",
            "target_debug_layer": "single_transformer_layer_kernel",
            "validation_errors": []
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
          "vcs_diagnosis_status": "needs_repair",
          "vcs_failure_class": "board_output_lifecycle_frontier_violation"
        },
        "scope": "verification_capability_repair",
        "source": "case_vcs_functional_diagnosis",
        "status": "ready_for_agent_patch",
        "target_modules": [
          "connected_single_transformer_layer_kernel",
          "single_layer_pipeline_overlap_contract"
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
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json
</source_sacg_state>

<completed_lower_layer_capabilities>
[
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
]
</completed_lower_layer_capabilities>

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
      "last_observed_at": "2026-09-09T09:40:25+00:00",
      "observation_count": 41,
      "observed_transition_ids": [
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
        "transition.2502"
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
      "observation_count": 1,
      "observed_transition_ids": [
        "transition.2495"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-06T05:44:16+00:00",
      "transition_id": "transition.2495",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "debug_layer": "board_axi_ddr_wrapped_system",
  "omitted_unscoped_cross_layer_or_limit_counts": {
    "backtrack_requests": 1,
    "contamination_barriers": 12,
    "failure_lessons": 214,
    "retry_requests": 0,
    "stage_outcomes": 225
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
      "last_observed_at": "2026-09-09T09:40:25+00:00",
      "observation_count": 41,
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
      "id": "failure_lesson.0215",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-05T11:31:10+00:00",
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
      "id": "failure_lesson.0216",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-06T05:43:46+00:00",
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
      "id": "failure_lesson.0217",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-06T15:08:23+00:00",
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
      "id": "failure_lesson.0218",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-07T01:39:47+00:00",
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
      "id": "failure_lesson.0219",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-07T13:28:42+00:00",
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
      "id": "failure_lesson.0220",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-07T13:35:31+00:00",
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
      "id": "failure_lesson.0221",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-09T09:33:07+00:00",
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
      "id": "failure_lesson.0222",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Fail-closed authoritative Stage7 decision: board_axi_ddr_closure is not promotable to backend synthesis, implementation, bitstream generation, runtime-ABI release, or board runtime. The earliest executed current-layer failure is real_tool.case_axi_ddr_interface: the board simulation manifest does not bind the current exact board identity, its compile authority and ordered-command authority references do not bind the exact Vivado export facts, and its simulator executables are not authorized by the current tool profile or cited export. The real board-wrapped VCS simulation was dependency-skipped, so there is no board-level functional, numeric, data-order, AXI, DDR, liveness, complete-weight-consumption, lifecycle-frontier, or output evidence. Current operator-leaf and connected single-layer certificates remain reusable because no current hash-bound trace contradicts a named lower-layer invariant. The conditional design-team router returned no_split; role consensus or the absence of a specialist review cannot replace missing deterministic evidence.",
      "timestamp": "2026-09-09T09:40:25+00:00",
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
      "id": "stage_outcome.0226",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-05T11:31:10+00:00",
      "transition_id": "transition.2480",
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
      "id": "stage_outcome.0227",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-06T05:43:46+00:00",
      "transition_id": "transition.2494",
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
      "id": "stage_outcome.0228",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-06T15:08:23+00:00",
      "transition_id": "transition.2497",
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
      "id": "stage_outcome.0229",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-07T01:39:47+00:00",
      "transition_id": "transition.2498",
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
      "id": "stage_outcome.0230",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-07T13:28:42+00:00",
      "transition_id": "transition.2499",
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
      "id": "stage_outcome.0231",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-07T13:35:31+00:00",
      "transition_id": "transition.2500",
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
      "id": "stage_outcome.0232",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-09T09:33:07+00:00",
      "transition_id": "transition.2501",
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
      "id": "stage_outcome.0233",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-09-09T09:40:25+00:00",
      "transition_id": "transition.2502",
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
  "active_contamination_barrier_count": 17,
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
      "last_observed_at": "2026-09-09T09:40:25+00:00",
      "observation_count": 41,
      "observed_transition_ids": [
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
        "transition.2502"
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
      "observation_count": 1,
      "observed_transition_ids": [
        "transition.2495"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-09-06T05:44:16+00:00",
      "transition_id": "transition.2495",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "active_contamination_barriers_truncated": false,
  "debug_layer": "board_axi_ddr_wrapped_system",
  "global_persisted_blocker_counts": {
    "active_contamination_barriers": 20,
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
      "last_observed_at": "2026-09-09T09:40:25+00:00",
      "observation_count": 41,
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
