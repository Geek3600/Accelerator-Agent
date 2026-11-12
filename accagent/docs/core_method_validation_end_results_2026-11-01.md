# Core Method Validation End Results — 2026-11-01

## Scope and evidence boundary

This report records execution of `accagent/docs/core_method_validation_end.md` (validation4). It is based on the GPT-2 Medium, sequence-length-32, W4A8, VU9P experiment snapshot used by validation3. The three workstreams were PropBench v5, TraceBench v7, and Paired Timing v5.

The experiment outputs are under `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation_20261031/`. The main machine-readable records are `propbench_v5/summary.json`, `tracebench_v7_metadata/summary.json`, `tracebench_v7_metadata/progress.json`, `tracebench_v7_rtl/summary.json`, `paired_timing_v5/summary.json`, and `validation4_integrity_audit.json`.

No new Chisel/SBT elaboration was run. Existing independent generated SV trees were reused. TraceBench VCS work was run remotely on `10.12.133.23`; local work was limited to Python analysis, hashing, small checks, and report generation. No RTL functional simulation, numerical comparison, synthesis, or board run was part of validation4.

The aspirational values embedded in the plan are not results. The measurements below retain misses, ambiguity, and costs as observed.

## PropBench v5

### Method

The runner reused the ten independent candidate trees already captured by PropBench v4. Before each retrospective manifest capture it checked candidate identity against the v4 record. The Stage-5 SV manifest binds the parameter signature, generated top-level SV membership, per-file SHA-256, generated `GeneratedDesignParams.scala` SHA-256, and a flat ANSI port/direction/range fingerprint. Each candidate's complete tree was then checked against the captured manifest.

For a partial-update negative case, the runner copied the candidate SV tree and its bound Scala source, replaced one changed SV file with the corresponding baseline file, and ran the exact manifest checker. This isolates file-level rollback detection. The manifest is retrospective: it was captured from the historical tree during this experiment and was not present when the historical Chisel run occurred.

Parameter-to-module-family rules were frozen before examining candidate diffs. These rules are template-family priors, not a learned semantic oracle. The measured quantities compare predicted families against actual changed file bytes. A byte change does not prove semantic dependence, and an unchanged byte does not prove semantic independence.

### Results

| Candidate | Changed parameter value | Changed SV files | Family-rule recall | Predicted-unrelated preservation | Partial revert detected |
|---|---:|---:|---:|---:|---|
| `rows_8` | rows 8 | 12 | 0.667 | 0.889 | yes, `Linear.sv` |
| `cols_16` | cols 16 | 15 | 0.533 | 0.806 | yes, `Linear.sv` |
| `fifo_128` | FIFO depth 128 | 7 | 0.857 | 0.955 | yes, `PhysicalStreamFifo.sv` |
| `banks_4` | activation banks 4 | 10 | 1.000 | 1.000 | yes, `PhysicalSimpleDualPortMemory_12.sv` |
| `rows_4` | rows 4 | 12 | 0.667 | 0.889 | yes, `DenseFFN.sv` |
| `cols_8` | cols 8 | 15 | 0.533 | 0.806 | yes, `DenseFFN.sv` |
| `cols_4` | cols 4 | 15 | 0.533 | 0.806 | yes, `DenseFFN.sv` |
| `fifo_32` | FIFO depth 32 | 4 | 1.000 | 1.000 | yes, `PhysicalSimpleDualPortMemory_19.sv` |
| `banks_8` | activation banks 8 | 10 | 1.000 | 1.000 | yes, `PhysicalSimpleDualPortMemory_12.sv` |
| `reuse_2` | cross-token reuse 2 | 12 | 0.500 | 0.842 | yes, `Linear.sv` |

Complete candidate manifests passed **10/10**. One-file partial rollback was rejected **10/10**. The mean declared-family byte-change recall was **0.729** and mean predicted-unrelated preservation was **0.899**. These figures are useful as a first measured dependency-rule baseline; they do not support a claim of 100% parameter propagation accuracy. The compute-array rules miss generated wrapper and memory files, the FIFO family misses a `ResidualAdd` change, and the reuse family misses memory files. Those are real observed gaps, not discarded outliers.

The prior Stage-4/Scala binding checker still passes the partial SV rollback in all ten cases (`old_binding_check.partial=pass`), while the new file manifest rejects each mixed-version tree. This directly shows which error class the file manifest detects. The retrospective manifest's protection depends on recording a trusted manifest at generation time in future production runs; the current benchmark does not retroactively prove that historical Stage-5 artifacts were originally protected.

