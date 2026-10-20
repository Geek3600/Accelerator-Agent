"""Shared helpers for the input preparation stage."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FRAMEWORK_ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE_DIR = FRAMEWORK_ROOT / "templates" / "operator_chisel"
DEFAULT_BOARD_MATERIALS_DIR = FRAMEWORK_ROOT / "input_materials" / "board"
DEFAULT_QUANTIZATION_MATERIALS_DIR = FRAMEWORK_ROOT / "input_materials" / "quantization"
DEFAULT_TOOL_MATERIALS_DIR = FRAMEWORK_ROOT / "input_materials" / "tools"


class InputPreparationError(ValueError):
    pass


def canonical_tool_role(value: Any) -> str:
    """Normalize separator-only variations in tool role identifiers."""

    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def normalized_functional_verification_role(value: Any) -> str:
    """Map detailed functional-verification capabilities to their tool role."""

    role = canonical_tool_role(value)
    if role == "functional_verification":
        return role
    if role.startswith("functional_verification_") and not any(
        token in role for token in ("alternative", "unconfigured", "fallback")
    ):
        return "functional_verification"
    return ""


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
