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
verification_artifacts
</stage>

<objective>
Plan and refine the real-tool verification gate DAG for the three repair-loop layers: operator leaf modules, a connected single transformer-layer kernel, and the board AXI/DDR wrapped system. Multi-layer pipeline, AXI/DDR, DDR image, and functional-simulation checks are third-layer subgates; Vivado bitstream and board runtime remain downstream after verification closure.
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
  "board_test_policy": "required_for_final_design_closure",
  "checker_plan": [
    {
      "checker": "task_card_check",
      "constraints": [
        "constraint.task.goal"
      ]
    },
    {
      "checker": "model_config_check",
      "constraints": [
        "constraint.model.decoder",
        "constraint.shape.model"
      ]
    },
    {
      "checker": "numeric_policy_check",
      "constraints": [
        "constraint.numeric.policy"
      ]
    },
    {
      "checker": "template_coverage_check",
      "constraints": [
        "constraint.template.library",
        "constraint.codegen.package"
      ]
    },
    {
      "checker": "stream_plan_check",
      "constraints": [
        "constraint.stream.order",
        "constraint.beat.pipeline"
      ]
    },
    {
      "checker": "parameter_binding_static_check",
      "constraints": [
        "constraint.parameter.binding"
      ]
    },
    {
      "checker": "code_generation_manifest_static_check",
      "constraints": [
        "constraint.codegen.package"
      ]
    },
    {
      "checker": "codegen_package_static_check",
      "constraints": [
        "constraint.codegen.package"
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
    },
    {
      "checker": "sacg_reference_check",
      "constraints": [
        "constraint.pipeline.structure"
      ]
    },
    {
      "checker": "data_order_trace_check",
      "constraints": [
        "constraint.stream.order",
        "constraint.beat.pipeline"
      ]
    },
    {
      "checker": "deadlock_watchdog",
      "constraints": [
        "constraint.verification.hierarchy",
        "constraint.tool.protocols"
      ]
    },
    {
      "checker": "implementation_package_static",
      "constraints": [
        "constraint.backend.package",
        "constraint.deployment.board"
      ]
    },
    {
      "checker": "board_runtime",
      "constraints": [
        "constraint.deployment.board",
        "constraint.human.boundary"
      ]
    }
  ],
  "checker_results": [
    {
      "checker": "task_card_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "task goal constraint is present in SACG"
    },
    {
      "checker": "model_config_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "model, shape, and attention semantics are visible"
    },
    {
      "checker": "numeric_policy_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 4 numeric binding plan and global params are visible"
    },
    {
      "checker": "template_coverage_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 5 template provenance and package static check are visible"
    },
    {
      "checker": "stream_plan_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 3 stream/data-edge plan passed static checks"
    },
    {
      "checker": "parameter_binding_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 4 parameter binding static checks passed"
    },
    {
      "checker": "code_generation_manifest_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "Stage 5 manifest targets the current case artifact set"
    },
    {
      "checker": "codegen_package_static_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "generated package manifest is structurally complete"
    },
    {
      "checker": "codegen_compile_gate",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "completed 4 compile/elaboration command(s)"
    },
    {
      "checker": "codegen_contract_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "all code generation contracts passed"
    },
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
      "checker": "memory_runtime_plan_check",
      "errors": [],
      "evidence_phase": "current_stage_static_check",
      "execution_status": "not_applicable",
      "status": "pass",
      "summary": "generated code package, memory layout, and runtime config exist for verification handoff"
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
    },
    {
      "checker": "implementation_package_static",
      "errors": [],
      "evidence_phase": "downstream_gate_declared",
      "execution_status": "not_run_required_downstream",
      "status": "pending_downstream",
      "summary": "implementation package evidence is required through the case_runtime_bitstream downstream gate"
    },
    {
      "checker": "board_runtime",
      "errors": [],
      "evidence_phase": "downstream_gate_declared",
      "execution_status": "not_run_required_downstream",
      "status": "pending_downstream",
      "summary": "board runtime evidence is required for final closure and is not claimed by Stage 6"
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
        "description": "One checker-bound semantic aggregate reconciles all operator-leaf simulator, golden, real-weight-consumption, and immutable identity evidence before promotion.",
        "name": "case_operator_leaf_semantic_evidence",
        "required": true
      },
      {
        "description": "A reproducible testbench/RTL scaffold loads declared manifests and is hashable before functional simulation.",
        "name": "case_tb_scaffold",
        "required": true
      },
      {
        "description": "Verified leaf modules are merged into one transformer layer/block kernel before multilayer or board wrapper gates.",
        "name": "single_transformer_layer",
        "required": true
      },
      {
        "description": "A single transformer layer/block kernel passes real functional verification before multi-layer pipeline verification.",
        "name": "case_single_layer_functional",
        "required": true
      },
      {
        "description": "The single transformer layer/block has golden comparison or declared numeric-tolerance evidence.",
        "name": "case_single_layer_golden_compare",
        "required": true
      },
      {
        "description": "One checker-bound semantic aggregate reconciles the connected single-layer simulator, golden, weight-consumption, and immutable identity evidence before promoti...<len=163>",
        "name": "case_single_layer_semantic_evidence",
        "required": true
      },
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
      },
      {
        "description": "One board semantic aggregate reconciles the canonical run, exact wrapper identity, all third-layer classifiers, real weights, and target-model output before bac...<len=173>",
        "name": "case_board_semantic_evidence",
        "required": true
      },
      {
        "description": "Vivado synthesis evidence is collected for the runtime/board shell target.",
        "name": "case_vivado_synthesis",
        "required": true
      },
      {
        "description": "Vivado implementation, timing, route, and DRC evidence are collected before runtime bitstream promotion.",
        "name": "case_vivado_implementation",
        "required": true
      },
      {
        "description": "Runtime ABI, DDR layout, register map, and bitstream artifacts are cross-checked before board runtime.",
        "name": "case_runtime_abi_check",
        "required": true
      },
      {
        "description": "Vivado produces a board-runtime case bitstream, not only a standalone core bitstream.",
        "name": "case_runtime_bitstream",
        "required": true
      },
      {
        "description": "Board runtime executes the generated bitstream with real packed inputs/weights and emits valid output bytes; liveness-only smoke is not final acceptance.",
        "name": "board_runtime",
        "required": true
      }
    ],
    "maturity_contract": {
      "levels": [
        {
          "debug_layer": "operator_leaf_modules",
          "id": "operator_leaf_functional",
          "required_before": "single_transformer_layer_kernel",
          "required_gates": {
            "_size": 8,
            "_type": "list"
          },
          "required_tool_roles": {
            "_size": 8,
            "_type": "list"
          }
        },
        {
          "debug_layer": "single_transformer_layer_kernel",
          "id": "single_layer_functional",
          "required_before": "board_axi_ddr_wrapped_system",
          "required_gates": {
            "_size": 5,
            "_type": "list"
          },
          "required_tool_roles": {
            "_size": 4,
            "_type": "list"
          }
        },
        {
          "debug_layer": "board_axi_ddr_wrapped_system",
          "id": "multilayer_pipeline_functional",
          "note": "Third-layer internal view: multi-layer ordering and liveness are derived from the real board-wrapped simulator evidence.",
          "required_before": "board_axi_ddr_wrapped_system_promotion",
          "required_gates": {
            "_size": 4,
            "_type": "list"
          },
          "required_tool_roles": {
            "_size": 5,
            "_type": "list"
          }
        },
        {
          "debug_layer": "board_axi_ddr_wrapped_system",
          "id": "axi_ddr_functional",
          "note": "Third-layer internal view: AXI/DDR protocol and transfers are derived from the same real board-wrapped simulator evidence before backend promotion.",
          "required_before": "backend_board",
          "required_gates": {
            "_size": 6,
            "_type": "list"
          },
          "required_tool_roles": {
            "_size": 8,
            "_type": "list"
          }
        },
        {
          "id": "contract_guided_debug_closure",
          "required_before": "repair_or_backend_handoff",
          "required_gates": {
            "_size": 1,
            "_type": "list"
          },
          "required_tool_roles": {
            "_size": 4,
            "_type": "list"
          }
        }
      ],
      "promotion_rule": "A later verification layer may not execute or promote until every earlier layer has pass evidence. That pass evidence is reusable but not absolute: a current-layer CCTG/boundary tr...<len=348>",
      "schema_version": "spatialaccagent.hierarchical_verification_maturity.v0"
    },
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
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
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
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
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
          "case_single_layer_golden_compare",
          "case_single_layer_semantic_evidence"
        ],
        "role": "single block merge agent"
      },
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
      },
      {
        "depends_on": [
          "merge.axi_ddr_runtime"
        ],
        "id": "merge.runtime_bitstream",
        "required_evidence": [
          "case_vivado_synthesis",
          "case_vivado_implementation",
          "case_runtime_bitstream",
          "case_runtime_abi_check",
          "board_runtime"
        ],
        "role": "runtime bitstream and board agent"
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
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
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
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence"
        ],
        "stage_id": "stage_02_residual_add_1"
      },
      {
        "id": "verify.stage_03_rms_norm_2",
        "kind": "norm",
        "module_checks": [
          "RMSNorm",
          "VectorNorm"
        ],
        "op": "rms_norm_2",
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
        "stage_id": "stage_03_rms_norm_2"
      },
      {
        "id": "verify.stage_04_mlp_gate_proj",
        "kind": "mlp",
        "module_checks": [
          "GatedMLP.gate:Linear"
        ],
        "op": "mlp_gate_proj",
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
        "stage_id": "stage_04_mlp_gate_proj"
      },
      {
        "id": "verify.stage_05_mlp_up_proj",
        "kind": "mlp",
        "module_checks": [
          "GatedMLP.up:Linear"
        ],
        "op": "mlp_up_proj",
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
        "stage_id": "stage_05_mlp_up_proj"
      },
      {
        "id": "verify.stage_06_activation_mul",
        "kind": "activation",
        "module_checks": [
          "GatedMLP.act:Activation",
          "GatedMLP.mul:ElementwiseMul"
        ],
        "op": "activation_mul",
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
        "stage_id": "stage_06_activation_mul"
      },
      {
        "id": "verify.stage_07_mlp_down_proj",
        "kind": "mlp",
        "module_checks": [
          "GatedMLP.down:Linear"
        ],
        "op": "mlp_down_proj",
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
        "stage_id": "stage_07_mlp_down_proj"
      },
      {
        "id": "verify.stage_08_residual_add_2",
        "kind": "residual",
        "module_checks": [
          "ResidualAdd",
          "Queue"
        ],
        "op": "residual_add_2",
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
        "stage_id": "stage_08_residual_add_2"
      }
    ],
    "strategy": "three_layer_repair_loop: operator_leaf_modules -> single_transformer_layer_kernel -> board_axi_ddr_wrapped_system"
  },
  "parameter_bindings": [
    {
      "legality_errors": [],
      "op": "rms_norm_1",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "eps": 1e-06,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16
      },
      "stage_id": "stage_00_rms_norm_1",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "legality_errors": [],
      "op": "self_attention",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "head_dim": 64,
        "hidden_size": 896,
        "input_bits": 16,
        "lanes": 8,
        "num_kv_heads": 2,
        "num_q_heads": 14,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "seq_len": 16
      },
      "stage_id": "stage_01_self_attention",
      "status": "ready",
      "template_id": "attention"
    },
    {
      "legality_errors": [],
      "op": "residual_add_1",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 32,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32
      },
      "stage_id": "stage_02_residual_add_1",
      "status": "ready",
      "template_id": "residual"
    },
    {
      "legality_errors": [],
      "op": "rms_norm_2",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "eps": 1e-06,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16
      },
      "stage_id": "stage_03_rms_norm_2",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "legality_errors": [],
      "op": "mlp_gate_proj",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 16,
        "intermediate_size": 4864,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "tile_k": 128,
        "tile_m": 16,
        "tile_n": 128
      },
      "stage_id": "stage_04_mlp_gate_proj",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "legality_errors": [],
      "op": "mlp_up_proj",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 16,
        "intermediate_size": 4864,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16,
        "tile_k": 128,
        "tile_m": 16,
        "tile_n": 128
      },
      "stage_id": "stage_05_mlp_up_proj",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "legality_errors": [],
      "op": "activation_mul",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 4864,
        "input_bits": 16,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 16
      },
      "stage_id": "stage_06_activation_mul",
      "status": "ready",
      "template_id": "elementwise"
    },
    {
      "legality_errors": [],
      "op": "mlp_down_proj",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 16,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 16,
        "intermediate_size": 4864,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32,
        "tile_k": 128,
        "tile_m": 16,
        "tile_n": 128
      },
      "stage_id": "stage_07_mlp_down_proj",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "legality_errors": [],
      "op": "residual_add_2",
      "params": {
        "clock_target_mhz": 0,
        "elem_bits": 32,
        "fifo_depth": 16,
        "hidden_size": 896,
        "input_bits": 32,
        "lanes": 8,
        "numeric_policy_id": "current_run_numeric_policy.md",
        "output_bits": 32
      },
      "stage_id": "stage_08_residual_add_2",
      "status": "ready",
      "template_id": "residual"
    }
  ],
  "schema_version": "spatialaccagent.verification_artifacts_review.v0",
  "stage": "verification_artifacts",
  "stage_gate_policy": {
    "current_certificate_validation": {
      "evidence_contract_version": "spatialaccagent.real_weight_semantic_evidence.v2",
      "policy": "Artifact presence is not certificate validity. Reuse is allowed only when the current validator returns current_contract_valid=true.",
      "schema_version": "spatialaccagent.current_certificate_validation_summary.v0",
      "scopes": [
        {
          "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "operator_leaf_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage7.single_layer_promotion_certificate",
          "artifact_present": false,
          "current_contract_valid": false,
          "producer_transition": null,
          "reuse_allowed": false,
          "scope": "single_layer_closure",
          "trust_status": null,
          "validation_status": "missing_or_stale_for_current_contract"
        },
        {
          "artifact_id": "artifact.stage7.board_axi_ddr_promotion_certificate",
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
  "system_test_policy": "required_before_backend_board",
  "template_source_checks": [
    {
      "checker": "stage5_template_source_manifest_check",
      "errors": [],
      "evidence_phase": null,
      "execution_status": null,
      "status": "pass",
      "summary": {
        "selected_operator_template_sources_count": 8,
        "template_sources_count": 14
      }
    }
  ],
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
    "evidence_path_requirements_summary": {
      "count": 36,
      "gate_names": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "boundary_contract_check",
        "leaf_stage.stage_00_rms_norm_1",
        "leaf_stage.stage_01_self_attention",
        "leaf_stage.stage_02_residual_add_1",
        "leaf_stage.stage_03_rms_norm_2",
        "leaf_stage.stage_04_mlp_gate_proj",
        "leaf_stage.stage_05_mlp_up_proj",
        "leaf_stage.stage_06_activation_mul",
        "leaf_stage.stage_07_mlp_down_proj",
        "leaf_stage.stage_08_residual_add_2",
        "case_stage_leaf_static",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence",
        "case_tb_scaffold",
        "single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "case_single_layer_semantic_evidence",
        "case_board_interface_discovery",
        "case_multilayer_pipeline",
        "case_axi_ddr_interface",
        "functional_sim",
        "case_multilayer_functional",
        "case_pipeline_deadlock_check",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_board_semantic_evidence",
        "case_vivado_synthesis",
        "case_vivado_implementation",
        "case_runtime_bitstream",
        "case_runtime_abi_check",
        "board_runtime"
      ],
      "phases": [
        "axi_protocol_check",
        "board_interface_discovery",
        "board_runtime",
        "board_semantic_aggregate",
        "board_wrapper_interface",
        "ddr_image_roundtrip",
        "debug_boundary_contract",
        "functional_simulation",
        "multilayer_deadlock_liveness",
        "multilayer_functional",
        "multilayer_pipeline",
        "operator_leaf_aggregate",
        "operator_leaf_functional",
        "operator_leaf_golden_compare",
        "operator_leaf_module",
        "operator_leaf_semantic_aggregate",
        "real_weight_catalog",
        "runtime_abi",
        "semantic_testbench_generation",
        "single_layer_functional",
        "single_layer_golden_compare",
        "single_layer_kernel",
        "single_layer_semantic_aggregate",
        "target_model_reference",
        "testbench_scaffold",
        "vivado_bitstream",
        "vivado_implementation",
        "vivado_synthesis"
      ]
    },
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
    "required_evidence_gate_names": [
      "case_real_weight_artifacts",
      "case_target_model_reference",
      "case_semantic_testbench",
      "case_stage_leaf_static",
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_tb_scaffold",
      "single_transformer_layer",
      "case_single_layer_functional",
      "case_single_layer_golden_compare",
      "case_single_layer_semantic_evidence",
      "case_board_interface_discovery",
      "case_multilayer_pipeline",
      "case_axi_ddr_interface",
      "functional_sim",
      "case_multilayer_functional",
      "case_pipeline_deadlock_check",
      "case_axi_protocol_check",
      "case_ddr_image_roundtrip",
      "case_board_semantic_evidence",
      "case_vivado_synthesis",
      "case_vivado_implementation",
      "case_runtime_abi_check",
      "case_runtime_bitstream",
      "board_runtime"
    ],
    "required_generated_artifacts": [
      {
        "exists": true,
        "name": "generated_code_package",
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel"
      },
      {
        "exists": true,
        "name": "memory_layout",
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/memory/memory_layout.json"
      },
      {
        "exists": true,
        "name": "runtime_config",
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/runtime/runtime_config.json"
      }
    ],
    "required_tool_protocols": [
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_weight_manifest_generate",
        "name": "case_weight_manifest_generate",
        "planned_consumes_count": 1,
        "planned_produces_count": 4,
        "produces_count": 2,
        "required": true,
        "role": "weight_manifest_generate",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 4,
        "evidence_status": "required_pending_execution",
        "kind": "target_model_reference_generate",
        "name": "case_target_model_reference",
        "planned_consumes_count": 4,
        "planned_produces_count": 7,
        "produces_count": 7,
        "required": true,
        "role": "target_model_reference_generate",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 4,
        "evidence_status": "required_pending_execution",
        "kind": "semantic_testbench_generate",
        "name": "case_semantic_testbench",
        "planned_consumes_count": 4,
        "planned_produces_count": 5,
        "produces_count": 5,
        "required": true,
        "role": "semantic_testbench_generate",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_tb_scaffold_generate",
        "name": "case_tb_scaffold_generate",
        "planned_consumes_count": 4,
        "planned_produces_count": 4,
        "produces_count": 3,
        "required": true,
        "role": "tb_scaffold_generate",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 4,
        "evidence_status": "required_pending_execution",
        "kind": "case_tb_scaffold",
        "name": "case_tb_scaffold",
        "planned_consumes_count": 4,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "tb_scaffold",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 1,
        "evidence_status": "required_pending_execution",
        "kind": "case_stage_leaf_static",
        "name": "case_stage_leaf_static",
        "planned_consumes_count": 2,
        "planned_produces_count": 1,
        "produces_count": 0,
        "required": true,
        "role": "stage_leaf_static",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 2,
        "evidence_status": "required_pending_execution",
        "kind": "boundary_contract_check",
        "name": "boundary_contract_check",
        "planned_consumes_count": 2,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "boundary_contract_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 6,
        "evidence_status": "required_pending_execution",
        "kind": "case_leaf_functional",
        "name": "case_leaf_functional",
        "planned_consumes_count": 6,
        "planned_produces_count": 3,
        "produces_count": 3,
        "required": true,
        "role": "leaf_functional_sim",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 6,
        "evidence_status": "required_pending_execution",
        "kind": "case_leaf_golden_compare",
        "name": "case_leaf_golden_compare",
        "planned_consumes_count": 6,
        "planned_produces_count": 3,
        "produces_count": 3,
        "required": true,
        "role": "leaf_golden_compare",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 6,
        "evidence_status": "required_pending_execution",
        "kind": "semantic_evidence_assemble",
        "name": "case_operator_leaf_semantic_evidence",
        "planned_consumes_count": 6,
        "planned_produces_count": 2,
        "produces_count": 2,
        "required": true,
        "role": "operator_leaf_semantic_evidence",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_real_weight_artifacts",
        "name": "case_real_weight_artifacts",
        "planned_consumes_count": 1,
        "planned_produces_count": 4,
        "produces_count": 2,
        "required": true,
        "role": "real_weight_artifacts",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 5,
        "evidence_status": "required_pending_execution",
        "kind": "case_single_transformer_layer",
        "name": "case_single_transformer_layer",
        "planned_consumes_count": 5,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "single_layer_kernel",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 7,
        "evidence_status": "required_pending_execution",
        "kind": "case_single_layer_functional",
        "name": "case_single_layer_functional",
        "planned_consumes_count": 7,
        "planned_produces_count": 4,
        "produces_count": 4,
        "required": true,
        "role": "single_layer_functional_sim",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 4,
        "evidence_status": "required_pending_execution",
        "kind": "case_single_layer_golden_reference_builder",
        "name": "case_single_layer_golden_reference_builder",
        "planned_consumes_count": 0,
        "planned_produces_count": 0,
        "produces_count": 3,
        "required": true,
        "role": "single_layer_golden_reference_builder",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 8,
        "evidence_status": "required_pending_execution",
        "kind": "case_single_layer_golden_compare",
        "name": "case_single_layer_golden_compare",
        "planned_consumes_count": 8,
        "planned_produces_count": 3,
        "produces_count": 3,
        "required": true,
        "role": "single_layer_golden_compare",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 5,
        "evidence_status": "required_pending_execution",
        "kind": "semantic_evidence_assemble",
        "name": "case_single_layer_semantic_evidence",
        "planned_consumes_count": 5,
        "planned_produces_count": 2,
        "produces_count": 2,
        "required": true,
        "role": "single_layer_semantic_evidence",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_multilayer_pipeline",
        "name": "case_multilayer_pipeline",
        "planned_consumes_count": 4,
        "planned_produces_count": 1,
        "produces_count": 0,
        "required": true,
        "role": "multilayer_pipeline",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_multilayer_functional",
        "name": "case_multilayer_functional",
        "planned_consumes_count": 0,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "multilayer_functional_sim",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_pipeline_deadlock_check",
        "name": "case_pipeline_deadlock_check",
        "planned_consumes_count": 0,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "pipeline_deadlock_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_board_interface_discovery",
        "name": "case_board_interface_discovery",
        "planned_consumes_count": 2,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "board_interface_discovery",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_axi_ddr_interface",
        "name": "case_axi_ddr_interface",
        "planned_consumes_count": 2,
        "planned_produces_count": 1,
        "produces_count": 0,
        "required": true,
        "role": "axi_ddr_interface",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_axi_protocol_check",
        "name": "case_axi_protocol_check",
        "planned_consumes_count": 0,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "axi_protocol_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 3,
        "evidence_status": "required_pending_execution",
        "kind": "case_ddr_image_roundtrip",
        "name": "case_ddr_image_roundtrip",
        "planned_consumes_count": 3,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "ddr_image_roundtrip",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 6,
        "evidence_status": "required_pending_execution",
        "kind": "vcs_real_functional_sim",
        "name": "case_vcs_functional_sim",
        "planned_consumes_count": 0,
        "planned_produces_count": 0,
        "produces_count": 1,
        "required": true,
        "role": "vcs_functional_sim",
        "scope": "remote"
      },
      {
        "configured": true,
        "consumes_count": 2,
        "evidence_status": "required_pending_execution",
        "kind": "vcs_evidence_analyzer",
        "name": "case_vcs_evidence_analyzer",
        "planned_consumes_count": 0,
        "planned_produces_count": 0,
        "produces_count": 1,
        "required": true,
        "role": "vcs_evidence_analyzer",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 6,
        "evidence_status": "required_pending_execution",
        "kind": "case_deadlock_axi_check",
        "name": "case_deadlock_axi_check",
        "planned_consumes_count": 0,
        "planned_produces_count": 0,
        "produces_count": 1,
        "required": true,
        "role": "deadlock_axi_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 7,
        "evidence_status": "required_pending_execution",
        "kind": "semantic_evidence_assemble",
        "name": "case_board_semantic_evidence",
        "planned_consumes_count": 7,
        "planned_produces_count": 2,
        "produces_count": 2,
        "required": true,
        "role": "board_semantic_evidence",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 1,
        "evidence_status": "required_pending_execution",
        "kind": "vivado_synthesis",
        "name": "case_vivado_synthesis",
        "planned_consumes_count": 3,
        "planned_produces_count": 3,
        "produces_count": 1,
        "required": true,
        "role": "vivado_synthesis",
        "scope": "remote"
      },
      {
        "configured": true,
        "consumes_count": 3,
        "evidence_status": "required_pending_execution",
        "kind": "vivado_report_check",
        "name": "case_vivado_synthesis_report_check",
        "planned_consumes_count": 0,
        "planned_produces_count": 0,
        "produces_count": 1,
        "required": true,
        "role": "vivado_synthesis_report_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 1,
        "evidence_status": "required_pending_execution",
        "kind": "vivado_implementation",
        "name": "case_vivado_implementation",
        "planned_consumes_count": 1,
        "planned_produces_count": 3,
        "produces_count": 1,
        "required": true,
        "role": "vivado_implementation",
        "scope": "remote"
      },
      {
        "configured": true,
        "consumes_count": 5,
        "evidence_status": "required_pending_execution",
        "kind": "vivado_report_check",
        "name": "case_vivado_implementation_report_check",
        "planned_consumes_count": 0,
        "planned_produces_count": 0,
        "produces_count": 1,
        "required": true,
        "role": "vivado_implementation_report_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 6,
        "evidence_status": "required_pending_execution",
        "kind": "case_runtime_abi_check",
        "name": "case_runtime_abi_check",
        "planned_consumes_count": 3,
        "planned_produces_count": 1,
        "produces_count": 1,
        "required": true,
        "role": "runtime_abi_check",
        "scope": "local"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "case_runtime_bitstream",
        "name": "case_runtime_bitstream",
        "planned_consumes_count": 3,
        "planned_produces_count": 4,
        "produces_count": 0,
        "required": true,
        "role": "runtime_bitstream",
        "scope": "remote"
      },
      {
        "configured": true,
        "consumes_count": 0,
        "evidence_status": "required_pending_execution",
        "kind": "board_runtime",
        "name": "board_runtime",
        "planned_consumes_count": 7,
        "planned_produces_count": 3,
        "produces_count": 0,
        "required": true,
        "role": "board_runtime",
        "scope": "board"
      }
    ],
    "schema_version": "spatialaccagent.verification_artifact_contract.v0",
    "status": "pass",
    "summary": "all verification artifact contracts are satisfiable",
    "verification_gate_dag": {
      "critical_nodes": [
        {
          "depends_on": [],
          "name": "case_real_weight_artifacts",
          "phase": "real_weight_catalog",
          "required_maturity": "operator_leaf_functional"
        },
        {
          "depends_on": [
            "case_real_weight_artifacts"
          ],
          "name": "case_target_model_reference",
          "phase": "target_model_reference",
          "required_maturity": "operator_leaf_functional"
        },
        {
          "depends_on": [
            "case_target_model_reference"
          ],
          "name": "case_semantic_testbench",
          "phase": "semantic_testbench_generation",
          "required_maturity": "operator_leaf_functional"
        },
        {
          "depends_on": [],
          "name": "boundary_contract_check",
          "phase": "debug_boundary_contract",
          "required_maturity": "contract_guided_debug_closure"
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
            "leaf_stage.stage_07_mlp_down_proj"
          ],
          "name": "case_stage_leaf_static",
          "phase": "operator_leaf_aggregate",
          "required_maturity": "operator_leaf_functional"
        },
        {
          "depends_on": [
            "case_stage_leaf_static",
            "boundary_contract_check",
            "case_semantic_testbench"
          ],
          "name": "case_leaf_functional",
          "phase": "operator_leaf_functional",
          "required_maturity": "operator_leaf_functional"
        },
        {
          "depends_on": [
            "case_leaf_functional",
            "boundary_contract_check",
            "case_target_model_reference",
            "case_semantic_testbench"
          ],
          "name": "case_leaf_golden_compare",
          "phase": "operator_leaf_golden_compare",
          "required_maturity": "operator_leaf_functional"
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
          "name": "case_operator_leaf_semantic_evidence",
          "phase": "operator_leaf_semantic_aggregate",
          "required_maturity": "operator_leaf_functional"
        },
        {
          "depends_on": [
            "case_operator_leaf_semantic_evidence",
            "case_semantic_testbench"
          ],
          "name": "case_tb_scaffold",
          "phase": "testbench_scaffold",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_operator_leaf_semantic_evidence",
            "case_tb_scaffold",
            "case_semantic_testbench"
          ],
          "name": "single_transformer_layer",
          "phase": "single_layer_kernel",
          "required_maturity": "single_layer_functional"
        },
        {
          "depends_on": [
            "single_transformer_layer",
            "case_operator_leaf_semantic_evidence",
            "case_tb_scaffold",
            "case_semantic_testbench"
          ],
          "name": "case_single_layer_functional",
          "phase": "single_layer_functional",
          "required_maturity": "single_layer_functional"
        },
        {
          "depends_on": [
            "case_single_layer_functional"
          ],
          "name": "case_single_layer_golden_compare",
          "phase": "single_layer_golden_compare",
          "required_maturity": "single_layer_functional"
        },
        {
          "depends_on": [
            "case_single_layer_golden_compare",
            "case_single_layer_functional",
            "case_operator_leaf_semantic_evidence",
            "case_target_model_reference",
            "case_semantic_testbench"
          ],
          "name": "case_single_layer_semantic_evidence",
          "phase": "single_layer_semantic_aggregate",
          "required_maturity": "single_layer_functional"
        },
        {
          "depends_on": [
            "case_single_layer_semantic_evidence"
          ],
          "name": "case_board_interface_discovery",
          "phase": "board_interface_discovery",
          "required_maturity": "axi_ddr_functional"
        },
        {
          "depends_on": [
            "case_single_layer_semantic_evidence",
            "case_semantic_testbench",
            "case_board_interface_discovery"
          ],
          "name": "case_multilayer_pipeline",
          "phase": "multilayer_pipeline",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_multilayer_pipeline",
            "case_board_interface_discovery"
          ],
          "name": "case_axi_ddr_interface",
          "phase": "board_wrapper_interface",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_semantic_testbench",
            "case_single_layer_semantic_evidence",
            "case_multilayer_pipeline",
            "case_board_interface_discovery",
            "case_axi_ddr_interface"
          ],
          "name": "functional_sim",
          "phase": "functional_simulation",
          "required_maturity": null
        },
        {
          "depends_on": [
            "functional_sim",
            "case_multilayer_pipeline"
          ],
          "name": "case_multilayer_functional",
          "phase": "multilayer_functional",
          "required_maturity": "multilayer_pipeline_functional"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_multilayer_functional"
          ],
          "name": "case_pipeline_deadlock_check",
          "phase": "multilayer_deadlock_liveness",
          "required_maturity": "multilayer_pipeline_functional"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_axi_ddr_interface",
            "case_board_interface_discovery"
          ],
          "name": "case_axi_protocol_check",
          "phase": "axi_protocol_check",
          "required_maturity": "axi_ddr_functional"
        },
        {
          "depends_on": [
            "functional_sim",
            "case_axi_protocol_check",
            "case_real_weight_artifacts"
          ],
          "name": "case_ddr_image_roundtrip",
          "phase": "ddr_image_roundtrip",
          "required_maturity": "axi_ddr_functional"
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
            "case_target_model_reference"
          ],
          "name": "case_board_semantic_evidence",
          "phase": "board_semantic_aggregate",
          "required_maturity": "axi_ddr_functional"
        },
        {
          "depends_on": [
            "case_multilayer_pipeline",
            "case_board_interface_discovery",
            "case_axi_ddr_interface",
            "functional_sim",
            "case_multilayer_functional",
            "case_pipeline_deadlock_check",
            "case_axi_protocol_check",
            "case_ddr_image_roundtrip"
          ],
          "name": "case_vivado_synthesis",
          "phase": "vivado_synthesis",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_vivado_synthesis"
          ],
          "name": "case_vivado_implementation",
          "phase": "vivado_implementation",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_vivado_implementation",
            "functional_sim",
            "case_axi_ddr_interface",
            "case_multilayer_pipeline"
          ],
          "name": "case_runtime_bitstream",
          "phase": "vivado_bitstream",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_runtime_bitstream"
          ],
          "name": "case_runtime_abi_check",
          "phase": "runtime_abi",
          "required_maturity": null
        },
        {
          "depends_on": [
            "case_runtime_bitstream",
            "case_runtime_abi_check",
            "functional_sim",
            "case_real_weight_artifacts"
          ],
          "name": "board_runtime",
          "phase": "board_runtime",
          "required_maturity": null
        }
      ],
      "leaf_node_count": 9,
      "node_count": 36,
      "phase_order": [
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
        "vivado_synthesis",
        "vivado_implementation",
        "vivado_bitstream",
        "runtime_abi",
        "board_runtime"
      ],
      "policy": {
        "_more_keys": 18,
        "all_gate_tool_roles_must_pass": true,
        "backend_discovery_before_vivado_bitstream": true,
        "backend_requires_all_third_layer_subgates": true,
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
        "hierarchical_order": {
          "_size": 27,
          "_type": "list"
        },
        "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
        "layer1_operator_leaf_closure": {
          "_size": 8,
          "_type": "list"
        }
      }
    },
    "warnings": []
  }
}
</candidate_stage_artifact>

