#!/usr/bin/env python3
"""Check whether a case has a board-runtime ABI, not just a standalone core.

This gate is intentionally conservative. It does not create a wrapper or
infer board pass from a generated bitstream; it records the concrete gaps that
must be closed before a runtime/app_shell bitstream or board run can pass.
"""

from __future__ import annotations

import argparse
import ast
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or str(value).strip().lower() in {"none", "null"}


def check(name: str, passed: bool, summary: str, **extra: Any) -> dict[str, Any]:
    return {"name": name, "status": "pass" if passed else "fail", "summary": summary, **extra}


def int_value(value: Any, default: int | None = None) -> int | None:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return int(text, 0)
        except ValueError:
            return default
    return default


def nested(data: dict[str, Any], path: list[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def first_value(data: dict[str, Any], paths: list[list[str]]) -> Any:
    for path in paths:
        value = nested(data, path)
        if not is_blank(value):
            return value
    return None


def clean_token(value: Any) -> str | None:
    if is_blank(value):
        return None
    text = str(value).strip().strip("`'\"")
    return text or None


def interface_prefix_from_profile(board_profile: dict[str, Any], override: str | None) -> str | None:
    if override:
        return override.rstrip("*").rstrip("_")
    memory = board_profile.get("memory_system", {}) if isinstance(board_profile.get("memory_system"), dict) else {}
    shell = board_profile.get("shell", {}) if isinstance(board_profile.get("shell"), dict) else {}
    raw = clean_token(memory.get("core_side_interface_name")) or clean_token(shell.get("core_ddr_axi_interface"))
    if not raw:
        return None
    return raw.rstrip("*").rstrip("_")


def resolve_path(run_dir: Path, value: Any) -> Path | None:
    text = clean_token(value)
    if not text:
        return None
    path = Path(text)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    run_path = run_dir / path
    if run_path.exists():
        return run_path
    return run_path


def board_reference_path(run_dir: Path, board_profile: dict[str, Any], override: Path | None) -> Path | None:
    if override:
        return override
    memory = board_profile.get("memory_system", {}) if isinstance(board_profile.get("memory_system"), dict) else {}
    shell = board_profile.get("shell", {}) if isinstance(board_profile.get("shell"), dict) else {}
    return resolve_path(run_dir, memory.get("real_board_reference_rtl") or shell.get("real_board_axi_reference_rtl"))


def required_board_signals(board_profile: dict[str, Any], prefix: str | None) -> list[str]:
    memory = board_profile.get("memory_system", {}) if isinstance(board_profile.get("memory_system"), dict) else {}
    shell = board_profile.get("shell", {}) if isinstance(board_profile.get("shell"), dict) else {}
    signals: list[str] = []
    for value in [
        memory.get("axi_clock"),
        shell.get("axi_clock"),
        memory.get("axi_reset"),
        shell.get("axi_reset"),
        memory.get("calibration_done_signal"),
        shell.get("init_calibration_done_signal"),
    ]:
        token = clean_token(value)
        if token and token not in signals:
            signals.append(token)
    if prefix:
        for inferred in [f"{prefix}_clk", f"{prefix}_rst_n"]:
            if inferred not in signals:
                signals.append(inferred)
    return signals


def expand_candidates(run_dir: Path, raw_candidates: list[str], default_patterns: list[str]) -> list[Path]:
    patterns = raw_candidates or default_patterns
    result: list[Path] = []
    seen: set[str] = set()
    for raw in patterns:
        text = str(raw).strip()
        if not text:
            continue
        path = Path(text)
        pattern = str(path if path.is_absolute() else run_dir / path)
        matches = [Path(item) for item in glob.glob(pattern)]
        if not matches:
            matches = [path if path.is_absolute() else run_dir / path]
        for item in matches:
            key = str(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
    return result


def safe_eval_expr(expr: str, params: dict[str, int]) -> int | None:
    expr = expr.strip()
    if re.fullmatch(r"\d+", expr):
        return int(expr)
    replaced = expr
    for name, value in sorted(params.items(), key=lambda item: -len(item[0])):
        replaced = re.sub(rf"\b{re.escape(name)}\b", str(value), replaced)
    if not re.fullmatch(r"[0-9+\-*/ ()]+", replaced):
        return None
    try:
        tree = ast.parse(replaced, mode="eval")
    except SyntaxError:
        return None
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.USub,
        ast.UAdd,
        ast.Constant,
        ast.Load,
    )
    if not all(isinstance(node, allowed) for node in ast.walk(tree)):
        return None
    try:
        value = eval(compile(tree, "<width_expr>", "eval"), {"__builtins__": {}}, {})
    except Exception:
        return None
    return int(value)


def parse_params(text: str) -> dict[str, int]:
    params: dict[str, int] = {}
    pattern = re.compile(r"\bparameter(?:\s+\w+)?\s+(\w+)\s*=\s*([^,\n;)]+)")
    progress = True
    while progress:
        progress = False
        for name, expr in pattern.findall(text):
            if name in params:
                continue
            value = safe_eval_expr(expr, params)
            if value is not None:
                params[name] = value
                progress = True
    return params


def range_width(range_text: str | None, params: dict[str, int]) -> int:
    if not range_text:
        return 1
    match = re.match(r"\[\s*(.*?)\s*:\s*(.*?)\s*\]", range_text)
    if not match:
        return 1
    left = safe_eval_expr(match.group(1), params)
    right = safe_eval_expr(match.group(2), params)
    if left is None or right is None:
        return -1
    return abs(left - right) + 1


def signal_width(text: str, signal: str) -> int | None:
    params = parse_params(text)
    line_pattern = re.compile(rf"^[^\n;]*\b(?:input|output|inout)\b[^\n;]*\b{re.escape(signal)}\b[^\n;]*", re.M)
    match = line_pattern.search(text)
    if not match:
        return None
    range_match = re.search(r"\[[^\]]+\]", match.group(0))
    return range_width(range_match.group(0) if range_match else None, params)


def check_file(path: Path, label: str) -> tuple[bool, dict[str, Any]]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return exists and size > 0, check(label, exists and size > 0, f"path={path} size={size}", path=str(path), size_bytes=size)


def expected_board_widths(board_profile: dict[str, Any]) -> dict[str, int | None]:
    memory = board_profile.get("memory_system", {}) if isinstance(board_profile.get("memory_system"), dict) else {}
    data_bits = int_value(memory.get("axi_data_width_bits"), int_value(memory.get("ddr_word_width_bits"), None))
    data_bytes = int_value(memory.get("axi_data_bytes"), data_bits // 8 if data_bits else None)
    return {
        "data_bits": data_bits,
        "data_bytes": data_bytes,
        "addr_bits": int_value(memory.get("axi_addr_width_bits"), None),
        "id_bits": int_value(memory.get("axi_id_width_bits"), None),
        "wstrb_bits": int_value(memory.get("axi_wstrb_width_bits"), data_bytes),
    }


def interface_checks(
    label: str,
    text: str,
    prefix: str,
    expected: dict[str, int | None],
    required_signals: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    required = {
        f"{prefix}_awaddr": expected["addr_bits"],
        f"{prefix}_araddr": expected["addr_bits"],
        f"{prefix}_awid": expected["id_bits"],
        f"{prefix}_arid": expected["id_bits"],
        f"{prefix}_wdata": expected["data_bits"],
        f"{prefix}_rdata": expected["data_bits"],
        f"{prefix}_wstrb": expected["wstrb_bits"],
    }
    for signal, width in required.items():
        found = signal in text
        observed = signal_width(text, signal) if found else None
        ok = found and (width is None or observed == width)
        checks.append(check(f"{label}_{signal}", ok, f"observed_width={observed} expected_width={width}", signal=signal, observed_width=observed, expected_width=width))
        if not ok:
            blockers.append(f"{label} missing or mismatches {signal}: observed_width={observed} expected_width={width}")
    for signal in required_signals:
        found = signal in text
        checks.append(check(f"{label}_{signal}", found, "required board clock/reset/calibration signal", signal=signal))
        if not found:
            blockers.append(f"{label} missing required signal {signal}")
    return checks, blockers


def generic_axi_summary(text: str, signals: list[str]) -> dict[str, int | None]:
    return {signal: signal_width(text, signal) for signal in signals}


def first_candidate_value(candidates: list[tuple[str, dict[str, Any], list[str]]]) -> dict[str, Any]:
    for source, data, path in candidates:
        value = nested(data, path)
        if not is_blank(value):
            return {"value": value, "source": source, "path": ".".join(path)}
    return {"value": None, "source": None, "path": None}


def runtime_field_records(
    runtime_config_interface: dict[str, Any],
    board_profile_interface: dict[str, Any],
    address_map: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    cfg = runtime_config_interface
    profile = board_profile_interface
    return {
        "control_protocol": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["control_protocol"]),
            ("board_profile.runtime_interface", profile, ["control_protocol"]),
        ]),
        "board_run_command": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["board_run_command"]),
            ("board_profile.runtime_interface", profile, ["board_run_command"]),
        ]),
        "remote_host": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["remote_host"]),
            ("runtime_config.runtime_interface", cfg, ["runtime_machine"]),
            ("board_profile.runtime_interface", profile, ["remote_host"]),
            ("board_profile.runtime_interface", profile, ["runtime_machine"]),
        ]),
        "mimic_dir": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["mimic_dir"]),
            ("board_profile.runtime_interface", profile, ["mimic_dir"]),
        ]),
        "xdma_id": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["xdma_id_default"]),
            ("runtime_config.runtime_interface", cfg, ["xdma_id_variable"]),
            ("board_profile.runtime_interface", profile, ["xdma_id_default"]),
            ("board_profile.runtime_interface", profile, ["xdma_id_variable"]),
        ]),
        "ctrl_base": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["ctrl_base"]),
            ("runtime_config.runtime_interface", cfg, ["control_base"]),
            ("board_profile.runtime_interface", profile, ["ctrl_base"]),
            ("board_profile.runtime_interface", profile, ["control_base"]),
            ("board_profile.memory_system.address_map", address_map, ["control_registers"]),
        ]),
        "ddr_base": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["ddr_base"]),
            ("board_profile.runtime_interface", profile, ["ddr_base"]),
            ("board_profile.memory_system.address_map", address_map, ["ddr_base"]),
            ("board_profile.memory_system.address_map", address_map, ["input_abs"]),
        ]),
        "output_abs": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["output_abs"]),
            ("board_profile.runtime_interface", profile, ["output_abs"]),
            ("board_profile.memory_system.address_map", address_map, ["output_abs"]),
        ]),
        "h2c_device_template": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["h2c_device_template"]),
            ("board_profile.runtime_interface", profile, ["h2c_device_template"]),
        ]),
        "c2h_device_template": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["c2h_device_template"]),
            ("board_profile.runtime_interface", profile, ["c2h_device_template"]),
        ]),
        "ddr_image": first_candidate_value([
            ("runtime_config.runtime_interface", cfg, ["ddr_image_default"]),
            ("runtime_config.runtime_interface", cfg, ["default_ddr_image_path_observed"]),
            ("board_profile.runtime_interface", profile, ["ddr_image_default"]),
            ("board_profile.runtime_interface", profile, ["default_ddr_image_path_observed"]),
        ]),
    }


