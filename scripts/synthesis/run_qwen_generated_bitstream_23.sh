#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-bitstream}"
RUN_DIR="${2:-/tmp/spatialacc_qwen_agent_run}"
CLOCK_PERIOD_NS="${3:-10.000}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/tmp/spatialacc_qwen_agent_run}"
VIVADO_BIN="${VIVADO_BIN:-}"
REMOTE_KNOWN_HOSTS="${REMOTE_KNOWN_HOSTS:-/tmp/codex_ssh_known_hosts}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCAL_TCL="$ROOT_DIR/scripts/synthesis/qwen_generated_bitstream_23.tcl"
LOCAL_SV_DIR="$RUN_DIR/generated/chisel"
LOCAL_TOP="$LOCAL_SV_DIR/GeneratedAcceleratorTop.sv"
LOCAL_FPGA_TOP="$LOCAL_SV_DIR/GeneratedAxiDdrTop.sv"
LOCAL_IP_TCL="$LOCAL_SV_DIR/scripts/gen_xilinx_fp_ips_23.tcl"
LOCAL_IP_MODULES="$LOCAL_SV_DIR/simulation/fpga_ip_modules.txt"
LOCAL_RUNTIME_CONFIG="$LOCAL_SV_DIR/runtime/runtime_config.json"
LOCAL_NUMERIC_DIR="$LOCAL_SV_DIR/src/main/resources/spatialaccagent/numeric"
LOCAL_OUT_DIR="$RUN_DIR/vivado_qwen_generated_${MODE}"

if [[ -z "$REMOTE_HOST" ]]; then
  echo "REMOTE_HOST must be set from the Stage 0 tool profile or user environment" >&2
  exit 2
fi
if [[ -z "$VIVADO_BIN" ]]; then
  echo "VIVADO_BIN must be set from the Stage 0 tool profile or user environment" >&2
  exit 2
fi
if [[ -z "${FPGA_PART:-}" ]]; then
  if [[ ! -f "$LOCAL_RUNTIME_CONFIG" ]]; then
    echo "Missing generated runtime config: $LOCAL_RUNTIME_CONFIG" >&2
    exit 1
  fi
  FPGA_PART="$(python3 - "$LOCAL_RUNTIME_CONFIG" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("board", {}).get("fpga_part", ""))
PY
)"
fi
if [[ -z "$FPGA_PART" ]]; then
  echo "FPGA part is missing from runtime_config.json and FPGA_PART is unset" >&2
  exit 1
fi

case "$MODE" in
  synth|bitstream|power) ;;
  *)
    echo "Usage: $0 [synth|bitstream|power] [run_dir]" >&2
    exit 2
    ;;
esac

if [[ "$MODE" != "power" && ! -f "$LOCAL_TOP" ]]; then
  echo "Missing generated Qwen top SystemVerilog: $LOCAL_TOP" >&2
  exit 1
fi
if [[ "$MODE" != "power" && ! -f "$LOCAL_FPGA_TOP" ]]; then
  echo "Missing generated Qwen FPGA AXI/DDR top SystemVerilog: $LOCAL_FPGA_TOP" >&2
  exit 1
fi
if [[ "$MODE" != "power" && ! -f "$LOCAL_SV_DIR/LlamaStyleBlock.sv" ]]; then
  echo "Missing generated Qwen core SystemVerilog: $LOCAL_SV_DIR/LlamaStyleBlock.sv" >&2
  exit 1
fi
if [[ ! -f "$LOCAL_TCL" ]]; then
  echo "Missing Vivado Tcl: $LOCAL_TCL" >&2
  exit 1
fi
if [[ "$MODE" != "power" && ! -f "$LOCAL_IP_TCL" ]]; then
  echo "Missing generated Vivado IP Tcl: $LOCAL_IP_TCL" >&2
  exit 1
fi
if [[ "$MODE" != "power" && ! -s "$LOCAL_IP_MODULES" ]]; then
  echo "Missing generated Vivado IP module manifest: $LOCAL_IP_MODULES" >&2
  exit 1
