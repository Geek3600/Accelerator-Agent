<agent>
team_decomposer
</agent>

<task>
Decide whether this stage should be decomposed into parallel specialist sub-agents, then produce the subtask plan.
</task>

<rules>
1. Use split_required=false only when the stage is atomic and no independent specialist can add value.
2. If split_required=true, create 2 to 6 subtasks. Put independent specialists in parallel_group=0 and optional auditors/evidence gates in parallel_group=1.
3. Each subtask must have a chip-design-team role and a bounded objective.
4. Each subtask must explicitly define role_profile and role_assignment: mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope.
5. Each subtask must declare action_type, expected_artifacts, acceptance_checkers, handoff_to, and handoff_rule.
6. Role assignments must make cooperation explicit: what this sub-agent consumes, what it produces, which downstream agents/tools consume its output, and which checker accepts it.
7. Every subtask must focus on cross-layer consistency, template binding, checker evidence, implementation/deployment evidence, or repair boundaries.
8. Ground acceptance_checkers and tool-oriented roles in action_grounding_registry. Use exact canonical names whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
9. Use state_summary.sacg_memory_truth, not historical memory text, to decide whether retry requests, backtrack requests, or contamination barriers are currently active blockers.
10. If a required checker/tool is missing, mark the subtask handoff as requiring planned_tool.<short_name> or planned_checker.<short_name> implementation.
11. Do not create agents for generic brainstorming, paper writing, marketing, or unrelated code cleanup.
12. Use the reference subtask plan as a formatting and role-coverage guide; the actual split decision must come from the LLM response.
</rules>

<stage>
repair
</stage>

<objective>
Classify failed evidence into bounded repair actions while respecting human approval boundaries.
</objective>

<paper_problem_definition>
Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design
</paper_problem_definition>

<method_boundary>
SACG-guided, template-constrained, checker-verified design closure; not free-form RTL generation.
</method_boundary>

