"""Preflight and export the Plan 3 Huginn core as USW-512 payloads."""

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile

import numpy as np
import torch

try:
    from .pack_usw512 import (
        DENSE_BYTES, SLOT_COUNT, WINDOW_SIZE, WORD_BYTES,
        pack_matrix_to_usw512, window_slot_mask,
    )
except ImportError:
    from pack_usw512 import (
        DENSE_BYTES, SLOT_COUNT, WINDOW_SIZE, WORD_BYTES,
        pack_matrix_to_usw512, window_slot_mask,
    )


ROOT = Path("/home/kemove/hyyuan/LoopQuant")
PLAN3_CHECKPOINT = ROOT / "results/plan3/pre_sparse_ridge_twn_sparse005_g-1.pt"
BETA_CHECKPOINT = ROOT / "results/plan3/tf_pre_sparse_ridge_twn_sparse005_g-1.pt"
PROBE_CHECKPOINT = ROOT / "results/plan1/probe4_calibration.pt"
REPORT_PATH = ROOT / "results/plan5/model_preflight.json"
OUTPUT_DIR = ROOT / "results/plan5/huginn_usw512"
SPARSE_FRACTION = 0.005
EXPECTED_LAYERS = 16
BETA_RANGE = (0.80, 2.00)
Q4_12_SCALE = 1 << 12
QUANTIZATION = {
    "method": "pre_sparse_ridge_twn_sparse005_tf_norm_step_scale",
    "group_size": -1,
    "damping": 1.0,
    "trajectory_weighting": "early8_tail",
    "beta": "tf_norm",
    "beta_clip": list(BETA_RANGE),
    "candidate_sparse_fraction": SPARSE_FRACTION,
    "encoded_sparse_fraction_policy": "up to four retained values per 256-column window; excess values are projected to the ternary grid",
}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def retained_coordinates(retained, element_count, fraction):
    count = math.ceil(element_count * fraction)
    indices = retained["indices"][:count].to(torch.int64).numpy()
    values = retained["values"][:count].float().numpy()
    if indices.size != count or values.size != count:
        raise ValueError("probe retained checkpoint has fewer coordinates than required")
    if np.any(indices < 0) or np.any(indices >= element_count):
        raise ValueError("probe retained checkpoint contains an out-of-range index")
    order = np.argsort(indices, kind="stable")
    indices = indices[order]
    values = values[order]
    if np.any(indices[1:] == indices[:-1]):
        raise ValueError("probe retained checkpoint contains duplicate indices")
    return indices, values


