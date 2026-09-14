"""Hierarchical verification/repair-loop contracts.

The loop is intentionally generic.  Case adapters provide concrete tools and
gate names; this module only defines how failed evidence is routed through the
three hardware-debug layers before downstream promotion is allowed.
"""

from __future__ import annotations

from typing import Any


DEBUG_LAYERS = [
    {
        "id": "operator_leaf_modules",
        "order": 0,
        "purpose": "Debug every spatially parallel operator module before integration.",
        "repair_loop": "module_tool_run__cctg_localize__bounded_module_or_checker_repair__rerun",
        "required_gates": [
            "case_real_weight_artifacts",
            "case_target_model_reference",
            "case_semantic_testbench",
            "case_stage_leaf_static",
            "boundary_contract_check",
            "case_leaf_functional",
            "case_leaf_golden_compare",
            "case_operator_leaf_semantic_evidence",
        ],
        "promotion_target": "single_transformer_layer_kernel",
    },
    {
        "id": "single_transformer_layer_kernel",
        "order": 1,
        "purpose": "Debug the connected one-layer transformer spatial kernel after leaf modules pass.",
        "repair_loop": "layer_tool_run__cctg_failure_slice__bounded_interconnect_or_module_repair__rerun",
        "required_gates": [
            "single_transformer_layer",
            "case_single_layer_functional",
            "case_single_layer_golden_compare",
            "case_single_layer_semantic_evidence",
        ],
        "promotion_target": "board_axi_ddr_wrapped_system",
    },
    {
        "id": "board_axi_ddr_wrapped_system",
        "order": 2,
        "purpose": "Debug the accelerator behind the real board AXI/DDR wrapper and runtime ABI.",
        "repair_loop": "board_wrapper_tool_run__cctg_axi_ddr_slice__bounded_wrapper_or_runtime_repair__rerun",
        "required_gates": [
            "case_board_interface_discovery",
            "case_multilayer_pipeline",
            "case_multilayer_functional",
            "case_pipeline_deadlock_check",
            "case_axi_ddr_interface",
            "case_axi_protocol_check",
            "case_ddr_image_roundtrip",
            "functional_sim",
            "case_board_semantic_evidence",
        ],
        "promotion_target": "backend_bitstream_and_board_runtime",
    },
]


GATE_TO_LAYER = {
    gate: layer["id"]
    for layer in DEBUG_LAYERS
    for gate in layer["required_gates"]
}


def hierarchical_debug_loop_contract() -> dict[str, Any]:
    return {
        "schema_version": "spatialaccagent.hierarchical_debug_loop_contract.v0",
        "layer_order": [layer["id"] for layer in DEBUG_LAYERS],
        "layers": [
            {
                "id": layer["id"],
                "order": layer["order"],
                "purpose": layer["purpose"],
                "entry_condition": (
                    "all lower debug layers have pass evidence"
                    if int(layer["order"]) > 0
                    else "Stage6 verification gate DAG and real case-adapter tools are available"
                ),
                "exit_condition": "all required gates for this layer pass with real-tool evidence and any required golden/numeric comparison",
                "failure_loop": [
                    "run current-layer real tool",
                    "collect CCTG boundary trace or failure localization evidence",
                    "classify earliest violated boundary/current-layer contract",
                    "apply only bounded repair permitted by SACG/human-boundary rules",
                    "rerun the same current layer until pass before promotion",
                ],
                "required_gates": layer["required_gates"],
                "promotion_target": layer["promotion_target"],
            }
            for layer in DEBUG_LAYERS
        ],
        "cctg_policy": {
            "purpose": "speed root-cause localization by mapping real-tool symptoms to the earliest violated contract/boundary",
            "required_on_failure": True,
            "first_action_when_trace_missing": "debug_trace_rerun for the failed current-layer gate",
            "localized_action": "causal_slice_repair over the localized boundary or current-layer integration slice",
            "trace_schema_is_case_adapter_driven": True,
        },
        "anti_spin_policy": {
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "passed_lower_layer_can_be_challenged_by_current_layer_trace": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_current_layer_trace": True,
            "current_layer_failure_after_lower_pass_means": "debug current-layer integration, interconnect, wrapper, scheduler, data order, or boundary contract first",
            "reopening_lower_layer_requires": [
                "a current-layer boundary trace record that directly contradicts lower-layer pass evidence",
                "or a SACG-approved design-contract change invalidating the previous lower-layer evidence",
            ],
            "when_reopened": [
                "record the contradicted lower-layer gate/module and source trace in SACG",
                "rerun only the challenged lower-layer scope with expanded boundary stimuli or corrected contract",
                "after lower-layer revalidation, rerun the failed current layer before any higher-layer promotion",
            ],
        },
        "promotion_policy": {
            "next_layer_requires_current_layer_certificate": True,
            "dependency_skipped_or_smoke_evidence_cannot_promote": True,
            "backend_or_board_runtime_requires_all_three_debug_layers_to_pass": True,
        },
    }


