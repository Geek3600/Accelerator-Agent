<agent>
board_axi_ddr_verification_planner
</agent>

<task>
Refine the layer-3 verification subgate DAG: board interface discovery, multilayer pipeline, AXI/DDR interface, functional_sim, multilayer functional, pipeline deadlock, AXI protocol, DDR image roundtrip, and board semantic evidence. Keep Vivado bitstream and board runtime downstream after verification closure.
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
</rules>

<team_context>
{
  "collaboration_contract": {
    "coordination_policy": [
      "parallel specialists may disagree, but disagreement must be surfaced as bounded risks or handoff actions",
      "auditor/evidence-gate roles consume specialist outputs and must not silently rewrite them",
      "downstream stages consume the aggregate only after all required specialist roles completed without fallback"
    ],
    "rule": "Each sub-agent owns its explicit role_assignment and hands off only checker-grounded observations, risks, approval needs, and executable actions.",
    "schema_version": "spatialaccagent.team_collaboration_contract.v0",
    "team_model": "chip_design_team"
  },
  "objective": "Plan and refine the real-tool verification gate DAG for the three repair-loop layers: operator leaf modules, a connected single transformer-layer kernel, and the board AXI/DDR wrapped system. Multi-layer pipeline, AXI/DDR, DDR image, and functional-simulation ...<len=373>",
  "paper_alignment": {
    "method": "SACG-guided, template-constrained, checker-verified design closure",
    "problem": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design"
  },
  "stage": "verification_artifacts",
  "team_rules": [
    "Act as an AI chip design team for FPGA spatial accelerator automatic design, not as isolated static scripts.",
    "Stay inside the SpatialAccAgent paper story: cross-layer consistency for LLM spatial accelerators.",
    "Treat SACG as the design team's shared memory and evidence ledger; do not rely on natural-language memory as correctness evidence.",
    "Treat sacg_memory_truth as the authoritative current blocker set; closed, superseded, or historical memory records are recovery evidence onl...<len=142>",
    "Use trusted templates and bounded glue code; do not propose free-form RTL rewrites outside approved repair boundaries.",
    "Map every observation to model, shape, numeric precision, data order, transfer unit, memory, runtime, implementation, or deployment constrai...<len=144>",
    "Do not bypass checkers, modify golden outputs, loosen tolerance, or claim hardware pass without tool evidence.",
    "All verification layers pass when the current hardware sources compile, elaborate, and link successfully in real VCS; repair compiler errors...<len=191>",
    "Do not require simulation execution, runtime weight loading, golden comparisons, signal traces, output dumps, or numerical correctness. Hist...<len=207>",
    "Require the exact user sample-project wrapper and source identity at board level, and keep model/board/example names out of framework-core d...<len=149>",
    "The accelerator scope is Transformer blocks only; exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT we...<len=169>",
    "For board/app-shell integration, use LLM reasoning to synthesize profile/contract policy from user-supplied materials and real tool evidence...<len=199>",
    "Use hash-validated hierarchical learning context to preserve certified lower-layer timing invariants; only a current named trace contradicti...<len=168>",
    "At board scope, keep independent AXI/prefetch progress separate from output/lifecycle-frontier progress, and treat a frontier stall as local...<len=196>",
    "Do not reopen a certified lower layer from a board output symptom alone; require current hash-bound direct core start/ingress/egress evidenc...<len=216>"
  ]
}
</team_context>

