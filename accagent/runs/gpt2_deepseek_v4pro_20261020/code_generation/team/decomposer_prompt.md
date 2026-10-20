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
code_generation
</stage>

<objective>
Generate and audit a template-bound accelerator code package from SACG.
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
  "compile_gate": {
    "cwd": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel",
    "elaboration_enabled": true,
    "enabled": true,
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/compile_check.json",
    "returncode": 0,
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
        "status": "pass",
        "stderr_tail": "[info] [launcher] getting org.scala-sbt sbt 1.9.7  (this may take some time)...\n[info] [launcher] getting Scala 2.12.18 ...<len=133>",
        "stdout_tail": "copying runtime jar...\n[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] ...<len=720>"
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
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for pr...<len=652>"
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
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for pr...<len=579>"
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
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for pr...<len=577>"
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
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for pr...<len=585>"
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
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for pr...<len=583>"
      }
    ],
    "summary": "completed 6 compile/elaboration command(s)"
  },
  "constraints_touched": [
    "constraint.codegen.package",
    "constraint.codegen.compile_gate",
    "constraint.codegen.contract_check",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.deployment.board"
  ],
  "contract_check": {
    "checked_contracts": [
      "upstream_transition_status",
      "model_shape_to_generated_params",
      "stage3_implementation_contract_to_generated_top",
      "numeric_policy_to_generated_bits",
      "template_provenance_hashes",
      "mandatory_fpga_ip_binding",
      "simulation_implementation_ip_timing_identity",
      "compiled_generated_ddr_tile_service_abi",
      "compile_and_elaboration_warning_free",
      "memory_layout_alignment_nonoverlap",
      "runtime_config_consistency",
      "parameter_binding_legality"
    ],
    "checker": "codegen_contract_check",
    "errors": [],
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/codegen_contract_check.json",
    "status": "pass",
    "summary": "all code generation contracts passed",
    "warnings": []
  },
  "generated_files": [
    "generated/chisel/Activation.sv",
    "generated/chisel/Attention.sv",
    "generated/chisel/DenseFFN.sv",
    "generated/chisel/GPT2PreLNBlock.sv",
    "generated/chisel/GeneratedAcceleratorTop.sv",
    "generated/chisel/GeneratedAxiDdrTop.sv",
    "generated/chisel/IntegerAttention.sv",
    "generated/chisel/IntegerVectorNorm.sv",
    "generated/chisel/Linear.sv",
    "generated/chisel/Linear_1.sv",
    "generated/chisel/Linear_2.sv",
    "generated/chisel/Linear_3.sv",
    "generated/chisel/PhysicalIntegerSqrt.sv",
    "generated/chisel/PhysicalLinearAdd.sv",
    "generated/chisel/PhysicalLinearMul.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_12.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_14.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_15.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_16.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_17.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_2.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_25.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_28.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_3.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_32.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_36.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_4.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_5.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_6.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_7.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_8.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_9.sv",
    "generated/chisel/PhysicalStreamFifo.sv",
    "generated/chisel/PhysicalStreamFifo_3.sv",
    "generated/chisel/PhysicalStreamFifo_7.sv",
    "generated/chisel/QKVProjection.sv",
    "generated/chisel/README.md",
    "generated/chisel/ResidualAdd.sv",
    "generated/chisel/VectorNorm.sv",
    "generated/chisel/WeightTileCache.sv",
    "generated/chisel/WeightTileCache_1.sv",
    "generated/chisel/WeightTileCache_2.sv",
    "generated/chisel/WeightTileServiceMux.sv",
    "generated/chisel/build.sbt",
    "generated/chisel/filelist.f",
    "generated/chisel/logs/codegen_contract_check.json",
    "generated/chisel/logs/codegen_package_static_check.json",
    "generated/chisel/logs/compile_check.json",
    "generated/chisel/logs/dse_physical_binding_check.json",
    "generated/chisel/memory/memory_layout.json",
    "generated/chisel/project/build.properties",
    "generated/chisel/project/target/config-classes/$c9ee876ec3eb95f78e43$.class",
    "generated/chisel/project/target/config-classes/$c9ee876ec3eb95f78e43.cache",
    "generated/chisel/project/target/config-classes/$c9ee876ec3eb95f78e43.class",
    "generated/chisel/project/target/config-classes/$edbb0dd1284013ce9485$.class",
    "generated/chisel/project/target/config-classes/$edbb0dd1284013ce9485.cache",
    "generated/chisel/project/target/config-classes/$edbb0dd1284013ce9485.class",
    "generated/chisel/project/target/config-classes/$ee7405b860434bc224b5$.class",
    "generated/chisel/project/target/config-classes/$ee7405b860434bc224b5.cache",
    "generated/chisel/project/target/config-classes/$ee7405b860434bc224b5.class",
    "generated/chisel/project/target/scala-2.12/sbt-1.0/sync/copy-resource",
    "generated/chisel/project/target/scala-2.12/sbt-1.0/update/update_cache_2.12/inputs",
    "generated/chisel/project/target/scala-2.12/sbt-1.0/update/update_cache_2.12/output",
    "generated/chisel/project/target/streams/_global/_global/_global/streams/out",
    "generated/chisel/project/target/streams/_global/_global/csrLogger/_global/streams/out",
    "generated/chisel/project/target/streams/_global/csrConfiguration/_global/streams/out",
    "generated/chisel/project/target/streams/_global/csrProject/_global/streams/out",
    "generated/chisel/project/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.12/input_dsp",
    "generated/chisel/project/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.12/output_dsp",
    "generated/chisel/project/target/streams/_global/ivyConfiguration/_global/streams/out",
    "generated/chisel/project/target/streams/_global/ivySbt/_global/streams/out",
    "generated/chisel/project/target/streams/_global/moduleSettings/_global/streams/out",
    "generated/chisel/project/target/streams/_global/projectDescriptors/_global/streams/out",
    "generated/chisel/project/target/streams/_global/scalaCompilerBridgeScope/_global/streams/out",
    "generated/chisel/project/target/streams/_global/update/_global/streams/out",
    "generated/chisel/project/target/streams/compile/_global/_global/compileOutputs/previous",
    "generated/chisel/project/target/streams/compile/_global/_global/discoveredMainClasses/data",
    "generated/chisel/project/target/streams/compile/bspReporter/_global/streams/out",
    "generated/chisel/project/target/streams/compile/compile/_global/streams/out",
    "generated/chisel/project/target/streams/compile/compileIncremental/_global/streams/export",
    "generated/chisel/project/target/streams/compile/compileIncremental/_global/streams/out",
    "generated/chisel/project/target/streams/compile/copyResources/_global/streams/out",
    "generated/chisel/project/target/streams/compile/dependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/exportedProducts/_global/streams/export",
    "generated/chisel/project/target/streams/compile/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/incOptions/_global/streams/out",
    "generated/chisel/project/target/streams/compile/internalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/internalDependencyClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/compile/managedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/scalacOptions/_global/streams/out",
    "generated/chisel/project/target/streams/compile/unmanagedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/unmanagedClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/compile/unmanagedJars/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/dependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/exportedProducts/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/fullClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/internalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/internalDependencyClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/runtime/managedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/unmanagedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/unmanagedClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/runtime/unmanagedJars/_global/streams/export",
    "generated/chisel/runtime/runtime_config.json",
    "generated/chisel/scripts/compile_check.sh",
    "generated/chisel/scripts/elaborate.sh",
    "generated/chisel/simulation/fpga_ip_modules.txt",
    "generated/chisel/simulation/fpga_ip_simulation_closure.json",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.mem",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.memh",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.mem",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.memh",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/transcendental_approximation_contract.json",
    "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAcceleratorTop.scala",
    "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
    "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedContractCheck.scala",
    "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala",
    "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedSACGMetadata.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Activation.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Attention.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Common.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/DecoderBlock.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Elementwise.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/FFN.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/KVCache.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Linear.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Mask.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Norm.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/PhysicalResources.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/QKVProjection.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/RoPE.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Softmax.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/WeightTileCache.scala",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAcceleratorVivado$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAcceleratorVivado$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAcceleratorVivado.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTopVivado$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTopVivado$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTopVivado.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAcceleratorTop$$anon$1$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAcceleratorTop$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAcceleratorTop.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAxiDdrTop$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAxiDdrTop.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedContractCheck$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedContractCheck$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedContractCheck.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedDesignParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedDesignParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedSACGMetadata$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedSACGMetadata.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/exp2_fraction_q24.mem",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/exp2_fraction_q24.memh",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/sigmoid_pwl_q18.mem",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/sigmoid_pwl_q18.memh",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/transcendental_approximation_contract.json",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AccMath$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AccMath.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Activation$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Activation.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationGELUNew.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationGELUTanh.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationReLU.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationSiLU.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Attention$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Attention.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionGQA.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMHA.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMQA.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMask$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMask.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMaskParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMaskParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlock$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFN$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFN.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFNParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFNParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseMLP.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMul$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMul.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMulParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMulParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingAttention$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingAttention.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingRoPE$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingRoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingVectorNorm$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingVectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GPT2PreLNBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLP$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLP.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLPParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLPParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlock$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IeeeMath$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IeeeMath.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Int8QuantPorts.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerAttention$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerAttention.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerRoPE$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerRoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerSoftmax$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerSoftmax.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerVectorNorm$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerVectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCache$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCache.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCacheParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCacheParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Linear$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Linear.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearScaleMetadata.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearScalePorts.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlock$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/OPTPreLNBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ParametricLinearInt8ToFP32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ParametricLinearInt8ToInt8.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp16ToFp32$$anon$11.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp16ToFp32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Add.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32AddPipeline.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Binary$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Binary$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Binary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32CompareLt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Div.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Mul.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32MulPipeline.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Sqrt$$anon$8.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Sqrt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Sub.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToFp16$$anon$12.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToFp16.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToSigned$$anon$13.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToSigned.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFpLatency$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFpLatency.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalImplementation$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalImplementation.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalIntegerSqrt$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalIntegerSqrt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearAdd$$anon$6$$anon$7.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearAdd$$anon$6.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearAdd.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul$$anon$4$$anon$5.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul$$anon$4.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalMath$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalMath.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalRom$$anon$10.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalRom.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSignedToFp32$$anon$15.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSignedToFp32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSimpleDualPortMemory$$anon$17.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSimpleDualPortMemory.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalStreamFifo$$anon$18.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalStreamFifo.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalTaggedFp32Binary$$anon$2$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalTaggedFp32Binary$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalTaggedFp32Binary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalUIntToFp32$$anon$14.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalUIntToFp32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNorm$$anon$5.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjection$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjection.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjectionParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjectionParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjector.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVStreamBeat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Qwen2Block.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNorm$$anon$4.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormQ.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualAdd$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualAdd.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPE$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEApply.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Softmax$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Softmax.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/SoftmaxParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/SoftmaxParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StageConfig.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamBeat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamSpec$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamSpec.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/TaggedFp32Result.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNorm$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpBinary$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpBinary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpFloatToInt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpIntToFloat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpUnary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileCache$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileCache$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileCache.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileRequest.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileResponse$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileResponse.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceIO$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceIO.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceMux$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceMux$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceMux.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightWrite.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WideRefillParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSimpleDualPort$$anon$16.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSimpleDualPort.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSinglePortRom$$anon$9.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSinglePortRom.class",
    "generated/chisel/target/scala-2.13/spatialaccagent-generated_2.13-0.1.0.jar",
    "generated/chisel/target/scala-2.13/sync/copy-resource",
    "generated/chisel/target/scala-2.13/update/update_cache_2.13/inputs",
    "generated/chisel/target/scala-2.13/update/update_cache_2.13/output",
    "generated/chisel/target/scala-2.13/zinc/inc_compile_2.13.zip",
    "generated/chisel/target/streams/_global/_global/_global/streams/out",
    "generated/chisel/target/streams/_global/_global/csrLogger/_global/streams/out",
    "generated/chisel/target/streams/_global/csrConfiguration/_global/streams/out",
    "generated/chisel/target/streams/_global/csrProject/_global/streams/out",
    "generated/chisel/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.13/input_dsp",
    "generated/chisel/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.13/output_dsp",
    "generated/chisel/target/streams/_global/ivyConfiguration/_global/streams/out",
    "generated/chisel/target/streams/_global/ivySbt/_global/streams/out",
    "generated/chisel/target/streams/_global/moduleSettings/_global/streams/out",
    "generated/chisel/target/streams/_global/projectDescriptors/_global/streams/out",
    "generated/chisel/target/streams/_global/scalaCompilerBridgeScope/_global/streams/out",
    "generated/chisel/target/streams/_global/update/_global/streams/out",
    "generated/chisel/target/streams/compile/_global/_global/compileOutputs/previous",
    "generated/chisel/target/streams/compile/_global/_global/discoveredMainClasses/data",
    "generated/chisel/target/streams/compile/bspReporter/_global/streams/out",
    "generated/chisel/target/streams/compile/compile/_global/streams/out",
    "generated/chisel/target/streams/compile/compileIncremental/_global/streams/export",
    "generated/chisel/target/streams/compile/compileIncremental/_global/streams/out",
    "generated/chisel/target/streams/compile/copyResources/_global/streams/out",
    "generated/chisel/target/streams/compile/dependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/exportedProductJars/_global/streams/export",
    "generated/chisel/target/streams/compile/exportedProducts/_global/streams/export",
    "generated/chisel/target/streams/compile/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/incOptions/_global/streams/out",
    "generated/chisel/target/streams/compile/internalDependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/internalDependencyClasspath/_global/streams/out",
    "generated/chisel/target/streams/compile/mainClass/_global/streams/out",
    "generated/chisel/target/streams/compile/managedClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/packageBin/_global/streams/inputs",
    "generated/chisel/target/streams/compile/packageBin/_global/streams/out",
    "generated/chisel/target/streams/compile/packageBin/_global/streams/output",
    "generated/chisel/target/streams/compile/scalacOptions/_global/streams/out",
    "generated/chisel/target/streams/compile/unmanagedClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/unmanagedClasspath/_global/streams/out",
    "generated/chisel/target/streams/compile/unmanagedJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/dependencyClasspathAsJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/exportedProductJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/runtime/fullClasspathAsJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/internalDependencyAsJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/internalDependencyAsJars/_global/streams/out",
    "generated/chisel/target/streams/runtime/managedClasspath/_global/streams/export",
    "generated/chisel/target/streams/runtime/unmanagedClasspath/_global/streams/export",
    "generated/chisel/target/streams/runtime/unmanagedClasspath/_global/streams/out",
    "generated/chisel/target/streams/runtime/unmanagedJars/_global/streams/export",
    "generated/chisel/verification/assert/layers-GeneratedAcceleratorTop-Verification-Assert.sv",
    "generated/chisel/verification/assert/layers-GeneratedAxiDdrTop-Verification-Assert.sv",
    "generated/chisel/verification/assume/layers-GeneratedAcceleratorTop-Verification-Assume.sv",
    "generated/chisel/verification/assume/layers-GeneratedAxiDdrTop-Verification-Assume.sv",
    "generated/chisel/verification/cover/layers-GeneratedAcceleratorTop-Verification-Cover.sv",
    "generated/chisel/verification/cover/layers-GeneratedAxiDdrTop-Verification-Cover.sv",
    "generated/chisel/verification/layers-GeneratedAcceleratorTop-Verification.sv",
    "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv",
    "generated/chisel/vivado/Activation.sv",
    "generated/chisel/vivado/Attention.sv",
    "generated/chisel/vivado/DenseFFN.sv",
    "generated/chisel/vivado/GPT2PreLNBlock.sv",
    "generated/chisel/vivado/GeneratedAcceleratorTop.sv",
    "generated/chisel/vivado/GeneratedAxiDdrTop.sv",
    "generated/chisel/vivado/IntegerAttention.sv",
    "generated/chisel/vivado/IntegerVectorNorm.sv",
    "generated/chisel/vivado/Linear.sv",
    "generated/chisel/vivado/Linear_1.sv",
    "generated/chisel/vivado/Linear_2.sv",
    "generated/chisel/vivado/Linear_3.sv",
    "generated/chisel/vivado/PhysicalIntegerSqrt.sv",
    "generated/chisel/vivado/PhysicalLinearAdd.sv",
    "generated/chisel/vivado/PhysicalLinearMul.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_12.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_14.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_15.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_16.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_17.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_2.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_25.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_28.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_3.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_32.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_36.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_4.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_5.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_6.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_7.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_8.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_9.sv",
    "generated/chisel/vivado/PhysicalStreamFifo.sv",
    "generated/chisel/vivado/PhysicalStreamFifo_3.sv",
    "generated/chisel/vivado/PhysicalStreamFifo_7.sv",
    "generated/chisel/vivado/QKVProjection.sv",
    "generated/chisel/vivado/ResidualAdd.sv",
    "generated/chisel/vivado/VectorNorm.sv",
    "generated/chisel/vivado/WeightTileCache.sv",
    "generated/chisel/vivado/WeightTileCache_1.sv",
    "generated/chisel/vivado/WeightTileCache_2.sv",
    "generated/chisel/vivado/WeightTileServiceMux.sv",
    "generated/chisel/vivado/filelist.f",
    "generated/chisel/vivado/verification/assert/layers-GeneratedAcceleratorTop-Verification-Assert.sv",
    "generated/chisel/vivado/verification/assert/layers-GeneratedAxiDdrTop-Verification-Assert.sv",
    "generated/chisel/vivado/verification/assume/layers-GeneratedAcceleratorTop-Verification-Assume.sv",
    "generated/chisel/vivado/verification/assume/layers-GeneratedAxiDdrTop-Verification-Assume.sv",
    "generated/chisel/vivado/verification/cover/layers-GeneratedAcceleratorTop-Verification-Cover.sv",
    "generated/chisel/vivado/verification/cover/layers-GeneratedAxiDdrTop-Verification-Cover.sv",
    "generated/chisel/vivado/verification/layers-GeneratedAcceleratorTop-Verification.sv",
    "generated/chisel/vivado/verification/layers-GeneratedAxiDdrTop-Verification.sv"
  ],
  "generated_memory_layout": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/memory/memory_layout.json",
  "generated_package_root": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel",
  "generated_runtime_config": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/runtime/runtime_config.json",
  "generated_top": {
    "fpga_wrapper_class": "GeneratedAxiDdrTop",
    "param_class": "DecoderBlockParams",
    "params": {
      "acc_bits": 32,
      "activation_banks": 4,
      "activation_memory": "xpm_bram",
      "board_axi_data_width_bits": 512,
      "burst_beats": 1,
      "cache_refill_data_width_bits": 512,
      "cache_tile_count": 2,
      "cache_tile_words": 256,
      "clock_target_mhz": 0,
      "compute_backend": "integer_dsp",
      "cross_token_reuse_tokens": 8,
      "elem_bits": 8,
      "fifo_depth": 128,
      "fifo_memory": "xpm_bram",
      "head_dim": 64,
      "hidden_size": 768,
      "input_bits": 8,
      "integer_mode": true,
      "intermediate_size": 3072,
      "lanes": 16,
      "large_cache_memory": "xpm_uram",
      "max_seq_len": 16,
      "num_kv_heads": 12,
      "num_q_heads": 12,
      "output_bits": 8,
      "pipeline_depth": 1,
      "rounding_mode": "nearest_even",
      "saturation_enabled": true,
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
    "top_class": "GPT2PreLNBlock"
  },
  "generation_policy": "from_scratch_target_accelerator_package",
  "model_type": "gpt2",
  "package_static_check": {
    "checked_contracts": [
      "generated_package_required_files",
      "target_artifact_match_explicit",
      "planned_output_status",
      "template_source_coverage",
      "compile_and_contract_gate_status"
    ],
    "checker": "codegen_package_static_check",
    "errors": [],
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/codegen_package_static_check.json",
    "status": "pass",
    "summary": "generated package manifest is structurally complete",
    "warnings": []
  },
  "planned_code_outputs": [
    {
      "depends_on": [
        "artifact.input.model_config"
      ],
      "id": "generated.model_ir",
      "kind": "model_ir",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding"
      ],
      "id": "generated.arch_plan",
      "kind": "architecture_plan",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [],
      "id": "generated.chisel_modules",
      "kind": "chisel",
      "selected_operator_template_sources": [
        "Activation.scala",
        "Attention.scala",
        "DecoderBlock.scala",
        "FFN.scala",
        "Mask.scala",
        "Norm.scala",
        "Residual.scala",
        "Softmax.scala"
      ],
      "status": "generated",
      "template_sources": [
        "Activation.scala",
        "Attention.scala",
        "Common.scala",
        "DecoderBlock.scala",
        "Elementwise.scala",
        "FFN.scala",
        "KVCache.scala",
        "Linear.scala",
        "Mask.scala",
        "Norm.scala",
        "PhysicalResources.scala",
        "QKVProjection.scala",
        "Residual.scala",
        "RoPE.scala",
        "Softmax.scala",
        "WeightTileCache.scala"
      ]
    },
    {
      "depends_on": [
        "generated.chisel_modules"
      ],
      "id": "generated.fpga_ip_simulation_closure",
      "kind": "fpga_ip_simulation_closure",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.top_wrapper",
      "kind": "top_wrapper",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.top_wrapper",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.fpga_axi_ddr_top_wrapper",
      "kind": "fpga_axi_ddr_top_wrapper",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.fpga_axi_ddr_top_wrapper",
        "generated.runtime_config"
      ],
      "id": "generated.performance_counter",
      "kind": "synthesizable_performance_counter",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "artifact.stage4.parameter_binding",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.memory_layout",
      "kind": "memory_layout",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.memory_layout",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.runtime_config",
      "kind": "runtime_config",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "artifact.stage4.parameter_binding"
      ],
      "id": "generated.scala_contract_check",
      "kind": "scala_contract_check",
      "selected_operator_template_sources": [],
      "status": "generated",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "generated.top_wrapper",
        "generated.fpga_axi_ddr_top_wrapper"
      ],
      "id": "generated.codegen_compile_gate",
      "kind": "compile_gate",
      "selected_operator_template_sources": [],
      "status": "pass",
      "template_sources": []
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "generated.memory_layout",
        "generated.runtime_config",
        "generated.codegen_compile_gate"
      ],
      "id": "generated.codegen_contract_check",
      "kind": "contract_check",
      "selected_operator_template_sources": [],
      "status": "pass",
      "template_sources": []
    }
  ],
  "schema_version": "spatialaccagent.code_generation_manifest.v0",
  "selected_operator_template_sources": [
    "Activation.scala",
    "Attention.scala",
    "DecoderBlock.scala",
    "FFN.scala",
    "Mask.scala",
    "Norm.scala",
    "Residual.scala",
    "Softmax.scala"
  ],
  "stage": "code_generation",
  "stage_gate_policy": {
    "current_stage_acceptance": [
      "generated package root, Chisel sources, top wrappers, memory layout, runtime config, and contract checker source must exist",
      "compile/elaboration gate must pass every declared SBT command and expose per-command status/returncode",
      "codegen_contract_check must pass upstream transition, model/shape/numeric, template provenance, compile warning, memory layout, runtime config, and parameter legality checks",
      "target_model_artifact_status.current_artifacts_match_target must be true and missing_for_target must be empty",
      "manifest template_sources must cover every template Scala file copied into the generated package",
      "generated FPGA IP simulation closure must require the same Vivado IP/XPM module interfaces and latencies as implementation"
    ],
    "later_stage_obligations": [
      "Current-source VCS compilation, elaboration, and linking belong to Stage 6, not Stage 5; their absence must not block this code-generation handoff",
      "Vivado synthesis, timing/resource reports, and source-cycle performance analysis belong to Stage 7",
      "clock_target_mhz=0 means the board shell clock is unknown; assigning a nonzero target requires board-profile evidence or approval",
      "memory_layout.json and runtime_config.json are generated handoff artifacts; Stage 6+ must validate them against board/runtime tools before hardware pass claims"
    ],
    "risk_classification_rule": "If current-stage checks pass and no concrete current binding error is evidenced, return ready. candidate_only is the normal pre-publication state, not a failed check. Team audit proposals are not additional required reports; use the supplied contract/static results. Route later tool obligations to proposed_actions rather than blocking Stage 5."
  },
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
  },
  "template_sources": [
    "Activation.scala",
    "Attention.scala",
    "Common.scala",
    "DecoderBlock.scala",
    "Elementwise.scala",
    "FFN.scala",
    "KVCache.scala",
    "Linear.scala",
    "Mask.scala",
    "Norm.scala",
    "PhysicalResources.scala",
    "QKVProjection.scala",
    "Residual.scala",
    "RoPE.scala",
    "Softmax.scala",
    "WeightTileCache.scala"
  ]
}
</candidate_stage_artifact>

