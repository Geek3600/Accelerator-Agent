"""Materialize complete Transformer-block checkpoint weights for board simulation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from accagent.framework.weight_layout import (
    COMPOSITE_STREAM_SCHEMA_VERSION,
    SCHEMA_VERSION as WEIGHT_LAYOUT_SCHEMA_VERSION,
    sha256_file,
    sha256_json,
)
from accagent.framework.board_validation_scope import (
    BoardValidationScopeError,
    validation_scope_from_plan,
)


SCHEMA_VERSION = "spatialaccagent.full_weight_image_manifest.v1"
PLAN_SCHEMA_VERSION = "spatialaccagent.board_workload_image_plan.v1"
IMAGE_FORMAT = "u32le_binary"
SUPPORTED_SOURCE_DTYPES = {"BF16": 2, "F16": 2, "F32": 4}
HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


class BoardWeightImageError(RuntimeError):
    """Raised when a complete board weight image cannot be proven correct."""


@dataclass(frozen=True)
class _Document:
    value: dict[str, Any]
    canonical_sha256: str
    identity_sha256: str
    base_dir: Path
    path: Path | None
    file_sha256: str | None


def _load_document(value: dict[str, Any] | str | Path, label: str) -> _Document:
    path: Path | None = None
    file_hash: str | None = None
    if isinstance(value, dict):
        document = value
        base_dir = Path.cwd().resolve()
    elif isinstance(value, (str, Path)):
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise BoardWeightImageError(f"{label} file is missing: {path}")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BoardWeightImageError(f"cannot read {label}: {path}: {exc}") from exc
        if not isinstance(document, dict):
            raise BoardWeightImageError(f"{label} must be a JSON object: {path}")
        base_dir = path.parent
        file_hash = sha256_file(path)
    else:
        raise BoardWeightImageError(f"{label} must be a JSON object or path")
    canonical_hash = sha256_json(document)
    return _Document(
        value=document,
        canonical_sha256=canonical_hash,
        identity_sha256=file_hash or canonical_hash,
        base_dir=base_dir,
        path=path,
        file_sha256=file_hash,
    )


def _hash(value: Any, label: str) -> str:
    normalized = str(value or "").lower()
    if not HASH_PATTERN.fullmatch(normalized):
        raise BoardWeightImageError(f"{label} is not a SHA-256 digest")
    return normalized


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BoardWeightImageError(f"{label} must be an integer >= {minimum}")
    return value


def _range(word_offset: int, word_count: int) -> dict[str, int]:
    return {
        "word_offset": word_offset,
        "word_count": word_count,
        "word_end_exclusive": word_offset + word_count,
    }


def _byte_range(byte_offset: int, byte_count: int) -> dict[str, int]:
    return {
        "byte_offset": byte_offset,
        "byte_count": byte_count,
        "byte_end_exclusive": byte_offset + byte_count,
    }


def _align_up(value: int, alignment: int) -> int:
    return ((value + alignment - 1) // alignment) * alignment


def _tensor_elements(shape: list[Any], label: str) -> int:
    if not shape or not all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in shape):
        raise BoardWeightImageError(f"{label} has an invalid non-positive shape: {shape}")
    return math.prod(shape)


def _resolve_source_path(raw: Any, base_dir: Path, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise BoardWeightImageError(f"{label}.source_file is missing")
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else base_dir / path).resolve()


def _validate_catalog(
    document: _Document,
) -> tuple[list[int], list[str], dict[tuple[int, str], dict[str, Any]], list[dict[str, Any]]]:
    catalog = document.value
    if catalog.get("status") != "pass":
        raise BoardWeightImageError("Transformer-block weight catalog status is not pass")
    if catalog.get("accelerator_scope") != "transformer_blocks_only":
        raise BoardWeightImageError("weight catalog accelerator_scope must be transformer_blocks_only")
    if catalog.get("scope_coverage_complete") is not True:
        raise BoardWeightImageError("weight catalog scope_coverage_complete is not true")

    raw_layer_ids = catalog.get("layer_ids")
    if not isinstance(raw_layer_ids, list) or not raw_layer_ids:
        raise BoardWeightImageError("weight catalog layer_ids is empty or malformed")
    layer_ids = [_integer(value, f"weight catalog layer_ids[{index}]") for index, value in enumerate(raw_layer_ids)]
    if len(set(layer_ids)) != len(layer_ids) or layer_ids != sorted(layer_ids):
        raise BoardWeightImageError("weight catalog layer_ids must be unique and ascending")
    target_layer_count = _integer(catalog.get("target_layer_count"), "weight catalog target_layer_count", minimum=1)
    if target_layer_count != len(layer_ids):
        raise BoardWeightImageError("weight catalog target_layer_count does not match layer_ids")

    tensor_rows = catalog.get("tensors")
    if not isinstance(tensor_rows, list) or not tensor_rows:
        raise BoardWeightImageError("weight catalog tensors is empty or malformed")
    if _integer(catalog.get("tensor_count"), "weight catalog tensor_count", minimum=1) != len(tensor_rows):
        raise BoardWeightImageError("weight catalog tensor_count does not match tensors")

    by_key: dict[tuple[int, str], dict[str, Any]] = {}
    names: set[str] = set()
    suffixes_by_layer: dict[int, set[str]] = {layer: set() for layer in layer_ids}
    source_identities: dict[Path, str] = {}
    normalized_rows: list[dict[str, Any]] = []
    for index, original in enumerate(tensor_rows):
        if not isinstance(original, dict):
            raise BoardWeightImageError(f"weight catalog tensor[{index}] is not an object")
        row = dict(original)
        layer = _integer(row.get("layer_index"), f"weight catalog tensor[{index}].layer_index")
        suffix = str(row.get("parameter_suffix") or "")
        name = str(row.get("name") or "")
        if layer not in suffixes_by_layer or not suffix:
            raise BoardWeightImageError(f"weight catalog tensor[{index}] has an unknown layer or empty suffix")
        if not name or name in names:
            raise BoardWeightImageError(f"weight catalog tensor names must be non-empty and unique: {name!r}")
        key = (layer, suffix)
        if key in by_key:
            raise BoardWeightImageError(f"duplicate catalog tensor for layer={layer} suffix={suffix}")

        dtype = str(row.get("dtype") or "").upper()
        if dtype not in SUPPORTED_SOURCE_DTYPES:
            raise BoardWeightImageError(f"{name}: unsupported safetensors dtype {dtype!r}")
        shape = row.get("shape")
        if not isinstance(shape, list):
            raise BoardWeightImageError(f"{name}: shape is not a list")
        element_count = _tensor_elements(shape, name)
        offsets = row.get("data_offsets")
        if not isinstance(offsets, list) or len(offsets) != 2:
            raise BoardWeightImageError(f"{name}: data_offsets is malformed")
        start = _integer(offsets[0], f"{name}.data_offsets[0]")
        end = _integer(offsets[1], f"{name}.data_offsets[1]")
        if end < start:
            raise BoardWeightImageError(f"{name}: data_offsets are reversed")
        byte_count = end - start
        expected_bytes = element_count * SUPPORTED_SOURCE_DTYPES[dtype]
        if byte_count != expected_bytes:
            raise BoardWeightImageError(f"{name}: source byte count {byte_count} != dtype/shape byte count {expected_bytes}")
        declared_count = row.get("source_byte_count")
        if declared_count is not None and _integer(declared_count, f"{name}.source_byte_count") != byte_count:
            raise BoardWeightImageError(f"{name}: source_byte_count does not match data_offsets")
        source_path = _resolve_source_path(row.get("source_file"), document.base_dir, name)
        source_hash = _hash(row.get("source_file_sha256"), f"{name}.source_file_sha256")
        if source_path in source_identities and source_identities[source_path] != source_hash:
            raise BoardWeightImageError(f"catalog declares conflicting hashes for source shard {source_path}")
        source_identities[source_path] = source_hash
        data_base = _integer(row.get("source_data_base"), f"{name}.source_data_base", minimum=8)
        slice_hash = _hash(row.get("source_slice_sha256"), f"{name}.source_slice_sha256")

        normalized = {
            **row,
            "layer_index": layer,
            "parameter_suffix": suffix,
            "name": name,
            "dtype": dtype,
            "shape": list(shape),
            "data_offsets": [start, end],
            "source_data_base": data_base,
            "source_file_sha256": source_hash,
            "source_slice_sha256": slice_hash,
            "source_byte_count": byte_count,
            "_source_path": source_path,
        }
        by_key[key] = normalized
        normalized_rows.append(normalized)
        suffixes_by_layer[layer].add(suffix)
        names.add(name)

    suffixes = sorted(suffixes_by_layer[layer_ids[0]])
    if not suffixes:
        raise BoardWeightImageError("first catalog layer has no Transformer-block tensors")
    inconsistent = [layer for layer in layer_ids if sorted(suffixes_by_layer[layer]) != suffixes]
    if inconsistent:
        raise BoardWeightImageError(f"catalog layer suffix coverage is inconsistent: {inconsistent}")
    if len(tensor_rows) != len(layer_ids) * len(suffixes):
        raise BoardWeightImageError("catalog does not contain exactly one tensor per layer and suffix")
    declared_suffixes = catalog.get("tensor_suffixes")
    if declared_suffixes is not None and (
        not isinstance(declared_suffixes, list) or sorted(str(value) for value in declared_suffixes) != suffixes
    ):
        raise BoardWeightImageError("weight catalog tensor_suffixes does not match tensor rows")
    per_layer = catalog.get("per_layer_tensor_count")
    if per_layer is not None and _integer(per_layer, "weight catalog per_layer_tensor_count", minimum=1) != len(suffixes):
        raise BoardWeightImageError("weight catalog per_layer_tensor_count does not match suffix coverage")
    return layer_ids, suffixes, by_key, normalized_rows


def _contract_hash(value: dict[str, Any], label: str, *, exclude_path: bool = False) -> str:
    declared = _hash(value.get("contract_sha256"), f"{label}.contract_sha256")
    excluded = {"contract_sha256"}
    if exclude_path:
        excluded.add("path")
    payload = {key: item for key, item in value.items() if key not in excluded}
    if sha256_json(payload) != declared:
        raise BoardWeightImageError(f"{label} contract hash mismatch")
    return declared


def _validate_layouts(
    requirements_document: _Document,
    catalog_document: _Document,
    catalog: dict[str, Any],
    layer_ids: list[int],
    suffixes: list[str],
    catalog_by_key: dict[tuple[int, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, str, list[str], str]:
    requirements = requirements_document.value
    if requirements.get("accelerator_scope") != "transformer_blocks_only":
        raise BoardWeightImageError("weight requirements accelerator_scope must be transformer_blocks_only")
    if requirements.get("accelerator_weight_catalog_sha256") != catalog_document.identity_sha256:
        raise BoardWeightImageError("weight requirements do not bind the supplied Transformer-block catalog")
    checkpoint_hash = _hash(catalog.get("source_checkpoint_sha256"), "catalog.source_checkpoint_sha256")
    if requirements.get("source_checkpoint_sha256") != checkpoint_hash:
        raise BoardWeightImageError("weight requirements source checkpoint identity does not match catalog")

    connected = requirements.get("connected_weight_stream_contract")
    if not isinstance(connected, dict):
        raise BoardWeightImageError("connected_weight_stream_contract is missing")
    if connected.get("schema_version") != COMPOSITE_STREAM_SCHEMA_VERSION or connected.get("status") != "pass":
        raise BoardWeightImageError("connected weight stream contract is not pass")
    if connected.get("word_bits") != 32:
        raise BoardWeightImageError("connected weight stream contract word_bits must be 32")
    connected_hash = _contract_hash(connected, "connected weight stream", exclude_path=True)

    raw_stages = requirements.get("stage_requirements")
    if not isinstance(raw_stages, list) or not raw_stages:
        raise BoardWeightImageError("weight requirements stage_requirements is empty or malformed")
    template_layer = layer_ids[0]
    stage_descriptors: list[dict[str, Any]] = []
    layout_hashes: list[str] = []
    covered_suffixes: list[str] = []
    stage_ids: set[str] = set()
    local_word_offset = 0
    for stage_index, stage in enumerate(raw_stages):
        if not isinstance(stage, dict):
            raise BoardWeightImageError(f"stage_requirements[{stage_index}] is not an object")
        stage_id = str(stage.get("stage_id") or "")
        op = str(stage.get("op") or "")
        if not stage_id or not op or stage_id in stage_ids:
            raise BoardWeightImageError("canonical stage ids and ops must be non-empty and stage ids unique")
        stage_ids.add(stage_id)
        layout = stage.get("weight_layout")
        if not isinstance(layout, dict):
            raise BoardWeightImageError(f"{stage_id}: canonical weight_layout is missing")
        if layout.get("schema_version") != WEIGHT_LAYOUT_SCHEMA_VERSION or layout.get("status") != "pass":
            raise BoardWeightImageError(f"{stage_id}: canonical weight_layout is not pass")
        if layout.get("stage_id") != stage_id or layout.get("op") != op:
            raise BoardWeightImageError(f"{stage_id}: stage identity differs from canonical weight_layout")
        layout_hash = _contract_hash(layout, f"{stage_id} weight layout")
        if stage.get("weight_layout_contract_sha256") != layout_hash:
            raise BoardWeightImageError(f"{stage_id}: requirement does not bind canonical weight_layout hash")
        layout_hashes.append(layout_hash)

        stage_word_count = _integer(layout.get("stream_word_count"), f"{stage_id}.stream_word_count")
        target_rows = layout.get("storage_targets")
        if not isinstance(target_rows, list):
            raise BoardWeightImageError(f"{stage_id}: storage_targets is not a list")
        target_descriptors: list[dict[str, Any]] = []
        target_ids: set[str] = set()
        target_word_offset = 0
        stage_template_hashes: list[str] = []
        stage_suffixes: list[str] = []
        for target_index, target in enumerate(target_rows):
            if not isinstance(target, dict):
                raise BoardWeightImageError(f"{stage_id}: storage target[{target_index}] is not an object")
            target_id = str(target.get("target_id") or "")
            if not target_id or target_id in target_ids:
                raise BoardWeightImageError(f"{stage_id}: target ids must be non-empty and unique")
            target_ids.add(target_id)
            word_count = _integer(target.get("stream_word_count"), f"{stage_id}/{target_id}.stream_word_count")
            expected_range = _range(target_word_offset, word_count)
            if target.get("stream_range") != expected_range:
                raise BoardWeightImageError(f"{stage_id}/{target_id}: canonical target stream_range is not contiguous")
            if target.get("storage_scalar_dtype") not in {"fp16", "fp32"}:
                raise BoardWeightImageError(f"{stage_id}/{target_id}: unsupported storage scalar dtype")
            scalar_bits = _integer(target.get("storage_scalar_bits"), f"{stage_id}/{target_id}.storage_scalar_bits", minimum=1)
            if scalar_bits not in {16, 32} or scalar_bits != int(str(target.get("storage_scalar_dtype"))[2:]):
                raise BoardWeightImageError(f"{stage_id}/{target_id}: storage dtype/bits disagree")
            compose = target.get("compose")
            source_templates = target.get("source_tensors")
            if not isinstance(compose, dict) or not isinstance(source_templates, list) or not source_templates:
                raise BoardWeightImageError(f"{stage_id}/{target_id}: source composition is missing")
            source_order = compose.get("source_order")
            template_suffixes = [
                str(source.get("parameter_suffix") or "") if isinstance(source, dict) else ""
                for source in source_templates
            ]
            if source_order != template_suffixes or any(not suffix for suffix in template_suffixes):
                raise BoardWeightImageError(f"{stage_id}/{target_id}: source_order differs from source_tensors")
            if compose.get("kind") not in {"identity", "concat"}:
                raise BoardWeightImageError(f"{stage_id}/{target_id}: unsupported source composition")
            if compose.get("kind") == "identity" and len(template_suffixes) != 1:
                raise BoardWeightImageError(f"{stage_id}/{target_id}: identity composition must have one source")
            if compose.get("kind") == "concat" and compose.get("axis") != 0:
                raise BoardWeightImageError(f"{stage_id}/{target_id}: only axis-0 concatenation is supported")
            for source in source_templates:
                suffix = str(source["parameter_suffix"])
                row = catalog_by_key.get((template_layer, suffix))
                if row is None:
                    raise BoardWeightImageError(f"{stage_id}/{target_id}: catalog lacks template-layer suffix {suffix}")
                if list(source.get("shape") or []) != row["shape"]:
                    raise BoardWeightImageError(f"{stage_id}/{target_id}/{suffix}: canonical and catalog shapes differ")
                template_hash = _hash(source.get("sha256"), f"{stage_id}/{target_id}/{suffix}.sha256")
                source_dtype = str(source.get("source_dtype") or "").upper()
                if source_dtype and source_dtype != row["dtype"]:
                    raise BoardWeightImageError(f"{stage_id}/{target_id}/{suffix}: template dtype differs from catalog")
                covered_suffixes.append(suffix)
                stage_suffixes.append(suffix)
                stage_template_hashes.append(template_hash)
            target_descriptors.append(
                {
                    "target": target,
                    "target_id": target_id,
                    "source_suffixes": template_suffixes,
                    "local_word_range": expected_range,
                }
            )
            target_word_offset += word_count
        if target_word_offset != stage_word_count:
            raise BoardWeightImageError(f"{stage_id}: storage targets do not cover the complete canonical stage stream")
        required_hashes = layout.get("required_tensor_hashes")
        if not isinstance(required_hashes, list) or sorted(required_hashes) != sorted(stage_template_hashes):
            raise BoardWeightImageError(f"{stage_id}: required_tensor_hashes differs from canonical target sources")
        required_tensors = stage.get("required_tensors")
        if not isinstance(required_tensors, list):
            raise BoardWeightImageError(f"{stage_id}: required_tensors is not a list")
        required_by_suffix: dict[str, dict[str, Any]] = {}
        for index, required in enumerate(required_tensors):
            if not isinstance(required, dict):
                raise BoardWeightImageError(f"{stage_id}: required_tensors[{index}] is not an object")
            suffix = str(required.get("parameter_suffix") or "")
            if not suffix or suffix in required_by_suffix:
                raise BoardWeightImageError(f"{stage_id}: required tensor suffixes must be non-empty and unique")
            required_by_suffix[suffix] = required
        if sorted(required_by_suffix) != sorted(stage_suffixes):
            raise BoardWeightImageError(f"{stage_id}: required_tensors differs from canonical target suffixes")
        template_by_suffix = {
            str(source["parameter_suffix"]): source
            for target in target_rows
            for source in target.get("source_tensors", [])
        }
        for suffix, required in required_by_suffix.items():
            template = template_by_suffix[suffix]
            if (
                _hash(required.get("sha256"), f"{stage_id}/{suffix}.required_tensor.sha256")
                != _hash(template.get("sha256"), f"{stage_id}/{suffix}.template.sha256")
                or list(required.get("shape") or []) != list(template.get("shape") or [])
            ):
                raise BoardWeightImageError(f"{stage_id}/{suffix}: required tensor differs from canonical source")
        stage_descriptors.append(
            {
                "stage_index": stage_index,
                "stage_id": stage_id,
                "op": op,
                "layout": layout,
                "layout_contract_sha256": layout_hash,
                "word_count": stage_word_count,
                "layer_word_range": _range(local_word_offset, stage_word_count),
                "targets": target_descriptors,
            }
        )
        local_word_offset += stage_word_count

    if sorted(covered_suffixes) != suffixes or len(covered_suffixes) != len(suffixes):
        raise BoardWeightImageError(
            "canonical stage layouts do not cover every catalog suffix exactly once: "
            f"covered={sorted(covered_suffixes)} catalog={suffixes}"
        )
    connected_word_count = _integer(connected.get("word_count"), "connected weight stream word_count")
    if connected_word_count != local_word_offset:
        raise BoardWeightImageError(
            f"canonical stage word count {local_word_offset} != connected weight stream word count {connected_word_count}"
        )
    if connected.get("stage_order") != [row["stage_id"] for row in stage_descriptors]:
        raise BoardWeightImageError("connected weight stream stage_order differs from canonical stage requirements")
    connected_segments = connected.get("stage_segments")
    if not isinstance(connected_segments, list) or len(connected_segments) != len(stage_descriptors):
        raise BoardWeightImageError("connected weight stream stage_segments is incomplete")
    for descriptor, segment in zip(stage_descriptors, connected_segments):
        if not isinstance(segment, dict) or (
            segment.get("stage_index") != descriptor["stage_index"]
            or segment.get("stage_id") != descriptor["stage_id"]
            or segment.get("op") != descriptor["op"]
            or segment.get("layout_contract_sha256") != descriptor["layout_contract_sha256"]
            or segment.get("global_stream_range") != descriptor["layer_word_range"]
        ):
            raise BoardWeightImageError(f"{descriptor['stage_id']}: connected stream segment differs from layout")

    layout_set_hash = sha256_json({"stage_weight_layout_contract_sha256s": layout_hashes})
    return stage_descriptors, local_word_offset, connected_hash, layout_hashes, layout_set_hash


def _validate_plan(
    document: _Document,
    *,
    catalog_sha256: str,
    checkpoint_sha256: str,
    connected_sha256: str,
    layout_hashes: list[str],
    layout_set_sha256: str,
    layer_ids: list[int],
    canonical_layer_bytes: int,
) -> tuple[int, int, list[int]]:
    plan = document.value
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION or plan.get("status") != "pass":
        raise BoardWeightImageError(f"board workload image plan must be pass {PLAN_SCHEMA_VERSION}")
    identity = plan.get("input_identity")
    image = plan.get("image")
    memory = plan.get("memory")
    if not isinstance(identity, dict) or not isinstance(image, dict) or not isinstance(memory, dict):
        raise BoardWeightImageError("board workload image plan input_identity/image/memory objects are required")
    expected_identity = {
        "transformer_block_weight_catalog_sha256": catalog_sha256,
        "source_checkpoint_sha256": checkpoint_sha256,
        "connected_weight_stream_contract_sha256": connected_sha256,
        "stage_weight_layout_contract_sha256s": layout_hashes,
    }
    for key, expected in expected_identity.items():
        if identity.get(key) != expected:
            raise BoardWeightImageError(f"board workload image plan input_identity.{key} mismatch")
    optional_layout_set = identity.get("canonical_weight_layout_set_sha256")
    if optional_layout_set is not None and optional_layout_set != layout_set_sha256:
        raise BoardWeightImageError("board workload image plan canonical layout-set identity mismatch")

    if image.get("format") != IMAGE_FORMAT or image.get("word_bits") != 32 or image.get("byte_order") != "little":
        raise BoardWeightImageError("board workload image plan must request little-endian u32 binary")
    try:
        scope = validation_scope_from_plan(
            plan,
            model_layer_count=len(layer_ids),
        )
    except BoardValidationScopeError as exc:
        raise BoardWeightImageError(str(exc)) from exc
    selected_layer_ids = list(scope.layer_indices)
    alignment = _integer(image.get("layer_alignment_bytes"), "plan.image.layer_alignment_bytes", minimum=4)
    if alignment & (alignment - 1) or alignment % 4:
        raise BoardWeightImageError("plan.image.layer_alignment_bytes must be a power of two divisible by four")
    if plan.get("target_layer_count") is not None and plan.get("target_layer_count") != len(selected_layer_ids):
        raise BoardWeightImageError("board workload image plan target_layer_count differs from validation scope")

    if memory.get("weight_bank_count") != 2:
        raise BoardWeightImageError("board workload image plan must declare exactly two weight banks")
    bank_capacity = _integer(
        memory.get("weight_bank_capacity_bytes"),
        "plan.memory.weight_bank_capacity_bytes",
        minimum=4,
    )
    if bank_capacity % 4:
        raise BoardWeightImageError("weight_bank_capacity_bytes must be divisible by four")
    padded_layer_bytes = _align_up(canonical_layer_bytes, alignment)
    if padded_layer_bytes > bank_capacity:
        raise BoardWeightImageError(
            "canonical layer weight payload exceeds weight bank capacity: "
            f"required={padded_layer_bytes} capacity={bank_capacity} shortfall={padded_layer_bytes - bank_capacity} bytes"
        )
    return alignment, bank_capacity, selected_layer_ids


class _SafetensorReader:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._streams: dict[Path, BinaryIO] = {}
        identities: dict[Path, str] = {}
        for row in rows:
            path = row["_source_path"]
            declared = row["source_file_sha256"]
            if path in identities and identities[path] != declared:
                raise BoardWeightImageError(f"conflicting source shard identity: {path}")
            identities[path] = declared
        self.source_files: list[dict[str, Any]] = []
        for path in sorted(identities, key=lambda item: str(item)):
            if not path.is_file():
                raise BoardWeightImageError(f"source safetensors shard is missing: {path}")
            actual = sha256_file(path)
            if actual != identities[path]:
                raise BoardWeightImageError(f"source shard hash mismatch: {path}")
            self.source_files.append({"path": str(path), "sha256": actual, "size_bytes": path.stat().st_size})

    def tensor(self, row: dict[str, Any]) -> Any:
        import torch

        path: Path = row["_source_path"]
        stream = self._streams.get(path)
        if stream is None:
            stream = path.open("rb")
            self._streams[path] = stream
        start, end = row["data_offsets"]
        stream.seek(int(row["source_data_base"]) + start)
        raw = stream.read(end - start)
        if len(raw) != end - start:
            raise BoardWeightImageError(f"short safetensors slice read: {row['name']}")
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != row["source_slice_sha256"]:
            raise BoardWeightImageError(f"source tensor slice hash mismatch: {row['name']}")
        dtype = {
            "BF16": torch.bfloat16,
            "F16": torch.float16,
            "F32": torch.float32,
        }[row["dtype"]]
        try:
            value = torch.frombuffer(bytearray(raw), dtype=dtype).clone().reshape(row["shape"])
        except (RuntimeError, ValueError) as exc:
            raise BoardWeightImageError(f"cannot decode safetensors slice {row['name']}: {exc}") from exc
        return value

    def close(self) -> None:
        for stream in self._streams.values():
            stream.close()
        self._streams.clear()

    def __enter__(self) -> _SafetensorReader:
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def _packed_u32_bytes(value: Any, storage_dtype: str) -> bytes:
    import numpy as np
    import torch

    contiguous = value.detach().cpu().contiguous()
    if storage_dtype == "fp16":
        bits = contiguous.to(torch.float16).view(torch.int16).reshape(-1).numpy().view(np.uint16)
        if bits.size % 2:
            raise BoardWeightImageError("fp16 canonical target has an odd scalar count")
        packed = bits[0::2].astype(np.uint32) | (bits[1::2].astype(np.uint32) << np.uint32(16))
        return packed.astype("<u4", copy=False).tobytes(order="C")
    if storage_dtype == "fp32":
        bits = contiguous.to(torch.float32).view(torch.int32).reshape(-1).numpy().view(np.uint32)
        return bits.astype("<u4", copy=False).tobytes(order="C")
    raise BoardWeightImageError(f"unsupported canonical storage dtype: {storage_dtype}")


def _target_bytes(
    target: dict[str, Any],
    source_rows: list[dict[str, Any]],
    reader: _SafetensorReader,
) -> bytes:
    import torch

    conversion = target.get("value_conversion")
    if not isinstance(conversion, dict):
        raise BoardWeightImageError(f"{target.get('target_id')}: value_conversion is missing")
    source_dtype = str(conversion.get("source_dtype") or "")
    if source_dtype not in {"fp16", "fp32"}:
        raise BoardWeightImageError(f"{target.get('target_id')}: unsupported conversion source dtype")
    torch_source_dtype = torch.float16 if source_dtype == "fp16" else torch.float32
    tensors = [reader.tensor(row).to(torch_source_dtype) for row in source_rows]
    compose = target["compose"]
    if compose.get("kind") == "identity":
        value = tensors[0]
    else:
        value = torch.cat(tensors, dim=0)
    logical_shape = [int(item) for item in target.get("logical_shape", [])]
    if list(value.shape) != logical_shape:
        raise BoardWeightImageError(
            f"{target.get('target_id')}: composed shape {list(value.shape)} != logical_shape {logical_shape}"
        )
    storage_dtype = str(target.get("storage_scalar_dtype") or "")
    value = value.to(torch.float16 if storage_dtype == "fp16" else torch.float32)
    if target.get("target_kind") == "linear_weight_matrix":
        if len(logical_shape) != 2:
            raise BoardWeightImageError(f"{target.get('target_id')}: linear matrix logical shape must have rank two")
        tile = target.get("tile")
        if not isinstance(tile, dict):
            raise BoardWeightImageError(f"{target.get('target_id')}: matrix tile contract is missing")
        out_features, in_features = logical_shape
        out_lanes = _integer(tile.get("out_lanes"), f"{target.get('target_id')}.tile.out_lanes", minimum=1)
        in_lanes = _integer(tile.get("in_lanes"), f"{target.get('target_id')}.tile.in_lanes", minimum=1)
        if out_features % out_lanes or in_features % in_lanes:
            raise BoardWeightImageError(f"{target.get('target_id')}: logical matrix does not divide canonical tile")
        value = value.reshape(
            out_features // out_lanes,
            out_lanes,
            in_features // in_lanes,
            in_lanes,
        ).permute(0, 2, 1, 3).contiguous()
    elif len(logical_shape) != 1:
        raise BoardWeightImageError(f"{target.get('target_id')}: unsupported non-vector canonical target kind")
    return _packed_u32_bytes(value.reshape(-1), storage_dtype)


def _write_bytes(
    output: BinaryIO,
    value: bytes,
    *digests: Any,
) -> None:
    output.write(value)
    for digest in digests:
        digest.update(value)


def _write_zero_padding(output: BinaryIO, count: int, *digests: Any) -> None:
    remaining = count
    zero_chunk = b"\x00" * min(1024 * 1024, max(1, count))
    while remaining:
        chunk = zero_chunk[: min(len(zero_chunk), remaining)]
        _write_bytes(output, chunk, *digests)
        remaining -= len(chunk)


def materialize_board_weight_image(
    transformer_catalog: dict[str, Any] | str | Path,
    weight_requirements: dict[str, Any] | str | Path,
    board_workload_image_plan: dict[str, Any] | str | Path,
    image_path: str | Path,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Pack every Transformer-block layer into one hash-bound little-endian image."""

    catalog_document = _load_document(transformer_catalog, "Transformer-block weight catalog")
    requirements_document = _load_document(weight_requirements, "DUT weight binding requirements")
    plan_document = _load_document(board_workload_image_plan, "board workload image plan")
    catalog = catalog_document.value
    layer_ids, suffixes, catalog_by_key, normalized_rows = _validate_catalog(catalog_document)
    stages, canonical_layer_words, connected_hash, layout_hashes, layout_set_hash = _validate_layouts(
        requirements_document,
        catalog_document,
        catalog,
        layer_ids,
        suffixes,
        catalog_by_key,
    )
    checkpoint_hash = _hash(catalog.get("source_checkpoint_sha256"), "catalog.source_checkpoint_sha256")
    canonical_layer_bytes = canonical_layer_words * 4
    alignment, bank_capacity, selected_layer_ids = _validate_plan(
        plan_document,
        catalog_sha256=catalog_document.identity_sha256,
        checkpoint_sha256=checkpoint_hash,
        connected_sha256=connected_hash,
        layout_hashes=layout_hashes,
        layout_set_sha256=layout_set_hash,
        layer_ids=layer_ids,
        canonical_layer_bytes=canonical_layer_bytes,
    )

    final_image = Path(image_path).expanduser().resolve()
    final_manifest = (
        Path(manifest_path).expanduser().resolve()
        if manifest_path is not None
        else final_image.parent / "full_weight_image_manifest.json"
    )
    if final_image == final_manifest:
        raise BoardWeightImageError("image_path and manifest_path must differ")
    selected_rows = [
        row for row in normalized_rows if row["layer_index"] in selected_layer_ids
    ]
    source_paths = {row["_source_path"] for row in selected_rows}
    if final_image in source_paths or final_manifest in source_paths:
        raise BoardWeightImageError("output paths must not replace a source checkpoint shard")
    final_image.parent.mkdir(parents=True, exist_ok=True)
    final_manifest.parent.mkdir(parents=True, exist_ok=True)
    token = f"{os.getpid()}.{uuid.uuid4().hex}"
    temporary_image = final_image.with_name(f".{final_image.name}.{token}.tmp")
    temporary_manifest = final_manifest.with_name(f".{final_manifest.name}.{token}.tmp")
    image_preexisted = final_image.exists()
    image_committed = False

    try:
        with _SafetensorReader(selected_rows) as reader:
            image_digest = hashlib.sha256()
            layer_segments: list[dict[str, Any]] = []
            packed_tensor_hashes: list[str] = []
            packed_tensor_keys: list[tuple[int, str]] = []
            image_byte_offset = 0
            with temporary_image.open("wb") as output:
                for layer_index in selected_layer_ids:
                    if image_byte_offset % alignment:
                        raise BoardWeightImageError("internal layer alignment invariant failed")
                    layer_start = image_byte_offset
                    layer_digest = hashlib.sha256()
                    payload_digest = hashlib.sha256()
                    layer_tensor_hashes: list[str] = []
                    stage_segments: list[dict[str, Any]] = []
                    layer_word_offset = 0
                    for stage in stages:
                        stage_start = image_byte_offset
                        stage_digest = hashlib.sha256()
                        target_segments: list[dict[str, Any]] = []
                        stage_hashes: list[str] = []
                        stage_word_offset = 0
                        for target_descriptor in stage["targets"]:
                            target = target_descriptor["target"]
                            target_start = image_byte_offset
                            source_rows = [
                                catalog_by_key[(layer_index, suffix)]
                                for suffix in target_descriptor["source_suffixes"]
                            ]
                            for template, row in zip(target["source_tensors"], source_rows):
                                if list(template.get("shape") or []) != row["shape"]:
                                    raise BoardWeightImageError(
                                        f"layer {layer_index}/{target_descriptor['target_id']}/{row['parameter_suffix']}: "
                                        "catalog shape differs from canonical template"
                                    )
                            packed = _target_bytes(target, source_rows, reader)
                            expected_words = target_descriptor["local_word_range"]["word_count"]
                            if len(packed) != expected_words * 4:
                                raise BoardWeightImageError(
                                    f"layer {layer_index}/{stage['stage_id']}/{target_descriptor['target_id']}: "
                                    f"packed word count {len(packed) // 4} != canonical {expected_words}"
                                )
                            _write_bytes(output, packed, image_digest, layer_digest, payload_digest, stage_digest)
                            image_byte_offset += len(packed)
                            hashes = [row["source_slice_sha256"] for row in source_rows]
                            stage_hashes.extend(hashes)
                            layer_tensor_hashes.extend(hashes)
                            packed_tensor_hashes.extend(hashes)
                            packed_tensor_keys.extend((layer_index, row["parameter_suffix"]) for row in source_rows)
                            target_segments.append(
                                {
                                    "target_id": target_descriptor["target_id"],
                                    "target_kind": target.get("target_kind"),
                                    "dut_port_role": target.get("dut_port_role"),
                                    "storage_scalar_dtype": target.get("storage_scalar_dtype"),
                                    "storage_scalar_bits": target.get("storage_scalar_bits"),
                                    **_byte_range(target_start, len(packed)),
                                    **_range(target_start // 4, expected_words),
                                    "layer_word_offset": layer_word_offset + stage_word_offset,
                                    "stage_word_offset": stage_word_offset,
                                    "sha256": hashlib.sha256(packed).hexdigest(),
                                    "tensor_hashes": hashes,
                                    "source_tensors": [
                                        {
                                            "tensor": row["name"],
                                            "layer_index": layer_index,
                                            "parameter_suffix": row["parameter_suffix"],
                                            "dtype": row["dtype"],
                                            "shape": row["shape"],
                                            "source_slice_sha256": row["source_slice_sha256"],
                                        }
                                        for row in source_rows
                                    ],
                                }
                            )
                            stage_word_offset += expected_words
                        if stage_word_offset != stage["word_count"]:
                            raise BoardWeightImageError(f"layer {layer_index}/{stage['stage_id']}: canonical word count mismatch")
                        stage_segments.append(
                            {
                                "stage_index": stage["stage_index"],
                                "stage_id": stage["stage_id"],
                                "op": stage["op"],
                                "weight_layout_contract_sha256": stage["layout_contract_sha256"],
                                **_byte_range(stage_start, stage_word_offset * 4),
                                **_range(stage_start // 4, stage_word_offset),
                                "layer_word_offset": layer_word_offset,
                                "sha256": stage_digest.hexdigest(),
                                "tensor_hashes": stage_hashes,
                                "target_segments": target_segments,
                            }
                        )
                        layer_word_offset += stage_word_offset
                    if layer_word_offset != canonical_layer_words:
                        raise BoardWeightImageError(
                            f"layer {layer_index}: packed words {layer_word_offset} != canonical {canonical_layer_words}"
                        )
                    payload_bytes = image_byte_offset - layer_start
                    if payload_bytes != canonical_layer_bytes:
                        raise BoardWeightImageError(f"layer {layer_index}: canonical payload byte count mismatch")
                    segment_bytes = _align_up(payload_bytes, alignment)
                    padding_bytes = segment_bytes - payload_bytes
                    _write_zero_padding(output, padding_bytes, image_digest, layer_digest)
                    image_byte_offset += padding_bytes
                    layer_segments.append(
                        {
                            "layer_index": layer_index,
                            **_byte_range(layer_start, segment_bytes),
                            **_range(layer_start // 4, segment_bytes // 4),
                            "payload_byte_count": payload_bytes,
                            "payload_word_count": canonical_layer_words,
                            "padding_byte_count": padding_bytes,
                            "payload_sha256": payload_digest.hexdigest(),
                            "sha256": layer_digest.hexdigest(),
                            "tensor_hashes": layer_tensor_hashes,
                            "stage_segments": stage_segments,
                        }
                    )
                output.flush()
                os.fsync(output.fileno())

            expected_keys = {
                (layer, suffix) for layer in selected_layer_ids for suffix in suffixes
            }
            if len(packed_tensor_keys) != len(expected_keys) or set(packed_tensor_keys) != expected_keys:
                raise BoardWeightImageError("packed image does not cover every catalog layer/suffix exactly once")
            if temporary_image.stat().st_size != image_byte_offset:
                raise BoardWeightImageError("temporary image size differs from streamed byte count")
            image_hash = image_digest.hexdigest()
            if sha256_file(temporary_image) != image_hash:
                raise BoardWeightImageError("temporary image hash differs from streamed image hash")

            canonical_stage_layouts = [
                {
                    "stage_index": stage["stage_index"],
                    "stage_id": stage["stage_id"],
                    "op": stage["op"],
                    "weight_layout_contract_sha256": stage["layout_contract_sha256"],
                    **stage["layer_word_range"],
                }
                for stage in stages
            ]
            manifest: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "status": "pass",
                "accelerator_scope": "transformer_blocks_only",
                "scope_coverage_complete": True,
                "scope_coverage_complete": True,
                "all_target_layers": len(selected_layer_ids) == len(layer_ids),
                "model_layer_count": len(layer_ids),
                "target_layer_count": len(selected_layer_ids),
                "bound_layer_count": len(selected_layer_ids),
                "validation_layer_indices": selected_layer_ids,
                "layer_order": selected_layer_ids,
                "source_checkpoint_sha256": checkpoint_hash,
                "accelerator_weight_catalog_sha256": catalog_document.identity_sha256,
                "accelerator_weight_catalog_canonical_sha256": catalog_document.canonical_sha256,
                "dut_weight_binding_requirements_sha256": requirements_document.identity_sha256,
                "dut_weight_binding_requirements_canonical_sha256": requirements_document.canonical_sha256,
                "board_workload_image_plan_sha256": plan_document.canonical_sha256,
                **(
                    {"board_workload_image_plan_file_sha256": plan_document.file_sha256}
                    if plan_document.file_sha256 is not None
                    else {}
                ),
                "connected_weight_stream_contract_sha256": connected_hash,
                "stage_weight_layout_contract_sha256s": layout_hashes,
                "canonical_weight_layout_set_sha256": layout_set_hash,
                "canonical_stage_layouts": canonical_stage_layouts,
                "canonical_layer_word_count": canonical_layer_words,
                "canonical_layer_byte_count": canonical_layer_bytes,
                "word_bits": 32,
                "byte_order": "little",
                "image_format": IMAGE_FORMAT,
                "layer_alignment_bytes": alignment,
                "weight_bank_count": 2,
                "weight_bank_capacity_bytes": bank_capacity,
                "path": str(final_image),
                "sha256": image_hash,
                "image_sha256": image_hash,
                "byte_count": image_byte_offset,
                "total_bytes": image_byte_offset,
                "word_count": image_byte_offset // 4,
                "packed_tensor_count": len(packed_tensor_hashes),
                "packed_tensor_hashes": packed_tensor_hashes,
                "source_checkpoint_files": reader.source_files,
                "layer_segments": layer_segments,
                "padding_policy": {
                    "placement": "zero bytes after each canonical layer payload",
                    "alignment_bytes": alignment,
                    "padding_value": 0,
                    "padding_is_not_sent_to_canonical_weight_loader": True,
                },
                "image": {
                    "path": str(final_image),
                    "sha256": image_hash,
                    "format": IMAGE_FORMAT,
                    "word_bits": 32,
                    "byte_order": "little",
                    "byte_count": image_byte_offset,
                    "total_bytes": image_byte_offset,
                    "word_count": image_byte_offset // 4,
                },
                "manifest_path": str(final_manifest),
            }
            manifest["manifest_contract_sha256"] = sha256_json(manifest)
            temporary_manifest.write_text(
                json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
            with temporary_manifest.open("rb") as stream:
                os.fsync(stream.fileno())

        os.replace(temporary_image, final_image)
        image_committed = True
        os.replace(temporary_manifest, final_manifest)
        return manifest
    except Exception:
        temporary_image.unlink(missing_ok=True)
        temporary_manifest.unlink(missing_ok=True)
        if image_committed and not image_preexisted:
            final_image.unlink(missing_ok=True)
        raise


__all__ = [
    "BoardWeightImageError",
    "IMAGE_FORMAT",
    "PLAN_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "materialize_board_weight_image",
]
