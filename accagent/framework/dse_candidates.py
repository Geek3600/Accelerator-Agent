"""Normalize Stage-0 physical DSE tuples without inventing candidates."""

from __future__ import annotations

from itertools import product
from typing import Any


def _positive(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _values(value: Any) -> list[int]:
    if isinstance(value, dict):
        values: Any = None
        for key in (
            "candidate_values",
            "values_in_complete_universe",
            "entries_candidates",
            "candidates",
            "values",
        ):
            if key in value:
                values = value[key]
                break
        if values is None and "fixed" in value:
            values = [value["fixed"]]
    else:
        values = value
    if not isinstance(values, list):
        values = [values] if values is not None else []
    result: list[int] = []
    for item in values:
        parsed = _positive(item)
        if parsed is not None and parsed not in result:
            result.append(parsed)
    return result


def _field(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def _normal_tuple(row: dict[str, Any], index: int) -> dict[str, int]:
    array = row.get("compute_array") if isinstance(row.get("compute_array"), dict) else {}
    lanes = _positive(row.get("lanes"))
    rows = _positive(_field(array, "rows"))
    cols = _positive(_field(array, "cols"))
    fifo_depth = _positive(_field(row, "fifo_depth", "physical_fifo_depth_entries", "physical_fifo_depth"))
    activation_banks = _positive(_field(row, "activation_banks", "activation_bank_count"))
    missing = [
        name
        for name, value in (
            ("lanes", lanes),
            ("compute_array.rows", rows),
            ("compute_array.cols", cols),
            ("physical_fifo_depth", fifo_depth),
            ("activation_bank_count", activation_banks),
        )
        if value is None
    ]
    if missing:
        raise ValueError(f"physical DSE tuple {index} is missing {missing}")
    if rows > lanes or cols > lanes or lanes % rows or lanes % cols or cols & (cols - 1):
        raise ValueError(
            f"physical DSE tuple {index} has illegal PE array {rows}x{cols} for lanes={lanes}"
        )
    return {
        "lanes": lanes,
        "compute_array_rows": rows,
        "compute_array_cols": cols,
        "fifo_depth": fifo_depth,
        "activation_banks": activation_banks,
    }


def _candidate_universe_tuples(search: dict[str, Any]) -> list[dict[str, int]]:
    universe = search.get("candidate_universe")
    if not isinstance(universe, dict):
        return []

    array = universe.get("compute_array") if isinstance(universe.get("compute_array"), dict) else {}
    declared = array.get("legal_compute_array_tuples")
    declared_shapes = array.get("valid_physical_shapes")
    declared_pairs = array.get("legal_pairs")
    fifo_values = (
        _values(universe.get("physical_fifo_depth"))
        or _values(universe.get("physical_fifo_depth_entries"))
        or _values(universe.get("fifo_depth"))
    )
    activation_values = _values(universe.get("activation_bank_count"))
    if not fifo_values or not activation_values:
        # Some Stage-0 producers use candidate_universe only as a complete-
        # universe declaration and keep the actual physical axes beside it in
        # search_params.  That is a valid declarative form, so let the legacy
        # top-level-axis parser consume those exact axes below.
        return []

    tuples: list[dict[str, int]] = []
    if isinstance(declared, list) and declared:
        for index, raw in enumerate(declared):
            if not isinstance(raw, dict):
                raise ValueError(f"candidate_universe legal_compute_array_tuples[{index}] must be an object")
            lanes = _positive(raw.get("lanes"))
            rows = _positive(raw.get("rows"))
            cols = _positive(raw.get("cols"))
            if lanes is None or rows is None or cols is None:
                raise ValueError(f"candidate_universe legal_compute_array_tuples[{index}] is incomplete")
            for fifo_depth, activation_banks in product(fifo_values, activation_values):
                tuples.append(
                    _normal_tuple(
                        {
                            "lanes": lanes,
                            "compute_array": {"rows": rows, "cols": cols},
                            "fifo_depth": fifo_depth,
                            "activation_banks": activation_banks,
                        },
                        index,
                    )
                )
        return tuples

    # Current Stage-0 design-space agents describe PE geometry as physical
    # shapes and keep the lane axis at the enclosing universe level.  This is
    # the same finite Cartesian declaration as legal_pairs, just with optional
    # PE-count metadata retained for reporting.
    if isinstance(declared_shapes, list) and declared_shapes:
        lanes_values = _values(universe.get("lanes"))
        if not lanes_values:
            raise ValueError("candidate_universe valid_physical_shapes requires declared lane values")
        for index, raw in enumerate(declared_shapes):
            if not isinstance(raw, dict):
                raise ValueError(f"candidate_universe valid_physical_shapes[{index}] must be an object")
            rows = _positive(_field(raw, "rows", "compute_array_rows"))
            cols = _positive(_field(raw, "cols", "compute_array_cols"))
            shape_lanes = _positive(raw.get("lanes"))
            if rows is None or cols is None:
                raise ValueError(f"candidate_universe valid_physical_shapes[{index}] is incomplete")
            for lanes, fifo_depth, activation_banks in product(
                [shape_lanes] if shape_lanes is not None else lanes_values,
                fifo_values,
                activation_values,
            ):
                try:
                    tuples.append(
                        _normal_tuple(
                            {
                                "lanes": lanes,
                                "compute_array": {"rows": rows, "cols": cols},
                                "fifo_depth": fifo_depth,
                                "activation_banks": activation_banks,
                            },
                            index,
                        )
                    )
                except ValueError:
                    continue
        return tuples

    if isinstance(declared_pairs, list) and declared_pairs:
        lanes_values = _values(universe.get("lanes"))
        if not lanes_values:
            raise ValueError("candidate_universe legal_pairs requires declared lane values")
        for index, raw in enumerate(declared_pairs):
            if not isinstance(raw, (list, tuple)) or len(raw) != 2:
                raise ValueError(f"candidate_universe legal_pairs[{index}] must be [rows, cols]")
            rows = _positive(raw[0])
            cols = _positive(raw[1])
            if rows is None or cols is None:
                raise ValueError(f"candidate_universe legal_pairs[{index}] is incomplete")
            for lanes, fifo_depth, activation_banks in product(
                lanes_values, fifo_values, activation_values
            ):
                try:
                    tuples.append(
                        _normal_tuple(
                            {
                                "lanes": lanes,
                                "compute_array": {"rows": rows, "cols": cols},
                                "fifo_depth": fifo_depth,
                                "activation_banks": activation_banks,
                            },
                            index,
                        )
                    )
                except ValueError:
                    continue
        return tuples

    lanes_values = _values(universe.get("lanes"))
    row_values = _values(array.get("rows"))
    col_values = _values(array.get("cols"))
    if not lanes_values or not row_values or not col_values:
        raise ValueError("candidate_universe must declare legal lane and PE-array values")
    for index, (lanes, rows, cols, fifo_depth, activation_banks) in enumerate(
        product(lanes_values, row_values, col_values, fifo_values, activation_values)
    ):
        try:
            tuples.append(
                _normal_tuple(
                    {
                        "lanes": lanes,
                        "compute_array": {"rows": rows, "cols": cols},
                        "fifo_depth": fifo_depth,
                        "activation_banks": activation_banks,
                    },
                    index,
                )
            )
        except ValueError:
            continue
    return tuples


def _candidate_dimension_tuples(search: dict[str, Any]) -> list[dict[str, int]]:
    """Normalize an explicit finite Stage-0 candidate-dimensions declaration."""

    dimensions = search.get("candidate_dimensions")
    if not isinstance(dimensions, dict):
        return []
    lanes_values = _values(dimensions.get("lanes"))
    fifo_values = _values(dimensions.get("physical_fifo_depth"))
    activation_values = _values(dimensions.get("activation_bank_count"))
    raw_arrays = dimensions.get("compute_array")
    shapes = raw_arrays.get("values") if isinstance(raw_arrays, dict) else raw_arrays
    if not isinstance(shapes, list):
        shapes = []
    if not all((lanes_values, fifo_values, activation_values, shapes)):
        raise ValueError("candidate_dimensions has no complete physical DSE candidate declaration")

    tuples: list[dict[str, int]] = []
    for index, raw in enumerate(shapes):
        if not isinstance(raw, dict):
            raise ValueError(f"candidate_dimensions compute_array.values[{index}] must be an object")
        rows = _positive(_field(raw, "rows", "compute_array_rows"))
        cols = _positive(_field(raw, "cols", "compute_array_cols"))
        if rows is None or cols is None:
            raise ValueError(f"candidate_dimensions compute_array.values[{index}] is incomplete")
        for lanes, fifo_depth, activation_banks in product(
            lanes_values, fifo_values, activation_values
        ):
            try:
                tuples.append(
                    _normal_tuple(
                        {
                            "lanes": lanes,
                            "compute_array": {"rows": rows, "cols": cols},
                            "physical_fifo_depth": fifo_depth,
                            "activation_bank_count": activation_banks,
                        },
                        index,
                    )
                )
            except ValueError:
                continue
    return tuples


def _legacy_tuples(search: dict[str, Any]) -> list[dict[str, int]]:
    array = search.get("compute_array") if isinstance(search.get("compute_array"), dict) else {}
    lanes_values = _values(search.get("lanes"))
    row_values = _values(array.get("rows"))
    col_values = _values(array.get("cols"))
    fifo_values = _values(search.get("physical_fifo_depth")) or _values(search.get("fifo_depth")) or _values(
        (search.get("fifo_depths") or {}).get("module_stream_fifo_depth_entries")
        if isinstance(search.get("fifo_depths"), dict)
        else None
    )
    activation_values = _values(search.get("activation_bank_count")) or _values(
        (search.get("bank_counts") or {}).get("activation_sram_banks")
        if isinstance(search.get("bank_counts"), dict)
        else None
    )
    if not all((lanes_values, row_values, col_values, fifo_values, activation_values)):
        raise ValueError("design space has no complete physical DSE candidate declaration")

    # Stage-0 may declare the legal PE array pairs while retaining rows and
    # columns as individually documented axes.  Preserve that correlation;
    # never recreate a wider Cartesian space from those descriptive axes.
    declared_pairs = array.get("valid_candidate_pairs") or array.get("legal_pairs")
    tuples: list[dict[str, int]] = []
    if isinstance(declared_pairs, list) and declared_pairs:
        for index, pair in enumerate(declared_pairs):
            if isinstance(pair, dict):
                rows = _positive(_field(pair, "rows", "compute_array_rows"))
                cols = _positive(_field(pair, "cols", "compute_array_cols"))
            elif isinstance(pair, (list, tuple)) and len(pair) == 2:
                rows, cols = _positive(pair[0]), _positive(pair[1])
            else:
                raise ValueError(f"compute_array valid_candidate_pairs[{index}] is malformed")
            if rows is None or cols is None:
                raise ValueError(f"compute_array valid_candidate_pairs[{index}] is incomplete")
            for lanes, fifo_depth, activation_banks in product(
                lanes_values, fifo_values, activation_values
            ):
                try:
                    tuples.append(
                        _normal_tuple(
                            {
                                "lanes": lanes,
                                "compute_array": {"rows": rows, "cols": cols},
                                "fifo_depth": fifo_depth,
                                "activation_banks": activation_banks,
                            },
                            index,
                        )
                    )
                except ValueError:
                    continue
        return tuples

    for index, values in enumerate(product(lanes_values, row_values, col_values, fifo_values, activation_values)):
        lanes, rows, cols, fifo_depth, activation_banks = values
        try:
            tuples.append(
                _normal_tuple(
                    {
                        "lanes": lanes,
                        "compute_array": {"rows": rows, "cols": cols},
                        "fifo_depth": fifo_depth,
                        "activation_banks": activation_banks,
                    },
                    index,
                )
            )
        except ValueError:
            continue
    return tuples


def physical_candidate_tuples(search: dict[str, Any]) -> list[dict[str, int]]:
    """Return the complete Stage-0-declared physical candidate universe.

    The function accepts either explicit finite tuples or a declared legal
    Cartesian universe. It never creates a candidate dimension not present in
    Stage 0 and rejects malformed or empty declarations.
    """

    explicit = search.get("hardware_parameter_tuples")
    if not explicit and isinstance(search.get("candidate_universe"), list):
        explicit = search["candidate_universe"]
    if isinstance(explicit, list) and explicit:
        tuples = [
            _normal_tuple(row, index)
            for index, row in enumerate(explicit)
            if isinstance(row, dict)
        ]
        if len(tuples) != len(explicit):
            raise ValueError("hardware_parameter_tuples entries must be objects")
    else:
        tuples = (
            _candidate_universe_tuples(search)
            or _candidate_dimension_tuples(search)
            or _legacy_tuples(search)
        )

    unique: dict[tuple[int, int, int, int, int], dict[str, int]] = {}
    for row in tuples:
        key = (
            row["lanes"],
            row["compute_array_rows"],
            row["compute_array_cols"],
            row["fifo_depth"],
            row["activation_banks"],
        )
        unique[key] = row
    if not unique:
        raise ValueError("design space has no legal physical DSE candidates")
    return [unique[key] for key in sorted(unique)]
