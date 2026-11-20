#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../../.." && pwd)
result_root="$repo_root/results/resource_opt3_20261031/vcs"
reference_command="$repo_root/results/plan6/u280_plan2_attention_stream7_packedgamma_reuse_r32_context512_20261030/compile_command.txt"
vcs_home=/tmp/loopquant_vcs_compat_v202109
mkdir -p "$result_root"

read -r -a reference < "$reference_command"
sources=()
for token in "${reference[@]}"; do
    if [[ "$token" == hardware/rtwsr_qkv_head_buffer.sv ]]; then
        sources+=("$repo_root/$token" "$repo_root/hardware/rtwsr_qkv_head_buffer_banked.sv")
    elif [[ "$token" == hardware/*.sv ]]; then
        sources+=("$repo_root/$token")
    fi
done

run_case() {
    local name=$1 context=$2 recurrences=$3 trits128=$4 fast=$5
    local run_root="$result_root/$name"
    local build_dir="$run_root/build_vcsfix7"
    mkdir -p "$build_dir"
    if [[ -s "$run_root/full_run.log" && -s "$run_root/inputs.sha256" ]] \
        && grep -q '^U280_CYCLE_E2E_TEST_PASS' "$run_root/full_run.log" \
        && (cd "$repo_root" && sha256sum -c "$run_root/inputs.sha256" >/dev/null 2>&1); then
        printf 'RESOURCE_OPT3_REUSE_VALID_CASE %s\n' "$name"
        return 0
    fi
    sha256sum "${sources[@]}" > "$run_root/inputs.sha256"

    local command=(
        "$vcs_home/bin/vcs" -full64 -sverilog +v2k -O3
        +notimingcheck +nospecify -Mupdate -CFLAGS "-O3 -march=native"
        -top rtwsr_u280_hbm_cycle_e2e_tb -o "$build_dir/simv"
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CONTEXT_TOKENS="$context"
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.RECURRENCES="$recurrences"
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CORE_LINEAR_CHANNELS=96
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.HBM_POOL_LANES=24
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.HBM_RING_RECORDS=73728
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CORE_TIMING_CANDIDATE=1
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.CORE_128TRIT_CANDIDATE="$trits128"
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.POOL_READ_PARALLEL_SLOTS=0
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.GAMMA_PARALLEL_LOAD=1
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ATTENTION_PARALLEL_CANDIDATE=1
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ADAPTER_STATIC_REUSE=1
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.RESIDUAL_NORM_FUSION=1
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.RESIDUAL_NORM_TILE_PRELOAD=0
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.NORM_GAMMA_FROM_HOST=1
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ATTENTION_PARALLEL_HEADS=2
        -pvalue+rtwsr_u280_hbm_cycle_e2e_tb.ATTENTION_QUANT_STREAM_PIPELINE=1
    )
    if (( fast )); then
        command+=(+define+SIM_SCHEDULING_FAST_DATAPATH)
    fi
    command+=("${sources[@]}")

    printf '%q ' "${command[@]}" > "$run_root/compile_command.txt"
    printf '\n' >> "$run_root/compile_command.txt"
    (cd "$build_dir" && "${command[@]}") > "$run_root/compile.log" 2>&1
    sha256sum -c "$run_root/inputs.sha256" > "$run_root/input_check.log"
    "$build_dir/simv" > "$run_root/full_run.log" 2>&1
    grep -q '^U280_CYCLE_E2E_TEST_PASS' "$run_root/full_run.log"
}

compare_r2_cycles() {
    local reference_log="$result_root/b_context512_r2_reference/full_run.log"
    local fast_log="$result_root/b_context512_r2_fast/full_run.log"
    local reference_cycles fast_cycles
    reference_cycles=$(grep '^U280_CYCLE_E2E_RESULT ' "$reference_log" | sed -n 's/.*shell_cycles=\([0-9][0-9]*\).*/\1/p')
    fast_cycles=$(grep '^U280_CYCLE_E2E_RESULT ' "$fast_log" | sed -n 's/.*shell_cycles=\([0-9][0-9]*\).*/\1/p')
    if [[ -z "$reference_cycles" || "$reference_cycles" != "$fast_cycles" ]]; then
        printf 'R2 shell-cycle mismatch: reference=%s fast=%s\n' "$reference_cycles" "$fast_cycles" >&2
        return 1
    fi
    diff -u \
        <(grep '^U280_CYCLE_E2E_BREAKDOWN ' "$reference_log") \
        <(grep '^U280_CYCLE_E2E_BREAKDOWN ' "$fast_log")
}

export VCS_HOME="$vcs_home"
export PATH="$vcs_home/bin:$PATH"

if [[ -n "${RESOURCE_OPT3_CASE:-}" ]]; then
    compare_r2_cycles
    case "$RESOURCE_OPT3_CASE" in
        a_context512_r32) run_case a_context512_r32 512 32 0 1 ;;
        b_context512_r32) run_case b_context512_r32 512 32 1 1 ;;
        a_context2048_r32) run_case a_context2048_r32 2048 32 0 1 ;;
        b_context2048_r32) run_case b_context2048_r32 2048 32 1 1 ;;
        *) printf 'Unknown RESOURCE_OPT3_CASE: %s\n' "$RESOURCE_OPT3_CASE" >&2; exit 2 ;;
    esac
else
    run_case b_context512_r2_reference 512 2 1 0
    run_case b_context512_r2_fast 512 2 1 1
    compare_r2_cycles

    run_case a_context512_r32 512 32 0 1
    run_case b_context512_r32 512 32 1 1
    run_case a_context2048_r32 2048 32 0 1
    run_case b_context2048_r32 2048 32 1 1
fi

echo RESOURCE_OPT3_VCS_ALL_CASES_COMPLETE
