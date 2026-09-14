<agent>
numeric_policy_agent
</agent>

<task>
Act as the numeric precision engineer. Convert the current-run quantization materials into numeric_policy JSON.
</task>

<rules>
1. Treat the quantization materials directory as the complete current-run numeric input.
2. If no explicit quantization policy is provided, mark dtype and rounding fields unknown and record a blocking note; do not invent a default precision.
3. Use exactly the field names in the schema.
4. Do not rename default_rules to rules or default_numeric_rules.
5. Do not loosen tolerance or change numeric policy beyond the provided materials.
6. Record unclear, conflicting, or missing quantization decisions in notes so later verification does not silently assume them.
</rules>

<quantization_materials>
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
</quantization_materials>

<output_schema>
{
  "additionalProperties": true,
  "properties": {
    "default_rules": {
      "additionalProperties": true,
      "properties": {
        "acc_dtype": {
          "type": "string"
        },
        "activation_dtype": {
          "type": "string"
        },
        "rounding": {
          "type": "string"
        },
        "saturation": {
          "type": "boolean"
        },
        "scale_dtype": {
          "type": "string"
        },
        "weight_dtype": {
          "type": "string"
        }
      },
      "required": [
        "weight_dtype",
        "activation_dtype",
        "acc_dtype",
        "scale_dtype",
        "rounding",
        "saturation"
      ],
      "type": "object"
    },
    "notes": {
      "items": {
        "type": "string"
      },
      "type": "array"
    },
    "policy_id": {
      "type": "string"
    },
    "schema_version": {
      "type": "string"
    },
    "tolerance": {
      "additionalProperties": true,
      "properties": {
        "stage": {
          "type": "string"
        },
        "system": {
          "type": "string"
        }
      },
      "required": [
        "stage",
        "system"
      ],
      "type": "object"
    }
  },
  "required": [
    "schema_version",
    "policy_id",
    "default_rules",
    "tolerance",
    "notes"
  ],
  "type": "object"
}
</output_schema>

Your response will be processed by a program, not a human.
Return exactly one valid JSON object matching <output_schema>.
Do not wrap the object in another key such as result, output, or task_card.
Do not include markdown, code fences, comments, or any text outside the JSON object.
