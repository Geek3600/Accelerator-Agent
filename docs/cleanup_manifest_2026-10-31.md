# Cleanup Manifest - 2026-10-31

This manifest records a conservative cleanup of generated build products. It is not permission to remove experiment evidence, source code, model data, or toolchain installations.

## Inventory Before Cleanup

- Local repository size: approximately 138 GiB.
- Local `obj_dir/`: 34,463 Verilator-generated C++/object/archive files, 30,372,534,882 bytes. The directory is git-ignored and contains generated build products, not source RTL or test results.
- Local Python bytecode: 860 `__pycache__` directories and 6,029 `.pyc` files, approximately 184,909,824 bytes. These are reproducible from their Python sources.
- Local run-local `.sbt_codegen_cache/`: 74 directories, approximately 13.43 GiB. **Retained** because they contain the run-local SBT boot and Coursier dependency caches, and run records refer to these paths.
- Remote home filesystem: 3.9 TiB total, approximately 99% used with 63 GiB free at inspection.
- Remote `board_vcs/`: approximately 34 GiB. It contains 331 staged compile attempts; each has a `stage.tar.gz`, a separate source tree, a compile report/log and compile status artifacts. The staged archives contain the complete `stage/sources/` tree. The per-attempt `vcs_work/` and `vcs_lib/` are generated VCS compile products.
- Remote `board_vcs/` VCS build products: `vcs_work/` approximately 14 GiB; `vcs_lib/` approximately 8.7 GiB. Retain each attempt's source tree and archive, `.spatialacc_*` metadata, `reports/`, logs, and exit markers.
- Remote `vivado_app_shell_runtime/`: approximately 10 GiB. It contained 99 run-local `.Xil/` temporary directories totaling approximately 7.3 GiB. No `hyyuan` VCS/Vivado process was identified as using this repository artifact tree. Other-user Vivado processes had inaccessible working-directory links and were not acted on.
- Remote `semantic_vcs/` VCS libraries (approximately 7 GiB) are **retained** because the corresponding remote tree has no staged source archives to prove an exact local reconstruction path.
- Remote shared toolchain and compiled simulation library trees, including `toolchains/` and `vivado_vcs_simlib_probe_202109_2021_1/`, are **retained**.

## Preserved Experiment Evidence

No files are removed from source, run result, report, or experiment directories. In particular, retain:

- `docs/context_2026-03-27.md` and the experiment plans/results under `accagent/experiments/`.
- `accagent/experiments/gpt2_medium_seq32_20261027/core_method_validation_20261031/`, including TraceBench v5, PropBench v3, and Paired Timing v3.
- Current model runs, compiler baselines, generated RTL, source bundles, timing histories, QoR reports, VCS logs, and remote source archives.
- The remote `board_vcs/**/sources/`, `board_vcs/**/stage.tar.gz`, `board_vcs/**/reports/`, status markers, `semantic_vcs/`, all shared simulator libraries, and all toolchain directories.
- Root `old/`, `backups/`, waveform, Vivado, verification, model-weight, and log directories. Their age alone does not establish that they are useless.

## Actions

| Target | Basis | Pre-clean size | Result |
|---|---|---:|---|
| Local `obj_dir/` | Git-ignored generated Verilator build output; no active local Verilator/VCS process | 30,372,534,882 bytes | Removed; about 28 GiB reclaimed |
| Local `__pycache__/` and `*.pyc` | Regenerable Python interpreter bytecode; Python sources retained | approximately 184,909,824 bytes | Removed; 0 bytecode files remain |
| Remote `spatialaccagent_artifacts/board_vcs/**/vcs_work/` and `vcs_lib/` | Completed compile products; source archives, source trees, reports/logs and status records retained | approximately 22.7 GiB | Removed; 0 VCS work/library directories remain |
| Remote `spatialaccagent_artifacts/vivado_app_shell_runtime/**/.Xil/` | Run-local Vivado temporary database/cache; final reports, bitstreams, logs and source closures retained | approximately 7.3 GiB | Removed; 0 run-local `.Xil/` directories remain |

## Exclusions

- Do not delete or reset modified/untracked source files or experiment outputs.
- Do not delete run-local `.sbt_codegen_cache/`; its dependency caches can make subsequent code generation work offline.
- Do not delete remote `semantic_vcs/**/vcs_lib/`, because its remote stage lacks an exact source archive.
- Do not touch `/home/hyyuan/.Xil`, user-wide simulator caches, or the unrelated active `flightloop_plan2_core_ooc_192ch_8head_20261029` Vivado task.
- Do not stop any process outside this repository/artifact tree.

## Post-Cleanup Verification

- Local `obj_dir/` is absent; `__pycache__/` count is 0 and `*.pyc` count is 0. The 74 run-local `.sbt_codegen_cache/` directories remain.
- The context document and TraceBench v5, PropBench v3, and Paired Timing v3 result files all passed non-empty checks.
- Remote `/home` free space increased from approximately 63 GiB to 93 GiB. `board_vcs/` retains all 331 `stage.tar.gz` archives and 331 `reports/vcs_compile.log` files. It retains the pre-existing 330 compile exit markers; one attempt had no exit marker before cleanup and still has its source/log artifacts.
- Remote `board_vcs/` has no remaining `vcs_work/` or `vcs_lib/` directories. `semantic_vcs/` remains approximately 35 GiB and was not modified. The run-local Vivado `.Xil/` count under `vivado_app_shell_runtime/` is 0; the directory still contains approximately 2.8 GiB of results, reports, logs, and other preserved outputs.
- The remote toolchain (approximately 8.6 MiB), shared simulation-library probe (approximately 814 MiB), and all three latest remote mechanism experiment directories remain present.
- No source files, experiment result files, timing histories, QoR reports, tool reports, generated RTL, backups, or model data were removed. No test was run because source code was not modified.
- Long-running remote Vivado processes outside the verified cleanup targets were left running, including processes owned by another user and the separate `flightloop_plan2_core_ooc_192ch_8head_20261029` job. Their status is outside this cleanup's scope.
