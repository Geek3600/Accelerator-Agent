<agent>
memory_runtime_package_engineer
</agent>

<task>
Verify that generated memory_layout.json, runtime_config.json, RAM artifacts, and GeneratedAxiDdrTop wrapper are consistent with board memory/runtime constraints and pipeline transfer assumptions, while preserving later-stage validation boundaries.
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
21. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
22. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
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
  "objective": "Generate and audit a template-bound accelerator code package from SACG.",
  "paper_alignment": {
    "method": "SACG-guided, template-constrained, checker-verified design closure",
    "problem": "Cross-Layer Consistency Problem in Agentic LLM Spatial Accelerator Design"
  },
  "stage": "code_generation",
  "team_rules": [
    "Act as an AI chip design team for FPGA spatial accelerator automatic design, not as isolated static scripts.",
    "Stay inside the SpatialAccAgent paper story: cross-layer consistency for LLM spatial accelerators.",
    "Treat SACG as the design team's shared memory and evidence ledger; do not rely on natural-language memory as correctness evidence.",
    "Treat sacg_memory_truth as the authoritative current blocker set; closed, superseded, or historical memory records are recovery evidence onl...<len=142>",
    "Use trusted templates and bounded glue code; do not propose free-form RTL rewrites outside approved repair boundaries.",
    "Map every observation to model, shape, numeric precision, data order, transfer unit, memory, runtime, implementation, or deployment constrai...<len=144>",
    "Do not bypass checkers, modify golden outputs, loosen tolerance, or claim hardware pass without tool evidence.",
    "For board/app-shell integration, use LLM reasoning to synthesize profile/contract policy from user-supplied materials and real tool evidence...<len=199>"
  ]
}
</team_context>