<subtask>
{
  "acceptance_checkers": [
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "tool_protocol_check",
    "human_boundary_check",
    "required_real_tool_evidence_check",
    "functional_sim",
    "data_order_trace_check",
    "transfer_count_check"
  ],
  "action_type": "verification_planning",
  "agent": "board_axi_ddr_verification_planner",
  "artifact_focus": [
    "gate:case_board_interface_discovery",
    "gate:case_multilayer_pipeline",
    "gate:case_axi_ddr_interface",
    "gate:functional_sim",
    "gate:case_multilayer_functional",
    "gate:case_pipeline_deadlock_check",
    "gate:case_axi_protocol_check",
    "gate:case_ddr_image_roundtrip",
    "gate:case_board_semantic_evidence",
    "downstream:case_vivado_synthesis",
    "downstream:case_vivado_implementation",
    "downstream:case_runtime_bitstream",
    "downstream:board_runtime"
  ],
  "constraints": [
    "constraint.verification.hierarchy",
    "constraint.pipeline.structure",
    "constraint.stream.order",
    "constraint.beat.pipeline",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.tool.protocols",
    "constraint.human.boundary"
  ],
  "expected_artifacts": [
    "artifact.stage6.board_axi_ddr_verification_dag",
    "artifact.stage6.board_axi_ddr_gate_contract_map",
    "artifact.stage6.downstream_backend_gate_declarations"
  ],
  "handoff_rule": {
    "completion_criteria": [],
    "evidence_rule": "Do not claim pass unless evidence is bound to SACG constraints or explicitly recorded as not_run.",
    "produces": [
      "sacg_focus",
      "observations",
      "risks",
      "proposed_actions",
      "approval_required_for"
    ]
  },
  "handoff_to": [
    "verification_artifacts.verification_dag_auditor"
  ],
  "id": "verification_artifacts.board_axi_ddr_verification_dag_planner",
  "objective": "Refine the layer-3 verification subgate DAG: board interface discovery, multilayer pipeline, AXI/DDR interface, functional_sim, multilayer functional, pipeline deadlock, AXI protocol, DDR image roundtrip, and board seman...<len=312>",
  "role": "Board AXI/DDR wrapped-system verification gate planner",
  "role_assignment": {
    "collaboration_interfaces": {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "tool_protocol_check",
        "human_boundary_check",
        "required_real_tool_evidence_check",
        "functional_sim",
        "data_order_trace_check",
        "transfer_count_check",
        "addr_map_check",
        "deadlock_watchdog",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_board_semantic_evidence"
      ],
      "consumes": [
        "artifact.stage6.single_layer_verification_dag",
        "artifact.stage5.memory_layout",
        "artifact.stage5.runtime_config",
        "artifact.input.target_board_profile"
      ],
      "handoff_to": [
        "verification_artifacts.verification_dag_auditor"
      ],
      "produces": [
        "artifact.stage6.board_axi_ddr_verification_dag",
        "artifact.stage6.board_axi_ddr_gate_contract_map",
        "artifact.stage6.downstream_backend_gate_declarations"
      ]
    },
    "decision_authority": [
      "Promote the board DAG only when functional_sim precedes derived board semantic subgates",
      "Block any current-stage pass that claims Vivado or board runtime evidence before verification closure"
    ],
    "mission": "Plan the layer-3 board AXI/DDR wrapped-system verification DAG and keep Vivado/bitstream/board runtime gates explicitly downstream after verification closure.",
    "out_of_scope": [
      "Do not execute Vivado synthesis/implementation or board runtime",
      "Do not claim bitstream or board runtime evidence in this stage",
      "Do not alter the runtime/memory layout without a later repair boundary"
    ],
    "primary_responsibilities": [
      "Plan case_board_interface_discovery, case_multilayer_pipeline, and case_axi_ddr_interface before functional_sim",
      "Define subgates after functional_sim: case_multilayer_functional, case_pipeline_deadlock_check, case_axi_protocol_check, case_ddr_image_roundtrip, and case_board_semantic_evidence",
      "Declare data-order, transfer-count, address-map, and deadlock risks as checker gates",
      "Mark Vivado synthesis/implementation/runtime bitstream and board_runtime as downstream gates, not current verifier responsibilities"
    ]
  },
  "role_profile": {
    "capabilities": [
      "audit data order",
      "check transfer-count/liveness risks",
      "bind DDR/runtime layout",
      "classify evidence",
      "enforce repair boundaries"
    ],
    "constraint_focus": [
      "constraint.stream.order",
      "constraint.beat.pipeline",
      "constraint.memory.board",
      "constraint.runtime.board",
      "constraint.verification.plan"
    ],
    "family": "data_memory_runtime"
  },
  "title": "Plan board AXI/DDR wrapped-system verification gates"
}
</subtask>

