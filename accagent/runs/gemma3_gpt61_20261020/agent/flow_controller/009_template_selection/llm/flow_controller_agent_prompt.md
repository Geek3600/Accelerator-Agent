<agent>
flow_controller_agent
</agent>

<task>
Review SACG memory and the latest stage result, then decide whether the autonomous design team should proceed, retry the current stage, backtrack to an earlier stage, run bounded repair, or stop to avoid artifact contamination. Framework, hash, manifest, provenance, evidence-binding, or stage-routing failures must never rewind hardware design stages; retry the failed current stage. Backtracking is allowed only when the action names a hardware-design failure category and cites failed gates, measurements, a critical path, or tool evidence. For backend timing, use the run-local timing repair executed by Stage 7; when its status is compiled_pending_vcs, request current-source compile-only verification and return to Stage 7, never code_generation or parameter_binding.
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
34. Use exact internal stage names for backtrack targets. Public Stage 5 contains both code_generation and verification_artifacts: verification-plan, artifact-contract, or action-audit repairs target verification_artifacts; hardware regeneration targets code_generation. Do not use the ambiguous label stage5 for those actions.
35. For Stage-7 loader-to-DUT mapping failures, case_compute_slot_adapter_generate is an existing bounded repair path. Prefer that real tool and its current hash-verified board-source context over a separate planned_tool read-only audit; a missing dedicated audit role alone is not a missing system capability. When validated_stage6_selection passes, preserve that exact target without asking for approval merely to restate it. Keep approval for changing the target or semantic contracts.
36. For a Stage-7 read-only trust, provenance, or identity audit, compose the registered checks such as stage_artifact_trust_barrier_check, verification_action_audit_check, artifact_hash_check, sacg_memory_check, stage_backtrack_request_check, and stage_retry_request_check. Do not request a new planned_tool or planned_checker only because no single registered role wraps the whole audit; keep unresolved barriers active until the existing checks pass, and name a capability gap only for a specific required check that none of the registered capabilities can perform.
37. For a Stage-6 trace replay, include targeted_replay_plan with the current stage_id and rerun_env.SPATIALACC_TARGET_BOUNDARY set to a specific boundary from the supplied failure-localization evidence. Use targeted_replay_history when supplied: a new rationale, probe label, or unused plan field is not a new observation unless the effective trace environment or semantic input fingerprint changes. Choose a boundary not already observed for the same stage and semantic inputs; state what root-cause alternatives the new signal distinguishes, or return a bounded replan instead of authorizing another VCS replay.
</rules>

<current_stage>
template_selection
</current_stage>

<stage_passed>
false
</stage_passed>

<attempt_count>
2
</attempt_count>

