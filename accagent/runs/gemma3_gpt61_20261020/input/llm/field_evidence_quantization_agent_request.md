<agent>
field_evidence_quantization_agent
</agent>

<task>
Act as the source-evidence engineer for the quantization input domain. Read the complete supplied domain_materials_text and extract its supported fields; candidate excerpts are optional hints, not a limit on the evidence you can extract.
</task>

<rules>
1. Deterministic regex candidates are hints only, not ground truth.
2. Accept a field only when the cited excerpt semantically supports it.
3. Each evidence item must cite source, chunk_id when available, and a short excerpt from domain_materials_text or its candidate summary.
4. Reject false positives, stale sample/scaffold interfaces, generic paths, or contradicted values.
5. Extract every supported operational host, executable, scope and environment field in tool documents. Omit a field only if the complete supplied material does not establish it; never infer tool availability without the later real probes.
</rules>

<material_corpus_summary>
{
  "complete_domain_material_is_supplied": true,
  "domain": "quantization",
  "material_chars": 8475
}
</material_corpus_summary>

<domain_materials_text>
### chunk:quantization:000001 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization/README.md offset:0-530
```text
# Quantization Input Materials

Place numeric precision and quantization materials for the current accelerator
design run here. Stage 0 treats this directory as the numeric input for this run.

Supported inputs:
- docs (`.md`, `.rst`, `.txt`)
- `.docx` and `.pdf` documents
- JSON/YAML policy snippets
- numeric notes or benchmark requirements

If no policy file is provided, the framework uses the fallback policy:
- weight/activation = FP16
- accumulation = FP32
- scale = FP16
- valid-output requirement and no-deadlock check.

```

### chunk:quantization:000002 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization/current_run_numeric_policy.md offset:0-7600
```text
# Current-Run Numeric Policy

This file is the explicit numeric policy for the current SpatialAccAgent run.
It is an input artifact, not a framework fallback and not a checker shortcut.

Default precision rules for this run:
- weight_dtype: int4
- activation_dtype: int8
- acc_dtype: int32
- scale_dtype: int32
- rounding: nearest_even
- saturation: true

Implementation contract for this run:
- W4A8 means signed INT4 learned matrix weights and signed INT8 activations,
  with INT32 accumulators and bias. QK and PV multiply activations, so their
  operands use INT8 rather than treating an activation as an INT4 weight.
- Use integer DSP MACs and integer/fixed-point arithmetic throughout the
  generated accelerator. Floating-point IP is not required and must not remain
  in the elaborated W4A8 datapath. Normalization, activation, Softmax, RoPE,
  residual scaling and requantization need explicit integer/fixed-point contracts.
- Initial defaults: symmetric signed quantization; per-output-channel weight
  scales and per-tensor activation scales; INT32 fixed-point scale multipliers
  with declared shifts, nearest-even rounding and saturating INT8 outputs.
  Bias and normalization vector parameters may use explicitly declared wider
  integer formats; W4 applies to learned matrix weights. These defaults are
  replaceable policy, not model-specific constants.
- Pack actual INT4 values densely in DDR/cache: 8 weights per 32-bit image
  word and 128 weights per 512-bit beat. Do not retain FP16/FP32 storage and
  merely relabel the metadata. Derive scale/shift metadata from real model
  weights and input calibration, never from DUT outputs.
- Preserve 512-bit DDR refill, bounded active/shadow prefetch, parallel cache
  reads, token/operator overlap, and all Transformer blocks.
- This policy supersedes the previous floating-point policy. Start new runs
  from Stage-0; old floating-point bindings, RTL, images, calibration and
  verification results are historical baselines only.

Architecture preservation for this W4A8 run:
- Quantization changes numeric formats and only the datapath/interface logic
  strictly needed to carry those formats and scales. Preserve the established
  OPT accelerator's non-quantization architecture and schedule: its pipeline
  stage ordering and overlap, full model weights in DDR, wide next-layer
  prefetch, bounded active/shadow weight caches with safe switching, activation
  ping-pong, exact board AXI/DDR wrapper, and ready/valid backpressure.
- Do not replace layer/token streaming with bulk buffering or serial execution,
  narrow the refill path, change cache ownership/prefetch behavior, alter the
  board ABI, or retime/restructure unrelated operators as part of W4A8. When a
  numeric-width change requires a local interface update, keep the surrounding
  OPT dataflow and timing contract intact and bind the actual cost to DSE.
- Preserve model topology and all operator-level token overlap. W4A8 is not
[REDACTED SENSITIVE MATERIAL]
  difference from OPT must be limited to a demonstrably necessary numeric
  representation or its transport.

Integer implementation invariants:
- A nonnegative fixed-point sigmoid/Softmax coefficient stored as UINT8 must
  be zero-extended before signed multiplication. Reinterpreting values 128..255
  directly as SINT8 changes their sign and violates this numeric policy.
- Both attention QK and PV matrix operands must be real signed INT8 values.
  Softmax may use wider internal fixed-point math, but its probabilities must
  be requantized into the declared activation domain before PV multiplication.
  Keeping Q15 probabilities in a 32-bit operand and multiplying INT8 by INT32
  is not an A8xA8 implementation; accumulator and DSP accounting must match the
  declared INT32 attention datapath.
- Derive Softmax reciprocal scaling from integer-code units. For raw exponential
  codes e and S=sum(e), e*floor(2^31/S) already represents e/S in Q31;
  shifting it right by the exponential table fraction again destroys that scale
  and can make every INT8 probability zero. A one-element unmasked row must
  produce the declared representation of unit probability. Choose and declare
  probability scales that avoid systematic all-zero underflow at admitted row
  lengths, and consume the same scale in PV/context requantization.
- Tail tiles must not change the DDR tile stride. Compute a tile start as
  base + route_offset + layer_index*layer_stride + tile_index*full_tile_stride,
  using the fixed full-tile storage geometry from the bound route. The actual
  tile_word_count controls the response length and may be smaller on the tail;
  multiplying tile_index by that shortened count addresses the wrong weights.
  Apply the same fixed-stride rule to both cache requests and board-adapter
  address validation. In the older tile-service example, tile_word_count in
  the address formula denotes full tile stride, not a shortened tail length;
  this clarification supersedes that ambiguous example.
- Bound integer Softmax sum and divider widths by the numeric range:
  summing N nonnegative E-bit codes needs at most E+ceil(log2(N)) bits,
  not N*E bits. Use that range in restoring-divider/reciprocal hardware;
  sequence length times element width describes storage size, not operand width.
- The integer elaboration branch must never construct floating-point modules,
  including unused helper multipliers outside a conditional backend branch.
  Keeping FP source code for other numeric policies is allowed; instantiating
  it in the integer hierarchy is not.
- Integer nonlinear arithmetic must remain physically reasonable: derive widths
  from activation/statistic ranges and use a bounded iterative unit, a properly
  pipelined datapath, or an explicit fixed-point approximation. Do not unroll
  dozens of full-width variable dividers into a single combinational square-root
  path; this defeats the resource and timing goals even when compilation passes.
  Bind the implemented operator latency and initiation interval into DSE.
- Unknown activation kinds must be rejected or implemented explicitly. A
  pass-through is not a replacement for a requested GELU/SiLU or other operator.

Tolerance and acceptance policy:
- stage: functional_or_shape
- system: valid_output_required
- Quantitative comparison values are intentionally omitted in this current-run
  input, so the framework must apply its versioned loose defaults. Explicit
  current-run values would override those defaults.
- The resolved values are frozen before simulation and are never derived from
  DUT output.
- For the currently authorized VCS compile/elaboration/link gate, nonfatal
  warnings alone do not justify a repair loop. In particular, compile-only
  fixtures must instantiate the real connected DUT, but do not need a complex
  generated testbench port parser solely to remove unconnected-port warnings.
  Keep the compile-only testbench minimal and spend repair work on real errors
  and the deployed kernel/top/DDR path. This does not waive actual board-top
  interface connections or replace connected-DUT elaboration with an empty tb.

Notes:
- The current end-to-end goal is board-runnable execution with valid output and
  no deadlock. Exact numerical equivalence to the source model is not required
  for this run unless a later user-provided policy strengthens the tolerance.
- Later users may replace this file with a different model-specific quantization
  policy. Checkpoint reuse must treat such changes as input changes and rerun
  the affected stages.

```
</domain_materials_text>

