#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

REMOTE_USER="${REMOTE_USER:-hyyuan}"
REMOTE_HOST="${REMOTE_HOST:-10.12.133.79}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/home/hyyuan/workspace/OptAcc}"
REMOTE_MAKE_JOBS="${REMOTE_MAKE_JOBS:-16}"
REMOTE_CONDA_ENV="${REMOTE_CONDA_ENV:-chisel_env}"
REMOTE_VCS_HOME="${REMOTE_VCS_HOME:-/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109}"
REMOTE_KNOWN_HOSTS="${REMOTE_KNOWN_HOSTS:-/tmp/codex_ssh_known_hosts}"

REMOTE_TARGET="${REMOTE_USER}@${REMOTE_HOST}"
SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}"
  -p "${REMOTE_PORT}"
)
REMOTE_LOCK_DIR="${REMOTE_LOCK_DIR:-/tmp/qwen2_remote_vcs}"

usage() {
  cat <<'EOF'
Usage:
  remote_vcs.sh sync
  remote_vcs.sh exec <remote command...>
  remote_vcs.sh validate-9p-fullseq-vcs [args...]
  remote_vcs.sh validate-axi-board-fullseq-vcs [args...]
  remote_vcs.sh validate-cnn-core-fullseq-vcs [args...]
  remote_vcs.sh validate-opt-acc-core-fullseq-vcs [args...]
  remote_vcs.sh monitor-9p-fullseq-vcs [interval_seconds]
EOF
}

remote_bash() {
  local cmd="$1"
  local remote_cmd
  remote_cmd="mkdir -p \"${REMOTE_WORKDIR}\" \"${REMOTE_LOCK_DIR}\" && cd \"${REMOTE_WORKDIR}\" && source ~/.bashrc && conda activate \"${REMOTE_CONDA_ENV}\" && CONDA_ENV_PREFIX=\"\$CONDA_PREFIX\" && unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS && export PATH=\"${REMOTE_VCS_HOME}/bin:/usr/bin:/bin:\$PATH\" VCS_HOME=\"${REMOTE_VCS_HOME}\" PYTHON_BIN=\"\$CONDA_ENV_PREFIX/bin/python3\" CC=/usr/bin/gcc CXX=/usr/bin/g++ CPP=/usr/bin/cpp LINK=/usr/bin/g++ AR=/usr/bin/ar LD=/usr/bin/ld NM=/usr/bin/nm RANLIB=/usr/bin/ranlib STRIP=/usr/bin/strip LANG=C LC_ALL=C && ${cmd}"
  local quoted_remote_cmd
  printf -v quoted_remote_cmd '%q' "${remote_cmd}"
  ssh "${SSH_OPTS[@]}" "${REMOTE_TARGET}" "bash -lc ${quoted_remote_cmd}"
}

sync_project() {
  remote_bash "mkdir -p generated verification verification/rtl verification/assert verification/assume verification/cover testbench/vcs scripts/verification verification/cases deliverables deliverables/vivado_opt_acc_core_ip deliverables/vivado_opt_acc_core_ip/hdl deliverables/vivado_cnn_core_ip deliverables/vivado_cnn_core_ip/hdl"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/generated/Top.sv" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/generated/Top.sv"

  if [[ -f "${REPO_ROOT}/generated/Top_vivado.sv" ]]; then
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/generated/Top_vivado.sv" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/generated/Top_vivado.sv"
  fi

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/assert/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/assert/"

  if [[ -f "${REPO_ROOT}/verification/layers-Top-Verification.sv" ]]; then
    rsync -az \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/verification/layers-Top-Verification.sv" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/layers-Top-Verification.sv"
  fi

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/assume/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/assume/"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/cover/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cover/"

  if [[ -d "${REPO_ROOT}/verification/board_sample_ip" ]]; then
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/verification/board_sample_ip/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/board_sample_ip/"
  fi

  if [[ -d "${REPO_ROOT}/verification/board_ddr_ip" ]]; then
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/verification/board_ddr_ip/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/board_ddr_ip/"
  fi

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/rtl/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/rtl/"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/testbench/vcs/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/testbench/vcs/"

  if [[ -d "${REPO_ROOT}/deliverables/vivado_opt_acc_core_ip/hdl" ]]; then
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/deliverables/vivado_opt_acc_core_ip/hdl/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/deliverables/vivado_opt_acc_core_ip/hdl/"
  fi

  if [[ -d "${REPO_ROOT}/deliverables/vivado_cnn_core_ip/hdl" ]]; then
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/deliverables/vivado_cnn_core_ip/hdl/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/deliverables/vivado_cnn_core_ip/hdl/"
  fi

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/scripts/verification/opt125m_e2e.py" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/scripts/verification/opt125m_e2e.py"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/scripts/verification/run_vcs_server.sh" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/scripts/verification/run_vcs_server.sh"

  if [[ -d "${REPO_ROOT}/scripts/synthesis" ]]; then
    remote_bash "mkdir -p scripts/synthesis"
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/scripts/synthesis/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/scripts/synthesis/"
  fi

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/cases/opt125m_stage_full/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cases/opt125m_stage_full/"

  local fullseq_dir
  for fullseq_dir in "${REPO_ROOT}"/verification/cases/opt125m_9p_fullseq* \
                     "${REPO_ROOT}"/verification/cases/pyjm12_alllayers_9p_fullseq \
                     "${REPO_ROOT}"/verification/cases/pyjm_9p_fullseq; do
    [[ -d "${fullseq_dir}" ]] || continue
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${fullseq_dir}/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cases/$(basename "${fullseq_dir}")/"
  done

  if [[ -d "${REPO_ROOT}/verification/cases/pyjm_stage_full" ]]; then
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/verification/cases/pyjm_stage_full/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cases/pyjm_stage_full/"
  fi
}

