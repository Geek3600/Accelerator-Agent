<agent>
code_generation_agent
</agent>

<task>
Review the accelerator code generation manifest, generated code package, and team handoff for missing cross-layer design outputs.
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

<candidate_artifact_manifest>
{
  "candidate_only": true,
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
  "constraints_touched": [
    "constraint.codegen.package",
    "constraint.codegen.compile_gate",
    "constraint.codegen.contract_check",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.deployment.board"
  ],
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
  "final_manifest_path": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/code_generation/code_generation_manifest.json",
  "generated_code_outputs": [
    {
      "depends_on": [
        "artifact.input.model_config"
      ],
      "id": "generated.model_ir",
      "kind": "model_ir",
      "status": "generated"
    },
    {
      "depends_on": [
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding"
      ],
      "id": "generated.arch_plan",
      "kind": "architecture_plan",
      "status": "generated"
    },
    {
      "id": "generated.chisel_modules",
      "kind": "chisel",
      "selected_operator_template_sources": [
        "Activation.scala",
        "Attention.scala",
        "DecoderBlock.scala",
        "FFN.scala",
        "Mask.scala",
        "Norm.scala",
        "Residual.scala",
        "Softmax.scala"
      ],
      "status": "generated",
      "template_sources": [
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
      ]
    },
    {
      "depends_on": [
        "generated.chisel_modules"
      ],
      "id": "generated.fpga_ip_simulation_closure",
      "kind": "fpga_ip_simulation_closure",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.top_wrapper",
      "kind": "top_wrapper",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.top_wrapper",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.fpga_axi_ddr_top_wrapper",
      "kind": "fpga_axi_ddr_top_wrapper",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.fpga_axi_ddr_top_wrapper",
        "generated.runtime_config"
      ],
      "id": "generated.performance_counter",
      "kind": "synthesizable_performance_counter",
      "status": "generated"
    },
    {
      "depends_on": [
        "artifact.stage4.parameter_binding",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.memory_layout",
      "kind": "memory_layout",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.memory_layout",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.runtime_config",
      "kind": "runtime_config",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "artifact.stage4.parameter_binding"
      ],
      "id": "generated.scala_contract_check",
      "kind": "scala_contract_check",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "generated.top_wrapper",
        "generated.fpga_axi_ddr_top_wrapper"
      ],
      "id": "generated.codegen_compile_gate",
      "kind": "compile_gate",
      "status": "pass"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "generated.memory_layout",
        "generated.runtime_config",
        "generated.codegen_compile_gate"
      ],
      "id": "generated.codegen_contract_check",
      "kind": "contract_check",
      "status": "pass"
    }
  ],
  "generated_files": [
    "generated/chisel/Activation.sv",
    "generated/chisel/Attention.sv",
    "generated/chisel/DenseFFN.sv",
    "generated/chisel/GPT2PreLNBlock.sv",
    "generated/chisel/GeneratedAcceleratorTop.sv",
    "generated/chisel/GeneratedAxiDdrTop.sv",
    "generated/chisel/IntegerAttention.sv",
    "generated/chisel/IntegerVectorNorm.sv",
    "generated/chisel/Linear.sv",
    "generated/chisel/Linear_1.sv",
    "generated/chisel/Linear_2.sv",
    "generated/chisel/Linear_3.sv",
    "generated/chisel/PhysicalIntegerSqrt.sv",
    "generated/chisel/PhysicalLinearAdd.sv",
    "generated/chisel/PhysicalLinearMul.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_12.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_14.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_15.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_16.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_17.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_2.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_25.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_28.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_3.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_32.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_36.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_4.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_5.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_6.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_7.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_8.sv",
    "generated/chisel/PhysicalSimpleDualPortMemory_9.sv",
    "generated/chisel/PhysicalStreamFifo.sv",
    "generated/chisel/PhysicalStreamFifo_3.sv",
    "generated/chisel/PhysicalStreamFifo_7.sv",
    "generated/chisel/QKVProjection.sv",
    "generated/chisel/README.md",
    "generated/chisel/ResidualAdd.sv",
    "generated/chisel/VectorNorm.sv",
    "generated/chisel/WeightTileCache.sv",
    "generated/chisel/WeightTileCache_1.sv",
    "generated/chisel/WeightTileCache_2.sv",
    "generated/chisel/WeightTileServiceMux.sv",
    "generated/chisel/build.sbt",
    "generated/chisel/filelist.f",
    "generated/chisel/logs/codegen_contract_check.json",
    "generated/chisel/logs/codegen_package_static_check.json",
    "generated/chisel/logs/compile_check.json",
    "generated/chisel/logs/dse_physical_binding_check.json",
    "generated/chisel/memory/memory_layout.json",
    "generated/chisel/project/build.properties",
    "generated/chisel/project/target/config-classes/$c9ee876ec3eb95f78e43$.class",
    "generated/chisel/project/target/config-classes/$c9ee876ec3eb95f78e43.cache",
    "generated/chisel/project/target/config-classes/$c9ee876ec3eb95f78e43.class",
    "generated/chisel/project/target/config-classes/$edbb0dd1284013ce9485$.class",
    "generated/chisel/project/target/config-classes/$edbb0dd1284013ce9485.cache",
    "generated/chisel/project/target/config-classes/$edbb0dd1284013ce9485.class",
    "generated/chisel/project/target/config-classes/$ee7405b860434bc224b5$.class",
    "generated/chisel/project/target/config-classes/$ee7405b860434bc224b5.cache",
    "generated/chisel/project/target/config-classes/$ee7405b860434bc224b5.class",
    "generated/chisel/project/target/scala-2.12/sbt-1.0/sync/copy-resource",
    "generated/chisel/project/target/scala-2.12/sbt-1.0/update/update_cache_2.12/inputs",
    "generated/chisel/project/target/scala-2.12/sbt-1.0/update/update_cache_2.12/output",
    "generated/chisel/project/target/streams/_global/_global/_global/streams/out",
    "generated/chisel/project/target/streams/_global/_global/csrLogger/_global/streams/out",
    "generated/chisel/project/target/streams/_global/csrConfiguration/_global/streams/out",
    "generated/chisel/project/target/streams/_global/csrProject/_global/streams/out",
    "generated/chisel/project/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.12/input_dsp",
    "generated/chisel/project/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.12/output_dsp",
    "generated/chisel/project/target/streams/_global/ivyConfiguration/_global/streams/out",
    "generated/chisel/project/target/streams/_global/ivySbt/_global/streams/out",
    "generated/chisel/project/target/streams/_global/moduleSettings/_global/streams/out",
    "generated/chisel/project/target/streams/_global/projectDescriptors/_global/streams/out",
    "generated/chisel/project/target/streams/_global/scalaCompilerBridgeScope/_global/streams/out",
    "generated/chisel/project/target/streams/_global/update/_global/streams/out",
    "generated/chisel/project/target/streams/compile/_global/_global/compileOutputs/previous",
    "generated/chisel/project/target/streams/compile/_global/_global/discoveredMainClasses/data",
    "generated/chisel/project/target/streams/compile/bspReporter/_global/streams/out",
    "generated/chisel/project/target/streams/compile/compile/_global/streams/out",
    "generated/chisel/project/target/streams/compile/compileIncremental/_global/streams/export",
    "generated/chisel/project/target/streams/compile/compileIncremental/_global/streams/out",
    "generated/chisel/project/target/streams/compile/copyResources/_global/streams/out",
    "generated/chisel/project/target/streams/compile/dependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/exportedProducts/_global/streams/export",
    "generated/chisel/project/target/streams/compile/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/incOptions/_global/streams/out",
    "generated/chisel/project/target/streams/compile/internalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/internalDependencyClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/compile/managedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/scalacOptions/_global/streams/out",
    "generated/chisel/project/target/streams/compile/unmanagedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/compile/unmanagedClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/compile/unmanagedJars/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/dependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/exportedProducts/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/fullClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/internalDependencyClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/internalDependencyClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/runtime/managedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/unmanagedClasspath/_global/streams/export",
    "generated/chisel/project/target/streams/runtime/unmanagedClasspath/_global/streams/out",
    "generated/chisel/project/target/streams/runtime/unmanagedJars/_global/streams/export",
    "generated/chisel/runtime/runtime_config.json",
    "generated/chisel/scripts/compile_check.sh",
    "generated/chisel/scripts/elaborate.sh",
    "generated/chisel/simulation/fpga_ip_modules.txt",
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
    "generated/chisel/src/main/scala/spatialaccagent/templates/WeightTileCache.scala",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAccelerator.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAcceleratorVivado$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAcceleratorVivado$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAcceleratorVivado.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTop.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTopVivado$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTopVivado$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/ElaborateGeneratedAxiDdrTopVivado.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAcceleratorTop$$anon$1$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAcceleratorTop$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAcceleratorTop.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAxiDdrTop$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedAxiDdrTop.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedContractCheck$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedContractCheck$delayedInit$body.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedContractCheck.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedDesignParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedDesignParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedSACGMetadata$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/generated/GeneratedSACGMetadata.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/exp2_fraction_q24.mem",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/exp2_fraction_q24.memh",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/sigmoid_pwl_q18.mem",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/sigmoid_pwl_q18.memh",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/numeric/transcendental_approximation_contract.json",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AccMath$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AccMath.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Activation$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Activation.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationGELUNew.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationGELUTanh.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationReLU.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ActivationSiLU.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Attention$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Attention.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionGQA.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMHA.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMQA.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMask$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMask.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMaskParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionMaskParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/AttentionParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlock$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DecoderBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFN$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFN.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFNParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseFFNParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/DenseMLP.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMul$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMul.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMulParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ElementwiseMulParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingAttention$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingAttention.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingRoPE$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingRoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingVectorNorm$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/FloatingVectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GPT2PreLNBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLP$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLP.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLPParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/GatedMLPParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlock$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Gemma3TextBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IeeeMath$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IeeeMath.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Int8QuantPorts.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerAttention$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerAttention.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerRoPE$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerRoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerSoftmax$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerSoftmax.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerVectorNorm$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/IntegerVectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCache$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCache.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCacheParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/KVCacheParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Linear$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Linear.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearScaleMetadata.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LinearScalePorts.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlock$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlockParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/LlamaStyleBlockParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/OPTPreLNBlock.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ParametricLinearInt8ToFP32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ParametricLinearInt8ToInt8.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp16ToFp32$$anon$11.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp16ToFp32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Add.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32AddPipeline.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Binary$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Binary$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Binary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32CompareLt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Div.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Mul.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32MulPipeline.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Sqrt$$anon$8.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Sqrt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32Sub.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToFp16$$anon$12.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToFp16.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToSigned$$anon$13.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFp32ToSigned.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFpLatency$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalFpLatency.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalImplementation$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalImplementation.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalIntegerSqrt$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalIntegerSqrt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearAdd$$anon$6$$anon$7.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearAdd$$anon$6.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearAdd.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul$$anon$4$$anon$5.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul$$anon$4.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalLinearMul.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalMath$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalMath.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalRom$$anon$10.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalRom.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSignedToFp32$$anon$15.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSignedToFp32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSimpleDualPortMemory$$anon$17.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalSimpleDualPortMemory.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalStreamFifo$$anon$18.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalStreamFifo.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalTaggedFp32Binary$$anon$2$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalTaggedFp32Binary$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalTaggedFp32Binary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalUIntToFp32$$anon$14.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/PhysicalUIntToFp32.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNorm$$anon$5.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjection$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjection.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjectionParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjectionParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVProjector.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/QKVStreamBeat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Qwen2Block.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNorm$$anon$4.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RMSNormQ.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualAdd$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualAdd.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/ResidualParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPE$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPE.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEApply.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/RoPEParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Softmax$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/Softmax.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/SoftmaxParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/SoftmaxParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StageConfig.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamBeat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamSpec$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/StreamSpec.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/TaggedFp32Result.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNorm$$anon$3.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNorm.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNormParams$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VectorNormParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpBinary$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpBinary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpFloatToInt.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpIntToFloat.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/VivadoFpUnary.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileCache$$anon$2.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileCache$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileCache.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileRequest.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileResponse$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileResponse.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceIO$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceIO.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceMux$$anon$1.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceMux$.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightTileServiceMux.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WeightWrite.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/WideRefillParams.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSimpleDualPort$$anon$16.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSimpleDualPort.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSinglePortRom$$anon$9.class",
    "generated/chisel/target/scala-2.13/classes/spatialaccagent/templates/XpmSinglePortRom.class",
    "generated/chisel/target/scala-2.13/spatialaccagent-generated_2.13-0.1.0.jar",
    "generated/chisel/target/scala-2.13/sync/copy-resource",
    "generated/chisel/target/scala-2.13/update/update_cache_2.13/inputs",
    "generated/chisel/target/scala-2.13/update/update_cache_2.13/output",
    "generated/chisel/target/scala-2.13/zinc/inc_compile_2.13.zip",
    "generated/chisel/target/streams/_global/_global/_global/streams/out",
    "generated/chisel/target/streams/_global/_global/csrLogger/_global/streams/out",
    "generated/chisel/target/streams/_global/csrConfiguration/_global/streams/out",
    "generated/chisel/target/streams/_global/csrProject/_global/streams/out",
    "generated/chisel/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.13/input_dsp",
    "generated/chisel/target/streams/_global/dependencyPositions/_global/streams/update_cache_2.13/output_dsp",
    "generated/chisel/target/streams/_global/ivyConfiguration/_global/streams/out",
    "generated/chisel/target/streams/_global/ivySbt/_global/streams/out",
    "generated/chisel/target/streams/_global/moduleSettings/_global/streams/out",
    "generated/chisel/target/streams/_global/projectDescriptors/_global/streams/out",
    "generated/chisel/target/streams/_global/scalaCompilerBridgeScope/_global/streams/out",
    "generated/chisel/target/streams/_global/update/_global/streams/out",
    "generated/chisel/target/streams/compile/_global/_global/compileOutputs/previous",
    "generated/chisel/target/streams/compile/_global/_global/discoveredMainClasses/data",
    "generated/chisel/target/streams/compile/bspReporter/_global/streams/out",
    "generated/chisel/target/streams/compile/compile/_global/streams/out",
    "generated/chisel/target/streams/compile/compileIncremental/_global/streams/export",
    "generated/chisel/target/streams/compile/compileIncremental/_global/streams/out",
    "generated/chisel/target/streams/compile/copyResources/_global/streams/out",
    "generated/chisel/target/streams/compile/dependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/exportedProductJars/_global/streams/export",
    "generated/chisel/target/streams/compile/exportedProducts/_global/streams/export",
    "generated/chisel/target/streams/compile/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/incOptions/_global/streams/out",
    "generated/chisel/target/streams/compile/internalDependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/internalDependencyClasspath/_global/streams/out",
    "generated/chisel/target/streams/compile/mainClass/_global/streams/out",
    "generated/chisel/target/streams/compile/managedClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/packageBin/_global/streams/inputs",
    "generated/chisel/target/streams/compile/packageBin/_global/streams/out",
    "generated/chisel/target/streams/compile/packageBin/_global/streams/output",
    "generated/chisel/target/streams/compile/scalacOptions/_global/streams/out",
    "generated/chisel/target/streams/compile/unmanagedClasspath/_global/streams/export",
    "generated/chisel/target/streams/compile/unmanagedClasspath/_global/streams/out",
    "generated/chisel/target/streams/compile/unmanagedJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/dependencyClasspathAsJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/exportedProductJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/externalDependencyClasspath/_global/streams/export",
    "generated/chisel/target/streams/runtime/fullClasspathAsJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/internalDependencyAsJars/_global/streams/export",
    "generated/chisel/target/streams/runtime/internalDependencyAsJars/_global/streams/out",
    "generated/chisel/target/streams/runtime/managedClasspath/_global/streams/export",
    "generated/chisel/target/streams/runtime/unmanagedClasspath/_global/streams/export",
    "generated/chisel/target/streams/runtime/unmanagedClasspath/_global/streams/out",
    "generated/chisel/target/streams/runtime/unmanagedJars/_global/streams/export",
    "generated/chisel/verification/assert/layers-GeneratedAcceleratorTop-Verification-Assert.sv",
    "generated/chisel/verification/assert/layers-GeneratedAxiDdrTop-Verification-Assert.sv",
    "generated/chisel/verification/assume/layers-GeneratedAcceleratorTop-Verification-Assume.sv",
    "generated/chisel/verification/assume/layers-GeneratedAxiDdrTop-Verification-Assume.sv",
    "generated/chisel/verification/cover/layers-GeneratedAcceleratorTop-Verification-Cover.sv",
    "generated/chisel/verification/cover/layers-GeneratedAxiDdrTop-Verification-Cover.sv",
    "generated/chisel/verification/layers-GeneratedAcceleratorTop-Verification.sv",
    "generated/chisel/verification/layers-GeneratedAxiDdrTop-Verification.sv",
    "generated/chisel/vivado/Activation.sv",
    "generated/chisel/vivado/Attention.sv",
    "generated/chisel/vivado/DenseFFN.sv",
    "generated/chisel/vivado/GPT2PreLNBlock.sv",
    "generated/chisel/vivado/GeneratedAcceleratorTop.sv",
    "generated/chisel/vivado/GeneratedAxiDdrTop.sv",
    "generated/chisel/vivado/IntegerAttention.sv",
    "generated/chisel/vivado/IntegerVectorNorm.sv",
    "generated/chisel/vivado/Linear.sv",
    "generated/chisel/vivado/Linear_1.sv",
    "generated/chisel/vivado/Linear_2.sv",
    "generated/chisel/vivado/Linear_3.sv",
    "generated/chisel/vivado/PhysicalIntegerSqrt.sv",
    "generated/chisel/vivado/PhysicalLinearAdd.sv",
    "generated/chisel/vivado/PhysicalLinearMul.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_12.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_14.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_15.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_16.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_17.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_2.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_25.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_28.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_3.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_32.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_36.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_4.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_5.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_6.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_7.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_8.sv",
    "generated/chisel/vivado/PhysicalSimpleDualPortMemory_9.sv",
    "generated/chisel/vivado/PhysicalStreamFifo.sv",
    "generated/chisel/vivado/PhysicalStreamFifo_3.sv",
    "generated/chisel/vivado/PhysicalStreamFifo_7.sv",
    "generated/chisel/vivado/QKVProjection.sv",
    "generated/chisel/vivado/ResidualAdd.sv",
    "generated/chisel/vivado/VectorNorm.sv",
    "generated/chisel/vivado/WeightTileCache.sv",
    "generated/chisel/vivado/WeightTileCache_1.sv",
    "generated/chisel/vivado/WeightTileCache_2.sv",
    "generated/chisel/vivado/WeightTileServiceMux.sv",
    "generated/chisel/vivado/filelist.f",
    "generated/chisel/vivado/verification/assert/layers-GeneratedAcceleratorTop-Verification-Assert.sv",
    "generated/chisel/vivado/verification/assert/layers-GeneratedAxiDdrTop-Verification-Assert.sv",
    "generated/chisel/vivado/verification/assume/layers-GeneratedAcceleratorTop-Verification-Assume.sv",
    "generated/chisel/vivado/verification/assume/layers-GeneratedAxiDdrTop-Verification-Assume.sv",
    "generated/chisel/vivado/verification/cover/layers-GeneratedAcceleratorTop-Verification-Cover.sv",
    "generated/chisel/vivado/verification/cover/layers-GeneratedAxiDdrTop-Verification-Cover.sv",
    "generated/chisel/vivado/verification/layers-GeneratedAcceleratorTop-Verification.sv",
    "generated/chisel/vivado/verification/layers-GeneratedAxiDdrTop-Verification.sv"
  ],
  "generated_memory_layout": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/memory/memory_layout.json",
  "generated_package_root": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel",
  "generated_runtime_config": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/generated/chisel/runtime/runtime_config.json",
  "generated_top": {
    "fpga_wrapper_class": "GeneratedAxiDdrTop",
    "param_class": "DecoderBlockParams",
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
    "top_class": "GPT2PreLNBlock"
  },
  "generation_policy": "from_scratch_target_accelerator_package",
  "model_type": "gpt2",
  "note": "This manifest describes template-bound generated accelerator code for the target model; checker/tool evidence is still required before design pass.",
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
  "parameter_binding": {
    "acc_bits": 32,
    "activation_banks": 4,
    "activation_memory": "xpm_bram",
    "burst_beats": 1,
    "cache_refill_data_width_bits": 512,
    "cache_tile_count": 2,
    "cache_tile_words": 256,
    "clock_target_mhz": null,
    "compute_array_cols": 32,
    "compute_array_rows": 16,
    "compute_backend": "integer_dsp",
    "cross_token_reuse_tokens": 8,
    "elem_bits": 8,
    "fifo_depth": 128,
    "fifo_memory": "xpm_bram",
    "input_bits": 8,
    "integer_mode": true,
    "lanes": 16,
    "large_cache_memory": "xpm_uram",
    "output_bits": 8,
    "pipeline_depth": 1,
    "rounding": "nearest_even",
    "saturation": true,
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
  "planned_code_outputs": [
    {
      "depends_on": [
        "artifact.input.model_config"
      ],
      "id": "generated.model_ir",
      "kind": "model_ir",
      "status": "generated"
    },
    {
      "depends_on": [
        "artifact.stage3.pipeline_plan",
        "artifact.stage4.parameter_binding"
      ],
      "id": "generated.arch_plan",
      "kind": "architecture_plan",
      "status": "generated"
    },
    {
      "id": "generated.chisel_modules",
      "kind": "chisel",
      "selected_operator_template_sources": [
        "Activation.scala",
        "Attention.scala",
        "DecoderBlock.scala",
        "FFN.scala",
        "Mask.scala",
        "Norm.scala",
        "Residual.scala",
        "Softmax.scala"
      ],
      "status": "generated",
      "template_sources": [
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
      ]
    },
    {
      "depends_on": [
        "generated.chisel_modules"
      ],
      "id": "generated.fpga_ip_simulation_closure",
      "kind": "fpga_ip_simulation_closure",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.top_wrapper",
      "kind": "top_wrapper",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.top_wrapper",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.fpga_axi_ddr_top_wrapper",
      "kind": "fpga_axi_ddr_top_wrapper",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.fpga_axi_ddr_top_wrapper",
        "generated.runtime_config"
      ],
      "id": "generated.performance_counter",
      "kind": "synthesizable_performance_counter",
      "status": "generated"
    },
    {
      "depends_on": [
        "artifact.stage4.parameter_binding",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.memory_layout",
      "kind": "memory_layout",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.memory_layout",
        "artifact.input.target_board_profile"
      ],
      "id": "generated.runtime_config",
      "kind": "runtime_config",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "artifact.stage4.parameter_binding"
      ],
      "id": "generated.scala_contract_check",
      "kind": "scala_contract_check",
      "status": "generated"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "generated.top_wrapper",
        "generated.fpga_axi_ddr_top_wrapper"
      ],
      "id": "generated.codegen_compile_gate",
      "kind": "compile_gate",
      "status": "pass"
    },
    {
      "depends_on": [
        "generated.chisel_modules",
        "generated.memory_layout",
        "generated.runtime_config",
        "generated.codegen_compile_gate"
      ],
      "id": "generated.codegen_contract_check",
      "kind": "contract_check",
      "status": "pass"
    }
  ],
  "publish_status": "candidate_only",
  "schema_version": "spatialaccagent.code_generation_manifest.v0",
  "selected_operator_template_sources": [
    "Activation.scala",
    "Attention.scala",
    "DecoderBlock.scala",
    "FFN.scala",
    "Mask.scala",
    "Norm.scala",
    "Residual.scala",
    "Softmax.scala"
  ],
  "stage": "code_generation",
  "stage_gate_policy": {
    "current_stage_acceptance": [
      "generated package root, Chisel sources, top wrappers, memory layout, runtime config, and contract checker source must exist",
      "compile/elaboration gate must pass every declared SBT command and expose per-command status/returncode",
      "codegen_contract_check must pass upstream transition, model/shape/numeric, template provenance, compile warning, memory layout, runtime config, and parameter legality checks",
      "target_model_artifact_status.current_artifacts_match_target must be true and missing_for_target must be empty",
      "manifest template_sources must cover every template Scala file copied into the generated package",
      "generated FPGA IP simulation closure must require the same Vivado IP/XPM module interfaces and latencies as implementation"
    ],
    "later_stage_obligations": [
      "Current-source VCS compilation, elaboration, and linking belong to Stage 6, not Stage 5; their absence must not block this code-generation handoff",
      "Vivado synthesis, timing/resource reports, and source-cycle performance analysis belong to Stage 7",
      "clock_target_mhz=0 means the board shell clock is unknown; assigning a nonzero target requires board-profile evidence or approval",
      "memory_layout.json and runtime_config.json are generated handoff artifacts; Stage 6+ must validate them against board/runtime tools before hardware pass claims"
    ],
    "risk_classification_rule": "If current-stage checks pass and no concrete current binding error is evidenced, return ready. candidate_only is the normal pre-publication state, not a failed check. Team audit proposals are not additional required reports; use the supplied contract/static results. Route later tool obligations to proposed_actions rather than blocking Stage 5."
  },
  "status": "ready",
  "target_model_artifact_status": {
    "current_artifacts_match_target": true,
    "missing_for_target": [],
    "model_type": "gpt2",
    "planned_for_target": [
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
    ]
  },
  "template_sources": [
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
  ]
}
</candidate_artifact_manifest>

