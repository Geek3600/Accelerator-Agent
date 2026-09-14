"""Materialize hash-bound runtime semantic constants for DUT loader ports."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "spatialaccagent.semantic_runtime_constant_contract.v1"
COMPOSITE_STREAM_SCHEMA_VERSION = "spatialaccagent.composite_runtime_stream.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def tensor_sha256(tensor: Any) -> str:
    value = tensor.detach().cpu().contiguous().float().numpy()
    return hashlib.sha256(value.tobytes()).hexdigest()


def tensor_u32_words(tensor: Any, storage_dtype: str) -> tuple[list[int], dict[str, Any]]:
    import torch

    value = tensor.detach().cpu().contiguous()
    if storage_dtype == "fp16":
        scalars = [int(item) & 0xFFFF for item in value.to(torch.float16).view(torch.int16).reshape(-1).tolist()]
        padded = len(scalars) % 2
        if padded:
            scalars.append(0)
        words = [scalars[index] | (scalars[index + 1] << 16) for index in range(0, len(scalars), 2)]
        return words, {
            "storage_dtype": "fp16",
            "scalar_bits": 16,
            "scalars_per_u32_word": 2,
            "scalar_zero_is_lsb": True,
            "padding_scalars": padded,
            "conversion": "IEEE fp32/source value to fp16 round-to-nearest-even",
        }
    if storage_dtype == "fp32":
        words = [int(item) & 0xFFFFFFFF for item in value.to(torch.float32).view(torch.int32).reshape(-1).tolist()]
        return words, {
            "storage_dtype": "fp32",
            "scalar_bits": 32,
            "scalars_per_u32_word": 1,
            "scalar_zero_is_lsb": True,
            "padding_scalars": 0,
            "conversion": "IEEE fp32 bit preserving",
        }
    if storage_dtype == "uint32":
        integers = value.to(torch.int64).reshape(-1).tolist()
        if any(int(item) < 0 or int(item) > 0xFFFFFFFF for item in integers):
            raise ValueError("runtime uint32 tensor contains an out-of-range value")
        return [int(item) for item in integers], {
            "storage_dtype": "uint32",
            "scalar_bits": 32,
            "scalars_per_u32_word": 1,
            "scalar_zero_is_lsb": True,
            "padding_scalars": 0,
            "conversion": "non-negative integer value preserving",
        }
    raise ValueError(f"unsupported runtime semantic storage dtype: {storage_dtype}")


def logical_shape_and_axes(
    shape: list[int],
    source_axes: list[str],
    drop_singleton_axes: list[int],
) -> tuple[list[int], list[str]]:
    if len(shape) != len(source_axes):
        raise ValueError(f"runtime tensor rank {len(shape)} does not match declared axes {source_axes}")
    dropped = set(drop_singleton_axes)
    for axis in dropped:
        if axis < 0 or axis >= len(shape) or shape[axis] != 1:
            raise ValueError(f"runtime tensor may drop only a declared singleton axis: axis={axis} shape={shape}")
    return (
        [size for index, size in enumerate(shape) if index not in dropped],
        [name for index, name in enumerate(source_axes) if index not in dropped],
    )


def write_u32_stream(path: Path, words: list[int]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{word & 0xFFFFFFFF:08x}\n" for word in words), encoding="ascii")
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "word_bits": 32,
        "word_count": len(words),
        "address_order": "strictly ascending from zero",
        "word_zero_is_lsb": True,
    }


def materialize_composite_runtime_stream(
    path: Path,
    stage_streams: list[dict[str, Any]],
) -> dict[str, Any]:
    """Concatenate hash-verified runtime streams in pipeline-stage order."""

    if not isinstance(stage_streams, list) or not stage_streams:
        raise ValueError("composite runtime stream requires at least one stage descriptor")
    stage_order: list[str] = []
    stage_segments: list[dict[str, Any]] = []
    sources: list[tuple[str, Path, str, int]] = []
    seen_stage_ids: set[str] = set()
    global_offset = 0
    for stage_index, descriptor in enumerate(stage_streams):
        if not isinstance(descriptor, dict):
            raise ValueError(f"composite runtime stage descriptor {stage_index} is not an object")
        stage_id = str(descriptor.get("stage_id") or "")
        op = str(descriptor.get("op") or "")
        if not stage_id or not op or stage_id in seen_stage_ids:
            raise ValueError("composite runtime stage identities must be non-empty and unique")
        seen_stage_ids.add(stage_id)
        runtime = descriptor.get("runtime_contract")
        if runtime is not None and not isinstance(runtime, dict):
            raise ValueError(f"{stage_id}: runtime contract is not an object")

        word_count = 0
        runtime_contract_hash = ""
        local_stream_hash = hashlib.sha256(b"").hexdigest()
        targets: list[dict[str, Any]] = []
        if isinstance(runtime, dict):
            runtime_contract_hash = str(runtime.get("contract_sha256") or "")
            payload = {key: value for key, value in runtime.items() if key != "contract_sha256"}
            if not runtime_contract_hash or sha256_json(payload) != runtime_contract_hash:
                raise ValueError(f"{stage_id}: runtime contract hash mismatch")
            stream = runtime.get("stream")
            if not isinstance(stream, dict):
                raise ValueError(f"{stage_id}: runtime stream is missing")
            if stream.get("word_bits") != 32:
                raise ValueError(f"{stage_id}: runtime stream word_bits must be 32")
            word_count = stream.get("word_count")
            if isinstance(word_count, bool) or not isinstance(word_count, int) or word_count <= 0:
                raise ValueError(f"{stage_id}: runtime stream word_count is invalid")
            source_path = Path(str(stream.get("path") or ""))
            local_stream_hash = str(stream.get("sha256") or "")
            if not source_path.is_file() or not local_stream_hash:
                raise ValueError(f"{stage_id}: runtime stream path/hash is missing")
            sources.append((stage_id, source_path, local_stream_hash, word_count))

            local_offset = 0
            source_targets = runtime.get("targets")
            if not isinstance(source_targets, list) or not source_targets:
                raise ValueError(f"{stage_id}: runtime target coverage is missing")
            for target in source_targets:
                if not isinstance(target, dict):
                    raise ValueError(f"{stage_id}: runtime target is not an object")
                target_id = str(target.get("target_id") or "")
                local_range = target.get("stream_range")
                if not target_id or not isinstance(local_range, dict):
                    raise ValueError(f"{stage_id}: runtime target identity/range is missing")
                target_count = local_range.get("word_count")
                expected = {
                    "word_offset": local_offset,
                    "word_count": target_count,
                    "word_end_exclusive": local_offset + int(target_count or 0),
                }
                if isinstance(target_count, bool) or not isinstance(target_count, int) or target_count <= 0:
                    raise ValueError(f"{stage_id}/{target_id}: runtime target word_count is invalid")
                if local_range != expected:
                    raise ValueError(f"{stage_id}/{target_id}: runtime target range is not contiguous")
                targets.append(
                    {
                        "target_id": target_id,
                        "semantic_role": target.get("semantic_role"),
                        "local_stream_range": expected,
                        "global_stream_range": {
                            "word_offset": global_offset + local_offset,
                            "word_count": target_count,
                            "word_end_exclusive": global_offset + expected["word_end_exclusive"],
                        },
                        "source_tensor_sha256": target.get("source_tensor_sha256"),
                    }
                )
                local_offset = expected["word_end_exclusive"]
            if local_offset != word_count:
                raise ValueError(f"{stage_id}: runtime targets do not cover the local stream")

        stage_segments.append(
            {
                "stage_index": stage_index,
                "stage_id": stage_id,
                "op": op,
                "runtime_contract_sha256": runtime_contract_hash,
                "local_stream_sha256": local_stream_hash,
                "global_stream_range": {
                    "word_offset": global_offset,
                    "word_count": word_count,
                    "word_end_exclusive": global_offset + word_count,
                },
                "targets": targets,
            }
        )
        stage_order.append(stage_id)
        global_offset += word_count

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    try:
        with temporary_path.open("wb") as output:
            for stage_id, source_path, declared_hash, declared_count in sources:
                digest = hashlib.sha256()
                actual_count = 0
                with source_path.open("rb") as source:
                    for line in source:
                        digest.update(line)
                        if not re.fullmatch(rb"[0-9A-Fa-f]{8}\n", line):
                            raise ValueError(f"{stage_id}: runtime stream is not strict u32 memh")
                        output.write(line)
                        actual_count += 1
                if digest.hexdigest() != declared_hash or actual_count != declared_count:
                    raise ValueError(f"{stage_id}: runtime stream file identity mismatch")
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
    result["path"] = str(path.resolve())
    return result


def materialize_semantic_runtime_constants(
    reference: dict[str, Any],
    semantic_adapter: dict[str, Any],
    out_dir: Path,
    *,
    semantic_adapter_sha256: str,
) -> dict[str, Any]:
    import torch

    out_dir = out_dir.resolve()
    runtime_records = reference.get("reference", {}).get("semantic_runtime_inputs", {})
    stream_specs = semantic_adapter.get("semantic_runtime_streams", {})
    if not isinstance(stream_specs, dict):
        raise ValueError("model semantic adapter semantic_runtime_streams is not an object")
    streams = []
    blockers: list[str] = []
    for consumer_op, stream_spec in stream_specs.items():
        if not isinstance(stream_spec, dict):
            blockers.append(f"runtime stream specification is malformed for {consumer_op}")
            continue
        targets_spec = stream_spec.get("targets", {})
        source_order = [str(value) for value in stream_spec.get("source_order", [])]
        if not isinstance(targets_spec, dict) or set(source_order) != set(targets_spec):
            blockers.append(f"runtime stream source_order/targets disagree for {consumer_op}")
            continue
        words: list[int] = []
        targets = []
        for source_key in source_order:
            spec = targets_spec.get(source_key, {})
            record = runtime_records.get(source_key, {}) if isinstance(runtime_records, dict) else {}
            source_path = Path(str(record.get("path") or ""))
            if not source_path.is_file() or sha256_file(source_path) != record.get("file_sha256"):
                blockers.append(f"runtime semantic tensor file/hash mismatch: {source_key}")
                continue
            tensor = torch.load(source_path, map_location="cpu", weights_only=True)
            if tensor_sha256(tensor) != record.get("tensor_sha256"):
                blockers.append(f"runtime semantic tensor value hash mismatch: {source_key}")
                continue
            source_axes = [str(value) for value in spec.get("source_axis_order", [])]
            drop_axes = [int(value) for value in spec.get("drop_singleton_axes", [])]
            shape = [int(value) for value in tensor.shape]
            try:
                logical_shape, logical_axes = logical_shape_and_axes(shape, source_axes, drop_axes)
                target_words, packing = tensor_u32_words(tensor, str(spec.get("storage_dtype") or ""))
            except ValueError as exc:
                blockers.append(f"{source_key}: {exc}")
                continue
            offset = len(words)
            words.extend(target_words)
            targets.append(
                {
                    "source_key": source_key,
                    "target_id": spec.get("target_id"),
                    "semantic_role": spec.get("semantic_role"),
                    "source_path": str(source_path.resolve()),
                    "source_file_sha256": record.get("file_sha256"),
                    "source_tensor_sha256": record.get("tensor_sha256"),
                    "source_dtype": record.get("dtype"),
                    "source_shape": shape,
                    "source_axis_order": source_axes,
                    "dropped_singleton_axes": drop_axes,
                    "logical_shape": logical_shape,
                    "logical_axis_order": logical_axes,
                    "packing": packing,
                    "stream_range": {
                        "word_offset": offset,
                        "word_count": len(target_words),
                        "word_end_exclusive": len(words),
                    },
                    "address_formula": spec.get("address_formula"),
                    "sharing": spec.get("sharing"),
                }
            )
        stream_file = write_u32_stream(out_dir / f"{consumer_op}_runtime_constants.u32.memh", words) if words else None
        stream_contract = {
            "consumer_op": consumer_op,
            "source_order": source_order,
            "targets": targets,
            "stream": stream_file,
            "loader": {
                "protocol": "ready_valid_addressed_words",
                "data_width_bits": 32,
                "address_order": "strictly ascending from zero",
                "last_assertion": "true exactly on the final accepted word",
                "stimulus_allowed_before_last_accepted_word": False,
            },
        }
        stream_contract["contract_sha256"] = sha256_json(stream_contract)
        streams.append(stream_contract)
    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not blockers else "fail",
        "blockers": blockers,
        "model_semantic_adapter_sha256": semantic_adapter_sha256,
        "streams": streams,
        "policy": {
            "values_come_from_same_target_model_inference_as_golden_outputs": True,
            "rtl_outputs_are_never_read": True,
            "runtime_constants_are_inputs_not_expected_outputs": True,
            "hardware_must_consume_the_hash_bound_stream_before_stimulus": True,
            "framework_core_is_model_independent_and_consumes_adapter_declared_layouts": True,
        },
    }
    contract["contract_sha256"] = sha256_json(contract)
    contract_path = out_dir / "semantic_runtime_constant_contract.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    contract["path"] = str(contract_path)
    contract["file_sha256"] = sha256_file(contract_path)
    return contract