<reference_subtask_plan_if_split_is_needed>
[
  {
    "acceptance_checkers": [
      "addr_map_check",
      "codegen_package_static_check",
      "implementation_package_static",
      "required_real_tool_evidence_check",
      "sacg_static_check",
      "template_binding_static_check"
    ],
    "action_type": "template_bound_artifact_review",
    "artifact_focus": [
      "generated.chisel_modules",
      "generated.top_wrapper",
      "generated.fpga_axi_ddr_top_wrapper"
    ],
    "constraints": [
      "constraint.model.decoder",
      "constraint.shape.model",
      "constraint.template.library",
      "constraint.parameter.binding"
    ],
    "id": "code_generation.template_codegen_engineer",
    "objective": "Check that generated Chisel/top/wrapper code is derived from selected templates, parameter bindings, and SACG constraints rather than free RTL.",
    "parallel_group": 0,
    "role": "template codegen engineer",
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
      "mission": "Check that generated Chisel/top/wrapper code is derived from selected templates, parameter bindings, and SACG constraint...<len=143>",
      "out_of_scope": {
        "_size": 3,
        "_type": "list"
      },
      "primary_responsibilities": {
        "_size": 5,
        "_type": "list"
      },
      "professional_family": "numeric_template"
    },
    "role_profile": {
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
      "family": "numeric_template"
    },
    "title": "Generate template-bound Chisel package"
  },
  {
    "acceptance_checkers": [
      "addr_map_check",
      "data_order_trace_check",
      "deadlock_watchdog",
      "implementation_package_static",
      "repair_boundary_check",
      "required_real_tool_evidence_check"
    ],
    "action_type": "sacg_constraint_review",
    "artifact_focus": [
      "artifact.stage5.design_artifact_manifest"
    ],
    "constraints": [
      "constraint.model.decoder",
      "constraint.stream.order",
      "constraint.memory.board",
      "constraint.runtime.board"
    ],
    "id": "code_generation.cross_layer_consistency_auditor",
    "objective": "Identify whether code generation is drifting away from the model, shape, numeric, template, and board rules established in earlier stages.",
    "parallel_group": 1,
    "role": "cross layer consistency auditor",
    "role_assignment": {
      "_more_keys": 5,
      "collaboration_interfaces": {
        "acceptance_checkers": {
          "_size": 9,
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
      "mission": "Identify whether code generation is drifting away from the model, shape, numeric, template, and board rules established ...<len=138>",
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
    "title": "Audit design story alignment"
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
