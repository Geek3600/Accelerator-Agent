#!/bin/bash
set -euo pipefail

DEMO_DIR=${DEMO_DIR:-/home/hyyuan/pyjm12_demo}
MIMIC_DIR=${MIMIC_DIR:-/home/test/mimic_driver_c6}
CARD_ID=${CARD_ID:-0}
XDMA_ID=${XDMA_ID:-7}

BIT=${BIT:-${DEMO_DIR}/app_shell_9p_wrapper_debug_latency_fixedmux_constrained_20260513.bit}
DDR_IMAGE=${DDR_IMAGE:-${DEMO_DIR}/ddr_image.u32.bin}
PATTERNS_FILE=${PATTERNS_FILE:-${DEMO_DIR}/patterns.txt}
OUTPUT_FILE=${OUTPUT_FILE:-${DEMO_DIR}/10^4_fpga.txt}
TOOL_SRC=${TOOL_SRC:-${DEMO_DIR}/pyjm_fpga_demo.c}
TOOL_BIN=${TOOL_BIN:-/tmp/pyjm_fpga_demo}
BATCH_PY=${BATCH_PY:-${DEMO_DIR}/pyjm_fpga_batch_gen.py}

EXPECTED_BIT_SIZE=80159236
EXPECTED_DDR_SIZE=154080256
TOTAL_GENERATE=${TOTAL_GENERATE:-10000}
POLL_TIMEOUT_MS=${POLL_TIMEOUT_MS:-5000}
WARMUP_RETRIES=${WARMUP_RETRIES:-5}
POST_PROGRAM_SLEEP_SEC=${POST_PROGRAM_SLEEP_SEC:-5}
VALIDATE_SIMPLE_PATTERN=0
SEED=${SEED:-42}

usage() {
  cat <<'EOF'
Usage: run_pyjm_batch_demo.sh [options]

Options:
  --patterns-file PATH       Pattern ratio TSV.
  --output-file PATH         Output file.
  --total-generate N         Total password count, default 10000.
  --poll-timeout-ms N        Poll timeout per FPGA run, default 5000.
  --card-id N                FPGA card id, default 0.
  --xdma-id N                XDMA driver id, default 7.
  --seed N                   Password generation seed, default 42.
  --validate-simple-pattern  Enable simple L/N/S/U/l validation.
  -h, --help                 Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --patterns-file)
      PATTERNS_FILE=$2
      shift 2
      ;;
    --output-file)
      OUTPUT_FILE=$2
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
    --validate-simple-pattern)
      VALIDATE_SIMPLE_PATTERN=1
      shift
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

