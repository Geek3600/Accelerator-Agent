# Evaluation Table Data Audit (2026-11-07)

This document records the values that can be traced to preserved experiment artifacts for the proposed `e2e_main` table. It keeps model/workload scope and evidence classes explicit. Unless a row says otherwise, frequency is source-bound post-synthesis Vivado Fmax and throughput is a source-calibrated DSE estimate, not RTL-simulated or board-measured throughput.

## Direct fill values for the current draft table

The following is the conservative fill-in for the draft shown in the paper discussion. Values are rounded only for the paper table; the exact values and archive paths remain in the sections below. `N/A` means that no comparable artifact exists, rather than zero.

| Draft row | Target workload and scope | Precision | Array / lanes | Fmax MHz | LUT / FF K | DSP | BRAM36 / URAM | Throughput tok/s | tok/s/DSP |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| Allo | Published GPT-2, `[32:1]`, U280 | W4A8 (paper precision scope) | — | 250.00* | 508 / 652 | 1,780 | 384 / — | 8.40** | 0.005 |
| StreamTensor | Published GPT-2, `[32:32]`, U55C | W4A8 | — | 250.00* | N/A | N/A | N/A | 199.51 | N/A |
| ACCORD, GPT-6.1 | GPT-2 Medium, 24L, seq32, VU9P | W4A8/I32 | 16x32 / 16 | 155.45 | 634.9 / 197.3 | 4,232 | 180 / 208 | 332.30*** | 0.079 |
| ACCORD, Qwen2 | Qwen2-0.5B, 24L, seq16 | W4A8/I32 | 16x32 / 16 | 175.19 | 643.5 / 228.2 | 4,212 | 252 / 214 | 254.69*** | 0.061 |
| ACCORD, Gemma | Gemma 3 1B IT, 26L, seq16 | W4A8/I32 | 16x32 / 16 | 121.83 | 946.5 / 253.6 | 4,184 | 294 / 413 | 125.47*** | 0.030 |
| ACCORD, LLaMA-family | TinyLlama-1.1B, 22L, seq16 | W4A8/I32 | 16x16 / 16 | 175.35 | 524.4 / 179.3 | 4,012 | 215 / 150 | 78.45*** | 0.020 |
| Unrefined B0 | GPT-2 Medium, 24L, seq32, Claude archive | W4A8/I32 | 16x32 / 16 | 27.38 | 652.2 / 162.1 | 4,130 | 180 / 208 | 58.52*** | 0.014 |
| ACCORD, Claude Opus 5 | No completed optimized candidate | W4A8/I32 | 16x32 / 16 | N/A | N/A | N/A | N/A | N/A | N/A |
| ACCORD, DeepSeek-V4-Pro | GPT-2 Medium, 24L, seq32, VU9P | W4A8/I32 | 16x32 / 16 | 152.74 | 614.3 / 177.4 | 3,074 | 180 / 208 | 326.52*** | 0.106 |
| ACCORD, GPT-6.1 | GPT-2 Medium, 24L, seq32, VU9P | W4A8/I32 | 16x32 / 16 | 155.45 | 634.9 / 197.3 | 4,232 | 180 / 208 | 332.30*** | 0.079 |

`*` The published 250 MHz values for Allo (U280) and StreamTensor (U55C) are their reported operating frequencies, not VU9P post-synthesis Fmax. `**` Allo Figure 14 reports approximately 119 ms for the `[32:1]` point. Following the paper's input:output notation, this is one generated output token after a 32-token input; the table therefore uses `1 / 0.119 = 8.403 tok/s`, rounded to 8.40, and `8.403 / 1780 = 0.00472 tok/s/DSP`, rounded to 0.005. This is a graph-digitized estimate, not a raw tabulated value, and is not directly comparable to StreamTensor's `[32:32]` speed. `***` ACCORD throughput is a DSE/source-derived estimate from the same archive, not an RTL counter or board measurement. The Qwen2, Gemma and LLaMA-family rows are historical seq16 cross-workload records; new seq32 restarts are tracked separately and must not overwrite them.

## Evidence rules

- Use the same source archive for Fmax, resources, cycle estimate, and throughput within a row.
- Do not combine a best-clock result with a best-throughput result from another archive.
- `vcs_compile_only` is a compile/elaboration/link gate. It is not runtime simulation, numerical validation, place-and-route closure, bitstream generation, or board measurement.
- The 2026-10-27 GPT-2 Medium rows are batch 1, sequence length 32, 24 layers, hidden size 1024, 16 heads, MLP 4096, signed W4A8/I32, 512-bit refill, VU9P, array 16x32 and lanes 16.
- The 2026-10-18 Qwen2, Gemma3 and TinyLlama/LLaMA-family rows are separate model campaigns with sequence length 16. They are useful cross-workload records, but they are not GPT-2 Medium measurements.
- Resource notation in this audit is `LUT / FF` in raw counts; divide by 1000 for the table's K columns. BRAM is reported as `BRAM36 / BRAM18`; URAM is a separate count.
- Efficiency is computed from the same-row estimated throughput divided by the same-row DSP count. Values below are rounded to three decimals for table display; retain the raw artifact values in supplementary material.

