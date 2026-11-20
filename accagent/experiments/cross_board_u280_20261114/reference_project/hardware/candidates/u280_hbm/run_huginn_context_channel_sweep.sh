#!/usr/bin/env bash
set -euo pipefail
cd /home/remote/workspace/LoopQuant

reference_command=results/plan6/u280_plan2_attention_stream7_packedgamma_reuse_r32_context2048_20261030/compile_command.txt
result_root=results/plan6/huginn_context_channel_sweep_20261030
contexts=(128 256 512 1024 2048 4096)
channels_list=(96 192)
mkdir -p "$result_root"
summary="$result_root/summary.tsv"
printf 'context\tmax_context\tlinear_channels\tresult\n' > "$summary"

for context in "${contexts[@]}"; do
    max_context=2048
    if (( context > max_context )); then
        max_context=$context
    fi

    for channels in "${channels_list[@]}"; do
        existing_result=
        if (( channels == 192 && context == 512 )); then
            existing_result=results/plan6/u280_plan2_attention_stream7_packedgamma_reuse_r32_context512_20261030/full_run.log
        elif (( channels == 192 && context == 2048 )); then
            existing_result=results/plan6/u280_plan2_attention_stream7_packedgamma_reuse_r32_context2048_20261030/full_run.log
        fi

        if [[ -n "$existing_result" ]]; then
            while ! rg -q '^U280_CYCLE_E2E_TEST_PASS' "$existing_result"; do
                sleep 20
            done
            result_line=$(rg '^U280_CYCLE_E2E_RESULT ' "$existing_result" | tail -n 1)
            printf '%s\t%s\t%s\t%s\n' "$context" "$max_context" "$channels" "$result_line" >> "$summary"
            continue
        fi

        result_dir="$result_root/context${context}_channels${channels}"
        build_dir="/tmp/loopquant_huginn_context${context}_channels${channels}_20261030/obj_dir"
        mkdir -p "$result_dir" "$build_dir"
        read -r -a reference < "$reference_command"
        command=()
        sources=()
        replace_mdir=0
        max_context_set=0

        for token in "${reference[@]}"; do
            if (( replace_mdir )); then
                command+=("$build_dir")
                replace_mdir=0
            elif [[ "$token" == --Mdir ]]; then
                command+=("$token")
                replace_mdir=1
            elif [[ "$token" == -GCONTEXT_TOKENS=* ]]; then
                command+=("-GCONTEXT_TOKENS=$context")
            elif [[ "$token" == -GCORE_LINEAR_CHANNELS=* ]]; then
                command+=("-GCORE_LINEAR_CHANNELS=$channels")
            elif [[ "$token" == -GMAX_CONTEXT=* ]]; then
                command+=("-GMAX_CONTEXT=$max_context")
                max_context_set=1
            else
                if [[ "$token" == *.sv ]] && (( ! max_context_set )); then
                    command+=("-GMAX_CONTEXT=$max_context")
                    max_context_set=1
                fi
                command+=("$token")
                if [[ "$token" == *.sv ]]; then
                    sources+=("$token")
                fi
            fi
        done

        if (( replace_mdir || ! max_context_set )) || (( ${#sources[@]} == 0 )); then
            printf 'invalid reference compile command for context=%s channels=%s\n' "$context" "$channels" >&2
            exit 1
        fi

        sha256sum "${sources[@]}" > "$result_dir/inputs.sha256"
        printf '%q ' "${command[@]}" > "$result_dir/compile_command.txt"
        printf '\n' >> "$result_dir/compile_command.txt"
        "${command[@]}" > "$result_dir/compile.log" 2>&1
        sha256sum -c "$result_dir/inputs.sha256" > "$result_dir/input_check.log"
        "$build_dir/Vrtwsr_u280_hbm_cycle_e2e_tb" > "$result_dir/full_run.log" 2>&1
        rg -q '^U280_CYCLE_E2E_TEST_PASS' "$result_dir/full_run.log"
        result_line=$(rg '^U280_CYCLE_E2E_RESULT ' "$result_dir/full_run.log" | tail -n 1)
        printf '%s\t%s\t%s\t%s\n' "$context" "$max_context" "$channels" "$result_line" >> "$summary"
    done
done
