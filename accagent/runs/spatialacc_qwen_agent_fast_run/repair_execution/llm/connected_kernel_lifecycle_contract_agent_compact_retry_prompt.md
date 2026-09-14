<agent>
connected_kernel_lifecycle_contract_agent_compact_retry
</agent>

<task>
Produce the missing static connected-kernel lifecycle design contract from the hash-bound current-run authority. Specify reload/rearm and atomic external bank ownership semantics needed by the board shell. This is a design contract only: dynamic execution evidence remains pending until the generated shell runs.
</task>

<rules>
1. This is an evidence-preserving compact retry after transient provider failures or oversized prompt transport failure.
2. Use only the compact inputs and named constraints. The compact inputs preserve original evidence by path, sha256, schema/status fields, interface summaries, module headers, and source/compile indexes.
3. If the output schema requires file_edits, return complete file contents, never snippets, prose patches, ellipses, or instructions for a human to finish.
4. For functional verification, random generation may create only the input stimulus. Expected output must be target-model inference using the same checkpoint and input; never accept random or RTL-derived golden data.
5. Do not infer DUT real-weight consumption from file existence. Require complete-scope tensor hashes, a bound loader/harness, and executed evidence.
6. If the current-run policy omits atol, rtol, or max_mismatch_fraction, accept the frozen framework loose defaults recorded in numeric_comparison_resolution. This initial resolution is authorized; never derive or loosen it from DUT output.
7. Preserve the numeric policy, comparison tolerance, checkpoint hash, stimulus hash, and expected-output hash throughout repair.
8. Board-level acceptance requires source-hash identity with the exact user sample-project wrapper; a simplified wrapper is not equivalent.
9. For board integration, exact simulation behavior is preserved by the hash-bound source files and compile authority; do not replace them with a behavioral or idealized model.
10. Compact JSON may use lossless columnar indexes and JSON-pointer $ref objects. Resolve column names, path_prefixes, views, and refs before reasoning; expand aliases and refs to real absolute paths in file_edits.
11. If compact inputs include checker_results, parameter_bindings, template_source_checks, attention_semantics, or cross_layer_trace, treat those fields as supplied evidence.
12. If compact inputs include candidate_verification_artifact_contract, candidate_verification_plan, retry_reconciliation_contract, or design_team, treat their visible status, summary, policy, node counts, error lists, and checker summaries as supplied Stage6 evidence; do not claim the evidence is absent merely because compact retry omitted full nested details.
13. If compact inputs include stage_gate_policy, report only current-stage blockers in risks and move later-stage obligations to proposed_actions.
14. Return conservative review findings; mark evidence as not_run only when the relevant field is absent from compact inputs.
15. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible.
16. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name>; do not invent free-form tool roles such as verification_planner or tool_runner.
17. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
18. Return one JSON object only.
</rules>

<stage>
repair_execution
</stage>

<agent>
connected_kernel_lifecycle_contract_agent
</agent>

<compact_inputs>
{"_more_keys":3,"agent":"connected_kernel_lifecycle_contract_agent","source_sacg_state":"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json","stage":"repair_execution"}
</compact_inputs>

