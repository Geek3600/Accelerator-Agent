#!/bin/bash
set -euo pipefail

DEMO_DIR=${DEMO_DIR:-/home/hyyuan/pyjm12_demo}
MIMIC_DIR=${MIMIC_DIR:-/home/test/mimic_driver_c6}
CARDS=${CARDS:-0,1,2,3,4,5,6,7}
TOTAL_GENERATE=${TOTAL_GENERATE:-10000}
POLL_TIMEOUT_MS=${POLL_TIMEOUT_MS:-5000}
SEED=${SEED:-42}
PARALLEL=1
CARD_START_SPREAD_SEC=${CARD_START_SPREAD_SEC:-4}
MULTI_POST_PROGRAM_SLEEP_SEC=${MULTI_POST_PROGRAM_SLEEP_SEC:-8}
MULTI_WARMUP_RETRIES=${MULTI_WARMUP_RETRIES:-8}
APP_STATUS_ENABLE=${APP_STATUS_ENABLE:-1}
APP_STATUS_JSON=${APP_STATUS_JSON:-/home/share/app_status.json}
APP_STATUS_LOCK=${APP_STATUS_LOCK:-/home/share/.app_status.lock}
APP_STATUS_COUNTER=${APP_STATUS_COUNTER:-/home/share/.app_status_task_counter_10.txt}
APP_STATUS_APPLICATION=${APP_STATUS_APPLICATION:-应用2-4}
APP_STATUS_REFRESH_SEC=${APP_STATUS_REFRESH_SEC:-0.2}
APP_STATUS_WORKER_IP=${APP_STATUS_WORKER_IP:-}
APP_STATUS_SCRIPT=${APP_STATUS_SCRIPT:-${DEMO_DIR}/pyjm_update_app_status.py}

BASE_OFFICE_ROOT=${BASE_OFFICE_ROOT:-${DEMO_DIR}/office2010_shared}
SINGLE_SCRIPT=${SINGLE_SCRIPT:-${DEMO_DIR}/run_pyjm_office2010_single_card.sh}
LOG_DIR=${LOG_DIR:-${DEMO_DIR}/multi_card_logs}

usage() {
  cat <<'EOF'
Usage: run_pyjm_office2010_multi_card.sh [options]

Options:
  --cards LIST              Comma-separated card ids, default 0,1,2,3,4,5,6,7.
  --total-generate N        Total password count per card, default 10000.
  --poll-timeout-ms N       Poll timeout per OPT FPGA run, default 5000.
  --seed N                  Base password generation seed, default 42.
  --parallel                Run cards in parallel.
  --sequential              Run cards one by one.
  --status-json PATH        Frontend app status json, default /home/share/app_status.json.
  --status-refresh SEC      Running-card status refresh interval, default 0.2.
  -h, --help                Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cards)
      CARDS=$2
      shift 2
      ;;
    --total-generate)
      TOTAL_GENERATE=$2
      shift 2
      ;;
    --poll-timeout-ms)
      POLL_TIMEOUT_MS=$2
      shift 2
      ;;
    --seed)
      SEED=$2
      shift 2
      ;;
    --parallel)
      PARALLEL=1
      shift
      ;;
    --sequential)
      PARALLEL=0
      shift
      ;;
    --status-json)
      APP_STATUS_JSON=$2
      shift 2
      ;;
    --status-refresh)
      APP_STATUS_REFRESH_SEC=$2
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

xdma_for_card() {
  case "$1" in
    0) echo 7 ;;
    1) echo 3 ;;
    2) echo 6 ;;
    3) echo 2 ;;
    4) echo 5 ;;
    5) echo 1 ;;
    6) echo 4 ;;
    7) echo 0 ;;
    *)
      echo "unsupported card id: $1" >&2
      return 1
      ;;
  esac
}

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

