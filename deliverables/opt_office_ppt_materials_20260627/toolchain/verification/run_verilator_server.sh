#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CONDA_ENV_NAME="${CONDA_ENV_NAME:-chisel_env}"
MAKE_JOBS="${MAKE_JOBS:-32}"
LOCK_DIR="${LOCK_DIR:-/tmp/qwen2_remote_verilator}"

usage() {
  cat <<'EOF'
Usage:
  run_verilator_server.sh validate-top [args...]
  run_verilator_server.sh validate-system-top [args...]
  run_verilator_server.sh prepare-9p-fullseq-case [args...]

Examples:
  ./scripts/verification/run_verilator_server.sh validate-top --token-start 0 --token-count 1
  MAKE_JOBS=32 ./scripts/verification/run_verilator_server.sh validate-system-top --token-start 0 --token-count 1
EOF
}

if (($# == 0)); then
  usage
  exit 1
fi

MODE="$1"
shift

source ~/.bashrc
conda activate "${CONDA_ENV_NAME}"

export CONDA_ENV_PREFIX="${CONDA_PREFIX}"
export VERILATOR_BIN="${CONDA_ENV_PREFIX}/bin/verilator"
export PYTHON_BIN="${CONDA_ENV_PREFIX}/bin/python3"

# Conda 的编译器 wrapper 会把标准降回 gnu++14，导致 <filesystem> 相关编译失败。
# 这里显式切到系统工具链，同时继续使用 conda 环境里的 Python / Verilator。
unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS
export PATH="/usr/bin:/bin:${PATH}"
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
export VERILATOR_BUILD_JOBS="${MAKE_JOBS}"

cd "${REPO_ROOT}"
mkdir -p "${LOCK_DIR}"
LOCK_FILE="${LOCK_DIR}/${MODE}.lock"
flock -n "${LOCK_FILE}" "${PYTHON_BIN}" scripts/verification/opt125m_e2e.py "${MODE}" "$@"
