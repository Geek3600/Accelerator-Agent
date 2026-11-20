"""Package the complete Huginn recurrent-core parameters for Plan 6."""

from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import torch
from safetensors import safe_open

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hardware.pack_usw512 import pack_matrix_to_usw512
from hardware.plan6_models import PLAN6_MODELS


MODEL_DIR = Path("/home/kemove/hyyuan/models/huginn-0125")
QUANTIZATION_CHECKPOINT = ROOT / "results/plan6/huginn_twsr_checkpoint.pt"
OUTPUT_DIR = ROOT / "results/plan6/huginn_recurrent_core_twsr"
HEAD_DIM = 96
MAX_CONTEXT = 2048
RECURRENCES = 32
CORE_BLOCKS = 4


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tensor_bf16_bytes(value):
    value = value.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
    return value.view(torch.uint16).numpy().astype("<u2", copy=False).tobytes()


def load_model_tensors(model_dir, tensor_names):
    model_dir = Path(model_dir)
    weight_map = json.loads((model_dir / "model.safetensors.index.json").read_text())["weight_map"]
    shards = defaultdict(list)
    for name in tensor_names:
        if name not in weight_map:
            raise KeyError(f"model checkpoint is missing {name}")
        shards[weight_map[name]].append(name)

    tensors = {}
    for shard_name, names in shards.items():
        with safe_open(model_dir / shard_name, framework="pt", device="cpu") as shard:
            for name in names:
                tensors[name] = shard.get_tensor(name)
    return tensors, weight_map


def pack_twsr_matrix(weight, quantized_weight, sparse_indices, beta_steps):
    spec = PLAN6_MODELS["huginn"]["quantization"]
    source = weight.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
    quantized = quantized_weight.detach().to(dtype=torch.bfloat16, device="cpu").contiguous()
    if source.ndim != 2 or source.shape[0] == 0 or source.shape[1] == 0:
        raise ValueError(f"unexpected matrix source shape {tuple(source.shape)}")
    if quantized.shape != source.shape or not torch.isfinite(quantized).all():
        raise ValueError("TWSR checkpoint has an invalid quantized matrix")

    indices = torch.as_tensor(sparse_indices, dtype=torch.int64, device="cpu").flatten()
    expected_count = int(np.ceil(source.numel() * spec["sparse_fraction"]))
    if indices.numel() != expected_count or torch.unique(indices).numel() != expected_count:
        raise ValueError("TWSR sparse coordinates do not match the fixed 0.5% count")
    if indices.min().item() < 0 or indices.max().item() >= source.numel():
        raise ValueError("TWSR sparse coordinate is outside the matrix")
    if not torch.equal(quantized.view(-1)[indices], source.view(-1)[indices]):
        raise ValueError("TWSR sparse coordinates are not preserved from BF16 source")

    beta = torch.as_tensor(beta_steps, dtype=torch.float32, device="cpu").numpy()
    if beta.shape != (RECURRENCES, source.shape[0]) or not np.isfinite(beta).all():
        raise ValueError(f"TWSR beta must be finite with shape [{RECURRENCES}, C_out]")
    if ((beta < spec["beta_clip"][0]) | (beta > spec["beta_clip"][1])).any():
        raise ValueError("TWSR beta is outside the Plan 4 clipping range")

    dense = quantized.float().numpy()
    sparse = np.zeros(dense.shape, dtype=np.float32)
    source_values = source.float().view(-1).numpy()
    dense_flat = dense.reshape(-1)
    dense_flat[indices.numpy()] = 0.0
    sparse.reshape(-1)[indices.numpy()] = source_values[indices.numpy()]
    alpha = np.max(np.abs(dense), axis=1)
    if not np.isfinite(dense).all() or (alpha <= 0).any():
        raise ValueError("TWSR dense residual has an invalid row scale")
    ternary = np.sign(dense).astype(np.int8)
    reconstructed = (ternary.astype(np.float32) * alpha[:, None]).astype(np.float32)
    if not np.array_equal(reconstructed.astype(np.float32), dense):
        raise ValueError("TWSR dense residual is not row-scaled ternary")

    packed, gamma, _, sparse_q4_12 = pack_matrix_to_usw512(
        ternary, sparse, alpha, beta
    )
    return packed, gamma, ternary, alpha, int(np.count_nonzero(sparse_q4_12))


def make_rope_table(head_dim=HEAD_DIM, context=MAX_CONTEXT, theta=50000.0):
    inverse = 1.0 / (
        theta ** (torch.arange(0, head_dim, 2, dtype=torch.float32) / head_dim)
    )
    positions = torch.arange(context, dtype=torch.float32)
    frequencies = torch.outer(positions, inverse)
    table = torch.stack((frequencies.cos(), frequencies.sin()), dim=-1)
    return table.contiguous().numpy().astype("<f4", copy=False)


