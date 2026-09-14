"""Resolve quantitative comparison tolerances for verification artifacts."""

from __future__ import annotations

import copy
import math
from typing import Any


NUMERIC_COMPARISON_FIELDS = ("atol", "rtol", "max_mismatch_fraction")
LOOSE_DEFAULT_POLICY_ID = "spatialaccagent.loose_numeric_compare.v1"
LOOSE_NUMERIC_COMPARISON_DEFAULTS = {
    "atol": 0.1,
    "rtol": 0.1,
    "max_mismatch_fraction": 0.05,
}


def _valid_value(name: str, value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    if name == "max_mismatch_fraction" and parsed > 1:
        return None
    return parsed


def _comparison_candidates(tolerance: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for name in ("comparison", "operator", "stage"):
        value = tolerance.get(name)
        if isinstance(value, dict):
            candidates.append(value)
    candidates.append(tolerance)
    return candidates


def resolve_numeric_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with a complete, provenance-marked comparison policy.

    Values supplied by the current-run policy take precedence. Missing,
    non-finite, negative, or out-of-range values use the loose framework
    defaults. The function is idempotent so cached Stage 0 artifacts retain
    their original per-field provenance.
    """

    resolved = copy.deepcopy(policy)
    tolerance = resolved.get("tolerance")
    if not isinstance(tolerance, dict):
        tolerance = {}

    previous_resolution = resolved.get("_numeric_comparison_resolution")
    previous_sources = (
        previous_resolution.get("field_sources", {})
        if isinstance(previous_resolution, dict)
        and isinstance(previous_resolution.get("field_sources"), dict)
        else {}
    )
    candidates = _comparison_candidates(tolerance)
    comparison: dict[str, Any] = {}
    field_sources: dict[str, str] = {}
    defaulted_fields: list[str] = []

    for name in NUMERIC_COMPARISON_FIELDS:
        selected = None
        selected_candidate: dict[str, Any] | None = None
        for candidate in candidates:
            selected = _valid_value(name, candidate.get(name))
            if selected is not None:
                selected_candidate = candidate
                break
        if selected is None:
            selected = LOOSE_NUMERIC_COMPARISON_DEFAULTS[name]
            source = "framework_default"
            defaulted_fields.append(name)
        else:
            prior_source = str(previous_sources.get(name) or "")
            candidate_source = str((selected_candidate or {}).get("source") or "")
            if prior_source == "framework_default" or candidate_source == "framework_default":
                source = "framework_default"
                defaulted_fields.append(name)
            else:
                source = "provided_policy"
        comparison[name] = selected
        field_sources[name] = source

    unique_sources = set(field_sources.values())
    comparison["source"] = unique_sources.pop() if len(unique_sources) == 1 else "mixed"
    comparison["default_policy_id"] = LOOSE_DEFAULT_POLICY_ID
    tolerance["comparison"] = comparison
    resolved["tolerance"] = tolerance
    resolved["_numeric_comparison_resolution"] = {
        "schema_version": "spatialaccagent.numeric_comparison_resolution.v1",
        "default_policy_id": LOOSE_DEFAULT_POLICY_ID,
        "defaults": dict(LOOSE_NUMERIC_COMPARISON_DEFAULTS),
        "resolved": {name: comparison[name] for name in NUMERIC_COMPARISON_FIELDS},
        "field_sources": field_sources,
        "defaulted_fields": defaulted_fields,
        "provided_values_take_precedence": True,
        "dut_outputs_used_for_resolution": False,
    }

    notes = resolved.get("notes")
    if not isinstance(notes, list):
        notes = []
    note = (
        "Missing or invalid quantitative comparison values use "
        f"{LOOSE_DEFAULT_POLICY_ID}; current-run provided values take precedence."
    )
    if note not in notes:
        notes.append(note)
    resolved["notes"] = notes
    return resolved


def numeric_comparison(policy: dict[str, Any]) -> tuple[dict[str, float], dict[str, Any]]:
    """Return the resolved three-field comparison and its provenance."""

    resolved = resolve_numeric_policy(policy)
    comparison = resolved["tolerance"]["comparison"]
    values = {name: float(comparison[name]) for name in NUMERIC_COMPARISON_FIELDS}
    return values, resolved["_numeric_comparison_resolution"]
