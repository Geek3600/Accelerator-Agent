"""Shared helpers for the input preparation stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FRAMEWORK_ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_DIR = FRAMEWORK_ROOT / "templates" / "operator_chisel"
DEFAULT_BOARD_MATERIALS_DIR = FRAMEWORK_ROOT / "input_materials" / "board"
DEFAULT_QUANTIZATION_MATERIALS_DIR = FRAMEWORK_ROOT / "input_materials" / "quantization"
DEFAULT_TOOL_MATERIALS_DIR = FRAMEWORK_ROOT / "input_materials" / "tools"


class InputPreparationError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise InputPreparationError(f"expected JSON object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def copy_json(src: Path, dst: Path) -> dict[str, Any]:
    data = read_json(src)
    write_json(dst, data)
    return data


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)
