#!/usr/bin/env python3
"""Generate the real app-shell compute-slot adapter.

The board scheduler is intentionally reused from the current board artifact:
it owns the AXI/DDR protocol, ping-pong activation buffers, weight prefetch,
and writeback sequencing.  This generator only replaces the old semantic
harness instance with the generated FPGA top and inserts the width-changing
weight stream packer described by the current loader route contract.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _port_names(verilog: str) -> set[str]:
    names: set[str] = set()
    for match in re.finditer(
        r"(?ms)^\s*(?:input|output)(?:\s+wire|\s+reg)?"
        r"(?:\s+\[[^]]+\])?\s+(.*?)"
        r"(?=^\s*(?:input|output)\b|\);|\Z)",
        verilog,
    ):
        declaration = match.group(1)
        for value in declaration.split(","):
            value = re.sub(r"^(?:input|output)(?:\s+wire|\s+reg)?\s+", "", value.strip())
            name = value.split()[0] if value else ""
            if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", name):
                names.add(name)
    return names


def _module_port_names(verilog: str) -> set[str]:
    """Read only the first module header, excluding function/task inputs."""

    header = verilog.split(");", 1)[0]
    return _port_names(header)


def _module_port_widths(verilog: str) -> dict[str, int]:
    """Read widths from the generated top header when they are declared."""

    header = verilog.split(");", 1)[0]
    widths: dict[str, int] = {}
    pattern = re.compile(
        r"(?ms)^\s*(?:input|output)(?:\s+wire|\s+reg)?\s*"
        r"(?:\[(?P<msb>\d+):(?P<lsb>\d+)\]\s*)?"
        r"(?P<decl>.*?)"
        r"(?=^\s*(?:input|output)\b|\);|\Z)"
    )
    for match in pattern.finditer(header):
        msb = match.group("msb")
        width = int(msb) + 1 if msb is not None else 1
        for value in match.group("decl").split(","):
            value = re.sub(r"^(?:input|output)(?:\s+wire|\s+reg)?\s+", "", value.strip())
            name = value.split()[0] if value else ""
            if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", name):
                widths[name] = width
    return widths


def _module_name(verilog: str) -> str:
    match = re.search(r"\bmodule\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", verilog)
    if not match:
        raise ValueError("generated top does not contain a module declaration")
    return match.group(1)


def _safe_symbol(value: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_$]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        return fallback
    if value[0].isdigit():
        return f"r_{value}"
    return value


def _snake_symbol(value: str, fallback: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return _safe_symbol(value.lower(), fallback)


def _port_width(widths: dict[str, int], port: str, fallback: int = 1) -> int:
    width = int(widths.get(port, 0) or 0)
    return width if width > 0 else fallback


def _width_adapter(signal: str, source_width: int, target_width: int, name: str) -> str:
    """Create an explicit, compile-time-safe width adapter.

    The sample compute slot transports one 256-bit activation half, while a
    generated top may expose a different stream width.  Keeping this
    conversion explicit prevents Verilog's silent truncation/extension from
    changing the generated design without appearing in the adapter manifest.
    """

    if source_width <= 0 or target_width <= 0:
        raise ValueError(f"invalid width adapter {name}: {source_width}->{target_width}")
    if source_width == target_width:
        return f"wire [{target_width - 1}:0] {name} = {signal};"
    if target_width < source_width:
        return f"wire [{target_width - 1}:0] {name} = {signal}[{target_width - 1}:0];"
    return (
        f"wire [{target_width - 1}:0] {name} = "
        f"{{{{{target_width - source_width}{{1'b0}}}}, {signal}}};"
    )


def _find_port(port_names: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in port_names:
            return candidate
    return None


def _route_interface(
    row: dict[str, Any],
    port_names: set[str],
    port_widths: dict[str, int],
    index: int,
) -> dict[str, Any]:
    """Resolve one loader route against the generated top's real ports.

    The route contract supplies the semantic DUT port.  The generated top is
    the authority for the concrete ready/valid/data/address spelling and
    widths.  This keeps the board adapter independent of a model's number or
    naming of weight streams while still failing early on an incomplete top.
    """

    base = f"io_{row['port']}"
    ready = _find_port(port_names, [f"{base}_ready"])
    valid = _find_port(port_names, [f"{base}_valid"])
    data = _find_port(port_names, [f"{base}_bits_data", f"{base}_bits"])
    addr = _find_port(port_names, [f"{base}_bits_addr", f"{base}_addr"])
    missing = [name for name, value in (("ready", ready), ("valid", valid), ("data", data)) if value is None]
    if missing:
        raise ValueError(
            f"generated top is missing {row['port']} route port(s): {', '.join(missing)}"
        )
    raw_symbol = re.sub(r"(?i)(weight|bias)$", "", str(row["port"]))
    symbol = _safe_symbol(raw_symbol or row["port"], f"route_{index}")
    data_width = _port_width(port_widths, data, int(row.get("data_width_bits", 0) or 32))
    words_per_tx = int(row.get("words_per_tx", 0) or 0)
    if words_per_tx <= 0:
        words_per_tx = max(1, (data_width + 31) // 32)
    if data_width < words_per_tx * 32:
        raise ValueError(
            f"route {row['port']} data width {data_width} is smaller than "
            f"its {words_per_tx} 32-bit words"
        )
    return {
        **row,
        "symbol": symbol,
        "ready_port": ready,
        "valid_port": valid,
        "data_port": data,
        "addr_port": addr,
        "data_width_bits": data_width,
        "words_per_tx": words_per_tx,
        "addr_width": _port_width(port_widths, addr, 1) if addr else 1,
    }


def _weight_target_metadata(contract: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    """Index physical port metadata from the current weight stream contract."""

    loader = contract.get("loader_route_contract", {})
    weight = loader.get("weight", {}) if isinstance(loader, dict) else {}
    result: dict[tuple[int, int], dict[str, Any]] = {}
    for segment in weight.get("stage_segments", []) if isinstance(weight, dict) else []:
        if not isinstance(segment, dict):
            continue
        for target in segment.get("targets", []):
            if not isinstance(target, dict):
                continue
            stream = target.get("global_stream_range", {})
            key = (int(stream.get("word_offset", 0) or 0), int(stream.get("word_count", 0) or 0))
            if key[1] > 0:
                result[key] = target
    return result


def _route_rows(contract: dict[str, Any], contract_path: Path | None = None) -> list[dict[str, Any]]:
    routes = contract.get("loader_route_contract", {}).get("weight_routes", [])
    if not isinstance(routes, list) or not routes:
        routes = contract.get("dut_loader_route_contract", {}).get("weight_routes", [])
    if (not isinstance(routes, list) or not routes) and isinstance(contract_path, Path):
        source_artifacts = contract.get("source_artifacts", {})
        manifest_value = source_artifacts.get("semantic_testbench_manifest") if isinstance(source_artifacts, dict) else None
        manifest_path = Path(str(manifest_value)) if manifest_value else None
        if manifest_path is None or not manifest_path.is_file():
            # Generated backend contracts are stored below the run directory;
            # use the current run's semantic manifest rather than a fixed
            # model/board path when an older contract omitted the reference.
            try:
                run_dir = contract_path.parents[3]
            except IndexError:
                run_dir = contract_path.parent
            manifest_path = run_dir / "verification" / "semantic_testbench" / "semantic_testbench_manifest.json"
        if manifest_path.is_file():
            manifest = read_json(manifest_path)
            single_layer = manifest.get("single_layer", {})
            harness = single_layer.get("dut_harness", {}) if isinstance(single_layer, dict) else {}
            route_contract = harness.get("loader_route_contract", {}) if isinstance(harness, dict) else {}
            routes = route_contract.get("weight_routes", []) if isinstance(route_contract, dict) else []
    target_metadata = _weight_target_metadata(contract)
    rows: list[dict[str, Any]] = []
    for row in routes:
        if not isinstance(row, dict):
            continue
        stream = row.get("global_stream_range", {})
        local = row.get("local_stream_range", {})
        port = str(row.get("dut_port", "")).split(".")[-1]
        count = int(stream.get("word_count", 0) or 0)
        start = int(stream.get("word_offset", 0) or 0)
        if count <= 0 or not port:
            continue
        target = target_metadata.get((start, count), {})
        target_port = target.get("port", {}) if isinstance(target, dict) else {}
        data_width = int(target_port.get("data_width_bits", 0) or 0)
        words_per_tx = int(target_port.get("words_per_write", 0) or 0)
        role = str(row.get("dut_port_role") or target.get("dut_port_role") or "")
        if not data_width and words_per_tx:
            data_width = words_per_tx * 32
        if not words_per_tx and data_width:
            words_per_tx = max(1, (data_width + 31) // 32)
        rows.append({
            "port": port,
            "role": role,
            "start": start,
            "count": count,
            "local_start": int(local.get("word_offset", 0) or 0),
            "data_width_bits": data_width,
            "words_per_tx": words_per_tx,
        })
    rows.sort(key=lambda row: row["start"])
    return rows


def _route_kind(port: str, role: str = "", index: int = 0) -> str:
    names = {
        "rms1Weight": "RMS1",
        "qkvWeight": "QKV",
        "qkvBias": "QKV_BIAS",
        "attentionOutWeight": "OUT_PROJ",
        "rms2Weight": "RMS2",
        "mlpGateWeight": "MLP_GATE",
        "mlpUpWeight": "MLP_UP",
        "mlpDownWeight": "MLP_DOWN",
    }
    if port in names:
        return names[port]
    role_names = {
        "qkv_weight": "QKV",
        "qkv_bias": "QKV_BIAS",
        "out_proj_weight": "OUT_PROJ",
        "rms1_weight": "RMS1",
        "rms2_weight": "RMS2",
        "mlp_gate_weight": "MLP_GATE",
        "mlp_up_weight": "MLP_UP",
        "mlp_down_weight": "MLP_DOWN",
    }
    normalized_role = re.sub(r"[^a-z0-9]+", "_", role.lower()).strip("_")
    return role_names.get(normalized_role, f"ROUTE_{index}")


def _pack_width_words(kind: str, row: dict[str, Any] | None = None) -> int:
    if row:
        explicit = int(row.get("words_per_tx", 0) or 0)
        if explicit > 0:
            return explicit
    return {
        "RMS1": 8,
        "QKV": 32,
        "QKV_BIAS": 8,
        "OUT_PROJ": 256,
        "RMS2": 8,
        "MLP_GATE": 32,
        "MLP_UP": 32,
        "MLP_DOWN": 32,
    }.get(kind, 1)


def _decorate_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    used_kinds: set[str] = set()
    used_signals: set[str] = set()
    for index, source_row in enumerate(routes):
        row = dict(source_row)
        base_kind = _route_kind(row["port"], row.get("role", ""), index)
        kind = base_kind
        suffix = 2
        while kind in used_kinds:
            kind = f"{base_kind}_{suffix}"
            suffix += 1
        used_kinds.add(kind)
        signal = _snake_symbol(
            re.sub(r"(?i)weights?$", "", str(row["port"])) or str(row["port"]),
            f"route_{index}",
        )
        base_signal = signal
        suffix = 2
        while signal in used_signals:
            signal = f"{base_signal}_{suffix}"
            suffix += 1
        used_signals.add(signal)
        row.update({"kind": kind, "signal": signal, "route_id": index + 1})
        rows.append(row)
    return rows


def _adapter_bridge(
    routes: list[dict[str, Any]],
    target_tokens: int,
    cfg_width: int,
    pos_width: int,
    input_addr_width: int,
    generated_read_width: int,
    generated_write_width: int,
) -> str:
    """Emit a route-count and route-width independent weight bridge."""

    rows = _decorate_routes(routes)

    if not rows:
        raise ValueError("the current loader contract contains no non-empty weight routes")
    route_bits = max(1, (len(rows) + 1).bit_length())
    stream_end = max(int(row["start"]) + int(row["count"]) for row in rows)
    stream_bits = max(1, stream_end.bit_length())
    words_bits = max(1, max(int(row["words_per_tx"]) for row in rows).bit_length())
    addr_bits = max(1, max(int(row.get("addr_width", 1)) for row in rows))

    constants = []
    route_checks = []
    data_decls = []
    valid_decls = []
    data_assigns = []
    route_cases = []
    pending_cases = []
    ready_terms = []
    for index, row in enumerate(rows):
        kind = row["kind"]
        signal = row["signal"]
        data_width = int(row["data_width_bits"])
        words_per_tx = int(row["words_per_tx"])
        constants.append(
            f"localparam [{route_bits - 1}:0] WEIGHT_ROUTE_{kind} = {route_bits}'d{row['route_id']};\n"
            f"localparam [{stream_bits - 1}:0] WEIGHT_{kind}_START = {stream_bits}'d{row['start']};\n"
            f"localparam [{stream_bits - 1}:0] WEIGHT_{kind}_END = {stream_bits}'d{row['start'] + row['count']};\n"
            f"localparam integer WEIGHT_{kind}_WORDS_PER_TX = {words_per_tx};"
        )
        keyword = "if" if index == 0 else "else if"
        route_checks.append(
            f"  {keyword} ((weight_word_index >= WEIGHT_{kind}_START) && "
            f"(weight_word_index < WEIGHT_{kind}_END)) begin\n"
            f"    weight_route_d = WEIGHT_ROUTE_{kind};\n"
            f"    weight_local_word_d = weight_word_index - WEIGHT_{kind}_START;\n"
            f"    weight_words_per_tx_d = WEIGHT_{kind}_WORDS_PER_TX;\n"
            f"  end"
        )
        data_decls.append(f"reg [{data_width - 1}:0] gen_{signal}_data;")
        valid_decls.append(f"wire gen_{signal}_valid; wire gen_{signal}_ready;")
        data_assigns.append(
            f"assign gen_{signal}_valid = weight_pack_pending_q && "
            f"(weight_pack_route_q == WEIGHT_ROUTE_{kind});"
        )
        route_cases.append(
            f"      WEIGHT_ROUTE_{kind}: gen_{signal}_data["
            f"(weight_local_word_d % WEIGHT_{kind}_WORDS_PER_TX)*32 +: 32] <= weight_data_q;"
        )
        pending_cases.append(
            f"          WEIGHT_ROUTE_{kind}: begin weight_pack_route_q <= WEIGHT_ROUTE_{kind}; "
            f"weight_pack_addr_q <= weight_local_word_d / WEIGHT_{kind}_WORDS_PER_TX; end"
        )
        ready_terms.append(
            f"((weight_pack_route_q == WEIGHT_ROUTE_{kind}) && gen_{signal}_ready)"
        )

    return f"""// Generated physical weight bridge. It is driven by the current