fi
if [[ "$MODE" != "power" ]]; then
  for lut in exp2_fraction_q24.mem sigmoid_pwl_q18.mem; do
    if [[ ! -s "$LOCAL_NUMERIC_DIR/$lut" ]]; then
      echo "Missing generated XPM ROM initialization file: $LOCAL_NUMERIC_DIR/$lut" >&2
      exit 1
    fi
  done
fi

SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}"
  -p "${REMOTE_PORT}"
)

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "mkdir -p '$REMOTE_WORKDIR'"
if [[ "$MODE" != "power" ]]; then
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "rm -f '$REMOTE_WORKDIR'/*.sv; rm -rf '$REMOTE_WORKDIR/fpga_ip' '$REMOTE_WORKDIR/src/main/resources'"
  scp -q -P "$REMOTE_PORT" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
    "$LOCAL_SV_DIR"/*.sv "$REMOTE_HOST:$REMOTE_WORKDIR/"
  scp -q -P "$REMOTE_PORT" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
    "$LOCAL_IP_TCL" "$REMOTE_HOST:$REMOTE_WORKDIR/gen_xilinx_fp_ips_23.tcl"
  scp -q -P "$REMOTE_PORT" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
    "$LOCAL_IP_MODULES" "$REMOTE_HOST:$REMOTE_WORKDIR/fpga_ip_modules.txt"
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "mkdir -p '$REMOTE_WORKDIR/src/main/resources/spatialaccagent/numeric'"
  scp -q -P "$REMOTE_PORT" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
    "$LOCAL_NUMERIC_DIR/exp2_fraction_q24.mem" \
    "$LOCAL_NUMERIC_DIR/sigmoid_pwl_q18.mem" \
    "$REMOTE_HOST:$REMOTE_WORKDIR/src/main/resources/spatialaccagent/numeric/"
fi
scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$LOCAL_TCL" "$REMOTE_HOST:$REMOTE_WORKDIR/qwen_generated_bitstream_23.tcl"

stamp="$(date +%Y%m%d_%H%M%S)"
if [[ "$MODE" != "power" ]]; then
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" \
    "cd '$REMOTE_WORKDIR' && '$VIVADO_BIN' -mode batch -nojournal -nolog -source gen_xilinx_fp_ips_23.tcl -tclargs fpga_ip/vivado_ip_project fpga_ip/vivado_ip '$FPGA_PART' fpga_ip_modules.txt"
fi
ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" \
  "cd '$REMOTE_WORKDIR' && '$VIVADO_BIN' -mode batch -source qwen_generated_bitstream_23.tcl -log 'qwen_generated_${MODE}_${stamp}.log' -journal 'qwen_generated_${MODE}.jou' -tclargs '$MODE' '$CLOCK_PERIOD_NS' '$FPGA_PART'"

if [[ "$MODE" == "bitstream" ]]; then
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "test -s '$REMOTE_WORKDIR/vivado_qwen_generated_bitstream/qwen_generated_core.bit' && ls -lh '$REMOTE_WORKDIR/vivado_qwen_generated_bitstream/qwen_generated_core.bit'"
elif [[ "$MODE" == "power" ]]; then
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "test -s '$REMOTE_WORKDIR/vivado_qwen_generated_power/qwen_generated_impl_power.rpt' && ls -lh '$REMOTE_WORKDIR/vivado_qwen_generated_power/qwen_generated_impl_power.rpt'"
else
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "test -s '$REMOTE_WORKDIR/vivado_qwen_generated_synth/qwen_generated_synth.dcp' && ls -lh '$REMOTE_WORKDIR/vivado_qwen_generated_synth/qwen_generated_synth.dcp'"
fi

rm -rf "$LOCAL_OUT_DIR"
scp -qr -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$REMOTE_HOST:$REMOTE_WORKDIR/vivado_qwen_generated_${MODE}" "$RUN_DIR/"

if [[ "$MODE" == "bitstream" ]]; then
  test -s "$RUN_DIR/vivado_qwen_generated_bitstream/qwen_generated_core.bit"
elif [[ "$MODE" == "power" ]]; then
  test -s "$RUN_DIR/vivado_qwen_generated_power/qwen_generated_impl_power.rpt"
else
  test -s "$RUN_DIR/vivado_qwen_generated_synth/qwen_generated_synth.dcp"
fi
