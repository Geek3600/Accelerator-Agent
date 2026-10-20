"""Stable identities for framework-owned semantic contracts.

Contract hashes are useful only when the hashed payload is an explicit
semantic identity.  This module keeps that calculation in one place and
allows a contract family to provide deterministic legacy projections for
backward-compatible materialized artifacts.  It deliberately does not make
arbitrary hash mismatches pass.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Iterable
from typing import Any


Projection = Callable[[Any], Any]


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def without_fields(value: Any, fields: Iterable[str]) -> Any:
    """Copy a top-level contract and remove only explicitly derived fields."""

    projection = copy.deepcopy(value)
    if isinstance(projection, dict):
        for field in fields:
            projection.pop(str(field), None)
    return projection


def identity_sha256(
    value: Any,
    *,
    projection: Projection | None = None,
    excluded_fields: Iterable[str] = (),
) -> str:
    """Hash a declared semantic projection, excluding only derived fields."""

    payload = projection(value) if projection is not None else copy.deepcopy(value)
    payload = without_fields(payload, excluded_fields)
    return canonical_sha256(payload)


def hash_matches(
    value: Any,
    declared_hash: Any,
    *,
    projection: Projection | None = None,
    excluded_fields: Iterable[str] = (),
    legacy_projections: Iterable[Projection] = (),
) -> bool:
    candidate = str(declared_hash or "").lower()
    if not candidate:
        return False
    expected = identity_sha256(
        value,
        projection=projection,
        excluded_fields=excluded_fields,
    )
    if candidate == expected:
        return True
    return any(
        candidate
        == identity_sha256(
            value,
            projection=legacy_projection,
            excluded_fields=excluded_fields,
        )
        for legacy_projection in legacy_projections
    )
