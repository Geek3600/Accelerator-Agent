"""Create a first spatial pipeline plan from selected templates."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from accagent.framework.sacg_store import SACGStore
from accagent.framework.sacg_utils import (
    add_constraint,
    add_edge,
    add_invariant,
    add_node,
    artifact_path,
    constraint_facts,
    copy_state,
    read_json,
    run_dir_from_state,
    safe_id,
    stage_status_allows_promotion,
    write_json,
)
from accagent.framework.stage_entry import run_sacg_stage
from accagent.framework.stage_llm import ACTION_GROUNDING_REGISTRY, run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary


class PipelinePlanningError(ValueError):
    pass


TOUCHED_CONSTRAINTS = [
    "constraint.model.decoder",
    "constraint.shape.model",
    "constraint.template.library",
    "constraint.arch.design_space",
    "constraint.memory.board",
    "constraint.runtime.board",
    "constraint.cross_layer.input_consistency",
]


def stage_kind(op: str, template_id: str) -> str:
    if template_id == "attention":
        return "attention"
    if template_id == "ffn":
        return "mlp"
    if template_id == "residual":
        return "residual"
    if template_id == "norm":
        return "norm"
    if template_id == "activation" or template_id == "elementwise" or op == "activation_mul":
        return "activation"
    return op


def bound_value(binding: dict[str, Any], name: str, default: Any = None) -> Any:
    params = binding.get("bound_params", {}) if isinstance(binding.get("bound_params"), dict) else {}
    record = params.get(name)
    if isinstance(record, dict) and record.get("status") == "bound":
        return record.get("value")
    if isinstance(record, dict) and record.get("status") == "candidate_bound":
        return record.get("planning_value", default)
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
        "I8": 8,
        "U8": 8,
    }
    return mapping.get(text, default)


def numeric_bit_policy(state: dict[str, Any]) -> dict[str, Any]:
    numeric = constraint_facts(state, "constraint.numeric.policy")
    rules = numeric.get("default_rules", {}) if isinstance(numeric.get("default_rules"), dict) else {}
    activation_bits = dtype_bits(rules.get("activation_dtype") or numeric.get("activation_dtype"), 16)
    acc_bits = dtype_bits(rules.get("acc_dtype") or numeric.get("acc_dtype"), 32)
    weight_bits = dtype_bits(rules.get("weight_dtype") or numeric.get("weight_dtype"), activation_bits)
    return {
        "policy_id": numeric.get("policy_id"),
        "activation_bits": activation_bits,
        "accumulator_bits": acc_bits,
        "weight_bits": weight_bits,
        "scale_bits": dtype_bits(rules.get("scale_dtype") or numeric.get("scale_dtype"), activation_bits),
        "rounding": rules.get("rounding"),
        "saturation": rules.get("saturation"),
        "source": "constraint.numeric.policy.default_rules",
    }


def bytes_for_elements(elements: int, bits: int) -> int:
    return (max(0, elements) * max(1, bits) + 7) // 8


def align_up(value: int, alignment: int) -> int:
    if alignment <= 1:
        return value
    return ((value + alignment - 1) // alignment) * alignment


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


def selected_fifo_depth(design_space: dict[str, Any], default: int = 32) -> int:
    search = design_space.get("search_params", {}) if isinstance(design_space.get("search_params"), dict) else {}
    fifo_depth = search.get("fifo_depth")
    if isinstance(fifo_depth, list) and fifo_depth:
        return scalar(fifo_depth[0], default)
    fifo_depths = search.get("fifo_depths", {}) if isinstance(search.get("fifo_depths"), dict) else {}
    module_fifo = fifo_depths.get("module_stream_fifo_depth_entries")
    return fixed_or_first(module_fifo, default)


def bindings_by_op(selection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in selection.get("parameter_bindings", []):
        if isinstance(item, dict) and item.get("op"):
            result[str(item["op"])] = item
    return result


SEMANTIC_BOUNDARIES = {"block_input", "block_output"}
NUMERIC_STREAM_ROLES = {"activation", "accumulator"}
TENSOR_WIDTH_ROLES = {"hidden": "hidden_size", "intermediate": "intermediate_size"}
SCALA_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
IMPLEMENTATION_PARAM_SOURCES = {
    "hidden_size",
    "intermediate_size",
    "num_q_heads",
    "num_kv_heads",
    "head_dim",
    "lanes",
    "compute_array_rows",
    "compute_array_cols",
    "batch_size",
    "token_count",
    "max_seq_len",
    "input_bits",
    "elem_bits",
    "output_bits",
}


def validate_implementation_contract(contract: Any, adapter_path: Path | str) -> dict[str, Any]:
    """Validate the model-owned binding from semantic plan to trusted Chisel."""

    prefix = f"{adapter_path}: implementation_contract"
    if not isinstance(contract, dict):
        raise PipelinePlanningError(f"{prefix} must be an object")

    top_class = str(contract.get("top_class") or "")
    if not SCALA_IDENTIFIER.fullmatch(top_class):
        raise PipelinePlanningError(f"{prefix}.top_class must be a Scala identifier")
    if not isinstance(contract.get("requires_position_input"), bool):
        raise PipelinePlanningError(f"{prefix}.requires_position_input must be boolean")

    def port_names(field: str) -> list[str]:
        values = contract.get(field)
        if not isinstance(values, list):
            raise PipelinePlanningError(f"{prefix}.{field} must be a list")
        names = [str(value or "") for value in values]
        invalid = [name for name in names if not SCALA_IDENTIFIER.fullmatch(name)]
        if invalid:
            raise PipelinePlanningError(f"{prefix}.{field} has invalid port name(s): {invalid}")
        if len(set(names)) != len(names):
            raise PipelinePlanningError(f"{prefix}.{field} must not repeat ports")
        return names

    loader_ports = port_names("loader_ports")
    disabled_weight_ports = port_names("disabled_weight_ports")
    overlap = sorted(set(loader_ports) & set(disabled_weight_ports))
    if overlap:
        raise PipelinePlanningError(f"{prefix} ports cannot be both connected and disabled: {overlap}")

    params = contract.get("params")
    if not isinstance(params, dict):
        raise PipelinePlanningError(f"{prefix}.params must be an object")
    param_class = str(params.get("class") or "")
    if not SCALA_IDENTIFIER.fullmatch(param_class):
        raise PipelinePlanningError(f"{prefix}.params.class must be a Scala identifier")
    bindings = params.get("bindings")
    if not isinstance(bindings, dict) or not bindings:
        raise PipelinePlanningError(f"{prefix}.params.bindings must be a non-empty object")
    normalized_bindings: dict[str, str] = {}
    for parameter, source in bindings.items():
        parameter_name = str(parameter or "")
        source_name = str(source or "")
        if not SCALA_IDENTIFIER.fullmatch(parameter_name):
            raise PipelinePlanningError(f"{prefix}.params.bindings has invalid parameter name {parameter!r}")
        if source_name not in IMPLEMENTATION_PARAM_SOURCES:
            raise PipelinePlanningError(
                f"{prefix}.params.bindings.{parameter_name} uses unsupported source {source_name!r}"
            )
        normalized_bindings[parameter_name] = source_name

    return {
        "top_class": top_class,
        "requires_position_input": contract["requires_position_input"],
        "loader_ports": loader_ports,
        "disabled_weight_ports": disabled_weight_ports,
        "params": {"class": param_class, "bindings": normalized_bindings},
    }


def pipeline_dataflow_for_state(state: dict[str, Any]) -> dict[str, Any]:
    """Load the model-owned pipeline contract without inferring topology.

    The model semantic adapter is the only authority for Stage 3 graph shape.
    A missing or malformed declaration is a configuration error, rather than an
    opportunity to silently substitute a Qwen/LLaMA-style dataflow.
    """

    try:
        case_adapter = read_json(artifact_path(state, "artifact.input.case_adapter"))
    except Exception as exc:
        raise PipelinePlanningError(f"cannot load current case adapter: {exc}") from exc
    semantic = case_adapter.get("model_semantic_adapter")
    if not isinstance(semantic, dict) or not semantic.get("path"):
        raise PipelinePlanningError("case adapter is missing model_semantic_adapter.path")
    adapter_path = Path(str(semantic["path"]))
    if not adapter_path.is_file():
        adapter_path = Path.cwd() / adapter_path
    if not adapter_path.is_file():
        raise PipelinePlanningError(f"model semantic adapter is missing: {adapter_path}")
    try:
        adapter = read_json(adapter_path)
    except Exception as exc:
        raise PipelinePlanningError(f"cannot read model semantic adapter {adapter_path}: {exc}") from exc
    dataflow = adapter.get("pipeline_dataflow")
    if not isinstance(dataflow, dict):
        raise PipelinePlanningError(f"{adapter_path}: missing pipeline_dataflow contract")
    stage_metadata = dataflow.get("stage_metadata")
    edges = dataflow.get("edges")
    boundary_numeric = dataflow.get("boundary_numeric")
    storage_terms = dataflow.get("weight_storage_terms")
    if not isinstance(stage_metadata, dict) or not stage_metadata:
        raise PipelinePlanningError(f"{adapter_path}: pipeline_dataflow.stage_metadata must be a non-empty object")
    if not isinstance(edges, list) or not edges:
        raise PipelinePlanningError(f"{adapter_path}: pipeline_dataflow.edges must be a non-empty list")
    if not isinstance(boundary_numeric, dict):
        raise PipelinePlanningError(f"{adapter_path}: pipeline_dataflow.boundary_numeric must be an object")
    if not isinstance(storage_terms, list) or not storage_terms:
        raise PipelinePlanningError(f"{adapter_path}: pipeline_dataflow.weight_storage_terms must be a non-empty list")

    model = constraint_facts(state, "constraint.model.decoder")
    declared_ops = [str(op) for op in model.get("operator_sequence", [])]
    duplicate_ops = sorted({op for op in declared_ops if declared_ops.count(op) > 1})
    if duplicate_ops:
        raise PipelinePlanningError(
            "Stage 3 requires unique semantic operator identifiers; duplicate operator names need explicit instance ids: "
            f"{duplicate_ops}"
        )
    missing_metadata = [op for op in declared_ops if not isinstance(stage_metadata.get(op), dict)]
    extra_metadata = sorted(set(stage_metadata) - set(declared_ops))
    if missing_metadata or extra_metadata:
        raise PipelinePlanningError(
            f"{adapter_path}: pipeline_dataflow stage metadata mismatch: missing={missing_metadata}, extra={extra_metadata}"
        )
    for op in declared_ops:
        metadata = stage_metadata[op]
        shape_spec = metadata.get("shape")
        numeric_spec = metadata.get("numeric")
        if not isinstance(shape_spec, dict) or set(shape_spec) != {"input", "output"}:
            raise PipelinePlanningError(f"{adapter_path}: {op} requires shape.input and shape.output roles")
        if any(shape_spec.get(key) not in TENSOR_WIDTH_ROLES for key in ("input", "output")):
            raise PipelinePlanningError(f"{adapter_path}: {op} uses an unsupported tensor-width role: {shape_spec}")
        if not isinstance(numeric_spec, dict) or set(numeric_spec) != {"input", "internal", "output"}:
            raise PipelinePlanningError(f"{adapter_path}: {op} requires numeric input/internal/output roles")
        if any(numeric_spec.get(key) not in NUMERIC_STREAM_ROLES for key in ("input", "internal", "output")):
            raise PipelinePlanningError(f"{adapter_path}: {op} uses an unsupported numeric role: {numeric_spec}")
        if not metadata.get("latency_kind"):
            raise PipelinePlanningError(f"{adapter_path}: {op} is missing latency_kind")
    seen_storage_terms: set[str] = set()
    for term in storage_terms:
        if not isinstance(term, dict):
            raise PipelinePlanningError(f"{adapter_path}: every weight_storage_terms entry must be an object")
        term_id = str(term.get("id") or "")
        owner = str(term.get("stage") or "")
        physical_role = str(term.get("physical_role") or "")
        if not term_id or term_id in seen_storage_terms:
            raise PipelinePlanningError(f"{adapter_path}: weight storage term ids must be unique and non-empty")
        if owner not in declared_ops:
            raise PipelinePlanningError(
                f"{adapter_path}: weight storage term {term_id!r} has unknown stage owner {owner!r}"
            )
        if physical_role != "weight" and not physical_role.startswith("weight_"):
            raise PipelinePlanningError(
                f"{adapter_path}: weight storage term {term_id!r} has invalid physical_role {physical_role!r}"
            )
        seen_storage_terms.add(term_id)
    if any(boundary_numeric.get(key) not in NUMERIC_STREAM_ROLES for key in ("input", "output")):
        raise PipelinePlanningError(f"{adapter_path}: boundary_numeric must use activation or accumulator roles")

    known_nodes = set(declared_ops) | SEMANTIC_BOUNDARIES
    seen_edges: set[tuple[str, str, str, str, str]] = set()
    connected_ops: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise PipelinePlanningError(f"{adapter_path}: every pipeline edge must be an object")
        src = str(edge.get("source") or "")
        dst = str(edge.get("destination") or "")
        if src not in known_nodes or dst not in known_nodes:
            raise PipelinePlanningError(f"{adapter_path}: edge has unknown endpoint {src!r}->{dst!r}")
        if src == "block_output" or dst == "block_input":
            raise PipelinePlanningError(f"{adapter_path}: invalid boundary direction {src!r}->{dst!r}")
        key = (src, dst, str(edge.get("kind") or "main"), str(edge.get("source_port") or "out"), str(edge.get("destination_port") or "in"))
        if key in seen_edges:
            raise PipelinePlanningError(f"{adapter_path}: duplicate pipeline edge {key}")
        seen_edges.add(key)
        connected_ops.update({src, dst} & set(declared_ops))
    missing_connected = sorted(set(declared_ops) - connected_ops)
    if missing_connected:
        raise PipelinePlanningError(f"{adapter_path}: declared operators are disconnected from pipeline_dataflow: {missing_connected}")
    return {
        "adapter_path": str(adapter_path),
        "schema_version": dataflow.get("schema_version"),
        "boundary_numeric": boundary_numeric,
        "stage_metadata": stage_metadata,
        "edges": edges,
        "weight_storage_terms": storage_terms,
        "implementation_contract": validate_implementation_contract(
            adapter.get("implementation_contract"), adapter_path
        ),
    }


def shape_for_role(role: str, shape: dict[str, Any]) -> dict[str, Any]:
    key = TENSOR_WIDTH_ROLES.get(role)
    if key is None:
        raise PipelinePlanningError(f"unsupported tensor-width role: {role}")
    return {"seq_len": shape.get("target_max_seq_len"), "width": shape.get(key)}


def stage_shapes(metadata: dict[str, Any], shape: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    shape_spec = metadata.get("shape", {}) if isinstance(metadata.get("shape"), dict) else {}
    return shape_for_role(str(shape_spec.get("input")), shape), shape_for_role(str(shape_spec.get("output")), shape)


def symbolic_latency(metadata: dict[str, Any], shape: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    seq_len = int(shape.get("target_max_seq_len") or 1)
    hidden = int(shape.get("hidden_size") or 1)
    intermediate = int(shape.get("intermediate_size") or hidden)
    lanes = int(bound_value(binding, "lanes", 1) or 1)
    head_dim = int(shape.get("head_dim") or 1)
    q_heads = int(shape.get("num_q_heads") or 1)
    latency_kind = str(metadata.get("latency_kind"))
    if latency_kind == "self_attention":
        stream_width = hidden
        cycles = (seq_len * hidden + seq_len * seq_len * q_heads * head_dim) // max(lanes, 1)
    elif latency_kind == "linear_hidden_to_intermediate":
        stream_width = intermediate
        cycles = seq_len * hidden * intermediate // max(lanes, 1)
    elif latency_kind == "linear_intermediate_to_hidden":
        stream_width = hidden
        cycles = seq_len * intermediate * hidden // max(lanes, 1)
    elif latency_kind == "pointwise_intermediate":
        stream_width = intermediate
        cycles = seq_len * intermediate // max(lanes, 1)
    elif latency_kind == "pointwise_hidden":
        stream_width = hidden
        cycles = seq_len * hidden // max(lanes, 1)
    else:
        raise PipelinePlanningError(f"unsupported semantic latency_kind: {latency_kind}")
    return {
        "estimate_kind": "symbolic_first_order",
        "used_for": "planning estimate only; not timing, throughput, or hardware pass evidence",
        "cycles": max(1, cycles),
        "formula_inputs": {
            "seq_len": seq_len,
            "hidden_size": hidden,
            "intermediate_size": intermediate,
            "stream_width": stream_width,
            "lanes": lanes,
            "latency_kind": latency_kind,
        },
    }


def make_edge(
    src: str,
    dst: str,
    *,
    kind: str = "main",
    src_port: str = "out",
    dst_port: str = "in",
    order: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "edge_id": f"edge.data.{safe_id(src)}.to.{safe_id(dst)}.{safe_id(kind)}",
        "src_stage": src,
        "dst_stage": dst,
        "src_port": src_port,
        "dst_port": dst_port,
        "kind": kind,
        "transfer_order": order or ["token", "tile", "lane", "word"],
        "flow_control": "ready_valid",
        "backpressure": "dst_ready_propagates_to_src",
    }


def stage_id_by_op(stages: list[dict[str, Any]]) -> dict[str, str]:
    return {stage["op"]: stage["stage_id"] for stage in stages}


def build_data_edges(stages: list[dict[str, Any]], declared_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_op = stage_id_by_op(stages)
    def endpoint(name: str) -> str:
        if name in SEMANTIC_BOUNDARIES:
            return name
        if name not in by_op:
            raise PipelinePlanningError(f"pipeline_dataflow references unselected operator: {name}")
        return by_op[name]

    edges: list[dict[str, Any]] = []
    for declared in declared_edges:
        edges.append(
            make_edge(
                endpoint(str(declared.get("source"))),
                endpoint(str(declared.get("destination"))),
                kind=str(declared.get("kind") or "main"),
                src_port=str(declared.get("source_port") or "out"),
                dst_port=str(declared.get("destination_port") or "in"),
                order=declared.get("transfer_order") if isinstance(declared.get("transfer_order"), list) else None,
            )
        )
    return edges


def build_buffer_plan(edges: list[dict[str, Any]], design_space: dict[str, Any]) -> list[dict[str, Any]]:
    default_depth = selected_fifo_depth(design_space, 32)
    fanout = {str(edge.get("src_stage")): 0 for edge in edges}
    fanin = {str(edge.get("dst_stage")): 0 for edge in edges}
    for edge in edges:
        fanout[str(edge.get("src_stage"))] += 1
        fanin[str(edge.get("dst_stage"))] += 1
    buffers = []
    for edge in edges:
        src = str(edge.get("src_stage"))
        dst = str(edge.get("dst_stage"))
        is_branch_edge = fanout[src] > 1 or fanin[dst] > 1
        depth = max(default_depth, 64) if is_branch_edge else default_depth
        buffers.append(
            {
                "edge_id": edge["edge_id"],
                "buffer_id": f"buffer.{safe_id(edge['edge_id'])}",
                "kind": "bounded_ready_valid_fifo",
                "implementation": "trusted_queue_template",
                "resource_class": "on_chip_fifo",
                "depth": depth,
                "purpose": "preserve branch token order under backpressure" if is_branch_edge else "decouple adjacent pipeline stages",
                "correctness_note": "depth is a bounded elasticity/resource choice; correctness relies on ready/valid backpressure, not on latency equalization",
            }
        )
    return buffers


def board_axi_contract(state: dict[str, Any]) -> dict[str, Any]:
    memory = constraint_facts(state, "constraint.memory.board")
    design_space = constraint_facts(state, "constraint.arch.design_space")
    search = design_space.get("search_params", {}) if isinstance(design_space.get("search_params"), dict) else {}
    ddr_axi = search.get("ddr_axi", {}) if isinstance(search.get("ddr_axi"), dict) else {}
    memory_system = memory.get("memory_system", {}) if isinstance(memory.get("memory_system"), dict) else memory
    data_width_bits = scalar(memory_system.get("axi_data_width_bits"), fixed_or_first(ddr_axi.get("data_width_bits"), 512))
    data_bytes = scalar(memory_system.get("axi_data_bytes"), max(1, data_width_bits // 8))
    return {
        "protocol": memory_system.get("axi_protocol", "AXI"),
        "core_side_interface_name": memory_system.get("core_side_interface_name"),
        "data_width_bits": data_width_bits,
        "data_bytes": data_bytes,
        "alignment_bytes": fixed_or_first(ddr_axi.get("alignment_bytes"), data_bytes),
        "addr_width_bits": scalar(memory_system.get("axi_addr_width_bits"), fixed_or_first(ddr_axi.get("addr_width_bits"), 37)),
        "id_width_bits": scalar(memory_system.get("axi_id_width_bits"), fixed_or_first(ddr_axi.get("id_width_bits"), 4)),
        "wstrb_width_bits": scalar(memory_system.get("axi_wstrb_width_bits"), fixed_or_first(ddr_axi.get("wstrb_width_bits"), data_bytes)),
        "ddr_channels": scalar(memory_system.get("ddr_channels"), 1),
        "ddr_type": memory_system.get("ddr_type"),
        "calibration_done_signal": memory_system.get("calibration_done_signal"),
        "source": "constraint.memory.board.memory_system",
    }


def numeric_bits_for_role(role: str, policy: dict[str, Any]) -> int:
    if role == "activation":
        return scalar(policy.get("activation_bits"), 16)
    if role == "accumulator":
        return scalar(policy.get("accumulator_bits"), 32)
    raise PipelinePlanningError(f"unsupported numeric stream role: {role}")


def stage_numeric_contract(metadata: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    elem_bits = scalar(policy.get("activation_bits"), 16)
    acc_bits = scalar(policy.get("accumulator_bits"), 32)
    weight_bits = scalar(policy.get("weight_bits"), elem_bits)
    numeric = metadata.get("numeric", {}) if isinstance(metadata.get("numeric"), dict) else {}
    input_bits = numeric_bits_for_role(str(numeric.get("input")), policy)
    internal_bits = numeric_bits_for_role(str(numeric.get("internal")), policy)
    output_bits = numeric_bits_for_role(str(numeric.get("output")), policy)
    return {
        "input_bits": input_bits,
        "internal_elem_bits": internal_bits,
        "output_bits": output_bits,
        "accumulator_bits": acc_bits,
        "weight_bits": weight_bits,
        "numeric_policy_id": policy.get("policy_id"),
        "source": policy.get("source"),
    }


def stage_contracts(
    stages: list[dict[str, Any]], state: dict[str, Any], boundary_numeric: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    policy = numeric_bit_policy(state)
    contracts: dict[str, dict[str, Any]] = {
        "block_input": {
            "output_bits": numeric_bits_for_role(str(boundary_numeric.get("input")), policy),
            "output_shape": stages[0]["input_shape"] if stages else {},
            "role": "pipeline_boundary_input",
        },
        "block_output": {
            "input_bits": numeric_bits_for_role(str(boundary_numeric.get("output")), policy),
            "input_shape": stages[-1]["output_shape"] if stages else {},
            "role": "pipeline_boundary_output",
        },
    }
    for stage in stages:
        numeric_contract = stage_numeric_contract(stage.get("semantic_metadata", {}), policy)
        stage["numeric_contract"] = numeric_contract
        numeric_contract["lanes"] = bound_value(stage, "lanes", None)
        contracts[stage["stage_id"]] = {
            "input_bits": numeric_contract["input_bits"],
            "output_bits": numeric_contract["output_bits"],
            "input_shape": stage.get("input_shape", {}),
            "output_shape": stage.get("output_shape", {}),
            "role": "pipeline_stage",
            "lanes": numeric_contract.get("lanes"),
        }
    return contracts


def tensor_elements(shape: dict[str, Any]) -> int:
    return scalar(shape.get("seq_len"), 1) * scalar(shape.get("width"), 1)


def enrich_edges_with_contracts(
    edges: list[dict[str, Any]],
    contracts: dict[str, dict[str, Any]],
    shape: dict[str, Any],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    axi = board_axi_contract(state)
    lanes = 1
    for contract in contracts.values():
        if contract.get("role") == "pipeline_stage":
            lanes = scalar(contract.get("lanes"), lanes)
    enriched = []
    for edge in edges:
        src = contracts.get(str(edge.get("src_stage")), {})
        dst = contracts.get(str(edge.get("dst_stage")), {})
        tensor = src.get("output_shape") or dst.get("input_shape") or {
            "seq_len": shape.get("target_max_seq_len"),
            "width": shape.get("hidden_size"),
        }
        bits = scalar(src.get("output_bits"), scalar(dst.get("input_bits"), 16))
        elements = tensor_elements(tensor)
        byte_count = bytes_for_elements(elements, bits)
        axi_bytes = scalar(axi.get("data_bytes"), 64)
        stream_beat_bits = max(1, lanes * bits)
        edge_contract = {
            "tensor": tensor,
            "element_bits": bits,
            "src_output_bits": src.get("output_bits"),
            "dst_input_bits": dst.get("input_bits"),
            "transfer_count_elements": elements,
            "transfer_count_bytes": byte_count,
            "transfer_count_aligned_bytes": align_up(byte_count, axi_bytes),
            "axi_beats": align_up(byte_count, axi_bytes) // max(1, axi_bytes),
            "axi_data_width_bits": axi.get("data_width_bits"),
            "axi_alignment_bytes": axi.get("alignment_bytes"),
            "stream_beat_bits": stream_beat_bits,
            "stream_beats_per_axi_beat": scalar(axi.get("data_width_bits"), stream_beat_bits) // stream_beat_bits
            if stream_beat_bits and scalar(axi.get("data_width_bits"), 0) % stream_beat_bits == 0
            else None,
            "valid_byte_policy": "full_beats_only" if byte_count % max(1, axi_bytes) == 0 else "tail_beat_with_valid_bytes",
            "stream_order": edge.get("transfer_order", []),
            "producer_consumer_pairing": "same token/tile/lane/word order; consumers must not reinterpret layout",
        }
        enriched.append(edge | {"stream_contract": edge_contract})
    return enriched


def branch_join_contracts(edges: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive stream fanout/fanin obligations from the declared semantic DAG."""

    by_source: dict[str, list[dict[str, Any]]] = {}
    by_destination: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        by_source.setdefault(str(edge.get("src_stage")), []).append(edge)
        by_destination.setdefault(str(edge.get("dst_stage")), []).append(edge)
    split_contracts = [
        {
            "node": source,
            "output_edges": [str(edge["edge_id"]) for edge in source_edges],
            "duplicator": "ready_valid_broadcast_with_per_output_fifo",
            "source_accept_rule": "source beat is accepted only when all branch FIFOs can enqueue the same token/tile/lane/word",
            "branch_dequeue_rule": "after duplication each branch observes its own downstream ready",
        }
        for source, source_edges in by_source.items()
        if len(source_edges) > 1
    ]
    join_contracts = [
        {
            "node": destination,
            "input_edges": [str(edge["edge_id"]) for edge in destination_edges],
            "fire_rule": "all required inputs valid before fire",
            "pairing_key": ["token", "tile", "lane", "word"],
        }
        for destination, destination_edges in by_destination.items()
        if len(destination_edges) > 1
    ]
    return {"split_contracts": split_contracts, "join_contracts": join_contracts}


