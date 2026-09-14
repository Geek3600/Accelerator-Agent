<agent>
verification_closure_auditor
</agent>

<task>
Integrate the four specialist audits into one checker-verifiable real-tool gate DAG. Resolve dependency omissions and contradictions, confirm reusable leaf and single-layer promotion evidence, enforce complete board AXI/DDR functional closure, and issue a bounded decision that either accepts the refined verification DAG, blocks specific nodes for repair, or identifies a missing tool capability. Keep Vivado synthesis, implementation, runtime bitstream, ABI checking, and board runtime strictly downstream of verification closure.
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
21. Before any functional pass, require a complete target-checkpoint tensor catalog, deterministic or real input provenance, target-model inference expected outputs for the same input/checkpoint, explicit numeric comparison tolerance, generated semantic testbench hashes, and proof that the DUT consumed every required bound weight.
22. A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.
23. During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.
24. At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.
25. Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.
26. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
27. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
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
    "For functional verification, random generation may create input stimulus only; expected output must come from real target-model inference on...<len=181>",
    "A weight manifest or memory image is not proof of DUT consumption; require complete tensor coverage, bound loader/harness hashes, and execut...<len=162>",
    "Keep checkpoint, stimulus, reference-output, numeric-policy, tolerance, and semantic-testbench hashes immutable during repair; repair the DU...<len=165>",
    "Require the exact user sample-project wrapper and source identity at board level, and keep model/board/example names out of framework-core d...<len=149>",
    "The accelerator scope is Transformer blocks only; exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT we...<len=169>",
    "For board/app-shell integration, use LLM reasoning to synthesize profile/contract policy from user-supplied materials and real tool evidence...<len=199>"
  ]
}
</team_context>

