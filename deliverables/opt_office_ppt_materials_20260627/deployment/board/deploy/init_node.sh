#!/bin/bash
set -euo pipefail

DEMO_DIR=${DEMO_DIR:-/home/hyyuan/pyjm12_demo}
MIMIC_DIR=${MIMIC_DIR:-/home/test/mimic_driver_c6}
SHARE_DIR=${SHARE_DIR:-/home/share}
APP_STATUS_JSON=${APP_STATUS_JSON:-${SHARE_DIR}/app_status.json}
APP_STATUS_LOCK=${APP_STATUS_LOCK:-${SHARE_DIR}/.app_status.lock}
APP_STATUS_COUNTER=${APP_STATUS_COUNTER:-${SHARE_DIR}/.app_status_task_counter_10.txt}
XDMA_LOAD_SCRIPT=${XDMA_LOAD_SCRIPT:-${MIMIC_DIR}/xdma_driver/tests/load_driver.sh}
XDMA_LOAD_ARG=${XDMA_LOAD_ARG:-4}

run_sudo() {
  if [[ -n "${PYJM_SUDO_PASSWORD:-}" ]]; then
    sudo -S -p '' "$@" <<<"$PYJM_SUDO_PASSWORD"
  else
    sudo "$@"
  fi
}

require_file() {
  if [[ ! -e "$1" ]]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

require_file "${MIMIC_DIR}/test/fpga_program/fpga_program"
require_file "${MIMIC_DIR}/test/get_fpga_num/get_fpga_num"
require_file "${MIMIC_DIR}/xdma_driver/tools/dma_from_device"
require_file "${MIMIC_DIR}/xdma_driver/tools/dma_to_device"
require_file "$XDMA_LOAD_SCRIPT"
require_file "${DEMO_DIR}/deploy/app_status.template.json"

run_sudo mkdir -p "$SHARE_DIR"
if [[ ! -e "$APP_STATUS_JSON" ]]; then
  run_sudo cp "${DEMO_DIR}/deploy/app_status.template.json" "$APP_STATUS_JSON"
fi
run_sudo touch "$APP_STATUS_LOCK" "$APP_STATUS_COUNTER"
run_sudo chmod 777 "$SHARE_DIR"
run_sudo chmod 666 "$APP_STATUS_JSON" "$APP_STATUS_LOCK" "$APP_STATUS_COUNTER"
run_sudo chmod +x \
  "${MIMIC_DIR}/xdma_driver/tools/dma_from_device" \
  "${MIMIC_DIR}/xdma_driver/tools/dma_to_device"

if ! ls /dev/xdma*_h2c_0 >/dev/null 2>&1; then
  pushd "$(dirname "$XDMA_LOAD_SCRIPT")" >/dev/null
  run_sudo bash "./$(basename "$XDMA_LOAD_SCRIPT")" "$XDMA_LOAD_ARG"
  popd >/dev/null
fi

python3 -m json.tool "$APP_STATUS_JSON" >/dev/null
"${DEMO_DIR}/deploy/preflight_check.sh"
