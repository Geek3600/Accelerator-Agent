"""Canonical real-weight layout contracts for semantic DUT harnesses."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from accagent.framework.contract_identity import (
    canonical_sha256,
    hash_matches,
    identity_sha256,
)
from accagent.framework.numeric_policy import canonical_dtype


SCHEMA_VERSION = "spatialaccagent.dut_weight_layout_contract.v1"
STREAM_SCHEMA_VERSION = "spatialaccagent.materialized_weight_stream.v1"
COMPOSITE_STREAM_SCHEMA_VERSION = "spatialaccagent.composite_weight_stream.v1"
# Source checkpoint tensors remain FP16/FP32, but deployed storage is
# policy-driven and may be signed INT4 matrix weights, signed INT8 vectors, or
# signed INT32 accumulator-domain bias.  The source dtype and deployed scalar
# dtype are intentionally separate contracts.
DTYPE_BITS = {
    "fp16": 16,
    "fp32": 32,
    "int4": 4,
    "int8": 8,
    "int32": 32,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    return canonical_sha256(value)


def _legacy_identity_transform_projection(value: Any) -> Any:
    """Project the pre-canonical layout that serialized an identity transform."""

    projected = deepcopy(value)
    if not isinstance(projected, dict):
        return projected
    targets = projected.get("storage_targets")
    if not isinstance(targets, list):
        return projected
    for target in targets:
        if not isinstance(target, dict):
            continue
        if (
            target.get("target_kind") == "linear_weight_matrix"
            and target.get("source_transform") == {"kind": "identity"}
        ):
            target.pop("source_transform", None)
    return projected


def weight_layout_hash_matches(layout: dict[str, Any], declared_hash: Any) -> bool:
    """Validate a layout hash without treating arbitrary mismatches as aliases."""

    return hash_matches(
        layout,
        declared_hash,
        excluded_fields={"contract_sha256"},
        legacy_projections=(_legacy_identity_transform_projection,),
    )


def weight_layout_binding_matches(layout: dict[str, Any], bound_hash: Any) -> bool:
    """Check both the self-declared layout hash and an external binding."""

    return weight_layout_hash_matches(
        layout, layout.get("contract_sha256")
    ) and weight_layout_hash_matches(layout, bound_hash)


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
    preferred_text = str(preferred or "").lower()
    if preferred_text.startswith("int"):
        candidate = f"int{bits}"
    else:
        candidate = f"fp{bits}"
    if candidate not in DTYPE_BITS:
        raise ValueError(f"no declared deployed storage dtype for {bits} bits")
    return candidate


def conversion_contract(source_dtype: str, storage_dtype: str) -> dict[str, Any]:
    if storage_dtype in {"int4", "int8", "int32"} and source_dtype in {"fp16", "fp32"}:
        return {
            "kind": "symmetric_signed_quantization",
            "source_dtype": source_dtype,
            "storage_dtype": storage_dtype,
            "zero_point": 0,
            "rounding": "nearest_even",
            "saturation": True,
            "scale_granularity": "per_output_channel_for_matrix_else_per_tensor",
        }
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
    transpose_source: bool = False,
    array_rows: int | None = None,
    array_cols: int | None = None,
) -> dict[str, Any]:
    if not sources:
        raise ValueError(f"{target_id} has no source tensor")
    shapes = [[int(value) for value in source.get("shape", [])] for source in sources]
    if any(len(shape) != 2 for shape in shapes):
        raise ValueError(f"{target_id} requires rank-2 source tensors, got {shapes}")
    if transpose_source:
        in_features = shapes[0][0]
        if any(shape[0] != in_features for shape in shapes):
            raise ValueError(f"{target_id} source input dimensions disagree: {shapes}")
        out_features = sum(shape[1] for shape in shapes)
    else:
        in_features = shapes[0][1]
        if any(shape[1] != in_features for shape in shapes):
            raise ValueError(f"{target_id} source input dimensions disagree: {shapes}")
        out_features = sum(shape[0] for shape in shapes)
    tile_in_lanes = array_cols if array_cols is not None and array_cols > in_lanes else in_lanes
    tile_out_lanes = array_rows if array_cols is not None and array_cols > in_lanes else out_lanes
    if in_features % tile_in_lanes or out_features % tile_out_lanes:
        raise ValueError(
            f"{target_id} dimensions do not divide selected lanes: "
            f"shape=[{out_features}, {in_features}] tile_rows={tile_out_lanes} tile_cols={tile_in_lanes}"
        )
    scalar_bits = dtype_bits(storage_dtype)
    data_width_bits = tile_in_lanes * tile_out_lanes * scalar_bits
    if data_width_bits % 32:
        raise ValueError(f"{target_id} port width is not divisible by the 32-bit harness loader")
    in_beats = in_features // tile_in_lanes
    out_beats = out_features // tile_out_lanes
    write_count = in_beats * out_beats
    return {
        "target_id": target_id,
        "target_kind": "linear_weight_matrix",
        "dut_port_role": port_role,
        "source_tensors": [tensor_record(source) for source in sources],
        "compose": {
            "kind": "identity" if len(sources) == 1 else "concat",
            "axis": 1 if transpose_source else 0,
            "source_order": [source.get("parameter_suffix") for source in sources],
        },
        "logical_shape": [out_features, in_features],
        "source_axis_order": (
            ["input_feature", "output_feature"]
            if transpose_source
            else ["output_feature", "input_feature"]
        ),
        **({"source_transform": {"kind": "transpose_2d"}} if transpose_source else {}),
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
            "out_lanes": tile_out_lanes,
            "in_lanes": tile_in_lanes,
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


def linear_array_tile(stage: dict[str, Any], in_lanes: int, out_lanes: int) -> tuple[int | None, int | None]:
    rows = bound_int(stage, "compute_array_rows", out_lanes)
    cols = bound_int(stage, "compute_array_cols", in_lanes)
    if cols > in_lanes:
        return rows, cols
    return None, None


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
            in_lanes = bound_int(stage, str(row.get("in_lanes_param") or "lanes"))
            out_lanes = bound_int(stage, str(row.get("out_lanes_param") or "lanes"))
            array_rows, array_cols = linear_array_tile(stage, in_lanes, out_lanes)
            targets.append(
                linear_weight_target(
                    target_id=str(row.get("target_id")),
                    port_role=str(row.get("dut_port_role")),
                    sources=sources,
                    in_lanes=in_lanes,
                    out_lanes=out_lanes,
                    source_dtype=weight_dtype,
                    storage_dtype=storage,
                    transpose_source=bool(row.get("transpose_source", False)),
                    array_rows=array_rows,
                    array_cols=array_cols,
                )
            )
        elif kind in {"norm_scale_vector", "norm_bias_vector", "linear_bias_vector"}:
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
    if op.startswith("layer_norm"):
        roles: dict[str, dict[str, Any]] = {}
        for suffix, binding in by_suffix.items():
            role = suffix.rsplit(".", 1)[-1]
            if role in {"weight", "bias"}:
                roles[role] = binding
        if set(roles) != {"weight", "bias"} or len(bindings) != 2:
            raise ValueError(
                f"{stage.get('stage_id')}: LayerNorm requires exactly one weight and one bias tensor"
            )
        storage_dtype = storage_dtype_for_bits(acc_dtype, bound_int(stage, "input_bits"))
        # VectorNorm consumes beta before gamma on its single weight stream.
        return [
            vector_target(
                target_id="norm.bias",
                target_kind="norm_bias_vector",
                port_role="weight",
                sources=[roles["bias"]],
                elements_per_write=lanes,
                source_dtype=weight_dtype,
                storage_dtype=storage_dtype,
            ),
            vector_target(
                target_id="norm.scale",
                target_kind="norm_scale_vector",
                port_role="weight",
                sources=[roles["weight"]],
                elements_per_write=lanes,
                source_dtype=weight_dtype,
                storage_dtype=storage_dtype,
            ),
        ], "canonical_semantic_op_layout.v1"
    if op in {"mlp_gate_proj", "mlp_up_proj", "mlp_down_proj"}:
        if len(bindings) != 1:
            raise ValueError(f"{stage.get('stage_id')}: standalone MLP projection requires one matrix")
        array_rows, array_cols = linear_array_tile(stage, lanes, lanes)
        return [
            linear_weight_target(
                target_id="linear.weight",
                port_role="weight",
                sources=bindings,
                in_lanes=lanes,
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
                array_rows=array_rows,
                array_cols=array_cols,
            )
        ], "canonical_semantic_op_layout.v1"
    if op == "self_attention":
        roles: dict[tuple[str, str], dict[str, Any]] = {}
        for suffix, binding in by_suffix.items():
            role = projection_role(suffix)
            if role is not None:
                roles[role] = binding
        standard_projection_names = ("q_proj", "k_proj", "v_proj", "o_proj")
        fused_conv1d = ("c_attn", "weight") in roles and ("c_proj", "weight") in roles
        if fused_conv1d:
            qkv_weights = [roles[("c_attn", "weight")]]
            out_weight = roles[("c_proj", "weight")]
            qkv_biases = [roles[("c_attn", "bias")]] if ("c_attn", "bias") in roles else []
            out_bias = roles.get(("c_proj", "bias"))
            transpose_source = True
        else:
            required_weight_roles = [(name, "weight") for name in standard_projection_names]
            missing = [role for role in required_weight_roles if role not in roles]
            if missing:
                raise ValueError(f"{stage.get('stage_id')}: canonical attention layout is missing roles {missing}")
            qkv_weights = [roles[(name, "weight")] for name in ("q_proj", "k_proj", "v_proj")]
            out_weight = roles[("o_proj", "weight")]
            qkv_biases = [roles[(name, "bias")] for name in ("q_proj", "k_proj", "v_proj") if (name, "bias") in roles]
            out_bias = roles.get(("o_proj", "bias"))
            transpose_source = False
        qkv_array_rows, qkv_array_cols = linear_array_tile(stage, lanes, lanes)
        out_array_rows, out_array_cols = linear_array_tile(stage, bound_int(stage, "head_dim"), lanes)
        targets = [
            linear_weight_target(
                target_id="attention.qkv.weight",
                port_role="qkv_weight",
                sources=qkv_weights,
                in_lanes=lanes,
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
                transpose_source=transpose_source,
                array_rows=qkv_array_rows,
                array_cols=qkv_array_cols,
            )
        ]
        if qkv_biases and (not fused_conv1d and len(qkv_biases) != 3):
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
                sources=[out_weight],
                in_lanes=bound_int(stage, "head_dim"),
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
                transpose_source=transpose_source,
                array_rows=out_array_rows,
                array_cols=out_array_cols,
            )
        )
        if out_bias is not None:
            targets.append(
                vector_target(
                    target_id="attention.out_proj.bias",
                    target_kind="linear_bias_vector",
                    port_role="out_proj_bias",
                    sources=[out_bias],
                    elements_per_write=lanes,
                    source_dtype=weight_dtype,
                    storage_dtype=acc_dtype,
                )
            )
        return targets, "canonical_semantic_op_layout.v1"
    if op in {"mlp_fc", "mlp_proj"}:
        prefix = "c_fc" if op == "mlp_fc" else "c_proj"
        roles = {
            suffix.rsplit(".", 1)[-1]: binding
            for suffix, binding in by_suffix.items()
            if f".{prefix}." in f".{suffix}"
        }
        if set(roles) != {"weight", "bias"}:
            raise ValueError(
                f"{stage.get('stage_id')}: {op} requires exactly one {prefix}.weight and {prefix}.bias tensor"
            )
        weight_role = "weight_mlp_up" if op == "mlp_fc" else "weight_mlp_down"
        bias_role = f"{weight_role}_bias"
        array_rows, array_cols = linear_array_tile(stage, lanes, lanes)
        return [
            linear_weight_target(
                target_id="linear.weight",
                port_role=weight_role,
                sources=[roles["weight"]],
                in_lanes=lanes,
                out_lanes=lanes,
                source_dtype=weight_dtype,
                storage_dtype=weight_dtype,
                transpose_source=True,
                array_rows=array_rows,
                array_cols=array_cols,
            ),
            vector_target(
                target_id="linear.bias",
                target_kind="linear_bias_vector",
                port_role=bias_role,
                sources=[roles["bias"]],
                elements_per_write=lanes,
                source_dtype=weight_dtype,
                storage_dtype=acc_dtype,
            ),
        ], "canonical_semantic_op_layout.v1"
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
    weight_dtype = canonical_dtype(rules.get("weight_dtype")).lower()
    acc_dtype = canonical_dtype(rules.get("acc_dtype")).lower()
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
            "source_matrix_axis_order": (
                "checkpoint [input_feature, output_feature] for transposed targets"
                if any(
                    target.get("source_transform", {}).get("kind") == "transpose_2d"
                    for target in normalized_targets
                )
                else "checkpoint [output_feature, input_feature]"
            ),
            "linear_storage_order": "out_beat, in_beat, out_lane, in_lane",
            "source_values_are_rounded_to_weight_dtype_before_storage_conversion": True,
            "padding": "forbidden because selected dimensions must divide selected lanes",
            "default_or_identity_fallback": "forbidden",
        },
    }
    contract["contract_sha256"] = identity_sha256(contract)
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


def _policy_scalar_scale_fixed_point() -> dict[str, Any]:
    """Declare unit activation/output scales in the signed-INT8 code domain.

    This is an explicit numeric-policy convention for a run with no learned
    activation calibration payload. It is not inferred from checkpoint values
    or DUT outputs. The per-output-channel matrix scales remain independently
    derived from the real checkpoint tensors.
    """

    unit = _q31_scale_encoding(1.0)
    convention = {
        "id": "w4a8_signed_int8_code_domain_unit_real_scale",
        "activation_real_scale": 1.0,
        "output_real_scale": 1.0,
        "source": "explicit_numeric_policy_code_domain_convention",
        "learned_activation_calibration_assumed": False,
    }
    return {
        "representation": "unsigned_q31_multiplier_times_power_of_two",
        "fractional_bits": 31,
        "scalar_scale_convention": convention,
        "activationScale": dict(unit),
        "activationShift": int(unit["binary_shift"]),
        "outputScale": dict(unit),
        "outputShift": int(unit["binary_shift"]),
    }


def _q31_scale_encoding(scale: float) -> dict[str, int]:
    """Encode a positive real scale as unsigned Q31 mantissa plus exponent."""

    if not math.isfinite(float(scale)) or float(scale) <= 0.0:
        raise ValueError(f"quantization scale must be finite and positive, got {scale!r}")
    mantissa, exponent = math.frexp(float(scale))
    multiplier = int(round(mantissa * (1 << 31)))
    if multiplier >= (1 << 31):
        multiplier >>= 1
        exponent += 1
    if multiplier <= 0 or multiplier >= (1 << 31):
        raise ValueError(f"quantization scale cannot be represented as unsigned Q31: {scale!r}")
    return {
        "multiplier_unsigned_q31": multiplier,
        "binary_shift": int(exponent),
    }


def _q31_scale_encoding_list(scales: list[float]) -> list[dict[str, int]]:
    return [_q31_scale_encoding(scale) for scale in scales]


def target_scalars(target: dict[str, Any], by_suffix: dict[str, dict[str, Any]]) -> tuple[Any, dict[str, Any] | None]:
    """Read source FP tensors, quantize to deployed integer storage, then tile-pack.

    Checkpoint dtype remains independent from deployed dtype. Matrix quantizing
    uses symmetric per-output-channel scales; vector/bias targets use a
    symmetric per-tensor scale. torch.round implements nearest-even rounding.
    The scale record is carried alongside the packed stream for downstream
    loader/scale-port binding rather than being silently discarded.
    """
    import torch

    conversion = target.get("value_conversion", {}) if isinstance(target.get("value_conversion"), dict) else {}
    source_dtype = str(conversion.get("source_dtype") or "")
    source_order = target.get("compose", {}).get("source_order", [])
    tensors = [load_target_tensor(by_suffix[str(suffix)], source_dtype) for suffix in source_order]
    axis = int(target.get("compose", {}).get("axis", 0))
    value = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=axis)
    if target.get("source_transform", {}).get("kind") == "transpose_2d":
        value = value.transpose(0, 1).contiguous()
    logical_shape = [int(item) for item in target.get("logical_shape", [])]
    if list(value.shape) != logical_shape:
        raise ValueError(f"{target.get('target_id')}: composed tensor shape {list(value.shape)} != {logical_shape}")
    storage_dtype = str(target.get("storage_scalar_dtype") or "")
    quantization: dict[str, Any] | None = None
    if storage_dtype in {"int4", "int8", "int32"}:
        bits = {"int4": 4, "int8": 8, "int32": 32}[storage_dtype]
        qmin = -(1 << (bits - 1))
        qmax = (1 << (bits - 1)) - 1
        if target.get("target_kind") == "linear_weight_matrix":
            if value.ndim != 2:
                raise ValueError(f"{target.get('target_id')}: quantized matrix must have rank two")
            maxima = value.abs().amax(dim=1)
            scales = torch.where(maxima > 0, maxima / float(qmax), torch.ones_like(maxima))
            value = torch.round(value / scales[:, None]).clamp(qmin, qmax).to(torch.int64)
            scale_values = [float(item) for item in scales.tolist()]
            quantization = {
                "scheme": "symmetric_signed_per_output_channel",
                "rounding": "nearest_even",
                "zero_point": 0,
                "saturation_range": [qmin, qmax],
                "scale": scale_values,
                "scale_fixed_point": {
                    "representation": "unsigned_q31_multiplier_times_power_of_two",
                    "fractional_bits": 31,
                    "channels": _q31_scale_encoding_list(scale_values),
                },
                # Activation/output scalar metadata is supplied by the
                # explicit current-policy code-domain convention, not by an
                # invented learned calibration value. Keep it separate from
                # the checkpoint-derived per-output-channel weight scales.
                "scalar_scale_fixed_point": _policy_scalar_scale_fixed_point(),
            }
        else:
            maximum = float(value.abs().max().item()) if value.numel() else 0.0
            scale = maximum / float(qmax) if maximum > 0 else 1.0
            value = torch.round(value / scale).clamp(qmin, qmax).to(torch.int64)
            quantization = {
                "scheme": "symmetric_signed_per_tensor",
                "rounding": "nearest_even",
                "zero_point": 0,
                "saturation_range": [qmin, qmax],
                "scale": float(scale),
                "scale_fixed_point": {
                    "representation": "unsigned_q31_multiplier_times_power_of_two",
                    "fractional_bits": 31,
                    **_q31_scale_encoding(float(scale)),
                },
            }
    elif storage_dtype == "fp16":
        value = value.to(torch.float16)
    elif storage_dtype == "fp32":
        value = value.to(torch.float32)
    else:
        raise ValueError(f"unsupported storage dtype: {storage_dtype}")
    if target.get("target_kind") == "linear_weight_matrix":
        out_features, in_features = logical_shape
        tile = target["tile"]
        out_lanes = int(tile["out_lanes"])
        in_lanes = int(tile["in_lanes"])
        if out_features % out_lanes or in_features % in_lanes:
            raise ValueError(f"{target.get('target_id')}: matrix dimensions do not divide the tile")
        value = value.reshape(out_features // out_lanes, out_lanes, in_features // in_lanes, in_lanes)
        value = value.permute(0, 2, 1, 3).contiguous()
    elif len(logical_shape) != 1:
        raise ValueError(f"{target.get('target_id')}: unsupported non-vector target shape {logical_shape}")
    return value.reshape(-1), quantization


def scalar_words(value: Any, dtype: str) -> list[int]:
    import torch

    if dtype == "fp16":
        raw = value.contiguous().view(torch.int16).reshape(-1).tolist()
        return [int(item) & 0xFFFF for item in raw]
    if dtype == "fp32":
        raw = value.contiguous().view(torch.int32).reshape(-1).tolist()
        return [int(item) & 0xFFFFFFFF for item in raw]
    if dtype in {"int4", "int8", "int32"}:
        bits = {"int4": 4, "int8": 8, "int32": 32}[dtype]
        return [int(item) & ((1 << bits) - 1) for item in value.to(torch.int64).reshape(-1).tolist()]
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
        scalars, quantization = target_scalars(target, by_suffix)
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
        scale_metadata = None
        scale_payload = None
        scale_consumer_binding = None
        if isinstance(quantization, dict):
            fixed_point = quantization.get("scale_fixed_point")
            if isinstance(fixed_point, dict):
                # This is the canonical materialized payload. Merge the
                # checkpoint-derived per-channel weight fields with the
                # explicitly declared policy code-domain scalar fields while
                # preserving each source and channel order.
                scalar_fixed_point = quantization.get("scalar_scale_fixed_point")
                scale_payload = deepcopy(fixed_point)
                if isinstance(scalar_fixed_point, dict):
                    scale_payload.update(deepcopy(scalar_fixed_point))
                scale_metadata = {
                    "representation": fixed_point.get("representation"),
                    "fractional_bits": fixed_point.get("fractional_bits"),
                    "payload": deepcopy(scale_payload),
                    "scalar_scale_convention": deepcopy(
                        scalar_fixed_point.get("scalar_scale_convention")
                        if isinstance(scalar_fixed_point, dict)
                        else None
                    ),
                    "consumer_binding": "LinearScalePorts.channelScale/activationScale/outputScale and downstream requantizeQ31WithShift",
                }
                scale_consumer_binding = scale_metadata["consumer_binding"]
        target_rows.append(
            {
                "target_id": target.get("target_id"),
                "target_kind": target.get("target_kind"),
                "dut_port_role": target.get("dut_port_role"),
                "storage_scalar_dtype": target.get("storage_scalar_dtype"),
                "storage_scalar_bits": target.get("storage_scalar_bits"),
                "logical_shape": deepcopy(target.get("logical_shape")),
                "tile": deepcopy(target.get("tile")),
                "quantization": quantization,
                "scale_metadata": scale_metadata,
                "scale_payload": scale_payload,
                "scale_consumer_binding": scale_consumer_binding,
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
        if not layout_hash or not weight_layout_hash_matches(layout, layout_hash):
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
                    "target_kind": target.get("target_kind"),
                    "dut_port_role": target.get("dut_port_role"),
                    "storage_scalar_dtype": target.get("storage_scalar_dtype"),
                    "storage_scalar_bits": target.get("storage_scalar_bits"),
                    "logical_shape": deepcopy(target.get("logical_shape")),
                    "tile": deepcopy(target.get("tile")),
                    "local_stream_range": expected_range,
                    "global_stream_range": global_range,
                    "port": target.get("port"),
                    "quantization": deepcopy(target.get("quantization")),
                    "scale_metadata": deepcopy(target.get("scale_metadata")),
                    "scale_payload": deepcopy(target.get("scale_payload")),
                    "scale_consumer_binding": deepcopy(target.get("scale_consumer_binding")),
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

            # The canonical layout declares structural target ranges, while the
            # local stream materializes checkpoint-derived quantization. Bind
            # those records by stable target_id before composing the global
            # stream. Never retain layout-only metadata when the local stream
            # contains the actual INT4/INT8 quantization and Q31 scale payload.
            stream_targets_by_id: dict[str, dict[str, Any]] = {}
            for stream_index, stream_target in enumerate(stream_targets):
                if not isinstance(stream_target, dict):
                    raise ValueError(
                        f"{stage_id}: canonical local stream target {stream_index} is not an object"
                    )
                stream_target_id = str(stream_target.get("target_id") or "")
                if not stream_target_id or stream_target_id in stream_targets_by_id:
                    raise ValueError(
                        f"{stage_id}: canonical local stream target ids must be non-empty and unique"
                    )
                stream_targets_by_id[stream_target_id] = stream_target
            layout_target_ids = [str(target.get("target_id") or "") for target in targets]
            if set(stream_targets_by_id) != set(layout_target_ids):
                raise ValueError(
                    f"{stage_id}: materialized local stream target ids do not match canonical layout targets"
                )
            for target_segment in target_segments:
                target_id = target_segment["target_id"]
                materialized_target = stream_targets_by_id[target_id]
                # Preserve exact materialized values and per-channel ordering;
                # board_weight_image.py consumes these composite target records.
                if "quantization" in materialized_target:
                    target_segment["quantization"] = deepcopy(materialized_target["quantization"])
                if "scale_metadata" in materialized_target:
                    target_segment["scale_metadata"] = deepcopy(materialized_target["scale_metadata"])
                if "scale_payload" in materialized_target:
                    target_segment["scale_payload"] = deepcopy(materialized_target["scale_payload"])
                # Preserve the complete materialized target record at the
                # local-to-composite boundary. Board image generation consumes
                # this record, so route/range metadata and checkpoint-derived
                # quantization must remain bound to the same stable target_id.
                target_segment["materialized_target"] = deepcopy(materialized_target)

            for target in targets:
                target_id = str(target.get("target_id") or "")
                target_segment = next(
                    segment for segment in target_segments
                    if segment["target_id"] == target_id
                )
                stream_target = stream_targets_by_id[target_id]
                expected_stream_target = {
                    "target_id": target_segment["target_id"],
                    "dut_port_role": target_segment["dut_port_role"],
                    "stream_range": target_segment["local_stream_range"],
                    "port": target_segment["port"],
                    "source_tensor_hashes": target_segment["source_tensor_hashes"],
                }
                # Quantization and fixed-point scale payloads are materialized
                # from the real checkpoint tensors during stream generation;
                # they are intentionally absent from the canonical layout
                # template. Validate stable route/range/source metadata exactly,
                # then require and preserve the materialized integer metadata.
                for key, expected_value in expected_stream_target.items():
                    if stream_target.get(key) != expected_value:
                        raise ValueError(
                            f"{stage_id}/{target_id}: canonical local stream target metadata mismatch"
                        )
                storage_dtype = str(target.get("storage_scalar_dtype") or "")
                if storage_dtype in {"int4", "int8", "int32"}:
                    quantization = stream_target.get("quantization")
                    if not isinstance(quantization, dict):
                        raise ValueError(
                            f"{stage_id}/{target_id}: materialized integer quantization metadata is missing"
                        )
                    fixed_point = quantization.get("scale_fixed_point")
                    if not isinstance(fixed_point, dict):
                        raise ValueError(
                            f"{stage_id}/{target_id}: materialized Q31 scale/shift metadata is missing"
                        )
                    expected_scale_payload = deepcopy(fixed_point)
                    scalar_fixed_point = quantization.get("scalar_scale_fixed_point")
                    if isinstance(scalar_fixed_point, dict):
                        expected_scale_payload.update(deepcopy(scalar_fixed_point))
                    if stream_target.get("scale_payload") != expected_scale_payload:
                        raise ValueError(
                            f"{stage_id}/{target_id}: first-class scale payload differs from canonical quantization and policy scalar convention"
                        )
                    materialized_scale_metadata = stream_target.get("scale_metadata")
                    if not isinstance(materialized_scale_metadata, dict) or materialized_scale_metadata.get("payload") != expected_scale_payload:
                        raise ValueError(
                            f"{stage_id}/{target_id}: scale_metadata payload differs from canonical quantization and policy scalar convention"
                        )
                    if not stream_target.get("scale_consumer_binding"):
                        raise ValueError(
                            f"{stage_id}/{target_id}: materialized scale consumer binding is missing"
                        )
                    if fixed_point.get("representation") != "unsigned_q31_multiplier_times_power_of_two":
                        raise ValueError(
                            f"{stage_id}/{target_id}: unsupported fixed-point scale representation"
                        )
                    if fixed_point.get("fractional_bits") != 31:
                        raise ValueError(
                            f"{stage_id}/{target_id}: fixed-point scale must use Q31 fractional bits"
                        )
                    if storage_dtype == "int4" and quantization.get("saturation_range") != [-8, 7]:
                        raise ValueError(
                            f"{stage_id}/{target_id}: INT4 saturation range is not signed W4"
                        )
                    declared_scale_metadata = target_segment.get("scale_metadata")
                    materialized_scale_metadata = stream_target.get("scale_metadata")
                    if declared_scale_metadata is not None and materialized_scale_metadata != declared_scale_metadata:
                        raise ValueError(
                            f"{stage_id}/{target_id}: materialized scale metadata differs from canonical declaration"
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
