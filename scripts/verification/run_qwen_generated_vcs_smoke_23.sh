#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="${1:-/tmp/spatialacc_qwen_agent_run}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/tmp/spatialacc_qwen_vcs_smoke}"
REMOTE_VCS_HOME="${REMOTE_VCS_HOME:-}"
REMOTE_SIM_TIMEOUT_SEC="${REMOTE_SIM_TIMEOUT_SEC:-120}"
REMOTE_KNOWN_HOSTS="${REMOTE_KNOWN_HOSTS:-/tmp/codex_ssh_known_hosts}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SV_DIR="$RUN_DIR/generated/chisel"
AXI_WRAPPER="$ROOT_DIR/verification/rtl/QwenAxiBoardSystemTop.sv"
TB="$ROOT_DIR/testbench/vcs/qwen_axi_board_tb.sv"

if [[ -z "$REMOTE_HOST" ]]; then
  echo "REMOTE_HOST must be set from the Stage 0 tool profile or user environment" >&2
  exit 2
fi

for f in \
  "$SV_DIR/GeneratedAcceleratorTop.sv" \
  "$SV_DIR/GeneratedAxiDdrTop.sv" \
  "$SV_DIR/QwenMultiLayerSystemTop.sv" \
  "$SV_DIR/LlamaStyleBlock.sv" \
  "$AXI_WRAPPER" \
  "$TB"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required VCS smoke input: $f" >&2
    exit 1
  fi
done

SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}"
  -p "${REMOTE_PORT}"
)

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "mkdir -p '$REMOTE_WORKDIR' && rm -f '$REMOTE_WORKDIR'/*.sv '$REMOTE_WORKDIR'/simv '$REMOTE_WORKDIR'/vcs.log"
scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$SV_DIR"/*.sv "$AXI_WRAPPER" "$TB" "$REMOTE_HOST:$REMOTE_WORKDIR/"

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "
  cd '$REMOTE_WORKDIR' &&
  if [[ -n '$REMOTE_VCS_HOME' ]]; then export PATH='$REMOTE_VCS_HOME/bin:/usr/bin:/bin':\"\$PATH\" VCS_HOME='$REMOTE_VCS_HOME'; fi &&
  export VCS_TARGET_ARCH=linux64 LANG=C LC_ALL=C &&
  vcs -full64 -sverilog -timescale=1ns/1ps +v2k -debug_access+all -top qwen_axi_board_tb -o simv *.sv > vcs.log 2>&1 &&
  set -o pipefail &&
  timeout '$REMOTE_SIM_TIMEOUT_SEC' ./simv 2>&1 | tee sim.log &&
  grep -q 'qwen_axi_board_tb PASS' sim.log
"
