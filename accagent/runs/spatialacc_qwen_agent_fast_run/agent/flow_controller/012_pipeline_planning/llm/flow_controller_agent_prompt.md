<agent>
flow_controller_agent
</agent>

<task>
Review SACG memory and the latest stage result, then decide whether the autonomous design team should proceed, retry the current stage, backtrack to an earlier stage, run bounded repair, or stop to avoid artifact contamination.
</task>

<rules>
1. Review only the supplied artifact summary and named constraints.
2. Treat sacg_memory as the shared long-context design memory: preserve design goals, failure lessons, retry requests, backtrack requests, and contamination barriers.
3. If sacg_memory contains open backtrack_requests or contamination_barriers relevant to this stage, address them explicitly in observations and executable_actions.
4. If inputs include a retry_reconciliation_contract for the current stage, distinguish previous failed artifacts from the candidate retry artifacts: same-stage retry requests/barriers are downstream-consumption blockers until promotion, but they are not independent blockers for approving a refined current-stage contract that explicitly supersedes them after all current-stage checks pass.
5. If inputs include stage_gate_policy, use it to classify current-stage blocking risks versus later-stage actions.
6. If inputs include role_slice_policy or presence_summary, do not infer a field is missing merely because detailed rows were omitted from a compact/role-specific prompt slice.
7. When presence_summary says an artifact class exists, report missing-detail concerns as handoff/action items unless the visible checker status proves a current-stage blocker.
8. Report cross-layer consistency risks across model, shape, numeric policy, data order, memory, runtime, implementation, and board facts.
9. Keep actions bounded and executable by later tools/checkers.
10. Populate executable_actions with concrete next tool/repair actions; each action must name consumed artifacts, produced artifacts, tool roles, acceptance checkers, failure handling, and approval need.
11. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
12. For backend/app-shell target discovery, treat the LLM as the adaptive board-integration engineer: convert supplied board materials and real Vivado evidence into target_discovery_policy updates with cited artifacts; if evidence is ambiguous, require bounded approval instead of guessing names.
13. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name> and state the implementation gap in rationale.
14. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
15. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
16. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
17. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
18. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
</rules>

