"""Small execution-layer handoff for generated Vivado IP.

The framework keeps the IP contract in Stage 5, but materializes the actual
Vivado-generated simulation models only when a cold VCS compile is launched.
This module deliberately owns no design identity or LLM evidence; it only
returns a shell fragment and staged files for the real-tool execution layer.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import shutil
from pathlib import Path
from typing import Any

from accagent.framework.fpga_ip_contract import check_fpga_ip_simulation_closure


FPGA_IP_RUNTIME_PROTOCOL_VERSION = "vivado_export_file_info_v1"
_RUNTIME_DIR = Path(__file__).resolve().parent
_EXPORT_HELPER = _RUNTIME_DIR / "fpga_ip_vcs_export.tcl"
_PLAN_HELPER = _RUNTIME_DIR / "fpga_ip_vcs_plan.py"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fpga_ip_runtime_protocol_identity() -> dict[str, Any]:
    """Return the versioned static helpers that define physical VCS closure."""

    helpers = {
        "fpga_ip/export_vcs_file_info.tcl": _EXPORT_HELPER,
        "fpga_ip/build_vcs_library_plan.py": _PLAN_HELPER,
    }
    missing = [str(path) for path in helpers.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("FPGA IP runtime helper is missing: " + ", ".join(missing))
    files = {name: _sha256_file(path) for name, path in helpers.items()}
    payload = {
        "protocol_version": FPGA_IP_RUNTIME_PROTOCOL_VERSION,
        "files": files,
    }
    payload["sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def _tool(tool_profile: dict[str, Any], name: str) -> dict[str, Any]:
    for row in tool_profile.get("tools", []):
        if isinstance(row, dict) and str(row.get("name") or "").lower() == name:
            return row
    return {}


def _closure_artifact_path(value: Any, closure_path: Path) -> Path:
    path = Path(str(value or "")).expanduser()
    return path if path.is_absolute() else closure_path.parent / path


def stage_fpga_ip_runtime(
    run_dir: Path,
    stage_dir: Path,
    tool_profile: dict[str, Any],
    *,
    compiler_workdir: str = "vcs_work",
    compiler_workdirs: list[str] | None = None,
    expected_default_library: str = "",
) -> dict[str, Any]:
    """Stage the IP generator and return the cold-compile provisioning command.

    Vivado runs on the configured remote host, so the command intentionally
    references the remote Vivado installation and writes all generated files
    inside the remote VCS work directory.  The generated file list is consumed
    by the generated VCS command from ``compiler_workdir``; no behavioral
    fallback is allowed.
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
    tcl_source = _closure_artifact_path(closure["ip_generation_tcl"], closure_path)
    if not tcl_source.is_file():
        raise FileNotFoundError(f"Vivado IP generation TCL is missing: {tcl_source}")

    vivado = _tool(tool_profile, "vivado")
    executable = str(vivado.get("executable") or "")
    if not executable:
        raise ValueError("tool_profile does not provide a Vivado executable")

    runtime_dir = stage_dir / "fpga_ip"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    staged_tcl = runtime_dir / "gen_xilinx_fp_ips.tcl"
    module_manifest_source = _closure_artifact_path(
        closure["ip_module_manifest"], closure_path
    )
    if not module_manifest_source.is_file():
        raise FileNotFoundError(f"Vivado IP module manifest is missing: {module_manifest_source}")
    staged_module_manifest = runtime_dir / "fpga_ip_modules.txt"
    shutil.copy2(tcl_source, staged_tcl)
    shutil.copy2(module_manifest_source, staged_module_manifest)
    shutil.copy2(closure_path, runtime_dir / "fpga_ip_simulation_closure.json")
    protocol = fpga_ip_runtime_protocol_identity()
    staged_export_helper = runtime_dir / "export_vcs_file_info.tcl"
    staged_plan_helper = runtime_dir / "build_vcs_library_plan.py"
    shutil.copy2(_EXPORT_HELPER, staged_export_helper)
    shutil.copy2(_PLAN_HELPER, staged_plan_helper)

    ip_project = "fpga_ip/vivado_ip_project"
    ip_output = "fpga_ip/vivado_ip"
    module_manifest = "fpga_ip/fpga_ip_modules.txt"
    vivado_bin = shlex.quote(executable)
    tcl = shlex.quote("fpga_ip/gen_xilinx_fp_ips.tcl")
    project = shlex.quote(ip_project)
    output = shlex.quote(ip_output)
    module_manifest_q = shlex.quote(module_manifest)
    fpga_part_q = shlex.quote(str(closure["fpga_part"]))
    compiler_workdir = compiler_workdir.strip() or "."
    if (
        compiler_workdir.startswith("/")
        or any(part == ".." for part in compiler_workdir.split("/"))
    ):
        raise ValueError("compiler_workdir must be a safe relative path")
    workdirs = compiler_workdirs if compiler_workdirs is not None else [compiler_workdir]
    # compile_ip_models.sh executes from the staged root before any board-plan
    # command changes cwd, so the root library map is always required.
    workdirs = [".", *workdirs]
    normalized_workdirs: list[str] = []
    for value in workdirs:
        candidate = str(value).strip() or "."
        if candidate.startswith("/") or any(part == ".." for part in candidate.split("/")):
            raise ValueError("compiler workdirs must be safe relative paths")
        if candidate not in normalized_workdirs:
            normalized_workdirs.append(candidate)
    if not normalized_workdirs:
        normalized_workdirs = ["."]
    if expected_default_library and not expected_default_library.replace("_", "a").isalnum():
        raise ValueError("expected_default_library must be an HDL logical-library name")
    # Resolve this once on the remote host.  A tool profile may name Vivado by
    # its absolute path or via PATH, so deriving the installation root in
    # Python would make the execution handoff needlessly host-specific.
    vivado_bin_assignment = f"VIVADO_BIN={shlex.quote(executable)};"
    vivado_root_assignment = (
        'VIVADO_ROOT="$(cd \"$(dirname \"$(command -v \"$VIVADO_BIN\")\")/.." '
        '&& pwd)";'
    )
    export_tcl = shlex.quote("fpga_ip/export_vcs_file_info.tcl")
    export_root = "fpga_ip/vivado_export"
    plan_helper = shlex.quote("fpga_ip/build_vcs_library_plan.py")
    plan_args = [
        "python3",
        plan_helper,
        "--module-manifest",
        module_manifest_q,
        "--ip-root",
        shlex.quote(ip_output),
        "--export-root",
        shlex.quote(export_root),
        "--library-root",
        shlex.quote("vcs_lib"),
        *(
            value
            for workdir in normalized_workdirs
            for value in ("--compiler-workdir", shlex.quote(workdir))
        ),
    ]
    if expected_default_library:
        plan_args.extend(["--expected-default-library", shlex.quote(expected_default_library)])
    # Vivado owns both the source/language/library manifest and the generated
    # IP models.  The plan helper only materializes that official order for
    # VCS-MX; it never substitutes a behavioral implementation.
    command = " ".join(
        [
            "set -euo pipefail;",
            vivado_bin_assignment,
            vivado_root_assignment,
            f"rm -rf -- {shlex.quote('fpga_ip/vivado_ip_project')} {shlex.quote('fpga_ip/vivado_ip')} {shlex.quote(export_root)};",
            f'"$VIVADO_BIN" -mode batch -nojournal -nolog -source {tcl} -tclargs {project} {output} {fpga_part_q} {module_manifest_q};',
            f'"$VIVADO_BIN" -mode batch -nojournal -nolog -source {export_tcl} -tclargs {shlex.quote(ip_output)} {shlex.quote(export_root)} {fpga_part_q} {module_manifest_q};',
            " ".join(plan_args) + ";",
            "test -x fpga_ip/compile_ip_models.sh;",
            "test -s fpga_ip/vcs_runtime.env;",
            "test -s fpga_ip/vcs_elab_args.txt;",
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
        "remote_vivado_export_dir": export_root,
        "remote_vcs_plan": "fpga_ip/vcs_library_plan.json",
        "remote_vcs_compile_script": "fpga_ip/compile_ip_models.sh",
        "remote_vcs_runtime_env": "fpga_ip/vcs_runtime.env",
        "remote_vcs_elab_args": "fpga_ip/vcs_elab_args.txt",
        "compiler_workdir": compiler_workdir,
        "compiler_workdirs": normalized_workdirs,
        "expected_default_library": expected_default_library,
        "vivado_executable": executable,
        "runtime_protocol": protocol,
        "provision_command": command,
        "compile_command": "bash fpga_ip/compile_ip_models.sh",
        "required_modules": list(closure.get("required_ip_modules", [])),
    }