def make_linear_operator_views(layer):
    """Describe the DMA-visible linear matrices used by the Huginn scheduler."""
    name = layer["name"]
    rows, columns = map(int, layer["shape"])
    row_bytes = int(layer["windows_per_row"]) * 64
    weight_offset = int(layer.get("usw512_offset_bytes", layer.get("weight_offset_bytes", 0)))
    gamma_offset = int(layer.get("gamma_fp16_offset_bytes", layer.get("gamma_offset_bytes", 0)))
    block_index = -1
    if name.startswith("transformer.core_block."):
        block_index = int(name.split(".")[2])

    def make_view(view_name, command_id, view_rows, row_offset=0):
        return {
            "name": view_name,
            "command_id": command_id,
            "block_index": block_index,
            "source_matrix": name,
            "shape": [view_rows, columns],
            "source_row_offset": row_offset,
            "weight_file": layer["weight_file"],
            "weight_offset_bytes": weight_offset + row_offset * row_bytes,
            "weight_bytes": view_rows * row_bytes,
            "gamma_file": layer["gamma_file"],
            "gamma_offset_bytes": gamma_offset,
            "gamma_row_offset": row_offset,
            "gamma_row_stride_elements": rows,
            "gamma_recurrence_stride_bytes": rows * 2,
            "gamma_bytes_per_recurrence": view_rows * 2,
            "rounds": int(layer["rounds"]),
        }

    if name.endswith(".mlp.fc"):
        intermediate = int(PLAN6_MODELS["huginn"]["intermediate_size"])
        if rows != 2 * intermediate:
            raise ValueError(f"unexpected fused Huginn Gate/Up shape: {layer['shape']}")
        return [
            make_view(f"{name}.gate_proj", 21, intermediate),
            make_view(f"{name}.up_proj", 22, intermediate, intermediate),
        ]

    if name == "transformer.adapter":
        command_id = 0
    elif name.endswith(".attn.Wqkv"):
        command_id = 3
    elif name.endswith(".attn.proj"):
        command_id = 9
    elif name.endswith(".mlp.proj"):
        command_id = 15
    else:
        return []
    return [make_view(name, command_id, rows)]


def build_huginn_linear_operator_map(manifest):
    return [view for layer in manifest["layers"]
            for view in make_linear_operator_views(layer)]


