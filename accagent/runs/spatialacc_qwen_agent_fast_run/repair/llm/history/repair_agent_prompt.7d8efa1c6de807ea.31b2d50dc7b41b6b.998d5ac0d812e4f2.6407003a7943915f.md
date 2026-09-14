<agent>
repair_agent
</agent>

<task>
Make the authoritative bounded-repair decision from verification failures, SACG/CCTG evidence, and the conditional specialist review when one was triggered, without bypassing checkers. Respect the hierarchical repair loop: if lower layers already passed and the current layer failed, request current-layer boundary trace/targeted replay first; reopen lower-layer modules only when the trace explicitly contradicts their pass evidence.
</task>

<rules>
1. Review only the supplied artifact summary and named constraints.
2. If inputs include subtask.role_assignment, act as that chip-design-team specialist: stay inside its mission, primary_responsibilities, decision_authority, collaboration_interfaces, and out_of_scope boundaries.
3. For sub-agent work, make observations, risks, approval_required_for, and executable_actions usable by peer agents through the declared handoff_to and acceptance_checkers; do not silently assume another specialist's responsibility.
4. Treat sacg_memory as the shared long-context design memory: preserve design goals, failure lessons, retry requests, backtrack requests, and contamination barriers.
5. Treat sacg_memory_truth as the authoritative current blocker set: only active_contamination_barriers and open retry/backtrack requests listed there are current SACG-memory blockers.
6. Do not infer active blockers from historical, closed, superseded, rejected, or recently summarized records when sacg_memory_truth shows the corresponding active/open count is zero.
7. When agent_status_bar is supplied, treat it as deterministic framework-maintained current-state metadata for scope identity, active blocker counts, certified lower-layer identities, and current evidence frontier. It does not replace raw SACG/CCTG records or real tool artifacts, and omitted raw detail is not evidence of absence.
8. If sacg_memory contains open backtrack_requests or contamination_barriers relevant to this stage, address them explicitly in observations and executable_actions.
9. If inputs include a retry_reconciliation_contract for the current stage, distinguish previous failed artifacts from the candidate retry artifacts: same-stage retry requests/barriers are downstream-consumption blockers until promotion, but they are not independent blockers for approving a refined current-stage contract that explicitly supersedes them after all current-stage checks pass.
10. If inputs include stage_gate_policy, use it to classify current-stage blocking risks versus later-stage actions.
11. If inputs include role_slice_policy or presence_summary, do not infer a field is missing merely because detailed rows were omitted from a compact/role-specific prompt slice.
12. When presence_summary says an artifact class exists, report missing-detail concerns as handoff/action items unless the visible checker status proves a current-stage blocker.
13. Report cross-layer consistency risks across model, shape, numeric policy, data order, memory, runtime, implementation, and board facts.
14. Keep actions bounded and executable by later tools/checkers.
15. Populate executable_actions with concrete next tool/repair actions; each action must name consumed artifacts, produced artifacts, tool roles, acceptance checkers, failure handling, and approval need.
16. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible; do not invent Qwen/OPT-specific core names unless they are supplied by the case adapter or tool protocol.
17. For backend/app-shell target discovery, treat the LLM as the adaptive board-integration engineer: convert supplied board materials and real Vivado evidence into target_discovery_policy updates with cited artifacts; if evidence is ambiguous, require bounded approval instead of guessing names.
18. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name> and state the implementation gap in rationale.
19. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
20. For verification/backend failures, executable_actions must drive the next stage/tool decision instead of relying on static scripts or human memory.
21. For hardware debug, enforce the three-layer repair loop: first operator/leaf modules, then the connected single-transformer-layer kernel, then the board-accurate AXI/DDR wrapped system. A failed layer must enter tool-output -> CCTG/contract-guided localization -> bounded repair -> rerun, and must not promote or skip to a higher layer.
22. When hierarchical_learning_context is supplied, treat it as live hash-validated lower-layer knowledge rather than informal history. Reuse its certified invariants, and reopen a lower layer only for a current trace that explicitly contradicts a named invariant.
23. When hierarchical_learning_context supplies connected-kernel timing knowledge, preserve its elastic variable-latency token-pipeline semantics: required boundary order and cross-token overlap matter, while strict same-cycle start/end across unequal-latency stages is not required.
24. At board scope, distinguish independent AXI/prefetch progress from output or lifecycle-frontier progress. A current frontier stall localizes what to observe next, but is neither a pass claim nor a preselected RTL root cause.
25. A board output-frontier symptom alone cannot reopen a certified connected kernel. Require a current hash-bound lower-layer contradiction with direct core start, ingress, egress, named causal-boundary, and current-certificate evidence before scheduling lower-layer revalidation.
26. Before any functional pass, require a complete target-checkpoint tensor catalog, deterministic or real input provenance, target-model inference expected outputs for the same input/checkpoint, a resolved numeric comparison tolerance (current-run values first, otherwise frozen framework loose defaults), generated semantic testbench hashes, and proof that the DUT consumed every required bound weight.
27. Applying the recorded framework loose defaults for initially missing atol, rtol, or max_mismatch_fraction is authorized and is not a repair-time tolerance change. Never derive or loosen those values from DUT output.
28. A random generator may produce input stimulus only. Never generate expected output randomly, derive it from RTL output, replace model inference with an identity/default implementation, or treat sampled weights as complete evidence.
29. During repair, keep checkpoint, stimulus, target-model reference, numeric policy, tolerance, testbench contract, and exact board-wrapper source hashes immutable. Repair the DUT, loader/harness, instrumentation, or integration that violated the contract.
30. At the third layer, use the exact wrapper and simulation sources discovered from the current user-supplied sample project. Do not substitute a simplified AXI/DDR wrapper or hardcode model, board, module, or path names into framework-core actions.
31. Treat Transformer blocks as the complete accelerator scope. Exclude embedding/tokenization, final model norm, LM head/logits, and sampling from DUT implementation, DUT weight coverage, and acceptance golden boundaries.
32. When a verifier capability is missing, classify it as a checker/golden-reference repair, not as hardware correctness. When real RTL/tool evidence shows liveness, value, order, or protocol failure, localize the earliest causal boundary/module before proposing a code repair.
33. Use approval_required_for for architecture, pipeline, memory layout, numeric policy, or major template changes.
</rules>

