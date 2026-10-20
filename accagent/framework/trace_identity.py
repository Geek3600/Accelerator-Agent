"""Shared identity projection for adaptive Stage-6 trace replays."""

from __future__ import annotations

from typing import Any


TARGETED_TRACE_ENV_KEYS = (
    "SPATIALACC_BOUNDARY_TRACE",
    "SPATIALACC_CHECKPOINT_REPLAY",
    "SPATIALACC_TARGETED_REPLAY",
    "SPATIALACC_TARGET_BOUNDARY",
    "SPATIALACC_TARGETED_TRACE_SCOPE",
)


def targeted_trace_env(environment: dict[str, Any] | None) -> dict[str, str]:
    """Keep every trace control that can change the observed VCS run."""

    values = environment if isinstance(environment, dict) else {}
    keys = set(TARGETED_TRACE_ENV_KEYS)
    keys.update(
        str(key)
        for key, value in values.items()
        if str(key).startswith("SPATIALACC_TRACE_") and value is not None
    )
    return {
        key: str(values.get(key) or "")
        for key in sorted(keys)
        if key in TARGETED_TRACE_ENV_KEYS or values.get(key) is not None
    }
