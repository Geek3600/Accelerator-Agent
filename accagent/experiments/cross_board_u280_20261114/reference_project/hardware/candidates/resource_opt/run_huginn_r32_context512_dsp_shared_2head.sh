#!/usr/bin/env bash
set -euo pipefail
cd /home/remote/workspace/LoopQuant

result_dir=results/resource_opt_20261030/huginn_r32_context512_dsp_shared_2head
reference_command=results/plan6/u280_plan2_attention_stream7_packedgamma_reuse_r32_context512_20261030/compile_command.txt
core_rtl_dir=hardware/candidates/resource_opt/rtl_integrated
attention_source=hardware/candidates/resource_opt/rtwsr_attention_gemv_unit_dsp_shared.sv
build_dir=/tmp/loopquant_resource_opt_20261030_huginn_r32_context512_dsp_shared_2head/obj_dir
read -r -a reference < "$reference_command"
mkdir -p "$result_dir" "$build_dir"

command=()
sources=()
replace_mdir=0
replace_jobs=0
found_attention=0
found_qkv=0
found_heads=0
for token in "${reference[@]}"; do
    if (( replace_mdir )); then
        command+=("$build_dir")
        replace_mdir=0
    elif (( replace_jobs )); then
        command+=(2)
        replace_jobs=0
    elif [[ "$token" == --Mdir ]]; then
        command+=("$token")
        replace_mdir=1
    elif [[ "$token" == --build-jobs ]]; then
        command+=("$token")
        replace_jobs=1
    elif [[ "$token" == -GATTENTION_PARALLEL_HEADS=8 ]]; then
        command+=(-GATTENTION_PARALLEL_HEADS=2)
        found_heads=1
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
if (( ! found_attention || ! found_qkv || ! found_heads )); then
    printf 'Required attention, QKV, or 2-head configuration was not selected\n' >&2
    exit 1
fi

sha256sum "${sources[@]}" > "$result_dir/inputs.sha256"
printf '%q ' "${command[@]}" > "$result_dir/compile_command.txt"
printf '\n' >> "$result_dir/compile_command.txt"
"${command[@]}" > "$result_dir/compile.log" 2>&1
sha256sum -c "$result_dir/inputs.sha256" > "$result_dir/input_check.log"
"$build_dir/Vrtwsr_u280_hbm_cycle_e2e_tb" > "$result_dir/full_run.log" 2>&1
rg -q '^U280_CYCLE_E2E_TEST_PASS' "$result_dir/full_run.log"
