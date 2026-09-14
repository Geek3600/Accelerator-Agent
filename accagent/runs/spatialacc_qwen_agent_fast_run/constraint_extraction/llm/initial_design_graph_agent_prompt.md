<agent>
initial_design_graph_agent
</agent>

<task>
Review the initial design graph extracted from prepared inputs. You are the design-intake lead in a chip accelerator team: check whether model, shape, numeric policy, template, board DDR/AXI/runtime, tool, evidence, and human-boundary facts are represented clearly enough for later architecture, code generation, verification, and board implementation agents.
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

<prepared_inputs_manifest>
{
  "design_team": {
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/input/team/team_aggregate.json",
    "approval_required_for": [
      "Adding, replacing, or materially modifying trusted templates or template metadata used by artifact.input.template_library.",
      "Any DDR base address, DDR size, AXI data/address width, burst/alignment policy, address-map, transfer unit, or memory layout change not directly supported by cited board evidence and accepted checkers.",
      "Any downstream architecture, pipeline, memory layout, numeric policy, or template-library change proposed to compensate for model-shape gaps.",
      "Any runtime ABI, host driver protocol, register map, buffer ordering, or deployment protocol override beyond the supplied target_board_profile, tool_protocols, and human_agent_boundary.",
      "Any substitution of required real tools or consumption of fallback/diagnostic records as successful evidence.",
      "Architecture or design_space changes, including changes to operator decomposition, layer topology, pipeline boundaries, or major scheduling assumptions.",
      "Backend/app-shell target selection when board materials or Vivado evidence are ambiguous or conflicting.",
      "Backtrack beyond current-stage input repair scope or promotion of artifacts across an unresolved retry/backtrack/trust barrier.",
      "Changing artifact.input.design_space hard constraints, architecture choices, tiling/parallelism limits, memory layout, transfer unit assumptions, or resource budgets to close coverage gaps.",
      "Changing artifact.input.numeric_policy quantization formats, scaling, rounding, saturation, accumulator width, or numeric comparison policy.",
      "LLM model override, consumption of fallback diagnostics as successful decisions, or bypass of enforced LLM review.",
      "Major template-library changes or free-form RTL/code-template rewrites outside approved bounded repair scopes.",
      "Manual board or app-shell target selection if target discovery evidence remains ambiguous after cited material/sample and real Vivado checks.",
      "Numeric policy changes, including precision, quantization, accumulation policy, comparison tolerance, or replacement of golden-reference policy; direct golden-output edits or tolerance loosening to force pass remain forbidden.",
      "Pipeline or memory-layout changes, including address map, transfer unit, DDR/AXI ordering, stream order, runtime ABI, or host-buffer layout changes.",
      "Promoting any repair that expands beyond bounded glue code or trusted-template parameter binding.",
      "Selecting one interpretation among conflicting model-shape facts from task_card, model_config, or case_adapter.",
      "Supplying or changing task_card/model_config semantics for model goal, decoder topology, tensor dimensions, attention/head mapping, sequence length, operator ordering, or residual path after the checker gap list is emitted.",
      "architecture or pipeline topology changes discovered during input audits",
      "backend/app-shell target-selection decisions without unambiguous cited board or Vivado evidence",
      "human-boundary exceptions, forbidden-action overrides, or LLM/tool-policy overrides",
      "major template-library or operator-coverage changes beyond bounded metadata repair",
      "memory layout, address map, DDR image layout, or runtime ABI policy changes",
      "numeric precision, quantization, accumulation, rounding, saturation, or tolerance policy changes"
    ],
    "completed_subtasks": 5,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/input/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "llm_semantic_extraction_check",
          "no_static_keyword_semantic_matching_check",
          "sacg_static_check"
        ],
        "action_type": "implementation_evidence_review",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "artifact.input.field_evidence",
          "artifact.input.field_evidence_candidates",
          "artifact.input.material_index",
          "artifact.input.sample_project_index"
        ],
        "id": "input_preparation.audit_board_runtime_tool_evidence",
        "on_failure": "Record the failed or not_run evidence item in artifact.input_audit.board_memory_runtime_gap_list and block downstream implementation, deployment, and hardware-pass claims that depend on it.",
        "produces": [
          "artifact.input_audit.board_runtime_tool_report",
          "artifact.input_audit.tool_availability_matrix",
          "artifact.input_audit.board_memory_runtime_gap_list",
          "artifact.input_audit.field_evidence_trace_index"
        ],
        "rationale": "Consolidate the compact board, tool, material, sample, and field-evidence inputs into an explicit evidence ledger. The supplied summary cannot certify concrete DDR/AXI, address-map, runtime ABI, deployment, or real-tool facts, so each required item must be cited or marked not_run.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "real_tool_evidence_check",
          "llm_semantic_extraction",
          "no_static_keyword_semantic_matching"
        ]
      },
      {
        "acceptance_checkers": [
          "case_board_interface_discovery",
          "case_axi_ddr_interface",
          "addr_map_check",
          "memory_runtime_plan_check",
          "case_runtime_abi_check"
        ],
        "action_type": "board_memory_runtime_contract_validation",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.design_space",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.case_adapter",
          "artifact.input.material_index",
          "artifact.input.sample_project_index",
          "artifact.input_audit.field_evidence_trace_index"
        ],
        "id": "input_preparation.validate_board_memory_runtime_contract",
        "on_failure": "Localize the earliest missing or conflicting boundary among board profile, AXI/DDR interface, address map, transfer plan, and runtime ABI; do not repair by changing golden outputs, loosening tolerance, or silently adopting template defaults.",
        "produces": [
          "artifact.input_audit.board_axi_ddr_contract",
          "artifact.input_audit.address_map_contract",
          "artifact.input_audit.runtime_abi_contract",
          "artifact.input_audit.board_memory_runtime_gap_list"
        ],
        "rationale": "Bind target board facts to a checked DDR/AXI interface, address map, transfer plan, and runtime ABI before templates or code generation consume any board defaults.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "case_board_interface_discovery",
          "case_axi_ddr_interface",
          "addr_map_check",
          "memory_runtime_plan_check",
          "case_runtime_abi_check"
        ]
      },
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "human_boundary_check"
        ],
        "action_type": "tool_availability_protocol_validation",
        "consumes": [
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "artifact.input.human_agent_boundary"
        ],
        "id": "input_preparation.verify_tool_protocol_and_availability_matrix",
        "on_failure": "Mark unavailable or protocol-ambiguous tools as blockers for the dependent checker stages and request bounded tool substitution or capability repair through the human-agent boundary.",
        "produces": [
          "artifact.input_audit.tool_availability_matrix",
          "artifact.input_audit.tool_protocol_gap_list",
          "artifact.input_audit.real_tool_evidence_requirements"
        ],
        "rationale": "The tool artifacts are present but detailed tool paths, versions, invocation protocols, and executable evidence are not visible in the supplied summary. This action verifies that later real-tool stages can be executed under the recorded protocols.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "human_boundary_check"
        ]
      },
      {
        "acceptance_checkers": [
          "backend_app_shell_integration_contract_static_check",
          "backend_app_shell_target_discovery_check",
          "backend_app_shell_target_hint_synthesis_check",
          "backend_bounded_recovery_action_check",
          "real_tool.app_shell_target_discovery_contract",
          "real_tool.app_shell_target_hint_synthesis",
          "real_tool.app_shell_target_discovery_after_hint",
          "human_boundary_check"
        ],
        "action_type": "target_discovery_policy_update",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.material_index",
          "artifact.input.sample_project_index",
          "artifact.input.field_evidence",
          "artifact.input_audit.field_evidence_trace_index",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability"
        ],
        "id": "input_preparation.prepare_backend_app_shell_target_discovery_policy",
        "on_failure": "Keep runtime bitstream generation and board runtime blocked; if discovery remains ambiguous after cited hints, produce a bounded recovery action and request approval rather than selecting an app-shell target by memory or guesswork.",
        "produces": [
          "artifact.input_audit.target_discovery_policy_update",
          "artifact.input_audit.app_shell_target_discovery_contract",
          "artifact.input_audit.backend_target_ambiguity_report"
        ],
        "rationale": "Backend/app-shell target discovery must be synthesized from supplied board materials, sample-project evidence, and real Vivado evidence. Since no concrete target names or Vivado discovery results are visible here, the policy must cite evidence, record ambiguity, and require bounded approval instead of guessing.",
        "requires_approval": true,
        "stage": "input_preparation",
        "tool_roles": [
          "app_shell_target_discovery_contract",
          "app_shell_target_hint_synthesis",
          "app_shell_target_discovery_after_hint",
          "backend_bounded_recovery_action"
        ]
      },
      {
        "acceptance_checkers": [
          "stage_artifact_trust_barrier_check",
          "sacg_memory_check",
          "sacg_static_check",
          "required_real_tool_evidence_check"
        ],
        "action_type": "trust_barrier",
        "consumes": [
          "artifact.input_audit.board_runtime_tool_report",
          "artifact.input_audit.board_memory_runtime_gap_list",
          "artifact.input.field_evidence",
          "sacg_memory"
        ],
        "id": "input_preparation.install_board_runtime_tool_trust_barrier",
        "on_failure": "Block promotion to cross-layer evidence gate until the barrier state is recorded and downstream consumers are prevented from treating unverified implementation, bitstream, or board-runtime claims as facts.",
        "produces": [
          "sacg_memory.contamination_barrier.board_runtime_tool_evidence_pending",
          "artifact.input_audit.unsupported_implementation_claim_blocklist"
        ],
        "rationale": "No active sacg_memory barrier is visible, but the current evidence summary is insufficient for downstream implementation claims. A temporary trust barrier prevents unverified board/runtime/tool claims from contaminating SACG-guided design decisions.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "stage_artifact_trust_barrier",
          "sacg_memory_update",
          "sacg_validate"
        ]
      },
      {
        "acceptance_checkers": [
          "human_boundary_check",
          "tool_protocol_check",
          "verification_plan_static_check",
          "verification_artifact_contract_check",
          "repair_boundary_check",
          "boundary_contract_check",
          "sacg_memory_check"
        ],
        "action_type": "verification_boundary_review",
        "consumes": [
          "artifact.input.case_adapter",
          "artifact.input.human_agent_boundary",
          "artifact.input.tool_protocols",
          "artifact.input.prepared_inputs",
          "constraint.human.boundary",
          "constraint.tool.protocols",
          "state_summary.sacg_memory",
          "action_grounding_registry"
        ],
        "id": "inputprep.audit_boundary_protocol_checker_pack",
        "on_failure": "Block SACG extraction and downstream implementation decisions; create a bounded current-stage retry or backtrack request with a trust barrier; do not waive checkers, edit golden outputs, loosen tolerances, or claim pass from absent evidence.",
        "produces": [
          "artifact.input_audit.boundary_repair_report",
          "artifact.input_audit.checker_coverage_matrix",
          "artifact.input_audit.approval_and_forbidden_action_list",
          "artifact.input_audit.repair_boundary_gap_list"
        ],
        "rationale": "Convert the summarized case_adapter acceptance/evidence_gates, human_agent_boundary, tool_protocols, prepared_inputs errors, and relevant SACG memory state into checker-backed audit artifacts. The supplied summary shows presence but not pass evidence, so no SACG extraction or downstream implementation decision should proceed until these checks produce evidence.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "human_boundary_check",
          "tool_protocol_check",
          "verification_plan_static_check",
          "verification_artifact_contract_check",
          "repair_boundary_check",
          "boundary_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "stage_retry_request_check",
          "stage_backtrack_request_check",
          "stage_artifact_trust_barrier_check",
          "repair_boundary_check",
          "causal_repair_context_check",
          "human_boundary_check"
        ],
        "action_type": "bounded_repair_or_backtrack_request",
        "consumes": [
          "artifact.input_audit.boundary_repair_report",
          "artifact.input_audit.checker_coverage_matrix",
          "artifact.input_audit.approval_and_forbidden_action_list",
          "artifact.input_audit.repair_boundary_gap_list",
          "state_summary.sacg_memory"
        ],
        "id": "inputprep.reconcile_current_stage_trust_barriers",
        "on_failure": "Keep candidate artifacts quarantined from SACG extraction; require approval for architecture, numeric, memory-layout, pipeline, or major-template changes; otherwise repair only within the bounded input-preparation contract and rerun the boundary/protocol checker pack.",
        "produces": [
          "artifact.input_audit.current_stage_retry_or_backtrack_request",
          "artifact.input_audit.stage_artifact_trust_barrier",
          "artifact.input_audit.repair_scope_contract"
        ],
        "rationale": "If the boundary audit finds missing checker coverage, conflicting approval/forbidden rules, non-empty hidden errors, or unsupported evidence gates, create bounded retry/backtrack artifacts. No open memory blocker is visible now, but any new same-stage blocker must be recorded before downstream consumption.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "stage_retry_request",
          "stage_backtrack_request",
          "stage_artifact_trust_barrier",
          "repair_boundary_check",
          "causal_repair_context_pack"
        ]
      },
      {
        "acceptance_checkers": [
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "tool_protocol_check",
          "human_boundary_check",
          "deployment_board_check",
          "boundary_contract_check"
        ],
        "action_type": "cross_layer_evidence_gate",
        "consumes": [
          "artifact.input.task_card",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.case_adapter",
          "artifact.input.tool_protocols",
          "artifact.input.human_agent_boundary",
          "artifact.input_audit.boundary_repair_report",
          "artifact.input_audit.checker_coverage_matrix",
          "artifact.input_audit.approval_and_forbidden_action_list",
          "artifact.input_audit.repair_boundary_gap_list",
          "constraint.task.goal",
          "constraint.model.decoder",
          "constraint.shape.model",
          "constraint.numeric.policy",
          "constraint.template.library",
          "constraint.arch.design_space",
          "constraint.deployment.board",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.tool.protocols",
          "constraint.human.boundary"
        ],
        "id": "inputprep.cross_layer_evidence_gate_before_sacg",
        "on_failure": "Classify the inconsistency as a current-stage blocker when it affects input acceptance/evidence gates, human boundary, or tool protocol; otherwise emit an explicit later-stage action with approvals. Do not start SACG extraction until the readiness decision is checker-backed.",
        "produces": [
          "artifact.input_audit.cross_layer_evidence_gate_report",
          "artifact.input_audit.sacg_extraction_readiness_decision"
        ],
        "rationale": "After boundary audit artifacts exist, verify that task, model, shape, numeric, data-order, template, memory, runtime, implementation, and board facts are consistently represented before SACG extraction.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "stream_plan_check",
          "memory_runtime_plan_check",
          "tool_protocol_check",
          "human_boundary_check",
          "deployment_board_check"
        ]
      },
      {
        "acceptance_checkers": [
          "llm_io_quality_check",
          "llm_semantic_extraction_check",
          "no_static_keyword_semantic_matching_check",
          "tool_protocol_check"
        ],
        "action_type": "llm_protocol_quality_review",
        "consumes": [
          "llm_policy",
          "artifact.input.case_adapter",
          "artifact.input.tool_protocols",
          "artifact.input_audit.boundary_repair_report"
        ],
        "id": "inputprep.llm_decision_and_protocol_evidence_quality_gate",
        "on_failure": "Block promotion; regenerate the agent decision with the locked model or an approved override path, then rerun the boundary/protocol audit.",
        "produces": [
          "artifact.input_audit.llm_and_protocol_quality_report"
        ],
        "rationale": "LLM policy is enforce=true, so boundary decisions and protocol interpretation must be real agent outputs and must not be replaced by fallback diagnostics, static keyword matching, or unreviewed scripts.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "llm_io_quality_check",
          "llm_semantic_extraction",
          "no_static_keyword_semantic_matching",
          "tool_protocol_check"
        ]
      },
      {
        "acceptance_checkers": [
          "backend_app_shell_integration_contract_static_check",
          "backend_app_shell_target_discovery_check",
          "backend_bounded_recovery_action_check",
          "human_boundary_check",
          "tool_protocol_check"
        ],
        "action_type": "backend_target_discovery_policy_audit",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.case_adapter",
          "artifact.input.tool_protocols",
          "artifact.input.human_agent_boundary",
          "constraint.deployment.board",
          "constraint.runtime.board",
          "constraint.tool.protocols",
          "constraint.human.boundary"
        ],
        "id": "inputprep.backend_target_discovery_policy_static_audit",
        "on_failure": "Record a later-stage backend recovery blocker and require bounded approval for ambiguous shell targets; do not allow runtime bitstream or board-runtime actions to rely on guessed target names.",
        "produces": [
          "artifact.input_audit.backend_target_discovery_policy_findings",
          "artifact.input_audit.backend_bounded_recovery_policy_requirements"
        ],
        "rationale": "Ensure the tool_protocols and human boundary require backend/app-shell target discovery to cite supplied board materials and real Vivado evidence, with bounded approval when evidence is ambiguous, instead of guessing integration target names.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "app_shell_target_discovery_contract",
          "backend_bounded_recovery_action",
          "human_boundary_check",
          "tool_protocol_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check",
          "stage_retry_request_check",
          "stage_backtrack_request_check",
          "stage_artifact_trust_barrier_check"
        ],
        "action_type": "sacg_memory_update",
        "consumes": [
          "state_summary.sacg_memory",
          "sacg_memory",
          "artifact.input_audit.boundary_repair_report",
          "artifact.input_audit.repair_boundary_gap_list",
          "artifact.input_audit.sacg_extraction_readiness_decision"
        ],
        "id": "inputprep.update_sacg_memory_after_boundary_audit",
        "on_failure": "Keep audit artifacts local and block cross-stage handoff until SACG memory either records the blockers or explicitly records that no retry/backtrack/barrier state is open.",
        "produces": [
          "artifact.input_audit.sacg_memory_delta",
          "updated_sacg_memory"
        ],
        "rationale": "Preserve the audit outcome, explicit absence or presence of retry/backtrack requests, and any contamination barriers in shared SACG memory before handoff.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_memory_update"
        ]
      },
      {
        "acceptance_checkers": [
          "llm_semantic_extraction_check",
          "no_static_keyword_semantic_matching_check",
          "task_card_check",
          "model_config_check"
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
        "id": "input_prep.extract_and_check_model_shape_facts",
        "on_failure": "Block SACG extraction for model-shape constraints, emit a source-linked gap list for each missing or ambiguous fact, and do not substitute guessed decoder or tensor semantics.",
        "produces": [
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.model_shape_gap_list",
          "artifact.input_audit.model_shape_sacg_seed_requirements"
        ],
        "rationale": "The visible summary proves artifact existence but not semantic sufficiency. This action extracts and checks model-goal, decoder-block, tensor-shape, attention/head, sequence-length, operator-ordering, and residual-path facts without relying on static keyword matching or project-name inference.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "llm_semantic_extraction",
          "no_static_keyword_semantic_matching",
          "task_card_check",
          "model_config_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "sacg_reference_check"
        ],
        "action_type": "sacg_static_validation",
        "consumes": [
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.model_shape_sacg_seed_requirements",
          "constraint.task.goal",
          "constraint.model.decoder",
          "constraint.shape.model"
        ],
        "id": "input_prep.validate_sacg_seed_graph_for_model_shape",
        "on_failure": "Return violations to the model_shape_gap_list and keep partial or conflicting seed nodes out of the promoted SACG.",
        "produces": [
          "artifact.input_audit.model_shape_sacg_validation",
          "artifact.sacg.seed.model_shape_nodes_edges"
        ],
        "rationale": "The SACG currently has no nodes or edges; extracted model-shape facts must be converted into checked seed requirements before downstream stages can reference them.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_validate",
          "sacg_static_check",
          "sacg_reference_check"
        ]
      },
      {
        "acceptance_checkers": [
          "stage_backtrack_request_check",
          "stage_artifact_trust_barrier_check",
          "human_boundary_check"
        ],
        "action_type": "bounded_backtrack_request",
        "consumes": [
          "artifact.input_audit.model_shape_gap_list",
          "artifact.input.human_agent_boundary",
          "artifact.input.task_card",
          "artifact.input.model_config"
        ],
        "id": "input_prep.issue_model_shape_backtrack_if_gaps_block_seed",
        "on_failure": "Keep downstream SACG extraction, parameter binding, template selection, and code generation blocked until the backtrack request or approved clarification is recorded.",
        "produces": [
          "artifact.stage0.backtrack_request.model_shape_inputs",
          "artifact.stage0.trust_barrier.model_shape_downstream_block"
        ],
        "rationale": "If the checked gap list shows missing or conflicting source facts, the system needs source artifact repair or human clarification; inventing architecture, shape, or operator semantics is not allowed.",
        "requires_approval": true,
        "stage": "input_preparation",
        "tool_roles": [
          "stage_backtrack_request",
          "stage_artifact_trust_barrier",
          "human_boundary_check"
        ]
      },
      {
        "acceptance_checkers": [
          "numeric_policy_check",
          "template_coverage_check",
          "memory_runtime_plan_check",
          "tool_protocol_check",
          "sacg_static_check"
        ],
        "action_type": "cross_layer_evidence_gate",
        "consumes": [
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.model_shape_sacg_validation",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.target_board_profile",
          "artifact.input.tool_protocols"
        ],
        "id": "input_prep.cross_layer_model_shape_evidence_gate_handoff",
        "on_failure": "Route the inconsistency to the responsible input owner or backtrack action and do not proceed to parameter binding, code generation, or backend planning.",
        "produces": [
          "artifact.input_audit.cross_layer_model_shape_handoff",
          "artifact.input_audit.cross_layer_model_shape_risk_register"
        ],
        "rationale": "Once model-shape facts pass the current checks, they must be compared against numeric policy, template coverage, memory/runtime expectations, and tool protocols to prevent cross-layer inconsistency.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "team_aggregate",
          "numeric_policy_check",
          "template_coverage_check",
          "memory_runtime_plan_check",
          "tool_protocol_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check"
        ],
        "action_type": "sacg_memory_update",
        "consumes": [
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.model_shape_gap_list",
          "artifact.input_audit.model_shape_sacg_validation"
        ],
        "id": "input_prep.record_model_shape_audit_memory",
        "on_failure": "Do not let downstream stages rely on out-of-band memory of this audit; rerun memory update before handoff.",
        "produces": [
          "artifact.sacg_memory.model_shape_intake_entry"
        ],
        "rationale": "The design memory must preserve that no model-shape pass was claimed from the compact summary and must record any approved facts, gaps, barriers, or backtrack decisions for downstream agents.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_memory_update"
        ]
      },
      {
        "acceptance_checkers": [
          "numeric_policy_check",
          "template_coverage_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "sacg_static_check"
        ],
        "action_type": "template_binding_review",
        "consumes": [
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.model_config",
          "constraint.numeric.policy",
          "constraint.template.library",
          "constraint.arch.design_space",
          "constraint.model.decoder",
          "constraint.shape.model"
        ],
        "id": "input_preparation.run_numeric_template_static_audit",
        "on_failure": "Keep the numeric/template audit unapproved, mark failed or unavailable checker results explicitly, and route unsupported quantization, template coverage gaps, or unbound parameters to bounded repair or architecture review. Do not promote artifacts to SACG extraction or code generation.",
        "produces": [
          "artifact.input_audit.numeric_template_report",
          "artifact.input_audit.template_coverage_matrix",
          "artifact.input_audit.parameter_binding_gap_list",
          "artifact.input_audit.numeric_template_checker_results"
        ],
        "rationale": "Generate the stage-required evidence for supported quantization, trusted template coverage, and static parameter binding. The current prompt only proves artifact presence, not checker pass status.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "repair_boundary_check",
          "human_boundary_check",
          "numeric_policy_check",
          "template_coverage_check",
          "template_binding_static_check",
          "parameter_binding_static_check"
        ],
        "action_type": "bounded_repair_or_architecture_review",
        "consumes": [
          "artifact.input_audit.numeric_template_report",
          "artifact.input_audit.template_coverage_matrix",
          "artifact.input_audit.parameter_binding_gap_list",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.human_agent_boundary",
          "constraint.human.boundary"
        ],
        "id": "input_preparation.resolve_numeric_template_binding_gaps",
        "on_failure": "Do not apply or promote the repair candidate. Emit a backtrack request or approval request naming the exact numeric policy, template, metadata, or design_space change required.",
        "produces": [
          "artifact.input.numeric_policy.repair_candidate",
          "artifact.input.template_metadata.repair_candidate",
          "artifact.input.design_space.repair_candidate",
          "artifact.input_audit.repair_decision_record",
          "stage_backtrack_request_if_unrepairable"
        ],
        "rationale": "If the static audit finds unsupported quantization, missing trusted-template coverage, or illegal parameter ranges, the repair must stay inside trusted template boundaries or become an explicit architecture/numeric-policy approval item.",
        "requires_approval": true,
        "stage": "input_preparation",
        "tool_roles": [
          "bounded_template_repair",
          "architecture_review",
          "human_boundary_check"
        ]
      },
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "deployment_board_check",
          "sacg_static_check"
        ],
        "action_type": "resource_risk_assumption_review",
        "consumes": [
          "artifact.input.design_space",
          "artifact.input.template_metadata",
          "artifact.input.target_board_profile",
          "artifact.input.tool_profile",
          "constraint.arch.design_space",
          "constraint.memory.board",
          "constraint.deployment.board",
          "constraint.runtime.board"
        ],
        "id": "input_preparation.bind_design_space_resource_risks",
        "on_failure": "Keep resource-risk assumptions as unresolved handoff risks for the cross-layer evidence gate; do not claim timing, utilization, bandwidth, or board feasibility until later real tool evidence exists.",
        "produces": [
          "artifact.input_audit.resource_risk_assumption_report",
          "artifact.input_audit.design_space_board_binding_notes"
        ],
        "rationale": "Resource-risk assumptions in design_space must be carried forward as bounded risks, not as timing/resource pass claims, and must be tied to board memory/runtime/deployment constraints before backend use.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "architecture_review",
          "memory_runtime_plan_check",
          "deployment_board_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check",
          "sacg_static_check"
        ],
        "action_type": "sacg_memory_update",
        "consumes": [
          "artifact.input_audit.numeric_template_report",
          "artifact.input_audit.template_coverage_matrix",
          "artifact.input_audit.parameter_binding_gap_list",
          "artifact.input_audit.resource_risk_assumption_report"
        ],
        "id": "input_preparation.record_numeric_template_audit_in_sacg_memory",
        "on_failure": "Do not hand off the audit as completed. Preserve the current blocker that checker-backed numeric/template evidence has not been committed to SACG memory.",
        "produces": [
          "artifact.sacg_memory.numeric_template_audit_record"
        ],
        "rationale": "SACG memory is the shared evidence ledger; the numeric/template audit result, including not_run or failed checker states, must be recorded for later stages to avoid relying on informal memory.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_memory_update",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "memory_runtime_plan_check",
          "tool_protocol_check",
          "human_boundary_check",
          "boundary_contract_check",
          "output_validity_check"
        ],
        "action_type": "input_audit_materialization",
        "consumes": [
          "artifact.input.prepared_inputs",
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
          "artifact.input.case_adapter",
          "artifact.input.field_evidence"
        ],
        "id": "input_preparation.materialize_specialist_audits",
        "on_failure": "Keep SACG extraction blocked. Emit artifact.input_audit.stage_retry_or_backtrack_requests with the failed constraints. Repair only input/audit bindings unless a checker proves that an architecture, numeric, memory-layout, template, or board-target change is required.",
        "produces": [
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.numeric_template_report",
          "artifact.input_audit.board_runtime_tool_report",
          "artifact.input_audit.boundary_repair_report",
          "artifact.input_audit.blocker_to_constraint_map"
        ],
        "rationale": "The candidate prepared_inputs bundle exists and has no top-level errors, but the specialist reports required for cross-layer merging are not visible. This action materializes model/shape, numeric/template, board/runtime/tool, and human-boundary audit evidence without changing design policy.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "memory_runtime_plan_check",
          "tool_protocol_check",
          "human_boundary_check",
          "team_aggregate"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check",
          "stage_retry_request_check",
          "stage_backtrack_request_check",
          "stage_artifact_trust_barrier_check",
          "output_validity_check"
        ],
        "action_type": "memory_barrier_audit",
        "consumes": [
          "sacg_memory",
          "artifact.input.prepared_inputs"
        ],
        "id": "input_preparation.reconcile_sacg_memory_barriers",
        "on_failure": "Treat any open or inconsistent memory barrier as a downstream-consumption blocker and require explicit retry reconciliation before SACG extraction consumes current-stage artifacts.",
        "produces": [
          "artifact.input_audit.sacg_memory_reconciliation",
          "artifact.input_audit.stage_retry_or_backtrack_requests"
        ],
        "rationale": "The supplied memory state indicates no open retry requests, backtrack requests, or contamination barriers, but this must be recorded as checker-consumable stage evidence so downstream agents do not rely on natural-language memory.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_memory_update",
          "stage_retry_request",
          "stage_backtrack_request",
          "stage_artifact_trust_barrier"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "boundary_contract_check",
          "failure_localization_check",
          "stage_retry_request_check",
          "stage_backtrack_request_check",
          "stage_artifact_trust_barrier_check",
          "output_validity_check"
        ],
        "action_type": "contract_generation",
        "consumes": [
          "artifact.input.prepared_inputs",
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.numeric_template_report",
          "artifact.input_audit.board_runtime_tool_report",
          "artifact.input_audit.boundary_repair_report",
          "artifact.input_audit.sacg_memory_reconciliation"
        ],
        "id": "input_preparation.generate_sacg_extraction_contract",
        "on_failure": "Do not promote to SACG extraction. Localize the earliest failing boundary and produce a retry request for input-audit repair or a backtrack request only if the failure requires policy or design-space change.",
        "produces": [
          "artifact.input_audit.cross_layer_readiness_decision",
          "artifact.input_audit.sacg_extraction_input_contract",
          "artifact.input_audit.blocker_to_constraint_map"
        ],
        "rationale": "After specialist audits pass, generate the formal input contract for SACG extraction with explicit constraint bindings, blocker classifications, and not_run markers for later-stage evidence. This is the promotion boundary from input_preparation to SACG extraction.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "boundary_contract_generate",
          "sacg_validate",
          "sacg_static_check",
          "boundary_contract_check",
          "failure_slice_localization",
          "output_validity_check"
        ]
      },
      {
        "acceptance_checkers": [
          "repair_boundary_check",
          "human_boundary_check",
          "boundary_contract_check",
          "backend_bounded_recovery_action_check",
          "targeted_failed_checker_rerun",
          "output_validity_check"
        ],
        "action_type": "bounded_repair_or_backtrack",
        "consumes": [
          "artifact.input_audit.blocker_to_constraint_map",
          "artifact.input_audit.model_shape_report",
          "artifact.input_audit.numeric_template_report",
          "artifact.input_audit.board_runtime_tool_report",
          "artifact.input_audit.boundary_repair_report",
          "artifact.input.design_space",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.target_board_profile",
          "artifact.input.human_agent_boundary"
        ],
        "id": "input_preparation.resolve_policy_changing_or_ambiguous_inputs",
        "on_failure": "Keep SACG extraction blocked and preserve the original prepared_inputs as unpromoted. Do not guess board target names or silently change numeric/template/memory policy.",
        "produces": [
          "artifact.input_audit.stage_retry_or_backtrack_requests",
          "artifact.input.updated_prepared_inputs",
          "artifact.input.target_discovery_policy_updates"
        ],
        "rationale": "If the regenerated audits reveal ambiguity or inconsistency that would alter architecture, pipeline, memory layout, numeric policy, major templates, or board/app-shell target selection, the change is outside automatic audit repair and must be bounded by the human-agent boundary.",
        "requires_approval": true,
        "stage": "input_preparation",
        "tool_roles": [
          "repair_boundary_check",
          "architecture_review",
          "memory_runtime_repair",
          "bounded_template_repair",
          "backend_bounded_recovery_action",
          "human_boundary_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "llm_io_quality_check",
          "llm_semantic_extraction_check",
          "no_static_keyword_semantic_matching_check",
          "sacg_reference_check",
          "output_validity_check"
        ],
        "action_type": "stage_handoff",
        "consumes": [
          "artifact.input_audit.sacg_extraction_input_contract",
          "artifact.input_audit.cross_layer_readiness_decision",
          "artifact.input_audit.blocker_to_constraint_map"
        ],
        "id": "sacg_extraction.promote_after_input_gate_pass",
        "on_failure": "Route back to input_preparation only if the failure is caused by missing or contradictory input contract evidence; otherwise repair the SACG extraction/checker path. Do not modify golden outputs or loosen tolerances.",
        "produces": [
          "artifact.sacg.initial_graph",
          "artifact.sacg.extraction_report"
        ],
        "rationale": "Only after the input_preparation gate produces a passing sacg_extraction_input_contract should SACG extraction run semantic graph construction from the approved contract rather than from informal memory or compact summaries.",
        "requires_approval": false,
        "stage": "sacg_extraction",
        "tool_roles": [
          "sacg_validate",
          "llm_semantic_extraction",
          "no_static_keyword_semantic_matching",
          "output_validity_check"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 25,
      "max_duration_sec": 717.6816129840008,
      "max_prompt_bytes": 25377,
      "result_count": 5,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 1936.426369320001,
      "total_prompt_bytes": 125407
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 5,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/input/team/subtask_plan.json",
    "used_fallback_count": 0
  },
  "errors": [],
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
  "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
  "schema_version": "spatialaccagent.prepared_inputs.v0",
  "source_roles": {
    "board_materials_dir": "current-run target FPGA board, DDR/AXI, runtime, and sample-project materials",
    "model_source": "run-specific model architecture source",
    "quantization_materials_dir": "current-run numeric and quantization design materials",
    "task_spec": "run-specific objective and acceptance boundary",
    "template_dir": "trusted local hardware template library",
    "tool_materials_dir": "current-run EDA tool location, usage, and limitation materials"
  },
  "source_specs": {
    "board_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board",
    "model_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/qwen2_0_5b/model_config.json",
    "quantization_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization",
    "task_spec": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/examples/task_spec.md",
    "template_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel",
    "tool_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools"
  },
  "stage": "input_preparation",
  "status": "ready",
  "summary": {
    "llm_mode": "llm",
    "llm_provider": "OpenAI",
    "model_type": "qwen2",
    "operator_count": 9,
    "template_count": 13,
    "tool_protocols": 18
  },
  "warnings": [
    "sample_project_index failed to read one or more declared sample projects; later real-tool/remote probes must confirm these references"
  ]
}
</prepared_inputs_manifest>