<action_grounding_registry>
{"acceptance_checkers":["sacg_static_check","task_card_check","model_config_check","numeric_policy_check","template_coverage_check","parameter_binding_static_check","code_generation_manifest_static_check","stream_plan_check","memory_runtime_plan_check","boundary_contract_check","failure_localization_check","targeted_replay_check","causal_repair_context_check","template_binding_static_check","repair_boundary_check","verification_plan_static_check","tool_protocol_check","human_boundary_check","hierarchical_verification_plan_check","verification_artifact_contract_check","sacg_reference_check","case_stage_leaf_static","boundary_contract_check","case_leaf_functional","case_leaf_golden_compare","case_single_transformer_layer","case_single_layer_functional","case_single_layer_golden_compare","single_transformer_layer","case_multilayer_pipeline","case_multilayer_functional","case_pipeline_deadlock_check","case_real_weight_artifacts","case_target_model_reference","case_semantic_testbench","case_operator_leaf_semantic_evidence","case_single_layer_semantic_evidence","case_board_semantic_evidence","real_weight_semantic_evidence_check","case_tb_scaffold","case_board_interface_discovery","case_axi_ddr_interface","case_axi_protocol_check","case_ddr_image_roundtrip","case_runtime_abi_check","case_runtime_bitstream","board_runtime","functional_sim","deadlock_watchdog","data_order_trace_check","transfer_count_check","addr_map_check","numeric_compare","artifact_hash_check","codegen_compile_gate_check","codegen_contract_check","codegen_package_static_check","verification_artifact_contract_check","required_real_tool_evidence_check","real_tool.case_real_weight_artifacts","real_tool.boundary_contract_check","real_tool.case_leaf_functional","real_tool.case_leaf_golden_compare","real_tool.case_tb_scaffold","real_tool.case_single_transformer_layer","real_tool.case_single_layer_functional","real_tool.case_single_layer_golden_compare","real_tool.case_multilayer_functional","real_tool.case_pipeline_deadlock_check","real_tool.case_vcs_functional_sim","real_tool.case_verilator_functional_sim","real_tool.case_deadlock_axi_check","real_tool.case_board_interface_discovery","real_tool.case_axi_ddr_interface","real_tool.case_axi_protocol_check","real_tool.case_ddr_image_roundtrip","real_tool.case_vivado_synthesis","real_tool.case_vivado_synthesis_report_check","real_tool.case_vivado_implementation","real_tool.case_vivado_implementation_report_check","real_tool.case_board_shell_wrapper_generate","real_tool.case_runtime_abi_check","real_tool.case_runtime_bitstream","real_tool.app_shell_target_discovery_contract","real_tool.app_shell_target_hint_synthesis","real_tool.app_shell_target_discovery_after_hint","real_tool.board_runtime","real_tool.app_shell_runtime_bitstream","implementation_package_static","timing_resource_check","deployment_board_check","output_validity_check","targeted_failed_checker_rerun","verification_action_audit_check","llm_io_quality_check","llm_semantic_extraction_check","no_static_keyword_semantic_matching_check","sacg_memory_check","stage_retry_request_check","stage_backtrack_request_check","stage_artifact_trust_barrier_check","backend_app_shell_integration_contract_static_check","backend_app_shell_target_discovery_check","backend_app_shell_target_hint_synthesis_check","backend_bounded_recovery_action_check","backend_recovery_approval_ingest_check"],"policy":"Executable actions should use these tool/checker names when applicable. If a required capability is missing, name it as planned_tool.<short_name> and make the rationale say that multi-agent system capability implementation is required.","schema_version":"spatialaccagent.action_grounding_registry.v0","tool_roles":["sacg_validate","sacg_static_check","task_card_check","model_config_check","numeric_policy_check","template_coverage_check","template_binding_static_check","parameter_binding_static_check","code_generation_manifest_static_check","stream_plan_check","memory_runtime_plan_check","repair_boundary_check","boundary_contract_generate","failure_slice_localization","boundary_trace_rerun","targeted_replay","causal_repair_context_pack","verification_plan_static_check","tool_protocol_check","human_boundary_check","hierarchical_verification_plan_check","verification_artifact_contract_check","sacg_reference_check","codegen_compile_gate","codegen_contract_check","codegen_package_static_check","verification_artifact_contract_check","required_real_tool_evidence_check","real_tool_evidence_check","case_real_weight_artifacts","case_target_model_reference","case_semantic_testbench","case_operator_leaf_semantic_evidence","case_single_layer_semantic_evidence","case_board_semantic_evidence","case_stage_leaf_static","boundary_contract_check","case_leaf_functional","case_leaf_golden_compare","case_single_transformer_layer","case_single_layer_functional","case_single_layer_golden_compare","single_transformer_layer","case_multilayer_pipeline","case_multilayer_functional","case_pipeline_deadlock_check","case_tb_scaffold","case_vcs_functional_sim","functional_sim","functional_sim_contract_check","case_verilator_functional_sim","case_weight_manifest_generate","case_tb_scaffold_generate","case_vcs_evidence_analyzer","deadlock_watchdog","data_order_trace_check","transfer_count_check","addr_map_check","numeric_compare","artifact_hash_check","case_deadlock_axi_check","case_board_interface_discovery","case_axi_ddr_interface","case_axi_protocol_check","case_ddr_image_roundtrip","case_vivado_synthesis","case_vivado_synthesis_report_check","case_vivado_implementation","case_vivado_implementation_report_check","case_board_shell_wrapper_generate","case_runtime_abi_check","case_runtime_bitstream","app_shell_target_discovery_contract","app_shell_target_hint_synthesis","app_shell_target_discovery_after_hint","backend_bounded_recovery_action","backend_recovery_approval_ingest","implementation_package_static","timing_resource_check","deployment_board_check","board_runtime","output_validity_check","targeted_failed_checker_rerun","bounded_template_repair","pipeline_repair","memory_runtime_repair","architecture_review","team_aggregate","verification_action_audit","llm_io_quality_check","llm_semantic_extraction","no_static_keyword_semantic_matching","sacg_memory_update","stage_retry_request","stage_backtrack_request","stage_artifact_trust_barrier","app_shell_runtime_bitstream"]}
</action_grounding_registry>