def attention_contract(state: dict[str, Any]) -> dict[str, Any]:
    model = constraint_facts(state, "constraint.model.decoder")
    shape = constraint_facts(state, "constraint.shape.model")
    q_heads = scalar(shape.get("num_q_heads"), scalar(model.get("num_q_heads"), 1))
    kv_heads = scalar(shape.get("num_kv_heads"), scalar(model.get("num_kv_heads"), q_heads))
    return {
        "attention_kind": model.get("attention_kind"),
        "num_q_heads": q_heads,
        "num_kv_heads": kv_heads,
        "head_dim": scalar(shape.get("head_dim"), scalar(model.get("head_dim"), 1)),
        "gqa_group_size": q_heads // max(1, kv_heads) if kv_heads else None,
        "seq_len_bound": shape.get("target_max_seq_len"),
        "causal": True,
        "position_encoding": model.get("position_encoding", {}),
        "stage_boundary": "logical self_attention stage covers model-declared QKV projection, positional encoding, causal attention, and output projection",
        "kv_storage_policy": "bounded by target_max_seq_len inside the generated block; external KV-cache materialization requires a later memory-layout artifact",
    }


def runtime_xdma_id(runtime: dict[str, Any]) -> int | None:
    for key in ["xdma_id_default", "device_id_default", "xdma_id"]:
        value = runtime.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def derived_xdma_device_templates(runtime: dict[str, Any]) -> dict[str, Any]:
    control_protocol = runtime.get("control_protocol")
    xdma_id = runtime_xdma_id(runtime)
    h2c = runtime.get("h2c_device_template")
    c2h = runtime.get("c2h_device_template")
    source = "constraint.runtime.board"
    if control_protocol == "xdma_raw_register_and_ddr" and xdma_id is not None:
        h2c = h2c or f"/dev/xdma{xdma_id}_h2c_0"
        c2h = c2h or f"/dev/xdma{xdma_id}_c2h_0"
        source = "constraint.runtime.board.control_protocol + constraint.runtime.board.xdma_id_default"
    return {
        "h2c_device_template": h2c,
        "c2h_device_template": c2h,
        "xdma_id_default": xdma_id,
        "device_template_source": source,
    }