<subtask>
{
  "acceptance_checkers": [
    "verification_plan_static_check",
    "hierarchical_verification_plan_check",
    "verification_artifact_contract_check",
    "tool_protocol_check",
    "human_boundary_check",
    "sacg_reference_check",
    "required_real_tool_evidence_check",
    "case_operator_leaf_semantic_evidence"
  ],
  "action_type": "cross_layer_evidence_gate_audit",
  "agent": "verification_closure_auditor",
  "artifact_focus": [
    "all parallel-group-0 audit artifacts",
    "artifact.stage6.verification_plan",
    "artifact.stage6.verification_artifact_contract",
    "artifact.stage6.stage7_gate_selector_contract",
    "artifact.stage6.downstream_artifact_blocklist",
    "artifact.stage7.real_tool_results",
    "operator-leaf and single-layer promotion certificates"
  ],
  "constraints": [
    "constraint.cross_layer.input_consistency",
    "constraint.verification.plan",
    "constraint.verification.hierarchy",
    "constraint.verification.artifacts",
    "constraint.tool.protocols",
    "constraint.human.boundary",
    "constraint.pipeline.structure",
    "constraint.stream.order",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.deployment.board"
  ],
  "expected_artifacts": [
    "refined_three_layer_verification_gate_dag.json",
    "verification_gate_dependency_diff.json",
    "cross_layer_evidence_ledger.json",
    "verification_closure_and_backend_handoff_decision.json",
    "checker_failure_to_repair_route_manifest.json"
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
    "stage7.verification_executor",
    "stage8.repair",
    "backend_board"
  ],
  "id": "verification_artifacts.cross_layer_evidence_gate_auditor",
  "objective": "Integrate the four specialist audits into one checker-verifiable real-tool gate DAG. Resolve dependency omissions and contradictions, confirm reusable leaf and single-layer promotion evidence, enforce complete board AXI/...<len=532>",
  "role": "cross-layer verification evidence-gate lead",
  "role_assignment": {
    "collaboration_interfaces": {
      "accepted_by": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "required_real_tool_evidence_check"
      ],
      "consumes": [
        "all parallel-group-0 expected artifacts",
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage7.real_tool_results"
      ],
      "handoff_to": [
        "stage7.verification_executor",
        "stage8.repair",
        "backend_board"
      ],
      "produces": [
        "refined_three_layer_verification_gate_dag.json",
        "verification_closure_and_backend_handoff_decision.json",
        "checker_failure_to_repair_route_manifest.json"
      ]
    },
    "decision_authority": [
      "Own the final decomposition-stage DAG acceptance decision.",
      "Block unsupported pass or backend-ready claims.",
      "Escalate only genuine missing-capability cases as planned tool/checker implementation requirements."
    ],
    "mission": "Independently adjudicate the refined three-layer verification gate DAG and its backend boundary.",
    "out_of_scope": [
      "Bypassing pending real-tool gates.",
      "Treating Vivado or board runtime as part of current verification closure.",
      "Broad RTL or architecture modification."
    ],
    "primary_responsibilities": [
      "Reconcile parallel audits and resolve contradictory edges.",
      "Check that existing lower-layer certificates remain hash-valid.",
      "Require complete third-layer functional evidence before backend.",
      "Publish checker-grounded pass, blocked, or repair decisions."
    ]
  },
  "role_profile": {
    "collaboration_interfaces": {
      "acceptance_checker": "verification_artifact_contract_check",
      "consumes": [
        "all specialist audit artifacts",
        "verification plans and contracts",
        "real-tool evidence",
        "promotion certificates"
      ],
      "downstream_agents_tools": [
        "stage7.verification_executor",
        "stage8.repair",
        "backend_board",
        "case_vivado_synthesis"
      ],
      "produces": [
        "refined DAG",
        "dependency diff",
        "evidence ledger",
        "closure decision",
        "repair routing manifest"
      ]
    },
    "decision_authority": [
      "May accept the refined Stage 6/Stage 7 gate contract.",
      "May block individual or downstream gates on missing evidence.",
      "May authorize backend handoff only after all third-layer functional subgates close."
    ],
    "family": "verification_repair",
    "mission": "Serve as the independent evidence gate for cross-layer, checker-verified verification closure.",
    "out_of_scope": [
      "Executing synthesis or implementation.",
      "Generating a runtime bitstream.",
      "Claiming board deployment success before board_runtime and output validity evidence."
    ],
    "primary_responsibilities": [
      "Merge specialist findings into one authoritative DAG.",
      "Check edge completeness, acyclicity, maturity ordering, and evidence provenance.",
      "Enforce verification closure before backend execution.",
      "Issue precise repair or missing-capability handoffs."
    ]
  },
  "title": "Reconcile the three-layer DAG and issue the verification-to-backend gate decision"
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
    },
    {
      "id": "artifact.stage6.verification_plan",
      "type": "stage.verification_plan"
    },
    {
      "id": "artifact.stage6.verification_review_artifact",
      "type": "stage.verification_review_artifact"
    },
    {
      "id": "artifact.stage6.verification_artifact_contract",
      "type": "stage.verification_artifact_contract"
    },
    {
      "id": "artifact.stage6.llm_action_audit",
      "type": "stage.llm_action_audit"
    },
    {
      "id": "artifact.stage6.llm_io_quality",
      "type": "stage.llm_io_quality"
    },
    {
      "id": "artifact.stage6.refinement_manifest",
      "type": "stage.stage6_refinement_manifest"
    },
    {
      "id": "artifact.stage6.stage7_gate_selector_contract",
      "type": "stage.stage7_gate_selector_contract"
    },
    {
      "id": "artifact.stage6.downstream_artifact_blocklist",
      "type": "stage.downstream_artifact_blocklist"
    },
    {
      "id": "artifact.stage6.dependency_blocked_manifest_schema",
      "type": "stage.dependency_blocked_manifest_schema"
    },
    {
      "id": "artifact.stage6.functional_sim_real_tool_nodes",
      "type": "stage.functional_sim_real_tool_nodes"
    },
    {
      "id": "artifact.stage6.debug_trace_manifest_schema",
      "type": "stage.debug_trace_manifest_schema"
    },
    {
      "id": "artifact.stage6.failure_localization_schema",
      "type": "stage.failure_localization_schema"
    },
    {
      "id": "artifact.stage6.backend_app_shell_target_discovery_policy",
      "type": "stage.backend_app_shell_target_discovery_policy"
    },
    {
      "id": "artifact.stage7.verification_result",
      "type": "stage.verification_result"
    },
    {
      "id": "artifact.stage7.real_tool_results",
      "type": "stage.real_tool_results"
    },
    {
      "id": "artifact.stage7.debug_closure",
      "type": "stage.debug_closure"
    },
    {
      "id": "artifact.stage7.operator_leaf_promotion_certificate",
      "type": "stage.promotion_certificate"
    },
    {
      "id": "artifact.stage7.single_layer_promotion_certificate",
      "type": "stage.promotion_certificate"
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
      "id": "constraint.parameter.binding",
      "type": "parameter"
    },
    {
      "id": "constraint.resource.estimate",
      "type": "resource"
    },
    {
      "id": "constraint.bandwidth.estimate",
      "type": "bandwidth"
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
    },
    {
      "id": "constraint.verification.plan",
      "type": "verification"
    },
    {
      "id": "constraint.verification.hierarchy",
      "type": "verification"
    },
    {
      "id": "constraint.verification.artifacts",
      "type": "verification"
    }
  ],
  "design_id": "qwen2_spatialacc_agent_run",
  "edges": 21,
  "failed_invariants": [],
  "nodes": 32,
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
        "timestamp": "2026-07-09T09:23:00+00:00",
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
        "summary": "completed 4 compile/elaboration command(s)",
        "timestamp": "2026-07-09T11:11:05+00:00",
        "transition_id": "transition.0004"
      },
      {
        "artifacts": [
          "artifact.stage6.verification_plan",
          "artifact.stage6.verification_artifact_contract",
          "artifact.stage6.llm_action_audit",
          "artifact.stage6.llm_io_quality"
        ],
        "errors": [],
        "id": "stage_outcome.0003",
        "next_actions": [],
        "retryable": false,
        "stage": "stage6.verification_artifacts",
        "status": "ready",
        "summary": "all verification artifact contracts are satisfiable",
        "timestamp": "2026-07-10T00:11:53+00:00",
        "transition_id": "transition.0005"
      },
      {
        "artifacts": [
          "artifact.stage7.verification_result"
        ],
        "errors": [],
        "id": "stage_outcome.0004",
        "next_actions": [],
        "retryable": false,
        "stage": "stage7.verification",
        "status": "ready",
        "summary": "Stage7 execution_scope=operator_leaf_closure status=pass",
        "timestamp": "2026-07-10T00:48:51+00:00",
        "transition_id": "transition.0006"
      },
      {
        "artifacts": [
          "artifact.stage7.verification_result"
        ],
        "errors": [],
        "id": "stage_outcome.0005",
        "next_actions": [],
        "retryable": false,
        "stage": "stage7.verification",
        "status": "ready",
        "summary": "Stage7 execution_scope=single_layer_closure status=pass",
        "timestamp": "2026-07-10T07:58:49+00:00",
        "transition_id": "transition.0007"
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
      "checker": "verification_plan_static_check",
      "constraints": [
        "constraint.verification.plan"
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
    }
  ],
  "checker_results": [
    {
      "checker": "verification_plan_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 6 plan declares checker list, leaf stage agents, and merge agents"
    },
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
      "checker": "sacg_reference_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 3, Stage 4, and Stage 5 artifacts referenced by SACG are ready/promoted inputs"
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
        "summary": "board runtime evidence is required for final closure and is not claimed by Stage 6"
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
        "description": "The complete target checkpoint tensor catalog and hashes are available; sampled/default weights are not acceptance evidence.",
        "name": "case_real_weight_artifacts",
        "required": true
      },
      {
        "description": "The real target model runs on the reproducible random input and emits independent per-operator, single-layer, and all-target-Transformer-block boundary golden t...<len=167>",
        "name": "case_target_model_reference",
        "required": true
      },
      {
        "description": "Generated semantic testbenches encode the numeric policy and prove that the DUT consumes every required checkpoint-derived weight tensor.",
        "name": "case_semantic_testbench",
        "required": true
      },
      {
        "description": "Generated case RTL exposes expected leaf stage modules and stream boundaries.",
        "name": "case_stage_leaf_static",
        "required": true
      },
      {
        "description": "Each module boundary has a case-adapter-independent contract and trace schema for failure slicing.",
        "name": "boundary_contract_check",
        "required": true
      },
      {
        "description": "Every spatial operator leaf module has independent functional simulation evidence before any layer merge.",
        "name": "case_leaf_functional",
        "required": true
      },
      {
        "description": "Every spatial operator leaf module has a golden comparison or equivalent numeric contract evidence.",
        "name": "case_leaf_golden_compare",
        "required": true
      },
      {
        "description": "A reproducible testbench/RTL scaffold loads declared manifests and is hashable before functional simulation.",
        "name": "case_tb_scaffold",
        "required": true
      }
    ],
    "merge_agents": [
      {
        "depends_on": [
          "stage_00_rms_norm_1",
          "stage_01_self_attention",
          "stage_02_residual_add_1"
        ],
        "id": "merge.self_attention",
        "required_evidence": [
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "case_leaf_functional",
          "case_leaf_golden_compare"
        ],
        "role": "self-attention merge agent"
      },
      {
        "depends_on": [
          "stage_03_rms_norm_2",
          "stage_04_mlp_gate_proj",
          "stage_05_mlp_up_proj",
          "stage_06_activation_mul",
          "stage_07_mlp_down_proj",
          "stage_08_residual_add_2"
        ],
        "id": "merge.mlp",
        "required_evidence": [
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "case_leaf_functional",
          "case_leaf_golden_compare"
        ],
        "role": "MLP merge agent"
      },
      {
        "depends_on": [
          "merge.self_attention",
          "merge.mlp"
        ],
        "id": "merge.single_decoder_block",
        "required_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_tb_scaffold",
          "single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare"
        ],
        "role": "single block merge agent"
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
        "id": "verify.stage_00_rms_norm_1",
        "kind": "norm",
        "module_checks": [
          "RMSNorm",
          "VectorNorm"
        ],
        "op": "rms_norm_1",
        "required_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare"
        ],
        "stage_id": "stage_00_rms_norm_1"
      },
      {
        "id": "verify.stage_01_self_attention",
        "kind": "attention",
        "module_checks": [
          "QKVProjection",
          "RoPE",
          "AttentionGQA",
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
          "case_leaf_golden_compare"
        ],
        "stage_id": "stage_01_self_attention"
      },
      {
        "id": "verify.stage_02_residual_add_1",
        "kind": "residual",
        "module_checks": [
          "ResidualAdd",
          "Queue"
        ],
        "op": "residual_add_1",
        "required_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare"
        ],
        "stage_id": "stage_02_residual_add_1"
      }
    ],
    "strategy": "three_layer_repair_loop: operator_leaf_modules -> single_transformer_layer_kernel -> board_axi_ddr_wrapped_system"
  },
  "parameter_bindings": {
    "count": 9,
    "omitted_in_role_slice": true
  },
  "presence_summary": {
    "attention_semantics_present": true,
    "debug_boundary_contract_count": 13,
    "debug_trace_schema_present": true,
    "evidence_gate_count": 24,
    "evidence_path_requirement_count": 33,
    "merge_agent_count": 6,
    "parameter_binding_count": 9,
    "parameter_binding_stage_ids": [
      "stage_00_rms_norm_1",
      "stage_01_self_attention",
      "stage_02_residual_add_1",
      "stage_03_rms_norm_2",
      "stage_04_mlp_gate_proj",
      "stage_05_mlp_up_proj",
      "stage_06_activation_mul",
      "stage_07_mlp_down_proj",
      "stage_08_residual_add_2"
    ],
    "required_tool_protocol_count": 34,
    "stage_agent_count": 9,
    "stage_agent_ids": [
      "stage_00_rms_norm_1",
      "stage_01_self_attention",
      "stage_02_residual_add_1",
      "stage_03_rms_norm_2",
      "stage_04_mlp_gate_proj",
      "stage_05_mlp_up_proj",
      "stage_06_activation_mul",
      "stage_07_mlp_down_proj",
      "stage_08_residual_add_2"
    ],
    "verification_gate_dag_node_count": 33
  },
  "role_slice_policy": {
    "do_not_infer_missing_from_omitted_details": true,
    "sliced_for_subtask": "verification_artifacts.cross_layer_evidence_gate_auditor",
    "use_presence_summary_before_reporting_current_stage_missing_field_risks": true
  },
  "schema_version": "spatialaccagent.verification_artifacts_review.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {
    "current_stage_acceptance": [
      "verification_plan must declare the three debug/repair layers: operator leaf modules, single transformer-layer kernel, and board AXI/DDR wrapped system",
      "verification_artifact_contract must pass before the Stage 6 transition can be promoted",
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
        "attention_kind": "gqa",
        "causal": true,
        "gqa_group_size": 7,
        "head_dim": 64,
        "kv_storage_policy": "bounded by target_max_seq_len inside the generated block; external KV-cache materialization requires a later memory-layout artifact",
        "num_kv_heads": 2,
        "num_q_heads": 14,
        "position_encoding": {
          "rope_theta": 1000000.0,
          "type": "rope"
        },
        "seq_len_bound": 16,
        "stage_boundary": "logical self_attention stage covers QKV projection, RoPE, causal GQA attention, and output projection for decoder-block planning"
      },
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 10,
        "warnings": []
      },
      "data_edge_count": 13,
      "stage": "pipeline_planning",
      "stage_count": 9,
      "status": "ready",
      "stream_edge_count": 13
    },
    "stage4_parameter_binding": {
      "checker_summary": {
        "errors": [],
        "failed": 0,
        "passed": 6,
        "warnings": []
      },
      "global_params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "input_bits": 32,
        "lanes": 8,
        "output_bits": 32,
        "tile_k": 8,
        "tile_m": 8,
        "tile_n": 24
      },
      "numeric_binding_plan": {
        "acc_dtype": "fp32",
        "activation_dtype": "fp16",
        "cast_points": [
          {
            "input_bits": 32,
            "input_cast": "32_to_16",
            "internal_elem_bits": 16,
            "op": "rms_norm_1",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_00_rms_norm_1"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "self_attention",
            "output_bits": 32,
            "output_cast": "16_to_32",
            "residual_precision": null,
            "stage_id": "stage_01_self_attention"
          },
          {
            "input_bits": 32,
            "input_cast": "none",
            "internal_elem_bits": 32,
            "op": "residual_add_1",
            "output_bits": 32,
            "output_cast": "none",
            "residual_precision": 32,
            "stage_id": "stage_02_residual_add_1"
          },
          {
            "input_bits": 32,
            "input_cast": "32_to_16",
            "internal_elem_bits": 16,
            "op": "rms_norm_2",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_03_rms_norm_2"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "mlp_gate_proj",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_04_mlp_gate_proj"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "mlp_up_proj",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_05_mlp_up_proj"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "activation_mul",
            "output_bits": 16,
            "output_cast": "none",
            "residual_precision": null,
            "stage_id": "stage_06_activation_mul"
          },
          {
            "input_bits": 16,
            "input_cast": "none",
            "internal_elem_bits": 16,
            "op": "mlp_down_proj",
            "output_bits": 32,
            "output_cast": "16_to_32",
            "residual_precision": null,
            "stage_id": "stage_07_mlp_down_proj"
          },
          {
            "input_bits": 32,
            "input_cast": "none",
            "internal_elem_bits": 32,
            "op": "residual_add_2",
            "output_bits": 32,
            "output_cast": "none",
            "residual_precision": 32,
            "stage_id": "stage_08_residual_add_2"
          }
        ],
        "eps_source": "constraint.model.decoder.norm_type/default eps from template binding",
        "policy_id": "current_run_numeric_policy.md",
        "rounding": "nearest_even",
        "saturation": false,
        "source": "constraint.numeric.policy.default_rules",
        "weight_dtype": "fp16"
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
          }
        ],
        "summary": "completed 4 compile/elaboration command(s)"
      },
      "contract_check": {
        "errors": [],
        "status": "pass",
        "summary": "all code generation contracts passed"
      },
      "generated_files_count": 273,
      "generated_package_root": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
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
        "model_type": "qwen2",
        "planned_for_target": [
          "generated.model_ir",
          "generated.arch_plan",
          "generated.chisel_modules",
          "generated.top_wrapper",
          "generated.fpga_axi_ddr_top_wrapper",
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
      "boundary_count": 13,
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
        "localization": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/failure_localization.json",
        "manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/trace_manifest.json",
        "trace": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json"
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
        "kind": "vcs_liveness_not_acceptance",
        "name": "case_vcs_liveness",
        "scope": "remote"
      },
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
      "later_stage_missing_gate_or_tool_requires_stage6_backtrack": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "random_or_rtl_derived_expected_output_forbidden": true,
      "real_axi_ddr_runtime_required": true,
      "real_functional_sim_required": true,
      "real_target_model_reference_required": true,
      "real_weight_artifacts_required": true,
      "same_stage_retry_can_supersede_prior_stage6_barriers_after_promotion": true,
      "smoke_is_not_acceptance": true,
      "transformer_blocks_are_the_only_accelerator_scope": true
    },
    "required_evidence_gates": [],
    "required_tool_protocols": [
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_weight_manifest_generate",
        "name": "case_weight_manifest_generate",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "target_model_reference_generate",
        "name": "case_target_model_reference",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "semantic_testbench_generate",
        "name": "case_semantic_testbench",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_tb_scaffold_generate",
        "name": "case_tb_scaffold_generate",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_tb_scaffold",
        "name": "case_tb_scaffold",
        "planned_consumes": [],
        "planned_produces": [],
        "required": true,
        "scope": "local"
      },
      {
        "configured": true,
        "evidence_status": "required_pending_execution",
        "kind": "case_stage_leaf_static",
        "name": "case_stage_leaf_static",
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
          "name": "leaf_stage.stage_00_rms_norm_1",
          "role": "verify spatial operator module stage_00_rms_norm_1 before any layer/block merge"
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
          "name": "leaf_stage.stage_03_rms_norm_2",
          "role": "verify spatial operator module stage_03_rms_norm_2 before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_04_mlp_gate_proj",
          "role": "verify spatial operator module stage_04_mlp_gate_proj before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_05_mlp_up_proj",
          "role": "verify spatial operator module stage_05_mlp_up_proj before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_06_activation_mul",
          "role": "verify spatial operator module stage_06_activation_mul before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_07_mlp_down_proj",
          "role": "verify spatial operator module stage_07_mlp_down_proj before any layer/block merge"
        },
        {
          "depends_on": [],
          "evidence_status": "required_pending_execution",
          "name": "leaf_stage.stage_08_residual_add_2",
          "role": "verify spatial operator module stage_08_residual_add_2 before any layer/block merge"
        },
        {
          "depends_on": [
            "leaf_stage.stage_00_rms_norm_1",
            "leaf_stage.stage_01_self_attention",
            "leaf_stage.stage_02_residual_add_1",
            "leaf_stage.stage_03_rms_norm_2",
            "leaf_stage.stage_04_mlp_gate_proj",
            "leaf_stage.stage_05_mlp_up_proj",
            "leaf_stage.stage_06_activation_mul",
            "leaf_stage.stage_07_mlp_down_proj",
            "leaf_stage.stage_08_residual_add_2"
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
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_tb_scaffold",
          "role": "materialize and audit testbench/RTL scaffold that loads the declared input and weight artifacts"
        },
        {
          "depends_on": [
            "case_leaf_golden_compare",
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
            "case_leaf_golden_compare",
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
            "case_semantic_testbench"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_multilayer_pipeline",
          "role": "prove multi-layer pipeline scaffold and layer-to-layer ordering"
        },
        {
          "depends_on": [
            "case_multilayer_pipeline"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_board_interface_discovery",
          "role": "discover board/app-shell interface facts before board-wrapped functional simulation"
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
            "case_single_layer_golden_compare",
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
            "case_axi_ddr_interface",
            "case_board_interface_discovery"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_vivado_synthesis",
          "role": "run Vivado synthesis and collect utilization/timing evidence"
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
            "functional_sim",
            "case_axi_ddr_interface",
            "case_multilayer_pipeline"
          ],
          "evidence_status": "required_pending_execution",
          "name": "case_runtime_bitstream",
          "role": "run runtime/app-shell bitstream flow only after functional simulation and Vivado implementation pass"
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
            "functional_sim",
            "case_real_weight_artifacts"
          ],
          "evidence_status": "required_pending_execution",
          "name": "board_runtime",
          "role": "program board/runtime and collect valid output evidence"
        }
      ],
      "policy": {
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
          "testbench_scaffold",
          "single_layer_kernel",
          "single_layer_functional",
          "single_layer_golden_compare",
          "multilayer_pipeline",
          "board_interface_discovery",
          "board_wrapper_interface",
          "functional_simulation",
          "multilayer_functional",
          "multilayer_deadlock_liveness",
          "axi_protocol_check",
          "ddr_image_roundtrip",
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
          "operator_leaf_golden_compare"
        ],
        "layer2_single_layer_kernel_closure": [
          "testbench_scaffold",
          "single_layer_kernel",
          "single_layer_functional",
          "single_layer_golden_compare"
        ],
        "layer3_board_axi_ddr_wrapper_closure": [
          "multilayer_pipeline",
          "board_interface_discovery",
          "board_wrapper_interface",
          "functional_simulation",
          "multilayer_functional",
          "multilayer_deadlock_liveness",
          "axi_protocol_check",
          "ddr_image_roundtrip"
        ],
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "multilayer_pipeline_before_axi_ddr": true,
        "operator_leaf_functional_before_single_layer_kernel": true,
        "real_input_and_weight_artifacts_required": true,
        "real_model_inference_golden_required": true,
        "rtl_derived_or_random_expected_output_forbidden": true,
        "single_layer_functional_before_board_axi_ddr_wrapped_system": true,
        "single_layer_kernel_after_leaf_modules": true,
        "smoke_is_not_acceptance": true,
        "testbench_scaffold_before_functional_sim": true,
        "third_layer_contains_multilayer_pipeline_and_board_axi_ddr_wrapper_subgates": true,
        "three_debug_layers": [
          "operator_leaf_modules",
          "single_transformer_layer_kernel",
          "board_axi_ddr_wrapped_system"
        ],
        "transformer_blocks_are_the_only_accelerator_scope": true
      },
      "schema_version": "spatialaccagent.verification_gate_dag.v0"
    }
  }
}
</candidate_stage_artifact>

<sacg_memory>
{}
</sacg_memory>

<sacg_memory_truth>
{}
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