### PCWM warning policy replay

The existing four top-level elaboration records were re-read under a stricter experiment contract that treats any `PCWM-W` port-width warning as failure even when VCS returns zero. `rows_8` had 6 warnings and `cols_16` had 10, so each is classified as a contract failure under this policy despite historical tool return code 0. `fifo_128` and `banks_4` had zero warnings and remain pass. This is a reclassification of saved VCS evidence, not a fresh `-Werror=PCWM-W` invocation. A VCS command-line warning-promotion flag was not assumed or claimed.

## TraceBench v7

### Metadata-contract arm

Ten prior stream-contract metadata faults were repaired in isolated SACG transitions. Each case ran the native pipeline static checker, native Stage-6 static stream-plan and data-order-ledger checkers, the existing remote `vlogan` source compile, and the actual `SACGStore.promote()` call. Results: **10/10 fault detected, 10/10 downstream and upstream edge endpoints included, 10/10 static repair checks pass, 10/10 remote `vlogan` pass, 10/10 promoted, zero scope violations**. Archived module-to-stage mapping replay also covered 10/10 archived syntax reports; it used no new EDA execution.

The `data_order_trace_check` in these cases is a native static ledger check. It does not run an RTL simulation or establish numerical/data-order behavior at runtime. The injected fault is a metadata mismatch explicitly reported by `check_edge_contracts`; this is checker-assisted repair, not blind root-cause discovery.

### Generated RTL port-fault arm

The ten-module cohort replaced the old uninstantiated outer `GeneratedAxiDdrTop` sample with `DenseFFN`, which has an in-package consumer. Each case independently changed one producer port name while retaining named-port labels in its consumer, ran remote VCS elaboration with the generated source closure, derived the patch from the VCS diagnostic and actual consumer declaration, authorized the exact changed file, then reran VCS and native package checks.

| Case | Producer | Initial graph candidates | Refined candidates | Projection basis | Fault VCS | Repair VCS | Promoted |
|---|---|---:|---:|---|---:|---:|---|
| F1 | `DenseFFN` | 2 | 2 | shared consumer ownership retained | 255 | 0 | yes |
| F2 | `GeneratedAcceleratorTop` | 2 | unresolved / retained original candidates | top-boundary consumer not uniquely stage-mapped | 255 | 0 | yes |
| F3 | `Attention` | 1 | 1 | unique candidate; no consumer owner | 255 | 0 | yes |
| F4 | `IntegerAttention` | 1 | 1 | producer/consumer owner intersection | 255 | 0 | yes |
| F5 | `Linear` | 1 | 1 | unique graph-bound consumer owner | 255 | 0 | yes |
| F6 | `Activation` | 1 | 1 | unique candidate; no consumer owner | 255 | 0 | yes |
| F7 | `ResidualAdd` | 1 | 1 | observed data connection plus graph predecessor | 255 | 0 | yes |
| F8 | `PhysicalStreamFifo` | 2 | 2 | shared producer/consumer ownership retained | 255 | 0 | yes |
| F9 | `WeightTileCache` | 2 | 2 | shared producer/consumer ownership retained | 255 | 0 | yes |
| F10 | `QKVProjection` | 1 | 1 | unique candidate; no consumer owner | 255 | 0 | yes |

Aggregate results: **10/10 executed; 10/10 fault elaborations failed with the intended connection diagnostic; 10/10 repaired elaborations returned 0; 10/10 exact-file authorizations; 0 scope violations; 10/10 native static promotions**. All fault and repair arms also had `vlogan` return 0. The runner checks local, uploaded, and remote source manifests through the existing helper and preserves per-case logs, patch, evidence records, and source hashes.

Consumer context is now accepted only when its source hash and artifact origin bind to the graph and the same hashed tool log contains the reported producer, instance, consumer location, and undefined-port diagnostic. A focused regression test verifies valid narrowing and rejects an invented instance.

The table is not a 10/10 unique-root result. DenseFFN, `PhysicalStreamFifo`, and `WeightTileCache` retain multiple stage candidates; the outer generated top also does not resolve to one stage. Some one-candidate rows were already unique before the consumer projection. The best evidence for actual added disambiguation is `ResidualAdd` F7, where the consumer's connected input and the graph predecessor select the first residual stage without relying on an `add1`/`add2` suffix rule. Repair success is a deterministic benchmark edit from compiler/source evidence, not an autonomous LLM repair. Promotion occurred on isolated benchmark states and does not show integration of the new authorization path into the production repair executor.

