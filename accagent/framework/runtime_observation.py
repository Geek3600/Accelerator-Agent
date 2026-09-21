"""Runtime-only signal selection for Layer-3 board simulation.

The board testbench is compiled once with broad, unconditional observation.
Later debug rounds select a useful subset from that compiled catalog without
editing SystemVerilog.  This keeps the compiled-model identity stable so the
same native VCS snapshot can be restored for every observation-only round.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Iterable


CATALOG_SCHEMA_VERSION = "spatialaccagent.compiled_signal_catalog.v3"
SELECTION_SCHEMA_VERSION = "spatialaccagent.runtime_observation_selection.v1"
MINIMUM_RUNTIME_SIGNAL_COUNT = 300

_EMITTED_STATIC_SIGNAL_RE = re.compile(
    r'emit_stage_trace_scalar\(\s*"[^"]*"\s*,\s*[^,]+\s*,\s*[^,]+\s*,\s*[^,]+\s*,\s*"([^"]+)"'
)
_EMITTED_DYNAMIC_SIGNAL_RE = re.compile(
    r'emit_stage_trace_scalar\(\s*"[^"]*"\s*,\s*[^,]+\s*,\s*[^,]+\s*,\s*[^,]+\s*,\s*\$sformatf\(\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)'
)
_DUT_SIGNAL_RE = re.compile(
    r"\bdut(?:\.[A-Za-z_$][A-Za-z0-9_$]*(?:\[[^\]\n]+\])?)+"
)
_BOUNDARY_NAME_RE = re.compile(
    r'^\s*(\d+)\s*:\s*current_dag_boundary_name\s*=\s*"([^"]+)"\s*;',
    re.MULTILINE,
)
_BOUNDARY_BINDING_RE = re.compile(
    r"assign\s+current_dag_boundary_(valid|ready|payload)\[(\d+)\]\s*=\s*"
    r"(dut(?:\.[A-Za-z_$][A-Za-z0-9_$]*(?:\[[^\]\n]+\])?)+)\s*;"
)
_DIRECT_DUT_ASSIGNMENT_RE = re.compile(
    r"assign\s+[A-Za-z_$][A-Za-z0-9_$]*(?:\[[^\]\n]+\])?\s*=\s*"
    r"(dut(?:\.[A-Za-z_$][A-Za-z0-9_$]*(?:\[[^\]\n]+\])?)+)\s*;"
)


def compiled_signal_catalog_path(run_dir: Path) -> Path:
    return (
        Path(run_dir)
        / "verification"
        / "adaptive_observation"
        / "compiled_signal_catalog.json"
    )


def current_observation_selection_path(run_dir: Path) -> Path:
    return (
        Path(run_dir)
        / "verification"
        / "adaptive_observation"
        / "current_selection.json"
    )


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _board_testbench_path(run_dir: Path) -> Path | None:
    manifest_path = (
        Path(run_dir)
        / "generated"
        / "memory"
        / "dut_weight_binding_manifest.json"
    )
    manifest = _read_json(manifest_path)
    plan = manifest.get("board_simulation_preflight_plan", {})
    plan = plan if isinstance(plan, dict) else {}
    testbench = plan.get("testbench", {})
    testbench = testbench if isinstance(testbench, dict) else {}
    candidates = [
        testbench.get("path"),
        testbench.get("local_path"),
        testbench.get("generated_source_path"),
        Path(run_dir)
        / "generated"
        / "board_integration"
        / "spatialacc_exact_board_multilayer_tb.sv",
    ]
    for value in candidates:
        if not value:
            continue
        path = Path(str(value))
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        if path.is_file():
            return path
    return None


def _compiled_model_identity(run_dir: Path) -> str:
    """Read the identity of the current board source closure.

    The replay state describes the last usable simulator.  It can legitimately
    lag after a functional source edit, so it must never label a newly scanned
    testbench as if it belonged to the old snapshot.  The board manifest is
    the single source of truth for the current compiled model.
    """

    manifest = _read_json(
        Path(run_dir)
        / "verification"
        / "board_simulation"
        / "board_simulation_manifest.json"
    )
    try:
        from .simulation_checkpoint import simulation_execution_identity

        return str(
            simulation_execution_identity(manifest).get(
                "compiled_model_sha256"
            )
            or ""
        )
    except (ImportError, TypeError, ValueError):
        # Catalog construction is observational.  A missing manifest is
        # reported as an unavailable identity by the caller, never used to
        # substitute a stale replay identity.
        return ""


def _signal_role(expression: str) -> str:
    name = expression.rsplit(".", 1)[-1].lower()
    if "valid" in name or "ready" in name:
        return "handshake"
    if any(token in name for token in ("empty", "full", "ptr", "queue", "fifo")):
        return "queue"
    if any(token in name for token in ("count", "index", "beat", "token", "addr")):
        return "counter"
    if any(token in name for token in ("state", "phase", "start", "done", "last")):
        return "control"
    if any(token in name for token in ("error", "overflow", "underflow")):
        return "error"
    if any(token in name for token in ("data", "bits", "payload")):
        return "data"
    return "state"


def _signal_stage(expression: str) -> str:
    lowered = expression.lower()
    stage_markers = (
        (".rms1.", "stage_00_rms_norm_1"),
        (".qkv.", "stage_01_self_attention"),
        (".rope.", "stage_01_self_attention"),
        (".attn.", "stage_01_self_attention"),
        (".add1.", "stage_02_residual_add_1"),
        (".res1q.", "stage_02_residual_add_1"),
        (".rms2.", "stage_03_rms_norm_2"),
        (".mlp.gate.", "stage_04_mlp_gate_proj"),
        (".mlp.up.", "stage_05_mlp_up_proj"),
        (".mlp.mul.", "stage_06_activation_mul"),
        (".mlp.actq.", "stage_06_activation_mul"),
        (".mlp.upq.", "stage_06_activation_mul"),
        (".mlp.down.", "stage_07_mlp_down_proj"),
        (".add2.", "stage_08_residual_add_2"),
        (".res2q.", "stage_08_residual_add_2"),
        (".core.io_out", "block_output"),
        ("kernel_output", "board_output"),
        ("c0_ddr4_s_axi", "axi_ddr"),
        ("weight", "weight_loader"),
        ("runtime", "runtime_loader"),
    )
    for marker, stage in stage_markers:
        if marker in lowered:
            return stage
    return "board_control"


def _direct_assignment_is_scalar(expression: str) -> bool:
    """Keep direct control/status assignments, not raw payload vectors."""

    leaf = expression.rsplit(".", 1)[-1].lower()
    return not any(token in leaf for token in ("bits_data", "payload", "wdata", "rdata"))


def build_compiled_signal_catalog(run_dir: Path) -> dict[str, Any]:
    """Build the signal catalog from the already compiled broad testbench."""

    run_dir = Path(run_dir)
    testbench_path = _board_testbench_path(run_dir)
    if testbench_path is None:
        return {
            "schema_version": CATALOG_SCHEMA_VERSION,
            "status": "unavailable",
            "compiled_model_sha256": _compiled_model_identity(run_dir) or None,
            "signal_count": 0,
            "signals": [],
            "advisories": ["current board testbench source is unavailable"],
        }

    text = testbench_path.read_text(encoding="utf-8", errors="replace")
    boundary_names = {
        int(index): name for index, name in _BOUNDARY_NAME_RE.findall(text)
    }
    boundary_by_expression: dict[str, str] = {}
    boundary_expressions: set[str] = set()
    for field, index, expression in _BOUNDARY_BINDING_RE.findall(text):
        boundary = boundary_names.get(int(index))
        if boundary:
            boundary_by_expression[expression] = boundary
        if field in {"valid", "ready"}:
            boundary_expressions.add(expression)

    # Only advertise expressions that are really passed to the common trace
    # task.  Scanning every DUT reference also finds signals that appear only
    # in JSON boundary records or control logic and can never reach the
    # runtime stage trace.
    emitted: set[str] = set(_EMITTED_STATIC_SIGNAL_RE.findall(text))
    for match in _EMITTED_DYNAMIC_SIGNAL_RE.finditer(text):
        template, loop_variable = match.groups()
        prefix = text[max(0, match.start() - 800) : match.start()]
        bound_match = re.search(
            rf"for\s*\(\s*{re.escape(loop_variable)}\s*=\s*0\s*;\s*"
            rf"{re.escape(loop_variable)}\s*<\s*(\d+)\s*;",
            prefix,
        )
        if bound_match is None:
            continue
        bound = int(bound_match.group(1))
        for index in range(bound):
            emitted.add(template.replace("%0d", str(index)))
    direct_assignments = {
        expression
        for expression in _DIRECT_DUT_ASSIGNMENT_RE.findall(text)
        if _direct_assignment_is_scalar(expression)
    }
    expressions = sorted(emitted | boundary_expressions | direct_assignments)
    signals = [
        {
            "expression": expression,
            "stage": _signal_stage(expression),
            "boundary": boundary_by_expression.get(expression),
            "role": _signal_role(expression),
            "trace_available": True,
            "observation_sources": [
                source
                for source, available in (
                    ("stage_trace", expression in emitted),
                    ("boundary_trace", expression in boundary_expressions),
                    ("direct_assignment", expression in direct_assignments),
                )
                if available
            ],
        }
        for expression in expressions
    ]
    compiled_model = _compiled_model_identity(run_dir)
    catalog = {
        "schema_version": CATALOG_SCHEMA_VERSION,
        "status": "ready" if signals else "unavailable",
        "compiled_model_sha256": compiled_model or None,
        "testbench": {
            "path": str(testbench_path),
            "sha256": _sha256_file(testbench_path),
        },
        "signal_count": len(signals),
        "signals": signals,
        "policy": {
            "compiled_once": True,
            "selection_is_runtime_only": True,
            "selection_must_not_modify_compiled_sources": True,
            "old_signal_values_are_not_reused": True,
        },
        "advisories": [],
    }
    _atomic_write_json(compiled_signal_catalog_path(run_dir), catalog)
    return catalog


def load_or_build_compiled_signal_catalog(run_dir: Path) -> dict[str, Any]:
    current_model = _compiled_model_identity(run_dir)
    path = compiled_signal_catalog_path(run_dir)
    existing = _read_json(path)
    if (
        existing.get("schema_version") == CATALOG_SCHEMA_VERSION
        and existing.get("status") == "ready"
        and str(existing.get("compiled_model_sha256") or "") == current_model
        and isinstance(existing.get("signals"), list)
        and existing.get("signals")
    ):
        return existing
    return build_compiled_signal_catalog(run_dir)


def _expression_from_binding(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "=" in text:
        text = text.rsplit("=", 1)[-1].strip()
    match = _DUT_SIGNAL_RE.search(text)
    return match.group(0) if match else text


def requested_signal_expressions(decision: dict[str, Any]) -> list[str]:
    """Collect every signal expression requested by one Agent decision."""

    expressions: list[str] = []

    def add(values: Any) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            expression = _expression_from_binding(value)
            if expression:
                expressions.append(expression)

    delta = decision.get("observation_delta", {})
    delta = delta if isinstance(delta, dict) else {}
    add(delta.get("new_signal_expressions"))
    for row in delta.get("candidate_cause_checks", []):
        if isinstance(row, dict):
            add(row.get("signal_expressions"))

    for row in decision.get("signal_binding_plan", []):
        if not isinstance(row, dict):
            continue
        for key, value in row.items():
            if key.endswith("_source"):
                expression = _expression_from_binding(value)
                if expression:
                    expressions.append(expression)
        diagnostic = row.get("diagnostic_sources")
        if isinstance(diagnostic, list):
            for value in diagnostic:
                if isinstance(value, dict):
                    expression = _expression_from_binding(
                        value.get("expression") or value.get("signal")
                    )
                    if expression:
                        expressions.append(expression)
                else:
                    expression = _expression_from_binding(value)
                    if expression:
                        expressions.append(expression)

    for row in decision.get("stage_internal_signal_plan", []):
        if not isinstance(row, dict):
            continue
        for key in ("signals", "signal_expressions", "diagnostic_sources"):
            values = row.get(key)
            if not isinstance(values, list):
                continue
            for value in values:
                if isinstance(value, dict):
                    expression = _expression_from_binding(
                        value.get("expression") or value.get("signal")
                    )
                else:
                    expression = _expression_from_binding(value)
                if expression:
                    expressions.append(expression)

    return list(dict.fromkeys(expressions))


def runtime_observation_selection(
    run_dir: Path,
    decision: dict[str, Any],
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Select compiled signals without touching RTL or the board testbench."""

    catalog = load_or_build_compiled_signal_catalog(run_dir)
    catalog_rows = {
        str(row.get("expression") or ""): row
        for row in catalog.get("signals", [])
        if isinstance(row, dict) and row.get("expression")
    }
    requested = requested_signal_expressions(decision)
    selected = [catalog_rows[value] for value in requested if value in catalog_rows]
    unknown = [value for value in requested if value not in catalog_rows]
    if not requested:
        # A broad observation-only rerun still remains useful.  Select the
        # complete compiled catalog rather than editing the testbench again.
        selected = list(catalog_rows.values())

    selected_expressions = {row["expression"] for row in selected}
    auto_filled = 0
    if (
        len(catalog_rows) >= MINIMUM_RUNTIME_SIGNAL_COUNT
        and len(selected) < MINIMUM_RUNTIME_SIGNAL_COUNT
    ):
        for expression in sorted(catalog_rows):
            if expression in selected_expressions:
                continue
            selected.append(catalog_rows[expression])
            selected_expressions.add(expression)
            auto_filled += 1
            if len(selected) >= MINIMUM_RUNTIME_SIGNAL_COUNT:
                break
    decision_sha256 = hashlib.sha256(
        json.dumps(decision, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    selection = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": "ready" if selected else "advisory_only",
        "decision_sha256": decision_sha256,
        "frontier_id": decision.get("frontier_id"),
        "compiled_model_sha256": catalog.get("compiled_model_sha256"),
        "catalog_path": str(compiled_signal_catalog_path(run_dir)),
        "catalog_signal_count": catalog.get("signal_count", 0),
        "requested_signal_count": len(requested),
        "selected_signal_count": len(selected),
        "auto_filled_signal_count": auto_filled,
        "minimum_signal_count": MINIMUM_RUNTIME_SIGNAL_COUNT,
        "selected_signals": selected,
        "unknown_signal_expressions": unknown,
        "advisories": (
            [
                "some requested expressions are not present in the compiled signal catalog; "
                "the broad compiled observation remains active"
            ]
            if unknown
            else []
        ),
        "policy": {
            "runtime_only": True,
            "compiled_source_edit_required": False,
            "unknown_expressions_do_not_block_layer3": True,
            "current_signal_epoch_only": True,
            "minimum_signal_count": MINIMUM_RUNTIME_SIGNAL_COUNT,
        },
    }
    if persist:
        _atomic_write_json(current_observation_selection_path(run_dir), selection)
    return selection


def catalog_prompt_projection(catalog: dict[str, Any]) -> dict[str, Any]:
    """Return the complete bounded catalog used by the Layer-3 Agent."""

    rows = catalog.get("signals", [])
    rows = rows if isinstance(rows, list) else []
    return {
        "schema_version": catalog.get("schema_version"),
        "status": catalog.get("status"),
        "compiled_model_sha256": catalog.get("compiled_model_sha256"),
        "signal_count": len(rows),
        "signals": rows,
        "selection_contract": {
            "file_edits_must_be_empty": True,
            "select_only_catalog_expressions": True,
            "selection_is_runtime_only": True,
            "same_snapshot_remains_reusable": True,
        },
    }


def selected_expression_set(selection: dict[str, Any]) -> set[str]:
    return {
        str(row.get("expression"))
        for row in selection.get("selected_signals", [])
        if isinstance(row, dict) and row.get("expression")
    }


def event_contains_selected_signal(event: Any, expressions: Iterable[str]) -> bool:
    """Best-effort match of a fresh trace record to a runtime selection."""

    wanted = set(expressions)
    if not wanted or not isinstance(event, dict):
        return bool(wanted)
    text = json.dumps(event, sort_keys=True, ensure_ascii=True)
    return any(expression in text for expression in wanted)
