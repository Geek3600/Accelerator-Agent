"""Run-local profile controls for controlled ACCORD ablations."""

from __future__ import annotations

import os
import re
from typing import Any


PROFILE_ENV = "SPATIALACC_ACCORD_PROFILE"
SUPPORTED_PROFILES = {"ACCORD", "B0", "B2"}

DESIGN_GRAPH_KEYS = {
    "source_sacg_state",
    "sacg_state",
    "sacg_context",
    "sacg_memory",
    "sacg_memory_truth",
    "hierarchical_learning_context",
    "design_consistency_graph",
    "cross_stage_dependency_graph",
    "dependency_graph",
    "dependency_closure",
}

GUIDED_REPAIR_KEYS = {
    "causal_frontier",
    "causal_graph_slice",
    "causal_localization",
    "cctg_policy",
    "contract_guided_debug_closure",
    "cctg_boundaries",
    "cctg_causal_paths",
    "current_board_to_lower_layer_contradiction",
    "earliest_unproven_frontier",
    "failure_localization",
    "failure_loop",
    "minimal_repair_context",
    "experiment_profile",
    "prior_repair_execution_feedback",
    "repair_loop",
    "root_candidate_module",
    "sacg_cctg_causal_slice",
    "targeted_replay_plan",
    "violated_contract",
}
GUIDED_REPAIR_TOOLS = {
    "causal_repair_context_check",
    "causal_repair_context_pack",
    "connected_kernel_cctg_contradiction_reconciliation_check",
    "connected_kernel_cctg_contradiction_targeted_replay",
    "failure_localization_check",
    "failure_slice_localization",
}
GUIDED_REPAIR_TEXT_MARKERS = (
    "contract-guided",
    "contract guided",
    "causal frontier",
    "causal slice",
    "causally affected interface family",
    "causal-boundary",
    "causal boundary",
    "causal distinction",
    "earliest causal",
    "earliest violated boundary",
    "failure_localization",
    "failure localization",
    "frontier stall",
)


def contains_guided_repair_text(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            contains_guided_repair_text(key)
            or contains_guided_repair_text(child)
            for key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(contains_guided_repair_text(item) for item in value)
    text = str(value).lower()
    return bool(re.search(r"\bcctg\b", text)) or any(
        marker in text for marker in GUIDED_REPAIR_TEXT_MARKERS
    )


def without_guided_repair_prompt_rules(rules: list[str]) -> list[str]:
    return [rule for rule in rules if not contains_guided_repair_text(rule)]


def active_profile() -> str:
    value = os.environ.get(PROFILE_ENV, "ACCORD").strip().upper() or "ACCORD"
    if value not in SUPPORTED_PROFILES:
        supported = ", ".join(sorted(SUPPORTED_PROFILES))
        raise ValueError(f"unsupported ACCORD experiment profile {value!r}; supported: {supported}")
    return value


def without_guided_repair_context(value: Any) -> Any:
    """Remove CCTG-produced projections while retaining ordinary evidence."""

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in GUIDED_REPAIR_KEYS or "cctg" in normalized_key:
                continue
            if isinstance(child, str) and contains_guided_repair_text(child):
                continue
            if normalized_key in {"tool_roles", "acceptance_checkers"} and isinstance(child, list):
                child = [
                    item
                    for item in child
                    if str(item).strip().lower() not in GUIDED_REPAIR_TOOLS
                    and not contains_guided_repair_text(item)
                ]
            elif normalized_key == "action_contract_examples" and isinstance(child, list):
                child = [
                    item
                    for item in child
                    if not any(
                        name in str(item).lower()
                        for name in GUIDED_REPAIR_TOOLS
                    )
                    and not contains_guided_repair_text(item)
                ]
            result[str(key)] = without_guided_repair_context(child)
        return result
    if isinstance(value, list):
        return [
            without_guided_repair_context(item)
            for item in value
            if not contains_guided_repair_text(item)
        ]
    if isinstance(value, tuple):
        return tuple(
            without_guided_repair_context(item)
            for item in value
            if not contains_guided_repair_text(item)
        )
    return value


def without_design_graph_context(value: Any) -> Any:
    """Keep task facts and tool evidence while hiding SACG/DCG prompt context."""

    if isinstance(value, dict):
        return {
            str(key): without_design_graph_context(child)
            for key, child in value.items()
            if str(key).strip().lower() not in DESIGN_GRAPH_KEYS
        }
    if isinstance(value, list):
        return [without_design_graph_context(item) for item in value]
    if isinstance(value, tuple):
        return tuple(without_design_graph_context(item) for item in value)
    return value