## Paired Timing v5

The full suite contains the six prior checks plus a remote `GeneratedAcceleratorTop` VCS elaboration with the XPM simulation source. The local targeted elaboration uses `DenseFFN`. Both elaboration helpers include fresh remote `vlogan` analysis; this cost is included in the measured gate. The four arms use paired, isolated snapshots. Hashing and resolver planning are included in targeted time; snapshot preparation is excluded.

| Mutation | Targeted gates | Targeted seconds | Full 7-gate seconds | Time reduction |
|---|---|---:|---:|---:|
| E1 documentation | none after resolver reports empty invalidation | 0.01799 | 32.11772 | 99.944% |
| E2 pipeline metadata | pipeline static checker | 0.02117 | 32.03216 | 99.934% |
| E3 parameter binding | DSE materialization checker | 0.01941 | 32.07468 | 99.939% |
| E4 Activation SV comment | package static + remote `vlogan` + `DenseFFN` elaboration | 16.72969 | 31.98947 | 47.703% |

Baseline seven gates and every selected/full arm passed; all four cases retained equal before/after source hashes across the paired executions. The `E1` resolver selected no validation gate because the documentation edit invalidated no registered evidence; its 0.018 s is planning/hash overhead, not a checker run. E4 did **not** reach the plan's predicted 80% saving. It is a comment-only RTL mutation and the test compares local `DenseFFN` elaboration with full top elaboration; this does not establish that any arbitrary internal RTL logic change is safe with local-only validation. The timing result is for the explicit experimental dependency registry and these four mutations, not an end-to-end production acceleration guarantee.

## Implementation and validation changes

- Added `build_stage5_sv_manifest()` and `validate_stage5_sv_manifest()` in `accagent/framework/dse_materialization.py`. The checker detects file membership/hash changes, parameter signature mismatch, Scala binding drift, and generated flat ANSI port fingerprint changes. It is not a full SV parser or semantic equivalence checker.
- `generate_code()` records a manifest only after successful Stage-5 compile/elaboration; the package static checker compares it against the independently recorded `generated_top.params` binding. The v5 benchmark's historical manifests remain explicitly retrospective.
- Added predeclared parameter-family rules and byte-change recall/preservation calculations. The rules missed changes as shown above; they remain a baseline for further graph work, not production propagation truth.
- Extended `build_static_failure_context()` to verify consumer source, graph artifact origin, source hash, tool-log hash, and that the same VCS report names the producer/instance/consumer. Valid evidence can narrow candidates; unresolved shared ownership stays unresolved.
- Added `validation4_evidence.py`, which runs native static checkers, records only observed results, and calls the real promotion method. Historical Stage-5 compile evidence is reused only after exact SV and Scala byte identity checks; it is marked `fresh_execution: false`.
- Added remote TraceBench v7 runners and an independent 59-check artifact consistency audit.

## Verification performed

- `tests/test_stage5_sv_manifest.py`: 6/6 passed.
- `tests/test_stage_artifacts.py`: 13/13 passed.
- `tests/test_sacg_cctg_causal_slice.py`: 15/15 passed, including new valid/forged consumer-context cases.
- `audit_validation4_results.py`: **59/59 consistency checks passed** over candidate manifests, partial reverts, promotion evidence-log hashes, remote source bindings, paired timing gates, and shared-source hashes.
- VCS remote executions are compile/elaboration-only; each per-case result and raw log is stored under the experiment output directories.

## Conclusions supported by this run

This run supports the narrower claims that a generation-time SV manifest can detect a later mixed-version file tree; declared parameter-family rules can predict some, but not all, changed generated files; actual compiler consumer diagnostics can support bounded graph candidate refinement; native static evidence can satisfy the isolated SACG transition's required checks; and targeted compile/elaboration work can save time on the tested mutation classes.

It does not support a universal 100% parameter propagation rate, a 10/10 unique graph root-cause localization rate, autonomous LLM repair, runtime CCTG diagnosis, numerical correctness, exact-board simulation, arbitrary-RTL targeted validation safety, a fresh warning-as-error VCS policy run, or production repair-executor promotion integration. These limits should remain visible in any paper table or text.