<state_summary>
{
  "artifacts": [
    {
      "id": "artifact.input.material_index",
      "type": "input.material_index"
    },
    {
      "id": "artifact.input.sample_project_index",
      "type": "input.sample_project_index"
    },
    {
      "id": "artifact.input.field_evidence",
      "type": "input.field_evidence"
    },
    {
      "id": "artifact.input.task_card",
      "type": "input.task_card"
    },
    {
      "id": "artifact.input.model_config",
      "type": "input.model_config"
    },
    {
      "id": "artifact.input.numeric_policy",
      "type": "input.numeric_policy"
    },
    {
      "id": "artifact.input.template_library",
      "type": "input.template_library"
    },
    {
      "id": "artifact.input.template_metadata",
      "type": "input.template_metadata"
    },
    {
      "id": "artifact.input.design_space",
      "type": "input.design_space"
    },
    {
      "id": "artifact.input.target_board_profile",
      "type": "input.target_board_profile"
    },
    {
      "id": "artifact.input.tool_profile",
      "type": "input.tool_profile"
    },
    {
      "id": "artifact.input.tool_availability",
      "type": "input.tool_availability"
    },
    {
      "id": "artifact.input.tool_protocols",
      "type": "input.tool_protocols"
    },
    {
      "id": "artifact.input.case_adapter",
      "type": "input.case_adapter"
    },
    {
      "id": "artifact.input.human_agent_boundary",
      "type": "input.human_agent_boundary"
    },
    {
      "id": "artifact.stage2.template_selection",
      "type": "stage.template_selection"
    },
    {
      "id": "artifact.stage3.pipeline_plan",
      "type": "stage.pipeline_plan"
    },
    {
      "id": "artifact.stage3.pipeline_static_checks",
      "type": "stage.pipeline_static_checks"
    },
    {
      "id": "artifact.stage4.dse_search_space",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.dse_candidate_records",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.dse_constraint_report",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.dse_pareto_frontier",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.dse_measurements",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.selected_architecture",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.dse_selection_rationale",
      "type": "stage.dse_selection"
    },
    {
      "id": "artifact.stage4.parameter_binding",
      "type": "stage.parameter_binding"
    },
    {
      "id": "artifact.stage4.parameter_static_checks",
      "type": "stage.parameter_static_checks"
    },
    {
      "id": "artifact.stage5.design_artifact_manifest",
      "type": "stage.design_artifact_manifest"
    },
    {
      "id": "artifact.stage5.generated_code_package",
      "type": "stage.generated_code_package"
    },
    {
      "id": "artifact.stage5.memory_layout",
      "type": "stage.memory_layout"
    },
    {
      "id": "artifact.stage5.runtime_config",
      "type": "stage.runtime_config"
    },
    {
      "id": "artifact.stage5.codegen_compile_gate",
      "type": "stage.codegen_compile_gate"
    },
    {
      "id": "artifact.stage5.codegen_contract_check",
      "type": "stage.codegen_contract_check"
    },
    {
      "id": "artifact.stage5.codegen_package_static_check",
      "type": "stage.codegen_package_static_check"
    }
  ],
  "constraints": [
    {
      "id": "constraint.source.materials",
      "type": "source_materials"
    },
    {
      "id": "constraint.source.evidence",
      "type": "source_evidence"
    },
    {
      "id": "constraint.task.goal",
      "type": "task"
    },
    {
      "id": "constraint.model.decoder",
      "type": "model"
    },
    {
      "id": "constraint.shape.model",
      "type": "shape"
    },
    {
      "id": "constraint.numeric.policy",
      "type": "numeric"
    },
    {
      "id": "constraint.template.library",
      "type": "template"
    },
    {
      "id": "constraint.arch.design_space",
      "type": "architecture"
    },
    {
      "id": "constraint.deployment.board",
      "type": "deployment"
    },
    {
      "id": "constraint.memory.board",
      "type": "memory"
    },
    {
      "id": "constraint.runtime.board",
      "type": "runtime"
    },
    {
      "id": "constraint.tool.profile",
      "type": "tool_profile"
    },
    {
      "id": "constraint.tool.protocols",
      "type": "tool"
    },
    {
      "id": "constraint.case.adapter",
      "type": "verification_case_adapter"
    },
    {
      "id": "constraint.human.boundary",
      "type": "human_boundary"
    },
    {
      "id": "constraint.cross_layer.input_consistency",
      "type": "cross_layer_consistency"
    },
    {
      "id": "constraint.pipeline.structure",
      "type": "pipeline"
    },
    {
      "id": "constraint.stream.order",
      "type": "data_order"
    },
    {
      "id": "constraint.beat.pipeline",
      "type": "transfer_alignment"
    },
    {
      "id": "constraint.buffering.pipeline",
      "type": "buffering"
    },
    {
      "id": "constraint.flow_control.pipeline",
      "type": "flow_control"
    },
    {
      "id": "constraint.memory_schedule.pipeline",
      "type": "memory_schedule"
    },
    {
      "id": "constraint.liveness.pipeline",
      "type": "liveness"
    },
    {
      "id": "constraint.dse.selection",
      "type": "architecture"
    },
    {
      "id": "constraint.parameter.binding",
      "type": "parameter"
    },
    {
      "id": "constraint.parameter.structure",
      "type": "parameter"
    },
    {
      "id": "constraint.axi.layout",
      "type": "memory"
    },
    {
      "id": "constraint.codegen.package",
      "type": "codegen"
    },
    {
      "id": "constraint.codegen.compile_gate",
      "type": "tool_evidence"
    },
    {
      "id": "constraint.codegen.contract_check",
      "type": "checker_evidence"
    }
  ],
  "design_id": "gpt2_deepseek_v4pro_20261020",
  "edges": 18,
  "failed_invariants": [],
  "hierarchical_learning_context": {
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
  },
  "nodes": 30,
  "sacg_memory": {
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
      },
      {
        "artifacts": [
          "artifact.stage5.design_artifact_manifest",
          "artifact.stage5.generated_code_package",
          "artifact.stage5.memory_layout",
          "artifact.stage5.runtime_config"
        ],
        "errors": [],
        "id": "stage_outcome.0002",
        "next_actions": [],
        "retryable": false,
        "stage": "stage5.code_generation",
        "status": "ready",
        "summary": "completed 6 compile/elaboration command(s)",
        "timestamp": "2026-10-20T13:04:51+00:00",
        "transition_id": "transition.0004"
      }
    ],
    "schema_version": "spatialaccagent.sacg_memory.v0"
  },
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
  }
}
</state_summary>