<role_catalog>
[
  {
    "capabilities": [
      "extract model semantics",
      "audit shape and head mapping",
      "track residual/operator order"
    ],
    "constraint_focus": [
      "constraint.model.decoder",
      "constraint.shape.model"
    ],
    "family": "model_shape",
    "keywords": [
      "model",
      "shape",
      "graph",
      "operator",
      "intake"
    ]
  },
  {
    "capabilities": [
      "bind trusted templates",
      "audit numeric policy",
      "check resource-risk assumptions"
    ],
    "constraint_focus": [
      "constraint.numeric.policy",
      "constraint.template.library",
      "constraint.parameter.binding"
    ],
    "family": "numeric_template",
    "keywords": [
      "numeric",
      "template",
      "parameter",
      "dse",
      "resource"
    ]
  },
  {
    "capabilities": [
      "audit data order",
      "check transfer-count/liveness risks",
      "bind DDR/runtime layout"
    ],
    "constraint_focus": [
      "constraint.stream.order",
      "constraint.beat.pipeline",
      "constraint.memory.board",
      "constraint.runtime.board"
    ],
    "family": "data_memory_runtime",
    "keywords": [
      "data order",
      "transfer",
      "memory",
      "runtime",
      "dataflow",
      "stream",
      "beat"
    ]
  },
  {
    "capabilities": [
      "classify evidence",
      "map failures to violated constraints",
      "enforce repair boundaries"
    ],
    "constraint_focus": [
      "constraint.verification.plan",
      "constraint.human.boundary"
    ],
    "family": "verification_repair",
    "keywords": [
      "verification",
      "checker",
      "failure",
      "repair",
      "boundary",
      "auditor",
      "gate"
    ]
  },
  {
    "capabilities": [
      "prepare implementation handoff",
      "audit timing/board evidence",
      "block unsupported pass claims"
    ],
    "constraint_focus": [
      "constraint.backend_board.plan",
      "constraint.backend.package",
      "constraint.deployment.board"
    ],
    "family": "implementation_deployment",
    "keywords": [
      "backend",
      "synthesis",
      "implementation",
      "timing",
      "board",
      "deployment"
    ]
  }
]
</role_catalog>

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
    },
    {
      "id": "artifact.stage6.canonical_gate_dag_refinement",
      "type": "stage.canonical_gate_dag_refinement"
    },
    {
      "id": "artifact.stage6.semantic_promotion_gate_matrix",
      "type": "stage.semantic_promotion_gate_matrix"
    },
    {
      "id": "artifact.stage6.immutable_semantic_identity_contract",
      "type": "stage.immutable_semantic_identity_contract"
    },
    {
      "id": "artifact.stage6.canonical_functional_sim_binding_contract",
      "type": "stage.canonical_functional_sim_binding_contract"
    },
    {
      "id": "artifact.stage6.backend_eligibility_gate_contract",
      "type": "stage.backend_eligibility_gate_contract"
    },
    {
      "id": "artifact.stage6.failed_node_repair_route_matrix",
      "type": "stage.failed_node_repair_route_matrix"
    },
    {
      "id": "artifact.stage6.certificate_reuse_and_target_discovery_contract",
      "type": "stage.certificate_reuse_and_target_discovery_contract"
    },
    {
      "id": "artifact.stage6.action_materialization_coverage",
      "type": "stage.stage6_action_materialization_coverage"
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
  "failed_invariants": [
    {
      "checker": "required_real_tool_evidence_check",
      "id": "invariant.required_real_tool_evidence_check"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_00_rms_norm_1",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_00_rms_norm_1"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_01_self_attention",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_01_self_attention"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_02_residual_add_1",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_02_residual_add_1"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_03_rms_norm_2",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_03_rms_norm_2"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_04_mlp_gate_proj",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_04_mlp_gate_proj"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_05_mlp_up_proj",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_05_mlp_up_proj"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_06_activation_mul",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_06_activation_mul"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_07_mlp_down_proj",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_07_mlp_down_proj"
    },
    {
      "checker": "real_tool.case_tb_scaffold_generate__leaf_stage_stage_08_residual_add_2",
      "id": "invariant.real_tool.case_tb_scaffold_generate__leaf_stage_stage_08_residual_add_2"
    },
    {
      "checker": "case_functional_sim_precondition_check",
      "id": "invariant.case_functional_sim_precondition_check"
    },
    {
      "checker": "hierarchical_verification_maturity_check",
      "id": "invariant.hierarchical_verification_maturity_check"
    },
    {
      "checker": "verification_agent_decision_check",
      "id": "invariant.verification_agent_decision_check"
    },
    {
      "checker": "real_tool.case_semantic_testbench",
      "id": "invariant.real_tool.case_semantic_testbench"
    },
    {
      "checker": "real_weight_semantic_evidence_check",
      "id": "invariant.real_weight_semantic_evidence_check"
    }
  ],
  "nodes": 32,
  "sacg_memory": {
    "active_contamination_barriers": [
      {
        "artifact_id": "artifact.stage7.verification_result",
        "id": "contamination_barrier.0001",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      },
      {
        "artifact_id": "artifact.stage7.real_tool_results",
        "id": "contamination_barrier.0002",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      },
      {
        "artifact_id": "artifact.stage7.debug_closure",
        "id": "contamination_barrier.0003",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      }
    ],
    "open_backtrack_requests": [],
    "open_retry_requests": [
      {
        "blocked_artifacts": [
          "artifact.stage7.verification_result"
        ],
        "id": "retry_request.0001",
        "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
        "required_inputs": [
          "artifact.stage6.verification_artifact_contract",
          "artifact.stage6.llm_action_audit"
        ],
        "stage": "stage7.verification",
        "status": "open",
        "target_stage": "stage7.verification",
        "timestamp": "2026-07-10T15:47:40+00:00"
      }
    ],
    "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
    "recent_contamination_barriers": [
      {
        "artifact_id": "artifact.stage7.verification_result",
        "id": "contamination_barrier.0001",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      },
      {
        "artifact_id": "artifact.stage7.real_tool_results",
        "id": "contamination_barrier.0002",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      },
      {
        "artifact_id": "artifact.stage7.debug_closure",
        "id": "contamination_barrier.0003",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      }
    ],
    "recent_failure_lessons": [
      {
        "artifacts": [
          "artifact.stage7.verification_result"
        ],
        "failure_class": "verification_real_tool_or_gate",
        "id": "failure_lesson.0001",
        "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
        "retry_scope": "stage7_or_stage6_backtrack",
        "stage": "stage7.verification",
        "summary": "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_00_rms_norm_1: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_01_self_attention: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_02_residual_add_1: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_03_rms_norm_2: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_04_mlp_gate_proj: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_05_mlp_up_proj: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation; real_tool.case_tb_scaffold_generate__leaf_stage_stage_06_activation_mul: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "violated_constraints": [
          "constraint.verification.plan",
          "constraint.verification.hierarchy",
          "constraint.tool.protocols",
          "constraint.deployment.board"
        ]
      }
    ],
    "recent_stage_outcomes": [
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
      },
      {
        "artifacts": [
          "artifact.stage6.verification_plan",
          "artifact.stage6.verification_artifact_contract",
          "artifact.stage6.llm_action_audit",
          "artifact.stage6.llm_io_quality"
        ],
        "errors": [],
        "id": "stage_outcome.0006",
        "next_actions": [],
        "retryable": false,
        "stage": "stage6.verification_artifacts",
        "status": "ready",
        "summary": "all verification artifact contracts are satisfiable",
        "timestamp": "2026-07-10T15:22:54+00:00",
        "transition_id": "transition.0008"
      },
      {
        "artifacts": [
          "artifact.stage7.verification_result"
        ],
        "errors": [
          "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_00_rms_norm_1: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_01_self_attention: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_02_residual_add_1: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_03_rms_norm_2: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_04_mlp_gate_proj: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_05_mlp_up_proj: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_06_activation_mul: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_07_mlp_down_proj: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "real_tool.case_tb_scaffold_generate__leaf_stage_stage_08_residual_add_2: returncode=1 report_status=incomplete blockers=DUT weight-binding manifest status is not pass; DUT weight binding accelerator_scope is not transformer_blocks_only; DUT weight binding source_checkpoint_sha256 does not match verification preparation; DUT weight binding source_reference_sha256 does not match verification preparation",
          "case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; DUT real-weight binding manifest missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; testbench_artifact_loading missing required tokens: ['target_model_inference', 'dut_weight_binding', 'numeric_policy_sha256']; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']",
          "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail, case_tb_scaffold_generate__leaf_stage_stage_00_rms_norm_1=fail, case_tb_scaffold_generate__leaf_stage_stage_01_self_attention=fail, case_tb_scaffold_generate__leaf_stage_stage_02_residual_add_1=fail, case_tb_scaffold_generate__leaf_stage_stage_03_rms_norm_2=fail, case_tb_scaffold_generate__leaf_stage_stage_04_mlp_gate_proj=fail, case_tb_scaffold_generate__leaf_stage_stage_05_mlp_up_proj=fail, case_tb_scaffold_generate__leaf_stage_stage_06_activation_mul=fail, case_tb_scaffold_generate__leaf_stage_stage_07_mlp_down_proj=fail, case_tb_scaffold_generate__leaf_stage_stage_08_residual_add_2=fail; dependency_blocked=['case_tb_scaffold_generate=not_run', 'case_stage_leaf_static=not_run', 'case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']",
          "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: operator_leaf_functional: semantic evidence report status is fail; operator_leaf_functional: semantic evidence report does not bind the current evidence contract; operator_leaf_functional: accelerator acceptance scope is not transformer-block-only; operator_leaf_functional: weight tensor coverage is incomplete for this verification scope; operator_leaf_functional: DUT consumption of the real weights is not proven; operator_leaf_functional: weight manifest/tensor hashes are missing; operator_leaf_functional: explicit numeric comparison atol/rtol/max_mismatch_fraction is missing; operator_leaf_functional: semantic testbench does not prove real-weight loading; operator_leaf_functional: semantic comparison did not pass; operator_leaf_functional: not every target-model operator has complete semantic evidence",
          "hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_stage_leaf_static=not_run, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run; real-weight semantic evidence contract failed: operator_leaf_functional: semantic evidence report status is fail; operator_leaf_functional: semantic evidence report does not bind the current evidence contract; operator_leaf_functional: accelerator acceptance scope is not transformer-block-only; operator_leaf_functional: weight tensor coverage is incomplete for this verification scope; operator_leaf_functional: DUT consumption of the real weights is not proven; operator_leaf_functional: weight manifest/tensor hashes are missing; operator_leaf_functional: explicit numeric comparison atol/rtol/max_mismatch_fraction is missing; operator_leaf_functional: semantic testbench does not prove real-weight loading; operator_leaf_functional: semantic comparison did not pass; operator_leaf_functional: not every target-model operator has complete semantic evidence",
          "verification_agent_decision_check: verification.evidence_classifier: blocked_current_scope: The current operator-leaf closure is blocked by semantic-verification contract and DUT loader/harness binding deficiencies, not by a demonstrated RTL value mismatch. Real-tool evidence passes for the complete checkpoint catalog, independent target-model reference, boundary contract, and per-stage leaf static exposure. The semantic testbench fails because the DUT binding has the wrong accelerator scope and immutable hashes, lacks all 12 required current-scope tensor hashes, permits default/identity fallback, lacks stage harnesses and consumption proof, and the numeric policy has no explicit atol/rtol/max_mismatch_fraction. Leaf functional simulation, golden comparison, and semantic aggregation were dependency-blocked and did not execute. Numeric tolerance cannot be filled in during this repair loop; it requires an approved backtrack and a new immutable verification contract before bounded loader/harness repair and same-layer rerun."
        ],
        "id": "stage_outcome.0007",
        "next_actions": [
          "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
        ],
        "retryable": true,
        "stage": "stage7.verification",
        "status": "needs_repair",
        "summary": "Stage7 execution_scope=operator_leaf_closure status=fail",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      }
    ],
    "schema_version": "spatialaccagent.sacg_memory.v0"
  },
  "sacg_memory_truth": {
    "active_contamination_barrier_count": 3,
    "active_contamination_barriers": [
      {
        "artifact_id": "artifact.stage7.verification_result",
        "id": "contamination_barrier.0001",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      },
      {
        "artifact_id": "artifact.stage7.real_tool_results",
        "id": "contamination_barrier.0002",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      },
      {
        "artifact_id": "artifact.stage7.debug_closure",
        "id": "contamination_barrier.0003",
        "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
        "reason": "one or more framework static checks failed",
        "status": "active",
        "timestamp": "2026-07-10T15:47:40+00:00",
        "transition_id": "transition.0009"
      }
    ],
    "active_contamination_barriers_truncated": false,
    "open_backtrack_request_count": 0,
    "open_backtrack_requests": [],
    "open_backtrack_requests_truncated": false,
    "open_retry_request_count": 1,
    "open_retry_requests": [
      {
        "blocked_artifacts": [
          "artifact.stage7.verification_result"
        ],
        "id": "retry_request.0001",
        "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
        "required_inputs": [
          "artifact.stage6.verification_artifact_contract",
          "artifact.stage6.llm_action_audit"
        ],
        "stage": "stage7.verification",
        "status": "open",
        "target_stage": "stage7.verification",
        "timestamp": "2026-07-10T15:47:40+00:00"
      }
    ],
    "open_retry_requests_truncated": false,
    "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
    "schema_version": "spatialaccagent.sacg_memory_truth.v0",
    "truth_source": "source_sacg_state.memory"
  }
}
</state_summary>

