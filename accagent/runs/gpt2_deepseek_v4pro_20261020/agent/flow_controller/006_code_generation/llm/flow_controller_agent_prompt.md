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
code_generation
</current_stage>

<stage_passed>
true
</stage_passed>

<attempt_count>
1
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
      ],
      [
        "sbt",
        "--no-server",
        "--batch",
        "--supershell=false",
        "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
      ],
      [
        "sbt",
        "--no-server",
        "--batch",
        "--supershell=false",
        "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
      ]
    ],
    "cwd": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel",
    "duration_sec": 182.4589252860169,
    "elaboration_enabled": true,
    "empty_generated_outputs": [],
    "enabled": true,
    "fpga_ip_modules": [],
    "local_sbt_dirs": {
      "coursier_cache": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/.sbt_codegen_cache/coursier",
      "sbt_boot_directory": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/.sbt_codegen_cache/sbt/boot",
      "sbt_global_base": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/.sbt_codegen_cache/sbt",
      "sbt_ivy_home": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/.sbt_codegen_cache/ivy2"
    },
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/compile_check.json",
    "missing_generated_outputs": [],
    "required_generated_outputs": [
      "GeneratedAcceleratorTop.sv",
      "GeneratedAxiDdrTop.sv"
    ],
    "returncode": 0,
    "schema_version": "spatialaccagent.codegen_compile_gate.v0",
    "status": "pass",
    "stderr_tail": "",
    "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado \n[success] Total time: 16 s, completed Oct 20, 2026, 9:02:44 PM\n",
    "steps": [
      {
        "command": [
          "sbt",
          "--no-server",
          "--batch",
          "--supershell=false",
          "Compile/compile"
        ],
        "failure_markers": [],
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "[info] [launcher] getting org.scala-sbt sbt 1.9.7  (this may take some time)...\n[info] [launcher] getting Scala 2.12.18 (for sbt)...\n",
        "stdout_tail": "copying runtime jar...\n[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] compiling 21 Scala sources to /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/target/scala-2.13/classes ...\n[info] done compiling\n[success] Total time: 46 s, completed Oct 20, 2026, 9:01:24 PM\n"
      },
      {
        "command": [
          "sbt",
          "--no-server",
          "--batch",
          "--supershell=false",
          "runMain spatialaccagent.generated.GeneratedContractCheck"
        ],
        "failure_markers": [],
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] running spatialaccagent.generated.GeneratedContractCheck \nGeneratedContractCheck pass: hidden=768, intermediate=3072, lanes=16, bits=8/8/8\n[success] Total time: 1 s, completed Oct 20, 2026, 9:01:28 PM\n"
      },
      {
        "command": [
          "sbt",
          "--no-server",
          "--batch",
          "--supershell=false",
          "runMain spatialaccagent.generated.ElaborateGeneratedAccelerator"
        ],
        "failure_markers": [],
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAccelerator \n[success] Total time: 15 s, completed Oct 20, 2026, 9:01:46 PM\n"
      },
      {
        "command": [
          "sbt",
          "--no-server",
          "--batch",
          "--supershell=false",
          "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTop"
        ],
        "failure_markers": [],
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAxiDdrTop \n[success] Total time: 16 s, completed Oct 20, 2026, 9:02:05 PM\n"
      },
      {
        "command": [
          "sbt",
          "--no-server",
          "--batch",
          "--supershell=false",
          "runMain spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado"
        ],
        "failure_markers": [],
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAcceleratorVivado \n[success] Total time: 16 s, completed Oct 20, 2026, 9:02:25 PM\n"
      },
      {
        "command": [
          "sbt",
          "--no-server",
          "--batch",
          "--supershell=false",
          "runMain spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado"
        ],
        "failure_markers": [],
        "returncode": 0,
        "status": "pass",
        "stderr_tail": "",
        "stdout_tail": "[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.20.1)\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/project\n[info] loading settings for project root from build.sbt ...\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/)\n[info] running spatialaccagent.generated.ElaborateGeneratedAxiDdrTopVivado \n[success] Total time: 16 s, completed Oct 20, 2026, 9:02:44 PM\n"
      }
    ],
    "summary": "completed 6 compile/elaboration command(s)",
    "timeout_sec": 1800
  },
  "contract_check": {
    "checked_contracts": [
      "upstream_transition_status",
      "model_shape_to_generated_params",
      "stage3_implementation_contract_to_generated_top",
      "numeric_policy_to_generated_bits",
      "template_provenance_hashes",
      "mandatory_fpga_ip_binding",
      "simulation_implementation_ip_timing_identity",
      "compiled_generated_ddr_tile_service_abi",
      "compile_and_elaboration_warning_free",
      "memory_layout_alignment_nonoverlap",
      "runtime_config_consistency",
      "parameter_binding_legality"
    ],
    "checker": "codegen_contract_check",
    "design_id": "gpt2_deepseek_v4pro_20261020",
    "errors": [],
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/codegen_contract_check.json",
    "schema_version": "spatialaccagent.codegen_contract_check.v0",
    "status": "pass",
    "summary": "all code generation contracts passed",
    "warnings": []
  },
  "design_team": {
    "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/team/team_aggregate.json",
    "approval_required_for": [],
    "completed_subtasks": 0,
    "decomposer_error": null,
    "decomposer_used_fallback": false,
    "decomposition_source": "llm",
    "errors": [],
    "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/team/event_log.jsonl",
    "executable_actions": [],
    "execution_groups": [],
    "llm_io_metrics": {
      "executable_action_count": 0,
      "max_duration_sec": 0.0,
      "max_prompt_bytes": 0,
      "result_count": 0,
      "subtasks_without_executable_actions": [],
      "total_duration_sec": 0,
      "total_prompt_bytes": 0
    },
    "split_required": false,
    "status": "no_split",
    "subtask_count": 0,
    "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/team/subtask_plan.json",
    "used_fallback_count": 0
  },
  "errors": [],
  "generated_files": [
    "generated/chisel/README.md",
    "generated/chisel/build.sbt",
    "generated/chisel/logs/dse_physical_binding_check.json",
    "generated/chisel/memory/memory_layout.json",
    "generated/chisel/project/build.properties",
    "generated/chisel/runtime/runtime_config.json",
    "generated/chisel/scripts/compile_check.sh",
    "generated/chisel/scripts/elaborate.sh",
    "generated/chisel/simulation/fpga_ip_simulation_closure.json",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.mem",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/exp2_fraction_q24.memh",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.mem",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/sigmoid_pwl_q18.memh",
    "generated/chisel/src/main/resources/spatialaccagent/numeric/transcendental_approximation_contract.json",
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
    "generated/chisel/src/main/scala/spatialaccagent/templates/PhysicalResources.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/QKVProjection.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/RoPE.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/Softmax.scala",
    "generated/chisel/src/main/scala/spatialaccagent/templates/WeightTileCache.scala"
  ],
  "llm_agent": {
    "agent": "code_generation_agent",
    "approval_required_for": [],
    "executable_actions": [
      {
        "acceptance_checkers": [
          "code_generation_manifest_static_check",
          "codegen_package_static_check",
          "codegen_contract_check",
          "codegen_compile_gate_check",
          "sacg_memory_check"
        ],
        "action_type": "stage_gate_advance",
        "consumes": [
          "artifact.code_generation_manifest",
          "generated/chisel/logs/compile_check.json",
          "generated/chisel/logs/codegen_contract_check.json",
          "generated/chisel/logs/codegen_package_static_check.json",
          "generated/chisel/memory/memory_layout.json",
          "generated/chisel/runtime/runtime_config.json",
          "sacg_memory_truth"
        ],
        "id": "codegen.advance_ready_handoff",
        "on_failure": "Keep publish_status as candidate_only, localize the failing current-stage artifact or checker, repair it, and rerun the affected compile/contract/static check before attempting any Stage 6 handoff.",
        "produces": [
          "artifact.code_generation_handoff.ready",
          "sacg_memory.recent_stage_outcome.stage5.code_generation"
        ],
        "rationale": "All current-stage acceptance evidence passes: compile/elaboration gate returncode is 0, contract and package static checks pass with no warnings, target_model_artifact_status matches the GPT-2 target with no missing artifacts, and SACG memory truth has no active blockers. Promote the candidate manifest to ready handoff and persist the stage outcome for Stage 6 consumers.",
        "requires_approval": false,
        "stage": "code_generation",
        "tool_roles": [
          "code_generation_manifest_static_check",
          "codegen_package_static_check",
          "codegen_contract_check",
          "sacg_memory_update"
        ]
      }
    ],
    "observations": [
      "Compile/elaboration gate passed all 6 declared SBT commands with returncode 0; generated_outputs include required GeneratedAcceleratorTop.sv and GeneratedAxiDdrTop.sv, with no missing or empty generated outputs.",
      "GeneratedContractCheck passed and reported hidden=768, intermediate=3072, lanes=16, bits=8/8/8.",
      "codegen_contract_check passed all 12 listed contracts with zero errors and zero warnings.",
      "codegen_package_static_check passed all 5 listed package-structure contracts with zero errors and zero warnings.",
      "target_model_artifact_status.current_artifacts_match_target is true and missing_for_target is empty for model_type gpt2.",
      "Manifest template_sources cover 16 template Scala sources and match the generated package template list; selected_operator_template_sources are a strict subset.",
      "publish_status is candidate_only and manifest status is ready, which stage_gate_policy treats as normal pre-publication state.",
      "design_team reports no_split with zero subtasks and empty executable_actions; the stage gate does not require team decomposition for this code-generation step, and the manifest itself functions as the handoff artifact.",
      "sacg_memory_truth shows active_contamination_barrier_count=0, open_backtrack_request_count=0, and open_retry_request_count=0; no current SACG-memory blockers affect promotion.",
      "hierarchical_learning_context contains no validated lower-layer certificates; this does not block code generation because Stage 5 does not require lower-layer VCS evidence.",
      "Generated package includes both standard generated/chisel and Vivado-oriented generated/chisel/vivado SystemVerilog outputs plus verification assert/assume/cover scaffolding.",
      "generated_top.params contains derived fields such as head_dim=64, num_q_heads=12, num_kv_heads=12, max_seq_len=16, and board_axi_data_width_bits=512; some of these are not repeated in the top-level parameter_binding block, but codegen_contract_check parameter_binding_legality passed, so this is a downstream handoff-consistency item rather than a current-stage blocker."
    ],
    "proposed_actions": [
      "Promote the Stage 5 candidate manifest to a ready code-generation handoff and record the stage outcome in SACG memory.",
      "In Stage 6 planning, consume the generated manifest, memory layout, runtime config, and generated_top.params to create bottom-up VCS compile-only verification artifacts in leaf, connected-kernel, and exact board-wrapper order.",
      "Include head_dim, num_q_heads, num_kv_heads, max_seq_len, board_axi_data_width_bits, cache_refill_data_width_bits, and memory selection fields in the Stage 6 handoff checklist, while keeping the current contract-check pass as authoritative for Stage 5.",
      "Require Stage 7/backend work to use the exact user-supplied board wrapper and sample project rather than simplified or hardcoded AXI/DDR paths.",
      "Do not assign a nonzero FPGA clock target until board-profile evidence or explicit approval establishes it."
    ],
    "risks": [
      "Stage 6 must validate generated memory_layout.json and runtime_config.json against real board/runtime evidence before any hardware pass claim; their current generated status is not a board or runtime validation.",
      "clock_target_mhz=0 in generated_top.params and null in parameter_binding mean the board shell clock is unknown; assigning a nonzero clock target without board-profile evidence or explicit approval could contaminate later timing work.",
      "compile_gate.fpga_ip_modules is empty; Stage 6 must verify the generated FPGA IP simulation closure still enforces the same XPM/Vivado IP module interfaces and latencies as implementation, even though the current mandatory/simulation-implementation identity contract passed.",
      "Cross-layer model/board fields present only in generated_top.params should be explicitly consumed by Stage 6 verification artifact contracts to avoid ambiguous downstream weight, address, or token-pipeline assumptions.",
      "Current-source VCS compilation, elaboration, and linking are later-stage obligations; their absence must not be retroactively treated as a Stage 5 code-generation failure.",
      "Vivado synthesis, backend shell target discovery, runtime bitstream, and board deployment evidence remain Stage 7/later obligations and must use real user-supplied board materials, not guessed or hardcoded names."
    ],
    "sacg_focus": {
      "artifacts": [
        "code_generation_manifest.json",
        "generated/chisel/logs/compile_check.json",
        "generated/chisel/logs/codegen_contract_check.json",
        "generated/chisel/logs/codegen_package_static_check.json",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "generated/chisel/GeneratedAcceleratorTop.sv",
        "generated/chisel/GeneratedAxiDdrTop.sv",
        "generated/chisel/vivado/filelist.f"
      ],
      "constraints": [
        "constraint.codegen.package",
        "constraint.codegen.compile_gate",
        "constraint.codegen.contract_check",
        "constraint.memory.board",
        "constraint.runtime.board",
        "constraint.deployment.board"
      ],
      "edges": [
        "artifact.input.model_config -> generated.model_ir",
        "artifact.stage3.pipeline_plan + artifact.stage4.parameter_binding -> generated.arch_plan",
        "generated.chisel_modules -> generated.fpga_ip_simulation_closure",
        "generated.chisel_modules + artifact.input.target_board_profile -> generated.top_wrapper",
        "generated.top_wrapper + artifact.input.target_board_profile -> generated.fpga_axi_ddr_top_wrapper",
        "artifact.stage4.parameter_binding + artifact.input.target_board_profile -> generated.memory_layout",
        "generated.memory_layout + artifact.input.target_board_profile -> generated.runtime_config",
        "generated.chisel_modules + generated.top_wrapper + generated.fpga_axi_ddr_top_wrapper -> generated.codegen_compile_gate",
        "generated.chisel_modules + generated.memory_layout + generated.runtime_config + generated.codegen_compile_gate -> generated.codegen_contract_check"
      ],
      "nodes": [
        "generated.model_ir",
        "generated.arch_plan",
        "generated.chisel_modules",
        "generated.top_wrapper",
        "generated.fpga_axi_ddr_top_wrapper",
        "generated.memory_layout",
        "generated.runtime_config",
        "generated.scala_contract_check",
        "generated.codegen_compile_gate",
        "generated.codegen_contract_check",
        "artifact.input.model_config",
        "artifact.input.target_board_profile",
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding"
      ]
    },
    "schema_version": "spatialaccagent.agent_response.v0",
    "stage": "code_generation",
    "status": "ready",
    "summary": "Reviewed the candidate code-generation manifest, generated package, compile/elaboration gate, contract/static checks, team aggregate, and SACG memory truth. All supplied current-stage acceptance evidence passes, target artifacts match the GPT-2 target with no missing artifacts, and there are no active contamination barriers, retries, or backtracks. The manifest is ready to hand off to Stage 6; candidate_only is the normal pre-publication state and not a current-stage failure."
  },
  "llm_executable_actions": [
    {
      "acceptance_checkers": [
        "code_generation_manifest_static_check",
        "codegen_package_static_check",
        "codegen_contract_check",
        "codegen_compile_gate_check",
        "sacg_memory_check"
      ],
      "action_type": "stage_gate_advance",
      "consumes": [
        "artifact.code_generation_manifest",
        "generated/chisel/logs/compile_check.json",
        "generated/chisel/logs/codegen_contract_check.json",
        "generated/chisel/logs/codegen_package_static_check.json",
        "generated/chisel/memory/memory_layout.json",
        "generated/chisel/runtime/runtime_config.json",
        "sacg_memory_truth"
      ],
      "id": "codegen.advance_ready_handoff",
      "on_failure": "Keep publish_status as candidate_only, localize the failing current-stage artifact or checker, repair it, and rerun the affected compile/contract/static check before attempting any Stage 6 handoff.",
      "produces": [
        "artifact.code_generation_handoff.ready",
        "sacg_memory.recent_stage_outcome.stage5.code_generation"
      ],
      "rationale": "All current-stage acceptance evidence passes: compile/elaboration gate returncode is 0, contract and package static checks pass with no warnings, target_model_artifact_status matches the GPT-2 target with no missing artifacts, and SACG memory truth has no active blockers. Promote the candidate manifest to ready handoff and persist the stage outcome for Stage 6 consumers.",
      "requires_approval": false,
      "stage": "code_generation",
      "tool_roles": [
        "code_generation_manifest_static_check",
        "codegen_package_static_check",
        "codegen_contract_check",
        "sacg_memory_update"
      ]
    }
  ],
  "memory_layout": {
    "alignment_bytes": 64,
    "axi_data_width_bits": 512,
    "design_id": "gpt2_deepseek_v4pro_20261020",
    "element_bits": {
      "block_input_bits": 8,
      "block_output_bits": 8,
      "internal_elem_bits": 8
    },
    "layout_policy": "aligned_static_regions_with_double_buffered_layer_weights",
    "num_layers": 12,
    "regions": [
      {
        "alignment_bytes": 64,
        "base_addr": 0,
        "meta": {
          "stage3_size_bytes": 12288,
          "stage3_size_bytes_formula": "semantic block-input tensor elements * declared block-input bits / 8"
        },
        "name": "input_tokens",
        "role": "activation_input",
        "size_bytes": 12288
      },
      {
        "alignment_bytes": 64,
        "base_addr": 12288,
        "meta": {
          "stage3_size_bytes": 12288,
          "stage3_size_bytes_formula": "semantic block-output tensor elements * declared block-output bits / 8"
        },
        "name": "output_tokens",
        "role": "activation_output",
        "size_bytes": 12288
      },
      {
        "alignment_bytes": 64,
        "base_addr": 24576,
        "meta": {
          "stage3_size_bytes": 49152,
          "stage3_size_bytes_formula": "max(declared semantic stage input/output tensor bytes)"
        },
        "name": "activation_ping",
        "role": "activation_buffer",
        "size_bytes": 49152
      },
      {
        "alignment_bytes": 64,
        "base_addr": 73728,
        "meta": {
          "stage3_size_bytes": 49152,
          "stage3_size_bytes_formula": "same as activation_ping"
        },
        "name": "activation_pong",
        "role": "activation_buffer",
        "size_bytes": 49152
      },
      {
        "alignment_bytes": 64,
        "base_addr": 122880,
        "meta": {
          "stage3_size_bytes": 3568128,
          "stage3_size_bytes_formula": "sum(model-semantic weight_storage_terms)"
        },
        "name": "weight_buffer_a",
        "role": "weight_buffer",
        "size_bytes": 3568128
      },
      {
        "alignment_bytes": 64,
        "base_addr": 3691008,
        "meta": {
          "stage3_size_bytes": 3568128,
          "stage3_size_bytes_formula": "same as weight_buffer_a"
        },
        "name": "weight_buffer_b",
        "role": "weight_buffer",
        "size_bytes": 3568128
      },
      {
        "alignment_bytes": 64,
        "base_addr": 7259136,
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
      "hidden_size": 768,
      "intermediate_size": 3072,
      "num_kv_heads": 12,
      "num_q_heads": 12,
      "seq_len": 16
    },
    "total_bytes": 7259200,
    "transfer_rules": [
      "all addresses are byte offsets from the accelerator DDR window base",
      "all transfer byte counts are aligned to axi_data_width_bits",
      "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes"
    ],
    "weight_storage_terms": [
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_1_weight",
        "physical_role": "weight",
        "stage": "layer_norm_1"
      },
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_1_bias",
        "physical_role": "weight",
        "stage": "layer_norm_1"
      },
      {
        "bytes": 884736,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 1769472,
        "factors": [
          "hidden_size",
          3,
          "num_q_heads",
          "head_dim"
        ],
        "id": "attn_c_attn_weight",
        "physical_role": "weight_qkv",
        "stage": "self_attention"
      },
      {
        "bytes": 9216,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 2304,
        "factors": [
          3,
          "num_q_heads",
          "head_dim"
        ],
        "id": "attn_c_attn_bias",
        "physical_role": "weight_qkv_bias",
        "stage": "self_attention"
      },
      {
        "bytes": 294912,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 589824,
        "factors": [
          "hidden_size",
          "hidden_size"
        ],
        "id": "attn_c_proj_weight",
        "physical_role": "weight_attn_out",
        "stage": "self_attention"
      },
      {
        "bytes": 3072,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "attn_c_proj_bias",
        "physical_role": "weight_attn_out_bias",
        "stage": "self_attention"
      },
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_2_weight",
        "physical_role": "weight",
        "stage": "layer_norm_2"
      },
      {
        "bytes": 384,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "ln_2_bias",
        "physical_role": "weight",
        "stage": "layer_norm_2"
      },
      {
        "bytes": 1179648,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 2359296,
        "factors": [
          "hidden_size",
          "intermediate_size"
        ],
        "id": "mlp_c_fc_weight",
        "physical_role": "weight_mlp_up",
        "stage": "mlp_fc"
      },
      {
        "bytes": 12288,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 3072,
        "factors": [
          "intermediate_size"
        ],
        "id": "mlp_c_fc_bias",
        "physical_role": "weight_mlp_up_bias",
        "stage": "mlp_fc"
      },
      {
        "bytes": 1179648,
        "dtype_role": "weight",
        "element_bits": 4,
        "elements": 2359296,
        "factors": [
          "intermediate_size",
          "hidden_size"
        ],
        "id": "mlp_c_proj_weight",
        "physical_role": "weight_mlp_down",
        "stage": "mlp_proj"
      },
      {
        "bytes": 3072,
        "dtype_role": "weight",
        "element_bits": 32,
        "elements": 768,
        "factors": [
          "hidden_size"
        ],
        "id": "mlp_c_proj_bias",
        "physical_role": "weight_mlp_down_bias",
        "stage": "mlp_proj"
      }
    ]
  },
  "outputs": {
    "code_generation_manifest": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/code_generation_manifest.json",
    "compile_gate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/compile_check.json",
    "contract_check": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/codegen_contract_check.json",
    "generated_code_package": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel",
    "llm_agent": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/llm/code_generation_agent_result.json",
    "memory_layout": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/memory/memory_layout.json",
    "runtime_config": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/runtime/runtime_config.json",
    "sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/sacg_state.json",
    "team_aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/team/team_aggregate.json",
    "team_subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/team/subtask_plan.json"
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
    "log_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/logs/codegen_package_static_check.json",
    "schema_version": "spatialaccagent.codegen_package_static_check.v0",
    "status": "pass",
    "summary": "generated package manifest is structurally complete",
    "warnings": []
  },
  "planned_code_outputs": [
    "generated.model_ir",
    "generated.arch_plan",
    "generated.chisel_modules",
    "generated.fpga_ip_simulation_closure",
    "generated.top_wrapper",
    "generated.fpga_axi_ddr_top_wrapper",
    "generated.performance_counter",
    "generated.memory_layout",
    "generated.runtime_config",
    "generated.scala_contract_check",
    "generated.codegen_compile_gate",
    "generated.codegen_contract_check"
  ],
  "runtime_config": {
    "board": {
      "board_document_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/board/mimic_computer_v6.0\u677f\u5361\u4f7f\u7528\u6587\u6863.docx",
      "board_name": "mimic_computer_v6.0",
      "fpga_part": "xcvu9p_CIV-flgb2104-2-i",
      "resource_budget": {
        "bram": 2160,
        "bram18": 4320,
        "bram36": 2160,
        "dsp": 6840,
        "ff": 2364480,
        "lut": 1182240,
        "uram": 960
      },
      "resource_budget_source": "real_vivado_target_part_probe"
    },
    "chisel_top": "GPT2PreLNBlock",
    "design_id": "gpt2_deepseek_v4pro_20261020",
    "memory_layout": {
      "alignment_bytes": 64,
      "axi_data_width_bits": 512,
      "design_id": "gpt2_deepseek_v4pro_20261020",
      "element_bits": {
        "block_input_bits": 8,
        "block_output_bits": 8,
        "internal_elem_bits": 8
      },
      "layout_policy": "aligned_static_regions_with_double_buffered_layer_weights",
      "num_layers": 12,
      "regions": [
        {
          "alignment_bytes": 64,
          "base_addr": 0,
          "meta": {
            "stage3_size_bytes": 12288,
            "stage3_size_bytes_formula": "semantic block-input tensor elements * declared block-input bits / 8"
          },
          "name": "input_tokens",
          "role": "activation_input",
          "size_bytes": 12288
        },
        {
          "alignment_bytes": 64,
          "base_addr": 12288,
          "meta": {
            "stage3_size_bytes": 12288,
            "stage3_size_bytes_formula": "semantic block-output tensor elements * declared block-output bits / 8"
          },
          "name": "output_tokens",
          "role": "activation_output",
          "size_bytes": 12288
        },
        {
          "alignment_bytes": 64,
          "base_addr": 24576,
          "meta": {
            "stage3_size_bytes": 49152,
            "stage3_size_bytes_formula": "max(declared semantic stage input/output tensor bytes)"
          },
          "name": "activation_ping",
          "role": "activation_buffer",
          "size_bytes": 49152
        },
        {
          "alignment_bytes": 64,
          "base_addr": 73728,
          "meta": {
            "stage3_size_bytes": 49152,
            "stage3_size_bytes_formula": "same as activation_ping"
          },
          "name": "activation_pong",
          "role": "activation_buffer",
          "size_bytes": 49152
        },
        {
          "alignment_bytes": 64,
          "base_addr": 122880,
          "meta": {
            "stage3_size_bytes": 3568128,
            "stage3_size_bytes_formula": "sum(model-semantic weight_storage_terms)"
          },
          "name": "weight_buffer_a",
          "role": "weight_buffer",
          "size_bytes": 3568128
        },
        {
          "alignment_bytes": 64,
          "base_addr": 3691008,
          "meta": {
            "stage3_size_bytes": 3568128,
            "stage3_size_bytes_formula": "same as weight_buffer_a"
          },
          "name": "weight_buffer_b",
          "role": "weight_buffer",
          "size_bytes": 3568128
        },
        {
          "alignment_bytes": 64,
          "base_addr": 7259136,
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
        "hidden_size": 768,
        "intermediate_size": 3072,
        "num_kv_heads": 12,
        "num_q_heads": 12,
        "seq_len": 16
      },
      "total_bytes": 7259200,
      "transfer_rules": [
        "all addresses are byte offsets from the accelerator DDR window base",
        "all transfer byte counts are aligned to axi_data_width_bits",
        "weight_buffer_a and weight_buffer_b alternate by layer to allow prefetch of layer N+1 while layer N computes"
      ],
      "weight_storage_terms": [
        {
          "bytes": 384,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 768,
          "factors": [
            "hidden_size"
          ],
          "id": "ln_1_weight",
          "physical_role": "weight",
          "stage": "layer_norm_1"
        },
        {
          "bytes": 384,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 768,
          "factors": [
            "hidden_size"
          ],
          "id": "ln_1_bias",
          "physical_role": "weight",
          "stage": "layer_norm_1"
        },
        {
          "bytes": 884736,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 1769472,
          "factors": [
            "hidden_size",
            3,
            "num_q_heads",
            "head_dim"
          ],
          "id": "attn_c_attn_weight",
          "physical_role": "weight_qkv",
          "stage": "self_attention"
        },
        {
          "bytes": 9216,
          "dtype_role": "weight",
          "element_bits": 32,
          "elements": 2304,
          "factors": [
            3,
            "num_q_heads",
            "head_dim"
          ],
          "id": "attn_c_attn_bias",
          "physical_role": "weight_qkv_bias",
          "stage": "self_attention"
        },
        {
          "bytes": 294912,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 589824,
          "factors": [
            "hidden_size",
            "hidden_size"
          ],
          "id": "attn_c_proj_weight",
          "physical_role": "weight_attn_out",
          "stage": "self_attention"
        },
        {
          "bytes": 3072,
          "dtype_role": "weight",
          "element_bits": 32,
          "elements": 768,
          "factors": [
            "hidden_size"
          ],
          "id": "attn_c_proj_bias",
          "physical_role": "weight_attn_out_bias",
          "stage": "self_attention"
        },
        {
          "bytes": 384,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 768,
          "factors": [
            "hidden_size"
          ],
          "id": "ln_2_weight",
          "physical_role": "weight",
          "stage": "layer_norm_2"
        },
        {
          "bytes": 384,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 768,
          "factors": [
            "hidden_size"
          ],
          "id": "ln_2_bias",
          "physical_role": "weight",
          "stage": "layer_norm_2"
        },
        {
          "bytes": 1179648,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 2359296,
          "factors": [
            "hidden_size",
            "intermediate_size"
          ],
          "id": "mlp_c_fc_weight",
          "physical_role": "weight_mlp_up",
          "stage": "mlp_fc"
        },
        {
          "bytes": 12288,
          "dtype_role": "weight",
          "element_bits": 32,
          "elements": 3072,
          "factors": [
            "intermediate_size"
          ],
          "id": "mlp_c_fc_bias",
          "physical_role": "weight_mlp_up_bias",
          "stage": "mlp_fc"
        },
        {
          "bytes": 1179648,
          "dtype_role": "weight",
          "element_bits": 4,
          "elements": 2359296,
          "factors": [
            "intermediate_size",
            "hidden_size"
          ],
          "id": "mlp_c_proj_weight",
          "physical_role": "weight_mlp_down",
          "stage": "mlp_proj"
        },
        {
          "bytes": 3072,
          "dtype_role": "weight",
          "element_bits": 32,
          "elements": 768,
          "factors": [
            "hidden_size"
          ],
          "id": "mlp_c_proj_bias",
          "physical_role": "weight_mlp_down_bias",
          "stage": "mlp_proj"
        }
      ]
    },
    "params": {
      "acc_bits": 32,
      "activation_banks": 4,
      "activation_memory": "xpm_bram",
      "board_axi_data_width_bits": 512,
      "burst_beats": 1,
      "cache_refill_data_width_bits": 512,
      "cache_tile_count": 2,
      "cache_tile_words": 256,
      "clock_target_mhz": 0,
      "compute_backend": "integer_dsp",
      "cross_token_reuse_tokens": 8,
      "elem_bits": 8,
      "fifo_depth": 128,
      "fifo_memory": "xpm_bram",
      "head_dim": 64,
      "hidden_size": 768,
      "input_bits": 8,
      "integer_mode": true,
      "intermediate_size": 3072,
      "lanes": 16,
      "large_cache_memory": "xpm_uram",
      "max_seq_len": 16,
      "num_kv_heads": 12,
      "num_q_heads": 12,
      "output_bits": 8,
      "pipeline_depth": 1,
      "rounding_mode": "nearest_even",
      "saturation_enabled": true,
      "scale_bits": 32,
      "scale_shift": 31,
      "weight_banks": 1,
      "weight_banks_by_role": {
        "weight": 1,
        "weight_attn_out": 1,
        "weight_attn_out_bias": 1,
        "weight_mlp_down": 1,
        "weight_mlp_down_bias": 1,
        "weight_mlp_up": 1,
        "weight_mlp_up_bias": 1,
        "weight_qkv": 1,
        "weight_qkv_bias": 1
      },
      "weight_bits": 4,
      "weight_memory": "xpm_uram"
    },
    "pass_criteria": {
      "bit_exact_float_model": false,
      "required": [
        "no_deadlock",
        "done_asserted",
        "valid_output_bytes"
      ]
    },
    "performance_counter": {
      "counter_source": "synthesizable_dut_counter",
      "counter_width_bits": 64,
      "counting_rule": "exclude the accepted start edge and include the completion edge",
      "cycles_signal": "performanceCycles",
      "end_event": "final_output_transfer",
      "qor_metric_inputs": [
        "clock_frequency_mhz",
        "performance_tokens_per_second"
      ],
      "start_event": "accepted_run_start",
      "valid_signal": "performanceValid"
    },
    "physical_implementation": {
      "acc_bits": 32,
      "activation_banks": 4,
      "activation_memory": "xpm_bram",
      "burst_beats": 1,
      "cache_refill_data_width_bits": 512,
      "cache_tile_count": 2,
      "cache_tile_words": 256,
      "compute_backend": "integer_dsp",
      "cross_token_reuse_tokens": 8,
      "elem_bits": 8,
      "fifo_depth": 128,
      "fifo_memory": "xpm_bram",
      "integer_mode": true,
      "large_cache_memory": "xpm_uram",
      "pipeline_depth": 1,
      "rounding_mode": "nearest_even",
      "saturation_enabled": true,
      "scale_bits": 32,
      "scale_shift": 31,
      "weight_banks": 1,
      "weight_banks_by_role": {
        "weight": 1,
        "weight_attn_out": 1,
        "weight_attn_out_bias": 1,
        "weight_mlp_down": 1,
        "weight_mlp_down_bias": 1,
        "weight_mlp_up": 1,
        "weight_mlp_up_bias": 1,
        "weight_qkv": 1,
        "weight_qkv_bias": 1
      },
      "weight_bits": 4,
      "weight_memory": "xpm_uram"
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
      "c2h_device_template": "/dev/xdma${XDMA_ID}_c2h_0",
      "control_protocol": "xdma_raw_register_and_ddr",
      "ctrl_base": "0x3000000000",
      "ddr_base": "0x2800000000",
      "ddr_image_default": "/home/test/pyjm12_alllayers_9p_fullseq/pyjm12_alllayers_9p_fullseq/artifacts/ddr_image.u32.bin",
      "h2c_device_template": "/dev/xdma${XDMA_ID}_h2c_0",
      "mimic_dir": "/home/test/mimic_driver_c6",
      "output_abs": "0x28092f1000",
      "remote_host": "hyyuan@10.12.133.23",
      "xdma_id_default": 1
    },
    "schema_version": "spatialaccagent.runtime_config.v0",
    "top_module": "GeneratedAxiDdrTop"
  },
  "sacg_transition_id": "transition.0004",
  "schema_version": "spatialaccagent.code_generation_report.v0",
  "source_sacg_state": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/sacg_state.json",
  "stage": "code_generation",
  "status": "ready",
  "team_executable_actions": []
}
</recent_stage_summary>

