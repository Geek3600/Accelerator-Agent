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
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/input/team/team_aggregate.json",
    "approval_required_for": [
      "Adding or materially changing a trusted template, template parameter, or design-space target.",
      "Any action not explicitly allowed by the full artifact.input.human_agent_boundary.auto_allowed policy.",
      "Any action the full human boundary marks approval_required; forbidden actions remain blocked and are not authorized by this review.",
      "Any change or selection of numeric precision, quantization behavior, or numeric-policy assumptions.",
      "Any change or selection that establishes or changes the board binding, DDR/AXI address map, memory layout, transfer-unit semantics, or runtime ABI.",
      "Any change to numeric policy or tolerance values",
      "Any change to the selected model, decoder semantics, model dimensions, head mapping, sequence contract, or operator order.",
      "Any major template change",
      "Any proposed architecture or pipeline change",
      "Any proposed memory-layout change",
      "Architecture, pipeline, memory-layout, numeric-policy, or major-template changes.",
      "Changes to the exact user-supplied sample-project board wrapper or its immutable source identity."
    ],
    "completed_subtasks": 5,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/input/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "stream_plan_check",
          "deployment_board_check",
          "sacg_static_check"
        ],
        "action_type": "implementation_evidence_review",
        "consumes": [
          "artifact.input.target_board_profile",
          "artifact.input.field_evidence",
          "artifact.input.field_evidence_candidates",
          "artifact.input.material_index",
          "artifact.input.sample_project_index",
          "constraint.memory.board",
          "constraint.runtime.board",
          "constraint.deployment.board",
          "constraint.stream.order",
          "constraint.beat.pipeline"
        ],
        "id": "input_preparation.audit_board_memory_runtime_evidence",
        "on_failure": "Retain unknown or uninspectable facts as explicit evidence gaps and mark applicable checks not_run or failed according to their results. Do not guess board wiring or address values, upgrade declarations to verified evidence, or claim implementation/runtime/deployment readiness; route unresolved binding decisions for approval.",
        "produces": [
          "artifact.stage0.board_memory_runtime_review",
          "artifact.stage0.board_evidence_gap_matrix"
        ],
        "rationale": "Inspect the materialized board profile, field-evidence rows/candidates, material index, and sample-project index against the named memory, runtime, deployment, stream-order, and beat-pipeline constraints. Produce an evidence-strength review and gap matrix; this is an input audit, not a board or runtime execution.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "memory_runtime_plan_check",
          "addr_map_check",
          "stream_plan_check",
          "deployment_board_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "task_card_check",
          "model_config_check",
          "llm_semantic_extraction_check",
          "sacg_static_check"
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
        "id": "input_preparation.review_model_facts_and_gaps",
        "on_failure": "Record failed or not-run checks and source-bound ambiguities in the review and fact-and-gap matrix. Do not claim pass or promote unsupported facts; route any established model contradiction to the cross-layer SACG gate for a bounded resolution.",
        "produces": [
          "artifact.stage0.model_intake_review",
          "artifact.stage0.model_fact_and_gap_matrix"
        ],
        "rationale": "The available summary does not expose enough artifact content to establish decoder semantics, model shapes, or operator order. Review the full source artifacts with the registered checkers and bind each reported fact or gap to its source; do not infer model facts.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "task_card_check",
          "model_config_check",
          "llm_semantic_extraction",
          "sacg_validate"
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
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space"
        ],
        "id": "input_preparation.audit_numeric_template_bindings",
        "on_failure": "Record the failing or not_run checker, the affected artifact and constraint, and the unresolved binding in the review and gap matrix; hand off to input_preparation.cross_layer_sacg_gate. Do not promote an unverified binding or modify numeric policy, templates, or design-space targets.",
        "produces": [
          "artifact.stage0.numeric_template_review",
          "artifact.stage0.template_binding_gap_matrix"
        ],
        "rationale": "Evaluate only the supplied numeric policy, template library and metadata, and design space against their named SACG constraints. Record unavailable detail as unresolved or not_run; do not invent formats, template support, or parameter values.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "numeric_policy_check",
          "template_coverage_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "human_boundary_check",
          "boundary_contract_check",
          "sacg_static_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "artifact.input.field_evidence",
          "artifact.input.field_evidence_candidates",
          "artifact.input.case_adapter",
          "artifact.input.human_agent_boundary",
          "constraint.tool.protocols",
          "constraint.human.boundary"
        ],
        "id": "input_preparation.audit_tool_evidence_and_human_boundary",
        "on_failure": "Record each failing or unresolved contract as a bounded capability, evidence, or approval gap in the produced artifacts; mark unsupported evidence not_run/unverified. Do not claim pass, execute real tools, assume availability, change approval boundaries, or promote downstream work on unresolved required checks. Do not create a new compile-only tool solely because an existing verification role includes functional_sim in its name.",
        "produces": [
          "artifact.stage0.tool_evidence_boundary_review",
          "artifact.stage0.capability_and_approval_gap_matrix"
        ],
        "rationale": "The required artifact classes are present in the state, but their detailed contracts are not visible in the supplied summary. Checker-grounded inspection is needed to establish usable tool/evidence contracts and explicit autonomous-change limits without executing tools or claiming their results.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "tool_protocol_check",
          "required_real_tool_evidence_check",
          "human_boundary_check",
          "boundary_contract_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "sacg_static_check",
          "template_binding_static_check",
          "verification_plan_static_check",
          "repair_boundary_check",
          "sacg_reference_check",
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "memory_runtime_plan_check",
          "tool_protocol_check",
          "human_boundary_check"
        ],
        "action_type": "sacg_constraint_review",
        "consumes": [
          "artifact.input.task_card",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.target_board_profile",
          "artifact.input.sample_project_index",
          "artifact.input.tool_profile",
          "artifact.input.tool_availability",
          "artifact.input.tool_protocols",
          "artifact.input.human_agent_boundary",
          "artifact.stage0.model_intake_review",
          "artifact.stage0.numeric_template_review",
          "artifact.stage0.board_memory_runtime_review",
          "artifact.stage0.tool_evidence_boundary_review",
          "artifact.stage0.model_fact_and_gap_matrix",
          "artifact.stage0.template_binding_gap_matrix",
          "artifact.stage0.board_evidence_gap_matrix",
          "artifact.stage0.capability_and_approval_gap_matrix"
        ],
        "id": "input_preparation.run_cross_layer_checker_gate",
        "on_failure": "Keep SACG extraction blocked for each failed or unassessed constraint; record checker evidence and not_run status accurately, route the bounded correction to its responsible input owner, and rerun affected registered checkers. Do not guess missing facts, waive checkers, alter golden outputs or numeric policy, or claim hardware pass.",
        "produces": [
          "artifact.stage0.cross_layer_input_consistency_review",
          "artifact.stage0.sacg_extraction_readiness",
          "artifact.stage0.cross_layer_checker_results"
        ],
        "rationale": "Consolidate only checker-supported specialist findings and verify cross-layer bindings before SACG extraction. The visible compact summary is insufficient to establish readiness; registered checkers can validate the detailed source inputs and review artifacts without claiming implementation or deployment results.",
        "requires_approval": false,
        "stage": "input_preparation",
        "tool_roles": [
          "sacg_validate",
          "task_card_check",
          "model_config_check",
          "numeric_policy_check",
          "template_coverage_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "memory_runtime_plan_check",
          "verification_plan_static_check",
          "tool_protocol_check",
          "human_boundary_check",
          "repair_boundary_check",
          "sacg_reference_check",
          "sacg_static_check"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 5,
      "max_duration_sec": 38.05833217903273,
      "max_prompt_bytes": 40046,
      "result_count": 5,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 151.51239773607813,
      "total_prompt_bytes": 196655
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 5,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/input/team/subtask_plan.json",
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
  "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020",
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
    "model_dir": "/home/remote/.cache/huggingface/hub/models--google--gemma-3-1b-it/snapshots/dcc83ea841ab6100d6b47a070329e1ba4cf78752",
    "model_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/model_configs/gemma3_1b_it/model_config.json",
    "quantization_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization",
    "task_spec": "/home/remote/workspace/Qwen2-Accelerator/accagent/campaigns/20261020_gemma_gpt61/task_spec.md",
    "template_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel",
    "tool_materials_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/tools"
  },
  "stage": "input_preparation",
  "status": "ready",
  "summary": {
    "llm_mode": "llm",
    "llm_provider": "OpenAI",
    "model_type": "gemma3_text",
    "operator_count": 11,
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
    "board.card_topology.example_design",
    "board.example_design.documented_api_functions",
    "board.example_design.driver_basis",
    "board.example_design.interconnect",
    "board.example_design.pcie_address_map",
    "board.example_design.pcie_address_translation",
    "board.fpga_part",
    "board.sample_project_access_scope",
    "board.sample_project_directory",
    "board.sample_project_part_property",
    "board.sample_project_server",
    "board.sample_project_vivado_project",
    "board.sample_project_write_restriction",
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
    "memory_system.ddr_interface_type",
    "memory_system.ddr_word_width_bits",
    "memory_system.real_board_reference_rtl",
    "memory_system.simulation_scaffold_interface",
    "numeric_policy.accumulator_dtype",
    "numeric_policy.activation_dtype",
    "numeric_policy.activation_kind_handling",
    "numeric_policy.architecture_preservation",
    "numeric_policy.arithmetic_implementation",
    "numeric_policy.attention_accumulator_and_dsp_accounting",
    "numeric_policy.attention_qk_pv_operand_dtype",
    "numeric_policy.attention_softmax_to_pv",
    "numeric_policy.bias_and_normalization_parameter_formats",
    "numeric_policy.comparison_stage",
    "numeric_policy.compile_only_fixture",
    "numeric_policy.ddr_refill_and_overlap",
    "numeric_policy.disallowed_weight_storage",
    "numeric_policy.end_to_end_goal",
    "numeric_policy.fallback_when_no_policy",
    "numeric_policy.initial_activation_scale_granularity",
    "numeric_policy.initial_quantization_scheme",
    "numeric_policy.initial_weight_scale_granularity",
    "numeric_policy.integer_elaboration_floating_point_modules",
    "numeric_policy.integer_nonlinear_implementation",
    "numeric_policy.local_interface_changes",
    "numeric_policy.operators_requiring_explicit_integer_contracts",
    "numeric_policy.packed_weight_storage",
    "numeric_policy.policy_change_checkpointing",
    "numeric_policy.quantitative_comparison_values",
    "numeric_policy.requantized_output",
    "numeric_policy.rounding",
    "numeric_policy.saturation",
    "numeric_policy.scale_dtype",
    "numeric_policy.scale_multiplier_representation",
    "numeric_policy.scale_shifts",
    "numeric_policy.softmax_probability_scale",
    "numeric_policy.softmax_probability_scale_requirements",
    "numeric_policy.softmax_reciprocal_scaling",
    "numeric_policy.softmax_single_element_row",
    "numeric_policy.softmax_sum_width",
    "numeric_policy.system_acceptance",
    "numeric_policy.tail_tile_address_validation",
    "numeric_policy.tail_tile_addressing",
    "numeric_policy.tolerance_resolution_timing",
    "numeric_policy.uint8_coefficient_multiply",
    "numeric_policy.vcs_compile_elaboration_link_gate",
    "numeric_policy.w4a8_operand_semantics",
    "numeric_policy.weight_and_calibration_metadata_source",
    "numeric_policy.weight_dtype",
    "runtime_interface.board_run_command",
    "runtime_interface.board_runtime_host",
    "runtime_interface.c2h_device_template",
    "runtime_interface.control_protocol",
    "runtime_interface.ctrl_base",
    "runtime_interface.ddr_base",
    "runtime_interface.ddr_image_default",
    "runtime_interface.ddr_image_load_behavior",
    "runtime_interface.dma_from_device_executable",
    "runtime_interface.dma_to_device_executable",
    "runtime_interface.h2c_device_template",
    "runtime_interface.mimic_dir",
    "runtime_interface.output_abs",
    "runtime_interface.remote_tool_server",
    "runtime_interface.smoke_pass_criteria",
    "runtime_interface.smoke_sequence",
    "runtime_interface.xdma_id_default",
    "tool.remote_server.passwordless_login_configured",
    "tool.remote_server.ssh_command",
    "tool.vcs.documented_older_version_issue",
    "tool.vcs.documented_prior_test",
    "tool.vcs.environment.HOME",
    "tool.vcs.environment.REMOTE_HOST",
    "tool.vcs.environment.REMOTE_VCS_HOME",
    "tool.vcs.environment.VCS_TARGET_ARCH",
    "tool.vcs.environment.default_HOME_library_restriction",
    "tool.vcs.environment.synopsys_sim_setup_binding",
    "tool.vcs.executable",
    "tool.vcs.existing_framework_script",
    "tool.vcs.functional_verification_role",
    "tool.vcs.host",
    "tool.vcs.probe_requirement",
    "tool.vcs.scope",
    "tool.vcs.version_probe_command",
    "tool.verilator.location",
    "tool.verilator.scope",
    "tool.vivado.documented_version",
    "tool.vivado.environment.REMOTE_HOST",
    "tool.vivado.environment.VIVADO_BIN",
    "tool.vivado.executable",
    "tool.vivado.existing_framework_script",
    "tool.vivado.final_evidence_role",
    "tool.vivado.host",
    "tool.vivado.probe_requirement",
    "tool.vivado.scope",
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
    "node.model_op.00_rms_norm_input",
    "node.model_op.01_self_attention",
    "node.model_op.02_rms_norm_post_attention",
    "node.model_op.03_residual_add_1",
    "node.model_op.04_rms_norm_pre_ffn",
    "node.model_op.05_mlp_gate_proj",
    "node.model_op.06_mlp_up_proj",
    "node.model_op.07_activation_mul",
    "node.model_op.08_mlp_down_proj",
    "node.model_op.09_rms_norm_post_ffn",
    "node.model_op.10_residual_add_2"
  ],
  "num_constraints": 16,
  "num_edges": 10,
  "num_nodes": 23,
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
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/constraint_extraction/team/team_aggregate.json",
  "approval_required_for": [
    "Ambiguous case-adapter or board-target choices that cannot be resolved from cited user-supplied materials and real tool evidence.",
    "Any action that would alter the checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, or exact board-wrapper source hashes.",
    "Any change to accelerator architecture or stream protocol assumptions",
    "Any change to architecture design-space limits.",
    "Any change to numeric formats, numeric policy, or tolerances.",
    "Any change to the board DDR or memory address layout",
    "Any major template selection or template parameter change that alters the architecture.",
    "Any proposed change to accelerator architecture, pipeline structure, memory layout, numeric policy, or major template selection requires the applicable human approval before adoption.",
    "Any proposed change to model architecture, operator or residual order, attention/head mapping, or model-shape interpretation; such a change must be source-supported and approved before adoption.",
    "Any unresolved human-boundary approval specified by the detailed boundary artifact must be recorded and obtained before adopting the affected delta.",
    "Architecture, pipeline, memory-layout, numeric-policy, or major template changes."
  ],
  "completed_subtasks": 6,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/constraint_extraction/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "stream_plan_check",
        "memory_runtime_plan_check",
        "addr_map_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.target_board_profile",
        "artifact.input.field_evidence",
        "artifact.input.sample_project_index",
        "artifact.input.task_card",
        "constraint.source.evidence",
        "constraint.deployment.board",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.audit_data_memory_runtime_evidence",
      "on_failure": "Record each failed or unavailable check and the precise unsupported or ambiguous fact in the review; mark it not_run or unsupported where appropriate. Propose only deltas supported by cited supplied evidence, and keep downstream interface/runtime readiness unclaimed. Escalate any proposed architecture, stream-protocol, or memory-layout change for approval rather than silently changing it.",
      "produces": [
        "constraint_extraction/reviews/data_memory_runtime_review.json",
        "constraint_extraction/proposed_deltas/data_memory_runtime.json"
      ],
      "rationale": "Inspect detailed graph fields and source artifacts, then use the registered checkers to determine whether stream order, transfer/liveness, board memory layout, and runtime facts are represented with evidence and consistent across layers. The summary alone is insufficient to establish these details or interface readiness.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "stream_plan_check",
        "memory_runtime_plan_check",
        "addr_map_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "tool_protocol_check",
        "required_real_tool_evidence_check",
        "implementation_package_static",
        "deployment_board_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.material_index",
        "artifact.input.sample_project_index",
        "artifact.input.field_evidence",
        "artifact.input.target_board_profile",
        "artifact.input.tool_profile",
        "artifact.input.tool_availability",
        "artifact.input.tool_protocols"
      ],
      "id": "constraint_extraction.audit_implementation_deployment_evidence",
      "on_failure": "Record the specific failed check and its cited artifacts in the review and propose a bounded graph correction. Treat omitted detail as unresolved rather than absent; do not claim tool execution or implementation/deployment success without validated current-run evidence, and do not alter architecture or deployment choices in this review.",
      "produces": [
        "constraint_extraction/reviews/implementation_deployment_review.json",
        "constraint_extraction/proposed_deltas/implementation_deployment.json"
      ],
      "rationale": "The available summary establishes artifact-class presence and candidate-graph structure, but not detailed source or tool facts. Check the detailed supplied records and graph before accepting implementation, backend, or deployment claims; distinguish checker-grounded facts from plans and not_run items.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "tool_protocol_check",
        "required_real_tool_evidence_check",
        "implementation_package_static",
        "deployment_board_check",
        "sacg_static_check",
        "sacg_validate"
      ]
    },
    {
      "acceptance_checkers": [
        "model_config_check",
        "sacg_static_check",
        "template_binding_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_stage_artifact.candidate_design_graph_summary",
        "artifact.input.model_config",
        "artifact.input.task_card",
        "artifact.input.case_adapter"
      ],
      "id": "constraint_extraction.audit_model_shape_provenance",
      "on_failure": "Record the exact unavailable, ambiguous, or contradictory source-to-graph facts in the review; do not claim semantic verification or invent a graph correction. Hand unresolved questions to constraint_extraction.constraint_graph_auditor.",
      "produces": [
        "constraint_extraction/reviews/model_shape_review.json",
        "constraint_extraction/proposed_deltas/model_shape.json"
      ],
      "rationale": "The compact graph summary cannot substantiate model semantics or shape provenance. Review the detailed candidate graph against the current model inputs, then run the registered model and SACG checks without inferring facts from artifact names or aggregate counts.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "model_config_check",
        "sacg_static_check",
        "template_binding_static_check"
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
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "constraint.numeric.policy",
        "constraint.template.library",
        "constraint.arch.design_space",
        "constraint.cross_layer.input_consistency"
      ],
      "id": "constraint_extraction.audit_numeric_template_bindings",
      "on_failure": "Record the failing checker and the exact unsupported, unbound, conflicting, or untraceable fact. Do not infer missing detail from this compact summary, invent a replacement binding, alter numeric policy, or claim closure. Produce only evidence-backed proposed graph deltas; request approval for numeric-policy, architecture-limit, or major-template changes.",
      "produces": [
        "constraint_extraction/reviews/numeric_template_review.json",
        "constraint_extraction/proposed_deltas/numeric_template.json",
        "constraint_extraction/checker_results/numeric_template_static_checks.json"
      ],
      "rationale": "The visible summary establishes structural presence but does not expose the detailed facts or checker results needed to verify numeric-policy consistency, trusted-template coverage, parameter bindings, design-space limits, or current-input traceability. Run the registered static checks and report supported bindings separately from unresolved choices.",
      "requires_approval": false,
      "stage": "constraint_extraction",
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
        "verification_plan_static_check",
        "verification_artifact_contract_check",
        "human_boundary_check",
        "repair_boundary_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.case_adapter",
        "artifact.input.tool_protocols",
        "artifact.input.tool_availability",
        "artifact.input.human_agent_boundary"
      ],
      "id": "constraint_extraction.verify_boundary_checker_review",
      "on_failure": "Record the failing or not_run checker and its violated or unverified constraint; return the bounded finding to constraint_graph_auditor. Do not describe omitted details as passes or promote the graph on the empty validation_errors list alone.",
      "produces": [
        "constraint_extraction/reviews/verification_boundary_review.json",
        "checker result and evidence bindings for verification-plan, artifact-contract, human-boundary, repair-boundary, and SACG checks"
      ],
      "rationale": "Use the registered static checkers on the detailed graph and named inputs to establish whether verification planning, evidence contracts, human approvals, and bounded repairs are explicitly and consistently represented. The compact summary is insufficient to infer edge-level coverage.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_validate",
        "verification_plan_static_check",
        "verification_artifact_contract_check",
        "human_boundary_check",
        "repair_boundary_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "verification_plan_static_check",
        "verification_artifact_contract_check",
        "human_boundary_check",
        "repair_boundary_check",
        "sacg_static_check"
      ],
      "action_type": "sacg_graph_delta_proposal",
      "consumes": [
        "candidate_design_graph_summary",
        "artifact.input.case_adapter",
        "artifact.input.tool_protocols",
        "artifact.input.tool_availability",
        "artifact.input.human_agent_boundary",
        "constraint_extraction/reviews/verification_boundary_review.json"
      ],
      "id": "constraint_extraction.propose_verification_plan_graph_delta",
      "on_failure": "Keep the graph delta unpromoted and report the precise checker failure to constraint_graph_auditor. Do not guess missing case-adapter details or change architecture, numeric policy, verification inputs, or approval boundaries.",
      "produces": [
        "constraint_extraction/proposed_deltas/verification_boundary.json"
      ],
      "rationale": "The visible constraint inventory lacks a dedicated verification-plan constraint. Propose one, with evidence and checker obligations, unless the detailed checker review establishes an equivalent explicit mapping. The proposal must preserve the compile-only VCS acceptance policy and explicit human and repair boundaries.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "llm_semantic_extraction",
        "sacg_validate"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "sacg_reference_check",
        "template_binding_static_check",
        "repair_boundary_check",
        "human_boundary_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "candidate_design_graph_summary",
        "prepared_inputs_manifest",
        "validation_errors",
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
      "id": "constraint_extraction.audit_candidate_graph",
      "on_failure": "Record each failed or not_run checker against its relevant constraint and source artifact. Keep the audit incomplete, do not promote the graph, and route any required repair through the responsible specialist without changing golden outputs or relaxing constraints.",
      "produces": [
        "constraint_extraction/reviews/candidate_graph_checker_results.json",
        "constraint_extraction/reviews/consolidated_graph_audit.json"
      ],
      "rationale": "The supplied summaries report no validation errors but do not establish reference integrity, template binding, or boundary compliance. Run the registered checks on the current graph and source inputs to produce checker-grounded evidence.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "sacg_static_check",
        "sacg_reference_check",
        "template_binding_static_check",
        "repair_boundary_check",
        "human_boundary_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_reference_check",
        "template_binding_static_check",
        "repair_boundary_check",
        "human_boundary_check"
      ],
      "action_type": "cross_layer_evidence_reconciliation",
      "consumes": [
        "prepared_inputs_manifest",
        "constraint_extraction/reviews/candidate_graph_checker_results.json",
        "model/shape review and deltas",
        "numeric/template review and deltas",
        "data/memory/runtime review and deltas",
        "implementation/deployment review and deltas",
        "verification/boundary review and deltas"
      ],
      "id": "constraint_extraction.reconcile_specialist_deltas",
      "on_failure": "If specialist artifacts, required checker evidence, or detailed completion/non-fallback status cannot be verified, record the affected review as unresolved or not_run and withhold downstream handoff. Do not convert missing detail into a pass or silently rewrite specialist findings.",
      "produces": [
        "constraint_extraction/reviews/consolidated_graph_audit.json",
        "constraint_extraction/proposed_deltas/consolidated_graph_deltas.json"
      ],
      "rationale": "The requested specialist findings and deltas are not visible in the supplied summary. Retrieve the detailed run artifacts, reconcile each proposal against source provenance and checker results, and preserve unresolved boundaries rather than inferring approval.",
      "requires_approval": false,
      "stage": "constraint_extraction",
      "tool_roles": [
        "team_aggregate",
        "sacg_reference_check",
        "template_binding_static_check",
        "repair_boundary_check",
        "human_boundary_check"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 8,
    "max_duration_sec": 677.3505573319853,
    "max_prompt_bytes": 40313,
    "result_count": 6,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 832.4614266949939,
    "total_prompt_bytes": 239062
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 6,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/constraint_extraction/team/subtask_plan.json",
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
  "model": "gpt-6.1-sol",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
  "requested_model_override": "",
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
