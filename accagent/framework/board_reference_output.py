"""Select the real-model output that terminates a board-validation prefix."""

from __future__ import annotations

import re
from typing import Any

from accagent.framework.board_validation_scope import BoardValidationScope


class BoardReferenceOutputError(ValueError):
    """Raised when a target-model reference lacks the requested prefix output."""


def _record_layer_index(record: dict[str, Any], position: int) -> int | None:
    value = record.get("layer_index")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    module = str(record.get("module") or "")
    match = re.search(r"(?:^|[_./-])(\d+)$", module)
    if match:
        return int(match.group(1))
    return position


def select_board_reference_output(
    reference: dict[str, Any],
    scope: BoardValidationScope,
) -> dict[str, Any]:
    """Return the immutable capture at the final layer of ``scope``.

    Full-model runs retain the model's final-output artifact.  Every partial
    prefix binds the capture emitted by its final Transformer layer instead of
    reusing layer zero for all partial depths.
    """

    root = reference.get("reference")
    root = root if isinstance(root, dict) else {}
    if scope.covers_full_model:
        output = root.get("full_model_output")
        if not isinstance(output, dict):
            raise BoardReferenceOutputError("full-model output capture is missing")
        return {
            **output,
            "source_capture": str(
                output.get("source_capture")
                or f"model_output_layer_{scope.reference_output_layer_index}"
            ),
            "payload_key": None,
            "reference_kind": "full_model_output",
            "target_layer_count": scope.validation_layer_count,
        }

    selected: dict[str, Any] | None = None
    for position, row in enumerate(root.get("layer_output_records", [])):
        if not isinstance(row, dict):
            continue
        if _record_layer_index(row, position) == scope.reference_output_layer_index:
            selected = row
            break
    if selected is None:
        raise BoardReferenceOutputError(
            "target-model layer-output capture is missing for validation layer "
            f"{scope.reference_output_layer_index}"
        )
    path = selected.get("tensor_path")
    file_sha256 = selected.get("tensor_file_sha256")
    tensor_sha256 = selected.get("output_sha256")
    shape = selected.get("output_shape")
    dtype = selected.get("output_dtype")
    if not all((path, file_sha256, tensor_sha256, isinstance(shape, list), dtype)):
        raise BoardReferenceOutputError(
            "target-model layer-output capture lacks tensor provenance for validation layer "
            f"{scope.reference_output_layer_index}"
        )
    return {
        "path": path,
        "file_sha256": file_sha256,
        "tensor_sha256": tensor_sha256,
        "shape": shape,
        "dtype": dtype,
        "source_capture": str(
            selected.get("module") or f"layer_{scope.reference_output_layer_index}"
        ),
        "payload_key": "output",
        "reference_kind": "layer_output_record",
        "target_layer_count": scope.validation_layer_count,
    }


__all__ = [
    "BoardReferenceOutputError",
    "select_board_reference_output",
]
