"""Bind model, numeric, and architecture parameters to selected stages."""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path
from typing import Any

from accagent.framework.dse_ledger import candidate_fingerprint, candidate_id, ledger_path, load_latest, measurement_summary
from accagent.framework.dse_candidates import physical_candidate_tuples
from accagent.framework.dse_materialization import validate_candidate_universe
from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    add_constraint,
    add_invariant,
    artifact_path,
    constraint_facts,
    copy_state,
    read_json,
    run_dir_from_state,
    sacg_memory_truth,
    stage_status_allows_promotion,
    status_claims_inactive_sacg_memory_blocker,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_llm import STAGE_AGENT_SCHEMA, run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary


TOUCHED_CONSTRAINTS = [
    "constraint.parameter.binding",
    "constraint.dse.selection",
    "constraint.parameter.structure",
    "constraint.axi.layout",
]


DSE_SELECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": True,
    "properties": {
        **STAGE_AGENT_SCHEMA["properties"],
        "selected_candidate_id": {"type": "string"},
        "ranked_candidate_ids": {"type": "array", "items": {"type": "string"}},
        "selection_rationale": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        *STAGE_AGENT_SCHEMA["required"],
        "selected_candidate_id",
        "ranked_candidate_ids",
        "selection_rationale",
        "assumptions",
    ],
}


DSE_OVERRIDE_KEYS = (
    "lanes",
    "compute_array_rows",
    "compute_array_cols",
    "fifo_depth",
    "weight_banks",
    "activation_banks",
    "weight_banks_by_role",
)

PHYSICAL_IMPLEMENTATION = {
    "compute_backend": "vivado_fp_ip",
    "weight_memory": "xpm_uram",
    "activation_memory": "xpm_bram",
    "fifo_memory": "xpm_bram",
    "large_cache_memory": "xpm_uram",
}


def integer_role_map(value: Any, valid_roles: set[str]) -> dict[str, int]:
    """Keep only explicit, physical role-to-bank bindings."""

    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for role, count in value.items():
        name = str(role)
        parsed = scalar(count, 0)
        if name in valid_roles and parsed > 0:
            result[name] = parsed
    return result