def required_runtime_fields(args: argparse.Namespace, values: dict[str, Any]) -> list[str]:
    if args.required_runtime_field:
        return list(dict.fromkeys(args.required_runtime_field))
    required = ["control_protocol", "board_run_command"]
    protocol = str(values.get("control_protocol") or "").lower()
    if "xdma" in protocol:
        required.extend(["xdma_id", "ctrl_base", "ddr_base", "output_abs", "h2c_device_template", "c2h_device_template"])
    command = str(values.get("board_run_command") or "").lower()
    if "mimic" in protocol or "mimic" in command:
        required.append("mimic_dir")
    return list(dict.fromkeys(required))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    base_paths = {
        "runtime_config": args.runtime_config,
        "memory_layout": args.memory_layout,
        "board_profile": args.board_profile,
        "generated_top": args.generated_top,
        "board_wrapper": args.board_wrapper,
    }
    for label, path in base_paths.items():
        ok, item = check_file(path, label)
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty {label}: {path}")

    runtime_config = read_json(args.runtime_config) if args.runtime_config.exists() else {}
    memory_layout = read_json(args.memory_layout) if args.memory_layout.exists() else {}
    board_profile = read_json(args.board_profile) if args.board_profile.exists() else {}
    interface_prefix = interface_prefix_from_profile(board_profile, args.interface_prefix)
    reference_path = board_reference_path(run_dir, board_profile, args.board_reference)
    if reference_path:
        ok, item = check_file(reference_path, "board_reference")
        checks.append(item)
        if not ok:
            blockers.append(f"missing or empty board_reference: {reference_path}")
    else:
        reference_path = Path("")
        checks.append(check("board_reference", False, "board reference RTL path is not configured"))
        blockers.append("board profile or case adapter must provide a real board AXI reference RTL path")
    if not interface_prefix:
        checks.append(check("board_interface_prefix", False, "board interface prefix is not configured"))
        blockers.append("board profile or case adapter must provide core_side_interface_name/core_ddr_axi_interface")

    expected = expected_board_widths(board_profile)
    runtime = runtime_config.get("runtime_interface", {}) if isinstance(runtime_config.get("runtime_interface"), dict) else {}
    profile_runtime = board_profile.get("runtime_interface", {}) if isinstance(board_profile.get("runtime_interface"), dict) else {}
    board_memory = board_profile.get("memory_system", {}) if isinstance(board_profile.get("memory_system"), dict) else {}
    address_map = board_memory.get("address_map", {}) if isinstance(board_memory.get("address_map"), dict) else {}

    layout_axi = int_value(memory_layout.get("axi_data_width_bits"), None)
    layout_align = int_value(memory_layout.get("alignment_bytes"), None)
    checks.append(check("memory_layout_axi_width", layout_axi == expected["data_bits"], f"layout_axi={layout_axi} board_axi={expected['data_bits']}", layout_axi_bits=layout_axi, board_axi_bits=expected["data_bits"]))
    if layout_axi != expected["data_bits"]:
        blockers.append(f"memory_layout axi width {layout_axi} does not match board width {expected['data_bits']}")
    checks.append(check("memory_layout_alignment", layout_align == expected["data_bytes"], f"layout_alignment={layout_align} board_beat_bytes={expected['data_bytes']}", layout_alignment_bytes=layout_align, board_beat_bytes=expected["data_bytes"]))
    if layout_align != expected["data_bytes"]:
        blockers.append(f"memory_layout alignment {layout_align} does not match board AXI beat bytes {expected['data_bytes']}")

    alignment = layout_align or expected["data_bytes"] or 1
    misaligned = []
    for region in memory_layout.get("regions", []) if isinstance(memory_layout.get("regions"), list) else []:
        base = int_value(region.get("base_addr"), -1)
        size = int_value(region.get("size_bytes"), -1)
        if base is None or size is None or base < 0 or size < 0 or base % alignment != 0 or size % alignment != 0:
            misaligned.append(region.get("name"))
    checks.append(check("memory_regions_aligned", not misaligned, f"alignment={alignment} misaligned={misaligned}", misaligned_regions=misaligned))
    if misaligned:
        blockers.append(f"memory layout regions are not aligned to {alignment} bytes: {misaligned}")

    runtime_records = runtime_field_records(runtime, profile_runtime, address_map)
    runtime_values = {name: record.get("value") for name, record in runtime_records.items()}
    required_runtime = set(required_runtime_fields(args, runtime_values))
    for name, record in runtime_records.items():
        value = record.get("value")
        ok = not is_blank(value)
        checks.append(
            check(
                f"runtime_field_{name}",
                ok,
                f"value={value} source={record.get('source')}",
                value=value,
                source=record.get("source"),
                source_path=record.get("path"),
            )
        )
        if name in required_runtime and not ok:
            blockers.append(f"runtime ABI missing concrete field: {name}")

    generated_text = read_text(args.generated_top)
    wrapper_text = read_text(args.board_wrapper)
    reference_text = read_text(reference_path)

    gen_widths = generic_axi_summary(generated_text, ["io_axiReadData", "io_axiWriteData", "io_axiReadAddr", "io_axiWriteAddr"])
    generated_has_board_ports = bool(interface_prefix and interface_prefix in generated_text)
    generated_width_ok = gen_widths.get("io_axiReadData") == expected["data_bits"] and gen_widths.get("io_axiWriteData") == expected["data_bits"]
    checks.append(check("generated_top_board_axis", generated_has_board_ports, f"interface_prefix={interface_prefix}", observed_widths=gen_widths))
    checks.append(check("generated_top_stream_width_matches_board", generated_width_ok, f"observed={gen_widths} expected_data_bits={expected['data_bits']}", observed_widths=gen_widths, expected_data_bits=expected["data_bits"]))

    wrapper_axi = generic_axi_summary(wrapper_text, ["io_m_axi_wdata", "io_m_axi_rdata", "io_m_axi_awaddr", "io_m_axi_araddr", "io_m_axi_awid", "io_m_axi_arid", "io_m_axi_wstrb"])
    wrapper_has_board_ports = bool(interface_prefix and interface_prefix in wrapper_text)
    wrapper_has_generic_axi = any(signal in wrapper_text for signal in ["io_m_axi_awaddr", "io_m_axi_araddr", "io_m_axi_wdata", "io_m_axi_rdata"])
    wrapper_data_ok = wrapper_axi.get("io_m_axi_wdata") == expected["data_bits"] and wrapper_axi.get("io_m_axi_rdata") == expected["data_bits"]
    checks.append(check("board_wrapper_has_board_ports", wrapper_has_board_ports, f"interface_prefix={interface_prefix}", generic_axi_widths=wrapper_axi))
    checks.append(check("board_wrapper_has_generic_axi", wrapper_has_generic_axi, "generic AXI wrapper is useful for simulation but not sufficient for the board shell interface"))
    if wrapper_has_board_ports and not wrapper_has_generic_axi:
        checks.append(
            {
                "name": "board_wrapper_generic_axi_width_matches_board",
                "status": "informational",
                "summary": "board-prefixed AXI ports are present; generic io_m_axi width check is not required",
                "generic_axi_widths": wrapper_axi,
                "expected_data_bits": expected["data_bits"],
            }
        )
    else:
        checks.append(check("board_wrapper_generic_axi_width_matches_board", wrapper_data_ok, f"observed={wrapper_axi} expected_data_bits={expected['data_bits']}", generic_axi_widths=wrapper_axi, expected_data_bits=expected["data_bits"]))
    if interface_prefix and not (generated_has_board_ports or wrapper_has_board_ports):
        blockers.append(f"no generated/runtime top exposes board shell interface prefix {interface_prefix}")
    if not wrapper_has_board_ports and wrapper_has_generic_axi and not wrapper_data_ok:
        blockers.append(
            f"available board wrapper is a generic AXI simulation scaffold, not the board shell interface: "
            f"observed={wrapper_axi} expected_data_bits={expected['data_bits']}"
        )

    if interface_prefix:
        ref_checks, ref_blockers = interface_checks("board_reference", reference_text, interface_prefix, expected, required_board_signals(board_profile, interface_prefix))
        checks.extend(ref_checks)
        if ref_blockers:
            blockers.extend(ref_blockers)

    runtime_candidates = expand_candidates(
        run_dir,
        args.runtime_bitstream_candidate,
        [
            "app_shell_runtime_bitstream/*.bit",
            "runtime_board_shell_bitstream/*.bit",
            "runtime_bitstream/*.bit",
            "vivado_runtime_bitstream/*.bit",
            "backend/vivado/*.bit",
        ],
    )
    runtime_bits = [str(path) for path in runtime_candidates if path.exists() and path.stat().st_size > 0]
    standalone_candidates = expand_candidates(run_dir, args.standalone_bitstream_candidate, ["vivado_*/*.bit", "*.bit"])
    standalone_bits = [
        str(path)
        for path in standalone_candidates
        if path.exists() and path.stat().st_size > 0
        and str(path) not in set(runtime_bits)
    ]
    checks.append(check("runtime_board_shell_bitstream_exists", bool(runtime_bits), f"runtime_bits={runtime_bits}", runtime_bits=runtime_bits))
    checks.append({"name": "standalone_core_bitstreams", "status": "informational", "paths": standalone_bits})
    if not runtime_bits:
        blockers.append("no runtime/board-shell bitstream artifact exists; standalone generated-core bitstream is not board-runtime evidence")

    if args.vivado_report_check and args.vivado_report_check.exists():
        vivado_report = read_json(args.vivado_report_check)
        report_status = vivado_report.get("status")
        checks.append(check("standalone_vivado_report_gate", report_status == "pass", f"status={report_status}", report_path=str(args.vivado_report_check), blockers=vivado_report.get("blockers", [])))
        if report_status != "pass":
            checks.append(
                {
                    "name": "standalone_vivado_report_gate_scope",
                    "status": "informational",
                    "summary": "standalone generated-core report is not runtime board-shell evidence; backend Vivado report gates remain responsible for timing/DRC closure",
                }
            )

    return {
        "schema_version": "spatialaccagent.case_runtime_abi_check.v0",
        "gate": "runtime_abi_check",
        "run_dir": str(run_dir),
        "status": "pass" if not blockers else "fail",
        "interface_prefix": interface_prefix,
        "expected_board_widths": expected,
        "required_runtime_fields": sorted(required_runtime),
        "runtime_field_records": runtime_records,
        "checks": checks,
        "blockers": blockers,
        "summary": "runtime ABI/board-shell preflight passed" if not blockers else f"{len(blockers)} blocker(s)",
        "next_actions": [
            f"Generate a board-runtime wrapper that exposes the board DDR AXI interface"
            f"{f' ({interface_prefix})' if interface_prefix else ''} and maps the generated core stream protocol to the board data width.",
            "Stabilize runtime ABI fields in target_board_profile/runtime_config for the selected control protocol, including address map, device IDs, runtime tool paths, and DDR image path when required.",
            "Run Vivado against the board-shell-integrated top and bind timing, DRC, bitstream, and board runtime logs back into SACG.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check runtime ABI and app_shell integration preconditions.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--runtime-config", type=Path, required=True)
    parser.add_argument("--memory-layout", type=Path, required=True)
    parser.add_argument("--board-profile", type=Path, required=True)
    parser.add_argument("--generated-top", type=Path, required=True)
    parser.add_argument("--board-wrapper", type=Path, required=True)
    parser.add_argument("--board-reference", type=Path)
    parser.add_argument("--vivado-report-check", type=Path)
    parser.add_argument("--interface-prefix")
    parser.add_argument("--required-runtime-field", action="append", default=[])
    parser.add_argument("--runtime-bitstream-candidate", action="append", default=[])
    parser.add_argument("--standalone-bitstream-candidate", action="append", default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    out = args.out or args.run_dir / "backend_board" / "case_diagnostics" / "runtime_abi_check.json"
    report = build_report(args)
    write_json(out, report)
    if report["status"] != "pass":
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