<subtask>
{
  "acceptance_checkers": [
    "memory_runtime_plan_check",
    "stream_plan_check",
    "addr_map_check",
    "transfer_count_check",
    "codegen_contract_check",
    "codegen_package_static_check"
  ],
  "action_type": "memory_runtime_handoff_review",
  "agent": "memory_runtime_package_engineer",
  "artifact_focus": [
    "artifact.input.target_board_profile",
    "artifact.input.tool_profile",
    "artifact.input.tool_protocols",
    "artifact.stage3.pipeline_plan",
    "generated.memory_layout",
    "generated.runtime_config",
    "generated.fpga_axi_ddr_top_wrapper",
    "generated.codegen_contract_check"
  ],
  "constraints": [
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.deployment.board",
    "constraint.stream.order",
    "constraint.beat.pipeline",
    "constraint.memory_schedule.pipeline",
    "constraint.liveness.pipeline"
  ],
  "expected_artifacts": [
    "memory_runtime_codegen_audit.json",
    "addr_map_alignment_report.json",
    "runtime_abi_handoff_notes.json"
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
    "code_generation.evidence_gate_auditor"
  ],
  "id": "code_generation.memory_runtime_package_engineer",
  "objective": "Verify that generated memory_layout.json, runtime_config.json, RAM artifacts, and GeneratedAxiDdrTop wrapper are consistent with board memory/runtime constraints and pipeline transfer assumptions, while preserving later-...<len=248>",
  "role": "memory and runtime integration engineer",
  "role_assignment": {
    "collaboration_interfaces": {
      "accepted_by": [
        "memory_runtime_plan_check",
        "stream_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "codegen_contract_check"
      ],
      "consumes": [
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_protocols",
        "artifact.stage3.pipeline_plan",
        "candidate_stage_artifact.generated_memory_layout",
        "candidate_stage_artifact.generated_runtime_config",
        "candidate_stage_artifact.generated_files"
      ],
      "downstream_consumers": [
        "code_generation.evidence_gate_auditor",
        "later_stage.verification",
        "later_stage.backend_board"
      ],
      "produces": [
        "memory_runtime_codegen_audit.json",
        "addr_map_alignment_report.json",
        "runtime_abi_handoff_notes.json"
      ]
    },
    "decision_authority": [
      "Accept or reject memory/runtime artifact consistency for the codegen stage.",
      "Flag transfer-count, address-map, or runtime-ABI mismatches as blockers.",
      "Prevent claims that generated memory/runtime artifacts are board-validated before real tool evidence exists."
    ],
    "mission": "Ensure generated package handoff artifacts for memory, runtime, and DDR integration are internally consistent and checker-verifiable without overstating deployment readiness.",
    "out_of_scope": [
      "Running DDR image roundtrip, AXI protocol simulation, Vivado implementation, or board runtime execution in this stage.",
      "Choosing a nonzero clock_target_mhz without board-profile evidence or approval.",
      "Changing pipeline schedule or memory architecture outside bounded repair rules."
    ],
    "primary_responsibilities": [
      "Consume target board profile, tool protocols, pipeline plan, generated memory layout, runtime config, and AXI DDR wrapper files.",
      "Check address alignment, non-overlap, RAM dimensions, stream beat widths, transfer-count assumptions, and runtime configuration references.",
      "Confirm generated.codegen_contract_check includes memory_layout_alignment_nonoverlap and runtime_config_consistency.",
      "Separate current-stage codegen acceptance from later VCS/Verilator, Vivado, and board runtime obligations.",
      "Produce a handoff report for verification and backend stages."
    ]
  },
  "role_profile": {
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
    "family": "data_memory_runtime"
  },
  "title": "Audit generated memory layout, runtime config, and AXI DDR wrapper handoff"
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
    "cwd": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
    "elaboration_enabled": true,
    "enabled": true,
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/compile_check.json",
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
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for pr...<len=700>"
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for pr...<len=655>"
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for pr...<len=580>"
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for pr...<len=578>"
      }
    ],
    "summary": "completed 4 compile/elaboration command(s)"
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
      "numeric_policy_to_generated_bits",
      "template_provenance_hashes",
      "compile_and_elaboration_warning_free",
      "memory_layout_alignment_nonoverlap",
      "runtime_config_consistency",
      "parameter_binding_legality"
    ],
    "checker": "codegen_contract_check",
    "errors": [],
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/codegen_contract_check.json",
    "status": "pass",
    "summary": "all code generation contracts passed",
    "warnings": []
  },
  "generated_files": [
    "generated/chisel/Activation.sv",
    "generated/chisel/AttentionGQA.sv",
    "generated/chisel/ElementwiseMul.sv",
    "generated/chisel/GatedMLP.sv",
    "generated/chisel/GeneratedAcceleratorTop.sv",
    "generated/chisel/GeneratedAxiDdrTop.sv",
    "generated/chisel/Linear.sv",
    "generated/chisel/Linear_1.sv",
    "generated/chisel/Linear_2.sv",
    "generated/chisel/Linear_4.sv",
    "generated/chisel/LlamaStyleBlock.sv",
    "generated/chisel/QKVProjection.sv",
    "generated/chisel/Queue1792_StreamBeat.sv",
    "generated/chisel/Queue4_StreamBeat.sv",
    "generated/chisel/README.md",
    "generated/chisel/RMSNorm.sv",
    "generated/chisel/ResidualAdd.sv",
    "generated/chisel/RoPE.sv",
    "generated/chisel/VectorNorm.sv",
    "generated/chisel/build.sbt",
    "generated/chisel/filelist.f",
    "generated/chisel/logs/codegen_contract_check.json",
    "generated/chisel/logs/codegen_package_static_check.json",
    "generated/chisel/logs/compile_check.json",
    "generated/chisel/memory/memory_layout.json",
    "generated/chisel/project/build.properties",
    "generated/chisel/project/target/config-classes/$12c5193f5eb1a2774175$.class",
    "generated/chisel/project/target/config-classes/$12c5193f5eb1a2774175.cache",
    "generated/chisel/project/target/config-classes/$12c5193f5eb1a2774175.class",
    "generated/chisel/project/target/config-classes/$427ebed637acdd4502f7$.class",
    "generated/chisel/project/target/config-classes/$427ebed637acdd4502f7.cache",
    "generated/chisel/project/target/config-classes/$427ebed637acdd4502f7.class",
    "generated/chisel/project/target/config-classes/$c7e6e4aef3d918c0c4fd$.class",
    "generated/chisel/project/target/config-classes/$c7e6e4aef3d918c0c4fd.cache",
    "generated/chisel/project/target/config-classes/$c7e6e4aef3d918c0c4fd.class",
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
    "generated/chisel/ram_1792x256.sv",
    "generated/chisel/ram_4x129.sv",
    "generated/chisel/runtime/runtime_config.json",
    "generated/chisel/scripts/compile_check.sh",
    "generated/chisel/scripts/elaborate.sh",
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
    "generated/chisel/src/main/scala/spatialaccagent/templates/QKVProjection.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/RoPE.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Softmax.scala",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop.class",
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
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Attention$$anon$1.class",
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
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GPT2PreLNBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLP$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLP.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLPParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLPParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlock$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Int8QuantPorts.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCache$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCache.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCacheParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCacheParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Linear$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Linear.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearScalePorts.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlock$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/OPTPreLNBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ParametricLinearInt8ToFP32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ParametricLinearInt8ToInt8.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNorm$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjection$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjection.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjectionParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjectionParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjector.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVStreamBeat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNorm$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormQ.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualAdd$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualAdd.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPE$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEApply.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Softmax$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Softmax.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/SoftmaxParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/SoftmaxParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StageConfig.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamBeat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamSpec$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamSpec.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNorm$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightWrite.class",
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
    "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv"
  ],
  "generated_memory_layout": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/memory/memory_layout.json",
  "generated_package_root": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
  "generated_runtime_config": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/runtime/runtime_config.json",
  "generated_top": {
    "fpga_wrapper_class": "GeneratedAxiDdrTop",
    "param_class": "LlamaStyleBlockParams",
    "params": {
      "clock_target_mhz": 0,
      "elem_bits": 16,
      "head_dim": 64,
      "hidden_size": 896,
      "input_bits": 32,
      "intermediate_size": 4864,
      "lanes": 8,
      "max_seq_len": 16,
      "num_kv_heads": 2,
      "num_q_heads": 14,
      "output_bits": 32
    },
    "top_class": "LlamaStyleBlock"
  },
  "generation_policy": "from_scratch_target_accelerator_package",
  "model_type": "qwen2",
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
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/codegen_package_static_check.json",
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
        "Attention.scala",
        "DecoderBlock.scala",
        "Elementwise.scala",
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
        "QKVProjection.scala",
        "Residual.scala",
        "RoPE.scala",
        "Softmax.scala"
      ]
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
    "Attention.scala",
    "DecoderBlock.scala",
    "Elementwise.scala",
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
      "manifest template_sources must cover every template Scala file copied into the generated package"
    ],
    "later_stage_obligations": [
      "VCS/Verilator functional simulation, numerical/model validation, Vivado synthesis/implementation/timing, and board execution are later verification/deployment gates",
      "clock_target_mhz=0 means the board shell clock is unknown; assigning a nonzero target requires board-profile evidence or approval",
      "memory_layout.json and runtime_config.json are generated handoff artifacts; Stage 6+ must validate them against board/runtime tools before hardware pass claims"
    ],
    "risk_classification_rule": "If compile_gate, codegen_contract_check, and codegen_package_static_check pass, do not report resolved current-stage codegen items as risks; later tool obligations belong in proposed_actions."
  },
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
    "QKVProjection.scala",
    "Residual.scala",
    "RoPE.scala",
    "Softmax.scala"
  ]
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
