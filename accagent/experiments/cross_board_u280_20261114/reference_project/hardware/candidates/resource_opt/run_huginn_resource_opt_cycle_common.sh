#!/usr/bin/env bash
set -euo pipefail
cd /home/remote/workspace/LoopQuant

result_dir="results/resource_opt_20261030/candidate_${candidate}_context${context_tokens}"
reference_command="results/plan6/u280_plan2_attention_stream7_packedgamma_reuse_r32_context${context_tokens}_20261030/compile_command.txt"
core_rtl_dir=hardware/candidates/resource_opt/rtl_integrated
attention_source=hardware/candidates/resource_opt/rtwsr_attention_gemv_unit_dsp_shared.sv
build_dir="/tmp/loopquant_resource_opt_20261030_candidate_${candidate}_context${context_tokens}/obj_dir"
read -r -a reference < "$reference_command"
mkdir -p "$result_dir" "$build_dir"

command=()
sources=()
replace_mdir=0
replace_jobs=0
found_attention=0
found_qkv=0
found_context=0
found_channels=0
found_ring=0
found_pool_lanes=0
found_trits=0
found_slots=0
found_heads=0
found_tile_preload=0
for token in "${reference[@]}"; do
    if (( replace_mdir )); then
        command+=("$build_dir")
        replace_mdir=0
    elif (( replace_jobs )); then
        command+=(1)
        replace_jobs=0
    elif [[ "$token" == --Mdir ]]; then
        command+=("$token")
        replace_mdir=1
    elif [[ "$token" == --build-jobs ]]; then
        command+=("$token")
        replace_jobs=1
    elif [[ "$token" == -GCONTEXT_TOKENS=* ]]; then
        command+=("-GCONTEXT_TOKENS=$context_tokens")
        found_context=1
    elif [[ "$token" == -GCORE_LINEAR_CHANNELS=* ]]; then
        command+=(-GCORE_LINEAR_CHANNELS=96)
        found_channels=1
    elif [[ "$token" == -GHBM_RING_RECORDS=* ]]; then
        command+=(-GHBM_RING_RECORDS=73728)
        found_ring=1
    elif [[ "$token" == -GHBM_POOL_LANES=* ]]; then
        command+=(-GHBM_POOL_LANES=24)
        found_pool_lanes=1
    elif [[ "$token" == -GCORE_128TRIT_CANDIDATE=* ]]; then
        command+=("-GCORE_128TRIT_CANDIDATE=$trits128")
        found_trits=1
    elif [[ "$token" == -GPOOL_READ_PARALLEL_SLOTS=* ]]; then
        command+=(-GPOOL_READ_PARALLEL_SLOTS=0)
        found_slots=1
    elif [[ "$token" == -GATTENTION_PARALLEL_HEADS=* ]]; then
        command+=(-GATTENTION_PARALLEL_HEADS=2)
        found_heads=1
    elif [[ "$token" == -GRESIDUAL_NORM_TILE_PRELOAD=* ]]; then
        command+=("-GRESIDUAL_NORM_TILE_PRELOAD=$tile_preload")
        found_tile_preload=1
    elif [[ "$token" == hardware/rtwsr_attention_gemv_unit.sv ]]; then
        command+=("$attention_source")
        sources+=("$attention_source")
        found_attention=1
    elif [[ "$token" == hardware/rtwsr_qkv_head_buffer.sv ]]; then
        command+=("$core_rtl_dir/rtwsr_qkv_head_buffer.sv"
                  "$core_rtl_dir/rtwsr_qkv_head_buffer_banked.sv")
        sources+=("$core_rtl_dir/rtwsr_qkv_head_buffer.sv"
                  "$core_rtl_dir/rtwsr_qkv_head_buffer_banked.sv")
        found_qkv=1
    elif [[ "$token" == hardware/*.sv && -f "$core_rtl_dir/${token##*/}" ]]; then
        command+=("$core_rtl_dir/${token##*/}")
        sources+=("$core_rtl_dir/${token##*/}")
    else
        command+=("$token")
        if [[ "$token" == *.sv ]]; then
            sources+=("$token")
        fi
    fi
done
if (( ! found_attention || ! found_qkv || ! found_context || ! found_channels ||
      ! found_ring || ! found_pool_lanes || ! found_trits || ! found_slots || ! found_heads ||
      ! found_tile_preload )); then
    printf 'A required Candidate A/B configuration was not selected\n' >&2
    exit 1
fi

sha256sum "${sources[@]}" > "$result_dir/inputs.sha256"
printf '%q ' "${command[@]}" > "$result_dir/compile_command.txt"
printf '\n' >> "$result_dir/compile_command.txt"
"${command[@]}" > "$result_dir/compile.log" 2>&1
sha256sum -c "$result_dir/inputs.sha256" > "$result_dir/input_check.log"
stdbuf -oL -eL "$build_dir/Vrtwsr_u280_hbm_cycle_e2e_tb" > "$result_dir/full_run.log" 2>&1
rg -q '^U280_CYCLE_E2E_TEST_PASS' "$result_dir/full_run.log"