<candidate_stage_artifact>
{
  "_more_keys": 6,
  "case_adapter": {
    "case_id": "qwen2_hf_case",
    "model_family": "qwen2",
    "source": "built_in_case_adapter",
    "status": "ready"
  },
  "diagnostics": {
    "case_vcs_functional": null,
    "contract_guided_debug_closure": {
      "_keys": [
        "causal_path",
        "current_layer_failure_context",
        "failed_boundaries",
        "failing_transaction",
        "failure_signature"
      ],
      "_size": 15,
      "_type": "dict"
    },
    "hierarchical_repair_loop": {
      "_keys": [
        "agent_runtime_llm_blocker",
        "current_layer",
        "debug_loop_contract",
        "failed_current_layer_gates",
        "failure_kind"
      ],
      "_size": 14,
      "_type": "dict"
    }
  },
  "failures": [
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 16,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 16,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 16,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 16,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 16,
      "_type": "dict"
    },
    {
      "_more_items": 10
    }
  ],
  "note": "Failing checkers are classified; not_run real tools are evidence gaps, not automatic repair failures.",
  "pending_evidence": [
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 15,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 14,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 15,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 15,
      "_type": "dict"
    },
    {
      "_keys": [
        "acceptance_role",
        "checker",
        "command",
        "failure_class",
        "kind"
      ],
      "_size": 15,
      "_type": "dict"
    }
  ]
}
</candidate_stage_artifact>