def required_gate_statuses(gate_summary: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for row in gate_summary.get("required_gates", []):
        if isinstance(row, dict) and row.get("name"):
            statuses[str(row["name"])] = str(row.get("status") or "not_run")
    return statuses


def tool_statuses(verification_result: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in verification_result.get("results", []):
        if not isinstance(row, dict):
            continue
        checker = str(row.get("checker") or "")
        if checker.startswith("real_tool."):
            result[checker.removeprefix("real_tool.")] = str(row.get("status") or "not_run")
    return result


def gate_layer(layer_id: str) -> dict[str, Any]:
    for layer in DEBUG_LAYERS:
        if layer["id"] == layer_id:
            return dict(layer)
    return {}


def layer_reports(gate_summary: dict[str, Any], verification_result: dict[str, Any]) -> list[dict[str, Any]]:
    gates = required_gate_statuses(gate_summary)
    tools = tool_statuses(verification_result)
    reports: list[dict[str, Any]] = []
    lower_layer_failed = False
    for layer in DEBUG_LAYERS:
        gate_rows = []
        for gate in layer["required_gates"]:
            status = gates.get(gate) or tools.get(gate) or "not_run"
            gate_rows.append({"name": gate, "status": status})
        missing_or_failed = [
            f"{row['name']}={row['status']}"
            for row in gate_rows
            if row["status"] != "pass"
        ]
        pending_later_stage = bool(gate_rows) and all(
            row["status"] == "pending_later_stage" for row in gate_rows
        )
        if lower_layer_failed:
            status = "blocked"
        elif not missing_or_failed:
            status = "pass"
        elif pending_later_stage:
            # The selector deliberately did not run this higher layer.  This is
            # not a failed gate and must not trigger a repair/LLM investigation.
            status = "pending_later_stage"
        else:
            status = "needs_repair"
        reports.append(
            {
                **layer,
                "status": status,
                "required_gates": gate_rows,
                "missing_or_failed": missing_or_failed,
            }
        )
        lower_layer_failed = lower_layer_failed or status == "needs_repair"
    return reports


def passed_lower_layer_gates(layers: list[dict[str, Any]], current_layer_id: str) -> list[str]:
    gates: list[str] = []
    for layer in layers:
        if layer.get("id") == current_layer_id:
            break
        if layer.get("status") != "pass":
            continue
        for row in layer.get("required_gates", []):
            if isinstance(row, dict) and row.get("status") == "pass":
                gates.append(str(row.get("name")))
    return gates


def failed_current_layer_gates(layer: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"name": str(row.get("name")), "status": str(row.get("status") or "not_run")}
        for row in layer.get("required_gates", [])
        if isinstance(row, dict) and row.get("status") not in {"pass", "pending_later_stage"}
    ]


def current_layer(layers: list[dict[str, Any]]) -> dict[str, Any]:
    for layer in layers:
        if layer.get("status") == "needs_repair":
            return layer
    for layer in layers:
        if layer.get("status") == "blocked":
            return layer
    for index, layer in enumerate(layers):
        if layer.get("status") == "pending_later_stage":
            # Report the last completed layer as the active scope.  This keeps
            # a successful leaf-only run from being misclassified as a pending
            # single-layer repair loop.
            return layers[index - 1] if index else layer
    return layers[-1] if layers else {}


def higher_layer_gate_executed(
    current_layer_id: str,
    verification_result: dict[str, Any],
) -> list[str]:
    current = gate_layer(current_layer_id)
    if not current:
        return []
    current_order = int(current.get("order", 99))
    higher_gates = {
        gate
        for layer in DEBUG_LAYERS
        if int(layer["order"]) > current_order
        for gate in layer["required_gates"]
    }
    executed = []
    for row in verification_result.get("results", []):
        if not isinstance(row, dict):
            continue
        checker = str(row.get("checker") or "").removeprefix("real_tool.")
        if checker in higher_gates and row.get("status") in {"pass", "fail"}:
            executed.append(checker)
    return sorted(set(executed))


def failure_kind(debug_localization: dict[str, Any], verification_result: dict[str, Any]) -> str:
    failed_rows = [item for item in verification_result.get("results", []) if isinstance(item, dict) and item.get("status") == "fail"]
    current_failure_text = " ".join(
        [
            " ".join(str(item.get("summary") or "") for item in failed_rows),
            " ".join(
                " ".join(str(blocker) for blocker in item.get("tool_report_blockers", []) if blocker)
                for item in failed_rows
            ),
        ]
    ).lower()
    if any(
        token in current_failure_text
        for token in (
            "remote vcs transport failed",
            "remote transport failure",
            "remote_transport_failure",
            "ssh returncode=255",
        )
    ):
        return "verification_tool_transport_failure"
    failed_real_tools = [
        item for item in failed_rows if str(item.get("checker") or "").startswith("real_tool.")
    ]
    dependency_skipped_tools = [
        item
        for item in verification_result.get("results", [])
        if isinstance(item, dict)
        and str(item.get("checker") or "").startswith("real_tool.")
        and item.get("status") == "not_run"
        and str(item.get("summary") or "").startswith("skipped because dependency gate")
    ]
    current_semantic_tool_failures = [
        item
        for item in failed_real_tools
        if any(
            token in f"{item.get('checker', '')} {item.get('kind', '')}".lower()
            for token in ("functional", "golden", "numeric_compare")
        )
        and not any(
            token in str(item.get("kind") or "").lower()
            for token in ("generate", "assemble", "static")
        )
    ]
    localized_failures = [
        item
        for item in debug_localization.get("failed_boundaries", [])
        if isinstance(item, dict) and item.get("status") == "fail"
    ]
    if current_semantic_tool_failures and any(
        item.get("evidence_type") == "semantic_numeric_compare"
        and item.get("failure_class")
        and item.get("stage_id")
        and item.get("module")
        for item in localized_failures
    ):
        return "hardware_value_mismatch"
    summary = " ".join(
        [
            str(debug_localization.get("violated_contract") or ""),
            str(debug_localization.get("failure_signature", {}).get("summary") or ""),
            " ".join(str(item.get("summary") or "") for item in failed_rows),
            " ".join(" ".join(str(blocker) for blocker in item.get("tool_report_blockers", []) if blocker) for item in failed_rows),
            " ".join(
                " ".join(str(blocker) for blocker in report.get("blockers", []) if blocker)
                for item in failed_rows
                for report in (item.get("produced_reports", []) if isinstance(item.get("produced_reports"), list) else [])
                if isinstance(report, dict)
            ),
        ]
    ).lower()
    failed_checkers = " ".join(str(item.get("checker") or "") for item in failed_rows).lower()
    if failed_real_tools and dependency_skipped_tools and not current_semantic_tool_failures:
        return "verification_capability_gap"
    if (
        "missing independent golden" in summary
        or "golden reference is not implemented" in summary
        or "golden reference memh is missing" in summary
        or ("golden_compare" in failed_checkers and "reference" in summary and "missing" in summary)
        or "semantic testbench manifest status is incomplete" in summary
        or "dut real-weight binding manifest missing" in summary
        or "dut weight-binding manifest status is not pass" in summary
        or "semantic testbench does not prove real-weight loading" in summary
        or "explicit numeric comparison atol/rtol/max_mismatch_fraction is missing" in summary
        or "verification contract" in summary and "incomplete" in summary
        or "required python environment" in summary
        or "python environment" in summary and ("missing" in summary or "unavailable" in summary or "fail" in summary)
        or "no module named" in summary
    ):
        return "verification_capability_gap"
    if "model_not_found" in summary or "llm" in summary and "unavailable" in summary:
        return "agent_runtime_llm_configuration"
    if "timeout" in summary or "did not produce" in summary or "deadlock" in summary:
        return "hardware_liveness_or_handshake"
    if "mismatch" in summary:
        return "hardware_value_mismatch"
    if "axi" in summary or "ddr" in summary:
        return "board_interface_or_runtime"
    return "unclassified_debug_failure"


def layer_aware_failure_kind(
    active: dict[str, Any],
    debug_localization: dict[str, Any],
    verification_result: dict[str, Any],
    lower_passed: list[str],
) -> str:
    challenge = lower_layer_evidence_challenge(debug_localization, active, lower_passed)
    if challenge.get("status") == "challenge_present":
        return "lower_layer_evidence_contradicted"
    base = failure_kind(debug_localization, verification_result)
    if base in {
        "verification_capability_gap",
        "verification_tool_transport_failure",
        "agent_runtime_llm_configuration",
    }:
        return base
    failed_names = {row["name"] for row in failed_current_layer_gates(active)}
    if (
        active.get("id") == "single_transformer_layer_kernel"
        and lower_passed
        and failed_names.intersection({"single_transformer_layer", "case_single_layer_functional", "case_single_layer_golden_compare"})
    ):
        return "integration_boundary_or_layer_interconnect"
    if (
        active.get("id") == "board_axi_ddr_wrapped_system"
        and lower_passed
        and failed_names.intersection(
            {
                "case_multilayer_pipeline",
                "case_multilayer_functional",
                "case_pipeline_deadlock_check",
                "case_axi_ddr_interface",
                "case_axi_protocol_check",
                "case_ddr_image_roundtrip",
                "functional_sim",
            }
        )
    ):
        return "board_wrapper_or_pipeline_integration"
    return base


def lower_layer_evidence_challenge(
    debug_localization: dict[str, Any],
    active: dict[str, Any],
    lower_passed: list[str],
) -> dict[str, Any]:
    if not debug_localization or not lower_passed or not active:
        return {
            "status": "no_lower_layer_challenge",
            "reason": "no lower-layer pass evidence or no debug localization is available",
        }
    raw = debug_localization.get("lower_layer_evidence_challenge")
    if not isinstance(raw, dict):
        context = debug_localization.get("minimal_repair_context", {})
        if isinstance(context, dict):
            raw = context.get("lower_layer_evidence_challenge")
    if not isinstance(raw, dict):
        return {
            "status": "no_lower_layer_challenge",
            "reason": "current-layer evidence does not explicitly contradict lower-layer pass evidence",
            "lower_layer_pass_evidence": lower_passed,
        }
    contradicts = bool(
        raw.get("contradicts_lower_layer_pass")
        or raw.get("contradicts_lower_layer_evidence")
        or raw.get("invalidates_lower_layer_evidence")
    )
    trace = raw.get("source_trace") or raw.get("trace_record") or raw.get("evidence")
    challenged_gates = [str(item) for item in raw.get("challenged_gates", []) if str(item)] if isinstance(raw.get("challenged_gates"), list) else []
    challenged_modules = [str(item) for item in raw.get("challenged_modules", []) if str(item)] if isinstance(raw.get("challenged_modules"), list) else []
    if not contradicts:
        return {
            "status": "no_lower_layer_challenge",
            "reason": "challenge object is present but does not assert a contradiction",
            "lower_layer_pass_evidence": lower_passed,
        }
    if not (trace or challenged_gates or challenged_modules):
        return {
            "status": "insufficient_challenge_evidence",
            "reason": "lower-layer challenge lacks source trace, gate, or module binding",
            "lower_layer_pass_evidence": lower_passed,
        }
    return {
        "status": "challenge_present",
        "current_layer": active.get("id"),
        "source_trace": trace,
        "challenged_gates": challenged_gates,
        "challenged_modules": challenged_modules,
        "reason": raw.get("reason") or "current-layer CCTG trace contradicts lower-layer pass evidence",
        "lower_layer_pass_evidence": lower_passed,
    }


def has_llm_runtime_blocker(verification_result: dict[str, Any]) -> bool:
    for row in verification_result.get("results", []):
        if not isinstance(row, dict) or row.get("status") != "fail":
            continue
        checker = str(row.get("checker") or "")
        summary = str(row.get("summary") or "").lower()
        if "llm" in checker or "model_not_found" in summary or "used fallback output" in summary:
            return True
    return False


def build_repair_loop_report(
    *,
    verification_result: dict[str, Any],
    debug_localization: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gate_summary = verification_result.get("hierarchical_gate_summary", {}) if isinstance(verification_result.get("hierarchical_gate_summary"), dict) else {}
    layers = layer_reports(gate_summary, verification_result)
    active = current_layer(layers)
    debug_localization = debug_localization or {}
    out_of_order = higher_layer_gate_executed(str(active.get("id") or ""), verification_result) if active else []
    status = (
        "pass"
        if layers
        and all(layer.get("status") in {"pass", "pending_later_stage"} for layer in layers)
        else "needs_repair"
    )
    if out_of_order:
        status = "fail"
    lower_passed = passed_lower_layer_gates(layers, str(active.get("id") or "")) if active else []
    current_failed = failed_current_layer_gates(active) if active else []
    lower_challenge = lower_layer_evidence_challenge(debug_localization, active, lower_passed) if status != "pass" else {
        "status": "no_lower_layer_challenge",
        "reason": "verification passed",
    }
    kind = layer_aware_failure_kind(active, debug_localization, verification_result, lower_passed) if status != "pass" else "none"
    return {
        "schema_version": "spatialaccagent.hierarchical_repair_loop.v0",
        "status": status,
        "debug_loop_contract": hierarchical_debug_loop_contract(),
        "current_layer": active,
        "layers": layers,
        "failure_kind": kind,
        "agent_runtime_llm_blocker": has_llm_runtime_blocker(verification_result),
        "root_candidate_module": debug_localization.get("root_candidate_module"),
        "violated_contract": debug_localization.get("violated_contract"),
        "lower_layer_pass_evidence": lower_passed,
        "lower_layer_evidence_challenge": lower_challenge,
        "failed_current_layer_gates": current_failed,
        "out_of_order_executed_higher_layer_gates": out_of_order,
        "policy": {
            "three_layer_debug_order_is_mandatory": True,
            "failed_layer_must_repair_before_next_layer": True,
            "cctg_required_for_root_cause_localization": True,
            "tool_output_then_llm_analysis_then_bounded_patch_then_rerun": True,
            "no_stage_promotion_from_smoke_or_dependency_skipped_evidence": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "higher_layer_trace_can_trigger_targeted_lower_layer_backtrack": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
            "current_layer_failure_after_lower_pass_means_integration_boundary_debug": True,
        },
    }
