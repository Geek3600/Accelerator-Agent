#!/usr/bin/env bash
set -euo pipefail

# Run on server 79. It creates a portable package that can open the app_shell_9p
# block design on another server with Vivado installed. The package is for GUI
# viewing/debugging of the BD, not for synthesis/implementation.

PROJECT_ROOT="${PROJECT_ROOT:-/home/hyyuan/workspace/v6.0_9p_cnn_2slr_4core_yolov8/v6.0_9p_cnn_v0825}"
PACKAGE_ROOT="${PACKAGE_ROOT:-/home/hyyuan/workspace/Qwen2-Accelerator/vivado_bd_viewer_app_shell_9p_20260622}"
TARBALL="${TARBALL:-${PACKAGE_ROOT}.tar.gz}"
PART="${PART:-xcvu9p_CIV-flgb2104-2-i}"

BD_REL="app_shell_9p.srcs/sources_1/bd/app_shell_9p"
CONSTR_REL="app_shell_9p.srcs/constrs_1/new"
GEN_BD_REL="app_shell_9p.gen/sources_1/bd/app_shell_9p"

copy_path() {
  local src="$1"
  local dst="$2"
  if [[ ! -e "${src}" ]]; then
    echo "ERROR: missing required path: ${src}" >&2
    exit 1
  fi
  mkdir -p "$(dirname "${dst}")"
  cp -a "${src}" "${dst}"
}

copy_optional_path() {
  local src="$1"
  local dst="$2"
  if [[ -e "${src}" ]]; then
    mkdir -p "$(dirname "${dst}")"
    cp -a "${src}" "${dst}"
  fi
}

if [[ ! -f "${PROJECT_ROOT}/app_shell_9p.xpr" ]]; then
  echo "ERROR: project not found: ${PROJECT_ROOT}/app_shell_9p.xpr" >&2
  exit 1
fi
if [[ ! -f "${PROJECT_ROOT}/${BD_REL}/app_shell_9p.bd" ]]; then
  echo "ERROR: BD not found: ${PROJECT_ROOT}/${BD_REL}/app_shell_9p.bd" >&2
  exit 1
fi

rm -rf "${PACKAGE_ROOT}"
mkdir -p "${PACKAGE_ROOT}"

copy_path "${PROJECT_ROOT}/app_shell_9p.xpr" "${PACKAGE_ROOT}/app_shell_9p.xpr"
copy_optional_path "${PROJECT_ROOT}/component.xml" "${PACKAGE_ROOT}/component.xml"

# BD source, BD UI, and all BD-local XCI files. This is the key portable state.
copy_path "${PROJECT_ROOT}/${BD_REL}" "${PACKAGE_ROOT}/${BD_REL}"

# Top-level constraints are small and useful for context when the GUI opens.
copy_optional_path "${PROJECT_ROOT}/${CONSTR_REL}/app_shell_9p.xdc" "${PACKAGE_ROOT}/${CONSTR_REL}/app_shell_9p.xdc"
copy_optional_path "${PROJECT_ROOT}/${CONSTR_REL}/opt_acc_core_resources.xdc" "${PACKAGE_ROOT}/${CONSTR_REL}/opt_acc_core_resources.xdc"

# Only the custom IP repos used by the current app_shell_9p.bd.
mkdir -p "${PACKAGE_ROOT}/ip_repo"
copy_path "${PROJECT_ROOT}/ip_repo/axi_chip2chip_0to3_lane" "${PACKAGE_ROOT}/ip_repo/axi_chip2chip_0to3_lane"
copy_path "${PROJECT_ROOT}/ip_repo/axi_combine_v1_0" "${PACKAGE_ROOT}/ip_repo/axi_combine_v1_0"
copy_path "${PROJECT_ROOT}/ip_repo/cnncore_sys_config_1.0" "${PACKAGE_ROOT}/ip_repo/cnncore_sys_config_1.0"

# opt_acc_core is a BD module-reference/custom IP instance in this project.
# There is no standalone ip_repo/opt_acc_core/component.xml in the source
# project, so keep the BD XCI plus its shared HDL products.
copy_path "${PROJECT_ROOT}/${GEN_BD_REL}/ipshared/3011" "${PACKAGE_ROOT}/${GEN_BD_REL}/ipshared/3011"
mkdir -p "${PACKAGE_ROOT}/${BD_REL}/ipshared"
cp -a "${PROJECT_ROOT}/${GEN_BD_REL}/ipshared/3011" "${PACKAGE_ROOT}/${BD_REL}/ipshared/3011"

copy_optional_path \
  "${PROJECT_ROOT}/${GEN_BD_REL}/ip/app_shell_9p_opt_acc_core_0_3/app_shell_9p_opt_acc_core_0_3.xml" \
  "${PACKAGE_ROOT}/${GEN_BD_REL}/ip/app_shell_9p_opt_acc_core_0_3/app_shell_9p_opt_acc_core_0_3.xml"
copy_optional_path \
  "${PROJECT_ROOT}/${GEN_BD_REL}/ip/app_shell_9p_opt_acc_core_0_3/sim/app_shell_9p_opt_acc_core_0_3.sv" \
  "${PACKAGE_ROOT}/${GEN_BD_REL}/ip/app_shell_9p_opt_acc_core_0_3/sim/app_shell_9p_opt_acc_core_0_3.sv"
copy_optional_path \
  "${PROJECT_ROOT}/${GEN_BD_REL}/ip/app_shell_9p_opt_acc_core_0_3/synth/app_shell_9p_opt_acc_core_0_3.sv" \
  "${PACKAGE_ROOT}/${GEN_BD_REL}/ip/app_shell_9p_opt_acc_core_0_3/synth/app_shell_9p_opt_acc_core_0_3.sv"