<current_stage>
pipeline_planning
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
  "checker_summary": {
    "errors": [],
    "failed": 0,
    "passed": 10,
    "warnings": []
  },
  "design_team": {
    "action_normalization": {
      "alias_rewrites": [
        {
          "action_id": "verification.run_hierarchical_stream_order_count_deadlock_checks",
          "from": "case_deadlock_axi_check",
          "to": "real_tool.case_deadlock_axi_check"
        }
      ],
      "duplicate_actions_removed": 0,
      "policy": "Normalize team executable action checker names before LLM architect review and SACG commit; this does not change pipeline semantics.",
      "schema_version": "spatialaccagent.stage3_action_normalization.v0"
    },
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/team_aggregate.json",
    "approval_required_for": [
      "Any ambiguous backend/app-shell target selection without cited board materials and real Vivado/tool evidence.",
      "Any architecture or pipeline-topology change beyond the checker-backed operator_stream_pipeline and operator order.",
      "Any architecture, pipeline, memory-layout, or board/runtime contract change needed to resolve a numeric/template binding failure.",
      "Any attempt to reinterpret symbolic_first_order latency as timing, throughput, or hardware-pass evidence.",
      "Any change to the current numeric policy: activation_bits=16, weight_bits=16, scale_bits=16, accumulator_bits=32, rounding=nearest_even, saturation=false.",
      "Any major template substitution or free-form RTL generation outside the trusted template library.",
      "Any memory-layout or AXI/DDR address-map change that departs from the checker-backed board/runtime constraints or requires a new memory policy.",
      "Any numeric precision, rounding, saturation, tolerance, or golden-output change.",
      "Any replacement of selected trusted templates or major change to the template library/template metadata.",
      "changes to AXI data width, address width, WSTRB width, or 64-byte alignment",
      "changes to XDMA device index, control/status base apertures, or raw register/DDR runtime protocol",
      "changes to numeric element widths, accumulator widths, target sequence length, hidden size, intermediate size, or stream lane count that alter transfer counts",
      "changes to the double-buffered weight or activation ping/pong policy",
      "changing GQA head counts, group size, RoPE policy, causal mask policy, or seq_len_bound",
      "changing decoder operator order or adding/removing stages",
      "changing numeric policy, element widths, rounding, saturation, or data-order/transfer-unit policy",
      "changing residual skip sources, join fire rules, or MLP split/join topology",
      "concrete DDR base-address assignment or any change to the six-region memory layout",
      "finalizing or changing memory layout, base addresses, runtime sequence policy, or external KV-cache materialization",
      "introducing new templates, replacing trusted template bindings, or allowing free-form RTL generation",
      "major template changes or any replacement of trusted_queue_template/operator templates with unapproved free-form RTL",
      "memory layout, base address, AXI beat-width, alignment, or transfer-count policy changes",
      "numeric precision, rounding, saturation, or accumulator policy changes",
      "pipeline topology, edge ID, transfer_order, or branch/join contract changes beyond preserving the reviewed semantics"
    ],
    "completed_subtasks": 5,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "tool_protocol_check",
          "deployment_board_check",
          "sacg_static_check"
        ],
        "action_type": "checker_gate",
        "consumes": [
          "candidate_stage_artifact.memory_schedule",
          "candidate_stage_artifact.data_edges",
          "candidate_stage_artifact.stream_edges",
          "candidate_stage_artifact.stage_gate_policy",
          "artifact.input.target_board_profile",
          "artifact.input.tool_protocols",
          "artifact.input.tool_profile",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.deployment.board",
          "constraint.tool.protocols",
          "constraint.cross_layer.input_consistency"
        ],
        "id": "pipeline_planning.memory_runtime_exact_checker_gate",
        "on_failure": "Keep the candidate in pipeline_planning, route the failing constraints to memory_runtime_repair or pipeline_repair as appropriate, and rerun only the failed bounded checker set before handoff; do not promote to parameter binding or code generation.",
        "produces": [
          "artifact.pipeline_planning.memory_runtime_review",
          "pipeline_planning/checker_reports/memory_runtime_plan_check.json",
          "pipeline_planning/checker_reports/addr_map_check.boundary_mode.json",
          "pipeline_planning/checker_reports/transfer_count_check.json",
          "pipeline_planning/checker_reports/tool_protocol_check.json",
          "pipeline_planning/checker_reports/deployment_board_check.json",
          "pipeline_planning/checker_reports/sacg_static_check.json"
        ],
        "rationale": "Bind this memory/runtime review to the exact registry checkers requested for the role, including DDR region completeness, AXI width/alignment, transfer-count formulas, runtime tool protocol, deployment-board constraints, and SACG consistency. This action reconciles the visible planning-level memory_runtime_contract_check result with the registry checker names without claiming hardware evidence.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "tool_protocol_check",
          "deployment_board_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "transfer_count_check"
        ],
        "action_type": "parameter_binding",
        "consumes": [
          "artifact.pipeline_planning.memory_runtime_review",
          "candidate_stage_artifact.stages",
          "candidate_stage_artifact.stream_edges",
          "candidate_stage_artifact.numeric_stream_policy",
          "artifact.stage2.template_selection",
          "artifact.input.template_metadata",
          "artifact.input.numeric_policy"
        ],
        "id": "stage4.bind_stream_axi_memory_parameters",
        "on_failure": "Block code generation, localize the mismatch to the affected stage/edge/template parameter, repair within approved template-parameter bounds, and rerun the same checkers.",
        "produces": [
          "artifact.stage4.parameter_binding.memory_stream_axi_contract",
          "stage4/checker_reports/parameter_binding_static_check.json",
          "stage4/checker_reports/stream_plan_check.json",
          "stage4/checker_reports/transfer_count_check.json"
        ],
        "rationale": "Materialize the planning-level consistency into implementation parameters so template-bound stream widths, lane count, element widths, AXI packing, and transfer-order contracts cannot drift from data_edges.transfer_count_bytes.",
        "requires_approval": false,
        "stage": "parameter_binding",
        "tool_roles": [
          "parameter_binding_static_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "transfer_count_check"
        ]
      },
      {
        "acceptance_checkers": [
          "addr_map_check",
          "deployment_board_check",
          "tool_protocol_check",
          "case_runtime_abi_check",
          "memory_runtime_plan_check"
        ],
        "action_type": "address_map_and_runtime_abi_generation",
        "consumes": [
          "artifact.pipeline_planning.memory_runtime_review",
          "artifact.stage4.parameter_binding.memory_stream_axi_contract",
          "artifact.input.target_board_profile",
          "artifact.input.tool_protocols",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.deployment.board"
        ],
        "id": "stage5.generate_concrete_ddr_addr_map_and_runtime_abi",
        "on_failure": "Do not guess addresses or device names. If the target profile or board apertures are ambiguous, request bounded approval; otherwise route to memory_runtime_repair and rerun addr_map_check and case_runtime_abi_check before RTL/backend consumption.",
        "produces": [
          "artifact.stage5.concrete_ddr_addr_map",
          "artifact.stage5.runtime_abi_contract",
          "generated/chisel/runtime/runtime_config.json",
          "stage5/checker_reports/addr_map_check.json",
          "stage5/checker_reports/case_runtime_abi_check.json"
        ],
        "rationale": "Concrete DDR base addresses and runtime ABI must be generated after planning from the six required regions, 64-byte alignment, board/control apertures, and XDMA requirements. This preserves the Stage 3 boundary while creating the artifact needed by generated RTL and host runtime.",
        "requires_approval": true,
        "stage": "implementation",
        "tool_roles": [
          "addr_map_check",
          "deployment_board_check",
          "tool_protocol_check",
          "case_runtime_abi_check",
          "memory_runtime_plan_check"
        ]
      },
      {
        "acceptance_checkers": [
          "case_real_weight_artifacts",
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "verification_plan_static_check"
        ],
        "action_type": "memory_schedule_materialization",
        "consumes": [
          "artifact.pipeline_planning.memory_runtime_review",
          "artifact.stage4.parameter_binding.memory_stream_axi_contract",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.target_board_profile"
        ],
        "id": "stage5.generate_weight_activation_double_buffer_manifest",
        "on_failure": "Block runtime ABI and code generation consumption of weights, localize the failing section or buffer transition, repair the manifest/schedule within the approved memory contract, and rerun weight, transfer-count, and address-map checks.",
        "produces": [
          "artifact.stage5.packed_weight_manifest",
          "artifact.stage5.double_buffer_schedule",
          "stage5/checker_reports/case_real_weight_artifacts.json",
          "stage5/checker_reports/transfer_count_check.weights.json"
        ],
        "rationale": "The planning artifact states double-buffered weights and activation ping/pong regions; implementation needs an explicit per-layer packed weight manifest and active/inactive buffer schedule to prove no read/write aliasing during prefetch, compute, and output readback.",
        "requires_approval": false,
        "stage": "implementation",
        "tool_roles": [
          "case_weight_manifest_generate",
          "memory_runtime_plan_check",
          "addr_map_check",
          "verification_plan_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "real_tool.case_axi_ddr_interface",
          "real_tool.case_axi_protocol_check",
          "real_tool.case_ddr_image_roundtrip",
          "real_tool.case_runtime_abi_check",
          "real_tool.board_runtime"
        ],
        "action_type": "real_tool_execution",
        "consumes": [
          "artifact.stage5.concrete_ddr_addr_map",
          "artifact.stage5.runtime_abi_contract",
          "artifact.stage5.double_buffer_schedule",
          "generated/chisel/runtime/runtime_config.json",
          "artifact.stage6.verification_artifact_contract",
          "verification/case_real_weights/packed_weight_manifest.json"
        ],
        "id": "stage6plus.run_axi_ddr_xdma_runtime_evidence_after_lower_layers",
        "on_failure": "Do not promote to hardware pass. Feed real tool output into contract-guided localization at the earliest causal boundary, repair only within the bounded template/address/runtime contract, and rerun the failed layer before any higher-layer or board claim.",
        "produces": [
          "verification/case_diagnostics/axi_ddr_interface_report.json",
          "verification/case_diagnostics/axi_protocol_report.json",
          "verification/case_diagnostics/ddr_image_roundtrip_report.json",
          "verification/case_diagnostics/runtime_abi_report.json",
          "verification/case_diagnostics/board_runtime_report.json"
        ],
        "rationale": "Real hardware/runtime claims require board-accurate AXI/DDR and XDMA evidence after lower verification layers pass. This action enforces the three-layer repair loop by requiring operator/leaf and connected single-transformer-layer evidence before board-accurate wrapped-system execution.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_runtime_abi_check",
          "board_runtime"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "model_config_check",
          "stream_plan_check",
          "template_binding_static_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "candidate_stage_artifact.pipeline_plan",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.stage2.template_selection",
          "constraint.model.decoder",
          "constraint.shape.model",
          "constraint.cross_layer.input_consistency",
          "constraint.template.library",
          "sacg_memory"
        ],
        "id": "pp_audit_attach_model_pipeline_review",
        "on_failure": "Block promotion to downstream stages. If a semantic, shape, stream, or template-boundary mismatch is found, route to pipeline_repair or architecture_review with the violated SACG constraints; do not modify golden outputs, loosen tolerances, or claim hardware pass.",
        "produces": [
          "artifact.pipeline_planning.model_pipeline_review",
          "operator/stage boundary findings mapped to SACG constraints",
          "handoff notes for model-shape or operator-order repair boundaries"
        ],
        "rationale": "Bind the model-shape semantic audit to the named SACG constraints and require the exact current-stage acceptance checkers before downstream promotion. This distinguishes semantic review from hardware proof and avoids consuming lower-level checker evidence as a substitute for the stage gate.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "sacg_validate",
          "sacg_static_check",
          "model_config_check",
          "stream_plan_check",
          "parameter_binding_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "template_binding_static_check",
          "numeric_policy_check",
          "model_config_check"
        ],
        "action_type": "template_parameter_binding_handoff",
        "consumes": [
          "artifact.pipeline_planning.model_pipeline_review",
          "candidate_stage_artifact.pipeline_plan",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata"
        ],
        "id": "pp_to_stage4_parameter_binding_guard",
        "on_failure": "Return to pipeline_planning with a bounded repair request. Any change to operator order, branch topology, numeric policy, or template boundary requires approval; do not introduce free-form RTL.",
        "produces": [
          "artifact.stage4.template_parameter_binding_contract",
          "template-bound operator parameter map for the decoder block"
        ],
        "rationale": "Ensure the refined pipeline contract is converted into template parameters without changing operator order or stage boundaries, including Qwen2 RMSNorm parameters, causal GQA/RoPE fields, residual source ports, gated MLP activation/multiply behavior, hidden/intermediate widths, element widths, and token/tile/lane/word order.",
        "requires_approval": false,
        "stage": "parameter_binding",
        "tool_roles": [
          "parameter_binding_static_check",
          "template_coverage_check",
          "numeric_policy_check",
          "model_config_check"
        ]
      },
      {
        "acceptance_checkers": [
          "boundary_contract_check",
          "verification_plan_static_check",
          "hierarchical_verification_plan_check",
          "sacg_reference_check"
        ],
        "action_type": "verification_plan_static_handoff",
        "consumes": [
          "artifact.pipeline_planning.model_pipeline_review",
          "artifact.stage4.template_parameter_binding_contract",
          "constraint.case.adapter",
          "constraint.tool.protocols"
        ],
        "id": "pp_generate_boundary_contracts_for_hierarchical_verification",
        "on_failure": "Keep verification and backend blocked. If a verifier capability is missing, classify it as a checker/golden-reference repair; if a real tool later reports liveness, value, order, or protocol failure, localize the earliest causal boundary before any code repair.",
        "produces": [
          "artifact.stage6.verification_artifact_contract",
          "SACG-referenced boundary contracts for leaf modules and the single decoder block"
        ],
        "rationale": "Prepare downstream checkers to verify the same semantics at bounded boundaries: RMSNorm leaf, attention leaf, residual leaf, gated MLP elementwise/projection leaves, the connected single decoder block, and later the board-accurate AXI/DDR system. This preserves the required three-layer repair loop and prevents hardware claims from static planning evidence.",
        "requires_approval": false,
        "stage": "verification_planning",
        "tool_roles": [
          "boundary_contract_generate",
          "verification_plan_static_check",
          "hierarchical_verification_plan_check",
          "sacg_reference_check"
        ]
      },
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check"
        ],
        "action_type": "memory_runtime_plan",
        "consumes": [
          "artifact.pipeline_planning.model_pipeline_review",
          "candidate_stage_artifact.memory_schedule",
          "candidate_stage_artifact.attention_contract",
          "constraint.memory.board",
          "constraint.runtime.board"
        ],
        "id": "pp_memory_runtime_handoff_for_seq_and_kv_bounds",
        "on_failure": "Block code generation and backend use of the memory map. Invoke memory_runtime_repair with cited SACG constraints; changes to memory layout or KV-cache policy require approval.",
        "produces": [
          "artifact.stage5.memory_runtime_layout_contract",
          "runtime transfer-count and sequence-bound check records"
        ],
        "rationale": "Finalize the later memory/runtime contract for target_seq_len<=16, transfer counts, base address assignment, and any external KV-cache materialization without changing the current operator-stream semantics.",
        "requires_approval": true,
        "stage": "memory_layout",
        "tool_roles": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check"
        ]
      },
      {
        "acceptance_checkers": [
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check",
          "sacg_static_check"
        ],
        "action_type": "template_binding_review",
        "consumes": [
          "candidate_stage_artifact",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.stage2.template_selection",
          "constraint.numeric.policy",
          "constraint.template.library",
          "constraint.parameter.binding",
          "constraint.arch.design_space",
          "candidate_stage_artifact.checker_results"
        ],
        "id": "pipeline_planning.run_numeric_template_acceptance_gate",
        "on_failure": "Do not promote the pipeline plan. Localize the failed numeric/template field and route to bounded_template_repair; do not modify golden outputs, loosen tolerance, or bypass the failed checker.",
        "produces": [
          "artifact.pipeline_planning.numeric_template_review",
          "per-stage numeric/template binding matrix",
          "checker_results.numeric_policy_check",
          "checker_results.template_coverage_check",
          "checker_results.parameter_binding_static_check",
          "checker_results.sacg_static_check"
        ],
        "rationale": "Complete the current-stage acceptance evidence by checking the candidate pipeline plan against the numeric policy, selected template library, template metadata, Stage 2 template selection, and SACG constraints. The candidate has a passing template_binding_static_check, but the required numeric_policy_check, template_coverage_check, parameter_binding_static_check, and sacg_static_check evidence is not visible.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "repair_boundary_check",
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check",
          "sacg_static_check"
        ],
        "action_type": "bounded_repair",
        "consumes": [
          "artifact.pipeline_planning.numeric_template_review",
          "checker_results.numeric_policy_check",
          "checker_results.template_coverage_check",
          "checker_results.parameter_binding_static_check",
          "checker_results.template_binding_static_check",
          "checker_results.sacg_static_check",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.stage2.template_selection",
          "candidate_stage_artifact"
        ],
        "id": "pipeline_planning.repair_numeric_template_binding_if_gate_fails",
        "on_failure": "Keep promotion blocked. If repair requires changing numeric policy, replacing trusted templates, changing architecture/pipeline structure, or changing memory layout, emit a stage_backtrack_request and require explicit approval.",
        "produces": [
          "candidate_stage_artifact.refined_pipeline_plan",
          "bounded repair notes for missing or inconsistent template parameters",
          "updated per-stage numeric/template binding matrix"
        ],
        "rationale": "If the acceptance gate identifies missing or inconsistent numeric/template bindings, repair only bounded contract fields such as per-stage rounding/saturation inheritance, FFN role parameters, elementwise activation/multiply selector, GQA bindings, tensor dimensions, lane/tile bindings, stream widths, or accumulator declarations while staying inside the trusted template library.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "bounded_template_repair",
          "pipeline_repair",
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "code_generation_manifest_static_check",
          "codegen_contract_check",
          "codegen_package_static_check",
          "template_binding_static_check",
          "numeric_policy_check"
        ],
        "action_type": "handoff_contract_generation",
        "consumes": [
          "artifact.pipeline_planning.numeric_template_review",
          "candidate_stage_artifact",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "constraint.numeric.policy",
          "constraint.template.library",
          "constraint.parameter.binding",
          "constraint.arch.design_space"
        ],
        "id": "pipeline_planning.prepare_stage4_parameter_binding_handoff",
        "on_failure": "Keep Stage 4 code generation blocked and route the failed manifest fields back to bounded template/parameter repair; do not emit or consume RTL generated from an unverified manifest.",
        "produces": [
          "artifact.stage4.parameter_binding_manifest",
          "artifact.stage4.code_generation_manifest",
          "artifact.stage4.template_bound_numeric_contract"
        ],
        "rationale": "After all current-stage numeric/template gates pass, materialize the final per-template parameter and code-generation manifest so Stage 4 cannot drift from the checked numeric policy, stage bit widths, accumulator policy, attention parameters, stream order, buffer depths, and AXI transfer contracts.",
        "requires_approval": false,
        "stage": "stage4_parameter_binding",
        "tool_roles": [
          "parameter_binding_static_check",
          "code_generation_manifest_static_check",
          "codegen_contract_check",
          "codegen_package_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check",
          "sacg_static_check"
        ],
        "action_type": "sacg_memory_update",
        "consumes": [
          "artifact.pipeline_planning.numeric_template_review",
          "sacg_memory"
        ],
        "id": "pipeline_planning.record_numeric_template_review_in_sacg_memory",
        "on_failure": "Do not promote the review artifact until SACG memory is updated and validated without dropping any retry, backtrack, contamination, or failure-lesson state.",
        "produces": [
          "sacg_memory.updated",
          "handoff note for pipeline_planning.evidence_gate_auditor"
        ],
        "rationale": "Persist the numeric/template review result, the per-stage binding matrix, and the explicit absence of open retry, backtrack, or contamination barriers into SACG memory for the pipeline_planning.evidence_gate_auditor handoff.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "sacg_memory_update",
          "sacg_validate"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "stream_plan_check",
          "data_order_trace_check",
          "transfer_count_check",
          "deadlock_watchdog",
          "boundary_contract_check"
        ],
        "action_type": "cross_layer_rule_review",
        "consumes": [
          "candidate_stage_artifact.data_edges",
          "candidate_stage_artifact.stream_edges",
          "candidate_stage_artifact.branch_join_contracts",
          "candidate_stage_artifact.buffer_plan",
          "candidate_stage_artifact.flow_control",
          "candidate_stage_artifact.memory_schedule",
          "candidate_stage_artifact.checker_results",
          "constraint.stream.order",
          "constraint.beat.pipeline",
          "constraint.liveness.pipeline",
          "constraint.cross_layer.input_consistency"
        ],
        "id": "pipeline_planning.emit_stream_liveness_review_acceptance_bundle",
        "on_failure": "Block pipeline_planning promotion; attach failed edge_id, buffer_id, checker name, and violated SACG constraint, then route to pipeline_repair or memory_runtime_repair without changing golden outputs or tolerances.",
        "produces": [
          "artifact.pipeline_planning.stream_liveness_review",
          "edge-by-edge stream/beat audit table",
          "branch/join and buffer liveness findings mapped to edge_id and buffer_id"
        ],
        "rationale": "Bind the supplied candidate stream, beat, branch/join, buffer, and liveness evidence to SACG constraints and produce the expected current-stage review artifacts before evidence-gate consumption.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "sacg_static_check",
          "stream_plan_check",
          "data_order_trace_check",
          "transfer_count_check",
          "deadlock_watchdog",
          "boundary_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "boundary_contract_check",
          "stream_plan_check",
          "data_order_trace_check"
        ],
        "action_type": "template_parameter_binding_handoff",
        "consumes": [
          "artifact.pipeline_planning.stream_liveness_review",
          "candidate_stage_artifact.branch_join_contracts",
          "candidate_stage_artifact.buffer_plan",
          "candidate_stage_artifact.stream_edges",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.stage2.template_selection"
        ],
        "id": "template_binding.preserve_stream_join_and_residual_port_contracts",
        "on_failure": "Block code generation; localize the mismatch to the affected edge_id or template port. If repair changes pipeline topology, edge order, residual duplication semantics, or template boundaries, request architecture/pipeline approval before rerun.",
        "produces": [
          "artifact.stage4.boundary_contracts.stream_port_bindings",
          "artifact.stage4.parameter_binding_stream_constraints"
        ],
        "rationale": "Ensure the template-bound implementation preserves the reviewed stream order, transfer counts, join pairing keys, residual-skip semantics, and bounded FIFO choices without introducing free-form RTL changes.",
        "requires_approval": false,
        "stage": "template_binding",
        "tool_roles": [
          "parameter_binding_static_check",
          "boundary_contract_generate",
          "stream_plan_check"
        ]
      },
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "transfer_count_check",
          "addr_map_check",
          "boundary_contract_check"
        ],
        "action_type": "memory_runtime_plan_verification",
        "consumes": [
          "artifact.pipeline_planning.stream_liveness_review",
          "candidate_stage_artifact.memory_schedule",
          "candidate_stage_artifact.data_edges",
          "candidate_stage_artifact.stream_edges",
          "constraint.memory.board",
          "constraint.runtime.board"
        ],
        "id": "memory_runtime.verify_full_beat_transfer_plan",
        "on_failure": "Block memory/runtime promotion; route count or alignment mismatches to memory_runtime_repair. Any memory-layout or base-address change requires explicit approval and a full rerun of transfer_count_check and addr_map_check.",
        "produces": [
          "artifact.stage5.memory_runtime_plan.checked_transfer_counts",
          "artifact.stage5.addr_map_constraints"
        ],
        "rationale": "Carry the reviewed AXI beat counts, full-beat policy, activation buffer maxima, target sequence bound, and runtime transfer sequence into the memory/runtime plan before code generation and address-map finalization.",
        "requires_approval": false,
        "stage": "memory_runtime_planning",
        "tool_roles": [
          "memory_runtime_plan_check",
          "transfer_count_check",
          "addr_map_check"
        ]
      },
      {
        "acceptance_checkers": [
          "hierarchical_verification_plan_check",
          "case_stage_leaf_static",
          "case_single_transformer_layer",
          "case_pipeline_deadlock_check",
          "data_order_trace_check",
          "transfer_count_check",
          "deadlock_watchdog",
          "real_tool.case_deadlock_axi_check"
        ],
        "action_type": "hierarchical_verification_handoff",
        "consumes": [
          "artifact.stage4.boundary_contracts.stream_port_bindings",
          "artifact.stage5.memory_runtime_plan.checked_transfer_counts",
          "generated template-bound RTL/Chisel package",
          "verification input and weight manifests"
        ],
        "id": "verification.run_hierarchical_stream_order_count_deadlock_checks",
        "on_failure": "Do not promote to a higher layer. Localize the earliest causal boundary/module from tool output, package CCTG/contract-guided context, apply only bounded repair, and rerun the failed layer before proceeding.",
        "produces": [
          "verification/case_diagnostics/stream_order_count_deadlock_report.json",
          "verification/case_diagnostics/failure_localization_context.json"
        ],
        "rationale": "Static pipeline-planning liveness is not hardware evidence; later verification must exercise stream order, transfer counts, boundary contracts, and deadlock watchdogs through the required leaf, single-layer, and board-accurate hierarchy.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "hierarchical_verification_plan_check",
          "case_stage_leaf_static",
          "case_single_transformer_layer",
          "case_multilayer_pipeline",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "case_deadlock_axi_check"
        ]
      },
      {
        "acceptance_checkers": [
          "verification_action_audit_check",
          "verification_plan_static_check",
          "verification_artifact_contract_check",
          "required_real_tool_evidence_check",
          "repair_boundary_check",
          "human_boundary_check",
          "sacg_memory_check",
          "sacg_static_check"
        ],
        "action_type": "evidence_gate_audit",
        "consumes": [
          "candidate_stage_artifact.pipeline_planning_pipeline_plan",
          "candidate_stage_artifact.checker_results",
          "candidate_stage_artifact.checker_summary",
          "candidate_stage_artifact.stage_gate_policy",
          "state_summary.sacg_memory",
          "artifact.input.human_agent_boundary",
          "artifact.input.tool_protocols"
        ],
        "id": "pipeline_planning.run_final_evidence_gate_audit",
        "on_failure": "Block promotion, create a bounded stage_retry_request or stage_backtrack_request tied to the failed checker and SACG constraint, add a contamination barrier for unpromoted artifacts, and do not change golden outputs or tolerance.",
        "produces": [
          "artifact.pipeline_planning.evidence_gate_decision",
          "artifact.pipeline_planning.checker_constraint_matrix",
          "artifact.pipeline_planning.later_stage_obligation_handoff",
          "sacg_memory.stage_outcome_record.pipeline_planning"
        ],
        "rationale": "Close the current-stage evidence gate by binding the supplied checker_results, stage_gate_policy, SACG memory state, human boundary, and tool protocols to the promotion decision. This action records Stage6+ real-tool evidence as not_run/not_applicable for Stage3 rather than treating it as a hardware pass or failure.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "verification_action_audit",
          "verification_plan_static_check",
          "verification_artifact_contract_check",
          "required_real_tool_evidence_check",
          "repair_boundary_check",
          "human_boundary_check",
          "sacg_validate",
          "sacg_static_check",
          "sacg_memory_update"
        ]
      },
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "boundary_contract_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "template_binding_static_check",
          "sacg_static_check"
        ],
        "action_type": "next_stage_handoff",
        "consumes": [
          "artifact.pipeline_planning.evidence_gate_decision",
          "candidate_stage_artifact.pipeline_planning_pipeline_plan",
          "artifact.stage2.template_selection",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_metadata",
          "artifact.input.design_space"
        ],
        "id": "pipeline_planning.promote_contract_to_parameter_binding",
        "on_failure": "Localize the failed Stage4 parameter or boundary contract; open a backtrack to pipeline_planning only if the promoted contract is inconsistent; quarantine unpromoted Stage4 artifacts.",
        "produces": [
          "artifact.stage4.parameter_binding_contract",
          "artifact.stage4.boundary_contracts",
          "artifact.stage4.parameter_binding_checker_results"
        ],
        "rationale": "With current Stage3 plan evidence passing, bind final template parameters from the stable pipeline contract while preserving the approved operator order, stream/data edges, numeric policy, and trusted-template boundary.",
        "requires_approval": false,
        "stage": "parameter_binding",
        "tool_roles": [
          "parameter_binding_static_check",
          "boundary_contract_generate",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "code_generation_manifest_static_check",
          "codegen_contract_check",
          "codegen_package_static_check",
          "codegen_compile_gate_check",
          "artifact_hash_check",
          "sacg_static_check"
        ],
        "action_type": "later_stage_obligation",
        "consumes": [
          "artifact.stage4.parameter_binding_contract",
          "candidate_stage_artifact.memory_schedule",
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_protocols",
          "artifact.input.template_library"
        ],
        "id": "memory_layout.codegen_prepare_checker_backed_addresses",
        "on_failure": "Route to memory_runtime_repair or bounded_template_repair. If repair changes memory layout policy, AXI width/order, template choice, numeric policy, or pipeline topology, require approval and block promotion.",
        "produces": [
          "artifact.stage5.memory_layout_contract",
          "artifact.stage5.codegen_manifest",
          "artifact.stage5.elaboration_compile_report"
        ],
        "rationale": "Stage5 must convert the planning-level memory/runtime handoff into a checker-backed concrete address map and template-bound Chisel package. This is a later-stage obligation, not a current Stage3 blocker.",
        "requires_approval": false,
        "stage": "memory_layout",
        "tool_roles": [
          "memory_runtime_plan_check",
          "code_generation_manifest_static_check",
          "codegen_contract_check",
          "codegen_package_static_check",
          "codegen_compile_gate",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "required_real_tool_evidence_check",
          "case_stage_leaf_static",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "real_tool.case_vcs_functional_sim",
          "real_tool.case_verilator_functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "numeric_compare"
        ],
        "action_type": "later_stage_real_tool_verification",
        "consumes": [
          "artifact.stage5.codegen_manifest",
          "artifact.stage5.memory_layout_contract",
          "artifact.stage4.boundary_contracts",
          "candidate_stage_artifact.pipeline_planning_pipeline_plan",
          "artifact.input.tool_protocols",
          "artifact.input.case_adapter"
        ],
        "id": "verification.enforce_hierarchical_real_tool_evidence",
        "on_failure": "Do not promote to a higher verification layer. Convert tool output into CCTG/contract-guided localization of the earliest causal boundary, perform bounded repair, rerun the failed layer, and do not change golden outputs, tolerances, or numeric policy.",
        "produces": [
          "artifact.stage6.hierarchical_verification_plan",
          "verification.case_diagnostics.leaf_results",
          "verification.case_diagnostics.single_layer_results",
          "verification.case_diagnostics.axi_ddr_wrapped_results"
        ],
        "rationale": "Stage6+ must prove implementation behavior with real tool evidence and the three-layer repair loop: operator/leaf modules, then connected single-transformer-layer kernel, then board-accurate AXI/DDR wrapped system. Stage3 evidence must not be upgraded into a hardware pass.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "required_real_tool_evidence_check",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_vcs_functional_sim",
          "case_verilator_functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "numeric_compare"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 21,
      "max_duration_sec": 663.8878129720033,
      "max_prompt_bytes": 64420,
      "result_count": 5,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 2419.3756883539827,
      "total_prompt_bytes": 321591
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 5,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/subtask_plan.json",
    "used_fallback_count": 0
  },
  "errors": [],
  "llm_agent": {
    "agent": "pipeline_architect_agent",
    "approval_required_for": [
      "Any architecture or pipeline-topology change beyond the checker-backed operator_stream_pipeline and operator order.",
      "Changing decoder operator order, adding/removing stages, changing residual skip sources, join fire rules, or MLP split/join topology.",
      "Changing GQA head counts, group size, RoPE policy, causal mask policy, target sequence length, hidden size, intermediate size, lane count, transfer order, or transfer-unit policy.",
      "Any numeric precision, rounding, saturation, accumulator policy, tolerance, or golden-output change.",
      "Any trusted-template replacement, major template-library/template-metadata change, or free-form RTL generation outside the approved template library.",
      "Concrete DDR base-address assignment or any memory-layout/AXI/DDR address-map change, including changes to AXI data width, address width, WSTRB width, or 64-byte alignment.",
      "Any change to XDMA device index, control/status base apertures, raw register/DDR runtime protocol, double-buffered weight policy, or activation ping/pong policy.",
      "External KV-cache materialization or final runtime sequence/base-address policy changes.",
      "Any ambiguous backend/app-shell target selection without cited board materials and real Vivado/tool evidence."
    ],
    "executable_actions": [
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "sacg_memory_check"
        ],
        "action_type": "sacg_commit_gate",
        "consumes": [
          "candidate_pipeline_plan",
          "pipeline_static_checks",
          "checker_results",
          "checker_summary",
          "stage_gate_policy",
          "sacg_memory",
          "constraint.model.decoder",
          "constraint.shape.model",
          "constraint.template.library",
          "constraint.arch.design_space",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.cross_layer.input_consistency"
        ],
        "id": "pipeline_planning.commit_checked_pipeline_plan_to_sacg",
        "on_failure": "Block SACG commit, preserve the uncommitted candidate behind a stage_artifact_trust_barrier, open a bounded stage_retry_request tied to the failed SACG/static field, and rerun the failed checker after repair.",
        "produces": [
          "artifact.pipeline_planning.sacg_committed_pipeline_plan",
          "artifact.pipeline_planning.checker_constraint_matrix",
          "sacg_memory.stage_outcome_record.pipeline_planning"
        ],
        "rationale": "The candidate Stage 3 pipeline has passing supplied checker evidence and no SACG memory retry/backtrack/contamination blockers. Commit only the checker-backed contract and mark symbolic latency and hardware evidence as non-promotional metadata for this stage.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "sacg_validate",
          "sacg_static_check",
          "sacg_memory_update"
        ]
      },
      {
        "acceptance_checkers": [
          "verification_action_audit_check",
          "llm_io_quality_check",
          "sacg_static_check"
        ],
        "action_type": "team_action_normalization_gate",
        "consumes": [
          "design_team.team_aggregate",
          "design_team.executable_actions",
          "action_grounding_registry",
          "artifact.pipeline_planning.sacg_committed_pipeline_plan",
          "stage_gate_policy"
        ],
        "id": "pipeline_planning.normalize_team_handoff_queue",
        "on_failure": "Do not execute the ambiguous team queue. Keep the committed pipeline plan intact, localize duplicate or ungrounded actions, repair only the action metadata, and rerun the action audit before downstream handoff.",
        "produces": [
          "artifact.pipeline_planning.normalized_handoff_action_queue",
          "artifact.pipeline_planning.team_action_audit_report"
        ],
        "rationale": "The design-team decomposition is usable but contains overlapping Stage 4/5/6 handoff actions. Normalize it into a single ordered queue so downstream tools consume one authoritative pipeline contract and one artifact lineage per stage.",
        "requires_approval": false,
        "stage": "pipeline_planning",
        "tool_roles": [
          "team_aggregate",
          "verification_action_audit",
          "llm_io_quality_check",
          "sacg_validate"
        ]
      },
      {
        "acceptance_checkers": [
          "parameter_binding_static_check",
          "template_coverage_check",
          "numeric_policy_check",
          "boundary_contract_check",
          "stream_plan_check",
          "template_binding_static_check"
        ],
        "action_type": "template_parameter_binding_handoff",
        "consumes": [
          "artifact.pipeline_planning.sacg_committed_pipeline_plan",
          "artifact.pipeline_planning.normalized_handoff_action_queue",
          "artifact.stage2.template_selection",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.numeric_policy",
          "artifact.input.model_config",
          "constraint.template.library",
          "constraint.numeric.policy",
          "constraint.parameter.binding"
        ],
        "id": "stage4.bind_template_parameters_from_committed_pipeline",
        "on_failure": "Block code generation, localize the mismatch to the affected stage, edge, template parameter, or numeric field, repair within the approved template-parameter bounds, and rerun the same checkers. Any topology, numeric-policy, or template-library change requires approval.",
        "produces": [
          "artifact.stage4.template_parameter_binding_contract",
          "artifact.stage4.boundary_contracts",
          "artifact.stage4.template_bound_numeric_contract",
          "stage4/checker_reports/parameter_binding_static_check.json"
        ],
        "rationale": "Stage 4 must materialize per-template parameters from the committed Stage 3 contract while preserving the trusted template library, numeric policy, stage boundaries, GQA/RoPE semantics, residual joins, stream order, buffer depths, and AXI transfer-count formulas.",
        "requires_approval": false,
        "stage": "parameter_binding",
        "tool_roles": [
          "parameter_binding_static_check",
          "template_coverage_check",
          "numeric_policy_check",
          "boundary_contract_generate",
          "stream_plan_check"
        ]
      },
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "tool_protocol_check",
          "deployment_board_check",
          "case_real_weight_artifacts",
          "code_generation_manifest_static_check",
          "codegen_contract_check",
          "codegen_package_static_check"
        ],
        "action_type": "memory_runtime_codegen_handoff",
        "consumes": [
          "artifact.pipeline_planning.sacg_committed_pipeline_plan",
          "artifact.stage4.template_parameter_binding_contract",
          "artifact.stage4.boundary_contracts",
          "candidate_pipeline_plan.memory_schedule",
          "artifact.input.target_board_profile",
          "artifact.input.tool_protocols",
          "artifact.input.tool_profile",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.deployment.board"
        ],
        "id": "stage5.materialize_memory_layout_runtime_abi_and_codegen_manifest",
        "on_failure": "Block RTL/backend consumption. If addresses, transfer counts, runtime ABI, or buffer schedules are ambiguous, do not guess; route to memory_runtime_repair and request bounded approval for any memory-layout, AXI, runtime-protocol, or address-map change.",
        "produces": [
          "artifact.stage5.concrete_ddr_addr_map",
          "artifact.stage5.runtime_abi_contract",
          "artifact.stage5.packed_weight_manifest",
          "artifact.stage5.double_buffer_schedule",
          "artifact.stage5.codegen_manifest",
          "generated/chisel/runtime/runtime_config.json"
        ],
        "rationale": "Stage 5 must convert the Stage 3 memory/runtime handoff into concrete aligned DDR regions, runtime ABI, packed weight and activation-buffer schedule, and code-generation manifest without changing the board AXI facts or pipeline semantics.",
        "requires_approval": true,
        "stage": "memory_layout",
        "tool_roles": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "transfer_count_check",
          "tool_protocol_check",
          "deployment_board_check",
          "case_weight_manifest_generate",
          "code_generation_manifest_static_check",
          "codegen_contract_check",
          "codegen_package_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "required_real_tool_evidence_check",
          "case_stage_leaf_static",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "real_tool.case_vcs_functional_sim",
          "real_tool.case_verilator_functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "numeric_compare",
          "failure_localization_check",
          "causal_repair_context_check"
        ],
        "action_type": "later_stage_real_tool_verification",
        "consumes": [
          "artifact.stage4.boundary_contracts",
          "artifact.stage5.codegen_manifest",
          "artifact.stage5.concrete_ddr_addr_map",
          "artifact.stage5.runtime_abi_contract",
          "artifact.stage5.packed_weight_manifest",
          "artifact.stage5.double_buffer_schedule",
          "artifact.input.tool_protocols",
          "artifact.input.case_adapter"
        ],
        "id": "verification.plan_and_run_hierarchical_real_tool_evidence",
        "on_failure": "Do not promote to a higher verification layer or claim hardware pass. Convert tool output into contract-guided localization at the earliest causal boundary, perform bounded repair only, and rerun the failed layer. Do not modify golden outputs, tolerances, or numeric policy.",
        "produces": [
          "artifact.stage6.hierarchical_verification_plan",
          "verification/case_diagnostics/leaf_results",
          "verification/case_diagnostics/single_layer_results",
          "verification/case_diagnostics/axi_ddr_wrapped_results",
          "verification/case_diagnostics/failure_localization_context.json"
        ],
        "rationale": "Hardware correctness cannot be inferred from Stage 3 static planning. Later verification must use checker-backed boundary contracts and real tool evidence in order: leaf/operator modules, connected single-transformer-layer kernel, then board-accurate AXI/DDR wrapped system.",
        "requires_approval": false,
        "stage": "verification",
        "tool_roles": [
          "hierarchical_verification_plan_check",
          "verification_artifact_contract_check",
          "required_real_tool_evidence_check",
          "case_stage_leaf_static",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_axi_ddr_interface",
          "case_axi_protocol_check",
          "case_ddr_image_roundtrip",
          "case_vcs_functional_sim",
          "case_verilator_functional_sim",
          "deadlock_watchdog",
          "data_order_trace_check",
          "transfer_count_check",
          "numeric_compare",
          "failure_slice_localization",
          "causal_repair_context_pack"
        ]
      }
    ],
    "observations": [
      "The supplied Stage 3 checker summary is clean: operator order, stream/data edge mirroring, stream contracts, shape/numeric contracts, branch/join contracts, buffer contracts, liveness/backpressure, memory/runtime handoff, attention semantics, and template binding all pass with no warnings.",
      "The candidate plan preserves the decoder block order rms_norm_1 -> self_attention -> residual_add_1 -> rms_norm_2 -> mlp_gate_proj/mlp_up_proj -> activation_mul -> mlp_down_proj -> residual_add_2, with 13 mirrored data/stream edges and explicit ready/valid flow control.",
      "Attention fields are internally consistent in the supplied contract: causal GQA, num_q_heads=14, num_kv_heads=2, group size=7, head_dim=64, hidden_size=896, RoPE theta=1000000.0, seq_len_bound=16.",
      "Numeric and transfer-count planning is checker-backed for the current stage: activation_bits=16, weight_bits=16, accumulator_bits=32, rounding=nearest_even, saturation=false, 512-bit AXI, 64-byte alignment, and full-beat transfer counts are carried in the stream contracts.",
      "Buffering uses concrete bounded ready/valid FIFO entries with allowed depths 32 or 64; ping/pong activation buffers remain memory-layout artifacts rather than pipeline latency-equalization assumptions.",
      "The memory schedule is a valid Stage 3 handoff contract, not a concrete address map: it identifies six required regions, activation ping/pong, double-buffered weights, 512-bit DDR AXI facts, XDMA runtime requirements, and defers exact aligned base-address assignment to Stage 5.",
      "The design-team decomposition is broad but directionally aligned: it separates current-stage evidence gating, Stage 4 parameter binding, Stage 5 memory/runtime/codegen materialization, and Stage 6+ real hierarchical verification.",
      "The supplied SACG memory has no active contamination barriers, no open retry requests, and no open backtrack requests; there is therefore no same-stage blocker from SACG memory for this review.",
      "Per the supplied stage_gate_policy, symbolic_first_order latency values are planning metadata only and must not be promoted as throughput, timing, or hardware-pass evidence.",
      "Stage 3 must not claim hardware pass. Real VCS/Verilator/Vivado/board evidence remains a later-stage obligation and must follow the required leaf-module, single-transformer-layer, then board-accurate AXI/DDR wrapped-system repair loop."
    ],
    "proposed_actions": [
      "Commit the candidate pipeline plan and checker matrix to SACG as the Stage 3 pipeline_planning outcome because all current-stage checkers passed and SACG memory has no blockers.",
      "Normalize the design-team executable-action queue into an ordered SACG handoff: current-stage commit/evidence gate, Stage 4 parameter binding, Stage 5 concrete memory/runtime/codegen materialization, and Stage 6+ hierarchical real-tool verification.",
      "Carry the memory schedule forward as a handoff contract only; do not finalize concrete DDR addresses or external KV-cache materialization in Stage 3.",
      "Require explicit approval for any change to architecture, pipeline topology, numeric policy, memory layout, AXI/DDR board facts, template substitution, free-form RTL, or golden-reference/tolerance policy.",
      "In verification planning, enforce the three-layer repair loop: leaf/operator modules first, connected single-transformer-layer kernel second, board-accurate AXI/DDR wrapped system third."
    ],
    "risks": [
      "Later-stage implementation risk: Stage 4 must bind template parameters without changing operator order, residual skip sources, GQA/RoPE fields, stream order, element widths, lane count, or trusted-template boundaries.",
      "Later-stage memory/runtime risk: Stage 5 must assign concrete DDR base addresses and runtime ABI fields from the six-region plan while preserving 64-byte alignment, 512-bit AXI data width, 37-bit address width, WSTRB width, XDMA device index, and raw register/DDR protocol.",
      "Later-stage data-order risk: stream order token/tile/lane/word and full-beat transfer counts must remain identical across parameter binding, code generation, weight packing, runtime command generation, and verification manifests.",
      "Later-stage numeric risk: fp32 block input/residual paths, fp16 activation/weight paths, fp32 accumulation, nearest-even rounding, and no-saturation policy must be preserved in generated templates and golden-reference comparisons; tolerance or golden-output changes require approval.",
      "Later-stage verification risk: static liveness/backpressure checks do not prove RTL or board behavior; real tool failures must be localized to the earliest causal boundary before bounded repair and rerun.",
      "Team-decomposition risk: the aggregate contains overlapping handoff actions across memory/runtime, template binding, and verification. Before execution, the action graph should be normalized into a single ordered queue to avoid duplicate or conflicting downstream artifact names."
    ],
    "sacg_focus": {
      "artifacts": [
        "candidate_pipeline_plan",
        "pipeline_static_checks",
        "checker_results",
        "checker_summary",
        "design_team.team_aggregate",
        "sacg_memory",
        "action_grounding_registry",
        "stage_gate_policy"
      ],
      "constraints": [
        "constraint.model.decoder",
        "constraint.shape.model",
        "constraint.template.library",
        "constraint.arch.design_space",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.cross_layer.input_consistency",
        "constraint.numeric.policy",
        "constraint.tool.protocols"
      ],
      "edges": [
        "edge.data.block_input.to.stage_00_rms_norm_1.input",
        "edge.data.block_input.to.stage_02_residual_add_1.residual_skip",
        "edge.data.stage_00_rms_norm_1.to.stage_01_self_attention.main",
        "edge.data.stage_01_self_attention.to.stage_02_residual_add_1.main",
        "edge.data.stage_02_residual_add_1.to.stage_03_rms_norm_2.main",
        "edge.data.stage_02_residual_add_1.to.stage_08_residual_add_2.residual_skip",
        "edge.data.stage_03_rms_norm_2.to.stage_04_mlp_gate_proj.mlp_gate_branch",
        "edge.data.stage_03_rms_norm_2.to.stage_05_mlp_up_proj.mlp_up_branch",
        "edge.data.stage_04_mlp_gate_proj.to.stage_06_activation_mul.mlp_gate_to_mul",
        "edge.data.stage_05_mlp_up_proj.to.stage_06_activation_mul.mlp_up_to_mul",
        "edge.data.stage_06_activation_mul.to.stage_07_mlp_down_proj.main",
        "edge.data.stage_07_mlp_down_proj.to.stage_08_residual_add_2.main",
        "edge.data.stage_08_residual_add_2.to.block_output.output"
      ],
      "nodes": [
        "block_input",
        "stage_00_rms_norm_1",
        "stage_01_self_attention",
        "stage_02_residual_add_1",
        "stage_03_rms_norm_2",
        "stage_04_mlp_gate_proj",
        "stage_05_mlp_up_proj",
        "stage_06_activation_mul",
        "stage_07_mlp_down_proj",
        "stage_08_residual_add_2",
        "block_output"
      ]
    },
    "schema_version": "spatialaccagent.pipeline_architect_review.v0",
    "stage": "pipeline_planning",
    "status": "approved_for_sacg_commit",
    "summary": "Candidate Stage 3 operator_stream_pipeline plan is acceptable for SACG commit based on the supplied checker evidence: 10/10 current-stage static checks passed with no warnings or errors. No open SACG retry requests, backtrack requests, or contamination barriers are present. Commit should preserve the checker-backed plan while carrying forward bounded Stage 4/5/6 obligations for parameter binding, concrete memory layout/runtime ABI, and real hierarchical verification without treating Stage 3 planning evidence as hardware evidence."
  },
  "num_data_edges": 13,
  "num_pipeline_stages": 9,
  "num_stream_edges": 13,
  "outputs": {
    "llm_agent": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/llm/pipeline_architect_agent_result.json",
    "pipeline_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/pipeline_plan.json",
    "pipeline_static_checks": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/pipeline_static_checks.json",
    "sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/sacg_state.json",
    "team_aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/team_aggregate.json",
    "team_subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/subtask_plan.json"
  },
  "sacg_transition_id": "transition.0002",
  "schema_version": "spatialaccagent.pipeline_planning_report.v0",
  "source_sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/sacg_state.json",
  "stage": "pipeline_planning",
  "status": "ready"
}
</recent_stage_summary>

<command>
[
  "/home/remote/miniconda3/bin/python3",
  "-m",
  "accagent.framework.stage_pipeline",
  "--sacg-state",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/sacg_state.json"
]
</command>

<command_returncode>
0
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/agent/logs/30_pipeline_planning.json
</command_log>

<sacg_memory>
{
  "active_contamination_barriers": [],
  "open_backtrack_requests": [],
  "open_retry_requests": [],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [],
  "recent_failure_lessons": [],
  "recent_stage_outcomes": [],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/sacg_state.json
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
