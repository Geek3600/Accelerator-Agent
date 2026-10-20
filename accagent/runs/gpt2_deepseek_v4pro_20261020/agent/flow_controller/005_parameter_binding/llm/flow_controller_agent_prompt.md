<agent>
flow_controller_agent
</agent>

<task>
Review SACG memory and the latest stage result, then decide whether the autonomous design team should proceed, retry the current stage, backtrack to an earlier stage, run bounded repair, or stop to avoid artifact contamination. Framework, hash, manifest, provenance, evidence-binding, or stage-routing failures must never rewind hardware design stages; retry the failed current stage. Backtracking is allowed only when the action names a hardware-design failure category and cites failed gates, measurements, a critical path, or tool evidence. For backend timing, use the run-local timing repair executed by Stage 7; when its status is compiled_pending_vcs, request current-source compile-only verification and return to Stage 7, never code_generation or parameter_binding.
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
18. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or action_grounding_registry.acceptance_checkers, or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
19. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
20. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
21. When hierarchical_learning_context is supplied, treat it as live hash-validated lower-layer knowledge rather than informal history. Reuse its certified invariants, and reopen a lower layer only for a current trace that explicitly contradicts a named invariant.
22. When hierarchical_learning_context supplies connected-kernel timing knowledge, preserve its elastic variable-latency token-pipeline semantics: required boundary order and cross-token overlap matter, while strict same-cycle start/end across unequal-latency stages is not required.
23. At board scope, distinguish independent AXI/prefetch progress from output or lifecycle-frontier progress. A current frontier stall localizes what to observe next, but is neither a pass claim nor a preselected RTL root cause.
24. A board output-frontier symptom alone cannot reopen a certified connected kernel. Require a current hash-bound lower-layer contradiction with direct core start, ingress, egress, named causal-boundary, and current-certificate evidence before scheduling lower-layer revalidation.
25. At every verification layer, use successful current-source VCS compilation, elaboration, and linking as the sole acceptance standard. Repair actual compiler errors; do not add runtime, golden-output, waveform, or weight-consumption prerequisites.
26. The action_grounding_registry.verification_execution_policy documents the existing compile-only modes of the leaf, connected-kernel and exact-board tools. These modes already execute real VCS compile/elaboration/link without running simulation. A functional_sim role name does not imply simulation must execute. Reuse these existing roles rather than declaring a planned_tool capability gap solely from their names. At verification_artifacts planning, future VCS certificates are downstream obligations; actual execution still requires them in bottom-up order before backend synthesis.
27. Applying the recorded framework loose defaults for initially missing atol, rtol, or max_mismatch_fraction is authorized and is not a repair-time tolerance change. Never derive or loosen those values from DUT output.
28. A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.
29. During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.
30. At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.
31. Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.
32. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
33. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
34. Use exact internal stage names for backtrack targets. Public Stage 5 contains both code_generation and verification_artifacts: verification-plan, artifact-contract, or action-audit repairs target verification_artifacts; hardware regeneration targets code_generation. Do not use the ambiguous label stage5 for those actions.
35. For Stage-7 loader-to-DUT mapping failures, case_compute_slot_adapter_generate is an existing bounded repair path. Prefer that real tool and its current hash-verified board-source context over a separate planned_tool read-only audit; a missing dedicated audit role alone is not a missing system capability. When validated_stage6_selection passes, preserve that exact target without asking for approval merely to restate it. Keep approval for changing the target or semantic contracts.
36. For a Stage-7 read-only trust, provenance, or identity audit, compose the registered checks such as stage_artifact_trust_barrier_check, verification_action_audit_check, artifact_hash_check, sacg_memory_check, stage_backtrack_request_check, and stage_retry_request_check. Do not request a new planned_tool or planned_checker only because no single registered role wraps the whole audit; keep unresolved barriers active until the existing checks pass, and name a capability gap only for a specific required check that none of the registered capabilities can perform.
37. For a Stage-6 trace replay, include targeted_replay_plan with the current stage_id and rerun_env.SPATIALACC_TARGET_BOUNDARY set to a specific boundary from the supplied failure-localization evidence. Use targeted_replay_history when supplied: a new rationale, probe label, or unused plan field is not a new observation unless the effective trace environment or semantic input fingerprint changes. Choose a boundary not already observed for the same stage and semantic inputs; state what root-cause alternatives the new signal distinguishes, or return a bounded replan instead of authorizing another VCS replay.
</rules>

<current_stage>
parameter_binding
</current_stage>

<stage_passed>
true
</stage_passed>

<attempt_count>
1
</attempt_count>

<available_stages>
[
  "input_preparation",
  "constraint_extraction",
  "template_selection",
  "pipeline_planning",
  "parameter_binding",
  "code_generation",
  "verification_artifacts",
  "debug_loop",
  "backend_board"
]
</available_stages>