<candidate_stage_artifact>
{
  "attention_semantics": {
    "omitted_in_role_slice": true,
    "present": true
  },
  "checker_plan": [
    {
      "checker": "stream_plan_check",
      "constraints": [
        "constraint.stream.order",
        "constraint.beat.pipeline"
      ]
    },
    {
      "checker": "tool_protocol_check",
      "constraints": [
        "constraint.tool.protocols"
      ]
    },
    {
      "checker": "human_boundary_check",
      "constraints": [
        "constraint.human.boundary"
      ]
    },
    {
      "checker": "memory_runtime_plan_check",
      "constraints": [
        "constraint.memory.board",
        "constraint.runtime.board"
      ]
    },
    {
      "checker": "hierarchical_verification_plan_check",
      "constraints": [
        "constraint.verification.hierarchy",
        "constraint.pipeline.structure"
      ]
    },
    {
      "checker": "verification_artifact_contract_check",
      "constraints": [
        "constraint.verification.artifacts"
      ]
    },
    {
      "checker": "required_real_tool_evidence_check",
      "constraints": [
        "constraint.verification.hierarchy",
        "constraint.tool.protocols",
        "constraint.deployment.board"
      ]
    },
    {
      "checker": "sacg_reference_check",
      "constraints": [
        "constraint.pipeline.structure"
      ]
    }
  ],
  "checker_results": [
    {
      "checker": "tool_protocol_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "all required verification tool protocols are configured; planned evidence paths are declared for downstream execution"
    },
    {
      "checker": "human_boundary_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "human-boundary policy forbids smoke-only acceptance and requires board runtime before final pass"
    },
    {
      "checker": "hierarchical_verification_plan_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "three-layer repair-loop hierarchy and anti-spin debug contract are declared"
    },
    {
      "checker": "verification_artifact_contract_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "all verification artifact contracts are satisfiable"
    },
    {
      "checker": "required_real_tool_evidence_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "real weights, functional simulation, bitstream, and board runtime are required downstream gates; no final pass is claime...<len=121>"
    },
    {
      "checker": "data_order_trace_check",
      "errors": [],
      "evidence_phase": "current_stage_static_trace_ledger",
      "execution_status": "static_only_downstream_sim_required",
      "status": "pass",
      "summary": "Stage 3 stream order and numeric stream policy are available for downstream trace checks"
    },
    {
      "checker": "deadlock_watchdog",
      "errors": [],
      "evidence_phase": "downstream_gate_declared",
      "execution_status": "not_run_required_downstream",
      "status": "pending_downstream",
      "summary": "deadlock watchdog is required through the downstream functional_sim gate and must emit tool evidence"
    }
  ],
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 19,
    "pending": [
      {
        "checker": "deadlock_watchdog",
        "execution_status": "not_run_required_downstream",
        "summary": "deadlock watchdog is required through the downstream functional_sim gate and must emit tool evidence"
      },
      {
        "checker": "implementation_package_static",
        "execution_status": "not_run_required_downstream",
        "summary": "implementation package evidence is required through the case_runtime_bitstream downstream gate"
      },
      {
        "checker": "board_runtime",
        "execution_status": "not_run_required_downstream",
        "summary": "board runtime evidence is required for final closure and is not claimed by Stage 5"
      }
    ],
    "pending_downstream": 3,
    "warnings": []
  },
  "constraints_referenced": [
    "constraint.beat.pipeline",
    "constraint.codegen.package",
    "constraint.deployment.board",
    "constraint.human.boundary",
    "constraint.memory.board",
    "constraint.model.decoder",
    "constraint.numeric.policy",
    "constraint.parameter.binding",
    "constraint.pipeline.structure",
    "constraint.runtime.board",
    "constraint.shape.model",
    "constraint.stream.order",
    "constraint.task.goal",
    "constraint.template.library",
    "constraint.tool.protocols",
    "constraint.verification.artifacts",
    "constraint.verification.hierarchy",
    "constraint.verification.plan"
  ],
  "constraints_touched": [
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.verification.artifacts"
  ],
  "hierarchical_verification": {
    "evidence_gates": [
      {
        "description": "A board-interface LLM agent interprets Vivado-exported sample-project facts and emits a hash-bound compute-slot, AXI, clock/reset/calibration, and recursive sim...<len=213>",
        "name": "case_board_interface_discovery",
        "required": true
      },
      {
        "description": "A model-adaptive multi-layer scheduler and board-slot integration wrapper is generated only after the exact sample-project contract is available.",
        "name": "case_multilayer_pipeline",
        "required": true
      },
      {
        "description": "The multi-layer kernel is wrapped with the target board AXI/DDR runtime interface before simulation.",
        "name": "case_axi_ddr_interface",
        "required": true
      },
      {
        "description": "A real board-wrapped simulator runs with the immutable random input, complete Transformer-block weights, target-model boundary golden, and runtime artifacts.",
        "name": "functional_sim",
        "required": true
      },
      {
        "description": "Multi-layer functionality is classified from the real board-wrapped simulator evidence.",
        "name": "case_multilayer_functional",
        "required": true
      },
      {
        "description": "Pipeline liveness and deadlock status are classified from real simulator counters and traces.",
        "name": "case_pipeline_deadlock_check",
        "required": true
      },
      {
        "description": "AXI protocol, order, and address behavior is classified from real simulator evidence.",
        "name": "case_axi_protocol_check",
        "required": true
      },
      {
        "description": "Real input, weight, and output DDR image transfers are classified from real simulator evidence.",
        "name": "case_ddr_image_roundtrip",
        "required": true
      }
    ],
    "merge_agents": [
      {
        "depends_on": [
          "merge.single_decoder_block"
        ],
        "id": "merge.multi_layer_pipeline",
        "required_evidence": [
          "case_board_interface_discovery",
          "case_multilayer_pipeline"
        ],
        "role": "multi-layer pipeline agent"
      },
      {
        "depends_on": [
          "merge.multi_layer_pipeline"
        ],
        "id": "merge.axi_ddr_runtime",
        "required_evidence": [
          "case_board_interface_discovery",
          "case_axi_ddr_interface",
          "functional_sim",
          "case_multilayer_functional",
          "case_pipeline_deadlock_check",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_board_semantic_evidence"
        ],
        "role": "AXI DDR runtime agent"
      }
    ],
    "policy": {
      "board_axi_ddr_functional_before_backend": true,
      "contract_guided_debug_closure_required_for_repair": true,
      "debug_layers": [
        "operator_leaf_modules",
        "single_transformer_layer_kernel",
        "board_axi_ddr_wrapped_system"
      ],
      "do_not_claim_final_pass_with_pending_or_failed_required_gate": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
      "do_not_use_default_generated_weights_as_real_weight_evidence": true,
      "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "merge_order": "operator_leaf_modules_then_single_transformer_layer_kernel_then_board_axi_ddr_wrapped_system_then_backend",
      "operator_leaf_functional_before_single_layer": true,
      "single_layer_functional_before_board_axi_ddr_wrapper": true,
      "stage_agents_parallel": true,
      "strict_bottom_up_functional_closure_before_backend": true
    },
    "stage_agents": [
      {
        "id": "verify.stage_00_layer_norm_1",
        "kind": "norm",
        "module_checks": [
          "VectorNorm"
        ],
        "op": "layer_norm_1",
        "required_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
        ],
        "stage_id": "stage_00_layer_norm_1"
      },
      {
        "id": "verify.stage_01_self_attention",
        "kind": "attention",
        "module_checks": [
          "QKVProjection",
          "Attention",
          "Linear_1"
        ],
        "op": "self_attention",
        "required_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
        ],
        "stage_id": "stage_01_self_attention"
      },
      {
        "id": "verify.stage_02_residual_add_1",
        "kind": "residual",
        "module_checks": [
          "ResidualAdd",
          "PhysicalStreamFifo"
        ],
        "op": "residual_add_1",
        "required_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
        ],
        "stage_id": "stage_02_residual_add_1"
      }
    ],
    "strategy": "three_layer_repair_loop: operator_leaf_modules -> single_transformer_layer_kernel -> board_axi_ddr_wrapped_system"
  },
  "parameter_bindings": {
    "count": 8,
    "omitted_in_role_slice": true
  },
  "presence_summary": {
    "attention_semantics_present": true,
    "debug_boundary_contract_count": 11,
    "debug_trace_schema_present": true,
    "evidence_gate_count": 27,
    "evidence_path_requirement_count": 36,
    "merge_agent_count": 6,
    "parameter_binding_count": 8,
    "parameter_binding_stage_ids": [
      "stage_00_layer_norm_1",
      "stage_01_self_attention",
      "stage_02_residual_add_1",
      "stage_03_layer_norm_2",
      "stage_04_mlp_fc",
      "stage_05_activation",
      "stage_06_mlp_proj",
      "stage_07_residual_add_2"
    ],
    "required_tool_protocol_count": 33,
    "stage_agent_count": 8,
    "stage_agent_ids": [
      "stage_00_layer_norm_1",
      "stage_01_self_attention",
      "stage_02_residual_add_1",
      "stage_03_layer_norm_2",
      "stage_04_mlp_fc",
      "stage_05_activation",
      "stage_06_mlp_proj",
      "stage_07_residual_add_2"
    ],
    "verification_gate_dag_node_count": 36
  },
  "role_slice_policy": {
    "do_not_infer_missing_from_omitted_details": true,
    "sliced_for_subtask": "verification_artifacts.board_axi_ddr_verification_dag_planner",
    "use_presence_summary_before_reporting_current_stage_missing_field_risks": true
  },
  "schema_version": "spatialaccagent.verification_artifacts_review.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {
    "current_certificate_validation": {
      "evidence_contract_version": "spatialaccagent.real_weight_semantic_evidence.v2",
      "policy": "Artifact presence is not certificate validity. Reuse is allowed only when the current validator returns current_contract_valid=true.",
      "schema_version": "spatialaccagent.current_certificate_validation_summary.v0",
      "scopes": [
        {
          "artifact_id": "artifact.stage6.operator_leaf_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "operator_leaf_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage6.single_layer_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "single_layer_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage6.board_axi_ddr_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "board_axi_ddr_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        }
      ]
    },
    "current_stage_acceptance": [
      "verification_plan must declare the three debug/repair layers: operator leaf modules, single transformer-layer kernel, and board AXI/DDR wrapped system",
      "verification_artifact_contract must pass before the Stage 5 transition can be promoted",
      "required tool protocols and generated handoff artifacts must be configured and present",
      "upstream Stage 3, Stage 4, and Stage 5 static gates must be visible as evidence",
      "lower-layer pass evidence is reusable but can be challenged by a bound current-layer CCTG/boundary trace"
    ],
    "later_stage_obligations": [
      "Stage7 executes real tools for the three-layer verification closures; Vivado synthesis/implementation, timing, bitstream, and board runtime are downstream after verification closure",
      "smoke or default generated weights cannot be used as functional correctness acceptance"
    ],
    "risk_classification_rule": "If verification_artifact_contract_check and upstream static gates pass, do not report later VCS/Vivado/board execution obligations as current-stage risks; keep them as required gates or proposed_actions."
  },
  "status": "ready",
  "upstream_evidence": {
    "stage3_pipeline_plan": {
      "attention_semantics": {
        "attention_kind": "mha",
        "causal": true,
        "gqa_group_size": 1,
        "head_dim": 64,
        "kv_storage_policy": "bounded by target_max_seq_len inside the generated block; external KV-cache materialization requires a later memory-layout artifact",
        "num_kv_heads": 12,
        "num_q_heads": 12,
        "position_encoding": {
          "type": "learned_absolute"
        },
        "position_encoding_scope": {
          "dut_operation": "none",
          "dut_weight_binding": "forbidden",
          "placement": "pre_dut_input_boundary",
          "reference_requirement": "compose learned position contribution before the Transformer-block DUT input boundary"
        },
        "seq_len_bound": 16,
        "stage_boundary": "logical self_attention stage covers QKV projection, causal attention, and output projection; learned absolute positional embeddings are pre-DUT input/reference composition and are excluded from DUT weights and operations"
      },
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 11,
        "warnings": []
      },
      "data_edge_count": 11,
      "stage": "pipeline_planning",
      "stage_count": 8,
      "status": "ready",
      "stream_edge_count": 11
    },
    "stage4_parameter_binding": {
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 6,
        "warnings": []
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
      "stage": "parameter_binding",
      "status": "ready"
    },
    "stage5_code_generation": {
      "compile_gate": {
        "status": "pass",
        "steps": [
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "Compile/compile"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.GeneratedContractCheck"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
            ],
            "returncode": 0,
            "status": "pass"
          },
          {
            "command": [
              "sbt",
              "--no-server",
              "--batch",
              "--supershell=false",
              "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
            ],
            "returncode": 0,
            "status": "pass"
          }
        ],
        "summary": "completed 6 compile/elaboration command(s)"
      },
      "contract_check": {
        "errors": [],
        "status": "pass",
        "summary": "all code generation contracts passed"
      },
      "generated_files_count": 457,
      "generated_package_root": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel",
      "package_static_check": {
        "errors": [],
        "status": "pass",
        "summary": "generated package manifest is structurally complete"
      },
      "stage": "code_generation",
      "status": "ready",
      "target_model_artifact_status": {
        "current_artifacts_match_target": true,
        "missing_for_target": [],
        "model_type": "gpt2",
        "planned_for_target": [
          "generated.model_ir",
          "generated.arch_plan",
          "generated.chisel_modules",
          "generated.fpga_ip_simulation_closure",
          "generated.top_wrapper",
          "generated.fpga_axi_ddr_top_wrapper",
          "generated.performance_counter",
          "generated.memory_layout",
          "generated.runtime_config",
          "generated.scala_contract_check",
          "generated.codegen_compile_gate",
          "generated.codegen_contract_check"
        ]
      }
    }
  },
  "verification_artifact_contract": {
    "debug_closure_contract": {
      "boundary_count": 11,
      "causal_path_count": 1,
      "contract_type": "boundary_contract_failure_slice_targeted_replay",
      "instrumentation_modes": [
        "failing_transaction_first",
        "target_boundary_replay",
        "full_boundary_trace_when_requested"
      ],
      "monitor_points": [
        "module_boundary_valid_ready",
        "transaction_and_tile_identity",
        "logical_index_and_lane_mapping",
        "declared_latency_window",
        "numeric_policy_and_tolerance",
        "runtime_memory_address_range"
      ],
      "policy": {
        "do_not_patch_downstream_symptom_without_upstream_localization": true,
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "not_a_general_rtl_debugger": true,
        "production_goal_not_toy_trace": true,
        "repair_agent_receives_compact_causal_slice": true,
        "tool_trace_schema_must_be_case_adapter_independent": true,
        "uses_agent_generated_dataflow_knowledge": true
      },
      "repair_handoff_required_fields": [
        "root_candidate_module",
        "violated_contract",
        "failure_signature",
        "causal_path",
        "targeted_replay_plan",
        "minimal_repair_context"
      ],
      "schema_version": "spatialaccagent.debug_boundary_contracts.v0",
      "targeted_replay_outputs": [
        "root_candidate_module",
        "violated_contract",
        "failure_signature",
        "minimal_repair_context"
      ],
      "targeted_replay_strategy": "boundary_bisection_then_earliest_violation",
      "trace_paths": {
        "localization": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/verification/debug_closure/failure_localization.json",
        "manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/verification/debug_closure/trace_manifest.json",
        "trace": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/verification/debug_closure/boundary_trace.json"
      },
      "trace_required_fields": [
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
    "errors": [],
    "evidence_path_requirements": [],
    "functional_sim_candidates": [
      {
        "acceptance_role": "required_real_functional_sim_gate_not_smoke_acceptance",
        "candidate_label_is_not_acceptance": true,
        "kind": "vcs_real_functional_sim",
        "name": "case_vcs_functional_sim",
        "scope": "remote"
      }
    ],
    "policy": {
      "board_runtime_required_for_final_pass": true,
      "complete_transformer_block_weight_consumption_required": true,
      "contract_guided_debug_closure_required": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
      "downstream_failure_requires_failure_slice": true,
      "explicit_numeric_comparison_policy_required": true,
      "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
      "later_stage_missing_gate_or_tool_requires_stage5_backtrack": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "random_or_rtl_derived_expected_output_forbidden": true,
      "real_axi_ddr_runtime_required": true,
      "real_functional_sim_required": true,
      "real_target_model_reference_required": true,
      "real_weight_artifacts_required": true,
      "same_stage_retry_can_supersede_prior_stage5_barriers_after_promotion": true,
      "smoke_is_not_acceptance": true,
      "transformer_blocks_are_the_only_accelerator_scope": true
    },
    "required_evidence_gates": [],
    "required_tool_protocols": [
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_multilayer_pipeline",
        "name": "case_multilayer_pipeline",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_multilayer_functional",
        "name": "case_multilayer_functional",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_pipeline_deadlock_check",
        "name": "case_pipeline_deadlock_check",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_board_interface_discovery",
        "name": "case_board_interface_discovery",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_axi_ddr_interface",
        "name": "case_axi_ddr_interface",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_axi_protocol_check",
        "name": "case_axi_protocol_check",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_ddr_image_roundtrip",
        "name": "case_ddr_image_roundtrip",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "semantic_evidence_assemble",
        "name": "case_board_semantic_evidence",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      }
    ],
    "schema_version": "spatialaccagent.verification_artifact_contract.v0",
    "status": "pass",
    "summary": "all verification artifact contracts are satisfiable",
    "verification_gate_dag": {
      "nodes": [
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "case_real_weight_artifacts",
          "role": "catalog the complete target checkpoint and bind every tensor to immutable source hashes"
        },
        {
          "depends_on": [
            "case_real_weight_artifacts"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_target_model_reference",
          "role": "run the real target model on a reproducible random input and capture independent operator/single-layer/all-Transformer-block boundary golden...<len=148>"
        },
        {
          "depends_on": [
            "case_target_model_reference"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_semantic_testbench",
          "role": "generate numeric-policy-bound semantic vectors/testbenches and validate complete DUT real-weight consumption"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "boundary_contract_check",
          "role": "materialize boundary contracts and trace schema used by contract-guided debug closure"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_00_layer_norm_1",
          "role": "verify spatial operator module stage_00_layer_norm_1 before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_01_self_attention",
          "role": "verify spatial operator module stage_01_self_attention before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_02_residual_add_1",
          "role": "verify spatial operator module stage_02_residual_add_1 before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_03_layer_norm_2",
          "role": "verify spatial operator module stage_03_layer_norm_2 before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_04_mlp_fc",
          "role": "verify spatial operator module stage_04_mlp_fc before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_05_activation",
          "role": "verify spatial operator module stage_05_activation before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_06_mlp_proj",
          "role": "verify spatial operator module stage_06_mlp_proj before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_07_residual_add_2",
          "role": "verify spatial operator module stage_07_residual_add_2 before any layer/block merge"
        },
        {
          "depends_on": [
            "leaf_stage.stage_00_layer_norm_1",
            "leaf_stage.stage_01_self_attention",
            "leaf_stage.stage_02_residual_add_1",
            "leaf_stage.stage_03_layer_norm_2",
            "leaf_stage.stage_04_mlp_fc",
            "leaf_stage.stage_05_activation",
            "leaf_stage.stage_06_mlp_proj",
            "leaf_stage.stage_07_residual_add_2"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_stage_leaf_static",
          "role": "aggregate all per-operator leaf module checks; every spatial stage must pass before layer merge"
        },
        {
          "depends_on": [
            "case_stage_leaf_static",
            "boundary_contract_check",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_leaf_functional",
          "role": "prove every spatial operator leaf module with independent functional simulation before layer merge"
        },
        {
          "depends_on": [
            "case_leaf_functional",
            "boundary_contract_check",
            "case_target_model_reference",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_leaf_golden_compare",
          "role": "compare every spatial operator leaf module against golden/reference boundary values"
        },
        {
          "depends_on": [
            "case_leaf_golden_compare",
            "case_leaf_functional",
            "case_stage_leaf_static",
            "boundary_contract_check",
            "case_target_model_reference",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_operator_leaf_semantic_evidence",
          "role": "assemble checker-bound evidence for all operator leaves, complete real-weight consumption, independent target-model golden values, and immut...<len=164>"
        },
        {
          "depends_on": [
            "case_operator_leaf_semantic_evidence",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_tb_scaffold",
          "role": "materialize and audit testbench/RTL scaffold that loads the declared input and weight artifacts"
        },
        {
          "depends_on": [
            "case_operator_leaf_semantic_evidence",
            "case_tb_scaffold",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "single_transformer_layer",
          "role": "connect verified spatial operator modules into one transformer-layer/block kernel and validate layer-level stream/data-order behavior"
        },
        {
          "depends_on": [
            "single_transformer_layer",
            "case_operator_leaf_semantic_evidence",
            "case_tb_scaffold",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_single_layer_functional",
          "role": "run one transformer-layer/block functional verification before any multi-layer pipeline claim"
        },
        {
          "depends_on": [
            "case_single_layer_functional"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_single_layer_golden_compare",
          "role": "compare the single transformer-layer/block against golden/reference outputs or numeric tolerance contract"
        },
        {
          "depends_on": [
            "case_single_layer_golden_compare",
            "case_single_layer_functional",
            "case_operator_leaf_semantic_evidence",
            "case_target_model_reference",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_single_layer_semantic_evidence",
          "role": "assemble checker-bound connected single-layer semantic, golden, real-weight-consumption, and immutable identity evidence"
        },
        {
          "depends_on": [
            "case_single_layer_semantic_evidence"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_board_interface_discovery",
          "role": "use an LLM board-interface agent to interpret Vivado-exported sample-project structure before generating board integration RTL"
        },
        {
          "depends_on": [
            "case_single_layer_semantic_evidence",
            "case_semantic_testbench",
            "case_board_interface_discovery"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_multilayer_pipeline",
          "role": "generate and prove the model-adaptive multi-layer scheduler against the discovered exact compute-slot contract"
        },
        {
          "depends_on": [
            "case_multilayer_pipeline",
            "case_board_interface_discovery"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_axi_ddr_interface",
          "role": "prove AXI/DDR runtime interface scaffold around the multi-layer kernel before simulation"
        },
        {
          "depends_on": [
            "case_semantic_testbench",
            "case_single_layer_semantic_evidence",
            "case_multilayer_pipeline",
            "case_board_interface_discovery",
            "case_axi_ddr_interface"
          ],
          "evidence_status": "required_pending_execution",
          "name": "functional_sim",
          "role": "run the real board-wrapped simulator with the exact sample wrapper, immutable input, and complete Transformer-block weight image before deri...<len=159>"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_multilayer_pipeline"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_multilayer_functional",
          "role": "classify real simulator evidence for multi-layer pipeline functionality"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_multilayer_functional"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_pipeline_deadlock_check",
          "role": "classify real simulator liveness/deadlock evidence for the multi-layer pipeline"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_axi_ddr_interface",
            "case_board_interface_discovery"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_axi_protocol_check",
          "role": "classify dynamic AXI protocol/order/address evidence from the real simulator"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_axi_protocol_check",
            "case_real_weight_artifacts"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_ddr_image_roundtrip",
          "role": "classify real input, weight, and output DDR transfer evidence from the real simulator"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_multilayer_functional",
            "case_pipeline_deadlock_check",
            "case_axi_protocol_check",
            "case_ddr_image_roundtrip",
            "case_board_interface_discovery",
            "case_real_weight_artifacts",
            "case_target_model_reference",
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_board_semantic_evidence",
          "role": "assemble the canonical board-run identity, exact wrapper, all third-layer classifier, complete real-weight-consumption, and target-model out...<len=152>"
        },
        {
          "depends_on": [
            "case_single_layer_semantic_evidence",
            "case_board_interface_discovery",
            "functional_sim"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_board_bringup_ready",
          "role": "record board bring-up readiness from the passed single-layer certificate, validated exact board identity, current workload binding, complete...<len=237>"
        },
        {
          "depends_on": [
            "case_board_bringup_ready"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_vivado_synthesis",
          "role": "run Vivado synthesis and collect utilization/timing evidence after real board bring-up readiness; strict output/writeback functionality rema...<len=179>"
        },
        {
          "depends_on": [
            "case_vivado_synthesis"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_vivado_implementation",
          "role": "run Vivado implementation/route/DRC/timing evidence"
        },
        {
          "depends_on": [
            "case_vivado_implementation",
            "case_board_bringup_ready"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_runtime_bitstream",
          "role": "run runtime/app-shell bitstream flow only after board bring-up readiness and Vivado implementation pass"
        },
        {
          "depends_on": [
            "case_runtime_bitstream"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_runtime_abi_check",
          "role": "cross-check runtime ABI, register map, DDR layout, and bitstream artifacts"
        },
        {
          "depends_on": [
            "case_runtime_bitstream",
            "case_runtime_abi_check",
            "case_board_bringup_ready",
            "case_real_weight_artifacts"
          ],
          "evidence_status": "required_pending_execution",
          "name": "board_runtime",
          "role": "program board/runtime and collect valid output evidence"
        }
      ],
      "policy": {
        "all_gate_tool_roles_must_pass": true,
        "backend_discovery_before_vivado_bitstream": true,
        "board_axi_ddr_functional_before_backend": true,
        "board_runtime_after_bitstream": true,
        "complete_transformer_block_weight_scope_required": true,
        "do_not_promote_final_design_with_pending_required_node": true,
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
        "dut_real_weight_consumption_proof_required": true,
        "each_spatial_operator_module_must_have_leaf_gate": true,
        "explicit_numeric_comparison_policy_required": true,
        "functional_sim_before_backend": true,
        "functional_sim_before_derived_third_layer_checkers": true,
        "hierarchical_order": [
          "real_weight_catalog",
          "target_model_reference",
          "semantic_testbench_generation",
          "operator_leaf_module",
          "debug_boundary_contract",
          "operator_leaf_functional",
          "operator_leaf_golden_compare",
          "operator_leaf_semantic_aggregate",
          "testbench_scaffold",
          "single_layer_kernel",
          "single_layer_functional",
          "single_layer_golden_compare",
          "single_layer_semantic_aggregate",
          "board_interface_discovery",
          "multilayer_pipeline",
          "board_wrapper_interface",
          "functional_simulation",
          "multilayer_functional",
          "multilayer_deadlock_liveness",
          "axi_protocol_check",
          "ddr_image_roundtrip",
          "board_semantic_aggregate",
          "board_bringup",
          "vivado_synthesis",
          "vivado_implementation",
          "vivado_bitstream",
          "runtime_abi",
          "board_runtime"
        ],
        "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
        "layer1_operator_leaf_closure": [
          "real_weight_catalog",
          "target_model_reference",
          "semantic_testbench_generation",
          "operator_leaf_module",
          "debug_boundary_contract",
          "operator_leaf_functional",
          "operator_leaf_golden_compare",
          "operator_leaf_semantic_aggregate"
        ],
        "layer2_single_layer_kernel_closure": [
          "testbench_scaffold",
          "single_layer_kernel",
          "single_layer_functional",
          "single_layer_golden_compare",
          "single_layer_semantic_aggregate"
        ],
        "layer3_board_axi_ddr_wrapper_closure": [
          "board_interface_discovery",
          "multilayer_pipeline",
          "board_wrapper_interface",
          "functional_simulation",
          "multilayer_functional",
          "multilayer_deadlock_liveness",
          "axi_protocol_check",
          "ddr_image_roundtrip",
          "board_semantic_aggregate",
          "board_bringup"
        ],
        "llm_board_interface_discovery_before_multilayer_generation": true,
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "multilayer_pipeline_before_axi_ddr": true,
        "operator_leaf_functional_before_single_layer_kernel": true,
        "real_input_and_weight_artifacts_required": true,
        "real_model_inference_golden_required": true,
        "rtl_derived_or_random_expected_output_forbidden": true,
        "semantic_evidence_aggregators_are_mandatory_gate_tools": true,
        "single_layer_functional_before_board_axi_ddr_wrapped_system": true,
        "single_layer_kernel_after_leaf_modules": true,
        "smoke_is_not_acceptance": true,
        "strict_board_output_functionality_remains_diagnostic_until_separately_closed": true,
        "testbench_scaffold_before_functional_sim": true,
        "third_layer_contains_multilayer_pipeline_and_board_axi_ddr_wrapper_subgates": true,
        "three_debug_layers": [
          "operator_leaf_modules",
          "single_transformer_layer_kernel",
          "board_axi_ddr_wrapped_system"
        ],
        "transformer_blocks_are_the_only_accelerator_scope": true,
        "vivado_implementation_requires_board_bringup_readiness": true,
        "vivado_report_checkers_are_mandatory_gate_tools": true
      },
      "schema_version": "spatialaccagent.verification_gate_dag.v0"
    }
  }
}
</candidate_stage_artifact>

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

<sacg_memory>
{}
</sacg_memory>

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