copy_optional_path \
  "${PROJECT_ROOT}/${GEN_BD_REL}/hdl/app_shell_9p_wrapper.v" \
  "${PACKAGE_ROOT}/${GEN_BD_REL}/hdl/app_shell_9p_wrapper.v"

cat > "${PACKAGE_ROOT}/open_app_shell_9p_bd.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Open the packaged app_shell_9p block design in Vivado GUI.
# Run from a terminal with DISPLAY set, for example MobaXterm with X11 enabled.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIVADO_BIN="${VIVADO_BIN:-vivado}"
PART="${PART:-xcvu9p_CIV-flgb2104-2-i}"
FOCUS_CELL="${1:-opt_acc_core_0}"
WORK_DIR="${ROOT_DIR}/.vivado_bd_viewer"
TCL_SCRIPT="${WORK_DIR}/open_bd.tcl"

if [[ "${VIVADO_BIN}" == "vivado" ]] && ! command -v vivado >/dev/null 2>&1; then
  if [[ -x /home/EDA/Xilinx/Vivado/2021.1/bin/vivado ]]; then
    VIVADO_BIN=/home/EDA/Xilinx/Vivado/2021.1/bin/vivado
  fi
fi

if [[ ! -x "${VIVADO_BIN}" && "${VIVADO_BIN}" != "vivado" ]]; then
  echo "ERROR: Vivado executable not found: ${VIVADO_BIN}" >&2
  exit 1
fi
if [[ -z "${DISPLAY:-}" ]]; then
  echo "ERROR: DISPLAY is empty. Enable X11 forwarding or run in a graphical terminal." >&2
  exit 2
fi

mkdir -p "${WORK_DIR}"
cat > "${TCL_SCRIPT}" <<'TCL'
set root_dir [file normalize [lindex $::argv 0]]
set part     [lindex $::argv 1]
set focus    [lindex $::argv 2]

set proj_dir [file join $root_dir ".vivado_bd_viewer" "project"]
set bd_file  [file join $root_dir "app_shell_9p.srcs" "sources_1" "bd" "app_shell_9p" "app_shell_9p.bd"]

puts "=== Open packaged app_shell_9p BD ==="
puts "root_dir=$root_dir"
puts "part=$part"
puts "bd_file=$bd_file"
puts "focus=$focus"

if {![file exists $bd_file]} {
  error "BD file not found: $bd_file"
}

create_project -force app_shell_9p_bd_viewer $proj_dir -part $part
set_property ip_repo_paths [list [file join $root_dir "ip_repo"]] [current_project]
update_ip_catalog

set opt_core_hdl [file join $root_dir "app_shell_9p.gen" "sources_1" "bd" "app_shell_9p" "ipshared" "3011" "opt_acc_core.sv"]
set top_hdl      [file join $root_dir "app_shell_9p.gen" "sources_1" "bd" "app_shell_9p" "ipshared" "3011" "Top_vivado.sv"]
foreach src [list $opt_core_hdl $top_hdl] {
  if {[file exists $src]} {
    add_files -norecurse $src
  }
}

set xdc1 [file join $root_dir "app_shell_9p.srcs" "constrs_1" "new" "app_shell_9p.xdc"]
set xdc2 [file join $root_dir "app_shell_9p.srcs" "constrs_1" "new" "opt_acc_core_resources.xdc"]
foreach xdc [list $xdc1 $xdc2] {
  if {[file exists $xdc]} {
    add_files -fileset constrs_1 -norecurse $xdc
  }
}

add_files -norecurse $bd_file
open_bd_design $bd_file
current_bd_instance /

set cell [get_bd_cells -quiet $focus]
if {[llength $cell] != 0} {
  if {[llength [info commands select_bd_objs]] != 0} {
    catch {select_bd_objs $cell}
  } elseif {[llength [info commands select_objects]] != 0} {
    catch {select_objects $cell}
  }
  puts "Opened BD and selected cell: $focus"
} else {
  puts "Opened BD. Focus cell not found: $focus"
}

puts "Vivado GUI is ready. This viewer script does not save or modify the packaged BD."
TCL

exec "${VIVADO_BIN}" -mode gui -source "${TCL_SCRIPT}" -tclargs "${ROOT_DIR}" "${PART}" "${FOCUS_CELL}"
EOF
chmod +x "${PACKAGE_ROOT}/open_app_shell_9p_bd.sh"

cat > "${PACKAGE_ROOT}/README.md" <<EOF
# app_shell_9p Vivado BD Viewer Package

This package contains the minimal source files needed to open and inspect the
app_shell_9p block design GUI on a server with Vivado installed.

It is for block-design viewing/debugging only. It does not include implementation
runs, routed DCPs, bitstreams, IP cache, or simulation/build logs.

## Run

\`\`\`bash
./open_app_shell_9p_bd.sh
\`\`\`

Optional focus cell:

\`\`\`bash
./open_app_shell_9p_bd.sh opt_acc_core_0
\`\`\`

Requirements:

- Vivado 2021.1 or compatible version with support for part \`${PART}\`
- GUI/X11 available: \`DISPLAY\` must be non-empty
- Custom IP repos are packaged under \`ip_repo/\`

If Vivado is not in PATH, set:

\`\`\`bash
export VIVADO_BIN=/path/to/Vivado/2021.1/bin/vivado
./open_app_shell_9p_bd.sh
\`\`\`
EOF

(cd "$(dirname "${PACKAGE_ROOT}")" && tar -czf "${TARBALL}" "$(basename "${PACKAGE_ROOT}")")

echo "PACKAGE_ROOT=${PACKAGE_ROOT}"
echo "TARBALL=${TARBALL}"
du -sh "${PACKAGE_ROOT}" "${TARBALL}"
sha256sum "${TARBALL}"
