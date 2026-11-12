# Validation6 Results (2026-11-02)

## Scope

This report records the two experiments specified by `core_method_validation_end3.md`: TraceBench v9 realistic-name LLM repair comparison and PropBench v7 transitive parent-closure ablation. Results below are derived from the preserved per-case records, logs, frozen predictions, and source-bound remote VCS artifacts in `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation6_20261102/`.

The plan's expected outcomes were treated as hypotheses. They were not used as labels, acceptance criteria, or prompts to force a preferred result. Validation5 and prior experiment directories remain unchanged.

## TraceBench v9: Setup

TraceBench v9 uses ten archived interface mismatch cases, each evaluated in two arms, for twenty arm-case rows. The producer-side mismatched port was replaced with a plausible RTL identifier without `fault`, `bug`, `error`, or `tracebench` markers. The B0 and ACCORD prompts share the same bounded consumer and producer excerpts, raw UPIMI-E diagnostic, case source, and LLM endpoint/model. B0 receives no graph context and has no artifact write authorization boundary. ACCORD receives static SACG/DCG failure context and can edit only the authorized producer file. Both arms use at most two schema-valid model responses for each case, with a finite transport retry policy. Credentials are not recorded.

The resolved model configuration was OpenAI `gpt-6.1-sol`, `responses` wire API, endpoint host `www.a8pi.com`. No fallback provider was used. The exact sanitized settings are in `tracebench_v9_realistic_ablation/llm_run_config_audit.json`.

For each arm-case, an independent remote VCS run was made on the injected source. The valid initial-failure criterion is `vlogan_returncode == 0`, `vcs_returncode != 0`, the expected `Error-[UPIMI-E]`, and matching local/remote source manifests. A repair's raw VCS pass is source-bound to the exact post-repair bundle and log. Contract-preserving repair additionally requires the pristine producer port fingerprint to be restored and edits to remain within the intended producer scope. ACCORD promotion is counted only when fresh VCS evidence, a fresh generated-source manifest check, the producer port fingerprint, and the native promotion operation all pass.

## TraceBench v9: Results

| Metric | B0 raw-log | ACCORD DCG-bounded |
|---|---:|---:|
| Cases / initial faults reproduced | 10/10 | 10/10 |
| Raw post-repair VCS pass | 8/10 (80%) | 8/10 (80%) |
| Contract-preserving repair | 2/10 (20%) | 8/10 (80%) |
| Consumer corruption or unbounded edit | 6/10 (60%) | 0/10 (0%) |
| Scope violations intercepted by gate | 0 | 0 |
| Native promotion pass | not attempted for B0 | 8/8 attempted (8/10 cases overall) |
| Effective schema-valid model responses | 12 | 15 |
| Transport attempts | 12 | 15 |

These data support a narrower conclusion than “ACCORD always fixes the design better”: both arms obtained eight raw compile/elaboration passes, but six B0 passing repairs changed consumer or otherwise out-of-scope files and only two passed the independent producer-interface contract check. ACCORD produced eight contract-preserving repairs and eight fresh native promotions, with no consumer edits. The 0/10 intercepted-scope-violation count means the experiment observed no proposal that the ACCORD authorization gate had to reject; therefore the result demonstrates bounded edits in these observed proposals, not an empirical interception rate. Promotion was not attempted in B0, so promotion counts are not a symmetric outcome comparison.

Per-case outcome (R = initial fault reproduced; V = raw repair VCS pass; C = contract-preserving repair; P = native promotion):

| Case | B0 R/V/C | ACCORD R/V/C/P | Note |
|---|---|---|---|
| F1 DenseFFN | 1/1/0 | 1/1/1/1 | B0 repaired the consumer and compiled. ACCORD's saved-response replay passed fresh VCS, producer fingerprint, manifest, and promotion after a resume-path incident; it used no additional LLM response. |
| F2 GeneratedAcceleratorTop | 1/0/0 | 1/0/0/0 | Both models used two valid responses, but exact search strings did not match the source; no patch was applied. |
| F3 Attention | 1/0/0 | 1/0/0/0 | Both models used two valid responses, but exact search strings did not match the source; no patch was applied. |
| F4 IntegerAttention | 1/1/0 | 1/1/1/1 | B0 compiled after a consumer edit; ACCORD restored the producer contract and promoted. |
| F5 Linear | 1/1/0 | 1/1/1/1 | B0 compiled after an out-of-scope edit; ACCORD passed contract and promotion. |
| F6 Activation | 1/1/0 | 1/1/1/1 | B0 compiled after a consumer edit; ACCORD passed contract and promotion. |
| F7 ResidualAdd | 1/1/1 | 1/1/1/1 | Both passed contract checks; ACCORD also promoted. |
| F8 PhysicalStreamFifo | 1/1/1 | 1/1/1/1 | Both passed contract checks; ACCORD also promoted. |
| F9 WeightTileCache | 1/1/0 | 1/1/1/1 | B0 compiled after a consumer edit; ACCORD passed contract and promotion. |
| F10 QKVProjection | 1/1/0 | 1/1/1/1 | B0 compiled after a consumer edit; ACCORD passed contract and promotion. |

The summary records `initial_fault_reproduced=true` for all twenty rows. A runner state-label bug left some rows with textual status `initial_fault_not_reproduced` despite the valid initial-fault evidence and two valid model responses; those rows are not initial-fault failures. They are repair failures due to unapplied exact-search proposals. The per-case boolean fields, response artifacts, and remote VCS records are the source of truth. The original status label is preserved as an execution defect rather than silently interpreted as experiment outcome.

## TraceBench v9: Execution Incidents and Evidence

