<agent>
initial_design_graph_agent
</agent>

<task>
Review the initial design graph extracted from prepared inputs. You are the design-intake lead in a chip accelerator team: check whether model, shape, numeric policy, template, board DDR/AXI/runtime, tool, evidence, and human-boundary facts are represented clearly enough for later architecture, code generation, verification, and board implementation agents.
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

<prepared_inputs_manifest>
{
  "design_team": {
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/input/team/team_aggregate.json",
    "approval_required_for": [
      "Adopting a planned_tool.<short_name> or planned_checker.<short_name> as an approved workaround for a missing checker-verified capability",
      "Any change to artifact.input.design_space hard_constraints, objectives, or qor_targets",
      "Any change to artifact.input.human_agent_boundary or constraint.human.boundary",
      "Any major template_library/template_metadata binding override outside the already selected template set",
      "Changing numeric precision/quantization policy, compare tolerance, or memory layout away from a case-adapter-supplied value.",
      "Promoting to stage_sacg_extraction while unresolved numeric, DDR/AXI, runtime, or deployment facts remain open in artifact.stage0.board_open_risks.",
      "Substituting missing numeric_policy or target_board_profile facts with inferred defaults, generic board names, DUT output, or generated expected values."
    ],
    "completed_subtasks": 4,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/input/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "boundary_contract_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.material_index",
          "artifact.input.sample_project_index",
          "artifact.input.case_adapter",
          "candidate_stage_artifact.prepared_inputs"
        ],
        "id": "input_preparation.input_evidence_engineer.reify_source_material_trace",
        "on_failure": "Keep input-preparation readiness blocked, record the missing or conflicting source identity as not_run/gap in artifact.stage0.source_material_trace, and request upstream material_index/sample_project_index rows before SACG extraction.",
        "produces": [
          "artifact.stage0.source_material_trace"
        ],
        "rationale": "material_index and sample_project_index are not visible in the compact prepared_inputs.inputs slice, so the current run identity and source-project scope must be bound to the visible run_dir and case_adapter case_id before the evidence audit can pass.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_static_check",
          "boundary_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "boundary_contract_check"
        ],
        "action_type": "tool_protocol_review",
        "consumes": [
          "artifact.input.case_adapter",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols"
        ],
        "id": "input_preparation.input_evidence_engineer.align_tool_capability_protocols",
        "on_failure": "Mark tool capability alignment as not_run or conflicted in the audit, block promotion to SACG extraction, and request current-run tool_profile/tool_availability details from the upstream input registry.",
        "produces": [
          "artifact.stage0.input_evidence_audit.tool_alignment"
        ],
        "rationale": "case_adapter exposes acceptance and protocol-related keys, but tool_profile and tool_availability detailed rows are not visible in the compact slice; tool_protocol_check must confirm that case-adapter protocols are supported by the current tool set.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "boundary_contract_check"
        ]
      },
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "boundary_contract_check",
          "sacg_static_check"
        ],
        "action_type": "evidence_gate_review",
        "consumes": [
          "artifact.input.case_adapter",
          "artifact.input.field_evidence_candidates",
          "artifact.input.field_evidence"
        ],
        "id": "input_preparation.input_evidence_engineer.gate_field_evidence",
        "on_failure": "Keep field_evidence outside the accepted-evidence boundary, record the gate as not_run/failed, and do not allow downstream SACG extraction to consume it as accepted evidence.",
        "produces": [
          "artifact.stage0.input_evidence_audit"
        ],
        "rationale": "field_evidence_candidates and field_evidence are present, but the visible candidate artifact does not show checker evidence that the candidates were accepted through case_adapter.evidence_gates; this must be verified before accepted field evidence enters SACG extraction.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "boundary_contract_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "model_config_check",
          "task_card_check"
        ],
        "action_type": "static_evidence_gathering",
        "consumes": [
          "artifact.input.model_config",
          "artifact.input.task_card",
          "state_summary.sacg_memory_truth"
        ],
        "id": "stage0.run_model_task_checks",
        "on_failure": "Do not pass stage0 or promote to SACG extraction; record missing model facts as artifact.stage0.model_open_facts and request case-adapter model_config/task_card evidence.",
        "produces": [
          "artifact.stage0.model_input_audit",
          "artifact.stage0.model_open_facts"
        ],
        "rationale": "Run the registered model_config and task_card checkers on the declared input artifacts to determine whether decoder-block, shape, head, sequence, attention, residual, and operator-order facts are present and bound to model constraints rather than inferred from board or numeric artifacts.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_validate",
          "model_config_check",
          "task_card_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check"
        ],
        "action_type": "sacg_memory_handoff",
        "consumes": [
          "artifact.stage0.model_input_audit",
          "artifact.stage0.model_open_facts"
        ],
        "id": "stage0.record_model_open_facts",
        "on_failure": "Keep artifact.stage0.model_open_facts open and route to the toolchain boundary gate; do not treat missing model facts as hidden or inferred details.",
        "produces": [
          "sacg_memory.model_intake_open_facts_record"
        ],
        "rationale": "Persist the audit and open model facts in shared sacg_memory so downstream toolchain_boundary_engineer and stage_sacg_extraction consume only checker-bound model evidence.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_memory_update"
        ]
      },
      {
        "acceptance_checkers": [
          "artifact_hash_check",
          "sacg_static_check"
        ],
        "action_type": "artifact_identity_verification",
        "consumes": [
          "artifact.input.numeric_policy",
          "artifact.input.target_board_profile",
          "artifact.input.case_adapter"
        ],
        "id": "verify.numeric_board_artifact_identity",
        "on_failure": "If either artifact is absent or cannot be hash-bound to the current run_dir/prepared_inputs identity, record a board_open_risks entry and do not run numeric/board content checks against guessed paths; request the case adapter to re-emit the input artifact.",
        "produces": [
          "artifact.stage0.numeric_board_input_hashes"
        ],
        "rationale": "The compact prepared_inputs slice omits detailed keys for artifact.input.numeric_policy and artifact.input.target_board_profile even though the state summary declares them. Hash-check both current artifacts before any content audit to distinguish a missing input from an omitted detail row.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "artifact_hash_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "numeric_policy_check",
          "addr_map_check"
        ],
        "action_type": "numeric_board_input_review",
        "consumes": [
          "artifact.input.numeric_policy",
          "artifact.input.target_board_profile",
          "constraint.numeric.policy",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.deployment.board",
          "artifact.stage0.numeric_board_input_hashes"
        ],
        "id": "check.numeric_policy_and_board_facts",
        "on_failure": "If numeric_policy_check or addr_map_check reports missing precision/quantization policy, DDR/AXI address map, transfer-width, burst, runtime, or deployment facts, do not derive defaults from DUT output or generic knowledge. Record each exact missing field in artifact.stage0.board_open_risks and hand off as a blocker to input_preparation.toolchain_boundary_engineer and stage_sacg_extraction. If checker execution raises an artifact-location exception, return to verify.numeric_board_artifact_identity.",
        "produces": [
          "artifact.stage0.numeric_board_audit",
          "artifact.stage0.board_open_risks"
        ],
        "rationale": "Bind explicit facts from numeric_policy and target_board_profile to the named numeric, memory, runtime, and deployment constraints before downstream SACG extraction. Missing facts must become open risks, not inferred defaults.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "numeric_policy_check",
          "addr_map_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_memory_check",
          "sacg_static_check"
        ],
        "action_type": "sacg_memory_update",
        "consumes": [
          "artifact.stage0.numeric_board_audit",
          "artifact.stage0.board_open_risks"
        ],
        "id": "record.numeric_board_open_risks",
        "on_failure": "Do not clear the numeric/board gap. Keep stage_sacg_extraction gated for unresolved facts and mark the SACG memory update failed for replanning.",
        "produces": [
          "state_summary.sacg_memory.numeric_board_input_review_lesson"
        ],
        "rationale": "Persist checker-bound numeric/board gaps and evidence provenance in SACG memory so downstream toolchain-boundary and extraction agents receive the open-risk list without receiving invented board facts.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_memory_update"
        ]
      },
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "template_binding_static_check",
          "human_boundary_check",
          "repair_boundary_check",
          "sacg_static_check"
        ],
        "action_type": "input_artifact_validation",
        "consumes": [
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.tool_protocols",
          "artifact.input.human_agent_boundary",
          "artifact.input.case_adapter"
        ],
        "id": "stage0.validate_tool_template_human_boundary",
        "on_failure": "Block stage_sacg_extraction, record the violated constraint/artifact as an input-preparation blocker in sacg_memory, and return the bounded repair or approval item to the owning specialist; do not rewrite the inputs or bypass the checker.",
        "produces": [
          "artifact.stage0.toolchain_boundary_audit"
        ],
        "rationale": "The readiness gate must be grounded in checker evidence that template_library/template_metadata bind to the selected design_space and case_adapter, tool_protocols support checker-verified execution, and human_agent_boundary defines approval/forbidden actions without contradictory auto-allowed paths.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "template_binding_static_check",
          "human_boundary_check",
          "repair_boundary_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "repair_boundary_check",
          "tool_protocol_check",
          "human_boundary_check",
          "template_binding_static_check"
        ],
        "action_type": "readiness_gate_aggregation",
        "consumes": [
          "artifact.stage0.model_input_audit",
          "artifact.stage0.numeric_board_audit",
          "artifact.stage0.input_evidence_audit",
          "artifact.stage0.toolchain_boundary_audit"
        ],
        "id": "stage0.merge_peer_audits_to_readiness_gate",
        "on_failure": "Keep artifact.stage0.input_readiness_gate unapproved, block stage_sacg_extraction, and route each failed invariant back to the responsible specialist with the consumed artifact and checker status; do not aggregate contradictory audit findings into a false ready state.",
        "produces": [
          "artifact.stage0.input_readiness_gate"
        ],
        "rationale": "The toolchain-boundary audit is necessary but not sufficient; model, numeric/board, and field-evidence specialist findings must be merged into one checker-verified readiness decision before SACG extraction can consume the aggregate.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "team_aggregate",
          "sacg_validate",
          "repair_boundary_check",
          "tool_protocol_check",
          "human_boundary_check",
          "template_binding_static_check",
          "sacg_static_check"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 10,
      "max_duration_sec": 151.7565635360079,
      "max_prompt_bytes": 39262,
      "result_count": 4,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 417.2179059070768,
      "total_prompt_bytes": 155605
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 4,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/input/team/subtask_plan.json",
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
  "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020",
  "schema_version": "spatialaccagent.prepared_inputs.v0",
  "source_roles": {
    "board_materials_dir": "current-run target FPGA board, DDR/AXI, runtime, and sample-project materials",
    "model_dir": "run-specific target checkpoint directory",
    "model_source": "run-specific model architecture source",
    "quantization_materials_dir": "current-run numeric and quantization design materials",
    "task_spec": "run-specific objective and acceptance boundary",
    "template_dir": "trusted local hardware template library",
    "tool_materials_dir": "current-run EDA tool location, usage, and limitation materials"
  },
  "source_specs": {
    "board_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board",
    "model_dir": "/home/remote/.cache/huggingface/hub/models--openai-community--gpt2/snapshots/607a30d783dfa663caf39e06633721c8d4cfcd7e",
    "model_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/gpt2/model_config.json",
    "quantization_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization",
    "task_spec": "/home/remote/workspace/Qwen2-Accelerator/accagent/campaigns/20261020_gpt2_upstream_compare/task_spec.md",
    "template_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel",
    "tool_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools"
  },
  "stage": "input_preparation",
  "status": "ready",
  "summary": {
    "llm_mode": "llm",
    "llm_provider": "OpenAI",
    "model_type": "gpt2",
    "operator_count": 8,
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
    "board.aurora_c2c_channel0_base",
    "board.aurora_c2c_channel1_base",
    "board.card_name",
    "board.ddr4_0_9p_local_base",
    "board.example_design_ddr4_device_count",
    "board.fpga_part",
    "board.sample_project_dir",
    "board.sample_vivado_xpr",
    "input_materials.supported_formats",
    "memory_system.axi_addr_width_bits",
    "memory_system.axi_burst_length_width_bits",
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
    "notes.memory_system_ddr_channel_scope",
    "notes.scaffold_interface_not_board_accurate",
    "numeric_policy.change_management",
    "numeric_policy.current_run_artifact",
    "numeric_policy.default.acc_dtype",
    "numeric_policy.default.activation_dtype",
    "numeric_policy.default.rounding",
    "numeric_policy.default.saturation",
    "numeric_policy.default.scale_dtype",
    "numeric_policy.default.weight_dtype",
    "numeric_policy.fallback.acceptance",
    "numeric_policy.fallback.accumulation_dtype",
    "numeric_policy.fallback.scale_dtype",
    "numeric_policy.fallback.weight_activation_dtype",
    "numeric_policy.goal.end_to_end",
    "numeric_policy.integer_invariants.attention_operand_dtype",
    "numeric_policy.integer_invariants.no_floating_point_modules",
    "numeric_policy.integer_invariants.nonlinear_arithmetic_policy",
    "numeric_policy.integer_invariants.softmax_reciprocal_scaling",
    "numeric_policy.integer_invariants.softmax_requantization",
    "numeric_policy.integer_invariants.softmax_sum_width_bound",
    "numeric_policy.integer_invariants.softmax_unit_probability",
    "numeric_policy.integer_invariants.tail_tile_stride_formula",
    "numeric_policy.integer_invariants.tail_tile_stride_rule",
    "numeric_policy.integer_invariants.unknown_activation_policy",
    "numeric_policy.integer_invariants.zero_extend_uint8",
    "numeric_policy.packing.ddr_cache_density",
    "numeric_policy.packing.no_fp_storage",
    "numeric_policy.preserve.architecture_schedule",
    "numeric_policy.preserve.ddr_refill_width",
    "numeric_policy.preserve.prohibited_changes",
    "numeric_policy.quantization.activation_scale_granularity",
    "numeric_policy.quantization.output_rounding_saturation",
    "numeric_policy.quantization.scale_multiplier_format",
    "numeric_policy.quantization.scheme",
    "numeric_policy.quantization.weight_scale_granularity",
    "numeric_policy.quantization.wider_parameter_policy",
    "numeric_policy.scale_derivation",
    "numeric_policy.supersedes_previous_fp_policy",
    "numeric_policy.tolerance.quantitative_comparison",
    "numeric_policy.tolerance.resolved_values",
    "numeric_policy.tolerance.stage",
    "numeric_policy.tolerance.system",
    "numeric_policy.tolerance.vcs_warnings_policy",
    "numeric_policy.w4a8.arithmetic",
    "numeric_policy.w4a8.definition",
    "numeric_policy.w4a8.explicit_integer_contracts",
    "numeric_policy.w4a8.qk_pv_operand_dtype",
    "runtime_interface.board_run_command",
    "runtime_interface.c2h_device_template",
    "runtime_interface.control_protocol",
    "runtime_interface.ctrl_base",
    "runtime_interface.ddr_base",
    "runtime_interface.ddr_image_default",
    "runtime_interface.dma_from_device_tool",
    "runtime_interface.dma_to_device_tool",
    "runtime_interface.h2c_device_template",
    "runtime_interface.mimic_dir",
    "runtime_interface.output_abs",
    "runtime_interface.remote_host",
    "runtime_interface.smoke_pass_criteria",
    "runtime_interface.xdma_id_default",
    "tool.remote_server.host",
    "tool.remote_server.passwordless_login",
    "tool.remote_server.ssh_command",
    "tool.vcs.confirmed_compile_link_date",
    "tool.vcs.confirmed_version",
    "tool.vcs.executable",
    "tool.vcs.host",
    "tool.vcs.purpose",
    "tool.vcs.required_env",
    "tool.vcs.smoke_script",
    "tool.vcs.stage0_probe_required",
    "tool.vcs.synopsys_sim_setup_policy",
    "tool.vcs.verilator_fallback_note",
    "tool.vcs.version_probe_command",
    "tool.verilator.location",
    "tool.verilator.purpose",
    "tool.vivado.confirmed_version",
    "tool.vivado.executable",
    "tool.vivado.host",
    "tool.vivado.purpose",
    "tool.vivado.required_env",
    "tool.vivado.required_for_final_evidence",
    "tool.vivado.script",
    "tool.vivado.stage0_probe_required",
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
    "node.model_op.00_layer_norm_1",
    "node.model_op.01_self_attention",
    "node.model_op.02_residual_add_1",
    "node.model_op.03_layer_norm_2",
    "node.model_op.04_mlp_fc",
    "node.model_op.05_activation",
    "node.model_op.06_mlp_proj",
    "node.model_op.07_residual_add_2"
  ],
  "num_constraints": 16,
  "num_edges": 7,
  "num_nodes": 20,
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
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/constraint_extraction/team/team_aggregate.json",
  "approval_required_for": [
    "Any board DDR/AXI/memory/runtime constraint or deployment-evidence binding modification found ambiguous by static checks",
    "Any bounded graph addition or modification to architecture/design-space constraints found missing by static checks",
    "Any numeric-policy or parameter-binding constraint modification found missing by static checks",
    "minimal model/shape graph node and edge additions"
  ],
  "completed_subtasks": 4,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/constraint_extraction/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "artifact.candidate.candidate_design_graph_summary",
        "artifact.candidate.prepared_inputs_manifest",
        "artifact.input.material_index",
        "artifact.input.sample_project_index",
        "artifact.input.field_evidence",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "artifact.input.case_adapter",
        "artifact.input.human_agent_boundary",
        "constraint.source.materials",
        "constraint.source.evidence",
        "constraint.tool.profile",
        "constraint.tool.protocols",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.input_evidence_review.run_sacg_static_check",
      "on_failure": "Block stage handoff and emit a bounded repair/backtrack request listing the specific omitted or dangling material/evidence/tool input references; do not claim input coverage from the compact summary.",
      "produces": [
        "constraint_extraction.input_evidence_review_evidence.json"
      ],
      "rationale": "The compact candidate graph summary is not sufficient to prove that board materials, quantization materials, sample projects, extracted field evidence, tool profiles, tool availability, and real tool probe results are represented without dangling references. A static SACG check binds the graph to the prepared inputs before peer handoff.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_reference_check",
      "consumes": [
        "artifact.candidate.candidate_design_graph_summary",
        "artifact.candidate.prepared_inputs_manifest",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "artifact.input.field_evidence",
        "artifact.input.material_index",
        "artifact.input.sample_project_index",
        "constraint.source.materials",
        "constraint.source.evidence",
        "constraint.tool.profile",
        "constraint.tool.protocols",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.input_evidence_review.verify_input_reference_bindings",
      "on_failure": "Record unresolved references as current-stage handoff blockers and request targeted graph node/edge additions from the model graph engineer, template platform engineer, or constraint graph auditor; do not silently infer missing bindings.",
      "produces": [
        "constraint_extraction.input_evidence_review_reference_report.json"
      ],
      "rationale": "The role requires verifying that source-material, source-evidence, and tool-profile/protocol constraints are traceable to explicit graph nodes and that real tool availability/probe facts are not dangling. A reference check produces citable evidence for the downstream graph engineers and auditor.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_reference_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_binding_static_check",
        "model_config_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "constraint.model.decoder",
        "constraint.shape.model",
        "artifact.input.model_config"
      ],
      "id": "constraint_extraction.model_graph_engineer.static_model_shape_audit",
      "on_failure": "Do not pass this review or hand off as complete; record missing or ambiguous model and shape facts as bounded findings and route them to peer reviewers with proposed bounded actions.",
      "produces": [
        "constraint_extraction.model_shape_review_evidence.json",
        "constraint_extraction.model_shape_graph_findings.json"
      ],
      "rationale": "The candidate summary only provides aggregate sizes, so the full graph must be statically checked to determine whether model/shape facts are explicit nodes and edges before handoff.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_static_check",
        "template_binding_static_check",
        "model_config_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_binding_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "constraint_extraction.model_shape_review_evidence.json",
        "constraint_extraction.model_shape_graph_findings.json",
        "candidate_design_graph_summary"
      ],
      "id": "constraint_extraction.model_graph_engineer.propose_minimal_model_shape_edges",
      "on_failure": "If proposed node or edge names remain ambiguous, block handoff until model_config or case-adapter evidence supports exact terms; do not infer Qwen/OPT-specific core names.",
      "produces": [
        "constraint_extraction.model_shape_graph_findings.json"
      ],
      "rationale": "If the audit finds that required model/shape facts are absent or only isolated nodes, propose minimal graph node and edge additions while preserving the Transformer-block-only DUT scope.",
      "requires_approval": true,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "template_binding_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_coverage_check",
        "template_binding_static_check",
        "parameter_binding_static_check",
        "numeric_policy_check",
        "memory_runtime_plan_check",
        "addr_map_check",
        "tool_protocol_check",
        "required_real_tool_evidence_check",
        "implementation_package_static"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "prepared_inputs_manifest",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "artifact.input.numeric_policy",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols",
        "artifact.input.case_adapter",
        "constraint.template.library",
        "constraint.arch.design_space",
        "constraint.numeric.policy",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.tool.protocols",
        "constraint.deployment.board"
      ],
      "id": "constraint_extraction.template_platform_static_review",
      "on_failure": "Do not hand off to constraint_graph_auditor as passed. Record the exact missing or invalid node, edge, or unsupported backend/resource claim, then open a bounded graph-expansion/repair request. Approval is required for any addition or change to architecture/design-space, numeric-policy, or board memory/runtime constraints.",
      "produces": [
        "constraint_extraction.template_platform_review_evidence.json"
      ],
      "rationale": "The compact candidate graph summary alone is not sufficient evidence that template_library, design_space, numeric_policy, board DDR/AXI/memory/runtime, and tool_protocols are represented as graph constraints without unsupported resource-risk or backend claims. Run the existing static checkers against the full graph and produce the stage handoff evidence.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_static_check",
        "template_coverage_check",
        "template_binding_static_check",
        "parameter_binding_static_check",
        "numeric_policy_check",
        "memory_runtime_plan_check",
        "addr_map_check",
        "tool_protocol_check",
        "required_real_tool_evidence_check",
        "implementation_package_static"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "sacg_reference_check",
        "human_boundary_check",
        "repair_boundary_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "prepared_inputs_manifest",
        "validation_errors",
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.design_space",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.case_adapter",
        "artifact.input.human_agent_boundary"
      ],
      "id": "constraint_extraction.run_graph_reference_integrity_checks",
      "on_failure": "Do not promote candidate_design_graph_summary. Emit the failed invariant list and bounded repair actions scoped to broken graph references, missing cross-layer edges, or human-boundary violations, and route them to constraint_extraction.team_aggregate.",
      "produces": [
        "constraint_extraction.design_graph_audit_report.json"
      ],
      "rationale": "The compact candidate_design_graph_summary exposes only aggregate counts and an empty validation_errors list. Promotion as shared design state requires checker-bound evidence that every node and edge resolves to a supplied artifact or constraint and that no human-boundary violation is present.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_static_check",
        "sacg_reference_check",
        "human_boundary_check",
        "repair_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "repair_boundary_check",
        "human_boundary_check"
      ],
      "action_type": "team_aggregate",
      "consumes": [
        "constraint_extraction.design_graph_audit_report.json"
      ],
      "id": "constraint_extraction.promote_initial_design_graph_after_checks",
      "on_failure": "Keep next_stage handoff blocked and require a bounded remediation cycle before retrying aggregation.",
      "produces": [
        "constraint_extraction.team_aggregate.design_graph_promotion_decision"
      ],
      "rationale": "After the reference-integrity and human-boundary checks pass, the audit report can be aggregated into the team handoff state without making architecture, template, memory-layout, or numeric-policy changes.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "team_aggregate",
        "sacg_memory_update"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 7,
    "max_duration_sec": 105.60872719902545,
    "max_prompt_bytes": 39401,
    "result_count": 4,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 320.10441386303864,
    "total_prompt_bytes": 156919
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 4,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/constraint_extraction/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

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
