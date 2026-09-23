"""Build the initial shared design graph from prepared inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from accagent.framework.stage_constraints_common import (
    ConstraintExtractionError,
    make_input_artifact,
    read_json,
    resolve_input,
    write_json,
)
from accagent.framework.stage_llm import run_stage_agent
from accagent.framework.stage_team import run_design_team, team_failure_errors, team_summary


INPUT_NAMES = [
    "material_index",
    "sample_project_index",
    "field_evidence",
    "task_card",
    "model_config",
    "numeric_policy",
    "template_library",
    "template_metadata",
    "design_space",
    "target_board_profile",
    "tool_profile",
    "tool_availability",
    "tool_protocols",
    "case_adapter",
    "human_agent_boundary",
]


INPUT_CONSTRAINTS = {
    "material_index": ["constraint.source.materials"],
    "sample_project_index": ["constraint.source.materials"],
    "field_evidence": ["constraint.source.evidence", "constraint.cross_layer.input_consistency"],
    "task_card": ["constraint.task.goal"],
    "model_config": ["constraint.model.decoder", "constraint.shape.model"],
    "numeric_policy": ["constraint.numeric.policy"],
    "template_library": ["constraint.template.library"],
    "template_metadata": ["constraint.template.library"],
    "design_space": ["constraint.arch.design_space"],
    "target_board_profile": ["constraint.deployment.board", "constraint.memory.board", "constraint.runtime.board"],
    "tool_profile": ["constraint.tool.profile"],
    "tool_availability": ["constraint.tool.profile", "constraint.cross_layer.input_consistency"],
    "tool_protocols": ["constraint.tool.protocols"],
    "case_adapter": ["constraint.case.adapter", "constraint.tool.protocols"],
    "human_agent_boundary": ["constraint.human.boundary"],
}


def op_id(index: int, op: str) -> str:
    return f"node.model_op.{index:02d}_{op.replace('-', '_')}"


def material_counts(material_index: dict[str, Any], sample_project_index: dict[str, Any]) -> dict[str, Any]:
    counts = material_index.get("counts", {})
    return {
        "quantization_files": counts.get("quantization_files", 0),
        "board_files": counts.get("board_files", 0),
        "tool_files": counts.get("tool_files", 0),
        "sample_project_refs": counts.get("sample_project_refs", len(sample_project_index.get("refs", []))),
        "sample_project_samples": counts.get("sample_project_samples", len(sample_project_index.get("samples", []))),
    }


def evidence_fields(field_evidence: dict[str, Any]) -> list[str]:
    fields = {
        str(item.get("field"))
        for item in field_evidence.get("evidence", [])
        if isinstance(item, dict) and item.get("field")
    }
    return sorted(fields)


def evidence_items(field_evidence: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, item in enumerate(field_evidence.get("evidence", [])):
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "id": f"evidence.field.{index:04d}",
                "field": item.get("field"),
                "value": item.get("value"),
                "source": item.get("source"),
                "chunk_id": item.get("chunk_id"),
                "excerpt": item.get("excerpt"),
            }
        )
    return items


def evidence_by_field(field_evidence: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in evidence_items(field_evidence):
        field = str(item.get("field") or "")
        if not field:
            continue
        grouped.setdefault(field, []).append(item)
    return grouped


def unique_evidence_values(field_evidence: dict[str, Any], field: str) -> list[Any]:
    values: list[Any] = []
    seen: set[str] = set()
    for item in evidence_by_field(field_evidence).get(field, []):
        value = item.get("value")
        key = json.dumps(value, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        values.append(value)
    return values


def field_resolution(field_evidence: dict[str, Any], board: dict[str, Any], tool_profile: dict[str, Any]) -> dict[str, Any]:
    memory_system = board.get("memory_system", {})
    runtime = board.get("runtime_interface", {})
    board_info = board.get("board", {})
    tools = {str(tool.get("name", "")).lower(): tool for tool in tool_profile.get("tools", []) if isinstance(tool, dict)}
    resolved = {
        "board.fpga_part": board_info.get("fpga_part"),
        "memory_system.ddr_channels": memory_system.get("ddr_channels"),
        "memory_system.ddr_word_width_bits": memory_system.get("ddr_word_width_bits"),
        "memory_system.axi_data_bytes": memory_system.get("axi_data_bytes"),
        "memory_system.axi_data_width_bits": memory_system.get("axi_data_width_bits"),
        "memory_system.axi_addr_width_bits": memory_system.get("axi_addr_width_bits"),
        "memory_system.axi_id_width_bits": memory_system.get("axi_id_width_bits"),
        "memory_system.axi_wstrb_width_bits": memory_system.get("axi_wstrb_width_bits"),
        "memory_system.core_side_interface_name": memory_system.get("core_side_interface_name"),
        "memory_system.axi_clock": memory_system.get("axi_clock"),
        "memory_system.axi_reset": memory_system.get("axi_reset"),
        "memory_system.calibration_done_signal": memory_system.get("calibration_done_signal"),
        "runtime_interface.control_protocol": runtime.get("control_protocol"),
        "runtime_interface.board_run_command": runtime.get("board_run_command"),
        "runtime_interface.remote_host": runtime.get("remote_host"),
        "runtime_interface.xdma_id_default": runtime.get("xdma_id_default"),
        "runtime_interface.ctrl_base": runtime.get("ctrl_base"),
        "runtime_interface.ddr_base": runtime.get("ddr_base"),
        "runtime_interface.output_abs": runtime.get("output_abs"),
        "runtime_interface.ddr_image_default": runtime.get("ddr_image_default"),
        "tool.vcs.host": tools.get("vcs", {}).get("host"),
        "tool.vcs.executable": tools.get("vcs", {}).get("executable"),
        "tool.vivado.host": tools.get("vivado", {}).get("host"),
        "tool.vivado.executable": tools.get("vivado", {}).get("executable"),
    }
    by_field = evidence_by_field(field_evidence)
    result: dict[str, Any] = {}
    for field, value in resolved.items():
        values = unique_evidence_values(field_evidence, field)
        result[field] = {
            "resolved_value": value,
            "evidence_values": values,
            "evidence": by_field.get(field, []),
            "matches_evidence": True if value in {None, ""} or not values else value in values,
        }
    return result


def conflict_rules(field_evidence: dict[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    axi_values = unique_evidence_values(field_evidence, "memory_system.axi_data_bytes")
    if len(axi_values) > 1:
        rules.append(
            {
                "id": "rule.real_board_axi_width_over_simulation_scaffold",
                "field": "memory_system.axi_data_bytes",
                "observed_values": axi_values,
                "chosen_value": max(value for value in axi_values if isinstance(value, int)) if any(isinstance(value, int) for value in axi_values) else axi_values[0],
                "priority": [
                    "explicit target_board_profile memory_system source labels",
                    "real board reference RTL declared by the current board materials",
                    "simulation scaffold evidence only when it is marked as the real board interface",
                ],
                "reason": (
                    "Multiple AXI beat widths were observed in the input materials. The framework must not assume a fixed "
                    "board interface; Stage-7 runtime ABI gates must validate against the current target_board_profile and "
                    "its declared real board reference RTL."
                ),
            }
        )
    return rules


def tool_names(tool_profile: dict[str, Any]) -> list[str]:
    return sorted(
        str(tool.get("name"))
        for tool in tool_profile.get("tools", [])
        if isinstance(tool, dict) and tool.get("name")
    )


def availability_summary(tool_availability: dict[str, Any]) -> dict[str, Any]:
    tools = []
    for tool in tool_availability.get("tools", []):
        if not isinstance(tool, dict):
            continue
        tools.append(
            {
                "name": tool.get("name"),
                "available": tool.get("available"),
                "version_ok": tool.get("version_ok"),
                "flow_probe_ok": tool.get("flow_probe_ok"),
                "errors": tool.get("errors", []),
            }
        )
    return {"tools": tools}


def build_design_graph_nodes_edges(
    inputs: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    material_index = inputs["material_index"]
    sample_project_index = inputs["sample_project_index"]
    field_evidence = inputs["field_evidence"]
    task = inputs["task_card"]
    model = inputs["model_config"]
    numeric = inputs["numeric_policy"]
    templates = inputs["template_metadata"]
    library = inputs["template_library"]
    design_space = inputs["design_space"]
    board = inputs["target_board_profile"]
    tool_profile = inputs["tool_profile"]
    tool_availability = inputs["tool_availability"]
    tool_protocols = inputs["tool_protocols"]
    case_adapter = inputs["case_adapter"]
    boundary = inputs["human_agent_boundary"]
    ops = [str(op) for op in model.get("block", {}).get("operator_sequence", [])]
    material_summary = material_counts(material_index, sample_project_index)
    evidence_field_names = evidence_fields(field_evidence)
    all_evidence = evidence_items(field_evidence)
    grouped_evidence = evidence_by_field(field_evidence)
    resolved_fields = field_resolution(field_evidence, board, tool_profile)
    conflict_resolution_rules = conflict_rules(field_evidence)

    nodes: list[dict[str, Any]] = [
        {
            "id": "node.input_materials",
            "type": "input_materials",
            "name": "current_run_input_materials",
            "constraints": ["constraint.source.materials"],
            "artifacts": ["artifact.input.material_index", "artifact.input.sample_project_index"],
            "facts": material_summary,
        },
        {
            "id": "node.input_evidence",
            "type": "input_evidence",
            "name": "extracted_field_evidence",
            "constraints": ["constraint.source.evidence"],
            "artifacts": ["artifact.input.field_evidence"],
            "facts": {
                "fields": evidence_field_names,
                "evidence_count": len(all_evidence),
                "evidence_by_field": grouped_evidence,
            },
        },
        {
            "id": "node.task",
            "type": "task",
            "name": str(task.get("target_model", "task")),
            "constraints": ["constraint.task.goal"],
            "artifacts": ["artifact.input.task_card"],
        },
        {
            "id": "node.model",
            "type": "model_spec",
            "name": str(model.get("model_type")),
            "constraints": ["constraint.model.decoder", "constraint.shape.model"],
            "artifacts": ["artifact.input.model_config"],
        },
        {
            "id": "node.numeric_policy",
            "type": "numeric_policy",
            "name": str(numeric.get("policy_id", "numeric_policy")),
            "constraints": ["constraint.numeric.policy"],
            "artifacts": ["artifact.input.numeric_policy"],
        },
        {
            "id": "node.template_library",
            "type": "template_library",
            "name": str(templates.get("library_id", "template_library")),
            "constraints": ["constraint.template.library"],
            "artifacts": ["artifact.input.template_library", "artifact.input.template_metadata"],
        },
        {
            "id": "node.design_space",
            "type": "architecture_search",
            "name": "design_space",
            "constraints": ["constraint.arch.design_space"],
            "artifacts": ["artifact.input.design_space"],
        },
        {
            "id": "node.target_board",
            "type": "deployment_target",
            "name": str(board.get("board", {}).get("board_id", "target_board")),
            "constraints": ["constraint.deployment.board", "constraint.memory.board", "constraint.runtime.board"],
            "artifacts": ["artifact.input.target_board_profile"],
        },
        {
            "id": "node.tool_profile",
            "type": "tool_profile",
            "name": "tool_profile",
            "constraints": ["constraint.tool.profile"],
            "artifacts": ["artifact.input.tool_profile", "artifact.input.tool_availability"],
        },
        {
            "id": "node.tool_protocols",
            "type": "tool_protocol",
            "name": "tool_protocols",
            "constraints": ["constraint.tool.protocols"],
            "artifacts": ["artifact.input.tool_protocols"],
        },
        {
            "id": "node.case_adapter",
            "type": "verification_case_adapter",
            "name": str(case_adapter.get("case_id", "case_adapter")),
            "constraints": ["constraint.case.adapter", "constraint.tool.protocols"],
            "artifacts": ["artifact.input.case_adapter"],
            "facts": {
                "case_id": case_adapter.get("case_id"),
                "model_family": case_adapter.get("model_family"),
                "status": case_adapter.get("status"),
                "source": case_adapter.get("source"),
                "evidence_gates": case_adapter.get("evidence_gates", {}),
            },
        },
        {
            "id": "node.human_boundary",
            "type": "human_agent_boundary",
            "name": "human_agent_boundary",
            "constraints": ["constraint.human.boundary"],
            "artifacts": ["artifact.input.human_agent_boundary"],
        },
    ]
    for index, op in enumerate(ops):
        nodes.append(
            {
                "id": op_id(index, op),
                "type": "model_operator",
                "name": op,
                "constraints": ["constraint.model.decoder", "constraint.shape.model"],
                "artifacts": ["artifact.input.model_config"],
                "facts": {"op": op, "index": index},
            }
        )

    edges: list[dict[str, Any]] = []
    for index in range(len(ops) - 1):
        edges.append(
            {
                "id": f"edge.model_order.{index:02d}",
                "type": "model_order",
                "src": op_id(index, ops[index]),
                "dst": op_id(index + 1, ops[index + 1]),
                "constraints": ["constraint.model.decoder"],
                "artifacts": ["artifact.input.model_config"],
                "facts": {"src_op": ops[index], "dst_op": ops[index + 1]},
            }
        )

    op_nodes = [op_id(index, op) for index, op in enumerate(ops)]
    constraints = [
        {
            "id": "constraint.source.materials",
            "type": "source_materials",
            "nodes": ["node.input_materials"],
            "edges": [],
            "artifacts": ["artifact.input.material_index", "artifact.input.sample_project_index"],
            "facts": {
                "counts": material_summary,
                "paths": material_index.get("paths", {}),
                "sample_project_refs": sample_project_index.get("refs", []),
            },
        },
        {
            "id": "constraint.source.evidence",
            "type": "source_evidence",
            "nodes": ["node.input_evidence"],
            "edges": [],
            "artifacts": ["artifact.input.field_evidence"],
            "facts": {
                "policy": field_evidence.get("policy", {}),
                "fields": evidence_field_names,
                "evidence_count": len(all_evidence),
                "evidence": all_evidence,
                "evidence_by_field": grouped_evidence,
            },
        },
        {
            "id": "constraint.task.goal",
            "type": "task",
            "nodes": ["node.task"],
            "edges": [],
            "artifacts": ["artifact.input.task_card"],
            "facts": task,
        },
        {
            "id": "constraint.model.decoder",
            "type": "model",
            "nodes": ["node.model", *op_nodes],
            "edges": [edge["id"] for edge in edges],
            "artifacts": ["artifact.input.model_config"],
            "facts": {
                "model_type": model.get("model_type"),
                "num_layers": model.get("num_layers"),
                "block_type": model.get("block", {}).get("type"),
                "operator_sequence": ops,
                "attention_kind": model.get("attention", {}).get("kind"),
                "num_q_heads": model.get("attention", {}).get("num_q_heads"),
                "num_kv_heads": model.get("attention", {}).get("num_kv_heads"),
                "head_dim": model.get("attention", {}).get("head_dim"),
                "position_encoding": model.get("attention", {}).get("position_encoding", {}),
                "norm_type": model.get("norm", {}).get("type"),
                "mlp_type": model.get("mlp", {}).get("type"),
                "activation": model.get("mlp", {}).get("activation"),
            },
        },
        {
            "id": "constraint.shape.model",
            "type": "shape",
            "nodes": ["node.model", *op_nodes],
            "edges": [],
            "artifacts": ["artifact.input.model_config"],
            "facts": {
                "hidden_size": model.get("hidden_size"),
                "target_max_seq_len": model.get("target_max_seq_len"),
                "intermediate_size": model.get("mlp", {}).get("intermediate_size"),
                "head_dim": model.get("attention", {}).get("head_dim"),
                "num_q_heads": model.get("attention", {}).get("num_q_heads"),
                "num_kv_heads": model.get("attention", {}).get("num_kv_heads"),
            },
        },
        {
            "id": "constraint.numeric.policy",
            "type": "numeric",
            "nodes": ["node.numeric_policy"],
            "edges": [],
            "artifacts": ["artifact.input.numeric_policy"],
            "facts": numeric,
        },
        {
            "id": "constraint.template.library",
            "type": "template",
            "nodes": ["node.template_library"],
            "edges": [],
            "artifacts": ["artifact.input.template_library", "artifact.input.template_metadata"],
            "facts": {
                "library_id": templates.get("library_id"),
                "template_dir": library.get("template_dir"),
                "source_files": library.get("source_files", []),
                "policy": library.get("policy", {}),
                "templates": templates.get("templates", []),
            },
        },
        {
            "id": "constraint.arch.design_space",
            "type": "architecture",
            "nodes": ["node.design_space"],
            "edges": [],
            "artifacts": ["artifact.input.design_space"],
            "facts": design_space,
        },
        {
            "id": "constraint.deployment.board",
            "type": "deployment",
            "nodes": ["node.target_board"],
            "edges": [],
            "artifacts": ["artifact.input.target_board_profile"],
            "facts": {
                "board": board.get("board", {}),
                "shell": board.get("shell", {}),
                "board_pass_criteria": board.get("board_pass_criteria", {}),
            },
        },
        {
            "id": "constraint.memory.board",
            "type": "memory",
            "nodes": ["node.target_board"],
            "edges": [],
            "artifacts": ["artifact.input.target_board_profile"],
            "facts": {"memory_system": board.get("memory_system", {})},
        },
        {
            "id": "constraint.runtime.board",
            "type": "runtime",
            "nodes": ["node.target_board"],
            "edges": [],
            "artifacts": ["artifact.input.target_board_profile"],
            "facts": board.get("runtime_interface", {}),
        },
        {
            "id": "constraint.tool.profile",
            "type": "tool_profile",
            "nodes": ["node.tool_profile"],
            "edges": [],
            "artifacts": ["artifact.input.tool_profile", "artifact.input.tool_availability"],
            "facts": {
                "tool_names": tool_names(tool_profile),
                "profile": tool_profile,
                "availability": availability_summary(tool_availability),
            },
        },
        {
            "id": "constraint.tool.protocols",
            "type": "tool",
            "nodes": ["node.tool_protocols"],
            "edges": [],
            "artifacts": ["artifact.input.tool_protocols"],
            "facts": tool_protocols,
        },
        {
            "id": "constraint.case.adapter",
            "type": "verification_case_adapter",
            "nodes": ["node.case_adapter"],
            "edges": [],
            "artifacts": ["artifact.input.case_adapter"],
            "facts": case_adapter,
        },
        {
            "id": "constraint.human.boundary",
            "type": "human_boundary",
            "nodes": ["node.human_boundary"],
            "edges": [],
            "artifacts": ["artifact.input.human_agent_boundary"],
            "facts": boundary,
        },
        {
            "id": "constraint.cross_layer.input_consistency",
            "type": "cross_layer_consistency",
            "nodes": [
                "node.input_materials",
                "node.input_evidence",
                "node.task",
                "node.model",
                "node.numeric_policy",
                "node.template_library",
                "node.design_space",
                "node.target_board",
                "node.tool_profile",
                "node.tool_protocols",
                "node.case_adapter",
                "node.human_boundary",
            ],
            "edges": [edge["id"] for edge in edges],
            "artifacts": [f"artifact.input.{name}" for name in INPUT_NAMES],
            "facts": {
                "model": {
                    "model_type": model.get("model_type"),
                    "num_layers": model.get("num_layers"),
                    "target_max_seq_len": model.get("target_max_seq_len"),
                    "operator_count": len(ops),
                },
                "numeric_policy": {
                    "policy_id": numeric.get("policy_id"),
                    "default_rules": numeric.get("default_rules", {}),
                },
                "board": {
                    "board": board.get("board", {}),
                    "memory_system": board.get("memory_system", {}),
                    "runtime_interface": board.get("runtime_interface", {}),
                },
                "tools": {
                    "tool_names": tool_names(tool_profile),
                    "availability": availability_summary(tool_availability),
                    "protocol_count": len(tool_protocols.get("tools", [])),
                    "case_adapter": {
                        "case_id": case_adapter.get("case_id"),
                        "model_family": case_adapter.get("model_family"),
                        "status": case_adapter.get("status"),
                        "source": case_adapter.get("source"),
                    },
                },
                "materials": material_summary,
                "evidence_fields": evidence_field_names,
                "evidence_by_field": grouped_evidence,
                "field_resolution": resolved_fields,
                "conflict_rules": conflict_resolution_rules,
                "acceptance_boundary": task.get("acceptance") or task.get("acceptance_boundary") or {},
            },
        },
    ]
    return nodes, edges, constraints


def validate_constraints(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], constraints: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    node_ids = {node.get("id") for node in nodes}
    edge_ids = {edge.get("id") for edge in edges}
    constraint_ids = {constraint.get("id") for constraint in constraints}
    if len(node_ids) != len(nodes):
        errors.append("duplicate node id")
    if len(edge_ids) != len(edges):
        errors.append("duplicate edge id")
    if len(constraint_ids) != len(constraints):
        errors.append("duplicate constraint id")
    for node in nodes:
        for cid in node.get("constraints", []):
            if cid not in constraint_ids:
                errors.append(f"node {node.get('id')} references unknown constraint {cid}")
    for edge in edges:
        if edge.get("src") not in node_ids:
            errors.append(f"edge {edge.get('id')} references unknown src {edge.get('src')}")
        if edge.get("dst") not in node_ids:
            errors.append(f"edge {edge.get('id')} references unknown dst {edge.get('dst')}")
        for cid in edge.get("constraints", []):
            if cid not in constraint_ids:
                errors.append(f"edge {edge.get('id')} references unknown constraint {cid}")
    for constraint in constraints:
        for nid in constraint.get("nodes", []):
            if nid not in node_ids:
                errors.append(f"constraint {constraint.get('id')} references unknown node {nid}")
        for eid in constraint.get("edges", []):
            if eid not in edge_ids:
                errors.append(f"constraint {constraint.get('id')} references unknown edge {eid}")
    return errors


def build_initial_design_graph(
    design_id: str,
    input_paths: dict[str, Path],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    constraints: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "sacg_version": "1.0",
        "design_id": design_id,
        "nodes": nodes,
        "edges": edges,
        "constraints": constraints,
        "invariants": [],
        "artifacts": [make_input_artifact(name, input_paths[name], INPUT_CONSTRAINTS[name]) for name in INPUT_NAMES],
        "evidence": [],
        "failures": [],
        "repairs": [],
        "approvals": [],
        "transitions": [],
        "metadata": {
            "source_stage": "constraint_extraction",
            "framework_mode": "independent_from_scratch_design",
            "external_name": "initial_design_graph",
            "input_grouping": {
                "materials": ["material_index", "sample_project_index"],
                "evidence": ["field_evidence"],
                "tools": ["tool_profile", "tool_availability", "tool_protocols", "case_adapter"],
            },
        },
    }


def extract_constraints(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    prepared_inputs = read_json(args.prepared_inputs)
    if prepared_inputs.get("status") != "ready" or prepared_inputs.get("errors"):
        raise ConstraintExtractionError(
            "prepared_inputs must be ready and error-free before constraint extraction: "
            f"status={prepared_inputs.get('status')} errors={prepared_inputs.get('errors', [])}"
        )
    run_dir = Path(prepared_inputs.get("run_dir", args.prepared_inputs.parents[1])).resolve()
    out_dir = run_dir / "constraint_extraction"
    out_dir.mkdir(parents=True, exist_ok=True)
    input_paths = {name: resolve_input(run_dir, prepared_inputs, name) for name in INPUT_NAMES}
    inputs = {name: read_json(path) for name, path in input_paths.items()}
    nodes, edges, constraints = build_design_graph_nodes_edges(inputs)
    errors = validate_constraints(nodes, edges, constraints)

    design_graph_path = out_dir / "initial_design_graph.json"
    report_path = out_dir / "constraint_extraction_report.json"
    initial_graph = build_initial_design_graph(args.design_id, input_paths, nodes, edges, constraints)
    write_json(design_graph_path, initial_graph)
    candidate_summary = {
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "num_constraints": len(constraints),
        "node_ids": [node["id"] for node in nodes],
        "constraint_ids": [constraint["id"] for constraint in constraints],
        "input_groups": initial_graph["metadata"]["input_grouping"],
        "source_material_counts": material_counts(inputs["material_index"], inputs["sample_project_index"]),
        "evidence_fields": evidence_fields(inputs["field_evidence"]),
        "tool_names": tool_names(inputs["tool_profile"]),
    }
    team = run_design_team(
        stage="constraint_extraction",
        objective=(
            "Build and audit the initial design graph as shared state for a chip-design-team flow. "
            "The graph must preserve cross-layer consistency across model, shape, numeric policy, "
            "template choices, board DDR/AXI/runtime information, tool availability, and human boundaries."
        ),
        state=initial_graph,
        candidate_artifact={
            "prepared_inputs_manifest": prepared_inputs,
            "candidate_design_graph_summary": candidate_summary,
            "validation_errors": errors,
        },
        out_dir=out_dir,
    )
    design_team = team_summary(team)
    report_errors = [*errors, *team_failure_errors(design_team)]
    if report_errors:
        llm = {"result_path": None, "output": {}}
    else:
        llm = run_stage_agent(
            agent="initial_design_graph_agent",
            stage="constraint_extraction",
            task=(
                "Review the initial design graph extracted from prepared inputs. You are the design-intake "
                "lead in a chip accelerator team: check whether model, shape, numeric policy, template, "
                "board DDR/AXI/runtime, tool, evidence, and human-boundary facts are represented clearly "
                "enough for later architecture, code generation, verification, and board implementation agents."
            ),
            inputs={
                "prepared_inputs_manifest": prepared_inputs,
                "candidate_design_graph_summary": candidate_summary,
                "validation_errors": errors,
                "design_team": design_team,
            },
            out_dir=out_dir,
            fallback_summary="Initial design graph created by deterministic extractor.",
        )
    report = {
        "schema_version": "spatialaccagent.constraint_extraction_report.v0",
        "stage": "constraint_extraction",
        "status": "ready" if not report_errors else "incomplete",
        "prepared_inputs": str(args.prepared_inputs),
        "outputs": {
            "initial_design_graph": str(design_graph_path),
            "llm_agent": llm["result_path"],
            "team_subtask_plan": team["subtask_plan_path"],
            "team_aggregate": team["aggregate_path"],
        },
        "llm_agent": llm["output"],
        "design_team": design_team,
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "num_constraints": len(constraints),
        "errors": report_errors,
    }
    write_json(report_path, report)
    return report_path, report


def revalidate_constraint_extraction(report_path: Path) -> list[str]:
    """Rebuild the deterministic Stage-1 graph without replaying its LLM team."""

    try:
        report = read_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"constraint extraction report cannot be read: {exc}"]
    if report.get("status") != "ready" or report.get("errors"):
        return [
            "constraint extraction is not a reusable passed stage: "
            f"status={report.get('status')} errors={report.get('errors', [])}"
        ]

    errors: list[str] = []
    prepared_path = Path(str(report.get("prepared_inputs") or ""))
    if not prepared_path.is_file():
        return ["constraint extraction report is missing its prepared-input manifest"]
    try:
        prepared = read_json(prepared_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"prepared inputs cannot be read during Stage-1 revalidation: {exc}"]
    if prepared.get("status") != "ready" or prepared.get("errors"):
        return ["Stage-1 prepared inputs are not ready and error-free"]

    run_dir = Path(str(prepared.get("run_dir") or prepared_path.parents[1])).resolve()
    try:
        input_paths = {name: resolve_input(run_dir, prepared, name) for name in INPUT_NAMES}
        inputs = {name: read_json(path) for name, path in input_paths.items()}
        expected_nodes, expected_edges, expected_constraints = build_design_graph_nodes_edges(inputs)
        errors.extend(validate_constraints(expected_nodes, expected_edges, expected_constraints))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return [f"Stage-1 deterministic graph reconstruction failed: {exc}"]

    graph_path = Path(str((report.get("outputs") or {}).get("initial_design_graph") or ""))
    if not graph_path.is_file():
        return [*errors, "constraint extraction report is missing initial_design_graph"]
    try:
        graph = read_json(graph_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [*errors, f"initial design graph cannot be read: {exc}"]
    if graph.get("nodes") != expected_nodes:
        errors.append("initial design graph nodes differ from current deterministic reconstruction")
    if graph.get("edges") != expected_edges:
        errors.append("initial design graph edges differ from current deterministic reconstruction")
    if graph.get("constraints") != expected_constraints:
        errors.append("initial design graph constraints differ from current deterministic reconstruction")
    errors.extend(
        validate_constraints(
            graph.get("nodes", []), graph.get("edges", []), graph.get("constraints", [])
        )
    )
    design_team = report.get("design_team")
    if not isinstance(design_team, dict):
        errors.append("constraint extraction report is missing design_team acceptance record")
    else:
        errors.extend(team_failure_errors(design_team))
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Constraint extraction stage")
    parser.add_argument("--prepared-inputs", type=Path, required=True)
    parser.add_argument("--design-id", default="unnamed_design")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report_path, report = extract_constraints(args)
        if report["errors"]:
            for error in report["errors"]:
                print(f"error: {error}", file=sys.stderr)
            print(report_path)
            return 1
        print(report_path)
        return 0
    except (OSError, ValueError, ConstraintExtractionError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
