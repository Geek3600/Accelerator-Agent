<agent>
field_evidence_quantization_agent
</agent>

<task>
Act as the source-evidence engineer for the quantization input domain. Review compact current-run candidate excerpts and return only evidence supported by those excerpts.
</task>

<rules>
1. Deterministic regex candidates are hints only, not ground truth.
2. Accept a field only when the cited excerpt semantically supports it.
3. Each evidence item must cite source, chunk_id when available, and a short excerpt from the supplied candidate summary.
4. Reject false positives, stale sample/scaffold interfaces, generic paths, or contradicted values.
5. If compact evidence is insufficient for a field, omit it rather than inventing it.
</rules>

<material_corpus_summary>
{
  "complete_domain_material_is_supplied": true,
  "domain": "quantization",
  "material_chars": 1750
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

### chunk:quantization:000002 source:/home/remote/workspace/Qwen2-Accelerator/accagent/framework/input_materials/quantization/current_run_numeric_policy.md offset:0-876
```text
# Current-Run Numeric Policy

This file is the explicit numeric policy for the current SpatialAccAgent run.
It is an input artifact, not a framework fallback and not a checker shortcut.

Default precision rules for this run:
- weight_dtype: fp16
- activation_dtype: fp16
- acc_dtype: fp32
- scale_dtype: fp16
- rounding: nearest_even
- saturation: false

Tolerance and acceptance policy:
- stage: functional_or_shape
- system: valid_output_required

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
      "count": 5,
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
