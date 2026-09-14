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
LOCAL_OUT_DIR="$RUN_DIR/vivado_qwen_generated_${MODE}"

if [[ -z "$REMOTE_HOST" ]]; then
  echo "REMOTE_HOST must be set from the Stage 0 tool profile or user environment" >&2
  exit 2
fi
if [[ -z "$VIVADO_BIN" ]]; then
  echo "VIVADO_BIN must be set from the Stage 0 tool profile or user environment" >&2
  exit 2
fi

case "$MODE" in
  synth|bitstream) ;;
  *)
    echo "Usage: $0 [synth|bitstream] [run_dir]" >&2
    exit 2
    ;;
esac

if [[ ! -f "$LOCAL_TOP" ]]; then
  echo "Missing generated Qwen top SystemVerilog: $LOCAL_TOP" >&2
  exit 1
fi
if [[ ! -f "$LOCAL_FPGA_TOP" ]]; then
  echo "Missing generated Qwen FPGA AXI/DDR top SystemVerilog: $LOCAL_FPGA_TOP" >&2
  exit 1
fi
if [[ ! -f "$LOCAL_SV_DIR/LlamaStyleBlock.sv" ]]; then
  echo "Missing generated Qwen core SystemVerilog: $LOCAL_SV_DIR/LlamaStyleBlock.sv" >&2
  exit 1
fi
if [[ ! -f "$LOCAL_TCL" ]]; then
  echo "Missing Vivado Tcl: $LOCAL_TCL" >&2
  exit 1
fi

SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}"
  -p "${REMOTE_PORT}"
)

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "mkdir -p '$REMOTE_WORKDIR' && rm -f '$REMOTE_WORKDIR'/*.sv"
scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$LOCAL_SV_DIR"/*.sv "$REMOTE_HOST:$REMOTE_WORKDIR/"
scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$LOCAL_TCL" "$REMOTE_HOST:$REMOTE_WORKDIR/qwen_generated_bitstream_23.tcl"

stamp="$(date +%Y%m%d_%H%M%S)"
ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" \
  "cd '$REMOTE_WORKDIR' && '$VIVADO_BIN' -mode batch -source qwen_generated_bitstream_23.tcl -log 'qwen_generated_${MODE}_${stamp}.log' -journal 'qwen_generated_${MODE}.jou' -tclargs '$MODE' '$CLOCK_PERIOD_NS'"

if [[ "$MODE" == "bitstream" ]]; then
  ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "test -s '$REMOTE_WORKDIR/vivado_qwen_generated_bitstream/qwen_generated_core.bit' && ls -lh '$REMOTE_WORKDIR/vivado_qwen_generated_bitstream/qwen_generated_core.bit'"
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
else
  test -s "$RUN_DIR/vivado_qwen_generated_synth/qwen_generated_synth.dcp"
fi