<available_stages>
[
  "input_preparation",
  "constraint_extraction",
  "template_selection",
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
  "checker_results": [
    {
      "checker": "operator_coverage_check",
      "errors": [],
      "evidence": {
        "missing_ops": [],
        "required_ops": 11
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_parameter_binding_check",
      "errors": [
        "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024",
        "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "evidence": {
        "binding_count": 14
      },
      "status": "fail",
      "warnings": []
    },
    {
      "checker": "template_source_and_interface_check",
      "errors": [],
      "evidence": {
        "checked_templates": 14
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "mandatory_fpga_ip_binding_check",
      "errors": [],
      "evidence": {
        "checked_source_hashes": {
          "Activation.scala": "c77e42c70db8b3fb74c9563970edc90cd3a79a144d959eaa8a253008ae5f24ce",
          "Attention.scala": "c3e8bfc0ab0c1c8d4421bb0fe03272f4ea420df3f0e710b6a3c4154843593a7e",
          "Common.scala": "f358026cf47764dcc732f6c8550b17ab759d089bc9ad6cccbca814143e899b73",
          "DecoderBlock.scala": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
          "Elementwise.scala": "53f25bee2ff7dc030db606d1842a45ddd856b475c388ee82d6260779d4ec8870",
          "FFN.scala": "1896b7ea12ac548124a1a25266baa7d9ea087af21ee60d57633f6843db91a58c",
          "KVCache.scala": "727e172cfdfe380e30b9976ef77c443086ef088427eef31a84aa3a9e0da20069",
          "Linear.scala": "cf74d94c7857b2bbb55b0447bffad0c261824fdbd534e118675f90b8b0430fe8",
          "Mask.scala": "bfb70e48641d60c25100b8240d5fef461aa954847c5fe5777b7fbb5445fc0e0a",
          "Norm.scala": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
          "PhysicalResources.scala": "8479cbbaf57cbd85912037dc807694623b1b9a754825a47d084b1b5be59dcdd4",
          "QKVProjection.scala": "3ca84ba8f25c4f151d9bba237fbf61f1c2ca64b572dc02a1e570e8649a546bc1",
          "Residual.scala": "8bef8dac50264c2278438a18e5be48328ed1fd1bfb3f9bbee3c522f11258aca3",
          "RoPE.scala": "ad42db5781d4f0906d4f28864570fc72f3763f94926144dc5a27275f129209f8",
          "Softmax.scala": "4f68287b82eab429fa5da62a9d8f3fd1a537f00ef42e364f411e7dd3537e94f2",
          "WeightTileCache.scala": "ba0f85a03ce3ff2fd56fc28f07ed40ce6ce1327508222fe67b64d32108156873"
        },
        "checked_sources": [
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
        ],
        "errors": [],
        "physical_resource_source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/PhysicalResources.scala",
        "required_bindings": {
          "activations": "XPM BRAM",
          "arithmetic": "signed integer DSP MAC/reduction inference",
          "fifo": "XPM BRAM",
          "large_cache": "XPM URAM",
          "weights": "XPM URAM"
        },
        "schema_version": "spatialaccagent.fpga_ip_contract.v1",
        "simulation": {
          "behavioral_fallback_allowed": false,
          "compute_models": "signed integer DSP arithmetic inferred from current Chisel sources; no floating-point IP",
          "memory_models": "Xilinx XPM simulation library",
          "required_libraries": [
            "unisims_ver",
            "xpm"
          ],
          "required_sources": [
            "glbl.v",
            "XPM simulation sources"
          ],
          "same_interface_and_cycle_latency_as_implementation": true,
          "same_module_names_as_implementation": true
        },
        "status": "pass",
        "violations": []
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "attention_semantic_expansion_check",
      "errors": [],
      "evidence": {
        "components": [
          {
            "component": "qkv_projection",
            "evidence_pattern": "Module(new QKVProjection",
            "evidence_type": "hash_bound_template_source",
            "required": true,
            "source": "DecoderBlock.scala",
            "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
            "status": "covered"
          },
          {
            "component": "rope",
            "evidence_pattern": "Module(new RoPE",
            "evidence_type": "hash_bound_template_source",
            "required": true,
            "source": "DecoderBlock.scala",
            "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
            "status": "covered"
          },
          {
            "component": "gqa_head_mapping",
            "evidence_pattern": "kvGroupSize",
            "evidence_type": "hash_bound_template_source",
            "gqa_group_size": 4,
            "params": {
              "num_kv_heads": 1,
              "num_q_heads": 4
            },
            "required": true,
            "source": "QKVProjection.scala",
            "source_sha256": "3ca84ba8f25c4f151d9bba237fbf61f1c2ca64b572dc02a1e570e8649a546bc1",
            "status": "covered"
          },
          {
            "component": "softmax",
            "evidence_pattern": "template_id=softmax",
            "evidence_type": "hash_bound_template_source",
            "required": true,
            "source": "Softmax.scala",
            "source_sha256": "4f68287b82eab429fa5da62a9d8f3fd1a537f00ef42e364f411e7dd3537e94f2",
            "status": "covered"
          },
          {
            "component": "output_projection",
            "evidence_pattern": "val outputProjection = Module(new Linear(p.outLinear))",
            "evidence_type": "hash_bound_template_source",
            "required": true,
            "source": "Attention.scala",
            "source_sha256": "c3e8bfc0ab0c1c8d4421bb0fe03272f4ea420df3f0e710b6a3c4154843593a7e",
            "status": "covered"
          },
          {
            "component": "kv_cache",
            "evidence_pattern": "Module(new KVCache",
            "evidence_type": "hash_bound_template_source",
            "required": false,
            "source": "DecoderBlock.scala",
            "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
            "status": "not_required"
          },
          {
            "component": "causal_mask",
            "evidence_pattern": "template_id=mask",
            "evidence_type": "hash_bound_template_source",
            "required": true,
            "source": "Mask.scala",
            "source_sha256": "bfb70e48641d60c25100b8240d5fef461aa954847c5fe5777b7fbb5445fc0e0a",
            "status": "covered"
          }
        ],
        "required": true
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "cross_layer_trace_check",
      "errors": [],
      "evidence": {
        "constraints": [
          {
            "constraint": "constraint.numeric.policy",
            "fact_keys": [
              "_llm_provenance",
              "_numeric_comparison_resolution",
              "default_rules",
              "notes",
              "policy_id",
              "schema_version",
              "tolerance"
            ],
            "present": true
          },
          {
            "constraint": "constraint.memory.board",
            "fact_keys": [
              "memory_system"
            ],
            "present": true
          },
          {
            "constraint": "constraint.runtime.board",
            "fact_keys": [
              "board_run_command",
              "c2h_device_template",
              "control_base",
              "control_protocol",
              "ctrl_base",
              "ddr_base",
              "ddr_image_default",
              "device_id",
              "h2c_device_template",
              "image_path",
              "mimic_dir",
              "output_abs",
              "output_address",
              "runtime_directory",
              "xdma_id_default"
            ],
            "present": true
          },
          {
            "constraint": "constraint.deployment.board",
            "fact_keys": [
              "board",
              "board_pass_criteria",
              "shell"
            ],
            "present": true
          },
          {
            "constraint": "constraint.cross_layer.input_consistency",
            "fact_keys": [
              "acceptance_boundary",
              "board",
              "conflict_rules",
              "evidence_by_field",
              "evidence_fields",
              "field_resolution",
              "materials",
              "model",
              "numeric_policy",
              "tools"
            ],
            "present": true
          }
        ],
        "status": "pass"
      },
      "status": "pass",
      "warnings": []
    }
  ],
  "design_team": {
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/team/team_aggregate.json",
    "approval_required_for": [
      "Any change to model head counts, head dimension, attention architecture, or trusted template semantics proposed as a resolution to the 1152 versus 4\u00d7256 contradiction.",
      "Any change to model hidden_size, num_q_heads, head_dim, or attention/GQA architecture that is not a source-backed correction of the supplied facts",
      "Any change to model or attention geometry, architecture, template internals, or selection of a materially different template/adapter needed to resolve the 1152-versus-1024 binding; obtain authoritative evidence and designated approval before applying such a change.",
      "Any change to the supplied numeric policy",
      "Any proposed change to authoritative model shape facts or attention head geometry requires the responsible model-fact owner to provide the trusted correction; this specialist is not authorized to change those facts.",
      "Any template substitution or major template/architecture change",
      "Any template-internal or major architecture change intended to accommodate a different head geometry requires the applicable approval before implementation."
    ],
    "completed_subtasks": 4,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/team/event_log.jsonl",
    "executable_actions": [
      {
        "acceptance_checkers": [
          "model_config_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "template_coverage_check",
          "sacg_static_check"
        ],
        "action_type": "evidence_and_repair_review",
        "consumes": [
          "artifact.stage2.template_selection.attention_semantics",
          "artifact.stage2.template_selection.parameter_bindings",
          "artifact.stage2.template_selection.checker_results",
          "artifact.input.model_config",
          "artifact.input.template_metadata",
          "constraint.model.decoder",
          "constraint.shape.model",
          "constraint.template.library",
          "constraint.cross_layer.input_consistency",
          "sacg_memory_truth.active_contamination_barriers"
        ],
        "id": "review_attention_semantics_and_head_mapping",
        "on_failure": "Record checker failures and the unresolved 1152 != 4\u00d7256 contradiction in the review artifacts; keep self_attention and gemma3_text_block unapproved and preserve the active contamination barrier. Do not guess replacement dimensions or promote the candidate.",
        "produces": [
          "review/template_selection/attention_semantic_binding_review.json",
          "review/template_selection/head_mapping_consistency.json"
        ],
        "rationale": "Create the specialist handoff findings from the supplied hash-bound attention evidence and parameter bindings, and validate the current contradiction against the named model, shape, template, and SACG constraints. This action reviews evidence only; it does not alter dimensions or architecture.",
        "requires_approval": false,
        "stage": "template_selection",
        "tool_roles": [
          "model_config_check",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "template_coverage_check",
          "sacg_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "model_config_check",
          "sacg_static_check",
          "stage_artifact_trust_barrier_check"
        ],
        "action_type": "evidence_review",
        "consumes": [
          "artifact.input.model_config",
          "artifact.input.field_evidence",
          "artifact.stage2.template_selection (planning/debug evidence only)",
          "state_summary.sacg_memory_truth"
        ],
        "id": "template_selection.trace_shape_fact_provenance",
        "on_failure": "Record any unavailable or conflicting source fields explicitly; do not infer replacement dimensions, alter model facts, assert a legal binding, or treat the barriered candidate as validated.",
        "produces": [
          "review/template_selection/shape_fact_provenance.json"
        ],
        "rationale": "Establish field-level provenance for the four shape facts from the trusted model/configuration inputs. The visible candidate binding citations are not sufficient to independently verify upstream source values, and the active barrier makes the candidate artifact debug-only.",
        "requires_approval": false,
        "stage": "template_selection",
        "tool_roles": [
          "model_config_check",
          "sacg_static_check",
          "stage_artifact_trust_barrier_check"
        ]
      },
      {
        "acceptance_checkers": [
          "model_config_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check",
          "sacg_static_check",
          "stage_artifact_trust_barrier_check"
        ],
        "action_type": "evidence_and_repair_review",
        "consumes": [
          "artifact.input.model_config",
          "artifact.input.template_metadata",
          "artifact.input.template_library",
          "artifact.stage2.template_selection (planning/debug evidence only)",
          "review/template_selection/shape_fact_provenance.json",
          "state_summary.sacg_memory_truth"
        ],
        "id": "template_selection.rerun_decoder_coverage_and_binding_review",
        "on_failure": "Report coverage separately from binding legality. If the 1152-versus-1024 mismatch remains or the trusted facts cannot be established, keep template selection incomplete and request authoritative model-fact reconciliation; do not change facts or claim a legal binding.",
        "produces": [
          "review/template_selection/model_shape_coverage_review.json"
        ],
        "rationale": "Preserve the reported decoder order and template coverage while independently checking coverage and parameter legality against authoritative shape facts. This action reviews evidence only and does not modify templates or model configuration.",
        "requires_approval": false,
        "stage": "template_selection",
        "tool_roles": [
          "model_config_check",
          "template_coverage_check",
          "parameter_binding_static_check",
          "template_binding_static_check",
          "sacg_static_check",
          "stage_artifact_trust_barrier_check"
        ]
      },
      {
        "acceptance_checkers": [
          "template_binding_static_check",
          "parameter_binding_static_check",
          "numeric_policy_check",
          "sacg_memory_check",
          "stage_artifact_trust_barrier_check"
        ],
        "action_type": "evidence_and_repair_review",
        "consumes": [
          "artifact.stage2.template_selection",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space"
        ],
        "id": "numeric_template.persist_strict_binding_audit",
        "on_failure": "Keep the candidate blocked; record any checker as failed or not_run, retain the unsupported disposition, and do not promote or treat the candidate as a validated design input.",
        "produces": [
          "review/template_selection/strict_binding_audit.json",
          "review/template_selection/unsupported_binding_disposition.json"
        ],
        "rationale": "Persist a checker-grounded audit of all supplied bindings. Preserve the two head-dimension legality errors; source/interface and numeric passes are evidence for their respective checks only and cannot establish strict binding.",
        "requires_approval": false,
        "stage": "template_selection",
        "tool_roles": [
          "template_binding_static_check",
          "parameter_binding_static_check",
          "numeric_policy_check"
        ]
      },
      {
        "acceptance_checkers": [
          "model_config_check",
          "parameter_binding_static_check",
          "template_binding_static_check"
        ],
        "action_type": "evidence_and_repair_review",
        "consumes": [
          "artifact.input.model_config",
          "artifact.stage2.template_selection",
          "constraint.shape.model",
          "constraint.template.library",
          "template_selection.model_shape_coverage_engineer findings"
        ],
        "id": "numeric_template.reconcile_authoritative_attention_shape",
        "on_failure": "If authoritative evidence is unavailable or confirms the supplied 1152/4/256 values, keep both bindings unsupported and the stage blocked. Do not use defaults or change template internals; route any required model, architecture, or template decision for approval.",
        "produces": [
          "review/template_selection/model_shape_reconciliation.json",
          "updated review/template_selection/strict_binding_audit.json",
          "updated review/template_selection/unsupported_binding_disposition.json"
        ],
        "rationale": "Resolve whether the model-shape facts or the candidate bindings are inconsistent using authoritative model evidence and the model-shape coverage engineer's findings. This is a fact audit, not permission to select substitute dimensions or alter the architecture.",
        "requires_approval": false,
        "stage": "template_selection",
        "tool_roles": [
          "model_config_check",
          "parameter_binding_static_check",
          "template_binding_static_check"
        ]
      },
      {
        "acceptance_checkers": [
          "template_binding_static_check",
          "parameter_binding_static_check",
          "numeric_policy_check",
          "sacg_static_check"
        ],
        "action_type": "bounded_template_repair",
        "consumes": [
          "artifact.stage2.template_selection",
          "artifact.input.model_config",
          "artifact.input.numeric_policy",
          "artifact.input.template_library",
          "artifact.input.template_metadata",
          "artifact.input.design_space",
          "artifact.input.target_board_profile",
          "state_summary.sacg_memory_truth",
          "review/template_selection/model_shape_coverage_review.json",
          "review/template_selection/strict_binding_audit.json",
          "review/template_selection/attention_semantic_binding_review.json"
        ],
        "id": "template_selection.resolve_attention_binding_and_recheck",
        "on_failure": "Keep template selection blocked and the contamination barrier active. Record the unresolved binding and affected constraints; do not modify golden outputs, loosen numeric policy, infer different model facts, or pass the candidate downstream.",
        "produces": [
          "review/template_selection/bounded_binding_repair.json",
          "artifact.stage2.template_selection.refined",
          "review/template_selection/cross_layer_gate_disposition.json",
          "review/template_selection/blocker_to_constraint_map.json"
        ],
        "rationale": "The current candidate has a concrete illegal binding for the block wrapper and self-attention. Obtain an evidence-backed resolution within the trusted-template boundary, then rerun static binding and numeric/SACG checks. Do not promote or release the contamination barrier unless the refined candidate passes.",
        "requires_approval": true,
        "stage": "template_selection",
        "tool_roles": [
          "bounded_template_repair",
          "template_binding_static_check",
          "parameter_binding_static_check",
          "numeric_policy_check",
          "sacg_static_check"
        ]
      }
    ],
    "execution_groups": [
      0,
      1
    ],
    "llm_io_metrics": {
      "executable_action_count": 6,
      "max_duration_sec": 67.41587649000576,
      "max_prompt_bytes": 82283,
      "result_count": 4,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 183.6581523049972,
      "total_prompt_bytes": 327498
    },
    "split_required": true,
    "status": "ready",
    "subtask_count": 4,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/team/subtask_plan.json",
    "used_fallback_count": 0
  },
  "errors": [
    "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024",
    "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
  ],
  "llm_agent": {},
  "missing_ops": [],
  "outputs": {
    "llm_agent": null,
    "sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/sacg_state.json",
    "team_aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/team/team_aggregate.json",
    "team_subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/team/subtask_plan.json",
    "template_selection": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/template_selection.json"
  },
  "required_adapters": [],
  "sacg_transition_id": "transition.0002",
  "schema_version": "spatialaccagent.template_selection_report.v0",
  "selected_template_ids": [
    "attention",
    "decoder_block",
    "elementwise",
    "ffn",
    "mask",
    "norm",
    "residual",
    "softmax"
  ],
  "source_sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/sacg_state.json",
  "stage": "template_selection",
  "status": "incomplete",
  "unsupported_bindings": [
    {
      "kind": "parameter_binding",
      "legality_errors": [
        "gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "missing_params": [],
      "op": "gemma3_text_block",
      "template_id": "decoder_block"
    },
    {
      "kind": "parameter_binding",
      "legality_errors": [
        "self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024"
      ],
      "missing_params": [],
      "op": "self_attention",
      "template_id": "attention"
    }
  ]
}
</recent_stage_summary>

<command>
[
  "/usr/bin/python3",
  "-m",
  "accagent.framework.stage_templates",
  "--sacg-state",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/sacg_state.json"
]
</command>

<command_returncode>
1
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/agent/logs/09_template_selection.json
</command_log>

<sacg_memory>
{
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage2.template_selection",
      "id": "contamination_barrier.0001",
      "last_observed_at": "2026-10-20T13:13:37+00:00",
      "observation_count": 2,
      "observed_transition_ids": [
        "transition.0001",
        "transition.0002"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "strict template binding failed: ['gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024', 'self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024']",
      "status": "active",
      "timestamp": "2026-10-20T13:09:12+00:00",
      "transition_id": "transition.0001"
    }
  ],
  "open_backtrack_requests": [],
  "open_retry_requests": [],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [
    {
      "artifact_id": "artifact.stage2.template_selection",
      "id": "contamination_barrier.0001",
      "last_observed_at": "2026-10-20T13:13:37+00:00",
      "observation_count": 2,
      "observed_transition_ids": [
        "transition.0001",
        "transition.0002"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "strict template binding failed: ['gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024', 'self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024']",
      "status": "active",
      "timestamp": "2026-10-20T13:09:12+00:00",
      "transition_id": "transition.0001"
    }
  ],
  "recent_failure_lessons": [],
  "recent_stage_outcomes": [],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gemma3_gpt61_20261020/template_selection/sacg_state.json
</source_sacg_state>

<stage_local_capabilities>
{
  "backend_board": {
    "compiled_pending_vcs": "the source-local patch and Chisel elaboration are complete; verify current sources compile-only, then return to Stage 7 synthesis",
    "run_local_timing_repair": "stage_backend invokes repair_timing_sources on current-run RTL after local_optimization is selected",
    "timing_repair_scope": "preserve Stage-4 parameters and shared templates; never restart code_generation for timing-only repair"
  }
}
</stage_local_capabilities>

<flow_policy>
{
  "allowed_design_backtrack_categories": [
    "design_defect",
    "hardware_design_failure",
    "design_target_miss",
    "timing_target_miss",
    "resource_limit_exceeded",
    "functional_design_failure",
    "rtl_design_failure",
    "performance_target_miss"
  ],
  "backend_timing_repair_does_not_need_a_planned_tool": true,
  "backtrack_counters_are_observability_only": true,
  "compiled_pending_vcs_must_not_restart_code_generation": true,
  "design_backtrack_requires_explicit_failure_category_and_linked_evidence": true,
  "do_not_use_failed_artifacts_as_validated_downstream_inputs": true,
  "framework_failure_on_failed_stage_action": "retry_current_stage_without_rewinding_design",
  "framework_hash_evidence_or_orchestration_failures_never_backtrack": true,
  "framework_never_terminates_a_valid_llm_repair_or_replan_loop": true,
  "honor_backtrack_requests_before_downstream_progress": true,
  "llm_is_required": true,
  "local_qor_optimization_is_an_evidence_supported_design_backtrack": true,
  "prefer_retry_same_stage_for_retry_requests": true,
  "stage_attempt_counters_are_observability_only": true
}
</flow_policy>

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

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 1,
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage2.template_selection",
      "id": "contamination_barrier.0001",
      "last_observed_at": "2026-10-20T13:13:37+00:00",
      "observation_count": 2,
      "observed_transition_ids": [
        "transition.0001",
        "transition.0002"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "strict template binding failed: ['gemma3_text_block: hidden_size=1152 does not equal num_q_heads*head_dim=1024', 'self_attention: hidden_size=1152 does not equal num_q_heads*head_dim=1024']",
      "status": "active",
      "timestamp": "2026-10-20T13:09:12+00:00",
      "transition_id": "transition.0001"
    }
  ],
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

<hierarchical_learning_context>
{
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
}
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