## Directly supported GPT-2 Medium cross-backbone rows

All three runs use the same GPT-2 Medium seq32 task specification and the same selected physical binding (`16x32`, lanes `16`, W4A8/I32). Their cycle source is `dse_structural_cycle_estimate_v1`, with 14,969,236 estimated cycles for 32 processed tokens and 24 layers. The cycle estimate is not an RTL counter.

| Row | Run and QoR artifact | Fmax (MHz) | LUT / FF (K) | DSP | BRAM36 / URAM | Estimated throughput (tok/s) | tok/s/DSP | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Unrefined baseline B0 | `accagent/runs/gpt2_medium_seq32_claude_opus5_20261027/backend_board/measurements/7a0ff04e48380b8ee833815bd3476e8a09b0ae0ccf787bd5361154caced9b0ae/qor_metrics.json` | 27.376259 | 652.234 / 162.054 | 4130 | 180 / 208 | 58.522713 | 0.014 |
| ACCORD (Claude Opus 5) | No completed optimized Claude candidate beyond the preserved B0 archive. The current run's latest reusable QoR is not a new improved candidate. | — | — | — | — | — | — | Do not invent a result; Stage-7 remains blocked by repeated upstream 502 responses. |
| ACCORD (DeepSeek-V4-Pro) | `accagent/runs/gpt2_medium_seq32_deepseek_v4pro_20261027/backend_board/qor/qor_metrics.json` and its best archive | 152.741714 | 614.273 / 177.448 | 3074 | 180 / 208 | 326.518657 | 0.106 |
| ACCORD (GPT-6.1) | `accagent/runs/gpt2_medium_seq32_gpt61_20261027/backend_board/qor/qor_metrics.json` and its best archive | 155.448469 | 634.930 / 197.332 | 4232 | 180 / 208 | 332.304935 | 0.079 |

The Claude `qor_metrics.json` at the current source snapshot reports 26.056595 MHz, 651.531 K LUT, 160.172 K FF, 4241 DSP and 55.701643 estimated token/s, but its report marks the synthesis as restored/reused rather than a new synthesis for the active timing attempt. It must not be presented as an optimized Claude result. The preserved B0 archive is the valid historical baseline point.

## Cross-workload rows under the GPT-6.1 campaign label

The following values are real preserved source-bound records, but they use separate target models and sequence length 16. Their exact physical arrays and selected bindings are included because the draft table currently hard-codes `16x32 / 16` for every row; that hard-coded value is wrong for the LLaMA-family run, which used `16x16 / 16`.

| Target workload | Run | Model scope | Array / lanes | Fmax (MHz) | LUT / FF (K) | DSP | BRAM36 / URAM | Estimated throughput (tok/s) | tok/s/DSP |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen2 | `accagent/runs/w4a8_20261018_qwen2` | Qwen2-0.5B, 24 layers, hidden 896, seq16 | 16x32 / 16 | 175.192711983 | 643.450 / 228.158 | 4212 | 252 / 214 | 254.690776773 | 0.061 |
| Gemma | `accagent/runs/gemma3_gpt61_20261020` | Gemma 3 1B IT, 26 layers, hidden 1152, seq16 | 16x32 / 16 | 121.832358674 | 946.493 / 253.571 | 4184 | 294 / 413 | 125.467125620 | 0.030 |
| LLaMA-family | `accagent/runs/w4a8_20261018_llama` | TinyLlama-1.1B-Chat-v0.1, 22 layers, hidden 2048, seq16 | 16x16 / 16 | 175.346308960 | 524.392 / 179.324 | 4012 | 215 / 150 | 78.451578406 | 0.020 |

For Gemma, the best-throughput archive is 121.832 MHz / 125.467 tok/s. A different Gemma archive reaches 155.957580 MHz but only 111.235262 estimated tok/s; do not combine that frequency with the best-throughput resources or cycles. The same distinction applies to any line where the best-clock and best-throughput candidates differ.

## Compiler baseline rows

### Allo

The reusable value is an external published reference, not a local reproduction and not a same-board result. The source is `accagent/experiments/compiler_baselines/gpt2_medium_baseline_reuse_20261028.md`, which cites Allo PLDI'24 Figure 14.