<reference_subtask_plan_if_split_is_needed>
[
  {
    "acceptance_checkers": [
      "repair_boundary_check",
      "sacg_static_check"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "failures",
      "repair_actions"
    ],
    "constraints": [
      "constraint.verification.plan",
      "constraint.human.boundary"
    ],
    "id": "repair.root_cause_engineer",
    "objective": "Check whether each repair action is tied to evidence and a violated constraint rather than a raw symptom.",
    "parallel_group": 0,
    "role": "root cause engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 2,
          "_type": "list"
        },
        "consumes": {
          "_keys": [
            "artifact_focus",
            "constraints"
          ],
          "_size": 2,
          "_type": "dict"
        },
        "handoff_to": {
          "_size": 3,
          "_type": "list"
        },
        "produces": {
          "_size": 5,
          "_type": "list"
        }
      },
      "decision_authority": {
        "_size": 3,
        "_type": "list"
      },
      "mission": "Check whether each repair action is tied to evidence and a violated constraint rather than a raw symptom.",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 4,
        "_type": "list"
      },
      "professional_family": "stage_specialist"
    },
    "role_profile": {
      "capabilities": [
        "audit stage-local artifact",
        "map observations to SACG constraints"
      ],
      "constraint_focus": [],
      "family": "stage_specialist"
    },
    "title": "Review failed checks and root-cause candidates"
  },
  {
    "acceptance_checkers": [
      "repair_boundary_check",
      "sacg_static_check"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "repair_actions"
    ],
    "constraints": [
      "constraint.human.boundary"
    ],
    "id": "repair.repair_boundary_engineer",
    "objective": "Check whether proposed repair scopes are auto-allowed, approval-required, or forbidden under the human-agent boundary.",
    "parallel_group": 1,
    "role": "repair boundary engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 2,
          "_type": "list"
        },
        "consumes": {
          "_keys": [
            "artifact_focus",
            "constraints"
          ],
          "_size": 2,
          "_type": "dict"
        },
        "handoff_to": {
          "_size": 3,
          "_type": "list"
        },
        "produces": {
          "_size": 5,
          "_type": "list"
        }
      },
      "decision_authority": {
        "_size": 3,
        "_type": "list"
      },
      "mission": "Check whether proposed repair scopes are auto-allowed, approval-required, or forbidden under the human-agent boundary.",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "verification_repair"
    },
    "role_profile": {
      "capabilities": [
        "classify evidence",
        "map failures to violated constraints",
        "enforce repair boundaries"
      ],
      "constraint_focus": [
        "constraint.verification.plan",
        "constraint.human.boundary"
      ],
      "family": "verification_repair"
    },
    "title": "Review repair permission boundaries"
  }
]
</reference_subtask_plan_if_split_is_needed>

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
    "reason": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "split_required": {
      "type": "boolean"
    },
    "stage": {
      "type": "string"
    },
    "subtasks": {
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
          "agent": {
            "type": "string"
          },
          "artifact_focus": {
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
          "expected_artifacts": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "handoff_required": {
            "type": "boolean"
          },
          "handoff_rule": {
            "additionalProperties": true,
            "type": "object"
          },
          "handoff_to": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "id": {
            "type": "string"
          },
          "objective": {
            "type": "string"
          },
          "parallel_group": {
            "type": "integer"
          },
          "role": {
            "type": "string"
          },
          "role_assignment": {
            "additionalProperties": true,
            "type": "object"
          },
          "role_profile": {
            "additionalProperties": true,
            "type": "object"
          },
          "title": {
            "type": "string"
          }
        },
        "required": [
          "id",
          "agent",
          "role",
          "title",
          "objective",
          "constraints",
          "artifact_focus",
          "parallel_group",
          "handoff_required"
        ],
        "type": "object"
      },
      "type": "array"
    }
  },
  "required": [
    "schema_version",
    "stage",
    "split_required",
    "reason",
    "subtasks"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
