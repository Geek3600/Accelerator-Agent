"""Materialize full-layer runtime inputs for an exact board simulation.

Runtime tensors are captured from real target-model invocations.  This module
packs those tensors according to adapter and connected-kernel contracts, then
deduplicates only byte-identical per-layer streams.  It makes no assumption
that runtime values are shared across Transformer layers.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import struct
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from accagent.framework.semantic_runtime import (
    COMPOSITE_STREAM_SCHEMA_VERSION,
    SCHEMA_VERSION as SEMANTIC_RUNTIME_SCHEMA_VERSION,
    logical_shape_and_axes,
    tensor_sha256,
    tensor_u32_words,
)
from accagent.framework.board_validation_scope import (
    BoardValidationScopeError,
    PREFIX_MODEL_MODE,
    resolve_board_validation_scope,
)


CAPTURE_SCHEMA_VERSION = "spatialaccagent.layer_runtime_capture_contract.v1"
MANIFEST_SCHEMA_VERSION = "spatialaccagent.board_runtime_image_manifest.v1"
IMAGE_FORMAT = "u32le_binary"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


LAYER_RUNTIME_CAPTURE_CONTRACT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "schema_version": {"type": "string", "enum": [CAPTURE_SCHEMA_VERSION]},
        "status": {"type": "string", "enum": ["pass"]},
        "accelerator_scope": {"type": "string", "enum": ["transformer_blocks_only"]},
        "target_layer_count": {"type": "integer"},
        "source_reference_manifest_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "semantic_adapter_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "semantic_runtime_contract_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "connected_runtime_stream_contract_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "layers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "layer_index": {"type": "integer"},
                    "stage_invocations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "stage_id": {"type": "string"},
                                "consumer_op": {"type": "string"},
                                "sources": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "properties": {
                                            "source_key": {"type": "string"},
                                            "path": {"type": "string"},
                                            "file_sha256": {
                                                "type": "string",
                                                "pattern": "^[0-9a-f]{64}$",
                                            },
                                            "tensor_sha256": {
                                                "type": "string",
                                                "pattern": "^[0-9a-f]{64}$",
                                            },
                                            "dtype": {"type": "string"},
                                            "shape": {
                                                "type": "array",
                                                "items": {"type": "integer"},
                                            },
                                            "capture_path": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            },
                                        },
                                        "required": [
                                            "source_key",
                                            "path",
                                            "file_sha256",
                                            "tensor_sha256",
                                            "dtype",
                                            "shape",
                                        ],
                                    },
                                },
                            },
                            "required": ["stage_id", "consumer_op", "sources"],
                        },
                    },
                },
                "required": ["layer_index", "stage_invocations"],
            },
        },
        "capture_provenance": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "inference_count": {"type": "integer", "enum": [1]},
                "model_snapshot": {"type": "string"},
                "model_architecture": {"type": "string"},
                "source_checkpoint_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "source_input_file_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "source_input_tensor_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "expected_final_decoder_output_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "observed_final_decoder_output_sha256": {
                    "type": "string",
                    "pattern": "^[0-9a-f]{64}$",
                },
                "reference_output_verified": {"type": "boolean", "enum": [True]},
                "decoder_layer_container": {"type": "string"},
                "decoder_layer_class": {"type": "string"},
                "capture_path_learning": {
                    "type": "string",
                    "enum": ["first_layer_reference_identity_match"],
                },
                "capture_match_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "keyword_matching_used": {"type": "boolean", "enum": [False]},
            },
            "required": [
                "inference_count",
                "model_snapshot",
                "model_architecture",
                "source_checkpoint_sha256",
                "source_input_file_sha256",
                "source_input_tensor_sha256",
                "expected_final_decoder_output_sha256",
                "observed_final_decoder_output_sha256",
                "reference_output_verified",
                "decoder_layer_container",
                "decoder_layer_class",
                "capture_path_learning",
                "capture_match_fields",
                "keyword_matching_used",
            ],
        },
        "contract_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
        "path": {"type": "string"},
        "file_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
    },
    "required": [
        "schema_version",
        "status",
        "accelerator_scope",
        "target_layer_count",
        "source_reference_manifest_sha256",
        "semantic_adapter_sha256",
        "semantic_runtime_contract_sha256",
        "connected_runtime_stream_contract_sha256",
        "layers",
        "contract_sha256",
    ],
}


class BoardRuntimeImageError(RuntimeError):
    """Raised when a complete board runtime image cannot be proven."""


@dataclass(frozen=True)
class _Document:
    value: dict[str, Any]
    canonical_sha256: str
    identity_sha256: str
    base_dir: Path
    path: Path | None
    file_sha256: str | None


@dataclass
class _PreparedLayer:
    layer_index: int
    payload: bytes
    sha256: str
    stage_bindings: list[dict[str, Any]]
    source_files: list[dict[str, Any]]


def sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_document(value: dict[str, Any] | str | Path, label: str) -> _Document:
    path: Path | None = None
    file_hash: str | None = None
    if isinstance(value, dict):
        document = value
        base_dir = Path.cwd().resolve()
    elif isinstance(value, (str, Path)):
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            raise BoardRuntimeImageError(f"{label} file is missing: {path}")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BoardRuntimeImageError(f"cannot read {label}: {path}: {exc}") from exc
        if not isinstance(document, dict):
            raise BoardRuntimeImageError(f"{label} must be a JSON object: {path}")
        base_dir = path.parent
        file_hash = sha256_file(path)
    else:
        raise BoardRuntimeImageError(f"{label} must be a JSON object or path")
    canonical_hash = sha256_json(document)
    return _Document(
        value=document,
        canonical_sha256=canonical_hash,
        identity_sha256=file_hash or canonical_hash,
        base_dir=base_dir,
        path=path,
        file_sha256=file_hash,
    )


def _rows(value: Any) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _schema_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
    }.get(expected, True)


def _validate_schema_shape(
    value: Any,
    schema: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
        errors.append(f"{label} has the wrong JSON type")
        return
    if "enum" in schema and value not in schema.get("enum", []):
        errors.append(f"{label} is not an allowed value")
    pattern = schema.get("pattern")
    if (
        isinstance(pattern, str)
        and isinstance(value, str)
        and re.fullmatch(pattern, value) is None
    ):
        errors.append(f"{label} does not match the required pattern")
    if isinstance(value, dict):
        properties = (
            schema.get("properties")
            if isinstance(schema.get("properties"), dict)
            else {}
        )
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{label}.{key} is required")
        if schema.get("additionalProperties") is False:
            for key in sorted(set(value) - set(properties)):
                errors.append(f"{label}.{key} is not an allowed field")
        for key, child_schema in properties.items():
            if key in value and isinstance(child_schema, dict):
                _validate_schema_shape(
                    value[key], child_schema, f"{label}.{key}", errors
                )
    elif isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_schema_shape(item, item_schema, f"{label}[{index}]", errors)


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BoardRuntimeImageError(f"{label} must be an integer >= {minimum}")
    return value


def _sha256(value: Any, label: str) -> str:
    normalized = str(value or "").lower()
    if SHA256_PATTERN.fullmatch(normalized) is None:
        raise BoardRuntimeImageError(f"{label} is not a SHA-256 digest")
    return normalized


def _contract_sha256(
    value: dict[str, Any],
    label: str,
    *,
    excluded_fields: set[str] | None = None,
) -> str:
    declared = _sha256(value.get("contract_sha256"), f"{label}.contract_sha256")
    excluded = {"contract_sha256", *(excluded_fields or set())}
    payload = {key: item for key, item in value.items() if key not in excluded}
    if sha256_json(payload) != declared:
        raise BoardRuntimeImageError(f"{label} contract hash mismatch")
    return declared


def _resolve_source_path(raw: Any, base_dir: Path, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise BoardRuntimeImageError(f"{label}.path is missing")
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else base_dir / path).resolve()


def _strict_memh_identity(stream: dict[str, Any], label: str) -> tuple[Path, int, str]:
    if stream.get("word_bits") != 32:
        raise BoardRuntimeImageError(f"{label}.word_bits must be 32")
    word_count = _integer(stream.get("word_count"), f"{label}.word_count")
    declared_hash = _sha256(stream.get("sha256"), f"{label}.sha256")
    path = Path(str(stream.get("path") or "")).expanduser().resolve()
    if not path.is_file():
        raise BoardRuntimeImageError(f"{label} file is missing: {path}")
    digest = hashlib.sha256()
    actual_count = 0
    with path.open("rb") as source:
        for line in source:
            digest.update(line)
            if re.fullmatch(rb"[0-9A-Fa-f]{8}\n", line) is None:
                raise BoardRuntimeImageError(f"{label} is not strict u32 memh")
            actual_count += 1
    if digest.hexdigest() != declared_hash or actual_count != word_count:
        raise BoardRuntimeImageError(f"{label} file hash/count mismatch")
    return path, word_count, declared_hash


def _validate_semantic_authority(
    adapter_document: _Document,
    runtime_document: _Document,
) -> dict[str, dict[str, Any]]:
    adapter = adapter_document.value
    runtime = runtime_document.value
    if adapter.get("accelerator_scope") != "transformer_blocks_only":
        raise BoardRuntimeImageError("semantic adapter scope must be transformer_blocks_only")
    stream_specs = adapter.get("semantic_runtime_streams")
    if not isinstance(stream_specs, dict):
        raise BoardRuntimeImageError("semantic adapter runtime stream map is missing")
    if runtime.get("schema_version") != SEMANTIC_RUNTIME_SCHEMA_VERSION:
        raise BoardRuntimeImageError("semantic runtime contract schema is unsupported")
    if runtime.get("status") != "pass" or runtime.get("blockers") not in ([], None):
        raise BoardRuntimeImageError("semantic runtime contract is not pass")
    _contract_sha256(
        runtime,
        "semantic runtime",
        excluded_fields={"path", "file_sha256"},
    )
    if runtime.get("model_semantic_adapter_sha256") != adapter_document.identity_sha256:
        raise BoardRuntimeImageError("semantic runtime contract does not bind the adapter")
    streams: dict[str, dict[str, Any]] = {}
    for index, stream in enumerate(_rows(runtime.get("streams"))):
        consumer_op = str(stream.get("consumer_op") or "")
        if not consumer_op or consumer_op in streams:
            raise BoardRuntimeImageError(
                f"semantic runtime stream[{index}] consumer_op is empty or duplicated"
            )
        _contract_sha256(stream, f"semantic runtime stream {consumer_op}")
        stream_file = stream.get("stream")
        if not isinstance(stream_file, dict):
            raise BoardRuntimeImageError(f"semantic runtime stream {consumer_op} has no stream")
        _strict_memh_identity(stream_file, f"semantic runtime stream {consumer_op}")
        spec = stream_specs.get(consumer_op)
        if not isinstance(spec, dict):
            raise BoardRuntimeImageError(
                f"semantic runtime stream {consumer_op} is absent from the adapter"
            )
        source_order = [str(value) for value in spec.get("source_order", [])]
        target_specs = spec.get("targets")
        if (
            not isinstance(target_specs, dict)
            or not source_order
            or len(source_order) != len(set(source_order))
            or set(source_order) != set(target_specs)
            or stream.get("source_order") != source_order
        ):
            raise BoardRuntimeImageError(
                f"semantic runtime stream {consumer_op} source/target coverage is invalid"
            )
        targets = _rows(stream.get("targets"))
        if [str(row.get("source_key") or "") for row in targets] != source_order:
            raise BoardRuntimeImageError(
                f"semantic runtime stream {consumer_op} target order differs from adapter"
            )
        streams[consumer_op] = stream
    if set(streams) != set(stream_specs):
        raise BoardRuntimeImageError(
            "semantic runtime contract does not cover every adapter runtime stream"
        )
    return streams


def _validate_connected_contract(
    document: _Document,
    semantic_streams: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, str]:
    connected = document.value
    if connected.get("schema_version") != COMPOSITE_STREAM_SCHEMA_VERSION:
        raise BoardRuntimeImageError("connected runtime stream schema is unsupported")
    if connected.get("status") != "pass" or connected.get("word_bits") != 32:
        raise BoardRuntimeImageError("connected runtime stream is not pass u32")
    contract_hash = _contract_sha256(
        connected,
        "connected runtime stream",
        excluded_fields={"path"},
    )
    stream_path, word_count, stream_hash = _strict_memh_identity(
        connected, "connected runtime stream"
    )
    del stream_path
    if connected.get("sha256") != stream_hash:
        raise BoardRuntimeImageError("connected runtime stream hash is inconsistent")
    stage_order = [str(value) for value in connected.get("stage_order", [])]
    stages = _rows(connected.get("stage_segments"))
    if (
        not stage_order
        or len(stage_order) != len(set(stage_order))
        or [str(row.get("stage_id") or "") for row in stages] != stage_order
    ):
        raise BoardRuntimeImageError("connected runtime stage order/coverage is invalid")
    nonempty: list[dict[str, Any]] = []
    expected_global_offset = 0
    for stage_index, stage in enumerate(stages):
        stage_id = str(stage.get("stage_id") or "")
        op = str(stage.get("op") or "")
        global_range = stage.get("global_stream_range")
        if not isinstance(global_range, dict):
            raise BoardRuntimeImageError(f"{stage_id}: connected global range is missing")
        count = _integer(global_range.get("word_count"), f"{stage_id}.word_count")
        expected_range = {
            "word_offset": expected_global_offset,
            "word_count": count,
            "word_end_exclusive": expected_global_offset + count,
        }
        if (
            stage.get("stage_index") != stage_index
            or not stage_id
            or not op
            or global_range != expected_range
        ):
            raise BoardRuntimeImageError(f"{stage_id}: connected stage identity/range is invalid")
        targets = _rows(stage.get("targets"))
        if count == 0:
            if stage.get("runtime_contract_sha256") not in ("", None) or targets:
                raise BoardRuntimeImageError(f"{stage_id}: empty runtime stage has runtime metadata")
        else:
            semantic = semantic_streams.get(op)
            if semantic is None:
                raise BoardRuntimeImageError(
                    f"{stage_id}: connected runtime op {op!r} has no semantic stream"
                )
            if stage.get("runtime_contract_sha256") != semantic.get("contract_sha256"):
                raise BoardRuntimeImageError(
                    f"{stage_id}: connected runtime contract differs from semantic stream"
                )
            semantic_stream = semantic.get("stream", {})
            if (
                stage.get("local_stream_sha256") != semantic_stream.get("sha256")
                or count != semantic_stream.get("word_count")
            ):
                raise BoardRuntimeImageError(
                    f"{stage_id}: connected local stream identity differs from semantic stream"
                )
            semantic_targets = _rows(semantic.get("targets"))
            if len(targets) != len(semantic_targets):
                raise BoardRuntimeImageError(f"{stage_id}: connected runtime targets are incomplete")
            for target, template in zip(targets, semantic_targets):
                local_range = target.get("local_stream_range")
                template_range = template.get("stream_range")
                expected_global_range = (
                    {
                        "word_offset": expected_global_offset
                        + int(template_range.get("word_offset") or 0),
                        "word_count": template_range.get("word_count"),
                        "word_end_exclusive": expected_global_offset
                        + int(template_range.get("word_end_exclusive") or 0),
                    }
                    if isinstance(template_range, dict)
                    else None
                )
                if (
                    target.get("target_id") != template.get("target_id")
                    or target.get("semantic_role") != template.get("semantic_role")
                    or local_range != template_range
                    or target.get("global_stream_range") != expected_global_range
                ):
                    raise BoardRuntimeImageError(
                        f"{stage_id}: connected target differs from semantic layout"
                    )
            nonempty.append(stage)
        expected_global_offset += count
    if expected_global_offset != word_count:
        raise BoardRuntimeImageError("connected runtime stages do not cover the stream")
    return stages, nonempty, word_count, contract_hash


def _load_tensor(
    row: dict[str, Any],
    base_dir: Path,
    label: str,
) -> tuple[Any, Path, dict[str, Any]]:
    import torch

    source_path = _resolve_source_path(row.get("path"), base_dir, label)
    if not source_path.is_file():
        raise BoardRuntimeImageError(f"{label} source tensor file is missing: {source_path}")
    file_hash = _sha256(row.get("file_sha256"), f"{label}.file_sha256")
    if sha256_file(source_path) != file_hash:
        raise BoardRuntimeImageError(f"{label} source tensor file hash mismatch")
    try:
        tensor = torch.load(source_path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise BoardRuntimeImageError(f"cannot load {label}: {exc}") from exc
    if not isinstance(tensor, torch.Tensor):
        raise BoardRuntimeImageError(f"{label} source is not a tensor")
    declared_tensor_hash = _sha256(row.get("tensor_sha256"), f"{label}.tensor_sha256")
    if tensor_sha256(tensor) != declared_tensor_hash:
        raise BoardRuntimeImageError(f"{label} tensor value hash mismatch")
    if row.get("dtype") != str(tensor.dtype) or row.get("shape") != list(tensor.shape):
        raise BoardRuntimeImageError(f"{label} tensor dtype/shape differs from capture")
    source_record = {
        "source_key": row.get("source_key"),
        "path": str(source_path),
        "file_sha256": file_hash,
        "tensor_sha256": declared_tensor_hash,
        "dtype": str(tensor.dtype),
        "shape": list(tensor.shape),
    }
    return tensor, source_path, source_record


def _pack_stage_invocation(
    invocation: dict[str, Any],
    stage: dict[str, Any],
    adapter: dict[str, Any],
    semantic_stream: dict[str, Any],
    capture_base_dir: Path,
) -> tuple[list[int], dict[str, Any], list[dict[str, Any]]]:
    stage_id = str(stage.get("stage_id") or "")
    consumer_op = str(stage.get("op") or "")
    label = f"layer invocation {stage_id}"
    if (
        invocation.get("stage_id") != stage_id
        or invocation.get("consumer_op") != consumer_op
    ):
        raise BoardRuntimeImageError(f"{label} identity differs from connected contract")
    stream_spec = adapter.get("semantic_runtime_streams", {}).get(consumer_op)
    if not isinstance(stream_spec, dict):
        raise BoardRuntimeImageError(f"{label} has no adapter stream specification")
    source_order = [str(value) for value in stream_spec.get("source_order", [])]
    source_rows = _rows(invocation.get("sources"))
    source_by_key: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(source_rows):
        source_key = str(row.get("source_key") or "")
        if not source_key or source_key in source_by_key:
            raise BoardRuntimeImageError(
                f"{label}.sources[{index}] source_key is empty or duplicated"
            )
        source_by_key[source_key] = row
    if set(source_by_key) != set(source_order) or len(source_by_key) != len(source_order):
        raise BoardRuntimeImageError(f"{label} does not capture every runtime source exactly once")
    target_specs = stream_spec.get("targets")
    template_targets = _rows(semantic_stream.get("targets"))
    template_by_key = {
        str(row.get("source_key") or ""): row for row in template_targets
    }
    if not isinstance(target_specs, dict) or set(template_by_key) != set(source_order):
        raise BoardRuntimeImageError(f"{label} semantic target authority is incomplete")

    words: list[int] = []
    target_bindings: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    for source_key in source_order:
        spec = target_specs.get(source_key)
        template = template_by_key[source_key]
        if not isinstance(spec, dict):
            raise BoardRuntimeImageError(f"{label}/{source_key} adapter target is malformed")
        tensor, _source_path, source_record = _load_tensor(
            source_by_key[source_key], capture_base_dir, f"{label}/{source_key}"
        )
        source_axes = [str(value) for value in spec.get("source_axis_order", [])]
        drop_axes = [int(value) for value in spec.get("drop_singleton_axes", [])]
        try:
            logical_shape, logical_axes = logical_shape_and_axes(
                list(tensor.shape), source_axes, drop_axes
            )
            target_words, packing = tensor_u32_words(
                tensor, str(spec.get("storage_dtype") or "")
            )
        except (TypeError, ValueError) as exc:
            raise BoardRuntimeImageError(f"{label}/{source_key}: {exc}") from exc
        offset = len(words)
        words.extend(target_words)
        stream_range = {
            "word_offset": offset,
            "word_count": len(target_words),
            "word_end_exclusive": len(words),
        }
        for name, actual, expected in (
            ("target_id", spec.get("target_id"), template.get("target_id")),
            ("semantic_role", spec.get("semantic_role"), template.get("semantic_role")),
            ("source_dtype", source_record["dtype"], template.get("source_dtype")),
            ("source_shape", source_record["shape"], template.get("source_shape")),
            ("source_axis_order", source_axes, template.get("source_axis_order")),
            ("dropped_singleton_axes", drop_axes, template.get("dropped_singleton_axes")),
            ("logical_shape", logical_shape, template.get("logical_shape")),
            ("logical_axis_order", logical_axes, template.get("logical_axis_order")),
            ("packing", packing, template.get("packing")),
            ("stream_range", stream_range, template.get("stream_range")),
            ("address_formula", spec.get("address_formula"), template.get("address_formula")),
            ("sharing", spec.get("sharing"), template.get("sharing")),
        ):
            if actual != expected:
                raise BoardRuntimeImageError(
                    f"{label}/{source_key} {name} differs from semantic runtime authority"
                )
        target_bindings.append(
            {
                "source_key": source_key,
                "target_id": template.get("target_id"),
                "semantic_role": template.get("semantic_role"),
                "stream_range": stream_range,
                "source_tensor_sha256": source_record["tensor_sha256"],
                "source_file_sha256": source_record["file_sha256"],
                "source_dtype": source_record["dtype"],
                "source_shape": source_record["shape"],
                "logical_shape": logical_shape,
                "packing": packing,
            }
        )
        source_files.append(source_record)
    expected_words = int(stage.get("global_stream_range", {}).get("word_count") or 0)
    if len(words) != expected_words:
        raise BoardRuntimeImageError(
            f"{label} packed word count {len(words)} differs from connected {expected_words}"
        )
    return words, {
        "stage_id": stage_id,
        "consumer_op": consumer_op,
        "runtime_contract_sha256": semantic_stream.get("contract_sha256"),
        "word_offset": 0,
        "word_count": len(words),
        "targets": target_bindings,
    }, source_files


def _u32le_bytes(words: list[int]) -> bytes:
    payload = bytearray(len(words) * 4)
    for index, word in enumerate(words):
        if isinstance(word, bool) or not isinstance(word, int) or not 0 <= word <= 0xFFFFFFFF:
            raise BoardRuntimeImageError(f"packed runtime word {index} is outside u32")
        struct.pack_into("<I", payload, index * 4, word)
    return bytes(payload)


def _prepare_layers(
    capture_document: _Document,
    adapter_document: _Document,
    runtime_document: _Document,
    connected_document: _Document,
) -> tuple[list[_PreparedLayer], dict[str, Any]]:
    capture = capture_document.value
    adapter = adapter_document.value
    runtime = runtime_document.value
    connected = connected_document.value
    schema_errors: list[str] = []
    _validate_schema_shape(
        capture,
        LAYER_RUNTIME_CAPTURE_CONTRACT_SCHEMA,
        "layer_runtime_capture_contract",
        schema_errors,
    )
    if schema_errors:
        raise BoardRuntimeImageError(
            f"layer runtime capture schema violation: {schema_errors[0]}"
        )
    if capture.get("schema_version") != CAPTURE_SCHEMA_VERSION:
        raise BoardRuntimeImageError("layer runtime capture schema is unsupported")
    if (
        capture.get("status") != "pass"
        or capture.get("accelerator_scope") != "transformer_blocks_only"
    ):
        raise BoardRuntimeImageError("layer runtime capture contract is not pass")
    capture_hash = _contract_sha256(
        capture,
        "layer runtime capture",
        excluded_fields={"path", "file_sha256"},
    )
    source_reference_hash = _sha256(
        capture.get("source_reference_manifest_sha256"),
        "layer runtime capture source reference",
    )
    semantic_streams = _validate_semantic_authority(adapter_document, runtime_document)
    stages, nonempty_stages, composite_words, connected_hash = _validate_connected_contract(
        connected_document, semantic_streams
    )
    del stages
    runtime_hash = _contract_sha256(
        runtime,
        "semantic runtime",
        excluded_fields={"path", "file_sha256"},
    )
    if capture.get("semantic_adapter_sha256") != adapter_document.identity_sha256:
        raise BoardRuntimeImageError("capture contract does not bind the semantic adapter")
    if capture.get("semantic_runtime_contract_sha256") != runtime_hash:
        raise BoardRuntimeImageError("capture contract does not bind semantic runtime authority")
    if capture.get("connected_runtime_stream_contract_sha256") != connected_hash:
        raise BoardRuntimeImageError("capture contract does not bind connected runtime authority")
    layer_count = _integer(
        capture.get("target_layer_count"), "layer runtime capture target_layer_count", minimum=1
    )
    layer_rows = _rows(capture.get("layers"))
    if [row.get("layer_index") for row in layer_rows] != list(range(layer_count)):
        raise BoardRuntimeImageError(
            "layer runtime captures must cover every target layer exactly once in order"
        )

    prepared: list[_PreparedLayer] = []
    required_stage_ids = [str(stage.get("stage_id") or "") for stage in nonempty_stages]
    for layer_index, layer in enumerate(layer_rows):
        invocations = _rows(layer.get("stage_invocations"))
        invocation_by_stage: dict[str, dict[str, Any]] = {}
        for index, invocation in enumerate(invocations):
            stage_id = str(invocation.get("stage_id") or "")
            if not stage_id or stage_id in invocation_by_stage:
                raise BoardRuntimeImageError(
                    f"layer {layer_index} invocation[{index}] stage_id is empty or duplicated"
                )
            invocation_by_stage[stage_id] = invocation
        if set(invocation_by_stage) != set(required_stage_ids) or len(invocations) != len(
            required_stage_ids
        ):
            raise BoardRuntimeImageError(
                f"layer {layer_index} runtime invocations do not exactly cover non-empty connected stages"
            )
        layer_words: list[int] = []
        stage_bindings: list[dict[str, Any]] = []
        source_files: list[dict[str, Any]] = []
        for stage in nonempty_stages:
            stage_id = str(stage.get("stage_id") or "")
            op = str(stage.get("op") or "")
            stage_words, stage_binding, stage_sources = _pack_stage_invocation(
                invocation_by_stage[stage_id],
                stage,
                adapter,
                semantic_streams[op],
                capture_document.base_dir,
            )
            stage_offset = len(layer_words)
            layer_words.extend(stage_words)
            stage_binding["word_offset"] = stage_offset
            stage_binding["word_end_exclusive"] = len(layer_words)
            stage_bindings.append(stage_binding)
            source_files.extend(stage_sources)
        if len(layer_words) != composite_words:
            raise BoardRuntimeImageError(
                f"layer {layer_index} composite runtime word count differs from connected contract"
            )
        payload = _u32le_bytes(layer_words)
        prepared.append(
            _PreparedLayer(
                layer_index=layer_index,
                payload=payload,
                sha256=hashlib.sha256(payload).hexdigest(),
                stage_bindings=stage_bindings,
                source_files=source_files,
            )
        )
    authority = {
        "capture_contract_sha256": capture_hash,
        "capture_contract_identity_sha256": capture_document.identity_sha256,
        "source_reference_manifest_sha256": source_reference_hash,
        "semantic_adapter_sha256": adapter_document.identity_sha256,
        "semantic_runtime_contract_sha256": runtime_hash,
        "semantic_runtime_contract_identity_sha256": runtime_document.identity_sha256,
        "connected_runtime_stream_contract_sha256": connected_hash,
        "connected_runtime_stream_contract_identity_sha256": connected_document.identity_sha256,
        "target_layer_count": layer_count,
        "canonical_layer_word_count": composite_words,
    }
    return prepared, authority


def validate_layer_runtime_capture_contract(
    layer_runtime_capture_contract: dict[str, Any] | str | Path,
    semantic_adapter: dict[str, Any] | str | Path,
    semantic_runtime_contract: dict[str, Any] | str | Path,
    connected_runtime_stream_contract: dict[str, Any] | str | Path,
) -> tuple[dict[str, Any], list[str]]:
    """Validate every captured layer and return a byte-identity summary."""

    try:
        capture_document = _load_document(
            layer_runtime_capture_contract, "layer runtime capture contract"
        )
        adapter_document = _load_document(semantic_adapter, "semantic adapter")
        runtime_document = _load_document(
            semantic_runtime_contract, "semantic runtime contract"
        )
        connected_document = _load_document(
            connected_runtime_stream_contract, "connected runtime stream contract"
        )
        prepared, authority = _prepare_layers(
            capture_document,
            adapter_document,
            runtime_document,
            connected_document,
        )
    except (BoardRuntimeImageError, OSError, RuntimeError, TypeError, ValueError) as exc:
        return {"status": "fail"}, [str(exc)]
    return {
        "schema_version": "spatialaccagent.layer_runtime_capture_validation.v1",
        "status": "pass",
        **authority,
        "layers": [
            {
                "layer_index": layer.layer_index,
                "word_count": len(layer.payload) // 4,
                "byte_count": len(layer.payload),
                "sha256": layer.sha256,
                "stage_bindings": copy.deepcopy(layer.stage_bindings),
            }
            for layer in prepared
        ],
    }, []


def materialize_board_runtime_image(
    layer_runtime_capture_contract: dict[str, Any] | str | Path,
    semantic_adapter: dict[str, Any] | str | Path,
    semantic_runtime_contract: dict[str, Any] | str | Path,
    connected_runtime_stream_contract: dict[str, Any] | str | Path,
    image_path: str | Path,
    manifest_path: str | Path | None = None,
    *,
    validation_layer_indices: list[int] | tuple[int, ...] | None = None,
) -> dict[str, Any]:
    """Pack and hash-deduplicate real per-layer runtime invocation streams."""

    capture_document = _load_document(
        layer_runtime_capture_contract, "layer runtime capture contract"
    )
    adapter_document = _load_document(semantic_adapter, "semantic adapter")
    runtime_document = _load_document(
        semantic_runtime_contract, "semantic runtime contract"
    )
    connected_document = _load_document(
        connected_runtime_stream_contract, "connected runtime stream contract"
    )
    prepared, authority = _prepare_layers(
        capture_document,
        adapter_document,
        runtime_document,
        connected_document,
    )

    model_layer_count = int(authority["target_layer_count"])
    try:
        scope = resolve_board_validation_scope(
            {
                "acceptance_policy": {
                    "board_validation_mode": (
                        "full_model_pipeline_liveness"
                        if validation_layer_indices is None
                        else PREFIX_MODEL_MODE
                    ),
                    **(
                        {"board_validation_layer_indices": list(validation_layer_indices)}
                        if validation_layer_indices is not None
                        else {}
                    ),
                }
            },
            {"num_layers": model_layer_count},
        )
    except BoardValidationScopeError as exc:
        raise BoardRuntimeImageError(str(exc)) from exc
    prepared = [prepared[index] for index in scope.layer_indices]
    authority = {
        **authority,
        "model_layer_count": model_layer_count,
        "target_layer_count": scope.validation_layer_count,
        "validation_layer_indices": list(scope.layer_indices),
    }

    final_image = Path(image_path).expanduser().resolve()
    final_manifest = (
        Path(manifest_path).expanduser().resolve()
        if manifest_path is not None
        else final_image.parent / "board_runtime_image_manifest.json"
    )
    if final_image == final_manifest:
        raise BoardRuntimeImageError("image_path and manifest_path must differ")
    source_paths = {
        Path(str(source["path"])).resolve()
        for layer in prepared
        for source in layer.source_files
    }
    if final_image in source_paths or final_manifest in source_paths:
        raise BoardRuntimeImageError("runtime image outputs must not replace captured tensors")
    final_image.parent.mkdir(parents=True, exist_ok=True)
    final_manifest.parent.mkdir(parents=True, exist_ok=True)
    token = f"{os.getpid()}.{uuid.uuid4().hex}"
    temporary_image = final_image.with_name(f".{final_image.name}.{token}.tmp")
    temporary_manifest = final_manifest.with_name(f".{final_manifest.name}.{token}.tmp")

    try:
        unique_by_identity: dict[
            tuple[str, int], list[tuple[bytes, dict[str, Any]]]
        ] = {}
        unique_segments: list[dict[str, Any]] = []
        layer_bindings: list[dict[str, Any]] = []
        image_digest = hashlib.sha256()
        image_offset = 0
        with temporary_image.open("wb") as output:
            for layer in prepared:
                identity = (layer.sha256, len(layer.payload))
                candidates = unique_by_identity.get(identity, [])
                segment = next(
                    (
                        candidate_segment
                        for candidate_payload, candidate_segment in candidates
                        if candidate_payload == layer.payload
                    ),
                    None,
                )
                if segment is None:
                    segment = {
                        "segment_id": f"runtime_segment_{len(unique_segments)}",
                        "byte_offset": image_offset,
                        "byte_count": len(layer.payload),
                        "byte_end_exclusive": image_offset + len(layer.payload),
                        "word_offset": image_offset // 4,
                        "word_count": len(layer.payload) // 4,
                        "word_end_exclusive": (image_offset + len(layer.payload)) // 4,
                        "sha256": layer.sha256,
                        "layer_indices": [],
                    }
                    output.write(layer.payload)
                    image_digest.update(layer.payload)
                    image_offset += len(layer.payload)
                    unique_by_identity.setdefault(identity, []).append(
                        (layer.payload, segment)
                    )
                    unique_segments.append(segment)
                segment["layer_indices"].append(layer.layer_index)
                layer_bindings.append(
                    {
                        "layer_index": layer.layer_index,
                        "segment_id": segment["segment_id"],
                        "byte_offset": segment["byte_offset"],
                        "byte_count": segment["byte_count"],
                        "word_offset": segment["word_offset"],
                        "word_count": segment["word_count"],
                        "sha256": segment["sha256"],
                        "stage_bindings": copy.deepcopy(layer.stage_bindings),
                    }
                )
            output.flush()
            os.fsync(output.fileno())
        if temporary_image.stat().st_size != image_offset:
            raise BoardRuntimeImageError("temporary runtime image size mismatch")
        image_hash = image_digest.hexdigest()
        if sha256_file(temporary_image) != image_hash:
            raise BoardRuntimeImageError("temporary runtime image hash mismatch")

        source_file_rows: dict[tuple[str, str], dict[str, Any]] = {}
        for layer in prepared:
            for source in layer.source_files:
                key = (str(source["path"]), str(source["file_sha256"]))
                source_file_rows[key] = copy.deepcopy(source)
        manifest: dict[str, Any] = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "scope_coverage_complete": True,
            "all_target_layers": scope.validation_layer_count == model_layer_count,
            **authority,
            "word_bits": 32,
            "byte_order": "little",
            "image_format": IMAGE_FORMAT,
            "path": str(final_image),
            "sha256": image_hash,
            "image_sha256": image_hash,
            "byte_count": image_offset,
            "total_bytes": image_offset,
            "word_count": image_offset // 4,
            "unique_stream_count": len(unique_segments),
            "unique_segments": unique_segments,
            "layer_bindings": layer_bindings,
            "source_tensor_files": [
                source_file_rows[key] for key in sorted(source_file_rows)
            ],
            "deduplication_policy": {
                "kind": "exact_u32le_bytes_sha256_and_length",
                "cross_layer_sharing_is_never_assumed": True,
                "shared_segment_requires_equal_recomputed_bytes": True,
                "different_streams_remain_distinct": True,
            },
            "image": {
                "path": str(final_image),
                "sha256": image_hash,
                "format": IMAGE_FORMAT,
                "word_bits": 32,
                "byte_order": "little",
                "byte_count": image_offset,
                "word_count": image_offset // 4,
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
        os.replace(temporary_manifest, final_manifest)
        return manifest
    except Exception:
        temporary_image.unlink(missing_ok=True)
        temporary_manifest.unlink(missing_ok=True)
        raise
