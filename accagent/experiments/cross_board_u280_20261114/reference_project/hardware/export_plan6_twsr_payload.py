"""Package a Plan 4 TWSR model as Plan 6 recurrent-core payload files."""

from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
import torch

from hardware.pack_usw512 import pack_matrix_to_usw512
from hardware.plan6_models import PLAN6_MODELS


ROOT = Path(__file__).resolve().parents[1]


def tensor_bf16_sha256(value):
    value = value.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
    raw = value.view(torch.uint16).numpy().astype("<u2", copy=False).tobytes()
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pack_twsr_matrix(source_weight, quantized_weight, sparse_indices, beta_steps,
                     quantization, recurrence_count=4):
    source = source_weight.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
    quantized = quantized_weight.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
    if source.ndim != 2 or quantized.shape != source.shape:
        raise ValueError("source and quantized weights must be matching 2-D matrices")
    if not torch.isfinite(source).all() or not torch.isfinite(quantized).all():
        raise ValueError("source and quantized weights must be finite")

    indices = torch.as_tensor(sparse_indices, dtype=torch.int64, device="cpu").flatten()
    expected_count = math.ceil(source.numel() * quantization["sparse_fraction"])
    if indices.numel() != expected_count or torch.unique(indices).numel() != expected_count:
        raise ValueError("sparse coordinates do not match the configured candidate fraction")
    if indices.min().item() < 0 or indices.max().item() >= source.numel():
        raise ValueError("sparse coordinate is outside the matrix")
    indices = torch.sort(indices).values

    rows, columns = map(int, source.shape)
    dense = quantized.float().numpy().copy()
    source_values = source.float().numpy()
    dense_flat = dense.reshape(-1)
    dense_flat[indices.numpy()] = 0.0
    alpha = np.max(np.abs(dense), axis=1)
    if not np.isfinite(alpha).all() or (alpha <= 0.0).any():
        raise ValueError("a row has no positive dense ternary scale")
    normalized = dense / alpha[:, None]
    ternary = np.rint(normalized).astype(np.int8)
    if not np.allclose(normalized, ternary, rtol=0.0, atol=1e-6):
        raise ValueError("dense residual is not row-scaled ternary")

    sparse = np.zeros((rows, columns), dtype=np.float32)
    sparse.reshape(-1)[indices.numpy()] = source_values.reshape(-1)[indices.numpy()]
    beta = torch.as_tensor(beta_steps, dtype=torch.float32, device="cpu").numpy()
    expected_beta_shape = (int(recurrence_count), rows)
    if beta.shape != expected_beta_shape or not np.isfinite(beta).all():
        raise ValueError(f"beta must be finite with shape {expected_beta_shape}")
    beta_min, beta_max = quantization["beta_clip"]
    if ((beta < beta_min) | (beta > beta_max)).any():
        raise ValueError("beta is outside the configured clipping range")

    packed, gamma, encoded_ternary, sparse_q4_12 = pack_matrix_to_usw512(
        ternary, sparse, alpha, beta
    )
    return packed, gamma, {
        "shape": [rows, columns],
        "source_weight_sha256_bf16": tensor_bf16_sha256(source),
        "candidate_sparse_coordinates": int(indices.numel()),
        "encoded_sparse_slots": int(np.count_nonzero(sparse_q4_12)),
        "dense_ternary_nonzeros": int(np.count_nonzero(encoded_ternary)),
    }


def export_recurrent_core_payload(model_key, model, linears, original, bank,
                                  sparse_indices, beta_by_layer, calibration,
                                  output_dir=None):
    if model_key not in ("ouro14", "dory4b"):
        raise ValueError(f"unsupported Plan 6 payload model: {model_key}")
    model_spec = PLAN6_MODELS[model_key]
    quantization = model_spec["quantization"]
    names = set(linears)
    if names != set(original) or names != set(bank) or names != set(sparse_indices) or \
            names != set(beta_by_layer):
        raise ValueError("Plan 4 TWSR payload layers differ across model and quantization data")

    if output_dir is None:
        output_dir = ROOT / "results/plan6" / f"{model_key}_recurrent_core_twsr"
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing payload {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{model_key}_payload_", dir=output_dir.parent))
    layers = []
    try:
        weight_offset = 0
        gamma_offset = 0
        with (staging / "weights.usw512").open("wb") as weights, \
                (staging / "gamma.fp16").open("wb") as gamma_stream:
            for name in sorted(names):
                packed, gamma, record = pack_twsr_matrix(
                    original[name], bank[name][0], sparse_indices[name],
                    beta_by_layer[name], quantization, model_spec["recurrences"],
                )
                gamma_bytes = gamma.astype("<f2", copy=False).tobytes(order="C")
                weights.write(packed)
                gamma_stream.write(gamma_bytes)
                layers.append({
                    "name": name,
                    **record,
                    "window_size": 256,
                    "windows_per_row": (record["shape"][1] + 255) // 256,
                    "weight_file": "weights.usw512",
                    "weight_offset_bytes": weight_offset,
                    "weight_bytes": len(packed),
                    "gamma_file": "gamma.fp16",
                    "gamma_offset_bytes": gamma_offset,
                    "gamma_bytes": len(gamma_bytes),
                    "gamma_layout": "round-major",
                    "rounds": int(gamma.shape[0]),
                })
                weight_offset += len(packed)
                gamma_offset += len(gamma_bytes)

        core_start = int(model_spec.get("input_sublayers", 0))
        core_stop = core_start + int(model_spec["recurrent_sublayers"])
        quantized_names = {f"{name}.weight" for name in names}
        auxiliary = []
        with (staging / "auxiliary.bf16").open("wb") as auxiliary_stream:
            for name, parameter in model.named_parameters():
                pieces = name.split(".")
                loop_tail_parameter = model_key == "ouro14" and name.startswith("model.norm.")
                recurrent_layer_parameter = False
                if len(pieces) >= 4 and pieces[:2] == ["model", "layers"]:
                    try:
                        layer_index = int(pieces[2])
                    except ValueError:
                        layer_index = -1
                    recurrent_layer_parameter = core_start <= layer_index < core_stop
                if not (recurrent_layer_parameter or loop_tail_parameter) or \
                        name in quantized_names:
                    continue
                value = parameter.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
                raw = value.view(torch.uint16).numpy().astype("<u2", copy=False).tobytes()
                auxiliary_stream.write(raw)
                auxiliary.append({
                    "name": name,
                    "role": "loop_tail_normalization" if loop_tail_parameter else "recurrent_layer",
                    "shape": list(value.shape),
                    "dtype": "bfloat16",
                    "offset_bytes": auxiliary_stream.tell() - len(raw),
                    "bytes": len(raw),
                })

        manifest = {
            "format": "Plan6-TWSR-Recurrent-Core-Payload-v1",
            "created": datetime.now().astimezone().isoformat(timespec="seconds"),
            "scope": "recurrent core only",
            "model": {
                "repository": model_spec["repository"],
                "revision": model_spec["revision"],
                "core_layer_start": core_start,
                "recurrent_sublayers": int(model_spec["recurrent_sublayers"]),
                "core_blocks": int(model_spec["core_blocks"]),
                "recurrences": int(model_spec["recurrences"]),
            },
            "quantization": quantization,
            "calibration": calibration,
            "layers": layers,
            "auxiliary_parameters": auxiliary,
            "files_sha256": {
                name: file_sha256(staging / name)
                for name in ("weights.usw512", "gamma.fp16", "auxiliary.bf16")
            },
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        )
        os.replace(staging, output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_dir
