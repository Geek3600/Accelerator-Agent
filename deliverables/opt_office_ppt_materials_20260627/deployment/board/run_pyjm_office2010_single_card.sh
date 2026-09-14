#!/bin/bash
set -euo pipefail

DEMO_DIR=${DEMO_DIR:-/home/hyyuan/pyjm12_demo}
CARD_ID=${CARD_ID:-0}
XDMA_ID=${XDMA_ID:-7}
MIMIC_DIR=${MIMIC_DIR:-/home/test/mimic_driver_c6}

PYJM_SCRIPT=${PYJM_SCRIPT:-${DEMO_DIR}/run_pyjm_batch_demo.sh}
PATTERNS_FILE=${PATTERNS_FILE:-${DEMO_DIR}/patterns.txt}
PYJM_OUTPUT=${PYJM_OUTPUT:-${DEMO_DIR}/10^4_fpga.txt}
TOTAL_GENERATE=${TOTAL_GENERATE:-10000}
POLL_TIMEOUT_MS=${POLL_TIMEOUT_MS:-5000}
SEED=${SEED:-42}

OFFICE_ROOT=${OFFICE_ROOT:-${DEMO_DIR}/office2010_shared}
OFFICE_APP_DIR=${OFFICE_APP_DIR:-${OFFICE_ROOT}/App}
OFFICE_MASK_FILE=${OFFICE_MASK_FILE:-${OFFICE_APP_DIR}/1.hcmask}
OFFICE_ALL_MASK_FILE=${OFFICE_ALL_MASK_FILE:-${OFFICE_APP_DIR}/pyjm_all.hcmask}
OFFICE_CONVERT_PY=${OFFICE_CONVERT_PY:-${DEMO_DIR}/pyjm_passwords_to_hcmask.py}
OFFICE_TEST_BIN=${OFFICE_TEST_BIN:-${OFFICE_APP_DIR}/office2010_test}
OFFICE_BATCH_SIZE=21

usage() {
  cat <<'EOF'
Usage: run_pyjm_office2010_single_card.sh [options]

Options:
  --total-generate N         Total password count, default 10000.
  --poll-timeout-ms N        Poll timeout per OPT FPGA run, default 5000.
  --card-id N                FPGA card id, default 0.
  --xdma-id N                XDMA driver id, default 7.
  --seed N                   Password generation seed, default 42.
  -h, --help                 Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --total-generate)
      TOTAL_GENERATE=$2
      shift 2
      ;;
    --poll-timeout-ms)
      POLL_TIMEOUT_MS=$2
      shift 2
      ;;
    --card-id)
      CARD_ID=$2
      shift 2
      ;;
    --xdma-id)
      XDMA_ID=$2
      shift 2
      ;;
    --seed)
      SEED=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_file() {
  if [[ ! -e "$1" ]]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

run_sudo() {
  if [[ -n "${PYJM_SUDO_PASSWORD:-}" ]]; then
    sudo -S -p '' "$@" <<<"$PYJM_SUDO_PASSWORD"
  else
    sudo "$@"
  fi
}

echo "=== PYJM + Office2010 single-card flow ==="
echo "DEMO_DIR=${DEMO_DIR}"
echo "CARD_ID=${CARD_ID}"
echo "XDMA_ID=${XDMA_ID}"
echo "MIMIC_DIR=${MIMIC_DIR}"
echo "PATTERNS_FILE=${PATTERNS_FILE}"
echo "PYJM_OUTPUT=${PYJM_OUTPUT}"
echo "TOTAL_GENERATE=${TOTAL_GENERATE}"
echo "OFFICE_ROOT=${OFFICE_ROOT}"

require_file "$PYJM_SCRIPT"
require_file "$PATTERNS_FILE"
require_file "$OFFICE_CONVERT_PY"
require_file "${OFFICE_ROOT}/include/mimic_api.h"
require_file "${OFFICE_ROOT}/include/mimic_sdk.h"
require_file "${OFFICE_ROOT}/include/mimic_dma.h"
require_file "${OFFICE_ROOT}/lib/liboffice2010_mask.a"
require_file "${OFFICE_ROOT}/lib/libmimic_v6_api.so"
require_file "${OFFICE_ROOT}/lib/libmimic_v6_sdk.so"
require_file "${OFFICE_APP_DIR}/app_shell_9p_wrapper.bin"
require_file "${OFFICE_APP_DIR}/FPGA_Crack_Info.ini"
require_file "$OFFICE_TEST_BIN"
require_file "${MIMIC_DIR}/test/fpga_program/fpga_program"

pyjm_args=(
  --patterns-file "$PATTERNS_FILE"
  --output-file "$PYJM_OUTPUT"
  --total-generate "$TOTAL_GENERATE"
  --poll-timeout-ms "$POLL_TIMEOUT_MS"
  --card-id "$CARD_ID"
  --xdma-id "$XDMA_ID"
  --seed "$SEED"
)

echo "=== Stage 1: OPT password generation ==="
"$PYJM_SCRIPT" "${pyjm_args[@]}"

echo "=== Stage 2: Convert passwords to Office2010 exact hcmask ==="
python3 "$OFFICE_CONVERT_PY" \
  --input-file "$PYJM_OUTPUT" \
  --output-file "$OFFICE_ALL_MASK_FILE"

run_sudo -v

echo "=== Stage 3: Program Office2010 bitstream ==="
pushd "$MIMIC_DIR" >/dev/null
run_sudo env "LD_LIBRARY_PATH=${MIMIC_DIR}/src:${LD_LIBRARY_PATH:-}" \
  ./test/fpga_program/fpga_program "${OFFICE_APP_DIR}/app_shell_9p_wrapper.bin" "$CARD_ID"
popd >/dev/null

echo "=== Stage 4: Office2010 crack with generated masks ==="
mask_count=$(wc -l < "$OFFICE_ALL_MASK_FILE")
if [[ "$mask_count" -le 0 ]]; then
  echo "no generated Office2010 masks" >&2
  exit 1
fi

batch_idx=0
start_line=1
while [[ "$start_line" -le "$mask_count" ]]; do
  end_line=$((start_line + OFFICE_BATCH_SIZE - 1))
  batch_idx=$((batch_idx + 1))
  sed -n "${start_line},${end_line}p" "$OFFICE_ALL_MASK_FILE" > "$OFFICE_MASK_FILE"
  batch_log="${OFFICE_APP_DIR}/office2010_batch_${batch_idx}.log"

  echo "office2010 batch=${batch_idx} masks=${start_line}-${end_line}"
  pushd "$OFFICE_APP_DIR" >/dev/null
  set +e
  run_sudo env "LD_LIBRARY_PATH=${OFFICE_ROOT}/lib:${LD_LIBRARY_PATH:-}" \
    "$OFFICE_TEST_BIN" "$CARD_ID" | tee "$batch_log"
  office_rc=${PIPESTATUS[0]}
  set -e
  popd >/dev/null

  if [[ "$office_rc" -ne 0 ]]; then
    echo "office2010_test failed in batch ${batch_idx}" >&2
    exit "$office_rc"
  fi

  if grep -q '^password:' "$batch_log"; then
    echo "=== Office2010 hit ==="
    grep '^password:' "$batch_log" | tail -n 1
    exit 0
  fi

  start_line=$((end_line + 1))
done

echo "=== Office2010 exhausted all generated passwords without hit ==="
exit 4