<action_contract_examples>
[{"acceptance_checkers":["case_real_weight_artifacts","case_target_model_reference","case_semantic_testbench"],"action_type":"verification_evidence_preparation","consumes":["artifact.input.model_config","artifact.input.numeric_policy","artifact.stage3.pipeline_plan","current case-adapter target checkpoint","generated/memory/dut_weight_binding_manifest.json"],"id":"example.prepare_real_model_semantic_verification","on_failure":"treat missing reference, explicit tolerance, semantic harness, or DUT weight consumption as a verification-capability/code-generation blocker; do not run a legacy fallback test or promote the layer.","produces":["verification/real_weights/full_tensor_catalog.json","verification/model_reference/reference_manifest.json","verification/semantic_testbench/semantic_testbench_manifest.json","verification/semantic_testbench/dut_weight_binding_requirements.json"],"rationale":"Build immutable semantic evidence from the current case adapter before any hardware correctness claim.","requires_approval":false,"stage":"verification","tool_roles":["case_weight_manifest_generate","case_target_model_reference","case_semantic_testbench"]},{"acceptance_checkers":["functional_sim","data_order_trace_check","deadlock_watchdog","real_weight_semantic_evidence_check"],"action_type":"real_tool_execution","consumes":["artifact.stage6.verification_artifact_contract","verification/model_reference/reference_manifest.json","verification/semantic_testbench/semantic_testbench_manifest.json","generated/memory/dut_weight_binding_manifest.json","verification/board_simulation/board_simulation_manifest.json"],"id":"example.run_real_functional_sim","on_failure":"route simulator evidence to Stage8 repair with the violated SACG constraints; do not proceed to Vivado.","produces":["verification/vcs/case_functional_sim.log","verification/board_simulation/rtl_output.memh","verification/debug_closure/boundary_trace.json","verification/case_diagnostics/vcs_functional_diagnosis.json","verification/semantic_evidence/board_axi_ddr.json"],"rationale":"Run a real simulator after static hierarchy and artifact gates pass.","requires_approval":false,"stage":"verification","tool_roles":["case_vcs_functional_sim","case_vcs_evidence_analyzer","case_board_semantic_evidence"]},{"acceptance_checkers":["planned_checker.formal_axi_property_check"],"action_type":"system_capability_gap","consumes":["artifact.stage6.verification_plan"],"id":"example.declare_missing_capability","on_failure":"block promotion until the planned checker is implemented or an approved equivalent exists.","produces":["planned checker implementation task"],"rationale":"The design team needs a checker not yet implemented by the multi-agent system.","requires_approval":true,"stage":"verification","tool_roles":["planned_tool.formal_axi_property_runner"]},{"acceptance_checkers":["backend_app_shell_target_hint_synthesis_check","backend_bounded_recovery_action_check","human_boundary_check"],"action_type":"bounded_recovery","consumes":["artifact.stage9.app_shell_integration_contract","artifact.stage9.app_shell_target_selection_decision","backend_board/case_diagnostics/app_shell_target_discovery_after_hint.json"],"id":"example.ambiguous_backend_target_recovery","on_failure":"keep runtime bitstream and board runtime blocked until the target contract has cited evidence or explicit approval","produces":["artifact.stage9.backend_bounded_recovery_actions"],"rationale":"Real backend evidence produced multiple plausible shell integration targets, so the design team must not guess.","requires_approval":true,"stage":"backend_board","tool_roles":["app_shell_target_hint_synthesis","app_shell_target_discovery_after_hint"]}]
</action_contract_examples>

