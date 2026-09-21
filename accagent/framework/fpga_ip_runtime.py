"""Small execution-layer handoff for generated Vivado IP.

The framework keeps the IP contract in Stage 5, but materializes the actual
Vivado-generated simulation models only when a cold VCS compile is launched.
This module deliberately owns no design identity or LLM evidence; it only
returns a shell fragment and staged files for the real-tool execution layer.
"""

from __future__ import annotations

import json
import shlex
import shutil
from pathlib import Path
from typing import Any

from accagent.framework.fpga_ip_contract import check_fpga_ip_simulation_closure


def _tool(tool_profile: dict[str, Any], name: str) -> dict[str, Any]:
    for row in tool_profile.get("tools", []):
        if isinstance(row, dict) and str(row.get("name") or "").lower() == name:
            return row
    return {}


def stage_fpga_ip_runtime(
    run_dir: Path,
    stage_dir: Path,
    tool_profile: dict[str, Any],
) -> dict[str, Any]:
    """Stage the IP generator and return the cold-compile provisioning command.

    Vivado runs on the configured remote host, so the command intentionally
    references the remote Vivado installation and writes all generated files
    inside the remote VCS work directory.  The generated file list is consumed
    by the generated vlogan command; no behavioral fallback is allowed.
    """

    closure_path = (
        run_dir
        / "generated"
        / "chisel"
        / "simulation"
        / "fpga_ip_simulation_closure.json"
    )
    closure_check = check_fpga_ip_simulation_closure(closure_path)
    if closure_check.get("status") != "pass":
        errors = [str(value) for value in closure_check.get("errors", []) if str(value)]
        raise ValueError("FPGA IP simulation closure is invalid: " + "; ".join(errors))
    closure = closure_check["closure"]
    tcl_source = Path(str(closure["ip_generation_tcl"])).expanduser()
    if not tcl_source.is_file():
        raise FileNotFoundError(f"Vivado IP generation TCL is missing: {tcl_source}")

    vivado = _tool(tool_profile, "vivado")
    executable = str(vivado.get("executable") or "")
    if not executable:
        raise ValueError("tool_profile does not provide a Vivado executable")

    runtime_dir = stage_dir / "fpga_ip"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    staged_tcl = runtime_dir / "gen_xilinx_fp_ips.tcl"
    module_manifest_source = Path(str(closure["ip_module_manifest"])).expanduser()
    if not module_manifest_source.is_file():
        raise FileNotFoundError(f"Vivado IP module manifest is missing: {module_manifest_source}")
    staged_module_manifest = runtime_dir / "fpga_ip_modules.txt"
    shutil.copy2(tcl_source, staged_tcl)
    shutil.copy2(module_manifest_source, staged_module_manifest)
    shutil.copy2(closure_path, runtime_dir / "fpga_ip_simulation_closure.json")

    ip_project = "fpga_ip/vivado_ip_project"
    ip_output = "fpga_ip/vivado_ip"
    filelist = "fpga_ip/vcs_sim_sources.f"
    module_manifest = "fpga_ip/fpga_ip_modules.txt"
    vivado_bin = shlex.quote(executable)
    tcl = shlex.quote("fpga_ip/gen_xilinx_fp_ips.tcl")
    project = shlex.quote(ip_project)
    output = shlex.quote(ip_output)
    filelist_q = shlex.quote(filelist)
    module_manifest_q = shlex.quote(module_manifest)
    fpga_part_q = shlex.quote(str(closure["fpga_part"]))
    # Resolve this once on the remote host.  A tool profile may name Vivado by
    # its absolute path or via PATH, so deriving the installation root in
    # Python would make the execution handoff needlessly host-specific.
    vivado_bin_assignment = f"VIVADO_BIN={shlex.quote(executable)};"
    vivado_root_assignment = (
        'VIVADO_ROOT="$(cd \"$(dirname \"$(command -v \"$VIVADO_BIN\")\")/.." '
        '&& pwd)";'
    )
    # Keep the generated IP's own rfs implementation and sim wrapper together;
    # XPM and glbl come from the exact Vivado installation used to generate it.
    command = " ".join(
        [
            "set -euo pipefail;",
            vivado_bin_assignment,
            vivado_root_assignment,
            f"rm -rf -- {shlex.quote('fpga_ip/vivado_ip_project')} {shlex.quote('fpga_ip/vivado_ip')} {filelist_q};",
            f'"$VIVADO_BIN" -mode batch -nojournal -nolog -source {tcl} -tclargs {project} {output} {fpga_part_q} {module_manifest_q};',
            "{",
            # The list is consumed from vcs_work, while the generated IP lives
            # beside it under stage_dir/fpga_ip.  Keep generated RTL relative
            # to that real compiler cwd; Vivado installation files stay
            # absolute and therefore resolve independently of the workdir.
            f"find {shlex.quote(ip_output)} -type f -path '*/hdl/*_rfs.v' -print | sort | head -n 1 | sed 's#^#../#';",
            f"find {shlex.quote(ip_output)} -type f -path '*/sim/*.v' -print | sort | sed 's#^#../#';",
            'printf "%s\\n" "$VIVADO_ROOT/data/ip/xpm/xpm_cdc/hdl/xpm_cdc.sv" "$VIVADO_ROOT/data/ip/xpm/xpm_fifo/hdl/xpm_fifo.sv" "$VIVADO_ROOT/data/ip/xpm/xpm_memory/hdl/xpm_memory.sv" "$VIVADO_ROOT/data/verilog/src/glbl.v";',
            'printf "%s\\n" "-y" "$VIVADO_ROOT/data/verilog/src/unisims" "+libext+.v";',
            f"}} > {filelist_q};",
            f"test -s {filelist_q};",
        ]
    )
    return {
        "status": "ready",
        "closure_path": str(closure_path),
        "staged_tcl": str(staged_tcl),
        "staged_module_manifest": str(staged_module_manifest),
        "runtime_dir": str(runtime_dir),
        "remote_ip_output_dir": ip_output,
        "remote_ip_project_dir": ip_project,
        "remote_vcs_filelist": filelist,
        "vivado_executable": executable,
        "provision_command": command,
        "required_modules": list(closure.get("required_ip_modules", [])),
    }


def ip_vcs_filelist_argument() -> str:
    """Return the stable path used from the framework VCS command cwd."""

    return "-f ../fpga_ip/vcs_sim_sources.f"
