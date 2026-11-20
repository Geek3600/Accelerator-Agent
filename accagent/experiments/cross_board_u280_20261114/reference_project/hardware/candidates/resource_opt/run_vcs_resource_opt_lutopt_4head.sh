#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
result_root="$repo_root/results/resource_opt_lut_20261031/candidate_4head_optimized/vcs/b_context2048_r32_4head"
reference_command="$repo_root/results/resource_opt_lut_20261031/baseline_4head/vcs/b_context2048_r32_4head_20261031/compile_command.txt"
vcs_home=/tmp/loopquant_vcs_compat_v202109
mkdir -p "$result_root/build"

read -r -a reference < "$reference_command"
sources=()
for token in "${reference[@]}"; do
    if [[ "$token" == */hardware/*.sv ]]; then
        relative=${token#*/hardware/}
        if [[ "$relative" == "usw512_channel_array.sv" ]]; then
            relative=candidates/resource_opt/rtl_integrated/usw512_channel_array.sv
        fi
        sources+=("$repo_root/hardware/$relative")
    fi
done

sha256sum "${sources[@]}" > "$result_root/inputs.sha256"
command=(
    "$vcs_home/bin/vcs" -full64 -sverilog +v2k -O3
    +notimingcheck +nospecify -Mupdate -CFLAGS "-O3 -march=native"
    -top rtwsr_u280_hbm_cycle_e2e_tb -o "$result_root/build/simv"
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CONTEXT_TOKENS=2048
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.RECURRENCES=32
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CORE_LINEAR_CHANNELS=96
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.HBM_POOL_LANES=24
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.HBM_RING_RECORDS=73728
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CORE_TIMING_CANDIDATE=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CORE_128TRIT_CANDIDATE=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.POOL_READ_PARALLEL_SLOTS=0
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.GAMMA_PARALLEL_LOAD=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ATTENTION_PARALLEL_CANDIDATE=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ADAPTER_STATIC_REUSE=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.RESIDUAL_NORM_FUSION=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.RESIDUAL_NORM_TILE_PRELOAD=0
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.NORM_GAMMA_FROM_HOST=1
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ATTENTION_PARALLEL_HEADS=4
    -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ATTENTION_QUANT_STREAM_PIPELINE=1
    +define+SIM_SCHEDULING_FAST_DATAPATH
    "${sources[@]}"
)

printf '%q ' "${command[@]}" > "$result_root/compile_command.txt"
printf '\n' >> "$result_root/compile_command.txt"
export VCS_HOME="$vcs_home"
export PATH="$vcs_home/bin:$PATH"
(cd "$result_root/build" && "${command[@]}") > "$result_root/compile.log" 2>&1
sha256sum -c "$result_root/inputs.sha256" > "$result_root/input_check.log"
"$result_root/build/simv" > "$result_root/full_run.log" 2>&1
grep -q '^U280_CYCLE_E2E_TEST_PASS' "$result_root/full_run.log"
grep '^U280_CYCLE_E2E_RESULT ' "$result_root/full_run.log"