<candidate_repair_plan>
{
  "case_adapter": {
    "case_id": "qwen2_hf_case",
    "model_family": "qwen2",
    "source": "built_in_case_adapter",
    "status": "ready"
  },
  "diagnostics": {
    "case_vcs_functional": {
      "applicability": {
        "current_failed_gates": [
          "case_multilayer_pipeline",
          "functional_sim"
        ],
        "current_layer": "board_axi_ddr_wrapped_system",
        "executable": false,
        "reason": "persisted diagnosis lacks a source-bound applicability binding",
        "relation": null,
        "schema_version": "spatialaccagent.diagnosis_applicability_report.v1",
        "status": "historical_only",
        "target_layer": "single_transformer_layer_kernel",
        "validation_errors": [
          "applicability_binding is required for executable reuse"
        ]
      },
      "policy": "The raw diagnosis is durable project history but is omitted from the repair-agent prompt because it is not bound to the current hierarchy layer, failed gate, and live source artifacts.",
      "schema_version": "spatialaccagent.repair_diagnosis_prompt_projection.v1",
      "source_schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
      "status": "historical_only"
    },
    "case_vcs_functional_applicability": {
      "current_failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "current_layer": "board_axi_ddr_wrapped_system",
      "executable": false,
      "reason": "persisted diagnosis lacks a source-bound applicability binding",
      "schema_version": "spatialaccagent.diagnosis_applicability_report.v1",
      "status": "historical_only",
      "target_layer": "single_transformer_layer_kernel",
      "validation_errors": [
        "applicability_binding is required for executable reuse"
      ]
    },
    "contract_guided_debug_closure": {
      "causal_path": {
        "boundary_order": [
          "boundary.edge_data_block_input_to_stage_00_rms_norm_1_input",
          "boundary.edge_data_block_input_to_stage_02_residual_add_1_residual_skip",
          "boundary.edge_data_stage_00_rms_norm_1_to_stage_01_self_attention_main",
          "boundary.edge_data_stage_01_self_attention_to_stage_02_residual_add_1_main",
          "boundary.edge_data_stage_02_residual_add_1_to_stage_03_rms_norm_2_main",
          "boundary.edge_data_stage_02_residual_add_1_to_stage_08_residual_add_2_residual_skip",
          "boundary.edge_data_stage_03_rms_norm_2_to_stage_04_mlp_gate_proj_mlp_gate_branch",
          "boundary.edge_data_stage_03_rms_norm_2_to_stage_05_mlp_up_proj_mlp_up_branch",
          "boundary.edge_data_stage_04_mlp_gate_proj_to_stage_06_activation_mul_mlp_gate_to_mul",
          "boundary.edge_data_stage_05_mlp_up_proj_to_stage_06_activation_mul_mlp_up_to_mul",
          "boundary.edge_data_stage_06_activation_mul_to_stage_07_mlp_down_proj_main",
          "boundary.edge_data_stage_07_mlp_down_proj_to_stage_08_residual_add_2_main",
          "boundary.edge_data_stage_08_residual_add_2_to_block_output_output"
        ],
        "path_id": "default_pipeline_path",
        "stages": [
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
      "current_layer_failure_context": {},
      "failed_boundaries": [],
      "failing_transaction": {
        "checker": "real_tool.case_multilayer_pipeline",
        "source": "verification_result",
        "summary": "returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources"
      },
      "failure_record_count": 0,
      "failure_signature": {
        "boundary": null,
        "boundary_id": null,
        "expected_value": null,
        "integration_summary": null,
        "observed_value": null,
        "status": null,
        "summary": null
      },
      "lower_layer_evidence_challenge": {
        "reason": "no localized trace record with lower-layer pass evidence is available",
        "status": "no_lower_layer_challenge"
      },
      "minimal_repair_context": {
        "boundary_contract": {},
        "current_layer_failure_context": {},
        "lower_layer_evidence_challenge": {
          "reason": "no localized trace record with lower-layer pass evidence is available",
          "status": "no_lower_layer_challenge"
        },
        "repair_scope": "verification_capability_repair",
        "root_candidate_module": null,
        "trace_record": {},
        "violated_contract": "verification_semantic_capability_contract"
      },
      "policy": {
        "do_not_patch_output_module_only_because_symptom_is_downstream": true,
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
        "if_status_needs_boundary_trace_rerun_stage7_with_boundary_monitors": true,
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "repair_agent_should_use_causal_slice_only": true,
        "verification_capability_gap_must_be_repaired_before_hardware_trace": true
      },
      "recommended_trace_gate": null,
      "representative_failure_count": 0,
      "root_candidate_module": null,
      "schema_version": "spatialaccagent.debug_closure.v0",
      "status": "verification_capability_gap",
      "strategy": "contract_guided_boundary_failure_slice",
      "targeted_replay_plan": {
        "reason": "repair semantic testbench, loader/weight binding, numeric contract, or checker capability before requesting a hardware boundary trace",
        "status": "blocked_by_verification_capability_gap"
      },
      "violated_contract": "verification_semantic_capability_contract"
    },
    "hierarchical_repair_loop": {
      "agent_runtime_llm_blocker": false,
      "current_layer": {
        "id": "board_axi_ddr_wrapped_system",
        "missing_or_failed": [
          "case_multilayer_pipeline=fail",
          "case_multilayer_functional=not_run",
          "case_pipeline_deadlock_check=not_run",
          "case_axi_ddr_interface=not_run",
          "case_axi_protocol_check=not_run",
          "case_ddr_image_roundtrip=not_run",
          "functional_sim=fail",
          "case_board_semantic_evidence=not_run"
        ],
        "order": 2,
        "promotion_target": "backend_bitstream_and_board_runtime",
        "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
        "repair_loop": "board_wrapper_tool_run__cctg_axi_ddr_slice__bounded_wrapper_or_runtime_repair__rerun",
        "required_gates": [
          {
            "name": "case_board_interface_discovery",
            "status": "pass"
          },
          {
            "name": "case_multilayer_pipeline",
            "status": "fail"
          },
          {
            "name": "case_multilayer_functional",
            "status": "not_run"
          },
          {
            "name": "case_pipeline_deadlock_check",
            "status": "not_run"
          },
          {
            "name": "case_axi_ddr_interface",
            "status": "not_run"
          },
          {
            "name": "case_axi_protocol_check",
            "status": "not_run"
          },
          {
            "name": "case_ddr_image_roundtrip",
            "status": "not_run"
          },
          {
            "name": "functional_sim",
            "status": "fail"
          },
          {
            "name": "case_board_semantic_evidence",
            "status": "not_run"
          }
        ],
        "status": "needs_repair"
      },
      "debug_loop_contract": {
        "anti_spin_policy": {
          "current_layer_failure_after_lower_pass_means": "debug current-layer integration, interconnect, wrapper, scheduler, data order, or boundary contract first",
          "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace": true,
          "lower_layer_pass_evidence_is_reusable_not_absolute": true,
          "passed_lower_layer_can_be_challenged_by_current_layer_trace": true,
          "reopening_lower_layer_requires": [
            "a current-layer boundary trace record that directly contradicts lower-layer pass evidence",
            "or a SACG-approved design-contract change invalidating the previous lower-layer evidence"
          ],
          "when_reopened": [
            "record the contradicted lower-layer gate/module and source trace in SACG",
            "rerun only the challenged lower-layer scope with expanded boundary stimuli or corrected contract",
            "after lower-layer revalidation, rerun the failed current layer before any higher-layer promotion"
          ]
        },
        "cctg_policy": {
          "first_action_when_trace_missing": "debug_trace_rerun for the failed current-layer gate",
          "localized_action": "causal_slice_repair over the localized boundary or current-layer integration slice",
          "purpose": "speed root-cause localization by mapping real-tool symptoms to the earliest violated contract/boundary",
          "required_on_failure": true,
          "trace_schema_is_case_adapter_driven": true
        },
        "layer_order": [
          "operator_leaf_modules",
          "single_transformer_layer_kernel",
          "board_axi_ddr_wrapped_system"
        ],
        "layers": [
          {
            "entry_condition": "Stage6 verification gate DAG and real case-adapter tools are available",
            "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
            "failure_loop": [
              "run current-layer real tool",
              "collect CCTG boundary trace or failure localization evidence",
              "classify earliest violated boundary/current-layer contract",
              "apply only bounded repair permitted by SACG/human-boundary rules",
              "rerun the same current layer until pass before promotion"
            ],
            "id": "operator_leaf_modules",
            "order": 0,
            "promotion_target": "single_transformer_layer_kernel",
            "purpose": "Debug every spatially parallel operator module before integration.",
            "required_gates": [
              "case_real_weight_artifacts",
              "case_target_model_reference",
              "case_semantic_testbench",
              "case_stage_leaf_static",
              "boundary_contract_check",
              "case_leaf_functional",
              "case_leaf_golden_compare",
              "case_operator_leaf_semantic_evidence"
            ]
          },
          {
            "entry_condition": "all lower debug layers have pass evidence",
            "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
            "failure_loop": [
              "run current-layer real tool",
              "collect CCTG boundary trace or failure localization evidence",
              "classify earliest violated boundary/current-layer contract",
              "apply only bounded repair permitted by SACG/human-boundary rules",
              "rerun the same current layer until pass before promotion"
            ],
            "id": "single_transformer_layer_kernel",
            "order": 1,
            "promotion_target": "board_axi_ddr_wrapped_system",
            "purpose": "Debug the connected one-layer transformer spatial kernel after leaf modules pass.",
            "required_gates": [
              "single_transformer_layer",
              "case_single_layer_functional",
              "case_single_layer_golden_compare",
              "case_single_layer_semantic_evidence"
            ]
          },
          {
            "entry_condition": "all lower debug layers have pass evidence",
            "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
            "failure_loop": [
              "run current-layer real tool",
              "collect CCTG boundary trace or failure localization evidence",
              "classify earliest violated boundary/current-layer contract",
              "apply only bounded repair permitted by SACG/human-boundary rules",
              "rerun the same current layer until pass before promotion"
            ],
            "id": "board_axi_ddr_wrapped_system",
            "order": 2,
            "promotion_target": "backend_bitstream_and_board_runtime",
            "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
            "required_gates": [
              "case_board_interface_discovery",
              "case_multilayer_pipeline",
              "case_multilayer_functional",
              "case_pipeline_deadlock_check",
              "case_axi_ddr_interface",
              "case_axi_protocol_check",
              "case_ddr_image_roundtrip",
              "functional_sim",
              "case_board_semantic_evidence"
            ]
          }
        ],
        "promotion_policy": {
          "backend_or_board_runtime_requires_all_three_debug_layers_to_pass": true,
          "dependency_skipped_or_smoke_evidence_cannot_promote": true,
          "next_layer_requires_current_layer_certificate": true
        },
        "schema_version": "spatialaccagent.hierarchical_debug_loop_contract.v0"
      },
      "failed_current_layer_gates": [
        {
          "name": "case_multilayer_pipeline",
          "status": "fail"
        },
        {
          "name": "case_multilayer_functional",
          "status": "not_run"
        },
        {
          "name": "case_pipeline_deadlock_check",
          "status": "not_run"
        },
        {
          "name": "case_axi_ddr_interface",
          "status": "not_run"
        },
        {
          "name": "case_axi_protocol_check",
          "status": "not_run"
        },
        {
          "name": "case_ddr_image_roundtrip",
          "status": "not_run"
        },
        {
          "name": "functional_sim",
          "status": "fail"
        },
        {
          "name": "case_board_semantic_evidence",
          "status": "not_run"
        }
      ],
      "failure_kind": "verification_capability_gap",
      "layers": [
        {
          "id": "operator_leaf_modules",
          "missing_or_failed": [],
          "order": 0,
          "promotion_target": "single_transformer_layer_kernel",
          "purpose": "Debug every spatially parallel operator module before integration.",
          "repair_loop": "module_tool_run__cctg_localize__bounded_module_or_checker_repair__rerun",
          "required_gates": [
            {
              "name": "case_real_weight_artifacts",
              "status": "pass"
            },
            {
              "name": "case_target_model_reference",
              "status": "pass"
            },
            {
              "name": "case_semantic_testbench",
              "status": "pass"
            },
            {
              "name": "case_stage_leaf_static",
              "status": "pass"
            },
            {
              "name": "boundary_contract_check",
              "status": "pass"
            },
            {
              "name": "case_leaf_functional",
              "status": "pass"
            },
            {
              "name": "case_leaf_golden_compare",
              "status": "pass"
            },
            {
              "name": "case_operator_leaf_semantic_evidence",
              "status": "pass"
            }
          ],
          "status": "pass"
        },
        {
          "id": "single_transformer_layer_kernel",
          "missing_or_failed": [],
          "order": 1,
          "promotion_target": "board_axi_ddr_wrapped_system",
          "purpose": "Debug the connected one-layer transformer spatial kernel after leaf modules pass.",
          "repair_loop": "layer_tool_run__cctg_failure_slice__bounded_interconnect_or_module_repair__rerun",
          "required_gates": [
            {
              "name": "single_transformer_layer",
              "status": "pass"
            },
            {
              "name": "case_single_layer_functional",
              "status": "pass"
            },
            {
              "name": "case_single_layer_golden_compare",
              "status": "pass"
            },
            {
              "name": "case_single_layer_semantic_evidence",
              "status": "pass"
            }
          ],
          "status": "pass"
        },
        {
          "id": "board_axi_ddr_wrapped_system",
          "missing_or_failed": [
            "case_multilayer_pipeline=fail",
            "case_multilayer_functional=not_run",
            "case_pipeline_deadlock_check=not_run",
            "case_axi_ddr_interface=not_run",
            "case_axi_protocol_check=not_run",
            "case_ddr_image_roundtrip=not_run",
            "functional_sim=fail",
            "case_board_semantic_evidence=not_run"
          ],
          "order": 2,
          "promotion_target": "backend_bitstream_and_board_runtime",
          "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
          "repair_loop": "board_wrapper_tool_run__cctg_axi_ddr_slice__bounded_wrapper_or_runtime_repair__rerun",
          "required_gates": [
            {
              "name": "case_board_interface_discovery",
              "status": "pass"
            },
            {
              "name": "case_multilayer_pipeline",
              "status": "fail"
            },
            {
              "name": "case_multilayer_functional",
              "status": "not_run"
            },
            {
              "name": "case_pipeline_deadlock_check",
              "status": "not_run"
            },
            {
              "name": "case_axi_ddr_interface",
              "status": "not_run"
            },
            {
              "name": "case_axi_protocol_check",
              "status": "not_run"
            },
            {
              "name": "case_ddr_image_roundtrip",
              "status": "not_run"
            },
            {
              "name": "functional_sim",
              "status": "fail"
            },
            {
              "name": "case_board_semantic_evidence",
              "status": "not_run"
            }
          ],
          "status": "needs_repair"
        }
      ],
      "lower_layer_evidence_challenge": {
        "lower_layer_pass_evidence": [
          "case_real_weight_artifacts",
          "case_target_model_reference",
          "case_semantic_testbench",
          "case_stage_leaf_static",
          "boundary_contract_check",
          "case_leaf_functional",
          "case_leaf_golden_compare",
          "case_operator_leaf_semantic_evidence",
          "single_transformer_layer",
          "case_single_layer_functional",
          "case_single_layer_golden_compare",
          "case_single_layer_semantic_evidence"
        ],
        "reason": "challenge object is present but does not assert a contradiction",
        "status": "no_lower_layer_challenge"
      },
      "lower_layer_pass_evidence": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_stage_leaf_static",
        "boundary_contract_check",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence",
        "single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "case_single_layer_semantic_evidence"
      ],
      "out_of_order_executed_higher_layer_gates": [],
      "policy": {
        "cctg_required_for_root_cause_localization": true,
        "current_layer_failure_after_lower_pass_means_integration_boundary_debug": true,
        "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": true,
        "failed_layer_must_repair_before_next_layer": true,
        "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": true,
        "lower_layer_pass_evidence_is_reusable_not_absolute": true,
        "no_stage_promotion_from_smoke_or_dependency_skipped_evidence": true,
        "three_layer_debug_order_is_mandatory": true,
        "tool_output_then_llm_analysis_then_bounded_patch_then_rerun": true
      },
      "root_candidate_module": null,
      "schema_version": "spatialaccagent.hierarchical_repair_loop.v0",
      "status": "needs_repair",
      "violated_contract": "verification_semantic_capability_contract"
    },
    "prior_repair_execution_feedback": {
      "blockers": [
        "step_results[0] referenced LLM record is fallback or errored"
      ],
      "execution_errors": [],
      "input_fingerprint_sha256": "f3b977ae07a7e6b8b914c2a8a55a21442def19d8ed08b793fcd5deacee375bdb",
      "llm_records": [],
      "repair_execution_status": null,
      "report": {
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/repair_execution_report.json",
        "sha256": "5556f8a637f0639377d08a65644b81550d7b995876a3499a2c0883172690a544"
      },
      "required_capabilities": [],
      "schema_version": "spatialaccagent.prior_repair_execution_feedback.v1",
      "status": "invalid",
      "summary": "prior repair execution feedback failed closed integrity validation",
      "validation": {
        "errors": [
          "step_results[0] referenced LLM record is fallback or errored"
        ],
        "status": "fail"
      }
    }
  },
  "failures": [
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_multilayer_pipeline",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate multilayer_pipeline",
      "execution_fingerprint_sha256": "ef97715fcd3ddcec83cb3e9c31556fef04d9fd8569990306c58d7e67a247dde7",
      "failure_class": "runtime_harness",
      "kind": "case_multilayer_pipeline",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_multilayer_pipeline.json",
      "produced_reports": [
        {
          "blockers": [
            "DUT binding does not cover every transformer-block weight in every target layer",
            "hash-verified multi-layer pipeline harness is missing",
            "failed checks: multilayer_real_weight_binding, multilayer_harness_sources"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/multilayer_pipeline.json",
          "schema_version": "spatialaccagent.qwen_hierarchical_check.v0",
          "status": "fail",
          "summary": null
        }
      ],
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "fail",
      "summary": "returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
      "tool_report_blockers": [
        "DUT binding does not cover every transformer-block weight in every target layer",
        "hash-verified multi-layer pipeline harness is missing",
        "failed checks: multilayer_real_weight_binding, multilayer_harness_sources"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/multilayer_pipeline.json",
      "tool_report_status": "fail",
      "tool_report_summary": null
    },
    {
      "checker": "case_functional_sim_precondition_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']"
    },
    {
      "checker": "required_real_tool_evidence_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']"
    },
    {
      "checker": "real_weight_semantic_evidence_check",
      "failure_class": "framework_consistency",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
    },
    {
      "checker": "hierarchical_verification_maturity_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
    },
    {
      "checker": "verification_agent_decision_check",
      "failure_class": "runtime_harness",
      "repair_hint": "inspect violated constraint and rerun the related checker",
      "status": "fail",
      "summary": "verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to synthesis, implementation, bitstream, runtime ABI release, or board runtime. The earliest directly executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): complete Transformer-block tensor-to-loader-to-DUT binding for every target layer and a hash-verified multilayer harness source closure are absent. board_tb.sv is also absent as a downstream functional-simulation precondition. functional_sim is failed as an unsatisfied aggregate dependency gate, not executed VCS, RTL, numeric, AXI, DDR, liveness, or output-order evidence. Certified operator-leaf and elastic connected-single-layer evidence remains reusable because no current hash-bound trace contradicts a named lower-layer invariant."
    }
  ],
  "note": "Failing checkers are classified; not_run real tools are evidence gaps, not automatic repair failures.",
  "pending_evidence": [
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_axi_ddr_interface",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate axi_ddr_interface",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_axi_ddr_interface",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_axi_ddr_interface.json",
      "produced_reports": [
        {
          "blockers": [
            "simulation.status is not ready/pass",
            "simulation.source_identity_sha256 does not bind the current identity document",
            "simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts",
            "simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
            "simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
            "simulation.vcs_compile_plan.ordered_commands[1].authority_refs do not bind exact Vivado export contexts",
            "simulation.vcs_compile_plan.ordered_commands[1].executable is not authorized by current tool_profile or referenced Vivado export"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/axi_ddr_interface.json",
          "schema_version": "spatialaccagent.qwen_hierarchical_check.v0",
          "status": "fail",
          "summary": null
        }
      ],
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_multilayer_pipeline'] report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
      "tool_report_blockers": [
        "simulation.status is not ready/pass",
        "simulation.source_identity_sha256 does not bind the current identity document",
        "simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts",
        "simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "simulation.vcs_compile_plan.ordered_commands[0].executable is not authorized by current tool_profile or referenced Vivado export",
        "simulation.vcs_compile_plan.ordered_commands[1].authority_refs do not bind exact Vivado export contexts",
        "simulation.vcs_compile_plan.ordered_commands[1].executable is not authorized by current tool_profile or referenced Vivado export"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/qwen_hierarchy/axi_ddr_interface.json",
      "tool_report_status": "fail",
      "tool_report_summary": null
    },
    {
      "acceptance_role": "functional_sim_candidate",
      "checker": "real_tool.case_vcs_functional_sim",
      "command": "python3 scripts/verification/case_board_vcs_functional.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "vcs_real_functional_sim",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_vcs_functional_sim.json",
      "produced_reports": [
        {
          "blockers": [],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
          "schema_version": "spatialaccagent.board_vcs_functional_run.v1",
          "status": "fail",
          "summary": null
        },
        {
          "blockers": [],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
          "schema_version": "spatialaccagent.boundary_trace.v0",
          "status": "ready",
          "summary": null
        }
      ],
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": "functional_sim",
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_multilayer_pipeline', 'case_axi_ddr_interface']",
      "tool_report_blockers": [],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/vcs/case_board_vcs_functional.json",
      "tool_report_status": "fail",
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_vcs_evidence_analyzer",
      "command": "python3 scripts/verification/qwen_vcs_evidence_analyzer.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "vcs_evidence_analyzer",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_vcs_evidence_analyzer.json",
      "produced_reports": [
        {
          "blockers": [
            "intra_layer_spatial_pipeline_violation: all 16 input tokens completed by cycle 20805737 while the ready kernel output accepted zero beats"
          ],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
          "schema_version": "spatialaccagent.case_vcs_functional_diagnosis.v2",
          "status": "needs_repair",
          "summary": "intra_layer_spatial_pipeline_violation: all 16 input tokens completed by cycle 20805737 while the ready kernel output accepted zero beats"
        },
        {
          "blockers": [],
          "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/debug_closure/boundary_trace.json",
          "schema_version": "spatialaccagent.boundary_trace.v0",
          "status": "ready",
          "summary": null
        }
      ],
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": "target_model_oracle",
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_multilayer_pipeline', 'case_axi_ddr_interface'] report_status=needs_repair blockers=intra_layer_spatial_pipeline_violation: all 16 input tokens completed by cycle 20805737 while the ready kernel output accepted zero beats",
      "tool_report_blockers": [
        "intra_layer_spatial_pipeline_violation: all 16 input tokens completed by cycle 20805737 while the ready kernel output accepted zero beats"
      ],
      "tool_report_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/vcs_functional_diagnosis.json",
      "tool_report_status": "needs_repair",
      "tool_report_summary": "intra_layer_spatial_pipeline_violation: all 16 input tokens completed by cycle 20805737 while the ready kernel output accepted zero beats"
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_deadlock_axi_check",
      "command": "python3 scripts/verification/case_deadlock_axi_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/case_diagnostics/deadlock_axi_check.json --rtl-wrapper /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_interface/sample_project_sources/wrapper.v --testbench /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_deadlock_axi_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_deadlock_axi_check.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['case_multilayer_pipeline', 'case_axi_ddr_interface']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_multilayer_functional",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate multilayer_functional",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_multilayer_functional",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_multilayer_functional.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_multilayer_pipeline']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_pipeline_deadlock_check",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate pipeline_deadlock",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_pipeline_deadlock_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_pipeline_deadlock_check.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_multilayer_functional']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_axi_protocol_check",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate axi_protocol",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_axi_protocol_check",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_axi_protocol_check.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_axi_ddr_interface']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_ddr_image_roundtrip",
      "command": "python3 scripts/verification/qwen_hierarchical_check.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --gate ddr_image_roundtrip",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "case_ddr_image_roundtrip",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_ddr_image_roundtrip.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_axi_protocol_check']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    },
    {
      "acceptance_role": "diagnostic_or_static_tool",
      "checker": "real_tool.case_board_semantic_evidence",
      "command": "python3 scripts/verification/semantic_evidence_assembler.py --run-dir /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run --level axi_ddr_functional --out /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
      "execution_fingerprint_sha256": null,
      "failure_class": "pending_required_evidence",
      "kind": "semantic_evidence_assemble",
      "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/real_tools/case_board_semantic_evidence.json",
      "python_environment": null,
      "python_environment_fingerprint_sha256": null,
      "python_environment_group": null,
      "required": true,
      "required_group": null,
      "reused_existing_result": false,
      "status": "not_run",
      "summary": "skipped because dependency gate(s) are not pass: ['functional_sim', 'case_multilayer_functional', 'case_pipeline_deadlock_check', 'case_axi_protocol_check', 'case_ddr_image_roundtrip']",
      "tool_report_blockers": [],
      "tool_report_path": null,
      "tool_report_status": null,
      "tool_report_summary": null
    }
  ],
  "repair_actions": [
    {
      "approval_required": false,
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_current_layer_gates": [
        {
          "name": "case_multilayer_pipeline",
          "status": "fail"
        },
        {
          "name": "case_multilayer_functional",
          "status": "not_run"
        },
        {
          "name": "case_pipeline_deadlock_check",
          "status": "not_run"
        },
        {
          "name": "case_axi_ddr_interface",
          "status": "not_run"
        },
        {
          "name": "case_axi_protocol_check",
          "status": "not_run"
        },
        {
          "name": "case_ddr_image_roundtrip",
          "status": "not_run"
        },
        {
          "name": "functional_sim",
          "status": "fail"
        },
        {
          "name": "case_board_semantic_evidence",
          "status": "not_run"
        }
      ],
      "failure_signature": {
        "failed_gates": [
          "case_multilayer_pipeline",
          "functional_sim"
        ],
        "summaries": [
          "returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
          "real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
          "required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
          "real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
          "multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
          "verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to synthesis, implementation, bitstream, runtime ABI release, or board runtime. The earliest directly executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): complete Transformer-block tensor-to-loader-to-DUT binding for every target layer and a hash-verified multilayer harness source closure are absent. board_tb.sv is also absent as a downstream functional-simulation precondition. functional_sim is failed as an unsatisfied aggregate dependency gate, not executed VCS, RTL, numeric, AXI, DDR, liveness, or output-order evidence. Certified operator-leaf and elastic connected-single-layer evidence remains reusable because no current hash-bound trace contradicts a named lower-layer invariant."
        ]
      },
      "minimal_repair_context": {
        "failed_current_layer_gates": [
          {
            "name": "case_multilayer_pipeline",
            "status": "fail"
          },
          {
            "name": "case_multilayer_functional",
            "status": "not_run"
          },
          {
            "name": "case_pipeline_deadlock_check",
            "status": "not_run"
          },
          {
            "name": "case_axi_ddr_interface",
            "status": "not_run"
          },
          {
            "name": "case_axi_protocol_check",
            "status": "not_run"
          },
          {
            "name": "case_ddr_image_roundtrip",
            "status": "not_run"
          },
          {
            "name": "functional_sim",
            "status": "fail"
          },
          {
            "name": "case_board_semantic_evidence",
            "status": "not_run"
          }
        ]
      },
      "reason": "current layer lacks a valid semantic loader/harness, immutable numeric comparison contract, or executed weight-consumption evidence",
      "repair_gate": "case_multilayer_pipeline",
      "repair_kind": "exact_board_integration_harness",
      "root_candidate_module": null,
      "scope": "verification_capability_repair",
      "source": "hierarchical_repair_loop",
      "target_modules": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "violated_contract": "current_verification_capability_must_execute_before_hardware_repair"
    }
  ],
  "repair_workflow": {
    "approval_steps": [],
    "blockers": [],
    "case_adapter": {
      "case_id": "qwen2_hf_case",
      "model_family": "qwen2",
      "status": "ready"
    },
    "policy": {
      "cctg_boundary_trace_or_localization_required_before_code_repair": true,
      "do_not_apply_unbounded_code_changes": true,
      "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace": true,
      "do_not_rerun_smoke_as_acceptance": true,
      "lower_layer_pass_evidence_is_reusable_not_absolute": true,
      "regression_reruns_must_use_case_tool_protocols": true,
      "repair_output_must_return_to_stage7": true,
      "same_debug_layer_must_rerun_until_functionally_correct_before_promotion": true,
      "targeted_lower_layer_backtrack_requires_contradicting_current_layer_trace": true
    },
    "run_dir": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run",
    "schema_version": "spatialaccagent.repair_workflow.v0",
    "status": "ready",
    "steps": [
      {
        "action": {
          "approval_required": false,
          "debug_layer": "board_axi_ddr_wrapped_system",
          "failed_current_layer_gates": [
            {
              "name": "case_multilayer_pipeline",
              "status": "fail"
            },
            {
              "name": "case_multilayer_functional",
              "status": "not_run"
            },
            {
              "name": "case_pipeline_deadlock_check",
              "status": "not_run"
            },
            {
              "name": "case_axi_ddr_interface",
              "status": "not_run"
            },
            {
              "name": "case_axi_protocol_check",
              "status": "not_run"
            },
            {
              "name": "case_ddr_image_roundtrip",
              "status": "not_run"
            },
            {
              "name": "functional_sim",
              "status": "fail"
            },
            {
              "name": "case_board_semantic_evidence",
              "status": "not_run"
            }
          ],
          "failure_signature": {
            "failed_gates": [
              "case_multilayer_pipeline",
              "functional_sim"
            ],
            "summaries": [
              "returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
              "real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
              "required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
              "real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
              "multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
              "verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to synthesis, implementation, bitstream, runtime ABI release, or board runtime. The earliest directly executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): complete Transformer-block tensor-to-loader-to-DUT binding for every target layer and a hash-verified multilayer harness source closure are absent. board_tb.sv is also absent as a downstream functional-simulation precondition. functional_sim is failed as an unsatisfied aggregate dependency gate, not executed VCS, RTL, numeric, AXI, DDR, liveness, or output-order evidence. Certified operator-leaf and elastic connected-single-layer evidence remains reusable because no current hash-bound trace contradicts a named lower-layer invariant."
            ]
          },
          "minimal_repair_context": {
            "failed_current_layer_gates": [
              {
                "name": "case_multilayer_pipeline",
                "status": "fail"
              },
              {
                "name": "case_multilayer_functional",
                "status": "not_run"
              },
              {
                "name": "case_pipeline_deadlock_check",
                "status": "not_run"
              },
              {
                "name": "case_axi_ddr_interface",
                "status": "not_run"
              },
              {
                "name": "case_axi_protocol_check",
                "status": "not_run"
              },
              {
                "name": "case_ddr_image_roundtrip",
                "status": "not_run"
              },
              {
                "name": "functional_sim",
                "status": "fail"
              },
              {
                "name": "case_board_semantic_evidence",
                "status": "not_run"
              }
            ]
          },
          "reason": "current layer lacks a valid semantic loader/harness, immutable numeric comparison contract, or executed weight-consumption evidence",
          "repair_gate": "case_multilayer_pipeline",
          "repair_kind": "exact_board_integration_harness",
          "root_candidate_module": null,
          "scope": "verification_capability_repair",
          "source": "hierarchical_repair_loop",
          "target_modules": [
            "case_multilayer_pipeline",
            "functional_sim"
          ],
          "violated_contract": "current_verification_capability_must_execute_before_hardware_repair"
        },
        "approval_required": false,
        "debug_layer": "board_axi_ddr_wrapped_system",
        "id": "repair_step.00",
        "repair_context": {
          "failed_current_layer_gates": [
            {
              "name": "case_multilayer_pipeline",
              "status": "fail"
            },
            {
              "name": "case_multilayer_functional",
              "status": "not_run"
            },
            {
              "name": "case_pipeline_deadlock_check",
              "status": "not_run"
            },
            {
              "name": "case_axi_ddr_interface",
              "status": "not_run"
            },
            {
              "name": "case_axi_protocol_check",
              "status": "not_run"
            },
            {
              "name": "case_ddr_image_roundtrip",
              "status": "not_run"
            },
            {
              "name": "functional_sim",
              "status": "fail"
            },
            {
              "name": "case_board_semantic_evidence",
              "status": "not_run"
            }
          ]
        },
        "scope": "verification_capability_repair",
        "source": "hierarchical_repair_loop",
        "status": "ready_for_agent_patch",
        "target_modules": [
          "case_multilayer_pipeline",
          "functional_sim"
        ]
      }
    ]
  },
  "schema_version": "spatialaccagent.repair_plan.v0",
  "stage": "repair",
  "status": "needs_repair",
  "verification_status": "fail"
}
</candidate_repair_plan>

<design_team>
{
  "completed_subtasks": 0,
  "decomposer_used_fallback": false,
  "decomposition_source": "deterministic_conditional_router",
  "errors": [],
  "executable_actions": [],
  "reason": "deterministic failure class is unambiguous; the primary repair agent owns the bounded action decision",
  "routing_mode": "conditional",
  "schema_version": "spatialaccagent.conditional_review_summary.v0",
  "stage": "repair",
  "status": "no_split",
  "subtask_count": 0,
  "used_fallback_count": 0
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/sacg_state.json
</source_sacg_state>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "configured_model": "gpt-5.6-sol",
  "endpoint_configured": true,
  "enforce": true,
  "mode": "llm",
  "model": "gpt-5.6-sol",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "xhigh",
  "requested_model_override": "",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

<sacg_memory>
{
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0331",
      "last_observed_at": "2026-07-25T02:38:34+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0341",
      "last_observed_at": "2026-07-24T19:28:08+00:00",
      "observation_count": 7,
      "observed_transition_ids": [
        "transition.0231",
        "transition.0237",
        "transition.0239",
        "transition.0241",
        "transition.0244",
        "transition.0246",
        "transition.0248"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "transition_id": "transition.0231",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0342",
      "last_observed_at": "2026-07-24T19:33:35+00:00",
      "observation_count": 7,
      "observed_transition_ids": [
        "transition.0232",
        "transition.0238",
        "transition.0240",
        "transition.0242",
        "transition.0245",
        "transition.0247",
        "transition.0249"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-24T08:56:30+00:00",
      "transition_id": "transition.0232",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0343",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "observed_transition_ids": [
        "transition.0233"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0344",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "observed_transition_ids": [
        "transition.0233"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0345",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "observed_transition_ids": [
        "transition.0233"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0346",
      "observation_count": 1,
      "observed_transition_ids": [
        "transition.0234"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "transition_id": "transition.0234",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0347",
      "observation_count": 1,
      "observed_transition_ids": [
        "transition.0235"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T17:25:58+00:00",
      "transition_id": "transition.0235",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "debug_layer": "board_axi_ddr_wrapped_system",
  "omitted_unscoped_cross_layer_or_limit_counts": {
    "backtrack_requests": 1,
    "contamination_barriers": 5,
    "failure_lessons": 144,
    "retry_requests": 0,
    "stage_outcomes": 155
  },
  "open_backtrack_requests": [],
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0136",
      "last_observed_at": "2026-07-25T02:38:34+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0140",
      "last_observed_at": "2026-07-24T19:28:08+00:00",
      "observation_count": 7,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0141",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0142",
      "observation_count": 1,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "policy": "Only hierarchy-bound records matching this prompt scope are operational context. Omitted records remain persisted recovery history; sacg_memory_truth separately carries the complete authoritative current blocker set.",
  "recent_failure_lessons": [
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0145",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime ABI release, or board runtime. The directly executed current-scope failure is case_multilayer_pipeline (return code 1): complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding and a hash-verified multilayer harness source closure are absent. board_tb.sv is also missing as a downstream functional-simulation precondition. functional_sim is an unsatisfied aggregate gate, not executed board RTL evidence: VCS, its analyzer, and AXI/deadlock diagnostics are dependency-skipped behind case_multilayer_pipeline and case_axi_ddr_interface. The current discovery pass is not promotion evidence until its exact-wrapper/source-hash lineage is reconciled against active rejected SACG lineages. Certified operator-leaf and elastic connected-single-layer evidence remains reusable; no current trace asserts a named contradiction requiring lower-layer backtrack.",
      "timestamp": "2026-07-24T17:42:03+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0146",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime ABI release, or board runtime. The directly executed current-scope failure is case_multilayer_pipeline (return code 1): complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding and a hash-verified multilayer harness source closure are absent. board_tb.sv is also missing as a downstream functional-simulation precondition. functional_sim is an unsatisfied aggregate gate, not executed board RTL evidence: VCS, its analyzer, and AXI/deadlock diagnostics are dependency-skipped behind case_multilayer_pipeline and case_axi_ddr_interface. The current discovery pass is not promotion evidence until its exact-wrapper/source-hash lineage is reconciled against active rejected SACG lineages. Certified operator-leaf and elastic connected-single-layer evidence remains reusable; no current trace asserts a named contradiction requiring lower-layer backtrack.",
      "timestamp": "2026-07-24T17:53:33+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0147",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime ABI release, or board runtime. The directly executed current-scope failure is case_multilayer_pipeline (return code 1): complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding and a hash-verified multilayer harness source closure are absent. board_tb.sv is also missing as a downstream functional-simulation precondition. functional_sim is an unsatisfied aggregate gate, not executed board RTL evidence: VCS, its analyzer, and AXI/deadlock diagnostics are dependency-skipped behind case_multilayer_pipeline and case_axi_ddr_interface. The current discovery pass is not promotion evidence until its exact-wrapper/source-hash lineage is reconciled against active rejected SACG lineages. Certified operator-leaf and elastic connected-single-layer evidence remains reusable; no current trace asserts a named contradiction requiring lower-layer backtrack.",
      "timestamp": "2026-07-24T18:04:56+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0148",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "stage": "stage7.verification",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists.",
      "timestamp": "2026-07-24T18:33:06+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0149",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists.",
      "timestamp": "2026-07-24T18:38:31+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0150",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists.",
      "timestamp": "2026-07-24T18:49:42+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0151",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists.",
      "timestamp": "2026-07-24T19:28:08+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0152",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "stage": "stage7.verification",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to synthesis, implementation, bitstream, runtime ABI release, or board runtime. The earliest directly executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): complete Transformer-block tensor-to-loader-to-DUT binding for every target layer and a hash-verified multilayer harness source closure are absent. board_tb.sv is also absent as a downstream functional-simulation precondition. functional_sim is failed as an unsatisfied aggregate dependency gate, not executed VCS, RTL, numeric, AXI, DDR, liveness, or output-order evidence. Certified operator-leaf and elastic connected-single-layer evidence remains reusable because no current hash-bound trace contradicts a named lower-layer invariant.",
      "timestamp": "2026-07-25T02:38:34+00:00",
      "verification_scope": "board_axi_ddr_closure",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    }
  ],
  "recent_stage_outcomes": [
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime ABI release, or board runtime. The directly executed current-scope failure is case_multilayer_pipeline (return code 1): complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding and a hash-verified multilayer harness source closure are absent. board_tb.sv is also missing as a downstream functional-simulation precondition. functional_sim is an unsatisfied aggregate gate, not executed board RTL evidence: VCS, its analyzer, and AXI/deadlock diagnostics are dependency-skipped behind case_multilayer_pipeline and case_axi_ddr_interface. The current discovery pass is not promotion evidence until its exact-wrapper/source-hash lineage is reconciled against active rejected SACG lineages. Certified operator-leaf and elastic connected-single-layer evidence remains reusable; no current trace asserts a named contradiction requiring lower-layer backtrack."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0156",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-24T17:42:03+00:00",
      "transition_id": "transition.0237",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime ABI release, or board runtime. The directly executed current-scope failure is case_multilayer_pipeline (return code 1): complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding and a hash-verified multilayer harness source closure are absent. board_tb.sv is also missing as a downstream functional-simulation precondition. functional_sim is an unsatisfied aggregate gate, not executed board RTL evidence: VCS, its analyzer, and AXI/deadlock diagnostics are dependency-skipped behind case_multilayer_pipeline and case_axi_ddr_interface. The current discovery pass is not promotion evidence until its exact-wrapper/source-hash lineage is reconciled against active rejected SACG lineages. Certified operator-leaf and elastic connected-single-layer evidence remains reusable; no current trace asserts a named contradiction requiring lower-layer backtrack."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0157",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-24T17:53:33+00:00",
      "transition_id": "transition.0239",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime ABI release, or board runtime. The directly executed current-scope failure is case_multilayer_pipeline (return code 1): complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding and a hash-verified multilayer harness source closure are absent. board_tb.sv is also missing as a downstream functional-simulation precondition. functional_sim is an unsatisfied aggregate gate, not executed board RTL evidence: VCS, its analyzer, and AXI/deadlock diagnostics are dependency-skipped behind case_multilayer_pipeline and case_axi_ddr_interface. The current discovery pass is not promotion evidence until its exact-wrapper/source-hash lineage is reconciled against active rejected SACG lineages. Certified operator-leaf and elastic connected-single-layer evidence remains reusable; no current trace asserts a named contradiction requiring lower-layer backtrack."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0158",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-24T18:04:56+00:00",
      "transition_id": "transition.0241",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0159",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-07-24T18:33:06+00:00",
      "transition_id": "transition.0243",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0160",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-24T18:38:31+00:00",
      "transition_id": "transition.0244",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0161",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-24T18:49:42+00:00",
      "transition_id": "transition.0246",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to backend synthesis, implementation, bitstream, runtime-ABI release, or board runtime. The authoritative earliest executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): it reports absent complete all-target-layer Transformer-block tensor-to-loader-to-DUT binding coverage and absent hash-verified multilayer harness sources. board_tb.sv is additionally missing as a functional-simulation precondition. functional_sim is a dependency-unsatisfied aggregate, not executed VCS/RTL/AXI/DDR/numeric/liveness evidence: VCS, its analyzer, and deadlock/AXI diagnostics are not_run behind case_multilayer_pipeline and case_axi_ddr_interface. The conditional specialist review agrees with this evidence classification but does not replace the failing tool evidence. Certified operator-leaf and connected single-layer evidence remains reusable; no current hash-bound trace contradicts a named lower-layer invariant. The 10 active same-scope contamination barriers and 4 open same-scope retry requests remain downstream-consumption blockers; retry reconciliation is not ready and no content-addressed passing board-scope candidate exists."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0162",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-24T19:28:08+00:00",
      "transition_id": "transition.0248",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; failed checks: multilayer_real_weight_binding, multilayer_harness_sources",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Stage7 board_axi_ddr_closure is fail-closed and cannot promote to synthesis, implementation, bitstream, runtime ABI release, or board runtime. The earliest directly executed failing current-scope gate is real_tool.case_multilayer_pipeline (returncode=1): complete Transformer-block tensor-to-loader-to-DUT binding for every target layer and a hash-verified multilayer harness source closure are absent. board_tb.sv is also absent as a downstream functional-simulation precondition. functional_sim is failed as an unsatisfied aggregate dependency gate, not executed VCS, RTL, numeric, AXI, DDR, liveness, or output-order evidence. Certified operator-leaf and elastic connected-single-layer evidence remains reusable because no current hash-bound trace contradicts a named lower-layer invariant."
      ],
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "stage_outcome.0163",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-07-25T02:38:34+00:00",
      "transition_id": "transition.0250",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "schema_version": "spatialaccagent.scoped_sacg_memory.v1",
  "source_schema_version": "spatialaccagent.sacg_memory.v0",
  "verification_scope": "board_axi_ddr_closure"
}
</sacg_memory>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 10,
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0329",
      "last_observed_at": "2026-07-25T02:38:34+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0330",
      "last_observed_at": "2026-07-25T02:38:34+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0331",
      "last_observed_at": "2026-07-25T02:38:34+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "observed_transition_ids": [
        "transition.0226",
        "transition.0227",
        "transition.0228",
        "transition.0229",
        "transition.0230",
        "transition.0236",
        "transition.0243",
        "transition.0250"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "status": "active",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "transition_id": "transition.0226",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0341",
      "last_observed_at": "2026-07-24T19:28:08+00:00",
      "observation_count": 7,
      "observed_transition_ids": [
        "transition.0231",
        "transition.0237",
        "transition.0239",
        "transition.0241",
        "transition.0244",
        "transition.0246",
        "transition.0248"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "transition_id": "transition.0231",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "contamination_barrier.0342",
      "last_observed_at": "2026-07-24T19:33:35+00:00",
      "observation_count": 7,
      "observed_transition_ids": [
        "transition.0232",
        "transition.0238",
        "transition.0240",
        "transition.0242",
        "transition.0245",
        "transition.0247",
        "transition.0249"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-24T08:56:30+00:00",
      "transition_id": "transition.0232",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0343",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "observed_transition_ids": [
        "transition.0233"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0344",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "observed_transition_ids": [
        "transition.0233"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0345",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "observed_transition_ids": [
        "transition.0233"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "status": "active",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "transition_id": "transition.0233",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0346",
      "observation_count": 1,
      "observed_transition_ids": [
        "transition.0234"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "transition_id": "transition.0234",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "contamination_barrier.0347",
      "observation_count": 1,
      "observed_transition_ids": [
        "transition.0235"
      ],
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-24T17:25:58+00:00",
      "transition_id": "transition.0235",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "active_contamination_barriers_truncated": false,
  "debug_layer": "board_axi_ddr_wrapped_system",
  "global_persisted_blocker_counts": {
    "active_contamination_barriers": 13,
    "open_backtrack_requests": 1,
    "open_retry_requests": 4
  },
  "omitted_unscoped_or_cross_layer_blocker_counts": {
    "active_contamination_barriers": 3,
    "open_backtrack_requests": 1,
    "open_retry_requests": 0
  },
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 4,
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0136",
      "last_observed_at": "2026-07-25T02:38:34+00:00",
      "observation_count": 8,
      "observed_source_fingerprint_sha256s": [
        "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "ce9d39b08da7ed063e6fe2fda9ee1ec968b4b52961dc64270046e1753b0064b1",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T06:29:03+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_multilayer_pipeline",
        "functional_sim"
      ],
      "id": "retry_request.0140",
      "last_observed_at": "2026-07-24T19:28:08+00:00",
      "observation_count": 7,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T08:50:04+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0141",
      "observation_count": 1,
      "observed_source_fingerprint_sha256s": [
        "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700"
      ],
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "source_fingerprint_sha256": "111d8079db000ebfa17d28351d43d5a2d767529ac19bbb2af521828f6ba61700",
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:18:25+00:00",
      "verification_scope": "board_axi_ddr_closure"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "debug_layer": "board_axi_ddr_wrapped_system",
      "failed_gates": [
        "case_board_interface_discovery",
        "functional_sim"
      ],
      "id": "retry_request.0142",
      "observation_count": 1,
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-24T17:24:59+00:00",
      "verification_scope": "board_axi_ddr_closure"
    }
  ],
  "open_retry_requests_truncated": false,
  "policy": "This is the authoritative current blocker set for the named hierarchy scope. Unscoped and cross-layer blockers remain persisted in SACG and are enforced by their owning layer or downstream promotion gates, but they are not executable blockers for this repair prompt.",
  "schema_version": "spatialaccagent.scoped_sacg_memory_truth.v1",
  "truth_source": "source_sacg_state.memory",
  "verification_scope": "board_axi_ddr_closure"
}
</sacg_memory_truth>

<hierarchical_learning_context>
{
  "debug_layer": "board_axi_ddr_wrapped_system",
  "decision_policy": {
    "accepted_input_handshake_required_before_kernel_lifecycle_start": true,
    "current_output_or_lifecycle_frontier_evidence_required_for_board_liveness_claim": true,
    "current_scope_tools_and_exact_board_wrapper_remain_required": true,
    "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": true,
    "frontier_stall_is_localization_evidence_not_a_root_cause_or_pass_claim": true,
    "independent_prefetch_or_axi_progress_is_not_output_frontier_progress": true,
    "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": true,
    "lower_layer_reopen_requires_current_trace_named_contradiction": true,
    "repeat_repair_class_requires_fresh_intervention_response_evidence": true,
    "resolved_artifact_identity_lessons_are_not_rtl_failures": true,
    "use_only_live_validated_lower_layer_evidence": true
  },
  "kernel_timing_knowledge": [
    {
      "accepted_trace_record_count": 416,
      "all_planned_stages_concurrent_observed": true,
      "all_planned_stages_participate_in_required_overlap": true,
      "all_planned_stages_same_cycle_concurrency_required": false,
      "boundary_order_summary": {
        "all_first_token_order_preserved": true,
        "all_last_token_order_preserved": true,
        "boundary_count": 13,
        "complete_count": 13
      },
      "contract_sha256": "496fc6b3c907d9401a2156dc906f39f7a7ade964fa60f682fff0be5f31b5b393",
      "evidence_schema_version": "spatialaccagent.single_layer_pipeline_overlap_evidence.v3",
      "file_sha256": "8475614f6ff71fd6b7ccb2c80a307fa12ed0ed6517b0eb71ac74b010b19f748f",
      "kind": "connected_kernel_pipeline_timing",
      "lesson": "The connected kernel is an elastic, variable-latency token pipeline. Preserve verified boundary order and required adjacent-stage cross-token overlap; do not diagnose unequal stage durations as a failure merely because all stages do not start or finish on the same cycle.",
      "maximum_concurrent_stage_count": 9,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/d2d2039720d94e9aab7ffb152d15ef57/evidence/single_layer_functional/0095_case_single_layer_functional_single_layer_functional_report.json",
      "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
      "planned_stage_count": 9,
      "required_dependency_overlap_complete": true,
      "required_direct_dependency_overlap_summary": {
        "all_different_token_overlap_observed": true,
        "boundary_count": 9
      },
      "stage_turnover_gaps_are_diagnostic": true,
      "trace_record_count": 416,
      "trace_sha256": "3440370152a8584f86283bcd39924aa04050e9a0694a763ad12accc3242095b1"
    }
  ],
  "resolved_evidence_lessons": [
    {
      "file_sha256": "e5ed97138e1dbecd4fd1ed4cf28508674196e0bf46084e72656d0dbd25006813",
      "kind": "lower_scope_certificate_continuity",
      "lesson": "A higher-scope binding update was proven not to alter certified leaf evidence; do not replay or reopen leaf operators without a current contradictory trace.",
      "live_operator_leaf_file_count": 245,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/b5b9c90c11d5d96e420eddb259419e622e571608abd1e42d2a58d56a36dfed0a/operator_leaf_certificate_scope_continuity.json"
    },
    {
      "file_sha256": "b73f60137fa39f8a598938527be69488287821e4e6f8f0326926ac1543d2bfce",
      "kind": "lower_scope_certificate_continuity",
      "lesson": "A higher-scope binding update was proven not to alter certified leaf evidence; do not replay or reopen leaf operators without a current contradictory trace.",
      "live_operator_leaf_file_count": 245,
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/59e7c1304b51eee277b082f508c70402f44da1eec56b80af5b05f1142304638e/operator_leaf_certificate_scope_continuity.json"
    },
    {
      "bridge_fingerprint_sha256": "507a9946e13853f25266c5c8fa7847fa9618050add8e19c26618881308961430",
      "file_sha256": "0d269796162c045964d9caa52ef7049ad0bd395a6d34e813dc47fb57b25d9021",
      "kind": "lower_layer_certificate_scaffold_bridge",
      "lesson": "The connected-layer scaffold has a live lower-layer certificate bridge; do not regenerate certified leaf testbenches merely to satisfy a legacy scaffold checker.",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/candidates/d2d2039720d94e9aab7ffb152d15ef57/evidence/single_layer_functional/0000_case_tb_scaffold_tb_scaffold.json"
    }
  ],
  "schema_version": "spatialaccagent.hierarchical_learning_context.v1",
  "status": "pass",
  "status_bar_contract": {
    "covers_only_live_validated_lower_layer_certificates": true,
    "does_not_replace_current_scope_tool_results": true,
    "maintainer": "framework_deterministic_hash_bound_projection",
    "not_an_llm_generated_history_summary": true,
    "raw_evidence_remains_retrievable_by_path_and_sha256": true
  },
  "validated_lower_layer_certificates": [
    {
      "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
      "claim": "Every selected operator leaf passed target-model semantic comparison with real target weights, auditable input provenance, and an independent expected output, and may be reused as lower-layer evidence for single-transformer-layer verification.",
      "debug_layer": "operator_leaf_modules",
      "derivation_kind": "lower_scope_continuity_after_higher_scope_binding_update",
      "does_not_claim": [
        "full end-to-end model semantic correctness",
        "single-transformer-layer integration correctness",
        "board AXI/DDR wrapper correctness",
        "backend, bitstream, or board-runtime readiness"
      ],
      "evidence_binding_file_count": 812,
      "evidence_binding_roles": {
        "evidence_artifact": 12,
        "gate_log": 8,
        "input_artifact": 330,
        "lower_scope_certificate_continuity_proof": 9,
        "operator_leaf_continuity_bound_weight_tensor": 12,
        "operator_leaf_continuity_golden_output": 9,
        "operator_leaf_continuity_input_vector": 12,
        "operator_leaf_continuity_materialized_runtime_stream": 1,
        "operator_leaf_continuity_materialized_runtime_stream_source": 4,
        "operator_leaf_continuity_materialized_weight_stream": 6,
        "operator_leaf_continuity_semantic_harness_source": 191,
        "operator_leaf_continuity_semantic_testbench": 9,
        "operator_leaf_continuity_target_model_reference": 1,
        "produced_report": 9,
        "selector_contract": 8,
        "source_file": 191
      },
      "evidence_binding_sha256": "6e6d0ab26664b3af3f894cfcf69c0cd56b4c8a52203232a3f0ea9105347e5c2a",
      "file_sha256": "2bbc6880205155cbc1119882b2503281c2cb43b4b3c0d40a1754acb1e3a20569",
      "level_id": "operator_leaf_functional",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/operator_leaf_promotion_certificate.json",
      "required_gates": [
        "case_real_weight_artifacts",
        "case_target_model_reference",
        "case_semantic_testbench",
        "case_stage_leaf_static",
        "boundary_contract_check",
        "case_leaf_functional",
        "case_leaf_golden_compare",
        "case_operator_leaf_semantic_evidence"
      ],
      "scope": "operator_leaf_closure"
    },
    {
      "artifact_id": "artifact.stage7.single_layer_promotion_certificate",
      "claim": null,
      "debug_layer": "single_transformer_layer_kernel",
      "derivation_kind": null,
      "does_not_claim": [],
      "evidence_binding_file_count": 182,
      "evidence_binding_roles": {
        "evidence_artifact": 7,
        "gate_log": 5,
        "input_artifact": 101,
        "produced_report": 7,
        "selector_contract": 5,
        "source_file": 57
      },
      "evidence_binding_sha256": "aca81fec6b2bbaa488813c14c5631fa3f7b740b32aec2d5116617a301ff20e1f",
      "file_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7",
      "level_id": "single_layer_functional",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/single_layer_promotion_certificate.json",
      "required_gates": [
        "case_tb_scaffold",
        "single_transformer_layer",
        "case_single_layer_functional",
        "case_single_layer_golden_compare",
        "case_single_layer_semantic_evidence"
      ],
      "scope": "single_layer_closure"
    }
  ],
  "verification_scope": "board_axi_ddr_closure"
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

<agent_status_bar>
{
  "current_evidence_frontier": {},
  "current_scope": {
    "debug_layer": "board_axi_ddr_wrapped_system",
    "verification_scope": "board_axi_ddr_closure"
  },
  "current_scope_blocker_classes": {
    "active_contamination_barriers": {
      "class_count": 6,
      "classes": [
        {
          "failed_gates": [
            "case_multilayer_pipeline",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage7.verification_result",
            "artifact.stage7.real_tool_results",
            "artifact.stage7.debug_closure"
          ],
          "reason": "one or more framework static checks failed",
          "record_count": 3
        },
        {
          "failed_gates": [
            "case_multilayer_pipeline",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage8.repair_plan"
          ],
          "reason": "repair actions are required before promotion",
          "record_count": 1
        },
        {
          "failed_gates": [
            "case_multilayer_pipeline",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage8.repair_execution_report"
          ],
          "reason": "one or more repair execution steps failed",
          "record_count": 1
        },
        {
          "failed_gates": [
            "case_board_interface_discovery",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage7.verification_result",
            "artifact.stage7.real_tool_results",
            "artifact.stage7.debug_closure"
          ],
          "reason": "one or more framework static checks failed",
          "record_count": 3
        },
        {
          "failed_gates": [
            "case_board_interface_discovery",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage8.repair_plan"
          ],
          "reason": "repair actions are required before promotion",
          "record_count": 1
        },
        {
          "failed_gates": [
            "case_board_interface_discovery",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage8.repair_execution_report"
          ],
          "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
          "record_count": 1
        }
      ],
      "truncated": false
    },
    "open_backtrack_requests": {
      "class_count": 0,
      "classes": [],
      "truncated": false
    },
    "open_retry_requests": {
      "class_count": 4,
      "classes": [
        {
          "failed_gates": [
            "case_multilayer_pipeline",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage7.verification_result"
          ],
          "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
          "record_count": 1,
          "stage": "stage7.verification",
          "target_stage": "stage7.verification"
        },
        {
          "failed_gates": [
            "case_multilayer_pipeline",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage8.repair_plan"
          ],
          "reason": "Bounded repair actions must be completed before verification can be promoted",
          "record_count": 1,
          "stage": "stage8.repair",
          "target_stage": "stage7.verification"
        },
        {
          "failed_gates": [
            "case_board_interface_discovery",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage7.verification_result"
          ],
          "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
          "record_count": 1,
          "stage": "stage7.verification",
          "target_stage": "stage7.verification"
        },
        {
          "failed_gates": [
            "case_board_interface_discovery",
            "functional_sim"
          ],
          "protected_artifact_ids": [
            "artifact.stage8.repair_plan"
          ],
          "reason": "Bounded repair actions must be completed before verification can be promoted",
          "record_count": 1,
          "stage": "stage8.repair",
          "target_stage": "stage7.verification"
        }
      ],
      "truncated": false
    }
  },
  "current_scope_blocker_counts": {
    "active_contamination_barrier_count": 10,
    "open_backtrack_request_count": 0,
    "open_retry_request_count": 4
  },
  "decision_policy": {
    "accepted_input_handshake_required_before_kernel_lifecycle_start": true,
    "current_output_or_lifecycle_frontier_evidence_required_for_board_liveness_claim": true,
    "current_scope_tools_and_exact_board_wrapper_remain_required": true,
    "do_not_repeat_certified_lower_layer_tools_or_prompt_analysis": true,
    "frontier_stall_is_localization_evidence_not_a_root_cause_or_pass_claim": true,
    "independent_prefetch_or_axi_progress_is_not_output_frontier_progress": true,
    "lower_layer_pass_does_not_claim_board_axi_ddr_or_backend_readiness": true,
    "lower_layer_reopen_requires_current_trace_named_contradiction": true,
    "repeat_repair_class_requires_fresh_intervention_response_evidence": true,
    "resolved_artifact_identity_lessons_are_not_rtl_failures": true,
    "use_only_live_validated_lower_layer_evidence": true
  },
  "maintainer": "framework_deterministic_current_state_projection",
  "raw_evidence_policy": "This status bar is current-state metadata only. Raw SACG/CCTG records, artifacts, and real tool output remain authoritative for detailed reasoning.",
  "schema_version": "spatialaccagent.stage_agent_status_bar.v1",
  "source_sacg_state": {
    "loaded": true,
    "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/sacg_state.json",
    "sha256": "2cc2b4b3b34a059d7bee8c409bd70962929ab03dd969a4339b16e521d246012b"
  },
  "validated_lower_layer": {
    "certificate_count": 2,
    "certificate_identities": [
      {
        "artifact_id": "artifact.stage7.operator_leaf_promotion_certificate",
        "claim": "Every selected operator leaf passed target-model semantic comparison with real target weights, auditable input provenance, and an independent expected output, and may be reused as lower-layer evidence for single-transformer-layer verificati...<len=243>",
        "debug_layer": "operator_leaf_modules",
        "file_sha256": "2bbc6880205155cbc1119882b2503281c2cb43b4b3c0d40a1754acb1e3a20569",
        "level_id": "operator_leaf_functional",
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/operator_leaf_promotion_certificate.json",
        "scope": "operator_leaf_closure"
      },
      {
        "artifact_id": "artifact.stage7.single_layer_promotion_certificate",
        "debug_layer": "single_transformer_layer_kernel",
        "file_sha256": "44d3689d835f165fd30e794aeec2dabf648d1d65d17a24a53d3a6aac6e3854e7",
        "level_id": "single_layer_functional",
        "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/certificates/single_layer_promotion_certificate.json",
        "scope": "single_layer_closure"
      }
    ],
    "kernel_timing_knowledge_count": 1,
    "resolved_evidence_lesson_count": 3,
    "status": "pass"
  }
}
</agent_status_bar>

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
