<agent>
semantic_template_repair_basic_ieee_operators_agent
</agent>

<task>
Act as the implementation owner for one dependency-ordered semantic-template repair phase. Complete only phase basic_ieee_operators: Implement the frozen IEEE arithmetic and real-weight consumption for Linear, VectorNorm/RMSNorm, ElementwiseMul, and ResidualAdd. Linear must consume the declared tiled real weights without an identity/default path; RMSNorm must load gamma and compute x/sqrt(mean(x^2)+epsilon)*gamma over the complete vector; elementwise multiply and residual add must operate on numeric values rather than their IEEE encodings. Common.scala may contain shared synthesizable conversion/arithmetic helpers. Return complete compile-ready file contents for this phase; do not wait for later phases and do not claim any verification gate has passed.
</task>

<rules>
1. Return status=ready_to_apply when this phase is complete and compile-ready even though later semantic phases remain; use blocked only for exact facts missing from this phase bundle.
2. When relevant_project_knowledge is present, use it as a bounded project mental model, not as current proof. Reuse a claim only according to its epistemic_status, applicability, lifecycle_status, recorded source/contract identity, and evidence bindings. Current source, contract, and real-tool evidence always override it; a source_rebind_required claim must be re-established before it drives a repair, and no knowledge row expands edit authority or permits promotion.
3. Populate project_knowledge_updates only with genuinely new, refined, contradicted, or superseding understanding derived from the current hash-bound evidence. Capture durable operator semantics, ready/valid behavior, state-machine mechanism, timing relation, buffering/backpressure, memory mapping, or board lifecycle knowledge; cite exact evidence paths from the supplied package, state validity conditions and reuse guidance, and reference prior knowledge IDs when superseding or contradicting them. Return an empty list when this turn adds no durable understanding; do not restate unchanged context.
4. Edit only exact Scala paths listed in semantic_template_repair_phase_bundle.editable_contract.approved_bounded_template_repair_exact_files.
5. Treat phase.dependency_template_files and semantic_template_repair_phase_bundle.read_only_dependency_template_files as exact read-only interfaces; consume them but never return them in file_edits.
6. Replace every file named in phase.required_template_files in both the persistent framework-template root and current generated-template root. The paired contents must be byte-identical and use the exact supplied pre-edit SHA-256 values.
7. Provide complete file contents, never snippets, ellipses, prose patches, behavioral wrappers, simulator-only arithmetic, or human follow-up instructions.
8. Use the hash-verified target-model implementation, semantic adapter, stage numeric/weight-layout contracts, and trusted HardFloat/QuantCommon support as the only semantic and arithmetic authorities.
9. Preserve external accelerator/board ABI, stage order, dimensions, stream ordering, memory/runtime contracts, numeric policy, checkpoint/input/reference/checker hashes, and all non-phase files.
10. This phase is implementation-in-progress. Do not create a DUT binding manifest or semantic harness, edit emitted SystemVerilog, alter expected outputs/checkers, or claim operator/layer correctness.
11. Request only sbt --no-server Compile/compile in the exact generated Chisel project. The executor runs a mandatory compile even if the request is omitted.
</rules>

<source_sacg_state>
/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/repair/sacg_state.json
</source_sacg_state>

<repair_step>
{
  "action": {
    "approval_required": false,
    "debug_layer": "operator_leaf_modules",
    "failed_current_layer_gates": [
      {
        "name": "case_semantic_testbench",
        "status": "fail"
      },
      {
        "name": "case_leaf_functional",
        "status": "not_run"
      },
      {
        "name": "case_leaf_golden_compare",
        "status": "not_run"
      },
      {
        "name": "case_operator_leaf_semantic_evidence",
        "status": "not_run"
      }
    ],
    "failure_signature": {
      "failed_gates": [
        "case_semantic_testbench"
      ],
      "summaries": [
        "returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files",
        "real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']",
        "required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']",
        "operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run",
        "verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled."
      ]
    },
    "minimal_repair_context": {
      "failed_current_layer_gates": [
        {
          "name": "case_semantic_testbench",
          "status": "fail"
        },
        {
          "name": "case_leaf_functional",
          "status": "not_run"
        },
        {
          "name": "case_leaf_golden_compare",
          "status": "not_run"
        },
        {
          "name": "case_operator_leaf_semantic_evidence",
          "status": "not_run"
        }
      ]
    },
    "reason": "current layer lacks a valid semantic loader/harness, immutable numeric comparison contract, or executed weight-consumption evidence",
    "repair_gate": "case_semantic_testbench",
    "repair_kind": "semantic_loader_harness_binding",
    "root_candidate_module": null,
    "scope": "verification_capability_repair",
    "source": "hierarchical_repair_loop",
    "target_modules": [
      "case_semantic_testbench"
    ],
    "violated_contract": "current_verification_capability_must_execute_before_hardware_repair"
  },
  "approval_required": false,
  "debug_layer": "operator_leaf_modules",
  "id": "repair_step.00",
  "repair_context": {
    "failed_current_layer_gates": [
      {
        "name": "case_semantic_testbench",
        "status": "fail"
      },
      {
        "name": "case_leaf_functional",
        "status": "not_run"
      },
      {
        "name": "case_leaf_golden_compare",
        "status": "not_run"
      },
      {
        "name": "case_operator_leaf_semantic_evidence",
        "status": "not_run"
      }
    ]
  },
  "scope": "verification_capability_repair",
  "source": "hierarchical_repair_loop",
  "status": "ready_for_agent_patch",
  "target_modules": [
    "case_semantic_testbench"
  ]
}
</repair_step>