// loader contract and the generated top's actual stream widths.
{chr(10).join(constants)}
reg [{route_bits - 1}:0] weight_route_d;
reg [{stream_bits - 1}:0] weight_local_word_d;
reg [{words_bits - 1}:0] weight_words_per_tx_d;
reg [{route_bits - 1}:0] weight_pack_route_q;
reg [{addr_bits - 1}:0] weight_pack_addr_q;
reg weight_pack_pending_q;
{chr(10).join(data_decls)}
{chr(10).join(valid_decls)}
wire weight_word_fire = weight_valid_q && weight_ready;
wire weight_pack_ready = {' | '.join(ready_terms)};
assign weight_ready = ~weight_pack_pending_q;
{chr(10).join(data_assigns)}

always @* begin
  weight_route_d = {route_bits}'d0;
  weight_local_word_d = {stream_bits}'d0;
  weight_words_per_tx_d = {words_bits}'d1;
{chr(10).join(route_checks)}
end

always @(posedge c0_ddr4_s_axi_clk) begin
  if (global_reset) begin
    weight_pack_route_q <= {route_bits}'d0;
    weight_pack_addr_q <= {addr_bits}'d0;
    weight_pack_pending_q <= 1'b0;
  end else begin
    if (weight_pack_pending_q && weight_pack_ready) begin
      weight_pack_pending_q <= 1'b0;
    end
    if (weight_word_fire) begin
      case (weight_route_d)
{chr(10).join(route_cases)}
        default: begin end
      endcase
      if (((weight_local_word_d % weight_words_per_tx_d) + 1) >= weight_words_per_tx_d) begin
        weight_pack_pending_q <= 1'b1;
        case (weight_route_d)
{chr(10).join(pending_cases)}
          default: begin end
        endcase
      end
    end
  end
