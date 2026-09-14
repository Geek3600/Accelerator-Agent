<agent>
exact_board_memory_runtime_contract_agent_compact_retry
</agent>

<task>
Act as the single FPGA board memory/runtime architect for exact-board layer-3 closure. Interpret the complete current target-model, canonical weight-loader, and arbitrary physical board ABI semantically. Return one evidence-bound runtime plan; do not emit RTL, pack weights, run tools, or create files.
</task>

<rules>
1. This is an evidence-preserving compact retry after transient provider failures or oversized prompt transport failure.
2. Use only the compact inputs and named constraints. The compact inputs preserve original evidence by path, sha256, schema/status fields, interface summaries, module headers, and source/compile indexes.
3. If the output schema requires file_edits, return complete content for create/replace edits, or a hash-bound operation=replace_text with content='' and exact unique old_text/new_text anchors for an existing non-JSON source. The framework materializes anchored edits into the complete final file and rejects any missing, ambiguous, overlapping, or stale anchor. Never return ellipses, prose patches, or instructions for a human to finish.
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
15. All original task-specific rules below remain authoritative after compaction.
16. Return status=ready only when every required field is complete and copied or derived from current-run evidence; otherwise return status=blocked without inventing facts.
17. workload_image.image_plan must be the exact spatialaccagent.board_workload_image_plan.v1 object consumed directly by the deterministic packer. Copy required_input_bindings and required_image_plan_identity exactly.
18. Treat full_layer_runtime_capture_contract, full_runtime_image_manifest, and certified_single_layer_binding as framework-owned immutable evidence. Never copy those framework-owned objects into fields that the schema marks for later framework materialization.
19. When the connected runtime stream is non-empty, runtime_constants.enabled must be true and must bind its exact contract hash, certified runtime-loader ABI/routes, one complete-before-kernel-start load for every target layer, and the supplied runtime image segment for that layer. Reuse one segment across layers only when full_runtime_image_manifest explicitly proves byte identity.
20. Allocate a distinct non-overlapping runtime-constant region large enough for the materialized image and emit exactly one runtime_load_start and runtime_load_complete trace role in addition to all existing required roles.
21. The stage memory layout is a proposal, not layer-3 authority. When its weight bank is smaller than the certified connected stream, derive the minimum aligned capacity from connected_weight_stream_contract word_count/word_bits; this corrects a derived capacity contradiction and does not authorize truncation.
22. Every numeric address, size, alignment, capacity, and physical configuration value must use an artifact_ref or a recomputable derived_expression. Do not use opaque literal constants or self-referential workload_image sources.
23. Repair prior_candidate_plan against every prior_validation_feedback error while preserving its already valid mappings. A derived expression supports only integer names, +, -, *, //, %, <<, >>, &, | and unary +/-; function calls such as min/max/align_up are forbidden. Every symbol used by one expression must have a local ref to a directly integer-valued JSON pointer. artifact_ref must point directly to an integer leaf, never prose, a policy string, or an object.
24. Match every discovered physical configuration field exactly by field_id, fact_port_id, register, bit offset, width, access, and reset value regardless of its name. Do not select fields through keywords.
25. Preserve the exact discovered configure/start/observe_completion/clear_completion sequence and the discovered clock domain. Do not infer a generic ready/valid control protocol.
26. Cover every target layer with one reusable connected kernel, two weight banks, inactive-bank next-layer prefetch overlapped with current compute, atomic ownership switch, two activation banks with inter-layer ping-pong, first-input load, and final-layer-only writeback.
27. Define non-overlapping aligned regions within the exact discovered AXI address width and data width, and bind exactly one trace point for each required runtime event role.
28. Do not use values, paths, commands, module names, addresses, or layer counts from an earlier OPT, PyJM, Qwen, or other accelerator case unless they are present in the supplied current-run authority.
29. Return one JSON object only.
30. Ground executable_actions in action_grounding_registry. Use exact listed tool_roles and acceptance_checkers whenever possible.
31. If a missing capability is required, name it planned_tool.<short_name> or planned_checker.<short_name>; do not invent free-form tool roles such as verification_planner or tool_runner.
32. Before returning, self-check every executable action: each tool_roles entry must be listed in action_grounding_registry.tool_roles or start with planned_tool.; each acceptance_checkers entry must be listed in action_grounding_registry.acceptance_checkers or start with planned_checker.
33. Return one JSON object only.
</rules>