<recent_stage_summary>
{
  "axi_transfer_layout": {
    "board_axi": {
      "addr_width_bits": 37,
      "alignment_bytes": 64,
      "core_side_interface_name": "c0_ddr4_s_axi_*",
      "data_bytes": 64,
      "data_width_bits": 512,
      "ddr_channels": 1,
      "protocol": "AXI",
      "source": "constraint.memory.board.memory_system"
    },
    "layout_kind": "exact_tensor_shape_transfer_layout",
    "notes": [
      "Stage 5 assigns concrete base addresses and checks non-overlap/alignment.",
      "Stage 6+ must provide real simulation, implementation, timing, and board evidence."
    ],
    "per_stage": [
      {
        "aligned_bytes": 25344,
        "axi_beats": 396,
        "input_activation_bytes": 12288,
        "input_bits": 8,
        "op": "layer_norm_1",
        "output_activation_bytes": 12288,
        "output_bits": 8,
        "stage_id": "stage_00_layer_norm_1",
        "total_bytes": 25344,
        "weight_bytes": 768,
        "weight_term_ids": [
          "ln_1_weight",
          "ln_1_bias"
        ]
      },
      {
        "aligned_bytes": 1216512,
        "axi_beats": 19008,
        "input_activation_bytes": 12288,
        "input_bits": 8,
        "op": "self_attention",
        "output_activation_bytes": 12288,
        "output_bits": 8,
        "stage_id": "stage_01_self_attention",
        "total_bytes": 1216512,
        "weight_bytes": 1191936,
        "weight_term_ids": [
          "attn_c_attn_weight",
          "attn_c_attn_bias",
          "attn_c_proj_weight",
          "attn_c_proj_bias"
        ]
      },
      {
        "aligned_bytes": 24576,
        "axi_beats": 384,
        "input_activation_bytes": 12288,
        "input_bits": 8,
        "op": "residual_add_1",
        "output_activation_bytes": 12288,
        "output_bits": 8,
        "stage_id": "stage_02_residual_add_1",
        "total_bytes": 24576,
        "weight_bytes": 0,
        "weight_term_ids": []
      },
      {
        "aligned_bytes": 25344,
        "axi_beats": 396,
        "input_activation_bytes": 12288,
        "input_bits": 8,
        "op": "layer_norm_2",
        "output_activation_bytes": 12288,
        "output_bits": 8,
        "stage_id": "stage_03_layer_norm_2",
        "total_bytes": 25344,
        "weight_bytes": 768,
        "weight_term_ids": [
          "ln_2_weight",
          "ln_2_bias"
        ]
      },
      {
        "aligned_bytes": 1253376,
        "axi_beats": 19584,
        "input_activation_bytes": 12288,
        "input_bits": 8,
        "op": "mlp_fc",
        "output_activation_bytes": 49152,
        "output_bits": 8,
        "stage_id": "stage_04_mlp_fc",
        "total_bytes": 1253376,
        "weight_bytes": 1191936,
        "weight_term_ids": [
          "mlp_c_fc_weight",
          "mlp_c_fc_bias"
        ]
      },
      {
        "aligned_bytes": 98304,
        "axi_beats": 1536,
        "input_activation_bytes": 49152,
        "input_bits": 8,
        "op": "activation",
        "output_activation_bytes": 49152,
        "output_bits": 8,
        "stage_id": "stage_05_activation",
        "total_bytes": 98304,
        "weight_bytes": 0,
        "weight_term_ids": []
      },
      {
        "aligned_bytes": 1244160,
        "axi_beats": 19440,
        "input_activation_bytes": 49152,
        "input_bits": 8,
        "op": "mlp_proj",
        "output_activation_bytes": 12288,
        "output_bits": 8,
        "stage_id": "stage_06_mlp_proj",
        "total_bytes": 1244160,
        "weight_bytes": 1182720,
        "weight_term_ids": [
          "mlp_c_proj_weight",
          "mlp_c_proj_bias"
        ]
      },
      {
        "aligned_bytes": 24576,
        "axi_beats": 384,
        "input_activation_bytes": 12288,
        "input_bits": 8,
        "op": "residual_add_2",
        "output_activation_bytes": 12288,
        "output_bits": 8,
        "stage_id": "stage_07_residual_add_2",
        "total_bytes": 24576,
        "weight_bytes": 0,
        "weight_term_ids": []
      }
    ],
    "schema_version": "spatialaccagent.parameter_axi_transfer_layout.v1",
    "total_aligned_bytes_per_layer": 3912192,
    "used_for": "static AXI alignment and packing checks only; not bandwidth, timing, power, or throughput evidence"
  },
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 6,
    "warnings": []
  },
  "design_team": {
    "executable_actions": [],
    "reason": "DSE selection and deterministic parameter checks gate the exact measurement handoff.",
    "status": "not_required_for_measurement_handoff"
  },
  "dse_measurement_summary": {
    "complete": false,
    "implementation_infeasible_count": 0,
    "legal_candidate_count": 360,
    "measured_candidate_count": 0,
    "unmeasured_candidate_count": 360
  },
  "dse_selection_rationale": {
    "campaign_complete": false,
    "eligibility_reason": "Selected candidate is legal and has no target-board app-shell measurement yet.",
    "llm_assumptions": [
      "estimated_ranked_candidate_ids is the calibrated structural estimator's measurement-priority order even though qor_estimate status is insufficient_evidence.",
      "The selected candidate's parameters are exactly those in dse_selection_evidence and must not be changed.",
      "No candidate has measured QoR yet, so no optimality or Pareto claim is made.",
      "Resource budget is a capacity constraint; exact feasibility is determined by the app-shell synthesis measurement.",
      "The deterministic evaluator remains the authority on legality, measured status, and Pareto membership."
    ],
    "llm_ranked_candidate_ids": [
      "arch_08fc81fe6157",
      "arch_31c1198760c0",
      "arch_3fd8f432a88e",
      "arch_3fedd13a9880",
      "arch_513408c9134d",
      "arch_55b127fde887",
      "arch_5b4f9ef48e3b",
      "arch_63e2712b0d8c",
      "arch_6e9d2e7c3ed7",
      "arch_74c0530f0375"
    ],
    "llm_rationale": "No candidate has an exact app-shell measurement, so the deterministic rule requires selecting one supplied unmeasured legal candidate for next measurement. The supplied estimated_ranked_candidate_ids gives arch_08fc81fe6157 the highest measurement priority. It is legal, unmeasured, uses substantial compute parallelism within the discovered budget bounds, and therefore is the appropriate next exact measurement without implying measured QoR or Pareto membership.",
    "llm_requested_candidate_id": "arch_08fc81fe6157",
    "qor_estimate": {
      "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
      "reason": "no compatible source-bound calibration sample",
      "status": "insufficient_evidence"
    },
    "qor_estimator": {
      "model": "calibrated_bounded_ddr_pipeline_ratio_v10_integer_precision_image_abi",
      "validation": {
        "held_out_prediction_count": 0,
        "mean_absolute_error_for_zero_actual": {},
        "mean_relative_absolute_error": {},
        "method": "leave_one_source_fingerprint_out",
        "sample_count": 1,
        "status": "insufficient_independent_samples"
      }
    },
    "requires_measurement": [
      "integrated Vivado implementation resources",
      "post-implementation Vivado power",
      "achieved clock frequency",
      "hardware-counter-derived tokens per second"
    ],
    "schema_version": "spatialaccagent.stage4_dse_selection_rationale.v2",
    "selected_candidate_id": "arch_08fc81fe6157",
    "selection_source": "llm_measurement_order",
    "status": "ready"
  },
  "errors": [],
  "formal_dse_campaign": {
    "campaign_complete": false,
    "policy": {
      "next_required_evidence": "exact_target_board_app_shell",
      "no_qor_or_hardware_pass_claim_before_measurement": true
    },
    "promotion_scope": "candidate_binding_for_exact_target_board_app_shell_measurement",
    "selected_candidate_requires_exact_measurement": true,
    "status": "measurement_pending"
  },
  "global_params": {
    "acc_bits": 32,
    "activation_banks": 4,
    "activation_memory": "xpm_bram",
    "burst_beats": 1,
    "cache_refill_data_width_bits": 512,
    "cache_tile_count": 2,
    "cache_tile_words": 256,
    "clock_target_mhz": null,
    "compute_array_cols": 32,
    "compute_array_rows": 16,
    "compute_backend": "integer_dsp",
    "cross_token_reuse_tokens": 8,
    "elem_bits": 8,
    "fifo_depth": 128,
    "fifo_memory": "xpm_bram",
    "input_bits": 8,
    "integer_mode": true,
    "lanes": 16,
    "large_cache_memory": "xpm_uram",
    "output_bits": 8,
    "pipeline_depth": 1,
    "rounding": "nearest_even",
    "saturation": true,
    "scale_bits": 32,
    "scale_shift": 31,
    "weight_banks": 1,
    "weight_banks_by_role": {
      "weight": 1,
      "weight_attn_out": 1,
      "weight_attn_out_bias": 1,
      "weight_mlp_down": 1,
      "weight_mlp_down_bias": 1,
      "weight_mlp_up": 1,
      "weight_mlp_up_bias": 1,
      "weight_qkv": 1,
      "weight_qkv_bias": 1
    },
    "weight_bits": 4,
    "weight_memory": "xpm_uram"
  },
  "legality_errors": [],
  "llm_agent": {
    "agent": "dse_parameter_agent",
    "approval_required_for": [],
    "assumptions": [
      "estimated_ranked_candidate_ids is the calibrated structural estimator's measurement-priority order even though qor_estimate status is insufficient_evidence.",
      "The selected candidate's parameters are exactly those in dse_selection_evidence and must not be changed.",
      "No candidate has measured QoR yet, so no optimality or Pareto claim is made.",
      "Resource budget is a capacity constraint; exact feasibility is determined by the app-shell synthesis measurement.",
      "The deterministic evaluator remains the authority on legality, measured status, and Pareto membership."
    ],
    "executable_actions": [
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "real_tool.case_vivado_synthesis",
          "real_tool.case_vivado_synthesis_report_check",
          "timing_resource_check"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "dse_selection_evidence.candidate.arch_08fc81fe6157",
          "dse_constraint_report.json",
          "materialized_refill_rate_contract.value=512"
        ],
        "id": "dse_measure.arch_08fc81fe6157.next_exact_synthesis",
        "on_failure": "Record the actual synthesis failure or implementation infeasibility in dse_measurements.jsonl; do not modify candidate parameters, do not claim QoR or hardware pass, and advance measurement priority to the next supplied unmeasured legal candidate in estimated_ranked_candidate_ids unless the deterministic evaluator flags legality.",
        "produces": [
          "dse_measurements.jsonl.entry.arch_08fc81fe6157",
          "vivado_utilization_report.arch_08fc81fe6157",
          "vivado_timing_report.arch_08fc81fe6157",
          "rtl_cycle_derived_throughput.arch_08fc81fe6157"
        ],
        "rationale": "No legal candidate is measured yet, so the campaign requires a measurement-order handoff. arch_08fc81fe6157 is the first supplied unmeasured legal candidate in estimated_ranked_candidate_ids and therefore has the highest measurement priority; resource budget remains a capacity check, not a reason to prefer a smaller array before measuring this candidate.",
        "requires_approval": false,
        "stage": "stage4_dse_search",
        "targeted_replay_plan": {
          "candidate_id": "arch_08fc81fe6157",
          "parameters": {
            "activation_banks": 4,
            "cache_refill_data_width_bits": 512,
            "cache_tile_count": 2,
            "cache_tile_words": 256,
            "compute_array_cols": 32,
            "compute_array_rows": 16,
            "cross_token_reuse_tokens": 8,
            "fifo_depth": 128,
            "lanes": 16
          },
          "scope": "target_board_app_shell_synthesis_measurement"
        },
        "tool_roles": [
          "case_vivado_synthesis",
          "case_vivado_synthesis_report_check",
          "timing_resource_check"
        ]
      }
    ],
    "observations": [
      "Campaign complete=false; measured_candidate_count=0 and unmeasured_candidate_count=360.",
      "Supplied measured_pareto_candidates is empty, so Pareto-final selection is not permitted yet.",
      "qor_estimator validation status is insufficient_independent_samples; every listed candidate has qor_estimate.status=insufficient_evidence.",
      "The supplied estimated_ranked_candidate_ids list opens with arch_08fc81fe6157, so it is the measurement-priority candidate.",
      "arch_08fc81fe6157 is legal and unmeasured in dse_selection_evidence.",
      "arch_08fc81fe6157 parameters: activation_banks=4, cache_refill_data_width_bits=512, cache_tile_count=2, cache_tile_words=256, compute_array_cols=32, compute_array_rows=16, cross_token_reuse_tokens=8, fifo_depth=128, lanes=16.",
      "Resource lower bound for arch_08fc81fe6157 is uram=30, below the discovered uram budget of 960, but all other resource usage remains unknown until measurement.",
      "DSE constraint report status is pass with 360 feasible candidates and 0 infeasible candidates.",
      "materialized_refill_rate_contract status is pass with value 512 bits/cycle."
    ],
    "proposed_actions": [
      "Hand off arch_08fc81fe6157 to the exact target-board app-shell synthesis measurement tool.",
      "Record resource counts, Vivado estimated clock, and RTL-cycle-derived tokens per second only if the measurement completes successfully.",
      "After measurement, let the deterministic evaluator update measured/unmeasured status and recalibrate downstream estimates.",
      "If arch_08fc81fe6157 fails or is infeasible, advance to the next supplied unmeasured legal candidate in estimated_ranked_candidate_ids without modifying its parameters."
    ],
    "ranked_candidate_ids": [
      "arch_08fc81fe6157",
      "arch_31c1198760c0",
      "arch_3fd8f432a88e",
      "arch_3fedd13a9880",
      "arch_513408c9134d",
      "arch_55b127fde887",
      "arch_5b4f9ef48e3b",
      "arch_63e2712b0d8c",
      "arch_6e9d2e7c3ed7",
      "arch_74c0530f0375"
    ],
    "risks": [
      "Actual Vivado resource usage, timing, and derived throughput are unknown for arch_08fc81fe6157; the top estimated rank is not feasibility evidence.",
      "The estimator has only one calibration sample and insufficient independent validation, so cross-model or cross-configuration extrapolation may be unreliable.",
      "A 32x16 compute array with 16 lanes may stress DSP, FF, LUT, or BRAM resources even though the URAM lower bound is low.",
      "Treating the rank as QoR would violate the rule that predictions never replace measured tool evidence.",
      "Measurement may fail or be implementation-infeasible; this is a bounded learning outcome, not a license to alter parameters."
    ],
    "sacg_focus": {
      "artifacts": [
        "dse_selection_evidence",
        "dse_constraint_report",
        "dse_measurements.jsonl",
        "estimated_ranked_candidate_ids"
      ],
      "constraints": [
        "Before all legal candidates are measured, select only one supplied unmeasured legal candidate for measurement.",
        "Do not describe an unmeasured candidate as optimal or Pareto-optimal.",
        "Resource budgets are capacity constraints, not minimization objectives.",
        "Structural estimates rank measurement priority but never replace tool evidence.",
        "Unknown or near-capacity resource usage is not final eligibility evidence.",
        "Do not modify candidate parameters or claim hardware pass before measurement."
      ],
      "edges": [
        "candidate_arch_08fc81fe6157 -> target_board_app_shell_synthesis_measurement",
        "target_board_app_shell_synthesis_measurement -> dse_measurement_campaign",
        "qor_estimator_calibration -> estimated_ranked_candidate_ids",
        "estimated_ranked_candidate_ids -> candidate_arch_08fc81fe6157"
      ],
      "nodes": [
        "dse_measurement_campaign",
        "candidate_arch_08fc81fe6157",
        "estimated_ranked_candidate_ids",
        "qor_estimator_calibration",
        "target_board_app_shell_synthesis_measurement"
      ]
    },
    "schema_version": "spatialaccagent.stage4_dse_search.v2",
    "selected_candidate_id": "arch_08fc81fe6157",
    "selection_rationale": "No candidate has an exact app-shell measurement, so the deterministic rule requires selecting one supplied unmeasured legal candidate for next measurement. The supplied estimated_ranked_candidate_ids gives arch_08fc81fe6157 the highest measurement priority. It is legal, unmeasured, uses substantial compute parallelism within the discovered budget bounds, and therefore is the appropriate next exact measurement without implying measured QoR or Pareto membership.",
    "stage": "stage4_dse_search",
    "status": "next_exact_measurement_selected",
    "summary": "Campaign is not complete and no legal candidates have target-board app-shell measurements. Selected the supplied estimated-rank-first unmeasured legal candidate arch_08fc81fe6157 as the next exact synthesis measurement; this is a measurement-order handoff only, not an optimality, Pareto, feasibility, or hardware-pass claim."
  },
  "llm_executable_actions": [
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "real_tool.case_vivado_synthesis",
        "real_tool.case_vivado_synthesis_report_check",
        "timing_resource_check"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "dse_selection_evidence.candidate.arch_08fc81fe6157",
        "dse_constraint_report.json",
        "materialized_refill_rate_contract.value=512"
      ],
      "id": "dse_measure.arch_08fc81fe6157.next_exact_synthesis",
      "on_failure": "Record the actual synthesis failure or implementation infeasibility in dse_measurements.jsonl; do not modify candidate parameters, do not claim QoR or hardware pass, and advance measurement priority to the next supplied unmeasured legal candidate in estimated_ranked_candidate_ids unless the deterministic evaluator flags legality.",
      "produces": [
        "dse_measurements.jsonl.entry.arch_08fc81fe6157",
        "vivado_utilization_report.arch_08fc81fe6157",
        "vivado_timing_report.arch_08fc81fe6157",
        "rtl_cycle_derived_throughput.arch_08fc81fe6157"
      ],
      "rationale": "No legal candidate is measured yet, so the campaign requires a measurement-order handoff. arch_08fc81fe6157 is the first supplied unmeasured legal candidate in estimated_ranked_candidate_ids and therefore has the highest measurement priority; resource budget remains a capacity check, not a reason to prefer a smaller array before measuring this candidate.",
      "requires_approval": false,
      "stage": "stage4_dse_search",
      "targeted_replay_plan": {
        "candidate_id": "arch_08fc81fe6157",
        "parameters": {
          "activation_banks": 4,
          "cache_refill_data_width_bits": 512,
          "cache_tile_count": 2,
          "cache_tile_words": 256,
          "compute_array_cols": 32,
          "compute_array_rows": 16,
          "cross_token_reuse_tokens": 8,
          "fifo_depth": 128,
          "lanes": 16
        },
        "scope": "target_board_app_shell_synthesis_measurement"
      },
      "tool_roles": [
        "case_vivado_synthesis",
        "case_vivado_synthesis_report_check",
        "timing_resource_check"
      ]
    }
  ],
  "llm_memory_claim_audit": {
    "inactive_sacg_memory_blocker_status_ignored": false,
    "sacg_memory_truth": {
      "active_contamination_barrier_count": 0,
      "active_contamination_barriers": [],
      "active_contamination_barriers_truncated": false,
      "open_backtrack_request_count": 0,
      "open_backtrack_requests": [],
      "open_backtrack_requests_truncated": false,
      "open_retry_request_count": 0,
      "open_retry_requests": [],
      "open_retry_requests_truncated": false,
      "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
      "schema_version": "spatialaccagent.sacg_memory_truth.v0",
      "truth_source": "source_sacg_state.memory"
    },
    "schema_version": "spatialaccagent.llm_memory_claim_audit.v0"
  },
  "materialized_refill_rate_contract": {
    "board_width_discovered_from": "constraint.memory.board.memory_system.axi_data_width_bits",
    "candidate_bindings": [
      512
    ],
    "largest_board_supported_width": 512,
    "materialized_refill_rate_bits_per_cycle": 512,
    "optimistic_axi_beat_rate_credited": false,
    "parameter": "cache_refill_data_width_bits",
    "payload_is_not_address_or_count_units": true,
    "response_words_per_cycle": 16,
    "scalar_payload_fallback_allowed": false,
    "source": "exact_board_ddr_tile_service.aggregate_response_data_width_bits",
    "status": "pass",
    "supported_widths": [
      512
    ],
    "value": 512
  },
  "num_bindings": 8,
  "numeric_binding_plan": {
    "acc_dtype": "int32",
    "accumulator_bits": 32,
    "activation_bits": 8,
    "activation_dtype": "int8",
    "cast_points": [
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "layer_norm_1",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": null,
        "stage_id": "stage_00_layer_norm_1"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "self_attention",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": null,
        "stage_id": "stage_01_self_attention"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "residual_add_1",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": 8,
        "stage_id": "stage_02_residual_add_1"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "layer_norm_2",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": null,
        "stage_id": "stage_03_layer_norm_2"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "mlp_fc",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": null,
        "stage_id": "stage_04_mlp_fc"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "activation",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": null,
        "stage_id": "stage_05_activation"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "mlp_proj",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": null,
        "stage_id": "stage_06_mlp_proj"
      },
      {
        "input_bits": 8,
        "input_cast": "none",
        "internal_elem_bits": 8,
        "op": "residual_add_2",
        "output_bits": 8,
        "output_cast": "none",
        "residual_precision": 8,
        "stage_id": "stage_07_residual_add_2"
      }
    ],
    "eps_source": "constraint.model.decoder.norm_type/default eps from template binding",
    "fixed_point_contract": {
      "binary_exponent_is_consumed_by_requantizer": true,
      "binary_exponent_width_bits": 8,
      "fractional_bits": 31,
      "multiplier_bits": 32,
      "multiplier_dtype": "int32",
      "representation": "unsigned_q31_multiplier_times_signed_per_tensor_or_per_channel_binary_exponent",
      "rounding": "nearest_even",
      "saturation": true,
      "shift_is_explicit": true
    },
    "policy_id": "current_run_numeric_policy",
    "rounding": "nearest_even",
    "saturation": true,
    "scale_bits": 32,
    "scale_dtype": "int32",
    "source": "constraint.numeric.policy.default_rules",
    "weight_bits": 4,
    "weight_dtype": "int4"
  },
  "outputs": {
    "dse_candidate_records": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_candidate_records.jsonl",
    "dse_constraint_report": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_constraint_report.json",
    "dse_measurements": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_measurements.jsonl",
    "dse_pareto_frontier": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_pareto_frontier.json",
    "dse_search_space": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_search_space.json",
    "dse_selection_rationale": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_selection_rationale.json",
    "llm_agent": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/llm/dse_parameter_agent_result.json",
    "parameter_binding": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/parameter_binding.json",
    "parameter_static_checks": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/parameter_static_checks.json",
    "sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/sacg_state.json",
    "selected_architecture": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/selected_architecture.json"
  },
  "sacg_transition_id": "transition.0003",
  "schema_version": "spatialaccagent.parameter_binding_report.v0",
  "selected_architecture": {
    "candidate_id": "arch_08fc81fe6157",
    "measurement": null,
    "parameters": {
      "activation_banks": 4,
      "activation_memory": "xpm_bram",
      "cache_refill_data_width_bits": 512,
      "cache_tile_count": 2,
      "cache_tile_words": 256,
      "compute_array_cols": 32,
      "compute_array_rows": 16,
      "compute_backend": "integer_dsp",
      "cross_token_reuse_tokens": 8,
      "fifo_depth": 128,
      "fifo_memory": "xpm_bram",
      "lanes": 16,
      "large_cache_memory": "xpm_uram",
      "weight_banks": 1,
      "weight_banks_by_role": {
        "weight": 1,
        "weight_attn_out": 1,
        "weight_attn_out_bias": 1,
        "weight_mlp_down": 1,
        "weight_mlp_down_bias": 1,
        "weight_mlp_up": 1,
        "weight_mlp_up_bias": 1,
        "weight_qkv": 1,
        "weight_qkv_bias": 1
      },
      "weight_memory": "xpm_uram"
    },
    "selection_rationale": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/dse_selection_rationale.json"
  },
  "source_sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/pipeline_planning/sacg_state.json",
  "stage": "parameter_binding",
  "status": "ready",
  "stream_contract_trace": [
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_00_layer_norm_1",
      "edge_id": "edge.data.block_input.to.stage_00_layer_norm_1.input",
      "element_bits": 8,
      "kind": "input",
      "src_output_bits": 8,
      "src_stage": "block_input",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
      "element_bits": 8,
      "kind": "residual_skip",
      "src_output_bits": 8,
      "src_stage": "block_input",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_01_self_attention",
      "edge_id": "edge.data.stage_00_layer_norm_1.to.stage_01_self_attention.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_00_layer_norm_1",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_02_residual_add_1",
      "edge_id": "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_01_self_attention",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_03_layer_norm_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_03_layer_norm_2.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_02_residual_add_1",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_02_residual_add_1.to.stage_07_residual_add_2.residual_skip",
      "element_bits": 8,
      "kind": "residual_skip",
      "src_output_bits": 8,
      "src_stage": "stage_02_residual_add_1",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_04_mlp_fc",
      "edge_id": "edge.data.stage_03_layer_norm_2.to.stage_04_mlp_fc.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_03_layer_norm_2",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_05_activation",
      "edge_id": "edge.data.stage_04_mlp_fc.to.stage_05_activation.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_04_mlp_fc",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 3072
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_06_mlp_proj",
      "edge_id": "edge.data.stage_05_activation.to.stage_06_mlp_proj.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_05_activation",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 3072
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "stage_07_residual_add_2",
      "edge_id": "edge.data.stage_06_mlp_proj.to.stage_07_residual_add_2.main",
      "element_bits": 8,
      "kind": "main",
      "src_output_bits": 8,
      "src_stage": "stage_06_mlp_proj",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    },
    {
      "dst_input_bits": 8,
      "dst_stage": "block_output",
      "edge_id": "edge.data.stage_07_residual_add_2.to.block_output.output",
      "element_bits": 8,
      "kind": "output",
      "src_output_bits": 8,
      "src_stage": "stage_07_residual_add_2",
      "stream_order": [
        "token",
        "tile",
        "lane",
        "word"
      ],
      "tensor": {
        "seq_len": 16,
        "width": 768
      }
    }
  ],
  "team_executable_actions": []
}
</recent_stage_summary>

