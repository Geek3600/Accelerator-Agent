from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path


def fp_bits(value: float, width: int) -> int:
    return int.from_bytes(struct.pack("<e" if width == 16 else "<f", value), "little")


def packed(values: list[float], width: int) -> str:
    return f"{sum(fp_bits(value, width) << (index * width) for index, value in enumerate(values)):0{len(values) * width // 4}x}"


def packed_signed(values: list[int], width: int) -> str:
    mask = (1 << width) - 1
    bits = sum((int(value) & mask) << (index * width) for index, value in enumerate(values))
    return f"{bits:0{(len(values) * width + 3) // 4}x}"


def compile_only_port_declarations(directory: Path, module_name: str) -> tuple[list[str], list[str]]:
    """Return explicit port wires and named connections for a real DUT instance.

    Parse only the selected module's balanced ANSI port header. Splitting the
    header on every comma or selecting the last identifier in a declaration is
    unsafe: nested expressions, comments, and typed declarations can otherwise
    produce a bogus port name and leave real decoder ports unconnected.
    Compile-only fixture signals are intentionally undriven; the simulator is
    not invoked.
    """
    module_pattern = re.compile(
        rf"\bmodule\s+(?:automatic\s+|static\s+)?{re.escape(module_name)}\b"
    )

    def matching_paren(text: str, open_index: int) -> int:
        depth = 0
        for index in range(open_index, len(text)):
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
                if depth == 0:
                    return index
        raise ValueError(f"unterminated parenthesized header for {module_name}")

    def split_ports(header: str) -> list[str]:
        parts: list[str] = []
        start = 0
        paren = bracket = brace = 0
        for index, char in enumerate(header):
            if char == "(":
                paren += 1
            elif char == ")":
                paren -= 1
            elif char == "[":
                bracket += 1
            elif char == "]":
                bracket -= 1
            elif char == "{":
                brace += 1
            elif char == "}":
                brace -= 1
            elif char == "," and paren == 0 and bracket == 0 and brace == 0:
                parts.append(header[start:index].strip())
                start = index + 1
            if min(paren, bracket, brace) < 0:
                raise ValueError(f"unbalanced port declaration in {module_name}")
        if paren or bracket or brace:
            raise ValueError(f"unbalanced port header in {module_name}")
        parts.append(header[start:].strip())
        return parts

    header: str | None = None
    for candidate in sorted(directory.glob("*.sv")):
        source = candidate.read_text(encoding="utf-8", errors="replace")
        source = re.sub(r"/\*.*?\*/", " ", source, flags=re.DOTALL)
        source = re.sub(r"//[^\n]*", " ", source)
        module_match = module_pattern.search(source)
        if not module_match:
            continue
        cursor = module_match.end()
        while cursor < len(source) and source[cursor].isspace():
            cursor += 1
        if cursor < len(source) and source[cursor] == "#":
            cursor += 1
            while cursor < len(source) and source[cursor].isspace():
                cursor += 1
            if cursor >= len(source) or source[cursor] != "(":
                raise ValueError(f"cannot parse parameter header for generated module {module_name}")
            cursor = matching_paren(source, cursor) + 1
            while cursor < len(source) and source[cursor].isspace():
                cursor += 1
        if cursor >= len(source) or source[cursor] != "(":
            raise ValueError(f"cannot find ANSI port header for generated module {module_name}")
        close = matching_paren(source, cursor)
        header = source[cursor + 1:close]
        break
    if header is None:
        raise ValueError(f"generated SystemVerilog module {module_name} is missing below {directory}")

    declarations: list[str] = []
    connections: list[str] = []
    direction: str | None = None
    packed_width = ""
    qualifiers = {"wire", "reg", "logic", "bit", "signed", "unsigned", "var", "const", "tri"}
    for raw_port in split_ports(header):
        text = re.sub(r"\(\*.*?\*\)", " ", raw_port, flags=re.DOTALL).strip()
        if not text:
            continue
        direction_match = re.match(r"^(input|output|inout)\b\s*", text)
        if direction_match:
            direction = direction_match.group(1)
            text = text[direction_match.end():].strip()
            range_match = re.search(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", text)
            if range_match:
                width = abs(int(range_match.group(1)) - int(range_match.group(2))) + 1
                packed_width = f"[{width - 1}:0]"
            else:
                packed_width = ""
        elif direction is None:
            raise ValueError(f"cannot determine direction for {module_name} port declaration: {raw_port!r}")

        # Drop any default/unpacked dimensions, then remove net/type keywords.
        # This leaves the actual identifier rather than a token from a type or
        # annotation. The inherited direction/range handles ANSI shorthand such
        # as `input logic [7:0] a, b` without inventing a new port.
        declaration = text.split("=", 1)[0]
        declaration = re.sub(r"\[[^]]*\]", " ", declaration)
        names = [
            token for token in re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", declaration)
            if token not in qualifiers
        ]
        if not names:
            raise ValueError(f"cannot parse {module_name} port declaration: {raw_port!r}")
        port_name = names[-1]
        width_decl = f"{packed_width} " if packed_width else ""
        declarations.append(f"  wire {width_decl}{port_name};")
        connections.append(f"    .{port_name}({port_name})")
    if not declarations:
        raise ValueError(f"generated SystemVerilog module {module_name} has no parsed ports")
    if len({connection.split(".", 1)[1].split("(", 1)[0] for connection in connections}) != len(connections):
        raise ValueError(f"generated SystemVerilog module {module_name} has duplicate parsed port names")
    return declarations, connections


def prepare(directory: Path) -> None:
    params = json.loads((directory / "params.json").read_text())
    if params.get("compile_only_top"):
        compile_top = str(params["compile_only_top"])
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", compile_top):
            raise ValueError(f"invalid compile-only top module name: {compile_top}")
        # Instantiate the real connected decoder top and explicitly connect
        # every generated port. This avoids both an unused/stub hierarchy and
        # VCS warnings for omitted DUT ports without launching simulation.
        declarations, connections = compile_only_port_declarations(directory, compile_top)
        tb = "module tb;\n" + "\n".join(declarations) + "\n"
        tb += f"  {compile_top} dut(\n" + ",\n".join(connections) + "\n  );\nendmodule\n"
        (directory / "tb.sv").write_text(tb)
        return
    in_dim, out_dim = params["in_dim"], params["out_dim"]
    in_lanes, out_lanes = params["in_lanes"], params["out_lanes"]
    mac_rows, mac_cols = params["mac_rows"], params["mac_cols"]
    in_beats, out_beats = in_dim // in_lanes, out_dim // out_lanes
    wide_array = mac_cols > in_lanes
    tokens = 36
    inputs = [[((token * 3 + element * 5) % 7 - 3) / 4 for element in range(in_dim)] for token in range(tokens)]
    weights = [[((output * 7 + element * 3) % 11 - 5) / 8 for element in range(in_dim)] for output in range(out_dim)]
    biases = [(output % 5 - 2) / 8 if params["has_bias"] else 0.0 for output in range(out_dim)]
    outputs = [[sum(value * weight for value, weight in zip(vector, row)) + bias for row, bias in zip(weights, biases)] for vector in inputs]
    if params["activation"] == "relu":
        outputs = [[max(0.0, value) for value in vector] for vector in outputs]
    refill_bits = int(params.get("refill_data_width_bits", 512))
    if (
        refill_bits < 64
        or refill_bits % 32
        or (refill_bits & (refill_bits - 1)) != 0
    ):
        raise ValueError(f"new generated designs require a supported full-beat refill_data_width_bits, got {refill_bits}")
    refill_words_per_beat = refill_bits // 32
    if refill_bits != int(params.get("refill_data_width_bits", refill_bits)):
        raise ValueError("fixture refill contract width must match generated parameter width")
    integer_mode = bool(params.get("integer_mode", False))
    weight_bits = int(params.get("weight_bits", params["elem_bits"]))
    images: dict[str, list[str]] = {"input": [], "weights": [], "bias": [], "golden": []}

    # Keep the legacy FP oracle above unchanged. W4A8 has an independent
    # integer stimulus and golden path: input activations are quantized at
    # four real-value units per code, matrix weights at eight units per code,
    # and bias at the product scale (32 units per accumulator code). The
    # output requantization is therefore accumulator/8 with nearest-even
    # rounding and signed INT8 saturation.
    if integer_mode:
        if params["elem_bits"] != 8 or weight_bits != 4 or params["output_bits"] != 8:
            raise ValueError("the integer fixture must be signed W4A8 with INT8 output")
        input_q = [[max(-128, min(127, round(value * 4.0))) for value in row] for row in inputs]
        weight_q = [[max(-8, min(7, round(value * 8.0))) for value in row] for row in weights]
        bias_q = [round(value * 32.0) for value in biases]
        for token in range(tokens):
            for beat in range(in_beats):
                start = beat * in_lanes
                images["input"].append(packed_signed(input_q[token][start:start + in_lanes], 8))
        weight_rows = mac_rows if wide_array else out_lanes
        weight_cols = mac_cols if wide_array else in_lanes
        for output_tile in range(out_dim // weight_rows):
            for input_tile in range(in_dim // weight_cols):
                tile_values = []
                for output_lane in range(weight_rows):
                    output_index = output_tile * weight_rows + output_lane
                    for input_lane in range(weight_cols):
                        input_index = input_tile * weight_cols + input_lane
                        tile_values.append(weight_q[output_index][input_index])
                images["weights"].append(packed_signed(tile_values, 4))
        for beat in range(out_beats):
            start = beat * out_lanes
            images["bias"].append(packed_signed(bias_q[start:start + out_lanes], 32))

        def requantize_fixture(value: int) -> int:
            # Activations are x4 and weights x8, so the INT32 dot product
            # is in x32 units while the INT8 output is x4. The declared Q31
            # multiplier 0x10000000 therefore divides by eight.
            sign = -1 if value < 0 else 1
            quotient, remainder = divmod(abs(value), 8)
            if remainder > 4 or (remainder == 4 and (quotient & 1)):
                quotient += 1
            rounded = sign * quotient
            return max(-128, min(127, rounded))

        integer_outputs = []
        for token in range(tokens):
            row = []
            for output_index in range(out_dim):
                accumulator = sum(a * w for a, w in zip(input_q[token], weight_q[output_index])) + bias_q[output_index]
                row.append(requantize_fixture(accumulator))
            if params["activation"] == "relu":
                row = [max(0, value) for value in row]
            integer_outputs.append(row)
        for token in range(tokens):
            for beat in range(out_beats):
                start = beat * out_lanes
                images["golden"].append(packed_signed(integer_outputs[token][start:start + out_lanes], 8))
    else:
        for token in range(tokens):
            for beat in range(in_beats):
                start = beat * in_lanes
                images["input"].append(packed(inputs[token][start:start + in_lanes], params["elem_bits"]))
        weight_rows = mac_rows if wide_array else out_lanes
        weight_cols = mac_cols if wide_array else in_lanes
        for output_tile in range(out_dim // weight_rows):
            for input_tile in range(in_dim // weight_cols):
                tile_values = []
                for output_lane in range(weight_rows):
                    output_index = output_tile * weight_rows + output_lane
                    for input_lane in range(weight_cols):
                        input_index = input_tile * weight_cols + input_lane
                        tile_values.append(weights[output_index][input_index])
                images["weights"].append(packed(tile_values, weight_bits))
        for beat in range(out_beats):
            start = beat * out_lanes
            images["bias"].append(packed(biases[start:start + out_lanes], 32))
        for token in range(tokens):
            for beat in range(out_beats):
                start = beat * out_lanes
                images["golden"].append(packed(outputs[token][start:start + out_lanes], params["output_bits"]))

    for name, words in images.items():
        (directory / f"{name}.memh").write_text("\n".join(words) + "\n")
    weight_word_bits = ((mac_rows * mac_cols) if wide_array else (in_lanes * out_lanes)) * weight_bits
    if weight_word_bits <= 0 or weight_word_bits % 32:
        raise ValueError(f"weight cache words must contain complete 32-bit image words, got {weight_word_bits} bits")
    image_words_per_cache_word = weight_word_bits // 32
    image_words_32 = len(images["weights"]) * image_words_per_cache_word
    if image_words_32 <= 0:
        raise ValueError("weight image must contain at least one 32-bit image word")

    # Materialize the actual selected wide refill payload. Each cache word is
    # unpacked into little-endian 32-bit image words, then packed into one
    # full-width board beat. The final beat is zero-padded only in unused lanes;
    # validWords records the admitted tail count for the loader/cache ABI.
    weight_image_words = []
    for cache_word in images["weights"]:
        cache_value = int(cache_word, 16)
        for word_index in range(image_words_per_cache_word):
            weight_image_words.append((cache_value >> (word_index * 32)) & 0xffffffff)
    if len(weight_image_words) != image_words_32:
        raise ValueError("weight image unpacking changed the complete 32-bit word count")
    refill_payload_lines = []
    refill_valid_words = []
    for beat_start in range(0, image_words_32, refill_words_per_beat):
        beat_words = weight_image_words[beat_start:beat_start + refill_words_per_beat]
        payload_value = sum(word << (index * 32) for index, word in enumerate(beat_words))
        refill_payload_lines.append(f"{payload_value:0{refill_bits // 4}x}")
        refill_valid_words.append(len(beat_words))
    (directory / "weights_refill.memh").write_text("\n".join(refill_payload_lines) + "\n")
    (directory / "weights_refill_valid_words.memh").write_text(
        "\n".join(f"{value:x}" for value in refill_valid_words) + "\n"
    )

    full_beats = image_words_32 // refill_words_per_beat
    tail_valid_words = image_words_32 % refill_words_per_beat or refill_words_per_beat
    refill_contract = {
        "refill_data_width_bits": refill_bits,
        "refill_words_per_beat": refill_words_per_beat,
        "weight_image_words_32": image_words_32,
        "full_beats": full_beats,
        "tail_valid_words": tail_valid_words,
        "payload_word_order": "low_to_high_little_endian_32bit_words",
        "payload_tail_valid_words": tail_valid_words,
        "cache_tile_words": int(params.get("cache_tile_words", 256)),
        "cache_tile_count": int(params.get("cache_tile_count", 2)),
        "cross_token_reuse_tokens": int(params.get("cross_token_reuse_tokens", 16)),
        "payload_file": "weights_refill.memh",
        "valid_words_file": "weights_refill_valid_words.memh",
        "payload_beats": len(refill_payload_lines),
        "payload_word_order": "low_to_high_little_endian_32bit_words",
        "word_order": "little_endian_32bit_words_low_to_high",
        "tail_policy": "validWords reports only the final partial beat words",
    }
    (directory / "refill_contract.json").write_text(json.dumps(refill_contract, indent=2) + "\n")
    ports = (directory / "Linear.sv").read_text().split(");", 1)[0]
    expanded = re.sub(r"//[^\n]*", "", ports + ");")
    direction, width = "", ""
    declarations = []
    for segment in expanded[expanded.index("(") + 1:expanded.rindex(")")].split(","):
        fields = segment.split()
        if fields[0] in ("input", "output"):
            direction = fields.pop(0)
            width = fields.pop(0) if fields[0].startswith("[") else ""
        declarations.append(f"  logic {width} {fields[0]};")
    elem_width = in_lanes * params["elem_bits"]
    out_width = out_lanes * params["output_bits"]
    weight_width = (mac_rows * mac_cols if wide_array else in_lanes * out_lanes) * int(params.get("weight_bits", params["elem_bits"]))
    weight_writes = (out_dim // mac_rows) * (in_dim // mac_cols) if wide_array else in_beats * out_beats
    terms = in_dim // mac_cols
    expected_issues = tokens * out_beats * (out_lanes // params["mac_rows"]) * terms
    text = f"""`timescale 1ns/1ps
module tb;
{chr(10).join(declarations)}
  Linear dut(.*);
  logic [{elem_width - 1}:0] inputs [0:{tokens * in_beats - 1}];
  logic [{out_width - 1}:0] golden [0:{tokens * out_beats - 1}];
    logic [{weight_width - 1}:0] weights [0:{weight_writes - 1}];
  logic [{out_lanes * 32 - 1}:0] biases [0:{out_beats - 1}];
  integer cycles = 0, received = 0, sent = 0, issues = 0;
  integer burst = 0, longest_burst = 0, overlapped_input = 0, overlapped_output = 0;
  integer run_cycles = 0;
  bit running = 0;
  bit stalled = 0;
  logic [{out_width - 1}:0] held_output;
  initial begin clock = 0; forever #5 clock = ~clock; end
  always @(negedge clock) begin
  io_out_ready = running && ((run_cycles > 100 && run_cycles % 11 < 7) || run_cycles > 20000);
  end
  always @(posedge clock) begin
    cycles = cycles + 1;
    if (running) begin
      run_cycles = run_cycles + 1;
      if (io_in_valid && io_in_ready) sent = sent + 1;
      if (dut.readValid && dut.allMulReady) begin
        issues = issues + 1;
        burst = burst + 1;
        if (burst > longest_burst) longest_burst = burst;
        if (io_in_valid && io_in_ready) overlapped_input = overlapped_input + 1;
        if (io_out_valid && io_out_ready) overlapped_output = overlapped_output + 1;
      end else burst = 0;
      if (stalled && (!io_out_valid || io_out_bits_data !== held_output)) $fatal(1, "output changed under backpressure");
      stalled = io_out_valid && !io_out_ready;
      held_output = io_out_bits_data;
      if (io_out_valid && io_out_ready) begin
        if (received >= {tokens * out_beats}) $fatal(1, "extra output");
        if (io_out_bits_data !== golden[received]) $fatal(1, "numeric mismatch beat=%0d actual=%h expected=%h", received, io_out_bits_data, golden[received]);
        if (io_out_bits_addr !== received) $fatal(1, "address mismatch");
        if (io_out_bits_last !== (received % {out_beats} == {out_beats - 1})) $fatal(1, "last mismatch");
        if (io_out_bits_st !== (received == 0)) $fatal(1, "start mismatch");
        received = received + 1;
      end
      if (received == {tokens * out_beats}) begin
        if (sent != {tokens * in_beats} || issues != {expected_issues}) $fatal(1, "dropped or duplicated work sent=%0d issues=%0d", sent, issues);
        if (longest_burst < {terms * 16}) $fatal(1, "cross-token MAC requests are not continuously issued burst=%0d", longest_burst);
        if ({terms} > 16 && overlapped_input == 0) $fatal(1, "no input/compute overlap");
        if ({terms} >= 16 && overlapped_output == 0) $fatal(1, "no compute/output overlap");
        $display("PASS beats=%0d cycles=%0d issues=%0d longest_burst=%0d input_overlap=%0d output_overlap=%0d", received, run_cycles, issues, longest_burst, overlapped_input, overlapped_output);
        $finish;
      end
      if (run_cycles > 100000) $fatal(1, "timeout received=%0d issues=%0d", received, issues);
    end
  end
  initial begin
    $readmemh("input.memh", inputs);
    $readmemh("weights.memh", weights);
    $readmemh("bias.memh", biases);
    $readmemh("golden.memh", golden);
    reset = 1; io_start = 0; io_cfg_seqlen = {tokens}; io_cfg_prefill = 1; io_cfg_singleQuery = 0; io_cfgValid = 0;
    io_scale_outScale = 32'h{('10000000' if integer_mode else '3f800000')}; io_scale_biasScale = 32'h{('80000000' if integer_mode else '3f800000')};
    io_in_valid = 0; io_in_bits_data = 0; io_in_bits_st = 0; io_in_bits_last = 0; io_in_bits_addr = 0;
    io_weight_valid = 0; io_weight_bits_addr = 0; io_weight_bits_data = 0;
    io_bias_valid = 0; io_bias_bits_addr = 0; io_bias_bits_data = 0; io_out_ready = 0;
    repeat (20) @(negedge clock);
    reset = 0;
    for (integer index = 0; index < {weight_writes}; index = index + 1) begin
      io_weight_valid = 1; io_weight_bits_addr = index; io_weight_bits_data = weights[index];
      do @(posedge clock); while (!io_weight_ready);
      @(negedge clock);
    end
    io_weight_valid = 0;
    if ({int(params['has_bias'])}) begin
      for (integer index = 0; index < {out_beats}; index = index + 1) begin
        io_bias_valid = 1; io_bias_bits_addr = index; io_bias_bits_data = biases[index];
        do @(posedge clock); while (!io_bias_ready);
        @(negedge clock);
      end
      io_bias_valid = 0;
    end
    io_start = 1; io_cfgValid = 1;
    @(negedge clock); io_start = 0; io_cfgValid = 0; running = 1;
    for (integer index = 0; index < {tokens * in_beats}; index = index + 1) begin
      io_in_valid = 1; io_in_bits_data = inputs[index]; io_in_bits_addr = index;
      io_in_bits_st = index == 0; io_in_bits_last = index % {in_beats} == {in_beats - 1};
      do @(posedge clock); while (!io_in_ready);
      @(negedge clock);
      if (index % 11 == 4) begin
        io_in_valid = 0; repeat (2) @(negedge clock);
      end
    end
    io_in_valid = 0;
  end
endmodule
"""
    (directory / "tb.sv").write_text(text)


if __name__ == "__main__":
    for manifest in sorted(Path(sys.argv[1]).glob("*/params.json")):
        prepare(manifest.parent)
        print(manifest.parent.name)