end

localparam [10:0] GENERATED_CORE_BEATS_PER_TOKEN = KERNEL_TRANSFER_BEATS_PER_TOKEN;
localparam [10:0] GENERATED_AXI_BEATS_PER_TOKEN = KERNEL_TRANSFER_BEATS_PER_TOKEN / 2;
wire [{cfg_width - 1}:0] generated_cfg_seqlen = {cfg_width}'d{target_tokens};
wire [{pos_width - 1}:0] generated_position = {pos_width}'d0;
wire generated_cfg_prefill = 1'b1;
wire generated_cfg_single_query = 1'b0;
wire gen_runtime_ready;
wire gen_runtime_loaded;
wire gen_axi_read_ready;
wire gen_axi_write_valid;
wire [{generated_write_width - 1}:0] gen_axi_write_data;
wire [10:0] gen_axi_write_addr;
wire gen_axi_write_start;
wire gen_axi_write_last;
wire gen_busy;
wire gen_done;
wire [63:0] gen_performance_cycles;
wire gen_performance_valid;
{_width_adapter('kernel_input_data_q', 256, generated_read_width, 'generated_axi_read_data')}
{_width_adapter('gen_axi_write_data', generated_write_width, 256, 'kernel_output_data_q')}
wire [{max(1, int(input_addr_width)) - 1}:0] generated_input_addr =
    (input_axi_index[{max(1, int(input_addr_width)) - 1}:0] << 1) +
    ((state == S_COMPUTE_INPUT_HI) ? 1 : 0);