<stage>
repair_execution
</stage>

<agent>
exact_board_memory_runtime_contract_agent
</agent>

<compact_inputs>
{"_more_keys":1,"agent":"exact_board_memory_runtime_contract_agent","source_sacg_state":"/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json","stage":"repair_execution"}
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
    "activation_ping_pong": {
      "additionalProperties": false,
      "properties": {
        "bank_count": {
          "enum": [
            2
          ],
          "type": "integer"
        },
        "banks": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "bank_id": {
                "type": "string"
              },
              "capacity_bytes": {
                "additionalProperties": false,
                "properties": {
                  "resolved_value": {
                    "type": "integer"
                  },
                  "source": {
                    "oneOf": [
                      {
                        "additionalProperties": false,
                        "properties": {
                          "artifact": {
                            "enum": [
                              "catalog",
                              "identity",
                              "model",
                              "requirements",
                              "stage_memory_layout",
                              "workload_image"
                            ],
                            "type": "string"
                          },
                          "kind": {
                            "enum": [
                              "artifact_ref"
                            ],
                            "type": "string"
                          },
                          "path": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "kind",
                          "artifact",
                          "path"
                        ],
                        "type": "object"
                      },
                      {
                        "additionalProperties": false,
                        "properties": {
                          "expression": {
                            "type": "string"
                          },
                          "kind": {
                            "enum": [
                              "derived_expression"
                            ],
                            "type": "string"
                          },
                          "refs": {
                            "items": {
                              "additionalProperties": false,
                              "properties": {
                                "artifact": {
                                  "enum": [
                                    "catalog",
                                    "identity",
                                    "model",
                                    "requirements",
                                    "stage_memory_layout",
                                    "workload_image"
                                  ],
                                  "type": "string"
                                },
                                "path": {
                                  "type": "string"
                                },
                                "symbol": {
                                  "type": "string"
                                }
                              },
                              "required": [
                                "symbol",
                                "artifact",
                                "path"
                              ],
                              "type": "object"
                            },
                            "minItems": 1,
                            "type": "array"
                          }
                        },
                        "required": [
                          "kind",
                          "expression",
                          "refs"
                        ],
                        "type": "object"
                      }
                    ]
                  }
                },
                "required": [
                  "resolved_value",
                  "source"
                ],
                "type": "object"
              },
              "region_id": {
                "type": "string"
              }
            },
            "required": [
              "bank_id",
              "region_id",
              "capacity_bytes"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "input_load": {
          "additionalProperties": false,
          "properties": {
            "complete_before_start": {
              "type": "boolean"
            },
            "destination_bank_id": {
              "type": "string"
            },
            "source_region_id": {
              "type": "string"
            }
          },
          "required": [
            "source_region_id",
            "destination_bank_id",
            "complete_before_start"
          ],
          "type": "object"
        },
        "layer_schedule": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "external_writeback": {
                "type": "boolean"
              },
              "layer_index": {
                "type": "integer"
              },
              "read_bank_id": {
                "type": "string"
              },
              "write_bank_id": {
                "type": "string"
              }
            },
            "required": [
              "layer_index",
              "read_bank_id",
              "write_bank_id",
              "external_writeback"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "required_activation_bytes": {
          "additionalProperties": false,
          "properties": {
            "resolved_value": {
              "type": "integer"
            },
            "source": {
              "oneOf": [
                {
                  "additionalProperties": false,
                  "properties": {
                    "artifact": {
                      "enum": [
                        "catalog",
                        "identity",
                        "model",
                        "requirements",
                        "stage_memory_layout",
                        "workload_image"
                      ],
                      "type": "string"
                    },
                    "kind": {
                      "enum": [
                        "artifact_ref"
                      ],
                      "type": "string"
                    },
                    "path": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "kind",
                    "artifact",
                    "path"
                  ],
                  "type": "object"
                },
                {
                  "additionalProperties": false,
                  "properties": {
                    "expression": {
                      "type": "string"
                    },
                    "kind": {
                      "enum": [
                        "derived_expression"
                      ],
                      "type": "string"
                    },
                    "refs": {
                      "items": {
                        "additionalProperties": false,
                        "properties": {
                          "artifact": {
                            "enum": [
                              "catalog",
                              "identity",
                              "model",
                              "requirements",
                              "stage_memory_layout",
                              "workload_image"
                            ],
                            "type": "string"
                          },
                          "path": {
                            "type": "string"
                          },
                          "symbol": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "symbol",
                          "artifact",
                          "path"
                        ],
                        "type": "object"
                      },
                      "minItems": 1,
                      "type": "array"
                    }
                  },
                  "required": [
                    "kind",
                    "expression",
                    "refs"
                  ],
                  "type": "object"
                }
              ]
            }
          },
          "required": [
            "resolved_value",
            "source"
          ],
          "type": "object"
        },
        "trace_point_ids": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "bank_count",
        "required_activation_bytes",
        "banks",
        "input_load",
        "layer_schedule",
        "trace_point_ids"
      ],
      "type": "object"
    },
    "agent": {
      "enum": [
        "exact_board_memory_runtime_contract_agent"
      ],
      "type": "string"
    },
    "blocked_reasons": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "final_writeback": {
      "additionalProperties": false,
      "properties": {
        "destination_region_id": {
          "type": "string"
        },
        "enabled": {
          "type": "boolean"
        },
        "layer_index": {
          "type": "integer"
        },
        "only_final_layer": {
          "type": "boolean"
        },
        "source_activation_bank_id": {
          "type": "string"
        },
        "starts_after_final_layer_completion": {
          "type": "boolean"
        },
        "trace_point_ids": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "enabled",
        "only_final_layer",
        "layer_index",
        "source_activation_bank_id",
        "destination_region_id",
        "starts_after_final_layer_completion",
        "trace_point_ids"
      ],
      "type": "object"
    },
    "input_bindings": {
      "additionalProperties": false,
      "properties": {
        "axi_interfaces_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "compute_slot_abi_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "control_abi_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "dut_weight_requirements_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "exact_board_identity_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "stage_memory_layout_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "target_model_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "timing_contract_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        },
        "transformer_block_catalog_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": "string"
        }
      },
      "required": [
        "exact_board_identity_sha256",
        "target_model_sha256",
        "transformer_block_catalog_sha256",
        "dut_weight_requirements_sha256",
        "stage_memory_layout_sha256",
        "compute_slot_abi_sha256",
        "control_abi_sha256",
        "timing_contract_sha256",
        "axi_interfaces_sha256"
      ],
      "type": "object"
    },
    "memory_regions": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "address_width_bits": {
            "type": "integer"
          },
          "alignment_bytes": {
            "additionalProperties": false,
            "properties": {
              "resolved_value": {
                "type": "integer"
              },
              "source": {
                "oneOf": [
                  {
                    "additionalProperties": false,
                    "properties": {
                      "artifact": {
                        "enum": [
                          "catalog",
                          "identity",
                          "model",
                          "requirements",
                          "stage_memory_layout",
                          "workload_image"
                        ],
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "artifact_ref"
                        ],
                        "type": "string"
                      },
                      "path": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "kind",
                      "artifact",
                      "path"
                    ],
                    "type": "object"
                  },
                  {
                    "additionalProperties": false,
                    "properties": {
                      "expression": {
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "derived_expression"
                        ],
                        "type": "string"
                      },
                      "refs": {
                        "items": {
                          "additionalProperties": false,
                          "properties": {
                            "artifact": {
                              "enum": [
                                "catalog",
                                "identity",
                                "model",
                                "requirements",
                                "stage_memory_layout",
                                "workload_image"
                              ],
                              "type": "string"
                            },
                            "path": {
                              "type": "string"
                            },
                            "symbol": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "symbol",
                            "artifact",
                            "path"
                          ],
                          "type": "object"
                        },
                        "minItems": 1,
                        "type": "array"
                      }
                    },
                    "required": [
                      "kind",
                      "expression",
                      "refs"
                    ],
                    "type": "object"
                  }
                ]
              }
            },
            "required": [
              "resolved_value",
              "source"
            ],
            "type": "object"
          },
          "axi_interface_ref": {
            "type": "string"
          },
          "base_address": {
            "additionalProperties": false,
            "properties": {
              "resolved_value": {
                "type": "integer"
              },
              "source": {
                "oneOf": [
                  {
                    "additionalProperties": false,
                    "properties": {
                      "artifact": {
                        "enum": [
                          "catalog",
                          "identity",
                          "model",
                          "requirements",
                          "stage_memory_layout",
                          "workload_image"
                        ],
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "artifact_ref"
                        ],
                        "type": "string"
                      },
                      "path": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "kind",
                      "artifact",
                      "path"
                    ],
                    "type": "object"
                  },
                  {
                    "additionalProperties": false,
                    "properties": {
                      "expression": {
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "derived_expression"
                        ],
                        "type": "string"
                      },
                      "refs": {
                        "items": {
                          "additionalProperties": false,
                          "properties": {
                            "artifact": {
                              "enum": [
                                "catalog",
                                "identity",
                                "model",
                                "requirements",
                                "stage_memory_layout",
                                "workload_image"
                              ],
                              "type": "string"
                            },
                            "path": {
                              "type": "string"
                            },
                            "symbol": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "symbol",
                            "artifact",
                            "path"
                          ],
                          "type": "object"
                        },
                        "minItems": 1,
                        "type": "array"
                      }
                    },
                    "required": [
                      "kind",
                      "expression",
                      "refs"
                    ],
                    "type": "object"
                  }
                ]
              }
            },
            "required": [
              "resolved_value",
              "source"
            ],
            "type": "object"
          },
          "data_width_bits": {
            "type": "integer"
          },
          "purpose": {
            "type": "string"
          },
          "region_id": {
            "type": "string"
          },
          "size_bytes": {
            "additionalProperties": false,
            "properties": {
              "resolved_value": {
                "type": "integer"
              },
              "source": {
                "oneOf": [
                  {
                    "additionalProperties": false,
                    "properties": {
                      "artifact": {
                        "enum": [
                          "catalog",
                          "identity",
                          "model",
                          "requirements",
                          "stage_memory_layout",
                          "workload_image"
                        ],
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "artifact_ref"
                        ],
                        "type": "string"
                      },
                      "path": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "kind",
                      "artifact",
                      "path"
                    ],
                    "type": "object"
                  },
                  {
                    "additionalProperties": false,
                    "properties": {
                      "expression": {
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "derived_expression"
                        ],
                        "type": "string"
                      },
                      "refs": {
                        "items": {
                          "additionalProperties": false,
                          "properties": {
                            "artifact": {
                              "enum": [
                                "catalog",
                                "identity",
                                "model",
                                "requirements",
                                "stage_memory_layout",
                                "workload_image"
                              ],
                              "type": "string"
                            },
                            "path": {
                              "type": "string"
                            },
                            "symbol": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "symbol",
                            "artifact",
                            "path"
                          ],
                          "type": "object"
                        },
                        "minItems": 1,
                        "type": "array"
                      }
                    },
                    "required": [
                      "kind",
                      "expression",
                      "refs"
                    ],
                    "type": "object"
                  }
                ]
              }
            },
            "required": [
              "resolved_value",
              "source"
            ],
            "type": "object"
          }
        },
        "required": [
          "region_id",
          "purpose",
          "axi_interface_ref",
          "address_width_bits",
          "data_width_bits",
          "base_address",
          "size_bytes",
          "alignment_bytes"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "physical_cfg_bindings": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "access": {
            "type": "string"
          },
          "binding_id": {
            "type": "string"
          },
          "binding_mode": {
            "enum": [
              "program",
              "observe"
            ],
            "type": "string"
          },
          "bit_offset": {
            "type": "integer"
          },
          "fact_port_id": {
            "type": "string"
          },
          "field_id": {
            "type": "string"
          },
          "register": {
            "type": "string"
          },
          "reset_value": {
            "type": "integer"
          },
          "runtime_role": {
            "type": "string"
          },
          "value": {
            "additionalProperties": false,
            "properties": {
              "resolved_value": {
                "type": "integer"
              },
              "source": {
                "oneOf": [
                  {
                    "additionalProperties": false,
                    "properties": {
                      "artifact": {
                        "enum": [
                          "catalog",
                          "identity",
                          "model",
                          "requirements",
                          "stage_memory_layout",
                          "workload_image"
                        ],
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "artifact_ref"
                        ],
                        "type": "string"
                      },
                      "path": {
                        "type": "string"
                      }
                    },
                    "required": [
                      "kind",
                      "artifact",
                      "path"
                    ],
                    "type": "object"
                  },
                  {
                    "additionalProperties": false,
                    "properties": {
                      "expression": {
                        "type": "string"
                      },
                      "kind": {
                        "enum": [
                          "derived_expression"
                        ],
                        "type": "string"
                      },
                      "refs": {
                        "items": {
                          "additionalProperties": false,
                          "properties": {
                            "artifact": {
                              "enum": [
                                "catalog",
                                "identity",
                                "model",
                                "requirements",
                                "stage_memory_layout",
                                "workload_image"
                              ],
                              "type": "string"
                            },
                            "path": {
                              "type": "string"
                            },
                            "symbol": {
                              "type": "string"
                            }
                          },
                          "required": [
                            "symbol",
                            "artifact",
                            "path"
                          ],
                          "type": "object"
                        },
                        "minItems": 1,
                        "type": "array"
                      }
                    },
                    "required": [
                      "kind",
                      "expression",
                      "refs"
                    ],
                    "type": "object"
                  }
                ]
              }
            },
            "required": [
              "resolved_value",
              "source"
            ],
            "type": "object"
          },
          "width_bits": {
            "type": "integer"
          }
        },
        "required": [
          "binding_id",
          "runtime_role",
          "binding_mode",
          "field_id",
          "fact_port_id",
          "register",
          "bit_offset",
          "width_bits",
          "access",
          "reset_value",
          "value"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "programming_sequence": {
      "additionalProperties": false,
      "properties": {
        "clock_domain": {
          "type": "string"
        },
        "enforcement": {
          "type": "string"
        },
        "steps": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "event": {
                "type": "string"
              },
              "fact_port_ids": {
                "items": {
                  "type": "string"
                },
                "type": "array"
              },
              "order": {
                "type": "integer"
              }
            },
            "required": [
              "order",
              "event",
              "fact_port_ids"
            ],
            "type": "object"
          },
          "type": "array"
        }
      },
      "required": [
        "clock_domain",
        "enforcement",
        "steps"
      ],
      "type": "object"
    },
    "runtime_constants": {
      "additionalProperties": false,
      "properties": {
        "connected_runtime_stream_contract_sha256": {
          "pattern": "^[0-9a-f]{64}$",
          "type": [
            "string",
            "null"
          ]
        },
        "enabled": {
          "type": "boolean"
        },
        "full_runtime_image_manifest": {
          "additionalProperties": true,
          "type": "object"
        },
        "load_schedule": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "byte_count": {
                "type": "integer"
              },
              "byte_offset": {
                "type": "integer"
              },
              "complete_before_kernel_start": {
                "type": "boolean"
              },
              "last_word_address": {
                "type": "integer"
              },
              "layer_index": {
                "type": "integer"
              },
              "loader_address_count": {
                "type": "integer"
              },
              "loader_address_start": {
                "type": "integer"
              },
              "segment_id": {
                "type": "string"
              },
              "sha256": {
                "pattern": "^[0-9a-f]{64}$",
                "type": "string"
              },
              "word_count": {
                "type": "integer"
              },
              "word_offset": {
                "type": "integer"
              }
            },
            "required": [
              "layer_index",
              "segment_id",
              "byte_offset",
              "byte_count",
              "word_offset",
              "word_count",
              "sha256",
              "loader_address_start",
              "loader_address_count",
              "last_word_address",
              "complete_before_kernel_start"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "loader_abi": {
          "additionalProperties": false,
          "properties": {
            "addr_port": {
              "type": "string"
            },
            "addr_width_bits": {
              "type": "integer"
            },
            "data_port": {
              "type": "string"
            },
            "data_width_bits": {
              "type": "integer"
            },
            "last_port": {
              "type": "string"
            },
            "ready_port": {
              "type": "string"
            },
            "valid_port": {
              "type": "string"
            }
          },
          "required": [
            "valid_port",
            "ready_port",
            "data_port",
            "data_width_bits",
            "addr_port",
            "addr_width_bits",
            "last_port"
          ],
          "type": [
            "object",
            "null"
          ]
        },
        "loader_protocol": {
          "additionalProperties": false,
          "properties": {
            "address_increment": {
              "type": "integer"
            },
            "address_start": {
              "type": "integer"
            },
            "complete_before_kernel_start": {
              "type": "boolean"
            },
            "data_word_bits": {
              "type": "integer"
            },
            "last_on_final_accepted_word": {
              "type": "boolean"
            },
            "ready_valid_acceptance": {
              "type": "boolean"
            }
          },
          "required": [
            "ready_valid_acceptance",
            "address_start",
            "address_increment",
            "data_word_bits",
            "last_on_final_accepted_word",
            "complete_before_kernel_start"
          ],
          "type": [
            "object",
            "null"
          ]
        },
        "materialized_projection": {
          "additionalProperties": true,
          "type": "object"
        },
        "region_id": {
          "type": [
            "string",
            "null"
          ]
        },
        "trace_point_ids": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "enabled",
        "region_id",
        "connected_runtime_stream_contract_sha256",
        "loader_abi",
        "loader_protocol",
        "load_schedule",
        "trace_point_ids"
      ],
      "type": "object"
    },
    "schema_version": {
      "enum": [
        "spatialaccagent.board_memory_runtime_plan.v1"
      ],
      "type": "string"
    },
    "status": {
      "enum": [
        "ready",
        "blocked"
      ],
      "type": "string"
    },
    "summary": {
      "type": "string"
    },
    "trace_points": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "clock_domain": {
            "type": "string"
          },
          "condition": {
            "type": "string"
          },
          "observed_fields": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "role": {
            "enum": [
              "activation_bank_switch",
              "final_writeback_complete",
              "final_writeback_start",
              "runtime_load_complete",
              "runtime_load_start",
              "weight_bank_switch",
              "weight_prefetch_complete",
              "weight_prefetch_start"
            ],
            "type": "string"
          },
          "trace_id": {
            "type": "string"
          }
        },
        "required": [
          "trace_id",
          "role",
          "clock_domain",
          "condition",
          "observed_fields"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "weight_double_buffer": {
      "additionalProperties": false,
      "properties": {
        "bank_count": {
          "enum": [
            2
          ],
          "type": "integer"
        },
        "banks": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "bank_id": {
                "type": "string"
              },
              "capacity_bytes": {
                "additionalProperties": false,
                "properties": {
                  "resolved_value": {
                    "type": "integer"
                  },
                  "source": {
                    "oneOf": [
                      {
                        "additionalProperties": false,
                        "properties": {
                          "artifact": {
                            "enum": [
                              "catalog",
                              "identity",
                              "model",
                              "requirements",
                              "stage_memory_layout",
                              "workload_image"
                            ],
                            "type": "string"
                          },
                          "kind": {
                            "enum": [
                              "artifact_ref"
                            ],
                            "type": "string"
                          },
                          "path": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "kind",
                          "artifact",
                          "path"
                        ],
                        "type": "object"
                      },
                      {
                        "additionalProperties": false,
                        "properties": {
                          "expression": {
                            "type": "string"
                          },
                          "kind": {
                            "enum": [
                              "derived_expression"
                            ],
                            "type": "string"
                          },
                          "refs": {
                            "items": {
                              "additionalProperties": false,
                              "properties": {
                                "artifact": {
                                  "enum": [
                                    "catalog",
                                    "identity",
                                    "model",
                                    "requirements",
                                    "stage_memory_layout",
                                    "workload_image"
                                  ],
                                  "type": "string"
                                },
                                "path": {
                                  "type": "string"
                                },
                                "symbol": {
                                  "type": "string"
                                }
                              },
                              "required": [
                                "symbol",
                                "artifact",
                                "path"
                              ],
                              "type": "object"
                            },
                            "minItems": 1,
                            "type": "array"
                          }
                        },
                        "required": [
                          "kind",
                          "expression",
                          "refs"
                        ],
                        "type": "object"
                      }
                    ]
                  }
                },
                "required": [
                  "resolved_value",
                  "source"
                ],
                "type": "object"
              },
              "region_id": {
                "type": "string"
              }
            },
            "required": [
              "bank_id",
              "region_id",
              "capacity_bytes"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "initial_bank_id": {
          "type": "string"
        },
        "initial_layer_index": {
          "type": "integer"
        },
        "layer_schedule": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "compute_bank_id": {
                "type": "string"
              },
              "layer_index": {
                "type": "integer"
              },
              "prefetch_bank_id": {
                "type": [
                  "string",
                  "null"
                ]
              },
              "prefetch_layer_index": {
                "type": [
                  "integer",
                  "null"
                ]
              },
              "prefetch_overlaps_compute": {
                "type": "boolean"
              },
              "switch_is_atomic": {
                "type": "boolean"
              }
            },
            "required": [
              "layer_index",
              "compute_bank_id",
              "prefetch_layer_index",
              "prefetch_bank_id",
              "prefetch_overlaps_compute",
              "switch_is_atomic"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "ownership_protocol": {
          "additionalProperties": false,
          "properties": {
            "atomic_switch": {
              "type": "boolean"
            },
            "inactive_bank_prefetch_only": {
              "type": "boolean"
            },
            "prefetch_completion_before_switch": {
              "type": "boolean"
            },
            "single_compute_owner": {
              "type": "boolean"
            }
          },
          "required": [
            "single_compute_owner",
            "inactive_bank_prefetch_only",
            "prefetch_completion_before_switch",
            "atomic_switch"
          ],
          "type": "object"
        },
        "trace_point_ids": {
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "bank_count",
        "initial_layer_index",
        "initial_bank_id",
        "banks",
        "ownership_protocol",
        "layer_schedule",
        "trace_point_ids"
      ],
      "type": "object"
    },
    "workload_image": {
      "additionalProperties": false,
      "properties": {
        "full_weight_image_manifest": {
          "additionalProperties": true,
          "type": "object"
        },
        "image_plan": {
          "additionalProperties": true,
          "properties": {
            "additional_runtime_fields": {
              "additionalProperties": true,
              "type": "object"
            },
            "image": {
              "additionalProperties": false,
              "properties": {
                "byte_order": {
                  "enum": [
                    "little"
                  ],
                  "type": "string"
                },
                "format": {
                  "enum": [
                    "u32le_binary"
                  ],
                  "type": "string"
                },
                "layer_alignment_bytes": {
                  "type": "integer"
                },
                "layer_order": {
                  "items": {
                    "type": "integer"
                  },
                  "type": "array"
                },
                "word_bits": {
                  "enum": [
                    32
                  ],
                  "type": "integer"
                }
              },
              "required": [
                "format",
                "word_bits",
                "byte_order",
                "layer_order",
                "layer_alignment_bytes"
              ],
              "type": "object"
            },
            "input_identity": {
              "additionalProperties": false,
              "properties": {
                "canonical_weight_layout_set_sha256": {
                  "type": "string"
                },
                "connected_weight_stream_contract_sha256": {
                  "type": "string"
                },
                "source_checkpoint_sha256": {
                  "type": "string"
                },
                "stage_weight_layout_contract_sha256s": {
                  "items": {
                    "type": "string"
                  },
                  "type": "array"
                },
                "transformer_block_weight_catalog_sha256": {
                  "type": "string"
                }
              },
              "required": [
                "transformer_block_weight_catalog_sha256",
                "source_checkpoint_sha256",
                "connected_weight_stream_contract_sha256",
                "stage_weight_layout_contract_sha256s",
                "canonical_weight_layout_set_sha256"
              ],
              "type": "object"
            },
            "memory": {
              "additionalProperties": false,
              "properties": {
                "weight_bank_capacity_bytes": {
                  "type": "integer"
                },
                "weight_bank_count": {
                  "enum": [
                    2
                  ],
                  "type": "integer"
                }
              },
              "required": [
                "weight_bank_count",
                "weight_bank_capacity_bytes"
              ],
              "type": "object"
            },
            "schema_version": {
              "enum": [
                "spatialaccagent.board_workload_image_plan.v1"
              ],
              "type": "string"
            },
            "status": {
              "enum": [
                "pass"
              ],
              "type": "string"
            },
            "target_layer_count": {
              "type": "integer"
            }
          },
          "required": [
            "schema_version",
            "status",
            "target_layer_count",
            "input_identity",
            "image",
            "memory"
          ],
          "type": "object"
        },
        "materialized_projection": {
          "additionalProperties": true,
          "type": "object"
        },
        "region_id": {
          "type": "string"
        },
        "semantic_refs": {
          "additionalProperties": false,
          "properties": {
            "layer_alignment_bytes": {
              "additionalProperties": false,
              "properties": {
                "resolved_value": {
                  "type": "integer"
                },
                "source": {
                  "oneOf": [
                    {
                      "additionalProperties": false,
                      "properties": {
                        "artifact": {
                          "enum": [
                            "catalog",
                            "identity",
                            "model",
                            "requirements",
                            "stage_memory_layout",
                            "workload_image"
                          ],
                          "type": "string"
                        },
                        "kind": {
                          "enum": [
                            "artifact_ref"
                          ],
                          "type": "string"
                        },
                        "path": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "kind",
                        "artifact",
                        "path"
                      ],
                      "type": "object"
                    },
                    {
                      "additionalProperties": false,
                      "properties": {
                        "expression": {
                          "type": "string"
                        },
                        "kind": {
                          "enum": [
                            "derived_expression"
                          ],
                          "type": "string"
                        },
                        "refs": {
                          "items": {
                            "additionalProperties": false,
                            "properties": {
                              "artifact": {
                                "enum": [
                                  "catalog",
                                  "identity",
                                  "model",
                                  "requirements",
                                  "stage_memory_layout",
                                  "workload_image"
                                ],
                                "type": "string"
                              },
                              "path": {
                                "type": "string"
                              },
                              "symbol": {
                                "type": "string"
                              }
                            },
                            "required": [
                              "symbol",
                              "artifact",
                              "path"
                            ],
                            "type": "object"
                          },
                          "minItems": 1,
                          "type": "array"
                        }
                      },
                      "required": [
                        "kind",
                        "expression",
                        "refs"
                      ],
                      "type": "object"
                    }
                  ]
                }
              },
              "required": [
                "resolved_value",
                "source"
              ],
              "type": "object"
            },
            "weight_bank_capacity_bytes": {
              "additionalProperties": false,
              "properties": {
                "resolved_value": {
                  "type": "integer"
                },
                "source": {
                  "oneOf": [
                    {
                      "additionalProperties": false,
                      "properties": {
                        "artifact": {
                          "enum": [
                            "catalog",
                            "identity",
                            "model",
                            "requirements",
                            "stage_memory_layout",
                            "workload_image"
                          ],
                          "type": "string"
                        },
                        "kind": {
                          "enum": [
                            "artifact_ref"
                          ],
                          "type": "string"
                        },
                        "path": {
                          "type": "string"
                        }
                      },
                      "required": [
                        "kind",
                        "artifact",
                        "path"
                      ],
                      "type": "object"
                    },
                    {
                      "additionalProperties": false,
                      "properties": {
                        "expression": {
                          "type": "string"
                        },
                        "kind": {
                          "enum": [
                            "derived_expression"
                          ],
                          "type": "string"
                        },
                        "refs": {
                          "items": {
                            "additionalProperties": false,
                            "properties": {
                              "artifact": {
                                "enum": [
                                  "catalog",
                                  "identity",
                                  "model",
                                  "requirements",
                                  "stage_memory_layout",
                                  "workload_image"
                                ],
                                "type": "string"
                              },
                              "path": {
                                "type": "string"
                              },
                              "symbol": {
                                "type": "string"
                              }
                            },
                            "required": [
                              "symbol",
                              "artifact",
                              "path"
                            ],
                            "type": "object"
                          },
                          "minItems": 1,
                          "type": "array"
                        }
                      },
                      "required": [
                        "kind",
                        "expression",
                        "refs"
                      ],
                      "type": "object"
                    }
                  ]
                }
              },
              "required": [
                "resolved_value",
                "source"
              ],
              "type": "object"
            }
          },
          "required": [
            "layer_alignment_bytes",
            "weight_bank_capacity_bytes"
          ],
          "type": "object"
        }
      },
      "required": [
        "image_plan",
        "region_id",
        "semantic_refs"
      ],
      "type": "object"
    }
  },
  "required": [
    "schema_version",
    "agent",
    "status",
    "summary",
    "blocked_reasons",
    "input_bindings",
    "workload_image",
    "memory_regions",
    "physical_cfg_bindings",
    "programming_sequence",
    "runtime_constants",
    "weight_double_buffer",
    "activation_ping_pong",
    "final_writeback",
    "trace_points"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
