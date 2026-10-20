# Upstream LLM Generalization Runs

All three experiments use fresh Stage 0--7 runs and the current shared W4A8, 512-bit DDR, OPT-aligned accelerator flow. Per-run outputs and credentials remain separate; API credentials are never written here.

| Run | Target | Upstream LLM | Provider route | Status |
|---|---|---|---|---|
| `gemma3_gpt61_20261020` | Gemma 3 1B IT | `gpt-6.1-sol` | A8PI Responses | Stage 1 constraint extraction active; Stage 0 passed |
| `gpt2_deepseek_v4pro_20261020` | GPT-2 | `deepseek-v4-pro` | DeepSeek Responses endpoint | Stage 3 passed; Stage 4 binding handoff active |
| `gpt2_claude_fable51_20261020` | GPT-2 | `claude-opus-5` (probe) | A8PI | Blocked: A8PI returned 502 |

The GPT-2 upstream-model runs share `accagent/campaigns/20261020_gpt2_upstream_compare/task_spec.md` and all target/board/numeric inputs. The Gemma run uses `accagent/campaigns/20261020_gemma_gpt61/task_spec.md` and the existing local Gemma 3 1B IT checkpoint/model configuration. Do not apply the historical existing-design timing-only scope to these fresh experiments.

## Claude Route Check

At 2026-10-20 20:02 CST, the current shell default was `https://api.toskaxy.xyz/v1`, so its inherited routing must not be used to diagnose Claude. The Claude run's preflight/report specify `https://www.a8pi.com/v1` and `https://www.a8pi.com/v1/responses`. Initial probes used mismatched auth/wire combinations and returned 401; those results did not establish that the token itself was invalid. Requests using the Claude Code `ANTHROPIC_AUTH_TOKEN` Bearer convention to A8PI `/v1/messages` returned HTTP 503 `No available accounts` and, on retry at 20:22 CST, HTTP 502 `Upstream access forbidden`. At 20:24 CST the authenticated `/v1/models` request returned 200 and listed `claude-opus-5`; a minimal `/v1/messages` request with that exact model ID returned HTTP 502 `Upstream access forbidden`. All requests stayed on A8PI and yielded no model response. Claude is currently unavailable through this route; do not interpret the earlier 403 as confirmed quota exhaustion or the initial 401s as proof of an invalid token. The Claude controller is not running. No API key is recorded here.

The Gemma and DeepSeek controllers were restarted as detached processes on 2026-10-20 20:08 CST after confirming the earlier controllers had exited. Their live process environments were checked: Gemma uses `https://www.a8pi.com/v1/responses` with `gpt-6.1-sol`; DeepSeek uses `https://api.deepseek.com/v1/responses` with `deepseek-v4-pro`. Both have empty fallback endpoint/key settings. Controller PIDs are 2088955 (Gemma) and 2088956 (DeepSeek). No API key is recorded here.

## Progress checkpoint: 2026-10-20 20:30 CST

- GPT-2/DeepSeek Stage 0 passed with `input/prepared_inputs.json` status `ready`; Stage 1 constraint extraction is running in the existing run. The `input_evidence_engineer` and `toolchain_boundary_engineer` requests completed without transport retries; no DSE/performance result exists yet.
- Gemma remains at Stage 0. `input/prepared_inputs.json` is `incomplete` because `build_case_adapter()` returns `status=missing` for `model_type=gemma3_text`; the registered built-in families currently cover GPT-2, LLaMA, and Qwen2. Three input-preparation retry records preserve the same missing-adapter error. The run's model config includes Gemma-specific MQA, QK normalization, sliding-window attention, gated MLP/GELU-tanh, and multiple RMSNorm stages. Reusing GPT-2/LLaMA/Qwen2 semantics would invalidate the target-model experiment. There is no source-backed Gemma semantic adapter in the repository, so the run cannot proceed to DSE until the framework/agent produces and validates one.
- Both original controllers remain alive with their configured endpoints and no fallback. Claude remains paused; its Opus 5 probe to A8PI `/v1/messages` returned 502 and no Claude run was launched.
- Preserve both run directories and their artifacts. Do not claim either run has DSE results or hardware performance yet.