<semantic_template_repair_phase_bundle>
{
  "document_chars": 35767,
  "document_count": 5,
  "documents": [
    {
      "bytes": 1120,
      "content": "{\n  \"_llm_provenance\": {\n    \"mode\": \"llm\",\n    \"sub_agent\": \"model_config_agent\",\n    \"used_fallback\": false\n  },\n  \"attention\": {\n    \"causal\": true,\n    \"head_dim\": 64,\n    \"kind\": \"gqa\",\n    \"num_kv_heads\": 2,\n    \"num_q_heads\": 14,\n    \"out_bias\": false,\n    \"position_encoding\": {\n      \"rope_theta\": 1000000.0,\n      \"type\": \"rope\"\n    },\n    \"qkv_bias\": true\n  },\n  \"block\": {\n    \"operator_sequence\": [\n      \"rms_norm_1\",\n      \"self_attention\",\n      \"residual_add_1\",\n      \"rms_norm_2\",\n      \"mlp_gate_proj\",\n      \"mlp_up_proj\",\n      \"activation_mul\",\n      \"mlp_down_proj\",\n      \"residual_add_2\"\n    ],\n    \"type\": \"decoder\"\n  },\n  \"hidden_size\": 896,\n  \"mlp\": {\n    \"activation\": \"silu\",\n    \"down_bias\": false,\n    \"intermediate_size\": 4864,\n    \"type\": \"gated\",\n    \"up_bias\": false\n  },\n  \"model_type\": \"qwen2\",\n  \"norm\": {\n    \"eps\": 1e-06,\n    \"has_bias\": false,\n    \"position\": \"pre\",\n    \"type\": \"rms_norm\"\n  },\n  \"num_layers\": 24,\n  \"target_max_seq_len\": 16,\n  \"weight_layout\": {\n    \"mlp\": \"gate_up_down\",\n    \"norm\": \"weight_only\",\n    \"out_proj\": \"dense\",\n    \"qkv\": \"separate_q_k_v\"\n  }\n}\n",
      "path": "accagent/runs/spatialacc_qwen_agent_fast_run/input/model_config.json",
      "sha256": "55b4c398c3a9eaeaf6a8c3bd25e5b51e83d46c30c002ed562c9efa98cd50b113",
      "truncated": false
    },
    {
      "bytes": 2047,
      "content": "{\n  \"_llm_provenance\": {\n    \"mode\": \"llm\",\n    \"sub_agent\": \"numeric_policy_agent\",\n    \"used_fallback\": false\n  },\n  \"_numeric_comparison_resolution\": {\n    \"default_policy_id\": \"spatialaccagent.loose_numeric_compare.v1\",\n    \"defaulted_fields\": [\n      \"atol\",\n      \"rtol\",\n      \"max_mismatch_fraction\"\n    ],\n    \"defaults\": {\n      \"atol\": 0.1,\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1\n    },\n    \"dut_outputs_used_for_resolution\": false,\n    \"field_sources\": {\n      \"atol\": \"framework_default\",\n      \"max_mismatch_fraction\": \"framework_default\",\n      \"rtol\": \"framework_default\"\n    },\n    \"provided_values_take_precedence\": true,\n    \"resolved\": {\n      \"atol\": 0.1,\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1\n    },\n    \"schema_version\": \"spatialaccagent.numeric_comparison_resolution.v1\"\n  },\n  \"default_rules\": {\n    \"acc_dtype\": \"fp32\",\n    \"activation_dtype\": \"fp16\",\n    \"rounding\": \"nearest_even\",\n    \"saturation\": false,\n    \"scale_dtype\": \"fp16\",\n    \"weight_dtype\": \"fp16\"\n  },\n  \"notes\": [\n    \"Explicit numeric policy provided in current_run_numeric_policy.md; README fallback policy is not used for this run.\",\n    \"End-to-end acceptance target is board-runnable execution with valid output and no deadlock; exact numerical equivalence to the source model is not required for this run unless a later user-provided policy strengthens the tolerance.\",\n    \"If this policy is replaced, checkpoint reuse must treat it as an input change and rerun affected stages.\",\n    \"Missing or invalid quantitative comparison values use spatialaccagent.loose_numeric_compare.v1; current-run provided values take precedence.\"\n  ],\n  \"policy_id\": \"current_run_numeric_policy.md\",\n  \"schema_version\": \"1.0\",\n  \"tolerance\": {\n    \"comparison\": {\n      \"atol\": 0.1,\n      \"default_policy_id\": \"spatialaccagent.loose_numeric_compare.v1\",\n      \"max_mismatch_fraction\": 0.05,\n      \"rtol\": 0.1,\n      \"source\": \"framework_default\"\n    },\n    \"stage\": \"functional_or_shape\",\n    \"system\": \"valid_output_required\"\n  }\n}\n",
      "path": "accagent/runs/spatialacc_qwen_agent_fast_run/input/numeric_policy.json",
      "sha256": "29680d3fbddc19f210b9ffa17dc705aa4fac1f0ee594ddd0c98fa1a662c985b5",
      "truncated": false
    },
    {
      "bytes": 21621,
      "content": "#                \ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\n#           This file was automatically generated from src/transformers/models/qwen2/modular_qwen2.py.\n#               Do NOT edit this file manually as any edits will be overwritten by the generation of\n#             the file from the modular. If any change should be done, please apply the change to the\n#                          modular_qwen2.py file directly. One of our CI enforces this.\n#                \ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\ud83d\udea8\nfrom typing import Callable, Optional, Union\n\nimport torch\nfrom torch import nn\n\nfrom ...activations import ACT2FN\nfrom ...cache_utils import Cache, DynamicCache\nfrom ...generation import GenerationMixin\nfrom ...integrations import use_kernel_forward_from_hub\nfrom ...masking_utils import create_causal_mask, create_sliding_window_causal_mask\nfrom ...modeling_flash_attention_utils import FlashAttentionKwargs\nfrom ...modeling_layers import (\n    GenericForQuestionAnswering,\n    GenericForSequenceClassification,\n    GenericForTokenClassification,\n    GradientCheckpointingLayer,\n)\nfrom ...modeling_outputs import BaseModelOutputWithPast, CausalLMOutputWithPast\nfrom ...modeling_rope_utils import ROPE_INIT_FUNCTIONS, dynamic_rope_update\nfrom ...modeling_utils import ALL_ATTENTION_FUNCTIONS, PreTrainedModel\nfrom ...processing_utils import Unpack\nfrom ...utils import TransformersKwargs, auto_docstring, can_return_tuple\nfrom ...utils.deprecation import deprecate_kwarg\nfrom ...utils.generic import check_model_inputs\nfrom .configuration_qwen2 import Qwen2Config\n\n\nclass Qwen2MLP(nn.Module):\n    def __init__(self, config):\n        super().__init__()\n        self.config = config\n        self.hidden_size = config.hidden_size\n        self.intermediate_size = config.intermediate_size\n        self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)\n        self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)\n        self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)\n        self.act_fn = ACT2FN[config.hidden_act]\n\n    def forward(self, x):\n        down_proj = self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))\n        return down_proj\n\n\ndef rotate_half(x):\n    \"\"\"Rotates half the hidden dims of the input.\"\"\"\n    x1 = x[..., : x.shape[-1] // 2]\n    x2 = x[..., x.shape[-1] // 2 :]\n    return torch.cat((-x2, x1), dim=-1)\n\n\ndef apply_rotary_pos_emb(q, k, cos, sin, position_ids=None, unsqueeze_dim=1):\n    \"\"\"Applies Rotary Position Embedding to the query and key tensors.\n\n    Args:\n        q (`torch.Tensor`): The query tensor.\n        k (`torch.Tensor`): The key tensor.\n        cos (`torch.Tensor`): The cosine part of the rotary embedding.\n        sin (`torch.Tensor`): The sine part of the rotary embedding.\n        position_ids (`torch.Tensor`, *optional*):\n            Deprecated and unused.\n        unsqueeze_dim (`int`, *optional*, defaults to 1):\n            The 'unsqueeze_dim' argument specifies the dimension along which to unsqueeze cos[position_ids] and\n            sin[position_ids] so that they can be properly broadcasted to the dimensions of q and k. For example, note\n            that cos[position_ids] and sin[position_ids] have the shape [batch_size, seq_len, head_dim]. Then, if q and\n            k have the shape [batch_size, heads, seq_len, head_dim], then setting unsqueeze_dim=1 makes\n            cos[position_ids] and sin[position_ids] broadcastable to the shapes of q and k. Similarly, if q and k have\n            the shape [batch_size, seq_len, heads, head_dim], then set unsqueeze_dim=2.\n    Returns:\n        `tuple(torch.Tensor)` comprising of the query and key tensors rotated using the Rotary Position Embedding.\n    \"\"\"\n    cos = cos.unsqueeze(unsqueeze_dim)\n    sin = sin.unsqueeze(unsqueeze_dim)\n    q_embed = (q * cos) + (rotate_half(q) * sin)\n    k_embed = (k * cos) + (rotate_half(k) * sin)\n    return q_embed, k_embed\n\n\ndef repeat_kv(hidden_states: torch.Tensor, n_rep: int) -> torch.Tensor:\n    \"\"\"\n    This is the equivalent of torch.repeat_interleave(x, dim=1, repeats=n_rep). The hidden states go from (batch,\n    num_key_value_heads, seqlen, head_dim) to (batch, num_attention_heads, seqlen, head_dim)\n    \"\"\"\n    batch, num_key_value_heads, slen, head_dim = hidden_states.shape\n    if n_rep == 1:\n        return hidden_states\n    hidden_states = hidden_states[:, :, None, :, :].expand(batch, num_key_value_heads, n_rep, slen, head_dim)\n    return hidden_states.reshape(batch, num_key_value_heads * n_rep, slen, head_dim)\n\n\ndef eager_attention_forward(\n    module: nn.Module,\n    query: torch.Tensor,\n    key: torch.Tensor,\n    value: torch.Tensor,\n    attention_mask: Optional[torch.Tensor],\n    scaling: float,\n    dropout: float = 0.0,\n    **kwargs: Unpack[TransformersKwargs],\n):\n    key_states = repeat_kv(key, module.num_key_value_groups)\n    value_states = repeat_kv(value, module.num_key_value_groups)\n\n    attn_weights = torch.matmul(query, key_states.transpose(2, 3)) * scaling\n    if attention_mask is not None:\n        causal_mask = attention_mask[:, :, :, : key_states.shape[-2]]\n        attn_weights = attn_weights + causal_mask\n\n    attn_weights = nn.functional.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query.dtype)\n    attn_weights = nn.functional.dropout(attn_weights, p=dropout, training=module.training)\n    attn_output = torch.matmul(attn_weights, value_states)\n    attn_output = attn_output.transpose(1, 2).contiguous()\n\n    return attn_output, attn_weights\n\n\nclass Qwen2Attention(nn.Module):\n    \"\"\"Multi-headed attention from 'Attention Is All You Need' paper\"\"\"\n\n    def __init__(self, config: Qwen2Config, layer_idx: int):\n        super().__init__()\n        self.config = config\n        self.layer_idx = layer_idx\n        self.head_dim = getattr(config, \"head_dim\", config.hidden_size // config.num_attention_heads)\n        self.num_key_value_groups = config.num_attention_heads // config.num_key_value_heads\n        self.scaling = self.head_dim**-0.5\n        self.attention_dropout = config.attention_dropout\n        self.is_causal = True\n        self.q_proj = nn.Linear(config.hidden_size, config.num_attention_heads * self.head_dim, bias=True)\n        self.k_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * self.head_dim, bias=True)\n        self.v_proj = nn.Linear(config.hidden_size, config.num_key_value_heads * self.head_dim, bias=True)\n        self.o_proj = nn.Linear(config.num_attention_heads * self.head_dim, config.hidden_size, bias=False)\n        self.sliding_window = config.sliding_window if config.layer_types[layer_idx] == \"sliding_attention\" else None\n\n    @deprecate_kwarg(\"past_key_value\", new_name=\"past_key_values\", version=\"4.58\")\n    def forward(\n        self,\n        hidden_states: torch.Tensor,\n        position_embeddings: tuple[torch.Tensor, torch.Tensor],\n        attention_mask: Optional[torch.Tensor],\n        past_key_values: Optional[Cache] = None,\n        cache_position: Optional[torch.LongTensor] = None,\n        **kwargs: Unpack[FlashAttentionKwargs],\n    ) -> tuple[torch.Tensor, Optional[torch.Tensor]]:\n        input_shape = hidden_states.shape[:-1]\n        hidden_shape = (*input_shape, -1, self.head_dim)\n\n        query_states = self.q_proj(hidden_states).view(hidden_shape).transpose(1, 2)\n        key_states = self.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)\n        value_states = self.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)\n\n        cos, sin = position_embeddings\n        query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)\n\n        if past_key_values is not None:\n            # sin and cos are specific to RoPE models; cache_position needed for the static cache\n            cache_kwargs = {\"sin\": sin, \"cos\": cos, \"cache_position\": cache_position}\n            key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx, cache_kwargs)\n\n        attention_interface: Callable = eager_attention_forward\n        if self.config._attn_implementation != \"eager\":\n            attention_interface = ALL_ATTENTION_FUNCTIONS[self.config._attn_implementation]\n\n        attn_output, attn_weights = attention_interface(\n            self,\n            query_states,\n            key_states,\n            value_states,\n            attention_mask,\n            dropout=0.0 if not self.training else self.attention_dropout,\n            scaling=self.scaling,\n            sliding_window=self.sliding_window,  # main diff with Llama\n            **kwargs,\n        )\n\n        attn_output = attn_output.reshape(*input_shape, -1).contiguous()\n        attn_output = self.o_proj(attn_output)\n        return attn_output, attn_weights\n\n\n@use_kernel_forward_from_hub(\"RMSNorm\")\nclass Qwen2RMSNorm(nn.Module):\n    def __init__(self, hidden_size, eps: float = 1e-6) -> None:\n        \"\"\"\n        Qwen2RMSNorm is equivalent to T5LayerNorm\n        \"\"\"\n        super().__init__()\n        self.weight = nn.Parameter(torch.ones(hidden_size))\n        self.variance_epsilon = eps\n\n    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:\n        input_dtype = hidden_states.dtype\n        hidden_states = hidden_states.to(torch.float32)\n        variance = hidden_states.pow(2).mean(-1, keepdim=True)\n        hidden_states = hidden_states * torch.rsqrt(variance + self.variance_epsilon)\n        return self.weight * hidden_states.to(input_dtype)\n\n    def extra_repr(self):\n        return f\"{tuple(self.weight.shape)}, eps={self.variance_epsilon}\"\n\n\nclass Qwen2DecoderLayer(GradientCheckpointingLayer):\n    def __init__(self, config: Qwen2Config, layer_idx: int):\n        super().__init__()\n        self.hidden_size = config.hidden_size\n\n        self.self_attn = Qwen2Attention(config=config, layer_idx=layer_idx)\n\n        self.mlp = Qwen2MLP(config)\n        self.input_layernorm = Qwen2RMSNorm(config.hidden_size, eps=config.rms_norm_eps)\n        self.post_attention_layernorm = Qwen2RMSNorm(config.hidden_size, eps=config.rms_norm_eps)\n        self.attention_type = config.layer_types[layer_idx]\n\n    @deprecate_kwarg(\"past_key_value\", new_name=\"past_key_values\", version=\"4.58\")\n    def forward(\n        self,\n        hidden_states: torch.Tensor,\n        attention_mask: Optional[torch.Tensor] = None,\n        position_ids: Optional[torch.LongTensor] = None,\n        past_key_values: Optional[Cache] = None,\n        use_cache: Optional[bool] = False,\n        cache_position: Optional[torch.LongTensor] = None,\n        position_embeddings: Optional[tuple[torch.Tensor, torch.Tensor]] = None,  # necessary, but kept here for BC\n        **kwargs: Unpack[TransformersKwargs],\n    ) -> torch.Tensor:\n        residual = hidden_states\n        hidden_states = self.input_layernorm(hidden_states)\n        # Self Attention\n        hidden_states, _ = self.self_attn(\n            hidden_states=hidden_states,\n            attention_mask=attention_mask,\n            position_ids=position_ids,\n            past_key_values=past_key_values,\n            use_cache=use_cache,\n            cache_position=cache_position,\n            position_embeddings=position_embeddings,\n            **kwargs,\n        )\n        hidden_states = residual + hidden_states\n\n        # Fully Connected\n        residual = hidden_states\n        hidden_states = self.post_attention_layernorm(hidden_states)\n        hidden_states = self.mlp(hidden_states)\n        hidden_states = residual + hidden_states\n        return hidden_states\n\n\n@auto_docstring\nclass Qwen2PreTrainedModel(PreTrainedModel):\n    config: Qwen2Config\n    base_model_prefix = \"model\"\n    supports_gradient_checkpointing = True\n    _no_split_modules = [\"Qwen2DecoderLayer\"]\n    _skip_keys_device_placement = [\"past_key_values\"]\n    _supports_flash_attn = True\n    _supports_sdpa = True\n    _supports_flex_attn = True\n\n    _can_compile_fullgraph = True\n    _supports_attention_backend = True\n    _can_record_outputs = {\n        \"hidden_states\": Qwen2DecoderLayer,\n        \"attentions\": Qwen2Attention,\n    }\n\n\nclass Qwen2RotaryEmbedding(nn.Module):\n    inv_freq: torch.Tensor  # fix linting for `register_buffer`\n\n    def __init__(self, config: Qwen2Config, device=None):\n        super().__init__()\n        # BC: \"rope_type\" was originally \"type\"\n        if hasattr(config, \"rope_scaling\") and isinstance(config.rope_scaling, dict):\n            self.rope_type = config.rope_scaling.get(\"rope_type\", config.rope_scaling.get(\"type\"))\n        else:\n            self.rope_type = \"default\"\n        self.max_seq_len_cached = config.max_position_embeddings\n        self.original_max_seq_len = config.max_position_embeddings\n\n        self.config = config\n        self.rope_init_fn = ROPE_INIT_FUNCTIONS[self.rope_type]\n\n        inv_freq, self.attention_scaling = self.rope_init_fn(self.config, device)\n        self.register_buffer(\"inv_freq\", inv_freq, persistent=False)\n        self.original_inv_freq = self.inv_freq\n\n    @torch.no_grad()\n    @dynamic_rope_update  # power user: used with advanced RoPE types (e.g. dynamic rope)\n    def forward(self, x, position_ids):\n        inv_freq_expanded = self.inv_freq[None, :, None].float().expand(position_ids.shape[0], -1, 1).to(x.device)\n        position_ids_expanded = position_ids[:, None, :].float()\n\n        device_type = x.device.type if isinstance(x.device.type, str) and x.device.type != \"mps\" else \"cpu\"\n        with torch.autocast(device_type=device_type, enabled=False):  # Force float32\n            freqs = (inv_freq_expanded.float() @ position_ids_expanded.float()).transpose(1, 2)\n            emb = torch.cat((freqs, freqs), dim=-1)\n            cos = emb.cos() * self.attention_scaling\n            sin = emb.sin() * self.attention_scaling\n\n        return cos.to(dtype=x.dtype), sin.to(dtype=x.dtype)\n\n\n@auto_docstring\nclass Qwen2Model(Qwen2PreTrainedModel):\n    def __init__(self, config: Qwen2Config):\n        super().__init__(config)\n        self.padding_idx = config.pad_token_id\n        self.vocab_size = config.vocab_size\n\n        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, self.padding_idx)\n        self.layers = nn.ModuleList(\n            [Qwen2DecoderLayer(config, layer_idx) for layer_idx in range(config.num_hidden_layers)]\n        )\n        self.norm = Qwen2RMSNorm(config.hidden_size, eps=config.rms_norm_eps)\n        self.rotary_emb = Qwen2RotaryEmbedding(config=config)\n        self.gradient_checkpointing = False\n        self.has_sliding_layers = \"sliding_attention\" in self.config.layer_types\n\n        # Initialize weights and apply final processing\n        self.post_init()\n\n    @check_model_inputs\n    @auto_docstring\n    def forward(\n        self,\n        input_ids: Optional[torch.LongTensor] = None,\n        attention_mask: Optional[torch.Tensor] = None,\n        position_ids: Optional[torch.LongTensor] = None,\n        past_key_values: Optional[Cache] = None,\n        inputs_embeds: Optional[torch.FloatTensor] = None,\n        use_cache: Optional[bool] = None,\n        cache_position: Optional[torch.LongTensor] = None,\n        **kwargs: Unpack[TransformersKwargs],\n    ) -> BaseModelOutputWithPast:\n        if (input_ids is None) ^ (inputs_embeds is not None):\n            raise ValueError(\"You must specify exactly one of input_ids or inputs_embeds\")\n\n        if inputs_embeds is None:\n            inputs_embeds = self.embed_tokens(input_ids)\n\n        if use_cache and past_key_values is None:\n            past_key_values = DynamicCache(config=self.config)\n\n        if cache_position is None:\n            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0\n            cache_position = torch.arange(\n                past_seen_tokens, past_seen_tokens + inputs_embeds.shape[1], device=inputs_embeds.device\n            )\n\n        if position_ids is None:\n            position_ids = cache_position.unsqueeze(0)\n\n        # It may already have been prepared by e.g. `generate`\n        if not isinstance(causal_mask_mapping := attention_mask, dict):\n            # Prepare mask arguments\n            mask_kwargs = {\n                \"config\": self.config,\n                \"input_embeds\": inputs_embeds,\n                \"attention_mask\": attention_mask,\n                \"cache_position\": cache_position,\n                \"past_key_values\": past_key_values,\n                \"position_ids\": position_ids,\n            }\n            # Create the masks\n            causal_mask_mapping = {\n                \"full_attention\": create_causal_mask(**mask_kwargs),\n            }\n            # The sliding window alternating layers are not always activated depending on the config\n            if self.has_sliding_layers:\n                causal_mask_mapping[\"sliding_attention\"] = create_sliding_window_causal_mask(**mask_kwargs)\n\n        hidden_states = inputs_embeds\n\n        # create position embeddings to be shared across the decoder layers\n        position_embeddings = self.rotary_emb(hidden_states, position_ids)\n\n        for decoder_layer in self.layers[: self.config.num_hidden_layers]:\n            hidden_states = decoder_layer(\n                hidden_states,\n                attention_mask=causal_mask_mapping[decoder_layer.attention_type],\n                position_ids=position_ids,\n                past_key_values=past_key_values,\n                use_cache=use_cache,\n                cache_position=cache_position,\n                position_embeddings=position_embeddings,\n                **kwargs,\n            )\n\n        hidden_states = self.norm(hidden_states)\n        return BaseModelOutputWithPast(\n            last_hidden_state=hidden_states,\n            past_key_values=past_key_values if use_cache else None,\n        )\n\n\n@auto_docstring\nclass Qwen2ForCausalLM(Qwen2PreTrainedModel, GenerationMixin):\n    _tied_weights_keys = [\"lm_head.weight\"]\n    _tp_plan = {\"lm_head\": \"colwise_rep\"}\n    _pp_plan = {\"lm_head\": ([\"hidden_states\"], [\"logits\"])}\n\n    def __init__(self, config):\n        super().__init__(config)\n        self.model = Qwen2Model(config)\n        self.vocab_size = config.vocab_size\n        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)\n\n        # Initialize weights and apply final processing\n        self.post_init()\n\n    @can_return_tuple\n    @auto_docstring\n    def forward(\n        self,\n        input_ids: Optional[torch.LongTensor] = None,\n        attention_mask: Optional[torch.Tensor] = None,\n        position_ids: Optional[torch.LongTensor] = None,\n        past_key_values: Optional[Cache] = None,\n        inputs_embeds: Optional[torch.FloatTensor] = None,\n        labels: Optional[torch.LongTensor] = None,\n        use_cache: Optional[bool] = None,\n        cache_position: Optional[torch.LongTensor] = None,\n        logits_to_keep: Union[int, torch.Tensor] = 0,\n        **kwargs: Unpack[TransformersKwargs],\n    ) -> CausalLMOutputWithPast:\n        r\"\"\"\n        Example:\n\n        ```python\n        >>> from transformers import AutoTokenizer, Qwen2ForCausalLM\n\n        >>> model = Qwen2ForCausalLM.from_pretrained(\"meta-qwen2/Qwen2-2-7b-hf\")\n        >>> tokenizer = AutoTokenizer.from_pretrained(\"meta-qwen2/Qwen2-2-7b-hf\")\n\n        >>> prompt = \"Hey, are you conscious? Can you talk to me?\"\n        >>> inputs = tokenizer(prompt, return_tensors=\"pt\")\n\n        >>> # Generate\n        >>> generate_ids = model.generate(inputs.input_ids, max_length=30)\n        >>> tokenizer.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]\n        \"Hey, are you conscious? Can you talk to me?\\nI'm not conscious, but I can talk to you.\"\n        ```\"\"\"\n        outputs: BaseModelOutputWithPast = self.model(\n            input_ids=input_ids,\n            attention_mask=attention_mask,\n            position_ids=position_ids,\n            past_key_values=past_key_values,\n            inputs_embeds=inputs_embeds,\n            use_cache=use_cache,\n            cache_position=cache_position,\n            **kwargs,\n        )\n\n        hidden_states = outputs.last_hidden_state\n        # Only compute necessary logits, and do not upcast them to float if we are not computing the loss\n        slice_indices = slice(-logits_to_keep, None) if isinstance(logits_to_keep, int) else logits_to_keep\n        logits = self.lm_head(hidden_states[:, slice_indices, :])\n\n        loss = None\n        if labels is not None:\n            loss = self.loss_function(logits=logits, labels=labels, vocab_size=self.config.vocab_size, **kwargs)\n\n        return CausalLMOutputWithPast(\n            loss=loss,\n            logits=logits,\n            past_key_values=outputs.past_key_values,\n            hidden_states=outputs.hidden_states,\n            attentions=outputs.attentions,\n        )\n\n\nclass Qwen2ForSequenceClassification(GenericForSequenceClassification, Qwen2PreTrainedModel):\n    pass\n\n\nclass Qwen2ForTokenClassification(GenericForTokenClassification, Qwen2PreTrainedModel):\n    pass\n\n\nclass Qwen2ForQuestionAnswering(GenericForQuestionAnswering, Qwen2PreTrainedModel):\n    base_model_prefix = \"transformer\"  # For BC, where `transformer` was used instead of `model`\n\n\n__all__ = [\n    \"Qwen2PreTrainedModel\",\n    \"Qwen2Model\",\n    \"Qwen2ForCausalLM\",\n    \"Qwen2RMSNorm\",\n    \"Qwen2ForSequenceClassification\",\n    \"Qwen2ForTokenClassification\",\n    \"Qwen2ForQuestionAnswering\",\n]\n",
      "path": "/home/remote/miniconda3/envs/diff/lib/python3.10/site-packages/transformers/models/qwen2/modeling_qwen2.py",
      "sha256": "a59fa06524227361fb401baf4d177124a27aec146bc01ec931235a9abbab17cb",
      "truncated": false
    },
    {
      "bytes": 10284,
      "content": "{\n  \"blockers\": [],\n  \"files\": [\n    {\n      \"bytes\": 8776,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/AddRecFN.scala\",\n      \"destination_sha256\": \"2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85\",\n      \"source\": \"src/resource/hardfloat/AddRecFN.scala\",\n      \"source_sha256\": \"2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85\"\n    },\n    {\n      \"bytes\": 3476,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/CompareRecFN.scala\",\n      \"destination_sha256\": \"b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d\",\n      \"source\": \"src/resource/hardfloat/CompareRecFN.scala\",\n      \"source_sha256\": \"b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d\"\n    },\n    {\n      \"bytes\": 4428,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64.scala\",\n      \"destination_sha256\": \"ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0\",\n      \"source\": \"src/resource/hardfloat/DivSqrtRecF64.scala\",\n      \"source_sha256\": \"ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0\"\n    },\n    {\n      \"bytes\": 33929,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64_mulAddZ31.scala\",\n      \"destination_sha256\": \"9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776\",\n      \"source\": \"src/resource/hardfloat/DivSqrtRecF64_mulAddZ31.scala\",\n      \"source_sha256\": \"9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776\"\n    },\n    {\n      \"bytes\": 20218,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecFN_small.scala\",\n      \"destination_sha256\": \"e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f\",\n      \"source\": \"src/resource/hardfloat/DivSqrtRecFN_small.scala\",\n      \"source_sha256\": \"e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f\"\n    },\n    {\n      \"bytes\": 3417,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/INToRecFN.scala\",\n      \"destination_sha256\": \"92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb\",\n      \"source\": \"src/resource/hardfloat/INToRecFN.scala\",\n      \"source_sha256\": \"92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb\"\n    },\n    {\n      \"bytes\": 15293,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulAddRecFN.scala\",\n      \"destination_sha256\": \"be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037\",\n      \"source\": \"src/resource/hardfloat/MulAddRecFN.scala\",\n      \"source_sha256\": \"be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037\"\n    },\n    {\n      \"bytes\": 5706,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulRecFN.scala\",\n      \"destination_sha256\": \"cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d\",\n      \"source\": \"src/resource/hardfloat/MulRecFN.scala\",\n      \"source_sha256\": \"cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d\"\n    },\n    {\n      \"bytes\": 6827,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToIN.scala\",\n      \"destination_sha256\": \"e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3\",\n      \"source\": \"src/resource/hardfloat/RecFNToIN.scala\",\n      \"source_sha256\": \"e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3\"\n    },\n    {\n      \"bytes\": 3958,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToRecFN.scala\",\n      \"destination_sha256\": \"97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09\",\n      \"source\": \"src/resource/hardfloat/RecFNToRecFN.scala\",\n      \"source_sha256\": \"97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09\"\n    },\n    {\n      \"bytes\": 13901,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RoundAnyRawFNToRecFN.scala\",\n      \"destination_sha256\": \"31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d\",\n      \"source\": \"src/resource/hardfloat/RoundAnyRawFNToRecFN.scala\",\n      \"source_sha256\": \"31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d\"\n    },\n    {\n      \"bytes\": 2880,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/classifyRecFN.scala\",\n      \"destination_sha256\": \"787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16\",\n      \"source\": \"src/resource/hardfloat/classifyRecFN.scala\",\n      \"source_sha256\": \"787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16\"\n    },\n    {\n      \"bytes\": 3925,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/common.scala\",\n      \"destination_sha256\": \"ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb\",\n      \"source\": \"src/resource/hardfloat/common.scala\",\n      \"source_sha256\": \"ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb\"\n    },\n    {\n      \"bytes\": 2853,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/fNFromRecFN.scala\",\n      \"destination_sha256\": \"7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d\",\n      \"source\": \"src/resource/hardfloat/fNFromRecFN.scala\",\n      \"source_sha256\": \"7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d\"\n    },\n    {\n      \"bytes\": 5105,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/primitives.scala\",\n      \"destination_sha256\": \"134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31\",\n      \"source\": \"src/resource/hardfloat/primitives.scala\",\n      \"source_sha256\": \"134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31\"\n    },\n    {\n      \"bytes\": 3037,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromFN.scala\",\n      \"destination_sha256\": \"39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce\",\n      \"source\": \"src/resource/hardfloat/rawFloatFromFN.scala\",\n      \"source_sha256\": \"39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce\"\n    },\n    {\n      \"bytes\": 2885,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromIN.scala\",\n      \"destination_sha256\": \"d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8\",\n      \"source\": \"src/resource/hardfloat/rawFloatFromIN.scala\",\n      \"source_sha256\": \"d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8\"\n    },\n    {\n      \"bytes\": 2877,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromRecFN.scala\",\n      \"destination_sha256\": \"bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317\",\n      \"source\": \"src/resource/hardfloat/rawFloatFromRecFN.scala\",\n      \"source_sha256\": \"bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317\"\n    },\n    {\n      \"bytes\": 2352,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/recFNFromFN.scala\",\n      \"destination_sha256\": \"90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d\",\n      \"source\": \"src/resource/hardfloat/recFNFromFN.scala\",\n      \"source_sha256\": \"90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d\"\n    },\n    {\n      \"bytes\": 3237,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/resizeRawFloat.scala\",\n      \"destination_sha256\": \"702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561\",\n      \"source\": \"src/resource/hardfloat/resizeRawFloat.scala\",\n      \"source_sha256\": \"702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561\"\n    },\n    {\n      \"bytes\": 811,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/Precision.scala\",\n      \"destination_sha256\": \"4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b\",\n      \"source\": \"src/main/scala/QuantCommon/Precision.scala\",\n      \"source_sha256\": \"4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b\"\n    },\n    {\n      \"bytes\": 395,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FpBackend.scala\",\n      \"destination_sha256\": \"053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709\",\n      \"source\": \"src/main/scala/QuantCommon/FpBackend.scala\",\n      \"source_sha256\": \"053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709\"\n    },\n    {\n      \"bytes\": 18853,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/XilinxFpCompat.scala\",\n      \"destination_sha256\": \"f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7\",\n      \"source\": \"src/main/scala/QuantCommon/XilinxFpCompat.scala\",\n      \"source_sha256\": \"f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7\"\n    },\n    {\n      \"bytes\": 10596,\n      \"destination\": \"accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FP32.scala\",\n      \"destination_sha256\": \"f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5\",\n      \"source\": \"src/main/scala/QuantCommon/FP32.scala\",\n      \"source_sha256\": \"f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5\"\n    }\n  ],\n  \"policy\": {\n    \"read_only_for_repair_agent\": true,\n    \"rounding\": \"HardFloat round_near_even\",\n    \"simulator_only_arithmetic\": false,\n    \"synthesizable\": true\n  },\n  \"schema_version\": \"spatialaccagent.trusted_numeric_support.v1\",\n  \"source\": \"existing repository HardFloat and QuantCommon Chisel-7-compatible implementation\",\n  \"status\": \"pass\"\n}\n",
      "path": "accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/trusted_numeric_support.json",
      "sha256": "eb82c6932d3ecc330e1efc50bd4122f34114cd4f7143de552d29f2362ec2fbc0",
      "truncated": false
    },
    {
      "bytes": 983,
      "content": "{\n  \"cache_reused\": false,\n  \"command\": [\n    \"sbt\",\n    \"--no-server\",\n    \"Compile/compile\"\n  ],\n  \"input_fingerprint_sha256\": \"1eb33dcfb41d50455b76c3363f22ebf82df653b542945cb76015db5cd3118f40\",\n  \"result\": {\n    \"duration_sec\": 4.4789251450274605,\n    \"returncode\": 0,\n    \"status\": \"pass\",\n    \"stderr_tail\": \"\",\n    \"stdout_tail\": \"[info] welcome to sbt 1.9.7 (Eclipse Adoptium Java 17.0.17)\\n[info] loading project definition from /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/project\\n[info] loading settings for project root from build.sbt ...\\n[info] set current project to spatialaccagent-generated (in build file:/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/)\\n[success] Total time: 1 s, completed Jul 11, 2026, 9:59:20 AM\\n\",\n    \"summary\": \"returncode=0\"\n  },\n  \"schema_version\": \"spatialaccagent.trusted_numeric_support_compile.v1\",\n  \"status\": \"pass\"\n}\n",
      "path": "accagent/runs/spatialacc_qwen_agent_fast_run/repair_execution/trusted_numeric_support_compile.json",
      "sha256": "3f179febba967336419f0dcb5450eefa7e27f32cfe600a91ba6562bc2df3c61f",
      "truncated": false
    }
  ],
  "editable_contract": {
    "allowed_create_or_replace_roots": [
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/semantic_harness",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/semantic_harness"
    ],
    "allowed_exact_files": [
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json"
    ],
    "approved_bounded_template_repair_exact_files": [
      "accagent/framework/templates/operator_chisel/Common.scala",
      "accagent/framework/templates/operator_chisel/Elementwise.scala",
      "accagent/framework/templates/operator_chisel/Linear.scala",
      "accagent/framework/templates/operator_chisel/Norm.scala",
      "accagent/framework/templates/operator_chisel/Residual.scala",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Common.scala",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Elementwise.scala",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Linear.scala",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Norm.scala",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/spatialaccagent/templates/Residual.scala"
    ],
    "bounded_template_repair_approved": true,
    "forbidden": [
      "all input, checkpoint, target-model reference, golden-output, verification-report, certificate, checker, and numeric-policy files",
      "all existing generated DUT modules; this capability repair may add harness wrappers but may not patch datapath RTL before a real localized DUT failure",
      "behavioral replacement of the DUT, identity/default bypasses, sampled weights, random expected output, or RTL-derived golden output"
    ],
    "read_only_generated_dut_sources": [
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Activation.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/AttentionGQA.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ElementwiseMul.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GatedMLP.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GeneratedAcceleratorTop.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/GeneratedAxiDdrTop.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_1.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_2.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Linear_4.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/LlamaStyleBlock.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/QKVProjection.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Queue1792_StreamBeat.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/Queue4_StreamBeat.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/QwenMultiLayerSystemTop.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/RMSNorm.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ResidualAdd.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/RoPE.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/VectorNorm.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ram_1792x256.sv",
      "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/ram_4x129.sv"
    ],
    "read_only_template_sources": [
      "accagent/framework/templates/operator_chisel/Common.scala",
      "accagent/framework/templates/operator_chisel/Elementwise.scala",
      "accagent/framework/templates/operator_chisel/Linear.scala",
      "accagent/framework/templates/operator_chisel/Norm.scala",
      "accagent/framework/templates/operator_chisel/Residual.scala"
    ],
    "semantic_template_repair_approved": true,
    "semantic_template_repair_boundary": {
      "allowed": [
        "selected operator-template internal datapath and state-machine correction",
        "selected template internal stream/interface correction required by target-model semantics",
        "synthesizable implementation of the frozen numeric contract"
      ],
      "approval_source": "current user instruction to run the agent-owned real-tool root-cause/code-repair loop",
      "preserved": [
        "external accelerator and board/runtime ABI",
        "pipeline semantic stage order",
        "model dimensions and target tensor semantics",
        "numeric policy and comparison thresholds",
        "real checkpoint/input/golden/checker artifacts"
      ]
    }
  },
  "phase": {
    "id": "basic_ieee_operators",
    "objective": "Implement the frozen IEEE arithmetic and real-weight consumption for Linear, VectorNorm/RMSNorm, ElementwiseMul, and ResidualAdd. Linear must consume the declared tiled real weights without an identity/default path; RMSNorm must load gamma and compute x/sqrt(mean(x^2)+epsilon)*gamma over the complete vector; elementwise multiply and residual add must operate on numeric values rather than their IEEE encodings. Common.scala may contain shared synthesizable conversion/arithmetic helpers.",
    "required_template_files": [
      "Linear.scala",
      "Norm.scala",
      "Elementwise.scala",
      "Residual.scala"
    ],
    "template_files": [
      "Common.scala",
      "Linear.scala",
      "Norm.scala",
      "Elementwise.scala",
      "Residual.scala"
    ]
  },
  "read_only_dependency_template_files": [],
  "schema_version": "spatialaccagent.semantic_template_repair_phase_bundle.v1",
  "trusted_numeric_support": {
    "blockers": [],
    "files": [
      {
        "bytes": 8776,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/AddRecFN.scala",
        "destination_sha256": "2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85",
        "source": "src/resource/hardfloat/AddRecFN.scala",
        "source_sha256": "2746fea3b3291a8db97999a45303878fdeabc0a0c8acb318f4da4f52dda54a85"
      },
      {
        "bytes": 3476,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/CompareRecFN.scala",
        "destination_sha256": "b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d",
        "source": "src/resource/hardfloat/CompareRecFN.scala",
        "source_sha256": "b319e37c7e6c455a0bf39490a250e8b5ad8dbe54e22fa434f4f9ada134fe063d"
      },
      {
        "bytes": 4428,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64.scala",
        "destination_sha256": "ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0",
        "source": "src/resource/hardfloat/DivSqrtRecF64.scala",
        "source_sha256": "ce3c19d7433fef9a73044d80b4fbcd79466110fc527f6e40d91d83de2ad1dbd0"
      },
      {
        "bytes": 33929,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecF64_mulAddZ31.scala",
        "destination_sha256": "9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776",
        "source": "src/resource/hardfloat/DivSqrtRecF64_mulAddZ31.scala",
        "source_sha256": "9ea19322eafb96006feb9cdee0da451dff59347459c5f4ac6813ea23f2fad776"
      },
      {
        "bytes": 20218,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/DivSqrtRecFN_small.scala",
        "destination_sha256": "e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f",
        "source": "src/resource/hardfloat/DivSqrtRecFN_small.scala",
        "source_sha256": "e4c9fbce80b15e693533c2af2b6cd827f5879788f650bde94c86554769edf92f"
      },
      {
        "bytes": 3417,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/INToRecFN.scala",
        "destination_sha256": "92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb",
        "source": "src/resource/hardfloat/INToRecFN.scala",
        "source_sha256": "92090ded1e774a75811931ea4bd7e23fcb671ffbb5a55d9b2826a04d5c6d83eb"
      },
      {
        "bytes": 15293,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulAddRecFN.scala",
        "destination_sha256": "be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037",
        "source": "src/resource/hardfloat/MulAddRecFN.scala",
        "source_sha256": "be8ad43e761922ca479c8814f0ab202eef77a45bbfb17c83d70e10f2e78ff037"
      },
      {
        "bytes": 5706,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/MulRecFN.scala",
        "destination_sha256": "cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d",
        "source": "src/resource/hardfloat/MulRecFN.scala",
        "source_sha256": "cf42850379c249a97a073ac436ff6b4c564b56177e868c3e912be2f246243e1d"
      },
      {
        "bytes": 6827,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToIN.scala",
        "destination_sha256": "e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3",
        "source": "src/resource/hardfloat/RecFNToIN.scala",
        "source_sha256": "e56257592e88614f6be34877a3a9f412fdc09b1c4210ee3dfeaa6c67fdc670f3"
      },
      {
        "bytes": 3958,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RecFNToRecFN.scala",
        "destination_sha256": "97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09",
        "source": "src/resource/hardfloat/RecFNToRecFN.scala",
        "source_sha256": "97042141693cd2e8aaa90f88ee39d2c3c4177fc76c48f9ad46aaea71fee34f09"
      },
      {
        "bytes": 13901,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/RoundAnyRawFNToRecFN.scala",
        "destination_sha256": "31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d",
        "source": "src/resource/hardfloat/RoundAnyRawFNToRecFN.scala",
        "source_sha256": "31cdb3be147471d52e721f14914031c19b915bd7aaffe5c0e333393a0c7fb67d"
      },
      {
        "bytes": 2880,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/classifyRecFN.scala",
        "destination_sha256": "787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16",
        "source": "src/resource/hardfloat/classifyRecFN.scala",
        "source_sha256": "787aa923a8b5f7bc13550183339fc5e38b8d3ca505dcdd3bec032dc8bb19bf16"
      },
      {
        "bytes": 3925,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/common.scala",
        "destination_sha256": "ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb",
        "source": "src/resource/hardfloat/common.scala",
        "source_sha256": "ea83cdfac50db84f372d624ce4e0d45188207164a6a1eae5d42d8174241925cb"
      },
      {
        "bytes": 2853,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/fNFromRecFN.scala",
        "destination_sha256": "7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d",
        "source": "src/resource/hardfloat/fNFromRecFN.scala",
        "source_sha256": "7a114540c32ef9e43152e37d1610dd5bbb68dba6b3bbd1aa5600fa3bc411fa6d"
      },
      {
        "bytes": 5105,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/primitives.scala",
        "destination_sha256": "134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31",
        "source": "src/resource/hardfloat/primitives.scala",
        "source_sha256": "134cfae67052244a836aebbae3f9252b0e9bf4800ab5cbcba4b92eb1c56e7c31"
      },
      {
        "bytes": 3037,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromFN.scala",
        "destination_sha256": "39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce",
        "source": "src/resource/hardfloat/rawFloatFromFN.scala",
        "source_sha256": "39fb14ae28318821906f68ad63803ca24eecb1115bf24aa4f3df497392357dce"
      },
      {
        "bytes": 2885,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromIN.scala",
        "destination_sha256": "d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8",
        "source": "src/resource/hardfloat/rawFloatFromIN.scala",
        "source_sha256": "d82c1285d20523fe0bcf7a32e2a2307ea76c3c2581ec0c329f8914004555c1e8"
      },
      {
        "bytes": 2877,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/rawFloatFromRecFN.scala",
        "destination_sha256": "bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317",
        "source": "src/resource/hardfloat/rawFloatFromRecFN.scala",
        "source_sha256": "bf7e4b0e453569c91f6a9d8c414feb3a5fed6dc7354ba31cdc8c7c0f1ffd8317"
      },
      {
        "bytes": 2352,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/recFNFromFN.scala",
        "destination_sha256": "90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d",
        "source": "src/resource/hardfloat/recFNFromFN.scala",
        "source_sha256": "90060c571a38718330f8781ecc4f555096ac45a0c75abb3fe5219e06dacdbd2d"
      },
      {
        "bytes": 3237,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/hardfloat/resizeRawFloat.scala",
        "destination_sha256": "702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561",
        "source": "src/resource/hardfloat/resizeRawFloat.scala",
        "source_sha256": "702084355b5b1d825ed0885ee2e014091d76ba08f07b071cb77bcb4cb392d561"
      },
      {
        "bytes": 811,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/Precision.scala",
        "destination_sha256": "4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b",
        "source": "src/main/scala/QuantCommon/Precision.scala",
        "source_sha256": "4e22ee7a0a55b758aa1c1b30eb8346143431e929ecba195c0681d75e25c5a05b"
      },
      {
        "bytes": 395,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FpBackend.scala",
        "destination_sha256": "053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709",
        "source": "src/main/scala/QuantCommon/FpBackend.scala",
        "source_sha256": "053d1be012e3db88dc3d673a6cd294a139315c6f0dc3e69d78181e2d934b4709"
      },
      {
        "bytes": 18853,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/XilinxFpCompat.scala",
        "destination_sha256": "f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7",
        "source": "src/main/scala/QuantCommon/XilinxFpCompat.scala",
        "source_sha256": "f2542c11ded81a17af4cf8db508114c09047d0d6e338af0b71eff031cda9e7a7"
      },
      {
        "bytes": 10596,
        "destination": "accagent/runs/spatialacc_qwen_agent_fast_run/generated/chisel/src/main/scala/QuantCommon/FP32.scala",
        "destination_sha256": "f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5",
        "source": "src/main/scala/QuantCommon/FP32.scala",
        "source_sha256": "f0758e7c275d5048303d78a623eceffa2b5c3dc0cd2dbb61d09665268a4286f5"
      }
    ],
    "policy": {
      "read_only_for_repair_agent": true,
      "rounding": "HardFloat round_near_even",
      "simulator_only_arithmetic": false,
      "synthesizable": true
    },
    "schema_version": "spatialaccagent.trusted_numeric_support.v1",
    "source": "existing repository HardFloat and QuantCommon Chisel-7-compatible implementation",
    "status": "pass"
  }
}
</semantic_template_repair_phase_bundle>

