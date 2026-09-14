Use a conservative integer inference policy for the first accelerator design:

- weights are int8
- activations are int8
- matrix accumulation uses int32
- scale values are int32
- rounding uses truncate unless a stage-specific policy overrides it
- saturation is enabled
- stage-level checking may use functional or shape-valid tolerance
- system-level and board-level checking require valid output data and no deadlock