An early runner version classified VCS-stage `UPIMI-E` as an initial fault failure because it tested the wrong return-code stage. Three early records were preserved as `initial_elaboration_runner_incident.json` / `preflight_runner_incident.json` and excluded from the final twenty-row analysis. The corrected criterion was applied in fresh remote runs; all ten cases reproduced the injected error in both arms.

During F1 ACCORD, a post-repair helper initially resolved the source run path incorrectly. A subsequent resume attempt reconstructed the realistic-alias source but failed to apply its saved patch before compiling; this wrong-source compile was retained as an incident and is not the final F1 outcome. The explicit `replay_f1_accord.py` recovery then started from the immutable v7 fixture, replayed the two already-budgeted schema-valid responses in order (the first proposal was refused by exact-file authorization, the second producer proposal applied), and ran fresh VCS in a separate remote directory. The replay passed source binding, producer port fingerprint, fresh SV manifest check, and native promotion. It made zero additional LLM calls; response, patch, source, manifest, and log hashes are in `saved_response_replay.json` and its evidence files. This is post-hoc deterministic recovery, not uninterrupted live execution, and is reported as such.

All rows respected the two effective-response limit. Each counted response was schema-valid. The recorded transport attempts equal effective response counts (no transient provider error occurred in the completed rows). B0 had no native promotion attempt by design; it was not given an artificial promotion failure score. ACCORD's eight passing promotions each have a fresh compile gate and manifest/fingerprint check artifact, including the separately labeled F1 deterministic saved-response replay. Remote source-binding checks were true for the eight raw-VCS passes in each arm.

## PropBench v7: Setup and Results

PropBench v7 statically re-scores ten archived parameter variants against one independent baseline RTL package. Prediction sets for L1, L2, and L3 were frozen before candidate-vs-baseline file SHA differences were loaded. The gold labels are byte-level changed-file sets, not semantic dependency or causal necessity labels. No Chisel/SBT, VCS, simulation, or synthesis was run.

| Level | Rule | Macro Recall | Micro Recall | Macro Preservation | Micro Preservation | Macro predicted fraction | FP unchanged | FN changed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| L1 | Flat family prior | 0.729 | 0.679 | 0.899 | 0.885 | 0.332 | 80 | 36 |
| L2 | Up to two syntactic child-to-parent hops | 0.817 | 0.777 | 0.922 | 0.886 | 0.534 | 164 | 25 |
| L3 | Full transitive syntactic parent closure | 0.853 | 0.821 | 0.935 | 0.903 | 0.562 | 172 | 20 |

Full parent closure raised macro/micro recall over L2 by 0.036/0.044 and reduced false negatives from 25 to 20, while increasing false positives from 164 to 172 and the predicted affected-file fraction from 0.534 to 0.562. Preservation is specificity among files predicted unaffected; because its denominator changes with prediction scope, the higher L3 preservation values must be read alongside the larger predicted set and absolute FP counts. The result demonstrates increased coverage of byte-changed files for the tested topology, with a broader impact set; it does not show semantic accuracy or hardware correctness.

The requested stage-memory coupling expansion was not added. The available SACG stage stream/buffer contracts are not joined to individual RTL memory instances with a traceable instance-level parameter-to-width relation. Adding memory edges would therefore have been speculative and would violate the frozen-rule/no-gold-tuning protocol. The audit is in `propbench_v7_closure_ablation/width_contract_audit.json`.

## Reproduction and Artifact Map

All Validation6 experiment artifacts are under `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation6_20261102/`.

TraceBench v9 includes the runner, sanitized model configuration, twenty per-arm/case directories, raw request and response JSON, fault injection maps, failure reports, static SACG context for ACCORD, authorization records, source patches, VCS logs, source/bundle manifests, fresh compile gates, port fingerprints, promotion reports, progress JSON, and aggregate metrics/summary. The corrected final audit summary (including the F1 saved-response recovery) is `tracebench_v9_realistic_ablation/llm_ablation_summary.json`; aggregate counts are `metrics.json`, and structural/source/protocol checks are in `integrity_audit.json`. The runner's original `summary.json` is retained as an execution artifact and predates F1 recovery; it is not the authoritative final summary.

PropBench v7 includes `run_propbench_v7.py`, frozen prediction sets, per-case JSON ledgers, `summary.json`, `width_contract_audit.json`, and `RESULT.md` under `propbench_v7_closure_ablation/`.

The exact command for the static PropBench reproduction is `python accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation6_20261102/propbench_v7_closure_ablation/run_propbench_v7.py`. TraceBench was run with `python -u accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation6_20261102/tracebench_v9_realistic_ablation/run_tracebench_v9.py`; the runner and per-row records are retained because it depends on the configured LLM environment and remote VCS access.

## Overall Assessment and Limits

Validation6 provides evidence for two bounded claims: (1) in this ten-case test set, DCG context plus producer-only authorization coincided with a higher contract-preserving repair count and no consumer edits, with raw VCS pass tied at 8/10 and no gate interception observed; and (2) full transitive RTL parent closure found more byte-changed files than a two-hop closure at the cost of a wider predicted set and more false positives. Neither experiment establishes broad generalization beyond these cases. TraceBench uses one resolved LLM/provider configuration and synthetic interface fault injections; PropBench uses file-level SHA gold labels and a limited static topology graph. There is no simulated workload or hardware performance measurement in Validation6.

Do not report the plan's predicted B0 failure/ACCORD victory as an observed result. Do not claim that ACCORD improves raw VCS pass, that the authorization gate empirically intercepted violations, or that PropBench establishes semantic propagation correctness. The strongest defensible TraceBench comparison is 8/10 vs 2/10 contract-preserving repair, with tied 8/10 raw VCS pass and 0/10 vs 6/10 observed consumer/out-of-scope edits, with F1 deterministic recovery and unequal promotion instrumentation disclosed.