validate_remote() {
  local mode="$1"
  shift
  local args=("$@")
  sync_project
  local lock_file="${REMOTE_LOCK_DIR}/${mode}.lock"
  local inner_cmd="export VCS_BUILD_JOBS=${REMOTE_MAKE_JOBS}; \"\$PYTHON_BIN\" scripts/verification/opt125m_e2e.py ${mode}"
  local arg
  for arg in "${args[@]}"; do
    printf -v inner_cmd '%s %q' "${inner_cmd}" "${arg}"
  done
  local cmd="flock -n ${lock_file@Q} bash -lc ${inner_cmd@Q}"
  remote_bash "${cmd}"
}

monitor_fullseq_vcs() {
  local interval="${1:-20}"
  local run_dir="obj_dir/fullseq_vcs_validation/fullseq"
  local run_log="${run_dir}/run.log"
  local simv_pattern="${run_dir}/simv"
  local last_lines=0
  local seen_runtime=0
  local now

  while true; do
    now="$(date '+%F %T')"
    echo "=== ${now} monitor-9p-fullseq-vcs ==="

    remote_bash "
      if [[ -f ${run_log@Q} ]]; then
        current_lines=\$(wc -l < ${run_log@Q})
      else
        current_lines=0
      fi
      ps -eo pid=,pcpu=,etime=,args= | grep ${simv_pattern@Q} | grep -v grep || true
      printf '__RUN_LOG_LINES__ %s\n' \"\$current_lines\"
      if [[ -f ${run_log@Q} ]]; then
        grep -E 'cfg loaded|token-done|SystemTop progress|LN2 state|LN2 stat|LN2 X|ResAdd1 out|compare|mismatch|ERROR|FATAL' ${run_log@Q} | \
          awk '
            /cfg loaded/ { cfg = \$0 }
            /token-done/ { token_done = \$0 }
            /SystemTop progress/ { progress = \$0 }
            /ResAdd1 out/ { resadd = \$0 }
            /LN2 stat/ { ln2_stat = \$0 }
            /LN2 state/ { ln2_state = \$0 }
            /LN2 X/ { ln2_x = \$0 }
            /compare|mismatch|ERROR|FATAL/ { alerts[++alert_count] = \$0 }
            END {
              if (length(cfg)) print cfg
              if (length(token_done)) print token_done
              if (length(progress)) print progress
              if (length(resadd)) print resadd
              if (length(ln2_stat)) print ln2_stat
              if (length(ln2_state)) print ln2_state
              if (length(ln2_x)) print ln2_x
              for (i = 1; i <= alert_count; ++i) print alerts[i]
            }
          ' || true
      else
        echo 'run.log not found'
      fi
    " | awk -v last_lines="${last_lines}" '
      /^__RUN_LOG_LINES__ / {
        current_lines = $2 + 0;
        if (current_lines != last_lines) {
          printf("run.log lines: %d -> %d\n", last_lines, current_lines);
        } else {
          printf("run.log lines: %d (unchanged)\n", current_lines);
        }
        next;
      }
      { print }
    '

    if remote_bash "
      ps -eo args= | grep ${simv_pattern@Q} | grep -v grep >/dev/null
    "; then
      seen_runtime=1
      :
    else
      if ((seen_runtime)); then
        echo "simv not running, stop monitor"
        break
      fi
      echo "simv not running yet, keep waiting"
    fi

    last_lines="$(remote_bash "
      if [[ -f ${run_log@Q} ]]; then
        wc -l < ${run_log@Q}
      else
        echo 0
      fi
    " | tr -d '[:space:]')"
    sleep "${interval}"
  done
}

main() {
  if (($# == 0)); then
    usage
    exit 1
  fi

  local cmd="$1"
  shift
  case "${cmd}" in
    sync)
      sync_project
      ;;
    exec)
      if (($# == 0)); then
        usage
        exit 1
      fi
      local cmdline=""
      local arg
      for arg in "$@"; do
        printf -v cmdline '%s %q' "${cmdline}" "${arg}"
      done
      remote_bash "${cmdline# }"
      ;;
    validate-9p-fullseq-vcs)
      validate_remote "validate-9p-fullseq-vcs" "$@"
      ;;
    validate-axi-board-fullseq-vcs)
      validate_remote "validate-axi-board-fullseq-vcs" "$@"
      ;;
    validate-cnn-core-fullseq-vcs)
      validate_remote "validate-cnn-core-fullseq-vcs" "$@"
      ;;
    validate-opt-acc-core-fullseq-vcs)
      validate_remote "validate-opt-acc-core-fullseq-vcs" "$@"
      ;;
    monitor-9p-fullseq-vcs)
      monitor_fullseq_vcs "$@"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