print_power_status() {
  python3 - <<'PY' || true
import json
import subprocess
import urllib.request

api = "http://10.200.100.100:8000/power/cluster-monitor"

def detect_node_ip():
    try:
        out = subprocess.check_output(
            ["ip", "route", "get", "10.200.100.100"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        parts = out.split()
        if "src" in parts:
            src = parts[parts.index("src") + 1]
            if src.startswith("10.200.100."):
                return "192.168.100." + str(int(src.rsplit(".", 1)[1]) + 100)
    except Exception:
        pass
    return ""

try:
    with urllib.request.urlopen(api, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    payload = data.get("data") or {}
    node_ip = detect_node_ip()
    nodes = payload.get("nodes") or {}
    if node_ip and node_ip in nodes:
        print(f"local_node_power[{node_ip}]={float(nodes[node_ip]):.2f} W")
    elif payload.get("cluster_avg") is not None:
        print(f"cluster_power={float(payload['cluster_avg']):.2f} W")
    else:
        print("power_status=unavailable")
except Exception as exc:
    print(f"power_status=unavailable ({exc})")
PY
}

echo "=== PYJM FPGA batch demo ==="
echo "BIT=${BIT}"
echo "DDR_IMAGE=${DDR_IMAGE}"
echo "PATTERNS_FILE=${PATTERNS_FILE}"
echo "OUTPUT_FILE=${OUTPUT_FILE}"
echo "TOTAL_GENERATE=${TOTAL_GENERATE}"
echo "CARD_ID=${CARD_ID}"
echo "XDMA_ID=${XDMA_ID}"

require_file "$BIT"
require_file "$DDR_IMAGE"
require_file "$PATTERNS_FILE"
require_file "$TOOL_SRC"
require_file "$BATCH_PY"
require_file "${MIMIC_DIR}/test/fpga_program/fpga_program"
require_file "${MIMIC_DIR}/test/get_fpga_num/get_fpga_num"
check_size "$BIT" "$EXPECTED_BIT_SIZE"
check_size "$DDR_IMAGE" "$EXPECTED_DDR_SIZE"

run_sudo -v

echo "=== FPGA card mapping ==="
fpga_map=$(run_sudo env "LD_LIBRARY_PATH=${MIMIC_DIR}/src:${LD_LIBRARY_PATH:-}" \
  "${MIMIC_DIR}/test/get_fpga_num/get_fpga_num")
printf '%s\n' "$fpga_map"
if ! printf '%s\n' "$fpga_map" | grep -Eq "FPGA device ${CARD_ID}: .*driver handle xdma${XDMA_ID}"; then
  echo "expected FPGA device ${CARD_ID} to use xdma${XDMA_ID}" >&2
  exit 1
fi
echo "xdma_devices=/dev/xdma${XDMA_ID}_h2c_0 /dev/xdma${XDMA_ID}_c2h_0"
ls -l "/dev/xdma${XDMA_ID}_h2c_0" "/dev/xdma${XDMA_ID}_c2h_0"

echo "=== Power status ==="
print_power_status

echo "=== Compile host tool ==="
gcc -O2 -Wall -Wextra "$TOOL_SRC" -o "$TOOL_BIN"

echo "=== Program FPGA ==="
pushd "$MIMIC_DIR" >/dev/null
run_sudo env "LD_LIBRARY_PATH=${MIMIC_DIR}/src:${LD_LIBRARY_PATH:-}" \
  ./test/fpga_program/fpga_program "$BIT" "$CARD_ID"
popd >/dev/null
sleep "$POST_PROGRAM_SLEEP_SEC"

echo "=== Load DDR image and warm up ==="
warmup_ok=0
for attempt in $(seq 1 "$WARMUP_RETRIES"); do
  echo "warmup attempt ${attempt}/${WARMUP_RETRIES}"
  if run_sudo env XDMA_ID="$XDMA_ID" DDR_IMAGE="$DDR_IMAGE" PATTERN=L8 \
    "$TOOL_BIN" \
      --runs 1 \
      --poll-timeout-ms "$POLL_TIMEOUT_MS" \
      --write-ddr-mode 2 \
      --pattern L8 \
      --raw-output-bytes 1024 \
      --nonce 0 \
      --no-password-record; then
    warmup_ok=1
    break
  fi
  sleep 1
done
if [[ "$warmup_ok" -ne 1 ]]; then
  echo "warmup failed after ${WARMUP_RETRIES} attempts" >&2
  exit 1
fi

batch_args=(
  --patterns-file "$PATTERNS_FILE"
  --output-file "$OUTPUT_FILE"
  --total-generate "$TOTAL_GENERATE"
  --max-retry-factor 10
  --seed "$SEED"
  --fpga-tool "$TOOL_BIN"
  --xdma-id "$XDMA_ID"
  --ddr-image "$DDR_IMAGE"
  --poll-timeout-ms "$POLL_TIMEOUT_MS"
)
if [[ "$VALIDATE_SIMPLE_PATTERN" -eq 1 ]]; then
  batch_args+=(--validate-simple-pattern)
fi

echo "=== Generate passwords ==="
run_sudo env \
  XDMA_ID="$XDMA_ID" \
  DDR_IMAGE="$DDR_IMAGE" \
  python3 "$BATCH_PY" "${batch_args[@]}"
run_sudo chown "$(id -u):$(id -g)" "$OUTPUT_FILE"

echo "=== Output summary ==="
sed -n '1,20p' "$OUTPUT_FILE"
wc -l "$OUTPUT_FILE"
run_sudo rm -f "${DEMO_DIR}/mmsdk.log" "$TOOL_BIN"
run_sudo rm -rf "${DEMO_DIR}/__pycache__"
