#!/usr/bin/env bash
set -euo pipefail
cd /home/remote/workspace/LoopQuant

result_dir=results/plan6/u280_plan2_attention_stream7_reuse_r32_context512_20261030
build_dir=/tmp/loopquant_plan2_attention_stream7_reuse_r32_20261030/obj_dir
reference_command=results/plan6/u280_plan2_fast_attention_reuse_r32_context512_20261030/compile_command.txt
mkdir -p "$result_dir" "$build_dir"
read -r -a reference < "$reference_command"
command=()
sources=()
replace_mdir=0
found_testbench=0
for token in "${reference[@]}"; do
    if (( replace_mdir )); then
        command+=("$build_dir")
        replace_mdir=0
    elif [[ "$token" == --Mdir ]]; then
        command+=("$token")
        replace_mdir=1
    elif [[ "$token" == -GATTENTION_QUANT_STREAM_PIPELINE=* ]]; then
        command+=(-GATTENTION_QUANT_STREAM_PIPELINE=1)
    elif [[ "$token" == -GATTENTION_PARALLEL_HEADS=* ]]; then
        command+=("$token" -GATTENTION_QUANT_STREAM_PIPELINE=1)
    elif [[ "$token" == hardware/candidates/u280_hbm/rtwsr_u280_hbm_cycle_e2e_tb.sv ]]; then
        command+=(hardware/candidates/u280_hbm/rtwsr_round_divider_stream7.sv "$token")
        sources+=(hardware/candidates/u280_hbm/rtwsr_round_divider_stream7.sv "$token")
        found_testbench=1
    else
        command+=("$token")
        if [[ "$token" == hardware/*.sv ]]; then
            sources+=("$token")
        fi
    fi
done
if (( ! found_testbench )); then
    printf 'testbench source not found in reference compile command\n' >&2
    exit 1
fi
sha256sum "${sources[@]}" > "$result_dir/inputs.sha256"
printf '%q ' "${command[@]}" > "$result_dir/compile_command.txt"
printf '\n' >> "$result_dir/compile_command.txt"
"${command[@]}" > "$result_dir/compile.log" 2>&1
sha256sum -c "$result_dir/inputs.sha256" > "$result_dir/input_check.log"
"$build_dir/Vrtwsr_u280_hbm_cycle_e2e_tb" > "$result_dir/full_run.log" 2>&1
