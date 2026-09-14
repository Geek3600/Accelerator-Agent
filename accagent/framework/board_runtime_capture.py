"""Capture every decoder layer's runtime tensors from one real-model inference.

The semantic adapter selects hook locations.  Runtime source names never select
Python arguments: layer zero learns each source's recursive args/kwargs path by
matching the immutable reference tensor hash, shape, and dtype.  The learned
paths are then replayed for every remaining decoder layer.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import shutil
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any

from accagent.framework.board_runtime_image import (
    CAPTURE_SCHEMA_VERSION,
    sha256_file,
    sha256_json,
)
from accagent.framework.semantic_runtime import (
    COMPOSITE_STREAM_SCHEMA_VERSION,
    SCHEMA_VERSION as SEMANTIC_RUNTIME_SCHEMA_VERSION,
    tensor_sha256,
)


REFERENCE_SCHEMA_VERSION = "spatialaccagent.target_model_reference.v1"
CAPTURE_CONTRACT_FILENAME = "layer_runtime_capture_contract.json"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class BoardRuntimeCaptureError(RuntimeError):
    """Raised when a complete, reference-bound layer capture cannot be proven."""


@dataclass(frozen=True)
class _Document:
    value: dict[str, Any]
    identity_sha256: str
    base_dir: Path
    path: Path | None


@dataclass(frozen=True)
class _TensorAuthority:
    tensor: Any
    path: Path
    file_sha256: str
    tensor_sha256: str
    shape: list[int]
    dtype: str

    @property
    def identity(self) -> tuple[str, tuple[int, ...], str]:
        return self.tensor_sha256, tuple(self.shape), self.dtype


PathToken = tuple[str, Any]
TensorPath = tuple[PathToken, ...]


def _load_document(value: dict[str, Any] | str | Path, label: str) -> _Document:
    if isinstance(value, dict):
        return _Document(
            value=value,
            identity_sha256=sha256_json(value),
            base_dir=Path.cwd().resolve(),
            path=None,
        )
    if not isinstance(value, (str, Path)):
        raise BoardRuntimeCaptureError(f"{label} must be a JSON object or path")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise BoardRuntimeCaptureError(f"{label} file is missing: {path}")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoardRuntimeCaptureError(f"cannot read {label}: {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise BoardRuntimeCaptureError(f"{label} must be a JSON object: {path}")
    return _Document(
        value=document,
        identity_sha256=sha256_file(path),
        base_dir=path.parent,
        path=path,
    )


def _sha256(value: Any, label: str) -> str:
    normalized = str(value or "").lower()
    if SHA256_PATTERN.fullmatch(normalized) is None:
        raise BoardRuntimeCaptureError(f"{label} is not a SHA-256 digest")
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
        raise BoardRuntimeCaptureError(f"{label} contract hash mismatch")
    return declared


def _resolve_path(raw: Any, base_dir: Path, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise BoardRuntimeCaptureError(f"{label}.path is missing")
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else base_dir / path).resolve()


def _load_tensor_record(
    record: dict[str, Any], base_dir: Path, label: str
) -> _TensorAuthority:
    import torch

    path = _resolve_path(record.get("path"), base_dir, label)
    if not path.is_file():
        raise BoardRuntimeCaptureError(f"{label} tensor file is missing: {path}")
    file_hash = _sha256(record.get("file_sha256"), f"{label}.file_sha256")
    if sha256_file(path) != file_hash:
        raise BoardRuntimeCaptureError(f"{label} tensor file hash mismatch")
    try:
        tensor = torch.load(path, map_location="cpu", weights_only=True)
    except Exception as exc:
        raise BoardRuntimeCaptureError(f"cannot load {label} tensor: {exc}") from exc
    if not isinstance(tensor, torch.Tensor):
        raise BoardRuntimeCaptureError(f"{label} file does not contain one tensor")
    value_hash = _sha256(record.get("tensor_sha256"), f"{label}.tensor_sha256")
    if tensor_sha256(tensor) != value_hash:
        raise BoardRuntimeCaptureError(f"{label} tensor value hash mismatch")
    shape = list(tensor.shape)
    dtype = str(tensor.dtype)
    if record.get("shape") != shape or record.get("dtype") != dtype:
        raise BoardRuntimeCaptureError(f"{label} tensor shape/dtype differs from reference")
    return _TensorAuthority(
        tensor=tensor.detach().cpu().clone(),
        path=path,
        file_sha256=file_hash,
        tensor_sha256=value_hash,
        shape=shape,
        dtype=dtype,
    )


def _qualified_type(value: Any) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}"


def _tensor_identity(tensor: Any) -> tuple[str, tuple[int, ...], str]:
    return tensor_sha256(tensor), tuple(int(value) for value in tensor.shape), str(tensor.dtype)


def _flatten_tensors(args: Any, kwargs: Any) -> dict[TensorPath, Any]:
    import torch

    result: dict[TensorPath, Any] = {}
    active: set[int] = set()

    def visit(value: Any, path: TensorPath) -> None:
        if isinstance(value, torch.Tensor):
            result[path] = value
            return
        if isinstance(value, Mapping):
            identity = id(value)
            if identity in active:
                return
            active.add(identity)
            try:
                for key, item in value.items():
                    visit(item, (*path, ("mapping_key", key)))
            finally:
                active.remove(identity)
            return
        if isinstance(value, (list, tuple)):
            identity = id(value)
            if identity in active:
                return
            active.add(identity)
            try:
                for index, item in enumerate(value):
                    visit(item, (*path, ("sequence_index", index)))
            finally:
                active.remove(identity)
            return
        if is_dataclass(value) and not isinstance(value, type):
            identity = id(value)
            if identity in active:
                return
            active.add(identity)
            try:
                for field in fields(value):
                    visit(getattr(value, field.name), (*path, ("attribute", field.name)))
            finally:
                active.remove(identity)

    visit(args, (("root", "args"),))
    visit(kwargs, (("root", "kwargs"),))
    return result


def _serialized_path(path: TensorPath) -> list[str]:
    tokens: list[str] = []
    for kind, value in path:
        if isinstance(value, (str, int, float, bool)) or value is None:
            encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        else:
            encoded = json.dumps(
                {"type": _qualified_type(value), "repr": repr(value)},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
        tokens.append(f"{kind}:{encoded}")
    return tokens


def _safe_component(value: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "tensor"
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"{stem[:48]}_{suffix}"


def _validate_reference(
    reference_document: _Document,
    adapter_document: _Document,
    required_source_keys: set[str],
) -> dict[str, Any]:
    reference = reference_document.value
    if (
        reference.get("schema_version") != REFERENCE_SCHEMA_VERSION
        or reference.get("status") != "ready"
    ):
        raise BoardRuntimeCaptureError("target-model reference is not ready or supported")
    target = reference.get("target_model")
    weights = reference.get("weights")
    input_record = reference.get("input")
    reference_body = reference.get("reference")
    if not all(isinstance(value, dict) for value in (target, weights, input_record, reference_body)):
        raise BoardRuntimeCaptureError("target-model reference sections are incomplete")
    if target.get("accelerator_scope") != "transformer_blocks_only":
        raise BoardRuntimeCaptureError("target-model reference scope is not transformer_blocks_only")

    adapter_binding = reference_body.get("semantic_adapter")
    if not isinstance(adapter_binding, dict):
        raise BoardRuntimeCaptureError("target-model reference has no semantic adapter binding")
    adapter_path = _resolve_path(
        adapter_binding.get("path"), reference_document.base_dir, "reference semantic adapter"
    )
    adapter_hash = _sha256(adapter_binding.get("sha256"), "reference semantic adapter")
    if not adapter_path.is_file() or sha256_file(adapter_path) != adapter_hash:
        raise BoardRuntimeCaptureError("reference semantic adapter file/hash mismatch")
    if adapter_hash != adapter_document.identity_sha256:
        raise BoardRuntimeCaptureError("supplied semantic adapter differs from reference authority")

    snapshot = _resolve_path(target.get("snapshot"), reference_document.base_dir, "model snapshot")
    if not snapshot.is_dir():
        raise BoardRuntimeCaptureError(f"target-model checkpoint snapshot is missing: {snapshot}")
    architecture = str(target.get("architecture") or "")
    if not architecture:
        raise BoardRuntimeCaptureError("target-model architecture is missing")
    layer_count = target.get("num_hidden_layers")
    if isinstance(layer_count, bool) or not isinstance(layer_count, int) or layer_count <= 0:
        raise BoardRuntimeCaptureError("target-model layer count is invalid")

    source_manifest = _resolve_path(
        weights.get("source_manifest"), reference_document.base_dir, "source weight manifest"
    )
    source_manifest_hash = _sha256(
        weights.get("source_manifest_sha256"), "source weight manifest"
    )
    if not source_manifest.is_file() or sha256_file(source_manifest) != source_manifest_hash:
        raise BoardRuntimeCaptureError("source weight manifest file/hash mismatch")
    checkpoint_hash = _sha256(
        weights.get("source_checkpoint_sha256"), "source checkpoint"
    )

    input_authority = _load_tensor_record(
        input_record, reference_document.base_dir, "reference input"
    )
    final_record = reference_body.get("full_model_output")
    if not isinstance(final_record, dict):
        raise BoardRuntimeCaptureError("reference final decoder-layer output is missing")
    final_authority = _load_tensor_record(
        final_record, reference_document.base_dir, "reference final decoder output"
    )
    if final_record.get("target_layer_count") != layer_count:
        raise BoardRuntimeCaptureError("reference final output layer count differs from target model")

    runtime_records = reference_body.get("semantic_runtime_inputs")
    if not isinstance(runtime_records, dict):
        raise BoardRuntimeCaptureError("reference semantic runtime tensor records are missing")
    runtime_authorities: dict[str, _TensorAuthority] = {}
    for source_key in sorted(required_source_keys):
        record = runtime_records.get(source_key)
        if not isinstance(record, dict):
            raise BoardRuntimeCaptureError(
                f"reference runtime tensor is missing for adapter source {source_key!r}"
            )
        runtime_authorities[source_key] = _load_tensor_record(
            record,
            reference_document.base_dir,
            f"reference runtime source {source_key}",
        )

    model_implementation = reference_body.get("model_implementation")
    symbols = (
        model_implementation.get("symbols")
        if isinstance(model_implementation, dict)
        and isinstance(model_implementation.get("symbols"), dict)
        else {}
    )
    decoder_layer_class = str(symbols.get("decoder_layer") or "")
    if not decoder_layer_class:
        raise BoardRuntimeCaptureError("reference decoder-layer implementation symbol is missing")
    layer_records = reference_body.get("layer_output_records")
    first_layer_record = ""
    if isinstance(layer_records, list) and layer_records and isinstance(layer_records[0], dict):
        first_layer_record = str(layer_records[0].get("module") or "")

    return {
        "snapshot": snapshot,
        "architecture": architecture,
        "layer_count": layer_count,
        "checkpoint_sha256": checkpoint_hash,
        "input": input_authority,
        "final_output": final_authority,
        "runtime_sources": runtime_authorities,
        "decoder_layer_class": decoder_layer_class,
        "first_layer_record": first_layer_record,
    }


def _validate_runtime_authorities(
    adapter_document: _Document,
    runtime_document: _Document,
    connected_document: _Document,
    reference_sources: dict[str, _TensorAuthority] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], str, str]:
    adapter = adapter_document.value
    runtime = runtime_document.value
    connected = connected_document.value
    if adapter.get("accelerator_scope") != "transformer_blocks_only":
        raise BoardRuntimeCaptureError("semantic adapter scope is not transformer_blocks_only")
    stream_specs = adapter.get("semantic_runtime_streams")
    semantic_stages = adapter.get("semantic_stages")
    if not isinstance(stream_specs, dict) or not stream_specs:
        raise BoardRuntimeCaptureError("semantic adapter has no runtime stream specifications")
    if not isinstance(semantic_stages, dict):
        raise BoardRuntimeCaptureError("semantic adapter has no semantic stage map")

    specs: dict[str, dict[str, Any]] = {}
    for consumer_op, original in stream_specs.items():
        if not isinstance(consumer_op, str) or not consumer_op or not isinstance(original, dict):
            raise BoardRuntimeCaptureError("semantic runtime consumer specification is malformed")
        source_order = original.get("source_order")
        targets = original.get("targets")
        if (
            not isinstance(source_order, list)
            or not source_order
            or not all(isinstance(value, str) and value for value in source_order)
            or len(source_order) != len(set(source_order))
            or not isinstance(targets, dict)
            or set(source_order) != set(targets)
        ):
            raise BoardRuntimeCaptureError(
                f"semantic runtime consumer {consumer_op} has incomplete source coverage"
            )
        stage = semantic_stages.get(consumer_op)
        expected = stage.get("expected") if isinstance(stage, dict) else None
        record = expected.get("record") if isinstance(expected, dict) else None
        if not isinstance(record, str) or not record:
            raise BoardRuntimeCaptureError(
                f"semantic runtime consumer {consumer_op} has no stage expected.record"
            )
        specs[consumer_op] = {
            "consumer_op": consumer_op,
            "source_order": list(source_order),
            "record": record,
        }

    if runtime.get("schema_version") != SEMANTIC_RUNTIME_SCHEMA_VERSION:
        raise BoardRuntimeCaptureError("semantic runtime contract schema is unsupported")
    if runtime.get("status") != "pass" or runtime.get("blockers") not in ([], None):
        raise BoardRuntimeCaptureError("semantic runtime contract is not pass")
    runtime_hash = _contract_sha256(
        runtime, "semantic runtime", excluded_fields={"path", "file_sha256"}
    )
    if runtime.get("model_semantic_adapter_sha256") != adapter_document.identity_sha256:
        raise BoardRuntimeCaptureError("semantic runtime contract does not bind the adapter")
    runtime_streams: dict[str, dict[str, Any]] = {}
    rows = runtime.get("streams")
    if not isinstance(rows, list):
        raise BoardRuntimeCaptureError("semantic runtime contract stream list is missing")
    for index, stream in enumerate(rows):
        if not isinstance(stream, dict):
            raise BoardRuntimeCaptureError(f"semantic runtime stream[{index}] is not an object")
        consumer_op = str(stream.get("consumer_op") or "")
        if not consumer_op or consumer_op in runtime_streams:
            raise BoardRuntimeCaptureError("semantic runtime consumer is empty or duplicated")
        _contract_sha256(stream, f"semantic runtime stream {consumer_op}")
        spec = specs.get(consumer_op)
        if spec is None or stream.get("source_order") != spec["source_order"]:
            raise BoardRuntimeCaptureError(
                f"semantic runtime stream {consumer_op} differs from adapter source order"
            )
        targets = stream.get("targets")
        if (
            not isinstance(targets, list)
            or not all(isinstance(row, dict) for row in targets)
            or [row.get("source_key") for row in targets] != spec["source_order"]
        ):
            raise BoardRuntimeCaptureError(
                f"semantic runtime stream {consumer_op} target coverage is incomplete"
            )
        if reference_sources is not None:
            for target in targets:
                source_key = str(target.get("source_key") or "")
                authority = reference_sources.get(source_key)
                if authority is None:
                    raise BoardRuntimeCaptureError(
                        f"semantic runtime target has unknown source {source_key!r}"
                    )
                if (
                    target.get("source_tensor_sha256") != authority.tensor_sha256
                    or target.get("source_file_sha256") != authority.file_sha256
                    or target.get("source_shape") != authority.shape
                    or target.get("source_dtype") != authority.dtype
                ):
                    raise BoardRuntimeCaptureError(
                        f"semantic runtime source {source_key} differs from reference authority"
                    )
        runtime_streams[consumer_op] = stream
    if set(runtime_streams) != set(specs):
        raise BoardRuntimeCaptureError("semantic runtime contract does not cover every adapter stream")

    if connected.get("schema_version") != COMPOSITE_STREAM_SCHEMA_VERSION:
        raise BoardRuntimeCaptureError("connected runtime stream schema is unsupported")
    if connected.get("status") != "pass" or connected.get("word_bits") != 32:
        raise BoardRuntimeCaptureError("connected runtime stream is not pass u32")
    connected_hash = _contract_sha256(
        connected, "connected runtime stream", excluded_fields={"path"}
    )
    stage_rows = connected.get("stage_segments")
    if not isinstance(stage_rows, list):
        raise BoardRuntimeCaptureError("connected runtime stage segments are missing")
    nonempty_stages: list[dict[str, Any]] = []
    consumers_seen: set[str] = set()
    for index, stage in enumerate(stage_rows):
        if not isinstance(stage, dict) or stage.get("stage_index") != index:
            raise BoardRuntimeCaptureError("connected runtime stage order is malformed")
        stage_id = str(stage.get("stage_id") or "")
        consumer_op = str(stage.get("op") or "")
        stream_range = stage.get("global_stream_range")
        word_count = stream_range.get("word_count") if isinstance(stream_range, dict) else None
        if not stage_id or not consumer_op or isinstance(word_count, bool) or not isinstance(word_count, int) or word_count < 0:
            raise BoardRuntimeCaptureError("connected runtime stage identity/range is malformed")
        if word_count == 0:
            continue
        semantic_stream = runtime_streams.get(consumer_op)
        if semantic_stream is None:
            raise BoardRuntimeCaptureError(
                f"connected runtime stage {stage_id} has no adapter/runtime consumer authority"
            )
        if stage.get("runtime_contract_sha256") != semantic_stream.get("contract_sha256"):
            raise BoardRuntimeCaptureError(
                f"connected runtime stage {stage_id} differs from semantic runtime contract"
            )
        consumers_seen.add(consumer_op)
        nonempty_stages.append(
            {"stage_id": stage_id, "consumer_op": consumer_op, "stage_index": index}
        )
    if consumers_seen != set(specs):
        raise BoardRuntimeCaptureError(
            "connected runtime stages do not cover every adapter runtime consumer"
        )
    return specs, nonempty_stages, runtime_hash, connected_hash


def _find_decoder_layers(
    model: Any, expected_count: int, expected_class: str
) -> tuple[str, list[Any]]:
    candidates: list[tuple[str, list[Any]]] = []
    seen: set[int] = set()
    for name, module in model.named_modules():
        children = list(module.children())
        if (
            len(children) == expected_count
            and all(_qualified_type(child) == expected_class for child in children)
            and id(module) not in seen
        ):
            seen.add(id(module))
            candidates.append((name or "<root>", children))
    if len(candidates) != 1:
        labels = [name for name, _layers in candidates]
        raise BoardRuntimeCaptureError(
            f"decoder-layer container is not uniquely proven from reference class/count: {labels}"
        )
    return candidates[0]


def _resolve_record_module(
    layer: Any, record: str, first_layer_record: str
) -> Any:
    relative = record
    if first_layer_record and record == first_layer_record:
        relative = ""
    elif first_layer_record and record.startswith(f"{first_layer_record}."):
        relative = record[len(first_layer_record) + 1 :]
    if not relative or relative == ".":
        return layer
    if hasattr(layer, "get_submodule"):
        try:
            return layer.get_submodule(relative)
        except Exception:
            pass
    current = layer
    for component in relative.split("."):
        if component.isdigit() and hasattr(current, "__getitem__"):
            current = current[int(component)]
        else:
            current = getattr(current, component, None)
        if current is None:
            break
    if current is None or not hasattr(current, "register_forward_pre_hook"):
        raise BoardRuntimeCaptureError(
            f"adapter expected.record {record!r} does not resolve inside decoder layer"
        )
    return current


def _default_model_loader(reference: dict[str, Any], input_tensor: Any) -> Any:
    from transformers import AutoModelForCausalLM

    snapshot = Path(str(reference["target_model"]["snapshot"])).expanduser().resolve()
    return AutoModelForCausalLM.from_pretrained(
        snapshot,
        local_files_only=True,
        dtype=input_tensor.dtype,
        low_cpu_mem_usage=True,
    )


def _default_inference_runner(model: Any, input_tensor: Any, _reference: dict[str, Any]) -> Any:
    parameters = inspect.signature(model.forward).parameters
    accepts_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    candidates = {
        "inputs_embeds": input_tensor,
        "use_cache": False,
        "output_hidden_states": True,
        "return_dict": True,
    }
    kwargs = {
        key: value
        for key, value in candidates.items()
        if accepts_kwargs or key in parameters
    }
    if "inputs_embeds" not in kwargs:
        raise BoardRuntimeCaptureError(
            "target model forward does not expose the reference inputs_embeds boundary"
        )
    return model(**kwargs)


def capture_board_runtime_contract(
    source_reference_manifest: dict[str, Any] | str | Path,
    semantic_adapter: dict[str, Any] | str | Path,
    semantic_runtime_contract: dict[str, Any] | str | Path,
    connected_runtime_stream_contract: dict[str, Any] | str | Path,
    output_dir: str | Path,
    *,
    model: Any | None = None,
    model_loader: Callable[[dict[str, Any], Any], Any] | None = None,
    inference_runner: Callable[[Any, Any, dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Run one complete inference and write a strict full-layer capture contract."""

    import torch

    reference_document = _load_document(
        source_reference_manifest, "source reference manifest"
    )
    adapter_document = _load_document(semantic_adapter, "semantic adapter")
    runtime_document = _load_document(
        semantic_runtime_contract, "semantic runtime contract"
    )
    connected_document = _load_document(
        connected_runtime_stream_contract, "connected runtime stream contract"
    )
    initial_specs, _initial_stages, _runtime_hash, _connected_hash = (
        _validate_runtime_authorities(
            adapter_document, runtime_document, connected_document
        )
    )
    required_source_keys = {
        source_key
        for spec in initial_specs.values()
        for source_key in spec["source_order"]
    }
    reference_info = _validate_reference(
        reference_document, adapter_document, required_source_keys
    )
    specs, nonempty_stages, runtime_hash, connected_hash = _validate_runtime_authorities(
        adapter_document,
        runtime_document,
        connected_document,
        reference_info["runtime_sources"],
    )

    final_output_dir = Path(output_dir).expanduser().resolve()
    if final_output_dir.exists():
        if not final_output_dir.is_dir() or any(final_output_dir.iterdir()):
            raise BoardRuntimeCaptureError(
                f"capture output directory must be absent or empty: {final_output_dir}"
            )

    if model is not None and model_loader is not None:
        raise BoardRuntimeCaptureError("supply model or model_loader, not both")
    if model is None:
        loader = model_loader or _default_model_loader
        loader_reference = dict(reference_document.value)
        loader_reference["target_model"] = {
            **reference_document.value["target_model"],
            "snapshot": str(reference_info["snapshot"]),
        }
        model = loader(loader_reference, reference_info["input"].tensor)
    if type(model).__name__ != reference_info["architecture"]:
        raise BoardRuntimeCaptureError(
            "loaded target-model architecture differs from reference manifest"
        )
    model.eval()
    layer_container, layers = _find_decoder_layers(
        model,
        reference_info["layer_count"],
        reference_info["decoder_layer_class"],
    )

    state: dict[str, dict[str, Any]] = {}
    for consumer_op, spec in specs.items():
        state[consumer_op] = {
            "record": spec["record"],
            "source_order": spec["source_order"],
            "learned_paths": {},
            "calls": [0 for _ in layers],
            "captured": [dict() for _ in layers],
        }
    layer_output_calls = [0 for _ in layers]
    layer_outputs: list[Any | None] = [None for _ in layers]
    hooks: list[Any] = []

    def make_runtime_hook(layer_index: int, consumer_op: str) -> Callable[..., None]:
        def capture(_module: Any, args: Any, kwargs: Any) -> None:
            consumer = state[consumer_op]
            consumer["calls"][layer_index] += 1
            if consumer["calls"][layer_index] != 1:
                raise BoardRuntimeCaptureError(
                    f"layer {layer_index} runtime consumer {consumer_op} executed more than once"
                )
            flattened = _flatten_tensors(args, kwargs)
            if layer_index == 0:
                learned: dict[str, TensorPath] = {}
                for source_key in consumer["source_order"]:
                    expected = reference_info["runtime_sources"][source_key].identity
                    candidates = [
                        path
                        for path, tensor in flattened.items()
                        if _tensor_identity(tensor) == expected
                    ]
                    if len(candidates) != 1:
                        raise BoardRuntimeCaptureError(
                            f"layer 0 source {source_key!r} identity matched {len(candidates)} "
                            f"recursive args/kwargs paths; capture path is not uniquely proven"
                        )
                    learned[source_key] = candidates[0]
                if len(set(learned.values())) != len(learned):
                    raise BoardRuntimeCaptureError(
                        f"layer 0 runtime consumer {consumer_op} has ambiguous source identities"
                    )
                consumer["learned_paths"] = learned
            elif not consumer["learned_paths"]:
                raise BoardRuntimeCaptureError(
                    f"layer {layer_index} executed before layer-0 capture path learning"
                )

            for source_key in consumer["source_order"]:
                capture_path = consumer["learned_paths"][source_key]
                tensor = flattened.get(capture_path)
                if tensor is None:
                    raise BoardRuntimeCaptureError(
                        f"layer {layer_index} source {source_key!r} is absent at learned capture path"
                    )
                reference_source = reference_info["runtime_sources"][source_key]
                if list(tensor.shape) != reference_source.shape or str(tensor.dtype) != reference_source.dtype:
                    raise BoardRuntimeCaptureError(
                        f"layer {layer_index} source {source_key!r} shape/dtype changed at learned path"
                    )
                consumer["captured"][layer_index][source_key] = tensor.detach().cpu().clone()

        return capture

    def make_layer_output_hook(layer_index: int) -> Callable[..., None]:
        def capture(_module: Any, _args: Any, output: Any) -> None:
            layer_output_calls[layer_index] += 1
            if layer_output_calls[layer_index] != 1:
                raise BoardRuntimeCaptureError(
                    f"decoder layer {layer_index} executed more than once"
                )
            flattened = _flatten_tensors((output,), {})
            if not flattened:
                raise BoardRuntimeCaptureError(
                    f"decoder layer {layer_index} output contains no tensor"
                )
            layer_outputs[layer_index] = next(iter(flattened.values())).detach().cpu().clone()

        return capture

    try:
        for layer_index, layer in enumerate(layers):
            hooks.append(layer.register_forward_hook(make_layer_output_hook(layer_index)))
            for consumer_op, consumer in state.items():
                module = _resolve_record_module(
                    layer,
                    consumer["record"],
                    reference_info["first_layer_record"],
                )
                hooks.append(
                    module.register_forward_pre_hook(
                        make_runtime_hook(layer_index, consumer_op), with_kwargs=True
                    )
                )
        runner = inference_runner or _default_inference_runner
        with torch.inference_mode():
            runner(model, reference_info["input"].tensor, reference_document.value)
    finally:
        for hook in hooks:
            hook.remove()

    for consumer_op, consumer in state.items():
        if consumer["calls"] != [1 for _ in layers]:
            raise BoardRuntimeCaptureError(
                f"runtime consumer {consumer_op} did not execute exactly once in every layer"
            )
        if any(set(row) != set(consumer["source_order"]) for row in consumer["captured"]):
            raise BoardRuntimeCaptureError(
                f"runtime consumer {consumer_op} capture coverage is incomplete"
            )
    if layer_output_calls != [1 for _ in layers] or any(value is None for value in layer_outputs):
        raise BoardRuntimeCaptureError("decoder-layer output capture coverage is incomplete")
    observed_final = layer_outputs[-1]
    expected_final = reference_info["final_output"]
    observed_final_hash = tensor_sha256(observed_final)
    if (
        observed_final_hash != expected_final.tensor_sha256
        or list(observed_final.shape) != expected_final.shape
        or str(observed_final.dtype) != expected_final.dtype
    ):
        raise BoardRuntimeCaptureError(
            "observed final decoder-layer output differs from existing reference hash/shape/dtype"
        )

    token = f"{os.getpid()}.{uuid.uuid4().hex}"
    staging_dir = final_output_dir.with_name(f".{final_output_dir.name}.{token}.tmp")
    if staging_dir.exists():
        raise BoardRuntimeCaptureError(f"capture staging directory already exists: {staging_dir}")
    staging_dir.mkdir(parents=True)
    try:
        file_records: dict[tuple[int, str, str], dict[str, Any]] = {}
        for layer_index in range(len(layers)):
            for consumer_op, consumer in state.items():
                for source_key in consumer["source_order"]:
                    tensor = consumer["captured"][layer_index][source_key]
                    relative = (
                        Path("layers")
                        / f"layer_{layer_index}"
                        / _safe_component(consumer_op)
                        / f"{_safe_component(source_key)}.pt"
                    )
                    staged_path = staging_dir / relative
                    final_path = final_output_dir / relative
                    staged_path.parent.mkdir(parents=True, exist_ok=True)
                    torch.save(tensor, staged_path)
                    file_records[(layer_index, consumer_op, source_key)] = {
                        "source_key": source_key,
                        "path": str(final_path),
                        "file_sha256": sha256_file(staged_path),
                        "tensor_sha256": tensor_sha256(tensor),
                        "dtype": str(tensor.dtype),
                        "shape": list(tensor.shape),
                        "capture_path": _serialized_path(
                            consumer["learned_paths"][source_key]
                        ),
                    }

        capture = {
            "schema_version": CAPTURE_SCHEMA_VERSION,
            "status": "pass",
            "accelerator_scope": "transformer_blocks_only",
            "target_layer_count": len(layers),
            "source_reference_manifest_sha256": reference_document.identity_sha256,
            "semantic_adapter_sha256": adapter_document.identity_sha256,
            "semantic_runtime_contract_sha256": runtime_hash,
            "connected_runtime_stream_contract_sha256": connected_hash,
            "layers": [
                {
                    "layer_index": layer_index,
                    "stage_invocations": [
                        {
                            "stage_id": stage["stage_id"],
                            "consumer_op": stage["consumer_op"],
                            "sources": [
                                file_records[
                                    (layer_index, stage["consumer_op"], source_key)
                                ]
                                for source_key in state[stage["consumer_op"]]["source_order"]
                            ],
                        }
                        for stage in nonempty_stages
                    ],
                }
                for layer_index in range(len(layers))
            ],
            "capture_provenance": {
                "inference_count": 1,
                "model_snapshot": str(reference_info["snapshot"]),
                "model_architecture": reference_info["architecture"],
                "source_checkpoint_sha256": reference_info["checkpoint_sha256"],
                "source_input_file_sha256": reference_info["input"].file_sha256,
                "source_input_tensor_sha256": reference_info["input"].tensor_sha256,
                "expected_final_decoder_output_sha256": expected_final.tensor_sha256,
                "observed_final_decoder_output_sha256": observed_final_hash,
                "reference_output_verified": True,
                "decoder_layer_container": layer_container,
                "decoder_layer_class": reference_info["decoder_layer_class"],
                "capture_path_learning": "first_layer_reference_identity_match",
                "capture_match_fields": ["tensor_sha256", "shape", "dtype"],
                "keyword_matching_used": False,
            },
        }
        capture["contract_sha256"] = sha256_json(capture)
        contract_path = staging_dir / CAPTURE_CONTRACT_FILENAME
        contract_path.write_text(
            json.dumps(capture, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        contract_file_hash = sha256_file(contract_path)
        if final_output_dir.exists():
            final_output_dir.rmdir()
        os.replace(staging_dir, final_output_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    result = dict(capture)
    result["path"] = str(final_output_dir / CAPTURE_CONTRACT_FILENAME)
    result["file_sha256"] = contract_file_hash
    return result
