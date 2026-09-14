#!/usr/bin/env python3
"""Generate semantic testbench vectors from a real-model reference run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from accagent.framework.numeric_policy import numeric_comparison
from accagent.framework.board_reference_output import select_board_reference_output
from accagent.framework.board_validation_scope import resolve_board_validation_scope
from accagent.framework.semantic_runtime import (
    materialize_composite_runtime_stream,
    materialize_semantic_runtime_constants,
)
from accagent.framework.transcendental_contract import materialize_transcendental_contract
from accagent.framework.verification_evidence_contract import certificate_contract_errors
from accagent.framework.weight_layout import (
    build_stage_weight_layout,
    materialize_composite_weight_stream,
    materialize_stage_weight_stream,
)


SCHEMA_VERSION = "spatialaccagent.semantic_testbench_manifest.v1"


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "stage"


def scalar(stage: dict[str, Any], name: str, default: int) -> int:
    bound = stage.get("bound_params", {}) if isinstance(stage.get("bound_params"), dict) else {}
    row = bound.get(name)
    if isinstance(row, dict) and row.get("value") is not None:
        try:
            return int(row["value"])
        except (TypeError, ValueError):
            pass
    numeric = stage.get("numeric_contract", {}) if isinstance(stage.get("numeric_contract"), dict) else {}
    if numeric.get(name) is not None:
        try:
            return int(numeric[name])
        except (TypeError, ValueError):
            pass
    return default


def numeric_comparison_policy(
    policy: dict[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    return numeric_comparison(policy)


def tensor_words(tensor: Any, bits: int) -> list[int]:
    import torch

    value = tensor.detach().cpu().contiguous()
    if bits == 16:
        raw = value.to(torch.float16).view(torch.int16).reshape(-1).tolist()
        return [int(item) & 0xFFFF for item in raw]
    if bits == 32:
        raw = value.to(torch.float32).view(torch.int32).reshape(-1).tolist()
        return [int(item) & 0xFFFFFFFF for item in raw]
    raise ValueError(f"unsupported floating-point testbench width: {bits}")


def write_packed_memh(path: Path, tensor: Any, bits: int, lanes: int) -> dict[str, Any]:
    words = tensor_words(tensor, bits)
    if len(words) % lanes:
        raise ValueError(f"tensor word count {len(words)} is not divisible by lanes={lanes}")
    mask = (1 << bits) - 1
    width = bits * lanes
    digits = (width + 3) // 4
    lines = []
    for offset in range(0, len(words), lanes):
        packed = 0
        for lane, word in enumerate(words[offset : offset + lanes]):
            packed |= (word & mask) << (lane * bits)
        lines.append(f"{packed:0{digits}x}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "bits": bits,
        "lanes": lanes,
        "beats": len(lines),
        "tensor_shape": list(tensor.shape),
        "encoding": f"ieee_fp{bits}_lane0_lsb",
    }


def sv_identifier(value: Any, label: str) -> str:
    text = str(value or "")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", text):
        raise ValueError(f"invalid SystemVerilog identifier for {label}: {text!r}")
    return text


def verified_source_files(harness: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in harness.get("source_files", []):
        if not isinstance(item, dict):
            errors.append("harness source-file entry is not an object")
            continue
        path = Path(str(item.get("path") or ""))
        declared = str(item.get("sha256") or "")
        if not path.is_file():
            errors.append(f"harness source file is missing: {path}")
            continue
        actual = sha256_file(path)
        if actual != declared:
            errors.append(f"harness source hash mismatch: {path}")
            continue
        rows.append({"path": str(path), "sha256": actual})
    if not rows:
        errors.append("harness has no hash-verified source files")
    return rows, errors


def write_weight_stream(path: Path, bindings: list[dict[str, Any]], bits: int = 16) -> dict[str, Any]:
    import torch

    if bits != 16:
        raise ValueError(f"semantic weight stream currently requires fp16 words, got {bits}")
    words: list[int] = []
    tensor_layout = []
    for tensor_id, binding in enumerate(bindings):
        tensor_path = Path(str(binding.get("path") or ""))
        if not tensor_path.is_file() or sha256_file(tensor_path) != binding.get("file_sha256"):
            raise ValueError(f"real-weight tensor file/hash mismatch: {tensor_path}")
        tensor = torch.load(tensor_path, map_location="cpu", weights_only=True)
        values = tensor_words(tensor, bits)
        if len(values) % 2:
            values.append(0)
        offset = len(words)
        for index in range(0, len(values), 2):
            words.append(values[index] | (values[index + 1] << 16))
        tensor_layout.append(
            {
                "tensor_id": tensor_id,
                "tensor": binding.get("tensor"),
                "tensor_sha256": binding.get("sha256"),
                "word_offset": offset,
                "word_count": len(words) - offset,
                "packing": "two_ieee_fp16_values_per_u32_lane0_lsb",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{word:08x}\n" for word in words), encoding="ascii")
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "word_bits": 32,
        "word_count": len(words),
        "tensor_layout": tensor_layout,
    }


def semantic_harness_tb(
    *,
    tb_module: str,
    harness: dict[str, Any],
    input_vectors: list[dict[str, Any]],
    expected_output: dict[str, Any],
    output_path: Path,
    weight_stream: dict[str, Any] | None,
    runtime_stream: dict[str, Any] | None,
) -> str:
    top_module = sv_identifier(harness.get("top_module"), "harness top module")
    interface = harness.get("interface", {}) if isinstance(harness.get("interface"), dict) else {}
    clock_port = sv_identifier(interface.get("clock_port"), "clock port")
    reset_port = sv_identifier(interface.get("reset_port"), "reset port")
    input_ports = interface.get("inputs", []) if isinstance(interface.get("inputs"), list) else []
    output_port = interface.get("output", {}) if isinstance(interface.get("output"), dict) else {}
    if len(input_ports) != len(input_vectors):
        raise ValueError(f"harness input count {len(input_ports)} does not match vectors {len(input_vectors)}")

    declarations = ["  reg clock = 0;", "  reg reset = 1;"]
    connections = [f"    .{clock_port}(clock)", f"    .{reset_port}(reset)"]
    drive_lines: list[str] = []
    handshake_lines: list[str] = []
    done_terms: list[str] = []
    for index, (port, vector) in enumerate(zip(input_ports, input_vectors)):
        if not isinstance(port, dict):
            raise ValueError(f"input interface {index} is not an object")
        width = int(vector["bits"]) * int(vector["lanes"])
        declared_width = int(port.get("data_width_bits") or 0)
        if declared_width != width:
            raise ValueError(f"input {index} width {declared_width} does not match encoded vector width {width}")
        valid_port = sv_identifier(port.get("valid_port"), f"input {index} valid")
        ready_port = sv_identifier(port.get("ready_port"), f"input {index} ready")
        data_port = sv_identifier(port.get("data_port"), f"input {index} data")
        declarations.extend(
            [
                f"  reg [{width - 1}:0] input_mem_{index} [0:{int(vector['beats']) - 1}];",
                f"  reg input_{index}_valid = 0;",
                f"  wire input_{index}_ready;",
                f"  reg [{width - 1}:0] input_{index}_data = 0;",
                f"  integer input_{index}_accepted = 0;",
            ]
        )
        connections.extend(
            [
                f"    .{valid_port}(input_{index}_valid)",
                f"    .{ready_port}(input_{index}_ready)",
                f"    .{data_port}(input_{index}_data)",
            ]
        )
        last_port = port.get("last_port")
        if last_port:
            last_port = sv_identifier(last_port, f"input {index} last")
            declarations.append(f"  reg input_{index}_last = 0;")
            connections.append(f"    .{last_port}(input_{index}_last)")
            drive_lines.append(f"      input_{index}_last = input_{index}_accepted == {int(vector['beats']) - 1};")
        drive_lines.extend(
            [
                f"      input_{index}_valid = input_{index}_accepted < {int(vector['beats'])};",
                f"      if (input_{index}_accepted < {int(vector['beats'])}) input_{index}_data = input_mem_{index}[input_{index}_accepted];",
            ]
        )
        handshake_lines.append(
            f"      if (input_{index}_valid && input_{index}_ready) input_{index}_accepted = input_{index}_accepted + 1;"
        )
        done_terms.append(f"input_{index}_accepted == {int(vector['beats'])}")

    output_width = int(expected_output["bits"]) * int(expected_output["lanes"])
    if int(output_port.get("data_width_bits") or 0) != output_width:
        raise ValueError("harness output width does not match encoded expected-output width")
    output_valid_port = sv_identifier(output_port.get("valid_port"), "output valid")
    output_ready_port = sv_identifier(output_port.get("ready_port"), "output ready")
    output_data_port = sv_identifier(output_port.get("data_port"), "output data")
    declarations.extend(
        [
            "  wire output_valid;",
            "  reg output_ready = 1;",
            f"  wire [{output_width - 1}:0] output_data;",
            "  integer output_produced = 0;",
            "  integer output_fd;",
            "  integer cycles = 0;",
        ]
    )
    connections.extend(
        [
            f"    .{output_valid_port}(output_valid)",
            f"    .{output_ready_port}(output_ready)",
            f"    .{output_data_port}(output_data)",
        ]
    )

    setup_lines: list[str] = []
    for index, vector in enumerate(input_vectors):
        declarations.append(f"  string input_path_{index};")
        setup_lines.extend(
            [
                f'    if (!$value$plusargs("INPUT_{index}_MEMH=%s", input_path_{index}))',
                f'      input_path_{index} = "{vector["path"]}";',
                f"    $readmemh(input_path_{index}, input_mem_{index});",
            ]
        )
    weight_setup: list[str] = []
    weight_drive: list[str] = []
    weight_done = "1'b1"
    loader = interface.get("weight_loader", {}) if isinstance(interface.get("weight_loader"), dict) else {}
    if weight_stream:
        valid_port = sv_identifier(loader.get("valid_port"), "weight valid")
        ready_port = sv_identifier(loader.get("ready_port"), "weight ready")
        data_port = sv_identifier(loader.get("data_port"), "weight data")
        addr_port = sv_identifier(loader.get("addr_port"), "weight address")
        last_port = sv_identifier(loader.get("last_port"), "weight last")
        if int(loader.get("data_width_bits") or 0) != 32:
            raise ValueError("semantic harness weight loader must consume 32-bit packed fp16 words")
        addr_width = int(loader.get("addr_width_bits") or 0)
        if addr_width <= 0:
            raise ValueError("semantic harness weight-loader address width is missing")
        count = int(weight_stream["word_count"])
        declarations.extend(
            [
                f"  reg [31:0] weight_mem [0:{count - 1}];",
                "  string weight_path;",
                "  reg weight_valid = 0;",
                "  wire weight_ready;",
                "  reg [31:0] weight_data = 0;",
                f"  reg [{addr_width - 1}:0] weight_addr = 0;",
                "  reg weight_last = 0;",
                "  integer weight_accepted = 0;",
                "  integer weight_stall_cycles = 0;",
            ]
        )
        connections.extend(
            [
                f"    .{valid_port}(weight_valid)",
                f"    .{ready_port}(weight_ready)",
                f"    .{data_port}(weight_data)",
                f"    .{addr_port}(weight_addr)",
                f"    .{last_port}(weight_last)",
            ]
        )
        weight_setup.extend(
            [
                '    if (!$value$plusargs("WEIGHT_MEMH=%s", weight_path))',
                f'      weight_path = "{weight_stream["path"]}";',
                "    $readmemh(weight_path, weight_mem);",
            ]
        )
        weight_drive.extend(
            [
                f"    while (weight_accepted < {count}) begin",
                "      @(negedge clock);",
                "      weight_valid = 1;",
                "      weight_data = weight_mem[weight_accepted];",
                "      weight_addr = weight_accepted;",
                f"      weight_last = weight_accepted == {count - 1};",
                "      @(posedge clock);",
                "      if (weight_valid && weight_ready) begin",
                "        weight_accepted = weight_accepted + 1;",
                "        weight_stall_cycles = 0;",
                "      end else begin",
                "        weight_stall_cycles = weight_stall_cycles + 1;",
                "        if (weight_stall_cycles >= 10000000)",
                "          $fatal(1, \"real-weight loader made no progress\");",
                "      end",
                "    end",
                "    @(negedge clock);",
                "    weight_valid = 0;",
                "    weight_last = 0;",
            ]
        )
        weight_done = f"weight_accepted == {count}"

    runtime_setup: list[str] = []
    runtime_drive: list[str] = []
    runtime_done = "1'b1"
    runtime_loader = interface.get("runtime_loader", {}) if isinstance(interface.get("runtime_loader"), dict) else {}
    if runtime_stream:
        valid_port = sv_identifier(runtime_loader.get("valid_port"), "runtime constant valid")
        ready_port = sv_identifier(runtime_loader.get("ready_port"), "runtime constant ready")
        data_port = sv_identifier(runtime_loader.get("data_port"), "runtime constant data")
        addr_port = sv_identifier(runtime_loader.get("addr_port"), "runtime constant address")
        last_port = sv_identifier(runtime_loader.get("last_port"), "runtime constant last")
        if int(runtime_loader.get("data_width_bits") or 0) != 32:
            raise ValueError("semantic harness runtime-constant loader must consume 32-bit words")
        addr_width = int(runtime_loader.get("addr_width_bits") or 0)
        if addr_width <= 0:
            raise ValueError("semantic harness runtime-constant loader address width is missing")
        count = int(runtime_stream["word_count"])
        declarations.extend(
            [
                f"  reg [31:0] runtime_mem [0:{count - 1}];",
                "  string runtime_path;",
                "  reg runtime_valid = 0;",
                "  wire runtime_ready;",
                "  reg [31:0] runtime_data = 0;",
                f"  reg [{addr_width - 1}:0] runtime_addr = 0;",
                "  reg runtime_last = 0;",
                "  integer runtime_accepted = 0;",
                "  integer runtime_stall_cycles = 0;",
            ]
        )
        connections.extend(
            [
                f"    .{valid_port}(runtime_valid)",
                f"    .{ready_port}(runtime_ready)",
                f"    .{data_port}(runtime_data)",
                f"    .{addr_port}(runtime_addr)",
                f"    .{last_port}(runtime_last)",
            ]
        )
        runtime_setup.extend(
            [
                '    if (!$value$plusargs("RUNTIME_MEMH=%s", runtime_path))',
                f'      runtime_path = "{runtime_stream["path"]}";',
                "    $readmemh(runtime_path, runtime_mem);",
            ]
        )
        runtime_drive.extend(
            [
                f"    while (runtime_accepted < {count}) begin",
                "      @(negedge clock);",
                "      runtime_valid = 1;",
                "      runtime_data = runtime_mem[runtime_accepted];",
                "      runtime_addr = runtime_accepted;",
                f"      runtime_last = runtime_accepted == {count - 1};",
                "      @(posedge clock);",
                "      if (runtime_valid && runtime_ready) begin",
                "        runtime_accepted = runtime_accepted + 1;",
                "        runtime_stall_cycles = 0;",
                "      end else begin",
                "        runtime_stall_cycles = runtime_stall_cycles + 1;",
                "        if (runtime_stall_cycles >= 10000000)",
                "          $fatal(1, \"runtime-constant loader made no progress\");",
                "      end",
                "    end",
                "    @(negedge clock);",
                "    runtime_valid = 0;",
                "    runtime_last = 0;",
            ]
        )
        runtime_done = f"runtime_accepted == {count}"

    for item in interface.get("constant_ports", []):
        if not isinstance(item, dict):
            continue
        port = sv_identifier(item.get("port"), "constant port")
        value = str(item.get("value") or "")
        if not re.fullmatch(r"[0-9A-Fa-f_xXzZ?'bdhoBDHO+\-]+", value):
            raise ValueError(f"unsafe SystemVerilog constant for {port}: {value!r}")
        connections.append(f"    .{port}({value})")

    start_lines: list[str] = []
    start_port = interface.get("start_port")
    if start_port:
        start_port = sv_identifier(start_port, "start port")
        declarations.append("  reg start = 0;")
        connections.append(f"    .{start_port}(start)")
        start_lines = ["    start = 1;", "    @(posedge clock);", "    start = 0;"]

    connection_text = ",\n".join(connections)
    declarations.append("  string output_path;")
    return "\n".join(
        [
            "`timescale 1ns/1ps",
            f"module {tb_module};",
            *declarations,
            "",
            f"  {top_module} dut (",
            connection_text,
            "  );",
            "  always #5 clock = ~clock;",
            "",
            "  initial begin",
            *setup_lines,
            *weight_setup,
            *runtime_setup,
            '    if (!$value$plusargs("OUTPUT_MEMH=%s", output_path))',
            f'      output_path = "{output_path}";',
            '    output_fd = $fopen(output_path, "w");',
            "    if (!output_fd) $fatal(1, \"cannot open semantic RTL output capture\");",
            "    repeat (8) @(posedge clock);",
            "    reset = 0;",
            *weight_drive,
            f"    if (!({weight_done})) $fatal(1, \"real-weight load did not complete\");",
            *runtime_drive,
            f"    if (!({runtime_done})) $fatal(1, \"runtime-constant load did not complete\");",
            *start_lines,
            f"    while (cycles < 10000000 && output_produced < {int(expected_output['beats'])}) begin",
            "      @(negedge clock);",
            *drive_lines,
            "      @(posedge clock);",
            *handshake_lines,
            "      if (output_valid && output_ready) begin",
            "        $fdisplay(output_fd, \"%0h\", output_data);",
            "        output_produced = output_produced + 1;",
            "      end",
            "      cycles = cycles + 1;",
            "    end",
            f"    if (!({' && '.join(done_terms)}) || output_produced != {int(expected_output['beats'])})",
            "      $fatal(1, \"semantic harness timeout or output-shape mismatch\");",
            "    @(negedge clock);",
            "    $fclose(output_fd);",
            "    $display(\"PASS semantic harness real-weight execution beats=%0d cycles=%0d\", output_produced, cycles);",
            "    $finish;",
            "  end",
            "endmodule",
            "",
        ]
    )


def load_reference_tensors(reference: dict[str, Any]) -> tuple[Any, dict[str, dict[str, Any]]]:
    import torch

    random_input = torch.load(reference["input"]["path"], map_location="cpu", weights_only=True)
    records: dict[str, dict[str, Any]] = {}
    for row in reference.get("reference", {}).get("operator_records", []):
        if not isinstance(row, dict) or not row.get("module") or not row.get("tensor_path"):
            continue
        data = torch.load(row["tensor_path"], map_location="cpu", weights_only=True)
        if isinstance(data, dict):
            records[str(row["module"])] = data
    return random_input, records


def semantic_stage_map(reference: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = reference.get("reference", {}).get("semantic_stage_map", {})
    if not isinstance(value, dict) or not value:
        raise ValueError("target-model reference has no adapter-provided semantic stage map")
    return {str(key): row for key, row in value.items() if isinstance(row, dict)}


def stage_tensors(
    op: str,
    random_input: Any,
    records: dict[str, dict[str, Any]],
    stage_map: dict[str, dict[str, Any]],
) -> tuple[list[Any], Any]:
    contract = stage_map.get(op)
    if not isinstance(contract, dict):
        raise ValueError(f"model semantic adapter has no mapping for pipeline op {op}")

    def value(selector: dict[str, Any]) -> Any:
        if selector.get("source") == "accelerator_input":
            return random_input
        name = str(selector.get("record") or "")
        key = str(selector.get("value") or "")
        tensor = records.get(name, {}).get(key)
        if tensor is None:
            raise ValueError(f"reference tensor is missing: {name}.{key}")
        return tensor

    input_selectors = contract.get("inputs", []) if isinstance(contract.get("inputs"), list) else []
    expected_selector = contract.get("expected", {}) if isinstance(contract.get("expected"), dict) else {}
    if not input_selectors or not expected_selector:
        raise ValueError(f"semantic mapping for {op} has no inputs or expected selector")
    return [value(selector) for selector in input_selectors if isinstance(selector, dict)], value(expected_selector)


def required_weights(op: str, stage_map: dict[str, dict[str, Any]]) -> list[str]:
    contract = stage_map.get(op, {})
    values = contract.get("required_weight_suffixes", []) if isinstance(contract, dict) else []
    if not isinstance(values, list):
        raise ValueError(f"semantic mapping required_weight_suffixes is malformed for {op}")
    return [str(value) for value in values]


def stream_metadata_contract() -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.semantic_stream_metadata.v1",
        "scope": "all operator-leaf harness input streams",
        "tensor_order": "row_major_with_feature_axis_last",
        "preconditions": [
            "each input tensor has at least one axis",
            "tensor_shape[-1] is divisible by encoded lanes",
            "each input stream has an independent accepted-beat counter",
        ],
        "derived_values": {
            "beats_per_logical_vector": "tensor_shape[-1] / lanes",
            "logical_vector_count": "product(tensor_shape[:-1])",
            "total_beats": "beats_per_logical_vector * logical_vector_count",
            "logical_vector_index": "accepted_beat_index / beats_per_logical_vector",
            "feature_beat_index": "accepted_beat_index % beats_per_logical_vector",
        },
        "internal_streambeat_fields": {
            "data": "external data_port unchanged",
            "st": "feature_beat_index == 0",
            "addr": "accepted_beat_index in row-major global-beat order",
            "last": "feature_beat_index == beats_per_logical_vector - 1",
        },
        "position_index_when_required": (
            "logical_vector_index modulo configured sequence length; captured runtime position/rope tables remain "
            "authoritative for semantic values"
        ),
        "counter_reset": "synchronous DUT reset; counters remain zero until all required loaders complete",
        "transaction_order": [
            "assert and release reset",
            "load all real-weight words in ascending address order",
            "load all runtime-constant words in ascending address order",
            "pulse start for one cycle when the DUT exposes start_port",
            "accept input beats and advance a counter only on valid && ready",
        ],
        "testbench_boundary": (
            "the generated testbench drives only declared ready/valid/data ports; the harness must synthesize "
            "internal StreamBeat st/addr/last metadata from this contract"
        ),
    }


def harness_elaboration_contract(run_dir: Path) -> dict[str, Any]:
    root = run_dir / "generated" / "semantic_harness"
    return {
        "schema_version": "spatialaccagent.semantic_harness_elaboration.v1",
        "agent_source_root": str(
            run_dir
            / "generated"
            / "chisel"
            / "src"
            / "main"
            / "scala"
            / "spatialaccagent"
            / "semantic_harness"
        ),
        "emitted_source_root": str(root),
        "stage_source_directory": f"{root}/<stage_id>",
        "isolation": (
            "each stage is elaborated into its own stage_source_directory; duplicate dependency module names "
            "may exist across stage directories but not within one directory"
        ),
        "validation": (
            "one approved runMain may elaborate every stage sequentially; the executor recursively discovers "
            "all .sv/.v files under each declared source_directory after runMain, rejects duplicate module "
            "definitions within that directory, recomputes hashes, and supplies only that stage's files to VCS"
        ),
        "existing_root_sv_policy": (
            "pre-existing emitted SystemVerilog outside the declared stage source_directory is not a semantic "
            "harness source and may be stale; elaborate from the compile-validated generated Scala baseline"
        ),
    }


def binding_requirements(
    run_dir: Path,
    reference: dict[str, Any],
    pipeline: dict[str, Any],
    pipeline_path: Path,
    numeric_policy: dict[str, Any],
    reference_path: Path,
    numeric_policy_path: Path,
    accelerator_catalog: dict[str, Any],
    accelerator_catalog_path: Path,
    transcendental_contract: dict[str, Any],
    semantic_runtime_contract: dict[str, Any],
    board_scope: dict[str, Any],
) -> dict[str, Any]:
    stage_map = semantic_stage_map(reference)
    stage_rows = []
    weights = reference.get("weights", {}).get("layer_0_tensor_bindings", [])
    by_suffix = {
        str(row.get("parameter_suffix") or ""): row
        for row in weights
        if isinstance(row, dict)
    }
    for stage in pipeline.get("stages", []):
        if not isinstance(stage, dict):
            continue
        op = str(stage.get("op") or "")
        names = required_weights(op, stage_map)
        bindings = [by_suffix[name] for name in names if name in by_suffix]
        if len(bindings) != len(names):
            missing = sorted(set(names) - set(by_suffix))
            raise ValueError(f"{stage.get('stage_id')}: real target weights are missing {missing}")
        weight_layout = build_stage_weight_layout(stage, stage_map.get(op, {}), bindings, numeric_policy)
        runtime_stream = next(
            (
                row
                for row in semantic_runtime_contract.get("streams", [])
                if isinstance(row, dict) and str(row.get("consumer_op") or "") == op
            ),
            None,
        )
        stage_rows.append(
            {
                "stage_id": stage.get("stage_id"),
                "op": stage.get("op"),
                "numeric_contract": stage.get("numeric_contract", {}),
                "required_tensors": [
                    {
                        "tensor": row.get("tensor"),
                        "sha256": row.get("sha256"),
                        "shape": row.get("shape"),
                        "parameter_suffix": row.get("parameter_suffix"),
                        "path": row.get("path"),
                        "file_sha256": row.get("file_sha256"),
                    }
                    for name in names
                    for row in [by_suffix.get(name, {})]
                ],
                "weight_layout": weight_layout,
                "weight_layout_contract_sha256": weight_layout.get("contract_sha256"),
                "runtime_constant_stream": runtime_stream,
                "runtime_constant_contract_sha256": (
                    runtime_stream.get("contract_sha256") if isinstance(runtime_stream, dict) else None
                ),
                "harness_required": True,
            }
        )
    validation_layer_indices = board_scope.get("validation_layer_indices")
    if (
        not isinstance(validation_layer_indices, list)
        or not validation_layer_indices
        or any(isinstance(value, bool) or not isinstance(value, int) for value in validation_layer_indices)
    ):
        raise ValueError("board validation scope has no valid layer indices")
    validation_layers = set(validation_layer_indices)
    covers_full_model = board_scope.get("covers_full_model") is True
    catalog_tensors = [
        row
        for row in accelerator_catalog.get("tensors", [])
        if isinstance(row, dict)
    ]
    missing_layer_metadata = [
        row for row in catalog_tensors if not isinstance(row.get("layer_index"), int)
    ]
    if missing_layer_metadata and not covers_full_model:
        raise ValueError(
            "partial board validation requires layer-indexed accelerator weight catalog tensors"
        )
    board_tensors = [
        row
        for row in catalog_tensors
        if covers_full_model or row.get("layer_index") in validation_layers
    ]
    if not board_tensors:
        raise ValueError("board validation scope selects no accelerator weight tensors")
    if not covers_full_model and {
        row.get("layer_index") for row in board_tensors
    } != validation_layers:
        raise ValueError("board validation scope is missing required layer weight tensors")
    return {
        "schema_version": "spatialaccagent.dut_weight_binding_requirements.v1",
        "status": "requirements",
        "source_reference_manifest": str(reference_path),
        "source_reference_sha256": sha256_file(reference_path),
        "source_checkpoint_sha256": reference.get("weights", {}).get("source_checkpoint_sha256"),
        "pipeline_plan": str(pipeline_path),
        "pipeline_plan_sha256": sha256_file(pipeline_path),
        "accelerator_scope": "transformer_blocks_only",
        "accelerator_weight_catalog": str(accelerator_catalog_path),
        "accelerator_weight_catalog_sha256": sha256_file(accelerator_catalog_path),
        "model_semantic_adapter_sha256": reference.get("reference", {}).get("semantic_adapter", {}).get("sha256"),
        "numeric_policy": str(numeric_policy_path),
        "numeric_policy_sha256": sha256_file(numeric_policy_path),
        "transcendental_approximation_contract": {
            "path": transcendental_contract.get("path"),
            "file_sha256": transcendental_contract.get("file_sha256"),
            "contract_sha256": transcendental_contract.get("contract_sha256"),
            "status": transcendental_contract.get("status"),
        },
        "semantic_runtime_constant_contract": {
            "path": semantic_runtime_contract.get("path"),
            "file_sha256": semantic_runtime_contract.get("file_sha256"),
            "contract_sha256": semantic_runtime_contract.get("contract_sha256"),
            "status": semantic_runtime_contract.get("status"),
        },
        "required_manifest_fields": {
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "source_checkpoint_sha256": "must equal this requirements artifact",
            "source_reference_sha256": "must equal this requirements artifact",
            "numeric_policy_sha256": "must equal this requirements artifact",
            "model_semantic_adapter_sha256": "must equal this requirements artifact",
            "scope_coverage_complete": True,
            "dut_consumes_bound_weights": True,
            "default_or_identity_weight_fallback_disabled": True,
            "consumed_tensor_hashes": "must cover all required tensors",
            "stage_harnesses": "one hash-verified semantic harness per pipeline stage",
            "single_layer_harness": "hash-verified connected-layer semantic harness",
        },
        "standard_harness_interface": {
            "required": ["clock_port", "reset_port", "inputs", "output"],
            "input_entry": ["valid_port", "ready_port", "data_port", "data_width_bits"],
            "output_entry": ["valid_port", "ready_port", "data_port", "data_width_bits"],
            "weight_loader_when_weights_exist": [
                "valid_port",
                "ready_port",
                "data_port",
                "data_width_bits=32",
                "addr_port",
                "addr_width_bits",
                "last_port",
            ],
            "runtime_loader_when_runtime_constants_exist": [
                "valid_port",
                "ready_port",
                "data_port",
                "data_width_bits=32",
                "addr_port",
                "addr_width_bits",
                "last_port",
            ],
            "source_directory": (
                "preferred absolute per-stage directory under generated/semantic_harness; executor discovers and "
                "hashes all Verilog/SystemVerilog files after elaboration"
            ),
            "source_files": (
                "optional explicit absolute paths; finalized manifest always contains executor-recomputed sha256"
            ),
        },
        "stream_metadata_contract": stream_metadata_contract(),
        "harness_elaboration_contract": harness_elaboration_contract(run_dir),
        "canonical_weight_stream_contract": {
            "schema_version": "spatialaccagent.canonical_weight_stream_contract.v1",
            "word_bits": 32,
            "stage_stream_order": "weight_layout.storage_targets list order",
            "target_word_order": "port write address ascending, then 32-bit word index ascending within the port data beat",
            "word_zero_is_lsb_within_port_write": True,
            "source_values": "real checkpoint tensors rounded to numeric-policy weight_dtype before any declared value-preserving storage cast",
            "linear_source_axis_order": ["output_feature", "input_feature"],
            "linear_tile_order": ["out_beat", "in_beat", "out_lane", "in_lane"],
            "qkv_fusion": "adapter/canonical target source_order concatenated on output_feature axis before tiling",
            "generated_by": "accagent.framework.weight_layout.materialize_stage_weight_stream",
            "rtl_or_golden_outputs_used": False,
        },
        "agent_manifest_schema": {
            "schema_version": "spatialaccagent.dut_weight_binding_manifest_agent_input.v1",
            "top_level_required_from_agent": ["stage_harnesses"],
            "top_level_required_from_agent_by_scope": {
                "operator_leaf_closure": ["stage_harnesses"],
                "single_layer_closure": ["stage_harnesses", "single_layer_harness"],
            },
            "top_level_materialized_by_framework": [
                "schema_version",
                "status",
                "accelerator_scope",
                "source_checkpoint_sha256",
                "source_reference_sha256",
                "numeric_policy_sha256",
                "model_semantic_adapter_sha256",
                "scope_coverage_complete",
                "dut_consumes_bound_weights",
                "default_or_identity_weight_fallback_disabled",
                "consumed_tensor_hashes",
            ],
            "stage_harness_entry_required": [
                "top_module",
                "source_directory or source_files",
                "consumed_tensor_hashes",
                "default_or_identity_weight_fallback_disabled",
                "weight_layout_contract_sha256",
                "interface",
            ],
            "stage_harness_runtime_fields_required_only_when_declared": [
                "runtime_constant_contract_sha256",
                "interface.runtime_loader",
            ],
            "single_layer_harness_entry_required": [
                "top_module",
                "source_directory or source_files",
                "consumed_tensor_hashes",
                "default_or_identity_weight_fallback_disabled",
                "weight_layout_contract_sha256",
                "runtime_constant_contract_sha256",
                "connected_weight_stream_contract_sha256",
                "connected_runtime_stream_contract_sha256",
                "pipeline_plan_sha256",
                "pipeline_overlap_trace_contract_sha256",
                "loader_route_contract",
                "interface",
            ],
            "path_policy": "source_directory and source_files paths must be absolute",
            "source_directory": (
                "preferred isolated per-stage directory under generated/semantic_harness; framework recursively "
                "discovers .sv/.v files and materializes source_files"
            ),
            "source_files": (
                "optional list of absolute generated harness/DUT Verilog paths or {path,sha256}; framework "
                "recomputes hashes"
            ),
            "interface": {
                "required": ["clock_port", "reset_port", "inputs", "output"],
                "weight_loader_required_only_for_weighted_stage": [
                    "valid_port",
                    "ready_port",
                    "data_port",
                    "data_width_bits=32",
                    "addr_port",
                    "addr_width_bits",
                    "last_port",
                ],
                "runtime_loader_required_only_for_stage_with_runtime_constants": [
                    "valid_port",
                    "ready_port",
                    "data_port",
                    "data_width_bits=32",
                    "addr_port",
                    "addr_width_bits",
                    "last_port",
                ],
            },
            "single_layer_harness": (
                "omitted for operator-leaf closure; required for single_layer_closure and must instantiate the "
                "real connected Transformer-block DUT"
            ),
        },
        "agent_manifest_example": {
            "schema_version": "spatialaccagent.dut_weight_binding_manifest_agent_input.v1",
            "stage_harnesses": {
                "<stage_id>": {
                    "top_module": "<elaborated_harness_top_module>",
                    "source_directory": str(
                        run_dir / "generated" / "semantic_harness" / "<stage_id>"
                    ),
                    "consumed_tensor_hashes": ["<every required_tensors[].sha256 for this stage>"],
                    "default_or_identity_weight_fallback_disabled": True,
                    "weight_layout_contract_sha256": "<stage weight_layout_contract_sha256 or empty string>",
                    "runtime_constant_contract_sha256": (
                        "<required only when stage runtime_constant_contract_sha256 is non-empty>"
                    ),
                    "interface": {
                        "clock_port": "clock",
                        "reset_port": "reset",
                        "start_port": "<optional start port>",
                        "inputs": [
                            {
                                "valid_port": "input_0_valid",
                                "ready_port": "input_0_ready",
                                "data_port": "input_0_data",
                                "data_width_bits": "<input bits * lanes>",
                            }
                        ],
                        "output": {
                            "valid_port": "output_valid",
                            "ready_port": "output_ready",
                            "data_port": "output_data",
                            "data_width_bits": "<output bits * lanes>",
                        },
                        "weight_loader": {
                            "valid_port": "weight_valid",
                            "ready_port": "weight_ready",
                            "data_port": "weight_data",
                            "data_width_bits": 32,
                            "addr_port": "weight_addr",
                            "addr_width_bits": "<positive width covering every canonical word>",
                            "last_port": "weight_last",
                        },
                        "runtime_loader": {
                            "valid_port": "runtime_valid",
                            "ready_port": "runtime_ready",
                            "data_port": "runtime_data",
                            "data_width_bits": 32,
                            "addr_port": "runtime_addr",
                            "addr_width_bits": "<positive width covering every runtime word>",
                            "last_port": "runtime_last",
                        },
                    },
                }
            },
            "single_layer_harness": {
                "top_module": "<elaborated_connected_harness_top_module>",
                "source_directory": str(
                    run_dir / "generated" / "semantic_harness" / "single_layer"
                ),
                "consumed_tensor_hashes": ["<every single_layer_required_tensors[].sha256>"],
                "default_or_identity_weight_fallback_disabled": True,
                "weight_layout_contract_sha256": "<connected_weight_stream_contract.contract_sha256>",
                "runtime_constant_contract_sha256": "<connected_runtime_stream_contract.contract_sha256>",
                "connected_weight_stream_contract_sha256": "<connected_weight_stream_contract.contract_sha256>",
                "connected_runtime_stream_contract_sha256": "<connected_runtime_stream_contract.contract_sha256>",
                "pipeline_plan_sha256": sha256_file(pipeline_path),
                "pipeline_overlap_trace_contract_sha256": "<single_layer_pipeline_overlap_contract.trace_contract_sha256>",
                "loader_route_contract": {
                    "weight_routes": [
                        {
                            "stage_id": "<stage segment stage_id>",
                            "target_id": "<target target_id>",
                            "dut_port_role": "<target dut_port_role>",
                            "local_stream_range": "<exact target local_stream_range>",
                            "global_stream_range": "<exact target global_stream_range>",
                            "dut_port": "<real connected DUT weight port>",
                        }
                    ],
                    "runtime_routes": [
                        {
                            "stage_id": "<non-empty runtime stage segment stage_id>",
                            "global_stream_range": "<exact stage global_stream_range>",
                            "target_ids": ["<every runtime target_id for the stage>"],
                            "dut_port": "<real connected DUT runtime port>",
                        }
                    ],
                },
                "interface": {
                    "clock_port": "clock",
                    "reset_port": "reset",
                    "start_port": "start",
                    "inputs": [
                        {
                            "valid_port": "input_0_valid",
                            "ready_port": "input_0_ready",
                            "data_port": "input_0_data",
                            "data_width_bits": "<first-stage input bits * lanes>",
                        }
                    ],
                    "output": {
                        "valid_port": "output_valid",
                        "ready_port": "output_ready",
                        "data_port": "output_data",
                        "data_width_bits": "<last-stage output bits * lanes>",
                    },
                    "weight_loader": {
                        "valid_port": "weight_valid",
                        "ready_port": "weight_ready",
                        "data_port": "weight_data",
                        "data_width_bits": 32,
                        "addr_port": "weight_addr",
                        "addr_width_bits": "<width covering connected weight stream>",
                        "last_port": "weight_last",
                    },
                    "runtime_loader": {
                        "valid_port": "runtime_valid",
                        "ready_port": "runtime_ready",
                        "data_port": "runtime_data",
                        "data_width_bits": 32,
                        "addr_port": "runtime_addr",
                        "addr_width_bits": "<width covering connected runtime stream>",
                        "last_port": "runtime_last",
                    },
                },
            },
            "notes": [
                "omit weight_loader when required_tensors is empty",
                "omit runtime_constant_contract_sha256 and runtime_loader when no runtime stream is declared",
                "the framework materializes all remaining top-level provenance and pass fields",
            ],
        },
        "reference_operator_semantics": {
            "semantic_adapter": reference.get("reference", {}).get("semantic_adapter"),
            "semantic_stage_map": stage_map,
            "semantic_execution_contract": reference.get("reference", {}).get("semantic_execution_contract"),
            "semantic_runtime_inputs": reference.get("reference", {}).get("semantic_runtime_inputs"),
            "semantic_runtime_values": reference.get("reference", {}).get("semantic_runtime_values"),
            "model_implementation": reference.get("reference", {}).get("model_implementation"),
            "transcendental_approximation_contract": {
                "path": transcendental_contract.get("path"),
                "file_sha256": transcendental_contract.get("file_sha256"),
                "contract_sha256": transcendental_contract.get("contract_sha256"),
                "status": transcendental_contract.get("status"),
            },
            "semantic_runtime_constant_contract": {
                "path": semantic_runtime_contract.get("path"),
                "file_sha256": semantic_runtime_contract.get("file_sha256"),
                "contract_sha256": semantic_runtime_contract.get("contract_sha256"),
                "status": semantic_runtime_contract.get("status"),
            },
            "stage_numeric_boundaries": [
                {
                    "stage_id": stage.get("stage_id"),
                    "op": stage.get("op"),
                    "numeric_contract": stage.get("numeric_contract", {}),
                }
                for stage in pipeline.get("stages", [])
                if isinstance(stage, dict)
            ],
            "policy": {
                "model_implementation_source_must_match_recorded_sha256": True,
                "runtime_mask_position_and_rope_tensors_come_from_same_golden_inference": True,
                "hardware_boundary_casts_come_only_from_pipeline_numeric_contracts": True,
                "rtl_outputs_used": False,
            },
        },
        "stage_requirements": stage_rows,
        "single_layer_required_tensors": [
            {
                "tensor": row.get("tensor"),
                "sha256": row.get("sha256"),
                "shape": row.get("shape"),
            }
            for row in weights
            if isinstance(row, dict)
        ],
        "board_required_tensors": [
            {
                "tensor": row.get("name"),
                "sha256": row.get("source_slice_sha256"),
                "shape": row.get("shape"),
                "dtype": row.get("dtype"),
                "source_data_offsets": row.get("data_offsets"),
            }
            for row in board_tensors
        ],
        "board_required_tensor_count": len(board_tensors),
        "board_required_layer_count": len(validation_layer_indices),
        "board_binding_required_fields": {
            "all_target_layers": covers_full_model,
            "all_validation_layers": True,
            "bound_layer_count": len(validation_layer_indices),
            "board_consumed_tensor_hashes": "must cover every source_slice_sha256 in board_required_tensors",
            "full_weight_image_manifest": "must bind this accelerator catalog hash and contain every required tensor hash",
        },
        "policy": {
            "weight_file_existence_alone_is_insufficient": True,
            "every_required_tensor_must_reach_a_DUT_weight_storage_or_port": True,
            "default_or_identity_initialization_cannot_pass": True,
            "testbench_must_load_weights_before_stimulus": True,
            "numeric_comparison_requires_explicit_atol_rtol_and_max_mismatch_fraction": True,
            "transformer_blocks_are_the_only_dut_weight_scope": True,
            "embedding_final_norm_lm_head_weights_are_not_required_by_dut": True,
        },
    }


def dut_binding_errors(
    binding: dict[str, Any],
    requirements: dict[str, Any],
    *,
    require_single_layer: bool = True,
) -> list[str]:
    errors: list[str] = []
    if binding.get("status") != "pass":
        errors.append("DUT weight-binding manifest status is not pass")
    if binding.get("accelerator_scope") != "transformer_blocks_only":
        errors.append("DUT weight binding accelerator_scope is not transformer_blocks_only")
    for key in (
        "source_checkpoint_sha256",
        "source_reference_sha256",
        "numeric_policy_sha256",
        "model_semantic_adapter_sha256",
    ):
        if binding.get(key) != requirements.get(key):
            errors.append(f"DUT weight binding {key} does not match verification preparation")
    if binding.get("scope_coverage_complete") is not True:
        errors.append("DUT weight binding does not claim complete verification-scope coverage")
    if binding.get("dut_consumes_bound_weights") is not True:
        errors.append("DUT weight binding does not prove that the bound weights are consumed")
    if binding.get("default_or_identity_weight_fallback_disabled") is not True:
        errors.append("DUT default/identity weight fallback is not disabled")
    required_hashes = {
        str(row.get("sha256"))
        for row in requirements.get("single_layer_required_tensors", [])
        if isinstance(row, dict) and row.get("sha256")
    }
    consumed_hashes = {str(value) for value in binding.get("consumed_tensor_hashes", []) if str(value)}
    missing_hashes = sorted(required_hashes - consumed_hashes)
    if missing_hashes:
        errors.append(f"DUT binding is missing {len(missing_hashes)} required real-weight tensor hash(es)")
    stage_harnesses = binding.get("stage_harnesses", {}) if isinstance(binding.get("stage_harnesses"), dict) else {}
    missing_stages = [
        str(row.get("stage_id"))
        for row in requirements.get("stage_requirements", [])
        if isinstance(row, dict) and str(row.get("stage_id")) not in stage_harnesses
    ]
    if missing_stages:
        errors.append(f"DUT binding has no semantic harness for stages {missing_stages}")
    if require_single_layer and not isinstance(binding.get("single_layer_harness"), dict):
        errors.append("DUT binding has no connected single-layer semantic harness")
    return errors


def validate_harness_weight_hashes(
    harness: dict[str, Any],
    required_bindings: list[dict[str, Any]],
    weight_layout: dict[str, Any] | None = None,
    runtime_constant_stream: dict[str, Any] | None = None,
) -> list[str]:
    required = {str(row.get("sha256")) for row in required_bindings if row.get("sha256")}
    consumed = {str(value) for value in harness.get("consumed_tensor_hashes", []) if str(value)}
    missing = sorted(required - consumed)
    errors = [f"semantic harness does not consume required tensor hashes {missing}"] if missing else []
    if required and harness.get("default_or_identity_weight_fallback_disabled") is not True:
        errors.append("semantic harness does not disable default/identity weight fallback")
    if required and isinstance(weight_layout, dict):
        expected_layout_hash = str(weight_layout.get("contract_sha256") or "")
        if harness.get("weight_layout_contract_sha256") != expected_layout_hash:
            errors.append("semantic harness weight-layout contract hash does not match requirements")
    if isinstance(runtime_constant_stream, dict):
        expected_runtime_hash = str(runtime_constant_stream.get("contract_sha256") or "")
        if harness.get("runtime_constant_contract_sha256") != expected_runtime_hash:
            errors.append("semantic harness runtime-constant contract hash does not match requirements")
        interface = harness.get("interface", {}) if isinstance(harness.get("interface"), dict) else {}
        if not isinstance(interface.get("runtime_loader"), dict):
            errors.append("semantic harness has no runtime-constant loader interface")
    return errors


def single_layer_pipeline_overlap_contract(
    input_vector: dict[str, Any],
    pipeline: dict[str, Any],
    pipeline_plan_sha256: str,
) -> dict[str, Any]:
    shape = [int(value) for value in input_vector.get("tensor_shape", [])]
    lanes = int(input_vector.get("lanes") or 0)
    if not shape or lanes <= 0 or shape[-1] % lanes:
        raise ValueError("single-layer input shape/lanes cannot define token stream boundaries")
    token_count = 1
    for size in shape[:-1]:
        token_count *= size
    beats_per_token = shape[-1] // lanes
    if token_count < 2:
        raise ValueError("pipeline-overlap verification requires at least two logical tokens")
    stages = [
        str(row.get("stage_id") or "")
        for row in pipeline.get("stages", [])
        if isinstance(row, dict) and row.get("stage_id")
    ]
    if not stages:
        raise ValueError("pipeline-overlap verification requires planned spatial stages")
    stage_set = set(stages)
    stream_edges = [
        row
        for row in pipeline.get("stream_edges", [])
        if isinstance(row, dict) and row.get("edge_id")
    ]
    if not stream_edges:
        raise ValueError("pipeline-overlap verification requires ready/valid stream edges")

    boundary_contracts = []
    for edge in stream_edges:
        stream = edge.get("stream_contract", {})
        stream = stream if isinstance(stream, dict) else {}
        total_elements = int(stream.get("transfer_count_elements") or 0)
        element_bits = int(stream.get("element_bits") or 0)
        stream_beat_bits = int(stream.get("stream_beat_bits") or 0)
        if (
            total_elements <= 0
            or total_elements % token_count
            or element_bits <= 0
            or stream_beat_bits <= 0
            or stream_beat_bits % element_bits
        ):
            raise ValueError(
                f"pipeline edge {edge.get('edge_id')} cannot define per-token stream beats"
            )
        elements_per_beat = stream_beat_bits // element_bits
        elements_per_token = total_elements // token_count
        if elements_per_token % elements_per_beat:
            raise ValueError(
                f"pipeline edge {edge.get('edge_id')} has a partial per-token stream beat"
            )
        boundary_contracts.append(
            {
                "boundary_id": str(edge["edge_id"]),
                "src_stage": str(edge.get("src_stage") or ""),
                "dst_stage": str(edge.get("dst_stage") or ""),
                "kind": str(edge.get("kind") or ""),
                "flow_control": str(edge.get("flow_control") or ""),
                "beats_per_token": elements_per_token // elements_per_beat,
            }
        )

    stage_activity_contracts = []
    for stage_id in stages:
        inputs = [
            row["boundary_id"]
            for row in boundary_contracts
            if row["dst_stage"] == stage_id
        ]
        outputs = [
            row["boundary_id"]
            for row in boundary_contracts
            if row["src_stage"] == stage_id
        ]
        if not inputs or not outputs:
            raise ValueError(
                f"pipeline stage {stage_id} lacks an observable input or output boundary"
            )
        stage_activity_contracts.append(
            {
                "stage_id": stage_id,
                "input_boundaries": inputs,
                "output_boundaries": outputs,
            }
        )
    internal_boundaries = [
        row
        for row in boundary_contracts
        if row["src_stage"] in stage_set and row["dst_stage"] in stage_set
    ]

    def has_alternate_path(candidate: dict[str, Any]) -> bool:
        adjacency: dict[str, list[str]] = {stage_id: [] for stage_id in stages}
        for row in internal_boundaries:
            if row["boundary_id"] == candidate["boundary_id"]:
                continue
            adjacency[row["src_stage"]].append(row["dst_stage"])
        pending = [
            stage_id
            for stage_id in adjacency.get(candidate["src_stage"], [])
            if stage_id != candidate["dst_stage"]
        ]
        visited: set[str] = set()
        while pending:
            stage_id = pending.pop()
            if stage_id == candidate["dst_stage"]:
                return True
            if stage_id in visited:
                continue
            visited.add(stage_id)
            pending.extend(adjacency.get(stage_id, []))
        return False

    dependency_edges = []
    for row in internal_boundaries:
        transitive_bypass = has_alternate_path(row)
        dependency_edges.append(
            {
                "boundary_id": row["boundary_id"],
                "src_stage": row["src_stage"],
                "dst_stage": row["dst_stage"],
                "kind": row["kind"],
                "relationship": (
                    "transitive_bypass" if transitive_bypass else "direct_dataflow"
                ),
                "overlap_requirement": (
                    "diagnostic" if transitive_bypass else "required"
                ),
            }
        )
    block_inputs = [
        row["boundary_id"]
        for row in boundary_contracts
        if row["src_stage"] == "block_input"
    ]
    block_outputs = [
        row["boundary_id"]
        for row in boundary_contracts
        if row["dst_stage"] == "block_output"
    ]
    if not block_inputs or len(block_outputs) != 1:
        raise ValueError("pipeline plan requires block-input edges and one block-output edge")
    trace_abi = (
        "SPATIALACC_PIPELINE_TRACE boundary=<id> cycle=<decimal> token=<decimal> beat=<decimal> "
        "st=<0_or_1> last=<0_or_1> valid=<0_or_1> ready=<0_or_1>"
    )
    legacy_v2_contract = {
        "schema_version": "spatialaccagent.single_layer_pipeline_overlap_contract.v2",
        "pipeline_plan_sha256": pipeline_plan_sha256,
        "stage_order": stages,
        "planned_stage_count": len(stages),
        "token_count": token_count,
        "beats_per_token": beats_per_token,
        "trace_abi": trace_abi,
        "required_boundaries": [row["boundary_id"] for row in boundary_contracts],
        "boundary_contracts": boundary_contracts,
        "stage_activity_contracts": stage_activity_contracts,
        "dependency_edges": [
            {
                "boundary_id": row["boundary_id"],
                "src_stage": row["src_stage"],
                "dst_stage": row["dst_stage"],
            }
            for row in dependency_edges
        ],
        "block_input_boundaries": block_inputs,
        "block_output_boundary": block_outputs[0],
        "acceptance": {
            "all_required_records_are_accepted_transfers": True,
            "every_token_has_first_and_last_record_at_each_required_boundary": True,
            "maximum_next_token_stage_entry_gap_cycles": 1,
            "every_stage_emits_token_0_before_accepting_the_final_token": True,
            "every_adjacent_stage_pair_overlaps_on_different_tokens": True,
            "all_planned_spatial_stages_are_concurrently_active_after_fill": True,
            "minimum_concurrent_stage_count": len(stages),
            "whole_sequence_barrier_forbidden": True,
        },
        "policy": {
            "trace_is_observation_only": True,
            "trace_must_not_change_ready_valid_or_data": True,
            "transaction_counts_alone_cannot_prove_pipeline_overlap": True,
            "stage_activity_is_derived_from_actual_module_port_handshakes": True,
            "layer_level_overlap_cannot_substitute_for_intra_layer_operator_overlap": True,
        },
    }
    legacy_v2_contract["contract_sha256"] = sha256_json(legacy_v2_contract)

    trace_contract = {
        "schema_version": "spatialaccagent.single_layer_pipeline_trace_contract.v1",
        "pipeline_plan_sha256": pipeline_plan_sha256,
        "trace_abi": trace_abi,
        "required_boundaries": [row["boundary_id"] for row in boundary_contracts],
        "boundary_contracts": boundary_contracts,
        "stage_activity_contracts": stage_activity_contracts,
        "token_count": token_count,
    }
    trace_contract_sha256 = sha256_json(trace_contract)
    required_dependency_count = sum(
        row["overlap_requirement"] == "required" for row in dependency_edges
    )
    contract = {
        "schema_version": "spatialaccagent.single_layer_pipeline_overlap_contract.v3",
        "pipeline_semantics": "elastic_rate_insensitive_token_pipeline",
        "pipeline_plan_sha256": pipeline_plan_sha256,
        "stage_order": stages,
        "planned_stage_count": len(stages),
        "token_count": token_count,
        "beats_per_token": beats_per_token,
        "trace_abi": trace_abi,
        "trace_contract": trace_contract,
        "trace_contract_sha256": trace_contract_sha256,
        "compatible_trace_contract_sha256s": [
            trace_contract_sha256,
            legacy_v2_contract["contract_sha256"],
        ],
        "required_boundaries": [row["boundary_id"] for row in boundary_contracts],
        "boundary_contracts": boundary_contracts,
        "stage_activity_contracts": stage_activity_contracts,
        "dependency_edges": dependency_edges,
        "required_dependency_count": required_dependency_count,
        "block_input_boundaries": block_inputs,
        "block_output_boundary": block_outputs[0],
        "acceptance": {
            "all_required_records_are_accepted_transfers": True,
            "every_token_has_first_and_last_record_at_each_required_boundary": True,
            "token_order_is_preserved_at_every_required_boundary": True,
            "every_stage_emits_token_0_before_accepting_the_final_token": True,
            "every_required_dependency_overlaps_on_different_tokens": True,
            "required_dependency_policy": "non_transitive_internal_dataflow_edges",
            "different_token_overlap_distance": "any_positive_upstream_token_distance",
            "every_planned_stage_participates_in_required_overlap": len(stages) > 1,
            "minimum_concurrent_stage_count": min(2, len(stages)),
            "stage_turnover_gaps_are_diagnostic": True,
            "all_planned_stages_same_cycle_concurrency_required": False,
            "transitive_bypass_overlap_is_diagnostic": True,
            "whole_sequence_barrier_forbidden": True,
        },
        "policy": {
            "trace_is_observation_only": True,
            "trace_must_not_change_ready_valid_or_data": True,
            "transaction_counts_alone_cannot_prove_pipeline_overlap": True,
            "stage_activity_is_derived_from_actual_module_port_handshakes": True,
            "layer_level_overlap_cannot_substitute_for_intra_layer_operator_overlap": True,
            "heterogeneous_stage_latency_and_initiation_interval_are_expected": True,
            "unequal_stage_start_or_end_cycles_are_not_failures": True,
            "throughput_metrics_may_guide_optimization_but_cannot_authorize_functional_repair": True,
        },
    }
    contract["contract_sha256"] = sha256_json(contract)
    return contract


def connected_loader_route_errors(
    harness: dict[str, Any],
    weight_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> list[str]:
    route_contract = (
        harness.get("loader_route_contract", {})
        if isinstance(harness.get("loader_route_contract"), dict)
        else {}
    )
    weight_routes = route_contract.get("weight_routes", [])
    runtime_routes = route_contract.get("runtime_routes", [])
    if not isinstance(weight_routes, list) or not isinstance(runtime_routes, list):
        return ["connected harness loader_route_contract routes must be lists"]
    errors: list[str] = []
    expected_weight: dict[tuple[str, str], dict[str, Any]] = {}
    for stage in weight_contract.get("stage_segments", []):
        if not isinstance(stage, dict):
            continue
        for target in stage.get("targets", []):
            if isinstance(target, dict) and int(target.get("global_stream_range", {}).get("word_count") or 0) > 0:
                expected_weight[(str(stage.get("stage_id")), str(target.get("target_id")))] = target
    actual_weight: dict[tuple[str, str], dict[str, Any]] = {}
    for row in weight_routes:
        if not isinstance(row, dict):
            errors.append("connected weight loader route is not an object")
            continue
        key = (str(row.get("stage_id") or ""), str(row.get("target_id") or ""))
        if key in actual_weight:
            errors.append(f"connected weight loader route is duplicated: {key}")
        actual_weight[key] = row
    if set(actual_weight) != set(expected_weight):
        errors.append("connected weight loader routes do not cover every canonical target exactly once")
    for key in sorted(set(actual_weight) & set(expected_weight)):
        actual = actual_weight[key]
        expected = expected_weight[key]
        for field in ("dut_port_role", "local_stream_range", "global_stream_range"):
            if actual.get(field) != expected.get(field):
                errors.append(f"connected weight loader route {key} has wrong {field}")
        if not str(actual.get("dut_port") or ""):
            errors.append(f"connected weight loader route {key} has no real DUT port")

    expected_runtime: dict[str, dict[str, Any]] = {
        str(stage.get("stage_id")): stage
        for stage in runtime_contract.get("stage_segments", [])
        if isinstance(stage, dict)
        and int(stage.get("global_stream_range", {}).get("word_count") or 0) > 0
    }
    actual_runtime: dict[str, dict[str, Any]] = {}
    for row in runtime_routes:
        if not isinstance(row, dict):
            errors.append("connected runtime loader route is not an object")
            continue
        stage_id = str(row.get("stage_id") or "")
        if stage_id in actual_runtime:
            errors.append(f"connected runtime loader route is duplicated: {stage_id}")
        actual_runtime[stage_id] = row
    if set(actual_runtime) != set(expected_runtime):
        errors.append("connected runtime loader routes do not cover every non-empty canonical stage exactly once")
    for stage_id in sorted(set(actual_runtime) & set(expected_runtime)):
        actual = actual_runtime[stage_id]
        expected = expected_runtime[stage_id]
        if actual.get("global_stream_range") != expected.get("global_stream_range"):
            errors.append(f"connected runtime loader route {stage_id} has wrong global_stream_range")
        expected_targets = [str(row.get("target_id")) for row in expected.get("targets", [])]
        if actual.get("target_ids") != expected_targets:
            errors.append(f"connected runtime loader route {stage_id} has wrong target_ids")
        if not str(actual.get("dut_port") or ""):
            errors.append(f"connected runtime loader route {stage_id} has no real DUT port")
    return errors


def validate_connected_harness(
    harness: dict[str, Any],
    weight_bindings: list[dict[str, Any]],
    weight_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
    pipeline_plan_sha256: str,
    overlap_contract: dict[str, Any],
) -> list[str]:
    errors = validate_harness_weight_hashes(harness, weight_bindings)
    trace_contract_sha256 = str(
        overlap_contract.get("trace_contract_sha256")
        or overlap_contract.get("contract_sha256")
        or ""
    )
    expected = {
        "weight_layout_contract_sha256": weight_contract.get("contract_sha256"),
        "runtime_constant_contract_sha256": runtime_contract.get("contract_sha256"),
        "connected_weight_stream_contract_sha256": weight_contract.get("contract_sha256"),
        "connected_runtime_stream_contract_sha256": runtime_contract.get("contract_sha256"),
        "pipeline_plan_sha256": pipeline_plan_sha256,
    }
    for field, value in expected.items():
        if harness.get(field) != value:
            errors.append(f"connected semantic harness {field} does not match requirements")
    compatible_trace_contracts = {
        str(value)
        for value in overlap_contract.get("compatible_trace_contract_sha256s", [])
        if str(value)
    }
    compatible_trace_contracts.add(trace_contract_sha256)
    if str(harness.get("pipeline_overlap_trace_contract_sha256") or "") not in compatible_trace_contracts:
        errors.append(
            "connected semantic harness pipeline_overlap_trace_contract_sha256 does not match requirements"
        )
    interface = harness.get("interface", {}) if isinstance(harness.get("interface"), dict) else {}
    for loader_name in ("weight_loader", "runtime_loader"):
        if not isinstance(interface.get(loader_name), dict):
            errors.append(f"connected semantic harness has no {loader_name} interface")
    errors.extend(connected_loader_route_errors(harness, weight_contract, runtime_contract))
    return errors


def reusable_operator_leaf_certificate(run_dir: Path) -> dict[str, Any]:
    path = (
        run_dir
        / "verification"
        / "certificates"
        / "operator_leaf_promotion_certificate.json"
    )
    certificate = read_json(path) if path.is_file() else {}
    gates = [
        row
        for row in certificate.get("required_gates", [])
        if isinstance(row, dict)
    ]
    policy = (
        certificate.get("policy", {})
        if isinstance(certificate.get("policy"), dict)
        else {}
    )
    required_gate_names = [str(row.get("name")) for row in gates if row.get("name")]
    contract_errors = certificate_contract_errors(
        certificate,
        "operator_leaf_functional",
        required_gate_names,
    ) if path.is_file() and required_gate_names else ["operator-leaf certificate has no required gates"]
    reusable = (
        certificate.get("artifact_id")
        == "artifact.stage7.operator_leaf_promotion_certificate"
        and certificate.get("gate_execution_scope") == "operator_leaf_closure"
        and certificate.get("status") == "pass"
        and bool(gates)
        and all(row.get("status") == "pass" for row in gates)
        and policy.get("lower_layer_pass_evidence_is_reusable_not_absolute") is True
        and not contract_errors
    )
    return {
        "status": "pass" if reusable else "incomplete",
        "path": str(path),
        "sha256": sha256_file(path) if path.is_file() else None,
        "required_gate_count": len(gates),
        "validation_errors": contract_errors,
    }


def generate(
    run_dir: Path,
    out_dir: Path,
    *,
    verification_scope: str = "all",
) -> dict[str, Any]:
    import torch

    scoped_single_layer = verification_scope in {
        "single_layer_closure",
        "board_axi_ddr_closure",
    }
    lower_layer_certificate = (
        reusable_operator_leaf_certificate(run_dir)
        if scoped_single_layer
        else {
            "status": "not_applicable",
            "reason": "operator-leaf verification does not consume a prior operator-leaf promotion certificate",
        }
    )

    reference_path = run_dir / "verification" / "model_reference" / "reference_manifest.json"
    task_card_path = run_dir / "input" / "task_card.json"
    model_config_path = run_dir / "input" / "model_config.json"
    pipeline_path = run_dir / "pipeline_planning" / "pipeline_plan.json"
    numeric_policy_path = run_dir / "input" / "numeric_policy.json"
    accelerator_catalog_path = run_dir / "verification" / "model_weights" / "transformer_block_weight_catalog.json"
    binding_path = run_dir / "generated" / "memory" / "dut_weight_binding_manifest.json"
    reference = read_json(reference_path)
    task_card = read_json(task_card_path)
    model_config = read_json(model_config_path)
    resolved_board_scope = resolve_board_validation_scope(task_card, model_config)
    board_scope = resolved_board_scope.as_dict()
    pipeline = read_json(pipeline_path)
    numeric_policy = read_json(numeric_policy_path)
    accelerator_catalog = read_json(accelerator_catalog_path)
    binding = read_json(binding_path) if binding_path.exists() else {}
    if reference.get("status") != "ready":
        raise ValueError(f"target model reference is not ready: {reference.get('status')}")
    default_rules = numeric_policy.get("default_rules", {}) if isinstance(numeric_policy.get("default_rules"), dict) else {}
    if default_rules.get("activation_dtype") not in {"fp16", "fp32"}:
        raise ValueError("semantic vector encoding currently requires activation_dtype fp16 or fp32")
    if default_rules.get("weight_dtype") != "fp16":
        raise ValueError("semantic weight-stream encoding currently requires weight_dtype fp16")
    comparison_policy, comparison_policy_resolution = numeric_comparison_policy(numeric_policy)
    transcendental_contract = materialize_transcendental_contract(
        run_dir / "generated" / "chisel" / "src" / "main" / "resources" / "spatialaccagent" / "numeric"
    )
    if transcendental_contract.get("status") != "pass":
        raise ValueError("transcendental approximation contract failed its frozen exhaustive error bounds")
    semantic_adapter_record = reference.get("reference", {}).get("semantic_adapter", {})
    semantic_adapter_path = Path(str(semantic_adapter_record.get("path") or ""))
    if (
        not semantic_adapter_path.is_file()
        or sha256_file(semantic_adapter_path) != semantic_adapter_record.get("sha256")
    ):
        raise ValueError("target-model semantic adapter file/hash mismatch")
    semantic_adapter = read_json(semantic_adapter_path)
    semantic_runtime_contract = materialize_semantic_runtime_constants(
        reference,
        semantic_adapter,
        run_dir / "generated" / "chisel" / "src" / "main" / "resources" / "spatialaccagent" / "numeric",
        semantic_adapter_sha256=str(semantic_adapter_record.get("sha256") or ""),
    )
    if semantic_runtime_contract.get("status") != "pass":
        raise ValueError(
            "semantic runtime constant materialization failed: "
            + "; ".join(semantic_runtime_contract.get("blockers", [])[:4])
        )
    if (
        accelerator_catalog.get("status") != "pass"
        or accelerator_catalog.get("accelerator_scope") != "transformer_blocks_only"
        or accelerator_catalog.get("scope_coverage_complete") is not True
    ):
        raise ValueError("complete transformer-block weight catalog is not ready")
    requirements = binding_requirements(
        run_dir,
        reference,
        pipeline,
        pipeline_path,
        numeric_policy,
        reference_path,
        numeric_policy_path,
        accelerator_catalog,
        accelerator_catalog_path,
        transcendental_contract,
        semantic_runtime_contract,
        board_scope,
    )
    requirements["board_validation_scope"] = board_scope
    requirements_path = out_dir / "dut_weight_binding_requirements.json"
    write_json(requirements_path, requirements)
    binding_issues = dut_binding_errors(binding, requirements, require_single_layer=False)
    random_input, records = load_reference_tensors(reference)
    stage_map = semantic_stage_map(reference)
    weight_rows = reference.get("weights", {}).get("layer_0_tensor_bindings", [])
    weights_by_suffix = {
        str(row.get("parameter_suffix") or ""): row
        for row in weight_rows
        if isinstance(row, dict)
    }
    pipeline_stages = [stage for stage in pipeline.get("stages", []) if isinstance(stage, dict)]
    stage_contracts = []
    blockers: list[str] = [] if scoped_single_layer else [*binding_issues]
    stage_harnesses = binding.get("stage_harnesses", {}) if isinstance(binding.get("stage_harnesses"), dict) else {}
    requirements_by_stage = {
        str(row.get("stage_id")): row
        for row in requirements.get("stage_requirements", [])
        if isinstance(row, dict)
    }
    for stage in pipeline_stages:
        stage_id = str(stage.get("stage_id") or "")
        op = str(stage.get("op") or "")
        stage_dir = out_dir / "stages" / safe_id(stage_id)
        try:
            inputs, expected = stage_tensors(op, random_input, records, stage_map)
            lanes = scalar(stage, "lanes", 1)
            input_bits = scalar(stage, "input_bits", 32)
            output_bits = scalar(stage, "output_bits", input_bits)
            input_vectors = [
                write_packed_memh(stage_dir / f"input_{index}.memh", tensor, input_bits, lanes)
                for index, tensor in enumerate(inputs)
            ]
            expected_vector = write_packed_memh(stage_dir / "expected.memh", expected, output_bits, lanes)
            weight_bindings = []
            required_weight_names = required_weights(op, stage_map)
            for name in required_weight_names:
                row = weights_by_suffix.get(name)
                if row is None:
                    blockers.append(f"{stage_id}: real target weight is missing: {name}")
                    continue
                weight_bindings.append(row)
            harness = stage_harnesses.get(stage_id, {}) if isinstance(stage_harnesses.get(stage_id), dict) else {}
            requirement_row = requirements_by_stage.get(stage_id, {})
            weight_layout = requirement_row.get("weight_layout", {}) if isinstance(requirement_row, dict) else {}
            runtime_constant_stream = (
                requirement_row.get("runtime_constant_stream") if isinstance(requirement_row, dict) else None
            )
            harness_errors = [] if scoped_single_layer else (
                validate_harness_weight_hashes(
                    harness,
                    weight_bindings,
                    weight_layout,
                    runtime_constant_stream if isinstance(runtime_constant_stream, dict) else None,
                )
                if harness
                else ["semantic harness is missing"]
            )
            source_rows: list[dict[str, Any]] = []
            if harness and not scoped_single_layer:
                source_rows, source_errors = verified_source_files(harness)
                harness_errors.extend(source_errors)
            weight_stream = None
            runtime_stream = (
                runtime_constant_stream.get("stream")
                if isinstance(runtime_constant_stream, dict) and isinstance(runtime_constant_stream.get("stream"), dict)
                else None
            )
            stream_errors: list[str] = []
            if weight_bindings and len(weight_bindings) == len(required_weight_names):
                try:
                    weight_stream = materialize_stage_weight_stream(
                        stage_dir / "real_weights.u32.memh",
                        weight_layout,
                        weight_bindings,
                    )
                except Exception as exc:
                    stream_errors.append(str(exc))
            tb_path = stage_dir / "semantic_tb.sv"
            output_capture = stage_dir / "rtl_output.memh"
            if not scoped_single_layer and not harness_errors and not stream_errors:
                tb_path.write_text(
                    semantic_harness_tb(
                        tb_module=f"semantic_{safe_id(stage_id)}_tb",
                        harness=harness,
                        input_vectors=input_vectors,
                        expected_output=expected_vector,
                        output_path=output_capture,
                        weight_stream=weight_stream,
                        runtime_stream=runtime_stream,
                    ),
                    encoding="ascii",
                )
            elif not scoped_single_layer and tb_path.exists():
                tb_path.unlink()
            blockers.extend(f"{stage_id}: {message}" for message in stream_errors)
            if not scoped_single_layer:
                blockers.extend(f"{stage_id}: {message}" for message in harness_errors)
            contract = {
                "schema_version": "spatialaccagent.operator_semantic_testbench_contract.v1",
                "status": (
                    "reused_lower_layer_certificate"
                    if scoped_single_layer
                    and lower_layer_certificate.get("status") == "pass"
                    and len(weight_bindings) == len(required_weight_names)
                    and not stream_errors
                    else
                    "ready"
                    if len(weight_bindings) == len(required_weight_names)
                    and not harness_errors
                    and not stream_errors
                    else "incomplete"
                ),
                "stage_id": stage_id,
                "op": op,
                "input_vectors": input_vectors,
                "expected_output": expected_vector,
                "real_weight_bindings": weight_bindings,
                "weight_layout": weight_layout,
                "weight_layout_contract_sha256": weight_layout.get("contract_sha256"),
                "real_weight_stream": weight_stream,
                "runtime_constant_stream": runtime_constant_stream,
                "runtime_constant_contract_sha256": (
                    runtime_constant_stream.get("contract_sha256")
                    if isinstance(runtime_constant_stream, dict)
                    else None
                ),
                "dut_harness": {
                    "top_module": harness.get("top_module"),
                    "source_files": source_rows,
                    "consumed_tensor_hashes": harness.get("consumed_tensor_hashes", []),
                },
                "testbench": (
                    str(tb_path)
                    if not scoped_single_layer and not harness_errors and not stream_errors
                    else None
                ),
                "testbench_sha256": (
                    sha256_file(tb_path)
                    if not scoped_single_layer and not harness_errors and not stream_errors
                    else None
                ),
                "rtl_output_capture": str(output_capture),
                "numeric_contract": stage.get("numeric_contract", {}),
                "source_reference_manifest": str(reference_path),
                "source_reference_sha256": sha256_file(reference_path),
            }
            contract_path = stage_dir / "testbench_contract.json"
            write_json(contract_path, contract)
            stage_contracts.append({**contract, "path": str(contract_path)})
        except Exception as exc:
            blockers.append(f"{stage_id}: {exc}")

    first_stage = pipeline_stages[0] if pipeline_stages else {}
    last_stage = pipeline_stages[-1] if pipeline_stages else {}
    input_lanes = scalar(first_stage, "lanes", 1)
    output_lanes = scalar(last_stage, "lanes", input_lanes)
    input_bits = scalar(first_stage, "input_bits", 32)
    output_bits = scalar(last_stage, "output_bits", input_bits)
    layer_output = torch.load(
        reference["reference"]["single_layer_output"]["path"],
        map_location="cpu",
        weights_only=True,
    )
    single_dir = out_dir / "single_layer"
    input_vector = write_packed_memh(single_dir / "input.memh", random_input, input_bits, input_lanes)
    expected_vector = write_packed_memh(single_dir / "expected.memh", layer_output, output_bits, output_lanes)
    pipeline_plan_sha256 = sha256_file(pipeline_path)
    overlap_contract = single_layer_pipeline_overlap_contract(
        input_vector,
        pipeline,
        pipeline_plan_sha256,
    )
    connected_contract_errors: list[str] = []
    single_weight_stream: dict[str, Any] | None = None
    single_runtime_stream: dict[str, Any] | None = None
    try:
        if len(stage_contracts) != len(pipeline_stages):
            raise ValueError("connected canonical streams require complete pipeline-stage contracts")
        single_weight_stream = materialize_composite_weight_stream(
            single_dir / "real_weights.u32.memh",
            [
                {
                    "stage_id": contract.get("stage_id"),
                    "op": contract.get("op"),
                    "layout": contract.get("weight_layout"),
                    "stream": contract.get("real_weight_stream"),
                }
                for contract in stage_contracts
            ],
        )
        single_runtime_stream = materialize_composite_runtime_stream(
            single_dir / "runtime_constants.u32.memh",
            [
                {
                    "stage_id": row.get("stage_id"),
                    "op": row.get("op"),
                    "runtime_contract": row.get("runtime_constant_stream"),
                }
                for row in requirements.get("stage_requirements", [])
                if isinstance(row, dict)
            ],
        )
    except Exception as exc:
        connected_contract_errors.append(str(exc))
    requirements["connected_weight_stream_contract"] = single_weight_stream
    requirements["connected_runtime_stream_contract"] = single_runtime_stream
    requirements["single_layer_pipeline_overlap_contract"] = overlap_contract
    write_json(requirements_path, requirements)
    board_reference = select_board_reference_output(reference, resolved_board_scope)
    board_reference_payload = torch.load(
        board_reference["path"],
        map_location="cpu",
        weights_only=True,
    )
    payload_key = board_reference.get("payload_key")
    if payload_key is not None:
        if not isinstance(board_reference_payload, dict) or payload_key not in board_reference_payload:
            raise ValueError(
                "selected board-reference capture has no "
                f"{payload_key!r} tensor payload"
            )
        board_model_output = board_reference_payload[payload_key]
    else:
        board_model_output = board_reference_payload
    if not isinstance(board_model_output, torch.Tensor):
        raise ValueError("selected board-reference payload is not a tensor")
    board_dir = out_dir / "board"
    board_input_vector = write_packed_memh(board_dir / "input.memh", random_input, input_bits, input_lanes)
    board_expected_vector = write_packed_memh(board_dir / "expected.memh", board_model_output, output_bits, output_lanes)
    board_expected_vector.update(
        {
            "source_capture": board_reference["source_capture"],
            "source_tensor_path": board_reference["path"],
            "source_tensor_file_sha256": board_reference["file_sha256"],
            "source_tensor_sha256": board_reference["tensor_sha256"],
            "reference_kind": board_reference["reference_kind"],
        }
    )
    tb_path = single_dir / "single_layer_real_model_tb.sv"
    single_harness = binding.get("single_layer_harness", {}) if isinstance(binding.get("single_layer_harness"), dict) else {}
    single_harness_errors = list(connected_contract_errors)
    if scoped_single_layer:
        if lower_layer_certificate.get("status") != "pass":
            single_harness_errors.append(
                "passing operator-leaf promotion certificate is unavailable for scoped single-layer reuse"
            )
        if binding.get("accelerator_scope") != "transformer_blocks_only":
            single_harness_errors.append(
                "DUT weight binding accelerator_scope is not transformer_blocks_only"
            )
        for field in (
            "source_checkpoint_sha256",
            "source_reference_sha256",
            "numeric_policy_sha256",
            "model_semantic_adapter_sha256",
        ):
            if binding.get(field) != requirements.get(field):
                single_harness_errors.append(
                    f"DUT weight binding {field} does not match verification preparation"
                )
    if not single_harness:
        single_harness_errors.append("connected single-layer semantic harness is missing")
    elif single_weight_stream is None or single_runtime_stream is None:
        single_harness_errors.append("connected canonical weight/runtime stream contracts are missing")
    else:
        single_harness_errors.extend(
            validate_connected_harness(
                single_harness,
                weight_rows,
                single_weight_stream,
                single_runtime_stream,
                pipeline_plan_sha256,
                overlap_contract,
            )
        )
    single_sources: list[dict[str, Any]] = []
    if single_harness:
        single_sources, source_errors = verified_source_files(single_harness)
        single_harness_errors.extend(source_errors)
    output_capture = single_dir / "rtl_output.memh"
    if not single_harness_errors:
        tb_path.write_text(
            semantic_harness_tb(
                tb_module="semantic_single_transformer_layer_kernel_tb",
                harness=single_harness,
                input_vectors=[input_vector],
                expected_output=expected_vector,
                output_path=output_capture,
                weight_stream=single_weight_stream,
                runtime_stream=single_runtime_stream,
            ),
            encoding="ascii",
        )
    elif tb_path.exists():
        tb_path.unlink()
    single_layer_blockers = [f"single_layer: {message}" for message in single_harness_errors]
    if not pipeline_stages:
        blockers.append("pipeline plan contains no semantic stages")
    elif len(stage_contracts) != len(pipeline_stages):
        blockers.append(
            f"semantic stage contract coverage is incomplete: expected={len(pipeline_stages)} actual={len(stage_contracts)}"
        )
    leaf_binding_ok = (
        lower_layer_certificate.get("status") == "pass"
        if scoped_single_layer
        else (
            bool(stage_contracts)
            and len(stage_contracts) == len(pipeline_stages)
            and not binding_issues
            and all(
                contract.get("status") == "ready" for contract in stage_contracts
            )
        )
    )
    single_layer_ready = leaf_binding_ok and not single_harness_errors
    if scoped_single_layer:
        blockers.extend(single_layer_blockers)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not blockers else "incomplete",
        "requested_verification_scope": verification_scope,
        "reused_operator_leaf_promotion_certificate": lower_layer_certificate,
        "run_dir": str(run_dir),
        "reference_manifest": str(reference_path),
        "reference_manifest_sha256": sha256_file(reference_path),
        "numeric_policy": str(numeric_policy_path),
        "numeric_policy_sha256": sha256_file(numeric_policy_path),
        "numeric_comparison_policy": comparison_policy,
        "numeric_comparison_resolution": comparison_policy_resolution,
        "transcendental_approximation_contract": {
            "path": transcendental_contract.get("path"),
            "file_sha256": transcendental_contract.get("file_sha256"),
            "contract_sha256": transcendental_contract.get("contract_sha256"),
            "status": transcendental_contract.get("status"),
        },
        "semantic_runtime_constant_contract": {
            "path": semantic_runtime_contract.get("path"),
            "file_sha256": semantic_runtime_contract.get("file_sha256"),
            "contract_sha256": semantic_runtime_contract.get("contract_sha256"),
            "status": semantic_runtime_contract.get("status"),
        },
        "dut_weight_binding_requirements": str(requirements_path),
        "dut_weight_binding_requirements_sha256": sha256_file(requirements_path),
        "dut_weight_binding_manifest": str(binding_path),
        "dut_weight_binding_verified": leaf_binding_ok,
        "random_input": reference.get("input"),
        "real_weight_source": reference.get("weights"),
        "accelerator_scope": "transformer_blocks_only",
        "stage_contracts": stage_contracts,
        "single_layer": {
            "status": "ready" if single_layer_ready else "incomplete",
            "blockers": single_layer_blockers,
            "testbench": str(tb_path) if not single_harness_errors else None,
            "testbench_sha256": sha256_file(tb_path) if not single_harness_errors else None,
            "input_vector": input_vector,
            "input_vectors": [input_vector],
            "expected_output": expected_vector,
            "real_weight_stream": single_weight_stream,
            "runtime_constant_stream": single_runtime_stream,
            "connected_weight_stream_contract_sha256": (
                single_weight_stream.get("contract_sha256") if single_weight_stream else None
            ),
            "connected_runtime_stream_contract_sha256": (
                single_runtime_stream.get("contract_sha256") if single_runtime_stream else None
            ),
            "pipeline_plan_sha256": pipeline_plan_sha256,
            "pipeline_overlap_contract": overlap_contract,
            "rtl_output_capture": str(output_capture),
            "dut_harness": {
                "top_module": single_harness.get("top_module"),
                "source_files": single_sources,
                "consumed_tensor_hashes": single_harness.get("consumed_tensor_hashes", []),
                "loader_route_contract": single_harness.get("loader_route_contract"),
                "pipeline_overlap_trace_contract_sha256": single_harness.get(
                    "pipeline_overlap_trace_contract_sha256"
                ),
            },
            "real_weight_binding_manifest": str(binding_path),
            "real_weight_binding_verified": single_layer_ready,
        },
        "board": {
            "input_vector": board_input_vector,
            "expected_output": board_expected_vector,
            "model_layer_count": board_scope["model_layer_count"],
            "expected_target_layers": board_scope["validation_layer_count"],
            "validation_layer_indices": board_scope["validation_layer_indices"],
            "reference_output_layer_index": board_scope["reference_output_layer_index"],
            "board_validation_scope": board_scope,
            "accelerator_scope": "transformer_blocks_only",
            "required_weight_tensor_count": requirements["board_required_tensor_count"],
            "all_target_layer_reference_captured": (
                reference.get("reference", {}).get("all_target_layers_captured") is True
            ),
            "scoped_layer_reference_captured": True,
            "testbench": None,
            "stream_boundary_encoding": {
                "input_bits": input_bits,
                "input_lanes": input_lanes,
                "output_bits": output_bits,
                "output_lanes": output_lanes,
                "source": "current pipeline first-input and last-output numeric contracts",
            },
            "note": "The exact sample-project board testbench is generated after board source discovery and must repack these immutable stream-boundary vectors into the declared DDR/AXI layout without changing their semantic values.",
        },
        "blockers": blockers,
        "policy": {
            "real_model_reference_required": True,
            "random_input_is_reproducible": True,
            "expected_output_is_computed_not_random": True,
            "expected_output_source": "target_model_inference",
            "rtl_output_is_never_used_as_golden": True,
            "testbench_must_bind_real_weights_to_dut": True,
            "missing_dut_weight_binding_is_not_a_pass": True,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate real-model semantic hardware testbench artifacts")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir = args.run_dir.resolve()
    out_dir = (args.out_dir or run_dir / "verification" / "semantic_testbench").resolve()
    manifest_path = out_dir / "semantic_testbench_manifest.json"
    verification_scope = os.environ.get(
        "SPATIALACC_VERIFICATION_SCOPE", "all"
    ).strip() or "all"
    try:
        manifest = generate(
            run_dir,
            out_dir,
            verification_scope=verification_scope,
        )
    except Exception as exc:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "status": "fail",
            "run_dir": str(run_dir),
            "error": str(exc),
            "blockers": [str(exc)],
        }
    write_json(manifest_path, manifest)
    print(manifest_path)
    if manifest.get("status") != "ready":
        print("semantic_testbench_generator.py: " + "; ".join(manifest.get("blockers", [])[:8]), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