prepare_card_dir() {
  local card_id=$1
  local card_dir="${DEMO_DIR}/card_${card_id}"
  local office_root="${card_dir}/office2010_shared"
  local office_app="${office_root}/App"

  mkdir -p "$card_dir" "$office_root" "$office_app"

  ln -sf "${DEMO_DIR}/app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit" \
    "${card_dir}/app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit"
  ln -sf "${DEMO_DIR}/ddr_image.u32.bin" "${card_dir}/ddr_image.u32.bin"
  ln -sf "${DEMO_DIR}/patterns.txt" "${card_dir}/patterns.txt"
  ln -sf "${DEMO_DIR}/pyjm_fpga_demo.c" "${card_dir}/pyjm_fpga_demo.c"
  ln -sf "${DEMO_DIR}/pyjm_fpga_batch_gen.py" "${card_dir}/pyjm_fpga_batch_gen.py"
  ln -sf "${DEMO_DIR}/pyjm_passwords_to_hcmask.py" "${card_dir}/pyjm_passwords_to_hcmask.py"
  ln -sf "${DEMO_DIR}/pyjm_update_app_status.py" "${card_dir}/pyjm_update_app_status.py"
  ln -sf "${DEMO_DIR}/run_pyjm_batch_demo.sh" "${card_dir}/run_pyjm_batch_demo.sh"

  ln -sfn "${BASE_OFFICE_ROOT}/include" "${office_root}/include"
  ln -sfn "${BASE_OFFICE_ROOT}/lib" "${office_root}/lib"
  ln -sf "${BASE_OFFICE_ROOT}/App/app_shell_9p_wrapper.bin" "${office_app}/app_shell_9p_wrapper.bin"
  ln -sf "${BASE_OFFICE_ROOT}/App/FPGA_Crack_Info.ini" "${office_app}/FPGA_Crack_Info.ini"
  ln -sf "${BASE_OFFICE_ROOT}/App/office2010_test" "${office_app}/office2010_test"
  rm -f "${office_app}/1.hcmask" "${office_app}/pyjm_all.hcmask" "${office_app}"/office2010_batch_*.log
}

app_status_update() {
  local mode=$1
  local card_id=$2
  local task=${3:-}

  if [[ "$APP_STATUS_ENABLE" -ne 1 ]]; then
    return 0
  fi

  python3 "$APP_STATUS_SCRIPT" "$mode" \
    --card-id "$card_id" \
    --task "$task" \
    --application "$APP_STATUS_APPLICATION" \
    --json-file "$APP_STATUS_JSON" \
    --lock-file "$APP_STATUS_LOCK" \
    --counter-file "$APP_STATUS_COUNTER" \
    --worker-ip "$APP_STATUS_WORKER_IP"
}

start_app_status_heartbeat() {
  local card_id=$1
  local task=$2

  if [[ "$APP_STATUS_ENABLE" -ne 1 ]]; then
    return 0
  fi

  (
    while true; do
      sleep "$APP_STATUS_REFRESH_SEC"
      app_status_update running "$card_id" "$task" >/dev/null || true
    done
  ) >/dev/null 2>&1 &
  echo "$!"
}

stop_app_status_heartbeat() {
  local heartbeat_pid=$1

  if [[ -n "$heartbeat_pid" ]]; then
    kill "$heartbeat_pid" 2>/dev/null || true
    wait "$heartbeat_pid" 2>/dev/null || true
  fi
}

