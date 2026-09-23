"""Audit LLM executable action grounding against the framework tool registry."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from accagent.framework.sacg_utils import read_json, write_json
from accagent.framework.stage_llm import ACTION_GROUNDING_REGISTRY


GENERIC_ACTION_ALIASES = {
    "case_stage_leaf_static_check": "case_stage_leaf_static",
    "operator_leaf_functional_sim": "case_leaf_functional",
    "leaf_functional_sim": "case_leaf_functional",
    "operator_leaf_golden_compare": "case_leaf_golden_compare",
    "leaf_golden_compare": "case_leaf_golden_compare",
    "boundary_contract_checker": "boundary_contract_check",
    "case_multilayer_pipeline_check": "case_multilayer_pipeline",
    "single_layer_functional_sim": "case_single_layer_functional",
    "single_layer_golden_compare": "case_single_layer_golden_compare",
    "multilayer_functional_sim": "case_multilayer_functional",
    "pipeline_deadlock_checker": "case_pipeline_deadlock_check",
    "case_axi_ddr_interface_check": "case_axi_ddr_interface",
    "axi_protocol_checker": "case_axi_protocol_check",
    "ddr_image_roundtrip_checker": "case_ddr_image_roundtrip",
    "case_real_weight_artifacts_check": "case_real_weight_artifacts",
    "case_runtime_bitstream_checker": "case_runtime_bitstream",
    "case_runtime_bitstream_check": "case_runtime_bitstream",
    "case_testbench_runner": "case_tb_scaffold_generate",
    "real_weight_manifest_generator": "case_weight_manifest_generate",
    "real_input_manifest_generator": "case_weight_manifest_generate",
    "runtime_memory_packer": "case_weight_manifest_generate",
    "remote_vcs_functional_sim": "case_vcs_functional_sim",
    "remote_vcs_or_verilator_runner": "case_vcs_functional_sim",
    "remote_simulation_runner": "case_vcs_functional_sim",
    "verilator_fallback_if_configured": "case_verilator_functional_sim",
    "diagnosis_classifier": "case_vcs_evidence_analyzer",
    "vivado_synthesis_runner": "case_vivado_synthesis",
    "vivado_implementation_runner": "case_vivado_implementation",
    "vivado_backend_runner": "case_runtime_bitstream",
    "timing_utilization_checker": "timing_resource_check",
    "implementation_package_static_checker": "implementation_package_static",
    "board_runtime_runner": "board_runtime",
    "board_programmer": "board_runtime",
    "board_output_checker": "output_validity_check",
    "runtime_io_hash_checker": "artifact_hash_check",
    "artifact_hash_checker": "artifact_hash_check",
    "artifact_hash_emitter": "artifact_hash_check",
    "numeric_comparator": "numeric_compare",
    "numeric_compare_checker": "numeric_compare",
    "data_order_trace_checker": "data_order_trace_check",
    "tool_protocol_static_checker": "tool_protocol_check",
    "functional_sim_result_check": "functional_sim",
    "functional_sim_contract_check": "functional_sim",
    "implementation_package_static_check": "implementation_package_static",
    "deployment_board_check": "deployment_board_check",
    "output_validity_check": "output_validity_check",
    "targeted_failed_checker_rerun": "targeted_failed_checker_rerun",
    "team_aggregate": "team_aggregate",
}


def read_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return read_json(path)
    except Exception:
        return {}


def collect_actions_from_output(source: str, output: dict[str, Any]) -> list[dict[str, Any]]:
    actions = []
    for action in output.get("executable_actions", []) if isinstance(output.get("executable_actions"), list) else []:
        if isinstance(action, dict):
            actions.append({"source": source, "action": action})
    return actions


def collect_actions(path: Path) -> list[dict[str, Any]]:
    data = read_json_or_empty(path)
    if not data:
        return []
    actions = []
    if isinstance(data.get("output"), dict):
        actions.extend(collect_actions_from_output(str(path), data["output"]))
    if isinstance(data.get("llm_agent"), dict):
        actions.extend(collect_actions_from_output(f"{path}:llm_agent", data["llm_agent"]))
    if isinstance(data.get("design_team"), dict):
        actions.extend(collect_actions_from_output(f"{path}:design_team", data["design_team"]))
    return actions


def case_adapter_aliases(case_adapter: dict[str, Any] | None) -> dict[str, str]:
    aliases: dict[str, str] = {}
    if not isinstance(case_adapter, dict):
        return aliases
    tools = case_adapter.get("tools", {}) if isinstance(case_adapter.get("tools"), dict) else {}
    for role, tool in tools.items():
        if not isinstance(tool, dict):
            continue
        name = str(tool.get("name") or "")
        if not name:
            continue
        aliases[str(role)] = name
        aliases[name] = name
        kind = str(tool.get("kind") or "")
        if kind:
            aliases[kind] = name
        legacy = str(tool.get("legacy_name") or "")
        if legacy:
            aliases[legacy] = name
    gates = case_adapter.get("evidence_gates", {}) if isinstance(case_adapter.get("evidence_gates"), dict) else {}
    for _, gate in gates.items():
        gate_name = str(gate)
        aliases[gate_name] = gate_name
        aliases[f"{gate_name}_check"] = gate_name
        aliases[f"{gate_name}_checker"] = gate_name
    return aliases


def case_adapter_registry_names(case_adapter: dict[str, Any] | None) -> set[str]:
    names: set[str] = set()
    if not isinstance(case_adapter, dict):
        return names
    tools = case_adapter.get("tools", {}) if isinstance(case_adapter.get("tools"), dict) else {}
    for role, tool in tools.items():
        if not isinstance(tool, dict):
            continue
        for value in [role, tool.get("name"), tool.get("kind"), tool.get("legacy_name")]:
            text = str(value or "")
            if text:
                names.add(text)
    gates = case_adapter.get("evidence_gates", {}) if isinstance(case_adapter.get("evidence_gates"), dict) else {}
    for gate in gates.values():
        text = str(gate or "")
        if text:
            names.add(text)
    names.update(f"real_tool.{name}" for name in list(names))
    return names


def automatic_aliases(known: set[str]) -> dict[str, str]:
    aliases = dict(GENERIC_ACTION_ALIASES)
    for name in known:
        aliases.setdefault(f"{name}_check", name)
        aliases.setdefault(f"{name}_checker", name)
        aliases.setdefault(f"{name}_runner", name)
        if name.startswith("case_"):
            aliases.setdefault(name.replace("case_", "generated_case_", 1), name)
    return aliases


def normalize_ref(value: str, known: set[str], aliases: dict[str, str], planned_prefix: str) -> tuple[str, str | None]:
    if value in known or value.startswith(planned_prefix):
        return value, None
    if value.startswith("real_tool."):
        suffix = value[len("real_tool.") :]
        canonical_suffix = aliases.get(suffix, suffix)
        canonical = f"real_tool.{canonical_suffix}"
        if canonical in known:
            return canonical, value
    canonical = aliases.get(value)
    if canonical and (canonical in known or canonical.startswith(planned_prefix)):
        return canonical, value
    qualified = f"real_tool.{value}"
    if qualified in known:
        return qualified, value
    if planned_prefix == "planned_checker.":
        for suffix in ("_check", "_checker"):
            if value.endswith(suffix):
                trimmed = value[: -len(suffix)]
                canonical = aliases.get(trimmed, trimmed)
                if canonical in known:
                    return canonical, value
                if suffix == "_checker":
                    canonical = aliases.get(f"{trimmed}_check", f"{trimmed}_check")
                    if canonical in known:
                        return canonical, value
                qualified = f"real_tool.{canonical}"
                if qualified in known:
                    return qualified, value
    suffixes = ("_check", "_checker")
    if planned_prefix == "planned_tool.":
        suffixes += ("_runner",)
    for suffix in suffixes:
        candidate = f"{value}{suffix}"
        if candidate in known:
            return candidate, value
        canonical = aliases.get(candidate)
        if canonical in known:
            return canonical, value
        qualified = f"real_tool.{candidate}"
        if qualified in known:
            return qualified, value
    return value, None


def audit_action(
    item: dict[str, Any],
    known_tools: set[str],
    known_checkers: set[str],
    aliases: dict[str, str] | None = None,
) -> dict[str, Any]:
    aliases = aliases or {}
    action = item["action"]
    tool_roles = [str(value) for value in action.get("tool_roles", []) if value is not None]
    checkers = [str(value) for value in action.get("acceptance_checkers", []) if value is not None]
    tool_norm = [normalize_ref(value, known_tools, aliases, "planned_tool.") for value in tool_roles]
    checker_norm = [normalize_ref(value, known_checkers, aliases, "planned_checker.") for value in checkers]
    canonical_tools = [value for value, _ in tool_norm]
    canonical_checkers = [value for value, _ in checker_norm]
    unknown_tools = [original for original, (value, _) in zip(tool_roles, tool_norm) if value not in known_tools and not value.startswith("planned_tool.")]
    unknown_checkers = [original for original, (value, _) in zip(checkers, checker_norm) if value not in known_checkers and not value.startswith("planned_checker.")]
    planned_tools = [value for value in canonical_tools if value.startswith("planned_tool.")]
    planned_checkers = [value for value in canonical_checkers if value.startswith("planned_checker.")]
    normalized_aliases = [
        {"original": original, "canonical": canonical}
        for original, (canonical, alias_from) in [*zip(tool_roles, tool_norm), *zip(checkers, checker_norm)]
        if alias_from is not None and original != canonical
    ]
    return {
        "source": item["source"],
        "id": action.get("id"),
        "action_type": action.get("action_type"),
        "tool_roles": tool_roles,
        "acceptance_checkers": checkers,
        "canonical_tool_roles": canonical_tools,
        "canonical_acceptance_checkers": canonical_checkers,
        "normalized_aliases": normalized_aliases,
        "unknown_tool_roles": unknown_tools,
        "unknown_acceptance_checkers": unknown_checkers,
        "planned_tools": planned_tools,
        "planned_checkers": planned_checkers,
        "status": "pass" if not unknown_tools and not unknown_checkers else "fail",
    }


def build_audit_from_action_items(
    action_items: list[dict[str, Any]],
    case_adapter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    adapter_names = case_adapter_registry_names(case_adapter)
    known_tools = set(ACTION_GROUNDING_REGISTRY["tool_roles"]) | adapter_names
    known_checkers = set(ACTION_GROUNDING_REGISTRY["acceptance_checkers"]) | adapter_names
    aliases = {
        **automatic_aliases(known_tools | known_checkers),
        **case_adapter_aliases(case_adapter),
    }
    audits = [audit_action(item, known_tools, known_checkers, aliases) for item in action_items]
    failed = [item for item in audits if item["status"] != "pass"]
    planned_tools = [tool for item in audits for tool in item.get("planned_tools", [])]
    planned_checkers = [checker for item in audits for checker in item.get("planned_checkers", [])]
    return {
        "schema_version": "spatialaccagent.llm_action_audit.v0",
        "status": "pass" if not failed else "fail",
        "summary": f"{len(audits)} executable action(s), {len(failed)} ungrounded",
        "registry": ACTION_GROUNDING_REGISTRY,
        "actions": audits,
        "ungrounded_actions": failed,
        "planned_tool_count": len(planned_tools),
        "planned_checker_count": len(planned_checkers),
        "planned_tools": sorted(set(planned_tools)),
        "planned_checkers": sorted(set(planned_checkers)),
        "policy": "LLM actions must be grounded in configured framework tool/checker names or explicitly marked planned_tool/planned_checker.",
    }


def build_audit_from_outputs(outputs: list[tuple[str, dict[str, Any]]], case_adapter: dict[str, Any] | None = None) -> dict[str, Any]:
    action_items: list[dict[str, Any]] = []
    for source, output in outputs:
        if isinstance(output, dict):
            action_items.extend(collect_actions_from_output(source, output))
    return build_audit_from_action_items(action_items, case_adapter)


def build_audit(paths: list[Path], case_adapter: dict[str, Any] | None = None) -> dict[str, Any]:
    action_items = []
    for path in paths:
        if path.is_dir():
            for item in sorted(path.rglob("*_result.json")):
                action_items.extend(collect_actions(item))
            for item in sorted(path.rglob("*_report.json")):
                action_items.extend(collect_actions(item))
            for item in sorted(path.rglob("team_aggregate.json")):
                action_items.extend(collect_actions(item))
        else:
            action_items.extend(collect_actions(path))
    return build_audit_from_action_items(action_items, case_adapter)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit LLM executable action grounding.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case-adapter-json", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    case_adapter = read_json_or_empty(args.case_adapter_json) if args.case_adapter_json else None
    report = build_audit([path.resolve() for path in args.paths], case_adapter)
    write_json(args.out, report)
    print(report["summary"])
    return 1 if report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
