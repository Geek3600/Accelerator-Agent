#!/bin/bash
set -euo pipefail

DEMO_DIR=${DEMO_DIR:-/home/hyyuan/pyjm12_demo}
MIMIC_DIR=${MIMIC_DIR:-/home/test/mimic_driver_c6}
APP_STATUS_JSON=${APP_STATUS_JSON:-/home/share/app_status.json}

require_file() {
  if [[ ! -e "$1" ]]; then
    echo "missing required file: $1" >&2
    exit 1
  fi
}

check_size() {
  local path=$1
  local expected=$2
  local got
  got=$(stat -Lc '%s' "$path")
  if [[ "$got" != "$expected" ]]; then
    echo "size mismatch: $path got=$got expected=$expected" >&2
    exit 1
  fi
}

require_file "${DEMO_DIR}/app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit"
require_file "${DEMO_DIR}/ddr_image.u32.bin"
require_file "${DEMO_DIR}/patterns.txt"
require_file "${DEMO_DIR}/pyjm_fpga_demo.c"
require_file "${DEMO_DIR}/pyjm_fpga_batch_gen.py"
require_file "${DEMO_DIR}/pyjm_passwords_to_hcmask.py"
require_file "${DEMO_DIR}/pyjm_update_app_status.py"
require_file "${DEMO_DIR}/run_pyjm_batch_demo.sh"
require_file "${DEMO_DIR}/run_pyjm_office2010_single_card.sh"
require_file "${DEMO_DIR}/run_pyjm_office2010_multi_card.sh"
require_file "${DEMO_DIR}/office2010_shared/App/app_shell_9p_wrapper.bin"
require_file "${DEMO_DIR}/office2010_shared/App/FPGA_Crack_Info.ini"
require_file "${DEMO_DIR}/office2010_shared/App/office2010_test"
require_file "${DEMO_DIR}/office2010_shared/include/mimic_api.h"
require_file "${DEMO_DIR}/office2010_shared/include/mimic_sdk.h"
require_file "${DEMO_DIR}/office2010_shared/include/mimic_dma.h"
require_file "${DEMO_DIR}/office2010_shared/lib/libmimic_v6_api.so"
require_file "${DEMO_DIR}/office2010_shared/lib/libmimic_v6_sdk.so"
require_file "${DEMO_DIR}/office2010_shared/lib/liboffice2010_mask.a"
require_file "${MIMIC_DIR}/test/fpga_program/fpga_program"
require_file "${MIMIC_DIR}/test/get_fpga_num/get_fpga_num"

check_size "${DEMO_DIR}/app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit" 80159236
check_size "${DEMO_DIR}/ddr_image.u32.bin" 154080256
check_size "${DEMO_DIR}/office2010_shared/App/app_shell_9p_wrapper.bin" 80159108

bash -n \
  "${DEMO_DIR}/run_pyjm_batch_demo.sh" \
  "${DEMO_DIR}/run_pyjm_office2010_single_card.sh" \
  "${DEMO_DIR}/run_pyjm_office2010_multi_card.sh"
python3 -m py_compile \
  "${DEMO_DIR}/pyjm_fpga_batch_gen.py" \
  "${DEMO_DIR}/pyjm_passwords_to_hcmask.py" \
  "${DEMO_DIR}/pyjm_update_app_status.py"
python3 -m json.tool "$APP_STATUS_JSON" >/dev/null

fpga_map=$("${MIMIC_DIR}/test/get_fpga_num/get_fpga_num")
printf '%s\n' "$fpga_map"
printf '%s\n' "$fpga_map" | grep -q "FPGA number is 8"

echo "preflight_check_ok"
