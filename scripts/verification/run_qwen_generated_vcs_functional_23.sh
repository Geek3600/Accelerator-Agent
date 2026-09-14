#!/usr/bin/env bash
set -euo pipefail

RUN_DIR="${1:-/tmp/spatialacc_qwen_agent_run}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_WORKDIR="${REMOTE_WORKDIR:-/tmp/spatialacc_qwen_vcs_functional}"
REMOTE_VCS_HOME="${REMOTE_VCS_HOME:-}"
REMOTE_SIM_TIMEOUT_SEC="${REMOTE_SIM_TIMEOUT_SEC:-300}"
REMOTE_KNOWN_HOSTS="${REMOTE_KNOWN_HOSTS:-/tmp/codex_ssh_known_hosts}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SV_DIR="$RUN_DIR/generated/chisel"
AXI_WRAPPER="$ROOT_DIR/verification/rtl/QwenAxiBoardSystemTop.sv"
TB="$ROOT_DIR/testbench/vcs/qwen_axi_board_tb.sv"
REAL_DIR="$RUN_DIR/verification/qwen_real_weights"
INPUT_MEMH="$REAL_DIR/input_activation.u32.memh"
WEIGHT_MEMH="$REAL_DIR/weight_prefetch.u32.memh"
INPUT_MANIFEST="$REAL_DIR/input_manifest.json"
WEIGHT_MANIFEST="$REAL_DIR/packed_weight_manifest.json"
LOCAL_VCS_DIR="$RUN_DIR/verification/vcs"

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
  "$TB" \
  "$INPUT_MEMH" \
  "$WEIGHT_MEMH" \
  "$INPUT_MANIFEST" \
  "$WEIGHT_MANIFEST"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required VCS functional input: $f" >&2
    exit 1
  fi
done

mkdir -p "$LOCAL_VCS_DIR"

SSH_OPTS=(
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}"
  -p "${REMOTE_PORT}"
)

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "mkdir -p '$REMOTE_WORKDIR' && rm -f '$REMOTE_WORKDIR'/*.sv '$REMOTE_WORKDIR'/*.memh '$REMOTE_WORKDIR'/*.json '$REMOTE_WORKDIR'/simv '$REMOTE_WORKDIR'/vcs.log '$REMOTE_WORKDIR'/sim.log"
scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$SV_DIR"/*.sv "$AXI_WRAPPER" "$TB" "$INPUT_MEMH" "$WEIGHT_MEMH" "$INPUT_MANIFEST" "$WEIGHT_MANIFEST" "$REMOTE_HOST:$REMOTE_WORKDIR/"

set +e
ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" "
  cd '$REMOTE_WORKDIR' &&
  if [[ -n '$REMOTE_VCS_HOME' ]]; then export PATH='$REMOTE_VCS_HOME/bin:/usr/bin:/bin':\"\$PATH\" VCS_HOME='$REMOTE_VCS_HOME'; fi &&
  export VCS_TARGET_ARCH=linux64 LANG=C LC_ALL=C &&
  vcs -full64 -sverilog -timescale=1ns/1ps +v2k -debug_access+all -top qwen_axi_board_tb -o simv *.sv > vcs.log 2>&1 &&
  set -o pipefail &&
  timeout '$REMOTE_SIM_TIMEOUT_SEC' ./simv \
    +INPUT_MEMH=input_activation.u32.memh \
    +WEIGHT_MEMH=weight_prefetch.u32.memh \
    +INPUT_MANIFEST=input_manifest.json \
    +WEIGHT_MANIFEST=packed_weight_manifest.json 2>&1 | tee sim.log &&
  grep -q 'qwen_axi_board_tb PASS real functional ddr path' sim.log
"
REMOTE_STATUS=$?
set -e

scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$REMOTE_HOST:$REMOTE_WORKDIR/vcs.log" "$LOCAL_VCS_DIR/case_functional_compile.log" || true
scp -q -P "$REMOTE_PORT" \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile="${REMOTE_KNOWN_HOSTS}" \
  "$REMOTE_HOST:$REMOTE_WORKDIR/sim.log" "$LOCAL_VCS_DIR/case_functional_sim.log" || true

exit "$REMOTE_STATUS"
