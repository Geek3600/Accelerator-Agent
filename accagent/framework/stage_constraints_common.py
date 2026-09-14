"""Shared helpers for constraint extraction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConstraintExtractionError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ConstraintExtractionError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def resolve_input(run_dir: Path, prepared_inputs: dict[str, Any], name: str) -> Path:
    inputs = prepared_inputs.get("inputs", {})
    value = inputs.get(name)
    if not isinstance(value, str) or not value:
        raise ConstraintExtractionError(f"prepared_inputs missing input path: {name}")
    path = Path(value)
    if not path.is_absolute():
        path = run_dir / path
    return path


def artifact_id(name: str) -> str:
    return f"artifact.input.{name}"


def make_input_artifact(name: str, path: Path, constraint_ids: list[str]) -> dict[str, Any]:
    return {
        "id": artifact_id(name),
        "path": str(path),
        "type": f"input.{name}",
        "nodes": [],
        "edges": [],
        "constraints": constraint_ids,
        "freshness": "fresh",
        "producer_transition": None,
    }
