"""Canonical real-weight layout contracts for semantic DUT harnesses."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "spatialaccagent.dut_weight_layout_contract.v1"
STREAM_SCHEMA_VERSION = "spatialaccagent.materialized_weight_stream.v1"
COMPOSITE_STREAM_SCHEMA_VERSION = "spatialaccagent.composite_weight_stream.v1"
DTYPE_BITS = {"fp16": 16, "fp32": 32}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bound_int(stage: dict[str, Any], name: str, default: int | None = None) -> int:
    bound = stage.get("bound_params", {}) if isinstance(stage.get("bound_params"), dict) else {}
    row = bound.get(name)
    value = row.get("value") if isinstance(row, dict) else row
    if value is None:
        numeric = stage.get("numeric_contract", {}) if isinstance(stage.get("numeric_contract"), dict) else {}
        value = numeric.get(name)
    if value is None:
        if default is None:
            raise ValueError(f"stage {stage.get('stage_id')} has no bound {name}")
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"stage {stage.get('stage_id')} has invalid {name}: {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"stage {stage.get('stage_id')} has non-positive {name}: {parsed}")
    return parsed


def dtype_bits(dtype: str) -> int:
    if dtype not in DTYPE_BITS:
        raise ValueError(f"unsupported canonical weight-layout dtype: {dtype}")
    return DTYPE_BITS[dtype]


def tensor_elements(shape: list[Any]) -> int:
    if not shape:
        raise ValueError("weight tensor shape is empty")
    values = [int(value) for value in shape]
    if any(value <= 0 for value in values):
        raise ValueError(f"weight tensor shape is invalid: {shape}")
    return math.prod(values)


def tensor_record(binding: dict[str, Any]) -> dict[str, Any]:
    return {
        "tensor": binding.get("tensor"),
        "parameter_suffix": binding.get("parameter_suffix"),
        "sha256": binding.get("sha256"),
        "file_sha256": binding.get("file_sha256"),
        "path": binding.get("path"),
        "shape": binding.get("shape"),
        "source_dtype": binding.get("source_dtype"),
    }


def projection_role(suffix: str) -> tuple[str, str] | None:
    parts = suffix.split(".")
    if len(parts) < 2 or parts[-1] not in {"weight", "bias"}:
        return None
    return parts[-2], parts[-1]


def storage_dtype_for_bits(preferred: str, bits: int) -> str:
    if dtype_bits(preferred) == bits:
        return preferred
    candidate = f"fp{bits}"
    if candidate not in DTYPE_BITS:
        raise ValueError(f"no floating-point storage dtype for {bits} bits")
    return candidate


def conversion_contract(source_dtype: str, storage_dtype: str) -> dict[str, Any]:
    if source_dtype == storage_dtype:
        return {
            "kind": "ieee754_bit_preserving",
            "source_dtype": source_dtype,
            "storage_dtype": storage_dtype,
        }
    return {
        "kind": "ieee754_value_preserving_cast",
        "source_dtype": source_dtype,
        "storage_dtype": storage_dtype,
        "round_source_before_cast": True,
    }


def linear_weight_target(
    *,
    target_id: str,
    port_role: str,
    sources: list[dict[str, Any]],
    in_lanes: int,
    out_lanes: int,
    source_dtype: str,
    storage_dtype: str,
) -> dict[str, Any]:
    if not sources:
        raise ValueError(f"{target_id} has no source tensor")
    shapes = [[int(value) for value in source.get("shape", [])] for source in sources]
    if any(len(shape) != 2 for shape in shapes):
        raise ValueError(f"{target_id} requires rank-2 source tensors, got {shapes}")
    in_features = shapes[0][1]
    if any(shape[1] != in_features for shape in shapes):
        raise ValueError(f"{target_id} source input dimensions disagree: {shapes}")
    out_features = sum(shape[0] for shape in shapes)
    if in_features % in_lanes or out_features % out_lanes:
        raise ValueError(
            f"{target_id} dimensions do not divide selected lanes: "
            f"shape=[{out_features}, {in_features}] out_lanes={out_lanes} in_lanes={in_lanes}"
        )
    scalar_bits = dtype_bits(storage_dtype)
    data_width_bits = in_lanes * out_lanes * scalar_bits
    if data_width_bits % 32:
        raise ValueError(f"{target_id} port width is not divisible by the 32-bit harness loader")
    in_beats = in_features // in_lanes
    out_beats = out_features // out_lanes
    write_count = in_beats * out_beats
    return {
        "target_id": target_id,
        "target_kind": "linear_weight_matrix",
        "dut_port_role": port_role,
        "source_tensors": [tensor_record(source) for source in sources],
        "compose": {
            "kind": "identity" if len(sources) == 1 else "concat",
            "axis": 0,
            "source_order": [source.get("parameter_suffix") for source in sources],
        },
        "logical_shape": [out_features, in_features],
        "source_axis_order": ["output_feature", "input_feature"],
        "storage_scalar_dtype": storage_dtype,
        "storage_scalar_bits": scalar_bits,
        "value_conversion": conversion_contract(source_dtype, storage_dtype),
        "port": {
            "protocol": "decoupled_weight_write",
            "data_width_bits": data_width_bits,
            "address_order": ["out_beat", "in_beat"],
            "address_formula": "out_beat * in_beats + in_beat",
            "address_count": write_count,
            "words_per_write": data_width_bits // 32,
        },
        "tile": {
            "out_lanes": out_lanes,
            "in_lanes": in_lanes,
            "out_beats": out_beats,
            "in_beats": in_beats,
            "scalar_order_within_write": ["out_lane", "in_lane"],
            "scalar_bit_offset_formula": "(out_lane * in_lanes + in_lane) * storage_scalar_bits",
            "scalar_zero_is_lsb": True,
        },
        "port_write_count": write_count,
        "stream_word_count": write_count * (data_width_bits // 32),
    }


def vector_target(
    *,
    target_id: str,
    target_kind: str,
    port_role: str,
    sources: list[dict[str, Any]],
    elements_per_write: int,
    source_dtype: str,
    storage_dtype: str,
) -> dict[str, Any]:
    if not sources:
        raise ValueError(f"{target_id} has no source tensor")
    shapes = [[int(value) for value in source.get("shape", [])] for source in sources]
    if any(len(shape) != 1 for shape in shapes):
        raise ValueError(f"{target_id} requires rank-1 source tensors, got {shapes}")
    element_count = sum(shape[0] for shape in shapes)
    if element_count % elements_per_write:
        raise ValueError(
            f"{target_id} length {element_count} does not divide elements_per_write={elements_per_write}"
        )
    scalar_bits = dtype_bits(storage_dtype)
    data_width_bits = elements_per_write * scalar_bits
    if data_width_bits % 32:
        raise ValueError(f"{target_id} port width is not divisible by the 32-bit harness loader")
    write_count = element_count // elements_per_write
    return {
        "target_id": target_id,
        "target_kind": target_kind,
        "dut_port_role": port_role,
        "source_tensors": [tensor_record(source) for source in sources],
        "compose": {
            "kind": "identity" if len(sources) == 1 else "concat",
            "axis": 0,
            "source_order": [source.get("parameter_suffix") for source in sources],
        },
        "logical_shape": [element_count],
        "source_axis_order": ["feature"],
        "storage_scalar_dtype": storage_dtype,
        "storage_scalar_bits": scalar_bits,
        "value_conversion": conversion_contract(source_dtype, storage_dtype),
        "port": {
            "protocol": "decoupled_weight_write",
            "data_width_bits": data_width_bits,
            "address_order": ["feature_beat"],
            "address_formula": "feature_beat",
            "address_count": write_count,
            "words_per_write": data_width_bits // 32,
        },
        "tile": {
            "elements_per_write": elements_per_write,
            "scalar_order_within_write": ["feature_lane"],
            "scalar_bit_offset_formula": "feature_lane * storage_scalar_bits",
            "scalar_zero_is_lsb": True,
        },
        "port_write_count": write_count,
        "stream_word_count": write_count * (data_width_bits // 32),
    }


def resolve_explicit_layout(
    stage: dict[str, Any],
    stage_semantics: dict[str, Any],
    by_suffix: dict[str, dict[str, Any]],
    weight_dtype: str,
    acc_dtype: str,
) -> list[dict[str, Any]] | None:
    layout = stage_semantics.get("weight_layout")
    if not isinstance(layout, dict):
        return None
    rows = layout.get("targets")
    if not isinstance(rows, list):
        raise ValueError(f"{stage.get('stage_id')}: explicit weight_layout.targets is malformed")
    targets: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{stage.get('stage_id')}: explicit weight target is not an object")
        suffixes = [str(value) for value in row.get("source_suffixes", [])]
        sources = [by_suffix[suffix] for suffix in suffixes if suffix in by_suffix]
        if len(sources) != len(suffixes):
            missing = sorted(set(suffixes) - set(by_suffix))
            raise ValueError(f"{stage.get('stage_id')}: explicit weight target is missing sources {missing}")
        kind = str(row.get("kind") or "")
        storage = str(row.get("storage_dtype") or weight_dtype).replace("weight_dtype", weight_dtype).replace("acc_dtype", acc_dtype)
        if kind == "linear_weight_matrix":
            targets.append(
                linear_weight_target(
                    target_id=str(row.get("target_id")),
                    port_role=str(row.get("dut_port_role")),
                    sources=sources,
                    in_lanes=bound_int(stage, str(row.get("in_lanes_param") or "lanes")),
                    out_lanes=bound_int(stage, str(row.get("out_lanes_param") or "lanes")),
                    source_dtype=weight_dtype,
                    storage_dtype=storage,
                )
            )
        elif kind in {"norm_scale_vector", "linear_bias_vector"}:
            targets.append(
                vector_target(
                    target_id=str(row.get("target_id")),
                    target_kind=kind,
                    port_role=str(row.get("dut_port_role")),
                    sources=sources,
                    elements_per_write=bound_int(stage, str(row.get("elements_per_write_param") or "lanes")),
                    source_dtype=weight_dtype,
                    storage_dtype=storage,
                )
            )
        else:
            raise ValueError(f"{stage.get('stage_id')}: unsupported explicit weight target kind {kind!r}")
    return targets


def canonical_targets(
    stage: dict[str, Any],
    stage_semantics: dict[str, Any],
    bindings: list[dict[str, Any]],
    weight_dtype: str,
    acc_dtype: str,
) -> tuple[list[dict[str, Any]], str]:
    by_suffix = {str(row.get("parameter_suffix")): row for row in bindings}
    explicit = resolve_explicit_layout(stage, stage_semantics, by_suffix, weight_dtype, acc_dtype)
    if explicit is not None:
        return explicit, "model_semantic_adapter.weight_layout"

    op = str(stage.get("op") or "")
    lanes = bound_int(stage, "lanes")
    if not bindings:
        return [], "no_required_weights"
    if op.startswith("rms_norm"):
        if len(bindings) != 1:
            raise ValueError(f"{stage.get('stage_id')}: RMSNorm requires exactly one scale tensor")
        input_bits = bound_int(stage, "input_bits")
        storage_dtype = storage_dtype_for_bits(acc_dtype, input_bits)
        return [
            vector_target(
                target_id="norm.scale",
                target_kind="norm_scale_vector",
                port_role="weight",
                sources=bindings,
                elements_per_write=lanes,
                source_dtype=weight_dtype,
                storage_dtype=storage_dtype,
            )
        ], "canonical_semantic_op_layout.v1"
    if op in {"mlp_gate_proj", "mlp_up_proj", "mlp_down_proj"}:
        if len(bindings) != 1:
            raise ValueError(f"{stage.get('stage_id')}: standalone MLP projection requires one matrix")
        return [
            linear_weight_target(
                target_id="linear.weight",
                port_role="weight",
                sources=bindings,
                in_lanes=lanes,
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
            )
        ], "canonical_semantic_op_layout.v1"
    if op == "self_attention":
        roles: dict[tuple[str, str], dict[str, Any]] = {}
        for suffix, binding in by_suffix.items():
            role = projection_role(suffix)
            if role is not None:
                roles[role] = binding
        required_weight_roles = [(name, "weight") for name in ("q_proj", "k_proj", "v_proj", "o_proj")]
        missing = [role for role in required_weight_roles if role not in roles]
        if missing:
            raise ValueError(f"{stage.get('stage_id')}: canonical attention layout is missing roles {missing}")
        qkv_weights = [roles[(name, "weight")] for name in ("q_proj", "k_proj", "v_proj")]
        targets = [
            linear_weight_target(
                target_id="attention.qkv.weight",
                port_role="qkv_weight",
                sources=qkv_weights,
                in_lanes=lanes,
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
            )
        ]
        qkv_biases = [roles[(name, "bias")] for name in ("q_proj", "k_proj", "v_proj") if (name, "bias") in roles]
        if qkv_biases and len(qkv_biases) != 3:
            raise ValueError(f"{stage.get('stage_id')}: Q/K/V bias coverage must be all-or-none")
        if qkv_biases:
            targets.append(
                vector_target(
                    target_id="attention.qkv.bias",
                    target_kind="linear_bias_vector",
                    port_role="qkv_bias",
                    sources=qkv_biases,
                    elements_per_write=lanes,
                    source_dtype=weight_dtype,
                    storage_dtype=acc_dtype,
                )
            )
        targets.append(
            linear_weight_target(
                target_id="attention.out_proj.weight",
                port_role="out_proj_weight",
                sources=[roles[("o_proj", "weight")]],
                in_lanes=bound_int(stage, "head_dim"),
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
            )
        )
        if ("o_proj", "bias") in roles:
            targets.append(
                vector_target(
                    target_id="attention.out_proj.bias",
                    target_kind="linear_bias_vector",
                    port_role="out_proj_bias",
                    sources=[roles[("o_proj", "bias")]],
                    elements_per_write=lanes,
                    source_dtype=weight_dtype,
                    storage_dtype=acc_dtype,
                )
            )
        return targets, "canonical_semantic_op_layout.v1"
    raise ValueError(
        f"{stage.get('stage_id')}: weighted op {op!r} has no explicit adapter weight_layout "
        "and no canonical semantic-op layout"
    )


def build_stage_weight_layout(
    stage: dict[str, Any],
    stage_semantics: dict[str, Any],
    bindings: list[dict[str, Any]],
    numeric_policy: dict[str, Any],
) -> dict[str, Any]:
    rules = numeric_policy.get("default_rules", {}) if isinstance(numeric_policy.get("default_rules"), dict) else {}
    weight_dtype = str(rules.get("weight_dtype") or "")
    acc_dtype = str(rules.get("acc_dtype") or "")
    dtype_bits(weight_dtype)
    dtype_bits(acc_dtype)
    targets, resolution = canonical_targets(stage, stage_semantics, bindings, weight_dtype, acc_dtype)
    required_suffixes = [str(binding.get("parameter_suffix")) for binding in bindings]
    covered_suffixes = [
        str(source.get("parameter_suffix"))
        for target in targets
        for source in target.get("source_tensors", [])
    ]
    if sorted(required_suffixes) != sorted(covered_suffixes):
        raise ValueError(
            f"{stage.get('stage_id')}: storage targets do not cover required tensors exactly once: "
            f"required={sorted(required_suffixes)} covered={sorted(covered_suffixes)}"
        )
    offset = 0
    normalized_targets = []
    for target in targets:
        row = dict(target)
        count = int(row["stream_word_count"])
        row["stream_range"] = {
            "word_offset": offset,
            "word_count": count,
            "word_end_exclusive": offset + count,
        }
        row["external_word_encoding"] = {
            "word_bits": 32,
            "scalar_bits": row["storage_scalar_bits"],
            "scalars_per_word": 32 // int(row["storage_scalar_bits"]),
            "scalar_zero_is_lsb": True,
            "word_zero_is_lsb_within_port_write": True,
        }
        normalized_targets.append(row)
        offset += count
    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "stage_id": stage.get("stage_id"),
        "op": stage.get("op"),
        "template_id": stage.get("template_id"),
        "resolution": resolution,
        "numeric_policy": {
            "policy_id": numeric_policy.get("policy_id"),
            "weight_dtype": weight_dtype,
            "acc_dtype": acc_dtype,
            "rounding": rules.get("rounding"),
            "saturation": rules.get("saturation"),
        },
        "external_loader": {
            "protocol": "ready_valid_addressed_words",
            "word_bits": 32,
            "word_address_order": "strictly ascending from zero",
            "last_assertion": "true exactly on final accepted word",
            "stimulus_allowed_before_last_accepted_word": False,
        },
        "storage_targets": normalized_targets,
        "stream_word_count": offset,
        "required_tensor_hashes": sorted(
            str(binding.get("sha256")) for binding in bindings if binding.get("sha256")
        ),
        "checker_rules": {
            "all_required_tensors_covered_exactly_once": True,
            "source_matrix_axis_order": "checkpoint [output_feature, input_feature]",
            "linear_storage_order": "out_beat, in_beat, out_lane, in_lane",
            "source_values_are_rounded_to_weight_dtype_before_storage_conversion": True,
            "padding": "forbidden because selected dimensions must divide selected lanes",
            "default_or_identity_fallback": "forbidden",
        },
    }
    contract["contract_sha256"] = sha256_json(contract)
    return contract


def load_target_tensor(binding: dict[str, Any], source_dtype: str) -> Any:
    import torch

    path = Path(str(binding.get("path") or ""))
    if not path.is_file() or sha256_file(path) != binding.get("file_sha256"):
        raise ValueError(f"real-weight tensor file/hash mismatch: {path}")
    tensor = torch.load(path, map_location="cpu", weights_only=True).detach().cpu().contiguous()
    expected_shape = [int(value) for value in binding.get("shape", [])]
    if list(tensor.shape) != expected_shape:
        raise ValueError(f"real-weight tensor shape mismatch for {path}: {list(tensor.shape)} != {expected_shape}")
    if source_dtype == "fp16":
        return tensor.to(torch.float16)
    if source_dtype == "fp32":
        return tensor.to(torch.float32)
    raise ValueError(f"unsupported source tensor dtype: {source_dtype}")


def target_scalars(target: dict[str, Any], by_suffix: dict[str, dict[str, Any]]) -> Any:
    import torch

    conversion = target.get("value_conversion", {}) if isinstance(target.get("value_conversion"), dict) else {}
    source_dtype = str(conversion.get("source_dtype") or target.get("storage_scalar_dtype"))
    source_order = target.get("compose", {}).get("source_order", [])
    tensors = [load_target_tensor(by_suffix[str(suffix)], source_dtype) for suffix in source_order]
    value = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)
    storage_dtype = str(target.get("storage_scalar_dtype") or "")
    value = value.to(torch.float16 if storage_dtype == "fp16" else torch.float32)
    if target.get("target_kind") == "linear_weight_matrix":
        out_features, in_features = [int(item) for item in target["logical_shape"]]
        tile = target["tile"]
        out_lanes = int(tile["out_lanes"])
        in_lanes = int(tile["in_lanes"])
        value = value.reshape(out_features // out_lanes, out_lanes, in_features // in_lanes, in_lanes)
        value = value.permute(0, 2, 1, 3).contiguous()
    return value.reshape(-1)


def scalar_words(value: Any, dtype: str) -> list[int]:
    import torch

    if dtype == "fp16":
        raw = value.contiguous().view(torch.int16).reshape(-1).tolist()
        return [int(item) & 0xFFFF for item in raw]
    if dtype == "fp32":
        raw = value.contiguous().view(torch.int32).reshape(-1).tolist()
        return [int(item) & 0xFFFFFFFF for item in raw]
    raise ValueError(f"unsupported storage dtype: {dtype}")


def pack_u32(words: list[int], scalar_bits: int) -> list[int]:
    scalars_per_word = 32 // scalar_bits
    if len(words) % scalars_per_word:
        raise ValueError(
            f"canonical target scalar count {len(words)} is not divisible by scalars_per_word={scalars_per_word}"
        )
    mask = (1 << scalar_bits) - 1
    packed = []
    for offset in range(0, len(words), scalars_per_word):
        value = 0
        for lane, scalar in enumerate(words[offset : offset + scalars_per_word]):
            value |= (scalar & mask) << (lane * scalar_bits)
        packed.append(value)
    return packed


def materialize_stage_weight_stream(
    path: Path,
    layout: dict[str, Any],
    bindings: list[dict[str, Any]],
) -> dict[str, Any]:
    by_suffix = {str(binding.get("parameter_suffix")): binding for binding in bindings}
    packed_words: list[int] = []
    target_rows = []
    for target in layout.get("storage_targets", []):
        scalars = target_scalars(target, by_suffix)
        words = scalar_words(scalars, str(target.get("storage_scalar_dtype")))
        packed = pack_u32(words, int(target.get("storage_scalar_bits")))
        expected = int(target.get("stream_word_count") or 0)
        if len(packed) != expected:
            raise ValueError(
                f"{target.get('target_id')} materialized word count mismatch: {len(packed)} != {expected}"
            )
        expected_offset = int(target.get("stream_range", {}).get("word_offset") or 0)
        if len(packed_words) != expected_offset:
            raise ValueError(
                f"{target.get('target_id')} stream offset mismatch: {len(packed_words)} != {expected_offset}"
            )
        packed_words.extend(packed)
        target_rows.append(
            {
                "target_id": target.get("target_id"),
                "dut_port_role": target.get("dut_port_role"),
                "stream_range": target.get("stream_range"),
                "port": target.get("port"),
                "source_tensor_hashes": [
                    row.get("sha256") for row in target.get("source_tensors", []) if row.get("sha256")
                ],
            }
        )
    if len(packed_words) != int(layout.get("stream_word_count") or 0):
        raise ValueError("materialized stage stream does not match layout stream_word_count")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{word:08x}\n" for word in packed_words), encoding="ascii")
    return {
        "schema_version": STREAM_SCHEMA_VERSION,
        "status": "pass",
        "path": str(path),
        "sha256": sha256_file(path),
        "word_bits": 32,
        "word_count": len(packed_words),
        "layout_contract_sha256": layout.get("contract_sha256"),
        "targets": target_rows,
    }


def materialize_composite_weight_stream(
    path: Path,
    stage_streams: list[dict[str, Any]],
) -> dict[str, Any]:
    """Concatenate hash-verified canonical stage streams in pipeline order."""

    if not isinstance(stage_streams, list) or not stage_streams:
        raise ValueError("composite weight stream requires at least one stage descriptor")

    stage_order: list[str] = []
    stage_segments: list[dict[str, Any]] = []
    source_paths: list[tuple[str, Path, str, int]] = []
    seen_stage_ids: set[str] = set()
    global_offset = 0

    for stage_index, descriptor in enumerate(stage_streams):
        if not isinstance(descriptor, dict):
            raise ValueError(f"composite stage descriptor {stage_index} is not an object")
        stage_id = str(descriptor.get("stage_id") or "")
        op = str(descriptor.get("op") or "")
        if not stage_id or not op:
            raise ValueError(f"composite stage descriptor {stage_index} is missing stage_id or op")
        if stage_id in seen_stage_ids:
            raise ValueError(f"composite weight stream has duplicate stage_id {stage_id}")
        seen_stage_ids.add(stage_id)

        layout = descriptor.get("layout")
        if not isinstance(layout, dict):
            raise ValueError(f"{stage_id}: canonical weight layout is missing")
        if layout.get("schema_version") != SCHEMA_VERSION or layout.get("status") != "pass":
            raise ValueError(f"{stage_id}: canonical weight layout is not pass")
        if str(layout.get("stage_id") or "") != stage_id or str(layout.get("op") or "") != op:
            raise ValueError(f"{stage_id}: descriptor identity does not match canonical weight layout")
        layout_hash = str(layout.get("contract_sha256") or "")
        layout_payload = {key: value for key, value in layout.items() if key != "contract_sha256"}
        if not layout_hash or sha256_json(layout_payload) != layout_hash:
            raise ValueError(f"{stage_id}: canonical weight-layout contract hash mismatch")

        layout_word_count = layout.get("stream_word_count")
        if isinstance(layout_word_count, bool) or not isinstance(layout_word_count, int) or layout_word_count < 0:
            raise ValueError(f"{stage_id}: canonical layout stream_word_count is invalid")

        targets = layout.get("storage_targets")
        if not isinstance(targets, list):
            raise ValueError(f"{stage_id}: canonical layout storage_targets is not a list")
        target_segments: list[dict[str, Any]] = []
        local_offset = 0
        seen_target_ids: set[str] = set()
        for target_index, target in enumerate(targets):
            if not isinstance(target, dict):
                raise ValueError(f"{stage_id}: storage target {target_index} is not an object")
            target_id = str(target.get("target_id") or "")
            if not target_id or target_id in seen_target_ids:
                raise ValueError(f"{stage_id}: storage target ids must be non-empty and unique")
            seen_target_ids.add(target_id)
            local_range = target.get("stream_range")
            if not isinstance(local_range, dict):
                raise ValueError(f"{stage_id}/{target_id}: local stream range is missing")
            target_word_count = target.get("stream_word_count")
            if (
                isinstance(target_word_count, bool)
                or not isinstance(target_word_count, int)
                or target_word_count < 0
            ):
                raise ValueError(f"{stage_id}/{target_id}: stream_word_count is invalid")
            expected_range = {
                "word_offset": local_offset,
                "word_count": target_word_count,
                "word_end_exclusive": local_offset + target_word_count,
            }
            if local_range != expected_range:
                raise ValueError(f"{stage_id}/{target_id}: local stream range is not contiguous")
            global_range = {
                "word_offset": global_offset + local_offset,
                "word_count": expected_range["word_count"],
                "word_end_exclusive": global_offset + expected_range["word_end_exclusive"],
            }
            target_segments.append(
                {
                    "target_id": target_id,
                    "dut_port_role": target.get("dut_port_role"),
                    "local_stream_range": expected_range,
                    "global_stream_range": global_range,
                    "port": target.get("port"),
                    "source_tensor_hashes": [
                        row.get("sha256")
                        for row in target.get("source_tensors", [])
                        if isinstance(row, dict) and row.get("sha256")
                    ],
                }
            )
            local_offset = expected_range["word_end_exclusive"]
        if local_offset != layout_word_count:
            raise ValueError(f"{stage_id}: storage targets do not cover the canonical local stream")

        local_stream = descriptor.get("stream")
        if local_stream is None and layout_word_count != 0:
            raise ValueError(f"{stage_id}: non-empty canonical local stream is missing")
        if local_stream is not None and not isinstance(local_stream, dict):
            raise ValueError(f"{stage_id}: canonical local stream is not an object")

        empty_sha256 = hashlib.sha256(b"").hexdigest()
        local_stream_hash = empty_sha256
        if isinstance(local_stream, dict):
            if local_stream.get("schema_version") != STREAM_SCHEMA_VERSION or local_stream.get("status") != "pass":
                raise ValueError(f"{stage_id}: canonical local stream is not pass")
            if local_stream.get("word_bits") != 32:
                raise ValueError(f"{stage_id}: canonical local stream word_bits must be 32")
            if local_stream.get("word_count") != layout_word_count:
                raise ValueError(f"{stage_id}: canonical local stream word_count does not match its layout")
            if local_stream.get("layout_contract_sha256") != layout_hash:
                raise ValueError(f"{stage_id}: canonical local stream layout hash mismatch")
            local_stream_hash = str(local_stream.get("sha256") or "")
            local_path = Path(str(local_stream.get("path") or ""))
            if not local_path.is_file() or not local_stream_hash:
                raise ValueError(f"{stage_id}: canonical local stream path/hash is missing")

            stream_targets = local_stream.get("targets")
            if not isinstance(stream_targets, list) or len(stream_targets) != len(target_segments):
                raise ValueError(f"{stage_id}: canonical local stream target coverage is incomplete")
            for target, stream_target, target_segment in zip(targets, stream_targets, target_segments):
                expected_stream_target = {
                    "target_id": target_segment["target_id"],
                    "dut_port_role": target_segment["dut_port_role"],
                    "stream_range": target_segment["local_stream_range"],
                    "port": target_segment["port"],
                    "source_tensor_hashes": target_segment["source_tensor_hashes"],
                }
                if stream_target != expected_stream_target:
                    raise ValueError(
                        f"{stage_id}/{target.get('target_id')}: canonical local stream target metadata mismatch"
                    )
            source_paths.append((stage_id, local_path, local_stream_hash, layout_word_count))

        stage_range = {
            "word_offset": global_offset,
            "word_count": layout_word_count,
            "word_end_exclusive": global_offset + layout_word_count,
        }
        required_tensor_hashes = layout.get("required_tensor_hashes")
        if not isinstance(required_tensor_hashes, list) or any(
            not isinstance(value, str) or not value for value in required_tensor_hashes
        ):
            raise ValueError(f"{stage_id}: required_tensor_hashes is malformed")
        stage_segments.append(
            {
                "stage_index": stage_index,
                "stage_id": stage_id,
                "op": op,
                "layout_contract_sha256": layout_hash,
                "local_stream_sha256": local_stream_hash,
                "local_stream_range": {
                    "word_offset": 0,
                    "word_count": layout_word_count,
                    "word_end_exclusive": layout_word_count,
                },
                "global_stream_range": stage_range,
                "required_tensor_hashes": list(required_tensor_hashes),
                "targets": target_segments,
            }
        )
        stage_order.append(stage_id)
        global_offset = stage_range["word_end_exclusive"]

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        with temporary_path.open("wb") as output:
            for stage_id, source_path, declared_hash, declared_count in source_paths:
                digest = hashlib.sha256()
                actual_count = 0
                with source_path.open("rb") as source:
                    for line in source:
                        digest.update(line)
                        if not re.fullmatch(rb"[0-9A-Fa-f]{8}\n", line):
                            raise ValueError(f"{stage_id}: canonical local stream is not strict u32 memh")
                        output.write(line)
                        actual_count += 1
                if digest.hexdigest() != declared_hash:
                    raise ValueError(f"{stage_id}: canonical local stream file/hash mismatch")
                if actual_count != declared_count:
                    raise ValueError(f"{stage_id}: canonical local stream file word_count mismatch")
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    result = {
        "schema_version": COMPOSITE_STREAM_SCHEMA_VERSION,
        "status": "pass",
        "sha256": sha256_file(path),
        "word_bits": 32,
        "word_count": global_offset,
        "stage_order": stage_order,
        "stage_segments": stage_segments,
    }
    result["contract_sha256"] = sha256_json(result)
    result["path"] = str(path)
    return result