<output_schema>
{
  "additionalProperties": false,
  "properties": {
    "agent": {
      "enum": [
        "connected_kernel_lifecycle_contract_agent"
      ],
      "type": "string"
    },
    "blocked_reasons": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "completion": {
      "additionalProperties": false,
      "properties": {
        "expected_accepted_beats_per_layer": {
          "type": "integer"
        },
        "requires_activation_ddr_commit_before_reset": {
          "type": "boolean"
        },
        "requires_output_valid_and_ready": {
          "type": "boolean"
        },
        "strategy": {
          "enum": [
            "accepted_output_transfer_count"
          ],
          "type": "string"
        },
        "target_layer_count": {
          "type": "integer"
        }
      },
      "required": [
        "strategy",
        "expected_accepted_beats_per_layer",
        "target_layer_count",
        "requires_output_valid_and_ready",
        "requires_activation_ddr_commit_before_reset"
      ],
      "type": "object"
    },
    "dynamic_validation": {
      "additionalProperties": false,
      "properties": {
        "hardware_pass_claimed": {
          "enum": [
            false
          ],
          "type": "boolean"
        },
        "obligations": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "acceptance": {
                "type": "string"
              },
              "obligation_id": {
                "enum": [
                  "multi_invocation_real_tool_execution",
                  "per_layer_loader_trace",
                  "per_layer_completion_trace",
                  "private_reset_external_state_isolation_trace",
                  "full_layer_exact_board_vcs_execution"
                ],
                "type": "string"
              },
              "status": {
                "enum": [
                  "pending"
                ],
                "type": "string"
              }
            },
            "required": [
              "obligation_id",
              "status",
              "acceptance"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "status": {
          "enum": [
            "pending"
          ],
          "type": "string"
        }
      },
      "required": [
        "status",
        "hardware_pass_claimed",
        "obligations"
      ],
      "type": "object"
    },
    "kernel": {
      "additionalProperties": false,
      "properties": {
        "clock_port": {
          "type": "string"
        },
        "input_ready_port": {
          "type": "string"
        },
        "input_valid_port": {
          "type": "string"
        },
        "output_data_port": {
          "type": "string"
        },
        "output_data_width_bits": {
          "type": "integer"
        },
        "output_ready_port": {
          "type": "string"
        },
        "output_valid_port": {
          "type": "string"
        },
        "reset_port": {
          "type": "string"
        },
        "runtime_loader": {
          "type": "object"
        },
        "start_port": {
          "type": "string"
        },
        "top_module": {
          "type": "string"
        },
        "weight_loader": {
          "type": "object"
        }
      },
      "required": [
        "top_module",
        "clock_port",
        "reset_port",
        "start_port",
        "input_valid_port",
        "input_ready_port",
        "output_valid_port",
        "output_ready_port",
        "output_data_port",
        "output_data_width_bits",
        "weight_loader",
        "runtime_loader"
      ],
      "type": "object"
    },
    "private_reset": {
      "additionalProperties": false,
      "properties": {
        "activation_and_weight_bank_state_preserved": {
          "type": "boolean"
        },
        "external_axi_ddr_state_preserved": {
          "type": "boolean"
        },
        "external_scheduler_state_preserved": {
          "type": "boolean"
        },
        "scope": {
          "enum": [
            "connected_kernel_instance_only"
          ],
          "type": "string"
        },
        "source_evidence": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "modules": {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              "reset_behavior": {
                "type": "string"
              },
              "source_id": {
                "type": "string"
              },
              "source_sha256": {
                "type": "string"
              }
            },
            "required": [
              "source_id",
              "source_sha256",
              "modules",
              "reset_behavior"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "strategy": {
          "enum": [
            "instance_private_reset"
          ],
          "type": "string"
        }
      },
      "required": [
        "strategy",
        "scope",
        "external_scheduler_state_preserved",
        "external_axi_ddr_state_preserved",
        "activation_and_weight_bank_state_preserved",
        "source_evidence"
      ],
      "type": "object"
    },
    "reload": {
      "additionalProperties": false,
      "properties": {
        "complete_before_start": {
          "type": "boolean"
        },
        "runtime_word_count": {
          "type": "integer"
        },
        "sequence": {
          "items": {
            "enum": [
              "wait_for_all_accepted_outputs",
              "wait_for_activation_ddr_commit",
              "assert_kernel_private_reset",
              "deassert_kernel_private_reset",
              "load_complete_layer_weights",
              "load_complete_layer_runtime",
              "observe_both_loader_completions",
              "start_kernel_invocation"
            ],
            "type": "string"
          },
          "type": "array"
        },
        "weight_word_count": {
          "type": "integer"
        }
      },
      "required": [
        "weight_word_count",
        "runtime_word_count",
        "complete_before_start",
        "sequence"
      ],
      "type": "object"
    },
    "schema_version": {
      "enum": [
        "spatialaccagent.connected_kernel_lifecycle_design_contract.v1"
      ],
      "type": "string"
    },
    "stage": {
      "enum": [
        "repair_execution"
      ],
      "type": "string"
    },
    "status": {
      "enum": [
        "design_feasible",
        "blocked"
      ],
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
    "blocked_reasons",
    "kernel",
    "completion",
    "private_reset",
    "reload",
    "dynamic_validation"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
