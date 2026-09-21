#!/usr/bin/env python3
"""Run the current case through the exact board app-shell Vivado flow.

This is a thin case-adapter entrypoint.  It resolves only current-run
artifacts, then delegates the actual remote project-copy/OOC/implementation
work to :mod:`app_shell_runtime_vivado`.  Keeping this mapping here prevents
model-family scripts from selecting an unrelated standalone synthesis flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.synthesis.app_shell_runtime_vivado import main as app_shell_main


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def first_text(*values: Any) -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def compute_slot_wrapper(run_dir: Path, contract: dict[str, Any]) -> Path:
    target = contract.get("integration_target", {})
    abi = contract.get("compute_slot_abi", {})
    if not isinstance(target, dict):
        target = {}
    if not isinstance(abi, dict):
        abi = {}
    module = first_text(
        target.get("replacement_module_identity"),
        target.get("ip_name"),
        abi.get("replacement_module_identity"),
        abi.get("slot_module"),
    )
    if not module:
        raise RuntimeError("app-shell contract has no current compute-slot module identity")
    wrapper = run_dir / "generated" / "backend" / "rtl" / f"{module}.v"
    if not wrapper.is_file():
        raise RuntimeError(f"current compute-slot adapter is missing: {wrapper}")
    return wrapper


def resolved_board_value(run_dir: Path, name: str) -> Any:
    profile = run_dir / "input" / "target_board_profile.json"
    if not profile.is_file():
        return None
    return read_json(profile).get(name)


def build_delegate_argv(run_dir: Path, mode: str, out: Path | None) -> list[str]:
    contract_path = run_dir / "generated" / "backend" / "constraints" / "app_shell_integration_contract.json"
    if not contract_path.is_file():
        raise RuntimeError(f"current app-shell integration contract is missing: {contract_path}")
    contract = read_json(contract_path)
    wrapper = compute_slot_wrapper(run_dir, contract)
    generated_vivado_dir = run_dir / "generated" / "chisel" / "vivado"
    ip_module_manifest = run_dir / "generated" / "chisel" / "simulation" / "fpga_ip_modules.txt"
    ip_generation_tcl = run_dir / "generated" / "chisel" / "scripts" / "gen_xilinx_fp_ips_23.tcl"
    ip_closure_path = run_dir / "generated" / "chisel" / "simulation" / "fpga_ip_simulation_closure.json"
    ip_closure = read_json(ip_closure_path) if ip_closure_path.is_file() else {}
    binding_path = run_dir / "parameter_binding" / "parameter_binding.json"
    binding = read_json(binding_path) if binding_path.is_file() else {}
    global_params = binding.get("global_params", {}) if isinstance(binding.get("global_params"), dict) else {}
    fpga_part = first_text(ip_closure.get("fpga_part"), resolved_board_value(run_dir, "fpga_part"))
    clock_target_mhz = first_text(global_params.get("clock_target_mhz"), resolved_board_value(run_dir, "clock_target_mhz"))
    missing = [
        str(path)
        for path in (generated_vivado_dir, ip_module_manifest, ip_generation_tcl)
        if not path.exists()
    ]
    if missing:
        raise RuntimeError(f"current FPGA implementation closure is incomplete: {missing}")
    if not fpga_part:
        raise RuntimeError("current run has no FPGA part in its board/IP contract")
    if not clock_target_mhz:
        raise RuntimeError("current run has no target clock frequency in parameter binding or board profile")
    report = out or run_dir / "backend_board" / "case_diagnostics" / "app_shell_runtime_vivado.json"
    return [
        "--run-dir",
        str(run_dir),
        "--contract",
        str(contract_path),
        "--wrapper-rtl",
        str(wrapper),
        "--generated-vivado-dir",
        str(generated_vivado_dir),
        "--ip-module-manifest",
        str(ip_module_manifest),
        "--ip-generation-tcl",
        str(ip_generation_tcl),
        "--fpga-part",
        fpga_part,
        "--clock-target-mhz",
        clock_target_mhz,
        "--mode",
        mode,
        "--out",
        str(report),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=["preflight", "ooc", "synth", "bitstream"], required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        return app_shell_main(build_delegate_argv(args.run_dir.resolve(), args.mode, args.out))
    except Exception as exc:
        print(f"case_app_shell_vivado.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