- Target: published 355M GPT-2, 24 layers, hidden 1024, W4A8; the paper's `[32:1]` point is used as the closest published workload point.
- Board and frequency: Alveo U280, 250 MHz.
- Published resources: LUT 508 K, FF 652 K, DSP 1,780, BRAM 384 (the paper reports BRAM percentage; no URAM value is given).
- End-to-end latency: approximately 119 ms read from the paper's vector graphic for `[32:1]`; this is a graph digitization, not a tabulated/raw latency value.
- Throughput: use the declared direct graph-read-off interpretation `[32:1] = one generated output token after a 32-token input`: `1 / 0.119 = 8.403 tok/s`, rounded to 8.40.
- Efficiency: `8.403 / 1780 = 0.00472 tok/s/DSP`, rounded to 0.005. Both values are approximate and graph-derived.
- Precision caveat: the paper does not explicitly establish the same I32 accumulator/bias and exact DDR/AXI boundary used by ACCORD.

Recommended table entry: use `U280 / 250 MHz` in a note or add a board column; put `508 / 652` K, `1,780`, `384 / —` in the resource columns; put `8.40` tok/s and `0.005` tok/s/DSP with a footnote recording the `1/0.119` graph-read-off formula. Do not label this as VU9P.

### StreamTensor

The StreamTensor paper reports a complete GPT-2 dataflow accelerator on an AMD U55C. Table 4 reports the `[32:32]` point as 194.99 ms end-to-end latency and 199.51 token/s; Table 6 reports 250 MHz and W4A8. The paper's Table 7 identifies GPT-2 as a 24-layer, hidden-1024, 16-head model, matching the architectural scale of GPT-2 Medium used by ACCORD. StreamTensor executes a fused transformer block on one FPGA and triggers it repeatedly with different weights, so its system boundary and schedule differ from ACCORD's full external-DDR multi-layer pipeline.

The paper does not report LUT, FF, DSP, BRAM, or URAM counts for the GPT-2 row. Those cells remain `N/A` rather than being inferred from on-chip-memory capacity or peak-performance figures. The reported 199.51 tok/s is an on-board measurement for `[32:32]`, while ACCORD's current values are source-calibrated estimates; the evidence classes remain separate.

Source: `docs/papers/Ye和Chen - 2025 - StreamTensor Make Tensors Stream in Dataflow Accelerators for LLMs.pdf`, Table 4 (latency/speed), Table 6 (platform/frequency/precision), Table 7 (GPT-2 model configuration), and Section 6.1 (execution boundary).

## Why the draft placeholders cannot all be filled with one number

1. The draft combines a new GPT-2 Medium seq32 campaign with older seq16 Qwen/Gemma/TinyLlama campaigns. They have different hidden sizes, layer counts, attention shapes, schedules and cycle counts.
2. The draft claims `16x32 / 16` for LLaMA, but the preserved LLaMA generated parameters are `computeArrayRows=16`, `computeArrayCols=16`, `lanes=16`.
3. The table uses a single Fmax and throughput per row, but each campaign can have separate best-clock and best-throughput source archives. Those archives must be kept paired.
4. All ACCORD throughput values in these artifacts are source-calibrated DSE estimates. They are not RTL simulation measurements or board measurements.
5. Allo's value is a published U280 external reference with a graph-digitized `[32:1]` latency converted to one-output-token throughput; StreamTensor is a published U55C `[32:32]` on-board result with no published resource breakdown. Neither supports a VU9P apples-to-apples QoR claim.
6. The current GLM-5.3 GPT-2 Medium seq32 run has not reached DSE or synthesis, so it supplies no table value yet.

## Source pointers

- GPT-2 Medium GPT-6.1: `accagent/runs/gpt2_medium_seq32_gpt61_20261027/backend_board/qor/qor_metrics.json`, `backend_board/best_qor.json`, `input/model_config.json`, `input/task_card.json`, `generated/chisel/src/main/scala/spatialaccagent/generated/GeneratedDesignParams.scala`.
- GPT-2 Medium DeepSeek: corresponding files under `accagent/runs/gpt2_medium_seq32_deepseek_v4pro_20261027/`.
- GPT-2 Medium Claude/B0: corresponding files under `accagent/runs/gpt2_medium_seq32_claude_opus5_20261027/`, especially the preserved best archive SHA above.
- Qwen2: `accagent/runs/w4a8_20261018_qwen2/backend_board/best_qor.json` and generated parameters.
- Gemma: `accagent/runs/gemma3_gpt61_20261020/backend_board/best_qor.json` and generated parameters.
- TinyLlama/LLaMA-family: `accagent/runs/w4a8_20261018_llama/backend_board/best_qor.json` and generated parameters.
- Compiler baselines: `accagent/experiments/compiler_baselines/gpt2_medium_baseline_reuse_20261028.md`, `gpt2_medium_status.md`, and `feasibility_report.md`.

