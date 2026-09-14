#!/usr/bin/env python3
"""Generate a board-shell runtime wrapper from a SpatialAccAgent contract.

The generator is deliberately contract-driven: board signal names, widths,
runtime addresses, and core module names come from the current run artifacts.
It does not encode a Qwen, OPT, or specific board assumption.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def nonblank(value: Any) -> bool:
    return value is not None and value != "" and value != [] and str(value).strip().lower() not in {"none", "null"}


def int_value(value: Any, default: int | None = None) -> int | None:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip(), 0)
        except ValueError:
            return default
    return default


def clean_ident(value: Any) -> str | None:
    if not nonblank(value):
        return None
    text = str(value).strip().strip("`'\"").rstrip("*").rstrip("_")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", text):
        return None
    return text


def width_range(width: int) -> str:
    return "" if width == 1 else f"[{width - 1}:0] "


def log2_bytes(byte_count: int) -> int:
    if byte_count <= 0 or byte_count & (byte_count - 1):
        raise ValueError(f"AXI beat bytes must be a power of two: {byte_count}")
    return int(math.log2(byte_count))


def parse_signal_width(text: str, signal: str) -> int | None:
    pattern = re.compile(rf"^[^\n;]*\b(?:input|output|inout)\b[^\n;]*\b{re.escape(signal)}\b[^\n;]*", re.M)
    match = pattern.search(text)
    if not match:
        return None
    range_match = re.search(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", match.group(0))
    if not range_match:
        return 1
    return abs(int(range_match.group(1)) - int(range_match.group(2))) + 1


def parse_module_name(text: str, preferred: str | None) -> str | None:
    if preferred and re.search(rf"\bmodule\s+{re.escape(preferred)}\b", text):
        return preferred
    match = re.search(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b", text)
    return match.group(1) if match else None


def first_region_bytes(contract: dict[str, Any], role: str) -> int | None:
    layout = contract.get("memory_layout", {}) if isinstance(contract.get("memory_layout"), dict) else {}
    for item in layout.get("regions", []) if isinstance(layout.get("regions"), list) else []:
        if isinstance(item, dict) and item.get("role") == role:
            return int_value(item.get("size_bytes"))
    return None


def sv_literal(value: Any, width: int = 64) -> str:
    text = str(value or "0").strip()
    try:
        number = int(text, 0)
    except ValueError:
        number = 0
    return f"{width}'h{number:x}"


def build_sv(contract: dict[str, Any], generated_top_text: str) -> tuple[str, dict[str, Any]]:
    board = contract.get("board_interface", {}) if isinstance(contract.get("board_interface"), dict) else {}
    runtime = contract.get("runtime_abi", {}) if isinstance(contract.get("runtime_abi"), dict) else {}
    core = contract.get("generated_core", {}) if isinstance(contract.get("generated_core"), dict) else {}
    params = core.get("params", {}) if isinstance(core.get("params"), dict) else {}

    prefix = clean_ident(board.get("signal_prefix"))
    clock = clean_ident(board.get("clock"))
    reset = clean_ident(board.get("reset"))
    calib = clean_ident(board.get("calibration_done"))
    top_module = clean_ident(core.get("top_module"))
    module_name = parse_module_name(generated_top_text, top_module)
    board_data_w = int_value(board.get("data_width_bits"))
    board_addr_w = int_value(board.get("addr_width_bits"), 64)
    board_id_w = int_value(board.get("id_width_bits"), 1)
    board_strb_w = int_value(board.get("wstrb_width_bits"))
    board_bytes = int_value(board.get("beat_bytes"), board_data_w // 8 if board_data_w else None)
    core_data_w = parse_signal_width(generated_top_text, "io_axiReadData")
    core_addr_w = parse_signal_width(generated_top_text, "io_axiReadAddr")
    cfg_seq_w = parse_signal_width(generated_top_text, "io_cfgSeqlen") or 16
    pos_w = parse_signal_width(generated_top_text, "io_position") or 16

    blockers = []
    for name, value in [
        ("board signal_prefix", prefix),
        ("board clock", clock),
        ("board reset", reset),
        ("generated core module", module_name),
        ("board data width", board_data_w),
        ("board address width", board_addr_w),
        ("board id width", board_id_w),
        ("board strobe width", board_strb_w),
        ("board beat bytes", board_bytes),
        ("core data width", core_data_w),
        ("core address width", core_addr_w),
    ]:
        if not nonblank(value):
            blockers.append(f"missing {name}")
    if blockers:
        return "", {"status": "fail", "blockers": blockers}
    assert prefix and clock and reset and module_name
    assert board_data_w and board_addr_w and board_id_w and board_strb_w and board_bytes and core_data_w and core_addr_w
    if board_data_w < core_data_w or board_data_w % core_data_w != 0:
        blockers.append(f"unsupported width adaptation: board_data_w={board_data_w} core_data_w={core_data_w}")
    if board_strb_w != board_data_w // 8:
        blockers.append(f"board strobe width {board_strb_w} does not match data bytes {board_data_w // 8}")
    if blockers:
        return "", {"status": "fail", "blockers": blockers}

    ratio = board_data_w // core_data_w
    ratio_w = max(1, (ratio - 1).bit_length())
    board_awsize = log2_bytes(board_bytes)
    core_bytes = core_data_w // 8
    input_bytes = first_region_bytes(contract, "activation_input") or board_bytes
    output_bytes = first_region_bytes(contract, "activation_output") or input_bytes
    total_core_beats = max(1, (input_bytes + core_bytes - 1) // core_bytes)
    total_board_reads = max(1, (input_bytes + board_bytes - 1) // board_bytes)
    total_board_writes = max(1, (output_bytes + board_bytes - 1) // board_bytes)
    hidden = int_value(params.get("hidden_size"), core_addr_w * ratio) or core_addr_w * ratio
    lanes = int_value(params.get("lanes"), 1) or 1
    token_core_beats = max(1, hidden // lanes)
    reset_active_low = reset.lower().endswith("_n")
    core_reset_expr = f"~{reset}" if reset_active_low else reset
    if calib:
        core_reset_expr = f"({core_reset_expr} | ~{calib})"
    calib_port = f"  input {calib},\n" if calib else ""
    calib_ready_expr = calib or "1'b1"
    if board_addr_w > 32:
        read_idx_addr_expr = f"{{{board_addr_w - 32}'d0, board_read_idx}}"
        write_idx_addr_expr = f"{{{board_addr_w - 32}'d0, board_write_idx}}"
    else:
        read_idx_addr_expr = f"board_read_idx[{board_addr_w - 1}:0]"
        write_idx_addr_expr = f"board_write_idx[{board_addr_w - 1}:0]"

    sv = f"""// Generated by SpatialAccAgent board_shell_wrapper_generator.py.