<candidate_design_graph_summary>
{
  "constraint_ids": [
    "constraint.source.materials",
    "constraint.source.evidence",
    "constraint.task.goal",
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.numeric.policy",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.deployment.board",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.tool.profile",
    "constraint.tool.protocols",
    "constraint.case.adapter",
    "constraint.human.boundary",
    "constraint.cross_layer.input_consistency"
  ],
  "evidence_fields": [
    "board.fpga_part",
    "memory_system.axi_addr_width_bits",
    "memory_system.axi_clock",
    "memory_system.axi_data_bytes",
    "memory_system.axi_data_width_bits",
    "memory_system.axi_id_width_bits",
    "memory_system.axi_reset",
    "memory_system.axi_wstrb_width_bits",
    "memory_system.calibration_done_signal",
    "memory_system.core_side_interface_name",
    "memory_system.ddr_channels",
    "memory_system.ddr_word_width_bits",
    "memory_system.real_board_reference_rtl",
    "numeric_policy.default_precision",
    "numeric_policy.end_to_end_goal",
    "numeric_policy.exact_numerical_equivalence_required_for_current_run",
    "numeric_policy.policy_change_requires_rerun",
    "numeric_policy.rounding",
    "numeric_policy.saturation",
    "numeric_policy.source_type",
    "numeric_policy.tolerance_and_acceptance",
    "runtime_interface.board_run_command",
    "runtime_interface.control_protocol",
    "runtime_interface.ctrl_base",
    "runtime_interface.ddr_base",
    "runtime_interface.ddr_image_default",
    "runtime_interface.mimic_dir",
    "runtime_interface.output_abs",
    "runtime_interface.remote_host",
    "runtime_interface.xdma_id_default",
    "tool.remote_server.passwordless_login_configured",
    "tool.remote_server.ssh_command",
    "tool.vcs.executable",
    "tool.vcs.host",
    "tool.vcs.purpose",
    "tool.vcs.required_environment",
    "tool.vcs.smoke_script",
    "tool.vcs.stage0_ssh_probe_required",
    "tool.vcs.version_probe_command",
    "tool.verilator.location",
    "tool.verilator.purpose",
    "tool.vivado.bitstream_script",
    "tool.vivado.confirmed_version",
    "tool.vivado.executable",
    "tool.vivado.final_synthesis_bitstream_required",
    "tool.vivado.host",
    "tool.vivado.purpose",
    "tool.vivado.required_environment",
    "tool.vivado.stage0_ssh_probe_required",
    "tool.vivado.version_probe_command"
  ],
  "input_groups": {
    "evidence": [
      "field_evidence"
    ],
    "materials": [
      "material_index",
      "sample_project_index"
    ],
    "tools": [
      "tool_profile",
      "tool_availability",
      "tool_protocols",
      "case_adapter"
    ]
  },
  "node_ids": [
    "node.input_materials",
    "node.input_evidence",
    "node.task",
    "node.model",
    "node.numeric_policy",
    "node.template_library",
    "node.design_space",
    "node.target_board",
    "node.tool_profile",
    "node.tool_protocols",
    "node.case_adapter",
    "node.human_boundary",
    "node.model_op.00_rms_norm_1",
    "node.model_op.01_self_attention",
    "node.model_op.02_residual_add_1",
    "node.model_op.03_rms_norm_2",
    "node.model_op.04_mlp_gate_proj",
    "node.model_op.05_mlp_up_proj",
    "node.model_op.06_activation_mul",
    "node.model_op.07_mlp_down_proj",
    "node.model_op.08_residual_add_2"
  ],
  "num_constraints": 16,
  "num_edges": 8,
  "num_nodes": 21,
  "source_material_counts": {
    "board_files": 0,
    "quantization_files": 0,
    "sample_project_refs": 7,
    "sample_project_samples": 7,
    "tool_files": 0
  },
  "tool_names": [
    "vcs",
    "verilator",
    "vivado"
  ]
}
</candidate_design_graph_summary>

