# FPGA DSE Literature And Framework Policy

Date: 2026-09-20

## Evidence-Backed Literature Takeaways

- **AutoScaleDSE** models HLS-code structure as a graph, co-explores code
  transformations and directives, and uses compatibility information to avoid
  invalid configurations. Its Random Forest is an exploration accelerator,
  not an implementation-quality oracle. [Jun et al., TRETS 2023,
  DOI:10.1145/3572959]
- **Elastic-DF** treats allocation/partitioning across a pipeline dataflow
  accelerator as a hardware resource-mapping problem. For a spatial
  accelerator, this supports making parallelism, buffering, and physical
  resource placement explicit candidate dimensions. [El Hajj et al., TRETS
  2022, DOI:10.1145/3470567]
- **TAPA** reports that task-level dataflow needs physical-design awareness;
  its coarse floorplanning is introduced during compilation to protect
  high-frequency pipelines. [Chi et al., TRETS 2023,
  DOI:10.1145/3609335]
- **FADO** co-optimizes directives and multi-die floorplanning, identifying
  routing and per-die resource limits as first-class DSE constraints. Its
  QoR-library and analytical variants are relevant contrast cases, not
  sources of authoritative QoR for this framework. [Wu et al., TRETS 2024,
  DOI:10.1145/3653458]
- The FPGA spatial-LLM study models compute and on-chip-memory resources to
  explore parallelization and buffering for model-specific spatial LLM
  accelerators. This supports treating the accelerator as a physical dataflow
  graph rather than a generic temporal overlay. [Lai et al., TRETS 2025,
  DOI:10.1145/3656177]
- **JAQ** demonstrates that joint model/hardware exploration has a large
  discrete space. It motivates retaining all semantics-preserving hardware
  parameters in a formal candidate universe instead of tuning one parameter
  in isolation. [Hu et al., AAAI 2025, DOI:10.1609/aaai.v39i20.35415]

## Adopted Policy

The framework adopts the candidate-space and physical-awareness lessons, but
does not use paper-style analytical, learned, or LLM QoR estimates to decide
the winner. They are not sufficiently authoritative for a real VU9P
app-shell closure.

1. Stage 4 materializes every legal value of every parameter that physically
   changes generated RTL, Vivado IP/XPM topology, or board-app-shell XDC.
2. A candidate is a concrete tuple of operator parallelism, stream buffering,
   activation-bank organization, role-specific BRAM/URAM layout, and any
   board-legal AXI or floorplan setting that is actually bound to generated
   implementation files.
3. Static logic checks legality only: model dimensions, stream packing, AXI
   alignment, physical memory bindings, and board-specific limits. It does
   not estimate resource, power, clock, or token/s.
4. The only QoR authority is the exact target-board sample-project app-shell
   Vivado implementation plus the synthesizable DUT cycle counter. A result
   must contain all four values: resource vector, power, achieved clock, and
   token/s.
5. The ledger accepts only two terminal outcomes: `measured` with the complete
   exact evidence set, or `infeasible` after an explicit real app-shell Vivado
   implementation failure. Remote transport, artifact copy, tool setup, and
   incomplete measurement failures are not DSE outcomes.
6. The Pareto set minimizes every resource component and power, while
   maximizing clock frequency and token/s. LLMs may select the next legal
   candidate to measure and explain the final measured Pareto choice; they may
   not invent, predict, extrapolate, or rank QoR without those measurements.

## Candidate-Dimension Admission Rule

A proposed DSE dimension is admitted only after all three conditions hold:

- it has a finite, user/model/board-derived legal domain;
- Stage 5 binds the selected value into RTL, Vivado IP/XPM parameters, or
  XDC/placement constraints; and
- Stage 7 exact app-shell implementation can observe its consequence in the
  same four metrics.

This prevents an abstract DSE parameter from creating a false optimization
degree of freedom. The current implemented dimensions are global lanes, one
global `compute_array_rows × compute_array_cols` PE array shared by every
Linear/QKV/FFN projection, FIFO depth, activation banks, and per-weight-role
BRAM/URAM banks. Each PE emits one DSP-backed Vivado `fp_mul_sp_*` instance;
the target-board Vivado report remains the authority for exact DSP48 usage.
Per-operator parallelism, AXI scheduling, pipeline-register placement, and
floorplanning must be added only together with their real code/IP/XDC bindings.
