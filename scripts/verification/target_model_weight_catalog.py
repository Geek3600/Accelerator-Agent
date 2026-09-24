#!/usr/bin/env python3
"""Catalog and hash the real Transformer-block weights for a target model."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "spatialaccagent.target_model_weight_manifest.v1"
CHECKPOINT_INVENTORY_SCHEMA_VERSION = (
    "spatialaccagent.target_model_checkpoint_inventory.v1"
)


class CatalogError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise CatalogError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def resolve_snapshot(path: Path) -> tuple[Path, str]:
    root = path.expanduser().resolve()
    if (root / "config.json").is_file():
        return root, root.name
    ref = root / "refs" / "main"
    if ref.is_file():
        revision = ref.read_text(encoding="utf-8").strip()
        snapshot = root / "snapshots" / revision
        if (snapshot / "config.json").is_file():
            return snapshot.resolve(), revision
    candidates = sorted((root / "snapshots").glob("*/config.json"))
    if candidates:
        return candidates[-1].parent.resolve(), candidates[-1].parent.name
    raise CatalogError(f"cannot resolve model snapshot under {root}")


def checkpoint_files(snapshot: Path) -> list[Path]:
    index_path = snapshot / "model.safetensors.index.json"
    if index_path.is_file():
        index = read_json(index_path)
        weight_map = index.get("weight_map", {}) if isinstance(index.get("weight_map"), dict) else {}
        names = sorted({str(name) for name in weight_map.values() if str(name)})
        paths = [snapshot / name for name in names]
    else:
        paths = sorted(snapshot.glob("*.safetensors"))
    missing = [str(path) for path in paths if not path.is_file()]
    if not paths or missing:
        raise CatalogError(f"safetensors checkpoint files are missing: {missing or snapshot}")
    return paths


def parse_safetensors(path: Path, file_sha256: str) -> tuple[int, list[dict[str, Any]]]:
    with path.open("rb") as stream:
        raw_len = stream.read(8)
        if len(raw_len) != 8:
            raise CatalogError(f"invalid safetensors header: {path}")
        (header_len,) = struct.unpack("<Q", raw_len)
        header_raw = stream.read(header_len)
    try:
        header = json.loads(header_raw)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"invalid safetensors header JSON in {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    max_end = 0
    for name, metadata in sorted(header.items()):
        if name == "__metadata__":
            continue
        if not isinstance(metadata, dict):
            raise CatalogError(f"invalid tensor metadata for {name}")
        offsets = metadata.get("data_offsets")
        shape = metadata.get("shape")
        if not isinstance(offsets, list) or len(offsets) != 2:
            raise CatalogError(f"invalid data offsets for {name}")
        if not isinstance(shape, list) or not all(isinstance(dim, int) and dim >= 0 for dim in shape):
            raise CatalogError(f"invalid shape for {name}")
        start, end = [int(value) for value in offsets]
        if start < 0 or end < start:
            raise CatalogError(f"invalid data range for {name}")
        max_end = max(max_end, end)
        rows.append(
            {
                "name": name,
                "dtype": str(metadata.get("dtype")),
                "shape": shape,
                "data_offsets": [start, end],
                "source_file": str(path),
                "source_file_sha256": file_sha256,
                "source_data_base": 8 + header_len,
            }
        )
    if 8 + header_len + max_end != path.stat().st_size:
        raise CatalogError(f"safetensors offsets do not cover the complete file: {path}")
    return header_len, rows


def bind_transformer_scope(
    rows: list[dict[str, Any]],
    patterns: list[str],
    num_layers: int,
) -> tuple[list[dict[str, Any]], list[str], str]:
    candidates = [re.compile(pattern) for pattern in patterns]
    selected: list[dict[str, Any]] = []
    excluded: list[str] = []
    used_pattern = ""
    for row in rows:
        matched = None
        matched_pattern = ""
        for pattern, compiled in zip(patterns, candidates):
            match = compiled.fullmatch(str(row["name"]))
            if match:
                matched = match
                matched_pattern = pattern
                break
        if matched is None:
            excluded.append(str(row["name"]))
            continue
        if "layer" not in matched.groupdict() or "suffix" not in matched.groupdict():
            raise CatalogError("decoder-layer regex must define named groups 'layer' and 'suffix'")
        layer_index = int(matched.group("layer"))
        if layer_index >= num_layers:
            excluded.append(str(row["name"]))
            continue
        if used_pattern and used_pattern != matched_pattern:
            raise CatalogError("multiple decoder-layer tensor patterns matched one checkpoint")
        used_pattern = matched_pattern
        selected.append({**row, "layer_index": layer_index, "parameter_suffix": matched.group("suffix")})
    if not used_pattern:
        raise CatalogError("no checkpoint tensor matched the adapter decoder-layer patterns")
    return selected, sorted(excluded), used_pattern


def hash_tensor_slices(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    streams: dict[str, Any] = {}
    try:
        result = []
        for row in rows:
            source = str(row["source_file"])
            if source not in streams:
                streams[source] = Path(source).open("rb")
            stream = streams[source]
            start, end = [int(value) for value in row["data_offsets"]]
            stream.seek(int(row["source_data_base"]) + start)
            remaining = end - start
            digest = hashlib.sha256()
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise CatalogError(f"short read while hashing {row['name']}")
                digest.update(chunk)
                remaining -= len(chunk)
            result.append({**row, "source_byte_count": end - start, "source_slice_sha256": digest.hexdigest()})
        return result
    finally:
        for stream in streams.values():
            stream.close()


def validate_layer_coverage(rows: list[dict[str, Any]], num_layers: int) -> tuple[list[int], list[str]]:
    suffixes: dict[int, set[str]] = {}
    for row in rows:
        suffixes.setdefault(int(row["layer_index"]), set()).add(str(row["parameter_suffix"]))
    expected_layers = list(range(num_layers))
    baseline = suffixes.get(0, set())
    inconsistent = [index for index in expected_layers if suffixes.get(index, set()) != baseline]
    if not baseline or sorted(suffixes) != expected_layers or inconsistent:
        raise CatalogError(
            f"incomplete Transformer-block weight scope: layers={sorted(suffixes)} inconsistent={inconsistent}"
        )
    return expected_layers, sorted(baseline)


def adapter_pattern_match_facts(
    tensor_names: list[str], patterns: list[str]
) -> list[dict[str, Any]]:
    """Record adapter-regex observations without treating them as validation."""

    facts: list[dict[str, Any]] = []
    for pattern in patterns:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            facts.append(
                {
                    "pattern": pattern,
                    "status": "invalid",
                    "error": str(exc),
                    "matched_tensor_names": [],
                }
            )
            continue
        matches = [name for name in tensor_names if compiled.fullmatch(name)]
        facts.append(
            {
                "pattern": pattern,
                "status": "matched" if matches else "no_match",
                "named_groups": sorted(compiled.groupindex),
                "matched_tensor_names": matches,
            }
        )
    return facts


def checkpoint_inventory(
    *,
    model_id: str,
    snapshot: Path,
    revision: str,
    config_path: Path,
    config: dict[str, Any],
    checkpoint_fingerprint: str,
    checkpoint_file_rows: list[dict[str, Any]],
    tensor_names: list[str],
    semantic_adapter_path: Path,
    semantic_adapter_sha256: str,
    decoder_layer_tensor_patterns: list[str],
) -> dict[str, Any]:
    """Return checkpoint facts for a bounded adapter-repair decision.

    This diagnostic artifact is not a Transformer-block scope catalog or
    evidence that a DUT consumed weights.
    """

    return {
        "schema_version": CHECKPOINT_INVENTORY_SCHEMA_VERSION,
        "status": "diagnostic",
        "purpose": (
            "checkpoint and adapter facts for repair diagnosis only; this is not "
            "a Transformer-block scope manifest or verification-pass evidence"
        ),
        "model_id": model_id,
        "snapshot": {"snapshot_dir": str(snapshot), "revision": revision},
        "config": {
            "path": str(config_path),
            "sha256": sha256_file(config_path),
            "model_type": config.get("model_type"),
            "architectures": config.get("architectures"),
            "num_hidden_layers": config.get("num_hidden_layers"),
        },
        "checkpoint": {
            "fingerprint_sha256": checkpoint_fingerprint,
            "shards": [
                {
                    "basename": Path(str(row["path"])).name,
                    "size_bytes": row["size_bytes"],
                    "sha256": row["sha256"],
                    "header_len": row["header_len"],
                    "tensor_count": row["tensor_count"],
                }
                for row in checkpoint_file_rows
            ],
            "header_tensor_names": tensor_names,
        },
        "semantic_adapter": {
            "path": str(semantic_adapter_path),
            "sha256": semantic_adapter_sha256,
            "decoder_layer_tensor_patterns": decoder_layer_tensor_patterns,
            "pattern_match_facts": adapter_pattern_match_facts(
                tensor_names,
                decoder_layer_tensor_patterns,
            ),
        },
    }


def generate(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    out_dir = (args.out_dir or run_dir / "verification" / "model_weights").resolve()
    snapshot, revision = resolve_snapshot(args.model_dir)
    config = read_json(snapshot / "config.json")
    adapter = read_json(args.semantic_adapter.resolve())
    if adapter.get("accelerator_scope") != "transformer_blocks_only":
        raise CatalogError("model semantic adapter scope must be transformer_blocks_only")
    model_config = read_json(run_dir / "input" / "model_config.json")
    num_layers = int(model_config.get("num_layers") or config.get("num_hidden_layers") or 0)
    if num_layers <= 0 or int(config.get("num_hidden_layers") or num_layers) != num_layers:
        raise CatalogError("target model and run configuration layer counts do not match")

    files = checkpoint_files(snapshot)
    file_rows = []
    all_rows: list[dict[str, Any]] = []
    for path in files:
        file_hash = sha256_file(path)
        header_len, rows = parse_safetensors(path, file_hash)
        file_rows.append(
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": file_hash,
                "header_len": header_len,
                "tensor_count": len(rows),
            }
        )
        all_rows.extend(rows)
    names = [str(row["name"]) for row in all_rows]
    if len(set(names)) != len(names):
        raise CatalogError("duplicate tensor names exist across checkpoint shards")
    checkpoint_fingerprint = canonical_sha256(
        [{"path": Path(row["path"]).name, "size_bytes": row["size_bytes"], "sha256": row["sha256"]} for row in file_rows]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "weight_manifest.json"
    full_catalog_path = out_dir / "full_tensor_catalog.json"
    accelerator_catalog_path = out_dir / "transformer_block_weight_catalog.json"
    checkpoint_inventory_path = out_dir / "checkpoint_inventory.json"
    hashes_path = out_dir / "artifact_hashes.json"
    semantic_adapter_path = args.semantic_adapter.resolve()
    semantic_adapter_hash = sha256_file(semantic_adapter_path)
    patterns = [str(value) for value in adapter.get("decoder_layer_tensor_patterns", [])]
    write_json(
        checkpoint_inventory_path,
        checkpoint_inventory(
            model_id=args.model_id,
            snapshot=snapshot,
            revision=revision,
            config_path=snapshot / "config.json",
            config=config,
            checkpoint_fingerprint=checkpoint_fingerprint,
            checkpoint_file_rows=file_rows,
            tensor_names=names,
            semantic_adapter_path=semantic_adapter_path,
            semantic_adapter_sha256=semantic_adapter_hash,
            decoder_layer_tensor_patterns=patterns,
        ),
    )
    scoped, excluded, used_pattern = bind_transformer_scope(
        all_rows,
        patterns,
        num_layers,
    )
    scoped = hash_tensor_slices(scoped)
    layer_ids, suffixes = validate_layer_coverage(scoped, num_layers)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass",
        "model_id": args.model_id,
        "snapshot": {"snapshot_dir": str(snapshot), "revision": revision},
        "checkpoint_fingerprint_sha256": checkpoint_fingerprint,
        "checkpoint_files": file_rows,
        "weights": {
            "format": "safetensors",
            "tensor_count": len(all_rows),
            "layer_ids": layer_ids,
            "offsets_valid": True,
            "checkpoint_fingerprint_sha256": checkpoint_fingerprint,
        },
        "config": {
            "path": str(snapshot / "config.json"),
            "model_type": config.get("model_type"),
            "architectures": config.get("architectures"),
            "hidden_size": config.get("hidden_size"),
            "intermediate_size": config.get("intermediate_size"),
            "num_hidden_layers": config.get("num_hidden_layers"),
            "num_attention_heads": config.get("num_attention_heads"),
            "num_key_value_heads": config.get("num_key_value_heads"),
            "torch_dtype": config.get("torch_dtype"),
        },
        "semantic_adapter": {
            "path": str(args.semantic_adapter.resolve()),
            "sha256": semantic_adapter_hash,
            "contract": adapter,
        },
        "accelerator_scope": {
            "accelerator_scope": "transformer_blocks_only",
            "target_layer_count": num_layers,
            "layer_ids": layer_ids,
            "tensor_count": len(scoped),
            "per_layer_tensor_count": len(suffixes),
            "tensor_suffixes": suffixes,
            "scope_coverage_complete": True,
            "decoder_layer_tensor_pattern": used_pattern,
        },
        "validation": {
            "complete_checkpoint_tensor_catalog": len(all_rows) == sum(row["tensor_count"] for row in file_rows),
            "complete_accelerator_scope_tensor_catalog": True,
            "accelerator_scope_is_transformer_blocks_only": True,
        },
    }
    write_json(manifest_path, manifest)
    write_json(
        full_catalog_path,
        {
            "schema_version": "spatialaccagent.complete_checkpoint_tensor_catalog.v1",
            "status": "pass",
            "model_id": args.model_id,
            "revision": revision,
            "checkpoint_files": file_rows,
            "source_checkpoint_sha256": checkpoint_fingerprint,
            "tensor_count": len(all_rows),
            "scope_coverage_complete": True,
            "catalog_scope": "complete_checkpoint_for_source_provenance",
            "tensors": all_rows,
        },
    )
    write_json(
        accelerator_catalog_path,
        {
            "schema_version": "spatialaccagent.transformer_block_weight_catalog.v1",
            "status": "pass",
            "model_id": args.model_id,
            "revision": revision,
            "source_checkpoint_sha256": checkpoint_fingerprint,
            **manifest["accelerator_scope"],
            "tensors": scoped,
            "excluded_non_accelerator_tensors": excluded,
            "semantic_adapter_sha256": semantic_adapter_hash,
            "policy": {
                "dut_must_consume_every_catalog_tensor": True,
                "non_transformer_model_regions_are_out_of_scope": True,
            },
        },
    )
    write_json(
        hashes_path,
        {
            "schema_version": "spatialaccagent.model_weight_artifact_hashes.v1",
            "status": "pass",
            "checkpoint_fingerprint_sha256": checkpoint_fingerprint,
            "artifacts": [
                {"role": "target_model_checkpoint", "sha256": checkpoint_fingerprint, "files": file_rows},
                {"role": "weight_manifest", "path": str(manifest_path), "sha256": sha256_file(manifest_path)},
                {"role": "complete_checkpoint_tensor_catalog", "path": str(full_catalog_path), "sha256": sha256_file(full_catalog_path)},
                {"role": "transformer_block_weight_catalog", "path": str(accelerator_catalog_path), "sha256": sha256_file(accelerator_catalog_path)},
                {"role": "model_semantic_adapter", "path": str(args.semantic_adapter.resolve()), "sha256": semantic_adapter_hash},
            ],
        },
    )
    return {
        "manifest": str(manifest_path),
        "full_catalog": str(full_catalog_path),
        "accelerator_catalog": str(accelerator_catalog_path),
        "checkpoint_inventory": str(checkpoint_inventory_path),
        "artifact_hashes": str(hashes_path),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--semantic-adapter", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        outputs = generate(args)
    except Exception as exc:
        print(f"target_model_weight_catalog.py: {exc}", file=sys.stderr)
        return 1
    for path in outputs.values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