<deterministic_regex_candidate_summary>
{
  "policy": {
    "candidate_only": true,
    "critical_fields_must_match_evidence_when_present": true,
    "llm_output_is_not_accepted_as_evidence_without_source": true,
    "llm_semantic_confirmation_required": true,
    "regex_is_not_semantic_ground_truth": true
  },
  "schema_version": "spatialaccagent.field_evidence_summary.v0",
  "selected_fields": [
    {
      "count": 14,
      "evidence": [
        {
          "chunk_id": "quantization:000001",
          "excerpt": "ric notes or benchmark requirements If no policy file is provided, the framework uses the fallback policy: - weight/activation = FP16 - accumulation = FP32 - scale = FP16 - valid-output requirement and no-deadlock check.",
          "source": "/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization/README.md",
          "value": "fp16"
        }
      ],
      "field": "numeric_policy.default_precision"
    }
  ]
}
</deterministic_regex_candidate_summary>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "evidence": {
      "items": {
        "additionalProperties": true,
        "properties": {
          "chunk_id": {
            "type": [
              "string",
              "null"
            ]
          },
          "confidence": {
            "type": [
              "string",
              "number",
              "null"
            ]
          },
          "excerpt": {
            "type": "string"
          },
          "field": {
            "type": "string"
          },
          "reason": {
            "type": [
              "string",
              "null"
            ]
          },
          "source": {
            "type": [
              "string",
              "null"
            ]
          },
          "value": {}
        },
        "required": [
          "field",
          "value",
          "source",
          "chunk_id",
          "excerpt"
        ],
        "type": "object"
      },
      "type": "array"
    },
    "policy": {
      "additionalProperties": true,
      "type": "object"
    },
    "schema_version": {
      "type": "string"
    }
  },
  "required": [
    "schema_version",
    "policy",
    "evidence"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