<command>
[
  "/usr/bin/python3",
  "-m",
  "accagent.framework.stage_params",
  "--sacg-state",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/pipeline_planning/sacg_state.json"
]
</command>

<command_returncode>
0
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/agent/logs/05_parameter_binding.json
</command_log>

<sacg_memory>
{
  "active_contamination_barriers": [],
  "open_backtrack_requests": [],
  "open_retry_requests": [],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [],
  "recent_failure_lessons": [],
  "recent_stage_outcomes": [
    {
      "artifacts": [
        "artifact.stage4.dse_search_space",
        "artifact.stage4.dse_candidate_records",
        "artifact.stage4.dse_constraint_report",
        "artifact.stage4.dse_pareto_frontier",
        "artifact.stage4.dse_measurements",
        "artifact.stage4.selected_architecture",
        "artifact.stage4.dse_selection_rationale",
        "artifact.stage4.parameter_binding",
        "artifact.stage4.parameter_static_checks"
      ],
      "errors": [],
      "id": "stage_outcome.0001",
      "next_actions": [],
      "retryable": false,
      "stage": "stage4.parameter_binding",
      "status": "ready",
      "summary": "parameter static checks passed",
      "timestamp": "2026-10-20T12:57:18+00:00",
      "transition_id": "transition.0003"
    }
  ],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/sacg_state.json
</source_sacg_state>

<stage_local_capabilities>
{
  "backend_board": {
    "compiled_pending_vcs": "the source-local patch and Chisel elaboration are complete; verify current sources compile-only, then return to Stage 7 synthesis",
    "run_local_timing_repair": "stage_backend invokes repair_timing_sources on current-run RTL after local_optimization is selected",
    "timing_repair_scope": "preserve Stage-4 parameters and shared templates; never restart code_generation for timing-only repair"
  }
}
</stage_local_capabilities>

<flow_policy>
{
  "allowed_design_backtrack_categories": [
    "design_defect",
    "hardware_design_failure",
    "design_target_miss",
    "timing_target_miss",
    "resource_limit_exceeded",
    "functional_design_failure",
    "rtl_design_failure",
    "performance_target_miss"
  ],
  "backend_timing_repair_does_not_need_a_planned_tool": true,
  "backtrack_counters_are_observability_only": true,
  "compiled_pending_vcs_must_not_restart_code_generation": true,
  "design_backtrack_requires_explicit_failure_category_and_linked_evidence": true,
  "do_not_use_failed_artifacts_as_validated_downstream_inputs": true,
  "framework_failure_on_failed_stage_action": "retry_current_stage_without_rewinding_design",
  "framework_hash_evidence_or_orchestration_failures_never_backtrack": true,
  "framework_never_terminates_a_valid_llm_repair_or_replan_loop": true,
  "honor_backtrack_requests_before_downstream_progress": true,
  "llm_is_required": true,
  "local_qor_optimization_is_an_evidence_supported_design_backtrack": true,
  "prefer_retry_same_stage_for_retry_requests": true,
  "stage_attempt_counters_are_observability_only": true
}
</flow_policy>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "configured_model": "gpt-6.1-sol",
  "endpoint_configured": true,
  "enforce": true,
  "mode": "llm",
  "model": "deepseek-v4-pro",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
  "requested_model_override": "deepseek-v4-pro",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 0,
  "active_contamination_barriers": [],
  "active_contamination_barriers_truncated": false,
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 0,
  "open_retry_requests": [],
  "open_retry_requests_truncated": false,
  "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
  "schema_version": "spatialaccagent.sacg_memory_truth.v0",
  "truth_source": "source_sacg_state.memory"
}
</sacg_memory_truth>

