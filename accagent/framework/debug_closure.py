"""Contract-guided debug-closure helpers.

This module keeps debug localization tied to artifacts the agent system already
owns: pipeline stages, dataflow edges, verification evidence, and case-adapter
diagnostics. It is intentionally boundary-focused rather than a general RTL
debugger.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from accagent.framework.repair_loop import failure_kind
from accagent.framework.sacg_utils import artifact_path, read_json, safe_id, write_json


DEBUG_CLOSURE_SCHEMA = "spatialaccagent.debug_closure.v0"


DEBUG_LAYERS = [
    {
        "id": "operator_leaf_modules",
        "order": 0,
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
        "trace_gate": "case_leaf_functional",
        "failure_scope": "leaf_operator_boundary",
    },
    {
        "id": "single_transformer_layer_kernel",
        "order": 1,
        "required_gates": [
            "single_transformer_layer",
            "case_single_layer_functional",
            "case_single_layer_golden_compare",
            "case_single_layer_semantic_evidence",
        ],
        "trace_gate": "case_single_layer_functional",
        "failure_scope": "inter_stage_integration_boundary",
    },
    {
        "id": "board_axi_ddr_wrapped_system",
        "order": 2,
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
        "trace_gate": "case_vcs_functional_sim",
        "failure_scope": "board_axi_ddr_runtime_boundary",
    },
]


def read_artifact_json(state: dict[str, Any], artifact_id: str) -> dict[str, Any]:
    try:
        return read_json(artifact_path(state, artifact_id))
    except Exception:
        return {}


def pipeline_graph(state: dict[str, Any]) -> dict[str, Any]:
    plan = read_artifact_json(state, "artifact.stage3.pipeline_plan")
    stages = [item for item in plan.get("stages", []) if isinstance(item, dict)]
    edges = [item for item in plan.get("stream_edges", []) if isinstance(item, dict)]
    if not edges:
        edges = [item for item in plan.get("data_edges", []) if isinstance(item, dict)]
    return {"plan": plan, "stages": stages, "edges": edges}


def edge_id(edge: dict[str, Any], index: int) -> str:
    value = edge.get("edge_id") or f"{edge.get('src_stage', 'src')}__to__{edge.get('dst_stage', 'dst')}"
    return safe_id(str(value or f"edge_{index}"))


def boundary_contract_for_edge(edge: dict[str, Any], index: int) -> dict[str, Any]:
    src = str(edge.get("src_stage") or edge.get("src") or "unknown_src")
    dst = str(edge.get("dst_stage") or edge.get("dst") or "unknown_dst")
    eid = edge_id(edge, index)
    return {
        "boundary_id": f"boundary.{eid}",
        "edge_id": eid,
        "src_stage": src,
        "dst_stage": dst,
        "boundary": f"{src}->{dst}",
        "expected_invariants": [
            "transaction_id_preserved",
            "valid_ready_order_preserved",
            "tile_id_preserved_when_present",
            "logical_index_mapping_matches_stage_contract",
            "output_valid_within_declared_latency_window",
            "numeric_policy_matches_stage_binding",
            "memory_address_range_matches_runtime_layout_when_present",
        ],
        "trace_fields": [
            "cycle",
            "boundary_id",
            "tx_id",
            "tile_id",
            "logical_index",
            "observed_value",
            "expected_value",
            "contract",
            "status",
        ],
        "debug_policy": {
            "check_only_boundary_transactions": True,
            "trace_only_failing_transaction_by_default": True,
        },
    }


def build_boundary_contracts(state: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    graph = pipeline_graph(state)
    boundaries = [boundary_contract_for_edge(edge, idx) for idx, edge in enumerate(graph["edges"])]
    stage_order = [str(item.get("stage_id")) for item in graph["stages"] if item.get("stage_id")]
    causal_path = ["block_input", *stage_order, "block_output"] if stage_order else []
    boundary_order = [item["boundary_id"] for item in boundaries]
    return {
        "schema_version": "spatialaccagent.debug_boundary_contracts.v0",
        "design_id": state.get("design_id"),
        "run_dir": str(run_dir),
        "contract_type": "boundary_contract_failure_slice_targeted_replay",
        "boundaries": boundaries,
        "causal_paths": [
            {
                "path_id": "default_pipeline_path",
                "stages": causal_path,
                "boundary_order": boundary_order,
            }
        ],
        "targeted_replay": {
            "strategy": "boundary_bisection_then_earliest_violation",
            "inputs": [
                "failing_output_transaction",
                "boundary_trace_records",
                "optional_golden_boundary_values",
            ],
            "outputs": [
                "root_candidate_module",
                "violated_contract",
                "failure_signature",
                "minimal_repair_context",
            ],
        },
        "trace_record_schema": {
            "required_fields": [
                "cycle",
                "boundary_id",
                "tx_id",
                "tile_id",
                "logical_index",
                "observed_value",
                "expected_value",
                "contract",
                "status",
            ],
            "status_values": ["pass", "fail", "warning", "diagnostic_seed"],
            "value_encoding": "case_adapter_defined_scalar_or_vector_with_explicit_width_when_available",
            "path_binding": {
                "manifest": str(run_dir / "verification" / "debug_closure" / "trace_manifest.json"),
                "trace": str(run_dir / "verification" / "debug_closure" / "boundary_trace.json"),
                "localization": str(run_dir / "verification" / "debug_closure" / "failure_localization.json"),
            },
        },
        "instrumentation_contract": {
            "monitor_points": [
                "module_boundary_valid_ready",
                "transaction_and_tile_identity",
                "logical_index_and_lane_mapping",
                "declared_latency_window",
                "numeric_policy_and_tolerance",
                "runtime_memory_address_range",
            ],
            "modes": [
                "failing_transaction_first",
                "target_boundary_replay",
                "full_boundary_trace_when_requested",
            ],
            "resource_policy": (
                "Boundary monitors are verification instrumentation and should be generated by the "
                "case adapter or testbench path. Persistent hardware monitors require explicit "
                "runtime/debug approval because they may consume FPGA resources."
            ),
        },
        "repair_handoff_contract": {
            "required_fields": [
                "root_candidate_module",
                "violated_contract",
                "failure_signature",
                "causal_path",
                "targeted_replay_plan",
                "minimal_repair_context",
            ],
            "repair_rule": (
                "Repair agents must patch the localized causal slice or request targeted replay; "
                "they must not patch the downstream symptom module solely because it observed the failure."
            ),
            "layer_rule": (
                "If all lower debug layers have passing evidence and the current merged layer fails, "
                "the next action is current-layer boundary tracing or targeted replay over the integration "
                "path. Lower-layer pass evidence is reusable, not absolute; reopen a lower layer only "
                "when the new boundary trace explicitly contradicts its pass evidence."
            ),
        },
        "policy": {
            "not_a_general_rtl_debugger": True,
            "uses_agent_generated_dataflow_knowledge": True,
            "repair_agent_receives_compact_causal_slice": True,
            "do_not_patch_downstream_symptom_without_upstream_localization": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
            "production_goal_not_toy_trace": True,
            "tool_trace_schema_must_be_case_adapter_independent": True,
        },
    }


def boundary_rank(boundary_contracts: dict[str, Any]) -> dict[str, int]:
    order: list[str] = []
    paths = boundary_contracts.get("causal_paths", [])
    if paths and isinstance(paths[0], dict):
        order = [str(item) for item in paths[0].get("boundary_order", [])]
    if not order:
        order = [str(item.get("boundary_id")) for item in boundary_contracts.get("boundaries", []) if item.get("boundary_id")]
    return {boundary_id: index for index, boundary_id in enumerate(order)}


def trace_failure_sort_key(
    row: dict[str, Any],
    ranks: dict[str, int],
    stage_exit_ranks: dict[str, int],
    source_order: int,
) -> tuple[int, int, int, int]:
    boundary_order = ranks.get(str(row.get("boundary_id") or ""), 10**9)
    if row.get("evidence_type") != "semantic_internal_boundary_trace":
        return boundary_order, 1, 10**9, source_order
    stage_order = stage_exit_ranks.get(str(row.get("stage_id") or ""), boundary_order)
    try:
        cycle = int(row.get("cycle"))
    except (TypeError, ValueError):
        cycle = 10**9
    return stage_order, 0, cycle, source_order


def representative_failure_records(
    failures: list[dict[str, Any]],
    limit: int = 16,
) -> list[dict[str, Any]]:
    """Keep one earliest causal record per failure boundary/class without losing evidence types."""

    representatives: list[dict[str, Any]] = []
    positions: dict[tuple[Any, ...], int] = {}
    for row in failures:
        key = (
            row.get("evidence_type"),
            row.get("stage_id"),
            row.get("boundary_id"),
            row.get("module"),
            row.get("failure_class"),
            row.get("violated_contract") or row.get("contract"),
        )
        position = positions.get(key)
        if position is not None:
            representatives[position]["equivalent_failure_count"] += 1
            continue
        positions[key] = len(representatives)
        representative = dict(row)
        representative["equivalent_failure_count"] = 1
        representatives.append(representative)
    return representatives[:limit]


def load_trace_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        try:
            data = read_json(path)
        except Exception:
            continue
        if isinstance(data.get("boundary_trace"), list):
            records.extend(item for item in data["boundary_trace"] if isinstance(item, dict))
        elif isinstance(data.get("debug_closure"), dict) and isinstance(data["debug_closure"].get("boundary_trace"), list):
            records.extend(item for item in data["debug_closure"]["boundary_trace"] if isinstance(item, dict))
        elif isinstance(data.get("records"), list):
            records.extend(item for item in data["records"] if isinstance(item, dict))
        elif str(data.get("schema_version") or "").startswith((
            "spatialaccagent.case_leaf_operator_verify",
            "spatialaccagent.qwen_leaf_operator_verify",
        )):
            closure = data.get("debug_closure", {}) if isinstance(data.get("debug_closure"), dict) else {}
            slice_items = closure.get("failure_slice", []) if isinstance(closure.get("failure_slice"), list) else []
            if not slice_items and data.get("status") == "fail":
                slice_items = [
                    item for item in data.get("module_results", [])
                    if isinstance(item, dict) and item.get("status") != "pass"
                ][:1]
            for item in slice_items:
                if not isinstance(item, dict):
                    continue
                records.append(
                    {
                        "status": "fail",
                        "source": str(path),
                        "evidence_type": data.get("gate") or "operator_leaf_verification",
                        "stage_id": data.get("stage_id"),
                        "module": item.get("module") or closure.get("root_candidate_module"),
                        "contract": data.get("gate") or "operator_leaf_boundary_contract",
                        "violated_contract": data.get("gate") or "operator_leaf_boundary_contract",
                        "summary": item.get("summary") or data.get("summary"),
                        "observed_value": item.get("verilator", {}).get("run", {}).get("stdout_tail")
                        if isinstance(item.get("verilator"), dict)
                        else None,
                        "expected_value": "leaf module must satisfy its local ready-valid/golden boundary contract before integration",
                    }
                )
        elif data.get("diagnosis_status") or data.get("root_cause_class"):
            records.append(
                {
                    "status": "diagnostic_seed",
                    "source": str(path),
                    "root_cause_class": data.get("root_cause_class"),
                    "summary": data.get("summary"),
                    "repair_handoff": data.get("repair_handoff", {}),
                }
            )
        elif "boundary_id" in data or "module" in data:
            records.append(data)
    deduplicated: list[dict[str, Any]] = []
    seen_internal: set[tuple[Any, ...]] = set()
    for record in records:
        if record.get("evidence_type") != "semantic_internal_boundary_trace":
            deduplicated.append(record)
            continue
        observed = record.get("observed_value", {}) if isinstance(record.get("observed_value"), dict) else {}
        key = (
            record.get("stage_id"),
            record.get("boundary_id"),
            record.get("module"),
            record.get("cycle"),
            record.get("beat_index"),
            record.get("status"),
            observed.get("valid"),
            observed.get("ready"),
            observed.get("packed_literal"),
        )
        if key in seen_internal:
            continue
        seen_internal.add(key)
        deduplicated.append(record)
    return deduplicated


def targeted_replay_plan(
    boundary_contracts: dict[str, Any],
    earliest: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    order = (boundary_contracts.get("causal_paths") or [{}])[0].get("boundary_order", [])
    order = [str(item) for item in order]
    if not order:
        order = [str(item.get("boundary_id")) for item in boundary_contracts.get("boundaries", []) if item.get("boundary_id")]
    failed_boundary = str(earliest.get("boundary_id") or "")
    failed_stage = str(earliest.get("stage_id") or "")
    try:
        failed_index = order.index(failed_boundary)
    except ValueError:
        failed_index = None
    probes = []
    adjacent_boundaries = [
        str(item.get("boundary_id"))
        for item in boundary_contracts.get("boundaries", [])
        if isinstance(item, dict)
        and item.get("boundary_id")
        and failed_stage
        and failed_stage in {str(item.get("src_stage") or ""), str(item.get("dst_stage") or "")}
    ]
    if failed_index is None and adjacent_boundaries:
        probes = [
            {
                "probe_id": f"targeted_replay.stage_boundary_{index:02d}",
                "boundary_id": boundary_id,
                "method": "golden_boundary_compare_or_injection",
                "purpose": f"localize the first divergence adjacent to failed leaf stage {failed_stage}",
            }
            for index, boundary_id in enumerate(adjacent_boundaries)
        ]
    elif order:
        lo = 0
        hi = len(order) - 1 if failed_index is None else failed_index
        while lo <= hi:
            mid = (lo + hi) // 2
            probes.append(
                {
                    "probe_id": f"targeted_replay.boundary_{mid:02d}",
                    "boundary_id": order[mid],
                    "method": "golden_boundary_compare_or_injection",
                    "purpose": "bisect failing transaction path before applying RTL repair",
                }
            )
            if failed_index is None or mid == failed_index:
                break
            if mid < failed_index:
                lo = mid + 1
            else:
                hi = mid - 1
    return {
        "schema_version": "spatialaccagent.targeted_replay_plan.v1",
        "status": "ready" if status == "localized" else "needs_boundary_trace",
        "strategy": (
            "failed_stage_adjacent_boundary_replay"
            if failed_index is None and adjacent_boundaries
            else "boundary_level_binary_search_then_earliest_violation"
        ),
        "failed_boundary_index": failed_index,
        "probe_sequence": probes,
        "rerun_env": {
            "SPATIALACC_BOUNDARY_TRACE": "1",
            "SPATIALACC_TARGETED_REPLAY": "1",
            "SPATIALACC_CHECKPOINT_REPLAY": "1",
            "SPATIALACC_TARGET_BOUNDARY": failed_boundary or (adjacent_boundaries[0] if adjacent_boundaries else ""),
        },
        "simulation_checkpoint_replay": {
            "status": "requested",
            "cut_selection": "latest_committed_semantic_event_before_active_cctg_frontier",
            "capture_scope": [
                "complete_simulator_state",
                "testbench_external_state",
                "axi_ddr_transaction_state",
            ],
            "reuse_modes": [
                "native_exact_model",
                "portable_cross_revision_with_schema_causal_cut_and_equivalence_certificates",
            ],
            "unsafe_reuse_action": "cold_capture",
            "max_heavy_jobs": 1,
            "persistent_content_addressed_storage": True,
        },
        "acceptance": {
            "earliest_failed_boundary_identified": bool(failed_boundary),
            "failed_stage_identified": bool(failed_stage),
            "repair_context_must_reference_boundary_contract": True,
            "checkpoint_replay_is_screening_only": True,
            "full_cold_exact_board_vcs_required_before_stage_pass": True,
        },
    }


def gate_statuses_from_verification(verification_result: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    gate_summary = verification_result.get("hierarchical_gate_summary", {})
    if isinstance(gate_summary, dict):
        for row in gate_summary.get("required_gates", []):
            if isinstance(row, dict) and row.get("name"):
                statuses[str(row["name"])] = str(row.get("status") or "not_run")
    for row in verification_result.get("results", []):
        if not isinstance(row, dict):
            continue
        checker = str(row.get("checker") or "")
        if checker.startswith("real_tool."):
            statuses[checker.removeprefix("real_tool.")] = str(row.get("status") or "not_run")
    return statuses


def current_debug_layer_context(verification_result: dict[str, Any]) -> dict[str, Any]:
    statuses = gate_statuses_from_verification(verification_result)
    lower_passed_gates: list[str] = []
    lower_passed = True
    for layer in DEBUG_LAYERS:
        gate_rows = [
            {"name": gate, "status": statuses.get(gate, "not_run")}
            for gate in layer["required_gates"]
        ]
        failed = [row for row in gate_rows if row["status"] != "pass"]
        if lower_passed and failed:
            failed_current = [row for row in failed if row["status"] in {"fail", "not_run", "blocked"}]
            functional_failures = [
                row["name"]
                for row in gate_rows
                if row["status"] == "fail" and ("functional" in row["name"] or row["name"] == "single_transformer_layer")
            ]
            return {
                "id": layer["id"],
                "order": layer["order"],
                "status": "needs_repair",
                "failure_scope": layer["failure_scope"],
                "recommended_trace_gate": functional_failures[0] if functional_failures else layer["trace_gate"],
                "required_gates": gate_rows,
                "failed_current_layer_gates": failed_current,
                "lower_layers_passed": True,
                "lower_layer_pass_evidence": lower_passed_gates,
            }
        if failed:
            return {
                "id": layer["id"],
                "order": layer["order"],
                "status": "blocked_by_lower_layer",
                "failure_scope": layer["failure_scope"],
                "recommended_trace_gate": layer["trace_gate"],
                "required_gates": gate_rows,
                "failed_current_layer_gates": failed,
                "lower_layers_passed": False,
                "lower_layer_pass_evidence": lower_passed_gates,
            }
        lower_passed_gates.extend(row["name"] for row in gate_rows)
    return {
        "id": DEBUG_LAYERS[-1]["id"],
        "order": DEBUG_LAYERS[-1]["order"],
        "status": "pass",
        "failure_scope": "none",
        "recommended_trace_gate": "",
        "required_gates": [],
        "failed_current_layer_gates": [],
        "lower_layers_passed": True,
        "lower_layer_pass_evidence": lower_passed_gates,
    }


def integration_failure_context(
    boundary_contracts: dict[str, Any],
    verification_result: dict[str, Any],
) -> dict[str, Any]:
    context = current_debug_layer_context(verification_result)
    if context.get("status") != "needs_repair" or not context.get("lower_layers_passed"):
        return {}
    if context.get("id") == "operator_leaf_modules":
        return {}
    failed_gates = [row["name"] for row in context.get("failed_current_layer_gates", []) if row.get("status") == "fail"]
    if not failed_gates:
        return {}
    boundaries = [
        {
            "boundary_id": item.get("boundary_id"),
            "src_stage": item.get("src_stage"),
            "dst_stage": item.get("dst_stage"),
            "boundary": item.get("boundary"),
        }
        for item in boundary_contracts.get("boundaries", [])
        if isinstance(item, dict)
    ]
    return {
        "current_debug_layer": context,
        "recommended_trace_gate": context.get("recommended_trace_gate"),
        "candidate_boundaries": boundaries[:32],
        "failure_scope": context.get("failure_scope"),
        "anti_deadlock_rule": (
            "Lower debug layer pass evidence is reusable but not absolute. First debug the current "
            "integration layer; reopen a lower layer only when a current-layer boundary trace explicitly "
            "contradicts that lower-layer evidence."
        ),
        "candidate_bug_classes": [
            "ready_valid_connection_order",
            "stream_last_or_transaction_boundary",
            "tensor_layout_or_lane_mapping_between_verified_modules",
            "queue_depth_or_latency_alignment_between_modules",
            "skip_residual_or_branch_join_alignment",
            "numeric_policy_conversion_at_module_boundary",
            "single_layer_testbench_or_manifest_binding",
        ],
    }


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def lower_layer_challenge_from_trace(
    trace_record: dict[str, Any],
    integration_context: dict[str, Any],
) -> dict[str, Any]:
    lower_passed = (
        integration_context.get("current_debug_layer", {}).get("lower_layer_pass_evidence", [])
        if isinstance(integration_context.get("current_debug_layer"), dict)
        else []
    )
    if not trace_record or not lower_passed:
        return {
            "status": "no_lower_layer_challenge",
            "reason": "no localized trace record with lower-layer pass evidence is available",
        }
    text = " ".join(
        str(trace_record.get(key) or "")
        for key in [
            "contract",
            "violated_contract",
            "summary",
            "reason",
            "root_cause_class",
            "failure_class",
            "lower_layer_evidence_status",
        ]
    ).lower()
    contradicts = bool(
        trace_record.get("contradicts_lower_layer_pass")
        or trace_record.get("contradicts_lower_layer_evidence")
        or trace_record.get("invalidates_lower_layer_evidence")
        or trace_record.get("requires_lower_layer_reopen")
        or "contradicts lower-layer" in text
        or "contradicts lower layer" in text
        or "invalidates lower-layer" in text
        or "invalidates lower layer" in text
    )
    challenged_gates = [
        str(item)
        for key in ["challenged_gates", "invalidated_gates", "lower_layer_gates", "reopen_gates"]
        for item in _as_list(trace_record.get(key))
        if str(item)
    ]
    challenged_modules = [
        str(item)
        for key in ["challenged_modules", "invalidated_modules", "lower_layer_modules", "reopen_modules"]
        for item in _as_list(trace_record.get(key))
        if str(item)
    ]
    for key in ["challenged_gate", "invalidated_gate", "lower_layer_gate", "reopen_gate"]:
        if trace_record.get(key):
            challenged_gates.append(str(trace_record[key]))
    for key in ["challenged_module", "invalidated_module", "lower_layer_module", "reopen_module"]:
        if trace_record.get(key):
            challenged_modules.append(str(trace_record[key]))
    if not contradicts:
        return {
            "status": "no_lower_layer_challenge",
            "reason": "localized trace does not explicitly contradict lower-layer pass evidence",
            "lower_layer_pass_evidence": lower_passed,
        }
    if not (challenged_gates or challenged_modules):
        return {
            "status": "insufficient_challenge_evidence",
            "reason": "trace asserts contradiction but does not bind it to lower-layer gates or modules",
            "source_trace": trace_record,
            "lower_layer_pass_evidence": lower_passed,
        }
    return {
        "status": "challenge_present",
        "contradicts_lower_layer_pass": True,
        "source_trace": trace_record,
        "challenged_gates": sorted(set(challenged_gates)),
        "challenged_modules": sorted(set(challenged_modules)),
        "lower_layer_pass_evidence": lower_passed,
        "reason": trace_record.get("reason") or trace_record.get("summary") or "current-layer trace contradicts lower-layer pass evidence",
    }


def failing_transaction_from_records(records: list[dict[str, Any]], verification_result: dict[str, Any]) -> dict[str, Any]:
    for row in records:
        if str(row.get("status") or "").lower() == "fail":
            return {
                "tx_id": row.get("tx_id"),
                "tile_id": row.get("tile_id"),
                "logical_index": row.get("logical_index"),
                "word_index": row.get("word_index"),
                "beat_index": row.get("beat_index"),
                "lane_index": row.get("lane_index"),
                "stage_id": row.get("stage_id"),
                "module": row.get("module"),
                "observed_value": row.get("observed_value"),
                "expected_value": row.get("expected_value"),
                "rtl_output_sha256": row.get("rtl_output_sha256"),
                "input_fingerprint_sha256": row.get("input_fingerprint_sha256"),
                "source": row.get("source") or "boundary_trace",
            }
    failed = [item for item in verification_result.get("results", []) if item.get("status") == "fail"]
    if failed:
        item = failed[0]
        return {
            "checker": item.get("checker"),
            "summary": item.get("summary"),
            "source": "verification_result",
        }
    return {"source": "none"}


def localize_failure(
    boundary_contracts: dict[str, Any],
    verification_result: dict[str, Any],
    trace_records: list[dict[str, Any]],
) -> dict[str, Any]:
    ranks = boundary_rank(boundary_contracts)
    failures = [
        row for row in trace_records
        if str(row.get("status") or "").lower() == "fail"
    ]
    stage_exit_ranks: dict[str, int] = {}
    for boundary in boundary_contracts.get("boundaries", []):
        if not isinstance(boundary, dict):
            continue
        stage_id = str(boundary.get("src_stage") or "")
        boundary_id = str(boundary.get("boundary_id") or "")
        if not stage_id or boundary_id not in ranks:
            continue
        stage_exit_ranks[stage_id] = min(stage_exit_ranks.get(stage_id, 10**9), ranks[boundary_id])
    failures = [
        row
        for _, row in sorted(
            enumerate(failures),
            key=lambda item: trace_failure_sort_key(item[1], ranks, stage_exit_ranks, item[0]),
        )
    ]
    earliest = failures[0] if failures else {}
    representative_failures = representative_failure_records(failures)
    boundary_by_id = {
        str(item.get("boundary_id")): item
        for item in boundary_contracts.get("boundaries", [])
        if isinstance(item, dict) and item.get("boundary_id")
    }
    contract = boundary_by_id.get(str(earliest.get("boundary_id") or ""), {})
    failing_tx = failing_transaction_from_records(trace_records, verification_result)
    capability_gap = not earliest and failure_kind({}, verification_result) == "verification_capability_gap"
    status = (
        "localized"
        if earliest
        else (
            "verification_capability_gap"
            if capability_gap
            else ("needs_boundary_trace" if verification_result.get("status") == "fail" else "no_failure")
        )
    )
    root_candidate = earliest.get("module") or contract.get("src_stage") or contract.get("dst_stage")
    violated_contract = earliest.get("violated_contract") or earliest.get("contract")
    if not violated_contract and earliest:
        violated_contract = "boundary_contract"
    if capability_gap:
        violated_contract = "verification_semantic_capability_contract"
    integration_context = integration_failure_context(boundary_contracts, verification_result) if not earliest and not capability_gap else {}
    if integration_context and status == "needs_boundary_trace":
        root_candidate = str(integration_context.get("current_debug_layer", {}).get("id") or "current_layer_integration")
        violated_contract = str(integration_context.get("failure_scope") or "current_layer_boundary_contract")
    lower_layer_challenge = lower_layer_challenge_from_trace(
        earliest,
        integration_context or integration_failure_context(boundary_contracts, verification_result),
    )
    return {
        "schema_version": DEBUG_CLOSURE_SCHEMA,
        "status": status,
        "strategy": "contract_guided_boundary_failure_slice",
        "failing_transaction": failing_tx,
        "root_candidate_module": root_candidate,
        "violated_contract": violated_contract,
        "current_layer_failure_context": integration_context,
        "lower_layer_evidence_challenge": lower_layer_challenge,
        "recommended_trace_gate": integration_context.get("recommended_trace_gate") if integration_context else None,
        "failure_signature": {
            "boundary_id": earliest.get("boundary_id"),
            "boundary": contract.get("boundary"),
            "observed_value": earliest.get("observed_value"),
            "expected_value": earliest.get("expected_value"),
            "status": earliest.get("status"),
            "summary": earliest.get("summary"),
            "integration_summary": (
                "current debug layer failed after all lower debug layers passed; collect current-layer "
                "boundary trace before reopening lower-layer leaf repairs"
                if integration_context
                else None
            ),
        },
        "causal_path": (boundary_contracts.get("causal_paths") or [{}])[0],
        "failed_boundaries": representative_failures,
        "failure_record_count": len(failures),
        "representative_failure_count": len(representative_failures),
        "targeted_replay_plan": (
            {
                "status": "blocked_by_verification_capability_gap",
                "reason": "repair semantic testbench, loader/weight binding, numeric contract, or checker capability before requesting a hardware boundary trace",
            }
            if capability_gap
            else targeted_replay_plan(boundary_contracts, earliest, status)
        ),
        "minimal_repair_context": {
            "root_candidate_module": root_candidate,
            "violated_contract": violated_contract,
            "boundary_contract": contract,
            "trace_record": earliest,
            "repair_scope": (
                "causal_slice"
                if earliest
                else (
                    "verification_capability_repair"
                    if capability_gap
                    else (
                    "current_layer_integration_boundary_trace"
                    if integration_context
                    else "collect_boundary_trace"
                    )
                )
            ),
            "current_layer_failure_context": integration_context,
            "lower_layer_evidence_challenge": lower_layer_challenge,
        },
        "policy": {
            "repair_agent_should_use_causal_slice_only": True,
            "if_status_needs_boundary_trace_rerun_stage7_with_boundary_monitors": True,
            "verification_capability_gap_must_be_repaired_before_hardware_trace": True,
            "do_not_patch_output_module_only_because_symptom_is_downstream": True,
            "lower_layer_pass_evidence_is_reusable_not_absolute": True,
            "do_not_reopen_passed_lower_layer_without_contradicting_boundary_trace": True,
        },
    }


def default_trace_candidates(run_dir: Path) -> list[Path]:
    candidates = [
        run_dir / "verification" / "debug_closure" / "boundary_trace.json",
        run_dir / "verification" / "case_diagnostics" / "boundary_trace.json",
        run_dir / "verification" / "case_diagnostics" / "vcs_functional_diagnosis.json",
        run_dir / "verification" / "case_diagnostics" / "contract_guided_failure_localization.json",
    ]
    for folder in ["operator_leaf_functional", "operator_leaf_golden"]:
        candidates.extend(
            path for path in sorted((run_dir / "verification" / folder).glob("*.json"))
            if path.name != "summary.json"
        )
        candidates.append(run_dir / "verification" / folder / "summary.json")
    return candidates


def build_debug_closure_artifacts(
    state: dict[str, Any],
    run_dir: Path,
    verification_result: dict[str, Any] | None = None,
    trace_paths: list[Path] | None = None,
) -> dict[str, Any]:
    boundary_contracts = build_boundary_contracts(state, run_dir)
    verification_result = verification_result or {}
    records = load_trace_records(trace_paths or default_trace_candidates(run_dir))
    localization = localize_failure(boundary_contracts, verification_result, records)
    trace_manifest = build_trace_manifest(run_dir, boundary_contracts)
    return {
        "schema_version": "spatialaccagent.debug_closure_artifacts.v0",
        "boundary_contracts": boundary_contracts,
        "trace_manifest": trace_manifest,
        "failure_localization": localization,
    }


def build_trace_manifest(run_dir: Path, boundary_contracts: dict[str, Any]) -> dict[str, Any]:
    trace_dir = run_dir / "verification" / "debug_closure"
    return {
        "schema_version": "spatialaccagent.boundary_trace_manifest.v0",
        "trace_policy": "failing_transaction_first_boundary_trace",
        "boundary_contracts_path": str(trace_dir / "boundary_contracts.json"),
        "boundary_trace_path": str(trace_dir / "boundary_trace.json"),
        "golden_boundary_values_path": str(trace_dir / "golden_boundary_values.json"),
        "failure_localization_path": str(trace_dir / "failure_localization.json"),
        "boundary_count": len(boundary_contracts.get("boundaries", [])),
        "required_record_fields": [
            "cycle",
            "boundary_id",
            "tx_id",
            "tile_id",
            "logical_index",
            "observed_value",
            "expected_value",
            "contract",
            "status",
        ],
        "targeted_replay": {
            "strategy": "boundary_bisection",
            "rerun_env": {
                "SPATIALACC_BOUNDARY_TRACE": "1",
                "SPATIALACC_TARGETED_REPLAY": "1",
            },
            "binary_search_over": [
                item.get("boundary_id")
                for item in boundary_contracts.get("boundaries", [])
                if isinstance(item, dict)
            ],
        },
        "policy": {
            "trace_all_boundaries_only_when_requested": True,
            "default_trace_scope": "failing_transaction",
            "trace_schema_is_case_adapter_independent": True,
            "downstream_failure_without_trace_must_request_targeted_replay": True,
            "repair_context_requires_earliest_violated_boundary": True,
        },
    }


def write_debug_closure_artifacts(
    state: dict[str, Any],
    run_dir: Path,
    out_dir: Path,
    verification_result: dict[str, Any] | None = None,
    trace_paths: list[Path] | None = None,
) -> dict[str, str]:
    artifacts = build_debug_closure_artifacts(state, run_dir, verification_result, trace_paths)
    out_dir.mkdir(parents=True, exist_ok=True)
    boundary_path = out_dir / "boundary_contracts.json"
    trace_manifest_path = out_dir / "trace_manifest.json"
    localization_path = out_dir / "failure_localization.json"
    write_json(boundary_path, artifacts["boundary_contracts"])
    write_json(trace_manifest_path, artifacts["trace_manifest"])
    write_json(localization_path, artifacts["failure_localization"])
    return {
        "boundary_contracts": str(boundary_path),
        "trace_manifest": str(trace_manifest_path),
        "boundary_trace": str(out_dir / "boundary_trace.json"),
        "failure_localization": str(localization_path),
    }
