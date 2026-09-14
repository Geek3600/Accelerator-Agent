#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

REMOTE_USER="${REMOTE_USER:-hyyuan}"
REMOTE_HOST="${REMOTE_HOST:-10.12.133.79}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/home/hyyuan/workspace/OptAcc}"
REMOTE_MAKE_JOBS="${REMOTE_MAKE_JOBS:-32}"
REMOTE_CONDA_ENV="${REMOTE_CONDA_ENV:-chisel_env}"
REMOTE_KNOWN_HOSTS="${REMOTE_KNOWN_HOSTS:-/tmp/codex_ssh_known_hosts}"

REMOTE_TARGET="${REMOTE_USER}@${REMOTE_HOST}"
SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}"
  -p "${REMOTE_PORT}"
)
REMOTE_LOCK_DIR="${REMOTE_LOCK_DIR:-/tmp/qwen2_remote_verilator}"

usage() {
  cat <<'EOF'
Usage:
  remote_verilator.sh sync
  remote_verilator.sh exec <remote command...>
  remote_verilator.sh validate-top [args...]
  remote_verilator.sh validate-system-top [args...]
  remote_verilator.sh validate-9p-fullseq [args...]

Environment overrides:
  REMOTE_USER
  REMOTE_HOST
  REMOTE_PORT
  REMOTE_WORKDIR
  REMOTE_MAKE_JOBS
  REMOTE_CONDA_ENV
  REMOTE_KNOWN_HOSTS
EOF
}

remote_bash() {
  local cmd="$1"
  local remote_cmd
  remote_cmd="mkdir -p \"${REMOTE_WORKDIR}\" \"${REMOTE_LOCK_DIR}\" && cd \"${REMOTE_WORKDIR}\" && source ~/.bashrc && conda activate \"${REMOTE_CONDA_ENV}\" && CONDA_ENV_PREFIX=\"\$CONDA_PREFIX\" && unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS && export PATH=/usr/bin:/bin:\$PATH VERILATOR_BIN=\"\$CONDA_ENV_PREFIX/bin/verilator\" PYTHON_BIN=\"\$CONDA_ENV_PREFIX/bin/python3\" CC=/usr/bin/gcc CXX=/usr/bin/g++ CPP=/usr/bin/cpp LINK=/usr/bin/g++ AR=/usr/bin/ar LD=/usr/bin/ld NM=/usr/bin/nm RANLIB=/usr/bin/ranlib STRIP=/usr/bin/strip LANG=C LC_ALL=C && ${cmd}"
  local quoted_remote_cmd
  printf -v quoted_remote_cmd '%q' "${remote_cmd}"
  ssh "${SSH_OPTS[@]}" "${REMOTE_TARGET}" "bash -lc ${quoted_remote_cmd}"
}

sync_project() {
  remote_bash "mkdir -p generated verification verification/rtl verification/assert verification/assume verification/cover testbench/verilator scripts/verification verification/cases"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/generated/Top.sv" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/generated/Top.sv"

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

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/rtl/NinePSystemTop.sv" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/rtl/NinePSystemTop.sv"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/testbench/verilator/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/testbench/verilator/"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/scripts/verification/opt125m_e2e.py" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/scripts/verification/opt125m_e2e.py"

  rsync -az --delete \
    -e "ssh ${SSH_OPTS[*]}" \
    "${REPO_ROOT}/verification/cases/opt125m_stage_full/" \
    "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cases/opt125m_stage_full/"

  if [[ -d "${REPO_ROOT}/verification/cases/opt125m_stage_windows" ]]; then
    rsync -az \
      -e "ssh ${SSH_OPTS[*]}" \
      "${REPO_ROOT}/verification/cases/opt125m_stage_windows/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cases/opt125m_stage_windows/"
  fi

  local fullseq_dir
  for fullseq_dir in "${REPO_ROOT}"/verification/cases/opt125m_9p_fullseq*; do
    [[ -d "${fullseq_dir}" ]] || continue
    rsync -az --delete \
      -e "ssh ${SSH_OPTS[*]}" \
      "${fullseq_dir}/" \
      "${REMOTE_TARGET}:${REMOTE_WORKDIR}/verification/cases/$(basename "${fullseq_dir}")/"
  done
}

validate_remote() {
  local mode="$1"
  shift
  local args=("$@")
  sync_project
  local lock_file="${REMOTE_LOCK_DIR}/${mode}.lock"
  local inner_cmd="export VERILATOR_BUILD_JOBS=${REMOTE_MAKE_JOBS}; \"\$PYTHON_BIN\" scripts/verification/opt125m_e2e.py ${mode}"
  local arg
  for arg in "${args[@]}"; do
    printf -v inner_cmd '%s %q' "${inner_cmd}" "${arg}"
  done
  local cmd="flock -n ${lock_file@Q} bash -lc ${inner_cmd@Q}"
  remote_bash "${cmd}"
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
    validate-top)
      validate_remote "validate-top" "$@"
      ;;
    validate-system-top)
      validate_remote "validate-system-top" "$@"
      ;;
    validate-9p-fullseq)
      validate_remote "validate-9p-fullseq" "$@"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