<hierarchical_learning_context>
{
  "debug_layer": null,
  "decision_policy": {
    "current_scope_tools_and_exact_board_wrapper_remain_required": true,
    "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": true,
    "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": true,
    "lower_layer_reopen_requires_current_trace_named_contradiction": true,
    "resolved_artifact_identity_lessons_are_not_rtl_failures": true,
    "use_only_live_validated_lower_layer_evidence": true
  },
  "kernel_timing_knowledge": [],
  "resolved_evidence_lessons": [],
  "schema_version": "spatialaccagent.hierarchical_learning_context.v1",
  "status": "no_validated_lower_layer_evidence",
  "status_bar_contract": {
    "covers_only_live_validated_lower_layer_certificates": true,
    "does_not_replace_current_scope_tool_results": true,
    "maintainer": "framework_deterministic_hash_bound_projection",
    "not_an_llm_generated_history_summary": true,
    "raw_evidence_remains_retrievable_by_path_and_sha256": true
  },
  "validated_lower_layer_certificates": [],
  "verification_scope": null
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
    "backend_recovery_approval_ingest",
    "backend_recovery_approval_ingest_check"
  ],
  "policy": "Executable actions should use these tool/checker names when applicable. A registered acceptance checker may also be requested as a validation operation in tool_roles. If a required capability is missing, name it as planned_tool.<short_name> and make the rationale say that multi-agent system capability implementation is required.",
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
    "case_compute_slot_adapter_generate",
    "app_shell_target_discovery_contract",
    "app_shell_target_hint_synthesis",
    "app_shell_target_discovery_after_hint",
    "backend_bounded_recovery_action",
    "backend_bounded_recovery",
    "backend_recovery_approval_ingest",
    "implementation_package_static",
    "timing_resource_check",
    "deployment_board_check",
    "board_runtime",
    "output_validity_check",
    "case_stage7_metrics",
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
    "sacg_memory_check",
    "stage_retry_request",
    "stage_backtrack_request",
    "stage_artifact_trust_barrier",
    "app_shell_runtime_bitstream"
  ],
  "verification_execution_policy": {
    "acceptance": "Real current-source VCS compilation, elaboration and linking; simulator execution and numerical comparison are not acceptance prerequisites.",
    "executor": "accagent/framework/stage_verification.py: compile_only_stage_gates and compile_only_required_gates_by_level select the existing layer tools in bottom-up order",
    "existing_tool_modes": {
      "case_leaf_functional": "scripts/verification/case_leaf_operator_verify.py: current-source VCS compile-only evidence for operator leaves",
      "case_single_layer_functional": "scripts/verification/case_single_layer_stream_sim.py: current-source VCS compile-only evidence for the connected kernel",
      "case_vcs_functional_sim": "scripts/verification/case_board_vcs_functional.py: compile-only VCS evidence for the exact discovered board wrapper; simulation is not invoked"
    },
    "planning_boundary": "Historical functional/golden DAG nodes describe optional diagnostic capabilities. Missing runtime/golden results and layer certificates are downstream execution obligations during verification_artifacts planning, not missing compile-only capabilities. Use existing tool roles; do not invent another compile-only runner merely because a role retains a functional_sim name.",
    "validation_policy": "vcs_compile_only"
  }
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
      "artifact.stage5.verification_artifact_contract",
      "verification/model_reference/reference_manifest.json",
      "verification/semantic_testbench/semantic_testbench_manifest.json",
      "generated/memory/dut_weight_binding_manifest.json",
      "verification/board_simulation/board_simulation_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to the Stage-6 repair loop with the violated SACG constraints; do not proceed to Vivado.",
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
      "artifact.stage5.verification_plan"
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
      "artifact.stage7.app_shell_integration_contract",
      "artifact.stage7.app_shell_target_selection_decision",
      "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json"
    ],
    "id": "example.ambiguous_backend_target_recovery",
    "on_failure": "keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval",
    "produces": [
      "artifact.stage7.backend_bounded_recovery_actions"
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
          "targeted_replay_plan": {
            "additionalProperties": true,
            "type": "object"
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
