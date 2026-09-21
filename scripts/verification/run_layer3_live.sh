#!/usr/bin/env bash
set -euo pipefail

# One stable owner for the Layer-3 observe -> repair -> real-board-VCS loop.
# Historical artifacts stay under the run directory, but live control always
# uses this fixed tmux session, log, SACG state, and report locations.
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
run_dir="$repo_root/accagent/runs/spatialacc_qwen_agent_fast_run"
session_name="accagent_layer3_live"
state_path="$run_dir/repair_execution/sacg_state.json"
log_path="$run_dir/repair_execution/layer3_live.log"

if tmux has-session -t "$session_name" 2>/dev/null; then
  printf 'Layer-3 controller is already running in tmux session %s\n' \
    "$session_name"
  exit 0
fi

mkdir -p "$(dirname "$log_path")"
tmux new-session -d -s "$session_name" \
  "cd '$repo_root' && exec python3 -m accagent.framework.stage_repair_execute --sacg-state '$state_path' --execute-reruns --include-remote --timeout-sec 0 --loop-until-pass --max-loop-iters 0 >> '$log_path' 2>&1"

printf 'Started Layer-3 controller in tmux session %s\n' "$session_name"