<reference_subtask_plan_if_split_is_needed>
[
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_00_rms_norm_1",
      "op:rms_norm_1",
      "kind:norm",
      "module:RMSNorm"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_00_rms_norm_1_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_00_rms_norm_1 stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_00_rms_norm_1 leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_01_self_attention",
      "op:self_attention",
      "kind:attention",
      "module:QKVProjection"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_01_self_attention_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_01_self_attention stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_01_self_attention leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_02_residual_add_1",
      "op:residual_add_1",
      "kind:residual",
      "module:ResidualAdd"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_02_residual_add_1_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_02_residual_add_1 stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_02_residual_add_1 leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_03_rms_norm_2",
      "op:rms_norm_2",
      "kind:norm",
      "module:RMSNorm"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_03_rms_norm_2_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_03_rms_norm_2 stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_03_rms_norm_2 leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_04_mlp_gate_proj",
      "op:mlp_gate_proj",
      "kind:mlp",
      "module:GatedMLP.gate:Linear"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_04_mlp_gate_proj_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_04_mlp_gate_proj stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_04_mlp_gate_proj leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_05_mlp_up_proj",
      "op:mlp_up_proj",
      "kind:mlp",
      "module:GatedMLP.up:Linear"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_05_mlp_up_proj_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_05_mlp_up_proj stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_05_mlp_up_proj leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_06_activation_mul",
      "op:activation_mul",
      "kind:activation",
      "module:GatedMLP.act:Activation"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_06_activation_mul_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_06_activation_mul stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_06_activation_mul leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_07_mlp_down_proj",
      "op:mlp_down_proj",
      "kind:mlp",
      "module:GatedMLP.down:Linear"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_07_mlp_down_proj_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_07_mlp_down_proj stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_07_mlp_down_proj leaf stage"
  },
  {
    "acceptance_checkers": [
      "boundary_contract_check",
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_real_weight_artifacts",
      "case_semantic_testbench"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "stage_id:stage_08_residual_add_2",
      "op:residual_add_2",
      "kind:residual",
      "module:ResidualAdd"
    ],
    "constraints": [
      "constraint.verification.hierarchy",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.beat.pipeline"
    ],
    "id": "verification_artifacts.stage_08_residual_add_2_stage_verification_engineer",
    "objective": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT binding, generated semantic testbench, resolved numeric compar...<len=433>",
    "parallel_group": 0,
    "role": "stage_08_residual_add_2 stage verification engineer",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 6,
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
      "mission": "Validate one case-adapter pipeline leaf stage before merge: target-model operator semantics, complete real-weight DUT bi...<len=433>",
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
    "title": "Validate stage_08_residual_add_2 leaf stage"
  },
  {
    "acceptance_checkers": [
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_semantic_testbench",
      "case_stage_leaf_static",
      "case_target_model_reference"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "merge_id:merge.self_attention",
      "depends_on:stage_00_rms_norm_1",
      "depends_on:stage_01_self_attention",
      "depends_on:stage_02_residual_add_1"
    ],
    "constraints": [
      "constraint.beat.pipeline",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.tool.protocols"
    ],
    "id": "verification_artifacts.self_attention_merge_agent",
    "objective": "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop hierarchy as operator leaf modules, single transformer-layer kernel, then board AXI/DDR wrapped sys...<len=314>",
    "parallel_group": 1,
    "role": "self-attention merge agent",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 5,
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
      "mission": "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop hierarchy as operator leaf modules, sin...<len=314>",
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
    "title": "Validate merge.self_attention merge gate"
  },
  {
    "acceptance_checkers": [
      "case_leaf_functional",
      "case_leaf_golden_compare",
      "case_operator_leaf_semantic_evidence",
      "case_semantic_testbench",
      "case_stage_leaf_static",
      "case_target_model_reference"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "merge_id:merge.mlp",
      "depends_on:stage_03_rms_norm_2",
      "depends_on:stage_04_mlp_gate_proj",
      "depends_on:stage_05_mlp_up_proj"
    ],
    "constraints": [
      "constraint.beat.pipeline",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.tool.protocols"
    ],
    "id": "verification_artifacts.mlp_merge_agent",
    "objective": "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop hierarchy as operator leaf modules, single transformer-layer kernel, then board AXI/DDR wrapped sys...<len=314>",
    "parallel_group": 1,
    "role": "MLP merge agent",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 5,
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
      "mission": "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop hierarchy as operator leaf modules, sin...<len=314>",
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
    "title": "Validate merge.mlp merge gate"
  },
  {
    "acceptance_checkers": [
      "case_real_weight_artifacts",
      "case_semantic_testbench",
      "case_single_layer_functional",
      "case_single_layer_golden_compare",
      "case_single_layer_semantic_evidence",
      "case_target_model_reference"
    ],
    "action_type": "evidence_and_repair_review",
    "artifact_focus": [
      "merge_id:merge.single_decoder_block",
      "depends_on:merge.self_attention",
      "depends_on:merge.mlp",
      "evidence:case_real_weight_artifacts"
    ],
    "constraints": [
      "constraint.beat.pipeline",
      "constraint.pipeline.structure",
      "constraint.stream.order",
      "constraint.tool.protocols"
    ],
    "id": "verification_artifacts.single_block_merge_agent",
    "objective": "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop hierarchy as operator leaf modules, single transformer-layer kernel, then board AXI/DDR wrapped sys...<len=314>",
    "parallel_group": 2,
    "role": "single block merge agent",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 5,
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
      "mission": "Validate the assigned chip-design-team merge boundary. Keep the main repair-loop hierarchy as operator leaf modules, sin...<len=314>",
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
    "title": "Validate merge.single_decoder_block merge gate"
  },
  {
    "_more_subtasks": 5
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