<semantic_template_repair_progress>
{
  "completed_phase_ids": [
    "bounded_nonlinear_operators",
    "operator_composition"
  ],
  "current_phase_id": "basic_ieee_operators",
  "global_status": "repair_in_progress"
}
</semantic_template_repair_progress>

<llm_policy>
{
  "api_key_configured": true,
  "configuration_error": "",
  "endpoint_configured": true,
  "enforce": true,
  "locked_model": "gpt-5.6-sol",
  "mode": "llm",
  "model": "gpt-5.6-sol",
  "model_override_approval_path": "",
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
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0252",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0253",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T12:38:45+00:00",
      "transition_id": "transition.0164"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0254",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0255",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0256",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0257",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T15:00:27+00:00",
      "transition_id": "transition.0166"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0258",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-23T15:01:38+00:00",
      "transition_id": "transition.0167"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0259",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T15:06:42+00:00",
      "transition_id": "transition.0168"
    }
  ],
  "open_backtrack_requests": [],
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0097",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:44:34+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0098",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T13:48:39+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0099",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:28:43+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0100",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:34:52+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0101",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-22T04:40:47+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0102",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-23T14:54:07+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0103",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-23T15:00:27+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0104",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-23T15:06:42+00:00"
    }
  ],
  "policy": "SACG memory is the long-context design memory for preserving goals, failures, lessons, retry needs, and cross-layer consistency across stages.",
  "recent_contamination_barriers": [
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0252",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0253",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T12:38:45+00:00",
      "transition_id": "transition.0164"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0254",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0255",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0256",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0257",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T15:00:27+00:00",
      "transition_id": "transition.0166"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0258",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-23T15:01:38+00:00",
      "transition_id": "transition.0167"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0259",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T15:06:42+00:00",
      "transition_id": "transition.0168"
    }
  ],
  "recent_failure_lessons": [
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0097",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest and only executed failing current-layer gate is real_tool.case_multilayer_pipeline, whose checker report proves incomplete all-target-layer Transformer-block DUT weight binding and a missing hash-verified multi-layer pipeline harness. The detailed board-wrapped VCS simulator was not run because prerequisite gates failed, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, order, deadlock, DDR, or AXI-protocol defect. Exact board-interface discovery passed, and certified operator-leaf and connected single-layer evidence remains reusable because no current boundary trace contradicts it and SACG truth has zero open backtrack requests. SACG truth nevertheless has 30 active contamination barriers and 12 open retry requests; prior rejected Stage7 and Stage8 artifacts are planning/debug evidence only until a clean retry passes the selected DAG, receives checker-bound promotion evidence, and completes SACG trust reconciliation. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but its stale assertion that SACG has no active blockers is superseded by sacg_memory_truth and cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-13T09:44:34+00:00",
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
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0098",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing; case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
      "timestamp": "2026-07-16T13:48:39+00:00",
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
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0099",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "stage": "stage7.verification",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "violated_constraints": [
        "constraint.verification.functional_scope"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0100",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-16T14:34:52+00:00",
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
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0101",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts; case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']; real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence.",
      "timestamp": "2026-07-22T04:40:47+00:00",
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
      "failure_class": "verification_real_tool_or_gate",
      "id": "failure_lesson.0102",
      "recommended_action": "Use contract-guided debug closure first: localize the failing transaction to a boundary/root-candidate slice, then let Stage8 repair only that causal slice or backtrack to Stage6 if gate/tool contracts are incomplete.",
      "retry_scope": "stage7_or_stage6_backtrack",
      "stage": "stage7.verification",
      "summary": "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files; case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']; hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled.",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.verification.hierarchy",
        "constraint.tool.protocols",
        "constraint.deployment.board"
      ]
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0103",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files; case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']; hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled.",
      "timestamp": "2026-07-23T15:00:27+00:00",
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
      "failure_class": "bounded_repair_required",
      "id": "failure_lesson.0104",
      "recommended_action": "Execute or approve the bounded repair workflow, then rerun Stage7. Do not continue to backend/board closure with unresolved verification failures.",
      "retry_scope": "repair_then_stage7_rerun",
      "stage": "stage8.repair",
      "summary": "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files; case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']; required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']; hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run; verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled.",
      "timestamp": "2026-07-23T15:06:42+00:00",
      "violated_constraints": [
        "constraint.verification.plan",
        "constraint.tool.protocols",
        "constraint.human.boundary",
        "constraint.case.adapter"
      ]
    }
  ],
  "recent_stage_outcomes": [
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block promotion. The earliest and only executed failing current-layer gate is real_tool.case_multilayer_pipeline, whose checker report proves incomplete all-target-layer Transformer-block DUT weight binding and a missing hash-verified multi-layer pipeline harness. The detailed board-wrapped VCS simulator was not run because prerequisite gates failed, so the aggregate functional_sim=fail state is not evidence of an RTL value, liveness, order, deadlock, DDR, or AXI-protocol defect. Exact board-interface discovery passed, and certified operator-leaf and connected single-layer evidence remains reusable because no current boundary trace contradicts it and SACG truth has zero open backtrack requests. SACG truth nevertheless has 30 active contamination barriers and 12 open retry requests; prior rejected Stage7 and Stage8 artifacts are planning/debug evidence only until a clean retry passes the selected DAG, receives checker-bound promotion evidence, and completes SACG trust reconciliation. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but its stale assertion that SACG has no active blockers is superseded by sacg_memory_truth and cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0106",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-13T09:44:34+00:00",
      "transition_id": "transition.0155"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_multilayer_pipeline: returncode=1 report_status=fail blockers=DUT binding does not cover every transformer-block weight in every target layer; hash-verified multi-layer pipeline harness is missing",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_simulation_manifest.json', '/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_multilayer_pipeline=fail; dependency_blocked=['case_axi_ddr_interface=not_run', 'case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: case_multilayer_pipeline=fail, functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=not_run, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json"
      ],
      "id": "stage_outcome.0107",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "transition_id": "transition.0159"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0108",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=board_axi_ddr_closure status=fail",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0109",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "transition_id": "transition.0162"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_axi_ddr_interface: returncode=1 report_status=fail blockers=simulation.status is not ready/pass; simulation.source_identity_sha256 does not bind the current identity document; simulation.vcs_compile_plan.compile_authority does not bind the identity's exact Vivado export facts; simulation.vcs_compile_plan.ordered_commands[0].authority_refs do not bind exact Vivado export contexts",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: DUT real-weight binding manifest status is incomplete, expected pass: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/generated/memory/dut_weight_binding_manifest.json; board_testbench_artifact_loading files missing: ['/home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/board_simulation/board_tb.sv']; dependency_blocked=['case_multilayer_pipeline will be produced and judged by the current Stage7 tool scope', 'case_multilayer_functional will be produced and judged by the current Stage7 tool scope', 'case_axi_ddr_interface will be produced and judged by the current Stage7 tool scope', 'case_axi_protocol_check will be produced and judged by the current Stage7 tool scope', 'case_ddr_image_roundtrip will be produced and judged by the current Stage7 tool scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_axi_ddr_interface=fail; dependency_blocked=['case_vcs_functional_sim=not_run', 'case_vcs_evidence_analyzer=not_run', 'case_deadlock_axi_check=not_run', 'case_multilayer_functional=not_run', 'case_pipeline_deadlock_check=not_run', 'case_axi_protocol_check=not_run', 'case_ddr_image_roundtrip=not_run', 'case_board_semantic_evidence=not_run', 'functional_sim: blocked by prerequisite gate [case_vcs_functional_sim=not_run]']",
        "real_weight_semantic_evidence_check: real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "hierarchical_verification_maturity_check: multilayer_pipeline_functional: functional_sim=fail, case_multilayer_functional=not_run, case_pipeline_deadlock_check=not_run; axi_ddr_functional: case_axi_ddr_interface=fail, functional_sim=fail, case_axi_protocol_check=not_run, case_ddr_image_roundtrip=not_run, case_board_semantic_evidence=not_run; real-weight semantic evidence contract failed: axi_ddr_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json; multilayer_pipeline_functional: semantic evidence report is missing: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_evidence/board_axi_ddr.json",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject board_axi_ddr_closure and block backend promotion. The earliest executed failing current-layer gate is real_tool.case_axi_ddr_interface. Its fail-closed report identifies board-simulation readiness and provenance defects: the simulation manifest is not ready, its source-identity hash does not bind the current exact board identity, compile authority and command authority references do not bind the cited Vivado export contexts, and compile executables are not authorized by the current tool profile or cited export evidence. The real board-wrapped VCS simulator did not execute because this prerequisite failed, so aggregate functional_sim=fail is an unsatisfied gate, not evidence of an RTL value, liveness, data-order, deadlock, DDR, or AXI-protocol defect. Operator-leaf and connected single-layer certificates remain reusable because no current boundary trace contradicts them and sacg_memory_truth has zero open backtrack requests. However, sacg_memory_truth authoritatively reports 39 active contamination barriers and 15 open retry requests; these supersede the specialist review's stale no-blocker statement and keep prior rejected Stage7/Stage8 outputs restricted to planning and debug use. The conditional specialist review supports the capability-gap classification and bounded repair sequence, but cannot replace checker or real-tool evidence."
      ],
      "id": "stage_outcome.0110",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    },
    {
      "artifacts": [
        "artifact.stage7.verification_result"
      ],
      "errors": [
        "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']",
        "hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled."
      ],
      "id": "stage_outcome.0111",
      "next_actions": [
        "run stage8.repair or backtrack to stage6 when gate DAG/tool protocol is incomplete"
      ],
      "retryable": true,
      "stage": "stage7.verification",
      "status": "needs_repair",
      "summary": "Stage7 execution_scope=operator_leaf_closure status=fail",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']",
        "hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled."
      ],
      "id": "stage_outcome.0112",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-23T15:00:27+00:00",
      "transition_id": "transition.0166"
    },
    {
      "artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "errors": [
        "real_tool.case_semantic_testbench: returncode=1 report_status=incomplete blockers=stage_00_rms_norm_1: harness has no hash-verified source files; stage_01_self_attention: harness has no hash-verified source files; stage_02_residual_add_1: harness has no hash-verified source files; stage_03_rms_norm_2: harness has no hash-verified source files",
        "case_functional_sim_precondition_check: real functional simulation preconditions failed: semantic testbench manifest status is incomplete, expected ready: /home/remote/workspace/Qwen2-Accelerator/accagent/runs/spatialacc_qwen_agent_fast_run/verification/semantic_testbench/semantic_testbench_manifest.json; dependency_blocked=['case_real_weight_artifacts will be produced and judged by the current Stage7 tool scope', 'case_leaf_functional will be produced and judged by the current Stage7 tool scope', 'case_leaf_golden_compare will be produced and judged by the current Stage7 tool scope', 'case_single_layer_functional is pending later verification scope', 'case_multilayer_pipeline is pending later verification scope', 'case_multilayer_functional is pending later verification scope', 'case_axi_ddr_interface is pending later verification scope', 'case_axi_protocol_check is pending later verification scope', 'case_ddr_image_roundtrip is pending later verification scope']",
        "required_real_tool_evidence_check: required real-tool evidence missing or failed: case_semantic_testbench=fail; dependency_blocked=['case_leaf_functional=not_run', 'case_leaf_golden_compare=not_run', 'case_operator_leaf_semantic_evidence=not_run']",
        "hierarchical_verification_maturity_check: operator_leaf_functional: case_semantic_testbench=fail, case_leaf_functional=not_run, case_leaf_golden_compare=not_run, case_operator_leaf_semantic_evidence=not_run",
        "verification_agent_decision_check: verification.evidence_classifier: needs_repair: Authoritative Stage7 decision: reject operator_leaf_closure and block promotion. The earliest executed failing current-layer gate is real_tool.case_semantic_testbench. Its returncode=1 report is incomplete because all nine operator-leaf harnesses lack hash-verified source-file records. Consequently case_leaf_functional, case_leaf_golden_compare, and case_operator_leaf_semantic_evidence were dependency-blocked and not run. This is a checker/harness provenance and verification-capability gap, not evidence of an RTL value, liveness, ordering, or protocol defect. Real checkpoint catalog, independent target-model reference, boundary contracts, leaf static structure, and the frozen numeric policy passed, but static and provenance evidence cannot replace executed leaf simulation and golden comparison. No conditional specialist review was triggered. SACG truth reports 45 active contamination barriers, 18 open retry requests, and zero open backtrack requests; prior rejected Stage7/Stage8 artifacts remain planning/debug evidence until a clean, checker-bound retry supersedes them and trust state is reconciled."
      ],
      "id": "stage_outcome.0113",
      "next_actions": [
        "complete bounded repair workflow and rerun Stage7"
      ],
      "retryable": true,
      "stage": "stage8.repair",
      "status": "needs_repair",
      "summary": "repair_status=needs_repair workflow_status=ready",
      "timestamp": "2026-07-23T15:06:42+00:00",
      "transition_id": "transition.0168"
    }
  ],
  "schema_version": "spatialaccagent.sacg_memory.v0"
}
</sacg_memory>

