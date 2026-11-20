"""Run a full-size, single-operator RTWSR RTL test with the Huginn payload."""

import hashlib
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_DIR = ROOT / "results/plan5/huginn_usw512"
MANIFEST_PATH = PAYLOAD_DIR / "manifest.json"
WEIGHTS_PATH = PAYLOAD_DIR / "weights.usw512"
GAMMA_PATH = PAYLOAD_DIR / "gamma.fp16"
REPORT_PATH = ROOT / "results/plan5/rtwsr_huginn_mlp_proj_payload_rtl.txt"
LAYER_NAME = "transformer.core_block.0.mlp.proj"
VERILATOR_PATH = Path("/usr/bin/verilator")
ACTIVATION_SCALE_FP16 = 0x3C00
ACTIVATION_SCALE_Q24 = 1 << 24
Q48 = 1 << 48


def fp16_to_q24(bits):
    exponent = (bits >> 10) & 0x1F
    significand = bits & 0x3FF
    if exponent == 0:
        magnitude = significand
    elif exponent == 0x1F:
        magnitude = 0
    else:
        magnitude = (0x400 + significand) << (exponent - 1)
    value = -magnitude if bits & 0x8000 else magnitude
    return min(0x7FFFFFFF, max(-0x80000000, value))


def fixed_product_q12(base_q12, scale_q48):
    product = int(base_q12) * int(scale_q48)
    result = product >> 48
    round_bit = (product >> 47) & 1
    lower_bits = product & ((1 << 47) - 1)
    if round_bit and (lower_bits or (result & 1)):
        result += 1
    return min(0x7FFFFFFF, max(-0x80000000, result))


