"""Separate immutable model coverage from the current board-validation workload."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


SCHEMA_VERSION = "spatialaccagent.board_validation_scope.v1"
FULL_MODEL_MODE = "full_model_pipeline_liveness"
SINGLE_LAYER_MODE = "single_transformer_layer_board_liveness"
PREFIX_MODEL_MODE = "configurable_prefix_pipeline_liveness"


class BoardValidationScopeError(ValueError):
    """Raised when a board-validation scope is incomplete or contradictory."""


@dataclass(frozen=True)
class BoardValidationScope:
    mode: str
    model_layer_count: int
    layer_indices: tuple[int, ...]

    @property
    def validation_layer_count(self) -> int:
        return len(self.layer_indices)

    @property
    def reference_output_layer_index(self) -> int:
        return self.layer_indices[-1]

    @property
    def covers_full_model(self) -> bool:
        return self.validation_layer_count == self.model_layer_count

    @property
    def requires_next_layer_prefetch(self) -> bool:
        return self.validation_layer_count > 1

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "mode": self.mode,
            "model_layer_count": self.model_layer_count,
            "validation_layer_indices": list(self.layer_indices),
            "validation_layer_count": self.validation_layer_count,
            "reference_output_layer_index": self.reference_output_layer_index,
            "covers_full_model": self.covers_full_model,
            "requires_next_layer_prefetch": self.requires_next_layer_prefetch,
        }
        payload["contract_sha256"] = canonical_sha256(payload)
        return payload


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BoardValidationScopeError(f"{label} must be a positive integer")
    return value


def resolve_board_validation_scope(
    task_card: dict[str, Any],
    model: dict[str, Any],
) -> BoardValidationScope:
    """Resolve a prefix workload while retaining the complete target-model authority."""

    if not isinstance(task_card, dict) or not isinstance(model, dict):
        raise BoardValidationScopeError("task card and model config must be JSON objects")
    model_layers = _positive_int(
        model.get("num_layers", model.get("num_hidden_layers")),
        "model layer count",
    )
    policy = task_card.get("acceptance_policy")
    policy = policy if isinstance(policy, dict) else {}
    mode = str(policy.get("board_validation_mode") or FULL_MODEL_MODE)
    raw_indices = policy.get("board_validation_layer_indices")
    raw_count = policy.get("board_validation_layer_count")
    if mode not in {FULL_MODEL_MODE, SINGLE_LAYER_MODE, PREFIX_MODEL_MODE}:
        raise BoardValidationScopeError(f"unsupported board_validation_mode: {mode!r}")
    if raw_count is not None:
        layer_count = _positive_int(raw_count, "board_validation_layer_count")
        if layer_count > model_layers:
            raise BoardValidationScopeError(
                "board_validation_layer_count exceeds the target model layer count"
            )
        count_indices = list(range(layer_count))
    else:
        count_indices = None
    if raw_indices is None:
        if count_indices is not None:
            indices = count_indices
        elif mode == SINGLE_LAYER_MODE:
            indices = [0]
        elif mode == FULL_MODEL_MODE:
            indices = list(range(model_layers))
        else:
            raise BoardValidationScopeError(
                "configurable_prefix_pipeline_liveness requires "
                "board_validation_layer_count or board_validation_layer_indices"
            )
    elif isinstance(raw_indices, list) and raw_indices:
        indices = list(raw_indices)
        if count_indices is not None and indices != count_indices:
            raise BoardValidationScopeError(
                "board_validation_layer_indices conflicts with "
                "board_validation_layer_count"
            )
    else:
        raise BoardValidationScopeError("board_validation_layer_indices must be a non-empty array")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in indices):
        raise BoardValidationScopeError("board_validation_layer_indices must contain integers")
    if indices != list(range(len(indices))):
        raise BoardValidationScopeError(
            "board validation layers must be a contiguous prefix starting at layer 0"
        )
    if indices[-1] >= model_layers:
        raise BoardValidationScopeError("board validation layer is outside the target model")
    if mode == SINGLE_LAYER_MODE and len(indices) != 1:
        raise BoardValidationScopeError(
            "single_transformer_layer_board_liveness requires exactly one layer"
        )
    if mode == FULL_MODEL_MODE and len(indices) != model_layers:
        raise BoardValidationScopeError(
            "full_model_pipeline_liveness requires every target model layer"
        )
    if mode == PREFIX_MODEL_MODE and not indices:
        raise BoardValidationScopeError(
            "configurable_prefix_pipeline_liveness requires at least one layer"
        )
    return BoardValidationScope(mode, model_layers, tuple(indices))


def validation_scope_from_plan(
    plan: dict[str, Any],
    *,
    model_layer_count: int,
) -> BoardValidationScope:
    """Validate the deterministic image-plan layer order against the model authority."""

    image = plan.get("image") if isinstance(plan.get("image"), dict) else {}
    indices = image.get("layer_order")
    if not isinstance(indices, list) or not indices:
        raise BoardValidationScopeError("board workload image plan layer_order is missing")
    task_card = {
        "acceptance_policy": {
            "board_validation_mode": (
                FULL_MODEL_MODE
                if len(indices) == model_layer_count
                else PREFIX_MODEL_MODE
            ),
            "board_validation_layer_indices": indices,
        }
    }
    return resolve_board_validation_scope(task_card, {"num_layers": model_layer_count})


def validation_scope_record_errors(
    scope: BoardValidationScope,
    record: dict[str, Any],
    *,
    allowed_statuses: set[str] | None = None,
    require_accelerator_scope: bool = False,
) -> list[str]:
    """Check that one board artifact describes exactly the active layer range.

    ``all_target_layers`` describes whether the active range happens to be the
    whole model.  It must not be used as a proxy for whether every layer in a
    smaller configured range is present.  The count and ordered indices remain
    the direct proof of the current workload.
    """

    if not isinstance(record, dict):
        return ["board validation record is not an object"]

    errors: list[str] = []
    if allowed_statuses is not None and record.get("status") not in allowed_statuses:
        errors.append("record status is not accepted for board validation")
    if require_accelerator_scope and record.get("accelerator_scope") != "transformer_blocks_only":
        errors.append("record accelerator scope is not transformer_blocks_only")
    if record.get("model_layer_count") != scope.model_layer_count:
        errors.append("record model_layer_count does not match the target model")
    if record.get("validation_layer_indices") != list(scope.layer_indices):
        errors.append("record validation_layer_indices do not match the current board workload")
    if record.get("bound_layer_count") != scope.validation_layer_count:
        errors.append("record bound_layer_count does not match the current board workload")
    if record.get("all_target_layers") is not scope.covers_full_model:
        errors.append("record all_target_layers does not match whether the current workload covers the full model")
    return errors


__all__ = [
    "BoardValidationScope",
    "BoardValidationScopeError",
    "FULL_MODEL_MODE",
    "PREFIX_MODEL_MODE",
    "SCHEMA_VERSION",
    "SINGLE_LAYER_MODE",
    "canonical_sha256",
    "resolve_board_validation_scope",
    "validation_scope_record_errors",
    "validation_scope_from_plan",
]