<validation_errors>
[]
</validation_errors>

<design_team>
{
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/constraint_extraction/team/team_aggregate.json",
  "approval_required_for": [
    "Adding, removing, or materially modifying trusted templates or template metadata/operator coverage outside artifact.input.template_library and artifact.input.template_metadata.",
    "Any architecture change outside artifact.input.design_space or beyond the approved template library.",
    "Any attempt to consume fallback diagnostics as successful LLM agent decisions under the enforced LLM policy",
    "Any backend/app-shell target selection when supplied board materials and real Vivado/tool evidence are ambiguous",
    "Any board/app-shell target-selection decision when supplied materials and real tool evidence are ambiguous.",
    "Any change to DDR/AXI address map, DDR memory layout, transfer unit layout, or host/device buffer ownership.",
    "Any change to board runtime ABI, deployment target, app-shell target_discovery_policy, or backend board integration target.",
    "Any change to memory layout, data packing/order, transfer unit, AXI/DDR mapping, runtime ABI, or board profile facts",
    "Any change to numeric precision, scaling, accumulator width, tolerance, or golden-comparison policy",
    "Any graph repair that changes architecture design space, pipeline structure, or major template family",
    "Any inferred or changed sequence-length assumption, tensor layout/data order, hidden dimension, attention/head relationship, residual/operator ordering, architecture/pipeline mapping, memory layout, numeric-policy interpretation, or major template binding not directly evidenced by artifact.input.model_config and accepted SACG constraints.",
    "Any major template replacement or free-form RTL rewrite outside trusted bounded-template repair.",
    "Any memory-layout, address-map, DDR/AXI transfer-unit, or runtime-ABI change.",
    "Any modification to human-agent boundary, approval gates, or repair-boundary policy itself.",
    "Any numeric-policy change, including precision, scaling, tolerance, rounding, saturation, or golden-reference semantics.",
    "Any pipeline restructuring or verification-stage reordering that changes the leaf -> single-transformer-layer -> board-accurate AXI/DDR repair hierarchy.",
    "Any stream order, transfer-count, or liveness-contract change that alters pipeline/data-order semantics.",
    "Any tool profile/protocol change that introduces unavailable tools, changes required real-tool evidence, or substitutes an unapproved equivalent tool.",
    "Changing architecture/design-space parameters that affect tiling, parallelism, pipeline structure, buffer sizing, transfer unit, or resource budget.",
    "Changing memory layout, board/runtime ABI assumptions, or board resource assumptions to resolve numeric/template/resource binding conflicts.",
    "Changing numeric precision, quantization mode, scaling, rounding, saturation, accumulator width, or numeric comparison tolerance from artifact.input.numeric_policy."
  ],
  "completed_subtasks": 5,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/constraint_extraction/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "sacg_reference_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "prepared_inputs_manifest",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "artifact.input.field_evidence"
      ],
      "id": "constraint_extraction.run_sacg_binding_static_audit",
      "on_failure": "Block promotion to constraint_graph_auditor; emit a bounded constraint-enrichment request listing missing artifact-to-constraint evidence bindings and mark unproven evidence as not_run.",
      "produces": [
        "artifact.constraint_extraction.data_memory_runtime_review",
        "artifact.constraint_extraction.sacg_binding_evidence_report"
      ],
      "rationale": "The compact summary shows relevant artifact and constraint classes, but not the actual evidence bindings. A SACG static/reference audit must prove that the full graph contains nodes, edges, and cited evidence for the required data/memory/runtime/tool constraints.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "sacg_reference_check",
        "required_real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "stream_plan_check",
        "transfer_count_check",
        "data_order_trace_check"
      ],
      "action_type": "stream_memory_plan_validation",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_metadata",
        "artifact.input.target_board_profile",
        "artifact.input.field_evidence"
      ],
      "id": "constraint_extraction.audit_stream_order_transfer_liveness",
      "on_failure": "Keep stream/data-order constraints unapproved; route the missing or inconsistent stream fields to bounded repair and require rerun of the failed stream/transfer checker before any code generation or functional simulation consumes the graph.",
      "produces": [
        "stream_memory_risk_report",
        "artifact.constraint_extraction.stream_order_transfer_liveness_findings"
      ],
      "rationale": "Stream order, transfer count/unit, and liveness assumptions are required by this role, but are not visible in the compact summary. The static stream audit must bind model/template/runtime data order before later simulation or backend stages rely on it.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "stream_plan_check",
        "transfer_count_check",
        "data_order_trace_check"
      ]
    },
    {
      "acceptance_checkers": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "case_axi_ddr_interface",
        "case_runtime_abi_check",
        "deployment_board_check"
      ],
      "action_type": "memory_runtime_plan_validation",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.target_board_profile",
        "artifact.input.field_evidence",
        "artifact.input.case_adapter",
        "artifact.input.tool_profile"
      ],
      "id": "constraint_extraction.audit_ddr_axi_runtime_addr_map",
      "on_failure": "Do not promote memory/runtime constraints; localize the earliest missing or inconsistent boundary among board profile, DDR/AXI map, runtime ABI, or deployment target and request bounded repair with approval for any memory-layout or ABI change.",
      "produces": [
        "board_runtime_constraint_findings",
        "artifact.constraint_extraction.ddr_axi_addr_map_findings",
        "artifact.constraint_extraction.runtime_abi_deployment_findings"
      ],
      "rationale": "DDR layout, AXI address mapping, board runtime ABI, and deployment target are named audit targets, but detailed map fields are not visible. The memory/runtime plan must be checked against board evidence before downstream backend or runtime packaging.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "memory_runtime_plan_check",
        "addr_map_check",
        "case_axi_ddr_interface",
        "case_runtime_abi_check",
        "deployment_board_check"
      ]
    },
    {
      "acceptance_checkers": [
        "tool_protocol_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "tool_protocol_evidence_validation",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "artifact.input.field_evidence"
      ],
      "id": "constraint_extraction.audit_tool_profile_availability_protocols",
      "on_failure": "Mark affected tools unavailable or not_run in the evidence map; block any downstream action requiring those tools until protocol/availability evidence is repaired or an approved equivalent is added.",
      "produces": [
        "tool_availability_evidence_map",
        "artifact.constraint_extraction.tool_protocol_findings"
      ],
      "rationale": "Tool profile, availability, and protocols are present as input artifacts, but the summary does not prove their availability/status bindings or invocation protocols. This audit prevents downstream claims based on unavailable tools or fallback diagnostics.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "tool_protocol_check",
        "required_real_tool_evidence_check",
        "real_tool_evidence_check"
      ]
    },
    {
      "acceptance_checkers": [
        "backend_app_shell_integration_contract_static_check",
        "backend_app_shell_target_discovery_check",
        "backend_app_shell_target_hint_synthesis_check",
        "required_real_tool_evidence_check"
      ],
      "action_type": "bounded_target_discovery",
      "consumes": [
        "artifact.input.target_board_profile",
        "artifact.input.field_evidence",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "candidate_design_graph_summary",
        "board_runtime_constraint_findings"
      ],
      "id": "backend_board.prepare_bounded_app_shell_target_discovery_if_needed",
      "on_failure": "Keep board runtime bitstream and app-shell integration blocked; require bounded approval instead of selecting unproven target names.",
      "produces": [
        "artifact.backend_board.app_shell_target_discovery_contract",
        "artifact.backend_board.target_discovery_policy_update",
        "artifact.backend_board.ambiguous_target_approval_request"
      ],
      "rationale": "Deployment target and board runtime ABI must not be guessed. If the full evidence is ambiguous, the LLM board-integration role should synthesize a bounded target_discovery_policy update from supplied board materials and real Vivado/backend evidence, then require approval for ambiguous target selection.",
      "requires_approval": true,
      "stage": "backend_board",
      "tool_roles": [
        "app_shell_target_discovery_contract",
        "app_shell_target_hint_synthesis",
        "case_board_interface_discovery"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "sacg_static_check",
        "memory_runtime_plan_check",
        "stream_plan_check",
        "tool_protocol_check",
        "addr_map_check",
        "stage_retry_request_check",
        "stage_artifact_trust_barrier_check"
      ],
      "action_type": "bounded_repair",
      "consumes": [
        "artifact.constraint_extraction.sacg_binding_evidence_report",
        "stream_memory_risk_report",
        "board_runtime_constraint_findings",
        "tool_availability_evidence_map",
        "artifact.constraint_extraction.tool_protocol_findings"
      ],
      "id": "constraint_extraction.apply_bounded_constraint_enrichment_on_failed_audit",
      "on_failure": "Open a stage_backtrack_request with the failed checker evidence and preserve a trust barrier against consuming the unpromoted graph in later stages.",
      "produces": [
        "artifact.constraint_extraction.refined_design_graph_patch",
        "artifact.constraint_extraction.updated_data_memory_runtime_review",
        "sacg_memory_update_entry"
      ],
      "rationale": "If the audits find missing stream, memory/runtime, address-map, deployment, or tool evidence, the current graph needs a bounded SACG repair rather than downstream agents relying on unstated assumptions.",
      "requires_approval": true,
      "stage": "constraint_extraction",
      "tool_roles": [
        "memory_runtime_repair",
        "repair_boundary_check",
        "sacg_memory_update",
        "stage_retry_request",
        "stage_artifact_trust_barrier"
      ]
    },
    {
      "acceptance_checkers": [
        "llm_semantic_extraction_check",
        "model_config_check",
        "sacg_reference_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "artifact.input.model_config",
        "candidate_design_graph_summary",
        "constraint.model.decoder",
        "constraint.shape.model",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "ce_model_shape_explicit_semantics_audit",
      "on_failure": "Do not promote the initial design graph; emit a bounded gap report listing missing or ambiguous facts and route to graph repair or backtrack.",
      "produces": [
        "artifact.constraint_extraction.model_shape_review",
        "model_shape_gap_report",
        "sacg_node_edge_reference_findings"
      ],
      "rationale": "The visible candidate graph provides counts but not the explicit model-shape bindings required to approve decoder semantics and shape relationships.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "llm_semantic_extraction",
        "model_config_check",
        "sacg_reference_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "sacg_static_check"
      ],
      "action_type": "cross_layer_consistency_audit",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols",
        "candidate_design_graph_summary",
        "constraint.model.decoder",
        "constraint.shape.model",
        "constraint.numeric.policy",
        "constraint.template.library",
        "constraint.arch.design_space",
        "constraint.deployment.board",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.tool.protocols",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "ce_model_shape_cross_layer_constraint_link_audit",
      "on_failure": "Classify missing links as current-stage graph gaps when they prevent model/shape facts from being referenced; otherwise hand them off as later-stage consistency actions with exact constraint IDs.",
      "produces": [
        "model_shape_cross_layer_link_matrix",
        "constraint_graph_auditor_handoff_findings"
      ],
      "rationale": "Model-shape facts must be reference-linked to cross-layer input consistency so later numeric, template, memory, runtime, implementation, and board checkers can consume them without relying on implicit assumptions.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_reference_check",
        "team_aggregate"
      ]
    },
    {
      "acceptance_checkers": [
        "stage_backtrack_request_check",
        "sacg_static_check",
        "sacg_memory_check",
        "model_config_check",
        "sacg_reference_check"
      ],
      "action_type": "bounded_repair_or_backtrack",
      "consumes": [
        "model_shape_gap_report",
        "sacg_node_edge_reference_findings",
        "candidate_design_graph_summary",
        "artifact.input.model_config",
        "sacg_memory"
      ],
      "id": "ce_bounded_model_shape_graph_repair_if_needed",
      "on_failure": "Keep the design graph blocked for downstream codegen and verification; require bounded approval for any non-evidenced shape, sequence, architecture, pipeline, memory-layout, or numeric-policy assumption.",
      "produces": [
        "candidate_design_graph_summary.refined_model_shape_bindings",
        "stage_backtrack_request_if_model_config_insufficient",
        "sacg_memory.model_shape_audit_update"
      ],
      "rationale": "If the audit finds missing explicit nodes or edges, the graph must be repaired from model_config evidence or a backtrack request issued; no later stage should consume implicit semantics.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "stage_backtrack_request",
        "sacg_validate",
        "sacg_memory_update"
      ]
    },
    {
      "acceptance_checkers": [
        "numeric_policy_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_static_check",
      "consumes": [
        "artifact.input.numeric_policy",
        "artifact.input.model_config",
        "candidate_design_graph_summary",
        "constraint.numeric.policy",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "cte_numeric_policy_binding_check",
      "on_failure": "Mark numeric policy binding as a current-stage blocker; create a bounded repair or backtrack request for numeric policy clarification and do not allow code generation, template binding promotion, or golden tolerance changes.",
      "produces": [
        "numeric_policy_binding_findings"
      ],
      "rationale": "Numeric precision and quantization assumptions must be bound to constraint.numeric.policy and cross-checked against model/shape facts before downstream template or verification stages consume them.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "numeric_policy_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "template_coverage_check",
        "template_binding_static_check",
        "sacg_static_check"
      ],
      "action_type": "template_coverage_static_check",
      "consumes": [
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "candidate_design_graph_summary",
        "constraint.template.library",
        "constraint.arch.design_space",
        "constraint.numeric.policy"
      ],
      "id": "cte_template_coverage_binding_check",
      "on_failure": "Block downstream code generation and template promotion; route uncovered operators or datatype/shape mismatches to an approved template substitution or approved template-library extension, not free-form RTL.",
      "produces": [
        "template_coverage_gap_report",
        "template_binding_findings"
      ],
      "rationale": "Trusted template library coverage must be checked against required operators, datatypes, shapes, and design-space choices so missing coverage cannot become implicit free-form RTL implementation.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "template_coverage_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "sacg_static_check"
      ],
      "action_type": "parameter_binding_static_check",
      "consumes": [
        "artifact.input.design_space",
        "artifact.input.numeric_policy",
        "artifact.input.template_metadata",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "candidate_design_graph_summary",
        "constraint.arch.design_space",
        "constraint.deployment.board",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.tool.profile",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "cte_parameter_resource_risk_binding_check",
      "on_failure": "Treat unbound parameters or resource assumptions as a current-stage blocker; route to bounded architecture/design-space review with approval required for any architecture, pipeline, memory layout, or resource-budget change.",
      "produces": [
        "parameter_binding_risk_notes",
        "resource_assumption_binding_findings"
      ],
      "rationale": "Architecture parameters and resource-risk assumptions must be explicit SACG facts connected to design-space, numeric width, template metadata, board, and tool constraints before later synthesis or backend diagnosis.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "parameter_binding_static_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "sacg_reference_check"
      ],
      "action_type": "sacg_constraint_review_aggregate",
      "consumes": [
        "numeric_policy_binding_findings",
        "template_coverage_gap_report",
        "template_binding_findings",
        "parameter_binding_risk_notes",
        "resource_assumption_binding_findings",
        "candidate_design_graph_summary"
      ],
      "id": "cte_emit_numeric_template_review",
      "on_failure": "Keep the handoff to constraint_extraction.constraint_graph_auditor blocked until the review artifact cites checker outcomes or explicitly records not_run status for each required check.",
      "produces": [
        "artifact.constraint_extraction.numeric_template_review"
      ],
      "rationale": "The graph auditor needs a single SACG-bound review artifact that distinguishes present input artifact classes from checker-proven numeric/template/parameter bindings.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "team_aggregate",
        "sacg_validate"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "task_card_check",
        "boundary_contract_check",
        "verification_plan_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "artifact.input.task_card",
        "artifact.input.case_adapter",
        "candidate_design_graph_summary",
        "validation_errors",
        "constraint.task.goal",
        "constraint.case.adapter",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.run_task_case_adapter_boundary_static_checks",
      "on_failure": "Block constraint_extraction promotion, record the violated constraint IDs, and route the failed slice to failure localization; do not relax verification semantics or consume the graph downstream.",
      "produces": [
        "task_case_adapter_alignment_report",
        "artifact.constraint_extraction.verification_boundary_review"
      ],
      "rationale": "The required task and case-adapter artifacts and constraints are present, but the supplied summary does not expose detailed edge bindings or checker evidence. Static checks must prove task-goal to case-adapter alignment before promotion.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "sacg_static_check",
        "task_card_check",
        "verification_plan_static_check",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "human_boundary_check",
        "repair_boundary_check",
        "boundary_contract_check"
      ],
      "action_type": "boundary_contract_validation",
      "consumes": [
        "artifact.input.human_agent_boundary",
        "artifact.input.case_adapter",
        "artifact.input.design_space",
        "artifact.input.template_library",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols",
        "candidate_design_graph_summary",
        "constraint.human.boundary",
        "constraint.case.adapter",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.validate_human_and_repair_boundaries",
      "on_failure": "Keep the stage blocked until explicit approval gates and bounded repair clauses are added; if the fix changes architecture, pipeline, memory layout, numeric policy, or major templates, require human approval before promotion.",
      "produces": [
        "human_boundary_and_repair_gate_report",
        "artifact.constraint_extraction.repair_boundary_gate_contract"
      ],
      "rationale": "The human-boundary artifact and constraint are present, but the summary does not prove that approval requirements and repair boundaries are explicit. The boundary contract must define what agents may repair automatically and what requires human approval.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "boundary_contract_generate",
        "human_boundary_check",
        "repair_boundary_check",
        "boundary_contract_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "memory_runtime_plan_check",
        "tool_protocol_check",
        "sacg_reference_check"
      ],
      "action_type": "cross_layer_consistency_review",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "artifact.input.case_adapter",
        "artifact.input.human_agent_boundary",
        "candidate_design_graph_summary",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.audit_cross_layer_boundary_bindings",
      "on_failure": "Classify the failed binding as a current-stage blocker, localize to the violated SACG constraint, and hand off to constraint_extraction.constraint_graph_auditor for bounded graph repair.",
      "produces": [
        "artifact.constraint_extraction.cross_layer_boundary_consistency_report"
      ],
      "rationale": "Later failures can only be localized if model, shape, numeric, data-order, memory, runtime, implementation, tool, and board facts are bound into the task/case/human-boundary constraints. The compact summary does not prove these bindings.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_static_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "memory_runtime_plan_check",
        "tool_protocol_check",
        "sacg_reference_check"
      ]
    },
    {
      "acceptance_checkers": [
        "failure_localization_check",
        "causal_repair_context_check",
        "stage_retry_request_check",
        "stage_artifact_trust_barrier_check",
        "targeted_failed_checker_rerun"
      ],
      "action_type": "failure_localization_and_bounded_repair_context",
      "consumes": [
        "task_case_adapter_alignment_report",
        "human_boundary_and_repair_gate_report",
        "artifact.constraint_extraction.cross_layer_boundary_consistency_report",
        "candidate_design_graph_summary",
        "sacg_memory"
      ],
      "id": "constraint_extraction.create_failure_localization_repair_context_on_checker_failure",
      "on_failure": "Do not promote the candidate graph. Escalate only if the needed repair would alter an approval-gated architecture, pipeline, memory-layout, numeric-policy, or major-template decision.",
      "produces": [
        "artifact.constraint_extraction.localized_boundary_failures",
        "artifact.constraint_extraction.bounded_repair_context",
        "optional.stage_retry_request",
        "optional.stage_artifact_trust_barrier"
      ],
      "rationale": "If any current-stage checker fails, the repair must be driven by checker evidence and SACG constraints, not by static scripts or human memory. This action packages the causal slice and creates retry/trust-barrier records when needed.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "failure_slice_localization",
        "causal_repair_context_pack",
        "stage_retry_request",
        "stage_artifact_trust_barrier",
        "targeted_failed_checker_rerun"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "sacg_reference_check",
        "stage_artifact_trust_barrier_check",
        "llm_io_quality_check",
        "output_validity_check"
      ],
      "action_type": "evidence_gate",
      "consumes": [
        "candidate_design_graph_summary",
        "prepared_inputs_manifest",
        "validation_errors",
        "artifact.constraint_extraction.model_shape_review",
        "artifact.constraint_extraction.numeric_template_review",
        "artifact.constraint_extraction.data_memory_runtime_review",
        "artifact.constraint_extraction.verification_boundary_review",
        "artifact.input.material_index",
        "artifact.input.sample_project_index",
        "artifact.input.field_evidence",
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
        "artifact.input.case_adapter",
        "artifact.input.human_agent_boundary"
      ],
      "id": "constraint_extraction.run_current_stage_promotion_gate",
      "on_failure": "Do not promote the candidate graph. Emit the failed checker evidence and route to bounded graph repair or approval/backtrack if the fix would alter architecture, numeric policy, memory layout, template selection, runtime ABI, or board facts.",
      "produces": [
        "artifact.constraint_extraction.audited_design_graph_closure",
        "constraint_extraction_promotion_decision",
        "cross_layer_consistency_gap_list"
      ],
      "rationale": "The visible graph has no validation_errors or failed_invariants, but promotion requires explicit current-stage checker evidence binding the candidate graph and specialist reviews to SACG constraints.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "sacg_static_check",
        "sacg_reference_check",
        "stage_artifact_trust_barrier",
        "llm_io_quality_check",
        "output_validity_check"
      ]
    },
    {
      "acceptance_checkers": [
        "repair_boundary_check",
        "sacg_static_check",
        "sacg_reference_check",
        "human_boundary_check"
      ],
      "action_type": "bounded_graph_repair",
      "consumes": [
        "artifact.constraint_extraction.audited_design_graph_closure",
        "cross_layer_consistency_gap_list",
        "candidate_design_graph_summary",
        "prepared_inputs_manifest"
      ],
      "id": "constraint_extraction.repair_graph_binding_gaps_if_gate_fails",
      "on_failure": "If repair cannot stay within metadata/evidence/edge binding boundaries, stop promotion and create an approval or backtrack request; do not rewrite numeric policy, architecture, memory layout, template family, or board/runtime facts as an unapproved repair.",
      "produces": [
        "artifact.constraint_extraction.repaired_design_graph_summary",
        "artifact.constraint_extraction.repaired_cross_layer_edge_map",
        "artifact.constraint_extraction.repair_delta_log"
      ],
      "rationale": "If the evidence gate reports missing references, absent not_run records, or weak cross-layer edge bindings, repair only SACG metadata, evidence tags, and constraint edges; do not change design policy or hardware intent without approval.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "team_aggregate",
        "sacg_validate",
        "repair_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_memory_check",
        "stage_artifact_trust_barrier_check",
        "stage_backtrack_request_check"
      ],
      "action_type": "memory_update",
      "consumes": [
        "artifact.constraint_extraction.audited_design_graph_closure",
        "constraint_extraction_promotion_decision",
        "cross_layer_consistency_gap_list",
        "artifact.constraint_extraction.repair_delta_log_if_any"
      ],
      "id": "constraint_extraction.update_sacg_memory_after_audit",
      "on_failure": "Keep downstream stages from consuming stale memory; create a contamination barrier for the candidate graph if promotion/blocker status cannot be recorded.",
      "produces": [
        "sacg_memory_update_recommendations",
        "sacg_memory.patch.constraint_extraction_audit"
      ],
      "rationale": "SACG memory is the shared long-context design memory and must preserve this audit decision, any gap list, and the absence or presence of barriers/backtrack requests for downstream stages.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_memory_update",
        "stage_artifact_trust_barrier"
      ]
    },
    {
      "acceptance_checkers": [
        "task_card_check",
        "model_config_check",
        "numeric_policy_check",
        "template_coverage_check",
        "parameter_binding_static_check",
        "memory_runtime_plan_check",
        "tool_protocol_check",
        "human_boundary_check"
      ],
      "action_type": "downstream_handoff_gate",
      "consumes": [
        "artifact.constraint_extraction.audited_design_graph_closure",
        "constraint_extraction_promotion_decision",
        "cross_layer_consistency_gap_list",
        "artifact.input.design_space",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.numeric_policy",
        "artifact.input.target_board_profile",
        "artifact.input.tool_protocols",
        "artifact.input.human_agent_boundary"
      ],
      "id": "architecture_planning.consume_promoted_constraint_graph",
      "on_failure": "Return failed handoff evidence to constraint_extraction as a bounded backtrack request; do not select templates or alter numeric, memory, runtime, or board policy without approval.",
      "produces": [
        "artifact.architecture_planning.constraint_graph_handoff_contract",
        "artifact.architecture_planning.initial_parameter_binding_plan"
      ],
      "rationale": "After current-stage closure passes, architecture_planning must consume the audited graph and re-check model, numeric, template, memory/runtime, tool, and human-boundary constraints before binding parameters or choosing templates.",
      "requires_approval": false,
      "stage": "architecture_planning",
      "tool_roles": [
        "architecture_review",
        "parameter_binding_static_check",
        "template_coverage_check",
        "memory_runtime_plan_check",
        "human_boundary_check"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 21,
    "max_duration_sec": 535.5270560190002,
    "max_prompt_bytes": 25598,
    "result_count": 5,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 1070.4660308450002,
    "total_prompt_bytes": 127319
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 5,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/constraint_extraction/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

<sacg_memory>
{}
</sacg_memory>

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
