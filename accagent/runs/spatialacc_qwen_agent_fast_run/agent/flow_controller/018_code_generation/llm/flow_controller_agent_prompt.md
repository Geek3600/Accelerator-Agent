<agent>
flow_controller_agent
</agent>

<task>
Review SACG memory and the latest stage result, then decide whether the autonomous design team should proceed, retry the current stage, backtrack to an earlier stage, run bounded repair, or stop to avoid artifact contamination.
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

<current_stage>
code_generation
</current_stage>

<stage_passed>
true
</stage_passed>

<attempt_count>
2
</attempt_count>

<available_stages>
[
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
  "compile_gate": {
    "commands": [
      [
        "sbt",
        "--no-server",
        "--batch",
        "--supershell=false",
        "Compile/compile"
      ],
      [
        "sbt",
        "--no-server",
        "--batch",
        "--supershell=false",
        "runMain spatialaccagent.generated.GeneratedContractCheck"
      ],
      [
        "sbt",
        "--no-server",
        "--batch",
        "--supershell=false",
        "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
      ],
      [
        "sbt",
        "--no-server",
        "--batch",
        "--supershell=false",
        "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
      ]
    ],
    "cwd": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
    "duration_sec": 251.1909759650007,
    "elaboration_enabled": true,
    "enabled": true,
    "local_sbt_dirs": {
      "coursier_cache": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/.sbt_codegen_cache/coursier",
      "sbt_boot_directory": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/.sbt_codegen_cache/sbt/boot",
      "sbt_global_base": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/.sbt_codegen_cache/sbt",
      "sbt_ivy_home": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/.sbt_codegen_cache/ivy2"
    },
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/compile_check.json",
    "returncode": 0,
    "schema_version": "spatialaccagent.codegen_compile_gate.v0",
    "status": "pass",
    "stderr_tail": "",
    "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAxiDdrTop \n[success] Total time: 50 s, completed Jul 9, 2026, 6:33:12 PM\n",
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[info] compiling 19 Scala sources to /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/target/scala-2.13/classes ...\n[info] done compiling\n[success] Total time: 58 s, completed Jul 9, 2026, 6:30:41 PM\n"
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[info] running spatialaccagent.generated.GeneratedContractCheck \nGeneratedContractCheck pass: hidden=896, intermediate=4864, lanes=8, bits=32/16/32\n[success] Total time: 3 s, completed Jul 9, 2026, 6:31:00 PM\n"
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAccelerator \n[success] Total time: 50 s, completed Jul 9, 2026, 6:32:06 PM\n"
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
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAxiDdrTop \n[success] Total time: 50 s, completed Jul 9, 2026, 6:33:12 PM\n"
      }
    ],
    "summary": "completed 4 compile/elaboration command(s)",
    "timeout_sec": 1800
  },
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
    "design_id": "qwen2_spatialacc_agent_run",
    "errors": [],
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/codegen_contract_check.json",
    "schema_version": "spatialaccagent.codegen_contract_check.v0",
    "status": "pass",
    "summary": "all code generation contracts passed",
    "warnings": []
  },
  "design_team": {
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/team/team_aggregate.json",
    "approval_required_for": [
      "Any architecture, pipeline, memory-layout, numeric-policy, or major template change beyond bounded repair boundaries.",
      "Assigning a nonzero clock_target_mhz or board timing target without cited board-profile/tool evidence.",
      "Assigning a nonzero clock_target_mhz or changing board clock/reset/shell assumptions without cited board-profile or Vivado evidence.",
      "Assigning any nonzero clock_target_mhz or timing/runtime target before board-profile, Vivado, or app-shell evidence exists.",
      "Changing memory_layout.json base addresses, address regions, alignment policy, buffer sizing, RAM dimensions, or non-overlap assumptions.",
      "Changing numeric tolerance policy, golden-reference generation policy, or expected outputs.",
      "Changing pipeline schedule, stream beat width/order, lanes, or memory architecture outside bounded repair rules.",
      "Changing runtime_config.json ABI fields, transfer counts, data order, host/runtime protocol fields, or board runtime references.",
      "Changing stage4 parameter binding, model tensor shapes, stream/data order, memory layout, or numeric policy.",
      "Changing the selected template library/template set, adding new operator templates, or replacing template-derived modules with free-form RTL.",
      "Proceeding with deployment claims after any failed or missing real-tool checker evidence.",
      "Selecting ambiguous backend/app-shell target names without cited real tool evidence.",
      "Selecting app-shell target names, shell ports, or AXI/DDR integration points when backend target discovery evidence is ambiguous."
    ],
    "completed_subtasks": 4,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "model_config_check",
          "numeric_policy_check",
          "parameter_binding_static_check",
          "codegen_contract_check"
        ],
        "action_type": "cross_layer_consistency_review",
        "consumes": [
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.stage3.pipeline_plan",
          "artifact.stage4.parameter_binding",
          "artifact.stage4.parameter_static_checks",
          "candidate_stage_artifact.generated_top",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.compile_gate"
        ],
        "id": "codegen.materialize_model_numeric_consistency_traces",
        "on_failure": "Block code_generation evidence-gate promotion. If the mismatch is local to generated parameters or supplied top selection, route to bounded_template_repair/codegen regeneration; if artifact.stage4.parameter_binding or artifact.stage3.pipeline_plan is the conflicting source, raise a stage_backtrack_request instead of editing generated outputs or loosening checks.",
        "produces": [
          "model_numeric_codegen_consistency_report.json",
          "generated_params_shape_trace.json",
          "numeric_policy_binding_trace.json"
        ],
        "rationale": "Create the auditor handoff artifacts from the supplied model_config, numeric_policy, pipeline/parameter binding, generated_top parameters, and passed contract evidence so the final evidence gate can consume a checker-grounded model/shape/numeric trace.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "sacg_static_check",
          "model_config_check",
          "numeric_policy_check",
          "parameter_binding_static_check",
          "codegen_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "codegen_package_static_check",
          "codegen_compile_gate_check",
          "codegen_contract_check",
          "code_generation_manifest_static_check"
        ],
        "action_type": "evidence_gate_handoff",
        "consumes": [
          "model_numeric_codegen_consistency_report.json",
          "generated_params_shape_trace.json",
          "numeric_policy_binding_trace.json",
          "candidate_stage_artifact.package_static_check",
          "candidate_stage_artifact.compile_gate",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.generated_top"
        ],
        "id": "codegen.evidence_gate_consume_model_numeric_audit",
        "on_failure": "Keep code_generation promotion blocked and rerun only the failing checker or request a bounded codegen-local repair; do not bypass the failed checker and do not modify golden outputs or tolerances.",
        "produces": [
          "code_generation.evidence_gate_auditor.model_numeric_handoff_record"
        ],
        "rationale": "Aggregate this model/numeric audit with compile, package, and contract gate evidence before downstream consumption, without treating later functional or hardware validation as already passed.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "team_aggregate",
          "codegen_package_static_check",
          "codegen_compile_gate",
          "codegen_contract_check"
        ]
      },
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
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_protocols",
          "artifact.stage3.pipeline_plan",
          "artifact.stage4.parameter_binding",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
          "generated/chisel/ram_1792x256.sv",
          "generated/chisel/ram_4x129.sv",
          "generated/chisel/logs/codegen_contract_check.json",
          "generated/chisel/logs/codegen_package_static_check.json",
          "generated/chisel/logs/compile_check.json"
        ],
        "id": "codegen.memory_runtime_static_handoff_check",
        "on_failure": "Block evidence-gate promotion for memory/runtime handoff, preserve the failing checker evidence, and route to bounded memory_runtime_repair with repair_boundary_check; do not loosen checks, alter golden outputs, or silently change pipeline/memory architecture.",
        "produces": [
          "memory_runtime_codegen_audit.json",
          "addr_map_alignment_report.json",
          "runtime_abi_handoff_notes.json"
        ],
        "rationale": "Produce the specialist handoff artifacts by binding the generated memory/runtime artifacts and wrapper evidence to the named SACG constraints, while recording standalone checker status instead of inferring field-level address or transfer details from the compact summary.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "memory_runtime_plan_check",
          "stream_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "codegen_contract_check",
          "codegen_package_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "case_stage_leaf_static",
          "case_single_transformer_layer",
          "functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "addr_map_check",
          "verification_artifact_contract_check"
        ],
        "action_type": "hierarchical_real_tool_planning_and_execution",
        "consumes": [
          "artifact.stage6.verification_plan",
          "artifact.stage6.verification_artifact_contract",
          "memory_runtime_codegen_audit.json",
          "addr_map_alignment_report.json",
          "runtime_abi_handoff_notes.json",
          "artifact.stage3.pipeline_plan",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/GeneratedAcceleratorTop.sv",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/ram_1792x256.sv",
          "generated/chisel/ram_4x129.sv"
        ],
        "id": "verification.hierarchical_memory_transfer_validation",
        "on_failure": "Stop at the failed layer, localize the earliest causal boundary/module using tool evidence and SACG constraints, enter bounded repair, and rerun the failed layer; do not skip to AXI/DDR wrapper or board runtime.",
        "produces": [
          "verification/case_diagnostics/memory_transfer_validation.json",
          "verification/case_diagnostics/addr_transfer_trace_report.json",
          "verification/case_diagnostics/deadlock_liveness_report.json"
        ],
        "rationale": "Validate transfer count, stream order, liveness, and address-map assumptions in the required layer order before any board-accurate wrapper claim: leaf/static boundaries first, connected single-transformer-layer checks second, and wrapper/system checks only after lower layers pass.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "case_stage_leaf_static",
          "case_single_transformer_layer",
          "functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "addr_map_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_board_interface_discovery",
          "real_tool.case_axi_ddr_interface",
          "real_tool.case_axi_protocol_check",
          "real_tool.case_ddr_image_roundtrip",
          "real_tool.case_runtime_abi_check",
          "real_tool.case_runtime_bitstream",
          "required_real_tool_evidence_check",
          "deployment_board_check"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_protocols",
          "artifact.stage9.app_shell_integration_contract",
          "memory_runtime_codegen_audit.json",
          "addr_map_alignment_report.json",
          "runtime_abi_handoff_notes.json",
          "verification/case_diagnostics/memory_transfer_validation.json",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/GeneratedAxiDdrTop.sv"
        ],
        "id": "backend_board.memory_runtime_real_tool_closure",
        "on_failure": "Keep runtime bitstream and board runtime blocked, localize the failing interface/ABI/address boundary from tool evidence, and request bounded recovery or approval if app-shell targets or clock/runtime fields are ambiguous; do not modify memory layout, runtime ABI, or clock target without approval.",
        "produces": [
          "backend_board/case_diagnostics/board_interface_discovery.json",
          "backend_board/case_diagnostics/axi_ddr_interface_check.json",
          "backend_board/case_diagnostics/axi_protocol_check.json",
          "backend_board/case_diagnostics/ddr_image_roundtrip.json",
          "backend_board/case_diagnostics/runtime_abi_check.json",
          "backend_board/case_diagnostics/runtime_bitstream_report.json"
        ],
        "rationale": "After verification evidence passes, close the deployment boundary with real board/tool evidence for the generated memory layout, runtime ABI, and AXI/DDR wrapper rather than treating codegen elaboration as hardware validation.",
        "requires_approval": false,
        "stage": "backend_board",
        "tool_roles": [
          "case_board_interface_discovery",
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_runtime_abi_check",
          "case_runtime_bitstream"
        ]
      },
      {
        "acceptance_checkers": [
          "template_binding_static_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "code_generation_manifest_static_check",
          "codegen_package_static_check",
          "codegen_contract_check",
          "codegen_compile_gate_check"
        ],
        "action_type": "template_bound_artifact_review",
        "consumes": [
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.stage2.template_selection",
          "artifact.stage4.parameter_binding",
          "candidate_stage_artifact.generated_files",
          "candidate_stage_artifact.planned_code_outputs",
          "candidate_stage_artifact.generated_top",
          "candidate_stage_artifact.package_static_check",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.compile_gate"
        ],
        "id": "code_generation.finalize_template_bound_audit",
        "on_failure": "Treat the failure as a current-stage blocker; do not promote generated code. Invoke bounded_template_repair only for mismatches repairable within the existing template library and stage4 parameter binding; otherwise request backtrack or approval before changing templates, parameters, shapes, or numeric policy.",
        "produces": [
          "template_codegen_audit.json",
          "generated_source_to_template_trace.json",
          "compile_gate_evidence_summary.json"
        ],
        "rationale": "The supplied package_static_check, codegen_contract_check, and compile/elaboration gate all pass; materialize the expected audit and trace artifacts so downstream agents consume checker-grounded provenance rather than free-form RTL assumptions.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "template_coverage_check",
          "parameter_binding_static_check",
          "code_generation_manifest_static_check",
          "codegen_package_static_check",
          "codegen_contract_check",
          "codegen_compile_gate"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_reference_check",
          "verification_action_audit_check",
          "required_real_tool_evidence_check",
          "codegen_contract_check",
          "codegen_package_static_check"
        ],
        "action_type": "evidence_handoff",
        "consumes": [
          "template_codegen_audit.json",
          "generated_source_to_template_trace.json",
          "compile_gate_evidence_summary.json",
          "candidate_stage_artifact.generated_top",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.package_static_check"
        ],
        "id": "code_generation.handoff_template_codegen_evidence",
        "on_failure": "Hold downstream promotion until the handoff records cite the checker logs, preserve SACG constraint links, and explicitly state that no functional simulation, timing, bitstream, or board pass is being claimed.",
        "produces": [
          "code_generation.cross_layer_model_numeric_handoff.json",
          "code_generation.memory_runtime_package_handoff.json",
          "code_generation.evidence_gate_handoff.json"
        ],
        "rationale": "Downstream cross-layer model/numeric, memory/runtime, and evidence-gate agents need a compact handoff that preserves the template-provenance pass, structural package pass, and compile-only evidence boundary.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "team_aggregate",
          "sacg_reference_check",
          "verification_action_audit",
          "required_real_tool_evidence_check"
        ]
      },
      {
        "acceptance_checkers": [
          "code_generation_manifest_static_check",
          "codegen_compile_gate_check",
          "codegen_contract_check",
          "codegen_package_static_check",
          "required_real_tool_evidence_check",
          "repair_boundary_check",
          "human_boundary_check",
          "sacg_memory_check"
        ],
        "action_type": "checker_evidence_gate",
        "consumes": [
          "candidate_stage_artifact",
          "candidate_stage_artifact.compile_gate",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.package_static_check",
          "state_summary.sacg_memory_truth",
          "constraint.codegen.package",
          "constraint.codegen.compile_gate",
          "constraint.codegen.contract_check",
          "constraint.verification.plan",
          "constraint.human.boundary"
        ],
        "id": "code_generation.accept_ready_evidence_matrix",
        "on_failure": "Quarantine the candidate stage artifact, open a bounded stage_retry_request or trust barrier, and do not promote to verification/backend consumers.",
        "produces": [
          "code_generation_stage_acceptance_decision.json",
          "checker_evidence_matrix.json",
          "repair_or_handoff_boundary_record.json"
        ],
        "rationale": "Emit the stage acceptance decision and evidence matrix from visible pass evidence while recording that later functional, backend, and board checks remain unproven.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "team_aggregate",
          "code_generation_manifest_static_check",
          "codegen_compile_gate",
          "codegen_contract_check",
          "codegen_package_static_check",
          "required_real_tool_evidence_check",
          "repair_boundary_check",
          "human_boundary_check"
        ]
      },
      {
        "acceptance_checkers": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "sacg_reference_check",
          "case_stage_leaf_static",
          "boundary_contract_check"
        ],
        "action_type": "handoff_static_contract",
        "consumes": [
          "code_generation_stage_acceptance_decision.json",
          "checker_evidence_matrix.json",
          "generated/chisel/filelist.f",
          "generated/chisel/GeneratedAcceleratorTop.sv",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/verification/layers-GeneratedAcceleratorTop-Verification.sv",
          "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "artifact.input.case_adapter",
          "constraint.verification.plan"
        ],
        "id": "verification.build_hierarchical_artifact_contract",
        "on_failure": "Do not run real functional simulation; return the failed contract evidence to the orchestrator for bounded codegen/verification repair classification.",
        "produces": [
          "artifact.stage6.verification_plan",
          "artifact.stage6.verification_artifact_contract",
          "verification/boundary_contracts/operator_leaf_contracts.json",
          "verification/boundary_contracts/single_layer_contract.json",
          "verification/boundary_contracts/axi_ddr_contract.json"
        ],
        "rationale": "Downstream verification must convert the accepted codegen package into a checker-grounded hierarchical verification plan before real simulation or repair decisions.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "sacg_reference_check",
          "case_stage_leaf_static",
          "boundary_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_real_weight_artifacts",
          "artifact_hash_check",
          "numeric_compare"
        ],
        "action_type": "artifact_generation_and_hash_gate",
        "consumes": [
          "artifact.stage6.verification_artifact_contract",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.case_adapter",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/memory/memory_layout.json"
        ],
        "id": "verification.prepare_real_weight_and_golden_artifacts",
        "on_failure": "Classify the issue as checker/golden-reference/input-packing repair unless real RTL tool evidence identifies a hardware failure; do not alter tolerances or golden outputs without approved numeric-policy change.",
        "produces": [
          "verification/case_real_weights/input_manifest.json",
          "verification/case_real_weights/packed_weight_manifest.json",
          "verification/case_real_weights/golden_reference_manifest.json",
          "verification/case_real_weights/artifact_hashes.json"
        ],
        "rationale": "Real functional and numerical checks require reproducible input, packed weight, golden-reference, and hash manifests derived from the accepted model/numeric/runtime contracts.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "case_weight_manifest_generate",
          "case_real_weight_artifacts",
          "artifact_hash_check",
          "numeric_compare"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_leaf_functional",
          "real_tool.case_leaf_golden_compare",
          "real_tool.case_single_transformer_layer",
          "real_tool.case_single_layer_functional",
          "real_tool.case_single_layer_golden_compare",
          "real_tool.case_vcs_functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "numeric_compare"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "artifact.stage6.verification_artifact_contract",
          "generated/chisel/filelist.f",
          "generated/chisel/GeneratedAcceleratorTop.sv",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/memory/memory_layout.json",
          "verification/case_real_weights/input_manifest.json",
          "verification/case_real_weights/packed_weight_manifest.json",
          "verification/case_real_weights/golden_reference_manifest.json"
        ],
        "id": "verification.run_layered_real_functional_simulation",
        "on_failure": "Stop at the earliest failed layer; route simulator output through boundary-contract-guided localization and causal repair context, then rerun only the targeted failed checker before promotion.",
        "produces": [
          "verification/case_diagnostics/leaf_functional_diagnosis.json",
          "verification/case_diagnostics/single_layer_functional_diagnosis.json",
          "verification/case_diagnostics/layered_numeric_compare.json",
          "verification/case_diagnostics/layered_liveness_trace.json"
        ],
        "rationale": "Enforce the three-layer verification loop after static contract and real-weight gates: operator/leaf modules first, connected single-transformer-layer second, and no promotion beyond the first failing layer.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_vcs_functional_sim",
          "case_vcs_evidence_analyzer",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "numeric_compare"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_axi_ddr_interface",
          "real_tool.case_axi_protocol_check",
          "real_tool.case_ddr_image_roundtrip",
          "real_tool.case_deadlock_axi_check",
          "real_tool.case_verilator_functional_sim",
          "addr_map_check",
          "transfer_count_check",
          "data_order_trace_check"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "artifact.stage6.verification_artifact_contract",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/filelist.f",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "verification/case_real_weights/packed_weight_manifest.json",
          "verification/case_diagnostics/single_layer_functional_diagnosis.json"
        ],
        "id": "verification.run_board_accurate_axi_ddr_wrapper_checks",
        "on_failure": "Localize to the wrapper, runtime ABI, memory layout, or generated RTL boundary before any code repair; do not proceed to Vivado or board execution.",
        "produces": [
          "verification/case_diagnostics/axi_ddr_interface_check.json",
          "verification/case_diagnostics/axi_protocol_trace.json",
          "verification/case_diagnostics/ddr_image_roundtrip.json",
          "verification/case_diagnostics/axi_deadlock_diagnosis.json"
        ],
        "rationale": "After leaf and single-layer verification pass, validate the board-accurate AXI/DDR wrapped system against memory layout, runtime config, protocol, order, and liveness constraints before backend synthesis.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_deadlock_axi_check",
          "case_verilator_functional_sim",
          "addr_map_check",
          "transfer_count_check",
          "data_order_trace_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.app_shell_target_discovery_contract",
          "backend_app_shell_target_discovery_check",
          "real_tool.app_shell_target_hint_synthesis",
          "real_tool.app_shell_target_discovery_after_hint",
          "backend_bounded_recovery_action_check",
          "human_boundary_check"
        ],
        "action_type": "target_discovery",
        "consumes": [
          "code_generation_stage_acceptance_decision.json",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/memory/memory_layout.json",
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "constraint.deployment.board",
          "constraint.human.boundary"
        ],
        "id": "backend_board.discover_app_shell_target_and_clock_policy",
        "on_failure": "If target names, shell ports, memory interfaces, or clock evidence remain ambiguous, require bounded human/architecture approval and keep runtime bitstream and board runtime blocked.",
        "produces": [
          "artifact.stage9.app_shell_integration_contract",
          "artifact.stage9.app_shell_target_selection_decision",
          "backend_board/case_diagnostics/app_shell_target_discovery_contract.json",
          "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json",
          "target_discovery_policy_update.json"
        ],
        "rationale": "Board/app-shell integration must be synthesized from cited board materials and real tool evidence; clock_target_mhz is currently unknown and must not be guessed.",
        "requires_approval": false,
        "stage": "backend_board",
        "tool_roles": [
          "app_shell_target_discovery_contract",
          "app_shell_target_hint_synthesis",
          "app_shell_target_discovery_after_hint",
          "backend_bounded_recovery_action",
          "human_boundary_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_board_shell_wrapper_generate",
          "implementation_package_static",
          "real_tool.case_vivado_synthesis",
          "real_tool.case_vivado_synthesis_report_check",
          "real_tool.case_vivado_implementation",
          "real_tool.case_vivado_implementation_report_check",
          "timing_resource_check",
          "deployment_board_check"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "artifact.stage9.app_shell_integration_contract",
          "artifact.stage9.app_shell_target_selection_decision",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/filelist.f",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/memory/memory_layout.json",
          "verification/case_diagnostics/axi_ddr_interface_check.json"
        ],
        "id": "backend_board.run_vivado_synthesis_implementation_after_verification",
        "on_failure": "Route real Vivado evidence to backend bounded recovery or architecture review; do not bypass DRC/timing failures or represent them as code_generation pass evidence.",
        "produces": [
          "backend_board/case_diagnostics/vivado_synthesis_report.json",
          "backend_board/case_diagnostics/vivado_implementation_report.json",
          "backend_board/timing_resource_summary.json",
          "backend_board/implementation_package_static.json"
        ],
        "rationale": "Vivado synthesis, implementation, and timing/resource reports are later-stage real-tool evidence and must not be inferred from Chisel compile/elaboration success.",
        "requires_approval": false,
        "stage": "backend_board",
        "tool_roles": [
          "case_board_shell_wrapper_generate",
          "implementation_package_static",
          "case_vivado_synthesis",
          "case_vivado_synthesis_report_check",
          "case_vivado_implementation",
          "case_vivado_implementation_report_check",
          "timing_resource_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_runtime_abi_check",
          "real_tool.case_runtime_bitstream",
          "real_tool.app_shell_runtime_bitstream",
          "real_tool.board_runtime",
          "output_validity_check",
          "deployment_board_check"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "backend_board/case_diagnostics/vivado_implementation_report.json",
          "backend_board/timing_resource_summary.json",
          "artifact.stage9.app_shell_integration_contract",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/memory/memory_layout.json",
          "verification/case_real_weights/packed_weight_manifest.json",
          "verification/case_real_weights/golden_reference_manifest.json"
        ],
        "id": "backend_board.run_runtime_bitstream_and_output_validity",
        "on_failure": "Localize the board/runtime/interface boundary using real tool output, then open bounded recovery or backtrack; do not claim hardware pass.",
        "produces": [
          "backend_board/case_diagnostics/runtime_abi_check.json",
          "backend_board/case_diagnostics/runtime_bitstream_check.json",
          "backend_board/case_diagnostics/board_runtime_output_validity.json"
        ],
        "rationale": "Only board runtime, runtime ABI, bitstream, and output-validity evidence can support a board-level pass claim.",
        "requires_approval": false,
        "stage": "backend_board",
        "tool_roles": [
          "case_runtime_abi_check",
          "case_runtime_bitstream",
          "app_shell_runtime_bitstream",
          "board_runtime",
          "output_validity_check"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 15,
      "max_duration_sec": 569.9556472939876,
      "max_prompt_bytes": 66784,
      "result_count": 4,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 1439.5173056949716,
      "total_prompt_bytes": 266723
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 4,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/team/subtask_plan.json",
    "used_fallback_count": 0
  },
  "errors": [],
  "generated_files": [
    "generated/chisel/README.md",
    "generated/chisel/build.sbt",
    "generated/chisel/memory/memory_layout.json",
    "generated/chisel/project/build.properties",
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
    "generated/chisel/src/main/scala/spatialaccagent/templates/Softmax.scala"
  ],
  "llm_agent": {
    "agent": "code_generation_agent",
    "approval_required_for": [
      "Any architecture, pipeline, memory-layout, numeric-policy, or major template change beyond bounded repair boundaries.",
      "Assigning any nonzero clock_target_mhz, board timing target, clock/reset assumption, or runtime timing target without cited board-profile, Vivado, or app-shell evidence.",
      "Changing memory_layout.json base addresses, address regions, alignment policy, buffer sizing, RAM dimensions, or non-overlap assumptions.",
      "Changing runtime_config.json ABI fields, transfer counts, data order, host/runtime protocol fields, or board runtime references.",
      "Changing numeric tolerance policy, golden-reference generation policy, expected outputs, or model tensor shapes.",
      "Changing selected template library/template set, adding new operator templates, or replacing template-derived modules with free-form RTL.",
      "Selecting ambiguous backend/app-shell target names, shell ports, or AXI/DDR integration points without cited real tool evidence.",
      "Proceeding with deployment or hardware-pass claims after failed or missing real-tool checker evidence."
    ],
    "executable_actions": [
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "model_config_check",
          "numeric_policy_check",
          "parameter_binding_static_check",
          "codegen_contract_check"
        ],
        "action_type": "cross_layer_consistency_review",
        "consumes": [
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.stage3.pipeline_plan",
          "artifact.stage4.parameter_binding",
          "artifact.stage4.parameter_static_checks",
          "candidate_stage_artifact.generated_top",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.compile_gate",
          "state_summary.sacg_memory_truth"
        ],
        "id": "codegen.materialize_model_numeric_consistency_traces",
        "on_failure": "Block downstream code_generation evidence promotion. If the mismatch is local to generated parameter emission, route to bounded_template_repair/codegen regeneration; if stage3 or stage4 artifacts are the conflicting source, raise a stage_backtrack_request instead of editing generated outputs or loosening checks.",
        "produces": [
          "model_numeric_codegen_consistency_report.json",
          "generated_params_shape_trace.json",
          "numeric_policy_binding_trace.json"
        ],
        "rationale": "Create the missing model/shape/numeric trace artifacts from the supplied model, numeric policy, pipeline/parameter binding, generated_top parameters, and passing contract evidence so downstream agents consume checker-grounded parameter provenance instead of inferring it from the compact manifest.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "sacg_static_check",
          "model_config_check",
          "numeric_policy_check",
          "parameter_binding_static_check",
          "codegen_contract_check"
        ]
      },
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
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_protocols",
          "artifact.stage3.pipeline_plan",
          "artifact.stage4.parameter_binding",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
          "generated/chisel/ram_1792x256.sv",
          "generated/chisel/ram_4x129.sv",
          "generated/chisel/logs/codegen_contract_check.json",
          "generated/chisel/logs/codegen_package_static_check.json",
          "generated/chisel/logs/compile_check.json"
        ],
        "id": "codegen.memory_runtime_static_handoff_check",
        "on_failure": "Block memory/runtime handoff promotion, preserve failing checker evidence, and route to bounded memory_runtime_repair with repair_boundary_check; do not silently change memory layout, runtime ABI, pipeline schedule, data order, or golden outputs.",
        "produces": [
          "memory_runtime_codegen_audit.json",
          "addr_map_alignment_report.json",
          "runtime_abi_handoff_notes.json"
        ],
        "rationale": "Materialize the missing memory/runtime handoff artifacts by binding memory_layout.json, runtime_config.json, generated AXI/DDR wrapper evidence, and the passed codegen check logs to the named memory/runtime/board constraints without inferring hidden field details from the compact summary.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "memory_runtime_plan_check",
          "stream_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "codegen_contract_check",
          "codegen_package_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "template_binding_static_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "code_generation_manifest_static_check",
          "codegen_package_static_check",
          "codegen_contract_check",
          "codegen_compile_gate_check"
        ],
        "action_type": "template_bound_artifact_review",
        "consumes": [
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.stage2.template_selection",
          "artifact.stage4.parameter_binding",
          "candidate_stage_artifact.generated_files",
          "candidate_stage_artifact.planned_code_outputs",
          "candidate_stage_artifact.generated_top",
          "candidate_stage_artifact.package_static_check",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.compile_gate"
        ],
        "id": "code_generation.finalize_template_bound_audit",
        "on_failure": "Treat the failure as a current-stage codegen handoff blocker. Invoke bounded_template_repair only for mismatches repairable within the existing template library and stage4 parameter binding; otherwise request backtrack or approval before changing templates, parameters, shapes, or numeric policy.",
        "produces": [
          "template_codegen_audit.json",
          "generated_source_to_template_trace.json",
          "compile_gate_evidence_summary.json"
        ],
        "rationale": "The supplied package_static_check, codegen_contract_check, and compile/elaboration gate pass; materialize the missing template provenance and compile-evidence artifacts so downstream consumers can distinguish template-bound generated RTL from unverified free-form assumptions.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "template_coverage_check",
          "parameter_binding_static_check",
          "code_generation_manifest_static_check",
          "codegen_package_static_check",
          "codegen_contract_check",
          "codegen_compile_gate"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_reference_check",
          "verification_action_audit_check",
          "required_real_tool_evidence_check",
          "codegen_contract_check",
          "codegen_package_static_check",
          "sacg_memory_check"
        ],
        "action_type": "evidence_gate_handoff",
        "consumes": [
          "model_numeric_codegen_consistency_report.json",
          "generated_params_shape_trace.json",
          "numeric_policy_binding_trace.json",
          "memory_runtime_codegen_audit.json",
          "addr_map_alignment_report.json",
          "runtime_abi_handoff_notes.json",
          "template_codegen_audit.json",
          "generated_source_to_template_trace.json",
          "compile_gate_evidence_summary.json",
          "candidate_stage_artifact.generated_top",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "candidate_stage_artifact.contract_check",
          "candidate_stage_artifact.package_static_check",
          "candidate_stage_artifact.compile_gate",
          "state_summary.sacg_memory_truth"
        ],
        "id": "code_generation.handoff_cross_layer_codegen_evidence",
        "on_failure": "Hold downstream promotion until handoff records cite checker logs, preserve SACG constraint links, and explicitly state that no functional simulation, timing, bitstream, or board pass is being claimed; do not bypass failed checkers.",
        "produces": [
          "code_generation.cross_layer_model_numeric_handoff.json",
          "code_generation.memory_runtime_package_handoff.json",
          "code_generation.evidence_gate_handoff.json",
          "code_generation_stage_acceptance_decision.json",
          "checker_evidence_matrix.json",
          "repair_or_handoff_boundary_record.json"
        ],
        "rationale": "Aggregate the newly materialized model/numeric, memory/runtime, template/provenance, compile, package, and contract evidence into the compact cross-layer records required by verification and backend agents, while explicitly preserving that later hardware/tool gates are unproven.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "team_aggregate",
          "sacg_reference_check",
          "verification_action_audit",
          "required_real_tool_evidence_check"
        ]
      },
      {
        "acceptance_checkers": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "sacg_reference_check",
          "case_stage_leaf_static",
          "boundary_contract_check"
        ],
        "action_type": "handoff_static_contract",
        "consumes": [
          "code_generation_stage_acceptance_decision.json",
          "checker_evidence_matrix.json",
          "generated/chisel/filelist.f",
          "generated/chisel/GeneratedAcceleratorTop.sv",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/verification/layers-GeneratedAcceleratorTop-Verification.sv",
          "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "artifact.input.case_adapter",
          "constraint.verification.plan"
        ],
        "id": "verification.build_hierarchical_artifact_contract",
        "on_failure": "Do not run functional simulation. Return failed contract evidence for bounded codegen/verification repair classification and preserve the three-layer verification order.",
        "produces": [
          "artifact.stage6.verification_plan",
          "artifact.stage6.verification_artifact_contract",
          "verification/boundary_contracts/operator_leaf_contracts.json",
          "verification/boundary_contracts/single_layer_contract.json",
          "verification/boundary_contracts/axi_ddr_contract.json"
        ],
        "rationale": "After code_generation handoff artifacts exist, convert the accepted package into a checker-grounded hierarchical verification plan before any real functional simulation or repair decision.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "sacg_reference_check",
          "case_stage_leaf_static",
          "boundary_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.app_shell_target_discovery_contract",
          "backend_app_shell_target_discovery_check",
          "real_tool.app_shell_target_hint_synthesis",
          "real_tool.app_shell_target_discovery_after_hint",
          "backend_bounded_recovery_action_check",
          "human_boundary_check"
        ],
        "action_type": "target_discovery",
        "consumes": [
          "code_generation_stage_acceptance_decision.json",
          "generated/chisel/GeneratedAxiDdrTop.sv",
          "generated/chisel/runtime/runtime_config.json",
          "generated/chisel/memory/memory_layout.json",
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "constraint.deployment.board",
          "constraint.human.boundary"
        ],
        "id": "backend_board.discover_app_shell_target_and_clock_policy",
        "on_failure": "If target names, shell ports, memory interfaces, or clock evidence remain ambiguous, require bounded human/architecture approval and keep runtime bitstream and board runtime blocked.",
        "produces": [
          "artifact.stage9.app_shell_integration_contract",
          "artifact.stage9.app_shell_target_selection_decision",
          "backend_board/case_diagnostics/app_shell_target_discovery_contract.json",
          "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json",
          "target_discovery_policy_update.json"
        ],
        "rationale": "The generated_top clock_target_mhz is 0, so board/app-shell integration and any nonzero clock target must be derived from cited board materials and real tool evidence rather than guessed from codegen elaboration.",
        "requires_approval": false,
        "stage": "backend_board",
        "tool_roles": [
          "app_shell_target_discovery_contract",
          "app_shell_target_hint_synthesis",
          "app_shell_target_discovery_after_hint",
          "backend_bounded_recovery_action",
          "human_boundary_check"
        ]
      }
    ],
    "observations": [
      "Current-stage acceptance evidence is present and passing: package_static_check status=pass, codegen_contract_check status=pass with no errors or warnings, and compile_gate status=pass with returncode 0 for Compile/compile, GeneratedContractCheck, ElaborateGeneratedAccelerator, and ElaborateGeneratedAxiDdrTop.",
      "The candidate manifest reports target_model_artifact_status.current_artifacts_match_target=true and missing_for_target=[] for model_type=qwen2.",
      "Generated top parameters visible in the manifest bind hidden_size=896, intermediate_size=4864, lanes=8, max_seq_len=16, q_heads=14, kv_heads=2, and bits=32/16/32; these are covered by the passing contract check, not independently revalidated here.",
      "SACG memory truth has zero active contamination barriers and zero open retry/backtrack requests, so there is no current SACG-memory blocker for code_generation review.",
      "The generated package contains Chisel/Scala sources, generated SystemVerilog, top wrappers, AXI/DDR wrapper, memory_layout.json, runtime_config.json, contract checker source, filelist, and verification-layer SV stubs as listed in the manifest.",
      "The team handoff names cross-layer audit and handoff files that are not listed as generated_files in the candidate manifest: model_numeric_codegen_consistency_report.json, generated_params_shape_trace.json, numeric_policy_binding_trace.json, memory_runtime_codegen_audit.json, addr_map_alignment_report.json, runtime_abi_handoff_notes.json, template_codegen_audit.json, generated_source_to_template_trace.json, compile_gate_evidence_summary.json, checker_evidence_matrix.json, code_generation_stage_acceptance_decision.json, repair_or_handoff_boundary_record.json, and the compact code_generation.*_handoff.json records.",
      "Those missing handoff/audit files should be treated as downstream-consumption handoff actions, not as evidence that the current package or contract gate failed, because the current-stage package, compile, and contract gates all pass under the supplied stage_gate_policy.",
      "clock_target_mhz is 0 in generated_top/parameter_binding; the stage policy explicitly classifies a nonzero clock assignment as a later board-profile/tool-evidence or approval item, not a codegen compile-pass fact.",
      "No functional simulation, numeric golden comparison, AXI protocol validation, Vivado timing/resource closure, bitstream, or board-runtime evidence is supplied; codegen elaboration must not be represented as hardware correctness."
    ],
    "proposed_actions": [
      "Materialize the missing model/shape/numeric, memory/runtime, template/provenance, compile-evidence, and stage-acceptance handoff artifacts from the passing manifest and checker logs before promoting the candidate to downstream consumption.",
      "Preserve the candidate-only/evidence-boundary language: codegen is ready by current-stage gates, but functional simulation, numeric validation, Vivado implementation, timing, bitstream, and board runtime remain later-stage obligations.",
      "Hand off the accepted codegen package to verification only through a hierarchical verification artifact contract that enforces the required order: operator/leaf checks, then connected single-transformer-layer checks, then AXI/DDR wrapped-system checks.",
      "Start backend/app-shell target discovery only from cited board materials and real tool evidence; keep clock_target_mhz at 0 until evidence or bounded approval supports a nonzero target.",
      "Do not edit generated memory layout, runtime ABI, templates, numeric policy, or golden/tolerance settings to satisfy later checkers without bounded repair classification and the required approval when scope is exceeded."
    ],
    "risks": [
      "Downstream verification/backend agents may lose model-shape-numeric, template-provenance, memory-runtime, and checker-boundary traceability if the named handoff/audit files are not materialized before consumption.",
      "Memory layout and runtime config exist and passed static contract checks, but transfer counts, data order, address behavior, liveness, and AXI/DDR protocol behavior remain unproven until the later hierarchical verification and board-accurate checks run.",
      "The board clock/app-shell target remains unknown because clock_target_mhz=0; guessing a clock, shell port, target name, or timing target without cited board/Vivado evidence would violate the deployment and human-boundary constraints.",
      "Functional/numerical correctness of the Qwen2 single-layer accelerator is not established by the code_generation package; real leaf, single-transformer-layer, and wrapped-system simulations must still pass before backend or board claims.",
      "Any later fix that changes architecture, pipeline schedule, memory map, runtime ABI, data order, numeric policy, selected templates, or golden/tolerance policy would exceed bounded codegen handoff repair and require the approvals listed below."
    ],
    "sacg_focus": {
      "artifacts": [
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/code_generation_manifest.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/compile_check.json",
        "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/codegen_contract_check.json",
        "generated/chisel/logs/codegen_package_static_check.json",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/GeneratedAcceleratorTop.sv",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/filelist.f"
      ],
      "constraints": [
        "constraint.codegen.package",
        "constraint.codegen.compile_gate",
        "constraint.codegen.contract_check",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.deployment.board",
        "constraint.verification.plan",
        "constraint.human.boundary"
      ],
      "edges": [
        "model_shape_to_generated_params",
        "numeric_policy_to_generated_bits",
        "pipeline_plan_to_generated_arch_plan",
        "parameter_binding_to_generated_top_params",
        "template_sources_to_generated_chisel_modules",
        "generated_memory_layout_to_runtime_config",
        "runtime_config_to_axi_ddr_wrapper",
        "codegen_checker_logs_to_stage_acceptance_decision",
        "codegen_handoff_to_verification_artifact_contract",
        "target_board_profile_to_clock_and_app_shell_policy"
      ],
      "nodes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
        "generated.model_ir",
        "generated.arch_plan",
        "generated.chisel_modules",
        "generated.top_wrapper",
        "generated.fpga_axi_ddr_top_wrapper",
        "generated.memory_layout",
        "generated.runtime_config",
        "generated.codegen_compile_gate",
        "generated.codegen_contract_check",
        "generated.codegen_package_static_check",
        "artifact.stage6.verification_plan",
        "artifact.stage9.app_shell_integration_contract"
      ]
    },
    "schema_version": "spatialaccagent.code_generation_agent.review.v0",
    "stage": "code_generation",
    "status": "ready_with_handoff_actions",
    "summary": "The supplied code-generation candidate satisfies the visible current-stage gates: package static check passes, all four SBT compile/elaboration commands pass, codegen_contract_check passes, target Qwen2 artifacts match with no missing target outputs, and SACG memory truth reports no active barriers or open retry/backtrack requests. The missing items are not current-stage codegen gate failures; they are materialized cross-layer handoff/audit outputs needed before downstream verification/backend agents consume the candidate."
  },
  "llm_executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "parameter_binding_static_check",
        "codegen_contract_check"
      ],
      "action_type": "cross_layer_consistency_review",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
        "artifact.stage4.parameter_static_checks",
        "candidate_stage_artifact.generated_top",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.compile_gate",
        "state_summary.sacg_memory_truth"
      ],
      "id": "codegen.materialize_model_numeric_consistency_traces",
      "on_failure": "Block downstream code_generation evidence promotion. If the mismatch is local to generated parameter emission, route to bounded_template_repair/codegen regeneration; if stage3 or stage4 artifacts are the conflicting source, raise a stage_backtrack_request instead of editing generated outputs or loosening checks.",
      "produces": [
        "model_numeric_codegen_consistency_report.json",
        "generated_params_shape_trace.json",
        "numeric_policy_binding_trace.json"
      ],
      "rationale": "Create the missing model/shape/numeric trace artifacts from the supplied model, numeric policy, pipeline/parameter binding, generated_top parameters, and passing contract evidence so downstream agents consume checker-grounded parameter provenance instead of inferring it from the compact manifest.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "parameter_binding_static_check",
        "codegen_contract_check"
      ]
    },
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
      "consumes": [
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_protocols",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
        "generated/chisel/ram_1792x256.sv",
        "generated/chisel/ram_4x129.sv",
        "generated/chisel/logs/codegen_contract_check.json",
        "generated/chisel/logs/codegen_package_static_check.json",
        "generated/chisel/logs/compile_check.json"
      ],
      "id": "codegen.memory_runtime_static_handoff_check",
      "on_failure": "Block memory/runtime handoff promotion, preserve failing checker evidence, and route to bounded memory_runtime_repair with repair_boundary_check; do not silently change memory layout, runtime ABI, pipeline schedule, data order, or golden outputs.",
      "produces": [
        "memory_runtime_codegen_audit.json",
        "addr_map_alignment_report.json",
        "runtime_abi_handoff_notes.json"
      ],
      "rationale": "Materialize the missing memory/runtime handoff artifacts by binding memory_layout.json, runtime_config.json, generated AXI/DDR wrapper evidence, and the passed codegen check logs to the named memory/runtime/board constraints without inferring hidden field details from the compact summary.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "memory_runtime_plan_check",
        "stream_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "codegen_contract_check",
        "codegen_package_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "template_binding_static_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "codegen_package_static_check",
        "codegen_contract_check",
        "codegen_compile_gate_check"
      ],
      "action_type": "template_bound_artifact_review",
      "consumes": [
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.stage2.template_selection",
        "artifact.stage4.parameter_binding",
        "candidate_stage_artifact.generated_files",
        "candidate_stage_artifact.planned_code_outputs",
        "candidate_stage_artifact.generated_top",
        "candidate_stage_artifact.package_static_check",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.compile_gate"
      ],
      "id": "code_generation.finalize_template_bound_audit",
      "on_failure": "Treat the failure as a current-stage codegen handoff blocker. Invoke bounded_template_repair only for mismatches repairable within the existing template library and stage4 parameter binding; otherwise request backtrack or approval before changing templates, parameters, shapes, or numeric policy.",
      "produces": [
        "template_codegen_audit.json",
        "generated_source_to_template_trace.json",
        "compile_gate_evidence_summary.json"
      ],
      "rationale": "The supplied package_static_check, codegen_contract_check, and compile/elaboration gate pass; materialize the missing template provenance and compile-evidence artifacts so downstream consumers can distinguish template-bound generated RTL from unverified free-form assumptions.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "template_coverage_check",
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "codegen_package_static_check",
        "codegen_contract_check",
        "codegen_compile_gate"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "verification_action_audit_check",
        "required_real_tool_evidence_check",
        "codegen_contract_check",
        "codegen_package_static_check",
        "sacg_memory_check"
      ],
      "action_type": "evidence_gate_handoff",
      "consumes": [
        "model_numeric_codegen_consistency_report.json",
        "generated_params_shape_trace.json",
        "numeric_policy_binding_trace.json",
        "memory_runtime_codegen_audit.json",
        "addr_map_alignment_report.json",
        "runtime_abi_handoff_notes.json",
        "template_codegen_audit.json",
        "generated_source_to_template_trace.json",
        "compile_gate_evidence_summary.json",
        "candidate_stage_artifact.generated_top",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.package_static_check",
        "candidate_stage_artifact.compile_gate",
        "state_summary.sacg_memory_truth"
      ],
      "id": "code_generation.handoff_cross_layer_codegen_evidence",
      "on_failure": "Hold downstream promotion until handoff records cite checker logs, preserve SACG constraint links, and explicitly state that no functional simulation, timing, bitstream, or board pass is being claimed; do not bypass failed checkers.",
      "produces": [
        "code_generation.cross_layer_model_numeric_handoff.json",
        "code_generation.memory_runtime_package_handoff.json",
        "code_generation.evidence_gate_handoff.json",
        "code_generation_stage_acceptance_decision.json",
        "checker_evidence_matrix.json",
        "repair_or_handoff_boundary_record.json"
      ],
      "rationale": "Aggregate the newly materialized model/numeric, memory/runtime, template/provenance, compile, package, and contract evidence into the compact cross-layer records required by verification and backend agents, while explicitly preserving that later hardware/tool gates are unproven.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "team_aggregate",
        "sacg_reference_check",
        "verification_action_audit",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "case_stage_leaf_static",
        "boundary_contract_check"
      ],
      "action_type": "handoff_static_contract",
      "consumes": [
        "code_generation_stage_acceptance_decision.json",
        "checker_evidence_matrix.json",
        "generated/chisel/filelist.f",
        "generated/chisel/GeneratedAcceleratorTop.sv",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/verification/layers-GeneratedAcceleratorTop-Verification.sv",
        "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "artifact.input.case_adapter",
        "constraint.verification.plan"
      ],
      "id": "verification.build_hierarchical_artifact_contract",
      "on_failure": "Do not run functional simulation. Return failed contract evidence for bounded codegen/verification repair classification and preserve the three-layer verification order.",
      "produces": [
        "artifact.stage6.verification_plan",
        "artifact.stage6.verification_artifact_contract",
        "verification/boundary_contracts/operator_leaf_contracts.json",
        "verification/boundary_contracts/single_layer_contract.json",
        "verification/boundary_contracts/axi_ddr_contract.json"
      ],
      "rationale": "After code_generation handoff artifacts exist, convert the accepted package into a checker-grounded hierarchical verification plan before any real functional simulation or repair decision.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "case_stage_leaf_static",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.app_shell_target_discovery_contract",
        "backend_app_shell_target_discovery_check",
        "real_tool.app_shell_target_hint_synthesis",
        "real_tool.app_shell_target_discovery_after_hint",
        "backend_bounded_recovery_action_check",
        "human_boundary_check"
      ],
      "action_type": "target_discovery",
      "consumes": [
        "code_generation_stage_acceptance_decision.json",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/memory/memory_layout.json",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "constraint.deployment.board",
        "constraint.human.boundary"
      ],
      "id": "backend_board.discover_app_shell_target_and_clock_policy",
      "on_failure": "If target names, shell ports, memory interfaces, or clock evidence remain ambiguous, require bounded human/architecture approval and keep runtime bitstream and board runtime blocked.",
      "produces": [
        "artifact.stage9.app_shell_integration_contract",
        "artifact.stage9.app_shell_target_selection_decision",
        "backend_board/case_diagnostics/app_shell_target_discovery_contract.json",
        "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json",
        "target_discovery_policy_update.json"
      ],
      "rationale": "The generated_top clock_target_mhz is 0, so board/app-shell integration and any nonzero clock target must be derived from cited board materials and real tool evidence rather than guessed from codegen elaboration.",
      "requires_approval": false,
      "stage": "backend_board",
      "tool_roles": [
        "app_shell_target_discovery_contract",
        "app_shell_target_hint_synthesis",
        "app_shell_target_discovery_after_hint",
        "backend_bounded_recovery_action",
        "human_boundary_check"
      ]
    }
  ],
  "memory_layout": {
    "alignment_bytes": 64,
    "axi_data_width_bits": 512,
    "design_id": "qwen2_spatialacc_agent_run",
    "element_bits": {
      "block_input_bits": 32,
      "block_output_bits": 32,
      "internal_elem_bits": 16
    },
    "layout_policy": "aligned_static_regions_with_double_buffered_layer_weights",
    "num_layers": 24,
    "regions": [
      {
        "alignment_bytes": 64,
        "base_addr": 0,
        "meta": {
          "bits": 32,
          "hidden_size": 896,
          "seq_len": 16
        },
        "name": "input_tokens",
        "role": "activation_input",
        "size_bytes": 57344
      },
      {
        "alignment_bytes": 64,
        "base_addr": 57344,
        "meta": {
          "bits": 32,
          "hidden_size": 896,
          "seq_len": 16
        },
        "name": "output_tokens",
        "role": "activation_output",
        "size_bytes": 57344
      },
      {
        "alignment_bytes": 64,
        "base_addr": 114688,
        "meta": {
          "buffer": "ping"
        },
        "name": "activation_ping",
        "role": "activation_buffer",
        "size_bytes": 155648
      },
      {
        "alignment_bytes": 64,
        "base_addr": 270336,
        "meta": {
          "buffer": "pong"
        },
        "name": "activation_pong",
        "role": "activation_buffer",
        "size_bytes": 155648
      },
      {
        "alignment_bytes": 64,
        "base_addr": 425984,
        "meta": {
          "bits": 16,
          "double_buffer": "a"
        },
        "name": "weight_buffer_a",
        "role": "weight_buffer",
        "size_bytes": 29826048
      },
      {
        "alignment_bytes": 64,
        "base_addr": 30252032,
        "meta": {
          "bits": 16,
          "double_buffer": "b"
        },
        "name": "weight_buffer_b",
        "role": "weight_buffer",
        "size_bytes": 29826048
      },
      {
        "alignment_bytes": 64,
        "base_addr": 60078080,
        "meta": {
          "status_words": 16
        },
        "name": "runtime_status",
        "role": "runtime_status",
        "size_bytes": 64
      }
    ],
    "schema_version": "spatialaccagent.memory_layout.v0",
    "tensor_shape": {
      "head_dim": 64,
      "hidden_size": 896,
      "intermediate_size": 4864,
      "num_kv_heads": 2,
      "num_q_heads": 14,
      "seq_len": 16
    },
    "total_bytes": 60078144,
    "transfer_rules": [
      "all addresses are byte offsets from the accelerator DDR window base",
      "all transfer byte counts are aligned to axi_data_width_bits",
      "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes"
    ]
  },
  "outputs": {
    "code_generation_manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/code_generation_manifest.json",
    "compile_gate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/compile_check.json",
    "contract_check": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/logs/codegen_contract_check.json",
    "generated_code_package": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel",
    "llm_agent": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/llm/code_generation_agent_result.json",
    "memory_layout": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/memory/memory_layout.json",
    "runtime_config": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/runtime/runtime_config.json",
    "sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/sacg_state.json",
    "team_aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/team/team_aggregate.json",
    "team_subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/team/subtask_plan.json"
  },
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
    "schema_version": "spatialaccagent.codegen_package_static_check.v0",
    "status": "pass",
    "summary": "generated package manifest is structurally complete",
    "warnings": []
  },
  "planned_code_outputs": [
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
  ],
  "runtime_config": {
    "board": {
      "board_model": null,
      "board_name": "mimic_computer_v6.0",
      "board_name_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0\u677f\u5361\u4f7f\u7528\u6587\u6863.docx",
      "board_revision": "v6.0",
      "clock_frequency_hz": null,
      "evidence": [
        {
          "chunk_id": "board:000004",
          "excerpt": "\u6837\u4f8b\u5de5\u7a0b Vivado project \u4e2d\u7684\u5177\u4f53 part \u662f `xcvu9p_CIV-flgb2104-2-i`",
          "field": "fpga_part",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/vu9p_fpga_\u6837\u4f8b\u5de5\u7a0b.md"
        },
        {
          "excerpt": "<Option Name=\"Part\" Val=\"xcvu9p_CIV-flgb2104-2-i\"/>",
          "field": "fpga_part",
          "source": "/home/share/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr"
        }
      ],
      "fpga_device": "VU9P",
      "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
      "fpga_vendor": null,
      "resource_numbers": null
    },
    "chisel_top": "LlamaStyleBlock",
    "design_id": "qwen2_spatialacc_agent_run",
    "memory_layout": {
      "alignment_bytes": 64,
      "axi_data_width_bits": 512,
      "design_id": "qwen2_spatialacc_agent_run",
      "element_bits": {
        "block_input_bits": 32,
        "block_output_bits": 32,
        "internal_elem_bits": 16
      },
      "layout_policy": "aligned_static_regions_with_double_buffered_layer_weights",
      "num_layers": 24,
      "regions": [
        {
          "alignment_bytes": 64,
          "base_addr": 0,
          "meta": {
            "bits": 32,
            "hidden_size": 896,
            "seq_len": 16
          },
          "name": "input_tokens",
          "role": "activation_input",
          "size_bytes": 57344
        },
        {
          "alignment_bytes": 64,
          "base_addr": 57344,
          "meta": {
            "bits": 32,
            "hidden_size": 896,
            "seq_len": 16
          },
          "name": "output_tokens",
          "role": "activation_output",
          "size_bytes": 57344
        },
        {
          "alignment_bytes": 64,
          "base_addr": 114688,
          "meta": {
            "buffer": "ping"
          },
          "name": "activation_ping",
          "role": "activation_buffer",
          "size_bytes": 155648
        },
        {
          "alignment_bytes": 64,
          "base_addr": 270336,
          "meta": {
            "buffer": "pong"
          },
          "name": "activation_pong",
          "role": "activation_buffer",
          "size_bytes": 155648
        },
        {
          "alignment_bytes": 64,
          "base_addr": 425984,
          "meta": {
            "bits": 16,
            "double_buffer": "a"
          },
          "name": "weight_buffer_a",
          "role": "weight_buffer",
          "size_bytes": 29826048
        },
        {
          "alignment_bytes": 64,
          "base_addr": 30252032,
          "meta": {
            "bits": 16,
            "double_buffer": "b"
          },
          "name": "weight_buffer_b",
          "role": "weight_buffer",
          "size_bytes": 29826048
        },
        {
          "alignment_bytes": 64,
          "base_addr": 60078080,
          "meta": {
            "status_words": 16
          },
          "name": "runtime_status",
          "role": "runtime_status",
          "size_bytes": 64
        }
      ],
      "schema_version": "spatialaccagent.memory_layout.v0",
      "tensor_shape": {
        "head_dim": 64,
        "hidden_size": 896,
        "intermediate_size": 4864,
        "num_kv_heads": 2,
        "num_q_heads": 14,
        "seq_len": 16
      },
      "total_bytes": 60078144,
      "transfer_rules": [
        "all addresses are byte offsets from the accelerator DDR window base",
        "all transfer byte counts are aligned to axi_data_width_bits",
        "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes"
      ]
    },
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
    "pass_criteria": {
      "bit_exact_float_model": false,
      "required": [
        "no_deadlock",
        "done_asserted",
        "valid_output_bytes"
      ]
    },
    "run_sequence": [
      "load input_tokens",
      "load layer 0 weights into weight_buffer_a",
      "start accelerator",
      "prefetch next layer weights into inactive weight buffer while active layer computes",
      "poll runtime_status or done",
      "read output_tokens"
    ],
    "runtime_interface": {
      "board_run_command": "scripts/board/run_pyjm12_smoke.sh",
      "control_base_address": "0x3000000000",
      "control_protocol": "xdma_raw_register_and_ddr",
      "ctrl_base": "0x3000000000",
      "ddr_base": "0x2800000000",
      "ddr_base_address": "0x2800000000",
      "ddr_image_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
      "ddr_image_path_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
      "device_id_default": 1,
      "evidence": [
        {
          "chunk_id": "board:000003",
          "excerpt": "`control_protocol`: `xdma_raw_register_and_ddr`",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
        },
        {
          "chunk_id": "board:000003",
          "excerpt": "\u5f53\u524d\u5df2\u6709\u677f\u7ea7 smoke \u811a\u672c\uff1a```bash scripts/board/run_pyjm12_smoke.sh ```",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
        },
        {
          "chunk_id": "board:000003",
          "excerpt": "\u5f53\u524d\u5de5\u5177\u670d\u52a1\u5668\u4e3a `hyyuan@10.12.133.23`\uff1b\u9ed8\u8ba4 MIMIC runtime \u76ee\u5f55\uff1a`MIMIC_DIR = /home/test/mimic_driver_c6`\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
        },
        {
          "chunk_id": "board:000003",
          "excerpt": "\u9ed8\u8ba4 XDMA id\uff1a`XDMA_ID = 1`\u3002\u63a7\u5236\u5bc4\u5b58\u5668\u57fa\u5730\u5740\uff1a`CTRL_BASE = 0x3000000000`\u3002DDR \u6570\u636e\u57fa\u5730\u5740\uff1a`DDR_BASE = 0x2800000000`\u3002\u5f53\u524d\u793a\u4f8b\u8f93\u51fa\u7edd\u5bf9\u5730\u5740\uff1a`OUTPUT_ABS = 0x28092f1000`\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
        },
        {
          "chunk_id": "board:000003",
          "excerpt": "\u5f53\u524d DDR image \u9ed8\u8ba4\u4f4d\u7f6e\uff1a`/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin`\u3002",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/runtime_axi_ddr.md"
        }
      ],
      "mimic_dir": "/home/test/mimic_driver_c6",
      "output_abs": "0x28092f1000",
      "output_address_abs": "0x28092f1000",
      "output_size_bytes": null,
      "register_map": null,
      "remote_host": "hyyuan@10.12.133.23",
      "remote_port": 22,
      "runtime_dir": "/home/test/mimic_driver_c6",
      "xdma_id_default": 1
    },
    "schema_version": "spatialaccagent.runtime_config.v0",
    "top_module": "GeneratedAxiDdrTop"
  },
  "sacg_transition_id": "transition.0004",
  "schema_version": "spatialaccagent.code_generation_report.v0",
  "source_sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/parameter_binding/sacg_state.json",
  "stage": "code_generation",
  "status": "ready",
  "team_executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "parameter_binding_static_check",
        "codegen_contract_check"
      ],
      "action_type": "cross_layer_consistency_review",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
        "artifact.stage4.parameter_static_checks",
        "candidate_stage_artifact.generated_top",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.compile_gate"
      ],
      "id": "codegen.materialize_model_numeric_consistency_traces",
      "on_failure": "Block code_generation evidence-gate promotion. If the mismatch is local to generated parameters or supplied top selection, route to bounded_template_repair/codegen regeneration; if artifact.stage4.parameter_binding or artifact.stage3.pipeline_plan is the conflicting source, raise a stage_backtrack_request instead of editing generated outputs or loosening checks.",
      "produces": [
        "model_numeric_codegen_consistency_report.json",
        "generated_params_shape_trace.json",
        "numeric_policy_binding_trace.json"
      ],
      "rationale": "Create the auditor handoff artifacts from the supplied model_config, numeric_policy, pipeline/parameter binding, generated_top parameters, and passed contract evidence so the final evidence gate can consume a checker-grounded model/shape/numeric trace.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "parameter_binding_static_check",
        "codegen_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "codegen_package_static_check",
        "codegen_compile_gate_check",
        "codegen_contract_check",
        "code_generation_manifest_static_check"
      ],
      "action_type": "evidence_gate_handoff",
      "consumes": [
        "model_numeric_codegen_consistency_report.json",
        "generated_params_shape_trace.json",
        "numeric_policy_binding_trace.json",
        "candidate_stage_artifact.package_static_check",
        "candidate_stage_artifact.compile_gate",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.generated_top"
      ],
      "id": "codegen.evidence_gate_consume_model_numeric_audit",
      "on_failure": "Keep code_generation promotion blocked and rerun only the failing checker or request a bounded codegen-local repair; do not bypass the failed checker and do not modify golden outputs or tolerances.",
      "produces": [
        "code_generation.evidence_gate_auditor.model_numeric_handoff_record"
      ],
      "rationale": "Aggregate this model/numeric audit with compile, package, and contract gate evidence before downstream consumption, without treating later functional or hardware validation as already passed.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "team_aggregate",
        "codegen_package_static_check",
        "codegen_compile_gate",
        "codegen_contract_check"
      ]
    },
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
      "consumes": [
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_protocols",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedAxiDdrTop.scala",
        "generated/chisel/ram_1792x256.sv",
        "generated/chisel/ram_4x129.sv",
        "generated/chisel/logs/codegen_contract_check.json",
        "generated/chisel/logs/codegen_package_static_check.json",
        "generated/chisel/logs/compile_check.json"
      ],
      "id": "codegen.memory_runtime_static_handoff_check",
      "on_failure": "Block evidence-gate promotion for memory/runtime handoff, preserve the failing checker evidence, and route to bounded memory_runtime_repair with repair_boundary_check; do not loosen checks, alter golden outputs, or silently change pipeline/memory architecture.",
      "produces": [
        "memory_runtime_codegen_audit.json",
        "addr_map_alignment_report.json",
        "runtime_abi_handoff_notes.json"
      ],
      "rationale": "Produce the specialist handoff artifacts by binding the generated memory/runtime artifacts and wrapper evidence to the named SACG constraints, while recording standalone checker status instead of inferring field-level address or transfer details from the compact summary.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "memory_runtime_plan_check",
        "stream_plan_check",
        "addr_map_check",
        "transfer_count_check",
        "codegen_contract_check",
        "codegen_package_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "case_stage_leaf_static",
        "case_single_transformer_layer",
        "functional_sim",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "addr_map_check",
        "verification_artifact_contract_check"
      ],
      "action_type": "hierarchical_real_tool_planning_and_execution",
      "consumes": [
        "artifact.stage6.verification_plan",
        "artifact.stage6.verification_artifact_contract",
        "memory_runtime_codegen_audit.json",
        "addr_map_alignment_report.json",
        "runtime_abi_handoff_notes.json",
        "artifact.stage3.pipeline_plan",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/GeneratedAcceleratorTop.sv",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/ram_1792x256.sv",
        "generated/chisel/ram_4x129.sv"
      ],
      "id": "verification.hierarchical_memory_transfer_validation",
      "on_failure": "Stop at the failed layer, localize the earliest causal boundary/module using tool evidence and SACG constraints, enter bounded repair, and rerun the failed layer; do not skip to AXI/DDR wrapper or board runtime.",
      "produces": [
        "verification/case_diagnostics/memory_transfer_validation.json",
        "verification/case_diagnostics/addr_transfer_trace_report.json",
        "verification/case_diagnostics/deadlock_liveness_report.json"
      ],
      "rationale": "Validate transfer count, stream order, liveness, and address-map assumptions in the required layer order before any board-accurate wrapper claim: leaf/static boundaries first, connected single-transformer-layer checks second, and wrapper/system checks only after lower layers pass.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_stage_leaf_static",
        "case_single_transformer_layer",
        "functional_sim",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "addr_map_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_board_interface_discovery",
        "real_tool.case_axi_ddr_interface",
        "real_tool.case_axi_protocol_check",
        "real_tool.case_ddr_image_roundtrip",
        "real_tool.case_runtime_abi_check",
        "real_tool.case_runtime_bitstream",
        "required_real_tool_evidence_check",
        "deployment_board_check"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_protocols",
        "artifact.stage9.app_shell_integration_contract",
        "memory_runtime_codegen_audit.json",
        "addr_map_alignment_report.json",
        "runtime_abi_handoff_notes.json",
        "verification/case_diagnostics/memory_transfer_validation.json",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/GeneratedAxiDdrTop.sv"
      ],
      "id": "backend_board.memory_runtime_real_tool_closure",
      "on_failure": "Keep runtime bitstream and board runtime blocked, localize the failing interface/ABI/address boundary from tool evidence, and request bounded recovery or approval if app-shell targets or clock/runtime fields are ambiguous; do not modify memory layout, runtime ABI, or clock target without approval.",
      "produces": [
        "backend_board/case_diagnostics/board_interface_discovery.json",
        "backend_board/case_diagnostics/axi_ddr_interface_check.json",
        "backend_board/case_diagnostics/axi_protocol_check.json",
        "backend_board/case_diagnostics/ddr_image_roundtrip.json",
        "backend_board/case_diagnostics/runtime_abi_check.json",
        "backend_board/case_diagnostics/runtime_bitstream_report.json"
      ],
      "rationale": "After verification evidence passes, close the deployment boundary with real board/tool evidence for the generated memory layout, runtime ABI, and AXI/DDR wrapper rather than treating codegen elaboration as hardware validation.",
      "requires_approval": false,
      "stage": "backend_board",
      "tool_roles": [
        "case_board_interface_discovery",
        "case_axi_ddr_interface",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_runtime_abi_check",
        "case_runtime_bitstream"
      ]
    },
    {
      "acceptance_checkers": [
        "template_binding_static_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "codegen_package_static_check",
        "codegen_contract_check",
        "codegen_compile_gate_check"
      ],
      "action_type": "template_bound_artifact_review",
      "consumes": [
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.stage2.template_selection",
        "artifact.stage4.parameter_binding",
        "candidate_stage_artifact.generated_files",
        "candidate_stage_artifact.planned_code_outputs",
        "candidate_stage_artifact.generated_top",
        "candidate_stage_artifact.package_static_check",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.compile_gate"
      ],
      "id": "code_generation.finalize_template_bound_audit",
      "on_failure": "Treat the failure as a current-stage blocker; do not promote generated code. Invoke bounded_template_repair only for mismatches repairable within the existing template library and stage4 parameter binding; otherwise request backtrack or approval before changing templates, parameters, shapes, or numeric policy.",
      "produces": [
        "template_codegen_audit.json",
        "generated_source_to_template_trace.json",
        "compile_gate_evidence_summary.json"
      ],
      "rationale": "The supplied package_static_check, codegen_contract_check, and compile/elaboration gate all pass; materialize the expected audit and trace artifacts so downstream agents consume checker-grounded provenance rather than free-form RTL assumptions.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "template_coverage_check",
        "parameter_binding_static_check",
        "code_generation_manifest_static_check",
        "codegen_package_static_check",
        "codegen_contract_check",
        "codegen_compile_gate"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "verification_action_audit_check",
        "required_real_tool_evidence_check",
        "codegen_contract_check",
        "codegen_package_static_check"
      ],
      "action_type": "evidence_handoff",
      "consumes": [
        "template_codegen_audit.json",
        "generated_source_to_template_trace.json",
        "compile_gate_evidence_summary.json",
        "candidate_stage_artifact.generated_top",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.package_static_check"
      ],
      "id": "code_generation.handoff_template_codegen_evidence",
      "on_failure": "Hold downstream promotion until the handoff records cite the checker logs, preserve SACG constraint links, and explicitly state that no functional simulation, timing, bitstream, or board pass is being claimed.",
      "produces": [
        "code_generation.cross_layer_model_numeric_handoff.json",
        "code_generation.memory_runtime_package_handoff.json",
        "code_generation.evidence_gate_handoff.json"
      ],
      "rationale": "Downstream cross-layer model/numeric, memory/runtime, and evidence-gate agents need a compact handoff that preserves the template-provenance pass, structural package pass, and compile-only evidence boundary.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "team_aggregate",
        "sacg_reference_check",
        "verification_action_audit",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "code_generation_manifest_static_check",
        "codegen_compile_gate_check",
        "codegen_contract_check",
        "codegen_package_static_check",
        "required_real_tool_evidence_check",
        "repair_boundary_check",
        "human_boundary_check",
        "sacg_memory_check"
      ],
      "action_type": "checker_evidence_gate",
      "consumes": [
        "candidate_stage_artifact",
        "candidate_stage_artifact.compile_gate",
        "candidate_stage_artifact.contract_check",
        "candidate_stage_artifact.package_static_check",
        "state_summary.sacg_memory_truth",
        "constraint.codegen.package",
        "constraint.codegen.compile_gate",
        "constraint.codegen.contract_check",
        "constraint.verification.plan",
        "constraint.human.boundary"
      ],
      "id": "code_generation.accept_ready_evidence_matrix",
      "on_failure": "Quarantine the candidate stage artifact, open a bounded stage_retry_request or trust barrier, and do not promote to verification/backend consumers.",
      "produces": [
        "code_generation_stage_acceptance_decision.json",
        "checker_evidence_matrix.json",
        "repair_or_handoff_boundary_record.json"
      ],
      "rationale": "Emit the stage acceptance decision and evidence matrix from visible pass evidence while recording that later functional, backend, and board checks remain unproven.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "team_aggregate",
        "code_generation_manifest_static_check",
        "codegen_compile_gate",
        "codegen_contract_check",
        "codegen_package_static_check",
        "required_real_tool_evidence_check",
        "repair_boundary_check",
        "human_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "case_stage_leaf_static",
        "boundary_contract_check"
      ],
      "action_type": "handoff_static_contract",
      "consumes": [
        "code_generation_stage_acceptance_decision.json",
        "checker_evidence_matrix.json",
        "generated/chisel/filelist.f",
        "generated/chisel/GeneratedAcceleratorTop.sv",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/verification/layers-GeneratedAcceleratorTop-Verification.sv",
        "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "artifact.input.case_adapter",
        "constraint.verification.plan"
      ],
      "id": "verification.build_hierarchical_artifact_contract",
      "on_failure": "Do not run real functional simulation; return the failed contract evidence to the orchestrator for bounded codegen/verification repair classification.",
      "produces": [
        "artifact.stage6.verification_plan",
        "artifact.stage6.verification_artifact_contract",
        "verification/boundary_contracts/operator_leaf_contracts.json",
        "verification/boundary_contracts/single_layer_contract.json",
        "verification/boundary_contracts/axi_ddr_contract.json"
      ],
      "rationale": "Downstream verification must convert the accepted codegen package into a checker-grounded hierarchical verification plan before real simulation or repair decisions.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "hierarchical_verification_plan_check",
        "verification_artifact_contract_check",
        "sacg_reference_check",
        "case_stage_leaf_static",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_real_weight_artifacts",
        "artifact_hash_check",
        "numeric_compare"
      ],
      "action_type": "artifact_generation_and_hash_gate",
      "consumes": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.case_adapter",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/memory/memory_layout.json"
      ],
      "id": "verification.prepare_real_weight_and_golden_artifacts",
      "on_failure": "Classify the issue as checker/golden-reference/input-packing repair unless real RTL tool evidence identifies a hardware failure; do not alter tolerances or golden outputs without approved numeric-policy change.",
      "produces": [
        "verification/case_real_weights/input_manifest.json",
        "verification/case_real_weights/packed_weight_manifest.json",
        "verification/case_real_weights/golden_reference_manifest.json",
        "verification/case_real_weights/artifact_hashes.json"
      ],
      "rationale": "Real functional and numerical checks require reproducible input, packed weight, golden-reference, and hash manifests derived from the accepted model/numeric/runtime contracts.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_weight_manifest_generate",
        "case_real_weight_artifacts",
        "artifact_hash_check",
        "numeric_compare"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_leaf_functional",
        "real_tool.case_leaf_golden_compare",
        "real_tool.case_single_transformer_layer",
        "real_tool.case_single_layer_functional",
        "real_tool.case_single_layer_golden_compare",
        "real_tool.case_vcs_functional_sim",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "numeric_compare"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "artifact.stage6.verification_artifact_contract",
        "generated/chisel/filelist.f",
        "generated/chisel/GeneratedAcceleratorTop.sv",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/memory/memory_layout.json",
        "verification/case_real_weights/input_manifest.json",
        "verification/case_real_weights/packed_weight_manifest.json",
        "verification/case_real_weights/golden_reference_manifest.json"
      ],
      "id": "verification.run_layered_real_functional_simulation",
      "on_failure": "Stop at the earliest failed layer; route simulator output through boundary-contract-guided localization and causal repair context, then rerun only the targeted failed checker before promotion.",
      "produces": [
        "verification/case_diagnostics/leaf_functional_diagnosis.json",
        "verification/case_diagnostics/single_layer_functional_diagnosis.json",
        "verification/case_diagnostics/layered_numeric_compare.json",
        "verification/case_diagnostics/layered_liveness_trace.json"
      ],
      "rationale": "Enforce the three-layer verification loop after static contract and real-weight gates: operator/leaf modules first, connected single-transformer-layer second, and no promotion beyond the first failing layer.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "case_vcs_functional_sim",
        "case_vcs_evidence_analyzer",
        "deadlock_watchdog",
        "data_order_trace_check",
        "transfer_count_check",
        "numeric_compare"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_axi_ddr_interface",
        "real_tool.case_axi_protocol_check",
        "real_tool.case_ddr_image_roundtrip",
        "real_tool.case_deadlock_axi_check",
        "real_tool.case_verilator_functional_sim",
        "addr_map_check",
        "transfer_count_check",
        "data_order_trace_check"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "artifact.stage6.verification_artifact_contract",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/filelist.f",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "verification/case_real_weights/packed_weight_manifest.json",
        "verification/case_diagnostics/single_layer_functional_diagnosis.json"
      ],
      "id": "verification.run_board_accurate_axi_ddr_wrapper_checks",
      "on_failure": "Localize to the wrapper, runtime ABI, memory layout, or generated RTL boundary before any code repair; do not proceed to Vivado or board execution.",
      "produces": [
        "verification/case_diagnostics/axi_ddr_interface_check.json",
        "verification/case_diagnostics/axi_protocol_trace.json",
        "verification/case_diagnostics/ddr_image_roundtrip.json",
        "verification/case_diagnostics/axi_deadlock_diagnosis.json"
      ],
      "rationale": "After leaf and single-layer verification pass, validate the board-accurate AXI/DDR wrapped system against memory layout, runtime config, protocol, order, and liveness constraints before backend synthesis.",
      "requires_approval": false,
      "stage": "verification",
      "tool_roles": [
        "case_axi_ddr_interface",
        "case_axi_protocol_check",
        "case_ddr_image_roundtrip",
        "case_deadlock_axi_check",
        "case_verilator_functional_sim",
        "addr_map_check",
        "transfer_count_check",
        "data_order_trace_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.app_shell_target_discovery_contract",
        "backend_app_shell_target_discovery_check",
        "real_tool.app_shell_target_hint_synthesis",
        "real_tool.app_shell_target_discovery_after_hint",
        "backend_bounded_recovery_action_check",
        "human_boundary_check"
      ],
      "action_type": "target_discovery",
      "consumes": [
        "code_generation_stage_acceptance_decision.json",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/memory/memory_layout.json",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "constraint.deployment.board",
        "constraint.human.boundary"
      ],
      "id": "backend_board.discover_app_shell_target_and_clock_policy",
      "on_failure": "If target names, shell ports, memory interfaces, or clock evidence remain ambiguous, require bounded human/architecture approval and keep runtime bitstream and board runtime blocked.",
      "produces": [
        "artifact.stage9.app_shell_integration_contract",
        "artifact.stage9.app_shell_target_selection_decision",
        "backend_board/case_diagnostics/app_shell_target_discovery_contract.json",
        "backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json",
        "target_discovery_policy_update.json"
      ],
      "rationale": "Board/app-shell integration must be synthesized from cited board materials and real tool evidence; clock_target_mhz is currently unknown and must not be guessed.",
      "requires_approval": false,
      "stage": "backend_board",
      "tool_roles": [
        "app_shell_target_discovery_contract",
        "app_shell_target_hint_synthesis",
        "app_shell_target_discovery_after_hint",
        "backend_bounded_recovery_action",
        "human_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_board_shell_wrapper_generate",
        "implementation_package_static",
        "real_tool.case_vivado_synthesis",
        "real_tool.case_vivado_synthesis_report_check",
        "real_tool.case_vivado_implementation",
        "real_tool.case_vivado_implementation_report_check",
        "timing_resource_check",
        "deployment_board_check"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "artifact.stage9.app_shell_integration_contract",
        "artifact.stage9.app_shell_target_selection_decision",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/filelist.f",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/memory/memory_layout.json",
        "verification/case_diagnostics/axi_ddr_interface_check.json"
      ],
      "id": "backend_board.run_vivado_synthesis_implementation_after_verification",
      "on_failure": "Route real Vivado evidence to backend bounded recovery or architecture review; do not bypass DRC/timing failures or represent them as code_generation pass evidence.",
      "produces": [
        "backend_board/case_diagnostics/vivado_synthesis_report.json",
        "backend_board/case_diagnostics/vivado_implementation_report.json",
        "backend_board/timing_resource_summary.json",
        "backend_board/implementation_package_static.json"
      ],
      "rationale": "Vivado synthesis, implementation, and timing/resource reports are later-stage real-tool evidence and must not be inferred from Chisel compile/elaboration success.",
      "requires_approval": false,
      "stage": "backend_board",
      "tool_roles": [
        "case_board_shell_wrapper_generate",
        "implementation_package_static",
        "case_vivado_synthesis",
        "case_vivado_synthesis_report_check",
        "case_vivado_implementation",
        "case_vivado_implementation_report_check",
        "timing_resource_check"
      ]
    },
    {
      "acceptance_checkers": [
        "real_tool.case_runtime_abi_check",
        "real_tool.case_runtime_bitstream",
        "real_tool.app_shell_runtime_bitstream",
        "real_tool.board_runtime",
        "output_validity_check",
        "deployment_board_check"
      ],
      "action_type": "real_tool_execution",
      "consumes": [
        "backend_board/case_diagnostics/vivado_implementation_report.json",
        "backend_board/timing_resource_summary.json",
        "artifact.stage9.app_shell_integration_contract",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/memory/memory_layout.json",
        "verification/case_real_weights/packed_weight_manifest.json",
        "verification/case_real_weights/golden_reference_manifest.json"
      ],
      "id": "backend_board.run_runtime_bitstream_and_output_validity",
      "on_failure": "Localize the board/runtime/interface boundary using real tool output, then open bounded recovery or backtrack; do not claim hardware pass.",
      "produces": [
        "backend_board/case_diagnostics/runtime_abi_check.json",
        "backend_board/case_diagnostics/runtime_bitstream_check.json",
        "backend_board/case_diagnostics/board_runtime_output_validity.json"
      ],
      "rationale": "Only board runtime, runtime ABI, bitstream, and output-validity evidence can support a board-level pass claim.",
      "requires_approval": false,
      "stage": "backend_board",
      "tool_roles": [
        "case_runtime_abi_check",
        "case_runtime_bitstream",
        "app_shell_runtime_bitstream",
        "board_runtime",
        "output_validity_check"
      ]
    }
  ]
}
</recent_stage_summary>

<command>
[
  "/home/remote/miniconda3/bin/python3",
  "-m",
  "accagent.framework.stage_code_generation",
  "--sacg-state",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/parameter_binding/sacg_state.json"
]
</command>

<command_returncode>
0
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/agent/logs/35_code_generation.json
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
}
</sacg_memory>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/code_generation/sacg_state.json
</source_sacg_state>

<flow_policy>
{
  "bounded_attempts_per_stage": 2,
  "bounded_total_backtracks": 6,
  "do_not_use_failed_artifacts_as_validated_downstream_inputs": true,
  "honor_backtrack_requests_before_downstream_progress": true,
  "llm_is_required": true,
  "prefer_retry_same_stage_for_retry_requests": true
}
</flow_policy>

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