def semantic_weight_storage_terms(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the Stage-3-resolved physical parameter terms for this model.

    Stage 4 must never infer a Qwen/LLaMA parameter inventory. Stage 3 already
    resolves every adapter-declared term against the current model shape and
    numeric policy, so it is the single source of truth for XPM placement.
    """

    schedule = plan.get("memory_schedule", {}) if isinstance(plan.get("memory_schedule"), dict) else {}
    raw_terms = schedule.get("weight_storage_terms", [])
    if not isinstance(raw_terms, list) or not raw_terms:
        raise ValueError("Stage3 memory_schedule.weight_storage_terms is missing or empty")
    terms: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_terms:
        if not isinstance(raw, dict):
            raise ValueError("Stage3 weight storage terms must be objects")
        term_id = str(raw.get("id") or "")
        owner = str(raw.get("stage") or "")
        physical_role = str(raw.get("physical_role") or "")
        elements = scalar(raw.get("elements"), 0)
        element_bits = scalar(raw.get("element_bits"), 0)
        if (
            not term_id
            or term_id in seen
            or not owner
            or (physical_role != "weight" and not physical_role.startswith("weight_"))
            or elements <= 0
            or element_bits <= 0
        ):
            raise ValueError(f"invalid Stage3 weight storage term: {raw!r}")
        seen.add(term_id)
        terms.append(raw)
    return terms


def weight_role_capacity_bits(plan: dict[str, Any]) -> dict[str, int]:
    """Return exact model-semantic storage capacities grouped by XPM role."""

    capacities: dict[str, int] = {}
    for term in semantic_weight_storage_terms(plan):
        role = str(term["physical_role"])
        capacities[role] = capacities.get(role, 0) + scalar(term.get("elements"), 0) * scalar(term.get("element_bits"), 0)
    return capacities


def physical_weight_layout(plan: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Bind every generated weight role to explicit XPM banks.

    Every model weight role uses XPM URAM. DSE may vary total banks per role,
    but cannot remap a weight role into BRAM. Primitive counts are intentionally
    absent: only Vivado's exact app-shell result supplies resource, power,
    clock, and performance metrics.
    """

    capacities = weight_role_capacity_bits(plan)
    valid_roles = set(capacities)
    default_banks = max(1, scalar(parameters.get("weight_banks"), 1))
    requested_banks = integer_role_map(parameters.get("weight_banks_by_role"), valid_roles)
    roles = []
    terms_by_role: dict[str, list[dict[str, Any]]] = {}
    for term in semantic_weight_storage_terms(plan):
        terms_by_role.setdefault(str(term["physical_role"]), []).append(term)
    for role, capacity_bits in capacities.items():
        banks = requested_banks.get(role, default_banks)
        roles.append(
            {
                "role": role,
                "term_ids": [str(term["id"]) for term in terms_by_role[role]],
                "stages": sorted({str(term["stage"]) for term in terms_by_role[role]}),
                "capacity_bits": capacity_bits,
                "element_bits": sorted({scalar(term.get("element_bits"), 0) for term in terms_by_role[role]}),
                "elements": sum(scalar(term.get("elements"), 0) for term in terms_by_role[role]),
                "banks": banks,
                "uram_banks": banks,
                "primitive_policy": "xpm_uram",
            }
        )
    return {
        "schema_version": "spatialaccagent.weight_memory_layout.v2",
        "measurement_policy": "Vivado app-shell implementation is the only resource/power authority for this layout.",
        "roles": roles,
        "weight_banks_by_role": {row["role"]: row["banks"] for row in roles},
    }


def first_value(search_params: dict[str, Any], key: str, default: Any) -> Any:
    values = search_params.get(key, [])
    if isinstance(values, list) and values:
        return values[0]
    nested = search_params.get(key, {})
    if isinstance(nested, dict):
        values = nested.get("candidates", [])
        if isinstance(values, list) and values:
            return values[0]
    return default


def scalar(value: Any, default: int) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def dtype_bits(dtype: Any, default: int) -> int:
    text = str(dtype or "").strip().upper().replace("_", "")
    mapping = {
        "FP32": 32,
        "FLOAT32": 32,
        "F32": 32,
        "FP16": 16,
        "FLOAT16": 16,
        "F16": 16,
        "BF16": 16,
        "BFP16": 16,
        "INT8": 8,
        "UINT8": 8,
    }
    return mapping.get(text, default)


def fixed_or_first(entry: Any, default: int) -> int:
    if isinstance(entry, dict):
        if entry.get("fixed") is not None:
            return scalar(entry.get("fixed"), default)
        values = entry.get("candidates")
        if isinstance(values, list) and values:
            return scalar(values[0], default)
    if isinstance(entry, list) and entry:
        return scalar(entry[0], default)
    return default


def first_nested_candidate(search_params: dict[str, Any], group: str, name: str, default: int) -> int:
    values = search_params.get(group, {}) if isinstance(search_params.get(group), dict) else {}
    return fixed_or_first(values.get(name), default)


def selected_fifo_depth(search_params: dict[str, Any], default: int = 16) -> int:
    direct = first_value(search_params, "fifo_depth", None)
    if direct is not None:
        return scalar(direct, default)
    return first_nested_candidate(search_params, "fifo_depths", "module_stream_fifo_depth_entries", default)


def selected_clock_target_mhz(search_params: dict[str, Any]) -> int | None:
    direct = first_value(search_params, "clock_target_mhz", None)
    if direct is not None:
        return scalar(direct, 0)
    clocking = search_params.get("clocking", {}) if isinstance(search_params.get("clocking"), dict) else {}
    target = clocking.get("target_clock_mhz") if isinstance(clocking.get("target_clock_mhz"), dict) else {}
    if isinstance(target, dict):
        if target.get("known_value") is None and target.get("candidates") is None:
            return None
        return fixed_or_first(target, 0)
    return None


def candidate_values(entry: Any, default: int) -> list[int]:
    """Return a stable, de-duplicated list of integral architecture choices."""

    values: Any = entry
    preferred: Any = None
    if isinstance(entry, dict):
        values = entry.get("candidates", entry.get("values", []))
        preferred = entry.get("preferred_initial", entry.get("fixed"))
    if not isinstance(values, list):
        values = [values] if values is not None else []
    normalized: list[int] = []
    for value in [preferred, *values, default]:
        parsed = scalar(value, 0)
        if parsed > 0 and parsed not in normalized:
            normalized.append(parsed)
    return normalized


def search_group_values(search: dict[str, Any], group: str, name: str, default: int) -> list[int]:
    container = search.get(group, {}) if isinstance(search.get(group), dict) else {}
    return candidate_values(container.get(name), default)


def common_candidate_values(entries: list[Any], default: int) -> list[int]:
    """Keep only values legal for every supplied stage-specific candidate set."""

    choices = [set(candidate_values(entry, default)) for entry in entries if entry is not None]
    if not choices:
        return [default]
    common = set.intersection(*choices)
    if not common:
        return [default]
    return sorted(common, reverse=True)


def declared_weight_layout_candidates(
    search: dict[str, Any], weight_banks: list[int], weight_roles: set[str]
) -> list[dict[str, Any]]:
    """Return complete physical XPM layouts declared by Stage 0.

    Layouts are hardware candidates, not estimates: each changes the generated
    XPM URAM bank topology. Older Stage-0 inputs without explicit layouts get
    one all-URAM layout per declared total-bank setting for compatibility.
    """

    raw = search.get("physical_weight_layout_candidates", [])
    if isinstance(raw, dict):
        raw = raw.get("candidates", [])
    layouts: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for value in raw:
            if not isinstance(value, dict):
                continue
            banks_by_role = integer_role_map(value.get("weight_banks_by_role"), weight_roles)
            if set(banks_by_role) != weight_roles:
                raise ValueError(
                    "physical_weight_layout_candidates must bind exactly the model-semantic weight roles: "
                    f"expected={sorted(weight_roles)}, actual={sorted(banks_by_role)}"
                )
            layouts.append(
                {
                    "weight_banks": max(banks_by_role.values()),
                    "weight_banks_by_role": banks_by_role,
                }
            )
    if not layouts:
        for count in weight_banks:
            layouts.append(
                {
                    "weight_banks": count,
                    "weight_banks_by_role": {role: count for role in sorted(weight_roles)},
                }
            )
    unique: dict[str, dict[str, Any]] = {}
    for layout in layouts:
        unique[candidate_fingerprint(layout)] = layout
    return list(unique.values())


def architecture_candidate_space(search: dict[str, Any], weight_roles: set[str]) -> dict[str, Any]:
    """Materialize only parameters that alter generated FPGA hardware."""

    weight_banks = search_group_values(
        search,
        "bank_counts",
        "weight_sram_banks",
        scalar(first_value(search, "weight_banks", 1), 1),
    )
    tuples = physical_candidate_tuples(search)
    return {
        "physical_candidate_tuples": tuples,
        "lanes": sorted({item["lanes"] for item in tuples}),
        "compute_array_rows": sorted({item["compute_array_rows"] for item in tuples}),
        "compute_array_cols": sorted({item["compute_array_cols"] for item in tuples}),
        "fifo_depth": sorted({item["fifo_depth"] for item in tuples}),
        "activation_banks": sorted({item["activation_banks"] for item in tuples}),
        "physical_weight_layouts": declared_weight_layout_candidates(search, weight_banks, weight_roles),
        "excluded_until_hardware_binding": [
            "burst_beats",
            "pipeline_depth",
            "clock_target_mhz",
        ],
    }


def selected_search_params(search: dict[str, Any], parameters: dict[str, Any] | None) -> dict[str, Any]:
    """Overlay one selected architecture point without mutating SACG facts."""

    selected = parameters or {}
    result = dict(search)
    for key in DSE_OVERRIDE_KEYS:
        if key in selected and selected[key] is not None:
            result[key] = [selected[key]]
    return result


def candidate_parameter_points(search: dict[str, Any], weight_roles: set[str]) -> list[dict[str, Any]]:
    """Enumerate the complete declared legal DSE universe without sampling."""

    space = architecture_candidate_space(search, weight_roles)
    raw: list[dict[str, Any]] = []
    for physical, layout in product(space["physical_candidate_tuples"], space["physical_weight_layouts"]):
        point = {
            **physical,
            **layout,
            **PHYSICAL_IMPLEMENTATION,
        }
        raw.append(point)
    unique: dict[str, dict[str, Any]] = {}
    for point in raw:
        unique[candidate_fingerprint(point)] = point
    return list(unique.values())


def bytes_for_elements(elements: int, bits: int) -> int:
    return (max(0, elements) * max(1, bits) + 7) // 8


def align_up(value: int, alignment: int) -> int:
    if alignment <= 1:
        return value
    return ((value + alignment - 1) // alignment) * alignment


def concrete_bound_params(stage: dict[str, Any]) -> dict[str, Any]:
    params = {}
    bound = stage.get("bound_params", {}) if isinstance(stage.get("bound_params"), dict) else {}
    for name, record in bound.items():
        if isinstance(record, dict) and record.get("status") == "bound":
            params[str(name)] = record.get("value")
    return params


def fallback_params(shape: dict[str, Any], numeric: dict[str, Any], search: dict[str, Any]) -> dict[str, Any]:
    rules = numeric.get("default_rules", {}) if isinstance(numeric.get("default_rules"), dict) else {}
    activation_bits = dtype_bits(rules.get("activation_dtype", "FP16"), 16)
    acc_bits = dtype_bits(rules.get("acc_dtype", "FP32"), 32)
    physical = physical_candidate_tuples(search)[0]
    return {
        "hidden_size": shape.get("hidden_size"),
        "intermediate_size": shape.get("intermediate_size"),
        "num_q_heads": shape.get("num_q_heads"),
        "num_kv_heads": shape.get("num_kv_heads"),
        "head_dim": shape.get("head_dim"),
        "seq_len": shape.get("target_max_seq_len"),
        "lanes": physical["lanes"],
        "compute_array_rows": physical["compute_array_rows"],
        "compute_array_cols": physical["compute_array_cols"],
        "elem_bits": activation_bits,
        "input_bits": acc_bits,
        "output_bits": acc_bits,
        "causal": True,
        "fifo_depth": physical["fifo_depth"],
        "weight_banks": first_value(search, "weight_banks", 1),
        "activation_banks": physical["activation_banks"],
        "burst_beats": first_value(search, "burst_beats", 1),
        "pipeline_depth": first_value(search, "pipeline_depth", 1),
        "clock_target_mhz": selected_clock_target_mhz(search),
        "numeric_policy_id": numeric.get("policy_id"),
    }


def bind_stage_params(
    stage: dict[str, Any],
    shape: dict[str, Any],
    numeric: dict[str, Any],
    search: dict[str, Any],
    selected_architecture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    defaults = fallback_params(shape, numeric, search)
    params = defaults | concrete_bound_params(stage)
    for key in DSE_OVERRIDE_KEYS:
        if key in (selected_architecture or {}) and (key in params or key in stage.get("required_params", [])):
            params[key] = selected_architecture[key]
    contract = stage.get("numeric_contract", {}) if isinstance(stage.get("numeric_contract"), dict) else {}
    for param_name, contract_name, fallback_name in [
        ("input_bits", "input_bits", "input_bits"),
        ("elem_bits", "internal_elem_bits", "elem_bits"),
        ("output_bits", "output_bits", "output_bits"),
    ]:
        params[param_name] = scalar(contract.get(contract_name), scalar(defaults.get(fallback_name), 16))
    required = {name: params.get(name) for name in stage.get("required_params", []) if name in params}
    return required | {
        "input_bits": params.get("input_bits"),
        "elem_bits": params.get("elem_bits"),
        "output_bits": params.get("output_bits"),
        "compute_array_rows": (selected_architecture or {}).get("compute_array_rows", defaults["compute_array_rows"]),
        "compute_array_cols": (selected_architecture or {}).get("compute_array_cols", defaults["compute_array_cols"]),
        "fifo_depth": (selected_architecture or {}).get("fifo_depth", defaults["fifo_depth"]),
        "weight_banks": (selected_architecture or {}).get("weight_banks", defaults["weight_banks"]),
        "activation_banks": (selected_architecture or {}).get("activation_banks", defaults["activation_banks"]),
        "burst_beats": (selected_architecture or {}).get("burst_beats", defaults["burst_beats"]),
        "pipeline_depth": (selected_architecture or {}).get("pipeline_depth", defaults["pipeline_depth"]),
        "clock_target_mhz": defaults["clock_target_mhz"],
        "numeric_policy_id": defaults["numeric_policy_id"],
        **{
            key: (selected_architecture or {}).get(key, value)
            for key, value in PHYSICAL_IMPLEMENTATION.items()
        },
    }


def dim_pair(stage: dict[str, Any]) -> tuple[int | None, int | None]:
    """Return semantic stream widths already resolved by Stage 3."""

    input_shape = stage.get("input_shape", {}) if isinstance(stage.get("input_shape"), dict) else {}
    output_shape = stage.get("output_shape", {}) if isinstance(stage.get("output_shape"), dict) else {}
    return input_shape.get("width"), output_shape.get("width")


def check_legality(stage: dict[str, Any], params: dict[str, Any], shape: dict[str, Any], memory: dict[str, Any]) -> list[str]:
    errors = []
    for name in stage.get("required_params", []):
        if params.get(name) is None:
            errors.append(f"{stage['stage_id']}: missing required parameter {name}")
    lanes = params.get("lanes")
    compute_rows = params.get("compute_array_rows")
    compute_cols = params.get("compute_array_cols")
    in_dim, out_dim = dim_pair(stage)
    if isinstance(lanes, int) and lanes > 0:
        dimensions = [("input", in_dim), ("output", out_dim)]
        if stage.get("template_id") == "attention":
            dimensions.append(("head_dim", shape.get("head_dim")))
        for dim_name, dim in dimensions:
            if isinstance(dim, int) and dim % lanes != 0:
                errors.append(f"{stage['stage_id']}: {dim_name} dimension {dim} is not divisible by lanes={lanes}")
    if not isinstance(compute_rows, int) or compute_rows <= 0:
        errors.append(f"{stage['stage_id']}: compute_array_rows must be positive")
    if not isinstance(compute_cols, int) or compute_cols <= 0:
        errors.append(f"{stage['stage_id']}: compute_array_cols must be positive")
    if isinstance(lanes, int) and lanes > 0 and isinstance(compute_rows, int) and isinstance(compute_cols, int):
        if compute_rows > lanes or lanes % compute_rows != 0:
            errors.append(f"{stage['stage_id']}: lanes={lanes} must be divisible by compute_array_rows={compute_rows}")
        if compute_cols > lanes or lanes % compute_cols != 0:
            errors.append(f"{stage['stage_id']}: lanes={lanes} must be divisible by compute_array_cols={compute_cols}")
        if compute_cols & (compute_cols - 1):
            errors.append(f"{stage['stage_id']}: compute_array_cols={compute_cols} must be a power of two")
        if stage.get("template_id") == "attention":
            head_dim = shape.get("head_dim")
            if isinstance(head_dim, int) and head_dim % compute_cols != 0:
                errors.append(f"{stage['stage_id']}: head_dim={head_dim} is not divisible by compute_array_cols={compute_cols}")
    elem_bits = params.get("elem_bits") or params.get("output_bits") or params.get("input_bits")
    axi_bits = (memory.get("memory_system") or {}).get("axi_data_width_bits")
    if isinstance(lanes, int) and isinstance(elem_bits, int) and isinstance(axi_bits, int):
        data_bits = lanes * elem_bits
        if data_bits > axi_bits or axi_bits % data_bits != 0:
            errors.append(f"{stage['stage_id']}: lanes*elem_bits={data_bits} is not aligned to axi_data_width_bits={axi_bits}")
    return errors


def stage_structural_dimensions(
    stage: dict[str, Any], params: dict[str, Any], weight_terms: list[dict[str, Any]]
) -> dict[str, Any]:
    """Describe exact tensor/stream dimensions without predicting QoR.

    This data exists solely to build the concrete AXI transfer layout and to
    validate packing.  It contains no primitive, timing, power, or throughput
    estimate and is never used to order DSE candidates.
    """

    input_shape = stage.get("input_shape", {}) if isinstance(stage.get("input_shape"), dict) else {}
    output_shape = stage.get("output_shape", {}) if isinstance(stage.get("output_shape"), dict) else {}
    seq_len = scalar(input_shape.get("seq_len"), scalar(output_shape.get("seq_len"), 1))
    in_dim, out_dim = dim_pair(stage)
    lanes = int(params.get("lanes") or 1)
    elem_bits = int(params.get("elem_bits") or params.get("output_bits") or params.get("input_bits") or 16)
    owned_terms = [term for term in weight_terms if str(term.get("stage")) == str(stage.get("op"))]
    weight_elements = sum(scalar(term.get("elements"), 0) for term in owned_terms)
    weight_bytes = sum(scalar(term.get("bytes"), 0) for term in owned_terms)
    return {
        "description_kind": "exact_model_shape_and_stream_width",
        "used_for": "AXI layout and parameter-legality checks only; never QoR ranking or hardware pass evidence",
        "weight_elements": weight_elements,
        "weight_bytes": weight_bytes,
        "weight_term_ids": [str(term.get("id")) for term in owned_terms],
        "input_elements": seq_len * scalar(in_dim, 1),
        "output_elements": seq_len * scalar(out_dim, 1),
        "datapath_bits": lanes * elem_bits,
        "lanes": lanes,
        "elem_bits": elem_bits,
    }


def board_axi(state: dict[str, Any]) -> dict[str, Any]:
    memory = constraint_facts(state, "constraint.memory.board")
    memory_system = memory.get("memory_system", {}) if isinstance(memory.get("memory_system"), dict) else memory
    data_width_bits = scalar(memory_system.get("axi_data_width_bits"), 512)
    data_bytes = scalar(memory_system.get("axi_data_bytes"), max(1, data_width_bits // 8))
    return {
        "protocol": memory_system.get("axi_protocol", "AXI"),
        "data_width_bits": data_width_bits,
        "data_bytes": data_bytes,
        "alignment_bytes": data_bytes,
        "addr_width_bits": scalar(memory_system.get("axi_addr_width_bits"), 37),
        "core_side_interface_name": memory_system.get("core_side_interface_name"),
        "ddr_channels": scalar(memory_system.get("ddr_channels"), 1),
        "source": "constraint.memory.board.memory_system",
    }


def build_axi_transfer_layout(state: dict[str, Any], bindings: list[dict[str, Any]]) -> dict[str, Any]:
    axi = board_axi(state)
    alignment = scalar(axi.get("alignment_bytes"), 64)
    per_stage = []
    for item in bindings:
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        op = str(item.get("op"))
        input_bits = scalar(params.get("input_bits"), scalar(params.get("elem_bits"), 16))
        output_bits = scalar(params.get("output_bits"), scalar(params.get("elem_bits"), 16))
        structure = item.get("structural_dimensions", {}) if isinstance(item.get("structural_dimensions"), dict) else {}
        input_bytes = bytes_for_elements(scalar(structure.get("input_elements"), 0), input_bits)
        output_bytes = bytes_for_elements(scalar(structure.get("output_elements"), 0), output_bits)
        weight_bytes = scalar(structure.get("weight_bytes"), 0)
        total_bytes = input_bytes + output_bytes + weight_bytes
        aligned_bytes = align_up(total_bytes, alignment)
        per_stage.append(
            {
                "stage_id": item.get("stage_id"),
                "op": op,
                "input_activation_bytes": input_bytes,
                "output_activation_bytes": output_bytes,
                "weight_bytes": weight_bytes,
                "total_bytes": total_bytes,
                "aligned_bytes": aligned_bytes,
                "axi_beats": aligned_bytes // max(1, scalar(axi.get("data_bytes"), 64)),
                "input_bits": input_bits,
                "output_bits": output_bits,
                "weight_term_ids": structure.get("weight_term_ids", []),
            }
        )
    return {
        "schema_version": "spatialaccagent.parameter_axi_transfer_layout.v1",
        "layout_kind": "exact_tensor_shape_transfer_layout",
        "used_for": "static AXI alignment and packing checks only; not bandwidth, timing, power, or throughput evidence",
        "board_axi": axi,
        "per_stage": per_stage,
        "total_aligned_bytes_per_layer": sum(scalar(row.get("aligned_bytes"), 0) for row in per_stage),
        "notes": [
            "Stage 5 assigns concrete base addresses and checks non-overlap/alignment.",
            "Stage 6+ must provide real simulation, implementation, timing, and board evidence.",
        ],
    }


def numeric_binding_plan(state: dict[str, Any], bindings: list[dict[str, Any]]) -> dict[str, Any]:
    numeric = constraint_facts(state, "constraint.numeric.policy")
    rules = numeric.get("default_rules", {}) if isinstance(numeric.get("default_rules"), dict) else {}
    cast_points = []
    for item in bindings:
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        input_bits = scalar(params.get("input_bits"), 0)
        elem_bits = scalar(params.get("elem_bits"), 0)
        output_bits = scalar(params.get("output_bits"), 0)
        cast_points.append(
            {
                "stage_id": item.get("stage_id"),
                "op": item.get("op"),
                "input_bits": input_bits,
                "internal_elem_bits": elem_bits,
                "output_bits": output_bits,
                "input_cast": "none" if input_bits == elem_bits else f"{input_bits}_to_{elem_bits}",
                "output_cast": "none" if output_bits == elem_bits else f"{elem_bits}_to_{output_bits}",
                "residual_precision": output_bits if item.get("template_id") == "residual" else None,
            }
        )
    return {
        "policy_id": numeric.get("policy_id"),
        "source": "constraint.numeric.policy.default_rules",
        "activation_dtype": rules.get("activation_dtype"),
        "weight_dtype": rules.get("weight_dtype"),
        "acc_dtype": rules.get("acc_dtype"),
        "rounding": rules.get("rounding"),
        "saturation": rules.get("saturation"),
        "eps_source": "constraint.model.decoder.norm_type/default eps from template binding",
        "cast_points": cast_points,
    }


def stream_contract_trace(state: dict[str, Any], bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    by_stage = {str(item.get("stage_id")): item for item in bindings}
    global_in = scalar((numeric_binding_plan(state, bindings).get("cast_points") or [{}])[0].get("input_bits"), 32)
    global_out = scalar((numeric_binding_plan(state, bindings).get("cast_points") or [{}])[-1].get("output_bits"), 32)
    rows = []
    for edge in plan.get("stream_edges", []):
        contract = edge.get("stream_contract", {}) if isinstance(edge.get("stream_contract"), dict) else {}
        src_stage = str(edge.get("src_stage"))
        dst_stage = str(edge.get("dst_stage"))
        src_params = (by_stage.get(src_stage) or {}).get("params", {})
        dst_params = (by_stage.get(dst_stage) or {}).get("params", {})
        rows.append(
            {
                "edge_id": edge.get("edge_id"),
                "src_stage": src_stage,
                "dst_stage": dst_stage,
                "kind": edge.get("kind"),
                "element_bits": contract.get("element_bits"),
                "src_output_bits": global_in if src_stage == "block_input" else src_params.get("output_bits"),
                "dst_input_bits": global_out if dst_stage == "block_output" else dst_params.get("input_bits"),
                "stream_order": contract.get("stream_order") or edge.get("transfer_order", []),
                "tensor": contract.get("tensor", {}),
            }
        )
    return rows


def pass_row(checker: str, summary: str, **extra: Any) -> dict[str, Any]:
    return {"checker": checker, "status": "pass", "summary": summary, "errors": [], "warnings": [], **extra}


def fail_row(checker: str, errors: list[str], warnings: list[str] | None = None, **extra: Any) -> dict[str, Any]:
    return {"checker": checker, "status": "fail", "summary": "; ".join(errors[:3]), "errors": errors, "warnings": warnings or [], **extra}


def check_stage_numeric_contract(state: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    stage_contract = {
        str(stage.get("stage_id")): stage.get("numeric_contract", {})
        for stage in plan.get("stages", [])
        if isinstance(stage.get("numeric_contract"), dict)
    }
    errors = []
    for item in bindings.get("bindings", []):
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        contract = stage_contract.get(str(item.get("stage_id")), {})
        checks = [
            ("input_bits", "input_bits"),
            ("internal_elem_bits", "elem_bits"),
            ("output_bits", "output_bits"),
        ]
        for key, param_key in checks:
            if scalar(contract.get(key), -1) != scalar(params.get(param_key), -2):
                errors.append(
                    f"{item.get('stage_id')}: params.{param_key}={params.get(param_key)} does not match Stage3 numeric_contract.{key}={contract.get(key)}"
                )
    if errors:
        return fail_row("parameter_stage_numeric_contract_check", errors)
    return pass_row("parameter_stage_numeric_contract_check", f"bindings={len(bindings.get('bindings', []))}")


def check_edge_dtype_contract(bindings: dict[str, Any]) -> dict[str, Any]:
    errors = []
    for row in bindings.get("stream_contract_trace", []):
        bits = scalar(row.get("element_bits"), -1)
        if scalar(row.get("src_output_bits"), -2) != bits:
            errors.append(f"{row.get('edge_id')}: src_output_bits={row.get('src_output_bits')} expected {bits}")
        if scalar(row.get("dst_input_bits"), -2) != bits:
            errors.append(f"{row.get('edge_id')}: dst_input_bits={row.get('dst_input_bits')} expected {bits}")
        if row.get("stream_order") != ["token", "tile", "lane", "word"]:
            errors.append(f"{row.get('edge_id')}: unexpected stream_order={row.get('stream_order')}")
    if errors:
        return fail_row("edge_dtype_stream_contract_check", errors)
    return pass_row("edge_dtype_stream_contract_check", f"edges={len(bindings.get('stream_contract_trace', []))}")


def check_stream_packing(bindings: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    shape = constraint_facts(state, "constraint.shape.model")
    axi = board_axi(state)
    axi_bits = scalar(axi.get("data_width_bits"), 512)
    errors = []
    for item in bindings.get("bindings", []):
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        lanes = scalar(params.get("lanes"), 0)
        if lanes <= 0:
            errors.append(f"{item.get('stage_id')}: lanes must be positive")
            continue
        in_dim, out_dim = dim_pair(item)
        dimensions = [("input", in_dim), ("output", out_dim)]
        if item.get("template_id") == "attention":
            dimensions.append(("head_dim", shape.get("head_dim")))
        for name, dim in dimensions:
            if isinstance(dim, int) and dim % lanes != 0:
                errors.append(f"{item.get('stage_id')}: {name} dimension {dim} is not divisible by lanes={lanes}")
        for key in ["input_bits", "elem_bits", "output_bits"]:
            bits = scalar(params.get(key), 0)
            if bits <= 0:
                errors.append(f"{item.get('stage_id')}: {key} must be positive")
                continue
            datapath = lanes * bits
            if axi_bits % datapath != 0:
                errors.append(f"{item.get('stage_id')}: lanes*{key}={datapath} does not divide axi_data_width_bits={axi_bits}")
        rows = scalar(params.get("compute_array_rows"), 0)
        cols = scalar(params.get("compute_array_cols"), 0)
        if rows <= 0 or cols <= 0:
            errors.append(f"{item.get('stage_id')}: compute_array_rows and compute_array_cols must be positive")
        elif rows > lanes or cols > lanes or lanes % rows != 0 or lanes % cols != 0:
            errors.append(f"{item.get('stage_id')}: compute array {rows}x{cols} must tile lanes={lanes}")
        elif cols & (cols - 1):
            errors.append(f"{item.get('stage_id')}: compute_array_cols={cols} must be a power of two")
    if errors:
        return fail_row("stream_packing_axi_check", errors)
    return pass_row("stream_packing_axi_check", f"axi_bits={axi_bits}")


def check_axi_transfer_layout(bindings: dict[str, Any]) -> dict[str, Any]:
    layout = bindings.get("axi_transfer_layout", {}) if isinstance(bindings.get("axi_transfer_layout"), dict) else {}
    axi = layout.get("board_axi", {}) if isinstance(layout.get("board_axi"), dict) else {}
    alignment = scalar(axi.get("alignment_bytes"), 64)
    errors = []
    if not layout.get("per_stage"):
        errors.append("axi_transfer_layout.per_stage is empty")
    for row in layout.get("per_stage", []):
        aligned = scalar(row.get("aligned_bytes"), 0)
        if aligned <= 0:
            errors.append(f"{row.get('stage_id')}: aligned_bytes must be positive")
        if alignment > 1 and aligned % alignment != 0:
            errors.append(f"{row.get('stage_id')}: aligned_bytes={aligned} is not aligned to {alignment}")
        if scalar(row.get("axi_beats"), 0) <= 0:
            errors.append(f"{row.get('stage_id')}: axi_beats must be positive")
    if errors:
        return fail_row("axi_transfer_layout_check", errors)
    return pass_row("axi_transfer_layout_check", f"total_aligned_bytes_per_layer={layout.get('total_aligned_bytes_per_layer')}")


def check_fifo_contract(bindings: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    errors = []
    for item in plan.get("buffer_plan", []):
        if item.get("kind") != "bounded_ready_valid_fifo":
            errors.append(f"{item.get('buffer_id')}: unsupported buffer kind {item.get('kind')}")
        if scalar(item.get("depth"), 0) <= 0:
            errors.append(f"{item.get('buffer_id')}: depth must be positive")
    if errors:
        return fail_row("fifo_contract_check", errors)
    return pass_row("fifo_contract_check", f"edge_buffers={len(plan.get('buffer_plan', []))}; stage fifo_depth is local default, Stage3 edge buffer depths remain authoritative")


def check_physical_implementation(bindings: dict[str, Any]) -> dict[str, Any]:
    errors = []
    global_params = bindings.get("global_params", {})
    for key, expected in PHYSICAL_IMPLEMENTATION.items():
        if global_params.get(key) != expected:
            errors.append(f"global_params.{key}={global_params.get(key)!r} expected {expected!r}")
    for item in bindings.get("bindings", []):
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        for key, expected in PHYSICAL_IMPLEMENTATION.items():
            if params.get(key) != expected:
                errors.append(f"{item.get('stage_id')}: {key}={params.get(key)!r} expected {expected!r}")
    if errors:
        return fail_row("physical_implementation_binding_check", errors)
    return pass_row(
        "physical_implementation_binding_check",
        "compute=vivado_fp_ip, weights=xpm_uram, activations/fifos=xpm_bram",
    )


def run_parameter_static_checks(state: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    rows = [
        check_stage_numeric_contract(state, bindings),
        check_edge_dtype_contract(bindings),
        check_stream_packing(bindings, state),
        check_axi_transfer_layout(bindings),
        check_fifo_contract(bindings, state),
        check_physical_implementation(bindings),
    ]
    errors = [
        f"{row['checker']}: {error}"
        for row in rows
        if row.get("status") != "pass"
        for error in row.get("errors", [])
    ]
    warnings = [f"{row['checker']}: {warning}" for row in rows for warning in row.get("warnings", [])]
    return {
        "schema_version": "spatialaccagent.parameter_static_checks.v0",
        "stage": "parameter_binding",
        "status": "pass" if not errors else "fail",
        "checker_results": rows,
        "summary": {
            "passed": sum(1 for row in rows if row.get("status") == "pass"),
            "failed": sum(1 for row in rows if row.get("status") != "pass"),
            "errors": errors,
            "warnings": warnings,
        },
    }


def stage_gate_policy() -> dict[str, Any]:
    return {
        "current_stage_acceptance": [
            "per-stage params must match Stage 3 numeric_contract and edge stream_contract bit widths",
            "per-stage tile overrides are authoritative and must divide the corresponding tensor dimensions",
            "lanes and all bound bit widths must pack cleanly into the board AXI data width",
            "compute_array_rows and compute_array_cols must tile vector lanes; every PE maps to one physical Vivado multiplier IP",
            "the concrete AXI transfer layout must align every transfer to the board data width; it is not bandwidth or QoR evidence",
            "Stage 3 edge FIFO contracts remain authoritative; Stage 4 local fifo_depth is a template parameter default",
        ],
        "later_stage_obligations": [
            "Stage 5 assigns concrete memory base addresses and elaborates generated Chisel",
            "Stage 6+ supplies real simulation, synthesis, timing, and board evidence",
            "Numeric rounding remains recorded as unspecified unless a later approved numeric policy binds it",
        ],
        "risk_classification_rule": "If checker_results pass, do not report resolved current-stage consistency items as risks; later-stage tool obligations belong in proposed_actions.",
    }


def evaluate_architecture_candidate(state: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    shape = constraint_facts(state, "constraint.shape.model")
    numeric = constraint_facts(state, "constraint.numeric.policy")
    design_space = constraint_facts(state, "constraint.arch.design_space")
    memory = constraint_facts(state, "constraint.memory.board")
    search = selected_search_params(
        design_space.get("search_params", {}) if isinstance(design_space.get("search_params"), dict) else {},
        parameters,
    )
    bindings = []
    errors = []
    for stage in plan.get("stages", []):
        params = bind_stage_params(stage, shape, numeric, search, parameters)
        legality_errors = check_legality(stage, params, shape, memory)
        errors.extend(legality_errors)
        bindings.append(
            {
                "stage_id": stage["stage_id"],
                "op": stage["op"],
                "template_id": stage["template_id"],
                "params": params,
                "legality_errors": legality_errors,
                "status": "ready" if not legality_errors else "incomplete",
            }
        )
    layout = physical_weight_layout(plan, parameters)
    return {
        "parameters": parameters,
        "feasible": not errors,
        "hard_constraint_errors": errors,
        "physical_weight_layout": layout,
        "binding_count": len(bindings),
    }


def measured_value(metrics: dict[str, Any], key: str) -> float:
    try:
        return float(metrics[key])
    except (KeyError, TypeError, ValueError):
        return float("inf")


def measured_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Compare only exact four-metric app-shell measurements."""

    left_metrics = (left.get("measurement") or {}).get("metrics", {})
    right_metrics = (right.get("measurement") or {}).get("metrics", {})
    left_resources = left_metrics.get("resources", {}) if isinstance(left_metrics, dict) else {}
    right_resources = right_metrics.get("resources", {}) if isinstance(right_metrics, dict) else {}
    if not isinstance(left_resources, dict) or not isinstance(right_resources, dict):
        return False
    minimize = [
        (measured_value(left_resources, key), measured_value(right_resources, key))
        for key in ("lut", "ff", "dsp", "bram18", "bram36", "uram")
    ] + [
        (measured_value(left_metrics, "power_w"), measured_value(right_metrics, "power_w")),
    ]
    maximize = [
        (measured_value(right_metrics, "clock_frequency_mhz"), measured_value(left_metrics, "clock_frequency_mhz")),
        (measured_value(right_metrics, "performance_tokens_per_second"), measured_value(left_metrics, "performance_tokens_per_second")),
    ]
    return (
        all(left_value <= right_value for left_value, right_value in minimize)
        and all(left_value <= right_value for left_value, right_value in maximize)
        and (
            any(left_value < right_value for left_value, right_value in minimize)
            or any(left_value < right_value for left_value, right_value in maximize)
        )
    )


def build_dse_search(state: dict[str, Any], run_dir: Path | None = None) -> dict[str, Any]:
    design_space = constraint_facts(state, "constraint.arch.design_space")
    search = design_space.get("search_params", {}) if isinstance(design_space.get("search_params"), dict) else {}
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    weight_roles = set(weight_role_capacity_bits(plan))
    measurements = load_latest(ledger_path(run_dir or run_dir_from_state(state)))
    records = []
    for parameters in candidate_parameter_points(search, weight_roles):
        record = evaluate_architecture_candidate(state, parameters)
        record["candidate_id"] = candidate_id(parameters)
        record["candidate_fingerprint"] = candidate_fingerprint(parameters)
        record["measurement"] = measurements.get(record["candidate_fingerprint"])
        records.append(record)
    records.sort(key=lambda record: str(record["candidate_id"]))
    materialization = validate_candidate_universe(records)
    summary = measurement_summary(records)
    measured = [
        record
        for record in records
        if isinstance(record.get("measurement"), dict)
        and record["measurement"].get("measurement_status") == "measured"
    ]
    pareto = [
        record
        for record in measured
        if not any(other is not record and measured_dominates(other, record) for other in measured)
    ]
    pareto.sort(key=lambda record: str(record["candidate_id"]))
    unmeasured_ids = [
        str(record["candidate_id"])
        for record in records
        if record.get("feasible") and record.get("measurement") is None
    ]
    return {
        "schema_version": "spatialaccagent.stage4_dse_search.v2",
        "status": "measurement_pending" if unmeasured_ids else ("complete" if pareto else "incomplete"),
        "search_space": architecture_candidate_space(search, weight_roles),
        "candidate_count": len(records),
        "records": records,
        "measurement_summary": summary,
        "unmeasured_candidate_ids": unmeasured_ids,
        "pareto_candidate_ids": [record["candidate_id"] for record in pareto],
        "policy": {
            "candidate_universe_is_complete_and_unsampled": True,
            "llm_selects_measurement_order_before_campaign_completion": True,
            "llm_selects_only_measured_pareto_candidates_after_campaign_completion": True,
            "deterministic_evaluator_enforces_hard_constraints": True,
            "static_logic_never_estimates_or_ranks_qor": True,
            "target_board_app_shell_measurements_are_the_only_qor_authority": True,
            "candidate_dimensions_must_reach_generated_fpga_ip": True,
        },
        "candidate_materialization": materialization,
    }


def select_dse_candidate(dse: dict[str, Any], llm_output: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    records = {
        str(record.get("candidate_id")): record
        for record in dse.get("records", [])
        if isinstance(record, dict) and record.get("candidate_id")
    }
    campaign_complete = bool((dse.get("measurement_summary") or {}).get("complete"))
    eligible_ids = (
        [str(value) for value in dse.get("pareto_candidate_ids", []) if str(value) in records]
        if campaign_complete
        else [str(value) for value in dse.get("unmeasured_candidate_ids", []) if str(value) in records]
    )
    requested = str(llm_output.get("selected_candidate_id") or "")
    if not eligible_ids:
        raise ValueError("Stage4 DSE has no eligible candidate for exact measurement or final Pareto selection")
    if requested not in eligible_ids:
        raise ValueError(
            "Stage4 DSE requires the LLM to select one explicit eligible candidate; "
            f"requested={requested or '<missing>'}, eligible={eligible_ids}"
        )
    ranked = [str(value) for value in llm_output.get("ranked_candidate_ids", []) if str(value) in eligible_ids]
    selected_id = requested
    selected = records[selected_id]
    rationale = {
        "schema_version": "spatialaccagent.stage4_dse_selection_rationale.v2",
        "status": "ready",
        "selected_candidate_id": selected_id,
        "selection_source": (
            "llm_measured_pareto_selection" if campaign_complete else "llm_measurement_order"
        ),
        "campaign_complete": campaign_complete,
        "llm_requested_candidate_id": requested or None,
        "llm_ranked_candidate_ids": ranked,
        "llm_rationale": str(llm_output.get("selection_rationale") or ""),
        "llm_assumptions": [str(value) for value in llm_output.get("assumptions", []) if str(value)],
        "eligibility_reason": (
            "Selected candidate belongs to the exact measured Pareto frontier."
            if campaign_complete
            else "Selected candidate is legal and has no target-board app-shell measurement yet."
        ),
        "requires_measurement": [] if campaign_complete else [
            "integrated Vivado implementation resources",
            "post-implementation Vivado power",
            "achieved clock frequency",
            "hardware-counter-derived tokens per second",
        ],
    }
    return selected, rationale


def dse_llm_candidate_record(record: dict[str, Any]) -> dict[str, Any]:
    """Project one physical candidate into the LLM decision evidence.

    The evaluator keeps the complete candidate records on disk.  The selector
    only needs the immutable candidate identity, hardware-effective parameters,
    legality, and measured QoR; sending the repeated structural bindings and
    full candidate universe makes the prompt exceed the provider context.
    """

    parameters = record.get("parameters", {})
    parameters = parameters if isinstance(parameters, dict) else {}
    measurement = record.get("measurement")
    measurement = measurement if isinstance(measurement, dict) else None
    metrics = measurement.get("metrics", {}) if measurement else {}
    metrics = metrics if isinstance(metrics, dict) else {}
    resources = metrics.get("resources", {})
    resources = resources if isinstance(resources, dict) else {}
    return {
        "candidate_id": record.get("candidate_id"),
        "parameters": {
            key: parameters.get(key)
            for key in (
                "lanes",
                "compute_array_rows",
                "compute_array_cols",
                "fifo_depth",
                "activation_banks",
                "weight_banks",
                "weight_banks_by_role",
            )
            if parameters.get(key) is not None
        },
        "feasible": bool(record.get("feasible")),
        "hard_constraint_errors": list(record.get("hard_constraint_errors", [])),
        "measurement_status": measurement.get("measurement_status") if measurement else "unmeasured",
        "measurement": (
            {
                "clock_frequency_mhz": metrics.get("clock_frequency_mhz"),
                "performance_tokens_per_second": metrics.get("performance_tokens_per_second"),
                "power_w": metrics.get("power_w"),
                "resources": {
                    key: resources.get(key)
                    for key in ("lut", "ff", "dsp", "bram18", "bram36", "uram")
                    if resources.get(key) is not None
                },
            }
            if measurement
            else None
        ),
    }


def dse_llm_selection_evidence(
    dse: dict[str, Any],
    eligible_records: list[dict[str, Any]],
    pareto_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a bounded, non-lossy candidate view for the DSE selector."""

    search_space = dse.get("search_space", {})
    search_space = search_space if isinstance(search_space, dict) else {}
    return {
        "schema_version": "spatialaccagent.stage4_dse_llm_selection_evidence.v1",
        "candidate_count": dse.get("candidate_count"),
        "measurement_summary": dse.get("measurement_summary", {}),
        "candidate_dimensions": {
            key: search_space.get(key, [])
            for key in (
                "lanes",
                "compute_array_rows",
                "compute_array_cols",
                "fifo_depth",
                "activation_banks",
            )
        },
        "eligible_candidates": [
            dse_llm_candidate_record(record)
            for record in eligible_records
            if isinstance(record, dict)
        ],
        "measured_pareto_candidates": [
            dse_llm_candidate_record(record)
            for record in pareto_records
            if isinstance(record, dict)
        ],
        "policy": {
            "candidate_ids_and_parameters_are_complete_for_selection": True,
            "eligible_candidates_are_the_only_selectable_candidates": True,
            "unmeasured_candidates_must_be_selected_before_pareto_selection": True,
            "qor_is_valid_only_when_measurement_status_is_measured": True,
        },
    }


def build_parameter_bindings(state: dict[str, Any], selected_architecture: dict[str, Any] | None = None) -> dict[str, Any]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    shape = constraint_facts(state, "constraint.shape.model")
    numeric = constraint_facts(state, "constraint.numeric.policy")
    design_space = constraint_facts(state, "constraint.arch.design_space")
    memory = constraint_facts(state, "constraint.memory.board")
    selected_architecture = selected_architecture or {}
    search = selected_search_params(
        design_space.get("search_params", {}) if isinstance(design_space.get("search_params"), dict) else {},
        selected_architecture,
    )
    qor_targets = design_space.get("qor_targets", {}) if isinstance(design_space.get("qor_targets"), dict) else {}
    target_clock = scalar(qor_targets.get("clock_frequency_mhz"), 0)
    if target_clock > 0 and selected_clock_target_mhz(search) is None:
        search = dict(search)
        search["clock_target_mhz"] = [target_clock]
    default_weight_banks = scalar(selected_architecture.get("weight_banks"), scalar(first_value(search, "weight_banks", 1), 1))
    weight_terms = semantic_weight_storage_terms(plan)
    weight_layout = physical_weight_layout(plan, {**selected_architecture, "weight_banks": default_weight_banks})
    bindings = []
    errors = []
    structures = []
    for stage in plan.get("stages", []):
        params = bind_stage_params(stage, shape, numeric, search, selected_architecture)
        legality_errors = check_legality(stage, params, shape, memory)
        structure = stage_structural_dimensions(stage, params, weight_terms)
        errors.extend(legality_errors)
        structures.append({"stage_id": stage["stage_id"], "op": stage["op"], **structure})
        bindings.append(
            {
                "stage_id": stage["stage_id"],
                "op": stage["op"],
                "template_id": stage["template_id"],
                "input_shape": stage.get("input_shape", {}),
                "output_shape": stage.get("output_shape", {}),
                "params": params,
                "legality_errors": legality_errors,
                "structural_dimensions": structure,
                "status": "ready" if not legality_errors else "incomplete",
            }
        )
    lane_values = [item["params"].get("lanes") for item in bindings if item["params"].get("lanes")]
    compute_row_values = [item["params"].get("compute_array_rows") for item in bindings if item["params"].get("compute_array_rows")]
    compute_col_values = [item["params"].get("compute_array_cols") for item in bindings if item["params"].get("compute_array_cols")]
    fifo_values = [item["params"].get("fifo_depth") for item in bindings if item["params"].get("fifo_depth")]
    activation_bank_values = [
        item["params"].get("activation_banks")
        for item in bindings
        if item["params"].get("activation_banks")
    ]
    clock_values = [item["params"].get("clock_target_mhz") for item in bindings if item["params"].get("clock_target_mhz")]
    clock_target = clock_values[0] if clock_values else selected_clock_target_mhz(search)
    result = {
        "schema_version": "spatialaccagent.parameter_binding.v0",
        "stage": "parameter_binding",
        "status": "ready" if not errors else "incomplete",
        "binding_policy": "stage2_strict_binding_plus_checked_global_defaults",
        "bindings": bindings,
        "stage_structural_dimensions": structures,
        "legality_errors": errors,
        "global_params": {
            "lanes": lane_values[0] if lane_values else selected_architecture.get("lanes", first_value(search, "lanes", 8)),
            "compute_array_rows": compute_row_values[0] if compute_row_values else selected_architecture.get("compute_array_rows", first_nested_candidate(search, "compute_array", "rows", 8)),
            "compute_array_cols": compute_col_values[0] if compute_col_values else selected_architecture.get("compute_array_cols", first_nested_candidate(search, "compute_array", "cols", 8)),
            "fifo_depth": fifo_values[0] if fifo_values else selected_architecture.get("fifo_depth", selected_fifo_depth(search, 16)),
            "weight_banks": selected_architecture.get("weight_banks", first_value(search, "weight_banks", 1)),
            "activation_banks": (
                activation_bank_values[0]
                if activation_bank_values
                else selected_architecture.get("activation_banks", first_value(search, "buffer_banks", 2))
            ),
            "weight_banks_by_role": weight_layout["weight_banks_by_role"],
            "burst_beats": selected_architecture.get("burst_beats", first_value(search, "burst_beats", 1)),
            "pipeline_depth": selected_architecture.get("pipeline_depth", first_value(search, "pipeline_depth", 1)),
            "clock_target_mhz": clock_target,
            "input_bits": fallback_params(shape, numeric, search)["input_bits"],
            "elem_bits": fallback_params(shape, numeric, search)["elem_bits"],
            "output_bits": fallback_params(shape, numeric, search)["output_bits"],
            **{
                key: selected_architecture.get(key, value)
                for key, value in PHYSICAL_IMPLEMENTATION.items()
            },
        },
        "global_param_scope": {
            "compute_array_rows": "physical MAC-array row count; each PE row maps to an output lane group",
            "compute_array_cols": "physical MAC-array column count; each PE column maps to an input lane group",
            "fifo_depth": "local template default only; Stage 3 buffer_plan owns edge FIFO depths",
            "weight_banks": "physical XPM weight-bank parameter retained across DSE backtracks",
            "activation_banks": "physical XPM activation-bank parameter retained across DSE backtracks",
            "burst_beats": "generator compatibility default; excluded from DSE until it changes generated board behavior",
            "pipeline_depth": "generator compatibility default; excluded from DSE until it changes generated hardware",
            "clock_target_mhz": "board shell clock is unknown unless non-null; this is not timing evidence",
        },
        "numeric_binding_plan": numeric_binding_plan(state, bindings),
        "stream_contract_trace": stream_contract_trace(state, bindings),
        "axi_transfer_layout": build_axi_transfer_layout(state, bindings),
        "stage_gate_policy": stage_gate_policy(),
        "selected_architecture_parameters": selected_architecture,
        "physical_weight_layout": weight_layout,
        "constraints_touched": TOUCHED_CONSTRAINTS,
    }
    checks = run_parameter_static_checks(state, result)
    result["checker_results"] = checks["checker_results"]
    result["checker_summary"] = checks["summary"]
    if checks["status"] != "pass":
        result["status"] = "incomplete"
    return result


def stage_worker_errors(output: dict[str, Any], memory_truth: dict[str, Any] | None = None) -> list[str]:
    if not output:
        return []
    errors = []
    status = str(output.get("status") or "").strip().lower()
    inactive_memory_blocker_claim = status_claims_inactive_sacg_memory_blocker(status, memory_truth)
    if not stage_status_allows_promotion(status) and not inactive_memory_blocker_claim:
        errors.append(f"dse_parameter_agent status is {output.get('status')}")
        risks = output.get("risks", [])
        if isinstance(risks, list) and risks:
            errors.append(f"dse_parameter_agent reported {len(risks)} unresolved risk(s)")
    return errors


def update_sacg(
    source_state: Path,
    target_state: Path,
    binding_path: Path,
    check_path: Path,
    dse_paths: dict[str, Path],
    bindings: dict[str, Any],
    selected_architecture: dict[str, Any],
    selection_rationale: dict[str, Any],
    checks: dict[str, Any],
    errors: list[str],
) -> str:
    state = copy_state(source_state, target_state)
    node_ids = [f"node.pipeline.{item['stage_id']}" for item in bindings["bindings"]]
    edge_ids = [str(item.get("edge_id")) for item in bindings.get("stream_contract_trace", []) if item.get("edge_id")]
    artifact_ids = [
        "artifact.stage4.dse_search_space",
        "artifact.stage4.dse_candidate_records",
        "artifact.stage4.dse_constraint_report",
        "artifact.stage4.dse_pareto_frontier",
        "artifact.stage4.dse_measurements",
        "artifact.stage4.selected_architecture",
        "artifact.stage4.dse_selection_rationale",
        "artifact.stage4.parameter_binding",
        "artifact.stage4.parameter_static_checks",
    ]
    add_constraint(
        state,
        "constraint.dse.selection",
        "architecture",
        node_ids,
        edge_ids,
        artifact_ids,
        {
            "selected_candidate_id": selected_architecture.get("candidate_id"),
            "parameters": selected_architecture.get("parameters", {}),
            "selection_source": selection_rationale.get("selection_source"),
            "requires_measurement": selection_rationale.get("requires_measurement", []),
            "policy": "Static checks select only legal hardware-effective candidates; target-board app-shell measurements determine Pareto membership and final QoR selection.",
        },
    )
    add_constraint(
        state,
        "constraint.parameter.binding",
        "parameter",
        node_ids,
        edge_ids,
        artifact_ids,
        {
            "binding_policy": bindings["binding_policy"],
            "global_params": bindings["global_params"],
            "global_param_scope": bindings.get("global_param_scope", {}),
            "numeric_binding_plan": bindings.get("numeric_binding_plan", {}),
            "stream_contract_trace": bindings.get("stream_contract_trace", []),
            "legality_errors": bindings.get("legality_errors", []),
            "checker_summary": bindings.get("checker_summary", {}),
        },
    )
    add_constraint(
        state,
        "constraint.parameter.structure",
        "parameter",
        node_ids,
        edge_ids,
        artifact_ids,
        {
            "stage_structural_dimensions": bindings.get("stage_structural_dimensions", []),
            "used_for": "parameter legality and AXI layout only; never resource, timing, power, or performance evidence",
        },
    )
    add_constraint(
        state,
        "constraint.axi.layout",
        "memory",
        node_ids,
        edge_ids,
        artifact_ids,
        {
            "datapath_bits": [
                item.get("structural_dimensions", {}).get("datapath_bits")
                for item in bindings.get("bindings", [])
            ],
            "axi_transfer_layout": bindings.get("axi_transfer_layout", {}),
            "rule": "datapath width must align with board AXI/DDR data width before code generation",
        },
    )
    add_invariant(
        state,
        "invariant.parameter_binding_static",
        "parameter_binding_static_check",
        ["constraint.parameter.binding"],
    )
    add_invariant(
        state,
        "invariant.parameter_structure_axi_layout",
        "parameter_structure_axi_layout_check",
        ["constraint.parameter.structure", "constraint.axi.layout"],
    )
    write_json(target_state, state)

    store = SACGStore(target_state)
    transition = store.declare_transition(
        action_type="parameter_binding",
        touched_nodes=["node.design_space", *node_ids],
        touched_edges=edge_ids,
        touched_constraints=TOUCHED_CONSTRAINTS,
        note="Bound one legal hardware-effective candidate for exact target-board app-shell measurement or measured Pareto selection.",
    )
    for artifact_id, key in [
        ("artifact.stage4.dse_search_space", "search_space"),
        ("artifact.stage4.dse_candidate_records", "candidate_records"),
        ("artifact.stage4.dse_constraint_report", "constraint_report"),
        ("artifact.stage4.dse_pareto_frontier", "pareto_frontier"),
        ("artifact.stage4.dse_measurements", "measurements"),
        ("artifact.stage4.selected_architecture", "selected_architecture"),
        ("artifact.stage4.dse_selection_rationale", "selection_rationale"),
    ]:
        store.bind_artifact(
            artifact_id,
            str(dse_paths[key]),
            "stage.dse_selection",
            node_ids,
            edge_ids,
            TOUCHED_CONSTRAINTS,
            transition["id"],
        )
    store.bind_artifact(
        "artifact.stage4.parameter_binding",
        str(binding_path),
        "stage.parameter_binding",
        node_ids,
        edge_ids,
        TOUCHED_CONSTRAINTS,
        transition["id"],
    )
    store.bind_artifact(
        "artifact.stage4.parameter_static_checks",
        str(check_path),
        "stage.parameter_static_checks",
        node_ids,
        edge_ids,
        TOUCHED_CONSTRAINTS,
        transition["id"],
    )
    evidence_status = "pass" if checks.get("status") == "pass" else "fail"
    evidence_summary = str((checks.get("summary") or {}).get("errors") or "parameter static checks passed")
    store.attach_evidence(
        checker="parameter_binding_static_check",
        status=evidence_status,
        invariant="invariant.parameter_binding_static",
        constraints=["constraint.parameter.binding"],
        artifacts=["artifact.stage4.parameter_binding", "artifact.stage4.parameter_static_checks"],
        log_path=str(check_path),
        transition_id=transition["id"],
        summary=evidence_summary,
    )
    store.attach_evidence(
        checker="parameter_structure_axi_layout_check",
        status=evidence_status,
        invariant="invariant.parameter_structure_axi_layout",
        constraints=["constraint.parameter.structure", "constraint.axi.layout"],
        artifacts=["artifact.stage4.parameter_binding", "artifact.stage4.parameter_static_checks"],
        log_path=str(check_path),
        transition_id=transition["id"],
        summary=evidence_summary,
    )
    if not errors and checks.get("status") == "pass":
        store.promote(transition["id"])
    else:
        store.reject(transition["id"], f"parameter binding failed gate checks: {errors[:8]}")
        store.record_failure_lesson(
            stage="stage4.parameter_binding",
            failure_class="parameter_binding_static",
            summary=f"parameter binding failed gate checks: {errors[:8]}",
            violated_constraints=TOUCHED_CONSTRAINTS,
            artifacts=artifact_ids,
            recommended_action="Rerun Stage4 after the LLM design team resolves parameter legality or AXI-layout blockers; do not feed rejected parameter bindings into code generation.",
            retry_scope="same_stage",
        )
        store.record_retry_request(
            stage="stage4.parameter_binding",
            reason="Stage4 parameter binding did not pass static parameter or AXI-layout gates",
            target_stage="stage4.parameter_binding",
            required_inputs=["artifact.stage3.pipeline_plan", "constraint.shape.model", "constraint.numeric.policy", "constraint.arch.design_space"],
            blocked_artifacts=artifact_ids,
        )
    store.record_stage_outcome(
        stage="stage4.parameter_binding",
        status="ready" if not errors and checks.get("status") == "pass" else "incomplete",
        transition_id=transition["id"],
        summary=evidence_summary,
        errors=errors,
        artifacts=artifact_ids,
        next_actions=[] if not errors else ["retry stage4.parameter_binding before Stage5 code generation"],
        retryable=bool(errors),
    )
    store.save()
    return transition["id"]


def bind_parameters(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "parameter_binding"
    binding_path = out_dir / "parameter_binding.json"
    check_path = out_dir / "parameter_static_checks.json"
    dse_search_path = out_dir / "dse_search_space.json"
    dse_records_path = out_dir / "dse_candidate_records.jsonl"
    dse_constraint_path = out_dir / "dse_constraint_report.json"
    dse_pareto_path = out_dir / "dse_pareto_frontier.json"
    dse_measurements_path = ledger_path(run_dir)
    selected_architecture_path = out_dir / "selected_architecture.json"
    selection_rationale_path = out_dir / "dse_selection_rationale.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "parameter_binding_report.json"

    source_data = read_json(source_state)
    memory_truth = sacg_memory_truth(source_data)
    dse = build_dse_search(source_data, run_dir)
    dse_measurements_path.parent.mkdir(parents=True, exist_ok=True)
    dse_measurements_path.touch(exist_ok=True)
    eligible_candidate_ids = (
        dse.get("pareto_candidate_ids", [])
        if (dse.get("measurement_summary") or {}).get("complete")
        else dse.get("unmeasured_candidate_ids", [])
    )
    eligible_records = [
        record
        for record in dse["records"]
        if record.get("candidate_id") in set(eligible_candidate_ids)
    ]
    dse_search = {
        "schema_version": dse["schema_version"],
        "status": dse["status"],
        "search_space": {
            key: dse["search_space"].get(key, [])
            for key in (
                "lanes",
                "compute_array_rows",
                "compute_array_cols",
                "fifo_depth",
                "activation_banks",
            )
        },
        "candidate_count": dse["candidate_count"],
        "measurement_summary": dse["measurement_summary"],
        "unmeasured_candidate_ids": dse["unmeasured_candidate_ids"],
        "policy": dse["policy"],
        "measurement_ledger": str(dse_measurements_path),
    }
    write_json(dse_search_path, dse_search)
    dse_records_path.parent.mkdir(parents=True, exist_ok=True)
    dse_records_path.write_text(
        "".join(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n" for record in dse["records"]),
        encoding="utf-8",
    )
    pareto_records = [
        record for record in dse["records"]
        if record.get("candidate_id") in set(dse.get("pareto_candidate_ids", []))
    ]
    dse_constraint_report = {
        "schema_version": "spatialaccagent.stage4_dse_constraint_report.v1",
        "status": "pass" if any(record.get("feasible") for record in dse["records"]) else "fail",
        "candidate_count": dse["candidate_count"],
        "feasible_candidate_count": sum(1 for record in dse["records"] if record.get("feasible")),
        "infeasible_candidates": [
            {
                "candidate_id": record.get("candidate_id"),
                "hard_constraint_errors": record.get("hard_constraint_errors", []),
            }
            for record in dse["records"]
            if not record.get("feasible")
        ],
        "policy": dse["policy"],
        "candidate_materialization": dse.get("candidate_materialization", {}),
    }
    write_json(dse_constraint_path, dse_constraint_report)
    write_json(
        dse_pareto_path,
        {
            "schema_version": "spatialaccagent.stage4_dse_pareto_frontier.v1",
            "status": "ready" if (dse.get("measurement_summary") or {}).get("complete") and pareto_records else "measurement_pending",
            "candidate_ids": dse.get("pareto_candidate_ids", []),
            "records": pareto_records,
            "objectives": [
                "minimize measured resources",
                "minimize measured power",
                "maximize measured achieved clock",
                "maximize measured tokens per second",
            ],
        },
    )
    campaign_complete = bool((dse.get("measurement_summary") or {}).get("complete"))
    selection_evidence = dse_llm_selection_evidence(dse, eligible_records, pareto_records)
    llm = run_stage_agent(
        agent="dse_parameter_agent",
        stage="parameter_binding",
        task=(
            "Select the next exact-measurement candidate from the supplied legal candidate universe. "
            "If and only if all legal candidates have target-board app-shell measurements, select a candidate "
            "from the supplied measured Pareto frontier. Do not invent parameter values, QoR values, or select "
            "outside the supplied eligible candidates."
        ),
        inputs={
            "dse_search_space": dse_search,
            "dse_selection_evidence": selection_evidence,
            "formal_dse_campaign": {
                "campaign_complete": campaign_complete,
                "eligible_candidate_ids": eligible_candidate_ids,
                "eligible_candidate_count": len(eligible_records),
                "measured_pareto_frontier": {
                    "candidate_ids": dse.get("pareto_candidate_ids", []),
                    "candidate_count": len(pareto_records),
                },
            },
            "dse_constraint_report": dse_constraint_report,
            "current_sacg_memory_truth": memory_truth,
            "source_sacg_state": str(source_state),
        },
        out_dir=out_dir,
        fallback_summary="Deterministic Stage4 DSE evaluated legal architecture candidates.",
        output_schema=DSE_SELECTION_SCHEMA,
        prompt_rules=[
            "Before all legal candidates are measured, choose only one supplied unmeasured legal candidate as the next app-shell measurement; do not call it optimal or Pareto-optimal.",
            "After the campaign is complete, choose only a supplied measured Pareto candidate using the four real objectives: resources, power, clock frequency, and tokens per second.",
            "Never estimate, extrapolate, predict, or invent resources, power, clock, or performance. Only candidate-specific app-shell measurements are QoR evidence.",
            "Rank at least the selected candidate and state the assumptions that make the choice appropriate.",
            "The deterministic evaluator owns legality and hardware-effective parameter filtering; do not modify candidate parameters or claim a hardware pass before measurement.",
            "dse_selection_evidence is the complete current candidate decision set; use its candidate_id and parameters directly. Do not claim that the candidate universe or measurement status is absent merely because full evaluator records are stored on disk.",
        ],
    )
    selected_architecture, selection_rationale = select_dse_candidate(dse, llm["output"])
    write_json(selected_architecture_path, selected_architecture)
    write_json(selection_rationale_path, selection_rationale)
    bindings = build_parameter_bindings(source_data, selected_architecture.get("parameters", {}))
    bindings["selected_architecture"] = {
        "candidate_id": selected_architecture.get("candidate_id"),
        "parameters": selected_architecture.get("parameters", {}),
        "measurement": selected_architecture.get("measurement"),
        "selection_rationale": str(selection_rationale_path),
    }
    checks = {
        "schema_version": "spatialaccagent.parameter_static_checks.v0",
        "stage": "parameter_binding",
        "status": "pass" if not (bindings.get("checker_summary") or {}).get("errors") else "fail",
        "checker_results": bindings.get("checker_results", []),
        "summary": bindings.get("checker_summary", {}),
    }
    write_json(binding_path, bindings)
    write_json(check_path, checks)
    team = run_design_team(
        stage="parameter_binding",
        objective="Audit the selected legal DSE architecture and its exact target-board measurement obligations without changing model or numeric semantics.",
        state=source_data,
        candidate_artifact=bindings,
        out_dir=out_dir,
    )
    design_team = team_summary(team)
    errors = list((checks.get("summary") or {}).get("errors") or [])
    errors.extend(bindings.get("legality_errors", []))
    errors.extend(team_failure_errors(design_team))
    errors.extend(stage_worker_errors(llm["output"], memory_truth))
    inactive_memory_blocker_claim = status_claims_inactive_sacg_memory_blocker(
        (llm.get("output") or {}).get("status"),
        memory_truth,
    )
    dse_paths = {
        "search_space": dse_search_path,
        "candidate_records": dse_records_path,
        "constraint_report": dse_constraint_path,
        "pareto_frontier": dse_pareto_path,
        "selected_architecture": selected_architecture_path,
        "selection_rationale": selection_rationale_path,
        "measurements": dse_measurements_path,
    }
    transition_id = update_sacg(
        source_state,
        state_path,
        binding_path,
        check_path,
        dse_paths,
        bindings,
        selected_architecture,
        selection_rationale,
        checks,
        errors,
    )
    report = {
        "schema_version": "spatialaccagent.parameter_binding_report.v0",
        "stage": "parameter_binding",
        "status": "ready" if not errors else "incomplete",
        "source_sacg_state": str(source_state),
        "outputs": {
            "parameter_binding": str(binding_path),
            "parameter_static_checks": str(check_path),
            "dse_search_space": str(dse_search_path),
            "dse_candidate_records": str(dse_records_path),
            "dse_constraint_report": str(dse_constraint_path),
            "dse_pareto_frontier": str(dse_pareto_path),
            "dse_measurements": str(dse_measurements_path),
            "selected_architecture": str(selected_architecture_path),
            "dse_selection_rationale": str(selection_rationale_path),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        },
        "llm_agent": llm["output"],
        "llm_memory_claim_audit": {
            "schema_version": "spatialaccagent.llm_memory_claim_audit.v0",
            "inactive_sacg_memory_blocker_status_ignored": inactive_memory_blocker_claim,
            "sacg_memory_truth": memory_truth,
        },
        "llm_executable_actions": llm["output"].get("executable_actions", []),
        "design_team": design_team,
        "team_executable_actions": design_team.get("executable_actions", []),
        "num_bindings": len(bindings["bindings"]),
        "global_params": bindings["global_params"],
        "selected_architecture": bindings.get("selected_architecture", {}),
        "dse_measurement_summary": dse.get("measurement_summary", {}),
        "dse_selection_rationale": selection_rationale,
        "checker_summary": checks.get("summary", {}),
        "numeric_binding_plan": bindings.get("numeric_binding_plan", {}),
        "stream_contract_trace": bindings.get("stream_contract_trace", []),
        "axi_transfer_layout": bindings.get("axi_transfer_layout", {}),
        "legality_errors": errors,
        "sacg_transition_id": transition_id,
        "errors": errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Parameter binding stage", bind_parameters, argv)


if __name__ == "__main__":
    raise SystemExit(main())
