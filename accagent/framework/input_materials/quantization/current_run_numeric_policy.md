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
- Quantitative comparison values are intentionally omitted in this current-run
  input, so the framework must apply its versioned loose defaults. Explicit
  current-run values would override those defaults.
- The resolved values are frozen before simulation and are never derived from
  DUT output.

Notes:
- The current end-to-end goal is board-runnable execution with valid output and
  no deadlock. Exact numerical equivalence to the source model is not required
  for this run unless a later user-provided policy strengthens the tolerance.
- Later users may replace this file with a different model-specific quantization
  policy. Checkpoint reuse must treat such changes as input changes and rerun
  the affected stages.