run_card() {
  local card_id=$1
  local xdma_id=$2
  local card_dir="${DEMO_DIR}/card_${card_id}"
  local card_seed=$SEED
  local start_delay=0
  local task_id=""
  local heartbeat_pid=""
  local rc=1

  if [[ "$CARD_START_SPREAD_SEC" -gt 0 ]]; then
    start_delay=$((card_id % CARD_START_SPREAD_SEC))
  fi
  if [[ "$start_delay" -gt 0 ]]; then
    sleep "$start_delay"
  fi

  prepare_card_dir "$card_id"

  if [[ "$APP_STATUS_ENABLE" -eq 1 ]]; then
    task_id=$(app_status_update start "$card_id")
    heartbeat_pid=$(start_app_status_heartbeat "$card_id" "$task_id")
    echo "app_status card=${card_id} task=${task_id} json=${APP_STATUS_JSON}"
  fi

  set +e
  DEMO_DIR="$card_dir" \
  MIMIC_DIR="$MIMIC_DIR" \
  POST_PROGRAM_SLEEP_SEC="$MULTI_POST_PROGRAM_SLEEP_SEC" \
  WARMUP_RETRIES="$MULTI_WARMUP_RETRIES" \
  TOOL_BIN="${card_dir}/pyjm_fpga_demo" \
  "$SINGLE_SCRIPT" \
    --card-id "$card_id" \
    --xdma-id "$xdma_id" \
    --seed "$card_seed" \
    --total-generate "$TOTAL_GENERATE" \
    --poll-timeout-ms "$POLL_TIMEOUT_MS"
  rc=$?
  set -e

  stop_app_status_heartbeat "$heartbeat_pid"
  if [[ "$APP_STATUS_ENABLE" -eq 1 ]]; then
    app_status_update finish "$card_id" "$task_id" >/dev/null || true
  fi
  return "$rc"
}

require_file "$SINGLE_SCRIPT"
require_file "${DEMO_DIR}/run_pyjm_batch_demo.sh"
require_file "${DEMO_DIR}/pyjm_passwords_to_hcmask.py"
if [[ "$APP_STATUS_ENABLE" -eq 1 ]]; then
  require_file "$APP_STATUS_SCRIPT"
fi
require_file "${BASE_OFFICE_ROOT}/App/office2010_test"
mkdir -p "$LOG_DIR"

IFS=',' read -r -a card_list <<< "$CARDS"

echo "=== PYJM + Office2010 multi-card flow ==="
echo "DEMO_DIR=${DEMO_DIR}"
echo "MIMIC_DIR=${MIMIC_DIR}"
echo "CARDS=${CARDS}"
echo "TOTAL_GENERATE=${TOTAL_GENERATE}"
echo "POLL_TIMEOUT_MS=${POLL_TIMEOUT_MS}"
echo "PARALLEL=${PARALLEL}"
echo "LOG_DIR=${LOG_DIR}"
echo "APP_STATUS_ENABLE=${APP_STATUS_ENABLE}"
echo "APP_STATUS_JSON=${APP_STATUS_JSON}"
echo "APP_STATUS_REFRESH_SEC=${APP_STATUS_REFRESH_SEC}"

run_sudo -v

if [[ "$PARALLEL" -eq 0 ]]; then
  final_rc=4
  for card_id in "${card_list[@]}"; do
    xdma_id=$(xdma_for_card "$card_id")
    log="${LOG_DIR}/card_${card_id}.log"
    echo "card=${card_id} xdma=${xdma_id} log=${log}"
    set +e
    run_card "$card_id" "$xdma_id" 2>&1 | tee "$log"
    rc=${PIPESTATUS[0]}
    set -e
    if [[ "$rc" -eq 0 ]]; then
      final_rc=0
    elif [[ "$rc" -ne 4 ]]; then
      final_rc=1
    fi
  done
  exit "$final_rc"
fi

declare -a pids=()
declare -a cards=()

for card_id in "${card_list[@]}"; do
  xdma_id=$(xdma_for_card "$card_id")
  log="${LOG_DIR}/card_${card_id}.log"
  echo "start card=${card_id} xdma=${xdma_id} log=${log}"
  (
    run_card "$card_id" "$xdma_id"
  ) >"$log" 2>&1 &
  pids+=("$!")
  cards+=("$card_id")
done

final_rc=4
for i in "${!pids[@]}"; do
  pid=${pids[$i]}
  card_id=${cards[$i]}
  set +e
  wait "$pid"
  rc=$?
  set -e
  echo "card=${card_id} exit=${rc} log=${LOG_DIR}/card_${card_id}.log"
  if [[ "$rc" -eq 0 ]]; then
    final_rc=0
  elif [[ "$rc" -ne 4 ]]; then
    final_rc=1
  fi
done

exit "$final_rc"