<sacg_memory_truth>
{
  "active_contamination_barrier_count": 51,
  "active_contamination_barriers": [
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0228",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T05:48:26+00:00",
      "transition_id": "transition.0147"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0229",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:21:23+00:00",
      "transition_id": "transition.0148"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0230",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:21:23+00:00",
      "transition_id": "transition.0148"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0231",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:21:23+00:00",
      "transition_id": "transition.0148"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0232",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T08:26:28+00:00",
      "transition_id": "transition.0149"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0233",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T08:28:09+00:00",
      "transition_id": "transition.0150"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0234",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0235",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0236",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T08:39:55+00:00",
      "transition_id": "transition.0151"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0237",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T09:16:02+00:00",
      "transition_id": "transition.0152"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0238",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-13T09:21:47+00:00",
      "transition_id": "transition.0153"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0239",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0240",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0241",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-13T09:38:23+00:00",
      "transition_id": "transition.0154"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0242",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-13T09:44:34+00:00",
      "transition_id": "transition.0155"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0243",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:24:32+00:00",
      "transition_id": "transition.0156"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0244",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:28:03+00:00",
      "transition_id": "transition.0157"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0245",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-16T13:30:03+00:00",
      "transition_id": "transition.0158"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0246",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T13:48:39+00:00",
      "transition_id": "transition.0159"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0247",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:04:49+00:00",
      "transition_id": "transition.0160"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0248",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0249",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0250",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-16T14:28:43+00:00",
      "transition_id": "transition.0161"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0251",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-16T14:34:52+00:00",
      "transition_id": "transition.0162"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0252",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-22T04:40:47+00:00",
      "transition_id": "transition.0163"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0253",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair execution completed; Stage 7 verification rerun is required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T12:38:45+00:00",
      "transition_id": "transition.0164"
    },
    {
      "artifact_id": "artifact.stage7.verification_result",
      "id": "contamination_barrier.0254",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage7.real_tool_results",
      "id": "contamination_barrier.0255",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage7.debug_closure",
      "id": "contamination_barrier.0256",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more framework static checks failed",
      "status": "active",
      "timestamp": "2026-07-23T14:54:07+00:00",
      "transition_id": "transition.0165"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0257",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T15:00:27+00:00",
      "transition_id": "transition.0166"
    },
    {
      "artifact_id": "artifact.stage8.repair_execution_report",
      "id": "contamination_barrier.0258",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "one or more repair execution steps failed",
      "status": "active",
      "timestamp": "2026-07-23T15:01:38+00:00",
      "transition_id": "transition.0167"
    },
    {
      "artifact_id": "artifact.stage8.repair_plan",
      "id": "contamination_barrier.0259",
      "policy": "Downstream stages must treat artifacts from rejected transitions as planning/debug evidence only, not validated design inputs.",
      "reason": "repair actions are required before promotion",
      "status": "active",
      "timestamp": "2026-07-23T15:06:42+00:00",
      "transition_id": "transition.0168"
    }
  ],
  "active_contamination_barriers_truncated": true,
  "open_backtrack_request_count": 0,
  "open_backtrack_requests": [],
  "open_backtrack_requests_truncated": false,
  "open_retry_request_count": 21,
  "open_retry_requests": [
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0084",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-12T11:39:06+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0085",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-12T11:41:54+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0086",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T03:59:05+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0087",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T04:01:36+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0088",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T04:15:41+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0089",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T04:19:31+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0090",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T05:41:26+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0091",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T05:46:48+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0092",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:21:23+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0093",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:26:28+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0094",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T08:39:55+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0095",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:16:02+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0096",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:38:23+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0097",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-13T09:44:34+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0098",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T13:48:39+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0099",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:28:43+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0100",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-16T14:34:52+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0101",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-22T04:40:47+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage7.verification_result"
      ],
      "id": "retry_request.0102",
      "reason": "Stage7 verification result did not pass all selected real-tool/checker gates",
      "required_inputs": [
        "artifact.stage6.verification_artifact_contract",
        "artifact.stage6.llm_action_audit"
      ],
      "stage": "stage7.verification",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-23T14:54:07+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0103",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-23T15:00:27+00:00"
    },
    {
      "blocked_artifacts": [
        "artifact.stage8.repair_plan"
      ],
      "id": "retry_request.0104",
      "reason": "Bounded repair actions must be completed before verification can be promoted",
      "required_inputs": [
        "artifact.stage8.repair_plan"
      ],
      "stage": "stage8.repair",
      "status": "open",
      "target_stage": "stage7.verification",
      "timestamp": "2026-07-23T15:06:42+00:00"
    }
  ],
  "open_retry_requests_truncated": false,
  "policy": "Only active_contamination_barriers and open retry/backtrack requests in this object are current SACG-memory blockers. Historical, closed, superseded, or rejected records are recovery evidence only and must not be treated as active blockers.",
  "schema_version": "spatialaccagent.sacg_memory_truth.v0",
  "truth_source": "source_sacg_state.memory"
}
</sacg_memory_truth>

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

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "adaptive_observation_decision": {
      "additionalProperties": false,
      "properties": {
        "evidence_refs": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "field_observations": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "evidence_pointer": {
                "type": "string"
              },
              "interpretation": {
                "type": "string"
              },
              "observed_value": {},
              "semantic_role": {
                "enum": [
                  "control",
                  "handshake",
                  "payload",
                  "counter",
                  "state",
                  "error",
                  "contract"
                ],
                "type": "string"
              }
            },
            "required": [
              "evidence_pointer",
              "observed_value",
              "semantic_role",
              "interpretation"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "frontier_id": {
          "type": "string"
        },
        "mode": {
          "enum": [
            "direct_executed_contradiction",
            "direct_tool_failure",
            "deepen_simulation_observation"
          ],
          "type": "string"
        },
        "probe_plan": {
          "additionalProperties": false,
          "properties": {
            "add_or_update_probe_ids": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "bounded_window": {
              "type": "string"
            },
            "event_match": {
              "additionalProperties": {
                "type": [
                  "string",
                  "number",
                  "integer",
                  "boolean",
                  "null"
                ]
              },
              "type": "object"
            },
            "required_event_fields": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "retire_probe_ids": {
              "items": {
                "type": "string"
              },
              "type": "array"
            },
            "target_boundary": {
              "type": "string"
            },
            "trigger_condition": {
              "type": "string"
            }
          },
          "required": [
            "target_boundary",
            "add_or_update_probe_ids",
            "retire_probe_ids",
            "required_event_fields",
            "event_match",
            "trigger_condition",
            "bounded_window"
          ],
          "type": "object"
        },
        "rationale": {
          "type": "string"
        },
        "schema_version": {
          "type": "string"
        }
      },
      "required": [
        "schema_version",
        "mode",
        "frontier_id",
        "evidence_refs",
        "field_observations",
        "probe_plan",
        "rationale"
      ],
      "type": "object"
    },
    "agent": {
      "type": "string"
    },
    "approval_required_for": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "blocked_reasons": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "causal_prediction": {
      "additionalProperties": false,
      "properties": {
        "evidence_refs": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "expected_progress_changes": {
          "items": {
            "additionalProperties": false,
            "properties": {
              "metric": {
                "type": "string"
              },
              "relation": {
                "enum": [
                  "increase_from_baseline",
                  "decrease_from_baseline",
                  "change_from_baseline",
                  "no_change_from_baseline",
                  "reach_at_least",
                  "reach_at_most"
                ],
                "type": "string"
              },
              "value": {
                "type": [
                  "number",
                  "null"
                ]
              }
            },
            "required": [
              "metric",
              "relation",
              "value"
            ],
            "type": "object"
          },
          "type": "array"
        },
        "falsified_if": {
          "type": "string"
        },
        "intervention_family": {
          "type": "string"
        },
        "target_frontier_id": {
          "type": "string"
        }
      },
      "required": [
        "intervention_family",
        "target_frontier_id",
        "expected_progress_changes",
        "falsified_if",
        "evidence_refs"
      ],
      "type": "object"
    },
    "checkpoint_impact": {
      "additionalProperties": false,
      "properties": {
        "affected_cctg_nodes": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "changed_state_elements": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "evidence_refs": {
          "items": {
            "type": "string"
          },
          "type": "array"
        },
        "rationale": {
          "type": "string"
        },
        "state_schema_change": {
          "enum": [
            "none",
            "compatible",
            "incompatible",
            "unknown"
          ],
          "type": "string"
        },
        "status": {
          "enum": [
            "ready",
            "unknown"
          ],
          "type": "string"
        }
      },
      "required": [
        "status",
        "state_schema_change",
        "affected_cctg_nodes",
        "changed_state_elements",
        "evidence_refs",
        "rationale"
      ],
      "type": "object"
    },
    "file_edits": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "content": {
            "type": "string"
          },
          "expected_sha256": {
            "type": "string"
          },
          "json_content": {
            "additionalProperties": true,
            "type": "object"
          },
          "operation": {
            "enum": [
              "create",
              "replace",
              "replace_text",
              "merge_json"
            ],
            "type": "string"
          },
          "path": {
            "type": "string"
          },
          "rationale": {
            "type": "string"
          },
          "text_replacements": {
            "items": {
              "additionalProperties": false,
              "properties": {
                "new_text": {
                  "type": "string"
                },
                "old_text": {
                  "type": "string"
                }
              },
              "required": [
                "old_text",
                "new_text"
              ],
              "type": "object"
            },
            "type": "array"
          }
        },
        "required": [
          "path",
          "operation",
          "expected_sha256",
          "content",
          "rationale"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "project_knowledge_updates": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "claim": {
            "type": "string"
          },
          "confidence": {
            "enum": [
              "high",
              "medium",
              "low"
            ],
            "type": "string"
          },
          "contradicts_knowledge_ids": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "evidence_refs": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "knowledge_kind": {
            "enum": [
              "operator_semantics",
              "ready_valid_protocol",
              "state_machine",
              "timing_relationship",
              "buffering_backpressure",
              "memory_mapping",
              "board_lifecycle",
              "negative_hypothesis",
              "causal_mechanism"
            ],
            "type": "string"
          },
          "reuse_guidance": {
            "type": "string"
          },
          "subject_ids": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "supersedes_knowledge_ids": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "timing_observations": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "validity_conditions": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "validity_scope": {
            "enum": [
              "current_source_fingerprint",
              "current_contract",
              "architecture_invariant"
            ],
            "type": "string"
          }
        },
        "required": [
          "knowledge_kind",
          "subject_ids",
          "claim",
          "timing_observations",
          "validity_scope",
          "validity_conditions",
          "evidence_refs",
          "confidence",
          "reuse_guidance",
          "supersedes_knowledge_ids",
          "contradicts_knowledge_ids"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "requested_validation": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "argv": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "cwd": {
            "type": "string"
          },
          "purpose": {
            "type": "string"
          }
        },
        "required": [
          "purpose",
          "argv",
          "cwd"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "required_capabilities": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "capability_id": {
            "type": "string"
          },
          "debug_layer": {
            "type": "string"
          },
          "producer_scope": {
            "type": "string"
          },
          "rationale": {
            "type": "string"
          },
          "required_evidence": {
            "items": {
              "type": "string"
            },
            "type": "array"
          },
          "target_modules": {
            "items": {
              "type": "string"
            },
            "type": "array"
          }
        },
        "required": [
          "capability_id",
          "debug_layer",
          "producer_scope",
          "target_modules",
          "required_evidence",
          "rationale"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "root_cause": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "stage": {
      "const": "repair_execution",
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
    "root_cause",
    "file_edits",
    "requested_validation",
    "blocked_reasons",
    "approval_required_for"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