def export_core(model_dir=MODEL_DIR, quantization_checkpoint=QUANTIZATION_CHECKPOINT,
                output_dir=OUTPUT_DIR):
    model_dir = Path(model_dir)
    quantization_checkpoint = Path(quantization_checkpoint)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory {output_dir}")

    core_names = []
    norm_names = []
    bias_names = []
    for block in range(CORE_BLOCKS):
        prefix = f"transformer.core_block.{block}"
        core_names.extend((
            f"{prefix}.attn.Wqkv",
            f"{prefix}.attn.proj",
            f"{prefix}.mlp.fc",
            f"{prefix}.mlp.proj",
        ))
        norm_names.extend(f"{prefix}.norm_{index}.weight" for index in range(1, 5))
        bias_names.append(f"{prefix}.attn.qk_bias")
    adapter_name = "transformer.adapter"
    all_names = core_names + [adapter_name]
    tensor_names = [f"{name}.weight" for name in all_names]
    tensors, weight_map = load_model_tensors(model_dir, tensor_names + norm_names + bias_names)
    state = torch.load(quantization_checkpoint, map_location="cpu", weights_only=True)
    expected_spec = PLAN6_MODELS["huginn"]["quantization"]
    if state.get("format") != "Plan6-Huginn-TWSR-CoDesign-0.5-v1":
        raise ValueError("checkpoint is not a Plan 6 Huginn TWSR package")
    if state.get("quantization") != expected_spec:
        raise ValueError("Huginn checkpoint does not match the fixed Plan 6 quantization")
    if state.get("model_revision") != PLAN6_MODELS["huginn"]["revision"]:
        raise ValueError("Huginn checkpoint model revision differs from the pinned Plan 6 revision")
    calibration = state.get("calibration", {})
    for name in ("config.json", "raven_modeling_minimal.py", "model.safetensors.index.json"):
        if calibration.get("model_files_sha256", {}).get(name) != file_sha256(model_dir / name):
            raise ValueError(f"Huginn model source file differs from calibrated file: {name}")
    if calibration.get("plan4_sha256") != file_sha256(ROOT / "docs/plan4.md"):
        raise ValueError("Plan 4 document changed after Huginn TWSR calibration")
    if calibration.get("plan6_sha256") != file_sha256(ROOT / "docs/plan6.md"):
        raise ValueError("Plan 6 document changed after Huginn TWSR calibration")
    if calibration.get("quantization_script_sha256") != file_sha256(
        ROOT / "experiments/plan6_huginn_twsr.py"
    ):
        raise ValueError("Huginn TWSR calibration script changed after checkpoint generation")
    if set(state.get("layers", {})) != set(all_names):
        raise ValueError("Huginn checkpoint must include all 16 core matrices and the Adapter")
    adapter = tensors[f"{adapter_name}.weight"]
    if tuple(adapter.shape) != (5280, 10560):
        raise ValueError(f"unexpected Huginn Adapter shape {tuple(adapter.shape)}")

    core_weight_data = bytearray()
    core_gamma_data = bytearray()
    layers = []
    adapter_data = None
    adapter_gamma_data = None
    quantized_summary = {}
    for name in all_names:
        source = tensors[f"{name}.weight"]
        layer_state = state["layers"][name]
        source_hash = sha256_bytes(tensor_bf16_bytes(source))
        if layer_state.get("source_weight_sha256") != source_hash:
            raise ValueError(f"Huginn source-weight hash differs for {name}")
        packed, gamma, ternary, alpha, encoded_sparse_slots = pack_twsr_matrix(
            source,
            layer_state["quantized_weight"],
            layer_state["sparse_indices"],
            layer_state["beta"],
        )
        rows, columns = map(int, source.shape)
        if name == adapter_name:
            weight_file = "adapter.usw512"
            gamma_file = "adapter_gamma.fp16"
            weight_offset = gamma_offset = 0
            adapter_data = packed
            adapter_gamma_data = gamma.tobytes(order="C")
        else:
            weight_file = "weights.usw512"
            gamma_file = "gamma.fp16"
            weight_offset = len(core_weight_data)
            gamma_offset = len(core_gamma_data)
            core_weight_data.extend(packed)
            core_gamma_data.extend(gamma.tobytes(order="C"))
        layers.append({
            "name": name,
            "shape": [rows, columns],
            "window_size": 256,
            "windows_per_row": (columns + 255) // 256,
            "rounds": RECURRENCES,
            "usw512_offset_bytes": weight_offset,
            "usw512_bytes": len(packed),
            "gamma_fp16_offset_bytes": gamma_offset,
            "gamma_fp16_bytes": gamma.nbytes,
            "weight_file": weight_file,
            "gamma_file": gamma_file,
            "quantization": expected_spec["method"],
            "sparse_candidates": int(layer_state["sparse_indices"].numel()),
            "encoded_sparse_slots": encoded_sparse_slots,
            "gamma_layout": "round-major",
            "gamma_row_stride_elements": rows,
        })
        quantized_summary[name] = {
            "source_weight_sha256": source_hash,
            "candidate_sparse_coordinates": int(layer_state["sparse_indices"].numel()),
            "encoded_sparse_slots": encoded_sparse_slots,
            "ternary_values": int(np.count_nonzero(ternary)),
            "output_channels": int(alpha.size),
        }
        del packed, gamma, ternary, alpha

    if adapter_data is None or adapter_gamma_data is None:
        raise ValueError("Huginn Adapter payload was not generated")

    norm_values = []
    bias_values = []
    norm_manifest = []
    bias_manifest = []
    norm_offset = 0
    bias_offset = 0
    for block in range(CORE_BLOCKS):
        for norm_index in range(1, 5):
            name = f"transformer.core_block.{block}.norm_{norm_index}.weight"
            value = tensors[name].to(torch.bfloat16).contiguous()
            if tuple(value.shape) != (5280,) or not torch.isfinite(value).all():
                raise ValueError(f"invalid RMSNorm vector {name}")
            data = tensor_bf16_bytes(value)
            norm_values.append(data)
            norm_manifest.append({
                "name": name, "shape": [5280], "dtype": "bfloat16",
                "offset_bytes": norm_offset, "length_bytes": len(data),
            })
            norm_offset += len(data)

        name = f"transformer.core_block.{block}.attn.qk_bias"
        value = tensors[name].to(torch.bfloat16).contiguous()
        if tuple(value.shape) != (2, 1, 55, 96) or not torch.isfinite(value).all():
            raise ValueError(f"invalid attention Q/K bias {name}")
        data = tensor_bf16_bytes(value)
        bias_values.append(data)
        bias_manifest.append({
            "name": name, "shape": [2, 1, 55, 96], "dtype": "bfloat16",
            "offset_bytes": bias_offset, "length_bytes": len(data),
        })
        bias_offset += len(data)

    rope = make_rope_table()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".huginn_recurrent_core.tmp-", dir=output_dir.parent))
    try:
        (staging / "weights.usw512").write_bytes(core_weight_data)
        (staging / "gamma.fp16").write_bytes(core_gamma_data)
        (staging / "adapter.usw512").write_bytes(adapter_data)
        (staging / "adapter_gamma.fp16").write_bytes(adapter_gamma_data)
        (staging / "rmsnorm.bf16").write_bytes(b"".join(norm_values))
        (staging / "qk_bias.bf16").write_bytes(b"".join(bias_values))
        (staging / "rope.f32").write_bytes(rope.tobytes(order="C"))

        index = json.loads((model_dir / "model.safetensors.index.json").read_text())
        manifest = {
            "format": "Plan6-Huginn-Recurrent-Core-v1",
            "created": datetime.now().astimezone().isoformat(),
            "scope": "Huginn recurrent core only; prelude, coda, embeddings, and LM head excluded",
            "model": {
                "repository": "tomg-group-umd/huginn-0125",
                "revision": PLAN6_MODELS["huginn"]["revision"],
                "hidden_size": 5280,
                "intermediate_size": 17920,
                "head_dim": HEAD_DIM,
                "attention_heads": 55,
                "key_value_heads": 55,
                "core_blocks": CORE_BLOCKS,
                "recurrences": RECURRENCES,
                "context_lengths": [512, 2048],
                "norm_epsilon": 1e-6,
                "rope_theta": 50000.0,
                "parameter_dtype": "bfloat16",
            },
            "entry_inputs": [
                {"name": "initial_state", "shape": [5280], "dtype": "bfloat16"},
                {"name": "input_embeds", "shape": [5280], "dtype": "bfloat16"},
                {"name": "past_key_values", "shape": [128, 55, "context", 96], "dtype": "bfloat16"},
            ],
            "execution_order": [
                "adapter(cat(previous_state, input_embeds))",
                "for each recurrent step: core_block[0], core_block[1], core_block[2], core_block[3]",
                "per block: norm_1, Wqkv, qk_bias, RoPE, KV update, attention score/softmax/context, proj, residual_add, norm_2, norm_3, gate_proj, up_proj, SiLU_gate_multiply, mlp.proj, residual_add, norm_4",
            ],
            "layers": layers,
            "linear_operator_views": [
                view for layer in layers for view in make_linear_operator_views(layer)
            ],
            "quantization": expected_spec,
            "calibration": calibration,
            "auxiliary_parameters": {
                "rmsnorm_file": "rmsnorm.bf16",
                "rmsnorm_layout": "block-major, norm_1 through norm_4",
                "rmsnorm_tensors": norm_manifest,
                "qk_bias_file": "qk_bias.bf16",
                "qk_bias_tensors": bias_manifest,
                "rope_file": "rope.f32",
                "rope_shape": list(rope.shape),
                "rope_layout": "position, complex_pair, cos_then_sin",
                "rope_positions": MAX_CONTEXT,
            },
            "sources": {
                "model_config_sha256": file_sha256(model_dir / "config.json"),
                "modeling_source_sha256": file_sha256(model_dir / "raven_modeling_minimal.py"),
                "model_index_sha256": file_sha256(model_dir / "model.safetensors.index.json"),
                "twsr_checkpoint_sha256": file_sha256(quantization_checkpoint),
                "plan4_sha256": calibration["plan4_sha256"],
                "plan6_sha256": calibration["plan6_sha256"],
                "source_weight_shards": {name: weight_map[f"{name}.weight"] for name in all_names},
            },
            "file_sha256": {
                "weights.usw512": sha256_bytes(core_weight_data),
                "gamma.fp16": sha256_bytes(core_gamma_data),
                "adapter.usw512": sha256_bytes(adapter_data),
                "adapter_gamma.fp16": sha256_bytes(adapter_gamma_data),
                "rmsnorm.bf16": sha256_bytes(b"".join(norm_values)),
                "qk_bias.bf16": sha256_bytes(b"".join(bias_values)),
                "rope.f32": sha256_bytes(rope.tobytes(order="C")),
            },
            "layer_quantization": quantized_summary,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
        staging.replace(output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return manifest


def main():
    manifest = export_core()
    print(json.dumps({
        "output_dir": str(OUTPUT_DIR),
        "linear_layers": len(manifest["layers"]),
        "auxiliary_tensor_count": sum(
            len(manifest["auxiliary_parameters"][key])
            for key in ("rmsnorm_tensors", "qk_bias_tensors")
        ),
        "files": manifest["file_sha256"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
