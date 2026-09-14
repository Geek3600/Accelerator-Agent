#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="${1:-/tmp/spatialacc_qwen_agent_run}"
VERILATOR_BIN="${VERILATOR_BIN:-verilator}"
SIM_TIMEOUT_SEC="${SIM_TIMEOUT_SEC:-120}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SV_DIR="$RUN_DIR/generated/chisel"
AXI_WRAPPER="$ROOT_DIR/verification/rtl/QwenAxiBoardSystemTop.sv"
TB="$ROOT_DIR/testbench/vcs/qwen_axi_board_tb.sv"

for f in \
  "$SV_DIR/GeneratedAcceleratorTop.sv" \
  "$SV_DIR/GeneratedAxiDdrTop.sv" \
  "$SV_DIR/QwenMultiLayerSystemTop.sv" \
  "$SV_DIR/LlamaStyleBlock.sv" \
  "$AXI_WRAPPER" \
  "$TB"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required Verilator smoke input: $f" >&2
    exit 1
  fi
done

cd "$SV_DIR"
"$VERILATOR_BIN" \
  -Wno-fatal \
  -Wno-TIMESCALEMOD \
  --timing \
  --binary \
  -j "${VERILATOR_BUILD_JOBS:-4}" \
  --top-module qwen_axi_board_tb \
  -I"$SV_DIR" \
  "$SV_DIR"/*.sv \
  "$AXI_WRAPPER" \
  "$TB"

timeout "$SIM_TIMEOUT_SEC" "$SV_DIR/obj_dir/Vqwen_axi_board_tb" 2>&1 | tee "$SV_DIR/obj_dir/qwen_axi_board_tb.log"
grep -q "qwen_axi_board_tb PASS" "$SV_DIR/obj_dir/qwen_axi_board_tb.log"
