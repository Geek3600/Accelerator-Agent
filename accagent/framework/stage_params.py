"""Bind model, numeric, and architecture parameters to selected stages."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

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
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary


TOUCHED_CONSTRAINTS = [
    "constraint.parameter.binding",
    "constraint.resource.estimate",
    "constraint.bandwidth.estimate",
]


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
    return {
        "hidden_size": shape.get("hidden_size"),
        "intermediate_size": shape.get("intermediate_size"),
        "num_q_heads": shape.get("num_q_heads"),
        "num_kv_heads": shape.get("num_kv_heads"),
        "head_dim": shape.get("head_dim"),
        "seq_len": shape.get("target_max_seq_len"),
        "lanes": first_value(search, "lanes", 8),
        "tile_m": first_value(search, "tile_m", 8),
        "tile_n": first_value(search, "tile_n", 24),
        "tile_k": first_value(search, "tile_k", 8),
        "elem_bits": activation_bits,
        "input_bits": acc_bits,
        "output_bits": acc_bits,
        "causal": True,
        "fifo_depth": selected_fifo_depth(search, 16),
        "weight_banks": first_value(search, "weight_banks", 1),
        "buffer_banks": first_value(search, "buffer_banks", 2),
        "clock_target_mhz": selected_clock_target_mhz(search),
        "numeric_policy_id": numeric.get("policy_id"),
    }


def bind_stage_params(stage: dict[str, Any], shape: dict[str, Any], numeric: dict[str, Any], search: dict[str, Any]) -> dict[str, Any]:
    defaults = fallback_params(shape, numeric, search)
    params = defaults | concrete_bound_params(stage)
    op = str(stage.get("op"))
    if op in {"rms_norm_1", "rms_norm_2"}:
        params["input_bits"] = defaults["input_bits"]
        params["output_bits"] = defaults["elem_bits"]
    elif op in {"residual_add_1", "residual_add_2"}:
        params["elem_bits"] = defaults["output_bits"]
        params["input_bits"] = defaults["output_bits"]
        params["output_bits"] = defaults["output_bits"]
    elif op == "mlp_down_proj":
        params["input_bits"] = defaults["elem_bits"]
        params["output_bits"] = defaults["output_bits"]
    elif op == "self_attention":
        params["input_bits"] = defaults["elem_bits"]
        params["elem_bits"] = defaults["elem_bits"]
        params["output_bits"] = defaults["output_bits"]
    elif op in {"mlp_gate_proj", "mlp_up_proj", "activation_mul", "softmax"}:
        params["input_bits"] = defaults["elem_bits"]
        params["elem_bits"] = defaults["elem_bits"]
        params["output_bits"] = defaults["elem_bits"]
    required = {name: params.get(name) for name in stage.get("required_params", []) if name in params}
    return required | {
        "input_bits": params.get("input_bits"),
        "elem_bits": params.get("elem_bits"),
        "output_bits": params.get("output_bits"),
        "fifo_depth": defaults["fifo_depth"],
        "clock_target_mhz": defaults["clock_target_mhz"],
        "numeric_policy_id": defaults["numeric_policy_id"],
    }


def dim_pair(op: str, shape: dict[str, Any]) -> tuple[int | None, int | None]:
    hidden = shape.get("hidden_size")
    intermediate = shape.get("intermediate_size")
    if op in {"mlp_gate_proj", "mlp_up_proj"}:
        return hidden, intermediate
    if op == "activation_mul":
        return intermediate, intermediate
    if op == "mlp_down_proj":
        return intermediate, hidden
    return hidden, hidden


def check_legality(stage: dict[str, Any], params: dict[str, Any], shape: dict[str, Any], memory: dict[str, Any]) -> list[str]:
    errors = []
    for name in stage.get("required_params", []):
        if params.get(name) is None:
            errors.append(f"{stage['stage_id']}: missing required parameter {name}")
    lanes = params.get("lanes")
    in_dim, out_dim = dim_pair(str(stage.get("op")), shape)
    if isinstance(lanes, int) and lanes > 0:
        for dim_name, dim in [("input", in_dim), ("output", out_dim), ("head_dim", shape.get("head_dim"))]:
            if isinstance(dim, int) and dim % lanes != 0:
                errors.append(f"{stage['stage_id']}: {dim_name} dimension {dim} is not divisible by lanes={lanes}")
    elem_bits = params.get("elem_bits") or params.get("output_bits") or params.get("input_bits")
    axi_bits = (memory.get("memory_system") or {}).get("axi_data_width_bits")
    if isinstance(lanes, int) and isinstance(elem_bits, int) and isinstance(axi_bits, int):
        data_bits = lanes * elem_bits
        if data_bits > axi_bits or axi_bits % data_bits != 0:
            errors.append(f"{stage['stage_id']}: lanes*elem_bits={data_bits} is not aligned to axi_data_width_bits={axi_bits}")
    seq_len = shape.get("target_max_seq_len")
    for name, divisor in [("tile_m", seq_len), ("tile_n", out_dim), ("tile_k", in_dim)]:
        value = params.get(name)
        if isinstance(value, int) and isinstance(divisor, int) and divisor > 0 and divisor % value != 0:
            errors.append(f"{stage['stage_id']}: {name}={value} does not divide {divisor}")
    return errors


def estimate_resources(stage: dict[str, Any], params: dict[str, Any], shape: dict[str, Any]) -> dict[str, Any]:
    op = str(stage.get("op"))
    seq_len = int(shape.get("target_max_seq_len") or 1)
    hidden = int(shape.get("hidden_size") or 1)
    intermediate = int(shape.get("intermediate_size") or hidden)
    q_heads = int(shape.get("num_q_heads") or 1)
    kv_heads = int(shape.get("num_kv_heads") or q_heads)
    head_dim = int(shape.get("head_dim") or max(1, hidden // max(q_heads, 1)))
    lanes = int(params.get("lanes") or 1)
    elem_bits = int(params.get("elem_bits") or params.get("output_bits") or params.get("input_bits") or 16)
    in_dim, out_dim = dim_pair(op, shape)
    if op == "self_attention":
        weight_elements = hidden * ((q_heads + 2 * kv_heads) * head_dim + hidden)
        compute_ops = seq_len * hidden + seq_len * seq_len * q_heads * head_dim
    elif op in {"mlp_gate_proj", "mlp_up_proj"}:
        weight_elements = hidden * intermediate
        compute_ops = seq_len * hidden * intermediate
    elif op == "mlp_down_proj":
        weight_elements = intermediate * hidden
        compute_ops = seq_len * intermediate * hidden
    elif op in {"rms_norm_1", "rms_norm_2"}:
        weight_elements = hidden
        compute_ops = seq_len * hidden
    else:
        weight_elements = 0
        compute_ops = seq_len * int(out_dim or hidden)
    return {
        "estimate_kind": "symbolic_first_order",
        "used_for": "parameter binding sanity check only; not timing, implementation, or hardware pass evidence",
        "weight_elements": weight_elements,
        "activation_elements": seq_len * int(out_dim or hidden),
        "compute_ops": compute_ops,
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


def estimate_bandwidth(state: dict[str, Any], bindings: list[dict[str, Any]]) -> dict[str, Any]:
    shape = constraint_facts(state, "constraint.shape.model")
    axi = board_axi(state)
    alignment = scalar(axi.get("alignment_bytes"), 64)
    seq_len = scalar(shape.get("target_max_seq_len"), 1)
    per_stage = []
    for item in bindings:
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        op = str(item.get("op"))
        in_dim, out_dim = dim_pair(op, shape)
        input_bits = scalar(params.get("input_bits"), scalar(params.get("elem_bits"), 16))
        output_bits = scalar(params.get("output_bits"), scalar(params.get("elem_bits"), 16))
        weight_bits = scalar(params.get("elem_bits"), 16)
        estimate = item.get("resource_estimate", {}) if isinstance(item.get("resource_estimate"), dict) else {}
        input_bytes = bytes_for_elements(seq_len * scalar(in_dim, 1), input_bits)
        output_bytes = bytes_for_elements(seq_len * scalar(out_dim, 1), output_bits)
        weight_bytes = bytes_for_elements(scalar(estimate.get("weight_elements"), 0), weight_bits)
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
                "weight_bits": weight_bits,
            }
        )
    return {
        "schema_version": "spatialaccagent.parameter_bandwidth_estimate.v0",
        "estimate_kind": "symbolic_transfer_count_from_bound_params",
        "used_for": "static transfer-count and AXI packing sanity only; not board bandwidth or timing pass evidence",
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
                "residual_precision": output_bits if str(item.get("op", "")).startswith("residual_add") else None,
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
        checks = [("input_bits", "input_bits"), ("output_bits", "output_bits")]
        if str(item.get("op")) not in {"rms_norm_1", "rms_norm_2"}:
            checks.append(("internal_elem_bits", "elem_bits"))
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


def check_tile_overrides(bindings: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    shape = constraint_facts(state, "constraint.shape.model")
    errors = []
    for item in bindings.get("bindings", []):
        params = item.get("params", {}) if isinstance(item.get("params"), dict) else {}
        op = str(item.get("op"))
        in_dim, out_dim = dim_pair(op, shape)
        seq_len = scalar(shape.get("target_max_seq_len"), 1)
        for key, divisor in [("tile_m", seq_len), ("tile_n", scalar(out_dim, 1)), ("tile_k", scalar(in_dim, 1))]:
            value = params.get(key)
            if value is None:
                continue
            if scalar(value, 0) <= 0 or divisor % scalar(value, 1) != 0:
                errors.append(f"{item.get('stage_id')}: {key}={value} does not divide {divisor}")
    if errors:
        return fail_row("tile_override_legality_check", errors)
    return pass_row("tile_override_legality_check", "per-stage tile params are authoritative; global tile params are defaults only")


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
        op = str(item.get("op"))
        in_dim, out_dim = dim_pair(op, shape)
        for name, dim in [("input", in_dim), ("output", out_dim), ("head_dim", shape.get("head_dim"))]:
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
    if errors:
        return fail_row("stream_packing_axi_check", errors)
    return pass_row("stream_packing_axi_check", f"axi_bits={axi_bits}")


def check_bandwidth_estimate(bindings: dict[str, Any]) -> dict[str, Any]:
    estimate = bindings.get("bandwidth_estimate", {}) if isinstance(bindings.get("bandwidth_estimate"), dict) else {}
    axi = estimate.get("board_axi", {}) if isinstance(estimate.get("board_axi"), dict) else {}
    alignment = scalar(axi.get("alignment_bytes"), 64)
    errors = []
    if not estimate.get("per_stage"):
        errors.append("bandwidth_estimate.per_stage is empty")
    for row in estimate.get("per_stage", []):
        aligned = scalar(row.get("aligned_bytes"), 0)
        if aligned <= 0:
            errors.append(f"{row.get('stage_id')}: aligned_bytes must be positive")
        if alignment > 1 and aligned % alignment != 0:
            errors.append(f"{row.get('stage_id')}: aligned_bytes={aligned} is not aligned to {alignment}")
        if scalar(row.get("axi_beats"), 0) <= 0:
            errors.append(f"{row.get('stage_id')}: axi_beats must be positive")
    if errors:
        return fail_row("bandwidth_memory_estimate_check", errors)
    return pass_row("bandwidth_memory_estimate_check", f"total_aligned_bytes_per_layer={estimate.get('total_aligned_bytes_per_layer')}")


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


def run_parameter_static_checks(state: dict[str, Any], bindings: dict[str, Any]) -> dict[str, Any]:
    rows = [
        check_stage_numeric_contract(state, bindings),
        check_edge_dtype_contract(bindings),
        check_tile_overrides(bindings, state),
        check_stream_packing(bindings, state),
        check_bandwidth_estimate(bindings),
        check_fifo_contract(bindings, state),
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
            "bandwidth estimates must expose concrete static transfer counts and explicitly remain non-hardware evidence",
            "Stage 3 edge FIFO contracts remain authoritative; Stage 4 local fifo_depth is a template parameter default",
        ],
        "later_stage_obligations": [
            "Stage 5 assigns concrete memory base addresses and elaborates generated Chisel",
            "Stage 6+ supplies real simulation, synthesis, timing, and board evidence",
            "Numeric rounding remains recorded as unspecified unless a later approved numeric policy binds it",
        ],
        "risk_classification_rule": "If checker_results pass, do not report resolved current-stage consistency items as risks; later-stage tool obligations belong in proposed_actions.",
    }


def build_parameter_bindings(state: dict[str, Any]) -> dict[str, Any]:
    plan = read_json(artifact_path(state, "artifact.stage3.pipeline_plan"))
    shape = constraint_facts(state, "constraint.shape.model")
    numeric = constraint_facts(state, "constraint.numeric.policy")
    design_space = constraint_facts(state, "constraint.arch.design_space")
    memory = constraint_facts(state, "constraint.memory.board")
    search = design_space.get("search_params", {})
    bindings = []
    errors = []
    estimates = []
    for stage in plan.get("stages", []):
        params = bind_stage_params(stage, shape, numeric, search)
        legality_errors = check_legality(stage, params, shape, memory)
        estimate = estimate_resources(stage, params, shape)
        errors.extend(legality_errors)
        estimates.append({"stage_id": stage["stage_id"], "op": stage["op"], **estimate})
        bindings.append(
            {
                "stage_id": stage["stage_id"],
                "op": stage["op"],
                "template_id": stage["template_id"],
                "params": params,
                "legality_errors": legality_errors,
                "resource_estimate": estimate,
                "status": "ready" if not legality_errors else "incomplete",
            }
        )
    lane_values = [item["params"].get("lanes") for item in bindings if item["params"].get("lanes")]
    clock_values = [item["params"].get("clock_target_mhz") for item in bindings if item["params"].get("clock_target_mhz")]
    clock_target = clock_values[0] if clock_values else selected_clock_target_mhz(search)
    result = {
        "schema_version": "spatialaccagent.parameter_binding.v0",
        "stage": "parameter_binding",
        "status": "ready" if not errors else "incomplete",
        "binding_policy": "stage2_strict_binding_plus_checked_global_defaults",
        "bindings": bindings,
        "resource_estimates": estimates,
        "legality_errors": errors,
        "global_params": {
            "lanes": lane_values[0] if lane_values else first_value(search, "lanes", 8),
            "tile_m": first_value(search, "tile_m", 8),
            "tile_n": first_value(search, "tile_n", 24),
            "tile_k": first_value(search, "tile_k", 8),
            "fifo_depth": selected_fifo_depth(search, 16),
            "clock_target_mhz": clock_target,
            "input_bits": fallback_params(shape, numeric, search)["input_bits"],
            "elem_bits": fallback_params(shape, numeric, search)["elem_bits"],
            "output_bits": fallback_params(shape, numeric, search)["output_bits"],
        },
        "global_param_scope": {
            "tile_m": "default_only; per-stage tile_m takes precedence",
            "tile_n": "default_only; per-stage tile_n takes precedence",
            "tile_k": "default_only; per-stage tile_k takes precedence",
            "fifo_depth": "local template default only; Stage 3 buffer_plan owns edge FIFO depths",
            "clock_target_mhz": "board shell clock is unknown unless non-null; this is not timing evidence",
        },
        "numeric_binding_plan": numeric_binding_plan(state, bindings),
        "stream_contract_trace": stream_contract_trace(state, bindings),
        "bandwidth_estimate": estimate_bandwidth(state, bindings),
        "stage_gate_policy": stage_gate_policy(),
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
    bindings: dict[str, Any],
    checks: dict[str, Any],
    errors: list[str],
) -> str:
    state = copy_state(source_state, target_state)
    node_ids = [f"node.pipeline.{item['stage_id']}" for item in bindings["bindings"]]
    edge_ids = [str(item.get("edge_id")) for item in bindings.get("stream_contract_trace", []) if item.get("edge_id")]
    artifact_ids = ["artifact.stage4.parameter_binding", "artifact.stage4.parameter_static_checks"]
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
        "constraint.resource.estimate",
        "resource",
        node_ids,
        edge_ids,
        artifact_ids,
        {
            "stage_estimates": bindings.get("resource_estimates", []),
            "estimate_kind": "symbolic_first_order",
            "used_for": "parameter binding sanity only; not timing, implementation, or hardware pass evidence",
        },
    )
    add_constraint(
        state,
        "constraint.bandwidth.estimate",
        "bandwidth",
        node_ids,
        edge_ids,
        artifact_ids,
        {
            "datapath_bits": [
                item.get("resource_estimate", {}).get("datapath_bits")
                for item in bindings.get("bindings", [])
            ],
            "bandwidth_estimate": bindings.get("bandwidth_estimate", {}),
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
        "invariant.resource_estimate_static",
        "resource_estimate_static_check",
        ["constraint.resource.estimate", "constraint.bandwidth.estimate"],
    )
    write_json(target_state, state)

    store = SACGStore(target_state)
    transition = store.declare_transition(
        action_type="parameter_binding",
        touched_nodes=["node.design_space", *node_ids],
        touched_edges=edge_ids,
        touched_constraints=TOUCHED_CONSTRAINTS,
        note="Bound template parameters using the first design-space point.",
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
        checker="resource_estimate_static_check",
        status=evidence_status,
        invariant="invariant.resource_estimate_static",
        constraints=["constraint.resource.estimate", "constraint.bandwidth.estimate"],
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
            recommended_action="Rerun Stage4 after the LLM design team resolves parameter legality/resource/bandwidth blockers; do not feed rejected parameter bindings into code generation.",
            retry_scope="same_stage",
        )
        store.record_retry_request(
            stage="stage4.parameter_binding",
            reason="Stage4 parameter binding did not pass static/resource gates",
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
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "parameter_binding_report.json"

    source_data = read_json(source_state)
    memory_truth = sacg_memory_truth(source_data)
    bindings = build_parameter_bindings(source_data)
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
        objective="Bind template parameters and audit DSE/resource risks without changing model or numeric semantics.",
        state=source_data,
        candidate_artifact=bindings,
        out_dir=out_dir,
    )
    llm = run_stage_agent(
        agent="dse_parameter_agent",
        stage="parameter_binding",
        task="Review the first architecture parameter binding point, team decomposition, and DSE risks.",
        inputs={
            "candidate_parameter_binding": bindings,
            "stage_gate_policy": bindings.get("stage_gate_policy", {}),
            "checker_results": checks.get("checker_results", []),
            "checker_summary": checks.get("summary", {}),
            "parameter_static_checks": checks,
            "design_team": team_summary(team),
            "current_sacg_memory_truth": memory_truth,
            "source_sacg_state": str(source_state),
        },
        out_dir=out_dir,
        fallback_summary="Parameter binding selected the first design-space point.",
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
    transition_id = update_sacg(source_state, state_path, binding_path, check_path, bindings, checks, errors)
    report = {
        "schema_version": "spatialaccagent.parameter_binding_report.v0",
        "stage": "parameter_binding",
        "status": "ready" if not errors else "incomplete",
        "source_sacg_state": str(source_state),
        "outputs": {
            "parameter_binding": str(binding_path),
            "parameter_static_checks": str(check_path),
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
        "checker_summary": checks.get("summary", {}),
        "numeric_binding_plan": bindings.get("numeric_binding_plan", {}),
        "stream_contract_trace": bindings.get("stream_contract_trace", []),
        "bandwidth_estimate": bindings.get("bandwidth_estimate", {}),
        "legality_errors": errors,
        "resource_estimates": bindings.get("resource_estimates", []),
        "sacg_transition_id": transition_id,
        "errors": errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Parameter binding stage", bind_parameters, argv)


if __name__ == "__main__":
    raise SystemExit(main())
