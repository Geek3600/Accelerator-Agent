#!/usr/bin/env bash
set -euo pipefail
cd /home/remote/workspace/LoopQuant

result_dir=results/plan6/u280_plan2_channel192_pool32_reuse_r32_context512_20261030
build_dir=/tmp/loopquant_plan2_channel192_pool32_reuse_r32_20261030/obj_dir
reference_command=results/plan6/u280_plan2_channel192_pool32_r2_context512_20261029/compile_command.txt
mkdir -p "$result_dir" "$build_dir"
read -r -a command < "$reference_command"
sources=()
for index in "${!command[@]}"; do
    case "${command[index]}" in
        -GRECURRENCES=2) command[index]=-GRECURRENCES=32 ;;
        /tmp/loopquant_plan2_channel192_pool32_r2_20261029/obj_dir) command[index]="$build_dir" ;;
        hardware/*.sv) sources+=("${command[index]}") ;;
    esac
done
command+=(--threads 4)
sha256sum "${sources[@]}" > "$result_dir/inputs.sha256"
printf '%q ' "${command[@]}" > "$result_dir/compile_command.txt"
printf '\n' >> "$result_dir/compile_command.txt"
"${command[@]}" > "$result_dir/compile.log" 2>&1
sha256sum -c "$result_dir/inputs.sha256" > "$result_dir/input_check.log"
"$build_dir/Vrtwsr_u280_hbm_cycle_e2e_tb" > "$result_dir/full_run.log" 2>&1