// schema: spatialaccagent.board_shell_wrapper.v0
// This RTL is a board-shell integration candidate. It is not acceptance
// evidence until runtime ABI, Vivado timing/DRC, bitstream, and board logs pass.
module SpatialAccBoardShellRuntimeTop #(
  parameter integer BOARD_DATA_W = {board_data_w},
  parameter integer CORE_DATA_W = {core_data_w},
  parameter integer BOARD_ADDR_W = {board_addr_w},
  parameter integer BOARD_ID_W = {board_id_w},
  parameter integer BOARD_STRB_W = {board_strb_w},
  parameter integer WIDTH_RATIO = {ratio},
  parameter integer CORE_ADDR_W = {core_addr_w},
  parameter integer TOTAL_CORE_BEATS = {total_core_beats},
  parameter integer TOTAL_BOARD_READS = {total_board_reads},
  parameter integer TOTAL_BOARD_WRITES = {total_board_writes},
  parameter integer TOKEN_CORE_BEATS = {token_core_beats}
) (
  input {clock},
  input {reset},
{calib_port}  input io_start,
  input [15:0] io_cfg_seqlen,
  input io_cfg_prefill,
  input io_cfg_single_query,
  input [{max(pos_w, 16) - 1}:0] io_position,
  input [63:0] io_input_base_addr,
  input [63:0] io_output_base_addr,
  output [{board_id_w - 1}:0] {prefix}_awid,
  output [{board_addr_w - 1}:0] {prefix}_awaddr,
  output [7:0] {prefix}_awlen,
  output [2:0] {prefix}_awsize,
  output [1:0] {prefix}_awburst,
  output {prefix}_awvalid,
  input {prefix}_awready,
  output [{board_data_w - 1}:0] {prefix}_wdata,
  output [{board_strb_w - 1}:0] {prefix}_wstrb,
  output {prefix}_wlast,
  output {prefix}_wvalid,
  input {prefix}_wready,
  input [{board_id_w - 1}:0] {prefix}_bid,
  input [1:0] {prefix}_bresp,
  input {prefix}_bvalid,
  output {prefix}_bready,
  output [{board_id_w - 1}:0] {prefix}_arid,
  output [{board_addr_w - 1}:0] {prefix}_araddr,
  output [7:0] {prefix}_arlen,
  output [2:0] {prefix}_arsize,
  output [1:0] {prefix}_arburst,
  output {prefix}_arvalid,
  input {prefix}_arready,
  input [{board_id_w - 1}:0] {prefix}_rid,
  input [{board_data_w - 1}:0] {prefix}_rdata,
  input [1:0] {prefix}_rresp,
  input {prefix}_rlast,
  input {prefix}_rvalid,
  output {prefix}_rready,
  output io_busy,
  output io_done,
  output reg io_error
);

  localparam [1:0] RD_IDLE = 2'd0, RD_AR = 2'd1, RD_WAIT = 2'd2, RD_STREAM = 2'd3;
  localparam [1:0] WR_IDLE = 2'd0, WR_AW = 2'd1, WR_W = 2'd2, WR_B = 2'd3;
  localparam [{ratio_w - 1}:0] RATIO_ZERO = {ratio_w}'d0;
  localparam [{ratio_w - 1}:0] RATIO_ONE = {ratio_w}'d1;
  localparam [{ratio_w - 1}:0] RATIO_LAST = {ratio_w}'d{ratio - 1};

  reg [1:0] rd_state;
  reg [1:0] wr_state;
  reg [31:0] board_read_idx;
  reg [31:0] core_read_idx;
  reg [31:0] board_write_idx;
  reg [{ratio_w - 1}:0] split_idx;
  reg [{ratio_w - 1}:0] pack_idx;
  reg [{board_data_w - 1}:0] read_buffer;
  reg [{board_data_w - 1}:0] write_buffer;
  reg started;

  wire [BOARD_ADDR_W-1:0] board_read_idx_addr = {read_idx_addr_expr};
  wire [BOARD_ADDR_W-1:0] board_write_idx_addr = {write_idx_addr_expr};
  wire core_reset = {core_reset_expr};
  wire read_done = core_read_idx >= 32'd{total_core_beats};
  wire writes_done = board_write_idx >= 32'd{total_board_writes};
  wire core_read_valid = (rd_state == RD_STREAM) && !read_done;
  wire core_read_ready;
  wire [{core_data_w - 1}:0] core_read_data = read_buffer[split_idx * CORE_DATA_W +: CORE_DATA_W];
  wire [{core_addr_w - 1}:0] core_read_addr = core_read_idx[CORE_ADDR_W-1:0];
  wire core_read_start = (core_read_idx % 32'd{token_core_beats}) == 32'd0;
  wire core_read_last = (core_read_idx % 32'd{token_core_beats}) == 32'd{token_core_beats - 1};
  wire core_write_valid;
  wire core_write_ready = (wr_state == WR_IDLE);
  wire [{core_data_w - 1}:0] core_write_data;
  wire [{core_addr_w - 1}:0] core_write_addr;
  wire core_write_start;
  wire core_write_last;
  wire core_busy;
  wire core_done;

  assign {prefix}_arid = {{BOARD_ID_W{{1'b0}}}};
  assign {prefix}_araddr = io_input_base_addr[BOARD_ADDR_W-1:0] + board_read_idx_addr * {board_addr_w}'d{board_bytes};
  assign {prefix}_arlen = 8'd0;
  assign {prefix}_arsize = 3'd{board_awsize};
  assign {prefix}_arburst = 2'b01;
  assign {prefix}_arvalid = (rd_state == RD_AR);
  assign {prefix}_rready = (rd_state == RD_WAIT);

  assign {prefix}_awid = {{BOARD_ID_W{{1'b0}}}};
  assign {prefix}_awaddr = io_output_base_addr[BOARD_ADDR_W-1:0] + board_write_idx_addr * {board_addr_w}'d{board_bytes};
  assign {prefix}_awlen = 8'd0;
  assign {prefix}_awsize = 3'd{board_awsize};
  assign {prefix}_awburst = 2'b01;
  assign {prefix}_awvalid = (wr_state == WR_AW);
  assign {prefix}_wdata = write_buffer;
  assign {prefix}_wstrb = {{BOARD_STRB_W{{1'b1}}}};
  assign {prefix}_wlast = 1'b1;
  assign {prefix}_wvalid = (wr_state == WR_W);
  assign {prefix}_bready = (wr_state == WR_B);

  assign io_busy = started && !io_done;
  assign io_done = started && read_done && core_done && writes_done && (wr_state == WR_IDLE);

  {module_name} core (
    .clock({clock}),
    .reset(core_reset),
    .io_start(io_start),
    .io_cfgSeqlen(io_cfg_seqlen[{cfg_seq_w - 1}:0]),
    .io_cfgPrefill(io_cfg_prefill),
    .io_cfgSingleQuery(io_cfg_single_query),
    .io_position(io_position[{pos_w - 1}:0]),
    .io_axiReadValid(core_read_valid),
    .io_axiReadReady(core_read_ready),
    .io_axiReadData(core_read_data),
    .io_axiReadAddr(core_read_addr),
    .io_axiReadStart(core_read_start),
    .io_axiReadLast(core_read_last),
    .io_axiWriteValid(core_write_valid),
    .io_axiWriteReady(core_write_ready),
    .io_axiWriteData(core_write_data),
    .io_axiWriteAddr(core_write_addr),
    .io_axiWriteStart(core_write_start),
    .io_axiWriteLast(core_write_last),
    .io_busy(core_busy),
    .io_done(core_done)
  );

  always @(posedge {clock}) begin
    if (core_reset) begin
      rd_state <= RD_IDLE;
      wr_state <= WR_IDLE;
      board_read_idx <= 32'd0;
      core_read_idx <= 32'd0;
      board_write_idx <= 32'd0;
      split_idx <= RATIO_ZERO;
      pack_idx <= RATIO_ZERO;
      read_buffer <= {{BOARD_DATA_W{{1'b0}}}};
      write_buffer <= {{BOARD_DATA_W{{1'b0}}}};
      started <= 1'b0;
      io_error <= 1'b0;
    end else begin
      if (io_start && {calib_ready_expr}) begin
        started <= 1'b1;
        rd_state <= RD_AR;
        board_read_idx <= 32'd0;
        core_read_idx <= 32'd0;
        board_write_idx <= 32'd0;
        split_idx <= RATIO_ZERO;
        pack_idx <= RATIO_ZERO;
        io_error <= 1'b0;
      end

      case (rd_state)
        RD_IDLE: begin
          if (started && !read_done) rd_state <= RD_AR;
        end
        RD_AR: begin
          if ({prefix}_arvalid && {prefix}_arready) rd_state <= RD_WAIT;
        end
        RD_WAIT: begin
          if ({prefix}_rvalid && {prefix}_rready) begin
            read_buffer <= {prefix}_rdata;
            if ({prefix}_rresp != 2'b00) io_error <= 1'b1;
            split_idx <= RATIO_ZERO;
            rd_state <= RD_STREAM;
          end
        end
        RD_STREAM: begin
          if (core_read_valid && core_read_ready) begin
            core_read_idx <= core_read_idx + 32'd1;
            if (split_idx == RATIO_LAST || core_read_idx == 32'd{total_core_beats - 1}) begin
              split_idx <= RATIO_ZERO;
              board_read_idx <= board_read_idx + 32'd1;
              rd_state <= (core_read_idx == 32'd{total_core_beats - 1}) ? RD_IDLE : RD_AR;
            end else begin
              split_idx <= split_idx + RATIO_ONE;
            end
          end
        end
      endcase

      case (wr_state)
        WR_IDLE: begin
          if (core_write_valid) begin
            write_buffer[pack_idx * CORE_DATA_W +: CORE_DATA_W] <= core_write_data;
            if (pack_idx == RATIO_LAST || core_write_last) begin
              pack_idx <= RATIO_ZERO;
              wr_state <= WR_AW;
            end else begin
              pack_idx <= pack_idx + RATIO_ONE;
            end
          end
        end
        WR_AW: begin
          if ({prefix}_awvalid && {prefix}_awready) wr_state <= WR_W;
        end
        WR_W: begin
          if ({prefix}_wvalid && {prefix}_wready) wr_state <= WR_B;
        end
        WR_B: begin
          if ({prefix}_bvalid && {prefix}_bready) begin
            if ({prefix}_bresp != 2'b00) io_error <= 1'b1;
            board_write_idx <= board_write_idx + 32'd1;
            write_buffer <= {{BOARD_DATA_W{{1'b0}}}};
            wr_state <= WR_IDLE;
          end
        end
      endcase
    end
  end
endmodule
"""
    manifest = {
        "status": "pass",
        "blockers": [],
        "module": "SpatialAccBoardShellRuntimeTop",
        "core_module": module_name,
        "board_signal_prefix": prefix,
        "board_data_width_bits": board_data_w,
        "core_data_width_bits": core_data_w,
        "width_ratio": ratio,
        "total_core_beats": total_core_beats,
        "total_board_reads": total_board_reads,
        "total_board_writes": total_board_writes,
        "token_core_beats": token_core_beats,
        "runtime_abi": {
            "control_protocol": runtime.get("control_protocol"),
            "ctrl_base": runtime.get("ctrl_base"),
            "ddr_base": runtime.get("ddr_base"),
            "output_abs": runtime.get("output_abs"),
        },
    }
    return sv, manifest


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate board-shell runtime wrapper from board_shell_contract.json")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--generated-top", type=Path, required=True)
    parser.add_argument("--out-rtl", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Output manifest/report JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []
    for label, path in [("contract", args.contract), ("generated_top", args.generated_top)]:
        exists = path.exists() and path.stat().st_size > 0
        checks.append({"name": f"{label}_exists", "path": str(path), "status": "pass" if exists else "fail"})
        if not exists:
            blockers.append(f"missing or empty {label}: {path}")
    contract = read_json(args.contract) if args.contract.exists() else {}
    generated_top_text = read_text(args.generated_top)
    if contract.get("status") not in {"ready_for_generation", "ready", "pass"}:
        blockers.append(f"board shell contract is not ready: {contract.get('status')}")
    sv = ""
    build_manifest: dict[str, Any] = {}
    if not blockers:
        sv, build_manifest = build_sv(contract, generated_top_text)
        blockers.extend(build_manifest.get("blockers", []))
    if not blockers:
        args.out_rtl.parent.mkdir(parents=True, exist_ok=True)
        args.out_rtl.write_text(sv, encoding="utf-8")
        checks.append({"name": "wrapper_rtl_written", "path": str(args.out_rtl), "status": "pass", "size_bytes": args.out_rtl.stat().st_size})
    report = {
        "schema_version": "spatialaccagent.board_shell_wrapper_manifest.v0",
        "status": "pass" if not blockers else "fail",
        "summary": "board-shell wrapper RTL generated" if not blockers else f"{len(blockers)} blocker(s)",
        "contract": str(args.contract),
        "generated_top": str(args.generated_top),
        "wrapper_rtl": str(args.out_rtl),
        "checks": checks,
        "blockers": blockers,
        "wrapper": build_manifest,
        "acceptance_policy": "This manifest proves wrapper generation only. Runtime ABI, Vivado timing/DRC, bitstream, and board runtime evidence are still required.",
    }
    write_json(args.out, report)
    if blockers:
        print(report["summary"], file=sys.stderr)
        return 1
    print(report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