def default_runtime_targets(runtime: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    h2c_existing = runtime.get("h2c_write_targets")
    c2h_existing = runtime.get("c2h_read_targets")
    h2c_targets = h2c_existing if isinstance(h2c_existing, list) and h2c_existing else []
    c2h_targets = c2h_existing if isinstance(c2h_existing, list) and c2h_existing else []
    if not h2c_targets:
        ctrl_base = runtime.get("ctrl_base") or runtime.get("control_base_address")
        ddr_base = runtime.get("ddr_base") or runtime.get("ddr_base_address")
        if ctrl_base:
            h2c_targets.append({"name": "control_registers", "base": ctrl_base, "role": "start/config writes"})
        if ddr_base:
            h2c_targets.append({"name": "ddr_input_and_weights", "base": ddr_base, "role": "input activations and weight image writes"})
    if not c2h_targets:
        ctrl_base = runtime.get("ctrl_base") or runtime.get("control_base_address")
        output_abs = runtime.get("output_abs") or runtime.get("output_address_abs")
        if ctrl_base:
            c2h_targets.append({"name": "status_registers", "base": ctrl_base, "role": "status polling"})
        if output_abs:
            c2h_targets.append({"name": "output_tokens", "base": output_abs, "role": "output data reads"})
    return h2c_targets, c2h_targets


def storage_term_elements(term: dict[str, Any], shape: dict[str, Any]) -> int:
    factors = term.get("factors")
    if not isinstance(factors, list) or not factors:
        raise PipelinePlanningError(f"weight storage term {term.get('id')!r} must declare non-empty factors")
    product = 1
    for factor in factors:
        if isinstance(factor, bool):
            raise PipelinePlanningError(f"weight storage term {term.get('id')!r} has invalid boolean factor")
        if isinstance(factor, int):
            value = factor
        elif isinstance(factor, str):
            value = shape.get(factor)
        else:
            value = None
        if not isinstance(value, int) or value <= 0:
            raise PipelinePlanningError(
                f"weight storage term {term.get('id')!r} has unresolved positive factor {factor!r}"
            )
        product *= value
    return product


def weight_storage_layout(
    storage_terms: list[dict[str, Any]], shape: dict[str, Any], numeric: dict[str, Any]
) -> list[dict[str, Any]]:
    bit_roles = {
        "weight": scalar(numeric.get("weight_bits"), 16),
        "activation": scalar(numeric.get("activation_bits"), 16),
        "accumulator": scalar(numeric.get("accumulator_bits"), 32),
    }
    layout: list[dict[str, Any]] = []
    seen: set[str] = set()
    for term in storage_terms:
        if not isinstance(term, dict):
            raise PipelinePlanningError("weight_storage_terms entries must be objects")
        term_id = str(term.get("id") or "")
        dtype_role = str(term.get("dtype_role") or "")
        if not term_id or term_id in seen:
            raise PipelinePlanningError(f"weight storage term ids must be unique and non-empty: {term_id!r}")
        if dtype_role not in bit_roles:
            raise PipelinePlanningError(f"weight storage term {term_id!r} has unsupported dtype_role={dtype_role!r}")
        seen.add(term_id)
        elements = storage_term_elements(term, shape)
        element_bits = bit_roles[dtype_role]
        layout.append(
            {
                "id": term_id,
                "stage": term.get("stage"),
                "physical_role": term.get("physical_role"),
                "dtype_role": dtype_role,
                "factors": term["factors"],
                "elements": elements,
                "element_bits": element_bits,
                "bytes": bytes_for_elements(elements, element_bits),
            }
        )
    return layout


def build_memory_schedule(
    state: dict[str, Any],
    model: dict[str, Any],
    shape: dict[str, Any],
    stages: list[dict[str, Any]],
    semantic_dataflow: dict[str, Any],
) -> dict[str, Any]:
    memory = constraint_facts(state, "constraint.memory.board")
    runtime = constraint_facts(state, "constraint.runtime.board")
    numeric = numeric_bit_policy(state)
    axi = board_axi_contract(state)
    num_layers = model.get("num_layers")
    seq_len = scalar(shape.get("target_max_seq_len"), 1)
    hidden = scalar(shape.get("hidden_size"), 1)
    alignment = scalar(axi.get("alignment_bytes"), scalar(axi.get("data_bytes"), 64))
    numeric = numeric_bit_policy(state)
    weights = weight_storage_layout(semantic_dataflow["weight_storage_terms"], shape, numeric)
    per_layer_weight_bytes = sum(scalar(term.get("bytes"), 0) for term in weights)
    input_stage = stages[0] if stages else {}
    output_stage = stages[-1] if stages else {}
    input_shape = input_stage.get("input_shape", {}) if isinstance(input_stage.get("input_shape"), dict) else {}
    output_shape = output_stage.get("output_shape", {}) if isinstance(output_stage.get("output_shape"), dict) else {}
    input_bits = scalar((input_stage.get("numeric_contract") or {}).get("input_bits"), 32)
    output_bits = scalar((output_stage.get("numeric_contract") or {}).get("output_bits"), 32)
    input_elements = tensor_elements(input_shape) if input_shape else seq_len * hidden
    output_elements = tensor_elements(output_shape) if output_shape else seq_len * hidden
    activation_buffer_bytes = max(
        [
            bytes_for_elements(tensor_elements(tensor), bits)
            for stage in stages
            for tensor, bits in (
                (stage.get("input_shape", {}), scalar((stage.get("numeric_contract") or {}).get("input_bits"), input_bits)),
                (stage.get("output_shape", {}), scalar((stage.get("numeric_contract") or {}).get("output_bits"), output_bits)),
            )
            if isinstance(tensor, dict)
        ]
        or [max(bytes_for_elements(input_elements, input_bits), bytes_for_elements(output_elements, output_bits))]
    )
    device_templates = derived_xdma_device_templates(runtime)
    h2c_targets, c2h_targets = default_runtime_targets(runtime)
    required_regions = [
        {
            "name": "input_tokens",
            "role": "activation_input",
            "size_bytes_formula": "semantic block-input tensor elements * declared block-input bits / 8",
            "size_bytes": align_up(bytes_for_elements(input_elements, input_bits), alignment),
            "alignment_bytes": alignment,
        },
        {
            "name": "output_tokens",
            "role": "activation_output",
            "size_bytes_formula": "semantic block-output tensor elements * declared block-output bits / 8",
            "size_bytes": align_up(bytes_for_elements(output_elements, output_bits), alignment),
            "alignment_bytes": alignment,
        },
        {
            "name": "activation_ping",
            "role": "activation_buffer",
            "size_bytes_formula": "max(declared semantic stage input/output tensor bytes)",
            "size_bytes": align_up(activation_buffer_bytes, alignment),
            "alignment_bytes": alignment,
        },
        {
            "name": "activation_pong",
            "role": "activation_buffer",
            "size_bytes_formula": "same as activation_ping",
            "size_bytes": align_up(activation_buffer_bytes, alignment),
            "alignment_bytes": alignment,
        },
        {
            "name": "weight_buffer_a",
            "role": "weight_buffer",
            "size_bytes_formula": "sum(model-semantic weight_storage_terms)",
            "size_bytes": align_up(per_layer_weight_bytes, alignment),
            "alignment_bytes": alignment,
        },
        {
            "name": "weight_buffer_b",
            "role": "weight_buffer",
            "size_bytes_formula": "same as weight_buffer_a",
            "size_bytes": align_up(per_layer_weight_bytes, alignment),
            "alignment_bytes": alignment,
        },
    ]
    return {
        "policy": "double_buffered_weights_and_streamed_activations",
        "num_layers": num_layers,
        "target_seq_len": shape.get("target_max_seq_len"),
        "sequence_semantics": {
            "target_seq_len_role": "compile-time maximum and default fixed tile bound for generated artifacts",
            "runtime_cfg_rule": "runtime sequence length must be <= target_max_seq_len; transfer counts derive from the configured sequence length",
        },
        "activation_flow": "input DDR read -> block pipeline -> output DDR write",
        "weight_flow": "while layer N computes, prefetch layer N+1 weights into the inactive weight buffer",
        "weight_buffers": ["weight_buffer_a", "weight_buffer_b"],
        "activation_buffers": ["activation_ping", "activation_pong"],
        "required_regions": required_regions,
        "per_layer_weight_bytes": align_up(per_layer_weight_bytes, alignment),
        "weight_storage_terms": weights,
        "board_axi": axi,
        "board_memory_refs": {
            "memory_system": memory.get("memory_system", {}),
            "runtime_fields": sorted(str(key) for key in runtime.keys()),
        },
        "runtime_config_requirements": {
            "control_protocol": runtime.get("control_protocol"),
            "h2c_device_template": device_templates.get("h2c_device_template"),
            "c2h_device_template": device_templates.get("c2h_device_template"),
            "xdma_id_default": device_templates.get("xdma_id_default"),
            "device_template_source": device_templates.get("device_template_source"),
            "h2c_write_targets": h2c_targets,
            "c2h_read_targets": c2h_targets,
            "command_sequence": [
                "write input and first-layer weights through XDMA H2C into DDR/control regions",
                "write start/control register",
                "prefetch next-layer weights into inactive weight buffer while active layer computes",
                "poll status register through XDMA C2H until done/status changes",
                "read output header/data from output DDR region",
            ],
        },
        "axi_ddr_requirements": [
            "preserve board-provided data width and alignment",
            "all read/write transfer counts must be derived from tensor shape and element width",
            "host/runtime commands must use the board profile from Stage 0",
            "exact base addresses are assigned by Stage 5 memory_layout and must remain aligned to board_axi.alignment_bytes",
        ],
    }


def pass_row(checker: str, summary: str, **extra: Any) -> dict[str, Any]:
    return {"checker": checker, "status": "pass", "summary": summary, "errors": [], "warnings": [], **extra}


def fail_row(checker: str, errors: list[str], warnings: list[str] | None = None, **extra: Any) -> dict[str, Any]:
    return {"checker": checker, "status": "fail", "summary": "; ".join(errors[:3]), "errors": errors, "warnings": warnings or [], **extra}


def is_empty_value(value: Any) -> bool:
    return value is None or value == "" or value == []


def edge_by_id(edges: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(edge.get("edge_id")): edge for edge in edges}


def check_operator_order(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    model = constraint_facts(state, "constraint.model.decoder")
    expected = [str(op) for op in model.get("operator_sequence", [])]
    actual = [str(stage.get("op")) for stage in plan.get("stages", [])]
    if actual != expected:
        return fail_row("operator_order_check", [f"operator order mismatch: expected={expected}, actual={actual}"])
    return pass_row("operator_order_check", f"operator_order={actual}")


def check_stream_data_edge_mirror(plan: dict[str, Any]) -> dict[str, Any]:
    data_ids = [str(edge.get("edge_id")) for edge in plan.get("data_edges", [])]
    stream_ids = [str(edge.get("edge_id")) for edge in plan.get("stream_edges", [])]
    errors = []
    if data_ids != stream_ids:
        errors.append(f"stream_edges must mirror data_edges exactly: data={data_ids}, stream={stream_ids}")
    if len(set(data_ids)) != len(data_ids):
        errors.append("data_edges contain duplicate edge_id")
    if errors:
        return fail_row("stream_data_edge_mirror_check", errors)
    return pass_row("stream_data_edge_mirror_check", f"edges={len(data_ids)}")


def check_semantic_dataflow_contract(plan: dict[str, Any]) -> dict[str, Any]:
    semantic = plan.get("semantic_dataflow", {}) if isinstance(plan.get("semantic_dataflow"), dict) else {}
    declared = semantic.get("declared_edges", []) if isinstance(semantic.get("declared_edges"), list) else []
    stage_by_op = {str(stage.get("op")): str(stage.get("stage_id")) for stage in plan.get("stages", [])}

    def endpoint(name: Any) -> str:
        text = str(name)
        return text if text in SEMANTIC_BOUNDARIES else stage_by_op.get(text, "")

    expected = {
        (
            endpoint(edge.get("source")),
            endpoint(edge.get("destination")),
            str(edge.get("kind") or "main"),
            str(edge.get("source_port") or "out"),
            str(edge.get("destination_port") or "in"),
        )
        for edge in declared
        if isinstance(edge, dict)
    }
    actual = {
        (
            str(edge.get("src_stage")),
            str(edge.get("dst_stage")),
            str(edge.get("kind") or "main"),
            str(edge.get("src_port") or "out"),
            str(edge.get("dst_port") or "in"),
        )
        for edge in plan.get("data_edges", [])
    }
    errors = []
    if not semantic.get("adapter_path"):
        errors.append("semantic_dataflow.adapter_path is missing")
    if not declared:
        errors.append("semantic_dataflow.declared_edges is empty")
    if "" in {value for edge in expected for value in edge[:2]}:
        errors.append("semantic_dataflow references an operator without a generated stage")
    if expected != actual:
        errors.append(f"generated graph diverges from semantic adapter: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    if errors:
        return fail_row("semantic_dataflow_contract_check", errors)
    return pass_row("semantic_dataflow_contract_check", f"adapter_graph_edges={len(actual)}")


def check_edge_contracts(plan: dict[str, Any]) -> dict[str, Any]:
    errors = []
    warnings = []
    for edge in plan.get("stream_edges", []):
        contract = edge.get("stream_contract", {}) if isinstance(edge.get("stream_contract"), dict) else {}
        for key in ["tensor", "element_bits", "transfer_count_elements", "transfer_count_bytes", "axi_beats", "stream_order"]:
            if is_empty_value(contract.get(key)):
                errors.append(f"{edge.get('edge_id')}: missing stream_contract.{key}")
        bits = scalar(contract.get("element_bits"), 0)
        src_bits = contract.get("src_output_bits")
        dst_bits = contract.get("dst_input_bits")
        if src_bits is not None and scalar(src_bits, -1) != bits:
            errors.append(f"{edge.get('edge_id')}: element_bits={bits} does not match src_output_bits={src_bits}")
        if dst_bits is not None and scalar(dst_bits, -1) != bits:
            errors.append(f"{edge.get('edge_id')}: element_bits={bits} does not match dst_input_bits={dst_bits}")
        if contract.get("stream_beats_per_axi_beat") is None:
            errors.append(f"{edge.get('edge_id')}: stream beat width does not divide AXI data width")
        if contract.get("valid_byte_policy") != "full_beats_only":
            warnings.append(f"{edge.get('edge_id')}: uses tail-beat valid-byte policy")
    if errors:
        return fail_row("edge_stream_contract_check", errors, warnings)
    return pass_row("edge_stream_contract_check", f"checked_edges={len(plan.get('stream_edges', []))}", warnings=warnings)


def check_shape_numeric_contracts(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    policy = numeric_bit_policy(state)
    shape = constraint_facts(state, "constraint.shape.model")
    semantic = plan.get("semantic_dataflow", {}) if isinstance(plan.get("semantic_dataflow"), dict) else {}
    metadata_by_op = semantic.get("stage_metadata", {}) if isinstance(semantic.get("stage_metadata"), dict) else {}
    errors = []
    for stage in plan.get("stages", []):
        op = str(stage.get("op"))
        metadata = metadata_by_op.get(op)
        if not isinstance(metadata, dict):
            errors.append(f"missing semantic metadata for {op}")
            continue
        numeric = metadata.get("numeric", {}) if isinstance(metadata.get("numeric"), dict) else {}
        expected_bits = {
            "input_bits": numeric_bits_for_role(str(numeric.get("input")), policy),
            "internal_elem_bits": numeric_bits_for_role(str(numeric.get("internal")), policy),
            "output_bits": numeric_bits_for_role(str(numeric.get("output")), policy),
        }
        contract = stage.get("numeric_contract", {}) if isinstance(stage.get("numeric_contract"), dict) else {}
        for field, expected in expected_bits.items():
            if scalar(contract.get(field), -1) != expected:
                errors.append(f"{stage.get('stage_id')}: {field}={contract.get(field)} expected {expected}")
        expected_input, expected_output = stage_shapes(metadata, shape)
        if stage.get("input_shape") != expected_input:
            errors.append(f"{stage.get('stage_id')}: input_shape={stage.get('input_shape')} expected {expected_input}")
        if stage.get("output_shape") != expected_output:
            errors.append(f"{stage.get('stage_id')}: output_shape={stage.get('output_shape')} expected {expected_output}")
        latency_inputs = (stage.get("latency") or {}).get("formula_inputs", {}) if isinstance(stage.get("latency"), dict) else {}
        if scalar(latency_inputs.get("stream_width"), -1) != scalar(expected_output.get("width"), -2):
            errors.append(
                f"{stage.get('stage_id')}: latency stream_width={latency_inputs.get('stream_width')} expected output width={expected_output.get('width')}"
            )
    if errors:
        return fail_row("shape_numeric_contract_check", errors)
    return pass_row(
        "shape_numeric_contract_check",
        f"stages={len(plan.get('stages', []))}, activation_bits={policy.get('activation_bits')}, accumulator_bits={policy.get('accumulator_bits')}",
    )


def check_branch_join_contracts(plan: dict[str, Any]) -> dict[str, Any]:
    contracts = plan.get("branch_join_contracts", {}) if isinstance(plan.get("branch_join_contracts"), dict) else {}
    errors = []
    split_contracts = contracts.get("split_contracts", [])
    join_contracts = contracts.get("join_contracts", [])
    all_edges = set(edge_by_id(plan.get("stream_edges", [])).keys())
    by_source: dict[str, list[str]] = {}
    by_destination: dict[str, list[str]] = {}
    for edge in plan.get("stream_edges", []):
        by_source.setdefault(str(edge.get("src_stage")), []).append(str(edge.get("edge_id")))
        by_destination.setdefault(str(edge.get("dst_stage")), []).append(str(edge.get("edge_id")))
    expected_splits = {node: edges for node, edges in by_source.items() if len(edges) > 1}
    expected_joins = {node: edges for node, edges in by_destination.items() if len(edges) > 1}
    actual_splits = {str(row.get("node")): list(row.get("output_edges") or []) for row in split_contracts if isinstance(row, dict)}
    actual_joins = {str(row.get("node")): list(row.get("input_edges") or []) for row in join_contracts if isinstance(row, dict)}
    if actual_splits != expected_splits:
        errors.append(f"split contracts do not match semantic graph fanout: expected={expected_splits}, actual={actual_splits}")
    if actual_joins != expected_joins:
        errors.append(f"join contracts do not match semantic graph fanin: expected={expected_joins}, actual={actual_joins}")
    for contract in split_contracts + join_contracts:
        edge_ids = contract.get("output_edges") or contract.get("input_edges") or []
        if not edge_ids:
            errors.append(f"{contract.get('node')}: missing edge list")
        missing = sorted(set(edge_ids) - all_edges)
        if missing:
            errors.append(f"{contract.get('node')}: unknown contract edges {missing}")
        if contract.get("pairing_key") and contract.get("pairing_key") != ["token", "tile", "lane", "word"]:
            errors.append(f"{contract.get('node')}: unexpected pairing_key={contract.get('pairing_key')}")
    if errors:
        return fail_row("branch_join_contract_check", errors)
    return pass_row("branch_join_contract_check", f"splits={len(split_contracts)}, joins={len(join_contracts)}")


def check_buffer_contracts(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    errors = []
    edge_ids = set(edge_by_id(plan.get("stream_edges", [])).keys())
    buffers = plan.get("buffer_plan", [])
    buffer_edges = [str(item.get("edge_id")) for item in buffers]
    allowed_depths = sorted(
        {
            selected_fifo_depth(constraint_facts(state, "constraint.arch.design_space"), 32),
            64,
        }
    )
    if set(buffer_edges) != edge_ids:
        errors.append(f"buffer edges must match stream edges: missing={sorted(edge_ids - set(buffer_edges))}, extra={sorted(set(buffer_edges) - edge_ids)}")
    if len(buffer_edges) != len(set(buffer_edges)):
        errors.append("buffer_plan contains duplicate edge_id")
    for item in buffers:
        if item.get("kind") == "fifo_or_pingpong_buffer":
            errors.append(f"{item.get('buffer_id')}: ambiguous buffer kind")
        if item.get("kind") != "bounded_ready_valid_fifo":
            errors.append(f"{item.get('buffer_id')}: unsupported buffer kind {item.get('kind')}")
        if scalar(item.get("depth"), 0) <= 0:
            errors.append(f"{item.get('buffer_id')}: depth must be positive")
        if scalar(item.get("depth"), 0) not in allowed_depths:
            errors.append(f"{item.get('buffer_id')}: depth={item.get('depth')} outside selected allowed depths {allowed_depths}")
    if errors:
        return fail_row("buffer_contract_check", errors)
    return pass_row("buffer_contract_check", f"buffers={len(buffers)}, allowed_depths={allowed_depths}")


def graph_has_cycle(edges: list[dict[str, Any]]) -> bool:
    graph: dict[str, list[str]] = {}
    for edge in edges:
        src = str(edge.get("src_stage"))
        dst = str(edge.get("dst_stage"))
        graph.setdefault(src, []).append(dst)
        graph.setdefault(dst, [])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for dst in graph.get(node, []):
            if visit(dst):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def check_liveness_contract(plan: dict[str, Any]) -> dict[str, Any]:
    errors = []
    if graph_has_cycle(plan.get("stream_edges", [])):
        errors.append("directed ready/valid dataflow graph has a cycle; cycle-specific bounded-buffer proof is required")
    flow = plan.get("flow_control", {}) if isinstance(plan.get("flow_control"), dict) else {}
    if flow.get("protocol") != "ready_valid":
        errors.append(f"unsupported flow protocol {flow.get('protocol')}")
    buffer_text = str(plan.get("buffer_plan", [])).lower()
    if "align branch latency" in buffer_text or "fifo_or_pingpong_buffer" in buffer_text:
        errors.append("buffer plan must use concrete bounded FIFOs and must not claim correctness from branch latency alignment")
    if errors:
        return fail_row("liveness_backpressure_check", errors)
    return pass_row("liveness_backpressure_check", "directed graph is acyclic; bounded FIFOs provide elasticity and backpressure, not latency-equality proof")


def check_memory_runtime_contract(plan: dict[str, Any]) -> dict[str, Any]:
    schedule = plan.get("memory_schedule", {}) if isinstance(plan.get("memory_schedule"), dict) else {}
    errors = []
    axi = schedule.get("board_axi", {}) if isinstance(schedule.get("board_axi"), dict) else {}
    for key in ["data_width_bits", "data_bytes", "alignment_bytes", "addr_width_bits", "core_side_interface_name"]:
        if is_empty_value(axi.get(key)):
            errors.append(f"memory_schedule.board_axi missing {key}")
    regions = schedule.get("required_regions", [])
    if not isinstance(regions, list) or len(regions) < 6:
        errors.append("memory_schedule.required_regions must include input/output, ping/pong, and double weight buffers")
    alignment = scalar(axi.get("alignment_bytes"), 1)
    for region in regions if isinstance(regions, list) else []:
        size = scalar(region.get("size_bytes"), 0)
        if size <= 0:
            errors.append(f"{region.get('name')}: size_bytes must be positive")
        if alignment > 1 and size % alignment != 0:
            errors.append(f"{region.get('name')}: size_bytes={size} is not aligned to {alignment}")
    runtime = schedule.get("runtime_config_requirements", {}) if isinstance(schedule.get("runtime_config_requirements"), dict) else {}
    for key in ["control_protocol", "h2c_device_template", "c2h_device_template", "command_sequence"]:
        if is_empty_value(runtime.get(key)):
            errors.append(f"runtime_config_requirements missing {key}")
    if errors:
        return fail_row("memory_runtime_contract_check", errors)
    return pass_row("memory_runtime_contract_check", f"regions={len(regions)}, axi_bits={axi.get('data_width_bits')}")


def check_attention_contract(plan: dict[str, Any]) -> dict[str, Any]:
    contract = plan.get("attention_contract", {}) if isinstance(plan.get("attention_contract"), dict) else {}
    errors = []
    attention_kind = str(contract.get("attention_kind") or "")
    if attention_kind not in {"mha", "gqa", "mqa"}:
        errors.append(f"unsupported attention_kind={contract.get('attention_kind')}")
    if scalar(contract.get("num_q_heads"), 0) <= 0 or scalar(contract.get("num_kv_heads"), 0) <= 0:
        errors.append("attention head counts must be positive")
    q_heads = scalar(contract.get("num_q_heads"), 0)
    kv_heads = scalar(contract.get("num_kv_heads"), 0)
    if q_heads % max(1, kv_heads) != 0:
        errors.append("num_q_heads must be divisible by num_kv_heads")
    if attention_kind == "mha" and q_heads != kv_heads:
        errors.append("MHA requires num_q_heads == num_kv_heads")
    if attention_kind == "mqa" and kv_heads != 1:
        errors.append("MQA requires num_kv_heads == 1")
    if attention_kind == "gqa" and kv_heads in {0, 1, q_heads}:
        errors.append("GQA requires 1 < num_kv_heads < num_q_heads")
    if scalar(contract.get("head_dim"), 0) <= 0:
        errors.append("head_dim must be positive")
    if not contract.get("stage_boundary"):
        errors.append("attention stage_boundary must describe QKV/RoPE/attention/out-projection scope")
    if errors:
        return fail_row("attention_semantics_check", errors)
    return pass_row("attention_semantics_check", f"q={contract.get('num_q_heads')}, kv={contract.get('num_kv_heads')}, head_dim={contract.get('head_dim')}")


def check_template_binding_contract(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    template = constraint_facts(state, "constraint.template.library")
    policy = template.get("policy", {}) if isinstance(template.get("policy"), dict) else {}
    allowed_sources = set(str(path) for path in template.get("source_files", []))
    errors = []
    for stage in plan.get("stages", []):
        if stage.get("source") not in allowed_sources:
            errors.append(f"{stage.get('stage_id')}: source {stage.get('source')} not in template library")
        if not stage.get("template_id"):
            errors.append(f"{stage.get('stage_id')}: missing template_id")
    if policy.get("free_form_rtl_generation") is not False:
        errors.append("template policy must forbid free-form RTL generation for Stage 3 planning")
    if errors:
        return fail_row("template_binding_static_check", errors)
    return pass_row("template_binding_static_check", f"stages={len(plan.get('stages', []))}, free_form_rtl_generation=false")


def run_pipeline_static_checks(plan: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    rows = [
        check_operator_order(plan, state),
        check_semantic_dataflow_contract(plan),
        check_stream_data_edge_mirror(plan),
        check_edge_contracts(plan),
        check_shape_numeric_contracts(plan, state),
        check_branch_join_contracts(plan),
        check_buffer_contracts(plan, state),
        check_liveness_contract(plan),
        check_memory_runtime_contract(plan),
        check_attention_contract(plan),
        check_template_binding_contract(plan, state),
    ]
    errors = [
        f"{row['checker']}: {error}"
        for row in rows
        if row.get("status") != "pass"
        for error in row.get("errors", [])
    ]
    warnings = [
        f"{row['checker']}: {warning}"
        for row in rows
        for warning in row.get("warnings", [])
    ]
    return {
        "schema_version": "spatialaccagent.pipeline_static_checks.v0",
        "stage": "pipeline_planning",
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
            "operator order, edge graph, stream order, tensor shape, element width, branch/join, buffer, liveness, attention, template, memory/runtime handoff contracts must be checker-backed",
            "symbolic_first_order latency is only planning metadata and must not be used as throughput, timing, or hardware pass evidence",
            "stream_edges must mirror data_edges including block_input, residual-skip, and block_output boundary edges",
            "buffer implementations must be concrete bounded ready/valid FIFOs; ping-pong buffers are reserved for memory layout artifacts",
        ],
        "later_stage_obligations": [
            "Stage 4 binds final per-template parameters from this contract",
            "Stage 5 assigns concrete memory base addresses and generates/elaborates template-bound Chisel",
            "Stage 6+ supplies real VCS/Verilator/Vivado/board evidence; Stage 3 must not claim hardware pass",
        ],
        "risk_classification_rule": "If checker_results pass, do not list those resolved current-stage items as risks. Put later-stage obligations in proposed_actions unless a current Stage 3 checker failed.",
    }


def build_pipeline_plan(state: dict[str, Any]) -> dict[str, Any]:
    selection = read_json(artifact_path(state, "artifact.stage2.template_selection"))
    model = constraint_facts(state, "constraint.model.decoder")
    shape = constraint_facts(state, "constraint.shape.model")
    design_space = constraint_facts(state, "constraint.arch.design_space")
    selected = [item for item in selection.get("selected_templates", []) if item.get("role") == "operator"]
    if not selected:
        raise PipelinePlanningError("template selection has no operator templates")
    stage2_bindings = bindings_by_op(selection)
    semantic_dataflow = pipeline_dataflow_for_state(state)
    stage_metadata = semantic_dataflow["stage_metadata"]

    stages = []
    for index, item in enumerate(selected):
        op = str(item["op"])
        binding = stage2_bindings.get(op, {})
        metadata = stage_metadata[op]
        input_shape, output_shape = stage_shapes(metadata, shape)
        stages.append(
            {
                "stage_id": f"stage_{index:02d}_{safe_id(op)}",
                "index": index,
                "op": op,
                "template_id": item["template_id"],
                "source": item.get("source"),
                "kind": stage_kind(op, str(item["template_id"])),
                "input_shape": input_shape,
                "output_shape": output_shape,
                "required_params": item.get("required_params", []),
                "bound_params": binding.get("bound_params", {}),
                "constraints_emitted": item.get("constraints_emitted", []),
                "semantic_metadata": metadata,
                "latency": symbolic_latency(metadata, shape, binding),
            }
        )

    contracts = stage_contracts(stages, state, semantic_dataflow["boundary_numeric"])
    data_edges = enrich_edges_with_contracts(
        build_data_edges(stages, semantic_dataflow["edges"]), contracts, shape, state
    )
    buffer_plan = build_buffer_plan(data_edges, design_space)

    plan = {
        "schema_version": "spatialaccagent.pipeline_plan.v0",
        "stage": "pipeline_planning",
        "status": "ready",
        "model_type": model.get("model_type"),
        "pipeline_style": "operator_stream_pipeline",
        "semantic_dataflow": {
            "adapter_path": semantic_dataflow["adapter_path"],
            "schema_version": semantic_dataflow["schema_version"],
            "boundary_numeric": semantic_dataflow["boundary_numeric"],
            "stage_metadata": semantic_dataflow["stage_metadata"],
            "declared_edges": semantic_dataflow["edges"],
        },
        "implementation_contract": semantic_dataflow["implementation_contract"],
        "stages": stages,
        "data_edges": data_edges,
        "stream_edges": [
            edge | {"stream_order": edge.get("transfer_order", [])}
            for edge in data_edges
        ],
        "buffer_plan": buffer_plan,
        "flow_control": {
            "protocol": "ready_valid",
            "join_policy": "all_required_inputs_valid_before_fire",
            "split_policy": "source beat is duplicated into all branch FIFOs atomically; branch dequeue observes downstream ready independently",
            "deadlock_rule": "directed graph must be acyclic, or every cycle must include a bounded buffer and a checker-backed ready path proof",
        },
        "branch_join_contracts": branch_join_contracts(data_edges),
        "attention_contract": attention_contract(state),
        "numeric_stream_policy": numeric_bit_policy(state),
        "multi_layer_execution": {
            "num_layers": model.get("num_layers"),
            "layer_order": "sequential_layers_with_inter_layer_streaming",
            "pipeline_overlap": "next token may enter stage_0 when backpressure allows; do not serialize whole-token full-block execution unless forced by dependencies",
            "weight_prefetch": "double_buffer_next_layer_weights",
        },
        "memory_schedule": build_memory_schedule(state, model, shape, stages, semantic_dataflow),
        "memory_policy": {
            "weight_policy": "template_bound",
            "activation_policy": "stream_between_stages",
            "board_memory_constraints": ["constraint.memory.board", "constraint.runtime.board"],
        },
        "design_space_refs": sorted(design_space.get("search_params", {}).keys()),
        "constraints_touched": TOUCHED_CONSTRAINTS,
        "stage_gate_policy": stage_gate_policy(),
    }
    checks = run_pipeline_static_checks(plan, state)
    plan["checker_results"] = checks["checker_results"]
    plan["checker_summary"] = checks["summary"]
    plan["status"] = "ready" if checks["status"] == "pass" else "incomplete"
    return plan


def stage_worker_errors(output: dict[str, Any]) -> list[str]:
    if not output:
        return []
    errors = []
    status = str(output.get("status") or "").strip().lower()
    if not stage_status_allows_promotion(status):
        errors.append(f"pipeline_architect_agent status is {output.get('status')}")
        risks = output.get("risks", [])
        if isinstance(risks, list) and risks:
            errors.append(f"pipeline_architect_agent reported {len(risks)} unresolved risk(s)")
    return errors


def normalize_action_checkers(checkers: Any) -> tuple[list[str], list[dict[str, str]], list[str]]:
    if not isinstance(checkers, list):
        return [], [], []
    registered = {
        str(item)
        for item in ACTION_GROUNDING_REGISTRY.get("acceptance_checkers", [])
        if isinstance(item, str)
    }
    normalized_checkers: list[str] = []
    registry_rewrites: list[dict[str, str]] = []
    unregistered: list[str] = []
    for checker in checkers:
        text = str(checker)
        replacement = text
        qualified = f"real_tool.{text}"
        if text not in registered and qualified in registered:
            replacement = qualified
            registry_rewrites.append({"from": text, "to": replacement})
        elif text not in registered and not text.startswith("planned_checker."):
            unregistered.append(text)
        if replacement not in normalized_checkers:
            normalized_checkers.append(replacement)
    return normalized_checkers, registry_rewrites, unregistered


def normalize_design_team_actions(summary: dict[str, Any]) -> dict[str, Any]:
    actions = summary.get("executable_actions", [])
    if not isinstance(actions, list):
        return summary
    normalized_actions: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    checker_rewrites: list[dict[str, str]] = []
    unregistered_checkers: list[dict[str, str]] = []
    duplicate_count = 0
    for action in actions:
        if not isinstance(action, dict):
            continue
        normalized = dict(action)
        normalized_checkers, rewrites, unregistered = normalize_action_checkers(normalized.get("acceptance_checkers", []))
        normalized["acceptance_checkers"] = normalized_checkers
        for rewrite in rewrites:
            checker_rewrites.append({"action_id": str(normalized.get("id") or ""), **rewrite})
        for checker in unregistered:
            unregistered_checkers.append({"action_id": str(normalized.get("id") or ""), "checker": checker})
        key = (
            str(normalized.get("id") or ""),
            str(normalized.get("stage") or ""),
            str(normalized.get("action_type") or ""),
        )
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        normalized_actions.append(normalized)
    if checker_rewrites or unregistered_checkers or duplicate_count:
        summary = dict(summary)
        summary["executable_actions"] = normalized_actions
        summary["action_normalization"] = {
            "schema_version": "spatialaccagent.action_normalization.v0",
            "registry_rewrites": checker_rewrites,
            "unregistered_checkers": unregistered_checkers,
            "duplicate_actions_removed": duplicate_count,
            "policy": "Normalize team executable action checker names through the action grounding registry before LLM review and SACG commit; this does not change design semantics.",
        }
    return summary


def update_sacg(
    source_state: Path,
    target_state: Path,
    plan_path: Path,
    check_path: Path,
    plan: dict[str, Any],
    checks: dict[str, Any],
    errors: list[str],
) -> str:
    state = copy_state(source_state, target_state)
    boundary_node_ids = ["node.pipeline.block_input", "node.pipeline.block_output"]
    stage_node_ids = [f"node.pipeline.{stage['stage_id']}" for stage in plan["stages"]]
    pipeline_node_ids = [boundary_node_ids[0], *stage_node_ids, boundary_node_ids[1]]
    edge_ids = [edge["edge_id"] for edge in plan["stream_edges"]]
    constraints = [
        "constraint.pipeline.structure",
        "constraint.stream.order",
        "constraint.beat.pipeline",
        "constraint.buffering.pipeline",
        "constraint.flow_control.pipeline",
        "constraint.memory_schedule.pipeline",
        "constraint.liveness.pipeline",
    ]
    artifact_ids = ["artifact.stage3.pipeline_plan", "artifact.stage3.pipeline_static_checks"]
    add_constraint(
        state,
        "constraint.pipeline.structure",
        "pipeline",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        {
            "num_stages": len(plan["stages"]),
            "data_edges": len(plan.get("data_edges", [])),
            "stream_edges": len(plan.get("stream_edges", [])),
            "pipeline_style": plan.get("pipeline_style"),
            "multi_layer_execution": plan.get("multi_layer_execution", {}),
            "branch_join_contracts": plan.get("branch_join_contracts", {}),
            "checker_summary": plan.get("checker_summary", {}),
        },
    )
    add_constraint(
        state,
        "constraint.stream.order",
        "data_order",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        {
            "transfer_order": ["token", "tile", "lane", "word"],
            "stream_edges_mirror_data_edges": True,
            "edge_contracts": [
                {
                    "edge_id": edge.get("edge_id"),
                    "src_stage": edge.get("src_stage"),
                    "dst_stage": edge.get("dst_stage"),
                    "kind": edge.get("kind"),
                    "stream_contract": edge.get("stream_contract", {}),
                }
                for edge in plan.get("stream_edges", [])
            ],
        },
    )
    add_constraint(
        state,
        "constraint.beat.pipeline",
        "transfer_alignment",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        {
            "alignment": "stage_outputs_must_match_declared_shape_and_numeric_stream_contract",
            "board_axi": (plan.get("memory_schedule") or {}).get("board_axi", {}),
        },
    )
    add_constraint(
        state,
        "constraint.buffering.pipeline",
        "buffering",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        {"buffers": plan.get("buffer_plan", [])},
    )
    add_constraint(
        state,
        "constraint.flow_control.pipeline",
        "flow_control",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        plan.get("flow_control", {}),
    )
    add_constraint(
        state,
        "constraint.memory_schedule.pipeline",
        "memory_schedule",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        plan.get("memory_schedule", {}),
    )
    add_constraint(
        state,
        "constraint.liveness.pipeline",
        "liveness",
        pipeline_node_ids,
        edge_ids,
        artifact_ids,
        {
            "producer_consumer_rates": "bounded by ready_valid backpressure and measured by later verification; not proven from symbolic latency estimates",
            "static_liveness": "acyclic_dataflow_with_bounded_ready_valid_fifos",
        },
    )
    add_invariant(state, "invariant.pipeline_plan_static", "pipeline_plan_static_check", constraints)

    add_node(
        state,
        "node.pipeline.block_input",
        "pipeline_boundary",
        "block_input",
        constraints,
        artifact_ids,
        {
            "role": "input_boundary",
            "shape": (plan.get("stages") or [{}])[0].get("input_shape", {}) if plan.get("stages") else {},
            "numeric_bits": (plan.get("numeric_stream_policy") or {}).get("accumulator_bits"),
        },
    )
    add_node(
        state,
        "node.pipeline.block_output",
        "pipeline_boundary",
        "block_output",
        constraints,
        artifact_ids,
        {
            "role": "output_boundary",
            "shape": (plan.get("stages") or [{}])[-1].get("output_shape", {}) if plan.get("stages") else {},
            "numeric_bits": (plan.get("numeric_stream_policy") or {}).get("accumulator_bits"),
        },
    )
    for stage in plan["stages"]:
        node_id = f"node.pipeline.{stage['stage_id']}"
        add_node(state, node_id, "pipeline_stage", stage["stage_id"], constraints, artifact_ids, stage)
    for edge in plan["stream_edges"]:
        src_node = f"node.pipeline.{safe_id(str(edge['src_stage']))}"
        dst_node = f"node.pipeline.{safe_id(str(edge['dst_stage']))}"
        add_edge(
            state,
            edge["edge_id"],
            "stream",
            src_node,
            dst_node,
            ["constraint.stream.order", "constraint.beat.pipeline", "constraint.liveness.pipeline"],
            artifact_ids,
            edge,
        )
    write_json(target_state, state)

    store = SACGStore(target_state)
    touched_constraints = [*TOUCHED_CONSTRAINTS, *constraints]
    transition = store.declare_transition(
        action_type="pipeline_planning",
        touched_nodes=["node.model", "node.template_library", "node.design_space", *pipeline_node_ids],
        touched_edges=edge_ids,
        touched_constraints=touched_constraints,
        note="Created initial spatial pipeline plan from selected templates.",
    )
    store.bind_artifact("artifact.stage3.pipeline_plan", str(plan_path), "stage.pipeline_plan", pipeline_node_ids, edge_ids, constraints, transition["id"])
    store.bind_artifact(
        "artifact.stage3.pipeline_static_checks",
        str(check_path),
        "stage.pipeline_static_checks",
        pipeline_node_ids,
        edge_ids,
        constraints,
        transition["id"],
    )
    store.attach_evidence(
        checker="pipeline_plan_static_check",
        status="pass" if checks.get("status") == "pass" else "fail",
        invariant="invariant.pipeline_plan_static",
        constraints=constraints,
        artifacts=["artifact.stage3.pipeline_plan", "artifact.stage3.pipeline_static_checks"],
        log_path=str(check_path),
        transition_id=transition["id"],
        summary=str((checks.get("summary") or {}).get("errors") or "pipeline static checks passed"),
    )
    if errors:
        store.reject(transition["id"], f"pipeline planning failed gate checks: {errors[:8]}")
    else:
        store.promote(transition["id"])
    store.save()
    return transition["id"]


def plan_pipeline(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    source_state = args.sacg_state.resolve()
    run_dir = run_dir_from_state(source_state)
    out_dir = run_dir / "pipeline_planning"
    plan_path = out_dir / "pipeline_plan.json"
    check_path = out_dir / "pipeline_static_checks.json"
    state_path = out_dir / "sacg_state.json"
    report_path = out_dir / "pipeline_planning_report.json"

    source_data = read_json(source_state)
    plan = build_pipeline_plan(source_data)
    checks = {
        "schema_version": "spatialaccagent.pipeline_static_checks.v0",
        "stage": "pipeline_planning",
        "status": "pass" if not (plan.get("checker_summary") or {}).get("errors") else "fail",
        "checker_results": plan.get("checker_results", []),
        "summary": plan.get("checker_summary", {}),
    }
    write_json(plan_path, plan)
    write_json(check_path, checks)
    team = run_design_team(
        stage="pipeline_planning",
        objective="Plan and audit the spatial pipeline as a set of SACG stream, beat, memory, and liveness constraints.",
        state=source_data,
        candidate_artifact=plan,
        out_dir=out_dir,
    )
    design_team = normalize_design_team_actions(team_summary(team))
    llm = run_stage_agent(
        agent="pipeline_architect_agent",
        stage="pipeline_planning",
        task="Review the candidate spatial pipeline plan and team decomposition before it is committed into SACG.",
        inputs={
            "candidate_pipeline_plan": plan,
            "stage_gate_policy": plan.get("stage_gate_policy", {}),
            "checker_results": checks.get("checker_results", []),
            "checker_summary": checks.get("summary", {}),
            "pipeline_static_checks": checks,
            "design_team": design_team,
            "source_sacg_state": str(source_state),
        },
        out_dir=out_dir,
        fallback_summary="Pipeline plan generated from selected templates.",
    )
    errors = list((checks.get("summary") or {}).get("errors") or [])
    errors.extend(team_failure_errors(design_team))
    errors.extend(stage_worker_errors(llm["output"]))
    transition_id = update_sacg(source_state, state_path, plan_path, check_path, plan, checks, errors)
    report = {
        "schema_version": "spatialaccagent.pipeline_planning_report.v0",
        "stage": "pipeline_planning",
        "status": "ready" if not errors else "incomplete",
        "source_sacg_state": str(source_state),
        "outputs": {
            "pipeline_plan": str(plan_path),
            "pipeline_static_checks": str(check_path),
            "sacg_state": str(state_path),
            "llm_agent": llm["result_path"],
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        },
        "llm_agent": llm["output"],
        "design_team": design_team,
        "checker_summary": checks.get("summary", {}),
        "num_pipeline_stages": len(plan["stages"]),
        "num_stream_edges": len(plan["stream_edges"]),
        "num_data_edges": len(plan.get("data_edges", [])),
        "sacg_transition_id": transition_id,
        "errors": errors,
    }
    write_json(report_path, report)
    return report_path, report


def main(argv: list[str] | None = None) -> int:
    return run_sacg_stage("Pipeline planning stage", plan_pipeline, argv)


if __name__ == "__main__":
    raise SystemExit(main())
