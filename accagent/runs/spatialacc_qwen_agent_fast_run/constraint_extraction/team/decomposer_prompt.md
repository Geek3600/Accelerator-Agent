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
4. Each subtask must declare action_type, expected_artifacts, acceptance_checkers, handoff_to, and handoff_rule.
5. Every subtask must focus on cross-layer consistency, template binding, checker evidence, implementation/deployment evidence, or repair boundaries.
6. Ground acceptance_checkers and tool-oriented roles in action_grounding_registry. Use exact canonical names whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
7. If a required checker/tool is missing, mark the subtask handoff as requiring planned_tool.<short_name> or planned_checker.<short_name> implementation.
8. Do not create agents for generic brainstorming, paper writing, marketing, or unrelated code cleanup.
9. Use the reference subtask plan as a formatting and role-coverage guide; the actual split decision must come from the LLM response.
</rules>

<stage>
constraint_extraction
</stage>

<objective>
Build and audit the initial design graph as shared state for a chip-design-team flow. The graph must preserve cross-layer consistency across model, shape, numeric policy, template choices, board DDR/AXI/runtime information, tool availability, and human boundaries.
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
    }
  ],
  "design_id": "qwen2_spatialacc_agent_run",
  "edges": 8,
  "failed_invariants": [],
  "nodes": 21,
  "sacg_memory": {
    "active_contamination_barriers": [],
    "open_backtrack_requests": [],
    "open_retry_requests": [],
    "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
    "recent_contamination_barriers": [],
    "recent_failure_lessons": [],
    "recent_stage_outcomes": [],
    "schema_version": "spatialaccagent.sacg_memory.v0"
  }
}
</state_summary>

<candidate_stage_artifact>
{
  "candidate_design_graph_summary": {
    "_more_keys": 4,
    "constraint_ids": {
      "_size": 16,
      "_type": "list"
    },
    "evidence_fields": {
      "_size": 50,
      "_type": "list"
    },
    "input_groups": {
      "_keys": [
        "evidence",
        "materials",
        "tools"
      ],
      "_size": 3,
      "_type": "dict"
    },
    "node_ids": {
      "_size": 21,
      "_type": "list"
    },
    "num_constraints": 16
  },
  "prepared_inputs_manifest": {
    "_more_keys": 7,
    "design_team": {
      "_keys": [
        "aggregate",
        "approval_required_for",
        "completed_subtasks",
        "decomposer_error",
        "decomposer_used_fallback"
      ],
      "_size": 16,
      "_type": "dict"
    },
    "errors": {
      "_size": 0,
      "_type": "list"
    },
    "inputs": {
      "_keys": [
        "case_adapter",
        "design_space",
        "field_evidence",
        "field_evidence_candidates",
        "human_agent_boundary"
      ],
      "_size": 16,
      "_type": "dict"
    },
    "mode": "independent_from_scratch_design",
    "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run"
  },
  "validation_errors": []
}
</candidate_stage_artifact>

<reference_subtask_plan_if_split_is_needed>
[
  {
    "acceptance_checkers": [
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "candidate_design_graph_summary",
      "model_operator_nodes"
    ],
    "constraints": [
      "constraint.model.decoder",
      "constraint.shape.model"
    ],
    "id": "constraint_extraction.model_graph_engineer",
    "objective": "Check that model operators, residual order, attention facts, head mapping, hidden sizes, and sequence facts are explicit design-graph nodes and constraints.",
    "parallel_group": 0,
    "role": "model graph engineer",
    "title": "Review model and shape constraints"
  },
  {
    "acceptance_checkers": [
      "sacg_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "candidate_design_graph_summary",
      "input_artifacts"
    ],
    "constraints": [
      "constraint.source.materials",
      "constraint.source.evidence",
      "constraint.tool.profile",
      "constraint.cross_layer.input_consistency"
    ],
    "id": "constraint_extraction.input_evidence_engineer",
    "objective": "Check that user-provided board materials, quantization materials, sample projects, extracted field evidence, tool profiles, and real tool probe results are represented in the initi...<len=196>",
    "parallel_group": 0,
    "role": "input evidence engineer",
    "title": "Review current-run materials and evidence"
  },
  {
    "acceptance_checkers": [
      "addr_map_check",
      "implementation_package_static",
      "real_tool_evidence_check",
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "candidate_design_graph_summary",
      "input_artifacts"
    ],
    "constraints": [
      "constraint.template.library",
      "constraint.arch.design_space",
      "constraint.memory.board",
      "constraint.runtime.board"
    ],
    "id": "constraint_extraction.template_platform_engineer",
    "objective": "Check that template library, design space, board, memory, runtime, and tool protocols are represented as design-graph constraints.",
    "parallel_group": 0,
    "role": "template platform engineer",
    "title": "Review template/platform constraints"
  },
  {
    "acceptance_checkers": [
      "repair_boundary_check",
      "sacg_static_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "candidate_design_graph_summary",
      "validation_errors"
    ],
    "constraints": [
      "constraint.human.boundary",
      "constraint.cross_layer.input_consistency"
    ],
    "id": "constraint_extraction.constraint_graph_auditor",
    "objective": "Check whether the initial design graph can act as shared design state for later agent subtasks and checker evidence.",
    "parallel_group": 1,
    "role": "constraint graph auditor",
    "title": "Review design graph reference integrity"
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
      "functional_sim",
      "data_order_trace_check",
      "deadlock_watchdog"
    ],
    "action_type": "real_tool_execution",
    "consumes": [
      "artifact.stage6.verification_artifact_contract",
      "generated/chisel/runtime/runtime_config.json",
      "verification/case_real_weights/input_manifest.json",
      "verification/case_real_weights/packed_weight_manifest.json"
    ],
    "id": "example.run_real_functional_sim",
    "on_failure": "route simulator evidence to Stage8 repair with the violated SACG constraints; do not proceed to Vivado.",
    "produces": [
      "verification/case_diagnostics/vcs_functional_diagnosis.json"
    ],
    "rationale": "Run a real simulator after static hierarchy and artifact gates pass.",
    "requires_approval": false,
    "stage": "verification",
    "tool_roles": [
      "case_vcs_functional_sim",
      "case_vcs_evidence_analyzer"
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
  "locked_model": "gpt-5.5",
  "mode": "llm",
  "model": "gpt-5.5",
  "model_override_approval_path": "",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
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
