#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CONDA_ENV_NAME="${CONDA_ENV_NAME:-chisel_env}"
MAKE_JOBS="${MAKE_JOBS:-16}"
LOCK_DIR="${LOCK_DIR:-/tmp/qwen2_remote_vcs}"
VCS_HOME="${VCS_HOME:-/home/EDA/Software/EDATools/Synopsys/VCSALL/v202109}"

usage() {
  cat <<'EOF'
Usage:
  run_vcs_server.sh validate-9p-fullseq-vcs [args...]
  run_vcs_server.sh validate-axi-board-fullseq-vcs [args...]
  run_vcs_server.sh validate-cnn-core-fullseq-vcs [args...]
  run_vcs_server.sh validate-opt-acc-core-fullseq-vcs [args...]

Examples:
  MAKE_JOBS=16 ./scripts/verification/run_vcs_server.sh validate-9p-fullseq-vcs
  MAKE_JOBS=16 ./scripts/verification/run_vcs_server.sh validate-axi-board-fullseq-vcs
  MAKE_JOBS=16 ./scripts/verification/run_vcs_server.sh validate-cnn-core-fullseq-vcs
  MAKE_JOBS=16 ./scripts/verification/run_vcs_server.sh validate-opt-acc-core-fullseq-vcs
EOF
}

if (($# == 0)); then
  usage
  exit 1
fi

MODE="$1"
shift

export PS1="${PS1-}"
set +u
source ~/.bashrc
conda activate "${CONDA_ENV_NAME}"
set -u

export CONDA_ENV_PREFIX="${CONDA_PREFIX}"
export PYTHON_BIN="${CONDA_ENV_PREFIX}/bin/python3"
export VCS_HOME
export PATH="${VCS_HOME}/bin:/usr/bin:/bin:${PATH}"

unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CPP=/usr/bin/cpp
export LINK=/usr/bin/g++
export AR=/usr/bin/ar
export LD=/usr/bin/ld
export NM=/usr/bin/nm
export RANLIB=/usr/bin/ranlib
export STRIP=/usr/bin/strip
export LANG=C
export LC_ALL=C
export VCS_BUILD_JOBS="${MAKE_JOBS}"

cd "${REPO_ROOT}"
mkdir -p "${LOCK_DIR}"
LOCK_FILE="${LOCK_DIR}/${MODE}.lock"
flock -n "${LOCK_FILE}" "${PYTHON_BIN}" scripts/verification/opt125m_e2e.py "${MODE}" "$@"
