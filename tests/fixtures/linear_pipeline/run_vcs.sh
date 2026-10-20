#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C LANG=C

ip_root=$(realpath "$1")
rtl_root=$(realpath "$2")
simlib_setup=$(realpath "$3")
ip_models=$(realpath "$4")
if [[ -n "${SPATIALACC_VCS_HOME:-}" ]]; then
  export VCS_HOME="$SPATIALACC_VCS_HOME"
  export VCS_TARGET_ARCH=linux64
  export PATH="$VCS_HOME/bin:$PATH"
fi
source "$ip_root/fpga_ip/vcs_runtime.env"
mapfile -t libraries < "$ip_root/fpga_ip/vcs_elab_args.txt"

# Cases have separate work libraries and executables. Bound remote parallelism
# without multiplying the number of local JVMs or changing any compile gate.
case_jobs=${SPATIALACC_VCS_CASE_JOBS:-3}
[[ "$case_jobs" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid SPATIALACC_VCS_CASE_JOBS" >&2; exit 2; }
case_pids=()
case_pid_count=0
wait_case_batch() {
  local failed=0 pid
  # Bash versions used by remote VCS hosts may treat expansion of an empty
  # array as an unset variable under set -u. Callers pass arguments only when
  # the scalar count proves that the batch is non-empty.
  if (( $# == 0 )); then
    return 0
  fi
  for pid in "$@"; do
    wait "$pid" || failed=1
  done
  case_pids=()
  case_pid_count=0
  return "$failed"
}

for case_dir in "$rtl_root"/*; do
  [[ -f "$case_dir/tb.sv" ]] || continue
  (
    cd "$case_dir"
    mkdir -p work
    printf 'WORK > DEFAULT\nDEFAULT : ./work\n' > synopsys_sim.setup
    if [[ -f "$ip_root/vcs_work/synopsys_sim.setup" ]]; then
      sed "s|\.\./vcs_lib/|$ip_root/vcs_lib/|g" "$ip_root/vcs_work/synopsys_sim.setup" >> synopsys_sim.setup
    fi
    if [[ -n "${SYNOPSYS_DW_FPGA_LIB_SETUP:-}" ]]; then
      cat "$simlib_setup" >> synopsys_sim.setup
    else
      # The supplied board setup may reference an optional site-local
      # DesignWare include that is absent on the remote VCS host. Remove only
      # that unresolved include; keep the rest of the real setup intact.
      sed '/^[[:space:]]*OTHERS[[:space:]]*=[[:space:]]*\$SYNOPSYS_DW_FPGA_LIB_SETUP[[:space:]]*$/d' \
        "$simlib_setup" >> synopsys_sim.setup
    fi
    # Use the explicit per-case setup without importing the login user's libraries.
    # The W4A8 hierarchy must compile without floating-point IP sources.
    compile_only_top=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("compile_only_top", ""))' "$case_dir/params.json")
    integer_mode=$(python3 -c 'import json,sys; print("1" if json.load(open(sys.argv[1])).get("integer_mode") else "0")' "$case_dir/params.json")
    if [[ "$integer_mode" == "1" ]]; then
      if grep -E -q '^[[:space:]]*fp_(add|sub|mul|div|sqrt|cmp|i2f|f2i)_sp_[0-9]+[[:space:]]' "$case_dir"/*.sv; then
        echo "W4A8 RTL unexpectedly instantiates a floating-point IP" >&2
        exit 1
      fi
      SYNOPSYS_SIM_SETUP="$case_dir/synopsys_sim.setup" vlogan -work WORK -full64 -sverilog -timescale=1ns/1ps +incdir+. ./*.sv > compile.log 2>&1
    else
      SYNOPSYS_SIM_SETUP="$case_dir/synopsys_sim.setup" vlogan -work WORK -full64 -sverilog -timescale=1ns/1ps +incdir+. "$ip_models"/fp_add_sp_12/sim/fp_add_sp_12.v "$ip_models"/fp_mul_sp_9/sim/fp_mul_sp_9.v ./*.sv > compile.log 2>&1
    fi
    SYNOPSYS_SIM_SETUP="$case_dir/synopsys_sim.setup" vcs -full64 -t ps -licqueue WORK.tb "${libraries[@]}" "$FPGA_IP_GLBL_UNIT" -o simv > elaborate.log 2>&1
    test -x simv
    if [[ "${SPATIALACC_COMPILE_ONLY:-0}" == "1" ]]; then
      # This gate proves VCS compilation, elaboration, and linking only. Do not
      # write a simulation PASS record or launch the simulation executable.
      printf 'PASS VCS compile/elaboration/link; simulation not run (compile-only gate)\n' > compile_only.log
      printf 'simulation_not_run=1\n' >> compile_only.log
      cp compile_only.log simulation.log
    else
      timeout 120 ./simv > simulation.log 2>&1
      grep '^PASS ' simulation.log
    fi
  ) &
  case_pids+=("$!")
  case_pid_count=$((case_pid_count + 1))
  if (( case_pid_count >= case_jobs )); then
    wait_case_batch "${case_pids[@]}" || exit 1
  fi
done
if (( case_pid_count > 0 )); then
  wait_case_batch "${case_pids[@]}"
fi