def analyze_layer(name, weight, retained, beta, fraction=SPARSE_FRACTION):
    if weight.ndim != 2:
        raise ValueError(f"{name}: checkpoint matrix must be two-dimensional")
    channels, columns = map(int, weight.shape)
    element_count = channels * columns
    indices, sparse_values = retained_coordinates(retained, element_count, fraction)
    checkpoint_values = weight.reshape(-1)[torch.from_numpy(indices)].float().numpy()
    retained_value_mismatches = int(np.count_nonzero(checkpoint_values != sparse_values))

    chunks = (columns + WINDOW_SIZE - 1) // WINDOW_SIZE
    alpha = np.zeros(channels, dtype=np.float32)
    layer = {
        "shape": [channels, columns],
        "elements": element_count,
        "sparse_coordinates": int(indices.size),
        "retained_value_mismatches": retained_value_mismatches,
        "windows": channels * chunks,
        "windows_over_capacity": 0,
        "coordinates_over_capacity": 0,
        "maximum_window_occupancy": 0,
        "coordinates_folded_to_ternary": 0,
        "folded_ternary_nonzero": 0,
        "folded_ternary_zero": 0,
        "folded_projection_abs_error_sum": 0.0,
        "folded_projection_max_abs_error": 0.0,
        "q4_12_checked_slots": 0,
        "q4_12_exact_slots": 0,
        "q4_12_saturated_slots": 0,
        "q4_12_invalid_alpha_slots": 0,
        "q4_12_rounded_to_zero_slots": 0,
        "q4_12_inexact_slots": 0,
        "q4_12_abs_error_sum": 0.0,
        "q4_12_max_abs_error": 0.0,
        "zero_alpha_rows": 0,
        "nonternary_dense_values": 0,
        "reconstruction_mismatch_rows": 0,
        "beta_shape": list(beta.shape),
        "beta_out_of_range_values": 0,
        "gamma_fp16_nonfinite_values": 0,
    }

    if beta.ndim != 2 or beta.shape[1] != channels:
        raise ValueError(f"{name}: beta must have shape [R, C_out]")
    beta_values = beta.float().numpy().astype(np.float64, copy=False)
    layer["beta_out_of_range_values"] = int(
        np.count_nonzero((beta_values < BETA_RANGE[0]) | (beta_values > BETA_RANGE[1]))
    )

    for row_index in range(channels):
        start = row_index * columns
        first = np.searchsorted(indices, start, side="left")
        last = np.searchsorted(indices, start + columns, side="left")
        row_indices = indices[first:last] - start
        row_sparse_values = sparse_values[first:last]
        row = weight[row_index].float().numpy().astype(np.float32, copy=True)
        row_dense = row.copy()
        row_dense[row_indices] = 0.0
        nonzero = np.flatnonzero(row_dense)

        if nonzero.size:
            row_alpha = abs(float(row_dense[nonzero[0]]))
            alpha[row_index] = row_alpha
            layer["nonternary_dense_values"] += int(
                np.count_nonzero(np.abs(row_dense[nonzero]) != row_alpha)
            )
            if row_alpha == 0.0:
                layer["zero_alpha_rows"] += 1
        elif row_indices.size:
            layer["zero_alpha_rows"] += 1

        reconstructed = np.sign(row_dense) * alpha[row_index]
        if row_indices.size:
            reconstructed[row_indices] = row_sparse_values
        reconstructed_bf16 = torch.from_numpy(reconstructed.astype(np.float32)).to(weight.dtype)
        if not torch.equal(reconstructed_bf16, weight[row_index]):
            layer["reconstruction_mismatch_rows"] += 1

    window_keys = (indices // columns) * chunks + (indices % columns) // WINDOW_SIZE
    occupancy = np.bincount(window_keys, minlength=channels * chunks)
    overfull_keys = np.flatnonzero(occupancy > SLOT_COUNT)
    layer["windows_over_capacity"] = int(overfull_keys.size)
    layer["coordinates_over_capacity"] = int(
        np.sum(occupancy[overfull_keys] - SLOT_COUNT, dtype=np.int64)
    )
    layer["maximum_window_occupancy"] = int(occupancy.max(initial=0))
    q4_mask = window_slot_mask(indices, sparse_values, columns)
    folded_values = sparse_values[~q4_mask].astype(np.float64)
    folded_rows = indices[~q4_mask] // columns
    folded_alpha = alpha[folded_rows].astype(np.float64)
    valid_folded = folded_alpha > 0.0
    layer["coordinates_folded_to_ternary"] = int(folded_values.size)
    if valid_folded.any():
        projected = np.clip(
            np.rint(folded_values[valid_folded] / folded_alpha[valid_folded]), -1, 1
        )
        folded_errors = np.abs(
            projected * folded_alpha[valid_folded] - folded_values[valid_folded]
        )
        layer["folded_ternary_nonzero"] = int(np.count_nonzero(projected))
        layer["folded_ternary_zero"] = int(projected.size - np.count_nonzero(projected))
        layer["folded_projection_abs_error_sum"] = float(folded_errors.sum(dtype=np.float64))
        layer["folded_projection_max_abs_error"] = float(folded_errors.max(initial=0.0))

    checked_rows = indices[q4_mask] // columns
    checked_values = sparse_values[q4_mask].astype(np.float64)
    checked_alpha = alpha[checked_rows].astype(np.float64)
    layer["q4_12_checked_slots"] = int(checked_values.size)
    positive_alpha = checked_alpha > 0.0
    layer["q4_12_invalid_alpha_slots"] = int(np.count_nonzero(~positive_alpha))
    if positive_alpha.any():
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            scaled = checked_values[positive_alpha] / checked_alpha[positive_alpha] * Q4_12_SCALE
            rounded = np.rint(scaled)
        saturated = (~np.isfinite(rounded)) | (rounded < -32768) | (rounded > 32767)
        fixed = np.clip(np.nan_to_num(rounded, nan=0.0, posinf=32767.0, neginf=-32768.0), -32768, 32767)
        rounded_zero = fixed == 0
        exact = (
            (~saturated) & (~rounded_zero) & (scaled == fixed) &
            (checked_alpha[positive_alpha] * (fixed / Q4_12_SCALE) == checked_values[positive_alpha])
        )
        inexact = (~saturated) & (~rounded_zero) & (~exact)
        layer["q4_12_saturated_slots"] = int(np.count_nonzero(saturated))
        layer["q4_12_rounded_to_zero_slots"] = int(np.count_nonzero(rounded_zero))
        layer["q4_12_exact_slots"] = int(np.count_nonzero(exact))
        layer["q4_12_inexact_slots"] = int(np.count_nonzero(inexact))
        q4_errors = np.abs(
            checked_alpha[positive_alpha] * (fixed / Q4_12_SCALE) - checked_values[positive_alpha]
        )
        layer["q4_12_abs_error_sum"] = float(q4_errors.sum(dtype=np.float64))
        layer["q4_12_max_abs_error"] = float(q4_errors.max(initial=0.0))

    gamma = beta_values * alpha[np.newaxis, :]
    with np.errstate(over="ignore", invalid="ignore"):
        gamma_fp16 = gamma.astype(np.float16)
    layer["gamma_fp16_nonfinite_values"] = int(np.count_nonzero(~np.isfinite(gamma_fp16)))
    return layer, alpha


def preflight_model(bank, retained_by_layer, beta_by_layer,
                    fraction=SPARSE_FRACTION, expected_layers=EXPECTED_LAYERS):
    names = set(bank)
    if names != set(retained_by_layer) or names != set(beta_by_layer):
        raise ValueError("checkpoint layer names differ across T, mask, and beta sources")
    if len(names) != expected_layers:
        raise ValueError(f"expected {expected_layers} core matrices, found {len(names)}")

    report_layers = {}
    alpha_by_layer = {}
    for name in sorted(names):
        weight, _ = bank[name]
        layer_report, alpha = analyze_layer(
            name, weight, retained_by_layer[name], beta_by_layer[name], fraction
        )
        report_layers[name] = layer_report
        alpha_by_layer[name] = alpha

    count_fields = (
        "elements", "sparse_coordinates", "retained_value_mismatches", "windows",
        "windows_over_capacity", "coordinates_over_capacity", "coordinates_folded_to_ternary",
        "folded_ternary_nonzero", "folded_ternary_zero", "q4_12_checked_slots",
        "q4_12_exact_slots", "q4_12_saturated_slots", "q4_12_invalid_alpha_slots",
        "q4_12_rounded_to_zero_slots", "q4_12_inexact_slots", "zero_alpha_rows", "nonternary_dense_values",
        "reconstruction_mismatch_rows", "beta_out_of_range_values",
        "gamma_fp16_nonfinite_values",
    )
    totals = {field: sum(row[field] for row in report_layers.values()) for field in count_fields}
    totals["maximum_window_occupancy"] = max(
        (row["maximum_window_occupancy"] for row in report_layers.values()), default=0
    )
    totals["folded_projection_abs_error_sum"] = sum(
        row["folded_projection_abs_error_sum"] for row in report_layers.values()
    )
    totals["folded_projection_max_abs_error"] = max(
        (row["folded_projection_max_abs_error"] for row in report_layers.values()), default=0.0
    )
    totals["folded_projection_mean_abs_error"] = (
        totals["folded_projection_abs_error_sum"] / totals["coordinates_folded_to_ternary"]
        if totals["coordinates_folded_to_ternary"] else 0.0
    )
    totals["q4_12_abs_error_sum"] = sum(
        row["q4_12_abs_error_sum"] for row in report_layers.values()
    )
    totals["q4_12_max_abs_error"] = max(
        (row["q4_12_max_abs_error"] for row in report_layers.values()), default=0.0
    )
    totals["q4_12_mean_abs_error"] = (
        totals["q4_12_abs_error_sum"] / totals["q4_12_checked_slots"]
        if totals["q4_12_checked_slots"] else 0.0
    )
    compatible = (
        totals["retained_value_mismatches"] == 0 and
        totals["q4_12_invalid_alpha_slots"] == 0 and
        totals["zero_alpha_rows"] == 0 and
        totals["nonternary_dense_values"] == 0 and
        totals["reconstruction_mismatch_rows"] == 0 and
        totals["beta_out_of_range_values"] == 0 and
        totals["gamma_fp16_nonfinite_values"] == 0
    )
    report = {
        "created": datetime.now().astimezone().isoformat(),
        "configuration": {
            "sparse_fraction": fraction,
            "window_size": WINDOW_SIZE,
            "outlier_slots_per_window": SLOT_COUNT,
            "q_format": "signed Q4.12",
            "q4_12_rounding": "nearest, ties to even",
            "q4_12_overflow": "saturate to signed int16",
            "overflow_window_policy": "keep four largest-magnitude W_sp values; project excess values to clip(round(W_sp/alpha), -1, 1)",
            "beta_range": list(BETA_RANGE),
            "expected_core_matrices": expected_layers,
        },
        "scope": "Plan 3 Huginn core_blocks[0..3] matrices; adapter has no matching Plan 3 T/W_sp/alpha/beta checkpoint",
        "compatible": compatible,
        "totals": totals,
        "layers": report_layers,
    }
    return report, alpha_by_layer


def write_json_atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def annotate_payload_manifest(manifest_path, preflight_path):
    manifest_path = Path(manifest_path)
    preflight_path = Path(preflight_path)
    manifest = json.loads(manifest_path.read_text())
    preflight = json.loads(preflight_path.read_text())
    if not preflight.get("compatible"):
        raise ValueError("quantization provenance requires a compatible preflight")
    if preflight["configuration"].get("sparse_fraction") != SPARSE_FRACTION:
        raise ValueError("preflight sparse fraction differs from the payload configuration")
    sources = preflight.get("sources", {})
    required_sources = ("plan3_checkpoint", "beta_checkpoint", "probe_checkpoint")
    if any(name not in sources or "sha256" not in sources[name] for name in required_sources):
        raise ValueError("preflight source fingerprints are incomplete")
    layer_names = {layer["name"] for layer in manifest.get("layers", [])}
    if layer_names != set(preflight.get("layers", {})):
        raise ValueError("payload and preflight layer sets differ")

    per_layer = {}
    for layer_name, values in preflight["layers"].items():
        encoded_slots = values["q4_12_checked_slots"] - values["q4_12_rounded_to_zero_slots"]
        per_layer[layer_name] = {
            "candidate_outliers": values["sparse_coordinates"],
            "folded_to_ternary": values["coordinates_folded_to_ternary"],
            "encoded_sparse_slots": encoded_slots,
            "encoded_sparse_fraction": encoded_slots / values["elements"],
        }

    quantization = {
        **QUANTIZATION,
        "candidate_sparse_fraction": preflight["configuration"]["sparse_fraction"],
        "source_checkpoints": sources,
        "preflight": {
            "path": str(preflight_path),
            "totals": preflight["totals"],
        },
        "per_layer": per_layer,
        "payload_sha256": {
            "weights.usw512": file_sha256(manifest_path.parent / "weights.usw512"),
            "gamma.fp16": file_sha256(manifest_path.parent / "gamma.fp16"),
        },
    }
    manifest["quantization"] = quantization
    for layer in manifest["layers"]:
        layer["quantization"] = per_layer[layer["name"]]
    temporary = manifest_path.with_name(manifest_path.name + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(manifest_path)
    return manifest


def export_payload(bank, retained_by_layer, beta_by_layer, alpha_by_layer, output_dir,
                   fraction=SPARSE_FRACTION, quantization_metadata=None):
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent))
    manifest_layers = []
    try:
        weight_offset = 0
        gamma_offset = 0
        with (staging / "weights.usw512").open("wb") as weight_stream, \
                (staging / "gamma.fp16").open("wb") as gamma_stream:
            for name in sorted(bank):
                weight, _ = bank[name]
                channels, columns = map(int, weight.shape)
                indices, sparse_values = retained_coordinates(
                    retained_by_layer[name], channels * columns, fraction
                )
                ternary = np.sign(weight.float().numpy()).astype(np.int8)
                ternary.reshape(-1)[indices] = 0
                sparse = np.zeros(weight.shape, dtype=np.float64)
                sparse.reshape(-1)[indices] = sparse_values
                beta = beta_by_layer[name].float().numpy()
                packed, gamma, _, _ = pack_matrix_to_usw512(
                    ternary, sparse, alpha_by_layer[name], beta
                )
                weight_stream.write(packed)
                gamma_bytes = gamma.tobytes(order="C")
                gamma_stream.write(gamma_bytes)
                layer_manifest = {
                    "name": name,
                    "shape": [channels, columns],
                    "window_size": WINDOW_SIZE,
                    "windows_per_row": (columns + WINDOW_SIZE - 1) // WINDOW_SIZE,
                    "usw512_offset_bytes": weight_offset,
                    "usw512_bytes": len(packed),
                    "gamma_fp16_offset_bytes": gamma_offset,
                    "gamma_fp16_bytes": len(gamma_bytes),
                    "rounds": int(gamma.shape[0]),
                }
                if quantization_metadata and name in quantization_metadata.get("per_layer", {}):
                    layer_manifest["quantization"] = quantization_metadata["per_layer"][name]
                manifest_layers.append(layer_manifest)
                weight_offset += len(packed)
                gamma_offset += len(gamma_bytes)

        manifest = {
            "format": "Plan5-USW-512-v1",
            "weight_record_bytes": WORD_BYTES,
            "dense_payload_bytes": DENSE_BYTES,
            "outlier_slots": SLOT_COUNT,
            "outlier_value_format": "signed Q4.12 normalized by alpha",
            "gamma_format": "IEEE-754 binary16, row-major [round, channel]",
            "quantization": quantization_metadata or QUANTIZATION,
            "layers": manifest_layers,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
        staging.replace(output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def run_export(plan3_path=PLAN3_CHECKPOINT, beta_path=BETA_CHECKPOINT,
               probe_path=PROBE_CHECKPOINT, report_path=REPORT_PATH,
               output_dir=OUTPUT_DIR, fraction=SPARSE_FRACTION,
               expected_layers=EXPECTED_LAYERS):
    if Path(output_dir).exists():
        raise FileExistsError(f"refusing to overwrite existing output directory {output_dir}")
    plan3 = torch.load(plan3_path, map_location="cpu", weights_only=True, mmap=True)
    beta_checkpoint = torch.load(beta_path, map_location="cpu", weights_only=True, mmap=True)
    probe = torch.load(probe_path, map_location="cpu", weights_only=True, mmap=True)
    if "bank" not in plan3 or "tf_norm_step_scale" not in beta_checkpoint:
        raise ValueError("Plan 3 checkpoint fields do not match the expected export sources")
    retained = probe["retained"][("gptq", -1)]
    beta = beta_checkpoint["tf_norm_step_scale"]
    report, alpha = preflight_model(
        plan3["bank"], retained, beta, fraction=fraction, expected_layers=expected_layers
    )
    report["sources"] = {
        "plan3_checkpoint": {"path": str(plan3_path), "sha256": file_sha256(plan3_path)},
        "beta_checkpoint": {"path": str(beta_path), "sha256": file_sha256(beta_path)},
        "probe_checkpoint": {"path": str(probe_path), "sha256": file_sha256(probe_path)},
    }
    write_json_atomic(report_path, report)
    if report["compatible"]:
        quantization_metadata = {
            **QUANTIZATION,
            "candidate_sparse_fraction": fraction,
            "source_checkpoints": report["sources"],
            "preflight": {
                "path": str(report_path),
                "totals": report["totals"],
            },
            "per_layer": {
                name: {
                    "candidate_outliers": values["sparse_coordinates"],
                    "folded_to_ternary": values["coordinates_folded_to_ternary"],
                    "encoded_sparse_slots": values["q4_12_checked_slots"] -
                                            values["q4_12_rounded_to_zero_slots"],
                    "encoded_sparse_fraction": (
                        values["q4_12_checked_slots"] -
                        values["q4_12_rounded_to_zero_slots"]
                    ) / values["elements"],
                }
                for name, values in report["layers"].items()
            },
        }
        export_payload(plan3["bank"], retained, beta, alpha, output_dir, fraction,
                       quantization_metadata)
        report["payload"] = {"directory": str(output_dir), "files": [
            "weights.usw512", "gamma.fp16", "manifest.json"
        ]}
        write_json_atomic(report_path, report)
    return report


if __name__ == "__main__":
    result = run_export()
    print(json.dumps({"compatible": result["compatible"], "totals": result["totals"],
                      "report": str(REPORT_PATH)}, ensure_ascii=False, indent=2))