"""


def _common_top_ports(port_names: set[str]) -> dict[str, str]:
    required = {
        "clock": ["clock"],
        "reset": ["reset"],
        "start": ["io_start"],
        "cfg_seqlen": ["io_cfgSeqlen"],
        "cfg_prefill": ["io_cfgPrefill"],
        "cfg_single_query": ["io_cfgSingleQuery"],
        "position": ["io_position"],
        "read_valid": ["io_axiReadValid"],
        "read_ready": ["io_axiReadReady"],
        "read_data": ["io_axiReadData"],
        "read_addr": ["io_axiReadAddr"],
        "read_start": ["io_axiReadStart"],
        "read_last": ["io_axiReadLast"],
        "write_valid": ["io_axiWriteValid"],
        "write_ready": ["io_axiWriteReady"],
        "write_data": ["io_axiWriteData"],
        "write_addr": ["io_axiWriteAddr"],
        "write_start": ["io_axiWriteStart"],
        "write_last": ["io_axiWriteLast"],
        "busy": ["io_busy"],
        "done": ["io_done"],
        "performance_cycles": ["io_performanceCycles"],
        "performance_valid": ["io_performanceValid"],
    }
    result: dict[str, str] = {}
    missing: list[str] = []
    for role, candidates in required.items():
        selected = _find_port(port_names, candidates)
        if selected is None:
            missing.append(f"{role} ({', '.join(candidates)})")
        else:
            result[role] = selected
    if missing:
        raise ValueError(f"generated top is missing required control/data ports: {missing}")
    return result


def _runtime_interface(
    contract: dict[str, Any],
    port_names: set[str],
) -> dict[str, str] | None:
    route_contract = contract.get("dut_loader_route_contract", {})
    routes = route_contract.get("runtime_routes", []) if isinstance(route_contract, dict) else []
    if not isinstance(routes, list) or not routes:
        return None
    first = routes[0] if isinstance(routes[0], dict) else {}
    port = str(first.get("dut_port", "")).split(".")[-1]
    if not port:
        raise ValueError("runtime route is present but has no DUT port")
    base = f"io_{port}"
    candidates = {
        "ready": [f"{base}_ready"],
        "valid": [f"{base}_valid"],
        "data": [f"{base}_bits_data", f"{base}_bits"],
        "addr": [f"{base}_bits_addr", f"{base}_addr"],
        "last": [f"{base}Last", f"{base}_last"],
        "loaded": [f"{base}Loaded", f"{base}_loaded"],
    }
    result: dict[str, str] = {}
    missing: list[str] = []
    for role, names in candidates.items():
        selected = _find_port(port_names, names)
        if selected is None and role in {"ready", "valid", "data", "addr", "last"}:
            missing.append(f"{role} ({', '.join(names)})")
        elif selected is not None:
            result[role] = selected
    if missing:
        raise ValueError(f"generated top is missing runtime route port(s): {missing}")
    return result


def _instance(
    target_module: str,
    top_module: str,
    common: dict[str, str],
    routes: list[dict[str, Any]],
    runtime: dict[str, str] | None,
) -> str:
    connections = [
        f"  .{common['clock']}(c0_ddr4_s_axi_clk),",
        f"  .{common['reset']}(kernel_reset_q),",
        f"  .{common['start']}(kernel_start_to_core),",
        f"  .{common['cfg_seqlen']}(generated_cfg_seqlen),",
        f"  .{common['cfg_prefill']}(generated_cfg_prefill),",
        f"  .{common['cfg_single_query']}(generated_cfg_single_query),",
        f"  .{common['position']}(generated_position),",
    ]
    for row in routes:
        signal = row["signal"]
        connections.extend(
            [
                f"  .{row['ready_port']}(gen_{signal}_ready),",
                f"  .{row['valid_port']}(gen_{signal}_valid),",
                f"  .{row['data_port']}(gen_{signal}_data),",
            ]
        )
        if row.get("addr_port"):
            connections.append(f"  .{row['addr_port']}(weight_pack_addr_q),")
    if runtime is not None:
        connections.extend(
            [
                f"  .{runtime['ready']}(gen_runtime_ready),",
                f"  .{runtime['valid']}(runtime_valid_q),",
                f"  .{runtime['addr']}(runtime_addr_q),",
                f"  .{runtime['data']}(runtime_data_q),",
            ]
        )
        if runtime.get("last"):
            connections.append(f"  .{runtime['last']}(runtime_last_q),")
        if runtime.get("loaded"):
            connections.append(f"  .{runtime['loaded']}(gen_runtime_loaded),")
    else:
        connections.append("  // This model has no runtime stream route.")
    connections.extend(
        [
            f"  .{common['read_valid']}(kernel_input_valid_q),",
            f"  .{common['read_ready']}(gen_axi_read_ready),",
            f"  .{common['read_data']}(generated_axi_read_data),",
            f"  .{common['read_addr']}(generated_input_addr),",
            f"  .{common['read_start']}(kernel_input_start_q),",
            f"  .{common['read_last']}(kernel_input_last_q),",
            f"  .{common['write_valid']}(gen_axi_write_valid),",
            f"  .{common['write_ready']}(kernel_output_ready),",
            f"  .{common['write_data']}(gen_axi_write_data),",
            f"  .{common['write_addr']}(gen_axi_write_addr),",
            f"  .{common['write_start']}(gen_axi_write_start),",
            f"  .{common['write_last']}(gen_axi_write_last),",
            f"  .{common['busy']}(gen_busy),",
            f"  .{common['done']}(gen_done),",
            f"  .{common['performance_cycles']}(gen_performance_cycles),",
            f"  .{common['performance_valid']}(gen_performance_valid)",
        ]
    )
    post_assign = "assign gen_runtime_ready = 1'b1;\n" if runtime is None else ""
    return f"""{top_module} spatialacc_generated_top(
{chr(10).join(connections)}
);
{post_assign}
assign kernel_input_ready = gen_axi_read_ready;
assign kernel_output_valid = gen_axi_write_valid;
assign kernel_output_data = kernel_output_data_q;
assign runtime_ready = gen_runtime_ready;
"""


def generate(contract_path: Path, legacy_adapter: Path, generated_top: Path, output_path: Path, manifest_path: Path) -> dict[str, Any]:
    if legacy_adapter.resolve() == output_path.resolve():
        raise ValueError(
            "legacy adapter and generated output must be different files; "
            "the legacy scheduler is an input template and must remain read-only"
        )
    contract = read_json(contract_path)
    target = contract.get("integration_target", {})
    target_module = str(target.get("replacement_module_identity") or target.get("ip_name") or "")
    if not target_module:
        target_module = str(contract.get("compute_slot_abi", {}).get("replacement_module_identity") or "")
    if not target_module:
        raise ValueError("app-shell contract has no replacement module identity")
    source = legacy_adapter.read_text(encoding="utf-8")
    top_text = generated_top.read_text(encoding="utf-8")
    if "SingleLayerSemanticHarness" not in source:
        raise ValueError("legacy compute-slot adapter does not contain the expected scheduler instance")
    top_module = _module_name(top_text)
    top_ports = _module_port_names(top_text)
    top_widths = _module_port_widths(top_text)
    common_ports = _common_top_ports(top_ports)
    compute_slot_abi = contract.get("compute_slot_abi", {})
    required_ports = {
        str(row.get("name"))
        for row in compute_slot_abi.get("required_ports", [])
        if isinstance(row, dict) and row.get("name")
    }
    if required_ports:
        actual_ports = _module_port_names(source)
        missing_ports = sorted(required_ports - actual_ports)
        if missing_ports:
            raise ValueError(f"legacy compute-slot adapter misses required ABI ports: {missing_ports}")
    routes = [
        _route_interface(row, top_ports, top_widths, index)
        for index, row in enumerate(_route_rows(contract, contract_path))
    ]
    routes = _decorate_routes(routes)
    params = contract.get("generated_core", {}).get("params", {})
    target_tokens = int(params.get("max_seq_len", 16) or 16)
    cfg_width = _port_width(top_widths, common_ports["cfg_seqlen"])
    pos_width = _port_width(top_widths, common_ports["position"])
    input_addr_width = _port_width(top_widths, common_ports["read_addr"])
    generated_read_width = _port_width(top_widths, common_ports["read_data"], 256)
    generated_write_width = _port_width(top_widths, common_ports["write_data"], 256)
    bridge = _adapter_bridge(
        routes,
        target_tokens,
        cfg_width,
        pos_width,
        input_addr_width,
        generated_read_width,
        generated_write_width,
    )
    source = source.replace("SingleLayerSemanticHarness spatialacc_single_kernel(", "__OLD_INSTANCE__", 1)
    old_start = source.index("__OLD_INSTANCE__")
    old_end = source.index("\n\nalways @(posedge", old_start)
    instance = _instance(
        target_module,
        top_module,
        common_ports,
        routes,
        _runtime_interface(contract, top_ports),
    )
    source = source[:old_start] + bridge + instance + source[old_end:]
    # The generated top has explicit AXI-stream metadata ports; keep the
    # scheduler's token markers as registers instead of introducing a second
    # protocol adapter.
    source = source.replace(
        "reg [255:0] kernel_input_data_q;",
        "reg [255:0] kernel_input_data_q;\nreg kernel_input_start_q;\nreg kernel_input_last_q;",
        1,
    )
    source = source.replace(
        "kernel_input_data_q <= 256'd0;",
        "kernel_input_data_q <= 256'd0;\n    kernel_input_start_q <= 1'b0;\n    kernel_input_last_q <= 1'b0;",
        1,
    )
    source = source.replace(
        "trace_layer_output_complete <= 1'b0;\n    kernel_start_q <= 1'b0;",
        "trace_layer_output_complete <= 1'b0;\n    kernel_start_q <= 1'b0;\n    kernel_input_start_q <= 1'b0;\n    kernel_input_last_q <= 1'b0;",
        1,
    )
    source = source.replace(
        "      S_KERNEL_START: begin\n        kernel_start_q <= 1'b0;",
        "      S_KERNEL_START: begin\n        // GeneratedAxiDdrTop gates input ready with its active run bit.\n        // Start the core before the first DDR activation read.\n        kernel_start_q <= 1'b1;",
        1,
    )
    old_input_read = (
        "          kernel_input_valid_q <= 1'b1;\n"
        "          kernel_input_data_q <= c0_ddr4_s_axi_rdata[255:0];\n"
        "          state <= S_COMPUTE_INPUT_LO;\n"
    )
    new_input_read = (
        "          kernel_input_valid_q <= 1'b1;\n"
        "          kernel_input_start_q <=\n"
        "              (input_axi_index[10:0] % GENERATED_AXI_BEATS_PER_TOKEN) == 11'd0;\n"
        "          kernel_input_last_q <= 1'b0;\n"
        "          kernel_input_data_q <= c0_ddr4_s_axi_rdata[255:0];\n"
        "          state <= S_COMPUTE_INPUT_LO;\n"
    )
    if old_input_read not in source:
        raise ValueError("legacy scheduler input-read state did not match expected source")
    source = source.replace(old_input_read, new_input_read, 1)
    old_input_low = (
        "      S_COMPUTE_INPUT_LO: begin\n"
        "        if (kernel_input_valid_q && kernel_input_ready) begin\n"
        "          if ((input_axi_index == 20'd0) && !kernel_invocation_launched) begin\n"
        "            kernel_input_valid_q <= 1'b0;\n"
        "            state <= S_COMPUTE_ARM;\n"
        "          end else begin\n"
        "            kernel_input_data_q <= read_data_q[511:256];\n"
        "            state <= S_COMPUTE_INPUT_HI;\n"
        "          end\n"
        "        end\n"
        "      end\n"
    )
    new_input_low = (
        "      S_COMPUTE_INPUT_LO: begin\n"
        "        if (kernel_input_valid_q && kernel_input_ready) begin\n"
        "          kernel_input_valid_q <= 1'b0;\n"
        "          kernel_input_start_q <= 1'b0;\n"
        "          kernel_input_last_q <=\n"
        "              (input_axi_index[10:0] % GENERATED_AXI_BEATS_PER_TOKEN) ==\n"
        "              (GENERATED_AXI_BEATS_PER_TOKEN - 11'd1);\n"
        "          kernel_input_data_q <= read_data_q[511:256];\n"
        "          state <= S_COMPUTE_INPUT_HI;\n"
        "        end\n"
        "      end\n"
    )
    if old_input_low not in source:
        raise ValueError("legacy scheduler input-low state did not match expected source")
    source = source.replace(old_input_low, new_input_low, 1)
    old_input_high = (
        "          kernel_input_valid_q <= 1'b0;\n"
        "          input_axi_index <= input_axi_index + 20'd1;\n"
        "          state <= S_COMPUTE_RUN;"
    )
    new_input_high = (
        "          kernel_input_valid_q <= 1'b0;\n"
        "          kernel_input_start_q <= 1'b0;\n"
        "          kernel_input_last_q <= 1'b0;\n"
        "          input_axi_index <= input_axi_index + 20'd1;\n"
        "          state <= S_COMPUTE_RUN;"
    )
    if old_input_high not in source:
        raise ValueError("legacy scheduler input-high state did not match expected source")
    source = source.replace(old_input_high, new_input_high, 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(source, encoding="utf-8")
    manifest = {
        "schema_version": "spatialaccagent.compute_slot_adapter.v1",
        "status": "ready",
        "module": target_module,
        "generated_top_module": top_module,
        "generated_top": str(generated_top),
        "legacy_scheduler_source": str(legacy_adapter),
        "weight_route_count": len(routes),
        "weight_routes": routes,
        "uses_generated_top": True,
        "semantic_harness_substitution": False,
        "exact_port_abi_source": str(contract_path),
        "required_port_count": len(required_ports),
        "required_ports_present": True,
        "target_tokens": target_tokens,
        "axi_data_widths": {
            "scheduler_half_bits": 256,
            "generated_read_bits": generated_read_width,
            "generated_write_bits": generated_write_width,
            "read_adapter": "explicit_zero_extend_or_low_bits",
            "write_adapter": "explicit_low_bits_or_zero_extend",
        },
    }
    write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--legacy-adapter", type=Path, required=True)
    parser.add_argument("--generated-top", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(generate(args.contract, args.legacy_adapter, args.generated_top, args.output, args.manifest), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