<stage_gate_policy>
{
  "current_stage_acceptance": [
    "generated package root, Chisel sources, top wrappers, memory layout, runtime config, and contract checker source must exist",
    "compile/elaboration gate must pass every declared SBT command and expose per-command status/returncode",
    "codegen_contract_check must pass upstream transition, model/shape/numeric, template provenance, compile warning, memory layout, runtime config, and parameter legality checks",
    "target_model_artifact_status.current_artifacts_match_target must be true and missing_for_target must be empty",
    "manifest template_sources must cover every template Scala file copied into the generated package",
    "generated FPGA IP simulation closure must require the same Vivado IP/XPM module interfaces and latencies as implementation"
  ],
  "later_stage_obligations": [
    "Current-source VCS compilation, elaboration, and linking belong to Stage 6, not Stage 5; their absence must not block this code-generation handoff",
    "Vivado synthesis, timing/resource reports, and source-cycle performance analysis belong to Stage 7",
    "clock_target_mhz=0 means the board shell clock is unknown; assigning a nonzero target requires board-profile evidence or approval",
    "memory_layout.json and runtime_config.json are generated handoff artifacts; Stage 6+ must validate them against board/runtime tools before hardware pass claims"
  ],
  "risk_classification_rule": "If current-stage checks pass and no concrete current binding error is evidenced, return ready. candidate_only is the normal pre-publication state, not a failed check. Team audit proposals are not additional required reports; use the supplied contract/static results. Route later tool obligations to proposed_actions rather than blocking Stage 5."
}
</stage_gate_policy>

<compile_gate>
{
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
}
</compile_gate>

<contract_check>
{
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
}
</contract_check>

<package_static_check>
{
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
}
</package_static_check>

<design_team>
{
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
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/parameter_binding/sacg_state.json
</source_sacg_state>

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
    }
  ],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

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