<command>
[
  "/usr/bin/python3",
  "-m",
  "accagent.framework.stage_code_generation",
  "--sacg-state",
  "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/sacg_state.json"
]
</command>

<command_returncode>
0
</command_returncode>

<command_log>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/agent/logs/06_code_generation.json
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
        "artifact.stage4.dse_search_space",
        "artifact.stage4.dse_candidate_records",
        "artifact.stage4.dse_constraint_report",
        "artifact.stage4.dse_pareto_frontier",
        "artifact.stage4.dse_measurements",
        "artifact.stage4.selected_architecture",
        "artifact.stage4.dse_selection_rationale",
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
      "timestamp": "2026-10-20T12:57:18+00:00",
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
      "summary": "completed 6 compile/elaboration command(s)",
      "timestamp": "2026-10-20T13:04:51+00:00",
      "transition_id": "transition.0004"
    }
  ],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/sacg_state.json
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
  "model": "deepseek-v4-pro",
  "model_selection_policy": "An explicit runtime model selection is authoritative and is recorded with the stage worker; it does not require a duplicate approval artifact.",
  "policy": "LLM planning/review is mandatory for agentic stages when enforce=true; fallback records are diagnostics only and must not be consumed as successful agent decisions.",
  "reasoning_effort": "medium",
  "requested_model_override": "deepseek-v4-pro",
  "schema_version": "spatialaccagent.llm_policy.v0"
}
</llm_policy>

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
