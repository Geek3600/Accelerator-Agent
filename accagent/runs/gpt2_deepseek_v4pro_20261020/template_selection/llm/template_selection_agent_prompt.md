<agent>
template_selection_agent
</agent>

<task>
Review strict template bindings, source/interface checks, attention semantics, team decomposition, and cross-layer gate risks. Apply candidate_template_selection.stage_gate_policy exactly: report only unresolved current Stage 2 blockers in risks, move later simulation/synthesis/code-generation/board bring-up obligations to proposed_actions or approval_required_for. candidate_bound means the complete legal domain is validated and deliberately awaits Stage 4 DSE; it is not an unbound Stage 2 parameter. Treat current source_sha256 and checked_source_hashes as the immutable source identity for this review. Return status='ready' with risks=[] when all current Stage 2 blocks are closed.
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

<candidate_template_selection>
{
  "attention_semantics": {
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
        "activation_policy": "template support alone is not activation; no rotary path may be bound when the model positional encoding is not rope",
        "component": "rope",
        "evidence_pattern": "Module(new RoPE",
        "evidence_type": "hash_bound_template_source",
        "model_position_encoding_type": "learned_absolute",
        "required": false,
        "source": "DecoderBlock.scala",
        "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
        "status": "not_applicable"
      },
      {
        "component": "gqa_head_mapping",
        "evidence_pattern": "kvGroupSize",
        "evidence_type": "hash_bound_template_source",
        "gqa_group_size": 1,
        "params": {
          "num_kv_heads": 12,
          "num_q_heads": 12
        },
        "required": false,
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
  "checker_results": [
    {
      "checker": "operator_coverage_check",
      "errors": [],
      "evidence": {
        "missing_ops": [],
        "required_ops": 8
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_parameter_binding_check",
      "errors": [],
      "evidence": {
        "binding_count": 11
      },
      "status": "pass",
      "warnings": []
    },
    {
      "checker": "template_source_and_interface_check",
      "errors": [],
      "evidence": {
        "checked_templates": 11
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
            "activation_policy": "template support alone is not activation; no rotary path may be bound when the model positional encoding is not rope",
            "component": "rope",
            "evidence_pattern": "Module(new RoPE",
            "evidence_type": "hash_bound_template_source",
            "model_position_encoding_type": "learned_absolute",
            "required": false,
            "source": "DecoderBlock.scala",
            "source_sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
            "status": "not_applicable"
          },
          {
            "component": "gqa_head_mapping",
            "evidence_pattern": "kvGroupSize",
            "evidence_type": "hash_bound_template_source",
            "gqa_group_size": 1,
            "params": {
              "num_kv_heads": 12,
              "num_q_heads": 12
            },
            "required": false,
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
              "control_protocol",
              "ctrl_base",
              "ddr_base",
              "ddr_image_default",
              "h2c_device_template",
              "mimic_dir",
              "output_abs",
              "remote_host",
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
  "constraints_touched": [
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.numeric.policy",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.deployment.board",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.cross_layer.input_consistency"
  ],
  "coverage": {
    "covered_ops": 8,
    "has_block_wrapper": true,
    "required_ops": 8
  },
  "cross_layer_trace": {
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
          "control_protocol",
          "ctrl_base",
          "ddr_base",
          "ddr_image_default",
          "h2c_device_template",
          "mimic_dir",
          "output_abs",
          "remote_host",
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
  "errors": [],
  "forbidden_edits": [
    "Do not close missing template coverage with free-form RTL.",
    "Do not rely on Chisel default constructor values when a model, numeric, or board value is available.",
    "Do not change template internals, data order, memory layout, numeric policy, or board/runtime assumptions without approval.",
    "Do not use HardFloat, SyncReadMem, or a simulation-only arithmetic/memory backend."
  ],
  "fpga_ip_contract": {
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
  "implementation_contract": {
    "disabled_weight_ports": [],
    "loader_ports": [
      "norm1Weight",
      "qkvWeight",
      "qkvBias",
      "attentionOutWeight",
      "attentionOutBias",
      "norm2Weight",
      "ffnUpWeight",
      "ffnUpBias",
      "ffnDownWeight",
      "ffnDownBias"
    ],
    "params": {
      "bindings": {
        "batchSize": "token_count",
        "computeArrayCols": "compute_array_cols",
        "computeArrayRows": "compute_array_rows",
        "elemBits": "elem_bits",
        "headDim": "head_dim",
        "hiddenSize": "hidden_size",
        "inputBits": "input_bits",
        "intermediateSize": "intermediate_size",
        "lanes": "lanes",
        "maxSeqLen": "max_seq_len",
        "numHeads": "num_q_heads",
        "outputBits": "output_bits"
      },
      "class": "DecoderBlockParams"
    },
    "requires_position_input": false,
    "top_class": "GPT2PreLNBlock"
  },
  "library_id": "spatialaccagent_chisel_templates_v0",
  "missing_ops": [],
  "model_type": "gpt2",
  "operator_sequence": [
    "layer_norm_1",
    "self_attention",
    "residual_add_1",
    "layer_norm_2",
    "mlp_fc",
    "activation",
    "mlp_proj",
    "residual_add_2"
  ],
  "parameter_bindings": [
    {
      "bound_params": {
        "compute_array_cols": {
          "candidate_values": [
            4,
            8,
            16,
            32
          ],
          "legal_values": [
            4,
            8,
            16,
            32
          ],
          "planning_value": 4,
          "source": "constraint.arch.design_space.search_params physical candidate universe",
          "status": "candidate_bound",
          "value": null
        },
        "compute_array_rows": {
          "candidate_values": [
            4,
            8,
            16
          ],
          "legal_values": [
            4,
            8,
            16
          ],
          "planning_value": 4,
          "source": "constraint.arch.design_space.search_params physical candidate universe",
          "status": "candidate_bound",
          "value": null
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 64
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "max_seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 12
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "token_count": {
          "source": "constraint.shape.model.target_max_seq_len (one streamed token per sequence position)",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "matched_op": "gpt2_block",
      "missing_params": [],
      "op": "gpt2_block",
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "head_dim",
        "intermediate_size",
        "lanes",
        "compute_array_rows",
        "compute_array_cols",
        "token_count",
        "max_seq_len",
        "input_bits",
        "elem_bits",
        "output_bits"
      ],
      "role": "block_wrapper",
      "source": "DecoderBlock.scala",
      "status": "ready",
      "template_id": "decoder_block"
    },
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-05
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "legality_errors": [],
      "matched_op": "layer_norm",
      "missing_params": [],
      "op": "layer_norm_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 64
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "num_kv_heads": {
          "source": "constraint.shape.model.num_kv_heads",
          "status": "bound",
          "value": 12
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 12
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [],
      "matched_op": "self_attention",
      "missing_params": [],
      "op": "self_attention",
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Attention.scala",
      "status": "ready",
      "template_id": "attention"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "legality_errors": [],
      "matched_op": "residual_add_1",
      "missing_params": [],
      "op": "residual_add_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "status": "ready",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-05
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "legality_errors": [],
      "matched_op": "layer_norm",
      "missing_params": [],
      "op": "layer_norm_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "status": "ready",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [],
      "matched_op": "mlp_fc",
      "missing_params": [],
      "op": "mlp_fc",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "legality_errors": [],
      "matched_op": "activation",
      "missing_params": [],
      "op": "activation",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Activation.scala",
      "status": "ready",
      "template_id": "activation"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "legality_errors": [],
      "matched_op": "mlp_proj",
      "missing_params": [],
      "op": "mlp_proj",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "status": "ready",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "legality_errors": [],
      "matched_op": "residual_add_2",
      "missing_params": [],
      "op": "residual_add_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "status": "ready",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "matched_op": "softmax",
      "missing_params": [],
      "op": "softmax",
      "required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "role": "attention_submodule",
      "source": "Softmax.scala",
      "status": "ready",
      "template_id": "softmax"
    },
    {
      "bound_params": {
        "causal": {
          "source": "artifact.input.model_config.attention.causal",
          "status": "bound",
          "value": true
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "legality_errors": [],
      "matched_op": "causal_mask",
      "missing_params": [],
      "op": "causal_mask",
      "required_params": [
        "seq_len",
        "causal"
      ],
      "role": "attention_submodule",
      "source": "Mask.scala",
      "status": "ready",
      "template_id": "mask"
    }
  ],
  "required_adapters": [],
  "schema_version": "spatialaccagent.template_selection.v0",
  "selected_template_ids": [
    "activation",
    "attention",
    "decoder_block",
    "ffn",
    "mask",
    "norm",
    "residual",
    "softmax"
  ],
  "selected_templates": [
    {
      "candidate_template_ids": [
        "decoder_block"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "runtime"
      ],
      "implementation_constructor_bindings": {
        "batchSize": "token_count",
        "computeArrayCols": "compute_array_cols",
        "computeArrayRows": "compute_array_rows",
        "elemBits": "elem_bits",
        "headDim": "head_dim",
        "hiddenSize": "hidden_size",
        "inputBits": "input_bits",
        "intermediateSize": "intermediate_size",
        "lanes": "lanes",
        "maxSeqLen": "max_seq_len",
        "numHeads": "num_q_heads",
        "outputBits": "output_bits"
      },
      "matched_op": "gpt2_block",
      "op": "gpt2_block",
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "head_dim",
        "intermediate_size",
        "lanes",
        "compute_array_rows",
        "compute_array_cols",
        "token_count",
        "max_seq_len",
        "input_bits",
        "elem_bits",
        "output_bits"
      ],
      "role": "block_wrapper",
      "source": "DecoderBlock.scala",
      "template_id": "decoder_block"
    },
    {
      "candidate_template_ids": [
        "norm"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "matched_op": "layer_norm",
      "op": "layer_norm_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "template_id": "norm"
    },
    {
      "candidate_template_ids": [
        "attention"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory",
        "liveness"
      ],
      "matched_op": "self_attention",
      "op": "self_attention",
      "required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Attention.scala",
      "template_id": "attention"
    },
    {
      "candidate_template_ids": [
        "residual"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "matched_op": "residual_add_1",
      "op": "residual_add_1",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "template_id": "residual"
    },
    {
      "candidate_template_ids": [
        "norm"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "matched_op": "layer_norm",
      "op": "layer_norm_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Norm.scala",
      "template_id": "norm"
    },
    {
      "candidate_template_ids": [
        "ffn"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "matched_op": "mlp_fc",
      "op": "mlp_fc",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "template_id": "ffn"
    },
    {
      "candidate_template_ids": [
        "activation"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "matched_op": "activation",
      "op": "activation",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Activation.scala",
      "template_id": "activation"
    },
    {
      "candidate_template_ids": [
        "ffn"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat",
        "memory"
      ],
      "matched_op": "mlp_proj",
      "op": "mlp_proj",
      "required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "FFN.scala",
      "template_id": "ffn"
    },
    {
      "candidate_template_ids": [
        "residual"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "matched_op": "residual_add_2",
      "op": "residual_add_2",
      "required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "role": "operator",
      "source": "Residual.scala",
      "template_id": "residual"
    },
    {
      "candidate_template_ids": [
        "softmax"
      ],
      "constraints_emitted": [
        "shape",
        "numeric",
        "stream",
        "beat"
      ],
      "matched_op": "softmax",
      "op": "softmax",
      "required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "role": "attention_submodule",
      "source": "Softmax.scala",
      "template_id": "softmax"
    },
    {
      "candidate_template_ids": [
        "mask"
      ],
      "constraints_emitted": [
        "shape",
        "stream",
        "beat"
      ],
      "matched_op": "causal_mask",
      "op": "causal_mask",
      "required_params": [
        "seq_len",
        "causal"
      ],
      "role": "attention_submodule",
      "source": "Mask.scala",
      "template_id": "mask"
    }
  ],
  "stage": "template_selection",
  "stage_gate_policy": {
    "classification_rule": "Put only unresolved current_stage_blocks in risks. Put not_current_stage_blocks in proposed_actions or approval_required_for. The supplied checker evidence is computed from the current source tree: template source/interface records and attention components carry source hashes, while the mandatory FPGA-IP checker scans the complete template directory. Do not require a second future code-generation, simulation, or synthesis audit to accept those current Stage-2 facts. If all deterministic checker_results pass and no concrete contradiction in their current evidence remains, return status='ready' and risks=[].",
    "current_stage_blocks": [
      "any decoder operator has no trusted selected template or explicit required adapter",
      "any selected template required parameter is unbound, illegal, or only supplied by an implicit constructor default when model/numeric/board input has a value",
      "any selected template source file is missing or its metadata required parameters do not match the Chisel case-class constructor",
      "the complete selected template closure contains HardFloat, SyncReadMem, or lacks mandatory Vivado floating-point/XPM bindings",
      "self_attention lacks selected or embedded coverage for Q/K/V projection, RoPE when required, GQA/MQA head mapping, softmax, output projection, required KV-cache behavior, or causal mask",
      "numeric policy, board memory, board runtime, board deployment, or cross-layer input-consistency constraints are absent from the template-selection trace",
      "LLM sub-agent output reports a concrete contradiction in the candidate selection for this stage"
    ],
    "not_current_stage_blocks": [
      "lanes, compute_array_rows, or compute_array_cols has not yet been selected from a Stage-2-validated candidate_bound domain; Stage 4 is the sole concrete DSE selection authority",
      "VCS/Verilator simulation has not been run yet",
      "Vivado synthesis, implementation, timing closure, or bitstream generation has not been run yet",
      "final generated accelerator code has not been emitted yet",
      "runtime driver, board wrapper, or full DDR/AXI top-level integration has not been generated yet",
      "later-stage numeric accuracy or board bring-up evidence is not present yet"
    ],
    "schema_version": "spatialaccagent.stage2_gate_policy.v0"
  },
  "status": "ready",
  "supported_bindings": [
    {
      "bound_params": {
        "compute_array_cols": {
          "candidate_values": [
            4,
            8,
            16,
            32
          ],
          "legal_values": [
            4,
            8,
            16,
            32
          ],
          "planning_value": 4,
          "source": "constraint.arch.design_space.search_params physical candidate universe",
          "status": "candidate_bound",
          "value": null
        },
        "compute_array_rows": {
          "candidate_values": [
            4,
            8,
            16
          ],
          "legal_values": [
            4,
            8,
            16
          ],
          "planning_value": 4,
          "source": "constraint.arch.design_space.search_params physical candidate universe",
          "status": "candidate_bound",
          "value": null
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 64
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "max_seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 12
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "token_count": {
          "source": "constraint.shape.model.target_max_seq_len (one streamed token per sequence position)",
          "status": "bound",
          "value": 16
        }
      },
      "op": "gpt2_block",
      "template_id": "decoder_block"
    },
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-05
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "op": "layer_norm_1",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "head_dim": {
          "source": "constraint.shape.model.head_dim",
          "status": "bound",
          "value": 64
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "num_kv_heads": {
          "source": "constraint.shape.model.num_kv_heads",
          "status": "bound",
          "value": 12
        },
        "num_q_heads": {
          "source": "constraint.shape.model.num_q_heads",
          "status": "bound",
          "value": 12
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "op": "self_attention",
      "template_id": "attention"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "op": "residual_add_1",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "eps": {
          "source": "artifact.input.model_config.norm.eps",
          "status": "bound",
          "value": 1e-05
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "input_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "output_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        }
      },
      "op": "layer_norm_2",
      "template_id": "norm"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "op": "mlp_fc",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "op": "activation",
      "template_id": "activation"
    },
    {
      "bound_params": {
        "acc_bits": {
          "dtype": "int32",
          "source": "constraint.numeric.policy.default_rules.acc_dtype",
          "status": "bound",
          "value": 32
        },
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "intermediate_size": {
          "source": "constraint.shape.model.intermediate_size",
          "status": "bound",
          "value": 3072
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "weight_bits": {
          "dtype": "int4",
          "source": "constraint.numeric.policy.default_rules.weight_dtype",
          "status": "bound",
          "value": 4
        }
      },
      "op": "mlp_proj",
      "template_id": "ffn"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "hidden_size": {
          "source": "constraint.shape.model.hidden_size",
          "status": "bound",
          "value": 768
        },
        "integer_mode": {
          "source": "constraint.numeric.policy.default_rules independent weight/activation/accumulator dtypes",
          "status": "bound",
          "value": true
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        }
      },
      "op": "residual_add_2",
      "template_id": "residual"
    },
    {
      "bound_params": {
        "elem_bits": {
          "dtype": "int8",
          "source": "constraint.numeric.policy.default_rules.activation_dtype",
          "status": "bound",
          "value": 8
        },
        "lanes": {
          "candidate_values": [
            8,
            16
          ],
          "legal_values": [
            8,
            16
          ],
          "planning_value": 8,
          "source": "constraint.arch.design_space.search_params + constraint.memory.board + constraint.numeric.policy",
          "status": "candidate_bound",
          "value": null
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "op": "softmax",
      "template_id": "softmax"
    },
    {
      "bound_params": {
        "causal": {
          "source": "artifact.input.model_config.attention.causal",
          "status": "bound",
          "value": true
        },
        "seq_len": {
          "source": "constraint.shape.model.target_max_seq_len",
          "status": "bound",
          "value": 16
        }
      },
      "op": "causal_mask",
      "template_id": "mask"
    }
  ],
  "template_source_checks": [
    {
      "case_class": "DecoderBlockParams",
      "constructor_binding_names": [
        "hiddenSize",
        "numHeads",
        "headDim",
        "intermediateSize",
        "lanes",
        "computeArrayRows",
        "computeArrayCols",
        "batchSize",
        "maxSeqLen",
        "inputBits",
        "elemBits",
        "outputBits"
      ],
      "constructor_binding_sources": {
        "batchSize": "token_count",
        "computeArrayCols": "compute_array_cols",
        "computeArrayRows": "compute_array_rows",
        "elemBits": "elem_bits",
        "headDim": "head_dim",
        "hiddenSize": "hidden_size",
        "inputBits": "input_bits",
        "intermediateSize": "intermediate_size",
        "lanes": "lanes",
        "maxSeqLen": "max_seq_len",
        "numHeads": "num_q_heads",
        "outputBits": "output_bits"
      },
      "constructor_params": [
        {
          "has_default": true,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "numHeads"
        },
        {
          "has_default": true,
          "name": "headDim"
        },
        {
          "has_default": true,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "inputBits"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "computeArrayRows"
        },
        {
          "has_default": true,
          "name": "computeArrayCols"
        },
        {
          "has_default": true,
          "name": "cacheTileWords"
        },
        {
          "has_default": true,
          "name": "cacheTileCount"
        },
        {
          "has_default": true,
          "name": "mlpActivation"
        },
        {
          "has_default": true,
          "name": "qkvHasBias"
        },
        {
          "has_default": true,
          "name": "attentionOutHasBias"
        },
        {
          "has_default": true,
          "name": "weightBits"
        },
        {
          "has_default": true,
          "name": "integerMode"
        },
        {
          "has_default": true,
          "name": "accBits"
        }
      ],
      "constructor_requirement_source": "implementation_contract",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "num_q_heads",
        "head_dim",
        "intermediate_size",
        "lanes",
        "compute_array_rows",
        "compute_array_cols",
        "token_count",
        "max_seq_len",
        "input_bits",
        "elem_bits",
        "output_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "gpt2_block",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/DecoderBlock.scala",
      "sha256": "ec517051054fb006bd56e9012481f6b412cff3834ba98e4bfe66539b3cecf785",
      "source": "DecoderBlock.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "decoder_block",
      "warnings": []
    },
    {
      "case_class": "VectorNormParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "inputBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "hasMeanSub"
        },
        {
          "has_default": true,
          "name": "hasBeta"
        },
        {
          "has_default": true,
          "name": "eps"
        },
        {
          "has_default": true,
          "name": "integerMode"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "layer_norm_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm",
      "warnings": []
    },
    {
      "case_class": "AttentionParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "qHeads"
        },
        {
          "has_default": false,
          "name": "kvHeads"
        },
        {
          "has_default": false,
          "name": "headDim"
        },
        {
          "has_default": false,
          "name": "seqLen"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "qkvElemsPerBeat"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "outHasBias"
        },
        {
          "has_default": true,
          "name": "outWeightRole"
        },
        {
          "has_default": true,
          "name": "outBiasRole"
        },
        {
          "has_default": true,
          "name": "computeArrayRows"
        },
        {
          "has_default": true,
          "name": "computeArrayCols"
        },
        {
          "has_default": true,
          "name": "cacheTileWords"
        },
        {
          "has_default": true,
          "name": "cacheTileCount"
        },
        {
          "has_default": true,
          "name": "refillDataWidthBits"
        },
        {
          "has_default": true,
          "name": "crossTokenReuseTokens"
        },
        {
          "has_default": true,
          "name": "weightBits"
        },
        {
          "has_default": true,
          "name": "integerMode"
        },
        {
          "has_default": true,
          "name": "accBits"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "num_q_heads",
        "num_kv_heads",
        "head_dim",
        "seq_len",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "self_attention",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Attention.scala",
      "sha256": "c3e8bfc0ab0c1c8d4421bb0fe03272f4ea420df3f0e710b6a3c4154843593a7e",
      "source": "Attention.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "attention",
      "warnings": []
    },
    {
      "case_class": "ResidualParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "integerMode"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_1",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "8bef8dac50264c2278438a18e5be48328ed1fd1bfb3f9bbee3c522f11258aca3",
      "source": "Residual.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "residual",
      "warnings": []
    },
    {
      "case_class": "VectorNormParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "inputBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "hasMeanSub"
        },
        {
          "has_default": true,
          "name": "hasBeta"
        },
        {
          "has_default": true,
          "name": "eps"
        },
        {
          "has_default": true,
          "name": "integerMode"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "input_bits",
        "output_bits",
        "eps",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "layer_norm_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Norm.scala",
      "sha256": "f3319af0d66c9e8c19e7cc789b9fc5799b62e0ad49811ef7da43ceb6dc2eeddf",
      "source": "Norm.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "norm",
      "warnings": []
    },
    {
      "case_class": "DenseFFNParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "activation"
        },
        {
          "has_default": true,
          "name": "upWeightRole"
        },
        {
          "has_default": true,
          "name": "upBiasRole"
        },
        {
          "has_default": true,
          "name": "downWeightRole"
        },
        {
          "has_default": true,
          "name": "downBiasRole"
        },
        {
          "has_default": true,
          "name": "computeArrayRows"
        },
        {
          "has_default": true,
          "name": "computeArrayCols"
        },
        {
          "has_default": true,
          "name": "cacheTileWords"
        },
        {
          "has_default": true,
          "name": "cacheTileCount"
        },
        {
          "has_default": true,
          "name": "refillDataWidthBits"
        },
        {
          "has_default": true,
          "name": "crossTokenReuseTokens"
        },
        {
          "has_default": true,
          "name": "weightBits"
        },
        {
          "has_default": true,
          "name": "integerMode"
        },
        {
          "has_default": true,
          "name": "accBits"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_fc",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "1896b7ea12ac548124a1a25266baa7d9ea087af21ee60d57633f6843db91a58c",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn",
      "warnings": []
    },
    {
      "case_class": "ActivationParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "kind"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "integerMode"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "activation",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Activation.scala",
      "sha256": "c77e42c70db8b3fb74c9563970edc90cd3a79a144d959eaa8a253008ae5f24ce",
      "source": "Activation.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "activation",
      "warnings": []
    },
    {
      "case_class": "DenseFFNParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": false,
          "name": "intermediateSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "outputBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "activation"
        },
        {
          "has_default": true,
          "name": "upWeightRole"
        },
        {
          "has_default": true,
          "name": "upBiasRole"
        },
        {
          "has_default": true,
          "name": "downWeightRole"
        },
        {
          "has_default": true,
          "name": "downBiasRole"
        },
        {
          "has_default": true,
          "name": "computeArrayRows"
        },
        {
          "has_default": true,
          "name": "computeArrayCols"
        },
        {
          "has_default": true,
          "name": "cacheTileWords"
        },
        {
          "has_default": true,
          "name": "cacheTileCount"
        },
        {
          "has_default": true,
          "name": "refillDataWidthBits"
        },
        {
          "has_default": true,
          "name": "crossTokenReuseTokens"
        },
        {
          "has_default": true,
          "name": "weightBits"
        },
        {
          "has_default": true,
          "name": "integerMode"
        },
        {
          "has_default": true,
          "name": "accBits"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "intermediate_size",
        "lanes",
        "elem_bits",
        "weight_bits",
        "acc_bits",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "mlp_proj",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/FFN.scala",
      "sha256": "1896b7ea12ac548124a1a25266baa7d9ea087af21ee60d57633f6843db91a58c",
      "source": "FFN.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "ffn",
      "warnings": []
    },
    {
      "case_class": "ResidualParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "hiddenSize"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "maxSeqLen"
        },
        {
          "has_default": true,
          "name": "integerMode"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "hidden_size",
        "lanes",
        "elem_bits",
        "integer_mode"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "residual_add_2",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Residual.scala",
      "sha256": "8bef8dac50264c2278438a18e5be48328ed1fd1bfb3f9bbee3c522f11258aca3",
      "source": "Residual.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "residual",
      "warnings": []
    },
    {
      "case_class": "SoftmaxParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "seqLen"
        },
        {
          "has_default": true,
          "name": "lanes"
        },
        {
          "has_default": true,
          "name": "elemBits"
        },
        {
          "has_default": true,
          "name": "fracBits"
        },
        {
          "has_default": true,
          "name": "batchSize"
        },
        {
          "has_default": true,
          "name": "causal"
        },
        {
          "has_default": true,
          "name": "slidingWindow"
        },
        {
          "has_default": true,
          "name": "probabilityFracBits"
        },
        {
          "has_default": true,
          "name": "integerMode"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "seq_len",
        "lanes",
        "elem_bits"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "softmax",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Softmax.scala",
      "sha256": "4f68287b82eab429fa5da62a9d8f3fd1a537f00ef42e364f411e7dd3537e94f2",
      "source": "Softmax.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "softmax",
      "warnings": []
    },
    {
      "case_class": "AttentionMaskParams",
      "constructor_binding_names": [],
      "constructor_binding_sources": {},
      "constructor_params": [
        {
          "has_default": false,
          "name": "seqLen"
        },
        {
          "has_default": true,
          "name": "causal"
        },
        {
          "has_default": true,
          "name": "slidingWindow"
        },
        {
          "has_default": true,
          "name": "globalEvery"
        }
      ],
      "constructor_requirement_source": "template_metadata",
      "errors": [],
      "exists": true,
      "metadata_required_params": [
        "seq_len",
        "causal"
      ],
      "missing_required_params_in_constructor": [],
      "numeric_constructor_params_not_bound_by_metadata": [],
      "op": "causal_mask",
      "path": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/templates/operator_chisel/Mask.scala",
      "sha256": "bfb70e48641d60c25100b8240d5fef461aa954847c5fe5777b7fbb5445fc0e0a",
      "source": "Mask.scala",
      "source_required_params_missing_from_metadata": [],
      "status": "pass",
      "template_id": "mask",
      "warnings": []
    }
  ],
  "unsupported_bindings": [],
  "warnings": []
}
</candidate_template_selection>

<design_team>
{
  "aggregate": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/template_selection/team/team_aggregate.json",
  "approval_required_for": [],
  "completed_subtasks": 4,
  "decomposer_error": null,
  "decomposer_used_fallback": false,
  "decomposition_source": "llm",
  "errors": [],
  "event_log": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/template_selection/team/event_log.jsonl",
  "executable_actions": [
    {
      "acceptance_checkers": [
        "template_binding_static_check",
        "parameter_binding_static_check",
        "numeric_compare",
        "sacg_static_check"
      ],
      "action_type": "evidence_and_repair_review",
      "consumes": [
        "artifact.input.model_config",
        "constraint.model.decoder",
        "constraint.shape.model",
        "constraint.numeric.policy",
        "constraint.cross_layer.input_consistency",
        "candidate attention_semantics",
        "candidate parameter_bindings",
        "candidate checker_results"
      ],
      "id": "template_selection.attention_semantic_engineer.promote_to_cross_layer",
      "on_failure": "Block promotion to the cross-layer gate and record the concrete current-stage attention semantic, parameter-binding, numeric-policy, or SACG contradiction; do not silently modify the candidate artifact.",
      "produces": [
        "artifact.template_selection.attention_semantic_review"
      ],
      "rationale": "All supplied deterministic checker results pass and the candidate attention semantics show no concrete current-stage contradiction. Promote the attention semantic review to the cross-layer gate while preserving the RoPE and KV-cache policies already recorded in the candidate artifact.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "template_binding_static_check",
        "parameter_binding_static_check",
        "numeric_compare",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "template_coverage_check",
        "template_binding_static_check",
        "sacg_static_check"
      ],
      "action_type": "evidence_and_repair_review",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "candidate selected_templates",
        "candidate operator_sequence",
        "candidate coverage",
        "candidate missing_ops",
        "candidate checker_results"
      ],
      "id": "template_selection.operator_coverage_review.publish",
      "on_failure": "If any checker reports errors or hidden unmatched/missing coverage, block template_selection and route the specific operator/constraint to bounded template/coverage repair with current SACG evidence; do not close with free-form RTL or implicit Chisel defaults.",
      "produces": [
        "artifact.template_selection.operator_coverage_review"
      ],
      "rationale": "Re-run current-source coverage, binding-static, and SACG-static checkers over the candidate selection and publish a deterministic checker-backed coverage review; this prevents promoting a completed coverage matrix without current checker evidence.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "template_coverage_check",
        "template_binding_static_check",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "parameter_binding_static_check",
        "template_binding_static_check",
        "numeric_compare",
        "sacg_static_check"
      ],
      "action_type": "sacg_constraint_review",
      "consumes": [
        "artifact.input.model_config",
        "artifact.input.numeric_policy",
        "artifact.input.template_library",
        "artifact.input.template_metadata",
        "artifact.input.design_space",
        "candidate_stage_artifact.template_selection"
      ],
      "id": "template_selection.binding_engineer.record_stage2_binding_review",
      "on_failure": "Do not promote the stage; record the concrete contradiction in sacg_memory and schedule a bounded rerun of the failed checker.",
      "produces": [
        "artifact.template_selection.template_binding_review"
      ],
      "rationale": "Persist a checker-grounded Stage-2 binding review and rerun the specialized parameter/source/numeric/SACG static checkers against the current candidate evidence before handing off to peer specialists.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "parameter_binding_static_check",
        "template_binding_static_check",
        "numeric_compare",
        "sacg_static_check"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check"
      ],
      "action_type": "team_handoff",
      "consumes": [
        "artifact.template_selection.template_binding_review"
      ],
      "id": "template_selection.binding_engineer.handoff_ready_to_peers",
      "on_failure": "Keep downstream template_selection peers blocked and open a bounded retry/backtrack request if SACG aggregation or memory update rejects the ready status.",
      "produces": [
        "sacg_memory.stage_outcome.template_binding_review_ready"
      ],
      "rationale": "Hand off the current ready Stage-2 binding review and checker evidence to attention_semantic_engineer and cross_layer_gate_engineer, preserving SACG memory for downstream traceability.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "team_aggregate",
        "sacg_memory_update"
      ]
    },
    {
      "acceptance_checkers": [
        "sacg_static_check",
        "template_binding_static_check",
        "numeric_compare"
      ],
      "action_type": "stage_gate_decision_handoff",
      "consumes": [
        "artifact.template_selection.operator_coverage_review",
        "artifact.template_selection.template_binding_review",
        "artifact.template_selection.attention_semantic_review",
        "artifact.template_selection.cross_layer_trace",
        "artifact.template_selection.checker_results",
        "artifact.template_selection.stage_gate_policy",
        "candidate_stage_artifact"
      ],
      "id": "template_selection.gate_decision.ready_handoff",
      "on_failure": "If team_aggregate rejects the gate decision, return the rejection as a current-stage evidence gap and rerun the relevant specialist/checker; do not promote past template_selection.",
      "produces": [
        "artifact.template_selection.stage_gate_decision"
      ],
      "rationale": "All deterministic current-stage checker_results pass, the cross_layer_trace contains the required numeric, board memory, board runtime, board deployment, and input-consistency facts, and no active SACG-memory blockers remain. The gate decision is ready for team_aggregate consumption.",
      "requires_approval": false,
      "stage": "template_selection",
      "tool_roles": [
        "team_aggregate"
      ]
    }
  ],
  "execution_groups": [
    0,
    1
  ],
  "llm_io_metrics": {
    "executable_action_count": 5,
    "max_duration_sec": 91.67410031502368,
    "max_prompt_bytes": 70767,
    "result_count": 4,
    "subtasks_without_executable_actions": [],
    "total_duration_sec": 305.99405312904855,
    "total_prompt_bytes": 282604
  },
  "split_required": true,
  "status": "ready",
  "subtask_count": 4,
  "subtask_plan": "/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/template_selection/team/subtask_plan.json",
  "used_fallback_count": 0
}
</design_team>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/gpt2_deepseek_v4pro_20261020/constraint_extraction/initial_design_graph.json
</source_sacg_state>

<stage_gate_policy>
{
  "classification_rule": "Put only unresolved current_stage_blocks in risks. Put not_current_stage_blocks in proposed_actions or approval_required_for. The supplied checker evidence is computed from the current source tree: template source/interface records and attention components carry source hashes, while the mandatory FPGA-IP checker scans the complete template directory. Do not require a second future code-generation, simulation, or synthesis audit to accept those current Stage-2 facts. If all deterministic checker_results pass and no concrete contradiction in their current evidence remains, return status='ready' and risks=[].",
  "current_stage_blocks": [
    "any decoder operator has no trusted selected template or explicit required adapter",
    "any selected template required parameter is unbound, illegal, or only supplied by an implicit constructor default when model/numeric/board input has a value",
    "any selected template source file is missing or its metadata required parameters do not match the Chisel case-class constructor",
    "the complete selected template closure contains HardFloat, SyncReadMem, or lacks mandatory Vivado floating-point/XPM bindings",
    "self_attention lacks selected or embedded coverage for Q/K/V projection, RoPE when required, GQA/MQA head mapping, softmax, output projection, required KV-cache behavior, or causal mask",
    "numeric policy, board memory, board runtime, board deployment, or cross-layer input-consistency constraints are absent from the template-selection trace",
    "LLM sub-agent output reports a concrete contradiction in the candidate selection for this stage"
  ],
  "not_current_stage_blocks": [
    "lanes, compute_array_rows, or compute_array_cols has not yet been selected from a Stage-2-validated candidate_bound domain; Stage 4 is the sole concrete DSE selection authority",
    "VCS/Verilator simulation has not been run yet",
    "Vivado synthesis, implementation, timing closure, or bitstream generation has not been run yet",
    "final generated accelerator code has not been emitted yet",
    "runtime driver, board wrapper, or full DDR/AXI top-level integration has not been generated yet",
    "later-stage numeric accuracy or board bring-up evidence is not present yet"
  ],
  "schema_version": "spatialaccagent.stage2_gate_policy.v0"
}
</stage_gate_policy>

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
  "recent_stage_outcomes": [],
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
