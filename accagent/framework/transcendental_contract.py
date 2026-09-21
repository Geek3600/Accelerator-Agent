"""Materialize synthesizable, error-bounded nonlinear approximation contracts."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "spatialaccagent.transcendental_approximation_contract.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_memh(path: Path, values: list[int], width_bits: int) -> dict[str, Any]:
    if width_bits <= 0 or width_bits > 32:
        raise ValueError(f"unsupported LUT word width: {width_bits}")
    digits = (width_bits + 3) // 4
    mask = (1 << width_bits) - 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{value & mask:0{digits}x}\n" for value in values), encoding="ascii")
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "word_width_bits": width_bits,
        "entry_count": len(values),
        "address_order": "ascending",
    }


def exp2_fraction_lut(input_fraction_bits: int, output_fraction_bits: int) -> list[int]:
    return [
        round(math.pow(2.0, index / (1 << input_fraction_bits)) * (1 << output_fraction_bits))
        for index in range(1 << input_fraction_bits)
    ]


def exp_approximation(
    x_fixed: int,
    *,
    input_fraction_bits: int,
    output_fraction_bits: int,
    log2e_fixed: int,
    table: list[int],
    minimum_input_fixed: int,
) -> float:
    if x_fixed <= minimum_input_fixed:
        return 0.0
    if x_fixed >= 0:
        return 1.0
    x_log2e = (x_fixed * log2e_fixed) >> input_fraction_bits
    integer_part = x_log2e >> input_fraction_bits
    fractional_part = x_log2e - (integer_part << input_fraction_bits)
    base = table[fractional_part]
    raw = base << integer_part if integer_part >= 0 else base >> -integer_part
    return raw / float(1 << output_fraction_bits)


def validate_exp_contract(
    *,
    input_fraction_bits: int,
    output_fraction_bits: int,
    log2e_fixed: int,
    table: list[int],
    minimum_input: int,
) -> dict[str, Any]:
    minimum_fixed = minimum_input << input_fraction_bits
    worst_abs = {"error": -1.0, "input": None, "observed": None, "reference": None}
    worst_rel = {"error": -1.0, "input": None, "observed": None, "reference": None}
    for x_fixed in range(minimum_fixed, 1):
        x = x_fixed / float(1 << input_fraction_bits)
        observed = exp_approximation(
            x_fixed,
            input_fraction_bits=input_fraction_bits,
            output_fraction_bits=output_fraction_bits,
            log2e_fixed=log2e_fixed,
            table=table,
            minimum_input_fixed=minimum_fixed,
        )
        reference = math.exp(x)
        absolute = abs(observed - reference)
        if absolute > worst_abs["error"]:
            worst_abs = {"error": absolute, "input": x, "observed": observed, "reference": reference}
        if reference >= 1e-4:
            relative = absolute / reference
            if relative > worst_rel["error"]:
                worst_rel = {"error": relative, "input": x, "observed": observed, "reference": reference}
    return {
        "method": "exhaustive_over_every_representable_input_in_declared_fixed_point_domain",
        "points": 1 - minimum_fixed,
        "max_absolute_error": worst_abs,
        "max_relative_error_where_reference_ge_1e-4": worst_rel,
        "acceptance_bound": {"max_absolute_error": 0.001, "status": "pass" if worst_abs["error"] <= 0.001 else "fail"},
    }


def sigmoid_table(segment_count: int, value_fraction_bits: int) -> list[int]:
    return [
        round((1.0 / (1.0 + math.exp(-(-8.0 + 16.0 * index / segment_count)))) * (1 << value_fraction_bits))
        for index in range(segment_count + 1)
    ]


def sigmoid_pwl_fixed(
    x_fixed: int,
    *,
    input_fraction_bits: int,
    value_fraction_bits: int,
    segment_count: int,
    table: list[int],
) -> int:
    lower = -8 << input_fraction_bits
    upper = 8 << input_fraction_bits
    if x_fixed <= lower:
        return 0
    if x_fixed >= upper:
        return 1 << value_fraction_bits
    domain_steps = upper - lower
    if domain_steps % segment_count:
        raise ValueError("sigmoid segment count does not divide fixed-point domain")
    segment_steps = domain_steps // segment_count
    offset = x_fixed - lower
    index = min(segment_count - 1, offset // segment_steps)
    remainder = offset - index * segment_steps
    delta = table[index + 1] - table[index]
    return table[index] + (delta * remainder + segment_steps // 2) // segment_steps


def validate_sigmoid_contract(
    *,
    input_fraction_bits: int,
    value_fraction_bits: int,
    segment_count: int,
    table: list[int],
) -> dict[str, Any]:
    minimum_fixed = -12 << input_fraction_bits
    maximum_fixed = 12 << input_fraction_bits
    worst_sigmoid = {"error": -1.0, "input": None, "observed": None, "reference": None}
    worst_silu = {"error": -1.0, "input": None, "observed": None, "reference": None}
    for x_fixed in range(minimum_fixed, maximum_fixed + 1):
        x = x_fixed / float(1 << input_fraction_bits)
        observed_sigmoid = sigmoid_pwl_fixed(
            x_fixed,
            input_fraction_bits=input_fraction_bits,
            value_fraction_bits=value_fraction_bits,
            segment_count=segment_count,
            table=table,
        ) / float(1 << value_fraction_bits)
        reference_sigmoid = 1.0 / (1.0 + math.exp(-x))
        sigmoid_error = abs(observed_sigmoid - reference_sigmoid)
        silu_error = abs(x * observed_sigmoid - x * reference_sigmoid)
        if sigmoid_error > worst_sigmoid["error"]:
            worst_sigmoid = {
                "error": sigmoid_error,
                "input": x,
                "observed": observed_sigmoid,
                "reference": reference_sigmoid,
            }
        if silu_error > worst_silu["error"]:
            worst_silu = {
                "error": silu_error,
                "input": x,
                "observed": x * observed_sigmoid,
                "reference": x * reference_sigmoid,
            }
    return {
        "method": "exhaustive_over_every_representable_q_input_on_extended_minus12_to12_domain",
        "points": maximum_fixed - minimum_fixed + 1,
        "max_sigmoid_absolute_error": worst_sigmoid,
        "max_silu_absolute_error": worst_silu,
        "acceptance_bound": {"max_silu_absolute_error": 0.005, "status": "pass" if worst_silu["error"] <= 0.005 else "fail"},
    }


def materialize_transcendental_contract(out_dir: Path) -> dict[str, Any]:
    out_dir = out_dir.resolve()
    input_fraction_bits = 11
    exp_output_fraction_bits = 24
    sigmoid_value_fraction_bits = 18
    sigmoid_segments = 128
    minimum_exp_input = -16
    log2e_fixed = round(math.log2(math.e) * (1 << input_fraction_bits))
    exp_table = exp2_fraction_lut(input_fraction_bits, exp_output_fraction_bits)
    sigmoid_values = sigmoid_table(sigmoid_segments, sigmoid_value_fraction_bits)
    exp_memh = write_memh(out_dir / "exp2_fraction_q24.memh", exp_table, exp_output_fraction_bits + 2)
    write_memh(out_dir / "exp2_fraction_q24.mem", exp_table, exp_output_fraction_bits + 2)
    sigmoid_memh = write_memh(
        out_dir / "sigmoid_pwl_q18.memh",
        sigmoid_values,
        sigmoid_value_fraction_bits + 1,
    )
    write_memh(
        out_dir / "sigmoid_pwl_q18.mem",
        sigmoid_values,
        sigmoid_value_fraction_bits + 1,
    )
    exp_validation = validate_exp_contract(
        input_fraction_bits=input_fraction_bits,
        output_fraction_bits=exp_output_fraction_bits,
        log2e_fixed=log2e_fixed,
        table=exp_table,
        minimum_input=minimum_exp_input,
    )
    sigmoid_validation = validate_sigmoid_contract(
        input_fraction_bits=input_fraction_bits,
        value_fraction_bits=sigmoid_value_fraction_bits,
        segment_count=sigmoid_segments,
        table=sigmoid_values,
    )
    blockers = []
    if exp_validation["acceptance_bound"]["status"] != "pass":
        blockers.append("exp approximation exceeds its frozen error bound")
    if sigmoid_validation["acceptance_bound"]["status"] != "pass":
        blockers.append("sigmoid/SiLU approximation exceeds its frozen error bound")
    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not blockers else "fail",
        "blockers": blockers,
        "exp_for_shifted_softmax": {
            "semantic_function": "exp(x)",
            "required_input_invariant": "x is score minus row maximum, therefore x <= 0",
            "input_domain": [minimum_exp_input, 0],
            "outside_domain": {"x_le_minimum": 0.0, "x_ge_zero": 1.0},
            "input_fixed_format": {"signed": True, "fraction_bits": input_fraction_bits},
            "range_reduction": {
                "formula": "exp(x) = 2^(x * log2(e))",
                "log2e_fixed": log2e_fixed,
                "integer_rule": "arithmetic right shift; integer part is floor for negative values",
                "fractional_address_bits": input_fraction_bits,
            },
            "table": exp_memh,
            "table_value_format": {"unsigned": True, "fraction_bits": exp_output_fraction_bits},
            "validation": exp_validation,
        },
        "sigmoid_and_silu": {
            "semantic_functions": {"sigmoid": "1/(1+exp(-x))", "silu": "x*sigmoid(x)"},
            "interpolation_domain": [-8, 8],
            "outside_domain": {"x_le_minus8_sigmoid": 0.0, "x_ge_8_sigmoid": 1.0},
            "input_fixed_format": {"signed": True, "fraction_bits": input_fraction_bits},
            "segment_count": sigmoid_segments,
            "segment_width": 16.0 / sigmoid_segments,
            "interpolation": "linear with nearest-integer rounding after multiplying the table delta by the within-segment remainder",
            "table": sigmoid_memh,
            "table_value_format": {"unsigned": True, "integer_bits": 1, "fraction_bits": sigmoid_value_fraction_bits},
            "validation": sigmoid_validation,
        },
        "implementation_boundary": {
            "tables_are_constants_not_expected_outputs": True,
            "tables_are_independent_of_rtl_outputs": True,
            "hardware_must_implement_the_declared_integer_rules_exactly": True,
            "hardware_still_requires_real_simulator_comparison_against_target_model_outputs": True,
            "no_sine_or_cosine_operator_is_required_when_hash_bound_runtime_RoPE_tables_are_consumed": True,
        },
    }
    contract["contract_sha256"] = sha256_json(contract)
    contract_path = out_dir / "transcendental_approximation_contract.json"
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    contract["path"] = str(contract_path)
    contract["file_sha256"] = sha256_file(contract_path)
    return contract