## Progress checkpoint: 2026-10-20 20:48 CST

- Added the generic built-in `gemma3_text` case/semantic adapter at `accagent/framework/case_adapters/gemma3_text_transformer_block.json` and registered it in `case_adapter.py`. It binds the supplied Gemma 3 block order, MQA (4/1 heads), Q/K norm, global/local RoPE, three extra RMSNorm points, gated GELU-tanh MLP, real weight suffixes, and the existing `Gemma3TextBlock` loader ports. The adapter is sourced from the current model config, Chisel top-level, and the checkpoint tensor header; it does not reuse another model's semantic contract.
- Static checks passed: JSON parsing, Python compilation, adapter construction, and the existing built-in adapter test suite (`4` tests). The actual Gemma safetensors header contains `340` tensors, `338` decoder tensors matching `26` layers; every declared semantic weight suffix is present.
- The currently rerun Gemma Stage 0 has written `input/case_adapter.json` with `status=ready`; its `prepared_inputs.json` is still the previous incomplete snapshot while the active input-preparation process completes its audits. Do not promote it until the current process writes a fresh ready report.
- GPT-2/DeepSeek completed Stage 1 and Stage 2; Stage 3 pipeline planning is active. No DSE/performance result exists yet.

- At 20:50 CST, Gemma Stage 0 completed with `prepared_inputs.json` status `ready` and automatically entered Stage 1 constraint extraction. GPT-2/DeepSeek Stage 3 pipeline architect and data-transfer reviews completed; its memory-dataflow review is active. Neither run has started DSE or produced performance data.
- At 20:55 CST, GPT-2/DeepSeek Stage 3 completed with 11/11 checkers passed and no warnings; the controller is handing off to Stage 4 binding. Gemma Stage 1 specialist reviews are mostly complete; its verification-boundary request is retrying one transient 502. No DSE result exists yet.

## Progress checkpoint: 2026-10-20 21:01 CST

- GPT-2/DeepSeek passed Stage 4 parameter binding (6/6 static checks) and advanced to Stage 5 `code_generation` using legal candidate `arch_08fc81fe6157`. Chisel build/runtime/memory/simulation closure files are present and SBT/Chisel expansion is active. No rollback or restart occurred.
- DeepSeek DSE evidence is still structural only (`qor_estimate=insufficient_evidence`, Pareto `measurement_pending`); no Vivado resource/Fmax, RTL-cycle, or throughput result is reportable.
- Gemma/GPT-6.1-Sol remains in Stage 1 constraint extraction. Its verification-boundary LLM request is retrying transient A8PI 502/overload responses under the existing retry policy. Controllers 2088955/2088956 remain alive with their configured endpoints and empty fallback; Claude remains paused.

## Progress checkpoint: 2026-10-20 21:09 CST

- GPT-2/DeepSeek passed Stage 5 `code_generation`: compile, both generated-top elaborations, contract, and package gates passed. Stage 6 `verification_artifacts` is active; operator-leaf planning completed and single-layer planning is running. VCS and synthesis have not run yet; DSE remains `insufficient_evidence`.
- Gemma/GPT-6.1-Sol passed Stage 1. Its first Stage 2 parameter-binding check failed because a checker requires `hidden_size == num_q_heads * head_dim` (1152 != 4*256=1024). The controller started bounded reconciliation within Stage 2, without backtracking. Verify the model's actual query-projection/attention tensor shapes before deciding whether this generic checker assumption is valid; do not promote while the checker fails.
- Snapshot both current run states in Git, excluding dependency caches, compile targets, PID/lock files, and old-run deletions.

## Progress checkpoint: 2026-10-20 21:11 CST

- Initial source and run snapshot was pushed to GitHub `main` as commit `d341a46`; both original controllers remain active.
- Gemma's Stage 2 bounded retry completed its model-shape provenance review; the numeric/template specialist is now running. The current retry has not passed or advanced. The `hidden_size`/head-geometry mismatch remains unresolved pending authoritative tensor/semantic evidence.
- GPT-2/DeepSeek remains in Stage 6 verification-artifact planning; its single-layer-kernel planner request is active. Stage 5 compile/elaboration passed, while VCS/synthesis are still pending.
