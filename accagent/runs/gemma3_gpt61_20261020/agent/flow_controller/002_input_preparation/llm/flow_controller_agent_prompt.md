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
input_preparation
</current_stage>

<stage_passed>
false
</stage_passed>

<attempt_count>
2
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
  "design_team": {
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/input/team/team_aggregate.json",
    "approval_required_for": [
      "Any addition, replacement, or major modification of a template or its supported parameter contract.",
      "Any change to architecture/design-space constraints or material resource assumptions.",
      "Any change to numeric precision, quantization intent, or numeric policy.",
      "Any major memory, pipeline, or deployment-template change needed to resolve a documented conflict.",
      "Any proposed architecture, pipeline, memory-layout, trusted-template, or numeric-policy change requires the applicable human approval before execution.",
      "Any proposed board memory layout, address-map, DDR/AXI interface, or runtime ABI choice not established by supplied evidence.",
      "Any proposed change or selection of data ordering, transfer/beat contract, or stream pipeline semantics not established by supplied evidence.",
      "Any repair that would change checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, or exact board-wrapper source identity requires approval and must not be used to mask a DUT or integration defect.",
      "No approval is evidenced as necessary for the audit-only action; human_boundary_check must determine permissions for any subsequent repair."
    ],
    "completed_subtasks": 5,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/input/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "stream_plan_check",
          "addr_map_check",
          "sacg_static_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.field_evidence",
          "artifact.input.case_adapter",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "candidate_stage_artifact.prepared_inputs.errors"
        ],
        "id": "input_preparation.extract_and_check_board_memory_runtime_contract",
        "on_failure": "Do not promote board or runtime readiness. Preserve checker findings and unresolved fields with their source references; classify the prepared-input error from its actual detail, and request the canonical artifact detail or a bounded board-owner decision where evidence is ambiguous. Do not invent ordering, beat, memory-map, or runtime defaults.",
        "produces": [
          "input_preparation.board_memory_runtime_audit.json",
          "input_preparation.data_order_and_transfer_assumptions.json",
          "input_preparation.board_memory_runtime_checker_results.json"
        ],
        "rationale": "The supplied summaries establish that the relevant input artifacts exist but do not expose their substantive values. Produce a source-bound audit and assumption ledger, then use the registered checkers to validate it without guessing board facts or claiming readiness.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "memory_runtime_plan_check",
          "stream_plan_check",
          "addr_map_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "sacg_static_check"
        ],
        "action_type": "source_and_tool_evidence_audit",
        "consumes": [
          "artifact.input.material_index",
          "artifact.input.sample_project_index",
          "artifact.input.field_evidence_candidates",
          "artifact.input.field_evidence",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "constraint.tool.protocols",
          "constraint.deployment.board",
          "constraint.memory.board"
        ],
        "id": "input_preparation.audit_source_and_tool_evidence",
        "on_failure": "Record the specific missing payload, provenance link, applicability basis, or checker result as unresolved/not_run; do not claim tool, backend, or board pass and hand the unresolved evidence requirement to the readiness auditor.",
        "produces": [
          "input_preparation.source_and_tool_evidence_audit.json",
          "input_preparation.evidence_provenance_and_applicability.json"
        ],
        "rationale": "Audit the complete artifact payloads rather than their compact index summary, and record provenance, applicability, tool declarations, checker outcomes, and explicit not_run status where execution evidence is absent.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "real_tool_evidence_check",
          "sacg_validate"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "tool_protocol_check",
          "required_real_tool_evidence_check"
        ],
        "action_type": "prepared_input_error_triage",
        "consumes": [
          "prepared_inputs.errors",
          "artifact.input.material_index",
          "artifact.input.sample_project_index",
          "artifact.input.field_evidence",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols"
        ],
        "id": "input_preparation.surface_prepared_error_for_readiness_triage",
        "on_failure": "Preserve prepared_inputs.errors[0] verbatim, mark its classification unresolved when the payload or cited evidence is unavailable, and hand that unresolved entry to input_preparation.cross_layer_readiness_auditor; do not suppress or reinterpret it.",
        "produces": [
          "input_preparation/prepared_input_error_triage.json"
        ],
        "rationale": "The supplied summary confirms one prepared_inputs.errors entry but hides its contents. Retrieve and surface the exact entry and classify it only against its cited source evidence so the readiness auditor can determine whether it blocks promotion.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_validate",
          "tool_protocol_check"
        ]
      },
      {
        "acceptance_checkers": [
          "llm_semantic_extraction_check",
          "task_card_check",
          "model_config_check",
          "sacg_static_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.task_card",
          "artifact.input.model_config",
          "artifact.input.case_adapter",
          "constraint.task.goal",
          "constraint.model.decoder",
          "constraint.shape.model"
        ],
        "id": "input_preparation.extract_and_check_model_shape_facts",
        "on_failure": "Record failed or unavailable checks as not_run/failed with the affected source fields. Keep unsupported facts unknown, preserve conflicting source evidence without resolving it by guesswork, and hand off the bounded gaps to input_preparation.cross_layer_readiness_auditor; do not claim SACG-ready model or shape coverage.",
        "produces": [
          "input_preparation/model_intake_audit.json",
          "input_preparation/model_shape_assumptions_and_gaps.json"
        ],
        "rationale": "The summarized inputs establish artifact presence but do not expose field-level model facts or provenance. Inspect and extract only source-supported decoder, shape, attention, head-mapping, sequence, and operator-order facts, retaining unknowns and contradictions explicitly for SACG handoff.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "llm_semantic_extraction",
          "task_card_check",
          "model_config_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "constraint.numeric.policy",
          "constraint.template.library",
          "constraint.arch.design_space"
        ],
        "id": "input_preparation.run_numeric_template_static_audit",
        "on_failure": "Record each checker result and the specific unresolved binding or unsupported claim in the expected artifacts; keep SACG extraction and template-constrained architecture planning blocked on failing or not_run required checks. Do not repair RTL, invent template support, or alter numeric policy. Route any proposed numeric-policy, template, architecture, or resource-assumption change for approval.",
        "produces": [
          "input_preparation/numeric_template_audit.json",
          "input_preparation/template_binding_gaps.json"
        ],
        "rationale": "Establish whether the supplied numeric policy and template-constrained design-space contract are traceable and statically supported. The current summary contains artifact-presence evidence only, so checker results must be obtained before promotion.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "boundary_contract_check",
          "deployment_board_check",
          "tool_protocol_check",
          "human_boundary_check",
          "repair_boundary_check",
          "verification_plan_static_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "input_preparation/model_intake_audit.json",
          "input_preparation/numeric_template_audit.json",
          "input_preparation/board_memory_runtime_audit.json",
          "input_preparation/source_and_tool_evidence_audit.json",
          "artifact.input.task_card",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "artifact.input.human_agent_boundary",
          "artifact.input.field_evidence",
          "artifact.input.case_adapter",
          "prepared_inputs.errors"
        ],
        "id": "input_preparation.integrate_audits_and_gate_sacg_extraction",
        "on_failure": "Keep SACG extraction blocked. Record each failing or unavailable checker, affected constraint, source evidence, and bounded repair or clarification owner. Preserve the prepared-input error until its actual content is classified. Do not alter golden/reference artifacts, loosen numeric policy, infer approval, or claim readiness from omitted details.",
        "produces": [
          "input_preparation/cross_layer_input_readiness.json",
          "input_preparation/constraint_to_evidence_gap_map.json",
          "input_preparation/human_and_repair_boundary_audit.json",
          "input_preparation/prepared_input_error_classification.json",
          "input_preparation/checker_results.json"
        ],
        "rationale": "The visible summary does not contain the specialist findings, checker results, or the content of the single prepared-input error. Integrate the source audits and execute the registered static checks so readiness and each remaining gap are evidence-bound rather than inferred.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "team_aggregate",
          "sacg_static_check",
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "boundary_contract_check",
          "deployment_board_check",
          "tool_protocol_check",
          "human_boundary_check",
          "repair_boundary_check",
          "verification_plan_static_check"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 6,
      "max_duration_sec": 40.7502856439678,
      "max_prompt_bytes": 40122,
      "result_count": 5,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 160.91118159191683,
      "total_prompt_bytes": 196749
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 5,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/input/team/subtask_plan.json",
    "used_fallback_count": 0
  },
  "errors": [
    "case_adapter is not ready for this run: status=missing errors=['No verification case adapter was provided for this model family. Provide SPATIALACC_CASE_ADAPTER or a case_adapter.json in tool materials with real weight, TB/RTL, simulator, and diagnosis tools.']"
  ],
  "inputs": {
    "case_adapter": "input/case_adapter.json",
    "design_space": "input/design_space.json",
    "field_evidence": "input/field_evidence.json",
    "field_evidence_candidates": "input/field_evidence_candidates.json",
    "human_agent_boundary": "input/human_agent_boundary.json",
    "material_index": "input/material_index.json",
    "model_config": "input/model_config.json",
    "numeric_policy": "input/numeric_policy.json",
    "sample_project_index": "input/sample_project_index.json",
    "target_board_profile": "input/target_board_profile.json",
    "task_card": "input/task_card.json",
    "template_library": "input/template_library.json",
    "template_metadata": "input/template_metadata.json",
    "tool_availability": "input/tool_availability.json",
    "tool_profile": "input/tool_profile.json",
    "tool_protocols": "input/tool_protocols.json"
  },
  "mode": "independent_from_scratch_design",
  "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020",
  "schema_version": "spatialaccagent.prepared_inputs.v0",
  "source_roles": {
    "board_materials_dir": "current-run target FPGA board, DDR/AXI, runtime, and sample-project materials",
    "model_dir": "run-specific target checkpoint directory",
    "model_source": "run-specific model architecture source",
    "quantization_materials_dir": "current-run numeric and quantization design materials",
    "task_spec": "run-specific objective and acceptance boundary",
    "template_dir": "trusted local hardware template library",
    "tool_materials_dir": "current-run EDA tool location, usage, and limitation materials"
  },
  "source_specs": {
    "board_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board",
    "model_dir": "/home/remote/.cache/huggingface/hub/models--google--gemma-3-1b-it/snapshots/dcc83ea841ab6100d6b47a070329e1ba4cf78752",
    "model_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/gemma3_1b_it/model_config.json",
    "quantization_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization",
    "task_spec": "/home/remote/workspace/Qwen2-Accelerator/accagent/campaigns/20261020_gemma_gpt61/task_spec.md",
    "template_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel",
    "tool_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools"
  },
  "stage": "input_preparation",
  "status": "incomplete",
  "summary": {
    "llm_mode": "llm",
    "llm_provider": "OpenAI",
    "model_type": "gemma3_text",
    "operator_count": 11,
    "template_count": 13,
    "tool_protocols": 18
  },
  "warnings": [
    "sample_project_index failed to read one or more declared sample projects; later real-tool/remote probes must confirm these references"
  ]
}
</recent_stage_summary>

<command>
[
  "/usr/bin/python3",
  "-m",
  "accagent.framework.stage_input",
  "--run-dir",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020",
  "--task-spec",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/campaigns/20261020_gemma_gpt61/task_spec.md",
  "--model-source",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/gemma3_1b_it/model_config.json",
  "--model-dir",
  "/home/remote/.cache/huggingface/hub/models--google--gemma-3-1b-it/snapshots/dcc83ea841ab6100d6b47a070329e1ba4cf78752",
  "--board-materials-dir",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board",
  "--quantization-materials-dir",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization",
  "--tool-materials-dir",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools"
]
</command>

<command_returncode>
1
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/agent/logs/02_input_preparation.json
</command_log>

<sacg_memory>
{}
</sacg_memory>

<source_sacg_state>

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
  "model": "gpt-6.1-sol",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
  "requested_model_override": "",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

<sacg_memory_truth>
{}
</sacg_memory_truth>

<hierarchical_learning_context>
{}
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
