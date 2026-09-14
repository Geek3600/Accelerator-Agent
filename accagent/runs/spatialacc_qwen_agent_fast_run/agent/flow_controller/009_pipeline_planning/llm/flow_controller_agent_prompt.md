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
false
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
  "command_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/agent/logs/27_pipeline_planning.json",
  "command_returncode": 2,
  "errors": [
    "stage command failed with returncode 2"
  ],
  "failed_output_policy": "existing stage report was not promoted because the current command failed",
  "stale_output_ignored": true,
  "stale_output_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/pipeline_planning_report.json",
  "stale_output_status": "incomplete",
  "status": "failed",
  "stdout_tail": "[team:decomposer] reuse cached /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/decomposer_result.json\n[stage:pipeline_planning.pipeline architect:llm] reuse cached model_shape_specialist: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/llm/model_shape_specialist_result.json\n[stage:pipeline_planning.numeric template engineer:llm] start numeric_template_specialist\n[stage:pipeline_planning.numeric template engineer:llm] prompt /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/llm/numeric_template_specialist_prompt.md\n[stage:llm] retry numeric_template_specialist_json after transient error (unbounded): HTTP Error 429: Too Many Requests; response_body={\"error\":{\"message\":\"Upstream rate limit exceeded, please retry later\",\"type\":\"rate_limit_error\"}}; sleep 8.0s\n[stage:pipeline_planning.numeric template engineer:llm] failed numeric_template_specialist: HTTP Error 404: Not Found; response_body={\"error\":{\"message\":\"Model \\\"gpt-5.5\\\" is not supported by any configured account in this group\",\"type\":\"model_not_found\"}}\n[stage:pipeline_planning.numeric template engineer:llm] log /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/llm/numeric_template_specialist_result.json\n[stage:pipeline_planning.stream and liveness engineer:llm] reuse cached data_memory_runtime_specialist__stream_and_liveness_engineer: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/llm/data_memory_runtime_specialist__stream_and_liveness_engineer_result.json\n[stage:pipeline_planning.memory dataflow engineer:llm] reuse cached data_memory_runtime_specialist__memory_dataflow_engineer: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/llm/data_memory_runtime_specialist__memory_dataflow_engineer_result.json\n[stage:pipeline_planning.verification evidence gate auditor:llm] reuse cached verification_repair_specialist: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/team/llm/verification_repair_specialist_result.json\n[stage:pipeline_planning:llm] start pipeline_architect_agent\n[stage:pipeline_planning:llm] prompt /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/llm/pipeline_architect_agent_prompt.md\n[stage:pipeline_planning:llm] failed pipeline_architect_agent: HTTP Error 404: Not Found; response_body={\"error\":{\"message\":\"Model \\\"gpt-5.5\\\" is not supported by any configured account in this group\",\"type\":\"model_not_found\"}}\n[stage:pipeline_planning:llm] log /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/pipeline_planning/llm/pipeline_architect_agent_result.json\nerror: HTTP Error 404: Not Found; response_body={\"error\":{\"message\":\"Model \\\"gpt-5.5\\\" is not supported by any configured account in this group\",\"type\":\"model_not_found\"}}",
  "warnings": []
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
2
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/agent/logs/27_pipeline_planning.json
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
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/template_selection/sacg_state.json
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