def write_reference_inputs(directory, layer, weight_data, gamma_data):
    rows, columns = layer["shape"]
    windows = layer["windows_per_row"]
    rounds = layer["rounds"]
    records = np.frombuffer(weight_data, dtype=np.uint8).reshape(rows, windows, 64)
    gamma_bits = np.frombuffer(gamma_data, dtype="<u2").reshape(rounds, rows)
    gamma_values = np.frombuffer(gamma_data, dtype="<f2")
    if not np.isfinite(gamma_values).all():
        raise ValueError("the selected Gamma payload contains non-finite FP16 values")

    with (directory / "payload_words.mem").open("w") as stream:
        for record in records.reshape(-1, 64):
            stream.write(record[::-1].tobytes().hex() + "\n")

    with (directory / "payload_gamma.mem").open("w") as stream:
        for value in gamma_bits.reshape(-1):
            stream.write(f"{int(value):04x}\n")

    dense_sum = np.zeros(rows, dtype=np.int64)
    sparse_sum_q12 = np.zeros(rows, dtype=np.int64)
    element = np.arange(256, dtype=np.int64)
    for window in range(windows):
        window_records = records[:, window, :]
        activation = ((window * 37 + element * 29) % 256) - 128
        trits = np.empty((rows, 256), dtype=np.int8)
        for byte_index in range(51):
            code = window_records[:, 12 + byte_index].astype(np.int16)
            for digit_index in range(5):
                trits[:, byte_index * 5 + digit_index] = (
                    (code // (3 ** digit_index)) % 3 - 1
                )
        trits[:, 255] = window_records[:, 63].astype(np.int16) - 1
        dense_sum += np.sum(trits.astype(np.int64) * activation, axis=1)

        for slot in range(4):
            slot_offset = slot * 3
            raw = window_records[:, slot_offset].astype(np.uint16)
            raw |= window_records[:, slot_offset + 1].astype(np.uint16) << 8
            values = raw.astype(np.int16).astype(np.int64)
            indices = window_records[:, slot_offset + 2]
            sparse_sum_q12 += values * activation[indices]

    base_q12 = dense_sum * 4096 + sparse_sum_q12
    with (directory / "payload_expected.mem").open("w") as stream:
        for round_index in range(rounds):
            for channel in range(rows):
                gamma_q24 = fp16_to_q24(int(gamma_bits[round_index, channel]))
                scale_q48 = gamma_q24 * ACTIVATION_SCALE_Q24
                result = fixed_product_q12(base_q12[channel], scale_q48)
                stream.write(f"{result & 0xFFFFFFFF:08x}\n")

    return rows, columns, windows, rounds


def main():
    manifest = json.loads(MANIFEST_PATH.read_text())
    layer = next(row for row in manifest["layers"] if row["name"] == LAYER_NAME)
    if layer["shape"] != [5280, 17920] or layer["rounds"] != 32:
        raise ValueError("the selected payload is not the full Huginn 5280x17920, 32-round matrix")

    with WEIGHTS_PATH.open("rb") as stream:
        stream.seek(layer["usw512_offset_bytes"])
        weight_data = stream.read(layer["usw512_bytes"])
    with GAMMA_PATH.open("rb") as stream:
        stream.seek(layer["gamma_fp16_offset_bytes"])
        gamma_data = stream.read(layer["gamma_fp16_bytes"])
    if len(weight_data) != layer["usw512_bytes"] or len(gamma_data) != layer["gamma_fp16_bytes"]:
        raise ValueError("the selected model payload segment is truncated")

    sources = [
        "hardware/radix3_5trit_decoder.sv",
        "hardware/scale_hoisted_ternary_lane.sv",
        "hardware/usw512_word_decoder.sv",
        "hardware/usw512_dual_track_channel.sv",
        "hardware/usw512_channel_array.sv",
        "hardware/uram_active_pool_bank.sv",
        "hardware/rtwsr_top.sv",
        "hardware/tests/tb_rtwsr_top.sv",
    ]
    with tempfile.TemporaryDirectory(prefix="loopquant_plan5_payload_") as temp_name:
        temp_dir = Path(temp_name)
        rows, columns, windows, rounds = write_reference_inputs(
            temp_dir, layer, weight_data, gamma_data
        )
        build_dir = temp_dir / "obj_dir"
        command = [
            str(VERILATOR_PATH), "--binary", "--timing", "-Wno-fatal", "--build-jobs", "1",
            "--top-module", "tb_rtwsr_top_payload", "--Mdir", str(build_dir),
        ] + [str(ROOT / source) for source in sources]
        build = subprocess.run(
            command, cwd=temp_dir, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False
        )
        if build.returncode:
            raise RuntimeError("Verilator build failed:\n" + "\n".join(build.stdout.splitlines()[-60:]))

        simulation = subprocess.run(
            [str(build_dir / "Vtb_rtwsr_top_payload")], cwd=temp_dir,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
        )
        if simulation.returncode:
            raise RuntimeError("payload RTL simulation failed:\n" + "\n".join(simulation.stdout.splitlines()[-60:]))

    metrics = [
        line.strip() for line in simulation.stdout.splitlines()
        if line.startswith("PASS:") or line.startswith("MEASURE:")
    ]
    if not any("168960 channel-round outputs" in line for line in metrics):
        raise RuntimeError("the simulator did not report all full-size channel-round comparisons")

    report = [
        f"created: {datetime.now().astimezone().isoformat()}",
        "simulator: Verilator 5.020, --binary --timing, build jobs 1",
        f"payload manifest matrices: {len(manifest['layers'])}",
        "evaluation scope: one linear operator; not a Transformer block or recurrent-core evaluation",
        f"layer: {LAYER_NAME}",
        f"shape: {rows} x {columns}",
        f"rounds: {rounds}",
        "invocation semantics: repeat the same operator; no output-to-next-invocation feedback",
        f"windows per row: {windows}",
        f"weight segment bytes: {len(weight_data)}",
        f"weight segment sha256: {hashlib.sha256(weight_data).hexdigest()}",
        f"Gamma segment bytes: {len(gamma_data)}",
        f"Gamma segment sha256: {hashlib.sha256(gamma_data).hexdigest()}",
        "activation: generated deterministic signed INT8 pattern, activation scale FP16 1.0; pattern repeats per invocation",
        "reference: independent radix-3/Q4.12 decode and Q8.24 fixed-point scale",
        *metrics,
    ]
    temporary_report = REPORT_PATH.with_suffix(REPORT_PATH.suffix + ".tmp")
    temporary_report.write_text("\n".join(report) + "\n")
    temporary_report.replace(REPORT_PATH)
    print("\n".join(report))


if __name__ == "__main__":
    main()
