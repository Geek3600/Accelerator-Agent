#!/usr/bin/env bash
set -euo pipefail

# Run this script in a MobaXterm SSH session to server 79 with X11 forwarding enabled.
# It opens the existing Vivado project and displays the app_shell_9p block design.

VIVADO_BIN="${VIVADO_BIN:-/home/EDA/Xilinx/Vivado/2021.1/bin/vivado}"
PROJECT_XPR="${1:-/home/hyyuan/workspace/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.xpr}"
BD_PATH="${2:-/home/hyyuan/workspace/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825/app_shell_9p.srcs/sources_1/bd/app_shell_9p/app_shell_9p.bd}"
FOCUS_CELL="${3:-opt_acc_core_0}"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<EOF
Usage:
  $0 [project_xpr] [bd_path] [focus_cell]

Default project:
  ${PROJECT_XPR}

Default block design:
  ${BD_PATH}

Default focus cell:
  ${FOCUS_CELL}
EOF
  exit 0
fi

if [[ ! -x "${VIVADO_BIN}" ]]; then
  echo "ERROR: Vivado executable not found: ${VIVADO_BIN}" >&2
  exit 1
fi
if [[ ! -f "${PROJECT_XPR}" ]]; then
  echo "ERROR: Vivado project not found: ${PROJECT_XPR}" >&2
  exit 1
fi
if [[ ! -f "${BD_PATH}" ]]; then
  echo "ERROR: Block design file not found: ${BD_PATH}" >&2
  exit 1
fi
if [[ -z "${DISPLAY:-}" ]]; then
  cat >&2 <<'EOF'
ERROR: DISPLAY is empty, so Vivado GUI cannot be shown.

In MobaXterm:
  1. Enable X11 forwarding for the SSH session.
  2. Reconnect to server 79.
  3. Check that `echo $DISPLAY` is non-empty.
  4. Run this script again.
EOF
  exit 2
fi

TMP_DIR="$(mktemp -d /tmp/open_vivado_bd_79.XXXXXX)"
TCL_SCRIPT="${TMP_DIR}/open_bd.tcl"
trap 'rm -rf "${TMP_DIR}"' EXIT

cat > "${TCL_SCRIPT}" <<'TCL'
proc get_arg_or_default {idx default_value} {
  if {[llength $::argv] > $idx} {
    return [lindex $::argv $idx]
  }
  return $default_value
}

set project_xpr [get_arg_or_default 0 ""]
set bd_path     [get_arg_or_default 1 ""]
set focus_cell  [get_arg_or_default 2 "opt_acc_core_0"]

puts "=== Open Vivado Block Design ==="
puts "project_xpr=$project_xpr"
puts "bd_path=$bd_path"
puts "focus_cell=$focus_cell"

if {![file exists $project_xpr]} {
  error "Vivado project not found: $project_xpr"
}
if {![file exists $bd_path]} {
  error "Block design file not found: $bd_path"
}

open_project $project_xpr

set bd_file [get_files -quiet $bd_path]
if {[llength $bd_file] == 0} {
  set bd_file [get_files -quiet */app_shell_9p.bd]
}
if {[llength $bd_file] == 0} {
  error "Unable to find app_shell_9p.bd in opened project"
}

open_bd_design [lindex $bd_file 0]
current_bd_instance /

set cell [get_bd_cells -quiet $focus_cell]
if {[llength $cell] != 0} {
  if {[llength [info commands select_bd_objs]] != 0} {
    catch {select_bd_objs $cell}
  } elseif {[llength [info commands select_objects]] != 0} {
    catch {select_objects $cell}
  }
  puts "Opened block design and selected cell: $focus_cell"
} else {
  puts "Opened block design. Focus cell not found: $focus_cell"
}

puts "Vivado GUI is open. This script intentionally does not save or modify the project."
TCL

echo "Launching Vivado GUI..."
echo "Project: ${PROJECT_XPR}"
echo "BD:      ${BD_PATH}"
echo "Focus:   ${FOCUS_CELL}"

"${VIVADO_BIN}" -mode gui -source "${TCL_SCRIPT}" -tclargs "${PROJECT_XPR}" "${BD_PATH}" "${FOCUS_CELL}"
